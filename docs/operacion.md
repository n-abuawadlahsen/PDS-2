# Operación

Este documento registra las decisiones y procedimientos operativos que el SPEC (`docs/SPEC/14-infraestructura-y-despliegue.md`) exige dejar por escrito, y el registro fechado de incidencias. Se actualiza a medida que cada etapa del plan (`docs/PLAN-IMPLEMENTACION.md`) entra en producción — hoy solo cubre lo que Etapa 0 (infraestructura) y Etapa P1 (identidad y acceso) ya construyeron.

## Migraciones (SPEC 14 §14.8)

- **Hay una sola migración** (`backend/alembic/versions/0001_esquema_inicial.py`), regenerada con `alembic revision --autogenerate` cada vez que una etapa nueva añade tablas, mientras estemos antes del 16-sep-2026. No se crea una revisión `0002` antes de esa fecha.
- **Desde el 16-sep-2026 cada cambio va en una revisión nueva y solo aditiva** (S14.8.2). `0002` (Etapa F3) añade `regla_fecha.retirada_en`. `0003` (Etapa F4) crea `version_entrega` y el disparador `version_entrega_inmutable`, que rechaza todo `DELETE` y todo `UPDATE` fuera de la lista cerrada de columnas mutables; la limpieza de pruebas (`backend/tests/conftest.py`) es el único lugar que lo desactiva, y solo durante su `DELETE`. Se generan con `alembic revision --autogenerate --rev-id 000N` contra la base desechable `proyecto2_gen` ya llevada a la cabeza anterior, y se verifican con `alembic check`. `0004` (Etapa F5) crea el espejo de actividad (`evento_webhook`, `evento_push`, `commit`, `autoria_commit`, `identidad_git`) y `curso.ingesta_actividad_desde`. `0005` (Etapa F6) crea `metrica_repositorio_dia`, `participacion_entrega` y `resumen_tarea`.
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
| `versiones_entrega` | F4 | 23-09-2026 20:00 | 25-09-2026 | `tests/api/test_versiones.py` (CA-9.6-01, 9.6-04, 9.6-05, 9.6-06, 9.8-01, 9.8-02, 9.8-04, 9.8-05, 9.9-01, 9.9-02, 9.12-02, GitHub sin acceso pospuesto, CA-8.2-03) y `tests/dominio/test_versiones.py` |
| `ingesta_actividad` | F5 | 30-09-2026 20:00 | 25-09-2026 | `tests/api/test_actividad.py` (firma inválida 401 sin efecto, reentrega sin duplicar, atribución, `push --force` con huérfanos, reconciliación por ETag, evento sin destino que caduca sin incidencia, `member`/`repository`, identidades con propagación desmarcada y revelado auditado, discrepancia espejo/GitHub), `tests/adaptadores/test_cliente_github_real.py` (CA-6.8-04) y `tests/arquitectura/test_atribucion_sin_login.py`. El criterio operativo de S10.2.6 —relleno ejecutado y `ultimo_backfill_en` escrito en todos los repositorios— se cumple en cada entorno con el primer `barrido_completo_actividad`, y queda visible en `curso.ingesta_actividad_desde` |
| `tablero_actividad` | F6 | 30-09-2026 20:00 | 25-09-2026 | `tests/api/test_tablero.py` (CA-10.4-01 idempotencia, tablero con `X-Llamadas-Externas: 0`, CA-10.5-03, CA-10.5-02, CA-10.4-02, CA-10.5-05, CA-10.8-02, silenciar, cooldown, CSV auditado, vista de curso) y `tests/dominio/test_metricas.py` (estado agregado de 9 valores, ventana `(inicio, cierre]`, índice de desequilibrio, cuartiles) |
| `repositorio_timeline` | F7 | 30-09-2026 20:00 | 25-09-2026 | `tests/api/test_timeline.py` (CA-10.9-01 historia reescrita con huérfanos visibles y evento en el ciclo de vida, CA-10.9-02 tramos sin actividad colapsados sin perder commits y destacados de primera participación y vuelta al trabajo, CA-10.9-03 franja idéntica a la comparación del tablero, CA-10.9-04 cero con causa, CA-10.9-05 hitos manuales con `tarea.administrar` y nota de hasta 140 caracteres, CA-10.9-06 sin acceso docente no hay enlace sino motivo y `X-Llamadas-Externas: 0`, repositorio vacío con causa). El panel de identidades de la misma pantalla usa los endpoints de F5 |
| `tarea_archivado` | F8 | 30-09-2026 20:00 | 25-09-2026 | `tests/api/test_archivado.py` (archivar deja `ARCHIVADO` en la base y en GitHub con la captura previa intacta, segundo aviso al ejecutar, `tarea.estado = ARCHIVADA` y `TAREA_ARCHIVADA` en la transacción del último repositorio, desarchivar lo revierte con `REPOSITORIO_DESARCHIVADO`; un ayudante con `tarea.administrar` recibe `403` con motivo en las tres acciones; guarda 1 con cierre futuro y con vencida sin captura que exige confirmación escrita; guardas 2 y 3 y reevaluación del trabajo antes de cada repositorio) y `tests/dominio/test_archivado.py` (las cinco guardas de `puede_archivar`) |

Las retiradas de F1 a F4 llegan dos días después de la fecha comprometida. `versiones_entrega` entra en servicio el 25-09-2026: toda entrega cuya fecha venció antes se captura igual con su corte original y `motivo = CAPTURA_TARDIA_POR_ALCANCE` (SPEC 09 §9.6.8).

## Webhook de la GitHub App (F5)

La App debe apuntar su URL de webhook a `https://<servicio-api>/webhooks/github` (directo al backend, no al proxy de Vercel, que solo reenvía `/api` y `/auth`) con el secreto `GITHUB_WEBHOOK_SECRET`, suscrita a exactamente `push`, `create`, `delete`, `repository`, `member`, `installation` e `installation_repositories`. Una firma inválida responde `401` y queda registrada sin procesarse; durante una rotación se acepta también `GITHUB_WEBHOOK_SECRET_ANTERIOR`.

## Registro de incidencias

_(vacío — ninguna incidencia registrada todavía; el proyecto no está desplegado fuera de local)_

## Archivado de tareas (Etapa F8)

- **Guarda 4, el aviso previo, es una acción propia**: `POST /api/cursos/{id}/tareas/{id}/archivar/aviso` (mismo permiso y rol que archivar) encola un mensaje `aviso_archivado_previo` por persona en el outbox. La guarda se cumple cuando todos los destinatarios lo recibieron (`ENVIADO`) y el último envío tiene al menos 14 días. Al ejecutar, cada repositorio archivado encola `aviso_archivado`. Con el canal de Canvas `BLOQUEADO` (A-227) se archiva igual solo con una confirmación escrita que declara el número de estudiantes sin aviso; queda en `bitacora` (`ARCHIVADO_SOLICITADO`).
- **Guarda 5 (correcciones terminales) se reporta y se cumple** mientras no exista el módulo de correcciones; `puede_archivar` ya recibe `correcciones_abiertas` y la bloquea en cuanto se le pase un número.
- **Destinatarios del aviso**: los estudiantes con `acceso_repositorio` en el repositorio, salvo `SIN_MAPEO`, `DESAPARECIDA` y `REVOCADO`, que no tienen acceso que perder.
- **Un repositorio que nunca llegó a crearse en GitHub** (sin `github_repo_id`) no se archiva ni impide que la tarea quede `ARCHIVADA`.
- **Desarchivar** abre todos los repositorios `ARCHIVADO` de la tarea, los deja `DEGRADADO` (igual que el webhook `unarchived`: la reconciliación de accesos reevalúa `OPERATIVO`) y devuelve la tarea al estado que tenía antes de archivarse, leído de la última `TAREA_ARCHIVADA` en `bitacora`.
- El doble de GitHub rechaza con `403` crear etiquetas en un repositorio archivado, como GitHub.
