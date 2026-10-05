"""Topes de mapeo compartidos: evidencia existente, sin contador nuevo (SPEC 02 §2.13)."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.adaptadores.modelos_aprovisionamiento import MensajeSaliente
from app.adaptadores.modelos_infraestructura import Bitacora
from app.adaptadores.modelos_padron import Estudiante

MAXIMO_RECORDATORIOS = 3


@dataclass(frozen=True)
class ResumenRecordatorios:
    enviados: int
    reservados: int
    manuales: int
    ultimo_en: datetime | None

    @property
    def proximo_en(self) -> datetime | None:
        return self.ultimo_en + timedelta(hours=24) if self.ultimo_en else None


def resumen_recordatorios(bd: Session, estudiante: Estudiante) -> ResumenRecordatorios:
    manuales = (
        bd.query(Bitacora.creado_en)
        .filter(
            Bitacora.curso_id == estudiante.curso_id,
            Bitacora.accion == "RECORDATORIO_GITHUB_ENVIADO",
            Bitacora.entidad == "estudiante",
            Bitacora.entidad_id == str(estudiante.id),
        )
        .all()
    )
    mensajes = (
        bd.query(MensajeSaliente)
        .filter(
            MensajeSaliente.curso_id == estudiante.curso_id,
            MensajeSaliente.estudiante_id == estudiante.id,
            MensajeSaliente.evento == "recordatorio_mapeo",
            MensajeSaliente.es_prueba.is_(False),
        )
        .all()
    )
    enviados = [m for m in mensajes if m.enviado_en is not None]
    reservados = sum(
        m.estado
        in {
            "PENDIENTE",
            "EN_CURSO",
            "ENVIANDO",
            "REINTENTAR",
            "ESPERANDO_LIMITE",
            "ESPERANDO_CREDENCIAL",
            "BLOQUEADO",
        }
        and m.enviado_en is None
        for m in mensajes
    )
    # El sello legado prueba un envío aunque su bitácora ya no esté disponible.
    cantidad_manual = max(len(manuales), int(estudiante.ultimo_recordatorio_en is not None))
    fechas = [f[0] for f in manuales] + [m.enviado_en for m in enviados if m.enviado_en]
    if estudiante.ultimo_recordatorio_en:
        fechas.append(estudiante.ultimo_recordatorio_en)
    return ResumenRecordatorios(
        enviados=cantidad_manual + len(enviados),
        reservados=reservados,
        manuales=cantidad_manual,
        ultimo_en=max(fechas) if fechas else None,
    )
