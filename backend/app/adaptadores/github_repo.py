"""Orquesta la vinculacion con GitHub y el equipo docente (SPEC 04 S4.6,
SPEC 06 S6.2, S6.10; SPEC 02 S2.9.3). Reemplaza el stub no-op de Etapa P2."""

from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.cliente_github import (
    ClienteGitHub,
    StateInstalacionInvalido,
    emitir_state_instalacion,
    verificar_state_instalacion,
)
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_github import (
    EquipoGithubCurso,
    InstalacionGithub,
    IntentoInstalacionGithub,
)
from app.adaptadores.modelos_identidad import Usuario
from app.dominio.estados import (
    EstadoEquipoGithub,
    EstadoMembresia,
    ViaEfectivaEquipoGithub,
)
from app.dominio.vinculacion_github import (
    MotivoRechazoInstalacion,
    RechazoInstalacion,
    es_cuenta_de_organizacion,
)
from app.infraestructura.cerrojos import bloquear_equipo

_NOMBRE_EQUIPO_DOCENTES = "docentes"
_VENTANA_ADOPCION = timedelta(minutes=30)
_VENTANA_AUTO_ADOPCION_POR_SUGERENCIA = timedelta(hours=24)


def iniciar_instalacion(
    bd: Session,
    *,
    curso: Curso,
    usuario: Usuario,
    signing_key: str,
    org_login_sugerido: str | None = None,
) -> str:
    """S4.6.1: persiste el intento *antes* de salir a GitHub (S4.6.5 "ley del
    intento antes de la llamada"), y emite el `state` de 15 minutos.
    `org_login_sugerido` es una pista opcional del profesor (no hay parametro
    documentado de GitHub para preseleccionar la organizacion, S6.2 nota) que
    solo sirve para la auto-adopcion de `verificar_instalacion_github`."""
    jti = secrets.token_urlsafe(16)
    bd.add(
        IntentoInstalacionGithub(
            curso_id=curso.id,
            usuario_id=usuario.id,
            jti=jti,
            org_login_sugerido=org_login_sugerido,
            emitido_en=ahora_utc(),
        )
    )
    bd.flush()
    return emitir_state_instalacion(
        signing_key=signing_key, curso_id=str(curso.id), usuario_id=str(usuario.id), jti=jti
    )


def resolver_curso_por_state(bd: Session, *, signing_key: str, state: str) -> Curso:
    """S4.6.3: el `state` resuelve el curso -- el profesor no copia ningun
    identificador. `jti` de un solo uso: un segundo canje del mismo state
    falla igual que uno caducado (A-058)."""
    try:
        reclamaciones = verificar_state_instalacion(signing_key=signing_key, state=state)
    except StateInstalacionInvalido as exc:
        raise RechazoInstalacion(MotivoRechazoInstalacion.STATE_INVALIDO) from exc
    intento = (
        bd.query(IntentoInstalacionGithub)
        .filter(IntentoInstalacionGithub.jti == reclamaciones.jti)
        .one_or_none()
    )
    if intento is None or intento.consumido_en is not None:
        raise RechazoInstalacion(MotivoRechazoInstalacion.STATE_INVALIDO)
    intento.consumido_en = ahora_utc()
    bd.flush()
    curso = bd.query(Curso).filter(Curso.id == uuid.UUID(reclamaciones.curso_id)).one_or_none()
    if curso is None:
        raise RechazoInstalacion(MotivoRechazoInstalacion.STATE_INVALIDO)
    return curso


def vincular_instalacion(
    bd: Session, cliente: ClienteGitHub, *, curso: Curso, installation_id: int
) -> InstalacionGithub:
    """S4.6.3, S6.2.4: la clave es `github_org_id`, nunca el `login` ni el
    `installation_id`. Reinstalar sobre la misma organizacion sustituye el
    `installation_id` en la misma transaccion, sin tocar repositorios."""
    info = cliente.obtener_instalacion(installation_id)

    if not es_cuenta_de_organizacion(
        existe_como_organizacion=cliente.existe_como_organizacion(info.account_login),
    ):
        raise RechazoInstalacion(MotivoRechazoInstalacion.CUENTA_PERSONAL)

    ocupante = (
        bd.query(Curso)
        .filter(Curso.github_org_id == info.account_id, Curso.id != curso.id)
        .one_or_none()
    )
    if ocupante is not None:
        raise RechazoInstalacion(
            MotivoRechazoInstalacion.ORGANIZACION_YA_VINCULADA, detalle=ocupante.nombre
        )

    ahora = ahora_utc()
    fila = bd.query(InstalacionGithub).filter(InstalacionGithub.curso_id == curso.id).one_or_none()
    if fila is None:
        fila = InstalacionGithub(
            installation_id=installation_id,
            curso_id=curso.id,
            org_login=info.account_login,
            org_id=info.account_id,
            repository_selection=info.repository_selection,
            permisos_pendientes=False,
            suspendida=info.suspendida,
            actualizada_en=ahora,
        )
        bd.add(fila)
    elif fila.installation_id != installation_id:
        anterior = fila.installation_id
        fila.installation_id = installation_id
        fila.org_login = info.account_login
        fila.org_id = info.account_id
        fila.repository_selection = info.repository_selection
        fila.suspendida = info.suspendida
        fila.actualizada_en = ahora
        registrar_bitacora(
            bd,
            accion="INSTALACION_GITHUB_SUSTITUIDA",
            entidad="instalacion_github",
            entidad_id=str(fila.id),
            curso_id=curso.id,
            antes={"installation_id": anterior},
            despues={"installation_id": installation_id},
        )
    else:
        fila.org_login = info.account_login
        fila.repository_selection = info.repository_selection
        fila.suspendida = info.suspendida
        fila.actualizada_en = ahora

    curso.github_org_login = info.account_login
    curso.github_org_id = info.account_id
    curso.github_installation_id = installation_id
    if curso.estado == "BORRADOR":
        curso.estado = "VINCULANDO"
    curso.actualizado_en = ahora
    bd.flush()
    return fila


def crear_y_poblar_equipo_docente(
    bd: Session, cliente: ClienteGitHub, *, curso: Curso, instalacion: InstalacionGithub
) -> EquipoGithubCurso:
    """S4.6.2, S6.10.3: el equipo `docentes` se crea antes que el primer
    repositorio de estudiante, con lectura (`pull`) via una sola llamada por
    repositorio (eso llega con P7/P8; aqui solo se crea y se puebla)."""
    token = cliente.obtener_token_instalacion(instalacion.installation_id)
    assert curso.github_org_login is not None

    equipo = (
        bd.query(EquipoGithubCurso).filter(EquipoGithubCurso.curso_id == curso.id).one_or_none()
    )
    ahora = ahora_utc()
    if equipo is None:
        team_id, team_slug = cliente.crear_equipo(
            curso.github_org_login, _NOMBRE_EQUIPO_DOCENTES, token
        )
        equipo = EquipoGithubCurso(
            curso_id=curso.id,
            team_id=team_id,
            team_slug=team_slug,
            estado=EstadoEquipoGithub.ACTIVO.value,
            via_efectiva=ViaEfectivaEquipoGithub.TEAM.value,
            creado_en=ahora,
        )
        bd.add(equipo)
        bd.flush()
    assert equipo.team_slug is not None

    miembros_activos = (
        bd.query(MembresiaCurso)
        .filter(
            MembresiaCurso.curso_id == curso.id,
            MembresiaCurso.estado == EstadoMembresia.ACTIVA.value,
        )
        .all()
    )
    for membresia in miembros_activos:
        sincronizar_acceso_de_un_docente(bd, cliente, curso=curso, membresia=membresia)
    bd.flush()
    return equipo


def sincronizar_acceso_de_un_docente(
    bd: Session, cliente: ClienteGitHub, *, curso: Curso, membresia: MembresiaCurso
) -> None:
    """Incorpora a UN docente (nuevo o reincorporado) sin tocar a los demas
    (S2.9.6, S6.10.3): un ayudante nuevo no toca ningun repositorio."""
    from app.adaptadores.acceso_docente_repo import motivo_no_elegible

    bloquear_equipo(bd)
    bd.refresh(membresia)
    if curso.github_org_login is None or curso.github_installation_id is None:
        return
    usuario = bd.query(Usuario).populate_existing().filter(Usuario.id == membresia.usuario_id).one()
    if not usuario.activo or membresia.estado != "ACTIVA":
        revocar_acceso_tres_planos(bd, cliente, membresia_id=membresia.id)
        return
    if not usuario.github_login_declarado or usuario.consentimiento_github_en is None:
        membresia.org_github_estado = (
            "SIN_CONSENTIMIENTO" if usuario.github_login_declarado else "NO_APLICA"
        )
        bd.flush()
        return
    info = cliente.obtener_cuenta_usuario(usuario.github_login_declarado)
    motivo = (
        "La cuenta de GitHub ya no está disponible."
        if info is None
        else motivo_no_elegible(
            bd, usuario=usuario, github_id=info.github_user_id, login=info.login
        )
    )
    if (
        info is not None
        and usuario.cuenta_github_id is not None
        and usuario.cuenta_github_id != info.github_user_id
    ):
        motivo = (
            "El nombre de GitHub ahora corresponde a otra cuenta. "
            "Declara nuevamente tu identidad en Perfil."
        )
    if motivo:
        membresia.org_github_estado = "ERROR"
        membresia.org_github_ultimo_error = motivo
        bd.flush()
        return
    if info is not None:
        usuario.cuenta_github_id = info.github_user_id
    equipo = bd.query(EquipoGithubCurso).filter_by(curso_id=curso.id).one_or_none()
    if equipo is None or equipo.team_slug is None:
        membresia.org_github_estado = "ERROR"
        membresia.org_github_ultimo_error = "Falta configurar el equipo docente de GitHub."
        bd.flush()
        return
    token = cliente.obtener_token_instalacion(curso.github_installation_id)
    login = usuario.github_login_declarado
    estado = cliente.obtener_membresia_organizacion(curso.github_org_login, login, token)
    if estado is None:
        # Persistir la intencion antes de la llamada permite reintentar sin
        # confundir un alta propia con una membresia preexistente.
        membresia.org_github_alta_por_app = True
        bd.flush()
        cliente.agregar_miembro_organizacion(curso.github_org_login, login, token)
        membresia.org_github_invitada_en = ahora_utc()
    cliente.agregar_miembro_equipo(curso.github_org_login, equipo.team_slug, login, token)
    membresia.org_github_estado = "ACTIVA" if estado == "active" else "PENDIENTE"
    if estado == "active":
        membresia.org_github_activa_en = ahora_utc()
    membresia.org_github_ultimo_error = None
    bd.flush()


def revocar_acceso_tres_planos(
    bd: Session,
    cliente: ClienteGitHub,
    *,
    membresia_id: uuid.UUID,
    login_anterior: str | None = None,
    alta_anterior_por_app: bool | None = None,
) -> None:
    """Retira la identidad capturada al encolar, aunque Perfil ya haya cambiado."""
    from app.adaptadores.modelos_aprovisionamiento import Repositorio
    from app.adaptadores.modelos_github import AccesoDocenteRepositorio

    membresia = bd.get(MembresiaCurso, membresia_id)
    if membresia is None:
        return
    curso = bd.get(Curso, membresia.curso_id)
    usuario = bd.get(Usuario, membresia.usuario_id)
    assert curso is not None and usuario is not None
    login = login_anterior or usuario.github_login_declarado
    if not login or not curso.github_org_login or curso.github_installation_id is None:
        return
    alta = (
        membresia.org_github_alta_por_app
        if alta_anterior_por_app is None
        else alta_anterior_por_app
    )
    token = cliente.obtener_token_instalacion(curso.github_installation_id)
    equipo = bd.query(EquipoGithubCurso).filter_by(curso_id=curso.id).one_or_none()
    if equipo is not None and equipo.team_slug:
        cliente.quitar_miembro_equipo(curso.github_org_login, equipo.team_slug, login, token)
    for acceso in bd.query(AccesoDocenteRepositorio).filter_by(membresia_id=membresia.id).all():
        repo = bd.get(Repositorio, acceso.repositorio_id)
        if repo is not None:
            cliente.quitar_colaborador_repo(curso.github_org_login, repo.nombre, login, token)
            acceso.estado = "REVOCADO"
            acceso.revocado_en = ahora_utc()
    if alta:
        cliente.quitar_miembro_organizacion(curso.github_org_login, login, token)
    if login == usuario.github_login_declarado or usuario.github_login_declarado is None:
        membresia.org_github_alta_por_app = False
        membresia.org_github_estado = "NO_APLICA"
    bd.flush()


def instalaciones_huerfanas_adoptables(
    bd: Session, *, usuario: Usuario, curso_id: uuid.UUID
) -> list[InstalacionGithub]:
    """S4.6.5 condicion (b): un intento reciente (30 min) de ESE usuario para
    ESTE curso habilita el bloque "Instalaciones sin curso". La condicion (a)
    (el `sender` del webhook coincide con el GitHub declarado) no se
    implementa en esta etapa: no hay receptor de webhooks todavia en el
    codigo (ninguna ruta consume `GITHUB_WEBHOOK_SECRET`); la via de deteccion
    de S4.6.4/S4.6.5 que SI esta implementada es el sondeo de
    `verificar_instalacion_github`. Documentado, no una desviacion silenciosa."""
    limite = ahora_utc() - _VENTANA_ADOPCION
    hay_intento_reciente = (
        bd.query(IntentoInstalacionGithub)
        .filter(
            IntentoInstalacionGithub.usuario_id == usuario.id,
            IntentoInstalacionGithub.curso_id == curso_id,
            IntentoInstalacionGithub.emitido_en >= limite,
        )
        .first()
        is not None
    )
    if not hay_intento_reciente:
        return []
    return bd.query(InstalacionGithub).filter(InstalacionGithub.curso_id.is_(None)).all()


def adoptar_instalacion_huerfana(
    bd: Session, *, curso: Curso, usuario: Usuario, installation_id: int, org_login_confirmado: str
) -> InstalacionGithub:
    """S4.6.5: "la adopcion exige ademas confirmacion escrita que nombra la
    organizacion" -- `org_login_confirmado` debe coincidir exactamente."""
    disponibles = instalaciones_huerfanas_adoptables(bd, usuario=usuario, curso_id=curso.id)
    huerfana = next((i for i in disponibles if i.installation_id == installation_id), None)
    if huerfana is None:
        raise RechazoInstalacion(MotivoRechazoInstalacion.STATE_INVALIDO)
    if huerfana.org_login != org_login_confirmado:
        raise RechazoInstalacion(
            MotivoRechazoInstalacion.STATE_INVALIDO, detalle="la organizacion no coincide"
        )

    ocupante = (
        bd.query(Curso)
        .filter(Curso.github_org_id == huerfana.org_id, Curso.id != curso.id)
        .one_or_none()
    )
    if ocupante is not None:
        raise RechazoInstalacion(
            MotivoRechazoInstalacion.ORGANIZACION_YA_VINCULADA, detalle=ocupante.nombre
        )

    ahora = ahora_utc()
    huerfana.curso_id = curso.id
    huerfana.actualizada_en = ahora
    curso.github_org_login = huerfana.org_login
    curso.github_org_id = huerfana.org_id
    curso.github_installation_id = huerfana.installation_id
    if curso.estado == "BORRADOR":
        curso.estado = "VINCULANDO"
    curso.actualizado_en = ahora
    bd.flush()
    return huerfana


def reconciliar_instalaciones(bd: Session, cliente: ClienteGitHub) -> None:
    """`verificar_instalacion_github` (cada hora, S4.6.4): sin webhook,
    `GET /app/installations` es la unica forma de descubrir que una
    instalacion pendiente de aprobacion del owner ya se aprobo -- aparece
    aqui por primera vez, sin que nadie haya vuelto del flujo interactivo."""
    ahora = ahora_utc()
    for info in cliente.listar_instalaciones():
        fila = (
            bd.query(InstalacionGithub)
            .filter(InstalacionGithub.installation_id == info.installation_id)
            .one_or_none()
        )
        if fila is None:
            fila = InstalacionGithub(
                installation_id=info.installation_id,
                curso_id=None,
                org_login=info.account_login,
                org_id=info.account_id,
                repository_selection=info.repository_selection,
                permisos_pendientes=False,
                suspendida=info.suspendida,
                actualizada_en=ahora,
            )
            bd.add(fila)
            bd.flush()
        else:
            fila.org_login = info.account_login
            fila.repository_selection = info.repository_selection
            fila.suspendida = info.suspendida
            fila.actualizada_en = ahora

        if fila.curso_id is None:
            _intentar_auto_adopcion(bd, cliente, huerfana=fila)
    bd.flush()


def _intentar_auto_adopcion(
    bd: Session, cliente: ClienteGitHub, *, huerfana: InstalacionGithub
) -> None:
    """Adopcion automatica cuando el profesor dejo escrita la organizacion
    que esperaba (`org_login_sugerido`) al iniciar el flujo (S4.6.4: "el curso
    avanza solo, sin que el profesor tenga que volver a pulsar nada")."""
    limite = ahora_utc() - _VENTANA_AUTO_ADOPCION_POR_SUGERENCIA
    intento = (
        bd.query(IntentoInstalacionGithub)
        .filter(
            IntentoInstalacionGithub.org_login_sugerido == huerfana.org_login,
            IntentoInstalacionGithub.consumido_en.is_(None),
            IntentoInstalacionGithub.emitido_en >= limite,
        )
        .order_by(IntentoInstalacionGithub.emitido_en.desc())
        .first()
    )
    if intento is None:
        return
    curso = bd.query(Curso).filter(Curso.id == intento.curso_id).one_or_none()
    if curso is None or curso.github_installation_id is not None:
        return
    ocupante = (
        bd.query(Curso)
        .filter(Curso.github_org_id == huerfana.org_id, Curso.id != curso.id)
        .one_or_none()
    )
    if ocupante is not None:
        return

    ahora = ahora_utc()
    huerfana.curso_id = curso.id
    huerfana.actualizada_en = ahora
    intento.consumido_en = ahora
    curso.github_org_login = huerfana.org_login
    curso.github_org_id = huerfana.org_id
    curso.github_installation_id = huerfana.installation_id
    if curso.estado == "BORRADOR":
        curso.estado = "VINCULANDO"
    curso.actualizado_en = ahora
    crear_y_poblar_equipo_docente(bd, cliente, curso=curso, instalacion=huerfana)
