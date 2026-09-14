# Preguntas de alcance — Area proceso

27 preguntas finales, fusionadas desde 35 de entrada, 9 bloqueantes para la parcial.

## Organizacion del equipo, cierre de decisiones y planificacion

### Q-proceso-01 — ¿Cuántos integrantes tiene el equipo y qué roles se asignan explícitamente, incluyendo un responsable único de las dependencias externas y otro de la disponibilidad de la URL después de cada entrega?

- **Requisitos:** —
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Los requisitos de la parcial dependen de tareas de infraestructura y de trámites externos que nadie asume "por defecto"; sin nombres asignados quedan sin dueño hasta el día de la demo.
- **Opciones:**
  - Roles fijos por área: integración Canvas, integración GitHub/worker, frontend/UX, infraestructura/deploy/secretos, spec/QA/documentación, demo/video
  - Roles rotativos por hito o por semana
  - Sin roles formales, asignación tarea por tarea
  - Roles fijos más un responsable único declarado de dependencias externas (Developer Key, organización de GitHub, cuentas de prueba) y un responsable de mantener viva la URL entregada
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P761

### Q-proceso-02 — ¿Quién decide las respuestas a este banco de preguntas de alcance, dónde se registran, con qué fechas de corte y de congelamiento, y quién responde por cada dependencia externa con fecha de "listo"?

- **Requisitos:** R2.1.1, R2.7.7, Sección 3.1, Sección 3.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Sin proceso de cierre las preguntas quedan abiertas y alguien "rellena huecos" implícitamente; sin fecha de congelamiento de stack y responsables por dependencia, el spec no puede fijar requisitos no funcionales ni cerrarse.
- **Opciones:**
  - Formato del registro: decision log con id, fecha, responsable, requisitos afectados y criterio de aceptación resultante
  - Trazabilidad: el spec cita cada decisión (pregunta → decisión → requisito) / no la cita
  - Fechas de corte separadas para decisiones que afectan la parcial y para las que afectan la final / una sola fecha de corte
  - Fecha de congelamiento de decisiones de stack, hosting, base de datos y cola (p. ej. 9-sep) / sin fecha de congelamiento
  - Responsable con fecha de "listo" por dependencia externa: Developer Key de Canvas, GitHub App/organización, proyecto Google, proveedor de email, cuenta de hosting
  - Procedimiento definido para cuando una verificación empírica posterior contradice el supuesto de una decisión ya tomada (reapertura formal, nueva entrada en el log, sin procedimiento)
- **Estudio de APIs:** §13 y §14 proponen plan e hitos por día (Día 1: Canvas de pruebas, Developer Key, GitHub App) pero no un proceso de decisión, ni un registro de decisiones de alcance, ni responsables asignados.
- **Fusiona:** P765, P774

### Q-proceso-03 — ¿Cuál es el canal oficial para resolver con el profesor del ramo las preguntas de alcance que dependen de él, quién las consolida y envía, con qué fecha límite y cómo se registran las respuestas?

- **Requisitos:** R2.1.4, R2.2.4, R2.3.10, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Una fracción grande de las decisiones abiertas son dependencias externas del profesor; sin canal, responsable y fecha límite se responden por omisión, y sin registro no se pueden citar como justificación durante la validación individual del 7-oct.
- **Opciones:**
  - Canal: correo al profesor / foro o discusión de Canvas del ramo / consulta en clase / horario de ayudantía / combinación
  - Consolidación: un integrante único envía una lista consolidada / cada integrante consulta lo suyo
  - Fecha límite de envío para que las respuestas alcancen a influir en la parcial (16-sep) y en la final (6-oct)
  - Registro: captura del mensaje más entrada en el decision log / solo captura / sin registro formal
  - Preguntas a incluir: interpretación de "la creación de repositorios no deberá depender de una acción del estudiante"; uso o no del curso real de ICC4201; si acepta que el calificador registrado en Canvas sea siempre el profesor; si tener cuenta de GitHub es obligatorio para los estudiantes; pauta de evaluación; formato de la actividad del 7-oct; acceso a la instancia institucional y a la Developer Key
- **Estudio de APIs:** No lo aborda: el estudio identifica dependencias externas (Developer Key, organización, cuentas) pero no define cómo ni cuándo se consultan.
- **Fusiona:** N016

### Q-proceso-04 — ¿Cuáles son los hitos internos con fecha para la parcial y para la final, y se adopta el plan día a día del §13 del estudio o se redefine uno propio?

- **Requisitos:** —
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** El spec de proceso necesita un cronograma verificable; el plazo hasta la parcial obliga a decidir qué se ataca primero (dependencias externas o desarrollo).
- **Opciones:**
  - Adoptar el plan día a día del §13 tal cual
  - Redefinir un cronograma propio con hitos y fechas
  - Sin hitos internos formales, solo las fechas externas (16-sep, 6-oct, 7-oct)
  - Hitos candidatos para la parcial: dataset de Canvas listo, GitHub App probada, primer deploy, código congelado, ensayo general
  - Hitos candidatos para la final: fin de desarrollo, congelamiento para el video, deploy final, prueba con revisor externo, simulacro de validación individual
- **Estudio de APIs:** §13 propone 10 hitos con días (Día 1 a Día 7) para la parcial.
- **Fusiona:** P760

### Q-proceso-05 — Sin punto base y con 20 días entre entregas, ¿cuál es el orden de prioridad de las secciones 2.4–2.7 para la final, qué elementos se declaran "recortables" si falta tiempo y qué criterio ordena esa lista?

- **Requisitos:** R2.4.3, R2.5.9, R2.6.7, R2.7.5, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Fija el backlog ordenado y evita decidir bajo presión el 4 de octubre qué queda fuera.
- **Opciones:**
  - Criterio de ordenamiento: visibilidad en la revisión / riesgo técnico / dependencia externa / combinación ponderada
  - Candidatos a "recortable": extras de R2.5.9, comunicaciones automáticas R2.6.7, rúbrica embebida R2.7.5, OAuth de GitHub (§6.2), ruleset de tags
  - No declarar nada recortable y tratar las cuatro secciones como igualmente obligatorias
- **Estudio de APIs:** §8.5 sugiere elegir 2–3 extras para 2.5.9; §7.5 marca la ruleset de tags como no imprescindible.
- **Fusiona:** P759

## Alcance de cada entrega

### Q-proceso-06 — ¿R2.1.7–R2.1.9 (co-profesores, ayudantes, retiro) quedan fuera de la demo del 16-sep o el equipo los incluye, y los evaluadores entrarán al mismo curso demo cada uno con su propia cuenta?

- **Requisitos:** R2.1.7, R2.1.8, R2.1.9
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Determina el alcance de la parcial y si el link entregado por Canvas debe permitir a varios evaluadores (profesor y ayudantes de ICC4201) operar sobre el mismo curso, lo que exigiría que al menos la incorporación de co-profesores funcione el 16-sep.
- **Opciones:**
  - Incluir R2.1.7–R2.1.9 completas en la parcial
  - Dejarlas para la final y declararlo explícitamente en el spec como fuera del alcance de la parcial
  - Implementar solo la incorporación de co-profesores para que los evaluadores accedan al mismo curso, y postergar ayudantes y retiro
  - Que cada evaluador use un curso demo propio en lugar de compartir uno
- **Estudio de APIs:** §13 (plan y guion de demo) no incluye co-profesores ni ayudantes; el enunciado (§3.1) dice que el link debe poder ser utilizado por ayudantes y el profesor.
- **Fusiona:** P782

### Q-proceso-07 — ¿Qué comunicaciones deben mostrarse funcionando el 16-sep y cómo se evidenciará ante el evaluador que el mensaje llegó al estudiante, dado que la entrega por email depende de las preferencias de notificación de Canvas que la app no controla?

- **Requisitos:** R2.3.12, R2.6.5, R2.6.6, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija el alcance mínimo de comunicación exigible en la parcial y lo que se posterga a la final, y define expectativas realistas del guion de demo, porque Canvas no garantiza la entrega por email.
- **Opciones:**
  - Alcance en la parcial: solo el mensaje «repositorio disponible» vía Canvas (necesario para cerrar el flujo de R2.3.12) / también el recordatorio de mapeo faltante / además algún toggle de comunicación en la configuración de la tarea individual (R2.6.7)
  - Evidencia de recepción: iniciar sesión como estudiante de prueba y mostrar su bandeja / mostrar la bandeja de Conversations del profesor / mostrar el historial de envíos de la propia app / mostrar el correo recibido en la casilla del estudiante ficticio
  - Documentar como limitación explícita en el spec que la recepción por email depende de las preferencias de notificación del estudiante / no documentarlo
- **Estudio de APIs:** §13 hito 9 «Notificación al estudiante por Canvas» dentro del plan de la parcial y el guion de demo termina con «mostrar el mensaje que le llegó al estudiante en Canvas»; §1.2 recomienda Free-for-Teacher como entorno de demo.
- **Fusiona:** P779, P780

### Q-proceso-08 — ¿La ingesta de commits (webhook o polling) debe estar operativa desde la entrega parcial, aunque el dashboard no se demuestre el 16-sep, o se posterga a la segunda mitad?

- **Requisitos:** R2.5.2, R2.5.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Fija el alcance de la parcial y el plan de trabajo; decide si la infraestructura de workers se construye en la primera o en la segunda mitad y si habrá historial real acumulado para la final.
- **Opciones:**
  - Ingesta operativa desde la parcial, para acumular historial real hasta la final y detectar problemas temprano
  - Ingesta desplegada pero sin UI ni demostración el 16-sep
  - Postergar la ingesta a la final; en la parcial solo se muestra el estado de creación de repositorios
- **Estudio de APIs:** §13 (plan de la parcial) no incluye la ingesta de commits; §8 la ubica implícitamente para la final.
- **Fusiona:** P776

### Q-proceso-09 — ¿El equipo evalúa LTI 1.3 y GitHub Classroom como alternativas a la estrategia de enrolamiento elegida, y documenta la comparación y la justificación en un ADR?

- **Requisitos:** R2.1.4, R2.2.4, R2.2.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** El enunciado deja la estrategia de enrolamiento al equipo y evalúa su usabilidad; el examinador del 7-oct puede preguntar por qué no se usó LTI 1.3 (un enlace dentro de Canvas que identifica al estudiante sin que use la app) ni GitHub Classroom (que ya hace roster más creación de repos).
- **Opciones:**
  - ADR de justificación sin implementar LTI
  - Explorar LTI 1.3 si el administrador puede emitir la LTI Developer Key en la instancia disponible
  - Fuera de alcance sin documentación
  - Evaluar GitHub Classroom explícitamente y documentar el motivo del descarte junto con la alternativa elegida (tarea de Canvas, magic link, OAuth)
- **Estudio de APIs:** §0 y §6 afirman que no existe puente Canvas↔GitHub y proponen tarea de Canvas más OAuth opcional (§6.2); no evalúan LTI 1.3 ni GitHub Classroom.
- **Fusiona:** P778

## Datos de demostracion, cuentas y entorno de prueba

### Q-proceso-10 — ¿Cuál es el dataset de demostración concreto en Canvas para la parcial y para la final, qué casos borde deliberados incluye, existe un script de seed/reset y cuántos ensayos completos cronometrados se harán sobre el entorno real?

- **Requisitos:** R2.2.1, R2.2.2, R2.2.3, R2.2.4, R2.2.6, R2.3.9, R2.3.11, R2.4.2, R2.4.3, Sección 3.1
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** El dataset define qué estados de la tabla R2.3.11 y del panel R2.2.6 se pueden mostrar; sin casos borde cargados esas funcionalidades no son "accesibles en el uso", y sin reset se corre el riesgo de un 422 "name already exists" en pleno ensayo.
- **Opciones:**
  - Composición: cantidad de estudiantes ficticios, número de secciones, group sets y grupos, y tareas con overrides por sección e individuales
  - Casos borde candidatos: estudiante en dos secciones; estudiante sin grupo; estudiante retirado o inactive; Test Student de Canvas; estudiante que entregó un usuario de GitHub inexistente o el nombre de una organización; grupo modificado después de crear los repos; tarea de Canvas eliminada tras vincularla
  - Estados de repositorio a exhibir: invitación aceptada, invitación pendiente, usuario inexistente
  - Script de seed/reset que devuelva la base de datos y la organización de GitHub (borrando repos de demo) al estado inicial antes de cada ensayo / reset manual / sin reset
  - Número de ensayos completos cronometrados sobre el entorno que se usará el día de la demo
- **Estudio de APIs:** §13 hito 1 sugiere 2 secciones, ~10 estudiantes, 1 group set y 2 assignments con overrides, y "dejen visible un caso con problema"; §4.1 advierte filtrar el Test Student; Apéndice A.7 pide probar la precedencia de overrides con un caso real.
- **Fusiona:** P753, P769

### Q-proceso-11 — ¿Cómo se crean los estudiantes ficticios en Canvas, puede el equipo iniciar sesión como ellos y cuántas cuentas se necesitan?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.12
- **Tipo:** dependencia_externa · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** En Free-for-Teacher cada estudiante invitado necesita un correo real que acepte la invitación; sin poder entrar como estudiante no se puede demostrar el enrolamiento (R2.2.4/R2.2.5) ni la recepción de la notificación (R2.3.12) desde el lado de Canvas durante la demo.
- **Opciones:**
  - Crear N cuentas de correo nuevas o alias del tipo usuario+n@dominio
  - Usar los correos de los integrantes del equipo
  - Pedir cuentas de prueba al administrador institucional
  - Usar la función "act as"/masquerade de Canvas si el administrador la habilita, sin cuentas de correo propias
  - Definir el número mínimo de cuentas necesarias para demostrar la entrega del usuario de GitHub vía tarea de Canvas y la recepción del mensaje o comentario
- **Estudio de APIs:** §6.1 asume que los estudiantes entregan su usuario en una tarea de Canvas; no aborda cómo se crean las cuentas de estudiante de prueba.
- **Fusiona:** P754

### Q-proceso-12 — ¿Cuántas cuentas de GitHub de "estudiante" se necesitan, de dónde salen y cómo se generará la actividad de commits distribuida en el tiempo que exige el dashboard y el timeline?

- **Requisitos:** R2.2.4, R2.3.9, R2.5.2, R2.5.4, R2.5.8
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Determina cuántos repositorios pueden llegar al estado READY y cuánta actividad real habrá para demostrar la sección 2.5; sin varios usuarios distintos haciendo commits en un mismo repo grupal, R2.5.4 y R2.5.8 no se pueden evidenciar.
- **Opciones:**
  - Origen de las cuentas: cuentas personales de los integrantes / cuentas secundarias (los Términos de GitHub limitan a una cuenta gratuita por persona) / cuentas de terceros que colaboren / cuentas "machine user"
  - Usos que deben cubrir: validar mapeos con GET /users, aceptar invitaciones a repos (pasar de 201 invitación pendiente a acceso efectivo), y producir commits que alimenten dashboard y timeline
  - Generación de actividad: script de commits sintéticos con fechas distribuidas / commits manuales durante las semanas previas / commits con distintos user.email sin cuenta de GitHub asociada, para exhibir el caso de autor no atribuido
  - El spec de datos de demo lista las cuentas y quién las controla / no las lista
- **Estudio de APIs:** §5.4 explica 201 (invitación pendiente) vs 204 (acceso inmediato); §6.4 sugiere invitar a la organización para simplificar estados; §13 plantea un Canvas de pruebas con estudiantes y overrides pero no datos de commits en GitHub.
- **Fusiona:** P755, P775

### Q-proceso-13 — ¿Cuál es el catálogo cerrado de casos con problema que se sembrarán y se mantendrán vivos en el curso demo para las secciones 2.4 a 2.7, quién prepara cada uno, cómo se documenta en el guion entregado a los revisores y cómo se restaura si un revisor lo "arregla" durante su sesión?

- **Requisitos:** R2.1.9, R2.3.11, R2.4.5, R2.4.7, R2.5.4, R2.6.2, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cada caso sembrado obliga a definir en el spec el estado de UI, el texto y la acción correctiva correspondientes; sin catálogo, las secciones 2.4–2.7 solo se pueden mostrar en su camino feliz y los estados de excepción quedan sin requisito ni dato que los demuestre.
- **Opciones:**
  - Candidatos a decidir uno por uno: entrega cerrada con snapshot NO_COMMITS; snapshot en ERROR; estudiante con extensión individual todavía abierta mientras el resto ya cerró; sección con fecha distinta; fecha cambiada en Canvas después de capturar la versión; commits no atribuidos por email desconocido; repositorio con force-push posterior al cierre; comunicación fallida visible en el historial de envíos; nota rechazada por Canvas; entrega sin corrector asignado junto a otras asignadas; ayudante retirado con correcciones pendientes
  - Preparación: un responsable único siembra todos los casos / cada dueño de sección siembra los suyos
  - Documentación: guion de prueba entregado a los revisores que nombra cada caso y dónde verlo / solo lista interna
  - Restauración: script de re-siembra ejecutable entre sesiones de revisión / re-siembra manual / los casos se declaran no restaurables
- **Estudio de APIs:** §13 solo recomienda "dejar visible un caso con problema" de repositorios para el 16-sep; no propone equivalentes para fechas, snapshots, monitoreo, comunicaciones ni corrección.
- **Fusiona:** N008

### Q-proceso-14 — ¿La aplicación tendrá un reloj inyectable o un modo de simulación de tiempo para probar y demostrar cierres, recordatorios e informes sin esperar días reales, y qué se usará para provocar un cierre frente al revisor?

- **Requisitos:** R2.3.10, R2.4.5, R2.6.1, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Sin control del tiempo, gran parte de 2.4–2.6 (cierre de entregas y captura, recordatorios de 48 h, informe diario, "N días sin actividad", cambio de horario) no se puede probar ni demostrar de forma repetible.
- **Opciones:**
  - Reloj inyectable por entorno (variable de entorno, solo en entornos no productivos)
  - Solo fechas históricas más tiempo real, apoyándose en que el job barre todo lo vencido y no capturado
  - Endpoint administrativo "ejecutar job X como si fuera la fecha Y", disponible solo fuera de producción
  - Endpoint administrativo disponible también en producción, protegido, para usarlo en la demo del 6-oct
- **Estudio de APIs:** §7.5 señala que el job captura "todo lo vencido y no capturado", lo que permite pruebas con fechas pasadas; no aborda simulación de tiempo ni pruebas de jobs.
- **Fusiona:** P777

## Practicas de ingenieria, calidad y documentacion

### Q-proceso-15 — ¿Cuál es la definición de "hecho" para cada requisito R2.x.y, en qué formato se escriben los criterios de aceptación y se mantiene una matriz de trazabilidad requisito → pantalla → criterio → estado que pueda entregarse a los revisores como guion de prueba?

- **Requisitos:** —
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Alinea la regla del enunciado ("las funcionalidades a las que no se puede acceder en el uso no se consideran cumplidas") con el cierre de tareas del equipo, y da a los revisores un camino explícito para encontrar cada funcionalidad.
- **Opciones:**
  - Elementos candidatos de la definición de hecho: accesible desde la UI desplegada en la URL oficial sin tocar base de datos ni consola; demostrable con los datos de demo; estados de error y vacío visibles; criterio de aceptación escrito en el spec y verificado por otro integrante; documentado para la validación individual; prueba automatizada
  - Formato de los criterios: Given/When/Then / checklist por pantalla / prosa libre
  - Matriz de trazabilidad requisito → pantalla → criterio → estado (hecho/parcial/fuera de alcance), entregada o no a los revisores como guion de prueba
- **Estudio de APIs:** §11 ofrece una matriz requisito → endpoints que puede servir de base para la trazabilidad; no aborda la definición de hecho ni el formato de criterios.
- **Fusiona:** P758, P764

### Q-proceso-16 — ¿Qué criterios de aceptación de usabilidad medibles fija el equipo para la evaluación de "facilidad de uso y guía adecuada"?

- **Requisitos:** R2.1.6, R2.3.11
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Convierte "facilidad de uso" en criterios verificables que se pueden incluir en el spec y usar como checklist de QA antes de la demo.
- **Opciones:**
  - Máximo de pantallas o pasos para el flujo registro → repositorios creados
  - Tiempo objetivo para un profesor nuevo sin ayuda (p. ej. menos de 10 minutos)
  - Una prueba de usabilidad con un usuario externo (un ayudante real) antes del 16-sep
  - "Cero callejones sin salida": toda pantalla de error o vacío ofrece al menos una acción
  - Toda acción en background muestra estado y última ejecución
  - No fijar criterios medibles y evaluar la usabilidad cualitativamente
- **Estudio de APIs:** No lo aborda; solo sugiere elementos puntuales de usabilidad (checklist verde/rojo, última sincronización, botón reintentar).
- **Fusiona:** P781

### Q-proceso-17 — ¿Qué niveles de test son obligatorios, se corren tests de contrato contra las APIs reales en CI o solo manualmente, y hay cobertura mínima exigida y quién la revisa?

- **Requisitos:** R2.2.4, R2.3.7, R2.3.8, R2.4.3
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Sin mocks, los tests dependen de instancias reales y consumen rate limit; la lógica de fechas y de nombres es donde se pierden puntos y sobre la que se pregunta el 7-oct.
- **Opciones:**
  - Unitarios para lógica pura: fecha efectiva con overrides, parser de login de GitHub, sanitización de nombres de repositorio, máquina de estados
  - Integración contra mocks HTTP de Canvas/GitHub (nock/msw/responses) con fixtures grabadas de la API real
  - e2e con Playwright sobre la UI
  - Tests de contrato contra las APIs reales: en CI con secretos / solo manualmente / no se hacen
  - Cobertura mínima exigida (porcentaje y responsable de revisarla) / sin umbral de cobertura
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P766

### Q-proceso-18 — ¿Habrá CI con checks obligatorios en cada PR, deploy automático o manual a producción, entorno de staging y ventana de congelamiento de deploys antes de cada entrega?

- **Requisitos:** Sección 3.1, Sección 3.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Define el flujo diario del equipo, evita el deploy roto la noche anterior y decide si se necesita un segundo entorno con su costo asociado.
- **Opciones:**
  - CI con GitHub Actions ejecutando lint/format (ESLint+Prettier o ruff+black), tests y build en cada PR como checks obligatorios (ilimitado en repositorio público, 2.000 min/mes en privado) / CI sin checks bloqueantes / sin CI
  - Deploy a producción automático al mergear a main / manual con aprobación
  - Entorno de staging con deploy automático de la rama de desarrollo / sin staging
  - Ventana de congelamiento de deploys antes del 16-sep y del 6-oct (p. ej. 24 h) / sin ventana
- **Estudio de APIs:** §13 hito 10: "nunca deployen la noche anterior".
- **Fusiona:** P767

### Q-proceso-19 — ¿Qué modelo de ramas, política de PRs y convenciones se adoptan, el repositorio del proyecto es público o privado, quién se agrega como colaborador y se exige que cada integrante haya tocado cada módulo?

- **Requisitos:** Sección 3.2, Sección 4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** La revisión individual del 7-oct penaliza no conocer el código y el flujo de PRs con revisión es el mecanismo para distribuir ese conocimiento; público o privado afecta los minutos de CI y la exposición de secretos.
- **Opciones:**
  - Modelo de ramas: trunk-based con ramas cortas / GitFlow / commits directos a main
  - PRs obligatorios con al menos un revisor distinto del autor y protección de main / PRs opcionales
  - Convenciones: Conventional Commits, nombres de ramas e issues, uso de GitHub Projects / sin convenciones formales
  - Repositorio público o privado; colaboradores a agregar (profesor, ayudantes del curso, nadie)
  - Exigir que cada integrante haya tocado cada módulo / rotación de revisores / sin exigencia
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P768

### Q-proceso-20 — ¿Se diseña y migra el esquema de datos completo antes del 16-sep aunque solo se implementen 2.1–2.3, qué tablas y columnas se declaran congeladas tras la parcial y cuál es la política de migraciones posteriores?

- **Requisitos:** R2.4.5, R2.5.2, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** Determina el orden del trabajo de la primera semana y si el curso demo de la parcial puede reutilizarse en la final sin volver a sembrar los datos, evitando migraciones destructivas sobre datos que siguen vivos.
- **Opciones:**
  - Esquema completo desde el inicio (incluidos snapshots, commits, agregados, membresías temporales, outbox y corrección)
  - Incremental con migraciones solo aditivas (expand–contract) y lista explícita de tablas y columnas congeladas tras la parcial
  - Incremental aceptando un reseed completo antes de la final
- **Estudio de APIs:** §12 da la arquitectura mínima; §5.2 y §8.3 dan modelos parciales; no aborda la evolución del esquema.
- **Fusiona:** P783

### Q-proceso-21 — ¿Cómo se interpreta "de uso libre y gratuito" respecto de licencias de librerías y de servicios SaaS, y se genera un inventario de licencias para la entrega?

- **Requisitos:** Sección 4
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Es un criterio explícito del enunciado; una dependencia con licencia incompatible o un servicio pago podrían cuestionarse en la corrección.
- **Opciones:**
  - Licencias aceptadas: solo permisivas (MIT/Apache/BSD) / también copyleft (GPL/AGPL)
  - Servicios SaaS con free tier (hosting, email, Sentry, Google OAuth) aceptados o no
  - Un plan de pago mínimo de hosting: aceptable / no aceptable / a consultar con el profesor
  - Inventario de licencias generado con license-checker o pip-licenses y entregado / sin inventario
  - Verificación de la licencia de fuentes tipográficas, íconos y componentes de UI / sin verificación
- **Estudio de APIs:** §12 presenta el "Stack sugerido (libre según el enunciado)"; no analiza licencias ni servicios.
- **Fusiona:** P770

### Q-proceso-22 — ¿Qué documentación se exige entregar: README con instalación local, .env.example, pasos para crear las credenciales externas, runbook operativo y ADRs de las decisiones de infraestructura?

- **Requisitos:** Sección 3.3, Sección 4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** La validación individual del 7-oct descuenta hasta 3 puntos por no conocer el proyecto; los ADRs y el runbook son la forma barata de distribuir ese conocimiento entre los integrantes.
- **Opciones:**
  - README con instalación local y .env.example
  - Pasos documentados para crear la GitHub App, la Developer Key de Canvas y el cliente de Google
  - Runbook operativo: reiniciar worker, rotar secreto, restaurar backup, agregar usuario de prueba de Google, reenviar webhook
  - ADRs cortos por decisión de infraestructura para que cada integrante pueda defenderlas el 7-oct
  - Solo README mínimo, sin runbook ni ADRs
- **Estudio de APIs:** §14 lista preguntas probables del 7-oct con sus respuestas; no propone documentación producida por el equipo.
- **Fusiona:** P773

## Ejecucion de la demo, entrega y recuperacion

### Q-proceso-23 — ¿La demo del 16-sep se ejecuta contra la producción desplegada o desde localhost, con qué congelamiento y precalentamiento, y qué commit o tag corresponde a cada entrega y hasta cuándo se congela el deploy?

- **Requisitos:** Sección 3.1, Sección 3.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Garantiza que lo revisado es lo entregado y evita el deploy roto de última hora y el arranque en frío frente al profesor; el tag permite volver a la versión demostrada si algo se rompe durante la ventana de dos semanas.
- **Opciones:**
  - Entorno de la demo: la producción desplegada en la misma URL entregada por Canvas / localhost / localhost con túnel
  - Congelamiento del código 24 h antes con prohibición de deploys / sin congelamiento
  - Precalentamiento de la instancia (ping minutos antes) para evitar el cold start / sin precalentamiento
  - Tags de entrega: git tag entrega-parcial y entrega-final, con el deploy congelado en ese tag hasta terminar la revisión / sin tags
  - Después del 6-oct: se permite seguir mergeando a main mientras la URL sigue viva / se congela main hasta el término de la ventana de dos semanas
- **Estudio de APIs:** §13 hito 10: "Deploy con URL pública el día 6; nunca deployen la noche anterior".
- **Fusiona:** P763, P772

### Q-proceso-24 — ¿Quién presenta, quién opera el teclado, quién juega el rol de estudiante y desde qué cuentas durante la demo, quién registra el feedback de los evaluadores y cómo se convierte ese feedback en backlog priorizado?

- **Requisitos:** —
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** El guion del spec debe listar actores, cuentas y pasos, y el ensayo detecta tiempos muertos del worker antes del día; sin responsable ni formato de registro, el feedback del evaluador —el mejor predictor de lo que revisará el 6-oct— se reconstruye de memoria días después.
- **Opciones:**
  - Presentación: un presentador único / rotación por etapa del flujo / todos participan
  - Roles simultáneos asignados: quien opera el teclado, quien juega el rol de estudiante en Canvas/GitHub en paralelo, quien toma notas
  - Cuentas a usar en vivo: profesor demo, estudiante demo de Canvas, GitHub del estudiante
  - Ensayo general cronometrado completo, con fecha fijada / sin ensayo
  - Formato del registro de feedback: frases textuales, requisito afectado, si fue bloqueante o cosmético, si el evaluador se salió del guion y qué encontró
  - Pedir feedback abierto al terminar la demo ("¿qué le costó entender?") / no pedirlo
  - Reunión del equipo dentro de las 24 horas siguientes para reordenar prioridades y decidir qué preguntas de alcance quedaron respondidas por el evaluador / revisión diferida
- **Estudio de APIs:** §13 propone un guion de demo pero no asigna roles ni contempla la captura del feedback recibido.
- **Fusiona:** P756, N017

### Q-proceso-25 — ¿Cuál es el plan de contingencia de la demo presencial ante cada modo de falla, quién lo ejecuta y cuánto tiempo se tolera perder antes de activarlo?

- **Requisitos:** Sección 3.1, R2.1.4, R2.1.5, R2.3.7, R2.3.12
- **Tipo:** decision_equipo · **Entrega:** parcial · **Bloquea la parcial:** no
- **Por que importa:** La entrega parcial se evalúa en vivo; el plan B debe estar definido, ensayado y con roles asignados, no improvisado, y define artefactos que hay que producir antes del 16-sep.
- **Opciones:**
  - Modos de falla a cubrir uno por uno: red del aula caída, Canvas institucional caído, incidente de GitHub, Google OAuth caído, hosting dormido o caído, respuestas 5xx, rate limit agotado
  - Respuestas candidatas: hotspot móvil; correr localmente con túnel (ngrok/cloudflared) desde un notebook; segundo curso demo precargado; instancia Free-for-Teacher como Canvas alterno; segunda cuenta o proveedor de hosting con la misma imagen; login alternativo (token manual de Canvas, usuario local de emergencia) tras flag; snapshot de base de datos restaurable a un estado pre-demo; video grabado del flujo completo como último recurso
  - Responsable asignado por cada plan B y umbral de tiempo perdido que dispara su activación
  - Sin plan de contingencia formal
- **Estudio de APIs:** §1.2 propone el token manual como plan B; §8.1 menciona ngrok/cloudflared para localhost pero recomienda desplegar temprano; §13 insiste en el deploy temprano; no aborda contingencias presenciales.
- **Fusiona:** P757, P771

### Q-proceso-26 — ¿Se tomará un respaldo de la base de datos y de la lista de repositorios de la organización inmediatamente antes de la demo del 16-sep y antes de la entrega del 6-oct, con procedimiento de restauración probado?

- **Requisitos:** —
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Permite volver a un estado conocido si una demo o un revisor rompe los datos durante la ventana de revisión.
- **Opciones:**
  - Respaldo antes de cada entrega con restauración probada al menos una vez / respaldo sin ensayo de restauración / sin respaldo
  - El seed reproducible parte de cero / incluye mapeos y repositorios ya creados
  - Alcance del respaldo: solo base de datos / base de datos más inventario de repositorios de la organización de GitHub
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P762

### Q-proceso-27 — ¿En qué estado queda el curso demo entre el 16-sep y el 6-oct respecto de los crons, las comunicaciones salientes, la suscripción de los revisores al informe diario y la conservación del dataset?

- **Requisitos:** R2.3.10, R2.4.5, R2.6.1, R2.6.3, R2.6.4, R2.6.5, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Obliga a definir un estado de curso o un interruptor global de salida que hoy no está en ningún requisito, y evita que el evaluador reciba veinte correos automáticos antes de la entrega final o encuentre el curso demo lleno de mensajes de prueba; también determina si el historial de commits del dashboard se acumula desde septiembre o se genera al final.
- **Opciones:**
  - Informe diario de las 07:00: los revisores quedan suscritos por defecto durante las tres semanas / se les suscribe recién antes de la final / se les pregunta su preferencia
  - Existe un estado "pausado" del curso o un interruptor de comunicaciones salientes que detiene mensajes, anuncios y correos sin borrar datos, con un responsable de activarlo / no existe tal interruptor
  - Durante el período se siguen enviando comentarios y Conversations a los estudiantes ficticios y anuncios al curso demo de Canvas / se detienen
  - El dataset del 16-sep se conserva como histórico (para que el dashboard tenga semanas de actividad real) / se resetea antes de la final
  - Los crons (aprovisionamiento, snapshots, sync de Canvas, informe diario) siguen corriendo / se detienen / se reducen a un subconjunto
- **Estudio de APIs:** No lo aborda: el estudio trata la operación continua (§9.1, §12) pero no el período entre entregas ni el efecto de los automatismos sobre los evaluadores.
- **Fusiona:** N010

## Ya respondidas por el enunciado

Ninguna de las 35 preguntas de entrada del area proceso quedo marcada como YA_RESPONDIDA en la etapa de verificacion: los 35 veredictos son ABIERTA o ABIERTA/BLOQUEA. El enunciado fija fechas externas (16-sep, 6-oct, 7-oct), la entrega del codigo por GitHub, la regla de correccion "las funcionalidades a las que no se puede acceder en el uso no se consideran cumplidas aunque esten en el codigo", la ausencia de punto base, la libertad de stack "mientras estas sean de uso libre y gratuito" y que "cada grupo debera definir una estrategia adecuada para realizar este proceso de enrolamiento", pero ninguna de esas frases responde de forma completa a alguna de las preguntas listadas arriba; todas quedan como decision del equipo o dependencia externa.
