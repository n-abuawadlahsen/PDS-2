# Handoff de contexto — Frontend de la entrega parcial

**Proyecto:** Proyecto 2 Web · ICC4201 · Universidad de los Andes · 2026-2.

**Corte de esta revisión:** 14 de septiembre de 2026, Etapa 0 y etapas P1–P8.

**Propósito:** contexto funcional y técnico para trabajar la experiencia y presentación del frontend existente. Este documento no contiene un prompt ni define una propuesta visual cerrada.

## 1. Situación y objetivo del producto

La aplicación ayuda a profesores y ayudantes a gestionar tareas de programación coordinando dos plataformas:

- **Canvas:** fuente de estudiantes, secciones, grupos, tareas académicas y fechas.
- **GitHub:** organización del curso, repositorios base, repositorios de estudiantes e invitaciones de acceso.
- **Esta aplicación:** vinculación entre plataformas, equipo docente y permisos, asociación de estudiantes con cuentas de GitHub, configuración de tareas y creación automática de repositorios.

Los estudiantes **no son usuarios de esta aplicación**. Interactúan exclusivamente con Canvas y GitHub. No hay portal de estudiantes, registro de estudiantes en la aplicación ni OAuth de GitHub para estudiantes.

Según el responsable del proyecto y el README, el backend de la parcial ya está implementado hasta P8. El frontend tiene pantallas conectadas para probar funcionalidades, con presentación básica. El trabajo que motiva este handoff es convertir ese frontend en una experiencia clara, consistente y bien guiada para la parcial.

El backend está desplegado en **Render** y el frontend en **Vercel**, según el responsable. Esta revisión se basa en archivos del repositorio; no certifica el funcionamiento del despliegue ni el resultado de una demo real.

## 2. Qué se evalúa en esta entrega

El enunciado fija la entrega parcial para el **miércoles 16 de septiembre de 2026, a las 13:30, presencial**, con valor de **1,6 puntos**. Se demuestra el recorrido completo:

1. Registro de un profesor.
2. Creación de un curso.
3. Vinculación con Canvas y con una organización de GitHub.
4. Asociación de estudiantes de Canvas con sus cuentas de GitHub.
5. Creación de una tarea individual.
6. Creación automática de los repositorios asociados.

También se entrega por Canvas un enlace utilizable por el profesor y los ayudantes evaluadores. **La facilidad de uso y la guía durante todo el proceso forman parte explícita de la evaluación.** El enunciado considera incumplidas las funcionalidades que no son accesibles durante el uso, aunque existan en código.

El enunciado permite lenguajes, frameworks y bibliotecas de uso libre y gratuito. El equipo debe poder explicar el código y las decisiones de implementación durante la validación individual.

Hay dos conceptos distintos llamados «entrega»: la entrega parcial del proyecto universitario y las entregas académicas dentro de la aplicación. En esta versión, cada tarea de la aplicación tiene **una sola entrega**, identificada internamente como `FINAL`, aunque la aplicación se esté presentando en la evaluación parcial.

## 3. Fuentes y cómo interpretar sus diferencias

Todas las rutas de archivos indicadas aquí son relativas a la raíz del repositorio.

| Fuente | Qué aporta |
|---|---|
| `docs/proyecto2.pdf` y `docs/proyecto2.md` | Enunciado original y extracción del PDF; el Markdown contiene artefactos de conversión. |
| `docs/enunciado-proyecto2.md` | Transcripción legible, con identificadores `R2.x.y`; §3.1 describe la demo parcial. |
| `docs/PLAN-IMPLEMENTACION.md` | Recorte por etapas: Etapa 0 y P1–P8 para esta oportunidad; F1–F12 corresponden a la final. |
| `docs/SPEC/13-interfaz.md` | Referencia de navegación, mensajes, guía, estados, accesibilidad y resoluciones. Describe más de lo que existe hoy. |
| `docs/SPEC/02-roles-y-permisos.md` | Roles, permisos, identidad e invitaciones. |
| `docs/SPEC/04-vinculacion.md` | Asistente Canvas/GitHub y checklist. |
| `docs/SPEC/07-estudiantes-y-grupos.md` | Personas, asociación con GitHub y Pendientes. |
| `docs/SPEC/08-aprovisionamiento.md` | Tareas, repositorio base, creación y estados de repositorios. |
| `docs/SPEC/09-entregas-fechas-y-versiones.md` | Fechas; para esta parcial, solo el recorte de lectura de P8. |
| `docs/ARQUITECTURA.md` | Decisiones de dominio y trazabilidad; §17 y §20 explican el reparto parcial/final. |
| `README.md`, `frontend/vercel.json` y código | Estado documentado de implementación, despliegue y contratos efectivos. |

El enunciado define los requisitos; el plan delimita esta entrega; el código muestra las capacidades y contratos disponibles. Una función descrita en el SPEC no equivale a una pantalla implementada. Las brechas relevantes aparecen en §10.

`docs/operacion.md` conserva afirmaciones antiguas sobre ausencia de despliegue y cobertura limitada a P1. Para el contexto actual de infraestructura, el responsable y el README indican Render/Vercel.

## 4. Alcance funcional de la parcial

| Etapa | Capacidad disponible según el corte P1–P8 | Consecuencia para la experiencia |
|---|---|---|
| P1 | Acceso mediante Google con cuenta personal Gmail, perfil y sesiones. | Entrada sencilla; explicación de rechazos y recuperación del acceso. |
| P2 | Cursos, profesores, ayudantes, invitaciones y permisos por curso. | Diferenciar rol, permisos y pertenencia a cada curso. |
| P3 | Credencial personal de Canvas y selección de un curso de Canvas. | Guía para obtener el token, consentimientos y selección por nombre. |
| P4 | Instalación de GitHub App en una organización y checklist de vinculación. | Mostrar avance, resultados y bloqueos concretos. |
| P5 | Sincronización de estudiantes, secciones y grupos de Canvas. | Datos de solo lectura académica con antigüedad visible. |
| P6 | Asociación estudiante–GitHub, importación CSV, registro en Canvas y Pendientes. | Hacer visible quién falta, qué falta y cómo resolverlo. |
| P7 | Tarea individual con una entrega de Canvas y repositorio base opcional. | Configuración comprensible, vista previa del nombre y activación. |
| P8 | Creación progresiva de repositorios, accesos, avisos por Canvas y lectura de fechas. | Progreso observable, motivos por fila y acciones de recuperación. |

### Capacidades de la final que no forman parte de este trabajo

- Aprovisionamiento de tareas grupales. Los grupos ya pueden aparecer como información sincronizada en Personas.
- Múltiples entregas de una misma tarea.
- Gestión completa de excepciones de fechas por estudiante/grupo y resincronización avanzada de fechas.
- Captura de versiones al cierre, enlaces a SHA de entrega y cierre/archivado de tareas.
- Métricas de commits, participación, inactividad, gráficos de actividad y timeline del repositorio.
- Corrección, asignación de correctores, rúbricas y publicación de notas.
- Informes diarios, preferencias de notificaciones y comunicaciones ampliadas.

El resumen de estados de creación de repositorios de P8 sí pertenece a la parcial. No es el dashboard de actividad de programación de la final. Los eventos automáticos contemplados en P8 son `repositorio_disponible` e `invitacion_aceptada`; el recordatorio manual por información faltante también pertenece a la parcial.

## 5. Usuarios, conceptos y reglas que afectan al diseño

### Usuarios y permisos

- **Profesor:** administra el curso y el equipo. Los co-profesores tienen los mismos permisos.
- **Ayudante:** sus permisos son específicos de cada curso. La API devuelve el rol y los permisos efectivos en `GET /api/cursos/{curso_id}/contexto`.
- **Estudiante:** es una persona sincronizada desde Canvas, nunca una sesión de esta aplicación.

Hay nueve claves de permiso:

| Grupo | Claves |
|---|---|
| Implícitos | `curso.ver`, `correccion.corregir` |
| Concedibles a ayudantes | `tarea.administrar`, `mapeo.editar`, `correccion.asignar`, `nota.publicar`, `comunicacion.enviar` |
| Exclusivos de profesores | `curso.administrar`, `equipo.administrar` |

Las claves de corrección ya existen en el catálogo, pero sus módulos son de la final. El formulario actual asigna por defecto `mapeo.editar` a un ayudante. Cambiar permisos o retirar a alguien tiene efecto en peticiones posteriores; la interfaz no puede asumir que los permisos duran toda la sesión.

El backend es la autoridad de autorización. La visibilidad de un botón debe corresponder a los permisos efectivos y a las capacidades disponibles, y un rechazo del servidor necesita una explicación útil. No se puede retirar/degradar al último profesor activo de un curso activo ni cerrar su cuenta sin resolver esa situación.

### Conceptos de dominio

- **Curso de la aplicación:** tiene nombre, código, período, identificador corto y zona horaria; se vincula a un curso de Canvas y una organización de GitHub.
- **Tarea de la aplicación:** agrupa configuración de repositorios y entregas. En la parcial es individual.
- **Entrega:** referencia una tarea ya existente en Canvas; no es un archivo subido a esta aplicación.
- **Sujeto:** término interno para el destinatario de un repositorio. En la parcial corresponde a un estudiante; es preferible mostrar «Estudiante» en la interfaz.
- **Repositorio base:** plantilla opcional creada por la aplicación, con archivos iniciales.
- **Asociación o mapeo:** correspondencia entre un estudiante de Canvas y una cuenta personal de GitHub.

### Reglas del recorrido

1. El acceso utiliza Google; no existe contraseña propia. Se aceptan cuentas personales Gmail y se rechazan cuentas institucionales gestionadas.
2. Cada profesor añade **su propia** credencial de Canvas. La selección del curso se hace desde los resultados del backend, sin escribir un ID a mano.
3. GitHub se vincula mediante una App instalada en una **organización**, no en una cuenta personal. El retorno firmado identifica el curso.
4. El registro habitual de GitHub ocurre mediante la tarea de Canvas «Registro de tu cuenta de GitHub». También existen edición manual docente y CSV con previsualización. El recordatorio manual no constituye otra fuente de identidad.
5. Estudiantes, secciones y grupos provienen de Canvas. La aplicación no los crea ni edita como si fuera un segundo LMS.
6. La modalidad de la tarea deriva de Canvas. La parcial permite seleccionar tareas individuales; una opción grupal debe conservar la explicación de su indisponibilidad.
7. El repositorio base es opcional y lo crea la aplicación. No hay importación de una plantilla arbitraria de GitHub. Modificarlo no actualiza repositorios de estudiantes ya creados.
8. **Activar la tarea es el único disparador manual del flujo normal de creación.** Los repositorios se crean automáticamente conforme se completa la información; no existe un botón «Crear todos los repositorios».
9. Un estudiante sin cuenta asociada no detiene a los demás. Su situación queda visible como información pendiente.
10. Los estudiantes reciben acceso como colaboradores del repositorio, con permiso de escritura; no ingresan como miembros de la organización.
11. El nombre de cada repositorio se genera en el backend y no cambia después de crearse. La vista previa también procede de la API.
12. Los avisos de acceso se envían por Canvas. Crear un repositorio, enviar una invitación y aceptar la invitación son hechos diferentes.
13. Una sustitución de repositorio requiere confirmación escrita y conserva el registro anterior. No equivale a borrar y recrear silenciosamente.

## 6. Inventario real del frontend

Las rutas siguientes están registradas en `frontend/src/App.tsx`. Los nombres entre `:` son parámetros.

| Ruta | Archivo en `frontend/src/paginas/` | Contenido actual |
|---|---|---|
| `/` | Definida en `App.tsx` | Redirige a `/acceso`. |
| `/acceso` | `Acceso.tsx` | Botón Google y motivos de rechazo. |
| `/confirmar` | `Confirmar.tsx` | Confirmación alternativa cuando no vuelve la cookie inicial de OAuth. |
| `/cursos` | `Cursos.tsx` | Lista de cursos y formulario de creación en la misma pantalla. |
| `/cursos/:cursoId/equipo` | `Equipo.tsx` | Miembros, incorporación con rol/permisos y retiro. |
| `/cursos/:cursoId/vinculacion` | `Vinculacion.tsx` | Token Canvas, consentimientos, selección de curso, instalación GitHub y adopción de instalaciones sin curso. |
| `/cursos/:cursoId/verificacion` | `Checklist.tsx` | Checklist completo, reintento por ítem, verificación manual y pruebas opcionales. |
| `/cursos/:cursoId/personas` | `Personas.tsx` | Estudiantes, secciones, grupos, sincronización, registro GitHub, edición de asociación y CSV. |
| `/cursos/:cursoId/pendientes` | `Pendientes.tsx` | Cuatro bloques de información pendiente y recordatorio manual. |
| `/cursos/:cursoId/tareas` | `Tareas.tsx` | Lista y creación desde tareas de Canvas, `.gitignore` opcional y vista previa de nombres. |
| `/cursos/:cursoId/tareas/:tareaId` | `Tarea.tsx` | Activación, entregas, fechas, repositorios y administración del repositorio base. |
| `/vinculacion/github/retorno` | `GithubRetorno.tsx` | Resultado de instalación GitHub y regreso al curso. |
| `/invitaciones/:token` | `InvitacionPublica.tsx` | Invitación al equipo, correo enmascarado, rol, permisos, consentimiento y aceptación. |
| `/perfil` | `Perfil.tsx` | Nombre, correo, sesiones y cierre de cuenta. |

`RepositoriosTarea.tsx` contiene `BloqueRepositorios` y `LineaFechas`, montados dentro de `Tarea.tsx`; **no es una ruta independiente actual**.

### Datos y acciones importantes por pantalla

**Cursos:** nombre, código de hasta 12 caracteres, período de 6 caracteres (ejemplo `2026-2`), identificador corto único de hasta 24 y zona horaria, inicialmente `America/Santiago`.

**Vinculación:** estado de credenciales, titular, huella y fecha de comprobación; nunca se recupera el token para mostrarlo. La pantalla incluye dos consentimientos de Canvas. El consentimiento de lectura del código forma parte del modelo de incorporación docente y aparece en la invitación; la declaración de cuenta GitHub del docente presenta la brecha indicada en §10.

**Checklist:** 19 ítems numerados y dos pruebas opcionales de escritura (`5-bis`, `17-bis`), con estados `CORRECTO`, `ADVERTENCIA`, `BLOQUEANTE`, `NO_VERIFICADO` y `VERIFICADO_A_MANO`. Las pruebas de escritura tienen consentimiento explícito porque producen efectos en Canvas. La interfaz actual consulta cada 2 segundos durante una ejecución.

**Personas:** conteo de cuentas verificadas sobre total de estudiantes, última sincronización de estudiantes/grupos, datos de inscripción y estado de asociación GitHub. Correo y otros identificadores pueden llegar enmascarados según permisos. El CSV acepta `canvas_user_id` o `login_id`, más `github_login`; el backend devuelve resultados por fila y aplica las válidas.

**Pendientes:** sin cuenta de GitHub; cuentas en conflicto; grupos incompletos; invitaciones sin aceptar. El recordatorio manual tiene límite de uno por estudiante y día. El bloque de grupos puede mostrar información sincronizada sin habilitar tareas grupales.

**Tarea/repositorios:** resumen con operativos, degradados, esperando información, listos/creando, esperando límite, errores, inaccesibles, fuera de alcance y archivados. La tabla distingue estado del repositorio, motivo, acceso del estudiante y acceso docente. Actualmente se consulta cada 10 segundos mientras el bloque está montado. Las fechas se consultan al montar su bloque.

**Repositorio base:** creación, carga, reemplazo, renombrado, borrado y previsualización de archivos. El backend devuelve el estado y la rama real; no se asume que se llame `main`. Una base declarada que no está lista puede bloquear la activación con motivo explícito.

## 7. Estados que deben conservar su significado

| Código de repositorio | Significado visible |
|---|---|
| `ESPERANDO_INFORMACION` | Falta información identificable, por ejemplo la cuenta de GitHub. |
| `LISTO_PARA_CREAR`, `CREANDO` | La creación está pendiente/en curso. |
| `CREADO_SIN_CONTENIDO`, `CONTENIDO_LISTO`, `CONFIGURANDO_ACCESOS` | Pasos intermedios; todavía no equivalen a operación completa. |
| `OPERATIVO` | Repositorio operativo. |
| `DEGRADADO` | Repositorio creado con configuración/accesos pendientes; por ejemplo una invitación sin aceptar. No se suma a errores. |
| `ESPERANDO_LIMITE` | Espera impuesta por el límite de uso de GitHub. |
| `ERROR_TRANSITORIO` | Se reintentará; puede existir hora del próximo intento. |
| `BLOQUEADO`, `ERROR_PERMANENTE` | Hay un impedimento o se requiere intervención. |
| `INACCESIBLE` | No se puede acceder al repositorio; puede requerir sustitución. |
| `FUERA_DE_ALCANCE`, `ARCHIVADO` | Estados distintos de una creación pendiente o un error. |

Los catálogos existentes están en `frontend/src/lib/textosTarea.ts`. La causa concreta procede del backend; no debe deducirse únicamente del color o del estado general.

Para las asociaciones de cuentas existen `SIN_DATO`, `RECIBIDO`, `NO_RESUELTO`, `NO_EXISTE`, `ES_ORGANIZACION`, `EN_CONFLICTO`, `VIGENTE`, `INVALIDADO` y `SUPERSEDIDO`. Para el usuario requieren etiquetas claras, no códigos internos.

Las pantallas también necesitan distinguir carga inicial, actualización de datos existentes, operación en curso, resultado vacío, información aún no sincronizada, acceso insuficiente, sesión vencida y fallo de proveedor. Una solicitud aceptada para procesamiento no implica que el trabajo ya terminó.

## 8. Base técnica y contratos de integración

### Stack y organización

- Frontend: **React 18, TypeScript estricto, Vite 5 y React Router 6**; Node 22 según `package.json` y `.nvmrc`.
- Backend: **FastAPI/Python 3.12**, SQLAlchemy, Alembic y PostgreSQL; trabajos en segundo plano mediante un motor propio.
- Estado del frontend: `useState`/`useEffect` y llamadas `fetch`. No hay biblioteca de consultas, store global o sistema de componentes instalado.
- Presentación: HTML nativo y estilos inline. No hay Tailwind, biblioteca visual, iconos ni hojas de estilo propias en el árbol actual de `frontend/src`.
- `frontend/src/lib/api.ts`: cliente compartido, tipos y buena parte de los contratos.
- `frontend/src/lib/permisos.ts`: catálogo de permisos y textos del formulario.
- `frontend/src/lib/mensajes.ts`: motivos de rechazo de acceso.
- `frontend/src/lib/textosTarea.ts`: etiquetas y formato de estados/fechas de tareas y repositorios.

### Sesión y despliegue

La sesión es una **cookie opaca validada por el backend**, no un JWT para guardar en `localStorage`. `apiFetch` envía `credentials: "include"` y añade `X-CSRF-Token` desde la cookie `csrf_token` en mutaciones.

En producción, el navegador usa el origen de Vercel. `frontend/vercel.json` reenvía `/api/*` y `/auth/*` a `https://proyecto2-api-oyxf.onrender.com`; el resto se reescribe a `/index.html` para soportar rutas de la SPA. Por ello, **`VITE_API_BASE_URL` queda vacía o ausente en Vercel**. Poner la URL de Render directamente en el frontend cambia el esquema de cookies y rompe la intención de este despliegue.

El inicio Google y la confirmación OAuth usan formularios de navegación `POST`, no `fetch`, para conservar el comportamiento de redirecciones y cookies. El retorno GitHub usa un `state` de un solo uso; `GithubRetorno.tsx` incluye una protección contra el doble canje por `StrictMode`.

La URL pública de Vercel no se fija en este documento: no fue aportada en la solicitud. La URL de Render anterior es la que figura en el archivo versionado, sin verificación en vivo.

El README describe API y trabajador en un único contenedor de Render gratuito mediante `backend/arranque_plan_gratuito.sh`, con base de datos en Supabase. El trabajador es necesario para las automatizaciones; mantener abierta una pantalla no ejecuta por sí mismo los trabajos.

### Capacidades y contratos útiles

| Contrato | Uso |
|---|---|
| `GET /api/perfil` | Sesión e identidad; `obtenerPerfil()` convierte `401` en `null`. |
| `GET /api/capacidades` | `{ perfil, banderas }`; bajo `parcial`, actualmente `banderas` es `[]`. Las banderas enumeradas representan capacidades habilitadas. |
| `GET /api/cursos/{curso_id}/contexto` | Rol y `permisos_efectivos` del usuario en ese curso. |
| `GET /api/cursos/{curso_id}/personas` y `/personas/cabecera` | Listas sincronizadas y resumen de asociaciones. |
| `POST /api/cursos/{curso_id}/sincronizaciones` | Encola una sincronización; no devuelve la sincronización terminada. |
| `GET /api/cursos/{curso_id}/pendientes` | Los cuatro bloques de Pendientes. |
| `GET /api/cursos/{curso_id}/tareas/assignments-canvas` | Tareas de Canvas con `seleccionable` y `motivo`, fecha de sincronización y plantillas `.gitignore`. |
| `GET /api/cursos/{curso_id}/tareas/vista-previa-nombre` | Validación y vista previa de nombres calculadas por el backend. |
| `GET /api/cursos/{curso_id}/tareas/{tarea_id}` | Detalle y acciones con `{ habilitada, motivo }`, entre ellas activar y crear base. |
| `GET /api/cursos/{curso_id}/tareas/{tarea_id}/repositorios` | `{ resumen, filas }`; contadores y estados reales. |
| `GET /api/cursos/{curso_id}/tareas/{tarea_id}/entregas/fechas` | Fechas de solo lectura para la parcial. |

Los payloads completos están en `api.ts` y en los modelos de `backend/app/api/rutas/`. Las escrituras de archivos base usan JSON con `contenido_base64`, no un upload multipart. La importación CSV actual envía `csv` y `aplicar` como cadenas, con `"true"` para aplicar.

Los métodos del cliente no manejan los errores de manera uniforme: algunos devuelven `Response`, otros lanzan excepciones y otros devuelven `Resultado<T>`. El campo `detail` del servidor puede tener distintas formas. Este detalle importa al unificar errores y evitar pantallas detenidas en «Cargando».

No hay SSE ni WebSocket en el flujo actual. Las consultas periódicas leen estados persistidos. Los contadores y las reglas de fechas/permisos permanecen bajo autoridad del backend.

## 9. Contexto de experiencia y presentación

El problema central del usuario docente es saber **en qué curso está, qué quedó configurado, qué falta y cuál es el siguiente paso**. Hoy la navegación se reparte entre enlaces sueltos y formularios extensos. No existe una estructura de navegación compartida ni un indicador global del progreso del curso.

La referencia de interfaz del proyecto establece:

- Español de Chile, con vocabulario comprensible para docentes. El documento HTML ya declara `lang="es-CL"`, aunque hay textos con voseo y códigos técnicos sin traducir.
- Tema claro y legibilidad en proyector. El SPEC declara el tema oscuro fuera de alcance.
- Resolución principal **1366×768** y segunda referencia **1920×1080**; texto de cuerpo de al menos 14 px para la demostración.
- Tablas anchas con desplazamiento dentro de su contenedor, sin desbordamiento horizontal de la página; primera columna identificadora fija.
- Pendientes usable en móvil. Las prioridades móviles de corrección e informe diario del SPEC corresponden a la final.
- Estados con texto e indicador, sin depender solo del color; foco visible, navegación por teclado y etiquetas de formulario.
- Errores que expliquen qué ocurrió y qué puede hacer la persona; controles deshabilitados con motivo visible.
- Tiempos de sincronización y progreso de operaciones visibles, sin simular inmediatez ni éxito.
- Confirmaciones comprensibles para retiro, cierre de cuenta, borrado de archivos y sustitución de repositorio. Hoy varias usan `window.confirm` o `window.prompt`.

El SPEC distingue módulos completos ausentes, que no aparecen en navegación, de acciones no disponibles dentro de una pantalla existente, que se muestran deshabilitadas con motivo y fecha. Los motivos de acciones ya devueltos por la API son la referencia efectiva; hay diferencias de fechas entre textos del SPEC y `backend/app/dominio/alcance.py`.

No existe una identidad visual desarrollada en el frontend revisado: «Proyecto 2» es el título actual. Este handoff no fija nombre comercial, logotipo, paleta ni biblioteca visual.

## 10. Brechas concretas entre código, documentación y experiencia

Estas observaciones provienen de la lectura del código; no constituyen una auditoría funcional ejecutada.

1. **El SPEC no describe exactamente el árbol actual.** No están registradas en `App.tsx` las rutas de resumen de curso, ajustes, operación, alcance, privacidad ni las pestañas independientes de tarea que el SPEC enumera. Tampoco existe una ruta comodín de página no encontrada. Su aparición en la documentación no demuestra que exista el soporte correspondiente.
2. **Hay operaciones de equipo en backend sin controles completos en la pantalla.** Cambiar rol/permisos, reincorporar, consultar impacto/historial y revocar/reenviar invitaciones tienen rutas en `backend/app/api/rutas/cursos.py`; `Equipo.tsx` se concentra en listar, invitar y retirar. `api.ts` ya incluye reincorporación, pero no todo ese conjunto.
3. **La cuenta GitHub docente no tiene formulario en Perfil.** Existen `PUT/DELETE /api/perfil/cuenta-github`; el alta recibe `{ login, consiento }`. `Perfil.tsx` solo muestra identidad, sesiones y cierre de cuenta. Es una brecha relevante para el acceso del equipo docente a GitHub.
4. **Los permisos no se reflejan consistentemente.** Equipo consulta el contexto, mientras distintas pantallas muestran acciones que pueden terminar rechazadas por la API. En particular, crear/restaurar la tarea de registro GitHub exige actualmente `curso.administrar` en el backend, aunque el plan P6 menciona `comunicacion.enviar`.
5. **Capacidades todavía no gobierna la navegación.** Existe `obtenerCapacidades()`, pero `App.tsx` registra las rutas estáticamente. El catálogo no aporta al frontend un calendario completo de fechas en esa respuesta.
6. **No hay interfaz de preferencias de comunicación de P8.** El SPEC describe interruptores, pero la pantalla de tarea actual no contiene ese bloque; la existencia de eventos automáticos no equivale a disponer de una API y controles para configurarlos.
7. **Las tablas son básicas.** Personas, tareas y repositorios no ofrecen actualmente búsqueda/paginación visible. El endpoint de repositorios devuelve `resumen` y `filas`, sin contrato de paginación de servidor en su firma actual.
8. **El tratamiento de carga y errores es incompleto.** Varias cargas iniciales no capturan fallos. Perfil puede permanecer en «Cargando» sin sesión. No existe una protección de rutas compartida.
9. **La previsualización CSV y la aplicación son botones independientes.** La interfaz actual no obliga a revisar una previsualización vigente antes de aplicar, aunque el flujo documentado sí contempla esa revisión.
10. **Las comprobaciones de UX del SPEC no están implementadas como suite frontend.** El CI actual ejecuta `npm ci` y `npm run build`; no hay pruebas frontend ni configuración Playwright/axe en el árbol revisado. Existe un script `lint`, pero no se encontró configuración ESLint en `frontend/`.

La afirmación «implementado hasta P8» se refiere al corte de trabajo del proyecto, no a que todas las pantallas, criterios del SPEC o casos reales estén verificados. Algunas mejoras de exposición pueden usar rutas ya disponibles; otras requerirían trabajo adicional de backend y no se resuelven solo con diseño visual.

## 11. Recorrido de referencia para la demo

| Momento | Lo que la persona debe poder entender/comprobar |
|---|---|
| Acceso | Entró con una cuenta válida y está viendo sus cursos. |
| Crear curso | Qué datos identifican el curso y que aún falta vincular las plataformas. |
| Canvas | Qué credencial está usando y qué curso real seleccionó. |
| GitHub | Qué organización quedó vinculada y si la instalación está completa o pendiente. |
| Verificación | Qué comprobaciones terminaron, cuáles bloquean y qué hacer para resolverlas. |
| Personas | Qué estudiantes llegaron de Canvas, cuándo se sincronizaron y cuántos tienen GitHub asociado. |
| Resolver asociaciones | Cómo funciona el registro en Canvas y qué alternativas docentes existen. |
| Crear tarea | Qué tarea individual de Canvas se eligió, su fecha y los nombres de repositorios previstos. |
| Repositorio base opcional | Qué archivos iniciales se copiarán y cuándo la base está lista. |
| Activar | Que los repositorios comenzarán a crearse automáticamente. |
| Observar creación | Qué repositorios existen, cuáles esperan información y qué accesos faltan. |
| Completar un dato faltante | Que el estudiante pendiente avanza sin volver a activar la tarea ni crear manualmente su repositorio. |
| Comprobar resultado | Enlace al repositorio en GitHub, invitación y aviso recibido en Canvas. |

El caso de un estudiante sin GitHub asociado es especialmente útil: permite observar el completado progresivo y distinguir un pendiente de un fallo general. Los datos, fechas y contadores de una demo conectada provienen de los sistemas reales o de un entorno de prueba identificado; no hay métricas de actividad de la final que mostrar en este corte.

## 12. Ejecución y validación disponibles

Desde la raíz del repositorio:

```bash
cd frontend
npm ci
npm run dev
```

Para backend local en el puerto 8000, `frontend/.env` usa `VITE_API_BASE_URL=http://localhost:8000`. `frontend/.env.example` muestra el valor vacío apropiado para el proxy de producción. El README contiene las instrucciones del backend, la base de datos y el trabajador; la autenticación Google real requiere sus credenciales configuradas.

La comprobación frontend existente es:

```bash
cd frontend
npm run build
```

Este comando ejecuta TypeScript y la construcción de Vite. No demuestra por sí solo accesibilidad, permisos, comportamiento de cookies, integración Canvas/GitHub ni funcionamiento de la demo. El flujo de referencia de §11 y las variantes de carga/error/permisos de §7 describen el contexto de validación funcional pertinente.

Las pruebas de backend están en `backend/tests/`. Según el README, borran tablas entre casos y requieren una base de pruebas separada. Para elaborar este handoff no se ejecutaron pruebas, no se accedió a secretos y no se hicieron operaciones en Canvas, GitHub, Render o Vercel.
