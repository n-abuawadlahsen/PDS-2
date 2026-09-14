# Carta de arquitectura — documento normativo

**Proyecto 2 · ICC4201 Desarrollo de Software · 202620 · Universidad de los Andes**
Aplicación web de apoyo al equipo docente que integra Canvas LMS y GitHub para la gestión de tareas de programación.

| | |
|---|---|
| Estado | **Definitivo, revisión 2.** Sustituye a los tres borradores de `.workflow/arquitectura/` y a la revisión 1 |
| Fecha | 9 de septiembre de 2026 |
| Decisiones normativas que fija | **235**, numeradas **A-001** a **A-235**. Las **62** decisiones **A-174** a **A-235** son la enmienda única de reconciliación de las 590 respuestas de alcance (§0.6) |
| Entrega parcial | miércoles 16 de septiembre de 2026, 13:30, presencial |
| Entrega final | martes 6 de octubre de 2026, 16:00 |
| Aplicación en pie hasta | **31 de octubre de 2026 inclusive** (cubre con margen las dos semanas que exige §3.2 del enunciado) |

---

## 0. Cómo se lee y cómo se cita este documento

Este documento está escrito en voz de especificación. **Cada afirmación es una decisión tomada, no una opción a evaluar.** Cada decisión lleva un identificador estable `A-nnn` y se cita así: «según A-047, el nombre del repositorio nunca cambia».

### 0.1 Autoridad de las fuentes

1. `docs/enunciado-proyecto2.md` — **autoridad máxima**. Si una decisión de aquí incumpliera un requisito `R2.x.y`, la decisión cede.
2. `.workflow/decisiones-infraestructura.md` — entrada fija del equipo. No se discute.
3. `docs/preguntas-averiguables-resueltas.md` — hechos técnicos verificados contra documentación oficial. Se cita por identificador `Q-…`.
4. `docs/estudio-apis-canvas-github.md` — **no es autoridad y contiene errores confirmados**. Sirve de pista, nunca de prueba. Donde este documento se aparta de él, se dice.

### 0.2 Las tres marcas

- **[DOC]** — hecho respaldado por documentación oficial verificada, con la pregunta `Q-…` que lo sostiene.
- **[MEDIR]** — comportamiento que la documentación **no** fija. La decisión existe igualmente, pero está declarada como dependiente de comprobación empírica y figura en el registro de riesgos (§19). **Ninguna decisión crítica de este documento se apoya en un [MEDIR] sin plan alternativo escrito.**
- **[EQUIPO]** — decisión de producto que no es un hecho de API y que este documento cierra.

### 0.3 Regla de oro para los 28 agentes que van a usar este documento

Este documento es la fuente de verdad para responder las 590 preguntas de alcance. **Si una pregunta toca algo decidido aquí, la respuesta es lo que dice aquí, citando el `A-nnn`.** Si una pregunta toca algo que este documento no cubre, la respuesta debe decirlo explícitamente («no fijado por la carta de arquitectura») y proponer, no inventar como si fuera doctrina existente. Nadie resuelve por su cuenta una contradicción con este documento: la escala.

### 0.4 Criterios de decisión, en orden estricto

1. **Cumplir el enunciado.** Si una opción incumple o deja cojo un `R2.x.y`, se descarta por elegante que sea.
2. Cumpliendo lo anterior, **que la aplicación quede lo más completa y profesional posible**: robusta ante fallos, usable para el equipo docente, bien modelada, trazable, y que se sostenga en una demostración en vivo y en una revisión de código.

No se optimiza para «lo más rápido de programar».

### 0.5 Qué cambió en la revisión 2 y por qué

Una revisión adversarial encontró once decisiones ausentes, veinte contradicciones internas y veintidós ambigüedades explotables. **Esta revisión las cierra todas.** Ninguna decisión de la revisión 1 que fuera correcta se ha retirado; las que estaban mal se han reescrito en su sitio, conservando su número, y lo que faltaba se ha añadido como decisiones nuevas **A-163** a **A-173**.

**Las once decisiones nuevas:**

| Nueva | Qué cierra |
|---|---|
| **A-163** | Acceso de lectura del equipo docente a los repositorios privados. Sin ella **R2.4.8**, **R2.7.4** y el enlace de **R2.5.10** devolvían `404` al corrector |
| **A-164** | Quién es sujeto de una tarea. De ella cuelgan **R2.3.7**, **R2.3.10**, **R2.4.5** y **R2.5.4** |
| **A-165** | Administración de usuarios y de miembros del curso. La mitad «administrar» de **R2.1.1** |
| **A-166** | Cómo entra el evaluador a la aplicación entregada (**§3.1**, **§3.2**) |
| **A-167** | Contra qué opera el entorno `ensayo` frente a Canvas |
| **A-168** | Quién archiva un repositorio y con qué efecto. Cierra la máquina 2 |
| **A-169** | Lista cerrada de escrituras externas síncronas desde una pantalla |
| **A-170** | Repositorio de operaciones, cómo se crea y cómo se sube el respaldo. De él cuelga la Ley 4 |
| **A-171** | Zona horaria del bucket diario y qué commit cuenta en cada métrica |
| **A-172** | `entrega.slug` y numeración del tag |
| **A-173** | Definición de «entrega anterior» para las ventanas de **R2.5.7** |

**Las reescrituras de fondo:** A-004 y A-112 (latido), A-021 (permisos por defecto), A-023 (versión por membresía), A-027 y A-028 (una organización, un curso), A-030 (qué se borra y qué no), A-033 (identidad de Canvas por instancia), A-035 (política de API de Canvas), A-036 (credencial nueva), A-041 (18 comprobaciones), A-048 y A-092 (estado del repositorio de grupo), A-060 (permisos de la App), A-080 (entrega única), A-090 (presupuesto real de 500 MB), A-096 (retroceso del sondeo), A-107 y A-108 (nombre de repositorio), A-114 y A-115 (cerrojo y ritmo), A-122 (ventanas), A-125 (outbox y síncrono), A-130 (alcance y topes), A-131 a A-133 (zona, cuota de correo), A-138 (validaciones al vincular), A-139 (publicación en grupo), A-143 (plan alternativo que sí cumple **R2.7.6**), A-151 (mapa de pantallas), A-159 (guion), §19 y §21.

### 0.6 La enmienda de reconciliación: A-174 a A-235, y cómo se leen las decisiones anuladas

La reconciliación de las **590 respuestas de alcance** produjo cuatro actas de arbitraje —`.workflow/acta/final/parte-1-datos.md`, `parte-2-integraciones.md`, `parte-3-gobierno.md` y `parte-4-cruce.md`— con reglas numeradas `RG-nnn`. Las reglas que afectan a más de un área pertenecen a esta carta y **están incorporadas aquí como las 62 decisiones A-174 a A-235**. Es la **enmienda única de RG-190**, y es previa a toda migración y a todo uso de un código de estado, de incidencia, de trabajo, de motivo o de entidad nuevo (**A-235**).

**Cómo se leen las decisiones anuladas, porque ninguna se borra.** Una decisión cuyo contenido ha sido superado lleva en su primera línea la marca **`— ANULADA POR RG-nnn`** y, justo debajo, una línea que dice **qué decisión manda ahora**. La decisión antigua **permanece íntegra** para que las citas anteriores —de las 590 respuestas, de las actas y de los informes— sigan teniendo sentido y se pueda comprobar qué cambió y por qué.

> **Regla de lectura, sin excepciones.** Ante una decisión marcada como anulada, **manda siempre la decisión que su línea de sustitución nombra**. Citar una decisión anulada sin citar su sustituta es un defecto de revisión y se rechaza.

**Orden de autoridad tras la enmienda:** enunciado → esta carta → las cuatro actas → las 590 respuestas de los lotes. Dentro de las actas, la **parte 4** arbitra sobre las partes 1, 2 y 3.

---

## 1. Las cinco restricciones que atraviesan todo

### 1.1 El equipo tiene rol de PROFESOR en Canvas, no de administrador de cuenta

Es la restricción más importante del proyecto. Consecuencias que se aceptan como marco, no como problema a resolver:

- **No hay Developer Key propia para OAuth2 en el caso general.** La guía de OAuth2 de Canvas dice que en Canvas Cloud las developer keys las emite el administrador de la institución, y que habilitar *scopes* es capacidad exclusiva de un administrador de cuenta raíz **[DOC]** (`Q-infraestructura-08`). **El camino que se implementa es el token de acceso personal generado por el propio profesor.** OAuth2 con Developer Key institucional queda como camino alternativo condicionado, y **no se le asigna ninguna funcionalidad que no exista también por token**.
- **No hay suplantación.** `as_user_id` exige el permiso «Become other users» **[DOC]** (`Q-2.7-49`). Toda escritura en Canvas —notas, rúbricas, anuncios, mensajes, comentarios— aparecerá firmada por el profesor titular del token, sea quien sea el ayudante que la originó. No es un defecto: es una consecuencia del rol, se declara en la interfaz y se compensa (A-142).
- **No hay informes de cuenta ni acceso garantizado a `sis_user_id`.** El campo sólo se incluye si el usuario vino de un import SIS y el llamante tiene permiso para ver información SIS **[DOC]** (`Q-2.2-30`). Por eso la clave de identidad del estudiante es `canvas_user_id` (A-074).
- **No hay creación de cursos por API.** El curso de Canvas existe antes que la aplicación; la aplicación lo vincula, nunca lo crea.
- **El roster puede llegar recortado sin aviso** si la matrícula de profesor del titular tiene `limit_privileges_to_course_section=true`. Que la API recorte en silencio no está documentado **[MEDIR]** (`Q-2.1-28`), pero el flag sí es legible en la propia matrícula **[DOC]**, y por eso el asistente lo lee y bloquea (A-052).

**Toda decisión que dependa de privilegios de administrador de Canvas está mal planteada y queda descartada de antemano.**

### 1.2 Canvas Free-for-Teacher ya no existe

Instructure discontinuó el programa de forma permanente y no registra cuentas nuevas **[DOC]** (`Q-infraestructura-08`, `Q-infraestructura-09`). La aplicación se desarrolla y se demuestra contra la **instancia institucional del curso**, con el token del integrante que tenga rol de profesor. No se planifica ningún camino que dependa de FFT.

### 1.3 La organización de GitHub es nueva y de plan gratuito

- **No hay rulesets ni protección de ramas en repositorios privados** con plan Free **[DOC]** (`Q-infraestructura-22`). Un tag de entrega es borrable por cualquiera con permiso de push. De ahí la Ley 4 (§2).
- **Cupos de invitación documentados** **[DOC]** (`Q-2.3-32`, `Q-2.3-33`): 50 invitaciones **por repositorio** cada 24 h, **sin límite si se invita a miembros de la organización a un repositorio de la organización**; y 50 invitaciones **a la organización** cada 24 h mientras la organización tenga menos de un mes o esté en plan gratuito. Esa asimetría es una de las razones de A-064 **y la razón de que el equipo docente entre a la organización antes que ningún repositorio** (A-163).
- **Reparto explícito del cupo de invitaciones a la organización.** Los estudiantes **no** consumen cupo de organización: entran como colaboradores de repositorio (A-064). El único consumo de ese cupo es el **equipo docente**, que se incorpora **una sola vez por curso**: profesores, ayudantes y —para la entrega— el evaluador (A-166). Presupuesto declarado: **≤ 15 invitaciones a la organización por curso**, muy por debajo de las 50 de una ventana de 24 h, y se emiten en el paso de vinculación, no durante el aprovisionamiento. Una vez que son miembros de la organización, añadirlos como colaboradores de lectura de cada repositorio **no consume cupo alguno** y responde `204` **[DOC]** (`Q-2.3-32`, `Q-2.3-33`). Es exactamente lo que hace viable A-163 a escala de 600 repositorios.

### 1.4 Los estudiantes NO son usuarios de la aplicación

El enunciado lo dice en §1 y lo repite en §2.3. Consecuencias arquitectónicas duras:

- **La aplicación no expone ninguna pantalla para estudiantes**, ni de sólo lectura. No hay alta de estudiante, no hay sesión de estudiante, no hay ruta pública de estudiante.
- Todo lo que el estudiante hace ocurre **en Canvas** (leer un anuncio, leer un mensaje, entregar un texto, leer un comentario) o **en GitHub** (aceptar una invitación, hacer push).
- Esto descarta por sí solo el enrolamiento por OAuth de GitHub del estudiante (A-149).

### 1.5 Dos despliegues en dominios distintos

Entrada fija del equipo: backend FastAPI en Render como contenedor Docker, frontend React en Vercel. Obliga a resolver CORS, sesión entre sitios y configuración del origen del backend de forma explícita y profesional (A-008, A-009).

---

## 2. Las cinco leyes del diseño

Toda decisión posterior es aplicación de una de estas cinco leyes. Si una decisión futura las contradice, la decisión está mal.

- **Ley 1 — Espejo, no caché.** La base de datos de la aplicación es un espejo mantenido de Canvas y de GitHub. Todo lo que alimente una lista, un tablero, una decisión de un trabajo de fondo o un registro histórico se persiste en Postgres con su marca de origen y de sincronización. **Ninguna vista consulta una API externa para renderizarse.** La consulta en vivo es la excepción y está enumerada exhaustivamente en A-089. Esto no es rendimiento: es **R2.5** literal, que exige la información «de forma inmediata al ingresar a la vista de una tarea, sin requerir esperar a que se recopile en ese momento la actividad de todos los repositorios».
- **Ley 2 — Nada se sobreescribe, todo se supersede.** Versiones de entrega, mapeos, fechas efectivas y publicaciones de nota son *append-only* con una fila vigente. Editar en sitio destruiría la trazabilidad que exigen **R2.4.6**, **R2.4.7** y **R2.7.6**.
- **Ley 3 — La clave es la duradera, no la legible.** Se persiste siempre el identificador estable del sistema externo (`canvas_user_id`, `canvas_enrollment_id`, `github_user_id`, `github_repo_id`) y el nombre legible (`login`, `nombre`, `full_name`) es un atributo mutable. El login de GitHub puede renombrarse y **el antiguo queda libre para que otra persona lo reclame** **[DOC]** (`Q-2.3-66`): un modelo con `login` como clave es un modelo roto.
- **Ley 4 — La evidencia vive en nuestra base de datos.** El `commit_sha` persistido es la evidencia normativa de una entrega. El tag de Git es una comodidad de navegación. Con organización Free no hay rulesets en repositorios privados **[DOC]** (`Q-infraestructura-22`), de modo que el tag es borrable y no puede ser la verdad.
- **Ley 5 — Un límite de una API externa nunca se pinta como error del equipo.** Se pinta como estado transitorio, con la hora de reintento visible. GitHub advierte que seguir pidiendo mientras se está limitado **puede acabar en el baneo de la integración** **[DOC]** (`Q-transversal-39`), así que el respeto del límite es una regla dura del cliente, y la distinción visual es una obligación de la interfaz.

---

## 3. Stack, entornos y despliegue

### A-001 · Backend

**FastAPI sobre Python 3.12**, empaquetado como imagen **Docker** y desplegado en **Render**. Bibliotecas fijadas y no negociables: `SQLAlchemy 2.x` + `Alembic` (persistencia y migraciones), `pydantic v2` (contratos de entrada y salida), `httpx` (cliente HTTP con *timeouts* explícitos), `structlog` (logs estructurados), `cryptography` (AES-256-GCM), `PyJWT` (JWT de la GitHub App y firmas internas), `tenacity` (reintentos con *backoff*). Sirve a todos los requisitos por ser el sustrato.

### A-002 · Frontend

**React 18 + TypeScript + Vite**, desplegado en **Vercel**. Enrutado con `react-router`; estado de servidor con `TanStack Query` (revalidación e invalidación explícitas, sin estado global duplicado); formularios con `react-hook-form` y validación `zod`; componentes propios sobre primitivas `Radix UI` para accesibilidad de teclado y foco. La URL del backend viaja en `VITE_API_BASE_URL`, distinta por entorno. Sirve a **R2.1**–**R2.7** por ser el único canal de acceso, y §4 del enunciado («lo que no se puede usar no cuenta») lo convierte en requisito.

### A-003 · Dos procesos Render desde la misma imagen

Un **servicio web** que sirve la API y un ***background worker*** que ejecuta la cola de trabajos y el planificador. Comparten imagen, código y base de datos, y se diferencian por el comando de arranque. Motivo: un fallo o una saturación del trabajador no debe degradar la interfaz que el evaluador está mirando, y separar permite escalar y reiniciar cada mitad por su cuenta.

Sirve a **R2.3.10**, **R2.4.5**, **R2.6.1**.

### A-004 · Los dos servicios corren en plan de pago mínimo, no en el gratuito

**Contratados desde el 10 de septiembre de 2026 hasta el 31 de octubre de 2026.** Es una decisión de cumplimiento, no de comodidad: Render suspende un servicio web gratuito que pasa 15 minutos sin tráfico entrante **[DOC]** (`Q-infraestructura-34`). Un servicio suspendido produce tres incumplimientos simultáneos y visibles:

1. Se pierden webhooks de GitHub, que son la fuente principal de **R2.5.2** y **R2.5.3**.
2. No corren los trabajos periódicos: no hay creación progresiva (**R2.3.10**), no hay captura de versión al cierre (**R2.4.5**), no hay informe diario (**R2.6.1**).
3. La primera carga tarda decenas de segundos, lo que contradice frontalmente **R2.5.1**.

Se descarta expresamente **el plan gratuito sostenido con un *pinger* externo**: mantiene el servicio vivo pero no elimina el arranque en frío del primer golpe, y es exactamente el tipo de artefacto que no se sostiene en una revisión de código. El coste mensual es el precio de tres requisitos.

**Precisión que hay que leer junto a A-112, porque la revisión 1 se contradecía aquí.** Lo que esta decisión descarta es *sustituir el plan de pago por un pinger*: usar tráfico artificial para que un servicio gratuito no se suspenda. Lo que A-112 instituye es otra cosa y **no es un pinger**: es un **vigilante externo** que, cada 10 minutos, comprueba desde fuera del propio despliegue que el planificador ha ejecutado un ciclo reciente y **abre incidencia y alerta si no**. No mantiene nada vivo —los servicios de A-004 no se suspenden— y **no se descarta**, porque un vigilante que corre en el mismo proceso que vigila no vigila nada. La prueba de que no son lo mismo es qué ocurre si el vigilante deja de correr: con un pinger, el servicio se suspende; con A-112, sólo se pierde la alerta temprana, y el sistema sigue funcionando.

### A-005 · Base de datos: PostgreSQL en Supabase, plan gratuito

Es la **única** base de datos del sistema. No hay Redis, no hay almacén de objetos, no hay segundo motor. Las alternativas se descartan por documentación, no por gusto **[DOC]** (`Q-infraestructura-34`):

- **Render Free Postgres queda descartado.** Expira 30 días después de su creación y una base expirada es **inaccesible** salvo que se pase a plan de pago; los 14 días de gracia sirven para pagar, no para consultar. Una base creada el 10 de septiembre deja de responder el 10 de octubre, **en mitad de las dos semanas posteriores al 6 de octubre en las que §3.2 del enunciado exige la aplicación disponible**. Es un incumplimiento garantizado.
- **Neon Free queda descartado** por el tope de 100 CU-hours por proyecto: con un trabajador que consulta la base cada 30 segundos el compute está prácticamente siempre despierto y el presupuesto mensual se agota. Su arranque en frío documentado, de unos cientos de milisegundos, **no** era el problema.
- **Supabase Free encaja** porque su criterio de pausa es la inactividad de una semana y «unas pocas peticiones diarias» bastan para evitarla; el planificador produce esa actividad por diseño. El límite de 500 MB por proyecto es holgado (A-090) y el plan concede dos proyectos, que es exactamente lo que se necesita (A-006).

### A-006 · Dos entornos completos y separados

`produccion` y `ensayo`, cada uno con su proyecto Supabase, su servicio Render, su GitHub App y su organización de GitHub. **La demostración del 16 de septiembre se hace contra `produccion`**, con el conjunto de datos de demostración cargado; `ensayo` existe para probar de forma destructiva sin miedo.

**Contra qué apunta `ensayo` en el lado de Canvas está decidido en A-167 y no se deja abierto**, porque §1.1 establece que no hay creación de cursos por API y prometer un entorno destructivo que no existe sería peor que no prometerlo. En GitHub sí hay dos organizaciones reales: crear una organización gratuita no depende de nadie.

### A-167 · Contra qué opera el entorno `ensayo` en el lado de Canvas

A-006 prometía a `ensayo` «su curso de Canvas cuando sea posible», y §1.1 establece que **no hay creación de cursos por API** y que el equipo recibe **un** curso. Si `ensayo` no tiene curso, no puede «probar de forma destructiva sin miedo» nada que toque Canvas, y **toda prueba destructiva caería sobre el único curso real**, que además es contra el que se demuestra el 16 de septiembre. Un entorno destructivo que no existe es peor que no prometerlo. Decisión, en dos capas que conviven:

**Capa 1 — Doble de pruebas del `ClienteCanvas`, que es lo que se implementa y no depende de nadie.** `ensayo` arranca con `CANVAS_MODO=doble`, y en ese modo la interfaz `ProveedorCredencialCanvas` y `ClienteCanvas` (A-032, A-039) se satisfacen con una implementación alimentada por **respuestas grabadas del curso real en modo sólo lectura**, guardadas como ficheros JSON versionados en `infra/grabaciones_canvas/`:

- **Se graban una sola vez**, ejecutando los `GET` del curso real con el token del profesor, y **se anonimizan al grabar**: nombres y correos de estudiantes se sustituyen por sinónimos estables, los `canvas_user_id` se conservan porque son la clave del modelo (A-074) y no son datos personales por sí solos.
- **Cubren el catálogo entero de lecturas** que el sistema hace: roster, secciones, matrículas, categorías, grupos, pertenencias, assignments, overrides, permisos, períodos, `late_policy`, rúbricas y submissions.
- **Las escrituras se aceptan, se registran y no salen a ninguna parte.** Publicar una nota en `ensayo` devuelve una respuesta verosímil y queda en `bitacora` marcada como simulada. **Es el mecanismo que hace posible ensayar el caso «cae Canvas» de A-036 y el guion de fallos de A-159 sin tocar el curso real.**
- **`ensayo` NUNCA puede apuntar al curso real.** El arranque comprueba que `CANVAS_BASE_URL` de `ensayo` no coincide con la de `produccion`, y **si coincide el proceso no arranca**. Es una comprobación de seguridad, no una convención.

**Capa 2 — Segundo curso real, si se consigue.** Se solicita al administrador de la instancia **un segundo curso de pruebas** con el mismo integrante como profesor, por escrito y **antes del 12 de septiembre** (RA-27). Si llega, `ensayo` conmuta a `CANVAS_MODO=real` apuntando a **ese** curso, y el doble queda como modo de desarrollo local, que es donde siempre es útil por ser rápido y determinista. **Nada del diseño cambia al conmutar**: es la misma interfaz.

**En GitHub no hay este problema.** `ensayo` tiene su propia organización gratuita y su propia GitHub App, creadas por el equipo sin depender de nadie (A-006), y ahí las pruebas destructivas son reales. **El único recurso que no se puede duplicar por decisión propia es el curso de Canvas, y por eso es el único que tiene doble.**

### A-007 · Conexiones y vigilancia de tamaño

Conexión **siempre por el conector con *pooling*** de Supabase, con tope duro de **10 conexiones** por proceso (web y trabajador por separado) configurado en el pool de SQLAlchemy. El límite real de conexiones simultáneas del plan Free no está documentado **[MEDIR]** (`Q-infraestructura-34`), así que se fija un techo propio conservador en vez de descubrirlo en producción. Un trabajo diario mide `pg_database_size` y **avisa por correo al superar 300 MB** (60 % del límite).

### A-008 · Dominio propio, y por qué

Se registra un **dominio propio** y se publica el frontend en `app.<dominio>` (Vercel) y el backend en `api.<dominio>` (Render), ambos con certificado gestionado. **No se opera sobre `*.vercel.app` y `*.onrender.com`.** Con esa topología la cookie de sesión es *same-site* y desaparece por construcción el problema de las cookies de terceros, del bloqueo por ITP de Safari y del `state` de OIDC que no sobrevive al redirect en ventana privada **[MEDIR]** (`Q-2.1-06`).

### A-009 · Sesión, CORS y CSRF

- **Sesión:** cookie **opaca** (identificador aleatorio de 256 bits) con `Domain=.<dominio>; HttpOnly; Secure; SameSite=Lax; Path=/`. El estado vive en la tabla `sesion`, **no** en un JWT autocontenido, para que el retiro de un ayudante (**R2.1.9**) invalide sus sesiones de inmediato. Expiración deslizante de **12 horas** y absoluta de **7 días**.
- **CORS:** lista blanca explícita (`https://app.<dominio>` y `http://localhost:5173`), `allow_credentials=True`, métodos y cabeceras enumerados. Las URLs de *preview* de Vercel se admiten mediante expresión regular anclada al proyecto y **sólo en preproducción**. `allow_origins=["*"]` está **prohibido** y hay una prueba automatizada que falla si aparece.
- **CSRF:** toda mutación exige cabecera `X-CSRF-Token` contrastada contra una cookie de doble envío no `HttpOnly`. `SameSite=Lax` cubre el caso general; el doble envío cubre la navegación de nivel superior.

### A-010 · Contingencia de sesión, con fecha de decisión

Si el dominio propio no está operativo el **12 de septiembre**, se conmuta a *bearer token* de acceso de 15 minutos guardado en memoria del frontend, con *refresh token* rotativo, hasheado en base, con detección de reutilización y revocación en cadena. **La decisión de conmutar se toma el 12 de septiembre, no el 15.** Es una contingencia declarada, no una opción abierta.

### A-011 · Un único repositorio, público, del equipo

Monorepo con `backend/`, `frontend/`, `infra/`, `docs/`, `.workflow/` y `.github/workflows/`. **La estructura interna de `backend/app/` está fijada aquí y no es negociable**, porque de ella depende una puerta de CI (A-012):

```
backend/app/
  dominio/        reglas de negocio puras: entidades, máquinas de estado, cálculo
                  de fecha efectiva, materialización de sujetos, atribución de
                  commits, ventanas de entrega, normalización de nombres.
                  NO importa httpx, ni SQLAlchemy, ni FastAPI. Sin E/S.
  adaptadores/    ClienteCanvas, ClienteGitHub, ProveedorCorreo, repositorios
                  SQLAlchemy. Todo lo que habla con el mundo.
  api/            rutas FastAPI, esquemas Pydantic de entrada y salida.
  trabajos/       los trabajos del catálogo cerrado de A-114.
  infraestructura/ configuración, cifrado, logs, migraciones.
```

**`backend/app/dominio/` es literalmente lo que A-012 llama «la capa de dominio».** No es una expresión de estilo: es esa ruta, y la puerta de cobertura se mide sobre ella con `pytest --cov=backend/app/dominio`. La regla que la hace medible: **si un módulo de `dominio/` importa `httpx`, `sqlalchemy` o `fastapi`, la construcción falla**, con una prueba de arquitectura que recorre los imports. Así la cobertura del 70 % es una promesa verificable y no una frontera que cada agente traza donde le conviene.

Es **público** por dos razones concretas: §3.2 del enunciado exige entregar todo el código por GitHub, y en una organización con plan Free **la protección de ramas sólo está disponible en repositorios públicos** **[DOC]** (`Q-infraestructura-22`). Ser público obliga además a una higiene de secretos desde el primer día (A-014).

### A-012 · CI/CD desde el primer día — ANULADA POR RG-161 en su tabla de puertas

> **Manda ahora A-174.** Las diez puertas de herramienta de esta tabla se conservan íntegras; lo que queda superado es la única fila de contrato —«Contrato de autorización»—, que pasa a ser un conjunto cerrado de **ocho puertas de contrato** con orden de evaluación escrito.

GitHub Actions, con estas puertas obligatorias en cada `push` y cada *pull request*:

| Puerta | Herramienta | Condición de fallo |
|---|---|---|
| Formato y lint del backend | `ruff format --check`, `ruff check` | cualquier hallazgo |
| Tipos del backend | `mypy --strict` sobre `backend/app` | cualquier error |
| Pruebas del backend | `pytest` con `pytest-cov` | fallo, o cobertura de línea **< 70 % medida con `--cov=backend/app/dominio`** (la ruta exacta que A-011 declara como capa de dominio) |
| **Pureza del dominio** | prueba de arquitectura sobre los imports | cualquier módulo de `backend/app/dominio/` que importe `httpx`, `sqlalchemy` o `fastapi` |
| Migraciones | `alembic upgrade head` sobre base efímera y comprobación de que no hay migración pendiente de generar | divergencia entre modelos y migraciones |
| Lint y tipos del frontend | `eslint`, `tsc --noEmit` | cualquier error |
| Build del frontend | `vite build` | fallo |
| Build de la imagen | `docker build` | fallo |
| Secretos | `gitleaks` sobre árbol e historial del push | cualquier hallazgo |
| Dependencias | `pip-audit`, `npm audit --omit=dev` | vulnerabilidad alta o crítica |
| **Contrato de autorización** | prueba que recorre todas las rutas registradas | ruta bajo `/api/cursos/{curso_id}` sin dependencia de permiso |

`main` está protegida: no se empuja directo, se integra por *pull request* con todas las puertas en verde. El despliegue a producción se dispara **sólo** al integrar en `main`, mediante *deploy hooks* de Render y la integración de Git de Vercel.

### A-013 · Migraciones — ANULADA POR RG-144, RG-145, RG-146 y RG-193 en su calendario

> **Manda ahora A-175.** La regla de compatibilidad hacia atrás se conserva; lo que queda superado es la libertad de migrar cuando haga falta: hay **una sola migración de esquema, anterior al 16 de septiembre**, y la fase de *contract* queda prohibida hasta el 31 de octubre.

Alembic. **Las aplica el trabajador al arrancar**, tomando antes un `pg_advisory_lock`; el servicio web nunca migra. Regla dura: las migraciones son compatibles hacia atrás dentro de un despliegue —se añade columna, se rellena, se empieza a leer; nunca se borra en la misma versión en que se deja de escribir—, de modo que un despliegue a medias no deja el esquema inconsistente.

### A-014 · Configuración y secretos — ANULADA POR RG-138, RG-081 y RG-202 en su inventario

> **Manda ahora A-176**, que cierra el inventario en **quince entradas** con custodio y fecha de retirada, y **A-191**, que sustituye `APP_ENCRYPTION_KEY` por el llavero versionado. Se conservan íntegras las dos reglas de fondo: ninguna configuración fuera de variables de entorno y **ningún secreto en el repositorio**.

Toda configuración por variables de entorno; **ningún secreto en el repositorio**. `.env.example` lista todas las claves y ningún valor. Secretos operativos: `DATABASE_URL`, `APP_ENCRYPTION_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` (PEM en base64), `GITHUB_WEBHOOK_SECRET`, `EMAIL_PROVIDER_API_KEY`, `SIGNING_KEY`. El procedimiento de **rotación** de cada uno está escrito en `docs/operacion.md` y se ensaya una vez antes del 6 de octubre.

### A-015 · Observabilidad — ANULADA POR RG-143, RG-127 y RG-204 en dos puntos

> **Mandan ahora A-177**, que fija **cinco** alertas por correo y no cuatro, y **A-232**, que acota `/operacion` a los cursos donde el solicitante es PROFESOR ACTIVO y le da un inventario único de secciones. Se conserva íntegro todo lo demás: los logs estructurados con redacción central, las dos sondas y el registro de coste de cada llamada saliente.

- **Logs JSON estructurados** con `correlacion_id`, `curso_id`, `usuario_id`, `trabajo_id`, `proveedor`, `endpoint`, `codigo_http`, `duracion_ms`. La cabecera `Authorization` y cualquier credencial se **redactan en un filtro central**; no se confía en la disciplina de quien escribe cada log.
- **`GET /salud`** (vivo) y **`GET /estado`** (listo: base de datos, presupuesto de GitHub, validez de la credencial de Canvas por curso, antigüedad de la última sincronización por curso).
- Cada llamada saliente registra el coste: `X-Request-Cost` y `X-Rate-Limit-Remaining` de Canvas; `x-ratelimit-remaining`, `x-ratelimit-used` y `x-ratelimit-resource` de GitHub. **Es la única forma de conocer el presupuesto real**, porque GitHub no publica el coste en puntos de todos los endpoints ni permite consultar el estado del límite secundario **[DOC]** (`Q-2.5-08`, `Q-transversal-38`).
- **Panel de operación** en `/operacion`, visible sólo para profesores: colas por estado, trabajos en `REQUIERE_ATENCION` con su error literal, presupuesto de GitHub, consumo acumulado de Canvas, últimos webhooks recibidos y última ejecución de cada trabajo periódico. Durante la demostración, este panel es la mejor respuesta posible cuando algo externo falla: se abre y se muestra la causa.
- **Alertas por correo** al equipo en cuatro condiciones: credencial de Canvas inválida, presupuesto de GitHub por debajo del 20 %, tres fallos consecutivos del *outbox*, y un trabajo periódico sin ejecutarse durante tres ciclos.

### A-016 · Respaldo diario

Un trabajo nocturno a las 05:00 exporta un `pg_dump` comprimido y **cifrado**, y lo deposita en el **repositorio privado de operaciones** cuya creación, credencial y alcance fija **A-170** —no se dan por supuestos, porque de este respaldo cuelga entera la Ley 4—. Retención de 14 días. Motivo directo: la evidencia de las entregas vive en la base y el plan gratuito de Supabase no ofrece respaldos gestionados. Sin este respaldo, la base es punto único de fallo de toda la evidencia de **R2.4.5**–**R2.4.7**.

### A-174 · Las ocho puertas de contrato, cerradas y con orden de evaluación

**Amplía A-012 y sustituye su única fila de contrato.** Las **diez puertas de herramienta** de A-012 —formato y lint del backend, tipos, pruebas con cobertura, pureza del dominio, migraciones, lint y tipos del frontend, build del frontend, build de la imagen, secretos y dependencias— **se conservan sin cambios**. Junto a ellas corren **ocho puertas de contrato, ninguna más**, en un único *workflow* `.github/workflows/puertas.yml` con un trabajo por fila y **en este orden de evaluación**:

| # | Puerta | Falla la construcción si… | Fuente de datos única |
|---|---|---|---|
| 1 | **Contrato de autorización** | una ruta bajo `/api/cursos/{curso_id}` se registra sin dependencia de permiso | el enrutador real de FastAPI |
| 2 | **Rol fuera de la dependencia** | aparece una lectura de `membresia_curso.rol` con efecto de autorización fuera de `requiere(...)`, o una ruta registrada pasa `rol_minimo` sin figurar en `ACCIONES_SOLO_PROFESOR` | la constante `ACCIONES_SOLO_PROFESOR` (A-179) |
| 3 | **Superficie sin sesión** | se registra una ruta sin dependencia de sesión que no figura en la tabla de A-182 | la tabla de A-182 |
| 4 | **Registro por perfil** | bajo el perfil en curso aparece registrada una ruta que A-233 declara oculta en ese perfil, o falta una que declara registrada | la lista de A-233 |
| 5 | **Acotación del panel** | una ruta de `/api/operacion/**`, o `/api/estado` en su forma completa, se registra sin la dependencia que acota por los cursos del solicitante | A-232 |
| 6 | **Alcanzabilidad** | el caso 9 de A-151 regla 0, parametrizado por `PERFIL_ALCANCE`, no pasa en el modo correspondiente a la construcción | el enrutador real y la tabla de A-157 como estructura de datos |
| 7 | **Migraciones** | aparece un fichero de migración con fecha posterior al 16 de septiembre que contenga `DROP`, `ALTER … TYPE`, un cambio de clave o un cambio de unicidad; o el esquema desplegado no contiene alguna columna o algún valor de catálogo de A-175 | el esquema desplegado |
| 8 | **Banderas** | queda en el código una bandera del catálogo de A-233 sin usar, o el catálogo no está vacío después del **5 de octubre a las 12:00** | el catálogo de A-233 |

**Tres reglas de convivencia, que no son consejos:**

1. **Las puertas 3 y 4 son complementarias y se evalúan en ese orden.** La 3 dice *qué está permitido que exista sin sesión*; la 4 dice *qué está permitido que exista hoy*. Una ruta puede figurar en A-182 y estar prohibida en el perfil en curso; el caso contrario —registrada en el perfil y ausente de A-182— **es siempre un fallo**.
2. **Ningún rojo se resuelve registrando media pantalla ni relajando una comprobación de seguridad.** Si una puerta se pone en rojo por una decisión de alcance, la salida es **mover la bandera**, no bajar la puerta. Registrar una pantalla a medias es exactamente el «comportamiento parcial» que A-156 y §4 del enunciado prohíben.
3. **Las ocho corren en los dos perfiles.** Las puertas 4 y 6 se parametrizan por `PERFIL_ALCANCE`; las otras seis dan el mismo resultado en los dos.

**Pruebas de arquitectura que cuelgan de la puerta de pruebas del backend de A-012**, y que fallan la construcción igual que las ocho anteriores: `test_check_coincide_con_enum`, `test_toda_transicion_declarada_tiene_origen_alcanzable` y `test_todo_codigo_tiene_etiqueta` (A-209); la prohibición de `ON DELETE CASCADE` y `ON DELETE SET NULL` (A-200); la validación de `bitacora.accion` y de `bitacora.entidad` contra sus catálogos (A-184); la comprobación de que todo modelo SQLAlchemy está en el censo (A-198); la que prohíbe que un manejador de `backend/app/api/` invoque `ClienteCanvas` o `ClienteGitHub` fuera de las seis escrituras de A-169 (A-226); la del orden y el anidamiento de cerrojos (A-217); y la que prohíbe un literal `"author"` o `"committer"` en el cuerpo de `POST /git/commits` y de `PUT /contents` (A-196).

Sirve a **R2.1.7**, **R2.1.8**, **R2.1.9**, y por construcción a todos los requisitos citados en A-151 y en A-157.

### A-175 · Una sola migración de esquema, y es anterior al 16 de septiembre

**Sustituye el calendario de A-013.** Hay **una sola migración de esquema en todo el proyecto** y **es anterior al 16 de septiembre**. Crea, de una vez:

1. **Las 70 entidades del censo de A-198**, incluidas las diez que ningún código leerá hasta la entrega final. Crear diez tablas vacías cuatro semanas antes no cuesta nada y elimina la única migración que podía fallar delante del evaluador.
2. **Todas las columnas, índices y restricciones que la autorización y la seguridad necesitan**, aunque el código que las lee llegue después. Lista cerrada: `membresia_curso.org_github_alta_por_app` y `.es_via_compartida`; los cuatro `CHECK` sobre `permisos` y `rol` de `membresia_curso` e `invitacion_equipo` (A-181); `usuario.cuenta_github_id` con índice único parcial donde no es nulo, `usuario.consentimiento_github_en` y `usuario.generacion_enlaces`; `credencial_canvas.version_clave`; `bitacora.permiso_exigido`, `.ruta` y `.metodo`; `suscripcion_informe.origen_baja` y `.dada_de_baja_en`; la tabla `cubo_tasa` con PK `(clave, ventana_inicio)`; y `verificacion_vinculacion.detalle jsonb` con las cuatro sub-comprobaciones de la organización. Viajan también `commit.parent_shas`, `commit.en_rama_por_defecto`, `commit.recibido_en`, `cursor_sincronizacion.ultimo_backfill_en`, `curso.ingesta_actividad_desde` y `mensaje_saliente.reserva`.
3. **Todos los valores de todos los catálogos cerrados** que cualquier bloque posterior vaya a escribir: los **51** tipos de incidencia de A-207, los siete subtipos de A-098, los enums de las **siete** máquinas de A-209, los veinte motivos de `mensaje_saliente.motivo_estado`, los dieciséis de `trabajo.motivo_cancelacion`, los seis de `acceso_repositorio.motivo_revocacion`, los cinco de `version_entrega.motivo`, los siete de `tag_motivo`, los cinco de `verificacion_vinculacion.resultado`, los cinco de `membresia_curso.org_github_estado`, los diez de `correccion.motivo_no_publicable` y el valor `PENDIENTE_BLOQUE_2` de `evento_webhook.estado`.
4. **Todos los índices únicos parciales** que el patrón *append-only* exige: `mapeo_github` (A-077), `identidad_git` (A-201), `repositorio` (A-202) y `version_entrega` (A-204).

**No hay ninguna migración de esquema entre el 16 de septiembre y el 6 de octubre.** Después del 16 la política es **expand–contract y sólo aditiva** —se añade columna, se rellena, se empieza a leer—, y **la fase de *contract* queda prohibida hasta el 31 de octubre**: una columna que sobre se deja y se documenta.

**Por qué.** Ampliar un `CHECK` es un `ALTER`, y un `ALTER` en la ventana de la entrega final pone en rojo la puerta 7 de A-174 el mismo día de la defensa. Sin esta regla, **la primera incidencia de un tipo nuevo abortaría la transacción que la abre**, en producción y delante del evaluador.

**Prueba de arranque obligatoria:** al iniciar, el proceso compara el esquema desplegado con el esperado y **falla si falta una columna o un valor de catálogo** de esta lista. `docs/operacion.md` declara qué tablas nacen vacías y qué bloque las empieza a escribir.

Sirve a **R2.4.5**, **R2.4.7**, **R2.5.2**, **R2.5.3**, **R2.5.8**, **R2.5.10** y, por dependencia de esquema, a todos los demás.

### A-176 · Inventario cerrado de quince secretos operativos, con custodio y fecha de retirada

**Sustituye la lista de nueve de A-014.** El inventario es **cerrado**: un secreto vivo fuera de él no se rota, no se custodia y no se retira. Es la lista contra la que se ensaya la rotación antes del 6 de octubre, contra la que se rota el 7 de octubre, y contra la que `gitleaks` comprueba que nada vive en el árbol ni en el historial.

| # | Secreto | Quién lo usa | Custodia y retirada |
|---|---|---|---|
| 1 | `DATABASE_URL` | backend | Bóveda compartida; rotación en `docs/operacion.md` |
| 2 | `APP_ENCRYPTION_KEYS` | cifrado del token de Canvas (A-191) | Bóveda compartida; llavero versionado |
| 3 | `APP_ENCRYPTION_KEY_ACTIVA` | cifrado del token de Canvas (A-191) | Bóveda compartida |
| 4 | `GOOGLE_CLIENT_ID` | OIDC (A-018) | Bóveda compartida |
| 5 | `GOOGLE_CLIENT_SECRET` | OIDC (A-018) | Bóveda compartida |
| 6 | `GITHUB_APP_ID` | backend y `.github/workflows/actividad_demo.yml` | Bóveda compartida y *secrets* del repositorio del equipo |
| 7 | `GITHUB_APP_PRIVATE_KEY` (PEM en base64) | los mismos | Bóveda compartida y *secrets* del repositorio del equipo |
| 8 | `GITHUB_WEBHOOK_SECRET` | receptor de webhooks (A-070) | Bóveda compartida |
| 9 | `GITHUB_WEBHOOK_SECRET_ANTERIOR` | receptor, **sólo durante la ventana de rotación** | Se retira al cerrar la ventana |
| 10 | `EMAIL_PROVIDER_API_KEY` | `ProveedorCorreo` (A-133) | Bóveda compartida |
| 11 | `SIGNING_KEY` | `state` de OIDC y de instalación, tokens de baja y de traza (A-182) | Bóveda compartida |
| 12 | `SIGNING_KEY_ANTERIOR` | verificación, **sólo durante la ventana de 7 días** | Se retira al cerrar la ventana |
| 13 | `GITHUB_ENSAYO_APP_ID` | `infra/prueba_permisos.py`, `infra/medicion_atribucion.py` | Bóveda compartida; **se retira al cerrar RA-02** |
| 14 | `GITHUB_ENSAYO_APP_PRIVATE_KEY` | los mismos | Bóveda compartida; **se retira al cerrar RA-02** |
| 15 | `CANVAS_TOKEN_DEMO` | `infra/semilla_demo.py` | Token del profesor titular del curso de demostración; **se retira el 1 de noviembre** con los accesos del evaluador (A-166 punto 7) |

**Las dos cuentas `gmail.com` de evaluación de A-189 entran en el mismo inventario** como credenciales de acceso, con custodio nombrado y fecha de retirada.

**Ninguno vive en la base de datos ni en el repositorio.** El **token de Canvas es el único secreto que se persiste**, cifrado con el llavero de A-191; **no se persiste ningún token de GitHub** (A-038). **No existe ninguna cuenta de máquina y no existe ningún PAT** en ningún artefacto del proyecto (A-195).

### A-177 · Cinco alertas por correo, y las cinco operativas desde el 16 de septiembre

**A-015 tiene cinco alertas por correo, no cuatro**, y las cinco están **operativas y con envío efectivo desde el 16 de septiembre**:

1. Credencial de Canvas inválida.
2. Presupuesto de GitHub por debajo del 20 %.
3. Tres fallos consecutivos del *outbox*.
4. Trabajo periódico sin ejecutarse durante tres ciclos.
5. **Denegaciones de autorización por encima del umbral** — se dispara cuando una misma `sesion_id` acumula **20 respuestas `403` o `404` de recurso ajeno en 10 minutos**, o una misma IP truncada acumula **50 en 10 minutos**. Abre la incidencia **`DENEGACIONES_ANOMALAS`** y aparece como fila propia en `/operacion` con el recuento de las últimas 24 horas, acotada por A-232.

**Por qué la quinta no espera al Bloque 3:** es la **única vigilancia de seguridad del sistema**, y el período que tiene que vigilar es exactamente aquel en que la aplicación está expuesta con datos reales. Aplazarla la dejaría inútil justo cuando hace falta.

A ellas se suman, **en el mismo régimen y desde la misma fecha**: el correo a todos los profesores del curso del paso 5 de A-036, el aviso de tamaño de base de A-007, la alerta del vigilante externo de A-112, `RESPALDO_FALLIDO` de A-170 y los dos correos de acceso docente de A-187 y A-188.

**Régimen de envío, sin excepciones:** todas van al canal `CORREO` con `reserva = OPERATIVO` (A-228), **agrupadas en un solo correo por ciclo de vigilancia** con todas sus líneas, y **`despachar_outbox` no consulta `curso.comunicaciones_salientes` para este canal** (A-225): una aplicación que no puede avisar de que está rota es peor que una aplicación caída. **Techo transitorio de 40 envíos operativos diarios entre el 16 de septiembre y el 2 de octubre**, con la incidencia informativa `CORREO_OPERATIVO_ELEVADO` por encima de 20. El adaptador `ProveedorCorreo`, con su implementación de producción y la de consola, está en pie el **12 de septiembre**.

**Criterio verificable, en `docs/criterios/`:** «revocado el token de Canvas en el ensayo del 14 de septiembre, llega un correo a cada profesor del curso en menos de un ciclo de vigilancia, y queda una fila en `bitacora`».

---

## 4. Usuarios, roles y permisos

### A-017 · Los usuarios de la aplicación son exclusivamente el equipo docente

Profesores y ayudantes. **Los estudiantes no tienen cuenta, no tienen sesión y no tienen ninguna ruta de acceso, ni siquiera de sólo lectura.** Es §1 del enunciado, y condiciona todo el capítulo de enrolamiento (§15).

Sirve a **R2.1.1**, y es la restricción que gobierna **R2.2.4**–**R2.2.5**.

### A-018 · Alta y acceso con Google OpenID Connect

**R2.1.2** exige registro asociando una cuenta de correo basada en `gmail.com`. Se implementa con **Google OIDC (Authorization Code + PKCE)**, no con contraseña propia: evita almacenar credenciales, aporta verificación de correo de origen y es demostrable en vivo. Reglas fijadas:

1. Se acepta el alta **sólo si** el `id_token` trae `email_verified=true` **y** el dominio del `email` es exactamente `gmail.com`. Se acepta `googlemail.com` normalizándolo a `gmail.com`. **Se rechaza cualquier correo con reclamación `hd`** (dominio gestionado de Workspace), con un mensaje explícito que dice que el enunciado exige una cuenta de `gmail.com`.
2. El parámetro **`prompt=select_account` se envía siempre**, no sólo en un botón de «usar otra cuenta». La documentación de Google describe ese valor como el que hace que el servidor pida seleccionar cuenta y **no garantiza** que sin él se ofrezca elegir **[DOC]** (`Q-2.1-06`). En una demostración con varias sesiones de Google abiertas, un auto-login silencioso a la cuenta equivocada es un fallo caro y evitable.
3. **El `state` y la defensa contra el CSRF de inicio de sesión.** El `state` es un **JWT firmado con HMAC y caducidad de 10 minutos** que contiene tres cosas: el `nonce` esperado, el destino al que volver, y `sha256(txn_id)`. El `txn_id` es un valor aleatorio de 256 bits que viaja **además** en una cookie de un solo uso `oidc_txn` (`Secure; HttpOnly; SameSite=Lax; Path=/auth; Max-Age=600`).

   La revisión 1 decía que prescindir de la cookie «es igual de seguro»; **era falso y se corrige aquí**: la vinculación al navegador es precisamente lo que convierte al `state` en defensa contra el CSRF de inicio de sesión, es decir, contra que un tercero haga que la víctima quede autenticada en la cuenta del atacante. La regla queda así:

   - **Camino normal:** la cookie `oidc_txn` vuelve con el *callback*, su `sha256` coincide con el del JWT, el `nonce` del JWT coincide con el del `id_token`, y la sesión se crea sin fricción. El `nonce` esperado **vive dentro del JWT firmado**, no en el servidor: no hay estado que perder.
   - **Camino degradado, y sólo si la cookie no vuelve** (ventana privada, ITP de Safari, bloqueo de cookies — comportamiento no documentado **[MEDIR]**, `Q-2.1-06`): **la sesión no se crea todavía**. Se muestra en nuestro propio origen una pantalla de confirmación que dice a qué cuenta de Google se va a entrar y exige **un gesto explícito del usuario** con un token anti-CSRF de formulario. Un ataque de inicio de sesión forzado no sobrevive a un gesto en el origen atacado.
   - **La firma, la caducidad y el `nonce` se validan siempre**, en los dos caminos. Un `state` con firma inválida, caducado, ya consumido (se registra su `jti` en `sesion`) o con `nonce` discrepante se rechaza sin excepción.
4. Un usuario recién autenticado **no es profesor de nada**. Se convierte en profesor de un curso al crearlo (**R2.1.3**) o al ser incorporado por otro profesor (**R2.1.7**), y en ayudante al ser incorporado (**R2.1.8**).
5. **`usuario.activo` tiene dueño y semántica**, fijados en A-165. No es una columna decorativa.

### A-019 · Matriz de navegadores declarada

**Chrome, Edge y Firefox de escritorio en ventana normal y privada, más Safari de escritorio en ventana normal.** Safari en navegación privada queda **fuera de alcance declarado**. La prueba en ventana privada antes del 16 de septiembre es criterio de aceptación, no una comprobación opcional.

### A-020 · Dos roles por curso, y el rol vive en la membresía

**PROFESOR** y **AYUDANTE**. Una misma persona puede ser profesora de un curso y ayudante de otro. **R2.1.7** se cumple porque un segundo profesor recibe exactamente los mismos permisos que el primero, sin distinción de «creador» y sin ningún permiso reservado.

### A-021 · Tabla de permisos de profesor y ayudante

Se definen **nueve permisos nombrados**, muy por encima del mínimo de tres que exige **R2.1.8**. Dos son implícitos y siete son configurables. El profesor los tiene **todos, de forma implícita e irrevocable**. Al ayudante se le concede un subconjunto explícito, editable por cualquier profesor del curso, y cada cambio queda en `bitacora`.

| Permiso | Qué habilita exactamente | Profesor | Ayudante: por defecto | Ayudante: concedible |
|---|---|---|---|---|
| `curso.ver` | Ver el curso, personas, tareas, tablero, timeline, estado de repositorios, entregas y fechas | Sí (implícito) | **Sí (implícito)** | — (no revocable mientras la membresía esté activa) |
| `correccion.corregir` | Abrir y trabajar **sólo** las entregas asignadas a uno mismo, guardar la corrección local | Sí (implícito) | **Sí (implícito)** | — (no revocable) |
| `curso.administrar` | Editar el curso, rehacer la vinculación con Canvas o GitHub, sustituir la credencial, cambiar la zona horaria | Sí | No | **NO CONCEDIBLE** |
| `equipo.administrar` | Incorporar y retirar profesores y ayudantes, cambiar permisos | Sí | No | **NO CONCEDIBLE** |
| `tarea.administrar` | Crear y editar tareas, vincular entregas de Canvas, gestionar el repositorio base y sus archivos, forzar aprovisionamiento, reintentar fallos | Sí | No | Sí |
| `mapeo.editar` | Crear, corregir e invalidar el mapeo estudiante ↔ cuenta de GitHub; importar CSV; reenviar invitaciones | Sí | **Sí** | Sí |
| `correccion.asignar` | Repartir las entregas entre los correctores | Sí | No | Sí |
| `nota.publicar` | Escribir calificación, comentario y rúbrica en Canvas | Sí | **No** | Sí |
| `comunicacion.enviar` | Enviar mensajes y anuncios manuales por Canvas y activar o desactivar las comunicaciones automáticas de una tarea | Sí | No | Sí |

**Qué significa exactamente «por defecto», porque la revisión 1 no lo decía y de ahí salían dos implementaciones incompatibles:** es el **conjunto precargado en el formulario de invitación** (A-024). El profesor que invita **lo ve y lo puede editar antes de enviar**, la invitación guarda el conjunto elegido en `invitacion_equipo.permisos`, y **al aceptar se copia tal cual a `membresia_curso.permisos`**. No es una semilla que se aplique sola con valores distintos de los que se vieron en pantalla, y no es un valor inmutable: cualquier profesor puede cambiarlo después desde Equipo, y cada cambio queda en `bitacora` y revoca sesiones (A-023).

**Por qué los dos configurables marcados NO CONCEDIBLES no lo son a un ayudante:** quien puede cambiar la credencial de Canvas puede actuar como el profesor sobre todo el curso, y quien puede administrar el equipo puede concederse a sí mismo el resto. Es una escalada de privilegios trivial y se cierra por diseño, no por confianza.

**Por qué `correccion.corregir` es implícito y `nota.publicar` no se concede por defecto:** el valor por defecto es la configuración conservadora —**ayudantes que corrigen y un profesor que publica**—, porque publicar escribe en Canvas con la identidad del titular del token (§1.1, A-142) y esa escritura es la única del sistema que un docente no puede deshacer desde la aplicación. La otra configuración —ayudantes que publican lo suyo— **es igual de legítima y se habilita con un clic**, marcando `nota.publicar` al invitar o después. La aplicación soporta las dos; la que viene marcada es la que menos daño hace si nadie revisa el formulario.

**Dos permisos no aparecen en esta tabla porque no son permisos:** ver y cambiar **la propia** suscripción al informe (**R2.6.3**) y editar el **propio** perfil. Son acciones sobre uno mismo, disponibles para todo miembro activo del curso con `curso.ver`, y viven fuera de `/cursos/{id}/ajustes` precisamente por eso (A-132, A-151, A-165).

Sirve a **R2.1.7**, **R2.1.8**, **R2.7.1**, **R2.7.2**, **R2.7.6**, **R2.6.5**, **R2.6.7**.

### A-022 · Cómo se aplica la autorización — ANULADA POR RG-122 y RG-125 en dos puntos

> **Mandan ahora A-179**, que da a la dependencia la firma `requiere(permiso, curso_id, rol_minimo=None)` con una lista cerrada de seis acciones cerradas por rol, y **A-180**, que precisa la cláusula «`correccion.corregir` filtra además por propiedad»: acota **sobre qué filas se puede trabajar**, no qué estado se puede leer. Se conservan íntegras la dependencia única y la acotación por `curso_id` de toda consulta.

Una única dependencia de FastAPI, `requiere(permiso, curso_id)`, resuelve la membresía activa, comprueba el permiso y adjunta el contexto a la petición. **Ninguna ruta de curso se registra sin ella**, y la puerta de CI de A-012 falla la construcción si aparece una. Además:

- **Toda consulta al modelo se filtra por el `curso_id` del contexto.** No existe consulta que reciba un identificador de entidad sin acotar por curso, lo que cierra el acceso indirecto a datos de otro curso.
- `correccion.corregir` filtra además por propiedad: un ayudante sólo ve las filas de `asignacion_correccion` cuyo corrector es él.
- **El frontend oculta lo que el usuario no puede hacer, pero ocultar no es autorizar.** La comprobación real está siempre en el servidor.

### A-023 · Cambio de permisos invalida sesiones en curso

`membresia_curso` lleva una columna `version` que se incrementa en cada cambio de rol o de permisos, en la misma transacción que el cambio.

**La comprobación es por membresía, no por sesión.** La revisión 1 guardaba un escalar `sesion.version_membresias` y lo comparaba contra `membresia_curso.version`, que es **una columna por membresía**: un escalar no puede representar N versiones, y A-020 declara normal que una misma persona sea profesora de un curso y ayudante de otro. Ese mecanismo no sostenía **R2.1.9** y **queda retirado**. En su lugar:

- Existe la tabla **`sesion_membresia (sesion_id, membresia_id, version, refrescada_en)`**, con clave primaria `(sesion_id, membresia_id)`. Al iniciar sesión se escribe una fila por cada membresía activa del usuario, con la versión vigente en ese instante.
- **En cada petición**, la dependencia `requiere(permiso, curso_id)` de A-022 —que ya resuelve la membresía del curso del contexto— comprueba en el mismo `SELECT` que `sesion_membresia.version = membresia_curso.version` **para esa membresía**. Si difieren, la sesión **no se destruye entera**: se recarga la fila desde `membresia_curso`, se aplican los permisos nuevos y, si la membresía pasó a `RETIRADA`, se deniega el acceso a **ese** curso con `403` y un mensaje explícito. El acceso del usuario a **sus otros cursos no se toca**, que es lo correcto y lo que el escalar hacía imposible.
- **Una membresía nueva** (aceptar una invitación con la sesión ya abierta) inserta su fila en la primera petición que toque ese curso.
- El coste es cero llamadas extra: es el mismo `JOIN` que la autorización ya hacía.

Un permiso retirado surte efecto **de inmediato**, no en el próximo inicio de sesión. **La regla es verificable**: hay una prueba automatizada que abre dos sesiones del mismo usuario en dos cursos, retira la de uno y comprueba que la otra sigue funcionando.

### A-024 · Incorporación de profesores y ayudantes: por invitación, nunca por búsqueda

**R2.1.7** y **R2.1.8** se implementan escribiendo una dirección `gmail.com` y enviando un **enlace de un solo uso con caducidad de 7 días**. Motivo: no existe directorio de usuarios que consultar, y buscar por correo entre los usuarios registrados filtraría quién usa la aplicación. La invitación vive en `invitacion_equipo` con estado y actor, y puede revocarse antes de aceptarse.

### A-025 · Retiro de un ayudante: baja lógica, nunca borrado — ANULADA POR RG-136 y RG-139 en su punto 6

> **Manda ahora A-188.** La revocación en GitHub no son dos planos sino **tres** —equipo, colaborador y membresía de la organización cuando la aplicación la dio—, y el retiro de un **profesor** arrastra además sus credenciales de Canvas de ese curso a `RETIRADA`. Los cinco primeros puntos de esta decisión se conservan sin cambio.

**R2.1.9** se implementa como una transacción que:

1. Pasa `membresia_curso.estado` a `RETIRADA`, con `retirada_en` y `retirada_por`.
2. Incrementa `version`, lo que **revoca sus sesiones de ese curso de inmediato** (A-023).
3. Vacía sus permisos.
4. Deja sus asignaciones de corrección pendientes en estado `SIN_CORRECTOR`, con una incidencia visible para que un profesor las reasigne.
5. **Conserva íntegra la autoría de lo que ya corrigió y publicó.**

No se borra la fila y no se borran sus asignaciones. Borrarlas perdería la trazabilidad de quién corrigió qué, que es justamente lo que hace defendible el sistema en una revisión de código y en la actividad individual del 7 de octubre.

6. **Se le retira el acceso de lectura a los repositorios del curso en GitHub** (A-163): sale del equipo `docentes`, o —si el curso opera por la vía de respaldo— se encola `revocar_acceso_docente`. **R2.1.9 no está cumplido si la persona retirada sigue pudiendo leer el código de los estudiantes.**

### A-165 · Administrar usuarios: qué significa y dónde se hace (R2.1.1) — ANULADA POR RG-001, RG-133 y RG-139 en dos filas

> **Mandan ahora A-185 y A-186** sobre el Plano 2, que gana el bloque «Mi cuenta de GitHub» con la declaración de la cuenta, su consentimiento fechado y su desvinculación; y **A-188** sobre la fila «Retirar a un profesor», que arrastra sus credenciales de Canvas y puede dejar el curso en `CANVAS_DESVINCULADO`. Todo lo demás de esta decisión se conserva íntegro, incluido el invariante del último profesor.

**R2.1.1** dice «crear **y administrar** usuarios de tipo profesor». La revisión 1 cubría la creación (A-018) y la incorporación por invitación (A-024) y **no tenía ninguna pantalla que administrara nada**: `usuario.activo` existía en el modelo y no lo tocaba nadie, no había desactivación, ni edición, ni listado. Por §4 del enunciado —que este documento cita como propia en A-151 regla 1— **la mitad «administrar» del requisito no se cumplía**. Queda cubierta aquí, en dos planos, porque en esta aplicación no existe un administrador global (A-017, A-020) y no se va a inventar uno.

**Plano 1 — Administración de los miembros de un curso, en `/cursos/{id}/equipo`.** Con `equipo.administrar`, que sólo tiene un profesor:

| Acción | Alcance | Regla |
|---|---|---|
| **Listar** todos los profesores y ayudantes con rol, permisos, estado, fecha de alta y último acceso | Lectura con `curso.ver` | Es información de coordinación |
| **Incorporar** por invitación nominal (A-024) | Profesor o ayudante | Con los permisos precargados y editables de A-021 |
| **Editar los permisos** de un ayudante | Los siete configurables | Surte efecto **de inmediato** (A-023). Queda en `bitacora` |
| **Cambiar el rol** de un miembro | Ayudante ⇄ profesor | Promover a profesor concede los nueve permisos; degradar a ayudante exige elegir el subconjunto. **Nunca en silencio** |
| **Retirar** a un ayudante | **R2.1.9** | Íntegramente A-025 |
| **Retirar a un profesor** | **R2.1.7** simétrico | Mismo procedimiento que A-025. **Invariante duro: un curso `ACTIVO` conserva siempre al menos un profesor `ACTIVO`.** La acción se rechaza si es el último, con el mensaje «promueve antes a otro profesor». La revisión 1 no contemplaba retirar a un profesor y A-020 declara que los profesores no tienen jerarquía entre sí: entonces cualquiera puede retirar a cualquiera, **salvo al último** |
| **Reincorporar** a alguien retirado | Reactiva la misma `membresia_curso` | Conserva su historial y su autoría (A-025). No se crea una fila nueva |
| **Revocar una invitación** pendiente | Antes de aceptarse | `invitacion_equipo.estado = REVOCADA`, con actor y fecha |
| **Ver el historial** de cambios de equipo | Lectura de `bitacora` filtrada | Responde «¿quién le dio ese permiso y cuándo?» |

**Plano 2 — Administración de la propia cuenta, en `/perfil`.** Sin permiso, para todo usuario con sesión:

- **Editar** nombre visible. El correo **no es editable**: es la identidad de Google y la clave de `usuario` (A-075).
- **Ver y desvincular** sus identidades de Canvas por instancia (`identidad_canvas_usuario`, A-033).
- **Ver sus sesiones abiertas** y cerrarlas todas.
- **Cerrar su cuenta**, que es lo que da semántica a `usuario.activo`, columna que hasta ahora no tocaba nadie:

> **`usuario.activo = false` significa «esta persona cerró su cuenta» y sólo lo escribe su propio dueño**, desde `/perfil`, con confirmación. Efectos: se revocan todas sus sesiones, sus membresías activas pasan a `RETIRADA` con el procedimiento completo de A-025 —incluida la revocación del acceso en GitHub—, y **no puede volver a iniciar sesión**. **No se borra la fila** (A-030): su autoría, sus correcciones publicadas y su bitácora se conservan íntegras, y la interfaz lo muestra como «cuenta cerrada» donde aparezca. **Un profesor no puede cerrar la cuenta de otro**: lo que puede es retirarlo de **su** curso, que es su ámbito legítimo. Cerrar cuentas ajenas requeriría un rol de administrador global que esta aplicación no tiene y que el enunciado no pide.

**Por qué no hay un administrador global de la aplicación.** Sería la lectura más literal de «administrar usuarios de tipo profesor», y **se descarta a propósito**: el enunciado dice que la aplicación se organiza «en torno a cursos administrados por profesores» (§2.1), no en torno a una consola de administración; A-017 restringe los usuarios al equipo docente de algún curso; y un rol capaz de entrar a todos los cursos sería el mayor agujero de privacidad del sistema, sobre datos de estudiantes reales. **La administración es por curso, la ejerce cualquier profesor de ese curso, y cada persona administra su propia cuenta.** Con eso, «crear y administrar usuarios de tipo profesor» está cubierto entero y con pantalla, que es lo que §4 exige.

### A-166 · Cómo entra el evaluador a la entrega (§3.1 y §3.2) — ANULADA POR RG-121 y RG-140 en sus puntos 2 y 6

> **Mandan ahora A-178** —al evaluador se le conceden **los cinco permisos concedibles**, no «los siete configurables», expresión que queda prohibida— y **A-189**, que somete la cuenta compartida del punto 6 a un régimen de custodia con doble factor, marca visible y retirada en tres actos. Los puntos 1, 3, 4, 5 y 7 se conservan íntegros.

El enunciado exige entregar «un link para acceder a su entrega **y que ésta pueda ser utilizada por ayudantes y el profesor**» (§3.1), y una URL utilizable durante dos semanas (§3.2). **La revisión 1 no decidía cómo entra el evaluador**, y sus propias reglas cerraban todas las puertas: A-017 prohíbe cualquier cuenta que no sea profesor o ayudante de un curso, A-018 **rechaza todo correo con reclamación `hd`** —es decir, la cuenta institucional del evaluador— y A-024 exige invitación nominal a una dirección `gmail.com`. **Un link que no se puede usar no cumple §3.1.** Decisión:

1. **El profesor y los ayudantes del ramo se incorporan como AYUDANTES del curso de demostración**, por el mismo camino que cualquier otro miembro: invitación nominal de A-024 a una dirección **`gmail.com`** que **se les solicita por adelantado**, por escrito y con acuse, **antes del 14 de septiembre** para la parcial y **antes del 2 de octubre** para la final.
2. **Se les concede el conjunto completo de permisos concedibles a un ayudante** —los siete configurables— para que puedan recorrer la aplicación entera sin tropezar con un `403`. Los dos NO CONCEDIBLES (`curso.administrar`, `equipo.administrar`) **siguen sin concederse**, porque dan acceso a la credencial de Canvas del profesor titular y a la escalada de privilegios; **se les explica por escrito en la entrega**, junto con lo que sí pueden hacer.
3. **Además se les incorpora al equipo `docentes` de GitHub** (A-163), para que los enlaces a los repositorios de **R2.4.8** y **R2.7.4** les abran. Sin este paso verían `404` y concluirían, con razón, que el requisito no está.
4. **Se prepara un segundo curso de demostración** en el que el evaluador figura como **profesor**, con datos sintéticos y su propia organización de GitHub (A-027), para que pueda recorrer también el asistente de vinculación, la administración de equipo y los ajustes. **No necesita token de Canvas propio**: ese curso queda en estado `BORRADOR`/`VINCULANDO`, que es exactamente lo que hace falta para evaluar la guía de **R2.1.6**, y la entrega lo dice.
5. **El texto de la entrega por Canvas incluye, literalmente:** la URL de la aplicación, la instrucción de indicar una dirección `gmail.com` para recibir la invitación, el nombre del curso de demostración, un recorrido sugerido de cinco minutos, y la advertencia de que **el registro exige una cuenta `gmail.com` porque lo exige R2.1.2 del propio enunciado** —una cuenta institucional será rechazada, y eso es cumplimiento, no un fallo—.
6. **Si el evaluador prefiere no dar una dirección `gmail.com`**, la entrega ofrece la alternativa preparada: **una cuenta `gmail.com` creada por el equipo para la evaluación**, con sus credenciales entregadas por Canvas, ya incorporada al curso y al equipo de GitHub. **Es una vía de acceso, no un usuario compartido**: se declara como tal, se registra en `bitacora` y se retira el 1 de noviembre.
7. **Vigencia:** los accesos del evaluador se mantienen **hasta el 31 de octubre inclusive** (A-161), y su retirada está en el calendario del equipo, no en la memoria de nadie.

### A-026 · Un curso pertenece a la aplicación, no a Canvas

`curso` es una entidad propia con nombre, código, período y zona horaria. Se **vincula** a un curso de Canvas (**R2.1.4**) y a una organización de GitHub (**R2.1.5**), pero existe antes de ambos vínculos y sobrevive a que uno se rompa. Estado de vinculación explícito: `BORRADOR` → `VINCULANDO` → `ACTIVO`, con los estados laterales `CANVAS_DESVINCULADO`, `GITHUB_DESVINCULADO` y `ARCHIVADO`.

### A-027 · Un curso de Canvas se vincula una sola vez, y una organización de GitHub pertenece a un solo curso

Dos unicidades, y **las dos apuntan en la misma dirección**:

- Unicidad `(canvas_base_url, canvas_course_id)` en `curso`. Dos cursos de la aplicación no pueden apuntar al mismo curso de Canvas: produciría dos rosters, dos conjuntos de repositorios y dos verdades.
- **Unicidad `github_org_id` en `curso`, donde no es nulo: una organización de GitHub pertenece a exactamente un curso de la aplicación.**

**La revisión 1 afirmaba lo contrario** («la organización sí puede compartirse entre cursos») y esa frase **queda retirada**, porque era incompatible con las otras dos decisiones del propio documento: una GitHub App tiene **una sola instalación por organización**, de modo que dos cursos que compartieran organización compartirían `installation_id`, y tanto A-028 (`github_installation_id` único) como A-075 (`instalacion_github.curso_id` único) lo prohíben. De las tres frases, la que cede es la que no estaba respaldada por ninguna restricción de base de datos.

**Qué se gana y qué cuesta.** Se gana coherencia con el modelo real de GitHub Apps, un espacio de nombres de repositorios que pertenece a un solo curso, y que el `installation_id` identifique sin ambigüedad al curso al recibir un webhook. Cuesta que un equipo docente con dos secciones creadas como dos cursos distintos en Canvas necesite **dos organizaciones gratuitas**, que se crean en dos minutos y no cuestan dinero. Es un coste aceptable frente a un modelo que no cierra.

**Consecuencia sobre el nombre del repositorio:** con una organización por curso, el nombre ya no tiene que desambiguar entre cursos dentro de una misma organización. Aun así **A-107 usa `curso.slug`, que es único globalmente**, y no `<codigo>-<periodo>`, que no lo es: cinturón y tirantes, porque el coste es cero y el fallo que evita —adoptar el repositorio de otro curso— es de los caros.

### A-028 · Unicidad de la instalación de GitHub

`github_installation_id` es único donde no es nulo: una instalación de la App en una organización pertenece a un solo curso de la aplicación en cada momento, **lo que es exactamente la misma regla que A-027 vista desde el otro lado**. Si se reinstala, el `installation_id` nuevo sustituye al anterior y el hecho queda en `bitacora`. Si un profesor intenta instalar la App en una organización ya vinculada a otro curso, **la vinculación se rechaza en el paso 3 del asistente** con el nombre del curso que ya la ocupa, en lugar de crear la segunda verdad.

### A-029 · Auditoría de toda acción con consecuencia — ANULADA POR RG-043, RG-044, RG-206 y RG-142 en su falta de catálogo

> **Mandan ahora A-184**, que cierra los catálogos de `bitacora.accion` y de `bitacora.entidad` y los defiende con `CHECK` y con prueba de arquitectura, y **A-183**, que fija dónde vive el rastro de una autorización denegada y añade `permiso_exigido`, `ruta` y `metodo`. El carácter *append-only* y el alcance «toda acción con consecuencia» se conservan enteros.

`bitacora` es *append-only* y registra **quién, cuándo, contra qué sistema, con qué resultado**: cambios de permisos, retiros, ediciones de mapeo, creación y borrado de archivos del repositorio base, publicaciones de nota, envíos, y toda escritura externa. Es lo que permite responder el 7 de octubre a «¿cómo saben que ese mensaje se envió?» sin abrir Canvas.

### A-030 · La aplicación no borra datos propios de dominio — ANULADA POR RG-191 en su lista de eliminaciones

> **Manda ahora A-190.** La regla dura y la frase final se conservan enteras; lo que queda superado es el número: la lista cerrada pasa de **seis a nueve** eliminaciones externas, y las tres nuevas son retiradas de permiso en GitHub, no datos de dominio.

**El título de la revisión 1 era «la aplicación no borra nada» y era falso**: el propio documento describía cuatro eliminaciones externas legítimas. Un agente que tomara aquella frase al pie de la letra —y este documento le ordena tomarla al pie de la letra— se habría negado a implementarlas. La regla correcta, y la que manda, es ésta:

**Regla dura.** Retiros, bajas, conflictos, salidas de alcance y correcciones se modelan **con estado, nunca con `DELETE`**, sobre los datos de dominio de la aplicación. Un estudiante retirado conserva su repositorio, su historia y sus versiones capturadas, marcado como `RETIRADO`. Nunca se borra una fila de `commit`, `version_entrega`, `bitacora`, `publicacion_nota`, `mapeo_github`, `correccion` ni `incidencia`.

**Lista cerrada de eliminaciones que la aplicación SÍ realiza.** Ninguna otra, y añadir una es una decisión que se registra aquí:

| Qué se borra | Dónde | Decisión | Por qué es legítimo |
|---|---|---|---|
| El anuncio de verificación `[verificación app]` | Canvas | **A-042** | Es un artefacto que la propia aplicación acaba de crear para probar la escritura; dejarlo sería ensuciar el curso del profesor. Su limpieza diaria existe por si el proceso muere entre crear y borrar |
| Archivos del **repositorio base** | GitHub | **A-067** | **R2.3.6** dice literalmente «incorporar y administrar los archivos iniciales». Administrar incluye borrar, y el repositorio base es material del profesor, no trabajo de un estudiante |
| Una invitación de colaborador **caducada** (`expired = true`) | GitHub | **A-100** paso 3 | Es el único camino documentado para reemitirla. **Nunca a ciegas**: sólo tras comprobar que el estudiante no entró ya y que la invitación está efectivamente caducada |
| El **cuerpo** de un `evento_webhook` antiguo | Base propia | **A-113** | Es carga bruta ya procesada, no evidencia. **La cabecera se conserva indefinidamente**, de modo que la trazabilidad de qué llegó y cuándo sobrevive |
| Trabajos terminados y filas de `sincronizacion` vencidas | Base propia | **A-113** | Telemetría operativa con retención declarada |

**Nunca se borra un repositorio de un estudiante, ni sus commits, ni un tag de entrega, ni una nota publicada, bajo ninguna circunstancia y por ninguna vía de la aplicación.** Ésa es la frase que la revisión 1 quería escribir.

### A-178 · Aritmética de los nueve permisos: siete configurables, cinco concedibles

**Precisa A-021 y corrige el punto 2 de A-166.** Los **nueve permisos** de A-021 se descomponen así, y la descomposición es normativa:

- **Dos implícitos e irrevocables** mientras la membresía esté activa: `curso.ver` y `correccion.corregir`. **Nunca se persisten** en `membresia_curso.permisos` ni en `invitacion_equipo.permisos`.
- **Siete configurables**, que son los únicos valores que el array admite: `curso.administrar`, `equipo.administrar`, `tarea.administrar`, `mapeo.editar`, `correccion.asignar`, `nota.publicar`, `comunicacion.enviar`.
- De los siete configurables, **cinco son concedibles a un ayudante** —`tarea.administrar`, `mapeo.editar`, `correccion.asignar`, `nota.publicar`, `comunicacion.enviar`— y **dos son NO CONCEDIBLES**: `curso.administrar` y `equipo.administrar`.

> **La expresión «los siete permisos concedibles» queda prohibida** en la especificación, en la interfaz, en los correos y en el texto de la entrega. Se escribe **«los cinco concedibles»** o **«los siete configurables»**, que son cosas distintas.

**Interfaz.** El formulario de permisos de `/cursos/{id}/equipo` y el de invitación de A-024 muestran **las siete casillas configurables**: las cinco concedibles editables; las dos NO CONCEDIBLES **deshabilitadas con el motivo escrito en el propio control** —«da acceso a la credencial de Canvas del curso» y «permitiría concederse a sí mismo el resto»—; y los dos implícitos marcados y fijos con la nota «siempre incluidos». **Ningún conjunto preparado contiene una NO CONCEDIBLE**: el tercero se llama **«Gestión completa (los cinco concedibles)»**.

**Servidor.** Se rechaza con **`422`** todo array de permisos de una `membresia_curso` o de una `invitacion_equipo` de rol `AYUDANTE` que contenga `curso.administrar` o `equipo.administrar`, en `PATCH /api/cursos/{id}/miembros/{membresia_id}/permisos`, en `PATCH .../rol` y en `POST /api/cursos/{id}/equipo/invitaciones`. Hay una prueba automatizada que lo intenta y espera `422`.

**Al evaluador (A-166 punto 2) se le conceden exactamente esos cinco**, y la entrega explica por escrito qué puede hacer con ellos y qué no.

Sirve a **R2.1.7**, **R2.1.8**, **R2.1.9**, §3.1 y §3.2.

### A-179 · `ACCIONES_SOLO_PROFESOR`: las seis acciones que se cierran por ROL

La dependencia de autorización pasa a ser **`requiere(permiso, curso_id, rol_minimo=None)`**. El valor `rol_minimo='PROFESOR'` se usa en **exactamente seis acciones y ninguna más**, enumeradas en la constante **`ACCIONES_SOLO_PROFESOR`** de un único módulo:

| # | Acción | Permiso que exige además |
|---|---|---|
| 1 | Confirmar `POSIBLE_FUSION_CANVAS` (A-051) | `mapeo.editar` |
| 2 | **Recapturar una versión con otra fecha de corte** (`origen_captura = MANUAL_FECHA`) | `tarea.administrar` |
| 3 | **Fijar una versión en un SHA concreto** (`origen_captura = MANUAL_SHA`) | `tarea.administrar` |
| 4 | **Archivar y desarchivar los repositorios de una tarea** (A-168, A-197) | `tarea.administrar` |
| 5 | Entrar a `/operacion`, a `/operacion/invariantes` y a todo `/api/operacion/**` | — |
| 6 | Salir de `MODO_RECUPERACION` | — |

**«Capturar ahora» sin cambiar la fecha de corte NO está en la lista**: es `tarea.administrar`, y un ayudante con ese permiso puede hacerlo.

> **Ninguna otra ruta, servicio o consulta lee `membresia_curso.rol` para decidir si una acción procede.** La puerta 2 de A-174 falla la construcción si aparece una lectura de `rol` con efecto de autorización fuera de `requiere(...)`.

**La lista es invariante respecto del perfil de alcance.** Las acciones 1, 2 y 3 pertenecen a funciones que sólo se registran al retirar sus banderas (A-233); bajo `PERFIL_ALCANCE=parcial` esas rutas **no están en el enrutador**, y la constante no cambia por ello. Una acción de la lista que no esté registrada **no** incumple la lista; una acción registrada que exija rol sin figurar en ella **sí** la incumple.

**Archivar, con su fecha de nacimiento escrita.** `POST /api/cursos/{id}/tareas/{id}/archivar` y `.../desarchivar` **no están registrados bajo `parcial`** y responden `404` de enrutado hasta el **30 de septiembre a las 20:00**. Desde entonces, un ayudante con `tarea.administrar` ve el control **deshabilitado con el motivo escrito** —«archivar los repositorios de la tarea es una acción reservada a un profesor del curso»— y una llamada directa recibe `403` con código `PERMISO_INSUFICIENTE`. Un mismo control **no puede estar a la vez «no registrado» y «presente y deshabilitado»**: manda la capa de alcance mientras la bandera vive, y la restricción de rol desde el instante en que el control existe.

Sirve a **R2.1.7**, **R2.1.8**, **R2.2.4**, **R2.4.5**, **R2.4.7**.

### A-180 · La cláusula de propiedad de A-022 acota el TRABAJO, no la LECTURA

**Precisa la tercera viñeta de A-022.** «`correccion.corregir` filtra además por propiedad» significa **sobre qué filas se puede trabajar**, y no qué estado se puede leer.

**Se lee con `curso.ver`** —implícito e irrevocable para todo miembro activo— la **matriz nominal completa** del estado de corrección de una tarea: sujeto, entrega, corrector asignado, estado de corrección, versión vigente y si está publicada. Con el mismo permiso se leen los tres agregados (por corrector, por sección y por entrega), el doble contador «N de M corregidas en la aplicación · K de M con nota en Canvas · comprobado hace X», los filtros —incluido el filtro por corrector— y la exportación a CSV de lo que se está viendo.

**Queda acotado por propiedad, y sólo esto:** abrir la corrección **en modo edición** y guardar borrador; ver el **borrador** de otro corrector —nota local, rúbrica local, comentario sin publicar—; y ver sus **notas internas y banderas**. La pestaña «Repartir» exige `correccion.asignar`; publicar exige `nota.publicar`.

La pestaña de estado se llama **«Estado de la entrega»**, es **siempre visible** para todo miembro activo, y **sobre una fila ajena el botón principal es «ver», no «corregir»**.

**En la capa de repositorio**, el filtro `sólo_propias` se aplica **únicamente** a las rutas de escritura de corrección y a la lectura de `correccion.borrador`, `correccion.notas_internas` y `correccion.banderas`. `GET /api/cursos/{curso_id}/tareas/{tarea_id}/correccion/estado` se registra con `requiere('curso.ver', curso_id)` y devuelve la matriz nominal completa, los tres agregados y los dos contadores en una sola respuesta, con `curso_id` en el `WHERE`.

Sirve a **R2.7.7**, **R2.7.1**, **R2.7.2**, **R2.7.5**.

### A-181 · El catálogo de permisos, defendido también en la base, y diecisiete invariantes

**Cinturón y tirantes**, el mismo patrón que A-075 aplica a la regla de `gmail.com`. `membresia_curso.permisos` e `invitacion_equipo.permisos` (`text[]`) llevan **cuatro `CHECK`**, todos en la migración inicial (A-175):

1. Los elementos del array se restringen a **los siete nombres configurables** de A-178. Los dos implícitos **nunca se persisten**.
2. Se prohíbe `curso.administrar` y `equipo.administrar` cuando `rol = 'AYUDANTE'`, en las dos tablas.
3. Se exige `permisos = '{}'` cuando `rol = 'PROFESOR'`: el profesor tiene los nueve de forma implícita e irrevocable, y su array se guarda **vacío** para que no exista un segundo lugar donde contradecir la tabla. **La aplicación nunca lee `permisos` de una membresía de rol `PROFESOR`.**
4. Se prohíbe `NULL` dentro del array, y toda escritura usa valores distintos.

**`verificar_invariantes` pasa de 14 a 17.** Los tres nuevos son **bloqueantes** y los tres **listan y no auto-reparan**:

| # | Invariante | Por qué no se auto-repara |
|---|---|---|
| 15 | Todo curso `ACTIVO` conserva al menos una `membresia_curso` `ACTIVA` de rol `PROFESOR` | Promover a alguien es una decisión de personas |
| 16 | Ninguna `membresia_curso` ni `invitacion_equipo` de rol `AYUDANTE` contiene un permiso NO CONCEDIBLE | Vaciar permisos a mano sería decidir por un profesor |
| 17 | Ninguna cuenta de GitHub enlazada desde `usuario.cuenta_github_id` tiene un `mapeo_github` `VIGENTE` en ningún curso (A-187) | Invalidar el mapeo de un estudiante sin que un docente lo decida le quitaría el repositorio a quien no hizo nada |

Las violaciones se escriben en `resultado_invariante` y su fila de `/operacion/invariantes` queda **acotada por A-232**. Hay pruebas que intentan cada violación **contra la base directamente** y esperan el error de la restricción.

Sirve a **R2.1.7**, **R2.1.8**, **R2.1.9**.

### A-182 · Lista cerrada de dieciséis rutas sin sesión, cada una con su autorización y su limitador

**El receptor de webhooks no es el único endpoint sin autenticación de usuario**, y afirmarlo era falso. Ésta es la superficie sin sesión completa; **ninguna otra ruta puede quedar fuera de `requiere(...)` sin figurar aquí**:

| Ruta | Qué la autoriza | Límite |
|---|---|---|
| `POST /webhooks/github` | firma `X-Hub-Signature-256` sobre el cuerpo crudo, en tiempo constante | 600/min por `installation_id`, contado **después** de validar la firma |
| `GET` y `POST /auth/google/inicio` | ninguna: inicia el flujo OIDC | 30/min por IP truncada |
| `GET /auth/google/callback` | `state` firmado de un solo uso y cookie `oidc_txn` | 30/min por IP truncada |
| `GET` y `POST /auth/confirmar` | camino degradado de A-018 regla 3, con token anti-CSRF de formulario | 30/min por IP truncada |
| `GET /github/instalacion/callback` | `state` firmado de A-058 | 30/min por IP truncada |
| `GET` y `POST /baja/{token}` | firma del token y alcance `(curso_id, usuario_id)` | 20/min por IP truncada |
| `GET /r/{t}` | firma del token de traza | 60/min por IP truncada |
| `GET /api/invitaciones/{token}` | hash del token; devuelve el correo destinatario **enmascarado** | 20/min por IP truncada |
| `POST /api/invitaciones/{token}/aceptar` | hash del token más coincidencia con `id_token.email` | 20/min por IP truncada |
| `/invitaciones/{token}` (página) | ninguna: pinta lo que devuelve `GET /api/invitaciones/{token}` | 60/min por IP truncada |
| `GET /api/capacidades` | ninguna: devuelve sólo el perfil de alcance y las banderas activas | 60/min por IP truncada |
| `/alcance` | ninguna: publica la tabla de A-157 (A-234) | 60/min por IP truncada |
| `/privacidad` | ninguna | 60/min por IP truncada |
| `GET /salud` | ninguna; no toca la base de datos | sin límite |
| `GET /estado` (forma anónima) | ninguna | 20/min por IP truncada |
| `POST /interno/latido` | HMAC del vigilante externo (A-112) | 12/min por token del vigilante |

**Son dieciséis.** Todo lo demás bajo `/api/**` exige sesión, con 300/min por `sesion_id`. Se registran en un **router público único**, fuera del middleware de sesión y de CSRF, con la dependencia `limitar(clave, limite)` sobre la tabla `cubo_tasa`.

**`GET /estado` tiene dos respuestas, no una:** la **anónima**, con booleanos y contadores agregados y **sin un solo nombre ni identificador de curso**, que es la que consultan los monitores externos; y la **completa**, con desglose por curso, que exige sesión y queda acotada por A-232.

**El registro efectivo se evalúa por perfil de alcance, y las dos listas se cruzan así:**

- **`GET` y `POST /baja/{token}` siguen a la bandera `mis_notificaciones`**: bajo `parcial` no están registradas y responden `404` de enrutado; nacen el **3 de octubre a las 12:00**. Es coherente porque bajo `parcial` **no se emite ningún token de baja**: los únicos correos de ese período son las alertas operativas de A-177, que son transaccionales, **no suscribibles**, y **no llevan enlace de baja ni cabecera `List-Unsubscribe`**. La plantilla del informe diario sí las lleva, junto con `List-Unsubscribe-Post`.
- **`GET /r/{t}` está registrada en los dos perfiles** y no depende de ninguna bandera: es un resolvedor de enlaces ya emitidos y su ausencia rompería un enlace vivo.
- **Las otras catorce están registradas en los dos perfiles.**

**El token de baja**, que es el único de estos que modifica estado: HMAC-SHA256 sobre `SIGNING_KEY`, verificado en tiempo constante, con `payload = {curso_id, usuario_id, generacion_enlaces, emitido_en, expira_en, jti}`. **No es un JWT genérico** y no se acepta ningún algoritmo declarado por el propio token. **Caducidad de 90 días, reutilizable**, la misma cifra que los tokens de traza. Rutas `GET /baja/{token}` y `POST /baja/{token}`, con la re-suscripción en `POST /baja/{token}?accion=alta`; **`/informes/baja/{token}` y `/informes/alta/{token}` no existen**, y el `GET` **no modifica nada**, con prueba automatizada que lo comprueba. Revocación en bloque con `usuario.generacion_enlaces`, que incrementa «regenerar mis enlaces de baja» de `/perfil`. **CSRF:** el endpoint no está autenticado por cookie, de modo que el doble envío de A-009 no aplica; su autorización es la firma y el alcance, y **se aceptan las dos entradas de `POST`** —el formulario servido en nuestro origen y el clic de un solo paso del cliente de correo por RFC 8058—, con el mismo efecto y la misma página de confirmación en español.

Sirve a **R2.1.2**, **R2.1.7**, **R2.5.2**, **R2.6.3**, **R2.6.4**, **R2.3.9**, **R2.3.11**, §3.2.

### A-183 · Dónde vive el rastro de una autorización denegada

**Dos destinos, sin zona intermedia sin decidir**, resueltos por un manejador central de `403` y `404` con el mismo contexto que ya resolvió `requiere(...)`:

1. **`bitacora`** — un `403` sobre una ruta de curso emitido a alguien que **sí** tiene `membresia_curso` `ACTIVA` en ese curso, **vaya la ruta de escritura o de lectura**. Se escribe con actor, `curso_id`, **`permiso_exigido`**, **`ruta`**, **`metodo`** e identificador del recurso, con la acción `AUTORIZACION_DENEGADA` (A-184). Es una acción con consecuencia y con actor identificado (A-029), y es la que responde «¿quién intentó qué y con qué permiso le faltaba?».
2. **Log estructurado de A-015** — un `403` o un `404` emitido a quien **no** tiene membresía activa en ese curso, y todo rechazo previo a la sesión, con `motivo`, `ip_truncada` y, cuando exista, `usuario_id`. **Nunca a `bitacora`** —no hay curso ni actor legítimo— y **nunca con el correo completo** de quien no llegó a ser usuario.

`bitacora` gana `permiso_exigido`, `ruta` y `metodo` en la migración inicial (A-175). Los contadores de esta señal alimentan la quinta alerta de A-177.

Sirve a **R2.1.2**, **R2.1.8**, **R2.1.9**, §3.2.

### A-184 · Catálogos cerrados de `bitacora.accion`, `bitacora.entidad` e `incidencia.sujeto_tipo`

**1 · `bitacora.accion` es un catálogo cerrado**, declarado como enumeración en `backend/app/dominio/bitacora.py` y defendido por un `CHECK` generado desde ella. **Convención: `<ENTIDAD>_<PARTICIPIO>`**, en mayúsculas y en español (A-154); `REVELAR_EMAIL_AUTOR` se normaliza a `EMAIL_AUTOR_REVELADO`.

- **Equipo y permisos:** `INVITACION_EMITIDA`, `INVITACION_ACEPTADA`, `INVITACION_REVOCADA`, `MEMBRESIA_CREADA`, `MEMBRESIA_RETIRADA`, `PERMISOS_CAMBIADOS`, `USUARIO_DESACTIVADO`, **`AUTORIZACION_DENEGADA`**.
- **Curso e integración:** `CURSO_CREADO`, `CURSO_DUPLICADO`, `CURSO_VINCULADO`, `CURSO_ARCHIVADO`, `CREDENCIAL_CANVAS_REGISTRADA`, `CREDENCIAL_CANVAS_RETIRADA`, `INSTALACION_VINCULADA`, `CHECKLIST_EJECUTADO`, `MODO_ESCRITURA_CAMBIADO`, `COMUNICACIONES_SUSPENDIDAS`, `COMUNICACIONES_REANUDADAS`, `ZONA_HORARIA_CAMBIADA`, **`CAPACIDAD_DEGRADADA`**, **`VERIFICACION_FIRMADA_A_MANO`**.
- **Mapeo e identidad:** `MAPEO_CREADO`, `MAPEO_SUPERSEDIDO`, `MAPEO_INVALIDADO`, `IDENTIDAD_GIT_RESUELTA`, `IDENTIDAD_GIT_SUPERSEDIDA`, `EMAIL_AUTOR_REVELADO`, `CUENTA_GITHUB_DOCENTE_VINCULADA`, `CUENTA_GITHUB_DOCENTE_DESVINCULADA`, **`CUENTA_GITHUB_RECHAZADA`**, **`INVITACION_ORG_REENVIADA`**.
- **Tareas, entregas y repositorios:** `TAREA_CREADA`, **`TAREA_ARCHIVADA`**, `ENTREGA_VINCULADA`, `ENTREGA_EXCLUIDA`, `ENTREGA_REVINCULADA`, `REPOSITORIO_CREADO`, `REPOSITORIO_ADOPTADO`, `REPOSITORIO_ARCHIVADO`, **`REPOSITORIO_DESARCHIVADO`**, `REPOSITORIO_SUSTITUIDO`, `ARCHIVO_BASE_SUBIDO`, `ARCHIVO_BASE_BORRADO`, `ACCESO_CONCEDIDO`, `ACCESO_REVOCACION_PROPUESTA`, `ACCESO_REVOCACION_PROGRAMADA`, `ACCESO_REVOCADO`, `ACCESO_MANTENIDO`.
- **Versiones y corrección:** `VERSION_CAPTURADA`, `VERSION_ABIERTA`, `VERSION_RECAPTURADA`, `CORRECTOR_ASIGNADO`, `NOTA_PUBLICADA`, `NOTA_DISPENSADA`, `CALIFICADA_SIN_CODIGO`.
- **Comunicación e incidencias:** `MENSAJE_ENCOLADO`, `MENSAJE_ENVIADO`, `MENSAJE_DESCARTADO`, `REGLA_COMUNICACION_CAMBIADA`, `SUSCRIPCION_CAMBIADA`, **`ENLACES_BAJA_REGENERADOS`**, `INCIDENCIA_SILENCIADA`, `INCIDENCIA_RESUELTA`.

**2 · `bitacora.entidad` es el nombre de la tabla tal como aparece en el censo de A-198**, en `snake_case` singular, más el valor `sistema`.

**3 · `incidencia.sujeto_tipo` es un catálogo cerrado**: `{CURSO, TAREA, ENTREGA, SUJETO, REPOSITORIO, ESTUDIANTE, GRUPO, MEMBRESIA, VERSION_ENTREGA, CORRECCION, IDENTIDAD_GIT, SISTEMA}`. `SISTEMA` lleva `sujeto_id` nulo, y `curso_id` nulo cuando la incidencia es global.

**4 · Cada tipo de incidencia tiene exactamente un `sujeto_tipo`**, declarado en la tabla de dominio `TIPO_INCIDENCIA → SUJETO_TIPO` de `backend/app/dominio/incidencias.py`. La función `abrir_incidencia(tipo, sujeto_id, …)` **deriva** el `sujeto_tipo` de esa tabla y **no lo acepta como argumento**: es lo que impide que dos llamadas abran dos incidencias del mismo hecho escribiendo un `sujeto_tipo` distinto en cada una y burlando el único parcial de A-087.

**Añadir un valor a cualquiera de los tres catálogos es una decisión que se registra en esta carta.** Tres pruebas de arquitectura fallan la construcción: una escritura a `bitacora` con una `accion` fuera de la enumeración, una `entidad` fuera del censo, y un tipo de incidencia sin fila en la tabla tipo → sujeto.

Sirve a **R2.1.7**, **R2.1.8**, **R2.1.9**, **R2.2.4**, **R2.2.6**, **R2.3.11**, **R2.5.5**, **R2.6.2**, **R2.7.6**.

### A-185 · La cuenta de GitHub del docente es un atributo de la persona; el correo tiene forma canónica

**1 · La cuenta de GitHub del equipo docente vive en `usuario.cuenta_github_id uuid NULL REFERENCES cuenta_github(id) ON DELETE RESTRICT`, con índice único parcial donde no es nulo.** **`membresia_curso.cuenta_github_id` no existe.** La identidad es `github_user_id` (Ley 3, A-074), no cambia al cambiar de curso, y por tanto **la unicidad es global y no por curso**.

- `invitacion_equipo.github_login_declarado text NULL` es un campo **opcional** del formulario de invitación (A-024); la invitación se envía igual si no se conoce.
- Al aceptar, la pantalla de bienvenida lo pide con validación en vivo `GET /users/{login}` (A-089), aplicando A-091: se rechaza si resuelve a una organización, y **se persisten el `github_user_id` numérico y el `login` canónico devueltos por la API**, nunca lo tecleado.
- **Un ayudante que no declara cuenta conserva su membresía activa y no bloquea nada**: ve el texto «necesitas vincular tu cuenta de GitHub para abrir el código» en lugar del enlace.
- La declaración y la desvinculación se hacen en **`/perfil`** (A-165 Plano 2), y quedan en `bitacora` con `CUENTA_GITHUB_DOCENTE_VINCULADA` y `CUENTA_GITHUB_DOCENTE_DESVINCULADA`.

**2 · `email_canonico`, en las dos tablas.** `usuario` conserva `email` (citext, único, con el `CHECK` de `@gmail.com` de A-075 y **R2.1.2**) y `google_sub` (único), y **gana `email_canonico citext NOT NULL UNIQUE`**. `invitacion_equipo` conserva `email` —lo que el profesor escribió— y **gana `email_canonico citext NOT NULL`**; su índice único parcial pasa a ser **`(curso_id, email_canonico) WHERE estado = 'PENDIENTE'`**, y el de `(curso_id, email)` **se retira**.

**Normalización, en este orden y sólo sobre correos ya aceptados por R2.1.2:** minúsculas; `googlemail.com` → `gmail.com`; `email` guarda ese resultado; `email_canonico` guarda además el *local-part* **sin puntos** y **sin sufijo `+etiqueta`**. **Sólo se aplica a `gmail.com` y `googlemail.com`**, que es donde está documentado que puntos y `+etiqueta` enrutan a la misma cuenta. La función vive en `backend/app/dominio/` y **se ejecuta antes del `CHECK` y antes de escribir**. **El emparejamiento de una invitación se hace por `email_canonico`, nunca por la cadena tecleada.**

**Cambio de dirección en Google:** manda `google_sub`; se actualizan `email` y `email_canonico` en la misma transacción y queda en `bitacora`. Si el nuevo `email_canonico` chocara con otro usuario **no se actualiza nada**, se deniega el acceso con mensaje explícito y se abre el caso.

Sirve a **R2.1.1**, **R2.1.2**, **R2.1.7**, **R2.1.8**, **R2.1.9**, **R2.3.9**, **R2.4.8**, **R2.5.10**, **R2.7.4**.

### A-186 · Consentimiento fechado de lectura de todo el código, y `org_github_estado` de cinco valores

**El texto es literal, es el mismo en los tres sitios, y en los dos primeros hay que verlo ANTES de que la acción ocurra:**

> «Al aceptar, tu cuenta de GitHub entrará en la organización **{organización}** y tendrás **lectura de todos los repositorios** de los estudiantes de este curso, no sólo de los que te toque corregir. Ese acceso se retira automáticamente si dejas de ser miembro de este curso.»

1. **Página pública de aceptación `/invitaciones/{token}`**, sobre el botón «Aceptar la invitación», junto al rol y a la lista de permisos que se conceden.
2. **Bloque «Mi cuenta de GitHub» de `/perfil`**, sobre el botón que guarda el `login`, con una **casilla que hay que marcar** para habilitarlo —el mismo patrón que la casilla de A-035 regla 2—. Al marcarla se persiste **`usuario.consentimiento_github_en (timestamptz, nullable)`**.
3. **`/cursos/{id}/equipo`** repite la misma frase como texto permanente bajo la lista de miembros, y el texto de la entrega por Canvas (A-166 punto 5) la incluye entre lo que el evaluador debe saber antes de aceptar.

> **Sin ese consentimiento fechado, `sincronizar_acceso_docente` NO incorpora a esa persona a la organización ni al equipo `docentes`.** Es una guarda, no un aviso.

**`membresia_curso.org_github_estado` toma cinco valores** —`NO_APLICA`, **`SIN_CONSENTIMIENTO`**, `PENDIENTE`, `ACTIVA`, `ERROR`— con doble `CHECK`: `NO_APLICA` **si y sólo si** `usuario.cuenta_github_id` es nulo; `SIN_CONSENTIMIENTO` **si y sólo si** la cuenta está declarada y `consentimiento_github_en` es nulo.

| Valor | Qué muestra la columna GitHub de `/cursos/{id}/equipo` |
|---|---|
| `NO_APLICA` | Enlace a `/perfil` para declarar la cuenta |
| `SIN_CONSENTIMIENTO` | «Pendiente de aceptar la lectura de todo el código del curso», con el enlace al bloque «Mi cuenta de GitHub» y el texto literal |
| `PENDIENTE` | Fecha de la invitación a la organización y botón de reenvío |
| `ACTIVA` | `login` declarado y fecha de la última revalidación |
| `ERROR` | Motivo literal de GitHub y botón «reintentar ahora» |

**Los relojes de reenvío cuelgan de `org_github_invitada_en`, no del alta de la membresía.** Mientras el estado sea `NO_APLICA` o `SIN_CONSENTIMIENTO` **no corre el plazo de cinco días, no se abre `INVITACION_NO_ACEPTADA`, no se reemite nada y no se consume cuota de correo**. Con cuatro valores, una persona que declaró su cuenta y no firmó el consentimiento sólo podía figurar como `NO_APLICA` —y la pantalla le pedía declarar una cuenta que ya declaró— o como `PENDIENTE` —y se mostraba una fecha de invitación inexistente y, cinco días después, se abría una incidencia por una invitación que nunca se envió—. **Las dos lecturas mienten al docente sobre lo que tiene que hacer.**

**Las tres pantallas y la guarda están operativas desde el 16 de septiembre: no llevan bandera** (A-233).

Sirve a **R2.1.7**, **R2.1.8**, **R2.4.8**, **R2.7.4**, §3.1.

### A-187 · Elegibilidad de una cuenta de GitHub, comprobada en toda la aplicación

**Una cuenta de GitHub no puede ser a la vez del equipo docente y de un estudiante**, y la comprobación es **una sola función de dominio**, `es_cuenta_elegible(github_user_id, curso_id) -> motivo | None`, en `backend/app/dominio/elegibilidad.py`.

**Su alcance es toda la aplicación, no el curso.** Rechaza un `github_user_id` que tenga un `mapeo_github` **`VIGENTE` en cualquier curso**, no sólo en los del declarante: un `github_user_id` es global (Ley 3, A-074) y la unicidad de `usuario.cuenta_github_id` también lo es (A-185), de modo que acotar por curso contradice el propio modelo. Si se acotara, **un ayudante podría declarar la cuenta de un estudiante de otro curso y obtener lectura de todos los repositorios de éste**, que es precisamente el riesgo que hay que cerrar.

**Cuenta no elegible es, en lista cerrada:** la cuenta enlazada desde `usuario.cuenta_github_id` de cualquier `membresia_curso` `ACTIVA` de ese curso; cualquier miembro de `equipo_github_curso`; el propietario de la organización; y la cuenta bot de la propia App (A-059).

**Las dos puertas y sus dos desenlaces, que no son el mismo:**

| Puerta | Cuándo | Desenlace |
|---|---|---|
| **Del docente** — `PUT /api/perfil/cuenta-github`, aceptación de invitación, carga manual o importación de un `mapeo_github` hecha por una persona | Hay peticionario | **`422`** con mensaje explícito, **sin persistir nada**, y registro en `bitacora` con `CUENTA_GITHUB_RECHAZADA` |
| **De la ingesta** — recolector de la tarea de registro, CSV, autoservicio del estudiante | No hay petición que rechazar | La fila se persiste con `estado = 'NO_RESUELTO'` y `motivo_invalidacion = 'CUENTA_NO_ELEGIBLE'`, con el texto «esa cuenta pertenece al equipo docente del curso; vuelve a entregar con tu cuenta personal» |

**`PUT /api/perfil/cuenta-github` rechaza además** con el mismo `422` un `github_user_id` ya declarado por otro usuario (índice único parcial de A-185) y uno que no valide contra `GET /users/{login}` o resulte ser una organización según la comparación de A-091.

**Guarda en tiempo de ejecución, no sólo en el formulario.** `sincronizar_acceso_docente` **repite la comprobación inmediatamente antes** de `PUT /orgs/{org}/memberships/{login}` y de `PUT /orgs/{org}/teams/{slug}/memberships/{login}` —lectura antes del efecto, A-115 garantía 3—; si falla, **no llama**, abre la incidencia bloqueante **`CUENTA_DOCENTE_ES_DE_ESTUDIANTE`** con `sujeto_tipo = 'MEMBRESIA'` y avisa por correo a los profesores del curso, con cargo a la reserva operativa de A-177. La prueba automatizada que A-060 promete **se conserva además de la guarda, no en su lugar**.

**Un solo tipo de incidencia para este hecho.** **`GITHUB_DUPLICADO` no se usa aquí**: conserva su significado de A-088 —dos estudiantes reclamando la misma cuenta— y confundirlos haría que Pendientes mezclara un problema del padrón con un problema de acceso del equipo docente. La abre tanto el **invariante 17** de A-181 como la guarda previa a la llamada, y **es la misma fila**.

**No es un `CHECK` de base ni un disparador**: la condición cruza cuatro tablas. Es una comprobación de dominio en las dos puertas, más el invariante nocturno, que **lista y no auto-repara**.

Sirve a **R2.1.7**, **R2.1.8**, **R2.1.9**, **R2.2.4**, **R2.2.5**, **R2.2.6**, **R2.4.8**, **R2.7.4**.

### A-188 · El retiro revoca en tres planos, y arrastra las credenciales de Canvas del profesor

**1 · Tres planos de revocación en GitHub, en este orden, dentro de `revocar_acceso_docente`**, para el retiro de un ayudante o de un profesor (A-025, A-165) y para el cierre de la propia cuenta:

| # | Plano | Llamada | Condición |
|---|---|---|---|
| 1 | **Equipo** (vía principal) | `DELETE /orgs/{org}/teams/{team_slug}/memberships/{login}` | Siempre. Una sola llamada revoca la lectura sobre todos los repositorios concedidos por el equipo |
| 2 | **Colaborador** (vía de respaldo) | `DELETE /repos/{org}/{repo}/collaborators/{login}` | Por **cada** fila de `acceso_docente_repositorio` con `via = COLABORADOR` y `estado = CONCEDIDO` de ese curso: un permiso de colaborador directo **no** se retira al salir de un equipo **[DOC]** (`Q-2.6-56`) |
| 3 | **Membresía de la organización** | `DELETE /orgs/{org}/memberships/{login}` | **Si y sólo si `membresia_curso.org_github_alta_por_app = true`** |

**`membresia_curso.org_github_alta_por_app` (`boolean NOT NULL DEFAULT false`)** se escribe a `true` en la misma transacción en que el `PUT /orgs/{org}/memberships/{login}` del paso 2 de A-163 devuelve éxito, y **nunca** para quien ya era miembro u *owner* de la organización antes. **La aplicación deshace lo que hizo y nada más.**

Cada plano hace su **lectura previa** —`GET /orgs/{org}/teams/{slug}/memberships/{login}`, `GET /repos/{o}/{r}/collaborators/{login}`, `GET /orgs/{org}/memberships/{login}`— para que un reintento sobre algo ya revocado sea un *no-op* (A-115 garantía 3). Agotados los cuatro reintentos, el trabajo queda `REQUIERE_ATENCION` con su error literal, reintentable a mano desde `/operacion`, y se abre la incidencia bloqueante **`ACCESO_DOCENTE_NO_REVOCADO`**. **R2.1.9 no está cumplido si la persona retirada sigue pudiendo leer el código de los estudiantes.**

**2 · Retirar a un profesor arrastra sus credenciales de Canvas.** Todas sus filas de `credencial_canvas` de ese curso pasan a **`RETIRADA` en la misma transacción del retiro**, y se dispara la **promoción automática de A-036**: la siguiente credencial `VALIDA` del orden de respaldo pasa a `orden_respaldo = 0`, respetando el único parcial `curso_id` donde `orden_respaldo = 0`.

**La confirmación nominal previa enumera, además de lo que ya enumera A-165** —sesiones que se cierran, lectura de los N repositorios que se pierde, M entregas que quedan sin corrector, historial que se conserva—, **una frase más, la que corresponda de estas dos**:

- «Esta persona es la titular de la credencial operativa. A partir de ahora la aplicación escribirá en Canvas como *nombre del sucesor*.»
- «Esta persona es la titular de la credencial operativa y **no hay ninguna credencial de respaldo válida**. **Este curso quedará sin poder escribir en Canvas** hasta que un profesor pegue la suya.»

**El retiro no se bloquea por ser el titular de la única credencial**: el único invariante duro es el del último profesor `ACTIVO` (invariante 15 de A-181). Sin respaldo válido, el curso pasa a **`CANVAS_DESVINCULADO`**, se abre `CANVAS_CREDENCIAL_INVALIDA`, se detienen las lecturas de Canvas, **las escrituras se encolan en `ESPERANDO_CREDENCIAL` y no se descartan**, y lo que no depende de Canvas —aprovisionamiento, ingesta de actividad, tableros, timeline y captura de versiones— **sigue funcionando** (A-036 paso 4). Todo queda en `bitacora` con actor, y se avisa por correo a todos los profesores del curso. **La misma regla rige cuando el retiro lo causa el cierre de cuenta del titular.**

**3 · Las cinco piezas de este apartado y de A-187 corren desde el 16 de septiembre y no llevan bandera**: la comprobación de elegibilidad repetida antes de las dos escrituras, la guarda de consentimiento, los tres planos con sus lecturas previas, la escritura de `org_github_alta_por_app` y las dos incidencias con su correo. **Una guarda que llega después que el efecto que guarda no guarda nada**, y el ensayo del 14 de septiembre incluye retirar a un miembro y comprobar que deja de leer el código.

**Criterio verificable, en `docs/criterios/`:** «en el ensayo del 14 de septiembre, retirado un miembro del curso, las tres llamadas de revocación se ejecutan, la lectura previa de cada plano queda en la bitácora del trabajo, y el `login` retirado recibe `404` al abrir un repositorio del curso».

Sirve a **R2.1.4**, **R2.1.7**, **R2.1.9**, **R2.6.5**, **R2.6.6**, **R2.7.6**.

### A-189 · Régimen de custodia de las cuentas compartidas de evaluación

Las dos cuentas `gmail.com` de evaluación —la de A-166 punto 6 y la de reserva— quedan sujetas a este régimen, que no es un conjunto de consejos:

1. **Están en el inventario de A-176**, con **custodio nombrado** —el responsable de infraestructura y su segundo—, viven en la bóveda compartida y tienen **verificación en dos pasos activada en la propia cuenta de Google**.
2. **Reciben exactamente los cinco permisos concedibles de A-178, y ninguno más.**
3. **La aplicación las marca** en `/cursos/{id}/equipo` como **«vía de acceso compartida»**, que es lo que A-166 punto 6 obliga a declarar. La marca vive en **`membresia_curso.es_via_compartida (boolean NOT NULL DEFAULT false)`** y **aparece junto al nombre en toda vista donde la persona figure**.
4. **Su uso queda en `bitacora` como el de cualquier miembro**, y la entrega declara por escrito que **la autoría registrada es la de la cuenta y no la de la persona** que la usó.
5. **Su retirada es el 1 de noviembre** (A-166 punto 7) y consiste en **tres actos, no en uno**: retirar la membresía de cada curso (A-025), sacarla del equipo `docentes` y de la organización por los tres planos de A-188, y **cambiar la contraseña de la cuenta de Google**. **Sin el tercero, la retirada no cierra nada.**
6. **El ejemplar impreso** que se lleva a la demostración **se destruye ese mismo día**, y su existencia queda anotada con fecha en `docs/operacion.md`.

**Qué puede enviar la cuenta compartida con las comunicaciones ya reanudadas** —el 1 de octubre a las 09:00 (A-233)—, bajo cuatro condiciones:

- **El interruptor de curso manda sobre el permiso**: con `curso.comunicaciones_salientes = SUSPENDIDAS` no sale ningún envío, tenga quien lo intente el permiso que tenga (A-225).
- **Todo envío desde una cuenta compartida queda en `bitacora` con la cuenta como actor y con la marca `es_via_compartida`**, y el diálogo previo dice, antes de enviar: «estás enviando desde una vía de acceso compartida; la autoría quedará registrada a nombre de la cuenta».
- **Los topes son los mismos y no se amplían**: 1 recordatorio manual por estudiante y día, 3 por estudiante en total. **Ningún tope se relaja para la demostración.**
- **La retirada del 1 de noviembre revoca también esta capacidad**, por los tres actos del punto 5.

Sirve a **R2.1.2**, **R2.1.8**, **R2.6.5**, **R2.6.6**, **R2.6.7**, §3.1 y §3.2.

### A-190 · La lista cerrada de A-030 pasa de seis a nueve eliminaciones externas

**A-030 dice literalmente que añadir una eliminación es una decisión que se registra en esta carta.** Se registran aquí las tres que faltaban, y **ninguna más**:

| Qué se borra | Dónde | Decisión | Por qué es legítimo |
|---|---|---|---|
| `DELETE /repos/{org}/{repo}/collaborators/{login}` | GitHub | **A-212** (estudiante) y **A-188** plano 2 (docente por vía `COLABORADOR`) | Es un **permiso**, no un dato de dominio; retirarlo es exactamente lo que exigen **R2.1.9** y **R2.3.9** |
| `DELETE /orgs/{org}/teams/{team_slug}/memberships/{login}` | GitHub | **A-188** plano 1 | Retira la lectura del equipo docente sobre todos los repositorios de una vez (A-025 punto 6) |
| `DELETE /orgs/{org}/memberships/{login}` | GitHub | **A-188** plano 3 | Sólo con `membresia_curso.org_github_alta_por_app = true`: la aplicación deshace lo que hizo y nada más |

**Ninguna de las tres toca un dato de dominio.** La prohibición verificable se conserva íntegra: la prueba de arquitectura **sigue fallando la construcción si aparece `DELETE /repos/{owner}/{repo}` en `backend/app/adaptadores/`**, y **nunca se borra un repositorio, un commit, un tag de entrega ni una nota publicada**. La prueba que enumera los `DELETE` permitidos en `adaptadores/` se escribe contra estas **nueve** filas.

Sirve a **R2.1.9**, **R2.3.9**, **R2.3.10**, **R2.4.8**, **R2.7.4**.

---

## 5. Credenciales y su ciclo de vida

### A-031 · Canvas: token de acceso personal del profesor

Es **el mecanismo que se implementa**, por la restricción de §1.1. El profesor lo genera desde su perfil de Canvas y lo pega en el asistente de vinculación.

### A-032 · OAuth2 con Developer Key: camino alternativo, condicionado y preparado

El acceso a Canvas se abstrae tras la interfaz `ProveedorCredencialCanvas`, con dos implementaciones: `TokenPersonal` (la que se despliega y se demuestra) y `OAuth2DeveloperKey` (esqueleto con canje de código y refresco). Si la administración de la universidad concediera una Developer Key institucional, se conmuta por configuración sin tocar el resto del sistema. **El camino OAuth2 es alternativo y condicionado a que la instancia lo permita; ninguna funcionalidad de este documento depende de él.** El equipo escala formalmente y por escrito la solicitud, con fecha límite de respuesta el 12 de septiembre, y registra la respuesta en `docs/`.

### A-033 · Sólo el titular pega su propio token

La documentación de Canvas dice literalmente que pedir a **otro** usuario que genere un token manualmente y lo introduzca en la aplicación **viola la API Policy**, y que las aplicaciones usadas por múltiples usuarios deben usar OAuth **[DOC]** (`Q-infraestructura-08`). La aplicación se ajusta así:

1. La pantalla de credenciales **sólo la puede usar quien tiene `curso.administrar`**, que no es concedible a un ayudante (A-021).
2. **Comprobación de identidad, reescrita.** La revisión 1 comparaba el `id` devuelto por `GET /api/v1/users/self` contra `usuario.canvas_user_id`, «que se fija en el primer pegado y ya no cambia». Eso tenía dos defectos y **ambos quedan corregidos**: en el primer pegado la columna está vacía, de modo que la comprobación era **vacua justo en el único momento en que alguien podría pegar el token de otro**; y un escalar único por usuario no puede representar identidades en dos instancias de Canvas distintas, escenario que el propio A-027 contempla al indexar por `(canvas_base_url, canvas_course_id)`. La identidad de Canvas pasa a vivir en su propia tabla, **`identidad_canvas_usuario (usuario_id, canvas_base_url, canvas_user_id, verificada_en, ultima_confirmacion_en)`**, con unicidad `(usuario_id, canvas_base_url)` y **unicidad `(canvas_base_url, canvas_user_id)`**. `usuario.canvas_user_id` **desaparece del esquema**. Las reglas, en orden, y todas se ejecutan siempre:

   | # | Comprobación al pegar un token | Si falla |
   |---|---|---|
   | 2.a | `GET /api/v1/users/self` responde `200` | Se rechaza: el token no sirve |
   | 2.b | Ese `id` **tiene una matrícula de profesor activa en el curso de Canvas que se está vinculando**, leída con `GET /courses/:id/enrollments?user_id=self&type[]=TeacherEnrollment` | Se rechaza con el mensaje «este token pertenece a alguien que no es profesor de ese curso». **Ésta es la comprobación que sí funciona en el primer pegado**, y es la que cierra el agujero |
   | 2.c | Ese `(canvas_base_url, canvas_user_id)` **no está ya vinculado a otro usuario de la aplicación** | Se rechaza y se abre incidencia: dos personas distintas no pueden ser la misma persona de Canvas |
   | 2.d | Si el usuario **ya tiene** identidad registrada para esa `canvas_base_url`, el `id` devuelto **coincide** con ella | Se rechaza. Es la comprobación de la revisión 1, ahora bien acotada: sólo aplica a partir del segundo pegado en esa instancia, que es cuando tiene sentido |
   | 2.e | Si **no la tiene**, se registra ahora como identidad verificada de esa instancia, con `verificada_en` | — |

   **La identidad registrada no es inmutable y el documento no finge que lo sea.** A-051 reconoce que una fusión en Canvas destruye el `canvas_user_id`, y por eso `identidad_canvas_usuario` es corregible por su propio dueño repitiendo el pegado tras confirmar en pantalla el cambio, lo que deja rastro en `bitacora`. La antigua frase «ya no cambia» **queda retirada**.
3. El formulario dice explícitamente: «pega tu propio token; no pegues el de otra persona», y el botón de envío está deshabilitado hasta marcar una casilla que lo afirma.

### A-034 · Cifrado y no exposición — ANULADA POR RG-138 en su clave maestra única

> **Manda ahora A-191.** El algoritmo, el *nonce* por fila y el `curso_id` como *additional authenticated data* se conservan; lo que queda superado es la clave única en `APP_ENCRYPTION_KEY`, que pasa a ser un **llavero versionado** con recifrado perezoso. La regla de no exposición se conserva entera.

El token de Canvas se cifra con **AES-256-GCM**: clave maestra de 32 bytes en `APP_ENCRYPTION_KEY`, *nonce* aleatorio por fila, y el `curso_id` como *additional authenticated data*, de modo que una fila cifrada no puede reutilizarse en otro curso. **Ninguna ruta de la API devuelve jamás un secreto.** La interfaz muestra únicamente la huella (`sha256` truncado), el nombre del titular, el estado y la fecha de la última validación con éxito. La columna se excluye explícitamente de todo esquema Pydantic de salida.

### A-035 · Una credencial operativa por curso, con respaldo ordenado

Un curso designa **una credencial operativa** —la que usan los trabajos de fondo— y admite credenciales de respaldo de otros profesores del curso, ordenadas. Motivo: **R2.6.7** y **R2.7.6** mueren si la única credencial se revoca, y el enunciado exige comunicaciones automáticas y publicación de notas. Unicidad: `(curso_id, usuario_id)` y una sola fila con `orden_respaldo = 0` por curso.

**Cómo se concilia esto con la API Policy que A-033 cita, porque la revisión 1 dejaba la tensión sin resolver.** La política dice que pedir a **otro** usuario que genere un token y lo introduzca en la aplicación es lo que está prohibido, y que las aplicaciones usadas por múltiples usuarios deben usar OAuth **[DOC]** (`Q-infraestructura-08`). Las tres reglas que cierran el hueco:

1. **Nadie pega jamás el token de otra persona.** Una credencial de respaldo sólo puede crearla **su propio titular, desde su propia sesión**, en la pantalla de credenciales del curso, y las comprobaciones 2.a–2.e de A-033 lo verifican contra Canvas en el momento del pegado. Un profesor **no puede** añadir la credencial de un colega ni pedírsela por escrito: la interfaz sólo ofrece «añadir **mi** credencial».
2. **El titular consiente por escrito y sabe exactamente a qué.** La pantalla dice, antes de guardar y con el texto a la vista: «con esta credencial la aplicación publicará notas, anuncios, mensajes y comentarios **a tu nombre** en Canvas, incluidos los originados por otros miembros del equipo docente, y podrá hacerlo cuando tú no estés conectado. Puedes retirarla en cualquier momento». Sin esa casilla marcada no se guarda nada, y el consentimiento queda en `bitacora` con fecha.
3. **Cada titular ve y puede retirar lo suyo.** La pantalla de credenciales lista, para el titular, cuántas escrituras se han hecho con su credencial en los últimos 7 días y con qué destino, y ofrece **«retirar mi credencial»**, que la pasa a `RETIRADA` y promueve la siguiente del orden.

Es el mismo patrón de consentimiento informado que una aplicación con OAuth obtiene en su pantalla de autorización, implementado con la única herramienta que el rol de profesor permite. **La solución limpia sigue siendo OAuth2 con Developer Key institucional, sigue estando pedida por escrito (A-032) y sigue siendo el camino que se conmuta el día que la universidad la conceda.** El documento no pretende que un formulario equivalga a OAuth: pretende no violar la política mientras OAuth no exista.

### A-036 · Qué pasa si el token se revoca, caduca o el titular pierde el rol

Este punto lo exige explícitamente el documento de decisiones de infraestructura, y es la diferencia entre una aplicación que se cae en silencio y una que degrada de forma controlada. Ante un `401` de Canvas, o un `403` no transitorio repetido tres veces:

1. La credencial pasa a `INVALIDA` de inmediato; el curso pasa a `CANVAS_DESVINCULADO`; se abre la incidencia `CANVAS_CREDENCIAL_INVALIDA`.
2. **Se promueve automáticamente la primera credencial de respaldo válida**, si existe. Si funciona, el resto de pasos no ocurre y queda registrado en `bitacora`.
3. **Los trabajos de lectura de Canvas se detienen** —no se sincroniza contra datos que no se pueden leer— y **los trabajos de escritura se encolan, no se descartan**: publicaciones de nota, anuncios, mensajes y comentarios quedan en `trabajo` con estado `ESPERANDO_CREDENCIAL`.
4. **Lo que no depende de Canvas no se detiene**: aprovisionamiento, ingesta de actividad, tableros, timeline y **captura de versiones**, porque las fechas efectivas ya están persistidas y **R2.4.5** no puede depender de que Canvas esté accesible en ese instante.
5. Todo el curso muestra una **banda roja persistente** con el texto exacto de qué falta, quién puede arreglarlo y el enlace a la pantalla de sustitución. Se envía correo a todos los profesores del curso.
6. **Cualquier profesor del curso** —no sólo el titular original— puede pegar **su propia** credencial nueva (A-035 regla 1). **Qué orden recibe está decidido y no se deja al implementador**, porque de ello depende con qué identidad aparecen firmadas todas las escrituras posteriores en Canvas, que es justamente el asunto de RA-21:

   | Situación al pegar | Orden que recibe | Por qué |
   |---|---|---|
   | **No hay credencial operativa válida** (la de `orden_respaldo = 0` está `INVALIDA` o `RETIRADA`) | **`orden_respaldo = 0` de inmediato**, desplazando a la inválida al final del orden | Es el caso de la banda roja: el curso está parado y lo urgente es que vuelva a funcionar. Se hace sin pregunta y se anuncia en pantalla: «a partir de ahora la aplicación escribirá en Canvas como *nombre*» |
   | **Hay credencial operativa válida** | **`orden_respaldo = max + 1`**, es decir, entra como respaldo y **no desplaza a nadie** | Cambiar en silencio la identidad con la que se firman las notas sería exactamente el tipo de efecto invisible que este documento prohíbe |
   | Un profesor quiere **promover** su credencial a operativa habiendo otra válida | Acción explícita **«hacer operativa la mía»**, con confirmación que nombra a la persona desplazada, aviso por correo a los profesores del curso y registro en `bitacora` | Es un cambio de identidad de escritura; se hace a propósito o no se hace |

   Al validarse, los trabajos encolados se reanudan en orden, respetando la idempotencia del *outbox* (A-125) para no duplicar mensajes. **La cabecera del curso muestra siempre, en texto, con qué identidad de Canvas escribe la aplicación**, para que nadie tenga que deducirlo.
7. Si el titular **perdió el rol de profesor en Canvas**, la validación falla al comprobar el curso, no al comprobar el usuario; el mensaje distingue los dos casos porque la acción correctiva es distinta.

### A-037 · Sonda periódica de la credencial

Cada **15 minutos** se valida la credencial operativa con `GET /api/v1/users/self` y `GET /api/v1/courses/:id`. El resultado alimenta `credencial_canvas.estado`, `ultimo_chequeo_en` y `GET /estado`. Detectar la revocación antes de que la note un envío es lo que permite avisar en lugar de fallar.

### A-038 · GitHub: no se persiste ningún token

Se guarda únicamente `installation_id`. Los tokens de instalación se obtienen en caliente firmando un JWT con la clave privada de la App y se cachean **en memoria del proceso**, nunca en base, hasta cinco minutos antes de su expiración. **Consecuencia deseada y defendible: un volcado de la base de datos no contiene ninguna credencial que permita escribir en GitHub.**

### A-191 · Llavero versionado de claves de cifrado, con recifrado perezoso

**Sustituye la clave única de A-034.** El token de Canvas se sigue cifrando con **AES-256-GCM**, *nonce* aleatorio por fila y `curso_id` como *additional authenticated data*. **La clave no es una: es un llavero versionado.**

| Pieza | Qué es |
|---|---|
| `APP_ENCRYPTION_KEYS` | Mapa `{"1": "<32 bytes en base64>", "2": …}` |
| `APP_ENCRYPTION_KEY_ACTIVA` | La versión con la que se **cifra** |
| `credencial_canvas.version_clave` (`smallint NOT NULL DEFAULT 1`) | La versión con la que se **descifra esa fila** |

- **El arranque falla** si `APP_ENCRYPTION_KEY_ACTIVA` no está en `APP_ENCRYPTION_KEYS`. Es una validación de configuración, no una comprobación en caliente.
- **Rotación en línea y reanudable:** se añade la clave nueva, se cambia la versión activa, y el **recifrado perezoso** reescribe cada fila la próxima vez que la sonda de A-037 la valida —cada 15 minutos, de modo que **un ciclo migra todas**—. La clave antigua se retira cuando no queda ninguna fila con esa versión, comprobable con una consulta, y **`/operacion` muestra cuántas filas faltan durante la rotación** (A-232, sección de despliegue).
- **`APP_ENCRYPTION_KEY` y `APP_ENCRYPTION_KEY_ANTERIOR` no existen**, y el comando `rotar_clave_maestra` **queda retirado**.
- **Ninguna ruta de la API devuelve jamás un secreto**, y la interfaz sigue mostrando únicamente la huella, el titular, el estado y la fecha de la última validación con éxito (A-034).

`infraestructura/cifrado.py` expone exactamente dos funciones: `cifrar(texto, curso_id)` y `descifrar(bytes, nonce, version_clave, curso_id)`. **El token de Canvas es el único secreto que se persiste** (A-176).

Sirve a **R2.1.4**, **R2.1.5**, **R2.1.6**, **R2.6.5**, **R2.6.6**, **R2.7.6**.

---

## 6. Integración con Canvas bajo rol de profesor

### A-039 · Cliente único con las reglas de la casa — ANULADA POR RG-071 y RG-070 en su registro de coste

> **Manda ahora A-219.** `X-Request-Cost` y `X-Rate-Limit-Remaining` dejan de vivir sólo en `sincronizacion.coste` y pasan al cubo `CANVAS` de **`presupuesto_api`**, único almacén de presupuesto medido; y un `403` de Canvas **sólo es límite de tasa si la respuesta lo demuestra**. Las cinco reglas de paginación, tope de páginas, concurrencia uno por curso, retroceso ante `429` y tratamiento de instantes se conservan íntegras.

Todo acceso a Canvas pasa por una clase `ClienteCanvas` construida a partir de un `curso_id`. Reglas no negociables, todas con respaldo documental:

- **Paginación siempre por el header `Link`, nunca calculando páginas.** La documentación dice que el límite de `per_page` no está especificado y prescribe tratar esas URLs como opacas y comprobar siempre el `Link` **[DOC]** (`Q-2.2-41`). Se envía `per_page=100` como valor de partida, pero el cliente **jamás asume que recibió 100**: mide `len(json)` en la primera llamada de cada recurso y lo persiste en `cursor_sincronizacion`. **El número 100 no se escribe como hecho en ninguna parte de la especificación.**
- **Tope de seguridad de 50 páginas por llamada.** Al alcanzarlo la sincronización **no falla**: cierra el ciclo, registra `TRUNCADA`, deja el cursor donde estaba, abre incidencia y continúa en el ciclo siguiente. Nunca se cuelga un trabajo por un curso anómalo.
- **Una sola petición simultánea por curso**, con semáforo por `curso_id`. La documentación afirma que un cliente que no hace más de una petición simultánea es improbable que sea limitado, y que las peticiones paralelas sufren una penalización adicional de *pre-flight* **[DOC]** (`Q-2.2-41`). Paralelizar contra Canvas nos perjudica; no se hace.
- **Ante `429`: retroceso exponencial con *jitter***, base 2 s, factor 2, tope 5 minutos, máximo 6 intentos. Agotados, el trabajo pasa a `ESPERANDO_LIMITE` —transitorio, visible y reintentable—, **nunca a `ERROR`** (Ley 5).
- **Todos los timestamps se tratan como instantes UTC en ISO 8601 con resolución de segundos**, que es el formato documentado **[DOC]** (`Q-2.4-18`, `Q-2.4-22`). Toda comparación entre Canvas y GitHub se hace **truncada al segundo**, porque ninguna de las dos APIs promete milisegundos.
- Cada respuesta registra `X-Request-Cost` y `X-Rate-Limit-Remaining` en `sincronizacion.coste`.

### A-040 · Asistente de vinculación de cuatro pasos con estado persistido

**R2.1.6** exige guiar al profesor y permitirle verificar que la configuración es correcta, y §3.1 del enunciado evalúa explícitamente «la facilidad de uso y la guía adecuada». El asistente **no es un formulario**: es un flujo de cuatro pasos que se puede abandonar y retomar, y cada paso muestra qué se verificó y cuándo.

1. **Datos del curso** — nombre, código, período, zona horaria.
2. **Canvas** — pegar el token personal y **elegir el curso de la lista** que devuelve `GET /api/v1/courses?enrollment_type=teacher`. **El profesor no escribe nunca el identificador numérico del curso**: escribirlo a mano es la fuente más común de vinculaciones incorrectas.
3. **GitHub** — instalar la App en la organización mediante el botón que lleva a la URL de instalación con `state` (A-058). Al volver, el `installation_id` queda asociado al curso sin que el profesor copie nada.
4. **Verificación** — el checklist de A-041, con semáforos, explicación en una frase y **un botón por ítem rojo que lleva exactamente al sitio donde se arregla**.

### A-041 · Checklist de verificación de la vinculación — ANULADA POR RG-061, RG-063, RG-135 y RG-200 en cuatro puntos

> **Manda ahora A-192.** Las 19 comprobaciones y su severidad se conservan una a una; lo que queda superado es que se ejecutara síncronamente, que `verificacion_vinculacion.item` admitiera sólo 19 códigos —son **21**, con `5-bis` y `17-bis`—, que `resultado` tuviera cuatro valores —son **cinco**, con `VERIFICADO_A_MANO`— y el contenido del **ítem 14**, que pasa a comprobar **seis** cosas.

Se ejecuta bajo demanda y su resultado se **persiste con fecha y con la respuesta cruda de cada comprobación** en `verificacion_vinculacion`, de modo que el docente ve qué se comprobó y cuándo.

| # | Comprobación | Llamada | Severidad |
|---|---|---|---|
| 1 | El token es válido y es tuyo | `GET /api/v1/users/self`, contrastado con A-033 | **Bloqueante** |
| 2 | El curso existe, es visible y está publicado | `GET /api/v1/courses/:id?include[]=permissions` | **Bloqueante** |
| 3 | Eres profesor del curso y **no estás limitado a una sección** | `GET /courses/:id/enrollments?user_id=self&type[]=TeacherEnrollment` → `limit_privileges_to_course_section` **[DOC]** (`Q-2.1-28`) | **Bloqueante si es `true`** (A-052) |
| 4 | Puedes editar notas | `GET /courses/:id/permissions?permissions[]=manage_grades` | Advertencia fuerte: afecta a **R2.7.6** |
| 5 | Puedes publicar anuncios | `permissions[]=post_to_forum` más `create_announcement` del hash de permisos del curso **[DOC]** (`Q-2.6-50`) | Advertencia: **R2.6.6** quedaría deshabilitado |
| 6 | Puedes enviar mensajes | `permissions[]=send_messages`, `send_messages_all` | **Advertencia fuerte**: es el canal primario de **R2.6.5** y **R2.3.12**. Si sale rojo, **R2.3.12 pasa al canal alternativo declarado en A-127**, y el ítem 17 se vuelve bloqueante |
| 7 | Puedes ver correos de estudiantes | `permissions[]=read_email_addresses` | Informativo: condiciona A-118 regla 3 |
| 8 | Secciones legibles y detección de *cross-listing* | `GET /courses/:id/sections` → `nonxlist_course_id` **[DOC]** (`Q-2.2-47`) | Advertencia (A-053) |
| 9 | Conjuntos de grupos colaborativos | `GET /courses/:id/group_categories` | Informativo (recuento) |
| 10 | Política de entrega tardía del curso | `GET /courses/:id/late_policy` **[DOC]** (`Q-2.7-67`) | **Advertencia fuerte**: condiciona A-140 |
| 11 | Períodos de calificación abiertos | `GET /courses/:id/grading_periods` → `is_closed` **[DOC]** (`Q-2.7-64`) | Advertencia; **bloqueante al publicar** |
| 12 | Tamaño real de página que acepta la instancia | primera llamada al roster, se mide `len(json)` y el `Link` | Informativo, se persiste |
| 13 | Zona horaria del curso | `course.time_zone` | Informativo; alimenta A-152 |
| 14 | La App está instalada y su alcance | `GET /app/installations/{id}` → `repository_selection`, permisos pendientes | **Bloqueante** si no está instalada |
| 15 | Estudiantes legibles | recuento del roster | Advertencia si el curso está vacío |
| **16** | **Puedes crear y editar tareas en Canvas** | `GET /courses/:id/permissions?permissions[]=manage_assignments&permissions[]=manage_assignments_add` | **Bloqueante.** De él depende A-144, y con A-144 la **vía principal de R2.2.4 y R2.2.5**. La revisión 1 verificaba notas, anuncios, mensajes, correos, secciones, categorías, política de atraso, períodos y paginación, y **no verificaba esto**, que es el permiso del que cuelga el enrolamiento entero |
| **17** | **Puedes escribir comentarios en las entregas** | `permissions[]=comment_on_submissions` si la instancia lo expone; si no, se resuelve con la prueba de escritura del ítem 17-bis | **Advertencia fuerte**, y **bloqueante si el ítem 6 salió rojo**, porque entonces es el único canal que le queda a **R2.3.12** (A-127) y a la respuesta al estudiante de A-146 |
| **18** | **El equipo docente puede recibir lectura de los repositorios** | `GET /orgs/{org}/teams/docentes` o, si no existe, `POST /orgs/{org}/teams`; y `GET /orgs/{org}/members/{login}` por cada miembro con `curso.ver` | **Bloqueante para R2.4.8 y R2.7.4.** Si la vía de equipo falla, el checklist lo dice y activa la **vía de respaldo por colaborador individual** de A-163, que está documentada; sólo si fallan las dos el ítem queda rojo |
| **19** | **Puedes borrar anuncios propios** | `permissions[]=moderate_forum` | Informativo: de él depende el borrado del anuncio de verificación de A-042. Si falta, la prueba de escritura del ítem se ofrece igualmente **avisando de que el anuncio habrá que borrarlo a mano**, y el trabajo `limpieza_verificacion` abre incidencia en vez de borrar |

**Son 19 comprobaciones, no 15.** Las cuatro últimas se añadieron en la revisión 2 porque la vía principal de enrolamiento (A-144), el canal alternativo de **R2.3.12** (A-127), el acceso del corrector (A-163) y la limpieza de A-042 descansaban en permisos que nadie miraba.

**Advertencia que el checklist declara por escrito en la propia pantalla:** un permiso en verde **no garantiza** que la llamada funcione, porque un token emitido por una developer key con *scopes* limitados puede responder `401` aunque el usuario tenga el permiso **[DOC]** (`Q-2.1-54`). Por eso existe A-042.

### A-042 · Prueba de escritura real, opcional y explícita

El checklist incluye una **prueba de escritura no destructiva**, ejecutada **sólo si el profesor la autoriza marcando una casilla**: crea un anuncio con `delayed_post_at` a un año vista y un título con el prefijo `[verificación app]`, comprueba el `201` y lo borra de inmediato con `DELETE`. Si no marca la casilla, ese ítem queda **«no verificado»**, nunca verde.

- **No se usa `published=false`**: la documentación **no** dice que Canvas acepte esa combinación con `is_announcement=true` ni que un borrador no notifique a los estudiantes **[MEDIR]** (`Q-2.1-54`). `delayed_post_at` sí es un campo documentado del objeto y produce un anuncio que no se publica ahora.
- Un trabajo de limpieza busca a diario anuncios con ese prefijo y los elimina, por si el proceso muriera entre crear y borrar.

**Por qué se hace y no se descarta:** **R2.1.6** pide «verificar que las configuraciones realizadas son correctas», y el endpoint de permisos, por documentación propia, no puede garantizarlo. Un ítem que dice «tienes el permiso, pero no hemos probado que la llamada funcione» es información honesta pero incompleta; la prueba opcional la completa sin tocar nada que el estudiante vea.

### A-043 · Lectura del roster

`GET /api/v1/courses/:id/enrollments?type[]=StudentEnrollment&state[]=active&state[]=invited&include[]=group_ids&include[]=uuid&per_page=100`, paginado por `Link`.

- **`state[]` se pide explícitamente** aunque coincida con el valor por defecto documentado **[DOC]** (`Q-2.2-40`): deja la intención escrita en el código y protege ante un cambio del valor por defecto. **No** se piden `deleted` ni `completed` en el ciclo normal, porque con ellos el upsert por estudiante colapsaría matrículas distintas.
- **Se filtra por `type[]`, nunca por `role[]`**: el filtro de tipo se ignora si se pasa el de rol **[DOC]** (`Q-2.1-29`). Que un rol personalizado derivado de `StudentEnrollment` aparezca bajo `type[]=StudentEnrollment` **no está documentado** **[MEDIR]**; el modelo admite `curso.roles_estudiante_extra` (lista de `role_id` configurable por curso) para cubrirlo sin cambiar el esquema si la medición sale negativa.
- **`include[]=group_ids` se pide pero no se usa como fuente de grupos.** Es un valor documentado del endpoint, pero la documentación **no** dice de qué categorías proceden esos ids, ni si incluye grupos no colaborativos **[DOC]/[MEDIR]** (`Q-2.2-43`). Se persiste como dato de contraste y se abre incidencia si contradice a A-047; la fuente autoritativa de grupos es siempre A-047.

### A-044 · Una fila por matrícula y un estudiante consolidado

`matricula` guarda una fila por cada `Enrollment` y `estudiante` una fila por persona. **No se colapsan.** La API devuelve una fila **por matrícula**, no por usuario, y un mismo estudiante puede tener dos matrículas activas simultáneas —por ejemplo en dos secciones— que son ambas legítimas **[DOC]** (`Q-2.2-40`).

Un modelo que guardara sólo el estudiante perdería la sección, que es lo que exige **R2.2.2**; un modelo que guardara sólo la matrícula duplicaría al estudiante en toda la interfaz y le crearía dos repositorios.

`estudiante.estado` se **deriva**: `ACTIVO` si tiene al menos una matrícula activa; `INVITADO` si sólo tiene invitadas; `RETIRADO` si desapareció del roster durante **dos ciclos consecutivos**.

Sirve a **R2.2.1**, **R2.2.2**.

### A-045 · Regla anti-bajas-masivas

Si un ciclo de `sync_roster` devuelve **cero estudiantes, o menos del 60 % del recuento anterior**, **no se aplica ninguna baja**: se registra `sincronizacion.resultado = PARCIAL`, se abre la incidencia `ROSTER_SOSPECHOSO` y se conserva el estado previo.

Motivo directo: un roster recortado por permisos llega como un `200` normal, sin ningún aviso **[MEDIR]** (`Q-2.1-28`). Sin esta regla, un fallo transitorio o un cambio de permisos revocaría accesos y dispararía comunicaciones falsas a media clase.

### A-046 · Estudiante en dos secciones activas

No se elige en silencio. Se registran **ambas** matrículas, la interfaz muestra las dos secciones con una etiqueta de conflicto, y se abre la incidencia `ESTUDIANTE_EN_DOS_SECCIONES`. Para el cálculo de la fecha de cierre se aplica la regla explícita de A-055 —se toma **la más tardía** y la fila se marca `ambigua=true`—, porque no elegir dejaría al estudiante sin fecha de captura y **R2.4.5** quedaría cojo.

### A-047 · Grupos: por `memberships`, y sólo categorías colaborativas

- La cadena es `GET /courses/:id/group_categories` → `GET /group_categories/:id/groups` → **`GET /groups/:id/memberships`**, no `/groups/:id/users`. Motivo documentado: sólo `memberships` expone y filtra `workflow_state`; la página de `/users` no dice si incluye u omite a los `invited` **[DOC]** (`Q-2.2-50`).
- **Sólo se sincronizan categorías colaborativas**, que es el valor por defecto de `collaboration_state` **[DOC]** (`Q-2.2-49`). Las *differentiation tags* (`non_collaborative=true`) **no** son grupos de **R2.2.3**, no reciben repositorio y no participan en el cálculo de fechas. Se detectan una vez al vincular pidiendo `collaboration_state=all` y se muestran como etiqueta informativa: «este conjunto es una etiqueta de diferenciación, no genera repositorios».
- **Los estados de pertenencia son exactamente `accepted`, `invited` y `requested`** **[DOC]** (`Q-2.2-50`), y se persisten tal cual.

Sirve a **R2.2.3**.

### A-048 · Cuenta como integrante quien está `accepted`

Los `invited` y `requested` se persisten con su estado, **no cuentan** para el repositorio del grupo y aparecen en Pendientes como «pendiente de aceptar en Canvas» (**R2.2.6**). En grupos de curso el `join_level` documentado es `invitation_only`, y ser invitado no es ser miembro.

**Un grupo con al menos un `accepted` cuyo mapeo esté verificado SÍ recibe repositorio.** Bloquearlo hasta tener el 100 % dejaría cojo **R2.3.10**, que exige crear «progresivamente a medida que se disponga de toda la información requerida para cada estudiante o grupo». Los integrantes que confirmen después se incorporan al repositorio existente en el ciclo siguiente, que es exactamente el comportamiento progresivo que el requisito describe.

**El estado del repositorio en ese caso es `DEGRADADO`, y el predicado exacto está en A-092, no aquí.** La revisión 1 decía `DEGRADADO` en esta decisión y, tres páginas más allá, la tabla de transiciones de A-092 dejaba el mismo repositorio en `OPERATIVO`; **la contradicción se resuelve en A-092, que es la autoridad sobre los estados del repositorio**, y esta decisión sólo aporta el hecho de entrada: *los `invited` y `requested` de Canvas no cuentan como integrantes, pero sí cuentan como personas que faltan*. Las dos cosas son verdad a la vez y la distinción es la que hacía falta: **no cuentan para decidir si el repositorio se crea; sí cuentan para decidir si está completo.**

### A-049 · Doble pertenencia a grupos: se materializa, no se rechaza

**No se impone unicidad `(conjunto_grupos, estudiante)` en la base de datos.** La documentación afirma que el modelo previsto por Canvas es un grupo por categoría, pero **no** afirma que la API lo impida ni que sea imposible recibir esa inconsistencia **[DOC]** (`Q-2.2-53`). Una restricción única haría que **la ingesta entera fallara** ante un dato que el sistema de origen sí admite, que es el peor desenlace posible.

En su lugar: se insertan ambas pertenencias, se abre la incidencia bloqueante `ESTUDIANTE_EN_DOS_GRUPOS`, **se bloquea el aprovisionamiento de los dos grupos implicados** —porque no se puede saber cuál debe recibir a esa persona— y se muestra en Pendientes con las dos opciones de resolución. Esto es literalmente lo que piden **R2.2.6** y **R2.3.11**: mostrar claramente el problema.

### A-050 · Estudiante de prueba de Canvas

El *Test Student* se excluye siempre del roster, del aprovisionamiento y de toda comunicación. El discriminador es el tipo de matrícula `StudentViewEnrollment`, que queda fuera del filtro `type[]=StudentEnrollment` de A-043; se contrasta además por nombre y se confirma en la instancia real **[MEDIR]**.

### A-051 · Fusión de usuarios en Canvas

`canvas_user_id` **no es inmutable frente a una fusión**, operación que borra el usuario origen y mueve sus matrículas al destino **[DOC]** (`Q-2.2-30`), y no existe señal documentada y utilizable de fusión en el roster **[MEDIR]**. La aplicación:

1. **No borra nada**: el estudiante desaparecido pasa a `RETIRADO` y conserva mapeo, repositorio y versiones.
2. Si aparece un `canvas_user_id` **nuevo** cuyo `login_id` o `sis_user_id` coincide con uno retirado, abre la incidencia `POSIBLE_FUSION_CANVAS` proponiendo migrar el mapeo y el repositorio.
3. **Un profesor confirma.** Fusionar solo sería adivinar sobre la identidad de una persona, y el coste de equivocarse es dar el repositorio de alguien a otro.

### A-052 · Profesor limitado a una sección: la vinculación se bloquea

Si el `TeacherEnrollment` del titular trae `limit_privileges_to_course_section = true`, **la vinculación no se completa**, con un mensaje que explica por qué y qué hacer. Motivo: un roster truncado llegaría como un `200` normal y la aplicación interpretaría a media clase como retirada. Con **R2.2.1** y **R2.3.7** cumplidos a medias y de forma invisible, es preferible no vincular a vincular mal.

### A-053 · *Cross-listing*: fuera de alcance soportado, pero advertido

Si una sección trae `nonxlist_course_id` no nulo **[DOC]** (`Q-2.2-47`), la sección se sincroniza igual y el asistente emite advertencia. La limitación se documenta en pantalla y en la memoria de entrega. No se intenta reconstruir la relación entre cursos cruzados.

### A-054 · Fuente autoritativa de fechas

**R2.4.1**–**R2.4.4** dependen enteramente de esta decisión. Se usan dos caminos con jerarquía explícita:

- **Aceleración:** `GET /courses/:id/assignments?include[]=all_dates&include[]=overrides&include[]=assignment_visibility&per_page=100`, que trae casi todo en pocas llamadas y sirve para **detectar rápido qué cambió**.
- **Autoridad:** `GET /courses/:id/assignments/:aid/overrides`, paginado siguiendo `Link`, por cada entrega vinculada. **Es el que fija el valor.**

Motivo: la documentación **no garantiza** que los arrays embebidos por `include[]` sean completos —no dice que estén truncados, pero tampoco que no lo estén— y `AssignmentDate` **no** trae los `student_ids`, que sólo existen en `AssignmentOverride` **[DOC]** (`Q-2.4-09`). Como de esas fechas depende cuándo se captura la versión de cada estudiante, apoyarse en un array sin garantía de completitud es inaceptable. **Una discrepancia entre ambas fuentes abre incidencia.**

**`include[]=assignment_visibility` no se pide de adorno: se persiste y se usa.** La revisión 1 lo pedía aquí y persistía `only_visible_to_overrides` en A-080 sin que ninguno de los dos campos apareciera jamás en una regla, lo que dejaba **R2.3.7** sin definir. Su destino está fijado: alimentan la tabla `visibilidad_entrega` y son la entrada de la regla de materialización de sujetos de **A-164**. Si la instancia no devolviera `assignment_visibility`, A-164 declara el desenlace exacto en vez de dejarlo al implementador.

### A-055 · Algoritmo de la fecha efectiva

Para cada `(entrega, sujeto)` se calcula un único instante y se persiste en `fecha_efectiva` con la regla que lo produjo. Prioridad, de mayor a menor:

1. Override dirigido al **estudiante** (`student_ids` contiene su `canvas_user_id`) — origen `ADHOC`.
2. Override dirigido al **grupo** del sujeto, evaluado **sólo si la tarea es grupal**, que es la condición documentada para que un override por grupo sea válido **[DOC]** (`Q-2.2-49`, `Q-2.3-05`) — origen `GRUPO`.
3. Override dirigido a la **sección** de su matrícula activa — origen `SECCION`.
4. Fecha **base** de la entrega — origen `BASE`.

Casos límite fijados, sin excepciones:

- **Dos overrides del mismo nivel** (por ejemplo, dos secciones activas): se toma **la fecha más tardía**, la fila se marca `ambigua=true` y se abre incidencia. Se elige la más tardía porque **capturar antes de tiempo destruiría trabajo legítimo**, mientras que capturar más tarde sólo incluye trabajo adicional que el docente puede ver. La regla de resolución de Canvas ante overrides concurrentes no está citada en la documentación **[MEDIR]**, así que la aplicación fija la suya, **la escribe junto a cada fecha en la interfaz** (`regla_aplicada`) y la contrasta con lo que Canvas muestra.
- **Sujeto no visible para esa entrega** (A-164): **no se calcula fecha efectiva, no se programa captura y la interfaz lo dice**, con el texto «esta entrega no aplica a este sujeto». No es un error ni una fecha ausente: es una entrega que no le corresponde. Es el caso que hace consistente que dos entregas de la misma tarea tengan visibilidad distinta compartiendo repositorio, como **R2.3.4** obliga.
- **Sujeto visible pero sin ninguna fecha aplicable** (`due_at` nulo y sin overrides): **no se programa captura** y la entrega se muestra como «sin fecha de cierre». **No se inventa una fecha.** Es distinto del caso anterior y la interfaz los distingue, porque la acción del docente no es la misma.
- **Fechas de sección** (`start_at`, `end_at`, `restrict_enrollments_to_section_dates`): **se ignoran para el cálculo**. La documentación las describe exclusivamente en términos de matrícula y acceso al curso y **no** les atribuye efecto sobre `due_at` **[DOC]** (`Q-2.4-16`). Se persisten y, si el `due_at` efectivo cae fuera del rango de participación de la sección, se muestra una advertencia informativa. **Advertir sin alterar el cálculo es lo correcto cuando la documentación no respalda el efecto.**

Sirve a **R2.4.1**, **R2.4.2**, **R2.4.3**.

### A-056 · El disparador de resincronización de fechas es un hash, no `updated_at`

**Se descarta `assignment.updated_at > ultimo_visto`**, que es lo que propone el estudio interno. La documentación describe `updated_at` como «la hora a la que la tarea fue modificada de cualquier forma», frase que **no** aclara si crear, editar o borrar un override cuenta como modificar la tarea, y el objeto `AssignmentOverride` **no expone ningún timestamp propio** **[MEDIR]** (`Q-2.4-10`).

Si la respuesta fuera que no lo toca, **las extensiones concedidas a un estudiante concreto serían invisibles para el sincronizador y R2.4.3 quedaría incumplido en silencio**, que es la peor forma de incumplir un requisito.

Decisión: en cada ciclo se recupera el conjunto completo de reglas de fecha de cada entrega, se normaliza y ordena canónicamente, se calcula un **SHA-256 (`huella_fechas`)** y se compara con el almacenado. Si difiere, se recalculan las fechas efectivas, se reprograman las capturas y se evalúan las comunicaciones. Cuesta una comparación de 32 bytes y es **inmune al supuesto no documentado**.

### A-192 · El checklist es un trabajo encolado: 21 códigos, cinco resultados y un ítem 14 de seis comprobaciones

**Cierra A-041 sin tocar sus 19 comprobaciones ni sus severidades.**

**1 · Se ejecuta como trabajo encolado y la interfaz lo sondea.** `POST /api/cursos/{id}/verificacion` y `POST /api/cursos/{id}/verificacion/items/{item}` **encolan `ejecutar_checklist_vinculacion` y no llaman al proveedor dentro de la petición** (A-226). El paso 4 del asistente sondea el resultado y pinta cada ítem a medida que llega, con un tope de **10 s por ítem**. **Nada se marca verde por omisión.**

**2 · El catálogo son 21 códigos y nada más.** Las **19 comprobaciones numeradas** de A-041 —el ítem 5 sigue siendo el permiso de publicar anuncios, con severidad advertencia— más **dos pruebas de escritura opcionales identificadas como `5-bis` y `17-bis`**. `verificacion_vinculacion.item` toma exactamente esos 21 valores. **No existen los identificadores `5.a`, `20` ni ninguna subnumeración decimal**, y una prueba automatizada falla la construcción si el catálogo del código y la tabla de A-041 divergen en número, identificador o severidad.

**3 · `verificacion_vinculacion.resultado` toma cinco valores:** `CORRECTO`, `ADVERTENCIA`, `BLOQUEANTE`, `NO_VERIFICADO` y **`VERIFICADO_A_MANO`**. El quinto **no se escribe nunca de forma automática**: exige la **firma de un profesor en pantalla**, con fecha y actor persistidos en `detalle` y registro en `bitacora` con `VERIFICACION_FIRMADA_A_MANO`. Es la única salida cuando `GET /orgs/{org}` no devuelve un campo que la comprobación necesita.

**4 · El ítem 14 comprueba seis cosas y sigue siendo uno solo**, dentro del tope de 10 s y del carril de GitHub de A-217:

| Sub-comprobación | Severidad |
|---|---|
| (a) La instalación existe y cubre la organización vinculada | **Bloqueante** |
| (b) El conjunto de permisos concedidos coincide exactamente con el congelado de `docs/permisos.md` (A-194) | **Bloqueante** |
| (c) El repositorio `.github` de perfil existe (A-059) | Advertencia, nunca bloqueante por sí sola |
| (d) `default_repository_permission = none` | **Bloqueante** |
| (e) `members_can_create_repositories = false` | **Bloqueante** |
| (f) Verificación en dos pasos exigida a todos los miembros, y **dos owners** nombrados | **Bloqueante** |

Cada una guarda en `detalle` **su valor leído o `NO_LEGIBLE`**. Con `default_repository_permission` distinto de `none`, **la vinculación no se completa**. Cuando un campo no es legible con token de instalación, la sub-comprobación queda `NO_LEGIBLE` y **el ítem sólo se cierra con `VERIFICADO_A_MANO`**.

**5 · La configuración base de la organización se hace a mano y ANTES de vincular ningún curso** —y por tanto **antes del 13 de septiembre**, fecha en que `infra/semilla_demo.py` crea el curso de demostración—, con los cuatro valores (d), (e) y (f) escritos en `docs/operacion.md` con su fecha de ejecución. Si la configuración se hiciera después, la vinculación de demostración se habría completado con la comprobación en rojo y habría que rehacerla, **o peor, se habría «arreglado» bajando la severidad**.

**6 · Cambiar la credencial operativa invalida el checklist de Canvas y lo reencola**, porque un permiso verificado con un token ya no dice nada del token nuevo.

Sirve a **R2.1.5**, **R2.1.6**, **R2.1.7**, **R2.3.7**, **R2.4.8**, **R2.7.4**.

### A-193 · Mecanismo único de capacidad degradada, para los dos proveedores

**Existe un único mapa cerrado**, en `backend/app/dominio/capacidades.py` y **sin E/S**, que asocia cada capacidad de la aplicación —**de Canvas y de GitHub**— con su `proveedor`, el endpoint del que depende, el ítem del checklist que la verifica **cuando lo hay**, el requisito que sostiene y **el estado degradado exacto** en que queda la aplicación cuando esa capacidad se pierde.

**Disparador.** Cuando una llamada devuelve `401`, o un `403` clasificado como no transitorio, **con la sonda de credencial en verde** —y, en GitHub, con la instalación viva—, se clasifica **`LLAMADA_NO_AUTORIZADA`**, **la credencial no se invalida** y ocurren cuatro cosas, siempre las cuatro:

1. Se escribe una fila en **`verificacion_vinculacion` con `origen = RUNTIME`**, la `capacidad` afectada, el `item` del mapa si lo hay, `ejecutada_por` nula, el resultado que el catálogo fija y **el cuerpo literal en `detalle`**; y queda en `bitacora` con `CAPACIDAD_DEGRADADA`.
2. **El control de la interfaz afectado queda deshabilitado con el motivo escrito**, y **nunca falla al pulsarlo**.
3. Se abre la incidencia del tipo que corresponde.
4. La capacidad vuelve a `DISPONIBLE` **sólo** cuando una ejecución posterior del checklist o una llamada con éxito lo demuestran.

**El estado de una capacidad es una derivación**, no una columna: la última fila por `(curso_id, capacidad)` para las filas `RUNTIME`, y la última por `(curso_id, item)` para las de `CHECKLIST`. **No hay tabla nueva y no existen banderas sueltas por capacidad**: `instalacion_github.topics_disponibles` y una bandera `rulesets_legibles` **no se crean**, y se sustituyen por `capacidad_disponible(curso, 'ESCRIBIR_TOPICS')` y `capacidad_disponible(curso, 'LEER_RULESETS')` sobre este mismo mecanismo. **Toda bandera booleana de capacidad queda suprimida.**

**Esquema.** `verificacion_vinculacion` suma **`origen ∈ {CHECKLIST, RUNTIME}`** y **`capacidad` (text, nullable)**; `ejecutada_por` e **`item` pasan a nullable**, con un `CHECK` que exige `origen = CHECKLIST ⇒ item` no nulo y `capacidad` nula, y `origen = RUNTIME ⇒ capacidad` no nula. Índices `(curso_id, item)` y `(curso_id, capacidad)`.

**Prueba obligatoria:** toda capacidad tiene proveedor, requisito y estado degradado, y **todo endpoint de escritura de `ClienteCanvas` y de `ClienteGitHub` está cubierto por alguna fila del mapa**. Los dos clientes invocan el clasificador único **en un solo punto de salida**.

**Efecto sobre la corrección, escrito para que nadie lo confunda con un estado.** Cuando cae la capacidad `PUBLICAR_NOTA`, las correcciones afectadas **no cambian de estado**: se escribe `correccion.publicable = false` con `motivo_no_publicable = 'PUBLICACION_NO_AUTORIZADA'` (A-214), y **todas las demás transiciones de la máquina 5 siguen disponibles**. **`NO_PUBLICABLE` no vuelve a ser un estado.**

`GET /api/cursos/{id}/salud` y la cabecera del curso muestran las capacidades degradadas **con su motivo y su fecha**; las pantallas afectadas leen el mismo derivado para deshabilitar sus controles **con el mismo texto** (A-155), y `/operacion` las lista como sección de curso (A-232).

Sirve a **R2.1.6**, **R2.2.1**–**R2.2.5**, **R2.3.7**, **R2.3.8**, **R2.3.12**, **R2.4.1**–**R2.4.4**, **R2.5.3**, **R2.6.5**, **R2.6.6**, **R2.7.6**, **R2.7.7**.

---

## 7. Integración con GitHub como GitHub App

### A-057 · La App es pública

No es una preferencia. Una App **privada sólo puede instalarse en la cuenta propietaria** **[DOC]** (`Q-2.1-31`), lo que impediría que un profesor vinculara una organización distinta de la del equipo y dejaría **R2.1.5** cojo para cualquier curso que no sea el de la demostración. **No se publica en GitHub Marketplace**: es opcional, exige revisión propia y no aporta nada al caso de uso.

### A-058 · La instalación se inicia con `state` firmado

El asistente envía al profesor a `https://github.com/apps/<nombre-app>/installations/new?state=<jwt>`, forma documentada para preservar el estado de la aplicación tras la instalación **[DOC]** (`Q-2.1-31`). El `state` es un JWT de **15 minutos** que contiene `curso_id` y `usuario_id`. Al volver, la aplicación resuelve el curso por ese `state` en lugar de pedirle al profesor que copie identificadores.

### A-059 · Marca de la App

El estudiante verá el nombre de la App en la invitación y debe poder distinguirla de un intento de suplantación **[DOC]** (`Q-2.3-34`): nombre de 34 caracteres o menos, descripción explícita del curso y la universidad, avatar PNG de 200×200, y un README de perfil en la organización que explique qué es y quién la opera. **Se acepta que el distintivo «Verified» queda fuera de alcance**, porque exige verificación DNS del dominio institucional.

### A-060 · Permisos que solicita la App — ANULADA POR RG-078 y RG-079 como conjunto final

> **Manda ahora A-194.** Esta tabla es el conjunto **de partida**, no el final: el conjunto se congela el **11 de septiembre a las 20:00** con el resultado de RA-02 y con el cruce documental endpoint a endpoint, y `Workflows: write` se solicita **si y sólo si** la medición demuestra que `POST /git/refs` lo exige. Los cuatro permisos de la tabla y la justificación de `Members: write` se conservan enteros.

| Ámbito | Permiso | Nivel | Para qué |
|---|---|---|---|
| Repositorio | Administration | write | `POST /orgs/{org}/repos`, `PATCH /repos/{o}/{r}` (`is_template`), `PUT .../collaborators/{u}` **[DOC]** (`Q-infraestructura-14`) |
| Repositorio | Contents | write | `POST /repos/{t}/{r}/generate`, `PUT .../contents/{ruta}`, `POST .../git/refs`, lectura de commits; habilita los webhooks `push`, `create` y `delete` **[DOC]** (`Q-2.5-02`) |
| Repositorio | Metadata | read | Obligatorio; habilita el webhook `repository` **[DOC]** (`Q-2.5-02`) |
| Organización | Members | **write** | Dos usos, y **el segundo se añadió en la revisión 2**: (a) recibir el webhook `member`, que es **la única señal documentada de que un estudiante aceptó una invitación** **[DOC]** (`Q-2.5-02`, `Q-2.3-30`); (b) **crear y poblar el equipo `docentes` de la organización y darle lectura sobre cada repositorio** (A-163), sin lo cual **R2.4.8** y **R2.7.4** no se cumplen |

**Por qué `Members` pasa de `read` a `write`.** Los estudiantes siguen sin invitarse a la organización (A-064) y esa decisión no cambia. Lo que cambia es que **el equipo docente sí entra a la organización**, porque es la única forma de que un ayudante pueda abrir la URL `https://github.com/{org}/{repo}/tree/{sha}` que A-136 le entrega: el repositorio es `private: true` (A-065) y GitHub responde `404` a quien no tiene acceso **[DOC]** (`Q-2.3-35`). La documentación enumera exactamente quién sí puede abrirlo: el dueño, un colaborador del repositorio, **o un miembro de un equipo con acceso al repositorio** **[DOC]** (`Q-2.3-35`). La revisión 1 no invitaba a nadie del equipo docente a ninguna de esas tres categorías, y por eso su corrector veía un `404`.

**El alcance del permiso está acotado por escrito y se dice en el asistente:** se usa **sólo** sobre el equipo `docentes` y sólo para añadir o quitar a personas que son miembros activos del curso en la aplicación. **La App nunca invita a un estudiante a la organización**, y hay una prueba automatizada que falla si aparece una llamada a `PUT /orgs/{org}/memberships/` con un login que pertenece a un `mapeo_github` vigente.

**Vía de respaldo si `Members: write` no resultara concedible o el equipo no pudiera crearse:** `PUT /repos/{org}/{repo}/collaborators/{login}` con `permission=pull` por cada miembro del curso con `curso.ver`, que la tabla oficial sitúa bajo `Administration: write` **y bajo ningún otro encabezado, sin marca de permisos adicionales** **[DOC]** (`Q-infraestructura-14`) — es decir, funciona con un permiso que la App ya tiene y que ya está cerrado por documentación. A-163 fija cuándo se usa cada vía.

**No se solicita `Organization Administration`**, porque su único uso sería crear *rulesets*, que no están disponibles en plan Free para repositorios privados **[DOC]** (`Q-infraestructura-22`).

Dos permisos quedan como **[MEDIR]** y su resolución está en §19 (RA-02): la columna «Additional permissions» de la tabla oficial es **ambigua por diseño** —cubre a la vez «requiere varios permisos» y «vale cualquiera del conjunto»— y marca tanto `/generate` como `/git/refs` **[DOC]** (`Q-2.1-32`, `Q-infraestructura-14`).

### A-061 · Si falta un permiso, se añade antes del 16 de septiembre — ANULADA POR RG-078 y RG-079 en la firma de la congelación

> **Manda ahora A-194.** El calendario se conserva hora por hora; lo que se añade es que **la congelación de las 20:00 del 11 de septiembre no se firma sin el cruce documental endpoint a endpoint** del plan de medición ampliado, y que la mitigación «se instalan todos los permisos candidatos» queda acotada a un conjunto de candidatos escrito y **sólo se aplica si a esa hora la medición no ha resuelto la ambigüedad**.

Añadir un permiso obliga a que **cada instalación lo apruebe**, y los permisos nuevos **no tienen efecto hasta la aprobación** **[DOC]** (`Q-2.1-32`). Por eso el conjunto se congela tras la prueba de permisos y **no se toca después**, salvo emergencia declarada.

**El calendario, corregido, porque el de la revisión 1 era imposible.** Aquélla congelaba los permisos «tras la prueba del 10-11 de septiembre» —lo que exige tener la App **registrada** esos días—, A-059 hacía depender la marca de la App del nombre del producto, y §21 fijaba la decisión del nombre y el dominio el **12 de septiembre**: no se puede registrar y probar el 10 una App cuyo nombre se decide el 12. Se adelanta la decisión de marca, que es lo barato, en lugar de retrasar la prueba, que es lo caro:

| Cuándo | Qué |
|---|---|
| **10-sep, 09:00** | **Se decide el nombre del producto y el dominio.** Sale de §21, que ya no lo deja abierto. Es una decisión de media hora que bloqueaba dos días de trabajo técnico |
| **10-sep, tarde** | Se registra la GitHub App con su nombre definitivo, avatar y descripción (A-059), y se registra el dominio (A-008) |
| **10 y 11-sep** | **Prueba de permisos** (RA-02): pasadas A y B de `Q-infraestructura-14` sobre la organización de `ensayo` |
| **11-sep, 20:00** | **Congelación del conjunto de permisos.** A partir de aquí, añadir uno exige re-aprobación de cada instalación |

**Y si aun así hubiera que separar las dos cosas:** el registro técnico de la App **puede hacerse con un nombre provisional** y renombrarse después, porque el nombre de una GitHub App es editable y lo que no es editable es el conjunto de permisos ya aprobado. **Se prefiere no hacerlo** —un renombrado cambia el identificador que ve el estudiante en la invitación, y A-059 existe precisamente para que ese identificador sea reconocible y no parezca suplantación—, pero queda escrito como salida si el 10 por la mañana la decisión de marca se atascara. **Lo que no se hace en ningún caso es retrasar la prueba de permisos.**

### A-062 · Manejo de permisos pendientes

La App se suscribe al webhook `installation` y trata la acción `new_permissions_accepted` **[DOC]** (`Q-2.1-32`). Mientras haya permisos pendientes: `instalacion_github.permisos_pendientes = true`, el curso muestra una banda de advertencia con el enlace a la aprobación, y **los trabajos que necesitan el permiso nuevo se encolan en estado `BLOQUEADO`, no fallan**. La aplicación degrada, no se rompe. Sin este manejador, añadir un permiso durante el proyecto produce `403` inexplicables.

### A-063 · Se acepta una instalación con alcance `selected`

No se exige `all repositories`, que es una petición invasiva. Está documentado que **los repositorios que la propia App crea quedan incluidos automáticamente en la instalación** **[DOC]** (`Q-2.3-29`, `Q-2.1-36`), y ése es el caso del 100 % de los repositorios de estudiantes y del repositorio base (A-066). El asistente lo explica en el paso 4. Se procesa el webhook `installation_repositories` para detectar que alguien saca un repositorio del alcance después de vincular, lo que abre incidencia.

### A-064 · Los ESTUDIANTES entran como colaboradores del repositorio, no como miembros de la organización

> **Esta decisión trata sólo del acceso del estudiante.** El acceso de lectura del **equipo docente** —del que dependen **R2.4.8**, **R2.7.4** y el enlace a GitHub del timeline de **R2.5.10**— lo fija **A-163**, y es una decisión distinta con una respuesta distinta, porque las restricciones no son las mismas: los docentes son ocho, no doscientos, y necesitan lectura sobre **todos** los repositorios, no sobre uno.


`PUT /repos/{org}/{repo}/collaborators/{login}` con `permission=push`.

| Criterio | **Colaborador de repositorio (elegido)** | Miembro de la organización (descartado) |
|---|---|---|
| Requisito del llamante | Ninguno más allá de `Administration: write` | La documentación de `POST /orgs/{org}/invitations` exige que el usuario autenticado sea **owner**, en tensión no resuelta con la tabla de permisos que dice que basta `Members: write` **[MEDIR]** (`Q-2.1-32`) |
| Cupo | 50 invitaciones **por repositorio** cada 24 h, y sólo se emite **una** por repositorio **[DOC]** (`Q-2.3-32`, `Q-2.3-33`) | 50 cada 24 h con organización de menos de un mes o gratuita **[DOC]**: 200 estudiantes exigirían cuatro ventanas |
| Privacidad | El estudiante sólo ve su repositorio | Depende de `default_repository_permission`, que con el valor por defecto **daría lectura sobre los repositorios de sus compañeros**, y que **[MEDIR]** no consta como legible con token de instalación (`Q-2.1-39`) |
| Caducidad de la invitación | No documentada **[MEDIR]** (`Q-2.3-30`) | 7 días documentados **[DOC]** (`Q-2.3-33`) |
| Aceptación | Queda invitación pendiente (`201`) | `204` inmediato una vez que ya es miembro |

**Se elige colaborador de repositorio** porque no depende de ninguna tensión documental sin resolver, porque el cupo nunca es la restricción activa, y sobre todo **porque no abre un agujero de privacidad que dependa de leer un campo que puede no ser legible**. La contrapartida —hay una invitación que aceptar por estudiante— se asume y se convierte en estado de primera clase: la modela `acceso_repositorio`, la muestra **R2.3.11** y la recuerda **R2.6.7**.

**Hecho documentado que se aprovecha:** si el estudiante **ya** fuera miembro de la organización, la misma llamada devuelve `204` sin crear invitación **[DOC]** (`Q-2.3-30`, `Q-2.3-33`). La máquina de estados distingue `201` de `204` y **salta el estado pendiente** cuando corresponde, en lugar de esperar una aceptación que nunca llegará.

### A-065 · Los estudiantes reciben `push`, nunca `admin`; los repositorios son privados

`private: true` en toda creación: es código de estudiantes de un curso con evaluación. Con `push` y sin `admin`, el estudiante **no puede borrar el repositorio ni cambiar su visibilidad**. Sí puede borrar tags, porque en organización Free no hay rulesets aplicables a repositorios privados **[DOC]** (`Q-infraestructura-22`) — de ahí la Ley 4.

Consecuencia asumida y que hay que anticipar al estudiante: **hasta que acepte la invitación verá un `404` en la URL del repositorio**, porque GitHub responde `404` en lugar de `403` para no confirmar la existencia de repositorios privados **[DOC]** (`Q-2.3-35`). El mensaje de **R2.3.12** lo advierte por adelantado (A-127).

**Y la misma consecuencia se aplica a cualquier humano sin acceso, incluido un ayudante.** De ahí A-163: sin ella, el enlace que A-136 pone delante del corrector devuelve `404` y **R2.4.8** —«permitir a profesores y ayudantes acceder directamente a la versión que corresponde revisar»— no se cumple, por mucho que el enlace se construya sin gastar una llamada a la API. El problema nunca fue el coste de la llamada: era el permiso del humano al otro lado.

### A-163 · El equipo docente tiene lectura sobre todos los repositorios del curso — ANULADA POR RG-133, RG-136 y RG-198 en su paso 2 y en su retirada

> **Mandan ahora A-186**, que antepone al paso 2 la guarda de **consentimiento fechado** y da a `membresia_curso.org_github_estado` cinco valores; **A-187**, que exige comprobar la elegibilidad de la cuenta **inmediatamente antes** de las dos escrituras; y **A-188**, que convierte la retirada en **tres planos** y no en dos. La vía principal, la de respaldo, el modelo de `acceso_docente_repositorio` y la regla «nunca `write`, nunca `admin`» se conservan enteros.

**Cubre R2.4.8, R2.7.4 y el enlace a GitHub del timeline de R2.5.10.** Es la decisión que faltaba en la revisión 1 y sin la cual esos tres requisitos no se cumplen y la demostración del 6 de octubre enseña un `404`.

**Hecho documentado del que parte todo** **[DOC]** (`Q-2.3-35`): quien puede abrir un repositorio privado de una organización es «el dueño del repositorio, un colaborador del repositorio, o **un miembro de un equipo con acceso al repositorio**». No hay una cuarta categoría. Por tanto el equipo docente tiene que estar en una de las tres, y esta decisión lo pone en dos.

**Vía principal — el equipo `docentes` de la organización.** Al vincular el curso (paso 3 del asistente, A-040) y antes de crear ningún repositorio:

1. Se crea, si no existe, el equipo `POST /orgs/{org}/teams` con `name = "docentes"`, `privacy = "closed"` y descripción con el nombre del curso. Su `team_slug` se persiste en **`equipo_github_curso`**.
2. **Cada miembro activo del curso con `curso.ver`** —es decir, todos: profesores y ayudantes— se incorpora a la organización y al equipo con `PUT /orgs/{org}/memberships/{login}` y `PUT /orgs/{org}/teams/{team_slug}/memberships/{login}`. Consumo del cupo: **≤ 15 invitaciones por curso, una sola vez**, presupuestado en §1.3.
3. **En el paso `CONFIGURANDO_ACCESOS` de cada repositorio** (A-092), junto a las invitaciones de los estudiantes, se ejecuta `PUT /orgs/{org}/teams/{team_slug}/repos/{org}/{repo}` con `{"permission": "pull"}`. **Una sola llamada por repositorio, no una por docente**, y el resultado se persiste en `acceso_docente_repositorio` con `via = TEAM`.
4. **Incorporar un ayudante nuevo después no toca ningún repositorio**: basta añadirlo al equipo. Retirarlo (A-025) lo saca del equipo, y **quitar a alguien de un equipo revoca el acceso concedido a través de ese equipo** **[DOC]** (`Q-2.6-56`). Ésa es la razón de fondo para preferir el equipo: **la revocación de R2.1.9 alcanza también a GitHub, con una llamada y sin recorrer 600 repositorios.**

**Vía de respaldo — colaborador individual con `pull`.** Si el equipo no puede crearse o poblarse —permiso `Members: write` no concedido, política de la organización, o la medición RA-02 sale negativa—, se ejecuta `PUT /repos/{org}/{repo}/collaborators/{login}` con `{"permission": "pull"}` por cada miembro con `curso.ver`, se persiste con `via = COLABORADOR`, y el checklist lo declara en el ítem 18. **Esta vía está cerrada por documentación**: `PUT collaborators` figura bajo `Administration: write` y bajo ningún otro encabezado, sin marca de permisos adicionales **[DOC]** (`Q-infraestructura-14`), y la App ya tiene ese permiso. Además, **como los docentes ya son miembros de la organización, la llamada responde `204` sin crear invitación y sin consumir cupo** **[DOC]** (`Q-2.3-32`, `Q-2.3-33`).

Al retirar a un ayudante por esta vía hay que recorrer sus accesos repositorio a repositorio con `DELETE /repos/{org}/{repo}/collaborators/{login}`, que se encola como trabajo `revocar_acceso_docente` y **es la razón por la que ésta es la vía de respaldo y no la principal**: la documentación advierte expresamente que un permiso de colaborador otorgado directamente **no se retira al salir de un equipo** **[DOC]** (`Q-2.6-56`).

**Modelo.** Tabla **`acceso_docente_repositorio (id, repositorio_id, membresia_id, via, estado, github_permission, concedido_en, revocado_en, ultimo_error)`**, con unicidad `(repositorio_id, membresia_id)` y `via ∈ {TEAM, COLABORADOR}`, `estado ∈ {PENDIENTE, CONCEDIDO, REVOCADO, ERROR}`. Con `via = TEAM` hay **una** fila lógica por repositorio con `membresia_id` nulo, porque el acceso es del equipo, no de la persona; con `via = COLABORADOR` hay una fila por persona.

**Nunca `write`, nunca `admin`.** El equipo docente recibe **`pull`** y sólo `pull`. Un corrector no debe poder empujar sobre el repositorio que corrige, ni borrar un tag de entrega, ni cambiar la visibilidad. Es coherente con la Ley 4 y con A-065.

**Estado visible y comprobable.** El repositorio **no llega a `OPERATIVO` mientras el equipo docente no tenga lectura concedida** (A-092), la barra de **R2.3.11** lo muestra como motivo propio `SIN_ACCESO_DOCENTE`, y la pantalla de corrección **verifica el acceso antes de pintar el enlace**: si el acceso está `PENDIENTE` o en `ERROR`, en lugar de un enlace que dará `404` se muestra el motivo y el botón de reintento. **Entregar un enlace roto es peor que decir por qué no está listo.**

**Comprobación en el checklist:** ítem 18 de A-041, bloqueante para **R2.4.8** y **R2.7.4**.

**Cupo:** contabilizado en §1.3 y en el presupuesto de A-117 como **una llamada adicional por repositorio** en la vía principal (600 repositorios ⇒ 600 llamadas repartidas al ritmo de A-117, no en ráfaga).

### A-066 · El repositorio base lo crea la aplicación, siempre

**R2.3.5** dice literalmente «permitir al profesor crear **desde la aplicación** un repositorio base». Se crea con `POST /orgs/{org}/repos` y se marca como plantilla con `PATCH /repos/{o}/{r}` (`is_template: true`, éxito documentado `200`) **[DOC]** (`Q-infraestructura-14`). **No se acepta vincular un repositorio base creado a mano.**

Motivo documental y decisivo: la garantía de acceso automático de A-063 cubre lo que la App **crea**, y **no cubre** un repositorio privado creado manualmente y no seleccionado **[DOC]** (`Q-2.1-36`, `Q-2.3-29`). Exigir que lo cree la App elimina de raíz el modo de fallo más difícil de diagnosticar del sistema —«el aprovisionamiento falla con 404 y el profesor no entiende por qué»— y permite aceptar instalaciones parciales.

**El repositorio base es opcional**, como exige **R2.3.5**: si la tarea no tiene base, los repositorios se crean vacíos con `POST /orgs/{org}/repos` y reciben un `README.md` inicial.

### A-067 · Archivos iniciales del repositorio base

**R2.3.6** se implementa con `PUT /repos/{o}/{r}/contents/{ruta}` y `DELETE` desde una pantalla propia: árbol de archivos, subir, reemplazar, renombrar, borrar y previsualizar texto. Cada operación queda en `bitacora`. La pantalla advierte que **los cambios en el repositorio base no se propagan a los repositorios ya creados**, porque `generate` copia una vez.

### A-068 · La rama por defecto se lee, no se supone

Se toma del campo `default_branch` de la respuesta `201` **[DOC]** (`Q-2.3-18`) y se persiste. La documentación **no** dice si el repositorio generado hereda la rama de la plantilla o aplica el ajuste de la organización, y **todo el monitoreo y todas las capturas dependen de ese nombre**. Suponer `main` es exactamente el tipo de error que produce un tablero vacío sin explicación.

### A-069 · Topics y descripción en cada repositorio creado

Cada repositorio recibe **tres topics** y una descripción estructurada. La revisión 1 ponía sólo dos y de ahí salía el agujero de A-097:

| Topic | Valor | Para qué |
|---|---|---|
| `gestor-tareas` | fijo | Marca de la aplicación |
| `curso-<slug>` | `curso.slug`, único globalmente (A-075) | Identifica el curso sin ambigüedad |
| `tarea-<slug-tarea>` | `tarea.slug`, único por curso | Identifica la tarea |

La **descripción** lleva, además del texto legible, un sufijo estructurado y estable que la aplicación sabe leer: `[gestor:{curso_slug}/{tarea_slug}/{tipo_sujeto}{id_sujeto}]` — por ejemplo `[gestor:icc4201-202620/t1-ordenamiento/e5310]`. **Es el dato que hace segura la adopción de A-097**, porque identifica curso, tarea **y sujeto**, y no sólo «esto lo creó la aplicación».

Sirve a cuatro cosas concretas: desambiguar visualmente en la organización, **permitir la adopción segura de A-097**, hacer verificable de un vistazo el estado de la organización durante la demostración, y permitir reconstruir la correspondencia repositorio ↔ sujeto desde GitHub si hiciera falta.

### A-170 · El repositorio de operaciones: quién lo crea, con qué credencial y en qué alcance

**De este repositorio cuelga entera la Ley 4**, porque en él vive el respaldo de la evidencia (A-016). La revisión 1 lo mencionaba sin decir quién lo creaba, con qué credencial se subía el respaldo ni cómo entraba en el alcance de la instalación —y la garantía de A-063 sólo cubre lo que la App **crea**, aceptando instalaciones con alcance `selected`. Queda cerrado así:

1. **Lo crea la App**, no una persona, con `POST /orgs/{org}/repos`, `name = "gestor-operaciones"`, `private: true`, en el **mismo paso 3 del asistente** en que se crea el equipo `docentes`. Por crearlo la App, **queda incluido automáticamente en el alcance de la instalación** **[DOC]** (`Q-2.3-29`, `Q-2.1-36`), que es exactamente el motivo por el que no se acepta uno creado a mano — el mismo argumento de A-066.
2. **El respaldo se sube con el token de instalación**, obtenido en caliente como cualquier otro (A-038), mediante **`PUT /repos/{org}/gestor-operaciones/contents/respaldos/{fecha}.sql.gz.enc`**, que usa `Contents: write`, permiso que la App ya declara en A-060 y que está cerrado por documentación. **No se usan *release assets***: exigirían un permiso adicional cuyo mínimo no está fijado, y el documento no apoya una pieza crítica en un **[MEDIR]** evitable. La revisión 1 los usaba; **queda retirado**.
3. **Está cifrado antes de salir del proceso** con la clave de A-034, de modo que el contenido del repositorio no es legible ni siquiera por un miembro de la organización.
4. **Recibe el topic `gestor-operaciones` y NO el topic `gestor-tareas`**, para que A-097 no pueda adoptarlo jamás y para que no aparezca en ninguna lista de repositorios de estudiantes.
5. **Acceso:** el equipo `docentes` **no** lo recibe; sólo la App escribe y sólo los propietarios de la organización leen. No contiene trabajo de estudiantes: contiene el volcado de la base.
6. **Retención:** 14 días, aplicada por el mismo trabajo `respaldo_base_datos`, que borra los ficheros más antiguos con `DELETE /repos/.../contents/...`. Es la sexta eliminación externa del sistema, y **se añade a la lista cerrada de A-030**. ~~y última~~ **ANULADA POR RG-191**: la lista pasa a **nueve** y las tres que faltaban están en **A-190**.
7. **Verificación, porque un respaldo que nadie restaura no es un respaldo:** una vez antes del 16 de septiembre y una vez antes del 6 de octubre se descarga el último fichero, se descifra y se restaura sobre el proyecto Supabase de `ensayo`, y el resultado se registra en `.workflow/mediciones/`.

### A-070 · Webhooks: suscripciones y trato

Suscripciones: **`push`, `create`, `delete`, `repository`, `member`, `installation`, `installation_repositories`**.

- **No existen `member_invite` ni `repository_invitation`** **[DOC]** (`Q-2.5-02`): la creación de una invitación **no genera evento**; sólo su aceptación lo hace, vía `member` con acción `added`.
- **Verificación de firma `X-Hub-Signature-256`** con HMAC-SHA256 en comparación de tiempo constante **sobre el cuerpo crudo, antes de parsear el JSON**. Un payload sin firma válida se rechaza con `401`, se registra y **nunca se procesa**.
- **Idempotencia por `X-GitHub-Delivery`**, con restricción única en `evento_webhook`. Una reentrega no duplica commits ni transiciones de estado.
- **El receptor valida, persiste y responde `202` en menos de 200 ms.** Todo el procesamiento ocurre después, en el trabajador. Un receptor que procesa en línea es un receptor que pierde entregas cuando GitHub lo considera lento.

### A-071 · Límites documentados del webhook que el diseño asume

- El array `commits` del payload de `push` trae **como máximo 2048** commits, y el propio payload remite a la Commits API para el resto **[DOC]** (`Q-2.5-04`). **No son 20**, como sugiere el estudio interno.
- GitHub **no entrega** el evento si el payload supera **25 MB**, si se empujan más de **5000 ramas** a la vez, o para tags cuando se empujan más de tres a la vez **[DOC]** (`Q-2.5-02`, `Q-2.5-04`).
- El relleno de un push grande se hace con `GET /repos/{o}/{r}/compare/{before}...{after}` **paginado**: el límite de 250 commits sólo aplica a la llamada sin paginar **[DOC]** (`Q-2.5-04`).

Por eso el webhook es la fuente rápida pero **nunca la única** (A-072).

### A-072 · Reconciliación con ETag como red de seguridad

Cada 15 minutos, por repositorio activo, `GET /repos/{o}/{r}/commits` con `If-None-Match` y el ETag guardado en `cursor_sincronizacion`. Una respuesta `304` **no descuenta del límite primario** si la petición va correctamente autenticada **[DOC]** (`Q-transversal-38`); que tampoco consuma límite **secundario** no está documentado **[MEDIR]**, por lo que el reconciliador respeta igualmente el techo de concurrencia.

La reconciliación existe porque hay un **hueco documentado** que ni el webhook ni `since` cubren: `since` filtra por **fecha del commit, no por fecha del push**, y el único campo que daba la fecha de push (`pushedDate` de GraphQL) está deprecado y retirado **[DOC]** (`Q-2.5-06`). **Un commit con fecha antigua empujado hoy es invisible para cualquier reconciliador basado en `since`.**

Estrategia adoptada: se guarda `ultimo_head_sha` por rama y se compara `ultimo_head_sha...head_actual`. Si `compare` devuelve `diverged` (reescritura de historia, `push --force`), se recorre el historial desde el head con `GET /commits` paginado hasta topar con un SHA conocido. **Los commits que desaparecen de la historia no se borran**: se marcan `huerfano=true`, porque forman parte del registro de actividad real y borrarlos falsearía el timeline.

Un **barrido completo nocturno** por repositorio cierra cualquier hueco restante.

### A-194 · La congelación del conjunto de permisos, y el plan de medición que la autoriza

**El conjunto de permisos de la GitHub App se congela el 11 de septiembre a las 20:00 con el resultado de RA-02, y no antes.** Hasta ese instante, la tabla de A-060 es el conjunto **de partida**.

**1 · `Workflows: write` se solicita si y sólo si la pasada B demuestra que `POST /git/refs` falla con `Contents: write` y funciona al añadirlo.** Si la pasada B sale positiva sólo con `Contents: write`, **`Workflows` no se pide** y el conjunto es exactamente el de A-060. El conjunto de candidatos queda escrito de antemano: `{Administration: write, Contents: write}` para `/generate` y `{Contents: write, Workflows: write}` para `/git/refs`, **de modo que el único candidato ajeno a A-060 es `Workflows: write`**. La mitigación de §19 RA-02 —«se instalan todos los permisos candidatos antes del 16 de septiembre»— **sólo se aplica si a las 20:00 del 11 de septiembre la medición no ha resuelto la ambigüedad**, nunca como atajo para no medir.

**2 · El plan de medición se amplía con cuatro endpoints**, todos usados por el diseño y ninguno con permiso mínimo cerrado por documentación. Se ejecutan **en la pasada A y en la pasada B** sobre la organización `<marca>-ensayo`, registrando código, cabeceras `x-ratelimit-*` y **cuerpo literal**:

1. `PUT /repos/{o}/{r}/topics` con los tres topics de A-069 —**obligatorio**, no opcional—.
2. `PUT /repos/{o}/{r}/actions/permissions` con `{"enabled": false}`.
3. `GET /orgs/{org}/rulesets`.
4. `GET /repos/{o}/{r}/rulesets`.

La pasada A captura además el objeto `commit` devuelto por `POST /git/commits` **sin enviar `author` ni `committer`** (A-196) y por `PUT /contents`, y la pasada D añade el paso de archivado.

**3 · La congelación no se firma sin el cruce documental.** **Ninguna llamada del diseño que no esté cerrada por documentación queda fuera del plan de medición** —que es la regla 4 de A-162—, y **la lista de llamadas medidas se compara, endpoint a endpoint, contra la lista de integración externa de todas las respuestas antes de las 20:00 del 11 de septiembre**. **Esa comparación es el paso que autoriza la congelación.** Su resultado vive en `.workflow/mediciones/RA-02.md` y **no es un resultado del checklist**.

**4 · `docs/permisos.md` se escribe después de la prueba**, con una fila condicional para `Workflows: write` y la salida literal que la justifica o la descarta. **El ítem 14 de A-192 compara los permisos concedidos contra ese conjunto congelado.**

**5 · Desenlace escrito de antemano si `PUT topics` no fuera concedible:** el marcador estructurado de la **descripción** —condición (d) de A-097, que viaja en el cuerpo de `POST /orgs/{org}/repos` y en `PATCH /repos/{o}/{r}`, ambos cerrados por documentación bajo `Administration: write`— **pasa a ser la única condición de identidad**, y las condiciones (a) y (c) se evalúan **contra ese mismo marcador**. Las condiciones (b) y (e) no cambian, la adopción sigue exigiendo las cinco, y su fuerza **no disminuye**: el marcador identifica curso, tarea **y sujeto**, que es más de lo que los topics identifican. **El modo degradado se activa y se consulta por el mecanismo único de A-193**, con la capacidad `ESCRIBIR_TOPICS`, y no por una bandera propia.

**6 · La política de producto no cambia en ninguno de los dos desenlaces:** la aplicación **no sube archivos bajo `.github/workflows/`**, el profesor los añade a mano en el repositorio base y `/generate` los copia. **No subir workflows es una decisión de producto, no una consecuencia del permiso**, y la validación de rutas sigue rechazando `.github/workflows/` con su mensaje, con permiso o sin él.

Sirve a **R2.1.5**, **R2.3.5**–**R2.3.9**, **R2.3.11**, **R2.4.5**–**R2.4.7**, **R2.5.3**.

### A-195 · Con qué credencial escriben los artefactos de `infra/` y el *workflow* de demostración

**No existe ninguna cuenta de máquina y no existe ningún PAT**, ni en la aplicación, ni en `infra/`, ni en GitHub Actions, ni como respaldo de desarrollo (A-038, A-176). Los **cuatro artefactos que escriben en organizaciones reales** se autentican con **token de instalación de una GitHub App, obtenido en caliente a partir de la clave privada**, exactamente igual que la aplicación:

| Artefacto | App e instalación | Credencial |
|---|---|---|
| `infra/prueba_permisos.py` | App de `ensayo`, sobre `<marca>-ensayo` | `GITHUB_ENSAYO_APP_ID` y `GITHUB_ENSAYO_APP_PRIVATE_KEY` como variables de entorno del ejecutor; **nunca en el repositorio, nunca en la base** |
| `infra/medicion_atribucion.py` | App de `ensayo`, sobre `<marca>-ensayo` | Igual |
| `infra/semilla_demo.py` | App de producción, sobre la organización del curso de demostración; y, para Canvas, el **token del profesor titular** de ese curso | Igual, más `CANVAS_TOKEN_DEMO`, pasado por entorno en cada ejecución |
| `.github/workflows/actividad_demo.yml` | App de producción, sobre la organización del curso de demostración | `GITHUB_APP_ID` y `GITHUB_APP_PRIVATE_KEY` como *secrets* del repositorio del equipo (A-011); el *workflow* **emite el token en cada ejecución** y lo usa como credencial de Git en la forma `https://x-access-token:<token>@github.com/{org}/{repo}.git` |

**No se añade un segundo camino de autenticación:** es el mismo que la aplicación ya mantiene, prueba y defiende, y su credencial caduca sola. **Ninguno de los cuatro persiste el token**; `prueba_permisos.py` y `medicion_atribucion.py` operan **sólo** sobre `<marca>-ensayo` y **borran lo que crean**.

**La única excepción declarada en todo el proyecto** es la identidad de los commits que `semilla_demo.py` y `actividad_demo.yml` producen: se firman deliberadamente con el correo `ID+login@users.noreply.github.com` del estudiante de demostración, para que la regla 2 `EMAIL_NOREPLY` de A-118 los atribuya. **La excepción está acotada a `infra/` y al curso de demostración, no existe en el código de la aplicación** (A-196), y **se declara por escrito en la memoria de entrega** junto al rótulo de curso de demostración. Todas las credenciales de la demostración se retiran el **1 de noviembre** (A-166 punto 7, A-176).

Módulo compartido `infra/_credenciales.py` emite el JWT y el token de instalación desde la clave privada, usado por los tres guiones y por el *workflow*; `gitleaks` sigue corriendo sobre árbol e historial en cada `push` (A-012).

Sirve a **R2.1.5**, **R2.5.1**, **R2.5.2**, **R2.5.7**, **R2.5.8**, **R2.5.10**, **R2.6.1**.

### A-196 · Todo commit escrito por la aplicación va a nombre de la cuenta `[bot]` de la instalación

En `POST /repos/{o}/{r}/git/commits`, cuando la aplicación escribe el commit inicial de un repositorio sin base, **no se envían los campos `author` ni `committer`** —exactamente igual que en `PUT /repos/{o}/{r}/contents/{ruta}`—, de modo que el commit queda a nombre de la **cuenta `[bot]` de la instalación** y **nunca a nombre de un integrante del equipo**.

Cuatro consecuencias, todas ya soportadas por esta carta:

1. `repositorio.commit_inicial_sha` es el SHA de ese commit, y **A-096 y A-171 lo excluyen del recuento** por ser andamiaje.
2. La cascada de atribución de **A-118** lo deja en `SIN_ATRIBUIR`, porque una cuenta de bot no tiene `mapeo_github` vigente: **nunca cuenta como participación de un estudiante**.
3. En el timeline de **A-124** aparece etiquetado como commit de la aplicación, como cualquier commit cuya `cuenta_github.tipo` sea `BOT`.
4. Se cumple **A-059**: el estudiante ve que quien creó su repositorio es la App del ramo, reconocible y distinguible de una suplantación.

**[MEDIR]**, en la pasada A de A-194. **Plan escrito si la medición sale distinta** —si omitir los campos produjera un error o una identidad vacía—: se envía `committer` explícito **con el nombre y el correo que esa misma medición revele para la cuenta de la App**, **nunca un correo inventado**, y `author` sigue omitido.

**Prueba de arquitectura:** falla la construcción si aparece un literal `"author"` o `"committer"` en el cuerpo de `POST /git/commits` o de `PUT /contents` dentro de `backend/`. La única excepción del proyecto es la de `infra/` y el curso de demostración (A-195).

Sirve a **R2.3.7**, **R2.5.2**, **R2.5.4**, **R2.5.8**.

### A-197 · Archivar: cinco guardas, rol de profesor, y `tarea.estado = ARCHIVADA` en la transacción final

**1 · «Archivar curso» no es un tercer camino a `ARCHIVADO`.** Se sigue entrando por los **dos caminos** de A-168 y no hay un tercero. Archivar el **curso** archiva la entidad `curso`, detiene sus trabajos periódicos, pasa la interfaz a sólo lectura y **no toca nada en Canvas ni en GitHub**. Antes de confirmar, `/cursos/{id}/ajustes` **enumera las tareas cuyos repositorios siguen sin archivar** y ofrece, como **segunda acción explícita y separada**, «archivar los repositorios de estas tareas», que **encola `archivar_repositorios` por cada tarea** y recorre el camino 1 con sus guardas completas.

**2 · Las guardas de `archivar_repositorios` son cinco, y rigen por igual venga el disparador de la tarea o del curso.** Viven en **una sola función** `puede_archivar(tarea) -> Resultado` de `backend/app/dominio/`, que devuelve **qué guarda falló**, y `archivar_repositorios` **la reevalúa antes de cada repositorio**:

| # | Guarda | Por qué |
|---|---|---|
| 1 | Bloqueada mientras exista alguna entrega de la tarea **sin versión vigente capturada** para ese sujeto **y con fecha de cierre en el futuro**; con una entrega ya vencida y sin capturar, se permite **con confirmación escrita** que nombra qué queda sin capturar | A-168 |
| 2 | **No se archiva un repositorio cuyo `acceso_docente_repositorio` no esté `CONCEDIDO`** | En un repositorio archivado no se pueden añadir ni quitar colaboradores ni equipos: archivarlo antes dejaría **R2.4.8** y **R2.7.4** rotos **sin arreglo posible** |
| 3 | **No se archiva mientras queden accesos de estudiante en `INVITADO`** | Quedarían congelados sin poder aceptar. La pantalla lo dice y ofrece resolverlos primero |
| 4 | **Aviso previo por Canvas**, catorce días antes y de nuevo al ejecutar, que es notificación obligatoria del sistema y **no tiene interruptor**; su exigibilidad con el canal caído la fija **A-227** | Nadie se entera de que su repositorio pasa a sólo lectura por descubrirlo |
| 5 | **Bloqueada mientras alguna corrección de la tarea no esté en estado terminal** —publicada, excusada o excluida— | Archivar lleva la tarea a `ARCHIVADA` y eso **detiene `reconciliar_notas_canvas`**, del que dependen el contraste de nota y la guarda de `posted_at`. Archivar dejaría una nota sin contrastar y sin quien la vuelva a mirar |

Antes de confirmar, la pantalla muestra **qué tareas quedarían sin archivar y por qué**, guarda por guarda. **La aplicación nunca archiva sola y nunca desarchiva sola.**

**3 · `tarea.estado = ARCHIVADA` es lo único que detiene la reconciliación de notas.** Archivar los repositorios de una tarea y archivar la tarea **son el mismo hecho y se escriben juntos**: `archivar_repositorios` pone `tarea.estado = ARCHIVADA` **en la transacción final, y sólo cuando todos los repositorios de la tarea están en `ARCHIVADO`, `INACCESIBLE` o `FUERA_DE_ALCANCE`**, dejando `bitacora` con `TAREA_ARCHIVADA`. Antes de esa transacción la tarea sigue `CERRADA` y **todos los trabajos de Canvas siguen corriendo sobre ella**. `reconciliar_notas_canvas` **lee `tarea.estado`, no `repositorio.estado`**. **Ningún otro trabajo cambia `tarea.estado`**, y la aplicación nunca lo revierte sola: se sale de `ARCHIVADA` sólo por el desarchivado humano sobre todos sus repositorios, que queda en `bitacora` con `REPOSITORIO_DESARCHIVADO`.

**4 · Permiso y rol.** Las dos acciones exigen **`tarea.administrar` y `rol_minimo='PROFESOR'`**, y son el **caso 4 de `ACCIONES_SOLO_PROFESOR`** (A-179). Los endpoints son `POST /api/cursos/{id}/tareas/{id}/archivar` y **`POST /api/cursos/{id}/tareas/{id}/desarchivar`** —se llama así y **no `desarchivar-para-acceso`**, para que la lista de rutas y el enrutador digan la misma palabra—, y **siguen a la bandera `tarea_archivado`** (A-233). `POST /api/cursos/{id}/archivar-repositorios` exige **`curso.administrar`**, que es NO CONCEDIBLE y por tanto exclusivo de un profesor, y sigue la misma bandera. **Los tres encolan y no llaman al proveedor dentro de la petición** (A-226).

**Por qué se cierra por rol:** archivar es **irreversible sin una segunda acción humana** y toca a la vez la evidencia capturada y el acceso del equipo docente.

Sirve a **R2.1.3**, **R2.1.8**, **R2.3.11**, **R2.4.5**, **R2.4.7**, **R2.4.8**, **R2.7.4**, **R2.7.6**, **R2.7.7**.

---

## 8. Modelo de datos

Convención: clave primaria propia `id UUID` (v7, ordenable por tiempo) en toda tabla; **nunca un identificador externo como clave primaria**, porque Canvas puede fusionar usuarios y GitHub puede renombrar cuentas. Identificadores externos en columnas propias con índice único donde corresponda, tipo `bigint`. Nombres de tablas y columnas en español, `snake_case`, singular. Toda tabla lleva `creado_en` y `actualizado_en`; las tablas espejo llevan además `sincronizado_en` y `origen ∈ {CANVAS, GITHUB, DOCENTE, SISTEMA}`.

### A-073 · Todo instante es `timestamptz` en UTC

**No existe una sola columna `timestamp` sin zona en el esquema.** Ningún cálculo de negocio —vencimiento de una fecha de cierre, ventana de actividad reciente, disparo de un recordatorio— usa hora local. La zona horaria es exclusivamente una propiedad de presentación (A-152). Es coherente con las dos APIs de origen, que devuelven ISO 8601 UTC con resolución de segundos **[DOC]** (`Q-2.4-18`, `Q-2.4-22`).

### A-074 · Regla de identidad

**Toda entidad espejada de un sistema externo se identifica por el identificador numérico de ese sistema, nunca por nombre, correo ni login.** Concretamente:

- El estudiante, por **`canvas_user_id`**. No por `sis_user_id`, que puede no venir **[DOC]** (`Q-2.2-30`); no por correo, cuya visibilidad para el token del profesor no está garantizada **[MEDIR]** (`Q-2.2-32`).
- La matrícula, por **`canvas_enrollment_id`**.
- La cuenta de GitHub, por **`github_user_id`** numérico, porque el `login` cambia y **el antiguo queda libre para que otra persona lo reclame** **[DOC]** (`Q-2.3-66`). El `login` se guarda como dato de presentación y se revalida.
- El repositorio, por **`github_repo_id`**, no por nombre.

`sis_user_id` y `login_id` se persisten cuando la instancia los entregue, **sólo como claves de reconciliación** para A-051, nunca como identidad.

### A-075 · Tablas de identidad de la aplicación — ANULADA POR RG-001, RG-002, RG-135, RG-198 y RG-200 en cuatro filas

> **Mandan ahora A-185** —`usuario` gana `cuenta_github_id` con único parcial y `email_canonico`; `invitacion_equipo` gana `email_canonico` y `github_login_declarado`, y su índice parcial pasa a `(curso_id, email_canonico)`—, **A-186** —`membresia_curso` gana `org_github_estado` de cinco valores, `org_github_invitada_en`, `org_github_alta_por_app` y `es_via_compartida`—, **A-191** —`credencial_canvas` gana `version_clave`— y **A-192** y **A-193** —`verificacion_vinculacion` pasa a cinco resultados, gana `origen` y `capacidad`, y su `item` recorre **21** códigos y admite nulo—. Todo lo demás de la tabla se conserva.

| Entidad | Campos clave | Unicidad y relaciones |
|---|---|---|
| `usuario` | `id`, `email` (citext), `google_sub`, `nombre`, `avatar_url`, `creado_en`, `ultimo_acceso_en`, `activo`, `desactivado_en`, `desactivado_por` | **único `email`**, **único `google_sub`**. CHECK: `email` termina en `@gmail.com` (**R2.1.2**). **`canvas_user_id` ya no vive aquí** (A-033). `activo` tiene dueño y semántica en A-165 |
| `identidad_canvas_usuario` | `id`, `usuario_id`, `canvas_base_url`, `canvas_user_id` (`bigint`), `verificada_en`, `ultima_confirmacion_en` | **único (`usuario_id`, `canvas_base_url`)** y **único (`canvas_base_url`, `canvas_user_id`)** (A-033). Una persona puede tener identidad en dos instancias de Canvas distintas |
| `sesion` | `id`, `usuario_id`, `token_hash`, `jti_oidc`, `creada_en`, `expira_en`, `revocada_en`, `agente`, `ip_truncada` | único `token_hash`; índice por `usuario_id`. **`version_membresias` retirada** (A-023) |
| `sesion_membresia` | `sesion_id`, `membresia_id`, `version`, `refrescada_en` | **PK (`sesion_id`, `membresia_id`)** (A-023). Sostiene **R2.1.9** con varias membresías por persona |
| `invitacion_equipo` | `id`, `curso_id`, `email`, `rol`, `permisos` (`text[]`), `token_hash`, `estado`, `invitada_por`, `expira_en`, `aceptada_en`, `revocada_en`, `revocada_por` | único parcial `(curso_id, email)` donde `estado='PENDIENTE'` (**R2.1.7**, **R2.1.8**). `permisos` es el conjunto que se vio en el formulario (A-021) |
| `curso` | `id`, `nombre`, `codigo`, `periodo`, `slug`, `zona_horaria`, `canvas_base_url`, `canvas_course_id`, `github_org_login`, `github_org_id`, `github_installation_id`, `estado`, `roles_estudiante_extra` (`jsonb`), `umbral_dias_sin_actividad`, `creado_por_usuario_id` | **único (`canvas_base_url`, `canvas_course_id`)** y **único `github_org_id` donde no nulo** (A-027); **único `slug`**, con CHECK `length(slug) <= 24` y `slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$'` (A-108); único `github_installation_id` donde no nulo (A-028). CHECK `length(codigo) <= 12`, `length(periodo) = 6` |
| `membresia_curso` | `id`, `curso_id`, `usuario_id`, `rol`, `permisos` (`text[]`), `estado`, `version`, `invitada_por`, `creada_en`, `retirada_en`, `retirada_por` | **único (`curso_id`, `usuario_id`)**. `rol ∈ {PROFESOR, AYUDANTE}`, `estado ∈ {ACTIVA, RETIRADA}`. **Invariante de A-165: todo curso `ACTIVO` conserva al menos una membresía `ACTIVA` de rol `PROFESOR`** |
| `credencial_canvas` | `id`, `curso_id`, `usuario_id`, `token_cifrado` (`bytea`), `nonce`, `huella`, `canvas_user_id`, `estado`, `orden_respaldo`, `consentimiento_en`, `ultimo_chequeo_en`, `ultimo_error` | único (`curso_id`, `usuario_id`); **único parcial `curso_id` donde `orden_respaldo = 0`** (A-035). `estado ∈ {VALIDA, INVALIDA, RETIRADA}` |
| `instalacion_github` | `installation_id` (PK, `bigint`), `curso_id`, `org_login`, `org_id`, `org_node_id`, `repository_selection`, `permisos_pendientes`, `suspendida`, `actualizada_en` | único `curso_id` (A-027, A-028) |
| `equipo_github_curso` | `id`, `curso_id`, `team_id` (`bigint`), `team_slug`, `estado`, `via_efectiva`, `creado_en`, `ultimo_error` | **único `curso_id`** (A-163). `via_efectiva ∈ {TEAM, COLABORADOR}`: registra qué vía quedó activa tras el ítem 18 del checklist |
| `verificacion_vinculacion` | `id`, `curso_id`, `item`, `resultado`, `detalle` (`jsonb`), `ejecutada_en`, `ejecutada_por` | índice `(curso_id, ejecutada_en)`. `resultado ∈ {CORRECTO, ADVERTENCIA, BLOQUEANTE, NO_VERIFICADO}`. `item` recorre los **19** de A-041 |

### A-076 · Tablas espejo de Canvas

| Entidad | Campos clave | Unicidad y notas |
|---|---|---|
| `seccion` | `id`, `curso_id`, `canvas_section_id`, `nombre`, `sis_section_id`, `nonxlist_course_id`, `estado`, `sincronizado_en` | **único (`curso_id`, `canvas_section_id`)**. `nonxlist_course_id` no nulo ⇒ *cross-listing* (A-053) |
| `estudiante` | `id`, `curso_id`, `canvas_user_id`, `nombre`, `nombre_ordenable`, `login_id`, `sis_user_id`, `email`, `estado`, `primera_vista_en`, `ultima_vista_en` | **único (`curso_id`, `canvas_user_id`)**. `estado ∈ {ACTIVO, INVITADO, INACTIVO, CONCLUIDO, RETIRADO}`, derivado (A-044) |
| `matricula` | `id`, `curso_id`, `estudiante_id`, `seccion_id`, `canvas_enrollment_id`, `tipo`, `role_id`, `estado`, `limitada_a_seccion`, `activa`, `sincronizado_en` | **único (`curso_id`, `canvas_enrollment_id`)**. Una fila por matrícula (A-044) |
| `conjunto_grupos` | `id`, `curso_id`, `canvas_group_category_id`, `nombre`, `no_colaborativo`, `sincronizado_en` | **único (`curso_id`, `canvas_group_category_id`)** |
| `grupo` | `id`, `curso_id`, `conjunto_grupos_id`, `canvas_group_id`, `nombre`, `slug`, `estado`, `sincronizado_en` | **único (`curso_id`, `canvas_group_id`)** |
| `pertenencia_grupo` | `id`, `grupo_id`, `estudiante_id`, `workflow_state`, `activa`, `sincronizado_en` | **único (`grupo_id`, `estudiante_id`)**. `workflow_state ∈ {accepted, invited, requested}` **[DOC]** (`Q-2.2-50`). **Sin unicidad `(conjunto_grupos, estudiante)`** (A-049) |

### A-077 · El puente Canvas ↔ GitHub — ANULADA POR RG-004 y RG-005 en la fila de `mapeo_github`

> **Manda ahora A-210.** `mapeo_github.cuenta_github_id` pasa a **nullable**, `estado` recibe `DEFAULT 'SIN_DATO'` y se añade el índice único parcial **`(curso_id, estudiante_id) WHERE estado <> 'SUPERSEDIDO'`**, que es lo que hace posible la fila anticipada. Los dos índices parciales sobre `estado = 'VIGENTE'` se conservan sin cambio.

| Entidad | Campos clave | Unicidad y notas |
|---|---|---|
| `cuenta_github` | `id`, `github_user_id` (`bigint`), `login`, `tipo`, `avatar_url`, `estado`, `revalidado_en` | **único `github_user_id`**. `tipo ∈ {USER, ORGANIZATION, BOT}`; `estado ∈ {VALIDA, RENOMBRADA, NO_EXISTE, ES_ORGANIZACION}` |
| `mapeo_github` | `id`, `curso_id`, `estudiante_id`, `cuenta_github_id`, `origen`, `confianza`, `evidencia` (`jsonb`), `estado`, `motivo_invalidacion`, `vigente_desde`, `vigente_hasta`, `creado_por`, `revalidado_en` | **único parcial (`curso_id`, `estudiante_id`) donde `estado='VIGENTE'`**; **único parcial (`curso_id`, `cuenta_github_id`) donde `estado='VIGENTE'`** |

### A-078 · El mapeo es *append-only* (Ley 2)

Corregir un mapeo **no actualiza la fila**: cierra la vigente (`estado='SUPERSEDIDO'`, `vigente_hasta`) y crea una nueva. Así se puede responder en la revisión de código y el 7 de octubre a «¿quién dijo que este repositorio era de este estudiante, cuándo y con qué evidencia?». `origen ∈ {AUTOSERVICIO_CANVAS, CARGA_DOCENTE, IMPORTACION_CSV}`; `evidencia` guarda el `canvas_submission_id`, el texto crudo, el actor y la marca de tiempo.

Sirve a **R2.2.4**, **R2.2.5**.

### A-079 · La doble unicidad del mapeo es una restricción de base de datos

Que dos estudiantes del mismo curso no puedan tener vigente la misma cuenta de GitHub **es un índice único parcial, no una comprobación en código**. Impide el error más caro del proyecto: dos estudiantes declarando la misma cuenta y uno recibiendo el repositorio del otro. La ingesta comprueba antes de insertar y produce la incidencia `GITHUB_DUPLICADO` con los dos candidatos; **la restricción es la última línea de defensa y su violación se captura y se convierte en la misma incidencia, nunca en un `500`.** Ninguno de los dos estudiantes recibe repositorio hasta que un docente resuelva.

### A-080 · Tareas, entregas y sujetos — ANULADA POR RG-017, RG-019 y RG-020 en dos filas

> **Mandan ahora A-203** —`entrega.estado_validacion` es un escalar cerrado de cuatro valores y la entrega gana `validaciones jsonb`, `advertencias text[]`, `ciclos_ausente` y `detectada_ausente_en`— y **A-208** —`repositorio_base.estado` se enumera con cinco valores y condiciona la activación de la tarea sólo cuando ésta declara base—. Las cuatro reglas de `orden`, `tipo` y entrega `FINAL` se conservan enteras.

| Entidad | Campos clave | Unicidad y notas |
|---|---|---|
| `tarea` | `id`, `curso_id`, `nombre`, `slug`, `modalidad`, `conjunto_grupos_id`, `repositorio_base_id`, `estado`, `creada_en` | **único (`curso_id`, `slug`)**. `modalidad ∈ {INDIVIDUAL, GRUPAL}`, derivada de Canvas y **congelada** tras el primer aprovisionamiento. `estado ∈ {BORRADOR, ACTIVA, INCONSISTENTE, CERRADA, ARCHIVADA}` |
| `entrega` | `id`, `tarea_id`, `curso_id`, `canvas_assignment_id`, `tipo`, `orden`, `nombre`, `slug`, `puntos_posibles`, `grading_type`, `publicada`, `moderated_grading`, `anonymous_grading`, `group_category_id_canvas`, `es_grupal_canvas`, `only_visible_to_overrides`, `due_at_base`, `all_day`, `huella_fechas` (`bytea`), `canvas_updated_at`, `estado_validacion`, `sincronizado_en` | **único (`curso_id`, `canvas_assignment_id`)**: una tarea de Canvas pertenece a una sola entrega. **único (`tarea_id`, `orden`)**, con `orden` **entero desde 1 y contiguo**. **único (`tarea_id`, `slug`)** (A-172). **único parcial `tarea_id` donde `tipo='FINAL'`**. `tipo ∈ {PARCIAL, FINAL}` |
| `visibilidad_entrega` | `entrega_id`, `estudiante_id`, `visible`, `origen`, `sincronizado_en` | **PK (`entrega_id`, `estudiante_id`)** (A-164). `origen ∈ {TODOS, ASSIGNMENT_VISIBILITY, OVERRIDE, SUPUESTO}` |
| `sujeto` | `id`, `tarea_id`, `tipo`, `estudiante_id`, `grupo_id`, `activo`, `creado_en`, `desactivado_en`, `motivo_desactivacion` | **único (`tarea_id`, `tipo`, `coalesce(estudiante_id, grupo_id)`)**. CHECK: exactamente uno de `estudiante_id`/`grupo_id` no nulo. **Se materializa por la regla de A-164, no por criterio de quien implemente** |
| `regla_fecha` | `id`, `entrega_id`, `alcance`, `canvas_override_id`, `seccion_id`, `grupo_id`, `estudiante_ids` (`bigint[]`), `due_at`, `unlock_at`, `lock_at`, `titulo`, `sincronizado_en` | **único (`entrega_id`, `canvas_override_id`)** donde no nulo; una fila `BASE` por entrega. Copia **cruda** de lo que devuelve Canvas |
| `fecha_efectiva` | `id`, `entrega_id`, `sujeto_id`, `due_at_utc`, `origen`, `regla_fecha_id`, `ambigua`, `calculada_en`, `estado`, `vigente_hasta` | **único parcial (`entrega_id`, `sujeto_id`) donde `estado='VIGENTE'`**. `origen ∈ {BASE, SECCION, GRUPO, ADHOC}` |
| `repositorio_base` | `id`, `tarea_id`, `github_repo_id`, `nombre`, `full_name`, `es_plantilla`, `rama_por_defecto`, `estado`, `creado_en` | **único `tarea_id`** (**R2.3.5**: nullable en `tarea`) |

**Una tarea con una sola entrega: la entrega única es `FINAL` con `orden = 1`.** La revisión 1 no lo decía y la unicidad parcial permitía cero finales, de modo que la mitad de los agentes habría creado `tipo=FINAL, orden=1` y la otra mitad `tipo=PARCIAL, orden=1`, divergiendo desde ahí el nombre del tag (A-104, A-172), las ventanas de A-122 y la línea de entregas de A-119. Las reglas, sin excepciones:

1. **`orden` arranca en 1** y es **contiguo**: al vincular la n-ésima entrega recibe `orden = n`. Desvincular una entrega **renumera** el resto en la misma transacción, y como el `orden` entra en el nombre del tag, la renumeración **sólo se permite mientras la tarea no tenga ninguna versión capturada**; después, desvincular está prohibido y sólo se puede marcar la entrega como excluida.
2. **`FINAL` es siempre la de mayor `orden`.** CHECK a nivel de aplicación y prueba automatizada.
3. **Una tarea `ACTIVA` tiene exactamente una entrega `FINAL`.** La unicidad parcial de base garantiza *como mucho una*; la validación de activación de la tarea garantiza *al menos una*. Una tarea en `BORRADOR` puede no tenerla todavía.
4. **La primera entrega vinculada nace `FINAL`.** Al vincular una segunda, la aplicación pregunta cuál de las dos es la final, con la anterior propuesta por defecto, y reordena. **Nunca lo decide en silencio.**

### A-081 · `sujeto` es la unidad de aprovisionamiento y de corrección

`sujeto` cuelga de **`tarea`**, y `repositorio` cuelga de **`sujeto`**. Nunca de `entrega`. Es la traducción literal de **R2.3.4** («todas las entregas asociadas a una misma tarea utilizarán el mismo repositorio»): todas las entregas de una tarea comparten los mismos sujetos y, por tanto, los mismos repositorios.

Y resuelve **R2.3.3** por construcción: como la modalidad vive en `tarea` y no en `entrega`, **es estructuralmente imposible representar dos entregas de la misma tarea con configuraciones distintas.**

Las **versiones capturadas**, en cambio, cuelgan de `(entrega, sujeto)`, que es la traducción literal de **R2.4.6**.

### A-082 · La fecha efectiva se materializa, no se calcula al vuelo

`fecha_efectiva` es una tabla con una fila por `(entrega_id, sujeto_id)`, su `due_at_utc`, el origen de la regla que ganó, si es ambigua y el instante en que se calculó. **No es una vista ni una función.** Tres requisitos dependen de que ese valor esté escrito y sea consultable:

- **R2.4.5** dispara la captura desde esta tabla: un trabajo que corre cada minuto necesita un índice sobre una columna, no recalcular la prioridad de overrides de todo el curso.
- **R2.6.7** programa los recordatorios de proximidad leyendo esta tabla.
- **R2.4.2** y **R2.4.3** se muestran al docente como «quién cierra cuándo», que es exactamente el contenido de esta tabla.

Además la hace **auditable**: cuando un docente pregunta por qué a un estudiante se le capturó a esa hora, la respuesta está en la fila, con el `regla_fecha_id` que la produjo.

### A-164 · Quién es sujeto de una tarea

**Es la regla de la que cuelgan R2.3.7, R2.3.10, R2.4.5 y R2.5.4, y la revisión 1 no la escribía en ninguna parte.** Sin ella, «los estudiantes o grupos de la tarea» no está definido y **R2.3.7** no es implementable de forma unívoca. Queda fijada aquí, y ninguna otra decisión la reinterpreta.

**Paso 1 — visibilidad, por entrega y por estudiante.** Para cada entrega vinculada se puebla `visibilidad_entrega`:

| Situación de la entrega en Canvas | Quién queda `visible = true` | `origen` |
|---|---|---|
| `only_visible_to_overrides = false` | **Todo estudiante del curso** con `estado ∈ {ACTIVO, INVITADO}` | `TODOS` |
| `only_visible_to_overrides = true` y la instancia devolvió `assignment_visibility` | **Exactamente los `canvas_user_id` de ese array** | `ASSIGNMENT_VISIBILITY` |
| `only_visible_to_overrides = true` y **no** llegó `assignment_visibility` | Los estudiantes alcanzados por algún `AssignmentOverride` de esa entrega, resueltos por `student_ids`, por sección o por grupo con las mismas reglas de A-055 | `OVERRIDE` |
| Ninguna de las anteriores es resoluble | **Nadie**, y se abre la incidencia `VISIBILIDAD_NO_RESOLUBLE` | `SUPUESTO` |

**No se supone visibilidad universal cuando `only_visible_to_overrides` es `true`**: suponerla crearía repositorios a estudiantes a los que la entrega no aplica, y borrarlos después está prohibido (A-030).

**Paso 2 — materialización del sujeto.** El conjunto de sujetos de una tarea es:

- **Tarea `INDIVIDUAL`:** un sujeto por cada `estudiante` del curso que cumpla **las dos** condiciones:
  1. `estudiante.estado ∈ {ACTIVO, INVITADO}` — se incluye `INVITADO` porque una matrícula invitada de Canvas es una matrícula legítima que casi siempre se activa, y esperar a que se active retrasaría la creación progresiva que exige **R2.3.10**. Se excluyen `INACTIVO`, `CONCLUIDO` y `RETIRADO`, y **siempre** el *Test Student* (A-050);
  2. es `visible = true` **en al menos una** de las entregas vinculadas a la tarea.
- **Tarea `GRUPAL`:** un sujeto por cada `grupo` del `conjunto_grupos` de la tarea que tenga **al menos un integrante `accepted`** (A-048) que a su vez cumpla las dos condiciones anteriores.

**Por qué «al menos una entrega» y no «todas».** **R2.3.4** obliga a que todas las entregas de una tarea compartan el mismo conjunto de repositorios. Si la visibilidad difiere entre entregas, exigir la intersección dejaría sin repositorio a estudiantes que sí deben entregar algo, lo que incumple **R2.3.7**; la unión no crea ningún efecto indebido, porque **la fecha efectiva y la captura se calculan por `(entrega, sujeto)`** y A-055 ya declara que un sujeto no visible para una entrega **no recibe fecha efectiva y no se le captura versión**. La unión da repositorio; la visibilidad por entrega decide qué se le exige en cada una. **Es la única combinación que cumple R2.3.4 y R2.3.7 a la vez.**

**Paso 3 — altas y bajas, que es lo que hace real R2.3.10.** El trabajo `materializar_sujetos` (A-114) recalcula el conjunto por curso tras cada `sync_roster`, `sync_grupos` o `sync_tareas_y_fechas`, en la misma transacción que encola el aprovisionamiento:

- **Sujeto nuevo** que aparece (matrícula nueva, grupo nuevo, override que le da visibilidad, mapeo que llega tarde): se inserta `activo = true` y entra en la máquina 2 por `ESPERANDO_INFORMACION`. **Sin que nadie pulse nada**, que es literalmente **R2.3.10**.
- **Sujeto que deja de cumplir la regla**: **no se borra nunca** (A-030). Pasa a `activo = false` con `motivo_desactivacion ∈ {SIN_MATRICULA_ACTIVA, SIN_VISIBILIDAD, GRUPO_DISUELTO, GRUPO_SIN_ACEPTADOS}`, y su repositorio pasa a `FUERA_DE_ALCANCE` conservando todo (A-095). Si vuelve a cumplirla, se reactiva la misma fila.
- **Un sujeto sin repositorio todavía** que se desactiva simplemente deja de aprovisionarse; no se crea nada y no se borra nada.

**Dónde se ve.** El recuento de sujetos activos, los desactivados con su motivo y los que están esperando información aparecen en la pantalla de tarea (**R2.3.11**), en la barra de **R2.5.5** y en Pendientes (**R2.2.6**). **Un sujeto desactivado nunca desaparece de la interfaz en silencio.**

### A-083 · Repositorios y accesos — ANULADA POR RG-013, RG-014, RG-015, RG-010 y RG-182 en sus tres filas

> **Mandan ahora A-202** —las unicidades `sujeto_id` y `(curso_id, nombre)` pasan a **parciales** con `WHERE estado <> 'INACCESIBLE'`, y `repositorio` gana `motivo`, `inaccesible_desde`, `nombre_canonico`, `reemplaza_a_id`, `recreado_en`, `archivado_en` y `archivado_por`— y **A-212** —`acceso_repositorio` gana las ocho columnas de la revocación—. `UNIQUE (github_repo_id)` sigue siendo total, y la fila de `acceso_docente_repositorio` se conserva tal cual.

| Entidad | Campos clave | Unicidad y notas |
|---|---|---|
| `repositorio` | `id`, `curso_id`, `tarea_id`, `sujeto_id`, `github_repo_id`, `nombre`, `full_name`, `url_html`, `rama_por_defecto`, `estado`, `motivo`, `clase_error`, `error_codigo`, `error_mensaje_literal`, `commit_inicial_sha`, `intentos`, `proximo_intento_en`, `creado_en`, `listo_en` | **único `sujeto_id`**; **único `github_repo_id`** donde no nulo; **único (`curso_id`, `nombre`)** |
| `acceso_repositorio` | `id`, `repositorio_id`, `estudiante_id`, `cuenta_github_id`, `estado`, `github_invitation_id`, `invitacion_html_url`, `invitado_en`, `aceptado_en`, `reenvios`, `ultimo_reenvio_en`, `ultimo_error` | **único (`repositorio_id`, `estudiante_id`)**. Es el acceso del **estudiante**, con `push` (A-064) |
| `acceso_docente_repositorio` | `id`, `repositorio_id`, `membresia_id` (nullable si `via='TEAM'`), `via`, `estado`, `github_permission`, `concedido_en`, `revocado_en`, `ultimo_error` | **único (`repositorio_id`, `coalesce(membresia_id, '00000000-…')`)** (A-163). `via ∈ {TEAM, COLABORADOR}`, `estado ∈ {PENDIENTE, CONCEDIDO, REVOCADO, ERROR}`, `github_permission` siempre `pull` |

### A-084 · Versiones de entrega, el corazón de R2.4 — ANULADA POR RG-025, RG-026, RG-028 y RG-195 en su lista de columnas

> **Manda ahora A-204.** `version_entrega` gana `tag_estado`, `tag_motivo`, `origen_captura`, `creada_por_usuario_id`, `motivo_manual`, `motivo_repositorio` e **`integrantes jsonb NOT NULL` con índice GIN**; `repositorio_id` pasa a **nullable**; `estado` queda en **seis valores terminales** y `motivo` en **cinco**. Las dos unicidades se conservan.

| Entidad | Campos clave | Unicidad y notas |
|---|---|---|
| `version_entrega` | `id`, `entrega_id`, `sujeto_id`, `repositorio_id`, `intento`, `fecha_corte_utc`, `rama`, `commit_sha` (char 40), `commit_tree_sha`, `commit_fecha_committer`, `commit_fecha_autor`, `commit_mensaje`, `tag_nombre`, `tag_creado`, `tag_error`, `estado`, `vigente`, `reemplaza_a_id`, `motivo`, `advertencias` (`text[]`), `verificacion` (`jsonb`), `capturada_en` | **único parcial (`entrega_id`, `sujeto_id`) donde `vigente`**; único (`entrega_id`, `sujeto_id`, `intento`). **Filas inmutables tras la captura** |

### A-085 · La versión registrada es inmutable (Ley 2) — ANULADA POR RG-026 y RG-188 en su formulación absoluta

> **Manda ahora A-204.** La fila **nunca se borra** y la evidencia —SHA, árbol, fechas, mensaje, integrantes congelados, fecha de corte— **nunca se toca**; lo que queda superado es «la fila nunca se actualiza»: hay una **lista cerrada de siete columnas mutables** y **dos transiciones de `estado`**, y ninguna de ellas altera evidencia.

**R2.4.7** exige que las versiones ya registradas se mantengan correctamente aunque siga habiendo actividad en el repositorio. La decisión es más fuerte: **la fila de `version_entrega` nunca se actualiza ni se borra.**

Si la fecha de cierre cambia en Canvas después de una captura (**R2.4.4**), no se corrige la fila: se inserta una fila nueva con `intento = anterior + 1` y `reemplaza_a_id` apuntando a la anterior, la anterior queda `vigente = false` con su `motivo`, y la interfaz **muestra ambas**. Así la trazabilidad sobrevive a los cambios de fecha y el corrector siempre puede ver qué se capturó y por qué cambió.

### A-086 · Actividad — ANULADA POR RG-006, RG-029 y RG-030 en tres filas

> **Mandan ahora A-201** —el índice de `identidad_git` pasa a **parcial** (`WHERE estado <> 'SUPERSEDIDA'`), se añade el índice no único `(curso_id, email_normalizado)` y la tabla gana siete columnas—, **A-205** —existe la tabla nueva `autoria_commit`, `commit` gana `motivo_exclusion`, `autor_es_bot` y `autor_es_docente`, `metrica_repositorio_dia` gana `commits_de_bot` y `commits_docentes`, y `participacion_entrega` gana `commits_coautorados` y `commits_sin_atribuir_repo`—. `cursor_sincronizacion` y `evento_webhook` se conservan tal cual.

| Entidad | Campos clave | Unicidad y notas |
|---|---|---|
| `identidad_git` | `id`, `repositorio_id`, `email_normalizado`, `nombre_visto`, `cuenta_github_id` (nullable), `estudiante_id` (nullable) | **único (`repositorio_id`, `email_normalizado`)**. Existe para no acusar por error a nadie: agrupa autores no resueltos |
| `commit` | `id`, `repositorio_id`, `sha` (char 40), `rama_detectada`, `mensaje_resumen`, `autor_nombre`, `autor_email`, `autor_github_user_id`, `committer_github_user_id`, `fecha_autor`, `fecha_committer`, `n_padres`, `es_merge`, `via_web`, `adiciones`, `eliminaciones`, `archivos_tocados`, `identidad_git_id`, `estudiante_id`, `regla_atribucion`, `huerfano`, `origen_ingesta`, `ingresado_en` | **único (`repositorio_id`, `sha`)**: la idempotencia de la ingesta es **estructural** |
| `evento_push` | `id`, `repositorio_id`, `delivery_id`, `ref`, `before_sha`, `after_sha`, `n_commits_payload`, `completado`, `recibido_en` | índice por `repositorio_id` |
| `evento_webhook` | `id`, `delivery_id`, `evento`, `accion`, `firma_valida`, `payload` (`jsonb`, **truncado a 64 KB**), `payload_bytes`, `payload_truncado`, `recibido_en`, `procesado_en`, `estado`, `error` | **único `delivery_id`** (A-070). El truncado y su motivo están en A-090 |
| `metrica_repositorio_dia` | `repositorio_id`, `dia` (date, **en la zona horaria del curso** — A-171), `commits`, `commits_merge`, `commits_excluidos`, `autores_distintos`, `adiciones`, `eliminaciones`, `recalculada_en` | **PK (`repositorio_id`, `dia`)**. `commits` cuenta **sólo commits contables** con las mismas exclusiones que `participacion_entrega` (A-171) |
| `participacion_entrega` | `entrega_id`, `repositorio_id`, `estudiante_id`, `commits`, `adiciones`, `eliminaciones`, `dias_activos`, `primer_commit_en`, `ultimo_commit_en` | **PK (`entrega_id`, `repositorio_id`, `estudiante_id`)**. `commits` son **contables** (A-171) |
| `cursor_sincronizacion` | `id`, `curso_id`, `recurso`, `referencia`, `etag`, `ultimo_head_sha`, `per_page_medido`, `ultimo_exito_en`, `ultimo_backfill_en`, `estado`, `ultimo_error` | **único (`curso_id`, `recurso`, `referencia`)** |

### A-087 · Corrección, comunicación e infraestructura del dominio — ANULADA POR RG-034, RG-036, RG-041, RG-042, RG-045, RG-046 y RG-192 en su recuento y en cinco filas

> **Mandan ahora A-198** —el censo pasa de **47 a 70 entidades**—, **A-206** —`asignacion_correccion.estado` **se elimina** y nace `estado_canvas_submission`—, **A-224** —`mensaje_saliente` gana `generacion`, `reemplaza_a_id`, `motivo_estado`, `reserva` y las columnas de despacho—, **A-229** —`informe_diario` pierde `hay_tareas_activas` y gana seis columnas—, **A-207** —`incidencia` gana `silenciada_hasta`, `motivo_silenciamiento` y `silenciada_por`— y **A-215** —`trabajo` gana `motivo_cancelacion`—. La frase «Total: 47 entidades» de esta decisión queda superada por A-198.

| Entidad | Campos clave | Unicidad y notas |
|---|---|---|
| `asignacion_correccion` | `id`, `entrega_id`, `sujeto_id`, `membresia_id` (corrector, nullable), `estado`, `asignada_por`, `asignada_en`, `iniciada_en` | **único (`entrega_id`, `sujeto_id`)**: un corrector por entrega y sujeto (**R2.7.1**) |
| `correccion` | `id`, `entrega_id`, `sujeto_id`, `estado`, `nota_local`, `rubrica_local` (`jsonb`), `comentario`, `corrector_usuario_id`, `publicada_en`, `intentos`, `ultimo_error` | **único (`entrega_id`, `sujeto_id`)** (**R2.7.7**) |
| `publicacion_nota` | `id`, `correccion_id`, `estudiante_id`, `intento`, `payload_enviado` (`jsonb`), `late_policy_status_enviado`, `codigo_http`, `respuesta` (`jsonb`), `grader_id_reportado`, `score_devuelto`, `entered_score_devuelto`, `estado`, `intentada_en` | **único (`correccion_id`, `estudiante_id`, `intento`)**. *Append-only* (**R2.7.6**) |
| `regla_comunicacion` | `id`, `curso_id`, `tarea_id` (**nullable**), `alcance`, `evento`, `activa`, `actualizada_por`, `actualizada_en` | **único (`curso_id`, `coalesce(tarea_id, '00000000-…')`, `evento`)** (**R2.6.7**). `alcance ∈ {CURSO, TAREA}`: los eventos de curso llevan `tarea_id` nulo (A-130) |
| `mensaje_saliente` | `id`, `curso_id`, `canal`, `clave_idempotencia`, `destinatario`, `referencia` (`jsonb`), `plantilla`, `cuerpo_renderizado`, `estado`, `proveedor_id`, `canvas_id_resultante`, `intentos`, `ultimo_error`, `enviado_en` | **único `clave_idempotencia`**. `canal ∈ {CANVAS_CONVERSACION, CANVAS_ANUNCIO, CANVAS_COMENTARIO, CORREO}` |
| `suscripcion_informe` | `curso_id`, `usuario_id`, `activa`, `actualizada_en` | **PK (`curso_id`, `usuario_id`)** (**R2.6.3**) |
| `informe_diario` | `id`, `curso_id`, `fecha`, `hay_tareas_activas`, `contenido` (`jsonb`), `contenido_html`, `contenido_texto`, `generado_en` | **único (`curso_id`, `fecha`)** (**R2.6.1**) |
| `incidencia` | `id`, `curso_id`, `tipo`, `severidad`, `sujeto_tipo`, `sujeto_id`, `titulo`, `detalle` (`jsonb`), `accion_sugerida`, `abierta`, `detectada_en`, `resuelta_en`, `resuelta_por` | **único parcial (`curso_id`, `tipo`, `sujeto_tipo`, `sujeto_id`) donde `abierta`**. `severidad ∈ {BLOQUEANTE, ADVERTENCIA, INFORMATIVA}` |
| `trabajo` | `id`, `tipo`, `clave_idempotencia`, `curso_id`, `payload` (`jsonb`), `estado`, `intentos`, `max_intentos`, `proximo_intento_en`, `tomado_por`, `tomado_en`, `ultimo_error`, `coste_api` (`jsonb`), `creado_en`, `terminado_en` | **índice único parcial `clave_idempotencia` donde `estado IN ('PENDIENTE','EN_CURSO','REINTENTAR','BLOQUEADO','ESPERANDO_CREDENCIAL','ESPERANDO_LIMITE')`** |
| `trabajo_periodico` | `id`, `tipo`, `curso_id`, `cadencia_segundos`, `proxima_ejecucion`, `ultima_ejecucion`, `activo` | único (`tipo`, `curso_id`) |
| `sincronizacion` | `id`, `curso_id`, `ambito`, `iniciada_en`, `terminada_en`, `resultado`, `contadores` (`jsonb`), `coste` (`jsonb`), `error` | `resultado ∈ {OK, PARCIAL, TRUNCADA, FALLIDA}` |
| `bitacora` | `id`, `curso_id`, `actor_usuario_id`, `accion`, `entidad`, `entidad_id`, `antes` (`jsonb`), `despues` (`jsonb`), `ocurrido_en` | *Append-only*; índice `(curso_id, ocurrido_en)` (A-029) |

**Total: 47 entidades.** La revisión 2 añade cinco: `identidad_canvas_usuario` (A-033), `sesion_membresia` (A-023), `equipo_github_curso` y `acceso_docente_repositorio` (A-163), y `visibilidad_entrega` (A-164). Ninguna se añadió por gusto: cada una sostiene un requisito que sin ella no se cumplía o una regla que sin ella era ambigua.

El catálogo cerrado de tipos de incidencia se amplía en consecuencia, y la lista completa está en **A-088**.

### A-088 · `incidencia` es una sola tabla que alimenta cuatro requisitos — ANULADA POR RG-190 en su catálogo

> **Manda ahora A-207.** La regla de una sola tabla y el argumento de las cuatro verdades divergentes se conservan enteros; lo que queda superado es el número: el catálogo pasa de **37 a 51 tipos**, con las catorce adiciones enumeradas, su `sujeto_tipo` único y **la lista escrita de los tipos que no entran**.

El panel de Pendientes de **R2.2.6**, el estado de repositorios de **R2.3.11**, el resumen de **R2.5.5** y el contenido del informe diario de **R2.6.2** leen **la misma tabla**. Modelar cuatro listas separadas produciría cuatro verdades divergentes, y la divergencia se vería en la demostración.

**Catálogo cerrado de tipos** —ningún código fuera de esta lista, y añadir uno es una decisión que se registra aquí—:

`SIN_MAPEO`, `MAPEO_NO_RESUELTO`, `GITHUB_DUPLICADO`, `GITHUB_CUENTA_PERDIDA`, `GITHUB_LOGIN_REASIGNADO`, `ESTUDIANTE_SIN_GRUPO`, `ESTUDIANTE_EN_DOS_GRUPOS`, `ESTUDIANTE_EN_DOS_SECCIONES`, `POSIBLE_FUSION_CANVAS`, `GRUPO_INCOMPLETO`, `ROSTER_SOSPECHOSO`, `ROSTER_TRUNCADO`, `SECCION_CROSS_LISTED`, `OVERRIDE_NO_INTERPRETABLE`, `DISCREPANCIA_FECHAS`, `REPO_BLOQUEADO_POLITICA`, `REPO_ERROR_PERMANENTE`, `REPO_NOMBRE_OCUPADO`, `INVITACION_NO_ACEPTADA`, `INVITACION_EXPIRADA`, `VERSION_REVISAR`, `VERSION_ERROR`, `SIN_ACTIVIDAD`, `SIN_PARTICIPACION`, `CANVAS_CREDENCIAL_INVALIDA`, `GITHUB_PERMISOS_PENDIENTES`, `LIMITE_API_ALCANZADO`, `PERIODO_CALIFICACION_CERRADO`, `TAREA_INCONSISTENTE`, `CORRECCION_SIN_CORRECTOR`, `CUOTA_CORREO_AGOTADA`,
**`SIN_ACCESO_DOCENTE`** (A-163), **`VISIBILIDAD_NO_RESOLUBLE`** (A-164), **`MODALIDAD_INCOMPATIBLE`** (A-138), **`PLANIFICADOR_DETENIDO`** (A-112), **`RESPALDO_FALLIDO`** (A-170), **`BASE_CERCA_DEL_LIMITE`** (A-090).

**Son 37 tipos.** Los seis últimos se añadieron en la revisión 2 con las decisiones que los necesitan; ninguno se usa sin estar en esta lista.

### A-089 · Qué se sincroniza y qué se consulta en vivo

**Se sincroniza y persiste** (Ley 1): roster, secciones, matrículas, conjuntos de grupos, grupos y pertenencias; tareas, entregas, overrides y fechas efectivas; estado de repositorios, invitaciones y colaboradores; commits, métricas diarias y participación; versiones capturadas; estado de corrección; mensajes enviados; incidencias.

**Se consulta en vivo, y sólo esto:**

| Qué | Cuándo | Por qué no se espeja |
|---|---|---|
| Checklist de vinculación (**R2.1.6**) | durante el asistente y al pulsar «volver a verificar» | su valor es decir «esto está bien **ahora**» |
| Rúbrica de la entrega (**R2.7.5**) | al abrir la pantalla de corrección **y de nuevo justo antes de publicar** | calificar contra una rúbrica que el profesor cambió hace diez minutos produciría identificadores inexistentes. Caché de 15 min |
| Períodos de calificación y `late_policy` | justo antes de publicar | condicionan el resultado de la escritura (A-140) |
| Validación de un login de GitHub | al teclearlo en la carga docente | es una comprobación interactiva |
| Estado de una invitación concreta | al pulsar «reintentar» en esa fila | es la acción del usuario sobre ese dato |
| `GET /rate_limit` | en el panel de operación | es el dato de diagnóstico |

**Escrituras externas síncronas desde una pantalla.** Son **seis, están enumeradas en A-169** y ninguna más es legal. La revisión 1 decía aquí «escrituras (nota, mensaje, anuncio, comentario) al confirmarlas», dejaba fuera la prueba de escritura del checklist, la creación del repositorio base, la carga de archivos y la creación de la tarea de registro, y A-125 afirmaba a la vez que **ninguna** vista escribe hacia fuera salvo la nota. Las tres reglas juntas no dejaban ninguna implementación legal para **R2.3.5**, **R2.3.6** ni **R2.2.4**. **A-169 las legaliza explícitamente y con contrato.**

**Nunca se persiste:** el token de Canvas en claro, ningún token de instalación de GitHub, y el **contenido** de los repositorios (sólo metadatos y SHA).

**Cualquier otra consulta en vivo desde una vista es un defecto de arquitectura y se rechaza en revisión de código.** Cada vista muestra la antigüedad del dato («sincronizado hace 3 min») y un botón de sincronización manual que **encola** un trabajo, nunca que llama a la API dentro de la petición HTTP.

### A-090 · Volumen, retención y presupuesto de 500 MB — ANULADA POR RG-047 en su tabla de retención

> **Manda ahora A-199.** El truncado a 64 KB, la retención de 7 días del cuerpo y los dos escalones de freno se conservan enteros; lo que queda superado es la tabla de retención, que pasa de **5 a 18 filas** con las 23 entidades nuevas, y el presupuesto, que se recalcula en **≈ 160 MB**.

Un curso de 200 estudiantes con 3 tareas, 6 entregas y 8 semanas de actividad produce del orden de 600 repositorios, 30 000 commits, 50 000 filas de métrica diaria y 40 000 eventos de webhook.

**La aritmética de la revisión 1 estaba mal y aquí se corrige.** Decía «por debajo de 250 MB» sin contar el peso real de los cuerpos crudos: `evento_webhook.payload` se persistía como `jsonb` **completo** con retención de 30 días, y el propio documento cita en A-071 que un payload puede llegar a **25 MB** **[DOC]** (`Q-2.5-02`, `Q-2.5-04`). Con 40 000 eventos, un tamaño medio de sólo 20 KB ya son 800 MB dentro de la ventana de retención: el margen no se estrechaba, **se evaporaba**. Tres decisiones lo cierran:

1. **El cuerpo se trunca al persistirlo.** Se guardan los primeros **64 KB** del JSON, más `payload_bytes` con el tamaño real recibido y `payload_truncado` como bandera. Es seguro porque **lo que importa de un `push` ya se extrae al procesarlo** y vive normalizado en `commit` y `evento_push`; el cuerpo crudo es material de diagnóstico, no evidencia. Un payload truncado **nunca impide el procesamiento**: el relleno se hace con `compare` paginado (A-071), que es lo que ya se hacía para los push grandes.
2. **La retención del cuerpo baja de 30 días a 7.** La cabecera —`delivery_id`, evento, acción, firma válida, tiempos, estado— **se conserva indefinidamente**, de modo que la trazabilidad de qué llegó y cuándo no se pierde.
3. **Hay un freno automático.** El trabajo diario de A-007 mide `pg_database_size`; al superar **300 MB** (60 %) avisa por correo con cargo a la reserva operativa de A-133 y **la purga acorta por sí sola la retención del cuerpo a 3 días**; al superar **400 MB** (80 %) abre la incidencia bloqueante `BASE_CERCA_DEL_LIMITE` y deja de persistir cuerpos nuevos, conservando cabeceras. **Ningún dato de evidencia se toca en ninguno de los dos escalones.**

Presupuesto recalculado con estas reglas: `commit` ~30 000 × 1 KB ≈ 30 MB; `metrica_repositorio_dia` 50 000 × 120 B ≈ 6 MB; `evento_webhook` con cabecera indefinida 40 000 × 400 B ≈ 16 MB, más los cuerpos de 7 días acotados a 64 KB y en la práctica muy por debajo, ≈ 40 MB en el peor caso realista; el resto de tablas, índices incluidos, ≈ 60 MB. **Total del orden de 150 MB, con el peor caso acotado por construcción**, no por optimismo.

Retención explícita, aplicada por el trabajo de purga:

| Tabla | Retención |
|---|---|
| `evento_webhook.payload` | **7 días**, truncado a 64 KB al escribirse; **3 días** si la base supera 300 MB. La **cabecera se conserva indefinidamente** |
| `trabajo` en estado terminal | 30 días |
| `sincronizacion` | 90 días |
| Ficheros de respaldo en `gestor-operaciones` (A-170) | 14 días |
| `commit`, `version_entrega`, `bitacora`, `publicacion_nota` | **sin purga**: son evidencia |

### A-198 · Censo cerrado de 70 entidades, con marca parcial y final

**El sistema tiene 70 entidades**: las **47** de A-075 a A-087 más **23 nuevas**. **§8 pasa de «Total: 47 entidades» a «Total: 70 entidades»**, una sola vez y aquí. **`integrante_version_entrega` no existe** (A-204) y **`commit_autoria` no existe** (A-205): toda respuesta que las cite lee `version_entrega.integrantes` y `autoria_commit`.

**La lista es cerrada:** añadir una entidad es una decisión que se registra en esta carta, igual que añadir un tipo de incidencia. Se declara en **`backend/app/dominio/censo.py`** y una prueba de arquitectura **falla la construcción si existe un modelo SQLAlchemy que no está en ella**. `bitacora.entidad` se valida contra este censo más el valor `sistema` (A-184).

**Las 23 nuevas.** Trece **se escriben antes del 16 de septiembre** —criterio de A-158 punto 5: una tabla es de la parcial si un requisito demostrado ese día escribe en ella, **o** si añadirla después obligaría a migrar filas ya creadas o a reconstruir un hecho que ya no será observable—:

| Tabla nueva | Por qué se escribe desde la parcial |
|---|---|
| `assignment_canvas` | **R2.3.1**–**R2.3.4** completos el 16-sep; su `payload` es el espejo del assignment vinculado y no se reconstruye hacia atrás |
| `archivo_repositorio_base` | **R2.3.5** y **R2.3.6** completos el 16-sep |
| `intento_instalacion_github` | La vinculación de A-040 y A-058 ocurre el 16-sep y sus intentos son evidencia del checklist |
| `plantilla_mensaje` | **R2.3.12** completo el 16-sep: el mensaje por integrante sale de plantilla |
| `verificacion_canal` | Ítem del checklist de A-192, ejecutado el 16-sep |
| `salud_proveedor_curso` | El correo transaccional se usa el 16-sep para **R2.1.7**; su salud alimenta A-177 |
| `cubo_tasa` | El freno de A-219 y los limitadores de A-182 operan desde el primer día |
| `presupuesto_api` | Sin él no hay control de cuota el día de la creación masiva (A-219) |
| `estado_sistema` | A-158 punto 6, panel de operación |
| `resultado_invariante` | A-158 punto 6; los invariantes 15 a 17 de A-181 escriben en ella |
| `respaldo` | A-158 punto 3: respaldo diario funcionando y restauración probada |
| `exposicion_entrega` | La guarda del asistente es de la parcial |
| `autoria_commit` | La ingesta del 16-sep en adelante debe escribirla **desde el primer commit**; los co-autores llegan del enriquecimiento GraphQL en el mismo lote, y reconstruirlos después obliga a reconsultar la API commit a commit |

**Las diez restantes empiezan a escribirse con la entrega final:** `estado_canvas_submission`, `nota_interna_correccion`, `resumen_tarea`, `preferencia_vista`, `hito_repositorio`, `supresion_comunicacion`, `ventana_supresion`, `cambio_fecha`, `cambio_pendiente`, `accion_ui`.

> **El reparto parcial/final dice QUÉ TABLAS SE ESCRIBEN antes del 16 de septiembre, no cuándo se crean.** **Las 70 se crean en la migración inicial** (A-175): crear diez tablas vacías cuatro semanas antes no cuesta nada y elimina la única migración que podía fallar delante del evaluador.

Sirve a todos los requisitos de la entrega parcial y, por dependencia de esquema, a los de la final.

### A-199 · Retención y presupuesto de las 23 tablas nuevas

**La tabla de retención de A-090 crece de 5 a 18 filas.** Ninguna entidad queda sin política:

| Tabla | Retención | Volumen estimado por curso |
|---|---|---|
| `autoria_commit` | **sin purga**: es evidencia de atribución | ≈ 36 000 filas × 80 B ≈ 3 MB |
| `estado_canvas_submission` | **sin purga**; se reescribe en cada sincronización | ≈ 1 200 filas × 150 B ≈ 0,2 MB |
| `exposicion_entrega` | **sin purga**: derivada, una fila por `(entrega, sujeto)` | ≈ 1 200 filas ≈ 0,2 MB |
| `assignment_canvas` | `payload` **truncado a 64 KB** al escribirse, igual que `evento_webhook`; cabecera sin purga | ≈ 0,4 MB |
| `archivo_repositorio_base` | sin purga; **metadatos y `sha`, nunca el contenido del archivo** | decenas de filas |
| `cambio_fecha`, `hito_repositorio`, `resumen_tarea`, `nota_interna_correccion` | **sin purga**: son evidencia o material del docente | < 1 MB en total |
| `plantilla_mensaje`, `preferencia_vista`, `verificacion_canal`, `salud_proveedor_curso`, `estado_sistema`, `supresion_comunicacion`, `ventana_supresion`, `cambio_pendiente`, `intento_instalacion_github` | sin purga; volumen despreciable | < 1 MB en total |
| `presupuesto_api` | **90 días**, como `sincronizacion` | ≈ 1 MB |
| `resultado_invariante` | **90 días** | ≈ 1 MB |
| `cubo_tasa` | **24 horas**: son ventanas de tasa, no historial | < 0,1 MB |
| `accion_ui` | **14 días**, y **no registra ninguna acción con consecuencia** —ésas van a `bitacora`, que es *append-only*— | ≈ 2 MB dentro de la ventana |
| `respaldo` | cabecera sin purga; **ficheros 14 días** (A-170) | < 0,1 MB en base |

**Presupuesto recalculado:** las 47 originales suman del orden de **150 MB**; las 23 nuevas suman del orden de **10 MB** en el peor caso realista. **Total ≈ 160 MB**, por debajo del primer escalón de freno de 300 MB.

**Los dos escalones de A-090 se aplican también a `accion_ui` y a `cubo_tasa`**, que son las únicas nuevas cuyo crecimiento **no está acotado** por el número de commits o de estudiantes: al superar 300 MB su retención baja a **3 días** y **6 horas** respectivamente. **Ningún dato de evidencia se toca en ninguno de los dos escalones.**

El trabajo de purga de las 03:00 gana cinco reglas nuevas y la caducidad de los mensajes diferidos de A-225.

### A-200 · Regla general de `ON DELETE` y lista cerrada de claves foráneas nullables

**1 · Todas las claves foráneas se declaran `ON DELETE RESTRICT ON UPDATE RESTRICT`.** **No existe `CASCADE` ni `SET NULL` en ninguna migración.** Una **prueba de arquitectura** falla la construcción si una migración contiene `ON DELETE CASCADE` o `ON DELETE SET NULL` (A-174).

> Es la **traducción a base de datos de A-030**: si nada se borra, nada necesita cascada, y **una cascada olvidada es la única vía por la que la aplicación podría destruir evidencia sin que nadie lo haya decidido**.

**2 · Toda clave foránea es `NOT NULL`, salvo esta lista cerrada**, y cada una lleva en la migración un **comentario de columna con su motivo**:

| Columna nullable | Motivo |
|---|---|
| `asignacion_correccion.membresia_id` | Una entrega puede estar sin corrector asignado (A-206) |
| `acceso_docente_repositorio.membresia_id` | Nulo cuando `via = 'TEAM'`: el acceso es del equipo, no de la persona (A-163) |
| `version_entrega.repositorio_id` | Estado `SIN_REPOSITORIO` (A-204) |
| `usuario.cuenta_github_id` | El docente puede no haber declarado su cuenta (A-185) |
| `mapeo_github.cuenta_github_id` | Estado `SIN_DATO` (A-210) |
| `correccion.trabajo_publicacion_id` | Sólo se escribe al pasar a `PUBLICANDO` (A-214) |
| `regla_comunicacion.tarea_id` | Los eventos de alcance `CURSO` la llevan nula (A-130) |
| `identidad_git.cuenta_github_id`, `identidad_git.estudiante_id` | Autor no resuelto (A-086) |
| `commit.estudiante_id`, `commit.identidad_git_id` | Commit sin atribuir (A-118 regla 4) |
| `autoria_commit.estudiante_id`, `autoria_commit.identidad_git_id` | Exactamente uno de los dos, por `CHECK` (A-205) |
| `sujeto.estudiante_id`, `sujeto.grupo_id` | Exactamente uno de los dos, por `CHECK` (A-080) |
| `bitacora.actor_usuario_id` | Nulo cuando el actor es `SISTEMA` (A-029) |
| `incidencia.curso_id`, `incidencia.resuelta_por` | Incidencia global; resolución automática por el sistema |
| `version_entrega.reemplaza_a_id`, `mensaje_saliente.reemplaza_a_id`, `repositorio.reemplaza_a_id` | Autorreferencias de cadena (A-204, A-202, A-224) |
| `mapeo_github.vigente_hasta`, `identidad_git.vigente_hasta`, `pertenencia_grupo.activa_hasta` | Fila vigente. No son FK; se listan para que la lista de nullables sea completa |

**3 · Añadir una FK nullable fuera de esta lista es una decisión que se registra en esta carta.**

### A-201 · `identidad_git` es *append-only*, y su unicidad pasa a ser parcial

**`identidad_git` gana siete columnas:**

```
curso_id            uuid NOT NULL REFERENCES curso(id) ON DELETE RESTRICT   -- derivado de repositorio
estado              text NOT NULL DEFAULT 'SIN_RESOLVER'
                      CHECK (estado IN ('SIN_RESOLVER','RESUELTA','NO_ES_ESTUDIANTE','SUPERSEDIDA'))
resuelta_por        uuid NULL
resuelta_en         timestamptz NULL
vigente_desde       timestamptz NOT NULL
vigente_hasta       timestamptz NULL
nombre_visto_ultimo text NULL
```

**El índice único `(repositorio_id, email_normalizado)` de A-086 pasa a ser parcial:**

```
CREATE UNIQUE INDEX ON identidad_git (repositorio_id, email_normalizado)
  WHERE estado <> 'SUPERSEDIDA';
```

Es el patrón que A-078 y A-079 ya aplican a `mapeo_github`. **Sin esa conversión, el patrón *append-only* produce un `IntegrityError` en producción la primera vez que un docente corrige una identidad.** Se añade además el índice **no único `(curso_id, email_normalizado)`**, que sostiene la propuesta de propagación.

**`commit.identidad_git_id` apunta a la fila que se vio en la ingesta**; la lectura resuelve por `(repositorio_id, email_normalizado)` a la fila vigente, de modo que una supersesión **no obliga a reescribir decenas de miles de filas de `commit`**.

**La unidad de identidad es `(repositorio_id, email_normalizado)`, no el curso.** `identidad_git.curso_id` existe, es `NOT NULL` y se deriva de `repositorio` al insertar, pero **no participa en ningún índice único**:

1. **La corrección docente resuelve una identidad en un repositorio**, y su alcance por defecto es ese repositorio.
2. **La propagación al resto de repositorios del curso es una propuesta, nunca automática:** la pantalla lista los demás repositorios donde aparece el mismo `email_normalizado`, con nombre visto y número de commits, y **casillas desmarcadas por defecto**; se aplica sólo a lo marcado, en una sola transacción, y **cada aplicación crea su propia fila `RESUELTA` en el repositorio de destino**.
3. **El motivo se declara por escrito en la pantalla:** correos genéricos como `user@localhost`, `root@localhost` o el de un ejecutor de CI aparecen en repositorios de estudiantes distintos, y una identidad de curso **atribuiría el trabajo de uno a otro**.
4. **La resolución de una identidad nunca crea ni modifica un `mapeo_github`**: son dos hechos distintos, y confundirlos permitiría **dar un repositorio a alguien a partir de un correo escrito en un commit**.

La corrección docente cierra la fila vigente y crea otra, reescribe `autoria_commit` con `regla_atribucion = 'IDENTIDAD_DOCENTE'` **sólo** donde las reglas 1 a 3 de A-118 no habían resuelto, y encola `agregar_metricas` en la misma transacción.

Sirve a **R2.2.4**, **R2.2.5**, **R2.5.4**, **R2.5.8**.

### A-202 · `repositorio`: unicidad parcial, y la sustitución crea una fila nueva

**1 · Las unicidades de `repositorio` pasan a parciales:**

```
UNIQUE (sujeto_id)        WHERE estado <> 'INACCESIBLE'
UNIQUE (curso_id, nombre) WHERE estado <> 'INACCESIBLE'
UNIQUE (github_repo_id)   WHERE github_repo_id IS NOT NULL   -- sigue siendo total
```

**2 · Una fila `INACCESIBLE` conserva su `github_repo_id`, su nombre y toda su historia**: es evidencia y no se toca. La sustitución **crea una fila nueva** para el mismo sujeto, con **`repositorio.reemplaza_a_id`** apuntando a la anterior y **`repositorio.recreado_en`** en la nueva, que nace en `LISTO_PARA_CREAR`. **`github_repo_id_anterior` y `recreado_por` no existen**: el identificador anterior vive en la fila anterior, y el actor vive en `bitacora` con `REPOSITORIO_SUSTITUIDO`.

> **Por qué una fila nueva y no la misma.** Reutilizar la fila mete **dos repositorios distintos de GitHub bajo un solo `repositorio_id`**, y entonces los `commit`, las `identidad_git` y las `version_entrega` capturadas contra el repositorio perdido pasan a colgar del nuevo. Eso es una **atribución falsa de evidencia**, que las Leyes 2 y 4 prohíben, y ninguna comodidad de esquema la compensa.

**3 · La aplicación nunca sustituye sola.** Es una acción explícita de un profesor con `tarea.administrar`, con confirmación escrita que nombra al sujeto, al repositorio perdido y a lo que no vuelve, en `POST /api/cursos/{curso_id}/tareas/{tarea_id}/repositorios/{id}/sustituir`, que **encola** (A-226). El verbo es **«sustituir»** y no «recrear», porque «recrear» sugiere la misma fila.

**4 · Guarda anti-bucle:** `aprovisionar_repositorios` **nunca crea un repositorio para un sujeto que ya tiene una fila de `repositorio` en estado distinto de `INACCESIBLE`**, cualquiera que sea ese estado y tenga o no `github_repo_id`. **La única vía que produce una fila nueva es la acción de sustitución.**

**5 · Nada se borra.** A-030 queda intacta y la prueba de arquitectura sigue fallando la construcción si aparece `DELETE /repos/{owner}/{repo}` en `backend/app/adaptadores/`. La ficha del sujeto muestra **los dos repositorios en orden**, con la fecha de la sustitución y la advertencia «el repositorio fue sustituido el *fecha*; los objetos anteriores al *SHA* ya no están en GitHub».

**6 · `repositorio.nombre_canonico text NOT NULL`**, calculado por A-107 y A-108 y persistido junto a `nombre`, para poder comparar tras un `renamed`. El seguimiento es siempre por `github_repo_id` (Ley 3, A-074) y **la aplicación no renombra de vuelta**: muestra los dos nombres y ofrece el botón «restaurar el nombre canónico», con `tarea.administrar`. Tras un `edited` **se restauran los topics y el marcador de la descripción** si desaparecieron, porque de ellos depende la adopción segura de A-097. **El renombrado no es un hecho absorbido en silencio**: se ve en la ficha del repositorio, con la fecha y el nombre anterior.

Sirve a **R2.3.7**, **R2.3.8**, **R2.3.10**, **R2.3.11**, **R2.4.5**, **R2.4.7**, **R2.5.5**.

### A-203 · `entrega`: un escalar cerrado, el detalle en `jsonb` y las advertencias en `text[]`

**1 · `entrega.estado_validacion` es una columna escalar, consultable e indexable, con cuatro valores mutuamente excluyentes:**

```
entrega.estado_validacion text NOT NULL DEFAULT 'VIGENTE'
  CHECK (estado_validacion IN ('VIGENTE','VINCULADA_TRAS_EL_CIERRE','ELIMINADA_EN_CANVAS','EXCLUIDA'))
```

| Valor | Qué significa |
|---|---|
| `VIGENTE` | La entrega está vinculada y se comporta con normalidad |
| `VINCULADA_TRAS_EL_CIERRE` | Se vinculó cuando su fecha ya había pasado. **No se captura nada** hasta que el profesor pulsa «registrar ahora las versiones con la fecha de cierre de Canvas». Es un estado y no una advertencia **porque gobierna una guarda de captura** |
| `ELIMINADA_EN_CANVAS` | El assignment desapareció. Congela fechas y capturas, **conserva íntegras versiones, correcciones y notas**, y ofrece dos salidas y sólo dos: restaurar en Canvas o marcar excluida. Es **reversible**: si el assignment reaparece con el mismo `canvas_assignment_id`, la entrega vuelve sola a `VIGENTE` |
| `EXCLUIDA` | Salida manual del equipo docente, que conserva el histórico |

**`DESPUBLICADA` no es un valor de esta columna**: la publicación vive en `entrega.publicada`, espejo literal de `published`, y duplicarla crearía **dos verdades del mismo hecho**. **`ADVERTENCIA` tampoco lo es**: una entrega con advertencias sigue `VIGENTE` y su chip lleva el distintivo ámbar derivado de `advertencias <> '{}'`. **Se retiran y no llegan a existir** `AUSENTE_EN_CANVAS`, `HUERFANA`, `DESVINCULADA`, `SIN_FECHA`, `NO_PUBLICADA` y `VALIDA`.

**2 · El detalle vive en `entrega.validaciones jsonb NOT NULL DEFAULT '[]'`**, con un objeto por comprobación —`{codigo, desenlace, detectada_en}`— sobre las validaciones de A-138, y **se reescribe entero en cada revalidación**. No sustituye al escalar: **lo explica**.

**3 · `entrega.advertencias text[] NOT NULL DEFAULT '{}'`**, con catálogo cerrado de cuatro valores: `LOCK_ANTES_DE_DUE`, `UNLOCK_DESPUES_DE_DUE`, `FINAL_ANTES_QUE_PARCIAL`, `DOS_ENTREGAS_MISMA_FECHA`.

**4 · Confirmación en dos ciclos:** `entrega.ciclos_ausente smallint NOT NULL DEFAULT 0` y `entrega.detectada_ausente_en timestamptz`. **`ultima_lectura_ok_en` y `ciclos_sin_ver` no existen**: la marca de última lectura correcta ya la lleva `cursor_sincronizacion.ultimo_exito_en`, y dos marcas de la misma lectura se desincronizan.

**5 · Una sola incidencia para el assignment desaparecido: `ENTREGA_ELIMINADA_EN_CANVAS`**, severidad **BLOQUEANTE**, con `sujeto_tipo = 'ENTREGA'`. **`ENTREGA_HUERFANA` y `ENTREGA_CANVAS_ELIMINADA` no llegan a existir.** La detección exige **ausencia en dos ciclos consecutivos** de `sync_tareas_y_fechas`, confirmada con `GET /courses/:id/assignments/:aid` antes de transicionar; **un `429` o un `5xx` nunca produce esta transición**. **`TAREA_INCONSISTENTE` queda reservada a lo que A-138 le reserva** —el cambio de modalidad tras el vínculo— y no se usa aquí.

**6 · Sin assignment no se escribe evidencia.** Al pasar a `ELIMINADA_EN_CANVAS`, los trabajos de captura pendientes de esa entrega pasan a **`CANCELADO`** con `motivo_cancelacion = 'ASSIGNMENT_ELIMINADO_EN_CANVAS'`, **y no se escribe ninguna fila de `version_entrega`**: sin assignment no hay fuente de autoridad para la fecha (A-054), y **escribir evidencia de un corte que ya nadie puede verificar es fabricar evidencia**. La cancelación ocurre por las **dos vías**: explícita en la misma transacción en que se detecta la eliminación, y **revalidación dentro del cerrojo** inmediatamente antes de cualquier llamada externa, para el trabajo ya tomado. **Se cancelan además** los mensajes de esa entrega que sigan en el *outbox* —`proximidad_cierre`, `cambio_de_fecha`—, y **no** se cancelan `repositorio_disponible`, `invitacion_aceptada`, `recordatorio_invitacion` ni `recordatorio_mapeo`, que cuelgan del acceso y del repositorio. **Lo ya capturado no se toca.**

Sirve a **R2.3.1**–**R2.3.3**, **R2.4.1**, **R2.4.4**, **R2.4.5**, **R2.4.7**, **R2.5.6**, **R2.6.2**, **R2.7.6**, **R2.7.7**.

### A-204 · `version_entrega`: columnas mutables, composición congelada e inmutabilidad real

**1 · Lista cerrada de columnas mutables tras la captura**, y **todo lo demás es evidencia inmutable**: `vigente` (transición única `true → false`), `motivo`, `tag_estado`, `tag_motivo`, `tag_error`, `tag_creado` y `advertencias`, más `estado` **sólo en las dos transiciones de A-213**. **La función única de transición rechaza cualquier escritura sobre una columna que no esté en esta lista.**

**2 · `version_entrega.motivo` es un enum cerrado de cinco valores:** `SIN_REPOSITORIO_AL_CIERRE`, `SUJETO_MATERIALIZADO_TRAS_EL_CIERRE`, `FECHA_ADELANTADA`, `FECHA_EXTENDIDA` y **`CAPTURA_TARDIA_POR_ALCANCE`**. **`FECHA_YA_VENCIDA_AL_VINCULAR` no existe como motivo de versión**: ese hecho es el estado `VINCULADA_TRAS_EL_CIERRE` de la entrega (A-203), **porque gobierna una guarda de captura**, y un motivo de una fila que todavía no existe no puede gobernar nada. `ALTA_POSTERIOR_AL_CIERRE` tampoco existe. El origen de una captura manual vive en `origen_captura`, no aquí.

**3 · `version_entrega.motivo_repositorio`** copia el motivo de la lista cerrada de A-094 cuando lo hay, para que el corrector lea la razón en una línea. **`version_entrega.reemplaza_a_id`** encadena la fila supersedida con la que la sustituye, y **la supersesión nunca borra la anterior**.

**4 · La composición congelada del grupo es `version_entrega.integrantes jsonb NOT NULL`**, escrita **una sola vez, en la misma transacción que la fila**, e inmutable. Contiene un objeto por integrante `accepted` en el instante del corte (A-048), con exactamente estos campos:

```
{ estudiante_id, canvas_user_id, nombre, github_user_id, github_login, mapeo_github_id,
  workflow_state_pertenencia, estado_matricula, seccion_id, canvas_section_id }
```

Para una tarea individual el array tiene un único elemento. **`integrante_version_entrega` no existe**; toda respuesta que la cite lee esta columna. El filtro por integrante se hace con `jsonb_path_exists` sobre un **índice GIN** (`CREATE INDEX ON version_entrega USING gin (integrantes jsonb_path_ops)`), **no con un `JOIN`**.

**5 · Un sujeto que se materializa después del cierre produce `SIN_REPOSITORIO`, no `SIN_COMMITS`.** Se escribe una fila terminal con `estado = 'SIN_REPOSITORIO'`, `motivo = 'SUJETO_MATERIALIZADO_TRAS_EL_CIERRE'` y `repositorio_id` nulo, y **no se consulta GitHub**: en la fecha de corte ese repositorio no existía y la llamada no puede hacerse. La etiqueta visible es **«Sin repositorio al cierre — alta posterior a la fecha»**, y **nunca «sin entrega»**: afirmar que el estudiante no entregó nada cuando lo que ocurrió es que la aplicación no le dio repositorio a tiempo **es una afirmación falsa con consecuencia de nota**. Cuando el repositorio aparece más tarde **no se captura solo**: al alcanzar `CONTENIDO_LISTO` se abre `VERSION_REVISAR` sobre ese `(entrega, sujeto)` con la acción sugerida «captura ahora la versión o fija una fecha de corte propia».

**6 · El cambio de composición del grupo tras el cierre produce una sola incidencia:** **`GRUPO_CAMBIO_TRAS_CIERRE`**, con `sujeto_tipo = 'SUJETO'`. Los tres casos vecinos se distinguen **dentro de la misma fila**, en `detalle.casos[] ∈ {INTEGRANTE_ENTRO_TRAS_CIERRE, INTEGRANTE_SALIO_TRAS_CIERRE, NOTA_A_NO_CONGELADO}`, cada uno con la persona, los dos grupos y la fecha. **La severidad es la máxima de los casos abiertos**: `ADVERTENCIA` para los dos primeros y **`BLOQUEANTE`** para `NOTA_A_NO_CONGELADO`. **`CAMBIO_DE_GRUPO_ENTRE_ENTREGAS` y `SALIDA_CON_ENTREGA_CAPTURADA` no llegan a existir**: con el único parcial de A-087, un mismo hecho abriría **tres filas** y el informe diario lo contaría tres veces.

Sirve a **R2.2.3**, **R2.4.5**–**R2.4.8**, **R2.5.6**, **R2.6.2**, **R2.7.6**, **R2.7.7**.

### A-205 · `autoria_commit` es la única tabla de autoría, y el predicado de commit contable no se amplía

**1 · «Qué estudiantes se acreditan por un commit» vive en una única tabla:**

```
autoria_commit (
  commit_id          uuid    NOT NULL REFERENCES commit(id) ON DELETE RESTRICT,
  estudiante_id      uuid        NULL REFERENCES estudiante(id) ON DELETE RESTRICT,
  identidad_git_id   uuid        NULL REFERENCES identidad_git(id) ON DELETE RESTRICT,
  papel              text    NOT NULL CHECK (papel IN ('AUTOR','COAUTOR')),
  regla_atribucion   text    NOT NULL CHECK (regla_atribucion IN
                       ('AUTOR_GITHUB','EMAIL_NOREPLY','EMAIL_DIRECTO','IDENTIDAD_DOCENTE','SIN_ATRIBUIR')),
  confianza          text    NOT NULL CHECK (confianza IN ('ALTA','MEDIA')),
  CHECK (estudiante_id IS NOT NULL OR identidad_git_id IS NOT NULL),
  PRIMARY KEY (commit_id, coalesce(estudiante_id, identidad_git_id))
)
```

- **`commit_autoria` no existe**: el nombre es `autoria_commit`, por la convención `<concepto>_<entidad>` (A-154). El discriminador se llama **`papel`** y no `tipo`, porque `tipo` ya está tomado en `cuenta_github.tipo`, `sujeto.tipo` y `entrega.tipo`.
- `commit.estudiante_id`, `commit.regla_atribucion` y `commit.identidad_git_id` **se conservan denormalizados** como autor principal y **coinciden siempre con la fila `papel = 'AUTOR'`**; una prueba de dominio falla si divergen.
- `participacion_entrega` recibe **`commits_coautorados`** y **`commits_sin_atribuir_repo`**. **Todos los agregados de participación se calculan desde `autoria_commit`, nunca desde `commit.estudiante_id`.**
- El valor de la cuarta regla de la cascada de A-118 se llama **`IDENTIDAD_DOCENTE`**; `IDENTIDAD_MANUAL` no existe en ninguna columna ni en ninguna pantalla.
- **Un co-autor no resuelto** se representa con `estudiante_id` nulo, `identidad_git_id` apuntando a su fila y `regla_atribucion = 'SIN_ATRIBUIR'`, y aparece en el timeline como **co-autor no atribuido**.

**2 · `es_commit_contable(commit)` mantiene exactamente las tres exclusiones de A-171 —*merge*, commit inicial de la plantilla, huérfano— y exactamente esa firma, de un solo argumento.** `commit.motivo_exclusion text NOT NULL DEFAULT 'NINGUNO'` con `CHECK IN ('NINGUNO','MERGE','COMMIT_INICIAL','HUERFANO')`. **Los commits de bots y del equipo docente son contables** y entran en `metrica_repositorio_dia.commits`.

**Para que eso no falsee R2.5.3 ni R2.5.4 se añaden dos hechos derivados y una segunda función, y ninguno toca el predicado:**

- `commit.autor_es_bot boolean NOT NULL DEFAULT false` —el `autor_github_user_id` resuelve a una `cuenta_github` con `tipo = 'BOT'`, o es la cuenta bot de la propia App— y `commit.autor_es_docente boolean NOT NULL DEFAULT false` —coincide con una cuenta enlazada desde `usuario.cuenta_github_id` de una `membresia_curso` `ACTIVA` de ese curso **y** no coincide con ningún `mapeo_github` vigente del curso—. Las dos se recalculan en el pase nocturno completo.
- `metrica_repositorio_dia` gana **`commits_de_bot`** y **`commits_docentes`** como contadores **informativos**. **Ninguno resta de `commits`.**
- **Las alertas de R2.5.3 y R2.5.4 no se evalúan sobre `commits`**, sino sobre una **segunda función única** del mismo módulo, **`hay_actividad_estudiantil(repositorio, ventana)`**, que exige al menos un commit contable con al menos una fila de `autoria_commit` cuyo `estudiante_id` no sea nulo. **Un `push` de un bot o del profesor no apaga la alerta.** La interfaz declara la diferencia con estas palabras: **«actividad del repositorio» frente a «actividad de los estudiantes»**.

El timeline de A-124 muestra todos los commits con su etiqueta: «merge, no cuenta como aporte», «commit inicial de la plantilla», «historia reescrita», «bot», «commit del equipo docente». **Prueba de dominio obligatoria:** falla si `es_commit_contable` recibe más de un argumento o consulta `autor_es_bot`, `autor_es_docente` o `sin_cambios`.

Sirve a **R2.5.2**–**R2.5.4**, **R2.5.8**–**R2.5.10**, **R2.6.2**.

### A-206 · El espejo de la submission es por estudiante, y `asignacion_correccion` no tiene estado

**1 · El estado que Canvas reporta de cada entrega se espeja en una tabla propia con granularidad por estudiante:**

```
estado_canvas_submission (
  entrega_id, estudiante_id, workflow_state, score, entered_score, graded_at, grader_id,
  excused, late, seconds_late, points_deducted, submitted_at, posted_at, gradeable,
  origen text NOT NULL DEFAULT 'CANVAS', sincronizado_en timestamptz NOT NULL,
  PRIMARY KEY (entrega_id, estudiante_id)
)
```

**Las siete columnas `canvas_*` de valor dentro de `correccion` no existen**, porque `correccion` tiene unicidad `(entrega_id, sujeto_id)` —una fila por grupo— y **Canvas devuelve `score`, `graded_at` y `points_deducted` por estudiante**.

**2 · `contraste_canvas` es una derivación, no una columna.** Se calcula en `backend/app/dominio/estado_correccion.py` a partir de las filas de `estado_canvas_submission` de los **integrantes congelados** del sujeto (A-204), y toma exactamente cuatro valores: **`NO_COMPROBADO`, `CONCUERDA`, `DIVERGE`, `SOLO_EN_CANVAS`**. **`DISCREPA` no existe** en ninguna columna, consulta, etiqueta ni nombre de función: la incidencia se llama `NOTA_DIVERGENTE_EN_CANVAS` y A-154 exige la misma palabra para el mismo hecho. **`correccion.canvas_verificado_en` tampoco existe**: la antigüedad del dato es `estado_canvas_submission.sincronizado_en`, leída por el componente único de A-231.

> **Por qué derivación y no bandera persistida.** Una bandera junto a una tabla espejo que se reescribe en cada ciclo produce **dos verdades del mismo hecho** en cuanto un ciclo actualiza la tabla y no la bandera, y «¿esta nota concuerda con Canvas?» pasa a tener dos respuestas correctas. Es además la única forma de que `correccion` —que es por sujeto— **no mienta sobre un grupo cuyos integrantes tienen estados distintos en Canvas**. Con el sujeto sin ninguna fila espejada, la derivación devuelve `NO_COMPROBADO`, que es exactamente lo que el modo degradado de A-193 necesita.

**3 · Reglas de la tabla espejo, sin excepciones.** La regla de contraste **no usa `workflow_state`**: un sujeto está «con nota en Canvas» **si y sólo si `graded_at` y `score` no son nulos**. La fuente es el endpoint masivo `GET /courses/:id/students/submissions?student_ids[]=all&assignment_ids[]=<id>&per_page=100`, leído **una vez por entrega** y paginado por `Link`; **`submission_summary` no se usa en ninguna pantalla ni en ningún trabajo**. Las **cuatro marcas de reparto** —`YA_CALIFICADA_EN_CANVAS`, `EXCUSADA`, `NO_CALIFICABLE`, `SIN_VERSION`— **se derivan de esta tabla y no se persisten aparte**. Si Canvas tiene nota para un sujeto **sin fila de `correccion`**, se crea la fila en `SIN_CORRECTOR` y la derivación da `SOLO_EN_CANVAS`. El trabajo es `reconciliar_notas_canvas` (A-218) y la incidencia, `NOTA_DIVERGENTE_EN_CANVAS`.

**4 · `asignacion_correccion.estado` se elimina del esquema.** La corrección tiene **un solo estado persistido**, `correccion.estado`, que es la máquina 5. `asignacion_correccion` conserva `id`, `entrega_id`, `sujeto_id`, `membresia_id` (nullable), `asignada_por`, `asignada_en` e `iniciada_en`, y su unicidad `(entrega_id, sujeto_id)`. El invariante «`membresia_id IS NULL` si y sólo si `correccion.estado = 'SIN_CORRECTOR'`» **se conserva como prueba automatizada**, y es exactamente la demostración de que la columna retirada **era una función de otras dos**. `iniciada_en` sigue produciendo la transición `ASIGNADA → EN_CURSO` y **no se borra nunca, ni al reasignar**.

Sirve a **R2.7.1**–**R2.7.3**, **R2.7.6**, **R2.7.7**.

### A-207 · `incidencia`: se silencia, nunca se pospone, y el catálogo pasa a 51 tipos

**1 · Una incidencia no bloqueante se SILENCIA. «Posponer» no existe.** `incidencia` gana **tres columnas y sólo tres**: `silenciada_hasta timestamptz NULL`, `motivo_silenciamiento text NULL` y `silenciada_por uuid NULL`. **`pospuesta_hasta` y `pospuesta_por` no existen**, y el verbo en las cuatro pantallas es **«silenciar»** (A-154). Reglas, sin excepciones:

1. Sólo se silencian incidencias de severidad `ADVERTENCIA` o `INFORMATIVA`, y **sólo de los tipos `SIN_ACTIVIDAD` y `SIN_PARTICIPACION`**. **Una incidencia `BLOQUEANTE` no se silencia jamás.**
2. **Silenciar no cierra la incidencia**: sigue `abierta = true`, el único parcial de A-087 sigue impidiendo duplicados y `detectada_en` sigue diciendo desde cuándo persiste.
3. **Caduca sola:** `silenciada_hasta = min(ahora + 14 días, próxima fecha efectiva de cierre del sujeto)`.
4. Exige **motivo escrito**, queda en `bitacora` con `INCIDENCIA_SILENCIADA`, y el permiso es `curso.ver`.
5. **Queda fuera de la sección 3 del informe diario** y se muestra plegada bajo «silenciadas (N)» en Pendientes y en el tablero. **No desaparece de la interfaz.**

**2 · El catálogo de A-088 pasa de 37 a 51 tipos.** Las **catorce adiciones**, cada una con su `sujeto_tipo` único (A-184):

| Tipo | Severidad | `sujeto_tipo` |
|---|---|---|
| `REPOSITORIO_INACCESIBLE` | ADVERTENCIA | `REPOSITORIO` |
| `ENTREGA_ELIMINADA_EN_CANVAS` | BLOQUEANTE | `ENTREGA` |
| `GRUPO_CAMBIO_TRAS_CIERRE` | máxima de sus casos abiertos | `SUJETO` |
| `SIN_CREDENCIAL_DE_RESPALDO` | BLOQUEANTE | `CURSO` |
| `ALTA_TARDIA` | ADVERTENCIA | `SUJETO` |
| `CANVAS_CURSO_NO_DISPONIBLE` | BLOQUEANTE | `CURSO` |
| `TAREA_REGISTRO_ALTERADA` | derivada de `detalle.estado` | `CURSO` |
| `MENSAJE_NO_ENTREGABLE` | ADVERTENCIA | `ESTUDIANTE` |
| `NOTA_OCULTA_AL_ESTUDIANTE` | INFORMATIVA | `ENTREGA` |
| `NOTA_DIVERGENTE_EN_CANVAS` | ADVERTENCIA | `CORRECCION` |
| `ACCESO_DOCENTE_NO_REVOCADO` | BLOQUEANTE | `MEMBRESIA` |
| `CUENTA_DOCENTE_ES_DE_ESTUDIANTE` | BLOQUEANTE | `MEMBRESIA` |
| `DENEGACIONES_ANOMALAS` | ADVERTENCIA | `SISTEMA` |
| `CORREO_OPERATIVO_ELEVADO` | INFORMATIVA | `SISTEMA` |

**No entran, y se declara por escrito para que nadie los reintroduzca:** `TAREA_REGISTRO_ELIMINADA`, `ENTREGA_HUERFANA`, `ENTREGA_CANVAS_ELIMINADA`, `CAMBIO_DE_GRUPO_ENTRE_ENTREGAS`, `SALIDA_CON_ENTREGA_CAPTURADA` y `TAG_ALTERADO`. **No son adiciones** `POSIBLE_FUSION_CANVAS` ni `CUOTA_CORREO_AGOTADA`, que **ya están entre los 37** de A-088.

**`TAREA_REGISTRO_ALTERADA` absorbe la desaparición de la tarea de registro:** `detalle.estado ∈ {ALTERADA, DESAPARECIDA}` con la diferencia campo a campo de los ocho campos de la huella; **`ADVERTENCIA` con `ALTERADA`** —la recolección sigue— y **`BLOQUEANTE` con `DESAPARECIDA`**, porque sin ese assignment caen la vía 1 de A-148 y el canal 2 de A-127, y con ellos **R2.2.4**, **R2.2.5** y la respuesta al estudiante de A-146. **`TAREA_REGISTRO_ELIMINADA` no existe.**

**Aviso de vocabulario, porque son dos objetos distintos:** el tipo de incidencia se llama **`CUOTA_CORREO_AGOTADA`** y el motivo de mensaje se llama **`CUOTA_AGOTADA`** (A-224). Comparten etiqueta en español, y **ninguna de las dos palabras se usa en el sitio de la otra**.

**El `CHECK` de `incidencia.tipo` se genera con 51 valores desde `dominio/incidencias.py`**, la tabla `TIPO_INCIDENCIA → SUJETO_TIPO` cubre los 51, y la prueba que exige fila en `dominio/errores.py` corre sobre **51 tipos y 7 subtipos** de A-098.

Sirve a **R2.2.6**, **R2.3.11**, **R2.5.3**–**R2.5.5**, **R2.6.1**, **R2.6.2**, **R2.7.6**, **R2.7.7**.

### A-208 · `repositorio_base.estado` tiene cinco valores, y `LISTO` es la guarda de activación

`repositorio_base.estado` es un enum cerrado de **cinco** valores con `DEFAULT 'CREANDO'`. **No existe un valor «no solicitado»**: `tarea.repositorio_base_id` es nullable y **una tarea sin base no tiene fila**.

| Estado | Se entra cuando | Sale a |
|---|---|---|
| `CREANDO` | Se lanzó la escritura síncrona número 2 de A-169, o su degradación a trabajo de cola | `CREADO_VACIO`, `ERROR` |
| `CREADO_VACIO` | `POST /orgs/{org}/repos` devolvió `201`, el `PATCH is_template=true` respondió `200` y el árbol sólo tiene el README de `auto_init` | `LISTO`, `INACCESIBLE` |
| `LISTO` | El árbol tiene al menos un archivo más que el README de `auto_init`, y `es_plantilla = true` verificado | `CREADO_VACIO` (el profesor borró los archivos, A-067), `INACCESIBLE` |
| `ERROR` | Fallo permanente al crear: nombre ocupado por un tercero que no supera las cinco condiciones de A-097, o la organización prohíbe crear | `CREANDO`, por acción explícita con `tarea.administrar` |
| `INACCESIBLE` | Webhook `repository` `deleted` o `transferred` sobre el base, o dos ciclos de `404`/`403` | `LISTO` o `CREADO_VACIO` por comprobación positiva |

**La guarda de activación de la tarea se escribe con este catálogo:** `BORRADOR → ACTIVA` exige `repositorio_base.estado = 'LISTO'` **sólo si la tarea declara repositorio base**. **Una tarea sin base se activa sin ninguna comprobación de base**, porque **R2.3.5** declara el repositorio base **opcional** y convertirlo en requisito sería añadir un requisito que el enunciado no pone.

**Con el base en `ERROR` o `INACCESIBLE`, el aprovisionamiento de esa tarea se detiene** con el motivo escrito en pantalla —`POST /repos/{template}/generate` fallaría repositorio a repositorio— y **los repositorios ya creados no se ven afectados**, porque `generate` copia una sola vez (A-067). **La tarea no pasa a `INCONSISTENTE`**: ese estado está reservado al cambio de modalidad en Canvas (A-138).

`repositorio_base` conserva `rama_por_defecto` leída de la respuesta `201` y **nunca supuesta `main`** (A-068), gana `clase_error`, `error_mensaje_literal` e `inaccesible_desde`, y conserva el marcador `[gestor:{curso_slug}/{tarea_slug}/base]` en la descripción, que es la condición (d) de A-097 para el base. La guarda vive en `tarea_activable(tarea)` de `backend/app/dominio/`, y el botón «Activar tarea» **se muestra deshabilitado con el motivo** mientras el base declarado no esté `LISTO`.

Sirve a **R2.3.5**–**R2.3.7**, **R2.3.11**.

---

## 9. Máquinas de estado

> **La cifra «seis» queda ANULADA POR RG-038, RG-049 y RG-203. Manda ahora A-209: son SIETE máquinas**, con `backend/app/dominio/estados.py` como fuente única de **todos** los enumerados del sistema. Las cuatro reglas de abajo se conservan enteras y rigen para las siete.

Seis máquinas gobiernan el sistema. **Las seis comparten cuatro reglas:**

1. Los estados **se persisten en una columna**, no se derivan al vuelo.
2. **Toda transición queda registrada con su causa** en `bitacora` o en la propia fila.
3. **Ningún estado terminal se alcanza por un fallo transitorio no clasificado.**
4. **Todo estado tiene una etiqueta en español visible en la interfaz** (A-155). Un estado que no se ve no cumple §4 del enunciado.

### A-091 · Máquina 1 — Mapeo estudiante → cuenta de GitHub — ANULADA POR RG-003, RG-004 y RG-005 en sus subtipos y en su fila `SIN_DATO`

> **Manda ahora A-210.** Los nueve estados y sus transiciones se conservan uno a uno; lo que queda superado es que `SIN_DATO` fuera una ausencia de fila —**es una fila persistida**— y que `motivo_invalidacion` tuviera **tres** subtipos, que pasan a **cinco**.

Cubre **R2.2.4**, **R2.2.5**, **R2.2.6**.

| Estado | Se entra cuando | Transiciones de salida | Condición de error |
|---|---|---|---|
| `SIN_DATO` | El estudiante existe y no hay ningún candidato | → `RECIBIDO` (llega entrega de Canvas, CSV o edición docente) | — |
| `RECIBIDO` | Hay un candidato extraído, aún sin validar | → `VIGENTE`, `NO_EXISTE`, `ES_ORGANIZACION`, `EN_CONFLICTO`, `NO_RESUELTO` | — |
| `NO_RESUELTO` | El texto era ambiguo, vacío, o casaron dos candidatos distintos | → `RECIBIDO` (nuevo intento o corrección docente) | Se guarda el texto crudo en `evidencia` |
| `NO_EXISTE` | `GET /users/{login}` devolvió `404` | → `RECIBIDO` | Comentario automático en la entrega de Canvas (A-137) |
| `ES_ORGANIZACION` | El login resuelve a una organización | → `RECIBIDO` | Se detecta comparando `GET /users/{login}` con `GET /orgs/{login}`, **no confiando en el campo `type`**, cuyos valores literales **no están impresos en la documentación** **[MEDIR]** (`Q-2.3-66`) |
| `EN_CONFLICTO` | Ese `github_user_id` ya está vigente para otro estudiante del mismo curso | → `VIGENTE` (tras resolución docente explícita) | **Ninguno de los dos estudiantes recibe repositorio** hasta resolver (A-079) |
| `VIGENTE` | `GET /users/{login}` devolvió `200` y es una persona | → `SUPERSEDIDO`, `INVALIDADO` | — |
| `INVALIDADO` | La revalidación diaria detectó un problema | → `RECIBIDO` | Tres subtipos, abajo |
| `SUPERSEDIDO` | Una corrección creó una fila nueva | terminal (histórico inmutable) | — |

**Tres subtipos de invalidación**, porque la acción correctiva es distinta en cada uno:

- **`RENOMBRADO`** — el `github_user_id` sigue existiendo con otro `login`. **Se actualiza solo, sin molestar a nadie.**
- **`CUENTA_ELIMINADA`** — `GET /user/{account_id}` devuelve `404`. Incidencia `GITHUB_CUENTA_PERDIDA`.
- **`LOGIN_REASIGNADO`** — el `login` almacenado devuelve `200` con un `id` distinto: **otra persona lo reclamó** **[DOC]** (`Q-2.3-66`). Es el peligroso y **siempre exige confirmación humana**.

**La revalidación se hace por `GET /user/{account_id}`**, que la documentación describe como el método que toma el identificador duradero en lugar del login **[DOC]** (`Q-2.3-66`).

**La transición a `INVALIDADO` no destruye el repositorio ni el acceso ya concedido**: abre incidencia y deja que un docente decida.

### A-092 · Máquina 2 — Aprovisionamiento del repositorio — ANULADA POR RG-011, RG-013, RG-016 y RG-181 en su tabla de estados

> **Manda ahora A-211.** El predicado de `OPERATIVO`, los seis motivos de `DEGRADADO` y la regla «`DEGRADADO` no es un error» se conservan enteros; lo que queda superado es el número de estados —**quince**, con `INACCESIBLE`—, la transición `DEGRADADO → CONFIGURANDO_ACCESOS` sin disparador escrito, y la salida de `ERROR_PERMANENTE` sin destino por subtipo.

Cubre **R2.3.7**, **R2.3.9**, **R2.3.10**, **R2.3.11**.

| Estado | Se entra cuando | Sale a | Condición de error |
|---|---|---|---|
| `ESPERANDO_INFORMACION` | El sujeto existe pero no se cumple la guarda de A-093 | `LISTO_PARA_CREAR` | Guarda el **motivo** (A-094) |
| `LISTO_PARA_CREAR` | Se cumple la guarda | `CREANDO` | — |
| `CREANDO` | El trabajo tomó el sujeto y llamó a GitHub | `CREADO_SIN_CONTENIDO`, `BLOQUEADO`, `ERROR_TRANSITORIO`, `ERROR_PERMANENTE` | `422 name exists` → adopción condicionada (A-097) |
| `CREADO_SIN_CONTENIDO` | Respuesta `201`, contenido aún no observado | `CONTENIDO_LISTO` | `404`, `409` y `200` con lista vacía se toleran como **transitorios** durante la ventana (A-096) |
| `CONTENIDO_LISTO` | Se observó el commit inicial, o venció el sondeo | `CONFIGURANDO_ACCESOS` | Si venció el sondeo: `commit_inicial_sha` nulo, incidencia informativa, **no error** |
| `CONFIGURANDO_ACCESOS` | Se emiten las invitaciones de colaborador de los estudiantes **y se concede la lectura al equipo docente** (A-163) | `OPERATIVO`, `DEGRADADO`, `ERROR_TRANSITORIO` | — |
| `OPERATIVO` | **Se cumple el predicado de abajo, entero** | `DEGRADADO`, `FUERA_DE_ALCANCE`, `ARCHIVADO` (A-168) | — |
| `DEGRADADO` | **Se niega el predicado de abajo y el repositorio existe y es usable** | `CONFIGURANDO_ACCESOS`, `OPERATIVO`, `FUERA_DE_ALCANCE`, `ARCHIVADO` (A-168) | Guarda el **motivo**, enumerado abajo |
| `BLOQUEADO` | Política de la organización, permisos pendientes, o cupo agotado | `LISTO_PARA_CREAR` al desaparecer la causa | **Se reintenta cada 30 min**, no en bucle |
| `ESPERANDO_LIMITE` | Límite de GitHub alcanzado | vuelve al estado previo | **Nunca se pinta como error** (Ley 5) |
| `ERROR_TRANSITORIO` | Fallo clasificado transitorio | reintenta con *backoff* | Hasta 8 intentos en ~2 h |
| `ERROR_PERMANENTE` | Error clasificado no transitorio | Sólo por acción del docente | Subtipos en A-098 |
| `FUERA_DE_ALCANCE` | El sujeto se desactivó por la regla de A-164 | `OPERATIVO` o `DEGRADADO` si vuelve | **No se borra ni se archiva nada** (A-095) |
| `ARCHIVADO` | **Acción explícita del profesor, o webhook que informa de que GitHub lo archivó** | Sólo a `OPERATIVO`/`DEGRADADO` por desarchivado explícito | **Regla de entrada completa en A-168.** Dejó de ser un estado terminal huérfano |

**El predicado de `OPERATIVO`, escrito una sola vez y sin lecturas alternativas.** La revisión 1 decía «todos los integrantes tienen acceso `ACEPTADO` o `INVITADO`», expresión que se cumplía trivialmente si los `invited` de Canvas «no cuentan» —como decide A-048— y que dejaba el mismo repositorio en `OPERATIVO` por A-092 y en `DEGRADADO` por A-048. Se resuelve así, y **la expresión «todos los integrantes» ya no aparece en ninguna parte**:

> Un repositorio está **`OPERATIVO`** si y sólo si se cumplen las **tres** condiciones:
> 1. **Existe y su contenido está resuelto** — estado previo `CONTENIDO_LISTO` alcanzado.
> 2. **Cobertura de estudiantes:** para **cada** `pertenencia_grupo` con `workflow_state = 'accepted'` del grupo (o para el único estudiante, si la tarea es individual), existe una fila de `acceso_repositorio` con `estado ∈ {ACEPTADO, ACCESO_DIRECTO}`; **y** no hay ninguna `pertenencia_grupo` con `workflow_state ∈ {'invited', 'requested'}` pendiente en Canvas.
> 3. **Acceso docente:** existe `acceso_docente_repositorio` con `estado = CONCEDIDO` (A-163).

Cualquier otra situación en la que el repositorio exista es **`DEGRADADO`**, con un motivo obligatorio de esta lista cerrada, que es lo que se muestra en pantalla:

`FALTA_ACEPTAR_INVITACION_GITHUB` · `INVITACION_EXPIRADA` · `INTEGRANTE_SIN_MAPEO` · `INTEGRANTE_PENDIENTE_EN_CANVAS` (los `invited`/`requested` de A-048) · `SIN_ACCESO_DOCENTE` · `ERROR_AL_CONCEDER_ACCESO`.

**`DEGRADADO` no es un error y la interfaz no lo pinta como tal.** Su etiqueta es **«Listo, falta gente por entrar»** y va en ámbar, no en rojo; el repositorio funciona, el estudiante que ya entró puede trabajar, y lo que falta está nombrado. Es el estado normal de un repositorio recién creado, y por eso el aviso de **R2.3.12** **no** cuelga de `OPERATIVO` (A-130): colgarlo de ahí sería no enviar nunca el mensaje que explica cómo aceptar la invitación cuya aceptación se está esperando.

**Consecuencias que se propagan y que hay que respetar en todas las vistas:** el recuento de **R2.3.11**, la barra de **R2.5.5** y las secciones 1 y 2 del informe diario usan **estas** definiciones, cuentan `OPERATIVO` y `DEGRADADO` **por separado**, y **nunca suman `DEGRADADO` a la columna de problemas**: va en su propia columna, «funcionando, incompleto».

### A-093 · Guarda de salida de `ESPERANDO_INFORMACION`

Se aplica **sobre los sujetos que A-164 haya materializado**; esta guarda decide *cuándo* se aprovisiona un sujeto, no *quién* es sujeto.

- **Tarea individual:** el estudiante tiene mapeo `VIGENTE` y ninguna incidencia bloqueante que le afecte.
- **Tarea grupal:** el grupo tiene **al menos un integrante `accepted` con mapeo `VIGENTE`** y ninguna incidencia bloqueante sobre el grupo (A-048, A-049).

Esto es exactamente **R2.3.10**: se crean progresivamente, a medida que la información está disponible, y **sin que nadie pulse nada**.

### A-094 · `ESPERANDO_INFORMACION` siempre dice por qué — ANULADA POR RG-037 en su lista de motivos

> **Mandan ahora A-211 y A-225.** La lista pasa de seis a **siete** motivos, con **`CURSO_EN_SOLO_LECTURA`** para los sujetos que no se aprovisionan por `curso.modo_escritura = 'SOLO_LECTURA'`. La regla «un estado pendiente sin causa no cumple R2.2.6 ni R2.3.11» se conserva entera.

El motivo se persiste y es uno de: `SIN_MAPEO_GITHUB`, `MAPEO_EN_CONFLICTO`, `SIN_GRUPO_ASIGNADO`, `GRUPO_SIN_INTEGRANTES_ACEPTADOS`, `ESTUDIANTE_EN_DOS_GRUPOS`, `TAREA_INCONSISTENTE`. **Un estado «pendiente» sin causa no cumple R2.2.6 ni R2.3.11**, que piden mostrar *claramente* qué falta.

### A-095 · Un sujeto que sale de alcance conserva todo

Si un sujeto se desactiva por la regla de A-164 después de que su repositorio existe, pasa a `FUERA_DE_ALCANCE`, **conserva el repositorio, los commits y las versiones capturadas**, y se muestra en la tarea bajo «sujetos retirados». No se borra —destruiría evidencia— y **no se archiva** —archivar impediría crear tags posteriores, porque en un repositorio archivado todo pasa a sólo lectura **[DOC]** (`Q-2.4-47`)—. Borrar trabajo de estudiantes por un cambio de configuración en Canvas es inaceptable.

**Esta decisión prohíbe archivar *por salida de alcance*; no prohíbe archivar.** Quién archiva, desde dónde y con qué efecto está en **A-168**, y las dos decisiones son compatibles: A-095 dice que el sistema no archiva solo, A-168 dice que un profesor sí puede archivar a propósito y qué pasa entonces.

### A-168 · Quién archiva un repositorio, desde dónde y con qué efecto — ANULADA POR RG-094, RG-098 y RG-201 en su guarda y en su permiso

> **Manda ahora A-197.** Los dos caminos de entrada y las cinco consecuencias de archivar se conservan; lo que queda superado es que la guarda fuera una sola —son **cinco**—, que bastara `tarea.administrar` —exige además **rol `PROFESOR`**— y que no se dijera quién escribe `tarea.estado = ARCHIVADA`.

**Cierra la máquina 2.** La revisión 1 listaba `ARCHIVADO` como salida de `OPERATIVO` **sin regla de entrada, sin actor, sin pantalla y sin trabajo**, mientras A-095 prohibía archivar por salida de alcance y A-101 declaraba consecuencias de encontrarse un repositorio archivado. Era un estado terminal sin causa escrita. Queda así:

**Sólo se entra a `ARCHIVADO` por dos caminos, y no hay un tercero:**

| Camino | Actor | Guarda |
|---|---|---|
| **Acción explícita «archivar repositorios de la tarea»**, desde la pantalla de tarea | Un profesor con `tarea.administrar` | **Bloqueada** mientras exista alguna entrega de la tarea sin versión vigente capturada para ese sujeto **y con fecha de cierre en el futuro**. Con una entrega ya vencida y sin capturar, se permite **con confirmación escrita** que nombra qué queda sin capturar |
| **Webhook `repository` con acción `archived`** | Alguien lo archivó desde GitHub | Ninguna: es un hecho, se refleja. Se abre incidencia informativa porque la aplicación no lo pidió |

**Qué implica archivar, dicho en la propia pantalla antes de confirmar:**

1. En un repositorio archivado **todo pasa a sólo lectura** **[DOC]** (`Q-2.4-47`). **No se pueden crear tags nuevos**, de modo que una captura posterior quedará `CAPTURADA_SIN_TAG` (A-101), que ya es el comportamiento declarado.
2. **Las versiones ya capturadas no se tocan** y siguen siendo válidas: la evidencia es el SHA en nuestra base (Ley 4), y la URL `.../tree/{sha}` sigue funcionando para el equipo docente, que conserva su lectura (A-163).
3. **La ingesta de actividad se detiene** para ese repositorio: sale de `reconciliar_actividad` y del barrido nocturno, lo que además libera presupuesto de GitHub (A-117).
4. **El estudiante conserva la lectura** y el repositorio sigue visible para él. No se le quita nada.
5. **Es reversible por acción explícita** del mismo profesor: `PATCH /repos/{o}/{r}` con `archived: false`, tras lo cual el repositorio vuelve a `OPERATIVO` o `DEGRADADO` según el predicado de A-092. **La aplicación nunca desarchiva por su cuenta** (A-101).

**Cuándo tiene sentido usarlo:** al cerrar el curso, después del 6 de octubre, para congelar el trabajo entregado. **La aplicación no lo hace sola nunca**, ni siquiera al cerrar la tarea: archivar es una decisión del docente sobre el trabajo de sus estudiantes.

**Pantalla:** acción en `/cursos/{id}/tareas/{id}`, bloque «cierre de la tarea», con recuento de lo que se va a archivar y la lista de lo que quedaría sin capturar. **Trabajo:** `archivar_repositorios`, por tarea, se añade al catálogo cerrado de A-114.

### A-096 · La espera de contenido tras `generate` es acotada y nunca produce error

La documentación **no** dice que la copia de contenido tras `POST /repos/{t}/{r}/generate` sea síncrona ni asíncrona; sólo documenta el `201` **[MEDIR]** (`Q-2.3-19`). El endpoint hermano de *fork* **sí** documenta asincronía, lo que hace imprudente asumir que aquí no la hay. **No se asume ninguna de las dos cosas: se comprueba.**

Procedimiento: sondeo de `GET /repos/{o}/{r}/commits?per_page=1` con **retroceso, no a cadencia fija**, y con **tope duro de 8 sondeos por repositorio**:

| Sondeo | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Espera previa | 2 s | 2 s | 5 s | 5 s | 10 s | 10 s | 30 s | 30 s |
| Tiempo acumulado | 2 s | 4 s | 9 s | 14 s | 24 s | 34 s | 64 s | **94 s** |

**Por qué cambia respecto de la revisión 1.** Aquélla sondeaba «cada 2 segundos hasta 90 segundos», es decir **hasta 45 peticiones por repositorio**; con el ritmo de aprovisionamiento de A-117 —1 repositorio cada 3 s, 200 sujetos en unos 10 minutos— el peor caso eran ~9 000 peticiones en esa ventana, un ritmo de ~54 000/hora contra un techo documentado de 12 500/hora **[DOC]** (`Q-2.5-08`). Los dos números estaban en el mismo documento y no cabían juntos. **Con 8 sondeos el peor caso es 1 600 peticiones en 10 minutos (~9 600/hora sumando la creación), que sí cabe bajo el techo del 50 % de A-117**, y la cobertura temporal es la misma: 94 segundos.

Si aparece el commit inicial, se guarda como `commit_inicial_sha` y se pasa a `CONTENIDO_LISTO`. Si se agotan los ocho, **se pasa igualmente a `CONTENIDO_LISTO`** con `commit_inicial_sha` nulo, incidencia informativa, y se delega la resolución al reconciliador. **La creación no se reintenta nunca por esta causa: el repositorio ya existe.** Los códigos `404` y `409` se toleran durante la ventana; el `409` está documentado como posible en `GET /commits` sin que la documentación explique su causa **[DOC]**.

**El sondeo está contabilizado en el presupuesto de A-117**, con su fórmula escrita, y no como un coste invisible.

El `commit_inicial_sha` sirve además de **línea base para las métricas**: los commits del propio andamiaje no cuentan como participación del estudiante (A-118).

### A-097 · Adopción segura ante nombre ya existente

Antes de crear se hace `GET /repos/{org}/{nombre}`. Si responde `200`, **se adopta el repositorio existente sólo si se cumplen las CINCO condiciones**:

| # | Condición | Qué descarta |
|---|---|---|
| a | Tiene el topic `gestor-tareas` | Un repositorio ajeno a la aplicación |
| b | Pertenece a la organización vinculada | Un repositorio de otra organización |
| c | **Tiene el topic `curso-<slug>` de ESTE curso** (A-069) | El repositorio de **otro curso** |
| d | **Su descripción contiene el marcador `[gestor:{curso_slug}/{tarea_slug}/{tipo_sujeto}{id_sujeto}]` que corresponde exactamente a este sujeto y esta tarea** (A-069) | El repositorio de **otra tarea o de otro sujeto** |
| e | Su historia no contiene commits ajenos a la plantilla | Un repositorio con trabajo real de alguien |

**Las condiciones (c) y (d) se añadieron en la revisión 2.** Las tres de la revisión 1 no comprobaban ni el curso, ni la tarea, ni el sujeto: sólo el topic `gestor-tareas`, que A-069 pone en **todos** los repositorios. Bastaba una colisión de nombre —dos secciones del mismo ramo, el mismo `slug-tarea`, un estudiante presente en ambas— para que la aplicación **adoptara el repositorio ajeno** y le entregara a un estudiante el trabajo de otro. Con la organización 1:1 por curso (A-027) y el `curso.slug` en el nombre (A-107) esa colisión ya no puede producirse; con (c) y (d) **tampoco se adoptaría si se produjera**. Defensa en profundidad, no redundancia inútil.

Cumplidas las cinco: se guarda su `github_repo_id` y se salta a `CONFIGURANDO_ACCESOS`, lo que hace **idempotente** el aprovisionamiento sin depender del comportamiento de la API ante un `422`.

En cualquier otro caso: `ERROR_PERMANENTE` con subtipo `NOMBRE_OCUPADO_POR_TERCERO` e incidencia `REPO_NOMBRE_OCUPADO`, **con el detalle de qué condición falló**. **Tratar el `422` como éxito a ciegas es cómodo y es incorrecto: podría adoptar el repositorio de otra cosa.**

### A-098 · Subtipos de `ERROR_PERMANENTE`, y cómo se construye la tabla

Enumerados y mostrados con texto accionable: `ORG_PROHIBE_CREAR_REPOS`, `ORG_EXIGE_2FA`, `CUENTA_BLOQUEADA_POR_ORG`, `CUENTA_ELIMINADA`, `LOGIN_ES_ORGANIZACION`, `NOMBRE_OCUPADO_POR_TERCERO`, `PERMISO_INSUFICIENTE`.

**La tabla que mapea el error real de GitHub a cada subtipo se construye midiendo, no adivinando.** Está documentado que una organización puede impedir que las GitHub Apps creen repositorios **[DOC]** (`Q-2.1-39`), pero **no** se publica el código ni el mensaje de ese caso **[MEDIR]**. Mientras la tabla no esté completa, **un `403` cuyo cuerpo no se reconozca se clasifica como `BLOQUEADO`** —no como error del sujeto— y se muestra al docente **con el mensaje literal de GitHub**, en lugar de traducirse a un diagnóstico inventado.

### A-099 · Máquina 3 — Acceso del estudiante al repositorio — ANULADA POR RG-009, RG-010 y RG-183 en su catálogo de siete valores

> **Manda ahora A-212.** Los siete estados de esta tabla se conservan uno a uno; lo que queda superado es que fueran todos: **la máquina 3 tiene diez valores**, con `REVOCACION_PROPUESTA`, `REVOCACION_PROGRAMADA` y `REVOCADO`, y `acceso_repositorio` gana ocho columnas de revocación y `motivo_revocacion` de seis valores.

Cubre **R2.3.9**, **R2.3.11**, y alimenta **R2.5.4**.

| Estado | Se entra cuando | Sale a | Nota |
|---|---|---|---|
| `SIN_MAPEO` | El integrante no tiene mapeo vigente | `POR_INVITAR` | — |
| `POR_INVITAR` | Hay mapeo vigente y el repositorio existe | `INVITADO`, `ACCESO_DIRECTO` | — |
| `INVITADO` | `PUT .../collaborators` devolvió **`201`** | `ACEPTADO`, `EXPIRADA`, `DESAPARECIDA` | Se guardan `invitation_id` y `html_url` |
| `ACCESO_DIRECTO` | `PUT` devolvió **`204`** | `ACEPTADO` (equivalente) | Documentado para colaborador existente, miembro de la organización y miembro de equipo colaborador **[DOC]** (`Q-2.3-33`). **Salta el estado pendiente** |
| `ACEPTADO` | Webhook `member` con acción `added`, **la única señal documentada de aceptación** **[DOC]** (`Q-2.5-02`) | `DESAPARECIDA` | — |
| `EXPIRADA` | La reconciliación ve `expired = true` | `POR_INVITAR` (reenvío) | `expired` figura **sólo en el ejemplo JSON**, no descrito en prosa **[MEDIR]** (`Q-2.3-30`) |
| `DESAPARECIDA` | Ni invitación abierta ni colaborador | `POR_INVITAR` | **Se llama `DESAPARECIDA`, no `RECHAZADA`** (A-100) |

### A-100 · El estado se llama `DESAPARECIDA` y la interfaz dice «rechazada o caducada»

**No existe señal documentada de rechazo.** El rechazo lo ejecuta el invitado con un endpoint que sólo acepta su propio token, no hay webhook de rechazo ni de expiración, la raíz «declin» no aparece en el catálogo de webhooks, y **una invitación rechazada es indistinguible de una revocada** **[DOC]** (`Q-2.3-30`). Nombrar un estado con una causa que no se puede probar sería **mentir en la interfaz**. Se dice literalmente «rechazada o caducada» en vez de fingir una precisión que la API no da.

**Política de reenvío:** máximo **3 reenvíos**, separados al menos **24 horas**, con este **orden obligatorio de comprobaciones antes de tocar nada** —para no chocar con una aceptación simultánea **[MEDIR]** (`Q-2.3-70`)—:

1. `GET /repos/{o}/{r}/collaborators/{login}` → si `204`, **el estudiante ya entró: no se toca nada** (`404` si no lo es **[DOC]**, `Q-2.3-33`).
2. `GET /repos/{o}/{r}/invitations` → si la invitación sigue viva y no expirada, **sólo se reenvía el aviso por Canvas**, sin tocar GitHub, porque `PUT collaborators` es idempotente por contrato y **`DELETE` es la única operación peligrosa**.
3. **Sólo si `expired = true`** se hace `DELETE` seguido de `PUT`.

**Nunca `DELETE` seguido de `PUT` a ciegas.**

### A-101 · Máquina 4 — Captura de la versión a la fecha de cierre — ANULADA POR RG-024, RG-025, RG-026 y RG-188 en sus estados

> **Manda ahora A-213.** El disparador, la gracia de 60 s, el pre-cierre, `SIN_COMMITS` como información y no como error, y las advertencias de LFS y submódulos se conservan enteros. Lo que queda superado es que `PROGRAMADA`, `EN_VENTANA` y `RESOLVIENDO_SHA` fueran estados de `version_entrega` —**son fases del trabajo, en la máquina 6, y no existe fila antes de la captura**—, que `ERROR_TRANSITORIO` fuera un valor de la columna, y que `SUPERSEDIDA` fuera un estado.

Cubre **R2.4.5**, **R2.4.6**, **R2.4.7**, **R2.4.8**.

`PROGRAMADA` → `EN_VENTANA` → `RESOLVIENDO_SHA` → { `CAPTURADA` | `CAPTURADA_SIN_TAG` | `SIN_COMMITS` | `REVISAR` | `ERROR_TRANSITORIO` } ; y `SUPERSEDIDA` se aplica a la fila anterior cuando una recaptura la sustituye.

- **Se programa por `(entrega, sujeto)`**, con su fecha efectiva propia. Es la única forma de cumplir **R2.4.2** y **R2.4.3** a la vez.
- **Cuándo:** una fila de `fecha_efectiva` vigente con `due_at_utc` vencido y sin `version_entrega` vigente entra en cola. El trabajo corre **cada minuto**, con una **gracia de 60 segundos** para absorber el desfase de relojes. Un **trabajo de pre-cierre a T−2 min** fuerza la reconciliación de actividad de ese repositorio, para que el espejo esté al día en el momento del corte.
- **Sin commits anteriores al cierre** (más allá del inicial): estado `SIN_COMMITS`, **no error**. Es información legítima para el docente y aparece en el informe diario (**R2.6.2**).
- **Inmutabilidad:** ninguna actividad posterior modifica una fila capturada. El SHA es un puntero a un objeto Git inmutable; fecha, estado y tag quedan congelados (A-085).
- **Advertencias de contenido:** al capturar se comprueba la existencia de `.gitattributes` y `.gitmodules` en el árbol del commit. Si los hay, la versión se marca con advertencia visible para el corrector, porque **los objetos de Git LFS aparecen como punteros en los archivos comprimidos por defecto** **[DOC]** (`Q-2.4-49`) y el contenido de los submódulos no viaja. Es una bandera informativa, **no un error**. **La aplicación no descarga ni archiva el código**: entrega enlaces.
- **Repositorio archivado:** se registra el SHA y **no se desarchiva**; la versión queda `CAPTURADA_SIN_TAG` con motivo explícito, porque en un repositorio archivado todo es de sólo lectura **[DOC]** (`Q-2.4-47`). Desarchivar el repositorio de un estudiante sin que nadie lo pida es inaceptable. **Cómo llega un repositorio a estar archivado está en A-168**, que fija la regla de entrada que la revisión 1 no escribía: sólo por acción explícita de un profesor o porque alguien lo archivó en GitHub, **nunca por decisión del sistema**.

### A-102 · Selección del commit de cierre: doble fuente, regla escrita

**No se confía en `GET /commits?until=…&per_page=1`.** La documentación no dice si `until` es inclusivo en el segundo exacto, no dice si filtra por fecha de autor o de *committer*, y **no documenta ningún orden de retorno para ese endpoint** **[MEDIR]** (`Q-2.4-22`).

Procedimiento, defendible porque no descansa en ninguna semántica no documentada:

1. **Fuente primaria — el espejo propio:** `MAX(fecha_committer) ≤ fecha_corte` sobre la rama por defecto en la tabla `commit`, excluyendo `huerfano` y el commit inicial de la plantilla.
2. **Fuente de contraste — GitHub:** `GET /repos/{o}/{r}/commits?sha=<rama>&until=<corte>&per_page=100`, y **selección local** del commit de mayor `committer.date` de la ventana devuelta. Nunca se toma «el primero».
3. **Si coinciden** → `CAPTURADA`. **Si difieren** → se guardan **ambas** en `verificacion`, se toma la del espejo, el estado es **`REVISAR`** y se abre incidencia visible para el docente. **Si no hay ninguno** → `SIN_COMMITS`.

**La regla de corte se declara por escrito y se muestra en la interfaz:** «último commit cuya **fecha de committer** es anterior o igual a la fecha efectiva de cierre, en UTC». Declararla elimina la ambigüedad del segundo exacto y hace la respuesta defendible el 7 de octubre.

### A-103 · Recaptura ante cambio de fecha: dos requisitos que se tensionan

**R2.4.4** (mantener las fechas actualizadas) y **R2.4.7** (conservar las versiones registradas) se resuelven así, sin excepción:

| Situación | Qué ocurre |
|---|---|
| La fecha **se adelanta** a un instante ya pasado y ya había versión | Se captura de nuevo con la fecha nueva; la anterior queda `vigente=false`, `motivo='FECHA_ADELANTADA'`; **ambas quedan visibles** |
| La fecha **se retrasa** | La captura existente queda `vigente=false`, `motivo='FECHA_EXTENDIDA'`; se programa una captura nueva para el instante nuevo |
| La fecha cambia **antes** de que la captura ocurra | Simplemente se reprograma; no hay fila que superseder |

En los tres casos se registra en `bitacora` y, si la tarea tiene activada la comunicación correspondiente, **se publica un anuncio en Canvas informando del cambio de fecha** (**R2.6.6**). **Nada se pierde nunca.**

La clave de idempotencia del trabajo de captura incluye la fecha de corte en epoch, de modo que **la misma fecha nunca captura dos veces y una fecha distinta siempre captura de nuevo**.

### A-104 · El tag es comodidad; el SHA es la evidencia (Ley 4) — ANULADA POR RG-025 y RG-188 en la forma de registrar la etiqueta

> **Manda ahora A-213.** La Ley 4, el nombre del tag, la regla «si el tag no se puede crear la captura no falla», la no sobrescritura ante `422` y la URL por SHA se conservan enteros. Lo que queda superado es que la etiqueta se registrara con un booleano `tag_creado` y un motivo libre: es una **segunda enumeración independiente**, `tag_estado` de cinco valores y `tag_motivo` de **siete**, con `tag_error` guardando **siempre el texto literal de GitHub**.

Se crea un tag con `POST /repos/{o}/{r}/git/refs` **como comodidad de navegación para el corrector**. La evidencia normativa es `version_entrega.commit_sha` en la base, respaldada a diario (A-016).

- **Nombre del tag:** `entrega/<orden>-<entrega.slug>/v<n>`, donde `entrega.slug` y `n` están **definidos sin ambigüedad en A-172** —la revisión 1 nombraba un `<slug-entrega>` que no existía en el modelo y un `v<n>` del que no se decía si era el mismo contador que `version_entrega.intento`—. Lleva número de versión desde el principio para que **el nombre nunca haya que reescribirlo**: reescribir un tag es borrarlo y crearlo, y eso rompe referencias ya enviadas a los correctores.
- **Ejemplos:** `entrega/1-parcial/v1`, `entrega/2-final/v1`, `entrega/2-final/v2` (recaptura por cambio de fecha).
- **Si el tag no se puede crear, la captura no falla**: se registra el SHA, `tag_creado=false` con su motivo, y la interfaz muestra «versión registrada (sin etiqueta en GitHub)».
- **Idempotencia:** ante `422` al crear el tag se compara el SHA del tag existente; **si difiere, no se sobrescribe**: incidencia.
- **El acceso del corrector (R2.4.8, R2.7.4) se construye siempre sobre la URL por SHA**, `https://github.com/{org}/{repo}/tree/{sha}`, que es inmutable y **no depende de que el tag exista**. Junto a ella, la interfaz ofrece `…/compare/{sha_entrega_anterior}...{sha_entrega_actual}` cuando hay una entrega previa: para un corrector, ver **qué cambió entre la parcial y la final** es más útil que ver el árbol completo, y sale gratis del modelo porque las versiones son independientes (**R2.4.6**).
- **Y ese enlace abre, que es la mitad que faltaba.** El repositorio es `private: true` (A-065) y GitHub responde `404` a quien no tiene acceso **[DOC]** (`Q-2.3-35`): construir la URL sin gastar una llamada no sirve de nada si el humano al otro lado no puede abrirla. **A-163 concede la lectura al equipo docente antes de que el repositorio llegue a `OPERATIVO`**, y A-136 comprueba el estado de ese acceso antes de pintar el enlace. Sin esas dos piezas, **R2.4.8** y **R2.7.4** no se cumplen por mucho que el enlace exista.

### A-105 · Máquina 5 — Corrección — ANULADA POR RG-032, RG-033 y RG-205 en su estado `NO_PUBLICABLE`

> **Manda ahora A-214.** Las transiciones a `SIN_CORRECTOR`, a `PUBLICADA_CON_ADVERTENCIA` y a `ERROR_PUBLICACION` se conservan enteras, y también la regla de mostrar el error literal de Canvas. Lo que queda superado es **`NO_PUBLICABLE` como estado**: la máquina 5 queda en **ocho** estados y la imposibilidad de publicar se modela con **dos columnas ortogonales**, `publicable` y `motivo_no_publicable` de **diez** valores.

Cubre **R2.7.1**–**R2.7.7**.

`SIN_CORRECTOR` → `ASIGNADA` → `EN_CURSO` → `LISTA_PARA_PUBLICAR` → `PUBLICANDO` → { `PUBLICADA` | `PUBLICADA_CON_ADVERTENCIA` | `ERROR_PUBLICACION` }, con la salida lateral `NO_PUBLICABLE` alcanzable desde `LISTA_PARA_PUBLICAR`.

| Transición | Condición |
|---|---|
| → `SIN_CORRECTOR` | Se retiró el ayudante asignado (A-025). Incidencia `CORRECCION_SIN_CORRECTOR` |
| → `NO_PUBLICABLE` | **Antes de llamar a Canvas**: período de calificación cerrado **[DOC]** (`Q-2.7-64`), `grading_type=not_graded`, entrega moderada o anónima (A-138), o el estudiante no aparece en `gradeable_students` |
| → `PUBLICADA_CON_ADVERTENCIA` | La relectura posterior muestra `score` distinto de `entered_score` (A-140) |
| → `ERROR_PUBLICACION` | Canvas devolvió error. Se guarda el **cuerpo literal** en `publicacion_nota` y se muestra al corrector sin traducir |

Los mensajes de error de Canvas para estos casos **no están documentados** **[MEDIR]** (`Q-2.7-63`, `Q-2.7-64`), así que se muestran tal cual bajo una explicación en español, en lugar de traducirse a un diagnóstico inventado.

### A-106 · Máquina 6 — Trabajo de la cola — ANULADA POR RG-045 en su catálogo de ocho valores

> **Manda ahora A-215.** La semántica de `REINTENTAR` y de `REQUIERE_ATENCION` se conserva entera; lo que queda superado es el catálogo, que gana el estado terminal **`CANCELADO`** —noveno valor— con `motivo_cancelacion` de dieciséis valores, **fuera del índice de idempotencia**.

`PENDIENTE` → `EN_CURSO` → { `OK` | `REINTENTAR` | `BLOQUEADO` | `ESPERANDO_CREDENCIAL` | `ESPERANDO_LIMITE` | `REQUIERE_ATENCION` }.

`REINTENTAR` vuelve a `PENDIENTE` cuando vence `proximo_intento_en`. **`REQUIERE_ATENCION` es el estado de un trabajo que agotó sus reintentos**: aparece en el panel de operación con su error literal y **se puede reintentar manualmente desde la interfaz**. **Nada se pierde en silencio.**

### A-209 · Siete máquinas de estado, con `estados.py` como fuente única de TODOS los enumerados

**§9 pasa de seis máquinas a siete.** `backend/app/dominio/estados.py` contiene los siete enums con sus tablas de transiciones como dato, **más todos los estados de entidad del sistema**. **El `CHECK` de cada columna se genera desde ese módulo**, y **ningún enumerado del sistema se declara fuera de él** —tampoco en el módulo del adaptador que lo usa—.

| # | Máquina | Columna | Valores | `DEFAULT` |
|---|---|---|---|---|
| 1 | Mapeo (A-210) | `mapeo_github.estado` | **nueve**; único terminal `SUPERSEDIDO` | `SIN_DATO` |
| 2 | Repositorio (A-211) | `repositorio.estado` | **quince**, con `INACCESIBLE` | `ESPERANDO_INFORMACION` |
| 3 | Acceso del estudiante (A-212) | `acceso_repositorio.estado` | **diez**; **ninguno terminal** | `SIN_MAPEO` |
| 4 | Versión de entrega (A-213) | `version_entrega.estado` | **seis, todos terminales** | sin `DEFAULT` |
| 5 | Corrección (A-214) | `correccion.estado` | **ocho** | `SIN_CORRECTOR` |
| 6 | Trabajo de la cola (A-215) | `trabajo.estado` | **nueve**, con `CANCELADO` | `PENDIENTE` |
| 7 | **Mensaje saliente (A-216)** | `mensaje_saliente.estado` | **quince** | `PENDIENTE` |

**Las cuatro reglas de §9 rigen para las siete, sin excepción**, y dos pruebas las hacen verificables: **`test_check_coincide_con_enum`** y **`test_todo_codigo_tiene_etiqueta`** **fallan la construcción** si el `CHECK` desplegado difiere del enum o si falta una etiqueta en español; una tercera, `test_toda_transicion_declarada_tiene_origen_alcanzable`, cubre las tablas de transiciones. La función `transicion(maquina, desde, hacia)` lanza `TransicionInvalida`.

**Estados de entidad, que no son máquinas porque no necesitan tabla de transiciones**, y cuyos `CHECK` genera el mismo módulo:

- **De esta carta:** `tarea.estado`, `entrega.estado_validacion` (cuatro, A-203), `repositorio_base.estado` (cinco, A-208), `acceso_docente_repositorio.estado`, `curso.estado`, `estudiante.estado`, `membresia_curso.estado`, `fecha_efectiva.estado`, `incidencia.severidad`, `sincronizacion.resultado`, `identidad_git.estado` (cuatro, A-201), `invitacion_equipo.estado`.
- **De las integraciones:** `curso.via_anuncio_seccion` (cuatro), `curso.registro_estado` (cuatro), `curso.canal_comunicacion_activo`, `curso.comunicaciones_salientes` y `curso.modo_escritura` (dos cada una, A-225), `equipo_github_curso.via_efectiva`, `membresia_curso.org_github_estado` (cinco, A-186), `verificacion_vinculacion.origen` y `.resultado` (cinco, A-192), `presupuesto_api.ambito` y `.cubo` (A-219), `evento_webhook.estado` con `PENDIENTE_BLOQUE_2` (A-221), `mensaje_saliente.reserva` (A-228), `suscripcion_informe.origen_baja`, y los booleanos declarados `membresia_curso.es_via_compartida` y `.org_github_alta_por_app`.

**Estados derivados y NO persistidos, declarados aquí para que nadie los confunda con una máquina:** el **estado agregado de la entrega** para **R2.5.6** (nueve valores con precedencia, A-220); `tarea_operativa`, `tarea_activa_informe` y `tarea_visible`; los cinco estados por persona de la vista de personas; las cuatro marcas de reparto de la corrección; `contraste_canvas` (A-206); y el distintivo ámbar de la entrega con advertencias.

> **Ninguno de estos derivados se escribe en una columna de estado**, y una prueba de arquitectura falla si alguno se persiste. Los que necesitan latencia se precomputan en **`resumen_tarea` con `calculado_en` visible**, que es una **caché declarada** y no una segunda verdad.

**Por qué la lista importa menos que las pruebas.** Un enumerado declarado en un adaptador **escapa a las dos pruebas** y aparece en pantalla en inglés y en mayúsculas el día de la demostración.

Sirve a **R2.2.6**, **R2.3.11**, **R2.5.5**, **R2.5.6**, **R2.7.7** y §4 del enunciado.

### A-210 · Máquina 1: `SIN_DATO` es una fila persistida, y hay cinco motivos de invalidación

**1 · Se crea una fila de `mapeo_github` por estudiante, en la misma transacción que lo espeja**, con `estado = 'SIN_DATO'` y `cuenta_github_id` nulo. La columna lleva `DEFAULT 'SIN_DATO'` y `cuenta_github_id` es **nullable**. **`mapeo_github.estado` no se deriva al vuelo en ninguna consulta**, que es la regla 1 de §9.

> **Por qué la fila se crea antes de tener dato.** **R2.2.6** exige mostrar claramente para qué estudiantes falta información. Con filas perezosas, **un estudiante sin cuenta declarada no tendría fila** y cada vista tendría que reimplementar la regla de ausencia por su cuenta. Es la misma disciplina que aplica `repositorio` y por el mismo motivo.

**Invariante que lo hace posible:** índice único parcial **`(curso_id, estudiante_id) WHERE estado <> 'SUPERSEDIDO'`** —exactamente **una fila viva por estudiante y curso**, más el histórico *append-only* de las supersedidas (A-078)—. Los dos índices sobre `estado = 'VIGENTE'` de A-077 se conservan sin cambio.

**Vocabulario, porque son dos máquinas distintas:** «Sin cuenta de GitHub» en la vista de personas se lee de **`mapeo_github.estado = 'SIN_DATO'`**, nunca de la ausencia de fila. **`SIN_MAPEO` queda reservado a `acceso_repositorio`** (máquina 3), donde significa «este integrante no tiene mapeo vigente y por eso no hay a quien invitar». Comparten etiqueta visible y **no comparten código**.

**2 · `mapeo_github.motivo_invalidacion` es un enum cerrado de cinco valores**, no de tres: `RENOMBRADO`, `CUENTA_ELIMINADA`, `LOGIN_REASIGNADO`, **`ESTUDIANTE_RETIRADO`** y **`CUENTA_NO_ELEGIBLE`** (A-187). Un estudiante retirado y una cuenta no elegible **son hechos distintos que exigen acciones distintas**, y colapsarlos dejaría sin nombre a uno de los dos.

Se conserva íntegro todo lo demás de A-091: los nueve estados, la columna «cuenta como falta información», el umbral de 15 minutos que saca un `RECIBIDO` atascado a `/operacion`, y la guarda de A-093 según la cual **sólo `VIGENTE` la cruza**. **Una invalidación nunca borra la fila**: se supersede y el histórico queda.

### A-211 · Máquina 2: `INACCESIBLE`, el disparador de `DEGRADADO` y la salida de `ERROR_PERMANENTE`

**1 · La máquina 2 gana un decimoquinto estado, `INACCESIBLE`**, con `repositorio.motivo` de lista cerrada de **cuatro** valores y `repositorio.inaccesible_desde`:

```
BORRADO_EN_GITHUB                     -- webhook repository, accion deleted
TRANSFERIDO_FUERA_DE_LA_ORG           -- accion transferred con destino <> curso.github_org_id
FUERA_DEL_ALCANCE_DE_LA_INSTALACION   -- installation_repositories, repositories_removed
APP_SIN_ACCESO                        -- dos ciclos de reconciliar_actividad con 404 o 403 no transitorio
```

> **`HUERFANO` no existe como valor de `repositorio.estado`.** La palabra está tomada por `commit.huerfano` (A-072) con el significado «historia reescrita», y **A-154 prohíbe el mismo término para dos hechos**. `INACCESIBLE` describe además dos casos que `HUERFANO` no cubría —el repositorio sacado del alcance de la instalación y el que la App deja de poder leer—, y sin ellos el sistema tendría que **fingir que un repositorio ilegible sigue operativo**.

- **Orígenes:** alcanzable desde **todo estado en que `github_repo_id` no es nulo** —`CREADO_SIN_CONTENIDO`, `CONTENIDO_LISTO`, `CONFIGURANDO_ACCESOS`, `OPERATIVO`, `DEGRADADO`, `FUERA_DE_ALCANCE` y `ARCHIVADO`—. El motivo inferido `APP_SIN_ACCESO` **no se aplica nunca** mientras el estado sea `CREANDO` o `CREADO_SIN_CONTENIDO`, porque A-096 declara ahí el `404` como transitorio.
- **Salidas, exactamente dos:** (a) comprobación positiva —un webhook que lo devuelve al alcance o una lectura `200` en la reconciliación—, tras la cual el repositorio vuelve **al estado que dicte el predicado de A-092 en ese instante**; (b) la acción explícita «sustituir repositorio» (A-202). **`INACCESIBLE` no tiene transición a `LISTO_PARA_CREAR`**: la sustitución crea una fila nueva que nace ahí.
- **`ERROR_PERMANENTE` no describe este hecho.** A-098 **no** gana el subtipo `REPO_ELIMINADO_EN_GITHUB` y **conserva sus siete subtipos**: `ERROR_PERMANENTE` es **una creación que no pudo completarse**, `INACCESIBLE` es **un repositorio que existió y desapareció**. La clasificación `LLAMADA_NO_AUTORIZADA` de A-193 es del mecanismo de capacidades, **no un octavo subtipo**.
- **Contabilidad, sin excepción:** `INACCESIBLE` cuenta en el universo de métricas —`github_repo_id` no nulo—, conserva su serie histórica y su timeline, **queda fuera de las alertas de R2.5.3 y R2.5.4** —no hay nada que leer— y se muestra **en columna propia** en la barra de **R2.5.5** y en la tabla de **R2.3.11**, junto a `ARCHIVADO` y `FUERA_DE_ALCANCE`, **nunca sumado a `OPERATIVO` ni oculto**. Etiqueta: «No accesible en GitHub».
- **Incidencia `REPOSITORIO_INACCESIBLE`**, severidad `ADVERTENCIA`, **una por repositorio y no una por versión**, con el motivo y el recuento de versiones afectadas. **La fila «repositorio inaccesible» no abre `VERSION_REVISAR`**: con seis versiones capturadas se abrirían siete incidencias del mismo hecho. En consecuencia **`VERSION_REVISAR` queda con cuatro motivos** —`SHA_NO_ALCANZABLE`, `TAG_BORRADO`, `TAG_MOVIDO`, `TAG_OCUPADO`—.

**2 · `DEGRADADO → CONFIGURANDO_ACCESOS` tiene un único disparador:** **aparece un miembro del conjunto objetivo de accesos que no tiene todavía ninguna fila de `acceso_repositorio`**. `CONFIGURANDO_ACCESOS` significa «la aplicación está emitiendo un conjunto de accesos», y **una reparación no es una emisión**. En cualquier otro caso el repositorio **permanece en `DEGRADADO` y la reparación ocurre sin cambio de estado**:

| Motivo de `DEGRADADO` | Quién repara | Cambia de estado |
|---|---|---|
| `FALTA_ACEPTAR_INVITACION_GITHUB`, `INVITACION_EXPIRADA`, acceso `DESAPARECIDA` | `reconciliar_accesos`, con el orden obligatorio de A-100 sobre filas **que ya existen** | **No.** Cumplido el predicado entero, pasa **directamente `DEGRADADO → OPERATIVO`** |
| `SIN_ACCESO_DOCENTE` con fila de `acceso_docente_repositorio` **inexistente** | Hay un acceso nuevo que emitir | **Sí**, vuelve a `CONFIGURANDO_ACCESOS` |
| `SIN_ACCESO_DOCENTE` o `ERROR_AL_CONCEDER_ACCESO` con fila en `PENDIENTE`, `ERROR` o `REVOCADO` | `sincronizar_acceso_docente` | **No** |
| `INTEGRANTE_SIN_MAPEO`, `INTEGRANTE_PENDIENTE_EN_CANVAS` | Nadie: no hay nada que emitir todavía | **No**, sigue `DEGRADADO` con el motivo escrito |

**Prueba obligatoria:** un ciclo de reconciliación sobre un repositorio `DEGRADADO` por invitación sin aceptar **no cambia el estado**; la entrada de un integrante nuevo **sí** lo cambia.

**3 · Reactivar un sujeto no reemite nada por decreto.** La transición `FUERA_DE_ALCANCE → OPERATIVO | DEGRADADO` **no reemite ninguna invitación ni concede ningún acceso por sí misma**: en la misma transacción en que `materializar_sujetos` reactiva el sujeto se **encolan `reconciliar_accesos` y `sincronizar_acceso_docente`**, y son ellos los que aplican sus reglas normales, incluido el orden obligatorio de A-100 **sin excepciones**. **El estado tras reactivar es el que dicte el predicado de A-092 en ese instante**, y **nunca se escribe `OPERATIVO` por suposición** ni se reescribe `repositorio.listo_en`. `acceso_repositorio.reenvios` vuelve a cero **únicamente** en esa transición, y el reinicio queda en `bitacora`. **Prueba obligatoria:** reactivar un sujeto cuyo estudiante ya era colaborador **no produce ninguna llamada de escritura a GitHub**.

**4 · Salida de `ERROR_PERMANENTE`: destino por subtipo**, porque devolver a `LISTO_PARA_CREAR` un repositorio cuyo bloqueo es del mapeo produce el mismo error en el ciclo siguiente:

| Subtipo de A-098 | Acción | Permiso | Destino |
|---|---|---|---|
| `ORG_PROHIBE_CREAR_REPOS`, `ORG_EXIGE_2FA`, `CUENTA_BLOQUEADA_POR_ORG`, `PERMISO_INSUFICIENTE` | «Reintentar» | `tarea.administrar` | `LISTO_PARA_CREAR` |
| `NOMBRE_OCUPADO_POR_TERCERO` | «Reintentar», que **vuelve a ejecutar las cinco condiciones de A-097** antes de crear | `tarea.administrar` | `LISTO_PARA_CREAR`, o de nuevo `ERROR_PERMANENTE` con el detalle de qué condición falló |
| `CUENTA_ELIMINADA`, `LOGIN_ES_ORGANIZACION` | «Corregir la cuenta de GitHub», que supersede el mapeo anterior | `mapeo.editar` | `ESPERANDO_INFORMACION` con motivo `SIN_MAPEO_GITHUB` |

Al salir se ponen `intentos = 0` y `proximo_intento_en = now()`, y se **vacían** `clase_error`, `error_codigo` y `error_mensaje_literal` **sólo después** de escribirlos en `bitacora` con `antes` y `despues`. La incidencia asociada se cierra en la misma transacción. **El aprovisionamiento automático nunca saca a un repositorio de `ERROR_PERMANENTE`**, ni siquiera si la causa desaparece sola: es lo que lo separa de `BLOQUEADO`.

### A-212 · Máquina 3: diez valores, y ninguna revocación se ejecuta sola

**1 · `acceso_repositorio.estado` es un enum cerrado de diez valores, `DEFAULT 'SIN_MAPEO'`, y ninguno es terminal:** `SIN_MAPEO`, `POR_INVITAR`, `INVITADO`, `ACCESO_DIRECTO`, `ACEPTADO`, `EXPIRADA`, `DESAPARECIDA`, **`REVOCACION_PROPUESTA`**, **`REVOCACION_PROGRAMADA`**, **`REVOCADO`**. **`RETIRADO` no existe**, ni `retirado_en`, ni `motivo_retiro`.

| Estado | Significado | Etiqueta (A-155) |
|---|---|---|
| `REVOCACION_PROPUESTA` | Canvas dice que ya no pertenece; **ninguna persona ha decidido** | «Acceso por revisar» |
| `REVOCACION_PROGRAMADA` | Una persona decidió revocar, **el aviso salió** y hay hora de ejecución escrita | «Se retira el DD-MM a las HH:MM» |
| `REVOCADO` | El `DELETE` se ejecutó con éxito | «Acceso retirado» |

**Por qué tres y no uno:** una revocación **decidida y avisada, con hora escrita**, y una que **espera decisión** son dos situaciones distintas del mismo acceso, y **R2.3.9**, **R2.3.10** y **R2.3.11** exigen mostrar el estado del acceso de forma clara. Con un solo valor, esa diferencia sólo se podría leer de un `detalle` en JSON, **que ninguna vista puede filtrar ni ordenar y que ninguna prueba de transición puede vigilar**.

**2 · La baja nunca revoca sola.** Confirmada la ausencia en **dos ciclos consecutivos** de `sync_grupos` (`pertenencia_grupo.ciclos_ausente`), la fila pasa a `REVOCACION_PROPUESTA`, se abre **`GRUPO_INCOMPLETO`** con `detalle.subtipo ∈ {INTEGRANTE_SALIO_DEL_GRUPO, TRASLADO_DE_GRUPO}`, y aparece en Pendientes con **dos botones** —«revocar acceso» y «mantener acceso»—, ambos con registro en `bitacora`. **La decisión vive en la fila de `acceso_repositorio` y en ningún otro sitio**: la incidencia se cierra cuando la fila abandona `REVOCACION_PROPUESTA`, y **no hay dos lugares donde consultar si alguien ya decidió**.

**3 · El repositorio no cambia de estado** por ninguno de los tres valores nuevos: el predicado de `OPERATIVO` cuantifica sobre pertenencias `accepted` vigentes. Se muestra un distintivo ámbar «1 acceso por revisar», **sin transición**.

**4 · Ningún estado es terminal.** `REVOCADO → POR_INVITAR` si la persona vuelve al grupo; `REVOCACION_PROPUESTA` y `REVOCACION_PROGRAMADA` vuelven a `ACEPTADO` o `ACCESO_DIRECTO` si la pertenencia se restaura o si un profesor pulsa «mantener acceso».

**5 · Cautela de padrón:** si un ciclo devuelve **menos del 60 %** de las pertenencias del grupo **no se aplica ninguna baja** y se abre `ROSTER_SOSPECHOSO` (A-044, A-045).

**6 · Ninguna transición a `REVOCACION_PROGRAMADA` ocurre sin decisión humana, tampoco la del traslado de grupo.** El traslado —el estudiante figura `accepted` en **exactamente otro** grupo del mismo `conjunto_grupos`— se detecta en el mismo ciclo de `sync_grupos`, abre `GRUPO_INCOMPLETO` con `detalle.subtipo = TRASLADO_DE_GRUPO`, deja la fila en **`REVOCACION_PROPUESTA`** con `motivo_revocacion = 'TRASLADO_DE_GRUPO'` y envía de inmediato el aviso con las instrucciones para clonar. **A las 24 horas no ocurre nada solo.** Si figura en **dos** grupos no es un traslado: rige A-049. **Por qué:** el aviso puede no salir —`canal_comunicacion_activo = BLOQUEADO`, A-227—, y una revocación automática apoyada en un aviso que quizá no salió **retira el acceso de un estudiante a un repositorio donde tiene trabajo sin que nadie lo haya mirado**.

**7 · La gracia se cuenta desde la decisión humana**, no desde la detección: **siete días naturales** en el caso general, **24 horas** con `TRASLADO_DE_GRUPO`, y **cero** con `ACCESO_INESPERADO` o `MAPEO_CORREGIDO` —el acceso está en manos de quien no corresponde y **cada hora es exposición del trabajo de otra persona**—, donde el aviso se envía después.

**8 · Guarda de aviso, que es la que cierra el caso.** Una fila **no puede pasar a `REVOCACION_PROGRAMADA` sin `avisada_en` escrito** o, con el canal `BLOQUEADO`, **sin la declaración escrita del profesor de que avisó por otra vía**, que queda en `bitacora`. Es un `CHECK` en base, no una comprobación en código.

**9 · Ocho columnas de revocación, sin sinónimos:** `propuesta_en`, `revocacion_decidida_por`, `revocacion_decidida_en`, `avisada_en`, `revocar_no_antes_de`, `revocado_en`, `revocado_por` y `motivo_revocacion`. **`revocacion_aprobada_por` y `revocacion_aprobada_en` no existen.** **La fila no se borra nunca.**

**10 · `motivo_revocacion` es un enum cerrado de seis valores:** `SALIDA_DE_GRUPO`, `TRASLADO_DE_GRUPO`, `MAPEO_CORREGIDO`, `RETIRO_DEL_CURSO`, `ACCESO_INESPERADO`, `ACCION_DOCENTE`. **`RETIRO_DE_MEMBRESIA` no pertenece a este enum**: el retiro de un docente vive en `acceso_docente_repositorio` y lo ejecuta `revocar_acceso_docente` con los tres planos de A-188.

**11 · Un solo ejecutor del `DELETE`.** El trabajo **`revocar_acceso_estudiante`** (A-218) es el **único** que ejecuta `DELETE /repos/{org}/{repo}/collaborators/{login}` para un estudiante, comprueba `revocar_no_antes_de` antes de llamar, y **si el `DELETE` falla la fila no pasa a `REVOCADO`, el mensaje de confirmación no sale y se abre incidencia**: **nunca se informa de una retirada que no ocurrió**. `reconciliar_accesos` **propone y no ejecuta**. El endpoint `POST /api/cursos/{id}/repositorios/{rid}/accesos/{eid}/revocar` **marca la decisión y encola** (A-226).

**12 · Ninguna revocación es silenciosa.** Al pasar a `REVOCACION_PROGRAMADA` sale **`aviso_revocacion_acceso`** —qué repositorio, por qué, la fecha y hora exactas con zona escrita y cómo conservar el trabajo—, y al ejecutarse sale **`confirmacion_revocacion_acceso`**. **Los dos mensajes no son comunicaciones de R2.6.7**: son **notificaciones obligatorias del sistema**, parte de la transacción de revocación, **sin interruptor, sin tope y sin fila en `regla_comunicacion`**. En consecuencia, **el evento `salida_de_grupo` no entra en el catálogo de A-130**, que conserva sus siete eventos: **un aviso que se puede apagar no puede ser parte obligatoria de una transacción que retira un acceso**.

**13 · Vigencia de la pertenencia.** `pertenencia_grupo` gana exactamente tres columnas: `activa_desde timestamptz NULL`, `activa_hasta timestamptz NULL` y `ciclos_ausente smallint NOT NULL DEFAULT 0`. **`entro_en` y `salio_en` no existen.** El recorte de la ventana de participación se calcula sobre ellas: `inicio = max(due_at_entrega_anterior_del_sujeto, repositorio.creado_en, activa_desde)` y `fin = min(due_at_de_esta_entrega_del_sujeto, coalesce(activa_hasta, 'infinity'))` (A-122, A-173).

Pendientes gana el bloque **«accesos por revisar»** con el recuento de commits que esa persona subió a ese repositorio.

### A-213 · Máquina 4: no hay fila antes de la captura, y la etiqueta es una enumeración aparte

**1 · `PROGRAMADA`, `EN_VENTANA` y `RESOLVIENDO_SHA` son fases del trabajo de captura en la máquina 6**, no valores de `version_entrega.estado`, y **no se persiste ninguna fila de `version_entrega` antes de que el SHA quede resuelto**.

> **El motivo está en la propia A-101:** el disparador de la captura es «una fila de `fecha_efectiva` vigente con `due_at_utc` vencido **y sin `version_entrega` vigente** entra en cola». **Si existiera una fila `PROGRAMADA` vigente, la captura no se encolaría nunca** y **R2.4.5** quedaría incumplido en silencio.

**Cuándo se inserta la fila, exactamente:** al terminar la **fase 1** del trabajo, que resuelve el SHA contra el espejo y contra GitHub (A-102), **en la misma transacción que cierra esa fase**. Nace con uno de los seis estados terminales y con `tag_estado` `PENDIENTE` o `NO_APLICA`. `SIN_REPOSITORIO` y `ERROR` **son filas terminales legítimas**, escritas también al terminar la fase 1.

El botón **«capturar ahora»** se ofrece sobre la **`fecha_efectiva` vencida sin versión vigente**, no sobre una fila `PROGRAMADA`, y su endpoint lleva la clave de idempotencia de A-103. La barra «registrando versiones: 43 de 60» se calcula sobre las `fecha_efectiva` vencidas, **no sobre filas de `version_entrega`**.

**2 · `version_entrega.estado` es un enum cerrado de seis valores, todos terminales y sin `DEFAULT`:** `CAPTURADA`, `CAPTURADA_SIN_TAG`, `SIN_COMMITS`, `REVISAR`, `SIN_REPOSITORIO`, `ERROR`. **`SUPERSEDIDA` no es un estado**: se expresa con `vigente = false` y su `motivo`, de modo que **se conserva para siempre que aquella fila fue `CAPTURADA` o `SIN_COMMITS`**.

**3 · La etiqueta de GitHub es una segunda enumeración independiente:** `tag_estado ∈ {PENDIENTE, CREADO, CONFLICTO, FALLIDO, NO_APLICA}`, con **`tag_motivo` de siete valores** —`REPOSITORIO_ARCHIVADO`, `LIMITE_API`, `SHA_DISTINTO`, `PERMISO_INSUFICIENTE`, `SIN_COMMITS`, `DESCONOCIDO` y **`REPOSITORIO_INACCESIBLE`**— y **`tag_error` guardando siempre el texto literal de GitHub**. `NO_INTENTADO` **se retira**: nadie puede producirlo. **Separar los dos ejes es lo que permite que un `403` de límite al crear la etiqueta no impida registrar la evidencia**, que es lo único que **R2.4.5** exige. `'TAG_OCUPADO'` **no es un valor de `tag_error`**: es un motivo de la incidencia `VERSION_REVISAR`.

**4 · Invariante escrito por implicaciones, no como equivalencia:**

- `estado = CAPTURADA` ⟹ `tag_estado = CREADO`
- `estado = CAPTURADA_SIN_TAG` ⟹ `tag_estado ∈ {PENDIENTE, CONFLICTO, FALLIDO}`
- `estado ∈ {SIN_COMMITS, SIN_REPOSITORIO, ERROR}` ⟹ `tag_estado = NO_APLICA`
- `estado = REVISAR` ⟹ `tag_estado ∈ {CREADO, PENDIENTE, CONFLICTO, FALLIDO}` — `REVISAR` describe una discrepancia de SHA entre espejo y GitHub (A-102) y **es ortogonal a la etiqueta**

**5 · Dos transiciones posteriores a la inserción, y sólo dos:** **`CAPTURADA_SIN_TAG → CAPTURADA`**, cuando la fase de etiqueta la crea; y **`CAPTURADA → CAPTURADA_SIN_TAG`**, con **un solo origen declarado**: el bloque de verificación de etiquetas del barrido nocturno y el manejador del webhook `delete` con `ref_type = tag`. Las dos escriben `estado` y `tag_estado` **en la misma sentencia**.

> **Por qué la transición inversa y no relajar el `CHECK`.** `CAPTURADA` significa «evidencia registrada **y anclada por una referencia**»; dejarla en `CAPTURADA` sin etiqueta viva convertiría el invariante en un adorno. Sin ella, además, **la primera escritura de `tag_estado = CONFLICTO` sobre una fila `CAPTURADA` aborta la transacción del barrido nocturno en producción.**

Los tres desenlaces quedan escritos sin contradecir el `CHECK`: etiqueta borrada → `CAPTURADA_SIN_TAG` con `tag_estado = PENDIENTE` y recreación por la cola; etiqueta movida a otro SHA → `CAPTURADA_SIN_TAG` con `tag_estado = CONFLICTO`, `tag_motivo = SHA_DISTINTO` y **nunca se sobrescribe** (A-104); repositorio inaccesible o archivado → **no se llama** y `tag_motivo` recoge el porqué.

**6 · `SIN_COMMITS` queda reservado a lo que A-101 le reserva**: el repositorio existe y no hay commits contables anteriores al cierre. El caso «no había repositorio» es `SIN_REPOSITORIO` (A-204).

**7 · El conjunto terminal que cierra `CERRADA_REGISTRADA` (A-220) son los seis valores, sin excepción**: con un solo sujeto en `SIN_REPOSITORIO` o en `ERROR`, una entrega cerrada se quedaría **para siempre** en `CERRADA_CAPTURANDO` y **R2.5.6** mostraría un estado falso de forma indefinida.

### A-214 · Máquina 5: ocho estados, y la imposibilidad de publicar es una bandera con motivo

**1 · `NO_PUBLICABLE` se retira de la máquina 5, que queda con ocho estados**, `DEFAULT 'SIN_CORRECTOR'`:

`SIN_CORRECTOR` → `ASIGNADA` → `EN_CURSO` → `LISTA_PARA_PUBLICAR` → `PUBLICANDO` → { `PUBLICADA` | `PUBLICADA_CON_ADVERTENCIA` | `ERROR_PUBLICACION` }

**2 · Dos columnas ortogonales:** `correccion.publicable` (booleano `NOT NULL DEFAULT true`) y `correccion.motivo_no_publicable`, enum cerrado de **diez** valores: `PERIODO_CERRADO`, `NO_GRADED`, `GPA_SCALE`, `LETTER_GRADE_SIN_ESQUEMA`, `MODERADA_O_ANONIMA`, `NO_GRADEABLE`, `ENTREGA_DESPUBLICADA`, `ENTREGA_ELIMINADA`, `SUJETO_EXCLUIDO` y **`PUBLICACION_NO_AUTORIZADA`** (A-193).

**Efecto exacto de la bandera:** con `publicable = false` la **única** transición prohibida es `LISTA_PARA_PUBLICAR → PUBLICANDO`; el botón de publicar aparece **deshabilitado con el motivo escrito y su enlace a Canvas**. **Todas las demás transiciones siguen disponibles**: la corrección se reparte, se abre, se trabaja y se marca como lista con normalidad, porque **la corrección local es trabajo docente válido aunque la nota no pueda viajar a Canvas**, y **R2.7.1**, **R2.7.2**, **R2.7.3** y **R2.7.7** siguen funcionando sobre ella.

**Una corrección puede nacer con `publicable = false`**, que es lo que A-138 fila 3 pide literalmente al vincular una entrega con `grading_type = not_graded`. **La fila 3 de A-138 se lee así**: «nace con `publicable = false` y su motivo», y no «nace `NO_PUBLICABLE`».

**3 · Quién reevalúa la bandera, sin huecos:**

| Motivo | Quién lo reevalúa |
|---|---|
| `PERIODO_CERRADO`, `NO_GRADEABLE` | `reconciliar_notas_canvas` en cada ciclo, y el pre-chequeo de A-140 al abrir la pantalla |
| `NO_GRADED`, `GPA_SCALE`, `LETTER_GRADE_SIN_ESQUEMA`, `MODERADA_O_ANONIMA`, `ENTREGA_DESPUBLICADA`, `ENTREGA_ELIMINADA` | `sync_tareas_y_fechas`, que detecta el cambio de configuración y el valor de `entrega.publicada` |
| `SUJETO_EXCLUIDO` | `materializar_sujetos`, y la acción «readmitir» |
| `PUBLICACION_NO_AUTORIZADA` | El mecanismo único de capacidades de A-193 |

**Cuando la causa desaparece, la bandera vuelve a `true` sola, sin tocar el estado**, y el aviso se retira de la pantalla.

**4 · La espera de credencial vive en la máquina 6, nunca en la máquina 5.** Una publicación detenida por falta de credencial válida **no cambia el estado de la corrección**: permanece en **`PUBLICANDO`** y el trabajo asociado queda en **`ESPERANDO_CREDENCIAL`**, que es donde A-036 paso 3 ya la sitúa. **La máquina 5 no gana ningún estado.** Para que la etiqueta sea legible sin derivar el estado, `correccion` recibe **`trabajo_publicacion_id`** (FK nullable), escrita en la misma transacción en que pasa a `PUBLICANDO`; la pantalla muestra el chip «Publicando» **y a su lado** el distintivo «Esperando credencial de Canvas», con quién puede arreglarlo y cuándo se reintentará. Si la publicación se **cancela**, la corrección vuelve a **`LISTA_PARA_PUBLICAR`** con el aviso escrito. Se conservan la promoción automática de la primera credencial de respaldo válida, la conservación íntegra del *payload*, la incidencia **`SIN_CREDENCIAL_DE_RESPALDO`** y la regla de que lo que no depende de Canvas no se detiene.

**5 · Banderas ortogonales de la máquina 5, enumeradas:** `publicable` con `motivo_no_publicable`; `version_desactualizada`; `reclamo_abierto`; `sin_commits`; `reconocimiento_sin_codigo` (A-230). **`contraste_canvas` no es una bandera de `correccion`: es una derivación** (A-206). **`asignacion_correccion` no tiene columna de estado** (A-206).

El distintivo rojo **«No publicable en Canvas — *motivo*»** aparece junto al chip, en la matriz de **R2.7.7** y en la pantalla de corrección.

### A-215 · Máquina 6: `CANCELADO` es el noveno estado, y queda fuera del índice de idempotencia

`trabajo.estado` queda con **nueve** valores, `DEFAULT 'PENDIENTE'`: `PENDIENTE`, `EN_CURSO`, `OK`, `REINTENTAR`, `BLOQUEADO`, `ESPERANDO_CREDENCIAL`, `ESPERANDO_LIMITE`, `REQUIERE_ATENCION`, **`CANCELADO`**.

**`trabajo.motivo_cancelacion` es un catálogo cerrado de dieciséis valores:** `SUJETO_DESACTIVADO`, `ESTUDIANTE_RETIRADO`, `MAPEO_CAMBIADO`, `MAPEO_INVALIDADO`, `ENTREGA_DESVINCULADA`, `ENTREGA_EXCLUIDA`, `ASSIGNMENT_ELIMINADO_EN_CANVAS`, `TAREA_ARCHIVADA`, `TAREA_INCONSISTENTE`, `REPOSITORIO_ARCHIVADO`, `REPOSITORIO_SUSTITUIDO`, `REPOSITORIO_INACCESIBLE`, `REPOSITORIO_EN_ERROR`, `VERSION_SUPERSEDIDA`, `FECHA_REPROGRAMADA`, `CURSO_ARCHIVADO`.

**Las tres cosas que hay que hacer a la vez:**

1. `CANCELADO` entra en `backend/app/dominio/estados.py`.
2. `CANCELADO` entra en el `CHECK` de `trabajo.estado`, generado desde ese enum.
3. **`CANCELADO` queda FUERA del índice único parcial de `trabajo.clave_idempotencia`**, que sigue cubriendo `PENDIENTE`, `EN_CURSO`, `REINTENTAR`, `BLOQUEADO`, `ESPERANDO_CREDENCIAL` y `ESPERANDO_LIMITE`. **Dejarlo fuera es lo que permite reencolar con la misma clave cuando la precondición se cumple de nuevo.**

**`CANCELADO` se pinta en ámbar, nunca en rojo**, con el motivo traducido al español, y es filtrable por motivo en `/operacion`. Toda cancelación escribe `bitacora` con actor de sistema y `correlacion_id`, y **abre incidencia sólo cuando afecta a algo que el docente esperaba**.

**Prueba parametrizada obligatoria:** por cada tipo del catálogo cerrado de A-218, se encola el trabajo, se invalida la precondición y se comprueba que **no sale ninguna petición** y que el motivo queda escrito.

### A-216 · Máquina 7 — `mensaje_saliente`: quince estados, siete guardas y veinte motivos

**1 · `mensaje_saliente.estado` es la séptima máquina**, con enum cerrado de **quince** valores y `DEFAULT 'PENDIENTE'`:

| Estado | Significado | Etiqueta (A-155) |
|---|---|---|
| `PROGRAMADO` | Tiene hora futura de envío | «Programado para el DD-MM a las HH:MM» |
| `DIFERIDO` | Retenido por una **condición externa reversible**, no por un fallo | «En espera» |
| `PENDIENTE` | Listo para que `despachar_outbox` lo tome | «En cola» |
| `EN_CURSO` | Tomado por el despachador | «Enviando» |
| `ENVIADO` | Confirmado por el proveedor | «Enviado» |
| `REINTENTAR` | `5xx`, red o tiempo agotado | «Reintentando, próximo intento a las HH:MM» |
| `ESPERANDO_LIMITE` | `429` o `403` de límite | «Esperando a Canvas por límite de uso» |
| `ESPERANDO_CREDENCIAL` | `401`; dispara A-036 entero | «Esperando credencial de Canvas» |
| `BLOQUEADO` | `403` por permiso retirado; reevaluado cada 30 min | «Bloqueado por permisos de Canvas» |
| `REQUIERE_ATENCION` | `EN_CURSO` vencido hace más de 10 min: **pudo haberse enviado** | «Pudo haberse enviado» |
| `FALLIDO` | Agotados los 6 intentos, o `4xx` permanente | «No se pudo enviar» |
| `CANCELADO` | **La entidad que lo originó desapareció** | «Cancelado» |
| `SUPRIMIDO` | **La condición que lo originó ya no se cumple** | «No se envió (filtrado)» |
| `CADUCADO` | Venció `caduca_en`, o la retención se prolongó | «Ya no tenía sentido» |
| `RETRACTADO` | Retirado a petición del docente | «Retirado» |

**Terminales:** `ENVIADO`, `FALLIDO`, `CANCELADO`, `SUPRIMIDO`, `CADUCADO`, `RETRACTADO`. Un `FALLIDO` **no se reintenta solo nunca más**: sólo por acción del docente.

**2 · Los motivos viajan en `motivo_estado`, nunca en el nombre del estado.** `DIFERIDO_POR_PUBLICACION`, `DIFERIDO_POR_CUOTA`, `CANCELADO_POR_ARCHIVO`, `RETENIDO_POR_SUSPENSION`, `CADUCADO_POR_SUSPENSION` y `RETENIDO_POR_MODO` **no son estados**. Si cada causa nueva de espera añadiera un estado, **el enum dejaría de ser cerrado en la práctica**.

**3 · `REQUIERE_ATENCION` significa exactamente una cosa y no se usa para otra:** un mensaje que quedó `EN_CURSO` más de 10 minutos y **pudo haberse enviado**. **No se usa para un envío que consta que no salió**, y estos tres casos se escriben con el estado que les corresponde:

| Caso | Estado correcto |
|---|---|
| Segunda publicación de anuncio fallida tras la degradación en caliente | **`FALLIDO`** con `ultimo_error_literal`: es un `4xx` permanente |
| Canal 1 y canal 2 de Canvas caídos (A-227) | **`BLOQUEADO`** con su motivo y reevaluación cada 30 min |
| Cuota de correo agotada (A-228) | **`DIFERIDO`** con `motivo_estado = 'CUOTA_AGOTADA'` |

**Por qué.** La máquina 7 existe para responder «¿por qué no le llegó?» **con una sola respuesta correcta**. `REQUIERE_ATENCION` es el único estado que **declara incertidumbre**, y por eso el diseño elige no reenviarlo a ciegas; usarlo cuando **se sabe** que el mensaje no salió convierte la única señal de duda del sistema en ruido y deja sin reintento a mensajes que sí deben reintentarse.

**4 · Siete guardas, en orden cerrado, en una sola función.** `despachar_outbox` evalúa **siete guardas en este orden exacto**, y **la primera que se cumple decide el desenlace y escribe `motivo_estado`**. El orden está escrito **una sola vez**, en **`guardas_outbox(mensaje) -> (estado, motivo) | None`** de `backend/app/dominio/comunicaciones.py`, y **ninguna otra parte del sistema decide por su cuenta si un mensaje puede salir**. La pantalla «por qué no salió» **llama a esa misma función**.

| # | Guarda | Desenlace | `motivo_estado` |
|---|---|---|---|
| 1 | `caduca_en` vencido | `CADUCADO` | `CADUCIDAD_ALCANZADA` |
| 2 | Destinatario sin matrícula `active` ni `invited` (A-129) | `SUPRIMIDO` | `MATRICULA_NO_ACTIVA` |
| 3 | `supresion_comunicacion` vigente para ese estudiante | `SUPRIMIDO` | `SUPRESION_POR_ESTUDIANTE` |
| 4 | `regla_comunicacion.activa = false` para `(curso, tarea, evento)` | `SUPRIMIDO` | `REGLA_DESACTIVADA` |
| 5 | `curso.modo_escritura = 'SOLO_LECTURA'` | `DIFERIDO` | `MODO_SOLO_LECTURA` |
| 6 | `curso.comunicaciones_salientes = 'SUSPENDIDAS'` **y** canal de Canvas | `DIFERIDO` | `SUSPENSION_DE_CURSO` |
| 7 | `ventana_supresion` vigente que cubre el mensaje | `DIFERIDO` | `VENTANA_TRAS_RESTAURACION` |

**Por qué ese orden y no otro:** primero las cuatro razones **terminales** —el mensaje ya no tiene sentido, el destinatario no es alcanzable, alguien decidió no escribirle, el evento está apagado— y después las **reversibles**. Al revés, **un mensaje caducado quedaría diferido esperando una reanudación que nunca lo hará útil**, y la bitácora diría «en espera» de algo que nadie iba a enviar jamás. La guarda 4 va después de la 3 porque **la supresión es una decisión sobre una persona y la regla una decisión sobre un evento: la más específica gana y es la que hay que mostrar**.

**La guarda se comprueba dentro del trabajo, inmediatamente antes de la llamada**, no sólo al encolar: con `despachar_outbox` cada 30 s, **la ventana real de un envío indeseado es el tiempo de una petición HTTP**. `comunicaciones_programadas` sigue evaluando y encolando siempre, para que los topes por persona de A-130 se respeten y el histórico quede completo. **Un mensaje `DIFERIDO` por las guardas 5, 6 o 7 durante más de 7 días pasa a `CADUCADO`** con `motivo_estado = 'SUSPENSION_PROLONGADA'`, en `purga_retencion`.

**5 · `motivo_estado` es un enum cerrado de veinte valores.** Ningún valor pertenece a dos estados, y es **obligatorio** en los seis estados terminales laterales y en `DIFERIDO`:

| Estado | Motivos |
|---|---|
| `CADUCADO` | `CADUCIDAD_ALCANZADA`, `SUSPENSION_PROLONGADA` |
| `SUPRIMIDO` | `MATRICULA_NO_ACTIVA`, `SUPRESION_POR_ESTUDIANTE`, `REGLA_DESACTIVADA`, `YA_ACEPTADO`, `MAPEO_YA_VIGENTE`, `ENTREGA_EXCLUIDA`, `NO_ES_DESTINATARIO_VALIDO`, `FUERA_DEL_GRUPO`, `TAREA_REGISTRO_AUSENTE` |
| `DIFERIDO` | `MODO_SOLO_LECTURA`, `SUSPENSION_DE_CURSO`, `VENTANA_TRAS_RESTAURACION`, `PUBLICACION_PENDIENTE`, `CUOTA_AGOTADA` |
| `CANCELADO` | `CURSO_ARCHIVADO`, `TAREA_ARCHIVADA`, `ENTREGA_ELIMINADA`, `ACCION_DOCENTE` |

**Un motivo que pudiera aparecer bajo dos estados haría que «¿por qué no le llegó?» tuviera dos respuestas correctas.** `CANCELACION_MANUAL` se escribe `ACCION_DOCENTE`, el mismo término que ya usan `motivo_revocacion` (A-212) y `motivo_cancelacion` (A-215). **Cada código tiene etiqueta en español**, y la pantalla muestra la etiqueta, **nunca el código**.

**6 · Columnas de despacho:** `motivo_estado`, `caduca_en`, `proximo_intento_en`, `intentos`, `ultimo_codigo_http`, `ultimo_error_literal`, `tomado_por`, `tomado_en`, `canal_efectivo` y `reserva`, con índice parcial `(estado, proximo_intento_en)` para la toma de lote.

---

## 10. Convención de nombres de repositorios (R2.3.8)

### A-107 · Plantilla

```
<curso.slug>-<tarea.slug>-<sujeto>

  <curso.slug>  slug del curso, ÚNICO GLOBALMENTE (A-075), <= 24 caracteres
                                                            p. ej.  icc4201-202620
  <tarea.slug>  slug de la tarea, único por curso, <= 24 caracteres
                                                            p. ej.  t1-ordenamiento
  <sujeto>      individual:  e<canvas_user_id>-<apellido-nombre>   legible <= 24
                grupal:      g<canvas_group_id>-<slug-grupo>       legible <= 24
                base:        base
```

**Qué cambió respecto de la revisión 1 y por qué.** Allí el prefijo era `<codigo>-<periodo>`, y `curso` **no tiene unicidad sobre `(codigo, periodo)`** —sólo sobre `(canvas_base_url, canvas_course_id)` y sobre `slug`—. Dos secciones del mismo ramo en el mismo período, creadas como dos cursos distintos, con el mismo `slug-tarea` y un estudiante presente en ambas, generaban **el mismo nombre**, y la unicidad en base es `(curso_id, nombre)`, que no lo detecta. Se sustituye por **`curso.slug`, que A-075 ya declara único globalmente** y que además lleva un `CHECK` de longitud y de forma. El riesgo desaparece por construcción, no por vigilancia. Y `<slug-tarea>` pasa de «≤ 20» a **≤ 24**, unificando el número con el paso 6 de A-108, que decía 24: eran **dos cifras distintas para el mismo componente en secciones contiguas**.

**Ejemplos reales, calculables sin consultar nada** (con `curso.slug = icc4201-202620`):

| Caso | Nombre resultante | Longitud |
|---|---|---|
| Ana Gómez (`canvas_user_id` 5310), tarea 1 individual | `icc4201-202620-t1-ordenamiento-e5310-gomez-ana` | 46 |
| Grupo «Equipo 04» (`canvas_group_id` 8842), tarea 2 grupal | `icc4201-202620-t2-compilador-g8842-equipo-04` | 44 |
| José Muñoz-Peña (`canvas_user_id` 84213), tarea 3 individual | `icc4201-202620-t3-web-e84213-munoz-pena-jose` | 44 |
| Repositorio base de la tarea 1 | `icc4201-202620-t1-ordenamiento-base` | 35 |
| Grupo «Los Punteros» (`canvas_group_id` 9912), tarea 1 | `icc4201-202620-t1-ordenamiento-g9912-los-punteros` | 49 |
| Estudiante con nombre íntegramente en escritura no latina, `canvas_user_id` 5310 | `icc4201-202620-t1-ordenamiento-e5310` | 36 |

### A-108 · Normalización y ensamblado, verificable paso a paso

**La revisión 1 numeraba siete pasos sin decir si se aplicaban por componente o al nombre completo, y ponía el recorte de guiones antes del truncado, de modo que un truncado que cayera sobre un guion dejaba un guion final que ya nadie recortaba.** Aquí queda escrito el algoritmo entero, sin huecos.

**Validación en el alta del curso, que es donde se paga el problema una sola vez:**

- `curso.codigo`: **≤ 12 caracteres tras normalizar**, comprobado en el formulario y por `CHECK` en base.
- `curso.periodo`: **exactamente 6 caracteres**, comprobado igual.
- `curso.slug`: se **propone** como `normalizar(codigo) + "-" + periodo`, es **editable** por el profesor, y se valida con **≤ 24 caracteres**, forma `^[a-z0-9][a-z0-9-]*[a-z0-9]$` y **unicidad global**. Si el propuesto ya existe, el formulario pide otro **antes** de crear el curso; nunca se resuelve con un sufijo automático.
- `tarea.slug`: mismas reglas, **≤ 24**, único por curso.

**`normalizar(texto)` — se aplica POR COMPONENTE, nunca al nombre ya ensamblado:**

1. Descomponer a `NFKD` y **descartar las marcas diacríticas** (`ñ` → `n`, tildes eliminadas).
2. Pasar a minúsculas.
3. Sustituir todo lo que no sea `[a-z0-9]` por `-`.
4. Colapsar guiones consecutivos.
5. Recortar guiones de los extremos.
6. **Truncar a 24 caracteres.**
7. **Volver a recortar guiones de los extremos**, porque el truncado del paso 6 puede haber caído justo sobre un guion. **Este paso faltaba y es el que dejaba nombres terminados en `-`.**

**Ensamblado:**

8. Los **identificadores numéricos nunca se truncan** ni pasan por `normalizar`: `e5310`, `g8842` se escriben tal cual.
9. **Si el componente legible queda vacío** tras normalizar —un nombre íntegramente en escritura no latina, un grupo llamado «★» — **el componente legible se omite entero, incluido su guion separador**, y el sujeto queda como `e<canvas_user_id>` o `g<canvas_group_id>` a secas. **Nunca se produce `…-e5310-`**, que es lo que salía con las reglas de la revisión 1. La inequivocidad no se resiente: la aporta el identificador de Canvas (A-109), no la parte legible.
10. Se unen los componentes con `-` y **se recortan guiones de los extremos del nombre completo** una última vez.

**Techo de longitud y por qué no puede alcanzarse:**

11. `24 + 1 + 24 + 1 + (1 + 10 + 1 + 24) = 86 caracteres` en el peor caso absoluto, tomando 10 dígitos para un `canvas_user_id`. **Por construcción el nombre nunca supera 90 caracteres.**
12. **Aun así se escribe la regla del caso imposible**, porque un catálogo cerrado sin regla de desbordamiento no es cerrado: si el nombre ensamblado superase **90** caracteres, se recorta el **componente legible del sujeto** hasta que quepa, aplicando de nuevo el paso 7; si aun así no cupiera, se omite el componente legible según el paso 9. **Nunca se recorta un identificador numérico y nunca se añade un sufijo** (A-111).
13. **El límite de 100 caracteres del nombre de repositorio de GitHub queda marcado `[MEDIR]`** (RA-26), **no `[DOC]`**. La revisión 1 lo afirmaba como hecho sin marca, sin identificador `Q-…` y sin que apareciera en `preguntas-averiguables-resueltas.md`, lo que violaba la regla 4 de A-162 en el punto que sostiene toda la convención. **El diseño no depende de que ese número sea 100**: depende del techo propio de 90, que es más estricto, y la medición sólo confirmará que hay margen.

La parte legible del sujeto se deriva de `estudiante.nombre_ordenable` (apellido y nombre), no del nombre de pila suelto.

**Pruebas obligatorias del normalizador**, en `backend/app/dominio/`, con estos casos exactos: nombre con tildes y `ñ`; nombre íntegramente en escritura no latina; nombre que trunca justo sobre un guion; grupo con emoji; `codigo` de 12 caracteres con `periodo` de 6 y legible de 24; y dos cursos distintos que no pueden producir el mismo nombre.

### A-109 · Por qué el identificador de Canvas y no el login de GitHub

La inequivocidad que exige **R2.3.8** la aporta **`canvas_user_id` / `canvas_group_id`**, no la parte legible. Las tres alternativas se descartan con motivo:

- **Usar el login de GitHub** (`…-agomez`): el login puede cambiar y, peor, **el antiguo queda libre para que otra persona lo reclame** **[DOC]** (`Q-2.3-66`). Como el nombre del repositorio **no cambia nunca** (A-110), un nombre que incorpore el login puede acabar designando a otra persona. **Un nombre que puede pasar a designar a otro no es inequívoco.** Este es el punto en que este documento se aparta de dos de los tres borradores, y el motivo es exactamente éste.
- **Usar sólo el nombre de la persona**: los homónimos existen y los nombres cambian.
- **Usar el `sis_user_id`**: puede no venir **[DOC]** (`Q-2.2-30`).

`canvas_user_id` y `canvas_group_id` no cambian por renombrados, no dependen de permisos SIS y son estables dentro del curso. La parte legible existe **únicamente** para que un docente reconozca el repositorio de un vistazo en la lista de la organización, y puede truncarse sin que se pierda la unicidad.

### A-110 · El nombre no cambia nunca después de la creación

Aunque el estudiante renombre su cuenta de GitHub, aunque el profesor renombre la tarea, aunque cambie el nombre del grupo en Canvas. Renombrar rompería las URLs ya enviadas por Canvas (**R2.3.12**) y las que los correctores tengan guardadas, a cambio de nada. **La identidad viva está en `github_repo_id`; el nombre es una etiqueta estable.**

Si alguien renombra el repositorio en GitHub, el webhook `repository` con acción `renamed` actualiza `nombre` y `full_name`, los enlaces se reconstruyen y **nada se rompe**, porque nada depende del nombre.

### A-111 · Colisión de nombre: nunca se añade sufijo

**No se sufija `-2`, `-3`.** Un sufijo destruiría la propiedad de inequivocidad que **R2.3.8** exige, y produciría dos nombres válidos para el mismo sujeto. Como el nombre incluye el identificador de Canvas, una colisión sólo puede significar una de dos cosas:

1. **El repositorio ya existe para ese mismo sujeto** —reintento tras un fallo parcial—: se adopta con las tres condiciones de A-097.
2. **Hay una anomalía real**: `ERROR_PERMANENTE` con subtipo `NOMBRE_OCUPADO_POR_TERCERO` e incidencia `REPO_NOMBRE_OCUPADO`, para que un docente lo mire.

Ambos desenlaces son mejores que un nombre ambiguo. La unicidad se refuerza además con el índice único `(curso_id, nombre)` en la base **y con la unicidad global de `curso.slug`** (A-107), que es lo que impide que dos cursos distintos generen el mismo nombre — el índice `(curso_id, nombre)`, por sí solo, no lo detectaría.

### A-172 · El nombre del tag, cerrado: `entrega.slug` y el contador de versión

A-104 nombra el tag `entrega/<orden>-<slug-entrega>/v<n>` y la revisión 1 dejaba las dos incógnitas sin definir: la tabla `entrega` tenía `nombre` pero no `slug`, sin regla de derivación, de longitud ni de colisión, y no se decía si `v<n>` era el mismo contador que `version_entrega.intento`. Queda cerrado:

**`entrega.slug`** es una **columna real** de la tabla `entrega` (A-080), no un valor calculado al vuelo:

1. Se deriva de `entrega.nombre` con `normalizar()` de A-108, con el mismo tope de **24 caracteres** y el mismo recorte final de guiones.
2. **Si queda vacío** —una entrega llamada «★» o en escritura no latina— **se usa `e<orden>`**: `e1`, `e2`. Nunca queda vacío.
3. **Colisión dentro de la misma tarea** (`único (tarea_id, slug)`): se resuelve **una sola vez, al vincular**, anexando `-<orden>`; si aun así colisionara, `e<orden>`. **Nunca se resuelve en el momento de crear el tag**, porque el tag debe poder calcularse desde la fila sin consultar nada.
4. **Se congela con la primera captura.** Renombrar la entrega en Canvas después **no cambia el slug**, por la misma razón por la que el nombre del repositorio no cambia nunca (A-110): reescribir un tag es borrarlo y crearlo, y eso rompe referencias ya enviadas a los correctores. El nombre legible sí se actualiza en la interfaz; el slug no.

**`v<n>` es exactamente `version_entrega.intento`.** No es un contador aparte:

- La primera captura de una `(entrega, sujeto)` es `intento = 1` y produce `…/v1`.
- Una recaptura por cambio de fecha (A-103) es `intento = 2` y produce `…/v2`, **sin tocar el `v1`**, que sigue existiendo y apuntando al SHA anterior. Eso es literalmente **R2.4.7**.
- El contador es **por `(entrega, sujeto)`**, igual que la unicidad `(entrega_id, sujeto_id, intento)` de A-084. Dos sujetos distintos tienen cada uno su `v1`, en repositorios distintos, y no hay ninguna colisión posible.

**Ejemplo completo, calculable sin consultar nada:** tarea con dos entregas, «Avance parcial» (`orden` 1, `slug` `avance-parcial`) y «Entrega final» (`orden` 2, `tipo` `FINAL`, `slug` `entrega-final`). Los tags del repositorio de Ana Gómez son `entrega/1-avance-parcial/v1` y `entrega/2-entrega-final/v1`; si la fecha final se adelanta y se recaptura, aparece `entrega/2-entrega-final/v2` **junto al v1**, no en su lugar.

---

## 11. Trabajos en segundo plano

### A-112 · La cola y el planificador viven en PostgreSQL

**No se usa Redis ni Celery ni ningún broker externo.** La cola es la tabla `trabajo`, consumida con `SELECT … FOR UPDATE SKIP LOCKED`. El planificador es la tabla `trabajo_periodico` con `proxima_ejecucion`, y un **tick del trabajador cada 30 segundos** encola lo vencido, bajo el cerrojo que fija **A-115 garantía 5** —que en la revisión 2 **es por `curso_id` para todo trabajo que hable con Canvas**, y no por `(tipo, curso_id)`, porque aquella granularidad implementaba exactamente lo contrario de la regla de A-039 que decía cumplir—.

Cuatro razones, en orden:

1. **Permite encolar el trabajo y escribir el cambio de dominio que lo justifica en la misma transacción de Postgres.** Eso es lo que da la idempotencia real; con un broker externo, esas dos escrituras no son atómicas.
2. Elimina un servicio, un coste y un modo de fallo en un despliegue que debe seguir en pie hasta el 31 de octubre.
3. Hace la cola **inspeccionable desde la propia interfaz** (`/operacion`), lo que es útil en la demostración y en la defensa del 7 de octubre.
4. Es defendible en una revisión de código sin apelar a la magia de un *broker*.

Contrapartida asumida: la cola no sobrevive a la pérdida de la base. Es aceptable porque la base ya es el punto único de verdad y está respaldada (A-016).

**Vigilante externo del planificador, que no es un *pinger* (léase A-004).** Un *workflow* programado de GitHub Actions llama cada 10 minutos a un endpoint autenticado `POST /interno/latido`. Ese endpoint **no mantiene vivo nada** —los servicios de A-004 están en plan de pago y no se suspenden— y **su efecto primario es una comprobación, no un disparo**:

1. Lee `MAX(ultima_ejecucion)` de `trabajo_periodico` y el retraso máximo de `proxima_ejecucion` vencida.
2. **Si el planificador está al día, responde `200` y no hace nada más.**
3. **Si hay algún trabajo periódico vencido por más de tres cadencias**, abre la incidencia `PLANIFICADOR_DETENIDO`, dispara la alerta por correo de A-015 con cargo a la reserva operativa de A-133, y **sólo entonces** fuerza un ciclo de planificación como medida de recuperación.

Es deliberadamente un vigilante **externo al despliegue que vigila**: un vigilante alojado en el mismo proceso que el planificador se muere con él y no avisa de nada. La puntualidad de los crons de GitHub Actions no está garantizada, y no hace falta que lo esté: el planificador real es el tick de 30 segundos del trabajador, y esto sólo detecta que ha dejado de latir. Si este *workflow* dejara de correr, **no se cae nada**: se pierde la detección temprana, que es exactamente la propiedad que se le pide.

### A-113 · Retención y purga — ANULADA POR RG-047 en su lista de reglas

> **Manda ahora A-199**, y la ventana del cuerpo de `evento_webhook` es la de **A-090: 7 días**, no 30 —la cifra de esta decisión era anterior a la corrección de A-090—. El trabajo de las 03:00 gana cinco reglas nuevas y la caducidad de los mensajes diferidos de A-216. La regla «nunca toca `commit`, `version_entrega`, `bitacora` ni `publicacion_nota`» se conserva entera.

Un trabajo nocturno a las 03:00 aplica exactamente la política de A-090: borra el `payload` de `evento_webhook` a los 30 días **conservando la cabecera**, archiva trabajos terminados de más de 30 días, y poda `sincronizacion` a los 90 días. **Nunca toca `commit`, `version_entrega`, `bitacora` ni `publicacion_nota`**, que son evidencia.

### A-114 · Catálogo cerrado de trabajos — ANULADA POR RG-062, RG-153, RG-194 y RG-024 en su recuento y en su columna «cerrojo»

> **Mandan ahora A-218** —el catálogo pasa de **27 a 31 trabajos**, y cada uno declara además su **fecha de entrada en servicio**— y **A-217** —la columna «cerrojo» pasa a nombrar **uno de los dos espacios por curso**, `1` para Canvas y `2` para GitHub, en vez de `curso_id` a secas o `(tipo, curso_id)`—. Las cadencias, los alcances, las claves de idempotencia y los reintentos de los 27 se conservan uno a uno, y también la corrección de fondo de `precierre_actividad`.

Ningún trabajo **de segundo plano** fuera de esta lista. Añadir uno es una decisión que se registra aquí. **No es el catálogo de todo lo que el sistema hace**: las seis escrituras externas síncronas desde una pantalla están en A-169 y no son trabajos, precisamente porque ocurren en la petición del usuario y le devuelven su resultado. La revisión 1 no lo aclaraba, y de ahí salía la impresión de que la creación del repositorio base no tenía implementación legal en ninguna parte.

La columna **«cerrojo»** dice qué `pg_advisory_lock` toma cada trabajo, según la regla de A-115 garantía 5.

| Trabajo | Cadencia | Alcance | Cerrojo | Clave de idempotencia | Reintentos |
|---|---|---|---|---|---|
| `tick_planificador` | 30 s | global | `global` | ventana | — |
| `sonda_credencial_canvas` | 15 min | por curso | **`curso_id`** | lectura pura | 3 |
| `sync_roster` | 10 min | por curso | **`curso_id`** | upsert por `canvas_enrollment_id` | 4 |
| `sync_grupos` | 10 min | por curso | **`curso_id`** | upsert por `canvas_group_id` y `(grupo, estudiante)` | 4 |
| `sync_tareas_y_fechas` | 5 min; **1 min en las 2 h previas a un cierre** | por curso | **`curso_id`** | comparación de `huella_fechas` (A-056) | 4 |
| `recolector_mapeos` | 3 min con la tarea de registro abierta; 15 min si no; **volcado completo cada hora** | por curso | **`curso_id`** | `(canvas_assignment_id, canvas_user_id, submitted_at)` | 4 |
| **`materializar_sujetos`** | tras cada `sync_*` + barrido cada 5 min | por curso | `curso_id` | `(tarea, conjunto_hash)` | 3 |
| `revalidar_mapeos` | diario 04:00 | por curso | `(tipo, curso_id)` — sólo GitHub | `github_user_id` | 2 |
| `aprovisionar_repositorios` | evento de dominio + barrido cada 2 min | por curso | `(tipo, curso_id)` — sólo GitHub | `repo:<tarea>:<sujeto>` | 8 en ~2 h |
| `reconciliar_accesos` | 15 min | por curso | `(tipo, curso_id)` — sólo GitHub | `(repositorio, estudiante)` | 4 |
| **`sincronizar_acceso_docente`** | al cambiar el equipo del curso + barrido 1 h | por curso | `(tipo, curso_id)` — sólo GitHub | `(repositorio, membresia)` (A-163) | 4 |
| **`revocar_acceso_docente`** | al retirar una membresía | por curso | `(tipo, curso_id)` | `(membresia, repositorio)` | 4 |
| `procesar_webhooks` | continuo | global | por `repositorio_id` | `delivery_id` | 5 |
| `reconciliar_actividad` | 15 min | por repositorio activo | `(tipo, curso_id)` — sólo GitHub | upsert `(repositorio, sha)`; ETag | 4 |
| `barrido_completo_actividad` | diario 03:30 | por repositorio | `(tipo, curso_id)` | cursor `ultimo_head_sha` | 2 |
| `precierre_actividad` | **repartido a lo largo de los 15 min previos** a cada fecha efectiva | **por repositorio** | `(tipo, curso_id)` | `(repositorio, corte_epoch)` | 2 |
| `capturar_versiones` | 1 min | global | `(tipo, curso_id)` | `version:<entrega>:<sujeto>:<corte_epoch>` | 8 en ~2 h |
| `agregar_metricas` | 10 min (últimos 2 días) + nocturno completo | por curso | `(tipo, curso_id)` | recomputa, no incrementa | 2 |
| `comunicaciones_programadas` | 5 min | por tarea | **`curso_id`** — escribe en Canvas | `(tarea, evento, sujeto, entrega, estudiante)` | 3 |
| `despachar_outbox` | 30 s | global | **`curso_id`** — escribe en Canvas | `mensaje_saliente.clave_idempotencia` | 6, luego `REQUIERE_ATENCION` |
| `informe_diario` | **07:00 en la zona horaria del curso** (A-152) | por curso | `curso_id` | `(curso, fecha)` | 3 |
| `verificar_instalacion_github` | 1 h | por curso | `(tipo, curso_id)` | `installation_id` | 2 |
| **`archivar_repositorios`** | acción del profesor (A-168) | por tarea | `(tipo, curso_id)` | `(tarea, repositorio)` | 3 |
| `respaldo_base_datos` | 05:00 diario | global | `global` | fecha (A-170) | 2 |
| `purga_retencion` | 03:00 diario | global | `global` | fecha | 1 |
| `limpieza_verificacion` | diario | por curso | **`curso_id`** — habla con Canvas | prefijo `[verificación app]` (A-042) | 1 |
| `vigilancia` | 5 min | global | `global` | — | — |

**`precierre_actividad` cambia de alcance y de ritmo, y es una corrección de fondo.** La revisión 1 lo agendaba «T−2 min de cada fecha efectiva» con alcance «por `(entrega, sujeto)`»: cuando una entrega cierra a la misma hora para todo el curso —el caso normal— eran **200 reconciliaciones en 120 segundos**, ~100 peticiones/minuto sostenidas, por encima del propio presupuesto de A-117 y con concurrencia máxima 4. Ahora:

- **El alcance es el repositorio**, no `(entrega, sujeto)`: un repositorio se reconcilia **una vez** aunque tres sujetos compartan cierre, y en una tarea grupal el ahorro es directo.
- **La ventana es de 15 minutos, no de 2**, y los repositorios se reparten uniformemente dentro de ella: 200 repositorios en 900 segundos son **1 cada 4,5 segundos**, es decir ~13 peticiones/minuto, dentro del presupuesto de A-117 y sin tocar el techo de concurrencia.
- **La captura sigue disparándose a la hora exacta** (A-101, cada minuto con gracia de 60 s): lo que se adelanta es la puesta al día del espejo, no el corte. Un commit hecho en esos 15 minutos finales **no se pierde**, porque la captura resuelve el SHA contra el espejo *y* contra GitHub (A-102) y la fuente de contraste se lee en el momento del corte.

### A-115 · Cinco garantías que comparte todo trabajo, y ninguna es opcional — ANULADA POR RG-062 en su garantía 5

> **Manda ahora A-217.** Las garantías 1 a 4 se conservan enteras, y también el argumento de A-039 que sostiene la serialización contra Canvas. Lo que queda superado es la tabla de la garantía 5: hay **dos espacios de cerrojo por curso, uno por proveedor**, con orden fijo y **prohibición de retención cruzada**.

1. **Clave de idempotencia única**, garantizada por **índice único parcial en base de datos**, no por una comprobación en memoria. Encolar dos veces el mismo trabajo lógico es un *no-op*.
2. **Transacción con el dominio.** Encolar el trabajo y escribir el cambio de estado que lo justifica ocurren en la misma transacción.
3. **Intención antes de llamada, y lectura antes de todo efecto externo.** Antes de producir un efecto externo se persiste la intención (`repositorio.estado = CREANDO`, `mensaje_saliente.estado = PENDIENTE`) y **se lee para comprobar si el efecto ya está producido**. Sin excepciones:

   | Antes de… | Se lee… |
   |---|---|
   | `POST /orgs/{org}/repos` o `/generate` | `GET /repos/{org}/{nombre}` (A-097) |
   | `PUT .../collaborators/{login}` | `GET .../collaborators/{login}` (`204`/`404` **[DOC]**) y `GET .../invitations` (A-100) |
   | `POST .../git/refs` (tag) | `GET .../git/ref/tags/{nombre}` |
   | Publicar una nota | La submission actual, comparando `score` y `graded_at` |
   | Enviar correo, mensaje, anuncio o comentario | `mensaje_saliente.clave_idempotencia` |

   Motivo: el proceso puede morir entre la llamada externa y el `commit` de la transacción local. Sin verificación previa, el reintento duplicaría repositorios, invitaciones o mensajes. **Con ella, el peor caso es una lectura de más.**
4. **Reintento con retroceso exponencial, *jitter* y tope**, respetando siempre `retry-after`. Un trabajo agotado **no desaparece**: queda `REQUIERE_ATENCION` con su último error visible y reintentable a mano.
5. **Serialización por curso, y la granularidad importa.** La regla, corregida en la revisión 2:

   | Qué toca el trabajo | Cerrojo que toma | Por qué |
   |---|---|---|
   | **Habla con Canvas** (`sonda_credencial_canvas`, `sync_roster`, `sync_grupos`, `sync_tareas_y_fechas`, `recolector_mapeos`, `materializar_sujetos`, `comunicaciones_programadas`, `despachar_outbox`, `informe_diario`, `limpieza_verificacion`) | **`pg_advisory_lock(curso_id)`**, a secas | A-039 fija **una sola petición simultánea por curso** contra Canvas, con respaldo documental: un cliente que no hace más de una petición simultánea es improbable que sea limitado, y las peticiones paralelas sufren penalización de *pre-flight* **[DOC]** (`Q-2.2-41`) |
   | **Habla sólo con GitHub** | `pg_advisory_lock(hash(tipo), curso_id)` | GitHub sí admite concurrencia; el techo lo pone A-117 (concurrencia 4), no el cerrojo |
   | Global | `pg_advisory_lock('global', tipo)` | Un solo ejecutor por instancia |

   **La revisión 1 tomaba `(tipo, curso_id)` para todo**, con lo que `sync_roster`, `sync_grupos`, `sync_tareas_y_fechas`, `recolector_mapeos` y `sonda_credencial_canvas` del mismo curso corrían **a la vez** y golpeaban Canvas en paralelo: la garantía implementaba lo contrario de la regla que decía cumplir. **Ahora un solo trabajo de Canvas por curso está en vuelo en cada instante**, y hay una prueba automatizada que lo comprueba lanzando los cinco a la vez y verificando que se serializan.

   Contra Canvas, la serialización no es una limitación sino la estrategia correcta (A-039). Contra GitHub sería un desperdicio, y por eso no se aplica allí.

### A-116 · Clasificación de errores en tres familias

La familia decide el comportamiento y **decide lo que ve el docente**:

| Familia | Ejemplos | Comportamiento | Qué ve el docente |
|---|---|---|---|
| **TRANSITORIO** | `429`, `5xx`, tiempo de espera agotado, `403` de límite secundario, `404` durante la ventana de creación | Retroceso exponencial con *jitter*, hasta el tope del trabajo | «Reintentando, próximo intento a las HH:MM» |
| **BLOQUEANTE** | `403` por política de la organización, permisos pendientes de aprobación, cupo de invitaciones agotado, credencial de Canvas inválida | Estado `BLOQUEADO` o `ESPERANDO_*`; **no se reintenta en bucle**; se reevalúa cada 30 min o cuando cambia la condición | «Esperando a GitHub por límite de uso. Reintento automático a las HH:MM» / «Falta aprobar permisos» |
| **PERMANENTE** | Cuenta de GitHub inexistente, login que es una organización, `grading_type=not_graded`, período de calificación cerrado, `422` de validación | **Cero reintentos**; estado terminal con motivo y acción sugerida; mensaje literal del proveedor guardado | «Requiere tu acción: …», con el texto literal debajo |

**Un límite de API jamás se pinta como error** (Ley 5). El evaluador de este proyecto puede estar revisando varias aplicaciones el mismo día contra la misma organización o el mismo curso, y las cuotas compartidas entre equipos **no están documentadas** **[MEDIR]** (`Q-transversal-39`): la aplicación tiene que distinguir visualmente «GitHub nos está frenando» de «el equipo programó mal».

### A-117 · Presupuesto y ritmo — ANULADA POR RG-071, RG-072 y RG-073 en su almacén

> **Manda ahora A-219.** Los topes propios, el desglose del coste por repositorio, el freno duro por presupuesto medido y el estrangulamiento se conservan enteros; lo que queda superado es que el margen se calculara en el cliente: **todo límite de tasa observado, de cualquier proveedor, vive en `presupuesto_api`**, con cuatro cubos y una sola tarjeta en `/operacion`.

**Contra GitHub**, con topes propios deliberadamente por debajo de los documentados:

| Parámetro | Valor fijado | Referencia documentada |
|---|---|---|
| Concurrencia máxima | **4** | 100 concurrentes **[DOC]** (`Q-3.2-3.3-4-13`) |
| Operaciones generadoras de contenido | **≤ 30 por minuto** | 80/min y 500/hora, **con la advertencia de que algunos endpoints tienen límites de creación menores y no se publican cuáles** **[DOC]** (`Q-2.2-18`, `Q-3.2-3.3-4-13`) |
| Ritmo de creación de repositorios | **1 cada 6 segundos** | Recalculado en la revisión 2: cada repositorio cuesta **hasta 12 peticiones**, no una (ver el desglose de abajo). Un curso de 200 sujetos se aprovisiona en **unos 20 minutos**, sigue siendo compatible con **R2.3.10** —que exige progresividad, no instantaneidad— y con la promesa que se hace al docente en pantalla, que dice el tiempo estimado |
| Consumo del presupuesto primario | **≤ 50 % del medido por hora** | 5 000/hora mínimo por instalación, escalando +50/hora por repositorio por encima de 20, con techo de 12 500 **[DOC]** (`Q-2.5-08`) |
| Peticiones condicionales | **siempre que haya ETag** | un `304` autenticado no consume límite primario **[DOC]** (`Q-transversal-38`) |

**Desglose del coste real de aprovisionar un repositorio, que la revisión 1 no hacía y por eso sus números no cabían juntos:**

| Paso | Llamadas | Decisión |
|---|---|---|
| Lectura previa por nombre | 1 | A-097, A-115 garantía 3 |
| Creación (`POST /repos` o `/generate`) | 1 | A-066 |
| Sondeo de contenido | **≤ 8** | A-096, con el retroceso corregido |
| Lectura previa de colaborador + invitación, por estudiante | 2 × integrantes | A-100, A-064 |
| Acceso del equipo docente | **1** (vía equipo) | A-163 |
| **Total, tarea individual** | **≤ 13** | |

A 1 repositorio cada 6 segundos son **≤ 130 peticiones/minuto de pico y ~7 800/hora**, que con el techo documentado de 12 500/hora **[DOC]** (`Q-2.5-08`) queda por encima del 50 % autoimpuesto sólo en el pico de aprovisionamiento masivo. Por eso se añade la regla siguiente, que la revisión 1 no tenía:

**Freno duro por presupuesto medido, no por aritmética de papel:** el aprovisionador **lee `x-ratelimit-remaining` y `x-ratelimit-limit` en cada respuesta** y ajusta su ritmo para no bajar del **50 % del límite real medido en esa hora**. Si el margen se estrecha, **espacia**; no se detiene ni falla. Un curso de 200 sujetos puede tardar 20 minutos o 40; **R2.3.10** exige que la creación sea progresiva y automática, no que sea rápida, y la pantalla muestra el avance con su estimación.

**Estrangulamiento automático:** si `x-ratelimit-remaining` baja del **20 %**, `reconciliar_actividad` reduce su lote a la mitad; por debajo del **10 %**, sólo procesa repositorios con una entrega abierta en las próximas 24 h.

**Ante `403` o `429`:** se respeta `retry-after` si viene; si no viene y `x-ratelimit-remaining` es 0, se espera hasta `x-ratelimit-reset`; en cualquier otro caso se espera **al menos un minuto**, y luego retroceso exponencial hasta 6 intentos. Es literalmente lo que prescribe la documentación, y la razón está también documentada: **seguir pidiendo mientras se está limitado puede acabar en el baneo de la integración** **[DOC]** (`Q-transversal-39`). **Un baneo el 6 de octubre sería catastrófico.**

**Contra Canvas:** una petición simultánea por curso (A-039), y registro de `X-Request-Cost` en cada respuesta.

**Instrumentación obligatoria:** el presupuesto real **no es calculable a priori**, porque GitHub no publica el coste en puntos de todos los endpoints ni permite consultar el estado del límite secundario **[DOC]** (`Q-2.5-08`). Por eso el ritmo se fija bajo, se mide en la prueba de carga (§19, RA-12) y **se ajusta con datos, no con aritmética de papel**.

### A-217 · Dos espacios de cerrojo por curso, uno por proveedor, y ninguno se retiene de más

**Sustituye la tabla de A-115 garantía 5.** La serialización por curso se hace con **dos espacios de cerrojo distintos**:

| Espacio | Qué protege | Trabajos |
|---|---|---|
| **`pg_advisory_lock(1, curso_id)`** | **Todo el tráfico con Canvas** del curso | `sync_roster`, `sync_grupos`, `sync_tareas_y_fechas`, `recolector_mapeos`, `sonda_credencial_canvas`, `reconciliar_notas_canvas`, `comunicaciones_programadas`, `limpieza_verificacion`, `informe_diario`, `despachar_outbox` en su parte Canvas y **el carril de Canvas del checklist** |
| **`pg_advisory_lock(2, curso_id)`** | **Todo el tráfico con GitHub** del curso | `aprovisionar_repositorios`, `reconciliar_actividad`, `barrido_completo_actividad`, `precierre_actividad`, `reconciliar_accesos`, `sincronizar_acceso_docente`, `revocar_acceso_docente`, `revocar_acceso_estudiante`, `resolver_sha`, `crear_etiqueta`, `verificar_instalacion_github`, `revalidar_mapeos`, `archivar_repositorios` y **el carril de GitHub del checklist** |

**Tres reglas, y las tres son verificables:**

1. **Ningún trabajo retiene un cerrojo mientras espera al otro carril.** `ejecutar_checklist_vinculacion` toma el cerrojo 1 **sólo alrededor de sus llamadas a Canvas** y el 2 **sólo alrededor de las suyas a GitHub**, y **los libera entre ítems**.
2. **Un trabajo que necesite los dos los toma siempre en orden 1 y luego 2**, nunca al revés.
3. **`infra/cerrojos.py` expone `cerrojo_canvas(curso_id)` y `cerrojo_github(curso_id)` como únicos puntos de toma**, y una **prueba de arquitectura falla la construcción** si aparece una toma en orden inverso o una toma anidada de dos cerrojos del mismo espacio.

> **Por qué dos y no uno.** Con un solo cerrojo por curso, los 180 s del checklist **pararían el aprovisionamiento de 600 repositorios y la reconciliación de actividad delante del evaluador**. Los dos proveedores tienen presupuestos y concurrencias distintas: contra Canvas la serialización **es la estrategia correcta** (A-039), contra GitHub sería un desperdicio y el techo lo pone A-219.

`/operacion` muestra, **por curso**, qué cerrojo está tomado y por qué trabajo (A-232).

### A-218 · A-114 pasa de 27 a 31 trabajos, cada uno con su cerrojo y su fecha de entrada en servicio

**El catálogo cerrado de A-114 queda en 31 trabajos: los 27 de la carta más cuatro, y ninguno más.**

| Trabajo | Qué hace | Cerrojo | Entra en servicio |
|---|---|---|---|
| **`ejecutar_checklist_vinculacion`** | Ejecuta los 21 códigos de A-192 y persiste su resultado | **1 y 2**, tomados por tramos y **nunca a la vez** | 16 de septiembre |
| **`reconciliar_notas_canvas`** | Lee las submissions y escribe `estado_canvas_submission` (A-206) | 1 (Canvas) | Bloque 3, **3 de octubre** |
| **`revocar_acceso_estudiante`** | **Único ejecutor** del `DELETE` de colaborador (A-212); por repositorio, clave `revocacion:<acceso_repositorio_id>`, 4 reintentos | 2 (GitHub) | 16 de septiembre |
| **`resolver_sha`** y **`crear_etiqueta`** | La partición de `capturar_versiones` en sus dos fases (A-213), con claves `version:<entrega>:<sujeto>:<corte_epoch>` y `tag:<entrega>:<sujeto>:<intento>` | 2 (GitHub) | Bloque 1, **23 de septiembre** |

**La partición de `capturar_versiones` suma uno al catálogo, no dos**: donde las banderas de A-233 y el calendario dicen `capturar_versiones` **se leen los dos trabajos**, con la misma bandera, la misma fecha y las dos claves de idempotencia.

**No se añaden** `verificar_publicacion_notas`, `verificar_etiquetas_entrega` ni ningún trabajo de archivado adicional: la verificación de etiquetas vive en el barrido nocturno, y el archivado es `archivar_repositorios`.

**Fecha de entrada en servicio, porque un trabajo que no está no debe contarse como parado.** Un trabajo entra en servicio **el día en que su bloque de A-160 lo entrega**, y no antes: `sonda_credencial_canvas`, los `sync_*`, `materializar_sujetos`, `aprovisionar_repositorios`, `reconciliar_accesos`, `sincronizar_acceso_docente`, `revocar_acceso_docente`, `revocar_acceso_estudiante`, `ejecutar_checklist_vinculacion`, `procesar_webhooks`, `despachar_outbox`, `verificar_instalacion_github`, `respaldo_base_datos`, `purga_retencion`, `limpieza_verificacion` y `vigilancia` corren **desde el 16 de septiembre**; `resolver_sha`, `crear_etiqueta` y `precierre_actividad` entran con el **Bloque 1**; `reconciliar_actividad`, `barrido_completo_actividad` y `agregar_metricas` con el **Bloque 2**; `comunicaciones_programadas` en su forma completa, `informe_diario` y `reconciliar_notas_canvas` con el **Bloque 3**.

> **Un trabajo cuya bandera no está retirada no se encola y NO aparece como «vencido»**, para que la alerta «trabajo periódico sin ejecutarse tres ciclos» de A-177 **no se dispare por diseño**.

**Por qué el catálogo tiene que ser uno solo:** gobierna el planificador, las banderas de A-233 y esa alerta. Con recuentos distintos, **un trabajo que no está en el catálogo del planificador no se encola nunca y nadie lo echa de menos**, y otro que no declara su cerrojo puede tomar el 2 antes que el 1 y romper la prueba de A-217.

El enum de `trabajo.tipo` suma los cuatro valores **en la migración inicial** (A-175), el planificador declara para cada uno cadencia, cerrojo, clave, reintentos y bandera, y **`/operacion` lista los 31 con su última ejecución**.

### A-219 · Un único almacén de presupuesto medido: `presupuesto_api` con cuatro cubos

**Todo límite de tasa observado, de cualquier proveedor, vive en la tabla `presupuesto_api`**, con unicidad `(ambito, ambito_id, cubo)`. Los cubos son **exactamente cuatro**:

| Cubo | Ámbito | Fuente de capacidad y recarga | Consumidores |
|---|---|---|---|
| `PRIMARIO` | `GITHUB_INSTALACION` | `x-ratelimit-limit` / `-remaining` / `-reset` de cada respuesta REST | todas las llamadas REST de `ClienteGitHub` |
| `CONTENIDO` | `GITHUB_INSTALACION` | Tope autoimpuesto de A-117: **30 fichas, recarga 30/min** | operaciones generadoras de contenido |
| `GRAFO` | `GITHUB_INSTALACION` | Cabeceras de la propia respuesta GraphQL | enriquecimiento de A-118 |
| **`CANVAS`** | **`CANVAS_CURSO`** | `X-Request-Cost` y `X-Rate-Limit-Remaining` de cada respuesta de Canvas | todas las llamadas de `ClienteCanvas` |

**El objetivo autoimpuesto es el mismo para los cuatro: no bajar del 50 % del límite real medido en la hora**, y por debajo del **20 %** sólo circulan las clases de máxima prioridad. **El máximo observado por curso se lee de `presupuesto_api`, no de un cálculo propio del cliente**, y `limite_observado` **deja de ser un derivado aparte**. `ClienteCanvas` toma y devuelve fichas del cubo `CANVAS` **en el mismo punto de salida en que clasifica errores** (A-193).

> **Por qué un solo almacén.** Con dos, **hay dos frenos que ajustar y dos pantallas que pueden contradecirse**, y el freno es exactamente lo que evita el fallo del día de mayor tráfico.

**Un `403` de Canvas sólo es límite de tasa si la respuesta lo demuestra**; en cualquier otro caso se clasifica por A-193 y **nunca se culpa a una developer key inexistente**.

`/operacion` pinta **los cuatro cubos con la misma tarjeta, el mismo margen y su antigüedad**, como **secciones de curso** —toda instalación de GitHub pertenece a un curso (A-027, A-028)— y por tanto **acotadas** (A-232).

---

## 12. Seguimiento y monitoreo (R2.5)

### A-118 · Atribución de un commit a un estudiante — ANULADA POR RG-029 en su almacén

> **Manda ahora A-205.** La cascada de cuatro reglas, su orden, sus confianzas y la justificación documental se conservan **exactamente**; lo que queda superado es que el resultado viviera sólo en `commit.estudiante_id`: hay una **tabla única de autoría, `autoria_commit`**, con una fila por acreditado, `papel ∈ {AUTOR, COAUTOR}` y la misma enumeración de reglas —cuya cuarta se llama **`IDENTIDAD_DOCENTE`**—, y **todos los agregados de participación se calculan desde ella**.

Es el punto silencioso donde una regla mal elegida produce **acusaciones falsas de no participar**. La cascada es exactamente ésta, en este orden:

| # | Regla | Condición | Confianza | Marca |
|---|---|---|---|---|
| 1 | `AUTOR_GITHUB` | El commit trae `author.id` y ese `github_user_id` está en un mapeo vigente del curso | **Alta** | Atribuido |
| 2 | `EMAIL_NOREPLY` | `author.email` es `ID+login@users.noreply.github.com` y el `ID` coincide con un mapeo vigente | **Alta** | Atribuido |
| 3 | `EMAIL_DIRECTO` | El correo del autor coincide, normalizado, con el correo conocido del estudiante en Canvas | **Media** | Atribuido, **marcado como débil en la interfaz** |
| 4 | `SIN_ATRIBUIR` | Ninguna de las anteriores | — | **`estudiante_id` nulo, y visible en la interfaz como «commits sin atribuir»** |

**Justificación documental:** la API admite explícitamente que el usuario de GitHub asociado a un commit no venga, y define ese caso como que el correo del commit no corresponde a ninguna cuenta de GitHub **[DOC]** (`Q-2.5-23`). **Nunca se adivina por nombre.**

**Por qué el paso 4 existe y es visible:** un estudiante que trabaja con el correo mal configurado **no** debe aparecer como «sin participación» sin más, sino como «hay commits sin atribuir en su repositorio». **La distinción es la diferencia entre una herramienta útil y una injusta.** Los autores no resueltos se agrupan en `identidad_git` para que el docente pueda asociarlos de una vez.

La regla 3 depende de que el token del profesor pueda ver el correo del estudiante, lo que **no está fijado** **[MEDIR]** (`Q-2.2-32`). Si la medición sale negativa, **la regla 3 desaparece y no pasa nada más**: la clave sigue siendo `canvas_user_id` y las reglas 1 y 2 cubren el caso normal.

**Los *merge commits*** (más de un padre) se registran, se muestran en el timeline por ser parte de la historia, y **se excluyen del recuento de participación**, con la exclusión declarada en la interfaz. **La misma exclusión rige en `metrica_repositorio_dia`, y eso lo fija A-171**, porque la revisión 1 lo decía sólo para la participación y dejaba que el tablero y el timeline mostraran números distintos para el mismo repositorio según quién escribiera cada consulta. **Las líneas de código no se usan nunca como medida de aporte**, y la razón se documenta en pantalla: son trivialmente inflables con archivos generados.

**Co-autores (`Co-authored-by`) y ediciones desde la web** sólo son resolubles por GraphQL, que documenta `Commit.authors` y `committedViaWeb`; la REST API no ofrece equivalente **[DOC]** (`Q-2.5-23`). El enriquecimiento usa **GraphQL en lotes de 100 commits** para obtener `authors`, `committedViaWeb` y `parents.totalCount`. Si esa vía resultara inviable, la aplicación degrada a las reglas 1-4 sobre REST y lo declara; el modelo no lo impide.

### A-119 · Ninguna pantalla de seguimiento llama a GitHub — ANULADA POR RG-023 en su punto 1

> **Manda ahora A-220.** La Ley 1, el presupuesto de 400 ms y los cinco bloques del tablero se conservan enteros; lo que queda superado es el «estado de captura» libre de la línea de entregas: es una **enumeración derivada de nueve valores con precedencia**, con **contadores obligatorios**, y esa enumeración es **fuente única** para el tablero, el informe diario y la pantalla de la entrega.

**R2.5** lo exige literalmente. No es una optimización: es el requisito. Todas las vistas leen `commit`, `metrica_repositorio_dia`, `participacion_entrega`, `repositorio` y `acceso_repositorio`, que se alimentan por webhook y por reconciliación.

**Presupuesto de rendimiento fijado:** la vista de tarea responde **en menos de 400 ms en el percentil 95 con 200 sujetos**.

El tablero muestra además, de forma visible, **cuándo se actualizó por última vez**, y ofrece un botón «actualizar ahora» que **encola** una reconciliación. Es honesto sobre la latencia en lugar de fingir tiempo real, y esa honestidad se defiende mejor que un número sin fecha.

**Contenido fijo del tablero de tarea**, de arriba abajo, y en este orden:

1. **Línea de entregas** (**R2.5.6**): una fila por entrega, con su tipo (parcial o final), su fecha de cierre **con zona escrita**, cuántas fechas distintas hay por sección o por excepción, la cuenta atrás si aún no ha vencido, y el **estado de captura** de la entrega — «programada», «N de M versiones registradas», «sin commits: N». Es la respuesta literal a «mostrar claramente las distintas entregas asociadas a una tarea, sus fechas y su estado».
2. **Barra de estado de los repositorios** (**R2.5.5**): recuento por estado con enlace a la tabla completa de **R2.3.11**. **`OPERATIVO` y `DEGRADADO` se cuentan por separado y `DEGRADADO` nunca se suma a la columna de problemas** (A-092): va en su propia columna ámbar, «funcionando, incompleto», con el motivo desglosado. Junto a ella, el recuento de **sujetos activos y desactivados con su motivo** (A-164), para que se vea de un vistazo si falta gente por materializar o si sobra gente que salió de alcance.
3. **Tarjetas de atención**: «sin actividad reciente» (**R2.5.3**) y «sin participación» con sus tres causas (**R2.5.4**).
4. **Serie temporal de commits por día** (**R2.5.2**), agregada y desglosable por repositorio, con el selector de período de **R2.5.7**.
5. **Métricas adicionales** de **R2.5.9** (A-123) y comparación intragrupo de **R2.5.8**.

### A-120 · «Sin participación» distingue tres causas

**R2.5.4** se implementa con tres categorías separadas, porque **la acción del docente es distinta en cada una** y mezclarlas en un solo número sería inutilizarlas:

1. **No ha aceptado la invitación** — problema de **acceso**. Acción: reenviar o avisar por Canvas.
2. **Ha aceptado pero no tiene commits** — problema de **trabajo**. Acción: contactar al estudiante.
3. **Hay commits sin atribuir en su repositorio** — problema de **configuración de su Git**. Acción: pedirle que configure su correo, o asociar la identidad desde la aplicación.

### A-121 · Umbrales de actividad, con valores por defecto y configurables — ANULADA POR RG-155 en su aplicación

> **Manda ahora A-222.** Los cuatro umbrales y su configurabilidad se conservan; lo que queda superado es aplicarlos sin mirar la ventana observada: **un indicador no se pronuncia sobre una ventana más corta que su propio umbral**, y lo dice en pantalla en lugar de callarlo.

| Métrica | Valor por defecto | Configurable |
|---|---|---|
| «Repositorio sin actividad reciente» (**R2.5.3**) | ningún commit en **7 días** | por curso, `curso.umbral_dias_sin_actividad`, entre 1 y 30 |
| Umbral en ventana crítica | **2 días**, cuando hay una entrega cuya fecha efectiva vence en menos de 72 h | derivado, no configurable |
| «Estudiante sin participación» (**R2.5.4**) | **cero commits atribuidos** en la ventana de la entrega | no configurable |
| «Invitación sin aceptar» que aparece en Pendientes | más de **48 horas** desde la invitación | no configurable |

Todos los cálculos se hacen sobre `metrica_repositorio_dia` y `participacion_entrega`, **nunca en vivo** (A-119), y **con la definición única de día y de commit contable de A-171**: el umbral de 7 días cuenta días del curso, no días UTC, y «ningún commit» significa ningún commit **contable**.

**Toda métrica muestra su definición al pasar el cursor, y ninguna se presenta como medida de calidad del código: son medidas de actividad, y la interfaz lo dice.**

### A-171 · La zona horaria del día y qué commit cuenta — ANULADA POR RG-030 en su cobertura de bots y docentes

> **Manda ahora A-205.** Las dos frases, la fórmula del bucket, el recálculo al cambiar la zona y **las tres exclusiones del commit contable** se conservan **exactamente, y la firma de un solo argumento también**. Lo que se añade es que **los commits de bots y del equipo docente SÍ son contables**, se cuentan aparte en dos contadores informativos, y las alertas de **R2.5.3** y **R2.5.4** se evalúan sobre la **segunda función** `hay_actividad_estudiantil`.

Dos frases que evitan que el tablero, el timeline y el informe se contradigan. La revisión 1 no las tenía y cada implementador habría trazado la frontera donde le conviniera.

**1 · `metrica_repositorio_dia.dia` es la fecha en la ZONA HORARIA DEL CURSO.** No es UTC.

- El bucket se calcula como `(commit.fecha_committer AT TIME ZONE 'UTC' AT TIME ZONE curso.zona_horaria)::date`.
- **La columna lleva ese comentario en la migración**, literalmente, para que nadie tenga que deducirlo leyendo este documento.
- **No contradice A-073.** A-073 dice que **todo instante** se almacena en UTC y que **ningún cálculo de negocio** —vencer una fecha de cierre, disparar un recordatorio, decidir una ventana de actividad— usa hora local; eso sigue siendo cierto sin excepción. Un **bucket diario no es un instante**: es una agregación cuyo único consumidor es la presentación, y agregarla en UTC produciría un resultado directamente falso para el docente. Con Chile en UTC−3/−4, el histograma de A-123 métrica 1 —«quién trabajó la última noche»— es exactamente la pregunta que se responde mal si el día empieza a las 21:00 hora local.
- **Si la zona horaria del curso cambia**, el trabajo `agregar_metricas` **recalcula todos los buckets del curso** en el ciclo siguiente y lo registra en `bitacora`. Las métricas son recomputables por diseño (A-114: «recomputa, no incrementa»), así que el recálculo es barato y correcto.
- **Lo que sí sigue en UTC:** los umbrales que son intervalos y no días de calendario. «Sin actividad en 7 días» se evalúa como `ahora_utc - MAX(fecha_committer) > interval '7 days'`, y «últimas 48 h» igual. **Un intervalo no tiene zona; un día sí.** La interfaz etiqueta ambos con la fecha local equivalente (A-152).

**2 · Un «commit contable» es el mismo en todas partes.** `metrica_repositorio_dia.commits` y `participacion_entrega.commits` aplican **exactamente** las mismas exclusiones:

| Se excluye | Por qué | Dónde estaba dicho |
|---|---|---|
| *Merge commits* (`es_merge = true`, más de un padre) | No son aporte de trabajo | A-118, que sólo lo decía para participación |
| El commit inicial de la plantilla (`sha = repositorio.commit_inicial_sha`) | Es andamiaje, no trabajo del estudiante | A-096 |
| Commits huérfanos (`huerfano = true`) | Desaparecieron de la historia tras un `push --force`; se conservan como registro, no cuentan como aporte | A-072 |

Los excluidos **no se pierden**: se cuentan aparte en `commits_merge` y `commits_excluidos`, **el timeline de A-124 los muestra todos** —es la historia real del repositorio y ocultarla sería falsearla— y la interfaz distingue con una etiqueta cuáles cuentan y cuáles no. **Ninguna consulta del sistema define «commit» por su cuenta**: hay una única función en `backend/app/dominio/` que produce el predicado, y todo lo demás la usa.

### A-122 · Ventanas de actividad por entrega (R2.5.7)

La ventana de una entrega para efectos de actividad es **`(cierre de la entrega anterior, cierre de esta entrega]`**, y para la primera entrega **`(creación del repositorio, cierre]`**. Se calcula **por sujeto**, con su fecha efectiva propia, **no con la fecha base**. El selector de la interfaz ofrece: «hasta la entrega 1», «entre la 1 y la 2», «todo».

**Qué es exactamente «la entrega anterior» lo fija A-173**, y no se deja al implementador: la revisión 1 no definía el caso en que la anterior quedó «sin fecha de cierre» para ese sujeto —caso que A-055 admite explícitamente—, ni el caso de `orden` no contiguo, ni el del sujeto que entró en alcance más tarde. **R2.5.7** se calculaba distinto en cada implementación.

### A-173 · «La entrega anterior», definida por sujeto

> **La entrega anterior de la entrega `E` para el sujeto `S`** es la entrega de la misma tarea con el **mayor `orden` estrictamente menor que `E.orden`** que además tenga **`fecha_efectiva` vigente y no nula para `S`**. Si no existe ninguna, no hay entrega anterior.

De ahí sale el **inicio de la ventana**, en este orden y sin excepciones:

| Caso | Inicio de la ventana |
|---|---|
| Existe entrega anterior para `S` | El `due_at_utc` de **su** fecha efectiva, exclusivo |
| No existe entrega anterior para `S` | `repositorio.creado_en` de ese sujeto |
| El sujeto entró en alcance **después** de la entrega anterior (A-164) y su repositorio se creó más tarde | **El más tardío de los dos**: `max(due_at_anterior, repositorio.creado_en)`. No se le atribuye actividad de un período en que no tenía repositorio |
| `E` no tiene fecha efectiva para `S` (no visible, o sin fecha) | **No hay ventana**: el selector muestra «esta entrega no aplica a este sujeto» y no se calcula participación |

**Las tres consecuencias que esto resuelve, dichas en voz alta:**

1. **`orden` no contiguo** no puede ocurrir por A-080 —el `orden` es contiguo desde 1—, pero la definición usa «mayor `orden` menor que», no «`orden − 1`», de modo que **sigue siendo correcta aunque alguna vez no lo fuera**.
2. **Una entrega anterior sin fecha para ese sujeto se salta**, y se busca la anterior a ésa. Es lo correcto: si a un estudiante no se le exigió esa entrega, su trabajo no se parte por una fecha que no le aplicaba.
3. **La ventana es por sujeto y las de dos estudiantes de la misma entrega pueden ser distintas**, porque sus fechas efectivas lo son (**R2.4.3**). El selector lo dice: «período de la entrega 2 **para este sujeto**».

### A-123 · Métricas adicionales de R2.5.9

Elegidas por utilidad docente, no por vistosidad. Son cinco:

1. **Distribución del trabajo en el tiempo** — histograma de commits por día previo al cierre, que hace visible de un vistazo quién trabajó la última noche.
2. **Reparto dentro del grupo** — índice de desequilibrio (porcentaje del integrante que más aporta sobre el total del grupo), con umbral configurable. Alimenta la tarjeta de **R2.5.8**.
3. **Racha de días sin actividad** por repositorio, ordenable. Alimenta **R2.5.3**.
4. **Progreso frente al cierre** — repositorios con actividad en las últimas 48 h antes del cierre frente a los que no, con cuenta atrás.
5. **Días activos distintos** por integrante — número de días con al menos un commit, que distingue a quien trabajó sostenidamente de quien concentró todo en una sesión.

**R2.5.8** se presenta como barras por integrante con commits, adiciones, eliminaciones y días activos, siempre con la nota de que los *merge commits* están excluidos y de que las líneas no miden calidad.

### A-124 · Timeline por repositorio (R2.5.10)

Un eje temporal único con **tres capas superpuestas**:

1. **Los commits agrupados por día**, con su autor atribuido y su regla de atribución visible.
2. **Los eventos de repositorio relevantes**: creación, contenido listo, invitación emitida, invitación aceptada, cambio de rama por defecto, renombrado.
3. **Las marcas de cada entrega**, con su fecha de cierre y **el commit exactamente capturado, resaltado**.

Al pulsar un día se despliegan sus commits con mensaje, líneas añadidas y eliminadas, y **enlace a GitHub**. Es la pantalla que responde literalmente a «identificando cuándo se produjeron los principales cambios, qué integrantes participaron en ellos y las distintas entregas asociadas a la tarea».

**Dos precisiones que la revisión 1 no hacía y que cambian lo que se ve:**

- **El timeline se pinta enteramente desde el espejo** y no llama a GitHub (Ley 1), pero **su enlace a GitHub sí necesita que el docente tenga acceso**, y por eso hereda A-163 igual que A-136. Mientras `acceso_docente_repositorio` no esté `CONCEDIDO`, el enlace **no se pinta**: en su lugar aparece el motivo y el botón de reintento. Un enlace que devuelve `404` no cumple «revisar fácilmente la evolución del trabajo».
- **El eje de días usa la zona horaria del curso** (A-171), la misma que el histograma de A-123 y que la sección 3 del informe. Los tres muestran el mismo número para el mismo repositorio, que era exactamente lo que estaba en riesgo.
- **La capa 1 muestra todos los commits, incluidos merges, commit inicial y huérfanos**, cada uno con su etiqueta de por qué no cuenta (A-171). El timeline es la historia; el recuento es la métrica. **Son cosas distintas y la pantalla lo dice.**

### A-220 · El estado de una entrega para R2.5.6 es una enumeración derivada de nueve valores con precedencia

**Es una enumeración cerrada, derivada y no persistida, evaluada de arriba abajo; el primero que se cumple es el estado:**

| # | Estado | Etiqueta (A-155) | Condición |
|---|---|---|---|
| 1 | `EXCLUIDA` | «Excluida por el equipo docente» | `estado_validacion = 'EXCLUIDA'` |
| 2 | `ELIMINADA_EN_CANVAS` | «Eliminada en Canvas» | `estado_validacion = 'ELIMINADA_EN_CANVAS'` |
| 3 | `NO_PUBLICADA` | «No publicada en Canvas» | `entrega.publicada = false` |
| 4 | `VINCULADA_TRAS_EL_CIERRE` | «Versiones no registradas: la fecha ya había pasado al vincular» | `estado_validacion = 'VINCULADA_TRAS_EL_CIERRE'` |
| 5 | `SIN_FECHA` | «Sin fecha de cierre» | Ninguna `fecha_efectiva` vigente con `due_at_utc` no nulo |
| 6 | `ABIERTA` | «Abierta · cierra en X» | Ninguna fecha efectiva ha vencido |
| 7 | `EN_CIERRE` | «Cerrando · N de M sujetos ya cerrados» | Alguna venció y alguna sigue pendiente |
| 8 | `CERRADA_CAPTURANDO` | «Cerrada · registrando versiones (M de N)» | Todas vencieron y **algún** sujeto con fecha efectiva no tiene aún versión vigente en estado terminal |
| 9 | `CERRADA_REGISTRADA` | «Cerrada · N versiones registradas» | **Todo** sujeto con fecha efectiva tiene versión vigente en uno de los **seis** estados terminales de A-213 |

**Por qué esa precedencia:** una decisión humana deliberada (1) manda sobre un hecho de Canvas (2), y **un assignment que ya no existe (2) manda sobre uno despublicado (3)**, porque un assignment eliminado **no puede estar publicado**.

**El estado agregado nunca aparece solo.** Junto a él se muestran siempre los contadores por sujeto: «N sujetos · M versiones registradas · K sin commits · J en revisión · P sin repositorio al cierre · Q con error · R sin fecha», más «N fechas distintas» cuando las hay.

**No se persiste.** Se calcula en **`backend/app/dominio/estado_entrega.py` con una función única**, se precomputa en `resumen_tarea` para el listado —con `calculado_en` visible— y es la **fuente única** de la línea de entregas de A-119 punto 1, del informe diario y de la pantalla de la entrega.

Se conservan íntegras, porque son presentación de fechas y no estado: el rango `[primera, ultima]`, la lista nominal de excepciones con su `origen` y su `canvas_override_id`, la insignia de fecha ambigua y el porcentaje con denominador escrito. **Pruebas obligatorias** con los nueve casos y con el caso mixto de dos secciones con fechas distintas. Color por familia: gris para `EXCLUIDA`, `ELIMINADA_EN_CANVAS` y `NO_PUBLICADA`; gris con aviso para `VINCULADA_TRAS_EL_CIERRE` y `SIN_FECHA`; azul para `ABIERTA`; ámbar para `EN_CIERRE` y `CERRADA_CAPTURANDO`; verde para `CERRADA_REGISTRADA`.

Sirve a **R2.4.2**, **R2.4.3**, **R2.4.5**, **R2.5.6**, **R2.6.1**, **R2.6.2**.

### A-221 · La ingesta de actividad, en tres piezas, con relleno hacia atrás obligatorio

**Se reparte en tres piezas con fecha propia, y ninguna se adelanta ni se aplaza.**

**1 · De la entrega parcial (16 de septiembre), operativo:** el endpoint receptor `POST /webhooks/github`, que **verifica `X-Hub-Signature-256` sobre el cuerpo crudo antes de parsear**, persiste en `evento_webhook` con unicidad `delivery_id` y responde `202` en menos de 200 ms **sin procesar en línea** (A-070); la suscripción congelada a los **siete** eventos de A-070; el trabajo `procesar_webhooks` **limitado a los manejadores de `member`, `repository`, `installation` e `installation_repositories`**; y la **persistencia sin procesamiento** de `push`, `create` y `delete`, que se guardan con **`estado = PENDIENTE_BLOQUE_2`**.

> **El manejador de `member`/`added` no es opcional:** es la **única señal documentada** de que un estudiante aceptó su invitación, y sin él **el predicado `OPERATIVO` de A-092 nunca se alcanza** y **R2.3.11** mostraría un estado falso el 16 de septiembre.

El despachador recibe una **lista blanca de pares `(evento, acción)` activos por perfil**; un par fuera de la lista **se persiste, se marca y no produce error**.

**2 · Del Bloque 2 (24 → 30 de septiembre):** los manejadores de `push`, `create` y `delete`; la ingesta `push` → `evento_push` → `commit`; `reconciliar_actividad` cada 15 minutos con `If-None-Match`; `barrido_completo_actividad` nocturno; `precierre_actividad`; `agregar_metricas`; los bloques 3, 4 y 5 del tablero, el timeline de **R2.5.10** y el ámbito `GITHUB_ACTIVIDAD` del indicador de sincronización.

**3 · Relleno hacia atrás, obligatorio y no opcional.** `evento_webhook.payload` se retiene **7 días** (A-090), de modo que **los cuerpos crudos de la ventana 16 → 23 de septiembre no existen cuando el Bloque 2 entra en servicio**. Al activarse el Bloque 2, `barrido_completo_actividad` ejecuta, **para cada repositorio y una sola vez**, un relleno histórico con `GET /repos/{o}/{r}/commits?sha=<rama_por_defecto>&since=<repositorio.listo_en>` paginado por `Link`, con clave de idempotencia `(repositorio_id, 'backfill')`, y escribe **`cursor_sincronizacion.ultimo_backfill_en`**.

> **El relleno no depende de los cuerpos retenidos** y deja `commit` completo **desde `repositorio.listo_en`**, de modo que **R2.5.2** y **R2.5.3** cubren también los días previos al Bloque 2. **El instante desde el que la ingesta es fiable se escribe en `curso.ingesta_actividad_desde`**, y de ahí lo lee A-222.

**Criterio de retirada de la bandera correspondiente (A-233):** relleno ejecutado y `ultimo_backfill_en` escrito **en todos los repositorios**.

Sirve a **R2.3.9**, **R2.3.11**, **R2.5.2**, **R2.5.3**, **R2.5.5**, **R2.5.7**, **R2.5.8**, **R2.5.10**.

### A-222 · Un indicador no se pronuncia sobre una ventana más corta que su umbral

**El indicador «repositorio sin actividad reciente» (R2.5.3, A-121) no se pronuncia sobre una ventana más corta que su propio umbral, y lo dice en pantalla en lugar de callarlo.**

1. **La ventana observada de un repositorio arranca en `max(repositorio.listo_en, curso.ingesta_actividad_desde)`.** Con el relleno hacia atrás de A-221, en el curso de demostración arranca el **16 de septiembre** —no el 30—, de modo que el 6 de octubre hay **veinte días observados** y el umbral por defecto de **7 días** es plenamente aplicable. **No se toca `curso.umbral_dias_sin_actividad` para maquillar el resultado.**
2. **Si la ventana observada es más corta que el umbral**, el repositorio **no se cuenta entre los inactivos en ninguna parte** —ni en el tablero, ni en Pendientes, ni en la sección 3 del informe diario— y su tarjeta muestra el texto fijo **«Sin dato suficiente: se observan N días de los M que exige el umbral»**. El indicador queda **declarado no concluyente**.
3. **La sección 3 del informe diario declara la ventana** en su encabezado: «actividad observada desde DD-MM-YYYY». **Un informe que dice «tres repositorios sin actividad» sin decir sobre cuántos días observa es un informe que engaña**, y **R2.6.2** pide informar, no alarmar.
4. **El umbral en ventana crítica** —2 días con una entrega que vence en menos de 72 h— **se somete a la misma regla**.

**La ventana observada es derivada**, no una columna: la calcula **la única función de dominio que produce el predicado de inactividad**, en `backend/app/dominio/actividad.py`, junto al predicado de commit contable de A-171 y a `hay_actividad_estudiantil` de A-205. **El tablero, Pendientes y el informe consumen esa misma función**, y ninguna reimplementa el criterio.

**Prueba automatizada:** un repositorio con `listo_en` de hace 3 días y umbral de 7 **no aparece** como inactivo y **sí aparece** con su texto de dato insuficiente.

### A-223 · El techo garantizado de frescura es una fórmula sobre el recuento real, no un número fijo

El requisito no funcional **NFR-2.5-A** se expresa así, y así se publica en `/operacion`:

- **Objetivo declarado:** p95 ≤ 60 s y p99 ≤ 180 s entre la recepción del webhook `push` y la visibilidad del commit. **No cambia.**
- **Techo garantizado sin webhook:** **`ceil(repositorios_en_ingesta_del_curso / tope_por_ciclo) × cadencia`**, donde `tope_por_ciclo` y `cadencia` son los de `reconciliar_actividad` —**200 repositorios y 15 minutos**— y `repositorios_en_ingesta_del_curso` es el **recuento real** de repositorios que **no** están `ARCHIVADO`, `FUERA_DE_ALCANCE` ni `INACCESIBLE`. Con 200 repositorios son 15 minutos; con los 600 que A-090 presupuesta, **45 minutos**.
- **Techo absoluto:** 24 horas, por `barrido_completo_actividad`. **No cambia.**

`/operacion` muestra el techo **calculado sobre el recuento real del curso**, **no un número escrito a mano**, junto al recuento del que sale: «techo garantizado: 45 min · 600 repositorios en ingesta · 200 por ciclo cada 15 min». Es el `techo_garantizado` que consume el sello de antigüedad de A-231.

**Si la medición demostrara que un `304` consume límite secundario**, la cadencia pasa a 30 minutos y el tope a 100 por ciclo, **y la fórmula se recalcula sola**: con 600 repositorios, 180 minutos, y **la pantalla lo dice**. **Subir el tope por ciclo queda descartado**: los 200 son lo que mantiene el ciclo dentro del freno por presupuesto medido de A-219.

Función pura `techo_frescura(curso) -> timedelta` en `backend/app/dominio/`, con pruebas para 200, 600 y el caso degradado. **El texto de la memoria de entrega cita la fórmula, no el número.**

---

## 13. Informes y comunicación (R2.6)

### A-125 · Un único *outbox* para los cuatro canales — ANULADA POR RG-036 en su componente `version`

> **Manda ahora A-224.** La regla de un solo *outbox*, la distinción entre comunicación y acción del docente, y **la clave por persona** se conservan enteras; lo que queda superado es que `version` fuera un componente implícito de la clave: es **`mensaje_saliente.generacion`**, columna auditable, y toda reemisión **la incrementa** en vez de tocar la fila anterior.

**Toda COMUNICACIÓN hacia el exterior** —mensaje de Canvas, anuncio de Canvas, comentario de entrega y correo— pasa por la tabla `mensaje_saliente` y por el trabajo `despachar_outbox`. **Ninguna comunicación se envía de forma síncrona desde una vista, sin excepción**: ni un recordatorio, ni un aviso de repositorio, ni un anuncio, ni un correo. Una comunicación es un efecto sobre un tercero y no debe depender de que una petición HTTP del docente termine bien.

**Qué NO es una comunicación, y por qué esta decisión ya no las prohíbe.** La revisión 1 escribía «ninguna vista escribe hacia fuera de forma síncrona, salvo la publicación de una nota», y con eso volvía ilegales la prueba de escritura del checklist (A-042), la creación del repositorio base (A-066), la carga de archivos (A-067) y la creación de la tarea de registro (A-144) —ninguna de las cuales aparecía tampoco en A-089 ni en el catálogo cerrado de A-114—. Eran **cuatro requisitos sin implementación legal**. La regla correcta distingue dos cosas que la revisión 1 confundía:

| | Comunicación | Acción del docente sobre su propio curso |
|---|---|---|
| Ejemplos | mensaje, anuncio, comentario automático, correo | crear el repositorio base, subir un archivo, publicar una nota, crear la tarea de registro, probar la escritura |
| Destinatario | un tercero que no está mirando | el propio docente, que está mirando la pantalla |
| Si falla | hay que reintentar sin que nadie espere | **hay que decírselo ahora**, porque está esperando el resultado |
| Camino | **siempre por el *outbox*** | **síncrono con contrato**, enumerado en **A-169** |

**La clave de idempotencia es `hash(canal, destinatario, plantilla, entidad, version)`** y es **única en base de datos**. **Incluye el destinatario, y por tanto es siempre por persona**, nunca por grupo: para un grupo de cuatro integrantes se producen cuatro claves distintas y cuatro mensajes, uno a cada uno. Los topes de A-130 se expresan en esos mismos términos y **no contradicen esta clave** — la revisión 1 sí lo hacía, fijando el tope de `repositorio_disponible` «por sujeto y tarea» mientras la clave era por persona, lo que producía 4 mensajes o 1 según qué frase ganara. Gana ésta: **una persona, un mensaje**.

Todo envío queda en bitácora con su estado, su identificador en el proveedor y su error literal si lo hubo.

### A-169 · Las seis escrituras externas síncronas desde una pantalla — ANULADA POR RG-087 en su entrada 4

> **Manda ahora A-226.** La lista **sigue teniendo seis entradas y no crece**, y el contrato de las seis se conserva punto por punto. Lo que cambia es la entrada 4, que pasa a decir «crear **o restaurar** la tarea de registro en Canvas», y lo que se añade es la regla de que **todo endpoint nuevo encola**, con su prueba de arquitectura.

**Lista cerrada.** Cualquier otra escritura externa disparada desde una vista es un defecto de arquitectura y se rechaza en revisión de código, igual que A-089 hace con las lecturas.

| # | Escritura | Pantalla | Decisión | Por qué tiene que ser síncrona |
|---|---|---|---|---|
| 1 | Prueba de escritura: crear y borrar el anuncio `[verificación app]` | Asistente, paso 4 | A-042 | El profesor acaba de marcar la casilla y el checklist tiene que ponerse verde delante de él. **R2.1.6** pide verificar, y verificar en diferido no es verificar |
| 2 | Crear el repositorio base (`POST /orgs/{org}/repos` + `PATCH is_template`) | Tarea → repositorio base | A-066 | **R2.3.5** dice literalmente «permitir al profesor crear **desde la aplicación** un repositorio base». Un botón que dice «lo crearemos en un rato» no es eso |
| 3 | Subir, reemplazar, renombrar o borrar un archivo del repositorio base | Tarea → repositorio base → archivos | A-067 | **R2.3.6** pide administrar los archivos. Un gestor de archivos que no confirma que el archivo se subió es inutilizable |
| 4 | Crear la tarea de registro en Canvas | Personas | A-144 | El profesor revisa el enunciado, pulsa publicar y **tiene que ver el enlace a la tarea creada** para comprobarla en Canvas |
| 5 | Publicar una nota | Corrección | A-139, A-140 | Es la acción explícita del corrector, con relectura inmediata y resultado en pantalla |
| 6 | Validar un login de GitHub en la carga docente | Pendientes | A-148 | Es lectura, no escritura, y ya figura en A-089; se lista aquí para que el contrato de abajo la cubra |

**Contrato obligatorio de las seis, sin excepciones:**

1. **Lectura antes del efecto** (A-115 garantía 3): se comprueba si el efecto ya existe antes de producirlo. Reintentar no duplica.
2. **Intención persistida antes de la llamada**, en la misma transacción, para que un proceso que muere a mitad deje rastro y no un hueco.
3. **Tiempo de espera duro de 20 segundos.** Si se agota, la operación **no se pierde**: se convierte en un trabajo de la cola, la pantalla lo dice con esas palabras y muestra dónde seguirlo. Es la única forma de que una API lenta no bloquee la interfaz.
4. **El resultado se muestra en pantalla**, con el error **literal** del proveedor si lo hubo (A-155).
5. **Queda en `bitacora`** como cualquier otra escritura externa (A-029).
6. **Ninguna de las seis envía una comunicación a un estudiante.** Si una acción síncrona debe además avisar a alguien, el aviso entra en el *outbox* (A-125). **La escritura es síncrona; el aviso nunca lo es.**

### A-126 · Formato por canal, derivado de lo documentado

| Canal | Endpoint | Formato | Fundamento |
|---|---|---|---|
| **Anuncio de curso** | `POST /courses/:id/discussion_topics` con `is_announcement=true` | **HTML mínimo** (`<p>`, `<ul>`, `<li>`, `<a>`, `<strong>`) | El campo `message` está documentado como «The HTML content of the message body» **[DOC]** (`Q-2.6-03`, `Q-2.3-55`) |
| **Mensaje directo** | `POST /api/v1/conversations` | **Texto plano**, con las URL completas en su propia línea, sin ninguna etiqueta | El parámetro `body` está documentado únicamente como «el mensaje a enviar», **sin ninguna mención de HTML, de autoenlazado de URLs ni de longitud máxima** **[DOC]** (`Q-2.3-55`). Es la única opción que se ve correcta tanto si Canvas escapa el HTML como si lo interpreta |
| **Comentario de entrega** | `comment[text_comment]` | **Texto plano** | Documentado como texto, sin mención de HTML **[DOC]** (`Q-2.3-55`) |
| **Correo** | Proveedor transaccional | **HTML con alternativa en texto** | Canal propio, sin restricción externa |

El **asunto** de una conversación se limita a **255 caracteres**, que es el único límite de longitud documentado en ese endpoint **[DOC]** (`Q-2.3-55`).

**Envío masivo: secuencial, un destinatario por llamada**, con la concurrencia 1 de A-039. Se descarta `recipients[]=course_X` y cualquier envío por contexto para los avisos de repositorio, porque **R2.3.12** exige entregar a cada estudiante la información de **su** repositorio. No se usa `bulk_message`, cuya semántica no está documentada como parámetro propio del endpoint **[MEDIR]** (`Q-2.6-04`).

Todas las plantillas están **versionadas** y viven en un único archivo de mensajes, no incrustadas en el código, para que puedan revisarse de una sentada antes de la demostración.

### A-127 · R2.3.12 se implementa con dos mensajes por Canvas, más un anuncio, y con canal alternativo declarado

**Un mensaje por PERSONA, no por repositorio.** El disparador es **`acceso_repositorio` de ese estudiante pasa a `INVITADO` o `ACCESO_DIRECTO`** — no que el repositorio llegue a `OPERATIVO`. La revisión 1 lo colgaba de `OPERATIVO` con tope «1 por sujeto y tarea», y eso producía dos fallos: en un grupo de cuatro se enviaba **un solo mensaje sin decir a quién**, y **el integrante cuyo mapeo llega después —el caso central de R2.3.10— no lo recibía nunca**, porque el tope por sujeto ya estaba consumido. Con el disparador por acceso, **cada integrante recibe su mensaje exactamente cuando hay algo que decirle**, y el que llega tarde lo recibe al invitarlo. Además el mensaje explica **cómo aceptar la invitación**, así que colgarlo de `OPERATIVO` —estado que exige que la invitación ya esté aceptada (A-092)— era colgarlo de que ya no hiciera falta.

**Canal alternativo declarado, porque el checklist puede decir que no hay canal principal.** El ítem 6 de A-041 (`send_messages`) es una **advertencia fuerte** y no bloquea la vinculación: con el permiso ausente, **R2.3.12** quedaba incumplido sin que nada lo impidiera. Ya no:

| Orden | Canal | Condición para usarlo | Requisito de permiso |
|---|---|---|---|
| 1 | **Mensaje directo** `POST /api/v1/conversations` | Ítem 6 en verde | `send_messages` |
| 2 | **Comentario en la entrega de la tarea de registro** del propio estudiante (`comment[text_comment]`, el mismo canal que A-146 ya usa para responderle) | Ítem 6 en rojo y ítem 17 en verde | comentar entregas |
| 3 | **Bloqueo declarado** | Los dos en rojo | El asistente **no completa la vinculación** y dice que **R2.3.12** no puede cumplirse en ese curso, en lugar de dejarlo silenciosamente incumplido |

El canal 2 es privado al estudiante, llega a su bandeja de Canvas igual que el canal 1, y **es el mismo sitio donde declaró su cuenta**, lo que lo hace incluso más natural. La aplicación **escribe en la interfaz qué canal está usando cada curso**, y el informe diario lo recuerda mientras no sea el canal 1.

**Al invitar al estudiante a su repositorio** — mensaje directo (o comentario, según el canal activo), texto plano, que dice **exactamente**:

- el nombre exacto de la **organización** de GitHub,
- el nombre exacto del **repositorio** y su URL completa,
- que la invitación llega **por correo** y también aparece en **la página de notificaciones de GitHub**,
- **que hasta que acepte la invitación la URL del repositorio le mostrará «no encontrado»**, porque GitHub responde `404` en lugar de `403` para repositorios privados **[DOC]** (`Q-2.3-35`). Advertirlo por adelantado evita la mitad de las consultas al equipo docente,
- la fecha de cierre de la primera entrega, con zona horaria escrita,
- qué hacer si el correo no llega.

**Al aceptar la invitación** — confirmación breve con el enlace directo.

**Más un anuncio de curso al inicio de cada tarea** explicando el flujo completo y avisando de que **la invitación es legítima**. Es la defensa práctica contra que los estudiantes la tomen por *phishing*.

Se envía el `html_url` de la invitación cuando la API lo devuelve, y la URL del repositorio como enlace secundario. La forma concreta de ese `html_url` **no está documentada** **[MEDIR]** (`Q-2.3-35`); si en la prueba resulta inservible, el mensaje remite a la página de invitaciones de GitHub más el nombre exacto del repositorio. **Quién figura exactamente como invitador en el correo de GitHub tampoco está documentado** **[MEDIR]** (`Q-2.1-63`, `Q-2.3-34`), así que el texto **describe la invitación sin afirmar un remitente concreto** hasta que la medición lo fije.

### A-128 · Anuncios por sección

Se usa `specific_sections`, documentado y restringido a anuncios de curso **[DOC]** (`Q-2.6-50`), para que un cambio de fecha que sólo afecta a una sección no confunda a las demás. Si el checklist detectó que faltan permisos de publicación de anuncios, **el interruptor aparece deshabilitado con el motivo escrito**, en lugar de fallar al pulsarlo.

Sirve a **R2.6.6**.

### A-129 · Filtro de destinatarios por estado de matrícula

**Sólo se envía a estudiantes con matrícula `active` o `invited`.** Los `inactive`, `completed` y `deleted` no reciben comunicaciones automáticas, y su exclusión se registra.

Motivo: la documentación **no** dice si Canvas acepta como destinatario a un estudiante en esos estados ni qué error devuelve **[MEDIR]** (`Q-2.6-56`). **Filtrar por adelantado con el dato que ya tenemos es más robusto que descubrirlo con un `4xx` en mitad de un lote.** Antes de un envío masivo se contrasta además contra `GET /api/v1/search/recipients?context=course_X`, que es el endpoint documentado para determinar destinatarios válidos.

### A-130 · Catálogo de comunicaciones automáticas (R2.6.7)

Cada una con **su alcance declarado**, su interruptor en `regla_comunicacion`, su clave de idempotencia y su valor por defecto. **La columna «alcance» se añadió en la revisión 2**, porque `regla_comunicacion` tenía unicidad `(tarea_id, evento)` mientras `recordatorio_mapeo` es un asunto **de curso**: un estudiante sujeto de tres tareas habría recibido tres recordatorios diarios, o uno, según lo leyera cada agente.

| Evento | Alcance | Cuándo se dispara | Canal | Por defecto | Tope, **siempre por persona** |
|---|---|---|---|---|---|
| `repositorio_disponible` | **Tarea** | **El acceso de ese estudiante pasa a `INVITADO` o `ACCESO_DIRECTO`** (A-127) | Canal activo de A-127 | **Activado** | **1 por `(tarea, sujeto, estudiante)`** |
| `invitacion_aceptada` | **Tarea** | Webhook `member`/`added` | Canal activo | **Activado** | 1 por `acceso_repositorio` |
| `recordatorio_mapeo` | **CURSO** (`tarea_id` nulo) | **09:00 en la zona horaria del curso** (A-152), a quien falte cuenta de GitHub | Canal activo | **Activado** | **máx. 3 por estudiante y CURSO en total**, nunca dos días seguidos |
| `recordatorio_invitacion` | **Tarea** | 48 h tras invitar sin aceptar | Canal activo | **Activado** | máx. 3 por `(repositorio, estudiante)`, separados ≥ 24 h (A-100) |
| `proximidad_cierre` | **Tarea** | 48 h y 6 h antes de la fecha efectiva de cada entrega | Canal activo | **Activado** | 1 por `(entrega, estudiante, ventana)` |
| `cambio_de_fecha` | **Tarea** | El sincronizador detecta un cambio (A-056) | Anuncio, con `specific_sections` si el cambio es de sección | **Activado** | 1 por cambio |
| `correccion_publicada` | **Tarea** | Se publica la nota de una entrega | Canal activo | **Desactivado** | 1 por `(publicacion, estudiante)` |

**Tres reglas que cierran las lecturas dobles que quedaban:**

1. **Todos los topes son por persona**, coherentes con la clave de idempotencia de A-125, que incluye el destinatario. Para un grupo de cuatro, `repositorio_disponible` produce **cuatro mensajes**, uno por integrante, cada uno cuando se le invita. Nunca uno solo «al grupo», que no tiene bandeja de entrada.
2. **`recordatorio_mapeo` es de curso y su tope es global por estudiante**: tres en todo el curso, no tres por tarea. Un estudiante sin cuenta de GitHub tiene **un** problema, no tres, y recibir tres correos el mismo día por el mismo problema es la forma más rápida de que deje de leerlos. Su interruptor vive en la pantalla de curso, no dentro de una tarea.
3. **Los eventos de alcance `TAREA` se activan y desactivan dentro de cada tarea**, que es literalmente lo que pide **R2.6.7**; el de alcance `CURSO` se activa en Personas. Cuando una regla de tarea no existe todavía, **hereda el valor por defecto de esta tabla** y se materializa la fila al primer cambio.

Toda comunicación tiene **previsualización** antes de enviarse, y la pantalla muestra **a cuántas personas** va a llegar antes de confirmar.

### A-131 · Contenido del informe diario (R2.6.1, R2.6.2) — ANULADA POR RG-041 y RG-207 en su registro y en su invariante

> **Manda ahora A-229.** Las cinco secciones, sus enlaces profundos, la zona horaria del curso y la disponibilidad del informe en la aplicación aunque el correo falle se conservan enteras. Lo que queda superado es que el histórico registrara un booleano —`informe_diario.estado` con **tres valores** y `motivo`; **`hay_tareas_activas` se retira del esquema**— y que el invariante fuera absoluto: **se acota a partir de la primera fila generada para el curso**.

Se genera **por curso, a las 07:00 en la zona horaria de ese curso** —no a las 07:00 de Chile cableadas—, y **sólo si hay al menos una tarea activa** —definida como una tarea con alguna entrega cuya fecha efectiva máxima aún no ha pasado, **o** con repositorios que no están todos operativos—. Si no hay ninguna, **no se genera ni se envía**, exactamente como dice el requisito («si no hay tareas activas entonces no hay informe»), y el histórico registra «sin tareas activas» para poder demostrar que la ausencia fue deliberada y no un fallo.

Secciones fijas, en este orden, y **cada una se omite si está vacía**:

1. **Requiere tu atención hoy** — repositorios `BLOQUEADO` o `ERROR_PERMANENTE`, incidencias bloqueantes sin resolver, credencial de Canvas inválida, permisos de la GitHub App pendientes, versiones en estado `REVISAR`.
2. **Información pendiente** — estudiantes sin cuenta de GitHub, invitaciones sin aceptar con más de 48 h, grupos incompletos, estudiantes sin grupo.
3. **Sin actividad** — repositorios sin commits según el umbral de A-121 y estudiantes sin participación, **con las tres causas distinguidas** de A-120.
4. **Próximos cierres** — entregas que cierran en las próximas 72 h, con el número de sujetos sin ningún commit.
5. **Resumen de ayer** — commits, repositorios activos, versiones capturadas, notas publicadas.

**Cada línea lleva un enlace profundo a la pantalla exacta donde se resuelve.** El informe queda siempre disponible en la aplicación, con histórico y vista previa, **aunque el correo falle**.

**La zona horaria del informe es la del curso, y sus secciones también.** «Ayer» de la sección 5 y los buckets diarios de la sección 3 se calculan con **A-171**, es decir con el día del curso; los umbrales de intervalo («72 h», «48 h») se calculan en UTC y se presentan convertidos (A-152). Un curso con zona distinta de Chile recibe su informe **a las 07:00 suyas**, y sus números son los de sus días. La revisión 1 cableaba `America/Santiago` aquí y en A-130 mientras A-152 admitía cursos con otra zona: el informe llegaba a una hora ajena a su propia regla.

### A-132 · Suscripción individual y bidireccional (R2.6.3)

Cada profesor y cada ayudante controla **su propia** suscripción, y **cada correo lleva un enlace de baja de un solo clic, firmado**. **Nadie puede dar de baja a otro.** El profesor puede ver quién está suscrito, que es información de coordinación, no de control.

**Dónde vive esa pantalla, y es una corrección importante.** La revisión 1 decía «desde Ajustes» y A-151 mapeaba **R2.6.1–R2.6.4** a `/cursos/{id}/ajustes`, pantalla que según A-021 exige `curso.administrar`, permiso marcado **NO CONCEDIBLE** a un ayudante: **un ayudante no podía entrar a la única pantalla desde la que el documento decía que se suscribía**, y **R2.6.3** —«permitir que profesores **y ayudantes** se suscriban o den de baja individualmente»— era inalcanzable para la mitad de sus destinatarios. Queda así:

- **La suscripción vive en `/cursos/{id}/mis-notificaciones`**, pantalla propia que exige **sólo `curso.ver`**, es decir, accesible a todo miembro activo del curso, profesor o ayudante.
- **Está enlazada desde la navegación del curso y desde el pie de cada informe**, no escondida.
- **`/cursos/{id}/ajustes` conserva `curso.administrar`** y sigue conteniendo credenciales, vinculación y zona horaria, que es lo que sí debe estar restringido. **Lo que se mueve es la suscripción, no el permiso.**
- Cambiar la propia suscripción **no es un permiso** (A-021): es una acción sobre uno mismo, y por eso no aparece en la tabla de los nueve.
- El listado de «quién está suscrito» se queda en Equipo, para quien tenga `curso.ver`, como información de coordinación.

### A-133 · Envío del informe por correo y política de cuota (R2.6.4) — ANULADA POR RG-104, RG-196 y RG-197 en su ámbito y en su desenlace

> **Manda ahora A-228.** El reparto **60 / 20 / 20** y el orden de cesión se conservan **exactamente**; lo que queda superado es que la cuota fuera por curso —**es del despliegue y del día**—, que el estado al agotarse fuera `DIFERIDO_POR_CUOTA` —es **`DIFERIDO` con `motivo_estado = 'CUOTA_AGOTADA'`**— y que la reserva operativa no cubriera los avisos al equipo docente, que **también salen de ella**.

Detrás de una interfaz `ProveedorCorreo` con una única implementación activa —**Resend**, plan gratuito— y una implementación de consola para desarrollo y pruebas. **El cambio de proveedor no toca nada fuera de esa clase**, como exige el documento de decisiones de infraestructura.

Restricción documentada que condiciona el diseño: el plan gratuito permite **100 correos al día** **[DOC]** (`Q-infraestructura-28`). Con esa cifra:

- **Un correo por destinatario suscrito**, lo que permite personalizar el enlace de baja y filtrar por curso.

**Reparto completo de los 100 correos diarios, con el correo operativo presupuestado.** La revisión 1 repartía 60 para el informe y 30 suscriptores por curso, y **dejaba fuera del presupuesto cuatro consumidores que el propio documento declaraba**: las cuatro alertas de A-015, el aviso de tamaño de A-007, el aviso de credencial inválida de A-036 paso 5 y la alerta del vigilante de A-112. Una tormenta de incidencias se comía el informe de **R2.6.4**. El reparto queda cerrado:

| Reserva | Cuota diaria | Quién consume |
|---|---|---|
| **Informe docente** (**R2.6.1**–**R2.6.4**) | **60** | Un correo por suscriptor activo, con **máximo 30 suscriptores activos por curso** |
| **Correo operativo** | **20** | Alertas de A-015 (credencial inválida, presupuesto de GitHub bajo, tres fallos del *outbox*, trabajo periódico parado), aviso de tamaño de A-007, aviso de credencial inválida a los profesores de A-036, alerta del vigilante de A-112, `RESPALDO_FALLIDO` de A-170 |
| **Margen de seguridad** | **20** | Sin asignar. Absorbe reintentos y picos; **no se planifica su uso** |

**Quién cede primero cuando compiten, en este orden y sin ambigüedad:**

1. **El correo operativo nunca cede por debajo de 5 envíos diarios**, porque una aplicación que no puede avisar de que está rota es peor que una aplicación caída. Por encima de 5, cede al informe.
2. **El correo operativo se agrupa antes de ceder**: todas las alertas de un mismo ciclo de vigilancia van en **un solo correo con todas las líneas**, no uno por incidencia. Con eso, 20 envíos diarios son 20 ciclos con problema, que es muchísimo.
3. **El informe cede el último**, y cuando cede lo hace **por suscriptor**, no por curso: se envía a los suscriptores que quepan por orden de antigüedad de suscripción y **el resto queda `DIFERIDO_POR_CUOTA`**, no descartado.
4. **Nada se descarta nunca.** Al agotar la cuota: encolar y reintentar al día siguiente, con estado `DIFERIDO_POR_CUOTA` visible en la bitácora e incidencia `CUOTA_CORREO_AGOTADA`.
5. **El panel de operación muestra el consumo del día por reserva**, para que el equipo lo vea antes de que sea un problema.

- **El informe siempre queda disponible en la aplicación aunque el correo falle.** **R2.6.4** pide enviarlo; **R2.6.1** pide generarlo. Generarlo y conservarlo aunque el envío falle es lo que impide perder el requisito por una cuota de terceros.

### A-224 · `clave_idempotencia` es única total, y la reemisión incrementa `generacion`

**El índice es `UNIQUE (clave_idempotencia)`, total.** **No hay índice parcial sobre estados.**

1. La clave es **`hash(canal, destinatario, plantilla, entidad, generacion)`**.
2. `mensaje_saliente` gana **`generacion smallint NOT NULL DEFAULT 1`** —el componente `version` de A-125, **materializado y auditable**— y **`reemplaza_a_id uuid NULL REFERENCES mensaje_saliente(id)`**, que encadena la reemisión con la retenida.
3. **Toda reprogramación** —fecha cambiada, regla reactivada, mensaje retractado que hay que reemitir, reenvío del informe pedido por su destinatario— **incrementa `generacion`** y produce por tanto una clave nueva. **No se toca la fila anterior ni el índice.**
4. **La garantía observable que esto preserva** es la de A-125: **una persona no puede recibir dos veces el mismo mensaje por el mismo hecho**, y marcar el primero como `SUPRIMIDO` **no habilita un segundo idéntico**.
5. Se conservan sin cambio `evento`, las seis FK indexadas, `destinatario_canvas_user_id`, `origen`, `disparado_por_usuario_id`, `disparado_por_trabajo_id`, `programado_para`, `caduca_en`, `asunto` y `cancelacion_solicitada`.

`comunicaciones_programadas` calcula la clave **con `generacion`**; la bandeja de retenidos de `/operacion` muestra la cadena `reemplaza_a_id`; y el reenvío del informe usa `generacion = n_reenvio + 1` **en vez de una clave ad-hoc**.

### A-225 · Dos interruptores ortogonales en `curso`, no tres sinónimos

`curso` tiene **dos** columnas de freno, y sólo dos:

1. **`comunicaciones_salientes text NOT NULL DEFAULT 'ACTIVAS' CHECK IN ('ACTIVAS','SUSPENDIDAS')`**, con `suspension_motivo`, `suspension_desde` y `suspension_por`. **Detiene el despacho de los canales `CANVAS_CONVERSACION`, `CANVAS_ANUNCIO` y `CANVAS_COMENTARIO` de ese curso; no detiene `CORREO`** (A-177). Los mensajes **se siguen generando** y quedan `DIFERIDO` con `motivo_estado = 'SUSPENSION_DE_CURSO'`, y **caducan a los 7 días**. Requiere `curso.administrar`, motivo obligatorio, **banda ámbar permanente** y `bitacora`.
2. **`modo_escritura text NOT NULL DEFAULT 'COMPLETO' CHECK IN ('COMPLETO','SOLO_LECTURA')`**. Cubre lo que la anterior no cubre: **las seis escrituras síncronas de A-169 y el aprovisionamiento de repositorios**, que no son comunicaciones. **`SOLO_LECTURA` implica `SUSPENDIDAS`, nunca al revés**, y el `CHECK` cruzado lo declara: `NOT (modo_escritura = 'SOLO_LECTURA' AND comunicaciones_salientes = 'ACTIVAS')`.

**`curso.comunicaciones_pausadas` no existe.** Los sujetos que no se aprovisionan por el modo quedan en `ESPERANDO_INFORMACION` con el motivo **`CURSO_EN_SOLO_LECTURA`**, séptimo de la lista cerrada de A-094.

**`supresion_comunicacion`** (por estudiante) y **`ventana_supresion`** (por ventana temporal tras una restauración) **se conservan**: no son sinónimos, **son otros ejes**, y su lugar en el orden de decisión está en las guardas 3 y 7 de A-216.

`PATCH /api/cursos/{id}/comunicaciones` cambia el interruptor; `purga_retencion` aplica la caducidad de los diferidos a las 03:00; `vigilancia` abre `COMUNICACIONES_SUSPENDIDAS` pasados 21 días; y `/operacion` gana la bandeja «Mensajes retenidos» como sección de curso (A-232).

### A-226 · A-169 conserva seis escrituras síncronas, y todo endpoint nuevo encola

**La lista de seis escrituras síncronas de A-169 no crece.** Su **entrada 4 se reescribe** como «crear **o restaurar** la tarea de registro en Canvas», y ésa es **la única modificación**. El contrato de las seis —lectura antes del efecto, intención persistida, tiempo de espera duro de 20 s con degradación a trabajo de cola, resultado en pantalla con el error literal, `bitacora`, y **ninguna de las seis envía una comunicación a un estudiante**— se conserva punto por punto.

**Todo endpoint creado por la enmienda encola y no llama:**

| Endpoint | Qué hace | Quién llama al proveedor |
|---|---|---|
| `POST /api/cursos/{id}/verificacion` y `.../items/{item}` | Encolan el checklist | `ejecutar_checklist_vinculacion` (A-192) |
| `POST …/repositorios/{rid}/accesos/{eid}/revocar` | Marca la decisión en la fila | `revocar_acceso_estudiante` (A-212) |
| `POST /api/cursos/{id}/archivar-repositorios` | Encola por tarea | `archivar_repositorios` (A-197) |
| `POST …/tareas/{id}/desarchivar` | Marca la solicitud aprobada y encola | `sincronizar_acceso_docente` (A-197) |
| `POST …/repositorios/{id}/sustituir` | Crea la fila nueva en `LISTO_PARA_CREAR` | `aprovisionar_repositorios` (A-202) |
| `POST …/tareas/{id}/archivar` | Encola | `archivar_repositorios` (A-197) |

> **Una prueba de arquitectura falla la construcción si un manejador de `backend/app/api/` invoca `ClienteCanvas` o `ClienteGitHub` desde un sitio que no sea una de las seis entradas de A-169** (puerta 1 de A-174).

**Por qué no se abre la lista.** Abrirla por comodidad es exactamente lo que A-089 y A-125 prohíben, y **una séptima escritura síncrona añade un modo de fallo visible el 16 de septiembre**, delante del evaluador.

### A-227 · Degradación del canal de Canvas, y qué pasa con los avisos obligatorios

El canal con el estudiante se degrada en el orden de A-127: **canal 1**, mensaje directo; **canal 2**, comentario en la entrega de la tarea de registro. **La conmutación es automática y la decide el mapa de capacidades de A-193**: si `ENVIAR_MENSAJE` cae, `despachar_outbox` conmuta al canal 2 y registra `via_efectiva`; si también cae `COMENTAR_ENTREGA`, el mensaje queda **`BLOQUEADO`** con su motivo y reevaluación cada 30 min, y **`curso.canal_comunicacion_activo` pasa a `BLOQUEADO`**, que es **un hecho declarado en pantalla y no un silencio**.

**Con `canal_comunicacion_activo = BLOQUEADO`, los avisos que otras decisiones declaran obligatorios se comportan así:**

| Aviso | Qué ocurre |
|---|---|
| **Aviso previo de archivado**, 14 días y al ejecutar (guarda 4 de A-197) | **La acción de archivar queda bloqueada** mientras el canal esté `BLOQUEADO`; la pantalla **nombra a cuántos estudiantes no se puede avisar**. Un profesor con `curso.administrar` puede archivar igualmente **con confirmación escrita que declara ese número**, y la declaración queda en `bitacora` y en la ficha de la tarea |
| **Aviso de revocación de acceso** (A-212) | El mensaje no sale; `GRUPO_INCOMPLETO` muestra «no se ha podido avisar al estudiante» y **el texto listo para copiar**, y **la propuesta de revocación no se puede aprobar** hasta que conste el aviso o el profesor declare por escrito que avisó por otra vía |
| **Invitación al repositorio y guía de acceso** (**R2.3.12**) | **El aprovisionamiento continúa**; los repositorios quedan creados y el acceso invitado, y la tarea muestra banda ámbar «N estudiantes no han recibido las instrucciones» **con el texto exportable** |
| **Notificación de nota publicada** (A-130) | Se queda en el *outbox* con su guarda de `posted_at` y **sale sola cuando el canal se recupera**; no se pierde y no se duplica, por la idempotencia de A-224 |

> **Ningún aviso obligatorio se da por enviado cuando no salió, y ninguna acción irreversible —archivar, revocar— se ejecuta sola apoyándose en un aviso que no salió.**

`puede_archivar(tarea)` (A-197) y la aprobación de revocación (A-212) **consultan el estado del canal y devuelven su motivo**. La aplicación **escribe en la interfaz qué canal está usando cada curso**, y el informe diario lo recuerda mientras no sea el canal 1.

### A-228 · La cuota de correo es del despliegue y del día, con tres reservas y un solo nombre

**La cuota de A-133 es la del proveedor transaccional: 100 correos al día para TODO EL DESPLIEGUE**, repartidos en **60 informe / 20 operativo / 20 margen**, con el orden de cesión de A-133 intacto. **No es una cuota por curso.**

> **Por qué del despliegue.** El cupo lo impone el proveedor **sobre la cuenta**, no sobre el curso. Contarlo por curso haría que dos cursos con incidentes simultáneos **creyeran tener 40 envíos operativos cuando el proveedor sólo acepta 20**, y el segundo incidente **se perdería en silencio justo cuando más importa**.

**De ella salen todos los correos que la aplicación envía**, a estudiantes o a docentes, y **cada envío se registra en `mensaje_saliente`** con `canal = 'CORREO'`, su **`reserva ∈ {INFORME, OPERATIVO, MARGEN}`** y su motivo.

1. Se cargan a **`OPERATIVO`**: las **cinco** alertas de A-177, el correo a los profesores de A-036, el aviso de tamaño de base de A-007, `RESPALDO_FALLIDO`, los dos correos de acceso docente de A-187 y A-188, y el «avisar a esta persona por correo» de una invitación de organización agotada.
2. Se carga a **`INFORME`** el informe diario y sus reenvíos.
3. **Techo transitorio de 40** para el correo operativo entre el **16 de septiembre y el 2 de octubre**, con la incidencia informativa `CORREO_OPERATIVO_ELEVADO` por encima de 20.
4. **Agotada la reserva y agotado el margen, el correo queda `DIFERIDO` con `motivo_estado = 'CUOTA_AGOTADA'`** y se abre la incidencia `CUOTA_CORREO_AGOTADA`. **Nunca se descarta un envío en silencio.** **`DIFERIDO_POR_CUOTA` no es un estado.**
5. **Las comunicaciones por Canvas —conversaciones, comentarios y anuncios— no consumen esta cuota.**

Función pura **`cuota_correo_restante(reserva, dia)`** sobre el despliegue; `/cursos/{id}/ajustes` muestra el consumo del día y lo que queda; y **`/operacion` lo muestra como magnitud de despliegue**, sin filtrar (A-232).

### A-229 · `informe_diario`: ventana con zona en el nombre, estado con motivo, e histórico desde la primera fila

**1 · La fila queda así**, conservando su único `(curso_id, fecha)` con `fecha` **en la zona horaria del curso**:

```
estado             text NOT NULL CHECK (estado IN ('GENERADO','SIN_TAREAS_ACTIVAS','NO_GENERADO'))
motivo             text NULL      -- obligatorio si estado = 'NO_GENERADO'
ventana_desde_utc  timestamptz NOT NULL
ventana_hasta_utc  timestamptz NOT NULL
origen             text NOT NULL CHECK (origen IN ('PROGRAMADO','MANUAL'))
disparado_por_usuario_id uuid NULL
frescura           jsonb NOT NULL
```

**`hay_tareas_activas` se retira del esquema.**

2. **Los nombres llevan la zona dentro**, que es lo que A-073 y A-152 obligan a no dejar implícito.
3. **Semántica acumulada:** la ventana cubre **el período realmente acumulado desde el último informe generado con éxito** —`ventana_desde_utc` es el `ventana_hasta_utc` del último informe generado del curso, o `curso.creado_en` si es el primero—, **acotado a 7 días**, y el encabezado lo dice con esas palabras.
4. **Las secciones 1 a 4 de A-131 son estado en el instante de generación**; **sólo la sección 5 usa la ventana**, y se titula «Resumen del período» cuando cubre más de un día.
5. **`estado` sustituye al booleano** porque **A-131 exige poder demostrar que la ausencia fue deliberada**, y un booleano no distingue «no había tareas activas» de «no se pudo generar».
6. **Una fila ya enviada es inmutable:** `contenido`, `contenido_html` y `contenido_texto` **se congelan al generarse**, por el mismo motivo por el que `version_entrega` es inmutable.

**2 · El invariante del histórico se acota a partir de la primera fila del curso.** No falta ninguna fila de `informe_diario` **entre la primera generada para ese curso y hoy**. La primera es la del día en que el trabajo entra en servicio para él —el **3 de octubre** en el curso de demostración—, y **no se generan filas retroactivas** para los días anteriores.

> **Por qué no el invariante absoluto.** Con el trabajo naciendo el 3 de octubre, «nunca falta la fila de un día pasado» es **falso para los diecisiete días anteriores**, y el primero que lo comprobaría sería el invariante nocturno, **en rojo por diseño y sin nada que reparar**. Lo que A-131 exige demostrar **se sigue demostrando entero**: para los días con trabajo, con `estado` y `motivo`; para los anteriores, **con la fecha de inicio declarada**.

`GET /api/cursos/{id}/informes` y la pantalla del histórico **declaran esa fecha** con el texto «el informe diario de este curso se genera desde el DD-MM-YYYY», y `/alcance` la publica (A-234). El invariante que `verificar_invariantes` comprueba **es el de esta regla, no el absoluto**, y se escribe sobre `min(informe_diario.fecha)` del curso.

**3 · Ritmo del trabajo:** **07:00 en la zona del curso** más barrido cada 30 minutos entre las 07:00 y las 23:00 de esa zona, ***no-op*** si la fila `(curso, hoy)` ya existe. La clave de idempotencia del correo es `hash(CORREO, destinatario, informe_diario_correo, informe_diario.id, generacion)` (A-224), y **las incidencias silenciadas quedan fuera de la sección 3** (A-207).

---

## 14. Corrección (R2.7)

### A-134 · Asignación de entregas entre correctores (R2.7.1)

`asignacion_correccion` con unicidad `(entrega_id, sujeto_id)`: **un corrector por entrega y sujeto**. El profesor reparte desde la pantalla Corrección → Repartir, con tres modos: **equitativo automático**, **por sección** y **manual**. El reparto se hace **por entrega**, no por tarea, porque **R2.7** exige que cada entrega se corrija de manera independiente.

Al retirar a un ayudante, sus asignaciones quedan `SIN_CORRECTOR` con incidencia (A-025), nunca borradas.

### A-135 · La bandeja del corrector y la navegación (R2.7.2, R2.7.3)

- **«Mis asignaciones» es la vista por defecto de un ayudante** al entrar en Corrección. No tiene que buscar nada.
- **Navegación:** barra «N de M», atajos de teclado, botón «siguiente sin corregir», y orden estable por sujeto para que la posición no cambie entre sesiones.
- Filtros por estado y por entrega, y contador de pendientes en la navegación.

### A-136 · Acceso directo a la versión que corresponde revisar (R2.7.4) — ANULADA POR RG-018 en su comprobación previa

> **Manda ahora A-230.** La tabla de estados de `acceso_docente_repositorio` y la regla «decir por qué no está listo es mejor que entregar un enlace roto» se conservan enteras; lo que se añade es que el panel **comprueba también `repositorio.estado`** y, con `INACCESIBLE`, muestra el motivo y la fecha **en lugar de una URL que dará `404`**.

El panel izquierdo de la pantalla de corrección muestra, destacado, el enlace `https://github.com/{org}/{repo}/tree/{sha}` de la versión de **esa** entrega, más el enlace de comparación con **la entrega anterior según A-173** cuando existe (A-104). **Se construye desde datos persistidos: no cuesta ninguna llamada a GitHub.**

**Y —esto es lo que faltaba— el enlace abre.** La revisión 1 se felicitaba por no gastar una llamada sin notar que el problema no era el coste de la llamada sino **el permiso del humano al otro lado**: el repositorio es `private: true` (A-065) y GitHub responde `404` a quien no tiene acceso **[DOC]** (`Q-2.3-35`), de modo que el ayudante recibía un enlace que no abría y **R2.7.4** —«acceder directamente a la versión del repositorio correspondiente a la entrega que está siendo revisada»— no se cumplía. **A-163 concede la lectura al equipo docente**, y esta pantalla **comprueba el estado antes de pintar**:

| Estado de `acceso_docente_repositorio` | Qué muestra el panel |
|---|---|
| `CONCEDIDO` | El enlace, destacado, con botón de copiado |
| `PENDIENTE` | «Preparando tu acceso al repositorio», con la hora del próximo intento. **No se pinta un enlace que dará `404`** |
| `ERROR` | El motivo literal de GitHub, el botón «reintentar ahora» y el enlace a la pantalla de vinculación si la causa es de permisos |

**Decir por qué no está listo es mejor que entregar un enlace roto**, y es la diferencia entre un requisito cumplido y uno que parece cumplido hasta que alguien lo pulsa.

Si la versión llevaba advertencias de LFS o submódulos (A-101), aparecen en la cabecera de la pantalla, para que el corrector sepa por qué puede faltar contenido.

### A-137 · La rúbrica se lee en vivo y no se persiste (R2.7.5)

El objeto `assignment` trae la rúbrica **embebida sin necesidad de ningún `include[]`**, con los criterios, sus `id`, sus `ratings` y los `id` de cada rating **[DOC]** (`Q-2.7-30`), que es exactamente lo que necesita el formulario.

**Se relee al abrir la pantalla y de nuevo justo antes de publicar**: calificar contra una rúbrica que el profesor cambió hace diez minutos produciría un `rubric_assessment` con identificadores inexistentes. Caché de 15 minutos.

Los ajustes de presentación (`free_form_criterion_comments`, `hide_points`) viven en el objeto `Rubric` y no en el embebido **[DOC]** (`Q-2.7-30`), así que se piden con una llamada adicional `GET /courses/:id/rubrics/:id`, **una vez por entrega**, cacheada 15 minutos.

### A-138 · Alcance declarado de rúbricas y de entregas soportadas — ANULADA POR RG-019, RG-020 y RG-032 en sus filas 3 y 4

> **Mandan ahora A-214** —la fila 3 se lee «nace con **`publicable = false` y su motivo**», no «nace `NO_PUBLICABLE`», y lo mismo vale para las filas 5 y 6— y **A-203** —el resultado de las validaciones se persiste en `entrega.validaciones jsonb` y las advertencias de fecha en `entrega.advertencias text[]`, y la fila 4 se deriva de `entrega.publicada`, que es el único espejo de `published`—. Las seis validaciones, sus dos desenlaces y la reserva de `TAREA_INCONSISTENTE` se conservan enteras.

- **Se soportan** rúbricas de criterios con `ratings` y puntos.
- **Se muestran en modo lectura y no se evalúan desde la aplicación** las filas vinculadas a *learning outcomes* y los criterios con rango, con un aviso que remite a SpeedGrader. Motivo: la documentación **no** explica cómo contribuyen al `score` ni cómo se representan en `rubric_assessment` **[MEDIR]** (`Q-2.7-29`), y **publicar una nota calculada con una fórmula supuesta sería peor que no publicarla**.
- **Las entregas moderadas y las anónimas quedan fuera de alcance de publicación**: se pueden vincular para efectos de fecha y repositorio, pero **la publicación de nota queda deshabilitada con el motivo escrito**, porque el endpoint síncrono de publicación de notas provisionales está deprecado con fecha efectiva 2026-10-15 **[DOC]** (`Q-2.3-03`), nueve días después de la entrega final.
**Validaciones al vincular una entrega: tabla de desenlaces, sin «según el caso».** La revisión 1 enumeraba cuatro validaciones y no asignaba desenlace a ninguna, y **no incluía el conflicto de modalidad, que es justo el que R2.3.3 exige resolver**. Cada fila tiene ahora un único desenlace posible:

| # | Validación | Desenlace | Por qué |
|---|---|---|---|
| 1 | **Conflicto de modalidad**: el assignment es grupal y la tarea es individual, o al revés | **BLOQUEO** | **R2.3.3** exige que todas las entregas de una tarea tengan la misma configuración. A-081 lo hace estructuralmente imposible de representar, así que **hay que impedirlo en el vínculo o no hay dónde guardarlo** |
| 2 | **Conflicto de `group_category_id`**: el assignment es grupal con una categoría distinta de la de las entregas ya vinculadas | **BLOQUEO** | Serían dos conjuntos de grupos, y por tanto dos conjuntos de sujetos, para una tarea que por **R2.3.4** comparte repositorios. No hay resolución correcta: hay que rechazarlo |
| 3 | `grading_type = not_graded` | **ADVERTENCIA** | Se vincula sin problema para fechas, repositorios y seguimiento; lo único que se pierde es publicar nota, y la corrección nace `NO_PUBLICABLE` con el motivo escrito (A-105) |
| 4 | `published = false` | **ADVERTENCIA** | Una entrega no publicada es un borrador legítimo del profesor. Se vincula, se muestra «no publicada en Canvas» y **no se envía ninguna comunicación sobre ella** hasta que se publique |
| 5 | `moderated_grading = true` | **ADVERTENCIA** | Se vincula para fecha y repositorio; **la publicación de nota queda deshabilitada** con el motivo escrito, por el endpoint deprecado con fecha efectiva 2026-10-15 **[DOC]** (`Q-2.3-03`) |
| 6 | `anonymous_grading = true` | **ADVERTENCIA** | Igual que la anterior |

**Qué significa exactamente cada desenlace, para que no quede a interpretación:**

- **BLOQUEO** = el botón «vincular» **rechaza la operación en el momento**, con un mensaje que dice qué configuración tiene el assignment, qué configuración tiene la tarea y qué hacer (crear otra tarea, o cambiar el assignment en Canvas). **No se crea la fila `entrega`**, no se abre incidencia y no se toca el estado de la tarea: no ha pasado nada.
- **ADVERTENCIA** = **se vincula**, se muestra el aviso en la pantalla de vinculación **y** de forma persistente en la tarjeta de la entrega, y se abre incidencia `INFORMATIVA`. La entrega funciona con la limitación declarada.

**El estado `TAREA_INCONSISTENTE` y su incidencia homónima quedan reservados a un caso, y sólo a uno:** que una entrega **ya vinculada** cambie de modalidad **en Canvas** después del vínculo, lo que la aplicación no puede impedir. Entonces la tarea pasa a `INCONSISTENTE`, **el aprovisionamiento se detiene** (A-094), la incidencia es **BLOQUEANTE** y la pantalla ofrece las dos salidas: revertir el cambio en Canvas, o desvincular esa entrega. **Nunca se alcanza ese estado por una vinculación nueva**, porque la fila 1 de la tabla la impide antes.

### A-139 · Publicación de notas: escribir una vez, verificar por integrante (R2.7.6) — ANULADA POR RG-028 y RG-031 en su fuente de verificación

> **Mandan ahora A-206** —la verificación se apoya en la tabla espejo **`estado_canvas_submission`, con granularidad por estudiante**, que es la que detecta al integrante sin nota propagada— y **A-204** —el conjunto de integrantes que se califica es **`version_entrega.integrantes jsonb`**, congelado al corte, y no una tabla aparte—. Las tres filas de «cómo se escribe», el bloque rojo de divergencia y la regla «una escritura por grupo» se conservan enteras.

**La revisión 1 se contradecía con su propia cita.** Justificaba iterar por integrante porque hacía falta «saber quién quedó publicado y quién no», mientras citaba que con `grade_group_students_individually=false` **Canvas aplica la nota a cada integrante del grupo** **[DOC]** (`Q-2.7-37`). Si eso es cierto, cada una de las N llamadas reescribe a los N: el estado por estudiante era ilusorio, se producían N² efectos y **carreras de sobreescritura** entre llamadas que compiten por la misma submission. Escribir más veces no da más certeza; da más ruido. El procedimiento correcto separa **escribir** de **verificar**:

| Caso | Cómo se escribe | Cuántas llamadas |
|---|---|---|
| **Entrega individual** | Una llamada al estudiante | 1 |
| **Entrega grupal con `grade_group_students_individually = false`** | **Una sola llamada**, dirigida a un integrante cualquiera del grupo (el de menor `canvas_user_id`, para que sea determinista y reproducible), con **`comment[group_comment]=true`** para que el comentario sí alcance a todos —que era el motivo 1 de la revisión 1, y sigue siendo válido— | **1** |
| **Entrega grupal con `grade_group_students_individually = true`** | Una llamada por integrante: en este modo Canvas **no** propaga, y cada uno es una nota distinta | N |

**La verificación es la que da la certeza que R2.7.7 necesita, y cuesta una llamada, no N.** Inmediatamente después de escribir se ejecuta la **lectura masiva de A-142** —`GET /courses/:id/students/submissions?student_ids[]=all&assignment_ids[]=…`, endpoint documentado, paginado y masivo— y de su respuesta se crea **una fila de `publicacion_nota` por integrante**, con el `score`, el `entered_score` y el `graded_at` que Canvas devolvió **para esa persona**. Así:

- **El estado por estudiante es real, no supuesto**: sale de lo que Canvas dice, no de lo que la aplicación cree haber escrito.
- **Si la propagación no ocurriera** —posibilidad abierta, porque la propagación de `rubric_assessment` a los integrantes **no está documentada** **[MEDIR]** (`Q-2.7-37`)—, la verificación lo detecta al ver integrantes sin nota, y **entonces sí** se publica individualmente a los que falten, con una llamada por cada uno. **La iteración pasa de ser el mecanismo a ser el remedio**, que es su sitio.
- **No hay carreras de sobreescritura**, porque hay una sola escritura en vuelo por grupo.
- **El total baja de N escrituras + 0 lecturas a 1 escritura + 1 lectura compartida por todo el lote.**

**El conjunto de integrantes que se califica es el que estaba en el grupo en la fecha de corte**, que la aplicación conoce porque lo persistió en `version_entrega` y en `participacion_entrega`.

Cada escritura envía en **una sola petición**: `submission[posted_grade]`, `submission[late_policy_status]=none`, `comment[text_comment]`, `comment[group_comment]` cuando corresponde, y `rubric_assessment[...]`. Un fallo en un sujeto **no bloquea la publicación del resto del lote**.

### A-140 · Pre-chequeo, política de entrega tardía y relectura obligatoria

**Antes de llamar a Canvas**, por entrega:

1. Se leen los **períodos de calificación** (`GET /courses/:id/grading_periods`) y se comprueba `is_closed`, porque las notas sólo pueden cambiarse antes de la fecha de cierre del período **[DOC]** (`Q-2.7-64`). Si está cerrado, la corrección pasa a `NO_PUBLICABLE` **antes de intentar la llamada**, con mensaje accionable y enlace a Canvas.
2. Se comprueba el estudiante contra `GET /assignments/:id/gradeable_students`. Si no aparece, no se intenta la escritura y se declara no publicable con el motivo. La documentación **no** dice qué criterio usa ese endpoint **[MEDIR]** (`Q-2.7-63`), así que se usa como filtro conservador, no como verdad.
3. Se lee `GET /courses/:id/late_policy`. Si hay deducción automática activa, **se avisa al corrector de que la aplicación va a enviar `late_policy_status=none`**.

**Después de publicar, la aplicación relee la submission siempre** y compara `entered_score` con `score`. Si difieren, la corrección pasa a `PUBLICADA_CON_ADVERTENCIA` y la interfaz muestra el descuento aplicado con enlace a Canvas.

Motivo del `late_policy_status` explícito: si el curso tiene una política de descuento automático, **una entrega espontánea de un estudiante en Canvas podría reducir la nota que la aplicación publica** **[DOC]** (`Q-2.7-67`). Que enviar `none` neutralice una deducción **ya aplicada** **no está documentado** **[MEDIR]**, y por eso existe la relectura: **la diferencia nunca es silenciosa.**

### A-141 · Formato de la nota y qué manda

- Se envía siempre en el formato canónico del `grading_type` de la entrega: `points` como número decimal; `percent` con el signo anexado; `pass_fail` como `pass` o `fail`; `letter_grade` como letra **sólo si la entrega tiene esquema definido**, porque la documentación dice que la letra se rechaza si no lo hay **[DOC]** (`Q-2.7-32`). `gpa_scale` y `not_graded` quedan **fuera de alcance con motivo escrito**.
- El número de decimales que Canvas conserva **no está documentado** **[MEDIR]** (`Q-2.7-32`), así que el campo acepta dos decimales y **la interfaz muestra el valor que devuelve Canvas tras publicar**.
- **El formulario calcula pero no decide.** Muestra la suma de los criterios como sugerencia y permite sobrescribir la nota final. **Manda lo que Canvas devuelve, no lo que la aplicación calculó**, porque las rúbricas y las calificaciones viven en Canvas por mandato del enunciado.

### A-142 · Estado de corrección local, y trazabilidad del corrector real — ANULADA POR RG-031 y RG-101 en su botón de contraste

> **Manda ahora A-206.** La regla «el estado de **R2.7.7** se calcula desde la base local, no desde `submission_summary`» y las tres compensaciones de trazabilidad se conservan enteras; lo que queda superado es que el contraste con Canvas fuera un botón puntual: hay un **lector periódico único**, `reconciliar_notas_canvas`, y **un solo almacén de su estado**, del que se deriva `contraste_canvas` y la incidencia `NOTA_DIVERGENTE_EN_CANVAS`.

**El estado de R2.7.7 se calcula desde la base local, no desde `submission_summary` de Canvas.** Motivo: la documentación **no** define la regla de clasificación de esos contadores y, en particular, **no dice en qué categoría cae una submission `unsubmitted` con nota**, que es precisamente el caso normal aquí **[MEDIR]** (`Q-2.7-55`). La aplicación conoce su propio estado con certeza y no depende de una semántica que no está escrita.

Como contraste, la pantalla ofrece un botón **«comprobar contra Canvas»** que lee `GET /courses/:id/students/submissions?student_ids[]=all&assignment_ids[]=…` —endpoint masivo y paginado, **no una llamada por estudiante**— y **señala cualquier discrepancia** entre lo que la aplicación cree publicado y lo que Canvas tiene.

**Trazabilidad del corrector.** Toda escritura en Canvas se hace con el token del profesor, de modo que `grader_id` será el del profesor y no el del ayudante que corrigió, por la restricción de §1.1. Que `grader_id` valga exactamente el id del titular del token es una inferencia por eliminación, no una frase documentada **[MEDIR]** (`Q-2.7-49`). Se compensa en **tres** lugares, y es una decisión de diseño, no un parche:

1. La aplicación guarda en `correccion` y en `bitacora` **quién corrigió realmente y quién pulsó el botón**.
2. **Añade al comentario de la submission una línea final** con el nombre del corrector y la fecha: «Corregido por Ana Pérez (ayudante). Publicado por el sistema de gestión del curso.» Así la información existe **también dentro de Canvas**, que es donde la buscará quien no use la aplicación.
3. **La pantalla de publicación lo dice explícitamente antes de publicar**, para que nadie se sorprenda.

### A-143 · Publicación sobre entregas sin submission: el riesgo se gestiona, no se ignora

El caso normal de este proyecto es que **nadie entrega en Canvas**: el trabajo está en GitHub. Que `PUT .../submissions/:user_id` con `posted_grade` funcione sobre una submission `unsubmitted` de un assignment con `submission_types=none` **no está documentado ni afirmado ni negado** **[MEDIR]** (`Q-2.7-38`). Es el riesgo más crítico del área y se trata así:

- **Se mide antes del 14 de septiembre**, con prioridad máxima (§19, RA-09). La revisión 1 la fechaba el **20 de septiembre**, cuatro días **después** de la parcial y sin holgura para rediseñar nada si salía mal. Se adelanta al 14 porque la medición no depende de nada que no exista ya el 11: basta un assignment de prueba con `submission_types=none` en el curso real y un `PUT` de nota sobre una submission `unsubmitted`. Cuesta diez minutos y compra tres semanas de margen.
- La aplicación **recomienda** al vincular que la entrega de Canvas tenga `submission_types=none`, lo que además **cierra la vía a entregas espontáneas que activarían descuentos por retraso** **[DOC]** (`Q-2.7-67`).
- **Plan alternativo si la medición sale negativa, y este plan SÍ cumple R2.7.6.** El de la revisión 1 **queda retirado**: preaprobaba degradar **R2.7.6** a «registrar desde la plataforma con un paso de confirmación en Canvas», es decir, autorizaba de antemano exactamente lo que el criterio 1 de §0.4 obliga a descartar —«si una opción incumple o deja cojo un `R2.x.y`, se descarta por elegante que sea»—. **La carta no puede preaprobar lo que su propia regla de oro prohíbe.** El plan nuevo:

  > Si publicar sobre una submission `unsubmitted` con `submission_types=none` no funciona, la aplicación **ofrece al profesor, con consentimiento explícito y previsualización, ajustar `submission_types` de esa entrega de Canvas en un clic** —exactamente el mismo patrón con el que A-144 ya crea un assignment: la aplicación propone, muestra qué va a cambiar, y el profesor confirma—. Hecho el ajuste, la publicación desde la plataforma funciona y **R2.7.6 se cumple entero**: «registrar las calificaciones desde la plataforma de manera que queden almacenadas en Canvas».

  El ajuste concreto se decide con el resultado de la medición —el candidato es `submission_types[]=on_paper`, que representa una entrega hecha fuera de Canvas, que es literalmente el caso de este proyecto—. **Requiere el mismo permiso `manage_assignments` que ya comprueba el ítem 16 de A-041**, así que no introduce ninguna dependencia nueva.

  **Sigue sin forzarse nada sin permiso:** modificar el assignment del profesor sin pedirlo sería invasivo, y no se hace. Lo que cambia es que la salida ya no es «hazlo tú a mano en Canvas», sino «pulsa aquí y lo hago yo, esto es lo que va a cambiar».
- **Si incluso ese ajuste fallara**, la aplicación conserva la preparación completa de la nota y lo declara como incumplimiento abierto en la interfaz y en la defensa. **Es el último recurso, no el plan.** Y con la medición el 14 de septiembre queda margen real para rediseñar, que era el otro problema de la revisión 1.

### A-230 · Una versión de un repositorio inaccesible sigue siendo corregible y publicable

Cuando un repositorio pasa a `INACCESIBLE` (A-211), **sus filas de `version_entrega` no se modifican, no se marcan como irrecuperables y no cambian de estado**: son inmutables (A-085, A-204) y **la evidencia normativa es `commit_sha` en la base propia**, respaldada a diario (Ley 4, A-016, A-104).

1. **La incidencia es informativa, nunca bloqueante:** `REPOSITORIO_INACCESIBLE`, severidad `ADVERTENCIA`, **una por repositorio** —no una por versión—.
2. **El corrector puede seguir corrigiendo y puede publicar la nota.** La calificación depende del SHA capturado, de la fecha de corte y del bloque denormalizado copiado en la propia fila. **`correccion.publicable` no cambia por este motivo y `motivo_no_publicable` no gana ningún valor**: bloquear la publicación **castigaría al estudiante por un borrado que no hizo** y dejaría **R2.7.6** incumplido por una causa ajena a la corrección.
3. **El panel de corrección y el timeline comprueban `repositorio.estado` antes de pintar el enlace** —junto a la comprobación que A-136 ya hace sobre `acceso_docente_repositorio`— y, con `INACCESIBLE`, muestran **«versión registrada; el repositorio ya no está accesible en GitHub desde el *fecha*, por *motivo*»** en lugar de una URL que dará `404`. Lo mismo con el enlace `compare/{sha_anterior}...{sha_actual}`.
4. **Reconocimiento escrito si nadie abrió nunca ese código.** Si la corrección **no** llegó a `EN_CURSO` antes de que el repositorio se volviera inaccesible, el diálogo de publicación exige marcar **«califico sin haber podido abrir el código de esta versión»**. Queda en `bitacora` con actor y fecha, con la acción `CALIFICADA_SIN_CODIGO`, y **se muestra de forma permanente junto a la nota**. Si la corrección ya estaba en `EN_CURSO` o más avanzada, **no se pide nada**.

`correccion` gana **`reconocimiento_sin_codigo` (booleano)** y **`reconocimiento_sin_codigo_en` (`timestamptz` nullable)**, y **ninguna incidencia nueva** más allá de `REPOSITORIO_INACCESIBLE`.

Sirve a **R2.3.11**, **R2.4.7**, **R2.4.8**, **R2.7.4**, **R2.7.6**, **R2.7.7**.

---

## 15. Estrategia de enrolamiento de estudiantes

El enunciado señala esta parte explícitamente como **evaluada por su usabilidad** (§2.2), y es la que más restringe el hecho de que **los estudiantes no entran a la aplicación** (§1.4). Hay cuatro vías y **todas conviven**, en este orden de preferencia.

### A-144 · Vía principal: una tarea de Canvas como formulario

La aplicación crea en Canvas, desde la pantalla Personas, una tarea llamada **«Registro de tu cuenta de GitHub»** con `submission_types[]=online_text_entry`, `points_possible=0`, `omit_from_final_grade=true`, publicada y con una fecha de cierre holgada. **El enunciado y las instrucciones los redacta la aplicación y el profesor puede editarlos antes de publicar.** El estudiante no entra a la aplicación en ningún momento: usa Canvas, que ya usa.

La recolección es **incremental**: `GET /api/v1/courses/:id/students/submissions?student_ids[]=all&assignment_ids[]=<aid>&submitted_since=<marca>` cada 3 minutos —endpoint documentado que admite filtro incremental por fecha **[DOC]** (`Q-2.2-11`)— **más un volcado completo cada hora como red de seguridad**, porque **no está documentado si un reenvío actualiza `submitted_at`** **[MEDIR]** (`Q-2.2-11`).

**El permiso del que depende esta vía se comprueba, y antes no se comprobaba.** Crear un assignment en Canvas exige `manage_assignments` (o su equivalente `manage_assignments_add`) en el token del profesor. Las comprobaciones de A-041 verificaban notas, anuncios, mensajes, correos, secciones, categorías, política de atraso, períodos y paginación, y **no verificaban la creación de tareas**: la vía principal de **R2.2.4** y **R2.2.5** descansaba en un permiso que el checklist de **R2.1.6** no miraba. **Ahora es el ítem 16 y es bloqueante.**

**Si el permiso faltara**, la creación de la tarea de registro se deshabilita **con el motivo escrito en el botón**, y la pantalla ofrece las tres vías complementarias de A-148 —edición manual, importación CSV y reintento asistido— más las instrucciones exactas para que el profesor cree la tarea a mano en Canvas y la vincule después. **R2.2.4** y **R2.2.5** siguen cumpliéndose por esas vías; lo que se pierde es la comodidad, no el requisito.

Sirve a **R2.2.4**, **R2.2.5**.

### A-145 · Reglas de extracción: el cuerpo es HTML, no texto plano

**El extractor asume HTML.** La documentación establece que el `body` de una entrega `online_text_entry` es un fragmento HTML saneado con el mismo conjunto de reglas que la interfaz web de Canvas **[DOC]** (`Q-2.2-11`). **Un extractor que asuma texto plano fallaría con cualquier estudiante que pegue un enlace desde el navegador**, que es el caso más común.

Procedimiento: quitar etiquetas, decodificar entidades, normalizar espacios, recortar. Después se aplican **en orden** cuatro patrones:

1. URL de perfil (`github.com/<login>`),
2. arroba (`@login`),
3. login desnudo que cumpla las reglas de nombre de GitHub,
4. correo `…@users.noreply.github.com`.

Si **ninguno casa** o **casan dos candidatos distintos**, el mapeo queda `NO_RESUELTO` con el texto crudo guardado en `evidencia`.

**El candidato se valida siempre contra GitHub** con `GET /users/{login}`; se guarda el **`id` numérico** y el **`login` canónico devuelto por la API**, no el que escribió el estudiante. Se rechaza si es una organización (A-091).

### A-146 · El bucle se cierra dentro de Canvas

**La aplicación responde siempre por el mismo canal por el que le hablaron.** Cada intento produce un **comentario en la propia entrega de Canvas** del estudiante (`comment[text_comment]`, texto plano), que dice:

- **si salió bien:** qué cuenta quedó registrada, con el login canónico devuelto por GitHub, y el nombre exacto del repositorio que recibirá;
- **si salió mal:** qué escribió y qué debe corregir, con el motivo concreto — «no existe una cuenta de GitHub con ese nombre», «eso es una organización, no una persona», «esa cuenta ya fue declarada por otro estudiante», «escribiste `github.com/jperez/tarea1`; escribe sólo `jperez`».

**Ésta es la pieza que hace usable el proceso sin que el estudiante entre a la aplicación**: recibe confirmación en el mismo sitio donde actuó. Es exactamente lo que **R2.2.5** pide al hablar de «completar progresivamente las asociaciones que aún no estén disponibles», y es lo que se demuestra el 16 de septiembre.

### A-147 · Reenvíos y conflictos

- Un valor nuevo **reemplaza al anterior mientras el mapeo no esté vigente y confirmado**.
- Si ya estaba vigente y **ya hay repositorio creado**, el reenvío **no cambia nada en silencio**: crea la incidencia `GITHUB_DUPLICADO` o `MAPEO_NO_RESUELTO` según el caso, para que el docente decida. Cambiar en silencio a quién pertenece un repositorio ya creado es inaceptable.
- Toda corrección crea una fila nueva y supersede la anterior (A-078). **El historial completo de quién declaró qué y cuándo queda disponible.**

### A-148 · Vías complementarias para el equipo docente

Siempre queda un caso que no se resuelve solo. Las tres son necesarias:

1. **Edición manual desde Pendientes.** Un campo por estudiante, con **validación en vivo** contra GitHub (uno de los pocos casos permitidos de consulta en vivo, A-089) y aviso inmediato si esa cuenta ya está asignada a otro. Requiere `mapeo.editar`.
2. **Importación CSV.** Columnas `canvas_user_id` (o `login_id`) y `github_login`. La pantalla muestra una **previsualización fila a fila** con el resultado de validación de cada una —qué se creará, qué se supersederá, qué fallará— **antes de aplicar nada**, y permite aplicar sólo las filas válidas. **Nunca se aplica a ciegas.**
3. **Reintento asistido.** Un botón envía un mensaje por Canvas a todos los que faltan, con el texto exacto de qué deben hacer y el enlace a la tarea de registro.

### A-149 · No se usa OAuth de GitHub del estudiante

Verificar la propiedad de la cuenta con un flujo de OAuth del estudiante sería **más fiable**, y aun así **se descarta**.

Motivo, y es de criterio 1, no de dificultad: el enunciado dice que «los estudiantes no serán usuarios de la aplicación: toda su interacción deberá realizarse a través de Canvas y GitHub». Un flujo con enlace, callback y página propia admite la lectura de que el estudiante **entra a la aplicación**, y **no se va a discutir esa lectura durante una evaluación**.

**La limitación se declara y se mitiga por tres caminos**, no se esconde:

1. La validación contra `GET /users/{login}` garantiza que la cuenta **existe y es una persona**.
2. La doble unicidad de A-079 impide que dos estudiantes reclamen la misma cuenta.
3. **La invitación de GitHub sólo la puede aceptar quien controla la cuenta**: un usuario mal escrito se detecta porque su invitación nunca se acepta, y eso aparece en Pendientes con nombre y apellido.

### A-150 · La pantalla Pendientes es la respuesta arquitectónica a R2.2.6

**No es un listado accesorio.** Es la primera pantalla que el docente ve al entrar a un curso con trabajo por hacer, tiene **contador en la navegación**, y lee **la misma tabla `incidencia`** que alimenta el estado de repositorios y el informe diario (A-088), de modo que **las tres vistas nunca se contradicen**.

Cuatro bloques, cada uno con recuento, exportación y **acción directa por fila**:

1. **Sin cuenta de GitHub** — `SIN_DATO`, `NO_RESUELTO`, `NO_EXISTE`, `ES_ORGANIZACION`. Acciones: escribir el usuario, enviar recordatorio por Canvas.
2. **Cuentas en conflicto** — `EN_CONFLICTO`, `INVALIDADO`, `LOGIN_REASIGNADO`, con las dos cuentas implicadas y el botón de resolución.
3. **Grupos incompletos** — grupos sin ningún integrante `accepted`, integrantes `invited`, estudiantes sin grupo, y dobles pertenencias (A-049).
4. **Invitaciones sin aceptar** — accesos `INVITADO` con más de 48 h, `EXPIRADA` y `DESAPARECIDA`. Acciones: reenviar, avisar por Canvas.

**Regla de diseño: ningún estado pendiente vive sólo dentro de una tarea.** Si algo bloquea un repositorio, aparece aquí. Y la cabecera del curso muestra siempre «N de M estudiantes con cuenta verificada», para que el equipo docente sepa de un vistazo si el enrolamiento va bien sin abrir nada.

**Secuencia recomendada al docente**, que la aplicación propone en pantalla con casillas porque el orden importa:

1. Vincular el curso y ejecutar el checklist.
2. Publicar la tarea de registro **y** un anuncio de curso explicando el proceso y por qué la invitación de GitHub es legítima.
3. Esperar 48 horas; revisar Pendientes.
4. Enviar el recordatorio a quien falte.
5. Crear la tarea y **dejar que los repositorios se creen solos** a medida que llegan los mapeos: **no hay que esperar al 100 %**, porque la creación es progresiva por diseño (**R2.3.10**).
6. Revisar las invitaciones sin aceptar a las 48 h de crearse los repositorios.

---

## 16. Interfaz, tiempo, idioma y vocabulario

### A-151 · Mapa de pantallas — ANULADA POR RG-127, RG-148 y RG-204 en su lista y en la fila de `/operacion`

> **Mandan ahora A-231** —el mapa gana **tres rutas públicas sin sesión**: `/invitaciones/{token}`, `/alcance` y `/privacidad`— y **A-232** —la fila de `/operacion` deja de decir «profesor» a secas: se acota a **los cursos donde el solicitante es PROFESOR ACTIVO**, y no existe vista global—. La **regla 0** y las tres reglas derivadas de §4 se conservan enteras, y la regla 2 pasa a hablar de **siete** máquinas (A-209).

§4 del enunciado dice que «las funcionalidades a las que no se puede acceder en el uso no se consideran cumplidas aunque estén en el código». **Toda funcionalidad de este documento tiene una pantalla, y ésta es la lista completa:**

| Pantalla | Ruta | Permiso | Contenido | Requisitos |
|---|---|---|---|---|
| Acceso | `/acceso` | — | Entrada con Google | R2.1.1, R2.1.2 |
| **Mi perfil** | `/perfil` | sesión | Nombre, correo, identidades de Canvas vinculadas, sesiones abiertas, **cerrar mi cuenta** | **R2.1.1** (A-165) |
| Mis cursos | `/cursos` | sesión | Cursos del usuario con su rol | R2.1.3 |
| Asistente de vinculación | `/cursos/nuevo`, `/cursos/{id}/vinculacion` | `curso.administrar` | Cuatro pasos y checklist de 19 ítems | R2.1.4–R2.1.6 |
| **Equipo** | `/cursos/{id}/equipo` | `curso.ver` para leer; `equipo.administrar` para actuar | **Listado de profesores y ayudantes con su estado, alta por invitación, edición de permisos, retiro y reincorporación, invitaciones pendientes y su revocación, historial de cambios** | **R2.1.1**, R2.1.7–R2.1.9 (A-165) |
| **Mis notificaciones** | `/cursos/{id}/mis-notificaciones` | **`curso.ver`** | **Mi** suscripción al informe diario y mis preferencias de aviso | **R2.6.3** (A-132) |
| Personas | `/cursos/{id}/personas` | `curso.ver` | Estudiantes, secciones, grupos, mapeo, tarea de registro, interruptor de `recordatorio_mapeo` | R2.2.1–R2.2.5 |
| **Pendientes** | `/cursos/{id}/pendientes` | `curso.ver` | Todo lo que falta, en un solo sitio | **R2.2.6** |
| Tareas | `/cursos/{id}/tareas` | `curso.ver` | Lista de tareas y su estado | R2.3.1 |
| Tarea | `/cursos/{id}/tareas/{id}` | `curso.ver`; acciones con `tarea.administrar` | Tablero, entregas, repositorios, repositorio base, comunicaciones, **sujetos activos y desactivados con su motivo** (A-164), **cierre y archivado** (A-168) | R2.3.2–R2.3.12, R2.4.1–R2.4.8, R2.5.1–R2.5.9, R2.6.5–R2.6.7 |
| Repositorio | `/cursos/{id}/tareas/{id}/repos/{id}` | `curso.ver` | Timeline y detalle | R2.5.10 |
| Corrección | `/cursos/{id}/correccion` | `correccion.corregir`; reparto con `correccion.asignar` | Bandeja del corrector, reparto y estado global | R2.7.1–R2.7.7 |
| Ajustes del curso | `/cursos/{id}/ajustes` | **`curso.administrar`** | Credenciales y su titular, revinculación, zona horaria, canal de comunicación activo, diagnóstico. **Ya no contiene la suscripción al informe** | R2.1.4, R2.1.5 |
| Operación | `/operacion` | profesor | Colas, límites, webhooks, trabajos periódicos, consumo de correo por reserva | — (defensa y demostración) |

**Comprobación explícita de que cada requisito tiene pantalla accesible por quien lo necesita.** La revisión 1 mapeaba **R2.6.1–R2.6.4** a `/cursos/{id}/ajustes`, que exige `curso.administrar`, permiso **NO CONCEDIBLE** a un ayudante: **R2.6.3** era inalcanzable para la mitad de sus destinatarios. Y no tenía ninguna pantalla que **administrara usuarios**, con lo que la mitad «administrar» de **R2.1.1** no se cumplía por su propia regla 1. Ambas cosas están corregidas arriba, y la regla que las gobierna se refuerza:

> **Regla 0 (nueva).** Una funcionalidad no está cubierta por tener pantalla: está cubierta cuando **la persona que el requisito nombra puede entrar en esa pantalla**. Si **R2.6.3** dice «profesores **y ayudantes**», la pantalla no puede exigir un permiso que un ayudante no puede tener. **Hay una prueba automatizada que recorre este mapa y comprueba, rol por rol, que cada requisito citado es alcanzable por los roles que el enunciado nombra.**

**Tres reglas que derivan de §4 del enunciado y que son de arquitectura, no de estilo:**

1. **Ninguna funcionalidad sin pantalla.** Si algo no tiene pantalla, no está hecho.
2. **Ningún estado interno sin representación.** Las seis máquinas de estado tienen sus estados visibles con nombre en español, no como código de error.
3. **Ninguna automatización invisible.** Cada trabajo que produce un efecto visible deja rastro consultable: la última sincronización con su hora, la bitácora de envíos, el historial de versiones y el panel de operación. **Un revisor puede comprobar que la creación progresiva de R2.3.10 ocurrió sola, en lugar de tener que creerlo.**

### A-152 · Tiempo: almacenamiento y presentación

- **Almacenamiento:** UTC, siempre (A-073).
- **Presentación:** la zona del curso, tomada de `Course.time_zone` (nombre IANA documentado, `Q-2.4-18`) al vincular y editable por el profesor; por defecto `America/Santiago` si Canvas no la entrega.
- **La conversión se hace con la zona del curso, no con la del navegador**, para que profesor y ayudante en husos distintos vean **la misma** fecha de cierre.
- **Y los trabajos periódicos por curso corren en la zona de ESE curso**, no en `America/Santiago` cableada: `informe_diario` a las 07:00 suyas y `recordatorio_mapeo` a las 09:00 suyas (A-114, A-130, A-131). La revisión 1 admitía cursos con otra zona y a la vez cableaba la de Chile en los dos trabajos, con lo que un curso con otra zona recibía su informe a una hora ajena a su propia regla.
- **El bucket diario de las métricas también es de la zona del curso**, y por qué eso no contradice A-073 está explicado en **A-171**.
- **Formato:** `dd-MM-yyyy HH:mm` con la **zona escrita al lado siempre**: `17-09-2026 23:59 (America/Santiago)`. **Nunca se muestra una hora desnuda.**
- Si `Course.time_zone` difiere de la zona configurada en el curso de la aplicación, la cabecera muestra una advertencia, porque significa que el docente y la aplicación podrían estar leyendo dos horas distintas para la misma fecha.
- Las **ventanas relativas** («últimas 24 h», «últimos 7 días») se calculan en UTC y se etiquetan con la fecha local equivalente.

### A-153 · Fechas de «todo el día»

**El disparo de la captura usa siempre `due_at` tal cual, como instante absoluto en UTC.** Nunca un fin de día derivado.

Motivo: la documentación **no** define que un cierre «todo el día» equivalga a 23:59:59, **no** da regla de redondeo, y `all_day`/`all_day_date` **ni siquiera están documentados como campos del objeto Assignment** —sólo constan en `CalendarEvent` y en `AssignmentOverride`— **[MEDIR]** (`Q-2.4-18`).

Si `all_day` llega y es `true`, **la interfaz muestra la hora exacta convertida y además la etiqueta «todo el día»**, sin ocultar la hora. **No se inventa un 23:59.**

### A-154 · Idioma y vocabulario cerrado

Toda la interfaz, los correos y los mensajes a estudiantes están en **español de Chile**, con tratamiento de «tú», registro profesional y **sin emojis**. Los textos viven en un único archivo de mensajes.

**El vocabulario es cerrado y no admite sinónimos en ninguna pantalla, ningún correo, ningún mensaje ni ningún nombre de tabla o de columna:**

| Se dice | Significa | No se dice |
|---|---|---|
| **Curso** | Curso de la aplicación, vinculado a uno de Canvas | clase, ramo, course |
| **Sección** | `Section` de Canvas | paralelo, section |
| **Conjunto de grupos** | `GroupCategory` colaborativa de Canvas | group set, categoría |
| **Grupo** | `Group` de una categoría colaborativa | equipo, group |
| **Estudiante** | Persona con matrícula de estudiante | alumno, student |
| **Tarea** | La agrupación con un único conjunto de repositorios (**R2.3.4**) | proyecto, assignment |
| **Entrega (parcial / final)** | Cada tarea de Canvas vinculada a una tarea (**R2.3.2**) | submission, deadline, hito |
| **Fecha de cierre** | Fecha efectiva aplicable a un sujeto | due date, plazo, vencimiento |
| **Versión de la entrega** | El estado inmutable del repositorio al cierre (**R2.4.5**) | snapshot, corte, foto, tag |
| **Repositorio / Repositorio base** | Repositorio de GitHub | repo del alumno, plantilla, template |
| **Cuenta de GitHub vinculada** | Correspondencia estudiante ↔ usuario de GitHub | mapeo, matching, linkeo |
| **Invitación · Aceptada · Pendiente** | Estado del acceso al repositorio | invite, pending |
| **Corrección · Publicar nota** | El trabajo de revisar y escribir la nota en Canvas | grading, push de notas |
| **Profesor / Ayudante** | Los dos roles de curso | admin, TA, staff, corrector |
| **Incidencia** | Problema que requiere atención del equipo docente | error, warning, alerta |
| **Informe diario** | El informe de **R2.6.1** | reporte, digest |
| **Sincronización · «Actualizado hace X»** | Traída de datos desde Canvas o GitHub | sync, refresh, job |

Los términos de Git que no tienen traducción asentada se dejan en inglés y en minúscula: *commit*, *push*, *branch*, *tag*, *merge*, *pull request*. Escribir «confirmación» por *commit* sólo confunde a quien va a mirar GitHub.

### A-155 · Estados traducidos, errores literales

- **Todo estado interno se muestra traducido, con etiqueta fija y la misma palabra en todas las vistas.** `ESPERANDO_INFORMACION` → «Falta información»; `ESPERANDO_LIMITE` → «Esperando a GitHub»; `CREADO_SIN_CONTENIDO` → «Creado, preparando contenido»; `OPERATIVO` → «Listo»; `CAPTURADA_SIN_TAG` → «Versión registrada (sin etiqueta en GitHub)»; `REVISAR` → «Versión registrada, requiere revisión». **Nunca aparece un identificador en mayúsculas en pantalla**, y nunca «OK» en una vista y «Completo» en otra.
- **Los identificadores técnicos que alguien debe copiar** —usuario de GitHub, nombre del repositorio, URL, SHA— **no se traducen ni se maquillan**: tipografía monoespaciada y botón de copiado.
- **Los mensajes de error de Canvas y de GitHub se muestran con su texto literal** en un bloque secundario, bajo una explicación en español de qué significa y qué hacer. **Ocultar el texto original haría indefendible el sistema en una revisión de código**, y es lo que permite diagnosticar en vivo lo que la documentación no cubre.

### A-231 · Tres rutas públicas entran en el mapa, y hay un solo componente de antigüedad

**1 · El mapa de pantallas de A-151 gana tres rutas sin sesión**, que la revisión 2 no inventariaba y que están en la lista cerrada de A-182:

| Pantalla | Ruta | Permiso | Contenido | Requisitos |
|---|---|---|---|---|
| **Aceptar invitación** | `/invitaciones/{token}` | **ninguno** (pública) | Rol, permisos que se conceden y **el texto literal del consentimiento de A-186** sobre el botón «Aceptar la invitación» | **R2.1.7**, **R2.1.8**, §3.1 |
| **Alcance** | `/alcance` | **ninguno** (pública) | La tabla de A-157 requisito a requisito, generada desde el catálogo de banderas (A-234) | §3.1, §4 |
| **Privacidad** | `/privacidad` | **ninguno** (pública) | Qué datos se tratan, con qué fin y cómo se dan de baja los avisos | **R2.6.3** |

**`/invitaciones/{token}` no es accesoria:** es **la pantalla donde el evaluador acepta su invitación** y donde vive el consentimiento de A-186, y **sin ella el paso 2 de A-166 no es ejecutable el 16 de septiembre**.

**2 · Todo dato espejado que se pinta en pantalla lleva su propio sello de antigüedad**, producido por **un único componente `SelloAntiguedad(sincronizado_en, techo_garantizado)`** que muestra «actualizado hace X · techo N», se pone **ámbar** cuando `ahora − sincronizado_en > techo` y **rojo** cuando lo dobla. El `techo_garantizado` **sale de la cadencia declarada del trabajo que lo escribe**: el de la actividad de GitHub es la fórmula de A-223; el de las submissions de Canvas, la cadencia de `reconciliar_notas_canvas`; el del roster y los grupos, la de su trabajo.

> **Ninguna pantalla escribe un número de antigüedad a mano**, y una prueba de interfaz falla si una pantalla pinta una antigüedad sin usar el componente. Con dos definiciones, **la misma pantalla puede mostrar dos antigüedades del mismo hecho**.

`techo_garantizado(entidad)` es una función pura de `backend/app/dominio/`. La antigüedad del contraste con Canvas sale de `estado_canvas_submission.sincronizado_en` (A-206), y no de una columna espejo en `correccion`.

### A-232 · `/operacion` tiene un solo inventario de secciones, y toda sección de curso está acotada

**1 · `/operacion`, `/operacion/invariantes`, todo `/api/operacion/**` y la forma completa de `GET /estado` sirven exclusivamente datos de los cursos en los que el solicitante tiene `membresia_curso` con `estado = ACTIVA` y `rol = PROFESOR`. No existe vista global.** Toda consulta de esos prefijos lleva **`curso_id IN (cursos del solicitante)` en el `WHERE`**, con la misma acotación que A-022 impone al resto del sistema.

- `POST /api/operacion/periodicos/{tipo}/ejecutar` y `POST /api/operacion/trabajos/{id}/reintentar` resuelven el `curso_id` del trabajo y responden **`404`, nunca `403`**, si no está en ese conjunto, **para no confirmar su existencia**.
- Un usuario **sin ninguna membresía `ACTIVA` de rol `PROFESOR`** recibe `404` en todo el prefijo, y **la entrada a `/operacion` no aparece en su navegación**.
- La dependencia `requiere_operacion()` resuelve ese conjunto y lo adjunta al contexto; entrar es el **caso 5 de `ACCIONES_SOLO_PROFESOR`** (A-179), y **la puerta 5 de A-174** falla la construcción si una consulta de sección de curso se registra sin la acotación.

**2 · `/operacion` es la única pantalla de estado del sistema, y su contenido es un solo inventario, con cada sección declarando si es de curso o de despliegue.**

**Secciones de CURSO —filtradas, sin excepción—:** colas y trabajos por estado y por motivo de cancelación (A-215); trabajos en `REQUIERE_ATENCION` con su error literal; últimos webhooks recibidos; última ejecución de cada uno de los **31** trabajos periódicos (A-218); **los cuatro cubos de `presupuesto_api`** —los tres de GitHub son por instalación y **toda instalación pertenece a un curso** (A-027, A-028), y el de Canvas es por curso— (A-219); la cola de etiquetas con su ritmo; **el techo de frescura calculado y su recuento** (A-223); los `403` de Canvas clasificados con su cuerpo literal; **las capacidades degradadas con su motivo y su fecha** (A-193); **los cerrojos tomados por proveedor** (A-217); los cursos con las lecturas de *rulesets* apagadas; la bandeja de mensajes retenidos y la cadena `reemplaza_a_id` (A-224, A-225); la cola de publicaciones detenidas (A-214); las violaciones de invariantes (A-181); y la fila de `DENEGACIONES_ANOMALAS` (A-177).

**Secciones de DESPLIEGUE —sin filtrar, y sólo éstas—:** consumo del día de la cuota de correo **por reserva** (A-228), latido del planificador, revisión de esquema desplegada, tamaño de la base y **bloque de rotación de claves** (A-191).

> **Por qué.** Un profesor que entra a `/operacion` **no puede ver el margen de límite de tasa, los cerrojos ni los errores literales de la organización de otro curso**; y el mismo dato mostrado en dos sitios con dos acotaciones distintas **es la forma más rápida de que una de las dos se quede vieja**.

**3 · Quien verifica en `/operacion` tiene que poder entrar.** El responsable de disponibilidad que firma la comprobación del primer informe diario real y **el titular de cada bandera que comprueba su criterio de aceptación** (A-233) **mantienen membresía `ACTIVA` de rol `PROFESOR` en el curso de demostración** durante todo el período. **Sin ella reciben `404` y la comprobación no es ejecutable.** Esa condición se anota en `.workflow/responsables.md` junto al nombre, y **la comprobación de arranque del ensayo del 14 de septiembre verifica que los titulares nombrados entran a `/operacion` sin `404`**.

**4 · Un trabajo cuya bandera no está retirada no se encola y no aparece como «vencido»** (A-218), para que la alerta de A-177 **no se dispare por diseño**.

`GET /api/operacion` devuelve las secciones **etiquetadas `CURSO` o `DESPLIEGUE`**, y **todo lo que muestra es dato medido y persistido, nunca una estimación escrita en el código**.

---

## 17. Reparto del alcance entre la entrega parcial y la final

### A-156 · El criterio de corte es el enunciado, no la comodidad

§3.1 nombra explícitamente el flujo que hay que demostrar el 16 de septiembre: **crear un usuario profesor → crear un curso → vincularlo con Canvas y GitHub → crear una tarea individual → creación automática de los repositorios asociados, incluido el proceso de asociación de los estudiantes con sus cuentas de GitHub**. Y evalúa **facilidad de uso y guía adecuada**.

**Todo lo que ese flujo toca debe estar completo y usable el 16 de septiembre, no esbozado.** Lo demás se construye con calidad plena entre el 17 de septiembre y el 6 de octubre.

**Enseñar un alcance recortado y consciente es mejor que enseñar cinco funciones a medias**, y en la demostración se dice con esas palabras qué queda fuera.

### A-157 · Tabla de alcance — ANULADA POR RG-147 y RG-148 en su lectura como lista de registro

> **Mandan ahora A-233 y A-234.** Esta tabla dice **qué requisito está completo en cada fecha**, y sigue siendo la fuente de la que se genera `/alcance`. Lo que queda superado es leerla como si dijera qué rutas y qué bloques están registrados: eso lo fija **la lista normativa única de A-233**, bandera por bandera, con fecha de retirada, titular, suplente y criterio de aceptación.

| Requisitos | Parcial · 16-sep | Final · 6-oct |
|---|---|---|
| **R2.1.1 – R2.1.6** (usuarios, curso, vinculación, checklist) | **Completo**, con **las 19 comprobaciones de A-041** y la administración de usuarios de **A-165** | Mejoras de guía y textos |
| **R2.1.7 – R2.1.9** (equipo, permisos, retiro) | **Completo**, con los nueve permisos de A-021, el retiro de A-025 y la revocación del acceso en GitHub de **A-163** | — |
| **R2.2.1, R2.2.2** (estudiantes, secciones) | **Completo** | — |
| **R2.2.3** (grupos) | Modelo y sincronización **completos y visibles en Personas**, sin uso todavía en tareas | **Completo**: tareas grupales |
| **R2.2.4 – R2.2.6** (mapeo y pendientes) | **Completo** para tareas individuales, con las cuatro vías de §15 | Ampliado a grupos |
| **R2.3.1 – R2.3.4** (tarea, entregas, modalidad, repositorio único) | **Completo** para modalidad **individual** y una sola entrega | Modalidad grupal y varias entregas parciales más la final |
| **R2.3.5, R2.3.6** (repositorio base y archivos) | **Completo**: creación del repositorio base y carga, reemplazo y borrado de archivos | Previsualización y árbol completos |
| **R2.3.7 – R2.3.11** (creación automática, nombres, accesos, estado) | **Completo**, incluida la materialización de sujetos de **A-164** y el acceso docente de **A-163** | Más estados, filtros y acciones masivas; archivado (**A-168**) |
| **R2.3.12** (avisar al estudiante por Canvas) | **Completo**: un mensaje **por integrante** al invitarlo a su repositorio (**A-127**, **A-130**) | Anuncio de curso y plantillas afinadas |
| **R2.4.1 – R2.4.4** (fechas, secciones, excepciones, actualización) | **Lectura y visualización** de la fecha base y de las fechas por sección; `fecha_efectiva` ya materializada | **Completo**: excepciones por estudiante y por grupo, detección de cambios por huella, aviso y reprogramación |
| **R2.4.5 – R2.4.8** (versiones) | **Fuera** — se dice explícitamente en la demostración | **Completo** |
| **R2.5.1 – R2.5.10** (seguimiento) | Sólo el **estado de creación y configuración de repositorios** (**R2.5.5**), que ya exige **R2.3.11** | **Completo** |
| **R2.6.1 – R2.6.4** (informe diario y correo) | **Fuera** | **Completo** |
| **R2.6.5** (mensajes por Canvas) | **Completo** en lo que exige **R2.3.12** | Ampliado a envío manual desde cualquier tabla |
| **R2.6.6, R2.6.7** (anuncios y automáticas) | **Fuera** | **Completo** |
| **R2.7.1 – R2.7.7** (corrección) | **Fuera** | **Completo** |

### A-158 · Lo que debe existir antes del 16 de septiembre aunque no se demuestre

Porque **no se puede retrofitear** sin migrar datos ya creados:

1. CI/CD completo y en verde (A-012), con `main` protegida.
2. Despliegue en Render y Vercel con dominio propio y certificados (A-004, A-008).
3. Base de datos definitiva creada, con **respaldo diario funcionando y una restauración ya probada** (A-005, A-016, **A-170**).
4. GitHub App registrada, con su marca y su **lista de permisos congelada tras medición** el 11-sep a las 20:00 (A-059, A-060, A-061), **incluido `Members: write`** del que depende A-163.
5. **`fecha_efectiva` materializada, `version_entrega` con su unicidad parcial, la tabla `incidencia`, `visibilidad_entrega`, `sujeto`, `sesion_membresia`, `identidad_canvas_usuario`, `equipo_github_curso` y `acceso_docente_repositorio`**, aunque las versiones no se capturen todavía. Añadirlas después obligaría a migrar y a reescribir la vista de estado, y **las cinco últimas sostienen requisitos que sin ellas no se cumplen**.
6. Motor de cola, planificador, bitácora, clasificación de errores y panel de operación (A-112, A-116, A-015).
7. **El equipo `docentes` creado y con lectura sobre los repositorios** (A-163): sin él, el 6 de octubre el corrector ve un `404` y no hay forma de retrofitearlo a 600 repositorios en una tarde.
8. **La regla de materialización de sujetos** (A-164) implementada en `backend/app/dominio/`, con sus pruebas. Es la entrada de todo el aprovisionamiento.
9. Las mediciones **RA-01 a RA-09**, **RA-25, RA-26 y RA-28** de §19 **ejecutadas y registradas** en `.workflow/mediciones/`. RA-09 se adelantó al 14-sep precisamente para que entre en esta lista.

### A-159 · Guion de la demostración del 16 de septiembre

**Se ensaya completo al menos dos veces**, la última el **14 de septiembre sobre producción**, con el conjunto de datos de demostración, cronómetro y guion escrito. **El ensayo incluye provocar deliberadamente dos fallos** —revocar el token de Canvas y agotar el presupuesto de GitHub— para ver las pantallas de fallo con calma. Duración objetivo: **12 minutos**.

| # | Paso | Requisitos | Tiempo |
|---|---|---|---|
| 1 | Entrar con una cuenta `gmail.com` nueva y crear el usuario profesor | R2.1.1, R2.1.2 | 30 s |
| 2 | Crear el curso: nombre, código, período, zona horaria | R2.1.3 | 30 s |
| 3 | Vincular Canvas: pegar el token y **elegir el curso de la lista** | R2.1.4 | 1 min |
| 4 | Vincular GitHub: instalar la App en la organización desde el botón | R2.1.5 | 1 min |
| 5 | Ejecutar el checklist y **mostrar deliberadamente un ítem en ámbar** y cómo se explica | R2.1.6 | 1,5 min |
| 6 | Incorporar un ayudante, concederle dos permisos, y **mostrar que no puede tocar las credenciales** | R2.1.7, R2.1.8 | 1 min |
| 7 | Ver Personas: estudiantes y secciones traídos de Canvas, con «actualizado hace X» | R2.2.1, R2.2.2 | 1 min |
| 8 | Mostrar la tarea de registro publicada en Canvas, **pulsar «sincronizar ahora» sobre una entrega preparada de antemano**, y ver aparecer el mapeo y el comentario de vuelta en la propia entrega de Canvas | R2.2.4, R2.2.5 | 2 min |
| 9 | Ver Pendientes con quien falta y enviar un recordatorio | R2.2.6 | 1 min |
| 10 | Crear una tarea individual vinculando un assignment; crear el repositorio base y subir dos archivos | R2.3.1–R2.3.6 | 2 min |
| 11 | Ver cómo **los repositorios se crean solos**, con el contador avanzando y sin pulsar nada más | R2.3.7–R2.3.11 | 1,5 min |
| 12 | Abrir un repositorio en GitHub, mostrar el nombre inequívoco, la invitación recibida y el mensaje que llegó por Canvas | R2.3.8, R2.3.9, R2.3.12 | 1 min |

**Reglas del ensayo, que son decisiones y no consejos:**

- **Si un paso necesita explicación verbal para entenderse, la pantalla está mal** y se corrige antes del 16, porque esa entrega evalúa explícitamente la facilidad de uso y la guía.
- El conjunto de datos de demostración se crea con un **guion versionado y reejecutable** (`infra/semilla_demo.py`) que incluye **al menos un caso con problema visible** —un estudiante sin cuenta declarada y una invitación sin aceptar—, porque **R2.3.11** exige mostrar los casos con información pendiente o problemas, y **una demostración enteramente en verde no demuestra ese requisito**.
- **Ninguna acción del guion depende de que un tercero haga algo en el momento**, y el paso 8 **ya no la contradice**. La revisión 1 pedía «entregar en vivo desde Canvas con una cuenta de estudiante» y tres párrafos después declaraba esta misma regla, además de que **la única identidad de estudiante que un profesor controla sin rol de administrador es el Test Student de Student View, que A-050 excluye del roster, del aprovisionamiento y de toda comunicación**: el paso central de la demostración no tenía actor viable. Corregido:

  > **La entrega del paso 8 está hecha de antemano en Canvas, con la matrícula de estudiante de prueba que se gestiona por RA-25, y en la demostración se dispara con el botón «sincronizar ahora», que encola el trabajo real.** Lo que se ve en pantalla es el recolector real leyendo una entrega real y respondiendo con un comentario real en Canvas: **es el flujo entero, no una simulación**, y lo único que no ocurre en vivo es el tecleo del estudiante, que no aporta nada a lo que se evalúa.

  **RA-25 — la matrícula de estudiante de prueba.** Se obtiene por dos caminos, en orden, **antes del 14 de septiembre**: (a) el titular intenta matricular a un integrante del equipo como estudiante del curso con `POST /courses/:id/enrollments`, lo que muchas instancias permiten a un profesor **[MEDIR]**; (b) si la instancia lo rechaza, **se solicita al administrador del curso por escrito**, y **se registra como riesgo con dependencia de un tercero con privilegios, junto a RA-01**. Si ninguno de los dos llega a tiempo, el paso 8 se demuestra sobre el **doble de A-167** en `ensayo`, **diciéndolo en voz alta**, que es infinitamente mejor que fingir. **En ningún caso se usa el Test Student**, que A-050 excluye y seguirá excluyendo.
- La demostración se ejecuta desde un **punto de acceso móvil propio**, no desde la red del aula, con la sesión ya iniciada en una pestaña de respaldo, y con el servicio **calentado 15 minutos antes**.
- Se lleva una **grabación de respaldo** hecha el 14 de septiembre. No sustituye la demostración en vivo: existe para el caso de una caída total de la red del recinto.

### A-160 · Cronograma hasta la entrega final, ordenado por riesgo

| Bloque | Fechas | Contenido |
|---|---|---|
| **Decisión de marca** | **10 de septiembre, 09:00** | Nombre del producto y dominio (§21, A-008, A-059). **Bloquea el registro de la GitHub App**, así que va primero |
| **Registro y prueba de permisos** | 10 → 11 de septiembre | GitHub App registrada con su nombre definitivo; pasadas A y B de RA-02 y RA-28; **congelación del conjunto de permisos el 11 a las 20:00** (A-061) |
| **Mediciones tempranas** | 12 → 14 de septiembre | RA-09 (adelantada), RA-25 (matrícula de estudiante de prueba), RA-26, RA-27. Todas antes de la parcial, con margen para rediseñar |
| **Bloque 1 — el de mayor riesgo técnico** | 17 → 23 de septiembre | Grupos y tareas grupales (**R2.2.3**, **R2.3.3**); múltiples entregas parciales y final (**R2.3.2**, **R2.3.4**); overrides por sección, por grupo y por estudiante, y fechas efectivas por sujeto (**R2.4.1**–**R2.4.4**); captura de versión con recaptura (**R2.4.5**–**R2.4.7**) y acceso directo a la versión (**R2.4.8**). Va primero porque concentra los `[MEDIR]` de `until`, orden e inclusividad |
| **Bloque 2** | 24 → 30 de septiembre | Ingesta por webhook, reconciliador y barrido; agregados diarios; tablero de tarea (**R2.5.1**–**R2.5.7**); comparación de participación (**R2.5.8**); métricas propias (**R2.5.9**); timeline por repositorio (**R2.5.10**) |
| **Bloque 3** | 1 → 5 de octubre | Informe diario, suscripción y envío (**R2.6.1**–**R2.6.4**); mensajes, anuncios y comunicaciones automáticas (**R2.6.5**–**R2.6.7**); asignación, navegación, rúbrica, publicación de notas y estado de corrección (**R2.7.1**–**R2.7.7**) |
| **Prueba de carga** | 25 de septiembre | 25 a 40 repositorios con 2 o 3 colaboradores y archivos base en una organización desechable, instrumentando cada respuesta, y borrado al terminar (§19, RA-12) |
| **Congelación** | **5 de octubre, 20:00 (Chile)** | Sólo correcciones de fallo con reproducción escrita |
| **Entrega** | 5 → 6 de octubre | Vídeo de 3 minutos, declaración de uso de IA, URL entregada por Canvas, código en GitHub |
| **Operación** | 6 → **31 de octubre** | Vigilancia diaria de las ~~cuatro~~ **cinco** alertas de A-015 —**ANULADA POR RG-143; manda A-177**— y de la cuota de correo del despliegue (A-228) |

### A-161 · Sostenimiento posterior a la entrega final

§3.2 exige la aplicación disponible **al menos dos semanas** después del 6 de octubre. Este documento compromete **hasta el 31 de octubre inclusive**, con margen, y lo sostiene con decisiones concretas y no con buena voluntad: base de datos que no caduca en esa ventana (A-005), servicios que no se suspenden (A-004), respaldo diario (A-016), comprobación automática de salud con alerta por correo (A-015) y congelación de despliegue (A-160).

### A-162 · Reglas de trabajo del equipo — ANULADA POR RG-079 y RG-190 en sus reglas 4 y 6

> **Mandan ahora A-194** —la regla 4 se refuerza: **ninguna llamada del diseño sin permiso cerrado queda fuera del plan de medición**, y el cruce endpoint a endpoint es el paso que autoriza la congelación— y **A-235** —la regla 6 gana su consecuencia escrita: la contradicción entre dos decisiones **se resuelve en una enmienda única a esta carta, previa a toda migración y a todo código nuevo**—. Las seis reglas se conservan enteras.

Derivadas de §3.3 y §4 del enunciado, que son requisitos de proceso **con consecuencias de nota**:

1. **Ninguna decisión de arquitectura la conoce una sola persona.** Cada sección de este documento tiene un responsable y un segundo capaz de defenderla. La actividad del 7 de octubre es individual y el descuento de hasta 3 puntos también.
2. **Nada entra a `main` sin revisión de otra persona**, y la revisión incluye la pregunta «¿podrías explicar esto el 7 de octubre?».
3. **Todo código generado con asistencia de IA se revisa, se prueba y se entiende antes de integrarse**, y se registra para la declaración de uso de IA que exige §3.2.
4. **Las mediciones empíricas de §19 se registran con fecha, comando y salida** en `.workflow/mediciones/`, y su resultado se refleja en este documento. **Una afirmación sobre una API sin medición ni cita no entra a la especificación.**
5. **Cada integrante debe poder explicar sin ayuda**, como mínimo: la regla de fecha efectiva (A-055), **quién es sujeto de una tarea y por qué se toma la unión de visibilidades** (A-164), por qué la evidencia es el SHA y no el tag (Ley 4, A-104), **cómo llega el ayudante a abrir un repositorio privado** (A-163), cómo se evita crear dos repositorios al mismo estudiante (A-097, A-115), qué pasa cuando GitHub limita (A-116, A-117), por qué el tablero carga instantáneo (Ley 1, A-119), y por qué el nombre del repositorio lleva el id de Canvas y el slug del curso (A-109, A-107).
6. **Regla de lectura cruzada, que es la que produjo la revisión 2.** Antes de responder una pregunta de alcance que toque **dos** decisiones, hay que leer las dos enteras y comprobar que no se contradicen. **Cincuenta y tres problemas de la revisión 1 eran invisibles dentro de su propia sección y evidentes al leer dos juntas.** Una contradicción encontrada **se escala con las dos citas `A-nnn` delante**; no se resuelve por cuenta propia (§0.3).

### A-233 · Catálogo cerrado de doce banderas de `PERFIL_ALCANCE`, y la lista normativa única de lo que existe el 16 de septiembre

**1 · `PERFIL_ALCANCE ∈ {parcial, completo}` gobierna un catálogo cerrado de doce banderas**, definido en `backend/app/infraestructura/alcance.py`, y **cada bandera tiene fecha de retirada, titular, suplente y criterio de aceptación**. **La retirada es una acción fechada con casilla, no una consecuencia de que alguien recuerde.** El titular y el suplente son los del bloque de A-160 que la entrega, nominados en `.workflow/responsables.md`, y **con membresía `ACTIVA` de rol `PROFESOR` en el curso de demostración** (A-232).

| # | Bandera | Capa | Qué habilita | Bloque | Retirada | Criterio de aceptación |
|---|---|---|---|---|---|---|
| 1 | `tarea_multientrega` | 3 | «Vincular otra entrega» y `POST …/entregas` a partir de la segunda | 1 | **23-sep 20:00** | La prueba de A-080 renumera `orden`, congela `entrega.slug` y el `409` desaparece |
| 2 | `tarea_modalidad_grupal` | 3 | Modalidad grupal y assignments grupales seleccionables | 1 | **23-sep 20:00** | A-138 filas 1 y 2 en verde; un repositorio de grupo llega a `OPERATIVO` |
| 3 | `fechas_excepciones` | 3 | Panel de excepciones por estudiante y por grupo | 1 | **23-sep 20:00** | `fecha_efectiva.origen` toma los cuatro valores en pantalla |
| 4 | `versiones_entrega` | 3 | Columna «estado de captura», tags y enlaces de **R2.4.8**; `resolver_sha`, `crear_etiqueta` y `precierre_actividad` | 1 | **23-sep 20:00** | Una captura real produce `CAPTURADA` con tag y la URL por SHA **abre para un ayudante** |
| 5 | `tarea_archivado` | 2 | Bloque «cierre de la tarea» con archivar y desarchivar (A-197) | 2 | **30-sep 20:00** | Archivar deja el repositorio en `ARCHIVADO` y la captura previa intacta; **un ayudante con `tarea.administrar` recibe `403`** |
| 6 | `tablero_actividad` | 2 | Bloques 3, 4 y 5 del tablero de A-119 | 2 | **30-sep 20:00** | El tablero pinta en < 400 ms p95 con 200 sujetos **y sin llamar a GitHub** |
| 7 | `repositorio_timeline` | 2 | Ruta `/cursos/{id}/tareas/{id}/repos/{id}` | 2 | **30-sep 20:00** | Las tres capas de A-124 con su catálogo cerrado de hitos |
| 8 | `ingesta_actividad` | 2 | Manejadores `push`/`create`/`delete`, `reconciliar_actividad`, `barrido_completo_actividad`, `agregar_metricas`, limitador del webhook | 2 | **30-sep 20:00** | **Relleno hacia atrás ejecutado y `ultimo_backfill_en` escrito en todos los repositorios** (A-221) |
| 9 | `mis_notificaciones` | 2 | `/cursos/{id}/mis-notificaciones`, `GET/POST /baja/{token}` y «regenerar mis enlaces» de `/perfil` | 3 | **3-oct 12:00** | La prueba de alcanzabilidad en modo `completo` confirma que **un ayudante entra** |
| 10 | `informe_diario` | 2 | Trabajo `informe_diario`, histórico y vista previa, botón «Enviarme el informe de hoy ahora» | 3 | **3-oct 12:00** | Informe generado con las cinco secciones de A-131 y **visible aunque el correo falle** |
| 11 | `comunicaciones_automaticas` | 3 | Los cinco interruptores de A-130 que no son `repositorio_disponible` ni `invitacion_aceptada` | 3 | **5-oct 12:00** | Los siete eventos con interruptor operativo, previsualización y recuento de destinatarios |
| 12 | `correccion` | 2 | Ruta `/cursos/{id}/correccion` (**R2.7.1**–**R2.7.7**) | 3 | **5-oct 12:00** | «Un ayudante sin `correccion.asignar` abre *Estado de la entrega* y ve la **matriz nominal completa** con los tres agregados y el doble contador; sobre una fila ajena ve *ver* y **no** puede abrir en modo edición ni leer el borrador, las notas internas o las banderas de otro corrector; *Repartir* no le aparece» (A-180) |

**Cuatro reglas de operación de la tabla, que no son consejos:**

- **La retirada de una bandera es un despliegue**, y su casilla vive en `docs/operacion.md` junto a la fecha y al titular.
- **Ninguna bandera se retira si su criterio de aceptación no está verde.** Si vence su fecha sin criterio verde, **se abre incidencia bloqueante y el bloque siguiente no empieza** hasta resolverla o hasta **declarar por escrito el recorte**.
- **El catálogo entero se elimina del código el 5 de octubre a las 12:00**, antes de la congelación de las 20:00, y su eliminación **la verifica la puerta 8 de A-174**.
- **`PERFIL_ALCANCE` no es estado del dominio y no vive en base de datos**, para que **no existan cursos con alcances distintos**.

**2 · Lista normativa ÚNICA de lo que existe el 16 de septiembre.** Toda otra sección remite a ella y **no repite el reparto**.

**Rutas registradas bajo `parcial`:** `/acceso`, `/perfil`, `/cursos`, `/cursos/nuevo`, `/cursos/{id}/vinculacion`, `/cursos/{id}/equipo`, `/cursos/{id}/personas`, `/cursos/{id}/pendientes`, `/cursos/{id}/tareas`, `/cursos/{id}/tareas/{id}`, `/cursos/{id}/ajustes`, `/operacion`, **`/invitaciones/{token}`**, **`/alcance`** y **`/privacidad`** (A-231).

**Rutas NO registradas bajo `parcial`** —una llamada directa responde **`404` de enrutado**, nunca un `500` ni una pantalla vacía—: `/cursos/{id}/mis-notificaciones`, `/cursos/{id}/tareas/{id}/repos/{id}`, `/cursos/{id}/correccion`, `GET|POST /baja/{token}`, `POST /api/perfil/regenerar-enlaces`, `POST /api/cursos/{id}/tareas/{id}/archivar` y `.../desarchivar`.

**Endpoints técnicos registrados en los dos perfiles:** `/auth/google/*`, `/auth/confirmar`, `/github/instalacion/callback`, `POST /webhooks/github`, `GET /api/invitaciones/{token}`, `POST /api/invitaciones/{token}/aceptar`, `GET /r/{t}`, `GET /salud`, `GET /estado`, `POST /interno/latido` y `GET /api/capacidades`.

**Bloques de `/cursos/{id}/tareas/{id}` registrados bajo `parcial`, y ninguno más:** (1) línea de entregas; (2) barra de estado de repositorios, con `OPERATIVO` y `DEGRADADO` **contados por separado**; (3) tabla completa de **R2.3.11** con estado traducido y motivo por fila; (4) repositorio base con carga, reemplazo, renombrado y borrado; (5) bloque «Comunicaciones» con los **siete** eventos de A-130, **dos operativos y cinco deshabilitados**. **No registrados:** bloques 3, 4 y 5 del tablero y el bloque «cierre de la tarea».

**Controles de capa 3 presentes y deshabilitados con motivo y fecha comprometida:** «Vincular otra entrega»; la modalidad grupal; la columna «estado de captura», sustituida por la nota «el registro de versiones al cierre llega el 6 de octubre»; el panel de excepciones; los cinco interruptores de A-130 de la final; y «regenerar mis enlaces de baja» en `/perfil`.

**Los siete interruptores de A-130 existen y se muestran en los dos perfiles.** Bajo `parcial` están operativos **exactamente dos**, `repositorio_disponible` e `invitacion_aceptada`, porque A-127 define **R2.3.12** como dos mensajes por Canvas y A-157 lo declara «Completo» el 16 de septiembre. Lo que sostiene **R2.2.5** ese día es el **botón manual** de Pendientes, con plantilla `recordatorio_mapeo_manual`, tope de 1 por estudiante y día y permiso `comunicacion.enviar`. **Es capa 3 y no capa 2: son acciones dentro de pantallas que sí existen.**

**3 · La prueba de alcanzabilidad se parametriza por perfil.** En modo `parcial` afirma dos cosas y sólo dos: que cada requisito de la columna «Parcial» de A-157 **es alcanzable por los roles que el enunciado nombra**, y que **cada ruta declarada no registrada devuelve `404` de enrutado**, es decir, **no existe a medias**. En modo `completo` afirma el mapa entero de A-151 y es **puerta de la entrega final**. **En ningún caso se resuelve un rojo registrando una pantalla a medias** (A-174 regla 2, A-156, §4 del enunciado).

Esta lista es el **dato de entrada** del registrador de rutas de FastAPI, de la **puerta 4** de A-174 y de la **puerta 6**. `GET /api/capacidades` devuelve `{perfil, banderas[]}` y es **la única fuente de la navegación del frontend**.

### A-234 · Régimen de `/alcance` y de la banda de cabecera, hasta el 31 de octubre

**La pantalla pública `/alcance` y la banda fija de la cabecera del curso se actualizan bloque a bloque y se retiran juntas, y su mantenimiento tiene dueño.**

1. **`/alcance` no es un documento estático: se genera.** Publica la tabla de A-157 requisito a requisito con **tres columnas** —requisito, qué se puede hacer hoy, cuándo llega lo que falta— y **su tercera columna se calcula desde el catálogo de banderas de A-233, no se teclea**. Una bandera retirada convierte automáticamente su fila en «disponible desde DD-MM-YYYY». **No existe una segunda lista que mantener a mano.**
2. **Se actualiza en el mismo despliegue que retira cada bandera**, y **el titular de la bandera responde de que su fila quedó bien**.
3. **La banda de la cabecera cambia de texto una vez por bloque.** Del 16 al 23 de septiembre dice literalmente: «Entrega parcial del 16 de septiembre. Esta versión cubre la creación del curso, la vinculación, el enrolamiento y la creación automática de repositorios. Ver el alcance completo.» Del 24 de septiembre al 5 de octubre: «Versión en construcción hacia la entrega final del 6 de octubre. Ver qué está disponible hoy.» **En los dos casos enlaza a `/alcance`.**
4. **La banda desaparece sola cuando no queda ninguna bandera activa**, el 5 de octubre a las 12:00. **No se retira a mano y no hay un interruptor para ocultarla.**
5. **`/alcance` no se retira: se congela.** Al eliminarse el catálogo el 5 de octubre a las 12:00, el generador **escribe una sola vez** la tabla resultante —todas las filas en «disponible», con su fecha— **en un fichero versionado** que `GET /api/alcance` sirve a partir de ese instante **sin depender del catálogo borrado**. La pantalla **queda accesible sin sesión hasta el 31 de octubre** (A-161, A-182), **porque es la evidencia de que el recorte del 16 de septiembre fue deliberado y declarado**, que es lo que A-156 obliga a decir en voz alta.

`/alcance` publica además **la fecha de inicio del histórico del informe diario** del curso (A-229). **Prueba automatizada:** con `PERFIL_ALCANCE=completo` y catálogo vacío, **ni la banda ni ninguna nota de capa 3 aparecen en ninguna pantalla**, y `/alcance` **sigue respondiendo `200`**.

### A-235 · La enmienda única a esta carta precede a toda migración y a todo código nuevo

**No se escribe ninguna migración ni se usa ningún código de incidencia, de trabajo, de estado, de motivo o de entidad nuevo hasta que esta carta incorpore la enmienda que consolida las cuatro partes del arbitraje.** Esa enmienda son las decisiones **A-174 a A-235** y las marcas de anulación de §0.6: **está incorporada y firmada con la revisión de este documento.**

**Orden obligatorio de los tres pasos, y no se altera:**

1. **Incorporar la enmienda a `docs/ARQUITECTURA.md`** —A-088 con 51 tipos, A-030 con nueve eliminaciones externas, §8 con 70 entidades, A-114 con 31 trabajos, A-092 con `INACCESIBLE`, A-099 con diez valores, A-105 con ocho estados y diez motivos de no publicable, A-133 como cuota del despliegue con tres reservas, A-169 con seis escrituras síncronas, A-041 con 19 ítems más dos pruebas de escritura y cinco resultados, y §9 con siete máquinas—.
2. **Declarar en `backend/app/dominio/estados.py` TODOS los enumerados** (A-209) y en **`backend/app/dominio/censo.py` las 70 entidades** (A-198).
3. **Escribir una sola migración, anterior al 16 de septiembre**, con las 70 tablas, todas las columnas y todos los valores de catálogo (A-175).

> **Por qué una sola y no tres parciales.** «Catálogo cerrado» **sólo funciona como criterio de revisión de código si el cierre lo firma alguien que ha visto todas las dimensiones**. Tres enmiendas parciales, cada una declarándose única, producen **tres cifras y tres `CHECK` incompatibles en la misma migración**.

**Ninguna de las cuatro partes del arbitraje queda derogada:** las tres primeras siguen siendo la ley de su dimensión, **leídas con las correcciones que la parte 4 dicta**, y esta carta manda sobre las cuatro. **Añadir un valor a cualquier catálogo cerrado de este documento —tipos de incidencia, acciones de bitácora, motivos, estados, trabajos, entidades, eliminaciones externas, rutas sin sesión, acciones cerradas por rol o secretos— es una decisión que se registra aquí, y sólo aquí.**

---

## 18. Contradicciones entre los borradores, y qué se decidió

Los tres borradores discreparon en trece puntos. **Aquí está la decisión y el motivo, en una línea cada uno.** Ningún agente debe reabrirlos.

| # | Punto en disputa | Decisión | Por qué |
|---|---|---|---|
| 1 | Base de datos: Supabase / Neon | **Supabase Free** (A-005) | Neon se descarta por el tope de 100 CU-hours con un planificador que nunca deja dormir el compute; su arranque en frío no era el problema |
| 2 | Un solo proceso web con planificador dentro, o web + *worker* | **Dos procesos desde la misma imagen** (A-003) | Un trabajador saturado no debe degradar la interfaz que el evaluador está mirando; con plan de pago el *worker* está disponible |
| 3 | Sesión: cookie *same-site* o *bearer* JWT | **Cookie opaca con dominio propio**, con el *bearer* como contingencia fechada (A-009, A-010) | Permite revocación inmediata al retirar a un ayudante (**R2.1.9**) y elimina el problema de cookies de terceros por construcción |
| 4 | Estudiantes: colaboradores de repositorio o miembros de la organización | **Colaboradores de repositorio** (A-064) | La vía de organización depende de una tensión documental sin resolver sobre si hace falta ser *owner*, y **abre un agujero de privacidad** que exige leer `default_repository_permission`, campo que puede no ser legible con token de instalación |
| 5 | Prueba de escritura en el checklist: sí o no | **Sí, opcional y con `delayed_post_at`** (A-042) | **R2.1.6** pide verificar que la configuración es correcta, y el endpoint de permisos por documentación propia no lo garantiza; se hace con consentimiento explícito, con borrado inmediato y limpieza de huérfanos, y **nunca con `published=false`**, que no está documentado |
| 6 | Colisión de nombre de repositorio: sufijo `-2` o no | **Nunca sufijo** (A-111) | Un sufijo destruye la inequivocidad que exige **R2.3.8**; como el nombre lleva el id de Canvas, la colisión sólo puede ser reintento (se adopta) o anomalía (incidencia) |
| 7 | Parte legible del nombre: login de GitHub o apellido-nombre | **Apellido-nombre** (A-109) | El login puede cambiar y **el antiguo queda libre para que otro lo reclame**; como el nombre del repositorio no cambia nunca, un login incrustado puede acabar designando a otra persona |
| 8 | Nombre del tag: `entrega/<slug>` o con número de versión | **`entrega/<orden>-<slug>/v<n>`** (A-104) | Una recaptura no debe obligar a reescribir un tag ya enviado a los correctores; reescribir un tag es borrarlo y crearlo |
| 9 | Selección del commit de cierre: sólo GitHub o doble fuente | **Doble fuente con estado `REVISAR`** (A-102) | La semántica de `until` y el orden de retorno no están documentados; contrastar espejo y API es lo único defendible sin apoyarse en un supuesto |
| 10 | Grupo con integrantes sin confirmar: crear repositorio o esperar | **Se crea con al menos un `accepted` con mapeo vigente** (A-048, A-093) | Esperar al 100 % dejaría cojo **R2.3.10**, que exige crear *progresivamente a medida que se disponga* de la información |
| 11 | Doble pertenencia a grupos: bloquear al estudiante o a los grupos | **Se bloquean los dos grupos implicados** (A-049) | No se puede saber cuál debe recibir a esa persona, y crear uno de los dos repositorios sería adivinar |
| 12 | Estudiante en dos secciones con fechas distintas: elegir o no elegir | **Se toma la más tardía y se marca ambigua, con incidencia** (A-046, A-055) | No elegir dejaría al estudiante sin fecha de captura y **R2.4.5** quedaría cojo; capturar antes de tiempo destruiría trabajo legítimo, capturar después sólo añade trabajo visible |
| 13 | OAuth de GitHub del estudiante: opcional desactivado o descartado | **Descartado** (A-149) | El enunciado dice que los estudiantes no serán usuarios de la aplicación; no se va a discutir esa lectura durante una evaluación |

Además, este documento **se aparta del estudio interno** (`docs/estudio-apis-canvas-github.md`) en cuatro puntos concretos, todos con motivo documentado: el disparador de fechas no es `assignment.updated_at` (A-056); el tope de commits del payload de `push` es 2048 y no 20 (A-071); `per_page=100` no se escribe como hecho (A-039); y el filtro del roster va por `type[]`, nunca por `role[]` (A-043).

### Contradicciones INTERNAS de la revisión 1, y cómo quedan resueltas

Las trece de arriba eran discrepancias entre borradores. Éstas son distintas y más graves: **eran dos frases del mismo documento definitivo que no podían ser verdad a la vez.** Se resuelven aquí y **ningún agente debe reabrirlas**.

| # | Las dos frases que chocaban | Cuál cede | Decisión resultante |
|---|---|---|---|
| 14 | A-027 «la organización SÍ puede compartirse entre cursos» vs. A-028 y A-075, que imponen `installation_id` y `curso_id` únicos | **Cede A-027**: una GitHub App tiene una sola instalación por organización | **Una organización pertenece a exactamente un curso** (A-027), y el nombre usa `curso.slug` de todos modos (A-107) |
| 15 | A-004 descarta «el plan gratuito con un pinger externo» vs. A-112 instituye un *workflow* que golpea `/interno/latido` cada 10 min | **Ninguna: no eran lo mismo**, y la revisión 1 no lo decía | A-112 es un **vigilante externo que comprueba y alerta**, no un pinger que mantiene vivo; A-004 lo declara explícitamente |
| 16 | A-039 «una sola petición simultánea por curso» vs. A-115 garantía 5, cerrojo por `(tipo, curso_id)` | **Cede A-115**: implementaba lo contrario de lo que decía cumplir | **Cerrojo por `curso_id` a secas en todo trabajo que hable con Canvas**; `(tipo, curso_id)` sólo para los de GitHub (A-115) |
| 17 | A-096 sondea hasta 45 veces por repositorio vs. A-117 promete 200 sujetos en 10 min bajo el 50 % de 12 500/hora | **Cede A-096**, y A-117 recalcula | **Retroceso 2→5→10→30 s con tope de 8 sondeos** (A-096), coste por repositorio desglosado y ritmo a 1 cada 6 s (A-117) |
| 18 | `precierre_actividad` «T−2 min, por `(entrega, sujeto)`» vs. el presupuesto de A-117 | **Cede A-114** | **Por repositorio, repartido en los 15 min previos** (A-114) |
| 19 | A-090 «por debajo de 250 MB» vs. `evento_webhook.payload` completo con retención de 30 días y payloads de hasta 25 MB | **Cede A-090**, cuya aritmética estaba mal | **Truncado a 64 KB, retención de 7 días, freno automático a 300 y 400 MB** (A-090) |
| 20 | A-030 «la aplicación no borra nada» vs. A-042, A-067, A-100 y A-113, que borran | **Cede el título de A-030**, que era falso | **«No borra datos propios de dominio»**, con la lista cerrada de seis eliminaciones externas (A-030) |
| 21 | A-023 `sesion.version_membresias` escalar vs. A-020 «una persona puede ser profesora de un curso y ayudante de otro» | **Cede A-023**: un escalar no representa N versiones | **Tabla `sesion_membresia`, comprobación por membresía** (A-023) |
| 22 | A-033 regla 2 comparada contra una columna vacía en el primer pegado, y «ya no cambia» vs. A-051 | **Cede A-033** | **`identidad_canvas_usuario` por instancia, y la comprobación real es la matrícula de profesor en el curso vinculado** (A-033) |
| 23 | A-035 guarda tokens de varios profesores vs. la API Policy que A-033 cita | **Cede la redacción de A-035**, no el mecanismo | **Cada titular pega sólo el suyo, con consentimiento escrito, visibilidad de uso y retirada propia** (A-035) |
| 24 | A-152 «la zona del curso» vs. A-131 «07:00 America/Santiago» y A-130 «09:00 Chile», cableados | **Ceden A-130 y A-131** | **Todo trabajo por curso corre en la zona de ese curso** (A-114, A-130, A-131, A-152) |
| 25 | A-125 «ninguna vista escribe hacia fuera» vs. A-042, A-066, A-067, A-144 | **Cede A-125**, que dejaba cuatro requisitos sin implementación legal | **A-169: seis escrituras síncronas enumeradas, con contrato**; A-125 pasa a hablar de **comunicaciones**, que son otra cosa |
| 26 | A-139 itera por integrante «para saber quién quedó publicado» vs. su propia cita, que dice que Canvas propaga a los N | **Cede A-139** | **Una escritura por grupo, verificación por integrante con la lectura masiva de A-142** (A-139) |
| 27 | A-048 «DEGRADADO» vs. la tabla de A-092, que daba `OPERATIVO` | **Cede la tabla de A-092**, y la expresión «todos los integrantes» desaparece | **Predicado de `OPERATIVO` escrito entero, con motivos cerrados de `DEGRADADO`** (A-092) |
| 28 | A-061 congela permisos tras probar el 10-11 vs. §21, que decidía el nombre el 12 | **Cede §21** | **Nombre y dominio el 10-sep a las 09:00**, con el calendario completo en A-061 |
| 29 | A-159 paso 8 «entregar en vivo con una cuenta de estudiante» vs. su propia regla del ensayo y vs. A-050 | **Cede el paso 8** | **Entrega preparada + sincronización manual**, con RA-25 para la matrícula de prueba (A-159) |
| 30 | A-133 reparte 100 correos entre informe y suscriptores vs. A-015, A-007 y A-036, que también envían | **Cede A-133** | **60 informe / 20 operativo / 20 margen, con orden de cesión escrito** (A-133) |
| 31 | §0.4 criterio 1 vs. A-143, que preaprobaba degradar **R2.7.6** | **Cede A-143**: la carta no puede autorizar lo que su regla de oro prohíbe | **Plan alternativo que sigue cumpliendo R2.7.6** y medición adelantada al 14-sep (A-143) |
| 32 | A-162 regla 4 «ninguna afirmación de API sin medición ni cita» vs. el límite de 100 caracteres de A-108, afirmado sin ninguna de las dos | **Cede A-108** | **Marcado `[MEDIR]` (RA-26), con techo propio de 90 que hace el diseño independiente del número** (A-108) |
| 33 | A-107 `<slug-tarea>` «≤ 20» vs. A-108 paso 6, que truncaba a 24 | **Cede A-107** | **24 en los dos sitios** (A-107, A-108) |

---

## 19. Riesgos abiertos que este documento reconoce

Cada riesgo lleva **responsable implícito, fecha límite y —esto es lo que lo convierte en riesgo gestionado y no en esperanza— qué hace la aplicación si la medición sale mal.**

| Id | Riesgo abierto | Origen | Fecha | Qué pasa si sale mal |
|---|---|---|---|---|
| **RA-01** | **Bloqueante.** La instancia institucional de Canvas y el token de profesor deben estar operativos; Free-for-Teacher ya no existe | `Q-infraestructura-08`, `Q-infraestructura-09` | **10-sep** | Sin instancia no hay demostración ni ensayo: se escala al profesor del ramo de inmediato. **Es el riesgo número uno del proyecto** |
| **RA-02** | El conjunto mínimo de permisos de `/generate` y `/git/refs` no está fijado: la marca «Additional permissions» es ambigua por diseño | `Q-2.1-32`, `Q-infraestructura-14` | **11-sep** | Se instalan todos los permisos candidatos **antes del 16-sep**; añadirlos después obliga a re-aprobación de cada instalación (A-061) |
| **RA-03** | No está documentado que la API avise cuando recorta el roster por profesor limitado a sección | `Q-2.1-28` | 12-sep | Ya mitigado: bloqueo en el checklist leyendo el flag (A-052) y regla anti-bajas-masivas (A-045) |
| **RA-04** | No está documentado si la copia tras `/generate` es asíncrona ni qué códigos transitorios aparecen | `Q-2.3-19` | 12-sep | Ya mitigado: sondeo acotado de 90 s y resolución diferida al reconciliador; **nunca produce error** (A-096) |
| **RA-05** | No está fijado si el token del profesor ve el correo del estudiante, ni por qué ruta | `Q-2.2-32` | 15-sep | Desaparece la regla 3 de atribución (A-118) y la importación CSV por correo; la clave sigue siendo `canvas_user_id` |
| **RA-06** | No está documentado si `type[]=StudentEnrollment` devuelve roles personalizados derivados | `Q-2.1-29` | 15-sep | Se puebla `curso.roles_estudiante_extra`; el modelo ya lo admite sin migración (A-043) |
| **RA-07** | No está documentado si el `body` de Conversations se interpreta como HTML, si autoenlaza URLs, ni su longitud máxima | `Q-2.3-55`, `Q-2.6-03` | 15-sep | Ya mitigado: plantilla en texto plano con URLs completas en línea propia (A-126) |
| **RA-08** | La cobertura de `include[]=group_ids` frente a las categorías reales no está documentada | `Q-2.2-43` | 15-sep | Ya mitigado: la fuente autoritativa es `group_categories → groups → memberships`; `group_ids` sólo se usa como contraste (A-043, A-047) |
| **RA-09** | **Crítico.** No está documentado si se puede publicar nota sobre una submission `unsubmitted` de un assignment con `submission_types=none` | `Q-2.7-38` | **14-sep** (adelantada desde el 20-sep: con fecha 20 quedaba **después** de la parcial y sin margen para rediseñar) | **Plan alternativo que SÍ cumple R2.7.6**: ajuste consentido de `submission_types` en un clic, con previsualización, igual que A-144 crea un assignment (A-143). **La degradación declarada de la revisión 1 queda retirada por violar §0.4 criterio 1** |
| **RA-10** | Semántica de `until` en `GET /commits`: inclusividad en el segundo exacto, fecha de autor o de *committer*, y orden de retorno | `Q-2.4-22` | 19-sep | Ya mitigado: doble fuente con estado `REVISAR` y regla de corte escrita (A-102). Un desacuerdo sistemático obligaría a mover la captura a GraphQL |
| **RA-11** | No está documentado si crear, editar o borrar un override toca `assignment.updated_at` | `Q-2.4-10` | 19-sep | Ya mitigado: comparación por huella del conjunto completo (A-056) |
| **RA-12** | Coste real de un ciclo de reconciliación y límites secundarios de GitHub no consultables | `Q-2.5-08`, `Q-3.2-3.3-4-13` | 25-sep | Ya mitigado por ritmo conservador (A-117); la prueba de carga convierte la estimación en un número |
| **RA-13** | Varios equipos evaluados el mismo día contra la misma organización o el mismo curso pueden compartir cuotas no documentadas | `Q-transversal-39` | no cerrable | Ya mitigado: estado transitorio explícito, distinguible de un error, con hora de reintento visible (Ley 5, A-116) |
| **RA-14** | Rechazo y expiración de una invitación de GitHub son indistinguibles; no hay número de días de expiración publicado | `Q-2.3-30` | 20-sep | Ya mitigado: el estado se llama `DESAPARECIDA` y la interfaz dice «rechazada o caducada» (A-100) |
| **RA-15** | Una cuenta recién creada sin correo verificado puede no poder aceptar la invitación; el 2FA obligatorio de la organización bloquea aceptaciones | `Q-2.3-33`, `Q-2.1-39` | 20-sep | Subtipos `ORG_EXIGE_2FA` y `CUENTA_BLOQUEADA_POR_ORG` (A-098); el anuncio inicial advierte de verificar el correo antes |
| **RA-16** | Períodos de calificación cerrados, matrículas inactivas y propagación de rúbrica en grupos | `Q-2.7-63`, `Q-2.7-64`, `Q-2.7-37` | 1-oct | Ya mitigado: pre-chequeo y estado `NO_PUBLICABLE` (A-140); iteración por integrante (A-139); se coordina que el período esté abierto el 6-oct |
| **RA-17** | Que `late_policy_status=none` elimine una deducción **ya aplicada** es una inferencia, no una frase documentada | `Q-2.7-67` | 1-oct | Ya mitigado: relectura obligatoria y estado `PUBLICADA_CON_ADVERTENCIA` (A-140) |
| **RA-18** | Los tags de entrega son borrables: sin plan de pago no hay rulesets en repositorios privados | `Q-infraestructura-22` | resuelto | Ya mitigado por diseño: la evidencia es el SHA en base con respaldo diario (Ley 4, A-104, A-016) |
| **RA-19** | Capacidad, caducidad y límite de conexiones de la base de datos en la ventana 10-sep → 31-oct | `Q-infraestructura-34` | 13-sep | Ya mitigado: elección de proveedor, tope propio de conexiones, vigilancia de tamaño y respaldo (A-005, A-007, A-016) |
| **RA-20** | El cupo de 100 correos diarios del proveedor puede quedarse corto | `Q-infraestructura-28` | 28-sep | Ya mitigado: tope de 60 envíos y 30 suscriptores, encolado y el informe siempre disponible en la aplicación (A-133) |
| **RA-21** | Toda calificación aparecerá firmada por el profesor, no por el ayudante que corrigió | `Q-2.7-49` | asumido | Pérdida real de trazabilidad **dentro** de Canvas, compensada por tres vías (A-142). No es resoluble sin rol de administrador |
| **RA-22** | Fusión de usuarios en Canvas destruye el `canvas_user_id` y no hay señal utilizable en la API | `Q-2.2-30` | 26-sep | Ya mitigado hasta donde se puede: incidencia con confirmación humana (A-051). Es lo mejor disponible, no una solución |
| **RA-23** | Los valores literales del campo `type` del objeto usuario de GitHub no están impresos en la documentación | `Q-2.3-66` | 15-sep | Ya mitigado: la detección de organización compara `GET /users/{login}` con `GET /orgs/{login}` (A-091) |
| **RA-24** | **De calendario.** Siete días hasta la parcial y tres semanas más hasta la final, con mediciones pendientes que exigen instancia de Canvas y organización de GitHub operativas | — | continuo | El Bloque 1 de A-160 concentra el riesgo; la congelación del 5-oct es innegociable |
| **RA-25** | **Bloqueante para el paso 8 del guion, y depende de un tercero con privilegios.** No hay identidad de estudiante que un profesor controle sin rol de administrador: el Test Student está excluido por A-050 | §1.1, A-050 | **14-sep** | (a) Se intenta `POST /courses/:id/enrollments` con el token del profesor **[MEDIR]**; (b) si falla, se solicita la matrícula al administrador **por escrito, junto a RA-01**; (c) si no llega, el paso 8 se demuestra sobre el doble de A-167 **diciéndolo en voz alta**. **Nunca con el Test Student** (A-159) |
| **RA-26** | El límite de longitud del nombre de repositorio de GitHub **no está en `preguntas-averiguables-resueltas.md`**: la revisión 1 lo afirmaba como 100 caracteres sin marca, sin `Q-…` y sin cita, violando la regla 4 de A-162 en el punto que sostiene toda la convención de nombres | — (hueco documental propio) | 11-sep | **Ya mitigado por diseño**: el techo propio es **90 caracteres y el peor caso construible es 86** (A-108 paso 11), de modo que el diseño no depende del número real. La medición —crear un repositorio de 100 y otro de 101 caracteres en la organización de `ensayo`— sólo confirma el margen |
| **RA-27** | **`ensayo` puede no tener curso de Canvas propio**, porque §1.1 impide crear cursos por API y el equipo recibe uno solo | §1.1 | **12-sep** | **Ya mitigado**: A-167 implementa el doble de pruebas del `ClienteCanvas` con respuestas grabadas y anonimizadas, que no depende de nadie. El segundo curso se solicita igualmente; si llega, `ensayo` conmuta por configuración sin tocar el diseño |
| **RA-28** | **`Members: write` de la GitHub App**, del que depende la vía principal de A-163, entra en el conjunto de permisos y hay que probarlo con el resto | `Q-2.1-32`, `Q-infraestructura-14` | **11-sep**, con RA-02 | **Ya mitigado**: la vía de respaldo —colaborador individual con `permission=pull`— está **cerrada por documentación** bajo `Administration: write`, permiso que la App ya tiene **[DOC]** (`Q-infraestructura-14`). El ítem 18 del checklist declara cuál quedó activa (A-163) |
| **RA-29** | **El evaluador podría no facilitar una dirección `gmail.com`**, y A-018 rechaza por diseño los correos con reclamación `hd` | §3.1, A-018 | **2-oct** | **Ya mitigado**: A-166 prepara una cuenta `gmail.com` del equipo, ya incorporada al curso y al equipo de GitHub, entregada por Canvas y declarada como vía de acceso. El rechazo de `hd` **no se relaja**: lo exige **R2.1.2** |

**Riesgos que la revisión 1 no registraba porque no había detectado el problema:** RA-25, RA-26, RA-27, RA-28 y RA-29. Los cinco salieron de la revisión adversarial, y los cinco están mitigados por decisiones escritas, no por confianza.

---

## 20. Trazabilidad: requisito → decisiones

| Requisito | Decisiones que lo sostienen |
|---|---|
| **R2.1.1** | A-017, A-018, A-020, A-021, **A-165**, **A-178**, **A-185** |
| **R2.1.2** | A-018, A-019, A-075, **A-182**, **A-183**, **A-185**, **A-189** |
| **R2.1.3** | A-026, A-027, A-040, **A-197** |
| **R2.1.4** | A-031, A-033, A-034, A-039, A-040, **A-176**, **A-188**, **A-191** |
| **R2.1.5** | A-057, A-058, A-063, A-040, A-027, **A-176**, **A-191**, **A-192**, **A-194**, **A-195** |
| **R2.1.6** | A-040, A-041, A-042, A-052, A-053, **A-169**, **A-192**, **A-193**, **A-226** |
| **R2.1.7** | A-020, A-021, A-024, **A-165**, **A-178**, **A-179**, **A-181**, **A-184**, **A-185**, **A-186**, **A-187**, **A-188** |
| **R2.1.8** | A-021, A-022, A-023, A-024, **A-165**, **A-178**–**A-190**, **A-197**, **A-232** |
| **R2.1.9** | A-009, A-023, A-025, A-030, **A-163**, **A-165**, **A-181**, **A-183**, **A-187**, **A-188**, **A-190**, **A-212** |
| **R2.2.1** | A-043, A-044, A-045, A-050, A-051, A-114, **A-193**, **A-218** |
| **R2.2.2** | A-043, A-044, A-046, A-076, **A-193**, **A-219** |
| **R2.2.3** | A-047, A-048, A-049, **A-204**, **A-212** |
| **R2.2.4** | A-074, A-077, A-078, A-079, A-091, A-144, A-145, **A-041** ítem 16, **A-169**, **A-184**, **A-187**, **A-201**, **A-210** |
| **R2.2.5** | A-091, A-144, A-146, A-147, A-148, **A-041** ítem 16, **A-187**, **A-201**, **A-210**, **A-233** |
| **R2.2.6** | A-088, A-094, A-150, **A-164**, **A-184**, **A-187**, **A-207**, **A-209**, **A-210** |
| **R2.3.1** | A-080, A-151, **A-203**, **A-207** |
| **R2.3.2** | A-080, A-081, **A-203** |
| **R2.3.3** | A-080, A-081, **A-138**, **A-203** |
| **R2.3.4** | A-081, A-084, **A-164**, **A-204**, **A-211** |
| **R2.3.5** | A-066, A-080, **A-169**, **A-194**, **A-208**, **A-226** |
| **R2.3.6** | A-067, **A-169**, **A-194**, **A-208**, **A-226** |
| **R2.3.7** | A-066, A-068, A-092, A-096, A-097, **A-164**, **A-192**–**A-194**, **A-196**, **A-202**, **A-208**, **A-211** |
| **R2.3.8** | A-027, A-069, A-097, A-107–A-111, **A-194**, **A-202**, **A-211** |
| **R2.3.9** | A-064, A-065, A-099, A-100, **A-185**, **A-190**, **A-211**, **A-212**, **A-221** |
| **R2.3.10** | A-092, A-093, A-112, A-114, A-117, **A-164**, **A-190**, **A-202**, **A-211**, **A-212**, **A-219** |
| **R2.3.11** | A-088, A-092, A-094, A-098, A-116, A-155, **A-163**, **A-164**, **A-197**, **A-202**, **A-207**–**A-212**, **A-221**, **A-230** |
| **R2.3.12** | A-125, A-126, A-127, **A-130**, **A-041** ítems 6 y 17, **A-193**, **A-212**, **A-216**, **A-224**, **A-227** |
| **R2.4.1** | A-054, A-055, A-080, **A-193**, **A-203** |
| **R2.4.2** | A-046, A-055, A-082, **A-193**, **A-220** |
| **R2.4.3** | A-054, A-055, A-082, **A-193**, **A-220** |
| **R2.4.4** | A-056, A-103, A-130, **A-193**, **A-203**, **A-204** |
| **R2.4.5** | A-082, A-101, A-102, A-114, **A-164**, **A-175**, **A-197**, **A-203**, **A-204**, **A-213**, **A-218**, **A-220** |
| **R2.4.6** | A-081, A-084, A-101, **A-172**, **A-204**, **A-213**, **A-218** |
| **R2.4.7** | A-085, A-101, A-103, A-104, **A-172**, **A-197**, **A-200**, **A-202**–**A-204**, **A-213**, **A-230** |
| **R2.4.8** | A-104, A-136, **A-163**, **A-041** ítem 18, **A-186**–**A-188**, **A-190**, **A-192**, **A-197**, **A-213**, **A-230** |
| **R2.5.1** | A-119, A-086, **A-217**, **A-223**, **A-232** |
| **R2.5.2** | A-070, A-071, A-072, A-086, **A-171**, **A-182**, **A-196**, **A-205**, **A-217**, **A-221**–**A-223** |
| **R2.5.3** | A-121, A-123, **A-171**, **A-205**, **A-211**, **A-221**, **A-222** |
| **R2.5.4** | A-118, A-120, A-121, **A-164**, **A-171**, **A-196**, **A-201**, **A-205**, **A-211**, **A-212** |
| **R2.5.5** | A-088, A-092, A-119, **A-163**, **A-202**, **A-207**, **A-209**, **A-211**, **A-221**, **A-223** |
| **R2.5.6** | A-080, A-082, A-101, A-151, **A-203**, **A-204**, **A-209**, **A-213**, **A-220** |
| **R2.5.7** | A-122, **A-173**, **A-212**, **A-219**, **A-221** |
| **R2.5.8** | A-118, A-123, **A-171**, **A-195**, **A-196**, **A-201**, **A-205**, **A-212**, **A-219** |
| **R2.5.9** | A-123, **A-171**, **A-205** |
| **R2.5.10** | A-124, **A-163**, **A-171**, **A-190**, **A-195**, **A-205**, **A-221** |
| **R2.6.1** | A-131, A-114, **A-152**, **A-207**, **A-218**, **A-220**, **A-222**, **A-229** |
| **R2.6.2** | A-088, A-131, **A-203**–**A-207**, **A-220**, **A-222**, **A-229** |
| **R2.6.3** | **A-132**, **A-151** (ruta `/cursos/{id}/mis-notificaciones`, sólo `curso.ver`), **A-182**, **A-229**, **A-231** |
| **R2.6.4** | A-133, A-125, **A-182**, **A-224**, **A-228**, **A-229** |
| **R2.6.5** | A-125, A-126, A-129, **A-188**, **A-189**, **A-212**, **A-216**, **A-224**–**A-228** |
| **R2.6.6** | A-103, A-126, A-128, **A-188**, **A-189**, **A-193**, **A-216**, **A-225**, **A-227** |
| **R2.6.7** | **A-130**, A-125, **A-189**, **A-216**, **A-224**–**A-227**, **A-233** |
| **R2.7.1** | A-134, **A-180**, **A-206**, **A-214** |
| **R2.7.2** | A-021, A-022, A-135, **A-180**, **A-193**, **A-206**, **A-214** |
| **R2.7.3** | A-135, **A-180**, **A-193**, **A-206**, **A-214** |
| **R2.7.4** | A-104, A-136, **A-163**, **A-041** ítem 18, **A-186**–**A-188**, **A-190**, **A-192**, **A-197**, **A-230** |
| **R2.7.5** | A-137, A-138, A-089, **A-180**, **A-193**, **A-214** |
| **R2.7.6** | A-139, A-140, A-141, A-142, **A-143**, **A-169**, **A-188**, **A-191**, **A-197**, **A-204**, **A-206**, **A-214**, **A-230** |
| **R2.7.7** | A-088, A-105, A-139, A-142, **A-180**, **A-193**, **A-204**, **A-206**, **A-209**, **A-214**, **A-230** |
| **§3.1** | A-156, A-157, A-158, A-159, **A-166**, **A-178**, **A-186**, **A-189**, **A-231**, **A-233**, **A-234** |
| **§3.2** | A-004, A-005, A-011, A-016, A-160, A-161, **A-166**, **A-170**, **A-176**, **A-177**, **A-182**, **A-183**, **A-189**, **A-199**, **A-232** |
| **§3.3** | A-162, **A-174**, **A-235** |
| **§4** | A-151, A-155, A-162, **A-165**, **A-174**, **A-209**, **A-231**, **A-232**, **A-233**, **A-234** |

**Decisiones nuevas de la revisión 2, y qué requisito sostiene cada una:**

| Decisión | Requisitos que sostiene |
|---|---|
| **A-163** acceso docente a los repositorios | R2.4.8, R2.7.4, R2.5.10, R2.3.11, R2.5.5, R2.1.9 |
| **A-164** materialización de sujetos | R2.3.7, R2.3.10, R2.3.4, R2.4.5, R2.5.4, R2.2.6 |
| **A-165** administración de usuarios | R2.1.1, R2.1.7, R2.1.8, R2.1.9, §4 |
| **A-166** acceso del evaluador | §3.1, §3.2 |
| **A-167** entorno `ensayo` frente a Canvas | §3.1 (ensayo del guion), soporte de A-006 |
| **A-168** archivado de repositorios | R2.3.11, cierre de la máquina 2 de A-092 |
| **A-169** escrituras síncronas | R2.1.6, R2.2.4, R2.3.5, R2.3.6, R2.7.6 |
| **A-170** repositorio de operaciones | §3.2, Ley 4, soporte de A-016 |
| **A-171** día y commit contable | R2.5.2, R2.5.3, R2.5.4, R2.5.8, R2.5.9, R2.5.10, R2.6.2 |
| **A-172** `entrega.slug` y tag | R2.4.6, R2.4.7, R2.4.8 |
| **A-173** «entrega anterior» | R2.5.7 |

**Decisiones nuevas de la enmienda de reconciliación (§0.6), y qué requisito sostiene cada una:**

| Decisión | Qué cierra | Requisitos que sostiene |
|---|---|---|
| **A-174** ocho puertas de contrato en CI | RG-161 | R2.1.7–R2.1.9, §3.3, §4 |
| **A-175** una sola migración anterior al 16-sep | RG-144, RG-145, RG-146, RG-193 | R2.4.5, R2.4.7, R2.5.2, R2.5.3, R2.5.8, R2.5.10 y, por esquema, todos |
| **A-176** inventario cerrado de quince secretos | RG-138, RG-081, RG-202 | R2.1.4–R2.1.6, §3.2 |
| **A-177** cinco alertas por correo | RG-143 | R2.1.2, R2.1.4–R2.1.6, R2.1.8, R2.1.9, R2.3.12, R2.6.1, §3.2 |
| **A-178** aritmética de permisos: cinco concedibles | RG-121 | R2.1.7–R2.1.9, §3.1, §3.2 |
| **A-179** `ACCIONES_SOLO_PROFESOR` | RG-122, RG-123, RG-201 | R2.1.7, R2.1.8, R2.2.4, R2.4.5, R2.4.7 |
| **A-180** propiedad acota el trabajo, no la lectura | RG-125, RG-126 | R2.7.1, R2.7.2, R2.7.5, R2.7.7 |
| **A-181** permisos defendidos en base; 17 invariantes | RG-124, RG-199 | R2.1.7–R2.1.9 |
| **A-182** dieciséis rutas sin sesión | RG-129, RG-130, RG-131, RG-132 | R2.1.2, R2.1.7, R2.3.9, R2.3.11, R2.5.2, R2.6.3, R2.6.4, §3.2 |
| **A-183** rastro de la autorización denegada | RG-142 | R2.1.2, R2.1.8, R2.1.9, §3.2 |
| **A-184** catálogos cerrados de bitácora e incidencia | RG-043, RG-044, RG-206 | R2.1.7–R2.1.9, R2.2.4, R2.2.6, R2.3.11, R2.5.5, R2.6.2, R2.7.6 |
| **A-185** cuenta de GitHub del docente y `email_canonico` | RG-001, RG-002 | R2.1.1, R2.1.2, R2.1.7–R2.1.9, R2.3.9, R2.4.8, R2.5.10, R2.7.4 |
| **A-186** consentimiento fechado y `org_github_estado` | RG-133, RG-198 | R2.1.7, R2.1.8, R2.4.8, R2.7.4, §3.1 |
| **A-187** elegibilidad de una cuenta de GitHub | RG-003, RG-134, RG-199 | R2.1.7–R2.1.9, R2.2.4–R2.2.6, R2.4.8, R2.7.4 |
| **A-188** retiro en tres planos y credenciales de Canvas | RG-136, RG-137, RG-139 | R2.1.4, R2.1.7, R2.1.9, R2.6.5, R2.6.6, R2.7.6 |
| **A-189** custodia de las cuentas compartidas | RG-140, RG-141 | R2.1.2, R2.1.8, R2.6.5–R2.6.7, §3.1, §3.2 |
| **A-190** nueve eliminaciones externas | RG-191 | R2.1.9, R2.3.9, R2.3.10, R2.4.8, R2.7.4 |
| **A-191** llavero versionado de claves | RG-138 | R2.1.4–R2.1.6, R2.6.5, R2.6.6, R2.7.6 |
| **A-192** checklist encolado, 21 códigos, cinco resultados | RG-061, RG-063, RG-064, RG-135, RG-200 | R2.1.5–R2.1.7, R2.3.7, R2.4.8, R2.7.4 |
| **A-193** mecanismo único de capacidad degradada | RG-065, RG-066, RG-067, RG-068, RG-080, RG-205 | R2.1.6, R2.2.1–R2.2.5, R2.3.7, R2.3.8, R2.3.12, R2.4.1–R2.4.4, R2.5.3, R2.6.5, R2.6.6, R2.7.6, R2.7.7 |
| **A-194** congelación de permisos y plan de medición | RG-078, RG-079, RG-080 | R2.1.5, R2.3.5–R2.3.9, R2.3.11, R2.4.5–R2.4.7, R2.5.3 |
| **A-195** credencial de los artefactos de `infra/` | RG-081 | R2.1.5, R2.5.1, R2.5.2, R2.5.7, R2.5.8, R2.5.10, R2.6.1 |
| **A-196** commits de la aplicación a nombre del `[bot]` | RG-090, RG-091 | R2.3.7, R2.5.2, R2.5.4, R2.5.8 |
| **A-197** archivar: cinco guardas y rol de profesor | RG-094, RG-095, RG-098, RG-201 | R2.1.3, R2.1.8, R2.3.11, R2.4.5, R2.4.7, R2.4.8, R2.7.4, R2.7.6, R2.7.7 |
| **A-198** censo cerrado de 70 entidades | RG-046, RG-192 | todos los de la parcial y, por esquema, los de la final |
| **A-199** retención de las 23 tablas nuevas | RG-047 | §3.2 y, por dependencia, R2.5.2, R2.5.7, R2.6.2 |
| **A-200** `ON DELETE RESTRICT` y FK nullables | RG-048 | R2.4.7, R2.7.6 y todo lo que la Ley 2 protege |
| **A-201** `identidad_git` parcial e índice por curso | RG-006, RG-007 | R2.2.4, R2.2.5, R2.5.4, R2.5.8 |
| **A-202** `repositorio` parcial y sustitución por fila nueva | RG-014, RG-015, RG-182 | R2.3.7, R2.3.8, R2.3.10, R2.3.11, R2.4.5, R2.4.7, R2.5.5 |
| **A-203** `entrega`: escalar, `validaciones` y `advertencias` | RG-019, RG-020, RG-021, RG-022 | R2.3.1–R2.3.3, R2.4.1, R2.4.4, R2.4.5, R2.4.7, R2.5.6, R2.6.2, R2.7.6, R2.7.7 |
| **A-204** `version_entrega`: mutables e `integrantes` | RG-024, RG-026, RG-027, RG-028, RG-035, RG-195 | R2.2.3, R2.4.5–R2.4.8, R2.5.6, R2.6.2, R2.7.6, R2.7.7 |
| **A-205** `autoria_commit` y commit contable intacto | RG-029, RG-030 | R2.5.2–R2.5.4, R2.5.8–R2.5.10, R2.6.2 |
| **A-206** `estado_canvas_submission` y `contraste_canvas` derivado | RG-031, RG-034, RG-101, RG-186, RG-187 | R2.7.1–R2.7.3, R2.7.6, R2.7.7 |
| **A-207** silenciar, y 51 tipos de incidencia | RG-042, RG-189, RG-190 | R2.2.6, R2.3.11, R2.5.3–R2.5.5, R2.6.1, R2.6.2, R2.7.6, R2.7.7 |
| **A-208** `repositorio_base.estado` y la guarda de activación | RG-017 | R2.3.5–R2.3.7, R2.3.11 |
| **A-209** siete máquinas y `estados.py` como fuente única | RG-049, RG-050, RG-203 | R2.2.6, R2.3.11, R2.5.5, R2.5.6, R2.7.7, §4 |
| **A-210** máquina 1: `SIN_DATO` persistido, cinco motivos | RG-004, RG-005 | R2.2.4–R2.2.6, R2.3.9, R2.3.10 |
| **A-211** máquina 2: `INACCESIBLE` y salidas escritas | RG-011, RG-012, RG-013, RG-016, RG-181 | R2.3.4, R2.3.7, R2.3.10, R2.3.11, R2.4.5, R2.4.7, R2.5.2, R2.5.5 |
| **A-212** máquina 3: diez valores, revocación con decisión humana | RG-008, RG-009, RG-010, RG-183, RG-184, RG-185 | R2.1.9, R2.2.3, R2.3.4, R2.3.9–R2.3.12, R2.5.4, R2.5.8, R2.6.5 |
| **A-213** máquina 4: seis terminales y `tag_estado` aparte | RG-024, RG-025, RG-188 | R2.4.5–R2.4.8, R2.5.6 |
| **A-214** máquina 5: ocho estados y bandera con motivo | RG-032, RG-033, RG-205 | R2.3.1, R2.7.1–R2.7.3, R2.7.5–R2.7.7 |
| **A-215** máquina 6: `CANCELADO` fuera de la idempotencia | RG-045 | R2.3.10, R2.4.5, R2.6.5, R2.6.7, R2.7.6 |
| **A-216** máquina 7: quince estados, siete guardas, veinte motivos | RG-038, RG-039, RG-040, RG-196 | R2.3.12, R2.6.2, R2.6.4–R2.6.7 |
| **A-217** dos espacios de cerrojo por curso | RG-062 | R2.1.6, R2.3.7, R2.3.10, R2.5.1, R2.5.2 |
| **A-218** A-114 con 31 trabajos y fecha de servicio | RG-153, RG-194 | R2.1.6, R2.3.9, R2.3.10, R2.4.5, R2.4.6, R2.7.6, R2.7.7 |
| **A-219** `presupuesto_api` con cuatro cubos | RG-070, RG-071, RG-072, RG-073 | R2.2.1, R2.2.2, R2.3.7, R2.3.10, R2.5.7, R2.5.8 |
| **A-220** estado agregado de la entrega para R2.5.6 | RG-023 | R2.4.2, R2.4.3, R2.4.5, R2.5.6, R2.6.1, R2.6.2 |
| **A-221** ingesta en tres piezas con relleno hacia atrás | RG-152 | R2.3.9, R2.3.11, R2.5.2, R2.5.3, R2.5.5, R2.5.7, R2.5.8, R2.5.10 |
| **A-222** ventana observada frente al umbral | RG-155 | R2.5.3, R2.5.4, R2.6.1, R2.6.2 |
| **A-223** techo de frescura por fórmula (NFR-2.5-A) | RG-100 | R2.5.1–R2.5.3, R2.5.5, R2.5.10 |
| **A-224** `generacion` y `reemplaza_a_id` en el *outbox* | RG-036 | R2.3.12, R2.6.4–R2.6.7 |
| **A-225** dos interruptores ortogonales en `curso` | RG-037 | R2.3.10, R2.3.12, R2.4.5, R2.6.5–R2.6.7 |
| **A-226** seis escrituras síncronas; todo endpoint nuevo encola | RG-087 | R2.1.4, R2.1.6, R2.2.5, R2.3.5, R2.3.6, R2.3.11, R2.4.8, R2.7.4, R2.7.6 |
| **A-227** degradación del canal de Canvas | RG-102, RG-103 | R2.3.9, R2.3.12, R2.4.7, R2.6.5, R2.6.7, R2.7.6 |
| **A-228** cuota de correo del despliegue, tres reservas | RG-104, RG-160, RG-197 | R2.1.7, R2.1.8, R2.2.2, R2.6.3–R2.6.5 |
| **A-229** `informe_diario`: ventana, estado e histórico acotado | RG-041, RG-207 | R2.6.1–R2.6.4 |
| **A-230** versión de repositorio inaccesible, corregible | RG-018 | R2.3.11, R2.4.7, R2.4.8, R2.7.4, R2.7.6, R2.7.7 |
| **A-231** tres rutas públicas y un solo sello de antigüedad | RG-075, RG-148 | R2.1.4, R2.1.7, R2.1.8, R2.2.2, R2.5.1, R2.5.2, R2.5.5, R2.6.3, R2.7.7, §3.1 |
| **A-232** `/operacion`: inventario único y acotado por curso | RG-127, RG-128, RG-204 | R2.1.7–R2.1.9, R2.5.1, R2.5.2, R2.5.5, R2.7.7, §3.2, §4 |
| **A-233** doce banderas de `PERFIL_ALCANCE` y lista normativa | RG-147, RG-148, RG-149, RG-150 | todos los de A-157, por construcción |
| **A-234** régimen de `/alcance` y de la banda de cabecera | RG-151 | §3.1 y §4; hace verificable el criterio de A-156 |
| **A-235** la enmienda única precede a la migración | RG-105, RG-190 | §3.3 y, por dependencia, todos |

**Decisiones anteriores marcadas como ANULADAS por esta enmienda, y quién manda en cada caso** (§0.6). **Ninguna se ha borrado:**

| Anulada | Por | Manda ahora |
|---|---|---|
| A-012 (tabla de puertas) | RG-161 | **A-174** |
| A-013 (calendario) | RG-144, RG-145, RG-146, RG-193 | **A-175** |
| A-014 (inventario) | RG-138, RG-081, RG-202 | **A-176**, **A-191** |
| A-015 (cuatro alertas; panel sin acotar) | RG-143, RG-127, RG-204 | **A-177**, **A-232** |
| A-022 (firma y cláusula de propiedad) | RG-122, RG-125 | **A-179**, **A-180** |
| A-025 (punto 6) | RG-136, RG-139 | **A-188** |
| A-029 (falta de catálogo) | RG-043, RG-044, RG-142, RG-206 | **A-183**, **A-184** |
| A-030 (seis eliminaciones) | RG-191 | **A-190** |
| A-034 (clave maestra única) | RG-138 | **A-191** |
| A-039 (registro de coste) | RG-070, RG-071 | **A-219** |
| A-041 (ejecución, códigos, resultados, ítem 14) | RG-061, RG-063, RG-135, RG-200 | **A-192** |
| A-060, A-061 (conjunto final y firma) | RG-078, RG-079 | **A-194** |
| A-075, A-077, A-080, A-083–A-088, A-090 (esquema) | RG-001–RG-047, RG-190, RG-192 | **A-185**, **A-186**, **A-191**–**A-193**, **A-198**–**A-208**, **A-210**–**A-215**, **A-224**, **A-229** |
| A-091, A-092, A-094, A-099, A-101, A-104–A-106 (máquinas) | RG-003–RG-016, RG-024–RG-045, RG-181–RG-188 | **A-209**–**A-216** |
| A-113, A-114, A-115, A-117 (cola y presupuesto) | RG-047, RG-062, RG-153, RG-194, RG-071 | **A-199**, **A-217**–**A-219** |
| A-118, A-119, A-121, A-171 (seguimiento) | RG-023, RG-029, RG-030, RG-155 | **A-205**, **A-220**, **A-222** |
| A-125, A-131, A-133, A-169 (comunicación) | RG-036, RG-041, RG-087, RG-104, RG-196, RG-197, RG-207 | **A-224**, **A-226**, **A-228**, **A-229** |
| A-136, A-138, A-139, A-142 (corrección) | RG-018, RG-019, RG-028, RG-031, RG-032, RG-101 | **A-203**, **A-204**, **A-206**, **A-214**, **A-230** |
| A-151, A-157, A-160, A-162 (pantallas, alcance y proceso) | RG-079, RG-127, RG-143, RG-147, RG-148, RG-190, RG-204 | **A-177**, **A-231**–**A-235** |
| A-163, A-165, A-166, A-168, A-170 (decisiones de la revisión 2) | RG-094, RG-098, RG-121, RG-133, RG-136, RG-139, RG-140, RG-191, RG-198, RG-201, RG-202 | **A-178**, **A-185**–**A-190**, **A-197** |

---

## 21. Lo que este documento deja deliberadamente abierto

Sólo dos cosas, y ninguna es de arquitectura. **Eran tres; la primera se ha cerrado en la revisión 2 porque se pisaba con A-061.**

1. ~~El nombre del producto y el dominio~~ — **CERRADO.** Se decide el **10 de septiembre a las 09:00**, no el 12, porque A-061 congela los permisos de la GitHub App tras la prueba del 10-11 y A-059 hace depender su marca del nombre del producto: **no se puede registrar y probar el 10 una App cuyo nombre se decide el 12.** El calendario completo está en A-061. Dejar esto «abierto» era, en la práctica, dejar abierta una fecha del camino crítico.
2. **El valor exacto del umbral de «actividad reciente»** por curso, propuesto en 7 días (A-121). Es una decisión pedagógica, no técnica, y la aplicación ya la expone como configurable entre 1 y 30 días.
3. **Si se persigue un plan de pago de GitHub por GitHub Education** para habilitar protección de tags en repositorios privados. **Este documento asume que no y diseña en consecuencia** (Ley 4, A-104); si se consiguiera, la protección sería una mejora, **nunca un cambio de arquitectura**.

**Todo lo demás está decidido.** Las **235** decisiones numeradas son el contrato: **cambiar una obliga a revisar los requisitos que la citan** en §20 y a actualizar este documento, nunca a resolver la contradicción por cuenta propia. **Una decisión marcada como anulada no se cita sola**: se cita junto a la que manda ahora (§0.6).

**Y una advertencia final, dirigida a los 28 agentes que van a decidir apoyándose en esto.** Este documento ha sido revisado de forma adversarial y ha resultado tener once decisiones ausentes, veinte contradicciones internas y veintidós ambigüedades explotables. **Ninguna era obvia leyendo la sección donde estaba**; todas aparecieron al leer dos secciones juntas. La lección operativa, que es una decisión de proceso y no un consejo:

> **Cuando una pregunta de alcance toque dos decisiones a la vez, hay que leer las dos y comprobar que no se contradicen antes de responder.** Si se contradicen, **no se resuelve por cuenta propia**: se escala, con las dos citas `A-nnn` delante. Ése es literalmente el mecanismo que encontró estos cincuenta y tres problemas antes de que llegaran al código.
