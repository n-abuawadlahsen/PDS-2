# Preguntas de alcance — Area 2.6

60 preguntas finales, fusionadas desde 73 de entrada (13 absorbidas por fusion), 10 bloqueantes para la parcial.

## Decisiones estructurales: emisor, canales y viabilidad tecnica

### Q-2.6-01 — ¿Desde qué cuenta de Canvas se envían los mensajes directos y los anuncios de la app: siempre con el token del profesor que vinculó el curso, con el token propio de quien dispara la acción cuando lo tiene, o un esquema híbrido? Con varios profesores (R2.1.7), ¿quién es el emisor «del curso» y es configurable? ¿Qué ocurre si el profesor vinculador revoca su token, sale del curso o pierde el rol teacher en Canvas, y cómo afecta eso a las comunicaciones automáticas que se disparan de madrugada sin nadie conectado? ¿La UI advierte «se enviará como Profesor X» antes de enviar?

- **Requisitos:** R2.6.5, R2.6.6, R2.6.7, R2.1.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Los mensajes aparecen en Canvas firmados por esa persona y los estudiantes le responderán a ella. Define el modelo de tokens, los mensajes de error, una advertencia de UI y la viabilidad de comunicaciones automáticas nocturnas.
- **Opciones:**
  - Siempre el token del profesor vinculador
  - Token del usuario que dispara la acción
  - Híbrido: el usuario si tiene token válido, si no el del profesor vinculador
  - Emisor configurable por curso entre los profesores
- **Estudio de APIs:** §3.4 propone A (token del vinculador) como default y B (token del actor) como fallback, y sugiere mostrarlo en la UI; §1.1 exige guardar el refresh token para jobs que corren sin el profesor conectado.
- **Fusiona:** P504

### Q-2.6-02 — ¿Se verificó que los canales de Canvas que la app usará están habilitados y son VISIBLES PARA LOS ESTUDIANTES en la instancia que se usará (institucional o Free-for-Teacher)? Casos a comprobar: bandeja de Conversations habilitada para estudiantes y sin restricciones institucionales sobre quién puede escribir a quién; comentarios de entrega visibles para el estudiante en el tipo de assignment elegido; anuncios habilitados y no restringidos por las fechas de participación del curso (restrict_student_past_view / participación por término); notificaciones por correo activas por defecto. ¿Qué canal de respaldo se adopta si alguno no está disponible (solo comentario en la entrega, solo anuncio, o exportar la lista estudiante↔repositorio para que el profesor la distribuya)? ¿Se incorpora este chequeo como ítem del checklist de vinculación (R2.1.6), distinto del chequeo de permisos del token?

- **Requisitos:** R2.6.5, R2.6.6, R2.3.12, R2.1.6
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** R2.3.12 y R2.6.5 dependen por completo de que el canal exista del lado del estudiante; un token con permisos correctos puede publicar mensajes que el estudiante nunca puede leer. Determina el diseño del mecanismo de enrolamiento y si hace falta un plan B antes del 16-sep.
- **Opciones:**
  - Conversations como canal principal, comentario en la entrega como respaldo
  - Solo comentario en la entrega (contextual, siempre visible)
  - Anuncio + comentario, sin mensajes individuales
  - Exportación manual para el profesor si ningún canal automático es viable
- **Estudio de APIs:** §3.3 propone un checklist que incluye «podemos publicar anuncios», pero mide permisos del token del profesor, no si el canal está habilitado y es visible para los estudiantes en esa instancia; §9.2 y §9.3 documentan los endpoints sin mencionar restricciones institucionales de visibilidad.
- **Fusiona:** N023

### Q-2.6-03 — ¿Cuáles son las restricciones de formato y longitud de cada canal de Canvas, y qué plantilla se define para cada uno? En concreto: el `body` de POST /conversations, ¿acepta HTML o solo texto plano, Canvas auto-enlaza las URLs, respeta saltos de línea y listas, y cuál es su longitud máxima?; los comentarios de submission (`comment[text_comment]`), ¿renderizan HTML y enlaces?; los anuncios aceptan HTML. ¿Se define una plantilla por canal (texto plano vs HTML) o una sola plantilla compartida sin que se muestren etiquetas crudas al estudiante, y se prueba que el enlace al repositorio, los pasos para aceptar la invitación y las fechas sean legibles y clicables en la app web y móvil de Canvas del estudiante?

- **Requisitos:** R2.6.5, R2.3.12, R2.6.6, R2.7.6
- **Tipo:** investigable_en_docs · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define el motor de plantillas (texto vs HTML por canal) y las pruebas de renderizado en Canvas; un mensaje con HTML crudo o una URL no clicable degrada la usabilidad del enrolamiento y de R2.3.12.
- **Opciones:**
  - Una plantilla por canal (texto plano para Conversations, HTML para anuncios y comentarios)
  - Una sola plantilla en texto plano para todos los canales
  - Plantilla única en HTML con degradación automática a texto
- **Estudio de APIs:** §9.3 muestra `body` en texto plano con la URL; §9.2 indica que `message` de anuncios acepta HTML; §5.7 escribe el comentario con URL sin indicar el formato soportado; no aclara el formato ni la longitud máxima de Conversations.
- **Fusiona:** P476, P479

### Q-2.6-04 — ¿Cuántos mensajes individuales personalizados por hora tolera el throttling de Canvas con un solo token (60 estudiantes × 1 POST secuencial)? ¿Existe algún límite diario de conversaciones nuevas para un usuario teacher en la instancia usada (Free-for-Teacher o institucional)? ¿Funciona `bulk_message`? ¿El token del profesor puede enviar a `recipients[]=course_X` o a una sección completa (permiso «enviar mensajes a toda la clase»)?

- **Requisitos:** R2.6.5, R2.6.7
- **Tipo:** verificar_empiricamente · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Determina si el envío masivo de «repositorio disponible» puede completarse en minutos durante la demo o requiere encolado con pausas mayores, y si el mensaje masivo por sección es viable como alternativa al anuncio.
- **Opciones:**
  - Envío secuencial uno a uno con backoff
  - Envío masivo con `bulk_message` o `recipients[]=course_X`
  - Cola con pausas y ventana de envío ampliada
- **Estudio de APIs:** §1.5 describe leaky bucket por token y una request simultánea; §9.3 documenta `recipients` con prefijo course_/group_; el Apéndice A.4 pide probar `bulk_message` en la instancia real.
- **Fusiona:** P510

### Q-2.6-05 — ¿Qué permisos concretos de R2.1.8 gobiernan cada acción de comunicación: activar o desactivar toggles, enviar mensaje manual, publicar anuncio, editar plantillas, ver el log de comunicaciones, suscribirse al informe? ¿Un ayudante puede enviar un mensaje a un estudiante que no tiene asignado para corregir?

- **Requisitos:** R2.6.3, R2.6.5, R2.6.6, R2.6.7, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cruza R2.1.8 con toda la sección 2.6 y define la matriz de permisos que debe documentarse.
- **Opciones:**
  - Un permiso único de comunicación para todas las acciones
  - Permisos separados por acción (toggles, envío, anuncios, plantillas, log)
  - Restricción adicional: el ayudante solo comunica con los estudiantes que tiene asignados
- **Estudio de APIs:** §3.4 propone `student.communicate` (profesor y ayudante jefe) y `report.subscribe` (todos los roles).
- **Fusiona:** P535

## Informe docente diario: cuando existe y que cubre

### Q-2.6-06 — ¿Exactamente entre qué instantes una tarea se considera «activa» para efectos del informe diario? Inicio: creación de la tarea en la app, `unlock_at` de la primera entrega, publicación del assignment en Canvas, o creación del primer repositorio. Fin: `due_at` base de la última entrega, la fecha efectiva más tardía incluyendo overrides de sección y extensiones individuales, `lock_at`, N días después del cierre para cubrir la corrección, o hasta que la última entrega esté calificada. Además: ¿cuenta como activa una tarea cuya assignment está sin publicar (`published=false`), cuyo curso de Canvas está en `workflow_state` completed/concluded, que aún no tiene ningún repositorio creado, o que el profesor «archivó» o desvinculó en la app? ¿Existe un estado explícito «archivada/pausada» que excluya la tarea del informe sin borrarla? Y si un curso no tiene tareas activas pero sí problemas pendientes (repositorios en error, invitaciones sin aceptar), ¿igual no hay informe?

- **Requisitos:** R2.6.1, R2.6.2, R2.6.3, R2.6.4, R2.4.1, R2.4.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.6.1 hace depender la existencia misma del informe de esta definición: decide cuándo se envían correos, si una extensión individual mantiene «activa» la tarea para todo el curso, si el informe sigue llegando durante la corrección, si una tarea recién creada sin repositorios ya genera informe, y cómo se prueba en la revisión.
- **Opciones:**
  - Inicio en la creación de la tarea en la app / en `unlock_at` / en la publicación del assignment / en la creación del primer repositorio
  - Fin en el `due_at` base / en la fecha efectiva más tardía con overrides y extensiones / en `lock_at` / N días tras el cierre / al calificar la última entrega
  - Marcado manual de tarea activa/archivada por el profesor
  - Excluir tareas no publicadas y cursos concluidos, incluirlas, o hacerlo configurable
- **Estudio de APIs:** §9.1 dice «tareas con alguna entrega cuyo período esté vigente» sin definir «período»; §7.3 define fecha efectiva por estudiante con precedencia ADHOC > grupo > sección > base; §5.1 sugiere «no creen repos para tareas no publicadas»; §3.2 lista el `workflow_state` del curso, sin relacionar ninguno de los dos con el informe.
- **Fusiona:** P477, P482, P483

### Q-2.6-07 — ¿En qué días y a qué hora se genera y envía el informe diario: todos los días del calendario (incluidos sábados, domingos, feriados y semanas de receso) mientras haya tareas activas, solo días hábiles, o configurable por curso? Si se omiten días, ¿el siguiente informe cubre el período acumulado y así se indica? ¿A qué hora local se envía, en qué zona horaria se fija (America/Santiago con horario de verano, o UTC fijo), y es esa hora una constante global del sistema o configurable por curso o por suscriptor? ¿Qué pasa el día del cambio de horario (Chile pasa de UTC-4 a UTC-3 el primer fin de semana de septiembre, entre la parcial y la final)?

- **Requisitos:** R2.6.1, R2.6.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el cron del job, la ventana de datos, el manejo de DST y el criterio de aceptación «el informe llega antes de las HH:MM hora de Chile»; evita correos irrelevantes en fin de semana o, al revés, la pérdida de alertas de sábado y domingo antes de un cierre el lunes. Si es configurable, agrega un campo al curso o al perfil y una UI.
- **Opciones:**
  - Todos los días del calendario
  - Solo días hábiles con ventana acumulada
  - Días configurables por curso
  - 07:00 fijo America/Santiago
  - Hora configurable por curso
  - Hora configurable por suscriptor
  - Hora fija en UTC
- **Estudio de APIs:** §9.1 propone un CRON diario a las 07:00 America/Santiago sin distinguir días de la semana; §14 «Zonas horarias» recomienda guardar UTC y convertir al renderizar; no aborda configurabilidad ni el día del cambio de horario.
- **Fusiona:** P480, P481

### Q-2.6-08 — Si un profesor o ayudante participa en varios cursos con tareas activas, ¿recibe un correo por curso o un único correo consolidado con todos sus cursos? Dentro de un curso con varias tareas activas, ¿un informe por curso con una sección por tarea, o un informe por tarea? ¿En qué orden se listan las tareas y las alertas (urgencia, fecha de cierre, alfabético)?

- **Requisitos:** R2.6.1, R2.6.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el asunto del correo, la estructura de la plantilla, la clave de idempotencia (curso+fecha vs usuario+fecha) y la granularidad de la suscripción.
- **Opciones:**
  - Un correo por curso
  - Un correo consolidado por usuario con todos sus cursos
  - Un informe por tarea
  - Configurable por suscriptor
- **Estudio de APIs:** §9.1 itera «para cada curso» y envía a los suscritos, lo que implica un correo por curso; no considera consolidación por usuario ni orden de listado.
- **Fusiona:** P484

### Q-2.6-09 — ¿Cuál es la lista cerrada de «situaciones que requieren atención» incluidas en el informe: repositorios sin actividad en N días, estudiantes con 0 commits, repositorios en ERROR o PENDING_MAPPING, invitaciones de GitHub sin aceptar, estudiantes sin usuario GitHub, estudiantes sin grupo en tarea grupal, entregas que vencen en menos de 48 h, snapshots capturados el día anterior (incluyendo NO_COMMITS), cambios de fecha detectados en Canvas, commits sin atribuir, comunicaciones automáticas fallidas, token de Canvas por expirar, otros? ¿Se incluye una sección «positiva» (commits de las últimas 24 h, repositorios activos sobre el total)?

- **Requisitos:** R2.6.2, R2.6.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es el contenido del informe: cada ítem implica una regla, una consulta sobre la base de datos y una fila en la plantilla, y define qué se considera cumplimiento de R2.6.2, cuya lista en el enunciado es ejemplificativa («tales como»).
- **Opciones:**
  - Lista cerrada fija en el código
  - Lista cerrada con secciones activables por curso
  - Incluir sección positiva de resumen
  - Solo secciones de alerta, sin resumen positivo
- **Estudio de APIs:** §9.1 propone 7 secciones (sin actividad N días, 0 commits, ERROR/PENDING, invitaciones, sin mapeo, vencen en menos de 48 h, resumen de commits de 24 h); §7.5 sugiere que NO_COMMITS «es un dato valioso para el informe».
- **Fusiona:** P486

### Q-2.6-10 — ¿Cuántos días sin commits convierten un repositorio en «sin actividad reciente» para el informe? «Estudiante sin participación», ¿se mide desde la creación del repositorio, dentro del período de la entrega vigente (desde el cierre de la entrega anterior), o en las últimas N horas? ¿Los umbrales son globales, por curso, por tarea o por entrega, y son exactamente los mismos que usa el dashboard (R2.5.3, R2.5.4)?

- **Requisitos:** R2.6.2, R2.5.3, R2.5.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija las reglas de negocio que producen cada alerta; sin valores concretos no hay criterio de aceptación verificable, y umbrales distintos entre dashboard e informe producen inconsistencias visibles en la revisión.
- **Opciones:**
  - Umbral global fijo en el código
  - Umbral configurable por curso
  - Umbral configurable por tarea o por entrega
  - Umbrales compartidos con el dashboard vs independientes
- **Estudio de APIs:** §8.5 propone «X días, configurable» para R2.5.3 y «0 commits atribuidos» para R2.5.4; §9.1 usa «N días» sin fijar valor ni alcance.
- **Fusiona:** P485

### Q-2.6-11 — Cuando una entrega tiene fechas distintas por sección o extensiones individuales, ¿el informe lista cada fecha efectiva (por sección y cada extensión), solo la fecha base, o la más próxima? ¿La alerta «próxima a vencer» se evalúa según la fecha efectiva de cada estudiante o grupo? ¿Se nombran en el informe los estudiantes con extensión?

- **Requisitos:** R2.6.1, R2.6.2, R2.4.2, R2.4.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la consulta de fechas para el informe y evita reportar como «vencida» una entrega que para algunos alumnos sigue abierta.
- **Opciones:**
  - Listar todas las fechas efectivas por sección y extensión
  - Listar solo la fecha base
  - Listar la fecha más próxima con indicador de heterogeneidad
  - Nombrar a los estudiantes con extensión vs mostrar solo el conteo
- **Estudio de APIs:** §7.3 recomienda «mostrar en la UI que ese repo tiene fechas heterogéneas»; §9.1 no lo aplica al informe.
- **Fusiona:** P487

### Q-2.6-12 — Si hay tareas activas pero ninguna situación requiere atención, ¿se envía igual un informe «sin novedades» con el resumen, o se omite el envío y el historial registra «generado sin alertas»?

- **Requisitos:** R2.6.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.6.1 solo fija que sin tareas activas no hay informe; el caso «activas pero sin alertas» cambia la expectativa del docente (silencio = todo bien vs silencio = falla del sistema).
- **Opciones:**
  - Enviar siempre que haya tareas activas, incluso sin alertas
  - No enviar si no hay alertas; registrar en el historial
  - Enviar un resumen breve sin secciones de alerta
- **Estudio de APIs:** §9.1 no lo aborda.
- **Fusiona:** P488

### Q-2.6-13 — ¿El informe que recibe un ayudante contiene la misma información que el del profesor, o se filtra a las entregas y estudiantes que tiene asignados para corregir (R2.7.1) y a lo que su permiso RBAC le permite ver? ¿Un ayudante cuyo rol no puede ver repositorios recibe informe?

- **Requisitos:** R2.6.1, R2.6.2, R2.1.8, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Obliga a generar variantes por destinatario (o no), y afecta rendimiento, privacidad y la definición de los permisos de R2.1.8.
- **Opciones:**
  - Mismo contenido para todos los suscritos
  - Contenido filtrado por asignación de corrección
  - Contenido filtrado por permiso RBAC
  - No enviar informe a roles sin acceso a repositorios
- **Estudio de APIs:** §3.4 propone el permiso `report.subscribe` para todos los roles; no discute filtrado del contenido por rol.
- **Fusiona:** P496

## Informe diario: correo, formato e infraestructura de envio

### Q-2.6-14 — ¿El informe se envía como HTML con alternativa en texto plano (multipart), solo texto, o resumen + enlace a la versión web dentro de la app? ¿Debe ser legible en móvil? ¿Incluye enlaces profundos a la tarea, el repositorio y el estudiante en la app y en GitHub? ¿Incluye nombres completos y usuarios de GitHub en el cuerpo del correo (fuera de la app) o solo conteos con enlace? Y en cuanto a presentación: ¿idioma de todas las comunicaciones (español de Chile), formato de fechas y horas (por ejemplo «mié 16-sep 16:30, hora de Chile»), nombre visible del remitente («Nombre de la app» vs «Curso ICC4201»), y direcciones From y Reply-To (noreply, correo del equipo, correo del profesor del curso)?

- **Requisitos:** R2.6.4, R2.6.5, R2.6.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la plantilla, la compatibilidad con clientes de correo, la política de privacidad del contenido que sale de la app por email, y evita que los docentes respondan a una casilla que nadie lee.
- **Opciones:**
  - HTML multipart con alternativa en texto plano
  - Solo texto plano
  - Resumen breve + enlace a la versión web del informe
  - Datos personales completos en el correo vs solo conteos con enlace
  - Reply-To a noreply, al equipo de desarrollo, o al profesor del curso
- **Estudio de APIs:** §9.1 recomienda «HTML + texto plano» y «resumen + link» a una página web del informe; sobre idioma, formato de fechas y remitente, no lo aborda.
- **Fusiona:** P491, P492

### Q-2.6-15 — ¿Qué servicio de email se usa (SMTP de Gmail, Resend, SendGrid, Mailgun u otro), con qué dominio remitente y qué configuración SPF/DKIM para que el informe llegue al gmail de los revisores y no a spam? ¿La cuota diaria del plan gratuito alcanza para el curso demo más los revisores? ¿Quién crea la cuenta y custodia la API key?

- **Requisitos:** R2.6.3, R2.6.4
- **Tipo:** dependencia_externa · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin un remitente confiable el revisor no recibirá el informe y R2.6.4 quedará «no accesible en el uso».
- **Opciones:**
  - SMTP de Gmail con la cuenta del equipo
  - Proveedor transaccional (Resend, SendGrid, Mailgun) con dominio propio
  - Proveedor transaccional con dominio compartido del proveedor
- **Estudio de APIs:** §9.1 lista SendGrid/Resend/Mailgun/SMTP Gmail y recomienda registrar los envíos; no aborda dominio remitente, SPF/DKIM ni cuotas.
- **Fusiona:** P473

### Q-2.6-16 — Los enlaces profundos del informe diario por correo (y de cualquier aviso de asignación de correcciones) llegan a un usuario que casi nunca tendrá sesión iniciada. ¿Se preserva la URL de destino a través del login con Google (parámetro de retorno firmado y validado contra una lista de rutas propias) o se aterriza siempre en la home obligando a re-navegar? ¿Qué se muestra si al llegar el destino ya no existe (tarea eliminada, entrega desvinculada, repositorio huérfano), si el usuario perdió el permiso, o si nunca perteneció a ese curso: respuesta genérica de «no disponible» para no revelar la existencia del recurso, o mensaje específico? ¿Los enlaces del correo llevan algún identificador para diagnosticar entregabilidad, y se garantiza que no viajan tokens de sesión en la URL?

- **Requisitos:** R2.6.4, R2.6.1, R2.1.2, R2.7.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Determina si el informe diario es realmente accionable (R2.6.4 con un clic) o solo informativo, y produce criterios de aceptación concretos de autorización y de manejo de recursos inexistentes, que además son puntos de revisión de seguridad.
- **Opciones:**
  - Login con retorno a la URL original (`return_to` firmado)
  - Aterrizaje siempre en la home del curso
  - Página pública del informe con token firmado, sin login, y enlaces internos que sí requieren login
- **Estudio de APIs:** §9.1 recomienda guardar cada informe como página web accesible y poner en el correo «el resumen + link», pero no aborda el retorno tras el login, ni el destino inexistente, ni la comprobación de permisos al llegar.
- **Fusiona:** N025

### Q-2.6-17 — Si el proveedor de email rechaza o falla el envío (5xx, cuota agotada, dirección inválida, bounce), ¿cuántos reintentos y con qué backoff, cuándo se marca como fallido definitivamente, se muestra el fallo en la app (banner en el curso, historial) y se notifica a alguien (profesor del curso, administrador)? ¿Los bounces se procesan vía webhook del proveedor o se ignoran?

- **Requisitos:** R2.6.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la máquina de estados del envío, el contenido del historial y la observabilidad mínima exigible.
- **Opciones:**
  - Sin reintentos, solo registro del fallo
  - N reintentos con backoff exponencial y estado final
  - Procesar bounces por webhook y desactivar la dirección
  - Notificar el fallo al profesor del curso o al administrador
- **Estudio de APIs:** §9.1 pide «registro de envíos (sent_at, status) para poder demostrarlo»; no define reintentos ni bounces.
- **Fusiona:** P493

## Suscripcion al informe diario

### Q-2.6-18 — ¿La suscripción al informe es por curso (un toggle por cada curso donde participo), global por usuario, o ambas (global con excepciones por curso)?

- **Requisitos:** R2.6.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la tabla de suscripciones, la UI y la semántica del enlace de baja del correo.
- **Opciones:**
  - Por curso
  - Global por usuario
  - Global con excepciones por curso
- **Estudio de APIs:** §9.1 propone `report_subscriptions(user_id, course_id, enabled)`, es decir, por curso.
- **Fusiona:** P498

### Q-2.6-19 — Cuando un profesor crea un curso, o cuando se incorpora un co-profesor (R2.1.7) o un ayudante (R2.1.8), ¿queda suscrito por defecto (opt-out) o debe suscribirse (opt-in)? ¿Se le informa del estado en la invitación o en su primer acceso?

- **Requisitos:** R2.6.3, R2.1.7, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cambia el comportamiento observable en la demo, el volumen de correo y el texto de la invitación.
- **Opciones:**
  - Suscrito por defecto (opt-out)
  - No suscrito por defecto (opt-in)
  - Profesores opt-out, ayudantes opt-in
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P499

### Q-2.6-20 — ¿Dónde vive el control de suscripción al informe: en el perfil del usuario, en la página del curso, en la vista «Equipo docente», o en varios de ellos? ¿El correo incluye un enlace «darse de baja» de un clic sin iniciar sesión con token firmado y, si es así, el token expira, da de baja solo de ese curso o de todo, pide confirmación en una página o es inmediato, y permite volver a suscribirse desde el mismo enlace? ¿Se muestra al usuario dentro de la app la hora de envío y el estado del último envío (enviado / falló / sin informe porque no hay tareas activas)?

- **Requisitos:** R2.6.3, R2.6.1, R2.6.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija el flujo de UI, los requisitos de seguridad del token de baja y los criterios de aceptación de R2.6.3, además de cómo el suscriptor comprueba que el sistema funcionó sin depender de su bandeja de correo.
- **Opciones:**
  - Toggle solo en el perfil del usuario
  - Toggle solo en la página del curso o en «Equipo docente»
  - Toggle en ambos lugares
  - Enlace de baja con token firmado sin login (con o sin página de confirmación)
  - Sin enlace de baja en el correo; solo dentro de la app
- **Estudio de APIs:** §9.1 recomienda un toggle en la UI y un link de baja con token firmado sin login, y guardar cada informe como página web accesible (`/courses/:id/reports/YYYY-MM-DD`).
- **Fusiona:** P500, P539

### Q-2.6-21 — ¿Puede un profesor ver y modificar el estado de suscripción de otros miembros del curso (desuscribir a un ayudante, suscribir a todos), o la suscripción es estrictamente individual y autogestionada, como sugiere el «individualmente» de R2.6.3?

- **Requisitos:** R2.6.3, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define permisos y si existe una vista de administración de suscripciones en el curso.
- **Opciones:**
  - Estrictamente self-service
  - El profesor puede ver el estado pero no modificarlo
  - El profesor puede administrar las suscripciones del curso
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P503

### Q-2.6-22 — ¿El informe se envía siempre al correo gmail.com de registro (R2.1.2) o el usuario puede configurar otra dirección (por ejemplo, institucional)? Si se permite, ¿se verifica la dirección antes de usarla?

- **Requisitos:** R2.6.3, R2.6.4, R2.1.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cambia el modelo de usuario y agrega un flujo de verificación de correo.
- **Opciones:**
  - Siempre a la dirección de registro
  - Dirección alternativa configurable con verificación
  - Dirección alternativa configurable sin verificación
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P502

### Q-2.6-23 — Al retirar a un ayudante del curso (R2.1.9) o al eliminar o archivar el curso, ¿se elimina o se desactiva su suscripción automáticamente, y qué pasa con un informe ya encolado para él? Si vuelve a incorporarse, ¿recupera su estado anterior de suscripción?

- **Requisitos:** R2.6.3, R2.1.9
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Evita filtrar información a personas que ya no pertenecen al curso; define efectos en cascada del retiro.
- **Opciones:**
  - Eliminar la suscripción y descartar lo encolado
  - Desactivar la suscripción conservando el registro para una eventual reincorporación
  - Conservar la suscripción hasta que el usuario la cancele
- **Estudio de APIs:** §3.4 menciona reasignar entregas y revocar acceso de GitHub al retirar un ayudante; no menciona suscripciones.
- **Fusiona:** P501

## Informe diario: persistencia, ejecucion manual y recuperacion

### Q-2.6-24 — ¿Cada informe generado se guarda como documento inmutable consultable en la app (por ejemplo `/courses/:id/reports/:fecha`), o se regenera bajo demanda con datos actuales? ¿Quién puede verlo (solo los suscritos, cualquier miembro del curso, según permiso RBAC), cuánto tiempo se retiene, y se muestra el estado de envío por destinatario?

- **Requisitos:** R2.6.1, R2.6.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es la única forma de demostrar R2.6.1–R2.6.4 en la revisión (Consideraciones §4: lo no accesible en el uso no se considera cumplido); define un modelo de datos y una vista.
- **Opciones:**
  - Documento inmutable persistido con historial por fecha
  - Regeneración bajo demanda con datos actuales
  - Persistencia solo del resumen y del estado de envío
- **Estudio de APIs:** §9.1 recomienda guardar cada informe como página web y enlazarla desde el correo.
- **Fusiona:** P494

### Q-2.6-25 — ¿Existe una acción «generar informe ahora» o «enviarme el informe de hoy» para pruebas y para la demo? Si existe, ¿produce un informe adicional marcado como manual o reemplaza el del día, qué rol puede dispararla, y se envía solo a quien lo pide o a todos los suscritos?

- **Requisitos:** R2.6.1, R2.6.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Sin ella el informe diario no puede demostrarse en la revisión presencial; además interactúa con la regla de unicidad del informe.
- **Opciones:**
  - No existe generación manual
  - Genera un informe adicional marcado como manual, solo para quien lo pide
  - Genera un informe adicional manual para todos los suscritos
  - Reemplaza el informe del día
- **Estudio de APIs:** No lo aborda directamente; §13 recomienda dejar visible en la demo lo que se evalúa.
- **Fusiona:** P495

### Q-2.6-26 — ¿La ventana de datos del informe es «últimas 24 h» fijas o «desde el último informe enviado con éxito» (si el de ayer falló, el de hoy cubre 48 h)? Si el servidor estuvo caído a la hora programada, ¿se genera el informe atrasado al levantarse (fechado ayer), se envía al momento con fecha de hoy, o se omite ese día? ¿Cuál es la regla de unicidad del informe (uno por curso por día calendario local) y qué ocurre si el cron se ejecuta dos veces (reinicio del worker, dos instancias del hosting): se reenvía, se ignora, o se regenera solo si cambió el contenido?

- **Requisitos:** R2.6.1, R2.6.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si el job «barre pendientes» o «dispara a hora fija», la clave de unicidad en la base de datos, lo que muestra el historial tras una caída del hosting gratuito y el criterio de aceptación «nunca dos correos el mismo día al mismo destinatario».
- **Opciones:**
  - Ventana fija de 24 h, se omite el día perdido
  - Ventana «desde el último envío exitoso», con barrido de pendientes al levantar
  - Unicidad por curso + día calendario, ignorando ejecuciones repetidas
  - Regenerar y reenviar solo si el contenido cambió
- **Estudio de APIs:** §7.5 recomienda para snapshots «barrer todo lo vencido y no capturado, no disparar a las 16:30», sin extender el criterio al informe; §9.4 propone un outbox con constraint único para las comunicaciones a estudiantes, pero §9.1 no lo hace explícito para el informe.
- **Fusiona:** P489, P490

### Q-2.6-27 — Si al generar el informe el refresh token de Canvas del profesor está revocado o expirado, la última sincronización falló, o la GitHub App fue desinstalada de la organización, ¿el informe se genera con los datos en base de datos indicando «datos actualizados hace X h», se omite, o se convierte en un informe de alerta «reconecte Canvas/GitHub»?

- **Requisitos:** R2.6.1, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el comportamiento ante dependencias caídas, situación probable durante las dos semanas de disponibilidad posteriores a la entrega.
- **Opciones:**
  - Generar con datos en base de datos y marcar la antigüedad
  - Omitir el informe
  - Enviar un informe de alerta pidiendo reconectar
- **Estudio de APIs:** §1.1 advierte que sin refresh token guardado el informe no funciona de madrugada; §4.4 sugiere mostrar `last_synced_at`; no define el comportamiento del informe ante fallo.
- **Fusiona:** P497

## Comunicaciones automaticas a estudiantes: catalogo y configuracion

### Q-2.6-28 — ¿Cuál es la lista cerrada de eventos que generan comunicación automática y su canal: repositorio disponible, invitación pendiente sin aceptar tras N días, falta usuario de GitHub (recordatorio), X horas antes de una entrega, repositorio sin commits cerca del cierre, cambio de fecha, entrega cerrada o snapshot capturado, nota publicada, estudiante agregado a un grupo tardíamente, otros? ¿Cuáles deben estar operativos para la parcial y cuáles solo para la final?

- **Requisitos:** R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Cada evento es un disparador, una plantilla, un toggle y un caso de prueba; el enunciado usa «tales como», por lo que la lista es decisión del equipo.
- **Opciones:**
  - Lista mínima para la parcial (repositorio disponible, falta usuario de GitHub) y el resto para la final
  - Lista completa desde la parcial
  - Lista cerrada fija vs extensible por configuración
- **Estudio de APIs:** §9.4 propone 6 eventos con canal y flag: `notify_repo_ready`, `notify_missing_mapping`, `notify_deadline_48h`, `notify_no_activity`, `notify_date_change`, `notify_graded`.
- **Fusiona:** P521

### Q-2.6-29 — ¿Los toggles de comunicaciones son por tarea con valores por defecto ON u OFF al crear la tarea? ¿Se heredan de una configuración a nivel de curso? ¿Pueden variar por entrega dentro de una tarea (recordatorio para la parcial pero no para la final)? ¿Qué roles pueden cambiarlos, dado que el enunciado dice «el profesor»?

- **Requisitos:** R2.6.7, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define el modelo de configuración, la UI de la tarea y los permisos RBAC; el valor por defecto del evento «repositorio disponible» afecta directamente lo que se ve en la parcial.
- **Opciones:**
  - Toggles por tarea, todos ON por defecto
  - Toggles por tarea, todos OFF por defecto
  - Toggles por tarea con herencia de una plantilla de curso
  - Granularidad por entrega dentro de la tarea
  - Solo el profesor puede cambiarlos vs también ayudantes con permiso
- **Estudio de APIs:** §9.4 propone una «tabla de flags por tarea»; §3.4 no asigna un permiso específico a los toggles.
- **Fusiona:** P522

### Q-2.6-30 — Para informar al estudiante el repositorio que le corresponde (R2.3.12), ¿se usa comentario en la entrega de Canvas (submission comment), mensaje directo (Conversation), o ambos, asumiendo el riesgo de doble aviso? Si la tarea tiene varias entregas, ¿en cuál submission se comenta (la primera, la próxima)? ¿Qué texto se envía cuando la invitación de GitHub quedó pendiente (201) frente a acceso inmediato (204)? Más en general, para todos los mensajes automáticos a estudiantes (repositorio disponible, usuario de GitHub inválido, recordatorio de usuario faltante, proximidad de fecha, cambio de fecha): ¿son plantillas editables por tarea con variables y vista previa, o textos fijos, y al activar o desactivar cada flag (R2.6.7) el profesor ve exactamente qué recibirá el estudiante y por qué canal?

- **Requisitos:** R2.3.12, R2.6.5, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es lo que se demuestra al cierre de la parcial («mostrar el mensaje que le llegó al estudiante en Canvas»); define plantilla, canal, número de llamadas por repositorio y la pantalla «Comunicaciones» de la tarea.
- **Opciones:**
  - Solo Conversation
  - Solo comentario en la entrega
  - Ambos siempre
  - Configurable por tarea
  - Textos fijos vs plantillas editables con vista previa por canal
- **Estudio de APIs:** §5.7 recomienda usar ambos canales (comentario en la entrega + Conversation); §5.4 documenta 201 (invitación pendiente) vs 204 (acceso directo); §9.4 propone 6 flags por tarea sin defaults ni plantillas.
- **Fusiona:** P512, P538

### Q-2.6-31 — ¿Se comunica al estudiante al crearse el repositorio (estado CREATED, aunque la invitación esté pendiente) o solo cuando está READY (invitación aceptada)? Si la invitación no se acepta en N días, ¿se envía un recordatorio automático «acepta tu invitación», con qué frecuencia y con qué tope, y se reenvía la invitación de GitHub (revocar y crear) junto con el mensaje?

- **Requisitos:** R2.6.7, R2.3.9, R2.3.11, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define el disparador exacto en la máquina de estados de repositorios y el texto del mensaje; el recordatorio agrega un evento y un job periódico.
- **Opciones:**
  - Avisar en CREATED con instrucciones para aceptar la invitación
  - Avisar solo en READY
  - Avisar en ambos estados con textos distintos
  - Recordatorio de invitación con reenvío automático vs solo mensaje
- **Estudio de APIs:** §5.5 paso 6 notifica tras agregar colaboradores; §5.4 explica 201 (invitación) vs 204 (acceso directo); §5.6 sugiere la acción «Reenviar».
- **Fusiona:** P526

### Q-2.6-32 — ¿Con qué frecuencia se envía el recordatorio automático a los estudiantes sin usuario de GitHub (diaria, cada N días), con qué tope de intentos, desde cuándo (al crear la tarea, al publicarse la tarea de recolección) y hasta cuándo (vencimiento de la tarea de recolección, cierre de la primera entrega)? ¿Se envía también a integrantes de grupos cuyo repositorio está bloqueado por un compañero sin mapeo, y con qué texto distinto?

- **Requisitos:** R2.6.7, R2.2.5, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** si
- **Por que importa:** Forma parte de la estrategia de enrolamiento cuya usabilidad se evalúa; define un job periódico y sus límites.
- **Opciones:**
  - Recordatorio diario con tope de N envíos
  - Recordatorio cada N días sin tope hasta el cierre
  - Un único recordatorio
  - Incluir a los compañeros de grupo bloqueados con texto distinto vs no incluirlos
- **Estudio de APIs:** §6.3 propone un «job diario que envía Canvas Conversation solo a los estudiantes sin mapeo»; §9.4 define el flag `notify_missing_mapping`.
- **Fusiona:** P527

### Q-2.6-33 — ¿Con cuánta anticipación se envía el recordatorio de proximidad de entrega (48 h fijas, configurable por tarea, varios hitos 7d/48h/24h)? ¿Se calcula sobre la fecha efectiva de cada estudiante o grupo (overrides por sección y extensiones individuales), generando envíos en momentos distintos, o sobre la fecha base? ¿Se envía por mensaje directo individual o por anuncio por sección? ¿Se omite si el sujeto ya tiene commits recientes?

- **Requisitos:** R2.6.7, R2.4.2, R2.4.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija la regla de programación del outbox (`scheduled_for` por sujeto), el canal y la lógica condicional.
- **Opciones:**
  - 48 h fijas sobre la fecha base
  - Hitos múltiples (7d/48h/24h) configurables por tarea
  - Cálculo sobre la fecha efectiva por estudiante o grupo
  - Omitir si hay commits recientes vs enviar siempre
- **Estudio de APIs:** §9.4 propone «Faltan 48 h → Conversation individual o anuncio» y «Faltan 24 h y el repo no tiene commits → Conversation»; §7.3 define la fecha efectiva por estudiante.
- **Fusiona:** P523

### Q-2.6-34 — ¿Se comunica al estudiante cuando se captura la versión de cierre de su entrega (SHA, fecha, enlace `tree/<sha>`), incluyendo el caso NO_COMMITS? ¿Se comunica al equipo docente de inmediato o solo dentro del informe diario?

- **Requisitos:** R2.6.7, R2.4.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.6.7 dice «tales como»; incluirlo agrega un evento, una plantilla y un toggle, y da transparencia al estudiante sobre qué versión será corregida.
- **Opciones:**
  - Comunicar al estudiante siempre, incluido NO_COMMITS
  - Comunicar solo cuando hay commits
  - No comunicar al estudiante; solo al equipo docente
  - Al equipo docente de inmediato vs solo en el informe diario
- **Estudio de APIs:** §7.5 sugiere que NO_COMMITS es «valioso para el informe»; no propone comunicarlo al estudiante.
- **Fusiona:** P528

### Q-2.6-35 — Al registrar una calificación desde la app (R2.7.6), ¿se envía además un mensaje directo al estudiante o grupo (con nota, comentario, SHA revisado, enlace a la rúbrica), o se confía en la notificación nativa de Canvas al publicar la nota? Si se envía, ¿es un toggle por tarea (R2.6.7) y cómo se maneja una tarea grupal con `grade_group_students_individually=true` (notas distintas por integrante)?

- **Requisitos:** R2.6.5, R2.6.7, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.6.5 menciona «corrección» como caso de uso; define un evento adicional del outbox, su plantilla y su interacción con la publicación de notas.
- **Opciones:**
  - Confiar en la notificación nativa de Canvas
  - Mensaje propio con detalle de la corrección, activable por tarea
  - Mensaje individual por integrante en tareas grupales con nota individual
- **Estudio de APIs:** §9.4 lista «Corrección publicada → Conversation individual (`notify_graded`)»; §10.4 explica la propagación de notas grupales.
- **Fusiona:** P513

## Mensajes directos: redaccion, destinatarios y ritmo

### Q-2.6-36 — ¿El equipo docente puede redactar y enviar un mensaje directo libre a un estudiante o grupo desde la app (desde la vista del repositorio o de la entrega), además de los automáticos? Si es así, ¿con texto totalmente libre, plantilla más edición, o solo plantillas predefinidas? ¿Qué roles pueden hacerlo?

- **Requisitos:** R2.6.5, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.6.5 («cuando sea necesario comunicar información particular… creación, corrección, etc.») admite lectura manual y automática; define una vista, un permiso y el tipo de contenido permitido.
- **Opciones:**
  - Solo comunicaciones automáticas
  - Texto totalmente libre
  - Plantilla predefinida con edición
  - Solo plantillas predefinidas sin edición
- **Estudio de APIs:** §3.4 propone el permiso `student.communicate`; §9.3 solo describe el endpoint POST /conversations.
- **Fusiona:** P505

### Q-2.6-37 — Para un repositorio grupal, ¿el mensaje va como conversaciones privadas individuales a cada integrante (`group_conversation=false`) o como un solo hilo con todos los integrantes (`group_conversation=true`, donde se ven entre sí y pueden responder a todos)? ¿Se envía también a los integrantes que aún no tienen usuario de GitHub mapeado, con un texto distinto?

- **Requisitos:** R2.6.5, R2.6.7, R2.2.3
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Cambia el parámetro de la API, el número de llamadas, la privacidad y la redacción («tu repositorio» vs «el repositorio del grupo»).
- **Opciones:**
  - Conversaciones individuales privadas
  - Un solo hilo grupal
  - Individual para automáticos y grupal para manuales
  - Texto diferenciado para integrantes sin usuario mapeado
- **Estudio de APIs:** §9.3 recomienda `group_conversation=false` para notificaciones masivas; no distingue el caso de un grupo pequeño ni el de integrantes sin mapeo.
- **Fusiona:** P506

### Q-2.6-38 — En los mensajes a integrantes de un grupo, ¿se nombra a los compañeros con información pendiente («falta que M. Soto registre su usuario» / «A. Díaz no ha aceptado su invitación») o solo se indica el conteo («falta 1 integrante») por privacidad entre pares? ¿Se informa a un estudiante de la extensión individual otorgada a un compañero cuando eso mueve la fecha efectiva del repositorio grupal? ¿Quién decide el nivel de detalle: es fijo o configurable por el profesor?

- **Requisitos:** R2.6.5, R2.6.7, R2.2.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija las variables permitidas en plantillas grupales y una regla de privacidad entre estudiantes defendible.
- **Opciones:**
  - Nombrar a los compañeros pendientes
  - Solo conteo
  - Configurable por el profesor
- **Estudio de APIs:** §9.3 recomienda `group_conversation=false` para privacidad frente al resto del curso; no aborda qué información de compañeros se revela dentro del grupo.
- **Fusiona:** P472

### Q-2.6-39 — ¿Cada tipo de mensaje lleva un asunto fijo (máx. 255 caracteres) y se usa `force_new` para crear una conversación por evento, o se agrega el mensaje a una conversación existente por estudiante y tarea (donde Canvas ignora el asunto)? ¿Se envía siempre `context_code=course_X` para que el mensaje quede asociado al curso?

- **Requisitos:** R2.6.5, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define cómo se ve el buzón del estudiante (un hilo por tarea vs muchos mensajes sueltos) y qué identificador externo se guarda para trazabilidad.
- **Opciones:**
  - Una conversación nueva por evento (`force_new`)
  - Un hilo por estudiante y tarea, agregando mensajes
  - Un hilo por estudiante y curso
- **Estudio de APIs:** §9.3 documenta `subject` (ignorado al reutilizar conversación), `force_new`, `context_code` y POST /conversations/:id/add_message.
- **Fusiona:** P507

### Q-2.6-40 — ¿Existe un tope o una consolidación de mensajes automáticos por estudiante y día considerando TODOS los tipos y tareas (repositorio disponible ×3 tareas, recordatorios de 48 h y 24 h, invitación pendiente, sin actividad, cambio de fecha, nota publicada), o cada evento envía su propio mensaje? Casos de ráfaga a resolver: tarea creada con cierre en 2 días (repositorio disponible + 48 h + 24 h casi juntos); estudiante que reentrega la tarea de registro con el mismo usuario válido tres veces (¿tres comentarios «confirmado» o uno solo?).

- **Requisitos:** R2.6.5, R2.6.7, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define reglas de agrupación y supresión en el outbox y evita que el estudiante ignore los mensajes por saturación.
- **Opciones:**
  - Sin tope
  - Digest diario por estudiante
  - Supresión por tipo dentro de una ventana de N horas
  - Dedupe de confirmaciones idénticas por contenido
- **Estudio de APIs:** §9.4 propone un outbox con unicidad por (kind, target, delivery_id) y flags por tarea; no aborda un tope por estudiante ni consolidación entre tipos o tareas.
- **Fusiona:** P471

### Q-2.6-41 — ¿Los mensajes automáticos pueden enviarse a cualquier hora (por ejemplo a las 03:00, cuando el worker crea un repositorio) o se agrupan en una ventana horaria (08:00–21:00 America/Santiago)? ¿Las fechas dentro de los mensajes se muestran en hora de Chile con indicación explícita de la zona horaria, y cómo se manejan los cambios de horario de verano en los textos?

- **Requisitos:** R2.6.7, R2.6.5
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define `scheduled_for` en el outbox y el formato de fechas de todas las plantillas.
- **Opciones:**
  - Envío inmediato a cualquier hora
  - Ventana horaria fija con encolado fuera de ella
  - Ventana configurable por curso
- **Estudio de APIs:** §14 recomienda guardar UTC y convertir al renderizar; no aborda ventanas horarias de envío.
- **Fusiona:** P532

### Q-2.6-42 — Las comunicaciones automáticas del tipo «tu repositorio no registra actividad» o «no has participado» se derivan de métricas que pueden estar equivocadas (estudiante que trabaja sin pushear, commits no atribuidos por email desconocido, invitación aún no aceptada, trabajo en una rama no considerada). ¿Qué salvaguardas se fijan antes de que un juicio de participación llegue al estudiante? Decidir: (a) si esos mensajes se envían al estudiante o se limitan al informe docente (R2.6.2) dejando el contacto a criterio humano; (b) si requieren aprobación o revisión previa del profesor (como un anuncio en borrador) o salen automáticos; (c) redacción obligatoria en términos verificables («no hemos detectado commits en la rama X de tu repositorio») en vez de acusatorios; (d) exclusiones automáticas que suprimen el envío (repositorio creado hace menos de N días, invitación pendiente, existen commits sin atribuir en ese repositorio, período anterior a `unlock_at`, estudiante retirado); (e) si existe una supresión por estudiante («no enviar más mensajes automáticos a X, motivo Y») con autor y fecha.

- **Requisitos:** R2.6.7, R2.6.5, R2.5.3, R2.5.4, R2.6.2
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Convierte R2.6.7 en reglas de negocio verificables y evita que la app envíe acusaciones falsas a estudiantes reales, algo que el profesor puede preguntar el 7-oct y que degrada la confianza en todo el módulo de seguimiento.
- **Opciones:**
  - No enviar juicios de participación al estudiante: solo al informe docente
  - Enviar automáticos con redacción neutra y exclusiones duras
  - Cola de aprobación: el profesor revisa y confirma antes de enviar
  - Configurable por tarea, con valor por defecto desactivado
- **Estudio de APIs:** §9.4 incluye `notify_no_activity` (faltan 24 h y el repo no tiene commits) como comunicación automática al estudiante, y §8.4 advierte que hay que mostrar los commits sin atribuir para «no acusar injustamente»; pero el estudio no propone aprobación previa, supresiones ni reglas de redacción para lo que llega al estudiante.
- **Fusiona:** N020

### Q-2.6-43 — Los mensajes salen con el token del profesor, así que las respuestas del estudiante a una Conversation, a un comentario de entrega o los comentarios en un anuncio llegan a la bandeja o al SpeedGrader del profesor en Canvas, no a la app. ¿La app (a) lee periódicamente esas respuestas (GET /conversations con el mismo token) y las muestra al equipo docente junto al estudiante y su repositorio (útil para «registré mal mi usuario», «no me llega la invitación», «solicito recorrección») o marca «el estudiante respondió»; (b) declara explícitamente que las respuestas se gestionan solo en Canvas y cada mensaje indica a quién responder y por qué canal; (c) marca cada mensaje automático como tal («Mensaje automático de <app>; para ayuda escribe a X»)? ¿Se advierte al profesor vinculador de que recibirá respuestas a mensajes que él no escribió, cómo las reconoce (prefijo en el asunto) y cómo se evita que reciba 60 correos de Canvas por esas respuestas?

- **Requisitos:** R2.6.5, R2.6.6, R2.6.7, R2.2.5, R2.1.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Decide si existe un canal de soporte cerrado para el estudiante y si la app necesita scopes de lectura de conversations; fija el pie de todos los mensajes automáticos y la advertencia en el paso de vinculación de Canvas.
- **Opciones:**
  - Leer respuestas de Canvas y mostrarlas en la app por estudiante
  - Solo en Canvas, declarado como limitación
  - Etiquetar los mensajes como automáticos con un contacto de ayuda en el pie
  - Prefijar los asuntos para que el profesor los filtre en Canvas
  - Advertencia explícita al profesor vinculador durante la vinculación
- **Estudio de APIs:** §9.3 y §9.4 solo cubren el envío (POST /conversations, add_message, outbox) con el token del profesor; no abordan la lectura de respuestas entrantes, la bandeja del profesor ni los comentarios en anuncios.
- **Fusiona:** P470, P474

## Anuncios en Canvas

### Q-2.6-44 — ¿Los anuncios generados por la app se publican automáticamente en Canvas (`published=true`) o se crean como borrador (`published=false`) para que el profesor los revise y publique desde Canvas o desde la app? ¿Depende del tipo de anuncio (automático por evento vs manual)?

- **Requisitos:** R2.6.6, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el flujo de aprobación, el uso del parámetro `published` y si la app necesita una bandeja de «anuncios pendientes de publicar».
- **Opciones:**
  - Publicar automáticamente
  - Crear borrador para revisión
  - Automático para eventos, borrador para manuales
  - Configurable por tarea
- **Estudio de APIs:** §9.2 muestra `published=true` en el ejemplo y documenta `published=false` como borrador y `delayed_post_at`.
- **Fusiona:** P514

### Q-2.6-45 — Cuando un cambio de fecha afecta solo a una sección, ¿el anuncio se dirige solo a esa sección (`specific_sections`) o a todo el curso? Cuando afecta a un override individual o de grupo (extensión a un estudiante), ¿se genera un anuncio público, un mensaje directo al afectado, o nada por privacidad?

- **Requisitos:** R2.6.6, R2.4.2, R2.4.3
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la regla de enrutamiento del evento «cambio de fecha» y protege la privacidad de las extensiones individuales.
- **Opciones:**
  - Anuncio a la sección afectada con `specific_sections`
  - Anuncio a todo el curso siempre
  - Mensaje directo al afectado en overrides individuales o de grupo
  - No comunicar las extensiones individuales
- **Estudio de APIs:** §9.2 sugiere `specific_sections` para fechas por sección; §7.1 distingue overrides ADHOC, de grupo y de sección; no aborda extensiones individuales en anuncios.
- **Fusiona:** P515

### Q-2.6-46 — ¿Cualquier cambio de `due_at` dispara un anuncio, o solo los cambios mayores a un umbral (por ejemplo, más de 1 h)? ¿También los cambios de `lock_at`/`unlock_at`, la creación o eliminación de un override, o el cambio de fecha de una entrega ya cerrada (con snapshot capturado)? Si el profesor edita la fecha varias veces dentro de la ventana de polling (10 min), ¿se publica un anuncio con la fecha final o uno por cada cambio? ¿Se espera un tiempo de gracia antes de anunciar?

- **Requisitos:** R2.6.6, R2.6.7, R2.4.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la detección de eventos, el debounce y evita anuncios ruidosos o contradictorios; también decide si un cambio posterior al cierre reabre la entrega o solo alerta al docente.
- **Opciones:**
  - Anunciar todo cambio de fecha
  - Anunciar solo cambios por encima de un umbral configurable
  - Debounce con ventana de gracia y anuncio con la fecha final
  - Incluir o excluir `lock_at`/`unlock_at` y overrides de la regla
- **Estudio de APIs:** §7.4 sugiere «si el cambio es relevante (>1h) y el profesor lo activó → publicar anuncio»; no aborda debounce, `lock_at` ni entregas ya cerradas.
- **Fusiona:** P516

### Q-2.6-47 — ¿Cuál es el contenido del anuncio de cambio de fecha (título, fecha anterior → nueva en hora local, entrega afectada, sección, enlace a la tarea en Canvas)? ¿Puede el profesor editar el título y el cuerpo antes de publicar, o es texto fijo generado por la app?

- **Requisitos:** R2.6.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la plantilla, sus variables y si existe una vista de edición previa a la publicación.
- **Opciones:**
  - Texto fijo generado por la app
  - Plantilla editable antes de publicar
  - Plantilla editable por curso o por tarea
- **Estudio de APIs:** §9.2 da un ejemplo mínimo de título y mensaje HTML.
- **Fusiona:** P517

### Q-2.6-48 — ¿El docente puede redactar anuncios libres desde la app asociados a una tarea (por ejemplo «los repositorios ya están disponibles», «recordatorio de entrega») con selección de secciones y publicación inmediata o programada (`delayed_post_at`)? ¿Qué roles pueden hacerlo?

- **Requisitos:** R2.6.6, R2.1.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.6.6 habla de «eventos generales asociados a una tarea, como cambio en las fechas» (ejemplo, no lista cerrada); define una vista y un permiso.
- **Opciones:**
  - Solo anuncios automáticos por evento
  - Anuncios libres con publicación inmediata
  - Anuncios libres con programación (`delayed_post_at`) y selección de secciones
- **Estudio de APIs:** §9.2 documenta `delayed_post_at` y `specific_sections`; §3.4 propone el permiso `student.communicate`.
- **Fusiona:** P518

### Q-2.6-49 — Canvas ya notifica nativamente a los estudiantes cuando cambia la fecha de una tarea: ¿el anuncio de la app se publica igual por requisito, y cómo se evita publicar dos anuncios por el mismo cambio tras un reinicio (clave de idempotencia: entrega + fecha anterior + fecha nueva)? ¿Se guarda el `discussion_topic_id` y se lista el historial de anuncios en la app con enlace a Canvas?

- **Requisitos:** R2.6.6, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la idempotencia y la trazabilidad de anuncios, y la explicación que el equipo dará si se le pregunta por la duplicidad con las notificaciones de Canvas.
- **Opciones:**
  - Publicar siempre el anuncio propio, aceptando la duplicidad
  - Publicar solo si el cambio es relevante, documentando la duplicidad
  - Clave de idempotencia por entrega + fecha anterior + fecha nueva
  - Historial de anuncios con `discussion_topic_id` y enlace a Canvas
- **Estudio de APIs:** §9.2 documenta GET discussion_topics?only_announcements=true; §9.4 propone un constraint único en el outbox.
- **Fusiona:** P519

### Q-2.6-50 — ¿El token del profesor puede crear anuncios con `specific_sections` en la instancia real (Free-for-Teacher o institucional)? ¿Qué ocurre si la Developer Key tiene «enforce scopes» sin POST discussion_topics, o si el curso restringe la creación de anuncios? ¿Se refleja el resultado en el checklist de verificación de la vinculación (R2.1.6)?

- **Requisitos:** R2.6.6, R2.1.6
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Si falla, R2.6.6 no es demostrable; hay que probarlo temprano y definir el mensaje de error y el chequeo de vinculación.
- **Opciones:**
  - Verificar y agregar el ítem al checklist de vinculación
  - Asumir viable y manejar el error en tiempo de ejecución
  - Plan B con anuncio a todo el curso si `specific_sections` falla
- **Estudio de APIs:** §3.3 incluye «Podemos publicar anuncios» en el checklist; §1.3 lista el scope `url:POST|/api/v1/courses/:course_id/discussion_topics`.
- **Fusiona:** P520

### Q-2.6-51 — ¿Cuál es el ciclo de vida de una comunicación ya publicada? (a) Los anuncios creados por la app, ¿permiten comentarios de los estudiantes (comportamiento por defecto de Canvas) o se crean cerrados a comentarios (`locked` / `lock_at` inmediato) para evitar hilos que nadie del equipo docente monitorea, y se respeta la configuración del curso que deshabilita comentarios en anuncios? (b) ¿Se guarda el `discussion_topic_id` para editar o eliminar el anuncio desde la app si la fecha vuelve a cambiar antes de que los estudiantes lo lean? (c) ¿Se puede RETRACTAR desde la app un anuncio publicado por error (DELETE discussion_topics) o un comentario de entrega, sabiendo que una Conversation no puede retirarse, y se exige confirmación adicional antes de enviar lo irreversible? (d) ¿Se evita que el anuncio notifique como ruido a los propios docentes?

- **Requisitos:** R2.6.5, R2.6.6, R2.6.7, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Fija los parámetros exactos del POST de anuncios, la política de comentarios, y da al docente una salida ante errores de comunicación masiva sin dejar hilos ruidosos sin moderar.
- **Opciones:**
  - Anuncio abierto a comentarios
  - Anuncio bloqueado a comentarios
  - Configurable por curso
  - Botón «eliminar anuncio» con registro, y confirmación fuerte antes de envíos irreversibles
  - Sin edición ni borrado desde la app; se gestiona en Canvas
- **Estudio de APIs:** §9.2 lista `lock_at` («cuándo se cierra a comentarios») y `delayed_post_at` sin fijar valores ni política de edición; §9.3 envía Conversations con el token del profesor; no aborda la retractación de mensajes.
- **Fusiona:** P475, P478

## Trazabilidad, plantillas y notificaciones internas

### Q-2.6-52 — ¿Qué campos guarda el log u outbox de comunicaciones (tipo, canal, destinatario, tarea y entrega, cuerpo final renderizado, disparado por automático o por el usuario X, programado para, enviado el, estado, error, id externo de Canvas —`conversation_id`, `discussion_topic_id`— o del proveedor de email), qué vistas lo exponen (por curso, por tarea, por estudiante, por repositorio), qué roles pueden verlo y cuánto tiempo se retiene? ¿Puede el docente abrir la conversación en Canvas desde la app, reenviar o reintentar un envío fallido, y enviar un mensaje manual a un estudiante o grupo desde la tabla de repositorios («Recordar usuario GitHub»)?

- **Requisitos:** R2.3.12, R2.6.4, R2.6.5, R2.6.6, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** si
- **Por que importa:** Cierra la trazabilidad de toda la sección 2.6: sin historial el docente no puede saber si el estudiante fue informado de su repositorio (R2.3.12) ni demostrarlo en la revisión, y define la pantalla, las acciones manuales y un criterio de aceptación demostrable.
- **Opciones:**
  - Outbox completo con cuerpo renderizado e id externo, visible por curso, tarea, estudiante y repositorio
  - Log mínimo (tipo, destinatario, fecha, estado) sin cuerpo
  - Con acciones de reenvío y reintento desde la vista
  - Solo lectura, sin acciones manuales
- **Estudio de APIs:** §9.4 propone `notification_outbox(id, kind, target, payload, scheduled_for, sent_at, error)` más una «pantalla de historial de comunicaciones que pueden mostrar en la demo»; §9.1 pide registro de envíos del informe; §5.6 muestra la acción «Recordar» en la tabla de repositorios.
- **Fusiona:** P508, P531, P537

### Q-2.6-53 — ¿Las plantillas de mensajes y anuncios son fijas en el código, editables por curso, o editables por tarea? ¿Qué variables se exponen (`{{nombre}}`, `{{repo_url}}`, `{{fecha_local}}`, `{{entrega}}`, `{{sha}}`), se validan las variables desconocidas al guardar, y existe «restaurar plantilla por defecto»? ¿El docente puede ver una vista previa renderizada de cada comunicación con datos reales de un estudiante de ejemplo antes de activarla, y enviarse un mensaje de prueba a sí mismo por Canvas o por email? ¿Los envíos de prueba quedan marcados como tales en el historial?

- **Requisitos:** R2.6.5, R2.6.6, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el modelo de plantillas, el motor de renderizado, una pantalla de edición con validación y una vista previa cuya usabilidad es evaluada; además obliga a distinguir los envíos de prueba en el log.
- **Opciones:**
  - Plantillas fijas en el código
  - Plantillas editables por curso
  - Plantillas editables por tarea
  - Vista previa con datos reales de un estudiante de ejemplo
  - Envío de prueba al propio docente, marcado en el historial
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P529, P530

### Q-2.6-54 — ¿Existe un centro de notificaciones dentro de la app (icono con badge) o las alertas se muestran solo en contexto (banners) y en el informe por email? Si existe: ¿qué eventos generan notificación in-app (repositorio con error, invitación sin aceptar más de N días, fecha cambiada en Canvas, tarea de Canvas eliminada, entrega cerrada y snapshot capturado, corrección asignada), se marcan como leídas, y son por usuario o por curso?

- **Requisitos:** R2.6.1, R2.6.2, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define un subsistema de notificaciones internas con su modelo de datos y UI, o lo descarta explícitamente en favor de banners más correo.
- **Opciones:**
  - Centro de notificaciones con estado de leído
  - Solo banners en contexto y correo
  - Banners más un resumen en el dashboard, sin centro de notificaciones
- **Estudio de APIs:** §9.4 propone la tabla `notification_outbox` para comunicaciones a estudiantes y una «pantalla de historial»; no propone notificaciones in-app para docentes.
- **Fusiona:** P536

## Casos borde, fallos y recuperacion

### Q-2.6-55 — Si POST /conversations falla (403 por throttling, 401 por token expirado, 5xx, destinatario inválido), ¿cuántos reintentos, con qué backoff y cuándo se declara fallido definitivamente? ¿Hay mensajes con fecha de caducidad (un recordatorio de 48 h que ya no tiene sentido si la entrega venció) que no deben enviarse tarde? ¿Se avisa al docente de los fallos en la UI o en el informe diario?

- **Requisitos:** R2.6.5, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la máquina de estados del outbox y evita enviar mensajes desfasados a los estudiantes.
- **Opciones:**
  - N reintentos con backoff exponencial y estado final de error
  - Sin reintentos, solo registro
  - Caducidad por tipo de mensaje (no enviar recordatorios vencidos)
  - Aviso de fallos en la UI, en el informe diario, o en ambos
- **Estudio de APIs:** §9.4 menciona reintentos en el outbox; §1.5 recomienda backoff ante 403/429; no define caducidad de mensajes.
- **Fusiona:** P509

### Q-2.6-56 — ¿Se envían mensajes a estudiantes cuya matrícula pasó a inactive/deleted/concluded en Canvas (por ejemplo, un recordatorio de entrega a un alumno que abandonó el curso)? ¿Canvas acepta ese destinatario con el token del profesor o devuelve error? ¿Y a un estudiante que salió de un grupo pero sigue como colaborador del repositorio?

- **Requisitos:** R2.6.5, R2.6.7, R2.2.1
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define los filtros del outbox y evita mensajes indebidos o errores 4xx que bloqueen la cola.
- **Opciones:**
  - Excluir toda matrícula que no esté activa
  - Enviar igual y registrar el error si Canvas lo rechaza
  - Excluir según el tipo de mensaje (recordatorios sí, avisos de repositorio no)
- **Estudio de APIs:** §4.4 recomienda marcar a los retirados sin borrarlos; §14 trata «Estudiantes que se retiran»; no lo relaciona con comunicaciones.
- **Fusiona:** P511

### Q-2.6-57 — ¿Cuál es la clave de idempotencia por evento (tipo + destinatario + entrega, más la fecha objetivo)? Si la fecha de una entrega cambia después de enviado el recordatorio y la nueva fecha vuelve a entrar en la ventana, ¿se envía un segundo recordatorio? Si un repositorio pasa READY → ERROR → READY, o se elimina y se recrea, ¿se reenvía «repositorio disponible»?

- **Requisitos:** R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el constraint único del outbox y evita spam a los estudiantes tras reinicios del worker o cambios de fecha.
- **Opciones:**
  - Clave por (tipo, destinatario, entrega) sin fecha objetivo: nunca se repite
  - Clave que incluye la fecha objetivo: un cambio de fecha permite un nuevo envío
  - Reenvío explícito solo por acción manual del docente
- **Estudio de APIs:** §9.4 propone un constraint único por (kind, target, delivery_id); no cubre cambios de fecha posteriores ni la recreación de repositorios.
- **Fusiona:** P524

### Q-2.6-58 — Cuando el profesor desactiva un toggle de comunicaciones, ¿se cancelan los mensajes ya programados y no enviados, y qué pasa con los que están en proceso de envío? Al reactivarlo, ¿se reprograman los eventos que aún tienen sentido (fecha futura) y se descartan los pasados, o se envían los pendientes acumulados? ¿Se registra quién y cuándo cambió el toggle?

- **Requisitos:** R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el efecto del toggle sobre el outbox y la auditoría de configuración.
- **Opciones:**
  - Cancelar lo programado al desactivar y reprogramar solo lo futuro al reactivar
  - Cancelar al desactivar y no reprogramar nada al reactivar
  - Enviar los pendientes acumulados al reactivar
  - Registrar autor y fecha de cada cambio de toggle
- **Estudio de APIs:** §9.4 no lo aborda.
- **Fusiona:** P525

### Q-2.6-59 — Si la assignment de Canvas asociada a una entrega es eliminada en Canvas o el profesor la desvincula en la app, ¿se cancelan los recordatorios pendientes de esa entrega, se comunica algo a los estudiantes (anuncio) y se alerta al docente en el informe o en la UI? ¿Y si se elimina la tarea de Canvas usada para recolectar los usuarios de GitHub?

- **Requisitos:** R2.6.7, R2.6.6, R2.3.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el comportamiento en cascada del outbox ante cambios estructurales en Canvas.
- **Opciones:**
  - Cancelar en silencio los pendientes y alertar solo al docente
  - Cancelar y anunciar a los estudiantes
  - Mantener los pendientes hasta que el docente decida
- **Estudio de APIs:** §7.4 sugiere un log de auditoría de cambios de Canvas; no aborda la eliminación de assignments.
- **Fusiona:** P533

### Q-2.6-60 — Si Canvas agrega un integrante a un grupo que ya tiene repositorio, ¿recibe automáticamente el mensaje «repositorio disponible» al ser agregado como colaborador? Si un integrante sale del grupo, ¿se le comunica algo, se le quita del repositorio y se deja de incluirlo en los recordatorios del grupo?

- **Requisitos:** R2.6.7, R2.2.3, R2.3.9
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define los disparadores de comunicación sobre cambios de membresía detectados por la sincronización.
- **Opciones:**
  - Mensaje automático al nuevo integrante y aviso de salida al que se va
  - Mensaje automático solo al nuevo integrante, salida en silencio
  - Sin comunicación automática; solo alerta al docente
- **Estudio de APIs:** §4.4 propone «upsert; marcar como retirado lo que ya no viene»; no lo relaciona con comunicaciones.
- **Fusiona:** P534

## Ya respondidas por el enunciado

Ninguna. La etapa de verificacion marco las 73 preguntas de entrada del area 2.6 (P470–P539 mas N020, N023 y N025) como ABIERTA o ABIERTA/BLOQUEA; ninguna quedo marcada como YA_RESPONDIDA, por lo que no hay entradas que apartar en esta seccion.
