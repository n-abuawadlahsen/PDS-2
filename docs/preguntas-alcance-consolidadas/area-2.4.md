# Preguntas de alcance — Area 2.4

49 preguntas finales, fusionadas desde 74 de entrada, 2 bloqueantes para la parcial.

## Alcance de la entrega parcial y entorno de prueba

### Q-2.4-01 — ¿Qué parte del área 2.4 debe estar construida y demostrable en la entrega parcial del 16-sep: nada relacionado con fechas, solo la fecha base de la entrega vinculada leída al momento de vincular, o también las fechas por sección y las extensiones individuales mostradas en la vista de la tarea con su zona horaria explícita? ¿Se exige ya el polling periódico de cambios de fecha (R2.4.4) o basta con leer las fechas una vez al vincular? ¿Se exige alguna forma de captura de versiones (R2.4.5) en la parcial, o queda íntegramente comprometida para el 6-oct?

- **Requisitos:** R2.4.1, R2.4.2, R2.4.3, R2.4.4, R2.4.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Fija el alcance mínimo de fechas para la demo y determina si el job de captura debe construirse antes del 16-sep o puede postergarse; lo no listado debe quedar declarado como fuera de alcance parcial.
- **Opciones:**
  - Nada de 2.4 en la parcial (solo secciones 2.1–2.3)
  - Solo la fecha base de la entrega, leída al vincular la tarea
  - Fecha base + fechas por sección + extensiones, con zona horaria visible, sin polling
  - Fechas completas + polling periódico de cambios (R2.4.4)
  - Fechas + captura de versiones (R2.4.5) en la parcial
- **Estudio de APIs:** §13 no incluye fechas ni snapshots entre los hitos mínimos de la parcial.
- **Fusiona:** P389

### Q-2.4-02 — ¿El equipo dispone, o dispondrá antes de la entrega final, de una instancia de Canvas donde pueda crear al menos dos secciones, estudiantes inscritos en dos secciones a la vez, un group set con grupos, y overrides por sección, por grupo y ADHOC, para probar y demostrar R2.4.2/R2.4.3? ¿El plan Free-for-Teacher permite todo eso (secciones múltiples, group sets, overrides, differentiation tags)? ¿Se dispone además de cuentas de estudiante de prueba con las que hacer push real a GitHub para probar la captura de versiones y los casos de force-push?

- **Requisitos:** R2.4.2, R2.4.3, R2.4.5
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Sin este entorno no se pueden resolver las preguntas empíricas de esta área ni demostrar la funcionalidad, y la sección 4 del enunciado indica que lo que no se puede usar no se considera cumplido.
- **Opciones:**
  - Instancia Canvas propia del equipo (Free-for-Teacher) con datos sintéticos
  - Instancia Canvas del curso o del profesor, con permisos de docente
  - Simulación local / mocks de la API de Canvas y limitación documentada
  - Entorno mixto: Canvas real para lectura y datos sintéticos para overrides
- **Estudio de APIs:** §1.2 propone Free-for-Teacher como plan B; §13 hito 1 pide "Canvas de pruebas con 2 secciones… 2 assignments con overrides".
- **Fusiona:** P388

## Definicion de la fecha de cierre y de la fecha efectiva

### Q-2.4-03 — ¿Qué campo de Canvas define la "fecha de cierre" de una entrega para efectos del snapshot, de la UI, de los informes y de las comunicaciones: due_at, lock_at, o una combinación (due_at como cierre "a tiempo" y lock_at como fin del período de atraso, capturando eventualmente dos versiones)? ¿Qué se hace cuando la entrega tiene due_at y además un lock_at posterior (Canvas permite entregas atrasadas), cuando solo existe uno de los dos campos, y cuando la fecha efectiva de un sujeto es nula (assignment sin due_at, u override con due_at=null, que en Canvas significa "sin fecha de entrega" para ese target): no se captura y se muestra un estado "SIN FECHA" excluido de atrasos e informes, se usa lock_at como respaldo, se permite al profesor fijar en la app una fecha de cierre manual marcada como no proveniente de Canvas, o se captura solo cuando el profesor lo indique?

- **Requisitos:** R2.4.1, R2.4.5, R2.5.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija el parámetro `until` de la captura, define si existe una ventana de atraso entre due_at y lock_at y qué fecha se muestra como cierre; sin regla para el caso nulo, el barrido (effective_due_at <= now()) nunca dispara y la entrega queda perpetuamente "abierta" en dashboard, informes y corrección. También define si la app puede tener fechas propias no provenientes de Canvas. El algoritmo de fecha efectiva debe replicarse para el campo elegido, porque cada override trae due_at, lock_at y unlock_at por separado.
- **Opciones:**
  - due_at siempre (lock_at se ignora)
  - lock_at si existe, si no due_at
  - Dos versiones: una a due_at ("a tiempo") y otra a lock_at ("última aceptada")
  - Configurable por el profesor por entrega
  - Sin fecha efectiva: no capturar; estado "SIN FECHA" visible y excluido de atrasos
  - Sin fecha efectiva: permitir fecha de cierre manual en la app (marcada como no-Canvas)
  - Sin fecha efectiva: usar lock_at como respaldo; si tampoco existe, "SIN FECHA"
  - Sin fecha efectiva: capturar solo manualmente cuando el profesor lo indique
- **Estudio de APIs:** §7.3 y §7.5 usan exclusivamente due_at (effective_due_at) y señalan que due_at:null en un override significa "sin fecha de entrega" para ese target, sin definir el comportamiento de la app; §5.1 lista due_at/lock_at/unlock_at como "fecha base (2.4.1)" sin elegir entre ellos; §7.5 solo captura cuando effective_due_at <= now(), y no considera lock_at ni el caso sin fecha base.
- **Fusiona:** P329, P337, P340

### Q-2.4-04 — ¿Cuál es el algoritmo de fecha efectiva por (entrega, sujeto) cuando a un mismo sujeto le aplican varios overrides a la vez (ADHOC + sección, dos secciones con fechas distintas, grupo + sección): una cadena de precedencia estricta ADHOC > grupo > sección > base, o la semántica más permisiva de Canvas (la fecha más tardía entre todos los overrides aplicables, siendo due_at=null la más permisiva)? La regla debe resolver además: (a) los overrides cuyo target es un `group_id` que apunta a una etiqueta de diferenciación o grupo no colaborativo usado para "asignar a" un subconjunto de estudiantes en una tarea INDIVIDUAL — ¿la app resuelve la pertenencia del estudiante a cualquier grupo referenciado por un override, independientemente del tipo de tarea; los ignora en tareas individuales y alerta al docente; o los trata como equivalentes a ADHOC para sus miembros?; (b) el caso de un estudiante inscrito en dos o más secciones, incluido el modelo de datos N:M estudiante–sección y si las inscripciones en estado inactive/completed cuentan para aplicar el override de esa sección; (c) si un ADHOC más restrictivo que el de la sección gana (cadena estricta) o pierde (más permisiva); (d) si la fecha efectiva se calcula localmente, se consulta a Canvas por estudiante (p. ej. GET /users/:id/courses/:cid/assignments) o se calcula localmente y se contrasta con Canvas alertando discrepancias; y (e) cómo se rotula el origen de la fecha resultante en la UI ("general", "sección X", "etiqueta X", "extensión individual") y qué se muestra si el resultado es ambiguo. ¿Se verificará contra un caso real qué fecha le muestra Canvas al estudiante?

- **Requisitos:** R2.4.1, R2.4.2, R2.4.3
- **Tipo:** decision_equipo + verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es el núcleo del área: si la app calcula una fecha distinta a la que el estudiante ve en Canvas, el snapshot se toma en un instante "incorrecto" desde su perspectiva y la corrección se vuelve impugnable. Si los overrides de grupo se ignoran en tareas individuales, las extensiones dadas vía etiquetas se pierden y el snapshot se captura con la fecha equivocada. Determina también el modelo de enrollments y un criterio de aceptación de UI reproducible en la validación individual.
- **Opciones:**
  - Cadena estricta ADHOC > grupo > sección > base
  - La más permisiva (más tardía) entre todos los overrides aplicables; null = sin fecha
  - Consultar la fecha efectiva a Canvas por estudiante en vez de calcularla localmente
  - Calcular localmente y contrastar con Canvas, alertando discrepancias
  - Resolver pertenencia a todo grupo referenciado por un override, independiente del tipo de tarea
  - Ignorar overrides de grupo en tareas individuales y alertar al docente
  - Tratar la etiqueta de diferenciación como equivalente a ADHOC para sus miembros
  - Una fecha efectiva única + etiqueta "origen: sección X / etiqueta X / extensión"
  - Mostrar todas las fechas candidatas y marcar el sujeto como "fecha ambigua"
  - Considerar solo inscripciones en estado active
  - Considerar cualquier inscripción no eliminada (incluidas inactive/completed)
- **Estudio de APIs:** §7.3 propone la cadena estricta ADHOC > grupo > sección > base y solo dentro de "sección" toma la más tardía (max()); su paso 2 aplica overrides de grupo únicamente si existe `student_group_id` (tareas grupales); §7.1 lista `group_id` sin distinguir tipos de grupo; §4.2 advierte la relación N:M estudiante–sección y no trata inscripciones inactivas; Apéndice A.7 pide verificar el caso de dos secciones ("la más permisiva gana").
- **Fusiona:** P338, P325, P339

### Q-2.4-05 — En una tarea grupal cuyos integrantes tienen fechas efectivas distintas (extensión ADHOC a un integrante, integrantes en secciones con fechas diferentes), ¿qué fecha de cierre rige la captura de la versión del repositorio: el máximo de las fechas de los integrantes, el mínimo, la de la mayoría, solo el override de grupo (group_id) o la base ignorando los ADHOC/sección de los integrantes, un snapshot por integrante (varios SHAs sobre el mismo repositorio, cada uno con su fecha) o se marca "fecha ambigua" y se exige al profesor unificar la fecha en Canvas? ¿Cómo se comunica la heterogeneidad al corrector y a los estudiantes? ¿Se verificará si Canvas permite overrides ADHOC en tareas grupales y qué fecha muestra al grupo?

- **Requisitos:** R2.4.3, R2.4.5, R2.4.6, R2.7.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cambia la cardinalidad de la versión registrada (una por repositorio vs una por sujeto) y el flujo de corrección grupal; define si un compañero con extensión arrastra a todo el grupo y qué ve el corrector.
- **Opciones:**
  - Un snapshot por repositorio con max() de las fechas efectivas de los integrantes
  - Un snapshot por repositorio con min() (la más estricta)
  - Solo override de grupo (group_id) o base; ignorar ADHOC/sección de los integrantes en tareas grupales
  - Un snapshot por integrante (N SHAs por repositorio, cada uno con su fecha)
  - Marcar "fecha ambigua" y requerir que el profesor la unifique en Canvas
- **Estudio de APIs:** §7.3 sugiere usar max() de las fechas de los integrantes y mostrar en la UI que el repositorio tiene fechas heterogéneas; es una sugerencia no aprobada. §7.1 documenta group_id y student_ids como targets de override.
- **Fusiona:** P331, P342

### Q-2.4-06 — Para un sujeto al que una entrega no le aplica (tarea con only_visible_to_overrides=true sin override aplicable, u override con due_at null): ¿se le crea igualmente el repositorio, dado que R2.3.4 exige un único conjunto de repositorios por tarea y la tarea puede tener otras entregas que sí le aplican, se crea solo si al menos una entrega le es visible, o queda excluido de la tarea mientras ninguna entrega le sea visible? ¿Con qué estado aparece en la vista de estados, en el dashboard y en la vista de corrección ("NO APLICA", oculto, pendiente sin fecha)? ¿Cuenta en los denominadores de las métricas de R2.7.7? ¿Y si una entrega de la misma tarea le es visible y otra no?

- **Requisitos:** R2.4.1, R2.4.3, R2.4.5, R2.3.4, R2.3.7, R2.5.6, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita marcar como atrasado o "sin entrega" a quien no debía entregar y define si la creación de repositorios (que es por tarea) depende de la visibilidad de cada entrega, además de cómo se cuentan los sujetos en dashboard, snapshots e informes.
- **Opciones:**
  - Repo se crea igual (es por tarea); snapshot de esa entrega en estado "NO APLICA"
  - Repo se crea solo si al menos una entrega es visible para el sujeto
  - Sujeto excluido de la tarea mientras ninguna entrega le sea visible
  - Mostrar al sujeto como "no aplica" y excluirlo de los denominadores de R2.7.7
  - Mostrar al sujeto oculto en las vistas de esa entrega, visible en las demás
- **Estudio de APIs:** §7.3 indica que "la tarea no existe para él; no le creen snapshot ni lo cuenten como atrasado", pero no dice si se crea el repositorio, cómo se muestra, ni cómo se resuelve la mezcla entre entregas de la misma tarea.
- **Fusiona:** P330, P341

### Q-2.4-07 — ¿Tiene algún rol el campo unlock_at en la app: define el inicio del "período" de la entrega para las métricas de actividad de R2.5.7, condiciona el estado "futura" de la entrega, impide notificar o contar actividad antes de esa fecha, o se ignora completamente?

- **Requisitos:** R2.4.1, R2.5.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el concepto de "período de entrega" del spec, del que dependen las métricas de actividad y los estados mostrados en el dashboard.
- **Opciones:**
  - unlock_at define el inicio del período de la entrega
  - El período va desde el cierre de la entrega anterior hasta el cierre de la actual
  - unlock_at solo condiciona el estado "futura" de la entrega, no las métricas
  - Ignorar unlock_at por completo
- **Estudio de APIs:** §5.1 lo lista como campo; §8.5 define el período por [entrega_anterior.due, entrega_actual.due] sin usar unlock_at.
- **Fusiona:** P385

### Q-2.4-08 — ¿La fecha efectiva por (entrega, sujeto) se MATERIALIZA en una tabla (delivery_id, subject_id, effective_due_at, effective_lock_at, source, override_id, applies:boolean, computed_at) que alimenta el barrido de snapshots, el dashboard, el informe y los recordatorios, o se recalcula en cada lectura a partir de overrides y membresías? Si se materializa: ¿cuándo se recalcula (en cada sync de fechas, ante cada cambio de roster, de grupo o de sección), las filas se crean eager al vincular la entrega o lazy en el barrido, y se guardan además los AssignmentOverride crudos en una tabla local?

- **Requisitos:** R2.4.1, R2.4.2, R2.4.3, R2.4.4, R2.4.5, R2.5.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El barrido "todo lo vencido y no capturado" necesita un índice sobre la fecha efectiva; el cálculo al vuelo no es indexable y la materialización exige definir sus disparadores de invalidación.
- **Opciones:**
  - Tabla materializada recalculada por eventos
  - Cálculo en cada lectura (función pura sobre overrides + membresías)
  - Híbrido: materializada solo para entregas no capturadas
- **Estudio de APIs:** §7.3 entrega el algoritmo como función pura; §5.2 pone effective_due_at solo en DeliverySnapshot; §7.5 barre "sin snapshot y con effective_due_at <= now()", lo que presupone materialización sin decirlo.
- **Fusiona:** P394

## Obtencion y sincronizacion de fechas desde Canvas

### Q-2.4-09 — ¿`include[]=all_dates` e `include[]=overrides` devuelven siempre todos los overrides (incluidos los ADHOC de todos los estudiantes) con el token del profesor, sin límite de cantidad ni truncamiento, o es necesario llamar además a GET /assignments/:id/overrides con paginación? ¿Basta una sola request por curso o se requiere una por entrega?

- **Requisitos:** R2.4.1, R2.4.2, R2.4.3
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la fuente de datos de fechas, el número de requests por ciclo de sincronización y si el cálculo de fecha efectiva puede quedar incompleto silenciosamente.
- **Opciones:**
  - Una request por curso con all_dates + overrides
  - Una request por entrega al endpoint de overrides, paginada
  - Combinación: all_dates para el listado y overrides paginado para el detalle
- **Estudio de APIs:** §7.2 asume que all_dates + overrides "trae todo en una sola request".
- **Fusiona:** P362

### Q-2.4-10 — ¿Crear, editar o eliminar un AssignmentOverride actualiza `assignment.updated_at`? Si no lo hace, el polling incremental basado en updated_at no detectará las extensiones y habrá que comparar siempre all_dates/overrides completos o consultar el endpoint de overrides en cada ciclo.

- **Requisitos:** R2.4.3, R2.4.4
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El mecanismo de detección de cambios propuesto depende de este supuesto; si es falso, R2.4.3 y R2.4.4 fallan silenciosamente.
- **Opciones:**
  - Confiar en updated_at como disparador incremental
  - Comparar siempre el conjunto completo de all_dates/overrides
  - Consultar el endpoint de overrides en cada ciclo, independientemente de updated_at
- **Estudio de APIs:** §7.4 usa "si assignment.updated_at > delivery.canvas_updated_at" como disparador.
- **Fusiona:** P361

### Q-2.4-11 — ¿Cómo se decide que un dato de Canvas CAMBIÓ realmente, para no generar historial, alertas ni anuncios espurios, sabiendo que la API puede devolver el mismo contenido con distinta forma (arrays de overrides en otro orden, fechas con distinta precisión o formato, HTML re-serializado en las descripciones, nombres con espacios distintos, updated_at que se mueve por ediciones irrelevantes)? Decidir: (a) el método de detección — comparación campo a campo sobre un subconjunto normalizado, hash del objeto crudo normalizado, o confiar en updated_at; (b) la lista cerrada de campos SIGNIFICATIVOS que disparan reacción (fecha efectiva, group_category_id, published, points_possible, membresías) frente a los COSMÉTICOS que se actualizan en silencio (descripción, orden de arrays, html_url); (c) qué umbral aplica a cada reacción — recalcular, registrar en historial, alertar al docente, anunciar en Canvas, notificar al estudiante — considerando que R2.6.6 exige anuncios por cambio de fecha; y (d) qué ocurre si dentro de un mismo ciclo de polling se detectan varios cambios encadenados del mismo campo: ¿un evento por cambio o uno consolidado con valor inicial y final? ¿Se guarda el objeto crudo o solo un hash para comparar?

- **Requisitos:** R2.4.4, R2.2.1, R2.6.6, R2.5.6, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Sin esta regla el historial de sincronización se llena de "cambios" inexistentes, el informe diario los reporta y, peor, se publican anuncios en el curso del profesor por cambios que nadie hizo. También define si se guarda el objeto crudo o solo un hash para comparar.
- **Opciones:**
  - Comparación campo a campo sobre un subconjunto normalizado de campos significativos
  - Hash del objeto crudo normalizado y comparación de hashes
  - Confiar únicamente en updated_at
  - Un evento de historial por cada cambio detectado en el ciclo
  - Un evento consolidado por ciclo con valor inicial y final
  - Guardar el objeto crudo completo por versión
  - Guardar solo el hash y los campos significativos
- **Estudio de APIs:** §7.4 propone comparar assignment.updated_at y "registrar en un log de auditoría: quién/cuándo/de qué a qué", y sugiere anunciar si el cambio es ">1h", pero no aborda cómo se determina que un campo cambió ni el ruido de cambios cosméticos.
- **Fusiona:** N036

### Q-2.4-12 — ¿Con qué frecuencia se hace polling de las fechas de Canvas: fija (el estudio propone cada 10 min), adaptativa (más frecuente en las horas previas a un cierre), o por evento? ¿Existe un botón "sincronizar ahora"? ¿Cuál es la latencia máxima aceptable entre un cambio hecho en Canvas y su reflejo en la app, expresada como criterio de aceptación medible?

- **Requisitos:** R2.4.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Convierte el "mantener actualizadas" de R2.4.4 en un criterio verificable y dimensiona el consumo del throttling de Canvas por token de profesor.
- **Opciones:**
  - Cron fijo cada 10 min para todos los cursos
  - Cadencia adaptativa según proximidad del cierre
  - Solo bajo demanda ("sincronizar ahora") más un barrido diario
  - Cron fijo + botón "sincronizar ahora" + refuerzo previo a cada cierre
- **Estudio de APIs:** §7.4 propone cron cada 10 min y botón "sincronizar ahora"; §12 fija sync_canvas cada 10 min.
- **Fusiona:** P360

### Q-2.4-13 — ¿Se mantiene un historial de cambios de fecha por entrega y por sujeto (valor anterior, valor nuevo, detectado_en, tipo e id del override que lo provocó) y dónde se muestra: vista de la entrega, timeline del repositorio, informe diario? Dado que la API de Canvas no informa quién realizó el cambio, ¿se registra el usuario del token con el que se detectó, se deja el campo vacío, o se omite la columna?

- **Requisitos:** R2.4.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define las tablas y la UI de auditoría de R2.4.4 y qué se puede afirmar honestamente durante la validación individual.
- **Opciones:**
  - Historial completo por (entrega, sujeto) con valor anterior y nuevo
  - Historial solo a nivel de entrega (fecha base y por sección), sin desglose por sujeto
  - Sin historial: solo el valor vigente
  - Registrar como origen el usuario del token con el que se detectó el cambio
  - Dejar el campo "quién" vacío y documentar la limitación de la API
- **Estudio de APIs:** §7.4 propone un "log de auditoría: quién/cuándo/de qué a qué", pero el "quién" no está disponible en la API pública.
- **Fusiona:** P365

### Q-2.4-14 — Cuando se detecta un cambio de fecha, ¿cómo se entera el equipo docente (banner in-app en la tarea, email inmediato, sección "cambios de fecha" del informe diario, ninguno más allá del historial) y qué cambios disparan comunicación automática a los estudiantes y por qué canal: cambio de fecha base o de sección → anuncio en Canvas (con specific_sections), extensión ADHOC → conversación individual o nada por ser información privada, adelantos de fecha, umbral mínimo de relevancia (el estudio sugiere >1 h), redacción del texto y flag de activación por tarea? ¿Qué se hace si el cambio ocurre cuando la entrega ya cerró?

- **Requisitos:** R2.4.4, R2.6.2, R2.6.6, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija R2.4.4 desde la perspectiva del usuario y su cruce con R2.6.2/R2.6.6/R2.6.7: evita anuncios masivos por extensiones individuales, define el criterio de "cambio relevante" y qué ve el docente sin entrar al historial.
- **Opciones:**
  - Docente: banner in-app en la tarea
  - Docente: email inmediato
  - Docente: sección "cambios de fecha" del informe diario
  - Docente: solo historial, sin notificación activa
  - Estudiantes: anuncio en Canvas con specific_sections para cambios de sección o base
  - Estudiantes: conversación individual para extensiones ADHOC
  - Estudiantes: no comunicar extensiones individuales (privacidad)
  - Umbral de relevancia configurable (p. ej. >1 h) antes de comunicar
  - Flag de activación por tarea (notify_date_change)
  - No comunicar cambios sobre entregas ya cerradas
- **Estudio de APIs:** §7.4 propone anuncio si el cambio es "relevante (>1h)" y el profesor lo activó, y menciona anuncio a estudiantes más log, sin definir la vía de aviso al docente; §9.2 propone specific_sections; §9.4 propone el flag notify_date_change.
- **Fusiona:** P366, P367

### Q-2.4-15 — ¿La app solo LEE las extensiones desde Canvas (interpretación mínima de "considerar" en R2.4.3) o también permite al profesor crear, editar y eliminar AssignmentOverrides en Canvas desde la app (POST/PUT/DELETE .../overrides), por ejemplo otorgar una extensión desde la vista del sujeto? Si es solo lectura, ¿el spec indica explícitamente que el cambio se hace en Canvas y cuánto tarda en reflejarse?

- **Requisitos:** R2.4.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el alcance funcional del área, los scopes OAuth adicionales necesarios y un flujo de UI completo; también determina qué se le promete al profesor sobre latencia de reflejo.
- **Opciones:**
  - Solo lectura de overrides
  - Lectura + creación de extensiones ADHOC desde la app
  - Lectura + CRUD completo de overrides desde la app
  - Solo lectura, con enlace directo a la pantalla de Canvas donde se edita
- **Estudio de APIs:** §7.1 lista los endpoints de escritura de overrides sin recomendar usarlos.
- **Fusiona:** P382

### Q-2.4-16 — ¿Los campos de sección `start_at`/`end_at` y `restrict_enrollments_to_section_dates` afectan algo en la app (participación del estudiante, fecha efectiva de una entrega) o se ignoran? Confirmar en la documentación de Canvas si alteran las fechas de entrega o solo el acceso al curso.

- **Requisitos:** R2.4.2
- **Tipo:** investigable_en_docs · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El estudio afirma que esa configuración "cambia qué fechas aplican"; hay que confirmar si eso rige para las fechas de entrega antes de modelarlo.
- **Opciones:**
  - Modelar el efecto sobre la fecha efectiva si la documentación lo confirma
  - Ignorar los campos y documentar el supuesto
  - Registrar los campos y mostrar una advertencia al docente sin alterar el cálculo
- **Estudio de APIs:** §4.2 advierte que restrict_enrollments_to_section_dates "cambia qué fechas aplican".
- **Fusiona:** P386

## Zona horaria, formato y presentacion de fechas

### Q-2.4-17 — ¿En qué zona horaria se muestran todas las fechas de la app: America/Santiago fija, la `time_zone` del curso en Canvas, la del navegador del usuario, o configurable por usuario con un default? ¿Se muestra el offset UTC o el sufijo de zona junto a la hora? ¿Qué formato se usa (24 h, estilo "mié 16 sep 2026, 13:30") y se combinan fecha relativa ("vence en 2 días") y absoluta? ¿Cómo se presenta una entrega con fechas heterogéneas por sección o con extensiones ("16 sep · Sección 2: 17 sep · 1 extensión")? ¿Cómo se manejan los cambios de horario de verano de Chile (offset -4/-3, primer domingo de septiembre y de abril) en la hora del informe diario, en el cálculo de "N días sin actividad", en las agrupaciones diarias del dashboard (¿día UTC o día local?), en la comparación con now() y cuando un cierre queda programado a una hora que no existe o que se repite ese día?

- **Requisitos:** R2.4.1, R2.4.2, R2.4.3, R2.4.8, R2.5.2, R2.5.3, R2.5.6, R2.6.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Las fechas se exhiben en la UI, en informes por email y en anuncios de Canvas; un error de 3 horas invalida un snapshot o un "vence hoy" y es un error visible y grave. Define además el criterio de agregación diaria, la programación del cron y el componente de fecha reutilizado en entregas, dashboard, timeline e informe.
- **Opciones:**
  - America/Santiago fija
  - time_zone del curso en Canvas
  - Zona del navegador del usuario
  - Configurable por usuario con default America/Santiago
  - Agregación diaria por día local de la zona elegida
  - Agregación diaria por día UTC
  - Mostrar siempre el sufijo de zona / offset junto a la hora
  - Combinar fecha absoluta y relativa en la UI
- **Estudio de APIs:** §14 "Zonas horarias" indica guardar en UTC (timestamptz) y convertir solo al renderizar, sin definir la zona de presentación ni la agregación diaria; §9.1 fija el cron del informe a las 07:00 America/Santiago; §7.3 sugiere mostrar en la UI que un repositorio grupal tiene fechas heterogéneas.
- **Fusiona:** P334, P364, P393

### Q-2.4-18 — ¿Cómo se representa e interpreta due_at cuando la fecha en Canvas es de "todo el día" (all_day=true, all_day_date): se toma como 23:59:59 en la zona horaria del curso convertida a UTC? ¿La app muestra "todo el día" o la hora exacta resultante, y qué zona horaria del curso (campo time_zone del Course) se usa para interpretar all_day_date?

- **Requisitos:** R2.4.1
- **Tipo:** investigable_en_docs · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Un cierre "todo el día" del 16-09 aparece como 17-09 02:59:59 UTC; sin regla, la UI puede mostrar un día distinto al que muestra Canvas y la captura dispararse en otro día.
- **Opciones:**
  - Interpretar all_day_date a 23:59:59 en la time_zone del curso y mostrar "todo el día"
  - Interpretar igual pero mostrar la hora exacta convertida
  - Ignorar all_day y usar el due_at en UTC tal cual lo entrega la API
- **Estudio de APIs:** §7.1 lista all_day y all_day_date sin darles tratamiento.
- **Fusiona:** P363

### Q-2.4-19 — En la vista de la entrega, ¿cómo se presenta la fecha efectiva de cada sujeto y su origen (general / sección X / grupo o etiqueta / extensión individual, con el id del override) y se listan explícitamente las excepciones ("3 estudiantes con extensión hasta …")? ¿Qué estados tiene la entrega a nivel agregado cuando sus sujetos tienen fechas distintas (futura, abierta, cerrando —algunos sujetos ya cerrados—, cerrada, capturada parcialmente, con problemas) y se muestran el rango [primera, última] de fechas efectivas y el porcentaje de snapshots capturados?

- **Requisitos:** R2.4.2, R2.4.3, R2.4.5, R2.5.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.5.6 exige mostrar las entregas, sus fechas y su estado, pero con overrides no existe una única fecha ni un único estado por entrega; es el criterio de aceptación de UI demostrable para R2.4.2/R2.4.3.
- **Opciones:**
  - Fecha efectiva por sujeto con etiqueta de origen y lista explícita de excepciones
  - Solo fecha base de la entrega, con un contador "N excepciones" desplegable
  - Estado agregado con enumeración cerrada (futura / abierta / cerrando / cerrada / capturada parcialmente / con problemas)
  - Mostrar el rango [primera, última] de fechas efectivas
  - Mostrar el porcentaje de snapshots capturados sobre el total de sujetos
- **Estudio de APIs:** §7.3 devuelve (due_at, origen) como texto; §5.6 muestra una tabla de estados de repositorios sin columna de fecha; el estado agregado de la entrega no lo aborda.
- **Fusiona:** P377, P378

## Definicion y mecanismo de la version registrada

### Q-2.4-20 — ¿Qué constituye formalmente "la versión registrada" de una entrega y con qué nivel de blindaje se protege: SHA en base de datos; SHA + tag en GitHub; SHA + rama entrega-N; SHA + zip descargado y almacenado por la app (GET /repos/{o}/{r}/zipball/{sha}); SHA + fork/mirror a un repositorio de archivo del equipo docente; o SHA + tag + ruleset de organización que impida force-push y borrado de tags? ¿Se aprueba la propuesta SHA + tag del estudio? Si un estudiante hace force-push y el commit capturado deja de ser alcanzable desde cualquier ref (GitHub puede dejar de servirlo tras la recolección de basura), ¿la app lo detecta y cómo lo señala al corrector? ¿Qué estado y qué mensaje muestra la UI cuando el SHA ya no resuelve (404) o cuando el repositorio fue eliminado o recreado por el profesor? Verificar empíricamente si GitHub mantiene accesible por URL un SHA huérfano.

- **Requisitos:** R2.4.5, R2.4.7, R2.4.8, R2.7.4
- **Tipo:** decision_equipo + verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.4.7 exige que la versión registrada siga siendo correcta aunque continúe la actividad; el SHA en base de datos no sirve si el código ya no es alcanzable. El nivel de blindaje define costos de almacenamiento, permisos de la GitHub App (los rulesets requieren permisos de organización) y los estados de error del spec.
- **Opciones:**
  - Solo SHA en BD
  - SHA + tag (propuesta del estudio)
  - SHA + tag + ruleset de protección de tags y bloqueo de force-push
  - SHA + zip archivado por la app en almacenamiento propio
  - SHA + fork/mirror a repositorio de archivo del equipo docente
  - SHA + rama entrega-N
  - Solo detectar y alertar mediante verificación periódica del SHA
- **Estudio de APIs:** §0 y §7.5 recomiendan el SHA en BD como fuente de verdad más un tag inmutable refs/tags/entrega-N, con el ruleset de tags como "opcional"; no cubren la inalcanzabilidad del commit, la copia local, el zip/mirror ni el caso de repositorio eliminado.
- **Fusiona:** P369, P353, P332

### Q-2.4-21 — ¿Qué rama o ramas se consideran para determinar la versión de cierre: solo el `default_branch` leído del repositorio, todas las ramas tomando el commit más reciente anterior o igual a la fecha en cualquiera de ellas, una rama fija configurable por tarea (p. ej. "entrega"), o default_branch con alerta cuando existan commits anteriores al cierre en otras ramas? ¿Se avisa al corrector de esa situación y qué se le comunica al estudiante sobre qué rama se corrige?

- **Requisitos:** R2.4.5, R2.4.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Un estudiante que trabaja en `dev` sin mergear quedaría con un snapshot vacío o antiguo; cambia la consulta a la API (una llamada por rama vs una sola) y el mensaje al estudiante en Canvas.
- **Opciones:**
  - Solo default_branch
  - Todas las ramas, commit más reciente <= fecha
  - Rama fija configurable por tarea (p. ej. "entrega")
  - default_branch + alerta "hay commits hasta el cierre en otras ramas"
- **Estudio de APIs:** §7.5 usa sha={default_branch}; §14 advierte no asumir "main" y leer repository.default_branch.
- **Fusiona:** P349

### Q-2.4-22 — Verificar contra la API de GitHub la semántica exacta de `until` en GET /repos/{o}/{r}/commits: ¿es inclusivo en el segundo exacto? ¿filtra por committer date o por author date? ¿qué devuelve con per_page=1 cuando el historial tiene fechas fuera de orden (recorrido topológico vs cronológico)? ¿Qué precisión (segundos, milisegundos) tienen las fechas que entrega Canvas y cómo se comparan con las de GitHub?

- **Requisitos:** R2.4.5
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina la regla "último commit antes o EN la fecha" del spec y si la captura es determinista ante historiales con fechas desordenadas.
- **Opciones:**
  - Confiar en el primer resultado de until con per_page=1
  - Traer una ventana de commits y elegir el máximo aplicando la regla localmente
  - Definir la regla como "estrictamente anterior" para evitar la ambigüedad del segundo exacto
- **Estudio de APIs:** §7.5 afirma que el primer resultado es el commit más reciente "en o antes de" until; no verifica committer vs author date ni el orden topológico.
- **Fusiona:** P350

### Q-2.4-23 — ¿Qué instante define que un commit "existía" al cierre: el committer date que filtra `until` (falsificable con `git commit --date` o un rebase, permitiendo subir después del cierre commits con fecha anterior), el author date, o el instante en que GitHub recibió el push (webhook `push`, received_at)? ¿Se aprueba el enfoque del estudio basado solo en `until`? ¿Se exige que el snapshot y el dashboard/timeline usen la MISMA definición de fecha del commit; y si no, qué se muestra cuando el commit capturado no es el último que el timeline dibuja antes de la línea de cierre, o cuando el timeline muestra commits "antes del cierre" que el snapshot no incluyó? ¿Se persisten en CommitRecord las tres marcas (authored_at, committed_at, received_at del push/webhook) para poder cambiar la regla sin reingestar?

- **Requisitos:** R2.4.5, R2.4.7, R2.5.2, R2.5.7, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es la decisión de integridad central de R2.4.5/R2.4.7 y a la vez la que evita que corrector y dashboard se contradigan sobre "qué había al cierre"; fija además las columnas obligatorias de CommitRecord desde la primera ingesta. Un enfoque por push time exige ingestión por webhook antes del cierre y un backfill por polling que no dispone de push time.
- **Opciones:**
  - Committer date vía until (simple, falsificable)
  - Author date
  - Push time vía webhooks: incluir solo commits cuyo push llegó antes del cierre; polling como respaldo marcado
  - Híbrido: until + bandera de anomalía si el push fue posterior al cierre o difiere del committer date en más de X
  - Congelar el HEAD conocido al instante del cierre a partir del último webhook recibido
  - Misma definición en snapshot y timeline
  - Definiciones distintas con aviso explícito en la UI
  - Persistir las tres fechas (authored_at, committed_at, received_at) y decidir por vista
- **Estudio de APIs:** §7.5 usa GET /commits?until= (committer date) sin advertir que la fecha es controlada por el cliente git; §8.1 registra webhooks push para el dashboard sin vincularlos al snapshot; §8.3 guarda authored_at y committed_at pero no la fecha de recepción del push.
- **Fusiona:** P333, P351, P397

### Q-2.4-24 — ¿Cuál es la convención de nombre de los tags de entrega (entrega-1, entrega-final, <slug-entrega>, con o sin fecha) y su tipo (ref ligero vs tag anotado con mensaje, fecha de captura y tagger)? ¿Qué se hace si ya existe un tag con ese nombre creado por el estudiante apuntando a otro SHA, y cómo se nombra el tag de una recaptura (entrega-1-v2, mover el tag con force, no crear tag)?

- **Requisitos:** R2.4.5, R2.4.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija la interfaz visible en GitHub para estudiantes y correctores, la idempotencia del job de captura y la trazabilidad de las recapturas.
- **Opciones:**
  - Ref ligero con nombre fijo por entrega (entrega-N)
  - Tag anotado con mensaje, fecha de captura y tagger
  - Nombre derivado del slug de la entrega
  - Ante colisión: no crear el tag y registrar conflicto
  - Ante colisión: crear con sufijo alternativo
  - Recaptura: nuevo tag versionado (entrega-N-v2)
  - Recaptura: mover el tag existente con force
  - Recaptura: no crear tag y dejar solo el SHA
- **Estudio de APIs:** §7.5 usa refs ligeros refs/tags/entrega-1-cierre y ante un 422 propone "verificar que apunte al mismo SHA"; no define nombres finales ni el tratamiento de recapturas.
- **Fusiona:** P355

### Q-2.4-25 — ¿Qué metadatos guarda y muestra cada versión registrada: SHA, committed_at, autor del último commit, número de commits hasta el cierre, fecha efectiva usada y su origen, captured_at, nombre del tag, estado, commits posteriores al cierre, y fuente (automático / manual / recaptura)? ¿Cuáles de ellos son obligatorios para dar por cumplido R2.4.8?

- **Requisitos:** R2.4.5, R2.4.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el esquema de DeliverySnapshot y el contenido de la vista de corrección; sin una lista mínima obligatoria no hay criterio de aceptación para R2.4.8.
- **Opciones:**
  - Mínimo: SHA + fecha efectiva usada + captured_at + estado
  - Mínimo + autor y fecha del último commit y número de commits
  - Completo: además tag, origen de la fecha, commits posteriores al cierre y fuente (automático/manual)
- **Estudio de APIs:** §5.2 propone commit_sha, committed_at, tag_name, captured_at, status y effective_due_at; §10.2 sugiere mostrar "capturado el… · 47 commits · último por…".
- **Fusiona:** P390

### Q-2.4-26 — ¿Cuál es la enumeración cerrada de estados de la fila DeliverySnapshot y sus transiciones (por ejemplo PENDING → CAPTURING → CAPTURED | NO_COMMITS | NO_REPO | NOT_APPLICABLE | ERROR, y CAPTURED → SUPERSEDED por recaptura), y existe un sub-estado de tag (TAG_PENDING / TAG_OK / TAG_CONFLICT / TAG_FAILED) independiente del SHA para permitir la captura en dos fases? ¿Cuáles son terminales y cuáles reintenta el barrido? ¿Se persisten la rama/ref y el `until` exactos usados en la consulta, y los metadatos derivados (número de commits, autores) se toman de CommitRecord —posiblemente incompleto— o de la API al capturar? ¿GradingRecord referencia la fila-versión del snapshot por FK o copia el SHA para detectar que se corrigió una versión superada? ¿Qué invariantes de concurrencia e idempotencia se fijan (unicidad de (entrega, repositorio[, versión]), lock por sujeto) y qué ocurre cuando el tag ya existe apuntando a otro SHA —creado por el estudiante o por una corrida anterior—: estado CONFLICTO, sobrescribir con force, crear con otro nombre, o ignorar el tag?

- **Requisitos:** R2.4.5, R2.4.6, R2.4.7, R2.4.8, R2.7.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija el contrato entre el job de captura, la vista de la entrega y la corrección; sin sub-estado de tag, un fallo de rate limit al crear tags deja snapshots "no capturados" aunque el SHA ya esté registrado, y sin invariantes de concurrencia dos workers o un reinicio producen snapshots duplicados o inconsistentes.
- **Opciones:**
  - Estado único con enumeración ampliada
  - Estado del SHA + sub-estado de tag independiente
  - Versionado de filas con flag `current`
  - Unicidad por (entrega, repositorio) que nunca se sobrescribe
  - Unicidad por (entrega, repositorio, versión) con historial
  - Tag en conflicto: estado CONFLICTO sin escribir
  - Tag en conflicto: sobrescribir con force
  - Tag en conflicto: crear con otro nombre
  - GradingRecord con FK a la fila-versión del snapshot
  - GradingRecord con copia del SHA corregido
- **Estudio de APIs:** §7.5 define solo NO_COMMITS y CAPTURED, indica una fila por (delivery, repository) que nunca se sobrescribe y, ante un tag existente (422), "verificar que apunte al mismo SHA" sin definir qué hacer si no coincide; §5.2 lista snapshot_status sin enumerarlo.
- **Fusiona:** P395, P380

### Q-2.4-27 — ¿Cada cuánto corre el job de captura (el estudio propone cada 5 min) y cuál es la tolerancia aceptable entre la fecha de cierre y la captura efectiva como criterio de aceptación ("capturado dentro de N minutos")? ¿Se muestra captured_at y una etiqueta "captura tardía" cuando se excede (p. ej. por servidor caído), considerando que con `until` histórico el resultado solo cambia ante force-push o commits retrodatados? Con 60–100 repositorios cerrando a la misma hora y sabiendo que la creación de tags son requests generadoras de contenido (límite 80/min y 500/h), ¿qué orden y throttle se aplica (p. ej. registrar primero todos los SHA con GETs y encolar los tags después), cuánto puede tardar en completarse la captura de toda la entrega y se muestra el progreso ("capturados 43/60")?

- **Requisitos:** R2.4.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Convierte el "automáticamente" de R2.4.5 en algo medible, dimensiona el job para el caso real de un curso completo y define la UI de progreso de cierre y qué se comunica cuando la captura fue tardía.
- **Opciones:**
  - Cron cada 5 min que barre todo lo vencido y no capturado
  - Cron adaptativo que se densifica alrededor de los cierres programados
  - Job programado por cierre (un timer por entrega/sujeto)
  - Dos fases: primero todos los SHA por GET, luego los tags en cola con throttle
  - Una sola fase por repositorio (SHA + tag) con throttle global
  - Mostrar progreso "capturados N/M" y etiqueta "captura tardía" cuando se excede la tolerancia
  - No mostrar progreso; solo el resultado final
- **Estudio de APIs:** §7.5 propone un cron cada 5 min que barre todo lo vencido y no capturado; §12 fija capture_snapshots cada 5 min; §2.4 documenta los límites secundarios y §5.5 fija throttle para la creación de repositorios, pero no lo aplica a los snapshots.
- **Fusiona:** P370, P371

### Q-2.4-28 — Si la fecha cambia en Canvas dentro de la ventana de polling previa al cierre (la app aún no la ha visto), la captura puede usar una fecha obsoleta. ¿Se exige re-sincronizar la tarea desde Canvas inmediatamente antes de cada captura (1 GET por entrega), se acepta la ventana de polling como riesgo asumido, o el snapshot queda en estado "provisional" hasta que el siguiente sync exitoso confirme la fecha?

- **Requisitos:** R2.4.4, R2.4.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el protocolo del job de captura, el costo en requests hacia Canvas y un posible estado adicional del snapshot.
- **Opciones:**
  - Sync de la tarea justo antes de capturar (1 GET por entrega)
  - Aceptar la ventana de polling y documentar el riesgo
  - Snapshot "provisional" confirmado en el siguiente sync
- **Estudio de APIs:** §7.5 no consulta Canvas al capturar; §7.4 asume polling cada 10 min.
- **Fusiona:** P359

### Q-2.4-29 — ¿Cómo se distinguen y se muestran los casos "repositorio sin commits" (GET /commits responde 409 en repositorios vacíos), "solo el commit inicial del repositorio base / auto_init" y "con trabajo del estudiante"? ¿Se crea el tag cuando el único commit es el del template? ¿Cómo identifica la app ese commit inicial (SHA del repositorio base, autor bot, mensaje)? ¿Cómo se maneja el 409 sin que el job falle?

- **Requisitos:** R2.4.5, R2.4.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Un snapshot que apunta al commit del template no es una "entrega" y no debería contarse como tal en informes ni en corrección; define además la robustez del job ante el 409.
- **Opciones:**
  - Tres estados: SIN_COMMITS / SOLO_BASE / CAPTURADO
  - Dos estados y mostrar el autor del último commit para que el corrector juzgue
  - Comparar el SHA con el commit inicial del repositorio base para detectar SOLO_BASE
  - No crear tag cuando el único commit es el del template
  - Crear tag siempre, con la marca de estado correspondiente
- **Estudio de APIs:** §7.5 define NO_COMMITS "si no hay commits"; §5.3 advierte que sin commit inicial no funcionan los tags; no distingue el caso "solo template".
- **Fusiona:** P348

### Q-2.4-30 — ¿Qué filas deben ser autocontenidas como evidencia, copiando el dato al momento del hecho (full_name y owner del repositorio, installation_id, rama, SHA, lista de integrantes con sus logins, sección, título e id del override y fecha efectiva usada, nombre del grupo), para seguir siendo legibles y correctas aunque el origen cambie o desaparezca (override borrado, grupo renombrado o eliminado, repositorio renombrado o transferido, organización re-vinculada, estudiante retirado, mapeo corregido)? ¿Cuáles llevan solo FKs y se resuelven en la lectura? ¿Se aplica el mismo criterio a GradingRecord (copia de la rúbrica y del payload enviado a Canvas) y al informe diario (copia de las alertas incluidas)?

- **Requisitos:** R2.4.7, R2.4.8, R2.7.4, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina si la vista de corrección y la auditoría sobreviven a cambios en Canvas y GitHub o quedan con referencias rotas; afecta el tamaño de las tablas y la política de FKs.
- **Opciones:**
  - Denormalizar en snapshot, grading e informe
  - Solo FKs con soft delete en el origen
  - Copia parcial (solo lo que puede desaparecer en Canvas/GitHub)
- **Estudio de APIs:** §7.5 sostiene que "el SHA en BD es la fuente de verdad", sin hablar de denormalizar el contexto que lo rodea.
- **Fusiona:** P396

## Acceso a la version, correccion y comunicacion de la entrega

### Q-2.4-31 — ¿El acceso directo a la versión registrada (R2.4.8) es un link a GitHub (/tree/<sha>) —lo que exige que cada ayudante tenga acceso de lectura a repositorios privados de la organización—, un visor de código dentro de la app usando el token de la GitHub App (GET /git/trees/{sha}?recursive=1 + GET /contents?ref=sha), una descarga de la versión exacta como zip (GET /repos/{o}/{r}/zipball/{sha}) servida por la app para revisar o ejecutar el código localmente sin cuenta de GitHub, o una combinación? Si es link, ¿cómo se otorga y se revoca ese acceso (miembro de la organización con base permission read, colaborador por repositorio, team docente) y qué ocurre al retirar a un ayudante? ¿La URL /tree/<sha> funciona si el SHA quedó inalcanzable desde cualquier ref? Si hay descarga zip: ¿límite de tamaño, qué permiso de R2.1.8 la habilita, se registra la descarga en auditoría, y la copia se conserva como respaldo del snapshot o se genera bajo demanda?

- **Requisitos:** R2.4.8, R2.7.4, R2.1.8, R2.1.9
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina los permisos de la GitHub App, el flujo de incorporación y retiro de ayudantes, y si R2.4.8/R2.7.4 dependen de que el ayudante tenga cuenta de GitHub y acceso a la organización; la descarga añade además implicaciones de almacenamiento y auditoría.
- **Opciones:**
  - Solo enlaces a GitHub + ayudantes como miembros de la organización con lectura
  - Enlaces a GitHub + colaborador de lectura por repositorio
  - Visor de código dentro de la app (sin cuenta GitHub del ayudante)
  - Descarga zip bajo demanda servida por la app
  - Zip almacenado al capturar el snapshot
  - Combinación de enlace y visor/descarga
- **Estudio de APIs:** §7.5 y §10.2 asumen el link https://github.com/ORG/REPO/tree/<SHA> y proponen solo links tree/compare/commits; §3.4 solo menciona quitar al ayudante de la organización y no trata cómo se le da acceso de lectura; §8 y §10.2 no mencionan zipball.
- **Fusiona:** P375, P327

### Q-2.4-32 — ¿Se ofrece comparación entre versiones (compare/<sha1>...<sha2>) entre entregas consecutivas y contra el commit inicial del repositorio base? ¿Cuál es la "base" de la comparación para la primera entrega cuando no hubo repositorio base (solo commit de auto_init)? ¿Funciona `compare` con SHAs no alcanzables desde refs?

- **Requisitos:** R2.4.6, R2.4.8, R2.5.9
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el alcance de R2.4.8 más allá del link a una versión y una posible métrica adicional de R2.5.9.
- **Opciones:**
  - Sin comparación entre versiones
  - Comparación entre entregas consecutivas
  - Comparación contra el commit inicial del repositorio base
  - Ambas, con la base configurable por entrega
- **Estudio de APIs:** §7.5 sugiere `compare` entre entregas como candidato a R2.5.9.
- **Fusiona:** P376

### Q-2.4-33 — Si dos entregas de la misma tarea capturan el mismo SHA (no hubo actividad entre ellas), o si para algún sujeto la fecha efectiva de la entrega "final" resulta anterior a la de una parcial (por overrides o extensiones cruzadas), ¿se acepta, se alerta al equipo docente, o se bloquea? ¿La UI indica "sin cambios respecto a la entrega anterior"? En el mismo escenario, cuando la extensión de un estudiante en la entrega 1 cae después de la fecha de la entrega 2 o las fechas de distintas secciones se cruzan, ¿cómo se definen los "períodos" de actividad por entrega de R2.5.7 para ese sujeto (por sujeto/grupo, con intervalos no disjuntos, o declarando el caso inválido) y puede el snapshot de la entrega 2 quedar cronológicamente antes que el de la 1?

- **Requisitos:** R2.4.3, R2.4.6, R2.3.2, R2.5.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.4.6 exige independencia entre versiones; con fechas cruzadas los períodos por entrega dejan de ser intervalos disjuntos y el orden de las entregas por sujeto puede invertirse, afectando métricas, snapshots y la corrección.
- **Opciones:**
  - Aceptar el mismo SHA en dos entregas y marcarlo como "sin cambios respecto a la entrega anterior"
  - Alertar al equipo docente sin bloquear
  - Bloquear la configuración que produce fechas invertidas
  - Calcular los períodos por sujeto aceptando intervalos solapados
  - Calcular los períodos con las fechas base de la entrega, ignorando extensiones
  - Declarar el caso inválido y advertir al profesor
- **Estudio de APIs:** §7.5 indica una fila por (delivery, repository) que nunca se sobrescribe, sin tratar SHAs iguales ni el orden invertido; §8.5 filtra commits por [entrega_anterior.due, entrega_actual.due] y no considera solapes por extensiones.
- **Fusiona:** P356, P335

### Q-2.4-34 — Además del snapshot al cierre, ¿se registra una versión "última" para tolerancia de atrasos: un segundo snapshot a lock_at, un puntero al HEAD actual con "N commits después del cierre", o nada? ¿Se calcula el atraso (fecha del último commit − fecha de cierre) y se refleja en Canvas (late_policy_status, comentario en la submission) o solo dentro de la app?

- **Requisitos:** R2.4.5, R2.4.7, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si la app soporta políticas de atraso del profesor y qué se muestra al corrector junto a la versión oficial.
- **Opciones:**
  - Solo snapshot al cierre
  - Snapshot al cierre + snapshot a lock_at
  - Snapshot al cierre + HEAD actual y conteo de commits posteriores
  - Configurable por tarea
  - Reflejar el atraso en Canvas (late_policy_status o comentario)
  - Mostrar el atraso solo en la app
- **Estudio de APIs:** §10.4 lista submission[late_policy_status] sin vincularlo a snapshots; §7.5 captura una sola versión por entrega.
- **Fusiona:** P374

### Q-2.4-35 — Al capturar la versión, ¿se informa al estudiante o al grupo por Canvas (comentario en la submission con SHA, tag y link, o conversación) indicando qué versión será corregida, incluido el caso "sin commits"? ¿Es un flag activable por tarea (R2.6.7) o un comportamiento fijo?

- **Requisitos:** R2.4.5, R2.6.7, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija el nivel de transparencia hacia el estudiante y agrega un evento adicional al outbox de comunicaciones.
- **Opciones:**
  - No avisar al capturar
  - Comentario en la submission con SHA, tag y link
  - Conversación individual o de grupo en Canvas
  - Aviso solo cuando el resultado es "sin commits"
  - Flag activable por tarea (R2.6.7)
- **Estudio de APIs:** §9.4 no incluye un evento "snapshot capturado" entre los flags; §10.4 sugiere un comentario con el SHA solo al momento de calificar.
- **Fusiona:** P383

### Q-2.4-36 — ¿La app registra algo en Canvas como "entrega" al momento del cierre (comentario en la submission, submission de tipo online_url con el link a tree/<sha>) o la tarea de Canvas queda sin submissions y solo recibe la nota? ¿Qué submission_types debe tener configurada la tarea de Canvas de cada entrega, y cómo se evita que una política de "missing submission" de Canvas asigne 0 automáticamente a los estudiantes sin submission después de la fecha, aunque la app haya capturado su versión?

- **Requisitos:** R2.4.5, R2.7.6, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Una configuración inadecuada de la tarea en Canvas puede calificar automáticamente con 0 o mostrar "faltante" a todos los estudiantes, aunque la app haya capturado correctamente su versión.
- **Opciones:**
  - No registrar submission; solo la nota al calificar
  - Comentario en la submission con el link a la versión
  - Submission de tipo online_url con el link a tree/<sha>
  - Exigir submission_types específicos y documentarlo como requisito de configuración del curso
  - Documentar que el profesor debe desactivar la política de "missing submission"
- **Estudio de APIs:** §5.7 usa un comentario en la submission para la URL del repositorio; §10.4 califica sin exigir submission; no aborda las políticas de faltantes.
- **Fusiona:** P384

## Cambios posteriores, recalculo y recaptura

### Q-2.4-37 — Cuando Canvas cambia la fecha efectiva de una entrega DESPUÉS de que la app ya capturó la versión (extensión otorgada tarde, corrección de un error, nuevo override), ¿la app recaptura automáticamente con la nueva fecha, pide confirmación al profesor, o nunca modifica lo ya registrado y solo alerta? Si recaptura, ¿se conserva el snapshot anterior como historial (SUPERSEDED) con su tag, o se descarta? ¿Aplica la misma política cuando la fecha se ADELANTA o se retira una extensión —caso en que el SHA registrado puede incluir commits posteriores al nuevo cierre— o la política es asimétrica? ¿Quién aprueba la recaptura y queda registrado? Y si un corrector ya inició o terminó la corrección sobre el SHA anterior, ¿se bloquea la recaptura automática y la manual, y qué ve el corrector (aviso, diff entre el snapshot anterior y el nuevo, estado "requiere re-revisión")?

- **Requisitos:** R2.4.3, R2.4.4, R2.4.5, R2.4.7, R2.7.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es el conflicto directo entre R2.4.4 (mantener las fechas actualizadas) y R2.4.7 (mantener correctamente las versiones ya registradas); define la máquina de estados del snapshot, su versionado, las reglas de bloqueo durante la corrección y los estados de la entrega por sujeto.
- **Opciones:**
  - Nunca recapturar automáticamente; alertar y permitir recaptura manual con auditoría
  - Recapturar automáticamente si la nueva fecha es posterior, conservando la versión anterior como historial
  - Recapturar siempre y descartar la anterior
  - Recapturar solo con confirmación explícita del profesor
  - Recapturar automáticamente salvo que la corrección ya haya iniciado
  - Política simétrica para adelantos y retiros de extensión
  - Política asimétrica: recapturar solo ante extensiones, alertar ante adelantos
  - Estado "requiere re-revisión" con diff entre la versión corregida y la nueva
- **Estudio de APIs:** §7.4 reprograma el job de snapshot solo si cambió la fecha de una entrega "NO capturada aún"; el caso post-captura, el adelanto de fecha y la interacción con la corrección no se abordan.
- **Fusiona:** P328, P357, P358, P373

### Q-2.4-38 — ¿Se permite a algún rol capturar manualmente ("capturar ahora"), recapturar, o fijar a mano un SHA o una fecha distinta para un sujeto (acuerdo informal de atraso, error de fecha, rama equivocada)? Si sí, ¿se conserva la versión automática original como histórico (R2.4.7), quién queda registrado como responsable, con qué auditoría (quién, cuándo, motivo) y marcado como "manual" frente a los automáticos, qué permiso de los que define R2.1.8 lo habilita, y se notifica al corrector asignado y al estudiante?

- **Requisitos:** R2.4.5, R2.4.7, R2.4.8, R2.1.8, R2.7.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si existe una vía de escape manual sobre el snapshot automático, cómo se preserva la trazabilidad y el equilibrio entre R2.4.7 (no alterar) y la operación real; afecta RBAC, UI y auditoría.
- **Opciones:**
  - Sin captura ni recaptura manual
  - Solo "capturar ahora" (adelantar el job), sin elegir SHA ni fecha
  - Recaptura manual con fecha alternativa
  - Fijación manual de un SHA específico
  - Habilitado solo para el profesor
  - Habilitado para profesor y co-profesor, no para ayudantes
  - Siempre con auditoría (quién, cuándo, motivo) y marca "manual"
  - Con notificación al corrector asignado y al estudiante
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P336, P372

### Q-2.4-39 — Si la composición de un grupo o la sección de un estudiante cambian en Canvas después de calcular las fechas efectivas (entra un integrante con extensión, sale uno, el grupo se elimina o se renombra, el estudiante se cambia de sección), ¿se recalcula la fecha del repositorio o del sujeto, y qué instante rige: la sección/grupo vigente al momento del cierre, la vigente al momento de la captura, o la del último sync? ¿Se registra el cambio en el historial de fechas del sujeto? ¿Y cómo se manejan los overrides con datos inconsistentes respecto de lo sincronizado: `course_section_id` de una sección desconocida (creada tras el sync), `student_ids` de estudiantes no inscritos, `group_id` de un grupo que ya no existe o que pertenece a otra group_category, overrides sin due_at ni lock_at? ¿Se ignoran, se registran advertencias visibles, o disparan un re-sync? ¿Qué orden de sincronización se fija (secciones y grupos antes que overrides)?

- **Requisitos:** R2.4.2, R2.4.3, R2.4.4, R2.4.5, R2.2.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el instante de evaluación de la regla de fecha y evita capturas inconsistentes cuando el cambio ocurre cerca del cierre o cuando el snapshot usaría una fecha derivada de un integrante que ya no está; además fija la robustez del cálculo ante datos sucios y el orden de sincronización.
- **Opciones:**
  - Recalcular en cada sync mientras la entrega no esté capturada; congelar tras la captura
  - Recalcular siempre y aplicar las reglas de recaptura
  - Congelar la fecha efectiva al momento del cierre y no recalcular
  - Usar la sección/grupo según el último sync anterior a la captura
  - Override con target desconocido: ignorar silenciosamente
  - Override con target desconocido: ignorar y registrar advertencia visible
  - Override con target desconocido: disparar un re-sync de secciones/grupos y reintentar
- **Estudio de APIs:** no lo aborda (§4.4 solo indica "no borrar, marcar deleted_at" al sincronizar).
- **Fusiona:** P343, P344, P387

### Q-2.4-40 — ¿Se captura la versión para un estudiante cuyo enrollment está en estado deleted, inactive o completed al momento del cierre? Si se retira después de capturada, ¿se conserva el snapshot, se muestra como "retirado" en la lista de corrección, se excluye de los informes? En tareas grupales, ¿el retiro de un integrante cambia la fecha efectiva del repositorio?

- **Requisitos:** R2.4.5, R2.2.1, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina qué sujetos entran al job de captura y a la asignación de correctores; evita corregir a estudiantes retirados y evita perder la evidencia de uno que se retira después de entregar.
- **Opciones:**
  - Capturar igual y marcar "retirado"
  - No capturar; estado "RETIRADO" y excluido de la corrección
  - Capturar solo si el retiro ocurrió después del cierre
  - Conservar el snapshot siempre, excluyéndolo de los informes agregados
- **Estudio de APIs:** §4.4 y §14 indican no borrar repositorios ni historia y marcar al estudiante como retirado; no dicen si se captura ni cómo se muestra.
- **Fusiona:** P345

### Q-2.4-41 — Si al llegar la fecha de cierre el repositorio aún no existe (estado PENDING_MAPPING, ERROR, invitación no aceptada) o el estudiante fue inscrito o mapeado a GitHub después de una fecha de cierre ya pasada, ¿qué se registra para esa (entrega, sujeto): un estado terminal como "SIN REPOSITORIO AL CIERRE" o "INSCRITO TRAS EL CIERRE" con acción manual "capturar ahora", una captura automática con `until` histórico cuando el repositorio aparezca (resultado previsible: vacío o solo commit inicial) marcada como "repo creado después del cierre", o una fecha individual definida por el profesor en la app? ¿Cómo se muestra en R2.5.6 y en las alertas de R2.6.2, y hay algo que corregir?

- **Requisitos:** R2.4.5, R2.4.6, R2.3.10, R2.3.11, R2.5.6, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El job de captura itera sobre (entrega, repositorio); sin repositorio no hay fila. Define el estado resultante, evita falsos "sin entrega" en dashboard e informes y determina si la app admite fechas individuales propias fuera de Canvas.
- **Opciones:**
  - Estado terminal ("SIN REPOSITORIO AL CIERRE" / "INSCRITO TRAS EL CIERRE") con acción manual "capturar ahora"
  - Captura automática al aparecer el repositorio, con until histórico
  - Captura automática marcando "repo creado después del cierre"
  - Captura manual o fecha individual definida en la app
- **Estudio de APIs:** §7.5 solo define NO_COMMITS y CAPTURED; §5.5 define los estados del repositorio sin su interacción con el cierre; el caso de inscripción posterior no lo aborda.
- **Fusiona:** P346, P347

### Q-2.4-42 — Si un estudiante cambia de grupo en Canvas entre la entrega parcial y la final, ¿su entrega final se captura en el repositorio del nuevo grupo mientras la parcial permanece asociada al repositorio antiguo? ¿El snapshot se ancla al sujeto o al repositorio? ¿Cómo lo ve el corrector y cómo se refleja en la lista de entregas del estudiante?

- **Requisitos:** R2.4.6, R2.3.4, R2.2.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.3.4 exige un único conjunto de repositorios por tarea, pero un cambio de grupo rompe la correspondencia sujeto–repositorio entre entregas; define el modelo de snapshots por sujeto vs por repositorio.
- **Opciones:**
  - Snapshot anclado al repositorio: la parcial queda en el repositorio antiguo
  - Snapshot anclado al sujeto: se muestran ambas entregas en la ficha del estudiante con su repositorio de origen
  - Bloquear el cambio de grupo entre entregas y exigir intervención del profesor
  - Permitir el cambio y marcar la entrega afectada con una advertencia visible al corrector
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P391

### Q-2.4-43 — Si la tarea de Canvas vinculada a una entrega se elimina (404 / workflow_state=deleted) o se despublica después de la vinculación, ¿qué ocurre con la entrega: se marca como "huérfana", se bloquea o cancela la captura pendiente, se conservan los snapshots ya capturados, se notifica al equipo docente?

- **Requisitos:** R2.4.1, R2.4.4, R2.4.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define estados de la entrega y evita que el sync falle o borre datos ante un 404 de Canvas.
- **Opciones:**
  - Marcar la entrega como "huérfana" y suspender la captura pendiente
  - Conservar todo y solo alertar, manteniendo la captura programada
  - Cancelar la entrega conservando los snapshots ya capturados
  - Exigir al profesor re-vincular o eliminar la entrega en la app
- **Estudio de APIs:** §5.1 indica no crear repositorios para tareas no publicadas; no aborda la eliminación posterior a la vinculación.
- **Fusiona:** P368

### Q-2.4-44 — ¿Qué validaciones sobre fechas se aplican al vincular una tarea de Canvas y en cada sincronización: lock_at < due_at, unlock_at > due_at, entrega final con fecha anterior a una parcial, dos entregas con la misma fecha, y tarea de Canvas cuya fecha ya pasó al momento de vincular? En este último caso, ¿se captura de inmediato con `until` histórico, se pide confirmación al profesor, o se marca la entrega como "vinculada tras el cierre"? Cada validación, ¿bloquea, advierte o se ignora?

- **Requisitos:** R2.4.1, R2.4.5, R2.3.1, R2.3.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define el flujo de creación de tarea en cuanto a fechas —presente ya en la demo parcial— y evita capturas sorpresa en el momento de vincular.
- **Opciones:**
  - Bloquear la vinculación ante fechas inconsistentes
  - Advertir y permitir continuar, registrando la advertencia
  - Ignorar las inconsistencias y capturar según la fecha vigente
  - Tarea ya cerrada: capturar de inmediato con until histórico
  - Tarea ya cerrada: pedir confirmación explícita al profesor
  - Tarea ya cerrada: marcar "vinculada tras el cierre" sin capturar
- **Estudio de APIs:** no lo aborda (§5.2 solo valida group_category_id entre entregas).
- **Fusiona:** P381

## Integridad, manipulacion y fallos de infraestructura

### Q-2.4-45 — Si se detecta un push posterior al cierre que contiene commits con fecha anterior al cierre, o una reescritura de historia (force-push) sobre la rama considerada, ¿cómo se refleja: alerta al corrector en la vista de la entrega, exclusión de esos commits, recaptura, inclusión en el informe diario, mensaje al estudiante? ¿Se registra el evento con su evidencia (before/after, pusher, hora) y por cuánto tiempo se conserva?

- **Requisitos:** R2.4.7, R2.4.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define los criterios de aceptación de la detección de manipulación y qué evidencia se conserva para la actividad de validación y para posibles reclamos.
- **Opciones:**
  - Registrar el evento y alertar al corrector en la vista de la entrega
  - Excluir del snapshot los commits cuyo push llegó después del cierre
  - Recapturar aplicando la política de recaptura
  - Incluirlo como sección del informe diario
  - Notificar al estudiante
  - Solo registrar el evento sin comunicarlo
- **Estudio de APIs:** no lo aborda (el payload push con before/after/pusher aparece en §8.1 solo para métricas).
- **Fusiona:** P352

### Q-2.4-46 — ¿Se detecta el borrado o el movimiento de un tag de entrega por parte del estudiante (evento webhook `delete` con ref_type=tag, o verificación periódica con GET /git/ref/tags/...) y qué se hace: recrear el tag desde el SHA guardado, notificar al equipo docente, registrar el incidente en el timeline del repositorio, avisar al estudiante, o impedirlo con un ruleset de tags?

- **Requisitos:** R2.4.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Con permiso de push los estudiantes pueden borrar tags; define el mecanismo de auto-reparación y si el hecho es información relevante para el corrector.
- **Opciones:**
  - Recrear silenciosamente en el próximo barrido
  - Recrear + registrar incidente visible al corrector
  - Solo registrar, sin recrear
  - Impedir con ruleset de tags
- **Estudio de APIs:** §7.5 advierte que los estudiantes pueden borrar tags y que el SHA en BD protege; no define detección ni reparación.
- **Fusiona:** P354

### Q-2.4-47 — GitHub rechaza escrituras (incluida la creación de tags vía POST /git/refs) en repositorios archivados. Si el equipo decide archivar los repositorios al cerrar la tarea o el curso, ¿en qué momento se archiva respecto del último snapshot, de las recapturas por cambio de fecha y de los snapshots manuales? Si un owner archiva un repositorio a mano antes del cierre, ¿el job registra solo el SHA en base de datos y marca "tag no creado (repositorio archivado)", desarchiva temporalmente vía PATCH para crear el tag, o pasa el snapshot a ERROR?

- **Requisitos:** R2.4.5, R2.4.7, R2.3.7
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita que el archivado —propuesto para proteger la evidencia— impida registrar la versión de cierre; define un sub-estado del snapshot.
- **Opciones:**
  - Archivar solo tras el último snapshot + N días
  - Registrar el SHA sin tag y marcar advertencia
  - Desarchivar temporalmente para crear el tag y volver a archivar
  - Pasar el snapshot a ERROR y requerir acción manual
  - No archivar repositorios
- **Estudio de APIs:** §7.5 crea tags sin considerar repositorios archivados; §14 no lo menciona.
- **Fusiona:** P326

### Q-2.4-48 — Si al momento del cierre el refresh token de Canvas del profesor está revocado o expirado (las fechas llevan X horas sin sincronizar) o la GitHub App fue desinstalada de la organización, ¿el job captura igual con las últimas fechas conocidas marcando "fechas posiblemente desactualizadas", suspende la captura y alerta, o bloquea la entrega? ¿Cuál es el umbral de antigüedad aceptable del último sync exitoso para considerar válida una captura?

- **Requisitos:** R2.4.4, R2.4.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la resiliencia del proceso automático y los estados de alerta visibles; el snapshot depende de GitHub (token de la App) mientras que la fecha depende de Canvas (token del profesor), y ambos pueden fallar por separado.
- **Opciones:**
  - Capturar igual con las últimas fechas conocidas y marcar "fechas posiblemente desactualizadas"
  - Suspender la captura, alertar y reintentar cuando se restablezca la credencial
  - Bloquear la entrega hasta intervención del profesor
  - Umbral de antigüedad configurable a partir del cual la captura se marca o se suspende
- **Estudio de APIs:** §1.1 advierte que sin refresh token guardado R2.4.5 no funciona de madrugada; no define el comportamiento ante el fallo.
- **Fusiona:** P379

### Q-2.4-49 — ¿Qué ocurre con la versión registrada y con su acceso cuando el repositorio usa Git LFS (los archivos aparecen como punteros en tree/<sha> y en el zipball), contiene submódulos (código externo no incluido), incluye archivos mayores a 100 MB rechazados por GitHub, o supera el tamaño recomendado (~1 GB)? ¿La app detecta .gitattributes/.gitmodules y marca el snapshot con una advertencia para el corrector, documenta la limitación en el mensaje inicial al estudiante ("no uses LFS ni submódulos"), o no hace nada? Verificar qué devuelve GET zipball para un repositorio con LFS.

- **Requisitos:** R2.4.5, R2.4.8, R2.5.10, R2.7.4
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El corrector podría revisar una versión incompleta sin saberlo; el spec debe fijar si se trata de una limitación documentada o de un caso detectado y señalizado.
- **Opciones:**
  - Detectar y advertir en el snapshot y en la vista de corrección
  - Documentar como limitación y avisar al estudiante al crear el repositorio
  - No manejar el caso
- **Estudio de APIs:** §5.3 solo trata los límites de GET /contents; no aborda LFS, submódulos ni el tamaño de los repositorios en los snapshots.
- **Fusiona:** P392

## Ya respondidas por el enunciado

Ninguna. Las 74 preguntas de entrada del area 2.4 (P325–P397 y N036) fueron marcadas ABIERTA en la etapa de verificacion: ninguna quedo respondida por el texto del enunciado, por lo que todas permanecen en el cuerpo del documento.
