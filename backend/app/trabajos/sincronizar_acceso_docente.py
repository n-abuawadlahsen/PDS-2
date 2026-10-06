"""Reconcilia el acceso vigente y limpia identidades anteriores del docente."""

import uuid

from sqlalchemy.orm import Session

from app.adaptadores import github_repo
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cerrojos import bloquear_ciclo_curso, bloquear_equipo, cerrojo_github
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("sincronizar_acceso_docente")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    consulta = (
        sesion.query(MembresiaCurso)
        .join(Curso, Curso.id == MembresiaCurso.curso_id)
        .filter(Curso.estado != "ARCHIVADO")
        .populate_existing()
    )
    mid = trabajo.payload.get("membresia_id")
    if mid:
        consulta = consulta.filter(MembresiaCurso.id == uuid.UUID(mid))
    else:
        consulta = consulta.filter(MembresiaCurso.estado == "ACTIVA")
        if trabajo.curso_id:
            consulta = consulta.filter(MembresiaCurso.curso_id == trabajo.curso_id)
    miembros = consulta.all()
    # Mismo orden que las mutaciones de curso: ciclo, equipo, proveedor.
    for cid in sorted({m.curso_id for m in miembros}):
        bloquear_ciclo_curso(sesion, cid)
    bloquear_equipo(sesion)
    for m in miembros:
        sesion.refresh(m)
        curso = sesion.get(Curso, m.curso_id)
        usuario = sesion.get(Usuario, m.usuario_id)
        assert curso is not None and usuario is not None
        sesion.refresh(curso)
        if curso.estado == "ARCHIVADO":
            continue
        sesion.refresh(usuario)
        anterior = trabajo.payload.get("login_anterior") if mid else None
        habilitado = (
            usuario.activo and m.estado == "ACTIVA" and usuario.consentimiento_github_en is not None
        )
        with cerrojo_github(sesion, curso.id):
            try:
                if anterior and (
                    not habilitado
                    or anterior.lower() != (usuario.github_login_declarado or "").lower()
                ):
                    github_repo.revocar_acceso_tres_planos(
                        sesion,
                        cliente,
                        membresia_id=m.id,
                        login_anterior=anterior,
                        alta_anterior_por_app=trabajo.payload.get("alta_anterior_por_app"),
                    )
                github_repo.sincronizar_acceso_de_un_docente(
                    sesion, cliente, curso=curso, membresia=m
                )
            except Exception:
                m.org_github_estado = "ERROR"
                m.org_github_ultimo_error = (
                    "No se pudo completar el acceso en GitHub. Se reintentará."
                )
                sesion.flush()
                raise
