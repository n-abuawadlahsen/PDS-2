# Preguntas de alcance — Area transversal

46 preguntas finales, fusionadas desde 63 de entrada, 30 bloqueantes para la parcial.

## Alcance del producto y coexistencia en el entorno de evaluacion

### Q-transversal-01 — ¿Cómo interpreta el equipo la restricción del enunciado "los estudiantes no serán usuarios de la aplicación: toda su interacción deberá realizarse a través de Canvas y GitHub"? ¿Prohíbe cualquier página web de la app abierta por un estudiante —incluido el magic link firmado hacia el OAuth de GitHub que propone §6.2 para verificar la propiedad de la cuenta, y una eventual página "tu versión registrada de la entrega 1"—, o prohíbe únicamente que el estudiante tenga cuenta y login en la app, permitiendo páginas sin autenticación accedidas por un enlace firmado enviado desde Canvas? ¿Se consultará al profesor del curso antes de implementar §6.2, y con qué fecha límite para no bloquear el desarrollo? ¿Qué responderá el equipo el 7-oct si el revisor pregunta por qué un estudiante abrió una URL de la app?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Habilita o descarta de raíz la verificación de propiedad de la cuenta de GitHub por OAuth (§6.2), las páginas de estado para estudiantes y los enlaces de confirmación; afecta la estrategia de enrolamiento que se evalúa en usabilidad.
- **Opciones:**
  - Ninguna página de la app visitada por estudiantes (interpretación estricta)
  - Páginas sin login accedidas por enlace firmado enviado desde Canvas (se prohíbe solo la cuenta/login)
  - Consultar al profesor del curso antes de implementar §6.2 y decidir según su respuesta
  - Descartar la verificación por OAuth de GitHub y validar el login solo por texto de la entrega en Canvas
- **Estudio de APIs:** §6.2 propone un magic link firmado hacia el OAuth de GitHub y afirma que "formalmente sigue interactuando a través de Canvas y GitHub"; el equipo aún no ha validado esa interpretación.
- **Fusiona:** P657

### Q-transversal-02 — ¿Cuál es la lista cerrada de NO-objetivos que el spec declara explícitamente, para que el evaluador no los espere y el equipo pueda responder "fuera de alcance por diseño" el 7-oct? Candidatos a decidir uno por uno: autograding o ejecución de tests sobre el snapshot; detección de similitud o plagio entre repositorios; comentarios de código línea a línea dentro de la app; cualquier UI para estudiantes; crear o editar secciones, grupos e inscripciones en Canvas; editar rúbricas; entregas sin assignment de Canvas asociada; estudiantes que no provienen de Canvas (oyentes); GitHub Enterprise Server; notificaciones por Slack o WhatsApp; importar desde GitHub Classroom. ¿Dónde vive esa lista (sección del spec, guía para el revisor, ambas)?

- **Requisitos:** R2.2.1, R2.3.1, R2.3.2, R2.5.9, R2.7.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Sin no-objetivos explícitos, la "revisión usando la herramienta" puede penalizar ausencias que el equipo consideraba obvias, y cada integrante asume un límite distinto del producto.
- **Opciones:**
  - Sección "Fuera de alcance" en el spec y en la guía para el revisor
  - Solo en el spec, sin material para el revisor
  - Sin declaración formal
- **Estudio de APIs:** §12 describe la arquitectura mínima; no enumera no-objetivos.
- **Fusiona:** P685

### Q-transversal-03 — Es muy probable que el profesor y los ayudantes evalúen las apps de VARIOS equipos del curso contra el MISMO curso de Canvas y la MISMA organización de GitHub (instalando varias GitHub Apps y vinculando el mismo curso en cada una). ¿Qué reglas de aislamiento adopta la app para coexistir sin interferir: prefijo o namespace de repositorios único y configurable; topic o marcador propio para reconocer "sus" repositorios y no adoptar por 422 uno creado por otra app; nombre único de la tarea de registro de usuarios de GitHub para no leer las entregas de la tarea de otro equipo; ignorar webhooks de repositorios que no están en su BD; no eliminar ni modificar nada que no haya creado; no duplicar mensajes ni anuncios a los mismos estudiantes? ¿Se ofrece una acción "eliminar todo lo que esta app creó en esta organización y este curso" para dejar limpio el entorno del profesor, y con qué confirmación?

- **Requisitos:** R2.1.4, R2.1.5, R2.2.5, R2.3.7, R2.3.8, R2.3.12, R2.6.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Sin reglas de aislamiento, dos apps pueden pisarse repositorios, robar mapeos o mandar mensajes duplicados durante la evaluación, y el fallo se atribuiría a la app del equipo.
- **Opciones:**
  - Prefijo único por instancia de la app + topic/marcador en cada repositorio; adoptar por 422 solo repositorios marcados
  - Namespace configurable por curso con vista previa del nombre resultante
  - Acción "limpiar lo creado por esta app" (repositorios, tarea de registro, anuncios) con confirmación
  - Ignorar eventos y repositorios ajenos, registrándolos en un log
  - Exigir una organización de GitHub separada por equipo y no resolver la coexistencia en la app
- **Estudio de APIs:** §5.4 propone sufijo -2 ante 422 y §5.5 adopta el 422 "name already exists" como éxito; §6.1 crea una tarea llamada "Registro de usuario GitHub"; no aborda la coexistencia con otras apps en la misma organización o curso.
- **Fusiona:** P684

## Configuracion, modelo de datos y definiciones canonicas

### Q-transversal-04 — ¿Cuál es el mecanismo único de configuración de la app, su jerarquía y qué parámetro vive en qué nivel? Parámetros a repartir: plantilla de nombres de repositorios, visibilidad de los repositorios, nivel de permiso de los estudiantes, política de acceso (miembro de la organización vs colaborador externo), repositorio base (¿existe uno reutilizable a nivel curso o siempre por tarea?), umbral de "sin actividad reciente", umbral de desbalance, flags y plantillas de comunicaciones automáticas, hora del informe diario, intervalos de los crons, zona horaria, tamaño de lote y throttle, correctores por defecto. Decidir además: (a) dónde vive cada uno (constante en código, variable de entorno, tabla de configuración por curso, por tarea, por entrega); (b) si hay herencia con tri-estado "heredar / activado / desactivado" o si al crear la tarea se COPIA congelado el valor vigente del curso; (c) si al cambiar el valor de curso se afecta a las tareas ya creadas, solo a las futuras, o se pregunta; (d) qué reciben los cursos y tareas EXISTENTES cuando se agrega un parámetro nuevo o cambia su default (NULL = heredar, backfill, migración explícita); (e) si los cambios quedan en auditoría con valor anterior→nuevo y si afectan retroactivamente a datos ya calculados (bajar el umbral de inactividad, ¿reabre alertas históricas?); (f) si existe una acción "duplicar tarea" que copie configuración, repositorio base, plantilla de nombres y flags para crear la tarea siguiente del semestre, o cada tarea se configura desde cero.

- **Requisitos:** R2.1.3, R2.1.8, R2.3.1, R2.3.5, R2.3.8, R2.5.3, R2.6.1, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Determina cuántos campos rellena el profesor por cada tarea (la facilidad de uso es criterio evaluado), define si el esquema tiene uno o dos niveles de configuración —decidirlo después obliga a migrar— y fija si el spec puede escribir criterios de aceptación con números concretos o solo "configurable".
- **Opciones:**
  - Todo se configura por tarea, sin nivel de curso
  - Valores por defecto a nivel de curso, sobreescribibles por tarea, sin propagación retroactiva
  - Valores por defecto a nivel de curso con opción de propagar a tareas existentes
  - Tabla settings clave-valor con resolución global→curso→tarea→entrega en lectura
  - Columnas explícitas en curso y tarea, con copia congelada del valor al crear la tarea
  - Híbrido: operativos (intervalos, throttle) en variables de entorno; pedagógicos (umbrales, plantillas, toggles) en BD por curso/tarea
  - Todo en código y variables de entorno, sin configuración por curso
  - Acción "duplicar tarea" disponible / no disponible
- **Estudio de APIs:** §8.5 y §9.4 mencionan umbrales "configurables" y una tabla de flags de notificación por tarea, y §5.4 una plantilla de nombres de repositorios, pero no definen el mecanismo, el nivel en que se configuran, la herencia curso→tarea, la migración de valores por defecto ni la posibilidad de duplicar una tarea.
- **Fusiona:** N004, N032

### Q-transversal-05 — ¿Cómo se IMPLEMENTAN en la base de datos los conjuntos de estados y tipos que el spec enumera (estado de repositorio, de mapeo estudiante↔GitHub, de snapshot, de corrección, tipo de evento del timeline, tipo de comunicación, clase de error): tipo ENUM nativo del motor, columna de texto con CHECK, tabla catálogo con FK, o solo constantes en el código sin restricción en la BD? ¿Se persiste un código estable ASCII (p. ej. COLLABORATORS_PENDING) con la etiqueta en español viviendo solo en la capa de presentación, o se guarda el texto que se muestra? ¿Qué procedimiento se seguirá para AGREGAR un estado nuevo después del 16-sep sobre datos vivos (en PostgreSQL agregar un valor a un ENUM no es reversible y en versiones antiguas no se puede crear y usar en la misma transacción), y para RENOMBRAR o retirar uno (migrar filas existentes, dejar el valor huérfano, o mapear a un estado "legacy")? ¿Toda fila tiene estado NOT NULL con default, y las transiciones inválidas se rechazan en código o se aceptan y se detectan después?

- **Requisitos:** R2.2.6, R2.3.11, R2.4.5, R2.5.5, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define columnas, restricciones y el costo de cada cambio de la máquina de estados; si hace falta un estado nuevo (INVITATION_EXPIRED, TAG_CONFLICT) la migración toca datos de la demo que deben sobrevivir hasta el 6-oct, y determina si la UI puede traducirse sin tocar datos y si filtros e informes pueden confiar en un conjunto cerrado de valores.
- **Opciones:**
  - Tipo ENUM nativo del motor
  - Columna texto + CHECK con lista de valores
  - Tabla catálogo con FK (permite agregar valores sin migración de esquema)
  - Constantes solo en la aplicación, columna de texto libre
- **Estudio de APIs:** §5.2 propone estados de Repository (PENDING_MAPPING, QUEUED, CREATING, CREATED, COLLABORATORS_PENDING, READY, ERROR) y §7.5/§8.3 esbozan tablas, pero no aborda cómo se implementan ni cómo se evolucionan los enumerados.
- **Fusiona:** N028

### Q-transversal-06 — ¿Qué convenciones de ALMACENAMIENTO se fijan para los identificadores y textos que vienen de Canvas y GitHub? Decidir explícitamente: (a) tipo de columna para los ids de Canvas —bigint, o texto para tolerar los global ids de 14+ dígitos y los ids "shadow" con tilde (formato 123~456) de cuentas de otras instancias—; (b) unicidad case-insensitive del login de GitHub (los logins no distinguen mayúsculas: "JPerez" y "jperez" son la misma cuenta, pero un índice único normal permitiría dos filas): ¿login canónico devuelto por la API más una columna normalizada indexada, citext, o índice sobre lower()?; (c) lo mismo para el NOMBRE del repositorio, que GitHub trata como único sin distinguir mayúsculas dentro de la organización (dos nombres generados que difieren solo en mayúsculas colisionan con 422 aunque la BD los acepte como distintos); (d) charset y colación de los campos con datos humanos (nombres de grupo con tildes, ñ o emoji exigen utf8mb4 si el motor es MySQL) y longitud máxima con política de truncado para mensajes de commit, cuerpos de mensajes y descripciones; (e) si además del login se persiste el id numérico de GitHub y el node_id.

- **Requisitos:** R2.1.4, R2.2.4, R2.3.8, R2.5.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Son decisiones de esquema irreversibles sin migración: un bigint que no acepta un id shadow rompe la sincronización de un estudiante de intercambio, y una unicidad sensible a mayúsculas produce mapeos duplicados y colisiones de nombre de repositorio que el worker interpretará como error permanente.
- **Opciones:**
  - Ids de Canvas como bigint / como texto
  - Login de GitHub con columna normalizada indexada / citext / índice funcional sobre lower()
  - Persistir solo el login / login + id numérico + node_id
  - Truncado con marca visible / rechazo / almacenamiento completo sin límite
- **Estudio de APIs:** §5.4 da reglas de sanitización de nombres de repositorio y §6.1 recomienda usar el "login canónico" de la respuesta de GitHub, pero no aborda tipos de columna, colación, longitudes ni unicidad insensible a mayúsculas.
- **Fusiona:** N033

### Q-transversal-07 — Si se adopta la regla "nunca borrar filas, marcar deleted_at": (a) ¿cómo se conjugan las claves únicas con el borrado lógico en cada caso —unique(curso, github_login) cuando el login perteneció a un estudiante retirado y ahora lo reclama otro; unique(curso, usuario) en membresías docentes al retirar y reincorporar a un ayudante; unique(curso, slug) de una tarea eliminada cuyo nombre se reutiliza; unique(github_repo_id) cuando un repositorio es adoptado por otra fila (R2.3.8/422)—: índices únicos parciales (WHERE deleted_at IS NULL), reactivar la fila existente en vez de crear otra, o sufijar el valor borrado? (b) ¿El borrado lógico del padre se PROPAGA a sus hijos o se resuelve filtrando por el ancestro en cada consulta —curso archivado → tareas, entregas, repositorios, snapshots, asignaciones de corrección, mensajes pendientes en outbox; tarea eliminada → entregas y repos; entrega desvinculada → snapshots y correcciones; estudiante retirado → membresías, mapeo, atribuciones de commits—? (c) ¿Qué acción de FK se declara (RESTRICT, NO ACTION, CASCADE), sabiendo que un CASCADE físico contradice el borrado lógico? (d) ¿Existe "restaurar" y qué restaura exactamente (¿los mensajes pendientes se reactivan y se envían tarde?)? (e) ¿Hay purga física definitiva y quién la ejecuta?

- **Requisitos:** R2.1.3, R2.1.9, R2.2.1, R2.2.4, R2.3.1, R2.3.4, R2.3.8, R2.3.11, R2.4.6, R2.4.7, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Sin una regla uniforme, la segunda alta de un mismo valor falla con error de constraint (bug invisible en demo) o crea duplicados que rompen la idempotencia del worker; y sin regla de propagación, la mitad de las consultas del dashboard, del informe diario y de los workers filtrará por deleted_at y la otra no, produciendo repositorios fantasma, alertas sobre tareas eliminadas y correos a estudiantes de un curso archivado.
- **Opciones:**
  - Índices únicos parciales (WHERE deleted_at IS NULL)
  - Reactivar la fila existente en lugar de crear otra
  - Sufijar los valores de las filas borradas
  - Borrado físico solo para ciertas tablas
  - Marca en cascada al borrar el padre (un job propaga deleted_at)
  - Filtrado por ancestro en cada consulta, sin propagar
  - Híbrido: propagar solo a las tablas que consumen los workers y filtrar en el resto
  - Borrado físico con FK CASCADE para entidades sin valor probatorio y lógico solo para snapshots/correcciones
- **Estudio de APIs:** §4.4 ("Reglas de oro") dice "nunca borren filas al sincronizar: marquen deleted_at", pero solo para el roster de Canvas; no aborda su interacción con las claves únicas, la propagación a entidades hijas, las FKs ni la restauración/purga.
- **Fusiona:** P703, N029

### Q-transversal-08 — ¿Qué registro de auditoría existe, con qué forma técnica y con qué visibilidad? Decidir: (a) qué eventos se registran (quién, cuándo, qué, valor anterior→nuevo): registro de usuario, creación/edición/archivo de curso, vinculación, re-autorización y desvinculación de Canvas y GitHub, alta/baja y cambio de permisos de co-profesores y ayudantes, mapeos manuales y su fuente, reintentos, cambios de fecha detectados en Canvas, snapshots automáticos y manuales, asignaciones de corrector, notas publicadas, mensajes y anuncios enviados; (b) la forma: una tabla genérica (entity_type, entity_id, action, actor_id | "system:job", before_json, after_json, occurred_at, correlation_id) o tablas de historial específicas por entidad (MappingHistory, DateChange, SnapshotVersion); (c) si se escribe en la misma transacción que el cambio (consistente) o de forma asíncrona (con riesgo de huecos ante fallos del worker); (d) si los cambios detectados por el sync sin actor humano usan el mismo mecanismo que las acciones de usuario; (e) quién puede consultarlo, dónde se ve en la UI, con qué retención y si se exporta.

- **Requisitos:** R2.1.1, R2.1.3, R2.1.4, R2.1.5, R2.1.7, R2.1.8, R2.1.9, R2.2.5, R2.4.4, R2.4.5, R2.6.5, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Sin auditoría no se puede explicar en la validación del 7-oct "por qué este repositorio tiene este estado" ni "quién cambió qué" ante conflictos entre profesores; define cuántas tablas de historial existen, cómo se consultan desde la UI y si la auditoría puede tener huecos.
- **Opciones:**
  - Tabla genérica escrita en la misma transacción
  - Historiales específicos por entidad
  - Tabla genérica escrita de forma asíncrona vía outbox
  - Sin registro de auditoría en la app (solo logs del servidor)
- **Estudio de APIs:** §7.4 propone "un log de auditoría: quién/cuándo/de qué a qué" solo para cambios de fecha; §9.1 registra los envíos y §9.4 el historial de comunicaciones. Cobertura parcial, sin definir alcance, forma ni visibilidad.
- **Fusiona:** P664, P701, P705

### Q-transversal-09 — ¿Se exige una definición CANÓNICA ÚNICA del universo de sujetos y de los contadores derivados, compartida por todas las vistas y workers, o cada pantalla aplica sus propios filtros? Las mismas cifras aparecen en al menos cinco lugares (panel de faltantes, tabla de estado de repositorios, KPIs del dashboard, informe diario por email, estado de corrección) y todas dependen de las mismas exclusiones: Test Student, enrollments no activos, estudiantes sin grupo en tarea grupal, sujetos con la entrega no aplicable por only_visible_to_overrides, sujetos exentos o excluidos manualmente, repositorios adoptados o huérfanos. Decidir: (a) si existe una vista o consulta única ("sujetos de la tarea", "sujetos con problema") que todos consumen, o cada consumidor la reimplementa; (b) qué denominador usa cada cifra y si se muestra explícito ("37 de 40 inscritos activos, 2 excluidos"); (c) si se escribe una prueba automatizada que verifique que dashboard, informe y tabla de estado dan el mismo número para el mismo dataset.

- **Requisitos:** R2.2.6, R2.3.11, R2.5.1, R2.5.5, R2.6.2, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Si el informe diario dice 3 estudiantes sin usuario y la pantalla dice 5, el evaluador concluye que el sistema no es confiable aunque ambas cifras sean "defendibles"; fija una capa de consulta compartida en el modelo y un criterio de aceptación verificable.
- **Opciones:**
  - Vista/consulta única consumida por todas las pantallas, workers e informes
  - Cada consumidor implementa sus propios filtros, documentados
  - Denominador explícito visible junto a cada cifra / solo el numerador
  - Prueba automatizada de consistencia entre vistas / sin prueba
- **Estudio de APIs:** §5.6, §8.3 y §9.1 definen por separado la tabla de estados, las tablas agregadas del dashboard y el contenido del informe, sin exigir una definición común de universo ni de denominadores.
- **Fusiona:** N038

### Q-transversal-10 — ¿Se fija la matriz de datos derivados y sus disparadores de recálculo? Ejemplos de aristas: cambio de roster → sujetos → filas Repository → fechas efectivas → estado deseado de colaboradores → alertas; cambio de mapeo → colaboradores deseados → atribución de commits → "sin participación"; cambio de override → fechas efectivas → programación del snapshot → recordatorios; cambio de grupo → todo lo anterior más períodos. Para cada arista: ¿el recálculo es sincrónico en la misma transacción, un job encolado, o un recálculo completo periódico que tolera desfase? ¿Qué desfase máximo se acepta entre el cambio en Canvas y su efecto en cada derivado, y cómo se mide?

- **Requisitos:** R2.2.1, R2.2.3, R2.2.4, R2.4.4, R2.5.3, R2.5.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** si
- **Por que importa:** Sin la matriz, cada worker recalcula lo que cree necesario y aparecen inconsistencias (repositorio listo con fecha vieja, alerta sobre un estudiante retirado); define además los criterios de latencia medibles del spec.
- **Opciones:**
  - Recálculo sincrónico en la transacción del sync
  - Jobs encolados por tipo de cambio
  - Recálculo completo periódico
  - Combinación por arista, documentada en una tabla del spec
- **Estudio de APIs:** no lo aborda; cada sección del estudio describe su worker de forma aislada.
- **Fusiona:** P706

## Zona horaria, idioma y vocabulario

### Q-transversal-11 — ¿Cuál es la regla única de fechas y horas de extremo a extremo? Decidir: (a) servidor, BD y APIs en UTC (timestamptz) con conversión solo al renderizar; (b) de dónde sale la zona horaria de visualización: configurada por curso (p. ej. America/Santiago), tomada del campo time_zone del curso en Canvas, o del navegador del usuario; (c) si toda fecha se muestra con la zona indicada explícitamente ("hora de Chile") y en qué formato, incluidas las fechas de "vinculado el…" y "última sincronización hace…"; (d) si los jobs (informe diario de las 07:00 America/Santiago, cierres, snapshots) se programan con un scheduler consciente de zona horaria o como hora UTC fija, que se desfasa con el cambio de hora chileno (primer sábado de septiembre y de abril; Chile está en UTC-3 desde el 6-sep-2026, días antes de la parcial); (e) cómo se muestran las fechas all_day de Canvas y el caso due_at=null ("sin fecha"); (f) si el dataset de demo incluye una entrega con fecha cercana a medianoche para verificar la conversión ante el revisor.

- **Requisitos:** R2.1.3, R2.1.4, R2.4.1, R2.4.5, R2.5.6, R2.6.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Un snapshot capturado con 3 h de error es un bug grave e invisible, y una fecha distinta a la que muestra Canvas es visible de inmediato para el profesor en la demo; la regla afecta a toda la sección 2.4.
- **Opciones:**
  - Zona horaria de visualización configurable por curso
  - Tomada del time_zone del curso en Canvas
  - Tomada del navegador del usuario
  - Fija America/Santiago para toda la app
  - Scheduler consciente de zona horaria / cron en UTC fijo
- **Estudio de APIs:** §14 "Zonas horarias" indica guardar UTC (timestamptz) y convertir al renderizar, sin definir de dónde sale la zona de renderizado; §9.1 fija un CRON diario a las 07:00 America/Santiago; §7.3 menciona due_at null.
- **Fusiona:** P660, P672, P702

### Q-transversal-12 — ¿Cuál es la política de idioma, tono y formatos de todos los textos del producto? Decidir: (a) si la UI, los mensajes de error, los emails y los mensajes a estudiantes por Canvas van 100 % en español de Chile o son bilingües; (b) si se instala infraestructura de i18n (archivos de traducción) o se hardcodea el español, sabiendo que es una capa técnica adicional que mantener; (c) tono y persona: tuteo ("Vincula tu curso"), formal ("Vincule su curso") o impersonal ("Vincular curso"), y si se usa el mismo tono en la UI, en los mensajes automáticos a estudiantes y en el informe por email; (d) formato de fecha/hora (DD-MM-YYYY HH:mm, 24 h) y separador decimal (coma); (e) qué se hace con los términos que Canvas y GitHub muestran en inglés ("Assignment", "Group Set", "Organization"): dejarlos en inglés, traducirlos, o mostrarlos con el original entre paréntesis; (f) quién mantiene la guía de redacción y dónde se versiona.

- **Requisitos:** R2.1.6, R2.2.6, R2.3.11, R2.3.12, R2.5.6, R2.6.4, R2.6.5, Sección 3.1 (usabilidad)
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** La usabilidad se evalúa en la parcial; textos mixtos inglés/español, tonos distintos entre integrantes y formatos de fecha ambiguos restan claridad y afectan la evaluación de "guía adecuada".
- **Opciones:**
  - Español de Chile hardcodeado, sin capa de i18n
  - Español con infraestructura de i18n desde el inicio
  - Bilingüe español/inglés
  - Tuteo / trato formal / impersonal
  - Términos de Canvas y GitHub en inglés / traducidos / traducidos con el original entre paréntesis la primera vez
- **Estudio de APIs:** no lo aborda; los ejemplos están en español y los mensajes de §5.7 y §9.3 usan tuteo informal ("Hola! Tu repositorio ya está creado").
- **Fusiona:** P658, P673, P694

### Q-transversal-13 — ¿Cuál es el glosario oficial de la UI y su equivalencia exacta con los términos de Canvas y GitHub? Pares a decidir: "Tarea" (app) vs "Entrega" (= assignment de Canvas) vs "tarea de Canvas"; "Grupo" vs "conjunto de grupos / group set"; "Sección"; "Repositorio base" vs "plantilla"; "Organización"; "Versión de entrega" vs "snapshot" vs "tag"; "Corrección" vs "Calificación" vs "Revisión"; "Ayudante" vs "TA"; "Corrector". ¿Se muestra el término original entre paréntesis la primera vez, en un tooltip, o no se muestra? ¿El glosario obliga también al spec, a las plantillas de mensajes y al informe por email?

- **Requisitos:** R2.2.3, R2.3.1, R2.3.2, R2.4.5, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** La relación 1 tarea → N entregas (cada una una assignment de Canvas) es confusa; sin vocabulario fijo la UI, el spec y los mensajes al estudiante se contradicen entre sí y con lo que el profesor ve en Canvas.
- **Opciones:**
  - Glosario único obligatorio en UI, spec, plantillas e informes
  - Glosario solo para la UI, con libertad en documentos internos
  - Término original entre paréntesis la primera vez / en tooltip / nunca
- **Estudio de APIs:** §5.2 usa el modelo Assignment (app) → Delivery (assignment de Canvas) → Repository → DeliverySnapshot, sin fijar términos de UI en español.
- **Fusiona:** P695

## Navegacion, pantallas y guia al equipo docente

### Q-transversal-14 — ¿Cuál es el árbol exacto de navegación y de URLs de la app? Propuesta a confirmar o corregir: Home = "Mis cursos" → Curso (pestañas: Resumen / Estudiantes / Tareas / Equipo docente / Configuración) → Tarea (pestañas: Resumen / Entregas / Repositorios / Dashboard / Corrección / Comunicaciones / Configuración) → Repositorio (Timeline). ¿Hay breadcrumbs en todas las vistas y se preserva el contexto (pestaña activa, filtros, orden) al volver atrás? ¿Qué vista es la "puerta de entrada" de cada requisito (p. ej., dónde vive la tabla de estado de repositorios de R2.3.11 frente al dashboard de R2.5.1)?

- **Requisitos:** R2.1.3, R2.3.11, R2.5.1, R2.7.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija el mapa de pantallas del spec, las rutas y la ubicación de cada requisito; sin esto cada integrante inventa su propia jerarquía y las pantallas no encajan al integrar.
- **Opciones:**
  - Árbol curso→tarea→repositorio con pestañas
  - Sidebar global con secciones por curso
  - Vista única por tarea con paneles colapsables
- **Estudio de APIs:** §12 lista las vistas que leen de BD y §5.6/§10.1 describen tablas concretas, pero no propone jerarquía de navegación.
- **Fusiona:** P687

### Q-transversal-15 — ¿Existe una ficha por estudiante que consolide, a través de todas las tareas del curso, su sección, sus grupos con historial, el mapeo de GitHub (fuente y cambios), sus repositorios y estados, snapshots, commits atribuidos, comunicaciones enviadas y notas publicadas? Si existe: ¿desde dónde se accede (clic en el nombre en cualquier tabla, buscador global), qué roles la ven, e incluye tareas archivadas? Si no existe, ¿cómo responde el equipo docente a "¿qué pasa con el estudiante X?" sin recorrer cada tarea?

- **Requisitos:** R2.2.1, R2.2.4, R2.5.4, R2.6.5, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define una vista y una ruta adicionales en la navegación, sus permisos y qué datos deben ser consultables por estudiante en vez de por tarea.
- **Opciones:**
  - Ficha consolidada por estudiante accesible desde cualquier tabla
  - Sin ficha; la información se consulta tarea por tarea
  - Ficha limitada al curso actual, sin tareas archivadas
- **Estudio de APIs:** no lo aborda (§12 describe vistas por curso, tarea y repositorio).
- **Fusiona:** P661

### Q-transversal-16 — ¿Se estandariza un componente "Pendientes / Qué falta" reutilizado en las vistas de curso y de tarea, que liste en lenguaje de acción cada bloqueo con su llamada a la acción ("3 estudiantes sin usuario de GitHub → Enviar recordatorio", "2 invitaciones sin aceptar → Reenviar", "1 grupo sin integrantes → Configurar en Canvas")? ¿Cuál es la lista cerrada de tipos de pendiente y su prioridad de orden?

- **Requisitos:** R2.2.6, R2.3.11, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** R2.2.6 y R2.3.11 exigen mostrar "claramente" lo que falta; un componente único con tipos definidos hace el requisito verificable y consistente entre pantallas.
- **Opciones:**
  - Componente único reutilizado en curso y tarea, con lista cerrada de tipos
  - Paneles distintos por pantalla, cada uno con su propia lógica
  - Lista de pendientes solo en la vista de tarea
- **Estudio de APIs:** §6.3 define el "panel de faltantes" como la unión de: estudiantes sin login, grupos con algún integrante sin mapeo, estudiantes sin grupo (unassigned=true) e invitaciones sin aceptar.
- **Fusiona:** P698

### Q-transversal-17 — ¿Qué debe mostrar cada vista cuando no hay datos: curso sin estudiantes o sin secciones, group set sin grupos todavía (self-signup abierto), tarea sin entregas vinculadas, tarea sin repositorios, repositorio sin commits, entrega cerrada con snapshot "sin commits" (¿qué corrige el ayudante y qué nota se publica?), dashboard antes del primer sync? ¿Qué texto y qué acción sugerida lleva cada estado vacío? ¿La verificación de vinculación de R2.1.6 falla o solo advierte cuando el curso tiene 0 estudiantes?

- **Requisitos:** R2.1.6, R2.2.6, R2.3.11, R2.4.5, R2.5.1, R2.5.10, R2.7.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Los estados vacíos son los primeros que verá el corrector en la demo; cada uno necesita un texto y una acción sugerida definidos, y el caso "0 estudiantes" decide si el checklist de verificación es un bloqueo o una advertencia.
- **Opciones:**
  - Texto y acción sugerida definidos por vista, en un catálogo del spec
  - Estado vacío genérico único para toda la app
  - Verificación con 0 estudiantes: falla / solo advierte
- **Estudio de APIs:** §3.3 propone el chequeo "vemos estudiantes: n > 0"; §7.5 marca el status NO_COMMITS como "dato valioso para el informe". No define la UI de estados vacíos.
- **Fusiona:** P663

### Q-transversal-18 — ¿El spec incluirá un catálogo cerrado de errores esperables de la UI docente con, para cada uno, el texto mostrado al usuario, la acción sugerida y quién puede resolverlo? Casos mínimos a decidir: token de Canvas expirado o revocado; scopes insuficientes; 403/429 por rate limit; GitHub App desinstalada; usuario de GitHub inexistente; login que corresponde a una Organization; repositorio ya existente; invitación de colaborador expirada; límite del plan de la organización; tarea de Canvas eliminada; estudiante sin grupo en tarea grupal. ¿Se muestra el detalle técnico (código HTTP, mensaje de la API, id de request) en un desplegable "Detalles técnicos"?

- **Requisitos:** R2.1.6, R2.2.6, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Los mensajes orientados a la acción son el corazón de la "guía adecuada"; un catálogo permite escribir criterios de aceptación por error y evita mostrar mensajes crudos de la API.
- **Opciones:**
  - Catálogo cerrado en el spec, con texto y acción por error
  - Mensajes genéricos por familia de error (autenticación, límite, validación)
  - Detalle técnico siempre visible / en desplegable / nunca visible
- **Estudio de APIs:** §5.6 muestra ejemplos ("🔴 Error: usuario inválido" con acción "Corregir") y §2.4 detalla el manejo de 403/429; no hay un catálogo unificado.
- **Fusiona:** P688

### Q-transversal-19 — ¿Qué guía embebida tendrá la app y quién la produce? Decidir: (a) si la página del curso tiene un checklist de progreso ("Canvas vinculado, GitHub vinculado, estudiantes sincronizados, 7/10 usuarios de GitHub mapeados, 1 tarea") con enlaces a la acción pendiente; (b) qué forma toma la ayuda contextual: tooltips en términos técnicos (installation, override, SHA, repositorio plantilla), panel lateral "¿Cómo funciona esta pantalla?", página de ayuda/FAQ dentro de la app, tour la primera vez, o varias de ellas; (c) para lo que la app NO hace (crear un group set, asignar integrantes, configurar overrides, crear una rúbrica, crear la organización), si se muestra el mensaje "esto se configura en Canvas/GitHub" con enlace profundo a la pantalla exacta y un botón "ya lo hice, sincronizar"; (d) quién redacta esos textos, dónde se versionan y en qué fecha se revisan antes de la parcial.

- **Requisitos:** R2.1.6, R2.2.3, R2.2.5, R2.2.6, R2.7.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es el criterio explícito de la parcial ("facilidad de uso y guía adecuada"); el enunciado exige guiar al equipo docente en procesos que requieren información de ambas plataformas, y el spec debe listar los textos de ayuda como entregables con responsable y fecha.
- **Opciones:**
  - Checklist de progreso en la página del curso con enlaces a la acción pendiente
  - Tooltips en términos técnicos
  - Panel lateral "¿Cómo funciona esta pantalla?"
  - Página de ayuda/FAQ dentro de la app
  - Tour guiado la primera vez
  - Enlaces profundos a Canvas/GitHub con botón "ya lo hice, sincronizar"
  - Sin ayuda embebida (solo el video de la entrega)
- **Estudio de APIs:** §3.3 propone un checklist de verificación y §4.4 mostrar "datos de Canvas actualizados hace X min"; §4.3 identifica unassigned=true para detectar estudiantes sin grupo y §14 lista los prerrequisitos externos; no describe un onboarding global ni un mecanismo de ayuda en la UI.
- **Fusiona:** P659, P693

### Q-transversal-20 — Indicador "última sincronización": ¿con qué granularidad se registra y se muestra (por curso, por tarea, por fuente Canvas vs GitHub, por repositorio)? ¿Dónde se ubica (cabecera del curso, pie de cada tabla, tooltip del dato)? ¿Formato relativo ("hace 4 min") con tooltip absoluto en hora local? ¿Qué se muestra si nunca se sincronizó, si la ejecución está en curso, o si la última falló (fecha del último éxito más el aviso "la sincronización de las 10:30 falló")?

- **Requisitos:** R2.2.1, R2.4.4, R2.5.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es el indicador que da confianza en datos que pueden tener 10–15 min de antigüedad; el spec debe fijar ubicación, granularidad, formato y los cuatro estados (nunca / ok / fallida / en curso).
- **Opciones:**
  - Un indicador global por curso
  - Un indicador por fuente (Canvas / GitHub)
  - Un indicador por tabla o por dato, con tooltip
  - Formato relativo con tooltip absoluto / solo absoluto
- **Estudio de APIs:** §4.4 indica "registren last_synced_at y muéstrenlo en la UI (datos de Canvas actualizados hace 4 min)" y §7.4 lo repite; no define granularidad ni estados de fallo.
- **Fusiona:** P689

### Q-transversal-21 — ¿Existe un botón "Sincronizar ahora"? Si sí: ¿para qué fuentes (roster de Canvas, fechas de Canvas, entregas de la tarea de registro de usuario de GitHub, commits de GitHub, disparar aprovisionamiento)? ¿Uno global por curso o uno por fuente? ¿Qué permiso se requiere para pulsarlo? ¿Se deshabilita mientras corre y tiene cooldown o debounce para respetar el throttling de Canvas? ¿Qué feedback da al terminar ("2 estudiantes nuevos, 1 fecha cambiada, 0 errores")? ¿Cómo se documenta que es complementario y que la creación de repositorios sigue siendo automática, sin interacción directa de un usuario (R2.3.10)?

- **Requisitos:** R2.2.1, R2.3.10, R2.4.4
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Afecta la demo (evitar esperas de 2–10 min), la percepción de datos frescos y la coherencia con el requisito de automatismo; un clic repetido puede además agotar el rate limit del token del profesor durante la evaluación.
- **Opciones:**
  - Sin botón (solo sincronización automática)
  - Botón global por curso
  - Botones por fuente con cooldown
  - Botón visible solo para el profesor / también para ayudantes
- **Estudio de APIs:** §7.4 recomienda ofrecer "sincronizar ahora" para la demo; §1.5 exige concurrencia 1 por token de Canvas; §5.5 advierte que "no sirve un botón crear repos" como mecanismo principal.
- **Fusiona:** P690

### Q-transversal-22 — ¿Qué acciones requieren confirmación explícita y con qué fuerza (modal simple, escribir el nombre del recurso, doble confirmación)? Lista a decidir: eliminar curso; desvincular Canvas o GitHub; eliminar tarea (¿y sus repositorios en GitHub: se borran, se archivan o se dejan intactos?); retirar a un ayudante con correcciones pendientes; cambiar el usuario de GitHub de un estudiante que ya tiene repositorio con commits; reenviar invitación; publicar una nota en Canvas cuando ya existe una; enviar un anuncio o mensaje masivo (mostrando el número de destinatarios); "reintentar todos los fallidos". ¿Existe "deshacer" para alguna de ellas y se registra quién ejecutó cada acción?

- **Requisitos:** R2.1.3, R2.1.9, R2.2.5, R2.6.5, R2.6.6, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Cada acción destructiva necesita un flujo de UI definido y una regla de negocio sobre sus efectos en sistemas externos (GitHub/Canvas), que no se pueden revertir desde la app.
- **Opciones:**
  - Modal simple para todas las acciones destructivas
  - Escribir el nombre del recurso para las irreversibles y modal simple para el resto
  - Confirmación con recuento de efectos externos ("se archivarán 37 repositorios")
  - Sin confirmaciones, con "deshacer" donde sea posible
- **Estudio de APIs:** §3.4 indica los efectos al retirar a un ayudante (reasignar entregas, revocar acceso a la organización); el resto no lo aborda.
- **Fusiona:** P692

### Q-transversal-23 — ¿La app muestra un registro visible para el equipo docente de los cambios detectados en cada sincronización (nuevo estudiante, estudiante retirado, cambio de sección, cambio de integrantes de un grupo, cambio de fecha con valor anterior→nuevo, tarea de Canvas eliminada)? ¿Dónde vive (pestaña "Actividad" del curso, panel dentro de la tarea, ambas)? ¿Con qué retención y con qué filtros por tipo de cambio?

- **Requisitos:** R2.2.1, R2.2.3, R2.4.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Permite al docente entender por qué algo cambió sin ir a Canvas; define la UI que consume la auditoría de sincronización y su política de retención.
- **Opciones:**
  - Pestaña "Actividad" por curso con filtros por tipo
  - Panel de cambios recientes dentro de cada tarea
  - Solo en el informe diario, sin vista en la app
  - Sin registro visible
- **Estudio de APIs:** §7.4 propone "registrar en un log de auditoría: quién/cuándo/de qué a qué" para los cambios de fecha; no lo generaliza al roster ni define su UI.
- **Fusiona:** P691

### Q-transversal-24 — ¿Qué nivel de accesibilidad se compromete: WCAG 2.1 AA completo, o un conjunto mínimo explícito (contraste AA, foco visible, navegación completa por teclado en el wizard, las tablas y la pantalla de corrección de R2.7.3, labels en todos los campos, y estados nunca comunicados solo por color)? ¿Se aceptan emojis como indicadores de estado en producción (✅ 🟡 🔴 📌 ⚠) o se exigen iconos SVG más etiqueta textual, considerando que los emojis se ven distinto entre sistemas operativos y navegadores y son ambiguos en un proyector? ¿Se audita con Lighthouse o axe como criterio de aceptación antes de cada entrega?

- **Requisitos:** R2.3.11, R2.5.5, R2.7.3, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** La tabla de estados propuesta usa semáforos de color; sin texto alternativo es inaccesible y ambigua en proyector. Convierte la accesibilidad en criterios de aceptación concretos en vez de una aspiración.
- **Opciones:**
  - WCAG 2.1 AA como compromiso formal, auditado con Lighthouse/axe
  - Lista mínima explícita de reglas, sin referencia a WCAG
  - Emojis permitidos como indicador / solo SVG + etiqueta textual
  - Sin compromiso de accesibilidad
- **Estudio de APIs:** §5.6 y §8.6 proponen iconos y emojis de color como indicadores de estado y §10.1 atajos de teclado; no aborda accesibilidad.
- **Fusiona:** P674, P696

### Q-transversal-25 — ¿Qué dispositivos y resoluciones se soportan: solo escritorio (demo presencial en proyector, 1366×768 / 1920×1080), desktop-first con degradación legible en tablet y móvil, o totalmente responsive? ¿Qué vistas deben funcionar bien en móvil (p. ej., un ayudante revisando "mis correcciones", el profesor mirando alertas) y cuáles pueden declararse "solo escritorio" (dashboard, tablas anchas)? ¿Las tablas anchas (estado de repositorios, dashboard) llevan scroll horizontal propio o una versión de tarjetas? ¿En qué resolución y con qué proyector se probará la demo antes del 16-sep?

- **Requisitos:** R2.3.11, R2.5.1, R2.7.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define breakpoints, qué tablas necesitan versión de tarjetas y el esfuerzo de frontend antes del 16-sep; un dashboard que no cabe en el proyector arruina la demo.
- **Opciones:**
  - Solo escritorio, declarado explícitamente en el spec
  - Desktop-first con degradación legible en tablet/móvil
  - Totalmente responsive en todas las vistas
  - Responsive solo en las vistas del ayudante
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P675, P697

## Sesion, autorizacion, credenciales y datos personales

### Q-transversal-26 — ¿Cómo se implementa la sesión de la app y su seguridad? Decidir: (a) cookie HttpOnly/Secure/SameSite firmada respaldada en servidor (BD/Redis) o stateless (JWT); (b) duración (8 h, 7 días, "recordarme"), expiración por inactividad y cierre de sesión global; (c) si al retirar a un ayudante (R2.1.9) o cambiar sus permisos su sesión activa se invalida de inmediato, lo que exige verificar el rol en cada request; (d) protección CSRF (token por formulario del framework más SameSite) y validación del parámetro state en los tres flujos OAuth (Google, Canvas, GitHub setup), guardado en un almacén que sobreviva a reinicios o al sleep de la instancia del PaaS; (e) si el cierre de sesión en la app solo termina la sesión local o también revoca el token de Canvas (DELETE /login/oauth2/token), lo que detendría los jobs nocturnos que dependen del refresh_token del profesor.

- **Requisitos:** R2.1.1, R2.1.2, R2.1.4, R2.1.8, R2.1.9
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define criterios de aceptación de seguridad verificables y el comportamiento observable al retirar a un ayudante; un state en memoria se pierde con el reinicio del PaaS y rompe el login, y un logout que revoca credenciales de Canvas detiene sync, snapshots e informes.
- **Opciones:**
  - Sesión de servidor con cookie firmada
  - JWT stateless
  - Verificación de rol en cada request (invalidación inmediata) / caché de rol con expiración
  - Logout local sin revocar Canvas / logout que revoca el token de Canvas / opción explícita separada "revocar credenciales"
- **Estudio de APIs:** §1.1 subraya que "state es obligatorio en la práctica" y documenta la revocación del token, advirtiendo que el refresh_token almacenado es crítico para R2.6.1 y R2.4.5; no cubre sesiones ni CSRF de la app.
- **Fusiona:** P677, P699

### Q-transversal-27 — ¿La autorización se verifica en el servidor en cada endpoint contra la membresía y los permisos del usuario en ESE curso, y no solo ocultando botones en la UI? ¿Los IDs en las URLs son secuenciales (permiten enumerar cursos ajenos) o UUID/slug? ¿Un ayudante puede ver repositorios, estudiantes o notas de entregas que no tiene asignadas? ¿Se escriben tests automatizados de autorización (el usuario A no accede a recursos del curso B; un ayudante no ejecuta acciones de profesor por URL directa)?

- **Requisitos:** R2.1.7, R2.1.8, R2.7.2, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** El enunciado exige al menos 3 permisos administrables; sin enforcement en el servidor y sin tests, el control de acceso es cosmético y un IDOR expone datos de estudiantes de otros cursos.
- **Opciones:**
  - Enforcement server-side en cada endpoint con tests automatizados de autorización
  - Enforcement server-side sin tests dedicados
  - IDs secuenciales / UUID o slug no adivinable
  - Ayudante limitado a sus asignaciones / con visibilidad de todo el curso
- **Estudio de APIs:** §3.4 propone una tabla de permisos (no aprobada); no trata el enforcement ni el riesgo de IDOR.
- **Fusiona:** P678

### Q-transversal-28 — ¿Cómo se almacenan los secretos y tokens (refresh_token de Canvas, archivo .pem de la GitHub App, webhook secret, client_secret de Google): cifrados en la BD y con qué clave y gestor, o en variables de entorno del despliegue? ¿Se ofrece al profesor un botón "revocar / rotar credenciales del curso"? ¿Qué muestra la UI sobre cada credencial (nunca el valor; sí fecha de autorización, usuario que autorizó y estado)?

- **Requisitos:** R2.1.4, R2.1.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define requisitos de seguridad verificables y una funcionalidad de administración de la vinculación; el código se entrega por GitHub y un secreto commiteado es un hallazgo evidente para el evaluador.
- **Opciones:**
  - Cifrado en BD con clave en variable de entorno
  - Solo variables de entorno del despliegue, sin persistir en BD
  - Gestor de secretos del proveedor de hosting
  - Botón de revocar/rotar credenciales disponible / no disponible
- **Estudio de APIs:** §1.1 indica "guarden el refresh_token cifrado en BD"; §14 indica "Secretos: variables de entorno, no al repo".
- **Fusiona:** P700

### Q-transversal-29 — Si el refresh token del profesor deja de funcionar (revocó la app en Canvas, replace_tokens, Developer Key deshabilitada, profesor retirado del curso), todos los jobs del curso fallan de madrugada. ¿Cómo se detecta (401 en el refresh), cómo se pausa el curso para evitar una tormenta de reintentos, y cómo se avisa (banner en la UI, email al profesor, entrada en el informe diario)? ¿Cómo se evita que dos jobs refresquen el mismo token simultáneamente (lock o single-flight)? ¿Qué ocurre si el único profesor con token válido se retira y quedan otros profesores que nunca autorizaron Canvas? ¿Se adopta el token del profesor (opción A del estudio) o un token por usuario (opción B)?

- **Requisitos:** R2.3.12, R2.4.4, R2.4.5, R2.6.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** si
- **Por que importa:** Define en términos operativos la elección A/B del estudio y el estado "credenciales rotas" que la UI debe mostrar; sin él, un curso queda mudo durante días sin que nadie lo note.
- **Opciones:**
  - Token del profesor que vinculó el curso (opción A)
  - Token por usuario, con el del profesor como respaldo de los jobs (opción B)
  - Pausa automática del curso ante credencial rota / reintento indefinido
  - Aviso por banner en la UI / email al profesor / entrada en el informe diario / los tres
- **Estudio de APIs:** §1.1 subraya la criticidad del refresh token; §3.4 plantea las opciones A (token del profesor) y B (token por usuario). No cubre la revocación ni la concurrencia del refresh.
- **Fusiona:** P676

### Q-transversal-30 — ¿Qué datos personales de estudiantes se persisten y qué se comunica sobre ellos? Decidir: (a) lista blanca de campos guardados (nombre, correo, sis_user_id, canvas_user_id, login de GitHub, avatar) y descarte explícito de los que llegan en las respuestas y no se necesitan —GET /enrollments devuelve el objeto grades con current_score/final_score, además de login_id y sis_user_id—; (b) si los ayudantes ven correos y sis_id; (c) si el informe diario por email incluye nombres de estudiantes "sin participación", sabiendo que viaja por un proveedor SMTP de terceros; (d) política de retención y borrado al eliminar un curso, al concluir el semestre y al terminar las 2 semanas de disponibilidad; (e) si se informa a los estudiantes (anuncio inicial en Canvas o texto en la tarea de registro) qué datos se recopilan, para qué y quién los ve, y si se requiere el visto bueno del profesor o de la universidad; (f) si hay una nota de privacidad en la app y si se evita PII en los logs.

- **Requisitos:** R2.2.1, R2.5.2, R2.5.4, R2.6.1, R2.6.4, R2.6.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** si
- **Por que importa:** La app concentra datos académicos en infraestructura gratuita de terceros y monitorea la actividad de estudiantes que no son usuarios; el spec debe fijar qué se guarda, quién lo ve, qué se les informa y cuándo se borra.
- **Opciones:**
  - Lista blanca de campos persistidos con descarte explícito de grades y campos no necesarios
  - Persistir la respuesta completa de la API y filtrar en la presentación
  - Anuncio informativo a los estudiantes al vincular el curso o crear la primera tarea
  - Texto informativo en la descripción de la tarea de registro
  - Sin aviso a los estudiantes
  - Nota de privacidad en la app / sin nota
- **Estudio de APIs:** §4.1 muestra que /enrollments trae el objeto grades; §5.4 pide nombres de repositorio "que no filtren datos sensibles" y §4.4 "nunca borren filas, marquen deleted_at"; §14 y §3.1 no mencionan aviso a estudiantes ni minimización de campos.
- **Fusiona:** P679, P686

### Q-transversal-31 — ¿Se activan cabeceras de seguridad (HSTS, X-Content-Type-Options, CSP básica, frame-ancestors) y se sanitiza el HTML proveniente de Canvas (descripciones de tareas, bodies de submissions, nombres) antes de renderizarlo en la app, para evitar XSS almacenado? ¿Se ejecuta Dependabot, npm audit o pip-audit en CI y con qué política de actualización? ¿Hay rate limiting propio en los endpoints públicos (webhook, unsubscribe, callbacks OAuth)?

- **Requisitos:** R2.2.4, R2.3.1, R2.5.2, R2.6.3
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Los bodies de submissions son texto controlado por estudiantes que la app muestra a docentes: es el vector de XSS más directo del sistema, y los endpoints públicos son alcanzables por cualquiera.
- **Opciones:**
  - Sanitización con librería de allowlist + cabeceras completas + auditoría de dependencias en CI
  - Renderizar el HTML de Canvas como texto plano (escapado), sin sanitizador
  - Cabeceras mínimas sin CSP
  - Rate limiting propio en endpoints públicos / sin rate limiting propio
- **Estudio de APIs:** §6.1 limpia tags del body solo para parsear el login; no trata XSS, cabeceras de seguridad ni auditoría de dependencias.
- **Fusiona:** P680

### Q-transversal-32 — ¿El enlace de "darse de baja" del email usa un token firmado (HMAC/JWT) con expiración y de un solo uso, o un token permanente? ¿La baja es inmediata al hacer clic —los escáneres de correo siguen los enlaces y producirían bajas involuntarias— o hay una página de confirmación? ¿El mismo mecanismo permite volver a suscribirse sin login?

- **Requisitos:** R2.6.3, R2.6.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.6.3 exige suscripción y baja individuales; el diseño del token define la seguridad del mecanismo y los criterios de aceptación del email.
- **Opciones:**
  - Token firmado con expiración y un solo uso
  - Token firmado permanente
  - Baja inmediata al hacer clic
  - Página de confirmación antes de aplicar la baja
  - Re-suscripción por el mismo enlace / solo desde la app con login
- **Estudio de APIs:** §9.1 propone un "link de darse de baja en el pie del email (con token firmado, sin login)".
- **Fusiona:** P681

## Integracion con APIs externas: limites, concurrencia y resiliencia

### Q-transversal-33 — ¿Existe un limitador de tasa COMPARTIDO por instalación de GitHub y por token de Canvas entre todos los procesos que escriben, o cada worker tiene su propio throttle? Decidir: (a) para Canvas, si se fija concurrencia 1 por token (cola secuencial por curso) y cómo se coordina cuando el mismo token del profesor lo usan a la vez la UI ("sincronizar ahora", checklist de verificación de R2.1.6), el cron de sync y el envío masivo de Conversations; (b) para GitHub, si hay un token-bucket persistido y compartido (¿en BD o Redis?) con prioridades entre efectos (creación de repositorios y generate, subida de archivos del repositorio base, PUT de colaboradores, revocación y reenvío de invitaciones, tags de cierre, cambios de configuración del repositorio, acciones manuales del docente), throttles independientes por worker aceptando los 403 secundarios con backoff, o una única cola global serializada; (c) el throttle concreto del creador de repositorios (p. ej. 1 repositorio cada 3–5 s), si se usa el plugin de throttling de Octokit o uno propio, y para qué tamaño máximo de curso se dimensiona y se prueba (¿60 estudiantes? ¿300?), documentándolo como requisito no funcional; (d) qué se posterga y qué muestra la UI cuando la cuota se agota (contador, ETA, "capturando 12/40, reanuda en X min"); (e) si la misma decisión aplica al presupuesto de lectura del reconciliador de commits; (f) si se muestran X-Rate-Limit-Remaining y X-Request-Cost en un panel de diagnóstico. Escenario concreto a soportar: 40 repositorios venciendo a la misma hora (40 tags) mientras el worker aprovisiona una tarea nueva de 60 repositorios y un ayudante pulsa "reintentar todos los fallidos".

- **Requisitos:** R2.1.6, R2.2.1, R2.3.6, R2.3.7, R2.3.9, R2.3.10, R2.4.4, R2.4.5, R2.6.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** GitHub limita a 80 requests generadoras de contenido por minuto y 900 puntos por minuto (crear repositorio + colaboradores + archivos suma unos 40 puntos por grupo) y Canvas devuelve 403 Rate Limit Exceeded por token; sin limitador compartido los workers se sabotean entre sí, un profesor con clics repetidos bloquea los jobs de su propio curso, y el 6-oct el revisor ve tareas colgadas en "CREATING".
- **Opciones:**
  - Token-bucket persistido y compartido, con prioridades entre tipos de efecto
  - Throttles independientes por worker, aceptando 403 secundarios con backoff
  - Cola global única que serializa todos los efectos de GitHub
  - Concurrencia 1 por token de Canvas (cola secuencial por curso)
  - Plugin de throttling de Octokit / implementación propia
  - Panel de diagnóstico de rate limit visible / oculto
- **Estudio de APIs:** §2.4 fija los límites primarios y secundarios de GitHub y §1.5 el throttling por token de Canvas recomendando "secuencial por curso (concurrencia 1 por token)"; §5.5 propone "máximo ~1 repo cada 3 s" y §7.5 advierte que los tags también son requests generadoras de contenido; §7.4 sugiere el botón "sincronizar ahora". El estudio no propone un limitador compartido ni prioridades entre workers.
- **Fusiona:** P667, P668, N034

### Q-transversal-34 — ¿Cuál es la política uniforme de reintentos por tipo de fallo y cuándo se deja de reintentar? Decidir: 5xx y timeouts (backoff exponencial: ¿máximo de intentos y tope de espera?), 403/429 por rate limit (respetar retry-after y x-ratelimit-reset), 401 token inválido (no reintentar, marcar credencial rota), 404 recurso eliminado (no reintentar, marcar), 422 de validación (no reintentar, mostrar error). ¿Tras N fallos el ítem pasa a ERROR y exige un "reintentar" manual, o se reintenta indefinidamente con espera creciente? Y ante errores SOSTENIDOS de Canvas o GitHub (caída, 401 por token revocado, 404 por curso concluido o tarea eliminada, GitHub App desinstalada de la organización): ¿se pausan los jobs del curso con un circuit breaker para no acumular reintentos ni consumir rate limit? ¿Cómo se muestra en la UI ("Canvas no responde desde hace 20 min", "la App fue desinstalada: reinstalar"), a quién se notifica, y se reanuda automáticamente al recuperarse o requiere acción del profesor?

- **Requisitos:** R2.1.6, R2.3.11, R2.4.4, R2.5.5, R2.6.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija el comportamiento observable en la tabla de estados (R2.3.11) y en el informe diario, evita tormentas de reintentos que agotan los rate limits, y define los estados de salud por curso para que un curso roto no degrade a los demás.
- **Opciones:**
  - Política por familia de código HTTP con máximo de intentos y paso a ERROR
  - Reintento indefinido con espera creciente, sin estado ERROR terminal
  - Circuit breaker por curso con reanudación automática
  - Circuit breaker por curso que exige acción explícita del profesor para reanudar
  - Sin circuit breaker (solo backoff por ítem)
- **Estudio de APIs:** §2.4 propone ghRequest con 5 intentos y backoff y §1.5 backoff ante 403/429, sin distinguir 401/404/422; §5.5 define un estado ERROR por sujeto. No cubre fallos prolongados ni la desinstalación de la App.
- **Fusiona:** P666, P683

### Q-transversal-35 — ¿Se implementa un iterador genérico de paginación que siga el header Link opaco de Canvas y GitHub, con tests y un límite de seguridad de páginas para evitar bucles infinitos, o se usan octokit.paginate y una librería para Canvas? En la UI, ¿las tablas son paginadas o virtualizadas para cursos grandes (200+ estudiantes), o se asume menos de 100 filas y se listan completas?

- **Requisitos:** R2.2.1, R2.2.3, R2.3.11, R2.5.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** El default de Canvas es 10 ítems por página: sin paginación se "pierden" estudiantes silenciosamente; y las tablas de estado y del dashboard deben seguir siendo usables con muchos repositorios.
- **Opciones:**
  - Iterador genérico propio con tests y límite de páginas
  - octokit.paginate para GitHub y librería o cliente propio para Canvas
  - Tablas de UI paginadas en servidor
  - Tablas de UI virtualizadas en cliente
  - Listado completo asumiendo cursos pequeños, documentado como límite
- **Estudio de APIs:** §1.4 describe la paginación de Canvas (per_page=100, header Link opaco) y §2.5 la de GitHub.
- **Fusiona:** P670

### Q-transversal-36 — ¿Qué timeouts se fijan: cliente HTTP hacia Canvas y GitHub (p. ej. 30 s), duración máxima de un job, y duración máxima de una request web (los PaaS suelen cortar a unos 30 s)? ¿El checklist de verificación de R2.1.6 (8 chequeos, que incluyen crear y borrar un repositorio temporal) se ejecuta dentro de la request, o de forma asíncrona con polling/SSE desde la UI mostrando resultados parciales?

- **Requisitos:** R2.1.6, R2.3.6, R2.5.1
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Un checklist síncrono puede superar el timeout del PaaS y mostrar un error genérico justo en la pantalla que se evalúa como "guía adecuada" el 16-sep.
- **Opciones:**
  - Checklist síncrono dentro de la request
  - Checklist asíncrono con polling desde la UI y resultados parciales
  - Checklist asíncrono con SSE/WebSocket
  - Timeouts uniformes para todos los clientes / distintos por operación
- **Estudio de APIs:** §1.4 muestra un snippet con timeout=30 y §3.3 un checklist con botón "reintentar", sin decir si es síncrono.
- **Fusiona:** P671

### Q-transversal-37 — ¿Para qué escala se diseña y se prueba: cuántos cursos simultáneos, estudiantes por curso, repositorios por tarea y commits por repositorio (p. ej. 3 cursos × 100 estudiantes × 3 tareas = 900 repositorios)? ¿Qué objetivo de tiempo de carga del dashboard se fija (p. ej. menos de 1 s p95 leyendo solo de la BD) y qué latencia "push en GitHub → visible en el dashboard" (segundos con webhook; hasta 15 min con polling)? ¿Se ejecuta una prueba de carga sintética antes de la entrega final y con qué dataset?

- **Requisitos:** R2.3.10, R2.5.1, R2.5.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Convierte "de forma inmediata" (R2.5.1) y "reciente" (R2.5.3) en números verificables, y dimensiona los rate limits, la cola y la base de datos del plan gratuito.
- **Opciones:**
  - Escala objetivo declarada como requisito no funcional, con prueba de carga sintética
  - Escala objetivo declarada sin prueba de carga
  - Sin escala declarada (solo el tamaño del curso de demo)
- **Estudio de APIs:** §2.1 usa un ejemplo con 60 estudiantes y 60 repositorios; §8.3 promete "milisegundos" para el dashboard leyendo de tablas agregadas.
- **Fusiona:** P682

### Q-transversal-38 — Verificar contra la API real que un GET /repos/{owner}/{repo}/commits con If-None-Match que devuelve 304 efectivamente no descuenta del rate limit primario del installation token, y medir el costo real de un ciclo de reconciliación con N repositorios. Con el resultado: ¿cada cuántos minutos se reconcilia y con qué tope de repositorios por ciclo?

- **Requisitos:** R2.5.2, R2.5.3
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El estudio basa la viabilidad del polling de 60+ repositorios en este comportamiento; si no se cumple, hay que reducir la frecuencia o depender más de los webhooks.
- **Opciones:**
  - Reconciliación cada 15 min con ETag y tope de repositorios por ciclo
  - Frecuencia menor si el 304 sí descuenta
  - Depender principalmente de webhooks y reconciliar solo como red de seguridad
- **Estudio de APIs:** §2.4 lo llama un "truco que vale oro" (el 304 no descuenta) y §8.2 propone un reconciliador cada 15 min con ETag.
- **Fusiona:** P669

### Q-transversal-39 — Si el profesor y los ayudantes evalúan las apps de varios equipos del curso el mismo día contra la MISMA organización de GitHub o el mismo curso de Canvas, ¿qué límites se comparten y cómo se comporta la app al chocar con ellos? Verificar empíricamente: si los límites secundarios de GitHub (80 requests generadoras de contenido por minuto, 500 por hora, 900 puntos/min) se contabilizan por instalación de la App o también por organización o por repositorio; si dos apps creando repositorios simultáneamente en la misma organización se bloquean entre sí; si existe un tope de invitaciones por organización que se agote entre todos; si varios equipos poleando el mismo curso de Canvas con tokens distintos comparten alguna cuota del curso además de la cuota por token. Y decidir: ante 403/429, ¿la app muestra "esperando por límite de GitHub, reintenta en X" como estado transitorio con reintento automático, o marca ERROR definitivo (que el revisor leerá como fallo del equipo)?

- **Requisitos:** R2.3.7, R2.3.9, R2.3.10, R2.3.11
- **Tipo:** verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es el escenario más probable de fallo simultáneo el día de la revisión y no depende del código propio. Determina el texto y el estado que verá el revisor, la política de reintentos, y puede obligar a exigir una organización de GitHub separada por equipo en lugar de la del profesor.
- **Opciones:**
  - Estado transitorio "esperando por límite" con reintento automático
  - Estado ERROR definitivo con reintento manual
  - Exigir una organización de GitHub por equipo para la evaluación
- **Estudio de APIs:** §2.4 documenta los límites primarios y secundarios de GitHub y §1.5 el throttling por token de Canvas, pero analiza siempre una sola app operando sobre la organización o el curso.
- **Fusiona:** N011

## Consistencia de efectos externos, trabajos en cola y recuperacion

### Q-transversal-40 — Para las acciones disparadas desde la UI —"crear repositorio base", "sincronizar ahora", "reintentar todos los fallidos", "reenviar invitación", "publicar nota" y "enviar anuncio"—: ¿qué garantía de idempotencia se exige (botón deshabilitado mientras corre, token de idempotencia por formulario, cola con deduplicación) y cuál es el comportamiento visible si el usuario repite la acción o hace doble clic ("ya en curso", segunda ejecución ignorada silenciosamente, o duplicado aceptado)?

- **Requisitos:** R2.3.5, R2.3.10, R2.4.4, R2.6.5, R2.6.6, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Un anuncio o una nota duplicados son visibles para los estudiantes; el spec debe definir criterios de aceptación de idempotencia por acción de UI, no solo en el worker.
- **Opciones:**
  - Botón deshabilitado mientras la acción está en curso
  - Token de idempotencia por formulario, con respuesta "ya en curso"
  - Cola con deduplicación por clave de acción
  - Duplicados aceptados y visibles en el historial
- **Estudio de APIs:** §5.5 trata la idempotencia del worker y §9.4 propone un outbox con constraint único (kind, target, delivery_id); no cubre las acciones disparadas desde la UI.
- **Fusiona:** P662

### Q-transversal-41 — ¿Cuál es la regla única de consistencia entre la base de datos y los efectos externos? Decidir: (a) el orden obligatorio: ¿se persiste una fila de intención ANTES de llamar (con el nombre del repositorio, el destinatario, el SHA del tag, el payload de la nota) y se marca el resultado después, o se llama primero y se registra al volver?; (b) qué se hace en la ventana en que la llamada tuvo éxito pero la app murió antes de registrarlo; (c) qué clave de idempotencia se define por efecto: mensaje o comentario al estudiante (unique (kind, target, delivery)), anuncio por cambio de fecha (¿uno por cambio o uno por día?), publicación de nota (el re-PUT sobreescribe en Canvas: ¿se permite? ¿se registra quién y cuándo?), creación de tag (422 → verificar SHA; ¿qué hacer si el tag existe con OTRO SHA?), procesamiento de webhooks (guardar X-GitHub-Delivery para descartar duplicados), creación de repositorio (más allá del 422 "name already exists"); (d) la clasificación de cada efecto según sea VERIFICABLE por lectura antes de reintentar —repositorio (GET por nombre/id), colaborador e invitación (GET /collaborators, /invitations), tag (GET /git/ref), nota (GET submission)— o NO verificable de forma fiable —POST /conversations y los comentarios de submission no tienen clave propia consultable, de modo que un reintento tras un timeout puede duplicar el mensaje al estudiante y un anuncio duplicado queda visible para todo el curso—; (e) qué se hace con los no verificables: aceptar el riesgo de duplicado, no reintentar nunca ante resultado desconocido y dejarlo para acción manual, o buscar heurísticamente en Canvas (listar conversaciones o anuncios recientes) antes de reenviar.

- **Requisitos:** R2.3.7, R2.3.9, R2.3.12, R2.4.5, R2.5.2, R2.6.5, R2.6.6, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es la diferencia entre un reinicio del worker que no deja rastro y uno que envía 60 mensajes repetidos a estudiantes reales o crea repositorios huérfanos que la BD no conoce; define columnas (intent_id, external_id, estado desconocido), la regla de reintento por tipo de efecto y, en el caso "tag con otro SHA", cuál es la fuente de verdad (R2.4.7).
- **Opciones:**
  - Persistir la intención antes de llamar y marcar el resultado después (outbox de intenciones)
  - Llamar primero y registrar al volver
  - Verificación por lectura antes de cada reintento, cuando el efecto es consultable
  - Ante resultado desconocido en efectos no verificables: no reintentar y escalar a acción manual
  - Ante resultado desconocido: reintentar aceptando el riesgo de duplicado
  - Búsqueda heurística en Canvas (conversaciones o anuncios recientes) antes de reenviar
- **Estudio de APIs:** §5.5 propone idempotencia apoyada en el 422 "name already exists", §7.5 verificar el SHA cuando el tag ya existe y §9.4 un outbox con constraint único (kind, target, delivery_id); no cubre las notas ni los webhooks duplicados, ni la ventana entre una llamada exitosa y su registro en BD, ni distingue efectos verificables de no verificables.
- **Fusiona:** P665, N035

### Q-transversal-42 — Entre que un trabajo se encola o se programa y se ejecuta pueden pasar minutos u horas, y el mundo cambia. ¿Cada job REVALIDA sus precondiciones inmediatamente antes de actuar (releyendo el estado del sujeto dentro del lock antes de llamar a la API externa), o confía en que quien invalidó la condición canceló la fila? Casos: crear el repositorio de un estudiante que fue retirado o cuyo mapeo cambió mientras estaba en cola; capturar el snapshot de una entrega que fue desvinculada, cuya assignment fue eliminada en Canvas o cuya tarea fue archivada; crear el tag en un repositorio que fue archivado, renombrado o eliminado; enviar "repositorio disponible" cuando el repositorio pasó a ERROR o se recreó; publicar la nota de una corrección cuyo snapshot quedó SUPERSEDED. ¿Qué se registra cuando la revalidación falla (estado CANCELADO con motivo visible en la bitácora, o silencio) y quién lo ve? ¿Existe además una cancelación explícita al detectar el cambio, o la revalidación tardía es el único mecanismo?

- **Requisitos:** R2.3.10, R2.4.5, R2.6.5, R2.6.7, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Determina si cada worker debe releer el estado del sujeto antes de llamar a la API externa y define un campo de motivo de cancelación en cada tabla de trabajo; sin esta regla se producen efectos externos indeseables (invitar a un retirado, avisar de un repositorio inexistente) que en la revisión se leen como bugs.
- **Opciones:**
  - Revalidación obligatoria de precondiciones dentro del lock, con estado CANCELADO y motivo
  - Cancelación explícita de trabajos al detectar el cambio, sin revalidación tardía
  - Ambos mecanismos combinados
  - Sin revalidación: se ejecuta lo encolado y se corrige después
- **Estudio de APIs:** §5.5 y §7.5 describen jobs que barren estado y son idempotentes, pero no abordan la revalidación de precondiciones al momento de ejecutar ni la cancelación de trabajo obsoleto.
- **Fusiona:** N030

### Q-transversal-43 — ¿La app aplica de inmediato cada cambio detectado en Canvas o espera una VENTANA DE GRACIA antes de ejecutar los efectos externos derivados? Un profesor reorganizando grupos, moviendo estudiantes de sección o ajustando fechas produce estados transitorios: en 10 minutos un estudiante puede entrar y salir de un grupo, y el reconciliador quitaría y volvería a agregar colaboradores, renombraría descripciones de repositorios, recalcularía fechas y podría publicar dos anuncios contradictorios. Decidir: (a) aplicar todo en el ciclo siguiente sin espera; (b) ventana de quietud configurable (p. ej. 30–60 min de estabilidad) solo para efectos destructivos o irreversibles (quitar colaborador, anunciar cambio de fecha, mensaje al estudiante) y aplicación inmediata para los aditivos (agregar colaborador, crear repositorio); (c) dejar toda diferencia destructiva como "cambio detectado, se aplicará en N min" con opción de aplicar o descartar por el docente. ¿Se detecta la oscilación (un mismo campo cambiando ida y vuelta N veces) y se marca para revisión humana? ¿Qué muestra la UI mientras el cambio está en espera y qué columnas se necesitan (pending_change, aplicar_despues_de, detectado_en)?

- **Requisitos:** R2.2.3, R2.3.9, R2.4.4, R2.6.6, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Fija si el reconciliador es inmediato o diferido y qué columnas necesita; impacta directamente en cuántos correos recibe un estudiante y en si el equipo docente ve el sistema como estable o como ruido durante la revisión del 6–20 de octubre.
- **Opciones:**
  - Aplicación inmediata en el ciclo siguiente
  - Ventana de quietud solo para efectos destructivos o irreversibles
  - Cola de cambios pendientes con confirmación docente
  - Ventana de quietud global configurable por curso
  - Detección de oscilación con marca para revisión humana / sin detección
- **Estudio de APIs:** §4.4 y §7.4 asumen aplicar en cada ciclo lo detectado (upsert por canvas_id, recalcular fechas, anunciar si el cambio supera 1 h) y no abordan estados transitorios, oscilaciones ni ventanas de gracia para efectos destructivos.
- **Fusiona:** N031

### Q-transversal-44 — ¿Se escribe un catálogo cerrado de fallas DEL LADO DEL ESTUDIANTE, complementario al catálogo de errores de la UI docente, con cada caso acompañado de su texto de autoayuda, la ubicación de ese texto, si la app la detecta y con qué señal, y quién la resuelve? Casos mínimos a cubrir: no llegó el correo de invitación o cayó en spam; intentó aceptar con otra cuenta de GitHub; el enlace del repositorio da 404; no puede autenticarse para clonar o hacer push; registró mal su usuario y la tarea de registro ya cerró; borró o renombró la rama por defecto; su cuenta de GitHub fue suspendida o eliminada; nunca vio los mensajes porque no revisa Canvas. Para cada uno: ¿es visible para la app (aparece como estado en R2.3.11) o es invisible y por lo tanto exige un canal humano explícito y publicado (a quién escribir, en qué horario, con qué tiempo de respuesta)?

- **Requisitos:** R2.2.5, R2.3.11, R2.3.12, R2.6.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** El estudiante no tiene acceso a la app, así que cada falla suya se manifiesta solo como un estado ambiguo ("invitación pendiente", "sin commits"). Sin este catálogo el equipo no puede escribir los textos de R2.3.12 ni decidir qué estados de R2.3.11 hacen falta, y la usabilidad del enrolamiento queda a la improvisación.
- **Opciones:**
  - Página de Canvas del curso con FAQ, mantenida por el equipo
  - Bloque de ayuda en la descripción de la tarea de registro
  - README de cada repositorio con sección de problemas frecuentes
  - Solo canal humano (correo del ayudante) sin material escrito
  - Combinación de varios, con la asignación de cada falla a su canal
- **Estudio de APIs:** no lo aborda: el estudio cubre los estados de error del lado de la app (§5.6) y la validación del login (§6.1), pero no enumera las fallas del estudiante ni dónde vive su texto de ayuda.
- **Fusiona:** N024

### Q-transversal-45 — ¿Existirá un job periódico de VERIFICACIÓN DE INVARIANTES internos de la propia base de datos, con un panel de inconsistencias para el equipo? Invariantes candidatos: repositorio en estado READY sin ninguna fila de integrante aceptado; repositorio con github_repo_id nulo pero estado CREATED; snapshot CAPTURED cuyo repositorio ya no existe o cuyo SHA no pertenece a ese repositorio; mapeo VALIDADO cuyo login ya no resuelve en GitHub; sujeto activo de una tarea sin fila de fecha efectiva materializada; agregados diarios que no cuadran con la suma de commits; asignación de corrección apuntando a un ayudante retirado; filas de outbox marcadas "enviadas" sin id externo; entrega vinculada a una assignment que ya no existe en Canvas. Decidir: qué invariantes se comprueban, con qué frecuencia y sobre qué volumen; qué se hace ante una violación (solo listar, alertar en el informe diario, intentar auto-reparar, bloquear el worker del sujeto afectado); quién puede verlo; y si se muestra en la revisión como evidencia de robustez.

- **Requisitos:** R2.2.6, R2.3.11, R2.4.5, R2.5.5, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Los errores de los workers ocurren cuando nadie mira; sin este chequeo, la inconsistencia se descubre en la demo. Además fija si el spec exige auto-reparación (peligrosa) o solo detección, y da una pantalla concreta que defender el 7-oct.
- **Opciones:**
  - Job de invariantes con panel de inconsistencias, solo detección
  - Job de invariantes con auto-reparación de casos seguros y detección del resto
  - Alerta en el informe diario sin panel dedicado
  - Sin verificación de invariantes
- **Estudio de APIs:** no lo aborda: el estudio propone reconciliación contra GitHub (§8.2) y estados por repositorio (§5.6), pero ningún chequeo de consistencia interna del modelo de datos.
- **Fusiona:** N037

### Q-transversal-46 — Si la base de datos se restaura a un respaldo anterior (o se reprocesan jobs tras un fallo a mitad), ¿qué garantiza el diseño respecto a los efectos externos ya ocurridos que la BD "olvidó": repositorios ya creados (la adopción por 422, ¿verifica que sea el repositorio correcto y no uno ajeno?), colaboradores ya invitados o aceptados, tags ya creados (422 → comparar SHA), mensajes, comentarios y anuncios ya enviados (el outbox también se pierde con la BD: ¿se reenvían duplicados a los estudiantes?), notas ya publicadas (el re-PUT sobrescribe)? ¿Se define y se prueba un procedimiento de "reconciliación post-restauración" (leer GitHub y Canvas antes de reanudar los workers, o arrancar con las comunicaciones salientes en pausa)? ¿Con qué frecuencia se respalda y quién ejecuta la restauración?

- **Requisitos:** R2.3.7, R2.3.12, R2.4.5, R2.6.7, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Los efectos externos no son transaccionales con la base de datos; sin una regla, una restauración puede bombardear a los estudiantes con mensajes repetidos o adoptar repositorios equivocados.
- **Opciones:**
  - Reconciliación post-restauración obligatoria antes de reanudar workers
  - Arrancar con las comunicaciones salientes en pausa y liberarlas manualmente
  - Aceptar duplicados y avisar al equipo docente
  - Sin procedimiento definido (restauración manual caso a caso)
- **Estudio de APIs:** §5.5 trata el 422 como éxito y §9.4 propone un outbox con constraint único —que se pierde junto con la BD—; no aborda la restauración.
- **Fusiona:** P704

## Ya respondidas por el enunciado

Ninguna. En la etapa de verificacion las 63 preguntas de entrada de esta area (50 del archivo de consolidacion mas 13 de la ronda critica) quedaron marcadas ABIERTA o ABIERTA/BLOQUEA; el enunciado no responde textualmente ninguna de ellas, por lo que no se aparto ninguna del cuerpo del documento.
