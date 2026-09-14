# Preguntas de alcance — Area 2.2

70 preguntas finales, fusionadas desde 111 de entrada, 28 bloqueantes para la parcial.

## Estrategia de enrolamiento y alcance

### Q-2.2-01 — ¿Cuál es la estrategia de enrolamiento Canvas↔GitHub que adopta el equipo (mecanismo primario y de respaldo), y qué parte de ella entra en la entrega parcial y qué parte en la final?

Los estudiantes no son usuarios de la aplicación, de modo que el mapeo debe obtenerse por canales externos: tarea de Canvas de texto donde el estudiante escribe su usuario (¿creada por la app o elegida entre las existentes?); tarea de Canvas más verificación por OAuth de GitHub mediante enlace; solo enlace OAuth enviado por Conversation; quiz o encuesta de Canvas; CSV cargado por el profesor; edición manual por el equipo docente; o una combinación con primaria y fallback declarados. Si la app crea o modifica objetos en el Canvas del profesor, ¿se le avisa y se le pide autorización antes de escribir en su curso?

- **Requisitos:** R2.2.4, R2.2.5, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es el proceso explícitamente evaluado por usabilidad; condiciona el flujo completo de la demo parcial, los permisos de la GitHub App, los mensajes a estudiantes, la máquina de estados del mapeo y si la app escribe tareas en el Canvas del profesor (efecto visible para los revisores).
- **Opciones:**
  - A: tarea de Canvas de texto
  - B: tarea de Canvas + verificación OAuth de GitHub
  - C: solo enlace OAuth enviado por Conversation
  - D: quiz o encuesta de Canvas
  - E: CSV + edición manual del equipo docente
  - Combinación con primaria y fallback definidos (p. ej. tarea Canvas + carga manual en la parcial; + CSV y OAuth en la final)
- **Estudio de APIs:** §6.1 recomienda la tarea de Canvas (online_text_entry) + validación con GET /users/{username}; §6.2 propone OAuth de GitHub como complemento opcional; §6.3 propone carga manual + CSV + recordatorios como escape hatch.
- **Fusiona:** P155, P106

### Q-2.2-02 — ¿El equipo acepta el riesgo de que un estudiante registre una cuenta de GitHub que no le pertenece, o exige prueba de propiedad de la cuenta?

Si exige verificación, ¿cuál mecanismo: OAuth de GitHub mediante enlace, la aceptación de la invitación de colaborador como confirmación implícita, o la coincidencia del email público de GitHub con el de Canvas? ¿Se distinguen en la app los estados VALIDADO (el login existe) y VERIFICADO (se probó la propiedad)?

- **Requisitos:** R2.2.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Cambia la estrategia de enrolamiento, los permisos y el callback de la GitHub App, y los estados del mapeo.
- **Opciones:**
  - Aceptar el riesgo (sin prueba de propiedad)
  - OAuth de GitHub
  - Aceptación de la invitación de colaborador como verificación
  - Coincidencia del email público de GitHub con el de Canvas
- **Estudio de APIs:** §6.1 declara como desventaja que el método de la tarea de Canvas "no prueba que el estudiante sea dueño"; §6.2 propone magic link + OAuth como verificación opcional.
- **Fusiona:** P163

### Q-2.2-03 — Si se adopta la verificación por OAuth de GitHub vía magic link (§6.2), ¿cómo se define el enlace, el token y la precedencia frente a lo que el estudiante escribió en Canvas?

Concretamente: (a) si el login verificado por OAuth difiere del entregado en la tarea de Canvas, ¿gana el verificado, se marca conflicto para decisión docente, o se pide confirmación?; (b) ¿el magic link es un JWT sin estado (no revocable, reutilizable hasta expirar) o un token de un solo uso almacenado (revocable, con used_at y reemisión), cuánto dura, y qué ocurre si un estudiante lo reenvía a un compañero que autoriza con SU cuenta de GitHub y queda mapeado al canvas_user_id equivocado?; (c) ¿qué página ve el estudiante tras autorizar (éxito, error, "este enlace ya fue usado") y en qué idioma?; (d) ¿qué scopes se solicitan (ninguno vs read:user) y se descarta el access_token del estudiante inmediatamente tras leer GET /user o se persiste (para qué uso y con qué cifrado)?; (e) ¿el estudiante que solo hizo OAuth y nunca entregó la tarea de Canvas cuenta como mapeado?

- **Requisitos:** R2.2.4, R2.2.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** si
- **Por que importa:** Fija reglas de precedencia entre fuentes de mapeo, la seguridad del enlace, las pantallas mínimas de cara al estudiante, la tabla de mapeos (fuente, verificado_en, github_id) y la política de datos personales de estudiantes.
- **Opciones:**
  - OAuth prevalece siempre
  - Conflicto marcado para decisión docente
  - OAuth solo como confirmación del texto entregado
  - JWT sin estado
  - Token de un solo uso almacenado
  - Descartar el token tras leer el login (guardar solo login/id)
  - Persistir el token cifrado
- **Estudio de APIs:** §6.2 describe un JWT con canvas_user_id y 7 días de vigencia y GET /user con el token del estudiante; no aborda conflictos con el texto entregado, el reuso del enlace, la página posterior, los scopes ni qué se guarda.
- **Fusiona:** P100, P207

### Q-2.2-04 — ¿Tener cuenta de GitHub es obligatorio para el curso, y qué se hace con el estudiante que no puede o no quiere crearla (objeción de privacidad, restricciones de GitHub por país o edad, cuenta suspendida)?

¿Se acuerda con el profesor una política del curso (exento con entrega alternativa fuera de la app; cuenta creada por el docente; plazo máximo antes de considerarlo sin entrega) y la app solo ofrece el estado "exento" con motivo registrado? ¿Qué se comunica al estudiante en la tarea de registro sobre esa política?

- **Requisitos:** R2.2.4, R2.2.6
- **Tipo:** dependencia_externa · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Fija una regla de negocio del curso que la app debe reflejar en estados y mensajes, y determina si un estudiante sin cuenta queda para siempre como faltante.
- **Opciones:**
  - Obligatoria sin excepciones
  - Estado "exento" con motivo y entrega alternativa fuera de la app
  - Cuenta creada por el equipo docente
  - Plazo máximo tras el cual se considera sin entrega
- **Estudio de APIs:** §6.1 señala como desventaja que no se prueba la propiedad de la cuenta; no aborda estudiantes sin cuenta ni una política de obligatoriedad.
- **Fusiona:** P102

### Q-2.2-05 — ¿El mapeo estudiante↔GitHub es por curso o global por identidad de Canvas (canvas_base_url + canvas_user_id)?

Si un estudiante ya está mapeado en otro curso de la aplicación, ¿se reutiliza automáticamente, se propone para confirmación docente, o se pide de nuevo? ¿Cuál es la clave única de la tabla de mapeo?

- **Requisitos:** R2.2.4
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define la tabla de mapeo y su clave única, y determina si existe un atajo de usabilidad para cursos siguientes.
- **Opciones:**
  - Por curso
  - Global por identidad Canvas
  - Global con confirmación del docente
- **Estudio de APIs:** §5.2 no incluye la tabla de mapeo en el modelo; §11 la menciona como "tabla de mapeo" sin definir su alcance.
- **Fusiona:** P169

### Q-2.2-06 — ¿Qué criterios de aceptación medibles se fijan para la usabilidad del enrolamiento desde el lado del estudiante, y se hará una prueba con un estudiante real antes del 16-sep?

Candidatos a fijar: número máximo de acciones del estudiante hasta tener acceso al repositorio (leer tarea → escribir usuario → entregar → aceptar invitación); tiempo máximo entre entrega válida y mensaje de confirmación, y entre confirmación y repositorio accesible; máximo de iteraciones del ciclo error→corrección; exigencia de que cada mensaje de error diga exactamente qué hacer; que todo funcione desde la app móvil de Canvas. ¿Se realizará una prueba con al menos un estudiante real ajeno al equipo siguiendo solo las instrucciones de Canvas, y quién la registra?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Convierte "se evaluará la usabilidad del proceso" en requisitos verificables y en un plan de prueba con usuario real.
- **Opciones:**
  - Fijar umbrales numéricos explícitos (acciones, tiempos, iteraciones) como criterios de aceptación
  - Solo criterios cualitativos (mensajes accionables, sin métricas)
  - Prueba con estudiante real externa al equipo, registrada
  - Sin prueba con usuario real antes de la parcial
- **Estudio de APIs:** §6.1 afirma que el "loop de feedback automático es la parte usable del requisito" y §13 propone un guion de demo; no fija criterios medibles para el estudiante.
- **Fusiona:** P101

### Q-2.2-07 — ¿Dispone el equipo del entorno de pruebas necesario: una instancia Canvas con cuentas de estudiante reales y cuentas de GitHub de prueba suficientes?

En concreto: una instancia Canvas (institucional o Free-for-Teacher) donde puedan crear al menos 10 cuentas de estudiante con login real, inscribirlas en dos o más secciones, crear group sets y hacer entregas en la tarea de registro actuando como esos estudiantes; y al menos 10 cuentas de GitHub de prueba correspondientes para recibir y aceptar invitaciones. Si no se dispone, ¿qué se recorta del alcance demostrable?

- **Requisitos:** R2.2.1, R2.2.3, R2.2.4
- **Tipo:** dependencia_externa · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Sin ese entorno no se puede demostrar el enrolamiento ni los estados "invitación pendiente" e "inválido" en la demo parcial, ni probar los casos borde de grupos.
- **Opciones:**
  - Instancia institucional con cuentas reales
  - Instancia Free-for-Teacher creada por el equipo
  - Cuentas simuladas / datos sembrados sin entregas reales
- **Estudio de APIs:** §1.2 plantea el Plan B Free-for-Teacher; §13 hito 1 pide un Canvas de pruebas con 2 secciones, ~10 estudiantes y 1 group set, y dejar visible un caso con problema.
- **Fusiona:** P176

## Tarea de Canvas de registro y recoleccion del mapeo

### Q-2.2-08 — Si se usa una tarea de Canvas como formulario de registro del usuario de GitHub, ¿quién la crea, cuántas hay y cómo se define su contenido?

Aspectos a decidir: ¿la crea automáticamente la app (¿al vincular el curso o al crear la primera tarea de programación?), la crea el profesor con un botón, o el profesor vincula una tarea existente? ¿Una por curso o una por tarea de programación? ¿Nombre, descripción, puntos (0), omit_from_final_grade, visibilidad por sección, due_at/lock_at (¿se aceptan entregas tardías?) y submission_type (texto vs URL)? ¿La descripción es una plantilla fija o editable con vista previa y variables ({curso}, {fecha límite}, {ejemplo}), quién puede editar esos textos, e incluye instrucciones para crear una cuenta de GitHub y el aviso de que recibirá una invitación por correo? ¿Se muestra al profesor el enlace a esa tarea en Canvas y un contador "N de M estudiantes ya respondieron"?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Concreta el paso del wizard, el objeto que la app escribe en Canvas y su impacto en el libro de notas del estudiante; el texto que leen los estudiantes es parte del producto cuya usabilidad se evalúa.
- **Opciones:**
  - Creación automática al vincular el curso, con plantilla fija
  - Creación al crear la primera tarea de programación
  - Creación asistida con plantilla editable y vista previa
  - El profesor vincula una tarea existente
  - Una por curso
  - Una por tarea de programación
- **Estudio de APIs:** §6.1 muestra POST /assignments con submission_types=online_text_entry, points_possible=0, published=true y una descripción de ejemplo ("Escribe SOLO tu nombre de usuario de GitHub (ej: jperez)…"), y dice que "la fecha de entrega sirve de plazo natural"; no decide una por curso vs por tarea, ni editabilidad ni vista previa.
- **Fusiona:** P156, P198

### Q-2.2-09 — Para la tarea de Canvas de registro, ¿qué se fija respecto de los efectos colaterales que ven el estudiante y el profesor en Canvas?

Puntos abiertos: (a) grading_type (not_graded evita que aparezca en la libreta y en la lista "por calificar" del profesor pero impide marcar "complete"; pass_fail muestra ✓/✗ al estudiante); (b) allowed_attempts (-1 ilimitado para permitir corregir un usuario inválido, o limitado a N); (c) si aparece en el calendario y en la lista de pendientes del estudiante y con qué etiqueta cuando la entrega es tardía o falta ("missing"/"late" en su libreta); (d) si la tarea queda en su propio assignment group para no distorsionar promedios ponderados; (e) si el profesor recibirá N ítems "necesita calificación" en su To-Do de Canvas por cada registro y quién los limpia; (f) si al vincular una tarea de registro ya existente se valida que sea individual (group_category_id nulo) y de tipo texto.

- **Requisitos:** R2.2.4, R2.2.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define la configuración exacta del POST/PUT de la tarea de registro y el comportamiento observable por estudiantes y profesor; evita contaminar la libreta o el To-Do del profesor y que estudiantes queden marcados "missing" por una tarea administrativa.
- **Opciones:**
  - grading_type=not_graded, sin marcar "complete"
  - pass_fail con "complete" al validar
  - points con 0 puntos y omit_from_final_grade
  - allowed_attempts ilimitado
  - allowed_attempts limitado a N
  - Assignment group propio para la tarea de registro
- **Estudio de APIs:** §6.1 propone crear la tarea con submission_types=online_text_entry, points_possible=0 y published=true; no aborda grading_type, allowed_attempts, assignment group, ni el efecto en la lista de pendientes del profesor o en la libreta del estudiante.
- **Fusiona:** P099

### Q-2.2-10 — ¿Cuál es el ciclo de vida de la tarea de recolección y qué hace la app si el profesor la altera en Canvas?

Casos a resolver: ¿esa tarea debe excluirse del selector de entregas vinculables de R2.3.1? Si el profesor la elimina, la despublica o le cambia la fecha directamente en Canvas, ¿la app la recrea, alerta al profesor en el checklist del curso, o deja de recolectar mapeos en silencio? ¿Un estudiante incorporado después de su fecha de cierre puede seguir entregando (fecha nula / sin lock_at)? ¿Se crea una por curso o una por tarea?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** La tarea de recolección es un artefacto propio con ciclo de vida que la spec debe definir, proteger y monitorear; su desaparición silenciosa detendría el mapeo progresivo.
- **Opciones:**
  - Excluirla del selector de entregas vinculables
  - Recrearla automáticamente si desaparece
  - Alertar en el checklist del curso sin recrearla
  - Sin monitoreo (se detiene la recolección en silencio)
- **Estudio de APIs:** §6.1 propone crear la assignment "Registro de usuario GitHub" con points_possible=0; no aborda su ciclo de vida, su monitoreo ni su exclusión del selector.
- **Fusiona:** P123, P174

### Q-2.2-11 — Verificar contra la instancia real el formato del body de una submission online_text_entry y las capacidades del endpoint de submissions, para diseñar el parser y el polling.

Concretamente: ¿el body llega como HTML envuelto en `<p>`, con entidades y saltos de línea? ¿GET /assignments/:aid/submissions acepta un filtro incremental (submitted_since o equivalente) junto con include[]=user y paginación completa, o cada ciclo debe leer todas las submissions?

- **Requisitos:** R2.2.4
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Determina el algoritmo del parser y si el polling puede ser incremental o debe volcar todas las submissions en cada ciclo, con su costo frente al throttling.
- **Opciones:**
  - Polling incremental con filtro por fecha
  - Volcado completo en cada ciclo
- **Estudio de APIs:** §6.1 indica que el body "viene como HTML → limpiar tags" y propone GET /assignments/:aid/submissions?include[]=user sin filtro incremental.
- **Fusiona:** P185

### Q-2.2-12 — ¿Cómo se le comunica a cada estudiante que debe registrar su usuario de GitHub: anuncio en Canvas al crear la tarea de registro, Conversation individual, solo la descripción de la tarea, o una combinación?

¿El texto incluye instrucciones para crear una cuenta de GitHub si no la tiene? ¿Es una plantilla editable por el profesor? ¿Se envía automáticamente al crear la tarea o lo dispara el profesor?

- **Requisitos:** R2.2.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es la primera interacción del estudiante con el proceso y parte de la usabilidad evaluada; define plantillas y un evento de comunicación.
- **Opciones:**
  - Anuncio en Canvas al crear la tarea de registro
  - Conversation individual a todos
  - Solo la descripción de la tarea
  - Plantilla editable + envío manual por el profesor
  - Combinación de anuncio + Conversation
- **Estudio de APIs:** §6.1 pone las instrucciones en la descripción de la tarea; §9.2 documenta anuncios; §9.3 Conversations individuales; §9.4 el flag notify_missing_mapping.
- **Fusiona:** P167

### Q-2.2-13 — ¿Qué fuentes de texto considera la app para extraer el usuario de GitHub, y cuál prevalece cuando difieren?

Los estudiantes escribirán su usuario en lugares distintos al cuerpo de la entrega: en el cuadro de comentarios de la entrega, respondiendo la Conversation de recordatorio, en un mensaje directo al profesor, o adjuntando una captura. ¿La app lee submission_comments como respaldo, solo el body, o todo lo demás lo carga el docente a mano? Si el estudiante reenvía la tarea de registro con un usuario distinto antes de que exista su repositorio, ¿se toma siempre la última entrega (attempt más reciente)? Si el docente ya había corregido el mapeo manualmente, ¿qué tiene precedencia: la corrección manual, la nueva entrega del estudiante, o el CSV?

- **Requisitos:** R2.2.4, R2.2.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Define las fuentes del parser, sus scopes, el manejo de múltiples attempts y la regla de precedencia entre fuentes de mapeo (entrega, comentario, manual, CSV); reduce o aumenta la carga manual del docente.
- **Opciones:**
  - Solo el body de la entrega
  - Body + comentarios de la entrega
  - Cualquier canal, con carga manual del docente
  - Última entrega siempre gana
  - La corrección manual gana y bloquea reentregas
  - La corrección manual gana pero la reentrega genera alerta al docente
- **Estudio de APIs:** §6.1 solo extrae el login del body de la submission (include[]=user) y hace polling de submissions sin tratar múltiples intentos; no aborda comentarios ni otras fuentes ni la precedencia frente a la carga manual de §6.3.
- **Fusiona:** P103, P161

## Parseo, validacion y ciclo de vida del mapeo estudiante-GitHub

### Q-2.2-14 — ¿Qué reglas exactas de normalización y parseo se aplican al texto entregado por el estudiante, y qué normalización canónica se guarda?

Casos a cubrir: "Mi usuario es jperez"; "https://github.com/JPerez/" con path o query; "@jperez"; "JPEREZ" en mayúsculas; "jperez@gmail.com" (email en vez de login); dos o más logins en el mismo texto; texto vacío; entrega con adjunto en vez de texto; saltos de línea, espacios y caracteres unicode. Ante ambigüedad (dos candidatos válidos), ¿se rechaza y se pide corrección, o se toma el último/primero, y con qué mensaje? ¿Se conserva el texto original entregado para auditoría? Además, confirmar en la documentación de GitHub las reglas de nombres de usuario (máximo 39 caracteres, alfanumérico y guiones, sin guion inicial/final ni dobles) y que los logins son case-insensitive en GET /users/{username} y en PUT collaborators, para decidir si se almacena en minúsculas o el login canónico y si "JPerez" y "jperez" son el mismo mapeo a efectos de detección de duplicados.

- **Requisitos:** R2.2.4, R2.2.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define el parser del mapeo y su criterio de aceptación, los mensajes de error al estudiante y los casos de prueba; errores aquí producen repositorios asignados a la persona equivocada o conflictos falsos por mayúsculas.
- **Opciones:**
  - Regex anclada que toma el último token válido
  - Rechazar cuando hay más de un candidato
  - Almacenar en minúsculas
  - Almacenar el login canónico devuelto por GitHub
  - Conservar el texto original para auditoría
- **Estudio de APIs:** §6.1 propone una regex anclada al final del texto que tolera el prefijo github.com/ y @, limpia HTML, admite máximo 39 caracteres y usa el login canónico devuelto por GET /users/{username} (respeta mayúsculas); no cubre email, dos logins, adjuntos ni la conservación del original.
- **Fusiona:** P157, P122, P186

### Q-2.2-15 — Además de que el login exista en GitHub (200 y type=User), ¿qué validaciones y reglas de unicidad se exigen antes de aceptar un mapeo, y cómo se resuelven los conflictos?

Validaciones candidatas: que el login no esté ya asociado a otro estudiante del mismo curso (o de otro curso), que no sea la cuenta de un profesor o ayudante ni la del bot de la app, que no sea una Organization, que la cuenta no esté suspendida. Ante dos estudiantes mapeados al mismo login (uno se equivocó o copió al compañero), ¿se rechaza el segundo mapeo, quedan ambos bloqueados como "conflicto" hasta que el docente decida, o gana el más reciente? ¿Se bloquea la creación de ambos repositorios mientras dure el conflicto? ¿Se notifica automáticamente por Canvas a los estudiantes implicados y al docente, y con qué texto?

- **Requisitos:** R2.2.4, R2.2.5, R2.2.6, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Un login duplicado provoca que un estudiante reciba acceso al repositorio de otro; la spec debe fijar la restricción de unicidad, los sub-estados de "inválido" y el flujo de resolución, que es parte central de la demo parcial.
- **Opciones:**
  - Unicidad estricta por curso: el segundo mapeo se rechaza y se notifica
  - Ambos quedan en "conflicto" y sin repositorio hasta resolución manual
  - Último en registrar gana, con alerta al docente
  - Primero en registrar gana, el segundo queda inválido
  - Rechazar organizaciones, cuentas suspendidas y cuentas del equipo docente o del bot
- **Estudio de APIs:** §6.1 valida 200 y type == "User" (advirtiendo que una organización también devuelve 200) y propone un comentario automático de corrección; no aborda duplicados, cuentas del equipo docente ni cuentas suspendidas.
- **Fusiona:** P158, P118, P160

### Q-2.2-16 — Cuando el usuario entregado no existe (404) o es inválido, ¿qué feedback recibe el estudiante, por qué canal, con qué texto y cuántas veces?

Detalles a fijar: ¿comentario en la entrega, Conversation, ambos? ¿El comentario explica el problema concreto (por ejemplo: «"juan-perez-uandes" no existe en GitHub; escribe solo tu nombre de usuario, por ejemplo jperez») y cómo reintentar (volver a entregar en la misma tarea)? ¿Se marca la entrega en Canvas como "incomplete"? ¿Se limita el número de avisos automáticos? ¿Se distingue el caso "entregó una Organization" del "no existe"? ¿Qué pasa si la tarea de registro ya cerró y el estudiante no puede reentregar: se le da otro canal o el docente lo carga manualmente? ¿Cómo aparece el caso en la vista docente?

- **Requisitos:** R2.2.4, R2.2.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es el loop de feedback que hace usable el proceso de enrolamiento evaluado; fija plantillas de mensaje, un estado INVALIDO visible y la regla para la fecha de cierre de la tarea de registro.
- **Opciones:**
  - Comentario en la submission
  - Conversation individual
  - Ambos
  - Además marcar la entrega como incomplete
  - Con tope de avisos automáticos
  - Sin tope de avisos automáticos
- **Estudio de APIs:** §6.1 paso 4: "si no → comentario pidiendo corrección. Ese loop de feedback automático es la parte usable del requisito", y advierte el caso type=Organization; §9.4 el flag notify_missing_mapping; §5.6 la fila "Error: usuario inválido → Corregir". No define textos, tope de avisos ni cierre de la tarea.
- **Fusiona:** P159, P199

### Q-2.2-17 — Al validar exitosamente un usuario de GitHub, ¿qué recibe el estudiante y en qué momento?

Opciones sobre la mesa: comentario de confirmación en la entrega, Conversation, calificación "complete" en la tarea de registro, o nada hasta que exista el repositorio. ¿Cuál es el texto exacto y anticipa que deberá aceptar una invitación que llegará por correo?

- **Requisitos:** R2.2.4, R2.2.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Cierra el loop de feedback y evita que el estudiante reenvíe la tarea por incertidumbre.
- **Opciones:**
  - Comentario de confirmación en la entrega
  - Conversation individual
  - Calificación "complete" en la tarea de registro
  - Nada hasta que exista el repositorio
- **Estudio de APIs:** §6.1 propone "confirmar por comentario en la entrega"; §5.7 indica que el mensaje de repositorio incluye "revisa tu correo para aceptar la invitación".
- **Fusiona:** P175

### Q-2.2-18 — ¿Cuál es la latencia real entre la entrega del usuario en Canvas y su aparición en la API, y entre eso y la creación del repositorio, y qué promesa de tiempo se escribe al estudiante?

Medir con los intervalos de polling y de worker elegidos, y decidir qué frase puede ponerse en la descripción de la tarea y en el mensaje al estudiante ("tu repositorio estará disponible en menos de X minutos"), y qué indicador de progreso ve el docente.

- **Requisitos:** R2.2.5, R2.3.10
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** El texto que lee el estudiante y el indicador de progreso del docente dependen de un tiempo medido, no supuesto.
- **Opciones:**
  - Publicar una promesa de tiempo medida
  - No prometer tiempo, solo notificar cuando esté listo
- **Estudio de APIs:** §6.1 describe el polling de submissions; §5.5 fija un cron cada 2 minutos; no mide latencias.
- **Fusiona:** P202

### Q-2.2-19 — ¿Se persiste el id numérico de GitHub además del login canónico, y qué ocurre si el estudiante cambia su nombre de usuario en GitHub?

¿La app sigue al usuario por su id y actualiza el login mostrado, o el mapeo queda "roto" y se marca para corrección? ¿Se revalida periódicamente para detectar que un login fue reasignado a otra persona, y qué se muestra si el login guardado ya no coincide con el id? Si el nombre del repositorio incluía el login (R2.3.8), ¿se renombra el repositorio o el nombre es inmutable?

- **Requisitos:** R2.2.4, R2.3.8, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Determina la clave de identidad del mapeo (login vs id numérico), una validación de integridad que evita agregar como colaborador a un desconocido, y la inmutabilidad del nombre del repositorio.
- **Opciones:**
  - Guardar solo el login canónico
  - Guardar login + id numérico y seguir renombres
  - Revalidar periódicamente login↔id
  - Nombre de repositorio inmutable
  - Renombrar el repositorio al cambiar el login
- **Estudio de APIs:** §6.1 guarda el login canónico devuelto por GET /users/{username}; no menciona guardar el id numérico ni el rename de cuentas.
- **Fusiona:** P120, P173

### Q-2.2-20 — Para la corrección manual del mapeo por el equipo docente, ¿cómo se comporta la edición: quién puede editar, cómo valida y qué queda registrado?

Aspectos abiertos: ¿qué roles pueden editar? ¿La edición valida contra GitHub en vivo al escribir (con debounce), mostrando avatar, nombre y enlace al perfil para que el docente confirme la identidad antes de guardar? ¿Qué se muestra si el login existe pero es una Organization, si ya está mapeado a otro estudiante del mismo curso, si el docente lo escribe con URL o @ (normalización visible), o si GitHub no responde (¿guardar sin validar o bloquear el guardado?)? ¿Se registra quién, cuándo y el valor anterior (auditoría)? ¿Se avisa al estudiante del cambio? ¿Puede el docente marcar a un estudiante como "exento / sin repositorio" para sacarlo de la lista de faltantes?

- **Requisitos:** R2.2.4, R2.2.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es el escape hatch del enrolamiento evaluado; define permisos (R2.1.8), el componente de edición inline y sus estados de validación, el log de auditoría, la regla de unicidad login↔estudiante por curso y el estado "exento".
- **Opciones:**
  - Validación en vivo obligatoria antes de guardar
  - Permitir guardar sin validar cuando GitHub no responde
  - Con auditoría de quién/cuándo/valor anterior
  - Con aviso automático al estudiante del cambio
  - Con estado "exento" disponible para el docente
- **Estudio de APIs:** §6.3 propone una "tabla editable con búsqueda incremental" que "valida contra GitHub en vivo"; §6.1 normaliza el login y valida GET /users/{username} con type == "User"; §3.4 la propuesta de permisos no incluye editar mapeos ni exentos.
- **Fusiona:** P164, P197

### Q-2.2-21 — ¿Qué import y export de datos por CSV se implementa, con qué formato, validación y semántica de sobrescritura?

Import de mapeos: ¿qué columnas de identificación (canvas_user_id, sis_user_id, email, nombre) más github_login, qué separador y codificación, hay plantilla descargable, validación por fila con reporte de errores (usuario inexistente, estudiante no encontrado, duplicado), vista previa antes de aplicar, y qué política ante conflictos con mapeos existentes (sobrescribir / ignorar / preguntar)? Export: ¿qué se puede exportar (lista de faltantes, tabla estudiante–usuario GitHub–repositorio–estado, asignación de correctores, estado de corrección, informe diario), con qué columnas y quién puede exportar? ¿El import forma parte de la entrega parcial como vía rápida de enrolamiento?

- **Requisitos:** R2.2.5, R2.2.6, R2.7.1, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Es una de las alternativas de R2.2.5; define formato, validación por fila, semántica de sobrescritura y si existen pantallas de import/export en el alcance.
- **Opciones:**
  - No implementar CSV
  - CSV por canvas_user_id
  - CSV por sis_user_id o email
  - Con vista previa y reporte por fila
  - Sobrescribir mapeos existentes / ignorarlos / preguntar
  - Export de faltantes y mapeos con columnas definidas
- **Estudio de APIs:** §6.3 propone un import CSV (canvas_user_id, github_login) "para casos masivos"; no define validación, vista previa, política de conflicto ni export.
- **Fusiona:** P165, P196, P179

### Q-2.2-22 — ¿Se puede eliminar o desvincular un mapeo existente, y qué ocurre entonces con el repositorio y el colaborador ya creados?

¿Se quita el colaborador o se mantiene? ¿El estudiante vuelve a la lista de faltantes y a recibir recordatorios? ¿Quién puede hacerlo?

- **Requisitos:** R2.2.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cierra el ciclo de vida del mapeo y define las transiciones inversas en la máquina de estados.
- **Opciones:**
  - No permitir eliminar mapeos
  - Eliminar y quitar el colaborador del repositorio
  - Eliminar manteniendo el acceso ya concedido
  - Eliminar y devolver al estudiante a "faltante" con recordatorios
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P166

### Q-2.2-23 — Si el mapeo cambia cuando el repositorio ya existe (el estudiante entrega otro usuario, perdió acceso a su cuenta, o el docente corrige un mapeo erróneo), ¿qué hace la app en GitHub y qué se le muestra al docente antes de confirmar?

Aspectos a decidir: ¿quién lo autoriza (solo docente, o también el estudiante reentregando)? ¿Se quita al colaborador anterior y se agrega al nuevo en el mismo repositorio, se crea un repositorio nuevo marcando el anterior, o solo se actualiza el mapeo sin tocar GitHub? ¿Se revocan las invitaciones pendientes? ¿Se renombra el repositorio si su nombre incluía el login? ¿Cómo se atribuyen los commits ya hechos con el login anterior (se reatribuyen al estudiante o quedan sin atribuir)? ¿Se muestra el impacto antes de confirmar (por ejemplo "este repositorio tiene 12 commits de jperez-old")? ¿Ocurre automáticamente en el siguiente ciclo del worker o requiere confirmación explícita?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.8, R2.3.9, R2.5.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Es un caso borde casi seguro en un semestre real; define transiciones adicionales de la máquina de estados del repositorio, la precedencia entre fuentes de mapeo, los efectos secundarios en GitHub, la re-atribución de commits y si la plantilla de nombre puede depender del login (R2.3.8).
- **Opciones:**
  - Bloquear cambios tras crear el repositorio salvo intervención docente
  - Permitir y reconciliar colaboradores automáticamente
  - Requerir confirmación explícita del docente con vista de impacto
  - Crear un repositorio nuevo y marcar el anterior
  - Mantener ambas cuentas con acceso
  - Nunca renombrar el repositorio (usar un id estable en el nombre)
- **Estudio de APIs:** §5.4 propone un nombre individual con {githublogin} y documenta los endpoints de colaboradores e invitaciones, incluido DELETE collaborators; §6.1 y §6.3 describen recolección automática, carga manual y CSV pero no definen precedencia ni cambios posteriores a la creación del repositorio.
- **Fusiona:** P119, P162, P194

### Q-2.2-24 — ¿Cuál es la máquina de estados del mapeo estudiante↔GitHub y cuáles de esos estados cuentan como "falta información" para R2.2.6?

Propuesta a confirmar o reemplazar: SIN_REGISTRO → PENDIENTE_VALIDACION → INVALIDO (no existe / es organización / duplicado) | VALIDADO (existe) → VERIFICADO (OAuth o invitación aceptada); más EXENTO y RETIRADO. ¿Qué texto y color se muestra por estado? ¿Cuáles se consideran faltantes y cuáles no?

- **Requisitos:** R2.2.4, R2.2.5, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es la base de la vista de faltantes, del worker de aprovisionamiento y de los mensajes; sin ella no hay criterios de aceptación verificables.
- **Opciones:**
  - Adoptar la máquina propuesta tal cual
  - Adoptarla sin el estado VERIFICADO
  - Definir otro conjunto de estados
- **Estudio de APIs:** §5.2 define los estados de Repository (PENDING_MAPPING… ERROR) pero no los del mapeo; §5.6 usa iconos y textos ad hoc.
- **Fusiona:** P180

## Acceso a GitHub: organizacion, invitaciones y recordatorios

### Q-2.2-25 — ¿Los estudiantes se invitan como miembros de la organización de GitHub o solo como colaboradores externos de cada repositorio?

Miembros de la organización supone una invitación por semestre y acceso inmediato a los repositorios posteriores; colaboradores externos suponen una invitación por repositorio. ¿Qué plan tiene la organización (Free/Team) y existen límites de colaboradores o asientos que condicionen la decisión?

- **Requisitos:** R2.2.4, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Cambia el permiso Members:write de la GitHub App, la cantidad de estados "invitación pendiente" y qué se muestra como faltante; el plan de la organización es una dependencia externa.
- **Opciones:**
  - Miembros de la organización
  - Outside collaborators por repositorio
  - Miembros solo si el plan de la organización lo permite
- **Estudio de APIs:** §6.4 plantea como opcional invitar a la organización, con lo que PUT collaborators devuelve 204 en vez de 201; §14 advierte "si la org es Free, revisen el límite de colaboradores en repos privados".
- **Fusiona:** P170

### Q-2.2-26 — Cuando la invitación de colaborador no es aceptada (queda pendiente, se rechaza o expira), ¿qué hace la app y cómo se refleja en los estados?

Puntos a definir: ¿cuenta como "información faltante" para R2.2.6? ¿Se reenvía automáticamente (con qué frecuencia y hasta cuántas veces), solo hay reenvío manual desde la tabla, o se notifica al estudiante por Canvas? ¿Cómo se distinguen "pendiente", "expirada" y "rechazada" en R2.3.11? ¿El repositorio cuenta como "listo" en el dashboard y en el informe diario mientras la invitación esté pendiente? ¿Cómo se detecta la aceptación (polling de GET /repos/../invitations, webhook member/member_invite)? Además, verificar en la documentación de GitHub cuánto duran las invitaciones antes de expirar (campo `expired`) y qué ocurre al reinvitar a un usuario con invitación expirada o rechazada.

- **Requisitos:** R2.2.6, R2.3.9, R2.3.11, R2.6.2, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define los sub-estados de COLLABORATORS_PENDING, la política de reintento del outbox, el mecanismo de detección de aceptación y el criterio de "problema pendiente" del informe diario.
- **Opciones:**
  - Reenvío automático diario hasta N veces + aviso por Canvas
  - Solo reenvío manual desde la tabla de estado
  - Invitar a la organización (§6.4) para evitar invitaciones por repositorio
  - Detección por polling de /invitations
  - Detección por webhook member/member_invite
- **Estudio de APIs:** §5.4 indica que 201 = invitación pendiente y 204 = acceso directo, menciona GET /invitations con campo `expired` y el DELETE de invitación "útil para reenviar" sin dar plazos; §5.6 ofrece la acción manual "Reenviar"; §6.3 incluye las invitaciones sin aceptar en el panel de faltantes; §8.1 sugiere suscribirse a member/member_invite. La expiración a 7 días es investigable en la documentación de GitHub.
- **Fusiona:** P117, P171, P172

### Q-2.2-27 — Para los recordatorios a estudiantes sin mapeo (o con mapeo inválido o invitación sin aceptar), ¿qué frecuencia, horario, tope y canal se fijan?

Detalles: ¿frecuencia diaria o cada N días? ¿Hora y zona horaria (America/Santiago) del envío? ¿Tope máximo de recordatorios por estudiante? ¿Canal (comentario, Conversation, anuncio)? ¿Configuración por curso o por tarea? ¿Se detienen si no hay tarea activa? ¿El docente puede enviarlos manualmente desde la vista de faltantes? ¿Se registra y se muestra el último recordatorio enviado por estudiante?

- **Requisitos:** R2.2.5, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el job de recordatorios, sus flags (R2.6.7) y la columna "último recordatorio" de la vista de faltantes.
- **Opciones:**
  - Diarios con tope configurable
  - Cada N días
  - Solo envío manual del docente
  - Configuración por curso
  - Configuración por tarea
- **Estudio de APIs:** §6.3 propone un job diario a estudiantes sin mapeo; §9.4 el flag notify_missing_mapping por tarea; §9.3 envío secuencial con pausa; §14 recomienda manejar las zonas horarias en UTC.
- **Fusiona:** P168

## Roster: quien cuenta como estudiante

### Q-2.2-28 — ¿Qué estados de inscripción de Canvas cuentan como "estudiante inscrito" para listar, exigir usuario de GitHub, crear repositorio y notificar, y cómo se trata al estudiante inalcanzable?

Estados en juego: active, invited (aún no aceptó la invitación al curso), creation_pending (cuenta de Canvas no activada, sin login), inactive, completed, rejected. Para invited y creation_pending debe verificarse contra la instancia real: (a) si POST /conversations acepta ese user_id como recipient y si el mensaje se entrega, se encola o se pierde; (b) si PUT .../submissions/:user_id con comment[text_comment] funciona para ese usuario; (c) si aparece en GET /courses/:id/users y con qué datos. Y decidirse: ¿se le exige usuario de GitHub y se le crea repositorio?, ¿cuenta como "falta información" en R2.2.6 y en los denominadores del dashboard, o se muestra en una categoría propia ("aún no activo en Canvas") excluida de los recordatorios automáticos hasta que active su cuenta? ¿Cómo se muestra en la UI cada estado distinto de active para que el profesor entienda por qué no tiene repositorio?

- **Requisitos:** R2.2.1, R2.2.6, R2.3.7, R2.3.12, R2.6.5
- **Tipo:** decision_equipo + verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija el filtro del sync y evita crear repositorios fantasma o dejar fuera a estudiantes reales; además, invited y creation_pending son los únicos estados en que el estudiante existe en el roster pero es inalcanzable por los dos únicos canales que la app tiene hacia él, de modo que sin distinguirlos el equipo docente verá "recordatorio enviado" para alguien que nunca lo recibirá y el estudiante aparecerá indefinidamente como moroso en la lista que se muestra el 16-sep.
- **Opciones:**
  - Solo active
  - active + invited mostrados como "invitado, sin repositorio"
  - active + inactive marcados sin acciones
  - Incluir completed para cursos concluidos
  - Tratar invited/creation_pending como estudiantes activos (repositorio y recordatorios normales)
  - Excluirlos de recordatorios y de los denominadores, con estado propio visible
  - Excluirlos del todo hasta que su enrollment pase a active
- **Estudio de APIs:** §4.1 recomienda enrollment_state[]=active / state[]=active y type StudentEnrollment, y enumera los demás estados (invited, rejected, completed, inactive, creation_pending) sin decidir su tratamiento; §9.3 documenta POST /conversations, pero el estudio no cruza ambos: no dice si un usuario sin cuenta de Canvas activada puede recibir mensajes o comentarios.
- **Fusiona:** P116, P129, N022

### Q-2.2-29 — ¿Qué usuarios se excluyen del roster aunque aparezcan en los endpoints de Canvas: Test Student, observers, roles personalizados y usuarios con más de un rol en el curso?

Casos y verificaciones: (a) confirmar empíricamente en la instancia que usarán cómo aparece el Test Student (Student View) en GET /courses/:id/enrollments (¿type StudentViewEnrollment?) y en GET /courses/:id/users (enrollment_type student_view), para fijar el filtro exacto en ambos endpoints y excluirlo de listados, conteos, faltantes y creación de repositorios; (b) las instancias institucionales suelen tener roles personalizados basados en StudentEnrollment/TeacherEnrollment (por ejemplo "Alumno Oyente" o "Profesor Titular"), donde `type` conserva el tipo base y `role`/`role_id` el nombre personalizado: ¿la app filtra por `type` y no por `role`, y qué hace con roles personalizados que el profesor no quiera tratar como estudiantes (¿lista de exclusión por role_id configurable?); (c) si un mismo usuario tiene una StudentEnrollment y además otro rol en el curso (TA, Teacher, Observer; por ejemplo un ayudante inscrito como estudiante en otra sección), ¿se trata como estudiante (se le exige usuario de GitHub y se le crea repositorio), se excluye, o se marca para decisión docente?

- **Requisitos:** R2.2.1, R2.2.6, R2.1.4
- **Tipo:** decision_equipo + verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Sin el filtro correcto el worker intenta crear un repositorio para un estudiante fantasma y el panel de faltantes muestra un pendiente imposible de resolver; un filtro por nombre de rol dejaría fuera a todos los estudiantes con rol personalizado o incluiría oyentes y ayudantes que no deben tener repositorio.
- **Opciones:**
  - Filtrar por type base (StudentEnrollment)
  - Filtrar por type con lista de exclusión por role_id configurable
  - Excluir siempre Test Student y observers
  - Usuario con doble rol tratado como estudiante
  - Usuario con doble rol excluido
  - Usuario con doble rol marcado para decisión docente
- **Estudio de APIs:** §4.1 y §14 ordenan filtrar el Test Student (enrollment_type[]=student explícito, sin include[]=test_student) pero no documentan cómo aparece en /enrollments ni si type[]=StudentEnrollment basta; §4.1 muestra type, role y role_id en el objeto Enrollment sin discutir roles personalizados ni usuarios con múltiples roles.
- **Fusiona:** P130, P139, P190

### Q-2.2-30 — ¿Cómo trata la app los datos sucios de identidad de Canvas: fusión de cuentas, roles derivados y ids de cuentas cruzadas?

Casos: (a) si el administrador fusiona dos cuentas de un mismo estudiante (user merge), su canvas_user_id cambia y la app verá un estudiante "retirado" y otro "nuevo" sin mapeo: ¿se detecta la fusión (mismo sis_user_id/login_id) y se migran mapeo, repositorio y snapshots automáticamente, o se pide confirmación docente?; (b) roles personalizados derivados de StudentEnrollment (type=StudentEnrollment con role distinto, por ejemplo "Oyente"): ¿cuentan como estudiantes con repositorio?; (c) verificar si en la instancia institucional aparecen ids "shadow" de otras cuentas (formato "123~456") para estudiantes de intercambio y si funcionan como recipients de Conversations y en PUT submissions.

- **Requisitos:** R2.2.1, R2.2.4
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija la clave de identidad efectiva (canvas_user_id vs sis_user_id) y las reglas de migración de mapeos ante cambios de id, evitando repositorios duplicados.
- **Opciones:**
  - Clave canvas_user_id sin detección de fusiones
  - Detección por sis_user_id/login_id con migración automática
  - Detección con confirmación docente antes de migrar
- **Estudio de APIs:** §4.4 recomienda canvas_user_id como clave estable y §4.1 menciona enrollment_role_id; no aborda fusiones de usuarios, roles personalizados ni ids de cuentas cruzadas.
- **Fusiona:** P104

### Q-2.2-31 — ¿Qué datos del estudiante se almacenan y se muestran, cuáles se refrescan en cada sincronización y se conserva historial de cambios?

Campos candidatos: nombre, sortable_name, short_name, sis_user_id, login_id, email, avatar, canvas_user_id. ¿Cuáles se actualizan si cambian en Canvas? ¿Se conserva historial (nombre, sección, grupo, alta y baja con fecha y origen) o solo el valor vigente?

- **Requisitos:** R2.2.1, R2.2.2
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define el modelo Student, la política de datos personales de la app y las columnas posibles de cualquier tabla de estudiantes; el historial permite explicar por qué un repositorio tiene colaboradores distintos al grupo actual.
- **Opciones:**
  - Conjunto mínimo (canvas_user_id, nombre, sección)
  - Conjunto ampliado con sis_user_id, login_id y email
  - Solo valor vigente
  - Valor vigente + historial de cambios con fecha y origen
- **Estudio de APIs:** §4.4 fija canvas_user_id como clave estable y advierte que "el nombre y el email cambian"; §7.4 propone log de auditoría solo para cambios de fechas; el Apéndice A.3 advierte que el email puede no venir en /users.
- **Fusiona:** P134

### Q-2.2-32 — ¿La instancia de Canvas que usarán devuelve el email del estudiante al token del profesor, y por qué vía?

Verificar: include[]=email en /users, campo login_id/email en /enrollments, o solo mediante GET /users/:id/profile (primary_email). ¿Con qué permisos? El spec debe declarar la fuente exacta o declarar que no se dispone de email.

- **Requisitos:** R2.2.1, R2.2.4
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Si el email no está disponible quedan descartadas del spec la atribución de commits por email, la importación CSV por email y cualquier comunicación fuera de Canvas.
- **Opciones:**
  - Usar el email obtenido de /users
  - Usar GET /users/:id/profile
  - No depender del email en ningún flujo
- **Estudio de APIs:** Apéndice A.3: include[]=email no está en la lista documentada; propone como ruta segura GET /api/v1/users/:id/profile o no depender del email.
- **Fusiona:** P135

### Q-2.2-33 — ¿Se permite vincular y sincronizar un curso de Canvas sin estudiantes, no publicado o ya concluido (workflow_state completed)?

¿Qué muestra la pantalla de estudiantes en estado vacío, y el checklist de verificación lo marca como error bloqueante o como advertencia?

- **Requisitos:** R2.2.1, R2.2.2
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define el estado vacío de la vista de estudiantes y el comportamiento del checklist; en la demo un curso recién creado puede tener 0 estudiantes hasta que se inscriban.
- **Opciones:**
  - Bloquear la vinculación si n=0
  - Permitir con advertencia visible
  - Permitir sin advertencia
- **Estudio de APIs:** §3.3 propone el checklist "Vemos estudiantes → n > 0" (implicando que 0 sería fallo); §3.2 lista workflow_state y state[] pero no restringe.
- **Fusiona:** P137

## Sincronizacion con Canvas

### Q-2.2-34 — ¿Cómo y con qué frecuencia se sincroniza la información de estudiantes, secciones y grupos desde Canvas, y qué muestra la UI sobre la última sincronización?

¿Solo automática (cada N minutos), solo manual (botón), o ambas? ¿La misma cadencia para inscritos, grupos y entregas de la tarea de registro, o cadencias distintas (por ejemplo inscritos 10 min, submissions de registro 2 min, grupos según la tarea)? ¿Qué se muestra sobre la última sincronización (hora, resultado, cambios detectados)? ¿Cuántas veces puede pulsarse "sincronizar ahora" antes de bloquearse por throttling?

- **Requisitos:** R2.2.1, R2.2.2, R2.2.3
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija el job de sincronización, su cadencia, el criterio de aceptación de "datos frescos" (el guion de demo exige ver un cambio en vivo) y la existencia y límites del botón manual.
- **Opciones:**
  - Solo automática cada N minutos
  - Solo manual
  - Automática + botón manual con límite de uso
  - Cadencias distintas por tipo de dato
- **Estudio de APIs:** §4.4 propone sync_course con upsert por canvas_id y last_synced_at visible; §12 fija sync_canvas cada 10 minutos; §7.4 sugiere un botón "sincronizar ahora"; §1.5 exige concurrencia 1 por token con backoff ante 403/429.
- **Fusiona:** P128

### Q-2.2-35 — Tras vincular Canvas, ¿qué ve el profesor mientras corre la primera importación de estudiantes, secciones y grupos, y qué ocurre si falla a mitad?

¿Pantalla o panel de progreso con detalle ("Importando… 42 estudiantes, 2 secciones, 1 grupo encontrados") o spinner genérico? ¿Se bloquea la navegación mientras importa? ¿Se puede seguir usando la app en otra pestaña? Ante una importación parcial, ¿se muestra lo importado con aviso o se descarta todo?

- **Requisitos:** R2.2.1, R2.2.2, R2.2.3
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define el patrón de espera para procesos largos que se repetirá en aprovisionamiento y backfill, y las reglas de consistencia ante importaciones parciales.
- **Opciones:**
  - Panel de progreso detallado sin bloquear navegación
  - Pantalla bloqueante hasta terminar
  - Spinner genérico
  - Mostrar lo importado con aviso ante fallo parcial
  - Descartar todo ante fallo parcial
- **Estudio de APIs:** §4.4 da la estrategia de sync (paginado, upsert, no borrar); no habla de la UI de progreso ni de fallos parciales.
- **Fusiona:** P193

### Q-2.2-36 — Si la sincronización con Canvas falla parcialmente, ¿se aplica lo leído o se descarta el ciclo completo, y cómo se comunica que los datos podrían estar incompletos?

Escenarios: se leen estudiantes pero fallan los grupos; Canvas devuelve 403 por throttling a mitad de la paginación. ¿El ciclo es transaccional? ¿Cómo se evita marcar como "retirados" a estudiantes que simplemente no vinieron por un error? ¿Qué se muestra al profesor ("última sincronización exitosa hace X", "sync con errores")?

- **Requisitos:** R2.2.1, R2.2.3, R2.4.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Un sync parcial mal aplicado puede revocar accesos o disparar notificaciones erróneas; define la atomicidad del ciclo y la semántica de last_synced_at.
- **Opciones:**
  - Ciclo transaccional: todo o nada
  - Aplicar lo leído y marcar el ciclo como incompleto
  - Aplicar lo leído pero suspender las acciones destructivas
- **Estudio de APIs:** §4.4 registra last_synced_at y recomienda no borrar filas; §1.5 exige backoff ante 403/429. No define atomicidad del ciclo ni el sync parcial.
- **Fusiona:** P126

### Q-2.2-37 — Si la sincronización con Canvas falla por completo (token expirado o revocado, 403/429, curso inaccesible porque el profesor dejó de ser teacher, timeout), ¿qué ve el equipo docente y cómo se recupera?

¿Banner con la causa y la hora del último dato válido? ¿Se siguen usando los datos previos para el worker de repositorios? ¿Quién recibe la alerta? ¿Puede otro profesor del curso re-autorizar con su propio token sin perder datos?

- **Requisitos:** R2.2.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Fija los estados de error de la sincronización, el comportamiento degradado, el flujo de recuperación y un criterio de aceptación de "la app no presenta datos viejos como actuales".
- **Opciones:**
  - Banner con causa y hora del último dato válido, operación degradada
  - Detener workers hasta recuperar el token
  - Permitir re-autorización por otro profesor del curso
- **Estudio de APIs:** §1.5 exige manejar 403 y 429 con backoff; §1.1 refresh_token cifrado para jobs nocturnos; §3.4 opción A usa el token del profesor para todo; §7.4 "muestren última sincronización". No define la UX de fallo ni la recuperación.
- **Fusiona:** P136

### Q-2.2-38 — ¿Qué garantías de consistencia se exigen cuando la sincronización, el worker de aprovisionamiento y la edición docente ocurren a la vez?

Escenarios: el docente corrige el login de un estudiante mientras el worker está a mitad de crear su repositorio con el login anterior; el sync cambia la membresía de un grupo mientras se agregan colaboradores; un estudiante desaparece del roster mientras se crea su repositorio. ¿Lock por curso, lock por sujeto que bloquee la edición en la UI, re-evaluación de los datos actuales al terminar el job, marcar el repositorio para revisión, o convergencia eventual en el siguiente ciclo? ¿Qué anomalías transitorias se aceptan en la tabla de estados?

- **Requisitos:** R2.2.1, R2.2.3, R2.2.4, R2.3.9, R2.3.10, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Determina el diseño de locks y transacciones, el alcance del lock por sujeto y si el estado READY se valida contra los datos actuales al finalizar el job.
- **Opciones:**
  - Lock por curso
  - Lock por sujeto (bloquea la edición mientras corre el job)
  - Re-evaluar al terminar el job y reparar
  - Convergencia eventual en el siguiente ciclo
- **Estudio de APIs:** §5.5 pide que crear_repo sea idempotente "con lock por sujeto"; §1.5 sync secuencial por token. No cubre la edición concurrente desde la UI ni los cambios de sync durante el job.
- **Fusiona:** P121, P138

### Q-2.2-39 — ¿Cómo detecta la app que un estudiante fue retirado, con qué salvaguardas antes de ejecutar efectos externos, y qué queda registrado de cada corrida de sincronización?

La API de enrollments no tiene filtro incremental: cada sync es un volcado completo. ¿El retiro se infiere por AUSENCIA en el volcado (frágil ante páginas inconsistentes o errores parciales) o se consulta explícitamente state[]=deleted,inactive,completed? ¿Se exige ausencia en N ciclos consecutivos o un umbral de seguridad (por ejemplo no marcar retirados si desaparece más del 20 % del roster en un ciclo) antes de reaccionar con efectos externos como revocar colaboradores? ¿El estado se guarda por ENROLLMENT (canvas_enrollment_id, sección, estado, last_seen_at) y el estado del estudiante se deriva (activo si alguna enrollment activa), cubriendo al que deja una de sus dos secciones? ¿Cada corrida queda persistida como SyncRun (inicio, fin, resultado, conteos de altas/bajas/cambios, error) y con qué retención? Verificar además contra la instancia real: si GET /courses/:id/enrollments?state[]=deleted,inactive,completed devuelve con el token del profesor las enrollments retiradas (incluyendo el objeto user), en cuánto tiempo aparecen tras el retiro, si se distingue "concluded" por fin de término de "deleted" manual, y si la enrollment reactivada conserva el mismo canvas_enrollment_id.

- **Requisitos:** R2.2.1, R2.2.2, R2.3.9, R2.5.4
- **Tipo:** decision_equipo + verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define el algoritmo de diff del sync, la tabla de enrollments, cuándo es seguro disparar bajas en GitHub, si canvas_enrollment_id sirve como clave estable y qué datos alimentan el registro de cambios y el indicador de última sincronización.
- **Opciones:**
  - Inferencia por ausencia en el volcado
  - Consulta explícita de estados no activos
  - Ausencia en N ciclos consecutivos
  - Umbral porcentual de bajas por ciclo
  - Estado por enrollment con derivación por estudiante
  - Persistir SyncRun por corrida
- **Estudio de APIs:** §4.1 lista state[] con deleted/inactive/completed pero no confirma qué devuelve un token de profesor ni la latencia; §4.4 dice marcar como retirado "lo que ya no viene" (inferencia por ausencia). No aborda histéresis, nivel enrollment ni SyncRun.
- **Fusiona:** P203, P204

### Q-2.2-40 — Cuando un estudiante es movido de sección, la API suele devolver dos enrollments para el mismo user_id (la antigua deleted/inactive y la nueva active): ¿la app consolida por user_id antes de aplicar las reglas de retiro y de sección?

¿Se agrupan las enrollments por user_id tomando solo las activas, para no marcar al estudiante como retirado y activo a la vez ni duplicarlo en las tablas? Verificar con state[] amplio qué devuelve exactamente la instancia tras un cambio de sección.

- **Requisitos:** R2.2.1, R2.2.2
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Un modelo que persiste una fila por enrollment sin consolidar por usuario genera duplicados, secciones erróneas y falsos retiros.
- **Opciones:**
  - Consolidar por user_id tomando solo enrollments activas
  - Persistir una fila por enrollment y derivar el estado del estudiante
- **Estudio de APIs:** §4.1 y §4.4 proponen upsert por canvas_user_id y marcar retirados; no abordan múltiples enrollments históricos del mismo usuario.
- **Fusiona:** P192

### Q-2.2-41 — ¿Cuál es el límite real de per_page en la instancia de Canvas usada, y qué per_page y límite de páginas de seguridad se fijan en el spec?

Verificar para roster, enrollments, submissions y assignments con include[]=all_dates,overrides, y comprobar si las respuestas grandes (muchos overrides ADHOC) se truncan o degradan el rendimiento.

- **Requisitos:** R2.2.1, R2.2.2, R2.4.4
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Un per_page rechazado silenciosamente (que cae a 10) multiplica las requests y puede activar el throttling en cursos grandes.
- **Opciones:**
  - Fijar per_page=100 con límite de páginas por llamada
  - Fijar otro valor verificado empíricamente
- **Estudio de APIs:** Apéndice A.6: "límite real de per_page: 100 funciona de forma confiable; no asuman más".
- **Fusiona:** P191

### Q-2.2-42 — ¿Qué tamaño máximo de curso debe garantizar la spec (estudiantes, secciones, grupos) y qué criterios de rendimiento se fijan?

Sirve para dimensionar la sincronización, la paginación y el throttling, y para fijar criterios de la vista de faltantes (tiempo de carga, paginación en UI).

- **Requisitos:** R2.2.1, R2.2.3, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija criterios de aceptación no funcionales (duración del sync, latencia de la vista) y las decisiones de paginación.
- **Opciones:**
  - Dimensionar para ~60 estudiantes (curso demo)
  - Dimensionar para 200+ estudiantes
  - Sin límite declarado
- **Estudio de APIs:** §1.4 usa per_page=100; §2.1 muestra un ejemplo con 60 estudiantes; §12 fija cadencias de workers; no fija un tamaño objetivo.
- **Fusiona:** P187

### Q-2.2-43 — Verificar si include[]=group_ids en GET /courses/:id/enrollments devuelve los grupos de todas las group categories del curso y con qué latencia frente a /groups/:id/users.

Sirve para decidir si basta una llamada para sincronizar la membresía de grupos o se requieren llamadas por grupo.

- **Requisitos:** R2.2.3
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cambia el número de requests del sync de grupos y su cadencia frente al throttling de Canvas.
- **Opciones:**
  - Una sola llamada con include[]=group_ids
  - Llamadas por grupo o por categoría
- **Estudio de APIs:** §4.1 recomienda include[]=group_ids ("te da los grupos del estudiante en la misma llamada"); §4.4 además pagina groups por categoría.
- **Fusiona:** P184

## Secciones

### Q-2.2-44 — Cuando un estudiante tiene enrollments activos en dos o más secciones del mismo curso, ¿cuál es el modelo de datos, qué sección se muestra y qué fecha efectiva rige?

¿El modelo es N:M mostrando todas las secciones, se elige una "principal" (¿con qué regla: enrollment más antiguo, elección del profesor?), o se marca conflicto para que el profesor decida? ¿Cuál se usa en la descripción del repositorio, en los filtros por sección de todas las tablas y en el cálculo de la fecha efectiva (la más tardía, la de la sección principal, o bloqueo hasta que el profesor elija)? Debe verificarse contra la instancia real qué fecha aplica Canvas en ese caso.

- **Requisitos:** R2.2.2, R2.4.2, R2.4.3
- **Tipo:** decision_equipo + verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Cambia el modelo de datos (1:N vs N:M estudiante-sección), el algoritmo de fecha efectiva, la columna "Sección" de todas las tablas, la descripción del repositorio y el filtro de sección de todas las vistas.
- **Opciones:**
  - Modelo N:M mostrando todas las secciones y fecha más permisiva
  - Sección principal = primera enrollment activa, resto en tooltip, con alerta si hay más de una
  - El profesor elige la sección principal por estudiante
  - Bloquear la tarea para ese estudiante hasta que el profesor elija sección
- **Estudio de APIs:** §4.2 advierte que un estudiante puede estar en más de una sección y pide modelo N:M; §7.3 sugiere usar max() de las fechas de sección; §5.4 pone "Sección 2" en la descripción del repositorio; el Apéndice A.7 pide verificarlo con un caso real.
- **Fusiona:** P140, P113

### Q-2.2-45 — ¿Qué información de secciones se muestra y dónde?

Elementos candidatos: lista de secciones del curso con conteo de estudiantes, nombre vs sis_section_id, filtro por sección en las tablas de estudiantes, faltantes y repositorios, y secciones sin estudiantes. ¿Qué se muestra como "sección" para un grupo cuyos integrantes son de secciones distintas?

- **Requisitos:** R2.2.2
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** R2.2.2 pide "identificar" la sección; hay que decidir si eso implica una pantalla propia o solo una columna y un filtro, y qué se muestra en grupos mixtos.
- **Opciones:**
  - Pantalla propia de secciones con conteos
  - Solo columna y filtro en las tablas existentes
  - Mostrar "mixto" o la lista de secciones para grupos con integrantes de varias secciones
- **Estudio de APIs:** §4.2 documenta /sections con include[]=total_students; §5.6 incluye la columna "Sección" en la tabla de repositorios. No define una vista de secciones ni el caso de grupos mixtos.
- **Fusiona:** P141

### Q-2.2-46 — Si un estudiante cambia de sección (o su sección se elimina o se cross-lista) después de configurada la tarea, ¿qué recalcula, recaptura y comunica la app?

¿Se actualiza la sección mostrada y se recalcula su fecha efectiva, reprogramando el snapshot pendiente? Si el snapshot ya fue capturado con la fecha de la sección anterior, ¿se mantiene (R2.4.7), se recaptura o se marca "requiere revisión"? ¿Se comunica el cambio al equipo docente y se registra en un historial de roster consultable? Si el nombre o la descripción del repositorio incluye la sección, ¿se actualiza en GitHub?

- **Requisitos:** R2.2.2, R2.3.8, R2.4.2, R2.4.4, R2.4.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina si la fecha efectiva es un valor derivado en vivo o congelado al capturar, y si el sync debe emitir eventos de auditoría o alerta por cambio de sección.
- **Opciones:**
  - Recalcular siempre; los snapshots capturados quedan intactos y se alerta
  - Recalcular y recapturar si la nueva fecha es posterior
  - Congelar sección y fecha por entrega al momento de la primera captura
  - Actualizar la descripción del repositorio en GitHub / no tocar GitHub
- **Estudio de APIs:** §7.3 calcula la fecha efectiva por estudiante; §7.4 reprograma solo si la entrega "NO fue capturada aún"; §4.4 hace upsert. No resuelve el caso ya capturado ni el cambio de sección en sí.
- **Fusiona:** P112, P142

### Q-2.2-47 — ¿Cómo aparecen las secciones cross-listed desde otro curso (nonxlist_course_id) y los estudiantes cuya sección fue eliminada o fusionada, y la app debe soportarlo?

Verificar el comportamiento en GET /courses/:id/sections y en /enrollments, y decidir si el modelo admite secciones "externas" o si el spec lo declara fuera de alcance, y qué se muestra cuando la sección referenciada por una enrollment ya no existe.

- **Requisitos:** R2.2.2
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Decide si el modelo admite secciones externas y qué mostrar cuando la sección referenciada ya no existe.
- **Opciones:**
  - Soportar secciones cross-listed
  - Declararlo fuera de alcance y documentar la limitación
- **Estudio de APIs:** §4.2 lista nonxlist_course_id y los endpoints de crosslist pero no describe el efecto sobre el roster.
- **Fusiona:** P143

## Grupos de Canvas

### Q-2.2-48 — ¿Qué group sets (group categories) se sincronizan: todos los del curso o solo el referenciado por assignment.group_category_id de las tareas vinculadas, y hay confirmación del profesor?

Al crear una tarea grupal, ¿la app muestra al profesor el group set detectado y sus grupos para que lo confirme antes de crear repositorios, o lo usa sin preguntar?

- **Requisitos:** R2.2.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el alcance del sync de grupos, un paso de UI en el wizard de tarea y cómo se resuelve "qué grupos aplican a esta tarea".
- **Opciones:**
  - Sincronizar todos los group sets siempre
  - Solo los referenciados por tareas vinculadas
  - Todos, mostrando o pidiendo confirmación del set detectado al crear la tarea
- **Estudio de APIs:** §5.1 indica que group_category_id nulo implica individual y con valor implica grupal; §4.4 sincroniza todas las categorías; §4.3 documenta los endpoints de group_categories y groups.
- **Fusiona:** P144

### Q-2.2-49 — ¿Cómo trata la app las Differentiation Tags de Canvas (group categories con non_collaborative=true), tanto como "grupos" de R2.2.3 como en el cálculo de fecha efectiva?

Canvas expone como group categories también las etiquetas de diferenciación (`non_collaborative=true`, filtro `collaboration_state`), y sus overrides llegan con group_id apuntando a un grupo de una categoría non_collaborative, permitiendo fechas distintas para subconjuntos de estudiantes en tareas INDIVIDUALES. ¿Qué categorías cuentan como "grupos" para la app: solo las colaborativas, todas, o se muestran las no colaborativas con una etiqueta distinta y sin repositorio? ¿Qué hace la app si un assignment vinculado trae un group_category_id que apunta a una categoría no colaborativa (¿se clasifica como grupal según R2.3.3?), o si un estudiante pertenece simultáneamente a una etiqueta y a un grupo real de otra categoría? ¿El algoritmo de fecha efectiva considera esos overrides en tareas individuales (el algoritmo del estudio solo evalúa group_id cuando la tarea es grupal, por lo que los ignoraría) y cómo aparecen en la vista de fechas ("extensión por etiqueta X")? Verificar en la instancia real cómo vienen en overrides[] y en group_categories.

- **Requisitos:** R2.2.3, R2.2.6, R2.3.3, R2.4.3
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija el filtro del sync de grupos y la clasificación individual/grupal de R2.3.3, evita crear repositorios grupales para etiquetas administrativas, y evita fechas efectivas incorrectas para estudiantes con extensión por etiqueta (R2.4.3).
- **Opciones:**
  - Sincronizar solo categorías colaborativas
  - Sincronizar todas y marcar las no colaborativas como "etiqueta" sin repositorio
  - Bloquear la vinculación si el assignment apunta a una categoría no colaborativa
  - Tratar los overrides de grupos non_collaborative como extensiones individuales en cualquier tipo de tarea
  - Ignorarlos y documentar la limitación
- **Estudio de APIs:** §4.3 lista el parámetro `collaboration_state` y el campo `non_collaborative` de GroupCategory pero no decide cómo tratarlos; §4.4 sincroniza todas las categorías del curso sin filtro; §7.3 solo evalúa group_id si la tarea es grupal.
- **Fusiona:** P107, P188

### Q-2.2-50 — ¿Qué estados de GroupMembership (workflow_state accepted / invited / requested) cuentan como integrante del grupo para efectos de repositorio y de faltantes?

Verificar en la documentación de Groups / Group Memberships de Canvas y fijar la regla.

- **Requisitos:** R2.2.3
- **Tipo:** investigable_en_docs · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Un integrante "invited" que nunca acepta no debería bloquear la creación del repositorio grupal ni recibir acceso, o sí, según lo que se decida.
- **Opciones:**
  - Solo accepted cuenta como integrante
  - accepted + invited cuentan
  - Todos los estados cuentan
- **Estudio de APIs:** §4.3 lista GET /groups/:id/memberships y /users pero no discute los estados de membresía.
- **Fusiona:** P154

### Q-2.2-51 — ¿Qué se hace con un grupo vacío (0 integrantes) o unipersonal dentro del group set de una tarea grupal?

¿Se ignora, se muestra como "grupo sin integrantes, sin repositorio", o se crea el repositorio igual para que el profesor asigne después? ¿Cuenta como información faltante en R2.2.6?

- **Requisitos:** R2.2.3, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si los grupos vacíos cuentan como faltantes y si el worker debe saltarlos.
- **Opciones:**
  - Ignorar silenciosamente
  - Mostrar como pendiente sin crear repositorio
  - Crear el repositorio igual
- **Estudio de APIs:** no lo aborda (§4.3 solo lista members_count).
- **Fusiona:** P145

### Q-2.2-52 — En una tarea grupal, ¿qué se hace con un estudiante inscrito que no pertenece a ningún grupo del group set?

¿Solo se muestra como faltante (R2.2.6), se le notifica por Canvas que debe unirse a un grupo, se avisa al profesor, se le crea un repositorio individual (¿automáticamente o tras una fecha de corte configurable?), o se espera indefinidamente? Si Canvas lo asigna a un grupo después del cierre de una entrega, ¿se aplica la misma regla que para las altas tardías?

- **Requisitos:** R2.2.3, R2.2.6, R2.3.7, R2.3.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es el caso central de R2.2.6 para grupos: define un estado "sin grupo" distinto de "sin mapeo", una comunicación y posiblemente una regla de creación excepcional, y su tratamiento en el worker, la tabla de estado y el informe.
- **Opciones:**
  - Solo mostrar como faltante
  - Notificar al estudiante
  - Notificar al profesor
  - Crear repositorio individual automáticamente
  - Repositorio individual tras una fecha de corte configurable
- **Estudio de APIs:** §4.3 señala GET /group_categories/:id/users?unassigned=true como "exactamente" lo que se necesita para listarlos; §6.3 los incluye en el panel de faltantes. No propone acción.
- **Fusiona:** P125, P146

### Q-2.2-53 — Confirmar en la documentación de Canvas si un usuario puede pertenecer a dos grupos del mismo group set, y decidir qué hace la app si la API devuelve esa inconsistencia.

Opciones defensivas: tomar el primero, marcar conflicto y alertar al docente, o bloquear la creación del repositorio.

- **Requisitos:** R2.2.3
- **Tipo:** investigable_en_docs · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina si el modelo necesita una restricción única (estudiante, group_set) y un estado de conflicto visible.
- **Opciones:**
  - Tomar el primer grupo
  - Marcar conflicto y alertar al docente
  - Bloquear la creación del repositorio
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P147

### Q-2.2-54 — ¿El líder de grupo definido en Canvas (campo `leader` del Group, `auto_leader` de la categoría) tiene algún rol en la app?

Posibles roles: destinatario principal o único de las comunicaciones del grupo, primer integrante en tablas y timeline, permiso distinto (`maintain`) en el repositorio, o se ignora por completo. Si el líder cambia en Canvas o el grupo no tiene líder, ¿qué se muestra y qué se hace?

- **Requisitos:** R2.2.3, R2.3.9, R2.6.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si el sync debe leer y persistir el líder, si las plantillas de mensajes lo mencionan y si hay diferencia de permisos en GitHub entre integrantes.
- **Opciones:**
  - Ignorar el líder
  - Mostrarlo como dato informativo
  - Usarlo como destinatario principal de los mensajes grupales
  - Darle permiso `maintain` en el repositorio
- **Estudio de APIs:** §4.3 menciona `auto_leader` en GroupCategory pero no lo usa en ningún flujo.
- **Fusiona:** P108

### Q-2.2-55 — Si el group set permite self-signup y los grupos siguen formándose, ¿cuándo crea el worker el repositorio grupal?

¿En cuanto haya al menos un integrante mapeado, cuando el grupo esté completo (is_full / group_limit), cuando cierre el self-signup, o en una fecha de corte configurada por el profesor?

- **Requisitos:** R2.2.3, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina el momento de creación de los repositorios grupales y evita repositorios con integrantes parciales que luego cambian.
- **Opciones:**
  - Crear con ≥1 integrante mapeado y agregar el resto progresivamente
  - Esperar a todos los integrantes mapeados
  - Esperar una fecha de corte configurable
  - Esperar a que cierre el self-signup
- **Estudio de APIs:** §4.3 lista self_signup, group_limit e is_full; §5.5 crea cuando "se dispone de toda la información", sin definir qué es "toda" para grupos en formación.
- **Fusiona:** P153

### Q-2.2-56 — En una tarea grupal donde solo algunos integrantes tienen usuario de GitHub válido, ¿se crea el repositorio con los mapeados o se espera a que todos lo estén, y cómo se muestra el grupo?

¿Se crea el repositorio agregando a los mapeados y completando progresivamente, se espera a todos, o se crea a partir de un umbral configurable? Si un integrante nunca completa el mapeo, ¿hay un plazo tras el cual el repositorio se crea igual? ¿Cómo se muestra la fila del grupo en R2.2.6 y R2.3.11 (por ejemplo "Grupo 12 · 2/3 mapeados · falta el usuario de M. Soto") y cuenta como "problema" en el informe diario?

- **Requisitos:** R2.2.6, R2.3.7, R2.3.9, R2.3.10, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** "Toda la información requerida" (R2.3.10) es ambiguo para grupos; la decisión cambia el estado PENDING_MAPPING, el momento de la notificación al grupo y la fila de grupo en la vista de faltantes.
- **Opciones:**
  - Esperar a todos los integrantes
  - Crear con los mapeados y completar progresivamente
  - Crear con los mapeados solo después de un plazo configurable
  - Crear a partir de un umbral configurable de integrantes mapeados
- **Estudio de APIs:** §5.5 dice "¿tiene(n) github_login mapeado? no → PENDING_MAPPING", ambiguo sobre si basta uno o se requieren todos; §5.6 muestra "Grupo 12 · 2/3 mapeados · sin repo · Falta usuario de M. Soto", lo que sugiere esperar.
- **Fusiona:** P124, P182

### Q-2.2-57 — Si un grupo cambia de nombre en Canvas, ¿el repositorio de GitHub se renombra, se actualiza solo la descripción, o el nombre queda fijo al momento de la creación?

¿La plantilla de nombre incluye el slug del grupo o solo su id?

- **Requisitos:** R2.2.3, R2.3.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.3.8 exige nombres inequívocos y estables; decide si la plantilla de nombre puede depender de un dato mutable.
- **Opciones:**
  - Nombre fijo al crear
  - Renombrar el repositorio en GitHub
  - Actualizar solo la descripción
- **Estudio de APIs:** §5.4 propone {curso}-{periodo}-{tarea}-g{canvas_group_id}-{slug_grupo}, donde el id garantiza la unicidad; no aborda renombres.
- **Fusiona:** P151

## Vista de informacion faltante, permisos y exenciones

### Q-2.2-58 — ¿La vista de información faltante vive a nivel de curso, a nivel de tarea, o ambas, y cómo se enlaza con la tabla de estado de repositorios (R2.3.11)?

El mapeo es del estudiante e independiente de la tarea, mientras que grupos y repositorios son por tarea. ¿Dónde se ubica cada vista en la navegación y cómo se evita duplicar la misma tabla en dos lugares con estados distintos?

- **Requisitos:** R2.2.6, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define la arquitectura de información de la parte más visible de la demo y evita dos tablas incoherentes.
- **Opciones:**
  - Solo a nivel de curso
  - Solo a nivel de tarea
  - Ambas con datos compartidos
- **Estudio de APIs:** §5.6 propone una tabla por tarea; §6.3 habla de un "panel de faltantes" sin ubicar el nivel.
- **Fusiona:** P178

### Q-2.2-59 — ¿Qué columnas, estados, filtros, búsqueda, orden y paginación tiene la vista de faltantes y la tabla de estudiantes/grupos y repositorios con 60–200 filas?

Columnas candidatas: estudiante, sección, grupo, usuario de GitHub y su estado, invitación al repositorio, estado del repositorio, último recordatorio, fuente del mapeo (entrega/manual/CSV), acciones. Filtros candidatos como chips: sección, tarea, estado, "solo problemas", "sin usuario GitHub", "invitación pendiente", "listo", por grupo. ¿Búsqueda por nombre, usuario de GitHub o nombre de repositorio? ¿Ordenamiento por columna? ¿Paginación, scroll virtual o todo en una página? ¿Los filtros se conservan en la URL para compartir o volver? ¿Contadores resumen tipo "37/40 mapeados"? ¿Qué se muestra en cada celda vacía?

- **Requisitos:** R2.2.6, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es la materialización de R2.2.6 y R2.3.11 y la pantalla central de la demo parcial; el spec debe fijar columnas, filtros y comportamiento con datos abundantes.
- **Opciones:**
  - Tabla única paginada con filtros como chips y estado en la URL
  - Scroll virtual sin paginación
  - Todo en una página sin filtros persistentes
- **Estudio de APIs:** §5.6 propone una tabla por tarea (Estudiante/Grupo, Sección, GitHub user, Repo, Colaboradores, Estado, Acción) con filtro "solo problemas" y botón "reintentar todos los fallidos"; §6.3 describe el panel de faltantes como la unión de 4 conjuntos.
- **Fusiona:** P177, P195

### Q-2.2-60 — ¿Qué acciones individuales y masivas ofrece la vista de faltantes, con qué confirmaciones e historial?

Acciones candidatas: enviar recordatorio (a uno o a todos), editar mapeo, reintentar validación, reenviar invitación, marcar exento, abrir la entrega en Canvas, abrir el perfil de GitHub. ¿Se piden confirmaciones para las acciones masivas? ¿Se muestra un historial de lo enviado?

- **Requisitos:** R2.2.5, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define botones, permisos asociados y el historial de comunicaciones.
- **Opciones:**
  - Acciones individuales solamente
  - Acciones individuales + masivas con confirmación
  - Con historial de comunicaciones visible
  - Sin historial
- **Estudio de APIs:** §5.6 propone las acciones "Recordar", "Reenviar", "Corregir" y "reintentar todos los fallidos"; §9.4 propone un outbox con pantalla de historial.
- **Fusiona:** P181

### Q-2.2-61 — Para un estudiante sin usuario registrado, ¿la app usa señales de actividad de Canvas para distinguir "no ha visto las instrucciones" de "las vio y no actuó"?

Señales disponibles: last_login y last_activity_at del estudiante en el curso (en los endpoints de usuarios y enrollments), si abrió la tarea de registro, si aceptó la invitación al curso. ¿Se muestra esa señal en la vista de faltantes (por ejemplo "sin actividad en Canvas hace 12 días") para que el docente lo contacte por otro medio, o se declara fuera de alcance?

- **Requisitos:** R2.2.5, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Agrega o no columnas y llamadas al sync, y permite priorizar recordatorios y contacto humano.
- **Opciones:**
  - Mostrar la última actividad en Canvas
  - Solo el estado del mapeo
  - Fuera de alcance
- **Estudio de APIs:** §4.1 lista sort=last_login e include[]=enrollments para GET /courses/:id/users; no propone usar la actividad del estudiante como señal en la vista de faltantes.
- **Fusiona:** P105

### Q-2.2-62 — ¿Existe una exclusión de sujeto POR TAREA, además de la exención a nivel de curso ("no crear repositorio / no capturar / no corregir / no alertar" para un estudiante o grupo concreto)?

¿Con motivo, autor y fecha? ¿Cómo interactúa con el predicado de "información completa" del worker, con los denominadores de R2.7.7 y del dashboard, y con el informe diario? ¿Es reversible, y qué pasa con el repositorio si ya existía (archivar, mantener, ignorar)?

- **Requisitos:** R2.2.6, R2.3.10, R2.4.5, R2.6.2, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin este flag, un caso especial aparece para siempre como "problema pendiente" en R2.3.11, R2.6.2 y R2.7.7; con él hay que definir su alcance y sus efectos en cada worker.
- **Opciones:**
  - Exclusión por tarea con motivo
  - Solo exención a nivel de curso
  - Sin exclusiones (todo es pendiente)
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P208

### Q-2.2-63 — ¿Qué roles pueden ejecutar cada acción del área 2.2: forzar sincronización, editar y eliminar mapeos, importar CSV, enviar recordatorios, marcar exentos y ver la vista de faltantes?

¿Un ayudante básico tiene solo lectura? R2.1.8 exige al menos 3 permisos definidos por el equipo; las acciones de esta área deben quedar asignadas a roles concretos.

- **Requisitos:** R2.2.1, R2.2.5, R2.2.6, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Sin el mapeo acción↔rol, los permisos exigidos por R2.1.8 no cubren las acciones más sensibles de esta área (escribir en GitHub y enviar mensajes a estudiantes).
- **Opciones:**
  - Profesor con todo; ayudante solo lectura
  - Profesor y ayudante con edición de mapeos; solo el profesor envía comunicaciones
  - Permisos granulares por acción
- **Estudio de APIs:** §3.4 propone 7 permisos (course.manage, assignment.manage, repo.provision, …) sin incluir sincronizar ni editar mapeos.
- **Fusiona:** P183

## Casos borde y recuperacion: cambios posteriores, retiros y datos inconsistentes

### Q-2.2-64 — Cuando cambia la composición de un grupo después de creado su repositorio, ¿cómo se reconcilian los colaboradores, la atribución de commits y la corrección de cada entrega?

Casos: (a) integrante nuevo: ¿se agrega como colaborador automáticamente y se le notifica? (b) integrante que sale: ¿se le revoca el acceso de inmediato, al cierre de la entrega en curso, nunca, o solo con confirmación docente? ¿Sus commits siguen contando en el repositorio antiguo y cómo se atribuyen en el dashboard y en la corrección? (c) integrante que se mueve a otro grupo que ya tiene repositorio: ¿queda con acceso a dos repositorios? (d) si el cambio ocurre entre la entrega 1 y la 2, ¿cómo se refleja en la corrección de cada entrega? (e) ¿queda registrado el período en que perteneció a cada grupo? (f) ¿hay una fecha límite de cambios (por ejemplo, tras la primera entrega ya no se aplican)? (g) ¿qué muestra la UI (repositorio "con integrantes desactualizados") y qué acciones ofrece, y las aplica el worker automáticamente o requieren confirmación docente?

- **Requisitos:** R2.2.3, R2.3.3, R2.3.4, R2.3.9, R2.5.8, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el reconciliador de colaboradores (el worker propuesto solo crea), la atribución de commits por período, la relación entre grupo "al cierre" y grupo "actual" para corregir, y evita marcar "sin participación" por error.
- **Opciones:**
  - Reconciliar colaboradores en cada sync (agregar y revocar)
  - Solo agregar nuevos; nunca revocar automáticamente
  - Agregar automático y quitar manual con confirmación
  - Congelar la membresía al crear el repositorio y solo alertar de diferencias
  - Aplicar cambios solo hasta una fecha configurable
- **Estudio de APIs:** §4.4 hace upsert de grupos y marca los retirados; §5.4 agrega colaboradores al crear y documenta agregar/quitar colaboradores; §5.5 el worker solo procesa sujetos sin repositorio READY. No aborda los cambios de membresía posteriores ni la revocación.
- **Fusiona:** P114, P148, P149, P200

### Q-2.2-65 — Si en Canvas se elimina un grupo o el group set completo, el assignment pasa a apuntar a otro group_category_id, o la tarea cambia de individual a grupal (o al revés) después de creados los repositorios, ¿qué hace la app?

¿El repositorio queda "huérfano" y se archiva, se mantiene visible con etiqueta ("grupo eliminado"), se intenta re-asociar por integrantes coincidentes, o se bloquea la tarea hasta que el profesor decida? ¿Se crean repositorios nuevos para los grupos del nuevo set, dejando a un estudiante con dos repositorios y violando R2.3.4? ¿Se quitan los colaboradores del repositorio huérfano? ¿Sus ex-integrantes pasan a "sin grupo" en la vista de faltantes? ¿La app detecta el cambio en el sync y muestra un estado de "configuración inconsistente", y el worker se detiene o continúa?

- **Requisitos:** R2.2.3, R2.2.6, R2.3.3, R2.3.4, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es el escenario donde el invariante "un único conjunto de repositorios por tarea" puede romperse; la spec debe decir si el worker se detiene o continúa, y definir un estado terminal del repositorio.
- **Opciones:**
  - Bloquear el aprovisionamiento y marcar la tarea como "inconsistente" hasta intervención
  - Archivar los repositorios huérfanos y crear los nuevos
  - Re-asociar automáticamente si los integrantes coinciden en ≥ N %
  - Mantener el repositorio visible con etiqueta y alertar al profesor
- **Estudio de APIs:** §5.2 valida group_category_id solo al vincular una segunda entrega; §7.4 hace polling por updated_at pero solo recalcula fechas; §4.4 indica "marcar deleted_at, no borrar". No define el efecto sobre el repositorio ni sobre los integrantes.
- **Fusiona:** P115, P150, P152

### Q-2.2-66 — ¿Se conserva la membresía histórica de grupos y secciones por entrega, y qué membresía usa la publicación de notas en Canvas?

Para responder "¿quién integraba el grupo y en qué sección estaba al cierre de la entrega N?": ¿se modelan las membresías de grupo y de sección con validez temporal (valid_from/valid_to, sin sobrescribir), se copia la lista de integrantes y secciones en la fila DeliverySnapshot al capturar, o no se conserva y siempre se usa la membresía actual? ¿Qué fuente usan la publicación de notas (R2.7.6), la comparación de integrantes (R2.5.8), los períodos por entrega (R2.5.7) y el cálculo de la fecha efectiva al recapturar? Además: con grade_group_students_individually=false, calificar a un integrante propaga la nota al grupo ACTUAL en Canvas; si el grupo cambió entre el cierre y la corrección, ¿la app califica según la membresía congelada al momento del snapshot o según la actual, y cómo evita que Canvas propague la nota a la persona equivocada? Verificar empíricamente el comportamiento real de la propagación.

- **Requisitos:** R2.2.2, R2.2.3, R2.4.5, R2.4.7, R2.5.8, R2.7.6
- **Tipo:** decision_equipo + verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin historial temporal, un cambio de grupo posterior al cierre hace que la nota, la comparación y la evidencia se atribuyan a la persona equivocada; decide dos tablas y su clave, y si la app debe calificar por integrante.
- **Opciones:**
  - Tablas de membresía con valid_from/valid_to
  - Copia de integrantes y secciones en el snapshot
  - Solo membresía actual
  - Calificar por integrante para evitar propagaciones incorrectas
- **Estudio de APIs:** §4.4 hace upsert por canvas_id sin historial; §7.3 calcula fechas con la membresía actual; §10.4 dice "lean ese campo antes de calificar" y calificar por integrante si es true. No aborda la validez temporal ni el cambio de grupo entre el cierre y la corrección.
- **Fusiona:** P127, P205

### Q-2.2-67 — Cuando un estudiante se inscribe después de que la tarea ya tiene repositorios creados (incluso después de cerrada la entrega 1), ¿qué hace la app automáticamente y qué requiere intervención?

Puntos: ¿aparece en la siguiente sincronización y se le solicita su usuario de GitHub sin intervención docente, creándole el repositorio en cuanto lo entregue, o algún paso requiere aprobación del profesor? ¿Se avisa al equipo docente de la incorporación tardía y hay un mensaje de bienvenida específico? ¿Se le captura snapshot de la entrega 1 ya vencida (con estado "sin commits"), se lo excluye de esa entrega ("no aplica"), o queda pendiente de decisión manual? ¿Se le asigna corrector automáticamente si ya se repartieron las correcciones? ¿Se dispara la notificación de "repositorio disponible" aunque la tarea vaya avanzada?

- **Requisitos:** R2.2.1, R2.2.5, R2.2.6, R2.3.10, R2.4.5, R2.6.7, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** El worker de aprovisionamiento y el de snapshots deben saber si tratan las altas tardías igual que las normales; afecta el estado de corrección (denominadores), el informe diario y si el flujo es 100 % automático o tiene aprobación.
- **Opciones:**
  - Automático total sin aviso
  - Automático con notificación al docente
  - Requiere aprobación del profesor antes de crear el repositorio
  - Crear repositorio y capturar el snapshot vencido inmediatamente (estado "sin commits")
  - Crear repositorio y marcar las entregas vencidas como "no aplica" para ese estudiante
  - Crear repositorio y dejar las entregas vencidas en "requiere decisión del profesor"
- **Estudio de APIs:** §5.5 indica que el cron recorre los "sujetos sin Repository en estado READY" y encola si hay login (implica creación automática); §7.5 dice que el job de snapshot barre "todo lo vencido y no capturado" (implica captura inmediata); §6.3 recordatorio diario a quienes no tienen mapeo. No distingue el caso de alta tardía ni menciona aviso al docente.
- **Fusiona:** P111, P133

### Q-2.2-68 — Cuando un estudiante deja de aparecer como StudentEnrollment activo (se retira, queda inactive, deleted o completed) y ya tiene repositorio, ¿qué hace la app, cómo se muestra y qué ocurre si se reincorpora?

Aspectos: (a) su acceso como colaborador al repositorio individual o grupal (mantener, revocar, degradar a solo lectura, preguntar al docente); (b) el repositorio individual (mantener, archivar en GitHub, marcar "retirado"); (c) su presencia y forma de mostrarse en el dashboard, en "estudiantes sin participación", en el informe diario, en la lista de corrección y en la vista de faltantes (¿desaparece de las tablas, se muestra tachado con filtro "incluir retirados", o se mantiene con badge "retirado"?); (d) los snapshots ya capturados; (e) su membresía en el grupo. Y si vuelve a inscribirse en el mismo curso (reactivate o nueva enrollment): ¿se restaura su registro anterior (mapeo de GitHub, repositorio, historial) o se trata como estudiante nuevo, y qué pasa si vuelve con otro canvas_user_id (cuenta de Canvas distinta)?

- **Requisitos:** R2.2.1, R2.2.4, R2.2.6, R2.3.9, R2.4.7, R2.5.4, R2.6.2, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define la máquina de estados del repositorio y del estudiante, las reglas de reconciliación del sync, qué filas se muestran u ocultan en cada vista, si el worker ejecuta acciones destructivas en GitHub, la regla para no marcar "sin participación" a quien ya no está, y la clave de identidad en la transición retirado→activo (evitando repositorios duplicados).
- **Opciones:**
  - Mantener acceso y repositorio, ocultar de métricas y corrección, marcar "retirado"
  - Revocar acceso, archivar el repositorio, mantener el histórico visible con etiqueta
  - Quitar colaborador pero mantener el repositorio
  - No hacer nada automático: alertar al profesor y ofrecer acciones manuales
  - Configurable por el profesor a nivel de curso
  - Restaurar el registro anterior al reinscribirse / tratarlo como estudiante nuevo
- **Estudio de APIs:** §4.4 dice "nunca borren filas; marcar deleted_at" y fija canvas_user_id como clave estable; §14 dice "no borren su repo ni su historia; márquenlos"; §4.1 menciona PUT .../reactivate. No define qué pasa con el acceso al repositorio, la visibilidad en dashboard/informe/corrección ni la reactivación.
- **Fusiona:** P110, P131, P201, P132

### Q-2.2-69 — Cuando el término o la sección concluyen y Canvas pasa masivamente las inscripciones a `completed`/`inactive`, ¿qué significa `completed` para la app y qué guardarraíl evita ejecutar en cascada las acciones de retiro?

Si una sección tiene `end_at` con `restrict_enrollments_to_section_dates=true`, o termina el término, Canvas concluye automáticamente las inscripciones aunque la corrección siga en curso. ¿La app trata `completed` igual que una baja (quitar acceso al repositorio, sacar de correcciones y métricas) o como "inscrito concluido" que sigue siendo calificable y visible? ¿Se distinguen ambos casos en la UI y el checklist advierte con antelación las fechas de fin de sección o de término que caigan dentro del período de corrección (6–20 de octubre en el curso demo)? ¿Existe un guardarraíl que distinga un cambio masivo (por ejemplo, más del X % del roster en un ciclo, o el workflow_state del curso cambiado) de retiros individuales, para no revocar colaboradores de todos los repositorios, marcar a todos como "retirados", enviar mensajes o inundar el informe? En ese caso, ¿se pausa y se pide confirmación al profesor, se trata como conclusión del curso, o se aplica la regla individual sin excepción?

- **Requisitos:** R2.2.1, R2.3.9, R2.4.2, R2.6.2, R2.6.5, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Una regla de retiro correcta a nivel individual puede destruir el acceso de todo un curso al terminar el semestre o ante un cambio administrativo en Canvas, y revocar accesos u ocultar sujetos en bloque justo durante la corrección.
- **Opciones:**
  - `completed` = retirado
  - `completed` = concluido calificable, sin cambios en GitHub
  - Configurable por curso
  - Umbral de cambio masivo que pausa las acciones destructivas y alerta
  - Detectar la conclusión del curso o del término y congelar el estado sin revocar
  - Aplicar la regla individual siempre
- **Estudio de APIs:** §4.2 advierte que `restrict_enrollments_to_section_dates` "cambia qué fechas aplican"; §4.4 indica "marcar como retirado lo que ya no viene"; §14 dice que los retirados pasan a deleted/inactive. No cubre la conclusión automática por fecha ni los cambios masivos.
- **Fusiona:** P109, P189

### Q-2.2-70 — ¿Qué hace la app ante inconsistencias entre las distintas fuentes de Canvas (roster, grupos y submissions)?

Casos: (a) GET /groups/:id/users devuelve un integrante que no figura como StudentEnrollment activo (retirado, Test Student, TA agregado a un grupo); (b) una submission de la tarea de registro llega con un user_id que aún no existe en el roster sincronizado (alta reciente, sync desfasado). ¿Se crea una fila de estudiante "no inscrito" marcada como tal, se ignora el dato hasta el próximo sync de roster, se dispara un sync inmediato, o se alerta al docente? ¿Ese integrante cuenta para "grupo completamente mapeado" y recibe acceso al repositorio? ¿El universo de grupos de una tarea son todos los del group set o solo los que tienen al menos un integrante del roster activo?

- **Requisitos:** R2.2.1, R2.2.3, R2.2.4, R2.3.9
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define las claves foráneas entre roster, grupos y mapeos (¿NOT NULL?) y evita que el worker cree repositorios o invite a personas que no son estudiantes activos.
- **Opciones:**
  - Fila fantasma marcada como "no inscrito"
  - Ignorar hasta el próximo sync
  - Disparar un sync inmediato del roster
  - Alertar al docente
- **Estudio de APIs:** §4.3 y §6.1 asumen consistencia entre roster, grupos y submissions; no lo aborda.
- **Fusiona:** P206

## Ya respondidas por el enunciado

Ninguna de las 111 preguntas de entrada quedó marcada como YA_RESPONDIDA en la etapa de verificación: los 111 veredictos son ABIERTA o ABIERTA/BLOQUEA, por lo que todas figuran en el cuerpo del documento y esta sección queda vacía.
