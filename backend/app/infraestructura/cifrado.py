"""Cifrado del token de Canvas y llavero versionado (SPEC 14 S14.6.4).

AES-256-GCM, nonce aleatorio por fila, `curso_id` como additional authenticated
data (AAD) -> una fila cifrada no puede reutilizarse en otro curso. El llavero es
un mapa {version: clave de 32 bytes}; se cifra siempre con la version activa y se
descifra con la version que la propia fila declara (`version_clave`).
"""

from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class DescifradoFallido(RuntimeError):
    """La fila no se pudo descifrar: llave ausente, AAD incorrecta o dato corrupto.

    Tratado por el llamador como credencial invalida (S14.6.4): la credencial pasa
    a INVALIDA y el curso se degrada de forma controlada, nunca como error 500.
    """


@dataclass(frozen=True)
class ValorCifrado:
    version_clave: int
    nonce: bytes
    texto_cifrado: bytes

    def empaquetar(self) -> bytes:
        return self.version_clave.to_bytes(2, "big") + self.nonce + self.texto_cifrado

    @staticmethod
    def desempaquetar(datos: bytes) -> ValorCifrado:
        version_clave = int.from_bytes(datos[:2], "big")
        nonce = datos[2:14]
        texto_cifrado = datos[14:]
        return ValorCifrado(version_clave, nonce, texto_cifrado)


class Llavero:
    """Llavero versionado de claves AES-256 (S14.6.4, RG-138, A-191)."""

    def __init__(self, claves: dict[int, bytes], version_activa: int) -> None:
        if version_activa not in claves:
            raise ValueError("version_activa ausente del llavero")
        for version, clave in claves.items():
            if len(clave) != 32:
                raise ValueError(f"la clave de version {version} no tiene 32 bytes")
        self._claves = dict(claves)
        self._version_activa = version_activa

    @property
    def version_activa(self) -> int:
        return self._version_activa

    def cifrar(self, texto_plano: bytes, *, curso_id: uuid.UUID) -> ValorCifrado:
        aad = _aad_de_curso(curso_id)
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._claves[self._version_activa])
        texto_cifrado = aesgcm.encrypt(nonce, texto_plano, aad)
        return ValorCifrado(self._version_activa, nonce, texto_cifrado)

    def descifrar(self, valor: ValorCifrado, *, curso_id: uuid.UUID) -> bytes:
        clave = self._claves.get(valor.version_clave)
        if clave is None:
            raise DescifradoFallido(
                f"no existe la version de clave {valor.version_clave} en el llavero"
            )
        aad = _aad_de_curso(curso_id)
        aesgcm = AESGCM(clave)
        try:
            return aesgcm.decrypt(valor.nonce, valor.texto_cifrado, aad)
        except InvalidTag as exc:
            raise DescifradoFallido(
                "fallo de autenticacion AEAD: llave, AAD o dato incorrectos"
            ) from exc

    def filas_por_recifrar(self, versiones_en_uso: set[int]) -> set[int]:
        """Versiones presentes en datos pero distintas de la activa (recifrado perezoso)."""
        return {v for v in versiones_en_uso if v != self._version_activa}


def huella_token(token_plano: str) -> str:
    """sha256 truncado (SPEC 05 S5.2.5): detecta el mismo token en dos cursos
    sin poder reconstruir el token a partir de la huella."""
    return hashlib.sha256(token_plano.encode()).hexdigest()[:16]


def _aad_de_curso(curso_id: uuid.UUID) -> bytes:
    return f"curso:{curso_id}".encode()
