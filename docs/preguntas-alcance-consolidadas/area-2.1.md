# Preguntas de alcance — Area 2.1

63 preguntas finales, fusionadas desde 98 de entrada, 32 bloqueantes para la parcial.

## Identidad, registro y administración de la plataforma

### Q-2.1-01 — ¿Quién crea las cuentas de profesor y existe un rol de "administrador de plataforma" distinto de "profesor"?

R2.1.1 ("Crear y administrar usuarios de tipo profesor") y R2.1.2 ("Permitir que usuarios se registren asociando su cuenta de correo basada en gmail.com") coexisten sin que el enunciado diga si son el mismo flujo o dos flujos distintos. ¿Toda persona que inicia sesión con su gmail queda creada automáticamente como profesor, o alguien "crea"/aprueba al profesor primero y el usuario después asocia su gmail? Si existe un administrador de plataforma: ¿qué puede hacer (listar, desactivar o eliminar profesores, ver todos los cursos, forzar desvinculaciones, intervenir cursos huérfanos) y cómo se crea el primero (seed del despliegue, variable de entorno con lista de correos, primer usuario registrado)?

- **Requisitos:** R2.1.1, R2.1.2
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define si hay pantallas de alta/aprobación/whitelist, el modelo de roles global vs por curso y si cualquier persona con gmail puede crear cursos en la instancia desplegada (que estará pública dos semanas tras la entrega final). También define el bootstrap del primer usuario privilegiado para la demo.
- **Opciones:**
  - Autoservicio: registrarse con Google = ser profesor; no existe rol admin
  - Administrador de plataforma pre-crea o aprueba cuentas (admin creado por seed / variable de entorno)
  - El primer usuario registrado se convierte en administrador
  - Whitelist de correos/dominios en configuración
  - Invitación por email desde un profesor existente
  - Código de invitación del curso ICC4201
- **Estudio de APIs:** §3.1 solo cubre el mecanismo de login (Google OIDC); §11 marca 2.1.1 como "App/BD ✅" sin decir quién crea a quién; §12 solo menciona RBAC profesor / ayudante jefe / ayudante a nivel de curso. No aborda el rol de administrador de plataforma.
- **Fusiona:** P045, P046

### Q-2.1-02 — ¿Cómo se implementa técnicamente "registrarse asociando su cuenta gmail.com" y qué datos de Google se guardan?

Opciones de implementación: (a) Google OAuth 2.0 / OpenID Connect ("Iniciar sesión con Google"); (b) formulario propio de email + contraseña validando el sufijo @gmail.com con verificación por correo; (c) magic link enviado al gmail; (d) alguna combinación (p. ej. OIDC como principal y contraseña como respaldo). ¿Qué datos del perfil de Google se almacenan (nombre, foto, email, `sub`) y qué scopes se solicitan (`openid`, `email`, `profile`)?

- **Requisitos:** R2.1.2
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define el stack de autenticación, las pantallas de registro/login, si existe recuperación de contraseña (solo en la opción b), la dependencia de Google Cloud y qué datos personales almacena la app.
- **Opciones:**
  - Google OAuth 2.0 / OIDC
  - Email + contraseña propia con validación de sufijo
  - Magic link al gmail
  - OIDC como principal y contraseña como respaldo
- **Estudio de APIs:** §0 y §3.1 recomiendan Google OAuth/OIDC exigiendo que el claim `email` termine en @gmail.com y `email_verified === true`.
- **Fusiona:** P049

### Q-2.1-03 — ¿Qué direcciones de correo se aceptan exactamente como "cuenta basada en gmail.com"?

¿Se aceptan solo direcciones @gmail.com estrictas, también @googlemail.com, y cuentas de Google Workspace con dominio institucional (p. ej. el correo universitario del profesor o de los ayudantes evaluadores)? ¿Se rechaza a un profesor que ingresa con Workspace institucional? ¿Las variantes del local-part de Gmail (puntos ignorados: `n.abuawad@gmail.com` ≡ `nabuawad@gmail.com`; sufijos `+etiqueta`; mayúsculas) se tratan como la misma cuenta o como cuentas distintas? ¿Existe una vía alternativa de alta por el administrador (R2.1.1) para quien no cumpla la regla, y qué mensaje ve al ser rechazado?

- **Requisitos:** R2.1.1, R2.1.2
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Fija la regla de validación de identidad y su mensaje de rechazo; una regla demasiado estricta puede impedir que los evaluadores entren el 16-sep, una demasiado laxa incumple literalmente R2.1.2.
- **Opciones:**
  - Solo @gmail.com estricto
  - @gmail.com y @googlemail.com
  - Cualquier cuenta Google (incluido Workspace institucional)
  - Lista de dominios permitidos configurable por entorno
  - Regla estricta con alta alternativa por administrador
- **Estudio de APIs:** §3.1 indica validar el sufijo @gmail.com y `email_verified=true`, y nota que para Workspace el claim `hd` daría el dominio mientras que para gmail puro `hd` no viene. No aborda alias ni normalización del local-part.
- **Fusiona:** P020, P050

### Q-2.1-04 — ¿Cuál es la clave de identidad del usuario y cómo se normalizan los alias de Gmail al registrar e invitar?

¿La identidad es el `sub` de Google (estable aunque cambie el correo) o el email? ¿Cómo se normalizan los alias (puntos, sufijos `+etiqueta`, mayúsculas) al registrar y al invitar co-profesores/ayudantes por correo, para evitar cuentas duplicadas o invitaciones que nunca se emparejan? ¿Qué ocurre si un profesor cambia su dirección de Google?

- **Requisitos:** R2.1.2, R2.1.7, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Determina la unicidad de usuarios en la BD, la lógica de emparejamiento de invitaciones pendientes y el comportamiento ante un cambio de dirección.
- **Opciones:**
  - Identidad = `sub` de Google; email solo informativo
  - Identidad = email normalizado
  - Ambos: `sub` como PK y email único normalizado
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P051

### Q-2.1-05 — ¿Qué ocurre cuando el intento de login no cumple la regla de correo o Google no devuelve un consentimiento válido?

¿Se rechaza con un mensaje que explica la regla, se crea una cuenta "pendiente" o se redirige a otra pantalla? ¿Qué se muestra si Google devuelve `email_verified=false`, o si el usuario cancela el consentimiento de Google a mitad del flujo? ¿Se ofrece "probar con otra cuenta"?

- **Requisitos:** R2.1.2
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es el criterio de aceptación de la pantalla de login y sus mensajes de error; es el primer paso de la demo y se evalúa facilidad de uso.
- **Opciones:**
  - Rechazo con mensaje explicativo y botón "probar con otra cuenta"
  - Cuenta creada en estado "pendiente" de aprobación
  - Redirección a una pantalla de solicitud de acceso
- **Estudio de APIs:** §3.1 exige `email_verified === true` pero no define la UI de rechazo.
- **Fusiona:** P052

### Q-2.1-06 — ¿Qué matriz de navegadores y qué comportamiento del selector de cuentas de Google se soporta y se probará explícitamente?

Los evaluadores probablemente usarán ventanas de incógnito y navegadores distintos para simular un "profesor nuevo", y suelen tener varias cuentas Google (institucional y gmail) en el mismo navegador. ¿El inicio de sesión fuerza el selector de cuentas (`prompt=select_account`) y, tras rechazar una cuenta no válida, ofrece cambiar de cuenta? ¿Qué navegadores y versiones se soportan y se probarán en incógnito (Chrome, Firefox, Safari, Edge) para los tres flujos OAuth (Google, Canvas, instalación de la GitHub App), dado que las políticas de cookies de terceros y el modo privado pueden romper el retorno del callback?

- **Requisitos:** R2.1.2, R2.1.4, R2.1.5
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Un login que auto-selecciona la cuenta institucional o un callback que falla en Safari privado arruina el primer minuto de la demo.
- **Opciones:**
  - `prompt=select_account` + botón "cambiar de cuenta"
  - Matriz de navegadores declarada en el spec con prueba en incógnito antes del 16-sep
  - Sin medidas específicas
- **Estudio de APIs:** §3.1 describe Google OIDC y §1.1 el uso de `state` en sesión; no aborda selector de cuentas, navegadores ni modo incógnito.
- **Fusiona:** P026

### Q-2.1-07 — ¿Qué operaciones abarca "administrar" un usuario de tipo profesor y qué pasa con sus cursos si se desactiva o elimina?

¿"Administrar" incluye editar nombre/foto, desactivar (bloquear login), reactivar, eliminar definitivamente, ver sus cursos? Si se desactiva o elimina a un profesor que es el único profesor de un curso, o cuyo token de Canvas está en uso por los jobs, ¿ese curso queda huérfano, se bloquea, se transfiere a otro profesor o se archiva? ¿Es borrado lógico o físico?

- **Requisitos:** R2.1.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define pantallas CRUD, soft vs hard delete y reglas de integridad referencial; sin regla explícita los jobs de sync/informe pueden quedar corriendo con las credenciales de una cuenta eliminada.
- **Opciones:**
  - Soft delete (desactivación) conservando cursos y credenciales
  - Hard delete con transferencia obligatoria de cursos
  - Hard delete dejando los cursos huérfanos/bloqueados
- **Estudio de APIs:** No lo aborda directamente; §1.1 advierte que sin `refresh_token` del profesor los jobs nocturnos (2.6.1, 2.4.5) dejan de funcionar.
- **Fusiona:** P047

### Q-2.1-08 — ¿Se fijan cuotas y controles de abuso sobre el registro abierto, dado que la URL será pública durante las dos semanas de revisión?

Con registro abierto (cualquier gmail crea cuenta y cursos), ¿se fijan cuotas por usuario o por curso (número de cursos, tareas, repos creados por día, mensajes de Canvas por hora, emails) para proteger el rate limit compartido de la instalación de la GitHub App y la cuota del proveedor de email, o se acepta el riesgo? ¿Crear cursos requiere aprobación o lista blanca del administrador (R2.1.1), o solo vincular GitHub lo requiere? ¿Qué ve un usuario que excede una cuota?

- **Requisitos:** R2.1.1, R2.1.2, R2.1.3
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define reglas de negocio de límites, el rol del admin y mensajes de error; sin cuotas un solo usuario puede agotar recursos compartidos durante la revisión.
- **Opciones:**
  - Registro abierto sin cuotas
  - Cuotas por usuario configurables por variable de entorno
  - Aprobación del administrador para crear cursos
- **Estudio de APIs:** §3.1 valida solo el sufijo gmail.com y `email_verified`; no aborda abuso, cuotas ni aprobación.
- **Fusiona:** P006

## Modelo de curso, membresías y ciclo de vida

### Q-2.1-09 — ¿Qué atributos propios tiene un curso en la app y cuál prevalece frente a los datos de Canvas?

¿Qué campos tiene un curso (nombre, código, período/semestre, descripción, zona horaria)? ¿Se completan automáticamente desde Canvas al vincular (`name`, `course_code`, término) o los escribe el profesor al crearlo? Si difieren, o si Canvas cambia el nombre después, ¿cuál prevalece y se sincroniza, o el sync respeta lo editado por el profesor?

- **Requisitos:** R2.1.3, R2.1.4
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define el formulario de creación de curso (paso 1 de la demo), el modelo de datos y si el sync de Canvas sobrescribe campos editados por el profesor.
- **Opciones:**
  - Atributos escritos por el profesor; Canvas nunca sobrescribe
  - Atributos importados de Canvas y de solo lectura en la app
  - Importación inicial editable, con marca de "modificado localmente"
- **Estudio de APIs:** §3.2 lista los campos del objeto Course (`name`, `course_code`, `sis_course_id`, `enrollment_term_id`, `start_at`, `end_at`) y sugiere guardar `canvas_course_id`, `canvas_base_url`, `course_code` y el id del profesor que hizo la vinculación.
- **Fusiona:** P053

### Q-2.1-10 — ¿Cuál es el modelo de membresía usuario ↔ curso ↔ rol y qué reglas de integridad rigen sobre el equipo docente?

¿Un mismo usuario (misma cuenta Google) puede tener roles distintos en cursos distintos (profesor en A, ayudante en B)? ¿Puede ser profesor y ayudante en el mismo curso? ¿Los ayudantes son "usuarios" con cuenta propia mediante el mismo login de Google que los profesores, o solo registros dentro de un curso sin login propio? Sobre las reglas entre profesores con "mismos permisos" (R2.1.7): ¿un profesor puede quitar a otro profesor, incluido el creador del curso? ¿Puede salir él mismo? ¿Se prohíbe dejar un curso sin profesores (regla del último profesor)? ¿Qué pasa si se quita al profesor cuyo token de Canvas está en uso? ¿Se permite cambiar el rol de una persona (ayudante → profesor o profesor → ayudante) y qué ocurre con sus correcciones asignadas y suscripciones al cambiar?

- **Requisitos:** R2.1.1, R2.1.7, R2.1.8, R2.1.9
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Fija el modelo Usuario ↔ Membresía(curso, rol) que debe existir desde la parcial aunque los ayudantes se implementen en la final, y las invariantes mínimas (al menos un profesor por curso) que evitan cursos huérfanos o pérdida de credenciales.
- **Opciones:**
  - Rol por curso con multi-membresía y regla del último profesor
  - Rol global único por usuario
  - Rol por curso sin restricción de último profesor
- **Estudio de APIs:** §3.4 propone RBAC por curso con roles profesor / ayudante jefe / ayudante y dice que profesores y ayudantes "viven en la BD de ustedes"; no define el modelo de usuario, la multi-membresía, los roles cruzados ni la regla del último profesor.
- **Fusiona:** P018, P048, P089

### Q-2.1-11 — ¿Qué ve cada usuario en su lista de cursos y qué muestra el estado vacío tras el login?

¿Cada usuario ve solo los cursos donde tiene membresía y el administrador ve todos? ¿Cómo se ordena y filtra la lista (activos vs archivados, por período)? ¿Qué muestra el estado vacío para un profesor recién registrado sin cursos (llamado a la acción "crear primer curso" con explicación de los pasos siguientes)?

- **Requisitos:** R2.1.3
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es la primera pantalla tras el login en la demo y se evalúa la guía al usuario; define la vista principal y la navegación.
- **Opciones:**
  - Solo cursos con membresía; admin ve todos
  - Solo cursos con membresía, sin vista global para nadie
  - Lista con filtros por estado y período y estado vacío con CTA guiado
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P058

### Q-2.1-12 — ¿Un mismo curso de Canvas o una misma organización de GitHub pueden vincularse a más de un curso de la app?

Casos: dos profesores crean cursos distintos apuntando al mismo curso de Canvas; una organización departamental se reutiliza entre semestres o asignaturas. Si se permite, ¿cómo se evitan colisiones de nombres de repos, cómo se sabe a qué curso pertenece cada repo preexistente en la org y cómo se evitan dobles notificaciones a los mismos estudiantes? Si no se permite, ¿qué mensaje ve el segundo profesor ("este curso de Canvas ya está vinculado por X") y cómo se le invita al curso existente?

- **Requisitos:** R2.1.3, R2.1.4, R2.1.5, R2.1.7, R2.3.8
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija restricciones de unicidad en la BD, el mensaje de conflicto y el diseño de la plantilla de nombres de repos (inclusión de curso y período).
- **Opciones:**
  - 1 curso Canvas ↔ 1 curso app y 1 org ↔ 1 curso app
  - 1 curso Canvas ↔ 1 curso app, con organización compartible usando prefijo por curso
  - Sin restricción, solo advertencia
- **Estudio de APIs:** §5.4 propone nombres `{curso}-{periodo}-{tarea}-...` que presuponen unicidad por curso+período, pero no fija si la org debe ser exclusiva de un curso ni la unicidad de la vinculación Canvas/org entre cursos de la app.
- **Fusiona:** P014, P057

### Q-2.1-13 — ¿Un curso de la app puede vincularse a VARIOS cursos de Canvas, cuando la universidad modela cada sección como un curso separado?

Muchas universidades modelan cada sección como un CURSO de Canvas independiente en lugar de como secciones dentro de un curso. Si el curso real de ICC4201 o el curso demo del profesor está así modelado: ¿la app soporta 1 curso app ↔ N cursos de Canvas (tratándolos como secciones virtuales con un único conjunto de repos por tarea y una sola org), obliga a crear un curso de la app por sección compartiendo la org (con riesgo de colisión de nombres y tareas duplicadas), o declara el caso fuera de alcance con un mensaje al profesor? ¿Se ha verificado con el profesor cómo está modelado su curso en la instancia institucional?

- **Requisitos:** R2.1.4, R2.2.2, R2.3.4, R2.4.2
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Cambia la cardinalidad curso-app ↔ curso-Canvas de 1:1 a 1:N en el modelo de datos, el sync, las fechas por sección y el nombre de los repos; descubrirlo el 16-sep sería fatal.
- **Opciones:**
  - 1 curso app = 1 curso Canvas (un curso app por sección, misma org)
  - 1 curso app = N cursos Canvas tratados como secciones virtuales
  - Fuera de alcance documentado, con mensaje al profesor
- **Estudio de APIs:** §3.2 guarda un único `canvas_course_id` por curso y §4.2 asume secciones dentro de un curso; no aborda cursos de Canvas separados por sección.
- **Fusiona:** P023

### Q-2.1-14 — ¿Se exige unicidad del nombre/slug de curso y de tarea, y cómo se sanitiza?

¿Se exige unicidad del nombre/slug de la tarea dentro del curso y del nombre del curso dentro de los cursos de un profesor (o global), o se permiten duplicados? Si dos tareas del mismo curso tienen el mismo slug, sus repos colisionarían en la organización: ¿se bloquea al crear, se agrega un sufijo automático, o se permite duplicar el nombre visible manteniendo un slug único generado? ¿Qué se hace si el slug sanitizado queda vacío (nombre compuesto solo por emojis o caracteres no ASCII)?

- **Requisitos:** R2.1.3, R2.3.1, R2.3.8
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Un evaluador que cree dos tareas "Tarea 1" provocaría colisiones de nombres de repo o confusión en las listas; R2.3.8 exige nombres automáticos e inequívocos sin definir la plantilla.
- **Opciones:**
  - Slug único por curso (bloquear duplicados)
  - Sufijo automático ante colisión
  - Nombre duplicable con slug único generado internamente
- **Estudio de APIs:** §5.2 incluye `slug` en Assignment y §5.4 usa `{tarea}` en el nombre del repo; no aborda unicidad de slug por curso ni sanitización.
- **Fusiona:** P025

### Q-2.1-15 — ¿Existen archivar, cerrar, reabrir y eliminar (curso y tarea), qué pasa con los repos de GitHub y cómo se define "curso activo" para los workers?

Ciclo de vida del curso: ¿existen archivar/cerrar, reabrir y eliminar? Al eliminar una tarea (o el curso) con repos ya creados y notas publicadas en Canvas, ¿se borran los repos de GitHub, se archivan o no se tocan? ¿Es borrado lógico recuperable o borrado duro? ¿Se exige confirmación tipeando el nombre y se notifica a los estudiantes? ¿Qué pasa con los correctores con entregas asignadas y con el informe diario? ¿Se detienen los jobs (sync de Canvas, aprovisionamiento, snapshots, informe)? ¿Quién puede ejecutar estas acciones? Y ¿cómo se define "curso activo" para los workers e informes: por fechas del término de Canvas, por estado manual en la app, o por tener tareas con entregas vigentes?

- **Requisitos:** R2.1.3, R2.3.4, R2.3.7, R2.6.1, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Decide si la app ejecuta acciones destructivas sobre GitHub y qué historial sobrevive (afecta permisos requeridos y flujo de confirmación); sin la regla de "curso activo" los workers procesan cursos muertos gastando rate limit o dejan de procesar cursos vigentes.
- **Opciones:**
  - Soft delete en la app; GitHub intacto
  - Soft delete + archivar repos en GitHub
  - Borrado duro con confirmación reforzada
  - "Curso activo" por estado manual (activo/archivado) fijado por el profesor
  - "Curso activo" derivado de `start_at`/`end_at` del término de Canvas
  - "Curso activo" derivado de tener tareas con entregas no cerradas
  - Combinación de criterios con prioridad definida
- **Estudio de APIs:** §4.4 fija la regla "nunca borren filas al sincronizar"; §9.1 define el informe por "tareas activas"; §12 dice "por curso activo" sin definirlo. No aborda el borrado de repos.
- **Fusiona:** P016, P055

### Q-2.1-16 — ¿Se requiere duplicar/clonar un curso para un nuevo semestre y qué se copia?

Si se incluye la duplicación, ¿qué se copia (tareas, permisos de ayudantes, configuración de notificaciones) y qué no (vinculaciones Canvas/GitHub, repos, mapeos de estudiantes)? ¿El curso duplicado exige pasar de nuevo por el wizard de vinculación?

- **Requisitos:** R2.1.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es una operación de "administrar cursos" que, si se incluye, define un flujo completo y reglas de qué datos son reutilizables entre semestres.
- **Opciones:**
  - No se duplica
  - Duplicar solo configuración (sin vinculaciones)
  - Duplicar con nuevo wizard de vinculación obligatorio
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P056

### Q-2.1-17 — ¿El modelo de datos soporta más de una instancia de Canvas (claves compuestas) y cuál es el alcance del mapeo estudiante ↔ GitHub?

Si la app admite más de una instancia de Canvas (`canvas_base_url`), ¿todo identificador de Canvas (`user_id`, `course_id`, `section_id`, `group_id`, `assignment_id`, `enrollment_id`) se almacena con clave compuesta (`canvas_instance_id`, `canvas_id`), dado que los IDs numéricos colisionan entre instancias? Si se fija una única instancia para el proyecto, ¿se deja igualmente la columna `canvas_instance_id` desde la primera migración para no rehacer claves después? Y si el mismo estudiante (mismo `canvas_user_id` en la misma instancia) está en dos cursos de la app: ¿el mapeo Canvas → GitHub es global por instancia (se reutiliza automáticamente y un cambio afecta a ambos cursos) o por curso (debe volver a entregarlo)? ¿Se soportan profesores con cursos en instancias distintas con tokens separados?

- **Requisitos:** R2.1.4, R2.2.1, R2.2.4, R2.2.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Cambiar las claves primarias después de la parcial es una migración destructiva sobre datos de demo; además define la clave del mapeo (instancia+usuario vs curso+usuario) y el modelo de credenciales multi-instancia.
- **Opciones:**
  - Clave compuesta por instancia y mapeo por instancia
  - ID de Canvas simple con instancia fija y mapeo por curso
  - Columna de instancia presente pero constante, con mapeo por curso
- **Estudio de APIs:** §3.2 recomienda guardar `canvas_base_url` porque "la instancia varía"; no aborda el impacto en las claves ni el alcance del mapeo entre cursos.
- **Fusiona:** P022, P098

## Flujo de configuración y vinculación del curso

### Q-2.1-18 — ¿La creación y vinculación de un curso es un wizard secuencial o pantallas/módulos independientes, y cómo se retoma?

¿Es un wizard con pasos (datos del curso → Canvas → GitHub → verificación → resumen) o una pantalla de configuración con tarjetas/secciones independientes, cada una con su estado? Si es wizard: ¿orden fijo o libre (Canvas y GitHub intercambiables)? ¿Se puede abandonar a mitad y retomar más tarde conservando lo hecho (curso creado sin GitHub), con estado persistente? ¿Se muestra un indicador de progreso ("paso 2 de 4") y desde dónde se reingresa (página del curso, banner "configuración incompleta")?

- **Requisitos:** R2.1.3, R2.1.4, R2.1.5, R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es el flujo central de la demo parcial y de la evaluación de "guía adecuada para realizar todo el proceso"; determina los estados intermedios del curso (borrador / parcialmente vinculado / verificado) que el modelo de datos y la UI deben soportar.
- **Opciones:**
  - Wizard lineal obligatorio
  - Wizard con pasos saltables y reanudables
  - Página de configuración con tarjetas independientes (Canvas / GitHub), cada una con su estado
- **Estudio de APIs:** §3.3 propone el flujo "Conectar organización" y una pantalla de verificación con checks y botón "reintentar"; §13 hito 5 lo llama "wizard de vinculación con checklist". No define pasos, orden, linealidad ni reanudación.
- **Fusiona:** P004, P028, P084

### Q-2.1-19 — ¿Cuál es la máquina de estados de vinculación del curso, qué muestra el estado vacío y qué acciones quedan bloqueadas en cada estado?

¿Puede existir un curso sin vinculaciones (estado "borrador")? ¿Cuáles son los estados (sin vincular / solo Canvas / solo GitHub / ambos verificados / vinculación con error) y qué funcionalidades quedan bloqueadas hasta que Canvas y GitHub estén vinculados y verificados (crear tareas, incorporar ayudantes, sincronizar estudiantes)? ¿Qué ve exactamente el profesor en un curso recién creado y aún no vinculado: un panel de "primeros pasos" con CTA ("Paso 1: vincular Canvas", "Paso 2: conectar GitHub", "Paso 3: crear tu primera tarea") y las demás pestañas bloqueadas o deshabilitadas con explicación, o todas las pestañas accesibles mostrando "0 estudiantes"?

- **Requisitos:** R2.1.3, R2.1.4, R2.1.5, R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define el onboarding evaluado el 16-sep, qué botones aparecen habilitados en cada estado, el banner de estado del curso y las reglas de precondición que el spec debe listar como reglas de negocio.
- **Opciones:**
  - Estados explícitos con bloqueo duro de acciones dependientes
  - Estados explícitos con advertencia pero sin bloqueo
  - Sin máquina de estados: todo accesible con datos vacíos
- **Estudio de APIs:** §3.3 propone un checklist de verificación y §13 hito 5 menciona el wizard, pero no definen estados del curso, estado vacío ni bloqueos por precondición.
- **Fusiona:** P027, P054

## Vinculación con Canvas

### Q-2.1-20 — ¿Qué instancia(s) de Canvas soporta la app y cómo se administran sus Developer Keys?

¿La URL base de Canvas es (a) única y fijada por configuración del despliegue (instancia institucional o `canvas.instructure.com` Free-for-Teacher), (b) escrita por el profesor al vincular (campo "URL de Canvas"), o (c) elegida de una lista cerrada de instancias preconfiguradas? Si hay más de una instancia, cada una requiere su propio `client_id`/`secret` y `redirect_uri` registrada: ¿cómo se administran esas credenciales y qué mensaje se muestra si la instancia no está soportada? ¿`canvas_base_url` se guarda por curso o es global?

- **Requisitos:** R2.1.4, R2.1.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Una URL fija impide que un revisor con otra instancia pruebe la vinculación; una URL variable exige gestión de múltiples credenciales OAuth en el spec y cambia el formulario de vinculación y el modelo de datos.
- **Opciones:**
  - Instancia única fija por configuración del servidor
  - Selector entre instancias preconfiguradas con sus Developer Keys
  - Campo libre de URL por curso con una sola Developer Key
  - Campo libre de URL con tabla de instancias y credenciales
- **Estudio de APIs:** §3.2 recomienda guardar `canvas_base_url` porque "la instancia varía"; §1.2 propone Free-for-Teacher como plan B. No decide si la UI expone la instancia.
- **Fusiona:** P003, P033, P059

### Q-2.1-21 — ¿Se solicitó (o se solicitará) una Developer Key en la instancia Canvas de la universidad, con qué responsable, plazo y plan B, y contra qué instancia y cuentas se hará la demo del 16-sep?

¿A quién se solicita, quién del equipo es responsable, cuál es la fecha límite para tenerla antes del 16-sep y cuál es el plan B (Free-for-Teacher con cuenta admin propia; token manual)? ¿La demo se hará contra el Canvas institucional o contra una instancia de prueba, y con qué cuentas de Canvas van a probar el profesor y los ayudantes evaluadores? ¿Qué datos de prueba (secciones, estudiantes, grupos, tareas) deben existir ese día?

- **Requisitos:** R2.1.4, R2.1.6
- **Tipo:** dependencia_externa · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Sin Developer Key no hay OAuth ni datos reales; determina qué instancia, qué cuentas y qué datos de prueba deben existir el día de la demo.
- **Opciones:**
  - Developer Key institucional gestionada con el administrador de la instancia
  - Instancia propia Free-for-Teacher con cuenta administradora del equipo
  - Token manual solo para la demo, con OAuth implementado igual
- **Estudio de APIs:** §1.1 indica que la Developer Key la crea un administrador de la instancia; §1.2 propone Free-for-Teacher como Plan B; §13 hito 2 está marcado "Día 1" con riesgo rojo "depende de terceros".
- **Fusiona:** P060

### Q-2.1-22 — ¿Qué mecanismo de autenticación con Canvas se implementa: OAuth2 con Developer Key, token manual, o ambos?

Opciones: (a) OAuth2 authorization code con Developer Key; (b) ingreso manual de un access token por el profesor; (c) ambos (OAuth como principal y token manual como respaldo, visible solo bajo un flag de entorno o modo demo). Si se incluye (b), ¿se acepta el riesgo de que los evaluadores lo consideren una violación de la política de la API de Canvas?

- **Requisitos:** R2.1.4
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define el flujo de vinculación (redirección a Canvas vs campo de texto), el almacenamiento del `refresh_token` y un posible punto de descuento en la evaluación.
- **Opciones:**
  - Solo OAuth2
  - Solo token manual
  - OAuth2 + token manual oculto tras flag de entorno
- **Estudio de APIs:** §1.1 recomienda OAuth2; §1.2 cita la política de Canvas que prohíbe pedir tokens manuales a otros usuarios y recomienda implementar OAuth2 igualmente aunque la demo use un token pegado.
- **Fusiona:** P061

### Q-2.1-23 — ¿La Developer Key tendrá "enforce scopes" activado, cuál es la lista exacta de scopes y qué pasa si el usuario rechaza el consentimiento o falta un scope?

¿Se activa "enforce scopes"? Si sí, ¿cuál es la lista exacta de scopes (lecturas y escrituras necesarias para 2.2–2.7) que se piden de una sola vez al vincular? ¿Qué se muestra si el usuario rechaza el consentimiento (`error=access_denied`) o si más adelante se descubre que falta un scope?

- **Requisitos:** R2.1.4
- **Tipo:** dependencia_externa · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Los scopes deben fijarse en la key y en la URL de autorización; agregar uno después obliga a re-autorizar a todos los profesores.
- **Opciones:**
  - Enforce scopes activado con lista cerrada declarada en el spec
  - Sin enforce scopes (token con todos los permisos del usuario)
- **Estudio de APIs:** §1.1 y §1.3 dan el formato `url:GET|/api/v1/...` y una lista de ejemplo de 14 scopes.
- **Fusiona:** P070

### Q-2.1-24 — ¿La conexión OAuth con Canvas es por usuario o por curso, dónde se gestiona en la UI y se usa `replace_tokens`?

¿El profesor autoriza una vez y el token se reutiliza en todos sus cursos, o autoriza en cada vinculación? Si el mismo profesor vincula dos cursos, ¿hace OAuth dos veces? ¿Se usa `replace_tokens=1`, que invalidaría los tokens previos del mismo usuario y rompería la otra vinculación? ¿Dónde se muestra y gestiona la conexión en la UI ("Mi cuenta → Conexiones" con estado, fecha de autorización, botones "Reconectar" / "Desconectar")? ¿Qué pasa con los cursos de un profesor si desconecta Canvas?

- **Requisitos:** R2.1.2, R2.1.4
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Cambia el wizard (si ya está conectado, el paso Canvas se reduce a elegir curso), la pantalla de cuenta, la tabla de credenciales (por usuario vs por curso) y el comportamiento de los jobs nocturnos que dependen del `refresh_token` del profesor que vinculó.
- **Opciones:**
  - Conexión por usuario, reutilizable en todos sus cursos
  - Conexión por curso (una credencial por vinculación)
  - Ambas: por usuario con posibilidad de reautorizar por curso
- **Estudio de APIs:** §1.1 recomienda OAuth2 con token del profesor, guardar el `refresh_token`, y advierte que `replace_tokens=1` invalida tokens previos del mismo usuario y que el refresh token no rota; §3.2 dice guardar "el id del profesor que hizo la vinculación", lo que sugiere token por usuario, sin definir la UI.
- **Fusiona:** P029, P071

### Q-2.1-25 — ¿Qué muestra el selector de curso de Canvas, qué cursos lista, qué pasa si la lista viene vacía y qué se hace ante un curso ya vinculado?

¿Se listan solo los cursos donde el usuario autenticado tiene enrollment `teacher` activo, o también `ta`/`designer`, cursos no publicados o concluidos? ¿Qué columnas se muestran para desambiguar homónimos (nombre, código, período/term, N estudiantes, estado publicado)? ¿Qué se muestra si la lista viene vacía (el usuario no es teacher en ningún curso, solo tiene rol TA, o faltan scopes) y qué acción se ofrece (guía para pedir el rol en Canvas, bloqueo, o ingreso manual del ID/URL del curso como ruta alternativa)? ¿Se advierte o se bloquea si ese curso de Canvas ya está vinculado a otro curso de la app (del mismo profesor o de otro)?

- **Requisitos:** R2.1.4, R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Fija los parámetros de la llamada a Canvas y el contenido de la pantalla clave del wizard: el mensaje de estado vacío, la ruta alternativa y la regla de unicidad Canvas-course ↔ app-course, todas visibles en la demo.
- **Opciones:**
  - Solo cursos con enrollment teacher activo
  - teacher + ta
  - Todos los cursos visibles con filtro en la UI
  - Con ingreso manual de ID/URL como alternativa
  - Sin ingreso manual (bloqueo con guía)
- **Estudio de APIs:** §3.2 propone `GET /courses?enrollment_type=teacher&enrollment_state=active&include[]=term&include[]=total_students` y enumera los campos disponibles; no aborda estado vacío, entrada manual ni duplicados.
- **Fusiona:** P030, P064, P065

### Q-2.1-26 — ¿Cómo se manejan los casos borde del callback OAuth de Canvas?

Casos: el usuario recarga la página de callback (el `code` es de un solo uso), el `state` no coincide, dos pestañas vinculan el mismo curso a la vez, o el usuario autoriza con una cuenta de Canvas distinta a la esperada. ¿Se guarda y muestra el `user.id`/`name` de Canvas devuelto con el token y se valida que sea profesor del curso elegido? ¿Qué mensaje y qué estado resultan en cada caso?

- **Requisitos:** R2.1.4, R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Evita vinculaciones a medias o con la identidad equivocada; define mensajes de error y la idempotencia del paso de vinculación.
- **Opciones:**
  - Validación estricta de `state` e identidad con mensajes específicos por caso
  - Reintento silencioso reiniciando el flujo
  - Sin manejo explícito (error genérico)
- **Estudio de APIs:** §1.1 indica que el `code` es de un solo uso, que el `state` es obligatorio contra CSRF y que la respuesta del token trae `user.id` y `user.name`; §3.2 sugiere guardar el id del profesor vinculador.
- **Fusiona:** P072

### Q-2.1-27 — ¿Con el token de qué persona opera la app sobre Canvas, qué ocurre si ese token falla y cómo se muestra y audita la autoría de las escrituras?

Opciones: (A) el token del profesor que hizo la vinculación se usa para todas las acciones del curso, incluidas las de co-profesores y ayudantes; (B) cada profesor/ayudante autoriza su propio token y la app usa el del usuario que ejecuta la acción; (C) híbrido con fallback. Si hay varios profesores, ¿de cuál se usa? ¿Qué pasa si ese profesor se retira del curso, revoca el token o su refresh falla: se hace failover automático al token de otro profesor, se pausa todo y se alerta, o se exige que cada profesor haga OAuth al ingresar? ¿Cómo se indica en la UI en nombre de quién se ejecutan las escrituras en Canvas (notas, anuncios, mensajes) y cómo se audita en la app quién ejecutó realmente la acción?

- **Requisitos:** R2.1.4, R2.1.7, R2.1.8, R2.6.5, R2.6.6, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Determina el modelo de credenciales por curso vs por usuario, los requisitos de enrolamiento en Canvas de co-profesores y ayudantes, el failover entre tokens y la trazabilidad de acciones ejecutadas "en nombre de" otro usuario.
- **Opciones:**
  - A: token del vinculador para todo el curso (curso en "vinculación rota" si falla)
  - A con failover automático al siguiente profesor que haya autorizado
  - B: token propio de cada usuario que ejecuta la acción
  - C: A por defecto, B si el usuario autorizó el suyo
- **Estudio de APIs:** §3.4 describe A ("simple y robusto") y B ("correcto pero frágil") y recomienda A por defecto con B como fallback, mostrando en la UI "las notas se publican como Profesor X"; §1.1 trata el refresh token. No resuelve el caso de múltiples profesores ni la salida del dueño del token.
- **Fusiona:** P019, P062

### Q-2.1-28 — ¿Qué hace la app si el profesor que vincula tiene su TeacherEnrollment limitado a su sección (`limit_privileges_to_course_section=true`)?

Con ese flag, la API le devuelve solo estudiantes, secciones y overrides visibles para su sección: el sync marcaría al resto como inexistente o retirado, las fechas de otras secciones serían invisibles y las escrituras (mensajes, notas, anuncios) hacia otras secciones fallarían. ¿El checklist de R2.1.6 lee ese flag (p. ej. `GET /courses/:id/enrollments?user_id=self`) y lo marca como bloqueante o como advertencia? ¿Qué se sugiere (que vincule otro profesor sin límite)? ¿Se exige que el vinculador vea el curso completo o se soporta explícitamente vincular "solo mi sección" como alcance declarado? Verificar el comportamiento real de `/enrollments` y `/conversations` con un teacher limitado.

- **Requisitos:** R2.1.4, R2.1.6, R2.2.1, R2.4.2, R2.6.5
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Produce un roster incompleto sin error visible, bajas masivas falsas de estudiantes y fechas incorrectas, con fallos posteriores difíciles de diagnosticar; agrega un ítem al checklist y una regla sobre quién puede vincular.
- **Opciones:**
  - Detectar y bloquear la vinculación con un profesor limitado a sección
  - Detectar y advertir, permitiendo continuar
  - Soportar cursos "de una sección" como alcance declarado
  - No manejar el caso
- **Estudio de APIs:** §3.2 lista cursos con `enrollment_type=teacher` y §3.3 define el checklist; §4 asume visibilidad completa del roster. No menciona `limit_privileges_to_course_section`.
- **Fusiona:** P007, P024

### Q-2.1-29 — ¿Cómo se tratan los roles personalizados de Canvas en los filtros de listado de cursos e importación de personas?

Las instituciones definen roles derivados de Teacher/Student/TA (p. ej. "Profesor coordinador", "Alumno oyente", "Ayudante corrector"). ¿Los filtros `enrollment_type=teacher` (listar cursos) y `type[]=StudentEnrollment` (roster) incluyen esos roles personalizados, o hay que filtrar por `role_id`/`base_role_type`? ¿Un rol personalizado basado en Student cuenta como estudiante para crear repo, y uno basado en TA para importar ayudantes desde Canvas?

- **Requisitos:** R2.1.4, R2.1.8, R2.2.1
- **Tipo:** verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Determina los parámetros exactos de las llamadas de sync y a quién se le crea repo en la instancia institucional.
- **Opciones:**
  - Filtrar por `base_role_type` (incluye roles personalizados derivados)
  - Filtrar por tipo base estricto (excluye roles personalizados)
  - Lista de `role_id` configurable por curso
- **Estudio de APIs:** §4.1 menciona `enrollment_role_id` como parámetro pero no la distinción entre roles base y personalizados.
- **Fusiona:** P008

## Vinculación con GitHub

### Q-2.1-30 — ¿Qué mecanismo se usa para operar sobre GitHub: GitHub App, OAuth App o PAT del profesor?

Opciones: (a) GitHub App instalada en la organización; (b) OAuth App actuando como el profesor; (c) PAT del profesor ingresado manualmente; (d) GitHub App con PAT como respaldo de desarrollo. Si se elige GitHub App, ¿el equipo acepta la complejidad de JWT + installation tokens para tenerla lista el 16-sep?

- **Requisitos:** R2.1.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define el flujo de vinculación (instalar App vs pegar token), el rate limit disponible, la recepción de webhooks y la dependencia de una cuenta personal.
- **Opciones:**
  - GitHub App
  - OAuth App
  - PAT del profesor
  - GitHub App con PAT como respaldo de desarrollo
- **Estudio de APIs:** §2.1 recomienda GitHub App por rate limit escalable, token acotado a la org, webhooks incluidos y no depender del PAT de una persona.
- **Fusiona:** P073

### Q-2.1-31 — ¿La GitHub App será pública o privada y cómo se distribuye?

¿Será pública (instalable por cualquier organización, necesario para que un profesor la instale en su propia org) o privada (solo instalable en la cuenta que la creó)? ¿Se comparte por URL de instalación o se publica en el Marketplace?

- **Requisitos:** R2.1.5
- **Tipo:** investigable_en_docs · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Una App privada solo se puede instalar en la cuenta propietaria, lo que impediría al profesor vincular una org que no sea la del equipo; determina la visibilidad de la App y el texto de guía.
- **Opciones:**
  - Pública, distribuida por URL de instalación
  - Pública, publicada en el Marketplace
  - Privada (solo la cuenta del equipo)
- **Estudio de APIs:** §3.3 asume la URL `github.com/apps/<tu-app>/installations/new` sin discutir la visibilidad pública/privada de la App.
- **Fusiona:** P074

### Q-2.1-32 — ¿Cuál es la lista exacta de permisos que solicitará la GitHub App y cómo se maneja la necesidad de un permiso adicional posterior?

Lista candidata: Repository (Administration: write, Contents: write, Metadata: read) y Organization (Members: write, Administration: write); ¿se agrega Workflows u otros? Si más adelante se necesita un permiso adicional, el owner de la org debe aceptar la actualización: ¿la app detecta la aceptación pendiente y guía al profesor?

- **Requisitos:** R2.1.5
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Los permisos se piden al instalar; un permiso faltante bloquea el aprovisionamiento o las invitaciones a mitad de camino y exige un flujo de re-aceptación.
- **Opciones:**
  - Lista mínima cerrada, con flujo de re-aceptación detectado por la app
  - Lista amplia desde el inicio para evitar re-aceptaciones
- **Estudio de APIs:** §2.3 incluye la tabla de permisos y advierte verificar `POST /orgs/{org}/repos`; Apéndice A.1 y A.2 detallan los permisos exactos para crear repos en una org y para `/generate`.
- **Fusiona:** P081

### Q-2.1-33 — ¿Se activa "Request user authorization (OAuth) during installation" en la GitHub App?

Activarlo daría un user-to-server token del profesor que permitiría (a) confirmar que quien instaló es owner de la org, (b) listar sus organizaciones para validar o preseleccionar la org antes de salir de la app, y (c) guardar su login de GitHub para agregarlo como docente a los repos. ¿O se evita para no pedir permisos adicionales y se confía en la instalación como única prueba de control de la org?

- **Requisitos:** R2.1.5, R2.1.6, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Cambia el flujo de vinculación (un consentimiento adicional), los datos guardados del profesor y la capacidad de verificar ownership en R2.1.6.
- **Opciones:**
  - Solo instalación (`setup_url`)
  - Instalación + autorización de usuario
  - Autorización de usuario opcional posterior ("conectar mi GitHub")
- **Estudio de APIs:** §3.3 usa únicamente `installations/new` + `setup_url`; no menciona la autorización de usuario durante la instalación.
- **Fusiona:** P011

### Q-2.1-34 — ¿Qué guía se da antes de salir a github.com, se puede preseleccionar la organización, y qué se muestra en cada resultado del retorno?

El paso GitHub saca al profesor de la app hacia github.com para instalar la App. ¿Qué guía se le da ANTES de salir (captura o lista: "elige la organización del curso, no tu cuenta personal", "selecciona All repositories")? ¿La URL de instalación permite preseleccionar la organización destino (parámetro `target_id` o similar) y qué parámetros devuelve GitHub en el `setup_url` en cada resultado (`install` / `update` / `request`)? ¿Qué se muestra al volver en cada caso anómalo: vuelve sin instalar (`setup_action` ≠ `install`), instaló en su cuenta personal en vez de una organización, instaló en otra org que ya está vinculada a otro curso, o instaló con "Only select repositories"?

- **Requisitos:** R2.1.5, R2.1.6
- **Tipo:** decision_equipo · investigable_en_docs · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Si se puede preseleccionar la org, el paso GitHub del wizard se simplifica y desaparecen varios mensajes de error; cada caso anómalo necesita de todos modos un mensaje y una acción de recuperación en el spec.
- **Opciones:**
  - Preselección de organización si la API lo permite, con guía previa mínima
  - Sin preselección, con guía previa detallada y manejo explícito de cada retorno anómalo
- **Estudio de APIs:** §3.3 describe la redirección a `/installations/new` y el retorno con `installation_id` y `setup_action=install`; no menciona preselección ni cubre casos anómalos.
- **Fusiona:** P031, P044

### Q-2.1-35 — ¿Qué hace la app si el profesor no tiene organización, no es owner, o la instalación queda como solicitud pendiente?

¿Se le explican dentro de la app los pasos para crear la organización (con enlace directo a `github.com/organizations/new` y sus requisitos: plan, repos privados) o se asume que la org existe previamente? ¿La app verifica que el profesor sea owner/admin de la org o basta con que la App esté instalada? Si es solo miembro, GitHub deja una "solicitud de instalación" pendiente de aprobación por un owner: ¿la app detecta ese estado y qué muestra mientras tanto? ¿Y si instala la App en su cuenta personal en lugar de una organización (se acepta o se rechaza)?

- **Requisitos:** R2.1.5, R2.1.6
- **Tipo:** decision_equipo · verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define si el onboarding incluye documentación embebida para un prerrequisito externo, los estados intermedios del paso GitHub del wizard y el mensaje de guía; el enunciado exige explícitamente una organización.
- **Opciones:**
  - Exigir org preexistente y ownership verificado, bloqueando lo demás
  - Guiar dentro de la app a crear la organización
  - Aceptar instalación en cuenta personal como caso soportado
  - Detectar y mostrar el estado "solicitud de instalación pendiente"
- **Estudio de APIs:** §3.3 describe solo el camino feliz (redirect a `setup_url` con `installation_id`) y asume una org del curso ya existente (§2.2); no cubre solicitudes pendientes, ownership ni instalación en cuentas personales.
- **Fusiona:** P032, P075

### Q-2.1-36 — ¿Se exige instalación con `repository_selection = all` o se acepta "solo repositorios seleccionados"?

Con selección parcial, ¿los repos que la app cree quedan automáticamente dentro de la instalación o la App pierde acceso a ellos? ¿Se verifica este aspecto en el checklist y qué mensaje se muestra si no cumple?

- **Requisitos:** R2.1.5, R2.1.6
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Si la instalación es parcial, los repos creados podrían quedar inaccesibles para webhooks y sync; define un chequeo potencialmente bloqueante del wizard.
- **Opciones:**
  - Exigir `all` y bloquear si es parcial
  - Aceptar selección parcial con advertencia
  - Aceptar selección parcial solo si se verifica empíricamente que los repos nuevos quedan incluidos
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P076

### Q-2.1-37 — ¿Cómo se correlaciona el `installation_id` devuelto al `setup_url` con el curso que se estaba vinculando, y qué se hace con instalaciones huérfanas?

¿La correlación es por parámetro `state`, por la sesión del usuario, u otra? ¿Qué pasa si alguien instala la App directamente desde GitHub sin pasar por la app (instalación sin curso asociado), o si un usuario vincula dos cursos a la misma organización?

- **Requisitos:** R2.1.5, R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define la correlación segura entre el callback y la intención del usuario, y evita vincular la organización al curso equivocado.
- **Opciones:**
  - Parámetro `state` firmado que identifica el curso
  - Correlación por sesión del usuario más pantalla de selección al volver
  - Pantalla de "instalaciones sin curso" para adoptarlas manualmente
- **Estudio de APIs:** §3.3 describe el redirect con `installation_id` y `setup_action=install` sin tratar la correlación con el curso ni las instalaciones huérfanas.
- **Fusiona:** P083

### Q-2.1-38 — ¿Con qué clave se identifica la vinculación de GitHub y qué pasa si la organización se renombra o la App se reinstala?

¿La vinculación se identifica por `installation_id`, por el id numérico de la organización o por su `login`? ¿Qué pasa si la organización se renombra, o si la App se desinstala y reinstala (nuevo `installation_id`): la app se auto-repara o exige volver a vincular?

- **Requisitos:** R2.1.5
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Define la clave estable de la vinculación y el comportamiento tras una reinstalación o un renombre.
- **Opciones:**
  - Clave = id numérico de la organización (estable ante renombre)
  - Clave = `installation_id` (exige re-vincular tras reinstalar)
  - Clave = `login` de la organización
  - Combinación con auto-reparación al detectar nueva instalación de la misma org
- **Estudio de APIs:** §3.3 guarda `installation_id` y lo confirma con `GET /orgs/{org}/installation`.
- **Fusiona:** P077

### Q-2.1-39 — ¿Qué restricciones y políticas de la organización se verifican, cuáles bloquean y qué se muestra cuando impiden completar el proceso?

Condiciones a considerar: plan de la organización (Free vs Team) y límite de colaboradores en repos privados; requisito de 2FA para miembros (impide agregar estudiantes sin 2FA); restricción de invitaciones a outside collaborators; política `members_can_create_repositories`; repos preexistentes con nombres que colisionan con la plantilla; fallo de la creación desde template por permisos. ¿Se detectan estas restricciones en la verificación de vinculación (R2.1.6) antes de crear la tarea, cuáles son bloqueantes y cuáles advertencias, y qué códigos de error del worker se consideran "definitivos" vs "transitorios"? Verificar en una organización Free real los límites vigentes.

- **Requisitos:** R2.1.5, R2.1.6, R2.3.7, R2.3.9, R2.3.11
- **Tipo:** verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Evita que la vinculación se dé por correcta y luego falle la creación de repos o la incorporación de estudiantes por políticas de la organización; determina qué chequeos incluye el checklist y la clasificación de errores del worker.
- **Opciones:**
  - Verificar todas las condiciones en el checklist con clasificación bloqueante/advertencia
  - Verificar solo las que la API expone directamente y reportar el resto al primer fallo real
  - No verificar y reportar errores contextuales en tiempo de ejecución
- **Estudio de APIs:** §3.3 propone el checklist con repo temporal; §2.3 y Apéndice A.1–A.2 piden verificar permisos; §14 indica "revisen el límite de colaboradores en repos privados de organización". No menciona 2FA ni políticas de creación de repos.
- **Fusiona:** P012, P082

### Q-2.1-40 — ¿Se soportan organizaciones con SAML SSO obligatorio o IP allowlist, y estudiantes con cuentas Enterprise Managed Users?

Si la organización destino es institucional con SAML SSO obligatorio o lista de IP permitidas, o si los estudiantes usan cuentas Enterprise Managed Users (login con sufijo `_empresa`, que no pueden ser colaboradores fuera de su enterprise): ¿la app lo soporta o lo declara fuera de alcance? ¿El checklist de R2.1.6 detecta SAML/IP allowlist (que puede bloquear los installation tokens desde el hosting) y la validación de R2.2.4 detecta cuentas EMU para avisar al estudiante que necesita una cuenta personal?

- **Requisitos:** R2.1.5, R2.1.6, R2.2.4, R2.3.9
- **Tipo:** dependencia_externa · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Condiciona qué organizaciones puede usar un profesor real, agrega ítems al checklist y un caso de rechazo en la validación de usuarios de GitHub.
- **Opciones:**
  - Soportar y detectar en el checklist
  - Declarar fuera de alcance documentado
  - Detectar solo el caso EMU en la validación de usuarios
- **Estudio de APIs:** No lo aborda (§2 y §3.3 asumen una organización estándar sin SSO ni IP allowlist).
- **Fusiona:** P009

### Q-2.1-41 — ¿Qué se hace con GitHub Actions y Codespaces en los repos de estudiantes y con los workflows del repo base?

Los estudiantes con `push` pueden agregar workflows de GitHub Actions y abrir Codespaces en sus repos privados, consumiendo minutos y almacenamiento del plan de la organización (GitHub bloquea Actions y pushes de LFS cuando la org agota su cuota facturable). ¿La app deshabilita Actions al crear cada repo, exige una política de organización ("Actions disabled" o "solo repos seleccionados") verificada en el checklist, o se acepta el consumo? ¿Se permite en cambio a los profesores incluir workflows de autocorrección en el repo base (R2.3.6), lo que exige el permiso Workflows en la App?

- **Requisitos:** R2.1.5, R2.1.6, R2.3.6, R2.3.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define permisos de la App, la configuración por repo al crearlo, un ítem del checklist y el alcance de la autocorrección.
- **Opciones:**
  - Deshabilitar Actions por repo al crearlo
  - Exigir política de organización y verificarla en el checklist
  - Permitir Actions y documentar el riesgo de cuota
- **Estudio de APIs:** §5.3 menciona el permiso Workflows solo para subir archivos en `.github/workflows`; no aborda consumo de minutos, Codespaces ni políticas de organización.
- **Fusiona:** P010

## Equipo docente: incorporación, permisos y alcance

### Q-2.1-42 — ¿Cómo se incorpora a un co-profesor o a un ayudante al curso y qué estados tiene la invitación?

Mecanismos posibles: (a) ingresar su correo gmail, quedando como invitación pendiente hasta que inicie sesión; (b) seleccionar un usuario ya registrado; (c) generar un enlace de invitación firmado con vigencia; (d) importar los `TeacherEnrollment` / `TaEnrollment` del curso de Canvas. ¿La invitación expira y se puede cancelar? ¿Qué ve el invitado al entrar por primera vez ("Has sido invitado como ayudante al curso X — Aceptar")? ¿Qué pasa si aún no tiene cuenta, si su correo no es gmail.com (p. ej. el correo del TA importado desde Canvas), o si la invitación expira? ¿Se muestran las invitaciones pendientes en la pantalla "Equipo docente"?

- **Requisitos:** R2.1.7, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el flujo completo de invitación con sus estados (pendiente / aceptada / expirada), sus pantallas y el emparejamiento con la cuenta Google; hoy no está especificado.
- **Opciones:**
  - Invitación por gmail (queda pendiente hasta el primer login)
  - Selección entre usuarios ya registrados
  - Link de invitación firmado con vigencia
  - Importar `TeacherEnrollment`/`TaEnrollment` desde Canvas
  - Combinación de varios mecanismos
- **Estudio de APIs:** §3.4 solo dice que profesores y ayudantes "viven en la BD de ustedes" y aporta una "Nota de coherencia": que un ayudante exista en la app no implica que exista en Canvas. No define el flujo de incorporación.
- **Fusiona:** P041, P087, P094

### Q-2.1-43 — ¿Se exige que el co-profesor o el ayudante tenga enrollment en el curso de Canvas y autorice su propio token?

¿Se exige que el co-profesor tenga enrollment de profesor (y el ayudante, de TA) en el curso de Canvas, y/o que autorice su propio token de Canvas? Si no lo tiene, ¿se le permite operar igual usando el token del profesor vinculador, y se le advierte? ¿Debe existir en Canvas para poder publicar notas (R2.7.6)?

- **Requisitos:** R2.1.7, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina si "mismos permisos" es realizable para alguien que no existe en Canvas, qué se verifica al aceptar la invitación y qué prerrequisitos externos debe explicar la app.
- **Opciones:**
  - Exigir enrollment en Canvas y token propio
  - No exigir nada: todo opera con el token del profesor vinculador
  - No exigir, pero advertir y ofrecer autorizar el token propio
- **Estudio de APIs:** §3.4 plantea las opciones A (token del profesor para todo) y B (cada uno su token; requiere enrollment en Canvas), con la "Nota de coherencia" sobre existir en la app vs en Canvas.
- **Fusiona:** P088

### Q-2.1-44 — ¿Cuál es la lista definitiva de permisos de ayudante y la matriz rol × pantalla × acción?

R2.1.8 exige definir al menos 3 permisos. ¿Se adopta la propuesta del estudio (gestionar curso, gestionar tareas/repo base, disparar aprovisionamiento, asignar correctores, publicar notas, comunicar con estudiantes, suscribirse al informe), se recorta o se agregan otros (ver dashboard, editar el mapeo Canvas ↔ GitHub de estudiantes, ver informes históricos)? ¿Cómo se nombran y describen en la UI? Y para cada pantalla o acción (configuración del curso, mapeo de estudiantes, estado de repos y reintentos, repo base, dashboard, timeline, informe, comunicaciones, asignación de correctores, calificar, ver notas de otros correctores, auditoría), ¿qué puede ver y hacer cada rol? En particular: ¿un ayudante ve logins de GitHub y correos de estudiantes, puede reintentar repos, enviar mensajes a estudiantes, ver o editar calificaciones de entregas no asignadas a él? ¿Un cambio de permisos o el retiro se aplican de inmediato en la sesión activa?

- **Requisitos:** R2.1.8, R2.1.9, R2.2.6, R2.3.11, R2.6.5, R2.7.2, R2.7.6, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Es un requisito explícito con umbral mínimo que será defendido en la actividad de validación del 7-oct; la matriz rol × pantalla × acción es la base de los criterios de aceptación de autorización del backend y del formulario de permisos.
- **Opciones:**
  - Adoptar los 7 permisos propuestos por el estudio
  - Recortar a un conjunto mínimo de 3 permisos
  - Ampliar con permisos adicionales de visualización de datos
- **Estudio de APIs:** §3.4 propone 7 permisos (`course.manage`, `assignment.manage`, `repo.provision`, `grading.assign`, `grading.submit`, `student.communicate`, `report.subscribe`) y 3 roles (profesor / ayudante jefe / ayudante), como "propuesta defendible en la validación del 7-oct"; no está aprobada ni cubre la vigencia inmediata de los cambios.
- **Fusiona:** P021, P090

### Q-2.1-45 — ¿Cuál es el modelo de autorización (roles fijos, permisos granulares o rol base con ajustes) y cómo se administra en la UI?

¿Se presentan roles predefinidos seleccionables ("Ayudante jefe" / "Ayudante"), checkboxes por permiso individual, o un rol base con ajuste fino? ¿Cada permiso tiene una descripción de una línea en la UI y el ayudante puede ver sus propios permisos? ¿Existe jerarquía (un ayudante jefe puede administrar los permisos de otros ayudantes) o solo el profesor administra? ¿Se puede cambiar el rol de un ayudante y qué ocurre con sus asignaciones en curso? ¿Los cambios surten efecto inmediato en las sesiones activas o al siguiente login?

- **Requisitos:** R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la implementación del RBAC, la pantalla "Equipo docente" con su vocabulario y el comportamiento visible cuando un permiso falta (relevante porque "lo no accesible no se considera cumplido").
- **Opciones:**
  - Roles fijos
  - Permisos granulares por ayudante (checkboxes)
  - Rol base + ajustes finos
- **Estudio de APIs:** §3.4 propone la tabla de permisos y los roles "Ayudante jefe" y "Ayudante" como propuesta; no trata la jerarquía de administración ni el efecto en sesiones activas.
- **Fusiona:** P040, P091

### Q-2.1-46 — ¿Qué navegación ve un ayudante y cómo se presentan los controles para los que no tiene permiso?

¿El ayudante ve la misma navegación que el profesor con acciones ocultas o deshabilitadas según permiso, o una interfaz distinta centrada en "mis correcciones"? ¿Los controles sin permiso se ocultan por completo o se muestran deshabilitados con un tooltip ("requiere permiso X, pídelo al profesor")? ¿Qué pestañas de tarea y de curso puede ver un ayudante con el rol mínimo?

- **Requisitos:** R2.1.8, R2.7.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la matriz vista × rol del spec y el patrón de UI para permisos, necesario para que los tres permisos mínimos sean verificables en la revisión.
- **Opciones:**
  - Misma navegación con controles ocultos
  - Misma navegación con controles deshabilitados y explicación
  - Interfaz reducida específica para ayudantes
- **Estudio de APIs:** §3.4 propone 7 permisos y 3 roles, sin definir la UI por rol.
- **Fusiona:** P039

### Q-2.1-47 — ¿A qué nivel se otorgan los permisos (curso, tarea o sección) y qué datos de estudiantes ve un ayudante?

¿Los permisos aplican a todo el curso y todas sus tareas, o pueden acotarse por tarea o por sección (p. ej. un ayudante que solo corrige la sección 2)? ¿Un ayudante ve el dashboard y los datos de todos los estudiantes del curso o solo de los que tiene asignados?

- **Requisitos:** R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el alcance de cada permiso, los filtros de datos por usuario y consideraciones de privacidad de los estudiantes.
- **Opciones:**
  - Permisos a nivel de curso únicamente
  - Permisos acotables por tarea
  - Permisos acotables por sección
  - Visibilidad de datos limitada a lo asignado
- **Estudio de APIs:** §3.4 marca `grading.submit` para ayudante como "(solo asignadas)", insinuando alcance por asignación; no fija alcance por sección ni la visibilidad del dashboard.
- **Fusiona:** P092

### Q-2.1-48 — ¿Los ayudantes necesitan acceso en GitHub y cómo se les aprovisiona?

Si necesitan abrir el código de repos privados para corregir (R2.7.4): ¿se les pide su usuario de GitHub al incorporarlos y la app los agrega automáticamente como miembros de la organización o como colaboradores (`pull`/`triage`) de cada repo de la tarea? ¿Qué pasa si el usuario es inválido, si no acepta la invitación, o si se incorpora al ayudante cuando ya existen repos creados?

- **Requisitos:** R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin acceso a GitHub el ayudante no puede abrir el código que debe corregir; define un flujo de aprovisionamiento de accesos para el equipo docente además del de estudiantes.
- **Opciones:**
  - Miembro de la organización con permiso base de lectura
  - Colaborador `pull`/`triage` por repo
  - Acceso solo mediante la app (sin GitHub directo)
- **Estudio de APIs:** §3.4 menciona revocar el acceso a la org "si se lo dieron" (`DELETE /orgs/{org}/memberships/{username}`) pero no define cómo ni cuándo se otorga.
- **Fusiona:** P093

## Retiro de ayudantes y bajas

### Q-2.1-49 — Al retirar a un ayudante con correcciones asignadas, ¿qué pasa con esas asignaciones, cómo se confirma el retiro y qué se conserva?

¿Las asignaciones pendientes vuelven a "sin asignar" con aviso en la tarea, se reasignan automáticamente (¿a quién, con qué criterio de equidad?) o se bloquea el retiro hasta que el profesor reasigne manualmente? ¿La UI muestra el resumen del impacto ("tiene 12 entregas pendientes en 2 tareas") antes de confirmar? ¿Las calificaciones ya publicadas y las correcciones ya realizadas conservan su autoría en el historial? ¿Se notifica al ayudante retirado? ¿Se le da de baja automáticamente del informe diario?

- **Requisitos:** R2.1.9, R2.6.3, R2.7.1, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el flujo de confirmación de R2.1.9, la regla de negocio sobre asignaciones huérfanas y los efectos en corrección, auditoría y suscripciones.
- **Opciones:**
  - Reasignación automática equitativa
  - Quedan sin asignar con alerta al profesor
  - Bloquear el retiro hasta reasignar manualmente
- **Estudio de APIs:** §3.4 indica "reasignen las entregas que tenía pendientes y revoquen su acceso a la org"; no dice si es automático, qué pasa con lo ya calificado, ni define el flujo de UI.
- **Fusiona:** P017, P043, P095

### Q-2.1-50 — Al retirar a un ayudante, ¿se revoca automáticamente su acceso en GitHub y cómo se manejan los fallos?

¿Se revoca su condición de colaborador de los repos y/o de miembro de la organización? ¿Qué pasa si el ayudante también es miembro de la organización por otras razones (otro curso en la misma org), o si la revocación falla por rate limit o por permisos insuficientes?

- **Requisitos:** R2.1.9
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define los efectos secundarios externos del retiro y su manejo de errores.
- **Opciones:**
  - Revocación automática con reintentos y reporte de fallos
  - Revocación solo de los accesos otorgados por la app, detectados por registro propio
  - Sin revocación automática: instrucción manual al profesor
- **Estudio de APIs:** §3.4 propone `DELETE /orgs/{org}/memberships/{username}` si se le dio acceso a la org.
- **Fusiona:** P096

### Q-2.1-51 — ¿El retiro de un ayudante es borrado lógico o físico, y cómo afecta sesiones, notificaciones, reincorporación y otros cursos?

¿Se conserva el historial y la auditoría (quién asignó y quién corrigió) mediante soft delete con `removed_at`, o se elimina el registro? ¿Se invalidan de inmediato sus sesiones activas? ¿Se le notifica el retiro? ¿Puede reincorporarse el mismo ayudante recuperando su historial? ¿El retiro es por curso (sigue siendo ayudante en otros cursos)?

- **Requisitos:** R2.1.9
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el modelo de membresía, la invalidación de sesión y la trazabilidad exigible en la validación oral.
- **Opciones:**
  - Soft delete por curso con invalidación inmediata de sesión
  - Soft delete sin invalidación inmediata (efectivo al siguiente login)
  - Hard delete del registro de membresía
- **Estudio de APIs:** §4.4 fija la regla "nunca borren filas, marquen `deleted_at`" para datos de Canvas, no explícitamente para el equipo docente.
- **Fusiona:** P097

## Verificación de la configuración (R2.1.6)

### Q-2.1-52 — ¿Cuál es la lista definitiva de ítems del checklist (Canvas y GitHub), cómo se redacta cada uno y qué evidencia se muestra?

El estudio propone 8 ítems (org existe + App instalada; podemos crear repos; podemos invitar colaboradores; el curso de Canvas responde; vemos estudiantes; vemos secciones; vemos tareas; podemos publicar anuncios). ¿Se agregan: permisos de la App suficientes (Administration/Contents/Members); token de Canvas con scopes de escritura (comentar entregas, enviar mensajes, publicar anuncios, calificar); el usuario es teacher del curso; curso de Canvas publicado y vigente; estudiantes > 0; secciones ≥ 1; existe al menos un group set; límite de repos privados/colaboradores del plan de la organización; el profesor es owner de la organización? ¿Cómo se redacta cada ítem en lenguaje no técnico y qué muestra cada uno (nombre, resultado, detalle técnico plegable, acción correctiva con enlace)? ¿Qué evidencia se presenta al profesor (nombre del curso, término, N estudiantes, N secciones, N tareas, nombre del usuario de Canvas que autorizó)?

- **Requisitos:** R2.1.4, R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es literalmente el requisito R2.1.6 y lo que se evalúa como "guía adecuada" el 16-sep; el spec necesita la tabla exacta de chequeos con su llamada, su criterio de éxito y su texto.
- **Opciones:**
  - Adoptar los 8 chequeos propuestos por el estudio
  - Ampliar con los chequeos adicionales de permisos, plan y ownership
  - Reducir a un subconjunto mínimo demostrable
- **Estudio de APIs:** §3.3 propone la tabla de 8 chequeos con su llamada asociada y sugiere renderizar ✅/❌ con botón "reintentar"; no clasifica bloqueante/advertencia ni fija la evidencia mostrada.
- **Fusiona:** P034, P067

### Q-2.1-53 — Para verificar GitHub, ¿se crea y elimina un repositorio temporal en la organización real o solo se inspeccionan los permisos de la instalación?

El chequeo "podemos crear repos" propuesto crea y borra un repo temporal en la organización del profesor: aparece brevemente, queda en el audit log de la org y requiere permiso de borrado. ¿El equipo acepta ese efecto secundario visible y se avisa al profesor antes de ejecutarlo? Si se crea: ¿qué nombre y visibilidad tiene, y qué pasa si la creación funciona pero el borrado falla (queda un repo basura)? ¿La alternativa es inspeccionar solo los permisos de la instalación, aceptando menor certeza, o crear un repo permanente de verificación (p. ej. `.curso-config`) que además sirva de bitácora?

- **Requisitos:** R2.1.5, R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Es el chequeo más fiable del wizard, pero también un efecto secundario sobre la organización real del profesor; cambia el texto del checklist, los permisos que pide la App y la confianza del profesor durante la demo.
- **Opciones:**
  - Crear y borrar un repo temporal, con aviso previo
  - Solo inspección de los permisos de la instalación
  - Repo permanente de verificación reutilizado (p. ej. `.curso-config`)
- **Estudio de APIs:** §3.3 propone explícitamente `POST` de un repo `--verificacion-temporal` (201) y luego `DELETE /repos/{org}/{repo}`; §2.3 y el Apéndice A.1 advierten que los permisos de creación deben verificarse empíricamente.
- **Fusiona:** P035, P080

### Q-2.1-54 — ¿Cómo se verifica que el token de Canvas tiene permisos de escritura sin producir efectos visibles para los estudiantes?

Escrituras a verificar: anuncios, conversaciones, calificaciones y comentarios en entregas. Alternativas: crear un anuncio no publicado y borrarlo; consultar los permisos del usuario en el curso; no verificar y reportar al primer fallo real.

- **Requisitos:** R2.1.6
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Determina si el checklist puede garantizar que 2.6 y 2.7 funcionarán, y si la verificación deja rastros en el Canvas real.
- **Opciones:**
  - Anuncio borrador (`published=false`) creado y eliminado
  - Consulta de permisos del curso (`include[]=permissions`)
  - Sin verificación previa; error contextual al usar
- **Estudio de APIs:** §3.3 lista "Podemos publicar anuncios: permiso del token del profesor" sin indicar una llamada concreta.
- **Fusiona:** P068

### Q-2.1-55 — ¿Qué niveles de resultado tiene el checklist, qué ítems bloquean acciones posteriores y existe "continuar de todos modos"?

¿Los resultados tienen tres niveles (correcto / advertencia / bloqueante) o solo dos? ¿Qué ítems bloquean acciones posteriores (p. ej. no crear tareas hasta que GitHub verifique) y cuáles solo advierten (0 estudiantes en un curso aún sin inscripciones al inicio del semestre, 0 tareas, sin group sets)? ¿Existe una opción "continuar de todos modos" y quién puede usarla?

- **Requisitos:** R2.1.6, R2.3.7
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Convierte el checklist en reglas de negocio verificables (precondiciones por acción) y evita que la UI deje avanzar a un estado donde el worker fallará silenciosamente.
- **Opciones:**
  - Tres niveles (correcto / advertencia / bloqueante) sin escape
  - Tres niveles con "continuar de todos modos" para el profesor
  - Dos niveles (verde/rojo) sin bloqueo de acciones
- **Estudio de APIs:** §3.3 solo distingue verde/rojo y propone 7 chequeos adicionales con ✅/❌; no clasifica severidades.
- **Fusiona:** P005, P036

### Q-2.1-56 — ¿El checklist se muestra progresivamente, con qué timeouts por ítem y con reintento individual?

¿Cada ítem pasa de "verificando…" a su resultado a medida que responde la API, o se muestra todo junto al terminar? ¿Cuál es el timeout por ítem y qué texto se muestra si Canvas o GitHub no responden ("No pudimos contactar a Canvas; reintentar")? ¿Se puede reintentar un solo ítem?

- **Requisitos:** R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Los chequeos implican varias llamadas de red en serie (throttling de Canvas); la percepción de espera y el manejo de timeouts son parte de la usabilidad evaluada.
- **Opciones:**
  - Progresivo con reintento por ítem
  - Resultado global al terminar, con reintento completo
- **Estudio de APIs:** §1.5 indica que las llamadas a Canvas deben ser secuenciales por token; §3.3 no habla de progreso ni timeouts.
- **Fusiona:** P038

### Q-2.1-57 — ¿La verificación es solo bajo demanda o también un health-check periódico con notificación y cambio de estado del curso?

¿Se re-ejecuta desde Configuración del curso ("Verificar conexiones") y además automáticamente en background (p. ej. en cada sync), mostrando "última verificación hace X" y un banner en el curso si algo se rompió (token de Canvas revocado, App desinstalada de la organización, profesor que perdió su rol en Canvas)? ¿Un fallo detectado periódicamente cambia el estado del curso y genera notificación al equipo docente? ¿Cómo y cuándo se entera el equipo docente si la instalación se desinstala a mitad de semestre?

- **Requisitos:** R2.1.6, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define si la salud de las conexiones es un estado persistente y vivo del curso, con su indicador y su notificación, en vez de una pantalla única del onboarding.
- **Opciones:**
  - Solo bajo demanda (botón "verificar / reintentar")
  - Bajo demanda + health-check periódico con banner y notificación
  - Health-check periódico que además cambia el estado del curso y pausa jobs
- **Estudio de APIs:** §3.3 sugiere un botón "reintentar" en la pantalla de verificación; §4.4 recomienda mostrar `last_synced_at` ("datos de Canvas actualizados hace 4 min"). No habla de monitoreo continuo ni de desinstalación.
- **Fusiona:** P037, P085

### Q-2.1-58 — ¿Cuál es la tabla de error → mensaje → acción correctiva para los fallos típicos de vinculación?

Errores a cubrir: en Canvas, 401 token inválido, 403 sin permisos o rate limit, 404 curso no encontrado; en GitHub, 403 permiso faltante, 404 App no instalada, instalación suspendida. ¿Qué mensaje accionable se muestra para cada uno y cada error incluye el enlace directo a la acción correctiva (re-autorizar Canvas, reinstalar la App, pedir el rol al administrador)?

- **Requisitos:** R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Convierte códigos HTTP en guía para el profesor, que es lo evaluado en R2.1.6.
- **Opciones:**
  - Tabla completa error → mensaje → acción con enlaces directos
  - Mensajes genéricos por categoría (credenciales / permisos / no encontrado)
  - Mostrar el error técnico crudo con instrucciones genéricas
- **Estudio de APIs:** §1.5 (403/429 en Canvas) y §2.4 (403/429 en GitHub) definen códigos y política de reintentos, no textos de UI.
- **Fusiona:** P086

### Q-2.1-59 — ¿El profesor puede ENSAYAR la experiencia del estudiante antes de abrir el proceso al curso, y ese ensayo es un paso de la guía de vinculación?

Canvas ofrece "Student View" (Test Student), pero la app lo excluye del roster, así que el profesor nunca vería el ciclo entrega → comentario → invitación → mensaje. ¿Se permite un "modo ensayo" donde el Test Student sí dispara el ciclo contra un repo de prueba que luego se borra, se usa una cuenta de estudiante real de prueba provista por la instancia, se muestra una vista previa estática de cada mensaje, o no se ofrece ensayo? ¿Se incluye en la guía de R2.1.6 un paso "prueba el flujo como estudiante"?

- **Requisitos:** R2.1.6, R2.2.5, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Define si el Test Student tiene un tratamiento especial además de la exclusión, y si se agrega un paso al asistente de configuración.
- **Opciones:**
  - Modo ensayo con Test Student y repo temporal
  - Cuenta de estudiante de prueba real
  - Vista previa estática de los mensajes
  - Sin ensayo
- **Estudio de APIs:** §4.1 y §14 indican filtrar siempre al Test Student para no crearle repo; no contemplan usarlo para ensayar el flujo.
- **Fusiona:** P002

## Casos borde, cambios de vinculación y recuperación

### Q-2.1-60 — ¿Se puede cambiar o desvincular el curso de Canvas o la organización de GitHub cuando ya existen tareas, repos, mapeos y snapshots?

Opciones: prohibir mientras existan tareas; permitir con confirmación dejando los repos anteriores "huérfanos" marcados; migrar transfiriendo los repos a la nueva organización; permitir solo re-autorizar (mismo curso, nuevo token). ¿Qué se conserva y qué se invalida en cada caso (mapeos, snapshots, dashboards, correcciones, entregas vinculadas a assignments del Canvas anterior)? ¿Qué advertencia y confirmación se exige?

- **Requisitos:** R2.1.4, R2.1.5, R2.1.6, R2.3.4, R2.4.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define las restricciones de edición del curso, si la vinculación es inmutable tras crear la primera tarea y el ciclo de vida de los datos dependientes de la vinculación.
- **Opciones:**
  - Bloquear mientras existan tareas o repos
  - Permitir con advertencia, dejando los datos anteriores como huérfanos marcados
  - Permitir con advertencia y borrado de los datos derivados
  - Permitir con transferencia/migración de repos a la nueva organización
  - Permitir solo re-autorizar (mismo curso u organización, nueva credencial)
- **Estudio de APIs:** No lo aborda; §3.2 solo indica guardar `canvas_course_id`.
- **Fusiona:** P015, P066, P079

### Q-2.1-61 — ¿Cómo se detecta, se comunica y se recupera una "vinculación rota" con Canvas o con GitHub?

Situaciones: la GitHub App es desinstalada o suspendida en la organización; el profesor revoca el token de Canvas, cambia su contraseña, pierde su enrollment de Teacher, o su `refresh_token` deja de funcionar. ¿Cómo se detecta (webhook `installation` con acción `deleted`/`suspend`, fallo al pedir un installation token, 401/403 en los jobs)? ¿Qué estado toma el curso ("vinculación rota")? ¿Qué operaciones se pausan (worker de aprovisionamiento, sync, snapshots, notificaciones, informe diario) y cuáles siguen funcionando (ver datos ya sincronizados)? ¿Qué ve cada rol (banner "Reconecta Canvas" con un clic de reautorización para el profesor; aviso "pide al profesor X que reconecte" para los ayudantes; botón "reinstalar" para GitHub)? ¿A quién se avisa y por qué canal (banner, email)? ¿Puede otro profesor del curso (R2.1.7) reconectar con su propio token, y cómo se re-vincula sin perder repos, mapeos ni snapshots?

- **Requisitos:** R2.1.4, R2.1.5, R2.1.6, R2.1.7, R2.3.10, R2.4.5, R2.6.1, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define el estado de salud del curso, su UI por rol, la degradación controlada de los cron jobs y el flujo de recuperación; sin esto, los jobs fallan en silencio y un curso puede quedar sin sync ni informes sin que nadie se entere.
- **Opciones:**
  - Detección por webhooks + 401/403 en jobs, con estado explícito y notificación
  - Detección solo reactiva (al fallar un job) con banner en el curso
  - Detección solo en la verificación bajo demanda
  - Re-autorización posible por cualquier profesor del curso
  - Re-autorización exclusiva del profesor vinculador original
- **Estudio de APIs:** §1.1 subraya que el `refresh_token` es crítico para los jobs nocturnos (2.6.1, 2.4.5) y explica expiración/refresh; §3.4 propone la opción A (token del profesor) con B como fallback; §3.3 define el checklist de verificación; §8.1 lista los eventos `push`, `create`, `delete`, `repository`, `member`, `member_invite` pero no el evento `installation`. No define detección de pérdida de acceso, UI degradada ni recuperación.
- **Fusiona:** P013, P042, P063, P078

### Q-2.1-62 — ¿Qué hace la app si el curso de Canvas vinculado cambia de estado, el término concluye o el profesor pierde su enrollment?

Casos: el `workflow_state` del curso pasa a `completed` o `deleted`, el término concluye, o el profesor pierde su enrollment en Canvas. ¿Cómo se detecta (en el sync periódico) y qué se muestra y se bloquea (banner, escrituras deshabilitadas)?

- **Requisitos:** R2.1.4, R2.1.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Caso borde "el curso de Canvas se elimina o concluye a mitad de camino"; define detección y degradación controlada en vez de errores opacos.
- **Opciones:**
  - Detección en el sync con banner y bloqueo de escrituras
  - Detección con advertencia sin bloquear
  - Sin detección específica (error al primer fallo)
- **Estudio de APIs:** §3.2 lista `workflow_state` entre los campos relevantes pero no define ninguna reacción.
- **Fusiona:** P069

### Q-2.1-63 — ¿Cómo reconoce el estudiante que la invitación de GitHub es legítima y quién configura el perfil de la organización?

Verificar quién aparece como invitador en el correo y en github.com cuando la GitHub App agrega colaboradores (¿`<app>[bot]`, el nombre de la organización, o nadie?). Y decidir: (a) si la organización tendrá un perfil identificable (nombre del curso o de la universidad, descripción, avatar, email de contacto, dominio verificado) antes de la primera invitación; (b) si el mensaje de Canvas menciona el nombre exacto de la organización, el nombre del repo y quién figurará como invitador, para que el estudiante pueda cotejar; (c) quién es responsable de configurar ese perfil (el equipo o el owner de la organización).

- **Requisitos:** R2.1.5, R2.3.9, R2.3.12
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Un estudiante que descarta la invitación por desconfianza queda con la invitación pendiente indefinidamente; fija el contenido del mensaje de R2.3.12 y una tarea de configuración de la organización previa a la demo.
- **Opciones:**
  - Perfil completo de la organización configurado antes de la primera invitación, con mensaje de Canvas que permite cotejar
  - Solo mensaje explicativo en Canvas, sin requisitos sobre el perfil de la organización
  - Sin medidas específicas
- **Estudio de APIs:** §5.4 explica que `PUT` collaborators devuelve 201 y que el estudiante debe aceptar por email; no aborda quién figura como invitador ni la legitimidad percibida de la organización.
- **Fusiona:** P001

## Ya respondidas por el enunciado

Ninguna de las 98 preguntas de entrada fue marcada como YA_RESPONDIDA en la etapa de verificación: los 98 veredictos son ABIERTA o ABIERTA/BLOQUEA. No hay, por tanto, preguntas apartadas con cita del enunciado en esta área.
