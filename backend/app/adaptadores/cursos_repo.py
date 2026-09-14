"""Acceso a `curso`, `membresia_curso` e `invitacion_equipo` (SPEC 02 S2.4-S2.5, S2.7, S2.9)."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_curso import Curso, InvitacionEquipo, MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.dominio.estados import EstadoCurso, EstadoInvitacion, EstadoMembresia, RolMembresia
from app.dominio.membresia import puede_retirar_o_degradar
from app.dominio.permisos import Permiso

_CADUCIDAD_INVITACION = timedelta(days=7)
_MAXIMO_REENVIOS = 3


def hash_token_invitacion(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def crear_curso(
    bd: Session,
    *,
    creador: Usuario,
    nombre: str,
    codigo: str,
    periodo: str,
    slug: str,
    zona_horaria: str,
) -> Curso:
    """El creador queda como PROFESOR con los nueve implicitos, `permisos = []` (S2.3.10 #3)."""
    ahora = ahora_utc()
    curso = Curso(
        estado=EstadoCurso.BORRADOR.value,
        nombre=nombre,
        codigo=codigo,
        periodo=periodo,
        slug=slug,
        zona_horaria=zona_horaria,
        creado_en=ahora,
        actualizado_en=ahora,
    )
    bd.add(curso)
    bd.flush()

    membresia = MembresiaCurso(
        curso_id=curso.id,
        usuario_id=creador.id,
        rol=RolMembresia.PROFESOR.value,
        permisos=[],
        estado=EstadoMembresia.ACTIVA.value,
        version=1,
        creada_en=ahora,
    )
    bd.add(membresia)
    bd.flush()
    return curso


def listar_cursos_de_usuario(bd: Session, usuario_id: uuid.UUID) -> list[Curso]:
    """S2.9.7: un curso con membresia RETIRADA no aparece, ni en gris."""
    return list(
        bd.execute(
            select(Curso)
            .join(MembresiaCurso, MembresiaCurso.curso_id == Curso.id)
            .where(
                MembresiaCurso.usuario_id == usuario_id,
                MembresiaCurso.estado == EstadoMembresia.ACTIVA.value,
            )
            .order_by(Curso.creado_en.desc())
        )
        .scalars()
        .all()
    )


def obtener_membresia(
    bd: Session, *, curso_id: uuid.UUID, usuario_id: uuid.UUID
) -> MembresiaCurso | None:
    return bd.execute(
        select(MembresiaCurso).where(
            MembresiaCurso.curso_id == curso_id, MembresiaCurso.usuario_id == usuario_id
        )
    ).scalar_one_or_none()


def contar_profesores_activos(bd: Session, curso_id: uuid.UUID) -> int:
    return bd.execute(
        select(func.count()).where(
            MembresiaCurso.curso_id == curso_id,
            MembresiaCurso.rol == RolMembresia.PROFESOR.value,
            MembresiaCurso.estado == EstadoMembresia.ACTIVA.value,
        )
    ).scalar_one()


def listar_equipo(bd: Session, curso_id: uuid.UUID) -> list[MembresiaCurso]:
    return list(
        bd.execute(
            select(MembresiaCurso)
            .where(MembresiaCurso.curso_id == curso_id)
            .order_by(MembresiaCurso.creada_en)
        )
        .scalars()
        .all()
    )


def cambiar_permisos(
    bd: Session, membresia: MembresiaCurso, nuevos_permisos: frozenset[Permiso]
) -> None:
    """S2.7.2: incrementa `version` en la misma transaccion; surte efecto de inmediato."""
    membresia.permisos = sorted(p.value for p in nuevos_permisos)
    membresia.version += 1
    bd.flush()


def cambiar_rol(
    bd: Session,
    membresia: MembresiaCurso,
    *,
    nuevo_rol: RolMembresia,
    permisos_si_ayudante: frozenset[Permiso],
) -> None:
    """S2.7.3: promover vacia `permisos`; degradar exige elegir el subconjunto, nunca hereda."""
    membresia.rol = nuevo_rol.value
    membresia.permisos = (
        [] if nuevo_rol == RolMembresia.PROFESOR else sorted(p.value for p in permisos_si_ayudante)
    )
    membresia.version += 1
    bd.flush()


def retirar_membresia(
    bd: Session, membresia: MembresiaCurso, *, actor: Usuario, curso_activo: bool
) -> None:
    """S2.9.2, pasos 1-3, 7 (encolar) y 9. Los pasos 4/5/6/8 dependen de tablas de
    etapas posteriores (asignacion_correccion F11, suscripcion_informe F9,
    credencial_canvas P3) y se añaden con ellas."""
    puede_retirar_o_degradar(
        es_profesor_activo=membresia.rol == RolMembresia.PROFESOR.value,
        cantidad_profesores_activos=contar_profesores_activos(bd, membresia.curso_id),
        curso_activo=curso_activo,
    )
    ahora = ahora_utc()
    membresia.estado = EstadoMembresia.RETIRADA.value
    membresia.retirada_en = ahora
    membresia.retirada_por = actor.id
    membresia.permisos = []
    membresia.version += 1
    bd.flush()


def reincorporar_membresia(
    bd: Session, membresia: MembresiaCurso, *, permisos: frozenset[Permiso]
) -> None:
    """S2.9.6: reactiva la misma fila; los permisos se vuelven a elegir, nunca se restauran."""
    membresia.estado = EstadoMembresia.ACTIVA.value
    membresia.retirada_en = None
    membresia.retirada_por = None
    membresia.permisos = (
        [] if membresia.rol == RolMembresia.PROFESOR.value else sorted(p.value for p in permisos)
    )
    membresia.version += 1
    bd.flush()


@dataclass(frozen=True)
class InvitacionCreada:
    invitacion: InvitacionEquipo
    token_plano: str


def crear_invitacion(
    bd: Session,
    *,
    curso_id: uuid.UUID,
    invitador: Usuario,
    email: str,
    email_canonico: str,
    rol: RolMembresia,
    permisos: frozenset[Permiso],
    github_login_declarado: str | None,
) -> InvitacionCreada:
    token_plano = secrets.token_urlsafe(32)
    ahora = ahora_utc()
    invitacion = InvitacionEquipo(
        curso_id=curso_id,
        email=email,
        email_canonico=email_canonico,
        rol=rol.value,
        permisos=[] if rol == RolMembresia.PROFESOR else sorted(p.value for p in permisos),
        github_login_declarado=github_login_declarado,
        token_hash=hash_token_invitacion(token_plano),
        estado=EstadoInvitacion.PENDIENTE.value,
        invitada_por=invitador.id,
        creada_en=ahora,
        expira_en=ahora + _CADUCIDAD_INVITACION,
    )
    bd.add(invitacion)
    bd.flush()
    return InvitacionCreada(invitacion=invitacion, token_plano=token_plano)


def obtener_invitacion_por_token(bd: Session, token_plano: str) -> InvitacionEquipo | None:
    return bd.execute(
        select(InvitacionEquipo).where(
            InvitacionEquipo.token_hash == hash_token_invitacion(token_plano)
        )
    ).scalar_one_or_none()


def invitacion_esta_vencida(invitacion: InvitacionEquipo) -> bool:
    """S2.5.2: EXPIRADA se deriva en lectura, ningun trabajo periodico la escribe."""
    return (
        invitacion.estado == EstadoInvitacion.PENDIENTE.value and invitacion.expira_en < ahora_utc()
    )


def contar_reenvios(bd: Session, *, curso_id: uuid.UUID, email_canonico: str) -> int:
    return bd.execute(
        select(func.count()).where(
            InvitacionEquipo.curso_id == curso_id, InvitacionEquipo.email_canonico == email_canonico
        )
    ).scalar_one()


class LimiteDeReenviosSuperado(Exception):
    """S2.5.6: maximo tres reenvios por direccion y curso."""


def reenviar_invitacion(
    bd: Session, invitacion_anterior: InvitacionEquipo, *, actor: Usuario
) -> InvitacionCreada:
    reenvios = contar_reenvios(
        bd, curso_id=invitacion_anterior.curso_id, email_canonico=invitacion_anterior.email_canonico
    )
    if reenvios > _MAXIMO_REENVIOS:
        raise LimiteDeReenviosSuperado()

    ahora = ahora_utc()
    invitacion_anterior.estado = EstadoInvitacion.REVOCADA.value
    invitacion_anterior.revocada_en = ahora
    invitacion_anterior.revocada_por = actor.id

    return crear_invitacion(
        bd,
        curso_id=invitacion_anterior.curso_id,
        invitador=actor,
        email=invitacion_anterior.email,
        email_canonico=invitacion_anterior.email_canonico,
        rol=RolMembresia(invitacion_anterior.rol),
        permisos=frozenset(Permiso(p) for p in invitacion_anterior.permisos),
        github_login_declarado=invitacion_anterior.github_login_declarado,
    )


class InvitacionNoAceptable(Exception):
    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)


def aceptar_invitacion(
    bd: Session, invitacion: InvitacionEquipo, *, usuario: Usuario
) -> MembresiaCurso:
    """S2.5.5: en una sola transaccion, crea o reactiva la membresia."""
    if invitacion.estado == EstadoInvitacion.REVOCADA.value:
        raise InvitacionNoAceptable("REVOCADA")
    if invitacion.estado == EstadoInvitacion.ACEPTADA.value:
        raise InvitacionNoAceptable("YA_ACEPTADA")
    if invitacion_esta_vencida(invitacion):
        raise InvitacionNoAceptable("EXPIRADA")
    if usuario.email_canonico.lower() != invitacion.email_canonico.lower():
        raise InvitacionNoAceptable("CORREO_NO_COINCIDE")

    ahora = ahora_utc()
    existente = obtener_membresia(bd, curso_id=invitacion.curso_id, usuario_id=usuario.id)
    if existente is None:
        membresia = MembresiaCurso(
            curso_id=invitacion.curso_id,
            usuario_id=usuario.id,
            rol=invitacion.rol,
            permisos=list(invitacion.permisos),
            estado=EstadoMembresia.ACTIVA.value,
            version=1,
            invitada_por=invitacion.invitada_por,
            creada_en=ahora,
        )
        bd.add(membresia)
    else:
        # Reactiva la misma fila (invariante 1 de S2.4.2), nunca crea una nueva.
        existente.rol = invitacion.rol
        existente.permisos = list(invitacion.permisos)
        existente.estado = EstadoMembresia.ACTIVA.value
        existente.retirada_en = None
        existente.retirada_por = None
        existente.version += 1
        membresia = existente

    invitacion.estado = EstadoInvitacion.ACEPTADA.value
    invitacion.aceptada_en = ahora
    bd.flush()
    return membresia
