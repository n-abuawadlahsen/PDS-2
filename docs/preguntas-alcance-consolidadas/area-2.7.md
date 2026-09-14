# Preguntas de alcance — Area 2.7

69 preguntas finales, fusionadas desde 84 de entrada, 7 bloqueantes para la parcial.

## Modelo y alcance de la corrección (decisiones estructurales)

### Q-2.7-01 — ¿Cuál es la unidad que se asigna a un corrector y con qué grano se persisten la asignación y el registro de corrección: cada ENTREGA de cada estudiante/grupo (entrega × repositorio), la TAREA completa (el mismo corrector revisa todas las entregas parciales y finales de ese estudiante/grupo), o el par (entrega, estudiante)?

Si la asignación es por entrega, ¿existe la acción "copiar la asignación de la entrega anterior"? Cuando el assignment tiene `grade_group_students_individually=true` y cada integrante recibe nota propia, ¿se crea un registro de corrección por integrante compartiendo `rubric_assessment` y comentario, un único registro con las notas por integrante en JSON, o se bloquea la corrección desde la app para tareas grupales con notas individuales? ¿Cómo se representa el estado agregado "corregida" de un repositorio cuando falta publicar la nota de un integrante, y qué ocurre con el integrante que ya no pertenece al grupo al momento de publicar?

- **Requisitos:** R2.7.1, R2.7.6, R2.7.7, R2.3.2, R2.3.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define las claves del modelo de datos de corrección (delivery_id+repository_id vs assignment_id+repository_id vs entrega+estudiante), la UI de asignación (una pantalla por entrega vs una por tarea), el número de llamadas PUT a Canvas por entrega y el cálculo del estado de R2.7.7.
- **Opciones:**
  - Por entrega, independiente
  - Por tarea, heredado a todas sus entregas
  - Por entrega con acción "copiar asignación de la entrega anterior"
  - Grano repositorio con notas por integrante en JSON
  - Grano estudiante con rúbrica y comentario compartidos
  - Bloquear desde la app las tareas grupales con notas individuales
- **Estudio de APIs:** §10.1 propone `grading_assignment(delivery_id, repository_id, grader_user_id, status)`, es decir grano entrega × repositorio y sin herencia entre entregas de una misma tarea; §10.4 advierte que con el flag en true hay que llamar por cada integrante.
- **Fusiona:** P547, P622

### Q-2.7-02 — ¿Puede una misma entrega tener más de un corrector (co-corrección, segunda revisión, moderación del profesor)?

Si se admite más de uno, ¿qué roles existen por asignación (principal, revisor de solo lectura, moderador), quién publica la nota definitiva a Canvas y cómo se resuelven las discrepancias entre correctores?

- **Requisitos:** R2.7.1, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Un solo corrector simplifica el modelo (clave foránea única); varios exigen roles por asignación, estados adicionales y una regla de consolidación de la nota.
- **Opciones:**
  - Exactamente uno
  - Uno principal + revisores de solo lectura
  - Varios con moderación final del profesor
- **Estudio de APIs:** §10.1: el modelo tiene un único `grader_user_id` por fila, lo que implica un corrector por entrega.
- **Fusiona:** P550

### Q-2.7-03 — ¿La app solo MUESTRA la rúbrica de Canvas (lectura, con enlace a SpeedGrader para evaluar allí) o permite EVALUARLA criterio por criterio desde la app (elegir rating, puntos y comentario por criterio) y envía `rubric_assessment` al publicar?

¿Existe una opción intermedia en la que se muestra la rúbrica como referencia pero la nota se ingresa como un valor único con comentario, sin enviar `rubric_assessment`?

- **Requisitos:** R2.7.5, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es la decisión de alcance más grande de 2.7: determina la complejidad de la pantalla de corrección, el payload de publicación y el volumen de validaciones previas.
- **Opciones:**
  - Solo lectura + enlace a SpeedGrader
  - Evaluación completa desde la app (criterio por criterio, envía `rubric_assessment`)
  - Lectura + nota numérica + comentario, sin `rubric_assessment`
- **Estudio de APIs:** §10.3 recomienda una "grilla clickeable (criterios × ratings)" y §10.4 muestra el payload `rubric_assessment[...]`; el estudio marca esta recomendación como no aprobada por el equipo.
- **Fusiona:** P572

### Q-2.7-04 — ¿Existe el concepto de BORRADOR local (la corrección se guarda en la app y llega a Canvas con una acción explícita "Publicar"), o cada guardado se escribe directamente en Canvas?

¿Existe además una publicación masiva ejecutada por el profesor ("revisar todo y publicar de una vez") además de la publicación individual del corrector?

- **Requisitos:** R2.7.6, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la distinción entre los estados "corregida" y "publicada", el botón principal de la pantalla de corrección y si existe un paso de revisión previa del profesor antes de que la nota llegue a Canvas.
- **Opciones:**
  - Borrador local + publicación explícita por el corrector
  - Escritura directa a Canvas en cada guardado
  - Borrador local + publicación masiva ejecutada por el profesor
- **Estudio de APIs:** §10.4 menciona `POST .../update_grades` (masivo y asíncrono, con objeto `Progress`); §10.1 propone los estados "pendiente / en curso / listo".
- **Fusiona:** P587

### Q-2.7-05 — Dentro de los ≥3 permisos que exige R2.1.8, ¿cuáles gobiernan exactamente las acciones de 2.7 (abrir la vista de corrección de una entrega NO asignada, ver el código, ver rúbrica, notas y comentarios de otros correctores, publicar en Canvas, asignar y reasignar) y qué puede ver un ayudante sin permiso de corrección?

¿Un ayudante puede ver, en solo lectura, las entregas asignadas a OTROS ayudantes con sus notas y comentarios, o únicamente las propias? ¿El profesor tiene una vista consolidada por corrector con el avance de cada uno?

- **Requisitos:** R2.1.8, R2.7.2, R2.7.5, R2.7.6, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** El modelo de permisos se define y demuestra desde la parcial y debe contemplar las acciones de corrección para no rehacerlo; además fija las reglas de autorización a nivel de fila y el alcance de la vista de estado (R2.7.7).
- **Opciones:**
  - Solo las propias; el profesor ve todo
  - Lectura de entregas ajenas para todos los ayudantes; escritura solo en las propias
  - Lectura de entregas ajenas solo para un rol de ayudante jefe
  - Permiso separado para ver el código de entregas no asignadas
- **Estudio de APIs:** §3.4 propone `grading.assign` (profesor y ayudante jefe) y `grading.submit` para el ayudante "(solo asignadas)"; no define reglas de lectura de entregas ajenas.
- **Fusiona:** P563, P606

## Asignación de correctores (R2.7.1)

### Q-2.7-06 — ¿Qué modos y mecánicas de asignación se implementan, y cuáles son obligatorios para la entrega final: manual uno a uno (select por fila), selección múltiple + "asignar a…", arrastrar y soltar, reparto automático equitativo, por sección, por grupo o categoría de grupos, por lista de carga por ayudante, importación CSV?

¿Se puede reasignar en bloque? ¿Cuál es el flujo de confirmación y qué se muestra antes de aplicar un reparto automático (previsualización del resultado, deshacer)?

- **Requisitos:** R2.7.1, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cada modo es un flujo de UI y un algoritmo distinto; fija el alcance de R2.7.1 y los criterios de aceptación de la pantalla de distribución del trabajo.
- **Opciones:**
  - Solo manual
  - Manual + aleatoria equitativa
  - Manual + equitativa + por sección
  - Manual + equitativa + por sección + cuotas por ayudante
  - Cualquiera de las anteriores + importación CSV
  - Cualquiera de las anteriores + reasignación en bloque
- **Estudio de APIs:** §10.1 propone "asignación manual (drag & drop o selects) + automática (repartir equitativamente, o por sección)", sin fijar cuáles son obligatorias; §10.5 propone mostrar el doble contador "18/25 corregidas en la app · 17/25 con nota en Canvas".
- **Fusiona:** P548, P621

### Q-2.7-07 — En la asignación "equitativa o balanceada", ¿qué métrica se balancea: número de entregas por corrector, número de estudiantes (un grupo de 4 pesa más que un individual), carga acumulada en otras entregas o tareas del curso, o una capacidad configurable por ayudante (por ejemplo, el ayudante jefe corrige 0)?

¿El balance es global en el curso o dentro de cada sección? ¿Cómo se verifica en la aceptación que el reparto es "justo"?

- **Requisitos:** R2.7.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina el algoritmo de reparto, los parámetros de la UI (capacidades, exclusiones) y el criterio con que se demostrará el requisito.
- **Opciones:**
  - Igual número de entregas
  - Igual número de estudiantes
  - Ponderado por carga previa
  - Capacidad configurable por ayudante
  - Balance por sección en lugar de global
- **Estudio de APIs:** §10.1 dice "repartir equitativamente" sin definir la métrica.
- **Fusiona:** P549

### Q-2.7-08 — ¿Quiénes son elegibles como correctores: solo ayudantes, o también los profesores del curso, incluidos los co-profesores incorporados según R2.1.7?

¿El profesor puede auto-asignarse entregas? ¿Basta pertenecer al curso o se requiere un permiso específico de corrección dentro de los ≥3 permisos de R2.1.8? ¿La vista "mis entregas asignadas" (R2.7.2) también aplica a profesores?

- **Requisitos:** R2.7.1, R2.1.7, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la lista de candidatos que aparece en la pantalla de asignación y si la vista del corrector es exclusiva de los ayudantes.
- **Opciones:**
  - Solo ayudantes
  - Ayudantes + profesores y co-profesores
  - Cualquier miembro del equipo docente con el permiso de corrección
- **Estudio de APIs:** §3.4 propone `grading.submit` para profesor, ayudante jefe y ayudante (solo asignadas); no dice si el profesor aparece como corrector asignable.
- **Fusiona:** P551

### Q-2.7-09 — ¿Quién puede asignar y reasignar entregas: solo los profesores, o también un rol de ayudante con permiso de asignación (por ejemplo "ayudante jefe")?

¿Puede un ayudante "tomar" entregas del conjunto de no asignadas (auto-asignación) o solo recibe lo que se le asigna?

- **Requisitos:** R2.7.1, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija qué permiso de R2.1.8 gobierna R2.7.1 y si existe un flujo de auto-servicio para ayudantes.
- **Opciones:**
  - Solo profesores
  - Profesores + rol con permiso `grading.assign`
  - Además, auto-asignación desde el conjunto no asignado
- **Estudio de APIs:** §3.4 propone `grading.assign` para profesor y ayudante jefe; el enunciado dice literalmente "permitir al profesor asignar".
- **Fusiona:** P552

### Q-2.7-10 — ¿Se puede asignar correctores ANTES del cierre de la entrega, cuando aún no existe snapshot, o solo después de capturada la versión? Y si un estudiante o grupo obtiene su repositorio DESPUÉS de hecha la asignación (mapeo tardío) o no tiene repositorio al cierre (estado PENDING_MAPPING/ERROR), ¿aparece en la lista de asignación?

Si se permite asignar antes del cierre, ¿la asignación queda "latente" y se activa al capturarse el snapshot? Para los sujetos que aparecen tarde: ¿quedan "sin asignar" con alerta al profesor, se asignan automáticamente al corrector con menos carga, o se excluyen hasta tener repositorio?

- **Requisitos:** R2.7.1, R2.7.7, R2.4.5, R2.3.10, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cambia el momento del ciclo de la tarea en que aparece la pantalla de asignación, el estado inicial de la asignación y el comportamiento incremental que evita dejar sujetos sin corrector.
- **Opciones:**
  - Solo después del snapshot
  - Antes del cierre, con asignación latente que se activa al capturar
  - Sujetos tardíos quedan sin asignar con alerta al profesor
  - Sujetos tardíos se asignan automáticamente al corrector con menos carga
  - Sujetos tardíos se excluyen hasta tener repositorio
- **Estudio de APIs:** §5.5 describe la creación progresiva de repositorios pero no su efecto sobre asignaciones ya hechas; el resto no lo aborda.
- **Fusiona:** P555, P556

### Q-2.7-11 — Al construir la lista de sujetos a asignar (R2.7.1) y el estado de corrección (R2.7.7), ¿qué sujetos se incluyen y con qué marca, considerando el estado previo en Canvas y los casos en que Canvas no permite calificar?

¿La app lee la submission previa en Canvas (`excused=true`, `late_policy_status=missing`, `workflow_state=graded` puesta en SpeedGrader) para excluir o marcar esos sujetos, o los trata como al resto? ¿Un estudiante excusado aparece como "excusado (Canvas)" sin consumir un corrector? ¿Se excluyen el Test Student y los estudiantes para quienes la entrega no existe (`only_visible_to_overrides=true` sin override)? ¿Se cruza con `gradeable_students` de Canvas para decidir a quién se puede calificar? ¿Con qué frecuencia y con qué endpoint se refresca ese estado antes de ejecutar la asignación automática?

- **Requisitos:** R2.7.1, R2.7.6, R2.7.7, R2.4.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define qué sujetos entran en el reparto de correctores, sus estados iniciales en R2.7.7, una lectura adicional de Canvas en la sincronización y evita contar o asignar sujetos que Canvas no permite calificar.
- **Opciones:**
  - Ignorar el estado previo en Canvas
  - Excluir excusados y ya calificados
  - Incluirlos marcados, sin asignar corrector por defecto
  - Excluir siempre Test Student y sujetos sin override
  - Cruzar con `gradeable_students` antes de asignar
- **Estudio de APIs:** §10.4 lista `submission[excuse]` como parámetro de escritura y menciona `gradeable_students`; §10.5 usa `submission_summary`; §7.3 indica que si la tarea no existe para un estudiante "no le creen snapshot ni lo cuenten como atrasado". No aborda leer el estado previo antes de asignar.
- **Fusiona:** P544, P607

### Q-2.7-12 — ¿Se permite reasignar una entrega que ya está "en progreso" o "corregida pero no publicada"?

¿Qué pasa con el borrador del corrector anterior: se conserva y lo ve el nuevo corrector, se descarta, o se bloquea la reasignación mientras exista? ¿Se guarda historial de reasignaciones (quién, cuándo, de quién a quién)?

- **Requisitos:** R2.7.1, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define las reglas de transición del estado de corrección y si el borrador es propiedad del corrector o de la entrega.
- **Opciones:**
  - Reasignación libre; el borrador se conserva y es visible para el nuevo corrector
  - Reasignación libre; el borrador se descarta
  - Reasignación bloqueada mientras haya trabajo en progreso
  - Con historial de reasignaciones auditable en cualquiera de los casos
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P553

### Q-2.7-13 — Al retirar a un ayudante (R2.1.9), ¿sus entregas pendientes vuelven a "sin asignar", se reasignan automáticamente de forma balanceada, o el flujo de retiro obliga al profesor a reasignarlas antes de confirmar?

¿Las entregas que ese ayudante ya publicó conservan su nombre como corrector histórico?

- **Requisitos:** R2.1.9, R2.7.1, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** El flujo de retiro, que ya existe desde la parcial, debe especificar qué hace con las asignaciones; sin regla, las entregas quedan huérfanas e invisibles.
- **Opciones:**
  - Vuelven a "sin asignar" con alerta
  - Reasignación automática balanceada
  - Retiro bloqueado hasta reasignar manualmente
- **Estudio de APIs:** §3.4 dice "reasignen las entregas que tenía pendientes" (recomendación no aprobada, sin definir automático vs manual).
- **Fusiona:** P554

### Q-2.7-14 — Si la asignación de correctores se hizo "por sección" o por grupo y luego un estudiante cambia de sección o de grupo en Canvas, ¿su entrega se reasigna automáticamente al corrector de la nueva sección o grupo, permanece con el corrector original, o se marca "requiere reasignación" con alerta?

¿La regla es la misma si el cambio ocurre después de que el corrector ya empezó a corregir?

- **Requisitos:** R2.7.1, R2.2.2, R2.2.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija la regla de estabilidad de la asignación frente a eventos del roster y qué alertas aparecen en la vista de estado de corrección.
- **Opciones:**
  - Reasignar automáticamente
  - Mantener corrector original
  - Marcar para reasignación manual
- **Estudio de APIs:** §10.1 propone asignación manual o automática "equitativa o por sección"; no aborda cambios posteriores de sección o grupo.
- **Fusiona:** P541

### Q-2.7-15 — Si los repositorios son privados y el acceso del corrector es por enlace a GitHub, el ayudante debe ser miembro de la organización o colaborador de cada repositorio. ¿La app pide y guarda la cuenta GitHub de cada ayudante al incorporarlo y lo agrega automáticamente (a la organización como miembro, o a cada repositorio con permiso `pull`/`triage`)?

¿Qué pasa si un ayudante no tiene cuenta GitHub? ¿Se revoca el acceso al retirarlo (R2.1.9), y ese paso es manual o automático?

- **Requisitos:** R2.7.4, R2.1.8, R2.1.9
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Determina los campos del formulario de alta de ayudante (que existe desde la parcial), un paso adicional del worker de aprovisionamiento y el contenido del flujo de retiro.
- **Opciones:**
  - Miembro de la organización (una invitación por semestre)
  - Colaborador con permiso `pull` por repositorio
  - Sin acceso GitHub: el corrector trabaja solo con lo que expone la app
- **Estudio de APIs:** §14 indica crear los repositorios privados; §3.4 dice que al retirar a un ayudante hay que "revocar su acceso a la org si se lo dieron"; no describe cómo se les otorga.
- **Fusiona:** P568

## Vista del ayudante y navegación (R2.7.2, R2.7.3)

### Q-2.7-16 — ¿Cómo es la vista "mis entregas asignadas": es por curso o transversal a todos los cursos del ayudante, existe como home por rol fuera del árbol de cursos, qué columnas, filtros y orden por defecto tiene, y qué muestra cuando no hay nada que corregir?

Columnas candidatas: estudiante o grupo, sección, tarea, entrega, fecha de cierre efectiva, estado, fecha de asignación, enlace a la versión. Filtros candidatos: tarea, entrega, estado, sección. ¿Muestra un contador de progreso "X de Y corregidas"? ¿Qué ve un ayudante sin entregas asignadas, o con entregas cuya versión aún no fue capturada por un cierre futuro con extensión: un estado vacío con explicación, o las entregas listadas como "no disponible aún" con su fecha efectiva? ¿El ayudante debe siempre entrar curso → tarea → corrección, o existe una vista agregada de pendientes y alertas de todos sus cursos?

- **Requisitos:** R2.7.2, R2.7.3, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es la pantalla central del ayudante y la evidencia directa de R2.7.2 ("identificar fácilmente"); sin definirla no hay criterios de aceptación, y la respuesta determina si se necesita un modelo de "pendientes por usuario" que cruce cursos.
- **Opciones:**
  - Lista por curso únicamente
  - Vista transversal "Mis correcciones" como home del ayudante
  - Ambas (home transversal + lista dentro de cada curso)
  - Con estado vacío explicativo y entregas "no disponibles aún" listadas con su fecha efectiva
- **Estudio de APIs:** §10.1 propone una vista "Mis correcciones" filtrada por `grader_user_id` con estados "pendiente / en curso / listo", sin indicar si es por tarea, por curso o global, ni definir columnas y filtros.
- **Fusiona:** P562, P564, P618

### Q-2.7-17 — En la navegación siguiente/anterior entre entregas (R2.7.3), ¿cuál es el orden determinístico (alfabético, por sección, por estado), "siguiente" avanza al siguiente elemento de la lista o al siguiente PENDIENTE saltando los ya corregidos, qué atajos de teclado son obligatorios y la navegación se limita a la misma entrega de la misma tarea o cruza tareas y entregas?

¿La navegación respeta los filtros aplicados en la lista?

- **Requisitos:** R2.7.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es literalmente el contenido de R2.7.3; hay que fijar el comportamiento para poder demostrarlo y probarlo.
- **Opciones:**
  - Siguiente en lista + botón separado "siguiente pendiente"
  - Solo siguiente pendiente
  - Navegación con los filtros aplicados
  - Navegación limitada a la entrega actual vs navegación que cruza tareas
- **Estudio de APIs:** §10.1 sugiere "anterior / siguiente con atajos de teclado" y un botón "siguiente sin corregir".
- **Fusiona:** P565

### Q-2.7-18 — Si el corrector navega a otra entrega con cambios sin guardar o sin publicar, ¿la app autoguarda un borrador, pide confirmación explícita, o se pierde el trabajo?

- **Requisitos:** R2.7.3, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Depende de si existe el concepto de borrador local y define un comportamiento de UI clave para no perder correcciones en la pantalla más usada.
- **Opciones:**
  - Autoguardado de borrador al navegar
  - Confirmación explícita antes de salir
  - Sin protección: se pierde lo no guardado
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P566

### Q-2.7-19 — ¿Cuál es el layout de la pantalla de corrección y qué muestra en sus estados borde?

Elementos a definir: rúbrica de Canvas a un lado y enlace o resumen del snapshot al otro; botón "siguiente sin corregir"; atajos de teclado; guardado de borrador antes de publicar; indicador "en revisión por X" visible para otros correctores. Estados borde a definir: entrega sin snapshot (sin commits antes del cierre), tarea sin rúbrica en Canvas, y estudiante que ya tiene nota en Canvas puesta desde fuera de la app.

- **Requisitos:** R2.7.2, R2.7.3, R2.7.4, R2.7.5, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la pantalla más usada por los ayudantes y sus estados borde; R2.7.3 exige que la navegación sea "sencilla" y eso se evalúa sobre esta pantalla.
- **Opciones:**
  - Dos columnas (rúbrica / versión) con acciones fijas al pie
  - Pestañas (versión, rúbrica, comentario)
  - Con indicador "en revisión por X" vs sin él
- **Estudio de APIs:** §10.1 propone navegación anterior/siguiente con atajos y "siguiente sin corregir"; §10.2 sugiere mostrar "capturado el 16-09 16:30 · 47 commits"; §10.3 propone la rúbrica como grilla clickeable; §7.5 define el estado NO_COMMITS.
- **Fusiona:** P619

### Q-2.7-20 — Al corregir la entrega N de una tarea con múltiples entregas, ¿la pantalla muestra el contexto de las entregas anteriores del mismo estudiante o grupo (nota, comentario, SHA, corrector que la revisó) y el diff respecto a la entrega anterior?

- **Requisitos:** R2.7.3, R2.7.4, R2.3.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si la vista de corrección es por entrega aislada o con historial, lo que afecta las consultas al modelo de datos y el layout.
- **Opciones:**
  - Entrega aislada, sin historial
  - Panel de historial con notas y comentarios previos
  - Historial + diff con la entrega anterior
- **Estudio de APIs:** §7.5 sugiere el `compare` entre entregas como extra.
- **Fusiona:** P609

### Q-2.7-21 — ¿La pantalla de corrección permite guardar NOTAS INTERNAS del corrector (visibles solo para el equipo docente y nunca enviadas a Canvas) y banderas por entrega ("revisar con profesor", "posible copia", "caso especial")?

Si existen, ¿aparecen también en el estado de corrección (R2.7.7) y en el informe diario? ¿Quién puede verlas y editarlas (todos los correctores, solo el profesor y el autor) y quedan registradas en auditoría?

- **Requisitos:** R2.7.2, R2.7.6, R2.7.7, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Los correctores necesitan un canal privado distinto del comentario que se publica en Canvas; sin él escribirán observaciones sensibles en comentarios visibles al estudiante.
- **Opciones:**
  - Notas internas + banderas con visibilidad por rol
  - Solo banderas predefinidas
  - Nada: se usa el comentario de Canvas
- **Estudio de APIs:** no lo aborda (§10 solo contempla comentarios que se publican en Canvas).
- **Fusiona:** P615

### Q-2.7-22 — ¿En qué zona horaria se muestran en la vista de corrección la fecha efectiva de cierre, el "capturado el" y el "publicado el": America/Santiago fija, la del navegador, o con offset explícito? ¿Se muestra además el origen de la fecha efectiva (base, sección u override individual)?

- **Requisitos:** R2.7.4, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Un corrector que ve una hora desplazada desconfía del snapshot y del estado; hay que fijar la regla de presentación de fechas.
- **Opciones:**
  - America/Santiago fija
  - Zona horaria del navegador
  - Zona configurable por usuario, con offset explícito visible
- **Estudio de APIs:** §14 indica "guarden todo en UTC y conviertan solo al renderizar"; no fija la zona de presentación.
- **Fusiona:** P608

## Acceso a la versión del repositorio (R2.7.4)

### Q-2.7-23 — ¿Cómo accede el corrector a la versión de la entrega: enlace externo a `github.com/ORG/REPO/tree/<sha>` (y al tag), visor embebido de árbol y archivos dentro de la app leyendo por API con el token de la GitHub App, descarga del snapshot como `.zip` (`GET /repos/{o}/{r}/zipball/{sha}`), comandos git mostrados en pantalla (`git clone` + `git checkout <sha>`, o `git fetch origin tag entrega-N`), o una combinación?

¿Se ofrece además el diff `compare/<sha_anterior>...<sha_actual>` con la entrega previa? Si hay descarga por la App, ¿se controla con permiso quién puede descargar y se registra la descarga? La respuesta determina si un ayudante sin cuenta GitHub o sin acceso a la organización puede corregir y ejecutar el código.

- **Requisitos:** R2.7.4, R2.4.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Un visor embebido o una descarga vía la App evitan que el ayudante necesite acceso GitHub a repositorios privados pero cuestan mucho más trabajo; el enlace externo lo exige. Además el corrector normalmente necesita EJECUTAR el código, no solo verlo.
- **Opciones:**
  - Solo enlace a GitHub (`tree/<sha>`)
  - Visor embebido en la app
  - Ambos
  - Ambos + diff con la entrega anterior
  - Descarga zip vía la App con control de permiso y registro
  - Comandos git mostrados en la vista
- **Estudio de APIs:** §10.2 recomienda el enlace directo al SHA ("nunca linkeen a main") y §7.5 paso 4 sugiere `compare` como extra para R2.5.9; ambos proponen solo enlaces web (tree, compare, commits), no descarga ni visor.
- **Fusiona:** P567, P617

### Q-2.7-24 — ¿Qué metadatos de la versión se muestran junto al acceso al código: SHA corto, nombre del tag, fecha efectiva de cierre usada y su origen (base, sección, extensión), fecha del commit capturado, número de commits, autores, y "N commits posteriores al cierre"?

- **Requisitos:** R2.7.4, R2.4.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Da confianza al corrector de que revisa la versión correcta y sustenta cualquier discusión sobre atrasos.
- **Opciones:**
  - Mínimo: SHA y tag
  - SHA, tag, fecha de captura y fecha efectiva con su origen
  - Lo anterior + número de commits, autores y commits posteriores al cierre
- **Estudio de APIs:** §10.2 sugiere mostrar "capturado el 16-09 16:30 · 47 commits · último por msoto".
- **Fusiona:** P569

### Q-2.7-25 — ¿La app deja algún rastro en la submission de Canvas al cierre de cada entrega (por ejemplo, un comentario con la URL `tree/<sha>` y la fecha de captura, visible al estudiante), de modo que estudiante y corrector vean en Canvas qué versión se evaluará, o el SHA vive únicamente dentro de la app?

Si se deja rastro, ¿el comentario de corrección (R2.7.6) debe referenciarlo?

- **Requisitos:** R2.7.6, R2.4.5, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el nivel de transparencia hacia el estudiante sobre qué código se corrige y si existe evidencia en Canvas independiente de la app.
- **Opciones:**
  - Sin rastro: el SHA solo vive en la app
  - Comentario automático en la submission al capturar el snapshot
  - Rastro solo en el comentario de la corrección al publicar la nota
- **Estudio de APIs:** §5.7 usa el comentario en la submission para informar la URL del repositorio al crearlo (R2.3.12); no lo propone para el snapshot.
- **Fusiona:** P600

## Rúbrica (R2.7.5)

### Q-2.7-26 — Si el assignment de Canvas vinculado NO tiene rúbrica asociada, ¿se permite calificar con nota directa, se muestra un aviso, se bloquea la corrección, o se ofrece un enlace para crearla en Canvas? ¿Se valida o advierte la ausencia de rúbrica ya al vincular la entrega con la tarea (R2.3.1)?

- **Requisitos:** R2.7.5, R2.7.6, R2.3.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** El enunciado establece que las rúbricas se mantienen en Canvas; hay que fijar qué ocurre cuando no existen y si tener rúbrica es prerrequisito del wizard de vinculación que se demuestra desde la parcial.
- **Opciones:**
  - Permitir calificar con nota directa sin aviso
  - Permitir con aviso visible
  - Bloquear la corrección hasta que exista rúbrica
  - Advertir ya al vincular la entrega, con enlace para crearla en Canvas
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P573

### Q-2.7-27 — Cuando la rúbrica está asociada pero con `use_for_grading=false` (o con `hide_points`/`hide_score_total`), ¿la nota se calcula igualmente desde la rúbrica o el corrector la ingresa aparte y la rúbrica queda solo como feedback? Si la suma de puntos de la rúbrica difiere de `points_possible` del assignment, ¿cómo se escala?

- **Requisitos:** R2.7.5, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la fórmula nota = f(rúbrica) y las validaciones que se ejecutan antes de publicar.
- **Opciones:**
  - Nota siempre derivada de la rúbrica
  - Nota manual + rúbrica como feedback
  - El comportamiento depende de `use_for_grading`
  - Escalado proporcional a `points_possible` vs bloqueo cuando no coinciden
- **Estudio de APIs:** §10.3 lista los campos `use_for_grading`, `hide_points` y `hide_score_total` sin definir su efecto en la app.
- **Fusiona:** P574

### Q-2.7-28 — Si la rúbrica cambia en Canvas a mitad de la corrección (criterios agregados o eliminados, puntos modificados, rúbrica reemplazada), ¿la app lo detecta, invalida o marca los borradores afectados y avisa al corrector? ¿La rúbrica se lee en vivo al abrir cada entrega o se cachea en la sincronización?

- **Requisitos:** R2.7.5, R2.4.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Un borrador con criterios obsoletos produce un `rubric_assessment` inválido o una nota incorrecta al publicar.
- **Opciones:**
  - Lectura en vivo al abrir la entrega
  - Cacheada en la sincronización, con detección de cambios y marca de borradores afectados
  - Cacheada sin detección de cambios
- **Estudio de APIs:** §10.3 sugiere usar el objeto `assignment.rubric` embebido; no aborda los cambios posteriores.
- **Fusiona:** P575

### Q-2.7-29 — Investigar en la documentación de Canvas cómo se representan en `rubric_assessment` los criterios especiales y cómo Canvas calcula el score con ellos.

Casos a resolver: criterios con `criterion_use_range=true` (puntos libres dentro del rango del rating) y con `free_form_criterion_comments=true` (comentario libre en lugar de rating); si la clave del criterio es `criterion_<id>` o el `id` tal cual viene en `data[]`; y criterios ligados a resultados de aprendizaje (`learning_outcome_id`, `mastery_points`) o con `ignore_for_scoring=true`: cómo se muestran en la grilla, si se envían en `rubric_assessment` igual que los demás y si se excluyen del cálculo de la nota sugerida.

- **Requisitos:** R2.7.5, R2.7.6
- **Tipo:** investigable_en_docs · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el formulario por criterio (selector de rating vs campo numérico vs texto), el formato exacto del payload y evita que la nota sugerida por la app difiera de la que Canvas calcula.
- **Opciones:**
  - (sin opciones predefinidas: el resultado de la investigación fija el diseño del formulario y del payload)
- **Estudio de APIs:** §10.3 lista `criterion_use_range` y `free_form_criterion_comments` en los objetos y §10.4 usa `rubric_assessment[criterion_1][points]` como ejemplo; §10.3 no menciona `learning_outcome_id`, `mastery_points` ni `ignore_for_scoring`.
- **Fusiona:** P576, P614

### Q-2.7-30 — Verificar contra la instancia real de Canvas: ¿el objeto `assignment.rubric` embebido trae todo lo necesario (criterios, ratings con sus ids, puntos) o hay que llamar `GET /courses/:id/rubrics/:id`? ¿Qué devuelve Canvas si `rubric_assessment` trae un `rating_id` inexistente o puntos fuera del rango del criterio: error 4xx o lo acepta silenciosamente?

- **Requisitos:** R2.7.5, R2.7.6
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina las validaciones que la app debe hacer del lado cliente antes de publicar y si hace falta una llamada adicional por assignment.
- **Opciones:**
  - (sin opciones predefinidas: el resultado de la verificación fija las validaciones previas)
- **Estudio de APIs:** §10.3 afirma que "el objeto Assignment ya trae rubric y rubric_settings embebidos... suele bastar", sin verificarlo.
- **Fusiona:** P577

## Nota, comentario y publicación en Canvas (R2.7.6)

### Q-2.7-31 — ¿En qué unidad trabaja el corrector la nota: puntos del assignment (`points_possible`), porcentaje, o escala 1.0–7.0? ¿Cómo se mapea a `submission[posted_grade]` según el `grading_type` del assignment (`points`, `percent`, `letter_grade`, `gpa_scale`, `pass_fail`)?

¿Qué validaciones aplican (rango, decimales, coma vs punto, `points_possible=0`)?

- **Requisitos:** R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el campo de nota de la pantalla de corrección, sus validaciones y el formato de publicación; un desajuste con `grading_type` produce notas erróneas en Canvas.
- **Opciones:**
  - Puntos del assignment
  - Escala 1.0–7.0 convertida a puntos
  - Según el `grading_type` de Canvas, adaptando el campo
- **Estudio de APIs:** §10.4 usa el ejemplo `submission[posted_grade]=5.8` y anota que acepta "puntos, porcentaje, nota en letra o pass/fail", sin fijar la regla de la app.
- **Fusiona:** P578

### Q-2.7-32 — Investigar en la documentación los formatos exactos que acepta `posted_grade` para cada `grading_type` (por ejemplo `85%` para percent, `A` para letter_grade, `complete`/`incomplete` para pass_fail) y cómo Canvas redondea los decimales.

- **Requisitos:** R2.7.6
- **Tipo:** investigable_en_docs · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es necesario para escribir la regla de conversión y los mensajes de validación del campo de nota.
- **Opciones:**
  - (sin opciones predefinidas: el resultado de la investigación fija la regla de conversión)
- **Estudio de APIs:** §10.4 menciona los tipos aceptados sin dar los formatos concretos.
- **Fusiona:** P579

### Q-2.7-33 — El comentario general al estudiante (`comment[text_comment]`): ¿es obligatorio u opcional al publicar? ¿La app añade automáticamente un pie con la entrega, el SHA o tag revisado y el nombre del corrector? En tareas grupales, ¿se envía con `comment[group_comment]=true`?

- **Requisitos:** R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija el contenido mínimo de una corrección y la trazabilidad visible para el estudiante en Canvas.
- **Opciones:**
  - Comentario obligatorio
  - Comentario opcional
  - Con pie de trazabilidad automático (entrega, SHA/tag, corrector)
  - Comentario grupal (`group_comment=true`) vs individual en tareas grupales
- **Estudio de APIs:** §10.4 muestra un ejemplo con "Revisado sobre la versión aa218f5 (entrega parcial)" y `group_comment=true`.
- **Fusiona:** P580

### Q-2.7-34 — En tareas grupales: ¿una sola nota para todo el grupo o notas individuales por integrante? ¿La app lo deriva del campo `grade_group_students_individually` del assignment de Canvas y lo valida como parte de la consistencia entre entregas (R2.3.3)?

¿Se permite al corrector ajustar la nota de un integrante específico (por ejemplo, sin participación detectada según R2.5.4) y se muestran las métricas de participación en la pantalla de corrección?

- **Requisitos:** R2.7.6, R2.3.3, R2.5.4, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la UI de nota (un campo vs uno por integrante), el payload de publicación (una llamada vs N) y la relación entre corrección y monitoreo de participación.
- **Opciones:**
  - Siempre nota grupal única
  - Siempre individual
  - Según `grade_group_students_individually`, con override manual por integrante
- **Estudio de APIs:** §10.4 advierte "lean ese campo antes de calificar o van a dejar a medio grupo sin nota"; §5.1 lo lista como campo relevante.
- **Fusiona:** P581

### Q-2.7-35 — Al publicar una nota, ¿la UI muestra explícitamente el alcance antes de confirmar ("esta nota se aplicará a los 3 integrantes" vs "solo a Ana Díaz", según la configuración de Canvas) y con qué identidad se publica ("se registrará como Profesor X")? ¿Qué feedback se da tras publicar (éxito con enlace al SpeedGrader, error con reintento)?

- **Requisitos:** R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita dejar medio grupo sin nota y sorpresas sobre la autoría registrada en Canvas; define el modal de confirmación y el estado posterior a la publicación.
- **Opciones:**
  - Modal de confirmación con alcance e identidad explícitos
  - Publicación directa con aviso posterior
  - Alcance visible de forma permanente en la pantalla, sin modal
- **Estudio de APIs:** §10.4 advierte leer `grade_group_students_individually` antes de calificar; §3.4 recomienda mostrar en la UI que "las notas se publican como Profesor X".
- **Fusiona:** P620

### Q-2.7-36 — Si la membresía de un grupo cambia en Canvas después del cierre (un integrante se mueve de grupo, o el grupo se elimina), ¿la corrección aplica al conjunto de integrantes CONGELADO al momento del snapshot o a la membresía ACTUAL?

Dado que con `grade_group_students_individually=false` Canvas propaga la nota a la membresía actual, ¿la app detecta la divergencia y avisa, bloquea, o exige una decisión del profesor?

- **Requisitos:** R2.7.6, R2.2.3, R2.4.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin regla, un estudiante que no trabajó en ese repositorio puede recibir la nota del grupo y uno que sí trabajó puede quedar sin nota.
- **Opciones:**
  - Congelar los integrantes por snapshot y publicar individualmente
  - Usar la membresía actual de Canvas
  - Detectar la divergencia y exigir decisión del profesor
- **Estudio de APIs:** §10.4 explica la propagación grupal; §4.4 indica hacer "upsert" de grupos, sin congelar la membresía por entrega.
- **Fusiona:** P560

### Q-2.7-37 — Verificar contra la instancia real de Canvas: con `grade_group_students_individually=false`, ¿un solo PUT a un integrante propaga `posted_grade`, `rubric_assessment` Y el comentario (con `comment[group_comment]=true`) a todos los integrantes? ¿Y qué ocurre con el integrante que al cierre estaba en el grupo pero ya no está?

- **Requisitos:** R2.7.6, R2.2.3
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina si basta una llamada por grupo o hay que iterar por integrante, y cómo se calcula el estado "publicada" de un grupo.
- **Opciones:**
  - (sin opciones predefinidas: el resultado de la verificación fija el número de llamadas por entrega grupal)
- **Estudio de APIs:** §10.4 afirma que "calificar a un integrante propaga la nota a todo el grupo. Si es true, hay que llamar por cada integrante", sin verificarlo.
- **Fusiona:** P561

### Q-2.7-38 — Verificar contra la instancia real de Canvas: ¿`PUT .../submissions/:user_id` con `posted_grade` (y `rubric_assessment`) sobre una submission `unsubmitted` de un assignment con `submission_types=none` crea la nota y ésta aparece en el libro de calificaciones y en SpeedGrader? ¿Y con `on_paper`?

- **Requisitos:** R2.7.6
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Toda la corrección depende de poder calificar sin que el estudiante haya entregado nada en Canvas, porque la entrega real es el repositorio.
- **Opciones:**
  - (sin opciones predefinidas: si Canvas lo rechaza, cambia el mecanismo completo de publicación)
- **Estudio de APIs:** §10.4 asume que funciona, sin mencionar el caso sin submission.
- **Fusiona:** P599

### Q-2.7-39 — Dado que el repositorio ES la entrega, ¿la app exige o solo recomienda, al vincular la entrega con la tarea de Canvas (R2.3.1), que el assignment tenga `submission_types` compatible (`none`, `on_paper`, `online_url`) y advierte si es `online_upload` u otro tipo que confunda al estudiante? ¿Se valida también que el assignment esté `published`?

- **Requisitos:** R2.7.6, R2.3.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es una validación del wizard de vinculación que se demuestra desde la parcial y evita que los estudiantes intenten entregar archivos en Canvas.
- **Opciones:**
  - Exigir tipo compatible (bloquea la vinculación)
  - Solo advertir
  - No validar
  - Validar además que esté `published`
- **Estudio de APIs:** §5.1 menciona `submission_types` solo como dato útil para la tarea de recolección de usuarios GitHub y recomienda no crear repositorios para tareas no publicadas.
- **Fusiona:** P598

### Q-2.7-40 — Si el assignment tiene política de publicación MANUAL en Canvas (notas ocultas al estudiante hasta "Post grades"), ¿qué hace la app y con qué mecanismo técnico?

Parte de investigación: ¿existe un endpoint REST para "postear" las notas o solo la mutación GraphQL `postAssignmentGrades`? ¿Cómo se lee la post policy del assignment (`post_manually`)? Parte de decisión: ¿la app solo muestra un aviso "la nota está oculta en Canvas", ofrece la acción "mostrar notas a estudiantes" para toda la entrega, o queda fuera de alcance y se resuelve en Canvas? ¿El estado "publicada" de la app significa "visible al estudiante"?

- **Requisitos:** R2.7.6, R2.6.7
- **Tipo:** decision_equipo + investigable_en_docs · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Si las notas quedan ocultas para el estudiante tras publicarlas, el significado del estado "publicada" y el disparador de la notificación de corrección cambian.
- **Opciones:**
  - Solo aviso de que la nota está oculta
  - Acción "mostrar notas" desde la app
  - Fuera de alcance
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P588, P589

### Q-2.7-41 — ¿Existe el concepto de "entrega atrasada" cuando la entrega es el snapshot al cierre, y la app aplica penalizaciones sobre la nota antes de publicar?

Alternativas para el atraso: no existe (lo que había al cierre es lo que se corrige); se informa al corrector "N commits después del cierre" sin efecto; el profesor puede aceptar una entrega tardía eligiendo un SHA posterior; se marca `late_policy_status=late` en Canvas. Sobre las penalizaciones: ¿la app calcula descuentos (por atraso aceptado, por integrante sin participación, etc.) con una fórmula configurable por tarea, o eso queda fuera de alcance y se resuelve en Canvas?

- **Requisitos:** R2.7.6, R2.7.4, R2.4.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si la pantalla de corrección tiene selector de versión alternativa, si se usa `late_policy_status` y si hace falta configuración de fórmulas y lógica de cálculo por tarea.
- **Opciones:**
  - No existe atraso; sin penalizaciones en la app
  - Informativo ("N commits posteriores"), sin efecto en la nota
  - Aceptar un SHA posterior con penalización calculada por la app
  - Marcar `late` en Canvas y dejar el descuento a la late policy de Canvas
  - Fórmula de penalización configurable por tarea dentro de la app
- **Estudio de APIs:** §10.4 lista `submission[late_policy_status]` (`late`, `missing`, `extended`, `none`) sin regla de uso; §7.5 fija el snapshot como versión única. No aborda penalizaciones calculadas por la app.
- **Fusiona:** P601, P602

### Q-2.7-42 — ¿La pantalla de corrección permite marcar una entrega como excusada (`submission[excuse]=true`) o como "missing" (`late_policy_status=missing`)? ¿Quién puede hacerlo: el corrector o solo el profesor?

- **Requisitos:** R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define acciones adicionales disponibles en la corrección y a qué permiso quedan asociadas.
- **Opciones:**
  - Ambas acciones disponibles para el corrector
  - Solo para el profesor
  - Ninguna: se resuelve en Canvas
- **Estudio de APIs:** §10.4 lista `submission[excuse]` y `late_policy_status` como parámetros disponibles.
- **Fusiona:** P603

### Q-2.7-43 — Si se implementa la publicación masiva de notas con `POST /courses/:cid/assignments/:aid/submissions/update_grades` (asíncrona, devuelve un objeto `Progress` que hay que poletear), ¿cómo se modela y se muestra ese trabajo?

Decidir: (a) si se usa esa ruta o se prefieren N PUT secuenciales por estudiante (más lentos y con más consumo de cuota, pero con resultado y error por sujeto); (b) si se usa, cómo se persiste el `Progress` (id, estado, url, intentos de poleo, resultado), cada cuánto se consulta y cuándo se declara perdido; (c) qué se hace ante éxito PARCIAL (algunos estudiantes calificados y otros no): ¿se marca cada corrección individualmente según lo que reporta Canvas, o se releen las submissions para determinar el estado real?; (d) qué ve el corrector mientras la publicación está "en curso" y si puede seguir corrigiendo o navegar; (e) si un fallo del proceso durante el poleo deja notas publicadas en Canvas sin registro en la app y cómo se reconcilia. Verificar además qué formato de errores devuelve el `Progress` en la instancia de Canvas que se usará.

- **Requisitos:** R2.7.6, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es el único punto donde la app depende de un trabajo asíncrono del lado de Canvas: sin modelarlo, la app quedará mostrando "publicando…" indefinidamente o marcará como publicadas notas que Canvas rechazó, justo en el requisito que el evaluador comprobará abriendo el libro de calificaciones.
- **Opciones:**
  - No usar `update_grades`: N PUT secuenciales por sujeto con estado individual
  - Usar `update_grades` con `Progress` persistido y poleo por job
  - Usar `update_grades` solo para acciones masivas del profesor y PUT individual para el flujo del ayudante
- **Estudio de APIs:** §10.4 lo menciona en una línea ("calificación masiva asíncrona (devuelve un Progress; hay que poletear su estado)"), sin describir estados, errores parciales ni modelo de datos.
- **Fusiona:** N039

### Q-2.7-44 — ¿Cómo se ejecuta la escritura de notas hacia Canvas: sincrónicamente desde la request del usuario o encolada, con qué garantías de idempotencia, reintentos y auditoría, y cómo se maneja la cuota por token cuando varios ayudantes publican a la vez?

Casos a cubrir: 403/429 por throttling, timeout después de que el PUT ya se aplicó, doble clic en "Publicar". ¿Se reintenta con backoff, se verifica leyendo la submission después, se serializan las publicaciones en una cola única por curso o por token, y se registra un log de publicaciones (quién, cuándo, payload, respuesta de Canvas)? De ello depende si el botón "Publicar" responde de inmediato o deja la entrega en estado "publicando".

- **Requisitos:** R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la robustez de la escritura hacia Canvas, la experiencia del corrector al publicar y la evidencia auditable para la defensa.
- **Opciones:**
  - Publicación sincrónica directa desde la request
  - Publicación encolada (outbox) con estado "pendiente de publicación" y reintentos
  - Cola serializada por curso o por token (concurrencia 1)
  - Con log de auditoría de cada publicación
- **Estudio de APIs:** §1.5 describe 403/429 y backoff para lecturas y dice que "el worker de sincronización debe ser secuencial por curso (concurrencia 1 por token)", sin aplicarlo a las escrituras de notas; §9.4 propone un outbox para comunicaciones, no para notas.
- **Fusiona:** P591, P592

### Q-2.7-45 — ¿Se permite reeditar y republicar desde la app una nota ya publicada? ¿Quién puede hacerlo (solo el profesor, el corrector original, cualquiera con permiso)? ¿Se guarda historial de versiones de la corrección? ¿Se notifica al estudiante en cada cambio o solo la primera vez?

- **Requisitos:** R2.7.6, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la transición "publicada → en progreso", los permisos de edición posterior y el disparador de la notificación de corrección al estudiante.
- **Opciones:**
  - Republicación libre para el corrector original
  - Republicación solo por el profesor
  - Republicación bloqueada (se corrige en Canvas)
  - Con historial de versiones y notificación solo en el primer envío vs en cada cambio
- **Estudio de APIs:** §9.4 lista el flag `notify_graded` ("Corrección publicada → Conversation individual") sin detallar repeticiones.
- **Fusiona:** P593

### Q-2.7-46 — La comunicación al estudiante al publicar la nota (R2.6.7): ¿se envía por cada publicación individual, o una sola vez cuando el profesor cierra la corrección de toda la entrega? ¿Por Conversation, por comentario en la submission, o ambos? ¿Qué contenido incluye (nota, enlace al SHA revisado, comentario del corrector)?

- **Requisitos:** R2.7.6, R2.6.7, R2.6.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cruce entre 2.7 y 2.6: define el disparador, el canal y el contenido de la notificación de corrección publicada.
- **Opciones:**
  - Una notificación por cada publicación individual
  - Una notificación cuando el profesor cierra la entrega completa
  - Sin notificación propia (se confía en la notificación nativa de Canvas)
  - Canal: Conversation, comentario en la submission, o ambos
- **Estudio de APIs:** §9.4 define el evento "Corrección publicada → Conversation individual" con el flag `notify_graded`.
- **Fusiona:** P610

## Identidad, credenciales y permisos para escribir en Canvas

### Q-2.7-47 — ¿Con qué credencial se escriben las notas en Canvas: (A) el token del profesor que vinculó el curso (la app actúa "en nombre del curso" y Canvas registrará al profesor como calificador), o (B) el token OAuth propio de cada ayudante (lo que exige que esté enrolado como TA en Canvas)?

¿Se muestra en la UI "se publicará como Profesor X"? ¿La app guarda internamente quién corrigió realmente, independientemente de la identidad con que se escribe?

- **Requisitos:** R2.7.6, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es una decisión de arquitectura de autenticación que el estudio recomienda pero el equipo no ha aprobado; afecta el onboarding de ayudantes, la auditoría y qué ocurre si el profesor no está disponible.
- **Opciones:**
  - A: token del profesor
  - B: token del ayudante (enrolado como TA en Canvas)
  - A con B como fallback
- **Estudio de APIs:** §3.4 recomienda A como default y B como fallback, y pide documentar la decisión ("las notas se publican como Profesor X"). Recomendación no aprobada por el equipo.
- **Fusiona:** P582

### Q-2.7-48 — Dependencia del profesor del curso real: ¿es aceptable para él que en Canvas el calificador de todas las notas figure como el profesor y no como el ayudante que corrigió? Si no lo es, ¿exige que cada ayudante esté enrolado como TA en Canvas y publique con su propio token?

- **Requisitos:** R2.7.6
- **Tipo:** dependencia_externa · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Puede invalidar la opción del token del profesor y obligar a implementar OAuth por ayudante, con impacto directo en el onboarding y en el calendario.
- **Opciones:**
  - Acepta que figure el profesor
  - Exige identidad real del ayudante (TA + token propio)
- **Estudio de APIs:** §3.4 asume que basta con "mostrarlo en la UI".
- **Fusiona:** P583

### Q-2.7-49 — Verificar contra la instancia real de Canvas: al publicar con el token del profesor, ¿qué muestra Canvas en `grader_id` de la submission y en `assessor_id` del rubric_assessment? ¿Aparece el nombre del profesor en SpeedGrader como calificador?

- **Requisitos:** R2.7.6
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Confirma el efecto visible de publicar con el token del profesor y qué debe explicarse en la UI y en la defensa.
- **Opciones:**
  - (sin opciones predefinidas: el resultado condiciona la decisión de identidad de publicación)
- **Estudio de APIs:** §3.4 lo afirma implícitamente, sin verificación.
- **Fusiona:** P584

### Q-2.7-50 — Si se usa el token del profesor: ¿qué ocurre cuando ese profesor es retirado del curso, revoca el token, o el refresh falla mientras un ayudante intenta publicar? ¿Se usa el token de otro co-profesor (R2.1.7)? ¿La publicación se encola con la entrega en estado "pendiente de publicación" y reintento automático?

- **Requisitos:** R2.7.6, R2.1.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el fallback de disponibilidad de la escritura hacia Canvas y un estado adicional de corrección.
- **Opciones:**
  - Fallback al token de otro co-profesor
  - Encolar y reintentar con estado "pendiente de publicación"
  - Fallar visiblemente y exigir intervención del profesor
- **Estudio de APIs:** §1.1 explica el refresh_token; §9.4 propone un outbox para notificaciones, no para notas.
- **Fusiona:** P585

### Q-2.7-51 — Si se usa el token del ayudante: ¿quién asegura que cada ayudante esté enrolado como TA en Canvas? ¿Qué ocurre con un TA limitado a su sección (`limit_privileges_to_course_section`) al que se le asigna una entrega de otra sección? ¿Un ayudante SIN cuenta Canvas puede corregir en la app y que otro usuario publique por él?

- **Requisitos:** R2.7.6, R2.1.8
- **Tipo:** dependencia_externa · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina validaciones al asignar (sección del TA) y si existe un flujo de "corrige uno, publica otro".
- **Opciones:**
  - Exigir TaEnrollment sin restricción de sección
  - Validar la sección del TA al asignar
  - Permitir "corrige uno, publica otro"
- **Estudio de APIs:** §3.4 indica que el ayudante "debe tener un TaEnrollment en Canvas"; no menciona TAs limitados a una sección.
- **Fusiona:** P586

### Q-2.7-52 — Dependencia externa: si la Developer Key de Canvas tiene "enforce scopes", ¿incluye los scopes necesarios para la corrección (`url:PUT|/api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id`, `url:GET|.../rubrics`, `url:GET|.../submission_summary`, `url:POST|.../update_grades`)? ¿Quién los solicita al administrador de la instancia y en qué plazo?

- **Requisitos:** R2.7.5, R2.7.6
- **Tipo:** dependencia_externa · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin esos scopes la corrección no puede escribir en Canvas aunque el código esté listo, y la gestión con el administrador tiene plazos ajenos al equipo.
- **Opciones:**
  - (sin opciones predefinidas: se requiere confirmar los scopes habilitados y el responsable de solicitarlos)
- **Estudio de APIs:** §1.3 lista los scopes de GET submissions, PUT submissions y GET rubrics; no lista `submission_summary` ni `update_grades`.
- **Fusiona:** P611

## Estado de corrección y seguimiento (R2.7.7)

### Q-2.7-53 — ¿Cuáles son exactamente los estados de corrección y qué evento dispara cada transición?

Estados candidatos: sin asignar, asignada, en progreso, corregida (borrador), pendiente de publicación, publicada, desactualizada, bloqueada, excusada, sin entrega. Disparadores candidatos: automático al abrir la entrega, acción manual "marcar lista", éxito del PUT a Canvas, detección de una nota puesta en Canvas fuera de la app. ¿Se puede retroceder de estado y quién puede hacerlo?

- **Requisitos:** R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es la máquina de estados que sustenta R2.7.7 y la vista del ayudante; sin ella no hay criterios de aceptación para el requisito.
- **Opciones:**
  - Estados mínimos (pendiente / en curso / listo)
  - Estados mínimos + dimensión separada "con nota en Canvas"
  - Máquina de estados extendida con bloqueos y desactualización
- **Estudio de APIs:** §10.1 propone "pendiente / en curso / listo"; §10.5 añade la dimensión "con nota en Canvas".
- **Fusiona:** P595

### Q-2.7-54 — ¿Cómo se visualiza el estado de corrección (R2.7.7): matriz estudiante/grupo × entrega con color por estado, con agregados por corrector y por sección y el doble contador "N corregidas en la app · M con nota en Canvas"?

¿Es visible para los ayudantes o solo para los profesores? ¿Incluye a los sujetos sin repositorio y a los retirados? ¿Qué significa para el usuario la discrepancia entre ambas cifras y qué acción se ofrece frente a ella?

- **Requisitos:** R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la pantalla con la que se demuestra R2.7.7, sus filtros y la interpretación de las cifras que verá el evaluador.
- **Opciones:**
  - Matriz sujeto × entrega con color por estado
  - Lista con agregados por corrector
  - Ambas vistas, con doble contador app/Canvas
  - Visible solo para profesores vs también para ayudantes
- **Estudio de APIs:** §10.5 sugiere mostrar "18/25 corregidas en la app · 17/25 con nota en Canvas".
- **Fusiona:** P596

### Q-2.7-55 — Verificar contra la instancia real de Canvas: dado que nadie "entrega" en Canvas, `submission_summary` reportará casi todo como `not_submitted`. ¿Los contadores `graded`/`ungraded` siguen siendo útiles cuando la submission está `unsubmitted` pero con nota, o la app debe leer las submissions individuales (`workflow_state`, `score`, `graded_at`, `grader_id`) para obtener el estado por sujeto?

- **Requisitos:** R2.7.7
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina cuál es la fuente en Canvas del estado "publicada" por sujeto y su costo en número de requests.
- **Opciones:**
  - (sin opciones predefinidas: el resultado determina el endpoint del que se alimenta R2.7.7)
- **Estudio de APIs:** §10.4 propone `submission_summary` como camino "directo para el requisito 2.7.7", sin considerar que no habrá submissions.
- **Fusiona:** P597

### Q-2.7-56 — Si alguien cambia la nota directamente en Canvas (SpeedGrader) después de que la app la publicó, ¿la app lo detecta sincronizando submissions periódicamente y actualiza la nota y el estado que muestra, o solo muestra lo que ella misma publicó? ¿Con qué frecuencia y con qué endpoint se hace ese refresco?

- **Requisitos:** R2.7.6, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina si Canvas es la fuente de verdad del estado "publicada" y qué se muestra cuando la app y Canvas divergen.
- **Opciones:**
  - Sin sincronización inversa: la app muestra lo que publicó
  - Sincronización periódica de submissions con actualización de estado
  - Sincronización bajo demanda al abrir la vista de estado
- **Estudio de APIs:** §10.5 propone combinar la base de datos con `submission_summary` como "fuente de verdad de qué está realmente calificado".
- **Fusiona:** P594

### Q-2.7-57 — ¿Existe una fecha objetivo de corrección por entrega definida por el profesor, con alertas de corrección atrasada, y recibe el corrector avisos inmediatos cuando se le asignan o reasignan entregas?

Sobre las alertas: ¿aparecen en la vista de estado (R2.7.7, "X entregas sin corregir a N días del cierre"), en el informe diario del profesor (avance por corrector) y en el informe del ayudante (sus pendientes)? Sobre los avisos: ¿el corrector recibe email y/o notificación in-app al asignársele entregas y cuando el snapshot de una entrega asignada queda disponible para corregir, o debe descubrirlo entrando a la app? ¿Qué contiene el aviso (número de entregas, tarea, fecha objetivo, enlace directo a "mis correcciones") y puede desactivarse individualmente como la suscripción de R2.6.3?

- **Requisitos:** R2.7.1, R2.7.2, R2.7.7, R2.6.2, R2.6.3, R2.6.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Convierte R2.7.7 en una herramienta de gestión real, define eventos de notificación hacia el equipo docente (no solo hacia estudiantes) y qué contenido de corrección lleva el informe de 2.6.
- **Opciones:**
  - Fecha objetivo por entrega + alertas en informe y UI
  - Solo contador de pendientes sin plazo
  - Email al ayudante al asignar
  - Email cuando el snapshot queda disponible
  - Solo notificación in-app
  - Nada (solo el informe diario existente)
- **Estudio de APIs:** §9.1 enumera el contenido del informe sin incluir avance de corrección; §10.5 define el estado de corrección sin plazos; §10.1 describe la vista "Mis correcciones" pero no notificaciones al corrector; §9.4 solo lista eventos hacia estudiantes.
- **Fusiona:** P545, P616

## Casos borde, conflictos y recuperación

### Q-2.7-58 — Si la nota ya existe en Canvas cuando un corrector intenta publicar desde la app (porque el profesor u otro ayudante calificó directamente en SpeedGrader), ¿la app lee la submission actual antes de publicar y bloquea, avisa con comparación ("Canvas: 5.5 por X el 3-oct; tú: 6.0") o sobrescribe sin preguntar?

¿El estado de corrección (R2.7.7) marca como corregida una entrega calificada fuera de la app? ¿Cuál es entonces la fuente de verdad del estado: la app o Canvas?

- **Requisitos:** R2.7.6, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la política de conflicto de escritura y la fuente de verdad del estado de corrección; evita pisar silenciosamente notas puestas fuera de la app.
- **Opciones:**
  - Bloquear la publicación
  - Avisar con comparación y pedir confirmación
  - Sobrescribir sin preguntar
- **Estudio de APIs:** §10.5 propone mostrar ambas cuentas ("corregidas en la app" vs "con nota en Canvas") y sugiere mostrar la diferencia, pero no define una regla de conflicto al publicar.
- **Fusiona:** P546, P590

### Q-2.7-59 — Cuando el corrector abre una entrega SIN snapshot (extensión individual aún no vencida, o snapshot en estado ERROR por fallo de GitHub), ¿se le muestra "no disponible aún" con la fecha efectiva, se le permite corregir sobre el HEAD actual con advertencia, o se bloquea hasta que el job capture la versión?

- **Requisitos:** R2.7.4, R2.4.3, R2.4.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita que se califique código que no corresponde a la entrega y define el mensaje y el estado para ese caso.
- **Opciones:**
  - "No disponible aún" con la fecha efectiva
  - Permitir corregir sobre HEAD con advertencia
  - Bloquear hasta que exista snapshot
- **Estudio de APIs:** §7.5 describe el job de captura y su robustez, no la UI del corrector ante la ausencia de snapshot.
- **Fusiona:** P570

### Q-2.7-60 — Si Canvas cambia la fecha de una entrega DESPUÉS de capturado el snapshot (extensión otorgada a posteriori) y existe una corrección en progreso o ya publicada sobre el SHA anterior, ¿la app bloquea la recaptura, recaptura y marca la corrección como "desactualizada" avisando al corrector, o conserva ambos SHA y deja la decisión al profesor?

- **Requisitos:** R2.7.4, R2.7.6, R2.4.4, R2.4.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cruce entre R2.4.7 (no alterar lo registrado) y la realidad de las extensiones tardías; define un estado adicional y una alerta.
- **Opciones:**
  - Bloquear la recaptura si hay corrección
  - Recapturar y marcar la corrección como "desactualizada"
  - Conservar ambos SHA y dejar decidir al profesor
- **Estudio de APIs:** §7.4 reprograma el snapshot solo si "cambió la fecha de una entrega NO capturada aún"; no aborda entregas ya capturadas ni ya corregidas.
- **Fusiona:** P571

### Q-2.7-61 — Si el snapshot de una entrega es NO_COMMITS (repositorio creado pero sin commits al cierre), ¿la entrega igual se asigna y se abre al corrector, o se marca automáticamente "sin entrega" con una nota predefinida (por ejemplo nota mínima o `late_policy_status=missing`)? ¿Quién confirma esa acción y existe un flujo masivo de "no entregó"?

- **Requisitos:** R2.7.1, R2.7.6, R2.4.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita gastar tiempo de corrección en repositorios vacíos y define si existe una acción masiva para los sujetos que no entregaron.
- **Opciones:**
  - Se asigna y se corrige normalmente
  - Se marca "sin entrega" y el corrector confirma
  - Publicación masiva de "missing" ejecutada por el profesor
- **Estudio de APIs:** §7.5 define el estado NO_COMMITS; §10.4 lista `submission[late_policy_status]` (`late`, `missing`, `extended`, `none`) sin regla de uso.
- **Fusiona:** P557

### Q-2.7-62 — Un estudiante retirado del curso (enrollment `inactive`, `deleted` o `completed`) con una entrega asignada: ¿desaparece de la lista del corrector, queda visible marcado "retirado" pero calificable, o se bloquea su corrección? Y en un grupo, ¿su retiro cambia a quiénes se propaga la nota?

- **Requisitos:** R2.7.1, R2.7.6, R2.2.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define los filtros de la vista de corrección y evita intentar publicar notas que Canvas rechazará o que no tienen destinatario.
- **Opciones:**
  - Desaparece de la lista
  - Visible, marcado "retirado" y calificable
  - Visible pero con la corrección bloqueada
- **Estudio de APIs:** §4.4 recomienda marcar `deleted_at` y no borrar; §14 pide "no borren su repo ni su historia". No aborda la corrección de estudiantes retirados.
- **Fusiona:** P558

### Q-2.7-63 — Verificar contra la instancia real de Canvas: ¿acepta `PUT .../submissions/:user_id` con `posted_grade` para un estudiante cuyo enrollment está `inactive` o `completed` (curso concluido)? ¿Qué código y mensaje de error devuelve?

- **Requisitos:** R2.7.6
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Si Canvas rechaza esas escrituras, la app debe detectar el estado del enrollment antes de publicar y mostrar un error comprensible en vez de un fallo genérico.
- **Opciones:**
  - (sin opciones predefinidas: el resultado define si hace falta una validación previa del enrollment)
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P559

### Q-2.7-64 — Si el curso usa períodos de calificación (grading periods) y el período de la tarea está CERRADO al momento de publicar, Canvas rechaza el cambio de nota para usuarios no administradores. ¿Cómo lo detecta y comunica la app, y cuál es el estado resultante de la corrección?

Aspectos a decidir: si se leen los grading periods del curso (`GET /courses/:id/grading_periods`) para advertir antes o se detecta solo por el error del PUT; si se bloquea el botón de publicar; qué pasa con las correcciones hechas en la app y pendientes de publicar cuando el período cierra a mitad de la corrección; si se valida anticipadamente al vincular la entrega o al asignar correctores que el período estará abierto en la fecha estimada de corrección. Además, verificar si la instancia de Canvas que se usará (institucional o demo) tiene grading periods configurados y con qué fechas respecto al período de evaluación del proyecto.

- **Requisitos:** R2.7.6, R2.7.7
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es una causa realista de fallo al publicar notas semanas después del cierre; determina un estado de corrección adicional ("no publicable en Canvas"), el mensaje al corrector y la coordinación de fechas del curso de demostración.
- **Opciones:**
  - Detectar al publicar y mostrar un error accionable con enlace a Canvas
  - Leer los grading periods del curso y advertir antes
  - Validar anticipadamente al vincular o al asignar
  - Ignorar y documentar como limitación
- **Estudio de APIs:** no lo aborda (§10.4 no menciona grading periods ni cursos concluidos).
- **Fusiona:** P543, P612

### Q-2.7-65 — Si la tarea de Canvas vinculada a una entrega es ELIMINADA o despublicada después de haber asignado o corregido, ¿la vista de corrección bloquea la publicación, muestra un aviso y conserva el estado histórico, o marca la entrega como inválida? ¿Cómo se detecta (404 en el polling de assignments)?

- **Requisitos:** R2.7.6, R2.7.7, R2.4.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el manejo de un dato roto en medio del flujo de corrección, cuando ya hay trabajo hecho que no se puede publicar.
- **Opciones:**
  - Bloquear la publicación y avisar, conservando el histórico
  - Marcar la entrega como inválida
  - Ignorar hasta que falle la publicación
- **Estudio de APIs:** §7.4 describe el polling de assignments, sin el caso de eliminación o despublicación.
- **Fusiona:** P604

### Q-2.7-66 — Concurrencia: dos usuarios (un corrector y el profesor, o dos correctores tras una reasignación) editan la misma entrega a la vez, o dos profesores ejecutan la asignación automática simultáneamente. ¿Se usa bloqueo optimista con aviso, "última escritura gana", o un lock por entrega mientras está abierta?

- **Requisitos:** R2.7.1, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita la pérdida silenciosa de correcciones y las asignaciones duplicadas o contradictorias.
- **Opciones:**
  - Bloqueo optimista con aviso de conflicto
  - Última escritura gana
  - Lock por entrega mientras está abierta
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P605

### Q-2.7-67 — Los estudiantes pueden dejar submissions espontáneas en la tarea de Canvas de una entrega (subir un zip o un texto por confusión) y, si el curso tiene una late policy con deducción automática, Canvas marcará esa submission como "late" y REDUCIRÁ la nota que la app publique. ¿La app detecta y muestra esas submissions al docente, envía `late_policy_status` explícito al publicar para neutralizar la deducción, advierte al vincular si el curso tiene late policy, o ignora el tema?

Verificar además empíricamente si la deducción se aplica a notas puestas por API sobre una submission tardía.

- **Requisitos:** R2.7.6, R2.3.1, R2.4.5, R2.3.12
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Puede alterar silenciosamente las notas publicadas y confundir a estudiantes que creen haber "entregado" en Canvas; el docente necesita verlo.
- **Opciones:**
  - Detectar las submissions del estudiante y mostrarlas en la vista de la entrega
  - Enviar `late_policy_status` explícito al publicar
  - Advertir al vincular si el curso tiene late policy
  - Ignorar
- **Estudio de APIs:** §10.4 menciona `late_policy_status` como parámetro y §5.1 menciona `submission_types`; no aborda late policies automáticas ni submissions espontáneas en tareas de entrega.
- **Fusiona:** P613

### Q-2.7-68 — Flujo de reclamo iniciado por el estudiante ("pusheé antes del cierre y no me consideraron", "quiero recorrección"): ¿la app modela un estado "en reclamo" por entrega que congela la nota y avisa al corrector, o el reclamo se maneja fuera de la app?

¿Qué evidencia ofrece la app al docente para resolverlo: pushes recibidos en una ventana de ±N minutos alrededor del cierre efectivo (hora de recepción del webhook vs fecha del commit), historial del SHA capturado y de sus recapturas, comunicaciones enviadas al estudiante? ¿Quién puede cerrar el reclamo y se notifica el resultado por Canvas?

- **Requisitos:** R2.7.6, R2.7.7, R2.4.5, R2.4.7, R2.6.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si existe un estado adicional en R2.7.7, qué datos de push deben persistirse como evidencia y si hace falta una plantilla de respuesta al estudiante.
- **Opciones:**
  - Estado "en reclamo" con evidencia dentro de la app
  - Reclamo fuera de la app, solo re-edición de la nota
  - Vista de evidencia sin estado formal
- **Estudio de APIs:** §7.5 hace del SHA en base de datos la fuente de verdad y §14 responde cómo saber qué código corregir; no aborda reclamos del estudiante ni evidencia de pushes cercanos al cierre.
- **Fusiona:** P542

### Q-2.7-69 — ¿Está en el alcance la retroalimentación del lado de GitHub (comentarios de commit sobre el SHA capturado, issues abiertos por el corrector, o un Pull Request generado desde el tag `entrega-N` para revisar línea a línea)?

Si está en el alcance, ¿la app los crea, los enlaza y los registra como comunicación? Si no lo está, ¿se prohíbe explícitamente para que toda calificación y feedback vivan en Canvas? Si un ayudante abre un issue por su cuenta en GitHub, ¿la app lo detecta o lo ignora?

- **Requisitos:** R2.7.4, R2.7.6, R2.6.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Delimita dónde puede recibir feedback el estudiante y si se requieren permisos adicionales (Issues, Pull requests) en la GitHub App.
- **Opciones:**
  - Solo Canvas (feedback en GitHub prohibido)
  - Pull Request de revisión desde el tag, enlazado desde la app
  - Comentarios de commit e issues libres, sin registro en la app
- **Estudio de APIs:** §10 mantiene rúbrica, notas y comentarios exclusivamente en Canvas y §2.3 no pide permisos de Issues ni Pull requests; no aborda el feedback del lado de GitHub.
- **Fusiona:** P540

## Ya respondidas por el enunciado

Ninguna. Los 84 veredictos de la etapa de verificación (P540–P622 y N039) quedaron marcados ABIERTA: no hay ninguna pregunta de esta área que el texto del enunciado responda de forma literal, por lo que ninguna fue apartada del cuerpo del documento.
