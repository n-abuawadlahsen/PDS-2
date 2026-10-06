"""Servidor de prueba aislado. No añade endpoints ni cambia el acceso de producción.

Usa una BD Docker efímera propia, los adaptadores dobles existentes y una sesión
opaca creada por las utilidades de pruebas del backend. Ningún secreto se imprime.
Playwright lo inicia/finaliza; las cookies temporales se guardan con modo 0600.
"""

from __future__ import annotations

import atexit
import base64
import json
import os
import secrets
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]
BACKEND = FRONTEND.parent / "backend"
STATE = FRONTEND / ".backend-test-state.json"
PYTEST = sys.argv[1:2] == ["--pytest"]
CONTAINER = f"pds2-ui-review-{os.getpid()}"
children: list[subprocess.Popen] = []


def cleanup():
    for child in children:
        child.terminate()
    for child in children:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
    if not PYTEST:
        STATE.unlink(missing_ok=True)
    subprocess.run(
        ["docker", "rm", "-f", CONTAINER],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


atexit.register(cleanup)
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
password = secrets.token_urlsafe(24)
subprocess.run(
    [
        "docker",
        "run",
        "--rm",
        "-d",
        "--name",
        CONTAINER,
        "--tmpfs",
        "/var/lib/postgresql/data",
        "-p",
        f"127.0.0.1:{port}:5432",
        "-e",
        "POSTGRES_DB=pds2_ui_review",
        "-e",
        "POSTGRES_USER=pds2_ui_review",
        "-e",
        f"POSTGRES_PASSWORD={password}",
        "postgres:16",
    ],
    check=True,
    stdout=subprocess.DEVNULL,
)
for _ in range(60):
    check = subprocess.run(
        ["docker", "exec", CONTAINER, "pg_isready", "-U", "pds2_ui_review"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if check.returncode == 0:
        break
    time.sleep(0.5)
else:
    raise RuntimeError("No inició PostgreSQL de prueba")

# Sobrescribe todos los nombres del ejemplo; nunca hereda secretos del .env real.
for line in (BACKEND / ".env.example").read_text().splitlines():
    if line and not line.startswith("#") and "=" in line:
        os.environ[line.split("=", 1)[0]] = ""
key = base64.b64encode(os.urandom(32)).decode()
os.environ.update(
    {
        "ENTORNO": "local",
        "PERFIL_ALCANCE": "parcial" if PYTEST else "completo",
        "CANVAS_MODO": "doble",
        "GITHUB_MODO": "doble",
        "CANVAS_BASE_URL": "https://canvas-doble.local",
        "CANVAS_INSTANCIAS": json.dumps(
            [
                {
                    "base_url": "https://canvas-doble.local",
                    "nombre_visible": "Canvas de ensayo",
                }
            ]
        ),
        "COMUNICACIONES_SALIENTES": "pausadas",
        "EMAIL_PROVEEDOR": "sin_configurar",
        "DATABASE_URL": f"postgresql+psycopg://pds2_ui_review:{password}@127.0.0.1:{port}/pds2_ui_review",
        "APP_ENCRYPTION_KEYS": f"1:{key}",
        "APP_ENCRYPTION_KEY_ACTIVA": "1",
        "SIGNING_KEY": key,
        "GOOGLE_CLIENT_ID": "local-no-oauth",
        "GOOGLE_CLIENT_SECRET": "local-no-oauth",
        "GITHUB_APP_ID": "1",
        "GITHUB_APP_PRIVATE_KEY": "doble",
        "GITHUB_WEBHOOK_SECRET": "doble",
        "EMAIL_FROM": "prueba@example.test",
        "EMAIL_FROM_NOMBRE": "Prueba local",
        "EMAIL_REPLY_TO": "prueba@example.test",
        "EMAIL_DOMINIO_VERIFICADO": "example.test",
        "FRONTEND_ORIGEN": "http://127.0.0.1:4187",
        "VITE_API_BASE_URL": "http://127.0.0.1:4187",
        "APP_VERSION": "prueba-frontend",
    }
)
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))
subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    check=True,
    stdout=subprocess.DEVNULL,
)
# Verifica ida y vuelta de la corrección autorizada sobre la base vacía propia.
subprocess.run(
    [sys.executable, "-m", "alembic", "downgrade", "0010"],
    check=True,
    stdout=subprocess.DEVNULL,
)
subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    check=True,
    stdout=subprocess.DEVNULL,
)
if PYTEST:
    args = sys.argv[2:]
    cobertura = any(arg.startswith("--cov") for arg in args)
    sys.exit(
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *([] if cobertura else ["--no-cov"]),
                *args,
            ]
        ).returncode
    )

from tests.api.test_cursos import _crear_usuario_con_sesion  # noqa: E402

_, token = _crear_usuario_con_sesion(
    email="revision.frontend@gmail.com", nombre="Docente de ensayo"
)
with os.fdopen(
    os.open(STATE, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600), "w"
) as file:
    json.dump({"sesion": token, "csrf": secrets.token_urlsafe(24)}, file)
children.append(
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8017",
            "--no-access-log",
        ]
    )
)
children.append(
    subprocess.Popen(
        [sys.executable, "-m", "app.trabajos.ejecutor"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
)
print("API local de revisión con dobles y base aislada preparada.", flush=True)
children[0].wait()
