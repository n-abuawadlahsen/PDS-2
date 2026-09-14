# 4. Vinculación de curso, Canvas y GitHub

Este capítulo especifica el flujo completo con el que un profesor vincula un curso de la aplicación a un curso de Canvas y a una organización de GitHub: el asistente de cuatro pasos, qué credencial se pega y cuándo, el checklist de verificación con sus 19 comprobaciones numeradas, qué ocurre cuando una comprobación falla, cómo se re-vincula o se cambia una vinculación existente, y los casos borde del proceso.

**Requisitos que satisface:** R2.1.4 (vincular cada curso con un curso disponible en Canvas), R2.1.5 (vincular cada curso con una organización de GitHub) y R2.1.6 (guiar al profesor durante la vinculación, permitiendo verificar que las configuraciones son correctas) por completo.

**Restricciones que gobiernan todo el capítulo**, ya fijadas en el capítulo 1 y que este capítulo no vuelve a discutir, sólo aplica: el equipo tiene rol de **profesor** en Canvas, no de administrador de cuenta, de modo que no hay Developer Key propia en el camino que se despliega, no hay creación de cursos en Canvas —la aplicación los vincula, nunca los crea— y **toda decisión que dependa de privilegios de administrador de Canvas está mal planteada y queda descartada de antemano** (§1.1 de ARQUITECTURA.md). La GitHub App es **pública** y se instala por URL, nunca por Marketplace (A-057). La organización de GitHub es **nueva y de plan gratuito**, sin *rulesets* en repositorios privados (§1.3 de ARQUITECTURA.md).

---

## 4.1 Cómo leer este capítulo

**Orden de precedencia aplicado, sin excepciones** (convención 1 de §1.14 de este mismo documento de especificación): enunciado → actas de reconciliación (`RG-nnn`) → carta de arquitectura (`A-nnn`) → respuestas de alcance (`Q-2.1-nn`, `Q-2.6-nn`). Donde una respuesta de alcance decía una cosa y una regla `RG` dice otra, manda la regla y este capítulo redacta la regla. Donde una decisión de la carta fue anulada por una regla del acta, este capítulo cita únicamente la regla vigente, y si la cita alguna vez a la decisión anulada es siempre junto a su sustituta.

**Correcciones de precedencia que este capítulo aplica y que conviene tener presentes desde el principio:**

| Punto | Lo que decía la fuente original | Lo que manda ahora | Fuente |
|---|---|---|---|
| Catálogo del checklist | 19 comprobaciones numeradas, 4 valores de resultado (A-041) | **21 códigos**: los 19 numerados más las pruebas de escritura opcionales `5-bis` y `17-bis`; **5 valores de resultado**, con `VERIFICADO_A_MANO` añadido | RG-063, A-192 |
| Mecanismo de ejecución del checklist | No especificado; el estudio interno contemplaba SSE para el asistente (`Q-2.1-56`, lote-03) | Trabajo encolado `ejecutar_checklist_vinculacion`, sondeado desde la interfaz cada 2 s; **no se usan SSE ni WebSocket en ninguna pantalla de la aplicación** | RG-061 |
| Tiempo de espera del checklist | No fijado por hueco (`Q-transversal-36`, lote-24) | **10 s por ítem**, tope global **180 s**; lo que no termine queda `NO_VERIFICADO` con motivo `TIEMPO_AGOTADO`, nunca en verde | RG-061 |
| Severidad de tres sub-comprobaciones del ítem 14 (`default_repository_permission`, `members_can_create_repositories`, verificación en dos pasos + dos owners) | Informativa / advertencia, condicionadas a que el campo sea legible (`Q-2.1-39`) | **Bloqueantes las cuatro sub-comprobaciones de configuración base de la organización**; si el campo no es legible, el ítem sólo se cierra con la marca `VERIFICADO_A_MANO`, firmada por un profesor en pantalla | RG-135 |
| Qué comprueba el ítem 14 | Una sola comprobación (A-041 original) | **Seis sub-comprobaciones** `(a)`–`(f)`, dentro del mismo tope de 10 s | A-192, RG-064 |
| Qué comprueba el ítem 18 y su severidad | Llamada en vivo a GitHub sobre lectura de repositorios, **bloqueante** para R2.4.8 y R2.7.4 (A-041, A-163) | **No llama a GitHub**: lee `membresia_curso.org_github_estado` y resume cuántos docentes están `ACTIVA`, `PENDIENTE`, `ERROR` o `NO_APLICA`; **severidad advertencia** | RG-064 |
| `verificacion_vinculacion.item` y `ejecutada_por` | `NOT NULL`, recorre 19 valores (A-075 original) | **`item` nullable** (recorre 21 valores o es nulo cuando `origen = RUNTIME`), **`ejecutada_por` nullable**; se añaden `origen ∈ {CHECKLIST, RUNTIME}` y `capacidad` | RG-065, A-193 |
| Cerrojo del checklist frente a Canvas y GitHub | Un único `pg_advisory_lock(curso_id)` para todo el curso | **Dos espacios de cerrojo distintos**, uno por proveedor, que el trabajo del checklist toma y libera ítem a ítem, nunca ambos a la vez | RG-062 |

**Convenciones de escritura que este capítulo respeta sin redefinirlas** (fijadas en ARQUITECTURA.md §16 y citadas en el capítulo 1 de esta especificación): todo instante se almacena en UTC y se presenta en la zona del curso con formato `dd-MM-yyyy HH:mm` y la zona escrita al lado siempre; todo estado interno se muestra traducido y **nunca aparece un identificador en mayúsculas en pantalla**; vocabulario cerrado — se dice **vinculación**, **asistente**, **checklist**, **comprobación**, **credencial**, **instalación**; no se dice wizard, setup, token (a secas, sin decir «de acceso personal»), ni check a secas.

---

## 4.2 Modelo de datos de la vinculación

El modelo base de `curso` —nombre, código, período y zona horaria, escritos en el paso 1 del asistente— es del área de creación y administración de cursos (R2.1.3) y no se redefine aquí. Esta sección documenta únicamente las columnas de `curso` y las tablas propias que la vinculación con Canvas y con GitHub necesita, tal como las fija A-075 con las correcciones de §4.1.

### 4.2.1 Columnas de `curso` que este capítulo utiliza

| Columna | Tipo y restricción | Para qué |
|---|---|---|
| `estado` | `{BORRADOR, VINCULANDO, ACTIVO, CANVAS_DESVINCULADO, GITHUB_DESVINCULADO, ARCHIVADO}` | Progresión del asistente y guardas de acceso (§4.3) |
| `canvas_base_url` | texto, normalizada al guardarse (esquema `https`, host en minúsculas, sin barra final) | Instancia de Canvas elegida en el paso 2; parte de la clave del vínculo, **único junto con `canvas_course_id`** |
| `canvas_course_id` | `bigint` | Curso de Canvas elegido en el paso 2; **único (`canvas_base_url`, `canvas_course_id`)** (A-027) |
| `github_org_login` | texto, dato de presentación mutable | Nombre visible de la organización; se refresca en cada ejecución de `verificar_instalacion_github` |
| `github_org_id` | `bigint` | Clave estable de la organización (Ley 3); **único donde no nulo** (A-027) |
| `github_installation_id` | `bigint` | Instalación activa de la GitHub App; **único donde no nulo** (A-028); reemplazable ante una reinstalación |
| `via_anuncio_seccion` | `{SECCION, CURSO, NINGUNA, NO_VERIFICADO}`, `DEFAULT NO_VERIFICADO` | Resultado de la prueba de escritura `5-bis` (§4.7) |
| `canal_comunicacion_activo` | `{CONVERSACION, COMENTARIO_ENTREGA, BLOQUEADO}` | Canal vigente para R2.3.12 y R2.6.5, resuelto por la verificación de canales (§4.9) |

`curso.slug`, `curso.roles_estudiante_extra`, `curso.umbral_dias_sin_actividad` y `curso.creado_por_usuario_id` existen y se citan cuando hace falta, pero no son de este capítulo.

### 4.2.2 Tablas propias de la vinculación

| Tabla | Columnas | Unicidad y notas |
|---|---|---|
| `credencial_canvas` | `id`, `curso_id`, `usuario_id`, `token_cifrado` (`bytea`), `nonce`, `huella`, `canvas_user_id`, `estado`, `orden_respaldo`, `version_clave` (`smallint`, `DEFAULT 1`), `consentimiento_en`, `ultimo_chequeo_en`, `ultimo_error`, `fallos_403_consecutivos` (`smallint`, `DEFAULT 0`, RG-070) | **único (`curso_id`, `usuario_id`)**; **único parcial `curso_id` donde `orden_respaldo = 0`**, que es la credencial operativa. `estado ∈ {VALIDA, INVALIDA, RETIRADA}`. Cifrada con AES-256-GCM, llavero versionado, `curso_id` como *additional authenticated data* (A-035, A-191). `fallos_403_consecutivos` cuenta los `403` no transitorios consecutivos que llevan a `INVALIDA` (§5.2.7); esta es la tabla canónica, **§5 la usa sin redefinirla** |
| `instalacion_github` | `installation_id` (PK, `bigint`), `curso_id`, `org_login`, `org_id`, `org_node_id`, `repository_selection`, `permisos_pendientes`, `suspendida`, `actualizada_en` | **único `curso_id`** (A-027, A-028). `curso_id` es **nullable**: una instalación huérfana es una fila con `curso_id` nulo (§4.6.5) |
| `equipo_github_curso` | `id`, `curso_id`, `team_id` (`bigint`), `team_slug`, `estado`, `via_efectiva`, `creado_en`, `ultimo_error` | **único `curso_id`** (A-163). `via_efectiva ∈ {TEAM, COLABORADOR}`: registra qué vía quedó activa tras el ítem 18 |
| `verificacion_vinculacion` | `id`, `curso_id`, `ejecucion_id` (`uuid`), `item` (**nullable**), `origen ∈ {CHECKLIST, RUNTIME}`, `capacidad` (texto, **nullable**), `resultado`, `detalle` (`jsonb`), `ejecutada_en`, `ejecutada_por` (**nullable**) | Índices `(curso_id, ejecucion_id)`, `(curso_id, item)`, `(curso_id, capacidad)`. `resultado ∈ {CORRECTO, ADVERTENCIA, BLOQUEANTE, NO_VERIFICADO, VERIFICADO_A_MANO}`. `CHECK`: `origen = CHECKLIST ⇒ item` no nulo y `capacidad` nula; `origen = RUNTIME ⇒ capacidad` no nula (RG-061, RG-065, A-192, A-193) |
| `intento_instalacion_github` | `id`, `curso_id`, `usuario_id`, `jti`, `org_login_sugerido`, `emitido_en`, `consumido_en` | Persiste la intención de instalar **antes** de salir a GitHub (Ley del intento antes de la llamada, restricción transversal 15 de este documento de especificación). Alimenta la guarda de adopción de instalaciones huérfanas (§4.6.5) (`Q-2.1-37`) |
| `verificacion_canal` | `id`, `curso_id`, `canal`, `resultado`, `evidencia` (`jsonb`), `verificado_por`, `verificado_en` | **único (`curso_id`, `canal`)**. Es el bloque «Canales de comunicación» del paso 4, **distinto del checklist de 19 ítems** (`Q-2.6-02`) |

**Ninguna de estas seis tablas propaga entre cursos.** Cada curso tiene su propia credencial, su propia instalación, su propio equipo, su propio historial de checklist y su propia verificación de canales, aun cuando dos cursos compartan el mismo profesor: es aplicación directa de la restricción transversal 9 de este documento de especificación (autorización acotada por `curso_id`) y de A-027/A-028 (una organización y un curso de Canvas pertenecen a exactamente un curso de la aplicación).

### Criterios de aceptación de 4.2

| Id | Comprobación |
|---|---|
| CA-4.2-01 | Insertar una segunda fila de `credencial_canvas` con `orden_respaldo = 0` para el mismo `curso_id` es rechazado por el índice único parcial |
| CA-4.2-02 | Insertar una segunda fila de `instalacion_github` con el mismo `curso_id` es rechazado; insertar una fila con `curso_id` nulo se acepta |
| CA-4.2-03 | Una fila de `verificacion_vinculacion` con `origen = 'CHECKLIST'` y `capacidad` no nula, o con `origen = 'RUNTIME'` y `item` no nulo, es rechazada por el `CHECK` |
| CA-4.2-04 | Vincular un segundo curso de la aplicación al mismo `(canvas_base_url, canvas_course_id)` ya vinculado es rechazado por la restricción única, nunca crea una segunda fila de `estudiante` para ese roster |
| CA-4.2-05 | Vincular un segundo curso de la aplicación a un `github_org_id` ya vinculado es rechazado antes de crear ningún repositorio |

---

## 4.3 Quién puede vincular: permisos y máquina de estados del curso

### 4.3.1 Permiso exigido en cada paso

**Un único permiso gobierna todo el capítulo: `curso.administrar`.** Es uno de los dos permisos configurables **NO CONCEDIBLES** (capítulo 1, §1.6): un profesor lo tiene siempre y de forma implícita; un ayudante **no puede tenerlo bajo ninguna circunstancia**, porque da acceso a la credencial de Canvas del curso. En consecuencia, **ningún ayudante puede iniciar, completar, reejecutar ni cambiar ninguna parte de la vinculación**, y la ruta del asistente (`/cursos/nuevo`, `/cursos/{id}/vinculacion`) y la de re-vinculación (`/cursos/{id}/ajustes`) exigen `curso.administrar` sin excepción (A-151).

| Paso | Quién puede iniciarlo y completarlo | Permiso | Regla adicional |
|---|---|---|---|
| 1. Datos del curso | Cualquier usuario con sesión; se convierte en profesor al crear el curso | ninguno (crea la membresía) | Fuera de alcance de este capítulo (R2.1.3) |
| 2. Canvas | Cualquier profesor **activo** del curso | `curso.administrar` | **Sólo el titular pega su propio token**; nadie pega el token de otra persona (A-033) |
| 3. GitHub | Cualquier profesor **activo** del curso | `curso.administrar` | Cualquiera de ellos puede iniciar la instalación; quien la complete es quien está en sesión en GitHub en ese momento |
| 4. Verificación | Cualquier profesor **activo** del curso | `curso.administrar` | Las pruebas de escritura opcionales (`5-bis`, `17-bis`) exigen además marcar la casilla de consentimiento en esa misma sesión |
| Re-vinculación / `/cursos/{id}/ajustes` | Cualquier profesor **activo** del curso | `curso.administrar` | Añadir, retirar y promover credenciales; reinstalar GitHub; reejecutar el checklist |

**No existe un rol «vinculador» distinto de profesor.** Los profesores no tienen jerarquía entre sí (A-020): cualquiera de ellos puede completar cualquier paso, cualquiera puede añadir su propia credencial de respaldo, y cualquiera puede promover la suya a operativa con la confirmación nominal que se describe en §4.10.

### 4.3.2 La máquina de estados de `curso` durante la vinculación

`curso.estado` tiene **seis valores** y gobierna qué está habilitado y qué está bloqueado mientras la vinculación no está completa, y qué degrada cuando se rompe después (`Q-2.1-15`, `Q-2.1-19`, A-026).

| Estado | Se entra cuando | Qué está habilitado | Qué está bloqueado, y cómo se explica |
|---|---|---|---|
| `BORRADOR` | Se crea el curso (paso 1) | `/cursos/{id}/vinculacion`, `/cursos/{id}/equipo`, `/cursos/{id}/ajustes`, `/perfil`, `/cursos/{id}/mis-notificaciones` | Personas, Pendientes, Tareas, Corrección y toda comunicación: cada una muestra su estado vacío con el botón «Vincular con Canvas» |
| `VINCULANDO` | Se completa **uno** de los dos vínculos (Canvas o GitHub) | Lo anterior, más Personas en sólo lectura si Canvas ya está vinculado | Crear tareas y aprovisionar repositorios. «Nueva tarea» queda deshabilitado con el texto «falta vincular GitHub» y su enlace |
| `ACTIVO` | Los **dos** vínculos hechos **y** el checklist ejecutado sin ningún ítem `BLOQUEANTE` en rojo | Todo | — |
| `CANVAS_DESVINCULADO` | `401` de Canvas, o `403` no transitorio repetido tres veces (A-036) | Aprovisionamiento, ingesta de actividad, tableros, timeline y **captura de versiones**, porque las fechas efectivas ya están persistidas | Lecturas de Canvas detenidas; escrituras **encoladas** en `ESPERANDO_CREDENCIAL`, nunca descartadas. Banda roja persistente con qué falta, quién puede arreglarlo y el enlace a `/cursos/{id}/ajustes` |
| `GITHUB_DESVINCULADO` | La instalación desaparece o queda suspendida (webhook `installation`, o el trabajo periódico de verificación) | Sincronización de Canvas, Personas, Pendientes, fechas y todo lo que se pinta del espejo | Trabajos de GitHub en `BLOQUEADO`; el aprovisionamiento no falla, espera. Banda roja con el enlace a reinstalar |
| `ARCHIVADO` | Acción explícita de un profesor con `curso.administrar` | Sólo lectura | Todos los trabajos periódicos. Fuera de alcance de este capítulo (administración del curso) |

**Precondiciones de negocio, que son bloqueos duros y no advertencias:**

- **No se completa la vinculación si el titular del token tiene `limit_privileges_to_course_section = true`** en todas sus matrículas de profesor activas de ese curso (A-052, ítem 3, §4.5.3).
- **No se completa la vinculación si los ítems 6 y 17 salen los dos en rojo**, porque entonces R2.3.12 no tiene ningún canal por Canvas (§4.9).
- **`curso.estado` pasa a `ACTIVO` sólo con cero ítems `BLOQUEANTE` en rojo.** Un ítem en `ADVERTENCIA`, `NO_VERIFICADO` o `VERIFICADO_A_MANO` no impide la transición.

`GET /api/cursos/{id}/capacidades` es la única fuente que decide qué está habilitado en cada estado, compartida por el backend (autorización) y el frontend (navegación), para que ocultar un control y autorizarlo nunca diverjan (restricción transversal 9 de este documento).

### Criterios de aceptación de 4.3

| Id | Comprobación |
|---|---|
| CA-4.3-01 | Un ayudante que intenta abrir `/cursos/{id}/vinculacion` o `/cursos/{id}/ajustes` recibe `403` con el motivo «da acceso a la credencial de Canvas del curso», y el enlace no aparece en su navegación |
| CA-4.3-02 | Con `curso.estado = VINCULANDO` y sólo Canvas vinculado, el botón «Nueva tarea» está deshabilitado con el texto «falta vincular GitHub» |
| CA-4.3-03 | Un curso con los dos vínculos hechos pero con el ítem 1 o el ítem 16 en rojo permanece en `VINCULANDO`, nunca pasa a `ACTIVO` |
| CA-4.3-04 | Provocado un `401` de Canvas sobre un curso `ACTIVO`, el curso pasa a `CANVAS_DESVINCULADO` en el ciclo siguiente de la sonda, y la captura de versiones programada sigue ejecutándose |
| CA-4.3-05 | `GET /api/cursos/{id}/capacidades` es la única función que decide si un botón de vinculación está habilitado; una prueba de arquitectura falla si aparece una segunda fuente de esa decisión en el frontend |

---

## 4.4 El asistente de vinculación: visión general

**Es un asistente de cuatro pasos con estado persistido, que se puede abandonar y retomar; no es un formulario** (A-040). El orden de progresión es lineal hacia `ACTIVO`, pero **los pasos 2 y 3 son independientes entre sí** y pueden completarse en cualquier orden, porque Canvas y GitHub no dependen el uno del otro.

| Paso | Qué hace | Obligatorio antes de `ACTIVO` |
|---|---|---|
| **1. Datos del curso** | Nombre, código, período, `slug` propuesto y editable, zona horaria | Sí — sin la fila `curso` no hay a qué colgar nada (fuera de alcance: R2.1.3) |
| **2. Canvas** | Pegar el token personal y elegir el curso de la lista (§4.5) | Sí |
| **3. GitHub** | Instalar la App con `state` firmado; se crea además el equipo `docentes` y el repositorio `gestor-operaciones` (§4.6) | Sí |
| **4. Verificación** | Checklist de 19 comprobaciones más `5-bis` y `17-bis`, y el bloque de canales (§4.7–§4.9) | El checklist es reejecutable siempre; `ACTIVO` exige cero ítems bloqueantes en rojo |

**Estado persistido en dos sitios**, para que el docente vea qué se comprobó y cuándo, y no una pantalla que se reinicia: `curso.estado` para la progresión (§4.3.2), y `verificacion_vinculacion` para el resultado de cada comprobación, con fecha y la respuesta cruda.

**Tres puntos de reanudación**, porque un asistente que sólo se retoma por una URL no se retoma:

1. La tarjeta del curso en `/cursos`, con el botón primario «Continuar la vinculación», que abre `/cursos/{id}/vinculacion` en el primer paso no completo.
2. Una **banda ámbar permanente** en la cabecera de cualquier pantalla del curso mientras la vinculación esté incompleta, con el paso que falta escrito.
3. La propia ruta `/cursos/{id}/vinculacion`, que muestra los pasos ya hechos **plegados y con su marca de verificación**, nunca ocultos.

**Después de `ACTIVO`, los mismos pasos siguen accesibles** desde `/cursos/{id}/ajustes` con `curso.administrar`, para sustituir la credencial de Canvas o rehacer cualquiera de los dos vínculos (§4.10).

### Criterios de aceptación de 4.4

| Id | Comprobación |
|---|---|
| CA-4.4-01 | Abandonado el asistente tras completar el paso 2 y recargada la sesión más tarde, `/cursos/{id}/vinculacion` reabre en el paso 3, con el paso 2 plegado y su marca de verificación visible |
| CA-4.4-02 | Completar el paso 3 antes que el paso 2 produce el mismo curso `ACTIVO` que completarlos en el orden inverso, una vez el checklist pasa sin ítems bloqueantes |
| CA-4.4-03 | La banda ámbar de vinculación incompleta aparece en toda pantalla del curso, incluidas Personas y Tareas, mientras `curso.estado ∈ {BORRADOR, VINCULANDO}` |
| CA-4.4-04 | `/cursos/{id}/ajustes` con `curso.estado = ACTIVO` sigue ofreciendo «añadir otra credencial de Canvas» y «reinstalar GitHub» |

---

## 4.5 Paso 2 — Vinculación con Canvas (R2.1.4)

### 4.5.1 Qué credencial se pega, y cuándo

**El mecanismo que se implementa y se despliega es el token de acceso personal, generado por el propio profesor desde su perfil de Canvas** (A-031). El profesor lo genera **antes** de abrir el paso 2 —el formulario enlaza a la pantalla de Canvas donde se genera— y lo pega en un único campo. **Sólo el titular pega su propio token; nadie pega el token de otra persona bajo ninguna circunstancia** (A-033, A-035 regla 1): la interfaz sólo ofrece «añadir **mi** credencial», el botón de envío está deshabilitado hasta marcar una casilla que afirma «pega tu propio token; no pegues el de otra persona», y una segunda casilla de consentimiento —«con esta credencial la aplicación publicará notas, anuncios, mensajes y comentarios **a tu nombre** en Canvas, incluidos los originados por otros miembros del equipo docente»— es obligatoria antes de guardar.

Existe además un camino alternativo, **OAuth2 con Developer Key institucional**, condicionado a que la universidad conceda esa key y **no desplegado**: ninguna funcionalidad de este capítulo depende de él (A-032). Mientras no se active, el paso 2 sólo muestra el campo de token.

### 4.5.2 Las cinco comprobaciones al pegar el token, en orden, siempre las cinco

**Esta tabla es la misma regla de negocio que `docs/SPEC/05-integracion-canvas.md` §5.2.3** (que además documenta la llamada HTTP exacta de cada comprobación); **§5.2.3 es la versión canónica** — si una comprobación cambia, se corrige ahí primero y esta tabla se actualiza para que coincida palabra por palabra. Se repite aquí, en la narrativa del asistente, porque el profesor la vive como parte del paso 2 del wizard (§4.4), no como un detalle de integración.

| # | Comprobación | Si falla |
|---|---|---|
| 2.a | `GET /api/v1/users/self` responde `200` | Se rechaza: el token no sirve |
| 2.b | Ese `id` tiene una matrícula de profesor **activa** en el curso de Canvas que se está vinculando | Se rechaza con «este token pertenece a alguien que no es profesor de ese curso» — es la comprobación que **sí funciona en el primer pegado** |
| 2.c | Ese `(canvas_base_url, canvas_user_id)` no está ya vinculado a otro usuario de la aplicación | Se rechaza y se abre incidencia: dos personas de la aplicación no pueden ser la misma persona de Canvas |
| 2.d | Si el usuario **ya tiene** identidad registrada para esa instancia, el `id` devuelto coincide con ella | Se rechaza; sólo aplica a partir del segundo pegado en esa instancia |
| 2.e | Si no la tiene, se registra ahora como identidad verificada, con `verificada_en` | — |

La identidad de Canvas de cada persona vive en `identidad_canvas_usuario (usuario_id, canvas_base_url, canvas_user_id, verificada_en, ultima_confirmacion_en)`, con único `(usuario_id, canvas_base_url)` y único `(canvas_base_url, canvas_user_id)` (A-033). **No es inmutable**: una fusión de usuarios en Canvas la invalida, y el propio dueño la corrige repitiendo el pegado tras confirmar en pantalla el cambio.

### 4.5.3 Elegir la instancia y el curso de Canvas

**La instancia de Canvas es un campo real por curso**, elegido de una lista blanca configurable por entorno, con la institucional preseleccionada (`Q-2.1-20`). No hay campo libre de URL.

**El profesor no escribe nunca el identificador numérico del curso** (A-040): elige de una lista de tarjetas obtenida con `GET /api/v1/courses?enrollment_type=teacher&enrollment_state=active&include[]=term&include[]=total_students&per_page=100`, paginada siempre por el header `Link` (`Q-2.1-25`). Cada tarjeta muestra `name`, `course_code`, el término, el número de estudiantes y el `id` de Canvas visible en tipografía monoespaciada y no editable, para contraste. Antes de guardar nada se ejecutan dos guardas adicionales a las de §4.5.2:

- **2.b** ya exige matrícula de profesor activa en **ese** curso.
- **A-052**: si **todas** las matrículas de profesor activas del titular en ese curso traen `limit_privileges_to_course_section = true`, el ítem 3 del checklist sale `BLOQUEANTE` y la vinculación **no se completa**, con el mensaje: «Tu matrícula de profesor está limitada a la sección *X*. Con esa limitación Canvas puede devolvernos un curso incompleto sin avisar, y la aplicación interpretaría a media clase como retirada. Pide en Canvas una matrícula sin limitación de sección, o vincula el curso con la credencial de otro profesor que no la tenga.»

**Curso ya vinculado a otro curso de la aplicación:** su tarjeta **aparece, deshabilitada**, con la etiqueta «ya vinculado a *nombre del curso de la aplicación*» (A-027, A-028). No se oculta, porque ocultarla haría que el profesor buscase un curso que ve en Canvas y no encuentra aquí.

### 4.5.4 Estados vacíos de la lista, con causa distinguida

| Causa | Qué se muestra | Acción |
|---|---|---|
| El token es válido pero no tiene ninguna matrícula de profesor activa | «Tu cuenta de Canvas no figura como profesora de ningún curso activo en *instancia*» | Enlace a Canvas y botón «usar otro token» |
| Sólo tiene cursos no publicados o concluidos | «No hay cursos activos. Puedes ver también los concluidos y los no publicados» | Botón «Mostrar también concluidos y no publicados», que repite la llamada sin `enrollment_state=active`; el ítem 2 del checklist sigue siendo bloqueante si el curso no está publicado |
| La llamada falló | Explicación en español más el texto literal de Canvas debajo | Botón «reintentar» |

### 4.5.5 Errores del pegado, contrato completo

| Caso | Detección | Desenlace |
|---|---|---|
| Token inválido o revocado | `2.a` falla | «El token no es válido. Genera uno nuevo desde tu perfil de Canvas» |
| Titular sin matrícula de profesor en ese curso | `2.b` falla | «Este token pertenece a alguien que no es profesor de ese curso» |
| Identidad ya vinculada a otro usuario de la aplicación | `2.c` falla | Rechazo, incidencia |
| Identidad distinta de la registrada previamente | `2.d` falla | Rechazo con la diferencia mostrada |
| Curso de Canvas ya vinculado | unicidad `(canvas_base_url, canvas_course_id)` | Rechazo nombrando el curso de la aplicación que lo ocupa (A-027) |
| Profesor limitado a una sección | `limit_privileges_to_course_section = true` en todas sus matrículas de profesor | Bloqueo de A-052, §4.5.3 |
| Instancia no reconocida | `canvas_base_url` fuera de la lista blanca | Rechazo explícito, no se intenta la llamada |

**Idempotencia:** el paso 2 es reejecutable sin efectos duplicados. La escritura de la credencial es un *upsert* sobre `credencial_canvas (curso_id, usuario_id)`, de modo que un doble clic o un reintento del navegador no producen dos credenciales.

### Criterios de aceptación de 4.5

| Id | Comprobación |
|---|---|
| CA-4.5-01 | Pegar el token de una persona que no tiene matrícula de profesor en el curso elegido se rechaza con el mensaje de la comprobación 2.b, sin crear ninguna fila |
| CA-4.5-02 | Elegir de la lista un curso de Canvas ya vinculado a otro curso de la aplicación es rechazado nombrando el curso ocupante, nunca con un `500` |
| CA-4.5-03 | Un titular con `limit_privileges_to_course_section = true` en todas sus matrículas de profesor no puede completar la vinculación, y el mensaje ofrece las dos salidas: pedir matrícula sin limitación, o usar la credencial de otro profesor |
| CA-4.5-04 | La lista de cursos disponibles nunca requiere que el profesor escriba un identificador numérico; no existe ningún campo de texto libre para el `canvas_course_id` en la interfaz |
| CA-4.5-05 | Repetir el pegado del mismo token dos veces seguidas no crea una segunda fila de `credencial_canvas`; la segunda escritura es un *upsert* sobre la primera |

---

## 4.6 Paso 3 — Vinculación con GitHub (R2.1.5)

### 4.6.1 Qué se instala, y cuándo

**No se pega ninguna credencial. Se instala la GitHub App**, que es pública (A-057), en la organización del curso. El botón «Instalar en mi organización de GitHub» lleva a `https://github.com/apps/<nombre-app>/installations/new?state=<jwt>`, donde el `state` es un JWT de **15 minutos** con `curso_id`, `usuario_id` y un `jti` de un solo uso (A-058). Al volver, la aplicación resuelve el curso por ese `state`: **el profesor no copia ningún identificador**.

**Guía previa, fijada como texto del archivo único de mensajes**, visible antes de pulsar el botón:

> Vas a instalar la aplicación en tu organización de GitHub. Al pulsar el botón te llevamos a GitHub. Allí verás una lista con tu cuenta personal y las organizaciones donde eres owner. Elige la organización del curso — no tu cuenta personal, porque los repositorios del curso deben vivir en una organización. Después GitHub te preguntará si la aplicación accede a *todos los repositorios* o a *sólo algunos*. Las dos opciones sirven: los repositorios que la aplicación cree quedan incluidos automáticamente. Vas a conceder cuatro permisos: crear y administrar repositorios, escribir su contenido, leer sus metadatos y administrar miembros de la organización. Los usamos sólo para crear los repositorios de tus estudiantes, darles acceso a ellos y dar acceso de lectura a tu equipo docente. La aplicación nunca invita a un estudiante a tu organización. Al terminar vuelves aquí solo. No tienes que copiar ningún identificador. Si no eres owner de la organización, GitHub enviará una solicitud a quien sí lo sea y nosotros te avisaremos cuando la aprueben. (`Q-2.1-34`)

El detalle técnico de la instalación, del token de instalación y de los permisos concedidos es del capítulo 6 (Integración con GitHub); este capítulo cubre el flujo que el profesor ve y decide.

### 4.6.2 El instante en que se crean el equipo docente y el repositorio de operaciones

**En el mismo paso 3, antes de crear ningún repositorio de estudiante**, la aplicación crea el equipo `docentes` de la organización y le da lectura, e incorpora a cada miembro activo del curso (A-163) — el mecanismo detallado de esa incorporación y su revocación es del capítulo 2, §2.8. También crea el repositorio `gestor-operaciones` (A-170), que no es de este capítulo salvo por el hecho de que nace aquí, en el mismo paso.

### 4.6.3 Los diez retornos posibles al volver de GitHub

| Retorno | Qué muestra y qué hace |
|---|---|
| `setup_action=install`, `installation_id` y `state` válidos | Se persiste `instalacion_github` y `curso.github_org_id`/`github_org_login`; se crea el equipo `docentes` y `gestor-operaciones`; paso 3 queda verde con el nombre de la organización a la vista |
| `setup_action=update` | Se refrescan `repository_selection` y permisos; «Actualizamos la configuración de la instalación» |
| `setup_action=request` (solicitud pendiente) | Paso 3 en ámbar, «Solicitud de instalación enviada» (§4.6.4) |
| Sin `installation_id` | «GitHub no nos devolvió ninguna instalación. Si cancelaste, puedes volver a intentarlo»; el curso sigue en `VINCULANDO` |
| `state` ausente, inválido o caducado | Pantalla de adopción explícita (§4.6.5); **nunca se vincula por deducción** |
| Instalación en una **cuenta personal**, no en una organización | Bloqueo: «R2.1.5 exige una organización. Desinstala la aplicación de tu cuenta personal e instálala en una organización», con enlace a la guía de creación |
| Esa organización ya está vinculada a otro curso | Rechazo nombrando el curso que la ocupa (A-028), con «una organización pertenece a un solo curso» y enlace a crear otra organización gratuita |
| `repository_selection = selected` | Se acepta: «La aplicación tiene acceso a los repositorios que elegiste, y también a todos los que cree ella misma, que es lo que necesita para esta tarea» |
| Permisos pendientes de aprobación | Se acepta, con la banda «Faltan permisos por aprobar en GitHub» |
| Tiempo de espera al leer la instalación | Se encola `verificar_instalacion_github` y la pantalla lo dice, con recarga automática |

### 4.6.4 El profesor no es owner de la organización

**No se bloquea la vinculación: se modela la espera como estado de primera clase.** Al volver sin `installation_id`, el paso 3 pasa a ámbar con «Solicitud de instalación enviada»: «Pediste instalar la aplicación en *org*. Un owner de esa organización tiene que aprobarla. Te avisaremos en cuanto ocurra; puedes cerrar esta página.» La detección de la aprobación tiene **dos vías simultáneas** — el webhook `installation` con acción `created`, y el trabajo `verificar_instalacion_github` cada hora — y **el curso avanza solo**, sin que el profesor tenga que volver a pulsar nada (`Q-2.1-35`).

### 4.6.5 Instalaciones huérfanas y su adopción

Una instalación **huérfana** —`state` caducado, faltó, o el profesor instaló desde la landing pública de la App sin pasar por el asistente— **no se descarta ni se adopta sola**. Queda registrada en `instalacion_github` con `curso_id` nulo, y el paso 3 ofrece un bloque **«Instalaciones sin curso»** con las que ese usuario puede adoptar, listadas con el `login` de la organización, la fecha de instalación y su alcance.

**Una instalación huérfana sólo se ofrece a un usuario si se cumple al menos una de estas dos condiciones, y la adopción exige además confirmación escrita que nombra la organización:**

- **(a)** el `sender` del webhook de instalación coincide con la cuenta de GitHub que ese usuario declaró en `/perfil`; o
- **(b)** la instalación ocurrió **dentro de los 30 minutos siguientes** a que ese mismo usuario, en esa misma sesión, pulsara «Instalar» para ese curso — hecho que se persiste en `intento_instalacion_github` al emitir el `state`, **antes** de salir a GitHub.

Si no se cumple ninguna, **la instalación no se ofrece a nadie**, y la única salida es reinstalar desde el asistente, que emite un `state` nuevo. Las instalaciones huérfanas no adoptadas a los 7 días abren una incidencia informativa en `/operacion`; **la aplicación nunca desinstala nada** (`Q-2.1-37`, A-030).

### Criterios de aceptación de 4.6

| Id | Comprobación |
|---|---|
| CA-4.6-01 | Instalar la App en la cuenta personal del profesor produce el bloqueo de §4.6.3 y no crea ninguna fila de `instalacion_github` con `curso_id` asignado |
| CA-4.6-02 | Instalar la App en una organización ya vinculada a otro curso es rechazado, nombrando el curso ocupante, sin crear una segunda fila `instalacion_github.curso_id` para esa organización |
| CA-4.6-03 | Con una instalación pendiente de aprobación del owner, el paso 3 queda en ámbar y se completa solo, sin acción del profesor, cuando llega el webhook `installation`/`created` o el sondeo horario lo detecta |
| CA-4.6-04 | Una instalación huérfana que no cumple ni la condición (a) ni la (b) no aparece en el bloque «Instalaciones sin curso» de ningún usuario |
| CA-4.6-05 | El equipo `docentes` y el repositorio `gestor-operaciones` existen antes de que se cree el primer repositorio de un estudiante, comprobado por orden de `creado_en` |

---

## 4.7 Paso 4 — Checklist de verificación (R2.1.6)

### 4.7.1 Mecanismo de ejecución

**El checklist se ejecuta como trabajo encolado, `ejecutar_checklist_vinculacion`, y la interfaz lo sondea cada 2 segundos; no se usan SSE ni WebSocket en ninguna pantalla** (RG-061). `POST /api/cursos/{id}/verificacion` encola el trabajo y responde `202` con `ejecucion_id`; `GET /api/cursos/{id}/verificacion/{ejecucion_id}` devuelve el estado de los ítems mientras llegan; `GET /api/cursos/{id}/verificacion/ultima` reconstruye la última pasada al recargar; `POST /api/cursos/{id}/verificacion/items/{item}` reejecuta un único ítem.

El trabajo ejecuta **dos carriles simultáneos, cada uno bajo su propio cerrojo por proveedor** (RG-062, §4.1): el de Canvas **en serie**, en el orden **1, 2, 3, 16, 4, 5, 6, 17, 7, 19, 11, 10, 8, 9, 13, 12, 15** —los bloqueantes primero—; el de GitHub **en paralelo**, ítems 14 y 18. Si el ítem 1 o el 2 salen `BLOQUEANTE`, los ítems de Canvas que dependen de ellos se escriben `NO_VERIFICADO` con motivo `DEPENDE_DE_ITEM_1` o `DEPENDE_DE_ITEM_2` y no se ejecutan; **el carril de GitHub continúa igualmente**.

**Tiempo de espera: 10 s por ítem, tope global 180 s.** Lo que no termine queda `NO_VERIFICADO` con motivo `TIEMPO_AGOTADO`, nunca en verde. Cada ítem se persiste en `verificacion_vinculacion` en cuanto termina, con su `ejecucion_id`, su `resultado` y la respuesta cruda en `detalle`.

### 4.7.2 Las 19 comprobaciones numeradas

| # | Comprobación | Llamada o fuente | Severidad |
|---|---|---|---|
| 1 | El token es válido y es tuyo | `GET /api/v1/users/self`, contrastado con §4.5.2 | **Bloqueante** |
| 2 | El curso existe, es visible y está publicado | `GET /api/v1/courses/:id?include[]=permissions` | **Bloqueante** |
| 3 | Eres profesor del curso y no estás limitado a una sección | `GET /courses/:id/enrollments?user_id=self&type[]=TeacherEnrollment` → `limit_privileges_to_course_section` | **Bloqueante si es `true`** (A-052) |
| 4 | Puedes editar notas | `permissions[]=manage_grades` | Advertencia fuerte (afecta a R2.7.6) |
| 5 | Puedes publicar anuncios | `permissions[]=post_to_forum`, `create_announcement` | Advertencia (R2.6.6 quedaría deshabilitado) |
| 6 | Puedes enviar mensajes | `permissions[]=send_messages`, `send_messages_all` | **Advertencia fuerte**: canal primario de R2.6.5 y R2.3.12; si sale rojo, el ítem 17 se vuelve bloqueante |
| 7 | Puedes ver correos de estudiantes | `permissions[]=read_email_addresses` | Informativo |
| 8 | Secciones legibles y detección de *cross-listing* | `GET /courses/:id/sections` → `nonxlist_course_id` | Advertencia (A-053) |
| 9 | Conjuntos de grupos colaborativos | `GET /courses/:id/group_categories` | Informativo (recuento) |
| 10 | Política de entrega tardía del curso | `GET /courses/:id/late_policy` | Advertencia fuerte |
| 11 | Períodos de calificación abiertos | `GET /courses/:id/grading_periods` → `is_closed` | Advertencia; **bloqueante al publicar** |
| 12 | Tamaño real de página que acepta la instancia | primera llamada al roster, `len(json)` y `Link` | Informativo, se persiste |
| 13 | Zona horaria del curso | `course.time_zone` | Informativo |
| 14 | La App está instalada, con sus permisos congelados y la organización presentable | `GET /app/installations/{id}` y `GET /orgs/{org}` — **seis sub-comprobaciones**, §4.7.3 | **Bloqueante** |
| 15 | Estudiantes legibles | recuento del roster | Advertencia si el curso está vacío |
| 16 | Puedes crear y editar tareas en Canvas | `permissions[]=manage_assignments`, `manage_assignments_add` | **Bloqueante**: vía principal de R2.2.4 y R2.2.5 |
| 17 | Puedes escribir comentarios en las entregas | `permissions[]=comment_on_submissions`, o prueba de escritura `17-bis` si la instancia no lo expone | Advertencia fuerte; **bloqueante si el ítem 6 salió rojo** |
| 18 | Cada docente del curso tiene membresía activa en la organización | lectura de `membresia_curso.org_github_estado`, **no llama a GitHub** | Advertencia (RG-064) |
| 19 | Puedes borrar anuncios propios | `permissions[]=moderate_forum` | Informativo: de él depende la limpieza de las pruebas de escritura |

**Dos pruebas de escritura opcionales, `5-bis` y `17-bis`**, ejecutadas **sólo si el profesor marca la casilla de consentimiento**, con tope de **20 s duros** cada una, fuera del trabajo encolado (son la escritura síncrona n.º 1 de las seis escrituras externas síncronas de esta especificación). Sin la casilla marcada, el ítem correspondiente queda `NO_VERIFICADO`, nunca verde.

- **`5-bis`** ejecuta la prueba en **dos pasadas**: un anuncio de verificación con `delayed_post_at` a un año vista, título con prefijo `[verificación app]` y `DELETE` inmediato — pasada 1 sin `specific_sections`, pasada 2 con `specific_sections` a la primera sección del curso. **Nunca se usa `published=false`.** Escribe `curso.via_anuncio_seccion ∈ {SECCION, CURSO, NINGUNA, NO_VERIFICADO}`: `SECCION` con las dos pasadas verdes; `CURSO` con la 1 verde y la 2 fallida —y entonces todo anuncio de sección se publica a todo el curso con una primera línea que lo advierte—; `NINGUNA` con las dos fallidas —y entonces R2.6.6 se declara incumplido en ese curso, en la interfaz y en la memoria de entrega—; `NO_VERIFICADO` si no se marcó la casilla.
- **`17-bis`** prueba la escritura de un comentario sobre una entrega, con el mismo régimen de casilla y de tope.

### 4.7.3 Las seis sub-comprobaciones del ítem 14

| Sub-comprobación | Fuente | Severidad |
|---|---|---|
| (a) La instalación existe y cubre la organización vinculada | `GET /app/installations/{id}` | **Bloqueante** |
| (b) El conjunto de permisos concedidos coincide exactamente con el congelado (`docs/permisos.md`) | misma llamada | **Bloqueante**; `detalle` enumera lo que falte o sobre |
| (c) Existe el repositorio `.github` de perfil | `GET /repos/{org}/.github` | Advertencia, nunca bloqueante por sí sola |
| (d) `default_repository_permission = none` | `GET /orgs/{org}` con token de instalación | **Bloqueante** (RG-135) |
| (e) `members_can_create_repositories = false` | misma llamada | **Bloqueante** (RG-135) |
| (f) Verificación en dos pasos exigida a todos los miembros, y dos owners nombrados | misma llamada | **Bloqueante** (RG-135) |

Las sub-comprobaciones `(d)`, `(e)` y `(f)` verifican la **configuración base de la organización**, que se hace **a mano y antes de vincular ningún curso** (RG-135, §4.1). Cuando un campo no es legible con el token de instalación, la sub-comprobación queda `NO_LEGIBLE` y **el ítem sólo se cierra con `VERIFICADO_A_MANO`**: un profesor lo firma en pantalla, declarando que lo comprobó en la interfaz de GitHub, con fecha y actor persistidos y registro en `bitacora` con `VERIFICACION_FIRMADA_A_MANO`.

### 4.7.4 Los cinco resultados posibles

`verificacion_vinculacion.resultado ∈ {CORRECTO, ADVERTENCIA, BLOQUEANTE, NO_VERIFICADO, VERIFICADO_A_MANO}`. El quinto **no se escribe nunca de forma automática**; es la única salida cuando una comprobación necesita un campo que la API no devuelve con el permiso disponible.

### Criterios de aceptación de 4.7

| Id | Comprobación |
|---|---|
| CA-4.7-01 | Ejecutado el checklist sobre un curso con el token válido y todos los permisos concedidos, los 19 ítems terminan en menos de 180 s y ninguno queda `NO_VERIFICADO` por tiempo agotado |
| CA-4.7-02 | Con el ítem 1 en `BLOQUEANTE`, los ítems de Canvas que dependen de él quedan `NO_VERIFICADO` con motivo `DEPENDE_DE_ITEM_1`, y el carril de GitHub (ítems 14 y 18) se ejecuta igualmente |
| CA-4.7-03 | `5-bis` sin la casilla marcada queda `NO_VERIFICADO`; marcada la casilla, produce una única fila con las dos pasadas en `detalle` y escribe `curso.via_anuncio_seccion` |
| CA-4.7-04 | Con `default_repository_permission` distinto de `none` y legible, el ítem 14 sale `BLOQUEANTE` y el curso no pasa a `ACTIVO` |
| CA-4.7-05 | Con `default_repository_permission` no legible con el token de instalación, el ítem 14 sólo puede cerrarse con `VERIFICADO_A_MANO`, firmado por un profesor con fecha y actor persistidos |
| CA-4.7-06 | El catálogo de `dominio/verificacion.py` tiene exactamente 21 entradas; una prueba automatizada falla la construcción si diverge en número, identificador o severidad de la tabla de este capítulo |

---

## 4.8 Qué pasa si una comprobación falla, y cómo se recupera

**Cada ítem en rojo lleva un botón que va exactamente al sitio donde se arregla** (A-040): un ítem de Canvas lleva a la pantalla de permisos de Canvas o al enlace profundo correspondiente; el ítem 14 lleva a la configuración de la organización en GitHub; el ítem 18 lleva a `/cursos/{id}/equipo`.

**Tratamiento según severidad:**

- **Bloqueante**: impide `curso.estado = ACTIVO`. La pantalla explica en una frase qué falta y qué hacer, y **no se crea ninguna fila ni se toca ningún estado** mientras siga en rojo (restricción transversal, capa 1 de este documento de especificación).
- **Advertencia** (incluida «advertencia fuerte»): no impide `ACTIVO`, pero degrada visiblemente la funcionalidad que depende de ella —por ejemplo, el ítem 6 en rojo mueve R2.3.12 al canal 2 (§4.9)— y queda visible en `/cursos/{id}/ajustes` mientras no se corrija.
- **Informativo**: no bloquea nada; alimenta datos de presentación (zona horaria, tamaño de página, recuentos).
- **`NO_VERIFICADO`**: el ítem no se pudo ejecutar (dependencia de otro ítem, tiempo agotado, o casilla de escritura no marcada). Nunca cuenta como verde.
- **`VERIFICADO_A_MANO`**: exclusivo del ítem 14 cuando un campo no es legible; exige firma de un profesor (§4.7.3).

**Todo ítem es reejecutable bajo demanda**, individualmente con `POST /api/cursos/{id}/verificacion/items/{item}` o el checklist entero con `POST /api/cursos/{id}/verificacion`, con el mismo cerrojo y el mismo sondeo.

**Degradación en tiempo de ejecución, no sólo en el checklist.** Cuando una llamada real —fuera del checklist— devuelve `401`, o un `403` clasificado como no transitorio, **con la sonda de credencial en verde**, se clasifica `LLAMADA_NO_AUTORIZADA`: la credencial **no se invalida**, se escribe una fila en `verificacion_vinculacion` con `origen = RUNTIME` y la `capacidad` afectada, el control de la interfaz correspondiente queda deshabilitado con el motivo escrito, se abre la incidencia del tipo que corresponde, y la capacidad vuelve a `DISPONIBLE` sólo cuando una ejecución posterior del checklist o una llamada con éxito lo demuestran (RG-065, A-193). El mapa cerrado de qué capacidad depende de qué endpoint y en qué estado degradado queda cada una —de Canvas y de GitHub— es del capítulo 5 y del capítulo 6 respectivamente; este capítulo sólo fija que ambos escriben en la misma tabla `verificacion_vinculacion` que el checklist, para que «qué puede hacer la aplicación en este curso» tenga una única fuente.

### Criterios de aceptación de 4.8

| Id | Comprobación |
|---|---|
| CA-4.8-01 | Cada ítem en rojo de la pantalla del paso 4 muestra un botón cuyo destino corresponde exactamente al sitio donde ese permiso o esa configuración se arregla |
| CA-4.8-02 | Reejecutar un único ítem con `POST /api/cursos/{id}/verificacion/items/{item}` actualiza sólo la fila de ese ítem, sin tocar el resultado de los demás |
| CA-4.8-03 | Una llamada real que devuelve `401` fuera del checklist escribe una fila `origen = RUNTIME` en `verificacion_vinculacion` y deshabilita únicamente el control afectado, sin invalidar la credencial ni desvincular el curso |
| CA-4.8-04 | Una capacidad degradada en tiempo de ejecución vuelve a `DISPONIBLE` sólo tras una comprobación posterior con éxito, nunca por el mero paso del tiempo |

---

## 4.9 Verificación de canales de comunicación

**Es un bloque distinto del checklist de 19 ítems, dentro del mismo paso 4 y en `/cursos/{id}/ajustes`**, porque comprueba algo que ninguna llamada a la API puede comprobar sola: que el mensaje se vea con ojos de estudiante, no sólo que el token tenga el permiso (`Q-2.6-02`).

**Qué se verifica, en tres piezas:**

1. **Medición empírica**, sobre la instancia institucional con la matrícula de estudiante de prueba: un mensaje directo y su llegada a la bandeja del estudiante; un comentario sobre una entrega y su visibilidad; un anuncio y su visibilidad efectiva contrastando `restrict_student_past_view`; si llega notificación por correo; y `GET /api/v1/search/recipients` comprobando que el estudiante de prueba aparece como destinatario válido — esta última no depende de nadie y se ejecuta siempre.
2. **El resultado se persiste por curso**, en `verificacion_canal (id, curso_id, canal, resultado, evidencia jsonb, verificado_por, verificado_en)`, único `(curso_id, canal)`, y en `curso.canal_comunicacion_activo ∈ {CONVERSACION, COMENTARIO_ENTREGA, BLOQUEADO}`. Un canal con permiso concedido (ítems 5, 6, 17, 19) y sin verificación de visibilidad se muestra en ámbar con «permiso concedido, visibilidad no verificada», **nunca en verde**.
3. **Plan de respaldo, ya fijado y sin variaciones**: canal 1 mensaje directo; canal 2 comentario en la entrega de la tarea de registro cuando el ítem 6 sale rojo y el 17 verde; canal 3, bloqueo declarado, cuando los dos salen rojos, y entonces R2.3.12 se declara incumplido en ese curso, en la interfaz y en la memoria de entrega. El mecanismo completo de envío por cada canal, sus plantillas y sus siete eventos de comunicación automática son de la especificación de R2.6.5–R2.6.7, no de este capítulo.

### Criterios de aceptación de 4.9

| Id | Comprobación |
|---|---|
| CA-4.9-01 | Un canal con el permiso de Canvas concedido pero sin `verificacion_canal` para ese `(curso_id, canal)` se muestra en ámbar, nunca en verde |
| CA-4.9-02 | Con los ítems 6 y 17 en rojo, `curso.canal_comunicacion_activo = BLOQUEADO` y la vinculación no se completa (§4.3.2) |
| CA-4.9-03 | `GET /api/v1/search/recipients` se ejecuta y se persiste aunque la matrícula de estudiante de prueba no esté disponible |

---

## 4.10 Re-vinculación y cambio de una vinculación existente

### 4.10.1 Sustituir o promover una credencial de Canvas

**Desde `/cursos/{id}/ajustes`, con `curso.administrar`**, la lista de credenciales del curso muestra, por titular, huella, estado, última validación con éxito y escrituras de los últimos 7 días, con tres acciones:

- **«Añadir la mía»**: sólo el propio titular, con las cinco comprobaciones de §4.5.2. Si no hay credencial operativa válida, entra de inmediato como `orden_respaldo = 0`, con el aviso en pantalla «a partir de ahora la aplicación escribirá en Canvas como *nombre*». Si ya hay una operativa válida, entra como respaldo (`max + 1`) y **no desplaza a nadie**.
- **«Hacer operativa la mía»**: acción explícita, con confirmación que **nombra a la persona desplazada**, aviso por correo a los profesores del curso y registro en `bitacora`.
- **«Retirar la mía»**: pasa la credencial a `RETIRADA` y promueve la siguiente del orden.

**Cambiar la credencial operativa invalida el checklist de Canvas y lo reencola, siempre y en la misma transacción** (RG-069):

1. Las filas vigentes de `verificacion_vinculacion` de los **diecisiete ítems de Canvas** —los 19 numerados menos el 14 y el 18, que son de GitHub— y de `5-bis` y `17-bis` pasan a `NO_VERIFICADO` con motivo `CREDENCIAL_CAMBIADA`. Las filas `origen = RUNTIME` de capacidades de Canvas se invalidan igual; las de GitHub no se tocan.
2. `curso.via_anuncio_seccion` vuelve a `NO_VERIFICADO`.
3. Se encola `ejecutar_checklist_vinculacion` de nuevo. **Las pruebas de escritura `5-bis` y `17-bis` no se reejecutan solas**: exigen que el **nuevo** titular marque su propia casilla.
4. El curso muestra una **banda ámbar** —no roja, porque nada está roto— con «la aplicación escribe ahora en Canvas como *nombre*; vuelve a ejecutar la verificación» y el botón directo al paso 4.

**Los trabajos que estaban `ESPERANDO_CREDENCIAL` se reanudan de inmediato** y no esperan a que el checklist se vuelva a ejecutar, porque condicionar la reanudación a un acto humano dejaría el curso parado indefinidamente justo después de un incidente.

### 4.10.2 Rehacer la vinculación con GitHub

Desde `/cursos/{id}/ajustes` está disponible «reinstalar GitHub», que reabre el paso 3. Dos casos se resuelven **sin que el profesor tenga que hacer nada explícito**:

- **Reinstalación de la misma organización** (`account.id` coincide con el `github_org_id` ya persistido): la aplicación **sustituye el `installation_id` anterior por el nuevo en la misma transacción**, deja el hecho en `bitacora` con los dos valores, cierra la incidencia de instalación perdida si estaba abierta, y **reanuda los trabajos que estaban `BLOQUEADO`**. No exige revincular ni tocar ningún repositorio: los repositorios se identifican por `github_repo_id`, no por instalación (`Q-2.1-38`).
- **Renombre de la organización**: `org_login` es un dato de presentación mutable, refrescado en cada ejecución del trabajo periódico de verificación de instalación. Un renombre no rompe nada y no exige revincular.

**Desinstalación de la App**: el curso pasa a `GITHUB_DESVINCULADO` (§4.3.2), se abre incidencia bloqueante, los trabajos de GitHub se encolan en `BLOQUEADO` y **no se borra nada**. El paso 3 queda disponible para reinstalar.

**Suspensión de la instalación**: `instalacion_github.suspendida` cambia y el curso muestra la banda correspondiente; la reanudación es automática al llegar la acción `unsuspend`.

### 4.10.3 Rehacer el checklist

El checklist es reejecutable en cualquier momento, completo o ítem a ítem, con `curso.administrar`, desde el paso 4 del asistente o desde `/cursos/{id}/ajustes`. No existe límite de reejecuciones ni ventana de enfriamiento distinta del cerrojo por proveedor que ya serializa el tráfico con Canvas y con GitHub.

### Criterios de aceptación de 4.10

| Id | Comprobación |
|---|---|
| CA-4.10-01 | Promover una credencial de respaldo a operativa exige confirmación que nombra a la persona desplazada, y queda registrada en `bitacora` |
| CA-4.10-02 | Cambiar la credencial operativa deja los diecisiete ítems de Canvas en `NO_VERIFICADO` con motivo `CREDENCIAL_CAMBIADA`, sin tocar los ítems 14 y 18 |
| CA-4.10-03 | Tras cambiar la credencial, los trabajos `ESPERANDO_CREDENCIAL` se reanudan sin esperar a que el checklist termine de reejecutarse |
| CA-4.10-04 | Reinstalar la App sobre la misma organización sustituye `installation_id` sin crear ningún repositorio nuevo ni alterar los existentes |
| CA-4.10-05 | Un renombre de la organización en GitHub se refleja en `curso.github_org_login` en menos de una hora, sin ninguna acción del profesor |

---

## 4.11 Casos borde de la vinculación

| Caso | Resolución | Fuente |
|---|---|---|
| Curso de Canvas ya vinculado por otro curso de la aplicación | Tarjeta deshabilitada en el selector con «ya vinculado a *nombre*»; rechazo por unicidad `(canvas_base_url, canvas_course_id)`, nunca `500` | A-027, `Q-2.1-12`, `Q-2.1-25` |
| Organización de GitHub ya vinculada a otro curso | Rechazo en el retorno de instalación, nombrando el curso ocupante; salida ofrecida: crear otra organización gratuita | A-028, `Q-2.1-12`, `Q-2.1-34` |
| Token inválido | Rechazo en la comprobación 2.a, «el token no es válido» | A-033 |
| Token de alguien que no es profesor del curso | Rechazo en la comprobación 2.b | A-033 |
| Curso de Canvas sin permisos suficientes (notas, anuncios, mensajes, tareas, comentarios) | No bloquea la vinculación salvo el ítem 16 (bloqueante); los demás degradan a advertencia con el canal de respaldo correspondiente | §4.7.2 |
| Profesor limitado a una sección (`limit_privileges_to_course_section`) | Vinculación bloqueada con las dos salidas escritas | A-052, ítem 3 |
| Instalación de la App en cuenta personal en vez de organización | Bloqueo con salida: desinstalar y reinstalar en una organización | `Q-2.1-35` |
| Profesor no es owner de la organización | Estado «Solicitud de instalación enviada»; se completa solo al aprobarse | `Q-2.1-35` |
| Instalación huérfana (sin `curso_id`) | Se ofrece con guarda de adopción (sender o ventana de 30 min); nunca automática | `Q-2.1-37` |
| Organización sin cupo de invitaciones | **No es un caso real bajo este diseño**: el paso 3 sólo incorpora al equipo docente del curso, presupuestado en ≤ 15 invitaciones a la organización por curso, muy por debajo del límite de 50 cada 24 h de una organización nueva o gratuita; los estudiantes no consumen cupo de organización porque entran como colaboradores de repositorio | §1.3 de ARQUITECTURA.md, A-163 |
| Reinstalación de la App sobre la misma organización | Auto-reparación: sustitución del `installation_id`, sin tocar repositorios | `Q-2.1-38` |
| Renombre de la organización de GitHub | Se refresca sola; no exige revincular | `Q-2.1-38` |
| Desinstalación de la App | `curso.estado = GITHUB_DESVINCULADO`; nada se borra | `Q-2.1-38` |
| Revocación o expiración del token de Canvas tras `ACTIVO` | `curso.estado = CANVAS_DESVINCULADO`; promoción automática de respaldo si existe; escrituras encoladas, nunca descartadas | A-036 (mecanismo detallado en el capítulo 5) |
| Cross-listing de secciones de Canvas | La sección se sincroniza igual; advertencia en el ítem 8 | A-053 |
| Ambos canales de comunicación caídos (ítems 6 y 17 en rojo) | Vinculación bloqueada; R2.3.12 declarado sin canal en ese curso | `Q-2.1-19`, §4.9 |

### Criterios de aceptación de 4.11

| Id | Comprobación |
|---|---|
| CA-4.11-01 | Cada fila de la tabla de casos borde de este capítulo tiene un mensaje de interfaz verificable y una prueba automatizada asociada |
| CA-4.11-02 | Ningún caso borde de vinculación produce un `500`: todos resuelven en un rechazo con mensaje, un estado ámbar o un estado bloqueante con salida escrita |
| CA-4.11-03 | El presupuesto de invitaciones a la organización durante la vinculación de un curso nunca supera 15 llamadas, medido en el registro de `bitacora` de ese curso |

---

## 4.12 Reparto entre la entrega parcial y la final

**R2.1.4, R2.1.5 y R2.1.6 están completos el 16 de septiembre de 2026, con las 19 comprobaciones del checklist y sus dos pruebas de escritura opcionales** (capítulo 1, §1.11; A-157). Entre el 17 de septiembre y el 6 de octubre sólo se afinan textos de guía; ninguna funcionalidad de este capítulo queda pendiente para la entrega final. Es, además, el tramo que ocupa los pasos 2 a 5 del guion de demostración del 16 de septiembre: pegar el token y elegir el curso (1 min), instalar la App en la organización (1 min), y ejecutar el checklist mostrando deliberadamente un ítem en ámbar y cómo se explica (1,5 min).

La organización de GitHub se configura a mano —los cuatro valores bloqueantes del ítem 14, `(d)`, `(e)` y `(f)`— **antes del 13 de septiembre**, fecha en que se crea el curso de demostración, precisamente para que ese ítem no se descubra en rojo el mismo día de la entrega (RG-135, §4.7.3).

### Criterios de aceptación de 4.12

| Id | Comprobación |
|---|---|
| CA-4.12-01 | El 16 de septiembre, un curso nuevo recorre los cuatro pasos del asistente hasta `ACTIVO` sin que ninguna pantalla muestre «próximamente» ni un control sin motivo escrito |
| CA-4.12-02 | La configuración base de la organización de GitHub está escrita en `docs/operacion.md` con fecha anterior al 13 de septiembre de 2026 |
| CA-4.12-03 | Ningún ítem del checklist, ni las dos pruebas de escritura, dependen de ninguna bandera de `PERFIL_ALCANCE` |
