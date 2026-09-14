"""SPEC 04 S4.6 (cuenta personal vs organizacion), S4.7.3 (item 14)."""

from __future__ import annotations

from app.dominio.vinculacion_github import (
    PERMISOS_APP_CONGELADOS,
    InstalacionInfo,
    OrganizacionInfo,
    es_cuenta_de_organizacion,
    evaluar_item_14,
)


def test_es_cuenta_de_organizacion_cuando_solo_existe_como_org():
    assert es_cuenta_de_organizacion(existe_como_usuario=False, existe_como_organizacion=True)


def test_no_es_organizacion_cuando_existe_como_usuario():
    assert not es_cuenta_de_organizacion(existe_como_usuario=True, existe_como_organizacion=True)


def test_no_es_organizacion_cuando_no_existe_como_ninguno():
    assert not es_cuenta_de_organizacion(existe_como_usuario=False, existe_como_organizacion=False)


def _instalacion_valida() -> InstalacionInfo:
    return InstalacionInfo(
        installation_id=8001,
        account_login="org-valida",
        account_id=90001,
        repository_selection="selected",
        permisos=dict(PERMISOS_APP_CONGELADOS),
        suspendida=False,
    )


def _organizacion_valida() -> OrganizacionInfo:
    return OrganizacionInfo(
        default_repository_permission="none",
        members_can_create_repositories=False,
        two_factor_requirement_enabled=True,
        cantidad_owners=2,
    )


def test_item_14_todo_correcto_aprueba():
    resultado = evaluar_item_14(
        instalacion=_instalacion_valida(),
        org_login_esperado="org-valida",
        organizacion=_organizacion_valida(),
        existe_repo_perfil=True,
    )
    assert resultado.aprobado
    assert not resultado.requiere_verificacion_a_mano


def test_item_14_permisos_distintos_al_congelado_no_aprueba():
    instalacion = InstalacionInfo(
        installation_id=8001,
        account_login="org-valida",
        account_id=90001,
        repository_selection="selected",
        permisos={"administration": "read"},
        suspendida=False,
    )
    resultado = evaluar_item_14(
        instalacion=instalacion,
        org_login_esperado="org-valida",
        organizacion=_organizacion_valida(),
        existe_repo_perfil=True,
    )
    assert not resultado.aprobado
    assert not resultado.requiere_verificacion_a_mano


def test_item_14_default_repository_permission_distinto_de_none_bloquea():
    organizacion = OrganizacionInfo(
        default_repository_permission="read",
        members_can_create_repositories=False,
        two_factor_requirement_enabled=True,
        cantidad_owners=2,
    )
    resultado = evaluar_item_14(
        instalacion=_instalacion_valida(),
        org_login_esperado="org-valida",
        organizacion=organizacion,
        existe_repo_perfil=True,
    )
    assert not resultado.aprobado


def test_item_14_campo_no_legible_exige_verificacion_a_mano():
    organizacion = OrganizacionInfo(
        default_repository_permission=None,
        members_can_create_repositories=False,
        two_factor_requirement_enabled=True,
        cantidad_owners=2,
    )
    resultado = evaluar_item_14(
        instalacion=_instalacion_valida(),
        org_login_esperado="org-valida",
        organizacion=organizacion,
        existe_repo_perfil=True,
    )
    assert resultado.requiere_verificacion_a_mano
    assert not resultado.aprobado


def test_item_14_repo_perfil_ausente_no_bloquea_por_si_solo():
    resultado = evaluar_item_14(
        instalacion=_instalacion_valida(),
        org_login_esperado="org-valida",
        organizacion=_organizacion_valida(),
        existe_repo_perfil=False,
    )
    assert resultado.aprobado
    assert resultado.detalle["c_existe_repo_github"] is False


def test_item_14_menos_de_dos_owners_bloquea():
    organizacion = OrganizacionInfo(
        default_repository_permission="none",
        members_can_create_repositories=False,
        two_factor_requirement_enabled=True,
        cantidad_owners=1,
    )
    resultado = evaluar_item_14(
        instalacion=_instalacion_valida(),
        org_login_esperado="org-valida",
        organizacion=organizacion,
        existe_repo_perfil=True,
    )
    assert not resultado.aprobado
