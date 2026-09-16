"""Cierre transaccional de cuenta y retiro de credenciales (SPEC 02 S2.10)."""

from sqlalchemy.orm import Session

from app.adaptadores import bitacora_repo, cursos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_canvas import CredencialCanvas
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.adaptadores.modelos_infraestructura import Incidencia
from app.dominio.cuenta import CursoBloqueante, puede_cerrar_cuenta
from app.infraestructura.cerrojos import bloquear_equipo


def cursos_bloqueantes(bd: Session, usuario: Usuario) -> list[CursoBloqueante]:
    cursos = (
        bd.query(Curso)
        .join(MembresiaCurso)
        .filter(
            Curso.estado == "ACTIVO",
            MembresiaCurso.usuario_id == usuario.id,
            MembresiaCurso.estado == "ACTIVA",
            MembresiaCurso.rol == "PROFESOR",
        )
        .all()
    )
    return puede_cerrar_cuenta(
        [
            CursoBloqueante(c.id, c.nombre)
            for c in cursos
            if cursos_repo.contar_profesores_activos(bd, c.id) <= 1
        ]
    )


def retirar_credenciales(bd: Session, membresia: MembresiaCurso) -> None:
    credencial = (
        bd.query(CredencialCanvas)
        .filter_by(
            curso_id=membresia.curso_id,
            usuario_id=membresia.usuario_id,
        )
        .one_or_none()
    )
    if credencial is None or credencial.estado == "RETIRADA":
        return
    operativa = credencial.orden_respaldo == 0
    credencial.estado = "RETIRADA"
    credencial.token_cifrado = b""
    credencial.nonce = b""
    if not operativa:
        bd.flush()
        return
    credenciales = bd.query(CredencialCanvas).filter_by(curso_id=membresia.curso_id).all()
    credencial.orden_respaldo = max(c.orden_respaldo for c in credenciales) + 1
    bd.flush()  # libera el indice unico de orden 0 antes de promover
    respaldo = (
        bd.query(CredencialCanvas)
        .join(
            MembresiaCurso,
            (MembresiaCurso.usuario_id == CredencialCanvas.usuario_id)
            & (MembresiaCurso.curso_id == CredencialCanvas.curso_id),
        )
        .join(Usuario, Usuario.id == CredencialCanvas.usuario_id)
        .filter(
            CredencialCanvas.curso_id == membresia.curso_id,
            CredencialCanvas.estado == "VALIDA",
            MembresiaCurso.estado == "ACTIVA",
            Usuario.activo.is_(True),
        )
        .order_by(CredencialCanvas.orden_respaldo)
        .first()
    )
    if respaldo is not None:
        respaldo.orden_respaldo = 0
    else:
        curso = bd.get(Curso, membresia.curso_id)
        assert curso is not None
        if curso.estado != "ARCHIVADO":
            curso.estado = "CANVAS_DESVINCULADO"
            curso.actualizado_en = ahora_utc()
        if (
            not bd.query(Incidencia)
            .filter_by(curso_id=curso.id, tipo="CANVAS_CREDENCIAL_INVALIDA", abierta=True)
            .first()
        ):
            bd.add(
                Incidencia(
                    tipo="CANVAS_CREDENCIAL_INVALIDA",
                    severidad="BLOQUEANTE",
                    sujeto_tipo="curso",
                    sujeto_id=curso.id,
                    curso_id=curso.id,
                    detalle={
                        "motivo": "Se retiró la credencial operativa y no hay respaldo válido."
                    },
                    abierta=True,
                    creado_en=ahora_utc(),
                )
            )
    bd.flush()


def cerrar(bd: Session, usuario: Usuario) -> list[CursoBloqueante]:
    from app.adaptadores.acceso_docente_repo import encolar_sincronizacion

    bloquear_equipo(bd)
    bd.refresh(usuario)
    bloqueantes = cursos_bloqueantes(bd, usuario)
    if bloqueantes:
        return bloqueantes
    for membresia in (
        bd.query(MembresiaCurso).filter_by(usuario_id=usuario.id, estado="ACTIVA").all()
    ):
        curso = bd.get(Curso, membresia.curso_id)
        assert curso is not None
        cursos_repo.retirar_membresia(
            bd, membresia, actor=usuario, curso_activo=curso.estado == "ACTIVO"
        )
        retirar_credenciales(bd, membresia)
        encolar_sincronizacion(bd, membresia, revocar=True)
        bitacora_repo.registrar(
            bd,
            accion="MEMBRESIA_RETIRADA",
            entidad="membresia_curso",
            entidad_id=str(membresia.id),
            actor_usuario_id=usuario.id,
            curso_id=curso.id,
        )
    ahora = ahora_utc()
    bd.query(Sesion).filter(Sesion.usuario_id == usuario.id, Sesion.revocada_en.is_(None)).update(
        {"revocada_en": ahora}
    )
    usuario.activo = False
    usuario.actualizado_en = ahora
    bitacora_repo.registrar(
        bd,
        accion="USUARIO_DESACTIVADO",
        entidad="usuario",
        entidad_id=str(usuario.id),
        actor_usuario_id=usuario.id,
    )
    bd.flush()
    return []
