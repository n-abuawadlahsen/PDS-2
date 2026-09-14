# Preguntas de alcance — Area 3.2-3.3-4

13 preguntas finales, fusionadas desde 14 de entrada (2 preguntas de origen unificadas en 1), 2 bloqueantes para la parcial, 0 apartadas por estar ya respondidas en el enunciado.

## Alcance evaluable: que debe poder ver y hacer un revisor con la herramienta

### Q-3.2-3.3-4-01 — ¿La aplicacion ofrecera a cualquier usuario recien registrado (incluidos el profesor y los ayudantes que entren con su propio Gmail durante las dos semanas posteriores a la entrega) un "curso de ejemplo" ya poblado —estudiantes, mapeos estudiante↔usuario de GitHub, repositorios, entregas cerradas con versiones capturadas, dashboard con semanas de actividad, timeline, correcciones y al menos un informe historico— que le permita evaluar los requisitos 2.4 a 2.7 sin tener un curso de Canvas con datos ni una organizacion de GitHub propia? Si la respuesta es si: ¿los datos son ficticios y estaticos, instanciados y aislados por usuario (de modo que un revisor no pueda dejarlos inservibles para el siguiente), o es el curso demo real compartido que cualquier revisor puede modificar? ¿Como se rotula que es un ejemplo y que acciones quedan bloqueadas dentro de el (enviar mensajes o correos reales, publicar notas en Canvas, crear repositorios reales)? Si la respuesta es no: ¿se acepta que un revisor que entre con su cuenta propia solo vea pantallas vacias y quede obligado a usar las credenciales demo entregadas junto al link?

- **Requisitos:** R2.1.3, R2.5.1, R2.5.10, R2.6.1, R2.7.2, R2.7.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El enunciado indica que las funcionalidades a las que no se puede acceder en el uso no se consideran cumplidas; un revisor sin curso de Canvas con datos ni organizacion de GitHub propia no veria dashboard, timeline, informes ni correccion aunque esten implementados. Ademas condiciona el modelo de datos (aislamiento por usuario, modo solo lectura), por lo que debe decidirse antes de construirlo.
- **Opciones:**
  - Seed ficticio y estatico, instanciado y aislado por usuario al registrarse, con acciones externas (correo, notas en Canvas, creacion de repos) bloqueadas y rotulo visible de "ejemplo"
  - Curso demo real compartido, visible para cualquier usuario registrado, asumiendo que un revisor pueda modificarlo o dejarlo inservible para el siguiente
  - Sin curso de ejemplo: el revisor con cuenta propia ve pantallas vacias y debe usar las credenciales demo entregadas junto al link
  - Enfoque mixto: curso de ejemplo de solo lectura para inspeccion mas credenciales demo para ejercer los flujos de creacion
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** N013

### Q-3.2-3.3-4-02 — Dado que "las funcionalidades a las que no se puede acceder en el uso no se consideran cumplidas", ¿la administracion de usuarios de tipo profesor que exige R2.1.1 (listar, desactivar, reactivar, eliminar) tendra una interfaz accesible para los revisores, con que credencial se accede (por ejemplo, una cuenta admin de demo entregada junto al link) y que salvaguardas se implementan para que un revisor no desactive o elimine al profesor demo cuyo token de Canvas sostiene los jobs automaticos? ¿O R2.1.1 se interpretara solo como registro y autoadministracion del perfil propio, dejandolo documentado asi en el spec?

- **Requisitos:** R2.1.1, R2.1.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define si existe una pantalla de administracion, con que credenciales se entrega a los revisores y cual es la interpretacion oficial de R2.1.1 frente al criterio de la seccion 4 del enunciado.
- **Opciones:**
  - UI de administracion completa mas credencial admin entregada a los revisores
  - UI de administracion visible solo para el equipo (no evaluable por el revisor)
  - R2.1.1 se interpreta como registro y perfil propio, sin pantalla de administracion
  - UI de administracion accesible al revisor pero con la cuenta del profesor demo protegida (no desactivable ni eliminable)
- **Estudio de APIs:** §3 y §11 marcan R2.1.1 como "App / BD ✅" sin describir pantallas ni rol admin.
- **Fusiona:** P656

### Q-3.2-3.3-4-03 — Dado que "lo no accesible en el uso no se considera cumplido", ¿como se hara visible en la revision de la final cada proceso automatico: (a) informe diario, ¿habra pagina de informes historicos y un boton "enviar ahora" disponible para el revisor?; (b) snapshot al cierre de una entrega, ¿se demuestra con entregas ya cerradas en el pasado mas una que cierre durante la ventana de revision?; (c) actualizacion de fechas, ¿el revisor cambia una fecha en Canvas y ve el cambio reflejado en la app, y con que mecanismo (boton de sincronizacion manual o espera al job periodico)?; (d) comunicaciones automaticas, ¿habra historial u outbox de envios?; (e) worker de creacion de repositorios, ¿habra log de actividad visible en la interfaz?

- **Requisitos:** R2.3.10, R2.4.4, R2.4.5, R2.6.1, R2.6.4, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Cada respuesta se traduce en pantallas adicionales (historial, log, boton "enviar ahora") y en fechas concretas del dataset demo. Sin ellas, procesos implementados pero invisibles pueden no considerarse cumplidos.
- **Opciones:**
  - Cada proceso automatico expone su propia pantalla de historial mas un disparador manual para ejecutarlo en vivo ante el revisor
  - Solo se exponen los resultados finales (informe, snapshot, mensaje enviado) sin historial ni disparadores manuales
  - Historial para los procesos con salida hacia el usuario (informe, comunicaciones) y log tecnico solo para el equipo (worker de repos)
  - Se decide caso por caso segun requisito, documentando en el spec que evidencia acredita cada proceso
- **Estudio de APIs:** §9.1 sugiere guardar cada informe como pagina web; §9.4 propone un outbox con pantalla de historial de comunicaciones; §7.4 propone un boton "sincronizar ahora".
- **Fusiona:** P651

## Datos y operacion del entorno de demostracion

### Q-3.2-3.3-4-04 — ¿Cual es el plan de datos del curso demo para que dashboards, timeline e informes tengan contenido durante la ventana de revision: (a) se generara actividad real en los repositorios demo durante las 3 semanas previas (commits desde cuentas de estudiante, en distintos dias y horas, con al menos un repositorio inactivo y al menos un integrante sin commits) o se importara historia sintetica mediante backfill con commits fechados?; (b) cuantos repositorios y cuantos commits se consideran suficientes y quien ejecuta ese calendario de actividad?; (c) con que fechas se configuran las entregas del curso demo: al menos una entrega ya cerrada con snapshot capturado, al menos una que cierre entre el 6 y el 20 de octubre para que el revisor vea la captura automatica y el aviso de proximidad, y tareas "activas" durante toda la ventana para que exista informe diario?; (d) quien mantiene vivo ese dataset durante las dos semanas posteriores a la entrega (reponer entregas activas, recrear fechas vencidas, verificar que sigue habiendo contenido)?

- **Requisitos:** R2.4.5, R2.4.6, R2.5.1, R2.5.2, R2.5.3, R2.5.4, R2.5.6, R2.5.7, R2.5.8, R2.5.10, R2.6.1, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.6.1 no emite informe si no hay tareas activas, y sin historia de commits los requisitos 2.5 se ven vacios ante el revisor. Define un plan con fechas, volumen de datos y responsables tanto para producir el dataset como para mantenerlo durante las dos semanas.
- **Opciones:**
  - Actividad real generada por el equipo con cuentas de estudiante segun un calendario asignado a un responsable
  - Historia sintetica cargada por backfill con commits fechados
  - Combinacion: base sintetica historica mas actividad real durante los dias previos y la ventana de revision
  - Dataset congelado sin mantenimiento posterior, asumiendo que las entregas venzan durante la ventana
  - Dataset con mantenimiento asignado a un responsable con revision periodica durante las dos semanas
- **Estudio de APIs:** §8.2 plantea backfill completo al ingresar un repositorio y §8.5 lista las metricas requeridas, pero no aborda como poblar datos de demo; §9.1 implementa literalmente "sin tareas activas no hay informe" y §7.5 describe el job que barre lo vencido y no capturado.
- **Fusiona:** P652, P653

### Q-3.2-3.3-4-05 — Durante las dos semanas posteriores a la entrega en que la URL debe estar disponible: ¿quien monitorea la disponibilidad (uptime check, alertas y con que frecuencia), quien esta autorizado a redeployar si el servicio cae, se congela el codigo o se permiten hotfixes durante la ventana y bajo que criterio, y como se evita que expiren o se invaliden las credenciales (refresh token de Canvas del profesor demo, instalacion de la GitHub App, API key del proveedor de correo)? ¿Se documentara un runbook de recuperacion y se ofrecera a los revisores un canal de soporte o de aviso de incidencias?

- **Requisitos:** R2.3.10, R2.4.5, R2.6.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Una caida durante la ventana de revision anula funcionalidades ya cumplidas. El spec debe fijar responsables, permisos de despliegue y procedimiento de recuperacion.
- **Opciones:**
  - Congelamiento total del codigo tras la entrega, con redeploy permitido solo para restaurar el servicio
  - Hotfixes permitidos bajo criterio acordado (solo caidas o errores que bloqueen la revision), con registro de cambios
  - Monitoreo automatico con alertas a un responsable de turno mas runbook escrito
  - Monitoreo manual por revision periodica del equipo, sin alertas automaticas
  - Con canal de soporte publicado a los revisores / sin canal de soporte
- **Estudio de APIs:** §1.1 explica que el refresh token permite ejecutar jobs sin el profesor conectado; §12 recuerda la exigencia de disponibilidad de dos semanas.
- **Fusiona:** P648

## Entregables de la seccion 3.2

### Q-3.2-3.3-4-06 — El codigo se entrega "por GitHub": ¿el repositorio sera publico o privado? Si es privado, ¿a que usuarios de GitHub del profesor y de los ayudantes hay que invitar, quien los solicita y en que fecha? ¿Que debe contener el repositorio al 6 de octubre: README con instrucciones de despliegue, .env.example, script de seed, diagrama de arquitectura, tag o release "entrega-final"? ¿Como se garantiza que no queden secretos en el historial (.pem de la GitHub App, client_secret, webhook secret): hook pre-commit, escaneo del historial, rotacion de credenciales expuestas?

- **Requisitos:** —
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el paquete de entrega de codigo y los controles que exige el proceso; un secreto commiteado es un hallazgo directo en la correccion.
- **Opciones:**
  - Repositorio publico
  - Repositorio privado con invitacion nominal al profesor y a los ayudantes en fecha acordada
  - Contenido minimo obligatorio definido y verificado por checklist antes del 6 de octubre
  - Control anti-secretos automatizado (pre-commit y escaneo del historial) / revision manual previa a la entrega
- **Estudio de APIs:** §14 advierte que un .pem commiteado es un hallazgo obvio en la correccion.
- **Fusiona:** P647

### Q-3.2-3.3-4-07 — Para el video de maximo 3 minutos: ¿que flujo se muestra y en que orden, que "virtudes principales" se destacan, se graba con el curso demo o con datos reales, quien graba, quien edita y quien narra, en que idioma, donde se aloja (YouTube no listado, Google Drive u otro) y cual es la fecha interna de corte para congelar la interfaz antes de grabar?

- **Requisitos:** —
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El video es un entregable evaluado y exige una interfaz congelada; el guion debe reflejar los requisitos priorizados y estar acordado antes de la grabacion.
- **Opciones:**
  - Guion escrito y aprobado por el equipo antes de grabar, con orden de flujos fijado
  - Grabacion sobre el curso demo / sobre datos reales de un curso propio
  - Alojamiento en YouTube no listado / Google Drive con enlace de acceso abierto / otro
  - Fecha interna de congelamiento de UI definida y comprometida / grabacion sobre la version del dia de la entrega
- **Estudio de APIs:** no lo aborda.
- **Fusiona:** P645

### Q-3.2-3.3-4-08 — ¿El curso define un formato para la declaracion de uso de IA (plantilla en Canvas, secciones obligatorias, entrega por integrante o por equipo) o lo define el equipo? ¿Se llevara desde ahora un registro por integrante de que herramientas de IA se usaron y para que (modulos afectados, prompts relevantes) de modo de completar la declaracion sin reconstruirla de memoria al final?

- **Requisitos:** —
- **Tipo:** dependencia_externa · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es un entregable obligatorio de la final y se relaciona directamente con la regla de que cada integrante debe ser dueño de su codigo.
- **Opciones:**
  - Consultar al profesor si existe plantilla o formato obligatorio antes de redactarla
  - Definir formato propio del equipo (secciones y nivel de detalle) sin consultar
  - Registro continuo por integrante desde ahora (herramienta, modulo, proposito) / reconstruccion al cierre
  - Declaracion unica por equipo / una declaracion por integrante
- **Estudio de APIs:** §14 solo recuerda que la declaracion esta pedida.
- **Fusiona:** P646

## Actividad de validacion individual del 7 de octubre y propiedad del codigo

### Q-3.2-3.3-4-09 — ¿Cual es el formato exacto de la actividad de validacion individual del 7 de octubre y se consultara al profesor antes de preparar al equipo: (a) entrevista oral uno a uno, prueba escrita o frente al computador con el codigo?; (b) si se pide leer, explicar, modificar o ejecutar codigo en vivo; (c) duracion por persona; (d) si se pregunta solo por lo que cada integrante escribio o por cualquier modulo del proyecto; (e) si se puede consultar documentacion propia durante la actividad? Segun la respuesta: ¿cada integrante debe tener el proyecto ejecutandose en su propia maquina ese dia (Docker, seed, .env, GitHub App de desarrollo, curso de Canvas de prueba, credenciales propias) o basta con la URL de produccion y el repositorio?

- **Requisitos:** —
- **Tipo:** dependencia_externa · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si hay que invertir en un entorno local reproducible por integrante, con credenciales propias de Canvas, GitHub y Google, y que documentacion interna se produce. El descuento es individual y llega hasta 3 puntos sobre la nota final.
- **Opciones:**
  - Consultar al profesor el formato y preparar segun la respuesta
  - Asumir el peor caso (modificar y ejecutar codigo en vivo) y exigir entorno local completo a cada integrante antes del 5 de octubre
  - Asumir formato oral y preparar solo documentacion y simulacro de preguntas
- **Estudio de APIs:** §14 lista preguntas probables del profesor y sus respuestas cortas, pero asume un formato oral y no aborda el formato real ni la necesidad de entorno local por integrante.
- **Fusiona:** N007

### Q-3.2-3.3-4-10 — ¿Que documentacion interna se producira para que todos los integrantes puedan explicar todo el proyecto el 7 de octubre: documento de arquitectura, ADRs con las decisiones tomadas (GitHub App vs PAT, SHA vs tag, polling vs webhook, precedencia de overrides, permisos push vs admin), guia por modulo, banco de preguntas probables con respuestas? ¿Quien la escribe, con que fecha de entrega interna y cuando se revisa en grupo?

- **Requisitos:** —
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El descuento de hasta 3 puntos es individual, por lo que estos artefactos deberian figurar en el spec de proceso como entregables internos con responsable y fecha.
- **Opciones:**
  - Set completo (arquitectura, ADRs, guia por modulo, banco de preguntas) con responsables y fechas internas
  - Solo banco de preguntas y respuestas cortas
  - Solo documento de arquitectura y ADRs, sin guia por modulo
  - Documentacion escrita por el autor de cada modulo / redactada por un responsable unico a partir de entrevistas
- **Estudio de APIs:** §14 propone una tabla de "preguntas probables" con respuestas breves y una lista de trampas a tener resueltas.
- **Fusiona:** P649

### Q-3.2-3.3-4-11 — ¿Que reglas de trabajo se adoptaran para asegurar que cada integrante conozca modulos que no escribio: rotacion de pares, revision obligatoria de cada PR por otro integrante que deba poder explicarlo, walkthroughs semanales, simulacro de validacion individual antes del 7 de octubre? ¿Se prohibira mergear codigo generado por IA que su autor no sea capaz de explicar, y como se verifica esa regla?

- **Requisitos:** —
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** La regla de 1.0 en el proyecto si un integrante no puede explicar como resolvio una situacion es un riesgo de nota mayor que cualquier requisito individual.
- **Opciones:**
  - Revision obligatoria de cada PR por otro integrante, con la condicion explicita de poder explicarlo
  - Rotacion de pares y walkthroughs semanales de modulos ajenos
  - Simulacro de validacion individual en fecha previa al 7 de octubre
  - Prohibicion explicita de mergear codigo de IA no explicable por su autor, con verificacion en la revision de PR
  - Sin reglas formales: cada integrante se prepara por su cuenta
- **Estudio de APIs:** §8.5 sugiere argumentos metodologicos para la defensa oral, pero no define proceso de equipo.
- **Fusiona:** P650

## Casos borde, limites y recuperacion del entorno

### Q-3.2-3.3-4-12 — Los revisores que creen tareas en el sandbox generaran repositorios reales en la organizacion de GitHub del equipo: ¿se permitira eliminar tareas y sus repositorios desde la app (el enunciado no lo pide), se limpiaran manualmente o se aceptara la acumulacion? ¿Como se comporta el sistema al recrear una tarea con el mismo nombre: reutiliza el repositorio existente, lo trata como exito idempotente o crea uno nuevo con sufijo? ¿Que se le muestra al usuario en ese caso?

- **Requisitos:** R2.3.7, R2.3.8
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** si
- **Por que importa:** Afecta el modelo de estados (repositorio existente encontrado vs creado), la politica de nombres inequivocos que exige R2.3.8 y la operacion del sandbox durante la ventana de revision.
- **Opciones:**
  - Eliminacion de tareas y repositorios desde la app, expuesta al usuario
  - Limpieza manual periodica del sandbox por el equipo, sin funcion en la app
  - Acumulacion aceptada sin limpieza durante la ventana de revision
  - Ante nombre repetido: reutilizar el repositorio existente y tratarlo como exito idempotente
  - Ante nombre repetido: crear un repositorio nuevo con sufijo numerico
  - Ante nombre repetido: rechazar la creacion y pedir un nombre distinto al usuario
- **Estudio de APIs:** §5.4 describe sanitizacion de nombres y sufijo -2 ante un 422; §5.5 trata el 422 "ya existe" como exito idempotente.
- **Fusiona:** P654

### Q-3.2-3.3-4-13 — ¿Se hara una prueba de carga realista antes del 6 de octubre (por ejemplo, 25 a 40 repositorios con 2 o 3 colaboradores y archivos base) para observar los limites secundarios de la API de GitHub (80 requests generadoras de contenido por minuto, 900 puntos por minuto) y validar el throttle del worker? ¿En que organizacion se ejecuta, quien la ejecuta y quien limpia los repositorios creados despues?

- **Requisitos:** R2.3.7, R2.3.10
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El dataset demo pequeño no revela los limites de la API; si el profesor prueba con un curso grande durante la ventana de revision, el worker debe comportarse correctamente.
- **Opciones:**
  - Prueba de carga en una organizacion desechable creada para ese fin, con limpieza posterior asignada
  - Prueba de carga en la organizacion demo, aceptando la acumulacion o limpiando despues
  - Sin prueba de carga: solo validacion del throttle por inspeccion de codigo y pruebas unitarias
  - Prueba de carga reducida (volumen menor al de un curso real) como compromiso
- **Estudio de APIs:** §2.4 calcula 40 puntos por grupo y recomienda un throttle de 1 repositorio cada 3 a 5 segundos.
- **Fusiona:** P655

## Ya respondidas por el enunciado

Ninguna. Las 14 preguntas de entrada de esta area (12 del archivo de consolidacion mas N007 y N013 de la ronda critica) recibieron veredicto ABIERTA en la etapa de verificacion; dos de ellas (P654 y P656) con marca adicional de BLOQUEA. No hay ninguna pregunta apartada por estar respondida textualmente en el enunciado.
