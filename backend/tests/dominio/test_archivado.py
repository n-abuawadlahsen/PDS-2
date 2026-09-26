"""Etapa F8 (A-197): las cinco guardas de archivar, en una sola funcion pura."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.dominio.archivado import (
    AvisoPrevio,
    EntregaDeSujeto,
    RepositorioArchivable,
    puede_archivar,
)

AHORA = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def _repo(
    nombre: str = "pds-t1-e2001-ana",
    *,
    entregas: tuple[EntregaDeSujeto, ...] | None = None,
    docentes: tuple[str, ...] = ("CONCEDIDO",),
    estudiantes: tuple[str, ...] = ("ACEPTADO",),
) -> RepositorioArchivable:
    if entregas is None:
        entregas = (EntregaDeSujeto("Entrega 1", AHORA - timedelta(days=20), capturada=True),)
    return RepositorioArchivable(nombre, entregas, docentes, estudiantes)


def _aviso(**cambios) -> AvisoPrevio:
    base = {
        "destinatarios": 2,
        "encolados": 2,
        "enviados": 2,
        "bloqueados": 0,
        "ultimo_envio": AHORA - timedelta(days=15),
        "canal_bloqueado": False,
    }
    base.update(cambios)
    return AvisoPrevio(**base)


def _evaluar(repos=None, aviso=None, **kw):
    return puede_archivar(
        repositorios=repos if repos is not None else [_repo()],
        aviso=aviso if aviso is not None else _aviso(),
        correcciones_abiertas=kw.pop("correcciones_abiertas", None),
        ahora=AHORA,
        **kw,
    )


def _guarda(resultado, numero):
    return next(g for g in resultado.guardas if g.numero == numero)


def test_todo_en_orden_permite_archivar_y_reporta_las_cinco():
    r = _evaluar()
    assert r.permitido
    assert [g.numero for g in r.guardas] == [1, 2, 3, 4, 5]
    assert r.fallida is None


def test_guarda_1_cierre_futuro_sin_captura_bloquea_sin_confirmacion_posible():
    futura = EntregaDeSujeto("Entrega 2", AHORA + timedelta(days=3), capturada=False)
    r = _evaluar([_repo(entregas=(futura,))], confirmacion_sin_captura="archivo igual, lo sé")
    g = _guarda(r, 1)
    assert not g.cumple and g.confirmacion is None
    assert "Entrega 2" in g.detalle[0]
    assert r.fallida is g


def test_guarda_1_vencida_sin_captura_exige_confirmacion_escrita():
    vencida = EntregaDeSujeto("Entrega 1", AHORA - timedelta(days=1), capturada=False)
    r = _evaluar([_repo(entregas=(vencida,))])
    g = _guarda(r, 1)
    assert not g.cumple and g.confirmacion == "SIN_CAPTURA"
    assert "pds-t1-e2001-ana" in g.detalle[0]
    corta = _evaluar([_repo(entregas=(vencida,))], confirmacion_sin_captura="ok")
    assert not _guarda(corta, 1).cumple
    ok = _evaluar(
        [_repo(entregas=(vencida,))], confirmacion_sin_captura="Ana no entregó; se evalúa aparte"
    )
    assert _guarda(ok, 1).cumple and ok.permitido


def test_guarda_1_sin_fecha_de_cierre_cuenta_como_no_capturada():
    sin_fecha = EntregaDeSujeto("Entrega 1", None, capturada=False)
    assert _guarda(_evaluar([_repo(entregas=(sin_fecha,))]), 1).confirmacion == "SIN_CAPTURA"


def test_guarda_2_acceso_docente_no_concedido_o_ausente():
    r = _evaluar([_repo(docentes=("CONCEDIDO", "PENDIENTE")), _repo("otro", docentes=())])
    g = _guarda(r, 2)
    assert not g.cumple and len(g.detalle) == 2


def test_guarda_3_invitaciones_pendientes():
    g = _guarda(_evaluar([_repo(estudiantes=("ACEPTADO", "INVITADO"))]), 3)
    assert not g.cumple and "1 invitación" in g.detalle[0]


def test_guarda_4_aviso_previo():
    nunca = _guarda(_evaluar(aviso=_aviso(encolados=0, enviados=0, ultimo_envio=None)), 4)
    assert not nunca.cumple and "aviso previo" in (nunca.motivo or "")
    en_camino = _guarda(_evaluar(aviso=_aviso(enviados=1)), 4)
    assert not en_camino.cumple and "1 de 2" in (en_camino.motivo or "")
    reciente = _guarda(_evaluar(aviso=_aviso(ultimo_envio=AHORA - timedelta(days=10))), 4)
    assert not reciente.cumple and "4 días" in (reciente.motivo or "")
    sin_nadie = _guarda(_evaluar(aviso=_aviso(destinatarios=0, encolados=0, enviados=0)), 4)
    assert sin_nadie.cumple


def test_guarda_4_canal_bloqueado_se_supera_declarando_el_numero():
    aviso = _aviso(enviados=0, ultimo_envio=None, canal_bloqueado=True)
    g = _guarda(_evaluar(aviso=aviso), 4)
    assert not g.cumple and g.confirmacion == "SIN_AVISO" and "2 estudiantes" in (g.motivo or "")
    sin_numero = _evaluar(aviso=aviso, confirmacion_sin_aviso="avisé por correo a todos")
    assert not _guarda(sin_numero, 4).cumple
    ok = _evaluar(aviso=aviso, confirmacion_sin_aviso="avisé en clase a los 2 estudiantes")
    assert _guarda(ok, 4).cumple


def test_guarda_5_correcciones_abiertas():
    assert _guarda(_evaluar(), 5).cumple  # el modulo de correcciones aun no existe
    assert not _guarda(_evaluar(correcciones_abiertas=3), 5).cumple
