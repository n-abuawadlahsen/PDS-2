"""Etapa F5 (SPEC 10 S10.2-S10.3; SPEC 06 S6.8; A-070 a A-072, A-118, A-205,
A-221): ingesta y atribucion, reglas puras."""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from app.dominio.actividad import (
    ContextoAtribucion,
    atribuir,
    decidir_relleno,
    es_mejora,
    firma_valida,
    id_desde_noreply,
    motivo_exclusion,
    normalizar_email,
    ofuscar_email,
    repositorio_en_ingesta,
    techo_frescura,
)
from app.dominio.estados import MotivoExclusionCommit, ReglaAtribucion

_CERO = "0" * 40


def _firma(secreto: str, cuerpo: bytes) -> str:
    return "sha256=" + hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()


def test_firma_hmac_sobre_el_cuerpo_crudo_con_secreto_anterior():
    cuerpo = b'{"zen": "Keep it logically awesome."}'
    assert firma_valida(cuerpo, _firma("s1", cuerpo), secretos=["s1", None])
    # Rotacion: el secreto anterior sigue valiendo mientras exista.
    assert firma_valida(cuerpo, _firma("viejo", cuerpo), secretos=["s1", "viejo"])
    assert not firma_valida(cuerpo, _firma("otro", cuerpo), secretos=["s1", None])
    assert not firma_valida(cuerpo, None, secretos=["s1", None])
    assert not firma_valida(cuerpo + b" ", _firma("s1", cuerpo), secretos=["s1", None])


def test_correos_normalizados_ofuscados_y_noreply():
    # Minusculas y recorte; nunca se quitan puntos ni sufijos +etiqueta.
    assert normalizar_email("  Juan.Perez+tarea@Gmail.com ") == "juan.perez+tarea@gmail.com"
    assert id_desde_noreply("70001+Estudiante-Valido@users.noreply.github.com") == 70001
    assert id_desde_noreply("estudiante@users.noreply.github.com") is None
    assert id_desde_noreply("70001+x@gmail.com") is None
    assert ofuscar_email("jperez@gmail.com") == "j•••@g•••.com"
    # El noreply no es un dato de contacto: se muestra completo.
    noreply = "70001+Estudiante-Valido@users.noreply.github.com"
    assert ofuscar_email(noreply) == noreply
    assert ofuscar_email(None) is None


def _contexto(**cambios):
    base = {
        "estudiante_por_github_id": {70001: "ana"},
        "estudiante_por_email": {"bruno@uc.cl": "bruno"},
        "identidad": None,
    }
    base.update(cambios)
    return ContextoAtribucion(**base)


def test_cascada_de_atribucion_en_orden_estricto():
    """S10.3.1: gana la primera regla que casa; nunca por login ni por nombre."""
    r = atribuir(autor_github_user_id=70001, autor_email="bruno@uc.cl", contexto=_contexto())
    assert (r.regla, r.estudiante_id, r.confianza) == (ReglaAtribucion.AUTOR_GITHUB, "ana", "ALTA")
    r = atribuir(
        autor_github_user_id=None,
        autor_email="70001+x@users.noreply.github.com",
        contexto=_contexto(),
    )
    assert (r.regla, r.estudiante_id) == (ReglaAtribucion.EMAIL_NOREPLY, "ana")
    r = atribuir(autor_github_user_id=999, autor_email=" Bruno@UC.cl", contexto=_contexto())
    assert (r.regla, r.estudiante_id, r.confianza) == (
        ReglaAtribucion.EMAIL_DIRECTO,
        "bruno",
        "MEDIA",
    )
    r = atribuir(
        autor_github_user_id=None,
        autor_email="root@localhost",
        contexto=_contexto(identidad=("RESUELTA", "carla")),
    )
    assert (r.regla, r.estudiante_id) == (ReglaAtribucion.IDENTIDAD_DOCENTE, "carla")
    r = atribuir(autor_github_user_id=None, autor_email="root@localhost", contexto=_contexto())
    assert (r.regla, r.estudiante_id) == (ReglaAtribucion.SIN_ATRIBUIR, None)
    # Una identidad marcada «no es estudiante» no se atribuye a nadie.
    r = atribuir(
        autor_github_user_id=None,
        autor_email="ci@bot",
        contexto=_contexto(identidad=("NO_ES_ESTUDIANTE", None)),
    )
    assert (r.regla, r.estudiante_id) == (ReglaAtribucion.SIN_ATRIBUIR, None)


def test_la_reatribucion_solo_mejora():
    assert es_mejora(ReglaAtribucion.SIN_ATRIBUIR, ReglaAtribucion.IDENTIDAD_DOCENTE)
    assert es_mejora(ReglaAtribucion.EMAIL_DIRECTO, ReglaAtribucion.AUTOR_GITHUB)
    # La correccion docente nunca pisa a las dos reglas de confianza alta.
    assert not es_mejora(ReglaAtribucion.AUTOR_GITHUB, ReglaAtribucion.IDENTIDAD_DOCENTE)
    assert not es_mejora(ReglaAtribucion.EMAIL_NOREPLY, ReglaAtribucion.SIN_ATRIBUIR)
    assert not es_mejora(ReglaAtribucion.AUTOR_GITHUB, ReglaAtribucion.AUTOR_GITHUB)


def test_solo_tres_motivos_de_exclusion():
    """S10.5.1: merge, commit inicial y huerfano; bots y docentes cuentan."""
    assert motivo_exclusion(n_padres=2, sha="a", commit_inicial_sha="i", huerfano=False) == (
        MotivoExclusionCommit.MERGE
    )
    assert motivo_exclusion(n_padres=1, sha="i", commit_inicial_sha="i", huerfano=False) == (
        MotivoExclusionCommit.COMMIT_INICIAL
    )
    assert motivo_exclusion(n_padres=1, sha="a", commit_inicial_sha="i", huerfano=True) == (
        MotivoExclusionCommit.HUERFANO
    )
    assert motivo_exclusion(n_padres=None, sha="a", commit_inicial_sha=None, huerfano=False) == (
        MotivoExclusionCommit.NINGUNO
    )


def test_decision_de_relleno_de_un_push():
    """S10.2.3: rama borrada, rama nueva, y todo lo demas por `compare`."""
    assert decidir_relleno(before="a" * 40, after=_CERO) == "RAMA_BORRADA"
    assert decidir_relleno(before=_CERO, after="b" * 40) == "RECORRIDO"
    assert decidir_relleno(before="a" * 40, after="b" * 40) == "COMPARE"


def test_repositorio_en_ingesta_con_cola_de_gracia():
    ahora = datetime(2026, 10, 10, tzinfo=UTC)
    assert repositorio_en_ingesta(
        estado_repositorio="OPERATIVO", estado_tarea="ACTIVA", ultima_fecha=ahora, ahora=ahora
    )
    assert repositorio_en_ingesta(
        estado_repositorio="DEGRADADO",
        estado_tarea="ACTIVA",
        ultima_fecha=ahora - timedelta(days=13),
        ahora=ahora,
    )
    assert not repositorio_en_ingesta(
        estado_repositorio="OPERATIVO",
        estado_tarea="ACTIVA",
        ultima_fecha=ahora - timedelta(days=15),
        ahora=ahora,
    )
    assert not repositorio_en_ingesta(
        estado_repositorio="ARCHIVADO", estado_tarea="ACTIVA", ultima_fecha=ahora, ahora=ahora
    )
    assert not repositorio_en_ingesta(
        estado_repositorio="OPERATIVO", estado_tarea="CERRADA", ultima_fecha=ahora, ahora=ahora
    )
    # Sin ninguna fecha todavia, el repositorio sigue en ingesta.
    assert repositorio_en_ingesta(
        estado_repositorio="OPERATIVO", estado_tarea="ACTIVA", ultima_fecha=None, ahora=ahora
    )


def test_techo_de_frescura_sin_webhook():
    """S10.2.1: ceil(repositorios / 200) x 15 min."""
    assert techo_frescura(200) == timedelta(minutes=15)
    assert techo_frescura(600) == timedelta(minutes=45)
    assert techo_frescura(201) == timedelta(minutes=30)
    assert techo_frescura(0) == timedelta(minutes=15)
