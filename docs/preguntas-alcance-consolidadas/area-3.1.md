# Preguntas de alcance — Area 3.1

18 preguntas finales, fusionadas desde 23 de entrada, 13 bloqueantes para la parcial.

## Alcance de la entrega parcial y criterios de evaluacion

### Q-3.1-01 — ¿Existe una pauta de evaluación publicada por el curso que detalle cómo se reparten los 1,6 ptos. de la entrega parcial y el puntaje de la entrega final entre cobertura de requisitos, facilidad de uso, video, código y validación individual, y se le pedirá formalmente al profesor antes de congelar el alcance? Si no existe o no se entrega a tiempo, ¿con qué criterio propio reparte el equipo el esfuerzo entre las secciones 2.1–2.3 y 2.4–2.7, qué peso explícito se asigna a la "facilidad de uso y la guía adecuada" (único criterio que el enunciado nombra para la parcial) y qué se hace si la pauta llega después de la fecha en que el equipo congeló el alcance?

- **Requisitos:** —
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Es el insumo externo que ordena el backlog y define qué requisitos son recortables; sin él, la priorización entre secciones y la inversión en usabilidad se deciden a ciegas y no pueden justificarse ante el profesor. La respuesta cambia el orden de construcción y el contenido del criterio de "hecho".
- **Opciones:**
  - Pedir la pauta formalmente al profesor antes del 12-sep y congelar el alcance después
  - Asumir peso igual por requisito R2.x.y y documentarlo como supuesto en el spec
  - Ponderar por visibilidad en la revisión con la herramienta (sección 4 del enunciado) en vez de por número de requisitos
  - Priorizar solo por lo que el enunciado nombra explícitamente en 3.1 y dejar 2.4–2.7 al criterio del equipo
  - Congelar el alcance sin pauta y reabrirlo únicamente si la pauta, al llegar, contradice el reparto asumido
- **Estudio de APIs:** no lo aborda: propone un plan de trabajo (§13) y una lista de riesgos, pero no considera la pauta de evaluación como insumo de priorización.
- **Fusiona:** N006

### Q-3.1-02 — ¿Cuál es la lista cerrada de requisitos que se demostrarán el 16-sep y cuáles quedan explícitamente declarados fuera del alcance parcial? El enunciado solo nombra el flujo usuario profesor → curso → vinculación con Canvas y GitHub → creación de una tarea individual → asociación estudiantes↔usuarios GitHub → creación automática de repositorios: ¿entran en la parcial R2.1.6 (checklist de verificación de la vinculación), R2.3.5/R2.3.6 (repositorio base con archivos), R2.3.9 (agregar colaboradores), R2.3.11 (tabla de estados de creación), R2.3.12 (aviso al estudiante por Canvas), R2.2.6 (panel de estudiantes faltantes) y R2.1.7/R2.1.8 (co-profesores y ayudantes)? Dentro de la sección 2.3, ¿se demuestra solo la tarea individual con una entrega o también el repositorio base con archivos y la multi-entrega, y qué queda comprometido para el 6-oct?

- **Requisitos:** R2.1.1, R2.1.3, R2.1.4, R2.1.5, R2.1.6, R2.1.7, R2.1.8, R2.2.4, R2.2.6, R2.3.1, R2.3.5, R2.3.6, R2.3.7, R2.3.9, R2.3.10, R2.3.11, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define el backlog de los días restantes y qué pantallas deben existir con datos reales; lo no listado se declara en el spec como "fuera de alcance parcial" para que nadie lo dé por exigido ni por omitido.
- **Opciones:**
  - Solo lo literal del enunciado (sin repositorio base, sin colaboradores, sin ayudantes, sin notificación)
  - Literal + R2.1.6 + R2.3.11 + R2.3.12 (plan §13)
  - Literal + repositorio base opcional R2.3.5/R2.3.6
  - Sección 2.3 completa (repositorio base, colaboradores, multi-entrega y aviso por Canvas) en la parcial
- **Estudio de APIs:** §13 propone 10 hitos mínimos que incluyen checklist de verificación (§3.3), recolección por tarea de Canvas, worker + tabla de estados y notificación al estudiante; no incluye repositorio base ni ayudantes. §13 también propone un guion de demo y recomienda "dejen visible un caso con problema" para R2.3.11.
- **Fusiona:** P623, P639

### Q-3.1-03 — Para la "tarea individual" de la demo parcial, ¿la tarea de la app se vincula a UNA sola tarea de Canvas (una entrega) o ya se demuestra la vinculación 1..N (parcial + final) aunque no existan snapshots? ¿La validación de consistencia individual/grupal entre entregas (R2.3.3) se muestra en la parcial o se posterga a la final?

- **Requisitos:** R2.3.1, R2.3.2, R2.3.3
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Determina si el modelo Tarea→Entregas y su UI de vinculación múltiple entran en el sprint de la parcial o quedan como alcance de la final.
- **Opciones:**
  - Una sola entrega vinculada, modelo 1..N presente en el esquema pero no en la UI
  - Vinculación 1..N demostrada en la UI, sin snapshots
  - Vinculación 1..N + validación de consistencia individual/grupal (R2.3.3) demostrada en la parcial
- **Estudio de APIs:** §5.2 define el modelo Assignment→Delivery 1..N y recomienda rechazar la segunda tarea de Canvas si su `group_category_id` difiere.
- **Fusiona:** P624

### Q-3.1-04 — En la build del 16-sep, ¿cómo se presentan las funciones que no están listas para que un evaluador que "se salga del guion" no encuentre comportamientos rotos: se BLOQUEA explícitamente vincular tareas grupales ("disponible en la entrega final") o se permite con comportamiento parcial; las secciones 2.4–2.7 (fechas, dashboard, informes, corrección) se ocultan por completo, se muestran deshabilitadas con etiqueta, o aparecen con datos vacíos? ¿Se usa un feature flag por entorno?

- **Requisitos:** R2.3.3, R2.4.1, R2.5.1, R2.6.1, R2.7.1
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** El evaluador evaluará usabilidad y la sección 4 del enunciado dice que lo no accesible no se considera cumplido; una pantalla a medias o un error 500 al probar algo fuera del flujo pesa distinto que una función oculta.
- **Opciones:**
  - Bloquear con mensaje explícito
  - Ocultar por feature flag
  - Mostrar deshabilitado con etiqueta "próximamente"
  - Permitir con comportamiento parcial
- **Estudio de APIs:** §13 define el mínimo indispensable de la parcial; no aborda cómo presentar lo no implementado.
- **Fusiona:** P640

## Autenticacion, registro y vinculacion de cuentas

### Q-3.1-05 — En la demo parcial, ¿la "creación de un usuario profesor" se hace con Google OAuth real (cuenta gmail.com) o con un formulario propio? Si es Google OAuth: ¿el proyecto de Google Cloud estará en modo "Testing" (máximo 100 usuarios de prueba que deben registrarse por correo) o en "Production"? ¿Hay que pedir los correos gmail del profesor y de los ayudantes para agregarlos como test users antes del 16-sep, y con qué fecha límite?

- **Requisitos:** R2.1.1, R2.1.2
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Si la pantalla de consentimiento está en Testing y el revisor no está registrado como usuario de prueba, no podrá entrar a la app y ninguna funcionalidad se considerará cumplida.
- **Opciones:**
  - Testing + registrar los correos de los revisores como test users
  - Publicar a Production
  - Formulario propio como respaldo
- **Estudio de APIs:** §3.1 indica validar que el claim `email` termine en @gmail.com y `email_verified`; no aborda el modo de publicación del consent screen ni los test users.
- **Fusiona:** P625

### Q-3.1-06 — ¿La restricción "cuenta de correo basada en gmail.com" (R2.1.2) se implementa como rechazo estricto de cualquier dominio distinto a @gmail.com? Si el profesor o los ayudantes intentan entrar con su cuenta institucional Google Workspace (p. ej. @uandes.cl), ¿se les rechaza y con qué texto de error exacto? ¿Se pedirá formalmente a los revisores que usen un gmail personal?

- **Requisitos:** R2.1.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija la regla de validación del login y su texto de error; un rechazo estricto puede impedir que el revisor entre con la cuenta que tiene a mano el día de la revisión.
- **Opciones:**
  - Estricto @gmail.com
  - Cualquier cuenta Google con `email_verified`
  - Estricto @gmail.com + lista blanca configurable de correos
- **Estudio de APIs:** §3.1 recomienda validar el sufijo @gmail.com (nota que el claim `hd` no viene para gmail puro).
- **Fusiona:** P626

### Q-3.1-07 — ¿La UI de vinculación con Canvas ofrecerá un modo "pegar token de acceso" además de OAuth2? Si sí, ¿visible para todos los usuarios, solo detrás de un flag de entorno, o solo en desarrollo? ¿Se muestra al revisor el 16-sep?

- **Requisitos:** R2.1.4, R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** El modo token es el respaldo si falla la Developer Key, pero exhibirlo puede evaluarse como incumplimiento de la política de Canvas; hay que decidir si existe como requisito del spec o como herramienta interna.
- **Opciones:**
  - Solo OAuth2
  - OAuth2 + token manual detrás de feature flag
  - OAuth2 + token manual visible con advertencia
- **Estudio de APIs:** §1.2 recomienda implementar OAuth2 igual aunque en la demo usen un token pegado a mano.
- **Fusiona:** P627

## Entorno de entrega: despliegue, acceso de revisores y entregables

### Q-3.1-08 — El "link para acceder a su entrega" del 16-sep, ¿será una URL pública desplegada con workers/cron activos 24/7 que los ayudantes puedan usar después de la clase, o un link a repositorio con instrucciones para correr localmente? Si es pública, ¿en qué proveedor, con qué plan (incluido el comportamiento de suspensión por inactividad del plan gratuito) y con qué fecha de primer deploy?

- **Requisitos:** R2.3.10
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Los ayudantes probarán fuera del aula; sin deploy permanente el worker automático (R2.3.10) no correrá y la creación automática no será verificable por ellos.
- **Opciones:**
  - URL pública con workers/cron activos 24/7, primer deploy varios días antes del 16-sep
  - URL pública sin workers permanentes (procesamiento solo durante la revisión)
  - Link al repositorio con instrucciones para ejecución local
  - URL pública temporal levantada solo el día de la demo
- **Estudio de APIs:** §13 hito 10: "Deploy con URL pública, nunca la noche anterior, Día 6"; §12 sugiere Railway/Render/Fly.io.
- **Fusiona:** P631

### Q-3.1-09 — ¿Cómo prueban la app el profesor y los ayudantes, que no tienen Developer Key ni organización GitHub propia: (a) con credenciales de una cuenta profesor demo ya vinculada al Canvas y a la organización de prueba; (b) cada revisor se registra con su gmail y el equipo lo agrega como co-profesor (R2.1.7) del curso demo; (c) el revisor vincula su propio curso Canvas y su propia organización (solo viable si la Developer Key es de la instancia institucional y la App es pública)? ¿Se entregan además credenciales de rol ayudante (para demostrar R2.1.8 y la vista "mis correcciones") o solo de profesor con instrucciones para crear ayudantes? ¿Se acompaña el link con un documento de acceso (cuentas, contraseñas, guion de prueba) y con instrucciones de primer uso y prerrequisitos en la landing (tener rol Teacher en un curso Canvas de la instancia soportada, tener una organización GitHub)?

- **Requisitos:** R2.1.1, R2.1.2, R2.1.4, R2.1.5, R2.1.7, R2.1.8, R2.7.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define qué pantallas puede recorrer un revisor sin ayuda, qué cuentas y roles hay que crear y qué material acompaña al link entregado por Canvas; si un revisor entra con permisos restringidos, las funciones que no alcance podrían considerarse no cumplidas (sección 4).
- **Opciones:**
  - Credenciales de cuenta profesor demo ya vinculada (Canvas + organización de prueba)
  - Registro propio del revisor con su gmail + alta como co-profesor del curso demo
  - El revisor vincula su propio curso Canvas y su propia organización GitHub desde cero
  - Entregar credenciales de profesor Y de ayudante para cubrir R2.1.8 y la vista "mis correcciones"
  - Entregar solo credenciales de profesor con instrucciones para crear ayudantes
  - Documento de acceso + guion de prueba adjunto al link, con instrucciones de primer uso en la landing
- **Estudio de APIs:** no lo aborda directamente; §3.4 describe co-profesores gestionados en la BD propia y propone tres roles (profesor, ayudante jefe, ayudante) con matriz de permisos; §1.2 sugiere Free-for-Teacher como entorno de demo; §13 hito 10 exige deploy con URL pública, pero no aborda cómo el revisor reproduce el flujo.
- **Fusiona:** P632, P644, P635

### Q-3.1-10 — ¿Se invitará al profesor y a los ayudantes como Teacher/Observer en el curso Canvas de prueba y como miembros de la organización GitHub demo para que puedan ver "el otro lado" (mensajes recibidos por los estudiantes, anuncios, notas publicadas, repositorios creados)? ¿Se les pedirán sus correos y usuarios GitHub, y para qué fecha?

- **Requisitos:** R2.3.12, R2.6.5, R2.6.6, R2.7.6
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Sin acceso a Canvas y GitHub, los efectos externos de la app (R2.3.12, R2.6.x, R2.7.6) solo se verían por captura de pantalla.
- **Opciones:**
  - Invitar a profesor y ayudantes al curso Canvas de prueba y a la organización GitHub demo, pidiendo correos y usuarios con fecha límite
  - Invitar solo al curso Canvas de prueba
  - No invitar y evidenciar los efectos externos con capturas o video
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P634

### Q-3.1-11 — ¿Se pedirá al profesor acceso (Teacher o TA) al curso real de ICC4201 en la instancia institucional para probar con datos reales? Si sí, ¿qué salvaguardas se exigen para no crear tareas, anuncios, mensajes ni repositorios sobre estudiantes reales (modo "solo lectura" por curso, lista blanca de cursos escribibles, entorno separado)?

- **Requisitos:** R2.1.4, R2.2.1, R2.6.5, R2.6.6
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Probar contra datos reales cambia el riesgo (efectos sobre personas reales) y podría agregar al spec un flag de curso de solo lectura.
- **Opciones:**
  - Pedir acceso al curso real con modo solo lectura por curso
  - Pedir acceso al curso real con lista blanca de cursos escribibles
  - No usar el curso real; solo instancia/curso de prueba
- **Estudio de APIs:** §13 hito 1 habla de "Canvas de pruebas con datos reales" sin distinguir instancia real vs de prueba.
- **Fusiona:** P636

### Q-3.1-12 — ¿Qué se sube exactamente a Canvas en cada entrega: (parcial) URL + credenciales demo + guion de prueba; (final) URL, link al repositorio, link al video, declaración de uso de IA, documento de acceso? ¿Quién del equipo lo sube y con qué hora límite interna anterior a las 13:30 del 16-sep y a la hora oficial de la final?

- **Requisitos:** —
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Evita omisiones el día de la entrega y define qué documentos debe redactar el equipo y con cuánta anticipación.
- **Opciones:**
  - Subir solo los entregables que el enunciado enumera explícitamente
  - Subir los entregables del enunciado + credenciales demo, guion de prueba y documento de acceso
  - Responsable único de la subida con hora límite interna fijada (p. ej. la víspera)
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P637

## Demo presencial del 16-sep: logistica, guion y tiempos

### Q-3.1-13 — ¿Cuánto dura el slot de demo del 16-sep, en qué formato se realiza (equipo frente al curso, por mesas, ante profesor y ayudantes) y con qué recursos del aula (proyector, red Wi-Fi, restricciones de puertos o de acceso a servicios externos)? ¿Se le puede pedir esta información al profesor antes de escribir el guion?

- **Requisitos:** —
- **Tipo:** dependencia_externa · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** El guion de demo, el número de casos a mostrar y el intervalo del worker dependen del tiempo disponible y de la conectividad del aula.
- **Opciones:**
  - Preguntar al profesor duración, formato y recursos antes de escribir el guion
  - Asumir un slot corto (≈6 min) y preparar una versión reducida y otra extendida del guion
  - Preparar respaldo offline (video/capturas) por si la red del aula falla
- **Estudio de APIs:** §13 propone un guion de ≈6 min sin conocer el slot real.
- **Fusiona:** P630

### Q-3.1-14 — ¿Qué guion de demo adopta el equipo para el 16-sep, qué casos con problema se mostrarán deliberadamente (estudiante que no entregó su usuario GitHub, usuario inexistente, usuario que en realidad es una Organization, invitación pendiente sin aceptar) y cuál de ellos se resuelve en vivo para evidenciar R2.2.5 y R2.3.11 (el "estudiante" entrega desde Canvas en otro navegador, el docente carga el usuario manualmente, se acepta la invitación desde una cuenta GitHub del equipo, y el worker crea el repositorio)? ¿Qué datos semilla se preparan (Canvas de prueba con N estudiantes, secciones, group set, cuentas GitHub controladas por el equipo)?

- **Requisitos:** R2.2.5, R2.2.6, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Sin casos problemáticos visibles y resueltos, R2.3.11 y R2.2.6 no pueden considerarse demostrados; el guion determina además qué pantallas deben estar pulidas primero y qué cuentas externas hay que conseguir.
- **Opciones:**
  - Preparar los cuatro tipos de caso con problema y resolver uno en vivo
  - Preparar uno o dos casos con problema y mostrarlos sin resolverlos en vivo
  - Mostrar solo el camino feliz y evidenciar los estados de problema con capturas
  - Datos semilla: Canvas de prueba con 2 secciones, ~10 estudiantes y 1 group set, con cuentas GitHub del equipo
- **Estudio de APIs:** §13 recomienda "dejen visible un caso con problema" y propone un guion de ~6 min; §5.6 muestra una tabla de estados con ejemplo de cada tipo; §13 hito 1 pide Canvas de pruebas con 2 secciones, ~10 estudiantes y 1 group set.
- **Fusiona:** P642, P629

### Q-3.1-15 — En la demo presencial, ¿se mostrará el lado Canvas y GitHub en vivo (pestañas abiertas con el curso de Canvas y la organización) para que el profesor verifique que los repositorios, colaboradores y mensajes existen realmente, o solo la UI de la app? ¿Qué cuentas deben estar logueadas simultáneamente en el navegador de la demo y en qué perfiles o ventanas separadas?

- **Requisitos:** R2.1.6, R2.3.9, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Define el guion y el estado previo del navegador, y determina si la integración se percibe como real o simulada.
- **Opciones:**
  - Mostrar en vivo app + Canvas + GitHub con varias cuentas logueadas en perfiles separados
  - Mostrar solo la UI de la app y evidenciar el lado externo con capturas
  - Mostrar app + GitHub en vivo y Canvas solo si el tiempo del slot lo permite
- **Estudio de APIs:** §13 el guion incluye "abrir un repo en GitHub" y "mostrar el mensaje que le llegó al estudiante en Canvas".
- **Fusiona:** P638

### Q-3.1-16 — ¿En la demo del 16-sep los repositorios se crearán EN VIVO (esperando el ciclo del worker) o se mostrarán ya creados antes de la presentación? Con cron de aprovisionamiento cada 2 min y sincronización de Canvas cada 10 min, ¿la demo acepta esas esperas o se exige que los intervalos sean configurables por entorno (p. ej. 15 s en demo, 2 min en producción)? ¿Existirá un botón "procesar ahora"/"sincronizar ahora" y cómo se concilia con R2.3.10 ("sin interacción directa de un usuario")? ¿La UI mostrará un indicador de "próxima ejecución en X s" y cuánto debe durar el flujo completo en la demo?

- **Requisitos:** R2.3.7, R2.3.10, R2.3.11, R2.4.4
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Fija los intervalos del cron, la existencia de un disparador manual y de un indicador de UI, y define el ritmo del guion: minutos de silencio frente al profesor son un riesgo de usabilidad evaluado.
- **Opciones:**
  - Todo en vivo con intervalo corto configurable por entorno
  - Pre-creado + un caso nuevo en vivo
  - Pre-creado + video de respaldo
  - Intervalos fijos de producción + botón "sincronizar ahora" visible
  - Intervalos configurables + indicador "próxima ejecución en X s" sin disparador manual
- **Estudio de APIs:** §5.5 propone cron cada 2 min y throttle ~1 repo cada 3 s; §12 fija intervalos (sync 10 min, provision 2 min, snapshots 5 min, backfill 15 min); §7.4 sugiere botón "sincronizar ahora" para "corregir la percepción de datos viejos durante la demo"; §13 propone que "el worker crea los repos en vivo".
- **Fusiona:** P628, P643

## Casos borde, concurrencia y recuperacion

### Q-3.1-17 — Además de los casos con problema de mapeo estudiante↔GitHub, ¿qué fallos de VINCULACIÓN se prepararán para que el evaluador los provoque o los vea en la demo del 16-sep: elegir un curso de Canvas donde el usuario no es profesor, instalar la App de GitHub en la cuenta personal en vez de en una organización, cancelar la instalación a mitad de camino, organización donde la App fue desinstalada, rechazar el consentimiento de Canvas? ¿Cada uno muestra el ítem rojo del checklist con acción correctiva y se recupera sin tener que recrear el curso?

- **Requisitos:** R2.1.4, R2.1.5, R2.1.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** La "guía adecuada" de R2.1.6 se evalúa sobre todo en los caminos de error, no en el camino feliz.
- **Opciones:**
  - Preparar 2–3 fallos de vinculación reproducibles en vivo
  - Solo camino feliz + fallos de mapeo
  - Preparar los cinco fallos enumerados, cada uno con ítem rojo en el checklist y acción correctiva documentada
- **Estudio de APIs:** §3.3 propone el checklist con botón reintentar y §13 sugiere dejar visible un caso con problema, pero solo de mapeo de estudiantes.
- **Fusiona:** P641

### Q-3.1-18 — Si varios revisores usan la misma cuenta o el mismo curso demo en paralelo, ¿cómo se evita que se pisen entre sí (crear tareas duplicadas, retirar al único ayudante, generar decenas de repositorios en la organización, desvincular el Canvas)? ¿Habrá un curso demo "de exhibición" con datos ricos y otro "sandbox" para que el revisor cree cosas? ¿El sandbox se resetea por seed cada noche o bajo demanda, y quién ejecuta ese reset?

- **Requisitos:** R2.1.3, R2.1.9, R2.3.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define la política de seeds y reset, los permisos del usuario demo y si hace falta un procedimiento de restauración documentado.
- **Opciones:**
  - Curso "de exhibición" de solo lectura + curso "sandbox" escribible
  - Un único curso demo con reset por seed programado cada noche
  - Un único curso demo con reset bajo demanda ejecutado por un responsable del equipo
  - Una cuenta demo distinta por revisor
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P633

## Ya respondidas por el enunciado

Ninguna. En la etapa de verificacion las 23 preguntas de entrada de esta area (22 del archivo de consolidacion + N006 de la ronda critica) quedaron marcadas ABIERTA o ABIERTA/BLOQUEA; el enunciado no responde textualmente ninguna de ellas, por lo que no se aparto ninguna del cuerpo del documento.
