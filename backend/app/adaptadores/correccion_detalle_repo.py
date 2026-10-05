"""Detalle de corrección obtenido del espejo y la auditoría, sin llamadas externas."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.adaptadores import correccion_repo
from app.adaptadores.modelos_actividad import Commit
from app.adaptadores.modelos_aprovisionamiento import AccesoRepositorio, Sujeto
from app.adaptadores.modelos_correccion import Correccion
from app.adaptadores.modelos_curso import MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_infraestructura import Bitacora
from app.adaptadores.modelos_tarea import Entrega


def autoria(bd: Session, c: Correccion, curso_id: uuid.UUID) -> dict[str, Any]:
    registro = (
        bd.query(Bitacora)
        .filter(
            Bitacora.entidad == "correccion",
            Bitacora.entidad_id == str(c.id),
            Bitacora.accion == "BORRADOR_CORRECCION_GUARDADO",
        )
        .order_by(Bitacora.creado_en.desc(), Bitacora.id.desc())
        .first()
    )
    usuario = bd.get(Usuario, c.corrector_usuario_id) if c.corrector_usuario_id else None
    miembro = (
        (
            bd.query(MembresiaCurso)
            .filter(
                MembresiaCurso.curso_id == curso_id,
                MembresiaCurso.usuario_id == c.corrector_usuario_id,
            )
            .first()
        )
        if c.corrector_usuario_id
        else None
    )
    return {
        "usuario_id": str(c.corrector_usuario_id) if c.corrector_usuario_id else None,
        "nombre": usuario.nombre if usuario else None,
        "rol": (registro.despues or {}).get("rol")
        if registro
        else miembro.rol
        if miembro
        else None,
        # actualizado_en también cambia con transiciones: no fingir que es la fecha de guardado.
        "guardado_en": registro.creado_en.isoformat() if registro else None,
    }


def evidencia_sin_commits(bd: Session, entrega: Entrega, sujeto: Sujeto) -> dict[str, Any]:
    repo = correccion_repo.repositorio_de(bd, sujeto.id)
    miembros = correccion_repo.integrantes(bd, sujeto)
    accesos = (
        {
            a.estudiante_id: a
            for a in bd.query(AccesoRepositorio).filter(AccesoRepositorio.repositorio_id == repo.id)
        }
        if repo
        else {}
    )
    aceptados = [a for a in accesos.values() if a.aceptado_en is not None or a.estado == "ACEPTADO"]
    verificado = bool(repo and miembros and all(e.id in accesos for e in miembros))
    sin_aceptar = verificado and not aceptados
    consulta = bd.query(Commit).filter(Commit.repositorio_id == repo.id) if repo else None
    sin_atribuir = (
        consulta.filter(
            Commit.regla_atribucion == "SIN_ATRIBUIR", Commit.huerfano.is_(False)
        ).count()
        if consulta is not None
        else 0
    )
    ultimo = (
        bd.query(func.max(Commit.fecha_committer))
        .filter(
            Commit.repositorio_id == repo.id,
            Commit.en_rama_por_defecto.is_(True),
            Commit.huerfano.is_(False),
        )
        .scalar()
        if repo
        else None
    )
    if not repo:
        causa = "Todavía no hay un repositorio registrado para este sujeto."
    elif sin_aceptar:
        causa = "Ningún integrante tiene aceptación de la invitación a GitHub registrada."
    elif sin_atribuir:
        causa = (
            f"Hay {sin_atribuir} commits sin atribuir en el espejo; revisa las identidades de Git."
        )
    elif ultimo:
        causa = "Hay actividad registrada en la rama por defecto; revisa el último commit y el corte de esta entrega."
    else:
        causa = "No hay commits registrados en la rama por defecto. Revisa la invitación y la sincronización."
    return {
        "repositorio_id": str(repo.id) if repo else None,
        "sujeto_id": str(sujeto.id),
        "causa_probable": causa,
        "acceso_verificado": verificado,
        "sin_aceptacion": sin_aceptar,
        "excluir_por_defecto": not verificado or sin_aceptar,
        "rama_por_defecto": repo.rama_por_defecto if repo else None,
        "ultimo_commit_en": ultimo.isoformat() if ultimo else None,
        "commits_sin_atribuir": sin_atribuir if repo else None,
        "integrantes": [
            {
                "estudiante_id": str(e.id),
                "nombre": e.nombre,
                "acceso_estado": accesos[e.id].estado if e.id in accesos else None,
                "aceptado_en": accesos[e.id].aceptado_en.isoformat()
                if e.id in accesos and accesos[e.id].aceptado_en
                else None,
            }
            for e in miembros
        ],
    }
