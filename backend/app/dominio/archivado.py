"""Archivar los repositorios de una tarea (A-168, A-197, A-227; Etapa F8).

`puede_archivar` es la unica funcion que decide si se puede archivar: la usan
la pantalla (para mostrar las cinco guardas antes de habilitar el boton), el
endpoint (para rechazar con el motivo) y el trabajo `archivar_repositorios`,
que la reevalua antes de cada repositorio. Pura: recibe hechos, no consulta.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.dominio.estados import EstadoAccesoDocente, EstadoAccesoRepositorio

# Guarda 4 (A-197): el aviso previo sale catorce dias antes de archivar.
DIAS_AVISO = 14
# Toda confirmacion escrita exige una frase, no un clic.
MIN_CONFIRMACION = 10


@dataclass(frozen=True)
class EntregaDeSujeto:
    """Una entrega de la tarea para el sujeto de un repositorio: su fecha de
    cierre efectiva vigente (nula = sin fecha) y si tiene version vigente."""

    entrega: str
    fecha: datetime | None
    capturada: bool


@dataclass(frozen=True)
class RepositorioArchivable:
    nombre: str
    entregas: tuple[EntregaDeSujeto, ...]
    accesos_docentes: tuple[str, ...]
    accesos_estudiantes: tuple[str, ...]


@dataclass(frozen=True)
class AvisoPrevio:
    """Estado del aviso previo por Canvas (guarda 4), contado por persona."""

    destinatarios: int
    encolados: int
    enviados: int
    bloqueados: int
    ultimo_envio: datetime | None
    canal_bloqueado: bool


@dataclass(frozen=True)
class Guarda:
    numero: int
    titulo: str
    cumple: bool
    motivo: str | None = None
    # Si la guarda puede superarse con una confirmacion escrita, cual.
    confirmacion: str | None = None
    detalle: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultadoArchivado:
    guardas: tuple[Guarda, ...]

    @property
    def permitido(self) -> bool:
        return all(g.cumple for g in self.guardas)

    @property
    def fallida(self) -> Guarda | None:
        return next((g for g in self.guardas if not g.cumple), None)


def _confirmado(texto: str | None) -> bool:
    return len((texto or "").strip()) >= MIN_CONFIRMACION


def _guarda_capturas(
    repositorios: list[RepositorioArchivable], *, ahora: datetime, confirmacion: str | None
) -> Guarda:
    titulo = "Versiones capturadas"
    futuras = [
        f"{r.nombre}: {e.entrega} cierra el {e.fecha:%d-%m-%Y %H:%M} UTC"
        for r in repositorios
        for e in r.entregas
        if not e.capturada and e.fecha is not None and e.fecha > ahora
    ]
    if futuras:
        return Guarda(
            1,
            titulo,
            False,
            f"Hay {len(futuras)} entregas con cierre futuro: no se archiva con trabajo en curso.",
            detalle=tuple(futuras),
        )
    vencidas = [
        f"{r.nombre}: {e.entrega} sin versión capturada"
        for r in repositorios
        for e in r.entregas
        if not e.capturada
    ]
    if not vencidas:
        return Guarda(1, titulo, True)
    if _confirmado(confirmacion):
        return Guarda(
            1,
            titulo,
            True,
            f"Confirmaste por escrito que {len(vencidas)} entregas quedan sin versión capturada.",
            detalle=tuple(vencidas),
        )
    return Guarda(
        1,
        titulo,
        False,
        f"{len(vencidas)} entregas vencidas no tienen versión capturada. Si archivas igual, "
        "escribe por qué.",
        confirmacion="SIN_CAPTURA",
        detalle=tuple(vencidas),
    )


def _guarda_acceso_docente(repositorios: list[RepositorioArchivable]) -> Guarda:
    faltan = [
        r.nombre
        for r in repositorios
        if not r.accesos_docentes
        or any(a != EstadoAccesoDocente.CONCEDIDO.value for a in r.accesos_docentes)
    ]
    if not faltan:
        return Guarda(2, "Acceso del equipo docente", True)
    return Guarda(
        2,
        "Acceso del equipo docente",
        False,
        f"{len(faltan)} repositorios no tienen el acceso docente concedido. En un repositorio "
        "archivado ya no se puede arreglar.",
        detalle=tuple(faltan),
    )


def _guarda_invitaciones(repositorios: list[RepositorioArchivable]) -> Guarda:
    pendientes = []
    for r in repositorios:
        n = sum(1 for a in r.accesos_estudiantes if a == EstadoAccesoRepositorio.INVITADO.value)
        if n:
            pendientes.append(f"{r.nombre}: {n} {'invitación' if n == 1 else 'invitaciones'}")
    if not pendientes:
        return Guarda(3, "Invitaciones resueltas", True)
    return Guarda(
        3,
        "Invitaciones resueltas",
        False,
        "Hay invitaciones sin aceptar: quedarían congeladas. Resuélvelas antes de archivar.",
        detalle=tuple(pendientes),
    )


def _guarda_aviso(aviso: AvisoPrevio, *, ahora: datetime, confirmacion: str | None) -> Guarda:
    titulo = "Aviso previo por Canvas"
    if aviso.destinatarios == 0:
        return Guarda(4, titulo, True, "No hay estudiantes a quienes avisar.")
    no_avisables = (
        aviso.destinatarios - aviso.enviados if aviso.canal_bloqueado else aviso.bloqueados
    )
    if no_avisables > 0:
        if _confirmado(confirmacion) and str(no_avisables) in (confirmacion or ""):
            return Guarda(
                4,
                titulo,
                True,
                f"Declaraste por escrito que {no_avisables} estudiantes no "
                "recibieron el aviso por Canvas.",
            )
        return Guarda(
            4,
            titulo,
            False,
            f"Canvas no permite avisar a {no_avisables} estudiantes. Para archivar igual, "
            f"declara por escrito ese número ({no_avisables}).",
            confirmacion="SIN_AVISO",
        )
    if aviso.encolados == 0:
        return Guarda(4, titulo, False, "Todavía no envías el aviso previo a los estudiantes.")
    if aviso.enviados < aviso.destinatarios or aviso.ultimo_envio is None:
        return Guarda(
            4,
            titulo,
            False,
            f"El aviso previo llegó a {aviso.enviados} de {aviso.destinatarios} estudiantes.",
        )
    desde = aviso.ultimo_envio + timedelta(days=DIAS_AVISO)
    if desde > ahora:
        dias = (desde - ahora).days + (1 if (desde - ahora) % timedelta(days=1) else 0)
        return Guarda(
            4,
            titulo,
            False,
            f"Faltan {dias} días: el aviso salió el {aviso.ultimo_envio:%d-%m-%Y} y se puede "
            f"archivar desde el {desde:%d-%m-%Y}.",
        )
    return Guarda(4, titulo, True)


def _guarda_correcciones(abiertas: int | None) -> Guarda:
    titulo = "Correcciones terminadas"
    if abiertas is None:
        # TODO(etapa-correcciones): contar las correcciones no terminales
        # (ni publicadas, ni excusadas, ni excluidas) cuando exista el modulo.
        return Guarda(
            5, titulo, True, "La aplicación todavía no registra correcciones: no hay abiertas."
        )
    if abiertas == 0:
        return Guarda(5, titulo, True)
    return Guarda(
        5,
        titulo,
        False,
        f"{abiertas} correcciones no están publicadas, excusadas ni excluidas.",
    )


def puede_archivar(
    *,
    repositorios: list[RepositorioArchivable],
    aviso: AvisoPrevio,
    correcciones_abiertas: int | None,
    ahora: datetime,
    confirmacion_sin_captura: str | None = None,
    confirmacion_sin_aviso: str | None = None,
) -> ResultadoArchivado:
    """Las cinco guardas de A-197, siempre las cinco y en su orden."""
    return ResultadoArchivado(
        (
            _guarda_capturas(repositorios, ahora=ahora, confirmacion=confirmacion_sin_captura),
            _guarda_acceso_docente(repositorios),
            _guarda_invitaciones(repositorios),
            _guarda_aviso(aviso, ahora=ahora, confirmacion=confirmacion_sin_aviso),
            _guarda_correcciones(correcciones_abiertas),
        )
    )
