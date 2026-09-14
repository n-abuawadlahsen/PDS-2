# SPEC 14 S14.5.1: un solo Dockerfile, dos comandos de arranque (declarados en
# infra/render.yaml). Multietapa, imagen base fijada por digest (S14.5.2).
#
# Digest capturado el 12-sep-2026 (docs/PLAN-IMPLEMENTACION.md Etapa 0). Si el
# registro retirase este digest, fijar el nuevo entra por el procedimiento de
# correccion urgente de S14.10.5, con aviso a los revisores.
ARG PYTHON_DIGEST=sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

FROM python:3.12-slim@${PYTHON_DIGEST} AS constructor
# Mismo WORKDIR que la etapa `ejecucion`: los shebangs de los scripts de consola
# que uv/pip generan en `.venv/bin/` llevan la ruta absoluta donde se creo el
# entorno virtual. Si el entorno se creara en otra ruta y se copiara despues,
# esos scripts quedarian rotos ("exec: no such file or directory").
WORKDIR /app

RUN pip install --no-cache-dir uv==0.12.13

COPY pyproject.toml uv.lock ./
# Modo frozen: falla si el lockfile diverge del manifiesto (S14.5.1).
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim@${PYTHON_DIGEST} AS ejecucion
ARG GIT_SHA=desconocido
LABEL org.opencontainers.image.revision=${GIT_SHA}

RUN groupadd --system app && useradd --system --gid app --home /app app
WORKDIR /app

COPY --from=constructor /app/.venv /app/.venv
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${GIT_SHA}

USER app

# Sin HEALTHCHECK propio: la comprobacion de salud la hace la plataforma
# contra /salud (S14.5.1). Los dos comandos de arranque literales viven en
# infra/render.yaml, nunca aqui, para que no puedan divergir en silencio.
