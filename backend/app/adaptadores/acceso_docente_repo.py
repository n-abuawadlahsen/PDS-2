"""Cambios de cuenta docente: validacion global y reconciliacion asincrona."""

import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.adaptadores import trabajos_repo
from app.adaptadores.modelos_curso import MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_mapeo import CuentaGithub, MapeoGithub


def motivo_no_elegible(bd: Session, *, usuario: Usuario, github_id: int, login: str) -> str | None:
    if (
        bd.query(MapeoGithub)
        .join(CuentaGithub)
        .filter(
            CuentaGithub.github_user_id == github_id,
            MapeoGithub.estado == "VIGENTE",
        )
        .first()
    ):
        return "Esta cuenta de GitHub pertenece a un estudiante con una asociación vigente."
    if (
        bd.query(Usuario)
        .filter(
            Usuario.id != usuario.id,
            or_(
                Usuario.cuenta_github_id == github_id,
                func.lower(Usuario.github_login_declarado) == login.lower(),
            ),
        )
        .first()
    ):
        return "Esta cuenta de GitHub ya está declarada por otra persona."
    return None


def encolar_sincronizacion(
    bd: Session,
    membresia: MembresiaCurso,
    *,
    revocar: bool = False,
    login_anterior: str | None = None,
) -> None:
    usuario = bd.get(Usuario, membresia.usuario_id)
    assert usuario is not None
    trabajos_repo.encolar(
        bd,
        tipo="revocar_acceso_docente" if revocar else "sincronizar_acceso_docente",
        clave_idempotencia=f"acceso-docente:{membresia.id}:{uuid.uuid4()}",
        max_intentos=4,
        curso_id=membresia.curso_id,
        payload={
            "membresia_id": str(membresia.id),
            "login_anterior": login_anterior
            or (usuario.github_login_declarado if revocar else None),
            "alta_anterior_por_app": membresia.org_github_alta_por_app,
        },
    )


def programar_cambio_cuenta(bd: Session, usuario: Usuario, login_anterior: str | None) -> None:
    for m in bd.query(MembresiaCurso).filter_by(usuario_id=usuario.id, estado="ACTIVA").all():
        encolar_sincronizacion(bd, m, login_anterior=login_anterior)
        if (
            login_anterior
            and login_anterior.lower() != (usuario.github_login_declarado or "").lower()
        ):
            m.org_github_alta_por_app = False
        m.org_github_estado = "PENDIENTE" if usuario.github_login_declarado else "NO_APLICA"
        m.org_github_ultimo_error = None
    bd.flush()
