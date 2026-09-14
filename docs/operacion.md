# Operación

Este documento registra las decisiones y procedimientos operativos que el SPEC (`docs/SPEC/14-infraestructura-y-despliegue.md`) exige dejar por escrito, y el registro fechado de incidencias. Se actualiza a medida que cada etapa del plan (`docs/PLAN-IMPLEMENTACION.md`) entra en producción — hoy solo cubre lo que Etapa 0 (infraestructura) y Etapa P1 (identidad y acceso) ya construyeron.

## Migraciones (SPEC 14 §14.8)

- **Hay una sola migración** (`backend/alembic/versions/0001_esquema_inicial.py`), regenerada con `alembic revision --autogenerate` cada vez que una etapa nueva añade tablas, mientras estemos antes del 16-sep-2026. No se crea una revisión `0002` antes de esa fecha.
- **`alembic downgrade` no se ejecuta nunca contra `producción`.** Existe en el código únicamente para poder probarse en `ensayo`/local. La función de arranque del trabajador (`aplicar_migraciones()` en `backend/app/infraestructura/migraciones.py`) solo expone `upgrade`.
- **El servicio web nunca migra.** Solo el trabajador (`python -m app.trabajos.ejecutor`) aplica migraciones al arrancar, tomando antes `pg_advisory_lock(hashtext('migraciones'))`.
- **Tablas nacidas vacías a la fecha de este documento** (12-sep-2026): `salud_proveedor_curso`, `estado_sistema`, `resultado_invariante`, `respaldo` (se llenan cuando se implemente `/operacion`, fuera del alcance de Etapa 0/P1), y todas las columnas/tablas que las etapas P2 en adelante todavía no escriben (`sesion_membresia.membresia_id` sin FK, `bitacora.curso_id`, `sincronizacion.curso_id`, etc. — ver comentarios en `backend/app/adaptadores/modelos_infraestructura.py` y `modelos_identidad.py`).

## Entornos (SPEC 14 §14.4)

- `local`: Postgres en Docker propio, `infra/docker-compose.local.yml` (puerto 5434, nunca compartido entre desarrolladores).
- `ensayo` y `producción`: pendientes de aprovisionar (Supabase/Render/Vercel) — requiere las cuentas y el dominio propio que el calendario de §14.13.3 fecha entre el 10 y el 13 de septiembre. No hay nada desplegado todavía fuera de local.

## Secretos (SPEC 14 §14.6)

Inventario cerrado de 15 claves en `backend/.env.example` (sin valores). Ninguna rotación se ha ejecutado todavía porque no hay entorno `ensayo`/`producción` desplegado.

## Registro de incidencias

_(vacío — ninguna incidencia registrada todavía; el proyecto no está desplegado fuera de local)_
