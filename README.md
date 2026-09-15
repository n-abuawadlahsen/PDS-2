# Proyecto 2 (ICC4201)

App web que coordina Canvas y GitHub para el equipo docente de un curso de programación. Ver [`docs/PLAN-IMPLEMENTACION.md`](docs/PLAN-IMPLEMENTACION.md) para el plan de implementación por etapas, [`docs/SPEC/`](docs/SPEC/) para la especificación y [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) para la arquitectura.

## Estado

Backend de la entrega parcial (`PERFIL_ALCANCE=parcial`) implementado, de la **Etapa 0** a la **Etapa P8**:

- Etapa 0: infraestructura (motor de trabajos, esquema inicial `0001`, cifrado, logs).
- P1 y P2: acceso con Google y equipo docente.
- P3 a P5: vinculación de Canvas y GitHub, checklist, espejo de estudiantes, secciones y grupos.
- P6: mapeo estudiante ↔ GitHub y Pendientes.
- P7: tarea individual con una entrega y repositorio base.
- P8: aprovisionamiento automático de repositorios, aviso por Canvas y lectura de fechas.

Falta, entre otras cosas, el receptor de webhooks de GitHub y las rutas de ajustes, operación y alcance del curso.

## Estructura

```
backend/    FastAPI (Python 3.12), SQLAlchemy + Alembic, motor de trabajos propio
frontend/   React + Vite + TypeScript
infra/      docker-compose para desarrollo local, render.yaml (Blueprint de Render)
docs/       SPEC normativo y plan de implementación
```

## Levantar en local

**1. Base de datos** (Postgres 16 en el puerto 5434):

```bash
docker compose -f infra/docker-compose.local.yml up -d
```

**2. Backend** (tres procesos: migración, API y trabajador):

```bash
cd backend
pip install uv
uv sync --dev
cp .env.example .env   # completar con valores locales (ver más abajo)
uv run alembic upgrade head          # lee DATABASE_URL del entorno o del .env
uv run uvicorn app.main:app --reload --port 8000
uv run python -m app.trabajos.ejecutor   # en otra terminal: sin él no corre ningún trabajo
```

Valores locales mínimos del `.env`:

- `DATABASE_URL=postgresql+psycopg://proyecto2:proyecto2_local@localhost:5434/proyecto2`
- `VITE_API_BASE_URL=http://localhost:8000`, `FRONTEND_ORIGEN=http://localhost:5173` y `COOKIE_DOMINIO=localhost`.
- `CANVAS_MODO=doble` y `GITHUB_MODO=doble`: dobles en memoria, sin llamar a ningún proveedor.
- `CANVAS_BASE_URL=https://canvas-doble.local` y `CANVAS_INSTANCIAS=[{"base_url": "https://canvas-doble.local", "nombre_visible": "Canvas doble"}]`.

Para generar una clave de 32 bytes en base64 (sirve para `SIGNING_KEY`, y para `APP_ENCRYPTION_KEYS` con el formato `1:<clave>` y `APP_ENCRYPTION_KEY_ACTIVA=1`):

```bash
uv run python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
```

Google OAuth real requiere credenciales OIDC en Google Cloud Console (tipo "Web application", origen `http://localhost:5173`, URI de redirección `http://localhost:8000/auth/google/callback`) y `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` reales en `.env`.

**3. Frontend:**

```bash
cd frontend
npm install
cp .env.example .env   # en local: VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

## Frontend y apariencia

El frontend de la parcial usa una navegación compartida para cursos, un resumen de preparación y tres paletas seleccionables desde Perfil. La guía [`docs/FRONTEND-DISENO.md`](docs/FRONTEND-DISENO.md) explica la estructura, cómo editar todos los colores en `frontend/src/styles/themes.css`, cómo cambiar el tema predeterminado en `frontend/src/config/theme.ts` y qué límites de integración siguen presentes.

Las correcciones de invitaciones, cierre de cuenta, sincronización docente GitHub y login tras el arranque de Render están documentadas en [`docs/CORRECCIONES-PARCIAL.md`](docs/CORRECCIONES-PARCIAL.md). Incluyen la migración incremental `0002` y la configuración de correo real.

## Pruebas y calidad

> **Cuidado:** las pruebas borran todas las tablas después de cada caso. Córrelas siempre contra una base aparte (por ejemplo `proyecto2_test`), nunca contra la de desarrollo.

```bash
cd backend
DATABASE_URL=postgresql+psycopg://proyecto2:proyecto2_local@localhost:5434/proyecto2_test \
  CANVAS_MODO=doble GITHUB_MODO=doble uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run alembic check
```

```bash
cd frontend
npm run build               # tsc + vite build
```

Las mismas comprobaciones corren en `.github/workflows/puertas.yml` en cada push/PR a `main`.

## Despliegue

Tres piezas:

- **Base de datos:** Supabase.
- **API y trabajador:** Render, desde una sola imagen Docker, con `infra/render.yaml` como Blueprint.
- **Frontend:** Vercel, con la raíz del proyecto en `frontend/`.

**Mismo origen:** el navegador solo habla con Vercel. `frontend/vercel.json` reenvía `/api/*` y `/auth/*` a la API de Render, así que las cookies de sesión quedan en el dominio de Vercel. Una API en `onrender.com` con un frontend en `vercel.app` no puede compartir cookies: son sitios distintos.

- En Vercel, `VITE_API_BASE_URL` va vacía o no se declara.
- En Render, `FRONTEND_ORIGEN` y `VITE_API_BASE_URL` valen la URL pública de Vercel.
- En Render, `COOKIE_DOMINIO` no se declara.
- La URL de Render está fija en `frontend/vercel.json` (hoy `https://proyecto2-api-oyxf.onrender.com`); si el servicio cambia de URL, se corrige ahí.

**Plan gratuito de Render (el que usamos, sin tarjeta):** los Blueprints y los *background workers* piden tarjeta, así que se crea a mano **un solo web service gratuito**:

- **Name** `proyecto2-api`, **Language** Docker, **Root Directory** `backend`, instancia **Free**.
- **Docker Command** `bash arranque_plan_gratuito.sh`: corre la API y el trabajador en el mismo contenedor. Si uno de los dos muere, el contenedor termina y Render lo reinicia.
- **Health Check Path** `/salud`.
- **Variables:** todas en *Environment → Add from .env* (no hay grupo compartido).
- **Se duerme** tras 15 minutos sin tráfico, y con él el trabajador. Un ping externo gratuito a `/salud` cada 10 minutos (cron-job.org o UptimeRobot) lo mantiene despierto; las 750 horas gratis al mes alcanzan para un servicio encendido todo el mes.
- `infra/render.yaml` queda para cuando haya plan de pago (dos servicios, como pide el SPEC).

**Migraciones:** las aplica el trabajador al arrancar, con un cerrojo. La API nunca migra; `GET /estado` muestra la revisión actual y la esperada.

**Supabase:** Render no tiene IPv6, así que se usa el *pooler* compartido en **modo sesión**:

- URL: `postgresql+psycopg://postgres.<ref>:<clave>@<host-del-pooler>:5432/postgres?sslmode=require`
- El host sale de *Connect → Session pooler* (algo como `aws-0-us-east-1.pooler.supabase.com`).
- El modo transacción (puerto 6543) rompe los cerrojos consultivos de sesión.
- Si la clave tiene caracteres especiales, se codifica en la URL.
