"""Ingesta de actividad de GitHub y atribucion (SPEC 10 S10.2-S10.3; SPEC 06
S6.8; A-070 a A-072, A-118, A-196, A-205, A-221; Etapa F5).

Tres fuentes y ninguna sustituye a las otras: el webhook (`procesar_webhooks`),
la reconciliacion condicional por ETag cada 15 minutos (`reconciliar_actividad`)
y el barrido nocturno con el relleno hacia atras (`barrido_completo_actividad`).
Las decisiones viven en `app/dominio/actividad.py`.

Toda escritura de `commit` pasa por `ingerir_commits`, que es idempotente por
`(repositorio_id, sha)`, solo enriquece campos nulos y nunca borra: lo que
desaparece de la historia queda `huerfano`.

Simplificaciones, cada una con su TODO donde toca:
- Sin enriquecimiento por GraphQL: los co-autores no se cuentan y las lineas
  quedan nulas («no disponible»), que es exactamente la degradacion que S10.3.3
  regla 7 y S10.3.5 declaran de antemano. TODO(graphql).
- `autor_es_docente` queda en falso: la cuenta de GitHub del equipo docente solo
  se conoce por su login declarado, y comparar por login esta prohibido
  (S10.3.1 regla 2). Es un dato informativo que no cambia ningun recuento.
- Sin `presupuesto_api` medido: un limite de GitHub hace fallar el ciclo como
  transitorio y el trabajo reintenta; no hay freno por porcentaje. TODO(presupuesto).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores import incidencia_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.cliente_github import ClienteGitHub, RechazoProveedorGithub
from app.adaptadores.modelos_actividad import (
    AutoriaCommit,
    Commit,
    EventoPush,
    EventoWebhook,
    IdentidadGit,
)
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    FechaEfectiva,
    Repositorio,
    Sujeto,
)
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import CursorSincronizacion
from app.adaptadores.modelos_mapeo import CuentaGithub, MapeoGithub
from app.adaptadores.modelos_padron import Estudiante
from app.adaptadores.modelos_tarea import RepositorioBase, Tarea
from app.dominio.actividad import (
    SHA_CEROS,
    CommitGithub,
    ContextoAtribucion,
    atribuir,
    decidir_relleno,
    es_mejora,
    motivo_exclusion,
    normalizar_email,
    repositorio_en_ingesta,
)
from app.dominio.estados import (
    EstadoAccesoRepositorio,
    EstadoEventoWebhook,
    EstadoFechaEfectiva,
    EstadoIdentidadGit,
    EstadoMapeoGithub,
    EstadoRepositorio,
    MotivoExclusionCommit,
    MotivoInaccesible,
    OrigenIngesta,
    PapelAutoria,
    ReglaAtribucion,
)
from app.dominio.versiones import CommitCierre

RECURSO_COMMITS = "commits"
MAX_RAMAS = 50  # S10.2.3 regla 6
REINTENTOS_SIN_DESTINO = (
    timedelta(minutes=1),
    timedelta(minutes=5),
    timedelta(minutes=15),
    timedelta(minutes=60),
)
PLAZO_SIN_DESTINO = timedelta(hours=24)


def _nombre_repo(repositorio: Repositorio) -> str:
    return (repositorio.full_name or "").split("/", 1)[-1] or repositorio.nombre


# --- Atribucion (S10.3) ---


def contexto_curso(bd: Session, curso_id: uuid.UUID) -> tuple[dict[int, Any], dict[str, Any]]:
    """`(estudiante por github_user_id, estudiante por correo de Canvas)`. La
    clave es siempre el identificador numerico, nunca el login."""
    por_id: dict[int, Any] = {}
    for estudiante_id, github_user_id in (
        bd.query(MapeoGithub.estudiante_id, CuentaGithub.github_user_id)
        .join(CuentaGithub, CuentaGithub.id == MapeoGithub.cuenta_github_id)
        .filter(
            MapeoGithub.curso_id == curso_id,
            MapeoGithub.estado == EstadoMapeoGithub.VIGENTE.value,
        )
    ):
        por_id[github_user_id] = estudiante_id
    por_email = {
        normalizado: e.id
        for e in bd.query(Estudiante).filter(Estudiante.curso_id == curso_id)
        if (normalizado := normalizar_email(e.email)) is not None
    }
    return por_id, por_email


def identidad_vigente(
    bd: Session, repositorio_id: uuid.UUID, email_normalizado: str
) -> IdentidadGit | None:
    return (
        bd.query(IdentidadGit)
        .filter(
            IdentidadGit.repositorio_id == repositorio_id,
            IdentidadGit.email_normalizado == email_normalizado,
            IdentidadGit.estado != EstadoIdentidadGit.SUPERSEDIDA.value,
        )
        .one_or_none()
    )


def _asegurar_identidad(
    bd: Session, repositorio: Repositorio, email: str, nombre: str | None
) -> IdentidadGit:
    normalizado = normalizar_email(email)
    assert normalizado is not None
    identidad = identidad_vigente(bd, repositorio.id, normalizado)
    if identidad is None:
        identidad = IdentidadGit(
            curso_id=repositorio.curso_id,
            repositorio_id=repositorio.id,
            email_normalizado=normalizado,
            email_visto=email.strip(),
            nombre_visto=nombre,
            nombre_visto_ultimo=nombre,
            estado=EstadoIdentidadGit.SIN_RESOLVER.value,
            vigente_desde=ahora_utc(),
        )
        bd.add(identidad)
        bd.flush()
    elif nombre and identidad.nombre_visto_ultimo != nombre:
        identidad.nombre_visto_ultimo = nombre
    return identidad


def atribuir_commit(
    bd: Session,
    commit: Commit,
    repositorio: Repositorio,
    contexto: tuple[dict[int, Any], dict[str, Any]],
    *,
    solo_si_mejora: bool,
) -> bool:
    """Aplica la cascada y deja la fila `AUTOR` de `autoria_commit` y su copia
    en `commit`. Con `solo_si_mejora`, nunca empeora una atribucion previa.
    Devuelve `True` si cambio algo."""
    por_id, por_email = contexto
    email = normalizar_email(commit.autor_email)
    identidad = identidad_vigente(bd, repositorio.id, email) if email else None
    resultado = atribuir(
        autor_github_user_id=commit.autor_github_user_id,
        autor_email=commit.autor_email,
        contexto=ContextoAtribucion(
            estudiante_por_github_id=por_id,
            estudiante_por_email=por_email,
            identidad=(identidad.estado, identidad.estudiante_id) if identidad else None,
        ),
    )
    actual = ReglaAtribucion(commit.regla_atribucion)
    tiene_autoria = (
        bd.query(AutoriaCommit.id)
        .filter(
            AutoriaCommit.commit_id == commit.id, AutoriaCommit.papel == PapelAutoria.AUTOR.value
        )
        .first()
        is not None
    )
    if solo_si_mejora and tiene_autoria and not es_mejora(actual, resultado.regla):
        return False
    # Un bot no es una persona que resolver: no abre identidad ni cuenta como
    # «sin atribuir» para las causas de S10.5.3 (sigue siendo contable).
    if (
        resultado.regla == ReglaAtribucion.SIN_ATRIBUIR
        and commit.autor_email
        and not commit.autor_es_bot
    ):
        identidad = identidad or _asegurar_identidad(
            bd, repositorio, commit.autor_email, commit.autor_nombre
        )
    commit.regla_atribucion = resultado.regla.value
    commit.estudiante_id = resultado.estudiante_id  # type: ignore[assignment]
    commit.identidad_git_id = identidad.id if identidad is not None else None
    bd.query(AutoriaCommit).filter(
        AutoriaCommit.commit_id == commit.id, AutoriaCommit.papel == PapelAutoria.AUTOR.value
    ).delete()
    if resultado.estudiante_id is not None or identidad is not None:
        bd.add(
            AutoriaCommit(
                commit_id=commit.id,
                estudiante_id=resultado.estudiante_id,
                identidad_git_id=identidad.id
                if resultado.estudiante_id is None and identidad is not None
                else None,
                papel=PapelAutoria.AUTOR.value,
                regla_atribucion=resultado.regla.value,
                confianza=resultado.confianza,
            )
        )
    bd.flush()
    return True


# --- Escritura del espejo ---


def ingerir_commits(
    bd: Session,
    *,
    repositorio: Repositorio,
    commits: Iterable[CommitGithub],
    origen: OrigenIngesta,
    rama: str | None,
    en_rama_por_defecto: bool,
    recibido_en: datetime | None = None,
    contexto: tuple[dict[int, Any], dict[str, Any]] | None = None,
) -> int:
    """Idempotente por `(repositorio_id, sha)`. Una fila ya presente solo se
    enriquece en sus campos nulos; nunca se reescriben `sha`,
    `fecha_committer`, `recibido_en` ni `origen_ingesta` (S10.2.4 regla 2).
    Devuelve cuantos commits eran nuevos."""
    ahora = ahora_utc()
    recibido_en = recibido_en or ahora
    contexto = contexto or contexto_curso(bd, repositorio.curso_id)
    nuevos = 0
    for c in commits:
        fila = (
            bd.query(Commit)
            .filter(Commit.repositorio_id == repositorio.id, Commit.sha == c.sha)
            .one_or_none()
        )
        autor_nuevo = False
        if fila is None:
            fila = Commit(
                repositorio_id=repositorio.id,
                sha=c.sha,
                parent_shas=list(c.parent_shas) if c.parent_shas is not None else None,
                n_padres=len(c.parent_shas) if c.parent_shas is not None else None,
                es_merge=c.parent_shas is not None and len(c.parent_shas) > 1,
                rama_detectada=rama,
                en_rama_por_defecto=en_rama_por_defecto,
                mensaje_resumen=(c.mensaje or "").splitlines()[0][:200] if c.mensaje else None,
                autor_nombre=c.autor_nombre,
                autor_email=c.autor_email,
                autor_github_user_id=c.autor_github_user_id,
                committer_github_user_id=c.committer_github_user_id,
                fecha_autor=c.fecha_autor,
                fecha_committer=c.fecha_committer,
                via_web=c.via_web,
                archivos_tocados=c.archivos_tocados,
                autor_es_bot=c.autor_es_bot,
                origen_ingesta=origen.value,
                recibido_en=recibido_en,
                ingresado_en=ahora,
                regla_atribucion=ReglaAtribucion.SIN_ATRIBUIR.value,
                motivo_exclusion=MotivoExclusionCommit.NINGUNO.value,
            )
            bd.add(fila)
            bd.flush()
            nuevos += 1
            # Un commit del payload de `push` es provisional: sin padres ni
            # `author.id` no se atribuye todavia, para no abrir una identidad
            # de Git que `compare` resolvera enseguida.
            autor_nuevo = c.parent_shas is not None
        else:
            if fila.parent_shas is None and c.parent_shas is not None:
                fila.parent_shas = list(c.parent_shas)
                fila.n_padres = len(c.parent_shas)
                fila.es_merge = len(c.parent_shas) > 1
                autor_nuevo = True
            if fila.autor_github_user_id is None and c.autor_github_user_id is not None:
                fila.autor_github_user_id = c.autor_github_user_id
                autor_nuevo = True
            if fila.committer_github_user_id is None:
                fila.committer_github_user_id = c.committer_github_user_id
            if fila.via_web is None:
                fila.via_web = c.via_web
            if fila.archivos_tocados is None:
                fila.archivos_tocados = c.archivos_tocados
            if fila.fecha_autor is None:
                fila.fecha_autor = c.fecha_autor
            if c.autor_es_bot:
                fila.autor_es_bot = True
            if en_rama_por_defecto:
                fila.en_rama_por_defecto = True
            if fila.huerfano:
                # Volvio a ser alcanzable (p. ej. se deshizo el push --force).
                fila.huerfano = False
                fila.huerfano_desde = None
        fila.motivo_exclusion = motivo_exclusion(
            n_padres=fila.n_padres,
            sha=fila.sha,
            commit_inicial_sha=repositorio.commit_inicial_sha,
            huerfano=fila.huerfano,
        ).value
        if autor_nuevo:
            atribuir_commit(bd, fila, repositorio, contexto, solo_si_mejora=True)
    bd.flush()
    return nuevos


def marcar_huerfanos(
    bd: Session, repositorio: Repositorio, shas: Iterable[str], *, desde: datetime
) -> int:
    """S10.2.3: los commits que desaparecen de la historia se conservan con
    `huerfano = true`; nunca se borran."""
    marcados = 0
    for fila in bd.query(Commit).filter(
        Commit.repositorio_id == repositorio.id,
        Commit.sha.in_(list(shas)),
        Commit.huerfano.is_(False),
    ):
        fila.huerfano = True
        fila.huerfano_desde = desde
        fila.en_rama_por_defecto = False
        fila.motivo_exclusion = MotivoExclusionCommit.HUERFANO.value
        marcados += 1
    bd.flush()
    return marcados


def _shas_conocidos(bd: Session, repositorio_id: uuid.UUID) -> frozenset[str]:
    return frozenset(
        s
        for (s,) in bd.query(Commit.sha).filter(
            Commit.repositorio_id == repositorio_id, Commit.huerfano.is_(False)
        )
    )


def _desde_payload(d: dict[str, Any]) -> CommitGithub:
    """Un commit del payload de `push`: sin padres ni `author.id` numerico
    (el `username` es un login y no se usa para atribuir)."""
    autor = d.get("author") or {}
    return CommitGithub(
        sha=str(d["id"]),
        parent_shas=None,
        autor_nombre=autor.get("name"),
        autor_email=autor.get("email"),
        autor_github_user_id=None,
        autor_es_bot=str(autor.get("username", "")).endswith("[bot]"),
        committer_github_user_id=None,
        fecha_autor=datetime.fromisoformat(str(d["timestamp"])),
        fecha_committer=datetime.fromisoformat(str(d["timestamp"])),
        mensaje=d.get("message"),
        via_web=None,
        archivos_tocados=sum(len(d.get(k) or []) for k in ("added", "removed", "modified")),
    )


# --- Webhooks: recepcion (S10.2.2, S6.8.2) ---

_TOPE_PAYLOAD = 64 * 1024


def registrar_entrega(
    bd: Session,
    *,
    delivery_id: str,
    evento: str,
    cuerpo: bytes,
    payload: dict[str, Any] | None,
    firma_valida: bool,
) -> EventoWebhook | None:
    """Persiste la cabecera siempre y el cuerpo truncado a 64 KB. `None` si la
    entrega ya estaba (reentrega de GitHub: cero filas nuevas)."""
    existente = bd.query(EventoWebhook.id).filter(EventoWebhook.delivery_id == delivery_id).first()
    if existente is not None:
        return None
    truncado = len(cuerpo) > _TOPE_PAYLOAD
    guardado = payload
    if truncado and payload is not None:
        # Lo que el procesamiento necesita sin el array de commits: la ingesta
        # completa llega de `compare` igual (S10.2.3).
        guardado = {
            k: payload.get(k)
            for k in (
                "ref",
                "before",
                "after",
                "forced",
                "created",
                "deleted",
                "action",
                "repository",
                "installation",
                "sender",
                "member",
            )
        }
        guardado["commits"] = []
    fila = EventoWebhook(
        delivery_id=delivery_id,
        evento=evento,
        accion=(payload or {}).get("action"),
        firma_valida=firma_valida,
        payload=guardado if firma_valida else None,
        payload_bytes=len(cuerpo),
        payload_truncado=truncado,
        recibido_en=ahora_utc(),
        estado=EstadoEventoWebhook.RECIBIDO.value
        if firma_valida
        else EstadoEventoWebhook.IGNORADO.value,
        error=None if firma_valida else "firma X-Hub-Signature-256 invalida o ausente",
    )
    bd.add(fila)
    bd.flush()
    return fila


# --- Webhooks: procesamiento (S10.2.2, S10.2.5) ---


class SinDestinoTodavia(Exception):
    def __init__(self, cuando: datetime) -> None:
        self.cuando = cuando
        super().__init__("evento sin destino todavia")


def resolver_destino(
    bd: Session, evento: EventoWebhook
) -> tuple[Repositorio | None, RepositorioBase | None]:
    """S10.2.5, cascada cerrada. El paso 3 (repositorio de operaciones) no
    aplica: la aplicacion no crea ese repositorio."""
    repositorio_gh = (evento.payload or {}).get("repository") or {}
    github_id = repositorio_gh.get("id")
    if github_id is not None:
        repo = bd.query(Repositorio).filter(Repositorio.github_repo_id == github_id).first()
        if repo is not None:
            return repo, None
        base = (
            bd.query(RepositorioBase)
            .filter(RepositorioBase.github_repo_id == github_id)
            .one_or_none()
        )
        if base is not None:
            return None, base
    nombre = repositorio_gh.get("name")
    installation_id = ((evento.payload or {}).get("installation") or {}).get("id")
    if nombre and installation_id is not None:
        curso_ids = [
            c for (c,) in bd.query(Curso.id).filter(Curso.github_installation_id == installation_id)
        ]
        repo = (
            bd.query(Repositorio)
            .filter(
                Repositorio.curso_id.in_(curso_ids),
                Repositorio.nombre == nombre,
                Repositorio.github_repo_id.is_(None),
            )
            .first()
        )
        if repo is not None and github_id is not None:
            # Carrera del aprovisionamiento masivo: el 201 aun no se persistio.
            repo.github_repo_id = github_id
            bd.flush()
            return repo, None
    return None, None


def procesar_evento(bd: Session, cliente: ClienteGitHub, *, evento: EventoWebhook) -> None:
    """Un manejador por par `(evento, accion)`; lo que no esta en la lista se
    marca `IGNORADO` sin error, para que una accion nueva de GitHub nunca rompa
    el receptor."""
    if evento.estado in (
        EstadoEventoWebhook.PROCESADO.value,
        EstadoEventoWebhook.IGNORADO.value,
        EstadoEventoWebhook.DESCARTADO_SIN_DESTINO.value,
    ):
        return
    ahora = ahora_utc()
    payload = evento.payload or {}
    if evento.evento in ("installation",):
        _terminar(evento, EstadoEventoWebhook.PROCESADO)
        return
    repositorio, base = resolver_destino(bd, evento)
    if base is not None:
        # S10.2.7: el base se reconoce y se excluye de toda metrica.
        evento.repositorio_base_id = base.id
        _terminar(evento, EstadoEventoWebhook.PROCESADO)
        return
    if repositorio is None:
        if evento.evento == "installation_repositories":
            _procesar_installation_repositories(bd, payload)
            _terminar(evento, EstadoEventoWebhook.PROCESADO)
            return
        if ahora - evento.recibido_en >= PLAZO_SIN_DESTINO:
            _terminar(evento, EstadoEventoWebhook.DESCARTADO_SIN_DESTINO)
            return
        evento.estado = EstadoEventoWebhook.SIN_DESTINO_PENDIENTE.value
        evento.motivo_no_resuelto = "ningún repositorio de la aplicación casa con el evento"
        bd.flush()
        transcurrido = ahora - evento.recibido_en
        espera = next((t for t in REINTENTOS_SIN_DESTINO if t > transcurrido), timedelta(hours=1))
        raise SinDestinoTodavia(evento.recibido_en + espera)
    evento.repositorio_id = repositorio.id
    if evento.evento == "push":
        _procesar_push(bd, cliente, repositorio=repositorio, evento=evento)
    elif evento.evento == "repository":
        _procesar_repository(bd, repositorio, payload)
    elif evento.evento == "member" and evento.accion == "added":
        _procesar_member_added(bd, repositorio, payload)
    elif evento.evento in ("create", "delete"):
        pass  # los hitos de rama salen del `push` que GitHub envia a la vez
    else:
        _terminar(evento, EstadoEventoWebhook.IGNORADO)
        return
    _terminar(evento, EstadoEventoWebhook.PROCESADO)


def _terminar(evento: EventoWebhook, estado: EstadoEventoWebhook) -> None:
    evento.estado = estado.value
    evento.procesado_en = ahora_utc()


def _procesar_push(
    bd: Session, cliente: ClienteGitHub, *, repositorio: Repositorio, evento: EventoWebhook
) -> None:
    payload = evento.payload or {}
    ref = str(payload.get("ref", ""))
    rama = ref.removeprefix("refs/heads/")
    if not ref.startswith("refs/heads/"):
        return  # empujes de etiquetas: no son commits nuevos
    before = str(payload.get("before", SHA_CEROS))
    after = str(payload.get("after", SHA_CEROS))
    push = bd.query(EventoPush).filter(EventoPush.delivery_id == evento.delivery_id).one_or_none()
    if push is None:
        push = EventoPush(
            repositorio_id=repositorio.id,
            delivery_id=evento.delivery_id,
            ref=ref,
            before_sha=before,
            after_sha=after,
            n_commits_payload=len(payload.get("commits") or []),
            forzado=bool(payload.get("forced")),
            recibido_en=evento.recibido_en,
        )
        bd.add(push)
        bd.flush()
    por_defecto = rama == (repositorio.rama_por_defecto or "main")
    contexto = contexto_curso(bd, repositorio.curso_id)
    # Primero el payload, como dato provisional y rapido (NFR-2.5-A).
    ingerir_commits(
        bd,
        repositorio=repositorio,
        commits=[_desde_payload(d) for d in payload.get("commits") or []],
        origen=OrigenIngesta.WEBHOOK,
        rama=rama,
        en_rama_por_defecto=por_defecto,
        recibido_en=evento.recibido_en,
        contexto=contexto,
    )
    decision = decidir_relleno(before=before, after=after)
    if decision == "RAMA_BORRADA":
        push.completado = True
        bd.flush()
        return
    curso = bd.get(Curso, repositorio.curso_id)
    assert curso is not None and curso.github_org_login and curso.github_installation_id
    token = cliente.obtener_token_instalacion(curso.github_installation_id)
    org, repo = curso.github_org_login, _nombre_repo(repositorio)
    if decision == "RECORRIDO":
        listado = cliente.listar_commits_rama(
            org, repo, rama, token, conocidos=_shas_conocidos(bd, repositorio.id)
        )
        ingerir_commits(
            bd,
            repositorio=repositorio,
            commits=listado.commits,
            origen=OrigenIngesta.RECORRIDO,
            rama=rama,
            en_rama_por_defecto=por_defecto,
            recibido_en=evento.recibido_en,
            contexto=contexto,
        )
        push.completado = not listado.truncado
    else:
        comparacion = cliente.comparar(org, repo, before, after, token)
        ingerir_commits(
            bd,
            repositorio=repositorio,
            commits=comparacion.commits,
            origen=OrigenIngesta.RELLENO_COMPARE,
            rama=rama,
            en_rama_por_defecto=por_defecto,
            recibido_en=evento.recibido_en,
            contexto=contexto,
        )
        push.completado = not comparacion.truncado
        if comparacion.estado == "diverged":
            push.divergido = True
            push.n_commits_huerfanos = _marcar_descartados(
                bd,
                cliente,
                org=org,
                repo=repo,
                token=token,
                repositorio=repositorio,
                cabeza_nueva=after,
                cabeza_vieja=before,
            )
    if not push.completado:
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="INGESTA_INCOMPLETA",
            severidad="INFORMATIVA",
            sujeto_tipo="REPOSITORIO",
            curso_id=repositorio.curso_id,
            sujeto_id=repositorio.id,
            detalle={"ref": ref, "motivo": "se agotó el tope de 30 páginas"},
        )
    bd.flush()


def _marcar_descartados(
    bd: Session,
    cliente: ClienteGitHub,
    *,
    org: str,
    repo: str,
    token: str,
    repositorio: Repositorio,
    cabeza_nueva: str,
    cabeza_vieja: str,
) -> int:
    """Los commits alcanzables desde la cabeza vieja y no desde la nueva son
    los que la reescritura descarto: `compare/{nueva}...{vieja}`."""
    try:
        descartados = cliente.comparar(org, repo, cabeza_nueva, cabeza_vieja, token)
    except RechazoProveedorGithub:
        return 0  # la cabeza vieja ya no existe en GitHub: el barrido lo cierra
    return marcar_huerfanos(
        bd, repositorio, [c.sha for c in descartados.commits], desde=ahora_utc()
    )


def _procesar_repository(bd: Session, repositorio: Repositorio, payload: dict[str, Any]) -> None:
    """A-110, A-168, RG-013. La aplicacion nunca archiva por su cuenta: aqui
    solo se refleja lo que alguien hizo en GitHub."""
    accion = payload.get("action")
    datos = payload.get("repository") or {}
    antes = repositorio.estado
    if accion == "archived":
        repositorio.estado = EstadoRepositorio.ARCHIVADO.value
    elif accion == "unarchived" and repositorio.estado == EstadoRepositorio.ARCHIVADO.value:
        # El predicado de OPERATIVO lo reevalua la proxima reconciliacion.
        repositorio.estado = EstadoRepositorio.DEGRADADO.value
    elif accion == "renamed":
        repositorio.full_name = datos.get("full_name", repositorio.full_name)
        repositorio.nombre = datos.get("name", repositorio.nombre)
        repositorio.url_html = datos.get("html_url", repositorio.url_html)
    elif accion in ("deleted", "transferred"):
        repositorio.estado = EstadoRepositorio.INACCESIBLE.value
        repositorio.motivo = (
            MotivoInaccesible.BORRADO_EN_GITHUB.value
            if accion == "deleted"
            else MotivoInaccesible.TRANSFERIDO_FUERA_DE_LA_ORG.value
        )
    repositorio.actualizado_en = ahora_utc()
    bd.flush()
    if antes != repositorio.estado:
        registrar_bitacora(
            bd,
            accion="REPOSITORIO_ESTADO",
            entidad="repositorio",
            entidad_id=str(repositorio.id),
            curso_id=repositorio.curso_id,
            antes={"estado": antes},
            despues={"estado": repositorio.estado, "origen": f"webhook repository/{accion}"},
        )


def _procesar_member_added(bd: Session, repositorio: Repositorio, payload: dict[str, Any]) -> None:
    """S10.2.2: la unica senal documentada de que el estudiante acepto."""
    github_user_id = (payload.get("member") or {}).get("id")
    if github_user_id is None:
        return
    cuenta = (
        bd.query(CuentaGithub).filter(CuentaGithub.github_user_id == github_user_id).one_or_none()
    )
    if cuenta is None:
        return
    for acceso in bd.query(AccesoRepositorio).filter(
        AccesoRepositorio.repositorio_id == repositorio.id,
        AccesoRepositorio.cuenta_github_id == cuenta.id,
        AccesoRepositorio.estado.in_(
            [EstadoAccesoRepositorio.INVITADO.value, EstadoAccesoRepositorio.POR_INVITAR.value]
        ),
    ):
        acceso.estado = EstadoAccesoRepositorio.ACEPTADO.value
        acceso.aceptado_en = ahora_utc()
        acceso.actualizado_en = ahora_utc()
    bd.flush()


def _procesar_installation_repositories(bd: Session, payload: dict[str, Any]) -> None:
    """Un repositorio que sale del alcance de la instalacion pasa a
    `INACCESIBLE` con su motivo; conserva toda su historia."""
    if payload.get("action") != "removed":
        return
    for datos in payload.get("repositories_removed") or []:
        repo = bd.query(Repositorio).filter(Repositorio.github_repo_id == datos.get("id")).first()
        if repo is not None:
            repo.estado = EstadoRepositorio.INACCESIBLE.value
            repo.motivo = MotivoInaccesible.FUERA_DEL_ALCANCE_DE_LA_INSTALACION.value
    bd.flush()


# --- Reconciliacion y barrido (S10.2.3, S6.8.4) ---


def _cursor(bd: Session, curso_id: uuid.UUID, referencia: str) -> CursorSincronizacion:
    fila = (
        bd.query(CursorSincronizacion)
        .filter(
            CursorSincronizacion.curso_id == curso_id,
            CursorSincronizacion.recurso == RECURSO_COMMITS,
            CursorSincronizacion.referencia == referencia,
        )
        .one_or_none()
    )
    if fila is None:
        fila = CursorSincronizacion(
            curso_id=curso_id, recurso=RECURSO_COMMITS, referencia=referencia
        )
        bd.add(fila)
        bd.flush()
    return fila


def referencia_backfill(repositorio: Repositorio) -> str:
    return f"repo:{repositorio.github_repo_id}:backfill"


def reconciliar_repositorio(
    bd: Session,
    cliente: ClienteGitHub,
    *,
    repositorio: Repositorio,
    org: str,
    token: str,
    origen: OrigenIngesta = OrigenIngesta.RECONCILIACION,
) -> int:
    """Por cada rama (tope 50): lista condicional por ETag; un `304` cierra la
    rama sin escribir nada. Si la cabeza guardada ya no es antecesora de la
    nueva, `compare` lo confirma y se marcan los huerfanos. `ultimo_head_sha`
    solo avanza cuando el recorrido de esa rama termina con exito."""
    nombre = _nombre_repo(repositorio)
    contexto = contexto_curso(bd, repositorio.curso_id)
    ramas = cliente.listar_ramas(org, nombre, token)[:MAX_RAMAS]
    por_defecto = repositorio.rama_por_defecto or "main"
    nuevos = 0
    for ref, cabeza in ramas:
        cursor = _cursor(bd, repositorio.curso_id, f"repo:{repositorio.github_repo_id}:{ref}")
        listado = cliente.listar_commits_rama(
            org,
            nombre,
            ref,
            token,
            etag=cursor.etag if origen == OrigenIngesta.RECONCILIACION else None,
            conocidos=_shas_conocidos(bd, repositorio.id),
        )
        if not listado.no_modificado:
            nuevos += ingerir_commits(
                bd,
                repositorio=repositorio,
                commits=listado.commits,
                origen=origen,
                rama=ref,
                en_rama_por_defecto=ref == por_defecto,
                contexto=contexto,
            )
            anterior = cursor.ultimo_head_sha
            if anterior and anterior != cabeza:
                try:
                    estado = cliente.comparar(org, nombre, anterior, cabeza, token).estado
                except RechazoProveedorGithub:
                    estado = "diverged"
                if estado == "diverged":
                    _marcar_descartados(
                        bd,
                        cliente,
                        org=org,
                        repo=nombre,
                        token=token,
                        repositorio=repositorio,
                        cabeza_nueva=cabeza,
                        cabeza_vieja=anterior,
                    )
            if listado.truncado:
                cursor.estado = "TRUNCADO"
            else:
                cursor.ultimo_head_sha = cabeza
                cursor.etag = listado.etag
                cursor.estado = "AL_DIA"
        cursor.ultimo_exito_en = ahora_utc()
        cursor.ultimo_error = None
    bd.flush()
    return nuevos


def repositorios_en_ingesta(bd: Session, curso: Curso) -> list[Repositorio]:
    """S10.2.8, la unica funcion que usan los tres trabajos de sondeo."""
    ahora = ahora_utc()
    salida = []
    for repo, tarea in (
        bd.query(Repositorio, Tarea)
        .join(Tarea, Tarea.id == Repositorio.tarea_id)
        .filter(Repositorio.curso_id == curso.id, Repositorio.github_repo_id.isnot(None))
        .order_by(Repositorio.creado_en)
    ):
        ultima = (
            bd.query(FechaEfectiva.due_at_utc)
            .filter(
                FechaEfectiva.sujeto_id == repo.sujeto_id,
                FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
                FechaEfectiva.due_at_utc.isnot(None),
            )
            .order_by(FechaEfectiva.due_at_utc.desc())
            .first()
        )
        if repositorio_en_ingesta(
            estado_repositorio=repo.estado,
            estado_tarea=tarea.estado,
            ultima_fecha=ultima[0] if ultima else None,
            ahora=ahora,
        ):
            salida.append(repo)
    return salida


def rellenar_hacia_atras(
    bd: Session, cliente: ClienteGitHub, *, repositorio: Repositorio, org: str, token: str
) -> bool:
    """S10.2.6: una sola vez por repositorio, la rama por defecto entera desde
    su creacion. Devuelve `True` si quedo completo."""
    cursor = _cursor(bd, repositorio.curso_id, referencia_backfill(repositorio))
    if cursor.ultimo_backfill_en is not None:
        return True
    listado = cliente.listar_commits_rama(
        org, _nombre_repo(repositorio), repositorio.rama_por_defecto or "main", token
    )
    ingerir_commits(
        bd,
        repositorio=repositorio,
        commits=listado.commits,
        origen=OrigenIngesta.BACKFILL_INICIAL,
        rama=repositorio.rama_por_defecto,
        en_rama_por_defecto=True,
    )
    if listado.truncado:
        cursor.estado = "TRUNCADO"
        return False
    cursor.ultimo_backfill_en = ahora_utc()
    cursor.estado = "AL_DIA"
    bd.flush()
    return True


def barrido_curso(bd: Session, cliente: ClienteGitHub, *, curso: Curso) -> int:
    """Diario: relleno hacia atras pendiente y reconciliacion completa (sin
    ETag) de cada repositorio en ingesta. Cuando todos los repositorios con
    historia tienen su relleno, se escribe `curso.ingesta_actividad_desde`."""
    if curso.github_org_login is None or curso.github_installation_id is None:
        return 0
    token = cliente.obtener_token_instalacion(curso.github_installation_id)
    repositorios = repositorios_en_ingesta(bd, curso)
    todos_completos = True
    for repo in repositorios:
        try:
            completo = rellenar_hacia_atras(
                bd, cliente, repositorio=repo, org=curso.github_org_login, token=token
            )
            reconciliar_repositorio(
                bd,
                cliente,
                repositorio=repo,
                org=curso.github_org_login,
                token=token,
                origen=OrigenIngesta.BARRIDO,
            )
        except RechazoProveedorGithub:
            completo = False
        todos_completos = todos_completos and completo
    if todos_completos and repositorios and curso.ingesta_actividad_desde is None:
        curso.ingesta_actividad_desde = min(
            (r.listo_en or r.creado_en for r in repositorios), default=ahora_utc()
        )
    bd.flush()
    return len(repositorios)


def reconciliar_curso(bd: Session, cliente: ClienteGitHub, *, curso: Curso, tope: int = 200) -> int:
    """Cada 15 minutos: hasta 200 repositorios por ciclo, los menos recientes
    primero (S10.2.1)."""
    if curso.github_org_login is None or curso.github_installation_id is None:
        return 0
    token = cliente.obtener_token_instalacion(curso.github_installation_id)
    repositorios = repositorios_en_ingesta(bd, curso)
    ultimo = {
        c.referencia: c.ultimo_exito_en
        for c in bd.query(CursorSincronizacion).filter(
            CursorSincronizacion.curso_id == curso.id,
            CursorSincronizacion.recurso == RECURSO_COMMITS,
        )
    }

    def _antiguedad(repo: Repositorio) -> datetime:
        clave = f"repo:{repo.github_repo_id}:{repo.rama_por_defecto or 'main'}"
        return ultimo.get(clave) or datetime.min.replace(tzinfo=ahora_utc().tzinfo)

    for repo in sorted(repositorios, key=_antiguedad)[:tope]:
        reconciliar_repositorio(
            bd, cliente, repositorio=repo, org=curso.github_org_login, token=token
        )
    return min(len(repositorios), tope)


# --- Lo que consume la captura de versiones (F4) ---


def espejo_fiable(bd: Session, repositorio: Repositorio) -> bool:
    """El espejo solo se usa como fuente del commit de cierre cuando ya tuvo
    al menos una lectura completa con exito (S10.7.7)."""
    return (
        bd.query(CursorSincronizacion.id)
        .filter(
            CursorSincronizacion.curso_id == repositorio.curso_id,
            CursorSincronizacion.recurso == RECURSO_COMMITS,
            CursorSincronizacion.referencia == referencia_backfill(repositorio),
            CursorSincronizacion.ultimo_backfill_en.isnot(None),
        )
        .first()
        is not None
    )


def commit_de_cierre_en_espejo(
    bd: Session, repositorio: Repositorio, corte: datetime
) -> CommitCierre | None:
    """A-102 paso 1: `MAX(fecha_committer) <= corte` en la rama por defecto,
    sin huerfanos. El commit inicial lo trata el dominio (`SIN_COMMITS`)."""
    fila = (
        bd.query(Commit)
        .filter(
            Commit.repositorio_id == repositorio.id,
            Commit.en_rama_por_defecto.is_(True),
            Commit.huerfano.is_(False),
            Commit.fecha_committer <= corte,
        )
        .order_by(Commit.fecha_committer.desc())
        .first()
    )
    if fila is None:
        return None
    return CommitCierre(
        sha=fila.sha,
        tree_sha=None,
        fecha_committer=fila.fecha_committer,
        fecha_autor=fila.fecha_autor,
        mensaje=fila.mensaje_resumen,
    )


def commits_posteriores_al_cierre(bd: Session, repositorio_id: uuid.UUID, corte: datetime) -> int:
    """S9.8.3: derivado del espejo, sin coste de API ni fila nueva."""
    return (
        bd.query(Commit)
        .filter(
            Commit.repositorio_id == repositorio_id,
            Commit.en_rama_por_defecto.is_(True),
            Commit.motivo_exclusion == MotivoExclusionCommit.NINGUNO.value,
            Commit.fecha_committer > corte,
        )
        .count()
    )


def repositorio_de_sujeto(bd: Session, sujeto_id: uuid.UUID) -> Repositorio | None:
    return (
        bd.query(Repositorio)
        .filter(Repositorio.sujeto_id == sujeto_id, Repositorio.github_repo_id.isnot(None))
        .order_by(Repositorio.creado_en.desc())
        .first()
    )


def _sujeto(bd: Session, sujeto_id: uuid.UUID) -> Sujeto | None:
    return bd.get(Sujeto, sujeto_id)


# --- Correccion docente de identidades de Git (S10.3.4) ---


class RechazoIdentidad(Exception):
    def __init__(self, motivo: str, detalle: str) -> None:
        self.motivo = motivo
        self.detalle = detalle
        super().__init__(detalle)


_REGLAS_CORREGIBLES = (
    ReglaAtribucion.SIN_ATRIBUIR.value,
    ReglaAtribucion.IDENTIDAD_DOCENTE.value,
)
_REGLAS_ALTAS = (ReglaAtribucion.AUTOR_GITHUB.value, ReglaAtribucion.EMAIL_NOREPLY.value)


def commits_de_identidad(bd: Session, identidad: IdentidadGit) -> list[Commit]:
    """Los commits del mismo correo en el repositorio: la correccion es por
    identidad, no por commit, y alcanza a los pasados y a los futuros."""
    return [
        c
        for c in bd.query(Commit).filter(Commit.repositorio_id == identidad.repositorio_id)
        if normalizar_email(c.autor_email) == identidad.email_normalizado
    ]


def resolver_identidad(
    bd: Session,
    *,
    identidad: IdentidadGit,
    estudiante_id: uuid.UUID | None,
    no_es_estudiante: bool,
    propagar_a: list[uuid.UUID],
    actor_usuario_id: uuid.UUID,
    confirmacion: str | None = None,
) -> IdentidadGit:
    """Append-only: cierra la fila vigente y crea otra. Reescribe la autoria
    solo de los commits que las reglas 1 a 3 no habian resuelto; nunca pisa
    `AUTOR_GITHUB` ni `EMAIL_NOREPLY`. La propagacion se aplica solo a los
    repositorios marcados, cada uno con su propia fila. Nunca toca un
    `mapeo_github`."""
    if (estudiante_id is None) == (not no_es_estudiante):
        raise RechazoIdentidad(
            "DESTINO_INVALIDO", "Elige un estudiante o marca «no es estudiante», no ambos."
        )
    if estudiante_id is not None:
        estudiante = bd.get(Estudiante, estudiante_id)
        if estudiante is None or estudiante.curso_id != identidad.curso_id:
            raise RechazoIdentidad("ESTUDIANTE_AJENO", "Ese estudiante no es de este curso.")
    ya_resueltos = [
        c for c in commits_de_identidad(bd, identidad) if c.regla_atribucion in _REGLAS_ALTAS
    ]
    if ya_resueltos and len((confirmacion or "").strip()) < 10:
        raise RechazoIdentidad(
            "CONFIRMACION_REQUERIDA",
            f"Este correo ya tiene {len(ya_resueltos)} commits atribuidos automáticamente con "
            "confianza alta; esos no cambiarán. Escribe por qué igualmente quieres asociarlo.",
        )
    nueva = _aplicar_resolucion(
        bd,
        identidad,
        estudiante_id=estudiante_id,
        no_es_estudiante=no_es_estudiante,
        actor_usuario_id=actor_usuario_id,
        confirmacion=confirmacion,
    )
    # S10.3.4 regla 5: recomputo inmediato de los repositorios afectados.
    from app.adaptadores import metricas_repo

    metricas_repo.encolar(
        bd,
        curso_id=identidad.curso_id,
        motivo=f"identidad:{identidad.id}:{ahora_utc().isoformat()}",
    )
    for repositorio_id in propagar_a:
        destino = (
            bd.query(IdentidadGit)
            .filter(
                IdentidadGit.curso_id == identidad.curso_id,
                IdentidadGit.repositorio_id == repositorio_id,
                IdentidadGit.email_normalizado == identidad.email_normalizado,
                IdentidadGit.estado != EstadoIdentidadGit.SUPERSEDIDA.value,
            )
            .one_or_none()
        )
        if destino is not None:
            _aplicar_resolucion(
                bd,
                destino,
                estudiante_id=estudiante_id,
                no_es_estudiante=no_es_estudiante,
                actor_usuario_id=actor_usuario_id,
                confirmacion=confirmacion,
                propagada_desde=identidad.repositorio_id,
            )
    return nueva


def _aplicar_resolucion(
    bd: Session,
    identidad: IdentidadGit,
    *,
    estudiante_id: uuid.UUID | None,
    no_es_estudiante: bool,
    actor_usuario_id: uuid.UUID,
    confirmacion: str | None,
    propagada_desde: uuid.UUID | None = None,
) -> IdentidadGit:
    ahora = ahora_utc()
    antes = {"estado": identidad.estado, "estudiante_id": str(identidad.estudiante_id or "")}
    identidad.estado = EstadoIdentidadGit.SUPERSEDIDA.value
    identidad.vigente_hasta = ahora
    bd.flush()
    nueva = IdentidadGit(
        curso_id=identidad.curso_id,
        repositorio_id=identidad.repositorio_id,
        email_normalizado=identidad.email_normalizado,
        email_visto=identidad.email_visto,
        nombre_visto=identidad.nombre_visto,
        nombre_visto_ultimo=identidad.nombre_visto_ultimo,
        estado=(
            EstadoIdentidadGit.NO_ES_ESTUDIANTE.value
            if no_es_estudiante
            else EstadoIdentidadGit.RESUELTA.value
        ),
        estudiante_id=estudiante_id,
        resuelta_por=actor_usuario_id,
        resuelta_en=ahora,
        vigente_desde=ahora,
    )
    bd.add(nueva)
    bd.flush()
    repositorio = bd.get(Repositorio, identidad.repositorio_id)
    assert repositorio is not None
    contexto = contexto_curso(bd, repositorio.curso_id)
    for commit in commits_de_identidad(bd, nueva):
        if commit.regla_atribucion in _REGLAS_CORREGIBLES:
            atribuir_commit(bd, commit, repositorio, contexto, solo_si_mejora=False)
    registrar_bitacora(
        bd,
        accion="IDENTIDAD_GIT_RESUELTA",
        entidad="identidad_git",
        entidad_id=str(nueva.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=identidad.curso_id,
        antes=antes,
        despues={
            "estado": nueva.estado,
            "estudiante_id": str(estudiante_id) if estudiante_id else None,
            "repositorio_id": str(identidad.repositorio_id),
            "propagada_desde": str(propagada_desde) if propagada_desde else None,
            "confirmacion": confirmacion,
        },
    )
    return nueva


def candidatos_propagacion(bd: Session, identidad: IdentidadGit) -> list[tuple[IdentidadGit, int]]:
    """Los demas repositorios del curso donde aparece el mismo correo, con su
    numero de commits. La propuesta nunca se aplica sola: correos como
    `root@localhost` aparecen en repositorios de estudiantes distintos."""
    salida = []
    for otra in bd.query(IdentidadGit).filter(
        IdentidadGit.curso_id == identidad.curso_id,
        IdentidadGit.email_normalizado == identidad.email_normalizado,
        IdentidadGit.repositorio_id != identidad.repositorio_id,
        IdentidadGit.estado != EstadoIdentidadGit.SUPERSEDIDA.value,
    ):
        salida.append((otra, len(commits_de_identidad(bd, otra))))
    return salida
