# Capítulo 1 — Introducción, alcance y actores

**Proyecto 2 · ICC4201 Desarrollo de Software · 202620 · Universidad de los Andes**

| | |
|---|---|
| Estado del capítulo | Normativo |
| Qué fija | Qué es el sistema, qué problema resuelve, quién lo usa y quién no, el vocabulario del dominio, el alcance incluido, el alcance explícitamente excluido y las restricciones que atraviesan todos los demás capítulos |
| Autoridad sobre la que se apoya | `docs/enunciado-proyecto2.md` (59 requisitos `R2.x.y`) → las cuatro actas de reconciliación (`RG-nnn`) → `docs/ARQUITECTURA.md` (`A-001` a `A-235`) → las 590 respuestas de alcance |
| Entrega parcial | miércoles 16 de septiembre de 2026, 13:30, presencial |
| Entrega final | martes 6 de octubre de 2026, 16:00 |
| Actividad de validación individual | miércoles 7 de octubre de 2026 |
| Aplicación en pie hasta | **31 de octubre de 2026 inclusive** (A-161) |
| Desmantelamiento del despliegue | 1 de noviembre de 2026 |

Este capítulo está escrito en voz de especificación. **Cada afirmación es una decisión tomada y verificable, no una opción a evaluar.** Quien implemente a partir de aquí no necesita volver a consultar las fuentes: lo que este capítulo no dice, lo dicen los capítulos siguientes, y lo que este capítulo declara fuera de alcance no se construye.

---

## 1.1 Propósito del sistema

La aplicación es una **herramienta web de apoyo al equipo docente** de un curso universitario de programación. Coordina, en un solo lugar, la información académica que vive en **Canvas LMS** —estudiantes, secciones, grupos, tareas, fechas de entrega y rúbricas— con los **repositorios de GitHub** en los que los estudiantes desarrollan su trabajo, y automatiza la creación y administración de esos repositorios, el seguimiento del avance y el reparto de la corrección.

El sistema cumple cinco funciones nucleares, y ninguna más:

| # | Función nuclear | Qué significa exactamente | Requisitos |
|---|---|---|---|
| 1 | **Vincular** | Un curso de la aplicación se vincula a un curso de Canvas y a una organización de GitHub, con un asistente que guía y con un checklist de **19 comprobaciones numeradas** que permite al profesor verificar que la configuración quedó correcta | R2.1.3 – R2.1.6 |
| 2 | **Enrolar** | Mantener el espejo de estudiantes, secciones y grupos traído de Canvas, y establecer la correspondencia entre cada estudiante y su cuenta de GitHub sin que el estudiante entre nunca a la aplicación | R2.2.1 – R2.2.6 |
| 3 | **Aprovisionar** | Crear automáticamente y de forma progresiva los repositorios de cada estudiante o grupo, con nombre inequívoco, con los archivos del repositorio base cuando lo haya, y con los colaboradores correctos, sin que nadie pulse un botón | R2.3.1 – R2.3.12 |
| 4 | **Registrar y seguir** | Registrar la versión inmutable del repositorio correspondiente a la fecha de cierre de cada entrega, y presentar de forma inmediata el estado y la actividad de todos los repositorios de una tarea | R2.4.1 – R2.4.8, R2.5.1 – R2.5.10 |
| 5 | **Informar y corregir** | Producir el informe docente diario, comunicar con los estudiantes por los canales de Canvas, repartir las entregas entre correctores y publicar las calificaciones en Canvas | R2.6.1 – R2.6.7, R2.7.1 – R2.7.7 |

**La aplicación no sustituye a Canvas ni a GitHub: los coordina.** Las calificaciones y las rúbricas viven en Canvas (§2.7 del enunciado); el código y su historia viven en GitHub. La aplicación mantiene un espejo de ambos y produce la evidencia que ninguno de los dos produce por sí solo.

### Criterios de aceptación de 1.1

| Id | Comprobación |
|---|---|
| CA-1.1-01 | Cada una de las cinco funciones nucleares es alcanzable desde la navegación de la aplicación por un usuario con el rol de menor privilegio que el requisito correspondiente nombra, sin escribir una URL a mano |
| CA-1.1-02 | Ninguna calificación de estudiante se encuentra persistida en ninguna tabla de la aplicación: la prueba automatizada que busca las claves `grades`, `score` y `grade` en los modelos de las tablas espejo falla la construcción si aparece alguna |
| CA-1.1-03 | La vista de una tarea se pinta sin ejecutar ninguna llamada a la API de GitHub ni de Canvas durante la petición HTTP, comprobado con el registro de llamadas externas de esa petición |

---

## 1.2 El problema que resuelve

Hoy la gestión de una tarea de programación obliga al equipo docente a operar a mano sobre dos plataformas que no se conocen entre sí. Los cinco costes concretos que el sistema elimina:

| # | Problema | Coste actual | Cómo lo resuelve el sistema |
|---|---|---|---|
| 1 | **No hay puente entre la identidad de Canvas y la de GitHub** | El equipo pide los usuarios de GitHub por correo o por planilla y los cruza a mano contra el roster | Tabla `mapeo_github`, *append-only*, alimentada por cuatro vías, con doble unicidad garantizada en base de datos (R2.2.4, R2.2.5) |
| 2 | **Crear los repositorios es trabajo manual y proporcional al número de estudiantes** | Con 200 estudiantes y 3 tareas son 600 repositorios creados, nombrados e invitados a mano | Aprovisionamiento progresivo y automático, sin interacción de un usuario, con estado por repositorio y motivo escrito cuando falta algo (R2.3.7, R2.3.10, R2.3.11) |
| 3 | **La fecha de cierre real de un estudiante no es una sola fecha** | Fechas por sección, extensiones por estudiante y por grupo, y cambios posteriores en Canvas, que nadie reconcilia | `fecha_efectiva` materializada por `(entrega, sujeto)` con su `origen` y su regla aplicada, resincronizada por huella de fechas (R2.4.1 – R2.4.4) |
| 4 | **El repositorio sigue vivo después del cierre** | Corregir «lo que había el día de la entrega» exige que alguien mire la fecha de cada commit | `version_entrega` registra el `commit_sha` a la fecha de cierre, es inmutable y sobrevive a toda actividad posterior (R2.4.5 – R2.4.7) |
| 5 | **El avance del curso no es observable** | Para saber quién no ha empezado hay que abrir repositorio por repositorio | Espejo persistido de la actividad, con tablero inmediato, identificación de repositorios sin actividad reciente y de estudiantes sin participación, e informe docente diario (R2.5.1 – R2.5.10, R2.6.1, R2.6.2) |

### Criterios de aceptación de 1.2

| Id | Comprobación |
|---|---|
| CA-1.2-01 | Con un estudiante sin cuenta de GitHub declarada, la pantalla Pendientes lo nombra y dice qué falta, sin que el evaluador tenga que buscarlo |
| CA-1.2-02 | Creada una tarea con sujetos aprovisionables, los repositorios aparecen creados sin que ningún usuario pulse un control, y el registro de aprovisionamiento muestra las transiciones con hora y **sin actor humano** |
| CA-1.2-03 | Una entrega con fechas distintas por sección muestra, por sujeto, la fecha efectiva y su `origen` (`BASE`, `SECCION`, `GRUPO` o `ADHOC`) |
| CA-1.2-04 | Registrada la versión de una entrega, un `push` posterior al repositorio no altera el `commit_sha` registrado |

---

## 1.3 Contexto de operación y sistemas externos

La aplicación opera contra cuatro sistemas externos y ninguno más.

| Sistema | Qué aporta | Credencial | Regla dura |
|---|---|---|---|
| **Canvas LMS** (instancia institucional del curso) | Estudiantes, secciones, grupos, tareas, fechas, rúbricas, calificaciones, mensajes y anuncios | **Token de acceso personal generado por el propio profesor** (A-031). Sólo el titular pega su propio token (A-033) | Toda escritura en Canvas aparece firmada por el titular del token, sea quien sea el ayudante que la originó, y así se declara en la interfaz (A-142) |
| **GitHub.com** | Organización del curso, repositorios, colaboradores, equipos, webhooks y actividad | **GitHub App pública** (A-057). No se persiste ningún token de GitHub: los de instalación se obtienen en caliente (A-038) | La aplicación nunca modifica ni elimina un objeto de GitHub cuyo identificador no proceda de una fila propia |
| **Google** (OpenID Connect) | Identidad de los usuarios de la aplicación | Authorization Code + PKCE, `prompt=select_account` siempre (A-018) | Se acepta el alta sólo con `email_verified = true` y dominio exactamente `gmail.com`; **se rechaza todo correo con reclamación `hd`** |
| **Proveedor transaccional de correo** | Informe diario y alertas operativas | Clave de servicio en variable de entorno | Cuota diaria del despliegue repartida en tres reservas; ninguna comunicación se descarta, se difiere (A-133, RG-197) |

**Infraestructura declarada:** backend FastAPI sobre Python 3.12, empaquetado como imagen Docker y desplegado en **Render** (A-001); frontend React desplegado en **Vercel** (A-002); base de datos **PostgreSQL en Supabase** (A-005); dos entornos completos y separados, `ensayo` y `produccion` (A-006); repositorio único, monorepo y **público**, del equipo (A-011).

### Las cinco restricciones del entorno, que ninguna decisión posterior puede ignorar

| # | Restricción | Consecuencias que se aceptan como marco |
|---|---|---|
| **1** | **El equipo tiene rol de PROFESOR en Canvas, no de administrador de cuenta** | No hay Developer Key propia para OAuth2 en el caso general; **no hay suplantación** (`as_user_id` exige el permiso «Become other users»); no hay informes de cuenta ni acceso garantizado a `sis_user_id`, por lo que la clave de identidad del estudiante es `canvas_user_id` (A-074); **la aplicación no crea cursos en Canvas**, los vincula; el roster puede llegar recortado si la matrícula del titular está limitada a una sección, y el asistente lee ese indicador y bloquea (A-052). **Toda decisión que dependa de privilegios de administrador de Canvas está mal planteada y queda descartada de antemano** |
| **2** | **Canvas Free-for-Teacher ya no existe** | El desarrollo y la demostración se hacen contra la instancia institucional del curso. No se planifica ningún camino que dependa de FFT |
| **3** | **La organización de GitHub es nueva y de plan gratuito** | No hay *rulesets* ni protección de ramas en repositorios privados: un tag de entrega es borrable por cualquiera con permiso de push, y de ahí que la evidencia sea el `commit_sha` persistido y no el tag. Los cupos de invitación obligan a que los estudiantes entren como **colaboradores de repositorio** y no como miembros de la organización; el único consumo del cupo de organización es el equipo docente, con presupuesto declarado de **≤ 15 invitaciones por curso** |
| **4** | **Los estudiantes NO son usuarios de la aplicación** | La aplicación no expone ninguna pantalla para estudiantes, ni de sólo lectura. Se desarrolla en 1.5 |
| **5** | **Dos despliegues en dominios distintos** | Backend y frontend viven en orígenes distintos, lo que obliga a resolver CORS, sesión entre sitios y origen del backend de forma explícita (A-008, A-009) |

### Las cinco leyes del diseño

Toda decisión de los capítulos siguientes es aplicación de una de estas cinco leyes. **Si una decisión futura las contradice, la decisión está mal.**

| Ley | Enunciado | Por qué es requisito y no preferencia |
|---|---|---|
| **Ley 1 — Espejo, no caché** | La base de datos es un espejo mantenido de Canvas y de GitHub. Todo lo que alimente una lista, un tablero, una decisión de un trabajo de fondo o un registro histórico se persiste con su marca de origen y de sincronización. **Ninguna vista consulta una API externa para renderizarse** | **R2.5** exige la información «de forma inmediata al ingresar a la vista de una tarea, sin requerir esperar a que se recopile en ese momento la actividad de todos los repositorios» |
| **Ley 2 — Nada se sobreescribe, todo se supersede** | Versiones de entrega, mapeos, fechas efectivas y publicaciones de nota son *append-only* con una fila vigente | **R2.4.6**, **R2.4.7** y **R2.7.6** exigen trazabilidad que editar en sitio destruiría |
| **Ley 3 — La clave es la duradera, no la legible** | Se persiste siempre el identificador estable del sistema externo (`canvas_user_id`, `canvas_enrollment_id`, `github_user_id`, `github_repo_id`); el nombre legible es un atributo mutable | Un login de GitHub renombrado **queda libre para que otra persona lo reclame**: un modelo con `login` como clave es un modelo roto |
| **Ley 4 — La evidencia vive en nuestra base de datos** | El `commit_sha` persistido es la evidencia normativa de una entrega; el tag de Git es una comodidad de navegación | Con organización Free no hay *rulesets* en repositorios privados, de modo que el tag es borrable y no puede ser la verdad |
| **Ley 5 — Un límite de una API externa nunca se pinta como error del equipo** | Se pinta como estado transitorio, con la hora de reintento visible | GitHub advierte que seguir pidiendo mientras se está limitado puede acabar en el baneo de la integración |

### Criterios de aceptación de 1.3

| Id | Comprobación |
|---|---|
| CA-1.3-01 | Ninguna llamada del sistema a Canvas incluye el parámetro `as_user_id`, comprobado con una prueba de arquitectura sobre el cliente de Canvas |
| CA-1.3-02 | Un intento de alta con un correo que trae reclamación `hd` se rechaza con un mensaje que dice que el enunciado exige una cuenta de `gmail.com` |
| CA-1.3-03 | Toda llamada mutante a GitHub construye su URL a partir de un identificador leído del modelo propio; la prueba de arquitectura correspondiente falla la construcción si aparece una que no lo hace |
| CA-1.3-04 | Alcanzado el límite de tasa de GitHub, la interfaz muestra estado transitorio con la hora de reintento y **no** un mensaje de error del equipo |

---

## 1.4 Actores

Un **actor** es toda entidad, humana o automática, que interactúa con la aplicación. La lista es cerrada.

| Actor | Quién es | Cómo entra | Qué hace |
|---|---|---|---|
| **Profesor de curso** | Persona con `membresia_curso` de rol `PROFESOR` y estado `ACTIVA` en ese curso | Sesión con Google OIDC; se convierte en profesor al **crear** un curso o al ser **promovido** por otro profesor | Los nueve permisos, de forma implícita e irrevocable. Vincula, administra el equipo y las credenciales, crea tareas, corrige, publica notas y comunica |
| **Ayudante de curso** | Persona con `membresia_curso` de rol `AYUDANTE` y estado `ACTIVA` | Sesión con Google OIDC, siempre por **invitación nominal** de un profesor a una dirección `gmail.com` | Dos permisos implícitos más el subconjunto de **cinco concedibles** que el profesor le haya otorgado |
| **Evaluador (profesor y ayudantes del ramo)** | No es un rol nuevo: es una persona que entra por los caminos anteriores | Como **AYUDANTE** del curso de demostración con los **cinco permisos concedibles**, y como **PROFESOR** de un curso de ensayo propio, con su propia organización de GitHub | Recorre la aplicación entera. **No existe modo de sólo lectura y ninguna acción se capa para él**: §4 del enunciado exige que las funcionalidades sean accesibles en el uso |
| **Responsable de disponibilidad y titulares de bandera** | Integrantes del equipo nombrados en `.workflow/responsables.md` | Como cualquier otro usuario, con membresía **`ACTIVA` de rol `PROFESOR` en el curso de demostración**, que es condición para entrar a `/operacion` | Verifican criterios de aceptación, reintentan trabajos, toman respaldos, restauran |
| **Estudiante** | Persona con matrícula de estudiante en el curso de Canvas | **No entra.** Actúa exclusivamente en Canvas y en GitHub | Declara su cuenta de GitHub entregando en una tarea de Canvas, lee mensajes y anuncios en Canvas, acepta la invitación en GitHub, hace *push* |
| **GitHub** (actor automático) | La organización del curso, a través de la instalación de la GitHub App | `POST /webhooks/github`, autorizado por firma `X-Hub-Signature-256` sobre el cuerpo crudo | Notifica `push`, `create`, `delete`, `repository`, `member`, `installation` e `installation_repositories` |
| **Vigilante externo** (actor automático) | Dos *workflows* de GitHub Actions alojados fuera del proceso vigilado | `POST /interno/latido`, autorizado por HMAC del vigilante; y `GET /salud` y la forma anónima de `GET /estado` | Comprueba cada 10 y cada 5 minutos que el planificador y el servicio están vivos, y abre incidencia y alerta por correo cuando no |
| **Monitor anónimo** | Cualquiera | `GET /salud` (pública, sin límite) y `GET /estado` en su **forma anónima**, con booleanos y contadores agregados y **sin un solo nombre ni identificador de curso** | Comprueba que el servicio responde |

**Nota sobre las vías de acceso compartidas.** Si un evaluador prefiere no facilitar una dirección `gmail.com`, la entrega ofrece una cuenta `gmail.com` creada por el equipo. **Es una vía de acceso, no un usuario compartido**: recibe exactamente los cinco permisos concedibles, se marca en `/cursos/{id}/equipo` como **«vía de acceso compartida»** mediante `membresia_curso.es_via_compartida`, esa marca aparece junto al nombre en toda vista donde la persona figure, su uso queda en `bitacora`, y la entrega declara por escrito que **la autoría registrada es la de la cuenta y no la de la persona que la usó**. Su retirada es el 1 de noviembre y consiste en tres actos: retirar la membresía de cada curso, sacarla del equipo `docentes` y de la organización, y **cambiar la contraseña de la cuenta de Google**.

### Criterios de aceptación de 1.4

| Id | Comprobación |
|---|---|
| CA-1.4-01 | Un usuario recién registrado y no invitado ve en `/cursos` un estado vacío que dice con esas palabras que aún no es profesor ni ayudante de ningún curso, ofrece «Crear un curso» y nombra el curso de demostración y la dirección de contacto |
| CA-1.4-02 | Un usuario **sin ninguna membresía `ACTIVA` de rol `PROFESOR`** recibe `404` en `/operacion`, en `/operacion/invariantes` y en todo `/api/operacion/**`, y la entrada a `/operacion` no aparece en su navegación |
| CA-1.4-03 | `GET /estado` sin sesión devuelve la forma anónima y no contiene ningún nombre ni identificador de curso |
| CA-1.4-04 | Una membresía marcada `es_via_compartida` muestra el distintivo «vía de acceso compartida» junto al nombre en `/cursos/{id}/equipo` y en toda vista que nombre al miembro |

---

## 1.5 Quién no es actor

Esta sección es tan normativa como la anterior. **Lo que aquí se declara no-actor no recibe pantalla, ni ruta, ni sesión, ni excepción.**

| No-actor | Por qué | Consecuencia dura |
|---|---|---|
| **El estudiante** | §1 y §2.3 del enunciado lo dicen dos veces: «los estudiantes no serán usuarios de la aplicación: toda su interacción deberá realizarse a través de Canvas y GitHub» | Se adopta la **interpretación estricta**: ningún estudiante abre jamás una URL de la aplicación, **ni siquiera una página sin sesión accedida por enlace firmado**. No hay alta de estudiante, no hay sesión de estudiante, no hay ruta pública de estudiante, no hay página «tu versión registrada», y queda descartado de raíz el enrolamiento por OAuth de GitHub del estudiante |
| **El administrador de la cuenta de Canvas** | La aplicación opera con rol de profesor. Las peticiones al administrador de la instancia son actos del equipo, por escrito y fuera de la aplicación | Ninguna funcionalidad depende de un privilegio de administrador de Canvas |
| **Un administrador global de la aplicación** | **No existe, y se descarta a propósito.** §2.1 del enunciado organiza la aplicación «en torno a cursos administrados por profesores», y un rol capaz de entrar a todos los cursos sería el mayor agujero de privacidad del sistema, sobre datos de estudiantes reales | La administración es **por curso**, la ejerce cualquier profesor de ese curso, y cada persona administra su propia cuenta en `/perfil`. **No se entrega ninguna credencial de administrador porque no existe ninguna** |
| **El propietario de la organización de GitHub como usuario** | Configura la organización a mano una vez, antes de vincular ningún curso | Los cuatro valores de configuración base de la organización quedan escritos en `docs/operacion.md`; la aplicación no los administra |
| **El público anónimo** | Existe una **lista cerrada de dieciséis rutas sin sesión**, cada una con lo que la autoriza y su limitador de tasa; ninguna otra ruta puede quedar fuera de la dependencia de autorización | Toda ruta bajo `/api/**` que no figure en esa lista exige sesión, con 300 peticiones por minuto y `sesion_id` |

**Cómo se defiende la regla del estudiante, y no es por disciplina.** Existe una prueba de arquitectura que recorre todas las rutas registradas en el enrutador real y **falla la construcción** si aparece una ruta accesible sin sesión que no figure en la lista cerrada de rutas públicas. La verificación de propiedad de la cuenta de GitHub, que un flujo de OAuth del estudiante daría, se sustituye por tres mitigaciones que se implementan enteras:

1. El candidato se valida contra la API de GitHub y **se persiste el login canónico devuelto por la API**, nunca lo tecleado; se rechaza si resuelve a una organización.
2. La doble unicidad parcial del mapeo impide que dos estudiantes del mismo curso reclamen la misma cuenta.
3. **Sólo quien controla la cuenta puede aceptar la invitación de GitHub**, de modo que un login mal escrito se delata solo: su invitación nunca se acepta y el estudiante aparece nombrado en Pendientes a las 48 horas.

Además, una cuenta de GitHub **no puede ser a la vez del equipo docente y de un estudiante**: la comprobación es simétrica, vive en una única función de dominio, se ejecuta en las dos puertas de entrada —al validar un mapeo y al declarar la cuenta de un docente— y se repite inmediatamente antes de incorporar a alguien a la organización; una colisión sobrevenida abre incidencia y la decide una persona, nunca se resuelve sola.

**Dónde se dice al usuario.** En `/cursos/{id}/personas`, junto a la tarea de registro, hay una línea permanente: «Los estudiantes no entran a esta aplicación. Declaran su cuenta en Canvas y reciben la respuesta en Canvas.»

### Criterios de aceptación de 1.5

| Id | Comprobación |
|---|---|
| CA-1.5-01 | La prueba `test_no_hay_rutas_publicas_de_estudiante` enumera las rutas del enrutador y falla si aparece una ruta sin sesión fuera de la lista cerrada de dieciséis |
| CA-1.5-02 | No existe ninguna pantalla, ruta ni correo dirigido a un estudiante que apunte a un dominio de la aplicación; los mensajes al estudiante nombran la organización y el repositorio exactos y viven en Canvas |
| CA-1.5-03 | Declarar en `/perfil` una cuenta de GitHub que tiene un mapeo vigente en cualquier curso responde `422` con motivo escrito y queda en `bitacora` |
| CA-1.5-04 | Crear o importar un mapeo con una cuenta ya declarada por un docente responde `422` con el texto «esa cuenta pertenece al equipo docente del curso; vuelve a entregar con tu cuenta personal» |
| CA-1.5-05 | No existe ninguna pantalla de administración global de usuarios, y la búsqueda de usuarios por correo entre los registrados no está disponible por ningún camino |

---

## 1.6 Roles y permisos

**Hay exactamente dos roles, y el rol vive en la membresía del curso**, no en la persona: la misma persona es profesora de un curso y ayudante de otro sin ninguna contradicción.

| Rol | Qué es | Cómo se obtiene | Cómo se pierde |
|---|---|---|---|
| `PROFESOR` | Dueño funcional del curso. Tiene los nueve permisos de forma implícita e irrevocable, y su columna `membresia_curso.permisos` se guarda **vacía** | Creando el curso, siendo invitado con rol profesor, o siendo promovido desde ayudante | Retiro por otro profesor, o cierre de la propia cuenta. **Un curso `ACTIVO` conserva siempre al menos un profesor `ACTIVO`** |
| `AYUDANTE` | Miembro del equipo docente con permisos explícitos | Sólo por **invitación nominal** de un profesor a una dirección `gmail.com`, con enlace de un solo uso y caducidad de 7 días | Retiro (baja lógica, nunca borrado) o cierre de la propia cuenta |

### Los nueve permisos

**Dos son implícitos y siete son configurables. De los siete configurables, cinco son concedibles a un ayudante y dos son NO CONCEDIBLES.**

| Permiso | Qué habilita exactamente | Profesor | Ayudante: precargado al invitar | Ayudante: concedible |
|---|---|---|---|---|
| `curso.ver` | Ver el curso, personas, tareas, tablero, timeline, estado de repositorios, entregas, fechas y **la matriz nominal completa del estado de corrección** | Sí (implícito) | **Sí (implícito)** | No revocable mientras la membresía esté activa |
| `correccion.corregir` | Abrir y trabajar **sólo** las entregas asignadas a uno mismo, y guardar la corrección local | Sí (implícito) | **Sí (implícito)** | No revocable |
| `curso.administrar` | Editar el curso, rehacer la vinculación con Canvas o GitHub, sustituir la credencial, cambiar la zona horaria, conmutar las comunicaciones salientes | Sí | No | **NO CONCEDIBLE** |
| `equipo.administrar` | Incorporar y retirar profesores y ayudantes, cambiar permisos y roles | Sí | No | **NO CONCEDIBLE** |
| `tarea.administrar` | Crear y editar tareas, vincular entregas de Canvas, gestionar el repositorio base y sus archivos, forzar aprovisionamiento, reintentar fallos | Sí | No | Sí |
| `mapeo.editar` | Crear, corregir e invalidar el mapeo estudiante ↔ cuenta de GitHub; importar CSV; reenviar invitaciones; ver sin enmascarar el correo y el `sis_user_id` | Sí | **Sí** | Sí |
| `correccion.asignar` | Repartir las entregas entre los correctores | Sí | No | Sí |
| `nota.publicar` | Escribir calificación, comentario y rúbrica en Canvas | Sí | **No** | Sí |
| `comunicacion.enviar` | Enviar mensajes y anuncios manuales por Canvas y activar o desactivar las comunicaciones automáticas de una tarea | Sí | No | Sí |

**Regla de vocabulario, obligatoria.** La expresión «los siete permisos concedibles» **queda prohibida** en esta especificación, en la interfaz y en el texto de la entrega. Se escribe **«los cinco concedibles»** o **«los siete configurables»**, que son cosas distintas. El conjunto preparado del formulario se llama **«Gestión completa (los cinco concedibles)»**.

**Cómo se ve el formulario.** `/cursos/{id}/equipo` y el diálogo de invitación muestran **las siete casillas configurables**: las cinco concedibles editables; las dos NO CONCEDIBLES **deshabilitadas con el motivo escrito en el propio control** —«da acceso a la credencial de Canvas del curso» y «permitiría concederse a sí mismo el resto»—; y los dos implícitos marcados y fijos con la nota «siempre incluidos».

**Cómo se defiende, en tres capas y no en una:**

| Capa | Defensa |
|---|---|
| Base de datos | Cuatro `CHECK` sobre `membresia_curso` e `invitacion_equipo`: los elementos del array pertenecen a los siete nombres configurables; ningún `AYUDANTE` lleva un permiso NO CONCEDIBLE; todo `PROFESOR` lleva `permisos = '{}'`; ningún `NULL` dentro del array. **Los cuatro viajan en la migración inicial** |
| Servidor | Dependencia única `requiere(permiso, curso_id, rol_minimo=None)` en toda ruta de curso, con `422` ante un array inválido y acotación de **toda** consulta por el `curso_id` del contexto |
| Invariantes | Invariante 15: todo curso `ACTIVO` conserva al menos una membresía `ACTIVA` de rol `PROFESOR`. Invariante 16: ninguna membresía ni invitación de rol `AYUDANTE` contiene un permiso NO CONCEDIBLE. **Los dos son bloqueantes y ninguno se auto-repara** |

**Ocultar un botón es presentación y no es autorización.** La comprobación real está siempre en el servidor, y una puerta de construcción falla si aparece registrada una ruta de curso sin la dependencia de permiso.

### Las seis acciones cerradas por rol

`rol_minimo='PROFESOR'` se usa en **exactamente seis acciones y ninguna más**; **ninguna otra ruta, servicio o consulta lee `membresia_curso.rol` para decidir si una acción procede**.

| # | Acción | Permiso adicional que además exige |
|---|---|---|
| 1 | Confirmar una posible fusión de usuarios de Canvas | `mapeo.editar` |
| 2 | Recapturar una versión con otra fecha de corte | `tarea.administrar` |
| 3 | Fijar una versión en un SHA concreto | `tarea.administrar` |
| 4 | Archivar y desarchivar los repositorios de una tarea | `tarea.administrar` |
| 5 | Entrar a `/operacion`, a `/operacion/invariantes` y a todo `/api/operacion/**` | — |
| 6 | Salir de `MODO_RECUPERACION` | — |

«Capturar ahora» **sin** cambiar la fecha de corte **no** está en la lista: es `tarea.administrar`, y un ayudante con ese permiso puede hacerlo.

### Efecto inmediato de los cambios

Un cambio de rol o de permisos incrementa `membresia_curso.version` en la misma transacción y **surte efecto de inmediato**, no en el próximo inicio de sesión. La comprobación es **por membresía**, contra la tabla `sesion_membresia`: si la membresía cambió, se recargan los permisos; si pasó a `RETIRADA`, se deniega el acceso **a ese curso** con `403` y mensaje explícito, y **el acceso del usuario a sus otros cursos no se toca**.

### Criterios de aceptación de 1.6

| Id | Comprobación |
|---|---|
| CA-1.6-01 | Un `PATCH` que intenta conceder `curso.administrar` o `equipo.administrar` a una membresía o invitación de rol `AYUDANTE` responde `422`, y el mismo intento ejecutado directamente contra la base de datos falla por restricción |
| CA-1.6-02 | Una membresía de rol `PROFESOR` tiene `permisos = '{}'` en base de datos, y ninguna consulta de la aplicación lee esa columna para un profesor |
| CA-1.6-03 | Retirar al último profesor `ACTIVO` de un curso `ACTIVO` se rechaza con el mensaje literal «no puedes retirar al último profesor del curso: promueve antes a otro profesor» |
| CA-1.6-04 | Con dos sesiones del mismo usuario en dos cursos, retirar su membresía en uno deja la otra sesión funcionando |
| CA-1.6-05 | La cadena «los siete permisos concedibles» no aparece en ningún archivo de la interfaz, del texto de entrega ni de esta especificación |
| CA-1.6-06 | Una prueba de matriz ejecuta cada una de las seis acciones cerradas por rol como ayudante con el permiso funcional correspondiente y obtiene `403` con código `PERMISO_INSUFICIENTE` |

---

## 1.7 Identidad y acceso

| Aspecto | Regla |
|---|---|
| **Alta y acceso** | Google OpenID Connect (Authorization Code + PKCE). **No hay formulario propio con contraseña, ni siquiera de respaldo** |
| **Correo admitido** | `email_verified = true` y dominio exactamente `gmail.com`. `googlemail.com` se normaliza a `gmail.com`. **Se rechaza todo correo con reclamación `hd`**, y eso es cumplimiento de **R2.1.2**, no un fallo, y así se explica en la pantalla y en el texto de la entrega |
| **Correo canónico** | `usuario.email_canonico` e `invitacion_equipo.email_canonico` guardan el correo en minúsculas, con `googlemail.com` normalizado, **sin puntos en el local-part y sin sufijo `+etiqueta`**. La canonización se aplica **sólo** a `gmail.com` y `googlemail.com`. El emparejamiento de una invitación se hace por `email_canonico`, nunca por la cadena tecleada |
| **Identidad estable** | Manda `google_sub`. Un cambio de dirección en Google actualiza `email` y `email_canonico` en la misma transacción y queda en `bitacora`; si el nuevo correo canónico chocara con otro usuario **no se actualiza nada** y se deniega el acceso con mensaje explícito |
| **Sesión** | Cookie opaca respaldada en servidor, no un JWT autocontenido |
| **Selección de cuenta** | `prompt=select_account` se envía **siempre**, para que en una demostración con varias sesiones de Google abiertas no ocurra un inicio de sesión silencioso en la cuenta equivocada |
| **Un usuario recién autenticado no es profesor de nada** | Se convierte en profesor de un curso al crearlo (**R2.1.3**) o al ser incorporado (**R2.1.7**), y en ayudante al ser incorporado (**R2.1.8**) |
| **Cuenta de GitHub del docente** | Es un atributo de la **persona** (`usuario.cuenta_github_id`), con índice único parcial global, no de la membresía. Se declara y se desvincula en `/perfil` |
| **Consentimiento de lectura** | Antes de que su cuenta entre a la organización, la persona ve y acepta el texto literal: «Al aceptar, tu cuenta de GitHub entrará en la organización **{organización}** y tendrás **lectura de todos los repositorios** de los estudiantes de este curso, no sólo de los que te toque corregir. Ese acceso se retira automáticamente si dejas de ser miembro de este curso.» Aparece en `/invitaciones/{token}` sobre el botón de aceptar y en `/perfil` con una **casilla que hay que marcar**; se persiste `usuario.consentimiento_github_en`, y **sin ese consentimiento fechado la aplicación no incorpora a esa persona a la organización ni al equipo `docentes`** |
| **Administración de la propia cuenta** | `/perfil`, sin permiso, para todo usuario con sesión: editar nombre visible (el correo **no es editable**), declarar y desvincular la cuenta de GitHub, ver y desvincular identidades de Canvas por instancia, ver y cerrar sesiones abiertas, y **cerrar la propia cuenta** |
| **Cierre de cuenta** | `usuario.activo = false` significa «esta persona cerró su cuenta» y **sólo lo escribe su propio dueño**. Efectos: se revocan todas sus sesiones, sus membresías activas pasan a `RETIRADA` con el procedimiento completo —incluida la revocación del acceso en GitHub— y no puede volver a iniciar sesión. **No se borra la fila**: su autoría, sus correcciones publicadas y su bitácora se conservan, y la interfaz lo muestra como «cuenta cerrada» donde aparezca. **Un profesor no puede cerrar la cuenta de otro** |

**Retiro de un miembro, en tres planos.** El retiro pasa la membresía a `RETIRADA` con actor y fecha, incrementa `version`, vacía permisos, deja sus asignaciones de corrección pendientes en `SIN_CORRECTOR` con incidencia visible, **conserva íntegra la autoría de lo que ya corrigió y publicó**, y revoca su acceso en GitHub en tres planos: equipo `docentes`, colaborador y **membresía de la organización cuando la aplicación la dio**. El retiro de un profesor arrastra además sus credenciales de Canvas de ese curso a `RETIRADA`. **R2.1.9 no está cumplido si la persona retirada sigue pudiendo leer el código de los estudiantes.**

### Criterios de aceptación de 1.7

| Id | Comprobación |
|---|---|
| CA-1.7-01 | El alta con una cuenta institucional (con reclamación `hd`) se rechaza; el alta con `gmail.com` verificada crea el usuario |
| CA-1.7-02 | Dos invitaciones al mismo destinatario escritas como `a.b@gmail.com` y `ab+curso@gmail.com` colisionan por `email_canonico` y la segunda se rechaza mientras la primera esté `PENDIENTE` |
| CA-1.7-03 | Sin `usuario.consentimiento_github_en`, el trabajo de sincronización de acceso docente **no llama a GitHub** y la persona figura en `/cursos/{id}/equipo` con el motivo escrito |
| CA-1.7-04 | Retirado un ayudante, su acceso de lectura a los repositorios del curso deja de funcionar, comprobado abriendo un repositorio privado del curso con su cuenta |
| CA-1.7-05 | Cerrada la propia cuenta, la fila de `usuario` sigue existiendo y su autoría sigue visible etiquetada «cuenta cerrada» |

---

## 1.8 Glosario del dominio

**El vocabulario es cerrado y no admite sinónimos en ninguna pantalla, ningún correo, ningún mensaje ni ningún nombre de tabla o de columna.** Toda la interfaz, los correos y los mensajes a estudiantes están en **español de Chile**, con tratamiento de «tú», registro profesional y **sin emojis**; los textos viven en un **único archivo de mensajes**.

| Se dice | Significa exactamente | No se dice |
|---|---|---|
| **Curso** | Entidad propia de la aplicación (`curso`), con nombre, código, período y zona horaria, vinculada a un curso de Canvas y a una organización de GitHub. **Existe antes de ambos vínculos y sobrevive a que uno se rompa** | clase, ramo, course |
| **Sección** | `Section` de Canvas, espejada en `seccion` | paralelo, section |
| **Conjunto de grupos** | `GroupCategory` **colaborativa** de Canvas, espejada en `conjunto_grupos` | group set, categoría |
| **Grupo** | `Group` de un conjunto colaborativo, espejado en `grupo`. Cuenta como integrante quien está `accepted` | equipo, group |
| **Estudiante** | Persona con matrícula de estudiante en el curso de Canvas, espejada en `estudiante`. **Nunca es usuario de la aplicación** | alumno, student |
| **Equipo docente** | El conjunto de personas con `membresia_curso` de estado `ACTIVA` en un curso, cualquiera sea su rol. **[DECISION NUEVA]** — el término se usa en toda la carta y en las actas sin definición formal; se cierra aquí para que «avisar al equipo docente» y «el equipo docente tiene lectura» tengan un destinatario computable | staff, cuerpo docente, docentes (salvo el nombre técnico del equipo de GitHub, que sí es `docentes`) |
| **Tarea** | La agrupación de la aplicación (`tarea`) que mantiene **un único conjunto de repositorios** para todas sus entregas (**R2.3.4**). Su `modalidad` (`INDIVIDUAL` o `GRUPAL`) vive en la tarea y no en la entrega, de modo que **es estructuralmente imposible representar dos entregas de la misma tarea con configuraciones distintas** | proyecto, assignment |
| **Entrega (parcial / final)** | Cada tarea de Canvas vinculada a una tarea de la aplicación (`entrega`), con su `tipo` (`PARCIAL` o `FINAL`), su `orden` contiguo desde 1 y su `slug`. Una tarea con una sola entrega tiene esa entrega como `FINAL` con `orden = 1` | submission, deadline, hito |
| **Sujeto** | La unidad de aprovisionamiento y de corrección (`sujeto`): **el estudiante en una tarea individual, el grupo en una tarea grupal**. Un sujeto tiene exactamente un repositorio. **[DECISION NUEVA]** — el término se usa en A-081, A-164 y en la pantalla de tarea y no figuraba en el vocabulario cerrado; se incorpora aquí con esta definición y con la etiqueta visible «estudiante o grupo» cuando el contexto no lo aclare | destinatario, entidad, target |
| **Fecha de cierre** | La **fecha efectiva** aplicable a un sujeto en una entrega (`fecha_efectiva`), con su `origen` (`BASE`, `SECCION`, `GRUPO`, `ADHOC`) y su regla aplicada. Se materializa, no se calcula al vuelo | due date, plazo, vencimiento |
| **Versión de la entrega** | El estado inmutable del repositorio a la fecha de cierre (`version_entrega`), cuya evidencia normativa es el `commit_sha` persistido | snapshot, corte, foto, tag |
| **Repositorio / Repositorio base** | Repositorio de GitHub creado por la aplicación (`repositorio`, `repositorio_base`). El base es **por tarea y opcional**, y lo crea siempre la aplicación | repo del alumno, plantilla, template |
| **Cuenta de GitHub vinculada** | La correspondencia estudiante ↔ usuario de GitHub (`mapeo_github`), *append-only*, con una fila viva por estudiante y curso | mapeo, matching, linkeo |
| **Invitación · Aceptada · Pendiente** | Estado del acceso de un estudiante a su repositorio (`acceso_repositorio`) | invite, pending |
| **Corrección · Publicar nota** | El trabajo de revisar y el acto de escribir la nota en Canvas (`correccion`, `publicacion_nota`) | grading, push de notas |
| **Profesor / Ayudante** | Los dos roles de curso | admin, TA, staff, corrector |
| **Incidencia** | Problema que requiere atención del equipo docente (`incidencia`), con tipo de catálogo cerrado y severidad determinada por el tipo | error, warning, alerta |
| **Informe diario** | El informe docente de **R2.6.1** (`informe_diario`), único por `(curso, fecha)` y de contenido inmutable | reporte, digest |
| **Sincronización · «Actualizado hace X»** | La traída de datos desde Canvas o GitHub y su sello de antigüedad, producido por un **único componente** que muestra «actualizado hace X · techo N» y se pone ámbar y rojo según el techo declarado del trabajo que lo escribe | sync, refresh, job |
| **Bitácora** | El registro *append-only* de quién, cuándo, contra qué sistema y con qué resultado (`bitacora`), con catálogos cerrados de acción y de entidad | log, auditoría, historial |

Los términos de Git que no tienen traducción asentada se dejan **en inglés y en minúscula**: *commit*, *push*, *branch*, *tag*, *merge*, *pull request*.

**Estados traducidos, errores literales.** Todo estado interno se muestra traducido, con etiqueta fija y **la misma palabra en todas las vistas**; **nunca aparece un identificador en mayúsculas en pantalla**. Los identificadores técnicos que alguien debe copiar —usuario de GitHub, nombre del repositorio, URL, SHA— **no se traducen ni se maquillan**: tipografía monoespaciada y botón de copiado. Los mensajes de error de Canvas y de GitHub se muestran con su **texto literal** en un bloque secundario, bajo una explicación en español de qué significa y qué hacer.

### Criterios de aceptación de 1.8

| Id | Comprobación |
|---|---|
| CA-1.8-01 | Una prueba automatizada falla si un código de estado del enumerado de dominio no tiene etiqueta en el archivo único de mensajes |
| CA-1.8-02 | Ninguna pantalla muestra un identificador en mayúsculas con guiones bajos, comprobado sobre el conjunto de pantallas de la aplicación |
| CA-1.8-03 | El mismo estado se lee con la misma palabra en la pantalla de tarea, en Pendientes, en el informe diario y en `/operacion` |
| CA-1.8-04 | Ningún término de la columna «No se dice» aparece en la interfaz ni en los textos salientes |

---

## 1.9 Alcance incluido

El alcance del sistema es **exactamente los 59 requisitos `R2.x.y` del enunciado**, sin recortes y sin añadidos que compitan por el tiempo. Este cuadro resume qué hace el sistema por sección del enunciado; el detalle vive en los capítulos siguientes.

| Sección | Qué queda dentro | Requisitos |
|---|---|---|
| **§2.1 Cursos y usuarios** | Alta de usuarios con Google OIDC y correo `gmail.com`; administración de usuarios en dos planos (miembros del curso y cuenta propia); creación y administración de cursos; vinculación con un curso de Canvas y con una organización de GitHub mediante asistente de cuatro pasos con estado persistido; checklist de **19 comprobaciones numeradas** ejecutado como trabajo encolado y sondeado desde la interfaz; incorporación de co-profesores y de ayudantes por invitación nominal; **nueve permisos** con las reglas de 1.6; retiro con baja lógica y revocación del acceso en GitHub | R2.1.1 – R2.1.9 |
| **§2.2 Estudiantes y grupos** | Espejo de estudiantes, matrículas y secciones; espejo de conjuntos de grupos colaborativos, grupos e integrantes; mapeo estudiante ↔ cuenta de GitHub por **cuatro vías** —tarea de registro en Canvas, comentario de vuelta en la propia entrega, edición manual y importación CSV—; pantalla **Pendientes**, que reúne en un solo sitio todo lo que falta | R2.2.1 – R2.2.6 |
| **§2.3 Tareas y repositorios** | Tarea vinculada a una o más tareas de Canvas como entregas parciales y final; modalidad derivada de Canvas y **congelada** tras el primer aprovisionamiento; conjunto único de repositorios por tarea; repositorio base opcional creado por la aplicación, con carga, reemplazo, renombrado y borrado de archivos; creación **progresiva y automática** de los repositorios; nombres automáticos e inequívocos que **no cambian nunca**; incorporación de los estudiantes como colaboradores con permiso `push` sobre repositorios **privados**; lectura del equipo docente sobre todos los repositorios del curso; tabla de estado por repositorio con **motivo obligatorio**; aviso al estudiante por Canvas | R2.3.1 – R2.3.12 |
| **§2.4 Fechas y cierre** | Lectura de las fechas de Canvas como fuente autoritativa; fechas distintas por sección; excepciones por estudiante y por grupo; resincronización disparada por **huella de fechas** y no por marca de actualización; captura de la versión del repositorio a la fecha de cierre, por `(entrega, sujeto)`, con recaptura registrada como intento nuevo y **sin destruir la anterior**; enlace directo a la versión que corresponde revisar | R2.4.1 – R2.4.8 |
| **§2.5 Seguimiento** | Tablero por tarea que se pinta **sin llamar a ninguna API externa**; serie de actividad en el tiempo; identificación de repositorios sin actividad reciente con umbral configurable por curso; identificación de estudiantes sin participación; barra de estado de creación y configuración; línea de entregas con fechas y estado; consulta de actividad por ventanas de entrega; comparación de participación intragrupo con umbral de desbalance configurable; métricas propias; **timeline por repositorio** | R2.5.1 – R2.5.10 |
| **§2.6 Informes y comunicación** | Informe docente diario a las 07:00 de la zona del curso, **sólo si hay tarea activa**; contenido accionable con incidencias, ausencias de actividad y próximos cierres; suscripción individual que cada persona gobierna, con enlace de baja firmado; envío por correo; mensajes directos por Canvas; anuncios de curso; **siete eventos de comunicación automática con interruptor por tarea** | R2.6.1 – R2.6.7 |
| **§2.7 Corrección** | Reparto de las entregas entre correctores con tres modos; bandeja del corrector; navegación entre entregas asignadas; acceso directo a la versión registrada; acceso a la rúbrica de Canvas **leída en vivo y no persistida**; publicación de la calificación en Canvas de forma trazable; **matriz nominal del estado de corrección**, legible con `curso.ver` | R2.7.1 – R2.7.7 |

**Magnitudes del sistema, cerradas:** **70 entidades** (60 creadas en la migración inicial y 10 con la entrega final), **siete máquinas de estado** con `estados.py` como fuente única, **31 trabajos periódicos** con espacio de cerrojo y fecha de entrada en servicio, **51 tipos de incidencia** en catálogo cerrado, **dieciséis rutas sin sesión**, **nueve eliminaciones externas** permitidas, **seis escrituras externas síncronas** desde una pantalla y **doce banderas** de perfil de alcance. Añadir un elemento a cualquiera de esas listas es una decisión que se escribe con fecha y motivo; **una lista cerrada que crece en silencio deja de ser una lista cerrada**.

### Criterios de aceptación de 1.9

| Id | Comprobación |
|---|---|
| CA-1.9-01 | La tabla de trazabilidad de la especificación asigna a cada uno de los 59 requisitos al menos una pantalla y al menos un criterio de aceptación |
| CA-1.9-02 | La prueba de alcanzabilidad recorre el mapa de pantallas y comprueba, rol por rol, que **cada requisito es alcanzable por los roles que el enunciado nombra**, con el rol de menor privilegio que el requisito cita |
| CA-1.9-03 | Una prueba de arquitectura falla si existe un modelo de persistencia que no figura en el censo cerrado de 70 entidades |
| CA-1.9-04 | Una prueba compara la lista de cada `CHECK` de catálogo con su enumerado de dominio y **falla la construcción si difieren** |

---

## 1.10 Alcance explícitamente excluido

**Un no-objetivo que no esté en esta lista no es un no-objetivo: es un hueco.** La lista es cerrada, y ampliarla es una decisión que se escribe con fecha y motivo. Ninguna de sus filas corresponde a un requisito `R2.x.y`.

### Lista cerrada de no-objetivos

| # | No-objetivo | Motivo | Dónde se dice, además de aquí |
|---|---|---|---|
| 1 | **Autograding o ejecución de tests sobre la versión capturada** | Ningún requisito lo pide; la aplicación **no descarga ni archiva el código**, sólo entrega enlaces | Pantalla de corrección, junto al enlace a la versión |
| 2 | **Detección de similitud o plagio entre repositorios** | No lo pide ningún requisito y exigiría descargar código | Guía del revisor |
| 3 | **Comentarios de código línea a línea dentro de la aplicación** | **R2.7.4** pide *acceder* a la versión, no comentarla: el comentario de código vive en GitHub y el comentario de la entrega en Canvas | Pantalla de corrección |
| 4 | **Cualquier interfaz para estudiantes** | §1 y §2.3 del enunciado | `/cursos/{id}/personas` |
| 5 | **Crear o editar secciones, grupos e inscripciones en Canvas** | **R2.2.1**–**R2.2.3** dicen «obtener», no crear; la Ley 1 hace de la aplicación un espejo | Personas y grupos, con enlace profundo a Canvas y botón «ya lo hice, sincronizar» |
| 6 | **Editar rúbricas** | §2.7 del enunciado: «las rúbricas y las calificaciones deberán mantenerse en Canvas». Se leen en vivo y no se persisten | Pantalla de corrección, sobre la rúbrica |
| 7 | **Entregas sin tarea de Canvas asociada** | **R2.3.1** y **R2.3.2** atan cada entrega a una tarea de Canvas, y la unicidad `(curso_id, canvas_assignment_id)` lo impone | Tarea → Entregas |
| 8 | **Estudiantes que no provienen de Canvas (oyentes)** | §2.2: la información de estudiantes proviene de Canvas; los sujetos se materializan sólo desde el espejo de estudiantes | Personas |
| 9 | **GitHub Enterprise Server** | Entrada fija del equipo: organización nueva y gratuita en GitHub.com | Guía del revisor |
| 10 | **Notificaciones por Slack, WhatsApp o cualquier canal fuera de Canvas y correo** | **R2.6.4** dice email y **R2.6.5**–**R2.6.6** dicen Canvas | `/cursos/{id}/mis-notificaciones` |
| 11 | **Importar desde GitHub Classroom** | Ningún requisito lo pide; el repositorio base lo crea siempre la aplicación, y la adopción de repositorios preexistentes está acotada por cinco condiciones estrictas | Guía del revisor |
| 12 | **Reconstruir la relación de cursos con *cross-listing*** | Fuera de alcance soportado, pero advertido en el checklist | Checklist de vinculación |
| 13 | **Publicar nota en entregas moderadas o anónimas** | La configuración de Canvas lo impide sin privilegios que el equipo no tiene | Pantalla de corrección |
| 14 | **Formatos de nota `gpa_scale` y `not_graded`** | No admiten publicación por el camino soportado | Pantalla de corrección |
| 15 | **Protección de tags y *rulesets*** | No existen en repositorios privados con organización Free; de ahí la Ley 4 | Guía del revisor |
| 16 | **Distintivo «Verified» de la GitHub App** | No se solicita | Guía del revisor |
| 17 | **Safari en ventana privada** | Fuera de la matriz de navegadores declarada | Guía del revisor |
| 18 | **Tema oscuro y versión móvil de las tablas anchas** | No lo pide ningún requisito | Guía del revisor |
| 19 | **Los *differentiation tags* de Canvas como generadores de repositorio** | Sólo las categorías de grupo colaborativas generan sujetos | Personas |

### Cinco exclusiones adicionales de comportamiento, que no son funciones sino garantías negativas

| # | La aplicación **nunca** | Por qué |
|---|---|---|
| 1 | **Borra un dato propio de dominio.** Retiros, bajas, conflictos, salidas de alcance y correcciones se modelan **con estado, nunca con `DELETE`**. Nunca se borra una fila de `commit`, `version_entrega`, `bitacora`, `publicacion_nota`, `mapeo_github`, `correccion` ni `incidencia` | Destruiría la evidencia que exigen **R2.4.6**, **R2.4.7** y **R2.7.6**. La lista de eliminaciones externas permitidas es cerrada y tiene **nueve** entradas, ninguna de las cuales es un dato de dominio |
| 2 | **Borra repositorios de estudiantes, ni sus commits, ni sus tags, ni sus notas** | Una aplicación docente que puede borrar 600 repositorios de estudiantes con un clic es un riesgo, no una función. El cierre de un curso es **archivado más inventario exportable**, y la palanca real para dejar el entorno limpio es desinstalar la GitHub App |
| 3 | **Persiste calificaciones de Canvas.** El objeto de notas que devuelve la API de matrículas se descarta en el adaptador, no se registra en logs y no viaja al frontend | §2.7 del enunciado: las calificaciones se mantienen en Canvas |
| 4 | **Escribe información personal identificable en los registros.** Se registran identificadores externos y propios; **nunca nombre, correo, `sis_user_id` ni cuerpo de una entrega**, y el filtro central redacta esas claves | No se confía en la disciplina de quien escribe cada línea de log |
| 5 | **Envía una comunicación de forma síncrona desde una vista.** Toda comunicación se encola | Una vista que espera a un proveedor externo se cuelga cuando el proveedor se cuelga |

### Cómo se declara lo excluido, porque declararlo es parte del alcance

§4 del enunciado dice que «las funcionalidades a las que no se puede acceder en el uso no se consideran cumplidas aunque estén en el código». **El reverso también manda: lo que nunca se prometió debe estar declarado para que no se lea como ausencia.** Por eso cada no-objetivo con consecuencia en una pantalla se dice **también in situ**, en el sitio donde el evaluador esperaría encontrarlo, con una frase corta del archivo único de mensajes; y decir en pantalla «esto se configura en Canvas» con enlace profundo convierte un no-objetivo en guía, que es lo que §2.1 pide explícitamente.

**Regla de mantenimiento.** Si un no-objetivo apareciera en la tabla de trazabilidad de requisitos, **la lista está mal y cede la lista**, nunca el requisito.

### Criterios de aceptación de 1.10

| Id | Comprobación |
|---|---|
| CA-1.10-01 | Ninguna fila de la lista de no-objetivos aparece en la tabla de trazabilidad de los 59 requisitos |
| CA-1.10-02 | Los no-objetivos 1, 3, 4, 5, 6, 7, 8, 10, 13, 14 y 19 tienen su frase visible en la pantalla que la tabla les asigna |
| CA-1.10-03 | No existe en el código ninguna sentencia de borrado sobre `commit`, `version_entrega`, `bitacora`, `publicacion_nota`, `mapeo_github`, `correccion` ni `incidencia` |
| CA-1.10-04 | Un registro emitido con todas las claves prohibidas sale redactado, comprobado por prueba automatizada |
| CA-1.10-05 | La acción de cierre de curso archiva y exporta el inventario, y no elimina ningún repositorio; su confirmación exige escribir el `slug` del curso y muestra el recuento de repositorios afectados |

---

## 1.11 Reparto del alcance entre la entrega parcial y la final

**El criterio de corte es el enunciado, no la comodidad.** §3.1 nombra el flujo que hay que demostrar el 16 de septiembre: crear un usuario profesor → crear un curso → vincularlo con Canvas y con GitHub → crear una tarea individual → asociar los estudiantes con sus cuentas de GitHub → ver los repositorios crearse automáticamente. **Todo lo que ese flujo toca está completo y usable el 16 de septiembre, no esbozado.** Lo demás se construye con calidad plena entre el 17 de septiembre y el 6 de octubre. **Enseñar un alcance recortado y consciente es mejor que enseñar cinco funciones a medias, y en la demostración se dice con esas palabras qué queda fuera.**

### Qué requisito está completo en cada fecha

| Requisitos | Parcial · 16-sep-2026 | Final · 6-oct-2026 |
|---|---|---|
| **R2.1.1 – R2.1.6** | **Completo**, con las 19 comprobaciones del checklist y la administración de usuarios en sus dos planos | Mejoras de guía y textos |
| **R2.1.7 – R2.1.9** | **Completo**, con los nueve permisos, el retiro con baja lógica y la revocación del acceso en GitHub | — |
| **R2.2.1, R2.2.2** | **Completo** | — |
| **R2.2.3** | Modelo y sincronización **completos y visibles en Personas**, sin uso todavía en tareas | **Completo**: tareas grupales |
| **R2.2.4 – R2.2.6** | **Completo** para tareas individuales, con las cuatro vías de enrolamiento | Ampliado a grupos |
| **R2.3.1 – R2.3.4** | **Completo** para modalidad **individual** y **una sola entrega** | Modalidad grupal y varias entregas parciales más la final |
| **R2.3.5, R2.3.6** | **Completo**: creación del repositorio base y carga, reemplazo, renombrado y borrado de archivos | Previsualización y árbol completos |
| **R2.3.7 – R2.3.11** | **Completo**, incluida la materialización de sujetos y el acceso de lectura del equipo docente | Más estados, filtros y acciones masivas; archivado |
| **R2.3.12** | **Completo**: un mensaje por Canvas **por integrante** al invitarlo a su repositorio | Anuncio de curso y plantillas afinadas |
| **R2.4.1 – R2.4.4** | **Lectura y visualización** de la fecha base y de las fechas por sección, con `fecha_efectiva` ya materializada | **Completo**: excepciones por estudiante y por grupo, detección de cambios por huella, aviso y reprogramación |
| **R2.4.5 – R2.4.8** | **Fuera** — se dice explícitamente en la demostración | **Completo** |
| **R2.5.1 – R2.5.10** | Sólo el **estado de creación y configuración de repositorios** (**R2.5.5**), que ya exige **R2.3.11** | **Completo** |
| **R2.6.1 – R2.6.4** | **Fuera** | **Completo** |
| **R2.6.5** | **Completo** en lo que exige **R2.3.12** | Ampliado a envío manual desde cualquier tabla |
| **R2.6.6, R2.6.7** | **Fuera** | **Completo** |
| **R2.7.1 – R2.7.7** | **Fuera** | **Completo** |

### Cómo se presenta lo que todavía no está: tres capas y ni una excepción

**Regla dura: nunca se permite comportamiento parcial.** Cada cosa que no está lista cae en exactamente una de estas tres capas, y la capa se decide con un criterio, no caso a caso.

| Capa | Cuándo se aplica | Cómo se ve |
|---|---|---|
| **1 · BLOQUEO con mensaje** | La acción **es alcanzable y sería estructuralmente incorrecta**, no simplemente no implementada | Se rechaza en el momento, con el mensaje que dice qué configuración hay, qué se esperaba y qué hacer. **No se crea ninguna fila y no se toca ningún estado** |
| **2 · OCULTO por perfil de alcance** | Falta **un módulo entero**: una pantalla completa o un bloque autónomo del tablero | **La ruta no se registra en el backend** y el enlace no existe en la navegación. Una llamada directa responde `404` **de enrutado**, nunca un `500` ni una pantalla vacía. No hay «próximamente» |
| **3 · DESHABILITADO con motivo** | Falta **una acción dentro de una pantalla que sí existe** y cuya ausencia sería desconcertante | Control presente, deshabilitado, con el motivo **visible sin pasar el cursor** y **la fecha comprometida escrita** (nunca la palabra «próximamente») |

**El perfil de alcance es una variable de entorno, no un montón de condicionales.** `PERFIL_ALCANCE ∈ {parcial, completo}` gobierna un **catálogo cerrado de doce banderas**, aplicado en el **registro de rutas** y en el **encolado del planificador**. Cada bandera tiene **fecha de retirada, titular, suplente y criterio de aceptación**; **ninguna se retira si su criterio no está verde**, y si vence su fecha sin criterio verde se abre incidencia bloqueante y el bloque siguiente no empieza. `PERFIL_ALCANCE` **no es estado del dominio y no vive en base de datos**, para que no existan cursos con alcances distintos. El frontend construye su navegación desde **`GET /api/capacidades`**, que devuelve `{perfil, banderas[]}` y es **la única fuente**: no hay una segunda lista de módulos en el frontend. **El catálogo entero se elimina del código el 5 de octubre a las 12:00**, y una puerta de construcción verifica que no queda ninguna bandera sin usar.

| # | Bandera | Capa | Retirada |
|---|---|---|---|
| 1 | `tarea_multientrega` | 3 | 23-sep 20:00 |
| 2 | `tarea_modalidad_grupal` | 3 | 23-sep 20:00 |
| 3 | `fechas_excepciones` | 3 | 23-sep 20:00 |
| 4 | `versiones_entrega` | 3 | 23-sep 20:00 |
| 5 | `tarea_archivado` | 2 | 30-sep 20:00 |
| 6 | `tablero_actividad` | 2 | 30-sep 20:00 |
| 7 | `repositorio_timeline` | 2 | 30-sep 20:00 |
| 8 | `ingesta_actividad` | 2 | 30-sep 20:00 |
| 9 | `mis_notificaciones` | 2 | 3-oct 12:00 |
| 10 | `informe_diario` | 2 | 3-oct 12:00 |
| 11 | `comunicaciones_automaticas` | 3 | 5-oct 12:00 |
| 12 | `correccion` | 2 | 5-oct 12:00 |

### Lista normativa única de lo que existe el 16 de septiembre

**Rutas de aplicación registradas bajo `PERFIL_ALCANCE=parcial`:** `/acceso`, `/perfil`, `/cursos`, `/cursos/nuevo`, `/cursos/{id}/vinculacion`, `/cursos/{id}/equipo`, `/cursos/{id}/personas`, `/cursos/{id}/pendientes`, `/cursos/{id}/tareas`, `/cursos/{id}/tareas/{id}`, `/cursos/{id}/ajustes`, `/operacion`, y las tres públicas sin sesión `/invitaciones/{token}`, `/alcance` y `/privacidad`.

**Rutas NO registradas bajo `parcial`** —responden `404` de enrutado—: `/cursos/{id}/mis-notificaciones`, `/cursos/{id}/tareas/{id}/repos/{id}`, `/cursos/{id}/correccion`, `GET` y `POST /baja/{token}`, `POST /api/perfil/regenerar-enlaces`, `POST /api/cursos/{id}/tareas/{id}/archivar` y `.../desarchivar`.

**Endpoints técnicos registrados en los dos perfiles:** `/auth/google/*`, `/auth/confirmar`, `/github/instalacion/callback`, `POST /webhooks/github`, `GET /api/invitaciones/{token}`, `POST /api/invitaciones/{token}/aceptar`, `GET /r/{t}`, `GET /salud`, `GET /estado`, `POST /interno/latido` y `GET /api/capacidades`.

**Bloques de `/cursos/{id}/tareas/{id}` registrados bajo `parcial`, y ninguno más:** línea de entregas; barra de estado de repositorios; tabla completa del estado de **R2.3.11** con estado traducido y motivo por fila; repositorio base con carga, reemplazo, renombrado y borrado de archivos; y el bloque «Comunicaciones» con los siete eventos, **dos operativos y cinco deshabilitados con motivo y fecha**.

### La pantalla que declara el alcance

**`/alcance` es pública, sin sesión, y no es un documento estático: se genera.** Publica la tabla anterior requisito a requisito con tres columnas —requisito, qué se puede hacer hoy, cuándo llega lo que falta— y **su tercera columna se calcula desde el catálogo de banderas**, no se teclea: una bandera retirada convierte automáticamente su fila en «disponible desde DD-MM-YYYY». **No existe una segunda lista que mantener a mano.**

La **banda fija de la cabecera del curso** enlaza a `/alcance` y cambia de texto una vez por bloque: del 16 al 23 de septiembre dice «Entrega parcial del 16 de septiembre. Esta versión cubre la creación del curso, la vinculación, el enrolamiento y la creación automática de repositorios. Ver el alcance completo.»; del 24 de septiembre al 5 de octubre dice «Versión en construcción hacia la entrega final del 6 de octubre. Ver qué está disponible hoy.». **La banda desaparece sola cuando no queda ninguna bandera activa**, el 5 de octubre a las 12:00: no se retira a mano y no hay interruptor para ocultarla. **`/alcance` no se retira: se congela** —el generador escribe una vez la tabla resultante en un fichero versionado— y **queda accesible sin sesión hasta el 31 de octubre**, porque es la evidencia de que el recorte del 16 de septiembre fue deliberado y declarado.

### Criterios de aceptación de 1.11

| Id | Comprobación |
|---|---|
| CA-1.11-01 | Con `PERFIL_ALCANCE=parcial`, cada ruta declarada no registrada devuelve **`404` de enrutado**, y la construcción falla si alguna aparece registrada |
| CA-1.11-02 | Con `PERFIL_ALCANCE=parcial`, la prueba de alcanzabilidad afirma que cada requisito de la columna «Parcial» es alcanzable por los roles que el enunciado nombra |
| CA-1.11-03 | Con `PERFIL_ALCANCE=completo` y catálogo vacío, ni la banda de alcance ni ninguna nota de capa 3 aparecen en ninguna pantalla, y `/alcance` sigue respondiendo `200` |
| CA-1.11-04 | Ningún control deshabilitado usa la palabra «próximamente»: todos nombran la fecha comprometida |
| CA-1.11-05 | Recorriendo la aplicación e intentando salirse del guion a propósito no aparece ni un `500`, ni una pantalla vacía, ni un botón que no hace nada |
| CA-1.11-06 | La retirada de cada bandera está registrada con fecha, titular y criterio verde en `docs/operacion.md` |

---

## 1.12 Restricciones transversales de producto

Estas reglas rigen en **todos** los capítulos. Ninguna admite excepción local.

| # | Restricción | Regla exacta |
|---|---|---|
| 1 | **Ninguna funcionalidad sin pantalla** | Si algo no tiene pantalla, no está hecho. El mapa de pantallas es cerrado |
| 2 | **Una funcionalidad no está cubierta por tener pantalla: está cubierta cuando la persona que el requisito nombra puede entrar en esa pantalla** | Si un requisito dice «profesores **y ayudantes**», su pantalla no puede exigir un permiso que un ayudante no puede tener. Una prueba automatizada lo recorre rol por rol |
| 3 | **Ningún estado interno sin representación** | Las siete máquinas de estado tienen sus estados visibles con nombre en español, nunca como código de error |
| 4 | **Ninguna automatización invisible** | Cada trabajo que produce un efecto visible deja rastro consultable: la última sincronización con su hora, la bitácora de envíos, el historial de versiones y el panel de operación. **Un revisor puede comprobar que la creación progresiva ocurrió sola, en lugar de tener que creerlo** |
| 5 | **Evidencia siempre; disparador manual sólo donde no falsee el requisito** | No existe un botón «capturar ahora» sin cambiar la fecha de corte para un proceso cuya automaticidad es el requisito, ni un «enviar a todos ahora» para las comunicaciones automáticas. Sí existen «sincronizar ahora», «reintentar» y «regenerar el informe de hoy», que **encolan un trabajo** y nunca llaman a la API dentro de la petición HTTP |
| 6 | **Tiempo: almacenar en UTC, presentar en la zona del curso** | Todo instante se persiste como `timestamptz` en UTC. La conversión usa la **zona del curso**, no la del navegador, para que profesor y ayudante en husos distintos vean la misma fecha. Formato `dd-MM-yyyy HH:mm` **con la zona escrita al lado siempre**: `17-09-2026 23:59 (America/Santiago)`. **Nunca se muestra una hora desnuda.** Los trabajos periódicos por curso corren en la zona de **ese** curso |
| 7 | **Idioma y vocabulario** | Español de Chile, tratamiento de «tú», registro profesional, **sin emojis**, textos en un archivo único, vocabulario cerrado de 1.8 |
| 8 | **Matriz de navegadores declarada** | Chrome, Edge y Firefox de escritorio en ventana normal y privada, más Safari de escritorio en ventana normal. **Safari en navegación privada queda fuera de alcance declarado.** La prueba en ventana privada es criterio de aceptación, no una comprobación opcional |
| 9 | **Autorización en el servidor, acotada por curso** | Una dependencia única en toda ruta de curso; **toda consulta al modelo se filtra por el `curso_id` del contexto**; no existe consulta que reciba un identificador de entidad sin acotar por curso |
| 10 | **Los conjuntos son cerrados y verificables** | Cada estado y cada tipo es una columna de texto con `CHECK` de lista cerrada y **código estable ASCII en mayúsculas**; la etiqueta en español vive sólo en la capa de presentación. La lista del `CHECK` se genera desde el enumerado de dominio y una prueba **falla la construcción si difieren**. **No existe un valor de vertedero** |
| 11 | **Un código escrito en una tabla de evidencia no se renombra jamás** | Si el nombre resulta equivocado, se añade el nuevo y el antiguo permanece marcado como deprecado; **ninguna fila de evidencia se reescribe** |
| 12 | **Privacidad por lista blanca** | El adaptador **proyecta la respuesta externa al conjunto permitido antes de que salga**; lo demás no llega nunca al dominio ni a la base. El correo y el `sis_user_id` del estudiante se muestran **enmascarados** salvo a quien tenga `mapeo.editar`, y **cada revelación queda en `bitacora`**. Existe la página pública `/privacidad`, enlazada desde el pie de la aplicación, desde el pie de cada correo y desde el texto de la tarea de registro |
| 13 | **Los estudiantes están informados** | Un anuncio de curso al vincular y al inicio de cada tarea, y un texto en la descripción de la tarea de registro que la aplicación redacta y **el profesor puede editar antes de publicar** —esa edición es el visto bueno del profesor y queda en `bitacora`—, que dicen qué se recopila, para qué, quién lo ve, dónde vive y hasta cuándo |
| 14 | **Idempotencia visible** | Ante una repetición, el comportamiento es **«ya en curso», nunca un duplicado y nunca un silencio**: control deshabilitado mientras la acción corre, token de idempotencia por formulario y deduplicación en la cola por clave de acción |
| 15 | **Se persiste la intención antes de llamar** | Se escribe la intención, se lee para comprobar si el efecto ya existe, se llama, y se marca el resultado después. **Nunca se llama primero** |

### Criterios de aceptación de 1.12

| Id | Comprobación |
|---|---|
| CA-1.12-01 | Ninguna hora aparece en la interfaz sin su zona escrita al lado |
| CA-1.12-02 | Un ayudante entra a `/cursos/{id}/mis-notificaciones` y gobierna su propia suscripción sin necesitar ningún permiso configurable |
| CA-1.12-03 | El flujo completo de acceso y de vinculación funciona en ventana privada en los tres navegadores de la matriz |
| CA-1.12-04 | Ningún botón que produce un efecto externo lo ejecuta dentro de la petición HTTP, salvo las seis escrituras síncronas enumeradas, cada una con su tiempo de espera declarado |
| CA-1.12-05 | Pulsar dos veces el mismo control produce un único efecto y un mensaje «ya en curso», nunca un duplicado ni una pantalla muda |
| CA-1.12-06 | El correo del estudiante aparece enmascarado para un ayudante sin `mapeo.editar`, y revelarlo escribe una fila en `bitacora` |

---

## 1.13 Restricciones no funcionales declaradas

**La escala y la latencia son requisitos, no adjetivos**, porque **R2.5.1** exige la información «de forma inmediata» y **R2.5.3** habla de actividad «reciente»: sin un número esas palabras no son verificables ni incumplibles.

### Escala objetivo

| Dimensión | Objetivo declarado |
|---|---|
| Cursos simultáneos activos | **3** |
| Estudiantes por curso | **200** |
| Tareas por curso · entregas por tarea | **3** · **2** |
| Repositorios por curso · total del sistema | **600** · **1 800** |
| Commits por repositorio | **50** de media, **500** en el peor caso; **30 000** por curso |
| Eventos de webhook | **40 000** por curso en 8 semanas |
| Tamaño de la base | **≤ 150 MB** esperado, con **freno a 300 MB y a 400 MB** |

### Objetivos de tiempo, todos en el percentil 95

| Medida | Objetivo |
|---|---|
| Vista de tarea con 200 sujetos | **< 400 ms** |
| Cualquier vista de listado paginada | **< 600 ms** |
| *push* en GitHub → visible en el tablero | **p50 < 30 s; p95 < 3 min; garantizado ≤ 15 min; techo absoluto 24 h** |
| Aprovisionamiento de 200 sujetos | **≈ 20 min**, con estimación visible en pantalla |
| Captura de versión tras la fecha de cierre | **< 2 min** |
| Generación del informe diario de un curso | **< 60 s** |

**El tablero muestra siempre cuándo se actualizó por última vez** y ofrece «actualizar ahora», que encola. Es honesto sobre la latencia en lugar de fingir tiempo real. **Los objetivos se miden, no se estiman**: la prueba de carga está fechada el 25 de septiembre y sus resultados se registran con fecha, orden y salida.

### Disponibilidad y sostenimiento

| Compromiso | Cómo se sostiene |
|---|---|
| Aplicación disponible y utilizable **hasta el 31 de octubre de 2026 inclusive** | Servicios en plan de pago que no se suspenden; base de datos que no caduca en esa ventana; el planificador produce por diseño la actividad que impide que el proyecto de base de datos se pause; respaldo diario cifrado con restauración **ya probada**; vigilancia externa cada 5 y cada 10 minutos con alerta por correo |
| **Congelación de código el 5 de octubre a las 20:00** | Durante la ventana sólo se integra un cambio que cumpla las cuatro condiciones a la vez: corrige una caída o un error **que bloquea la revisión** de un requisito; trae reproducción escrita; pasa **todas** las puertas de construcción en verde; y lo revisa otro integrante que declara poder explicarlo. Cada corrección se etiqueta y se anota |
| **Canal de soporte publicado** | Dirección de correo del equipo entregada por Canvas, con compromiso de atención **dentro de 24 horas** entre el 6 y el 31 de octubre y con el integrante de guardia nombrado por semana |
| **Punto de retorno siempre disponible** | Respaldo diario a las 05:00 más cinco respaldos etiquetados de hito, con objetivo de **restauración completa en 30 minutos o menos** y criterio de éxito por comparación de recuentos, no por «cargó» |
| **Fin de vida** | El **1 de noviembre de 2026** se desmantela el despliegue completo, se destruyen los proyectos de base de datos, se borran los respaldos y se retira el acceso del evaluador. Queda sólo el código fuente, que no contiene datos personales |

### Criterios de aceptación de 1.13

| Id | Comprobación |
|---|---|
| CA-1.13-01 | La vista de tarea con 200 sujetos se pinta por debajo de 400 ms en el percentil 95, medido con el conjunto sintético de la prueba de carga |
| CA-1.13-02 | `/operacion` muestra las latencias medidas frente a los objetivos declarados, con **dato medido y persistido, nunca una estimación escrita en el código** |
| CA-1.13-03 | Existe registro fechado de al menos tres restauraciones completas ejecutadas con éxito antes del 16 de septiembre, con orden, salida y duración |
| CA-1.13-04 | `GET /salud` responde sin tocar la base de datos y sin límite de tasa; los tres monitores externos están activos y apuntando a salud del backend, al frontend y a la forma anónima de estado |

---

## 1.14 Convenciones de esta especificación

**[DECISION NUEVA]** — el conjunto de documentos de `docs/SPEC/` no tenía fijadas sus propias reglas de lectura. Se cierran aquí y rigen para todos los capítulos.

| # | Convención |
|---|---|
| 1 | **Orden de precedencia, sin excepciones:** enunciado → las cuatro actas de reconciliación (`RG-nnn`) → la carta de arquitectura (`A-nnn`) → las 590 respuestas de alcance. Si una respuesta de alcance dice una cosa y una regla `RG` dice otra, **manda la regla y la respuesta está anulada** |
| 2 | **Dentro de las actas, la parte 4 arbitra** sobre las partes 1, 2 y 3 |
| 3 | **Una decisión de la carta marcada como anulada no se cita sola**: se cita junto a la decisión que su línea de sustitución nombra. Citar una decisión anulada sin su sustituta es un defecto de revisión y se rechaza |
| 4 | **Voz de especificación.** Se escribe «la aplicación registra», nunca «la aplicación debería registrar» ni «el equipo podría evaluar» |
| 5 | **Los códigos internos se escriben en `monoespaciada` y en MAYÚSCULAS**; sus etiquetas visibles se escriben «entre comillas» y en español. Un código nunca se traduce en el texto de la especificación ni se muestra sin traducir en la interfaz |
| 6 | **Toda sección principal termina con una tabla de criterios de aceptación numerados `CA-<sección>-<nn>`**, redactados como comprobaciones que un evaluador puede ejecutar |
| 7 | **Esta especificación no contiene código fuente.** Contiene firmas de endpoints, nombres de tablas y de columnas, nombres de estados y textos literales de interfaz |
| 8 | **Una contradicción entre dos capítulos se escala con las dos citas delante y se resuelve en una enmienda escrita**, previa a toda migración y a todo código nuevo. Nadie la resuelve por su cuenta |

### Criterios de aceptación de 1.14

| Id | Comprobación |
|---|---|
| CA-1.14-01 | Ningún capítulo de `docs/SPEC/` contiene las expresiones «se podría», «el equipo deberá evaluar» ni una opción abierta sin decidir |
| CA-1.14-02 | Toda sección principal de todo capítulo termina con su tabla de criterios de aceptación |
| CA-1.14-03 | Ninguna cita a una decisión anulada de la carta aparece sin su decisión sustituta |

---

## 1.15 Trazabilidad de los 59 requisitos

Este cuadro dice **dónde vive la especificación de cada requisito**. Ningún requisito queda sin destino, y ninguno tiene dos destinos.

| Requisitos | Área de especificación | Pantallas principales |
|---|---|---|
| R2.1.1, R2.1.2 | Identidad, alta y acceso | `/acceso`, `/perfil` |
| R2.1.3 – R2.1.6 | Curso y vinculación con Canvas y GitHub | `/cursos`, `/cursos/nuevo`, `/cursos/{id}/vinculacion`, `/cursos/{id}/ajustes` |
| R2.1.1 (mitad «administrar»), R2.1.7 – R2.1.9 | Equipo, roles y permisos | `/cursos/{id}/equipo`, `/invitaciones/{token}`, `/perfil` |
| R2.2.1 – R2.2.3 | Espejo de Canvas: estudiantes, secciones y grupos | `/cursos/{id}/personas` |
| R2.2.4 – R2.2.6 | Enrolamiento: mapeo estudiante ↔ cuenta de GitHub | `/cursos/{id}/personas`, `/cursos/{id}/pendientes` |
| R2.3.1 – R2.3.4 | Tareas y entregas | `/cursos/{id}/tareas`, `/cursos/{id}/tareas/{id}` |
| R2.3.5, R2.3.6 | Repositorio base y sus archivos | `/cursos/{id}/tareas/{id}` |
| R2.3.7 – R2.3.11 | Aprovisionamiento de repositorios y su estado | `/cursos/{id}/tareas/{id}` |
| R2.3.12, R2.6.5 – R2.6.7 | Comunicación con estudiantes por Canvas | `/cursos/{id}/tareas/{id}`, `/cursos/{id}/personas` |
| R2.4.1 – R2.4.4 | Fechas efectivas y su resincronización | `/cursos/{id}/tareas/{id}` |
| R2.4.5 – R2.4.8 | Versiones de entrega | `/cursos/{id}/tareas/{id}` |
| R2.5.1 – R2.5.9 | Tablero y métricas de seguimiento | `/cursos/{id}/tareas/{id}` |
| R2.5.10 | Timeline por repositorio | `/cursos/{id}/tareas/{id}/repos/{id}` |
| R2.6.1 – R2.6.4 | Informe docente diario y suscripción | `/cursos/{id}/mis-notificaciones`, `/baja/{token}` |
| R2.7.1 – R2.7.7 | Corrección, rúbrica y publicación de notas | `/cursos/{id}/correccion` |
| §3.1, §3.2, §4 (declaración de alcance y evidencia de operación) | Alcance declarado y panel de operación | `/alcance`, `/privacidad`, `/operacion` |

### Criterios de aceptación de 1.15

| Id | Comprobación |
|---|---|
| CA-1.15-01 | Cada uno de los 59 requisitos aparece exactamente una vez en la columna izquierda de este cuadro |
| CA-1.15-02 | Cada pantalla nombrada existe en el mapa de pantallas y es alcanzable desde la navegación por el rol de menor privilegio que su requisito cita |
| CA-1.15-03 | Ningún no-objetivo de 1.10 aparece en este cuadro |
