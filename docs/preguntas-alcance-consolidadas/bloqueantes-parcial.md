# Bloqueantes de la entrega parcial del 16 de septiembre

Las 193 preguntas que un revisor marco como imposibles de esquivar para construir la demo parcial: crear usuario profesor, crear curso, vincular Canvas y GitHub, crear una tarea individual, mapear estudiantes a usuarios de GitHub y aprovisionar repositorios automaticamente.

Cada entrada enlaza al documento de su area, donde estan el detalle, las opciones y la postura del estudio de APIs.

| Area | Bloqueantes |
|---|---|
| [2.1](area-2.1.md) | 32 |
| [2.2](area-2.2.md) | 28 |
| [2.3](area-2.3.md) | 36 |
| [2.4](area-2.4.md) | 2 |
| [2.5](area-2.5.md) | 3 |
| [2.6](area-2.6.md) | 10 |
| [2.7](area-2.7.md) | 7 |
| [3.1](area-3.1.md) | 13 |
| [3.2-3.3-4](area-3.2-3.3-4.md) | 2 |
| [transversal](area-transversal.md) | 30 |
| [infraestructura](area-infraestructura.md) | 21 |
| [proceso](area-proceso.md) | 9 |

## 2.1 — Cursos y usuarios

[Abrir el documento completo](area-2.1.md)

**Identidad, registro y administración de la plataforma**

- **Q-2.1-01** · parcial · decision_equipo
  ¿Quién crea las cuentas de profesor y existe un rol de "administrador de plataforma" distinto de "profesor"?
- **Q-2.1-02** · parcial · decision_equipo
  ¿Cómo se implementa técnicamente "registrarse asociando su cuenta gmail.com" y qué datos de Google se guardan?
- **Q-2.1-03** · parcial · decision_equipo
  ¿Qué direcciones de correo se aceptan exactamente como "cuenta basada en gmail.com"?
- **Q-2.1-04** · parcial · decision_equipo
  ¿Cuál es la clave de identidad del usuario y cómo se normalizan los alias de Gmail al registrar e invitar?
- **Q-2.1-05** · parcial · decision_equipo
  ¿Qué ocurre cuando el intento de login no cumple la regla de correo o Google no devuelve un consentimiento válido?
- **Q-2.1-08** · ambas · decision_equipo
  ¿Se fijan cuotas y controles de abuso sobre el registro abierto, dado que la URL será pública durante las dos semanas de revisión?
**Modelo de curso, membresías y ciclo de vida**

- **Q-2.1-09** · parcial · decision_equipo
  ¿Qué atributos propios tiene un curso en la app y cuál prevalece frente a los datos de Canvas?
- **Q-2.1-11** · parcial · decision_equipo
  ¿Qué ve cada usuario en su lista de cursos y qué muestra el estado vacío tras el login?
- **Q-2.1-12** · ambas · decision_equipo
  ¿Un mismo curso de Canvas o una misma organización de GitHub pueden vincularse a más de un curso de la app?
- **Q-2.1-13** · ambas · dependencia_externa
  ¿Un curso de la app puede vincularse a VARIOS cursos de Canvas, cuando la universidad modela cada sección como un curso separado?
- **Q-2.1-14** · parcial · decision_equipo
  ¿Se exige unicidad del nombre/slug de curso y de tarea, y cómo se sanitiza?
- **Q-2.1-17** · ambas · decision_equipo
  ¿El modelo de datos soporta más de una instancia de Canvas (claves compuestas) y cuál es el alcance del mapeo estudiante ↔ GitHub?
**Flujo de configuración y vinculación del curso**

- **Q-2.1-18** · parcial · decision_equipo
  ¿La creación y vinculación de un curso es un wizard secuencial o pantallas/módulos independientes, y cómo se retoma?
- **Q-2.1-19** · parcial · decision_equipo
  ¿Cuál es la máquina de estados de vinculación del curso, qué muestra el estado vacío y qué acciones quedan bloqueadas en cada estado?
**Vinculación con Canvas**

- **Q-2.1-20** · ambas · decision_equipo
  ¿Qué instancia(s) de Canvas soporta la app y cómo se administran sus Developer Keys?
- **Q-2.1-21** · parcial · dependencia_externa
  ¿Se solicitó (o se solicitará) una Developer Key en la instancia Canvas de la universidad, con qué responsable, plazo y plan B, y contra qué instancia y cuentas se hará la demo del 16-sep?
- **Q-2.1-22** · parcial · decision_equipo
  ¿Qué mecanismo de autenticación con Canvas se implementa: OAuth2 con Developer Key, token manual, o ambos?
- **Q-2.1-23** · parcial · dependencia_externa
  ¿La Developer Key tendrá "enforce scopes" activado, cuál es la lista exacta de scopes y qué pasa si el usuario rechaza el consentimiento o falta un scope?
- **Q-2.1-24** · parcial · decision_equipo
  ¿La conexión OAuth con Canvas es por usuario o por curso, dónde se gestiona en la UI y se usa `replace_tokens`?
- **Q-2.1-25** · parcial · decision_equipo
  ¿Qué muestra el selector de curso de Canvas, qué cursos lista, qué pasa si la lista viene vacía y qué se hace ante un curso ya vinculado?
**Vinculación con GitHub**

- **Q-2.1-30** · parcial · decision_equipo
  ¿Qué mecanismo se usa para operar sobre GitHub: GitHub App, OAuth App o PAT del profesor?
- **Q-2.1-31** · parcial · investigable_en_docs
  ¿La GitHub App será pública o privada y cómo se distribuye?
- **Q-2.1-32** · parcial · verificar_empiricamente
  ¿Cuál es la lista exacta de permisos que solicitará la GitHub App y cómo se maneja la necesidad de un permiso adicional posterior?
- **Q-2.1-33** · parcial · decision_equipo
  ¿Se activa "Request user authorization (OAuth) during installation" en la GitHub App?
- **Q-2.1-34** · parcial · decision_equipo
  ¿Qué guía se da antes de salir a github.com, se puede preseleccionar la organización, y qué se muestra en cada resultado del retorno?
- **Q-2.1-35** · parcial · decision_equipo
  ¿Qué hace la app si el profesor no tiene organización, no es owner, o la instalación queda como solicitud pendiente?
- **Q-2.1-36** · parcial · verificar_empiricamente
  ¿Se exige instalación con `repository_selection = all` o se acepta "solo repositorios seleccionados"?
- **Q-2.1-37** · parcial · decision_equipo
  ¿Cómo se correlaciona el `installation_id` devuelto al `setup_url` con el curso que se estaba vinculando, y qué se hace con instalaciones huérfanas?
- **Q-2.1-39** · ambas · verificar_empiricamente
  ¿Qué restricciones y políticas de la organización se verifican, cuáles bloquean y qué se muestra cuando impiden completar el proceso?
**Verificación de la configuración (R2.1.6)**

- **Q-2.1-52** · parcial · decision_equipo
  ¿Cuál es la lista definitiva de ítems del checklist (Canvas y GitHub), cómo se redacta cada uno y qué evidencia se muestra?
- **Q-2.1-53** · parcial · decision_equipo
  Para verificar GitHub, ¿se crea y elimina un repositorio temporal en la organización real o solo se inspeccionan los permisos de la instalación?
- **Q-2.1-55** · parcial · decision_equipo
  ¿Qué niveles de resultado tiene el checklist, qué ítems bloquean acciones posteriores y existe "continuar de todos modos"?

## 2.2 — Estudiantes y grupos

[Abrir el documento completo](area-2.2.md)

**Estrategia de enrolamiento y alcance**

- **Q-2.2-01** · ambas · decision_equipo
  ¿Cuál es la estrategia de enrolamiento Canvas↔GitHub que adopta el equipo (mecanismo primario y de respaldo), y qué parte de ella entra en la entrega parcial y qué parte en la final?
- **Q-2.2-02** · ambas · decision_equipo
  ¿El equipo acepta el riesgo de que un estudiante registre una cuenta de GitHub que no le pertenece, o exige prueba de propiedad de la cuenta?
- **Q-2.2-03** · final · decision_equipo
  Si se adopta la verificación por OAuth de GitHub vía magic link (§6.2), ¿cómo se define el enlace, el token y la precedencia frente a lo que el estudiante escribió en Canvas?
- **Q-2.2-05** · parcial · decision_equipo
  ¿El mapeo estudiante↔GitHub es por curso o global por identidad de Canvas (canvas_base_url + canvas_user_id)?
- **Q-2.2-06** · parcial · decision_equipo
  ¿Qué criterios de aceptación medibles se fijan para la usabilidad del enrolamiento desde el lado del estudiante, y se hará una prueba con un estudiante real antes del 16-sep?
- **Q-2.2-07** · parcial · dependencia_externa
  ¿Dispone el equipo del entorno de pruebas necesario: una instancia Canvas con cuentas de estudiante reales y cuentas de GitHub de prueba suficientes?
**Tarea de Canvas de registro y recoleccion del mapeo**

- **Q-2.2-08** · parcial · decision_equipo
  Si se usa una tarea de Canvas como formulario de registro del usuario de GitHub, ¿quién la crea, cuántas hay y cómo se define su contenido?
- **Q-2.2-09** · parcial · decision_equipo
  Para la tarea de Canvas de registro, ¿qué se fija respecto de los efectos colaterales que ven el estudiante y el profesor en Canvas?
- **Q-2.2-10** · ambas · decision_equipo
  ¿Cuál es el ciclo de vida de la tarea de recolección y qué hace la app si el profesor la altera en Canvas?
- **Q-2.2-11** · parcial · verificar_empiricamente
  Verificar contra la instancia real el formato del body de una submission online_text_entry y las capacidades del endpoint de submissions, para diseñar el parser y el polling.
- **Q-2.2-12** · parcial · decision_equipo
  ¿Cómo se le comunica a cada estudiante que debe registrar su usuario de GitHub: anuncio en Canvas al crear la tarea de registro, Conversation individual, solo la descripción de la tarea, o una combinación?
**Parseo, validacion y ciclo de vida del mapeo estudiante-GitHub**

- **Q-2.2-14** · ambas · decision_equipo
  ¿Qué reglas exactas de normalización y parseo se aplican al texto entregado por el estudiante, y qué normalización canónica se guarda?
- **Q-2.2-15** · ambas · decision_equipo
  Además de que el login exista en GitHub (200 y type=User), ¿qué validaciones y reglas de unicidad se exigen antes de aceptar un mapeo, y cómo se resuelven los conflictos?
- **Q-2.2-16** · parcial · decision_equipo
  Cuando el usuario entregado no existe (404) o es inválido, ¿qué feedback recibe el estudiante, por qué canal, con qué texto y cuántas veces?
- **Q-2.2-17** · parcial · decision_equipo
  Al validar exitosamente un usuario de GitHub, ¿qué recibe el estudiante y en qué momento?
- **Q-2.2-20** · parcial · decision_equipo
  Para la corrección manual del mapeo por el equipo docente, ¿cómo se comporta la edición: quién puede editar, cómo valida y qué queda registrado?
- **Q-2.2-24** · parcial · decision_equipo
  ¿Cuál es la máquina de estados del mapeo estudiante↔GitHub y cuáles de esos estados cuentan como "falta información" para R2.2.6?
**Acceso a GitHub: organizacion, invitaciones y recordatorios**

- **Q-2.2-25** · ambas · decision_equipo
  ¿Los estudiantes se invitan como miembros de la organización de GitHub o solo como colaboradores externos de cada repositorio?
- **Q-2.2-26** · ambas · decision_equipo
  Cuando la invitación de colaborador no es aceptada (queda pendiente, se rechaza o expira), ¿qué hace la app y cómo se refleja en los estados?
**Roster: quien cuenta como estudiante**

- **Q-2.2-28** · ambas · decision_equipo
  ¿Qué estados de inscripción de Canvas cuentan como "estudiante inscrito" para listar, exigir usuario de GitHub, crear repositorio y notificar, y cómo se trata al estudiante inalcanzable?
- **Q-2.2-29** · ambas · decision_equipo
  ¿Qué usuarios se excluyen del roster aunque aparezcan en los endpoints de Canvas: Test Student, observers, roles personalizados y usuarios con más de un rol en el curso?
- **Q-2.2-31** · parcial · decision_equipo
  ¿Qué datos del estudiante se almacenan y se muestran, cuáles se refrescan en cada sincronización y se conserva historial de cambios?
- **Q-2.2-33** · parcial · decision_equipo
  ¿Se permite vincular y sincronizar un curso de Canvas sin estudiantes, no publicado o ya concluido (workflow_state completed)?
**Sincronizacion con Canvas**

- **Q-2.2-34** · ambas · decision_equipo
  ¿Cómo y con qué frecuencia se sincroniza la información de estudiantes, secciones y grupos desde Canvas, y qué muestra la UI sobre la última sincronización?
- **Q-2.2-35** · parcial · decision_equipo
  Tras vincular Canvas, ¿qué ve el profesor mientras corre la primera importación de estudiantes, secciones y grupos, y qué ocurre si falla a mitad?
**Vista de informacion faltante, permisos y exenciones**

- **Q-2.2-58** · parcial · decision_equipo
  ¿La vista de información faltante vive a nivel de curso, a nivel de tarea, o ambas, y cómo se enlaza con la tabla de estado de repositorios (R2.3.11)?
- **Q-2.2-59** · parcial · decision_equipo
  ¿Qué columnas, estados, filtros, búsqueda, orden y paginación tiene la vista de faltantes y la tabla de estudiantes/grupos y repositorios con 60–200 filas?
- **Q-2.2-60** · parcial · decision_equipo
  ¿Qué acciones individuales y masivas ofrece la vista de faltantes, con qué confirmaciones e historial?

## 2.3 — Tareas y repositorios

[Abrir el documento completo](area-2.3.md)

**Modelo estructural: tarea, entregas y sujetos**

- **Q-2.3-01** · ambas · decision_equipo
  ¿Cual es la cardinalidad entre una entrega de la app y las tareas de Canvas cuando el profesor duplica el assignment por seccion (una copia por seccion, visible solo a la suya mediante only_visible_to_overrides / "Assign to") en lugar de usar overrides sobre un unico assignment?
- **Q-2.3-02** · ambas · decision_equipo
  ¿Que assignments de Canvas se ofrecen en el selector al crear una tarea, con que informacion y filtros, y que reglas de unicidad y validacion se aplican?
- **Q-2.3-04** · ambas · decision_equipo
  ¿Se permite vincular un assignment con published:false y crear repositorios para el, y que ocurre si el assignment se despublica despues de vinculado?
- **Q-2.3-05** · final · verificar_empiricamente
  Si el assignment tiene visibilidad diferenciada (only_visible_to_overrides=true o asignado solo a ciertas secciones o estudiantes), ¿que conjunto de sujetos recibe repositorio?
- **Q-2.3-06** · ambas · decision_equipo
  ¿Como se determinan el orden y el tipo (parcial/final) de las entregas de una tarea, y que ocurre cuando las fechas de Canvas contradicen ese orden?
- **Q-2.3-08** · ambas · decision_equipo
  ¿El nombre y el slug de la tarea dentro de la app los escribe el profesor o se derivan del primer assignment de Canvas, son editables despues y que efecto tiene cambiarlos sobre los repositorios ya creados?
- **Q-2.3-12** · ambas · decision_equipo
  ¿Como se modela el "sujeto" de una tarea (estudiante o grupo) al que apuntan Repository, DeliverySnapshot, GradingAssignment y NotificationOutbox, y cual es el ciclo de vida de la fila Repository?
**Repositorio base y contenido inicial**

- **Q-2.3-14** · ambas · decision_equipo
  ¿Como se constituye el repositorio base de una tarea: donde se crea, con que convencion y parametros, se puede designar uno ya existente en la organizacion o importar contenido, y es un paso saltable del flujo de crear tarea?
- **Q-2.3-18** · parcial · verificar_empiricamente
  ¿La generacion de cada repositorio a partir del base usara POST /repos/{template}/generate o una copia de archivos via Contents API, con que permisos exactos de la instalacion, funciona en una organizacion Free y con que rama por defecto queda el repositorio generado?
- **Q-2.3-19** · parcial · verificar_empiricamente
  Tras POST /repos/{template}/generate GitHub responde 201 pero la copia del contenido es asincrona: ¿el worker espera a detectar el commit inicial antes de continuar o sigue de inmediato y tolera 409 en los pasos posteriores?
- **Q-2.3-20** · ambas · decision_equipo
  ¿Que contenido tiene el repositorio de un estudiante cuando la tarea NO tiene repositorio base, y admiten los archivos personalizacion por sujeto?
**Nomenclatura de repositorios**

- **Q-2.3-22** · ambas · decision_equipo
  ¿Cual es la funcion de nombrado de los repositorios: que componentes la forman, es un patron fijo o configurable con vista previa, que reglas de sanitizacion y truncado aplica y es el nombre inmutable ante cambios en los datos de origen?
- **Q-2.3-23** · ambas · decision_equipo
  Ante una colision de nombre (422 "name already exists"), ¿la app agrega un sufijo, falla con error visible o adopta el repositorio existente, y como distingue un repositorio propio de uno ajeno preexistente en la organizacion?
**Acceso a GitHub: modelo de colaboradores, invitaciones y configuracion del repositorio**

- **Q-2.3-24** · ambas · decision_equipo
  ¿Cual es el modelo de acceso a los repositorios: outside collaborators por repositorio, miembros de la organizacion o teams, con que nivel de permiso para estudiantes y con que mecanismo para el equipo docente?
- **Q-2.3-25** · ambas · dependencia_externa
  ¿Los repositorios son siempre privados o la visibilidad es configurable por tarea, y que limites impone el plan de la organizacion de GitHub (Free/Team/Education) a repositorios privados, colaboradores y funcionalidades?
- **Q-2.3-29** · parcial · verificar_empiricamente
  Si la GitHub App esta instalada con "selected repositories" en la organizacion, ¿los repositorios creados por la propia App quedan automaticamente incluidos en la instalacion, o hay que exigir instalacion en "all repositories" al vincular el curso?
- **Q-2.3-30** · ambas · verificar_empiricamente
  ¿Como detecta la app el desenlace de una invitacion (aceptada, rechazada o expirada): polling a GET /collaborators e /invitations o webhooks de la App (member, member_invite), y que estado, reintentos y avisos corresponden a cada desenlace?
- **Q-2.3-32** · ambas · investigable_en_docs
  GitHub limita la cantidad de invitaciones que un repositorio u organizacion puede emitir por periodo: ¿cuales son los limites vigentes y que hace la app al alcanzarlos en un curso de 200 estudiantes?
- **Q-2.3-33** · parcial · verificar_empiricamente
  Muchos estudiantes crearan su cuenta de GitHub el mismo dia que registran su usuario: ¿que ocurre con las invitaciones a cuentas recien creadas, sin correo verificado o con invitacion a la organizacion pendiente, y que estado muestra la app?
- **Q-2.3-35** · ambas · verificar_empiricamente
  Mientras la invitacion no se acepta el estudiante no tiene acceso al repositorio privado: ¿que ve exactamente al abrir la URL del repositorio en cada situacion y que enlace canonico se le envia?
**Aprovisionamiento automatico: predicado, disparadores y arquitectura del worker**

- **Q-2.3-36** · ambas · decision_equipo
  ¿Cual es el predicado cerrado de "toda la informacion requerida" (R2.3.10), puede el repositorio crearse ANTES de conocer el usuario de GitHub del estudiante, y como se interpreta y defiende el mandato de que la creacion "no debera depender de una accion realizada por los estudiantes"?
- **Q-2.3-37** · ambas · decision_equipo
  ¿Cual es el ciclo de vida y el estado de una tarea de la app: cuando empieza el aprovisionamiento, que significa "tarea activa" para los workers, se puede pausar, reanudar o cancelar, y cuando termina?
- **Q-2.3-38** · ambas · decision_equipo
  ¿Cual es el disparador, la cadencia, el orden y la latencia objetivo del worker de aprovisionamiento, y existe un boton de ejecucion manual?
- **Q-2.3-39** · ambas · decision_equipo
  ¿El worker de repositorios se disena como reconciliador declarativo o como acciones imperativas disparadas por eventos, y que diferencias entre estado deseado y observado se aplican automaticamente?
- **Q-2.3-41** · ambas · decision_equipo
  ¿Existe una entidad de miembro de repositorio con historial (RepositoryMember) o el estado de colaboradores se consulta a GitHub en cada reconciliacion sin persistirlo?
- **Q-2.3-42** · ambas · decision_equipo
  ¿Cual es la maquina de estados definitiva por repositorio (y el sub-estado por integrante), y cuales de esos estados son terminales?
- **Q-2.3-43** · ambas · decision_equipo
  ¿Cual es la taxonomia de errores del aprovisionamiento, la politica de reintentos y las acciones manuales disponibles?
**Visibilidad del estado, errores y usabilidad**

- **Q-2.3-44** · ambas · decision_equipo
  ¿Como es la vista de estado de repositorios: que columnas, filtros, busqueda, contadores, ordenacion, paginacion, exportacion y acciones masivas ofrece, como comunica el progreso y como se actualiza?
- **Q-2.3-45** · ambas · decision_equipo
  Los errores del worker ocurren cuando nadie esta mirando: ¿donde afloran dentro de la jerarquia de la interfaz y se pueden silenciar?
- **Q-2.3-46** · ambas · decision_equipo
  ¿Como se redactan los mensajes de error para el equipo docente y existe una bitacora de intentos por repositorio?
- **Q-2.3-47** · ambas · decision_equipo
  ¿Que se muestra en los estados vacios de las pantallas de 2.3?
- **Q-2.3-48** · parcial · decision_equipo
  Antes de guardar una tarea, ¿la app muestra un resumen de impacto que el profesor deba confirmar?
**Comunicacion con el estudiante a traves de Canvas**

- **Q-2.3-52** · ambas · decision_equipo
  ¿Cual es el contenido exacto de "la informacion necesaria para acceder al repositorio" (R2.3.12), incluido el tramo de autenticacion con Git, donde vive esa informacion y como distingue la app a un estudiante bloqueado por autenticacion de uno que no ha participado?
- **Q-2.3-54** · ambas · decision_equipo
  ¿Que artefactos de Canvas visibles para el estudiante puede crear o EDITAR la app, ademas de la tarea de registro, los mensajes y los anuncios?
- **Q-2.3-55** · parcial · verificar_empiricamente
  ¿Como se renderizan para el estudiante los textos que la app envia por Canvas y que reglas de redaccion se derivan de ello?
**Cambios, casos borde y recuperacion**

- **Q-2.3-66** · final · verificar_empiricamente
  ¿Que hace la app cuando el login de GitHub mapeado deja de ser valido: no existe, fue renombrado, es una organizacion, esta suspendido, bloqueo a la organizacion, o la cuenta se elimino despues de aceptar la invitacion?

## 2.4 — Fechas de cierre y versiones

[Abrir el documento completo](area-2.4.md)

**Alcance de la entrega parcial y entorno de prueba**

- **Q-2.4-01** · parcial · decision_equipo
  ¿Qué parte del área 2.4 debe estar construida y demostrable en la entrega parcial del 16-sep: nada relacionado con fechas, solo la fecha base de la entrega vinculada leída al momento de vincular, o también las fechas por sección y las extensiones individuales mostradas en la vista de la tarea con su zona horaria explíc…
- **Q-2.4-02** · ambas · dependencia_externa
  ¿El equipo dispone, o dispondrá antes de la entrega final, de una instancia de Canvas donde pueda crear al menos dos secciones, estudiantes inscritos en dos secciones a la vez, un group set con grupos, y overrides por sección, por grupo y ADHOC, para probar y demostrar R2.4.2/R2.4.3? ¿El plan Free-for-Teacher permite t…

## 2.5 — Seguimiento del avance

[Abrir el documento completo](area-2.5.md)

**Atribucion de commits y definicion de participacion**

- **Q-2.5-24** · ambas · decision_equipo
  ¿La atribucion por login guarda el login textual o el id numerico de GitHub?
- **Q-2.5-30** · ambas · decision_equipo
  ¿Como se distingue en el dashboard al estudiante "mapeado pero sin acceso" del "con acceso y sin commits", y como se detecta la aceptacion de la invitacion?
**Contenido, rendimiento y usabilidad del dashboard**

- **Q-2.5-39** · ambas · decision_equipo
  ¿El bloque "estado general de creacion y configuracion" del dashboard (R2.5.5) es el mismo componente que la tabla de estado de repositorios de R2.3.11, y que se muestra en la entrega parcial?

## 2.6 — Informes y comunicacion

[Abrir el documento completo](area-2.6.md)

**Decisiones estructurales: emisor, canales y viabilidad tecnica**

- **Q-2.6-01** · ambas · decision_equipo
  ¿Desde qué cuenta de Canvas se envían los mensajes directos y los anuncios de la app: siempre con el token del profesor que vinculó el curso, con el token propio de quien dispara la acción cuando lo tiene, o un esquema híbrido? Con varios profesores (R2.1.7), ¿quién es el emisor «del curso» y es configurable? ¿Qué ocur…
- **Q-2.6-02** · ambas · dependencia_externa
  ¿Se verificó que los canales de Canvas que la app usará están habilitados y son VISIBLES PARA LOS ESTUDIANTES en la instancia que se usará (institucional o Free-for-Teacher)? Casos a comprobar: bandeja de Conversations habilitada para estudiantes y sin restricciones institucionales sobre quién puede escribir a quién; c…
- **Q-2.6-03** · ambas · investigable_en_docs
  ¿Cuáles son las restricciones de formato y longitud de cada canal de Canvas, y qué plantilla se define para cada uno? En concreto: el `body` de POST /conversations, ¿acepta HTML o solo texto plano, Canvas auto-enlaza las URLs, respeta saltos de línea y listas, y cuál es su longitud máxima?; los comentarios de submissio…
- **Q-2.6-04** · ambas · verificar_empiricamente
  ¿Cuántos mensajes individuales personalizados por hora tolera el throttling de Canvas con un solo token (60 estudiantes × 1 POST secuencial)? ¿Existe algún límite diario de conversaciones nuevas para un usuario teacher en la instancia usada (Free-for-Teacher o institucional)? ¿Funciona `bulk_message`? ¿El token del pro…
**Comunicaciones automaticas a estudiantes: catalogo y configuracion**

- **Q-2.6-28** · ambas · decision_equipo
  ¿Cuál es la lista cerrada de eventos que generan comunicación automática y su canal: repositorio disponible, invitación pendiente sin aceptar tras N días, falta usuario de GitHub (recordatorio), X horas antes de una entrega, repositorio sin commits cerca del cierre, cambio de fecha, entrega cerrada o snapshot capturado…
- **Q-2.6-29** · ambas · decision_equipo
  ¿Los toggles de comunicaciones son por tarea con valores por defecto ON u OFF al crear la tarea? ¿Se heredan de una configuración a nivel de curso? ¿Pueden variar por entrega dentro de una tarea (recordatorio para la parcial pero no para la final)? ¿Qué roles pueden cambiarlos, dado que el enunciado dice «el profesor»?
- **Q-2.6-30** · ambas · decision_equipo
  Para informar al estudiante el repositorio que le corresponde (R2.3.12), ¿se usa comentario en la entrega de Canvas (submission comment), mensaje directo (Conversation), o ambos, asumiendo el riesgo de doble aviso? Si la tarea tiene varias entregas, ¿en cuál submission se comenta (la primera, la próxima)? ¿Qué texto se…
- **Q-2.6-31** · ambas · decision_equipo
  ¿Se comunica al estudiante al crearse el repositorio (estado CREATED, aunque la invitación esté pendiente) o solo cuando está READY (invitación aceptada)? Si la invitación no se acepta en N días, ¿se envía un recordatorio automático «acepta tu invitación», con qué frecuencia y con qué tope, y se reenvía la invitación d…
- **Q-2.6-32** · final · decision_equipo
  ¿Con qué frecuencia se envía el recordatorio automático a los estudiantes sin usuario de GitHub (diaria, cada N días), con qué tope de intentos, desde cuándo (al crear la tarea, al publicarse la tarea de recolección) y hasta cuándo (vencimiento de la tarea de recolección, cierre de la primera entrega)? ¿Se envía tambié…
**Trazabilidad, plantillas y notificaciones internas**

- **Q-2.6-52** · final · decision_equipo
  ¿Qué campos guarda el log u outbox de comunicaciones (tipo, canal, destinatario, tarea y entrega, cuerpo final renderizado, disparado por automático o por el usuario X, programado para, enviado el, estado, error, id externo de Canvas —`conversation_id`, `discussion_topic_id`— o del proveedor de email), qué vistas lo ex…

## 2.7 — Correccion

[Abrir el documento completo](area-2.7.md)

**Modelo y alcance de la corrección (decisiones estructurales)**

- **Q-2.7-05** · ambas · decision_equipo
  Dentro de los ≥3 permisos que exige R2.1.8, ¿cuáles gobiernan exactamente las acciones de 2.7 (abrir la vista de corrección de una entrega NO asignada, ver el código, ver rúbrica, notas y comentarios de otros correctores, publicar en Canvas, asignar y reasignar) y qué puede ver un ayudante sin permiso de corrección?
**Asignación de correctores (R2.7.1)**

- **Q-2.7-09** · ambas · decision_equipo
  ¿Quién puede asignar y reasignar entregas: solo los profesores, o también un rol de ayudante con permiso de asignación (por ejemplo "ayudante jefe")?
- **Q-2.7-13** · ambas · decision_equipo
  Al retirar a un ayudante (R2.1.9), ¿sus entregas pendientes vuelven a "sin asignar", se reasignan automáticamente de forma balanceada, o el flujo de retiro obliga al profesor a reasignarlas antes de confirmar?
- **Q-2.7-15** · ambas · decision_equipo
  Si los repositorios son privados y el acceso del corrector es por enlace a GitHub, el ayudante debe ser miembro de la organización o colaborador de cada repositorio. ¿La app pide y guarda la cuenta GitHub de cada ayudante al incorporarlo y lo agrega automáticamente (a la organización como miembro, o a cada repositorio …
**Rúbrica (R2.7.5)**

- **Q-2.7-26** · ambas · decision_equipo
  Si el assignment de Canvas vinculado NO tiene rúbrica asociada, ¿se permite calificar con nota directa, se muestra un aviso, se bloquea la corrección, o se ofrece un enlace para crearla en Canvas? ¿Se valida o advierte la ausencia de rúbrica ya al vincular la entrega con la tarea (R2.3.1)?
**Nota, comentario y publicación en Canvas (R2.7.6)**

- **Q-2.7-39** · ambas · decision_equipo
  Dado que el repositorio ES la entrega, ¿la app exige o solo recomienda, al vincular la entrega con la tarea de Canvas (R2.3.1), que el assignment tenga `submission_types` compatible (`none`, `on_paper`, `online_url`) y advierte si es `online_upload` u otro tipo que confunda al estudiante? ¿Se valida también que el assi…
**Identidad, credenciales y permisos para escribir en Canvas**

- **Q-2.7-47** · ambas · decision_equipo
  ¿Con qué credencial se escriben las notas en Canvas: (A) el token del profesor que vinculó el curso (la app actúa "en nombre del curso" y Canvas registrará al profesor como calificador), o (B) el token OAuth propio de cada ayudante (lo que exige que esté enrolado como TA en Canvas)?

## 3.1 — Entrega parcial (16-sep)

[Abrir el documento completo](area-3.1.md)

**Alcance de la entrega parcial y criterios de evaluacion**

- **Q-3.1-02** · parcial · decision_equipo
  ¿Cuál es la lista cerrada de requisitos que se demostrarán el 16-sep y cuáles quedan explícitamente declarados fuera del alcance parcial? El enunciado solo nombra el flujo usuario profesor → curso → vinculación con Canvas y GitHub → creación de una tarea individual → asociación estudiantes↔usuarios GitHub → creación au…
- **Q-3.1-03** · parcial · decision_equipo
  Para la "tarea individual" de la demo parcial, ¿la tarea de la app se vincula a UNA sola tarea de Canvas (una entrega) o ya se demuestra la vinculación 1..N (parcial + final) aunque no existan snapshots? ¿La validación de consistencia individual/grupal entre entregas (R2.3.3) se muestra en la parcial o se posterga a la…
- **Q-3.1-04** · parcial · decision_equipo
  En la build del 16-sep, ¿cómo se presentan las funciones que no están listas para que un evaluador que "se salga del guion" no encuentre comportamientos rotos: se BLOQUEA explícitamente vincular tareas grupales ("disponible en la entrega final") o se permite con comportamiento parcial; las secciones 2.4–2.7 (fechas, da…
**Autenticacion, registro y vinculacion de cuentas**

- **Q-3.1-05** · ambas · dependencia_externa
  En la demo parcial, ¿la "creación de un usuario profesor" se hace con Google OAuth real (cuenta gmail.com) o con un formulario propio? Si es Google OAuth: ¿el proyecto de Google Cloud estará en modo "Testing" (máximo 100 usuarios de prueba que deben registrarse por correo) o en "Production"? ¿Hay que pedir los correos …
- **Q-3.1-06** · ambas · decision_equipo
  ¿La restricción "cuenta de correo basada en gmail.com" (R2.1.2) se implementa como rechazo estricto de cualquier dominio distinto a @gmail.com? Si el profesor o los ayudantes intentan entrar con su cuenta institucional Google Workspace (p. ej. @uandes.cl), ¿se les rechaza y con qué texto de error exacto? ¿Se pedirá for…
- **Q-3.1-07** · parcial · decision_equipo
  ¿La UI de vinculación con Canvas ofrecerá un modo "pegar token de acceso" además de OAuth2? Si sí, ¿visible para todos los usuarios, solo detrás de un flag de entorno, o solo en desarrollo? ¿Se muestra al revisor el 16-sep?
**Entorno de entrega: despliegue, acceso de revisores y entregables**

- **Q-3.1-08** · parcial · decision_equipo
  El "link para acceder a su entrega" del 16-sep, ¿será una URL pública desplegada con workers/cron activos 24/7 que los ayudantes puedan usar después de la clase, o un link a repositorio con instrucciones para correr localmente? Si es pública, ¿en qué proveedor, con qué plan (incluido el comportamiento de suspensión por…
- **Q-3.1-09** · ambas · decision_equipo
  ¿Cómo prueban la app el profesor y los ayudantes, que no tienen Developer Key ni organización GitHub propia: (a) con credenciales de una cuenta profesor demo ya vinculada al Canvas y a la organización de prueba; (b) cada revisor se registra con su gmail y el equipo lo agrega como co-profesor (R2.1.7) del curso demo; (c…
**Demo presencial del 16-sep: logistica, guion y tiempos**

- **Q-3.1-14** · parcial · decision_equipo
  ¿Qué guion de demo adopta el equipo para el 16-sep, qué casos con problema se mostrarán deliberadamente (estudiante que no entregó su usuario GitHub, usuario inexistente, usuario que en realidad es una Organization, invitación pendiente sin aceptar) y cuál de ellos se resuelve en vivo para evidenciar R2.2.5 y R2.3.11 (…
- **Q-3.1-15** · parcial · decision_equipo
  En la demo presencial, ¿se mostrará el lado Canvas y GitHub en vivo (pestañas abiertas con el curso de Canvas y la organización) para que el profesor verifique que los repositorios, colaboradores y mensajes existen realmente, o solo la UI de la app? ¿Qué cuentas deben estar logueadas simultáneamente en el navegador de …
- **Q-3.1-16** · parcial · decision_equipo
  ¿En la demo del 16-sep los repositorios se crearán EN VIVO (esperando el ciclo del worker) o se mostrarán ya creados antes de la presentación? Con cron de aprovisionamiento cada 2 min y sincronización de Canvas cada 10 min, ¿la demo acepta esas esperas o se exige que los intervalos sean configurables por entorno (p. ej…
**Casos borde, concurrencia y recuperacion**

- **Q-3.1-17** · parcial · decision_equipo
  Además de los casos con problema de mapeo estudiante↔GitHub, ¿qué fallos de VINCULACIÓN se prepararán para que el evaluador los provoque o los vea en la demo del 16-sep: elegir un curso de Canvas donde el usuario no es profesor, instalar la App de GitHub en la cuenta personal en vez de en una organización, cancelar la …
- **Q-3.1-18** · ambas · decision_equipo
  Si varios revisores usan la misma cuenta o el mismo curso demo en paralelo, ¿cómo se evita que se pisen entre sí (crear tareas duplicadas, retirar al único ayudante, generar decenas de repositorios en la organización, desvincular el Canvas)? ¿Habrá un curso demo "de exhibición" con datos ricos y otro "sandbox" para que…

## 3.2-3.3-4 — Entrega final, validacion individual y evaluacion

[Abrir el documento completo](area-3.2-3.3-4.md)

**Alcance evaluable: que debe poder ver y hacer un revisor con la herramienta**

- **Q-3.2-3.3-4-02** · ambas · decision_equipo
  Dado que "las funcionalidades a las que no se puede acceder en el uso no se consideran cumplidas", ¿la administracion de usuarios de tipo profesor que exige R2.1.1 (listar, desactivar, reactivar, eliminar) tendra una interfaz accesible para los revisores, con que credencial se accede (por ejemplo, una cuenta admin de d…
**Casos borde, limites y recuperacion del entorno**

- **Q-3.2-3.3-4-12** · final · decision_equipo
  Los revisores que creen tareas en el sandbox generaran repositorios reales en la organizacion de GitHub del equipo: ¿se permitira eliminar tareas y sus repositorios desde la app (el enunciado no lo pide), se limpiaran manualmente o se aceptara la acumulacion? ¿Como se comporta el sistema al recrear una tarea con el mis…

## transversal — Transversal

[Abrir el documento completo](area-transversal.md)

**Alcance del producto y coexistencia en el entorno de evaluacion**

- **Q-transversal-01** · ambas · decision_equipo
  ¿Cómo interpreta el equipo la restricción del enunciado "los estudiantes no serán usuarios de la aplicación: toda su interacción deberá realizarse a través de Canvas y GitHub"? ¿Prohíbe cualquier página web de la app abierta por un estudiante —incluido el magic link firmado hacia el OAuth de GitHub que propone §6.2 par…
- **Q-transversal-03** · ambas · decision_equipo
  Es muy probable que el profesor y los ayudantes evalúen las apps de VARIOS equipos del curso contra el MISMO curso de Canvas y la MISMA organización de GitHub (instalando varias GitHub Apps y vinculando el mismo curso en cada una). ¿Qué reglas de aislamiento adopta la app para coexistir sin interferir: prefijo o namesp…
**Configuracion, modelo de datos y definiciones canonicas**

- **Q-transversal-04** · ambas · decision_equipo
  ¿Cuál es el mecanismo único de configuración de la app, su jerarquía y qué parámetro vive en qué nivel? Parámetros a repartir: plantilla de nombres de repositorios, visibilidad de los repositorios, nivel de permiso de los estudiantes, política de acceso (miembro de la organización vs colaborador externo), repositorio b…
- **Q-transversal-05** · ambas · decision_equipo
  ¿Cómo se IMPLEMENTAN en la base de datos los conjuntos de estados y tipos que el spec enumera (estado de repositorio, de mapeo estudiante↔GitHub, de snapshot, de corrección, tipo de evento del timeline, tipo de comunicación, clase de error): tipo ENUM nativo del motor, columna de texto con CHECK, tabla catálogo con FK,…
- **Q-transversal-06** · ambas · decision_equipo
  ¿Qué convenciones de ALMACENAMIENTO se fijan para los identificadores y textos que vienen de Canvas y GitHub? Decidir explícitamente: (a) tipo de columna para los ids de Canvas —bigint, o texto para tolerar los global ids de 14+ dígitos y los ids "shadow" con tilde (formato 123~456) de cuentas de otras instancias—; (b)…
- **Q-transversal-07** · ambas · decision_equipo
  Si se adopta la regla "nunca borrar filas, marcar deleted_at": (a) ¿cómo se conjugan las claves únicas con el borrado lógico en cada caso —unique(curso, github_login) cuando el login perteneció a un estudiante retirado y ahora lo reclama otro; unique(curso, usuario) en membresías docentes al retirar y reincorporar a un…
- **Q-transversal-09** · ambas · decision_equipo
  ¿Se exige una definición CANÓNICA ÚNICA del universo de sujetos y de los contadores derivados, compartida por todas las vistas y workers, o cada pantalla aplica sus propios filtros? Las mismas cifras aparecen en al menos cinco lugares (panel de faltantes, tabla de estado de repositorios, KPIs del dashboard, informe dia…
- **Q-transversal-10** · final · decision_equipo
  ¿Se fija la matriz de datos derivados y sus disparadores de recálculo? Ejemplos de aristas: cambio de roster → sujetos → filas Repository → fechas efectivas → estado deseado de colaboradores → alertas; cambio de mapeo → colaboradores deseados → atribución de commits → "sin participación"; cambio de override → fechas ef…
**Zona horaria, idioma y vocabulario**

- **Q-transversal-11** · ambas · decision_equipo
  ¿Cuál es la regla única de fechas y horas de extremo a extremo? Decidir: (a) servidor, BD y APIs en UTC (timestamptz) con conversión solo al renderizar; (b) de dónde sale la zona horaria de visualización: configurada por curso (p. ej. America/Santiago), tomada del campo time_zone del curso en Canvas, o del navegador de…
- **Q-transversal-12** · ambas · decision_equipo
  ¿Cuál es la política de idioma, tono y formatos de todos los textos del producto? Decidir: (a) si la UI, los mensajes de error, los emails y los mensajes a estudiantes por Canvas van 100 % en español de Chile o son bilingües; (b) si se instala infraestructura de i18n (archivos de traducción) o se hardcodea el español, …
- **Q-transversal-13** · ambas · decision_equipo
  ¿Cuál es el glosario oficial de la UI y su equivalencia exacta con los términos de Canvas y GitHub? Pares a decidir: "Tarea" (app) vs "Entrega" (= assignment de Canvas) vs "tarea de Canvas"; "Grupo" vs "conjunto de grupos / group set"; "Sección"; "Repositorio base" vs "plantilla"; "Organización"; "Versión de entrega" v…
**Navegacion, pantallas y guia al equipo docente**

- **Q-transversal-14** · ambas · decision_equipo
  ¿Cuál es el árbol exacto de navegación y de URLs de la app? Propuesta a confirmar o corregir: Home = "Mis cursos" → Curso (pestañas: Resumen / Estudiantes / Tareas / Equipo docente / Configuración) → Tarea (pestañas: Resumen / Entregas / Repositorios / Dashboard / Corrección / Comunicaciones / Configuración) → Reposito…
- **Q-transversal-16** · parcial · decision_equipo
  ¿Se estandariza un componente "Pendientes / Qué falta" reutilizado en las vistas de curso y de tarea, que liste en lenguaje de acción cada bloqueo con su llamada a la acción ("3 estudiantes sin usuario de GitHub → Enviar recordatorio", "2 invitaciones sin aceptar → Reenviar", "1 grupo sin integrantes → Configurar en Ca…
- **Q-transversal-17** · ambas · decision_equipo
  ¿Qué debe mostrar cada vista cuando no hay datos: curso sin estudiantes o sin secciones, group set sin grupos todavía (self-signup abierto), tarea sin entregas vinculadas, tarea sin repositorios, repositorio sin commits, entrega cerrada con snapshot "sin commits" (¿qué corrige el ayudante y qué nota se publica?), dashb…
- **Q-transversal-18** · ambas · decision_equipo
  ¿El spec incluirá un catálogo cerrado de errores esperables de la UI docente con, para cada uno, el texto mostrado al usuario, la acción sugerida y quién puede resolverlo? Casos mínimos a decidir: token de Canvas expirado o revocado; scopes insuficientes; 403/429 por rate limit; GitHub App desinstalada; usuario de GitH…
- **Q-transversal-19** · ambas · decision_equipo
  ¿Qué guía embebida tendrá la app y quién la produce? Decidir: (a) si la página del curso tiene un checklist de progreso ("Canvas vinculado, GitHub vinculado, estudiantes sincronizados, 7/10 usuarios de GitHub mapeados, 1 tarea") con enlaces a la acción pendiente; (b) qué forma toma la ayuda contextual: tooltips en térm…
- **Q-transversal-20** · ambas · decision_equipo
  Indicador "última sincronización": ¿con qué granularidad se registra y se muestra (por curso, por tarea, por fuente Canvas vs GitHub, por repositorio)? ¿Dónde se ubica (cabecera del curso, pie de cada tabla, tooltip del dato)? ¿Formato relativo ("hace 4 min") con tooltip absoluto en hora local? ¿Qué se muestra si nunca…
- **Q-transversal-21** · parcial · decision_equipo
  ¿Existe un botón "Sincronizar ahora"? Si sí: ¿para qué fuentes (roster de Canvas, fechas de Canvas, entregas de la tarea de registro de usuario de GitHub, commits de GitHub, disparar aprovisionamiento)? ¿Uno global por curso o uno por fuente? ¿Qué permiso se requiere para pulsarlo? ¿Se deshabilita mientras corre y tien…
**Sesion, autorizacion, credenciales y datos personales**

- **Q-transversal-26** · ambas · decision_equipo
  ¿Cómo se implementa la sesión de la app y su seguridad? Decidir: (a) cookie HttpOnly/Secure/SameSite firmada respaldada en servidor (BD/Redis) o stateless (JWT); (b) duración (8 h, 7 días, "recordarme"), expiración por inactividad y cierre de sesión global; (c) si al retirar a un ayudante (R2.1.9) o cambiar sus permiso…
- **Q-transversal-28** · parcial · decision_equipo
  ¿Cómo se almacenan los secretos y tokens (refresh_token de Canvas, archivo .pem de la GitHub App, webhook secret, client_secret de Google): cifrados en la BD y con qué clave y gestor, o en variables de entorno del despliegue? ¿Se ofrece al profesor un botón "revocar / rotar credenciales del curso"? ¿Qué muestra la UI s…
- **Q-transversal-29** · final · decision_equipo
  Si el refresh token del profesor deja de funcionar (revocó la app en Canvas, replace_tokens, Developer Key deshabilitada, profesor retirado del curso), todos los jobs del curso fallan de madrugada. ¿Cómo se detecta (401 en el refresh), cómo se pausa el curso para evitar una tormenta de reintentos, y cómo se avisa (bann…
- **Q-transversal-30** · final · decision_equipo
  ¿Qué datos personales de estudiantes se persisten y qué se comunica sobre ellos? Decidir: (a) lista blanca de campos guardados (nombre, correo, sis_user_id, canvas_user_id, login de GitHub, avatar) y descarte explícito de los que llegan en las respuestas y no se necesitan —GET /enrollments devuelve el objeto grades con…
**Integracion con APIs externas: limites, concurrencia y resiliencia**

- **Q-transversal-33** · ambas · decision_equipo
  ¿Existe un limitador de tasa COMPARTIDO por instalación de GitHub y por token de Canvas entre todos los procesos que escriben, o cada worker tiene su propio throttle? Decidir: (a) para Canvas, si se fija concurrencia 1 por token (cola secuencial por curso) y cómo se coordina cuando el mismo token del profesor lo usan a…
- **Q-transversal-34** · ambas · decision_equipo
  ¿Cuál es la política uniforme de reintentos por tipo de fallo y cuándo se deja de reintentar? Decidir: 5xx y timeouts (backoff exponencial: ¿máximo de intentos y tope de espera?), 403/429 por rate limit (respetar retry-after y x-ratelimit-reset), 401 token inválido (no reintentar, marcar credencial rota), 404 recurso e…
- **Q-transversal-35** · ambas · decision_equipo
  ¿Se implementa un iterador genérico de paginación que siga el header Link opaco de Canvas y GitHub, con tests y un límite de seguridad de páginas para evitar bucles infinitos, o se usan octokit.paginate y una librería para Canvas? En la UI, ¿las tablas son paginadas o virtualizadas para cursos grandes (200+ estudiantes…
- **Q-transversal-36** · parcial · decision_equipo
  ¿Qué timeouts se fijan: cliente HTTP hacia Canvas y GitHub (p. ej. 30 s), duración máxima de un job, y duración máxima de una request web (los PaaS suelen cortar a unos 30 s)? ¿El checklist de verificación de R2.1.6 (8 chequeos, que incluyen crear y borrar un repositorio temporal) se ejecuta dentro de la request, o de …
- **Q-transversal-39** · ambas · verificar_empiricamente
  Si el profesor y los ayudantes evalúan las apps de varios equipos del curso el mismo día contra la MISMA organización de GitHub o el mismo curso de Canvas, ¿qué límites se comparten y cómo se comporta la app al chocar con ellos? Verificar empíricamente: si los límites secundarios de GitHub (80 requests generadoras de c…
**Consistencia de efectos externos, trabajos en cola y recuperacion**

- **Q-transversal-40** · ambas · decision_equipo
  Para las acciones disparadas desde la UI —"crear repositorio base", "sincronizar ahora", "reintentar todos los fallidos", "reenviar invitación", "publicar nota" y "enviar anuncio"—: ¿qué garantía de idempotencia se exige (botón deshabilitado mientras corre, token de idempotencia por formulario, cola con deduplicación) …
- **Q-transversal-41** · ambas · decision_equipo
  ¿Cuál es la regla única de consistencia entre la base de datos y los efectos externos? Decidir: (a) el orden obligatorio: ¿se persiste una fila de intención ANTES de llamar (con el nombre del repositorio, el destinatario, el SHA del tag, el payload de la nota) y se marca el resultado después, o se llama primero y se re…
- **Q-transversal-44** · ambas · decision_equipo
  ¿Se escribe un catálogo cerrado de fallas DEL LADO DEL ESTUDIANTE, complementario al catálogo de errores de la UI docente, con cada caso acompañado de su texto de autoayuda, la ubicación de ese texto, si la app la detecta y con qué señal, y quién la resuelve? Casos mínimos a cubrir: no llegó el correo de invitación o c…

## infraestructura — Infraestructura

[Abrir el documento completo](area-infraestructura.md)

**Decisiones estructurales de plataforma y stack**

- **Q-infraestructura-01** · ambas · decision_equipo
  ¿Con que lenguaje y framework se construye la aplicacion (backend y frontend), decidido segun la experiencia real de cada integrante y no segun la recomendacion del estudio de APIs? ¿Que integrante domina cada capa, que librerias cliente se usaran para GitHub y para Canvas, y cuanto tiempo de aprendizaje se acepta cons…
- **Q-infraestructura-02** · ambas · decision_equipo
  ¿La arquitectura es un monolito con render en servidor (un solo servicio desplegable, cookies de sesion) o una API + SPA separada (dos deploys, CORS, autenticacion por token, monorepo o dos repositorios)? Si es SPA, ¿se sirve desde el mismo origen que la API o desde otro dominio?
- **Q-infraestructura-03** · ambas · decision_equipo
  ¿Que motor de base de datos y que proveedor se usan: PostgreSQL gestionado por el PaaS, Postgres externo (Neon, Supabase), MySQL/MariaDB, SQLite en disco (se pierde en redeploy si el filesystem es efimero) o MongoDB? ¿Quien es dueño de la cuenta del proveedor y quien tiene acceso a la base de produccion?
- **Q-infraestructura-04** · ambas · decision_equipo
  ¿En que proveedor y con que plan se despliega la aplicacion, y que presupuesto se acepta, sabiendo que los planes gratuitos suelen suspender el servicio tras inactividad (lo que detiene cron y workers y rompe R2.3.10, R2.4.5 y R2.6.1) y que la app debe seguir viva al menos hasta el 20-oct? ¿El equipo esta dispuesto a p…
- **Q-infraestructura-05** · ambas · decision_equipo
  ¿Se fija desde ahora una URL HTTPS definitiva y publica (subdominio del proveedor, con TLS incluido, o dominio propio de ~US$10/año con DNS y certificado) que se use igual en la parcial y en la final, quede congelada antes del 16-sep y sea la misma que se entrega el 6-oct? Los redirect URIs de Google, de la Developer K…
**Cuentas, instancias y credenciales de los servicios externos**

- **Q-infraestructura-06** · ambas · dependencia_externa
  ¿Contra que instancia(s) de Canvas se desarrolla y se demuestra: la instancia institucional de la universidad con un curso del ramo (requiere Developer Key emitida por el administrador), Free-for-Teacher (canvas.instructure.com) con un curso de prueba creado por el equipo, o Canvas open-source autoalojado en Docker? ¿Q…
- **Q-infraestructura-07** · ambas · dependencia_externa
  Si se usa la instancia institucional: ¿quien solicita la Developer Key (¿el profesor del ramo ante el administrador de Canvas?), con que redirect_uri exacta (debe ser la URL publica definitiva), con que scopes, en que plazo se espera respuesta y cual es la fecha limite para abandonar este camino y pasar al plan B?
- **Q-infraestructura-08** · parcial · verificar_empiricamente
  ¿Es efectivo que en Free-for-Teacher (canvas.instructure.com) un usuario puede crear Developer Keys (client_id/secret OAuth2) para su propia cuenta, o solo puede generar tokens de acceso manuales por usuario? Debe probarse empiricamente entrando a canvas.instructure.com y buscando Admin → Developer Keys. Si NO es posib…
- **Q-infraestructura-09** · parcial · verificar_empiricamente
  Si se usa Free-for-Teacher: ¿permite crear secciones multiples, group sets, overrides por seccion y por estudiante, rubricas, anuncios y conversaciones via API con el token del profesor? ¿Hay limites de estudiantes o de invitaciones por curso?
- **Q-infraestructura-10** · ambas · dependencia_externa
  ¿Quien crea el proyecto de Google Cloud y la pantalla de consentimiento OAuth, y con que cuenta (personal de un integrante o cuenta del equipo)? ¿El proyecto queda en modo "Testing" (maximo 100 usuarios de prueba agregados a mano, lo que obliga a registrar los gmail del profesor y de los ayudantes evaluadores antes del…
- **Q-infraestructura-11** · ambas · decision_equipo
  ¿Que organizacion de GitHub se usa para la demo del 16-sep y para la revision: una organizacion nueva del equipo (plan Free), la organizacion del curso administrada por el profesor, o ambas? ¿Quienes son owners de cada una? ¿Es la misma organizacion donde vive el codigo fuente entregable o una separada para no mezclar …
- **Q-infraestructura-12** · ambas · decision_equipo
  ¿Bajo que cuenta se registra la GitHub App: la cuenta personal de un integrante o una organizacion del equipo (transferible, con varios administradores)? ¿Quien custodia la clave privada .pem y el webhook secret, y como se comparten con el resto del equipo y con el despliegue? ¿Se marca la App como publica para que el …
- **Q-infraestructura-13** · ambas · decision_equipo
  ¿Se activa "enforce scopes" en la Developer Key de Canvas y se enumera la lista exacta de scopes url:METHOD|path necesarios, o se deja sin scopes (token con todos los permisos del profesor)? En la GitHub App, ¿se piden solo Administration (write), Contents (write) y Metadata (read), y Members (write) unicamente si se d…
- **Q-infraestructura-14** · parcial · verificar_empiricamente
  ¿Se hara una prueba end-to-end (fecha limite propuesta: antes del 10-sep / semana 1) con la GitHub App instalada en la organizacion de prueba y el installation token, verificando que POST /orgs/{org}/repos, PATCH is_template, POST /repos/{t}/{r}/generate, PUT collaborators (201 vs 204) y POST /git/refs devuelven 201/20…
**Ejecucion automatica: scheduler, colas e ingesta de actividad**

- **Q-infraestructura-15** · ambas · decision_equipo
  Si el hosting duerme la instancia por inactividad (Render Free ~15 min), ¿como se garantiza que los jobs periodicos (aprovisionamiento cada 2 min, snapshots cada 5, sincronizacion con Canvas cada 10, informe a las 07:00) realmente se ejecuten? Si se usa un scheduler externo que llama a endpoints internos, ¿como se aute…
- **Q-infraestructura-16** · ambas · decision_equipo
  ¿Se usa una cola con Redis (BullMQ / Celery), que exige un servicio Redis adicional (Upstash free 10k comandos/dia, Render Redis free efimero), una cola respaldada en la propia base de datos (pg-boss, Solid Queue, django-q2, tabla jobs + SELECT ... FOR UPDATE SKIP LOCKED), o ninguna cola formal (cron en proceso que bar…
- **Q-infraestructura-17** · ambas · decision_equipo
  ¿El scheduler y los workers corren dentro del mismo proceso web (un solo servicio gratuito, con riesgo de bloquear requests y de doble ejecucion si el PaaS levanta dos instancias durante un rolling deploy) o como servicio aparte (el background worker es pago en Render)? Si es un solo proceso, ¿como se garantiza un unic…
- **Q-infraestructura-18** · ambas · decision_equipo
  ¿Como se implementa el "lock por sujeto" del worker de creacion de repositorios y del job de snapshot (advisory lock de Postgres, SELECT FOR UPDATE SKIP LOCKED, lock en Redis, columna locked_until)? Si un job muere a mitad por reinicio del proceso, ¿en cuanto expira el lock, quien lo retoma, cuantos reintentos hay ante…
**Repositorios generados: identidad, visibilidad y proteccion**

- **Q-infraestructura-21** · ambas · decision_equipo
  ¿Que identidad de committer/author llevan los commits que la aplicacion hace al repositorio base (PUT /contents) y los tags: el nombre y correo de un bot del curso, la identidad <app>[bot], o el profesor? ¿Los repositorios base y de estudiantes se crean privados por defecto (sin opcion) o el profesor puede elegir la vi…
**Secretos, cifrado y entornos**

- **Q-infraestructura-23** · ambas · decision_equipo
  ¿Donde viven los secretos (.pem de la GitHub App, client_id/secret de Canvas, client secret de Google, webhook secret, clave de cifrado de tokens, credenciales de email, DATABASE_URL): variables de entorno del PaaS, gestor de secretos, archivo .env cifrado (sops/dotenv-vault)? ¿Como se comparten entre integrantes (gest…
**Despliegue, migraciones y control de versiones**

- **Q-infraestructura-30** · ambas · decision_equipo
  ¿El deploy se hace con Dockerfile (mismo artefacto en local y produccion) o con buildpacks nativos del PaaS? ¿Como se hace rollback: redeploy del commit anterior (¿y las migraciones ya aplicadas?), o imagen/version previa? ¿Cuanto tarda un deploy y como se evita perder jobs en curso durante el reinicio (graceful shutdo…

## proceso — Proceso del equipo

[Abrir el documento completo](area-proceso.md)

**Organizacion del equipo, cierre de decisiones y planificacion**

- **Q-proceso-02** · ambas · decision_equipo
  ¿Quién decide las respuestas a este banco de preguntas de alcance, dónde se registran, con qué fechas de corte y de congelamiento, y quién responde por cada dependencia externa con fecha de "listo"?
- **Q-proceso-03** · ambas · decision_equipo
  ¿Cuál es el canal oficial para resolver con el profesor del ramo las preguntas de alcance que dependen de él, quién las consolida y envía, con qué fecha límite y cómo se registran las respuestas?
**Alcance de cada entrega**

- **Q-proceso-06** · parcial · decision_equipo
  ¿R2.1.7–R2.1.9 (co-profesores, ayudantes, retiro) quedan fuera de la demo del 16-sep o el equipo los incluye, y los evaluadores entrarán al mismo curso demo cada uno con su propia cuenta?
- **Q-proceso-07** · ambas · decision_equipo
  ¿Qué comunicaciones deben mostrarse funcionando el 16-sep y cómo se evidenciará ante el evaluador que el mensaje llegó al estudiante, dado que la entrega por email depende de las preferencias de notificación de Canvas que la app no controla?
- **Q-proceso-09** · ambas · decision_equipo
  ¿El equipo evalúa LTI 1.3 y GitHub Classroom como alternativas a la estrategia de enrolamiento elegida, y documenta la comparación y la justificación en un ADR?
**Datos de demostracion, cuentas y entorno de prueba**

- **Q-proceso-10** · ambas · dependencia_externa
  ¿Cuál es el dataset de demostración concreto en Canvas para la parcial y para la final, qué casos borde deliberados incluye, existe un script de seed/reset y cuántos ensayos completos cronometrados se harán sobre el entorno real?
- **Q-proceso-11** · parcial · dependencia_externa
  ¿Cómo se crean los estudiantes ficticios en Canvas, puede el equipo iniciar sesión como ellos y cuántas cuentas se necesitan?
- **Q-proceso-12** · ambas · decision_equipo
  ¿Cuántas cuentas de GitHub de "estudiante" se necesitan, de dónde salen y cómo se generará la actividad de commits distribuida en el tiempo que exige el dashboard y el timeline?
**Ejecucion de la demo, entrega y recuperacion**

- **Q-proceso-23** · ambas · decision_equipo
  ¿La demo del 16-sep se ejecuta contra la producción desplegada o desde localhost, con qué congelamiento y precalentamiento, y qué commit o tag corresponde a cada entrega y hasta cuándo se congela el deploy?
