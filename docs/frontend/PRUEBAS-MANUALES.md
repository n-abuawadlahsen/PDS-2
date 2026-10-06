# Guía de pruebas manuales de flujo

Plan para revisar la entrega final usando la aplicación como profesor y ayudante. Basado en el [enunciado, §§2.1–2.7](../enunciado-proyecto2.md), los [59 requisitos](REQUISITOS.md), las pantallas actuales y los [límites vigentes](LIMITACIONES.md). El PDF adjuntado por el usuario es idéntico a [docs/proyecto2.pdf](../proyecto2.pdf).

Esta guía no registra pruebas manuales ya ejecutadas. Las comprobaciones automatizadas anteriores están en [IMPLEMENTACION.md](IMPLEMENTACION.md). Cada resultado manual debe completarse después de hacer el recorrido.

## 1. Qué cuenta como una prueba aprobada

Una acción debe llegar al resultado correcto, conservarlo al recargar y respetar los permisos. Para repositorios, mensajes y notas, comprobar también GitHub o Canvas cuando se usen adaptadores reales. «Encolado» demuestra que se solicitó un trabajo; no demuestra que terminó ni que el proveedor recibió el efecto.

Registrar cada caso como **Aprobado**, **Falló**, **Bloqueado por preparación/configuración** o **No ejecutado**. Anotar si se usaron proveedores reales o dobles. No marcar una integración real como aprobada por haberla probado sólo con dobles.

## 2. Preparación

### Entorno y cuentas

- Usar un curso y una organización de ensayo que controlen. Las pruebas de publicaciones, mensajes, retiro y archivo cambian datos; los destinatarios y repositorios deben ser los del ensayo.
- Tener la API y el trabajador funcionando. Sin el trabajador, una solicitud puede permanecer pendiente aunque la interfaz funcione.
- Para aprobar envíos reales, las comunicaciones globales y del curso deben estar habilitadas, con proveedor y destinatarios de ensayo permitidos. Si están pausadas, comprobar el estado de espera sin dar por entregado el mensaje. El correo usa consola fuera de producción: en local/ensayo se comprueban cola/simulación; el buzón real requiere un despliegue con Resend operativo y cuentas de ensayo.
- Confirmar que `/estado` muestra el esquema esperado, actualmente `0012`, y que `/api/capacidades` permite las áreas de la entrega final. Si una pantalla falta, revisar la configuración y la versión desplegada antes de atribuirlo al navegador.
- Tener un profesor principal, otro profesor y dos ayudantes. Usar perfiles de navegador distintos para no mezclar cookies. Un ayudante comienza con los permisos implícitos `curso.ver` y `correccion.corregir`; otro permite revisar los permisos adicionales por separado.
- Para OAuth real, usar cuentas admitidas por el backend: Gmail o `miuandes.cl`. Los estudiantes trabajan sólo en Canvas/GitHub; no se crea un acceso de estudiante a esta aplicación.
- Preparar un segundo curso independiente para comprobar aislamiento. Si se vincula a Canvas, necesita otro curso Canvas: no intentar vincular el mismo curso externo a dos cursos locales.

### Datos mínimos en Canvas y GitHub

| Dato preparado | Para qué se necesita |
| --- | --- |
| Dos secciones y seis estudiantes de ensayo | Filtros, fechas por sección, permisos y correspondencias nominales. |
| Tres grupos de dos integrantes en un conjunto Canvas | Modalidad grupal y comparación de participación. |
| Una tarea individual; otra tarea grupal con parcial y final, en assignments distintos del mismo conjunto | Repositorios individuales/grupales y entregas independientes. |
| Rúbrica y puntos posibles definidos en Canvas | Corrección y publicación. Conviene usar 100 puntos para simplificar la demostración. |
| Fechas base, un override de sección y una extensión individual | Cálculo de fechas y sus orígenes. |
| Un estudiante sin mapeo, otro con invitación GitHub pendiente y varios con acceso aceptado | Pendientes, incorporación progresiva y reenvíos. |
| Repositorios con commits de dos integrantes antes del cierre; otro commit posterior | Métricas, timeline y versión congelada. |
| Una entrega próxima al cierre y otra ya capturada | Captura automática y consulta inmediata de versiones. |
| Una corrección editable, otra lista, una con nota externa distinta y otra bloqueada | Borrador, publicación, conflicto y restricciones. |
| Un informe diario ya generado y comunicaciones de ensayo | Histórico, suscripciones y bandeja. |

Algunos casos requieren preparación adicional: padrón de más de 50/200 sujetos, cambio de identidad Canvas, 24 horas de cooldown o aviso de archivo enviado hace al menos 14 días. Si falta esa condición, registrar el bloqueo; no cambiar el reloj del equipo ni editar la base compartida para aparentar que pasó el plazo.

### Resolver `zsh: command not found: uv`

`uv` es una herramienta instalada aparte; tener `backend/.venv` no garantiza que el comando esté disponible. En este Mac ya se instaló con Homebrew y se verificaron `uv --version`, `uv sync --frozen --dev` y `uv run alembic --version`.

Si la terminal sigue abierta en `backend`, ejecutar:

```bash
rehash
uv --version
uv sync --frozen --dev
```

En otro equipo con Homebrew, instalarlo primero:

```bash
brew install uv
rehash
uv --version
```

Si sigue sin encontrarlo en este Mac, usar la ruta verificada:

```bash
/opt/homebrew/bin/uv --version
/opt/homebrew/bin/uv sync --frozen --dev
```

La instalación por Homebrew está documentada por [Astral](https://docs.astral.sh/uv/getting-started/installation/#homebrew).

### Arranque local, en orden

Los comandos de `uv` se ejecutan dentro de `backend`, que contiene `pyproject.toml`. No volver a hacer `cd backend` si la terminal ya está allí. Conservar el `.env` existente y revisar la `DATABASE_URL` del entorno que se quiere actualizar.

Desde la raíz, si se usará el PostgreSQL local del proyecto:

```bash
docker compose -f infra/docker-compose.local.yml up -d
```

En la terminal del backend, con la configuración local preparada según el [README](../../README.md):

```bash
uv sync --frozen --dev
uv run alembic upgrade head
uv run alembic current
uv run uvicorn app.main:app --reload --port 8000
```

En otra terminal, desde la raíz:

```bash
cd backend
uv run python -m app.trabajos.ejecutor
```

En una tercera terminal, desde la raíz:

```bash
cd frontend
npm ci
VITE_API_BASE_URL= API_PROXY_TARGET=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Abrir `http://127.0.0.1:5173`. El origen/retorno OAuth debe coincidir con el host configurado; usar el mismo host en las URLs del frontend, cookies y retorno registrado. Si el proyecto ya está desplegado, realizar el recorrido en su URL de ensayo y no iniciar otra base para esa prueba. La configuración completa, incluidas las credenciales OAuth, está en el README.

## 3. Orden recomendado

Primero ejecutar el recorrido básico: **M01 → M03 → M04 → M05 → M06 → M10 → M11 → M16/M17 → M18 → M19 → M27 → M29 → M25 → M31 → M34 → M36 → M40 → M41**. Hacerlo con datos preparados puede tomar aproximadamente 30–45 minutos; los tiempos de los proveedores pueden alargarlo.

Después recorrer los casos restantes y las variantes de error. Ejecutar **retiro, desvinculación y archivo al final**, para que no bloqueen las pruebas que necesitan vínculos operativos. Reservar una sesión posterior para los casos sujetos a calendario.

## 4. Acceso, curso y equipo

| Caso | Pasos en la aplicación | Resultado que hay que comprobar |
| --- | --- | --- |
| M01 · Acceso y usuario nuevo | Sin sesión, abrir una URL interna de curso. Entrar con Google usando una cuenta admitida. Con una cuenta nueva, visitar Cursos. Repetir con un correo no admitido. | La ruta protegida pide acceso y conserva el destino permitido. El usuario nuevo ve un estado vacío y «Crear mi primer curso». El correo rechazado recibe una explicación; no se crea una sesión válida. |
| M02 · Perfil y sesiones | Editar el nombre y recargar. Abrir dos sesiones con la misma cuenta en perfiles distintos. Cerrar una sesión desde Perfil y verificar ambas. Revisar identidades Canvas propias. Intentar cerrar la cuenta del único profesor de un curso. | El nombre persiste y el correo no se edita. Sólo se cierra la sesión elegida. Las identidades corresponden a esa cuenta. El cierre bloqueado muestra el curso que necesita otro profesor. Probar la desvinculación de una credencial de ensayo al terminar M04–M06. |
| M03 · Crear y administrar curso | Crear «Curso QA» con código, período, slug y zona `America/Santiago`. Probar un campo requerido vacío, una zona inválida y un slug duplicado. Recargar y buscar el curso. | Se crea una sola entidad y conduce a su configuración. Los errores aparecen en los campos; el formulario conserva datos. La tarjeta y el curso abierto corresponden al mismo ID. |
| M04 · Canvas y renovación | Buscar cursos con un token inválido; repetir con el token propio válido y los consentimientos. Elegir el curso correcto. Renovar el vínculo con otra credencial propia. Desde otro curso local, comprobar que ese curso Canvas aparece ocupado. | El fallo no aparece como éxito. Se muestran nombre/ID del curso elegido y titular de la credencial. La renovación conserva tarea/personas/historia y sigue vinculada al mismo UUID local. El segundo curso no puede apropiarse del vínculo. |
| M05 · GitHub App | Iniciar la instalación, seleccionar la organización y repositorios previstos, regresar a la app y revisar el vínculo. Probar cancelar el flujo en una instalación de ensayo. | Se usa GitHub App, se valida el retorno y se muestra la organización correcta. Cancelar no deja una instalación aparentemente operativa. No se pide OAuth GitHub a estudiantes. |
| M06 · Verificación | Ejecutar el checklist y esperar su estado real. Recargar durante la ejecución. Revisar los 19 ítems y un fallo preparado. Para las pruebas de anuncio/comentario, revisar el consentimiento antes de aceptarlo. | Se retoma la ejecución, se muestran estado/intentos y los ítems no resueltos siguen pendientes o fallidos. Las pruebas de escritura sólo ocurren después del consentimiento y dejan evidencia en el Canvas de ensayo. |
| M07 · Ajustes | Cambiar nombre, zona y umbrales; probar valores inválidos y guardar. Configurar un ID real de rol Canvas derivado de estudiante y sincronizar Personas. | Los valores válidos persisten. Las fechas históricas conservan sus instantes y se muestran en la zona nueva. Los roles amplían el padrón sin duplicados ni docentes. No usar IDs inventados: obtenerlos de la administración Canvas de ensayo. |
| M08 · Incorporación y permisos | Incorporar al otro profesor y a los ayudantes. Abrir cada invitación en el perfil nominal y también con otra cuenta. Probar revocar una invitación pendiente. Conceder/quitar por separado los cinco permisos editables de ayudante, sin cerrar su sesión. | Otro profesor tiene los mismos nueve permisos. La invitación sólo se acepta con la cuenta indicada. El ayudante conserva los dos permisos implícitos y nunca recibe administración de curso/equipo. La revocación y los cambios afectan la siguiente acción, incluso con una pestaña previamente abierta. |
| M09 · Retiro y reincorporación | Asignar una corrección con borrador a un ayudante. Revisar impacto de retiro, cancelar y volver a confirmar. Intentar usar su pestaña abierta. Reincorporarlo. Intentar retirar al último profesor. | Cancelar no cambia nada. El retiro bloquea acceso y muestra el impacto real de repositorios/asignaciones; conserva el borrador y la historia. La reincorporación restaura la membresía según el flujo previsto, sin fingir acceso GitHub ya concedido. El último profesor no se puede retirar. |

## 5. Personas, enrolamiento y pendientes

| Caso | Pasos en la aplicación | Resultado que hay que comprobar |
| --- | --- | --- |
| M10 · Sincronizar padrón | En Personas, sincronizar Canvas y observar el trabajo hasta terminar. Comparar estudiantes, estados, secciones, conjuntos, grupos e integrantes con Canvas. Filtrar/buscar, recargar y regresar desde Pendientes. | El espejo coincide con la fuente, muestra cuándo se sincronizó y conserva filtros. Los datos viejos siguen legibles durante la actualización. Un trabajo en curso no se anuncia como terminado. |
| M11 · Mapeo individual y registro | En un pendiente, entrar a Personas, «Asociar cuenta», validar un login de ensayo y guardar. Probar un login inexistente o una asociación incompatible. Crear la tarea de registro Canvas con su confirmación; declarar otra cuenta desde Canvas y esperar la recogida. | Se asocia el estudiante correcto y aparece su historial. Los errores conservan lo escrito. El registro se confirma mediante el trabajo y realmente existe en Canvas. La declaración posterior se recoge sin que el estudiante entre en nuestra app. |
| M12 · CSV con revisión | Importar filas válidas junto a una fila desconocida/inválida. Leer la previsualización y aplicar sólo lo revisado. Después cambiar el archivo/texto y tratar de aplicar la revisión anterior. Recargar Personas. | La vista previa distingue filas válidas y errores; no escribe antes de aplicar. Cambiar el CSV invalida la revisión anterior. Persisten únicamente los resultados aceptados por el servidor, asociados por identidad estable. |
| M13 · Causas y recordatorios | Revisar cada grupo de Pendientes y abrir la persona correspondiente. Enviar un recordatorio manual al destinatario de ensayo; repetir inmediatamente y recargar. Para el límite automático, usar un caso con historia ya preparada. | Se muestran causa, último envío y próxima fecha permitida. El segundo envío dentro de 24 h se rechaza sin duplicarse. Agotar tres recordatorios automáticos no bloquea uno manual cuando ya transcurrieron sus 24 h. |
| M14 · Invitación GitHub dirigida | Abrir las invitaciones de un estudiante; comprobar/reenviar una pendiente y observar el trabajo. Dar doble clic, comprobar los accesos de otros estudiantes y aceptar la invitación desde GitHub. Probar casos preparados con reenvío reciente y tres reenvíos previos. | No se duplica una invitación todavía vigente. El doble clic devuelve una sola operación. Otros accesos se conservan. La aceptación se refleja tras reconciliar. Se respeta el intervalo de 24 h y el máximo de tres reenvíos; la UI explica el bloqueo. |
| M15 · Posible fusión Canvas | En ensayo, preparar una identidad retirada y una nueva con coincidencia exacta de login/SIS; sincronizar. Revisar evidencia e historial en Personas, cancelar y después confirmar como profesor. Repetir con nombres iguales sin coincidencia de identificador, y con ambas identidades teniendo evidencia productiva. | No hay fusión automática ni por nombre. La confirmación conserva el UUID con historia, repositorios, mapeos y SHA; la fila nueva queda como alias. El caso con dos historiales productivos se bloquea con motivo y no mueve evidencia arbitrariamente. |

## 6. Tareas, base y repositorios

| Caso | Pasos en la aplicación | Resultado que hay que comprobar |
| --- | --- | --- |
| M16 · Tarea individual | Tareas → «Crear tarea» → elegir una tarea Canvas individual → «Crear borrador». Revisar nombre, modalidad, puntos/entrega y configuración antes de activar. | La configuración deriva de Canvas y conduce a una tarea local real. Recargar conserva el borrador. No aparecen repositorios como creados antes de activar y completar el trabajo. |
| M17 · Grupo y múltiples entregas | Crear otra tarea desde un assignment grupal. Vincular una parcial y una final del mismo conjunto; probar otro conjunto o modalidad incompatible. Revisar la opción de nota individual en Entregas; si se cambia, hacerlo en Canvas y solicitar sincronización. Intentar desvincular una entrega que ya tiene evidencia. | Se reconoce el conjunto y sus integrantes. Parcial/final comparten repositorios, pero tienen entregas independientes. Se rechaza la incompatibilidad. La app no modifica el assignment vinculado; refleja el ajuste tras sincronizar. La evidencia existente no desaparece al desvincular/excluir. |
| M18 · Repositorio base | Antes de activar, crear la base opcional. Subir `README.md` y un archivo inicial pequeño; abrir, modificar, reemplazar, renombrar y borrar un archivo de ensayo. Volver a listar. | Las operaciones se confirman y persisten en la base. La previsualización corresponde al archivo elegido. Los mensajes identifican la ruta y los errores conservan el formulario. Crear sin base también es válido. |
| M19 · Activación y creación | Revisar la vista previa de nombres, activar una tarea con base y otra sin base. Observar Repositorios; recargar o repetir una solicitud pendiente. Comprobar nombres, archivos iniciales y colaboradores en GitHub. | Se crean automáticamente repositorios inequívocos por estudiante/grupo. No se duplica el repositorio por repetir la solicitud. La base se copia cuando existe y los estados de espera/fallo se distinguen de un repositorio listo. |
| M20 · Incorporación progresiva y fallos | Activar con un estudiante/grupo sin mapeo. Confirmar que los sujetos preparados avanzan. Completar luego la asociación desde Personas y esperar la reconciliación automática. En otro caso de ensayo, resolver una causa de fallo y usar su reintento visible. | No se bloquea toda la tarea por un pendiente. El repositorio pendiente se crea al disponer de la información, sin acción del estudiante en nuestra app. El reintento conserva nombre/historia y muestra el resultado real. Si no progresa, registrar estado e ID del trabajo. |
| M21 · Accesos y aviso al estudiante | Verificar colaboradores por repositorio, aceptar invitaciones en las cuentas GitHub de ensayo y comprobar accesos desde la app. Revisar la comunicación de disponibilidad en el Canvas del destinatario. | Cada estudiante recibe acceso al repositorio que le corresponde y el profesor conserva el suyo. La app distingue invitación de acceso concedido, con fecha de comprobación. El mensaje de Canvas tiene el enlace correcto; la cola sola no acredita entrega. |

## 7. Fechas y versiones

| Caso | Pasos en la aplicación | Resultado que hay que comprobar |
| --- | --- | --- |
| M22 · Fechas y excepciones | En Entregas, comparar fecha base, fecha por sección y extensión individual/grupal con Canvas. Revisar origen, zona y cualquier ambigüedad preparada. | La fecha efectiva corresponde a ese sujeto y entrega; no se aplica una extensión a otros. La UI muestra origen/candidatas y zona horaria. Una fecha ausente/ambigua no se presenta como una fecha inventada. |
| M23 · Cambio de fecha | Cambiar una fecha/override en Canvas; sincronizar desde la app y esperar el trabajo. Abrir el historial de fechas y comparar con una entrega cuya versión ya estaba registrada. | Se actualiza el espejo y se conserva el historial. La modificación no sobrescribe automáticamente una versión congelada ni una nota publicada. |
| M24 · Captura automática al cierre | Preparar una fecha cercana y commits anteriores. Mantener API/trabajador activos, esperar el cierre y comprobar la versión. Crear después otro commit en GitHub. | Se registra el SHA que corresponde al corte, sin pulsar una captura manual para aprobar este caso. El commit posterior no cambia ese SHA. La etiqueta Git se muestra aparte; un fallo de etiqueta no inventa otra evidencia. |
| M25 · Versiones por entrega y acceso | En una tarea con parcial y final capturadas, alternar entregas, abrir versión vigente/históricas y seguir el enlace al código. Repetir como ayudante autorizado. | Cada par entrega/sujeto muestra su versión propia. El código abierto corresponde al SHA mostrado, no a la rama actual. El repositorio es compartido entre entregas y la evidencia de cada una permanece independiente. |
| M26 · Captura manual y recaptura | Como profesor, capturar un caso permitido, recapturar con fecha explícita y motivo, y fijar un SHA válido de ensayo. Intentar la misma acción como ayudante sin el permiso necesario. | Las versiones anteriores siguen disponibles y los motivos quedan registrados. Se respeta la fecha con zona. La recaptura no publica ni cambia una nota anterior; para volver a calificar hay reapertura explícita. El rechazo de permisos no modifica la versión. |

## 8. Seguimiento y timeline

| Caso | Pasos en la aplicación | Resultado que hay que comprobar |
| --- | --- | --- |
| M27 · Tablero y períodos | Abrir una tarea con actividad ya recogida. Revisar sus bloques, fechas/estado de entregas y repositorios; filtrar sección, estado, alertas y período de parcial/final. Entrar al detalle y regresar. | El espejo se consulta sin esperar un barrido completo de GitHub. Se conserva el contexto al volver. Se distinguen cero real, dato ausente, datos antiguos y fallo de actualización. |
| M28 · Participación y métricas | Comparar dos integrantes con actividad distinta, otro sin commits, otro sin atribución y otro sin acceso. Revisar actividad diaria, líneas/días activos y avisos de coautoría. | Se señalan inactividad y falta de participación con evidencia. «Sin atribuir» o «Sin acceso» no se convierten en cero participación. Las métricas corresponden al período elegido y explican sus límites. |
| M29 · Timeline e identidades | Abrir el timeline de un repositorio desde el tablero. Filtrar rama/integrante/período y revisar commits, cambios de integrantes y entregas. Marcar/quitar un hito con permiso. Revisar una identidad sin atribuir, revelar su correo por el flujo permitido y previsualizar una propagación antes de seleccionarla. | Los filtros afectan ese repositorio y el retorno conserva el tablero. Los hitos persisten. La identidad no se asocia sólo por nombre ni propaga a repositorios no seleccionados. Los correos completos no aparecen automáticamente para todos. |
| M30 · Paginación y CSV | Con más de una página y, para la prueba de volumen, 200 sujetos preparados, avanzar/retroceder y aplicar filtros. Exportar CSV con la tabla filtrada. Comparar filas y totales. | Las páginas no mezclan filtros. El CSV contiene todas las filas coincidentes, no sólo las visibles; conserva el período y criterios. Un nombre largo no rompe la tabla. Si sólo hay seis sujetos, no marcar como comprobado el caso de 200. |

## 9. Corrección y publicación

| Caso | Pasos en la aplicación | Resultado que hay que comprobar |
| --- | --- | --- |
| M31 · Reparto y pesos | En Corrección → «Repartir correcciones», probar equitativo, manual, por sección y copia de entrega anterior. Editar un peso válido y uno fuera de 0–10. Previsualizar, cancelar y luego aplicar con confirmación. Revisar la otra entrega. | La previsualización no reasigna. Sólo la confirmación aplica el reparto mostrado. Cambiar pesos invalida la propuesta sin reasignar solo. Cada entrega conserva su reparto; los cambios de corrector no borran borradores. |
| M32 · Realineación | Con un reparto nuevo que tenga contexto, cambiar sección/grupo en Canvas y sincronizar. Revisar las marcas de desalineación. Previsualizar «Realinear sólo las asignaciones que requieren revisión» y aplicar. Probar un caso ambiguo. | Se marca el cambio sin reasignación silenciosa. La realineación usa el criterio original, conserva nota/comentario y actúa sólo sobre filas elegibles. Los casos ambiguos piden una decisión docente. No se inventa el criterio de un reparto antiguo sin contexto. |
| M33 · Asignaciones y privacidad | Entrar como ayudante, abrir «Mis asignaciones», filtrar entrega/sección/estado y usar Anterior/Siguiente. Consultar la matriz y una corrección no asignada, incluso concediéndole sólo `nota.publicar`. | El recorrido conserva entrega/filtros y no cruza a otra. La matriz se puede leer con `curso.ver`. Un ayudante no asignado no obtiene el borrador privado; conceder publicación no concede su lectura. |
| M34 · Código, rúbrica y borrador | Abrir una corrección propia, comprobar entrega/SHA y seguir el enlace al código. Revisar la rúbrica leída de Canvas, seleccionar niveles e introducir nota/comentario válidos. Guardar y recargar. Revisar autor, fecha y comentario que se publicará. | El código es la versión correcta. La rúbrica no se edita en nuestra app. Guardar persiste el borrador y su autoría, pero no escribe una nota en Canvas ni lo marca publicado. Nota/estado/contraste son datos distintos. |
| M35 · Protección del borrador | Editar sin guardar. Usar Anterior, un enlace, Atrás/Adelante y recargar/cerrar. Cancelar la salida cuando corresponda. En dos pestañas, guardar primero en una y después intentar guardar la versión vieja de la otra. | Cancelar conserva el formulario. Las salidas advierten los cambios. El conflicto de edición no sobrescribe el borrador nuevo y permite recuperar el contenido local. No se afirma guardado antes de la respuesta. |
| M36 · Publicación individual | En un caso publicable, guardar, «Marcar lista» y «Publicar en Canvas». Cancelar el diálogo una vez; después confirmar. Esperar estado/contraste y abrir el libro de calificaciones Canvas del mismo assignment/estudiante. | Cancelar no escribe. Confirmar registra nota/comentario y el resultado de verificación. La nota realmente aparece en Canvas. Si aparece advertencia/error, registrarlo como tal; guardar o quedar en «Publicando» no equivale a publicación confirmada. |
| M37 · Conflicto con Canvas | Preparar una nota externa distinta en Canvas para tres correcciones independientes. Abrir la publicación y probar por separado «Dejarlo como está», «Adoptar la de Canvas» y «Publicar la mía». | Se ofrecen las tres decisiones sin elegir por el usuario. Dejar conserva ambos lados; adoptar cambia el reflejo/local según el contrato sin escribir una nota externa nueva; publicar la propia exige confirmación y vuelve a verificar. Se conserva el historial de publicaciones. |
| M38 · Publicación masiva | Con varias correcciones listas, seleccionar dos y dejar otra sin seleccionar. Revisar resumen y confirmar. Incluir un fallo preparado y una corrección ya publicada. Salir de la vista durante otro lote de ensayo. | Sólo se publican las seleccionadas elegibles, con resultados por sujeto. No se duplica una ya confirmada. Un fallo no presenta a todo el lote como exitoso. Salir detiene las siguientes solicitudes; no deshace una publicación ya confirmada. |
| M39 · Bloqueos, revisión y reclamos | Abrir casos con un período cerrado/no calificable y otro sin commits. Revisar la causa; preparar una nota por falta de entrega sólo con selección explícita. Añadir una nota interna/reclamo, cerrarlo con desenlace y reabrir una corrección publicada con motivo. | Se muestra el motivo del bloqueo sin confundirlo con el estado de corrección. La ausencia de datos no selecciona ni asigna cero automáticamente. Reabrir es explícito, conserva la publicación anterior y no publica de nuevo por sí solo. El reclamo conserva autoría y desenlace. |

## 10. Informes y comunicaciones

| Caso | Pasos en la aplicación | Resultado que hay que comprobar |
| --- | --- | --- |
| M40 · Informe y suscripción | Consultar informe diario e histórico con tareas activas; comprobar otro curso sin tareas activas. Suscribir profesor y ayudante, darse de baja individualmente y pedir el envío propio disponible. Revisar el buzón de ensayo cuando haya proveedor real. | El informe contiene situaciones de esa fecha/curso; no rehace el histórico con datos actuales. Sin tareas activas no se envía un informe ficticio. La baja de una persona no afecta a otra. La cola/console de correo no acredita entrega real al buzón. |
| M41 · Mensaje y anuncio | En Comunicaciones, redactar para un estudiante/grupo de ensayo y previsualizar. Cancelar, volver a editar y confirmar. Crear un anuncio por sección y confirmar su alcance nominal. Revisar bandeja, filtros, detalle y destino en Canvas; probar cancelación/reintento/retractación sólo cuando la acción esté disponible. | Los destinatarios y contenidos coinciden con la vista previa. El anuncio no llega a secciones no seleccionadas. El historial diferencia cola, envío y fallo. Un fallo conserva el texto; el estado final y la existencia del mensaje/anuncio se comprueban en Canvas. |
| M42 · Automatizaciones y aviso docente | Revisar las seis reglas de tarea y el recordatorio de mapeo del curso; activar/desactivar y guardar. Con un evento de ensayo preparado, comprobar una regla habilitada y otra deshabilitada. Como ayudante sin reparto, solicitar aviso por entregas sin corrector y repetir inmediatamente. | Las reglas persisten y los eventos siguen la opción elegida. Un evento futuro requiere esperar/prepararlo; no se aprueba sólo por guardar la regla. El aviso docente queda visible en Comunicaciones, sin duplicarse en 24 h ni marcar un envío simulado como real. |

## 11. Cierre, recuperación y revisión final

| Caso | Pasos en la aplicación | Resultado que hay que comprobar |
| --- | --- | --- |
| M43 · Cierre de repositorios | En Entregas/Cierre, revisar las cinco guardas: versiones capturadas, acceso docente, invitaciones resueltas, aviso previo y correcciones terminadas. Probar un bloqueo de cada tipo. Con un caso elegible, archivar, esperar el trabajo y comprobar GitHub; después desarchivar desde el cierre de la tarea. | No se omiten guardas, y se reevalúan al trabajar. Un cierre futuro bloquea el archivo; el aviso normal exige 14 días desde el último envío, y las excepciones sólo se aceptan en los casos expresamente ofrecidos. GitHub confirma el archivo/desarchivo. Versiones y borradores permanecen. |
| M44 · Archivo del curso | En Ajustes, descargar inventario y revisar cierres sin captura. Cancelar el archivo; luego confirmar el slug con «Archivar también los repositorios en GitHub» desmarcado. Revisar una pestaña antigua e intentar escribir. Reactivar. En otro caso elegible, probar la opción remota marcada. | Cancelar no cambia nada. El curso archivado queda legible, pausa procesos/comunicaciones y bloquea escrituras incluso desde pestañas viejas. Reactivar conserva datos y restaura las pausas previas; cancela archivos remotos pendientes. Los repositorios ya archivados se reactivan desde su tarea. La opción remota respeta las cinco guardas. |
| M45 · Red, sesión y trabajos | Desconectar la red del navegador en una lectura y en un formulario de ensayo, reconectar y recuperar. Con un trabajo en vuelo, recargar/volver por su URL. Revocar esa sesión desde otro perfil y volver a intentar una acción. Revisar un caso de cooldown. | Los errores son recuperables y conservan datos/formulario; las mutaciones no se reenvían silenciosamente. Los trabajos mantienen identidad, estado e intentos. La sesión revocada pide acceso con destino permitido; un rechazo de permiso no se confunde con sesión vencida. Los límites explican cuándo reintentar. |
| M46 · Móvil y teclado | Recorrer Cursos, navegación, Personas/Pendientes, Tablero, Entregas y Corrección a 1366×768, 768×1024, 390×844 y 360 px. Probar Tab/Shift+Tab, Escape, abrir/cerrar diálogos y zoom 200 %. Usar nombres/comentarios largos y filtros vacíos. | No hay desborde horizontal del documento ni acciones tapadas. Las tablas pueden desplazarse dentro de su región. Se leen nota, rúbrica y confirmación; el foco es visible, se contiene en el diálogo y vuelve a un control válido. Las etiquetas/estados se entienden sin depender del color. |
| M47 · Aislamiento y permisos directos | Copiar URLs de administración y de una corrección a otro perfil sin permiso. Probar una cuenta fuera del curso y comparar cursos A/B. Revocar un permiso con una pestaña abierta y reintentar. | No se accede por conocer una URL/ID, ni se mezclan estudiantes, repositorios, notas o CSV entre cursos. La API rechaza la acción aunque el botón estuviera visible antes. No se muestra contenido privado mientras carga el contexto. |
| M48 · URL pública y entrega | En un navegador limpio, abrir la URL desplegada, entrar con una cuenta docente autorizada y repetir creación/consulta de un dato de ensayo. Reabrir después para comprobar persistencia. Revisar los enlaces de video/repositorio que se entregarán en Canvas. | La URL sirve al evaluador con el flujo normal de acceso, no depende del ordenador del grupo y persiste datos. El video se abre sin solicitar un permiso al autor y dura como máximo 3 min. Preparar disponibilidad por al menos dos semanas y la declaración de uso de IA, según §3.2. |

## 12. Cobertura del enunciado

La trazabilidad detallada ya está en [REQUISITOS.md](REQUISITOS.md). Para planificar esta revisión:

| Requisitos | Casos manuales |
| --- | --- |
| R2.1.1–R2.1.9 · Usuarios, cursos y equipo | M01–M09; M44 y M47. |
| R2.2.1–R2.2.6 · Estudiantes, grupos y enrolamiento | M10–M15. |
| R2.3.1–R2.3.12 · Tareas y repositorios | M16–M21; M41–M43. |
| R2.4.1–R2.4.8 · Fechas y versiones | M22–M26. |
| R2.5.1–R2.5.10 · Seguimiento y timeline | M27–M30. |
| R2.6.1–R2.6.7 · Informes y comunicaciones | M40–M42. |
| R2.7.1–R2.7.7 · Corrección | M31–M39. |
| Recuperación, presentación y acceso público | M45–M48, además del caso funcional correspondiente. |

## 13. Registro de ejecución

Copiar esta plantilla por caso o usar una planilla con las mismas columnas. En las capturas, incluir la entidad/estado necesario para comparar antes y después, sin tokens ni credenciales.

```text
Fecha / persona que probó:
URL y versión/commit:
Caso M__:
Rol y cuenta de ensayo:
Curso / tarea / entrega / sujeto:
Proveedores: reales / dobles (indicar cuáles)
Precondición y datos utilizados:
Resultado esperado:
Resultado observado:
Estado: Aprobado / Falló / Bloqueado / No ejecutado
Evidencia: captura, URL de Canvas/GitHub, ID del trabajo si corresponde
Pasos para reproducir el fallo:
```

No dar por cerrado el ensayo si falla acceso, aislamiento, conservación de borradores/versiones, creación progresiva o publicación verificada. Las variantes sujetas a credenciales, historia o calendario deben quedar identificadas como bloqueadas/no ejecutadas, con el dato que falta. Una prueba automática anterior no reemplaza esa anotación manual.

## 14. Comprobación automática complementaria

Desde la raíz, sin utilizar la base del equipo:

```bash
backend/.venv/bin/python frontend/tests/serve_backend.py --pytest -q --cov=app.dominio --cov-fail-under=70
```

Desde `frontend`:

```bash
npm run format:check
npm run lint
npm run typecheck
npm run build
npm test
npm run test:backend
```

El último comando necesita Docker y levanta su propia base efímera con proveedores dobles. No ejecutar el pytest normal del backend contra una base con datos: sus pruebas limpian tablas. Estas comprobaciones complementan la revisión manual y no certifican OAuth, correo o notas contra proveedores reales.
