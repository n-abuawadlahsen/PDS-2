# Plan de implementación por etapas — Proyecto 2

**Qué es este documento.** Es el `docs/SPEC/` (14 capítulos, ~275K tokens) reorganizado en etapas de trabajo, ordenadas por a qué entrega sirven. No repite el SPEC: lo resume a lo estrictamente necesario para implementar cada etapa, y remite a la sección exacta del capítulo correspondiente sólo para los casos borde. **Si te asignan "implementá la etapa Pn/Fn", leé sólo la Etapa 0 (fundamentos) más esa etapa — no hace falta abrir nada más**, salvo que la propia etapa te remita a un capítulo para un caso borde puntual.

**Fuente de la verdad.** El enunciado (`docs/enunciado-proyecto2.md`, 59 requisitos `R2.x.y`) define *qué* hay que construir. `docs/ARQUITECTURA.md` §17 (A-157) y §20 (trazabilidad) definen *qué parte de cada requisito* es de la entrega parcial (16-sep-2026) y cuál de la final (6-oct-2026). Los capítulos 1 (§1.11) y 13 (§13.3.3) del SPEC repiten esa misma tabla con el mecanismo concreto que la aplica: una variable de entorno `PERFIL_ALCANCE ∈ {parcial, completo}` que gobierna qué rutas registra el backend y un catálogo cerrado de **doce banderas** (`tarea_multientrega`, `tarea_modalidad_grupal`, `fechas_excepciones`, `versiones_entrega`, `tarea_archivado`, `tablero_actividad`, `repositorio_timeline`, `ingesta_actividad`, `mis_notificaciones`, `informe_diario`, `comunicaciones_automaticas`, `correccion`), cada una con fecha de retirada entre el 23-sep y el 5-oct. El capítulo 14 (§14.7.4) trae el catálogo de los 31 trabajos en segundo plano con su fecha exacta de entrada en servicio, que es el mecanismo formal equivalente para todo lo que corre en segundo plano.

**Aviso importante sobre cinco capítulos del SPEC (8, 9, 10, 11, 12).** No tienen su propia sección "Reparto entre la entrega parcial y la final" — es una excepción al patrón de los demás capítulos, verificada exhaustivamente capítulo por capítulo. El reparto de sus requisitos entre parcial y final que este plan usa **no viene de esos capítulos**: se reconstruyó cruzando la tabla de A-157/§1.11 (qué requisito está completo en cada fecha), la tabla de registro de rutas por perfil del capítulo 13 §13.3.3, y la columna "entra en servicio" del catálogo de 31 trabajos del capítulo 14 §14.7.4. Donde una etapa de este plan reparte un capítulo funcional entre dos entregas, se indica explícitamente con qué de esas tres fuentes se hizo el corte.

**Nota sobre el capítulo 7 del SPEC (`estudiantes-y-grupos.md`).** Cuando se redactaron por primera vez las etapas P5 y P6 de este plan, el capítulo 7 estaba incompleto (sólo 116 líneas, hasta §7.2) y esas etapas se reconstruyeron citando directo `docs/ARQUITECTURA.md`. El capítulo 7 ya se completó (494 líneas, hasta §7.10) y las etapas P5/P6 se actualizaron para citarlo como fuente principal. Si encontrás una referencia residual a "capítulo 7 incompleto" en otra parte de este documento, es un resto sin actualizar — el capítulo 7 completo manda.

**Fundamentos que no se repiten en cada etapa** (rigen en todas, fijados en el capítulo 1 del SPEC): español de Chile, tratamiento de "tú", sin emojis, vocabulario cerrado — no hay sinónimos para "curso", "sección", "sujeto", "entrega", "versión", "invitación", etc. Todo instante se guarda en UTC (`timestamptz`) y se muestra en la zona del curso con formato `dd-MM-yyyy HH:mm (Zona)`, nunca una hora desnuda. Todo estado interno se traduce en pantalla, nunca en mayúsculas. Ninguna vista llama a Canvas o a GitHub para renderizarse (Ley 1: espejo, no caché) — toda lectura externa ocurre en un trabajo de fondo y se persiste antes. Nada se sobreescribe: versiones, mapeos, fechas efectivas y notas publicadas son *append-only* con una fila vigente (Ley 2). La clave de toda entidad externa es su identificador numérico estable, nunca el nombre o login (Ley 3). El `commit_sha` persistido es la evidencia normativa de una entrega, nunca el tag de Git (Ley 4). Un límite de una API externa nunca se pinta como error propio: se muestra como estado transitorio con hora de reintento (Ley 5). Ninguna clave foránea usa `ON DELETE CASCADE` ni `SET NULL` — siempre `RESTRICT`. La aplicación nunca borra un dato de dominio (commit, versión, bitácora, nota publicada, mapeo): todo se modela con estado.

**Permisos, en una línea:** dos roles de curso (`PROFESOR`, `AYUDANTE`); nueve permisos (dos implícitos: `curso.ver`, `correccion.corregir`; siete configurables, de los cuales cinco son concedibles a un ayudante — `tarea.administrar`, `mapeo.editar`, `correccion.asignar`, `nota.publicar`, `comunicacion.enviar` — y dos son NO CONCEDIBLES — `curso.administrar`, `equipo.administrar`). Cada etapa cita el permiso exacto que exige cada acción.

---

## Etapa 0 — Fundamentos e infraestructura (antes de cualquier otra etapa)

**Entrega:** ninguna directamente — es prerequisito de todas. Debe estar completa y en verde **antes del 16 de septiembre**, aunque nada de lo que produce se demuestre ese día.

**Requisitos que cubre:** ninguno de forma directa; sostiene la totalidad de R2.x.y como cimiento técnico.

**Depende de:** nada (es la primera etapa).

### Qué hay que construir

**Estructura del monorepo** (público, único, `docs/SPEC/14-infraestructura-y-despliegue.md` §14.1):

```
backend/app/dominio/          reglas de negocio puras, sin I/O, sin importar ORM/HTTP
backend/app/adaptadores/       ClienteCanvas, ClienteGitHub, ProveedorCorreo, repos ORM
backend/app/api/               rutas y esquemas Pydantic
backend/app/trabajos/          los 31 trabajos del catálogo (ejecutor)
backend/app/infraestructura/   config, cifrado, logs, migraciones, cerrojos, banderas
frontend/                      SPA React (Vite)
infra/                         render.yaml, guiones de medición y semilla de demo
docs/                          este SPEC y este plan
.github/workflows/             exactamente 3 workflows (CI de puertas, dos de operación)
```

Una prueba de arquitectura falla la construcción si `dominio/` importa un ORM, un cliente HTTP o un framework — es la puerta de pureza que hace verificable que las reglas de negocio no dependen de infraestructura.

**Cuatro servicios contratados, ninguno más:**

| Servicio | Proveedor | Plan | Ejecuta |
|---|---|---|---|
| `api` (web) | Render | Pago mínimo | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --timeout-graceful-shutdown 25` |
| `trabajador` (worker) | Render | Pago mínimo | `python -m app.trabajos.ejecutor` (misma imagen Docker) |
| Base de datos | Supabase | Gratuito | PostgreSQL único — no hay Redis ni almacén de objetos |
| Frontend | Vercel | Gratuito | Integración Git nativa, `npm ci`, Node 22.x fijado |

Dockerfile único multietapa (`constructor` con lockfile en modo `frozen`, `ejecucion` con usuario no root), imagen base `python:3.12-slim` fijada **por digest**, no por tag. `infra/render.yaml` declara los dos servicios de Render como código — nunca se edita a mano en el panel. Despliegue disparado únicamente por integración a `main` (nunca por deploy hook).

**Tres entornos, separación física completa:** `produccion`, `ensayo` (Supabase, organización y GitHub App y correo propios; arranca con `CANVAS_MODO=doble` y grabaciones, para no tocar nunca datos reales de estudiantes) y `local` por desarrollador (Postgres en Docker propio, nunca compartido). Guarda de arranque: el proceso **no arranca** si `CANVAS_BASE_URL` de `ensayo` coincide con la de `produccion`. Dominio propio con subdominios `app.<dominio>`/`api.<dominio>` (prod) y `app-ensayo.<dominio>`/`api-ensayo.<dominio>` (ensayo) — nunca `*.vercel.app` ni `*.onrender.com`.

**Tablas de infraestructura propia** (parte del censo de 72, todas se crean en la única migración):

| Tabla | Columnas clave | Para qué |
|---|---|---|
| `trabajo` | `tipo, clave_idempotencia (único parcial en no-terminales), curso_id, payload, estado, intentos, max_intentos, proximo_intento_en, tomado_por, tomado_en, coste_api` | Cola de trabajos — sustituye a Redis/Celery; `SELECT … FOR UPDATE SKIP LOCKED` |
| `trabajo_periodico` | `tipo, curso_id, cadencia_segundos, proxima_ejecucion, ultima_ejecucion, activo`, único `(tipo, curso_id)` | Planificador, tick cada 30 s |
| `presupuesto_api` | `ambito, ambito_id, cubo, capacidad, restante, reinicio`, único `(ambito, ambito_id, cubo)` | Los 4 cubos de límite de tasa: `PRIMARIO`, `CONTENIDO`, `GRAFO` (GitHub) y `CANVAS` |
| `cubo_tasa` | PK `(clave, ventana_inicio)` | Limitador de tasa de rutas públicas (retención 24h/6h) |
| `bitacora` | `accion` (enum cerrado), `entidad` (contra el censo de 72), `actor`, `curso_id`, `antes`/`despues` jsonb | Auditoría *append-only* |
| `incidencia` | `tipo` (catálogo cerrado de 51), `severidad`, `sujeto_tipo`, `sujeto_id`, `abierta`, `resuelta_en`, `silenciada` | Alertas al equipo docente |
| `sincronizacion` | `curso_id, recurso, resultado (OK/PARCIAL/TRUNCADA/FALLIDA), contadores jsonb` | Rastro de cada ciclo de sincronización |
| `cursor_sincronizacion` | `curso_id, recurso, referencia, etag, ultimo_head_sha, ultimo_backfill_en, estado`, único `(curso_id, recurso, referencia)` | Punteros incrementales por curso/recurso |
| `salud_proveedor_curso`, `estado_sistema`, `resultado_invariante`, `respaldo` | — | Panel de operación, invariantes, respaldo |

**Migración única de esquema, anterior al 16-sep** (Alembic): crea las **72 entidades del censo completo de una vez**, incluidas las que no se usarán hasta la entrega final, todos los `CHECK` de catálogos cerrados y todos los índices únicos parciales. Nunca hay una segunda migración de esquema antes del 6-oct salvo corrección de fallo documentada; después del 16-sep sólo se admiten migraciones **aditivas** (expand-contract, nunca `DROP`/`ALTER TYPE`/cambio de clave).

**Motor de trabajos en segundo plano — cinco garantías, no negociables:**
1. Clave de idempotencia única vía índice único parcial en BD (no en memoria).
2. Encolar el trabajo y el cambio de dominio ocurren en la misma transacción.
3. Se persiste la intención **antes** de la llamada externa, se lee antes de todo efecto (un reinicio a mitad de operación es inocuo).
4. Retroceso exponencial con *jitter* y tope, respetando `retry-after`.
5. Serialización por curso con **dos espacios de cerrojo**, nunca uno: `pg_advisory_lock(1, curso_id)` para todo el tráfico con Canvas (una sola petición simultánea) y `pg_advisory_lock(2, curso_id)` para todo el tráfico con GitHub (concurrencia máxima 4, limitada por presupuesto, no por el cerrojo). Ningún trabajo retiene un cerrojo mientras espera al otro; quien necesita los dos los toma siempre en orden 1→2.

**Clasificación de errores en tres familias**, aplicada de forma idéntica a Canvas y a GitHub en todas las etapas siguientes: `TRANSITORIO` (429/5xx/timeout → retroceso exponencial), `BLOQUEANTE` (403/401 con credencial válida → no reintenta en bucle, reevalúa cada 30 min, degrada sólo la capacidad afectada sin invalidar toda la credencial), `PERMANENTE` (4xx de validación → cero reintentos, estado terminal). Un `403` no reconocido se clasifica siempre `BLOQUEANTE`, nunca `PERMANENTE`.

**Secretos:** inventario cerrado de 15 claves (`.env.example` las lista sin valores); el token de Canvas es el único secreto persistido, cifrado AES-256-GCM con *nonce* por fila y `curso_id` como *additional authenticated data*; llavero versionado (`APP_ENCRYPTION_KEYS` + `APP_ENCRYPTION_KEY_ACTIVA` + `credencial_canvas.version_clave`) con rotación en línea y recifrado perezoso. Ningún token de GitHub se persiste nunca — se emite en caliente desde la GitHub App.

**Endpoints técnicos de esta etapa:** `GET /salud` (sin sesión, sin tocar BD, <50ms, sin límite de tasa), `GET /estado` (forma anónima sin sesión con booleanos agregados; forma completa con sesión acotada a cursos propios), `POST /interno/latido` (HMAC del vigilante externo), `GET /api/capacidades` (perfil + banderas activas — única fuente de navegación del frontend).

**CI/CD:** un único workflow `.github/workflows/puertas.yml` con 10 puertas de herramienta (lint, tipos, pruebas unitarias, pruebas de integración, cobertura de dominio ≥70%, etc.) + 8 puertas de contrato (autorización, rutas por perfil, catálogos cerrados generados desde `dominio/estados.py`, pureza de `dominio/`, superficie sin sesión, prohibición de `ON DELETE CASCADE`, prohibición de `DELETE /repos/{owner}/{repo}`, cobertura de capacidades degradadas). Cualquier puerta roja bloquea el merge a `main`, que está protegida.

**Respaldo:** `respaldo_base_datos` diario a las 05:00, `pg_dump` cifrado AES-256-GCM, retención 14 días, destino el repositorio privado `gestor-operaciones` (creado por la propia GitHub App). **Restauración completa probada al menos dos veces antes del 16-sep**, cronometrada, comparando recuentos de tablas de evidencia — no "cargó".

### Reglas de negocio no obvias

1. **Una sola migración, no varias**: crear las 72 tablas de una vez el 16-sep, aunque 12 nazcan vacías, elimina el riesgo de una migración fallida en producción durante la ventana crítica de la parcial (A-175, RG-193).
2. **El servicio web nunca migra**: sólo el trabajador aplica la migración, con `pg_advisory_lock` dedicado antes de tomar cualquier trabajo; si la revisión de esquema falla, el trabajador no arranca y la base queda en la revisión anterior — nunca a medias.
3. **`PERFIL_ALCANCE` es una variable de entorno, no una columna de base de datos** — para que no existan cursos con alcances distintos dentro del mismo despliegue.
4. **Reversión = volver al despliegue anterior de la plataforma** (reutiliza la imagen ya construida, objetivo <3 min), nunca `git revert` + reconstrucción.
5. **Congelación de código el 5-oct a las 20:00**: después de esa hora sólo entra una corrección que cumpla las cuatro condiciones a la vez (bloquea la revisión de un requisito, trae reproducción escrita, pasa todas las puertas, la revisa otra persona).
6. **Trabajo manual previo, fuera del código, con fecha dura**: decisión de nombre/dominio y registro (10-sep 09:00), registro de la GitHub App y congelación de sus permisos tras medición (11-sep 20:00), configuración a mano de la organización de GitHub — `default_repository_permission=none`, `members_can_create_repositories=false`, verificación en dos pasos exigida — **antes del 13-sep**, porque el ítem 14 del checklist de vinculación (Etapa P4) la verifica y no puede salir bloqueante el día de la demo.

### Criterios de aceptación resumidos

- El monorepo tiene la estructura de carpetas fija y una prueba de arquitectura falla si `dominio/` importa infraestructura.
- `alembic upgrade head` sobre una base vacía crea las 72 tablas sin error; una migración posterior al 16-sep con `DROP` o `ALTER … TYPE` rompe la puerta de CI.
- Lanzar 5 trabajos de Canvas del mismo curso a la vez nunca produce más de una petición simultánea contra Canvas; lanzar 5 de GitHub nunca produce más de 4 simultáneas.
- `GET /salud` responde sin tocar la base de datos y sin límite de tasa.
- Existe registro fechado de al menos dos restauraciones completas exitosas antes del 16-sep, con orden, salida y duración.
- Arrancar con `APP_ENCRYPTION_KEY_ACTIVA` ausente del llavero falla el arranque, nombrando la variable.
- `ensayo` con la misma `CANVAS_BASE_URL` que producción no arranca.
- Las 18 puertas de CI (10+8) se ejecutan en cada `push`/PR y bloquean el merge si alguna falla.

### Dónde profundizar

`docs/SPEC/14-infraestructura-y-despliegue.md` completo, en particular §14.6.4 (cifrado y llavero), §14.7.3 (dos espacios de cerrojo, con prueba de arquitectura sobre el orden de toma), §14.8 (migraciones), §14.9.3 (las 8 puertas de contrato) y §14.13.3 (calendario exacto de infraestructura, con cada hito fechado día a día desde el 10-sep). Decisiones `A-005`, `A-011`, `A-012` (anulada, manda `A-174`), `A-175`, `A-176`, `A-191`.

---

# PARCIAL — 16 de septiembre de 2026

El flujo que se demuestra ese día (§3.1 del enunciado): crear un usuario profesor → crear un curso → vincularlo con Canvas y con GitHub → crear una tarea individual → ver los repositorios crearse automáticamente, incluida la asociación de los estudiantes con sus cuentas de GitHub. **Todo lo que ese flujo toca está completo y usable, no esbozado.** Las ocho etapas siguientes cubren exactamente eso y nada más; lo que queda fuera se declara en pantalla (capas de bloqueo/oculto/deshabilitado, §1.11 del SPEC), nunca a medias.

---

## Etapa P1 — Identidad y acceso

**Entrega:** PARCIAL.

**Requisitos que cubre:** R2.1.1 (crear y administrar usuarios profesor — la parte de alta), R2.1.2 (registro con cuenta `gmail.com`).

**Depende de:** Etapa 0.

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `usuario` | `email` (citext, único, `CHECK @gmail.com`), `email_canonico` (citext, único), `google_sub` (único), `nombre`, `avatar_url`, `cuenta_github_id` (nullable, único parcial), `consentimiento_github_en`, `generacion_enlaces`, `activo` | `activo=false` = cuenta cerrada por su propio dueño; nunca se borra la fila |
| `sesion` | `token_hash` (único), `jti_oidc`, `creada_en`, `expira_en`, `revocada_en`, `agente`, `ip_truncada` | Cookie opaca, no JWT — para poder revocar de inmediato |
| `sesion_membresia` | PK `(sesion_id, membresia_id)`, `version`, `refrescada_en` | Da efecto inmediato a cambios de rol/permisos (se llena en Etapa P2) |

**Endpoints:** `POST /auth/google/inicio`, `GET /auth/google/callback`, `GET`/`POST /auth/confirmar` (camino degradado sin cookie), `GET/PATCH /api/perfil`, `DELETE /api/perfil` (cerrar cuenta), `GET/DELETE /api/perfil/sesiones`.

**Llamadas externas:** Google OpenID Connect, Authorization Code + PKCE, `prompt=select_account` siempre. Se leen `sub`, `email`, `email_verified`, `name`, `picture` del `id_token` — nunca se piden alcances más allá de `openid email profile`, nunca se guarda `id_token`/`access_token`/`refresh_token`.

**Pantallas:** `/acceso` (botón único "Entrar con Google"), `/perfil` (nombre editable, correo no editable, sesiones abiertas con botón de cierre, cerrar cuenta con confirmación).

**Jobs:** ninguno propio de esta etapa.

### Reglas de negocio no obvias

1. **Se rechaza toda cuenta con reclamación `hd`**, incluida la institucional de la universidad, aunque termine en `@gmail.com` — es cumplimiento de R2.1.2, no un fallo, y se explica así en pantalla.
2. **`email_canonico` normaliza sin puntos y sin sufijo `+etiqueta`**, sólo para `gmail.com`/`googlemail.com` — es lo que permite que una invitación (Etapa P2) casee aunque la persona entre con una variante de su propio correo.
3. **No hay contraseña propia ni magic link de respaldo** bajo ninguna circunstancia.
4. **Cerrar la propia cuenta se rechaza si esa persona es la única profesora activa de algún curso activo** — la pantalla lista esos cursos con enlace a cada uno.
5. **Un usuario recién registrado no es profesor de nada**: sólo lo es al crear un curso (Etapa P2) o al ser invitado.
6. **La sesión es una cookie opaca respaldada en base de datos**, nunca un JWT autocontenido — es lo único que permite que el retiro de un ayudante (Etapa P2) invalide su sesión de inmediato.

### Criterios de aceptación resumidos

- Entrar con `gmail.com` verificada crea usuario y sesión en <30s y deja en `/cursos`.
- Entrar con una cuenta con `hd` (institucional) se rechaza sin crear ninguna fila.
- `ana@googlemail.com` entra y su `usuario.email` queda como `ana@gmail.com`.
- La URL de autorización siempre contiene `prompt=select_account`.
- Reutilizar un `state` ya consumido no crea sesión.
- En ventana privada de Chrome/Edge/Firefox el acceso se completa (con la pantalla de confirmación si la cookie no vuelve).
- Ninguna respuesta de la API expone `id_token`, `access_token` ni `refresh_token` de Google.
- Cerrar la cuenta no borra la fila de `usuario`; su autoría sigue visible marcada "cuenta cerrada".

### Dónde profundizar

`docs/SPEC/02-roles-y-permisos.md` §2.1–§2.2, §2.10. Casos de correo y de `state`/PKCE: §2.2.4–§2.2.8, con la tabla completa de los 8 motivos de rechazo. Decisiones `A-017`, `A-018`, `A-165`.

---

## Etapa P2 — Curso, equipo docente y permisos

**Entrega:** PARCIAL.

**Requisitos que cubre:** R2.1.1 (administración de usuarios, plano equipo del curso), R2.1.3 (crear y administrar cursos — la parte de creación; la vinculación es P3/P4), R2.1.7, R2.1.8, R2.1.9 completos.

**Depende de:** Etapa P1.

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `curso` | `estado ∈ {BORRADOR, VINCULANDO, ACTIVO, CANVAS_DESVINCULADO, GITHUB_DESVINCULADO, ARCHIVADO}`, `nombre, codigo (≤12), periodo (6 car.), slug (único global, ≤24), zona_horaria`, `umbral_dias_sin_actividad` (default 7), `umbral_desbalance_pct` (default 70) | Existe antes de ambos vínculos y sobrevive a que uno se rompa |
| `membresia_curso` | único `(curso_id, usuario_id)`, `rol ∈ {PROFESOR, AYUDANTE}`, `permisos text[]` (4 `CHECK`), `estado ∈ {ACTIVA, RETIRADA}`, `version`, `es_via_compartida` | Nunca se borra; reincorporar reactiva la misma fila |
| `invitacion_equipo` | `email`, `email_canonico` (único parcial mientras `PENDIENTE`), `rol`, `permisos`, `token_hash`, `estado ∈ {PENDIENTE, ACEPTADA, REVOCADA, EXPIRADA}`, caducidad 7 días | Enlace nominal de un solo uso |

**Endpoints:** `GET/POST /api/cursos`, `GET /api/cursos/{id}/equipo`, `POST /api/cursos/{id}/equipo/invitaciones`, `DELETE .../invitaciones/{id}`, `POST .../invitaciones/{id}/reenviar`, `PATCH /api/cursos/{id}/miembros/{mid}/permisos`, `PATCH .../rol`, `GET .../impacto-retiro`, `POST /api/cursos/{id}/equipo/{mid}/retiro`, `POST .../reincorporacion`, `GET /api/cursos/{id}/equipo/historial`, `GET /api/cursos/{id}/contexto` (rol y permisos efectivos), `GET /api/invitaciones/{token}`, `POST /api/invitaciones/{token}/aceptar` (públicas, sin sesión).

**Llamadas externas:** ninguna en esta etapa (la revocación de acceso en GitHub del retiro se dispara aquí como trabajo encolado, pero su mecánica HTTP es de la Etapa P4).

**Pantallas:** `/cursos` (lista, crear), `/cursos/{id}/equipo` (miembros, invitar con formulario de 7 casillas — 5 editables, 2 deshabilitadas con motivo, 2 implícitas fijas —, retirar, reincorporar, historial), `/invitaciones/{token}` (pública, muestra rol y permisos que se conceden).

**Jobs:** `revocar_acceso_docente` (al retirar una membresía, encolado — su llamada real a GitHub se especifica en P4).

### Reglas de negocio no obvias

1. **Nueve permisos exactos**: dos implícitos e irrevocables (`curso.ver`, `correccion.corregir`), cinco concedibles, dos NO CONCEDIBLES (`curso.administrar`, `equipo.administrar`). **"Los siete permisos concedibles" es una expresión prohibida** en código, interfaz y textos — son "los cinco concedibles" o "los siete configurables".
2. **Todo curso `ACTIVO` conserva siempre al menos un profesor `ACTIVA`**: retirar o degradar al último se rechaza con "promueve antes a otro profesor" (invariante bloqueante, no auto-reparable).
3. **La propiedad acota el trabajo, no la lectura**: cualquier miembro activo con `curso.ver` lee la matriz nominal completa de corrección (Etapa F11); sólo abrir en modo edición está acotado por asignación — esto se construye recién en F11 pero el modelo de permisos que lo sostiene se fija aquí.
4. **Un cambio de rol o de permisos surte efecto en la petición siguiente**, no en el próximo login: `sesion_membresia.version` se contrasta contra `membresia_curso.version` en el mismo `SELECT` que ya resuelve la autorización.
5. **Retirar revoca acceso en GitHub en tres planos** (equipo `docentes`, colaborador, membresía de organización) — el detalle HTTP se implementa en P4, pero el disparador y la garantía "nadie retirado sigue leyendo código" se exigen desde esta etapa.
6. **Las asignaciones de corrección del retirado pasan a `SIN_CORRECTOR`** con incidencia visible; su autoría de lo ya corregido y publicado se conserva íntegra (esto aplica recién en la final, pero la regla de retiro debe respetarla desde ya).

### Criterios de aceptación resumidos

- `PATCH` que intenta conceder `curso.administrar`/`equipo.administrar` a un ayudante responde `422`.
- Retirar al último profesor activo se rechaza con el mensaje literal.
- Dos sesiones del mismo usuario en dos cursos distintos: retirar la membresía de uno deja la otra funcionando.
- El formulario de invitación muestra 7 casillas configurables con las 2 NO CONCEDIBLES deshabilitadas y su motivo escrito.
- `/invitaciones/{token}` se pinta sin sesión y muestra rol + permisos + el texto de consentimiento.
- Un segundo profesor incorporado por invitación recibe los nueve permisos sin distinción respecto del primero.

### Dónde profundizar

`docs/SPEC/02-roles-y-permisos.md` §2.3–§2.9, §2.12 (matriz completa rol×pantalla), §2.13 (acceso del evaluador y cuentas compartidas — relevante para preparar la demo). Decisiones `A-020`, `A-021`, `A-023`, `A-024`, `A-025`, `A-165`, `A-178`–`A-190`.

---

## Etapa P3 — Vinculación con Canvas

**Entrega:** PARCIAL.

**Requisitos que cubre:** R2.1.4 completo.

**Depende de:** Etapa P2 (curso existente con profesor).

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `credencial_canvas` | único `(curso_id, usuario_id)`, único parcial `curso_id WHERE orden_respaldo=0`, `token_cifrado, nonce, huella, canvas_user_id, estado ∈ {VALIDA, INVALIDA, RETIRADA}, orden_respaldo, version_clave, consentimiento_en, fallos_403_consecutivos` | AES-256-GCM, `curso_id` como AAD |
| `identidad_canvas_usuario` | único `(usuario_id, canvas_base_url)`, único `(canvas_base_url, canvas_user_id)` | Identidad de la persona, no del curso |
| `curso` (columnas de esta etapa) | `canvas_base_url` (normalizada), `canvas_course_id` (único junto con la anterior) | — |

**Endpoints propios:** el pegado de credencial y la lista de cursos de Canvas viven dentro del asistente de vinculación (`/cursos/{id}/vinculacion`, paso 2); no hay rutas REST adicionales fuera de las que persiste el asistente.

**Llamadas externas (Canvas):** `GET /api/v1/users/self`, `GET /api/v1/courses` (para listar, con `enrollment_type=teacher&enrollment_state=active`), `GET /api/v1/courses/:id`, `GET /api/v1/courses/:id/enrollments?user_id=self&type[]=TeacherEnrollment` — las cinco comprobaciones del pegado de token (§9.5.2/§5.2.3, ver reglas abajo).

**Pantallas:** paso 2 del asistente de vinculación (`/cursos/{id}/vinculacion`): pegar token con doble casilla de consentimiento, elegir curso de una lista de tarjetas (nunca un ID escrito a mano), estados vacíos con causa distinguida.

**Jobs:** `sonda_credencial_canvas` (cada 15 min: token válido, curso accesible, matrícula de profesor conservada — 3 llamadas).

### Reglas de negocio no obvias

1. **Sólo el titular pega su propio token, nunca el de otra persona** — es cumplimiento de la política de la API de Canvas, no una preferencia: la interfaz sólo ofrece "añadir **mi** credencial".
2. **Las cinco comprobaciones se ejecutan siempre en orden, las cinco**: token válido → matrícula de profesor activa en **ese** curso → identidad no vinculada a otro usuario de la app → coincide con la identidad ya registrada si existe → se registra si no existe.
3. **Si el titular tiene `limit_privileges_to_course_section=true` en todas sus matrículas de profesor de ese curso, la vinculación no se completa** — Canvas puede devolver un curso recortado sin avisar y la app interpretaría a media clase como retirada.
4. **Un curso de Canvas ya vinculado a otro curso de la aplicación aparece en la lista, deshabilitado**, con el nombre del curso ocupante — nunca se oculta.
5. **Tres `403` no transitorios consecutivos** (nunca uno solo, y un `2xx` intermedio resetea el contador) invalidan la credencial y pasan el curso a `CANVAS_DESVINCULADO`; se promueve automáticamente la primera credencial de respaldo válida si existe.

### Criterios de aceptación resumidos

- Pegar el token de alguien sin matrícula de profesor en ese curso se rechaza con el mensaje exacto, sin crear ninguna fila.
- Elegir un curso ya vinculado a otro curso de la app se rechaza nombrando el curso ocupante, nunca `500`.
- Un titular limitado a sección no puede completar la vinculación; el mensaje ofrece las dos salidas.
- Repetir el pegado del mismo token dos veces no crea una segunda fila de `credencial_canvas`.
- Tres `403` no transitorios seguidos invalidan la credencial y desvinculan el curso; un `2xx` intermedio reinicia el contador.

### Dónde profundizar

`docs/SPEC/04-vinculacion.md` §4.5 (flujo de pantalla) y `docs/SPEC/05-integracion-canvas.md` §5.2 (ciclo de vida completo de la credencial, cifrado, degradación) — §5.2.3 es la versión canónica de las cinco comprobaciones. Decisiones `A-031`–`A-037`.

---

## Etapa P4 — Vinculación con GitHub y checklist de verificación

**Entrega:** PARCIAL.

**Requisitos que cubre:** R2.1.5, R2.1.6 completos.

**Depende de:** Etapa P3 (puede completarse en cualquier orden respecto de P3, pero ambas deben estar antes de que el curso pase a `ACTIVO`).

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `instalacion_github` | PK `installation_id`, único `curso_id` (nullable — instalación huérfana), `org_login, org_id, repository_selection, permisos_pendientes, suspendida` | — |
| `equipo_github_curso` | único `curso_id`, `team_id, team_slug, estado, via_efectiva ∈ {TEAM, COLABORADOR}` | Equipo `docentes` |
| `verificacion_vinculacion` | `item` (nullable), `origen ∈ {CHECKLIST, RUNTIME}`, `capacidad` (nullable), `resultado ∈ {CORRECTO, ADVERTENCIA, BLOQUEANTE, NO_VERIFICADO, VERIFICADO_A_MANO}`, `detalle jsonb` | 21 códigos: 19 numerados + `5-bis`/`17-bis` |
| `intento_instalacion_github` | `curso_id, usuario_id, jti, emitido_en, consumido_en` | Guarda de adopción de instalaciones huérfanas |
| `verificacion_canal` | único `(curso_id, canal)` | Bloque "Canales de comunicación", distinto del checklist |
| `acceso_docente_repositorio` | `repositorio_id, membresia_id, estado, via` | Se llena recién en Etapa P8, pero la tabla nace aquí |

**Endpoints:** `POST /api/cursos/{id}/verificacion` (encola checklist, `202`+`ejecucion_id`), `GET .../verificacion/{ejecucion_id}`, `GET .../verificacion/ultima`, `POST .../verificacion/items/{item}` (reejecutar uno).

**Llamadas externas (GitHub):** instalación de la GitHub App vía `https://github.com/apps/<nombre>/installations/new?state=<jwt>`; `GET /app/installations/{id}`, `GET /orgs/{org}`, `POST /app/installations/{id}/access_tokens`, `POST /orgs/{org}/teams`, `PUT /orgs/{org}/teams/{slug}/memberships/{login}`, `PUT /orgs/{org}/memberships/{login}`. (Canvas): las 19 llamadas de comprobación de permisos del checklist (`permissions[]=…` sobre `/courses/:id`), más `5-bis`/`17-bis` como pruebas de escritura reales (crear+borrar un anuncio, comentar una entrega).

**Pantallas:** paso 3 (instalar GitHub App, sin copiar ningún identificador — el `state` firmado resuelve el curso), paso 4 (checklist de 19 ítems + 2 pruebas de escritura opcionales, sondeado cada 2s, nunca SSE/WebSocket), `/cursos/{id}/ajustes` (re-vinculación, sustituir credencial de Canvas, reinstalar GitHub, reejecutar checklist).

**Jobs:** `ejecutar_checklist_vinculacion` (bajo demanda), `verificar_instalacion_github` (cada hora), `sincronizar_acceso_docente` (al cambio + barrido 1h), `revocar_acceso_docente` (ejecución real de lo disparado en P2).

### Reglas de negocio no obvias

1. **Los 19 ítems corren en dos carriles**: Canvas en serie bajo el cerrojo 1 (orden fijo: bloqueantes primero), GitHub en paralelo bajo el cerrojo 2 (ítems 14 y 18) — nunca los dos cerrojos a la vez.
2. **Tope 10s por ítem, 180s global**; lo que no termine queda `NO_VERIFICADO`, nunca en verde.
3. **El ítem 14 (App instalada) tiene 6 sub-comprobaciones**, 4 de ellas bloqueantes; cuando un campo no es legible con el token de instalación, sólo se cierra con `VERIFICADO_A_MANO`, firmado por un profesor en pantalla con fecha y actor persistidos.
4. **El ítem 18 no llama a GitHub**: lee `membresia_curso.org_github_estado` y es severidad advertencia, no bloqueante.
5. **`curso.estado` pasa a `ACTIVO` sólo con cero ítems `BLOQUEANTE` en rojo** — advertencia, `NO_VERIFICADO` o `VERIFICADO_A_MANO` no impiden la transición.
6. **El equipo `docentes` se crea antes que el primer repositorio de estudiante**, en el mismo paso 3, con lectura (`pull`, nunca `write`/`admin`) sobre cada repositorio vía una sola llamada por repositorio al equipo — no una por persona.
7. **Presupuesto declarado: ≤15 invitaciones a la organización por curso**, muy por debajo del límite de 50/24h — consumido sólo por el equipo docente, nunca por estudiantes (que entran como colaboradores de repositorio, no de organización).
8. **Sin el consentimiento fechado de lectura de todo el código, no se incorpora a nadie a la organización ni al equipo `docentes`** — es una guarda, no un aviso.

### Criterios de aceptación resumidos

- Con token y permisos correctos, los 19 ítems terminan en <180s sin ninguno `NO_VERIFICADO` por tiempo agotado.
- Con el ítem 1 bloqueante, los ítems de Canvas dependientes quedan `NO_VERIFICADO` con motivo explícito; el carril de GitHub (14, 18) se ejecuta igual.
- `default_repository_permission` distinto de `none` y legible: ítem 14 bloqueante, el curso no pasa a `ACTIVO`.
- Instalar en cuenta personal (no organización) se rechaza nombrando la restricción de R2.1.5.
- Reinstalar sobre la misma organización sustituye el `installation_id` sin crear ni tocar ningún repositorio.
- Un curso recién vinculado con 8 personas de equipo docente emite exactamente 8 invitaciones a la organización.
- Retirar a alguien de la vía principal (equipo) revoca su lectura sobre todos los repositorios con **una sola** llamada.

### Dónde profundizar

`docs/SPEC/04-vinculacion.md` §4.6–§4.11 (flujo completo, casos borde de instalación huérfana, re-vinculación). `docs/SPEC/06-integracion-github.md` §6.2–§6.4 (naturaleza de la App, permisos), §6.10 (equipo docente, presupuesto de invitaciones, mecánica de revocación en tres planos). Decisiones `A-040`–`A-042`, `A-057`–`A-063`, `A-163`, `A-186`–`A-188`, `A-192`–`A-194`.

---

## Etapa P5 — Espejo de Canvas: estudiantes, secciones y grupos

**Entrega:** PARCIAL.

**Requisitos que cubre:** R2.2.1, R2.2.2 completos; R2.2.3 — modelo y sincronización completos y **visibles en Personas, sin uso todavía en tareas** (el uso en tareas grupales es la Etapa F1).

**Depende de:** Etapa P4 (curso `ACTIVO` o al menos con Canvas vinculado).

### Qué construir

**Tablas** (censo §3, todas de origen "Espejo Canvas"):

| Tabla | Columnas clave | Unicidad |
|---|---|---|
| `seccion` | `canvas_section_id, nombre, sis_section_id, nonxlist_course_id, estado ∈ {ACTIVA, ELIMINADA}` | `(curso_id, canvas_section_id)` |
| `estudiante` | `canvas_user_id, nombre, nombre_ordenable, login_id, sis_user_id, email, uuid, past_uuid, estado` (derivado de matrículas) | `(curso_id, canvas_user_id)` |
| `matricula` | `canvas_enrollment_id, seccion_id, tipo, estado, limitada_a_seccion, activa` — **una fila por matrícula, no por persona** | `(curso_id, canvas_enrollment_id)` |
| `conjunto_grupos` | `canvas_group_category_id, nombre, no_colaborativo, self_signup, group_limit` | `(curso_id, canvas_group_category_id)` |
| `grupo` | `canvas_group_id, nombre, slug, estado, lider_estudiante_id, is_full` | `(curso_id, canvas_group_id)` |
| `pertenencia_grupo` | `workflow_state ∈ {accepted, invited, requested}, activa, activa_desde, activa_hasta, ciclos_ausente` | `(grupo_id, estudiante_id)` |

**Endpoints:** `GET /api/cursos/{id}/personas` (estudiantes, secciones, grupos, con sello de antigüedad), `POST /api/cursos/{id}/sincronizaciones` ("sincronizar ahora", encola, nunca llama en línea).

**Llamadas externas (Canvas):** `GET /courses/:id/enrollments?type[]=StudentEnrollment`, `GET /courses/:id/sections`, `GET /courses/:id/group_categories`, `GET /group_categories/:id/groups`, `GET /groups/:id/memberships` — todas paginadas por header `Link`, nunca por cálculo de páginas.

**Pantallas:** `/cursos/{id}/personas` (tabla de estudiantes con sección/grupo/estado; bloque de secciones; bloque de conjuntos de grupos y grupos; botón "sincronizar ahora").

**Jobs:** `sync_roster` (10 min), `sync_grupos` (10 min) — orden fijo dentro de un ciclo: roster antes que grupos, porque un grupo referencia estudiantes que deben existir primero.

### Reglas de negocio no obvias

1. **`sync_roster` es la única fuente de qué personas existen en el curso** — `sync_grupos` nunca crea estudiantes bajo ninguna circunstancia.
2. **Cuarentena, nunca fila fantasma**: un `canvas_user_id` visto en grupos que no existe en `estudiante` no se inserta; se registra como huérfano, abre una única incidencia `ROSTER_TRUNCADO` por curso, y dispara un `sync_roster` inmediato (una sola vez por ciclo, con clave de idempotencia).
3. **Un roster que cae a 0 o a menos del 60% del recuento anterior no aplica ninguna baja**: se marca `PARCIAL`, se abre `ROSTER_SOSPECHOSO`, se conserva el estado previo — es la defensa contra un fallo transitorio de Canvas que borraría medio curso.
4. **`canvas_user_id` es la clave de identidad efectiva**, nunca `login_id`/`sis_user_id`/`email` (que llegan sólo si la instancia los entrega y sólo sirven para reconciliación ante fusión de usuarios).
5. **Se sigue siempre el header `Link`, nunca se calculan páginas ni se asume `per_page=100`** — se mide `len(json)` de la primera respuesta y se persiste.
6. **Tope de seguridad 50 páginas por llamada**: al alcanzarlo, el ciclo se cierra como `TRUNCADA` (no falla), abre incidencia, y continúa en el ciclo siguiente desde donde quedó.

### Criterios de aceptación resumidos

- Un estudiante con dos matrículas activas aparece una sola vez en la tabla de Personas y dos veces en `matricula`.
- Un `canvas_user_id` en un grupo que no existe en el roster no crea fila de `estudiante`; abre `ROSTER_TRUNCADO` y dispara una única resincronización inmediata.
- Forzar 51 páginas cierra el ciclo `TRUNCADA` con incidencia, sin perder la página ya procesada.
- Un roster que cae de 200 a 40 estudiantes no da de baja a nadie.
- "Sincronizar ahora" responde antes de 200ms sin ninguna llamada HTTP a Canvas dentro de la petición.

### Dónde profundizar

`docs/SPEC/07-estudiantes-y-grupos.md` §7.2 (modelo de datos, identidad, cuarentena) y §7.3 (sincronización de secciones/grupos/pertenencias: cadencias, reconciliación asimétrica — altas automáticas, bajas nunca automáticas —, detección de traslado, guarda anti-cambio-masivo). `docs/SPEC/05-integracion-canvas.md` §5.4 (paginación, cadencias, huella de cambios — mecanismo compartido). Decisiones `A-043`–`A-053`, `A-093`, `A-094`.

---

## Etapa P6 — Mapeo estudiante ↔ GitHub y pantalla Pendientes

**Entrega:** PARCIAL — completo para tareas **individuales**.

**Requisitos que cubre:** R2.2.4, R2.2.5, R2.2.6 completos (modalidad individual).

**Depende de:** Etapa P5.

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Unicidad |
|---|---|---|
| `cuenta_github` | `github_user_id` (bigint, único **global**), `login` (con mayúsculas canónicas de la API), `tipo ∈ {USER, ORGANIZATION, BOT}`, `estado ∈ {VALIDA, RENOMBRADA, NO_EXISTE, ES_ORGANIZACION}` | Catálogo global — una fila por persona real de GitHub en todo el sistema |
| `mapeo_github` | `estudiante_id, cuenta_github_id (nullable), origen, confianza, evidencia jsonb, estado (default 'SIN_DATO'), motivo_invalidacion, vigente_desde/hasta, creado_por` | Único parcial `(curso_id, estudiante_id) WHERE estado<>'SUPERSEDIDO'`; único parcial `(curso_id, estudiante_id) WHERE estado='VIGENTE'`; único parcial `(curso_id, cuenta_github_id) WHERE estado='VIGENTE'` |

**Endpoints:** `GET /api/cursos/{id}/personas` (columna de cuenta GitHub vinculada, correo/`sis_user_id` enmascarados salvo `mapeo.editar`), `POST /api/cursos/{id}/personas/{estudiante_id}/mapeo` (edición manual, `mapeo.editar`), `POST .../mapeo/importar-csv`, `GET /api/cursos/{id}/pendientes`, `POST .../pendientes/{estudiante_id}/recordatorio` (tope 1/estudiante/día, `comunicacion.enviar`).

**Llamadas externas:** Canvas — creación de la tarea de registro "Registro de tu cuenta de GitHub" (`POST /courses/:id/assignments`), lectura de sus entregas (`GET /courses/:id/students/submissions`), comentario de respuesta sobre la entrega (`PUT .../submissions/:user_id` con sólo `comment[text_comment]`). GitHub — validación en vivo del `login` declarado (`GET /users/{login}` contrastado con `GET /orgs/{login}`, sin confiar en el campo `type`).

**Pantallas:** `/cursos/{id}/personas` (crear/publicar la tarea de registro con `curso.administrar`, ver mapeo vigente, corregirlo con `mapeo.editar`, importar CSV), `/cursos/{id}/pendientes` (todo lo que falta en un solo sitio, con acción y botón de recordatorio manual).

**Jobs:** `recolector_mapeos` (3 min con la tarea de registro abierta; 15 min si no; volcado completo cada hora), `revalidar_mapeos` (diario 04:00, revalida cuentas contra GitHub, nunca contra Canvas).

### Reglas de negocio no obvias

1. **Cuatro vías, y sólo cuatro, en orden de preferencia**: Vía 1, tarea de registro de Canvas "Registro de tu cuenta de GitHub" (principal — el estudiante entrega un texto, la app extrae y valida el candidato contra GitHub y responde con un comentario automático en la misma entrega, sin OAuth de GitHub del estudiante); Vía 2, edición manual de un docente con `mapeo.editar` (validación en vivo contra GitHub); Vía 3, importación CSV con previsualización fila a fila antes de aplicar; Vía 4, reintento asistido — un botón que reenvía por Canvas el aviso de qué falta, **no es una fuente de datos nueva**: cada respuesta que produce se procesa como una entrega de la Vía 1. Por eso `mapeo_github.origen` tiene **tres** valores, no cuatro: `AUTOSERVICIO_CANVAS` (vías 1 y 4), `CARGA_DOCENTE` (vía 2), `IMPORTACION_CSV` (vía 3). **No hay una quinta vía** y ninguna depende de que el estudiante entre a la aplicación; no se usa OAuth de GitHub del estudiante (decisión deliberada, no limitación técnica — la doble unicidad del mapeo y que solo el dueño de la cuenta puede aceptar la invitación de colaborador mitigan el riesgo).
2. **El mapeo es *append-only***: corregirlo nunca actualiza la fila — cierra la vigente (`SUPERSEDIDO`) y crea una nueva. Nunca hay un `DELETE`.
3. **Se persiste siempre el `github_user_id` numérico y el `login` canónico devuelto por la API, nunca lo tecleado** — un login renombrado queda libre para que otra persona lo reclame, y comparar por login sería un error de identidad.
4. **Una cuenta de GitHub nunca puede ser a la vez del equipo docente y de un estudiante**: la comprobación de elegibilidad es simétrica, vive en una única función de dominio, y se repite inmediatamente antes de cada incorporación — una colisión sobrevenida abre incidencia y la decide una persona.
5. **Cada estudiante nace con una fila de `mapeo_github` en `SIN_DATO`** en la misma transacción en que se espeja (no se crea recién cuando llega el primer candidato) — así "quién falta" es una consulta directa, no un cálculo por ausencia.
6. **Se crea al espejar, se cierra al invalidar; nunca se propaga entre cursos**: un curso nuevo empieza con cero mapeos, incluso si el mismo estudiante ya declaró su cuenta en otro curso del mismo profesor.
7. **`mapeo_github.estado` es un enum cerrado de nueve valores** (`SIN_DATO`, `RECIBIDO`, `NO_RESUELTO`, `NO_EXISTE`, `ES_ORGANIZACION`, `EN_CONFLICTO`, `VIGENTE`, `INVALIDADO`, `SUPERSEDIDO` — este último el único terminal), con **cinco** motivos de invalidación (`RENOMBRADO` se autoresuelve sin incidencia; `CUENTA_ELIMINADA`, `LOGIN_REASIGNADO`, `ESTUDIANTE_RETIRADO` y `CUENTA_NO_ELEGIBLE` abren incidencia y exigen decisión docente).
8. **Elegibilidad de cuenta se comprueba en toda la aplicación, no por curso**: se rechaza una cuenta con mapeo `VIGENTE` en cualquier curso, y también la de cualquier miembro activo del equipo docente (de cualquier curso) — un ayudante no puede declarar la cuenta de un estudiante de otro curso para leer sus repositorios.

### Criterios de aceptación resumidos

- Declarar un `login` que resuelve a una organización se rechaza con `422`.
- Declarar el login de un estudiante con mapeo vigente en **otro** curso se rechaza y queda en bitácora.
- Tras espejar un estudiante nuevo existe exactamente una fila de `mapeo_github` en `SIN_DATO`, en la misma transacción.
- Corregir un mapeo existente nunca hace `UPDATE` sobre la fila vieja: crea una fila nueva y supersede la anterior.
- La pantalla Pendientes nombra a cada estudiante sin cuenta declarada y dice exactamente qué falta.
- El correo y el `sis_user_id` aparecen enmascarados para quien no tiene `mapeo.editar`; revelarlos queda en bitácora.

### Dónde profundizar

`docs/SPEC/07-estudiantes-y-grupos.md` §7.4 (las cuatro vías completas, extracción y validación del candidato), §7.5 (elegibilidad de cuenta en toda la aplicación, las dos puertas), §7.6 (máquina de estados de nueve valores y los cinco motivos de invalidación), §7.7 (completado progresivo, cuándo usar cada vía) y §7.8 (pantalla Pendientes, los cuatro bloques). Endpoints de Canvas: `docs/SPEC/05-integracion-canvas.md` §5.3 (endpoints 16, 20, 21, 25) y §5.4.3 (cadencia de `recolector_mapeos`).

---

## Etapa P7 — Tarea individual, entrega única, repositorio base

**Entrega:** PARCIAL — completo para modalidad **individual** y **una sola entrega**.

**Requisitos que cubre:** R2.3.1–R2.3.6 completos (individual, una entrega).

**Depende de:** Etapas P4, P5, P6.

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `tarea` | `modalidad ∈ {INDIVIDUAL, GRUPAL}` (derivada de Canvas, se congela tras el primer aprovisionamiento), `estado ∈ {BORRADOR, ACTIVA, INCONSISTENTE, CERRADA, ARCHIVADA}`, `repositorio_base_id` (nullable), `gitignore_template` | En la parcial sólo se ejercita `modalidad=INDIVIDUAL` |
| `entrega` | único `(curso_id, canvas_assignment_id)`, `tipo ∈ {PARCIAL, FINAL}`, `orden` (desde 1, contiguo) | En la parcial, una sola entrega por tarea, siempre `FINAL` con `orden=1` |
| `visibilidad_entrega` | deriva de `only_visible_to_overrides`/`assignment_visibility`/`AssignmentOverride` | — |
| `repositorio_base` | `estado ∈ {CREANDO, CREADO_VACIO, LISTO, ERROR, INACCESIBLE}` (default `CREANDO`), `rama_por_defecto` | Nunca se asume `main` — se lee de la respuesta `201` |
| `archivo_repositorio_base` | — | Árbol de archivos iniciales |

**Endpoints:** `POST/GET /api/cursos/{id}/tareas`, `POST .../tareas/{id}/entregas` (vincular assignment de Canvas), `POST .../tareas/{id}/repositorio-base` (escritura síncrona), `PUT/DELETE .../repositorio-base/archivos/{ruta}` (escrituras síncronas), `POST .../tareas/{id}/activar`.

**Llamadas externas (GitHub):** `POST /orgs/{org}/repos` + `PATCH is_template=true` (crear repositorio base), `PUT/DELETE .../contents/{ruta}` (archivos), `GET /repos/{o}/{r}` (lectura previa). (Canvas): lectura de `assignment` para `visibilidad_entrega`.

**Pantallas:** `/cursos/{id}/tareas` (lista, crear con previsualización del nombre de repo), `/cursos/{id}/tareas/{id}` pestaña "Repositorio base" (árbol de archivos: subir, reemplazar, renombrar, borrar, previsualizar), botón "Activar tarea" (deshabilitado con motivo si el base declarado no está `LISTO`).

**Jobs:** ninguno de captura todavía (eso es P8); el recálculo de sujetos que dispara P8 se prepara aquí.

### Reglas de negocio no obvias

1. **El repositorio base es opcional y siempre lo crea la aplicación** — no se acepta vincular uno creado a mano, porque la garantía de inclusión automática en el alcance de la instalación (P4) sólo cubre lo que la propia App crea.
2. **Cambios al repositorio base después de crear tarea no se propagan retroactivamente** a los repositorios de sujetos ya creados — la copia ocurre una sola vez, en el aprovisionamiento (P8).
3. **La modalidad se deriva de Canvas y se congela tras el primer aprovisionamiento** — cambiarla después en Canvas produce `tarea.estado = INCONSISTENTE`, nunca una migración silenciosa de repositorios.
4. **Crear/subir/reemplazar/borrar un archivo del repositorio base son escrituras síncronas** (con contrato: lectura previa, intención persistida antes de llamar, tope duro de 20s, resultado en pantalla, bitácora) — nunca se encolan, porque el profesor está esperando el resultado.
5. **`entrega` está atada siempre a un `canvas_assignment_id`**, unicidad `(curso_id, canvas_assignment_id)` — no existen entregas sin tarea de Canvas asociada.

### Criterios de aceptación resumidos

- Activar una tarea sin repositorio base no exige ninguna comprobación adicional.
- Un repositorio base en `ERROR` detiene sólo los sujetos nuevos de esa tarea, sin afectar los ya creados ni mover la tarea a `INCONSISTENTE`.
- Vincular una segunda entrega a una tarea que ya tiene una en modalidad incompatible se rechaza.
- Editar el repositorio base después de crear repositorios de sujetos no los afecta.
- Repetir el pegado o la creación del base dos veces no crea dos repositorios base.

### Dónde profundizar

`docs/SPEC/08-aprovisionamiento.md` §8.2 (modelo tarea/entrega/sujeto) y §8.3 (repositorio base) — la más relevante para esta etapa. `docs/SPEC/06-integracion-github.md` §6.5.2 (catálogo de endpoints de repositorios). Decisiones `A-066`–`A-069`, `A-080`, `A-081`.

---

## Etapa P8 — Aprovisionamiento automático, estado, aviso al estudiante y lectura de fechas

**Entrega:** PARCIAL.

**Requisitos que cubre:** R2.3.7–R2.3.12 completos; R2.4.1–R2.4.4 en modo **lectura y visualización** (fecha base y por sección, `fecha_efectiva` ya materializada — las excepciones por sujeto y la resincronización activa por huella son la Etapa F3); R2.5.5 (sólo el estado de creación/configuración de repositorios); R2.6.5 completo en lo que exige R2.3.12 (el mensaje al invitar al repositorio).

**Depende de:** Etapa P7.

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `sujeto` | único `(tarea_id, tipo, coalesce(estudiante_id, grupo_id))`, `tipo ∈ {ESTUDIANTE, GRUPO}`, estado activo/inactivo con motivo | Cuelga de `tarea`, nunca de `entrega`; nunca se borra |
| `repositorio` | cuelga de `sujeto`; `estado` (enum de 15 valores); `motivo` (4 valores para `INACCESIBLE`); `commit_inicial_sha`; `reemplaza_a_id`; `github_repo_id`; `nombre/full_name` (único `(curso_id, nombre)`) | El nombre no cambia nunca tras la creación |
| `acceso_repositorio` | `estado` (10 valores, ninguno terminal) | Acceso de cada estudiante a su repositorio |
| `acceso_docente_repositorio` | (definida en P4, se llena aquí) | Lectura del equipo docente sobre cada repo |
| `regla_fecha`, `fecha_efectiva` | copia cruda de overrides de Canvas; fila materializada por `(entrega, sujeto)` con `origen ∈ {BASE, SECCION, GRUPO, ADHOC}` | Sólo lectura en esta etapa — el algoritmo completo con excepciones es F3 |
| `mensaje_saliente` (uso parcial) | sólo los eventos `repositorio_disponible` e `invitacion_aceptada` operativos | El resto del catálogo de 7 eventos nace deshabilitado (Etapa F10) |

**Endpoints:** `GET /api/cursos/{id}/tareas/{id}` (dashboard con ≥7 contadores separados), `GET .../repositorios` (tabla paginada con motivo por fila), `POST .../reintentar` (genérico sobre `ERROR_PERMANENTE`), `POST .../sustituir-repositorio` (confirmación escrita), `GET .../entregas` (fecha base y por sección, sólo lectura), `GET /api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}` (existe la tabla, la pantalla de timeline es F7).

**Llamadas externas (GitHub):** `/generate` (repo desde plantilla) o `POST /orgs/{org}/repos` + Git Data API en 4 llamadas (blob→tree→commit sin `author`/`committer`→ref) si no hay base; `PUT .../topics` (3 topics de identidad); `PUT .../collaborators/{login}` con `push` (nunca `admin`); `GET .../collaborators/{login}` (lectura previa); `GET .../invitations`. (Canvas): mensaje al estudiante por el canal vigente (§4.9 de P4: conversación o comentario en entrega).

**Pantallas:** dashboard de tarea (contadores: operativos, degradados, con problemas por subtipo, inaccesibles, fuera de alcance, esperando), progreso "creando 12 de 60 · quedan ~9 min", ficha del sujeto con su repositorio y su historial si hubo sustitución.

**Jobs:** `aprovisionar_repositorios` (evento + barrido cada 2 min, cerrojo 2, ritmo 1 repo/6s, 8 reintentos en ~2h), `reconciliar_accesos` (15 min), `sincronizar_acceso_docente`, `sync_tareas_y_fechas` (5 min, sólo lectura en esta etapa), `materializar_sujetos` (tras cada sync + barrido 5 min).

### Reglas de negocio no obvias

1. **Creación progresiva, sujeto a sujeto, nunca en lote y nunca por acción de un usuario** — ni un profesor puede "crear todos ahora": el único gesto humano es activar la tarea, una vez.
2. **Nombres nunca se sufijan ante colisión** (`-2`, `-3` prohibido): se resuelve por adopción segura de 5 condiciones o queda `ERROR_PERMANENTE` — el nombre lleva el id de Canvas y el slug del curso, y **nunca cambia** tras la creación, pase lo que pase después en Canvas o GitHub.
3. **Ante `INACCESIBLE` se sustituye, nunca se recrea**: se crea una fila nueva con `reemplaza_a_id`; la anterior se conserva íntegra.
4. **`DEGRADADO` no es error**: es el estado normal de un repositorio recién creado mientras faltan invitaciones por aceptar, y nunca se cuenta junto con "con problemas".
5. **El disparador del aviso al estudiante (R2.3.12) es por persona, no por repositorio ni por `OPERATIVO`** — un integrante que llega semanas después también recibe el suyo.
6. **El aprovisionamiento usa el cerrojo de GitHub (espacio 2), nunca el de Canvas (espacio 1)** — una sincronización lenta de Canvas nunca puede bloquear 600 creaciones de repositorio.
7. **Ningún estudiante entra a la organización de GitHub**: entra como colaborador de repositorio con `push`, nunca `admin`.

### Criterios de aceptación resumidos

- Al menos 7 contadores separados en el dashboard de tarea, y `DEGRADADO` nunca suma a "con problemas".
- La creación de repositorios ocurre sola, sin que ningún usuario pulse un control, y el registro muestra las transiciones con hora sin actor humano.
- Un estudiante sin cuenta de GitHub declarada aparece nombrado en Pendientes (P6) y el sujeto queda `ESPERANDO_INFORMACION` con motivo escrito.
- Abrir un repositorio en GitHub muestra el nombre inequívoco, la invitación recibida y el mensaje que llegó por Canvas.
- Sustituir un repositorio exige `tarea.administrar` y confirmación escrita, y conserva la fila anterior íntegra.

### Dónde profundizar

`docs/SPEC/08-aprovisionamiento.md` §8.4 (algoritmo exacto de nombres, 11 pasos), §8.5–§8.6 (predicado de aprovisionamiento y máquina de 15 estados — la sección más densa del capítulo), §8.8 (colaboradores), §8.11 (recuperación por subtipo de error). `docs/SPEC/09-entregas-fechas-y-versiones.md` §9.3 (algoritmo de fecha efectiva, en modo lectura aquí). Decisiones `A-092`–`A-111`, `A-127`, `A-130`, `A-164`.

---

# FINAL — 6 de octubre de 2026

Las doce etapas siguientes corresponden, una a una, a las doce banderas cerradas de `PERFIL_ALCANCE` (§1.11 y §13.3.3 del SPEC), agrupadas en los tres bloques cronológicos que fija `docs/ARQUITECTURA.md` §17 (A-160): **Bloque 1** (retirada de bandera 23-sep 20:00), **Bloque 2** (30-sep 20:00), **Bloque 3** (3-oct y 5-oct 12:00). Cada etapa nombra su bandera; la ruta o el bloque de pantalla que habilita esa bandera no se registra en el backend hasta que la etapa está completa y su criterio de aceptación está en verde — nunca se retira una bandera con el criterio en rojo.

---

## Etapa F1 — Modalidad grupal

**Entrega:** FINAL — Bloque 1, bandera `tarea_modalidad_grupal`, retirada 23-sep 20:00.

**Requisitos que cubre:** R2.2.3 (uso completo en tareas — el modelo ya estaba en P5), R2.3.3 (modalidad grupal).

**Depende de:** Etapas P5 (grupos ya espejados), P7, P8 (aprovisionamiento individual funcionando).

### Qué construir

No hay tablas nuevas: `tarea.modalidad`, `sujeto.tipo=GRUPO`, `pertenencia_grupo` y `conjunto_grupos` ya existen desde P5/P7. Esta etapa activa la rama `GRUPAL` del aprovisionamiento de P8 y del cálculo de fecha efectiva de P8/F3.

**Endpoints:** habilitar en el formulario de creación de tarea (P7) el selector de assignment **grupal** de Canvas y el `conjunto_grupos` correspondiente.

**Llamadas externas:** ninguna nueva — reutiliza `/generate`/Git Data API de P8, con `n` integrantes en vez de 1.

**Pantallas:** el selector de modalidad en "Nueva tarea" deja de estar deshabilitado; la ficha de sujeto grupal lista sus integrantes `accepted`.

**Jobs:** ninguno nuevo — `aprovisionar_repositorios` y `materializar_sujetos` ya cubren la rama grupal en su diseño (P8), simplemente no se ejercitaba.

### Reglas de negocio no obvias

1. **Basta un integrante con mapeo `VIGENTE` para crear el repositorio grupal** — no se espera a que todos declaren su cuenta.
2. **Cuenta como integrante quien está `accepted`** en la pertenencia de grupo, nunca `invited` ni `requested`.
3. **Si un grupo se queda sin ningún integrante `accepted`**, se desactiva con `motivo_desactivacion=GRUPO_SIN_ACEPTADOS` y su repositorio pasa a `FUERA_DE_ALCANCE` conservándolo todo.
4. **Un estudiante en dos grupos del mismo conjunto colaborativo** es un dato sucio de Canvas: se detecta, abre incidencia `ESTUDIANTE_EN_DOS_GRUPOS`, y no se aprovisiona hasta que se resuelve en Canvas.
5. **La revocación de acceso por salida de grupo nunca es automática**: siempre decisión humana explícita, confirmada en 2 ciclos antes de proponerse, y el plazo de gracia cuenta desde la decisión, no desde la detección.

### Criterios de aceptación resumidos

- Un grupo con 1 de 4 integrantes mapeados ya tiene repositorio creado.
- Un repositorio de grupo llega a `OPERATIVO` con acceso de todos los integrantes `accepted` con mapeo vigente.
- Un estudiante en dos grupos del mismo conjunto produce incidencia y no bloquea el aprovisionamiento de los demás sujetos.
- Salida de un integrante de un grupo no revoca su acceso en caliente ni automáticamente.

### Dónde profundizar

`docs/SPEC/08-aprovisionamiento.md` §8.5 (predicado con grupos), §8.8.2–§8.8.3 (máquina de acceso de 10 estados y política de revocación). Decisiones `A-047`–`A-049`, `A-093`, `A-212`.

---

## Etapa F2 — Múltiples entregas por tarea

**Entrega:** FINAL — Bloque 1, bandera `tarea_multientrega`, retirada 23-sep 20:00.

**Requisitos que cubre:** R2.3.1, R2.3.2, R2.3.4 (múltiples entregas parciales + una final, mismo conjunto de repositorios).

**Depende de:** Etapa P7.

### Qué construir

Reutiliza la tabla `entrega` de P7 (ya soporta `tipo`, `orden`). Esta etapa habilita:

**Endpoints:** `POST /api/cursos/{id}/tareas/{id}/entregas` deja de estar limitado a una sola fila — "Vincular otra entrega" pasa a estar operativo; `DELETE .../entregas/{id}` (desvincular, sólo si no hay versión capturada) o "excluir" (si ya la hay).

**Pantallas:** pestaña "Entregas" de la tarea, con selector de cuál es `FINAL` (la anterior propuesta por defecto queda como `PARCIAL`).

**Jobs:** ninguno nuevo directamente — activa el uso pleno de `sync_tareas_y_fechas` sobre múltiples assignments de la misma tarea.

### Reglas de negocio no obvias

1. **`orden` es contiguo desde 1**; desvincular una entrega sin versión capturada **renumera** transaccionalmente; con versión capturada, sólo se puede excluir, nunca desvincular.
2. **Una tarea `ACTIVA` tiene exactamente una entrega `FINAL`, siempre la de mayor `orden`** — nunca cero, nunca dos.
3. **Todas las entregas de una tarea comparten el mismo conjunto de repositorios** (R2.3.4) — vincular una segunda entrega nunca crea repositorios nuevos, sólo agrega una fecha de cierre y una versión más sobre los mismos.
4. **Cambiar la modalidad de una tarea con entregas ya vinculadas está prohibido**: la modalidad se lee de Canvas al vincular la primera entrega y se congela.

### Criterios de aceptación resumidos

- Vincular una segunda entrega renumera `orden` correctamente y la primera propuesta de "final" cambia a "parcial".
- Desvincular una entrega con versión capturada se rechaza; excluirla no borra la versión ya registrada.
- No existe ningún estado intermedio con 0 o con 2 entregas `FINAL` en una tarea `ACTIVA`.
- La misma consulta de `repositorio` para dos entregas del mismo sujeto/tarea devuelve la misma fila.

### Dónde profundizar

`docs/SPEC/08-aprovisionamiento.md` §8.2.1 (modelo tarea/entrega/sujeto). `docs/SPEC/09-entregas-fechas-y-versiones.md` §9.7 (independencia entre entregas, cómo el nombre del tag hace visible la separación). Decisión `A-080`, `A-081`, `A-084`.

---

## Etapa F3 — Fechas efectivas completas: excepciones y resincronización

**Entrega:** FINAL — Bloque 1, bandera `fechas_excepciones`, retirada 23-sep 20:00.

**Requisitos que cubre:** R2.4.1–R2.4.4 completos (la lectura básica ya estaba en P8).

**Depende de:** Etapas P8, F1 (fechas para sujetos grupales), F2 (fechas por entrega).

### Qué construir

Ninguna tabla nueva — completa el algoritmo sobre `regla_fecha`/`fecha_efectiva` ya creadas en P8.

**Endpoints:** `GET /api/cursos/{id}/entregas/{id}/historial-fechas` (encadenamiento de fechas superseded por sujeto), panel de excepciones por estudiante y por grupo en la pestaña "Entregas".

**Llamadas externas (Canvas):** `GET /assignments?include[]=all_dates&include[]=overrides&include[]=assignment_visibility` (aceleración) + `GET /assignments/:aid/overrides` (autoridad, la única que trae `student_ids`) — las dos, siempre, con jerarquía explícita: manda la autoridad.

**Pantallas:** panel de excepciones (estudiante/grupo) en la pestaña Entregas; insignia "fecha ambigua" con las candidatas desplegables.

**Jobs:** `sync_tareas_y_fechas` opera ahora a plena capacidad (5 min normal, 1 min en las 2h previas a un cierre), disparada por huella SHA-256 de las reglas de fecha, no por `updated_at`.

### Reglas de negocio no obvias

1. **Precedencia estricta de 4 niveles**: extensión individual (`ADHOC`) > grupo > sección > base. **Un `ADHOC` más restrictivo gana igual, aunque sea anterior a la fecha de sección** — la cadena es estricta entre niveles.
2. **Empate dentro del mismo nivel: gana la fecha más tardía**, marca `ambigua=true` y abre incidencia — capturar antes de tiempo destruye trabajo legítimo; capturar después sólo incluye trabajo adicional que el docente puede ver.
3. **Sujeto grupal: se calcula la cadena para cada integrante `accepted` y se toma el máximo** de las fechas resultantes, con el mismo criterio del punto anterior.
4. **El disparador de resincronización es una huella SHA-256 de las reglas normalizadas, nunca `assignment.updated_at`** — Canvas no documenta si un override cuenta como "modificar la tarea", y confiar en eso dejaría extensiones invisibles.
5. **`lock_at` y `unlock_at` nunca mandan sobre `due_at`** — son sólo informativos; `all_day` nunca deriva un fin de día, siempre usa `due_at` como instante absoluto.
6. **Orden fijo e innegociable en cada ciclo**: `sync_roster → sync_grupos → sync_tareas_y_fechas → materializar_sujetos`; si roster o grupos fallan, se pospone el cálculo de fechas de ese ciclo entero.

### Criterios de aceptación resumidos

- Un estudiante con `ADHOC` en una sección con override propio recibe la fecha del `ADHOC`, aunque sea anterior.
- Dos secciones con override sobre el mismo sujeto matriculado en ambas producen `ambigua=true` y la fecha más tardía.
- Un grupo con integrantes en secciones distintas y sin `ADHOC` propio recibe el máximo de las fechas de sus integrantes `accepted`.
- Editar sólo el `title` de un override no produce ninguna fila nueva de `fecha_efectiva`.
- Crear un override en Canvas produce una fila `fecha_efectiva` nueva dentro de 6 minutos (2 min en la ventana crítica, 60s con "sincronizar ahora").

### Dónde profundizar

`docs/SPEC/09-entregas-fechas-y-versiones.md` §9.3 (algoritmo completo de precedencia) y §9.4 (huella y resincronización) — la parte más densa del capítulo. Decisiones `A-054`–`A-056`, `A-082`.

---

## Etapa F4 — Captura y versiones de entrega

**Entrega:** FINAL — Bloque 1, bandera `versiones_entrega`, retirada 23-sep 20:00.

**Requisitos que cubre:** R2.4.5–R2.4.8 completos.

**Depende de:** Etapa F3 (fechas efectivas vencidas y materializadas).

### Qué construir

**Tabla:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `version_entrega` | `commit_sha, commit_tree_sha, commit_fecha_autor/committer, commit_mensaje, rama, fecha_corte_utc, intento, tag_nombre, tag_estado ∈ {PENDIENTE, CREADO, CONFLICTO, FALLIDO, NO_APLICA}, tag_motivo (7 valores), tag_error, tag_creado, estado (6 valores terminales, sin default), motivo, vigente, reemplaza_a_id, advertencias text[], verificacion jsonb, integrantes jsonb, origen_captura, creada_por_usuario_id, motivo_manual, capturada_en, repositorio_id (nullable)` | Único `(entrega_id, sujeto_id, intento)` + único parcial `(entrega_id, sujeto_id) WHERE vigente`. **No existe ninguna fila antes de que el SHA quede resuelto** |

**Endpoints:** `GET /api/cursos/{id}/entregas/{id}/progreso-captura`, `GET .../sujetos/{id}/version`, `POST .../version/capturar-ahora` (`tarea.administrar`), `POST .../version/recapturar` (rol `PROFESOR`), `POST .../version/fijar-sha` (rol `PROFESOR`), `POST .../registrar-versiones` (confirmar captura masiva de una entrega vinculada tras el cierre), `GET /api/cursos/{id}/versiones/{id}/abrir?destino=arbol|comparacion|zip` (redirección auditada, deja bitácora).

**Llamadas externas (GitHub):** `GET /repos/{o}/{r}/commits?until=<corte+1s>` (selección local del commit, nunca "el primero" de la lista), `POST /git/refs` (crear el tag `entrega/<orden>-<slug>/v<n>`), `GET /git/ref/tags/{nombre}` (verificación diaria), `GET /commits/{sha}` (alcanzabilidad).

**Pantallas:** columna "estado de captura" en la pestaña Entregas con enlace por SHA; ficha del sujeto con historial de versiones (vigente + superseded); comparación `…/compare/{sha_anterior}...{sha_actual}`.

**Jobs:** `resolver_sha` (cada minuto, gracia 60s, clave `version:<entrega>:<sujeto>:<corte_epoch>`), `crear_etiqueta` (fase 2, clave `tag:<entrega>:<sujeto>:<intento>`), `precierre_actividad` (repartido en los 15 min previos a cada cierre, pone al día el espejo de actividad antes del corte).

### Reglas de negocio no obvias

1. **Dos fases con dos claves de idempotencia**: resolver el SHA (evidencia) y crear la etiqueta (comodidad de navegación) — un `403` al crear la etiqueta nunca impide registrar la evidencia, que es lo único que R2.4.5 exige.
2. **Nunca se sobreescribe un tag que apunta a otro SHA**: si se movió, queda `tag_estado=CONFLICTO` con los dos SHA registrados y una incidencia — el `commit_sha` en base sigue siendo la verdad.
3. **Selección del commit de cierre por doble fuente** (espejo propio + contraste con GitHub pidiendo `until=corte+1s` y filtrando localmente el mayor `≤corte`) — nunca se confía en que `until` sea inclusivo en el segundo exacto, porque no está documentado.
4. **Una fila `version_entrega` es inmutable salvo una lista cerrada de columnas mutables** (`vigente`, `motivo`, `tag_*`, `advertencias`, y `estado` sólo en las dos transiciones permitidas) — una función única de transición rechaza cualquier otra escritura.
5. **Recapturar ante cambio de fecha nunca pide confirmación humana**: si la fecha se adelanta o se retrasa, se captura de nuevo automáticamente y **ambas versiones quedan visibles**, nunca se descarta la anterior.
6. **Commits posteriores al cierre se muestran, nunca se registran de nuevo**: un indicador derivado sin coste de API, nunca una segunda fila.
7. **Repositorio sin sujeto al cierre nunca se llama "sin entrega"**: es `SIN_REPOSITORIO` con motivo `SUJETO_MATERIALIZADO_TRAS_EL_CIERRE`, y cuando el repositorio aparece después **no se captura sola** — exige el botón "captura ahora" para no producir un falso `SIN_COMMITS`.
8. **Las tres acciones manuales** (capturar ahora, recapturar con otra fecha, fijar un SHA) crean siempre una fila nueva con `intento+1`, nunca modifican la anterior; las dos últimas exigen rol `PROFESOR`, no sólo el permiso `tarea.administrar`.

### Criterios de aceptación resumidos

- Ninguna fila de `version_entrega` existe para un `(entrega, sujeto)` cuya `fecha_efectiva` vigente no esté vencida.
- Un cierre masivo de 200 sujetos a la misma hora produce SHA resuelto en <5 min (percentil 95).
- Forzar discrepancia espejo/GitHub produce `estado=REVISAR` con ambos SHA guardados.
- Un intento de `UPDATE` sobre `commit_sha` o `fecha_corte_utc` de cualquier fila falla siempre.
- Adelantar la fecha de una entrega ya capturada produce una fila nueva vigente y dos filas visibles en la ficha.
- Borrar manualmente un tag lo recrea en el ciclo de verificación siguiente; moverlo a otro SHA nunca lo sobreescribe.
- "Fijar esta versión en un commit concreto" con un SHA de otro repositorio se rechaza antes de escribir nada.

### Dónde profundizar

`docs/SPEC/09-entregas-fechas-y-versiones.md` §9.6 (máquina de estados, doble fase, selección del commit — la sección más densa del capítulo), §9.8 (inmutabilidad, recaptura, manipulación tras el cierre), §9.9 (acceso directo). Decisiones `A-101`–`A-104`, `A-172`, `A-204`, `A-213`.

---

## Etapa F5 — Ingesta de actividad de GitHub

**Entrega:** FINAL — Bloque 2, bandera `ingesta_actividad`, retirada 30-sep 20:00.

**Requisitos que cubre:** sostiene R2.5.2, R2.5.3, R2.5.4, R2.5.7, R2.5.8, R2.5.10 (ninguno de ellos es alcanzable sin esta etapa, pero ella sola no cumple ninguno directamente — los cumplen F6 y F7).

**Depende de:** Etapa P8 (repositorios existentes), F4 (commit de cierre como referencia).

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `evento_webhook` | único `delivery_id`, `evento, accion, firma_valida, payload jsonb (trunc. 64KB), estado (8 valores)` | Cabecera+cuerpo de cada webhook recibido |
| `evento_push` | `repositorio_id, ref, before_sha, after_sha, n_commits_payload, forzado, divergido` | Metadatos de cada push |
| `commit` | único `(repositorio_id, sha)`, `parent_shas, n_padres, es_merge, en_rama_por_defecto, autor_github_user_id, fecha_autor/committer, adiciones/eliminaciones (nullable), huerfano, huerfano_desde, motivo_exclusion, origen_ingesta` | Espejo local de cada commit |
| `autoria_commit` | PK `(commit_id, coalesce(estudiante_id, identidad_git_id))`, `papel ∈ {AUTOR, COAUTOR}, regla_atribucion, confianza` | Permite multi-autor; co-autoría pesa 1 completo por persona |
| `identidad_git` | índice único parcial `(repositorio_id, email_normalizado) WHERE estado<>'SUPERSEDIDA'`, `estado ∈ {SIN_RESOLVER, RESUELTA, NO_ES_ESTUDIANTE, SUPERSEDIDA}` | Autores no resueltos por email; *append-only* |

**Endpoints:** `POST /webhooks/github` (sin sesión, firma HMAC, `202` en <200ms), `GET .../identidades` (identidades de git sin resolver), `POST .../identidades/{id}/resolver`, `GET .../identidades/{id}/propagacion`, `POST .../identidades/{id}/revelar` (audita en bitácora).

**Llamadas externas (GitHub):** webhooks suscritos: `push, create, delete, repository, member, installation, installation_repositories`. Reconciliación: `GET /repos/{o}/{r}/commits` con `If-None-Match`, `GET .../compare/{before}...{after}` (relleno), GraphQL por lotes de 100 (co-autores, líneas, vía web — cubo `GRAFO`).

**Jobs:** `procesar_webhooks` (continuo, cerrojo por `repositorio_id`), `reconciliar_actividad` (15 min, cerrojo 2), `barrido_completo_actividad` (diario 03:30, backfill histórico).

### Reglas de negocio no obvias

1. **El webhook es la fuente rápida, nunca la única**: la reconciliación por ETag cada 15 minutos es la red de seguridad, porque `since` filtra por fecha de commit, no de push — un commit con fecha antigua empujado hoy es invisible sin ella.
2. **`push --force` marca huérfanos, nunca borra**: los commits que desaparecen de la historia se conservan con `huerfano=true`, porque forman parte del registro de actividad real.
3. **Nunca se compara por `login` de GitHub, siempre por `github_user_id` numérico** — hay prueba de CI que falla si alguna consulta une por login.
4. **Cascada de atribución estrictamente ordenada y excluyente**: `AUTOR_GITHUB` (alta) → `EMAIL_NOREPLY` (alta) → `EMAIL_DIRECTO` (media) → `IDENTIDAD_DOCENTE` (alta) → `SIN_ATRIBUIR`. La corrección manual de un docente **nunca pisa** `AUTOR_GITHUB` ni `EMAIL_NOREPLY`.
5. **Los commits de bots y de docentes son contables igual** (sólo 3 motivos de exclusión: merge, commit inicial, huérfano) — las banderas de bot/docente son sólo informativas.
6. **El receptor valida, persiste y responde `202` en <200ms; todo el procesamiento ocurre después**, en el trabajador — un receptor que procesa en línea es uno que GitHub puede considerar lento y dejar de reintentar.
7. **Repositorio base y repositorio de operaciones están totalmente excluidos** de toda ingesta y métrica — no tienen sujeto.

### Criterios de aceptación resumidos

- Un payload sin `X-Hub-Signature-256` válida se rechaza con `401` y no produce ningún efecto de dominio.
- Reenviar la misma entrega (mismo `X-GitHub-Delivery`) no duplica ninguna fila.
- Un `push` con más de 250 commits sin paginar se completa vía `compare` paginado sin perder ninguno.
- Un `push --force` que reescribe historia no elimina ninguna fila de `commit`; las marca huérfanas.
- Un repositorio sin ningún webhook entregado en 15 minutos sigue al día gracias a la reconciliación por ETag.
- Correo genérico (`root@localhost`) nunca se propaga automáticamente entre repositorios: las casillas de propagación nacen desmarcadas.

### Dónde profundizar

`docs/SPEC/10-seguimiento.md` §10.2 (ingesta completa: relleno, historia reescrita, resolución de destino de un evento en 5 pasos) y §10.3 (atribución: la cascada de 5 reglas y la corrección docente append-only) — las dos secciones más densas del capítulo. `docs/SPEC/06-integracion-github.md` §6.8 (webhooks: verificación, idempotencia, límites documentados). Decisiones `A-070`–`A-072`, `A-196`, `A-221`.

---

## Etapa F6 — Tablero de tarea y comparación de participación

**Entrega:** FINAL — Bloque 2, bandera `tablero_actividad`, retirada 30-sep 20:00.

**Requisitos que cubre:** R2.5.1–R2.5.4, R2.5.6–R2.5.9 completos; amplía R2.5.5 (visual completa, el estado base ya estaba en P8).

**Depende de:** Etapa F5.

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `metrica_repositorio_dia` | PK `(repositorio_id, dia)`, `commits, commits_excluidos, commits_de_bot, commits_docentes, dias_activos_acumulados` | Agregado diario, **recomputado**, no incremental |
| `participacion_entrega` | PK `(entrega_id, repositorio_id, estudiante_id)`, `commits, adiciones, eliminaciones, dias_activos, commits_coautorados, commits_sin_atribuir_repo` | Agregado por sujeto y entrega |
| `resumen_tarea` | PK `tarea_id`, `calculado_en, contadores jsonb` | Evita `GROUP BY` en cada carga del tablero |
| `curso` (columnas usadas) | `umbral_dias_sin_actividad` (default 7, editable), `umbral_desbalance_pct` (default 70, editable) | Ya nacieron en P2 |

**Endpoints:** `GET /cursos/{id}/tareas/{id}` (tablero, pestaña por defecto — 5 bloques), botón "Actualizar ahora" (encola, cooldown 2min/usuario·tarea y 5min/tarea, nunca llama a GitHub en línea), exportación CSV.

**Llamadas externas:** ninguna directamente — el tablero se pinta exclusivamente del espejo (Ley 1), verificado por cabecera `X-Llamadas-Externas: 0`.

**Pantallas:** tablero de tarea (5 bloques: línea de entregas, barra de estado de repos, tarjetas de atención, actividad en el tiempo con series y sparklines, tabla detalle + comparación); comparación entre integrantes (tareas grupales: commits/días/líneas + índice de desequilibrio); "posición frente al curso" (tareas individuales: cuartiles con mediana de sección/curso); vista `/cursos/{id}/seguimiento` (una fila por tarea activa del curso).

**Jobs:** `agregar_metricas` (10 min sobre últimos 2 días + pase nocturno completo: reatribución → recompute → evaluación de alertas).

### Reglas de negocio no obvias

1. **Actividad del repositorio ≠ actividad de los estudiantes**: las alertas de R2.5.3/R2.5.4 se evalúan sólo sobre `hay_actividad_estudiantil` — un push de bot o de docente nunca cierra una alerta de inactividad.
2. **Umbral dinámico**: baja de 7 a 2 días automáticamente cuando hay una entrega venciendo en <72h para ese repositorio específico, sin tocar el umbral global del curso.
3. **Causas de "sin participación" en cascada estrictamente ordenada**: `SIN_ACCESO` → `SIN_ATRIBUIR` → `SIN_COMMITS` — mientras un repo tenga commits sin atribuir, ningún estudiante de ese repo se marca con la causa más grave.
4. **Co-autoría pesa 1 completo por persona acreditada** — la suma de commits por integrante puede superar el total del repositorio, y la interfaz lo declara explícitamente.
5. **Ventana de entrega es `(inicio, cierre]`**: abierta por izquierda, cerrada por derecha — un commit exactamente en el instante de cierre pertenece a la entrega que cierra.
6. **El tablero pinta en <400ms p95 con 200 sujetos y cero llamadas externas** (Ley 1) — es un requisito medido, no una aspiración.
7. **Estudiante retirado**: sale de alertas y denominadores, pero sus commits permanecen atribuidos y visibles con la etiqueta "retirado el dd-MM".

### Criterios de aceptación resumidos

- El tablero carga por debajo de 400ms p95 con 200 sujetos, medido con el conjunto sintético de carga.
- Un repositorio de 3 días de vida no aparece "sin actividad" (dato insuficiente, no falso negativo ni falso positivo).
- Doble ejecución de `agregar_metricas` no cambia ninguna fila (idempotente).
- Un repo con 8 vs 2 commits entre dos integrantes produce un índice de desequilibrio del 80%.
- INDIVIDUAL muestra medianas de sección/curso, nunca la palabra "ranking".
- Silenciar una alerta la oculta del tablero y del informe (Etapa F9) pero la conserva en Pendientes.

### Dónde profundizar

`docs/SPEC/10-seguimiento.md` §10.4 (motor de métricas), §10.5 (predicados de actividad — núcleo de la Ley del "nunca acusar sin evidencia"), §10.6 (estado agregado de la entrega, 9 valores), §10.7 (tablero) y §10.8 (comparación). Decisiones `A-118`–`A-124`, `A-171`, `A-205`, `A-220`, `A-222`, `A-223`.

---

## Etapa F7 — Timeline por repositorio

**Entrega:** FINAL — Bloque 2, bandera `repositorio_timeline`, retirada 30-sep 20:00.

**Requisitos que cubre:** R2.5.10 completo.

**Depende de:** Etapas F5, F6, F4 (marcas de versión).

### Qué construir

Ninguna tabla nueva — lee `commit`, `autoria_commit`, `version_entrega`, `pertenencia_grupo`.

**Endpoints:** `GET /cursos/{id}/tareas/{id}/repos/{id}` (ruta que ya existía sin registrar desde P4/P8).

**Pantallas:** timeline con 4 capas — commits por día con atribución y etiqueta de exclusión; ciclo de vida del repositorio; marcas de entrega (vigente + anteriores); cambios de composición del grupo. Franja de participación por tramo; colapso de ≥3 días sin actividad; filtros por integrante/periodo/rama; marcar/desmarcar hitos manuales (`tarea.administrar`).

### Reglas de negocio no obvias

1. **El enlace a GitHub se oculta, no se rompe**, cuando `acceso_docente_repositorio` de quien mira no está `CONCEDIDO` — se sustituye por el motivo y la acción.
2. **Un commit destacado sigue reglas cerradas** (cualquiera activa): versión de entrega, merge, primera participación del integrante, vuelta tras racha de inactividad, hito manual del docente.
3. **Colapsar ≥3 días sin actividad no pierde ningún commit al expandir** — es una vista, no una agregación con pérdida.
4. **La franja de participación debe coincidir exactamente con la comparación del bloque 5 del tablero (F6)** — misma función de cálculo, dos presentaciones.
5. **Cero commits en el repositorio siempre muestra la causa escrita** (sin actividad / sin acceso / sin atribuir), nunca un vacío sin explicación.

### Criterios de aceptación resumidos

- Commits huérfanos aparecen etiquetados con el evento "historia reescrita" en el timeline.
- Un repositorio sin acceso docente `CONCEDIDO` muestra el motivo en vez del enlace roto a GitHub.
- Marcar un hito manual exige `tarea.administrar` y queda visible con su fecha.
- El recuento de participación del timeline coincide exactamente con el de la comparación del tablero para el mismo periodo.

### Dónde profundizar

`docs/SPEC/10-seguimiento.md` §10.9 (las 4 capas y las reglas de commit destacado). Decisión `A-124`, `A-163`.

---

## Etapa F8 — Archivado de tareas y repositorios

**Entrega:** FINAL — Bloque 2, bandera `tarea_archivado`, retirada 30-sep 20:00.

**Requisitos que cubre:** amplía R2.3.11 (cierre del ciclo de vida de una tarea).

**Depende de:** Etapa P8.

### Qué construir

Reutiliza `tarea.estado` (ya incluye `CERRADA`, `ARCHIVADA` desde P7) y `repositorio.estado` (incluye `ARCHIVADO` desde P8).

**Endpoints:** `POST /api/cursos/{id}/tareas/{id}/archivar`, `POST .../desarchivar` — ambos exigen `tarea.administrar` **y** rol `PROFESOR`.

**Llamadas externas (GitHub):** `PATCH /repos/{o}/{r}` con `archived: true`/`false` — único sitio de llamada permitido en la lista blanca de campos parcheables.

**Pantallas:** bloque "Cierre de la tarea" en la pestaña Entregas, con las cinco guardas visibles antes de habilitar el botón.

### Reglas de negocio no obvias

1. **Archivar exige cinco guardas simultáneas** (§8/A-197): entre ellas, que no haya una captura de versión pendiente y que la fecha de cierre ya haya pasado — no se archiva una tarea con trabajo en curso.
2. **Un ayudante con `tarea.administrar` pero sin rol `PROFESOR` recibe `403`** con el motivo escrito — es una de las seis acciones cerradas por rol de todo el sistema.
3. **Archivar deja el repositorio en `ARCHIVADO` sin tocar la captura previa** — las versiones ya registradas son inmutables independientemente del estado del repositorio.
4. **La aplicación nunca archiva ni desarchiva por su cuenta** — sólo por acción explícita de un profesor o porque alguien lo archivó directamente en GitHub (detectado por webhook).

### Criterios de aceptación resumidos

- Archivar deja el repositorio en `ARCHIVADO` y la captura previa intacta.
- Un ayudante con `tarea.administrar` recibe `403` al intentar archivar.
- Las cinco guardas se comprueban todas antes de habilitar el botón, no una a una en el servidor tras el clic.

### Dónde profundizar

`docs/SPEC/08-aprovisionamiento.md` (repositorio archivado, cruzado con A-197). `docs/SPEC/09-entregas-fechas-y-versiones.md` §9.8.6 (repositorio archivado con captura pendiente). Decisión `A-168`, `A-197`.

---

## Etapa F9 — Informe docente diario y suscripción

**Entrega:** FINAL — Bloque 3, banderas `informe_diario` y `mis_notificaciones`, retirada 3-oct 12:00.

**Requisitos que cubre:** R2.6.1–R2.6.4 completos.

**Depende de:** Etapas F6 (métricas del tablero), P2 (equipo docente para suscribir).

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `informe_diario` | único `(curso_id, fecha)`, `estado ∈ {GENERADO, SIN_TAREAS_ACTIVAS, NO_GENERADO}`, `motivo` (si `NO_GENERADO`), `origen ∈ {PROGRAMADO, MANUAL}`, `frescura jsonb`, `contenido/contenido_html/contenido_texto` (congelado al generar) | *Append-only* — nunca se reescribe tras generar |
| `suscripcion_informe` | PK `(curso_id, usuario_id)`, `activa, origen_baja, dada_de_baja_en` | Por curso, no global — no es un permiso |

**Endpoints:** `GET/POST /baja/{token}` (público, firmado — GET nunca muta), `/cursos/{id}/mis-notificaciones` (autogestión, sólo `curso.ver`), `/perfil` (vista agregada de todos los cursos + "suscribirme a todos"/"darme de baja de todos"), `/cursos/{id}/informes/{fecha}` (ver un día), "Vista previa del informe de hoy" (no persiste), "Enviarme el informe de hoy ahora" (tope 2/persona/día).

**Llamadas externas:** ninguna — el informe se genera enteramente del espejo. El envío usa el proveedor de correo transaccional (cuota del despliegue: 100/día, reserva `INFORME`=60).

**Pantallas:** `/cursos/{id}/mis-notificaciones`, `/cursos/{id}/informes` (histórico + preview), `/baja/{token}` (confirmación de baja/re-alta).

**Jobs:** `informe_diario` (07:00 en la zona del curso + barrido cada 30 min entre 07:00-23:00, no-op si ya existe la fila del día).

### Reglas de negocio no obvias

1. **Sin tareas activas no hay informe** (§2.6.1 del enunciado, literal) — `estado=SIN_TAREAS_ACTIVAS`, sin fila de contenido.
2. **El contenido se congela al generar, nunca se actualiza** (Ley 2) — dos ejecuciones del job el mismo día producen una sola fila, no dos versiones.
3. **La suscripción es por curso, gobernada individualmente por cada persona** — nunca hay un botón que suscriba a otro.
4. **La cuota de correo es del despliegue y del día (100), no por curso**: si se agota, el envío queda `DIFERIDO` con reintento al día siguiente — nunca se descarta en silencio.
5. **El enlace de baja es firmado y de un solo generación (`usuario.generacion_enlaces`)** — regenerar enlaces invalida los anteriores.
6. **GET en `/baja/{token}` nunca cambia estado** — es protección contra prefetchers y escáneres de correo; sólo `POST` con token anti-CSRF aplica la baja.

### Criterios de aceptación resumidos

- Con cero tareas activas, no se encola ningún correo ese día.
- Dos ejecuciones del job el mismo día producen una sola fila de informe.
- "Enviarme a mí" como ayudante no envía a nadie más.
- Un enlace de baja con generación vieja se rechaza tras "regenerar enlaces".
- Retiro de un miembro con correo ya encolado termina en estado `SUPRIMIDO`, nunca se envía.
- La cuota agotada difiere el envío sin perder ningún destinatario.

### Dónde profundizar

`docs/SPEC/11-informes-y-comunicacion.md` §11.3 (generación, 5 secciones), §11.4 (suscripción), §11.5 (envío y cuota). Decisiones `A-131`–`A-133`, RG-041, RG-207.

---

## Etapa F10 — Comunicaciones ampliadas: mensajes, anuncios y automatismos

**Entrega:** FINAL — Bloque 3, bandera `comunicaciones_automaticas`, retirada 5-oct 12:00.

**Requisitos que cubre:** R2.6.5 ampliado (envío manual desde cualquier tabla, además de lo que ya exigía R2.3.12 desde P8), R2.6.6, R2.6.7 completos.

**Depende de:** Etapas P8 (outbox con 2 eventos ya operativo), F3 (cambios de fecha), F9 (outbox compartido con el informe).

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `mensaje_saliente` (ampliación de uso, tabla ya creada en P8) | `evento` (7 valores del catálogo, ver abajo), `generacion, reemplaza_a_id`, `estado` (15 valores, máquina 7), `motivo_estado` (20 valores) | Se activan los 5 eventos restantes |
| `plantilla_mensaje` | `clave, canal, asunto, cuerpo, version, activa` | *Append-only*: editar cierra vigente + crea `version+1` |
| `supresion_comunicacion` | único parcial `(curso_id, estudiante_id) WHERE levantada_en IS NULL` | Estudiante que pide no recibir automáticos |
| `cambio_fecha` | `entrega_id, huella_anterior/nueva, ambito, ventana_cierra_en, anunciado_en` | Sostiene el anuncio de cambio de fecha |
| `regla_comunicacion` | clave lógica `(curso, tarea, evento)`, `activa` | Interruptor por tarea; ausencia de fila = valor por defecto |

**Endpoints:** `/cursos/{id}/comunicaciones` (bandeja completa, filtros, reintentar/reenviar/cancelar), pestaña "Comunicaciones" de la tarea (7 interruptores con preview y recuento de destinatarios), composición de mensaje/anuncio manual, toggle `recordatorio_mapeo` en Personas.

**Llamadas externas (Canvas):** `POST /discussion_topics` (anuncios, con o sin `specific_sections`), `DELETE .../discussion_topics/:id`, `POST /conversations` (mensajes directos, `group_conversation=false` siempre, uno por destinatario).

**Jobs:** `despachar_outbox` (cada 30s, las 7 guardas en orden fijo), `comunicaciones_programadas` (5 min, recalcula desde cero al reactivar un interruptor), `purga_retencion` (03:00, `DIFERIDO` >7 días → `CADUCADO`).

### Reglas de negocio no obvias

1. **Catálogo cerrado de 7 eventos, y ninguno más**: `repositorio_disponible`, `invitacion_aceptada` (los 2 ya operativos desde P8), `recordatorio_mapeo` (único de alcance CURSO), `recordatorio_invitacion`, `proximidad_cierre`, `cambio_de_fecha`, `correccion_publicada` (el único desactivado por defecto).
2. **Tope duro: 3 mensajes automáticos por estudiante y día del curso**, con prioridad fija y **fusión antes que diferir** cuando coinciden dos eventos elegibles.
3. **Mensajes siempre individuales, nunca grupales** (`group_conversation=false`) — un destinatario lógico grupo se expande a integrantes `accepted`, cada uno con su propia fila.
4. **Ningún mensaje nombra a otro estudiante**; hay prueba de arquitectura que falla el build si una plantilla referencia a un tercero.
5. **Anuncios automáticos nunca usan `published=false`** para simular borrador; una corrección post-publicación es un anuncio nuevo enlazado, nunca una edición (Ley 2).
6. **Reactivar un interruptor recalcula desde cero, no vacía la cola**: hechos que siguen siendo verdad (invitaciones hechas mientras estaba apagado) se envían retroactivamente.
7. **El aviso de salida de grupo NO pertenece a este catálogo**: es obligatorio, sin interruptor, sin tope — corrección explícita de una propuesta anterior que lo trataba como evento configurable.
8. **La guarda de suspensión de comunicaciones del curso nunca detiene el canal `CORREO`** — sólo frena lo que se escribe en Canvas.

### Criterios de aceptación resumidos

- Invitación tardía a un grupo de 4 genera 4 mensajes individuales, ninguno con `group_conversation=true`.
- Apagar `repositorio_disponible` detiene envíos con advertencia visible; reactivarlo dispara los retroactivos pendientes.
- Ninguna llamada de anuncio automático incluye `published=false`.
- Tres ediciones de fecha en 15 minutos producen 1 solo anuncio con la fecha final, no tres.
- El tope de 3/estudiante/día respeta la prioridad fija (lo que caduca hoy > lo que desbloquea > lo que puede esperar).
- El evento `salida_de_grupo` no existe como fila con interruptor propio en `regla_comunicacion`.

### Dónde profundizar

`docs/SPEC/11-informes-y-comunicacion.md` §11.2 (modelo de datos, máquina de 15 estados, las 7 guardas en orden — núcleo técnico más denso), §11.6 (catálogo de 7 eventos con disparadores exactos), §11.8 (anuncios, `specific_sections` con plan B). Decisiones `A-125`–`A-130`, `A-224`–`A-228`.

---

## Etapa F11 — Corrección: asignación, bandeja, navegación y acceso a la versión

**Entrega:** FINAL — Bloque 3, bandera `correccion` (la ruta se registra al completar F11+F12 juntas), retirada 5-oct 12:00.

**Requisitos que cubre:** R2.7.1–R2.7.5 completos.

**Depende de:** Etapas F4 (versión capturada), P2 (permisos), F6/F7 (contexto de actividad en la pantalla de corrección).

### Qué construir

**Tablas:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `asignacion_correccion` | único `(entrega_id, sujeto_id)`, `membresia_id` (nullable = sin corrector), `criterio ∈ {MANUAL, EQUITATIVO, SECCION, COPIA_ENTREGA_ANTERIOR}`, `desalineada_motivo` | Invariante: `membresia_id IS NULL ⟺ correccion.estado='SIN_CORRECTOR'` |
| `correccion` | único por `(entrega, sujeto)`, `estado` (8 valores, máquina 5), `nota_local, rubrica_local jsonb, comentario`, `publicable bool, motivo_no_publicable` (10 valores), 5 banderas ortogonales (`version_desactualizada, reclamo_abierto, sin_commits, reconocimiento_sin_codigo, …`) | Sin ninguna columna espejo de Canvas |
| `nota_interna_correccion` | `clase ∈ {NOTA, RECLAMO_ABIERTO, RECLAMO_CERRADO}`, `desenlace_reclamo` (obligatorio si cierre) | Canal interno *append-only*; el reclamo del estudiante usa esta tabla, nunca abre incidencia |
| `estado_canvas_submission` | PK `(entrega_id, estudiante_id)` | Espejo de qué tiene Canvas; llenada por reconciliación |

**Endpoints:** `GET /cursos/{id}/correccion` (3 pestañas: Mis asignaciones, Estado de la entrega, Repartir), `GET .../correccion/{entrega_id}/{sujeto_id}` (pantalla propia), `PUT .../borrador`, `POST .../lista`, rutas de reparto (previsualizar→confirmar→aplicar, 4 criterios), "repartir sólo los nuevos", "registrar/cerrar reclamo".

**Llamadas externas (Canvas):** `GET /courses/:id/rubrics/:id` (caché 15 min, se lee en vivo, nunca se persiste el criterio evaluable). (GitHub): ninguna directa — el acceso a la versión reutiliza el endpoint auditado de F4 (`.../versiones/{id}/abrir`).

**Pantallas:** bandeja de corrección (3 pestañas), Estado de la entrega (matriz nominal + 3 agregados + doble contador), pantalla de corrección de dos columnas (código/versión a la izquierda, rúbrica+nota+comentario a la derecha), panel "Evidencia de la entrega" para reclamos.

**Jobs:** ninguno nuevo — reutiliza `materializar_sujetos` (P8) para sujetos tardíos y `reconciliar_notas_canvas` (llenado desde F12, pero la tabla `estado_canvas_submission` nace vacía aquí).

### Reglas de negocio no obvias

1. **La propiedad acota el trabajo, no la lectura**: cualquier miembro activo con `curso.ver` lee la matriz nominal completa; sólo abrir en modo edición exige `correccion.corregir` **y** ser el asignado — sobre fila ajena el botón dice "ver", nunca "corregir".
2. **No existe auto-asignación**: sin `correccion.asignar` nadie puede tomar una fila `SIN_CORRECTOR` para sí mismo.
3. **Reasignar o retirar a un ayudante nunca descarta el borrador** — pertenece al par (entrega, sujeto), no al corrector.
4. **Sujeto tardío nunca se asigna automáticamente**: requiere la acción explícita "repartir sólo los nuevos".
5. **`publicable`/`motivo_no_publicable` es una bandera ortogonal al estado**, no un estado en sí — sólo bloquea la transición a `PUBLICANDO` (Etapa F12).
6. **El grano de la asignación es siempre `(entrega, sujeto)`**: no hay herencia entre entregas de una misma tarea — corregir la parcial no asigna automáticamente la final al mismo corrector.
7. **Reclamo del estudiante usa `nota_interna_correccion.clase`, nunca abre incidencia** — decisión explícita por los catálogos cerrados (51 tipos de incidencia, no ampliables sin enmienda).

### Criterios de aceptación resumidos

- Un ayudante sin `correccion.asignar` ve la matriz completa pero no la pestaña "Repartir".
- Sujeto sin repositorio aparece asignable igual; sujeto tardío queda `SIN_CORRECTOR` con incidencia, sin tocar otras filas.
- Reparto equitativo es determinista y repetible con el mismo conjunto de entrada.
- Concurrencia de dos personas repartiendo a la vez nunca produce doble corrector para el mismo sujeto.
- La rúbrica se lee en vivo desde Canvas con caché de 15 min, nunca se persiste como calificable.
- Enlaces sólo se pintan con `acceso_docente_repositorio=CONCEDIDO`; `PENDIENTE` no pinta enlace roto.

### Dónde profundizar

`docs/SPEC/12-correccion.md` §12.5 (las 4 mecánicas de reparto y su concurrencia — la sección más densa), §12.9 (rúbrica y su reconciliación). Decisiones `A-134`–`A-138`, `A-180`, `A-206`, `A-214`.

---

## Etapa F12 — Publicación de notas y estado de corrección

**Entrega:** FINAL — Bloque 3, bandera `correccion` (compartida con F11), retirada 5-oct 12:00.

**Requisitos que cubre:** R2.7.6, R2.7.7 completos.

**Depende de:** Etapa F11.

### Qué construir

**Tabla nueva:**

| Tabla | Columnas clave | Notas |
|---|---|---|
| `publicacion_nota` | único `(correccion_id, estudiante_id, intento)`, `payload_enviado jsonb, codigo_http, respuesta jsonb (literal de Canvas), score/entered_score/grade_devuelto, grader_id_reportado, publicado_por_usuario_id, credencial_canvas_id` | Evidencia *append-only* de qué se escribió en Canvas |

**Endpoints:** `POST .../publicar` (`409` si `publicable=false` o hay conflicto pendiente), `GET .../correccion/estado` (matriz agregada, <400ms p95/200 sujetos), "Publicar seleccionadas" (masivo, secuencial reanudable), "Publicar sin entrega (N sujetos)" (flujo para `SIN_COMMITS`), botón "comprobar contra Canvas" (encola reconciliación).

**Llamadas externas (Canvas):** `PUT /courses/:id/assignments/:aid/submissions/:user_id` (nota+rúbrica+comentario en una sola petición, o sólo comentario para el canal 2), `GET .../students/submissions` (lectura masiva paginada, una vez por entrega), períodos de calificación (`is_closed`) y política de atraso.

**Jobs:** `reconciliar_notas_canvas` (inmediata al entrar en ventana de corrección, cada 30 min dentro, 1 vez al día fuera, nunca en tarea archivada).

### Reglas de negocio no obvias

1. **Toda escritura usa la credencial operativa del curso** (token del profesor titular); `as_user_id` nunca se envía — verificado por prueba de arquitectura.
2. **`contraste_canvas` es una función pura, nunca persistida** — evita que existan dos verdades del mismo hecho (`CONCORDA`/`DIVERGE`/`SOLO_EN_CANVAS`/`NO_COMPROBADO`).
3. **El grano de la escritura lo decide `entrega.grade_group_students_individually`, leído de Canvas, nunca elegido por la aplicación.**
4. **Pre-chequeo obligatorio antes de publicar**: período cerrado, `gradeable_students`, política de atraso (`late_policy_status=none` salvo acción explícita).
5. **Conflicto de publicación** (Canvas ya tiene `graded_at` posterior o score distinto) **bloquea con diálogo de 3 salidas nombradas**: publicar la mía / adoptar la de Canvas / dejarlo como está — nunca se resuelve solo.
6. **Verificación posterior obligatoria tras publicar**: tolerancia `0,001` en score; decide entre `PUBLICADA` y `PUBLICADA_CON_ADVERTENCIA`.
7. **La nota publicada nunca se modifica de forma automática** cuando la versión se recaptura después — se abre incidencia y se ofrece "reabrir la corrección" como acto explícito.
8. **`FALLIDO` nunca se reintenta solo** — el diseño prefiere perder un envío visible antes que duplicar una nota.

### Criterios de aceptación resumidos

- Borrador (`PUT`) nunca llama a Canvas.
- Publicar con período cerrado produce `NO_PUBLICABLE` sin ninguna llamada.
- Publicación de grupo no individual genera una sola llamada con `group_comment`.
- Discrepancia post-publicación produce `PUBLICADA_CON_ADVERTENCIA`, nunca un error silencioso.
- La matriz de "Estado de la entrega" nunca usa `submission_summary` de Canvas.
- "Comprobar contra Canvas" encola sin bloquear el render de la pantalla.
- Reclamo cerrado sin `desenlace_reclamo` responde `422`.

### Dónde profundizar

`docs/SPEC/12-correccion.md` §12.10 (grano de escritura, pre-chequeo, verificación posterior — la lógica más delicada de todo el capítulo) y §12.14 (contraste y conflictos). Decisiones `A-139`–`A-143`, `A-169`, `A-206`.

---

## Tabla de trazabilidad: requisito → etapa

Los 59 requisitos del enunciado, cada uno con la etapa donde queda completo. Donde un requisito se reparte entre dos entregas, se listan ambas etapas con la parte que cubre cada una.

| Requisito | Etapa(s) | Qué cubre cada una |
|---|---|---|
| R2.1.1 | P1, P2 | P1: alta vía Google OIDC · P2: administración del profesor en el plano del equipo del curso |
| R2.1.2 | P1 | Registro con cuenta `gmail.com` |
| R2.1.3 | P2 | Crear y administrar cursos |
| R2.1.4 | P3 | Vinculación con Canvas |
| R2.1.5 | P4 | Vinculación con GitHub |
| R2.1.6 | P4 | Checklist de 21 códigos y guía de la vinculación |
| R2.1.7 | P2 | Incorporar co-profesores, mismos permisos |
| R2.1.8 | P2 | Incorporar ayudantes, 9 permisos (mínimo 3 que exige el enunciado) |
| R2.1.9 | P2 (disparo) / P4 (ejecución GitHub) | Retiro con revocación en tres planos |
| R2.2.1 | P5 | Estudiantes inscritos |
| R2.2.2 | P5 | Sección de cada estudiante |
| R2.2.3 | P5 (modelo) / F1 (uso en tareas) | Grupos colaborativos y sus integrantes |
| R2.2.4 | P6 | Asociar estudiante ↔ cuenta de GitHub |
| R2.2.5 | P6 | Completar progresivamente las asociaciones |
| R2.2.6 | P6 | Mostrar claramente quién falta |
| R2.3.1 | P7 | Crear tarea vinculada a Canvas |
| R2.3.2 | P7 (una entrega) / F2 (múltiples) | Entregas parciales y final |
| R2.3.3 | P7 (individual) / F1 (grupal) | Modalidad según Canvas |
| R2.3.4 | P7 / F1 / F2 | Un único conjunto de repositorios por tarea |
| R2.3.5 | P7 | Repositorio base opcional |
| R2.3.6 | P7 | Archivos iniciales del base |
| R2.3.7 | P8 | Creación automática usando el base |
| R2.3.8 | P8 | Nombres automáticos e inequívocos |
| R2.3.9 | P8 | Incorporación automática de colaboradores |
| R2.3.10 | P8 | Creación progresiva, sin interacción humana |
| R2.3.11 | P8 (+ F8 archivado) | Estado de creación y configuración visible |
| R2.3.12 | P8 | Aviso al estudiante por Canvas |
| R2.4.1 | P8 (lectura) / F3 (completo) | Fechas de Canvas por entrega |
| R2.4.2 | P8 (lectura) / F3 | Fechas distintas por sección |
| R2.4.3 | P8 (lectura) / F3 | Extensiones por estudiante o grupo |
| R2.4.4 | P8 (lectura) / F3 | Fechas actualizadas ante cambios en Canvas |
| R2.4.5 | F4 | Registrar automáticamente la versión al cierre |
| R2.4.6 | F4 | Versiones independientes por entrega |
| R2.4.7 | F4 | Versión inmutable ante actividad posterior |
| R2.4.8 | F4 | Acceso directo a la versión |
| R2.5.1 | F6 | Dashboard general de la tarea |
| R2.5.2 | F5 (ingesta) / F6 (presentación) | Actividad de los repositorios en el tiempo |
| R2.5.3 | F6 | Repositorios sin actividad reciente |
| R2.5.4 | F6 | Estudiantes sin participación |
| R2.5.5 | P8 (parcial) / F6 (completo) | Estado de creación y configuración |
| R2.5.6 | F6 | Entregas de una tarea, fechas y estado |
| R2.5.7 | F6 | Actividad por periodo de entrega |
| R2.5.8 | F6 | Comparar participación intragrupo |
| R2.5.9 | F6 | Métricas adicionales propias |
| R2.5.10 | F7 | Timeline por repositorio |
| R2.6.1 | F9 | Informe docente diario |
| R2.6.2 | F9 | Situaciones que requieren atención |
| R2.6.3 | F9 | Suscripción individual |
| R2.6.4 | F9 | Envío por correo |
| R2.6.5 | P8 (lo que exige R2.3.12) / F10 (ampliado) | Mensajes directos por Canvas |
| R2.6.6 | F10 | Anuncios de curso |
| R2.6.7 | F10 | Comunicaciones automáticas con interruptor |
| R2.7.1 | F11 | Asignar entregas entre correctores |
| R2.7.2 | F11 | Identificar entregas asignadas |
| R2.7.3 | F11 | Navegación entre entregas asignadas |
| R2.7.4 | F11 | Acceso directo a la versión revisada |
| R2.7.5 | F11 | Acceso a la rúbrica de Canvas |
| R2.7.6 | F12 | Registrar calificación en Canvas |
| R2.7.7 | F12 | Estado de corrección del curso |

**Cobertura: 59 de 59 requisitos del enunciado, cada uno con al menos una etapa asignada.** Ningún requisito queda sin destino.

---

## Resumen de etapas por entrega

| Entrega | Etapas | Total |
|---|---|---|
| Fundamentos (previo a ambas) | Etapa 0 | 1 |
| PARCIAL — 16-sep-2026 | P1 Identidad · P2 Curso y equipo · P3 Vinculación Canvas · P4 Vinculación GitHub · P5 Espejo Canvas · P6 Mapeo GitHub · P7 Tarea y repo base · P8 Aprovisionamiento y estado | 8 |
| FINAL — 6-oct-2026 | F1 Modalidad grupal · F2 Multientrega · F3 Fechas completas · F4 Versiones · F5 Ingesta actividad · F6 Tablero · F7 Timeline · F8 Archivado · F9 Informe diario · F10 Comunicaciones · F11 Corrección (asignación) · F12 Corrección (publicación) | 12 |
| **Total** | | **21** |

## Notas de secuenciación y paralelización

**Dentro de la parcial, P3 y P4 son independientes entre sí** (Canvas y GitHub no dependen el uno del otro) y pueden trabajarse en paralelo por dos personas distintas una vez cerrada P2; el asistente de vinculación del SPEC está diseñado explícitamente para completarse en cualquier orden. **P5 y P6 también admiten paralelismo parcial**: P5 (espejo de estudiantes/secciones/grupos) es prerequisito de datos de P6 (mapeo), pero el modelo de datos y las pantallas de ambas pueden avanzar a la vez si quien construye P6 trabaja primero contra datos de prueba y conecta el espejo real al final. **P7 y P8 son estrictamente secuenciales** — no hay aprovisionamiento sin tarea ni repositorio base configurados.

**Dentro de la final, el Bloque 1 (F1–F4) es el de mayor riesgo técnico y conviene abordarlo primero**, tal como fija `docs/ARQUITECTURA.md` (A-160): concentra la mayor parte de las reglas `[MEDIR]` sobre comportamiento no documentado de la API de Canvas (orden de prioridad de overrides, inclusividad de `until` en GitHub) y los cambios de modelo de datos más profundos (múltiples entregas, modalidad grupal). **F1 y F2 pueden avanzar en paralelo** porque tocan columnas distintas de `tarea`/`entrega`, pero **ambas deben cerrar antes de F3** (fechas efectivas necesita sujetos grupales y entregas múltiples ya resueltas para ejercitar todos sus casos). **F4 depende estrictamente de F3.**

**El Bloque 2 (F5–F8) tiene una dependencia lineal clara**: F5 (ingesta) es prerequisito de F6 (tablero) y de F7 (timeline), porque ninguna de las dos tiene nada que mostrar sin commits espejados. **F8 (archivado) es independiente de F5–F7** y puede adelantarse o postergarse dentro del bloque sin afectar a las demás.

**El Bloque 3 (F9–F12) admite el mayor paralelismo de las tres**: F9 (informe diario) y F10 (comunicaciones) comparten el mismo motor de *outbox* (creado en la Etapa P8) pero son funcionalmente independientes entre sí y pueden repartirse entre dos personas. **F11 y F12 son estrictamente secuenciales** (no se publica una nota sin bandeja de corrección), y ambas comparten la única bandera `correccion`: la ruta `/cursos/{id}/correccion` no se registra en el backend hasta que las dos etapas están completas, así que conviene tratarlas como una sola unidad de entrega aunque este plan las describa por separado para mantener cada una en un tamaño manejable.

**Cuota de revisión cruzada.** `docs/ARQUITECTURA.md` (regla 2 de A-162/A-194) exige que nada entre a `main` sin la revisión de otra persona del equipo, y que esa revisión incluya la pregunta "¿podrías explicar esto el 7 de octubre?" — la actividad de validación individual del enunciado (§3.3) evalúa exactamente eso. Aplicarlo etapa por etapa, y no sólo al final, es lo que hace que esa pregunta tenga siempre una respuesta.

## Qué NO construir en ninguna etapa

Ninguna etapa de este plan produce, porque el capítulo 1 del SPEC (§1.10) los declara explícitamente fuera de alcance y ninguno corresponde a un requisito `R2.x.y`: autograding o ejecución de tests sobre la versión capturada; detección de plagio; comentarios de código línea a línea dentro de la aplicación (el comentario de código vive en GitHub, el de la entrega en Canvas); cualquier interfaz para estudiantes, ni siquiera de sólo lectura; creación o edición de secciones, grupos o inscripciones en Canvas (la aplicación las obtiene, no las crea); edición de rúbricas; entregas sin tarea de Canvas asociada; estudiantes que no provienen de Canvas; GitHub Enterprise Server; notificaciones por Slack, WhatsApp o cualquier canal fuera de Canvas y correo; importar desde GitHub Classroom; publicar nota en entregas moderadas o anónimas; los formatos de nota `gpa_scale` y `not_graded`; protección de tags o *rulesets* de GitHub (no existen en repositorios privados de un plan gratuito); el distintivo "Verified" de la GitHub App; Safari en ventana privada; tema oscuro; y los *differentiation tags* de Canvas como generadores de repositorio. Si alguna de estas apareciera como requisito de una etapa durante la implementación, es una señal de que algo se está malinterpretando — se revisa contra el enunciado antes de escribir código.

## Procedencia de este documento

Se construyó leyendo íntegros los 14 capítulos de `docs/SPEC/` (~275K tokens), `docs/ARQUITECTURA.md` §17 y §20, y `docs/enunciado-proyecto2.md`. El reparto parcial/final de los capítulos 1 a 6, 13 y 14 viene de sus propias secciones normativas (cada uno declara explícitamente qué le corresponde a cada entrega). El capítulo 7 se completó después de una primera pasada de este plan (pasó de 116 a 494 líneas) y no trae tampoco una sección de reparto propia, pero su contenido (§7.4-§7.8) es funcionalmente el mismo para ambas entregas — la mecánica de mapeo no distingue parcial/final, sólo su uso en tareas grupales (Etapa F1) lo hace. El reparto de los capítulos 7, 8, 9, 10, 11 y 12 — que no traen esa sección — se reconstruyó cruzando tres fuentes que sí son explícitas: la tabla de A-157 (`docs/ARQUITECTURA.md` §17), la tabla de registro de rutas por perfil de alcance del capítulo 13 (§13.3.3) y la columna "entra en servicio" del catálogo de 31 trabajos en segundo plano del capítulo 14 (§14.7.4). Donde estas tres fuentes coincidían, el corte quedó fijado sin ambigüedad; no se encontró ningún caso de discrepancia entre ellas durante la elaboración de este plan.
