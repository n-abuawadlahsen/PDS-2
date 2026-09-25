# Operación

Este documento registra las decisiones y procedimientos operativos que el SPEC (`docs/SPEC/14-infraestructura-y-despliegue.md`) exige dejar por escrito, y el registro fechado de incidencias. Se actualiza a medida que cada etapa del plan (`docs/PLAN-IMPLEMENTACION.md`) entra en producción — hoy solo cubre lo que Etapa 0 (infraestructura) y Etapa P1 (identidad y acceso) ya construyeron.

## Migraciones (SPEC 14 §14.8)

- **Hay una sola migración** (`backend/alembic/versions/0001_esquema_inicial.py`), regenerada con `alembic revision --autogenerate` cada vez que una etapa nueva añade tablas, mientras estemos antes del 16-sep-2026. No se crea una revisión `0002` antes de esa fecha.
- **Desde el 16-sep-2026 cada cambio va en una revisión nueva y solo aditiva** (S14.8.2). `0002` (Etapa F3) añade `regla_fecha.retirada_en`. Se generan con `alembic revision --autogenerate --rev-id 000N` contra la base desechable `proyecto2_gen` ya llevada a la cabeza anterior, y se verifican con `alembic check`.
- **`alembic downgrade` no se ejecuta nunca contra `producción`.** Existe en el código únicamente para poder probarse en `ensayo`/local. La función de arranque del trabajador (`aplicar_migraciones()` en `backend/app/infraestructura/migraciones.py`) solo expone `upgrade`.
- **El servicio web nunca migra.** Solo el trabajador (`python -m app.trabajos.ejecutor`) aplica migraciones al arrancar, tomando antes `pg_advisory_lock(hashtext('migraciones'))`.
- **Tablas nacidas vacías a la fecha de este documento** (12-sep-2026): `salud_proveedor_curso`, `estado_sistema`, `resultado_invariante`, `respaldo` (se llenan cuando se implemente `/operacion`, fuera del alcance de Etapa 0/P1), y todas las columnas/tablas que las etapas P2 en adelante todavía no escriben (`sesion_membresia.membresia_id` sin FK, `bitacora.curso_id`, `sincronizacion.curso_id`, etc. — ver comentarios en `backend/app/adaptadores/modelos_infraestructura.py` y `modelos_identidad.py`).

## Entornos (SPEC 14 §14.4)

- `local`: Postgres en Docker propio, `infra/docker-compose.local.yml` (puerto 5434, nunca compartido entre desarrolladores).
- `ensayo` y `producción`: pendientes de aprovisionar (Supabase/Render/Vercel) — requiere las cuentas y el dominio propio que el calendario de §14.13.3 fecha entre el 10 y el 13 de septiembre. No hay nada desplegado todavía fuera de local.

## Secretos (SPEC 14 §14.6)

Inventario cerrado de 15 claves en `backend/.env.example` (sin valores). Ninguna rotación se ha ejecutado todavía porque no hay entorno `ensayo`/`producción` desplegado.

## Retirada de banderas de alcance (SPEC 01 §1.11, CA-1.11-06)

Una bandera se retira escribiendo su fecha en `retirada_el` dentro de `backend/app/dominio/alcance.py`, y solo con el criterio de aceptación de su etapa en verde. Desde ese momento queda activa también bajo `PERFIL_ALCANCE=parcial`. Titular de todas las retiradas de esta tabla: equipo del Proyecto 2; suplente: sin designar.

| Bandera | Etapa | Fecha comprometida | Retirada el | Criterio en verde |
|---|---|---|---|---|
| `tarea_modalidad_grupal` | F1 | 23-09-2026 20:00 | 25-09-2026 | `tests/api/test_aprovisionamiento_grupal.py` (CA-8.5-01, grupo `OPERATIVO`, estudiante en dos grupos sin frenar a los demás, salida sin revocación) y `tests/dominio/test_aprovisionamiento.py`/`test_fechas.py` (F1) |
| `tarea_multientrega` | F2 | 23-09-2026 20:00 | 25-09-2026 | `tests/api/test_multientrega.py` (renumerar, cero o dos finales imposibles, excluir sin borrar, mismos repositorios para todas las entregas, modalidad congelada) y `tests/dominio/test_multientrega.py` |
| `fechas_excepciones` | F3 | 23-09-2026 20:00 | 25-09-2026 | `tests/api/test_fechas_excepciones.py` (CA-9.3-01, CA-9.3-02, CA-9.4-01 a CA-9.4-04, cadencia de 1 min antes de un cierre, override no interpretable, override retirado que sigue en el historial) y `tests/dominio/test_fechas_excepciones.py` |

Las retiradas de F1, F2 y F3 llegan dos días después de la fecha comprometida.

## Registro de incidencias

_(vacío — ninguna incidencia registrada todavía; el proyecto no está desplegado fuera de local)_
