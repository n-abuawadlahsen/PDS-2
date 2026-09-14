# Preguntas de alcance — Area 2.5

66 preguntas finales, fusionadas desde 76 de entrada (10 preguntas absorbidas por fusion de duplicados y casi-duplicados); 3 bloquean la entrega parcial; 0 preguntas ya respondidas por el enunciado.

## Arquitectura de ingesta y frescura de los datos

### Q-2.5-01 — ¿Que arquitectura de ingesta de actividad se adopta y cual es la latencia maxima aceptable entre un push y su aparicion en el dashboard y el timeline?

Hay que decidir entre webhooks de la GitHub App como fuente principal complementados con un polling de reconciliacion periodico (por ejemplo cada 15 minutos, con ETag), polling puro sin URL publica expuesta (mas simple de desplegar, latencia de minutos), o webhooks sin reconciliacion. La decision determina si la entrega parcial ya necesita una URL publica accesible desde GitHub. Ademas hay que fijar la latencia maxima aceptable como criterio de aceptacion verificable (por ejemplo, un commit visible en el dashboard en menos de N minutos desde el push) y si esa latencia se mide de extremo a extremo o solo desde la recepcion del evento.

- **Requisitos:** R2.5.1, R2.5.2, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Decide si la entrega parcial requiere URL publica para webhooks, el diseno del receptor y de los jobs del worker, y el requisito no funcional de frescura de datos que sostiene la exigencia de "informacion disponible de forma inmediata" del enunciado.
- **Opciones:**
  - Webhooks + reconciliacion periodica (propuesta del estudio)
  - Solo polling cada N minutos
  - Webhooks sin reconciliacion
  - Webhooks + reconciliacion, con latencia objetivo declarada y medida
- **Estudio de APIs:** §8.1 (webhooks de la App), §8.2 (reconciliador cada 15 min con ETag) y §12 (worker de backfill_commits cada 15 min) recomiendan la combinacion de ambos, pero la propuesta no esta aprobada por el equipo y §8.1/§8.2 no fijan latencia objetivo.
- **Fusiona:** P424

### Q-2.5-02 — ¿A que eventos de webhook se suscribe la GitHub App, para que se usa cada uno, y que entregan realmente segun verificacion empirica contra la API?

Candidatos: `push` (commits), `create`/`delete` (ramas y tags), `repository` (renombrado, borrado, archivado, transferido), `member` (colaborador agregado, es decir invitacion aceptada) y `member_invite`. Hay que confirmar contra la API real que `member` con `action: added` se dispara al aceptar la invitacion de colaborador, si existe algun evento para invitacion rechazada o expirada, y que entrega cada evento en repositorios privados de la instalacion. Si se decide contar actividad no-commit (ver Q-2.5-27) la lista se amplia a `pull_request`, `pull_request_review`, `pull_request_review_comment`, `issues` e `issue_comment`, con su volumen asociado.

- **Requisitos:** R2.5.2, R2.5.5, R2.5.10
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define que eventos puede mostrar el timeline (invitacion aceptada, creacion de repo, ramas) y como se actualiza el estado COLLABORATORS_PENDING sin recurrir a polling.
- **Opciones:**
  - Suscripcion minima: solo push
  - push + create/delete + repository
  - push + create/delete + repository + member + member_invite
  - Lo anterior mas eventos de pull requests, revisiones e issues
- **Estudio de APIs:** §8.1 lista push, create, delete, repository, member y member_invite "segun disponibilidad", sin verificar la semantica de cada uno ni cubrir eventos de pull requests o issues.
- **Fusiona:** P425

### Q-2.5-03 — ¿Que claves y garantias de idempotencia, orden y concurrencia tiene el pipeline de ingesta?

Hay que decidir: (a) si la clave del registro de commit es `(repository_id, sha)` en lugar de `sha` solo, dado que un mismo SHA puede existir en dos repositorios con historia compartida (forks, repos clonados de una plantilla comun); (b) si ademas se deduplican las entregas repetidas del webhook por `X-GitHub-Delivery`; (c) como se garantiza que un mismo push procesado dos veces (reintento de GitHub) o eventos que llegan fuera de orden no dupliquen commits ni corrompan agregados; (d) como reaparece un push perdido durante una caida del receptor; (e) si se serializa el procesamiento por repositorio mediante un lock, dado que el receptor de webhooks y el reconciliador pueden procesar el mismo repositorio simultaneamente; (f) como se garantiza que `last_commit_at` nunca retroceda y que un mismo dia no se agregue dos veces; (g) que ocurre con un webhook que llega mientras hay un backfill en curso para ese repositorio; y (h) si los agregados (RepoActivityDaily, RepoStatus) se recomputan integros desde los commits (derivables e idempotentes) o se incrementan en linea (con riesgo de doble conteo al reprocesar).

- **Requisitos:** R2.5.2, R2.5.3, R2.5.7, R2.5.8, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija el esquema, la clave de idempotencia de la ingesta y la estrategia de concurrencia del worker; sin ellas los reintentos de webhook duplican commits en los KPIs y aparecen inconsistencias visibles en el dashboard.
- **Opciones:**
  - Clave (repository_id, sha) + deduplicacion por delivery id + agregados recomputados desde commits
  - Clave sha unica + agregados incrementales en la ingesta
  - Lock por repositorio con serializacion estricta de receptor y reconciliador
  - Sin lock, con operaciones idempotentes (upsert) y recomputacion de agregados al final
- **Estudio de APIs:** §8.1 propone responder 202 y procesar en background; §8.2 propone un reconciliador cada 15 min con ETag; §8.3 propone `sha` como PK y una tabla agregada "actualizada en cada ingesta", sin especificar recomputacion ni deduplicacion por `X-GitHub-Delivery`; §5.5 habla de lock por sujeto solo para la creacion de repos, no para la ingesta.
- **Fusiona:** P400, P429, P430

### Q-2.5-04 — ¿Como se completan los pushes que traen mas commits de los que caben en el payload del webhook, y que tope de commits por push se ingiere?

El evento `push` incluye como maximo 20 commits en `commits[]`; un push mayor (por ejemplo un estudiante que sube un proyecto existente con 300 commits) exige completar via API usando `before`/`after`. La Compare API esta limitada a 250 commits; la alternativa es listar `GET /commits?sha=after` hasta llegar a `before`. Hay que definir como se implementa ese relleno y a partir de que tope de commits se marca el repositorio para un backfill completo en lugar de rellenar en linea.

- **Requisitos:** R2.5.2, R2.5.10
- **Tipo:** investigable_en_docs · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin este manejo el dashboard subcuenta silenciosamente los pushes grandes, precisamente los que corresponden a los casos mas anomalos; el tope es una decision de alcance del equipo.
- **Opciones:**
  - Relleno via Compare API (before..after) con tope de 250
  - Relleno listando commits desde `after` hasta encontrar `before`
  - Marcar el repositorio para backfill completo por encima de un tope de commits
  - Ingerir solo los commits del payload y aceptar la subcuenta
- **Estudio de APIs:** no lo aborda; §8.1 describe `commits[]` sin mencionar el limite de 20 elementos.
- **Fusiona:** P426

### Q-2.5-05 — ¿Que backfill de historial se hace cuando un repositorio entra al sistema, y se soporta adoptar repositorios creados fuera de la aplicacion?

Aplica al alta por creacion del worker, a la reinstalacion de la App y a un reinicio con base de datos vacia. Hay que decidir si se hace backfill completo del historial, si se incluyen los commits heredados del repositorio base o de la plantilla (y si se marcan como "base"), si existe un tope de commits o de paginas por repositorio para el backfill inicial, y si existe la funcionalidad de "adoptar" repositorios creados fuera de la aplicacion cuyo historial es previo a la instalacion de la App.

- **Requisitos:** R2.5.2, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina el costo del arranque (60 repositorios por N paginas cada uno), la completitud del timeline y si existe o no la funcionalidad de adopcion de repositorios externos.
- **Opciones:**
  - Backfill completo sin tope
  - Backfill completo con tope de paginas o de commits por repositorio
  - Backfill solo desde la fecha de creacion de la tarea
  - Sin backfill: solo actividad posterior al alta en el sistema
- **Estudio de APIs:** §8.2 afirma que "hay que hacer un backfill completo la primera vez que un repo entra al sistema"; no aborda topes, commits heredados de la plantilla ni repositorios externos.
- **Fusiona:** P428

### Q-2.5-06 — ¿Como se cubre el hueco de `GET /commits?since=`, que filtra por fecha del commit y no por fecha de push, y se persiste un cursor de backfill reanudable?

Un commit creado antes de `last_synced` pero pusheado despues (trabajo offline de dias, rebase, rama fusionada tarde) nunca sera traido por el reconciliador propuesto: los webhooks lo cubren salvo durante caidas. Hay que decidir entre aceptar el hueco, recorrer desde el head de cada rama hasta un SHA ya conocido (graph-walk), comparar `before..after` guardando el ultimo head visto por rama, o hacer un backfill completo periodico. Ademas, si se persiste un cursor de backfill (pagina o SHA) para reanudar backfills interrumpidos. Debe verificarse empiricamente con un commit retrodatado pusheado despues del ultimo sync.

- **Requisitos:** R2.5.2, R2.5.4, R2.4.7
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Un commit invisible para el reconciliador distorsiona "sin participacion" y "sin actividad reciente" y puede omitir commits anteriores al cierre de una entrega; define la estrategia de ingesta de respaldo.
- **Opciones:**
  - Aceptar el hueco
  - Graph-walk hasta un SHA conocido
  - Comparar before..after por rama guardando el ultimo head visto
  - Backfill completo periodico
- **Estudio de APIs:** §8.2 propone `since: last_commit_synced_at` mas ETag como respaldo de los webhooks; no advierte esta limitacion ni menciona cursores de reanudacion.
- **Fusiona:** P466

### Q-2.5-07 — ¿La precomputacion de agregados es incremental en cada evento ingerido o la hace un job periodico, y las alertas se evaluan en consulta o se materializan?

Hay que decidir si los agregados se actualizan al ingerir cada evento o si un job periodico recalcula agregados y alertas (cada 5, 10 o 15 minutos), y si las alertas "sin actividad reciente" y "sin participacion" se evaluan al momento de la consulta (sobre `last_commit_at`, barato, siempre al dia) o se materializan por el job con marca de tiempo (necesario para alimentar el informe diario y para conservar historico de alertas).

- **Requisitos:** R2.5.2, R2.5.3, R2.5.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la frecuencia de los workers, la latencia con la que aparece una alerta y si existe un historial de alertas consultable.
- **Opciones:**
  - Agregados incrementales en la ingesta y alertas evaluadas en consulta
  - Job periodico que recalcula agregados y materializa alertas
  - Hibrido: agregados incrementales y alertas materializadas por job
- **Estudio de APIs:** §8.3 indica que RepoStatus se "actualiza en cada ingesta" y §12 propone un worker de backfill cada 15 min; no separa el calculo de los agregados del calculo de las alertas.
- **Fusiona:** P433

### Q-2.5-08 — ¿Cual es el presupuesto real de rate limit del reconciliador y del registro de lineas, verificado empiricamente?

Hay que medir: 60 repositorios cada 15 minutos equivalen a 240 GET/h, mas 1 GET por commit si se registran lineas anadidas y eliminadas, mas el backfill inicial. Confirmar que las respuestas 304 con `If-None-Match` no descuentan del limite primario, que el ETag es estable mientras `since=` no cambia, y medir el costo real del backfill de 60 repositorios con historial.

- **Requisitos:** R2.5.2
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Valida la viabilidad de la frecuencia de polling elegida y del registro de lineas antes de fijarlos en el spec, y evita descubrir el agotamiento del limite durante la demostracion.
- **Opciones:**
  - Verificar y fijar frecuencia de polling en funcion del presupuesto medido
  - Fijar la frecuencia por diseno y monitorear el consumo en produccion
- **Estudio de APIs:** §2.4 afirma que "las conditional requests con 304 no descuentan del rate limit primario" y §8.2 propone ETag; no hay medicion empirica del backfill.
- **Fusiona:** P457

### Q-2.5-09 — ¿Hasta cuando se sigue ingiriendo actividad de los repositorios de una tarea y cuanto tiempo se conservan los payloads crudos de los webhooks?

Alternativas para el horizonte de ingesta: mientras la App este instalada, hasta N dias despues del ultimo cierre efectivo, o hasta que el profesor archive la tarea. Y por separado: si se conservan los payloads crudos de los webhooks para poder reprocesar ante bugs de atribucion, y por cuanto tiempo.

- **Requisitos:** R2.5.2, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Controla el consumo de rate limit y de almacenamiento a largo plazo y determina si se pueden recomputar metricas historicas despues de corregir una regla de atribucion.
- **Opciones:**
  - Ingesta indefinida mientras la App este instalada
  - Ingesta hasta N dias despues del ultimo cierre efectivo
  - Ingesta hasta el archivado manual de la tarea
  - Conservar payloads crudos con retencion definida / no conservarlos
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P459

## Modelo de datos del monitoreo

### Q-2.5-10 — ¿La atribucion commit-estudiante se almacena o se resuelve en consulta, y como se estructuran los agregados de actividad?

Hay que decidir: (a) si la atribucion se ALMACENA (columna `student_id` en CommitRecord mas la regla usada, lo que exige un job de reatribucion cuando cambian mapeos o alias) o se RESUELVE en consulta (join por login, email o alias vigente: siempre consistente pero mas costoso); (b) si RepoActivityDaily se normaliza por `(repository_id, student_id | author_key, day)` para soportar la comparacion por integrante y por periodo, o guarda un `authors_json` por `(repo, day)`; (c) si los agregados se recalculan integros desde CommitRecord (idempotente) o se incrementan durante la ingesta.

- **Requisitos:** R2.5.2, R2.5.4, R2.5.7, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina el costo de las consultas del dashboard, la existencia o no de un job de reatribucion y la posibilidad de doble conteo al reprocesar webhooks.
- **Opciones:**
  - Atribucion almacenada mas job de reatribucion
  - Atribucion resuelta en consulta
  - Agregados normalizados por autor y dia
  - Agregados con JSON de autores por dia
- **Estudio de APIs:** §8.3 propone `student_id` nullable en CommitRecord (atribucion almacenada) y RepoActivityDaily con `authors_json`; §8.4 propone fallback por email y nombre, sin abordar la reatribucion.
- **Fusiona:** P467

### Q-2.5-11 — ¿El modelo persiste el grafo de commits (parent_shas) y una tabla de ramas, o solo commits planos?

Con `parent_shas` y una tabla de ramas (RepoBranch: nombre, head_sha, visto_por_ultima_vez) o `commit_branches` se puede: (a) detectar merges sin llamar a la API, (b) recalcular alcanzabilidad tras un force-push o el borrado de una rama y marcar commits huerfanos, (c) filtrar el timeline por rama y (d) verificar que el SHA de cada snapshot de entrega sigue alcanzable. La alternativa es guardar solo commits planos (sha, fechas, autor) y aceptar no poder responder esas preguntas.

- **Requisitos:** R2.5.2, R2.5.3, R2.5.10, R2.4.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Decide si el modelo soporta las reglas elegidas para merges, force-push y ramas; agregar el grafo despues obliga a reingerir todo el historial de los 60 repositorios.
- **Opciones:**
  - Persistir parents mas tabla de ramas
  - Persistir solo parents
  - Commits planos sin grafo
- **Estudio de APIs:** §8.3 define CommitRecord sin parents ni ramas; §8.4 menciona detectar merges por `parents.length > 1` en el payload del webhook, sin persistirlo.
- **Fusiona:** P465

### Q-2.5-12 — ¿El timeline se sirve desde una tabla unificada de eventos o se compone en consulta uniendo las tablas de origen?

Alternativa A: una tabla TimelineEvent (repository_id, kind, occurred_at, payload_json, referencia a la entidad origen) que cada worker alimenta. Alternativa B: componer en consulta uniendo commits, snapshots de entrega, cambios de membresia, invitaciones, comunicaciones enviadas y cambios de fecha. Si es tabla: como se evita la divergencia con las tablas origen ante reprocesos, recapturas y borrados logicos, y como se garantiza idempotencia por `(kind, source_id)`. En ambos casos: si los gaps de inactividad se calculan al vuelo o se materializan como eventos.

- **Requisitos:** R2.5.6, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cambia el diseno de todos los workers (deben o no emitir eventos) y el rendimiento de la vista con cientos de commits.
- **Opciones:**
  - Tabla unificada de eventos
  - Union en consulta
  - Tabla solo para eventos no-commit, con los commits aparte
- **Estudio de APIs:** §8.6 describe el timeline como "alimentado 100% desde su BD" sin definir su modelo de datos.
- **Fusiona:** P468

### Q-2.5-13 — ¿Las alertas son entidades con ciclo de vida y se pueden silenciar o justificar, o se recalculan sin estado en cada render e informe?

Las alertas en juego son: repositorio inactivo, estudiante sin participacion, invitacion sin aceptar, repositorio en error y grupo desbalanceado. Hay que decidir si se modelan como entidad con ciclo de vida (kind, target, first_detected_at, last_detected_at, resolved_at, silenced_until, silenced_by) que un job evaluador abre y cierra, o si se recalculan como consulta en cada render y en cada informe sin estado. Si son entidad: si el informe diario puede distinguir "nuevo hoy" de "persiste desde hace N dias" y enlazar cada informe a las alertas exactas que incluyo (ReportItem). Ligado a esto: si el docente puede marcar una alerta como "vista" o "justificada" (por ejemplo, el grupo aviso que trabajara la ultima semana) para silenciarla en el dashboard y en el informe diario durante un plazo, y si se registra quien la silencio y cuando.

- **Requisitos:** R2.5.3, R2.5.4, R2.6.1, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si existe historial de alertas, si el informe es reproducible y si el docente puede evitar que el informe repita dia a dia situaciones ya gestionadas; una alerta sin estado no puede decir desde cuando persiste.
- **Opciones:**
  - Entidad Alert con ciclo de vida completo (incluye silenciamiento y justificacion)
  - Consulta sin estado, sin silenciamiento
  - Hibrido: consulta sin estado mas tabla de silenciados o reconocidos
- **Estudio de APIs:** §8.5 y §9.1 describen las reglas de alerta como consultas; no proponen entidad, ciclo de vida ni mecanismo de silenciamiento o reconocimiento.
- **Fusiona:** P469, P434

## Definiciones operativas de actividad y de tiempo

### Q-2.5-14 — ¿Que cuenta como "actividad" de un repositorio y que marca temporal define la fecha de un commit?

Primera parte: si "actividad" son solo commits, o tambien creacion de ramas y tags, pull requests, issues, comentarios y releases; y si "ultima actividad" es la fecha del ultimo commit o la del ultimo push (un push puede traer commits con fechas antiguas). Segunda parte: que marca temporal fecha un commit para las series, los periodos y el "ultimo commit": `author.date` (manipulable pero sobrevive a un rebase), `committer.date` (cambia con rebase o amend) o la fecha de recepcion del push (unica no falsificable). Tercera parte: como se tratan los commits con fecha futura, anterior a la creacion del repositorio (historial importado de otro proyecto) o con reloj desajustado: se aceptan tal cual, se recortan al rango del repositorio o se marcan como anomalos.

- **Requisitos:** R2.5.2, R2.5.3, R2.5.7, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define que webhooks y tablas se necesitan (los PRs e issues exigen eventos y modelos adicionales), la semantica de `last_commit_at` que usan R2.5.3 y el informe diario, a que periodo de entrega se asigna cada commit, la captura de version por fecha (R2.4.5 usa `until=`) y la posibilidad de que un estudiante retrodate trabajo para caer dentro del plazo.
- **Opciones:**
  - Solo commits
  - Commits mas eventos de push (fecha de recepcion)
  - Commits mas ramas y tags
  - Commits mas pull requests e issues
  - Fecha del commit = author.date
  - Fecha del commit = committer.date
  - Fecha del commit = fecha de recepcion del push (webhook)
  - Fecha del commit = committer.date con marca de anomalia si difiere mucho de la recepcion
- **Estudio de APIs:** §8.1 propone suscribirse a push, create, delete, repository, member y member_invite, pero §8.3 solo modela commits y no aborda PRs ni issues; §8.3 guarda `authored_at` y `committed_at` sin decidir cual se usa, y §7.5 usa `until=` sobre la fecha de committer de GitHub.
- **Fusiona:** P406, P409

### Q-2.5-15 — ¿Se monitorean los commits de todas las ramas o solo los de la rama por defecto?

`repository.default_branch` puede no ser `main`. Si se monitorean todas las ramas: si un commit presente en varias ramas se cuenta una sola vez por SHA y como se etiqueta en el timeline. Si solo la rama por defecto: si un estudiante que trabaja dos semanas en una rama `dev` aparece como "sin actividad". Y en cualquier caso: que ocurre si el estudiante cambia la rama por defecto del repositorio.

- **Requisitos:** R2.5.2, R2.5.4, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cambia el filtro del webhook `push` (por `ref`), la consulta de reconciliacion (`sha=`) y la definicion de participacion; afecta directamente a los falsos positivos de R2.5.3 y R2.5.4.
- **Opciones:**
  - Solo rama por defecto
  - Todas las ramas, conteo unico por SHA
  - Todas las ramas con etiqueta de rama en el timeline
- **Estudio de APIs:** §8.1 sugiere "filtrar rama por defecto si quieren"; §14 advierte no asumir `main` y leer `default_branch`.
- **Fusiona:** P407

### Q-2.5-16 — ¿Que commits se excluyen de las metricas de participacion y se muestran igualmente en el timeline?

Candidatos a exclusion: merge commits (mas de un padre), el commit inicial de `auto_init` o heredado de la plantilla, los commits del bot de la propia aplicacion (subida de archivos base), bots externos (`github-actions[bot]`, `dependabot`) y commits de profesores o ayudantes en repositorios de estudiantes. Hay que decidir si se mantiene una lista por curso de logins y emails "del equipo docente y bots" a excluir, quien la administra, y si esos commits se muestran igual en el timeline aunque no cuenten en las metricas.

- **Requisitos:** R2.5.2, R2.5.4, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita que un repositorio recien creado aparezca "con actividad" por el commit de la plantilla y que un arreglo del profesor cuente como participacion del estudiante; define una tabla de exclusiones y una regla de negocio.
- **Opciones:**
  - Sin exclusiones: todos los commits cuentan
  - Excluir solo merges y el commit inicial de plantilla
  - Excluir ademas bots (propios y externos) mediante lista configurable
  - Excluir ademas commits del equipo docente mediante lista por curso
  - Excluidos de las metricas pero visibles en el timeline / ocultos tambien en el timeline
- **Estudio de APIs:** §8.4 propone marcar los merges (`parents.length > 1`) y permitir excluirlos; §5.3 usa un committer "ICC4201 Bot"; no aborda los commits del profesor ni los bots externos.
- **Fusiona:** P408

### Q-2.5-17 — ¿Se registran lineas anadidas y eliminadas y archivos cambiados por commit?

El payload del webhook `push` trae listas de archivos (`added`/`modified`/`removed`) pero no conteo de lineas, y `GET /repos/{o}/{r}/commits` tampoco: obtener lineas exige una llamada `GET /repos/{o}/{r}/commits/{sha}` por commit (1 punto de rate limit cada una). Si se registran: si se filtran archivos generados o binarios (lock files, `node_modules`, imagenes) y con que lista de patrones. Si no se registran: si el timeline muestra el tamano del commit de otra forma (numero de archivos).

- **Requisitos:** R2.5.2, R2.5.8, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina el costo de la ingesta (60 repositorios por cientos de commits), el contenido de CommitRecord y que metricas son posibles para R2.5.8 y R2.5.10.
- **Opciones:**
  - No registrar lineas; usar el numero de archivos del payload
  - Registrar lineas con una llamada por commit y filtros de archivos generados
  - Registrar lineas solo via los endpoints `stats/` agregados por semana
- **Estudio de APIs:** §8.3 marca `additions`/`deletions`/`changed_files` como opcionales; §8.5 advierte que el conteo de lineas es una mala metrica de contribucion; no cuantifica el costo de obtenerlas.
- **Fusiona:** P410

### Q-2.5-18 — ¿Cual es la granularidad temporal de la serie de actividad y en que zona horaria se cortan los dias?

Granularidad: dia, semana, o ambas con selector. Zona horaria: America/Santiago fija, zona configurable por curso, o zona del navegador del usuario. Debe considerarse que Chile cambia a horario de verano en septiembre de 2026, dentro del periodo del proyecto, y que Canvas y GitHub entregan todo en UTC.

- **Requisitos:** R2.5.2, R2.5.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina la clave de agregacion de RepoActivityDaily y como se interpretan "ultimo dia", "ultimas 24 h" y los limites de los periodos de entrega; un corte en UTC desplaza los commits nocturnos chilenos al dia siguiente.
- **Opciones:**
  - Dia en America/Santiago fija
  - Dia en zona configurable por curso
  - Semana ISO
  - Dia mas semana con selector
- **Estudio de APIs:** §8.3 agrega por dia (`RepoActivityDaily.day`) sin fijar zona horaria; §14 recomienda guardar en UTC (`timestamptz`) y convertir solo al renderizar.
- **Fusiona:** P403

### Q-2.5-19 — ¿Cual es la definicion completa de "repositorio sin actividad reciente": umbral numerico, nivel de configuracion y punto de referencia?

Primera parte: N dias sin commits, con N fijo global (3, 5, 7...), configurable por curso, por tarea o por entrega; valor por defecto; y quien puede cambiarlo (que permiso). Si la misma N alimenta el informe diario (R2.6.2) y los marcadores de gap del timeline, o si cada uno tiene su propio umbral. Segunda parte: si "reciente" se mide respecto a "ahora" o respecto a la proxima fecha de cierre efectiva del repositorio (por ejemplo, alertar si faltan menos de 48 h y no hay commits en 3 dias). Tercera parte: si un repositorio que nunca ha tenido commits entra en "sin actividad reciente" o es una categoria propia ("sin iniciar"), y si un repositorio creado hace menos de N dias queda excluido de la alerta.

- **Requisitos:** R2.5.3, R2.5.10, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin un numero no hay criterio de aceptacion para R2.5.3; la coherencia entre dashboard, informe y timeline evita que la misma situacion se reporte distinto en cada lugar, y la distincion de estados evita falsas alertas en repositorios recien creados.
- **Opciones:**
  - N fijo global
  - N configurable por curso
  - N configurable por tarea
  - N configurable por entrega
  - "Reciente" medido contra ahora
  - "Reciente" medido contra la proxima fecha de cierre efectiva
  - Estados separados: sin iniciar / inactivo / activo
- **Estudio de APIs:** §8.5 propone `last_commit_at < now() - X dias` con "X configurable", sin valor ni nivel de configuracion; §9.1 usa "N dias" en el informe; §8.6 dibuja gaps sin fijar umbral; §9.4 menciona la notificacion "faltan 24 h y el repo no tiene commits", sin resolver el punto de referencia.
- **Fusiona:** P411, P412

### Q-2.5-20 — ¿Cuando deja de evaluarse la alerta de inactividad de un repositorio y cual es la definicion exacta de "tarea activa"?

Alternativas para el fin de la evaluacion: al pasar la ultima fecha efectiva de cierre del repositorio (que varia por overrides), al pasar `lock_at`, al cerrar la tarea manualmente, o nunca. Ligado a esto: cual es la definicion exacta de "tarea activa" que usan el dashboard y el informe diario, y si es automatica por fechas o un estado manual (abierta / cerrada / archivada) controlado por el profesor.

- **Requisitos:** R2.5.3, R2.5.6, R2.6.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita alertar por repositorios de tareas ya terminadas, define el ciclo de vida de una tarea y da contenido a la condicion "si no hay tareas activas entonces no hay informe" de R2.6.1.
- **Opciones:**
  - Automatico por fecha efectiva de cierre por repositorio
  - Automatico por `lock_at`
  - Estado manual de la tarea
  - Automatico con posibilidad de cierre o archivado manual
- **Estudio de APIs:** §9.1 habla de "tareas con alguna entrega cuyo periodo este vigente", sin definir "vigente" ni como interactua con los overrides o con un estado manual.
- **Fusiona:** P413

### Q-2.5-21 — ¿Cada indicador expone su definicion operativa dentro de la propia interfaz, o las definiciones viven solo en el spec?

Para cada indicador del dashboard, del timeline y del informe diario habria que exponer: que cuenta y que excluye (merges, commit inicial de plantilla, commits del bot y del equipo docente, commits no atribuidos), la ventana temporal considerada, la rama o ramas incluidas, la hora de corte del dia y la zona horaria, y la fuente y el momento de la ultima ingesta. El vehiculo puede ser un tooltip, un panel "como se calcula" o una pagina de definiciones enlazada. Ademas: si se muestra junto al dato el valor vigente de los umbrales configurables (por ejemplo "sin actividad reciente = 5 dias") y quien los cambio por ultima vez.

- **Requisitos:** R2.5.2, R2.5.3, R2.5.4, R2.5.8, R2.5.9, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es la primera pregunta que hara el examinador el 7-oct ("¿que significa exactamente ese numero?") y determina si un docente puede usar la metrica para una decision academica sin malinterpretarla; exponerla obliga a cerrar en el spec cada definicion operativa antes de implementar y crea un componente de UI reutilizable.
- **Opciones:**
  - Tooltip por indicador con su definicion operativa
  - Panel "como se calcula" desplegable por seccion
  - Pagina unica de definiciones enlazada desde cada indicador
  - Definiciones solo en el spec, sin exposicion en la UI
  - Mostrar tambien el valor vigente de los umbrales y su ultimo cambio / no mostrarlo
- **Estudio de APIs:** §8.5 advierte sobre la baja calidad de las lineas como metrica y recomienda presentar los indicadores como senal y no como veredicto, pero no propone exponer la definicion de cada metrica en la interfaz.
- **Fusiona:** N012

## Atribucion de commits y definicion de participacion

### Q-2.5-22 — ¿Cual es la regla de atribucion de un commit a un estudiante y su orden de precedencia?

Precedencia candidata: 1) login (`author.username` del webhook o `author.login` de REST), 2) email del autor igual a un email conocido, 3) nombre normalizado. Hay que definir que emails se consideran conocidos: el noreply de GitHub (`ID+login@users.noreply.github.com`, parseable), el email publico del perfil (`GET /users/{login}` solo lo trae si es publico), el email de Canvas (cuya obtencion via API no esta garantizada) o emails agregados a mano por el docente. Y si el match por nombre se aplica automaticamente (con riesgo de homonimos) o solo se sugiere para confirmacion manual.

- **Requisitos:** R2.5.4, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el algoritmo de resolucion de `student_id` en CommitRecord y cuantos commits quedan "sin atribuir"; de esto depende no acusar injustamente a un estudiante de no participar.
- **Opciones:**
  - Solo login
  - Login mas email conocido
  - Login mas email mas nombre normalizado automatico
  - Login mas email; nombre solo como sugerencia para confirmacion manual
- **Estudio de APIs:** §8.4 propone fallback por email conocido (de Canvas) y por nombre normalizado; el Apendice A.3 advierte que `include[]=email` en Canvas no esta documentado y sugiere `/users/:id/profile`.
- **Fusiona:** P417

### Q-2.5-23 — ¿Que traen realmente el payload `push` y `GET /repos/{o}/{r}/commits` en los casos limite de atribucion, verificado empiricamente?

Casos a verificar: cuando el email del autor no esta asociado a ninguna cuenta de GitHub (¿`author.username` ausente? ¿`author` null en REST?), cuando el commit se hace desde la web de GitHub, cuando se usa el email noreply de GitHub, cuando hay trailer `Co-authored-by`, y cuando `author` y `committer` diferen (rebase hecho por otro integrante). Los resultados fijan la regla de atribucion que se escribe en el spec.

- **Requisitos:** R2.5.4, R2.5.8
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** La regla de atribucion de R2.5.4 solo puede escribirse con precision conociendo los campos reales que llegan en cada caso; escribirla a ciegas produce falsos "sin participacion".
- **Opciones:**
  - Verificar los cinco casos y documentar los campos observados antes de fijar la regla
  - Fijar la regla por documentacion y ajustarla si falla en pruebas
- **Estudio de APIs:** §8.4 describe los casos (author null, ediciones web, co-autores, merges) sin aportar evidencia empirica.
- **Fusiona:** P458

### Q-2.5-24 — ¿La atribucion por login guarda el login textual o el id numerico de GitHub?

Un estudiante puede renombrar su cuenta: el login del payload cambia y un mapeo textual deja de coincidir. El payload `push` solo trae `commits[].author.username` (sin id). Hay que decidir si se resuelve el id con `GET /users/{login}` en el momento del mapeo, y si se re-resuelve el login periodicamente o solo ante un fallo de atribucion.

- **Requisitos:** R2.2.4, R2.5.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Determina la clave del mapeo estudiante-GitHub que usa todo el monitoreo y su robustez ante renombres de cuenta; es una decision de modelo de datos que condiciona la entrega parcial.
- **Opciones:**
  - Guardar solo el login textual
  - Guardar el id numerico como clave y el login como dato mostrado
  - Guardar ambos y re-resolver el login periodicamente
  - Guardar ambos y re-resolver solo ante fallo de atribucion
- **Estudio de APIs:** no lo aborda; §6.1 guarda el login canonico devuelto por `GET /users/{username}` sin mencionar el id numerico.
- **Fusiona:** P419

### Q-2.5-25 — ¿Los trailers `Co-authored-by` cuentan como participacion del co-autor y con que peso?

Aplica a R2.5.4 y R2.5.8. Si cuentan: si el commit suma 1 completo para cada autor o se reparte el credito (0,5 / 0,5). Ademas: si se valida que el co-autor sea integrante del repositorio y como se muestra la co-autoria en el timeline.

- **Requisitos:** R2.5.4, R2.5.8, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cambia el modelo de datos (N autores por commit), las sumas de la comparacion de integrantes del grupo y obliga a un parser de mensajes de commit.
- **Opciones:**
  - No se consideran
  - Cuentan 1 completo para cada autor
  - Se reparte el credito entre los autores
  - Se muestran en el timeline pero no cuentan en las metricas
- **Estudio de APIs:** §8.4 sugiere "parsear el trailer del mensaje si quieren credito compartido", sin decidir el peso ni la validacion.
- **Fusiona:** P420

### Q-2.5-26 — ¿Se usa `verification.verified` de GitHub como senal de confianza en la atribucion, y las instrucciones enviadas por Canvas piden configurar el email o firmar los commits?

GitHub expone por commit `verification.verified` (firma GPG/SSH valida, o commit hecho desde la web). Hay que decidir si se usa para distinguir "atribuido por login verificado" de "atribuido por email no verificable" y si se muestra al docente en el dashboard y en el timeline, o si se ignora. Ademas: si las instrucciones enviadas al estudiante por Canvas (R2.3.12) recomiendan configurar el email noreply de GitHub o firmar los commits para que la atribucion funcione.

- **Requisitos:** R2.3.12, R2.5.4, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Decide un campo mas en CommitRecord, un indicador en la UI y el texto de las instrucciones iniciales al estudiante, que es lo unico que la aplicacion puede hacer para mejorar la calidad de la atribucion antes de que empiece el trabajo.
- **Opciones:**
  - Ignorar la firma
  - Mostrar un indicador de verificacion sin afectar los conteos
  - Ponderar solo los commits verificados en las alertas de "sin participacion"
  - Incluir en las instrucciones de Canvas la configuracion de email o firma / no incluirla
- **Estudio de APIs:** §8.4 propone atribucion por login, email y nombre; no menciona la verificacion de firma de commits ni el contenido de las instrucciones al estudiante.
- **Fusiona:** P399

### Q-2.5-27 — ¿Cual es la definicion operativa de "estudiante que aun no ha participado", y cuenta la actividad que no son commits?

Primera parte, sobre commits: (a) 0 commits atribuidos como autor en toda la tarea; (b) 0 commits como autor, committer o co-autor; (c) ademas, no haber aceptado la invitacion al repositorio; (d) 0 commits dentro del periodo de la entrega vigente y no en toda la tarea. Y si se distinguen en la UI los sub-estados "sin mapeo GitHub", "invitacion no aceptada" y "con acceso y 0 commits".

Segunda parte, sobre actividad no-commit: un integrante puede trabajar sin aparecer nunca como autor de un commit (abriendo pull requests, revisando y aprobando los PR de sus companeros, comentando, abriendo o cerrando issues, o haciendo merges). Alternativas: (a) no se cuenta, y la limitacion se declara explicitamente en la UI y en el informe para no acusar injustamente ("esta metrica solo mide commits"); (b) si se cuenta, y entonces hay que decidir a que eventos de webhook se suscribe la GitHub App (`pull_request`, `pull_request_review`, `pull_request_review_comment`, `issues`, `issue_comment`), que tablas y agregados se agregan, como se pondera frente a los commits en la comparacion de integrantes y si esos eventos aparecen en el timeline (R2.5.10); (c) se registra y muestra como informacion complementaria pero no altera la alerta de "sin participacion". Si se opta por contarla, ¿se verificara que entregan esos eventos para repositorios privados de la instalacion y cuanto cuestan en volumen antes de comprometerlo?

- **Requisitos:** R2.5.2, R2.5.4, R2.5.8, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es la regla de negocio central de R2.5.4 y de la situacion "estudiantes sin participacion" del informe diario (R2.6.2), y de la comparacion de integrantes que el corrector usa para ajustar notas individuales (R2.7.6); cada opcion cambia la consulta, el texto mostrado y el alcance de la ingesta (eventos, tablas, retencion). Es exactamente el tipo de criterio que se pregunta en la actividad de validacion individual del 7-oct.
- **Opciones:**
  - 0 commits como autor en toda la tarea
  - 0 commits como autor, committer o co-autor
  - Incluye "invitacion no aceptada" como no participacion
  - 0 commits en el periodo de la entrega vigente
  - Solo commits, con declaracion explicita de la limitacion en UI e informe
  - Commits mas actividad no-commit ingerida y ponderada en las metricas
  - Commits para la alerta; actividad no-commit solo como contexto visible (timeline o ficha), sin afectar alertas
- **Estudio de APIs:** §8.5 define "estudiantes sin participacion = integrantes con 0 commits atribuidos"; §5.4 distingue 201 (invitacion pendiente) de 204 (acceso directo) pero no cruza ambos conceptos. El estudio modela la participacion exclusivamente a partir de commits (§8.3 CommitRecord/RepoActivityDaily/RepoStatus, §8.4 atribucion de commits) y solo sugiere suscribirse a push, create, delete, repository, member y member_invite (§8.1); su advertencia metodologica (§8.5) discute lineas frente a commits, pero no la actividad no-commit.
- **Fusiona:** P416, N005

### Q-2.5-28 — Si un repositorio grupal tiene commits sin atribuir, ¿se sigue marcando a un integrante con 0 commits como "sin participacion"?

Alternativa: degradar el estado a "participacion no verificable" hasta resolver la atribucion. Ademas: si aparece una fila "Desconocido" en la comparacion de integrantes con el conteo de commits no atribuidos, y con que severidad y texto se emite la alerta correspondiente en el informe diario.

- **Requisitos:** R2.5.4, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el texto y la severidad de la alerta ante datos sucios y evita conclusiones injustas en el informe diario.
- **Opciones:**
  - Se mantiene "sin participacion" con nota al pie
  - Se degrada a "participacion no verificable" mientras haya commits sin atribuir
  - Se suprime la alerta hasta resolver la atribucion
  - Fila "Desconocido" visible en la comparacion / no visible
- **Estudio de APIs:** §8.4 propone mostrar "N commits sin atribuir" para no acusar injustamente (R2.5.4); no define el efecto sobre la alerta.
- **Fusiona:** P421

### Q-2.5-29 — ¿Puede el docente asociar manualmente un email a un estudiante, y esa correccion se aplica retroactivamente y en que alcance?

Cuando el dashboard muestre "N commits sin atribuir" con sus emails y nombres, hay que decidir si el docente puede asociarlos manualmente desde la UI y como es ese flujo. Si lo hace: si se reatribuyen retroactivamente todos los commits historicos con ese email (recalculando agregados y alertas), y si la asociacion aplica a todos los repositorios del curso o solo a ese repositorio. Y el mismo comportamiento si cambia el mapeo Canvas-GitHub de un estudiante (nuevo login): si los commits del login antiguo se conservan atribuidos.

- **Requisitos:** R2.5.4, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define una tabla de alias por estudiante, la necesidad de recomputar agregados y alertas, y el flujo de UI de correccion de atribucion.
- **Opciones:**
  - Sin correccion manual: la atribucion es solo automatica
  - Correccion manual con efecto solo hacia adelante
  - Correccion manual con reatribucion retroactiva a nivel de repositorio
  - Correccion manual con reatribucion retroactiva a nivel de curso
- **Estudio de APIs:** §8.4 sugiere que el docente pueda mapear a mano los emails desconocidos; no aborda la retroactividad ni el alcance de la correccion.
- **Fusiona:** P418

### Q-2.5-30 — ¿Como se distingue en el dashboard al estudiante "mapeado pero sin acceso" del "con acceso y sin commits", y como se detecta la aceptacion de la invitacion?

En una tarea individual hay que distinguir al estudiante con invitacion de colaborador no aceptada (respuesta 201 al invitar) del que ya tiene acceso y no ha hecho commits (204 o invitacion aceptada). Ademas hay que decidir si la aceptacion de la invitacion se detecta por el webhook `member`, por polling de `GET /repos/{o}/{r}/invitations`, o por ambos, y con que frecuencia.

- **Requisitos:** R2.5.4, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define la transicion COLLABORATORS_PENDING a READY, que alimenta tanto R2.5.5 (estado de creacion y configuracion, exigible en la parcial junto con R2.3.11) como la interpretacion de "no ha participado".
- **Opciones:**
  - Deteccion solo por webhook `member`
  - Deteccion solo por polling de invitaciones
  - Ambos, con el webhook como via principal y el polling como respaldo
  - Sub-estados visibles en la UI: sin mapeo / invitado sin aceptar / con acceso sin commits / con commits
- **Estudio de APIs:** §5.4 describe las respuestas 201 y 204 y el endpoint `GET /repos/{o}/{r}/invitations`; §8.1 lista el evento `member` "segun disponibilidad", sin verificar su semantica ni fijar frecuencia de polling.
- **Fusiona:** P460

### Q-2.5-31 — ¿La aplicacion detecta y marca los commits vacios y las rafagas triviales, y como se encuadran las metricas ante el riesgo de inflado?

Los conteos de commits y de dias activos se pueden inflar (commits vacios con `--allow-empty`, rafagas de commits triviales, commits que solo tocan espacios en blanco). Hay que decidir si la aplicacion detecta y marca los commits sin cambios (0 archivos) o las rafagas anomalas (N commits en menos de 1 minuto) para excluirlos o senalarlos en el dashboard, en la comparacion de integrantes y en el timeline. Ademas: si las metricas se presentan explicitamente como "senal para revisar, no veredicto" en la UI y en el informe, y que respuesta prepara el equipo para el examinador del 7-oct ante la pregunta "¿como evitan que un estudiante infle su participacion?".

- **Requisitos:** R2.5.4, R2.5.8, R2.5.9, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina que se cuenta, como se etiqueta en la UI y la defensa metodologica de R2.5.4 y R2.5.8 ante el profesor.
- **Opciones:**
  - Marcar o excluir commits sin cambios y rafagas anomalas
  - Mostrar el tamano (numero de archivos) por commit como contexto
  - Solo texto "senal, no veredicto" sin deteccion automatica
  - No tratar el caso
- **Estudio de APIs:** §8.5 advierte contra el uso de lineas de codigo y propone commits y dias activos; §8.4 trata merges y co-autores; no aborda los commits vacios ni el inflado deliberado.
- **Fusiona:** P461

### Q-2.5-32 — ¿Se permite que un estudiante o grupo desarrolle fuera del repositorio asignado y suba todo en uno o pocos pushes al final?

Al usar `until` sobre la fecha del commit, esa historia importada entra integra en el snapshot y la entrega es formalmente valida, pero el seguimiento en el tiempo (R2.5.2), la deteccion de inactividad (R2.5.3) y el timeline (R2.5.10) quedan vacios hasta el ultimo dia. Hay que decidir: (a) si se acepta sin mas; (b) si se prohibe explicitamente en el reglamento comunicado por Canvas (R2.3.12), con que consecuencia y definida por quien (el equipo o el profesor del curso); (c) si se acepta pero se marca en el dashboard y en el timeline como "historia importada" usando las senales disponibles (muchos commits recibidos en un solo push, fechas de commit muy anteriores a la recepcion, autores desconocidos en el repositorio) y no cuenta como actividad distribuida; (d) que se le dice al estudiante al inicio para que sepa que se evalua el ritmo y no solo el resultado.

- **Requisitos:** R2.3.12, R2.4.5, R2.5.2, R2.5.3, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin esta regla las metricas de 2.5 pueden ser irrelevantes precisamente para los grupos mas organizados, y el equipo no tendra respuesta el 7-oct a "¿que pasa si trabajan en otro repositorio y suben todo al final?"; ademas decide si se persiste la fecha de recepcion del push, lo que condiciona el modelo de datos.
- **Opciones:**
  - Se acepta y no se distingue
  - Se prohibe en el reglamento y se marca como incumplimiento
  - Se acepta y se etiqueta como historia importada, excluida de la serie temporal
  - Se acepta pero el docente recibe una alerta especifica en el informe
- **Estudio de APIs:** §8.2 y §8.5 asumen que toda la actividad ocurre en el repositorio creado por la app y §7.5 captura por fecha de commit, de modo que una importacion previa al cierre entra completa; §14 menciona el riesgo de fechas manipuladas pero no fija ninguna regla sobre donde debe desarrollarse el trabajo.
- **Fusiona:** N021

## Contenido, rendimiento y usabilidad del dashboard

### Q-2.5-33 — ¿Cual es el contenido exacto y cerrado del dashboard de una tarea?

Hay que fijar: la lista de KPIs (por ejemplo repositorios totales / listos / con problema, repositorios con actividad en los ultimos N dias, repositorios sin actividad reciente, estudiantes sin participacion, commits en las ultimas 24 h y en 7 dias, proxima entrega con cuenta regresiva); la tabla o tablas con una fila por repositorio y sus columnas (integrantes, seccion, estado, ultimo commit, commits en el periodo, integrantes sin commits, enlace a GitHub y al timeline); los graficos incluidos; y el orden de las secciones.

- **Requisitos:** R2.5.1, R2.5.2, R2.5.3, R2.5.4, R2.5.5, R2.5.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define que agregados se precomputan, el modelo de datos de RepoStatus y RepoActivityDaily y los criterios de aceptacion de R2.5.1; sin una lista cerrada no se puede escribir el spec de la vista ni probarla.
- **Opciones:**
  - Tarjetas KPI mas tabla por repositorio mas un grafico de serie temporal
  - Tarjetas KPI mas tabla mas grafico mas panel de alertas separado (R2.5.3 y R2.5.4)
  - Dashboard por pestanas: Resumen / Repositorios / Entregas / Participacion
- **Estudio de APIs:** §8.3 propone las tablas RepoActivityDaily y RepoStatus; §8.5 mapea cada requisito a una metrica; no fija KPIs, columnas ni layout.
- **Fusiona:** P401

### Q-2.5-34 — ¿El dashboard es la pantalla que se abre por defecto al entrar a una tarea, y cuales son los numeros objetivo de rendimiento y escala?

Primera parte: si el dashboard es la pantalla por defecto (el enunciado dice "disponible de forma inmediata al ingresar a la vista de una tarea") o una pestana mas. Segunda parte: cual es el criterio de aceptacion medible de "inmediato" (por ejemplo respuesta del servidor p95 menor a 1 s con 60 repositorios y 5.000 commits, y cero llamadas a GitHub o Canvas dentro del request de render). Tercera parte: los numeros objetivo de escala y tiempo: maximo de tareas activas por curso, repositorios por tarea (60, 200), commits por repositorio, dashboard en menos de 1 s, timeline con 2.000 commits en menos de 2 s. Cuarta parte: si la tabla de 60 o mas repositorios se pagina, se virtualiza o se muestra completa.

- **Requisitos:** R2.5.1, R2.5.2, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Convierte la restriccion del enunciado ("sin requerir esperar a que se recopile en ese momento") en un requisito no funcional verificable, fija la navegacion de la tarea y da las cifras necesarias para disenar indices, agregados y pruebas de carga.
- **Opciones:**
  - Dashboard como pantalla por defecto / como una pestana mas
  - Criterio p95 con cifras declaradas y prueba de carga asociada
  - Criterio cualitativo sin cifras
  - Tabla paginada / virtualizada / completa
- **Estudio de APIs:** §8 (intro) afirma que "la vista lee de su base de datos, nunca de la API de GitHub" y §12 que todas las vistas leen de Postgres, sin fijar umbral numerico ni navegacion; §2.1 y §2.4 usan 60 estudiantes y 60 repositorios como escenario de rate limit, sin fijar criterios de aceptacion de la UI.
- **Fusiona:** P402, P456

### Q-2.5-35 — ¿Que artefacto observable se construye para que el profesor o ayudante pueda comprobar durante la revision que la vista de la tarea no recopila la actividad en ese momento?

Opciones: una linea en la UI del tipo "renderizado en X ms · 0 llamadas a GitHub/Canvas · datos ingeridos hace N min"; un panel de diagnostico con el contador de llamadas externas por request y su detalle; un "modo demostracion" que corta la salida de red hacia GitHub y muestra que el dashboard sigue cargando igual; una pagina de metricas de ingesta con la hora del ultimo webhook y de la ultima reconciliacion; o nada, confiando en que el revisor perciba la velocidad. Ademas: quien puede ver ese artefacto (todos los roles o solo el profesor) y si queda visible en produccion durante las dos semanas de revision.

- **Requisitos:** R2.5.1, R2.5.2, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El requisito 2.5 es no funcional e invisible: un dashboard rapido con datos en vivo y uno lento con datos precomputados se ven igual. Definir el artefacto obliga a instrumentar el request (contador de llamadas externas), fija un componente de UI y convierte el requisito en algo demostrable y defendible el 7-oct.
- **Opciones:**
  - Linea de UI con tiempo de render, llamadas externas y antiguedad de los datos
  - Panel de diagnostico con contador y detalle de llamadas externas por request
  - Modo demostracion que corta la salida de red hacia GitHub
  - Pagina de metricas de ingesta (ultimo webhook, ultima reconciliacion)
  - Ningun artefacto
- **Estudio de APIs:** §8 exige precomputar y advierte que llamar a GitHub en el render viola el enunciado, pero no propone ninguna forma de evidenciarlo ante el revisor.
- **Fusiona:** N009

### Q-2.5-36 — ¿Como se representa "la actividad de los distintos repositorios a lo largo del tiempo" cuando hay 60 o mas repositorios?

Una linea por repositorio es ilegible a esa escala. Alternativas: serie agregada de la tarea con posibilidad de aislar repositorios seleccionados; heatmap de repositorios por dias; sparkline en cada fila de la tabla; barras apiladas por seccion.

- **Requisitos:** R2.5.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija el tipo de grafico, los datos que la API interna debe entregar y el criterio de aceptacion de legibilidad para R2.5.2.
- **Opciones:**
  - Serie agregada mas seleccion de repositorios
  - Heatmap repositorios por dias
  - Sparklines por fila
  - Combinacion de las anteriores
- **Estudio de APIs:** §8.5 menciona una "serie diaria de commits por repo"; no aborda la visualizacion con muchos repositorios.
- **Fusiona:** P404

### Q-2.5-37 — ¿Cual es el rango temporal por defecto del grafico y de los KPIs "recientes"?

Inicio candidato: creacion del primer repositorio de la tarea, `unlock_at` o creacion de la primera entrega en Canvas, creacion de la tarea en la aplicacion, o primer commit. Fin candidato: hoy, o la ultima fecha efectiva de cierre si la tarea ya termino. Y ademas: si se usa una ventana movil (ultimos 14 o 30 dias) o el rango completo con zoom.

- **Requisitos:** R2.5.2, R2.5.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina que datos se cargan por defecto, el comportamiento del dashboard tras el cierre de la tarea y que se ve en una tarea recien creada.
- **Opciones:**
  - Rango completo desde la creacion del primer repositorio hasta hoy
  - Rango completo desde `unlock_at` o la creacion de la primera entrega
  - Ventana movil de N dias
  - Rango completo con zoom y seleccion manual
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P405

### Q-2.5-38 — ¿Que filtros, ordenamientos, agrupaciones e interacciones ofrecen el dashboard y sus tablas?

Candidatos: filtrar y agrupar por seccion y por estado del repositorio; ordenar la tabla por "dias desde el ultimo commit", por numero de integrantes sin participacion o por seccion; filtro "solo con alertas"; filtro por periodo de entrega y por autor; tooltips al pasar el mouse; clic en un commit que abre GitHub en una pestana nueva. Ademas: que filtros se recuerdan entre visitas. (El umbral configurable de inactividad se decide en Q-2.5-19 y el flujo de mapeo manual de commits no atribuidos en Q-2.5-29; aqui solo se decide su presencia y comportamiento en la interfaz.)

- **Requisitos:** R2.5.1, R2.5.2, R2.5.3, R2.5.4, R2.5.7, R2.5.8, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la interaccion basica de la tabla principal, su utilidad para cursos con varias secciones y el alcance funcional de las visualizaciones de 2.5.
- **Opciones:**
  - Conjunto minimo: orden por dias desde el ultimo commit y filtro "solo con alertas"
  - Filtros por seccion, estado, periodo y autor, con orden multiple
  - Ademas, persistencia de filtros entre visitas por usuario
  - Sin filtros: tabla estatica
- **Estudio de APIs:** §5.6 propone un filtro "solo problemas" para la tabla de estado y §8.5 sugiere "dias desde el ultimo commit" como columna ordenable; §8.4 recomienda mostrar "N commits sin atribuir" con lista de emails para mapear a mano; §8.6 describe los elementos del timeline.
- **Fusiona:** P455, P464

### Q-2.5-39 — ¿El bloque "estado general de creacion y configuracion" del dashboard (R2.5.5) es el mismo componente que la tabla de estado de repositorios de R2.3.11, y que se muestra en la entrega parcial?

Alternativas: el mismo componente embebido o enlazado desde el dashboard, o un resumen con contadores por estado (listos / invitacion pendiente / falta mapeo / error) con enlace al detalle. Hay que decidir tambien que parte de esto se muestra en la entrega parcial como parte de la vista de tarea.

- **Requisitos:** R2.3.11, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija la reutilizacion de componentes y que se puede demostrar el 16-sep; R2.3.11 forma parte del flujo de la entrega parcial y R2.5.5 lo referencia.
- **Opciones:**
  - Mismo componente reutilizado y embebido en el dashboard
  - Mismo componente enlazado desde el dashboard
  - Resumen con contadores por estado en el dashboard y detalle en la vista de R2.3.11
  - Componentes independientes con datos duplicados
- **Estudio de APIs:** §5.6 propone la tabla de estados de repositorio; §8.5 mapea R2.5.5 a "la maquina de estados de §5.6" sin decir si es la misma vista.
- **Fusiona:** P415

### Q-2.5-40 — ¿Los repositorios que aun no existen en GitHub entran en las metricas de actividad o solo en el bloque de estado de creacion?

Aplica a los repositorios en estado PENDING_MAPPING, QUEUED, CREATING, COLLABORATORS_PENDING o ERROR. Hay que decidir si se incluyen en las metricas de actividad (como 0 commits o "sin iniciar") o solo en el bloque de estado de creacion (R2.5.5), y si el KPI "repositorios sin actividad" cuenta a los que ni siquiera existen en GitHub, es decir, cuales son los denominadores de cada KPI.

- **Requisitos:** R2.5.3, R2.5.4, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita el doble conteo entre "problema de creacion" y "sin actividad" y define los denominadores de los KPIs, sin los cuales los porcentajes del dashboard no son interpretables.
- **Opciones:**
  - Excluidos de las metricas de actividad; solo en el bloque de estado
  - Incluidos como "sin iniciar" en una categoria propia
  - Incluidos como 0 commits sin distincion
- **Estudio de APIs:** §5.2 define la maquina de estados del repositorio; §8.5 no dice como la trata el dashboard de actividad.
- **Fusiona:** P414

### Q-2.5-41 — ¿Que muestran exactamente los estados vacios, y como se distingue "no hay datos aun" de "hubo 0 actividad"?

Estados vacios a definir: tarea sin entregas vinculadas, tarea sin repositorios aun (todos pendientes de mapeo), repositorio creado sin commits de estudiantes (solo el commit inicial de la plantilla), ingesta nunca ejecutada, webhook aun no recibido. Para cada uno: los textos, la llamada a la accion (por ejemplo "ir a mapeo de estudiantes") y si el commit inicial cuenta como "actividad". Por separado, hay que decidir si se muestra un estado explicito del tipo "aun no hemos recopilado actividad de este repositorio; se actualiza cada N min" con la hora de la ultima ingesta por repositorio, y si un estudiante con 0 commits porque su repositorio tiene cinco minutos de vida aparece en "sin participacion".

- **Requisitos:** R2.5.1, R2.5.2, R2.5.3, R2.5.4, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Los estados vacios son lo primero que vera el corrector al crear una tarea: definen textos de UI, evitan graficos rotos y evitan senalar injustamente a estudiantes cuyos datos aun no se han recopilado.
- **Opciones:**
  - Textos especificos por estado vacio con llamada a la accion
  - Un unico estado vacio generico
  - Distincion explicita "sin datos aun" frente a "0 actividad", con hora de ultima ingesta por repositorio
  - Sin distincion: ambos se muestran como 0
- **Estudio de APIs:** §8.2 describe el backfill inicial y la reconciliacion cada 15 min y §8.4 advierte contra acusar por error, pero no define la distincion visual entre "sin datos" y "cero", ni textos de estados vacios.
- **Fusiona:** P451, P463

### Q-2.5-42 — ¿Se muestra un indicador de "ultima actualizacion" y existe un boton "Actualizar ahora"?

Hay que decidir a que corresponde el indicador: al ultimo webhook recibido para la tarea, a la ultima reconciliacion exitosa por repositorio, o a ambos. Sobre el boton: si existe, si dispara la reconciliacion en background sin bloquear el render, con que cooldown (por ejemplo una vez por minuto y por tarea) y restringido a que permisos. Y ademas: que se muestra si la reconciliacion lleva mas de X minutos fallando (por ejemplo un banner "datos posiblemente desactualizados").

- **Requisitos:** R2.5.1, R2.5.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Concreta la usabilidad de la frescura de datos y protege el rate limit; un boton manual es compatible con el enunciado solo si el render por defecto no espera a la API.
- **Opciones:**
  - Indicador de ultima actualizacion sin boton manual
  - Indicador mas boton "Actualizar ahora" con cooldown y permiso asociado
  - Sin indicador ni boton
  - Banner de degradacion cuando la reconciliacion falla de forma sostenida
- **Estudio de APIs:** §4.4 y §7.4 recomiendan mostrar "ultima sincronizacion" y un boton "sincronizar ahora" para Canvas; no lo detallan para la ingesta de GitHub.
- **Fusiona:** P432

### Q-2.5-43 — ¿Se ofrece una vista de seguimiento a nivel de curso ademas del dashboard por tarea?

Es decir, una pantalla con todas las tareas activas y sus alertas consolidadas. El informe diario necesita esa consolidacion de todos modos; hay que decidir si se reutiliza como pagina web del informe o si la vista de curso queda fuera de alcance.

- **Requisitos:** R2.5.1, R2.6.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define una pantalla adicional y el grado de reutilizacion entre el dashboard y el informe diario.
- **Opciones:**
  - Vista de curso propia mas informe diario separado
  - La pagina web del informe diario hace de vista de curso
  - Sin vista de curso: solo dashboard por tarea
- **Estudio de APIs:** §9.1 construye la consolidacion para el informe y sugiere guardarlo como pagina web; no propone una vista de curso.
- **Fusiona:** P446

### Q-2.5-44 — ¿El dashboard y la comparacion de integrantes se pueden exportar o compartir mediante enlace permanente?

Formatos candidatos: CSV, XLSX, PDF. Alternativa o complemento: enlace permanente con los filtros aplicados. O bien la exportacion queda explicitamente fuera de alcance.

- **Requisitos:** R2.5.1, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define alcance y un posible requisito no funcional adicional, ademas de una via de salida de datos personales fuera de la aplicacion.
- **Opciones:**
  - Exportacion a CSV
  - Exportacion a CSV, XLSX y PDF
  - Solo enlace permanente con filtros
  - Fuera de alcance
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P454

## Entregas, periodos y fechas

### Q-2.5-45 — ¿Como se define el periodo de cada entrega para R2.5.7?

Definicion candidata: `(cierre_{k-1}, cierre_k]`. Hay que decidir desde donde parte el periodo de la primera entrega: creacion del repositorio, `unlock_at` de la tarea en Canvas, creacion de la tarea en la aplicacion, o primer commit. Ademas: si existe un periodo "post-cierre final" para la actividad posterior a la ultima entrega, y si el limite de cada periodo es `due_at` o `lock_at`.

- **Requisitos:** R2.5.6, R2.5.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es la regla de negocio que hace consultable la actividad por entrega; sin ella no se puede implementar el filtro por periodo ni dibujar las lineas de cierre en el grafico.
- **Opciones:**
  - Inicio en la creacion del repositorio
  - Inicio en `unlock_at` de Canvas
  - Inicio en la creacion de la tarea en la aplicacion
  - Inicio en el primer commit
  - Limite en `due_at` / limite en `lock_at`
  - Con periodo post-cierre final / sin el
- **Estudio de APIs:** §8.5 propone filtrar commits por `[entrega_anterior.due, entrega_actual.due]`; no define el inicio del primer periodo ni el tratamiento post-cierre.
- **Fusiona:** P435

### Q-2.5-46 — Dado que la fecha de cierre efectiva varia por seccion, estudiante o grupo, ¿el filtro por periodo usa la fecha efectiva de cada repositorio o una fecha unica para toda la tarea?

Si es una fecha unica, hay que decidir cual: la base, la minima o la maxima de los overrides. Ademas: como se marcan las lineas de cierre en el grafico agregado de la tarea cuando hay varias fechas, y si para los grupos cuyos integrantes tienen fechas distintas se adopta el `max()` de los integrantes senalando la heterogeneidad.

- **Requisitos:** R2.4.2, R2.4.3, R2.5.6, R2.5.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina si el periodo es un atributo de la entrega o de la pareja (entrega, repositorio), lo que cambia consultas, graficos y la coherencia con la captura de version de R2.4.5.
- **Opciones:**
  - Ventana por repositorio segun su fecha efectiva
  - Fecha unica de la tarea (base)
  - Fecha unica (maxima de todos los overrides)
  - Ventana por repositorio mas lineas multiples en el grafico
- **Estudio de APIs:** §7.3 propone usar el `max()` de las fechas efectivas para grupos y mostrarlo en la UI; §8.5 no cruza los periodos con los overrides.
- **Fusiona:** P436

### Q-2.5-47 — ¿Como se muestran los commits posteriores al cierre efectivo de una entrega pero anteriores al siguiente periodo?

Alternativas: como parte del siguiente periodo, como "actividad tardia" de la entrega vencida, o ambas cosas. Ademas: si se agrega un indicador por repositorio de "commits despues del cierre / no incluidos en la version registrada", util para detectar trabajo fuera de plazo y para explicar diferencias con el SHA capturado.

- **Requisitos:** R2.4.7, R2.5.7, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define una metrica y un texto de UI relevantes para la correccion, y la coherencia entre lo que muestra el dashboard y la version efectivamente capturada.
- **Opciones:**
  - Se asignan al siguiente periodo
  - Se marcan como actividad tardia de la entrega vencida
  - Ambas, con etiqueta explicita
  - Indicador por repositorio de commits no incluidos en la version registrada
- **Estudio de APIs:** §7.5 registra el SHA al cierre y menciona que la actividad puede continuar; no aborda su visualizacion.
- **Fusiona:** P437

### Q-2.5-48 — ¿Cual es la enumeracion cerrada de "estado" de una entrega para R2.5.6?

Candidatos: programada (aun no abre), abierta, cerrada (vencida, snapshot pendiente), capturada, capturada parcialmente (algunos repositorios sin commits o con error), en correccion, corregida. Ademas: como se resume el estado cuando, por overrides, algunos repositorios ya cerraron y otros no (por ejemplo "cierra entre el 16-09 y el 20-09; 40/60 versiones capturadas").

- **Requisitos:** R2.4.5, R2.5.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin una enumeracion cerrada no hay criterio de aceptacion para "sus fechas y su estado" ni para la UI de la lista de entregas.
- **Opciones:**
  - Enumeracion minima: abierta / cerrada / capturada
  - Enumeracion completa incluyendo capturada parcialmente y en correccion
  - Estado agregado con contadores por repositorio
  - Estado por repositorio sin estado agregado de la entrega
- **Estudio de APIs:** §5.2 define `snapshot_status` por pareja (entrega, repositorio) y §7.5 define CAPTURED y NO_COMMITS; no existe un estado agregado de la entrega.
- **Fusiona:** P438

### Q-2.5-49 — Si la fecha de una entrega cambia en Canvas despues de que el dashboard ya la uso, ¿se recalculan periodos y metricas y se avisa del cambio?

Hay que decidir si el recalculo de periodos y metricas es automatico, si se muestra un aviso del tipo "fecha modificada el ..., antes era ..." en el dashboard y en el timeline, y si se conserva el historial de fechas anteriores.

- **Requisitos:** R2.4.4, R2.5.6, R2.5.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la reactividad del dashboard a los cambios en Canvas y que explicaciones ve el docente cuando los numeros cambian solos.
- **Opciones:**
  - Recalculo automatico silencioso
  - Recalculo automatico con aviso visible y historial de fechas
  - Recalculo manual confirmado por el docente
  - Sin recalculo: los periodos se congelan al calcularse por primera vez
- **Estudio de APIs:** §7.4 propone un log de auditoria de cambios de fecha y reprogramar el snapshot; no aborda el impacto en el dashboard ni el aviso al docente.
- **Fusiona:** P439

### Q-2.5-50 — ¿Que muestra el dashboard si la tarea de Canvas asociada a una entrega es eliminada o despublicada, o si no tiene `due_at`?

Hay que decidir los textos y comportamientos ("entrega eliminada en Canvas", "sin fecha"), como se delimita el periodo en esos casos, si se desactivan las alertas relativas a fechas, y si una tarea con una sola entrega sin fecha puede tener dashboard de periodos.

- **Requisitos:** R2.5.3, R2.5.6, R2.5.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cubre estados degradados que apareceran en pruebas reales y define comportamientos por defecto para periodos abiertos.
- **Opciones:**
  - Mostrar estado degradado explicito y desactivar alertas por fecha
  - Conservar la ultima fecha conocida y avisar de la desvinculacion
  - Ocultar la entrega del dashboard
  - Periodo abierto sin limite superior cuando no hay `due_at`
- **Estudio de APIs:** §7.3 comenta `due_at` null solo en el contexto de overrides; no aborda la eliminacion de la tarea en Canvas ni las entregas sin fecha.
- **Fusiona:** P440

## Comparacion de integrantes y metricas adicionales

### Q-2.5-51 — ¿Que metricas se comparan entre los integrantes de un mismo grupo y con que alcance temporal?

Candidatas: numero de commits, dias distintos con actividad, lineas anadidas y eliminadas, archivos tocados, porcentaje del total del repositorio, fecha del primer y del ultimo commit. Hay que decidir si se adopta la advertencia del estudio de no priorizar las lineas, y si la comparacion es por toda la tarea, por periodo de entrega, o seleccionable por el docente.

- **Requisitos:** R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define las columnas de la comparacion, si se requiere registrar lineas (con su costo de ingesta) y el criterio de aceptacion de R2.5.8.
- **Opciones:**
  - Commits y dias activos unicamente
  - Commits, dias activos y archivos tocados
  - Ademas lineas anadidas y eliminadas
  - Alcance: toda la tarea / por periodo de entrega / seleccionable
- **Estudio de APIs:** §8.5 propone "commits, lineas y dias activos por autor dentro del repo" y advierte que el conteo de lineas es una metrica pesima, recomendando commits y dias activos.
- **Fusiona:** P441

### Q-2.5-52 — ¿Como se visualiza la comparacion de integrantes y existe un umbral de alerta de desbalance?

Visualizacion candidata: barras apiladas por integrante y periodo, tabla, sparklines por integrante. Sobre la alerta: si existe un umbral de desbalance (por ejemplo, un integrante concentra mas del X % de los commits, o alguien tiene menos del Y % con al menos Z commits totales en el repositorio para evitar falsos positivos en repositorios con 3 commits), si es configurable, quien lo configura, y si el desbalance aparece en el informe diario.

- **Requisitos:** R2.5.8, R2.5.9, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Convierte R2.5.8 en una alerta accionable o solo en una visualizacion; define parametros y su lugar en la configuracion del curso.
- **Opciones:**
  - Solo visualizacion, sin alerta
  - Alerta con umbral fijo
  - Alerta con umbral configurable por curso o por tarea
  - Alerta incluida en el informe diario / solo visible en el dashboard
- **Estudio de APIs:** §8.5 propone un "indice de concentracion" como senal y no como veredicto, sin fijar umbral.
- **Fusiona:** P442

### Q-2.5-53 — En tareas individuales, ¿que ocupa el lugar de la comparacion de integrantes, y se comparan grupos entre si?

Alternativas para tareas individuales: ocultar la seccion, o reemplazarla por una comparacion del estudiante contra la mediana del curso o de su seccion. Por separado: si se comparan grupos entre si (ranking de grupos) o si se considera indeseable mostrarlo.

- **Requisitos:** R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el comportamiento de la vista segun la configuracion individual o grupal de la tarea (R2.3.3) y el alcance de la comparacion.
- **Opciones:**
  - Ocultar la seccion en tareas individuales
  - Comparar contra la mediana del curso
  - Comparar contra la mediana de la seccion
  - Comparar grupos entre si (ranking) / no hacerlo
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P443

### Q-2.5-54 — ¿Que metricas o visualizaciones adicionales se comprometen para R2.5.9?

El estudio sugiere elegir dos o tres. Candidatas: heatmap dia por hora, curva acumulada de commits con lineas de cierre, indice de concentracion, columna "dias desde el ultimo commit" ordenable, ritmo (dias activos sobre dias transcurridos), enlace `compare` entre las versiones de entregas consecutivas, tamano promedio de commit, porcentaje de actividad nocturna o de fin de semana. La lista elegida debe convertirse en requisitos con criterio de aceptacion y con una justificacion defendible el 7-oct.

- **Requisitos:** R2.5.9
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.5.9 es un requisito abierto; sin decision no hay alcance ni pruebas, y la justificacion metodologica se evalua en la actividad de validacion individual.
- **Opciones:**
  - Dos metricas adicionales con criterio de aceptacion cerrado
  - Tres metricas adicionales con criterio de aceptacion cerrado
  - Mas de tres, priorizadas por costo de implementacion
- **Estudio de APIs:** §8.5 lista candidatas y advierte contra el uso de lineas de codigo; §7.5 sugiere el `compare` entre entregas como candidato.
- **Fusiona:** P444

### Q-2.5-55 — ¿Se usan los endpoints `stats/` de GitHub o todo se calcula localmente desde los commits ingeridos?

Los endpoints en cuestion son `contributors`, `punch_card` y `code_frequency`, con respuesta 202 asincrona y cache invalidada por cada push. Si se usan: politica de reintento ante el 202, frecuencia de consulta, y que fuente prevalece cuando sus datos difieren de los propios (por ejemplo, por una regla de atribucion distinta).

- **Requisitos:** R2.5.8, R2.5.9
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita tener dos fuentes de verdad inconsistentes y define, si se usan, un worker adicional con manejo del 202.
- **Opciones:**
  - Todo calculado localmente desde los commits ingeridos
  - Usar `stats/` solo para backfill inicial
  - Usar `stats/` como fuente de metricas agregadas, con politica de reintento
- **Estudio de APIs:** §8.5 incluye una tabla de endpoints `stats/` y advierte del 202, con la indicacion de "nunca llamen esto desde el render".
- **Fusiona:** P445

## Timeline de la evolucion del trabajo

### Q-2.5-56 — ¿Que tipos de evento incluye el timeline de cada repositorio?

Candidatos: commits; marcadores de entrega (fecha efectiva del repositorio, SHA o tag, enlace a `tree/<sha>`, o "sin commits al cierre"); creacion del repositorio; invitaciones enviadas y aceptadas; cambios de integrantes; creacion y borrado de ramas y tags; force push; cambios de fecha de entrega; gaps de inactividad; comunicaciones enviadas al estudiante; correccion publicada. Cada tipo elegido requiere una fuente de datos identificada.

- **Requisitos:** R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el modelo de eventos del timeline y que webhooks o registros internos deben persistirse para poder alimentarlo.
- **Opciones:**
  - Solo commits y marcadores de entrega
  - Ademas eventos del ciclo de vida del repositorio (creacion, invitaciones, integrantes)
  - Ademas eventos de ramas, tags y force push
  - Ademas eventos de la propia aplicacion (comunicaciones, correcciones, cambios de fecha)
- **Estudio de APIs:** §8.6 propone commits (autor, mensaje, hora, tamano), un marcador de entrega con enlace al SHA y los gaps de inactividad; no incluye invitaciones ni ramas.
- **Fusiona:** P447

### Q-2.5-57 — ¿Como se navega el timeline cuando tiene cientos de commits?

Decisiones: agrupacion por dia o por push, paginacion o scroll infinito, colapso de rangos, zoom por periodo de entrega. Filtros por integrante, por periodo y por rama. Si cada commit enlaza a `github.com/O/R/commit/<sha>` y cada entrega a `tree/<sha>`. Y si se muestra el mensaje completo del commit o solo su primera linea.

- **Requisitos:** R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la interaccion y el criterio de aceptacion de "revisar facilmente la evolucion del trabajo" con volumenes reales de commits.
- **Opciones:**
  - Agrupacion por dia con paginacion
  - Agrupacion por push con scroll infinito
  - Zoom por periodo de entrega con colapso de rangos
  - Lista plana sin agrupacion
  - Con filtros por integrante, periodo y rama / sin filtros
- **Estudio de APIs:** §8.6 propone un filtro por autor, un filtro por rango de entrega y una linea vertical de marcador; no aborda paginacion ni agrupacion.
- **Fusiona:** P448

### Q-2.5-58 — ¿Como se identifican los "principales cambios" que exige R2.5.10?

Alternativas: todos los commits se muestran igual; se destacan por tamano (lineas o archivos, lo que depende de si se registran lineas); se destacan por ser merges de pull request; se destacan los tags creados por los estudiantes; o el docente puede marcar hitos manualmente en el timeline.

- **Requisitos:** R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es el criterio de aceptacion literal del parrafo final de la seccion 2.5; sin definicion la vista no puede evaluarse.
- **Opciones:**
  - Sin destacar: todos los commits iguales
  - Por tamano del commit
  - Por merges, pull requests o tags
  - Hitos marcados manualmente por el docente
- **Estudio de APIs:** §8.6 muestra el +/- por commit pero no define que es un cambio "principal".
- **Fusiona:** P449

### Q-2.5-59 — ¿El timeline muestra un resumen de participacion por tramo entre entregas?

Es decir, entre dos marcadores de entrega, un resumen del tipo "3 commits de jperez, 0 de msoto" para cumplir con "que integrantes participaron" en cada entrega, o basta con mostrar el autor en cada commit. Ademas: si el tramo se marca de forma destacada cuando hay integrantes sin commits en el.

- **Requisitos:** R2.5.8, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define un agregado por la terna (repositorio, periodo, integrante) y su presentacion en el timeline.
- **Opciones:**
  - Solo autor por commit
  - Resumen de participacion por tramo entre entregas
  - Resumen por tramo con marca destacada de integrantes sin commits
- **Estudio de APIs:** no lo aborda; §8.6 solo muestra el autor por commit.
- **Fusiona:** P450

## Casos borde, recuperacion y gobierno de datos

### Q-2.5-60 — ¿Que hace el receptor con los eventos de repositorios que no reconoce, incluidos los que llegan antes de que exista su fila en la base de datos, y con la actividad del repositorio base?

La GitHub App recibe webhooks de TODOS los repositorios de la instalacion: el repositorio base, repositorios creados a mano en la organizacion, repositorios de otros cursos o semestres, y repositorios creados por el worker cuyo INSERT en la base de datos fallo. Hay que decidir si esos eventos se descartan en silencio, se registran como "repositorio desconocido" en un panel de diagnostico, o se intenta adoptarlos por nombre, topic o `template_repository`. Caso especifico: al crear un repositorio, GitHub emite webhooks (`repository` created, `push` del commit inicial de la plantilla, `member`) que pueden llegar ANTES de que el worker haya persistido la fila del repositorio; hay que decidir si se descartan confiando en el reconciliador, si se encolan con reintento y TTL hasta que exista la fila, o si se persiste una fila reservada (nombre mas estado CREATING) antes de llamar a GitHub. Por ultimo: si la actividad del repositorio base (commits del profesor) se ingiere y se muestra con su propio historial de versiones, o se excluye del pipeline de commits.

- **Requisitos:** R2.1.5, R2.3.7, R2.3.11, R2.5.2, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el filtro del receptor, la deteccion de repositorios huerfanos, si el repositorio base tiene su propia vista de actividad, y evita que durante el aprovisionamiento masivo se pierdan los primeros eventos o se generen errores ruidosos en el receptor.
- **Opciones:**
  - Descartar silenciosamente los eventos no reconocidos
  - Registrarlos como desconocidos para diagnostico
  - Adoptarlos automaticamente si coinciden con el patron de nombre, topic o plantilla
  - Reservar la fila antes de crear el repositorio en GitHub
  - Encolar los eventos huerfanos con reintento y TTL
  - Descartar y confiar en la reconciliacion periodica
  - Ingerir la actividad del repositorio base / excluirla
- **Estudio de APIs:** §8.1 afirma que "la App recibe eventos de todos los repos de la instalacion automaticamente", sin definir filtrado ni tratamiento del repositorio base, y describe el receptor de webhooks sin abordar el orden entre la creacion del repositorio y sus primeros eventos; §5.5 describe el worker de creacion.
- **Fusiona:** P398, P462

### Q-2.5-61 — Ante un push con `forced: true` o el borrado de una rama, ¿que ocurre con los commits que dejan de ser alcanzables?

Alternativas: eliminarlos de las metricas, conservarlos marcados como "huerfanos", o ignorar el caso. Hay que notar que el polling con `since=` nunca detecta eliminaciones. Ademas: si el timeline muestra un evento "historial reescrito por X" con el `before`/`after` del push.

- **Requisitos:** R2.5.2, R2.5.4, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si las metricas reflejan el estado actual del repositorio o todo lo que alguna vez se subio, y si un estudiante puede borrar su participacion o la de otro.
- **Opciones:**
  - Conservar todo (append-only) y marcar los huerfanos
  - Reconciliar contra el arbol actual y eliminar los huerfanos de las metricas
  - Ignorar el caso
  - Mostrar el evento de reescritura en el timeline / no mostrarlo
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P427

### Q-2.5-62 — Si un repositorio es borrado, renombrado, transferido o archivado en GitHub fuera de la aplicacion, ¿como lo refleja el dashboard?

Alternativas: estado "repositorio no encontrado", re-creacion automatica por el worker, alerta al docente. Ademas hay que cubrir la desinstalacion de la App de la organizacion y el caso en que el webhook devuelve errores repetidos (GitHub deja de entregar hooks que fallan de forma sostenida): si existe una alerta de salud de la integracion visible en el dashboard.

- **Requisitos:** R2.5.2, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define nuevos estados en la maquina de estados del repositorio y una alerta de salud de la integracion, sin la cual el dashboard puede mostrar datos congelados sin avisarlo.
- **Opciones:**
  - Estado "repositorio no encontrado" con alerta al docente
  - Seguimiento del renombrado o transferencia por el id del repositorio
  - Re-creacion automatica por el worker
  - Alerta de salud de la integracion (App desinstalada, webhooks fallando)
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P431

### Q-2.5-63 — ¿Que ocurre con un estudiante retirado del curso en Canvas o que sale de un grupo?

Alternativas: desaparece de la lista "sin participacion", se muestra como "retirado" con sus commits historicos, o se mantiene igual. Ademas: si sus commits siguen contando en la comparacion del grupo y en la actividad del repositorio, y si se marca el momento del retiro en el timeline.

- **Requisitos:** R2.2.1, R2.5.4, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita alertar por estudiantes que ya no estan en el curso y define como se conservan los datos historicos (regla de no borrar filas).
- **Opciones:**
  - Se oculta por completo del dashboard
  - Se muestra como "retirado" con sus commits historicos, fuera de las alertas
  - Se mantiene igual que un estudiante activo
  - Se marca el retiro como evento en el timeline / no se marca
- **Estudio de APIs:** §4.4 y §14 recomiendan marcar `deleted_at` y no borrar, senalando que "un estudiante que se retira sigue teniendo un repo con historia"; no abordan su tratamiento en las metricas.
- **Fusiona:** P422

### Q-2.5-64 — Si Canvas cambia la composicion de un grupo a mitad de una tarea, ¿como se recalculan la atribucion y las alertas?

Escenario: X pasa del grupo A al grupo B. Hay que decidir si los commits de X en el repositorio A siguen atribuidos a X y contando en A; si X aparece en B como "sin participacion" desde su ingreso o si se le mide solo desde la fecha del cambio; si el cambio se registra como evento en el timeline de ambos repositorios; y cuando y como se recomputa `members_with_zero_commits`.

- **Requisitos:** R2.2.3, R2.5.4, R2.5.8, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define los disparadores de recomputacion de agregados ante cambios de membresia y evita alertas falsas tras reasignaciones de grupo.
- **Opciones:**
  - Los commits quedan atribuidos al repositorio donde se hicieron; medicion en el nuevo grupo desde la fecha del cambio
  - Medicion en el nuevo grupo sobre todo el periodo de la tarea
  - Recomputacion inmediata de agregados al detectar el cambio / en el siguiente job periodico
  - Evento de cambio de membresia en el timeline de ambos repositorios / sin evento
- **Estudio de APIs:** §8.3 propone `members_with_zero_commits_json` en RepoStatus; no aborda los cambios de membresia ni su recomputacion.
- **Fusiona:** P423

### Q-2.5-65 — ¿Que permisos controlan el acceso al dashboard, al timeline y a la configuracion del monitoreo?

Hay que decidir si todo ayudante ve la tarea completa o solo los repositorios que tiene asignados para corregir, y quien puede cambiar umbrales (N dias de inactividad, umbral de desbalance), silenciar alertas y pulsar "Actualizar ahora". La tabla de permisos propuesta en el estudio no incluye ningun permiso de monitoreo.

- **Requisitos:** R2.1.8, R2.5.1, R2.5.10, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Completa el modelo de permisos exigido por R2.1.8 (minimo 3 permisos definidos por el equipo) con los permisos de monitoreo y define los filtros por asignacion en las vistas.
- **Opciones:**
  - Todos los roles ven todo el dashboard
  - Los ayudantes ven solo los repositorios asignados
  - Permisos explicitos `monitoring.view` y `monitoring.configure`
- **Estudio de APIs:** §3.4 propone una tabla de permisos (`course.manage`, `assignment.manage`, `repo.provision`, `grading.*`, `student.communicate`, `report.subscribe`) sin ningun permiso de monitoreo.
- **Fusiona:** P452

### Q-2.5-66 — ¿Se muestran a profesores y ayudantes los emails y nombres de autor de los commits?

Los emails y nombres de los commits sin atribuir son necesarios para mapearlos manualmente; hay que decidir si se muestran tal cual o solo mediante un identificador ofuscado. Por separado: si se muestran los emails de los estudiantes ya mapeados en el dashboard.

- **Requisitos:** R2.5.4, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el tratamiento de datos personales de terceros presentes en los commits (un commit puede llevar el email personal de cualquiera) y el contenido de la UI de atribucion manual.
- **Opciones:**
  - Mostrar email y nombre completos a profesores y ayudantes
  - Mostrar email ofuscado con opcion de revelarlo bajo permiso
  - Mostrar solo el nombre, nunca el email
  - Mostrar los emails de estudiantes ya mapeados / no mostrarlos
- **Estudio de APIs:** §8.4 propone mostrar al docente la lista de emails desconocidos para el mapeo manual; no aborda el tratamiento de datos personales.
- **Fusiona:** P453

## Ya respondidas por el enunciado

Ninguna de las 76 preguntas de entrada de esta area quedo resuelta por el texto del enunciado: los 76 veredictos de la etapa de verificacion son ABIERTA (tres de ellos ABIERTA/BLOQUEA: P415, P419 y P460). El enunciado enuncia los requisitos R2.5.1 a R2.5.10 en terminos de que mostrar ("Mostrar un dashboard general para cada tarea", "Presentar informacion sobre la actividad de los distintos repositorios a lo largo del tiempo", "Identificar repositorios que no han presentado actividad reciente", "Identificar estudiantes que aun no hayan participado en el desarrollo de su repositorio", "Permitir comparar la participacion de los integrantes de un mismo grupo") y anade una unica restriccion no funcional ("Esta informacion debera encontrarse disponible de forma inmediata al ingresar a la vista de una tarea, sin requerir esperar a que se recopile en ese momento la actividad de todos los repositorios"), sin definir ningun umbral, definicion operativa, enumeracion de estados, modelo de datos ni criterio de aceptacion numerico. R2.5.9 delega explicitamente en el equipo ("otras metricas o visualizaciones que cada grupo considere utiles") y R2.1.8 hace lo propio con los permisos ("uds. deben definir los permisos, minimo 3").
