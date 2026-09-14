# Preguntas de alcance — Area 2.3

73 preguntas finales, fusionadas desde 124 de entrada (116 del area 2.3 + 8 de la ronda critica), 36 bloqueantes para la parcial.

## Modelo estructural: tarea, entregas y sujetos

### Q-2.3-01 — ¿Cual es la cardinalidad entre una entrega de la app y las tareas de Canvas cuando el profesor duplica el assignment por seccion (una copia por seccion, visible solo a la suya mediante only_visible_to_overrides / "Assign to") en lugar de usar overrides sobre un unico assignment?

R2.3.1 permite vincular "una o mas tareas ya creadas en Canvas" y R2.3.2 asocia cada entrega a una tarea independiente de Canvas, lo que sugiere 1:1 entre entrega y assignment; el patron de assignments duplicados por seccion hace que dos o tres assignments distintos representen conceptualmente la MISMA entrega. Definir: si una entrega puede agrupar varios assignments (derivando la fecha efectiva de cada estudiante del assignment que le es visible y publicando su nota en ese mismo assignment); si cada assignment se vincula como entrega separada (aceptando N entregas, N snapshots y N tags para lo que es una sola entrega, y "no aplica" para cada estudiante en las demas); o si se exige un unico assignment con overrides y la app lo detecta y advierte en la verificacion de vinculacion (R2.1.6) o en el selector. ¿Se ha verificado como esta modelado el curso real de ICC4201 y el curso que usara el evaluador?

- **Requisitos:** R2.3.1, R2.3.2, R2.4.2, R2.5.6, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define la cardinalidad Entrega-assignment en el modelo de datos (claves unicas, snapshots, nombres de tags, denominadores del estado de correccion, vista de entregas), el algoritmo de fecha efectiva y a que submission se publica la nota; cambiarlo despues del 16-sep implica una migracion destructiva sobre datos vivos.
- **Opciones:**
  - Una entrega puede agrupar varios assignments de Canvas (uno por seccion)
  - Cada assignment es una entrega independiente y se acepta la duplicacion visible
  - Se exige un unico assignment con overrides y la app lo valida/advierte al vincular
- **Estudio de APIs:** Fija implicitamente la relacion 1:1: en §5.2 el modelo Delivery tiene un unico canvas_assignment_id ("1:1 con una tarea de Canvas") y en §7.1–7.3 resuelve las fechas por seccion exclusivamente con AssignmentOverride. No contempla el patron de un assignment duplicado por seccion.
- **Fusiona:** N002

### Q-2.3-02 — ¿Que assignments de Canvas se ofrecen en el selector al crear una tarea, con que informacion y filtros, y que reglas de unicidad y validacion se aplican?

Decidir: si se muestran los no publicados, los de tipo quiz/discusion/no-submission/external tool, el assignment auxiliar de "Registro de usuario GitHub" y los ya vinculados a otra tarea de la app; si los no aptos se ocultan o se muestran deshabilitados con el motivo; si un mismo assignment de Canvas puede pertenecer a mas de una tarea de la app o hay unicidad global por curso. Ademas: que datos se muestran por assignment (nombre, fecha, individual/grupal con nombre del group set, publicado o no, si ya esta vinculado), si las entregas se ordenan por fecha y se marca alguna como final por defecto (editable), cual es el mensaje exacto al intentar mezclar individual y grupal (R2.3.3) y que se muestra cuando el curso no tiene tareas en Canvas.

- **Requisitos:** R2.3.1, R2.3.2, R2.3.3
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define la restriccion de unicidad (canvas_assignment_id unico por curso o no), los filtros y validaciones visibles del wizard que se demuestra el 16-sep, el estado vacio y evita que se creen dos conjuntos de repos para el mismo assignment.
- **Opciones:**
  - Mostrar todos y marcar los no aptos como deshabilitados con motivo
  - Mostrar solo publicados y con submission_types compatibles
  - Permitir vincular un assignment a una sola tarea (unicidad estricta)
  - Permitir re-vincular con advertencia
- **Estudio de APIs:** §5.1 recomienda GET /assignments?include[]=all_dates&include[]=overrides y "no creen repos para tareas no publicadas", y lista los campos a mostrar (group_category_id, published, due_at); §5.2 modela Delivery con canvas_assignment_id 1:1 y exige rechazar con mensaje claro si difiere group_category_id, pero no fija unicidad global ni filtros del selector; §6.1 introduce un assignment auxiliar que probablemente no deberia ser vinculable.
- **Fusiona:** P219, P315

### Q-2.3-03 — ¿Que configuraciones del assignment de Canvas se validan al vincular una entrega por afectar la calificabilidad y el flujo, y con que consecuencia (bloquear, advertir o fallar al publicar)?

Verificar contra la instancia real y decidir para cada caso: grading_type=not_graded (Canvas no acepta nota); anonymous_grading=true (identidades ocultas a los graders, ids anonimizados en los endpoints de submissions); moderated_grading=true (calificaciones provisionales, final grader, liberacion de notas — ¿PUT .../submissions/:user_id con posted_grade crea solo una nota provisional?); peer_reviews activo; allowed_attempts que bloquee comentarios; rubric_assessment; y que tipos de assignment aparecen o no en la lista de pendientes y en el calendario del estudiante (¿un assignment de tipo "none" no se muestra y el estudiante nunca ve la fecha?). Definir tambien si esos flags se muestran en el selector, si se revalidan en cada sincronizacion cuando el profesor los cambia despues de vincular y que se muestra en la vista de correccion.

- **Requisitos:** R2.3.1, R2.4.1, R2.7.5, R2.7.6, R2.7.7
- **Tipo:** verificar_empiricamente + decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Evita descubrir el 6-oct que Canvas rechaza las notas o que se violan las condiciones de una tarea anonima o moderada, y asegura que el estudiante vea la fecha de cierre en Canvas.
- **Opciones:**
  - Bloquear la vinculacion de assignments no calificables o con flags incompatibles
  - Advertir en el selector y en la vista de correccion, sin bloquear
  - Operar igual y detectar el error solo al publicar la nota
  - Bloquear unos casos y advertir otros, con revalidacion en cada sincronizacion
- **Estudio de APIs:** §5.1 lista campos del Assignment (group_category_id, published, submission_types, grade_group_students_individually, updated_at) e incluye peer_review entre los include[], y §10.4 documenta el PUT de notas asumiendo que funciona sin precondiciones; no menciona grading_type, anonymous_grading ni moderated_grading.
- **Fusiona:** P215, P279, P305

### Q-2.3-04 — ¿Se permite vincular un assignment con published:false y crear repositorios para el, y que ocurre si el assignment se despublica despues de vinculado?

Definir si el selector acepta assignments no publicados, si el aprovisionamiento corre para ellos (el profesor puede querer preparar los repos antes de publicar) y si al despublicarse se pausan la creacion de repos y las notificaciones o continuan.

- **Requisitos:** R2.3.1, R2.3.7, R2.3.10
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** "Tareas ya creadas en Canvas" (R2.3.1) no equivale a publicadas; la decision afecta al flujo de la demo y a si se crean repos para tareas que el estudiante todavia no ve.
- **Opciones:**
  - No permitir vincular assignments no publicados
  - Permitir vincular pero no crear repos hasta que se publique
  - Permitir vincular y crear repos aunque no este publicado
  - Pausar aprovisionamiento y notificaciones si se despublica despues
- **Estudio de APIs:** §5.1: "published: no creen repos para tareas no publicadas" (recomendacion, no requisito).
- **Fusiona:** P229

### Q-2.3-05 — Si el assignment tiene visibilidad diferenciada (only_visible_to_overrides=true o asignado solo a ciertas secciones o estudiantes), ¿que conjunto de sujetos recibe repositorio?

Verificar como se obtiene la lista de destinatarios (include[]=assignment_visibility) y decidir si se crean repos solo para los estudiantes a quienes la tarea es visible o para todo el curso, y que ocurre si la visibilidad cambia despues (¿se crean repos nuevos, se marcan los sobrantes, se quita acceso?).

- **Requisitos:** R2.3.7, R2.3.10
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** si
- **Por que importa:** El enunciado manda crear "los repositorios necesarios" sin definir el conjunto de sujetos; evita crear repos para estudiantes que no tienen la tarea asignada en Canvas.
- **Opciones:**
  - Crear repos solo para los sujetos a quienes el assignment es visible
  - Crear repos para todos los estudiantes activos del curso
  - Crear segun visibilidad y recalcular el conjunto en cada sincronizacion
- **Estudio de APIs:** §5.1 lista include[]=assignment_visibility; §7.3 trata only_visible_to_overrides solo para snapshots, no para el aprovisionamiento.
- **Fusiona:** P230

### Q-2.3-06 — ¿Como se determinan el orden y el tipo (parcial/final) de las entregas de una tarea, y que ocurre cuando las fechas de Canvas contradicen ese orden?

Definir si el orden lo fija el profesor manualmente (order_index estable), se deriva de due_at recalculado en cada sincronizacion, o resulta del orden de vinculacion. Definir tambien como se identifica "la entrega final" (marca explicita del profesor, ultima por fecha, ultima del orden), si es obligatorio que exista exactamente una final, si una tarea puede tener solo entregas parciales, y si una tarea con una unica entrega es final automaticamente. Casos borde: due_at nulo; la final queda antes de una parcial tras un cambio de fechas en Canvas; dos entregas con la misma fecha; ¿la app reordena automaticamente o solo alerta la inconsistencia? Considerar el efecto sobre los "periodos" de actividad de R2.5.7, definidos entre entregas consecutivas.

- **Requisitos:** R2.3.2, R2.4.4, R2.5.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** El orden alimenta los nombres de tags (entrega-1, entrega-final), los periodos del dashboard, los informes y la navegacion del corrector; un orden mutable rompe referencias ya creadas y debe ser determinista.
- **Opciones:**
  - Orden manual fijado por el profesor (order_index estable) y tipo marcado a mano
  - Orden derivado de due_at y recalculado en cada sincronizacion
  - Manual con advertencia cuando las fechas lo contradicen
  - Exigir exactamente una entrega final por tarea / permitir tareas solo con parciales
- **Estudio de APIs:** §5.2 propone order_index y kind: "partial" | "final" como campos manuales, sin decir como se asignan, si se recalculan ni que cardinalidad se exige.
- **Fusiona:** P220, P221, P289

### Q-2.3-07 — ¿Con que rotulo se identifica cada entrega en la UI, en los tags de GitHub, en los mensajes a estudiantes y en los informes, y que pasa si el assignment se renombra en Canvas?

Decidir entre el nombre del assignment de Canvas sincronizado, una etiqueta propia editable ("Entrega parcial 1", "Entrega final") o un ordinal automatico mas el tipo. Definir si un renombre en Canvas se propaga, se conserva el rotulo propio o se alerta; si se fija un maximo de entregas por tarea; y si se exige unicidad de rotulos dentro de la tarea.

- **Requisitos:** R2.3.2, R2.4.4, R2.4.6, R2.5.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Fija el modelo de datos de Delivery (campo de rotulo), la convencion de tags de R2.4.6 y la regla de sincronizacion de nombres con Canvas.
- **Opciones:**
  - Nombre del assignment de Canvas (sincronizado)
  - Rotulo propio editable
  - Ordinal automatico + tipo (parcial/final)
- **Estudio de APIs:** §5.2 modela kind y order_index sin campo de rotulo; §7.5 usa tags entrega-1 / entrega-final sin definir su origen.
- **Fusiona:** P283

### Q-2.3-08 — ¿El nombre y el slug de la tarea dentro de la app los escribe el profesor o se derivan del primer assignment de Canvas, son editables despues y que efecto tiene cambiarlos sobre los repositorios ya creados?

- **Requisitos:** R2.3.1, R2.3.8
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** El slug es un componente del nombre inequivoco de R2.3.8; su mutabilidad decide si los nombres de repositorio son estables o si hay que renombrar repos existentes.
- **Opciones:**
  - Nombre y slug escritos por el profesor, editables mientras no existan repos
  - Derivados del primer assignment de Canvas y sincronizados
  - Derivados una vez y luego inmutables
  - Editables siempre, sin efecto retroactivo sobre repos ya creados
- **Estudio de APIs:** §5.2 incluye name y slug en Assignment(app) y §5.4 usa {tarea} en la plantilla de nombre, sin decir su origen ni su mutabilidad.
- **Fusiona:** P223

### Q-2.3-09 — ¿Que significa exactamente "misma configuracion" entre las entregas de una tarea (R2.3.3), que hace la app al vincular una entrega divergente y que hace si Canvas rompe la uniformidad DESPUES de creados los repos?

Definir si la uniformidad exige solo coincidir en individual vs grupal o tambien el mismo group_category_id exacto (¿dos assignments grupales con group sets distintos son compatibles?), y si al vincular una entrega divergente se rechaza, se permite con advertencia o se pide elegir cual manda. Para el cambio posterior en Canvas (individual→grupal, grupal→otro group set, grupal→individual): ¿se congela la configuracion detectada al vincular, se marca la tarea "inconsistente" y se pausa el aprovisionamiento con notificacion, o se recalculan los sujetos creando y quitando repos? ¿Puede el profesor desvincular la entrega conflictiva desde la app?

- **Requisitos:** R2.3.3, R2.3.4, R2.3.10, R2.4.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Decide si el worker puede llegar a crear repos de un tipo distinto para la misma tarea (rompiendo R2.3.4: un solo conjunto de repos), define la validacion de R2.3.3 y el estado de error de tarea con su flujo de resolucion.
- **Opciones:**
  - Rechazo estricto: mismo group_category_id identico
  - Rechazo solo si difiere individual/grupal
  - Permitir con advertencia y usar la configuracion de la primera entrega
  - Congelar la configuracion al vincular (o al crear el primer repo) e ignorar cambios posteriores con alerta
  - Marcar tarea "inconsistente", pausar workers y exigir decision
  - Adoptar el cambio y recrear/archivar los repos existentes
- **Estudio de APIs:** §5.2 recomienda comparar group_category_id al vincular y rechazar con mensaje claro si difieren; §7.4 (polling con updated_at) detectaria el cambio posterior pero no propone accion para ese caso.
- **Fusiona:** P224, P225, P286

### Q-2.3-10 — En una tarea grupal, ¿que se hace con los estudiantes que aun no tienen grupo (unassigned), con un group set sin grupos creados y con grupos de 0 integrantes?

Definir si se les crea un repositorio individual, si quedan en un estado pendiente indefinidamente o si hay un plazo tras el cual se actua; y si un grupo vacio cuenta como sujeto del aprovisionamiento.

- **Requisitos:** R2.3.7, R2.3.10, R2.3.11, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el estado PENDING_GROUP de la maquina de estados, que aparece en el panel de faltantes (R2.2.6) y si el worker puede crear repositorios sin dueno.
- **Opciones:**
  - Quedan en estado pendiente hasta que Canvas les asigne grupo
  - Se les crea repositorio individual provisional
  - Se actua tras un plazo configurable
  - Los grupos de 0 integrantes no son sujetos y no generan repositorio
- **Estudio de APIs:** §4.3 senala GET /group_categories/:id/users?unassigned=true para listar estudiantes sin grupo (R2.2.6); no define que hacer con ellos en el aprovisionamiento.
- **Fusiona:** P226

### Q-2.3-11 — ¿Cada tarea de la app tiene siempre su propio conjunto de repositorios, o se permite que una nueva tarea reutilice el conjunto de otra (por ejemplo, un proyecto semestral dividido en tareas por razones administrativas)?

- **Requisitos:** R2.3.4, R2.3.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Confirma la cardinalidad Repository-Tarea 1:1 que sugiere R2.3.4 o abre un caso de repositorios compartidos entre tareas, con efecto sobre snapshots, tags y correccion.
- **Opciones:**
  - Un conjunto de repositorios por tarea, sin excepciones
  - Permitir reutilizar el conjunto de otra tarea con advertencia
  - Permitirlo solo si ambas tareas comparten configuracion y sujetos
- **Estudio de APIs:** §5.2 y §11 (2.3.4): "FK a Assignment, no a Delivery" — un conjunto por tarea.
- **Fusiona:** P276

### Q-2.3-12 — ¿Como se modela el "sujeto" de una tarea (estudiante o grupo) al que apuntan Repository, DeliverySnapshot, GradingAssignment y NotificationOutbox, y cual es el ciclo de vida de la fila Repository?

Opciones de modelado: entidad Subject polimorfica unica (subject_id, kind, canvas_user_id | canvas_group_id); dos FKs nullable en cada tabla con CHECK de exclusion; o representar toda tarea individual como "grupo de uno" para unificar el codigo. Definir ademas: si se crean filas Repository para TODOS los sujetos al crear la tarea (en estado PENDING_*) y se recalculan en cada sincronizacion (alta → nueva fila, baja → marcar), o solo cuando la informacion esta completa; si un mismo sujeto puede tener mas de una fila Repository en la misma tarea (historica SUPERSEDED tras corregir un mapeo, mas la vigente) y cual es entonces la clave unica; y si una tarea puede mezclar owner_kind (repositorio individual para quien no tiene grupo).

- **Requisitos:** R2.3.4, R2.3.7, R2.3.10, R2.3.11, R2.4.5, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija las claves unicas, los indices y la forma de todas las consultas del worker, del dashboard y de la correccion; decide si R2.3.11 puede listar pendientes antes de que exista informacion y si es posible sustituir un repositorio sin perder snapshots.
- **Opciones:**
  - Subject polimorfico
  - Dos FKs nullable + CHECK de exclusion
  - Grupo de uno para las tareas individuales
  - Filas eager para todos los sujetos desde la creacion de la tarea
  - Filas lazy solo cuando la informacion esta completa
- **Estudio de APIs:** §5.2 propone Repository con owner_kind y dos columnas canvas_user_id | canvas_group_id; §5.5 crea filas PENDING_MAPPING para sujetos sin login. No aborda filas historicas ni mezcla de owner_kind.
- **Fusiona:** P320

### Q-2.3-13 — Ademas de las fechas, ¿que campos del assignment de Canvas se copian a Delivery, para cuales se conserva historial de versiones y que cambio dispara que reaccion?

Campos candidatos: name, published, workflow_state, group_category_id, grade_group_students_individually, only_visible_to_overrides, points_possible, grading_type, submission_types, rubric y rubric_settings, updated_at, html_url. Decidir si se versiona la entrega completa (DeliveryRevision) o solo se guarda el valor vigente; si se almacena el JSON crudo de cada objeto Canvas sincronizado (assignment, override, enrollment, group) junto a las columnas normalizadas para depurar y recalcular sin volver a llamar a la API; y que cambio de campo dispara alerta, bloqueo o recalculo.

- **Requisitos:** R2.3.1, R2.3.3, R2.4.4, R2.7.5, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Fija la tabla Delivery y la matriz de deteccion de drift; sin historial no se puede explicar por que una nota o un snapshot se hicieron con una configuracion anterior.
- **Opciones:**
  - Copiar campos clave sin historial
  - Versionar la entrega completa (DeliveryRevision)
  - Guardar JSON crudo + columnas normalizadas
- **Estudio de APIs:** §5.1 lista "campos que deciden todo tu modelo"; §7.4 solo versiona fechas en el log de auditoria.
- **Fusiona:** P323

## Repositorio base y contenido inicial

### Q-2.3-14 — ¿Como se constituye el repositorio base de una tarea: donde se crea, con que convencion y parametros, se puede designar uno ya existente en la organizacion o importar contenido, y es un paso saltable del flujo de crear tarea?

Definir: ubicacion (organizacion del curso u otra), convencion de nombre (por ejemplo {curso}-{tarea}-base), visibilidad, si se marca is_template, si se usa auto_init, y que ocurre si ya existe un repositorio con ese nombre en la organizacion. Definir tambien si el unico camino es crearlo desde la app como sugiere la lectura literal de R2.3.5, o si ademas se admite designar un repositorio existente de la organizacion (con que validaciones: pertenencia a la org, is_template) o importar contenido desde una URL o un zip. Y si el paso es saltable con "agregar despues" dentro del wizard de tarea.

- **Requisitos:** R2.3.5, R2.3.6, R2.3.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija el flujo de R2.3.5, los permisos requeridos por la GitHub App, el comportamiento ante colision de nombre y el alcance del wizard de tarea que se demuestra el 16-sep.
- **Opciones:**
  - Solo creacion desde la app, con convencion de nombre fija
  - Permitir designar un repositorio existente de la organizacion como base
  - Permitir importar contenido desde URL o archivo comprimido
  - Paso saltable con "agregar despues"
  - Fallar ante colision de nombre / reutilizar el repositorio existente
- **Estudio de APIs:** §5.3 recomienda crearlo en la organizacion como template repository con auto_init:true y private:true, y propone un explorador de archivos en la app mas un boton "abrir en GitHub"; no aborda designar uno existente, importar contenido ni los cambios tardios.
- **Fusiona:** P233, P234, P318

### Q-2.3-15 — ¿Que alcance tiene "incorporar y administrar los archivos iniciales" (R2.3.6): que limites de subida se aplican, hay CRUD completo dentro de la app y la app es fuente de verdad o espejo de GitHub?

Definir: cuantos archivos se pueden subir, tamano maximo por archivo y total (la Contents API es comoda hasta 1 MB; el hosting impone su propio limite de body), tipos permitidos incluyendo binarios en base64, soporte de carpetas y rutas anidadas, subida de zip, .gitignore por plantilla y generacion de README; que pasa con una carpeta vacia (git no la soporta). Definir tambien si se pueden editar, renombrar y eliminar archivos desde la app (explorador/editor, drag and drop) o solo directamente en GitHub, y si la app refleja los cambios hechos por el profesor directamente en GitHub. Y del lado operativo: si los archivos pasan directo a GitHub sin almacenamiento propio (el filesystem del PaaS es efimero) o se guardan temporalmente, y que estado muestra la UI y como se reanuda si falla a mitad de una subida en serie.

- **Requisitos:** R2.3.5, R2.3.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define las validaciones del formulario, los mensajes de error, la API a usar (Contents vs Git Data) y si la pantalla de repositorio base es un explorador completo o un enlace a GitHub.
- **Opciones:**
  - CRUD completo dentro de la app (explorador/editor propio)
  - Solo subida inicial, edicion posterior en GitHub
  - Espejo de solo lectura con enlace "abrir en GitHub"
  - Paso directo a GitHub sin almacenamiento propio / almacenamiento temporal con reanudacion
- **Estudio de APIs:** §5.3 usa PUT /contents con base64, indica los limites de la Contents API (1 MB comodo, 1–100 MB solo raw, mas de 100 MB no), recomienda subir archivos en serie por conflictos, menciona gitignore_template en POST /orgs/{org}/repos, sugiere la Git Data API para archivos grandes y propone explorador de archivos (GET /contents + textarea + PUT, que requiere el blob sha para actualizar).
- **Fusiona:** P235, P236, P302

### Q-2.3-16 — ¿Como se preservan las propiedades de los archivos que la Contents API no soporta (bit de ejecucion, symlinks) y que validaciones se aplican a las rutas y a los finales de linea?

La Contents API crea todos los archivos con modo 100644: los scripts que requieren bit de ejecucion (gradlew, mvnw, run.sh) lo pierden, y no soporta symlinks. Decidir si se declara fuera de alcance con aviso en la UI, si se usa la Git Data API (blobs/trees con modo 100755) para el repositorio base, o si se instruye al profesor a corregirlo en GitHub. Definir ademas que validacion se aplica a las rutas subidas (dos puntos seguidos, barra inicial, espacios, unicode, colision por mayusculas README.md vs readme.md) y que se hace con los finales de linea CRLF de archivos subidos desde Windows.

- **Requisitos:** R2.3.6, R2.3.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** En tareas de programacion un wrapper sin permiso de ejecucion rompe el arranque para todos los estudiantes; la decision fija la API a usar y las reglas de validacion del explorador de archivos.
- **Opciones:**
  - Contents API y documentar la limitacion
  - Git Data API para preservar modos
  - Editor de modo por archivo en la UI
  - Normalizar CRLF a LF / conservar el contenido tal cual
- **Estudio de APIs:** §5.3 usa PUT /contents con base64 y menciona la Git Data API solo para archivos grandes; no aborda modos de archivo, symlinks ni validacion de rutas.
- **Fusiona:** P282

### Q-2.3-17 — ¿Se permiten workflows de GitHub Actions en el repositorio base y quedan Actions habilitadas en los repositorios de los estudiantes?

Incluir archivos en .github/workflows exige el permiso Workflows en la GitHub App y consume minutos de Actions de la organizacion (limitados en repositorios privados con plan Free). Decidir si se validan rutas prohibidas o se pide el permiso adicional; si la app deshabilita Actions al crear cada repositorio (PUT /repos/{o}/{r}/actions/permissions enabled=false), lo deja habilitado, lo delega a la configuracion de la organizacion o lo hace configurable por tarea (algunos profesores quieren CI). Si queda habilitado, definir si los commits de github-actions[bot] y los eventos de workflow se excluyen o se muestran en dashboard y timeline.

- **Requisitos:** R2.3.6, R2.3.7, R2.5.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Afecta el costo y los limites de la organizacion del profesor, los permisos que debe pedir la GitHub App, la validacion de rutas del repositorio base y la limpieza de las metricas de actividad.
- **Opciones:**
  - Prohibir archivos en .github/workflows en el repositorio base
  - Permitirlos y solicitar el permiso Workflows en la App
  - Deshabilitar Actions en cada repositorio al crearlo
  - Dejar Actions habilitado / delegar a la configuracion de la organizacion / configurable por tarea
  - Excluir los commits de bots de las metricas de participacion
- **Estudio de APIs:** §5.3 indica "Contents (write) o Contents + Workflows write si suben archivos en .github/workflows/"; no aborda Actions en los repositorios de estudiantes.
- **Fusiona:** P239, P306

### Q-2.3-18 — ¿La generacion de cada repositorio a partir del base usara POST /repos/{template}/generate o una copia de archivos via Contents API, con que permisos exactos de la instalacion, funciona en una organizacion Free y con que rama por defecto queda el repositorio generado?

Verificar empiricamente ambos caminos, incluido el uso de include_all_branches.

- **Requisitos:** R2.3.5, R2.3.7
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** El estudio deja los permisos como ambiguos; un 403 el dia de la demo bloquea R2.3.7.
- **Opciones:**
  - Template + POST /generate
  - Creacion vacia + copia de archivos via Contents API
  - Camino distinto segun disponibilidad del plan de la organizacion
- **Estudio de APIs:** §5.3–§5.4 recomiendan template + generate; §2.3 y el Apendice A.1/A.2 piden verificar empiricamente los permisos de POST /orgs/{org}/repos y de /generate.
- **Fusiona:** P238

### Q-2.3-19 — Tras POST /repos/{template}/generate GitHub responde 201 pero la copia del contenido es asincrona: ¿el worker espera a detectar el commit inicial antes de continuar o sigue de inmediato y tolera 409 en los pasos posteriores?

Durante algunos segundos el repositorio puede estar vacio (GET /commits devuelve 409, default_branch sin refs). Definir si se hace polling hasta ver el commit inicial (con que timeout y cuantos intentos) antes de marcar CREATED, leer default_branch, aplicar protecciones y registrar el "commit base" de referencia; o si se continua de inmediato y se toleran los 409 en snapshot y backfill. Definir que estado intermedio se muestra en R2.3.11 mientras tanto.

- **Requisitos:** R2.3.7, R2.3.9, R2.3.11
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Afecta la maquina de estados del worker, la identificacion del commit inicial para las metricas de R2.5 y la aplicacion de protecciones; un 409 no manejado marcaria ERROR repositorios validos.
- **Opciones:**
  - Poll hasta ver el commit inicial (timeout N s) antes de CREATED
  - Marcar CREATED de inmediato y resolver default_branch y commit base en un paso posterior
  - Diferir al reconciliador de commits
- **Estudio de APIs:** §5.4 y §5.5 paso 3 guardan default_branch inmediatamente tras la creacion; no mencionan la latencia de la copia del template.
- **Fusiona:** P280

### Q-2.3-20 — ¿Que contenido tiene el repositorio de un estudiante cuando la tarea NO tiene repositorio base, y admiten los archivos personalizacion por sujeto?

Sin base, el repositorio se crea con auto_init:true y su commit inicial es un README vacio firmado por la App. Decidir si se acepta ese README vacio o si la app sube un README propio (nombre de la tarea, entregas y fechas efectivas, enlace a la tarea en Canvas, instrucciones de clonado e invitacion) y un .gitignore por plantilla (gitignore_template segun el lenguaje elegido por el profesor), si ese contenido es editable por el profesor y si se mantiene coherente con lo que reciben los repositorios generados desde un base. Decidir ademas si los archivos admiten personalizacion por sujeto (marcadores como estudiante, grupo, seccion o fecha de la entrega), lo que exigiria un commit adicional por repositorio tras el generate, o si el contenido es identico para todos y solo la description del repositorio es personalizada; y si el README incluye fechas y Canvas las cambia, si queda desactualizado (documentado), se actualiza con un commit del bot o se evita poner fechas en archivos.

- **Requisitos:** R2.3.5, R2.3.6, R2.3.7, R2.3.12, R2.4.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define el contenido minimo de un repositorio sin base, si existe un paso "lenguaje/.gitignore" en el formulario de tarea, el costo en requests por repositorio, la autoria de los commits del bot en las metricas y que commit se considera "inicial" al excluirlo de la participacion.
- **Opciones:**
  - README vacio de auto_init
  - README generado por la app con datos de la tarea
  - README + .gitignore elegido por el profesor
  - Sin personalizacion de archivos (solo description del repositorio)
  - Marcadores sustituidos por sujeto + commit adicional del bot por repositorio
  - README generado sin fechas volatiles
- **Estudio de APIs:** §5.4 indica "sin repo base: POST /orgs/{org}/repos con auto_init" y personaliza solo la description del repositorio generado; §5.3 lista gitignore_template como parametro sin decidir su uso y propone un template repo de contenido identico para todos.
- **Fusiona:** P281, P307

### Q-2.3-21 — Si el repositorio base se agrega, se reemplaza o se modifican sus archivos cuando ya existen repositorios de estudiantes, ¿que ocurre con los ya creados?

Decidir entre: no tocarlos (aceptando repositorios heterogeneos entre estudiantes, con advertencia), bloquear la edicion o el cambio del base una vez creado el primer repositorio, o propagar el cambio mediante commit o pull request automatico en cada repositorio existente. Decidir tambien si una tarea creada sin base cuyos repositorios ya existen vacios puede recibir un base despues, y si R2.3.11 muestra con que version del base (SHA del template) se creo cada repositorio.

- **Requisitos:** R2.3.5, R2.3.6, R2.3.7, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Determina la inmutabilidad del repositorio base tras el primer aprovisionamiento, evita conjuntos de repositorios heterogeneos y define las transiciones bloqueadas del ciclo de vida de la tarea.
- **Opciones:**
  - No retroactivo, mostrar advertencia de repositorios heterogeneos
  - Bloquear cambios del base tras el primer repositorio creado
  - Propagar mediante commit o pull request automatico
  - Registrar y mostrar el SHA del base usado en cada repositorio
- **Estudio de APIs:** §5.3 propone el repositorio base como template con explorador de archivos, pero no aborda su evolucion despues de crear repositorios.
- **Fusiona:** P237, P294

## Nomenclatura de repositorios

### Q-2.3-22 — ¿Cual es la funcion de nombrado de los repositorios: que componentes la forman, es un patron fijo o configurable con vista previa, que reglas de sanitizacion y truncado aplica y es el nombre inmutable ante cambios en los datos de origen?

Definir los componentes exactos (codigo de curso, periodo, slug de tarea, seccion, identificador de grupo — canvas_group_id o slug del nombre —, identificador del estudiante — login de GitHub, canvas_user_id o nombre); si el nombre incluye datos humanos (nombre del estudiante o del grupo, con tildes, enie o emoji) o solo identificadores estables, y si debe evitarse exponer datos personales; si el patron es fijo del sistema o configurable por curso o por tarea, visible y ajustable por el profesor antes de aprovisionar con vista previa (por ejemplo icc4201-2026-2-t1-jperez), y si se advierte que el nombre incluira el login del estudiante. Definir las reglas de sanitizacion (minusculas, tildes y enie, caracteres permitidos, guiones consecutivos, nombres reservados, nombre que sanitizado queda vacio) y, ante el limite de 100 caracteres de GitHub, que componente se trunca primero y como se garantiza unicidad tras truncar. Definir por ultimo si el nombre es inmutable cuando cambia el dato de origen (grupo renombrado en Canvas, estudiante que cambia su login de GitHub, mapeo corregido, dos grupos llamados igual): ¿se renombra el repositorio (GitHub mantiene redirecciones), se conserva el nombre original o se muestra un alias en la app?

- **Requisitos:** R2.2.3, R2.3.8, R2.3.9
- **Tipo:** decision_equipo + investigable_en_docs · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es el nucleo de R2.3.8: decide unicidad, legibilidad, privacidad, estabilidad a lo largo del semestre y la funcion determinista de nombrado con sus pruebas unitarias.
- **Opciones:**
  - Convencion fija propuesta en §5.4 del estudio
  - Plantilla configurable por curso con vista previa
  - Plantilla configurable por tarea
  - Incluir seccion en el nombre
  - Usar canvas_user_id / canvas_group_id en lugar de nombres o logins
  - Nombre inmutable tras la creacion / renombrar el repositorio al cambiar el dato de origen
- **Estudio de APIs:** §5.4 propone {curso}-{periodo}-{tarea}-{githublogin} e {curso}-{periodo}-{tarea}-g{canvas_group_id}-{slug_grupo}, recomienda incluir canvas_group_id para unicidad, sanitizar a minusculas, reemplazar los caracteres no permitidos por guion, colapsar guiones y truncar a 100, y sugiere sufijo -2 ante colision; no define prioridad de truncado ni inmutabilidad, y §5.2 guarda github_repo_id (estable ante renombres). Es propuesta no aprobada.
- **Fusiona:** P241, P242, P244, P298, P317

### Q-2.3-23 — Ante una colision de nombre (422 "name already exists"), ¿la app agrega un sufijo, falla con error visible o adopta el repositorio existente, y como distingue un repositorio propio de uno ajeno preexistente en la organizacion?

El estudio propone tratar el 422 como exito y continuar con el repositorio existente. Definir bajo que condiciones es seguro adoptarlo (creado por la app en un intento previo, marcado con topic o descripcion de la app, sin colaboradores ajenos, vacio) y cuando debe marcarse ERROR para revision (repositorio creado a mano, de otro curso o semestre, con contenido). Definir el marcador de propiedad (github_repo_id, topic, descripcion) y si se ofrece al profesor la accion manual "vincular repositorio existente".

- **Requisitos:** R2.3.7, R2.3.8, R2.3.10, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** La idempotencia del worker depende de esta regla y adoptar un repositorio ajeno daria a estudiantes acceso a codigo de otros.
- **Opciones:**
  - Adoptar solo si tiene marcador de la app (topic/descripcion) en la organizacion vinculada
  - Adoptar siempre (422 como exito)
  - Nunca adoptar: ERROR y accion manual "vincular existente"
  - Reintentar con sufijo -2
- **Estudio de APIs:** §5.4 sugiere reintentar con sufijo -2; §5.5 indica tratar el 422 name already exists como exito, hacer GET del repositorio y continuar por idempotencia, sin distinguir repositorios ajenos.
- **Fusiona:** P243, P292

## Acceso a GitHub: modelo de colaboradores, invitaciones y configuracion del repositorio

### Q-2.3-24 — ¿Cual es el modelo de acceso a los repositorios: outside collaborators por repositorio, miembros de la organizacion o teams, con que nivel de permiso para estudiantes y con que mecanismo para el equipo docente?

Decidir: si los estudiantes se agregan como colaboradores directos por repositorio, se invitan como miembros de la organizacion (una invitacion por semestre, con PUT que devuelve 204 inmediato en cada repositorio) o se usan Teams de GitHub (un team por grupo, que permite ver miembros y cambiar acceso en bloque, y/o un "team docente" con lectura sobre todos los repositorios del curso). Si son miembros de la organizacion: si la default repository permission queda en none para que no vean repositorios ajenos y si hay limite de asientos segun el plan. Definir el nivel de permiso del estudiante en su repositorio (push, maintain o admin), si el profesor y los ayudantes se agregan como colaboradores, como miembros u owners de la organizacion o si solo acceden via la App, que permisos extra de la GitHub App exige cada opcion (por ejemplo Members write) y si al retirar a un ayudante (R2.1.9) se le quita acceso a los repositorios.

- **Requisitos:** R2.3.9, R2.3.11, R2.1.8, R2.1.9, R2.7.4
- **Tipo:** decision_equipo + dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Cambia la maquina de estados de acceso (cuantos estados pendientes existen), los permisos de la GitHub App, el costo en requests por grupo y la seguridad de las versiones registradas: con admin el estudiante puede borrar tags o el repositorio y romper R2.4.7.
- **Opciones:**
  - Colaboradores directos por repositorio (estudiantes y docentes)
  - Miembros de la organizacion con base permission none
  - Team docente + colaboradores directos para estudiantes
  - Team por grupo + team docente
  - Permiso del estudiante: push / maintain / admin
- **Estudio de APIs:** §5.4 indica "Usen push, NUNCA admin", describe la "Alternativa con Teams" y recomienda colaboradores directos por simplicidad; §6.4 presenta la invitacion a la organizacion como opcional que mejora la experiencia y requiere permiso Members (write); §3.4 sugiere DELETE /orgs/{org}/memberships/{username} al retirar a un ayudante.
- **Fusiona:** P245, P249, P312

### Q-2.3-25 — ¿Los repositorios son siempre privados o la visibilidad es configurable por tarea, y que limites impone el plan de la organizacion de GitHub (Free/Team/Education) a repositorios privados, colaboradores y funcionalidades?

- **Requisitos:** R2.3.7, R2.3.9
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Determina el parametro private/visibility del payload de creacion, la privacidad del trabajo de los estudiantes y que protecciones (rulesets, branch protection) son siquiera posibles.
- **Opciones:**
  - Siempre privados
  - Visibilidad configurable por tarea
  - Visibilidad condicionada al plan de la organizacion
- **Estudio de APIs:** §14: "Crenlos privados. Si la org es Free, revisen el limite de colaboradores en repos privados de organizacion".
- **Fusiona:** P252

### Q-2.3-26 — ¿Se aplica proteccion a la rama por defecto y a los tags de entrega, cual es el conjunto EXACTO de reglas, se verifica antes del 16-sep que el flujo normal del estudiante sigue funcionando y como se entera el equipo docente si una regla lo bloquea?

Definir si se usan rulesets o branch protection y con que reglas exactas (por ejemplo solo impedir borrado y force-push de la rama por defecto y de refs/tags/entrega-*, sin exigir pull request, revisiones ni status checks), y si esta disponible en el plan de la organizacion para repositorios privados; si no lo esta, si se acepta el riesgo documentando que el SHA guardado en la base de datos es la fuente de verdad. Verificar con una cuenta de estudiante real, antes del 16-sep, que siguen funcionando el push directo a la rama por defecto, la creacion y el borrado de ramas propias, los merges y los tags propios del estudiante. Definir que mensaje de error ve el estudiante si una regla lo bloquea, por que canal se entera el equipo docente (hoy ese repositorio apareceria simplemente como "sin actividad reciente") y quien puede desactivar la regla de emergencia durante una entrega.

- **Requisitos:** R2.3.7, R2.3.9, R2.4.7, R2.5.3
- **Tipo:** dependencia_externa + verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Impacta R2.4.7 y el permiso que reciben los estudiantes, exige permisos adicionales de la App y, mal configurada, una regla bloquea silenciosamente a todo el curso y solo se descubre en el cierre, cuando ya no hay commits que capturar.
- **Opciones:**
  - No aplicar ninguna proteccion y confiar en el SHA guardado en la BD
  - Proteger solo tags entrega-* contra borrado y modificacion
  - Proteger tags y ademas la rama por defecto contra force-push y borrado
  - Proteger todo y aceptar que el flujo del estudiante requiera pull requests
  - Agregar un estado o alerta especifico distinto de "sin actividad" para el bloqueo por regla
- **Estudio de APIs:** §7.5 sugiere una ruleset de tags opcional (POST /orgs/{org}/rulesets con target tag) y afirma que no es imprescindible si el SHA esta en la base de datos; §5.4 recomienda dar permiso push y no admin. No analiza el riesgo de que las reglas bloqueen el trabajo normal del estudiante ni como verificarlo.
- **Fusiona:** P253, N014

### Q-2.3-27 — ¿Que rama se considera la del trabajo del estudiante: se fija "main" o se lee de repository.default_branch, que pasa si el estudiante la cambia y que ocurre si al cierre el trabajo esta en otra rama?

Definir si el snapshot se toma solo de la rama por defecto (y el corrector puede ver un repositorio casi vacio), de la rama con el ultimo commit, o si se registran todas las ramas; si la actividad del dashboard y el timeline consideran todas las ramas o solo la por defecto; si la app sigue una rama por defecto cambiada por el estudiante o mantiene la original para snapshots y metricas; y si esta regla se comunica al estudiante en el mensaje de disponibilidad del repositorio.

- **Requisitos:** R2.3.7, R2.3.12, R2.4.5, R2.5.2, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Afecta la captura de snapshots (R2.4.5), el conteo de actividad, la ingesta de webhooks (filtrar ref o no) y el texto de las comunicaciones automaticas.
- **Opciones:**
  - Snapshot y metricas solo de la rama por defecto vigente
  - Seguir la rama con el ultimo commit
  - Registrar todas las ramas
  - Congelar la rama por defecto detectada al crear el repositorio
- **Estudio de APIs:** §14: "No asuman main. Leanla de repository.default_branch"; §7.5 usa sha={default_branch} y §8.1 sugiere filtrar por rama por defecto "si quieren", sin fijar una regla.
- **Fusiona:** P254, P291

### Q-2.3-28 — ¿Que metadatos y ajustes se fijan al crear cada repositorio (description, topics, has_issues/has_wiki/has_projects, allow_forking, delete_branch_on_merge)?

Definir en particular si la description incluye el nombre del estudiante o del grupo y la seccion, y si se usan topics (curso, periodo, tarea) para filtrar e identificar los repositorios propios de la app.

- **Requisitos:** R2.3.7, R2.3.8
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define el payload de creacion, el marcador que permite identificar repositorios "propios" y consideraciones de privacidad sobre los datos visibles en GitHub.
- **Opciones:**
  - Description con nombre del sujeto y seccion / description neutra
  - Topics de curso, periodo y tarea como marcador de propiedad
  - Desactivar issues, wiki, projects y forks
  - Dejar los valores por defecto de GitHub
- **Estudio de APIs:** §5.4 usa description "Tarea 1 — Juan Perez (Seccion 2)" en el ejemplo; no aborda topics ni otros ajustes.
- **Fusiona:** P255

### Q-2.3-29 — Si la GitHub App esta instalada con "selected repositories" en la organizacion, ¿los repositorios creados por la propia App quedan automaticamente incluidos en la instalacion, o hay que exigir instalacion en "all repositories" al vincular el curso?

- **Requisitos:** R2.3.7, R2.3.9
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Si no quedan incluidos, las llamadas posteriores sobre el repositorio fallan con 404/403 y no llegan webhooks; condiciona el checklist de vinculacion de R2.1.5/R2.1.6.
- **Opciones:**
  - Exigir instalacion en "all repositories" y validarlo al vincular
  - Aceptar "selected repositories" si los repositorios creados se incorporan solos
  - Agregar explicitamente cada repositorio creado a la instalacion
- **Estudio de APIs:** No lo aborda; §3.3 solo confirma la instalacion con GET /orgs/{org}/installation.
- **Fusiona:** P274

### Q-2.3-30 — ¿Como detecta la app el desenlace de una invitacion (aceptada, rechazada o expirada): polling a GET /collaborators e /invitations o webhooks de la App (member, member_invite), y que estado, reintentos y avisos corresponden a cada desenlace?

Verificar si la App recibe efectivamente un evento cuando un outside collaborator acepta, con que frecuencia se haria polling y a que costo de rate limit para un curso completo; y como se detecta un rechazo (desaparece de /invitations sin aparecer en /collaborators). Definir el estado y el mensaje que se muestran ante un rechazo, si se reintenta automaticamente y si se avisa al profesor.

- **Requisitos:** R2.3.9, R2.3.11
- **Tipo:** verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define la latencia de la transicion a READY, la carga sobre el rate limit y la distincion entre "pendiente" y "rechazado" en la maquina de estados, evitando reintentos infinitos.
- **Opciones:**
  - Polling periodico a /collaborators e /invitations
  - Webhooks member / member_invite
  - Combinacion de webhook con reconciliacion periodica de respaldo
- **Estudio de APIs:** §8.1 lista los eventos push, create, delete, repository, member y member_invite "segun disponibilidad"; §5.4 propone monitorear via GET /invitations (con campo expired) y cubre 201/204 e invitaciones pendientes o expiradas, pero no el rechazo.
- **Fusiona:** P247, P248

### Q-2.3-31 — Las invitaciones de colaborador expiran a los siete dias: ¿la app las reenvia automaticamente, con que frecuencia y hasta cuantas veces, existe accion manual de reenvio y quien puede usarla?

Verificar antes que el reenvio es viable: si revocar con DELETE y volver a hacer PUT hace que GitHub reenvie efectivamente el correo, cuanto tarda en expirar una invitacion, que se ve en la API cuando expira, y si el estudiante puede aceptar desde la UI de GitHub sin el correo (github.com/<org>/<repo>/invitations). Definir si se notifica al estudiante por Canvas en cada reenvio y que instruccion alternativa se le da.

- **Requisitos:** R2.3.9, R2.3.11, R2.3.12
- **Tipo:** decision_equipo + verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define la transicion COLLABORATORS_PENDING → READY, los recordatorios, el trabajo del worker y si el boton "Reenviar invitacion" de la tabla de estados es viable y con que texto.
- **Opciones:**
  - Reenvio automatico periodico con tope de intentos
  - Solo accion manual del equipo docente
  - Automatico mas manual, con aviso por Canvas en cada reenvio
  - Sin reenvio: se instruye al estudiante a aceptar desde la UI de GitHub
- **Estudio de APIs:** §5.4 documenta GET /repos/{o}/{r}/invitations (campo expired), PATCH y DELETE "util para reenviar"; §5.6 muestra una accion "Reenviar" en la tabla de estados.
- **Fusiona:** P246, P319

### Q-2.3-32 — GitHub limita la cantidad de invitaciones que un repositorio u organizacion puede emitir por periodo: ¿cuales son los limites vigentes y que hace la app al alcanzarlos en un curso de 200 estudiantes?

Investigar en la documentacion de GitHub y probar con la organizacion real (incluidos los limites de invitaciones a la organizacion para organizaciones nuevas). Definir la politica: pausar y reprogramar, marcar los repositorios como "invitacion diferida" en R2.3.11, o invitar previamente a la organizacion.

- **Requisitos:** R2.3.9, R2.3.10, R2.3.11
- **Tipo:** investigable_en_docs · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Un limite de invitaciones detiene el aprovisionamiento masivo en plena demo; la especificacion necesita un estado visible y una politica de espera.
- **Opciones:**
  - Pausar y reprogramar el envio de invitaciones
  - Estado "invitacion diferida" visible en la vista de estado
  - Invitar previamente a la organizacion para evitar el limite por repositorio
- **Estudio de APIs:** No lo aborda (§2.4 cubre los rate limits de la API, no los limites de invitaciones).
- **Fusiona:** P296

### Q-2.3-33 — Muchos estudiantes crearan su cuenta de GitHub el mismo dia que registran su usuario: ¿que ocurre con las invitaciones a cuentas recien creadas, sin correo verificado o con invitacion a la organizacion pendiente, y que estado muestra la app?

Verificar con una cuenta recien creada: si una cuenta sin email verificado recibe y puede aceptar la invitacion de colaborador a un repositorio privado de una organizacion; si GitHub impone restricciones a cuentas nuevas (limites de invitaciones recibidas, verificacion adicional) que dejen la invitacion en un estado no visible en GET /invitations; y si un usuario con invitacion a la organizacion PENDIENTE recibe 201 o 204 al ser agregado como colaborador y que ocurre al aceptar la organizacion despues. Definir el estado y el mensaje que muestra la app para "invitacion enviada pero cuenta sin verificar".

- **Requisitos:** R2.3.9, R2.3.11
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Determina si hace falta un estado adicional en R2.3.11 y un texto en la tarea de registro ("verifica tu correo en GitHub antes de registrar tu usuario").
- **Opciones:**
  - Estado especifico "cuenta sin verificar" con instruccion al estudiante
  - Tratarlo como invitacion pendiente comun
  - Validar el estado de la cuenta antes de invitar
- **Estudio de APIs:** §5.4 y §6.4 describen 201 (invitacion) frente a 204 (acceso directo); no abordan cuentas nuevas, correos sin verificar ni invitaciones a la organizacion pendientes.
- **Fusiona:** P218

### Q-2.3-34 — ¿Como se controla lo que el estudiante ve desde el lado de GitHub para que no lo confunda con phishing: nombre, avatar y descripcion publica de la GitHub App, quien figura como invitador, a que correo llega la invitacion y el rastro visible del template y del commit inicial?

La invitacion de colaborador llega desde GitHub en ingles y con remitente del tipo <nombre-de-la-app>[bot], no el profesor, y lo mismo aparece en el audit log del repositorio; la invitacion va al correo asociado a la cuenta de GitHub y no al institucional; el repositorio muestra "generated from ORG/base" y el commit inicial queda firmado por la App. Decidir si se eligen nombre, avatar y descripcion de la App pensando en que los estudiantes los veran (por ejemplo "ICC4201 Repos") y si el mensaje de Canvas anticipa exactamente que correo recibiran y de quien. Verificar empiricamente con una cuenta de prueba el texto real, el remitente y el destinatario del correo de invitacion.

- **Requisitos:** R2.3.9, R2.3.12, R2.1.5
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Un estudiante que ignora la invitacion por desconfianza bloquea todo el flujo; el texto de R2.3.12 debe anticipar exactamente lo que vera y el naming de la App queda fijado antes de publicarla.
- **Opciones:**
  - Configurar nombre, avatar y descripcion de la App con marca del curso
  - Mensaje de Canvas que describe remitente, correo destino y aspecto del correo
  - Nada especial: se asume que el estudiante reconoce la invitacion
- **Estudio de APIs:** §5.4 explica 201/204 y que el estudiante "debe aceptar la invitacion por email"; §5.3 usa un committer "ICC4201 Bot"; no aborda como percibe el estudiante al remitente ni el naming de la App.
- **Fusiona:** P285, P309

### Q-2.3-35 — Mientras la invitacion no se acepta el estudiante no tiene acceso al repositorio privado: ¿que ve exactamente al abrir la URL del repositorio en cada situacion y que enlace canonico se le envia?

Verificar empiricamente que ve al abrir https://github.com/ORG/REPO estando invitado y con sesion iniciada en la cuenta correcta, invitado sin sesion iniciada, y con sesion iniciada en OTRA cuenta de GitHub: ¿aparece la pantalla de invitacion o un 404? A partir de eso decidir que enlace se envia por Canvas (la URL del repositorio, la URL de aceptacion /invitations, o ambos con el orden explicado), si el texto advierte que un 404 es esperable hasta aceptar y que hacer entonces, y que instruccion se da a quien acepto o intento aceptar con una cuenta distinta a la registrada (caso que deja el mapeo valido pero al estudiante sin acceso, y que puede requerir un estado o accion visible en R2.3.11).

- **Requisitos:** R2.3.12, R2.3.9, R2.3.11
- **Tipo:** verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Determina el texto y el enlace del mensaje que cierra el flujo de la demo del 16-sep y evita el ticket mas probable del estudiante ("mi repositorio no existe").
- **Opciones:**
  - Enviar solo la URL del repositorio y advertir del 404
  - Enviar la URL de aceptacion de la invitacion como enlace principal y la del repositorio como secundaria
  - Enviar dos mensajes: uno al invitar (aceptacion) y otro al detectar la aceptacion (URL del repositorio)
  - Agregar un estado visible para "invitado que abrio el enlace con otra cuenta"
- **Estudio de APIs:** §5.4 documenta 201 (invitacion pendiente) frente a 204 (acceso inmediato) y §5.7 el aviso por Canvas, pero no analiza que ve el estudiante al abrir la URL antes de aceptar ni que enlace conviene enviar.
- **Fusiona:** N019

## Aprovisionamiento automatico: predicado, disparadores y arquitectura del worker

### Q-2.3-36 — ¿Cual es el predicado cerrado de "toda la informacion requerida" (R2.3.10), puede el repositorio crearse ANTES de conocer el usuario de GitHub del estudiante, y como se interpreta y defiende el mandato de que la creacion "no debera depender de una accion realizada por los estudiantes"?

Decidir si se espera al mapeo validado (sin login no hay repositorio, con el nombre derivado del login); si el repositorio se crea apenas exista el sujeto en Canvas, con nombre derivado de identificadores estables (canvas_user_id / canvas_group_id + slug de tarea), aplicando el repositorio base y las protecciones y agregando colaboradores despues a medida que llegan los mapeos; o si es hibrido configurable por tarea. Consecuencias que deben decidirse para la opcion elegida: que componentes forman el nombre y si el repositorio se renombra al conocer el login; que estado y etiqueta muestra R2.3.11 para un repositorio que existe pero no tiene ningun colaborador; si ese repositorio cuenta como "listo" en el dashboard, en el informe diario y en la vista de faltantes (R2.2.6); cuando se dispara la notificacion al estudiante (al crear o al tener acceso); y que pasa con un repositorio creado para un estudiante que finalmente nunca entrega su usuario (¿se archiva, se elimina, queda vacio en la organizacion?). Para el sujeto grupal: si se espera a que todos los integrantes esten mapeados, si se crea con los disponibles y se agregan los demas progresivamente, si se crea tras un plazo aunque falten integrantes, y que se hace si un integrante tiene un login invalido de forma permanente (¿un solo estudiante puede bloquear a su grupo?). Y en el plano interpretativo: si "accion" se refiere solo al disparador de la creacion (el estudiante aporta un dato y el worker crea sin que nadie pulse nada), si debe existir ademas un camino sin accion del estudiante (mapeo precargado por el docente via CSV o reutilizado de un curso anterior) como requisito y no como extra, y si esa interpretacion se escribe como regla explicita en la especificacion para defenderla el 16-sep y el 7-oct.

- **Requisitos:** R2.3.10, R2.3.7, R2.3.8, R2.3.9, R2.2.4, R2.2.5, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es el predicado que ejecuta el worker y determina la plantilla de nombres (R2.3.8), la maquina de estados de R2.3.11, que se demuestra el 16-sep y si la creacion depende o no de un dato que solo aporta el estudiante; ademas prepara la respuesta a una objecion muy probable del evaluador.
- **Opciones:**
  - Esperar al mapeo validado (nombre con login de GitHub)
  - Crear el repositorio al detectar el sujeto en Canvas (nombre con identificadores de Canvas) y agregar colaboradores despues
  - Hibrido configurable por tarea
  - Grupos: esperar a todos los integrantes / crear con los disponibles / crear tras un plazo
  - Interpretar "accion" como disparador y documentarlo en el spec
  - Exigir un camino alternativo sin accion del estudiante (CSV, carga docente, mapeo de curso anterior)
- **Estudio de APIs:** El worker de aprovisionamiento (§5.5) condiciona la creacion a "¿tiene(n) github_login mapeado? no → state = PENDING_MAPPING; continue" y §5.6 muestra "Grupo 12: 2/3 mapeados" como pendiente, es decir, espera al mapeo de todos; las plantillas de nombres de §5.4 incluyen el login de GitHub. §6.1 recomienda la tarea de Canvas como formulario de registro. No evalua crear el repositorio antes del mapeo, su impacto en el nombre, ni la tension con el parrafo del enunciado.
- **Fusiona:** N003, P304, P257

### Q-2.3-37 — ¿Cual es el ciclo de vida y el estado de una tarea de la app: cuando empieza el aprovisionamiento, que significa "tarea activa" para los workers, se puede pausar, reanudar o cancelar, y cuando termina?

Decidir si el aprovisionamiento comienza inmediatamente al guardar la tarea, tras un paso explicito de activacion o confirmacion, al llegar el unlock_at del primer assignment o tras confirmar el repositorio base. Decidir si la tarea tiene una columna de estado explicita (por ejemplo DRAFT sin entregas → ACTIVE → CLOSED → ARCHIVED, mas PAUSED) que los workers usan como filtro, o si "activa" se deriva por predicado (tiene alguna entrega con fecha efectiva futura o dentro de N dias de correccion); que transiciones son automaticas por fechas y cuales manuales; y que worker (aprovisionamiento, snapshots, ingesta de commits, recordatorios, informe diario) consulta que estados. Un estado derivado no puede pausarse y uno manual puede quedar obsoleto: definir cual se elige o como se combinan. Definir tambien si el aprovisionamiento continua indefinidamente (un estudiante que se mapea despues del cierre de la entrega final recibe repositorio) o si existe un corte (tras la ultima fecha de cierre, al archivar la tarea) y que se le muestra a ese estudiante tardio; y si se puede pausar, reanudar o cancelar el aprovisionamiento, quien puede hacerlo (profesor, ayudante con permiso repo.provision) y si un repositorio en CREATING puede cancelarse.

- **Requisitos:** R2.3.10, R2.3.7, R2.3.11, R2.1.8, R2.5.6, R2.6.1, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es el filtro comun de todos los cron jobs; define si el profesor puede configurar la tarea sin que se creen repositorios a medias, si existe "pausar tarea" pese al automatismo exigido por R2.3.10, cuando deja de generarse el informe (R2.6.1) y cual es el estado terminal de la tarea.
- **Opciones:**
  - Columna de estado manual con transiciones explicitas
  - Estado derivado por fechas
  - Derivado + flag manual de pausa/archivo
  - Inicio inmediato al guardar / tras activacion explicita / al llegar unlock_at / tras confirmar el repositorio base
  - Corte del aprovisionamiento tras la ultima fecha de cierre / sin corte
- **Estudio de APIs:** §5.5 dice "para cada Assignment activo" y §9.1 "tareas activas" sin definir el campo ni las transiciones; §5.3 sugiere que el repositorio base exista antes de generar; §3.4 propone el permiso repo.provision ("disparar/reintentar creacion") pero no aborda pausar ni cancelar; el corte temporal no se aborda.
- **Fusiona:** P231, P232, P261, P324

### Q-2.3-38 — ¿Cual es el disparador, la cadencia, el orden y la latencia objetivo del worker de aprovisionamiento, y existe un boton de ejecucion manual?

Decidir: cron cada N minutos (¿cuantos?), evento inmediato al completarse un mapeo o un grupo, o ambos; que intervalos reales tendran los crons en produccion (aprovisionamiento, snapshots, sincronizacion con Canvas, reconciliacion) y cuales durante la demo del 16-sep (¿se acortan por variable de entorno para que el profesor vea el repositorio aparecer solo?); si se ofrece un boton "procesar ahora" o "ejecutar ahora" de respaldo sin violar el "sin interaccion directa de un usuario" de R2.3.10 y como se presenta para que no parezca que el proceso depende de un clic. Definir el criterio de aceptacion de latencia (repositorio creado y notificado en menos de X minutos tras completarse la informacion) y el tiempo total para un curso completo, considerando el throttle necesario por los limites secundarios de GitHub. Definir tambien si existe una cola global con throttle por instalacion, dado que varios cursos y tareas comparten la misma instalacion de la GitHub App, y en que orden se procesan los sujetos (FIFO por completitud de informacion, por tarea, por seccion, por proximidad de la fecha de cierre).

- **Requisitos:** R2.3.10, R2.4.4, R2.2.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija el criterio de aceptacion de R2.3.10, la frecuencia necesaria para una demo en vivo, el diseno de la cola y que repositorios aparecen primero tanto en la demo como en produccion.
- **Opciones:**
  - Cron periodico unicamente
  - Evento inmediato al completarse la informacion
  - Cron + evento inmediato
  - Con boton "procesar ahora" / sin boton
  - Cola global con throttle por instalacion / colas independientes por tarea
- **Estudio de APIs:** §5.5 propone cron cada 2 min y describe el worker por Assignment sin definir orden global; §2.4 indica throttle de aproximadamente 1 repositorio cada 3–5 s por limites secundarios (80 requests de creacion de contenido por minuto, 900 puntos por minuto) y limites por instalacion; §12 lista provision_repos cada 2 min junto a otros intervalos sugeridos (2/5/10/15 min, 07:00); §13 describe el guion de demo con "el worker crea los repos en vivo".
- **Fusiona:** P256, P260, P303

### Q-2.3-39 — ¿El worker de repositorios se disena como reconciliador declarativo o como acciones imperativas disparadas por eventos, y que diferencias entre estado deseado y observado se aplican automaticamente?

En el modelo declarativo, cada ciclo calcula el estado deseado por sujeto (repositorio existe, colaboradores = integrantes activos mapeados con permiso push, ayudantes con acceso de lectura), lo compara con lo observado en GitHub y aplica la diferencia; en el imperativo, cada evento dispara una accion (mapeo completado → agregar; integrante sale → quitar). Decidir ademas si Repository.state es una columna escrita por el worker o una vista derivada de los miembros y de la existencia del repositorio, y que diferencias se aplican solas y cuales quedan como "drift detectado, requiere confirmacion" (por ejemplo quitar colaboradores, o un colaborador agregado a mano por un owner de la organizacion).

- **Requisitos:** R2.3.9, R2.3.10, R2.3.11, R2.2.3, R2.1.9
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define la arquitectura completa del worker, su idempotencia, la reaccion a cambios de grupo y retiros, el costo en rate limit por ciclo y que se persiste frente a que se recalcula.
- **Opciones:**
  - Reconciliador declarativo
  - Acciones imperativas por evento
  - Hibrido: imperativo para crear, declarativo para colaboradores
- **Estudio de APIs:** §5.5 describe una funcion crear_repo imperativa con estados escritos por el worker; §8.2 aplica reconciliacion pero solo a commits.
- **Fusiona:** P321

### Q-2.3-40 — ¿Como se garantizan idempotencia, recuperacion ante caidas y control de concurrencia, y que campos quedan congelados una vez creado el primer repositorio?

Definir que ocurre si el worker cae a mitad (repositorio creado sin colaboradores, colaboradores sin notificacion): si la maquina de estados persiste por paso, si hay lock por sujeto con TTL y si puede haber varias instancias del worker. Definir tambien el control de concurrencia cuando dos profesores editan la misma tarea (uno cambia el repositorio base, otro agrega una entrega) o uno edita mientras el worker esta creando repositorios: bloqueo optimista con aviso de recarga, ultimo en guardar gana, o bloqueo de la edicion mientras hay jobs en curso. Y enumerar los campos inmutables una vez creado el primer repositorio (plantilla de nombre, tipo individual/grupal, repositorio base, organizacion).

- **Requisitos:** R2.3.7, R2.3.9, R2.3.10, R2.1.7, R2.3.1, R2.3.5, R2.3.8
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Evita repositorios duplicados, estados inconsistentes, notificaciones repetidas y configuraciones mezcladas; el estudio lo lista como pregunta probable en la validacion del 7-oct.
- **Opciones:**
  - Lock por sujeto con TTL y estado persistido por paso
  - Bloqueo optimista con aviso "la tarea cambio, recarga"
  - Ultimo en guardar gana
  - Bloquear la edicion mientras hay jobs en curso
  - Lista explicita de campos congelados tras el primer repositorio
- **Estudio de APIs:** §5.5 indica worker "idempotente, con lock por sujeto", 422 como exito y estados CREATING/CREATED/COLLABORATORS_PENDING/READY; §14 lo lista como pregunta probable. La concurrencia entre profesores no se aborda.
- **Fusiona:** P259, P297

### Q-2.3-41 — ¿Existe una entidad de miembro de repositorio con historial (RepositoryMember) o el estado de colaboradores se consulta a GitHub en cada reconciliacion sin persistirlo?

Campos candidatos: repository_id, student_id, github_login y github_id en el momento, permission, state (TO_INVITE / INVITED / ACCEPTED / REMOVED / FAILED), invitation_id de GitHub, invited_at, accepted_at, removed_at, removal_reason. Decidir si se guarda el invitation_id para revocar, reenviar y detectar expiracion o rechazo; si la fila se conserva como REMOVED al quitar a un retirado para saber quien tuvo acceso y cuando; y si la aceptacion de una invitacion en un repositorio eleva el estado del mapeo estudiante-GitHub a verificado para todo el curso.

- **Requisitos:** R2.3.9, R2.3.11, R2.2.6, R2.1.9, R2.2.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Sin esta entidad no hay sub-estado por integrante en R2.3.11 ni evidencia de accesos; con ella hay que definir su fuente de verdad frente a GitHub.
- **Opciones:**
  - Entidad persistida con historial de altas y bajas
  - Consulta en vivo a GitHub sin persistir
  - Persistir solo el estado vigente sin historial
- **Estudio de APIs:** §5.4 documenta GET /invitations (id, invitee, expired) y DELETE; §5.2 no tiene entidad de miembro, solo el estado agregado del repositorio.
- **Fusiona:** P322

### Q-2.3-42 — ¿Cual es la maquina de estados definitiva por repositorio (y el sub-estado por integrante), y cuales de esos estados son terminales?

Decidir si se adoptan los estados del estudio (PENDING_MAPPING, QUEUED, CREATING, CREATED, COLLABORATORS_PENDING, READY, ERROR) y si se agregan otros como PENDING_GROUP, NOTIFIED, ARCHIVED, ORPHANED, MEMBERSHIP_CHANGED, INVITATION_EXPIRED, INVITATION_REJECTED, SUPERSEDED o los sub-estados que surjan de las demas decisiones (repositorio sin colaboradores, bloqueado por autenticacion, drift detectado).

- **Requisitos:** R2.3.11, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es el contrato entre el worker, la vista de estado, el dashboard (R2.5.5) y el informe diario (R2.6.2); R2.3.11 exige mostrar claramente el estado sin enumerar cuales existen.
- **Opciones:**
  - Adoptar los estados base del estudio sin agregados
  - Ampliar el conjunto con los estados derivados de las demas decisiones
  - Estado agregado del repositorio + sub-estado por integrante
- **Estudio de APIs:** §5.2 y §5.5 proponen la lista de estados base; §5.6 muestra "Listo / Falta usuario / Invitacion sin aceptar / Error: usuario invalido".
- **Fusiona:** P264

### Q-2.3-43 — ¿Cual es la taxonomia de errores del aprovisionamiento, la politica de reintentos y las acciones manuales disponibles?

Definir el backoff (base y maximo), el numero maximo de intentos y la clasificacion de errores en transitorios (5xx, rate limit, timeout, fallo de red) frente a permanentes (404 usuario no existe, 403 de permisos, 422 de validacion), y cuando un repositorio pasa a "requiere intervencion humana". Definir que acciones manuales existen (reintentar, editar login y reintentar, vincular repositorio existente, marcar "gestionado fuera de la app", omitir estudiante) y quien puede ejecutarlas; y si los errores se clasifican como transitorios o definitivos en la vista de estado (R2.3.11) y en el informe diario.

- **Requisitos:** R2.3.10, R2.3.11, R2.5.5, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define las transiciones ERROR → QUEUED, evita martillar la API, determina que ve el profesor y convierte el estado ERROR en una taxonomia verificable en la demo con el caso problematico que sugiere el estudio.
- **Opciones:**
  - Reintentos automaticos con backoff y tope, luego ERROR hasta accion manual
  - Sin reintentos automaticos: ERROR inmediato con accion manual
  - Politica distinta segun clasificacion transitorio/permanente
- **Estudio de APIs:** §5.5 indica "cualquier excepcion → ERROR, reintento con backoff" sin parametros; §2.4 da un ejemplo con 5 intentos y retry-after; §5.6 propone un boton "reintentar todos los fallidos"; no cuantifica reintentos ni clasifica errores.
- **Fusiona:** P258, P300

## Visibilidad del estado, errores y usabilidad

### Q-2.3-44 — ¿Como es la vista de estado de repositorios: que columnas, filtros, busqueda, contadores, ordenacion, paginacion, exportacion y acciones masivas ofrece, como comunica el progreso y como se actualiza?

Definir filtros (solo problemas, seccion, estado, grupo), busqueda, contadores resumen (X/N listos), ordenacion y acciones masivas ("reintentar fallidos", "reenviar invitaciones"); si es el mismo componente que sirve a R2.2.6 (faltantes de informacion) y a R2.5.5 o son vistas distintas. Definir como se comunica el progreso del aprovisionamiento automatico (barra o contador en la cabecera de la tarea del tipo "7 de 10 repositorios listos, 2 esperando usuario GitHub, 1 con error", tiempo estimado, "proxima ejecucion en X s" o "procesando ahora") y si la tabla se actualiza en vivo (polling cada N segundos, SSE o WebSocket) o exige refrescar. Y para volumenes reales (200 estudiantes o 60 grupos): si las tablas paginan, filtran por seccion y estado y exportan a CSV, y cual es el tiempo maximo aceptable desde que un estudiante completa su mapeo hasta que su repositorio esta listo y notificado.

- **Requisitos:** R2.3.10, R2.3.11, R2.2.6, R2.5.1, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija el flujo de UI concreto que se demuestra el 16-sep, evita tres vistas inconsistentes, hace visible que "algo esta pasando" sin boton y convierte "progresivo y automatico" en criterios de aceptacion medibles.
- **Opciones:**
  - Un unico componente compartido por R2.3.11, R2.2.6 y R2.5.5
  - Vistas separadas por requisito
  - Polling del frontend cada 5–10 s mientras hay repositorios en curso
  - SSE/WebSocket con push de cambios
  - Refresco manual con indicador de ultima actualizacion
  - Con paginacion y exportacion CSV / sin ellas
- **Estudio de APIs:** §5.6 propone una tabla con columnas Estudiante/Seccion/GitHub user/Repo/Colaboradores/Estado/Accion, filtro "solo problemas" y "reintentar todos los fallidos"; §2.4 y §5.5 fijan un throttle de aproximadamente 1 repositorio cada 3–5 s; §13 habla de "tabla de estados pasando a verde" sin definir el mecanismo de actualizacion ni tiempos objetivo o paginacion.
- **Fusiona:** P266, P299, P314

### Q-2.3-45 — Los errores del worker ocurren cuando nadie esta mirando: ¿donde afloran dentro de la jerarquia de la interfaz y se pueden silenciar?

Definir si aparecen como columna de estado en la tabla de repositorios, banner en la cabecera de la tarea, badge en la tarjeta de la tarea dentro de la lista, badge en la tarjeta del curso en la pagina inicial, centro de notificaciones o informe diario; si un solo repositorio en error marca toda la tarea como "con problemas"; y si los errores se pueden descartar o silenciar una vez vistos.

- **Requisitos:** R2.3.10, R2.3.11, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define la propagacion de estados hacia arriba en la jerarquia y el componente de alertas; afecta directamente el "mostrar claramente" de R2.3.11 y la evaluacion de la demo con caso problematico.
- **Opciones:**
  - Solo en la tabla de repositorios
  - Propagacion a tarea y curso mediante badges
  - Centro de notificaciones ademas del informe diario
  - Errores silenciables / no silenciables
- **Estudio de APIs:** §5.5 define estados ERROR/PENDING_MAPPING/COLLABORATORS_PENDING con last_error y §9.1 los incluye en el informe diario; no define la propagacion visual.
- **Fusiona:** P313

### Q-2.3-46 — ¿Como se redactan los mensajes de error para el equipo docente y existe una bitacora de intentos por repositorio?

Definir si los mensajes van en espanol, si incluyen una accion sugerida por tipo de error y si muestran o no el texto crudo devuelto por GitHub y Canvas; y si se mantiene una bitacora por repositorio (timestamp, paso, error) visible para el equipo docente.

- **Requisitos:** R2.3.11
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define la usabilidad evaluada en la parcial y el nivel de trazabilidad disponible para la validacion individual del 7-oct.
- **Opciones:**
  - Mensaje en espanol con accion sugerida, sin texto crudo
  - Mensaje en espanol con detalle tecnico desplegable
  - Bitacora completa por repositorio / solo ultimo error
- **Estudio de APIs:** §5.2 guarda last_error y §5.6 muestra mensajes del tipo "Falta usuario de M. Soto"; no define bitacora.
- **Fusiona:** P265

### Q-2.3-47 — ¿Que se muestra en los estados vacios de las pantallas de 2.3?

Casos: tarea sin estudiantes mapeados; curso sin grupos; organizacion sin permisos suficientes (403 en la primera creacion); tarea recien creada antes del primer ciclo del worker ("proxima ejecucion en N s"); y primera sincronizacion del roster todavia en curso.

- **Requisitos:** R2.3.7, R2.3.10, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** La guia adecuada se evalua explicitamente en la parcial y los estados vacios son justamente donde el profesor no sabe que hacer.
- **Opciones:**
  - Mensaje explicativo con accion sugerida en cada estado vacio
  - Mensaje generico unico
  - Mostrar la tabla vacia sin explicacion
- **Estudio de APIs:** §4.4 sugiere mostrar last_synced_at y §3.3 un checklist de verificacion; no aborda los estados vacios de la tarea.
- **Fusiona:** P278

### Q-2.3-48 — Antes de guardar una tarea, ¿la app muestra un resumen de impacto que el profesor deba confirmar?

Por ejemplo: "se crearan N repositorios ahora, K estudiantes quedaran pendientes de usuario de GitHub, J estudiantes sin grupo, tipo individual/grupal detectado, organizacion destino X". Definir ademas que muestra ese resumen si la primera sincronizacion del roster aun no termino y si se advierte que los repositorios se crearan cuando lleguen los datos.

- **Requisitos:** R2.3.1, R2.3.3, R2.3.7, R2.3.10, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es el ultimo punto donde el profesor puede evitar crear decenas de repositorios equivocados, y los evaluadores de usabilidad lo notaran.
- **Opciones:**
  - Resumen de impacto con confirmacion obligatoria
  - Guardar directo y mostrar la tabla de estado
  - Resumen solo informativo sin confirmacion
- **Estudio de APIs:** §5.2 propone validar R2.3.3 al vincular y §5.6 la tabla de estado posterior; no aborda una vista previa de impacto antes de guardar.
- **Fusiona:** P308

### Q-2.3-49 — ¿Que roles pueden ejecutar cada accion del area 2.3 y que ve cada uno del repositorio base?

Definir que roles pueden crear y editar el repositorio base, subir archivos, forzar reintentos, reenviar invitaciones y borrar o archivar repositorios; y si los estudiantes deben poder ver el repositorio base (privado en la organizacion, sin acceso) o basta con que reciban su copia.

- **Requisitos:** R2.3.5, R2.3.6, R2.3.7, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Conecta los permisos que exige R2.1.8 (minimo tres, definidos por el equipo) con cada accion concreta de 2.3 y fija la visibilidad del repositorio base.
- **Opciones:**
  - Permisos separados assignment.manage y repo.provision
  - Un unico permiso para todo 2.3
  - Estudiantes sin acceso al repositorio base / con acceso de lectura
- **Estudio de APIs:** §3.4 propone assignment.manage (crear y editar tareas y repositorios base) y repo.provision (disparar y reintentar creacion); no aborda la visibilidad del base para estudiantes.
- **Fusiona:** P277

## Comunicacion con el estudiante a traves de Canvas

### Q-2.3-50 — ¿Por que canal de Canvas se informa el repositorio al estudiante, como se trata el caso grupal, y funciona ese canal antes de que exista una entrega?

Decidir entre comentario en la entrega (¿de cual entrega si hay varias?), mensaje directo (Conversation), anuncio, o varios canales combinados; y para grupos, si se usa una conversacion grupal, mensajes individuales o comment[group_comment]=true. Verificar antes: si Canvas permite PUT de comment[text_comment] sobre una submission cuando el estudiante aun no ha entregado nada (¿crea un placeholder?), si eso hace que la entrega aparezca como calificada o afecta el gradebook, si genera notificacion al estudiante y si funciona igual en assignments grupales.

- **Requisitos:** R2.3.12, R2.6.5
- **Tipo:** decision_equipo + verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define el endpoint, el permiso que necesita el token y como encuentra el estudiante la informacion; si el comentario falla en submissions inexistentes, ese canal no sirve para R2.3.12 al inicio de la tarea.
- **Opciones:**
  - Solo comentario en la entrega
  - Solo mensaje directo (Conversation)
  - Ambos
  - Anuncio general + mensaje individual
  - Conversacion grupal / mensajes individuales para tareas grupales
- **Estudio de APIs:** §5.7 recomienda usar ambos canales: comentario en la submission (comment[text_comment], group_comment=true) y Conversation individual (§9.3, group_conversation=false); no menciona el caso de submission inexistente.
- **Fusiona:** P267, P270

### Q-2.3-51 — ¿En que momento y en que orden recibe el estudiante las comunicaciones de acceso al repositorio, y hay recordatorios?

Hoy GitHub envia su correo de invitacion en cuanto la app hace PUT collaborators y el mensaje de Canvas llega despues, de modo que el estudiante ve primero un correo de GitHub sin contexto. Decidir si se envia un mensaje de Canvas de pre-aviso ANTES de invitar ("en los proximos minutos recibiras una invitacion de la organizacion X a tu correo de GitHub"), si se invita y avisa en la misma transaccion, o si se acepta el orden actual; y, en el modelo de miembros de la organizacion, si el mensaje explica las dos aceptaciones (organizacion y repositorio) y en que orden. Decidir tambien si la notificacion se envia al crear el repositorio (con invitacion aun pendiente), al confirmar el acceso (READY) o en ambos momentos, y si se envian recordatorios automaticos cuando el estudiante no acepta en X dias y cuantos. Y si el assignment tiene unlock_at futuro o esta en un modulo bloqueado por prerrequisitos: si la app igual envia "repositorio disponible" o retiene el mensaje hasta el desbloqueo, si un comentario en la submission de un assignment bloqueado es visible para el estudiante, y si se le da acceso al repositorio (invitacion) antes de que la tarea sea visible.

- **Requisitos:** R2.3.9, R2.3.12, R2.4.1, R2.6.7
- **Tipo:** decision_equipo + verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Reordena los pasos del worker y el contenido del mensaje de R2.3.12 para reducir invitaciones ignoradas, define los eventos que disparan el outbox y evita mensajes prematuros que apuntan a una tarea que el estudiante todavia no puede abrir.
- **Opciones:**
  - Pre-aviso por Canvas antes de invitar
  - Invitar y avisar en la misma transaccion
  - Aceptar el orden actual (correo de GitHub primero)
  - Notificar al crear el repositorio / al confirmar acceso / en ambos momentos
  - Retener la comunicacion hasta unlock_at
  - Retener tambien la invitacion de GitHub hasta unlock_at
  - Con recordatorios automaticos / sin recordatorios
- **Estudio de APIs:** §5.5 fija el orden crear repositorio → agregar colaboradores → notificar por Canvas (paso 6) y §6.4 describe la invitacion a la organizacion, sin considerar avisar antes de invitar; §9.4 propone el flag notify_repo_ready y recordatorios por outbox; §5.1 dice "no creen repos para tareas no publicadas" pero no trata unlock_at ni modulos bloqueados.
- **Fusiona:** P217, P268, P284

### Q-2.3-52 — ¿Cual es el contenido exacto de "la informacion necesaria para acceder al repositorio" (R2.3.12), incluido el tramo de autenticacion con Git, donde vive esa informacion y como distingue la app a un estudiante bloqueado por autenticacion de uno que no ha participado?

Aceptar la invitacion no basta para trabajar: GitHub no acepta contrasena para push por HTTPS (exige token personal, credential manager, GitHub Desktop o gh CLI) y por SSH exige una clave registrada (y autorizada por SSO si la organizacion lo requiere), ademas de la 2FA obligatoria en cuentas nuevas. Decidir: que URL de clonado se muestra (HTTPS, SSH o ambas) y si se incluyen los comandos exactos (git clone, git remote, primer push); si el mensaje incluye ademas la URL del repositorio, instrucciones para aceptar la invitacion, la rama que se evalua, las fechas de las entregas y un contacto; donde viven las instrucciones (mensaje de Canvas, README generado en cada repositorio, pagina o modulo unico de Canvas del curso, descripcion de la tarea); que se ofrece a quien nunca uso Git (guia paso a paso, video, o se asume conocido del ramo); si la organizacion exige 2FA y el mensaje advierte que debe activarse ANTES de aceptar la invitacion; si el texto es una plantilla editable por el profesor por tarea y si el idioma es fijo espanol; o si el tramo de autenticacion se declara fuera de alcance remitiendo a la documentacion oficial de GitHub o a una guia que redacte el equipo docente (definiendo quien la redacta y cuando). Decidir tambien el criterio de aceptacion ("el estudiante puede efectivamente clonar y pushear", no solo "tiene acceso") y si se probara el primer push con una cuenta de GitHub recien creada, ajena al equipo, contra un repositorio privado de la organizacion elegida para conocer el error exacto que vera el estudiante. Y del lado del monitoreo: si la app distingue al estudiante con invitacion aceptada y 0 commits del que probablemente esta bloqueado por autenticacion (por ejemplo acepto hace N dias y nunca hizo un push), si muestra ese sub-estado en la vista de faltantes y de estado de repositorios, y si ofrece un canal para que el docente lo detecte antes de marcarlo "sin participacion".

- **Requisitos:** R2.3.12, R2.3.9, R2.3.11, R2.2.5, R2.2.6, R2.5.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija el contenido y la plantilla del mensaje de R2.3.12 y un criterio de aceptacion de usabilidad del enrolamiento; si el estudiante no logra autenticarse, el repositorio existe pero no hay trabajo y la app solo ve "sin commits", indistinguible de "no trabajo" (R2.5.4), lo que alimenta el informe diario y puede afectar su evaluacion.
- **Opciones:**
  - Solo URL HTTPS y se asume que el estudiante resuelve la autenticacion
  - URL HTTPS y SSH + explicacion del metodo de autenticacion en el mensaje de Canvas
  - README generado en cada repositorio con los comandos exactos y enlaces a la documentacion oficial
  - Pagina o modulo unico de Canvas enlazado desde cada mensaje
  - Recomendar explicitamente GitHub Desktop / VS Code para evitar el problema de credenciales
  - Remitir a documentacion oficial de GitHub sin material propio
  - Guia redactada por el equipo docente y solo enlazada por la app
  - Declararlo fuera de alcance en el spec (no-objetivo)
  - Plantilla editable por el profesor por tarea / texto fijo del sistema
  - Agregar sub-estado "probablemente bloqueado por autenticacion" y alerta al docente
- **Estudio de APIs:** §5.7 propone el texto "Tu repositorio: <url> (revisa tu correo para aceptar la invitacion)" y §9.3 da ejemplos de mensajes; §5.4 fija el permiso push. El estudio se detiene en la invitacion y la URL del repositorio (§5.4, §5.7, §6.4) y su seccion de autenticacion (§2) trata solo la autenticacion de la app (GitHub App/JWT/installation token), no la del estudiante contra git; tampoco aborda plantillas editables, la politica de 2FA de la organizacion ni un sub-estado de bloqueo.
- **Fusiona:** P269, N001, N018

### Q-2.3-53 — ¿Donde y como se le comunica al estudiante el "reglamento tecnico" del repositorio y la transparencia del monitoreo, y escribe la app commits en los repositorios de los estudiantes?

Contenido a comunicar: rama que se evalua, prohibicion o no de trabajar en forks, tags reservados (entrega-N), criterio exacto de cierre (fecha del commit frente a hora del push), el hecho de que su actividad de commits se registra y se usa para evaluar participacion individual (R2.5.4/R2.5.8) y como confirmar cual es su version registrada. Ubicaciones posibles: README generado por la app en cada repositorio (¿tambien cuando no hay repositorio base, en lugar del README vacio de auto_init?), descripcion de la tarea de Canvas, anuncio al inicio del curso, mensaje de "repositorio disponible". Decidir si la app hara commits automaticos en repositorios de estudiantes (README, archivo con las fechas de entregas actualizadas), aceptando que apareceran en su historial y deben excluirse de las metricas; y si se enviara a los grupos un resumen periodico de participacion para que se autorregulen.

- **Requisitos:** R2.3.7, R2.3.12, R2.5.4, R2.5.8, R2.4.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define el contenido inicial de cada repositorio, si la app escribe en repositorios de estudiantes y el aviso etico de monitoreo que el equipo debera defender el 7-oct.
- **Opciones:**
  - README generado por la app en todo repositorio
  - Solo descripcion de la tarea de Canvas
  - Anuncio unico al inicio del curso
  - Sin commits de la app en repositorios de estudiantes
  - Resumen periodico de participacion a los grupos
- **Estudio de APIs:** §5.3/§5.4 usan auto_init (README vacio con el nombre del repositorio) o template; §8.4/§8.5 describen atribucion y metricas de participacion; no aborda informar al estudiante del monitoreo ni commits de la app en repositorios de estudiantes.
- **Fusiona:** P211

### Q-2.3-54 — ¿Que artefactos de Canvas visibles para el estudiante puede crear o EDITAR la app, ademas de la tarea de registro, los mensajes y los anuncios?

Decidir: si edita la descripcion de cada assignment vinculado como entrega para insertar un bloque generado ("esta entrega se evalua desde tu repositorio de GitHub; no subas archivos aqui; se registrara el ultimo commit de la rama X antes de tu fecha de cierre") con actualizacion automatica si cambian fechas o repositorio; si crea una Pagina o Modulo "Como trabajar con GitHub en este curso"; si crea eventos de calendario; o si solo crea la tarea de registro. Si edita descripciones: si pide confirmacion al profesor, si marca el bloque con delimitadores para no pisar el texto del profesor y que ocurre si el profesor lo borra. Decidir ademas si la app permite CREAR desde ella la tarea de Canvas de una entrega (nombre, fechas, tipo none/on_paper, grupal con group set, publicada) y editar sus fechas como conveniencia cuando el curso aun no tiene tareas; si en ese caso se advierte que Canvas enviara notificaciones nativas a todos los estudiantes al publicar y al cambiar fechas; con que token e identidad se crearia; y que se muestra cuando el selector de tareas de Canvas esta vacio.

- **Requisitos:** R2.3.1, R2.3.12, R2.4.1, R2.6.6, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Determina si el estudiante encuentra las instrucciones donde mira (la tarea de Canvas de la entrega) o solo en mensajes, fija el alcance de escritura en Canvas, los endpoints y scopes que necesita el token, el checklist de R2.1.6 y el estado vacio del flujo de creacion de tarea.
- **Opciones:**
  - Editar la descripcion de cada entrega con un bloque delimitado
  - Crear Pagina o Modulo informativo
  - Crear eventos de calendario
  - Solo tarea de registro + mensajes y anuncios
  - Dejar toda la redaccion al profesor con una plantilla sugerida copiable
  - Solo vincular assignments existentes (lectura literal de R2.3.1)
  - Crear assignments desde la app con advertencia de notificaciones nativas
  - Crear y ademas editar fechas y overrides
- **Estudio de APIs:** §5.1 lista POST/PUT de assignments como endpoints disponibles pero no propone editar descripciones ni crear tareas de entrega; §6.1 solo crea la tarea de registro; no aborda paginas, modulos ni calendario.
- **Fusiona:** P209, P311

### Q-2.3-55 — ¿Como se renderizan para el estudiante los textos que la app envia por Canvas y que reglas de redaccion se derivan de ello?

Verificar contra la instancia real: si el body de POST /conversations acepta HTML o solo texto plano y si las URLs se convierten en enlaces clicables en la web y en la app movil de Canvas; lo mismo para comment[text_comment] en submissions; limites de longitud del body y del subject; y si se conservan los saltos de linea. Fijar las reglas de redaccion derivadas: fechas siempre absolutas con zona horaria (no "quedan 48 h", que puede llegar tarde por cola o throttling), URL completa del repositorio y de la invitacion, y que campo de nombre de Canvas se usa para saludar (name, short_name, sortable_name).

- **Requisitos:** R2.3.12, R2.6.5, R2.7.6
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Si el body es texto plano, las plantillas no pueden usar HTML ni enlaces con texto; los limites acotan el contenido de R2.3.12 y el saludo y el formato de fecha fijan la plantilla base de todos los mensajes.
- **Opciones:**
  - Plantillas en texto plano con URLs completas
  - Plantillas en HTML donde el canal lo permita
  - Plantilla unica para todos los canales / plantilla por canal
- **Estudio de APIs:** §9.3 muestra el body de conversations como texto plano con una URL incrustada e indica que subject admite maximo 255 caracteres; §9.2 senala que el message de anuncios acepta HTML; no aclara si el body de conversations o text_comment aceptan HTML ni si los enlaces se vuelven clicables.
- **Fusiona:** P210

### Q-2.3-56 — ¿Como se garantizan reintentos, idempotencia y deduplicacion de las comunicaciones, y que se hace cuando el destinatario ya no es valido o Canvas falla?

Definir la clave unica del outbox por evento, repositorio y estudiante; que ocurre si el token del profesor esta expirado en la madrugada; cuantos reintentos se hacen si Canvas responde error o el throttling bloquea el envio (de un mensaje de repositorio disponible, un recordatorio o la publicacion de una nota), si se descarta el envio, si se marca en el historial de comunicaciones y si se alerta al docente; que se hace si el estudiante ya no esta inscrito; y si se evita reenviar "repositorio disponible" cuando el repositorio se recrea o renombra, se re-invita al estudiante o se corrige un mapeo.

- **Requisitos:** R2.3.12, R2.6.5, R2.6.7, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Evita mensajes duplicados o perdidos, define que eventos generan comunicacion y las claves de deduplicacion para no spamear a los estudiantes.
- **Opciones:**
  - Outbox con clave unica por evento y reintentos con backoff
  - Reintento limitado y descarte con registro visible
  - Alerta al docente ante destinatario invalido
  - Re-notificar en cada recreacion / nunca re-notificar el mismo evento
- **Estudio de APIs:** §9.4 propone notification_outbox con constraint unico (kind, target, delivery_id) y un worker con reintentos; §1.1 destaca guardar el refresh_token; no define politica ante destinatario invalido ni eventos repetidos por recreacion.
- **Fusiona:** P271, P301

### Q-2.3-57 — El toggle por tarea para desactivar comunicaciones automaticas (R2.6.7), ¿alcanza tambien a la notificacion de creacion de repositorio exigida por R2.3.12?

Si el profesor la desactiva, definir como se cumple R2.3.12 (envio manual, exclusion de esta notificacion del toggle) y cual es el valor por defecto del flag.

- **Requisitos:** R2.3.12, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Resuelve una tension explicita entre dos requisitos del enunciado y fija el valor por defecto del flag.
- **Opciones:**
  - El toggle no alcanza a la notificacion de R2.3.12 (siempre se envia)
  - El toggle la alcanza y se ofrece envio manual como alternativa
  - El toggle la alcanza y se advierte del incumplimiento al desactivarla
- **Estudio de APIs:** §9.4 lista el flag notify_repo_ready sin definir su valor por defecto ni su relacion con R2.3.12.
- **Fusiona:** P272

### Q-2.3-58 — ¿Con que token de Canvas se envian las notificaciones al estudiante y quien figura como remitente?

Decidir si se usa siempre el del profesor que vinculo el curso (que aparecera como remitente), el de otro profesor si el primero expiro, o el del ayudante que ejecuta la accion; y si la app muestra quien figura como remitente.

- **Requisitos:** R2.3.12, R2.6.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Determina el remitente que ve el estudiante y el comportamiento de respaldo cuando un token no esta disponible.
- **Opciones:**
  - Token del profesor que vinculo el curso, con fallback a otro profesor
  - Token del usuario que ejecuta la accion
  - Mostrar en la UI quien figura como remitente / no mostrarlo
- **Estudio de APIs:** §3.4 recomienda la opcion A (token del profesor para todas las escrituras) con B como fallback y mostrarlo en la interfaz.
- **Fusiona:** P273

### Q-2.3-59 — Cuando el repositorio de un estudiante no puede crearse por causas NO atribuibles a el, ¿que recibe el estudiante y cuando, y que canal de respaldo existe si Canvas no responde?

Causas: repositorio en ERROR por permisos o limites de la organizacion, token de Canvas roto que impide notificar, cola detenida. Decidir entre silencio hasta que se resuelva, mensaje automatico tras N horas en ERROR, o decision docente caso a caso desde la vista de estado. Definir tambien que se le informa al estudiante cuyo atraso es propio (repositorio creado despues del cierre de la entrega 1: que esa entrega quedo sin version y a quien contactar), y si existe un canal manual de respaldo (exportar la lista de estudiantes con la URL de su repositorio para que el profesor la comunique) cuando el token de Canvas esta roto.

- **Requisitos:** R2.3.11, R2.3.12, R2.6.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define plantillas y disparadores de mensajes por fallas internas y un plan de contingencia de comunicacion cuando Canvas no responde.
- **Opciones:**
  - Silencio hasta resolver
  - Aviso automatico tras N horas en ERROR
  - Decision docente caso a caso
  - Exportacion para comunicacion manual
- **Estudio de APIs:** §5.5 define el estado ERROR con reintentos y §9.4 el outbox; no aborda que se le dice al estudiante ante fallas del sistema.
- **Fusiona:** P213

## Cambios, casos borde y recuperacion

### Q-2.3-60 — Si un assignment vinculado es eliminado o despublicado en Canvas, o el curso se concluye o se elimina, ¿que estado toman la entrega y la tarea, que procesos se detienen y como se entera el profesor?

Decidir si la entrega se marca "huerfana", se elimina de la tarea o se congela con sus snapshots; si se detienen el aprovisionamiento, el snapshot pendiente, el dashboard, las notificaciones y el informe diario; si se conservan los repositorios; que ve el corrector que la tenia asignada; como se muestra en la interfaz (badge "eliminada en Canvas" en la entrega, aviso en la tarea, bloqueo del snapshot); si se notifica al docente; si se permite desvincular esa entrega y vincular otro assignment conservando los repositorios; y que ocurre con los snapshots ya capturados de esa entrega.

- **Requisitos:** R2.3.1, R2.3.10, R2.3.11, R2.4.4, R2.4.5, R2.5.6, R2.6.1, R2.7.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Sin regla, la sincronizacion fallara silenciosamente con 404 y el worker puede seguir creando repositorios para una entrega inexistente; determina los estados terminales de entrega y curso, cuando dejan de correr los cron jobs y que se conserva como historico.
- **Opciones:**
  - Marcar la entrega como huerfana y congelarla con sus snapshots
  - Eliminar la entrega de la tarea conservando el historico
  - Detener solo los procesos futuros y conservar todo lo capturado
  - Permitir re-vincular otro assignment a la misma entrega
- **Estudio de APIs:** §5.1 solo dice "no creen repos para tareas no publicadas"; §4.4 indica "nunca borren filas al sincronizar"; §7.4 cubre cambios de fecha por polling pero no la eliminacion del assignment ni la conclusion del curso.
- **Fusiona:** P228, P287, P316

### Q-2.3-61 — ¿Se pueden agregar o quitar entregas de una tarea despues de creada, incluso con repositorios, snapshots, asignaciones de corrector o notas ya existentes?

Decidir si se puede agregar una entrega (nueva tarea de Canvas) a una tarea con repositorios ya creados y si se puede desvincular una existente; si al quitar una entrega con snapshot registrado se conservan el snapshot y el tag o se eliminan; que ocurre con asignaciones de corrector y notas publicadas (conservar como historico, ocultar o eliminar); si se pueden re-vincular despues conservando lo anterior; y si se puede cambiar el assignment de Canvas asociado a una entrega existente.

- **Requisitos:** R2.3.1, R2.3.2, R2.3.4, R2.4.6, R2.4.7, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija las reglas de edicion del ciclo de vida de la tarea, que transiciones quedan bloqueadas, la mutabilidad de la relacion tarea-entregas y el destino de los datos derivados, protegiendo la evidencia exigida por R2.4.7.
- **Opciones:**
  - Permitir agregar y quitar entregas mientras no existan snapshots
  - Permitir siempre, conservando los datos derivados como historico
  - Bloquear cualquier cambio tras el primer snapshot
  - Permitir cambiar el assignment asociado a una entrega / prohibirlo
- **Estudio de APIs:** §5.2 describe la estructura Assignment→Delivery y valida la consistencia al vincular; no aborda desvincular ni agregar entregas despues de iniciada la tarea.
- **Fusiona:** P222, P295

### Q-2.3-62 — Si al crear la tarea o agregar una entrega la fecha efectiva de esa entrega ya paso, ¿que hace la app?

Decidir si se captura el snapshot de inmediato para los repositorios existentes; que ocurre con los repositorios que se creen despues (todo su trabajo seria posterior al cierre); si se suprimen las notificaciones de "proximo a vencer" y de "repositorio disponible"; y si se advierte al profesor antes de confirmar la vinculacion.

- **Requisitos:** R2.3.1, R2.4.5, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define validaciones del wizard de tarea y guardas del outbox de notificaciones para no enviar mensajes absurdos ni capturar versiones sin sentido.
- **Opciones:**
  - Capturar snapshot inmediato y advertir al profesor
  - Bloquear la vinculacion de entregas ya vencidas
  - Permitir sin snapshot y marcar la entrega como no capturable
- **Estudio de APIs:** §7.5 indica que el job barre todo lo vencido no capturado, lo que implica captura inmediata; no aborda la advertencia en la interfaz ni las notificaciones.
- **Fusiona:** P288

### Q-2.3-63 — Cuando la membresia de un grupo cambia en Canvas despues de creado el repositorio, ¿la app agrega y quita colaboradores automaticamente?

Casos: un estudiante sale, entra o se cambia de grupo; un grupo se elimina o se fusiona. Decidir si el estudiante que se cambia de grupo pierde acceso al repositorio anterior y gana acceso al nuevo, si se conserva el historial, y si existe un congelamiento de grupos a partir de cierta fecha (por ejemplo el primer due_at).

- **Requisitos:** R2.3.9, R2.3.4, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina la sincronizacion continua entre grupos de Canvas y colaboradores de GitHub y los estados de cambio de membresia visibles en R2.3.11.
- **Opciones:**
  - Sincronizacion automatica en ambos sentidos (agregar y quitar)
  - Solo agregar, nunca quitar, mostrando alerta
  - Congelar la membresia al primer cierre y requerir accion manual
- **Estudio de APIs:** §4.4 recomienda marcar como retirado sin borrar; no aborda la remocion ni la adicion de colaboradores por cambio de grupo.
- **Fusiona:** P227

### Q-2.3-64 — Cuando un estudiante se retira del curso o su enrollment no esta activo (deleted, inactive, completed, invited) o es el Test Student, ¿que se hace con su repositorio y su acceso?

Decidir si se le quita acceso, si se archiva su repositorio individual, si en un repositorio grupal se le remueve solo a el, si se excluye del aprovisionamiento y que estado se muestra.

- **Requisitos:** R2.3.9, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define las reglas de exclusion de sujetos y de revocacion de acceso sin destruir historia ni evidencia.
- **Opciones:**
  - Excluir del aprovisionamiento y revocar acceso
  - Excluir del aprovisionamiento conservando el acceso
  - Marcar como retirado sin tocar el repositorio ni el acceso
  - Archivar el repositorio individual
- **Estudio de APIs:** §4.1 y §14 indican filtrar al Test Student y no incluir estados no activos, y §14 anade "No borren su repo ni su historia; marquenlos", sin definir la revocacion de acceso.
- **Fusiona:** P250

### Q-2.3-65 — Si se corrige un mapeo Canvas-GitHub erroneo despues de creado el repositorio (otro usuario recibio acceso), ¿que hace la app?

Decidir si se remueve al colaborador anterior, si se renombra o se recrea el repositorio individual, y que se hace con los commits del usuario equivocado.

- **Requisitos:** R2.3.9, R2.3.8, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Es un caso plausible en la demo y en el uso real; define las transiciones de correccion, la seguridad del acceso y el destino del trabajo ya subido.
- **Opciones:**
  - Remover al colaborador anterior y conservar el repositorio y su historia
  - Recrear el repositorio y marcar el anterior como SUPERSEDED
  - Renombrar el repositorio al nuevo login
  - Requerir confirmacion docente en cada correccion
- **Estudio de APIs:** No lo aborda; §6 cubre solo la validacion inicial del login.
- **Fusiona:** P251

### Q-2.3-66 — ¿Que hace la app cuando el login de GitHub mapeado deja de ser valido: no existe, fue renombrado, es una organizacion, esta suspendido, bloqueo a la organizacion, o la cuenta se elimino despues de aceptar la invitacion?

Verificar que devuelve PUT /collaborators en cada caso (404/403/422) y como aparecen en la API y en los payloads los commits de una cuenta eliminada (atribucion "ghost", desaparicion de /collaborators). Definir que estado y mensaje muestra la app en cada caso, si el worker revalida GET /users/{login} antes de invitar, si existe una revalidacion periodica por id, si se vuelve a solicitar el usuario por Canvas automaticamente y si se conserva la atribucion historica de sus commits por id o email.

- **Requisitos:** R2.3.9, R2.3.11, R2.5.4
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** si
- **Por que importa:** Define los subtipos de ERROR permanente; sin deteccion el estudiante aparece como "sin participacion" o como "listo" indefinidamente y pierde acceso sin que nadie lo note.
- **Opciones:**
  - Revalidacion periodica + estado especifico + nueva solicitud automatica del usuario
  - Solo deteccion al fallar una operacion
  - No detectar
- **Estudio de APIs:** §6.1 valida type == "User" al mapear y §5.6 muestra "Error: usuario invalido"; §8.4 cubre casos de atribucion sin login; no cubre cambios posteriores del login ni cuentas eliminadas o suspendidas tras aceptar la invitacion.
- **Fusiona:** P275, P310

### Q-2.3-67 — ¿La app audita y reconcilia periodicamente quien tiene acceso a cada repositorio y si la configuracion derivo, y que hace ante un acceso indebido o una remocion hecha a mano en GitHub?

Casos: colaborador inesperado agregado por un owner de la organizacion o por un mapeo erroneo ya aceptado; repositorio vuelto publico; rama por defecto renombrada; forks existentes; estudiante removido como colaborador o salido de la organizacion despues de que el repositorio estaba READY. Decidir si la app reconcilia periodicamente y re-invita automaticamente, solo alerta al docente, o no lo detecta; con que frecuencia y a que costo de rate limit para 200 repositorios; y ante un acceso indebido detectado (un desconocido acepto la invitacion de un login mal registrado), si se revoca automaticamente, se alerta al docente, se informa a los integrantes del grupo que su codigo pudo ser visto y se registra el incidente.

- **Requisitos:** R2.3.9, R2.3.11, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si READY es un estado "una vez" o "continuo", un job de reconciliacion de accesos, nuevos estados en R2.3.11 (acceso inesperado, visibilidad alterada) y un procedimiento de incidente de privacidad.
- **Opciones:**
  - Reconciliacion automatica con revocacion y re-invitacion
  - Solo alerta al docente
  - Sin auditoria (fuera de alcance)
- **Estudio de APIs:** §5.4 lista GET /collaborators e /invitations y §8.1 los eventos member/member_invite y repository; no aborda accesos no esperados, cambios de visibilidad, reconciliacion de colaboradores ni incidentes.
- **Fusiona:** P216, P293

### Q-2.3-68 — Si un repositorio (base o de estudiante) es eliminado, renombrado, transferido o archivado directamente en GitHub, ¿la app lo detecta y que hace?

Decidir si se detecta por webhook repository o por 404 en la reconciliacion; y si se marca como huerfano y se pide decision, se recrea automaticamente (perdiendo historia), o se sigue el renombre actualizando full_name mediante github_repo_id. Definir tambien si los snapshots ya capturados se marcan como irrecuperables y como se muestra al docente.

- **Requisitos:** R2.3.4, R2.3.5, R2.3.7, R2.3.11, R2.4.7, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** El worker idempotente recrearia el repositorio silenciosamente; hay que decidir si eso es deseable, evitar bucles de recreacion y definir el estado correspondiente en la maquina de estados.
- **Opciones:**
  - Marcar ORPHANED y requerir accion manual
  - Recrear automaticamente
  - Seguir por github_repo_id y actualizar el nombre
  - Marcar los snapshots afectados como irrecuperables
- **Estudio de APIs:** §5.2 guarda github_repo_id, lo que permitiria seguir renombres, y §8.1 lista el evento repository entre los webhooks a suscribir; no define el comportamiento ante deleted/renamed/transferred.
- **Fusiona:** P240, P290

### Q-2.3-69 — ¿Se puede eliminar desde la app un repositorio creado por error (mapeo equivocado, prueba), con que salvaguardas, o la app nunca borra?

Decidir si el borrado se permite solo cuando no hay commits, con confirmacion y liberando el nombre para recrear; o si la app solo desvincula o archiva y el borrado se hace directamente en GitHub.

- **Requisitos:** R2.3.7, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si la GitHub App necesita permiso de borrado y las salvaguardas contra la perdida del trabajo de un estudiante.
- **Opciones:**
  - Borrado desde la app solo si el repositorio no tiene commits, con confirmacion
  - Borrado siempre disponible con doble confirmacion
  - La app nunca borra: solo desvincula o archiva
- **Estudio de APIs:** §3.3 usa DELETE /repos solo para el repositorio temporal de verificacion; no aborda el borrado de repositorios de estudiantes.
- **Fusiona:** P262

### Q-2.3-70 — ¿Que ocurre si el reenvio automatico de una invitacion (DELETE + PUT) coincide con el momento en que el estudiante la esta aceptando?

Verificar que ve el estudiante si el job revoca justo cuando hace clic ("invitacion invalida") y como se evita: comprobando GET /collaborators e /invitations inmediatamente antes de revocar, o no reenviando dentro de una ventana de gracia tras el ultimo recordatorio. Verificar tambien si el enlace de la invitacion antigua que quedo en el correo del estudiante sigue funcionando tras el reenvio o queda muerto, y si el nuevo mensaje de Canvas le advierte que use el enlace mas reciente.

- **Requisitos:** R2.3.9, R2.3.11
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita dejar al estudiante bloqueado por una accion del propio sistema y fija el orden de comprobaciones del job de reenvio.
- **Opciones:**
  - Verificar el estado inmediatamente antes de revocar
  - Ventana de gracia sin reenvios tras el ultimo recordatorio
  - Reenvio solo manual para eliminar la carrera
- **Estudio de APIs:** §5.4 menciona DELETE .../invitations/{id} como "util para reenviar"; no aborda la concurrencia con la aceptacion ni la validez del enlace antiguo.
- **Fusiona:** P212

### Q-2.3-71 — Cuando la app REVOCA el acceso de alguien a un repositorio, ¿se le comunica algo, por que canal, con cuanta anticipacion y queda auditado?

Casos: estudiante retirado del curso, integrante que sale de un grupo, mapeo erroneo corregido, o un tercero ajeno al curso que fue invitado por un typo del estudiante y ya acepto. Decidir si hay aviso previo con plazo para que el estudiante clone o copie su trabajo, aviso posterior, o revocacion silenciosa; que canal se usa para quien ya no esta inscrito en Canvas (Conversation puede fallar) y si existe un texto para el tercero ajeno, que no es alcanzable por Canvas y solo vera desaparecer el repositorio; si la revocacion es automatica o requiere confirmacion docente en cada caso; y si queda registrado quien tuvo acceso, entre que fechas y por que se revoco.

- **Requisitos:** R2.3.9, R2.2.4, R2.6.5, R2.1.9
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Convierte en regla explicita un efecto irreversible sobre una persona (perdida de acceso a su propio codigo) hoy definido solo desde el lado tecnico; afecta el flujo de retiro, el de correccion de mapeos y el texto de las comunicaciones.
- **Opciones:**
  - Revocacion silenciosa e inmediata
  - Aviso previo por Canvas con N dias de gracia antes de revocar
  - Revocacion inmediata + mensaje explicativo posterior
  - Solo tras confirmacion explicita del profesor, caso a caso
- **Estudio de APIs:** §3.4 menciona DELETE /orgs/{org}/memberships/{username} al retirar a un ayudante y §6.1 la validacion del login para evitar mapeos erroneos, pero el estudio no aborda ninguna comunicacion hacia el afectado cuando se le quita acceso a un repositorio.
- **Fusiona:** N027

### Q-2.3-72 — ¿Se define una regla de equidad por "tiempo de exposicion" del repositorio, es decir, por cuanto tiempo real tuvo el estudiante su repositorio antes de la fecha efectiva de cierre?

Un estudiante cuyo mapeo se completa tarde, o cuyo repositorio quedo en ERROR varios dias, puede recibirlo dos dias antes del cierre mientras sus companeros lo tuvieron tres semanas. Decidir: si la app calcula y muestra ese tiempo por sujeto (desde repositorio accesible hasta fecha efectiva de cierre); si por debajo de un umbral configurable genera una alerta en la vista de estado, en el informe diario (R2.6.2) y una marca visible para el corrector (R2.7.7); si el equipo docente puede registrar en la app la decision tomada (extension otorgada en Canvas, excusar la entrega, nada) y queda auditada; y si la app puede ademas crear el override de extension en Canvas o solo recomendarlo.

- **Requisitos:** R2.3.10, R2.4.3, R2.6.2, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es el caso en que el propio sistema perjudica al estudiante y hoy no queda registrado en ninguna parte: sin la senal, la entrega se corrige como cualquier otra. Define un dato derivado, una alerta y una columna de la vista de correccion.
- **Opciones:**
  - No se mide: la fecha es la fecha
  - Se mide y se alerta, pero la decision es humana y externa a la app
  - Se mide, se alerta y la app ofrece crear el override de extension en Canvas
- **Estudio de APIs:** §5.5 (creacion progresiva) y §7.5 (captura al cierre) se tratan por separado; el estudio no define ninguna senal ni politica para el repositorio que queda disponible poco antes de su fecha efectiva.
- **Fusiona:** N026

### Q-2.3-73 — Al cerrar la tarea o terminar el curso, ¿que pasa con los repositorios y con el acceso de los estudiantes a su propio trabajo?

Decidir si el estudiante conserva acceso de lectura o de push indefinidamente; si los repositorios se archivan (solo lectura) automaticamente tras N dias de la ultima entrega, manualmente o nunca; si se revoca el push; si se le ofrece transferir el repositorio a su cuenta personal o hacer fork antes de una fecha de eliminacion, con aviso por Canvas; quien decide la politica (profesor del curso u owner de la organizacion) y si la app la ejecuta o solo la documenta. Definir tambien que ocurre con repositorios, snapshots y notificaciones pendientes si se elimina la tarea en la app.

- **Requisitos:** R2.3.7, R2.3.9, R2.3.11, R2.4.7, R2.1.3
- **Tipo:** decision_equipo + dependencia_externa · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija las acciones de fin de curso (archivar, quitar colaboradores, transferir), los mensajes de cierre a estudiantes y el estado terminal ARCHIVED; afecta si los snapshots siguen siendo accesibles a los correctores tras una transferencia.
- **Opciones:**
  - Acceso permanente
  - Archivar manteniendo acceso de lectura
  - Retirar acceso
  - Ofrecer transferencia o fork con plazo y aviso por Canvas
- **Estudio de APIs:** No lo aborda; §14 solo indica no borrar el repositorio ni la historia de estudiantes retirados.
- **Fusiona:** P214, P263

## Ya respondidas por el enunciado

Ninguna. Los 124 veredictos de la etapa de verificacion (116 preguntas P209–P324 mas las 8 de la ronda critica N001, N002, N003, N014, N018, N019, N026, N027) son ABIERTA o ABIERTA/BLOQUEA: ninguna pregunta quedo marcada YA_RESPONDIDA, por lo que no hay entradas que apartar con cita textual del enunciado en esta seccion.
