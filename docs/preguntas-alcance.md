# Preguntas de alcance — Proyecto 2 (recuperadas del workflow)

Salida cruda del workflow `scope-questions-discovery`, corrida `wf_783f1f9e-bb7` del 8 de septiembre de 2026.

**Estado:** el workflow murió por límite de sesión. Se completaron el descubrimiento (11 lentes, 663 preguntas) y la primera ronda crítica (+120). Fallaron la segunda ronda crítica, la verificación adversarial y la consolidación. Por eso esta lista está **sin deduplicar semánticamente y sin verificar** contra el enunciado: algunas preguntas pueden estar repetidas con otras palabras o ya respondidas en el PDF.

**Total:** 783 preguntas.

| Tipo | N |
|---|---|
| Decisión del equipo | 648 |
| Verificar empíricamente | 76 |
| Dependencia externa | 38 |
| Investigable en docs | 21 |

| Entrega | N |
|---|---|
| Parcial (16-sep) | 153 |
| Ambas entregas | 211 |
| Final (6-oct) | 419 |

## Índice

- [2.1](#2-1) — 98 preguntas (P001–P098)
- [2.2](#2-2) — 110 preguntas (P099–P208)
- [2.3](#2-3) — 116 preguntas (P209–P324)
- [2.4](#2-4) — 73 preguntas (P325–P397)
- [2.5](#2-5) — 72 preguntas (P398–P469)
- [2.6](#2-6) — 70 preguntas (P470–P539)
- [2.7](#2-7) — 83 preguntas (P540–P622)
- [3.1](#3-1) — 22 preguntas (P623–P644)
- [3.2](#3-2) — 4 preguntas (P645–P648)
- [3.3](#3-3) — 2 preguntas (P649–P650)
- [4](#4) — 6 preguntas (P651–P656)
- [transversal](#transversal) — 50 preguntas (P657–P706)
- [infraestructura](#infraestructura) — 46 preguntas (P707–P752)
- [proceso](#proceso) — 31 preguntas (P753–P783)

---

## 2.1

### P001. ¿Cómo reconoce el estudiante que la invitación de GitHub es legítima y no phishing? Verificar quién aparece como invitador en el correo y en github.com cuando la GitHub App agrega colaboradores (¿'<app>[bot]', el nombre de la org, o nadie?). Y decidir: (a) si la organización tendrá perfil identificable (nombre del curso/universidad, descripción, avatar, email de contacto, dominio verificado) antes de la primera invitación; (b) si el mensaje de Canvas menciona el nombre exacto de la org, el nombre del repo y quién figurará como invitador, para que el estudiante pueda cotejar; (c) quién es responsable de configurar ese perfil (equipo u owner de la org).

- **Requisitos:** R2.1.5, R2.3.9, R2.3.12
- **Área declarada:** 2.1 / 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un estudiante que descarta la invitación por desconfianza queda en COLLABORATORS_PENDING indefinidamente; fija contenido del mensaje de R2.3.12 y una tarea de configuración de la org previa a la demo.
- **Estudio de APIs:** §5.4 explica que PUT collaborators devuelve 201 y el estudiante debe aceptar por email; no aborda quién figura como invitador ni la legitimidad percibida de la org.

### P002. ¿Cómo puede el profesor ENSAYAR la experiencia del estudiante antes de abrir el proceso al curso? Canvas ofrece 'Student View' (Test Student), pero la app lo excluye del roster, así que el profesor nunca verá el ciclo entrega→comentario→invitación→mensaje. Opciones: permitir un 'modo ensayo' donde el Test Student sí dispara el ciclo pero contra un repo de prueba que luego se borra; usar una cuenta de estudiante real de prueba provista por la instancia; mostrar en la app una vista previa estática de cada mensaje; no ofrecer ensayo. ¿Se incluye en la guía de vinculación (R2.1.6) un paso 'prueba el flujo como estudiante'?

- **Requisitos:** R2.1.6, R2.2.5, R2.3.12
- **Área declarada:** 2.1 / 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define si el Test Student tiene un tratamiento especial (no solo exclusión) y agrega o no un paso al asistente de configuración.
- **Opciones planteadas:**
  - Modo ensayo con Test Student y repo temporal
  - Cuenta de estudiante de prueba real
  - Vista previa estática de mensajes
  - Sin ensayo
- **Estudio de APIs:** §4.1 y §14 indican filtrar siempre al Test Student para no crearle repo; no contemplan usarlo para ensayar el flujo.

### P003. ¿La URL base de Canvas será configurable por curso (el profesor la escribe al vincular) o fija por variable de entorno del deploy? Si es configurable, ¿cada instancia necesita su propia Developer Key (client_id/secret) y cómo se administran esas credenciales?

- **Requisitos:** R2.1.4
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Una URL fija impide que un revisor con otra instancia pruebe la vinculación; una URL variable exige gestión de múltiples credenciales OAuth en el spec.
- **Opciones planteadas:**
  - Fija por variable de entorno
  - Configurable por curso con una sola Developer Key
  - Configurable con tabla de instancias y credenciales
- **Estudio de APIs:** §3.2 recomienda guardar canvas_base_url porque 'la instancia varía'.

### P004. ¿La vinculación será un asistente paso a paso (Canvas → GitHub → verificación) con estado persistente que se pueda abandonar y retomar, o pantallas independientes? ¿Qué muestra un curso recién creado sin vinculaciones (estado vacío) y qué acciones bloquea (p. ej. no permitir crear tareas hasta que ambas vinculaciones estén verificadas)?

- **Requisitos:** R2.1.4, R2.1.5, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el flujo de onboarding evaluado en la parcial y las reglas de bloqueo entre etapas.
- **Estudio de APIs:** §3.3 propone el flujo 'Conectar organización' y una pantalla de verificación con checks y botón reintentar.

### P005. La verificación propuesta crea y borra un repositorio temporal en la org del profesor. ¿Se acepta ese efecto secundario visible (queda en el audit log de la org) o se verifica solo leyendo los permisos de la instalación? ¿Qué checks son bloqueantes para continuar y cuáles solo advertencias (p. ej. '0 estudiantes' en un curso aún sin inscripciones, '0 tareas')?

- **Requisitos:** R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Determina la lista exacta de checks del spec, su severidad y si la verificación puede dejar rastros en la organización del usuario.
- **Estudio de APIs:** §3.3 propone crear un repo '--verificacion-temporal' y borrarlo, más 7 checks adicionales con ✅/❌.

### P006. El registro es abierto (cualquier gmail crea cuenta y cursos) y la URL será pública durante las dos semanas de revisión. ¿Se fijan cuotas por usuario o por curso (número de cursos, tareas, repos creados por día, mensajes Canvas por hora, emails) para proteger el rate limit compartido de la instalación de la GitHub App y la cuota del proveedor de email, o se acepta el riesgo? ¿Crear cursos requiere aprobación/lista blanca del administrador (R2.1.1) o solo vincular GitHub lo requiere? ¿Qué ve un usuario que excede una cuota?

- **Requisitos:** R2.1.1, R2.1.2, R2.1.3
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define reglas de negocio de límites, el rol del admin y mensajes de error; sin cuotas un solo usuario puede agotar recursos compartidos durante la revisión.
- **Opciones planteadas:**
  - Registro abierto sin cuotas
  - Cuotas por usuario configurables por variable de entorno
  - Aprobación del admin para crear cursos
- **Estudio de APIs:** §3.1 valida solo el sufijo gmail.com y `email_verified`; no aborda abuso, cuotas ni aprobación.

### P007. Si el profesor que vincula tiene su TeacherEnrollment limitado a su sección (`limit_privileges_to_course_section=true`), la API le devuelve solo estudiantes, secciones y overrides visibles para esa sección: el sync marcaría al resto como inexistente/retirado y las fechas de otras secciones serían invisibles. ¿El checklist de R2.1.6 detecta esa restricción (p. ej. GET /courses/:id/enrollments?user_id=self) y bloquea o advierte? ¿Se exige que el vinculador vea el curso completo o se soporta explícitamente vincular 'solo mi sección'?

- **Requisitos:** R2.1.4, R2.1.6, R2.2.1, R2.4.2
- **Área declarada:** 2.1 / 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Evita bajas masivas falsas de estudiantes y fechas incorrectas; agrega un ítem al checklist y una regla sobre quién puede vincular.
- **Opciones planteadas:**
  - Bloquear vinculación con profesor limitado a sección
  - Advertir y permitir
  - Soportar cursos 'de una sección' como alcance declarado
- **Estudio de APIs:** §3.2 lista cursos con `enrollment_type=teacher`; §4 asume visibilidad completa del roster; no menciona `limit_privileges_to_course_section`.

### P008. Las instituciones definen roles personalizados derivados de Teacher/Student/TA (p. ej. 'Profesor coordinador', 'Alumno oyente', 'Ayudante corrector'). ¿Los filtros `enrollment_type=teacher` (listar cursos) y `type[]=StudentEnrollment` (roster) incluyen esos roles personalizados, o hay que filtrar por `role_id`/`base_role_type`? ¿Un rol personalizado basado en Student cuenta como estudiante para crear repo, y uno basado en TA para importar ayudantes desde Canvas?

- **Requisitos:** R2.1.4, R2.2.1, R2.1.8
- **Área declarada:** 2.1 / 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Ambas entregas
- **Por qué importa:** Determina los parámetros exactos de las llamadas de sync y a quién se le crea repo en la instancia institucional.
- **Estudio de APIs:** §4.1 menciona `enrollment_role_id` como parámetro pero no la distinción entre roles base y personalizados.

### P009. Si la organización destino es institucional con SAML SSO obligatorio o lista de IP permitidas, o si los estudiantes usan cuentas Enterprise Managed Users (login con sufijo `_empresa`, que no pueden ser colaboradores fuera de su enterprise): ¿la app lo soporta o lo declara fuera de alcance? ¿El checklist de R2.1.6 detecta SAML/IP allowlist (que puede bloquear los installation tokens desde el hosting) y la validación de R2.2.4 detecta cuentas EMU para avisar al estudiante que necesita una cuenta personal?

- **Requisitos:** R2.1.5, R2.1.6, R2.2.4, R2.3.9
- **Área declarada:** 2.1
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Condiciona qué organizaciones puede usar un profesor real, agrega ítems al checklist y un caso de rechazo en la validación de usuarios GitHub.
- **Estudio de APIs:** No lo aborda (§2 y §3.3 asumen una organización estándar sin SSO ni IP allowlist).

### P010. Los estudiantes con `push` pueden agregar workflows de GitHub Actions y abrir Codespaces en sus repos privados, consumiendo los minutos y almacenamiento del plan de la org (y GitHub bloquea Actions/pushes de LFS cuando la org agota su cuota facturable). ¿La app deshabilita Actions al crear cada repo, exige una política de org ('Actions disabled' o 'solo repos seleccionados') verificada en el checklist, o se acepta el consumo? ¿Se permite en cambio a los profesores incluir workflows de autocorrección en el repo base (R2.3.6), lo que exige el permiso Workflows en la App?

- **Requisitos:** R2.1.5, R2.3.7, R2.1.6, R2.3.6
- **Área declarada:** 2.1 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define permisos de la App, configuración por repo al crearlo, un ítem del checklist y el alcance de autocorrección.
- **Opciones planteadas:**
  - Deshabilitar Actions por repo al crearlo
  - Exigir política de org y verificarla
  - Permitir Actions y documentar el riesgo de cuota
- **Estudio de APIs:** §5.3 menciona el permiso Workflows solo para subir archivos en .github/workflows; no aborda consumo de minutos, Codespaces ni políticas de org.

### P011. ¿Se activa en la GitHub App 'Request user authorization (OAuth) during installation' para obtener un user-to-server token del profesor que permita (a) confirmar que quien instaló es owner de la org, (b) listar sus organizaciones para validar o preseleccionar la org antes de salir de la app, y (c) guardar su login de GitHub para agregarlo como docente a los repos? ¿O se evita para no pedir permisos adicionales y se confía en la instalación como única prueba de control de la org?

- **Requisitos:** R2.1.5, R2.1.6, R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Cambia el flujo de vinculación (un consentimiento adicional), los datos guardados del profesor y la capacidad de verificar ownership en R2.1.6.
- **Opciones planteadas:**
  - Solo instalación (setup_url)
  - Instalación + autorización de usuario
  - Autorización de usuario opcional posterior ('conectar mi GitHub')
- **Estudio de APIs:** §3.3 usa únicamente installations/new + setup_url; no menciona la autorización de usuario durante la instalación.

### P012. ¿Qué debe hacer y mostrar la app si la organización de GitHub impide completar el proceso: exige 2FA y el estudiante no la tiene, restringe invitaciones a outside collaborators, el plan de la org limita algo (repos privados, colaboradores, características), o la creación desde template falla por permisos? ¿Se detectan estas restricciones en la verificación de vinculación (R2.1.6) antes de crear la tarea? Verificar en una org Free real los límites vigentes.

- **Requisitos:** R2.1.5, R2.1.6, R2.3.7, R2.3.9, R2.3.11
- **Área declarada:** 2.1 / 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Ambas entregas
- **Por qué importa:** Determina qué chequeos incluye el checklist de vinculación y qué códigos de error del worker son 'definitivos' vs 'transitorios'.
- **Estudio de APIs:** §3.3 checklist con repo temporal; §2.3 y Apéndice A.1–A.2 piden verificar permisos; §14 'revisen el límite de colaboradores en repos privados de organización'.

### P013. Si la GitHub App es desinstalada o suspendida en la org, o el profesor revoca el token de Canvas, pierde su enrollment de Teacher o el refresh token deja de funcionar: ¿cómo se detecta (webhook installation, 401/403 en jobs), qué estado toma el curso ('vinculación rota'), qué operaciones se pausan (worker, snapshots, notificaciones, informe), a quién se avisa y por qué canal (banner, email), y cómo se re-vincula sin perder repos, mapeos ni snapshots?

- **Requisitos:** R2.1.4, R2.1.5, R2.1.6, R2.3.10, R2.4.5, R2.6.1
- **Área declarada:** 2.1 / 2.3 / 2.4 / 2.6 (infraestructura)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el estado de salud del curso, la degradación controlada de los cron jobs y el flujo de recuperación; sin esto, los jobs fallan en silencio.
- **Estudio de APIs:** §1.1 subraya que el refresh token es crítico para jobs nocturnos; §3.3 checklist de verificación. No define detección de pérdida de acceso ni recuperación.

### P014. ¿Puede un mismo curso de Canvas o una misma organización de GitHub vincularse a más de un curso de la app (dos profesores lo crean por separado; la org se reutiliza semestre a semestre)? Si se permite, ¿cómo se evitan colisiones de nombres de repos y dobles notificaciones a los mismos estudiantes? Si no, ¿qué mensaje ve el segundo profesor y cómo se le invita al curso existente?

- **Requisitos:** R2.1.3, R2.1.4, R2.1.5, R2.1.7, R2.3.8
- **Área declarada:** 2.1 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija restricciones de unicidad en la vinculación y el diseño de la plantilla de nombres (inclusión de período/curso).
- **Estudio de APIs:** §5.4 incluye {curso}-{periodo} en el nombre; no aborda unicidad de vinculación Canvas/org entre cursos de la app.

### P015. ¿Puede el profesor cambiar o desvincular la organización de GitHub (o el curso de Canvas) cuando ya existen tareas con repos, mapeos y snapshots? Opciones: prohibir mientras existan tareas; permitir con confirmación dejando los repos 'huérfanos' marcados; migrar (transferir repos a la nueva org). ¿Qué se conserva y qué se invalida en cada caso (mapeos, snapshots, dashboards, correcciones)?

- **Requisitos:** R2.1.4, R2.1.5, R2.1.6, R2.3.4, R2.4.7
- **Área declarada:** 2.1 / 2.3 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define las restricciones de edición del curso y el ciclo de vida de los datos dependientes de la vinculación.
- **Estudio de APIs:** No lo aborda.

### P016. Al eliminar una tarea (o el curso) en la app con repos ya creados y notas publicadas en Canvas: ¿se borran los repos de GitHub, se archivan, o no se tocan? ¿Es un borrado lógico recuperable? ¿Se exige confirmación tipeando el nombre y se notifica a los estudiantes? ¿Qué pasa con los correctores con entregas asignadas y con el informe diario?

- **Requisitos:** R2.1.3, R2.3.4, R2.3.7, R2.6.1, R2.7.1
- **Área declarada:** 2.1 / 2.3 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Decide si la app ejecuta acciones destructivas sobre GitHub y qué historial sobrevive; afecta permisos requeridos y el flujo de confirmación.
- **Opciones planteadas:**
  - Soft delete en la app; GitHub intacto
  - Soft delete + archivar repos en GitHub
  - Borrado duro con confirmación reforzada
- **Estudio de APIs:** No lo aborda.

### P017. Al retirar a un ayudante que tiene entregas asignadas pendientes, en curso o ya calificadas: ¿sus asignaciones pendientes vuelven a 'sin asignar', se reasignan automáticamente (a quién) o se bloquea el retiro hasta reasignar? ¿Las calificaciones que ya publicó conservan su autoría en el historial? ¿Se le revoca acceso a la org/repos de GitHub si se le dio? ¿Se le da de baja del informe diario automáticamente?

- **Requisitos:** R2.1.9, R2.6.3, R2.7.1, R2.7.7
- **Área declarada:** 2.1 / 2.7 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el flujo de retiro (R2.1.9) y sus efectos en corrección, auditoría y suscripciones.
- **Estudio de APIs:** §3.4: 'reasignen las entregas que tenía pendientes y revoquen su acceso a la org'. No dice si es automático ni qué pasa con lo calificado.

### P018. ¿Puede un mismo usuario ser profesor en un curso y ayudante en otro (rol por curso)? ¿Puede ser profesor y ayudante en el mismo curso? ¿Puede el único profesor de un curso retirarse o degradarse, dejando el curso sin profesor? ¿Un profesor puede retirar a otro profesor (mismos permisos según R2.1.7), incluido el creador del curso?

- **Requisitos:** R2.1.1, R2.1.7, R2.1.8, R2.1.9
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el modelo de membresía (rol por curso vs global) y las invariantes mínimas (al menos un profesor por curso).
- **Estudio de APIs:** §3.4 propone RBAC por curso con roles profesor / ayudante jefe / ayudante; no aborda roles cruzados ni el último profesor.

### P019. El estudio propone que todas las escrituras a Canvas usen el token del profesor. ¿De qué profesor, si hay varios? ¿Qué pasa si ese profesor se retira del curso, revoca el token o su refresh token falla: se usa el token de otro profesor automáticamente, se pausa todo y se alerta, o se exige que cada profesor haga OAuth al ingresar? ¿Cómo se muestra en Canvas quién 'envió' mensajes/notas y cómo se audita en la app quién realmente ejecutó la acción?

- **Requisitos:** R2.1.7, R2.6.5, R2.6.6, R2.7.6
- **Área declarada:** 2.1 / 2.6 / 2.7 (transversal)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina el modelo de credenciales por curso, el failover entre tokens y la trazabilidad de acciones ejecutadas 'en nombre de' otro usuario.
- **Opciones planteadas:**
  - Token del curso = último profesor que autorizó; failover al siguiente profesor
  - Cada usuario con enrollment en Canvas usa su propio token
  - Token único del creador; si falla, curso en 'vinculación rota'
- **Estudio de APIs:** §3.4 opción A (token del profesor) vs B (token de cada ayudante), recomienda A con B como fallback; §1.1 refresh token. No resuelve múltiples profesores ni la salida del dueño del token.

### P020. R2.1.2 exige cuenta 'basada en gmail.com': ¿se rechaza a un profesor que ingresa con Google Workspace institucional (p.ej. dominio universitario), con alias googlemail.com, o con puntos y '+' en el local-part (mismo buzón: ¿misma cuenta en la app o cuentas distintas)? ¿Qué mensaje ve al ser rechazado y existe una vía alternativa de alta por el administrador (R2.1.1)?

- **Requisitos:** R2.1.1, R2.1.2
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija la regla de validación de identidad y la clave de unicidad del usuario (email normalizado vs sub de Google).
- **Estudio de APIs:** §3.1: validar sufijo @gmail.com y email_verified=true. No aborda alias ni normalización del local-part.

### P021. Para cada pantalla/acción (configuración del curso, mapeo de estudiantes, estado de repos y reintentos, repo base, dashboard, timeline, informe, comunicaciones, asignación de correctores, calificar, ver notas de otros correctores, auditoría), ¿qué puede ver y hacer cada rol (profesor y cada nivel de ayudante)? En particular: ¿un ayudante ve logins de GitHub y correos de estudiantes, puede reintentar repos, enviar mensajes a estudiantes, ver o editar calificaciones de entregas no asignadas a él? ¿Un cambio de permisos o el retiro aplican de inmediato en la sesión activa?

- **Requisitos:** R2.1.8, R2.1.9, R2.2.6, R2.3.11, R2.6.5, R2.7.2, R2.7.6, R2.7.7
- **Área declarada:** 2.1 / transversal (permisos)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El enunciado exige definir al menos 3 permisos; la matriz rol × pantalla × acción es la base de los criterios de aceptación de autorización.
- **Estudio de APIs:** §3.4 propone 7 permisos y 3 roles (profesor / ayudante jefe / ayudante); no está aprobado ni cubre vigencia inmediata de cambios.

### P022. Si el mismo estudiante (mismo canvas_user_id en la misma instancia de Canvas) está en dos cursos de la app: ¿el mapeo Canvas→GitHub es global por instancia (se reutiliza automáticamente y un cambio afecta ambos cursos) o por curso (debe volver a entregarlo)? ¿Se soportan profesores con cursos en distintas instancias de Canvas (canvas_base_url distinto) con tokens separados?

- **Requisitos:** R2.1.4, R2.2.4, R2.2.5
- **Área declarada:** 2.1 / 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la clave del mapeo (instancia+usuario vs curso+usuario) y el modelo de credenciales multi-instancia.
- **Estudio de APIs:** §3.2 recomienda guardar canvas_base_url por curso; no aborda el alcance del mapeo entre cursos.

### P023. Muchas universidades modelan cada sección como un CURSO de Canvas separado (no como secciones dentro de un curso). Si el curso real de ICC4201 o el curso demo del profesor está así, ¿la app soporta que un curso de la app se vincule a VARIOS cursos de Canvas (tratándolos como secciones virtuales con un único conjunto de repos por tarea y una sola org), obliga a crear un curso de la app por sección compartiendo la org (con riesgo de colisión de nombres y de tareas duplicadas), o declara el caso fuera de alcance? ¿Se ha verificado con el profesor cómo está modelado su curso en la instancia institucional?

- **Requisitos:** R2.1.4, R2.2.2, R2.4.2, R2.3.4
- **Área declarada:** 2.1 / 2.2
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Cambia la cardinalidad curso-app ↔ curso-Canvas de 1:1 a 1:N en el modelo de datos, el sync, las fechas por sección y el nombre de los repos; descubrirlo el 16-sep sería fatal.
- **Opciones planteadas:**
  - 1 curso app = 1 curso Canvas (un curso app por sección, misma org)
  - 1 curso app = N cursos Canvas tratados como secciones virtuales
  - Fuera de alcance documentado, con mensaje al profesor
- **Estudio de APIs:** §3.2 guarda un único canvas_course_id por curso y §4.2 asume secciones dentro de un curso; no aborda cursos de Canvas separados por sección.

### P024. Si el profesor que vincula tiene su TeacherEnrollment con limit_privileges_to_course_section=true (privilegios limitados a su sección), el sync solo verá los estudiantes de esa sección y las escrituras (mensajes, notas, anuncios) a otras secciones fallarán. ¿El checklist de verificación lee ese flag del enrollment del profesor y lo marca como bloqueante o advertencia, y qué se sugiere (que vincule otro profesor sin límite)? Verificar el comportamiento real de /enrollments y /conversations con un teacher limitado.

- **Requisitos:** R2.1.4, R2.1.6, R2.2.1, R2.6.5
- **Área declarada:** 2.1 / 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Produce un roster incompleto sin error visible y fallos posteriores difíciles de diagnosticar.
- **Opciones planteadas:**
  - Detectar y bloquear en checklist
  - Detectar y advertir
  - No manejar
- **Estudio de APIs:** §3.2 filtra cursos con enrollment_type=teacher y §3.3 define el checklist; no aborda privilegios limitados a sección.

### P025. ¿Se exige unicidad del nombre/slug de la tarea dentro del curso y del nombre del curso dentro de los cursos de un profesor (o global), o se permiten duplicados? Si dos tareas del mismo curso tienen el mismo slug, sus repos colisionarían en la org; ¿se bloquea al crear, se agrega sufijo automático, o se permite duplicar el nombre visible manteniendo slug único? ¿Y si el slug sanitizado queda vacío (nombre solo con emojis o caracteres no ASCII)?

- **Requisitos:** R2.1.3, R2.3.1, R2.3.8
- **Área declarada:** 2.1 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un evaluador que cree dos tareas 'Tarea 1' provocaría colisiones de nombres de repo o confusión en listas.
- **Opciones planteadas:**
  - Slug único por curso (bloquear duplicados)
  - Sufijo automático
  - Nombre duplicable con slug único generado
- **Estudio de APIs:** §5.2 incluye slug en Assignment y §5.4 usa {tarea} en el nombre del repo; no aborda unicidad de slug por curso.

### P026. Los evaluadores probablemente usarán ventanas de incógnito y navegadores distintos para simular un 'profesor nuevo', y suelen tener varias cuentas Google (institucional y gmail) en el mismo navegador. ¿El inicio de sesión fuerza el selector de cuentas de Google (prompt=select_account) y, tras rechazar una cuenta no gmail, ofrece 'probar con otra cuenta'? ¿Qué matriz de navegadores/versiones se soporta y se probará explícitamente en incógnito (Chrome, Firefox, Safari, Edge) para los tres flujos OAuth (Google, Canvas, instalación de GitHub App), dado que las políticas de cookies de terceros y modo privado pueden romper el retorno del callback?

- **Requisitos:** R2.1.2, R2.1.4, R2.1.5
- **Área declarada:** 2.1 / 3.1
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un login que auto-selecciona la cuenta institucional o un callback que falla en Safari privado arruina el primer minuto de la demo.
- **Opciones planteadas:**
  - prompt=select_account + botón 'cambiar de cuenta'
  - Matriz de navegadores en el spec con prueba en incógnito antes del 16-sep
  - Sin medidas
- **Estudio de APIs:** §3.1 describe Google OIDC y §1.1 el uso de state en sesión; no aborda selector de cuentas, navegadores ni modo incógnito.

### P027. ¿Qué ve exactamente el profesor en un curso recién creado y aún no vinculado (estado vacío)? ¿Un panel de 'primeros pasos' con CTA ('Paso 1: vincular Canvas', 'Paso 2: conectar GitHub', 'Paso 3: crear tu primera tarea') y las demás pestañas bloqueadas/deshabilitadas con explicación, o todas las pestañas accesibles mostrando '0 estudiantes'? ¿Se puede crear una tarea sin que ambas vinculaciones estén verificadas?

- **Requisitos:** R2.1.3, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el onboarding evaluado el 16-sep y las reglas de precondición (qué acciones requieren Canvas verificado, cuáles GitHub verificado) que el spec debe listar como reglas de negocio.
- **Estudio de APIs:** §13 hito 5 habla de 'wizard de vinculación con checklist' pero no del estado vacío ni de bloqueos por precondición.

### P028. ¿La creación + vinculación de un curso es un wizard secuencial (pasos: datos del curso → Canvas → GitHub → verificación → resumen) o un formulario único / pantalla de configuración con secciones independientes? Si es wizard: ¿orden fijo o libre (Canvas y GitHub intercambiables)?, ¿se puede abandonar a mitad y retomar más tarde conservando lo hecho (curso creado sin GitHub)?, ¿se muestra un indicador de progreso (paso 2 de 4)?

- **Requisitos:** R2.1.3, R2.1.4, R2.1.5, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es el flujo central de la demo parcial y de la evaluación de 'guía adecuada'. Determina estados intermedios del curso (borrador / parcialmente vinculado / verificado) que el modelo de datos y la UI deben soportar.
- **Opciones planteadas:**
  - Wizard lineal obligatorio
  - Wizard con pasos saltables y reanudables
  - Página de configuración con tarjetas independientes (Canvas / GitHub) cada una con su estado
- **Estudio de APIs:** §3.3 describe un flujo 'Conectar organización' + pantalla de verificación; §13 lo llama 'wizard'. No define pasos, orden ni reanudación.

### P029. ¿La conexión OAuth con Canvas es a nivel de usuario (el profesor autoriza una vez y reutiliza el token en todos sus cursos) o a nivel de curso (autoriza en cada vinculación)? ¿Dónde se muestra y gestiona esa conexión en la UI ('Mi cuenta → Conexiones' con estado, fecha de autorización y botón 'Reconectar' / 'Desconectar')? ¿Qué pasa con los cursos de un profesor si desconecta Canvas?

- **Requisitos:** R2.1.2, R2.1.4
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Cambia el wizard (si ya está conectado, el paso Canvas se reduce a elegir curso), la pantalla de cuenta, y el comportamiento de jobs nocturnos que dependen del refresh token del profesor que vinculó.
- **Opciones planteadas:**
  - Conexión por usuario, reutilizable
  - Conexión por curso
  - Ambas: por usuario con posibilidad de reautorizar por curso
- **Estudio de APIs:** §1.1 recomienda OAuth2 con token del profesor y guardar refresh_token; §3.2 dice guardar 'el id del profesor que hizo la vinculación', lo que sugiere token por usuario, sin definir la UI.

### P030. En el selector de curso de Canvas: ¿qué columnas se muestran (nombre, código, período/term, N estudiantes, estado publicado)? ¿Qué se muestra si la lista viene vacía (el usuario no es 'teacher' en ningún curso, o faltan scopes) y qué acción se ofrece? ¿Se permite como alternativa pegar la URL o ID del curso? ¿Se advierte o bloquea si ese curso de Canvas ya está vinculado a otro curso de la app (mismo profesor u otro)?

- **Requisitos:** R2.1.4
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija el contenido de la pantalla clave del wizard, el mensaje de estado vacío y la regla de unicidad Canvas-course ↔ app-course, todas visibles en la demo.
- **Estudio de APIs:** §3.2 da el endpoint con include[]=term,total_students y los campos disponibles; no aborda estado vacío, entrada manual ni duplicados.

### P031. El paso GitHub saca al profesor de la app hacia github.com para instalar la GitHub App. ¿Qué guía se le da ANTES de salir (captura/lista: 'elige la organización del curso, no tu cuenta personal'; 'selecciona All repositories')? ¿Qué se muestra al volver en cada caso anómalo: vuelve sin instalar (setup_action ≠ install), instaló en su cuenta personal en vez de una org, instaló en otra org que ya está vinculada a otro curso, o instaló con 'Only select repositories'? ¿Se puede cambiar de organización después de crear repos?

- **Requisitos:** R2.1.5, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Cada caso anómalo necesita un mensaje y una acción de recuperación en el spec; el cambio de org post-aprovisionamiento define una regla de negocio (bloquear / permitir con advertencia).
- **Estudio de APIs:** §3.3 describe redirección a /installations/new y retorno con installation_id; no cubre casos anómalos ni cambio posterior.

### P032. ¿Qué hace la app si el profesor no tiene una organización de GitHub o no es owner de la que tiene? ¿Se le explican dentro de la app los pasos para crearla (con link directo a github.com/organizations/new y requisitos: plan, repos privados) o se asume que la org existe previamente? ¿La app verifica que el profesor sea owner/admin de la org o basta con que la App esté instalada?

- **Requisitos:** R2.1.5
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define si el onboarding incluye documentación embebida para un prerrequisito externo y qué chequeo aparece en el checklist de verificación.
- **Estudio de APIs:** no lo aborda (asume una org del curso ya existente en §2.2 y §3.3).

### P033. ¿La instancia de Canvas es fija (una sola URL configurada por el equipo, p.ej. la de la universidad o canvas.instructure.com) o el profesor puede indicar su instancia en el wizard (campo 'URL de Canvas')? Si hay más de una instancia, ¿cómo se gestionan las Developer Keys de cada una y qué mensaje se muestra si la instancia no está soportada?

- **Requisitos:** R2.1.5
- **Área declarada:** 2.1
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un campo más en el wizard y un mensaje de error adicional, o una simplificación del flujo. Depende de si consiguen Developer Key institucional o usan Free-for-Teacher.
- **Opciones planteadas:**
  - Instancia única fija en configuración del servidor
  - Selector entre instancias preconfiguradas
  - Campo libre de URL
- **Estudio de APIs:** §3.2 dice guardar canvas_base_url porque 'la instancia varía'; §1.2 propone Free-for-Teacher como plan B. No decide si la UI expone la instancia.

### P034. ¿Cuál es la lista definitiva de ítems del checklist de verificación y cómo se redacta cada uno en lenguaje no técnico? El estudio propone 8 (org existe + App instalada; podemos crear repos; podemos invitar colaboradores; curso Canvas responde; vemos estudiantes; vemos secciones; vemos tareas; podemos publicar anuncios). ¿Se agregan: permisos de la App suficientes (Administration/Contents/Members); token de Canvas con scopes de escritura (comentar entregas, enviar mensajes, publicar anuncios, calificar); curso Canvas publicado y vigente; existe al menos un group set; límite de repos privados/colaboradores del plan de la org; el profesor es owner de la org? ¿Cada ítem muestra: nombre, resultado, detalle técnico plegable y acción correctiva con link?

- **Requisitos:** R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es literalmente el requisito R2.1.6 y lo que se evalúa como 'guía adecuada' el 16-sep. El spec necesita la tabla exacta de chequeos con su llamada, su criterio de éxito y su texto.
- **Estudio de APIs:** §3.3 propone la tabla de 8 chequeos con llamada asociada y sugiere renderizar ✅/❌ con botón 'reintentar'.

### P035. El chequeo 'podemos crear repos' propuesto crea y borra un repo temporal en la organización del profesor. ¿El equipo acepta que la verificación tenga efectos secundarios visibles (el repo aparece brevemente, queda en el audit log de la org, puede requerir permiso adicional de borrado)? ¿Se avisa al profesor antes de ejecutarlo? ¿Alternativa: inspeccionar solo los permisos de la instalación sin crear nada, aceptando menor certeza?

- **Requisitos:** R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Cambia el texto del checklist, los permisos que pide la App y la confianza del profesor en la herramienta durante la demo.
- **Opciones planteadas:**
  - Crear y borrar repo temporal con aviso previo
  - Solo inspección de permisos de la instalación
  - Crear un repo permanente de verificación (p.ej. '.curso-config') que además sirva de bitácora
- **Estudio de APIs:** §3.3 propone explícitamente POST repo '--verificacion-temporal' → 201 y luego DELETE. Apéndice A.1 advierte que los permisos de creación deben verificarse empíricamente.

### P036. ¿Los resultados del checklist tienen tres niveles (correcto / advertencia / bloqueante)? ¿Qué ítems bloquean acciones posteriores (p.ej., no crear tareas hasta que GitHub verifique) y cuáles solo advierten (0 estudiantes visibles todavía, sin group sets)? ¿Existe 'continuar de todos modos' y quién puede usarlo?

- **Requisitos:** R2.1.6, R2.3.7
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Convierte el checklist en reglas de negocio verificables (precondiciones por acción) y evita que la UI deje avanzar a un estado donde el worker fallará silenciosamente.
- **Estudio de APIs:** §3.3 solo distingue verde/rojo.

### P037. ¿El checklist es re-ejecutable en cualquier momento desde Configuración del curso ('Verificar conexiones') y además se ejecuta automáticamente en background (p.ej., en cada sync) mostrando un banner en el curso si algo se rompió (token de Canvas revocado, App desinstalada de la org, profesor perdió rol en Canvas)? ¿Cómo y cuándo se entera el equipo docente si la instalación se desinstala a mitad de semestre?

- **Requisitos:** R2.1.6, R2.3.11
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la salud de conexiones como un estado persistente del curso con su indicador y su notificación, en vez de una pantalla única del onboarding.
- **Estudio de APIs:** §3.3 sugiere botón 'reintentar' en la pantalla de verificación; no habla de monitoreo continuo ni de desinstalación.

### P038. ¿El checklist se muestra progresivamente (cada ítem pasa de 'verificando…' a resultado a medida que responde la API) o solo cuando terminan todos? ¿Cuál es el timeout por ítem y qué texto se muestra si Canvas o GitHub no responden ('No pudimos contactar a Canvas; reintentar')? ¿Se puede reintentar un solo ítem?

- **Requisitos:** R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Los chequeos implican varias llamadas de red en serie (throttling Canvas); la percepción de espera y el manejo de timeouts son parte de la usabilidad evaluada.
- **Estudio de APIs:** §1.5 indica que las llamadas a Canvas deben ser secuenciales por token; §3.3 no habla de progreso ni timeouts.

### P039. ¿El ayudante ve la misma navegación que el profesor con acciones ocultas/deshabilitadas según permiso, o una interfaz distinta centrada en 'mis correcciones'? ¿Los controles sin permiso se ocultan por completo o se muestran deshabilitados con tooltip 'requiere permiso X, pídelo al profesor'? ¿Qué pestañas de tarea/curso puede ver un ayudante con el rol mínimo?

- **Requisitos:** R2.1.8, R2.7.2
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la matriz vista × rol del spec y el patrón de UI para permisos, necesario para que los tres permisos mínimos sean verificables en la revisión.
- **Estudio de APIs:** §3.4 propone 7 permisos y 3 roles (Profesor / Ayudante jefe / Ayudante), sin definir la UI por rol.

### P040. ¿Cómo se presenta al profesor la administración de permisos de ayudantes: roles predefinidos (p.ej., 'Ayudante jefe' / 'Ayudante') seleccionables, checkboxes por permiso individual, o roles con posibilidad de ajustar permisos? ¿Cada permiso tiene una descripción de una línea en la UI? ¿El ayudante puede ver sus propios permisos? ¿Se puede cambiar el rol de un ayudante y qué pasa con sus asignaciones en curso?

- **Requisitos:** R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.1.8 exige definir mínimo 3 permisos administrables; la respuesta define la pantalla 'Equipo docente' y su vocabulario.
- **Opciones planteadas:**
  - Roles fijos
  - Permisos granulares por checkbox
  - Roles + ajuste fino
- **Estudio de APIs:** §3.4 propone la tabla de permisos y roles como 'propuesta… defendible en la validación del 7-oct'.

### P041. ¿Cómo se incorpora a otro profesor o ayudante: ingresando su correo gmail (debe registrarse antes con Google), generando un enlace de invitación con vigencia, o eligiendo entre usuarios ya registrados? ¿Qué ve el invitado al entrar ('Has sido invitado como ayudante al curso X — Aceptar')? ¿Qué pasa si aún no tiene cuenta, si el correo no es gmail.com, o si la invitación expira? ¿Se muestran invitaciones pendientes en 'Equipo docente'?

- **Requisitos:** R2.1.7, R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el flujo completo de invitación con sus estados (pendiente / aceptada / expirada) y sus pantallas, hoy no especificado.
- **Estudio de APIs:** no lo aborda (§3.4 solo dice que profesores y ayudantes 'viven en la BD de ustedes').

### P042. Si el token de Canvas del profesor que vinculó el curso deja de funcionar (revocado, refresh fallido, profesor eliminado del curso en Canvas), ¿qué ve cada rol? ¿Banner global 'Reconecta Canvas' para el profesor con un clic de reautorización, y para los ayudantes un aviso 'pide al profesor X que reconecte'? ¿Qué acciones se bloquean mientras tanto (publicar notas, enviar mensajes) y cuáles siguen (ver datos ya sincronizados)? ¿Puede otro profesor del curso (R2.1.7) reconectar con su propio token?

- **Requisitos:** R2.1.4, R2.1.6, R2.7.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define un estado de degradación del curso con su UI por rol y la regla de qué token se usa cuando hay varios profesores.
- **Estudio de APIs:** §1.1 explica expiración/refresh; §3.4 propone opción A (token del profesor para todas las escrituras) con B como fallback; no define la UI del estado degradado.

### P043. Al retirar a un ayudante con correcciones asignadas pendientes, ¿la UI obliga a elegir un nuevo corrector antes de confirmar, las deja 'sin asignar' con aviso en la tarea, o las reparte automáticamente? ¿Se muestra el resumen del impacto ('tiene 12 entregas pendientes en 2 tareas')? ¿Se notifica al ayudante retirado y pierde acceso inmediato? ¿Se conserva su historial de correcciones ya realizadas con su nombre?

- **Requisitos:** R2.1.9, R2.7.1
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el flujo de confirmación de R2.1.9 y la regla de negocio sobre asignaciones huérfanas.
- **Estudio de APIs:** §3.4: 'además de borrar el rol… reasignen las entregas que tenía pendientes y revoquen su acceso a la org de GitHub'. No define el flujo de UI.

### P044. ¿La URL de instalación de la GitHub App permite preseleccionar la organización destino (parámetro target_id o similar) para que el profesor no tenga que elegir entre sus cuentas/orgs, y qué parámetros devuelve GitHub en el setup_url en cada resultado (install / update / request)?

- **Requisitos:** R2.1.5
- **Área declarada:** 2.1
- **Tipo:** Investigable en docs · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Si se puede preseleccionar la org, el paso GitHub del wizard se simplifica y desaparecen varios mensajes de error del caso 'instaló en el lugar equivocado'.
- **Estudio de APIs:** §3.3 describe la redirección a /installations/new y el retorno con installation_id y setup_action=install; no menciona preselección.

### P045. ¿Quién crea las cuentas de profesor y cómo se relacionan R2.1.1 y R2.1.2? ¿Son el mismo flujo (toda persona que inicia sesión con su gmail queda creada automáticamente como profesor) o dos flujos distintos (alguien 'crea' al profesor primero y el usuario después 'asocia' su gmail)?

- **Requisitos:** R2.1.1, R2.1.2
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define si existe un rol administrador, si hay pantallas de alta/aprobación/whitelist, y si cualquier persona con gmail puede crear cursos en la instancia desplegada (que estará pública dos semanas tras la entrega final).
- **Opciones planteadas:**
  - Autoservicio: registrarse con Google = ser profesor
  - Administrador de plataforma pre-crea o aprueba cuentas
  - Whitelist de correos/dominios en configuración
  - Invitación por email desde un profesor existente
  - Código de invitación del curso ICC4201
- **Estudio de APIs:** §3.1 solo cubre el mecanismo de login (Google OIDC); §11 marca 2.1.1 como 'App/BD ✅' sin decir quién crea a quién — no lo aborda.

### P046. ¿Existe un rol 'administrador de plataforma' distinto de 'profesor'? Si sí: ¿qué puede hacer (listar/desactivar profesores, ver todos los cursos, forzar desvinculaciones) y cómo se crea el primero (seed en el despliegue, primer usuario registrado, lista de correos en variable de entorno)?

- **Requisitos:** R2.1.1
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el modelo de roles global vs por curso, el proceso de bootstrap para la demo y quién puede intervenir cuando un curso queda huérfano.
- **Opciones planteadas:**
  - No hay admin: solo profesores
  - Admin creado por seed/variable de entorno
  - El primer registro se convierte en admin
- **Estudio de APIs:** No lo aborda; §12 solo menciona RBAC profesor / ayudante jefe / ayudante a nivel de curso.

### P047. ¿Qué operaciones abarca 'administrar' un usuario profesor: editar nombre/foto, desactivar (bloquear login), reactivar, eliminar definitivamente, ver sus cursos? Si se desactiva o elimina a un profesor que es el único profesor de un curso o cuyo token de Canvas está en uso, ¿qué pasa con ese curso (queda huérfano, se bloquea, se transfiere, se archiva)?

- **Requisitos:** R2.1.1
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define pantallas CRUD, soft vs hard delete y reglas de integridad referencial; sin regla explícita los jobs de sync/informe pueden quedar corriendo con tokens de una cuenta eliminada.
- **Estudio de APIs:** No lo aborda directamente; §1.1 advierte que sin refresh_token del profesor los jobs nocturnos (2.6.1, 2.4.5) dejan de funcionar.

### P048. ¿Un mismo usuario (misma cuenta Google) puede tener roles distintos en cursos distintos (profesor en A, ayudante en B)? ¿Los ayudantes son 'usuarios' con cuenta propia mediante el mismo login Google que los profesores, o solo registros dentro de un curso sin login propio?

- **Requisitos:** R2.1.1, R2.1.7, R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el modelo Usuario ↔ Membresía(curso, rol) que debe existir desde la parcial aunque los ayudantes se implementen en la final; cambia login, menú de cursos y controles de acceso.
- **Estudio de APIs:** §3.4 dice que profesores y ayudantes 'viven en la BD de ustedes' pero no define el modelo de usuario ni la multi-membresía.

### P049. ¿Cómo se implementa 'registrarse asociando su cuenta gmail.com': (a) Google OAuth 2.0 / OpenID Connect ('Iniciar sesión con Google'), (b) formulario email+contraseña propio validando el sufijo @gmail.com con verificación por correo, (c) magic link al gmail, (d) combinación? ¿Qué datos del perfil de Google se guardan (nombre, foto, email) y qué scopes se piden (openid, email, profile)?

- **Requisitos:** R2.1.2
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el stack de autenticación, las pantallas de registro/login, si existe recuperación de contraseña (solo en b), la dependencia de Google Cloud y qué datos personales almacena la app.
- **Opciones planteadas:**
  - Google OAuth/OIDC
  - Email + contraseña con validación de sufijo
  - Magic link
  - OIDC como principal y contraseña como respaldo
- **Estudio de APIs:** §0 y §3.1 recomiendan Google OAuth/OIDC exigiendo que el claim `email` termine en @gmail.com y `email_verified === true`.

### P050. ¿Se aceptan solo direcciones @gmail.com estrictas, o también @googlemail.com y cuentas Google Workspace con dominio institucional (p. ej. correos de la universidad si están sobre Google)? ¿Qué pasa con el profesor y los ayudantes evaluadores si su correo principal es institucional y no gmail?

- **Requisitos:** R2.1.2
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija la regla de validación y su mensaje de rechazo; una regla demasiado estricta puede impedir que los evaluadores entren el 16-sep, una demasiado laxa incumple literalmente R2.1.2.
- **Opciones planteadas:**
  - Solo @gmail.com
  - @gmail.com y @googlemail.com
  - Cualquier cuenta Google
  - Lista de dominios permitidos configurable por entorno
- **Estudio de APIs:** §3.1: validar el sufijo @gmail.com; nota que para Workspace el claim `hd` daría el dominio pero para gmail puro `hd` no viene.

### P051. ¿Cuál es la clave de identidad del usuario: el `sub` de Google (estable aunque cambie el correo) o el email? ¿Cómo se normalizan los alias de Gmail (puntos ignorados: n.abuawad@gmail.com ≡ nabuawad@gmail.com; sufijos +etiqueta; mayúsculas) al registrar y al invitar co-profesores/ayudantes por correo, para evitar cuentas duplicadas o invitaciones que nunca se emparejan?

- **Requisitos:** R2.1.2, R2.1.7, R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Determina la unicidad de usuarios, la lógica de emparejamiento de invitaciones pendientes y qué ocurre si un profesor cambia su dirección de Google.
- **Opciones planteadas:**
  - Identidad = `sub` de Google, email solo informativo
  - Identidad = email normalizado
  - Ambos, con `sub` como PK y email único normalizado
- **Estudio de APIs:** No lo aborda.

### P052. ¿Qué ocurre cuando alguien intenta entrar con un correo no permitido (no gmail): se rechaza con un mensaje que explica la regla, se crea una cuenta 'pendiente', o se redirige a otra pantalla? ¿Y si Google devuelve `email_verified=false` o el usuario cancela el consentimiento de Google?

- **Requisitos:** R2.1.2
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Criterio de aceptación de la pantalla de login y de los mensajes de error; es el primer paso de la demo y se evalúa facilidad de uso.
- **Estudio de APIs:** §3.1 exige `email_verified === true` pero no define la UI de rechazo.

### P053. ¿Qué atributos propios tiene un curso en la app (nombre, código, período/semestre, descripción, zona horaria)? ¿Se completan automáticamente desde Canvas al vincular (`name`, `course_code`, término) o los escribe el profesor al crearlo? Si difieren, o si Canvas cambia el nombre después, ¿cuál prevalece y se sincroniza?

- **Requisitos:** R2.1.3, R2.1.4
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el formulario de creación de curso (paso 1 de la demo), el modelo de datos y si el sync de Canvas sobrescribe campos editados por el profesor.
- **Estudio de APIs:** §3.2 lista los campos del objeto Course (`name`, `course_code`, `sis_course_id`, `enrollment_term_id`, `start_at`, `end_at`) y sugiere guardar `canvas_course_id`, `canvas_base_url`, `course_code` y el id del profesor vinculador.

### P054. ¿Puede existir un curso sin vinculaciones (estado 'borrador') y qué funcionalidades quedan bloqueadas hasta que Canvas y GitHub estén vinculados y verificados (crear tareas, incorporar ayudantes, sincronizar estudiantes)? ¿Cuál es la máquina de estados de vinculación del curso (sin vincular / solo Canvas / solo GitHub / ambos verificados / vinculación con error)?

- **Requisitos:** R2.1.3, R2.1.4, R2.1.5, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define qué botones aparecen habilitados en cada estado, el banner de estado del curso y los criterios de aceptación del wizard.
- **Estudio de APIs:** §3.3 propone un checklist de verificación pero no define estados del curso ni bloqueos.

### P055. Ciclo de vida del curso: ¿existen archivar/cerrar, reabrir y eliminar? Al archivar o eliminar, ¿se detienen los jobs (sync de Canvas, aprovisionamiento, snapshots, informe diario)? ¿Se conservan o eliminan los repos en GitHub? ¿Soft delete o hard delete de los datos? ¿Quién puede hacerlo y qué confirmación se exige? ¿Cómo se define 'curso activo' para los workers e informes: por fechas del término de Canvas, por estado manual en la app o por tener tareas con entregas vigentes?

- **Requisitos:** R2.1.3
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin esta regla los workers procesan cursos muertos (gastando rate limit) o dejan de procesar cursos que deberían; también define si se puede recuperar un curso borrado por error.
- **Opciones planteadas:**
  - Estado manual (activo/archivado) fijado por el profesor
  - Derivado de `start_at/end_at` del término de Canvas
  - Derivado de tener tareas con entregas no cerradas
  - Combinación con prioridad definida
- **Estudio de APIs:** §4.4 regla 'nunca borren filas al sincronizar'; §9.1 define el informe por 'tareas activas'; §12 dice 'por curso activo' sin definirlo.

### P056. ¿Se requiere duplicar/clonar un curso para un nuevo semestre copiando tareas, permisos de ayudantes y configuración de notificaciones? Si sí, ¿qué se copia y qué no (vinculaciones Canvas/GitHub, repos, mapeos de estudiantes)?

- **Requisitos:** R2.1.3
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es una operación de 'administrar cursos' que, si se incluye, define un flujo completo y reglas de qué datos son reutilizables entre semestres.
- **Opciones planteadas:**
  - No se duplica
  - Duplicar solo configuración (sin vinculaciones)
  - Duplicar con nuevo wizard de vinculación obligatorio
- **Estudio de APIs:** No lo aborda.

### P057. Unicidad de vinculaciones: ¿un mismo curso de Canvas puede vincularse a más de un curso de la app (p. ej. dos profesores crean cursos distintos apuntando al mismo Canvas)? ¿Una misma organización de GitHub puede servir a varios cursos de la app (org departamental compartida entre semestres o asignaturas)? Si sí, ¿cómo se evita la colisión de nombres de repos y cómo se sabe a qué curso pertenece cada repo preexistente en la org?

- **Requisitos:** R2.1.3, R2.1.4, R2.1.5
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define restricciones de unicidad en la BD, el mensaje 'este curso de Canvas ya está vinculado por X' y la plantilla de nombres de repos.
- **Opciones planteadas:**
  - 1 Canvas ↔ 1 curso app, 1 org ↔ 1 curso app
  - 1 Canvas ↔ 1 curso app, org compartible con prefijo por curso
  - Sin restricción, solo advertencia
- **Estudio de APIs:** §5.4 propone nombres `{curso}-{periodo}-{tarea}-...` que presuponen unicidad por curso+período, pero no fija si la org debe ser exclusiva de un curso.

### P058. ¿Qué ve cada usuario en su lista de cursos (solo los cursos donde tiene membresía; el admin ve todos)? ¿Cómo se ordena y filtra (activos vs archivados, por período)? ¿Qué muestra el estado vacío para un profesor recién registrado sin cursos (llamado a la acción 'crear primer curso' con explicación de los pasos siguientes)?

- **Requisitos:** R2.1.3
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es la primera pantalla tras el login en la demo y se evalúa la guía al usuario; define la vista principal y la navegación.
- **Estudio de APIs:** No lo aborda.

### P059. ¿Qué instancia(s) de Canvas soporta la app: (a) una única URL base fijada por configuración del despliegue (p. ej. la instancia institucional o canvas.instructure.com Free-for-Teacher), (b) el profesor escribe la URL de su instancia al vincular (lo que exige una Developer Key distinta por instancia), (c) una lista de instancias preconfiguradas?

- **Requisitos:** R2.1.4
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Cada instancia requiere su propio client_id/secret y redirect_uri registrada; cambia el formulario de vinculación, el modelo (`canvas_base_url` por curso o global) y la complejidad del OAuth.
- **Opciones planteadas:**
  - Instancia única por configuración
  - Instancia por curso ingresada por el profesor
  - Lista cerrada de instancias con sus Developer Keys
- **Estudio de APIs:** §3.2 recomienda guardar `canvas_base_url` porque 'la instancia varía'; §1.2 propone Free-for-Teacher como Plan B.

### P060. ¿Se solicitó o se solicitará una Developer Key en la instancia Canvas de la universidad? ¿A quién, quién del equipo es responsable, cuál es la fecha límite para tenerla antes del 16-sep y cuál es el plan B (Free-for-Teacher con cuenta admin propia; token manual)? ¿La demo del 16-sep se hará contra el Canvas institucional o contra la instancia de prueba, y con qué cuenta de Canvas van a probar el profesor y los ayudantes evaluadores?

- **Requisitos:** R2.1.4, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Sin Developer Key no hay OAuth ni datos reales; determina qué instancia, qué cuentas y qué datos de prueba (secciones, estudiantes, grupos) deben existir el día de la demo.
- **Estudio de APIs:** §1.1: la Developer Key la crea un administrador de la instancia; §1.2 Plan B Free-for-Teacher; §13 hito 2 marcado 'Día 1' y riesgo rojo 'depende de terceros'.

### P061. ¿Qué mecanismo de autenticación con Canvas se implementa: (a) OAuth2 authorization code con Developer Key, (b) ingreso manual de un access token por el profesor, (c) ambos (OAuth principal y token manual como respaldo, visible solo en modo desarrollo/demo)? Si se incluye (b), ¿se acepta el riesgo de que los evaluadores lo consideren una violación de la política de la API de Canvas?

- **Requisitos:** R2.1.4
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el flujo de vinculación (redirección a Canvas vs campo de texto), el almacenamiento de refresh_token y un posible punto de descuento en la evaluación.
- **Opciones planteadas:**
  - Solo OAuth2
  - Solo token manual
  - OAuth2 + token manual oculto tras flag de entorno
- **Estudio de APIs:** §1.1 recomienda OAuth2; §1.2 cita la política de Canvas que prohíbe pedir tokens manuales a otros usuarios y recomienda implementar OAuth2 'igual' aunque la demo use un token pegado.

### P062. ¿De quién es el token de Canvas con el que la app opera sobre un curso: (A) el del profesor que hizo la vinculación, usado para todas las acciones del curso incluidas las de co-profesores y ayudantes; (B) cada profesor/ayudante autoriza su propio token y la app usa el del usuario que ejecuta la acción; (C) híbrido con fallback? ¿Cómo se indica en la UI en nombre de quién se ejecutan las escrituras en Canvas (notas, anuncios, mensajes)?

- **Requisitos:** R2.1.4, R2.1.7, R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Cambia el modelo de tokens (por curso vs por usuario), los requisitos de enrolamiento en Canvas de co-profesores y ayudantes, y la trazabilidad de quién publicó qué en Canvas.
- **Opciones planteadas:**
  - A: token del vinculador para todo el curso
  - B: token propio de cada usuario
  - C: A por defecto, B si el usuario autorizó el suyo
- **Estudio de APIs:** §3.4 describe A ('simple y robusto') y B ('correcto pero frágil') y recomienda A por defecto con B como fallback, mostrando en UI 'las notas se publican como Profesor X'.

### P063. ¿Qué pasa si el token/refresh_token de Canvas del profesor vinculador deja de funcionar (lo revocó desde Canvas, cambió su contraseña, fue retirado del curso en la app o perdió su enrollment en Canvas)? ¿La app detecta el 401, marca la vinculación como 'rota', notifica a todos los profesores del curso, pausa los jobs dependientes y permite que otro profesor re-autorice sin perder tareas, mapeos ni repos?

- **Requisitos:** R2.1.4, R2.1.6, R2.1.7
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el estado 'vinculación degradada', su banner, la notificación y el flujo de re-autorización; sin esto un curso puede quedar silenciosamente sin sync ni informes.
- **Estudio de APIs:** §1.1 subraya que sin refresh_token válido fallan los jobs nocturnos (2.6.1, 2.4.5); no define el flujo de detección ni recuperación.

### P064. ¿Qué cursos de Canvas se listan en el selector de vinculación: solo aquellos donde el usuario autenticado tiene enrollment `teacher` activo, o también `ta`/`designer`, cursos no publicados o concluidos? ¿Qué datos se muestran para desambiguar cursos homónimos (término, código, N estudiantes, estado)?

- **Requisitos:** R2.1.4
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define los parámetros de la llamada a Canvas y el diseño del selector, paso central de la demo.
- **Opciones planteadas:**
  - Solo teacher activo
  - teacher + ta
  - Todos los cursos visibles con filtro en UI
- **Estudio de APIs:** §3.2 propone `GET /courses?enrollment_type=teacher&enrollment_state=active&include[]=term&include[]=total_students`.

### P065. ¿Qué pasa si el usuario autoriza Canvas correctamente pero la lista de cursos como profesor viene vacía (o solo tiene rol TA)? ¿Se permite ingresar un ID/URL del curso manualmente, se muestra una guía para pedir el rol en Canvas, o se bloquea la vinculación?

- **Requisitos:** R2.1.4, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Estado vacío del paso de vinculación; determina si existe una ruta alternativa y su mensaje de guía.
- **Estudio de APIs:** No lo aborda.

### P066. ¿Se permite cambiar (re-vincular) el curso de Canvas o desvincularlo una vez que ya existen tareas, mapeos de estudiantes y repos creados? ¿Qué pasa con los datos derivados (estudiantes, entregas vinculadas a assignments del Canvas anterior)?

- **Requisitos:** R2.1.4
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si la vinculación es inmutable tras crear la primera tarea, y la advertencia/confirmación y limpieza asociada.
- **Opciones planteadas:**
  - Bloquear mientras existan tareas
  - Permitir con advertencia y borrado de datos derivados
  - Permitir solo re-autorizar (mismo curso, nuevo token)
- **Estudio de APIs:** No lo aborda; §3.2 solo indica guardar `canvas_course_id`.

### P067. ¿Qué comprobaciones exactas ejecuta el checklist de Canvas y cuáles son bloqueantes vs. advertencias? Ejemplos: curso responde; el usuario es teacher del curso; estudiantes > 0 (¿bloqueante al inicio del semestre con 0 inscritos?); secciones ≥ 1; tareas ≥ 0; permisos de escritura. ¿Qué evidencia se muestra al profesor (nombre del curso, término, N estudiantes, N secciones, N tareas, nombre del usuario Canvas que autorizó)?

- **Requisitos:** R2.1.4, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es literalmente R2.1.6 ('verificar que las configuraciones son correctas'); define la pantalla de verificación y sus criterios de aceptación.
- **Estudio de APIs:** §3.3 propone una tabla de 8 chequeos con ✅/❌ y botón 'reintentar', sin clasificar bloqueante/advertencia ni fijar la evidencia mostrada.

### P068. ¿Cómo se verifica que el token de Canvas tiene permisos de ESCRITURA (anuncios, conversaciones, calificaciones, comentarios en entregas) sin producir efectos visibles para los estudiantes? Opciones: crear un anuncio no publicado y borrarlo; consultar permisos del usuario en el curso; no verificar y reportar al primer fallo real.

- **Requisitos:** R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Determina si el checklist puede garantizar que 2.6 y 2.7 funcionarán, y si la verificación deja rastros en el Canvas real.
- **Opciones planteadas:**
  - Anuncio borrador (`published=false`) creado y eliminado
  - Consulta de permisos del curso (`include[]=permissions`)
  - Sin verificación previa; error contextual al usar
- **Estudio de APIs:** §3.3 lista 'Podemos publicar anuncios: permiso del token del profesor' sin indicar una llamada concreta.

### P069. ¿Qué hace la app si el curso de Canvas vinculado cambia de estado (`workflow_state` pasa a completed/deleted), si el término concluye, o si el profesor pierde su enrollment en Canvas? ¿Cómo se detecta (en el sync periódico) y qué se muestra y bloquea (banner, escrituras deshabilitadas)?

- **Requisitos:** R2.1.4, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Caso borde 'la tarea/curso de Canvas se elimina a mitad de camino'; define detección y degradación controlada en vez de errores opacos.
- **Estudio de APIs:** §3.2 lista `workflow_state` entre los campos relevantes pero no define reacción.

### P070. ¿La Developer Key tendrá 'enforce scopes' activado y, si sí, cuál es la lista exacta de scopes (lecturas y escrituras necesarias para 2.2–2.7) que se piden de una sola vez al vincular? ¿Qué se muestra si el usuario rechaza el consentimiento (`error=access_denied`) o si más adelante falta un scope?

- **Requisitos:** R2.1.4
- **Área declarada:** 2.1
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Los scopes deben fijarse en la key y en la URL de autorización; agregar uno después obliga a re-autorizar a todos los profesores.
- **Estudio de APIs:** §1.1 y §1.3 dan el formato `url:GET|/api/v1/...` y una lista de ejemplo de 14 scopes.

### P071. ¿El token de Canvas pertenece al usuario de la app (uno por profesor, reutilizado en todos sus cursos) o a la vinculación (uno por curso)? Si el mismo profesor vincula dos cursos, ¿hace OAuth dos veces? ¿Se usa `replace_tokens=1`, que invalidaría los tokens previos del mismo usuario y rompería la otra vinculación?

- **Requisitos:** R2.1.4
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define la tabla de credenciales (por usuario vs por curso), el comportamiento al vincular el segundo curso y la revocación.
- **Estudio de APIs:** §1.1 advierte que `replace_tokens=1` invalida tokens previos del mismo usuario y que el refresh_token no rota.

### P072. Casos borde del callback OAuth de Canvas: el usuario recarga la página de callback (el `code` es de un solo uso), el `state` no coincide, dos pestañas vinculan el mismo curso a la vez, o el usuario autoriza con una cuenta de Canvas distinta a la esperada (¿se guarda y muestra `user.id`/`name` de Canvas y se valida que sea profesor del curso elegido?). ¿Qué mensaje y estado resultan en cada caso?

- **Requisitos:** R2.1.4, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Evita vinculaciones a medias o con la identidad equivocada; define mensajes de error y la idempotencia del paso de vinculación.
- **Estudio de APIs:** §1.1: `code` de un solo uso, `state` obligatorio contra CSRF, la respuesta del token trae `user.id` y `user.name`; §3.2 sugiere guardar el id del profesor vinculador.

### P073. ¿Qué mecanismo se usa para GitHub: (a) GitHub App instalada en la organización, (b) OAuth App actuando como el profesor, (c) PAT del profesor ingresado manualmente? Si GitHub App, ¿el equipo acepta la complejidad de JWT + installation tokens para tenerla lista el 16-sep?

- **Requisitos:** R2.1.5
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el flujo de vinculación (instalar App vs pegar token), el rate limit disponible, la recepción de webhooks y la dependencia de una cuenta personal.
- **Opciones planteadas:**
  - GitHub App
  - OAuth App
  - PAT del profesor
  - GitHub App con PAT como respaldo de desarrollo
- **Estudio de APIs:** §2.1 recomienda GitHub App por rate limit escalable, token acotado a la org, webhooks incluidos y no depender del PAT de una persona.

### P074. ¿La GitHub App será pública (instalable por cualquier organización, necesario para que un profesor la instale en su propia org) o privada (solo instalable en la cuenta que la creó)? ¿Se comparte por URL de instalación o se publica en el Marketplace?

- **Requisitos:** R2.1.5
- **Área declarada:** 2.1
- **Tipo:** Investigable en docs · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Una App privada solo se puede instalar en la cuenta propietaria, lo que impediría al profesor vincular una org que no sea la del equipo; determina la visibilidad de la App y el texto de guía.
- **Estudio de APIs:** §3.3 asume la URL `github.com/apps/<tu-app>/installations/new` sin discutir la visibilidad pública/privada de la App.

### P075. ¿Se exige que el profesor sea owner de la organización para instalar la App? Si es solo miembro, GitHub deja una 'solicitud de instalación' pendiente de aprobación por un owner: ¿la app detecta ese estado y qué muestra? ¿Y si el profesor instala la App en su cuenta personal en lugar de una organización (se acepta o se rechaza)?

- **Requisitos:** R2.1.5, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define los estados intermedios del paso GitHub del wizard y el mensaje de guía; el enunciado exige explícitamente una organización.
- **Estudio de APIs:** §3.3 describe solo el camino feliz (redirect a `setup_url` con `installation_id`); no cubre solicitudes pendientes ni instalación en cuentas personales.

### P076. ¿Se exige instalación con `repository_selection = all` o se acepta 'solo repositorios seleccionados'? Con selección parcial, ¿los repos que la app cree quedan automáticamente dentro de la instalación o la App pierde acceso a ellos? ¿Se verifica en el checklist y qué mensaje se muestra si no cumple?

- **Requisitos:** R2.1.5, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Si la instalación es parcial, los repos creados podrían ser inaccesibles para webhooks y sync; define un chequeo bloqueante del wizard.
- **Estudio de APIs:** No lo aborda.

### P077. ¿La vinculación con GitHub se identifica por `installation_id`, por el id numérico de la org o por su `login`? ¿Qué pasa si la organización se renombra, o si la App se desinstala y reinstala (nuevo `installation_id`)?

- **Requisitos:** R2.1.5
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define la clave estable de la vinculación y si la app se auto-repara tras una reinstalación o exige volver a vincular.
- **Estudio de APIs:** §3.3 guarda `installation_id` y lo confirma con `GET /orgs/{org}/installation`.

### P078. ¿Cómo detecta la app que la instalación fue eliminada o suspendida desde GitHub (webhook `installation` con acción `deleted`/`suspend`, o fallo al pedir un installation token) y qué estado muestra (vinculación rota, jobs pausados, botón 'reinstalar')? ¿Se notifica a los profesores del curso?

- **Requisitos:** R2.1.5, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Caso 'el profesor desinstala la App a mitad del semestre'; sin detección, el aprovisionamiento y el sync fallan en silencio.
- **Estudio de APIs:** §8.1 lista los eventos `push`, `create`, `delete`, `repository`, `member`, `member_invite` pero no el evento `installation`.

### P079. ¿Se puede cambiar la organización de GitHub de un curso (re-vincular) después de que existen repos creados, o desvincularla sin reemplazo? ¿Qué pasa con los repos ya creados en la org anterior?

- **Requisitos:** R2.1.5
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si la org es inmutable tras el primer repo y el flujo de advertencia/migración.
- **Opciones planteadas:**
  - Bloquear si hay repos
  - Permitir y dejar repos anteriores como 'huérfanos' con advertencia
  - Permitir con transferencia de repos a la nueva org
- **Estudio de APIs:** No lo aborda.

### P080. En el checklist de GitHub, ¿se crea y elimina un repositorio temporal de prueba (efecto visible en la org y en su audit log; requiere permiso de borrado) o solo se inspeccionan los permisos concedidos a la instalación? Si se crea: ¿qué nombre y visibilidad tiene, y qué pasa si la creación funciona pero el borrado falla (queda un repo basura)?

- **Requisitos:** R2.1.5, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el chequeo más fiable del wizard pero también un efecto secundario sobre la org real del profesor.
- **Opciones planteadas:**
  - Repo temporal creado y borrado
  - Solo lectura de permisos de la instalación
  - Repo permanente de verificación (p. ej. `.curso-config`) reutilizado
- **Estudio de APIs:** §3.3 propone crear un repo `--verificacion-temporal` (201) y luego `DELETE /repos/{org}/{repo}`; §2.3 y Apéndice A.1 piden verificar empíricamente los permisos de creación.

### P081. ¿Cuál es la lista exacta de permisos que solicitará la GitHub App (Repository: Administration write, Contents write, Metadata read; Organization: Members write, Administration write) y qué pasa si más adelante se necesita un permiso adicional (el owner de la org debe aceptar la actualización): ¿la app detecta la aceptación pendiente y guía al profesor?

- **Requisitos:** R2.1.5
- **Área declarada:** 2.1
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Los permisos se piden al instalar; un permiso faltante bloquea aprovisionamiento o invitaciones a mitad de camino y exige un flujo de re-aceptación.
- **Estudio de APIs:** §2.3 tabla de permisos y advertencia de verificar `POST /orgs/{org}/repos`; Apéndice A.1 y A.2 (permisos exactos para crear repos en org y para `/generate`).

### P082. ¿El checklist verifica condiciones de la organización que afectan al flujo posterior: plan (Free vs Team) y límites de colaboradores en repos privados, requisito de 2FA para miembros (impide agregar estudiantes sin 2FA), política `members_can_create_repositories`, repos preexistentes con nombres que colisionan con la plantilla? ¿Cuáles son bloqueantes y cuáles advertencias?

- **Requisitos:** R2.1.5, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Evita que la vinculación se dé por correcta y luego falle la creación de repos o la incorporación de estudiantes por políticas de la org.
- **Estudio de APIs:** §14 'Repos privados vs públicos: si la org es Free, revisen el límite de colaboradores'; no menciona 2FA ni políticas de creación.

### P083. ¿Cómo se asocia el `installation_id` que vuelve al `setup_url` con el curso que se estaba vinculando (parámetro `state`, sesión del usuario)? ¿Qué pasa si alguien instala la App directamente desde GitHub sin pasar por la app (instalación sin curso asociado), o si un usuario vincula dos cursos a la misma org?

- **Requisitos:** R2.1.5, R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define la correlación segura entre callback e intención del usuario y evita vincular la org al curso equivocado.
- **Estudio de APIs:** §3.3 describe el redirect con `installation_id` y `setup_action=install` sin tratar la correlación con el curso ni instalaciones huérfanas.

### P084. ¿El proceso de vinculación es un wizard lineal con pasos obligatorios (Canvas → GitHub → verificación) o dos módulos independientes que se completan en cualquier orden y se pueden retomar más tarde? ¿Qué indicador de progreso se muestra y desde dónde se reingresa (página del curso, banner 'configuración incompleta')?

- **Requisitos:** R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** La parcial evalúa explícitamente 'la guía adecuada para realizar todo el proceso'; define la estructura de navegación del flujo de configuración.
- **Estudio de APIs:** §13 hito 5 'Wizard de vinculación con checklist de verificación' sin detallar linealidad ni reanudación.

### P085. ¿La verificación se ejecuta solo bajo demanda (botón 'verificar / reintentar') o también periódicamente como health-check, mostrando 'última verificación hace X'? ¿Un fallo detectado periódicamente cambia el estado del curso y genera notificación al equipo docente?

- **Requisitos:** R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define si la pantalla de verificación es puntual o un estado vivo del curso, y su impacto en jobs y notificaciones.
- **Estudio de APIs:** §3.3 botón 'reintentar'; §4.4 recomienda mostrar `last_synced_at` ('datos de Canvas actualizados hace 4 min').

### P086. ¿Qué mensajes accionables se muestran para cada error típico de vinculación (Canvas: 401 token inválido, 403 sin permisos o rate limit, 404 curso no encontrado; GitHub: 403 permiso faltante, 404 App no instalada, instalación suspendida)? ¿Cada error incluye el enlace directo a la acción correctiva (re-autorizar Canvas, reinstalar App, pedir rol al admin)?

- **Requisitos:** R2.1.6
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Convierte códigos HTTP en guía para el profesor, que es lo evaluado en R2.1.6; define una tabla error → mensaje → acción.
- **Estudio de APIs:** §1.5 (403/429 en Canvas) y §2.4 (403/429 en GitHub) definen códigos y reintentos, no textos de UI.

### P087. ¿Cómo se incorpora a un co-profesor: (a) ingresando su gmail, quedando como invitación pendiente hasta que inicie sesión; (b) seleccionando un usuario ya registrado; (c) link de invitación con token; (d) importando los `TeacherEnrollment` del curso de Canvas? ¿La invitación expira, se puede cancelar, y qué ve el invitado al entrar por primera vez?

- **Requisitos:** R2.1.7
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el flujo de invitación, el estado 'pendiente' en la lista de equipo docente y el emparejamiento con la cuenta Google.
- **Opciones planteadas:**
  - Invitación por gmail (pendiente)
  - Selección de usuario registrado
  - Link de invitación firmado
  - Importar TeacherEnrollment desde Canvas
- **Estudio de APIs:** §3.4 'esto vive en la BD de ustedes' sin definir el flujo de incorporación.

### P088. ¿Se exige que el co-profesor tenga enrollment de profesor en el curso de Canvas y/o que autorice su propio token de Canvas? Si no lo tiene, ¿se le permite operar igual usando el token del profesor vinculador, y se le advierte?

- **Requisitos:** R2.1.7
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina si 'mismos permisos' es realizable para alguien que no existe en Canvas y qué se verifica al aceptarlo.
- **Estudio de APIs:** §3.4 opciones A (token del profesor para todo) y B (cada uno su token; requiere enrollment en Canvas).

### P089. Reglas entre profesores con 'mismos permisos': ¿un profesor puede quitar a otro profesor? ¿Puede salir él mismo del curso? ¿Se prohíbe dejar un curso sin profesores (regla del último profesor)? ¿Qué pasa si se quita al profesor cuyo token de Canvas está en uso? ¿Se permite cambiar el rol de una persona (ayudante → profesor o profesor → ayudante) y qué pasa con sus correcciones asignadas y suscripciones al cambiar?

- **Requisitos:** R2.1.7, R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija las reglas de negocio de integridad del equipo docente y evita cursos huérfanos o pérdida de credenciales.
- **Estudio de APIs:** No lo aborda.

### P090. ¿Cuál es la lista definitiva de permisos de ayudante (mínimo 3)? ¿Se adopta la propuesta del estudio (gestionar curso, gestionar tareas/repo base, disparar aprovisionamiento, asignar correctores, publicar notas, comunicar con estudiantes, suscribirse al informe), se recorta, o se agregan otros (ver dashboard, editar mapeo Canvas↔GitHub de estudiantes, ver informes históricos)? ¿Cómo se nombran y describen en la UI?

- **Requisitos:** R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es un requisito explícito con umbral mínimo y será defendido en la actividad de validación del 7-oct; define la matriz de autorización del backend y el formulario de permisos.
- **Estudio de APIs:** §3.4 propone 7 permisos (`course.manage`, `assignment.manage`, `repo.provision`, `grading.assign`, `grading.submit`, `student.communicate`, `report.subscribe`) con matriz profesor / ayudante jefe / ayudante.

### P091. ¿Modelo de autorización: (a) roles predefinidos (Ayudante, Ayudante jefe) con permisos fijos; (b) permisos individuales activables por ayudante (checkboxes); (c) rol base más ajustes? ¿Existe jerarquía (un ayudante jefe puede administrar permisos de otros ayudantes) o solo el profesor administra? ¿Los cambios de permisos surten efecto inmediato en sesiones activas o al siguiente login, y la UI oculta o deshabilita (con explicación) las acciones no permitidas?

- **Requisitos:** R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la implementación del RBAC, la pantalla de administración de permisos y el comportamiento visible cuando un permiso falta (relevante porque 'lo no accesible no se considera cumplido').
- **Opciones planteadas:**
  - Roles fijos
  - Permisos granulares por ayudante
  - Rol base + ajustes
- **Estudio de APIs:** §3.4 propone roles 'Ayudante jefe' y 'Ayudante'; no trata jerarquía de administración ni efecto en sesiones.

### P092. ¿Los permisos se otorgan a nivel de curso (aplican a todas las tareas) o pueden acotarse por tarea o por sección (p. ej. un ayudante solo corrige la sección 2)? ¿Un ayudante ve el dashboard y los datos de todos los estudiantes del curso o solo de los que tiene asignados?

- **Requisitos:** R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el alcance de cada permiso, los filtros de datos por usuario y consideraciones de privacidad de estudiantes.
- **Estudio de APIs:** §3.4 marca `grading.submit` para ayudante como '(solo asignadas)', insinuando alcance por asignación; no fija alcance por sección ni visibilidad del dashboard.

### P093. ¿Los ayudantes necesitan acceso en GitHub para revisar el código de repos privados? Si sí: ¿se les pide su usuario de GitHub al incorporarlos y la app los agrega automáticamente como miembros de la org o como colaboradores (`pull`/`triage`) de cada repo de la tarea? ¿Qué pasa si el usuario es inválido, no acepta la invitación, o se incorpora al ayudante cuando ya existen repos?

- **Requisitos:** R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin acceso a GitHub el ayudante no puede abrir el código que debe corregir (R2.7.4); define un flujo de aprovisionamiento de accesos para el equipo docente además del de estudiantes.
- **Opciones planteadas:**
  - Miembro de la org con permiso base de lectura
  - Colaborador `pull`/`triage` por repo
  - Acceso solo mediante la app (sin GitHub directo)
- **Estudio de APIs:** §3.4 menciona revocar acceso a la org 'si se lo dieron' (`DELETE /orgs/{org}/memberships/{username}`) pero no define cómo ni cuándo se otorga.

### P094. ¿Cómo se incorpora un ayudante: por gmail (invitación), importando los `TaEnrollment` del curso de Canvas, o ambos? Si se importa desde Canvas y el correo del TA no es gmail, ¿cómo se empareja con su cuenta Google? ¿Debe existir como TA en Canvas para poder publicar notas (R2.7.6) o se usa el token del profesor?

- **Requisitos:** R2.1.8
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el formulario de alta de ayudantes y los prerequisitos externos (Canvas) que la app debe verificar o explicar.
- **Estudio de APIs:** §3.4 'Nota de coherencia': que un ayudante exista en la app no implica que exista en Canvas; para publicar notas necesita token con permiso o se usa el del profesor (opción A).

### P095. Al retirar a un ayudante, ¿qué pasa con sus correcciones pendientes (reasignación automática equitativa, quedan 'sin asignar' con alerta al profesor, o el profesor debe reasignarlas antes de confirmar el retiro)? ¿Se conserva la autoría de las correcciones ya realizadas y las notas ya publicadas? ¿Se cancela su suscripción al informe diario?

- **Requisitos:** R2.1.9
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el flujo de confirmación del retiro y las reglas de integridad con 2.7 y 2.6.
- **Opciones planteadas:**
  - Reasignación automática
  - Quedan sin asignar con alerta
  - Bloquear retiro hasta reasignar manualmente
- **Estudio de APIs:** §3.4 'reasignen las entregas que tenía pendientes' sin fijar mecanismo.

### P096. Al retirar a un ayudante, ¿se revoca automáticamente su acceso en GitHub (colaborador de repos y/o miembro de la org)? ¿Qué pasa si el ayudante también es miembro de la org por otras razones (otro curso en la misma org) o si la revocación falla por rate limit o permisos?

- **Requisitos:** R2.1.9
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define los efectos secundarios externos del retiro y su manejo de errores.
- **Estudio de APIs:** §3.4 propone `DELETE /orgs/{org}/memberships/{username}` si se le dio acceso a la org.

### P097. ¿El retiro de un ayudante es soft delete (se conserva historial y auditoría de quién asignó y quién corrigió) o hard delete? ¿Se invalidan de inmediato sus sesiones activas? ¿Se le notifica? ¿Puede reincorporarse el mismo ayudante recuperando su historial? ¿El retiro es por curso (sigue siendo ayudante en otros cursos)?

- **Requisitos:** R2.1.9
- **Área declarada:** 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el modelo de membresía (con `removed_at`), la invalidación de sesión y la trazabilidad exigible en la validación oral.
- **Estudio de APIs:** §4.4 regla 'nunca borren filas, marquen `deleted_at`' se plantea para datos de Canvas, no explícitamente para el equipo docente.

### P098. Si la app admite más de una instancia de Canvas (canvas_base_url), ¿todo identificador de Canvas (user_id, course_id, section_id, group_id, assignment_id, enrollment_id) se almacena con clave compuesta (canvas_instance_id, canvas_id) y las claves únicas del mapeo estudiante↔GitHub se definen por instancia? Si se fija una única instancia para el proyecto, ¿se deja igualmente la columna canvas_instance_id desde la primera migración para no tener que rehacer claves después?

- **Requisitos:** R2.1.4, R2.2.1, R2.2.4
- **Área declarada:** 2.1 / 2.2 (modelo de datos)
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Los IDs numéricos de Canvas colisionan entre instancias; cambiar las claves primarias después de la parcial es una migración destructiva sobre datos de demo.
- **Opciones planteadas:**
  - Clave compuesta por instancia
  - ID de Canvas simple con instancia fija
  - Columna presente pero constante
- **Estudio de APIs:** §3.2 'Guarden canvas_base_url (la instancia varía)'; no aborda el impacto en claves.

---

## 2.2

### P099. Para la tarea de Canvas 'Registro de usuario GitHub', además de los parámetros ya discutidos (puntos, omit_from_final_grade, fechas, submission_type), ¿qué se fija respecto a lo que el ESTUDIANTE y el PROFESOR ven en Canvas como efecto colateral?: (a) grading_type (not_graded evita que aparezca en la libreta y en la lista 'por calificar' del profesor, pero impide marcar 'complete'; pass_fail muestra ✓/✗ al estudiante); (b) allowed_attempts (-1 ilimitado para permitir corregir un usuario inválido, o limitado); (c) si aparece en el calendario / lista de pendientes del estudiante y con qué etiqueta cuando la entrega es tardía o falta ('missing'/'late' en su libreta); (d) si la tarea queda en su propio assignment group para no distorsionar promedios ponderados; (e) si el profesor recibirá N ítems 'necesita calificación' en su To-Do de Canvas por cada registro, y quién los limpia; (f) si al vincular una tarea de registro ya existente se valida que sea individual (group_category_id nulo) y de texto.

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define la configuración exacta del POST/PUT de la tarea de registro y el comportamiento observable por estudiantes y profesor en Canvas; evita que la libreta o el To-Do del profesor se contaminen y que estudiantes queden marcados 'missing' por una tarea administrativa.
- **Opciones planteadas:**
  - grading_type=not_graded sin marcar complete
  - pass_fail con 'complete' al validar
  - points con 0 puntos y omit_from_final_grade
  - allowed_attempts ilimitado
  - allowed_attempts limitado a N
- **Estudio de APIs:** §6.1 propone crear la tarea con submission_types=online_text_entry, points_possible=0 y published=true; no aborda grading_type, allowed_attempts, assignment group, ni el efecto en la lista de pendientes del profesor o en la libreta del estudiante.

### P100. Si se adopta la verificación por OAuth de GitHub vía magic link (§6.2): (a) ¿qué pasa cuando el login verificado por OAuth difiere del que el estudiante escribió en la tarea de Canvas: gana el verificado, se marca conflicto, o se pide confirmar?; (b) ¿el enlace es de un solo uso, cuánto dura, y qué ocurre si un estudiante lo reenvía a un compañero que autoriza con SU GitHub (queda mapeado al canvas_user_id equivocado)?; (c) ¿qué página ve el estudiante tras autorizar (éxito, error, 'este enlace ya fue usado') y en qué idioma?; (d) ¿se pide el scope mínimo (read:user) y se revoca/olvida el token del estudiante inmediatamente después de leer el login?; (e) ¿el estudiante que solo hizo OAuth y nunca entregó la tarea de Canvas cuenta como mapeado?

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija reglas de precedencia entre fuentes de mapeo, seguridad del enlace y las pantallas mínimas de cara al estudiante si §6.2 entra al alcance.
- **Opciones planteadas:**
  - OAuth prevalece siempre
  - Conflicto para decisión docente
  - OAuth solo como confirmación del texto entregado
- **Estudio de APIs:** §6.2 describe JWT con canvas_user_id y 7 días de vigencia, y GET /user con el token del estudiante; no aborda conflictos con el texto entregado, reuso del enlace ni la página posterior.

### P101. ¿Qué criterios de aceptación medibles se fijan para la usabilidad del enrolamiento DESDE EL LADO DEL ESTUDIANTE (el enunciado dice que se evaluará)? Por ejemplo: número máximo de acciones del estudiante hasta tener acceso al repo (leer tarea → escribir usuario → entregar → aceptar invitación); tiempo máximo entre entrega válida y mensaje de confirmación, y entre confirmación y repo accesible; máximo de iteraciones del ciclo error→corrección; que cada mensaje de error diga exactamente qué hacer; que todo funcione desde la app móvil de Canvas. ¿Se hará una prueba con al menos un estudiante real (no del equipo) siguiendo solo las instrucciones de Canvas antes del 16-sep, y quién la registra?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.12
- **Área declarada:** 2.2 / 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Convierte 'se evaluará la usabilidad del proceso' en requisitos verificables y en un plan de prueba con usuario real.
- **Estudio de APIs:** §6.1 afirma que el 'loop de feedback automático es la parte usable del requisito' y §13 propone un guion de demo; no fija criterios medibles para el estudiante.

### P102. ¿Tener cuenta de GitHub es obligatorio para aprobar el curso, y qué se hace con el estudiante que no puede o no quiere crearla (objeción de privacidad, restricciones de GitHub por país o edad, cuenta suspendida)? ¿Se acuerda con el profesor del curso una política (exento con entrega alternativa fuera de la app; cuenta creada por el docente; plazo máximo antes de considerarlo sin entrega) y la app solo ofrece el estado 'exento' con motivo?

- **Requisitos:** R2.2.4, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija una regla de negocio del curso que la app debe reflejar (estados y mensajes) y qué se comunica al estudiante en la tarea de registro.
- **Estudio de APIs:** §6.1 señala como desventaja que no se prueba la propiedad de la cuenta; no aborda estudiantes sin cuenta ni una política de obligatoriedad.

### P103. Los estudiantes escribirán su usuario en lugares distintos al cuerpo de la entrega: en el cuadro de comentarios de la entrega, respondiendo la Conversation de recordatorio, en un mensaje directo al profesor, o adjuntando una captura. ¿La app considera alguna de esas fuentes (leer submission_comments del estudiante como respaldo), o solo el body y todo lo demás lo carga el docente a mano? Si lee comentarios, ¿cuál prevalece cuando body y comentario difieren?

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define las fuentes del parser, sus scopes y la precedencia entre fuentes; reduce carga manual del docente.
- **Opciones planteadas:**
  - Solo body
  - Body + comentarios de la entrega
  - Cualquier canal, con carga manual del docente
- **Estudio de APIs:** §6.1 solo extrae el login del body de la submission (include[]=user); no aborda comentarios ni otras fuentes.

### P104. Datos sucios de identidad en Canvas: (a) si el administrador FUSIONA dos cuentas de un mismo estudiante (user merge), su canvas_user_id cambia y la app verá un estudiante 'retirado' y otro 'nuevo' sin mapeo: ¿se detecta (mismo sis_user_id/login_id) y se migra el mapeo, repo y snapshots automáticamente, o se pide confirmación docente?; (b) roles personalizados derivados de StudentEnrollment (type=StudentEnrollment con role distinto, p. ej. 'Oyente'): ¿cuentan como estudiantes con repo?; (c) verificar si en la instancia institucional aparecen ids 'shadow' de otras cuentas (formato '123~456') para estudiantes de intercambio y si funcionan como recipients y en PUT submissions.

- **Requisitos:** R2.2.1, R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija la clave de identidad efectiva (canvas_user_id vs sis_user_id) y reglas de migración de mapeos ante cambios de id, evitando repos duplicados.
- **Estudio de APIs:** §4.4 recomienda canvas_user_id como clave estable y §4.1 menciona enrollment_role_id; no aborda fusiones de usuarios, roles personalizados ni ids de cuentas cruzadas.

### P105. Para un estudiante sin usuario registrado, ¿la app usa señales de Canvas para distinguir 'no ha visto las instrucciones' de 'las vio y no actuó'?: last_login / last_activity_at del estudiante en el curso (disponibles en los endpoints de usuarios/enrollments), si abrió la tarea de registro, o si aceptó la invitación al curso. ¿Se muestra esa señal en la vista de faltantes (p. ej. 'sin actividad en Canvas hace 12 días') para que el docente lo contacte por otro medio, o se declara fuera de alcance?

- **Requisitos:** R2.2.6, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Agrega o no columnas y llamadas al sync, y permite priorizar recordatorios y contacto humano.
- **Opciones planteadas:**
  - Mostrar última actividad en Canvas
  - Solo estado del mapeo
  - Fuera de alcance
- **Estudio de APIs:** §4.1 lista sort=last_login e include[]=enrollments para GET /courses/:id/users; no propone usar actividad del estudiante como señal en la vista de faltantes.

### P106. ¿Qué mecanismos de enrolamiento se implementan para la parcial y cuáles para la final: tarea de Canvas de recolección (¿creada por la app o elegida entre las existentes?), carga manual por el docente con validación en vivo, importación CSV, verificación por OAuth de GitHub vía magic link? Si la app crea la tarea en Canvas, ¿se avisa al profesor antes de escribir en su curso?

- **Requisitos:** R2.2.4, R2.2.5, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Es lo que se evalúa como 'usabilidad del proceso de enrolamiento' y define si la app escribe tareas en el Canvas del profesor (efecto visible para revisores).
- **Opciones planteadas:**
  - Tarea Canvas + carga manual (parcial)
  - Tarea Canvas + manual + CSV
  - Todo lo anterior + OAuth GitHub (final)
- **Estudio de APIs:** §6.1 recomienda la tarea de Canvas como formulario; §6.2 OAuth opcional; §6.3 carga manual + CSV + recordatorios.

### P107. Canvas expone como group categories también las etiquetas de diferenciación (differentiation tags: `non_collaborative=true`, filtro `collaboration_state`). ¿Qué categorías cuentan como 'grupos' para la app: solo las colaborativas (`collaboration_state=collaborative`), todas, o se muestran las no colaborativas con una etiqueta distinta y sin repo? ¿Qué hace la app si un assignment vinculado trae un `group_category_id` que apunta a una categoría no colaborativa (¿se clasifica como grupal según R2.3.3?) o si un estudiante pertenece simultáneamente a una etiqueta y a un grupo real de otra categoría?

- **Requisitos:** R2.2.3, R2.3.3, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija el filtro del sync de grupos, la clasificación individual/grupal de R2.3.3 y evita crear repos grupales para etiquetas administrativas; también define qué aparece en la vista de faltantes.
- **Opciones planteadas:**
  - Sincronizar solo categorías colaborativas
  - Sincronizar todas y marcar las no colaborativas como 'etiqueta' sin repo
  - Bloquear la vinculación si el assignment apunta a una categoría no colaborativa
- **Estudio de APIs:** §4.3 lista el parámetro `collaboration_state` y el campo `non_collaborative` de GroupCategory pero no decide cómo tratarlos; §4.4 sincroniza todas las categorías del curso sin filtro.

### P108. ¿El líder de grupo definido en Canvas (campo `leader` del Group, `auto_leader` de la categoría) tiene algún rol en la app: destinatario principal o único de comunicaciones del grupo, primer integrante en tablas y timeline, permiso distinto (`maintain`) en el repo, o se ignora por completo? Si el líder cambia en Canvas o el grupo no tiene líder, ¿qué se muestra y qué se hace?

- **Requisitos:** R2.2.3, R2.6.5, R2.3.9
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si el sync debe leer y persistir el líder, si las plantillas de mensajes lo mencionan y si hay diferencia de permisos en GitHub entre integrantes.
- **Opciones planteadas:**
  - Ignorar el líder
  - Mostrarlo como dato informativo
  - Usarlo como destinatario principal de mensajes grupales
  - Darle permiso `maintain` en el repo
- **Estudio de APIs:** §4.3 menciona `auto_leader` en GroupCategory pero no lo usa en ningún flujo.

### P109. Si una sección tiene `end_at` con `restrict_enrollments_to_section_dates=true`, o termina el término del curso, Canvas concluye automáticamente las inscripciones (`enrollment_state=completed`) de forma masiva aunque la corrección siga en curso. ¿La app trata `completed` igual que una baja (`deleted`/`inactive`: quitar acceso al repo, sacar de correcciones y métricas) o como 'inscrito concluido' que sigue siendo calificable y visible? ¿Se distinguen ambos casos en la UI y el checklist advierte con antelación fechas de fin de sección/término que caigan dentro del período de corrección (6–20 de octubre en el curso demo)?

- **Requisitos:** R2.2.1, R2.4.2, R2.7.6, R2.3.9
- **Área declarada:** 2.2 / 2.4 / 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita revocar acceso y ocultar sujetos en bloque durante la corrección; fija la semántica de `completed` y un ítem preventivo del checklist.
- **Opciones planteadas:**
  - `completed` = retirado
  - `completed` = concluido calificable, sin cambios en GitHub
  - Configurable por curso
- **Estudio de APIs:** §4.2 advierte que `restrict_enrollments_to_section_dates` 'cambia qué fechas aplican'; §14 dice que los retirados pasan a deleted/inactive sin cubrir la conclusión automática por fecha.

### P110. Cuando un estudiante deja de aparecer como StudentEnrollment activo en Canvas (se retira, queda inactive o completed) y ya tiene repositorio creado (individual o como integrante de un grupo), ¿qué debe hacer la app con: (a) su acceso como colaborador al repo (mantener / revocar / degradar a solo lectura), (b) el repo individual (mantener, archivar en GitHub, marcar 'retirado'), (c) su presencia en el dashboard, en 'estudiantes sin participación', en el informe diario y en la lista de corrección, y (d) los snapshots ya capturados? ¿Y si el estudiante reaparece (reactivación del enrollment)?

- **Requisitos:** R2.2.1, R2.3.9, R2.4.7, R2.5.4, R2.6.2, R2.7.7
- **Área declarada:** 2.2 / 2.3 / 2.5 / 2.7 (transversal)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la máquina de estados del repo y del estudiante, las reglas de reconciliación del sync de Canvas, qué filas se muestran u ocultan en cada vista y si el worker debe ejecutar acciones destructivas en GitHub.
- **Opciones planteadas:**
  - Mantener acceso y repo, ocultar de métricas y corrección
  - Revocar acceso, archivar repo, mantener histórico visible con etiqueta 'retirado'
  - No hacer nada automático: alertar al profesor y ofrecer acciones manuales
- **Estudio de APIs:** §4.4 'Nunca borren filas; marcar deleted_at' y §14 'no borren su repo ni su historia; márquenlos'. No define qué pasa con el acceso al repo ni con la visibilidad en dashboard/informe/corrección.

### P111. Un estudiante se inscribe en Canvas después de que la tarea ya tiene repos creados e incluso después de que cerró la entrega 1: ¿se le crea repo automáticamente sin acción del profesor? ¿Se le captura snapshot de la entrega 1 ya vencida (con estado 'sin commits' o 'no aplicaba'), se lo excluye de esa entrega, o queda pendiente de decisión manual? ¿Se le asigna corrector automáticamente si ya se repartieron las correcciones? ¿Se dispara la notificación de 'repo disponible' aunque la tarea vaya avanzada?

- **Requisitos:** R2.2.1, R2.3.10, R2.4.5, R2.6.7, R2.7.1
- **Área declarada:** 2.2 / 2.3 / 2.4 / 2.7 (transversal)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El worker de aprovisionamiento y el de snapshots deben saber si tratan altas tardías igual que altas normales; afecta el estado de corrección (denominadores) y el informe diario.
- **Opciones planteadas:**
  - Crear repo y capturar snapshot vencido inmediatamente (estado 'sin commits')
  - Crear repo y marcar entregas vencidas como 'no aplica' para ese estudiante
  - Crear repo pero dejar las entregas vencidas en 'requiere decisión del profesor'
- **Estudio de APIs:** §5.5: el worker crea repo para todo sujeto sin repo READY (implica sí crear). §7.5: el job de snapshot barre 'todo lo vencido y no capturado' (implica captura inmediata al crear). No distingue el caso de alta tardía.

### P112. Si un estudiante cambia de sección en Canvas (o su sección se elimina o se cross-lista) después de configurada la tarea: ¿se recalcula su fecha efectiva y se reprograma el snapshot pendiente? Si el snapshot ya fue capturado con la fecha de la sección anterior, ¿se mantiene (R2.4.7), se recaptura o se marca 'requiere revisión'? ¿Se comunica el cambio al equipo docente? Si el nombre o la descripción del repo incluye la sección, ¿se actualiza?

- **Requisitos:** R2.2.2, R2.3.8, R2.4.2, R2.4.4, R2.4.7
- **Área declarada:** 2.2 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina si la fecha efectiva es un valor derivado en vivo o congelado al capturar, y si el sync de Canvas debe emitir eventos de auditoría/alerta por cambio de sección.
- **Opciones planteadas:**
  - Recalcular siempre; snapshots capturados quedan intactos y se alerta
  - Recalcular y recapturar si la nueva fecha es posterior
  - Congelar sección y fecha por entrega al momento de la primera captura
- **Estudio de APIs:** §7.3 calcula fecha efectiva por estudiante; §7.4 reprograma sólo si la entrega 'NO fue capturada aún'. No resuelve el caso ya capturado ni el cambio de sección en sí.

### P113. Cuando un estudiante tiene enrollments activos en dos o más secciones del mismo curso: ¿qué sección se muestra en las tablas y en los filtros por sección, y qué fecha efectiva rige (la más tardía como sugiere el estudio, la de una sección 'principal', o se marca conflicto para que el profesor decida)? Debe verificarse contra la instancia real qué fecha aplica Canvas en ese caso.

- **Requisitos:** R2.2.2, R2.4.2, R2.4.3
- **Área declarada:** 2.2 / 2.4
- **Tipo:** Verificar empíricamente · **Entrega:** Ambas entregas
- **Por qué importa:** Cambia el modelo de datos (1:N vs N:M estudiante-sección), el algoritmo de fecha efectiva y el filtro de sección de todas las vistas.
- **Opciones planteadas:**
  - Modelo N:M y fecha más permisiva
  - Sección principal = la del enrollment más antiguo; alertar si hay más de una
  - Bloquear la tarea para ese estudiante hasta que el profesor elija sección
- **Estudio de APIs:** §4.2 advierte que un estudiante puede estar en varias secciones (modelo N:M); §7.3 sugiere max() de fechas de sección; Apéndice A.7 pide verificarlo con un caso real.

### P114. Si la composición de un grupo cambia en Canvas después de creado el repo grupal: (a) integrante nuevo: ¿se agrega como colaborador automáticamente y se le notifica? (b) integrante que sale: ¿se le revoca el acceso de inmediato, al cierre de la entrega en curso, o nunca? ¿Sus commits siguen contando en el repo antiguo? (c) integrante que se mueve a otro grupo que ya tiene repo: ¿queda con acceso a dos repos? (d) si el cambio ocurre entre la entrega 1 y la 2, ¿cómo se refleja en la corrección de cada entrega?

- **Requisitos:** R2.2.3, R2.3.4, R2.3.9, R2.5.8, R2.7.1
- **Área declarada:** 2.2 / 2.3 / 2.5 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la reconciliación de colaboradores del worker, la atribución de commits por período y la relación entre grupo 'al cierre' y grupo 'actual' para corregir.
- **Opciones planteadas:**
  - Reconciliar colaboradores en cada sync (agregar y revocar)
  - Solo agregar nuevos; nunca revocar automáticamente
  - Congelar la membresía del grupo al crear el repo y alertar de diferencias
- **Estudio de APIs:** §4.4 hace upsert de grupos y marca retirados; §5.4 agrega colaboradores al crear. No aborda cambios de membresía posteriores ni revocación.

### P115. Si en Canvas se elimina un grupo (o el group set completo) cuyo repo ya existe, o el assignment pasa a apuntar a otro group_category_id: ¿el repo queda 'huérfano' y se archiva, se mantiene visible con etiqueta, se intenta re-asociar por integrantes coincidentes, o se bloquea la tarea hasta que el profesor decida? ¿Se crean repos nuevos para los grupos del nuevo set (dejando a un estudiante con dos repos y violando R2.3.4)?

- **Requisitos:** R2.2.3, R2.3.3, R2.3.4, R2.3.11
- **Área declarada:** 2.2 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es el escenario donde el invariante 'un conjunto de repos por tarea' puede romperse; la spec debe decir si el worker se detiene o continúa.
- **Opciones planteadas:**
  - Bloquear aprovisionamiento y marcar tarea 'inconsistente' hasta intervención
  - Archivar repos huérfanos y crear los nuevos
  - Re-asociar automáticamente si los integrantes coinciden ≥ N%
- **Estudio de APIs:** No lo aborda (§5.2 solo valida group_category_id al vincular una segunda entrega).

### P116. ¿Qué estados de enrollment de Canvas cuentan como 'estudiante inscrito' para crear repo, mostrar y notificar: solo active, o también invited (aún no aceptó la invitación al curso), inactive, completed? ¿Se excluyen siempre el Test Student y los observers? ¿Cómo se muestran los excluidos para que el profesor entienda por qué no tienen repo?

- **Requisitos:** R2.2.1, R2.2.6, R2.3.7
- **Área declarada:** 2.2 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el filtro del sync y evita crear repos fantasmas o dejar fuera a estudiantes reales; es visible en la demo parcial.
- **Estudio de APIs:** §4.1 recomienda state[]=active, type StudentEnrollment y filtrar el Test Student. No decide sobre invited/inactive/completed.

### P117. Cuando el estudiante no acepta la invitación de colaborador al repo (queda pendiente, la rechaza, o expira — GitHub expira las invitaciones a repositorio a los 7 días): ¿la app reenvía automáticamente (con qué frecuencia y cuántas veces), solo permite reenvío manual, o notifica por Canvas al estudiante? ¿Cómo distingue 'pendiente', 'expirada' y 'rechazada' en R2.3.11? ¿El repo cuenta como 'listo' en dashboard e informe mientras la invitación está pendiente?

- **Requisitos:** R2.2.6, R2.3.9, R2.3.11, R2.6.2, R2.6.7
- **Área declarada:** 2.2 / 2.3 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define los sub-estados de COLLABORATORS_PENDING, la política de reintento del outbox y el criterio de 'problema pendiente' del informe diario.
- **Opciones planteadas:**
  - Reenvío automático diario hasta N veces + aviso Canvas
  - Solo reenvío manual desde la tabla de estado
  - Invitar a la org (§6.4) para evitar invitaciones por repo
- **Estudio de APIs:** §5.4: 201 = invitación pendiente, 204 = acceso directo; GET /invitations con campo expired; acción manual 'Reenviar' en §5.6. No define política automática. La expiración a 7 días es investigable en docs de GitHub.

### P118. ¿Qué debe hacer la app cuando dos estudiantes del curso quedan mapeados al mismo login de GitHub (uno se equivocó o copió al compañero), cuando el login no existe, es una Organization, o es el login de un miembro del equipo docente? ¿Se rechaza el segundo mapeo, se bloquean ambos como 'conflicto' hasta que el docente decida, o se acepta el más reciente? ¿Se notifica al estudiante por Canvas automáticamente y con qué texto?

- **Requisitos:** R2.2.4, R2.2.5, R2.2.6, R2.3.11
- **Área declarada:** 2.2 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Un login duplicado provoca que un estudiante reciba acceso al repo de otro; la spec debe fijar la restricción de unicidad y el flujo de resolución (es parte central de la demo parcial).
- **Opciones planteadas:**
  - Unicidad estricta por curso: segundo mapeo rechazado y notificado
  - Ambos quedan en 'conflicto' y sin repo hasta resolución manual
  - Último gana, con alerta al docente
- **Estudio de APIs:** §6.1 valida existencia y type=User y propone comentario automático de corrección. No aborda duplicados ni logins del equipo docente.

### P119. Si un estudiante (vía la tarea de Canvas) o el docente cambia el login mapeado cuando el repo ya existe: ¿la app quita al colaborador anterior y agrega al nuevo automáticamente, requiere confirmación del docente, o bloquea el cambio? ¿Los commits ya atribuidos al login anterior se reatribuyen al estudiante? Si el estudiante vuelve a entregar la tarea de recolección con otro valor, ¿gana su última entrega o la corrección manual del docente?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.9, R2.5.4
- **Área declarada:** 2.2 / 2.3 / 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define precedencia entre fuentes de mapeo (estudiante vs docente vs CSV), efectos secundarios en GitHub y la re-atribución de commits.
- **Opciones planteadas:**
  - Manual del docente siempre gana y bloquea cambios del estudiante
  - Última fuente gana; se reconcilian colaboradores automáticamente
  - Cambio post-repo requiere confirmación explícita del docente
- **Estudio de APIs:** §6.1 y §6.3 describen recolección automática, carga manual y CSV pero no definen precedencia ni cambios después de creado el repo.

### P120. Si el estudiante cambia su nombre de usuario en GitHub después del mapeo: ¿la app guarda el id numérico de GitHub para seguirlo y actualiza el login mostrado, o el mapeo queda 'roto' y se marca para corrección? ¿Debe cambiar el nombre del repo si lo incluía (R2.3.8) o el nombre es inmutable?

- **Requisitos:** R2.2.4, R2.3.8, R2.3.11
- **Área declarada:** 2.2 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina la clave de identidad del mapeo (login vs id) y la inmutabilidad del nombre del repo.
- **Estudio de APIs:** §6.1 guarda el login canónico devuelto por GET /users/{u}; no menciona guardar el id numérico ni el rename.

### P121. Si el docente corrige el login de un estudiante mientras el worker está a mitad de crear su repo con el login anterior (o el sync de Canvas cambia la membresía del grupo durante la creación): ¿qué versión gana y cómo se repara automáticamente (re-evaluar colaboradores al terminar el job, lock por sujeto que bloquee la edición, o marcar el repo para revisión)?

- **Requisitos:** R2.2.4, R2.3.9, R2.3.10, R2.3.11
- **Área declarada:** 2.2 / 2.3 (concurrencia)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el alcance del lock por sujeto y si el estado READY se valida contra los datos actuales al finalizar.
- **Estudio de APIs:** §5.5 menciona 'lock por sujeto' para el worker; no cubre edición concurrente desde la UI ni cambios de sync durante el job.

### P122. ¿Cómo se normalizan y validan los logins entregados por los estudiantes (mayúsculas vs login canónico, URL con path o query, varios logins en la misma entrega, texto acompañante como 'mi usuario es X', @ inicial, espacios, caracteres unicode)? Ante ambigüedad (dos candidatos válidos), ¿se rechaza y se pide corrección, o se toma el último/primero? ¿Se conserva el texto original entregado para auditoría?

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2 (datos sucios)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el parser de mapeo y su criterio de aceptación; errores aquí producen repos asignados a la persona equivocada.
- **Estudio de APIs:** §6.1 propone una regex que toma el último token y valida contra GET /users/{u}; no cubre múltiples candidatos ni conservación del original.

### P123. Si la estrategia de enrolamiento usa una tarea de Canvas para recolectar el login: ¿esa tarea debe excluirse del selector de entregas vinculables? ¿Qué pasa si el profesor la elimina o despublica en Canvas (el mapeo progresivo se detendría en silencio)? ¿Un estudiante agregado después de su fecha de cierre puede seguir entregando (fecha nula / sin lock_at)? ¿Se crea una por curso o una por tarea?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.1
- **Área declarada:** 2.2 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** La tarea de recolección es un artefacto propio con ciclo de vida que la spec debe definir y proteger; es núcleo de la demo parcial.
- **Estudio de APIs:** §6.1 propone crear la assignment 'Registro de usuario GitHub' con points_possible=0; no aborda su ciclo de vida ni su exclusión del selector.

### P124. En una tarea grupal, si solo algunos integrantes tienen login mapeado: ¿se crea el repo y se agregan los mapeados (los demás quedan pendientes) o se espera a que todos estén mapeados? Si un integrante nunca completa el mapeo, ¿hay un plazo tras el cual el repo se crea igual? ¿Cómo se muestra en R2.2.6/R2.3.11 y cuenta como 'problema' en el informe diario?

- **Requisitos:** R2.2.6, R2.3.7, R2.3.9, R2.3.10, R2.6.2
- **Área declarada:** 2.2 / 2.3 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** 'Toda la información requerida' (R2.3.10) es ambiguo para grupos; la decisión cambia el estado PENDING_MAPPING y el momento de la notificación al grupo.
- **Opciones planteadas:**
  - Esperar a todos los integrantes
  - Crear con los mapeados y completar progresivamente
  - Crear con los mapeados solo después de un plazo configurable
- **Estudio de APIs:** §5.5: '¿tiene(n) github_login mapeado? no → PENDING_MAPPING' — ambiguo sobre si basta uno o se requieren todos.

### P125. Para estudiantes que no pertenecen a ningún grupo del group set de una tarea grupal: ¿quedan sin repo y se listan como pendientes (R2.2.6), se les crea repo individual dentro de la tarea grupal, o se notifica automáticamente al estudiante y al profesor? Si Canvas los asigna a un grupo después del cierre de una entrega, ¿se aplica la misma regla que para altas tardías?

- **Requisitos:** R2.2.3, R2.2.6, R2.3.7, R2.3.10
- **Área declarada:** 2.2 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define un estado 'sin grupo' distinto de 'sin mapeo' y su tratamiento en worker, tabla de estado e informe.
- **Estudio de APIs:** §4.3: GET /group_categories/:id/users?unassigned=true para listarlos; §6.3 los incluye en el panel de faltantes. No define acción.

### P126. Si la sincronización con Canvas falla parcialmente (se leen estudiantes pero fallan grupos; Canvas devuelve 403 por throttling a mitad de la paginación): ¿se aplica lo leído o se descarta el ciclo completo (transaccional)? ¿Cómo se evita marcar como 'retirados' a estudiantes que simplemente no vinieron por un error? ¿Cómo se muestra al profesor que los datos podrían estar incompletos ('última sincronización exitosa hace X', 'sync con errores')?

- **Requisitos:** R2.2.1, R2.2.3, R2.4.4
- **Área declarada:** 2.2 / 2.4 (recuperación)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Un sync parcial mal aplicado puede revocar accesos o disparar notificaciones erróneas; define atomicidad y semántica de last_synced_at.
- **Estudio de APIs:** §4.4 registra last_synced_at y recomienda no borrar; §1.5 backoff ante 403/429. No define atomicidad del ciclo ni sync parcial.

### P127. Con grade_group_students_individually=false, calificar a un integrante propaga la nota al grupo ACTUAL en Canvas. Si el grupo cambió entre el cierre y la corrección (un estudiante se fue a otro grupo o llegó uno nuevo), ¿la app califica según la membresía al momento del snapshot (congelada) o según la membresía actual, y cómo evita que Canvas propague la nota a la persona equivocada? Verificar empíricamente el comportamiento real de la propagación.

- **Requisitos:** R2.2.3, R2.4.5, R2.7.6
- **Área declarada:** 2.2 / 2.4 / 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina si la app debe congelar la membresía del grupo por entrega y si califica por integrante para evitar propagaciones incorrectas.
- **Estudio de APIs:** §10.4: 'lean ese campo antes de calificar' y calificar por integrante si es true; no cubre cambio de grupo entre cierre y corrección.

### P128. ¿Cómo y con qué frecuencia se sincroniza la información de estudiantes, secciones y grupos desde Canvas: solo automática (cada N minutos), solo manual (botón), o ambas? ¿Se usa la misma cadencia para inscritos, grupos y entregas de la tarea de registro, o cadencias distintas? ¿Qué debe mostrar la UI sobre la última sincronización (hora, resultado, cambios detectados) y cuántas veces puede pulsarse 'sincronizar ahora' antes de bloquearse por throttling?

- **Requisitos:** R2.2.1, R2.2.2, R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el job de sincronización, su cadencia, el criterio de aceptación de 'datos frescos' (el guion de demo exige ver un cambio en vivo) y la existencia y límites del botón manual.
- **Opciones planteadas:**
  - Solo automática cada N min
  - Solo manual
  - Automática + botón manual con límite de uso
  - Cadencias distintas por tipo de dato (inscritos 10 min, submissions de registro 2 min, grupos según tarea)
- **Estudio de APIs:** §4.4 propone sync_course con upsert por canvas_id y last_synced_at visible; §12 fija sync_canvas cada 10 min; §7.4 sugiere botón 'sincronizar ahora'; §1.5 exige concurrencia 1 por token con backoff ante 403/429.

### P129. ¿Qué estados de inscripción (enrollment_state) cuentan como 'estudiante inscrito' para listar, exigir usuario GitHub y crear repositorio: solo active, o también invited (aún no aceptó la invitación al curso), inactive, completed, creation_pending? ¿Cómo se muestra en la UI un estudiante con estado distinto de active?

- **Requisitos:** R2.2.1, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Decide a quién se le exige mapeo, a quién se le crea repo y quién aparece como 'faltante'; un 'invited' sin repo puede parecer un bug en la demo o generar un repo innecesario si luego rechaza la invitación.
- **Opciones planteadas:**
  - Solo active
  - active + invited mostrados como 'invitado, sin repo'
  - active + inactive marcados sin acciones
  - Incluir completed para cursos concluidos
- **Estudio de APIs:** §4.1 recomienda enrollment_state[]=active / state[]=active y enumera los demás estados (invited, rejected, completed, inactive, creation_pending) sin decidir su tratamiento.

### P130. ¿Se excluye siempre al 'Test Student' (Student View) de listados, conteos, faltantes y creación de repos? Confirmar empíricamente en la instancia Canvas que usarán cómo aparece en GET /courses/:id/enrollments (¿type StudentViewEnrollment?) y en GET /courses/:id/users (enrollment_type student_view), para fijar el filtro exacto en ambos endpoints.

- **Requisitos:** R2.2.1, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Sin el filtro correcto el worker intenta crear un repo a un estudiante fantasma y el panel de faltantes muestra un pendiente imposible de resolver.
- **Estudio de APIs:** §4.1 y §14 ordenan filtrarlo (enrollment_type[]=student explícito, no incluir include[]=test_student), pero no documentan cómo aparece en /enrollments ni si el filtro type[]=StudentEnrollment basta.

### P131. Cuando un estudiante se retira del curso (enrollment pasa a deleted/inactive/completed) después de que su repositorio individual o grupal fue creado, ¿qué hace la app con (a) su acceso al repo (mantener o quitar colaborador), (b) el repositorio individual (mantener, archivar), (c) su aparición en listas, faltantes, métricas de participación e informe diario, y (d) su membresía en el grupo?

- **Requisitos:** R2.2.1, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el estado 'retirado' en la máquina de estados, una acción del worker de reconciliación y la regla para no marcar 'sin participación' a alguien que ya no está.
- **Opciones planteadas:**
  - Mantener todo, solo marcar 'retirado' y excluir de métricas/informe
  - Quitar colaborador, mantener repo
  - Archivar repo individual / quitar del repo grupal
  - Configurable por el profesor a nivel de curso
- **Estudio de APIs:** §4.4 'nunca borren filas, marquen deleted_at'; §14 'no borren su repo ni su historia; márquenlos'. No dice qué hacer con el acceso del colaborador ni con su presencia en métricas/informe.

### P132. Si un estudiante retirado vuelve a inscribirse en el mismo curso (reactivate o nueva enrollment), ¿se restaura su registro anterior (mapeo GitHub, repositorio, historial) o se trata como estudiante nuevo? ¿Y si vuelve con otro canvas_user_id (cuenta Canvas distinta)?

- **Requisitos:** R2.2.1, R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita repos duplicados y pérdida del mapeo; fija la clave de identidad del estudiante en la BD y la transición retirado→activo.
- **Estudio de APIs:** §4.1 menciona PUT .../reactivate y §4.4 fija canvas_user_id como clave estable, pero no aborda la reactivación.

### P133. Un estudiante que se inscribe después de que la tarea y sus repos ya existen: ¿aparece automáticamente en la siguiente sincronización, se le solicita su usuario GitHub sin intervención docente y el worker le crea el repo en cuanto lo entregue, o algún paso requiere confirmación del profesor? ¿Se avisa al equipo docente de la incorporación tardía?

- **Requisitos:** R2.2.1, R2.2.5, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Concreta R2.3.10 para el alta tardía y define si el flujo es 100% automático o tiene aprobación; también decide si existe un mensaje de bienvenida específico para el rezagado.
- **Opciones planteadas:**
  - Automático total sin aviso
  - Automático con notificación al docente
  - Requiere aprobación del profesor antes de crear el repo
- **Estudio de APIs:** §5.5 el cron recorre 'sujetos sin Repository en estado READY' y encola si hay login (implica automático); §6.3 recordatorio diario a quienes no tienen mapeo. No menciona aviso al docente.

### P134. ¿Qué datos del estudiante se almacenan y muestran (nombre, sortable_name, short_name, sis_user_id, login_id, email, avatar, canvas_user_id) y cuáles se refrescan en cada sincronización si cambian en Canvas? ¿Se conserva historial de cambios (nombre, sección, grupo, alta/baja con fecha y origen) o solo el valor vigente?

- **Requisitos:** R2.2.1, R2.2.2
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el modelo Student, la política de datos personales de la app y las columnas posibles de cualquier tabla de estudiantes; el historial permite explicar por qué un repo tiene colaboradores distintos al grupo actual.
- **Estudio de APIs:** §4.4: canvas_user_id como clave estable, 'el nombre y el email cambian'. §7.4 propone log de auditoría solo para cambios de fechas. Apéndice A.3 advierte que el email puede no venir en /users.

### P135. ¿La instancia Canvas que usarán devuelve el email del estudiante al token del profesor (include[]=email en /users, campo login_id/email en /enrollments, o solo vía GET /users/:id/profile primary_email)? ¿Con qué permisos?

- **Requisitos:** R2.2.1, R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Si el email no está disponible, quedan descartados del spec la atribución de commits por email, la importación CSV por email y cualquier comunicación fuera de Canvas; el spec debe declarar la fuente exacta.
- **Estudio de APIs:** Apéndice A.3: include[]=email no está en la lista documentada; ruta segura GET /api/v1/users/:id/profile o no depender del email.

### P136. Si la sincronización con Canvas falla (token expirado o revocado, 403/429 por throttling, curso inaccesible porque el profesor dejó de ser teacher, timeout), ¿qué ve el equipo docente (banner con causa y hora del último dato válido), se siguen usando los datos previos para el worker de repos, quién recibe la alerta, y puede otro profesor del curso re-autorizar con su propio token sin perder datos?

- **Requisitos:** R2.2.1
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija los estados de error de la sincronización, el comportamiento degradado, el flujo de recuperación y un criterio de aceptación de 'la app no presenta datos viejos como actuales'.
- **Estudio de APIs:** §1.5 exige manejar 403 y 429 con backoff; §1.1 refresh_token cifrado para jobs nocturnos; §3.4 opción A usa el token del profesor para todo; §7.4 'muestren última sincronización'. No define UX de fallo ni recuperación.

### P137. ¿Se permite vincular y sincronizar un curso de Canvas sin estudiantes, no publicado o ya concluido (workflow_state completed)? ¿Qué muestra la pantalla de estudiantes en estado vacío y el checklist de verificación marca error o advertencia?

- **Requisitos:** R2.2.1, R2.2.2
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el estado vacío de la vista de estudiantes y el comportamiento del checklist; en la demo un curso recién creado puede tener 0 estudiantes hasta que se inscriban.
- **Opciones planteadas:**
  - Bloquear la vinculación si n=0
  - Permitir con advertencia visible
  - Permitir sin advertencia
- **Estudio de APIs:** §3.3 checklist: 'Vemos estudiantes → n > 0' (implica que 0 sería fallo); §3.2 lista workflow_state y state[] pero no restringe.

### P138. ¿Qué garantías de consistencia se exigen cuando la sincronización de Canvas y el worker de provisión corren a la vez: un estudiante desaparece del roster mientras se crea su repo, o un grupo cambia de integrantes mientras se agregan colaboradores? ¿Lock por curso, lock por sujeto, o se acepta convergencia eventual en el siguiente ciclo?

- **Requisitos:** R2.2.1, R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina el diseño de locks/transacciones y qué anomalías transitorias son aceptables en la tabla de estados.
- **Estudio de APIs:** §5.5 pide crear_repo idempotente 'con lock por sujeto'; §1.5 sync secuencial por token. No aborda la interacción sync↔worker.

### P139. Si un mismo usuario de Canvas tiene una StudentEnrollment y además otro rol en el curso (TA, Teacher, Observer; p. ej., un ayudante inscrito como estudiante en otra sección), ¿se trata como estudiante (se le exige usuario GitHub y se le crea repo), se excluye, o se marca para decisión docente?

- **Requisitos:** R2.2.1
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita crear repos a ayudantes y define un filtro explícito por tipo de enrollment y precedencia de roles.
- **Estudio de APIs:** §4.1 filtra type[]=StudentEnrollment; no discute usuarios con múltiples roles.

### P140. Un estudiante inscrito en dos o más secciones del mismo curso: ¿el modelo es N:M y se muestran todas las secciones, se elige una 'principal' (¿con qué regla?), o se pide al profesor resolverlo? ¿Cuál se usa en la descripción del repositorio, en filtros y en la fecha efectiva?

- **Requisitos:** R2.2.2
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Afecta el modelo de datos, la columna 'Sección' de todas las tablas, la descripción del repo y el cálculo de fechas por sección (R2.4.2).
- **Opciones planteadas:**
  - N:M, mostrar todas separadas por coma
  - Sección principal = primera enrollment activa, resto en tooltip
  - El profesor elige la sección principal por estudiante
- **Estudio de APIs:** §4.2 advierte 'un estudiante puede estar en más de una sección' y pide N:M; §7.3 usa la fecha más tardía entre secciones; §5.4 pone 'Sección 2' en la descripción del repo.

### P141. ¿Qué información de secciones se muestra y dónde: lista de secciones del curso con conteo de estudiantes, nombre vs sis_section_id, filtro por sección en las tablas de estudiantes/faltantes/repos, secciones sin estudiantes? ¿Se muestra 'sección' para un grupo cuyos integrantes son de secciones distintas?

- **Requisitos:** R2.2.2
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** R2.2.2 pide 'identificar' la sección; hay que decidir si eso implica una pantalla propia o solo una columna/filtro, y qué se muestra en grupos mixtos.
- **Estudio de APIs:** §4.2 endpoint /sections con include[]=total_students; §5.6 columna 'Sección' en la tabla de repos. No define vista de secciones ni el caso de grupos mixtos.

### P142. Si Canvas mueve a un estudiante de una sección a otra a mitad de una tarea, ¿la app actualiza la sección mostrada, recalcula la fecha efectiva de sus entregas pendientes, actualiza la descripción del repo en GitHub y registra el cambio en un historial visible para el docente?

- **Requisitos:** R2.2.2
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija qué hace el sync ante cambios de sección y si existe un log de cambios de roster consultable.
- **Estudio de APIs:** §7.4 recalcula fechas efectivas ante cambios en assignments; §4.4 upsert. No menciona cambios de sección del estudiante.

### P143. ¿Cómo aparecen en GET /courses/:id/sections y en /enrollments las secciones cross-listed desde otro curso (nonxlist_course_id) y los estudiantes cuya sección fue eliminada o fusionada? ¿La app debe soportarlo o el spec lo declara fuera de alcance?

- **Requisitos:** R2.2.2
- **Área declarada:** 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Decide si el modelo admite secciones 'externas' y qué mostrar cuando la sección referenciada por una enrollment ya no existe.
- **Estudio de APIs:** §4.2 lista nonxlist_course_id y los endpoints de crosslist pero no describe el efecto sobre el roster.

### P144. ¿Qué group sets (group categories) se sincronizan: todos los del curso o solo el referenciado por assignment.group_category_id de las tareas vinculadas? Al crear una tarea grupal, ¿la app muestra al profesor el group set detectado y sus grupos para confirmación antes de crear repos, o lo usa sin preguntar?

- **Requisitos:** R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el alcance del sync de grupos, un paso de UI en el wizard de tarea y cómo se resuelve 'qué grupos aplican a esta tarea'.
- **Opciones planteadas:**
  - Sincronizar todos los group sets siempre
  - Solo los referenciados por tareas vinculadas
  - Todos, y mostrar/pedir confirmación del set detectado al crear la tarea
- **Estudio de APIs:** §5.1: group_category_id null ⇒ individual, con valor ⇒ grupal; §4.4 sincroniza todas las categorías; §4.3 endpoints de group_categories/groups.

### P145. ¿Qué se hace con un grupo vacío (0 integrantes) o unipersonal dentro del group set de una tarea grupal: se ignora, se muestra como 'grupo sin integrantes, sin repo', o se crea el repo igual para que el profesor asigne después?

- **Requisitos:** R2.2.3, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si los grupos vacíos cuentan como 'faltantes' (R2.2.6) y si el worker debe saltarlos.
- **Opciones planteadas:**
  - Ignorar silenciosamente
  - Mostrar como pendiente sin crear repo
  - Crear repo vacío
- **Estudio de APIs:** no lo aborda (§4.3 solo lista members_count).

### P146. En una tarea grupal, un estudiante inscrito que no pertenece a ningún grupo del group set: ¿solo se muestra como faltante, se le notifica por Canvas que debe unirse a un grupo, se avisa al profesor, se le crea un repo individual (¿automático o tras una fecha de corte?), o se espera indefinidamente?

- **Requisitos:** R2.2.3, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es el caso central de R2.2.6 para grupos: define un estado 'sin grupo', una comunicación y posiblemente una regla de creación excepcional.
- **Opciones planteadas:**
  - Solo mostrar como faltante
  - Notificar al estudiante
  - Notificar al profesor
  - Crear repo individual automáticamente
  - Repo individual tras fecha de corte configurable
- **Estudio de APIs:** §4.3: GET /group_categories/:id/users?unassigned=true es 'exactamente' lo que necesitan; §6.3 lo incluye en el panel de faltantes. No propone acción.

### P147. Confirmar en la documentación de Canvas que un usuario no puede pertenecer a dos grupos del mismo group set; y decidir defensivamente qué hace la app si la API devuelve esa inconsistencia (datos sucios): tomar el primero, marcar conflicto y alertar al docente, o bloquear la creación de repo.

- **Requisitos:** R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina si el modelo necesita restricción única (estudiante, group_set) y un estado de conflicto visible.
- **Estudio de APIs:** no lo aborda.

### P148. Cuando cambian los integrantes de un grupo después de creado su repositorio: ¿un integrante nuevo se agrega como colaborador automáticamente? ¿Un integrante que sale se quita automáticamente, solo con confirmación docente, o mantiene acceso? ¿Se notifica al estudiante y al docente? ¿Hay fecha límite de cambios (p. ej., tras la primera entrega ya no se aplican)?

- **Requisitos:** R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define un reconciliador de colaboradores (el worker propuesto solo crea) y la política de acceso; impacta R2.3.9 y las métricas por integrante.
- **Opciones planteadas:**
  - Agregar y quitar automáticamente
  - Agregar automático, quitar manual con confirmación
  - Congelar integrantes al crear el repo y solo alertar
  - Cambios aplicados solo hasta una fecha configurable
- **Estudio de APIs:** §5.5 el worker solo procesa sujetos sin repo READY; §4.4 upsert de grupos. No aborda reconciliación de colaboradores tras la creación.

### P149. Un estudiante que pasa del grupo A al grupo B tras haber hecho commits en el repo de A: ¿pierde acceso a A?, ¿cómo se atribuyen sus commits históricos en A en el dashboard y la corrección?, ¿queda registrado el período en que perteneció a cada grupo?

- **Requisitos:** R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita marcar 'sin participación' por error y define si la relación estudiante↔repo lleva fechas de pertenencia.
- **Estudio de APIs:** no lo aborda.

### P150. Si un grupo es eliminado en Canvas después de que su repo existe, ¿el repo se archiva, se mantiene con etiqueta 'grupo eliminado', se quitan los colaboradores, o se alerta al profesor para que decida? ¿Sus ex-integrantes pasan a 'sin grupo' en la vista de faltantes?

- **Requisitos:** R2.2.3, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define un estado terminal de repositorio y la regla de faltantes para ex-integrantes.
- **Estudio de APIs:** §4.4 'marcar deleted_at, no borrar'. No define efecto sobre el repo ni sobre los integrantes.

### P151. Si un grupo cambia de nombre en Canvas, ¿el repo de GitHub se renombra, se actualiza solo la descripción, o el nombre queda fijo al momento de creación (mostrando el nuevo nombre solo en la app)?

- **Requisitos:** R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.3.8 exige nombres inequívocos y estables; decide si la plantilla de nombre incluye el slug del grupo o solo el id.
- **Opciones planteadas:**
  - Nombre fijo al crear
  - Renombrar repo en GitHub
  - Actualizar solo la descripción
- **Estudio de APIs:** §5.4 propone {curso}-{periodo}-{tarea}-g{canvas_group_id}-{slug_grupo}; el id garantiza unicidad. No aborda renombres.

### P152. Si el profesor cambia en Canvas la configuración de una assignment vinculada (individual→grupal, grupal→individual, o cambia el group set) después de creados los repos, ¿la app lo detecta en el sync, bloquea o alerta, y qué pasa con los repos existentes?

- **Requisitos:** R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.3.3 exige consistencia; define detección de cambios en group_category_id y un estado de 'configuración inconsistente' visible.
- **Estudio de APIs:** §5.2 valida consistencia solo al vincular la segunda tarea; §7.4 hace polling por updated_at pero solo recalcula fechas.

### P153. Si el group set permite self-signup y los grupos siguen formándose, ¿el worker crea el repo grupal en cuanto haya ≥1 integrante mapeado, espera a que el grupo esté completo (is_full/group_limit), espera a que cierre el self-signup, o espera una fecha de corte configurada por el profesor?

- **Requisitos:** R2.2.3, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina el momento de creación de repos grupales y evita repos con integrantes parciales que luego cambian.
- **Opciones planteadas:**
  - Crear con ≥1 mapeado y agregar el resto progresivamente
  - Esperar a todos los integrantes mapeados
  - Esperar fecha de corte configurable
  - Esperar a que cierre el self-signup
- **Estudio de APIs:** §4.3 lista self_signup, group_limit, is_full; §5.5 crea cuando 'se dispone de toda la información'. No define qué es 'toda' para grupos en formación.

### P154. ¿Qué estados de GroupMembership (workflow_state accepted/invited/requested) cuentan como integrante del grupo para efectos de repo y faltantes? Verificar en la documentación de Groups/Group Memberships de Canvas.

- **Requisitos:** R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** Un integrante 'invited' que nunca acepta no debería bloquear la creación del repo grupal ni recibir acceso.
- **Estudio de APIs:** §4.3 lista GET /groups/:id/memberships y /users pero no discute estados de membresía.

### P155. ¿Cuál es la estrategia de enrolamiento Canvas↔GitHub que adopta el equipo (primaria y de respaldo)? Los estudiantes no usan la app: tarea de Canvas de texto donde escriben su usuario; tarea de Canvas + verificación OAuth de GitHub vía enlace; solo enlace OAuth enviado por Conversation; quiz/encuesta de Canvas; CSV del profesor; edición manual por el equipo docente; o combinación.

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es el proceso explícitamente evaluado por usabilidad y condiciona el flujo completo de la demo parcial, los permisos de la GitHub App, los mensajes a estudiantes y la máquina de estados del mapeo.
- **Opciones planteadas:**
  - A: tarea Canvas de texto
  - B: tarea Canvas + OAuth GitHub
  - C: solo enlace OAuth por Conversation
  - D: quiz/encuesta Canvas
  - E: CSV + edición manual
  - Combinación con primaria y fallback definidos
- **Estudio de APIs:** §6.1 recomienda tarea de Canvas (online_text_entry) + validación GET /users/{username}; §6.2 OAuth GitHub como complemento opcional; §6.3 carga manual + CSV como escape hatch.

### P156. Si se usa una tarea de Canvas como formulario: ¿la crea la app automáticamente (¿al vincular el curso o al crear la primera tarea?) o el profesor elige una existente? ¿Una por curso o una por tarea? ¿Nombre, descripción, puntos (0), omit_from_final_grade, visibilidad por sección, due_at/lock_at (¿se aceptan entregas tardías?), submission_type (texto vs URL), y quién puede editar esos textos?

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Concreta el paso del wizard, el objeto que la app escribe en Canvas, su ciclo de vida y el impacto en el libro de notas del estudiante.
- **Opciones planteadas:**
  - Creada automáticamente al vincular el curso
  - Creada al crear la primera tarea de programación
  - El profesor vincula una existente
  - Una por curso
  - Una por tarea
- **Estudio de APIs:** §6.1 muestra POST /assignments con online_text_entry, points_possible 0, published true y descripción de ejemplo; dice que 'la fecha de entrega sirve de plazo natural'. No decide una por curso vs por tarea.

### P157. ¿Qué reglas exactas de normalización/parseo se aplican al texto entregado? Casos: 'Mi usuario es jperez', 'https://github.com/JPerez/', '@jperez', 'JPEREZ' (mayúsculas), 'jperez@gmail.com' (email en vez de login), dos logins en el texto, texto vacío, entrega con adjunto en vez de texto, saltos de línea. ¿Cuándo se rechaza por ambiguo y con qué mensaje?

- **Requisitos:** R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el algoritmo de extracción, los mensajes de error al estudiante y los casos de prueba de aceptación.
- **Estudio de APIs:** §6.1 propone regex anclada al final del texto que tolera prefijo github.com/ y @, limpia HTML y usa el login canónico devuelto por GitHub (respeta mayúsculas). No cubre email, dos logins ni adjuntos.

### P158. Además de existir en GitHub (200 y type=User), ¿qué validaciones adicionales se exigen antes de aceptar un mapeo: que el login no esté ya asociado a otro estudiante del curso (o de otro curso), que no sea la cuenta de un profesor/ayudante ni la del bot de la app, que no sea una organización, que la cuenta no esté suspendida?

- **Requisitos:** R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define los sub-estados de 'inválido' y previene colisiones al agregar colaboradores.
- **Estudio de APIs:** §6.1 valida 200 + type == 'User' (advierte que una organización también devuelve 200). No valida duplicados ni cuentas del equipo docente.

### P159. Cuando el usuario entregado no existe (404) o es inválido, ¿cómo se le comunica al estudiante (comentario en la entrega, Conversation, ambos), con qué texto, cuántas veces, y cómo se marca la entrega en Canvas (¿'incomplete'?)? ¿Cómo aparece el caso en la vista docente?

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es el loop de feedback que hace usable el proceso; fija plantillas de mensaje y un estado INVALIDO visible.
- **Opciones planteadas:**
  - Comentario en la submission
  - Conversation individual
  - Ambos
  - Además marcar la entrega como incomplete
- **Estudio de APIs:** §6.1: 'si no → comentario pidiendo corrección'; §9.4 flag notify_missing_mapping; §5.6 fila 'Error: usuario inválido → Corregir'.

### P160. Si dos estudiantes entregan el mismo usuario de GitHub, ¿quién gana (primero, último, ninguno hasta que el docente resuelva)? ¿Se avisa a ambos estudiantes y al docente? ¿Se bloquea la creación de ambos repos mientras dure el conflicto?

- **Requisitos:** R2.2.4, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define un estado CONFLICTO en el mapeo y una acción docente de resolución.
- **Opciones planteadas:**
  - Primero gana, el segundo queda inválido
  - Último gana
  - Ambos en conflicto hasta resolución docente
- **Estudio de APIs:** no lo aborda.

### P161. Si el estudiante reenvía la tarea de registro con un usuario distinto antes de que exista su repo, ¿la app toma siempre la última entrega (attempt más reciente)? Si el docente ya había corregido el mapeo manualmente, ¿cuál tiene precedencia: la corrección manual o la nueva entrega del estudiante?

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija la regla de precedencia entre fuentes de mapeo (entrega, manual, CSV) y el manejo de múltiples attempts.
- **Opciones planteadas:**
  - Última entrega siempre gana
  - Manual gana y bloquea reentregas
  - Manual gana pero la reentrega genera alerta al docente
- **Estudio de APIs:** §6.1 poletea submissions pero no trata múltiples intentos ni precedencia frente a la carga manual de §6.3.

### P162. ¿Puede un estudiante cambiar su cuenta de GitHub después de creado su repositorio (p. ej., perdió acceso a la cuenta)? Si sí: ¿quién lo autoriza (solo docente), se quita el colaborador anterior y se agrega el nuevo, se revocan invitaciones pendientes, se renombra el repo si el nombre incluye el login, y cómo se atribuyen los commits anteriores?

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el flujo de re-mapeo, su permiso, y si la plantilla de nombre del repo puede depender del login (R2.3.8).
- **Opciones planteadas:**
  - Bloquear cambios tras repo creado salvo por docente
  - Permitir y reconciliar colaboradores automáticamente
  - Mantener ambas cuentas con acceso
  - Nunca renombrar el repo (usar id estable en el nombre)
- **Estudio de APIs:** §5.4 propone nombre individual con {githublogin} y lista endpoints de colaboradores/invitaciones. No aborda re-mapeo.

### P163. ¿El equipo acepta el riesgo de que un estudiante registre la cuenta de otra persona (sin prueba de propiedad), o exige verificación? Si exige: ¿OAuth de GitHub vía enlace, aceptación de la invitación de colaborador como confirmación implícita, o coincidencia del email público de GitHub con el de Canvas?

- **Requisitos:** R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Cambia la estrategia de enrolamiento, los permisos/callback de la GitHub App y los estados del mapeo (VALIDADO vs VERIFICADO).
- **Opciones planteadas:**
  - Aceptar el riesgo
  - OAuth GitHub
  - Aceptación de invitación como verificación
  - Email público coincidente
- **Estudio de APIs:** §6.1 declara la desventaja 'no prueba que el estudiante sea dueño'; §6.2 propone magic link + OAuth como verificación opcional.

### P164. Para la corrección manual del mapeo por el equipo docente: ¿qué roles pueden editar? ¿La edición valida contra GitHub en vivo? ¿Se registra quién, cuándo y el valor anterior (auditoría)? ¿Se avisa al estudiante del cambio? ¿Puede el docente marcar a un estudiante como 'exento/sin repo' para sacarlo de faltantes?

- **Requisitos:** R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define permisos (R2.1.8), la UI de edición inline, un log de auditoría y el estado 'exento' para estudiantes que no harán la tarea.
- **Estudio de APIs:** §6.3 'tabla editable con búsqueda incremental, valida contra GitHub en vivo'; §3.4 la propuesta de permisos no incluye editar mapeos ni exentos.

### P165. ¿Se implementa importación masiva por CSV? Si sí: ¿columnas de identificación (canvas_user_id, sis_user_id, email, nombre) + github_login, separador, codificación, vista previa antes de aplicar, manejo de filas inválidas y si sobrescribe mapeos existentes?

- **Requisitos:** R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es una de las alternativas de R2.2.5; define formato, validación por fila y semántica de sobrescritura.
- **Opciones planteadas:**
  - No implementar
  - CSV por canvas_user_id
  - CSV por sis_user_id o email
  - Con preview y reporte por fila
- **Estudio de APIs:** §6.3 propone CSV (canvas_user_id, github_login) 'para casos masivos'.

### P166. ¿Se puede eliminar o desvincular un mapeo existente? ¿Qué ocurre entonces con el repo ya creado y el colaborador (se quita, se mantiene), y vuelve el estudiante a 'faltante' y a recibir recordatorios?

- **Requisitos:** R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cierra el ciclo de vida del mapeo y define las transiciones inversas en la máquina de estados.
- **Estudio de APIs:** no lo aborda.

### P167. ¿Cómo se le comunica a cada estudiante que debe registrar su usuario de GitHub: anuncio en Canvas al crear la tarea de registro, Conversation individual, solo la descripción de la tarea, o combinación? ¿El texto incluye instrucciones para crear una cuenta GitHub si no la tiene? ¿Es una plantilla editable por el profesor? ¿Se envía automáticamente o el profesor lo dispara?

- **Requisitos:** R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es la primera interacción del estudiante con el proceso y parte de la usabilidad evaluada; define plantillas y un evento de comunicación.
- **Opciones planteadas:**
  - Anuncio al crear la tarea de registro
  - Conversation individual a todos
  - Solo la descripción de la tarea
  - Plantilla editable + envío manual por el profesor
- **Estudio de APIs:** §6.1 pone las instrucciones en la descripción de la tarea; §9.2 anuncios; §9.3 Conversations individuales; §9.4 flag notify_missing_mapping.

### P168. Recordatorios a estudiantes sin mapeo (o con mapeo inválido / invitación sin aceptar): ¿frecuencia (diaria, cada N días), hora y zona horaria (America/Santiago), tope máximo, canal, configuración por curso o por tarea, ¿se detienen si no hay tarea activa?, ¿el docente puede enviarlos manualmente desde la vista de faltantes? ¿Se registra el último recordatorio enviado por estudiante?

- **Requisitos:** R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el job de recordatorios, sus flags (R2.6.7) y la columna 'último recordatorio' en la vista de faltantes.
- **Estudio de APIs:** §6.3 job diario a estudiantes sin mapeo; §9.4 flag notify_missing_mapping por tarea; §9.3 envío secuencial con pausa; §14 zonas horarias en UTC.

### P169. ¿El mapeo estudiante↔GitHub es por curso o global por identidad Canvas (canvas_base_url + canvas_user_id)? Si un estudiante ya está mapeado en otro curso de la app, ¿se reutiliza automáticamente, se propone para confirmación docente, o se pide de nuevo?

- **Requisitos:** R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define la tabla de mapeo, su clave única y un atajo de usabilidad para cursos siguientes.
- **Opciones planteadas:**
  - Por curso
  - Global por identidad Canvas
  - Global con confirmación del docente
- **Estudio de APIs:** §5.2 no incluye la tabla de mapeo en el modelo; §11 la menciona como 'tabla de mapeo' sin alcance.

### P170. ¿Los estudiantes se invitan como miembros de la organización de GitHub (una invitación por semestre, acceso inmediato a repos posteriores) o solo como colaboradores externos de cada repo (una invitación por repo)? ¿Qué plan tiene la org (Free/Team) y existen límites de colaboradores o asientos que lo condicionen?

- **Requisitos:** R2.2.4, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Cambia el permiso Members:write de la App, la cantidad de estados 'invitación pendiente' y qué se muestra como faltante; el plan de la org es una dependencia externa.
- **Opciones planteadas:**
  - Miembros de la org
  - Outside collaborators por repo
  - Miembros solo si el plan de la org lo permite
- **Estudio de APIs:** §6.4 opcional: miembros de la org → PUT collaborators devuelve 204 en vez de 201; §14 'si la org es Free, revisen el límite de colaboradores en repos privados'.

### P171. Una invitación de colaborador no aceptada (respuesta 201): ¿cuenta como 'información faltante' para R2.2.6? ¿Se recuerda al estudiante y con qué frecuencia? ¿Se ofrece 'reenviar' (DELETE + PUT) y a qué rol? ¿Cómo se detecta la aceptación (polling de /invitations, webhook member)?

- **Requisitos:** R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el estado COLLABORATORS_PENDING como pendiente del estudiante, una acción de reenvío y el mecanismo de detección.
- **Estudio de APIs:** §5.4 201 = invitación pendiente, 204 = acceso directo; §5.6 acción 'Reenviar'; §6.3 incluye invitaciones sin aceptar en el panel; §8.1 sugiere suscribirse a member/member_invite.

### P172. ¿Cuánto duran las invitaciones de colaborador de GitHub antes de expirar (campo expired en GET /repos/../invitations) y qué ocurre al reinvitar a un usuario con invitación expirada o rechazada? Verificar en la documentación de Collaborators/Repository invitations.

- **Requisitos:** R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** Decide si el worker debe reinvitar automáticamente y con qué cadencia, y qué estado mostrar tras la expiración.
- **Estudio de APIs:** §5.4 menciona el campo expired y DELETE de invitación 'útil para reenviar', sin plazos.

### P173. ¿Se persiste el id numérico de GitHub además del login canónico, para sobrevivir a renombres de cuenta y detectar que un login fue reasignado a otra persona? ¿Se revalida periódicamente y qué se muestra si el login guardado ya no coincide con el id?

- **Requisitos:** R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el modelo del mapeo y una validación de integridad que evita agregar como colaborador a un desconocido.
- **Estudio de APIs:** §6.1 guarda solo el login canónico de GET /users/{username}.

### P174. Si el profesor elimina, despublica o cambia la fecha de la tarea de registro directamente en Canvas, ¿la app la recrea, alerta al profesor en el checklist del curso, o deja de recolectar mapeos silenciosamente?

- **Requisitos:** R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el monitoreo del 'formulario' y su estado en la pantalla de verificación del curso.
- **Estudio de APIs:** no lo aborda.

### P175. Al validar exitosamente un usuario, ¿qué recibe el estudiante: comentario de confirmación en la entrega, Conversation, calificación 'complete' en la tarea de registro, o nada hasta que exista el repo? ¿Texto exacto y si anticipa que deberá aceptar una invitación por correo?

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Cierra el loop de feedback y evita que el estudiante reenvíe por incertidumbre.
- **Estudio de APIs:** §6.1 'confirmar por comentario en la entrega'; §5.7 el mensaje de repo incluye 'revisa tu correo para aceptar la invitación'.

### P176. ¿Dispone el equipo de una instancia Canvas (institucional o Free-for-Teacher) donde puedan crear al menos 10 cuentas de estudiante con login real, inscribirlas en ≥2 secciones, crear group sets y hacer entregas en la tarea de registro como esos estudiantes? ¿Y ≥10 cuentas GitHub de prueba correspondientes para recibir y aceptar invitaciones?

- **Requisitos:** R2.2.1, R2.2.3, R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Sin esto no se puede demostrar el enrolamiento ni los estados 'invitación pendiente' e 'inválido' en la demo parcial, ni probar los casos borde de grupos.
- **Estudio de APIs:** §1.2 Plan B Free-for-Teacher; §13 hito 1: Canvas de pruebas con 2 secciones, ~10 estudiantes, 1 group set; §13 pide dejar visible un caso con problema.

### P177. ¿Qué columnas, estados y filtros tiene la vista de faltantes? Columnas candidatas: estudiante, sección, grupo, usuario GitHub y su estado, invitación al repo, estado del repo, último recordatorio, fuente del mapeo (entrega/manual/CSV), acciones. Filtros: sección, tarea, estado, 'solo problemas'; búsqueda por nombre; orden. ¿Contadores resumen tipo '37/40 mapeados'?

- **Requisitos:** R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es la materialización de R2.2.6 y lo que se evalúa visualmente en la demo.
- **Estudio de APIs:** §5.6 tabla por tarea (Estudiante/Grupo, Sección, GitHub user, Repo, Colaboradores, Estado, Acción) con filtro 'solo problemas'; §6.3 panel de faltantes como unión de 4 conjuntos.

### P178. ¿La vista de faltantes vive a nivel de curso (el mapeo es del estudiante, independiente de la tarea), a nivel de tarea (incluye grupos y repos), o ambas? ¿Dónde se ubica en la navegación y cómo se enlaza con la tabla de estado de repos (R2.3.11)?

- **Requisitos:** R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define la arquitectura de información y evita duplicar la misma tabla en dos lugares con estados distintos.
- **Opciones planteadas:**
  - Solo a nivel de curso
  - Solo a nivel de tarea
  - Ambas con datos compartidos
- **Estudio de APIs:** §5.6 tabla por tarea; §6.3 'panel de faltantes' sin ubicar nivel.

### P179. ¿Se requiere exportar la lista de faltantes/mapeos (CSV) para uso fuera de la app (p. ej., contactar por otros medios)? ¿Con qué columnas y quién puede exportar?

- **Requisitos:** R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Agrega o descarta un requisito funcional y define su formato.
- **Estudio de APIs:** no lo aborda.

### P180. ¿Cuál es la máquina de estados del mapeo estudiante↔GitHub? Propuesta a confirmar: SIN_REGISTRO → PENDIENTE_VALIDACION → INVALIDO (no existe / es organización / duplicado) | VALIDADO (existe) → VERIFICADO (OAuth o invitación aceptada); más EXENTO y RETIRADO. ¿Qué texto y color se muestra por estado y cuáles cuentan como 'falta información'?

- **Requisitos:** R2.2.4, R2.2.5, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es la base de la vista de faltantes, del worker y de los mensajes; sin ella no hay criterios de aceptación verificables.
- **Estudio de APIs:** §5.2 define estados de Repository (PENDING_MAPPING…ERROR) pero no del mapeo; §5.6 usa iconos y textos ad hoc.

### P181. ¿Qué acciones individuales y masivas ofrece la vista de faltantes: enviar recordatorio (uno/todos), editar mapeo, reintentar validación, reenviar invitación, marcar exento, abrir la entrega en Canvas, abrir el perfil GitHub? ¿Se piden confirmaciones para acciones masivas y se muestra un historial de lo enviado?

- **Requisitos:** R2.2.5, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define botones, permisos asociados y el historial de comunicaciones.
- **Estudio de APIs:** §5.6 acciones 'Recordar', 'Reenviar', 'Corregir', 'reintentar todos los fallidos'; §9.4 propone outbox con pantalla de historial.

### P182. En una tarea grupal donde solo parte de los integrantes tiene usuario GitHub válido, ¿el worker crea el repo con los disponibles y agrega al resto progresivamente, o espera a que todos estén mapeados? ¿Cómo se muestra el grupo en faltantes ('2/3 mapeados' y nombres de quién falta)?

- **Requisitos:** R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Interpreta 'toda la información requerida' de R2.3.10 para grupos y define la fila de grupo en la vista de faltantes.
- **Opciones planteadas:**
  - Crear con los disponibles
  - Esperar a todos
  - Crear con ≥ umbral configurable
- **Estudio de APIs:** §5.5 pseudocódigo ambiguo ('¿tiene(n) github_login mapeado?'); §5.6 muestra 'Grupo 12 · 2/3 mapeados · sin repo · Falta usuario de M. Soto', lo que sugiere esperar.

### P183. ¿Qué roles pueden forzar sincronización, editar/eliminar mapeos, importar CSV, enviar recordatorios, marcar exentos y ver la vista de faltantes? ¿Un ayudante básico tiene solo lectura?

- **Requisitos:** R2.2.1, R2.2.5, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** R2.1.8 exige ≥3 permisos definidos por el equipo; las acciones de 2.2 deben quedar asignadas a roles concretos.
- **Estudio de APIs:** §3.4 propone 7 permisos (course.manage, assignment.manage, repo.provision, …) sin incluir sincronizar ni editar mapeos.

### P184. Verificar que include[]=group_ids en GET /courses/:id/enrollments devuelve los grupos de todas las group categories del curso (no solo de una) y que refleja cambios de membresía con la misma latencia que /groups/:id/users, para decidir si basta una llamada o se requieren llamadas por grupo.

- **Requisitos:** R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia el número de requests del sync de grupos y su cadencia frente al throttling de Canvas.
- **Estudio de APIs:** §4.1 recomienda include[]=group_ids ('te da los grupos del estudiante en la misma llamada'); §4.4 además pagina groups por categoría.

### P185. Verificar el formato real del body de una submission online_text_entry (HTML envuelto en <p>, entidades, saltos) y si GET .../submissions acepta un filtro incremental (submitted_since o similar) con include[]=user y paginación completa, para diseñar el parser y el polling.

- **Requisitos:** R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Determina el parser y si el polling puede ser incremental o debe leer todas las submissions cada ciclo.
- **Estudio de APIs:** §6.1 'viene como HTML → limpiar tags'; propone GET /assignments/:aid/submissions?include[]=user sin filtro incremental.

### P186. Confirmar en la documentación de GitHub las reglas de nombres de usuario (longitud máxima 39, alfanumérico y guiones, sin guion inicial/final ni dobles) y que los logins son case-insensitive en GET /users/{username} y PUT collaborators, para fijar la normalización (lowercase vs login canónico) y la detección de duplicados.

- **Requisitos:** R2.2.4
- **Área declarada:** 2.2
- **Tipo:** Investigable en docs · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija la regex de validación y si 'JPerez' y 'jperez' son el mismo mapeo (evita conflictos falsos).
- **Estudio de APIs:** §6.1 regex con máximo 39 caracteres y uso del login canónico devuelto por GitHub.

### P187. ¿Qué tamaño máximo de curso debe garantizar la spec (número de estudiantes, secciones, grupos) para dimensionar sincronización, paginación y throttling, y para fijar criterios de rendimiento de la vista de faltantes (tiempo de carga, paginación en UI)?

- **Requisitos:** R2.2.1, R2.2.3, R2.2.6
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija criterios de aceptación no funcionales (duración del sync, latencia de la vista) y decisiones de paginación.
- **Estudio de APIs:** §1.4 per_page=100; §2.1 ejemplo con 60 estudiantes; §12 workers con cadencias fijas; no fija un tamaño objetivo.

### P188. Canvas ofrece 'Differentiation Tags' (categorías de grupo non_collaborative) que permiten asignar fechas distintas a subconjuntos de estudiantes en tareas INDIVIDUALES; sus overrides llegan con group_id apuntando a un grupo de una categoría non_collaborative. ¿Cómo se comportan la app y el algoritmo de fecha efectiva ante ellos: se consideran (el algoritmo del estudio solo evalúa group_id cuando la tarea es grupal, por lo que los ignoraría), se excluyen las categorías non_collaborative del selector de group sets para tareas grupales (R2.2.3), y cómo aparecen en la vista de fechas ('extensión por etiqueta X')? Verificar en la instancia real cómo vienen en overrides[] y en group_categories.

- **Requisitos:** R2.2.3, R2.3.3, R2.4.3
- **Área declarada:** 2.2 / 2.4
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Un profesor que use etiquetas de diferenciación tendría fechas efectivas incorrectas para estudiantes con extensión (2.4.3) y la app podría ofrecer una 'categoría de etiquetas' como si fuera un group set de tarea grupal.
- **Opciones planteadas:**
  - Tratar overrides de grupos non_collaborative como extensiones individuales en cualquier tipo de tarea
  - Excluir categorías non_collaborative de los group sets seleccionables
  - Ignorar y documentar la limitación
- **Estudio de APIs:** §4.3 lista collaboration_state y el campo non_collaborative sin explicar su efecto; §7.3 solo evalúa group_id si la tarea es grupal.

### P189. Cuando el término de Canvas concluye o el curso pasa a 'completed', TODAS las inscripciones pueden pasar a 'completed'/'inactive' en un solo ciclo de sync. ¿Existe un guardarraíl que distinga un cambio masivo (p. ej. >X % del roster en un ciclo, o workflow_state del curso cambiado) de retiros individuales, para NO ejecutar en cascada las acciones previstas para retirados (revocar colaboradores de todos los repos, marcar a todos como 'retirado', enviar mensajes, inundar el informe)? ¿Qué se hace en ese caso: pausar y pedir confirmación al profesor, tratarlo como conclusión del curso, o aplicar la regla individual sin excepción?

- **Requisitos:** R2.2.1, R2.3.9, R2.6.2, R2.6.5
- **Área declarada:** 2.2 / transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Una regla de retiro correcta a nivel individual puede destruir el acceso de todo un curso al terminar el semestre o ante un cambio administrativo en Canvas.
- **Opciones planteadas:**
  - Umbral de cambio masivo que pausa acciones destructivas y alerta
  - Detectar conclusión de curso/término y congelar el estado sin revocar
  - Aplicar la regla individual siempre
- **Estudio de APIs:** §4.4 indica 'marcar como retirado lo que ya no viene' y §14 'estudiantes que se retiran: márquenlos'; no aborda cambios masivos ni la conclusión del término.

### P190. Las instancias institucionales suelen tener roles personalizados de Canvas (p. ej. 'Profesor Titular' o 'Alumno Oyente') basados en TeacherEnrollment/StudentEnrollment: en la API el campo type conserva el tipo base y role/role_id el nombre personalizado. ¿La app filtra estudiantes y profesores por type (y no por role), y qué hace con roles personalizados que el profesor no quiera tratar como estudiantes (excluir por role_id configurable)? Verificar en la instancia real qué devuelven enrollment_type y type para esos roles.

- **Requisitos:** R2.2.1, R2.1.4
- **Área declarada:** 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un filtro por el nombre del rol dejaría fuera a todos los estudiantes con rol personalizado, o incluiría oyentes que no deben tener repo.
- **Opciones planteadas:**
  - Filtrar por type base
  - Filtrar por type con lista de exclusión por role_id configurable
- **Estudio de APIs:** §4.1 muestra type, role y role_id en el objeto Enrollment sin discutir roles personalizados.

### P191. Verificar el límite real de per_page en la instancia de Canvas usada (la documentación dice 'unspecified limit'; el estudio asume 100) para roster, enrollments, submissions y assignments con include[]=all_dates,overrides, y si respuestas grandes (muchos overrides ADHOC) se truncan o degradan el rendimiento. Fijar en el spec el per_page usado y el límite de páginas de seguridad por llamada.

- **Requisitos:** R2.2.1, R2.2.2, R2.4.4
- **Área declarada:** 2.2 / 2.5
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un per_page rechazado silenciosamente (cae a 10) multiplica las requests y puede activar el throttling en cursos grandes.
- **Estudio de APIs:** Apéndice A.6: 'límite real de per_page: 100 funciona de forma confiable; no asuman más'.

### P192. Cuando un estudiante es movido de sección en Canvas, la API suele devolver DOS enrollments para el mismo user_id (la antigua en estado deleted/inactive y la nueva active). ¿La app agrupa enrollments por user_id y toma solo las activas antes de aplicar reglas de retiro y de sección, para no marcar al estudiante como retirado y activo a la vez ni duplicarlo en las tablas? Verificar con state[] amplio qué devuelve exactamente la instancia tras un cambio de sección.

- **Requisitos:** R2.2.1, R2.2.2
- **Área declarada:** 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un modelo que persiste una fila por enrollment sin consolidar por usuario genera duplicados, secciones erróneas y falsos retiros.
- **Estudio de APIs:** §4.1 y §4.4 proponen upsert por canvas_user_id y marcar retirados; no aborda múltiples enrollments históricos del mismo usuario.

### P193. Tras vincular Canvas, la primera importación de estudiantes/secciones/grupos puede tardar. ¿Se muestra una pantalla o panel de progreso ('Importando… 42 estudiantes, 2 secciones, 1 grupo encontrados') o un spinner genérico? ¿Se bloquea la navegación mientras importa? ¿Qué se muestra si falla a mitad (importación parcial: mostrar lo importado con aviso, o descartar todo)? ¿Se puede seguir usando la app en otra pestaña mientras corre?

- **Requisitos:** R2.2.1, R2.2.2, R2.2.3
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el patrón de espera para procesos largos que se repetirá en aprovisionamiento y backfill, y las reglas de consistencia ante importaciones parciales.
- **Estudio de APIs:** §4.4 da la estrategia de sync (paginado, upsert, no borrar); no habla de la UI de progreso ni de fallos parciales.

### P194. Cuando el docente corrige el usuario GitHub de un estudiante que YA tiene repositorio creado (mapeo erróneo, cuenta equivocada), ¿qué opciones ofrece la UI: quitar al colaborador antiguo y agregar al nuevo en el mismo repo; crear un repo nuevo y marcar el anterior; solo actualizar el mapeo sin tocar GitHub? ¿Se muestra el impacto antes de confirmar ('este repo tiene 12 commits de jperez-old')? ¿Ocurre automáticamente en el siguiente ciclo del worker o requiere confirmación?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.9
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es un caso borde casi seguro en un semestre real; define transiciones adicionales de la máquina de estados del repo y un flujo de confirmación.
- **Estudio de APIs:** §6.3 describe la carga manual y el import CSV; §5.4 documenta DELETE collaborators; no aborda el cambio de mapeo post-creación.

### P195. Para la tabla de estudiantes/grupos y repositorios con 60–200 filas: ¿paginación, scroll virtual o todo en una página? ¿Filtros predefinidos ('solo problemas', 'sin usuario GitHub', 'invitación pendiente', 'listo', por sección, por grupo) como chips? ¿Búsqueda por nombre, usuario GitHub o nombre de repo? ¿Ordenamiento por columna? ¿Los filtros se conservan en la URL para compartir/volver? ¿Columnas exactas de la tabla y qué se muestra en cada celda vacía?

- **Requisitos:** R2.2.6, R2.3.11
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es la pantalla central de la demo parcial y de R2.3.11/R2.2.6; el spec debe fijar columnas, filtros y comportamiento con datos abundantes.
- **Estudio de APIs:** §5.6 propone columnas (Estudiante/Grupo, Sección, GitHub user, Repo, Colaboradores, Estado, Acción), filtro 'solo problemas' y botón 'reintentar todos los fallidos'.

### P196. ¿Qué se puede exportar a CSV/Excel (tabla estudiante–usuario GitHub–repo–estado, asignación de correctores, estado de corrección, informe diario)? Para el import CSV de mapeos: ¿hay plantilla descargable, validación por fila con reporte de errores (usuario inexistente, estudiante no encontrado, duplicado), vista previa antes de aplicar y política ante conflictos con mapeos existentes (sobrescribir / ignorar / preguntar)?

- **Requisitos:** R2.2.5, R2.7.1, R2.7.7
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define flujos completos de import/export con sus pantallas de validación, y si el import es parte de la entrega parcial como vía rápida de enrolamiento.
- **Estudio de APIs:** §6.3 propone import CSV (canvas_user_id, github_login) 'para casos masivos'; no define validación, vista previa ni export.

### P197. En la edición manual del usuario GitHub desde la tabla: ¿validación en vivo contra GitHub al escribir (con debounce) mostrando avatar, nombre y link al perfil para que el docente confirme la identidad antes de guardar? ¿Qué se muestra si el login existe pero es una Organization, si ya está mapeado a otro estudiante del mismo curso, si el estudiante lo escribió con URL/@ (normalización visible), o si GitHub no responde (guardar sin validar o bloquear)?

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es el 'escape hatch' del enrolamiento evaluado; define componente, estados de validación y regla de unicidad login↔estudiante por curso.
- **Estudio de APIs:** §6.1 normaliza el login y valida GET /users/{username} con type == 'User'; §6.3 propone 'tabla editable con búsqueda incremental… valida contra GitHub en vivo'.

### P198. Para la tarea de Canvas 'Registro de usuario GitHub': ¿la app la crea automáticamente al crear el curso/tarea, la crea el profesor con un botón, o el profesor puede vincular una existente? ¿El texto de la descripción es una plantilla fija, o editable con vista previa y variables ({curso}, {fecha límite}, {ejemplo})? ¿Incluye instrucciones para crear cuenta GitHub si no tiene y aviso de que recibirá una invitación por correo? ¿Se muestra al profesor el enlace a esa tarea en Canvas y el conteo 'N de M estudiantes ya respondieron'?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.12
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es la pieza visible del enrolamiento cuya usabilidad se evalúa explícitamente; el texto que leen los estudiantes es parte del producto.
- **Opciones planteadas:**
  - Creación automática con plantilla fija
  - Creación asistida con plantilla editable y vista previa
  - Vincular tarea existente elegida por el profesor
- **Estudio de APIs:** §6.1 propone crear la tarea vía API con descripción 'Escribe SOLO tu nombre de usuario de GitHub (ej: jperez)…' y online_text_entry; no aborda editabilidad ni vista previa.

### P199. Cuando un estudiante entrega un usuario GitHub inválido, ¿qué feedback recibe en Canvas y cómo? ¿El comentario explica el problema concreto ('"juan-perez-uandes" no existe en GitHub; escribe solo tu nombre de usuario, por ejemplo jperez') y cómo reintentar (volver a entregar en la misma tarea)? ¿Se limita el número de avisos automáticos? ¿Qué pasa si la tarea de registro ya cerró (fecha límite) y el estudiante no puede reentregar: se le da otro canal o el docente lo carga manualmente? ¿Se distingue el caso 'entregó una Organization' del 'no existe'?

- **Requisitos:** R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Cierra el loop de feedback del enrolamiento, evaluado en usabilidad; define plantillas de mensaje y la regla para la fecha de cierre de la tarea de registro.
- **Estudio de APIs:** §6.1 paso 4: 'si no → comentario pidiendo corrección. Ese loop de feedback automático es la parte usable del requisito'; §6.1 advierte el caso type=Organization. No define textos ni cierre de la tarea.

### P200. Si en Canvas cambian los integrantes de un grupo después de creados los repos (estudiante se mueve de grupo, grupo eliminado, grupo nuevo), o la assignment pasa de individual a grupal: ¿qué muestra la UI (repo 'con integrantes desactualizados', repo 'huérfano') y qué acciones ofrece (agregar/quitar colaboradores, crear repo para el grupo nuevo, mantener acceso al antiguo)? ¿El worker lo aplica automáticamente o requiere confirmación docente?

- **Requisitos:** R2.2.3, R2.3.3, R2.3.9
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define reglas de negocio de reconciliación grupo↔repo y su representación en la tabla de estados; hoy es un vacío del alcance.
- **Estudio de APIs:** §4.4 'nunca borren filas… marquen deleted_at'; §5.4 documenta agregar/quitar colaboradores; no aborda el cambio de integrantes post-creación.

### P201. Un estudiante retirado del curso en Canvas (enrollment inactive/deleted): ¿desaparece de las tablas, se muestra tachado con filtro 'incluir retirados', o se mantiene igual con badge 'retirado'? ¿Se le quita automáticamente como colaborador del repo, se pregunta al docente, o se deja? ¿Cuenta en métricas y alertas ('estudiantes sin participación', informe diario)? ¿Y si vuelve a inscribirse?

- **Requisitos:** R2.2.1, R2.5.4, R2.3.9
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita alertas falsas y define el comportamiento visible y las acciones sobre GitHub para un caso que ocurre en todo semestre.
- **Estudio de APIs:** §4.4 y §14: marcar como retirado, no borrar repo ni historia. No define UI ni efecto en colaboradores/métricas.

### P202. ¿Cuál es la latencia real entre que un estudiante entrega su usuario en la tarea de Canvas y que esa submission aparece en la API (GET submissions), y entre eso y la creación del repo con los intervalos elegidos? ¿Qué promesa de tiempo se puede escribir en la descripción de la tarea y en el mensaje al estudiante ('tu repositorio estará disponible en menos de X minutos')?

- **Requisitos:** R2.2.5, R2.3.10
- **Área declarada:** 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** El texto que lee el estudiante y el indicador de progreso del docente dependen de un tiempo medido, no supuesto.
- **Estudio de APIs:** §6.1 describe el polling de submissions; §5.5 fija cron cada 2 min; no mide latencias.

### P203. La API de enrollments no tiene filtro incremental: cada sync es un volcado completo. ¿El retiro de un estudiante se infiere por AUSENCIA en el volcado (frágil ante páginas inconsistentes o errores parciales) o consultando explícitamente state[]=deleted,inactive,completed? ¿Se exige ausencia en N ciclos consecutivos o un umbral de seguridad (p. ej. no marcar retirados si desaparece más del 20% del roster en un ciclo, caso conclusión masiva de término o cambio de permisos del token) antes de reaccionar con efectos externos (revocar colaboradores)? ¿El estado se guarda por ENROLLMENT (canvas_enrollment_id, sección, estado, last_seen_at) y el estado del estudiante se deriva (activo si alguna enrollment activa), cubriendo al que deja una de sus dos secciones? ¿Cada corrida queda persistida como SyncRun (inicio, fin, resultado, conteos de altas/bajas/cambios, error) y con qué retención?

- **Requisitos:** R2.2.1, R2.2.2, R2.3.9, R2.5.4
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el algoritmo de diff del sync, la tabla de enrollments, cuándo es seguro disparar bajas en GitHub y qué datos alimentan el registro de cambios y el indicador de última sincronización.
- **Opciones planteadas:**
  - Ausencia en el volcado
  - Consulta explícita de estados no activos
  - Ausencia en N ciclos consecutivos
  - Umbral porcentual de bajas por ciclo
  - Estado por enrollment con derivación por estudiante
- **Estudio de APIs:** §4.1 lista state[] con deleted/inactive/completed; §4.4 dice marcar como retirado 'lo que ya no viene' (inferencia por ausencia). No aborda histéresis, nivel enrollment ni SyncRun.

### P204. Verificar contra la instancia Canvas real: ¿GET /courses/:id/enrollments?state[]=deleted,inactive,completed devuelve con el token del profesor las enrollments retiradas (incluyendo el objeto user), en cuánto tiempo aparecen tras el retiro, y se distingue 'concluded' por fin de término de 'deleted' manual? ¿Y la enrollment reactivada conserva el mismo canvas_enrollment_id?

- **Requisitos:** R2.2.1
- **Área declarada:** 2.2
- **Tipo:** Verificar empíricamente · **Entrega:** Ambas entregas
- **Por qué importa:** Determina si la detección de retiros puede ser explícita (más robusta) o debe inferirse por ausencia, y si canvas_enrollment_id sirve como clave estable.
- **Estudio de APIs:** §4.1 documenta los valores de state[] pero no confirma qué devuelve un token de profesor ni la latencia.

### P205. Para responder '¿quién integraba el grupo y en qué sección estaba al cierre de la entrega N?' ¿se modelan membresías de grupo y de sección con validez temporal (valid_from/valid_to, sin sobrescribir), se copia la lista de integrantes y secciones en la fila DeliverySnapshot al capturar, o no se conserva y siempre se usa la membresía actual? ¿Qué fuente usan la publicación de notas (R2.7.6), la comparación de integrantes (R2.5.8), los períodos por entrega (R2.5.7) y el cálculo de fecha efectiva al recapturar?

- **Requisitos:** R2.2.2, R2.2.3, R2.4.5, R2.4.7, R2.5.8, R2.7.6
- **Área declarada:** 2.2 / 2.4 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin historial temporal, un cambio de grupo posterior al cierre hace que la nota, la comparación y la evidencia se atribuyan a la persona equivocada; decide dos tablas y su clave.
- **Opciones planteadas:**
  - Tablas con valid_from/valid_to
  - Copia de integrantes en el snapshot
  - Solo membresía actual
- **Estudio de APIs:** §4.4 upsert por canvas_id sin historial; §7.3 calcula fechas con la membresía actual. No aborda validez temporal.

### P206. Inconsistencias entre fuentes de Canvas: (a) GET /groups/:id/users devuelve un integrante que no figura como StudentEnrollment activo (retirado, Test Student, TA agregado a un grupo); (b) una submission de la tarea de registro llega con un user_id que aún no existe en el roster sincronizado (alta reciente, sync desfasado). ¿Se crea una fila de estudiante 'no inscrito' marcada como tal, se ignora el dato hasta el próximo sync de roster, se dispara un sync inmediato, o se alerta al docente? ¿Ese integrante cuenta para 'grupo completamente mapeado' y recibe acceso al repo? ¿El universo de grupos de una tarea son todos los del group set o solo los que tienen al menos un integrante del roster activo?

- **Requisitos:** R2.2.1, R2.2.3, R2.2.4, R2.3.9
- **Área declarada:** 2.2 / 2.3 (datos sucios)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define las FKs entre roster, grupos y mapeos (¿NOT NULL?) y evita que el worker cree repos o invite a personas que no son estudiantes activos.
- **Opciones planteadas:**
  - Fila fantasma marcada
  - Ignorar hasta el próximo sync
  - Sync inmediato del roster
  - Alerta al docente
- **Estudio de APIs:** §4.3 y §6.1 asumen consistencia entre roster, grupos y submissions; no lo aborda.

### P207. Si se adopta la verificación por OAuth de GitHub (§6.2): ¿se descarta el access_token del estudiante inmediatamente tras leer GET /user o se persiste (¿para qué uso y con qué cifrado)? ¿Qué scopes se piden (ninguno vs read:user)? ¿El magic link es un JWT sin estado (no revocable, reutilizable hasta expirar) o un token de un solo uso almacenado (revocable, con used_at y reemisión)? Si el estudiante autoriza con una cuenta distinta a la que entregó por texto, ¿prevalece la verificada, se marca conflicto para el docente, o se rechaza?

- **Requisitos:** R2.2.4, R2.2.5
- **Área declarada:** 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la tabla de mapeos (fuente, verificado_en, github_id), la política de datos personales de estudiantes y la máquina de estados del enrolamiento.
- **Opciones planteadas:**
  - Descartar token, guardar solo login/id
  - Persistir token cifrado
  - JWT sin estado
  - Token de un solo uso almacenado
- **Estudio de APIs:** §6.2 propone JWT con canvas_user_id y 7 días de vigencia; no indica qué se guarda ni los scopes.

### P208. ¿Existe una exclusión de sujeto POR TAREA (además de la exención a nivel curso): 'no crear repo / no capturar / no corregir / no alertar' para un estudiante o grupo concreto (convalidación, caso especial), con motivo, autor y fecha? ¿Cómo interactúa con el predicado de 'información completa' del worker, con los denominadores de R2.7.7 y del dashboard, y con el informe diario? ¿Es reversible y qué pasa con el repo si ya existía (archivar, mantener, ignorar)?

- **Requisitos:** R2.2.6, R2.3.10, R2.4.5, R2.6.2, R2.7.7
- **Área declarada:** 2.2 / 2.3 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin este flag, un caso especial aparece para siempre como 'problema pendiente' en R2.3.11, R2.6.2 y R2.7.7; con él hay que definir su alcance y efectos en cada worker.
- **Opciones planteadas:**
  - Exclusión por tarea con motivo
  - Solo exención a nivel curso
  - Sin exclusiones (todo es pendiente)
- **Estudio de APIs:** No lo aborda.

---

## 2.3

### P209. ¿Qué artefactos de Canvas visibles para el estudiante puede crear o EDITAR la app además de la tarea de registro, los mensajes y los anuncios?: (a) editar la descripción de cada assignment de Canvas vinculado como entrega para insertar un bloque generado ('Esta entrega se evalúa desde tu repositorio GitHub; no subas archivos aquí; se registrará el último commit de la rama X antes de tu fecha de cierre'), con actualización automática si cambian fechas o repo; (b) crear una Página o Módulo 'Cómo trabajar con GitHub en este curso'; (c) crear eventos de calendario; (d) nada: la app solo crea la tarea de registro. Si edita descripciones, ¿pide confirmación al profesor, marca el bloque con delimitadores para no pisar el texto del profesor, y qué pasa si el profesor lo borra?

- **Requisitos:** R2.3.12, R2.6.6, R2.6.7, R2.3.1
- **Área declarada:** 2.3 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina si el estudiante encuentra las instrucciones en el lugar donde mira (la tarea de Canvas de la entrega) o solo en mensajes; fija qué endpoints de escritura adicionales (PUT assignments, POST pages/modules/calendar_events) necesita el token y el checklist de R2.1.6.
- **Opciones planteadas:**
  - Editar descripción de cada entrega con bloque delimitado
  - Crear Página/Módulo informativo
  - Solo tarea de registro + mensajes/anuncios
  - Dejar toda la redacción al profesor con plantilla sugerida copiable
- **Estudio de APIs:** §5.1 lista PUT /courses/:id/assignments/:id como endpoint disponible pero no propone editar descripciones; §6.1 solo crea la tarea de registro; no aborda páginas, módulos ni calendario.

### P210. ¿Cómo se renderizan para el estudiante los textos que la app envía por Canvas? Verificar contra la instancia real: (a) si el body de POST /conversations acepta HTML o solo texto plano y si las URLs se convierten en enlaces clicables en la web y en la app móvil de Canvas; (b) lo mismo para comment[text_comment] en submissions; (c) límites de longitud del body y del subject; (d) si los saltos de línea se conservan. Y fijar reglas de redacción derivadas: fechas siempre absolutas con zona horaria (no 'quedan 48 h', que puede llegar tarde por cola/throttling), URL completa del repo y de la invitación, y qué campo de nombre de Canvas se usa para saludar (name, short_name, sortable_name).

- **Requisitos:** R2.3.12, R2.6.5, R2.7.6
- **Área declarada:** 2.3 / 2.6
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Si el body es texto plano, las plantillas no pueden usar HTML ni enlaces con texto; los límites acotan el contenido de R2.3.12; el saludo y el formato de fecha fijan la plantilla base de todos los mensajes.
- **Estudio de APIs:** §9.3 muestra el body de conversations como texto plano con una URL incrustada y dice que subject es máx. 255; §9.2 indica que el message de anuncios acepta HTML; no aclara si body de conversations o text_comment aceptan HTML ni si los enlaces se vuelven clicables.

### P211. ¿Dónde y cómo se le comunica al estudiante el 'reglamento técnico' del repositorio y la transparencia del monitoreo?: rama que se evalúa, prohibición o no de trabajar en forks, tags reservados (entrega-N), criterio exacto de cierre (fecha del commit vs hora del push), que su actividad de commits se registra y se usa para evaluar participación individual (R2.5.4/R2.5.8), y cómo confirmar su versión registrada. Opciones de ubicación: README generado por la app en cada repo (¿también cuando no hay repo base, en vez del README vacío de auto_init?), descripción de la tarea de Canvas, anuncio al inicio, mensaje de 'repo disponible'. ¿La app hará commits automáticos en repos de estudiantes (README, archivo ENTREGAS.md con fechas actualizadas), aceptando que aparecerán en su historial y deben excluirse de métricas? ¿Se enviará a los grupos un resumen periódico de participación para que se autorregulen?

- **Requisitos:** R2.3.7, R2.3.12, R2.5.4, R2.5.8, R2.4.5
- **Área declarada:** 2.3 / 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el contenido inicial de cada repo (con o sin base), si la app escribe en repos de estudiantes, y el aviso ético de monitoreo que el equipo deberá defender el 7-oct.
- **Opciones planteadas:**
  - README generado por la app en todo repo
  - Solo descripción de la tarea de Canvas
  - Anuncio único al inicio del curso
  - Sin commits de la app en repos de estudiantes
- **Estudio de APIs:** §5.3/§5.4 usan auto_init (README vacío con el nombre del repo) o template; §8.4/§8.5 describen atribución y métricas de participación; no aborda informar al estudiante del monitoreo ni commits de la app en repos de estudiantes.

### P212. Carrera entre el reenvío automático de una invitación (DELETE + PUT) y el estudiante aceptándola: si el job revoca justo cuando el estudiante hace clic, ¿qué ve el estudiante ('invitación inválida') y cómo se evita (verificar GET /collaborators e /invitations inmediatamente antes de revocar; no reenviar dentro de una ventana de gracia tras el último recordatorio)? ¿El enlace de la invitación antigua que quedó en el correo del estudiante sigue funcionando tras el reenvío o queda muerto, y el nuevo mensaje de Canvas le advierte que use el enlace más reciente?

- **Requisitos:** R2.3.9, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita dejar al estudiante bloqueado por una acción del propio sistema y fija el orden de comprobaciones del job de reenvío.
- **Estudio de APIs:** §5.4 menciona DELETE .../invitations/{id} como 'útil para reenviar'; no aborda la concurrencia con la aceptación ni la validez del enlace antiguo.

### P213. Cuando el repositorio de un estudiante no puede crearse por causas NO atribuibles a él (repo en ERROR por permisos/límites de la org, token de Canvas roto que impide notificar, cola detenida), ¿qué recibe el estudiante y cuándo?: (a) silencio hasta que se resuelva; (b) mensaje 'estamos resolviendo un problema con tu repositorio' tras N horas en ERROR; (c) el docente decide caso a caso desde la vista de estado. Y para el caso de atraso causado por el propio estudiante (repo creado después del cierre de la entrega 1), ¿se le informa que esa entrega quedó sin versión y a quién debe contactar? Si el token de Canvas está roto y las notificaciones fallan, ¿existe un canal manual de respaldo (exportar lista de estudiantes con URL de repo para que el profesor la comunique)?

- **Requisitos:** R2.3.11, R2.3.12, R2.6.5
- **Área declarada:** 2.3 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define plantillas y disparadores de mensajes por fallas internas y un plan de contingencia de comunicación cuando Canvas no responde.
- **Opciones planteadas:**
  - Silencio hasta resolver
  - Aviso automático tras N horas en ERROR
  - Decisión docente caso a caso
  - Exportación para comunicación manual
- **Estudio de APIs:** §5.5 define el estado ERROR con reintentos y §9.4 el outbox; no aborda qué se le dice al estudiante ante fallas del sistema.

### P214. Al terminar el curso, ¿qué pasa con el repositorio desde la perspectiva del estudiante (su portafolio)?: (a) conserva acceso de lectura/push indefinidamente; (b) el repo se archiva (solo lectura) manteniendo su acceso; (c) se le retira el acceso; (d) se le ofrece transferir el repo a su cuenta personal o hacer fork antes de una fecha de eliminación, con aviso por Canvas. ¿Quién decide la política (profesor del curso, owner de la org) y la app la ejecuta o solo la documenta?

- **Requisitos:** R2.3.9, R2.4.7, R2.1.3
- **Área declarada:** 2.3 / 2.4
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija acciones de fin de curso (archivar, quitar colaboradores, transferir) y los mensajes de cierre a estudiantes; afecta si los snapshots siguen siendo accesibles a correctores tras la transferencia.
- **Opciones planteadas:**
  - Acceso permanente
  - Archivar manteniendo acceso
  - Retirar acceso
  - Ofrecer transferencia/fork con plazo
- **Estudio de APIs:** No lo aborda; §14 solo indica no borrar el repo ni la historia de estudiantes retirados.

### P215. Además de submission_types y published, ¿qué otras configuraciones del assignment de Canvas rompen el flujo y deben validarse al vincular una entrega? Verificar: si PUT .../submissions/:user_id con posted_grade y rubric_assessment funciona con anonymous_grading=true o moderated_grading=true (calificadores múltiples, notas ocultas hasta moderar); efecto de peer_reviews activas; de grading_type=not_graded (no acepta nota); de un assignment con allowed_attempts que bloquee comentarios; y qué tipos de assignment aparecen o no en la lista de pendientes/calendario del estudiante (¿'none' no se muestra y el estudiante nunca ve la fecha?). ¿Cuáles se bloquean, cuáles solo advierten, y se revalidan en cada sincronización?

- **Requisitos:** R2.3.1, R2.7.5, R2.7.6, R2.4.1
- **Área declarada:** 2.3 / 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita descubrir en la corrección que Canvas rechaza las notas, y asegura que el estudiante vea la fecha de cierre en Canvas.
- **Estudio de APIs:** §5.1 lista campos del Assignment (group_category_id, published, submission_types, grade_group_students_individually) y §10.4 el PUT de notas; no menciona anonymous_grading, moderated_grading, peer_reviews ni grading_type.

### P216. ¿La app audita periódicamente que quienes tienen acceso a cada repo sean exactamente los que deben (integrantes vigentes + equipo docente) y que la configuración no haya derivado?: colaborador inesperado agregado por un owner de la org o por un mapeo erróneo ya aceptado, repo vuelto público, rama por defecto renombrada, forks existentes. Ante un acceso indebido detectado (un desconocido aceptó la invitación de un login mal registrado), ¿cuál es el procedimiento: revocar automáticamente, alertar al docente, informar a los integrantes del grupo que su código pudo ser visto, registrar el incidente?

- **Requisitos:** R2.3.9, R2.3.11, R2.5.5
- **Área declarada:** 2.3 / 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define un job de reconciliación de accesos, nuevos estados en R2.3.11 ('acceso inesperado', 'visibilidad alterada') y un procedimiento de incidente de privacidad.
- **Opciones planteadas:**
  - Reconciliación automática con revocación
  - Solo alerta al docente
  - Sin auditoría (fuera de alcance)
- **Estudio de APIs:** §5.4 lista GET /collaborators e /invitations y §8.1 los eventos member/repository; no aborda accesos no esperados, cambios de visibilidad ni incidentes.

### P217. ¿En qué orden recibe el estudiante los dos correos? Hoy GitHub envía su email de invitación en cuanto la app hace PUT collaborators, y el mensaje de Canvas llega después; el estudiante ve primero un correo de GitHub sin contexto. ¿Se envía un mensaje de Canvas de 'pre-aviso' ANTES de invitar ('en los próximos minutos recibirás una invitación de la organización X a tu correo de GitHub'), se invita y avisa en la misma transacción, o se acepta el orden actual? En el modelo de miembros de la org (§6.4) hay DOS aceptaciones (org y luego nada, o repo): ¿el mensaje explica ambas y en qué orden?

- **Requisitos:** R2.3.9, R2.3.12, R2.6.7
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Reordena los pasos del worker (§5.5 paso 4 vs 6) y el contenido del mensaje de R2.3.12 para reducir invitaciones ignoradas.
- **Opciones planteadas:**
  - Pre-aviso por Canvas antes de invitar
  - Invitar y avisar simultáneamente
  - Orden actual (GitHub primero)
- **Estudio de APIs:** §5.5 fija el orden crear repo → agregar colaboradores → notificar por Canvas (paso 6); §6.4 describe la invitación a la org; no considera avisar antes de invitar.

### P218. Muchos estudiantes crearán la cuenta de GitHub el mismo día que registran su usuario. Verificar con una cuenta recién creada: (a) si una cuenta sin email verificado recibe y puede aceptar la invitación de colaborador a un repo privado de una org; (b) si GitHub impone restricciones a cuentas nuevas (límites de invitaciones recibidas, verificación adicional) que dejen la invitación en un estado no visible en GET /invitations; (c) si un usuario con invitación a la org PENDIENTE (§6.4) recibe 201 o 204 al ser agregado como colaborador y qué pasa al aceptar la org después. ¿Qué estado y mensaje muestra la app para 'invitación enviada pero cuenta sin verificar'?

- **Requisitos:** R2.3.9, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Determina si hace falta un estado adicional y un texto en la tarea de registro ('verifica tu correo en GitHub antes de registrar tu usuario').
- **Estudio de APIs:** §5.4 y §6.4 describen 201 (invitación) vs 204 (acceso directo); no aborda cuentas nuevas, emails sin verificar ni invitaciones a la org pendientes.

### P219. Al crear una tarea, ¿qué assignments de Canvas se ofrecen en el selector y con qué filtros? ¿Se muestran los no publicados, los de tipo quiz/discusión/no-submission/external tool, el assignment auxiliar de 'Registro de usuario GitHub' y los ya vinculados a otra tarea de la app? ¿Un mismo assignment de Canvas puede pertenecer a más de una tarea de la app o hay unicidad global por curso?

- **Requisitos:** R2.3.1, R2.3.2
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la restricción de unicidad (canvas_assignment_id único por curso o no), los filtros del wizard, el mensaje de estado vacío ('el curso no tiene tareas en Canvas') y evita que se creen dos conjuntos de repos para el mismo assignment.
- **Opciones planteadas:**
  - Mostrar todos y marcar los no aptos como deshabilitados con motivo
  - Mostrar solo publicados y con submission_types compatibles
  - Permitir vincular un assignment a una sola tarea (unicidad estricta)
  - Permitir re-vincular con advertencia
- **Estudio de APIs:** §5.1 recomienda GET /assignments?include[]=all_dates&include[]=overrides y 'no creen repos para tareas no publicadas'; §5.2 modela Delivery con canvas_assignment_id 1:1 pero no fija unicidad global ni filtros del selector; §6.1 introduce un assignment auxiliar que probablemente no debería ser vinculable.

### P220. ¿Cómo se determina el orden de las entregas de una tarea: por due_at de Canvas, por orden manual del profesor, o por orden de vinculación? ¿Qué ocurre si Canvas cambia una fecha y el orden por fecha deja de coincidir con el orden guardado, o si un assignment tiene due_at nulo?

- **Requisitos:** R2.3.2
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** El orden alimenta el nombre de tags (entrega-1, entrega-2), los períodos de actividad de R2.5.7 y la navegación del corrector; un orden mutable rompe referencias ya creadas.
- **Opciones planteadas:**
  - Orden manual fijado por el profesor (order_index estable)
  - Orden derivado de due_at recalculado en cada sync
  - Manual con advertencia cuando las fechas lo contradicen
- **Estudio de APIs:** §5.2 propone order_index en Delivery sin decir cómo se asigna ni si se recalcula.

### P221. ¿Cómo se identifica 'la entrega final': la marca el profesor explícitamente, es la última por fecha, o la última en el orden? ¿Es obligatorio que exista exactamente una final? ¿Puede una tarea tener solo entregas parciales? Si la tarea tiene una única entrega, ¿es final automáticamente?

- **Requisitos:** R2.3.2
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina reglas de validación al crear/editar la tarea, el rótulo en UI, qué entrega dispara el cierre/archivado de repos y qué se muestra como 'entrega final' en dashboards e informes.
- **Estudio de APIs:** §5.2 usa kind: 'partial' | 'final' sin definir cardinalidad ni regla de asignación.

### P222. ¿Se puede agregar o quitar una entrega después de creada la tarea, incluso cuando ya existen repositorios o snapshots capturados? Si se quita una entrega con snapshot registrado, ¿se conserva el snapshot/tag o se elimina? ¿Se puede cambiar el assignment de Canvas asociado a una entrega existente?

- **Requisitos:** R2.3.1, R2.3.2, R2.3.4
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija las reglas de edición del ciclo de vida de la tarea, qué transiciones quedan bloqueadas, y protege la evidencia de R2.4.7.
- **Estudio de APIs:** No lo aborda; §5.2 solo describe la estructura Assignment→Delivery.

### P223. ¿El nombre y el slug de la tarea en la app los escribe el profesor o se derivan del primer assignment de Canvas? ¿Son editables después? Si el slug forma parte del nombre de los repos, ¿qué pasa con los repos ya creados al cambiarlo?

- **Requisitos:** R2.3.1, R2.3.8
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El slug es un componente del nombre inequívoco de R2.3.8; su mutabilidad decide si los nombres son estables o si hay que renombrar repos.
- **Estudio de APIs:** §5.2 incluye name y slug en Assignment(app) y §5.4 usa {tarea} en la plantilla de nombre, sin decir su origen ni mutabilidad.

### P224. Cuando se vincula una segunda entrega cuya configuración individual/grupal difiere de la primera, ¿la app rechaza la vinculación, la permite con advertencia, o pide elegir cuál manda? Y ¿qué significa 'misma configuración': solo coincidir en individual vs grupal, o también el mismo group_category_id exacto? Dos assignments grupales con group sets distintos, ¿son compatibles?

- **Requisitos:** R2.3.3
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la regla de validación de R2.3.3 y si los repos grupales de una tarea pueden apuntar a agrupaciones distintas (lo que rompería R2.3.4: un solo conjunto de repos).
- **Opciones planteadas:**
  - Rechazo estricto por group_category_id idéntico
  - Rechazo solo si difiere individual/grupal
  - Permitir con advertencia y usar la configuración de la primera entrega
- **Estudio de APIs:** §5.2 recomienda comparar group_category_id y rechazar con mensaje claro si difieren; el enunciado solo exige 'misma configuración'.

### P225. Si después de vincular, el profesor cambia en Canvas el group_category_id de un assignment (individual→grupal, grupal→otro group set, grupal→individual), ¿qué hace la app? ¿Se congela la configuración detectada al vincular, se marca la tarea como inconsistente y se pausa el aprovisionamiento, o se recalculan sujetos (creando/quitando repos)?

- **Requisitos:** R2.3.3, R2.3.4, R2.3.10
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Decide si el worker de R2.3.10 puede llegar a crear repos de un tipo distinto para la misma tarea y qué alerta ve el profesor.
- **Opciones planteadas:**
  - Congelar configuración al vincular e ignorar cambios
  - Marcar tarea 'inconsistente', pausar worker y alertar
  - Recalcular sujetos automáticamente
- **Estudio de APIs:** §5.2 solo valida al vincular; §7.4 (polling con updated_at) detectaría el cambio pero no propone acción para este caso.

### P226. En una tarea grupal, ¿qué se hace con estudiantes que aún no tienen grupo (unassigned) o con un group set que todavía no tiene grupos creados? ¿Se les crea un repo individual, quedan en estado pendiente indefinidamente, o hay un plazo tras el cual se actúa? ¿Un grupo con 0 integrantes cuenta como sujeto?

- **Requisitos:** R2.3.7, R2.3.10, R2.3.11, R2.2.6
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define los estados 'PENDING_GROUP' de la máquina de estados, qué aparece en el panel de faltantes y si el worker puede crear repos sin dueño.
- **Estudio de APIs:** §4.3 señala GET /group_categories/:id/users?unassigned=true para listar estudiantes sin grupo (R2.2.6); no define qué hacer con ellos en el aprovisionamiento.

### P227. Cuando la membresía de un grupo cambia en Canvas después de creado el repo (un estudiante sale, entra, se cambia de grupo, un grupo se elimina o fusiona), ¿la app quita/agrega colaboradores automáticamente? ¿El estudiante que se cambia de grupo pierde acceso al repo anterior y gana acceso al nuevo? ¿Se conserva el historial? ¿Existe un 'congelamiento' de grupos a partir de cierta fecha (p. ej., primer due_at)?

- **Requisitos:** R2.3.9, R2.3.4, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina la sincronización continua entre grupos de Canvas y colaboradores de GitHub, y los estados 'MEMBERSHIP_CHANGED' visibles en R2.3.11.
- **Opciones planteadas:**
  - Sincronización automática bidireccional (agregar y quitar)
  - Solo agregar, nunca quitar; mostrar alerta
  - Congelar membresía al primer cierre y requerir acción manual
- **Estudio de APIs:** §4.4 recomienda marcar como retirado sin borrar; no aborda la remoción/adición de colaboradores por cambio de grupo.

### P228. Si un assignment vinculado es eliminado en Canvas (o el curso de Canvas se concluye/elimina), ¿qué estado toma la entrega, se detiene el aprovisionamiento de la tarea, se conservan los repos, y cómo se avisa al profesor?

- **Requisitos:** R2.3.1, R2.3.10, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin regla, el sync fallará silenciosamente (404) y el worker puede seguir creando repos para una entrega inexistente.
- **Estudio de APIs:** No lo aborda directamente; §4.4 solo indica 'nunca borren filas al sincronizar'.

### P229. ¿Se permite vincular un assignment con published:false? ¿Se crean repos para él? Si el assignment se despublica después de vinculado, ¿se pausa el aprovisionamiento y las notificaciones o continúan?

- **Requisitos:** R2.3.1, R2.3.7, R2.3.10
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El estudio sugiere no crear repos para tareas no publicadas, pero el enunciado no lo exige; afecta el flujo de la demo (el profesor puede querer preparar repos antes de publicar).
- **Estudio de APIs:** §5.1: 'published: no creen repos para tareas no publicadas' (recomendación, no requisito).

### P230. Si el assignment tiene visibilidad diferenciada (only_visible_to_overrides=true o asignado solo a ciertas secciones/estudiantes), ¿se crean repos solo para los estudiantes a quienes la tarea es visible? ¿Cómo se obtiene esa lista (include[]=assignment_visibility) y qué pasa si la visibilidad cambia después?

- **Requisitos:** R2.3.7, R2.3.10
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita crear repos para estudiantes que no tienen la tarea en Canvas y define el conjunto de sujetos de la tarea.
- **Estudio de APIs:** §5.1 lista include[]=assignment_visibility; §7.3 trata only_visible_to_overrides solo para snapshots, no para aprovisionamiento.

### P231. ¿Cuándo comienza el aprovisionamiento de una tarea: inmediatamente al guardarla, tras un paso explícito 'activar/confirmar', al llegar unlock_at del primer assignment, o tras confirmar el repo base? ¿Qué significa 'tarea activa' para el worker?

- **Requisitos:** R2.3.10, R2.3.7
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define si el profesor puede configurar la tarea (repo base, entregas) sin que se creen repos a medias, y el criterio de aceptación de la demo.
- **Estudio de APIs:** §5.5: 'para cada Assignment activo' sin definir 'activo'; §5.3 sugiere que el repo base exista antes de generar.

### P232. ¿El aprovisionamiento continúa indefinidamente (estudiante que se mapea después del cierre de la entrega final recibe repo) o existe un corte (p. ej., tras la última fecha de cierre, al archivar la tarea)? ¿Qué se muestra a ese estudiante tardío?

- **Requisitos:** R2.3.10
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita crear repos inútiles tras el cierre y define el estado terminal de la tarea.
- **Estudio de APIs:** No lo aborda.

### P233. ¿Dónde y cómo se crea el repo base: en la org del curso, con qué convención de nombre (p. ej., {curso}-{tarea}-base), privado, marcado is_template, con auto_init? ¿Qué ocurre si ya existe un repo con ese nombre en la org?

- **Requisitos:** R2.3.5
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el flujo de R2.3.5, los permisos requeridos de la App y el comportamiento ante colisión.
- **Estudio de APIs:** §5.3 recomienda crearlo en la org como template repository con auto_init:true y private:true.

### P234. ¿Se permite designar como base un repositorio ya existente en la org (no creado desde la app) o importar contenido desde una URL/zip, o el único camino es crearlo desde la app como dice R2.3.5?

- **Requisitos:** R2.3.5, R2.3.6
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Amplía o restringe el alcance del wizard de tarea y las validaciones (is_template, pertenencia a la org).
- **Estudio de APIs:** No lo aborda; §5.3 solo cubre la creación desde la app.

### P235. Para los archivos iniciales del repo base: ¿cuántos archivos se pueden subir, con qué tamaño máximo por archivo y total, se permiten carpetas/rutas anidadas y archivos binarios, se ofrece .gitignore por plantilla y se genera un README automático (con enunciado, fechas, nombre de la tarea)? ¿Qué pasa con una carpeta vacía (git no la soporta)?

- **Requisitos:** R2.3.6
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define validaciones del formulario, mensajes de error y el uso de la Contents API vs Git Data API.
- **Estudio de APIs:** §5.3: PUT /contents con base64, límites de 1 MB / 100 MB en GET /contents, subir en serie por conflictos, gitignore_template disponible en POST /orgs/{org}/repos; sugiere Git Data API para archivos grandes.

### P236. ¿Se pueden editar, renombrar y eliminar archivos del repo base después de creado, desde la app (explorador/editor) o solo directamente en GitHub? Si el profesor modifica el repo base directamente en GitHub, ¿la app refleja esos cambios?

- **Requisitos:** R2.3.6
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina si R2.3.6 'administrar' implica CRUD completo en la app y si la vista de la app es fuente de verdad o solo espejo.
- **Estudio de APIs:** §5.3 recomienda un explorador de archivos en la app (GET /contents + textarea + PUT) más botón 'abrir en GitHub'; PUT requiere el blob sha para actualizar.

### P237. Si el repo base cambia (se agrega, se reemplaza o se modifican sus archivos) cuando ya existen repos de estudiantes creados, ¿qué ocurre con los ya creados: no se tocan (con aviso de heterogeneidad), se bloquea el cambio una vez creado el primer repo, o se propaga el cambio (p. ej., commit/PR en cada repo)? Y una tarea creada sin base cuyos repos ya existen vacíos, ¿puede recibir base después?

- **Requisitos:** R2.3.5, R2.3.6, R2.3.7
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita conjuntos de repos heterogéneos y define las transiciones bloqueadas del ciclo de vida de la tarea.
- **Opciones planteadas:**
  - No retroactivo, mostrar advertencia de repos heterogéneos
  - Bloquear cambios de base tras el primer repo creado
  - Propagar mediante commit/PR automático
- **Estudio de APIs:** No lo aborda.

### P238. ¿La generación desde el repo base usará POST /repos/{t}/generate (template) o copia de archivos vía Contents API? ¿Qué permisos exactos de la instalación exige cada camino, funciona en org Free, y con qué rama por defecto queda el repo generado? ¿Se usa include_all_branches?

- **Requisitos:** R2.3.5, R2.3.7
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** El estudio deja los permisos como ambiguos; un 403 el día de la demo bloquea R2.3.7.
- **Estudio de APIs:** §5.3-§5.4 recomiendan template + generate; §2.3 y Apéndice A.1/A.2 piden verificar empíricamente los permisos de POST /orgs/{org}/repos y /generate.

### P239. ¿Se permite incluir archivos en .github/workflows (GitHub Actions) en el repo base? Requiere permiso Workflows en la App y tiene implicancias de minutos de Actions en la org.

- **Requisitos:** R2.3.6
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define una validación de rutas prohibidas o un permiso adicional de la App.
- **Estudio de APIs:** §5.3: 'Contents (write) o Contents + Workflows write si suben archivos en .github/workflows/'.

### P240. Si el repo base o un repo de estudiante es eliminado o renombrado manualmente en GitHub (404 al sincronizar), ¿la app lo recrea automáticamente, lo marca como 'huérfano' y pide decisión, o adopta el nuevo nombre (usando github_repo_id)?

- **Requisitos:** R2.3.5, R2.3.7, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define un estado de la máquina y evita bucles de recreación no deseados.
- **Opciones planteadas:**
  - Marcar ORPHANED y requerir acción manual
  - Recrear automáticamente
  - Seguir por github_repo_id y actualizar nombre
- **Estudio de APIs:** No lo aborda; §5.2 guarda github_repo_id, lo que permitiría seguir renombres.

### P241. ¿Qué componentes exactos forman el nombre del repo: código de curso, período, slug de tarea, sección, identificador de grupo (canvas_group_id, slug del nombre), identificador del estudiante (login de GitHub, canvas_user_id, nombre)? ¿Se usa una convención fija o una plantilla configurable por curso/tarea con vista previa? ¿Debe evitarse exponer datos personales en el nombre?

- **Requisitos:** R2.3.8
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Es el núcleo de R2.3.8; decide unicidad, legibilidad, estabilidad ante cambios (login/grupo) y privacidad.
- **Opciones planteadas:**
  - Convención fija propuesta en §5.4
  - Plantilla configurable por curso con vista previa
  - Incluir sección en el nombre
  - Usar canvas_user_id en lugar de login
- **Estudio de APIs:** §5.4 propone {curso}-{periodo}-{tarea}-{githublogin} e {curso}-{periodo}-{tarea}-g{canvas_group_id}-{slug_grupo}; recomienda incluir canvas_group_id para unicidad.

### P242. Ante el límite de 100 caracteres de GitHub, ¿qué componente se trunca primero y cómo se garantiza unicidad tras truncar? ¿Qué reglas de sanitización se aplican (minúsculas, tildes/ñ, caracteres permitidos . - _, guiones consecutivos, nombres reservados)?

- **Requisitos:** R2.3.8
- **Área declarada:** 2.3
- **Tipo:** Investigable en docs · **Entrega:** Ambas entregas
- **Por qué importa:** Define la función determinista de nombrado y sus pruebas unitarias.
- **Estudio de APIs:** §5.4: sanitizar minúsculas, [^a-z0-9-]→'-', colapsar guiones, truncar a 100; no define prioridad de truncado.

### P243. Ante colisión de nombre (422 name already exists), ¿se agrega sufijo -2, se falla con error visible, o se adopta el repo existente? ¿Cómo distingue la app un repo 'suyo' (creado en un intento anterior) de uno ajeno preexistente en la org (p. ej., del semestre pasado)? ¿Se usa github_repo_id, un topic o la descripción como marcador?

- **Requisitos:** R2.3.8, R2.3.7, R2.3.10
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** La idempotencia del worker depende de esto; adoptar un repo ajeno daría acceso a estudiantes a código de otros.
- **Estudio de APIs:** §5.4 sugiere reintentar con sufijo -2; §5.5 dice tratar 422 como éxito y 'GET el repo y continuar', sin distinguir repos ajenos.

### P244. Si un grupo se renombra en Canvas o un estudiante cambia su login de GitHub (o se corrige el mapeo) después de creado el repo, ¿se renombra el repo (GitHub mantiene redirecciones), se mantiene el nombre original, o se muestra un alias en la app?

- **Requisitos:** R2.3.8, R2.3.9
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Decide si los nombres son inmutables y cómo se mantiene la 'inequivocidad' a lo largo del semestre.
- **Estudio de APIs:** No lo aborda; §5.2 guarda github_repo_id (estable ante renombres).

### P245. ¿Qué nivel de permiso reciben los estudiantes en su repo: push, maintain o admin? ¿Y el profesor/ayudantes: se agregan como colaboradores, como miembros/owners de la org, o solo acceden vía la App? Al retirar un ayudante (R2.1.9), ¿se le quita acceso a los repos?

- **Requisitos:** R2.3.9
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** admin permite borrar tags/repo (rompe R2.4.7); define también el modelo de acceso del equipo docente y la limpieza al retirar ayudantes.
- **Opciones planteadas:**
  - push
  - maintain
  - admin
- **Estudio de APIs:** §5.4: 'Usen push, NUNCA admin'; §3.4 sugiere DELETE /orgs/{org}/memberships al retirar ayudante.

### P246. Las invitaciones de colaborador expiran a los 7 días: ¿la app las reenvía automáticamente (DELETE + PUT), con qué frecuencia y hasta cuántas veces? ¿Se notifica al estudiante por Canvas en cada reenvío? ¿Existe acción manual 'reenviar invitación' y quién puede usarla?

- **Requisitos:** R2.3.9, R2.3.11, R2.3.12
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la transición COLLABORATORS_PENDING→READY, los recordatorios y el trabajo del worker.
- **Estudio de APIs:** §5.4 documenta GET /repos/{o}/{r}/invitations (campo expired), PATCH y DELETE 'útil para reenviar'; §5.6 muestra acción 'Reenviar'.

### P247. Si un estudiante rechaza la invitación, ¿cómo lo detecta la app (desaparece de /invitations sin aparecer en /collaborators)? ¿Qué estado y mensaje se muestran, se reintenta automáticamente, y se avisa al profesor?

- **Requisitos:** R2.3.9, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Distingue 'pendiente' de 'rechazado' en la máquina de estados y evita reintentos infinitos.
- **Estudio de APIs:** No lo aborda; §5.4 solo cubre 201/204 e invitaciones pendientes/expiradas.

### P248. ¿Cómo se detecta que el estudiante aceptó la invitación: polling a GET /collaborators e /invitations (con qué frecuencia y costo de rate limit) o mediante webhook de la App (evento member/member_invite)? ¿La App recibe efectivamente un evento cuando un outside collaborator acepta?

- **Requisitos:** R2.3.9, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Ambas entregas
- **Por qué importa:** Define la latencia de la transición a READY y la carga sobre el rate limit.
- **Estudio de APIs:** §8.1 lista eventos push, create, delete, repository, member, member_invite 'según disponibilidad'; §5.4 propone monitorear vía GET /invitations.

### P249. ¿Se invita a los estudiantes como miembros de la organización (una invitación por semestre, PUT 204 inmediato en cada repo) o se agregan como outside collaborators por repo? Si son miembros, ¿la org tiene 'default repository permission' en none para que no vean repos ajenos, y hay límite de asientos según el plan?

- **Requisitos:** R2.3.9, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia la máquina de estados (menos estados pendientes), los permisos de la App (Members write) y depende del plan de la org.
- **Opciones planteadas:**
  - Outside collaborators por repo
  - Miembros de la org con base permission none
  - Teams por grupo (§5.4 alternativa)
- **Estudio de APIs:** §6.4 lo presenta como opcional que mejora la experiencia; requiere permiso Members (write).

### P250. Cuando un estudiante se retira del curso (enrollment deleted/inactive/completed) o es Test Student/enrollment 'invited', ¿se le quita acceso al repo, se archiva su repo individual, en un grupal se remueve solo a él, y se excluye del aprovisionamiento? ¿Qué estado se muestra?

- **Requisitos:** R2.3.9, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define reglas de exclusión de sujetos y de revocación de acceso sin destruir historia.
- **Estudio de APIs:** §4.1 y §14: filtrar Test Student y no incluir estados no activos; §14: 'No borren su repo ni su historia; márquenlos' (sin definir revocación de acceso).

### P251. Si se corrige un mapeo Canvas→GitHub erróneo después de creado el repo (otro usuario recibió acceso), ¿se remueve al colaborador anterior, se renombra o recrea el repo individual, y qué se hace con los commits del usuario equivocado?

- **Requisitos:** R2.3.9, R2.3.8, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Es un caso plausible en la demo y en el uso real; define transiciones de corrección y seguridad del acceso.
- **Estudio de APIs:** No lo aborda; §6 cubre solo la validación inicial del login.

### P252. ¿Los repos son siempre privados o la visibilidad es configurable por tarea? ¿El plan de la organización (Free/Team/Education) impone límites a repos privados, colaboradores o funcionalidades (rulesets, branch protection) que afecten el diseño?

- **Requisitos:** R2.3.7, R2.3.9
- **Área declarada:** 2.3
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Determina el parámetro private/visibility y qué protecciones son posibles.
- **Estudio de APIs:** §14: 'Créenlos privados. Si la org es Free, revisen el límite de colaboradores en repos privados de organización'.

### P253. ¿Se aplica protección a la rama por defecto y a los tags entrega-N (impedir force-push, borrado de rama, borrado de tags) mediante rulesets o branch protection? ¿Está disponible en el plan de la org para repos privados? Si no, ¿se acepta el riesgo documentando que el SHA en BD es la fuente de verdad?

- **Requisitos:** R2.3.7, R2.3.9
- **Área declarada:** 2.3
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Impacta R2.4.7 y el permiso que reciben los estudiantes; requiere permisos adicionales de la App.
- **Estudio de APIs:** §7.5 sugiere ruleset de tags opcional (POST /orgs/{org}/rulesets target tag) y afirma que no es imprescindible si el SHA está en BD.

### P254. ¿Se fija 'main' como rama por defecto en todos los repos o se lee de repository.default_branch? Si un estudiante cambia la rama por defecto, ¿la app sigue la nueva o mantiene la original para snapshots y métricas?

- **Requisitos:** R2.3.7
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Afecta la captura de snapshots (R2.4.5) y el conteo de actividad.
- **Estudio de APIs:** §14: 'No asuman main. Léanla de repository.default_branch'.

### P255. ¿Qué metadatos y ajustes se fijan al crear cada repo: description (¿incluye nombre del estudiante/grupo y sección?), topics (curso, período, tarea) para filtrado, has_issues/has_wiki/has_projects, allow_forking, delete_branch_on_merge?

- **Requisitos:** R2.3.7, R2.3.8
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el payload de creación, la identificación de repos 'propios' y consideraciones de privacidad.
- **Estudio de APIs:** §5.4 usa description 'Tarea 1 — Juan Pérez (Sección 2)' en el ejemplo; no aborda topics ni otros ajustes.

### P256. ¿Cuál es el disparador del worker: cron cada N minutos (¿cuántos?), evento inmediato al completarse un mapeo/grupo, o ambos? ¿Se ofrece un botón 'procesar ahora' sin violar 'sin interacción directa de un usuario'? ¿Cuál es el criterio de aceptación de latencia (p. ej., repo creado ≤ X min tras completarse la información) y de tiempo total para 60 repos?

- **Requisitos:** R2.3.10
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el criterio de aceptación de R2.3.10 y la frecuencia necesaria para una demo en vivo.
- **Estudio de APIs:** §5.5 propone cron cada 2 min; §2.4 throttle ~1 repo cada 3-5 s por límites secundarios (80 content-creating req/min, 900 pts/min); §12 lista provision_repos cada 2 min.

### P257. Para un grupo con mapeo parcial de integrantes, ¿se espera a que todos estén mapeados para crear el repo ('toda la información requerida') o se crea con los disponibles y se agregan los demás progresivamente? ¿Y si un integrante tiene un login inválido permanentemente?

- **Requisitos:** R2.3.10, R2.3.9
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la precondición del sujeto 'grupo' en el worker y si un solo estudiante puede bloquear a su grupo.
- **Opciones planteadas:**
  - Esperar a todos los integrantes
  - Crear con los disponibles y agregar el resto después
  - Crear tras un plazo aunque falten integrantes
- **Estudio de APIs:** §5.5: '¿tiene(n) github_login mapeado? no → PENDING_MAPPING' (implica esperar a todos); §5.6 muestra 'Grupo 12: 2/3 mapeados' como pendiente.

### P258. ¿Cuál es la política de reintentos: backoff (base, máximo), número máximo de intentos, y clasificación de errores en transitorios (5xx, rate limit, timeout) vs permanentes (404 usuario no existe, 403 permisos, 422 validación)? Tras agotar reintentos, ¿queda en ERROR hasta un reintento manual?

- **Requisitos:** R2.3.10, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define transiciones ERROR→QUEUED, evita martillar la API y determina qué ve el profesor.
- **Estudio de APIs:** §5.5: 'cualquier excepción → ERROR, reintento con backoff' sin parámetros; §2.4 da un ejemplo con 5 intentos y retry-after.

### P259. ¿Cómo se garantiza idempotencia y recuperación si el worker cae a mitad (repo creado sin colaboradores, colaboradores sin notificación)? ¿La máquina de estados persiste por paso? ¿Hay lock por sujeto con TTL? ¿Puede haber varias instancias del worker o dos docentes editando la misma tarea concurrentemente?

- **Requisitos:** R2.3.10, R2.3.7, R2.3.9
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Evita repos duplicados, estados inconsistentes y notificaciones repetidas; es pregunta probable en la validación del 7-oct.
- **Estudio de APIs:** §5.5: 'idempotente, con lock por sujeto', 422 como éxito, estados CREATING/CREATED/COLLABORATORS_PENDING/READY; §14 lo lista como pregunta probable.

### P260. Dado que varios cursos/tareas comparten la misma instalación de la GitHub App, ¿existe una cola global con throttle por instalación? ¿En qué orden se procesan los sujetos (FIFO por completitud de información, por tarea, por sección, por prioridad de fecha de cierre)?

- **Requisitos:** R2.3.10
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el diseño de la cola y qué repos aparecen primero en la demo y en producción.
- **Estudio de APIs:** §2.4: límites secundarios por instalación; §5.5 describe el worker por Assignment sin definir orden global.

### P261. ¿Se puede pausar, reanudar o cancelar el aprovisionamiento de una tarea? ¿Quién puede hacerlo (profesor, ayudante con permiso repo.provision)? ¿Un repo en CREATING puede cancelarse?

- **Requisitos:** R2.3.10, R2.3.11, R2.1.8
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define controles operativos y su vínculo con los permisos de R2.1.8.
- **Estudio de APIs:** §3.4 propone permiso repo.provision ('disparar/reintentar creación'); no aborda pausar/cancelar.

### P262. ¿Se puede eliminar desde la app un repo creado por error (mapeo equivocado, prueba)? ¿Solo si no tiene commits, con confirmación, y liberando el nombre para recrear? ¿O la app nunca borra, solo desvincula/archiva y el borrado se hace en GitHub?

- **Requisitos:** R2.3.7, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si la App necesita permiso de borrado y las salvaguardas contra pérdida de trabajo de estudiantes.
- **Estudio de APIs:** §3.3 usa DELETE /repos solo para el repo temporal de verificación; no aborda borrado de repos de estudiantes.

### P263. Al cerrar la tarea o el curso, ¿se archivan los repos (read-only) automáticamente tras N días de la última entrega, manualmente, o nunca? ¿Se revoca el push de los estudiantes? Si se elimina la tarea en la app, ¿qué pasa con repos, snapshots y notificaciones pendientes?

- **Requisitos:** R2.3.7, R2.3.9, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el estado terminal ARCHIVED y el ciclo de vida completo de la tarea.
- **Estudio de APIs:** No lo aborda.

### P264. ¿Cuál es la máquina de estados definitiva por repositorio (y sub-estado por integrante)? ¿Se adoptan los estados del estudio (PENDING_MAPPING, QUEUED, CREATING, CREATED, COLLABORATORS_PENDING, READY, ERROR) y se agregan PENDING_GROUP, NOTIFIED, ARCHIVED, ORPHANED, MEMBERSHIP_CHANGED, INVITATION_EXPIRED/REJECTED? ¿Cuáles son terminales?

- **Requisitos:** R2.3.11, R2.5.5
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Es el contrato entre worker, vista de estado, dashboard (R2.5.5) e informe diario (R2.6.2).
- **Estudio de APIs:** §5.2 y §5.5 proponen la lista de estados base; §5.6 muestra estados 'Listo / Falta usuario / Invitación sin aceptar / Error: usuario inválido'.

### P265. ¿Cómo se redactan los mensajes de error: en español, con acción sugerida por tipo de error, incluyendo o no el texto crudo de GitHub/Canvas? ¿Se mantiene una bitácora de intentos por repo (timestamp, paso, error) visible para el equipo docente?

- **Requisitos:** R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la usabilidad evaluada en la parcial y el nivel de trazabilidad para la validación individual.
- **Estudio de APIs:** §5.2 guarda last_error; §5.6 muestra mensajes tipo 'Falta usuario de M. Soto'; no define bitácora.

### P266. En la vista de estado: ¿qué filtros (solo problemas, sección, estado, grupo), búsqueda, contadores resumen (X/N listos), ordenación y acciones masivas ('reintentar fallidos', 'reenviar invitaciones') existen? ¿Se refresca automáticamente? ¿Es el mismo componente que sirve a R2.2.6 y R2.5.5?

- **Requisitos:** R2.3.11, R2.2.6, R2.5.5
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el flujo de UI concreto que se demuestra el 16-sep y evita tres vistas inconsistentes.
- **Estudio de APIs:** §5.6 propone tabla con columnas Estudiante/Sección/GitHub user/Repo/Colaboradores/Estado/Acción, filtro 'solo problemas' y 'reintentar todos los fallidos'.

### P267. ¿Por qué canal de Canvas se informa el repo al estudiante: comentario en la entrega (¿de cuál entrega si hay varias?), mensaje directo (Conversation), anuncio, o varios? Para grupos, ¿una conversación grupal o mensajes individuales, y comment[group_comment]=true?

- **Requisitos:** R2.3.12, R2.6.5
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el endpoint, el permiso del token y cómo el estudiante encuentra la información.
- **Opciones planteadas:**
  - Solo comentario en la entrega
  - Solo mensaje directo
  - Ambos
  - Anuncio general + mensaje individual
- **Estudio de APIs:** §5.7 recomienda usar ambos: comentario en la submission (comment[text_comment], group_comment=true) y Conversation individual (§9.3, group_conversation=false).

### P268. ¿Cuándo se envía la notificación: al crear el repo (con invitación aún pendiente), al confirmar el acceso (READY), o ambas? Si el estudiante no acepta la invitación en X días, ¿se envía recordatorio automático y cuántos?

- **Requisitos:** R2.3.12
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define los eventos que disparan el outbox y evita mensajes prematuros o ausentes.
- **Estudio de APIs:** §5.5 paso 6 notifica tras agregar colaboradores; §9.4 propone flag notify_repo_ready y reminders por outbox.

### P269. ¿Cuál es el contenido exacto del mensaje: URL del repo, instrucciones para aceptar la invitación por email/GitHub, rama, fechas de entregas, contacto? ¿Es una plantilla editable por el profesor por tarea? ¿Idioma fijo español?

- **Requisitos:** R2.3.12
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija la plantilla del mensaje y si requiere UI de edición.
- **Estudio de APIs:** §5.7 y §9.3 dan textos de ejemplo ('Tu repositorio: ... revisa tu correo para aceptar la invitación'); no abordan plantillas editables.

### P270. ¿Canvas permite PUT de comment[text_comment] sobre una submission cuando el estudiante aún no ha entregado nada (crea placeholder)? ¿Aparece como 'calificado', afecta el gradebook o genera notificación al estudiante? ¿Funciona igual en assignments grupales?

- **Requisitos:** R2.3.12
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Ambas entregas
- **Por qué importa:** Si falla en submissions inexistentes, el canal 'comentario en la entrega' no sirve para R2.3.12 al inicio de la tarea.
- **Estudio de APIs:** §5.7 propone el comentario en la submission sin mencionar el caso de submission inexistente.

### P271. ¿Cómo se garantizan reintentos e idempotencia de la notificación (outbox con clave única por evento/repo/estudiante)? Si el token del profesor está expirado en la madrugada, ¿se reintenta? ¿Se re-notifica al recrear/renombrar un repo o al corregir un mapeo?

- **Requisitos:** R2.3.12, R2.6.7
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Evita mensajes duplicados o perdidos y define qué eventos generan comunicación.
- **Estudio de APIs:** §9.4 propone notification_outbox con constraint único (kind, target, delivery_id) y worker; §1.1 destaca guardar refresh_token.

### P272. El toggle por tarea para desactivar comunicaciones automáticas (R2.6.7), ¿aplica también a la notificación de creación de repo? Si el profesor la desactiva, ¿cómo se cumple R2.3.12 (¿envío manual, valor por defecto activado)?

- **Requisitos:** R2.3.12, R2.6.7
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Resuelve una tensión entre dos requisitos y fija el valor por defecto del flag.
- **Estudio de APIs:** §9.4 lista flag notify_repo_ready sin definir default ni su relación con R2.3.12.

### P273. ¿Con qué token de Canvas se envían las notificaciones al estudiante: siempre el del profesor que vinculó el curso (aparece como remitente), el de otro profesor si el primero expiró, o el del ayudante que actúa? ¿Se muestra en la UI quién figura como remitente?

- **Requisitos:** R2.3.12, R2.6.5
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina el remitente visible por el estudiante y el fallback cuando un token no está disponible.
- **Estudio de APIs:** §3.4 recomienda opción A (token del profesor para todas las escrituras) con B como fallback y mostrarlo en UI.

### P274. Si la GitHub App está instalada con 'selected repositories' en la org, ¿los repos creados por la propia App quedan automáticamente incluidos en la instalación (para webhooks, colaboradores y accesos posteriores) o hay que exigir instalación en 'all repositories' durante la vinculación?

- **Requisitos:** R2.3.7, R2.3.9
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Si no quedan incluidos, las llamadas posteriores sobre el repo fallan con 404/403 y no llegan webhooks.
- **Estudio de APIs:** No lo aborda; §3.3 solo confirma la instalación con GET /orgs/{org}/installation.

### P275. ¿Qué devuelve PUT /collaborators cuando el login mapeado ya no existe (cuenta renombrada/eliminada), es una organización, está suspendido o el usuario bloqueó a la org (404/403/422)? ¿Qué estado y mensaje muestra la app en cada caso y se revalida el login al momento de aprovisionar?

- **Requisitos:** R2.3.9, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Define los subtipos de ERROR permanente y si el worker debe re-verificar GET /users/{login} antes de invitar.
- **Estudio de APIs:** §6.1 valida type == 'User' al mapear; §5.6 muestra 'Error: usuario inválido'; no cubre cambios posteriores del login.

### P276. ¿Cada tarea de la app tiene siempre su propio conjunto de repos, o se permite que una nueva tarea reutilice el conjunto de repos de otra (p. ej., un proyecto semestral dividido en tareas por razones administrativas)?

- **Requisitos:** R2.3.4, R2.3.7
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Confirma la cardinalidad Repository→Assignment(app) 1:1 exigida por R2.3.4 o abre un caso de repos compartidos entre tareas.
- **Estudio de APIs:** §5.2 y §11 (2.3.4): 'FK a Assignment, no a Delivery' — un conjunto por tarea.

### P277. ¿Qué roles pueden crear/editar el repo base, subir archivos, forzar reintentos, reenviar invitaciones y borrar/archivar repos? ¿Los estudiantes deben poder ver el repo base (privado en la org, sin acceso) o basta con que reciban su copia?

- **Requisitos:** R2.3.5, R2.3.6, R2.3.7, R2.1.8
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Conecta los permisos de R2.1.8 con cada acción de 2.3 y fija la visibilidad del repo base.
- **Estudio de APIs:** §3.4 propone assignment.manage (crear/editar tareas y repos base) y repo.provision (disparar/reintentar); no aborda visibilidad del base para estudiantes.

### P278. ¿Qué se muestra en los estados vacíos: tarea sin estudiantes mapeados, curso sin grupos, org sin permisos suficientes (403 en la primera creación), o tarea recién creada antes del primer ciclo del worker ('próxima ejecución en N s')?

- **Requisitos:** R2.3.7, R2.3.10, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** La guía adecuada se evalúa en la parcial; los estados vacíos son donde el profesor no sabe qué hacer.
- **Estudio de APIs:** §4.4 sugiere mostrar last_synced_at; §3.3 sugiere checklist de verificación; no aborda estados vacíos de la tarea.

### P279. Al vincular un assignment como entrega, ¿la app valida su 'calificabilidad': `grading_type=not_graded` (Canvas no acepta notas), `anonymous_grading=true` (Canvas oculta identidades a los graders), `moderated_grading=true` (exige un 'final grader' y liberar notas), `peer_reviews` activado? Para cada caso: ¿bloquear la vinculación, advertir y permitir, o permitir y fallar solo al publicar en R2.7.6? ¿Se re-verifica en cada sync si el profesor cambia esos flags después de vincular y qué se muestra en la vista de corrección?

- **Requisitos:** R2.3.1, R2.7.5, R2.7.6
- **Área declarada:** 2.3 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Evita descubrir el 6-oct que la nota no se puede publicar; fija reglas de validación y mensajes al vincular y al sincronizar.
- **Opciones planteadas:**
  - Bloquear vinculación de assignments no calificables
  - Advertir en el selector y en la tarea, sin bloquear
  - Solo detectar el error al publicar
- **Estudio de APIs:** §5.1 lista campos clave (group_category_id, published, submission_types, updated_at) pero no `grading_type`, `anonymous_grading` ni `moderated_grading`; §10.4 asume PUT directo sin precondiciones.

### P280. Tras `POST /repos/{template}/generate` GitHub responde 201 pero la copia del contenido es asíncrona: durante algunos segundos el repo puede estar vacío (GET /commits → 409, `default_branch` sin refs). ¿El worker espera/poletea hasta detectar el commit inicial (con qué timeout y cuántos intentos) antes de marcar CREATED, leer `default_branch`, aplicar protecciones y registrar el 'commit base' de referencia, o continúa de inmediato y tolera 409 en pasos posteriores (snapshot, backfill)? ¿Qué estado intermedio se muestra en R2.3.11 mientras tanto?

- **Requisitos:** R2.3.7, R2.3.9, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Afecta la máquina de estados del worker, la identificación del commit inicial para métricas (R2.5) y la protección de ramas; un 409 no manejado marcaría ERROR repos válidos.
- **Opciones planteadas:**
  - Poll hasta ver el commit inicial (timeout N s) antes de CREATED
  - Marcar CREATED de inmediato y resolver default_branch/commit base en un paso posterior
  - Diferir al reconciliador de commits
- **Estudio de APIs:** §5.4 y §5.5 paso 3 guardan `default_branch` inmediatamente tras la creación; no mencionan la latencia de la copia del template.

### P281. Cuando la tarea NO tiene repo base, el repo se crea con `auto_init: true`, cuyo commit inicial es un README vacío firmado por la App. ¿Se acepta ese README vacío o la app sube un README propio (nombre de la tarea, entregas y fechas efectivas, enlace a la tarea en Canvas, instrucciones de clone/invitación) y un `.gitignore` por plantilla (`gitignore_template` según lenguaje elegido por el profesor)? ¿Ese contenido es editable por el profesor y se mantiene coherente con lo que reciben los repos generados desde un base?

- **Requisitos:** R2.3.5, R2.3.7, R2.3.12
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el contenido mínimo de un repo sin base, si existe un paso 'lenguaje/.gitignore' en el formulario de tarea y qué commit se considera 'inicial' al excluirlo de métricas.
- **Opciones planteadas:**
  - README vacío de auto_init
  - README generado por la app con datos de la tarea
  - README + .gitignore elegido por el profesor
- **Estudio de APIs:** §5.4 indica 'sin repo base: POST /orgs/{org}/repos con auto_init'; §5.3 lista `gitignore_template` como parámetro sin decidir su uso.

### P282. La Contents API crea todos los archivos con modo 100644: scripts que requieren bit de ejecución (`gradlew`, `mvnw`, `run.sh`) lo pierden, y no soporta symlinks. ¿Se declara fuera de alcance (con aviso en la UI de archivos), se usa la Git Data API (blobs/trees con modo 100755) para el repo base, o se instruye al profesor a corregirlo en GitHub? Además, ¿qué validación se aplica a las rutas subidas (`..`, barra inicial, espacios, unicode, colisión por mayúsculas `README.md` vs `readme.md`) y a los finales de línea CRLF de archivos subidos desde Windows?

- **Requisitos:** R2.3.6, R2.3.7
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** En tareas de programación un wrapper sin +x rompe el arranque para todos los estudiantes; fija la API a usar y las reglas de validación del explorador de archivos.
- **Opciones planteadas:**
  - Contents API y documentar la limitación
  - Git Data API para preservar modos
  - Editor de modo por archivo en la UI
- **Estudio de APIs:** §5.3 usa PUT /contents con base64 y menciona la Git Data API solo para archivos grandes; no aborda modos de archivo, symlinks ni validación de rutas.

### P283. ¿Cómo se rotula cada entrega en la UI, en los tags de GitHub (R2.4.6), en los mensajes a estudiantes y en el informe: con el nombre del assignment de Canvas, con una etiqueta propia editable ('Entrega parcial 1', 'Entrega final') o con un ordinal? Si el assignment se renombra en Canvas, ¿se propaga el nuevo nombre, se conserva el rótulo propio o se alerta? ¿Se fija un máximo de entregas por tarea y se exige unicidad de rótulos dentro de la tarea?

- **Requisitos:** R2.3.2, R2.4.4, R2.4.6, R2.5.6
- **Área declarada:** 2.3 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el modelo de datos de Delivery (campo de rótulo), la convención de tags y la regla de sincronización de nombres.
- **Opciones planteadas:**
  - Nombre del assignment de Canvas (sincronizado)
  - Rótulo propio editable
  - Ordinal automático + tipo (parcial/final)
- **Estudio de APIs:** §5.2 modela `kind` y `order_index` sin campo de rótulo; §7.5 usa tags `entrega-1`/`entrega-final` sin definir su origen.

### P284. Si el assignment de Canvas tiene `unlock_at` futuro o está en un módulo bloqueado por prerrequisitos, el estudiante aún no ve la tarea: ¿la app igual envía 'repositorio disponible' (comentario en la submission o Conversation) o lo retiene hasta `unlock_at`/desbloqueo? ¿Un comentario en la submission de un assignment bloqueado es visible para el estudiante en Canvas? ¿Se le da acceso al repo (invitación) antes de que la tarea sea visible?

- **Requisitos:** R2.3.12, R2.4.1, R2.6.7
- **Área declarada:** 2.3 / 2.4
- **Tipo:** Verificar empíricamente · **Entrega:** Ambas entregas
- **Por qué importa:** Define el momento del envío de R2.3.12 respecto a la visibilidad en Canvas y evita mensajes que apuntan a una tarea que el estudiante no puede abrir.
- **Opciones planteadas:**
  - Notificar al crear el repo sin importar unlock_at
  - Retener comunicación hasta unlock_at
  - Retener también la invitación de GitHub
- **Estudio de APIs:** §5.1 dice 'no creen repos para tareas no publicadas' (published) pero no trata `unlock_at` ni módulos bloqueados; §5.7 notifica al crear el repo.

### P285. La invitación de colaborador que recibe el estudiante llega desde GitHub en inglés y con remitente '<nombre-de-la-app>[bot]' (no el profesor), y lo mismo aparece en el audit log del repo. ¿Se eligen nombre, avatar y descripción pública de la GitHub App pensando en que los estudiantes los verán (p. ej. 'ICC4201 Repos'), y el mensaje de Canvas anticipa exactamente qué correo recibirán y de quién para que no lo tomen por phishing? ¿Se verifica con una cuenta de prueba el texto real del correo de invitación?

- **Requisitos:** R2.3.9, R2.3.12, R2.1.5
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija el naming/branding de la App y el contenido del mensaje de R2.3.12; afecta la tasa de aceptación de invitaciones.
- **Estudio de APIs:** §5.4 describe el 201 (invitación) y que el estudiante 'debe aceptar la invitación por email'; no aborda cómo se ve ese correo ni el nombre de la App.

### P286. Si una tarea de Canvas vinculada cambia de individual a grupal (o viceversa) después de creados los repos, o el profesor intenta vincular una nueva entrega con configuración distinta: ¿la app bloquea la sincronización de esa entrega y marca la tarea 'inconsistente' con notificación, o adopta la nueva configuración y qué hace con los repos existentes? ¿Puede el profesor desvincular la entrega conflictiva desde la app?

- **Requisitos:** R2.3.3, R2.3.4, R2.4.4
- **Área declarada:** 2.3 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El enunciado exige configuración uniforme entre entregas pero no dice qué hacer si Canvas la rompe después; define un estado de error de tarea y su flujo de resolución.
- **Opciones planteadas:**
  - Congelar la configuración de la tarea al crear el primer repo e ignorar el cambio con alerta
  - Marcar tarea 'inconsistente', pausar workers, exigir decisión
  - Adoptar el cambio y archivar/recrear repos
- **Estudio de APIs:** §5.2 propone rechazar al vincular una segunda entrega con group_category_id distinto. No cubre el cambio posterior en Canvas.

### P287. Si una tarea de Canvas vinculada como entrega es eliminada o despublicada, o el curso de Canvas concluye (workflow_state completed / fin de término): ¿la entrega se marca 'huérfana', se elimina de la tarea, o se congela con sus snapshots? ¿Se detienen el snapshot pendiente, el dashboard, las notificaciones y el informe diario? ¿Qué ve el corrector que la tenía asignada? ¿Cómo se entera el profesor?

- **Requisitos:** R2.3.1, R2.4.4, R2.4.5, R2.6.1, R2.7.2
- **Área declarada:** 2.3 / 2.4 / 2.6 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina los estados terminales de entrega y curso, cuándo dejan de correr los cron jobs y qué se conserva como histórico.
- **Estudio de APIs:** §5.1 solo dice 'no creen repos para tareas no publicadas'. No aborda eliminación de assignment ni conclusión del curso.

### P288. Si al crear la tarea en la app (o al agregar una entrega) la fecha efectiva de esa entrega ya pasó: ¿se captura el snapshot de inmediato para los repos existentes? ¿Y para los repos que se creen después (todo su trabajo sería posterior al cierre)? ¿Se suprimen las notificaciones de 'próximo a vencer' y 'repo disponible'? ¿Se advierte al profesor antes de confirmar la vinculación?

- **Requisitos:** R2.3.1, R2.4.5, R2.6.7
- **Área declarada:** 2.3 / 2.4 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define validaciones del wizard de tarea y guardas del outbox de notificaciones para no mandar mensajes absurdos.
- **Estudio de APIs:** §7.5: el job barre todo lo vencido no capturado (implica captura inmediata). No aborda la advertencia en UI ni las notificaciones.

### P289. Las entregas se identifican como parciales y final: si tras un cambio de fechas en Canvas la 'final' queda antes de una 'parcial', o dos entregas quedan con la misma fecha, ¿el orden y el tipo los fija el profesor manualmente y la app solo alerta la inconsistencia, o se reordena automáticamente por fecha? ¿Cómo afecta esto a los 'períodos' de actividad de R2.5.7, que se definen entre entregas consecutivas?

- **Requisitos:** R2.3.2, R2.4.4, R2.5.7
- **Área declarada:** 2.3 / 2.4 / 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** El orden de entregas alimenta nombres de tags, períodos del dashboard y navegación del corrector; debe ser determinista.
- **Estudio de APIs:** §5.2 modela kind y order_index como campos manuales. No aborda reordenamiento por cambio de fechas.

### P290. Si el repo de un estudiante es eliminado, renombrado, transferido o archivado directamente en GitHub (por un owner de la org o por error): ¿la app lo detecta (webhook repository o 404 en reconciliación) y qué hace: marcar ERROR y esperar decisión, recrearlo automáticamente (perdiendo historia), o seguir el rename actualizando full_name? ¿Los snapshots ya capturados se marcan como irrecuperables?

- **Requisitos:** R2.3.4, R2.3.11, R2.4.7, R2.5.5
- **Área declarada:** 2.3 / 2.4 / 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El worker idempotente de §5.5 recrearía el repo silenciosamente; hay que decidir si eso es deseable y cómo se muestra al docente.
- **Estudio de APIs:** §8.1 lista el evento repository entre los webhooks a suscribir. No define comportamiento ante deleted/renamed/transferred.

### P291. Si el trabajo del estudiante está en una rama distinta a la por defecto al momento del cierre: ¿el snapshot se toma solo de la rama por defecto (y el corrector ve un repo casi vacío), de la rama con el último commit, o se registran todas las ramas? ¿La actividad del dashboard y el timeline consideran todas las ramas o solo la por defecto? ¿Esta regla se comunica al estudiante en el mensaje de disponibilidad del repo?

- **Requisitos:** R2.3.12, R2.4.5, R2.5.2, R2.5.10
- **Área declarada:** 2.3 / 2.4 / 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia la consulta de commits, la ingesta de webhooks (filtrar ref o no) y el texto de las comunicaciones automáticas.
- **Estudio de APIs:** §7.5 usa sha={default_branch}; §8.1 sugiere filtrar por rama por defecto 'si quieren'. No fija una regla.

### P292. Cuando el worker recibe 422 'name already exists' al crear un repo, el estudio propone adoptarlo como éxito. ¿Bajo qué condiciones es seguro adoptarlo (creado por la app en un intento previo, marcado con topic/descripción de la app, sin colaboradores ajenos, vacío) y cuándo debe marcarse ERROR para revisión (repo creado a mano, de otro curso, con contenido)? ¿Se ofrece al profesor la acción manual 'vincular repo existente'?

- **Requisitos:** R2.3.7, R2.3.8, R2.3.10, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Evita que la app se apropie de un repo ajeno y agregue estudiantes a él; define un marcador de propiedad y una acción manual de recuperación.
- **Opciones planteadas:**
  - Adoptar solo si tiene marcador de la app (topic/descripción) en la org vinculada
  - Adoptar siempre
  - Nunca adoptar: ERROR + acción manual 'vincular existente' o sufijo -2
- **Estudio de APIs:** §5.5: '422 name already exists → GET el repo y continuar (idempotencia)'.

### P293. Si el estudiante es removido como colaborador (o abandona la org) directamente en GitHub después de que el repo estaba READY: ¿la app reconcilia periódicamente los colaboradores y re-invita automáticamente, solo alerta al docente, o no lo detecta? ¿Con qué frecuencia y con qué costo en rate limit para 200 repos?

- **Requisitos:** R2.3.9, R2.3.11, R2.5.5
- **Área declarada:** 2.3 / 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si el estado READY es 'una vez' o 'continuo' y si hay un job adicional de reconciliación de colaboradores.
- **Estudio de APIs:** §8.1 menciona los eventos member/member_invite; no define reconciliación ni re-invitación.

### P294. Si el profesor modifica archivos del repo base (o lo agrega/cambia por otro) cuando ya se crearon algunos repos de estudiantes: ¿los repos existentes quedan con la versión antigua y los nuevos con la nueva (inconsistencia entre estudiantes), se bloquea la edición del base una vez creado el primer repo, o se propaga el cambio (commit/PR automático) a los repos existentes? ¿Se muestra en R2.3.11 con qué versión del base se creó cada repo?

- **Requisitos:** R2.3.5, R2.3.6, R2.3.7, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina la inmutabilidad del repo base tras el primer aprovisionamiento y si se registra el SHA del template usado en cada repo.
- **Estudio de APIs:** §5.3 propone repo base como template y explorador de archivos; no aborda su evolución después de crear repos.

### P295. ¿Puede el profesor agregar una entrega (nueva tarea de Canvas) a una tarea con repos ya creados, o desvincular una entrega existente? Si la entrega desvinculada ya tenía snapshots, asignaciones de corrector y notas publicadas, ¿se conservan como histórico, se ocultan o se eliminan? ¿Se pueden re-vincular después conservando lo anterior?

- **Requisitos:** R2.3.1, R2.3.2, R2.4.6, R2.7.1
- **Área declarada:** 2.3 / 2.4 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la mutabilidad de la relación tarea→entregas y el destino de los datos derivados (snapshots, tags en GitHub, asignaciones).
- **Estudio de APIs:** §5.2 valida consistencia al vincular; no aborda desvincular ni agregar después de iniciada la tarea.

### P296. GitHub limita la cantidad de invitaciones de colaborador que un repositorio/organización puede emitir por período (y las invitaciones a la org para orgs nuevas). ¿Cuáles son los límites vigentes y qué hace la app al alcanzarlos con un curso de 200 estudiantes: pausar y reprogramar, marcar los repos como 'invitación diferida' en R2.3.11, o invitar previamente a la org? Investigar en la documentación de GitHub y probar con la org real.

- **Requisitos:** R2.3.9, R2.3.10, R2.3.11
- **Área declarada:** 2.3 (escala)
- **Tipo:** Investigable en docs · **Entrega:** Ambas entregas
- **Por qué importa:** Un límite de invitaciones detiene el aprovisionamiento masivo en la demo; la spec necesita un estado y una política de espera.
- **Estudio de APIs:** No lo aborda (§2.4 cubre rate limits de API, no límites de invitaciones).

### P297. Dos profesores editan la misma tarea (uno cambia el repo base, otro agrega una entrega) o uno edita mientras el worker está creando repos: ¿se usa bloqueo optimista con aviso 'la tarea cambió, recarga', último en guardar gana, o se bloquea la edición mientras hay jobs en curso? ¿Qué campos son inmutables una vez creado el primer repo (plantilla de nombre, tipo individual/grupal, repo base, org)?

- **Requisitos:** R2.1.7, R2.3.1, R2.3.5, R2.3.7, R2.3.8
- **Área declarada:** 2.3 (concurrencia)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define control de concurrencia en la edición y la lista de campos congelados, evitando repos con configuraciones mezcladas.
- **Estudio de APIs:** No lo aborda.

### P298. ¿El nombre del repo incluye datos humanos (nombre del estudiante o del grupo con tildes, ñ, emoji, vacío) o solo identificadores estables (login de GitHub, canvas_user_id, canvas_group_id, código de tarea)? Si incluye nombres: ¿qué pasa con dos grupos llamados igual, un grupo renombrado luego, un nombre que sanitizado queda vacío, o un truncado a 100 caracteres que colisiona? ¿El nombre es inmutable aunque cambie el dato de origen?

- **Requisitos:** R2.2.3, R2.3.8
- **Área declarada:** 2.3 (datos sucios)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** R2.3.8 exige nombres inequívocos; la plantilla y las reglas de sanitización/colisión deben quedar fijadas como regla de negocio verificable.
- **Estudio de APIs:** §5.4 propone {curso}-{periodo}-{tarea}-{login} y -g{canvas_group_id}-{slug}, sanitización y sufijo -2 ante colisión; es propuesta no aprobada.

### P299. ¿Cuál es el tiempo máximo aceptable desde que un estudiante completa su mapeo hasta que su repo está listo y notificado, y para un curso completo de 200 estudiantes o 60 grupos (a 3–5 s por repo son 10–17 minutos)? ¿Las tablas de estado y el dashboard deben paginar, filtrar por sección/estado y exportar (CSV)? ¿Qué muestra la UI durante la creación masiva (progreso N/M, tiempo estimado, actualización automática)?

- **Requisitos:** R2.3.10, R2.3.11, R2.5.1, R2.5.5
- **Área declarada:** 2.3 / 2.5 (escala)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Convierte 'progresivo y automático' en criterios de aceptación medibles y define requisitos de UI para volúmenes reales.
- **Estudio de APIs:** §2.4 y §5.5: throttle de ~1 repo cada 3–5 s por límites de GitHub; §5.6 tabla con filtro 'solo problemas'. No fija tiempos objetivo ni paginación.

### P300. Para repos en ERROR (login inválido, 403 de permisos, rate limit, fallo de red): ¿cuántos reintentos automáticos, con qué backoff, y cuándo pasa a 'requiere intervención humana'? ¿Qué acciones manuales existen (reintentar, editar login y reintentar, vincular repo existente, marcar 'gestionado fuera de la app', omitir estudiante) y quién puede ejecutarlas? ¿Los errores se clasifican en 'transitorio' vs 'definitivo' en R2.3.11 y en el informe diario?

- **Requisitos:** R2.3.10, R2.3.11, R2.5.5, R2.6.2
- **Área declarada:** 2.3 / 2.5 / 2.6 (recuperación)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Convierte el estado ERROR en una taxonomía con reglas de transición y acciones, verificable en la demo con el caso problemático que sugiere el estudio.
- **Estudio de APIs:** §5.5 'reintento con backoff' y §5.6 botón 'reintentar todos los fallidos'; no cuantifica reintentos ni clasifica errores.

### P301. Si al enviar un mensaje o comentario de Canvas (repo disponible, recordatorio) o al publicar una nota, el estudiante ya no está inscrito, Canvas responde error o el throttling lo bloquea: ¿se reintenta (cuántas veces), se descarta, se marca en el historial de comunicaciones y se alerta al docente? ¿Se evita reenviar 'repo disponible' cuando el repo se re-crea, se re-invita o se corrige el mapeo?

- **Requisitos:** R2.3.12, R2.6.5, R2.6.7, R2.7.6
- **Área declarada:** 2.3 / 2.6 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la política de reintentos del outbox y las claves de deduplicación por evento para no spamear a los estudiantes.
- **Estudio de APIs:** §9.4 outbox con constraint único (kind, target, delivery_id) y reintentos; no define política ante destinatario inválido ni eventos repetidos por re-creación.

### P302. ¿Los archivos iniciales del repo base se suben pasando directo a GitHub (sin almacenamiento propio, filesystem del PaaS efímero) o se guardan temporalmente? ¿Límite de tamaño por archivo (Contents API cómoda ≤1 MB; límite de body multipart del hosting), tipos permitidos (binarios en base64), cantidad de archivos, soporte de carpetas/.zip? Si falla a mitad de la subida en serie, ¿qué estado muestra la UI y cómo se reanuda?

- **Requisitos:** R2.3.6, R2.3.5
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define límites explícitos y mensajes de error para R2.3.6; el filesystem efímero descarta guardar archivos en disco local.
- **Estudio de APIs:** §5.3 límites de Contents API (≤1 MB, 1–100 MB solo raw, >100 MB no), 'suban archivos en serie'.

### P303. ¿Qué intervalos reales tendrán los crons en producción (aprovisionamiento 2 min, snapshots 5 min, sync Canvas 10 min, reconciliación 15 min) y cuáles durante la demo del 16-sep (¿se acortan a 30 s por variable de entorno para que el profesor vea el repo aparecer 'solo'?)? ¿Se permite un botón 'ejecutar ahora' de respaldo aunque R2.3.10 exija automatismo, y cómo se presenta para que no parezca que el proceso depende de un clic?

- **Requisitos:** R2.3.10, R2.4.4, R2.2.5
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** La demo debe mostrar creación automática en tiempo razonable; los intervalos son parámetros del spec y del guion de demo, y afectan rate limits.
- **Estudio de APIs:** §12 intervalos sugeridos (2/5/10/15 min, 07:00); §13 guion 'el worker crea los repos en vivo'.

### P304. El párrafo de 2.3 exige que 'la creación de estos repositorios no deberá depender de una acción realizada por los estudiantes', pero la estrategia de enrolamiento recomendada exige que cada estudiante entregue su usuario de GitHub en una tarea de Canvas (una acción del estudiante sin la cual el repo no se crea). ¿Qué interpretación adopta el equipo y cómo la defiende ante el profesor el 16-sep y el 7-oct: (a) 'acción' se refiere al disparador de la creación (el estudiante solo aporta un dato; el worker crea sin que nadie pulse nada), (b) debe existir además un camino sin acción del estudiante (mapeo precargado por el docente vía CSV o reutilizado de un curso anterior) para que la creación nunca dependa del estudiante, (c) otra? ¿Se escribe esa interpretación como regla explícita en el spec?

- **Requisitos:** R2.3.10, R2.2.4, R2.2.5, R2.3.7
- **Área declarada:** 2.3 / 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define si el CSV/mapeo manual es un 'escape hatch' opcional o un requisito obligatorio para cumplir 2.3.10, y prepara la respuesta a una objeción muy probable del evaluador durante la demo.
- **Opciones planteadas:**
  - Interpretar 'acción' como disparador: el estudiante aporta un dato, no crea nada
  - Exigir camino alternativo sin estudiante (CSV / mapeo previo / carga docente) como requisito, no como extra
  - Combinación con texto explícito en el spec y en la guía de defensa
- **Estudio de APIs:** §6.1 recomienda la tarea de Canvas como formulario y §5.5 el worker automático; no aborda la tensión con el párrafo de 2.3 del enunciado.

### P305. Si la tarea de Canvas vinculada tiene calificación anónima (anonymous_grading), calificación moderada (moderated_grading, con calificaciones provisionales y un calificador final) o revisión entre pares (peer_reviews), ¿qué hace la app: bloquea la vinculación, advierte y continúa, u opera igual? Verificar contra Canvas si PUT .../submissions/:user_id con posted_grade funciona en una tarea moderada (o crea solo una nota provisional) y qué exponen los endpoints de submissions cuando la calificación es anónima (ids anonimizados). ¿Se muestran esos flags en el selector de tareas al crear la tarea?

- **Requisitos:** R2.3.1, R2.7.5, R2.7.6, R2.7.7
- **Área declarada:** 2.3 / 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** La publicación de notas (2.7.6) y el estado de corrección (2.7.7) pueden fallar silenciosamente o violar la intención del profesor (mostrar nombres en una tarea anónima).
- **Opciones planteadas:**
  - Bloquear vinculación con mensaje
  - Advertir en el selector y en la vista de corrección
  - Operar igual sin detección
- **Estudio de APIs:** §5.1 lista peer_review entre los include[] y §10.4 documenta el PUT de notas; no aborda anonymous_grading ni moderated_grading.

### P306. Los estudiantes pueden agregar workflows de GitHub Actions a su repo y consumir los minutos de Actions de la organización (limitados en repos privados con plan Free). ¿La app deshabilita Actions al crear cada repo (PUT /repos/{o}/{r}/actions/permissions enabled=false), lo deja habilitado, lo delega a la configuración de la org, o lo hace configurable por tarea (algunos profesores quieren CI)? Si queda habilitado, ¿los commits de github-actions[bot] y los eventos de workflow se excluyen o se muestran en dashboard/timeline?

- **Requisitos:** R2.3.7, R2.3.6, R2.5.2
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Afecta el costo/límites de la org del profesor, los permisos que debe pedir la GitHub App y la limpieza de las métricas de actividad.
- **Opciones planteadas:**
  - Deshabilitar Actions por repo al crear
  - Dejar habilitado
  - Configurable por tarea
  - Delegar a la configuración de la org
- **Estudio de APIs:** §5.3 menciona el permiso Workflows solo para archivos en .github/workflows del repo base; no aborda Actions en repos de estudiantes.

### P307. ¿Los archivos del repo base admiten personalización por sujeto (placeholders como {{estudiante}}, {{grupo}}, {{seccion}}, {{fecha_entrega_1}} en README u otros archivos), lo que exigiría un commit adicional por repo tras el generate, o el contenido es idéntico para todos y solo la description del repo es personalizada? Si el README incluye fechas y Canvas las cambia, ¿queda desactualizado (documentado), se actualiza con un commit del bot, o se evita poner fechas en archivos?

- **Requisitos:** R2.3.6, R2.3.7, R2.4.4
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina el costo en requests por repo, la autoría de commits del bot en las métricas y la coherencia de la información que el estudiante ve en su repo.
- **Opciones planteadas:**
  - Sin personalización de archivos
  - Placeholders + commit adicional del bot por repo
  - README generado por la app sin fechas volátiles
- **Estudio de APIs:** §5.3 propone un template repo (contenido idéntico) y §5.4 personaliza solo la description del repo generado.

### P308. Antes de guardar una tarea, ¿la app muestra un resumen de impacto ('se crearán N repos ahora, K estudiantes quedarán pendientes de usuario GitHub, J estudiantes sin grupo, tipo individual/grupal detectado, org destino X') que el profesor deba confirmar? Si la primera sincronización del roster aún no terminó al crear la tarea, ¿qué muestra ese resumen y se advierte que los repos se crearán cuando lleguen los datos?

- **Requisitos:** R2.3.1, R2.3.3, R2.3.7, R2.3.10, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es el último punto donde el profesor puede evitar crear decenas de repos equivocados; los evaluadores de usabilidad lo notarán.
- **Opciones planteadas:**
  - Resumen de impacto con confirmación
  - Guardar directo y mostrar la tabla de estado
  - Resumen solo informativo sin confirmación
- **Estudio de APIs:** §5.2 propone validar 2.3.3 al vincular y §5.6 la tabla de estado posterior; no aborda una vista previa de impacto antes de guardar.

### P309. ¿Qué ve el estudiante desde el lado de GitHub y cómo se controla para que no lo confunda con phishing: nombre, avatar y descripción pública de la GitHub App; quién figura como 'invitador' en el correo de invitación de colaborador (¿la App, la org, un bot?); el hecho de que la invitación llega al correo asociado a su cuenta de GitHub y no al institucional; el enlace 'generated from ORG/base' en el repo; y el autor del commit inicial generado por el template. ¿El mensaje de Canvas explica exactamente eso? Verificar empíricamente con una cuenta de prueba qué correo y remitente recibe.

- **Requisitos:** R2.3.9, R2.3.12, R2.1.5
- **Área declarada:** 2.3 / 2.6
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un estudiante que ignora la invitación por desconfianza bloquea todo el flujo; el texto de 2.3.12 debe anticipar lo que verá.
- **Opciones planteadas:**
  - Configurar nombre/avatar/descripción de la App con marca del curso
  - Mensaje de Canvas que describe remitente y correo destino
  - Nada especial
- **Estudio de APIs:** §5.4 explica 201/204 y que el estudiante 'debe aceptar la invitación por email'; §5.3 usa un committer 'ICC4201 Bot'; no aborda cómo percibe el estudiante al remitente.

### P310. Si un estudiante ELIMINA su cuenta de GitHub después de haber aceptado la invitación (o GitHub la suspende), sus commits pasan a mostrarse como 'ghost' y desaparece de /collaborators. ¿La app lo detecta (404 en GET /users/{login} o por id en una revalidación periódica, ausencia en collaborators), qué estado muestra ('cuenta GitHub eliminada: pedir nuevo usuario'), vuelve a solicitar el usuario por Canvas automáticamente, y conserva la atribución histórica de sus commits por id/email? Verificar cómo aparecen esos commits en el payload y en la API.

- **Requisitos:** R2.3.9, R2.3.11, R2.5.4
- **Área declarada:** 2.3 / 2.5
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin detección el estudiante aparece como 'sin participación' o 'listo' indefinidamente y pierde acceso sin que nadie lo note.
- **Opciones planteadas:**
  - Revalidación periódica + estado específico + nueva solicitud automática
  - Solo detección al fallar una operación
  - No detectar
- **Estudio de APIs:** §8.4 cubre casos de atribución sin login; no aborda cuentas eliminadas o suspendidas tras aceptar la invitación.

### P311. R2.3.1 habla de vincular tareas 'ya creadas en Canvas'. ¿La app también permite CREAR desde ella la tarea de Canvas de una entrega (nombre, fechas, tipo none/on_paper, grupal con group set, publicada) y editar sus fechas, como conveniencia cuando el curso aún no tiene tareas? Si sí, ¿se advierte que Canvas enviará notificaciones nativas a todos los estudiantes al publicar y al cambiar fechas, y con qué token/identidad se crea? ¿Qué se muestra cuando el selector de tareas de Canvas está vacío?

- **Requisitos:** R2.3.1, R2.4.1, R2.6.6
- **Área declarada:** 2.3 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Decide el alcance de escritura en Canvas, los scopes necesarios y el estado vacío del flujo de creación de tarea.
- **Opciones planteadas:**
  - Solo vincular existentes (lectura literal de R2.3.1)
  - Crear desde la app con advertencia de notificaciones nativas
  - Crear y también editar fechas/overrides
- **Estudio de APIs:** §5.1 lista POST/PUT de assignments y §6.1 crea la tarea de registro; no propone crear tareas de entrega desde la app.

### P312. ¿Se adopta el modelo de colaboradores directos por repo (recomendación del estudio) o Teams de GitHub: un team por grupo (permite ver miembros y cambiar acceso en bloque) y/o un 'team docente' con acceso de lectura a todos los repos del curso (simplifica dar y revocar acceso a ayudantes en R2.1.8/R2.1.9)? Si se usan teams, ¿los estudiantes deben ser miembros de la org (invitación adicional) y qué permisos extra de la App se requieren?

- **Requisitos:** R2.3.9, R2.1.8, R2.7.4
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia la máquina de estados de acceso, los permisos de la App y el costo en requests por grupo.
- **Opciones planteadas:**
  - Colaboradores directos (estudiantes y docentes)
  - Team docente + colaboradores directos para estudiantes
  - Team por grupo + team docente
- **Estudio de APIs:** §5.4 describe la 'Alternativa con Teams' y recomienda colaboradores directos por simplicidad.

### P313. Los errores del worker ocurren cuando nadie está mirando. ¿Dónde afloran? ¿Columna de estado en la tabla de repos, banner en la cabecera de la tarea, badge en la tarjeta de la tarea en la lista de tareas, badge en la tarjeta del curso en la home, centro de notificaciones, informe diario? ¿Un solo repo en error marca toda la tarea como 'con problemas'? ¿Los errores se pueden 'descartar/silenciar' una vez vistos?

- **Requisitos:** R2.3.10, R2.3.11, R2.5.5
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la propagación de estados hacia arriba en la jerarquía y el componente de alertas; afecta R2.3.11 ('mostrar claramente') y la evaluación de la demo con caso problemático.
- **Estudio de APIs:** §5.5 define estados ERROR/PENDING_MAPPING/COLLABORATORS_PENDING con last_error; §9.1 los incluye en el informe diario. No define la propagación visual.

### P314. ¿Cómo se comunica el progreso del aprovisionamiento automático? ¿Barra o contador en la cabecera de la tarea ('7 de 10 repositorios listos · 2 esperando usuario GitHub · 1 con error')? ¿La tabla se actualiza en vivo (polling cada N segundos, SSE o WebSocket) o hay que refrescar? ¿Se muestra 'próxima ejecución en X s' o 'procesando ahora'? ¿Cuál es la latencia máxima aceptable entre que un estudiante entrega su usuario en Canvas y el repo aparece 'Listo' en la app?

- **Requisitos:** R2.3.10, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** El enunciado exige creación automática sin interacción; la UI debe hacer visible que 'algo está pasando' sin botón. La latencia objetivo condiciona intervalos de cron y el guion de demo.
- **Opciones planteadas:**
  - Polling del frontend cada 5–10 s mientras hay repos en curso
  - SSE/WebSocket con push de cambios
  - Refresco manual con indicador de última actualización
- **Estudio de APIs:** §5.5 propone cron cada 2 min y throttle de ~1 repo cada 3 s; §13 dice 'el worker crea los repos en vivo' y 'tabla de estados pasando a verde', sin definir mecanismo de actualización de la UI.

### P315. En el flujo de crear tarea, ¿el selector de tareas de Canvas muestra para cada assignment: nombre, fecha, individual/grupal (y nombre del group set), publicada o no, y si ya está vinculada a otra tarea de la app? ¿Las incompatibles (grupal con otro group set, ya vinculada, la tarea de registro de usuario GitHub) se ocultan o se muestran deshabilitadas con la razón? ¿Se ordenan las entregas por fecha y se marca la última como 'final' por defecto, editable? ¿Qué mensaje exacto se muestra al intentar mezclar individual y grupal (R2.3.3)?

- **Requisitos:** R2.3.1, R2.3.2, R2.3.3
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la pantalla de creación de tarea de la demo (1 entrega individual) y su extensión a múltiples entregas para la final, con las validaciones visibles.
- **Estudio de APIs:** §5.1 lista los campos (group_category_id, published, due_at); §5.2 exige rechazar con mensaje claro si difiere group_category_id.

### P316. Si una tarea de Canvas vinculada es eliminada o despublicada después de crear la tarea en la app, ¿cómo se muestra (badge 'eliminada en Canvas' en la entrega, aviso en la tarea, bloqueo del snapshot)? ¿Se notifica al docente? ¿Se permite desvincular esa entrega y vincular otra assignment conservando los repos? ¿Qué pasa con snapshots ya capturados de esa entrega?

- **Requisitos:** R2.3.1, R2.4.4, R2.5.6
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Caso borde realista que define estados adicionales de 'Entrega' y acciones de recuperación en la UI.
- **Estudio de APIs:** §5.1 indica no crear repos para tareas no publicadas; §7.4 cubre cambios de fecha por polling pero no eliminación de la assignment.

### P317. ¿El profesor ve y puede ajustar el patrón de nombre de los repositorios antes de aprovisionar (con vista previa 'icc4201-2026-2-t1-jperez') o es fijo? ¿Qué componentes se usan (código de curso, período, slug de tarea, login GitHub o id de Canvas del estudiante, id/slug de grupo)? ¿Se advierte que el nombre incluirá el login del estudiante? ¿Cómo se muestran las colisiones resueltas con sufijo?

- **Requisitos:** R2.3.8
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** R2.3.8 exige nombres automáticos e inequívocos; la decisión define un campo de configuración de tarea y su vista previa, o lo elimina.
- **Opciones planteadas:**
  - Patrón fijo del sistema
  - Patrón editable por curso con vista previa
  - Patrón editable por tarea
- **Estudio de APIs:** §5.4 propone plantillas {curso}-{periodo}-{tarea}-{githublogin} y {…}-g{canvas_group_id}-{slug_grupo}, sanitización y sufijo -2 ante colisión.

### P318. ¿El repositorio base es un paso saltable del flujo de crear tarea con 'agregar después'? Si se agrega o modifica después de que ya existen repos de estudiantes, ¿se avisa que los repos ya creados no recibirán los archivos y se ofrece alguna acción? ¿La administración de archivos iniciales se hace con un explorador/editor dentro de la app, con subida de archivos (drag & drop, límite de tamaño), o solo con un enlace 'editar en GitHub'? ¿Se puede vincular un repo existente de la org como base?

- **Requisitos:** R2.3.5, R2.3.6, R2.3.7
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el alcance de la pantalla de repositorio base (potencialmente costosa) y la regla de negocio sobre cambios tardíos del base.
- **Estudio de APIs:** §5.3 recomienda repo template + explorador de archivos en la app (GET/PUT contents, textarea) + botón 'abrir en GitHub'; no aborda cambios tardíos ni vincular uno existente.

### P319. ¿Es posible 'reenviar' una invitación de colaborador de GitHub (revocar con DELETE y volver a PUT) y GitHub efectivamente reenvía el correo al estudiante? ¿Cuánto tarda en expirar una invitación y qué se ve en la API cuando expira? ¿El estudiante puede aceptar desde la UI de GitHub sin el correo (github.com/<org>/<repo>/invitations)?

- **Requisitos:** R2.3.9, R2.3.11
- **Área declarada:** 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define si el botón 'Reenviar invitación' de la tabla de estados es viable, su texto y qué instrucción alternativa se da al estudiante.
- **Estudio de APIs:** §5.4 documenta GET/PATCH/DELETE invitations y sugiere DELETE como forma de 'reenviar'; §5.6 propone acción 'Reenviar' en la tabla.

### P320. ¿Cómo se modela el 'sujeto' de una tarea (estudiante o grupo) al que apuntan Repository, DeliverySnapshot, GradingAssignment y NotificationOutbox: (a) entidad Subject polimórfica única (subject_id, kind, canvas_user_id | canvas_group_id); (b) dos FKs nullable en cada tabla con CHECK de exclusión; (c) toda tarea individual se representa como 'grupo de uno' para unificar el código? Además: ¿se crean filas Repository para TODOS los sujetos al crear la tarea (estado PENDING_*) y se recalculan en cada sync (alta → nueva fila, baja → marcar), o solo cuando la información está completa? ¿Puede un mismo sujeto tener más de una fila Repository en la misma tarea (histórica SUPERSEDED tras corregir un mapeo + vigente) y cuál es entonces la clave única? ¿Puede una tarea mezclar owner_kind (repo individual para quien no tiene grupo)?

- **Requisitos:** R2.3.4, R2.3.7, R2.3.10, R2.3.11, R2.4.5, R2.7.1
- **Área declarada:** 2.3 / transversal (modelo de datos)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija las claves únicas, los índices y la forma de todas las consultas del worker, del dashboard y de la corrección; decide si R2.3.11 puede listar pendientes antes de que exista información y si es posible sustituir un repo sin perder snapshots.
- **Opciones planteadas:**
  - Subject polimórfico
  - Dos FKs nullable + CHECK
  - Grupo de uno para individuales
  - Filas eager para todos los sujetos
  - Filas lazy solo con información completa
- **Estudio de APIs:** §5.2 propone Repository con owner_kind y dos columnas canvas_user_id | canvas_group_id; §5.5 crea filas PENDING_MAPPING para sujetos sin login. No aborda filas históricas ni mezcla de owner_kind.

### P321. ¿El worker de repositorios se diseña como reconciliador DECLARATIVO (en cada ciclo calcula el estado deseado por sujeto —repo existe, colaboradores = integrantes activos mapeados con permiso push, ayudantes con acceso de lectura— lo compara con el observado en GitHub y aplica la diferencia) o como acciones IMPERATIVAS disparadas por eventos (mapeo completado → agregar; integrante sale → quitar)? ¿Repository.state es una columna escrita por el worker o una vista derivada de RepositoryMember + existencia del repo? ¿Qué diferencias entre deseado y observado se aplican automáticamente y cuáles quedan como 'drift detectado, requiere confirmación' (p. ej. quitar colaboradores, colaborador agregado a mano por un owner de la org)?

- **Requisitos:** R2.3.9, R2.3.10, R2.3.11, R2.2.3, R2.1.9
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la arquitectura completa del worker, su idempotencia, la reacción a cambios de grupo/retiros y el costo en rate limit por ciclo; cambia qué se persiste y qué se recalcula.
- **Opciones planteadas:**
  - Reconciliador declarativo
  - Acciones imperativas por evento
  - Híbrido: imperativo para crear, declarativo para colaboradores
- **Estudio de APIs:** §5.5 describe crear_repo imperativo con estados escritos por el worker; §8.2 aplica reconciliación pero solo a commits.

### P322. ¿Existe una entidad RepositoryMember (repository_id, student_id, github_login y github_id en el momento, permission, state: TO_INVITE / INVITED / ACCEPTED / REMOVED / FAILED, invitation_id de GitHub, invited_at, accepted_at, removed_at, removal_reason) con historial de altas y bajas, o el estado de colaboradores se consulta a GitHub en cada reconciliación sin persistirlo? ¿Se guarda invitation_id para revocar/reenviar y detectar expiración o rechazo? ¿La fila se conserva como REMOVED al quitar a un retirado para saber quién tuvo acceso y cuándo? ¿La aceptación de una invitación en un repo eleva el estado del mapeo estudiante↔GitHub a VERIFICADO para todo el curso?

- **Requisitos:** R2.3.9, R2.3.11, R2.2.6, R2.1.9, R2.2.4
- **Área declarada:** 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Sin esta entidad no hay sub-estado por integrante en R2.3.11 ni evidencia de accesos; con ella hay que definir su fuente de verdad frente a GitHub.
- **Opciones planteadas:**
  - Entidad persistida con historial
  - Consulta en vivo a GitHub sin persistir
  - Persistir solo el estado vigente sin historial
- **Estudio de APIs:** §5.4 documenta GET /invitations (id, invitee, expired) y DELETE; §5.2 no tiene entidad de miembro, solo estado agregado del repo.

### P323. Además de las fechas, ¿qué campos del assignment de Canvas se copian a Delivery (name, published, workflow_state, group_category_id, grade_group_students_individually, only_visible_to_overrides, points_possible, grading_type, submission_types, rubric y rubric_settings, updated_at, html_url) y para cuáles se conserva historial de versiones (DeliveryRevision) en vez de solo el valor vigente? ¿Se guarda el JSON crudo de cada objeto Canvas sincronizado (assignment, override, enrollment, group) junto a las columnas normalizadas para depurar y recalcular sin volver a llamar a la API? ¿Qué cambio de campo dispara qué reacción (alerta / bloqueo / recálculo)?

- **Requisitos:** R2.3.1, R2.3.3, R2.4.4, R2.7.5, R2.7.6
- **Área declarada:** 2.3 / 2.4 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija la tabla Delivery y la matriz de detección de drift; sin historial no se puede explicar por qué una nota o un snapshot se hicieron con una configuración anterior.
- **Opciones planteadas:**
  - Copiar campos clave sin historial
  - Versionar Delivery completa
  - Guardar JSON crudo + columnas normalizadas
- **Estudio de APIs:** §5.1 lista 'campos que deciden todo tu modelo'; §7.4 solo versiona fechas en el log de auditoría.

### P324. ¿La Tarea (app) tiene una columna de estado explícita (DRAFT sin entregas → ACTIVE → CLOSED → ARCHIVED, más PAUSED) que los workers usan como filtro, o 'activa' se deriva por predicado (tiene alguna entrega con fecha efectiva futura o dentro de N días de corrección)? ¿Qué transiciones son automáticas por fechas y cuáles manuales? ¿Qué worker (aprovisionamiento, snapshots, ingesta de commits, recordatorios, informe diario) consulta qué estados? Un estado derivado no puede pausarse; uno manual puede quedar obsoleto: ¿cuál se elige o cómo se combinan?

- **Requisitos:** R2.3.10, R2.5.6, R2.6.1, R2.6.7
- **Área declarada:** 2.3 / 2.5 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Es el filtro común de todos los crons; decide si existe 'pausar tarea' (R2.3.10 sin intervención) y cuándo deja de generarse informe (R2.6.1).
- **Opciones planteadas:**
  - Columna de estado manual
  - Estado derivado por fechas
  - Derivado + flag manual de pausa/archivo
- **Estudio de APIs:** §5.5 'para cada Assignment activo' y §9.1 'tareas activas' sin definir el campo ni las transiciones.

---

## 2.4

### P325. Un AssignmentOverride puede tener `group_id` apuntando a una etiqueta de diferenciación (grupo no colaborativo) usada para 'asignar a' un subconjunto de estudiantes en una tarea INDIVIDUAL. El algoritmo propuesto solo evalúa overrides de grupo cuando la tarea es grupal (paso 2 condicionado a `student_group_id`), de modo que esas fechas se perderían. ¿La app resuelve la pertenencia del estudiante a cualquier grupo (colaborativo o no) referenciado por un override, con qué precedencia respecto a sección y ADHOC, y cómo se rotula ese origen en la UI ('etiqueta X')?

- **Requisitos:** R2.4.3, R2.4.1, R2.4.2
- **Área declarada:** 2.4
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin esto, extensiones dadas vía etiquetas se ignoran y el snapshot se captura con la fecha equivocada (R2.4.5) para tareas individuales.
- **Opciones planteadas:**
  - Resolver pertenencia a todo grupo referenciado por override, independiente del tipo de tarea
  - Ignorar overrides de grupo en tareas individuales y alertar al docente
  - Tratar la etiqueta como equivalente a ADHOC para sus miembros
- **Estudio de APIs:** §7.3 paso 2 aplica overrides de grupo solo si `student_group_id` existe (tareas grupales); §7.1 lista `group_id` sin distinguir tipos de grupo.

### P326. GitHub rechaza escrituras (incluida la creación de tags vía POST /git/refs) en repositorios archivados. Si el equipo decide archivar repos al cerrar la tarea o el curso, ¿en qué momento se archiva respecto al último snapshot, a recapturas por cambios de fecha y a snapshots manuales? Si un owner archiva un repo a mano antes del cierre, ¿el job registra solo el SHA en BD y marca 'tag no creado (repo archivado)', desarchiva temporalmente vía PATCH, o pasa el snapshot a ERROR?

- **Requisitos:** R2.4.5, R2.4.7, R2.3.7
- **Área declarada:** 2.4
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita que el archivado (propuesto para proteger evidencia) impida registrar la versión de cierre; define un sub-estado del snapshot.
- **Opciones planteadas:**
  - Archivar solo tras el último snapshot + N días
  - Registrar SHA sin tag y marcar advertencia
  - Desarchivar temporalmente para crear el tag
- **Estudio de APIs:** §7.5 crea tags sin considerar repos archivados; §14 no lo menciona.

### P327. ¿Se ofrece al corrector descargar la versión exacta como zip (`GET /repos/{o}/{r}/zipball/{sha}`, servido por la app con el installation token) para revisar o ejecutar el código localmente sin necesitar acceso GitHub al repo privado? Si sí: ¿límite de tamaño, qué permiso lo habilita, se registra la descarga, y la copia se conserva como respaldo del snapshot o se genera bajo demanda?

- **Requisitos:** R2.4.8, R2.7.4, R2.1.8
- **Área declarada:** 2.4 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Resuelve el acceso de ayudantes sin cuenta GitHub en la org y añade un flujo de descarga con implicaciones de almacenamiento y auditoría.
- **Opciones planteadas:**
  - Solo enlaces a GitHub
  - Descarga zip bajo demanda
  - Zip almacenado al capturar el snapshot
- **Estudio de APIs:** §7.5 paso 4 propone solo links tree/compare/commits; §8 y §10.2 no mencionan zipball.

### P328. Cuando Canvas cambia la fecha efectiva de una entrega DESPUÉS de que la app ya capturó el snapshot (extensión otorgada tarde, corrección de un error): ¿se recaptura automáticamente con la nueva fecha, se mantiene la versión original (R2.4.7) y solo se alerta, o se conserva la original y se crea una segunda versión marcada 'recapturada'? ¿Aplica igual si la fecha se adelanta? ¿Quién aprueba la recaptura y queda registrado?

- **Requisitos:** R2.4.3, R2.4.4, R2.4.5, R2.4.7, R2.7.4
- **Área declarada:** 2.4 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.4.4 (mantener fechas actualizadas) y R2.4.7 (no alterar lo registrado) entran en tensión; la spec debe fijar precedencia y flujo de aprobación.
- **Opciones planteadas:**
  - Nunca recapturar automáticamente; alertar y permitir recaptura manual con auditoría
  - Recapturar automáticamente si la nueva fecha es posterior, conservando la versión anterior
  - Recapturar siempre y descartar la anterior
- **Estudio de APIs:** §7.4 reprograma el job de snapshot solo si la entrega 'NO fue capturada aún'. No resuelve el caso ya capturado.

### P329. ¿Qué se considera 'fecha de cierre' para capturar la versión cuando la entrega tiene due_at y además lock_at posterior (Canvas permite entregas atrasadas), cuando due_at es null (sin fecha) y cuando un override tiene due_at null? Opciones: usar due_at; usar lock_at si existe; capturar dos versiones (a tiempo y tardía); no capturar hasta que el profesor fije una fecha manual en la app.

- **Requisitos:** R2.4.1, R2.4.5, R2.5.6
- **Área declarada:** 2.4 / 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el disparador del job de snapshot y qué muestra R2.5.6 como 'fecha' y 'estado' de una entrega sin fecha.
- **Estudio de APIs:** §7.3: due_at null en override significa 'sin fecha' para ese target; §7.5 usa due_at como fecha de captura. No considera lock_at ni el caso sin fecha base.

### P330. Para un estudiante al que una entrega no aplica (only_visible_to_overrides=true sin override, o override con due_at null): ¿se le crea repo igual (la tarea puede tener otras entregas que sí le aplican)? ¿Cómo se muestra en dashboard y corrección: 'no aplica', oculto, o pendiente sin fecha? ¿Cuenta en los denominadores de R2.7.7?

- **Requisitos:** R2.4.3, R2.4.5, R2.5.6, R2.7.7
- **Área declarada:** 2.4 / 2.5 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita marcar como atrasados a estudiantes que no debían entregar y define si el repo depende de la tarea o de la entrega.
- **Estudio de APIs:** §7.3: 'la tarea no existe para él; no le creen snapshot ni lo cuenten como atrasado'. No dice si se crea repo ni cómo se muestra.

### P331. En una tarea grupal donde los integrantes tienen fechas efectivas distintas (extensión individual a uno, integrantes de secciones distintas): ¿la fecha de cierre del repo es la máxima, la mínima, la de la mayoría, o se captura un snapshot por integrante (mismo repo, distintos SHAs) para corregir a cada uno con su fecha? ¿Cómo se comunica la heterogeneidad al corrector y al estudiante?

- **Requisitos:** R2.4.3, R2.4.5, R2.4.6, R2.7.4
- **Área declarada:** 2.4 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia la cardinalidad de DeliverySnapshot (por repo vs por estudiante) y el flujo de corrección grupal.
- **Opciones planteadas:**
  - Un snapshot por repo con max() de fechas
  - Un snapshot por integrante
  - Bloquear y exigir que el profesor unifique la fecha en Canvas
- **Estudio de APIs:** §7.3 sugiere usar max() y mostrar en la UI que el repo tiene fechas heterogéneas; es una sugerencia no aprobada.

### P332. Si un estudiante hace force-push y el commit del SHA capturado deja de ser alcanzable desde ninguna rama, o borra/mueve el tag de entrega: ¿la app lo detecta y cómo lo señala al corrector? ¿Se protegen la rama por defecto y los tags (branch protection / rulesets) al crear el repo, aceptando que los estudiantes no puedan reescribir historia? ¿Se conserva una copia del código (zip/tarball) al capturar el snapshot para no depender de GitHub? Verificar empíricamente si GitHub mantiene accesible por URL un SHA huérfano.

- **Requisitos:** R2.4.5, R2.4.7, R2.4.8, R2.7.4
- **Área declarada:** 2.4 / 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.4.7 exige que la versión registrada siga siendo correcta; el SHA en BD no sirve si el código ya no es alcanzable.
- **Opciones planteadas:**
  - Rulesets: bloquear force-push y borrado de tags
  - Guardar tarball del snapshot en almacenamiento propio
  - Solo detectar y alertar (verificación periódica del SHA)
- **Estudio de APIs:** §7.5: el SHA en BD es la fuente de verdad, tag como conveniencia, ruleset de tags 'opcional'. No cubre inalcanzabilidad del commit ni copia local.

### P333. El filtro `until` del API de commits usa la fecha declarada en el commit, que un estudiante puede alterar localmente y luego hacer push después del cierre con fecha anterior. ¿La app acepta ese riesgo, usa la fecha de recepción del push (webhook / reconciliación) como criterio de cierre, o combina ambas y marca como sospechosos los commits cuyo push llegó después del cierre con fecha anterior? ¿Cómo se muestra esto al corrector? (Investigar en docs si `until` filtra por author date o committer date.)

- **Requisitos:** R2.4.5, R2.4.7
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la fuente de la 'fecha del commit' en el modelo (commit date vs pushed_at) y la robustez del snapshot ante manipulación.
- **Opciones planteadas:**
  - Confiar en committer date (simple)
  - Usar fecha de push registrada por la app (requiere ingesta continua)
  - Committer date + marcar sospechosos los recibidos después del cierre
- **Estudio de APIs:** §7.5 usa GET /commits?until= sin advertir que la fecha es controlada por el cliente git.

### P334. ¿En qué zona horaria se muestran todas las fechas (America/Santiago fija, la del navegador, o la zona del curso en Canvas) y se indica explícitamente en la UI? ¿Cómo se manejan los cambios de hora de Chile (offset -4/-3) en la hora del informe diario, en 'N días sin actividad' y en las agrupaciones diarias del dashboard (¿día UTC o día local?)? ¿Qué pasa con un cierre programado a una hora que no existe o se repite el día del cambio?

- **Requisitos:** R2.4.1, R2.5.2, R2.5.3, R2.6.1
- **Área declarada:** 2.4 / 2.5 / 2.6 (tiempos)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el criterio de agregación diaria, la programación de cron y la presentación de fechas; errores de 3 horas invalidan snapshots.
- **Estudio de APIs:** §14: guardar UTC (timestamptz) y convertir al renderizar; §9.1: cron 07:00 America/Santiago. No define zona de visualización ni agregación diaria.

### P335. Si la extensión de un estudiante en la entrega 1 cae después de la fecha de la entrega 2 (o las fechas de distintas secciones se cruzan): ¿cómo se definen los 'períodos' de actividad por entrega (R2.5.7) para ese estudiante, y puede el snapshot de la entrega 2 quedar cronológicamente antes que el de la 1? ¿Se advierte al profesor de la inconsistencia?

- **Requisitos:** R2.4.3, R2.4.6, R2.5.7
- **Área declarada:** 2.4 / 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Los períodos por entrega dejan de ser intervalos disjuntos; la spec debe definir el cálculo por estudiante/grupo o declarar el caso como inválido.
- **Estudio de APIs:** §8.5 filtra commits por [entrega_anterior.due, entrega_actual.due]; no considera solapes por extensiones.

### P336. ¿Puede el profesor forzar o recapturar manualmente el snapshot de una entrega para un repo (acuerdo con el estudiante, error de fecha) indicando un SHA o una fecha específica? Si sí, ¿se conserva la versión automática original como histórico (R2.4.7), quién queda registrado como responsable, y se notifica al corrector asignado y al estudiante?

- **Requisitos:** R2.4.5, R2.4.7, R2.4.8, R2.7.4
- **Área declarada:** 2.4 / 2.7 (recuperación)
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si existe una vía de escape manual sobre el snapshot automático y cómo se preserva la trazabilidad.
- **Estudio de APIs:** No lo aborda.

### P337. ¿Qué campo de Canvas define la 'fecha de cierre' de una entrega para efectos del snapshot y de la UI: due_at, lock_at, o una combinación (por ejemplo due_at como cierre 'a tiempo' y lock_at como fin del período de atraso)? ¿Qué se hace cuando solo existe uno de los dos?

- **Requisitos:** R2.4.1, R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija el parámetro `until` de la captura, define si existe una 'ventana de atraso' entre due_at y lock_at, y qué fecha se muestra como cierre en dashboard, informes y comunicaciones. El algoritmo de fecha efectiva debe replicarse para el campo elegido, porque cada override trae due_at, lock_at y unlock_at por separado.
- **Opciones planteadas:**
  - due_at siempre (lock_at se ignora)
  - lock_at si existe, si no due_at
  - Dos versiones: una a due_at ('a tiempo') y otra a lock_at ('última aceptada')
  - Configurable por el profesor por entrega
- **Estudio de APIs:** §7.3 y §7.5 usan exclusivamente due_at (effective_due_at); §5.1 lista due_at/lock_at/unlock_at como 'fecha base (2.4.1)' sin elegir entre ellos.

### P338. Cuando a un mismo estudiante le aplican varios overrides a la vez (ADHOC + sección, o dos secciones con fechas distintas), ¿qué regla se adopta: la cadena de precedencia estricta ADHOC > grupo > sección > base propuesta en el estudio, o la semántica que aplica Canvas (la fecha más permisiva —la más tardía, siendo due_at=null la más permisiva— entre todos los overrides aplicables)? ¿Se verificará contra un caso real qué fecha le muestra Canvas al estudiante?

- **Requisitos:** R2.4.2, R2.4.3
- **Área declarada:** 2.4
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el algoritmo de fecha efectiva. Si la app calcula una fecha distinta a la que el estudiante ve en Canvas, el snapshot se toma en un instante 'incorrecto' desde la perspectiva del estudiante y la corrección se vuelve impugnable. También determina si un ADHOC más restrictivo que la sección debe ganar (cadena estricta) o perder (más permisiva).
- **Opciones planteadas:**
  - Cadena estricta ADHOC > grupo > sección > base
  - La más permisiva (tardía) entre todos los overrides aplicables; null = sin fecha
  - Consultar la fecha efectiva a Canvas por estudiante (p. ej. GET /users/:id/courses/:cid/assignments) en vez de calcularla localmente
  - Calcular localmente y contrastar con Canvas, alertando discrepancias
- **Estudio de APIs:** §7.3 propone cadena estricta ADHOC > grupo > sección > base y solo dentro de 'sección' toma la más tardía; Apéndice A.7 pide verificar el caso de dos secciones ('la más permisiva gana').

### P339. Para un estudiante inscrito en dos o más secciones, ¿cómo se modela (N:M estudiante–sección) y qué se muestra en la UI: una única fecha efectiva con su origen, todas las fechas candidatas con alerta, o se exige al profesor resolverlo? ¿Cuenta una inscripción a sección en estado inactive/completed para aplicar el override de esa sección?

- **Requisitos:** R2.4.2
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina el modelo de datos de enrollments, la lógica de fecha efectiva y un criterio de aceptación de UI para un caso que un ayudante puede pedir reproducir en la validación del 7-oct.
- **Opciones planteadas:**
  - Una fecha efectiva + etiqueta 'origen: sección X'
  - Mostrar todas las fechas candidatas y marcar el sujeto como 'fecha ambigua'
  - Considerar solo inscripciones active
  - Considerar cualquier inscripción no eliminada
- **Estudio de APIs:** §4.2 advierte N:M estudiante–sección; §7.3 paso 3 toma max() entre secciones; no trata inscripciones inactivas.

### P340. ¿Qué hace la app con una entrega cuya fecha efectiva para un sujeto es nula (assignment sin due_at, u override con due_at=null, que en Canvas significa 'sin fecha' para ese target)? ¿Se omite la captura, se permite que el profesor fije una fecha de cierre manual en la app, se usa lock_at como respaldo, o se marca 'sin cierre' y se excluye de atrasos e informes?

- **Requisitos:** R2.4.1, R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin regla, el job de captura (effective_due_at <= now()) nunca dispara y la entrega queda perpetuamente 'abierta' en dashboard, informes y corrección. Define además si la app puede tener fechas propias no provenientes de Canvas.
- **Opciones planteadas:**
  - No capturar; estado 'SIN FECHA' visible y excluido de atrasos
  - Permitir fecha de cierre manual en la app (marcada como no-Canvas)
  - Usar lock_at como respaldo; si tampoco existe, 'SIN FECHA'
  - Capturar solo manualmente cuando el profesor lo indique
- **Estudio de APIs:** §7.3 indica que due_at:null en un override significa 'sin fecha de entrega' para ese target, sin definir comportamiento de la app; §7.5 solo captura cuando effective_due_at <= now().

### P341. Si una tarea de Canvas tiene only_visible_to_overrides=true y un estudiante no tiene override aplicable (la entrega 'no existe' para él), ¿se le crea repositorio igual (R2.3.4 exige un único conjunto de repos por tarea), aparece en la vista de estados y en el dashboard, y con qué estado? ¿Y si una entrega de la misma tarea es visible para él y otra no?

- **Requisitos:** R2.4.1, R2.4.3, R2.3.4, R2.3.7
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si la visibilidad por entrega afecta la creación de repos (que es por tarea) y cómo se cuentan sujetos en dashboard, snapshots e informes; evita marcar como 'atrasado' o 'sin entrega' a quien no debía entregar.
- **Opciones planteadas:**
  - Repo se crea igual (es por tarea); snapshot de esa entrega en estado 'NO APLICA'
  - Repo se crea solo si al menos una entrega es visible para el sujeto
  - Sujeto excluido de la tarea mientras ninguna entrega le sea visible
- **Estudio de APIs:** §7.3 dice 'no le creen snapshot ni lo cuenten como atrasado', pero no aborda la creación de repo ni la mezcla entre entregas de la misma tarea.

### P342. Para un repositorio grupal cuyos integrantes tienen fechas efectivas distintas (extensión ADHOC a un integrante, integrantes en secciones con fechas diferentes), ¿qué fecha de cierre usa el snapshot del repo? ¿Se verificará si Canvas permite overrides ADHOC en tareas grupales y qué fecha muestra al grupo?

- **Requisitos:** R2.4.3, R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.4.3 habla de extensiones 'a estudiantes o grupos específicos', pero el snapshot es por repositorio. La decisión fija si un compañero con extensión arrastra a todo el grupo, si puede haber varios SHAs por repo y qué ve el corrector.
- **Opciones planteadas:**
  - max() de las fechas efectivas de los integrantes
  - min() (la más estricta)
  - Solo override de grupo (group_id) o base; ignorar ADHOC/sección de integrantes en tareas grupales
  - Un snapshot por integrante (N SHAs por repo, cada uno con su fecha)
  - Marcar 'fecha ambigua' y requerir que el profesor elija
- **Estudio de APIs:** §7.3 sugiere max() de las fechas de los integrantes y mostrar 'fechas heterogéneas'; §7.1 documenta group_id y student_ids como targets de override.

### P343. Si la composición del grupo cambia en Canvas después de calcular las fechas efectivas (entra un integrante con extensión, sale uno, el grupo se elimina o se renombra), ¿se recalcula la fecha del repo? ¿Qué pasa con un override group_id que apunta a un grupo que ya no existe o que pertenece a otra group_category?

- **Requisitos:** R2.4.3, R2.2.3, R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define reglas de recálculo y manejo de inconsistencias entre overrides y grupos; evita que un snapshot use una fecha derivada de un integrante que ya no está.
- **Opciones planteadas:**
  - Recalcular en cada sync mientras la entrega no esté capturada; congelar tras la captura
  - Recalcular siempre y aplicar las reglas de recaptura
  - Override con group_id desconocido se ignora y se registra advertencia visible
- **Estudio de APIs:** no lo aborda (§4.4 solo indica 'no borrar, marcar deleted_at' al sincronizar).

### P344. Si un estudiante cambia de sección durante el curso, ¿qué sección rige su fecha efectiva: la vigente al momento del cierre, la vigente al momento de la captura, o la del último sync? ¿Se registra el cambio en el historial de fechas del sujeto?

- **Requisitos:** R2.4.2, R2.4.4
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el instante de evaluación de la regla de fecha y evita capturas inconsistentes cuando el cambio de sección ocurre cerca del cierre.
- **Opciones planteadas:**
  - Sección según el último sync anterior a la captura
  - Congelar la fecha efectiva al momento del cierre y no recalcular
  - Recalcular y tratar como cambio de fecha (mismas reglas de recaptura)
- **Estudio de APIs:** no lo aborda.

### P345. ¿Se captura snapshot para un estudiante cuyo enrollment está deleted/inactive/completed al momento del cierre? ¿Y si se retira después de capturado: se conserva el snapshot, se muestra como 'retirado' en la lista de corrección, se excluye de informes? En grupos, ¿el retiro de un integrante cambia la fecha efectiva del repo?

- **Requisitos:** R2.4.5, R2.2.1, R2.7.1
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina qué sujetos entran al job de captura y a la asignación de correctores; evita corregir a estudiantes retirados o perder evidencia de uno que se retira tras entregar.
- **Opciones planteadas:**
  - Capturar igual y marcar 'retirado'
  - No capturar; estado 'RETIRADO' y excluido de corrección
  - Capturar solo si el retiro ocurrió después del cierre
- **Estudio de APIs:** §4.4 y §14 dicen no borrar repos ni historia y marcar al estudiante retirado; no dicen si se captura ni cómo se muestra.

### P346. Para un estudiante inscrito o mapeado a GitHub después de la fecha de cierre de una entrega ya pasada (p. ej. la parcial), ¿cuál es el estado de su snapshot de esa entrega: 'NO APLICA' (inscrito tras el cierre), captura con until histórico (dará sin commits), o el profesor fija una fecha individual desde la app?

- **Requisitos:** R2.4.5, R2.4.6
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita falsos 'sin entrega' en dashboard e informes y define si la app admite fechas individuales propias fuera de Canvas.
- **Opciones planteadas:**
  - Estado 'INSCRITO TRAS EL CIERRE', sin captura
  - Captura normal (probablemente NO_COMMITS)
  - Captura manual o fecha individual definida en la app
- **Estudio de APIs:** no lo aborda.

### P347. Si al llegar la fecha de cierre el repositorio aún no existe (PENDING_MAPPING, ERROR, invitación no aceptada), ¿qué se registra para esa (entrega, sujeto)? Y cuando el repo se crea después del cierre, ¿se captura con until histórico (resultado previsible: vacío o solo commit inicial) o el estado queda terminal hasta acción manual?

- **Requisitos:** R2.4.5, R2.3.10, R2.3.11
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** El job de captura itera sobre (entrega, repositorio); sin repo no hay fila. Define el estado, cómo se muestra en R2.5.6/R2.6.2 y si hay algo que corregir.
- **Opciones planteadas:**
  - Estado 'SIN REPOSITORIO AL CIERRE', terminal, con acción manual 'capturar ahora'
  - Captura automática al aparecer el repo con until histórico
  - Captura automática marcando 'repo creado después del cierre'
- **Estudio de APIs:** §7.5 solo define NO_COMMITS y CAPTURED; §5.5 define estados del repo sin su interacción con el cierre.

### P348. ¿Cómo se distinguen y muestran los casos 'repo sin commits' (GET /commits responde 409 en repos vacíos), 'solo commit inicial del template/auto_init' y 'con trabajo del estudiante'? ¿Se crea tag cuando el único commit es el del template? ¿Cómo identifica la app el commit inicial (SHA del repo base, autor bot, mensaje)?

- **Requisitos:** R2.4.5, R2.4.8
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Un snapshot que apunta al commit del template no es una 'entrega' y no debería contarse como tal en informes ni en corrección; define además la robustez del job ante el 409.
- **Opciones planteadas:**
  - Tres estados: SIN_COMMITS / SOLO_BASE / CAPTURADO
  - Dos estados y mostrar autor del último commit para que el corrector juzgue
  - Comparar SHA con el commit inicial del repo base para detectar SOLO_BASE
- **Estudio de APIs:** §7.5 define NO_COMMITS 'si no hay commits'; §5.3 advierte que sin commit inicial no funcionan tags; no distingue el caso 'solo template'.

### P349. ¿Qué rama(s) se consideran para la versión de cierre: solo default_branch (leída del repositorio), todas las ramas tomando el commit más reciente ≤ fecha en cualquiera de ellas, o configurable por tarea? ¿Se alerta al corrector si existen commits anteriores al cierre en ramas no consideradas?

- **Requisitos:** R2.4.5, R2.4.8
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Un estudiante que trabaja en `dev` sin mergear quedaría con snapshot vacío o antiguo; cambia la consulta (una llamada por rama vs una) y el mensaje al estudiante en Canvas sobre qué rama se corrige.
- **Opciones planteadas:**
  - Solo default_branch
  - Todas las ramas, commit más reciente ≤ fecha
  - Rama fija configurable por tarea (p. ej. 'entrega')
  - default_branch + alerta 'hay commits hasta el cierre en otras ramas'
- **Estudio de APIs:** §7.5 usa sha={default_branch}; §14 advierte no asumir 'main' y leer repository.default_branch.

### P350. Verificar contra la API de GitHub la semántica exacta de `until` en GET /repos/{o}/{r}/commits: ¿es inclusivo en el segundo exacto?, ¿filtra por committer date o author date?, ¿qué devuelve con per_page=1 cuando el historial tiene fechas fuera de orden (recorrido topológico vs cronológico)? ¿Qué precisión (segundos) tienen las fechas que entrega Canvas?

- **Requisitos:** R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina la regla 'último commit antes o EN la fecha' del spec y si la captura es determinista ante historiales con fechas desordenadas.
- **Estudio de APIs:** §7.5 afirma que el primer resultado es el commit más reciente 'en o antes de' until; no verifica committer vs author date ni orden topológico.

### P351. ¿Qué instante define que un commit 'existía' al cierre: el committer date que filtra `until` (falsificable con git commit --date o rebase), el author date, o el instante en que GitHub recibió el push (webhook `push`, received_at)? ¿Se aprueba el enfoque del estudio basado solo en `until`?

- **Requisitos:** R2.4.5, R2.4.7
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es la decisión de integridad central de R2.4.5/R2.4.7: con `until` un estudiante puede subir después del cierre commits con fecha anterior y quedarían incluidos. Un enfoque por push time exige ingestión por webhook antes del cierre y un backfill por polling que no tiene push time.
- **Opciones planteadas:**
  - Committer date vía until (simple, falsificable)
  - Push time vía webhooks: incluir solo commits cuyo push llegó antes del cierre; polling como respaldo marcado
  - Híbrido: until + bandera de anomalía si el push del commit fue posterior al cierre o difiere del committer date en más de X
  - Congelar el HEAD conocido al instante del cierre a partir del último webhook recibido
- **Estudio de APIs:** §7.5 usa `until` (committer date); §8.1 registra webhooks push para el dashboard, sin vincularlos al snapshot.

### P352. Si se detecta un push posterior al cierre que contiene commits con fecha anterior al cierre, o una reescritura de historia (force-push) sobre la rama considerada, ¿cómo se refleja: alerta al corrector en la vista de la entrega, exclusión de esos commits, recaptura, inclusión en el informe diario, mensaje al estudiante? ¿Se registra el evento (before/after, pusher, hora)?

- **Requisitos:** R2.4.7, R2.4.8
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define criterios de aceptación de detección de manipulación y qué evidencia se conserva para la actividad de validación y posibles reclamos.
- **Estudio de APIs:** no lo aborda (el payload push con before/after/pusher aparece en §8.1 solo para métricas).

### P353. ¿Qué protección se implementa contra un force-push que deje el SHA capturado inalcanzable desde cualquier ref (GitHub puede dejar de servirlo tras recolección de basura): tag (mantiene el commit vivo), ruleset de org que impida force-push/borrado de tags, copia zip descargada por la app (GET /repos/{o}/{r}/zipball/{sha}) en almacenamiento propio, mirror a repo de archivo, o solo SHA en BD? ¿Qué estado y mensaje muestra la UI cuando el SHA ya no resuelve (404) o cuando el repo fue eliminado/recreado por el profesor?

- **Requisitos:** R2.4.7, R2.4.8
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.4.7 exige mantener la versión aunque continúe la actividad; el nivel de blindaje define costos de almacenamiento, permisos de la App (rulesets requieren permisos de organización) y estados de error del spec.
- **Opciones planteadas:**
  - SHA + tag (propuesta del estudio)
  - SHA + tag + ruleset de protección de tags/force-push
  - SHA + zip archivado por la app
  - SHA + mirror a repo de archivo del equipo docente
  - Solo SHA en BD
- **Estudio de APIs:** §7.5: SHA en BD como fuente de verdad + tag; ruleset opcional. No considera zip/mirror ni el caso de SHA inalcanzable o repo eliminado.

### P354. ¿Se detecta el borrado o movimiento de un tag de entrega por parte del estudiante (evento webhook `delete` con ref_type=tag, o verificación periódica GET /git/ref/tags/...), y qué se hace: recrear el tag desde el SHA, notificar al equipo docente, registrar incidente en el timeline, avisar al estudiante?

- **Requisitos:** R2.4.7
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Con permiso push los estudiantes pueden borrar tags; define el mecanismo de auto-reparación y si el hecho es información relevante para el corrector.
- **Opciones planteadas:**
  - Recrear silenciosamente en el próximo barrido
  - Recrear + registrar incidente visible al corrector
  - Solo registrar, sin recrear
  - Impedir con ruleset de tags
- **Estudio de APIs:** §7.5 advierte que pueden borrar tags y que el SHA en BD protege; no define detección ni reparación.

### P355. ¿Convención de nombre de tags (entrega-1, entrega-final, <slug-entrega>, con o sin fecha) y tipo (ref ligero vs tag anotado con mensaje, fecha de captura y tagger)? ¿Qué pasa si ya existe un tag con ese nombre creado por el estudiante apuntando a otro SHA, y cómo se nombra una recaptura (entrega-1-v2, mover el tag con force, no crear tag)?

- **Requisitos:** R2.4.5, R2.4.6
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija la interfaz visible en GitHub para estudiantes y correctores, la idempotencia del job y la trazabilidad de recapturas.
- **Estudio de APIs:** §7.5 usa refs ligeros refs/tags/entrega-1-cierre y ante 422 'verificar que apunte al mismo SHA'; no define nombres finales ni recapturas.

### P356. Si dos entregas de la misma tarea capturan el mismo SHA (sin actividad entre ellas) o si para algún sujeto la fecha efectiva de la entrega 'final' resulta anterior a la de una parcial (por overrides), ¿se acepta, se alerta al equipo, o se bloquea? ¿La UI indica 'sin cambios respecto a la entrega anterior'?

- **Requisitos:** R2.4.6, R2.3.2
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.4.6 exige independencia entre versiones; define validaciones sobre el orden de entregas por sujeto y un indicador útil para la corrección.
- **Estudio de APIs:** §7.5 indica una fila por (delivery, repository) que nunca se sobrescribe; no trata SHAs iguales ni orden invertido.

### P357. Si Canvas extiende la fecha de un sujeto DESPUÉS de capturado su snapshot (nuevo override o due_at movido), ¿la app recaptura automáticamente, pide confirmación al profesor, o nunca modifica lo registrado? Si recaptura, ¿se conserva el snapshot anterior como historial (superseded) con su tag? ¿Y si la corrección ya comenzó o terminó sobre el SHA anterior?

- **Requisitos:** R2.4.4, R2.4.5, R2.4.7
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es el conflicto directo entre R2.4.4 (mantener fechas actualizadas) y R2.4.7 (mantener versiones registradas); define la máquina de estados del snapshot, su versionado y reglas de bloqueo.
- **Opciones planteadas:**
  - Recaptura automática conservando historial de snapshots
  - Recaptura solo con confirmación del profesor
  - Nunca recapturar; alertar y permitir acción manual
  - Recaptura automática salvo que la corrección haya iniciado
- **Estudio de APIs:** §7.4 solo reprograma el snapshot 'si cambió la fecha de una entrega NO capturada aún'; el caso post-captura no se aborda.

### P358. Si la fecha se ADELANTA o se elimina una extensión después de capturar, el SHA registrado puede incluir commits posteriores al nuevo cierre. ¿Se recaptura con el nuevo until, se mantiene y se alerta, o se ignora el cambio? ¿Se aplica la misma política que para extensiones?

- **Requisitos:** R2.4.4, R2.4.7
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define simetría o asimetría de la política de recaptura y evita corregir trabajo posterior al cierre vigente.
- **Estudio de APIs:** no lo aborda.

### P359. Si la fecha cambia en Canvas dentro de la ventana de polling previa al cierre (la app aún no la vio), la captura puede usar una fecha obsoleta. ¿Se exige re-sincronizar la tarea de Canvas inmediatamente antes de cada captura, se acepta la ventana, o el snapshot queda 'provisional' hasta el siguiente sync exitoso que confirme la fecha?

- **Requisitos:** R2.4.4, R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el protocolo del job de captura, el costo en requests a Canvas y un posible estado adicional del snapshot.
- **Opciones planteadas:**
  - Sync de la tarea justo antes de capturar (1 GET por entrega)
  - Aceptar la ventana de polling
  - Snapshot 'provisional' confirmado en el siguiente sync
- **Estudio de APIs:** §7.5 no consulta Canvas al capturar; §7.4 asume polling cada 10 min.

### P360. ¿Frecuencia del polling de fechas de Canvas: fija (10 min según el estudio), adaptativa (más frecuente en las horas previas a un cierre), y con botón 'sincronizar ahora'? ¿Cuál es la latencia máxima aceptable entre un cambio en Canvas y su reflejo en la app, como criterio de aceptación medible?

- **Requisitos:** R2.4.4
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Convierte R2.4.4 en un criterio verificable y dimensiona el consumo del throttling de Canvas por token de profesor.
- **Estudio de APIs:** §7.4 propone cron cada 10 min y botón 'sincronizar ahora'; §12 fija sync_canvas cada 10 min.

### P361. ¿Crear, editar o eliminar un AssignmentOverride actualiza assignment.updated_at? Si no, el polling incremental basado en updated_at no detectará extensiones y habrá que comparar siempre all_dates/overrides completos o consultar el endpoint de overrides.

- **Requisitos:** R2.4.3, R2.4.4
- **Área declarada:** 2.4
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** El mecanismo de detección de cambios propuesto depende de este supuesto; si es falso, R2.4.3 y R2.4.4 fallan silenciosamente.
- **Estudio de APIs:** §7.4 usa 'si assignment.updated_at > delivery.canvas_updated_at' como disparador.

### P362. ¿include[]=all_dates e include[]=overrides devuelven siempre todos los overrides (incluidos los ADHOC de todos los estudiantes) con el token del profesor, sin límite de cantidad ni truncamiento? ¿O es necesario llamar además GET /assignments/:id/overrides paginado?

- **Requisitos:** R2.4.1, R2.4.2, R2.4.3
- **Área declarada:** 2.4
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la fuente de datos de fechas y si basta una sola request por curso o se requiere una por entrega.
- **Estudio de APIs:** §7.2 asume que all_dates + overrides 'trae todo en una sola request'.

### P363. ¿Cómo se representa due_at cuando la fecha es 'todo el día' (all_day=true, all_day_date): 23:59:59 en la zona horaria del curso convertida a UTC? ¿La app debe mostrar 'todo el día' o la hora exacta, y qué zona horaria del curso (campo time_zone del Course) se usa para interpretar all_day_date?

- **Requisitos:** R2.4.1
- **Área declarada:** 2.4
- **Tipo:** Investigable en docs · **Entrega:** Ambas entregas
- **Por qué importa:** Un cierre 'todo el día' del 16-09 aparece como 17-09 02:59:59 UTC; sin regla, la UI puede mostrar un día distinto al de Canvas.
- **Estudio de APIs:** §7.1 lista all_day y all_day_date sin tratamiento.

### P364. ¿En qué zona horaria se muestran todas las fechas de la app: fija America/Santiago, la time_zone del curso en Canvas, la del navegador, o configurable por usuario? ¿Se muestra el offset UTC junto a la hora? ¿Cómo se manejan cierres cercanos al cambio de horario de verano chileno (primer domingo de septiembre / abril) en visualización y en la comparación con now()?

- **Requisitos:** R2.4.1, R2.4.2, R2.4.3, R2.4.8
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Las fechas se exhiben en UI, informes por email y anuncios en Canvas; una hora mal convertida es un error visible y grave. Aplica desde la entrega parcial si se muestran fechas.
- **Opciones planteadas:**
  - America/Santiago fija
  - time_zone del curso Canvas
  - Zona del navegador del usuario
  - Configurable por usuario con default America/Santiago
- **Estudio de APIs:** §14 dice guardar en UTC y convertir al renderizar, sin definir la zona de presentación.

### P365. ¿Se mantiene un historial de cambios de fecha por entrega y por sujeto (valor anterior, nuevo, detectado_en, tipo/id de override) y dónde se muestra (vista de la entrega, timeline del repo, informe diario)? Dado que la API de Canvas no informa quién realizó el cambio, ¿se registra el usuario del token con que se detectó o se deja vacío?

- **Requisitos:** R2.4.4
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define tablas y UI de auditoría de R2.4.4 y qué se puede afirmar honestamente en la validación.
- **Estudio de APIs:** §7.4 propone 'log de auditoría: quién/cuándo/de qué a qué', pero 'quién' no está disponible en la API pública.

### P366. ¿Cómo se entera el equipo docente de un cambio de fecha detectado: banner in-app en la tarea, email inmediato, sección 'cambios de fecha' del informe diario, o ninguno (solo historial)?

- **Requisitos:** R2.4.4, R2.6.2
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija R2.4.4 desde la perspectiva del usuario y su cruce con R2.6.2.
- **Estudio de APIs:** no lo aborda (§7.4 solo menciona anuncio a estudiantes y log).

### P367. ¿Qué cambios de fecha disparan comunicación automática a estudiantes y por qué canal: cambio de fecha base o de sección → anuncio (con specific_sections); extensión ADHOC → conversación individual o nada (es privado); adelantos; umbral mínimo (el estudio sugiere >1 h); redacción del texto; flag por tarea para activarlo? ¿Qué pasa si el cambio ocurre cuando la entrega ya cerró?

- **Requisitos:** R2.4.4, R2.6.6, R2.6.7
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Nace de R2.4.4 y define el comportamiento de R2.6.6/R2.6.7 respecto a fechas: evita anuncios masivos por extensiones individuales y fija el criterio de 'cambio relevante'.
- **Estudio de APIs:** §7.4 propone anuncio si el cambio es 'relevante (>1h)' y el profesor lo activó; §9.2 propone specific_sections; §9.4 flag notify_date_change.

### P368. Si la tarea de Canvas vinculada a una entrega se elimina (404 / workflow_state=deleted) o se despublica después de la vinculación, ¿qué pasa con la entrega: se marca 'huérfana', se bloquea o cancela la captura pendiente, se conservan los snapshots ya capturados, se notifica al equipo?

- **Requisitos:** R2.4.1, R2.4.4, R2.4.7
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define estados de la entrega y evita que el sync falle o borre datos ante un 404.
- **Estudio de APIs:** §5.1 indica no crear repos para tareas no publicadas; no aborda eliminación posterior a la vinculación.

### P369. ¿Qué constituye formalmente 'la versión registrada' de una entrega: SHA en BD; SHA + tag en GitHub; una rama entrega-N; un zip descargado y almacenado por la app; un fork/mirror? ¿Se aprueba la propuesta SHA + tag del estudio?

- **Requisitos:** R2.4.5, R2.4.7, R2.4.8
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define almacenamiento, permisos de la App, disponibilidad si GitHub o el repo dejan de estar accesibles y la forma del link de R2.4.8.
- **Opciones planteadas:**
  - SHA en BD
  - SHA + tag
  - SHA + rama
  - SHA + zip archivado
  - SHA + fork/mirror
- **Estudio de APIs:** §0 y §7.5 recomiendan SHA en BD (fuente de verdad) + tag inmutable refs/tags/entrega-N.

### P370. ¿Cada cuánto corre el job de captura (el estudio propone 5 min) y cuál es la tolerancia aceptable entre la fecha de cierre y la captura efectiva como criterio de aceptación ('capturado dentro de N minutos')? ¿Se muestra captured_at y una etiqueta 'captura tardía' cuando se excede (p. ej. servidor caído), considerando que con until histórico el resultado solo cambia ante force-push o commits retrodatados?

- **Requisitos:** R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Convierte el 'automáticamente' de R2.4.5 en algo medible y define qué se comunica cuando la captura fue tardía.
- **Estudio de APIs:** §7.5 propone cron cada 5 min que barre todo lo vencido y no capturado; §12 fija capture_snapshots cada 5 min.

### P371. Con N repositorios cerrando a la misma hora (60–100), las creaciones de tags son requests generadoras de contenido (límite 80/min y 500/h): ¿qué orden y throttle se aplica (p. ej. registrar todos los SHA con GETs primero, luego tags en cola) y cuánto puede tardar en completarse la captura de toda la entrega? ¿Se muestra el progreso 'capturados 43/60'?

- **Requisitos:** R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Dimensiona el job para el caso real de un curso y fija la UI de progreso de cierre.
- **Estudio de APIs:** §2.4 documenta los límites secundarios y §5.5 fija throttle para creación de repos; no lo aplica a snapshots.

### P372. ¿Se permite a algún rol capturar manualmente ('capturar ahora'), recapturar, o fijar a mano un SHA distinto para un sujeto (acuerdo informal de atraso, rama equivocada)? ¿Con auditoría (quién, cuándo, motivo) y marcado como 'manual' frente a los automáticos? ¿Qué permiso de R2.1.8 lo habilita?

- **Requisitos:** R2.4.5, R2.4.7, R2.1.8
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el equilibrio entre R2.4.7 (no alterar) y la operación real; afecta RBAC, UI y trazabilidad.
- **Estudio de APIs:** no lo aborda.

### P373. Una vez que un corrector inicia o termina la corrección sobre un SHA, ¿se bloquea la recaptura automática y manual? Si aun así el SHA cambia, ¿qué ve el corrector (aviso, diff entre snapshot anterior y nuevo, estado 'requiere re-revisión')?

- **Requisitos:** R2.4.7, R2.7.4
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cruza R2.4.7 con R2.7.4 y define estados de la entrega por sujeto dentro de la corrección.
- **Estudio de APIs:** no lo aborda.

### P374. Además del snapshot al cierre, ¿se registra una versión 'última' para tolerancia de atrasos: un segundo snapshot a lock_at, un puntero al HEAD actual con 'N commits después del cierre', o nada? ¿Se calcula el atraso (último commit − cierre) y se refleja en Canvas (late_policy_status, comentario) o solo en la app?

- **Requisitos:** R2.4.5, R2.4.7, R2.7.6
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si la app soporta políticas de atraso del profesor y qué se muestra al corrector junto a la versión oficial.
- **Opciones planteadas:**
  - Solo snapshot al cierre
  - Snapshot al cierre + snapshot a lock_at
  - Snapshot al cierre + HEAD actual y conteo de commits posteriores
  - Configurable por tarea
- **Estudio de APIs:** §10.4 lista submission[late_policy_status] sin vincularlo a snapshots; §7.5 captura una sola versión por entrega.

### P375. ¿El acceso directo a la versión es un link a GitHub (/tree/<sha>) —lo que exige que cada ayudante tenga acceso de lectura a repos privados de la org—, un visor de código dentro de la app usando el token de la App (GET /git/trees/{sha}?recursive=1 + GET /contents?ref=sha), o ambos? Si es link, ¿cómo se otorga y revoca ese acceso (miembro de la org con base permission read, colaborador por repo, team docente) y qué ocurre al retirar a un ayudante? ¿La URL /tree/<sha> funciona si el SHA quedó inalcanzable desde refs?

- **Requisitos:** R2.4.8, R2.7.4, R2.1.8, R2.1.9
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina permisos de la GitHub App, el flujo de incorporación de ayudantes y si R2.4.8/R2.7.4 dependen de que el ayudante tenga cuenta GitHub y acceso a la org.
- **Opciones planteadas:**
  - Link a GitHub + ayudantes como miembros de la org con lectura
  - Link a GitHub + colaborador de lectura por repo
  - Visor de código dentro de la app (sin cuenta GitHub del ayudante)
  - Ambos
- **Estudio de APIs:** §7.5 y §10.2 asumen link https://github.com/ORG/REPO/tree/<SHA>; §3.4 solo menciona quitar al ayudante de la org; no trata cómo se le da acceso de lectura.

### P376. ¿Se ofrece comparación entre versiones (compare/<sha1>...<sha2>) entre entregas consecutivas y contra el commit inicial del repo base? ¿Cuál es la 'base' de la primera entrega cuando no hubo repo base (commit auto_init)? ¿Funciona compare con SHAs no alcanzables desde refs?

- **Requisitos:** R2.4.6, R2.4.8, R2.5.9
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el alcance de R2.4.8 más allá del link y una posible métrica de R2.5.9.
- **Estudio de APIs:** §7.5 sugiere compare entre entregas como candidato a R2.5.9.

### P377. ¿Qué estados tiene una entrega a nivel agregado cuando sus sujetos tienen fechas distintas (futura, abierta, cerrando —algunos sujetos ya cerrados—, cerrada, capturada parcialmente, con problemas)? ¿Se muestra el rango [primera, última] de fechas efectivas y el % de snapshots capturados?

- **Requisitos:** R2.4.5, R2.5.6
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.5.6 exige mostrar entregas, fechas y estado; con overrides no existe una única fecha por entrega.
- **Estudio de APIs:** no lo aborda.

### P378. ¿Cómo se presenta la fecha efectiva de cada sujeto y su origen (general / sección X / grupo / extensión individual, con id del override) en la vista de la entrega, y se listan explícitamente las excepciones ('3 estudiantes con extensión hasta …')?

- **Requisitos:** R2.4.2, R2.4.3
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Criterio de aceptación de UI para R2.4.2/R2.4.3 y evidencia demostrable en la corrección.
- **Estudio de APIs:** §7.3 devuelve (due_at, origen) como texto; §5.6 muestra tabla de estados de repos sin columna de fecha.

### P379. Si al momento del cierre el refresh token de Canvas del profesor está revocado/expirado (fechas sin sincronizar hace X horas) o la GitHub App fue desinstalada de la org, ¿el job captura igual con las últimas fechas conocidas (marcando 'fechas posiblemente desactualizadas'), suspende la captura y alerta, o bloquea la entrega? ¿Cuál es el umbral de antigüedad aceptable del último sync?

- **Requisitos:** R2.4.4, R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la resiliencia del proceso automático y los estados de alerta visibles; el snapshot depende de GitHub (token de App) pero la fecha depende de Canvas (token del profesor).
- **Estudio de APIs:** §1.1 advierte que sin refresh token guardado R2.4.5 no funciona de madrugada; no define comportamiento ante fallo.

### P380. ¿Qué invariantes de concurrencia e idempotencia se fijan para la captura: unicidad (entrega, repositorio[, versión]), lock por sujeto, y comportamiento cuando el tag ya existe apuntando a otro SHA (creado por el estudiante o por una corrida anterior): estado CONFLICTO, sobrescribir con force, crear con otro nombre, ignorar el tag?

- **Requisitos:** R2.4.5, R2.4.6
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita snapshots duplicados o inconsistentes con dos workers o reinicios, y define un estado de error del spec.
- **Estudio de APIs:** §7.5: 'si el tag ya existe (422) → verificar que apunte al mismo SHA', sin definir qué hacer si no coincide.

### P381. ¿Qué validaciones sobre fechas se aplican al vincular y al sincronizar: lock_at < due_at, unlock_at > due_at, entrega final con fecha anterior a una parcial, dos entregas con la misma fecha, y tarea de Canvas cuya fecha ya pasó al momento de vincular (¿se captura de inmediato con until histórico, se pide confirmación, o se marca 'vinculada tras el cierre')? ¿Bloquear, advertir o ignorar?

- **Requisitos:** R2.4.1, R2.3.1, R2.3.2, R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el flujo de creación de tarea en cuanto a fechas (presente ya en la demo parcial) y evita capturas sorpresa al vincular.
- **Estudio de APIs:** no lo aborda (§5.2 solo valida group_category_id entre entregas).

### P382. ¿La app solo lee extensiones desde Canvas (R2.4.3 'considerar') o también permite al profesor crear/editar/eliminar overrides en Canvas desde la app (POST/PUT/DELETE .../overrides), p. ej. otorgar una extensión desde la vista del sujeto?

- **Requisitos:** R2.4.3
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define alcance funcional, scopes OAuth adicionales y un flujo de UI; si es solo lectura, el spec debe indicar que el cambio se hace en Canvas y cuánto tarda en reflejarse.
- **Estudio de APIs:** §7.1 lista los endpoints de escritura de overrides sin recomendar usarlos.

### P383. ¿Al capturar el snapshot se informa al estudiante o grupo por Canvas (comentario en la submission con SHA/tag/link, o conversación) indicando qué versión será corregida, incluido el caso 'sin commits'? ¿Es un flag por tarea (R2.6.7)?

- **Requisitos:** R2.4.5, R2.6.7, R2.3.12
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija la transparencia hacia el estudiante y agrega un evento al outbox de comunicaciones.
- **Estudio de APIs:** §9.4 no incluye un evento 'snapshot capturado' entre los flags; §10.4 sugiere comentario con SHA solo al calificar.

### P384. ¿La app registra algo en Canvas como 'entrega' al cierre (comentario, submission de tipo online_url con el link al tree/<sha>) o la tarea de Canvas queda sin submissions y solo recibe la nota? ¿Qué submission_types debe tener la tarea de Canvas de cada entrega, y cómo se evita que una política de 'missing submission' de Canvas asigne 0 automáticamente a estudiantes sin submission tras la fecha?

- **Requisitos:** R2.4.5, R2.7.6, R2.3.12
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Una configuración inadecuada de la tarea en Canvas puede calificar automáticamente con 0 o mostrar 'faltante' a todos los estudiantes, aunque la app haya capturado su versión.
- **Estudio de APIs:** §5.7 usa comentario en submission para la URL del repo; §10.4 califica sin exigir submission; no aborda políticas de faltantes.

### P385. ¿Tiene algún rol unlock_at: inicio del período de la entrega para métricas (R2.5.7), no notificar ni contar actividad antes de esa fecha, o se ignora completamente?

- **Requisitos:** R2.4.1, R2.5.7
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el concepto 'período de entrega' del spec y si el estado 'futura' depende de unlock_at.
- **Estudio de APIs:** §5.1 lo lista como campo; §8.5 define el período por [entrega_anterior.due, entrega_actual.due] sin usar unlock_at.

### P386. ¿Los campos de sección start_at/end_at y restrict_enrollments_to_section_dates afectan algo en la app (participación del estudiante, fecha efectiva) o se ignoran? Confirmar en la documentación de Canvas si alteran las fechas de entrega o solo el acceso al curso.

- **Requisitos:** R2.4.2
- **Área declarada:** 2.4
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** El estudio afirma que 'cambia qué fechas aplican'; hay que confirmar si eso rige para due dates antes de modelarlo.
- **Estudio de APIs:** §4.2 advierte que restrict_enrollments_to_section_dates 'cambia qué fechas aplican'.

### P387. ¿Cómo se manejan overrides con datos inconsistentes respecto a lo sincronizado: course_section_id de una sección desconocida (creada tras el sync), student_ids no inscritos, group_id de otra group_category, overrides sin due_at ni lock_at? ¿Se ignoran, se registran advertencias visibles, o disparan un re-sync?

- **Requisitos:** R2.4.2, R2.4.3
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la robustez del cálculo de fecha efectiva ante datos sucios y el orden de sincronización (secciones/grupos antes que overrides).
- **Estudio de APIs:** no lo aborda.

### P388. ¿El equipo dispone (o dispondrá antes de la final) de una instancia Canvas donde pueda crear al menos dos secciones, estudiantes en dos secciones, un group set, y overrides por sección, por grupo y ADHOC, para probar y demostrar R2.4.2/R2.4.3? ¿Free-for-Teacher permite todo eso? ¿Y cuentas de estudiantes de prueba con las que hacer push real a GitHub para probar la captura?

- **Requisitos:** R2.4.2, R2.4.3, R2.4.5
- **Área declarada:** 2.4
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Sin este entorno no se pueden resolver las preguntas empíricas ni demostrar la funcionalidad, y la sección 4 del enunciado indica que lo que no se puede usar no se considera cumplido.
- **Estudio de APIs:** §1.2 propone Free-for-Teacher como plan B; §13 hito 1 pide 'Canvas de pruebas con 2 secciones… 2 assignments con overrides'.

### P389. ¿Qué parte de la sección 2.4 se muestra en la entrega parcial del 16-sep: al menos la fecha base y las fechas por sección de la entrega vinculada en la vista de la tarea (con zona horaria), o nada relacionado con fechas? ¿Se requiere ya el polling de fechas o basta con leerlas al vincular?

- **Requisitos:** R2.4.1, R2.4.2
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija el alcance mínimo de fechas para la demo y evita construir el job de captura antes de tiempo.
- **Estudio de APIs:** §13 no incluye fechas ni snapshots entre los hitos mínimos de la parcial.

### P390. ¿Qué metadatos guarda y muestra cada snapshot: SHA, committed_at, autor del último commit, número de commits hasta el cierre, fecha efectiva usada y su origen, captured_at, nombre del tag, estado, commits posteriores al cierre, fuente (automático/manual/recaptura)? ¿Cuáles son obligatorios para dar por cumplido R2.4.8?

- **Requisitos:** R2.4.5, R2.4.8
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el esquema de DeliverySnapshot y el contenido de la vista de corrección.
- **Estudio de APIs:** §5.2 propone commit_sha, committed_at, tag_name, captured_at, status, effective_due_at; §10.2 sugiere mostrar 'capturado el… · 47 commits · último por…'.

### P391. Si un estudiante cambia de grupo en Canvas entre la entrega parcial y la final, ¿su entrega final se captura en el repo del nuevo grupo y la parcial permanece asociada al repo antiguo? ¿Cómo lo ve el corrector y cómo se refleja en la lista de entregas del estudiante?

- **Requisitos:** R2.4.6, R2.3.4, R2.2.3
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.3.4 exige un único conjunto de repos por tarea, pero un cambio de grupo rompe la correspondencia sujeto–repo entre entregas; define el modelo de snapshots por sujeto vs por repo.
- **Estudio de APIs:** no lo aborda.

### P392. ¿Qué ocurre con la versión registrada y su acceso cuando el repo usa Git LFS (los archivos aparecen como punteros en tree/<sha> y en el zipball), contiene submódulos (código externo no incluido), archivos >100 MB rechazados por GitHub, o supera el tamaño recomendado (~1 GB)? ¿La app detecta .gitattributes/.gitmodules y marca el snapshot con una advertencia para el corrector, documenta la limitación en el mensaje inicial al estudiante ('no uses LFS ni submódulos'), o no hace nada? Verificar qué devuelve GET zipball para un repo con LFS.

- **Requisitos:** R2.4.5, R2.4.8, R2.7.4, R2.5.10
- **Área declarada:** 2.4 / 2.5
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** El corrector podría revisar una versión incompleta sin saberlo; el spec debe fijar si es limitación documentada o caso detectado.
- **Opciones planteadas:**
  - Detectar y advertir en snapshot y vista de corrección
  - Documentar como limitación y avisar al estudiante
  - No manejar
- **Estudio de APIs:** §5.3 solo trata límites de GET /contents; no aborda LFS, submódulos ni tamaño de repos en snapshots.

### P393. ¿En qué zona horaria y formato se muestran todas las fechas: siempre America/Santiago, la del navegador del usuario, o la configurada en el curso de Canvas (campo time_zone)? ¿Se muestra el sufijo de zona? ¿Formato 24 h estilo 'mié 16 sep 2026, 13:30'? ¿Se combinan fecha relativa ('vence en 2 días') y absoluta? ¿Cómo se muestra una entrega con fechas heterogéneas por sección o con extensiones ('16 sep · Sección 2: 17 sep · 1 extensión')?

- **Requisitos:** R2.4.1, R2.4.2, R2.5.6
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Evita que un snapshot o un 'vence hoy' se interprete con 3 horas de error; define el componente de fecha reutilizado en entregas, dashboard, timeline e informe.
- **Opciones planteadas:**
  - America/Santiago fija
  - Zona del navegador
  - time_zone del curso Canvas
- **Estudio de APIs:** §14 'Zonas horarias': guardar UTC y convertir solo al renderizar; §7.3 sugiere mostrar en la UI que un repo grupal tiene fechas heterogéneas. No decide la zona de renderizado.

### P394. ¿La fecha efectiva por (entrega, sujeto) se MATERIALIZA en una tabla (delivery_id, subject_id, effective_due_at, effective_lock_at, source, override_id, applies:boolean, computed_at) que alimenta el barrido de snapshots, el dashboard, el informe y los recordatorios, o se recalcula en cada lectura desde overrides + membresías? Si se materializa: ¿cuándo se recalcula (cada sync de fechas, cada cambio de roster/grupo/sección), se crean filas eager al vincular la entrega o lazy en el barrido, y se guardan además los AssignmentOverride crudos en una tabla local?

- **Requisitos:** R2.4.1, R2.4.2, R2.4.3, R2.4.4, R2.4.5, R2.5.6
- **Área declarada:** 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** El barrido 'todo lo vencido y no capturado' necesita un índice sobre la fecha efectiva; el cálculo al vuelo no es indexable y la materialización exige definir sus disparadores de invalidación.
- **Opciones planteadas:**
  - Tabla materializada recalculada por eventos
  - Cálculo en cada lectura
  - Híbrido: materializada solo para entregas no capturadas
- **Estudio de APIs:** §7.3 entrega el algoritmo como función pura; §5.2 pone effective_due_at solo en DeliverySnapshot; §7.5 barre 'sin snapshot y con effective_due_at <= now()', lo que presupone materialización sin decirlo.

### P395. ¿Cuál es la enumeración cerrada de estados de la fila DeliverySnapshot y sus transiciones: PENDING → CAPTURING → CAPTURED | NO_COMMITS | NO_REPO | NOT_APPLICABLE | ERROR; CAPTURED → SUPERSEDED por recaptura; y un sub-estado de tag (TAG_PENDING / TAG_OK / TAG_CONFLICT / TAG_FAILED) independiente del SHA para permitir captura en dos fases? ¿Cuáles son terminales y cuáles reintenta el barrido? ¿Se persisten la rama/ref y el `until` exactos usados en la consulta, y los metadatos (número de commits, autores) se derivan de CommitRecord (posiblemente incompleto) o de la API al capturar? ¿GradingRecord referencia la fila-versión del snapshot (FK) o copia el SHA para detectar que se corrigió una versión superada?

- **Requisitos:** R2.4.5, R2.4.6, R2.4.7, R2.4.8, R2.7.4
- **Área declarada:** 2.4 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija el contrato entre el job de captura, la vista de la entrega y la corrección; sin sub-estado de tag un fallo de rate limit al crear tags deja snapshots 'no capturados' aunque el SHA ya esté registrado.
- **Opciones planteadas:**
  - Estado único con enumeración ampliada
  - Estado del SHA + sub-estado de tag
  - Versionado de filas con flag current
- **Estudio de APIs:** §7.5 define solo NO_COMMITS y CAPTURED; §5.2 lista snapshot_status sin enumerar.

### P396. ¿Qué filas deben ser autocontenidas como evidencia, copiando al momento del hecho (full_name y owner del repo, installation_id, rama, SHA, lista de integrantes con sus logins, sección, título/id del override y fecha efectiva usada, nombre del grupo), para seguir siendo legibles y correctas aunque el origen cambie o desaparezca (override borrado, grupo renombrado o eliminado, repo renombrado o transferido, org re-vinculada, estudiante retirado, mapeo corregido)? ¿Y cuáles solo llevan FKs y se resuelven en la lectura? ¿Se aplica lo mismo a GradingRecord (copia de la rúbrica y del payload enviado a Canvas) y al informe diario (copia de las alertas incluidas)?

- **Requisitos:** R2.4.7, R2.4.8, R2.7.4, R2.7.6
- **Área declarada:** 2.4 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina si la vista de corrección y la auditoría sobreviven a cambios en Canvas/GitHub o quedan con referencias rotas; afecta el tamaño de tablas y la política de FKs.
- **Opciones planteadas:**
  - Denormalizar en snapshot, grading e informe
  - Solo FKs con soft delete en origen
  - Copia parcial (solo lo que puede desaparecer en Canvas/GitHub)
- **Estudio de APIs:** §7.5 'SHA en BD = fuente de verdad', sin hablar de denormalizar el contexto que lo rodea.

### P397. El snapshot usa `until` (fecha del commit según GitHub) y el dashboard/timeline usarán la fecha que el equipo elija (author, committer o recepción del push). ¿Se exige que ambas definiciones coincidan? Si no, ¿qué se muestra cuando el commit capturado no es el último que el timeline dibuja antes de la línea de cierre, o cuando el timeline muestra commits 'antes del cierre' que el snapshot no incluyó? ¿Se persisten en CommitRecord las tres marcas (authored_at, committed_at, received_at del push/webhook) para poder cambiar la regla sin reingestar?

- **Requisitos:** R2.4.5, R2.5.2, R2.5.7, R2.5.10
- **Área declarada:** 2.4 / 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita que corrector y dashboard se contradigan sobre 'qué había al cierre' y fija columnas obligatorias de CommitRecord desde la primera ingesta.
- **Opciones planteadas:**
  - Misma definición en ambos
  - Definiciones distintas con aviso explícito en UI
  - Persistir las tres fechas y decidir por vista
- **Estudio de APIs:** §7.5 usa `until`; §8.3 guarda authored_at y committed_at pero no la fecha de recepción del push.

---

## 2.5

### P398. La GitHub App recibe webhooks de TODOS los repos de la instalación: el repo base, repos creados a mano en la org, repos de otros cursos o semestres, y repos creados por el worker cuyo INSERT en BD falló. ¿Qué hace el receptor con eventos de repos no reconocidos: descartarlos en silencio, registrarlos como 'repo desconocido' en un panel de diagnóstico, o intentar adoptarlos por nombre/topic/`template_repository`? ¿La actividad del repo base (commits del profesor) se ingiere y se muestra (historial de versiones del base) o se excluye del pipeline de commits?

- **Requisitos:** R2.5.2, R2.5.10, R2.1.5
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el filtro del receptor, la detección de repos huérfanos y si el base tiene su propia vista de actividad.
- **Opciones planteadas:**
  - Descartar silenciosamente
  - Registrar como desconocidos para diagnóstico
  - Adoptar automáticamente si coinciden con el patrón de nombre
- **Estudio de APIs:** §8.1: 'la App recibe eventos de todos los repos de la instalación automáticamente', sin definir filtrado ni tratamiento del repo base.

### P399. GitHub expone por commit `verification.verified` (firma GPG/SSH válida o commit hecho desde la web). ¿Se usa como señal de confianza en la atribución (distinguir 'atribuido por login verificado' de 'atribuido por email no verificable') y se muestra al docente en dashboard y timeline, o se ignora? ¿Las instrucciones enviadas al estudiante por Canvas (R2.3.12) recomiendan configurar el email noreply de GitHub o firmar commits para que la atribución funcione?

- **Requisitos:** R2.5.4, R2.5.8, R2.3.12
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Decide un campo más en CommitRecord, un indicador en la UI y el texto de las instrucciones iniciales al estudiante.
- **Opciones planteadas:**
  - Ignorar la firma
  - Mostrar indicador de verificación sin afectar conteos
  - Ponderar solo commits verificados en alertas de 'sin participación'
- **Estudio de APIs:** §8.4 propone atribución por login, email y nombre; no menciona la verificación de firma de commits.

### P400. ¿Cómo se garantiza que un mismo push procesado dos veces (reintento de GitHub) o eventos fuera de orden no dupliquen commits ni corrompan agregados, y que un push perdido durante una caída aparezca después? ¿Qué latencia máxima se acepta entre un push y su aparición en dashboard/timeline, y se muestra 'última actualización' por repo?

- **Requisitos:** R2.5.2, R2.5.3, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija la clave de idempotencia de la ingesta (sha por repo, delivery id), el reconciliador y el criterio de aceptación de frescura del dashboard.
- **Estudio de APIs:** §8.1 responder 202 y procesar en background; §8.2 reconciliador cada 15 min con ETag. No fija latencia objetivo ni deduplicación por X-GitHub-Delivery.

### P401. ¿Cuál es el contenido exacto y cerrado del dashboard de una tarea? Hay que fijar la lista de KPIs (p. ej. repos totales / listos / con problema, repos con actividad en los últimos N días, repos sin actividad reciente, estudiantes sin participación, commits en las últimas 24 h y 7 días, próxima entrega con cuenta regresiva), la(s) tabla(s) con una fila por repo y sus columnas (integrantes, sección, estado, último commit, commits en el período, integrantes sin commits, enlace a GitHub y al timeline), los gráficos incluidos y el orden de las secciones.

- **Requisitos:** R2.5.1, R2.5.2, R2.5.3, R2.5.4, R2.5.5, R2.5.6
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define qué agregados se precomputan (§8.3), el modelo de datos de RepoStatus/RepoActivityDaily y los criterios de aceptación de R2.5.1; sin lista cerrada no se puede escribir el spec de la vista ni probarla.
- **Opciones planteadas:**
  - Tarjetas KPI + tabla por repo + un gráfico de serie temporal
  - Tarjetas KPI + tabla + gráfico + panel de alertas separado (R2.5.3/R2.5.4)
  - Dashboard por pestañas: Resumen / Repositorios / Entregas / Participación
- **Estudio de APIs:** §8.3 propone las tablas RepoActivityDaily y RepoStatus; §8.5 mapea cada requisito a una métrica; no fija KPIs, columnas ni layout.

### P402. ¿El dashboard es la pantalla que se abre por defecto al entrar a una tarea (el enunciado dice 'disponible de forma inmediata al ingresar a la vista de una tarea') o una pestaña más? ¿Cuál es el criterio de aceptación medible de 'inmediato': p. ej. respuesta del servidor p95 < 1 s con 60 repos y 5.000 commits, y cero llamadas a GitHub o Canvas dentro del request de render?

- **Requisitos:** R2.5.1
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Convierte la restricción del enunciado ('sin requerir esperar a que se recopile en ese momento') en un requisito no funcional verificable y fija la navegación de la tarea.
- **Estudio de APIs:** §8 (intro): 'la vista lee de su base de datos, nunca de la API de GitHub'; §12: todas las vistas leen de Postgres. No fija un umbral numérico ni la navegación.

### P403. ¿Cuál es la granularidad temporal de la serie de actividad (día, semana, o ambas con selector) y en qué zona horaria se cortan los 'días': America/Santiago fija, zona configurable por curso, o zona del navegador del usuario? Nótese que Chile cambia a horario de verano en septiembre de 2026, dentro del período del proyecto, y que Canvas y GitHub entregan todo en UTC.

- **Requisitos:** R2.5.2, R2.5.7
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina la clave de agregación de RepoActivityDaily, cómo se interpretan 'último día', 'últimas 24 h' y los límites de período de entrega; un corte en UTC desplaza los commits nocturnos chilenos al día siguiente.
- **Opciones planteadas:**
  - Día en America/Santiago fija
  - Día en zona configurable por curso
  - Semana ISO
  - Día + semana con selector
- **Estudio de APIs:** §8.3 agrega por día (RepoActivityDaily.day) sin fijar zona; §14 recomienda guardar UTC (timestamptz) y convertir sólo al renderizar.

### P404. ¿Cómo se representa 'la actividad de los distintos repositorios a lo largo del tiempo' cuando hay 60 o más repos? Una línea por repo es ilegible. Opciones: serie agregada de la tarea con posibilidad de aislar repos seleccionados; heatmap repos × días; sparkline por fila de la tabla; barras apiladas por sección.

- **Requisitos:** R2.5.2
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija el tipo de gráfico, los datos que la API interna debe entregar y el criterio de aceptación de legibilidad para R2.5.2.
- **Opciones planteadas:**
  - Serie agregada + selección de repos
  - Heatmap repos × días
  - Sparklines por fila
  - Combinación de las anteriores
- **Estudio de APIs:** §8.5: 'serie diaria de commits por repo'; no aborda la visualización con muchos repos.

### P405. ¿Cuál es el rango temporal por defecto del gráfico y de los KPIs 'recientes'? Inicio: creación del primer repo de la tarea, unlock_at o creación de la primera entrega en Canvas, creación de la tarea en la app, o primer commit. Fin: hoy, o la última fecha efectiva de cierre si la tarea ya terminó. ¿Ventana móvil (últimos 14/30 días) o rango completo con zoom?

- **Requisitos:** R2.5.2, R2.5.3
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina qué datos se cargan por defecto, el comportamiento tras el cierre de la tarea y qué se ve en una tarea recién creada.
- **Estudio de APIs:** no lo aborda

### P406. ¿Qué cuenta como 'actividad' de un repositorio? Sólo commits, o también creación de ramas y tags, pull requests, issues, comentarios y releases. Si sólo commits, ¿la 'última actividad' es la fecha del último commit o la del último push (un push puede traer commits con fechas antiguas)?

- **Requisitos:** R2.5.2, R2.5.3, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define qué webhooks y tablas se necesitan (PRs/issues exigen eventos y modelos adicionales) y la semántica de last_commit_at usada por R2.5.3 y el informe diario.
- **Opciones planteadas:**
  - Sólo commits
  - Commits + eventos de push (fecha de recepción)
  - Commits + ramas/tags
  - Commits + PRs + issues
- **Estudio de APIs:** §8.1 propone suscribirse a push, create, delete, repository, member, member_invite, pero §8.3 sólo modela commits; no aborda PRs ni issues.

### P407. ¿Se monitorean commits de todas las ramas o sólo de la rama por defecto (repository.default_branch, que puede no ser main)? Si todas: ¿un commit presente en varias ramas se cuenta una sola vez por SHA y cómo se etiqueta en el timeline? Si sólo la por defecto: ¿un estudiante que trabaja dos semanas en una rama dev aparece como 'sin actividad'? ¿Qué ocurre si el estudiante cambia la rama por defecto del repo?

- **Requisitos:** R2.5.2, R2.5.4, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia el filtro del webhook push (ref), la consulta de reconciliación (sha=) y la definición de participación; afecta directamente falsos positivos de R2.5.3 y R2.5.4.
- **Opciones planteadas:**
  - Sólo rama por defecto
  - Todas las ramas, conteo único por SHA
  - Todas las ramas con etiqueta de rama en el timeline
- **Estudio de APIs:** §8.1: 'filtrar rama por defecto si quieren'; §14: no asumir main, leer default_branch.

### P408. ¿Qué commits se EXCLUYEN de las métricas de participación: merge commits (más de un padre), el commit inicial de auto_init o heredado de la plantilla, commits del bot de la app (subida de archivos base), bots externos (github-actions[bot], dependabot), y commits de profesores/ayudantes en repos de estudiantes? ¿Se mantiene una lista por curso de logins/emails 'del equipo docente y bots' a excluir, y esos commits se muestran igual en el timeline aunque no cuenten?

- **Requisitos:** R2.5.2, R2.5.4, R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita que un repo recién creado aparezca 'con actividad' por el commit de plantilla y que un fix del profesor cuente como participación del estudiante; define una tabla de exclusiones y una regla de negocio.
- **Estudio de APIs:** §8.4: marcar merges (parents.length > 1) y permitir excluirlos; §5.3 usa committer 'ICC4201 Bot'; no aborda commits del profesor ni bots externos.

### P409. ¿Qué marca temporal define la fecha de un commit para series, períodos y 'último commit': author.date (manipulable, sobrevive a rebase), committer.date (cambia con rebase/amend) o la fecha de recepción del push (única no falsificable)? ¿Cómo se tratan commits con fecha futura, anterior a la creación del repo (historial importado de otro proyecto) o con reloj desajustado: se aceptan tal cual, se recortan al rango del repo, o se marcan como anómalos?

- **Requisitos:** R2.5.2, R2.5.3, R2.5.7, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Afecta a qué período de entrega se asigna cada commit, a la captura de versión por fecha (R2.4.5 usa until=) y a la posibilidad de que un estudiante 'retrodate' trabajo para caer dentro del plazo.
- **Opciones planteadas:**
  - author.date
  - committer.date
  - Fecha de recepción del push (webhook)
  - committer.date con marca de anomalía si difiere mucho de la recepción
- **Estudio de APIs:** §8.3 guarda authored_at y committed_at pero no decide cuál se usa; §7.5 usa until= sobre la fecha de committer de GitHub.

### P410. ¿Se registran líneas añadidas/eliminadas y archivos cambiados por commit? El payload del webhook push trae listas de archivos (added/modified/removed) pero no conteo de líneas, y GET /repos/{o}/{r}/commits tampoco: obtener líneas exige una llamada GET /repos/{o}/{r}/commits/{sha} por commit (1 punto de rate limit cada una). Si se registran, ¿se filtran archivos generados o binarios (lock files, node_modules, imágenes) y con qué lista de patrones? Si no, ¿el timeline muestra tamaño del commit de otra forma (nº de archivos)?

- **Requisitos:** R2.5.2, R2.5.8, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina el costo de ingesta (60 repos × cientos de commits), el contenido de CommitRecord y qué métricas son posibles para R2.5.8 y R2.5.10.
- **Opciones planteadas:**
  - No registrar líneas; usar nº de archivos del payload
  - Registrar líneas con llamada por commit y filtros de archivos generados
  - Registrar líneas sólo vía stats/contributors agregado por semana
- **Estudio de APIs:** §8.3 marca additions/deletions/changed_files como opcional; §8.5 advierte que líneas es mala métrica de contribución; no cuantifica el costo de obtenerlas.

### P411. ¿Cuál es la definición numérica de 'sin actividad reciente': N días sin commits, con N fijo global (3, 5, 7…), configurable por curso, por tarea o por entrega? ¿Valor por defecto y quién puede cambiarlo (permiso)? ¿La misma N alimenta el informe diario (R2.6.2) y los marcadores de gap del timeline, o cada uno tiene su umbral?

- **Requisitos:** R2.5.3, R2.6.2, R2.5.10
- **Área declarada:** 2.5 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin un número no hay criterio de aceptación para R2.5.3; la coherencia entre dashboard, informe y timeline evita que la misma situación se reporte distinto en cada lugar.
- **Opciones planteadas:**
  - N fijo global
  - N configurable por curso
  - N configurable por tarea
  - N configurable por entrega
- **Estudio de APIs:** §8.5: 'last_commit_at < now() - X días; X configurable' sin valor ni nivel de configuración; §9.1 usa 'N días' en el informe; §8.6 dibuja gaps sin umbral.

### P412. ¿'Reciente' se mide respecto a 'ahora' o respecto a la próxima fecha de cierre efectiva del repo (p. ej. alertar si faltan menos de 48 h y no hay commits en 3 días)? Un repo que nunca ha tenido commits, ¿entra en 'sin actividad reciente' o es una categoría propia ('sin iniciar')? Un repo creado hace menos de N días, ¿queda excluido de la alerta?

- **Requisitos:** R2.5.3
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define los estados de alerta (sin iniciar / inactivo / activo), evita falsas alertas en repos nuevos y decide si la alerta depende de las fechas de Canvas.
- **Estudio de APIs:** no lo aborda directamente; §9.4 menciona la notificación 'faltan 24 h y el repo no tiene commits'.

### P413. ¿Cuándo deja de evaluarse la alerta de inactividad de un repo: al pasar su última fecha efectiva de cierre (que varía por overrides), al pasar lock_at, al cerrar la tarea manualmente, o nunca? Ligado a esto, ¿cuál es la definición exacta de 'tarea activa' que usan el dashboard y el informe diario, y es automática por fechas o un estado manual (abierta / cerrada / archivada) controlado por el profesor?

- **Requisitos:** R2.5.3, R2.5.6, R2.6.1
- **Área declarada:** 2.5 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita alertar por repos de tareas terminadas, define el ciclo de vida de una tarea y la condición 'si no hay tareas activas no hay informe' de R2.6.1.
- **Opciones planteadas:**
  - Automático por fecha efectiva de cierre por repo
  - Automático por lock_at
  - Estado manual de la tarea
  - Automático con posibilidad de cierre/archivado manual
- **Estudio de APIs:** §9.1: 'tareas con alguna entrega cuyo período esté vigente', sin definir vigente ni cómo interactúa con overrides o con un estado manual.

### P414. Para repos en estado PENDING_MAPPING, QUEUED, CREATING, COLLABORATORS_PENDING o ERROR, ¿se incluyen en las métricas de actividad (como 0 commits / 'sin iniciar') o sólo en el bloque de estado de creación (R2.5.5)? ¿El KPI 'repos sin actividad' cuenta a los que ni siquiera existen en GitHub?

- **Requisitos:** R2.5.3, R2.5.4, R2.5.5
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita doble conteo entre 'problema de creación' y 'sin actividad' y define los denominadores de los KPIs.
- **Estudio de APIs:** §5.2 define la máquina de estados del repo; §8.5 no dice cómo la trata el dashboard de actividad.

### P415. ¿El bloque 'estado general de creación y configuración' del dashboard (R2.5.5) es el mismo componente que la tabla de estado de repos de R2.3.11 (embebido o enlazado), o un resumen con contadores por estado (listos / invitación pendiente / falta mapeo / error) con enlace al detalle? ¿Se muestra en la entrega parcial como parte de la vista de tarea?

- **Requisitos:** R2.5.5, R2.3.11
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija reutilización de componentes y qué se puede demostrar el 16-sep; R2.3.11 es parte del flujo de la parcial y R2.5.5 lo referencia.
- **Estudio de APIs:** §5.6 propone la tabla de estados; §8.5 mapea 2.5.5 a 'máquina de estados de §5.6' sin decir si es la misma vista.

### P416. ¿Cuál es la definición operativa de 'estudiante que aún no ha participado'? Opciones: (a) 0 commits atribuidos como autor; (b) 0 commits como autor, committer o co-autor; (c) además, no ha aceptado la invitación al repo; (d) 0 commits dentro del período de la entrega vigente (no en toda la tarea). ¿Se distinguen en la UI los sub-estados 'sin mapeo GitHub', 'invitación no aceptada' y 'con acceso y 0 commits'?

- **Requisitos:** R2.5.4
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es la regla de negocio central de R2.5.4 y de la situación 'estudiantes sin participación' del informe diario; cada opción cambia la consulta y el texto mostrado.
- **Opciones planteadas:**
  - 0 commits como autor en toda la tarea
  - 0 commits como autor/committer/co-autor
  - Incluye 'invitación no aceptada' como no participación
  - 0 commits en el período de la entrega vigente
- **Estudio de APIs:** §8.5: 'integrantes con 0 commits atribuidos'; §5.4 distingue 201 (invitación pendiente) de 204 (acceso directo) pero no cruza ambos conceptos.

### P417. ¿Cuál es la regla de atribución de un commit a un estudiante y su orden de precedencia: 1) login (author.username del webhook o author.login de REST), 2) email del autor igual a un email conocido, 3) nombre normalizado? ¿Qué emails se consideran conocidos: el noreply de GitHub (ID+login@users.noreply.github.com, parseable), el email público del perfil (GET /users/{login} sólo lo trae si es público), el email de Canvas (cuya obtención vía API no está garantizada) o emails agregados a mano por el docente? ¿El match por nombre se aplica automáticamente (riesgo de homónimos) o sólo se sugiere para confirmación manual?

- **Requisitos:** R2.5.4, R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el algoritmo de resolución de student_id en CommitRecord y cuántos commits quedan 'sin atribuir'; de esto depende no acusar injustamente a un estudiante de no participar.
- **Opciones planteadas:**
  - Sólo login
  - Login + email conocido
  - Login + email + nombre normalizado automático
  - Login + email; nombre sólo como sugerencia manual
- **Estudio de APIs:** §8.4 propone fallback por email conocido (Canvas) y nombre normalizado; Apéndice A.3 advierte que include[]=email en Canvas no está documentado y sugiere /users/:id/profile.

### P418. Cuando el dashboard muestre 'N commits sin atribuir' con sus emails/nombres, ¿el docente puede asociar manualmente un email a un estudiante? Si lo hace, ¿se reatribuyen retroactivamente todos los commits históricos con ese email (recalculando agregados y alertas), y la asociación aplica a todos los repos del curso o sólo a ese repo? ¿Mismo comportamiento si cambia el mapeo Canvas↔GitHub de un estudiante (nuevo login): los commits del login antiguo se conservan atribuidos?

- **Requisitos:** R2.5.4, R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define una tabla de alias por estudiante, la necesidad de recomputar agregados y el flujo de UI de corrección de atribución.
- **Estudio de APIs:** §8.4 sugiere que el docente pueda mapear emails desconocidos a mano; no aborda retroactividad ni alcance.

### P419. ¿La atribución por login guarda el login textual o el id numérico de GitHub? Un estudiante puede renombrar su cuenta: el login del payload cambia y un mapeo textual deja de coincidir. El payload push sólo trae commits[].author.username (sin id). ¿Se resuelve el id con GET /users/{login} al momento del mapeo y se re-resuelve el login periódicamente o ante fallo de atribución?

- **Requisitos:** R2.5.4, R2.2.4
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina la clave del mapeo estudiante↔GitHub usada por todo el monitoreo y su robustez ante renombres de cuenta.
- **Estudio de APIs:** no lo aborda (§6.1 guarda el login canónico devuelto por GET /users/{username}, sin mencionar el id).

### P420. ¿Los trailers Co-authored-by en el mensaje del commit cuentan como participación del co-autor (para R2.5.4 y R2.5.8)? Si sí, ¿el commit cuenta 1 para cada uno o se reparte (0,5/0,5)? ¿Se valida que el co-autor sea integrante del repo y cómo se muestra en el timeline?

- **Requisitos:** R2.5.4, R2.5.8, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia el modelo (N autores por commit), las sumas de la comparación de grupo y el parser de mensajes.
- **Opciones planteadas:**
  - No se consideran
  - Cuentan 1 completo para cada autor
  - Se reparte el crédito
  - Se muestran pero no cuentan
- **Estudio de APIs:** §8.4: 'parsear el trailer del mensaje si quieren crédito compartido'.

### P421. Si un repo grupal tiene commits sin atribuir, ¿se sigue marcando a un integrante con 0 commits como 'sin participación' o se degrada a 'participación no verificable' hasta resolver la atribución? ¿Aparece una fila 'Desconocido' en la comparación de integrantes con el conteo de commits no atribuidos?

- **Requisitos:** R2.5.4, R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el texto y la severidad de la alerta ante datos sucios y evita conclusiones injustas en el informe diario.
- **Estudio de APIs:** §8.4: mostrar 'N commits sin atribuir' para no acusar injustamente (R2.5.4); no define el efecto sobre la alerta.

### P422. Un estudiante retirado del curso en Canvas (enrollment inactive/deleted/completed) o que sale de un grupo: ¿desaparece de la lista 'sin participación', se muestra como 'retirado' con sus commits históricos, o se mantiene igual? ¿Sus commits siguen contando en la comparación del grupo y en la actividad del repo? ¿Se marca el momento del retiro en el timeline?

- **Requisitos:** R2.5.4, R2.5.8, R2.2.1
- **Área declarada:** 2.5 / 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita alertar por estudiantes que ya no están y define cómo se conservan los datos históricos (regla de no borrar filas).
- **Estudio de APIs:** §4.4 y §14: marcar deleted_at, no borrar, 'un estudiante que se retira sigue teniendo un repo con historia'; no aborda su tratamiento en las métricas.

### P423. Si Canvas cambia la composición de un grupo a mitad de una tarea (X pasa del grupo A al B): ¿los commits de X en el repo A siguen atribuidos a X y contando en A? ¿X aparece en B como 'sin participación' desde su ingreso o se le mide sólo desde la fecha del cambio? ¿Se registra el cambio como evento en el timeline de ambos repos? ¿Cuándo y cómo se recomputa members_with_zero_commits?

- **Requisitos:** R2.5.4, R2.5.8, R2.5.10, R2.2.3
- **Área declarada:** 2.5 / 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define los disparadores de recomputación de agregados ante cambios de membresía y evita alertas falsas tras reasignaciones.
- **Estudio de APIs:** §8.3 propone members_with_zero_commits_json en RepoStatus; no aborda cambios de membresía.

### P424. ¿Se aprueba la arquitectura de ingesta propuesta por el estudio (webhooks de la GitHub App como fuente principal + polling de reconciliación cada 15 min con ETag) o se opta por polling puro (sin URL pública, más simple, con latencia de minutos)? ¿Cuál es la latencia máxima aceptable entre un push y su aparición en el dashboard (criterio de aceptación)?

- **Requisitos:** R2.5.1, R2.5.2, R2.5.10
- **Área declarada:** 2.5 / infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Decide si la entrega parcial ya requiere URL pública para webhooks, el diseño del receptor, los jobs del worker y el requisito no funcional de frescura de datos.
- **Opciones planteadas:**
  - Webhooks + reconciliación (propuesta del estudio)
  - Sólo polling cada N minutos
  - Webhooks sin reconciliación (no recomendado por el estudio)
- **Estudio de APIs:** §8.1 (webhooks), §8.2 (reconciliador cada 15 min con ETag), §12 (worker ④ backfill_commits cada 15 min). Recomienda ambos, no está aprobado por el equipo.

### P425. ¿A qué eventos de webhook se suscribe la App y para qué se usa cada uno: push (commits), create/delete (ramas y tags), repository (renombrado/borrado/archivado/transferido), member (colaborador agregado, es decir invitación aceptada), member_invite? Hay que confirmar contra la API real que member con action added se dispara al aceptar la invitación de colaborador y si existe algún evento para invitación rechazada o expirada.

- **Requisitos:** R2.5.2, R2.5.10, R2.5.5
- **Área declarada:** 2.5 / infraestructura
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Define qué eventos puede mostrar el timeline (invitación aceptada, creación) y cómo se actualiza el estado COLLABORATORS_PENDING sin polling.
- **Estudio de APIs:** §8.1 lista push, create, delete, repository, member, member_invite 'según disponibilidad' sin verificar semántica.

### P426. El evento push incluye como máximo 20 commits en commits[]; un push mayor (p. ej. un estudiante que sube un proyecto existente con 300 commits) exige completar vía API usando before/after (la Compare API está limitada a 250 commits; alternativa: listar GET /commits?sha=after hasta llegar a before). ¿Cómo se implementa este relleno y qué tope de commits por push se ingiere antes de marcar el repo para backfill completo?

- **Requisitos:** R2.5.2, R2.5.10
- **Área declarada:** 2.5 / infraestructura
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin este manejo el dashboard subcuenta silenciosamente los pushes grandes; el tope es una decisión de alcance del equipo.
- **Estudio de APIs:** no lo aborda (§8.1 describe commits[] sin mencionar el límite de 20).

### P427. Ante un push con forced: true (historial reescrito) o el borrado de una rama, ¿los commits que dejan de ser alcanzables se eliminan de las métricas, se conservan marcados como 'huérfanos', o se ignora el caso? El polling con since= nunca detecta eliminaciones. ¿El timeline muestra un evento 'historial reescrito por X' con el before/after?

- **Requisitos:** R2.5.2, R2.5.4, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si las métricas reflejan el estado actual del repo o todo lo que alguna vez se subió, y si un estudiante puede 'borrar' su participación o la de otro.
- **Opciones planteadas:**
  - Conservar todo (append-only) y marcar huérfanos
  - Reconciliar contra el árbol actual y eliminar huérfanos de las métricas
  - Ignorar el caso
- **Estudio de APIs:** no lo aborda

### P428. Al incorporar un repo al sistema (creación por el worker, reinstalación de la App o reinicio con BD vacía), ¿se hace backfill completo del historial? ¿Se incluyen los commits heredados del repo base/plantilla (marcados como 'base')? ¿Hay tope de commits o páginas por repo para el backfill inicial? ¿Se soporta 'adoptar' repos creados fuera de la app cuyo historial es previo a la instalación?

- **Requisitos:** R2.5.2, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina el costo del arranque (60 repos × páginas), la completitud del timeline y si existe la funcionalidad de adopción de repos externos.
- **Estudio de APIs:** §8.2: 'hay que hacer un backfill completo la primera vez que un repo entra al sistema'; no aborda topes ni repos externos.

### P429. ¿La clave del registro de commit es (repository_id, sha) en lugar de sha solo (el mismo SHA puede existir en dos repos con historia compartida, p. ej. forks o repos clonados de una plantilla común)? ¿Se deduplican entregas repetidas del webhook por X-GitHub-Delivery además de por SHA? ¿Los agregados (RepoActivityDaily, RepoStatus) se recomputan desde los commits (derivables e idempotentes) o se incrementan en línea (riesgo de doble conteo al reprocesar)?

- **Requisitos:** R2.5.2, R2.5.7, R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija el esquema y la garantía de idempotencia del pipeline de ingesta; sin ella, reintentos de webhook duplican commits en los KPIs.
- **Estudio de APIs:** §8.3 propone sha como PK y una tabla agregada 'actualizada en cada ingesta' sin especificar recomputación ni deduplicación de entregas.

### P430. El receptor de webhooks y el reconciliador pueden procesar el mismo repo simultáneamente, y los eventos pueden llegar desordenados. ¿Se serializa el procesamiento por repo (lock) y cómo se garantiza que last_commit_at nunca retroceda ni que un mismo día se agregue dos veces? ¿Qué pasa con un webhook que llega durante un backfill en curso?

- **Requisitos:** R2.5.2, R2.5.3
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la estrategia de concurrencia del worker y evita inconsistencias visibles en el dashboard.
- **Estudio de APIs:** no lo aborda (§5.5 habla de lock por sujeto sólo para creación de repos).

### P431. Si un repositorio es borrado, renombrado, transferido o archivado en GitHub fuera de la app (evento repository), ¿cómo lo refleja el dashboard: estado 'repo no encontrado', re-creación automática por el worker, alerta al docente? ¿Y si la App es desinstalada de la org o el webhook devuelve errores repetidos (GitHub deja de entregar hooks que fallan)?

- **Requisitos:** R2.5.5, R2.5.2
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define nuevos estados en la máquina de estados del repo y una alerta de salud de la integración visible en el dashboard.
- **Estudio de APIs:** no lo aborda

### P432. ¿Se muestra 'última actualización' en el dashboard y a qué corresponde: último webhook recibido para la tarea, última reconciliación exitosa por repo, o ambos? ¿Existe un botón 'Actualizar ahora' que dispare la reconciliación en background (sin bloquear el render), con cooldown (p. ej. una vez por minuto por tarea) y restringido a ciertos permisos? ¿Qué se muestra si la reconciliación lleva más de X minutos fallando (banner 'datos posiblemente desactualizados')?

- **Requisitos:** R2.5.1, R2.5.2
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Concreta la usabilidad de la frescura de datos y protege el rate limit; el botón manual es compatible con el enunciado sólo si el render por defecto no espera a la API.
- **Estudio de APIs:** §4.4 y §7.4 recomiendan mostrar 'última sincronización' y botón 'sincronizar ahora' para Canvas; no lo detalla para la ingesta de GitHub.

### P433. ¿La precomputación es incremental al ingerir cada evento, o un job periódico recalcula agregados y alertas (cada 5, 10 o 15 min)? ¿Las alertas 'sin actividad reciente' y 'sin participación' se evalúan al momento de la consulta (sobre last_commit_at, barato) o se materializan por el job con marca de tiempo (necesario para el informe diario y para conservar histórico de alertas)?

- **Requisitos:** R2.5.2, R2.5.3, R2.5.4
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la frecuencia de los workers, la latencia de las alertas y si existe historial de alertas consultable.
- **Estudio de APIs:** §8.3: RepoStatus 'actualizada en cada ingesta'; §12: worker de backfill cada 15 min; no separa cálculo de alertas.

### P434. ¿El docente puede marcar una alerta (repo inactivo, estudiante sin participación, grupo desbalanceado) como 'vista' o 'justificada' (p. ej. el grupo avisó que trabajará la última semana) para silenciarla en el dashboard y en el informe diario durante un plazo? ¿Se registra quién y cuándo la silenció?

- **Requisitos:** R2.5.3, R2.6.2
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define una tabla de reconocimiento de alertas y evita que el informe repita día a día situaciones ya gestionadas.
- **Estudio de APIs:** no lo aborda

### P435. ¿Cómo se define el período de la entrega k para R2.5.7: (cierre_{k-1}, cierre_k]? ¿Desde dónde parte el período de la primera entrega: creación del repo, unlock_at de la tarea en Canvas, creación de la tarea en la app, o primer commit? ¿Existe un período 'post-cierre final' para actividad posterior a la última entrega? ¿El límite es due_at o lock_at?

- **Requisitos:** R2.5.7, R2.5.6
- **Área declarada:** 2.5 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es la regla de negocio que hace consultable la actividad por entrega; sin ella no se puede implementar el filtro ni las líneas de cierre en el gráfico.
- **Opciones planteadas:**
  - Inicio en creación del repo
  - Inicio en unlock_at de Canvas
  - Inicio en creación de la tarea en la app
  - Inicio en primer commit
- **Estudio de APIs:** §8.5: filtrar commits por [entrega_anterior.due, entrega_actual.due]; no define el inicio del primer período ni el post-cierre.

### P436. Dado que la fecha de cierre efectiva varía por sección, estudiante o grupo (overrides), ¿el filtro 'período de la entrega' usa la fecha efectiva de CADA repo (ventanas distintas por fila) o una fecha única para toda la tarea (¿cuál: base, mínima, máxima)? En el gráfico agregado de la tarea, ¿cómo se marcan las líneas de cierre cuando hay varias fechas? Para grupos cuyos integrantes tienen fechas distintas, ¿se adopta la propuesta max() de los integrantes y se señala la heterogeneidad?

- **Requisitos:** R2.5.7, R2.5.6, R2.4.2, R2.4.3
- **Área declarada:** 2.5 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina si el período es un atributo de la entrega o de (entrega, repo), lo que cambia consultas, gráficos y la coherencia con la captura de versión de R2.4.5.
- **Opciones planteadas:**
  - Ventana por repo según fecha efectiva
  - Fecha única de la tarea (base)
  - Fecha única (máxima de todos los overrides)
  - Ventana por repo + líneas múltiples en el gráfico
- **Estudio de APIs:** §7.3 propone max() de las fechas efectivas para grupos y mostrarlo en la UI; §8.5 no cruza períodos con overrides.

### P437. ¿Cómo se muestran los commits posteriores al cierre efectivo de una entrega pero anteriores al siguiente período: como parte del siguiente período, como 'actividad tardía' de la entrega vencida, o ambos? ¿Se agrega un indicador por repo de 'commits después del cierre / no incluidos en la versión registrada' (útil para detectar trabajo fuera de plazo y explicar diferencias con el SHA capturado)?

- **Requisitos:** R2.5.7, R2.5.10, R2.4.7
- **Área declarada:** 2.5 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define una métrica y un texto de UI relevantes para corrección, y la coherencia entre el dashboard y la versión capturada.
- **Estudio de APIs:** §7.5 registra el SHA al cierre y menciona que la actividad puede continuar; no aborda su visualización.

### P438. ¿Cuál es la enumeración de 'estado' de una entrega para R2.5.6: p. ej. programada (aún no abre), abierta, cerrada (vencida, snapshot pendiente), capturada, capturada parcialmente (algunos repos sin commits o con error), en corrección, corregida? ¿Cómo se resume cuando, por overrides, algunos repos ya cerraron y otros no ('cierra entre el 16-09 y el 20-09; 40/60 versiones capturadas')?

- **Requisitos:** R2.5.6, R2.4.5
- **Área declarada:** 2.5 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin enumeración cerrada no hay criterio de aceptación para 'sus fechas y su estado' ni para la UI de la lista de entregas.
- **Estudio de APIs:** §5.2 tiene snapshot_status por (delivery, repo) y §7.5 define CAPTURED/NO_COMMITS; no existe estado agregado de la entrega.

### P439. Si la fecha de una entrega cambia en Canvas después de que el dashboard ya la usó (períodos calculados o versión capturada), ¿se recalculan períodos y métricas automáticamente y se muestra un aviso 'fecha modificada el …, antes era …' en el dashboard y en el timeline? ¿Se conserva el historial de fechas anteriores?

- **Requisitos:** R2.5.6, R2.5.7, R2.4.4
- **Área declarada:** 2.5 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la reactividad del dashboard a cambios en Canvas y qué explicaciones ve el docente cuando los números cambian solos.
- **Estudio de APIs:** §7.4 propone log de auditoría de cambios de fecha y reprogramar el snapshot; no aborda el impacto en el dashboard.

### P440. Si la tarea de Canvas asociada a una entrega es eliminada o despublicada, o si no tiene due_at (null): ¿qué muestra el dashboard ('entrega eliminada en Canvas', 'sin fecha'), cómo se delimita su período y se desactivan las alertas relativas a fechas? ¿Una tarea con una sola entrega sin fecha puede tener dashboard de períodos?

- **Requisitos:** R2.5.6, R2.5.7, R2.5.3
- **Área declarada:** 2.5 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cubre estados degradados que aparecerán en pruebas reales y define comportamientos por defecto para períodos abiertos.
- **Estudio de APIs:** §7.3 comenta due_at null sólo en overrides; no aborda eliminación de la tarea Canvas ni entregas sin fecha.

### P441. ¿Qué métricas se comparan entre integrantes de un grupo: número de commits, días distintos con actividad, líneas +/−, archivos tocados, porcentaje del total del repo, fecha del primer y último commit? ¿Se adopta la advertencia del estudio de no priorizar líneas? ¿La comparación es por toda la tarea, por período de entrega, o seleccionable?

- **Requisitos:** R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define las columnas de la comparación, si se requieren líneas (costo de ingesta) y el criterio de aceptación de R2.5.8.
- **Estudio de APIs:** §8.5: 'commits/líneas/días activos por autor dentro del repo'; advierte que líneas es una métrica pésima y recomienda commits y días activos.

### P442. ¿Cómo se visualiza la comparación de integrantes (barras apiladas por integrante y período, tabla, sparklines por integrante) y existe un umbral de alerta de desbalance (p. ej. un integrante concentra más de X % de los commits, o alguien tiene menos de Y % con al menos Z commits totales para evitar falsos positivos en repos con 3 commits)? ¿Es configurable, quién lo configura, y aparece en el informe diario?

- **Requisitos:** R2.5.8, R2.5.9, R2.6.2
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Convierte R2.5.8 en una alerta accionable o sólo en una visualización; define parámetros y su lugar en la configuración.
- **Opciones planteadas:**
  - Sólo visualización sin alerta
  - Alerta con umbral fijo
  - Alerta con umbral configurable por curso/tarea
- **Estudio de APIs:** §8.5 propone 'índice de concentración' como señal, no como veredicto, sin umbral.

### P443. En tareas individuales, ¿la sección de comparación de integrantes se oculta, o se reemplaza por una comparación del estudiante contra la mediana del curso o de su sección? ¿Se comparan grupos entre sí (ranking de grupos) o se considera indeseable mostrarlo?

- **Requisitos:** R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el comportamiento de la vista según configuración individual/grupal (R2.3.3) y el alcance de la comparación.
- **Estudio de APIs:** no lo aborda

### P444. ¿Qué métricas o visualizaciones adicionales se comprometen para R2.5.9 (el estudio sugiere elegir 2–3)? Candidatas: heatmap día × hora, curva acumulada de commits con líneas de cierre, índice de concentración, columna 'días desde el último commit' ordenable, ritmo (días activos / días transcurridos), enlace compare entre versiones de entregas consecutivas, tamaño promedio de commit, porcentaje de actividad nocturna o de fin de semana. La lista elegida debe convertirse en requisitos con criterio de aceptación y justificación defendible el 7-oct.

- **Requisitos:** R2.5.9
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.5.9 es abierto; sin decisión no hay alcance ni pruebas, y la justificación metodológica se evalúa en la validación individual.
- **Estudio de APIs:** §8.5 lista candidatas y advierte contra líneas de código; §7.5 sugiere el compare entre entregas como candidato.

### P445. ¿Se usan los endpoints stats/* de GitHub (contributors, punch_card, code_frequency; respuesta 202 asíncrona con caché invalidada por push) para backfill o métricas, o todo se calcula localmente desde los commits ingeridos? Si se usan: política de reintento ante 202, frecuencia, y qué prevalece cuando difieren de los datos propios (p. ej. por atribución distinta).

- **Requisitos:** R2.5.8, R2.5.9
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita dos fuentes de verdad inconsistentes y define un worker adicional con manejo de 202.
- **Estudio de APIs:** §8.5: tabla de endpoints stats/* y advertencia del 202; 'nunca llamen esto desde el render'.

### P446. ¿Se ofrece una vista de seguimiento a nivel de curso (todas las tareas activas con sus alertas consolidadas) además del dashboard por tarea, o queda fuera de alcance? El informe diario necesita esa consolidación de todos modos; ¿se reutiliza como página web del informe?

- **Requisitos:** R2.5.1, R2.6.1
- **Área declarada:** 2.5 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define una pantalla adicional y la reutilización entre dashboard e informe diario.
- **Estudio de APIs:** §9.1 construye la consolidación para el informe y sugiere guardarlo como página web; no propone una vista de curso.

### P447. ¿Qué tipos de evento incluye el timeline por repo? Candidatos: commits; marcadores de entrega (fecha efectiva del repo, SHA/tag, enlace tree/<sha>, o 'sin commits al cierre'); creación del repo; invitaciones enviadas y aceptadas; cambios de integrantes; creación y borrado de ramas y tags; force push; cambios de fecha de entrega; gaps de inactividad; comunicaciones enviadas al estudiante; corrección publicada. Cada tipo elegido requiere una fuente de datos.

- **Requisitos:** R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el modelo de eventos del timeline (¿tabla unificada de eventos o unión de tablas?) y qué webhooks o registros internos deben persistirse.
- **Estudio de APIs:** §8.6: commits (autor, mensaje, hora, tamaño), marcador de entrega con link al SHA, gaps de inactividad; no incluye invitaciones ni ramas.

### P448. ¿Cómo se navega el timeline con cientos de commits: agrupación por día o por push, paginación o scroll infinito, colapsar rangos, zoom por período de entrega? ¿Filtros por integrante, por período y por rama? ¿Cada commit enlaza a github.com/O/R/commit/<sha> y cada entrega a tree/<sha>? ¿Se muestra el mensaje completo o sólo la primera línea?

- **Requisitos:** R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la interacción y el criterio de aceptación de 'revisar fácilmente' con volúmenes reales.
- **Estudio de APIs:** §8.6 propone filtro por autor y por rango de entrega y una línea vertical; no aborda paginación ni agrupación.

### P449. ¿Cómo se identifican los 'principales cambios' que exige R2.5.10: todos los commits se muestran igual, se destacan por tamaño (líneas/archivos, depende de si se registran líneas), por ser merges de PR, por tags creados por los estudiantes, o el docente puede marcar hitos manualmente en el timeline?

- **Requisitos:** R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es el criterio de aceptación literal del párrafo final de 2.5; sin definición la vista no puede evaluarse.
- **Opciones planteadas:**
  - Sin destacar
  - Por tamaño del commit
  - Por merges/PRs/tags
  - Hitos marcados manualmente por el docente
- **Estudio de APIs:** §8.6 muestra +/− por commit pero no define 'principal'.

### P450. ¿El timeline muestra, entre dos marcadores de entrega, un resumen de participación del tramo ('3 commits de jperez, 0 de msoto') para cumplir 'qué integrantes participaron' en cada entrega, o basta con el autor en cada commit? ¿Se marca el tramo con integrantes sin commits?

- **Requisitos:** R2.5.10, R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define un agregado por (repo, período, integrante) y su presentación en el timeline.
- **Estudio de APIs:** no lo aborda (§8.6 muestra autor por commit).

### P451. ¿Qué muestran exactamente los estados vacíos: tarea sin entregas vinculadas, tarea sin repos aún (todos pendientes de mapeo), repo creado sin commits de estudiantes (sólo el commit inicial de plantilla), ingesta nunca ejecutada, webhook aún no recibido? Textos, llamada a la acción (p. ej. 'ir a mapeo de estudiantes') y si el commit inicial cuenta como 'actividad'.

- **Requisitos:** R2.5.1, R2.5.2, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Los estados vacíos son lo primero que verá el corrector al crear una tarea; definen textos de UI y evitan gráficos rotos.
- **Estudio de APIs:** no lo aborda

### P452. ¿Qué permiso controla el acceso al dashboard y al timeline? ¿Todo ayudante ve la tarea completa o sólo los repos que tiene asignados para corregir? ¿Quién puede cambiar umbrales (N días, desbalance), silenciar alertas y pulsar 'Actualizar ahora'? La tabla de permisos propuesta en el estudio no incluye un permiso de monitoreo.

- **Requisitos:** R2.5.1, R2.5.10, R2.1.8, R2.7.1
- **Área declarada:** 2.5 / 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Completa el modelo RBAC de R2.1.8 con los permisos de monitoreo y define filtros por asignación en las vistas.
- **Opciones planteadas:**
  - Todos los roles ven todo el dashboard
  - Ayudantes ven sólo repos asignados
  - Permiso explícito monitoring.view + monitoring.configure
- **Estudio de APIs:** §3.4: tabla de permisos (course.manage, assignment.manage, repo.provision, grading.*, student.communicate, report.subscribe) sin permiso de monitoreo.

### P453. ¿Se muestran a profesores y ayudantes los emails y nombres de autor de los commits sin atribuir (necesarios para mapearlos manualmente) o sólo un identificador ofuscado? ¿Se muestran emails de estudiantes ya mapeados en el dashboard?

- **Requisitos:** R2.5.4, R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el tratamiento de datos personales de terceros presentes en los commits y el contenido de la UI de atribución.
- **Estudio de APIs:** §8.4 propone mostrar la lista de emails desconocidos al docente.

### P454. ¿El dashboard y la comparación de integrantes se pueden exportar (CSV, XLSX, PDF) o compartir mediante enlace permanente con filtros aplicados? ¿O la exportación queda explícitamente fuera de alcance?

- **Requisitos:** R2.5.1, R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define alcance y un posible requisito no funcional adicional.
- **Estudio de APIs:** no lo aborda

### P455. ¿El dashboard permite filtrar y agrupar por sección y por estado del repo, ordenar la tabla por 'días desde el último commit', por número de integrantes sin participación o por sección, y aplicar un filtro 'sólo con alertas'? ¿Qué filtros se recuerdan entre visitas?

- **Requisitos:** R2.5.1, R2.5.2
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la interacción básica de la tabla principal y su utilidad para cursos con varias secciones.
- **Estudio de APIs:** §5.6 propone filtro 'solo problemas' para la tabla de estado; §8.5 sugiere 'días desde el último commit' ordenable.

### P456. ¿Cuáles son los números objetivo para los criterios de aceptación de rendimiento: máximo de tareas activas por curso, repos por tarea (60, 200), commits por repo, y tiempos (dashboard < 1 s, timeline con 2.000 commits < 2 s)? ¿La tabla de 60+ repos se pagina, se virtualiza o se muestra completa?

- **Requisitos:** R2.5.1, R2.5.2, R2.5.10
- **Área declarada:** 2.5 / infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin cifras no se pueden diseñar índices, agregados ni pruebas de carga que demuestren el 'inmediato' del enunciado.
- **Estudio de APIs:** §2.1 y §2.4 usan 60 estudiantes/60 repos como escenario de rate limit; no fijan criterios de aceptación de la UI.

### P457. Verificar empíricamente el presupuesto de rate limit del reconciliador: 60 repos cada 15 min = 240 GET/h, más 1 GET por commit si se registran líneas, más backfill inicial. Confirmar que las respuestas 304 con If-None-Match no descuentan del límite primario, que el ETag es estable mientras since= no cambia, y medir el costo real del backfill de 60 repos con historial.

- **Requisitos:** R2.5.2
- **Área declarada:** 2.5 / infraestructura
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Valida la viabilidad de la frecuencia de polling elegida y del registro de líneas antes de fijarlos en el spec.
- **Estudio de APIs:** §2.4 ('las conditional requests con 304 no descuentan del rate limit primario') y §8.2.

### P458. Verificar empíricamente qué traen el payload push y GET /repos/{o}/{r}/commits cuando el email del autor no está asociado a ninguna cuenta de GitHub (¿author.username ausente? ¿author null en REST?), cuando el commit se hace desde la web de GitHub, con el email noreply de GitHub, con Co-authored-by, y cuando author y committer difieren (rebase por otro integrante). Los resultados fijan la regla de atribución del spec.

- **Requisitos:** R2.5.4, R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** La regla de atribución (R2.5.4) sólo puede escribirse con precisión conociendo los campos reales que llegan en cada caso.
- **Estudio de APIs:** §8.4 describe los casos (author null, ediciones web, co-autores, merges) sin evidencia empírica.

### P459. ¿Hasta cuándo se sigue ingiriendo actividad de los repos de una tarea: mientras la App esté instalada, hasta N días después del último cierre efectivo, o hasta que el profesor archive la tarea? ¿Se conservan los payloads crudos de webhooks para reprocesar ante bugs de atribución y por cuánto tiempo?

- **Requisitos:** R2.5.2, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Controla el consumo de rate limit y almacenamiento a largo plazo y la capacidad de recomputar métricas tras corregir reglas.
- **Estudio de APIs:** no lo aborda

### P460. En una tarea individual, ¿cómo se distingue en el dashboard al estudiante 'mapeado pero sin acceso' (invitación de colaborador no aceptada, 201) del 'con acceso y sin commits' (204 o invitación aceptada)? ¿La aceptación de invitación se detecta por webhook member, por polling de GET /repos/{o}/{r}/invitations, o por ambos, y con qué frecuencia?

- **Requisitos:** R2.5.4, R2.5.5
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la transición COLLABORATORS_PENDING → READY que alimenta tanto R2.5.5 como la interpretación de 'no ha participado'.
- **Estudio de APIs:** §5.4 describe 201/204 y GET /repos/{o}/{r}/invitations; §8.1 lista el evento member 'según disponibilidad'.

### P461. Los conteos de commits y días activos también se pueden inflar (commits vacíos con --allow-empty, ráfagas de commits triviales, commits que solo tocan espacios). ¿La app detecta y marca commits sin cambios (0 archivos) o ráfagas anómalas (N commits en <1 min) para excluirlos o señalarlos en dashboard, comparación de integrantes y timeline? ¿Se presentan las métricas explícitamente como 'señal para revisar, no veredicto' en la UI y en el informe, y qué respuesta prepara el equipo para el examinador del 7-oct ante '¿cómo evitan que un estudiante infle su participación?'

- **Requisitos:** R2.5.4, R2.5.8, R2.5.10, R2.5.9
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina qué se cuenta, cómo se etiqueta en la UI y la defensa metodológica de 2.5.4/2.5.8 ante el profesor.
- **Opciones planteadas:**
  - Marcar/excluir commits sin cambios y ráfagas
  - Mostrar tamaño (archivos) por commit como contexto
  - Solo texto 'señal, no veredicto'
  - No tratar
- **Estudio de APIs:** §8.5 advierte contra líneas de código y propone commits y días activos; §8.4 trata merges y co-autores; no aborda commits vacíos ni inflado deliberado.

### P462. Al crear un repo, GitHub emite webhooks (repository created, push del commit inicial del template, member) que pueden llegar ANTES de que el worker haya persistido la fila del repo en la BD. ¿Cómo se maneja la carrera: se descartan y se confía en el reconciliador, se encolan con reintento hasta que exista la fila, o se persiste una fila 'reservada' (nombre + estado CREATING) antes de llamar a GitHub? ¿Qué pasa con eventos de repos que la app nunca reconocerá (repos ajenos de la org)?

- **Requisitos:** R2.5.2, R2.3.7, R2.3.11
- **Área declarada:** 2.5 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin política, se pierden los primeros eventos o se generan errores ruidosos en el receptor durante el aprovisionamiento masivo.
- **Opciones planteadas:**
  - Reservar fila antes de crear en GitHub
  - Encolar eventos huérfanos con reintento/TTL
  - Descartar y reconciliar cada 15 min
- **Estudio de APIs:** §8.1 describe el receptor de webhooks y §5.5 el worker; no aborda el orden entre la creación del repo y sus primeros eventos.

### P463. ¿Cómo se distingue en el dashboard 'no hay datos aún' (repos recién creados, backfill/webhook pendiente) de 'hubo 0 actividad'? ¿Se muestra un estado explícito ('Aún no hemos recopilado actividad de este repositorio; se actualiza cada 15 min') con la hora de la última ingesta por repo? ¿Un estudiante con 0 commits porque su repo tiene 5 minutos de vida aparece en 'sin participación'?

- **Requisitos:** R2.5.1, R2.5.2, R2.5.3, R2.5.4
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita señalar injustamente a estudiantes y define el estado vacío del dashboard, que el enunciado exige inmediato pero que arranca sin información.
- **Estudio de APIs:** §8.2 describe backfill inicial y reconciliación cada 15 min; §8.4 advierte contra acusar por error; no define la distinción visual 'sin datos' vs 'cero'.

### P464. Para dashboard y timeline: ¿qué interacciones se exigen (tooltips al pasar el mouse, filtro por período de entrega, filtro por autor, clic en commit abre GitHub en nueva pestaña, ordenar por 'días desde último commit')? ¿El umbral de 'sin actividad reciente' es configurable por tarea en la UI o fijo (¿cuántos días?)? ¿Cómo se presentan los commits no atribuidos a un estudiante y cómo el docente los mapea manualmente (email→estudiante) desde la UI?

- **Requisitos:** R2.5.2, R2.5.3, R2.5.4, R2.5.7, R2.5.8, R2.5.10
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija el alcance funcional de las visualizaciones (R2.5) y evita alertas injustas por commits sin atribución.
- **Estudio de APIs:** §8.5 propone 'X configurable' para inactividad y 2–3 extras; §8.4 recomienda mostrar 'N commits sin atribuir' con lista de emails para mapear a mano; §8.6 describe elementos del timeline.

### P465. ¿CommitRecord persiste parent_shas y existe una tabla de ramas (RepoBranch: nombre, head_sha, visto_por_última_vez) o commit_branches, de modo que se pueda (a) detectar merges sin llamar a la API, (b) recalcular alcanzabilidad tras force-push o borrado de rama y marcar commits huérfanos, (c) filtrar el timeline por rama y (d) verificar que el SHA de cada snapshot sigue alcanzable? ¿O se guardan solo commits planos (sha, fechas, autor) y se acepta no poder responder esas preguntas?

- **Requisitos:** R2.5.2, R2.5.3, R2.5.10, R2.4.7
- **Área declarada:** 2.5 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Decide si el modelo soporta las reglas elegidas para merges, force-push y ramas; agregar el grafo después obliga a reingestar todo el historial.
- **Opciones planteadas:**
  - Persistir parents + ramas
  - Persistir solo parents
  - Commits planos sin grafo
- **Estudio de APIs:** §8.3 CommitRecord sin parents ni ramas; §8.4 menciona merges por parents.length > 1 (payload de webhook) sin persistirlo.

### P466. `GET /repos/{o}/{r}/commits?since=` filtra por fecha del commit, no por fecha de push: un commit creado antes de last_synced pero pusheado después (trabajo offline de días, rebase, rama fusionada tarde) nunca será traído por el reconciliador propuesto. ¿Se acepta ese hueco (los webhooks lo cubren salvo caídas), se recorre desde el head de cada rama hasta un SHA ya conocido (graph-walk), se compara `before..after` guardando el último head visto por rama, o se hace backfill completo periódico? ¿Se persiste un cursor de backfill (página/SHA) para reanudar backfills interrumpidos? Verificar con un commit retrodatado pusheado después del último sync.

- **Requisitos:** R2.5.2, R2.5.4, R2.4.7
- **Área declarada:** 2.5
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Un commit invisible para el reconciliador distorsiona 'sin participación' y 'sin actividad' y puede omitir commits previos al cierre; define la estrategia de ingesta de respaldo.
- **Opciones planteadas:**
  - Aceptar el hueco
  - Graph-walk hasta SHA conocido
  - Comparar before..after por rama
  - Backfill completo periódico
- **Estudio de APIs:** §8.2 propone `since: last_commit_synced_at` + ETag como respaldo de webhooks; no advierte esta limitación.

### P467. ¿La atribución commit→estudiante se ALMACENA (columna student_id en CommitRecord más la regla usada, lo que exige un job de reatribución cuando cambian mapeos o alias) o se RESUELVE en consulta (join por login/email/alias vigente: siempre consistente, más costoso)? ¿RepoActivityDaily se normaliza por (repository_id, student_id | author_key, day) para soportar la comparación por integrante y por período, o guarda authors_json por (repo, day)? ¿Los agregados se recalculan íntegros desde CommitRecord (idempotente) o se incrementan en la ingesta?

- **Requisitos:** R2.5.2, R2.5.4, R2.5.7, R2.5.8
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina el costo de las consultas del dashboard, la existencia de un job de reatribución y la posibilidad de doble conteo al reprocesar webhooks.
- **Opciones planteadas:**
  - Atribución almacenada + job de reatribución
  - Atribución resuelta en consulta
  - Agregados normalizados por autor y día
  - Agregados con JSON por día
- **Estudio de APIs:** §8.3 propone student_id nullable en CommitRecord (atribución almacenada) y RepoActivityDaily con authors_json; §8.4 fallback por email/nombre.

### P468. ¿El timeline se sirve desde una tabla unificada de eventos por repositorio (TimelineEvent: repository_id, kind, occurred_at, payload_json, referencia a la entidad origen) que cada worker alimenta, o se compone en consulta uniendo commits, snapshots, cambios de membresía, invitaciones, comunicaciones y cambios de fecha? Si es tabla: ¿cómo se evita la divergencia con las tablas origen (reprocesos, recapturas, borrados lógicos) y se garantiza idempotencia por (kind, source_id)? ¿Los 'gaps de inactividad' se calculan al vuelo o se materializan como eventos?

- **Requisitos:** R2.5.10, R2.5.6
- **Área declarada:** 2.5
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia el diseño de todos los workers (deben o no emitir eventos) y el rendimiento de la vista con cientos de commits.
- **Opciones planteadas:**
  - Tabla unificada de eventos
  - Unión en consulta
  - Tabla solo para eventos no-commit + commits aparte
- **Estudio de APIs:** §8.6 describe el timeline 'alimentado 100% desde su BD' sin definir su modelo.

### P469. ¿Las alertas (repo inactivo, estudiante sin participación, invitación sin aceptar, repo en error, grupo desbalanceado) se modelan como entidad con ciclo de vida (kind, target, first_detected_at, last_detected_at, resolved_at, silenced_until, silenced_by) que el job evaluador abre y cierra, o se recalculan como consulta en cada render e informe sin estado? Si son entidad: ¿el informe diario puede distinguir 'nuevo hoy' de 'persiste desde hace N días' y enlazar cada informe a las alertas exactas que incluyó (ReportItem)?

- **Requisitos:** R2.5.3, R2.5.4, R2.6.1, R2.6.2
- **Área declarada:** 2.5 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si existe historial de alertas, cómo se silencian y si el informe es reproducible; una alerta sin estado no puede decir desde cuándo persiste.
- **Opciones planteadas:**
  - Entidad Alert con ciclo de vida
  - Consulta sin estado
  - Híbrido: consulta + tabla de silenciados
- **Estudio de APIs:** §8.5 y §9.1 describen las reglas de alerta como consultas; no proponen entidad ni ciclo de vida.

---

## 2.6

### P470. ¿Qué pasa con la comunicación ENTRANTE del estudiante? Los mensajes salen con el token del profesor, así que las respuestas del estudiante a una Conversation, a un comentario de entrega o los comentarios en un anuncio llegan a la bandeja/SpeedGrader del profesor en Canvas, no a la app. ¿La app (a) lee periódicamente esas respuestas y las muestra al equipo docente junto al estudiante/repo (útil para 'registré mal mi usuario', 'no me llega la invitación', 'solicito recorrección'); (b) declara explícitamente que las respuestas se gestionan solo en Canvas; (c) marca cada mensaje automático como tal ('Mensaje automático de <app>; para ayuda escribe a X') y bloquea comentarios en los anuncios generados (lock)? ¿Cómo evita que el profesor reciba 60 correos de Canvas por respuestas a mensajes que no escribió?

- **Requisitos:** R2.6.5, R2.6.6, R2.6.7, R2.2.5
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Decide si existe un canal de soporte cerrado para el estudiante y si la app necesita scopes de lectura de conversations; fija el pie de todos los mensajes automáticos y la configuración de anuncios.
- **Opciones planteadas:**
  - Leer respuestas de Canvas y mostrarlas en la app
  - Solo en Canvas, declarado como limitación
  - Etiquetar mensajes como automáticos con contacto de ayuda
  - Bloquear comentarios en anuncios generados
- **Estudio de APIs:** §9.3 y §9.4 solo cubren envío (POST /conversations, add_message, outbox); no aborda lectura de respuestas ni comentarios en anuncios.

### P471. ¿Existe un tope o consolidación de mensajes automáticos por estudiante y día considerando TODOS los tipos y tareas (repo disponible ×3 tareas, recordatorios 48h/24h, invitación pendiente, sin actividad, cambio de fecha, nota publicada), o cada evento envía su propio mensaje? Casos de ráfaga: tarea creada con cierre en 2 días (repo disponible + 48h + 24h casi juntos); estudiante que reentrega la tarea de registro con el mismo usuario válido tres veces (¿tres comentarios 'confirmado' o uno solo?). Opciones: sin tope; digest diario por estudiante; supresión de recordatorios cuando ya hubo un mensaje del mismo tipo en N horas; dedupe por contenido.

- **Requisitos:** R2.6.5, R2.6.7, R2.3.12
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define reglas de agrupación/supresión en el outbox y evita que el estudiante ignore los mensajes por saturación.
- **Opciones planteadas:**
  - Sin tope
  - Digest diario por estudiante
  - Supresión por tipo en ventana de N horas
  - Dedupe de confirmaciones idénticas
- **Estudio de APIs:** §9.4 propone outbox con unicidad por (kind, target, delivery_id) y flags por tarea; no aborda un tope por estudiante ni consolidación entre tipos o tareas.

### P472. En mensajes a integrantes de un grupo, ¿se nombra a los compañeros con información pendiente ('falta que M. Soto registre su usuario' / 'A. Díaz no ha aceptado su invitación') o solo se indica el conteo ('falta 1 integrante') por privacidad entre pares? ¿Se informa a un estudiante de la extensión individual otorgada a un compañero cuando eso mueve la fecha efectiva del repo grupal? ¿Quién decide el nivel de detalle (fijo, o configurable por el profesor)?

- **Requisitos:** R2.6.5, R2.6.7, R2.2.6
- **Área declarada:** 2.6 / 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija las variables permitidas en plantillas grupales y una regla de privacidad entre estudiantes defendible.
- **Opciones planteadas:**
  - Nombrar compañeros pendientes
  - Solo conteo
  - Configurable por el profesor
- **Estudio de APIs:** §9.3 recomienda group_conversation=false para privacidad frente al resto del curso; no aborda qué información de compañeros se revela dentro del grupo.

### P473. ¿Qué servicio de email se usa (SMTP Gmail, Resend, SendGrid, Mailgun), con qué dominio remitente y configuración SPF/DKIM para que el informe llegue al gmail de los revisores y no a spam? ¿La cuota diaria del plan gratuito alcanza para curso demo + revisores? ¿Quién crea la cuenta y custodia la API key?

- **Requisitos:** R2.6.3, R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin remitente confiable el revisor no recibirá el informe y R2.6.4 quedará 'no accesible en el uso'.
- **Estudio de APIs:** §9.1 lista SendGrid/Resend/Mailgun/SMTP Gmail y recomienda registrar envíos; no aborda dominio remitente ni cuotas.

### P474. Las Conversations enviadas con el token del profesor vinculador figuran como enviadas por él y las respuestas de los estudiantes llegan a SU bandeja de Canvas, no a la app. ¿La app lee esas respuestas (GET /conversations con el mismo token) para mostrarlas al equipo docente o marcar 'el estudiante respondió', o se documenta como limitación y cada mensaje automático indica explícitamente a quién responder y por qué canal? ¿Se advierte al profesor vinculador de que recibirá respuestas a mensajes que él no escribió y cómo las reconoce (prefijo en el asunto)?

- **Requisitos:** R2.6.5, R2.6.7, R2.1.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define si existe una bandeja de respuestas en la app, el pie estándar de los mensajes y la advertencia en el paso de vinculación de Canvas.
- **Opciones planteadas:**
  - No leer respuestas; instruir en el pie del mensaje
  - Leer y mostrar respuestas por estudiante
  - Prefijar asuntos para que el profesor filtre en Canvas
- **Estudio de APIs:** §9.3 cubre POST /conversations y add_message; no aborda respuestas entrantes ni la bandeja del profesor.

### P475. Los anuncios creados por la app, ¿permiten comentarios de los estudiantes (comportamiento por defecto de Canvas) o se crean cerrados a comentarios (`lock_at` inmediato/`locked`) para evitar hilos que nadie del equipo docente monitorea? ¿Se respeta la configuración del curso que deshabilita comentarios en anuncios? ¿Se guarda el `discussion_topic_id` para editar o eliminar el anuncio desde la app si la fecha vuelve a cambiar antes de que los estudiantes lo lean, y se evita que el anuncio notifique a los propios docentes como ruido?

- **Requisitos:** R2.6.6, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija los parámetros exactos del POST de anuncios, la política de comentarios y si hay acción de edición/borrado de anuncios en la app.
- **Opciones planteadas:**
  - Anuncio abierto a comentarios
  - Anuncio bloqueado a comentarios
  - Configurable por curso
- **Estudio de APIs:** §9.2 lista `lock_at` ('cuándo se cierra a comentarios') y `delayed_post_at` sin fijar valores ni política de edición.

### P476. ¿El `body` de POST /conversations acepta HTML o solo texto plano (¿Canvas auto-enlaza URLs? ¿respeta saltos de línea y listas?) y cuál es su longitud máxima? Esto determina cómo se redactan los mensajes con la URL del repo, los pasos para aceptar la invitación y las fechas, y si una misma plantilla puede servir tanto para Conversations como para el comentario en la submission (que sí acepta HTML) sin mostrar etiquetas crudas al estudiante.

- **Requisitos:** R2.6.5, R2.3.12
- **Área declarada:** 2.6
- **Tipo:** Investigable en docs · **Entrega:** Ambas entregas
- **Por qué importa:** Define el motor de plantillas (texto vs HTML por canal) y las pruebas de renderizado en Canvas.
- **Estudio de APIs:** §9.3 muestra `body` en texto plano con URL; §9.2 indica que `message` de anuncios acepta HTML; no aclara el formato de Conversations.

### P477. ¿Qué define una 'tarea activa' para el informe diario (tiene alguna entrega con fecha futura; desde su creación hasta la última fecha más N días de corrección; marcada activa manualmente por el profesor)? Si el servidor está caído a la hora programada, ¿se envía al recuperarse o se omite ese día? Si un curso no tiene tareas activas pero sí problemas pendientes (repos en error), ¿igual no hay informe? ¿Un usuario suscrito en varios cursos recibe un email por curso o uno consolidado?

- **Requisitos:** R2.6.1, R2.6.2, R2.6.3, R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** La condición 'si no hay tareas activas no hay informe' es literal en el enunciado; su definición decide cuándo se envían emails y cómo se prueba en la revisión.
- **Estudio de APIs:** §9.1: 'tareas con alguna entrega cuyo período esté vigente' y cron 07:00; no define 'período vigente' ni recuperación tras caída ni consolidación por usuario.

### P478. Ciclo de vida posterior al envío de una comunicación: (a) las Conversations se envían con el token del profesor, así que las RESPUESTAS de los estudiantes llegan a la bandeja de Canvas del profesor, no a la app; ¿el texto indica dónde responder, la app lee las respuestas (GET /conversations) y las muestra al docente, o se ignoran? (b) ¿los anuncios se crean con comentarios bloqueados (lock_at / discusión cerrada) o abiertos? (c) ¿se puede RETRACTAR desde la app un anuncio publicado por error (DELETE discussion_topics) o un comentario de entrega, sabiendo que una Conversation no puede retirarse, y se exige confirmación adicional antes de enviar lo irreversible?

- **Requisitos:** R2.6.5, R2.6.6, R2.6.7, R2.3.12
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define expectativas de los estudiantes sobre a quién escriben, evita hilos ruidosos bajo anuncios y da al docente una salida ante errores de comunicación masiva.
- **Opciones planteadas:**
  - Texto 'no respondas a este mensaje; escribe a X'
  - Leer y mostrar respuestas en la app
  - Anuncios con comentarios cerrados por defecto
  - Botón 'eliminar anuncio' con registro; confirmación fuerte para envíos irreversibles
- **Estudio de APIs:** §9.2 menciona lock_at para cerrar comentarios y §9.3 envía Conversations con el token del profesor; no aborda respuestas de estudiantes ni retractación de mensajes.

### P479. Investigar las restricciones de formato de cada canal de Canvas antes de diseñar las plantillas: el body de Conversations, ¿acepta HTML o solo texto plano (¿las URLs se convierten en enlaces?), y cuál es su longitud máxima?; los comentarios de submission (comment[text_comment]), ¿renderizan HTML/enlaces?; los anuncios aceptan HTML. ¿Se define una plantilla por canal (texto plano vs HTML) y se prueba que el enlace al repo sea clicable en la app web y móvil de Canvas del estudiante?

- **Requisitos:** R2.6.5, R2.3.12, R2.6.6, R2.7.6
- **Área declarada:** 2.6
- **Tipo:** Investigable en docs · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un mensaje con HTML crudo o una URL no clicable degrada la usabilidad del enrolamiento y de 2.3.12.
- **Estudio de APIs:** §9.2 indica que message acepta HTML en anuncios; §9.3 y §5.7 escriben body/comentario con URL sin indicar el formato soportado.

### P480. ¿El informe diario se genera todos los días del calendario (incluidos sábados, domingos, feriados y semanas de receso) mientras haya tareas activas, solo días hábiles, o es configurable por curso? Si se omiten días, ¿el siguiente informe cubre el período acumulado y así se indica?

- **Requisitos:** R2.6.1, R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la ventana de datos del informe y evita correos irrelevantes o, al revés, la pérdida de alertas de fin de semana antes de un cierre el lunes.
- **Opciones planteadas:**
  - Todos los días
  - Solo días hábiles con ventana acumulada
  - Configurable por curso
- **Estudio de APIs:** §9.1 fija un cron diario a las 07:00 sin distinguir días de la semana.

### P481. ¿A qué hora local se genera y envía el informe diario, en qué zona horaria se fija (America/Santiago con horario de verano, o UTC fijo), y es esa hora una constante global del sistema o configurable por curso o por suscriptor? ¿Qué pasa el día del cambio de horario (Chile pasa de UTC-4 a UTC-3 el primer fin de semana de septiembre, entre la parcial y la final)?

- **Requisitos:** R2.6.1, R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el cron del job, el manejo de DST, la ventana «últimas 24 h» y el criterio de aceptación «el informe llega antes de las HH:MM hora de Chile». Si es configurable, agrega un campo al curso o al perfil y una UI.
- **Opciones planteadas:**
  - 07:00 fijo America/Santiago
  - Hora configurable por curso
  - Hora configurable por suscriptor
  - Hora fija en UTC
- **Estudio de APIs:** §9.1 propone «CRON diario 07:00 America/Santiago»; §14 «Zonas horarias» recomienda guardar UTC y convertir al renderizar; no aborda configurabilidad ni el día del cambio de horario.

### P482. ¿Exactamente entre qué instantes una tarea se considera «activa» para efectos del informe? Inicio: creación de la tarea en la app, unlock_at de la primera entrega en Canvas, publicación del assignment, o creación del primer repositorio. Fin: due_at base de la última entrega, la fecha efectiva más tardía incluyendo overrides de sección y extensiones individuales, lock_at, N días después del cierre para cubrir la corrección, o hasta que la última entrega esté calificada.

- **Requisitos:** R2.6.1, R2.4.1, R2.4.3
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.6.1 hace depender la existencia misma del informe de esta definición. Decide si una extensión individual mantiene «activa» la tarea para todo el curso, si el informe sigue llegando durante la corrección y si una tarea recién creada sin repos ya genera informe.
- **Estudio de APIs:** §9.1 dice «tareas con alguna entrega cuyo período esté vigente» sin definir «período»; §7.3 define fecha efectiva por estudiante con precedencia ADHOC > grupo > sección > base.

### P483. ¿Cuenta como «activa» una tarea cuya assignment de Canvas está sin publicar (published=false), cuyo curso de Canvas está en workflow_state completed/concluded, que aún no tiene ningún repositorio creado, o que el profesor «archivó» o desvinculó en la app? ¿Existe un estado explícito «archivada/pausada» que excluya la tarea del informe sin borrarla?

- **Requisitos:** R2.6.1
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita falsos positivos (informar sobre tareas que no comenzaron o cursos terminados) y obliga a definir estados de tarea en el modelo de datos.
- **Estudio de APIs:** §5.1 sugiere «no creen repos para tareas no publicadas»; §3.2 lista workflow_state del curso; no relaciona ninguno de los dos con el informe.

### P484. Si un profesor o ayudante participa en varios cursos con tareas activas, ¿recibe un email por curso o un único email consolidado con todos sus cursos? Dentro de un curso con varias tareas activas, ¿un informe por curso con una sección por tarea, o un informe por tarea? ¿En qué orden se listan (urgencia, fecha de cierre, alfabético)?

- **Requisitos:** R2.6.1, R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el asunto del correo, la estructura de la plantilla, la clave de idempotencia (curso+fecha vs usuario+fecha) y la granularidad de la suscripción.
- **Opciones planteadas:**
  - Un email por curso
  - Un email consolidado por usuario con todos sus cursos
  - Configurable por suscriptor
- **Estudio de APIs:** §9.1 itera «para cada curso» y envía a los suscritos, lo que implica un email por curso; no considera consolidación por usuario ni orden.

### P485. ¿Cuántos días sin commits convierten un repositorio en «sin actividad reciente» para el informe? «Estudiante sin participación» ¿se mide desde la creación del repo, dentro del período de la entrega vigente (desde el cierre de la entrega anterior), o en las últimas N horas? ¿Los umbrales son globales, por curso, por tarea o por entrega, y son los mismos que usa el dashboard (R2.5.3, R2.5.4)?

- **Requisitos:** R2.6.2, R2.5.3, R2.5.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija las reglas de negocio que producen cada alerta; sin valores concretos no hay criterio de aceptación verificable. Umbrales distintos entre dashboard e informe producen inconsistencias visibles en la revisión.
- **Estudio de APIs:** §8.5 propone «X días, configurable» para 2.5.3 y «0 commits atribuidos» para 2.5.4; §9.1 usa «N días» sin fijar valor ni alcance.

### P486. ¿Cuál es la lista cerrada de «situaciones que requieren atención» incluidas en el informe: repos sin actividad en N días, estudiantes con 0 commits, repos en ERROR o PENDING_MAPPING, invitaciones de GitHub sin aceptar, estudiantes sin usuario GitHub, estudiantes sin grupo en tarea grupal, entregas que vencen en <48 h, snapshots capturados el día anterior (incluyendo NO_COMMITS), cambios de fecha detectados en Canvas, commits sin atribuir, comunicaciones automáticas fallidas, token de Canvas por expirar? ¿Qué sección «positiva» se incluye (commits últimas 24 h, repos activos/total)?

- **Requisitos:** R2.6.2, R2.6.1
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es el contenido del informe. Cada ítem implica una regla, una consulta sobre la BD y una fila en la plantilla; también define qué se considera cumplimiento de R2.6.2.
- **Estudio de APIs:** §9.1 propone 7 secciones (sin actividad N días, 0 commits, ERROR/PENDING, invitaciones, sin mapeo, vencen <48 h, resumen commits 24 h); §7.5 sugiere que NO_COMMITS «es un dato valioso para el informe».

### P487. Cuando una entrega tiene fechas distintas por sección o extensiones individuales, ¿el informe lista cada fecha efectiva (por sección y cada extensión), solo la fecha base, o la más próxima? ¿La alerta «próxima a vencer» se evalúa según la fecha efectiva de cada estudiante/grupo? ¿Se nombran los estudiantes con extensión en el informe?

- **Requisitos:** R2.6.1, R2.6.2, R2.4.2, R2.4.3
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la consulta de fechas para el informe y evita reportar como «vencida» una entrega que para algunos alumnos sigue abierta.
- **Estudio de APIs:** §7.3 recomienda «mostrar en la UI que ese repo tiene fechas heterogéneas»; §9.1 no lo aplica al informe.

### P488. Si hay tareas activas pero ninguna situación requiere atención, ¿se envía igual un informe «sin novedades» con el resumen, o se omite el envío y el historial registra «generado sin alertas»?

- **Requisitos:** R2.6.1
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.6.1 solo fija que sin tareas activas no hay informe; el caso «activas pero sin alertas» cambia la expectativa del docente (silencio = todo bien vs silencio = falla del sistema).
- **Opciones planteadas:**
  - Enviar siempre que haya tareas activas, incluso sin alertas
  - No enviar si no hay alertas; registrar en historial
  - Enviar resumen breve sin secciones de alerta
- **Estudio de APIs:** §9.1 no lo aborda.

### P489. ¿La ventana del informe es «últimas 24 h» fijas o «desde el último informe enviado con éxito» (si el de ayer falló, el de hoy cubre 48 h)? Si el servidor estuvo caído a la hora programada, ¿se genera el informe atrasado al levantarse (fechado ayer), se envía al momento con fecha de hoy, o se omite ese día?

- **Requisitos:** R2.6.1, R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si el job «barre pendientes» o «dispara a hora fija», la clave de unicidad y lo que muestra el historial tras una caída del hosting gratuito.
- **Estudio de APIs:** §7.5 recomienda para snapshots «barrer todo lo vencido y no capturado, no disparar a las 16:30»; no extiende el criterio al informe.

### P490. ¿Cuál es la regla de unicidad del informe (un informe por curso por día calendario local) y qué ocurre si el cron se ejecuta dos veces (reinicio del worker, dos instancias del hosting)? ¿Se reenvía, se ignora, o se regenera solo si cambió el contenido?

- **Requisitos:** R2.6.1, R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita correos duplicados durante la revisión y fija el constraint en BD y el criterio de aceptación «nunca dos correos el mismo día al mismo destinatario».
- **Estudio de APIs:** §9.4 propone outbox con constraint único para comunicaciones a estudiantes; §9.1 no lo hace explícito para el informe.

### P491. ¿El informe se envía como HTML con alternativa texto plano (multipart), solo texto, o resumen + enlace a la versión web dentro de la app? ¿Debe ser legible en móvil? ¿Incluye enlaces profundos a la tarea, repositorio y estudiante en la app y en GitHub? ¿Incluye nombres completos y usuarios GitHub de estudiantes en el cuerpo del correo (fuera de la app) o solo conteos con enlace?

- **Requisitos:** R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la plantilla, la compatibilidad con clientes de correo y la política de privacidad del contenido que sale de la app por email.
- **Estudio de APIs:** §9.1 recomienda «HTML + texto plano» y «resumen + link» a una página web del informe.

### P492. ¿Idioma de todas las comunicaciones (español de Chile), formato de fechas y horas (ej. «mié 16-sep 16:30, hora de Chile»), nombre visible del remitente («Nombre de la app» vs «Curso ICC4201»), dirección From y Reply-To (noreply, correo del equipo, correo del profesor del curso)?

- **Requisitos:** R2.6.4, R2.6.5, R2.6.6
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija criterios de aceptación de contenido y evita que los docentes respondan a una casilla que nadie lee.
- **Estudio de APIs:** No lo aborda.

### P493. Si el proveedor de email rechaza o falla el envío (5xx, cuota agotada, dirección inválida, bounce), ¿cuántos reintentos y con qué backoff, cuándo se marca como fallido definitivamente, se muestra el fallo en la app (banner en el curso, historial) y se notifica a alguien (profesor del curso, administrador)? ¿Los bounces se procesan vía webhook del proveedor o se ignoran?

- **Requisitos:** R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la máquina de estados del envío, el contenido del historial y la observabilidad mínima exigible.
- **Estudio de APIs:** §9.1 pide «registro de envíos (sent_at, status) para poder demostrarlo»; no define reintentos ni bounces.

### P494. ¿Cada informe generado se guarda como documento inmutable consultable en la app (ej. /courses/:id/reports/:fecha), o se regenera bajo demanda con datos actuales? ¿Quién puede verlo (solo suscritos, cualquier miembro del curso, según permiso RBAC), cuánto tiempo se retiene, y se muestra el estado de envío por destinatario?

- **Requisitos:** R2.6.1, R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es la única forma de demostrar R2.6.1–R2.6.4 en la revisión (Consideraciones §4: lo no accesible en el uso no se considera cumplido); define un modelo de datos y una vista.
- **Estudio de APIs:** §9.1 recomienda guardar cada informe como página web y enlazarla desde el email.

### P495. ¿Existe una acción «generar informe ahora» o «enviarme el informe de hoy» para pruebas y para la demo? Si sí, ¿produce un informe adicional marcado como manual o reemplaza el del día, qué rol puede dispararla, y se envía solo a quien lo pide o a todos los suscritos?

- **Requisitos:** R2.6.1, R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin ella el informe diario no puede demostrarse en la revisión presencial; además interactúa con la regla de unicidad.
- **Estudio de APIs:** No lo aborda directamente; §13 recomienda dejar visible en la demo lo que se evalúa.

### P496. ¿El informe que recibe un ayudante contiene la misma información que el del profesor, o se filtra a las entregas y estudiantes que tiene asignados para corregir (R2.7.1) y a lo que su permiso RBAC le permite ver? ¿Un ayudante cuyo rol no puede ver repositorios recibe informe?

- **Requisitos:** R2.6.1, R2.6.2, R2.1.8, R2.7.1
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Obliga a generar variantes por destinatario (o no), afecta rendimiento, privacidad y la definición de los permisos de R2.1.8.
- **Estudio de APIs:** §3.4 propone el permiso report.subscribe para todos los roles; no discute filtrado del contenido por rol.

### P497. Si al generar el informe el refresh token de Canvas del profesor está revocado o expirado, la última sincronización falló, o la GitHub App fue desinstalada de la organización, ¿el informe se genera con datos en BD indicando «datos actualizados hace X h», se omite, o se convierte en un informe de alerta «reconecte Canvas/GitHub»?

- **Requisitos:** R2.6.1, R2.6.2
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el comportamiento ante dependencias caídas, situación probable durante las dos semanas de disponibilidad posterior a la entrega.
- **Estudio de APIs:** §1.1 advierte que sin refresh token guardado el informe no funciona de madrugada; §4.4 sugiere mostrar last_synced_at; no define el comportamiento del informe ante fallo.

### P498. ¿La suscripción al informe es por curso (un toggle por cada curso donde participo), global por usuario, o ambas (global con excepciones por curso)?

- **Requisitos:** R2.6.3
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la tabla de suscripciones, la UI y la semántica del enlace de baja del correo.
- **Opciones planteadas:**
  - Por curso
  - Global por usuario
  - Global con excepciones por curso
- **Estudio de APIs:** §9.1 propone report_subscriptions(user_id, course_id, enabled), es decir por curso.

### P499. Cuando un profesor crea un curso, o cuando se incorpora un co-profesor (R2.1.7) o un ayudante (R2.1.8), ¿queda suscrito por defecto (opt-out) o debe suscribirse (opt-in)? ¿Se le informa del estado en la invitación o en su primer acceso?

- **Requisitos:** R2.6.3, R2.1.7, R2.1.8
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia el comportamiento observable en la demo, el volumen de correo y el texto de la invitación.
- **Opciones planteadas:**
  - Suscrito por defecto (opt-out)
  - No suscrito por defecto (opt-in)
  - Profesores opt-out, ayudantes opt-in
- **Estudio de APIs:** No lo aborda.

### P500. ¿Dónde vive el control de suscripción (perfil del usuario, página del curso, ambos)? ¿El correo incluye un enlace «darse de baja» de un clic sin iniciar sesión con token firmado? Si sí, ¿el token expira, da de baja solo de ese curso o de todo, pide confirmación en una página o es inmediato, y permite volver a suscribirse desde el mismo enlace?

- **Requisitos:** R2.6.3
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija el flujo de UI, los requisitos de seguridad del token y los criterios de aceptación de R2.6.3.
- **Estudio de APIs:** §9.1 recomienda toggle en UI y link de baja con token firmado sin login.

### P501. Al retirar a un ayudante del curso (R2.1.9) o eliminar/archivar el curso, ¿se elimina o desactiva su suscripción automáticamente y qué pasa con un informe ya encolado para él? Si vuelve a incorporarse, ¿recupera su estado anterior de suscripción?

- **Requisitos:** R2.6.3, R2.1.9
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita filtrar información a personas que ya no pertenecen al curso; define efectos en cascada del retiro.
- **Estudio de APIs:** §3.4 menciona reasignar entregas y revocar acceso GitHub al retirar un ayudante; no menciona suscripciones.

### P502. ¿El informe se envía siempre al correo gmail.com de registro (R2.1.2) o el usuario puede configurar otra dirección (por ejemplo, institucional)? Si se permite, ¿se verifica la dirección antes de usarla?

- **Requisitos:** R2.6.3, R2.6.4, R2.1.2
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia el modelo de usuario y agrega un flujo de verificación de correo.
- **Estudio de APIs:** No lo aborda.

### P503. ¿Puede un profesor ver y modificar el estado de suscripción de otros miembros del curso (desuscribir a un ayudante, suscribir a todos), o la suscripción es estrictamente individual/self-service como sugiere el «individualmente» de R2.6.3?

- **Requisitos:** R2.6.3, R2.1.8
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define permisos y si existe una vista de administración de suscripciones en el curso.
- **Estudio de APIs:** No lo aborda.

### P504. ¿Desde qué cuenta de Canvas se envían mensajes directos y anuncios: siempre con el token del profesor que vinculó el curso (opción A), con el token propio de quien dispara la acción si lo tiene (opción B), o híbrido? Con varios profesores (R2.1.7), ¿quién es el emisor «del curso»? ¿Qué pasa si el profesor vinculador revoca su token, sale del curso o pierde el rol teacher en Canvas? ¿Se muestra en la UI «se enviará como Profesor X»?

- **Requisitos:** R2.6.5, R2.6.6, R2.6.7, R2.1.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Los mensajes aparecen en Canvas firmados por esa persona y los estudiantes le responderán a ella. Define el modelo de tokens, los mensajes de error, una advertencia de UI y la viabilidad de comunicaciones automáticas nocturnas.
- **Opciones planteadas:**
  - Siempre el token del profesor vinculador
  - Token del usuario que dispara la acción
  - Híbrido: usuario si tiene token válido, si no el del profesor
  - Emisor configurable por curso entre los profesores
- **Estudio de APIs:** §3.4 propone A como default y B como fallback, y sugiere mostrarlo en la UI; §1.1 exige guardar el refresh token para jobs sin el profesor conectado.

### P505. ¿El equipo docente puede redactar y enviar un mensaje directo libre a un estudiante o grupo desde la app (vista del repositorio o de la entrega), además de los automáticos? Si sí, ¿con texto totalmente libre, plantilla más edición, o solo plantillas predefinidas? ¿Qué roles pueden hacerlo?

- **Requisitos:** R2.6.5, R2.1.8
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.6.5 («cuando sea necesario comunicar información particular... creación, corrección, etc.») admite lectura manual y automática; define una vista, un permiso y el tipo de contenido permitido.
- **Estudio de APIs:** §3.4 propone el permiso student.communicate; §9.3 solo describe el endpoint POST /conversations.

### P506. Para un repositorio grupal, ¿el mensaje va como conversaciones privadas individuales a cada integrante (group_conversation=false) o como un solo hilo con los integrantes del grupo (group_conversation=true, donde se ven entre sí y pueden responder a todos)? ¿Se envía también a integrantes que aún no tienen usuario GitHub mapeado, con un texto distinto?

- **Requisitos:** R2.6.5, R2.6.7, R2.2.3
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Cambia el parámetro de la API, el número de llamadas, la privacidad y la redacción («tu repositorio» vs «el repositorio del grupo»).
- **Estudio de APIs:** §9.3 recomienda group_conversation=false para notificaciones masivas; no distingue el caso de un grupo pequeño ni el de integrantes sin mapeo.

### P507. ¿Cada tipo de mensaje lleva un asunto fijo (máx. 255 caracteres) y se usa force_new para crear una conversación por evento, o se agrega el mensaje a una conversación existente por estudiante y tarea (donde Canvas ignora el asunto)? ¿Se envía siempre context_code=course_X para que el mensaje quede asociado al curso?

- **Requisitos:** R2.6.5, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define cómo se ve el buzón del estudiante (un hilo por tarea vs muchos mensajes sueltos) y qué identificador externo se guarda para trazabilidad.
- **Estudio de APIs:** §9.3 documenta subject (ignorado al reutilizar conversación), force_new, context_code y POST /conversations/:id/add_message.

### P508. ¿Se registra cada mensaje enviado (destinatario, tipo, canal, cuerpo final renderizado, conversation_id de Canvas, quién lo disparó, fecha, estado, error) y se muestra en la app por estudiante, por tarea y por curso? ¿Puede el docente abrir la conversación en Canvas desde la app?

- **Requisitos:** R2.6.5, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el outbox, la vista de historial y un criterio de aceptación demostrable en la revisión.
- **Estudio de APIs:** §9.4 propone notification_outbox(id, kind, target, payload, scheduled_for, sent_at, error) y una pantalla de historial.

### P509. Si POST /conversations falla (403 por throttling, 401 por token expirado, 5xx, destinatario inválido), ¿cuántos reintentos, con qué backoff y cuándo se declara fallido? ¿Hay mensajes con fecha de caducidad (un recordatorio de 48 h que ya no tiene sentido si la entrega venció) que no deben enviarse tarde? ¿Se avisa al docente de los fallos en la UI o en el informe diario?

- **Requisitos:** R2.6.5, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la máquina de estados del outbox y evita enviar mensajes desfasados a estudiantes.
- **Estudio de APIs:** §9.4 menciona reintentos en el outbox; §1.5 recomienda backoff ante 403/429; no define caducidad de mensajes.

### P510. ¿Cuántos mensajes individuales personalizados por hora tolera el throttling de Canvas con un solo token (60 estudiantes × 1 POST secuencial)? ¿Existe algún límite diario de conversaciones nuevas para un usuario teacher en la instancia usada (Free-for-Teacher o institucional)? ¿Funciona bulk_message? ¿El token del profesor puede enviar a recipients[]=course_X o a una sección completa (permiso «enviar mensajes a toda la clase»)?

- **Requisitos:** R2.6.5, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Verificar empíricamente · **Entrega:** Ambas entregas
- **Por qué importa:** Determina si el envío masivo de «repositorio disponible» puede completarse en minutos durante la demo o requiere encolado con pausas mayores, y si el mensaje masivo por sección es viable como alternativa al anuncio.
- **Estudio de APIs:** §1.5 (leaky bucket por token, una request simultánea); §9.3 documenta recipients con prefijo course_/group_; Apéndice A.4 pide probar bulk_message.

### P511. ¿Se envían mensajes a estudiantes cuya matrícula pasó a inactive/deleted/concluded en Canvas (por ejemplo, un recordatorio de entrega a un alumno que abandonó el curso)? ¿Canvas acepta ese recipient con el token del profesor o devuelve error? ¿Y a un estudiante que salió de un grupo pero sigue como colaborador del repositorio?

- **Requisitos:** R2.6.5, R2.6.7, R2.2.1
- **Área declarada:** 2.6
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Define los filtros del outbox y evita mensajes indebidos o errores 4xx que bloqueen la cola.
- **Estudio de APIs:** §4.4 recomienda marcar retirados sin borrar; §14 «Estudiantes que se retiran»; no lo relaciona con comunicaciones.

### P512. Para informar al estudiante su repositorio, ¿se usa comentario en la entrega de Canvas (submission comment), mensaje directo (Conversation), o ambos? Si la tarea tiene varias entregas, ¿en cuál submission se comenta (la primera, la próxima)? ¿Qué texto se envía cuando la invitación de GitHub quedó pendiente (201) versus acceso inmediato (204)?

- **Requisitos:** R2.3.12, R2.6.5, R2.6.7
- **Área declarada:** 2.6 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es lo que se demuestra al cierre de la parcial («mostrar el mensaje que le llegó al estudiante en Canvas»); define plantilla, canal y número de llamadas por repositorio.
- **Opciones planteadas:**
  - Solo Conversation
  - Solo submission comment
  - Ambos siempre
  - Configurable por tarea
- **Estudio de APIs:** §5.7 recomienda usar ambos canales; §5.4 documenta 201 (invitación pendiente) vs 204 (acceso directo).

### P513. Al registrar una calificación desde la app (R2.7.6), ¿se envía además un mensaje directo al estudiante o grupo (con nota, comentario, SHA revisado, enlace a la rúbrica), o se confía en la notificación nativa de Canvas al publicar la nota? Si se envía, ¿es un toggle por tarea (R2.6.7) y cómo se maneja una tarea grupal con grade_group_students_individually=true (notas distintas por integrante)?

- **Requisitos:** R2.6.5, R2.6.7, R2.7.6
- **Área declarada:** 2.6 / 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.6.5 menciona «corrección» como caso de uso; define un evento adicional del outbox, su plantilla y su interacción con la publicación de notas.
- **Estudio de APIs:** §9.4 lista «Corrección publicada → Conversation individual (notify_graded)»; §10.4 explica la propagación de notas grupales.

### P514. ¿Los anuncios generados por la app se publican automáticamente en Canvas (published=true) o se crean como borrador (published=false) para que el profesor los revise y publique desde Canvas o desde la app? ¿Depende del tipo (automático por evento vs manual)?

- **Requisitos:** R2.6.6, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el flujo de aprobación, el uso del parámetro published y si la app necesita una bandeja de «anuncios pendientes de publicar».
- **Opciones planteadas:**
  - Publicar automáticamente
  - Crear borrador para revisión
  - Automático para eventos, borrador para manuales
  - Configurable por tarea
- **Estudio de APIs:** §9.2 muestra published=true en el ejemplo y documenta published=false como borrador y delayed_post_at.

### P515. Cuando un cambio de fecha afecta solo a una sección, ¿el anuncio se dirige solo a esa sección (specific_sections) o a todo el curso? Cuando afecta a un override individual o de grupo (extensión a un estudiante), ¿se genera anuncio público, un mensaje directo al afectado, o nada por privacidad?

- **Requisitos:** R2.6.6, R2.4.2, R2.4.3
- **Área declarada:** 2.6 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la regla de enrutamiento del evento «cambio de fecha» y protege la privacidad de extensiones individuales.
- **Estudio de APIs:** §9.2 sugiere specific_sections para fechas por sección; §7.1 distingue overrides ADHOC, grupo y sección; no aborda extensiones individuales en anuncios.

### P516. ¿Cualquier cambio de due_at dispara un anuncio, o solo cambios mayores a un umbral (por ejemplo >1 h)? ¿También cambios de lock_at/unlock_at, creación o eliminación de un override, o cambio de fecha de una entrega ya cerrada (snapshot capturado)? Si el profesor edita la fecha varias veces dentro de la ventana de polling (10 min), ¿se publica un anuncio con la fecha final o uno por cambio? ¿Se espera un tiempo de gracia antes de anunciar?

- **Requisitos:** R2.6.6, R2.6.7, R2.4.4
- **Área declarada:** 2.6 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la detección de eventos, el debounce y evita anuncios ruidosos o contradictorios; también decide si un cambio posterior al cierre reabre la entrega o solo alerta al docente.
- **Estudio de APIs:** §7.4 sugiere «si el cambio es relevante (>1h) y el profesor lo activó → publicar anuncio»; no aborda debounce, lock_at ni entregas ya cerradas.

### P517. ¿Cuál es el contenido del anuncio de cambio de fecha (título, fecha anterior → nueva en hora local, entrega afectada, sección, enlace a la tarea en Canvas)? ¿Puede el profesor editar título y cuerpo antes de publicar, o es texto fijo generado por la app?

- **Requisitos:** R2.6.6
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la plantilla, sus variables y si existe una vista de edición previa a la publicación.
- **Estudio de APIs:** §9.2 da un ejemplo mínimo de título y mensaje HTML.

### P518. ¿El docente puede redactar anuncios libres desde la app asociados a una tarea (por ejemplo «los repositorios ya están disponibles», «recordatorio de entrega») con selección de secciones y publicación inmediata o programada (delayed_post_at)? ¿Qué roles pueden hacerlo?

- **Requisitos:** R2.6.6, R2.1.8
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.6.6 habla de «eventos generales asociados a una tarea, como cambio en las fechas» (ejemplo, no lista cerrada); define una vista y un permiso.
- **Estudio de APIs:** §9.2 documenta delayed_post_at y specific_sections; §3.4 propone el permiso student.communicate.

### P519. Canvas ya notifica nativamente a los estudiantes cuando cambia la fecha de una tarea; ¿el anuncio de la app se publica igual por requisito, y cómo se evita publicar dos anuncios por el mismo cambio tras un reinicio (clave de idempotencia: entrega + fecha anterior + fecha nueva)? ¿Se guarda el discussion_topic_id y se lista el historial de anuncios en la app con enlace a Canvas?

- **Requisitos:** R2.6.6, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la idempotencia y la trazabilidad de anuncios, y la explicación que el equipo dará si se le pregunta por la duplicidad con Canvas.
- **Estudio de APIs:** §9.2 documenta GET discussion_topics?only_announcements=true; §9.4 propone constraint único en el outbox.

### P520. ¿El token del profesor puede crear anuncios con specific_sections en la instancia real (Free-for-Teacher o institucional)? ¿Qué ocurre si la Developer Key tiene «enforce scopes» sin POST discussion_topics, o si el curso restringe la creación de anuncios? ¿Se refleja el resultado en el checklist de verificación de la vinculación (R2.1.6)?

- **Requisitos:** R2.6.6, R2.1.6
- **Área declarada:** 2.6 / 2.1
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Si falla, R2.6.6 no es demostrable; hay que probarlo temprano y definir el mensaje de error y el chequeo de vinculación.
- **Estudio de APIs:** §3.3 incluye «Podemos publicar anuncios» en el checklist; §1.3 lista el scope url:POST|/api/v1/courses/:course_id/discussion_topics.

### P521. ¿Cuál es la lista cerrada de eventos que generan comunicación automática y su canal: repositorio disponible, invitación pendiente sin aceptar tras N días, falta usuario GitHub (recordatorio), X horas antes de una entrega, repo sin commits cerca del cierre, cambio de fecha, entrega cerrada/snapshot capturado, nota publicada, estudiante agregado a un grupo tardíamente, otros? ¿Cuáles deben estar operativos para la parcial y cuáles solo para la final?

- **Requisitos:** R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Cada evento es un disparador, una plantilla, un toggle y un caso de prueba; el enunciado usa «tales como», por lo que la lista es decisión del equipo.
- **Estudio de APIs:** §9.4 propone 6 eventos con canal y flag: notify_repo_ready, notify_missing_mapping, notify_deadline_48h, notify_no_activity, notify_date_change, notify_graded.

### P522. ¿Los toggles de comunicaciones son por tarea con valores por defecto ON u OFF al crear la tarea? ¿Se heredan de una configuración a nivel de curso? ¿Pueden variar por entrega dentro de una tarea (recordatorio para la parcial pero no para la final)? ¿Qué roles pueden cambiarlos, dado que el enunciado dice «el profesor»?

- **Requisitos:** R2.6.7, R2.1.8
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el modelo de configuración, la UI de la tarea y los permisos RBAC; el default del evento «repositorio disponible» afecta lo que se ve en la parcial.
- **Estudio de APIs:** §9.4 propone «tabla de flags por tarea»; §3.4 no asigna un permiso específico a los toggles.

### P523. ¿Con cuánta anticipación se envía el recordatorio de proximidad de entrega (48 h fijas, configurable por tarea, varios hitos 7d/48h/24h)? ¿Se calcula sobre la fecha efectiva de cada estudiante o grupo (overrides por sección y extensiones), generando envíos en momentos distintos, o sobre la fecha base? ¿Se envía por mensaje directo individual o por anuncio por sección? ¿Se omite si el sujeto ya tiene commits recientes?

- **Requisitos:** R2.6.7, R2.4.2, R2.4.3
- **Área declarada:** 2.6 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija la regla de programación del outbox (scheduled_for por sujeto), el canal y la lógica condicional.
- **Estudio de APIs:** §9.4 propone «Faltan 48 h → Conversation individual o anuncio» y «Faltan 24 h y el repo no tiene commits → Conversation»; §7.3 define fecha efectiva por estudiante.

### P524. ¿Cuál es la clave de idempotencia por evento (tipo + destinatario + entrega, más la fecha objetivo)? Si la fecha de una entrega cambia después de enviado el recordatorio y la nueva fecha vuelve a entrar en la ventana, ¿se envía un segundo recordatorio? Si un repositorio pasa READY → ERROR → READY, o se elimina y recrea, ¿se reenvía «repositorio disponible»?

- **Requisitos:** R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el constraint único del outbox y evita spam a estudiantes tras reinicios del worker o cambios de fecha.
- **Estudio de APIs:** §9.4 propone constraint único por (kind, target, delivery_id); no cubre cambios de fecha posteriores ni recreación de repos.

### P525. Cuando el profesor desactiva un toggle, ¿se cancelan los mensajes ya programados y no enviados, y qué pasa con los que están en proceso de envío? Al reactivarlo, ¿se reprograman los eventos que aún tienen sentido (fecha futura) y se descartan los pasados, o se envían los pendientes acumulados? ¿Se registra quién y cuándo cambió el toggle?

- **Requisitos:** R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el efecto del toggle sobre el outbox y la auditoría de configuración.
- **Estudio de APIs:** §9.4 no lo aborda.

### P526. ¿Se comunica al estudiante al crearse el repositorio (CREATED, aunque la invitación esté pendiente) o solo cuando está READY (invitación aceptada)? Si la invitación no se acepta en N días, ¿se envía un recordatorio automático «acepta tu invitación», con qué frecuencia y tope, y se reenvía la invitación de GitHub (revocar y crear) junto con el mensaje?

- **Requisitos:** R2.6.7, R2.3.9, R2.3.11, R2.3.12
- **Área declarada:** 2.6 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el disparador exacto en la máquina de estados de repositorios y el texto del mensaje; el recordatorio agrega un evento y un job.
- **Estudio de APIs:** §5.5 paso 6 notifica tras agregar colaboradores; §5.4 explica 201 (invitación) vs 204 (acceso directo); §5.6 sugiere la acción «Reenviar».

### P527. ¿El recordatorio automático a estudiantes sin usuario GitHub se envía con qué frecuencia (diaria, cada N días), con qué tope de intentos, desde cuándo (al crear la tarea, al publicarse la tarea de recolección) y hasta cuándo (vencimiento de la tarea de recolección, cierre de la primera entrega)? ¿Se envía también a integrantes de grupos cuyo repositorio está bloqueado por un compañero sin mapeo, con texto distinto?

- **Requisitos:** R2.6.7, R2.2.5, R2.2.6
- **Área declarada:** 2.6 / 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Forma parte de la estrategia de enrolamiento cuya usabilidad se evalúa; define un job periódico y sus límites.
- **Estudio de APIs:** §6.3 propone «job diario que envía Canvas Conversation solo a los estudiantes sin mapeo»; §9.4 flag notify_missing_mapping.

### P528. ¿Se comunica al estudiante cuando se captura la versión de cierre de su entrega (SHA, fecha, enlace tree/<sha>), incluyendo el caso NO_COMMITS? ¿Se comunica al equipo docente de inmediato o solo en el informe diario?

- **Requisitos:** R2.6.7, R2.4.5
- **Área declarada:** 2.6 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.6.7 dice «tales como»; incluirlo agrega un evento, una plantilla y un toggle, y da transparencia al estudiante sobre qué versión será corregida.
- **Estudio de APIs:** §7.5 sugiere que NO_COMMITS es «valioso para el informe»; no propone comunicarlo al estudiante.

### P529. ¿Las plantillas de mensajes y anuncios son fijas en código, editables por curso, o editables por tarea? ¿Qué variables se exponen ({{nombre}}, {{repo_url}}, {{fecha_local}}, {{entrega}}, {{sha}}), se validan las variables desconocidas al guardar, y existe «restaurar plantilla por defecto»?

- **Requisitos:** R2.6.5, R2.6.6, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el modelo de plantillas, el motor de renderizado y una pantalla de edición con validación.
- **Estudio de APIs:** No lo aborda.

### P530. ¿El docente puede ver una vista previa renderizada de cada comunicación con datos reales de un estudiante de ejemplo antes de activarla, y enviarse un mensaje de prueba a sí mismo por Canvas o por email? ¿Los envíos de prueba quedan marcados como tales en el historial?

- **Requisitos:** R2.6.5, R2.6.6, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** La usabilidad es evaluada; define una vista y un tipo de envío distinguible en el log.
- **Estudio de APIs:** No lo aborda.

### P531. ¿Qué campos guarda el log de comunicaciones (tipo, canal, destinatario, tarea/entrega, cuerpo final, disparado por automático o usuario X, programado para, enviado el, estado, error, id externo de Canvas o del proveedor de email), qué vistas lo exponen (por curso, tarea, estudiante, repositorio), qué roles pueden verlo y cuánto tiempo se retiene?

- **Requisitos:** R2.6.4, R2.6.5, R2.6.6, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cierra la trazabilidad de toda la sección 2.6 y permite demostrar cada requisito de comunicación en la revisión.
- **Estudio de APIs:** §9.4 propone outbox más «pantalla de historial de comunicaciones»; §9.1 pide registro de envíos del informe.

### P532. ¿Los mensajes automáticos pueden enviarse a cualquier hora (por ejemplo a las 03:00 cuando el worker crea un repositorio) o se agrupan en una ventana horaria (08:00–21:00 America/Santiago)? ¿Las fechas dentro de los mensajes se muestran en hora de Chile con indicación explícita de zona horaria, y cómo se manejan los cambios de horario de verano en los textos?

- **Requisitos:** R2.6.7, R2.6.5
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define scheduled_for en el outbox y el formato de fechas de todas las plantillas.
- **Estudio de APIs:** §14 recomienda guardar UTC y convertir al renderizar; no aborda ventanas horarias de envío.

### P533. Si la assignment de Canvas asociada a una entrega es eliminada en Canvas o el profesor la desvincula en la app, ¿se cancelan los recordatorios pendientes de esa entrega, se comunica algo a los estudiantes (anuncio) y se alerta al docente en el informe o en la UI? ¿Y si se elimina la tarea de Canvas usada para recolectar usuarios GitHub?

- **Requisitos:** R2.6.7, R2.6.6, R2.3.1
- **Área declarada:** 2.6 / 2.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el comportamiento en cascada del outbox ante cambios estructurales en Canvas.
- **Estudio de APIs:** §7.4 sugiere un log de auditoría de cambios de Canvas; no aborda eliminación de assignments.

### P534. Si Canvas agrega un integrante a un grupo que ya tiene repositorio, ¿recibe automáticamente el mensaje «repositorio disponible» al ser agregado como colaborador? Si un integrante sale del grupo, ¿se le comunica algo, se le quita del repositorio y se deja de incluirlo en los recordatorios del grupo?

- **Requisitos:** R2.6.7, R2.2.3, R2.3.9
- **Área declarada:** 2.6 / 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define disparadores sobre cambios de membresía detectados por la sincronización.
- **Estudio de APIs:** §4.4 «upsert; marcar como retirado lo que ya no viene»; no lo relaciona con comunicaciones.

### P535. ¿Qué permisos concretos de R2.1.8 gobiernan cada acción de comunicación: activar o desactivar toggles, enviar mensaje manual, publicar anuncio, editar plantillas, ver el log, suscribirse al informe? ¿Un ayudante puede enviar un mensaje a un estudiante que no tiene asignado para corregir?

- **Requisitos:** R2.6.3, R2.6.5, R2.6.6, R2.6.7, R2.1.8
- **Área declarada:** 2.6 / 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cruza R2.1.8 con toda la sección 2.6 y define la matriz de permisos que debe documentarse.
- **Estudio de APIs:** §3.4 propone student.communicate (profesor y ayudante jefe) y report.subscribe (todos los roles).

### P536. ¿Existe un centro de notificaciones dentro de la app (icono con badge) o las alertas se muestran solo en contexto (banners) y en el informe por email? Si existe: ¿qué eventos generan notificación in-app (repo con error, invitación sin aceptar >N días, fecha cambiada en Canvas, tarea Canvas eliminada, entrega cerrada y snapshot capturado, corrección asignada), se marcan como leídas, y son por usuario o por curso?

- **Requisitos:** R2.6.1, R2.6.2, R2.3.11
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define un subsistema de notificaciones internas con su modelo de datos y UI, o lo descarta explícitamente en favor de banners + email.
- **Estudio de APIs:** §9.4 propone tabla notification_outbox para comunicaciones a estudiantes y una 'pantalla de historial'; no propone notificaciones in-app para docentes.

### P537. ¿La app muestra un historial de comunicaciones enviadas a estudiantes (por tarea y por estudiante): tipo (comentario en entrega / mensaje / anuncio), destinatario, fecha, estado (enviado / error / pendiente), texto exacto enviado, y permite reenviar o reintentar? ¿Puede el docente enviar un mensaje manual a un estudiante o grupo desde la tabla de repos ('Recordar usuario GitHub')?

- **Requisitos:** R2.3.12, R2.6.5, R2.6.6, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin historial, el docente no puede saber si el estudiante fue informado del repo (R2.3.12) ni demostrarlo en la corrección; define la pantalla y las acciones manuales de comunicación.
- **Estudio de APIs:** §9.4 recomienda outbox + 'pantalla de historial de comunicaciones que pueden mostrar en la demo'; §5.6 muestra acción 'Recordar' en la tabla.

### P538. Los mensajes automáticos a estudiantes (repositorio disponible, usuario GitHub inválido, recordatorio de usuario faltante, proximidad de fecha, cambio de fecha): ¿plantillas editables por tarea con variables y vista previa, o textos fijos? ¿Al activar/desactivar cada flag (R2.6.7) el profesor ve exactamente qué recibirá el estudiante y por qué canal? ¿'Repositorio disponible' se envía por comentario en la entrega, por mensaje directo, o por ambos como sugiere el estudio (con el riesgo de doble aviso)? ¿Cuál es el valor por defecto de cada flag en una tarea nueva?

- **Requisitos:** R2.3.12, R2.6.5, R2.6.7
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la pantalla 'Comunicaciones' de la tarea, las plantillas del spec y los defaults que se verán en la demo.
- **Estudio de APIs:** §5.7 recomienda usar ambos mecanismos (comentario en entrega + Conversation); §9.4 propone 6 flags por tarea (notify_repo_ready, notify_missing_mapping, notify_deadline_48h, notify_no_activity, notify_date_change, notify_graded) sin defaults ni plantillas.

### P539. ¿Dónde y cómo se gestiona la suscripción al informe diario: toggle en el perfil del usuario por curso, en 'Equipo docente', o ambos; más link 'darse de baja' en el pie del correo? ¿Los informes generados se pueden ver dentro de la app (historial por fecha) con el mismo contenido del email? ¿Se muestra al usuario la hora de envío y el estado del último envío (enviado / falló / sin informe porque no hay tareas activas)?

- **Requisitos:** R2.6.1, R2.6.3, R2.6.4
- **Área declarada:** 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la pantalla de suscripción, el historial de informes y cómo se demuestra R2.6.1–R2.6.4 en la revisión sin depender del correo.
- **Estudio de APIs:** §9.1 propone toggle en UI + link de baja con token firmado y guardar cada informe como página web accesible (/courses/:id/reports/YYYY-MM-DD).

---

## 2.7

### P540. ¿Está en el alcance la retroalimentación del lado de GitHub (el estudiante la ve en su repo): comentarios de commit sobre el SHA capturado, issues abiertos por el corrector, o un Pull Request generado desde el tag entrega-N para revisar línea a línea? Si sí, ¿la app los crea/enlaza y los registra como comunicación, o se prohíbe explícitamente para que toda calificación y feedback viva en Canvas como exige el enunciado? Si un ayudante abre un issue por su cuenta en GitHub, ¿la app lo detecta o lo ignora?

- **Requisitos:** R2.7.4, R2.7.6, R2.6.5
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Delimita dónde puede recibir feedback el estudiante y si se requieren permisos adicionales (Issues, Pull requests) en la GitHub App.
- **Opciones planteadas:**
  - Solo Canvas (prohibido en GitHub)
  - PR de revisión desde el tag, enlazado desde la app
  - Comentarios de commit/issues libres sin registro
- **Estudio de APIs:** §10 mantiene rúbrica, notas y comentarios exclusivamente en Canvas y §2.3 no pide permisos de Issues/PRs; no aborda feedback en GitHub.

### P541. Si la asignación de correctores se hizo 'por sección' o por grupo y luego un estudiante cambia de sección o de grupo en Canvas, ¿su entrega se reasigna automáticamente al corrector de la nueva sección/grupo, permanece con el original, o se marca 'requiere reasignación' con alerta? ¿Aplica igual si el cambio ocurre después de que el corrector ya empezó?

- **Requisitos:** R2.7.1, R2.2.2, R2.2.3
- **Área declarada:** 2.7 / 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija la regla de estabilidad de la asignación frente a eventos del roster y qué alertas aparecen en la vista de estado de corrección.
- **Opciones planteadas:**
  - Reasignar automáticamente
  - Mantener corrector original
  - Marcar para reasignación manual
- **Estudio de APIs:** §10.1 propone asignación manual o automática 'equitativa o por sección'; no aborda cambios posteriores de sección o grupo.

### P542. Flujo de reclamo iniciado por el estudiante (vía Canvas: 'pusheé antes del cierre y no me consideraron', 'quiero recorrección'): ¿la app modela un estado 'en reclamo' por entrega/estudiante que congela la nota y avisa al corrector, o el reclamo se maneja fuera de la app? ¿Qué evidencia ofrece la app al docente para resolverlo: pushes recibidos en una ventana de ±N minutos alrededor del cierre efectivo (hora de recepción del webhook vs fecha del commit), historial del SHA capturado y de recapturas, comunicaciones enviadas al estudiante? ¿Quién puede cerrar el reclamo y se notifica el resultado por Canvas?

- **Requisitos:** R2.7.6, R2.4.5, R2.4.7, R2.6.5
- **Área declarada:** 2.7 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si hay un nuevo estado en R2.7.7, qué datos de push deben persistirse como evidencia y una plantilla de respuesta al estudiante.
- **Opciones planteadas:**
  - Estado 'en reclamo' con evidencia en la app
  - Reclamo fuera de la app, solo re-edición de nota
  - Vista de evidencia sin estado formal
- **Estudio de APIs:** §7.5 hace del SHA en BD la fuente de verdad y §14 responde cómo saber qué código corregir; no aborda reclamos del estudiante ni evidencia de pushes cercanos al cierre.

### P543. Canvas impide modificar notas de assignments cuyo grading period está cerrado (y, según configuración, tras la conclusión del término) para usuarios no admin: el PUT a submissions devuelve error. ¿Cómo lo detecta y muestra la app ('período de calificación cerrado en Canvas'), se bloquea el botón de publicar, y qué pasa con correcciones hechas en la app pendientes de publicar cuando el período cierra a mitad de la corrección? ¿La instancia Canvas que usarán (institucional o demo) tiene grading periods configurados y con qué fechas respecto al 6–20 de octubre?

- **Requisitos:** R2.7.6, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina un estado de corrección adicional ('no publicable en Canvas'), el mensaje al corrector y la coordinación de fechas del curso demo.
- **Opciones planteadas:**
  - Detectar al publicar y mostrar error accionable
  - Leer grading periods del curso (`GET /courses/:id/grading_periods`) y advertir antes
  - Ignorar y documentar como limitación
- **Estudio de APIs:** No lo aborda (§10.4 no menciona grading periods ni cursos concluidos).

### P544. Al construir la lista de entregas a asignar (R2.7.1) y el estado de corrección (R2.7.7), ¿la app lee el estado previo de la submission en Canvas (`excused=true`, `late_policy_status=missing`, `workflow_state=graded` puesta en SpeedGrader) para excluir o marcar esos sujetos, o los trata como al resto? ¿Un estudiante excusado en Canvas aparece como 'excusado (Canvas)' sin consumir un corrector? ¿Con qué frecuencia y endpoint se refresca ese estado antes de ejecutar la asignación automática?

- **Requisitos:** R2.7.1, R2.7.7, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define qué sujetos entran en el reparto de correctores, los estados iniciales de R2.7.7 y una lectura adicional de Canvas en el sync.
- **Opciones planteadas:**
  - Ignorar estado previo en Canvas
  - Excluir excusados y ya calificados
  - Incluirlos marcados, sin asignar corrector por defecto
- **Estudio de APIs:** §10.4 lista `submission[excuse]` como parámetro de escritura y §10.5 usa submission_summary; no aborda leer el estado previo antes de asignar.

### P545. Además del informe diario, ¿el corrector recibe un aviso inmediato por email y/o in-app cuando se le asignan o reasignan entregas y cuando el snapshot de una entrega asignada queda disponible para corregir? ¿Qué contiene (número de entregas, tarea, fecha objetivo de corrección si existe, enlace directo a 'mis correcciones') y puede desactivarse individualmente como la suscripción de R2.6.3?

- **Requisitos:** R2.7.1, R2.7.2, R2.6.3
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define eventos de notificación hacia el equipo docente (no solo hacia estudiantes) y una preferencia más por usuario.
- **Opciones planteadas:**
  - Sin aviso inmediato (solo informe diario)
  - Email al asignar
  - Email cuando el snapshot esté disponible
  - In-app únicamente
- **Estudio de APIs:** §10.1 describe la vista 'Mis correcciones' pero no notificaciones al corrector; §9.4 solo lista eventos hacia estudiantes.

### P546. Si la nota ya existe en Canvas (otro ayudante o el profesor calificó directamente en Canvas) cuando un ayudante intenta publicar desde la app: ¿se sobrescribe, se bloquea con aviso, o se muestra la nota existente para confirmar? ¿El estado de corrección (R2.7.7) marca como corregida una entrega calificada fuera de la app? ¿Qué pasa si el estudiante fue retirado y Canvas rechaza la nota?

- **Requisitos:** R2.7.6, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la fuente de verdad del estado de corrección (app vs Canvas) y la política de conflicto de escritura.
- **Estudio de APIs:** §10.5 propone mostrar ambas cuentas ('corregidas en la app' vs 'con nota en Canvas'); no define qué hacer ante conflicto.

### P547. ¿Cuál es la unidad asignable a un corrector: cada ENTREGA de cada estudiante/grupo (delivery × repositorio), o la TAREA completa (el mismo corrector revisa todas las entregas parciales y finales de ese estudiante/grupo)? Si es por entrega, ¿existe la acción 'copiar la asignación de la entrega anterior'?

- **Requisitos:** R2.7.1, R2.3.2, R2.3.4
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la clave del modelo de asignación (delivery_id+repository_id vs assignment_id+repository_id), la UI de asignación (una pantalla por entrega vs una por tarea) y si el ayudante ve continuidad de contexto entre entregas del mismo grupo.
- **Opciones planteadas:**
  - Por entrega, independiente
  - Por tarea, heredado a todas sus entregas
  - Por entrega con acción 'copiar asignación de la entrega anterior'
- **Estudio de APIs:** §10.1 propone `grading_assignment(delivery_id, repository_id, grader_user_id, status)`, es decir por entrega, sin herencia entre entregas de una misma tarea.

### P548. ¿Qué modos de asignación se implementan y cuáles son obligatorios para la entrega final: manual (uno a uno), aleatoria equitativa, por sección, por grupo/categoría de grupos, por lista de carga por ayudante, importación CSV?

- **Requisitos:** R2.7.1
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cada modo es un flujo de UI y un algoritmo distinto; fija el alcance de R2.7.1 y los criterios de aceptación de la pantalla de asignación.
- **Opciones planteadas:**
  - Solo manual
  - Manual + aleatoria equitativa
  - Manual + equitativa + por sección
  - Manual + equitativa + por sección + cuotas por ayudante
- **Estudio de APIs:** §10.1: 'asignación manual (drag & drop o selects) + automática (repartir equitativamente, o por sección)'; no fija cuáles son obligatorias.

### P549. En la asignación 'equitativa/balanceada', ¿qué se balancea: número de entregas por corrector, número de estudiantes (un grupo de 4 pesa más que un individual), carga acumulada en otras entregas/tareas del curso, o una capacidad configurable por ayudante (p. ej. el ayudante jefe corrige 0)? ¿El balance es global o dentro de cada sección?

- **Requisitos:** R2.7.1
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina el algoritmo de reparto, los parámetros de la UI (capacidades, exclusiones) y cómo se verifica en la aceptación que el reparto es 'justo'.
- **Opciones planteadas:**
  - Igual número de entregas
  - Igual número de estudiantes
  - Ponderado por carga previa
  - Capacidad configurable por ayudante
- **Estudio de APIs:** §10.1 dice 'repartir equitativamente' sin definir la métrica.

### P550. ¿Puede una misma entrega tener más de un corrector (co-corrección, segunda revisión, moderación del profesor)? Si sí, ¿quién publica la nota definitiva a Canvas y cómo se resuelven discrepancias?

- **Requisitos:** R2.7.1, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Un solo corrector simplifica el modelo (FK única); varios exigen roles por asignación (principal/revisor), estados adicionales y una regla de consolidación de nota.
- **Opciones planteadas:**
  - Exactamente uno
  - Uno principal + revisores de solo lectura
  - Varios con moderación final del profesor
- **Estudio de APIs:** §10.1: el modelo tiene un único `grader_user_id` por fila, lo que implica un corrector por entrega.

### P551. ¿Quiénes son elegibles como correctores: solo ayudantes, o también los profesores del curso (incluidos co-profesores R2.1.7)? ¿El profesor puede auto-asignarse entregas? ¿Basta pertenecer al curso o se requiere un permiso específico de corrección dentro de los ≥3 permisos de R2.1.8?

- **Requisitos:** R2.7.1, R2.1.7, R2.1.8
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la lista de candidatos en la pantalla de asignación y si la vista 'mis entregas' (R2.7.2) también aplica a profesores.
- **Estudio de APIs:** §3.4 propone `grading.submit` para profesor, ayudante jefe y ayudante (solo asignadas); no dice si el profesor aparece como corrector asignable.

### P552. ¿Quién puede asignar y reasignar entregas: solo profesores, o también un rol de ayudante con permiso de asignación (p. ej. 'ayudante jefe')? ¿Puede un ayudante 'tomar' entregas del pool de no asignadas (auto-asignación) o solo recibe lo que se le asigna?

- **Requisitos:** R2.7.1, R2.1.8
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija qué permiso de R2.1.8 gobierna R2.7.1 y si existe un flujo de auto-servicio para ayudantes.
- **Opciones planteadas:**
  - Solo profesores
  - Profesores + rol con permiso grading.assign
  - Además, auto-asignación desde el pool
- **Estudio de APIs:** §3.4 propone `grading.assign` para profesor y ayudante jefe; el enunciado dice literalmente 'permitir al profesor asignar'.

### P553. ¿Se permite reasignar una entrega que ya está 'en progreso' o 'corregida pero no publicada'? ¿Qué pasa con el borrador del corrector anterior: se conserva y lo ve el nuevo, se descarta, o se bloquea la reasignación? ¿Se guarda historial de reasignaciones (quién, cuándo, de quién a quién)?

- **Requisitos:** R2.7.1, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define reglas de transición del estado de corrección y si el borrador es propiedad del corrector o de la entrega.
- **Estudio de APIs:** no lo aborda.

### P554. Al retirar a un ayudante (R2.1.9), ¿sus entregas pendientes vuelven a 'sin asignar', se reasignan automáticamente de forma balanceada, o el flujo de retiro obliga al profesor a reasignarlas antes de confirmar? ¿Las entregas que ya publicó conservan su nombre como corrector histórico?

- **Requisitos:** R2.1.9, R2.7.1, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El flujo de retiro (que ya existe en la parcial) debe especificar qué hace con las asignaciones; sin regla, las entregas quedan huérfanas e invisibles.
- **Opciones planteadas:**
  - Vuelven a sin asignar con alerta
  - Reasignación automática balanceada
  - Retiro bloqueado hasta reasignar manualmente
- **Estudio de APIs:** §3.4: 'reasignen las entregas que tenía pendientes' (recomendación no aprobada, sin decir automático vs manual).

### P555. ¿Se puede asignar correctores ANTES del cierre de la entrega (cuando aún no existe snapshot) o solo después de capturada la versión? Si es antes, ¿la asignación queda 'latente' y se activa al capturarse el snapshot?

- **Requisitos:** R2.7.1, R2.4.5
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cambia cuándo aparece la pantalla de asignación en el ciclo de la tarea y qué estado inicial tiene la asignación.
- **Estudio de APIs:** no lo aborda.

### P556. Un estudiante/grupo cuyo repositorio se crea DESPUÉS de hecha la asignación (mapeo tardío), o que al cierre no tiene repo (estado PENDING_MAPPING/ERROR): ¿aparece en la lista de asignación? ¿Queda como 'sin asignar' con alerta al profesor, se asigna automáticamente al corrector con menos carga, o se excluye hasta tener repo?

- **Requisitos:** R2.7.1, R2.7.7, R2.3.10, R2.3.11
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** La asignación automática es una foto en el tiempo; hay que definir el comportamiento incremental para no dejar sujetos sin corrector.
- **Estudio de APIs:** §5.5 describe la creación progresiva de repos pero no su efecto sobre asignaciones ya hechas.

### P557. Si el snapshot de una entrega es NO_COMMITS (repo creado pero sin commits al cierre), ¿la entrega igual se asigna y se abre al corrector, o se marca automáticamente 'sin entrega' con una nota predefinida (p. ej. nota mínima o `late_policy_status=missing`)? ¿Quién confirma esa acción?

- **Requisitos:** R2.7.1, R2.7.6, R2.4.5
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita gastar tiempo de corrección en repos vacíos y define un flujo masivo para 'no entregó'.
- **Opciones planteadas:**
  - Se asigna y corrige normal
  - Se marca 'sin entrega' y el corrector confirma
  - Publicación masiva de 'missing' por el profesor
- **Estudio de APIs:** §7.5 define el estado NO_COMMITS; §10.4 lista `submission[late_policy_status]` (`late`, `missing`, `extended`, `none`) sin regla de uso.

### P558. Un estudiante retirado del curso (enrollment `inactive`/`deleted`/`completed`) que tiene una entrega asignada: ¿desaparece de la lista del corrector, queda visible marcado 'retirado' pero calificable, o se bloquea su corrección? Y en un grupo, ¿su retiro cambia a quién se propaga la nota?

- **Requisitos:** R2.7.1, R2.7.6, R2.2.1
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define filtros de la vista de corrección y evita intentar publicar notas que Canvas rechazará o que no tienen destinatario.
- **Estudio de APIs:** §4.4 recomienda marcar `deleted_at` y no borrar; §14 'no borren su repo ni su historia'. No aborda la corrección de retirados.

### P559. Verificar contra Canvas real: ¿acepta `PUT .../submissions/:user_id` con `posted_grade` para un estudiante cuyo enrollment está `inactive` o `completed` (curso concluido)? ¿Qué código/mensaje devuelve?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Si Canvas rechaza, la app debe detectar el estado del enrollment antes de publicar y mostrar un error comprensible.
- **Estudio de APIs:** no lo aborda.

### P560. Si la membresía de un grupo cambia en Canvas después del cierre (un integrante se mueve de grupo o el grupo se elimina), ¿la corrección aplica al conjunto de integrantes CONGELADO al momento del snapshot o a la membresía ACTUAL? Dado que con `grade_group_students_individually=false` Canvas propaga a la membresía actual, ¿la app detecta la divergencia y avisa/bloquea?

- **Requisitos:** R2.7.6, R2.2.3, R2.4.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin regla, un estudiante que no trabajó en ese repo puede recibir la nota del grupo y uno que sí trabajó puede quedar sin nota.
- **Opciones planteadas:**
  - Congelar integrantes por snapshot y publicar individualmente
  - Usar membresía actual de Canvas
  - Detectar divergencia y exigir decisión del profesor
- **Estudio de APIs:** §10.4 explica la propagación grupal; §4.4 dice 'upsert' de grupos, sin congelar membresía por entrega.

### P561. Verificar contra Canvas real: con `grade_group_students_individually=false`, ¿un solo PUT a un integrante propaga `posted_grade`, `rubric_assessment` Y el comentario (con `comment[group_comment]=true`) a todos los integrantes? ¿Y qué pasa con el integrante que al cierre estaba en el grupo pero ya no está?

- **Requisitos:** R2.7.6, R2.2.3
- **Área declarada:** 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina si basta una llamada por grupo o hay que iterar por integrante, y cómo se calcula el estado 'publicada' del grupo.
- **Estudio de APIs:** §10.4: 'calificar a un integrante propaga la nota a todo el grupo. Si es true, hay que llamar por cada integrante' (afirmación no verificada).

### P562. La vista 'mis entregas asignadas': ¿es por curso o transversal a todos los cursos del ayudante? ¿Qué columnas muestra (estudiante/grupo, sección, tarea, entrega, fecha de cierre efectiva, estado, fecha de asignación, link a la versión)? ¿Qué filtros (tarea, entrega, estado, sección) y qué orden por defecto? ¿Muestra progreso 'X de Y corregidas'?

- **Requisitos:** R2.7.2
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es la pantalla central del ayudante; sin definirla no hay criterios de aceptación para R2.7.2.
- **Estudio de APIs:** §10.1: 'lista filtrada por grader_user_id, con estados pendiente / en curso / listo'; no define columnas, filtros ni alcance.

### P563. ¿Un ayudante puede ver las entregas asignadas a OTROS ayudantes (solo lectura), incluidas sus notas y comentarios, o únicamente las propias? ¿El profesor tiene una vista consolidada por corrector con avance de cada uno?

- **Requisitos:** R2.7.2, R2.7.7, R2.1.8
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define reglas de autorización a nivel de fila y el alcance de la vista de estado (R2.7.7).
- **Estudio de APIs:** §3.4: `grading.submit` para ayudante '(solo asignadas)'; no habla de lectura de entregas ajenas.

### P564. ¿Qué ve un ayudante sin entregas asignadas, o con entregas asignadas cuya versión aún no fue capturada (cierre futuro por extensión)? ¿Un estado vacío con explicación, o las entregas listadas como 'no disponible aún' con la fecha efectiva?

- **Requisitos:** R2.7.2
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Los estados vacíos y 'en espera' se evalúan en usabilidad; sin definirlos la pantalla queda en blanco.
- **Estudio de APIs:** no lo aborda.

### P565. Navegación siguiente/anterior: ¿en qué orden determinístico (alfabético, por sección, por estado)? ¿'Siguiente' avanza al siguiente en la lista o al 'siguiente pendiente' saltando las ya corregidas? ¿Qué atajos de teclado son obligatorios? ¿La navegación se limita a la misma entrega de la misma tarea o cruza tareas/entregas?

- **Requisitos:** R2.7.3
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es literalmente R2.7.3; hay que fijar el comportamiento para poder demostrarlo y probarlo.
- **Opciones planteadas:**
  - Siguiente en lista + siguiente pendiente
  - Solo siguiente pendiente
  - Navegación con filtros aplicados
- **Estudio de APIs:** §10.1 sugiere 'anterior / siguiente con atajos de teclado' y un botón 'siguiente sin corregir'.

### P566. Si el corrector navega a otra entrega con cambios sin guardar/publicar, ¿la app autoguarda un borrador, pide confirmación, o se pierde el trabajo?

- **Requisitos:** R2.7.3, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Depende de si existe el concepto de borrador local (pregunta aparte) y define un comportamiento de UI clave para no perder correcciones.
- **Estudio de APIs:** no lo aborda.

### P567. ¿Cómo se accede a la versión: solo link externo a `github.com/ORG/REPO/tree/<sha>` (y al tag), un visor embebido de árbol/archivos dentro de la app leyendo por API con el installation token, o ambos? ¿Se ofrece el diff `compare/<sha_anterior>...<sha_actual>` con la entrega previa?

- **Requisitos:** R2.7.4, R2.4.8
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Un visor embebido evita que el ayudante necesite acceso GitHub a repos privados pero es mucho más trabajo; el link externo lo requiere. También define el alcance de R2.7.4.
- **Opciones planteadas:**
  - Solo link a GitHub (tree/<sha>)
  - Visor embebido en la app
  - Ambos
  - Ambos + diff con la entrega anterior
- **Estudio de APIs:** §10.2: link directo al SHA ('nunca linkeen a main'); §7.5 sugiere `compare` como extra para R2.5.9.

### P568. Si los repos son privados y el acceso es vía link a GitHub, el ayudante necesita ser miembro de la org o colaborador de cada repo. ¿La app pide y guarda el usuario GitHub de cada ayudante al incorporarlo, y lo agrega automáticamente (a la org como miembro, o a cada repo con `pull`/`triage`)? ¿Qué pasa si un ayudante no tiene cuenta GitHub? ¿Se revoca el acceso al retirarlo (R2.1.9)?

- **Requisitos:** R2.7.4, R2.1.8, R2.1.9
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina los campos del formulario de alta de ayudante (que existe desde la parcial), un paso más del worker de aprovisionamiento y el flujo de retiro.
- **Opciones planteadas:**
  - Miembro de la org (una invitación por semestre)
  - Colaborador `pull` por repo
  - Sin acceso GitHub: visor embebido
- **Estudio de APIs:** §14: 'créenlos privados'; §3.4: al retirar, 'revoquen su acceso a la org si se lo dieron'; no dice cómo se les da acceso a los ayudantes.

### P569. ¿Qué metadatos de la versión se muestran junto al link: SHA corto, nombre del tag, fecha efectiva de cierre usada (y su origen: base/sección/extensión), fecha del commit capturado, número de commits, autores, y 'N commits posteriores al cierre'?

- **Requisitos:** R2.7.4, R2.4.8
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Da confianza al corrector de que revisa la versión correcta y sustenta la discusión de atrasos.
- **Estudio de APIs:** §10.2 sugiere mostrar 'capturado el 16-09 16:30 · 47 commits · último por msoto'.

### P570. Cuando el corrector abre una entrega SIN snapshot (extensión individual aún no vencida, o snapshot en ERROR por fallo de GitHub), ¿se le muestra 'no disponible aún' con la fecha efectiva, se le permite corregir sobre el HEAD actual con advertencia, o se bloquea hasta que el job capture?

- **Requisitos:** R2.7.4, R2.4.3, R2.4.5
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita que se califique código que no corresponde a la entrega y define el mensaje/estado para ese caso.
- **Estudio de APIs:** §7.5 describe el job de captura y su robustez, no la UI del corrector ante ausencia de snapshot.

### P571. Si Canvas cambia la fecha de una entrega DESPUÉS de capturado el snapshot (extensión otorgada a posteriori) y existe una corrección en progreso o publicada sobre el SHA anterior, ¿qué hace la app: bloquea la recaptura, recaptura y marca la corrección como 'desactualizada' avisando al corrector, o conserva ambos SHA y deja elegir al profesor?

- **Requisitos:** R2.7.4, R2.4.4, R2.4.7, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cruce entre R2.4.7 (no alterar lo registrado) y la realidad de las extensiones tardías; define un estado adicional y una alerta.
- **Opciones planteadas:**
  - Bloquear recaptura si hay corrección
  - Recapturar y marcar 'desactualizada'
  - Conservar ambos SHA, decide el profesor
- **Estudio de APIs:** §7.4 reprograma el snapshot solo si 'cambió la fecha de una entrega NO capturada aún'; no aborda entregas ya capturadas ni ya corregidas.

### P572. ¿La app solo MUESTRA la rúbrica de Canvas (lectura, con link a SpeedGrader para evaluar allí) o permite EVALUARLA criterio por criterio desde la app (elegir rating/puntos/comentario por criterio) y envía `rubric_assessment` al publicar?

- **Requisitos:** R2.7.5, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es la decisión de alcance más grande de 2.7: define la complejidad de la pantalla de corrección y el payload de publicación.
- **Opciones planteadas:**
  - Solo lectura + link a SpeedGrader
  - Evaluación completa desde la app
  - Lectura + nota numérica + comentario, sin rubric_assessment
- **Estudio de APIs:** §10.3 recomienda 'grilla clickeable (criterios × ratings)'; §10.4 muestra el payload `rubric_assessment[...]`. Recomendación no aprobada.

### P573. Si el assignment de Canvas vinculado NO tiene rúbrica: ¿se permite calificar con nota directa, se muestra un aviso, se bloquea la corrección, o se ofrece un link para crearla en Canvas? ¿Se valida/advierte la ausencia de rúbrica ya al vincular la entrega (R2.3.1)?

- **Requisitos:** R2.7.5, R2.7.6, R2.3.1
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El enunciado dice que las rúbricas 'deberán mantenerse en Canvas'; hay que fijar qué pasa cuando no existen y si es un prerrequisito.
- **Estudio de APIs:** no lo aborda.

### P574. Cuando la rúbrica está asociada pero `use_for_grading=false` (o con `hide_points`/`hide_score_total`), ¿la nota se calcula igualmente desde la rúbrica, o el corrector la ingresa aparte y la rúbrica es solo feedback? Si la suma de puntos de la rúbrica ≠ `points_possible` del assignment, ¿cómo se escala?

- **Requisitos:** R2.7.5, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la fórmula nota = f(rúbrica) y las validaciones antes de publicar.
- **Opciones planteadas:**
  - Nota siempre derivada de la rúbrica
  - Nota manual + rúbrica como feedback
  - Depende de use_for_grading
- **Estudio de APIs:** §10.3 lista los campos `use_for_grading`, `hide_points`, `hide_score_total` sin definir su efecto en la app.

### P575. Si la rúbrica cambia en Canvas a mitad de la corrección (criterios agregados/eliminados, puntos modificados, rúbrica reemplazada), ¿la app lo detecta, invalida o marca los borradores afectados y avisa al corrector? ¿La rúbrica se lee en vivo al abrir la entrega o se cachea en la sincronización?

- **Requisitos:** R2.7.5, R2.4.4
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Un borrador con criterios obsoletos produce un `rubric_assessment` inválido o una nota incorrecta.
- **Estudio de APIs:** §10.3 sugiere usar `assignment.rubric` embebido; no aborda cambios.

### P576. Investigar en la documentación de Canvas: ¿cómo se representan en `rubric_assessment` los criterios con `criterion_use_range=true` (puntos libres dentro del rango del rating) y `free_form_criterion_comments=true` (comentario libre en lugar de rating)? ¿La clave del criterio es `criterion_<id>` o el `id` tal cual viene en `data[]`?

- **Requisitos:** R2.7.5, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el formulario por criterio (selector de rating vs campo numérico vs texto) y el formato exacto del payload.
- **Estudio de APIs:** §10.3 lista `criterion_use_range` y `free_form_criterion_comments` en los objetos; §10.4 usa `rubric_assessment[criterion_1][points]` como ejemplo.

### P577. Verificar contra Canvas real: ¿el objeto `assignment.rubric` embebido trae todo lo necesario (criterios, ratings con ids, puntos) o hay que llamar `GET /courses/:id/rubrics/:id`? ¿Qué devuelve Canvas si `rubric_assessment` trae un `rating_id` inexistente o puntos fuera del rango del criterio: error 4xx o lo acepta silenciosamente?

- **Requisitos:** R2.7.5, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina las validaciones que la app debe hacer del lado cliente antes de publicar.
- **Estudio de APIs:** §10.3: 'el objeto Assignment ya trae rubric y rubric_settings embebidos... suele bastar' (no verificado).

### P578. ¿En qué unidad trabaja el corrector la nota: puntos del assignment (`points_possible`), porcentaje, o escala 1.0–7.0? ¿Cómo se mapea a `submission[posted_grade]` según el `grading_type` del assignment (`points`, `percent`, `letter_grade`, `gpa_scale`, `pass_fail`)? ¿Qué validaciones aplican (rango, decimales, coma vs punto, `points_possible=0`)?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el campo de nota, sus validaciones y el formato de publicación; un desajuste con grading_type produce notas erróneas en Canvas.
- **Opciones planteadas:**
  - Puntos del assignment
  - Escala 1.0–7.0 convertida a puntos
  - Según grading_type de Canvas
- **Estudio de APIs:** §10.4 ejemplo `submission[posted_grade]=5.8` y nota de que acepta 'puntos, porcentaje, nota en letra o pass/fail', sin fijar la regla de la app.

### P579. Investigar en la documentación: formatos exactos que acepta `posted_grade` por cada `grading_type` (p. ej. '85%' para percent, 'A' para letter_grade, 'complete'/'incomplete' para pass_fail) y cómo Canvas redondea decimales.

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** Necesario para escribir la regla de conversión y los mensajes de validación.
- **Estudio de APIs:** §10.4 menciona los tipos aceptados sin los formatos concretos.

### P580. El comentario general al estudiante (`comment[text_comment]`): ¿es obligatorio u opcional? ¿La app añade automáticamente un pie con la entrega, el SHA/tag revisado y el nombre del corrector? En tareas grupales, ¿se envía con `comment[group_comment]=true`?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija el contenido mínimo de la corrección y la trazabilidad visible para el estudiante.
- **Estudio de APIs:** §10.4 ejemplo con 'Revisado sobre la versión aa218f5 (entrega parcial)' y `group_comment=true`.

### P581. En tareas grupales: ¿una sola nota para todo el grupo, o notas individuales por integrante? ¿La app lo deriva de `grade_group_students_individually` del assignment de Canvas (y lo valida como parte de la consistencia entre entregas, R2.3.3)? ¿Se permite al corrector ajustar la nota de un integrante específico (p. ej. sin participación detectada en R2.5.4) y se muestran las métricas de participación en la pantalla de corrección?

- **Requisitos:** R2.7.6, R2.3.3, R2.5.4, R2.5.8
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la UI de nota (un campo vs uno por integrante), el payload (una llamada vs N) y la relación con el monitoreo.
- **Opciones planteadas:**
  - Siempre nota grupal única
  - Siempre individual
  - Según grade_group_students_individually, con override manual por integrante
- **Estudio de APIs:** §10.4: 'Lean ese campo antes de calificar o van a dejar a medio grupo sin nota'; §5.1 lo lista como campo relevante.

### P582. ¿Con qué token se escriben las notas en Canvas: (A) el token del profesor que vinculó el curso (la app actúa 'en nombre del curso'; Canvas registrará al profesor como calificador), o (B) el token OAuth propio de cada ayudante (requiere que esté enrolado como TA en Canvas)? ¿Se muestra en la UI 'se publicará como Profesor X'? ¿La app guarda internamente quién corrigió realmente?

- **Requisitos:** R2.7.6, R2.1.8
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Es una decisión de arquitectura de autenticación que el estudio recomienda pero el equipo no ha aprobado; afecta el onboarding de ayudantes, la auditoría y qué pasa si el profesor no está disponible.
- **Opciones planteadas:**
  - A: token del profesor
  - B: token del ayudante (TA en Canvas)
  - A con B como fallback
- **Estudio de APIs:** §3.4 recomienda A como default y B como fallback, y pide documentar la decisión ('las notas se publican como Profesor X').

### P583. Dependencia del profesor del curso real: ¿es aceptable para él que en Canvas el 'grader' de todas las notas sea el profesor y no el ayudante que corrigió? Si no, ¿exige que cada ayudante esté enrolado como TA en Canvas y use su propio token?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Puede invalidar la opción A del estudio y obligar a implementar OAuth por ayudante.
- **Estudio de APIs:** §3.4 asume que basta 'mostrarlo en la UI'.

### P584. Verificar contra Canvas real: al publicar con el token del profesor, ¿qué muestra Canvas en `grader_id`/`assessor_id` de la submission y del rubric_assessment? ¿Aparece el nombre del profesor en SpeedGrader como calificador?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Confirma el efecto visible de la opción A y qué debe explicarse en la UI y en la defensa del 7-oct.
- **Estudio de APIs:** §3.4 lo afirma implícitamente sin verificar.

### P585. Si se usa el token del profesor: ¿qué pasa cuando ese profesor es retirado del curso, revoca el token, o el refresh falla mientras un ayudante intenta publicar? ¿Se usa el token de otro co-profesor (R2.1.7)? ¿La publicación se encola (outbox) y la entrega queda 'pendiente de publicación' con reintento automático?

- **Requisitos:** R2.7.6, R2.1.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el fallback de disponibilidad de la escritura a Canvas y un estado adicional de corrección.
- **Estudio de APIs:** §1.1 explica refresh_token; §9.4 propone outbox para notificaciones, no para notas.

### P586. Si se usa el token del ayudante: ¿quién asegura que esté enrolado como TA en Canvas (dependencia del profesor del curso)? ¿Qué pasa con un TA limitado a su sección (`limit_privileges_to_course_section`) al que se le asigna una entrega de otra sección? ¿Un ayudante SIN cuenta Canvas puede corregir en la app y otro usuario publica por él?

- **Requisitos:** R2.7.6, R2.1.8
- **Área declarada:** 2.7
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina validaciones al asignar (sección del TA) y un flujo de 'corrige uno, publica otro'.
- **Estudio de APIs:** §3.4: 'debe tener un TaEnrollment en Canvas'; no menciona TAs limitados a sección.

### P587. ¿Existe el concepto de BORRADOR local (la corrección se guarda en la app y se publica a Canvas con una acción explícita 'Publicar'), o cada guardado va directo a Canvas? ¿Existe publicación masiva por el profesor ('revisar todo y publicar de una vez', p. ej. con `update_grades`)?

- **Requisitos:** R2.7.6, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define los estados 'corregida' vs 'publicada', el botón principal de la pantalla y si hay un flujo de revisión previa del profesor.
- **Opciones planteadas:**
  - Borrador local + publicar explícito
  - Escritura directa a Canvas
  - Borrador + publicación masiva del profesor
- **Estudio de APIs:** §10.4 menciona `POST .../update_grades` (masivo, asíncrono con `Progress`); §10.1 estados 'pendiente / en curso / listo'.

### P588. Investigar en la documentación: si el assignment tiene política de publicación MANUAL en Canvas (notas ocultas hasta 'Post grades'), ¿existe un endpoint REST para 'postear' las notas o solo la mutación GraphQL `postAssignmentGrades`? ¿Cómo se lee la post policy del assignment (`post_manually`)?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** Si las notas quedan ocultas para el estudiante tras publicarlas, la app debe avisarlo u ofrecer la acción; define si el estado 'publicada' significa 'visible al estudiante'.
- **Estudio de APIs:** no lo aborda.

### P589. Ante notas ocultas por post policy manual, ¿la app debe (a) solo mostrar aviso 'la nota está oculta en Canvas', (b) ofrecer 'mostrar notas a estudiantes' para toda la entrega, o (c) no hacer nada y dejarlo en Canvas?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el alcance de R2.7.6 respecto a la visibilidad de la nota y el evento que dispara `notify_graded` (R2.6.7).
- **Opciones planteadas:**
  - Solo aviso
  - Acción 'mostrar notas' en la app
  - Fuera de alcance
- **Estudio de APIs:** no lo aborda.

### P590. Antes de publicar, ¿la app lee la submission actual en Canvas y, si ya tiene nota (puesta en SpeedGrader por el profesor o por otro corrector), bloquea, avisa con comparación ('Canvas: 5.5 por X el 3-oct; tú: 6.0') o sobrescribe sin preguntar?

- **Requisitos:** R2.7.6, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Regla de resolución de conflictos entre la app y Canvas; evita pisar notas puestas fuera de la app.
- **Opciones planteadas:**
  - Bloquear
  - Avisar y confirmar
  - Sobrescribir
- **Estudio de APIs:** §10.5 sugiere mostrar la diferencia 'corregidas en la app vs con nota en Canvas', pero no una regla de conflicto al publicar.

### P591. Idempotencia y fallos de publicación: ante 403/429 de throttling, timeout tras un PUT aplicado, o doble clic en 'Publicar', ¿la app reintenta con backoff, verifica leyendo la submission después, y registra un log de publicaciones (quién, cuándo, payload, respuesta de Canvas)?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la robustez de la escritura y la evidencia auditable para la defensa.
- **Estudio de APIs:** §1.5 describe 403/429 y backoff para lecturas; §9.4 outbox para comunicaciones. No define outbox de notas.

### P592. Concurrencia de publicación con la opción A: si varios ayudantes publican a la vez con el mismo token del profesor, la cuota de Canvas es por token. ¿Las publicaciones se serializan en una cola única por curso o se envían directo desde la request del usuario?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina si 'Publicar' es sincrónico (respuesta inmediata) o asincrónico (estado 'publicando').
- **Estudio de APIs:** §1.5: 'el worker de sincronización debe ser secuencial por curso (concurrencia 1 por token)'; no lo aplica a escrituras de notas.

### P593. Cambios de nota posteriores: ¿se permite reeditar y republicar desde la app una nota ya publicada? ¿Quién puede (solo profesor, el corrector original, cualquiera con permiso)? ¿Se guarda historial de versiones de la corrección? ¿Se notifica al estudiante (`notify_graded`) en cada cambio o solo la primera vez?

- **Requisitos:** R2.7.6, R2.6.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define transiciones 'publicada → en progreso', permisos de edición y el disparador de la notificación de corrección.
- **Estudio de APIs:** §9.4 lista el flag `notify_graded` ('Corrección publicada → Conversation individual') sin detallar repeticiones.

### P594. Si alguien cambia la nota directamente en Canvas (SpeedGrader) después de publicada desde la app, ¿la app lo detecta (sincronizando submissions periódicamente) y actualiza la nota/estado que muestra, o solo muestra lo que ella publicó? ¿Con qué frecuencia y con qué endpoint?

- **Requisitos:** R2.7.6, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina si Canvas es la fuente de verdad del estado 'publicada' y qué mostrar cuando hay divergencia.
- **Estudio de APIs:** §10.5: combinar BD con `submission_summary` ('fuente de verdad de qué está realmente calificado').

### P595. ¿Cuáles son exactamente los estados de corrección (p. ej. sin asignar, asignada, en progreso, corregida, publicada, desactualizada, pendiente de publicación, excusada/sin entrega) y qué evento dispara cada transición: automático al abrir la entrega, acción manual 'marcar lista', éxito del PUT a Canvas, detección de nota en Canvas? ¿Se puede retroceder?

- **Requisitos:** R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es la máquina de estados que sustenta R2.7.7 y la vista del ayudante; sin ella no hay criterios de aceptación.
- **Estudio de APIs:** §10.1: 'pendiente / en curso / listo'; §10.5 añade la dimensión 'con nota en Canvas'.

### P596. Visualización del estado (R2.7.7): ¿matriz estudiante/grupo × entrega con color por estado, con agregados por corrector y por sección y el doble contador 'N corregidas en la app · M con nota en Canvas'? ¿Visible para ayudantes o solo profesores? ¿Incluye sujetos sin repositorio o retirados?

- **Requisitos:** R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la pantalla que demuestra R2.7.7 y sus filtros.
- **Estudio de APIs:** §10.5 sugiere '18/25 corregidas en la app · 17/25 con nota en Canvas'.

### P597. Verificar contra Canvas real: dado que nadie 'entrega' en Canvas, `submission_summary` reportará casi todo como `not_submitted`. ¿Los contadores `graded`/`ungraded` siguen siendo útiles cuando la submission está `unsubmitted` pero con nota? ¿O la app debe leer las submissions individuales (`workflow_state`, `score`, `graded_at`, `grader_id`) para el estado por sujeto?

- **Requisitos:** R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Determina la fuente Canvas del estado 'publicada' por sujeto y su costo en requests.
- **Estudio de APIs:** §10.4 propone `submission_summary` como 'directo para el requisito 2.7.7' sin considerar que no habrá submissions.

### P598. Dado que el repositorio ES la entrega, ¿la app exige o recomienda al vincular la entrega (R2.3.1) que el assignment de Canvas tenga `submission_types` = `none`/`on_paper`/`online_url`, y advierte si es `online_upload` u otro tipo que confunda al estudiante? ¿Se valida también que esté `published`?

- **Requisitos:** R2.7.6, R2.3.1
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Es una validación del wizard de vinculación (demostrado en la parcial) que evita que los estudiantes intenten entregar archivos en Canvas.
- **Opciones planteadas:**
  - Exigir tipo compatible
  - Solo advertir
  - No validar
- **Estudio de APIs:** §5.1 menciona `submission_types` solo como útil para la tarea de recolección de usuarios GitHub; §5.1 recomienda no crear repos para tareas no publicadas.

### P599. Verificar contra Canvas real: ¿`PUT .../submissions/:user_id` con `posted_grade` (y `rubric_assessment`) sobre una submission `unsubmitted` de un assignment con `submission_types=none` crea la nota y aparece en el gradebook y en SpeedGrader? ¿Y con `on_paper`?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Toda la corrección depende de poder calificar sin que el estudiante haya entregado nada en Canvas.
- **Estudio de APIs:** §10.4 asume que funciona sin mencionar el caso sin submission.

### P600. ¿La app deja algún rastro en la submission de Canvas al cierre de cada entrega (p. ej. comentario con la URL `tree/<sha>` y la fecha de captura, visible al estudiante), de modo que el estudiante y el corrector vean en Canvas qué versión se evaluará? ¿O el SHA solo vive en la app?

- **Requisitos:** R2.7.6, R2.4.5, R2.3.12
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la transparencia hacia el estudiante y si el comentario de corrección (R2.7.6) debe referenciar ese rastro.
- **Estudio de APIs:** §5.7 usa el comentario en la submission para informar la URL del repo al crearlo (R2.3.12); no para el snapshot.

### P601. ¿Existe el concepto de 'entrega atrasada' cuando la entrega es el snapshot al cierre? Opciones: no existe (lo que había al cierre es lo que se corrige); se informa al corrector 'N commits después del cierre' sin efecto; el profesor puede aceptar una entrega tardía eligiendo un SHA posterior con penalización; se marca `late_policy_status=late` en Canvas.

- **Requisitos:** R2.7.4, R2.7.6, R2.4.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si la pantalla de corrección tiene selector de versión alternativa y si se usa `late_policy_status`.
- **Opciones planteadas:**
  - No existe atraso
  - Informativo
  - Aceptar SHA posterior con penalización
  - Marcar late en Canvas
- **Estudio de APIs:** §10.4 lista `submission[late_policy_status]` sin regla; §7.5 fija el snapshot como versión única.

### P602. ¿La app aplica penalizaciones (por atraso aceptado, por integrante sin participación, etc.) sobre la nota antes de publicar, con una fórmula configurable por tarea, o eso queda fuera de alcance y se hace en Canvas?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Añadiría configuración por tarea y lógica de cálculo; hay que fijar explícitamente si está dentro o fuera.
- **Estudio de APIs:** no lo aborda.

### P603. ¿La pantalla de corrección permite marcar una entrega como excusada (`submission[excuse]=true`) o 'missing' (`late_policy_status=missing`)? ¿Quién puede hacerlo (corrector o solo profesor)?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define acciones adicionales del corrector y sus permisos.
- **Estudio de APIs:** §10.4 lista `submission[excuse]` y `late_policy_status` como parámetros disponibles.

### P604. Si la tarea de Canvas vinculada a una entrega es ELIMINADA o despublicada después de haber asignado o corregido, ¿la vista de corrección bloquea la publicación, muestra un aviso y conserva el estado histórico, o marca la entrega como inválida? ¿Cómo se detecta (404 en el polling)?

- **Requisitos:** R2.7.6, R2.7.7, R2.4.4
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el manejo de un dato roto en medio del flujo de corrección.
- **Estudio de APIs:** §7.4 describe el polling de assignments, sin el caso de eliminación.

### P605. Concurrencia: dos usuarios (corrector y profesor, o dos correctores tras una reasignación) editan la misma entrega a la vez; o dos profesores ejecutan la asignación automática simultáneamente. ¿Bloqueo optimista con aviso, 'última escritura gana', o lock por entrega mientras está abierta?

- **Requisitos:** R2.7.1, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita pérdida silenciosa de correcciones y asignaciones duplicadas.
- **Estudio de APIs:** no lo aborda.

### P606. Dentro de los ≥3 permisos de R2.1.8, ¿cuáles gobiernan 2.7 exactamente: ver la vista de corrección de una entrega no asignada, ver rúbrica y notas de otros, publicar en Canvas, reasignar? ¿Un ayudante sin permiso de corrección puede ver el código de las entregas?

- **Requisitos:** R2.1.8, R2.7.2, R2.7.5, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El modelo de permisos se define desde la parcial y debe contemplar las acciones de corrección para no rehacerlo.
- **Estudio de APIs:** §3.4 propone `grading.assign` y `grading.submit (solo asignadas)`; no define lectura.

### P607. Estudiantes para quienes la entrega no existe en Canvas (`only_visible_to_overrides=true` sin override) y el Test Student: ¿se excluyen de la asignación de correctores y del estado de corrección? ¿Se cruza con `gradeable_students` de Canvas para decidir a quién se puede calificar?

- **Requisitos:** R2.7.1, R2.7.7, R2.4.3
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita asignar y contar sujetos que Canvas no permite calificar.
- **Estudio de APIs:** §7.3: 'la tarea no existe para él; no le creen snapshot ni lo cuenten como atrasado'; §10.4 menciona `gradeable_students`.

### P608. ¿En qué zona horaria se muestran en la vista de corrección la fecha efectiva de cierre, el 'capturado el' y el 'publicado el' (America/Santiago fija, la del navegador, con offset explícito)? ¿Se muestra el origen de la fecha efectiva (base/sección/extensión)?

- **Requisitos:** R2.7.4, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Un corrector que ve una hora desplazada 3 h desconfía del snapshot; hay que fijar la regla de presentación.
- **Estudio de APIs:** §14: 'Guarden todo en UTC y conviertan solo al renderizar'; no fija la zona de presentación.

### P609. Al corregir la entrega N de una tarea con múltiples entregas, ¿la pantalla muestra contexto de las entregas anteriores del mismo estudiante/grupo (nota, comentario, SHA, corrector) y el diff respecto a la anterior?

- **Requisitos:** R2.7.3, R2.7.4, R2.3.2
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si la vista de corrección es por entrega aislada o con historial, lo que afecta consultas y layout.
- **Estudio de APIs:** §7.5 sugiere el `compare` entre entregas como extra.

### P610. La comunicación al estudiante al publicar la nota (`notify_graded`, R2.6.7): ¿se envía por cada publicación individual, o una vez cuando el profesor cierra la corrección de toda la entrega? ¿Por Conversation, por comentario en la submission, o ambos? ¿Qué contenido incluye (nota, link al SHA, comentario)?

- **Requisitos:** R2.7.6, R2.6.7, R2.6.5
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cruce entre 2.7 y 2.6: define el disparador y el canal de la notificación de corrección.
- **Estudio de APIs:** §9.4: evento 'Corrección publicada → Conversation individual' con flag `notify_graded`.

### P611. Dependencia externa: si la Developer Key de Canvas tiene 'enforce scopes', ¿incluye los scopes `url:PUT|/api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id`, `url:GET|.../rubrics`, `url:GET|.../submission_summary` y `url:POST|.../update_grades`? ¿Quién los solicita al administrador y cuándo?

- **Requisitos:** R2.7.5, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin esos scopes la corrección no puede escribir en Canvas aunque el código esté listo.
- **Estudio de APIs:** §1.3 lista los scopes de GET submissions, PUT submissions y GET rubrics; no lista submission_summary ni update_grades.

### P612. Si el curso usa períodos de calificación (grading periods) y el período al que pertenece la tarea está CERRADO al momento de publicar, Canvas rechaza cambios de nota salvo para ciertos roles. ¿La app detecta ese caso (leyendo grading periods / la respuesta de error del PUT), qué mensaje muestra al corrector y cuál es el estado resultante de la corrección ('bloqueada por período cerrado')? ¿Se valida al vincular la entrega o al asignar correctores que el período estará abierto en la fecha estimada de corrección?

- **Requisitos:** R2.7.6, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Es una causa realista de fallo al publicar notas semanas después del cierre; sin detección el corrector ve un error genérico y el estado 2.7.7 queda inconsistente.
- **Opciones planteadas:**
  - Detectar y mostrar error accionable con enlace a Canvas
  - Validar anticipadamente al vincular/asignar
  - No manejar; error genérico
- **Estudio de APIs:** no lo aborda (§10.4 no menciona grading periods).

### P613. Los estudiantes pueden dejar submissions espontáneas en la tarea de Canvas de una entrega (subir un zip o un texto por confusión), y si el curso tiene una late policy con deducción automática, Canvas marcará esa submission como 'late' y REDUCIRÁ la nota que la app publique. ¿La app detecta y muestra al docente las submissions hechas por estudiantes en tareas de entrega ('3 estudiantes subieron algo en Canvas; el repo es la entrega')? ¿Al publicar la nota envía late_policy_status=none (o el valor que el corrector decida) para neutralizar la deducción, advierte al vincular si el curso tiene late policy, o ignora el tema? Verificar empíricamente si la deducción se aplica a notas puestas por API sobre una submission tardía.

- **Requisitos:** R2.7.6, R2.3.1, R2.4.5, R2.3.12
- **Área declarada:** 2.7 / 2.3
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** Puede alterar silenciosamente las notas publicadas y confundir a estudiantes que creen haber 'entregado' en Canvas; el docente necesita verlo.
- **Opciones planteadas:**
  - Detectar submissions del estudiante y mostrarlas en la vista de la entrega
  - Enviar late_policy_status explícito al publicar
  - Advertir al vincular si existe late policy en el curso
  - Ignorar
- **Estudio de APIs:** §10.4 menciona late_policy_status como parámetro y §5.1 submission_types; no aborda late policies automáticas ni submissions espontáneas en tareas de entrega.

### P614. Las rúbricas de Canvas pueden incluir criterios ligados a resultados de aprendizaje (learning_outcome_id, mastery_points) y criterios con ignore_for_scoring=true. ¿Cómo los muestra la grilla de rúbrica de la app, se envían en rubric_assessment igual que los demás, y se excluyen del cálculo de la nota sugerida cuando ignore_for_scoring es true? Investigar en la documentación de Rubrics/RubricCriterion y verificar cómo Canvas calcula el score en esos casos.

- **Requisitos:** R2.7.5, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** Si la app suma puntos de criterios que Canvas ignora, la nota sugerida y la publicada diferirán y el corrector no entenderá por qué.
- **Estudio de APIs:** §10.3 lista los campos de Rubric/RubricCriterion sin learning_outcome_id, mastery_points ni ignore_for_scoring.

### P615. ¿La pantalla de corrección permite guardar NOTAS INTERNAS del corrector (visibles solo para el equipo docente, nunca enviadas a Canvas) y banderas por entrega ('revisar con profesor', 'posible copia', 'caso especial'), que además aparezcan en el estado de corrección (R2.7.7) y en el informe diario? Si sí, ¿quién puede verlas y editarlas (todos los correctores, solo profesor + autor) y quedan en auditoría?

- **Requisitos:** R2.7.2, R2.7.6, R2.7.7, R2.1.8
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Los correctores necesitan un canal privado distinto del comentario a Canvas; sin él escribirán observaciones sensibles en comentarios visibles al estudiante.
- **Opciones planteadas:**
  - Notas internas + banderas con visibilidad por rol
  - Solo banderas predefinidas
  - Nada; usar el comentario de Canvas
- **Estudio de APIs:** no lo aborda (§10 solo contempla comentarios que se publican en Canvas).

### P616. ¿Existe una fecha objetivo de corrección por entrega (definida por el profesor) y se alerta sobre correcciones atrasadas: en la vista de estado (R2.7.7, 'X entregas sin corregir a N días del cierre'), en el informe diario del profesor (avance por corrector) y en el informe del ayudante (sus pendientes)? ¿El ayudante recibe un email o notificación in-app cuando se le asignan o reasignan entregas, o debe descubrirlo entrando a la app?

- **Requisitos:** R2.7.1, R2.7.7, R2.6.2, R2.6.4
- **Área declarada:** 2.7 / 2.6
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Convierte 2.7.7 en una herramienta de gestión real y define qué contenido de corrección lleva el informe de 2.6.
- **Opciones planteadas:**
  - Fecha objetivo por entrega + alertas en informe y UI
  - Solo contador de pendientes sin plazo
  - Email al ayudante al asignar
  - Nada
- **Estudio de APIs:** §9.1 enumera el contenido del informe sin avance de corrección; §10.5 define el estado de corrección sin plazos.

### P617. El corrector necesita EJECUTAR el código, no solo mirarlo en GitHub. ¿La vista de corrección ofrece descarga del snapshot como .zip (GET /repos/{o}/{r}/zipball/{sha} vía el token de la App, sin requerir que el ayudante tenga acceso a la org), muestra los comandos exactos (git clone + git checkout <sha> o git fetch origin tag entrega-N), o solo el enlace tree/<sha>? Si es zip vía la App, ¿se controla quién puede descargarlo (permiso) y se registra?

- **Requisitos:** R2.7.4, R2.4.8
- **Área declarada:** 2.7 / 2.4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si un ayudante sin cuenta GitHub o sin acceso a la org puede corregir, y qué permisos de la App y de RBAC se necesitan.
- **Opciones planteadas:**
  - Descarga zip vía App con control de permiso
  - Comandos git mostrados en la vista
  - Solo enlace tree/<sha>
- **Estudio de APIs:** §7.5 paso 4 y §10.2 solo proponen enlaces web (tree, compare, commits) al SHA.

### P618. ¿Existe una vista transversal fuera del árbol de cursos (p.ej., 'Mis correcciones' o 'Mis pendientes') que agregue, para el usuario logueado, las entregas asignadas y alertas de TODOS sus cursos, o el ayudante siempre debe entrar curso→tarea→corrección? ¿Es esa vista la home del ayudante?

- **Requisitos:** R2.7.2, R2.7.3, R2.6.2
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.7.2 exige que el ayudante identifique 'fácilmente' sus entregas; la respuesta define la home según rol y si se necesita un modelo de datos de 'pendientes por usuario' cruzando cursos.
- **Estudio de APIs:** §10.1 propone una vista 'Mis correcciones' filtrada por grader_user_id, sin indicar si es por tarea, por curso o global.

### P619. ¿Cuál es el layout de la pantalla de corrección: rúbrica de Canvas a un lado y enlace/resumen del snapshot al otro; botón 'siguiente sin corregir'; atajos de teclado; guardado de borrador local antes de publicar en Canvas; indicador 'en revisión por X' visible para otros correctores? ¿Qué se muestra si la entrega no tiene snapshot (sin commits antes del cierre), si la tarea no tiene rúbrica en Canvas, o si el estudiante ya tiene nota en Canvas puesta desde fuera de la app?

- **Requisitos:** R2.7.2, R2.7.3, R2.7.4, R2.7.5, R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la pantalla más usada por ayudantes y sus estados borde; R2.7.3 exige navegación 'sencilla'.
- **Estudio de APIs:** §10.1 propone navegación anterior/siguiente con atajos y 'siguiente sin corregir'; §10.2 sugiere mostrar 'capturado el … · 47 commits'; §10.3 propone rúbrica como grilla clickeable; §7.5 define status NO_COMMITS.

### P620. Al publicar una nota en Canvas para una tarea grupal, ¿la UI muestra explícitamente el alcance antes de confirmar ('esta nota se aplicará a los 3 integrantes' vs 'solo a Ana Díaz', según la configuración de Canvas)? ¿Se indica con qué identidad se publica ('se registrará como Profesor X') si la app usa el token del profesor? ¿Qué feedback se da tras publicar (éxito con enlace al SpeedGrader / error con reintento)?

- **Requisitos:** R2.7.6
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Evita medio grupo sin nota y sorpresas sobre autoría en Canvas; define el modal de confirmación y el estado post-publicación.
- **Estudio de APIs:** §10.4 advierte leer grade_group_students_individually antes de calificar; §3.4 recomienda mostrar en UI 'las notas se publican como Profesor X'.

### P621. Para asignar entregas a correctores (R2.7.1): ¿asignación manual por fila (select), selección múltiple + 'asignar a…', reparto automático equitativo o por sección, arrastrar y soltar? ¿Se puede reasignar en bloque? ¿Cómo se muestra el estado de corrección (R2.7.7): por corrector y por entrega, con la doble cifra 'corregidas en la app' vs 'con nota en Canvas' y qué significa la discrepancia para el usuario?

- **Requisitos:** R2.7.1, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la pantalla de distribución del trabajo y la semántica de los estados de corrección visibles.
- **Estudio de APIs:** §10.1 propone manual (drag & drop o selects) + automática (equitativa o por sección); §10.5 propone mostrar '18/25 corregidas en la app · 17/25 con nota en Canvas'.

### P622. ¿El grano de GradingAssignment y GradingRecord es (entrega, repositorio) o (entrega, estudiante)? Con grade_group_students_individually=true cada integrante recibe nota propia: ¿un GradingRecord por integrante compartiendo rubric_assessment y comentario, un único registro con notas por integrante en JSON, o se bloquea la corrección desde la app para tareas grupales con notas individuales? ¿Cómo se representa el estado agregado 'corregida' de un repo cuando falta publicar a un integrante, y qué pasa con el integrante que ya no está en el grupo al publicar?

- **Requisitos:** R2.7.1, R2.7.6, R2.7.7
- **Área declarada:** 2.7
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define las claves de las tablas de corrección, el número de PUT a Canvas por entrega y el cálculo de R2.7.7.
- **Opciones planteadas:**
  - Grano repositorio con notas por integrante en JSON
  - Grano estudiante con rúbrica compartida
  - Bloquear grupal-individual desde la app
- **Estudio de APIs:** §10.1 grading_assignment(delivery_id, repository_id, grader_user_id, status) con grano repositorio; §10.4 advierte llamar por cada integrante si el flag es true.

---

## 3.1

### P623. ¿Cuál es la lista cerrada de requisitos que se demostrarán el 16-sep y cuáles quedan explícitamente fuera del alcance parcial? El enunciado nombra: usuario profesor → curso → vincular Canvas y GitHub → tarea individual → asociación estudiantes↔GitHub → repos automáticos. ¿Entran en la parcial R2.1.6 (checklist de verificación), R2.3.5/R2.3.6 (repo base con archivos), R2.3.9 (agregar colaboradores), R2.3.11 (tabla de estados), R2.3.12 (aviso al estudiante por Canvas), R2.2.6 (panel de faltantes), R2.1.7/R2.1.8 (co-profesores y ayudantes)?

- **Requisitos:** R2.1.1, R2.1.3, R2.1.4, R2.1.5, R2.1.6, R2.2.4, R2.2.6, R2.3.1, R2.3.5, R2.3.6, R2.3.7, R2.3.9, R2.3.11, R2.3.12, R2.1.7, R2.1.8
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el backlog de los 8 días restantes y qué pantallas deben existir con datos; lo no listado se declara en el spec como 'fuera de alcance parcial' para que nadie lo dé por exigido ni por omitido.
- **Opciones planteadas:**
  - Solo lo literal del enunciado (sin repo base, sin ayudantes, sin notificación)
  - Literal + R2.1.6 + R2.3.11 + R2.3.12 (plan §13)
  - Literal + repo base opcional R2.3.5/R2.3.6
- **Estudio de APIs:** §13 propone 10 hitos mínimos que incluyen checklist de verificación (§3.3), recolección por tarea de Canvas, worker + tabla de estados y notificación al estudiante; no incluye repo base ni ayudantes.

### P624. Para la 'tarea individual' de la demo parcial, ¿la tarea de la app se vincula a UNA sola tarea de Canvas (una entrega) o ya se demuestra la vinculación 1..N (parcial + final) aunque no existan snapshots? ¿La validación de consistencia individual/grupal entre entregas (R2.3.3) se muestra en la parcial o se posterga a la final?

- **Requisitos:** R2.3.1, R2.3.2, R2.3.3
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Determina si el modelo Tarea→Entregas y su UI de vinculación múltiple entran en el sprint de la parcial o quedan como alcance de la final.
- **Estudio de APIs:** §5.2 define el modelo Assignment→Delivery 1..N y recomienda rechazar la segunda tarea de Canvas si su group_category_id difiere.

### P625. En la demo parcial, ¿la 'creación de un usuario profesor' se hace con Google OAuth real (cuenta gmail.com) o con un formulario propio? Si es Google OAuth: ¿el proyecto de Google Cloud estará en modo 'Testing' (máximo 100 usuarios de prueba que deben registrarse por correo) o 'Production'? ¿Hay que pedir los correos gmail del profesor y de los ayudantes para agregarlos como test users antes del 16-sep?

- **Requisitos:** R2.1.1, R2.1.2
- **Área declarada:** 3.1
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Si la pantalla de consentimiento está en Testing y el revisor no está registrado, no podrá entrar a la app y ninguna funcionalidad se considerará cumplida.
- **Opciones planteadas:**
  - Testing + registrar correos de revisores
  - Publicar a Production
  - Formulario propio como respaldo
- **Estudio de APIs:** §3.1 indica validar que el claim email termine en @gmail.com y email_verified; no aborda el modo de publicación del consent screen ni los test users.

### P626. ¿La restricción 'cuenta de correo basada en gmail.com' se implementa como rechazo estricto de cualquier dominio distinto a @gmail.com? Si el profesor o los ayudantes intentan entrar con su cuenta institucional Google Workspace (p. ej. @uandes.cl), ¿se les rechaza con un mensaje? ¿Se pedirá a los revisores que usen un gmail personal?

- **Requisitos:** R2.1.2
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija la regla de validación del login y su texto de error; un rechazo estricto puede impedir que el revisor entre con la cuenta que tiene a mano el día de la revisión.
- **Opciones planteadas:**
  - Estricto @gmail.com
  - Cualquier cuenta Google con email_verified
  - Estricto @gmail.com + lista blanca configurable de correos
- **Estudio de APIs:** §3.1 recomienda validar el sufijo @gmail.com (nota que el claim hd no viene para gmail puro).

### P627. ¿La UI de vinculación con Canvas ofrecerá un modo 'pegar token de acceso' además de OAuth2? Si sí: ¿visible para todos los usuarios, solo detrás de un flag de entorno, o solo en desarrollo? ¿Se muestra al revisor el 16-sep?

- **Requisitos:** R2.1.4, R2.1.6
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** El modo token es el respaldo si falla la Developer Key, pero exhibirlo puede evaluarse como incumplimiento de la política de Canvas; hay que decidir si existe como requisito del spec o como herramienta interna.
- **Opciones planteadas:**
  - Solo OAuth2
  - OAuth2 + token manual detrás de feature flag
  - OAuth2 + token manual visible con advertencia
- **Estudio de APIs:** §1.2 recomienda implementar OAuth2 igual aunque en la demo usen un token pegado a mano.

### P628. ¿En la demo del 16-sep los repositorios se crearán EN VIVO (esperando el ciclo del worker) o se mostrarán ya creados antes de la presentación? Si es en vivo: ¿el intervalo del worker es configurable por entorno (p. ej. 15 s en demo, 2 min en producción)? ¿Existirá un botón 'procesar ahora' y, de existir, cómo se concilia con R2.3.10 ('sin interacción directa de un usuario')?

- **Requisitos:** R2.3.7, R2.3.10, R2.3.11
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija el intervalo del cron, la existencia de un disparador manual y el guion de la demo; una espera de 2 minutos en silencio frente al profesor es un riesgo de usabilidad.
- **Opciones planteadas:**
  - Todo en vivo con intervalo corto configurable
  - Pre-creado + un caso nuevo en vivo
  - Pre-creado + video de respaldo
- **Estudio de APIs:** §5.5 propone cron cada 2 min y throttle ~1 repo cada 3 s; §7.4 sugiere botón 'sincronizar ahora' para datos de Canvas; §13 propone que 'el worker crea los repos en vivo'.

### P629. ¿La demo parcial incluirá deliberadamente al menos un estudiante sin usuario GitHub, uno con usuario inexistente u organización, y una invitación sin aceptar, para mostrar los estados de problema? ¿Se resuelve uno de ellos en vivo (el docente corrige el usuario y el worker crea el repo) para demostrar R2.2.5?

- **Requisitos:** R2.2.5, R2.2.6, R2.3.11
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Sin casos problemáticos visibles, R2.3.11 y R2.2.6 no pueden considerarse demostrados en la revisión.
- **Estudio de APIs:** §13 recomienda 'dejen visible un caso con problema'; §5.6 muestra una tabla de estados con ejemplo de cada tipo.

### P630. ¿Cuánto dura el slot de demo del 16-sep, en qué formato se realiza (equipo frente al curso, por mesas, ante profesor y ayudantes) y con qué recursos del aula (proyector, red Wi-Fi, restricciones de puertos)? ¿Se puede pedir esta información al profesor antes de escribir el guion?

- **Requisitos:** —
- **Área declarada:** 3.1
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** El guion de demo, el número de casos a mostrar y el intervalo del worker dependen del tiempo disponible y de la conectividad del aula.
- **Estudio de APIs:** §13 propone un guion de ≈6 min sin conocer el slot real.

### P631. El 'link para acceder a su entrega' del 16-sep, ¿será una URL pública desplegada con workers/cron activos 24/7 que los ayudantes puedan usar después de la clase, o un link a repositorio con instrucciones para correr localmente? Si es pública, ¿en qué proveedor, con qué plan y qué fecha de primer deploy?

- **Requisitos:** R2.3.10
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Los ayudantes probarán fuera del aula; sin deploy permanente el worker automático (R2.3.10) no correrá y la creación automática no será verificable por ellos.
- **Estudio de APIs:** §13 hito 10: 'Deploy con URL pública, nunca la noche anterior, Día 6'; §12 sugiere Railway/Render/Fly.io.

### P632. ¿Cómo prueban la app los ayudantes y el profesor, que no tienen Developer Key ni org propia? (a) credenciales de una cuenta profesor demo ya vinculada al Canvas y org de prueba; (b) cada revisor se registra con su gmail y el equipo lo agrega como co-profesor (R2.1.7) del curso demo; (c) el revisor vincula su propio curso Canvas y su propia org (solo viable si la Developer Key es de la instancia institucional y la App es pública). ¿Se entregará junto al link un documento de acceso con cuentas, contraseñas y guion de prueba?

- **Requisitos:** R2.1.1, R2.1.2, R2.1.4, R2.1.5, R2.1.7
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define qué pantallas debe poder recorrer un revisor sin ayuda y qué material acompaña el link entregado por Canvas.
- **Estudio de APIs:** No lo aborda directamente; §3.4 describe co-profesores gestionados en la BD propia.

### P633. Si varios revisores usan la misma cuenta/curso demo en paralelo, ¿cómo se evita que se pisen (crear tareas duplicadas, retirar al único ayudante, generar decenas de repos en la org, desvincular el Canvas)? ¿Habrá un curso demo 'de exhibición' con datos ricos y otro 'sandbox' para que el revisor cree cosas? ¿Se resetea el sandbox por seed cada noche o bajo demanda, y quién lo ejecuta?

- **Requisitos:** R2.1.3, R2.1.9, R2.3.7
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define la política de seeds/reset, los permisos del usuario demo y si hace falta un procedimiento de restauración.
- **Estudio de APIs:** No lo aborda.

### P634. ¿Se invitará al profesor y ayudantes como Teacher/Observer en el curso Canvas de prueba y como miembros de la org GitHub demo para que puedan ver 'el otro lado' (mensajes recibidos por los estudiantes, anuncios, notas publicadas, repos creados)? ¿Se les pedirán sus correos y usuarios GitHub, y para qué fecha?

- **Requisitos:** R2.3.12, R2.6.5, R2.6.6, R2.7.6
- **Área declarada:** 3.1
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Sin acceso a Canvas y GitHub, los efectos externos de la app (R2.3.12, R2.6.x, R2.7.6) solo se verían por captura de pantalla.
- **Estudio de APIs:** No lo aborda.

### P635. Si un revisor entra con rol 'ayudante' (permisos restringidos), no podrá acceder a funciones de profesor y podrían considerarse no cumplidas. ¿Se entregan a los revisores credenciales de profesor Y de ayudante (para demostrar también R2.1.8 y la vista 'mis correcciones'), o solo de profesor con instrucciones para crear ayudantes?

- **Requisitos:** R2.1.8, R2.7.2
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el conjunto de cuentas demo y el guion de revisión de la final.
- **Estudio de APIs:** §3.4 propone tres roles (profesor, ayudante jefe, ayudante) con matriz de permisos.

### P636. ¿Se pedirá al profesor acceso (Teacher o TA) al curso real de ICC4201 en la instancia institucional para probar con datos reales? Si sí, ¿qué salvaguardas se exigen para no crear tareas, anuncios, mensajes ni repos sobre estudiantes reales (modo 'solo lectura' por curso, lista blanca de cursos escribibles)?

- **Requisitos:** R2.1.4, R2.2.1, R2.6.5, R2.6.6
- **Área declarada:** 3.1
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Probar contra datos reales cambia el riesgo (efectos sobre personas reales) y podría agregar al spec un flag de curso de solo lectura.
- **Estudio de APIs:** §13 hito 1 habla de 'Canvas de pruebas con datos reales' sin distinguir instancia real vs de prueba.

### P637. ¿Qué se sube exactamente a Canvas en cada entrega: (parcial) URL + credenciales demo + guion de prueba; (final) URL, link al repo, link al video, declaración de IA, documento de acceso? ¿Quién lo sube y a qué hora límite interna anterior a las 13:30 / 16:00 oficiales?

- **Requisitos:** —
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Evita omisiones el día de la entrega y define documentos que el equipo debe redactar.
- **Estudio de APIs:** No lo aborda.

### P638. En la demo presencial, ¿se mostrará el lado Canvas y GitHub en vivo (pestañas con el curso de Canvas y la org) para que el profesor verifique que los repos, colaboradores y mensajes existen realmente, o solo la UI de la app? ¿Qué cuentas deben estar logueadas simultáneamente en el navegador de la demo?

- **Requisitos:** R2.1.6, R2.3.9, R2.3.12
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el guion y el estado previo del navegador; muestra que la integración es real y no simulada.
- **Estudio de APIs:** §13 guion incluye 'abrir un repo en GitHub' y 'mostrar el mensaje que le llegó al estudiante en Canvas'.

### P639. Para la demo del 16-sep, ¿qué alcance de 2.3 se demuestra: solo tarea individual con una entrega, o también repo base con archivos y multi-entrega? ¿El worker corre solo en background con qué frecuencia para que se vea en vivo? ¿Se prepara deliberadamente un caso con problema (sin mapeo, invitación pendiente, usuario inválido)? ¿Se muestra el mensaje recibido en Canvas?

- **Requisitos:** R2.3.1, R2.3.5, R2.3.7, R2.3.10, R2.3.11, R2.3.12
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define el guion de demo y qué requisitos de 2.3 deben estar completos al 16-sep vs al 6-oct.
- **Estudio de APIs:** §13 propone guion de demo y recomienda 'dejen visible un caso con problema' para R2.3.11.

### P640. En la build del 16-sep, ¿cómo se presentan las funciones que no están listas para que el evaluador que 'se salga del guion' no encuentre comportamientos rotos: se BLOQUEA explícitamente vincular tareas grupales ('disponible en la entrega final') o se permite con comportamiento parcial; las secciones 2.4–2.7 (fechas, dashboard, informes, corrección) se ocultan por completo, se muestran deshabilitadas con etiqueta, o aparecen con datos vacíos? ¿Se usa un feature flag por entorno?

- **Requisitos:** R2.3.3, R2.4.1, R2.5.1, R2.6.1, R2.7.1
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** El evaluador evaluará usabilidad; una pantalla a medias o un error 500 al probar algo fuera del flujo penaliza más que una función oculta.
- **Opciones planteadas:**
  - Bloquear con mensaje explícito
  - Ocultar por feature flag
  - Mostrar deshabilitado con etiqueta 'próximamente'
  - Permitir con comportamiento parcial
- **Estudio de APIs:** §13 define el mínimo indispensable de la parcial; no aborda cómo presentar lo no implementado.

### P641. Además de los casos con problema de mapeo, ¿qué fallos de VINCULACIÓN se prepararán para que el evaluador los provoque o vea en la demo del 16-sep: elegir un curso de Canvas donde el usuario no es profesor, instalar la App en la cuenta personal en vez de una org, cancelar la instalación a mitad, org donde la App fue desinstalada, rechazar el consentimiento de Canvas? ¿Cada uno muestra el ítem rojo del checklist con acción correctiva y se recupera sin recrear el curso?

- **Requisitos:** R2.1.4, R2.1.5, R2.1.6
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** La 'guía adecuada' de R2.1.6 se evalúa sobre todo en los caminos de error, no en el camino feliz.
- **Opciones planteadas:**
  - Preparar 2–3 fallos de vinculación reproducibles en vivo
  - Solo camino feliz + fallos de mapeo
- **Estudio de APIs:** §3.3 propone el checklist con botón reintentar y §13 sugiere dejar visible un caso con problema, pero solo de mapeo de estudiantes.

### P642. ¿Qué guion de demo adopta el equipo para el 16-sep y qué caso con problema se mostrará deliberadamente (estudiante que no entregó usuario, usuario inexistente, usuario que es una Organization, invitación pendiente sin aceptar)? ¿Cómo se resuelve en vivo (el 'estudiante' entrega desde Canvas en otro navegador; el docente lo carga manualmente; se acepta la invitación desde una cuenta GitHub del equipo)? ¿Qué datos semilla se preparan (Canvas de prueba con N estudiantes, secciones, cuentas GitHub controladas por el equipo)?

- **Requisitos:** R2.3.11, R2.2.6
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** El guion determina qué pantallas deben estar pulidas primero y qué cuentas externas hay que conseguir; mostrar un caso problemático es necesario para evidenciar R2.3.11.
- **Estudio de APIs:** §13 propone un guion de ~6 min y recomienda 'dejen visible un caso con problema'; §13 hito 1 pide Canvas de pruebas con 2 secciones, ~10 estudiantes, 1 group set.

### P643. Con cron de aprovisionamiento cada 2 min y sync de Canvas cada 10 min, ¿la demo acepta esas esperas o se requiere que los intervalos sean configurables por entorno (más cortos en demo) y/o un 'sincronizar ahora'? ¿La UI muestra 'próxima ejecución en X s' para que el público entienda la espera? ¿Cuánto tiempo total debe durar el flujo completo en la demo?

- **Requisitos:** R2.3.10, R2.4.4
- **Área declarada:** 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define parámetros configurables del sistema y un indicador de UI; evita minutos de silencio en una demo presencial evaluada.
- **Estudio de APIs:** §12 fija intervalos (sync 10 min, provision 2 min, snapshots 5 min, backfill 15 min); §7.4 sugiere 'sincronizar ahora' para 'corregir la percepción de datos viejos durante la demo'.

### P644. El link entregado por Canvas debe poder ser usado por ayudantes y profesor del curso. ¿Se les entrega un curso demo ya cargado y cuentas de prueba (Canvas y GitHub) para reproducir el flujo, o deben registrarse con su propio gmail y vincular sus propios Canvas/GitHub desde cero? ¿La landing incluye instrucciones de primer uso y prerrequisitos (tener rol Teacher en un curso Canvas de la instancia soportada, tener una org GitHub)?

- **Requisitos:** R2.1.1, R2.1.2
- **Área declarada:** 3.1
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define la landing, la documentación de primer uso y qué recursos externos hay que preparar para que la revisión con la herramienta sea posible (sección 4: lo no accesible no cuenta).
- **Estudio de APIs:** §1.2 sugiere Free-for-Teacher como entorno para demo; §13 hito 10 exige deploy con URL pública; no aborda cómo el revisor reproduce el flujo.

---

## 3.2

### P645. Para el video de máximo 3 minutos: ¿qué flujo se muestra y en qué orden, qué 'virtudes principales' se destacan, se graba con el curso demo o con datos reales, quién graba/edita/narra, en qué idioma, dónde se aloja (YouTube no listado, Drive) y cuál es la fecha interna de corte para congelar la UI antes de grabar?

- **Requisitos:** —
- **Área declarada:** 3.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** El video es entregable evaluado y exige UI congelada; el guion debe reflejar los requisitos priorizados.
- **Estudio de APIs:** No lo aborda.

### P646. ¿El curso define un formato para la declaración de uso de IA (plantilla en Canvas, secciones obligatorias, por integrante o por equipo) o lo define el equipo? ¿Se lleva desde ahora un registro por integrante de qué herramientas se usaron y para qué (módulos, prompts relevantes) para completarla sin reconstruirla de memoria?

- **Requisitos:** —
- **Área declarada:** 3.2
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Es entregable obligatorio de la final y se relaciona con la regla 'deben ser dueños de su código'.
- **Estudio de APIs:** §14 solo recuerda que está pedida.

### P647. El código se entrega 'por GitHub': ¿repositorio público o privado? Si es privado, ¿a qué usuarios GitHub del profesor y ayudantes hay que invitar y cuándo se piden? ¿Qué debe contener el repo al 6-oct: README con instrucciones de despliegue, .env.example, script de seed, diagrama de arquitectura, tag/release 'entrega-final'? ¿Cómo se garantiza que no hay secretos (.pem, client_secret, webhook secret) en el historial (pre-commit, escaneo)?

- **Requisitos:** —
- **Área declarada:** 3.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el paquete de entrega de código y los controles que el spec de proceso exige.
- **Estudio de APIs:** §14 advierte que un .pem commiteado es un hallazgo obvio en la corrección.

### P648. Durante las dos semanas post-entrega: ¿quién monitorea la disponibilidad (uptime check, alertas), quién puede redeployar si cae, se congela el código o se permiten hotfixes, y cómo se evita que expiren credenciales (refresh token Canvas del profesor demo, instalación de la App, API key de email)? ¿Se documenta un runbook y se ofrece a los revisores un canal de soporte?

- **Requisitos:** R2.3.10, R2.4.5, R2.6.1
- **Área declarada:** 3.2
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Una caída en la ventana de revisión anula funcionalidades ya cumplidas; el spec debe fijar responsables y procedimiento.
- **Estudio de APIs:** §1.1 explica que el refresh token permite jobs sin el profesor conectado; §12 recuerda la disponibilidad de dos semanas.

---

## 3.3

### P649. ¿Qué documentación interna se producirá para que TODOS puedan explicar TODO el 7-oct: documento de arquitectura, ADRs con decisiones (GitHub App vs PAT, SHA vs tag, polling vs webhook, precedencia de overrides, permisos push vs admin), guía por módulo, banco de preguntas probables con respuestas? ¿Quién la escribe y cuándo se revisa en grupo?

- **Requisitos:** —
- **Área declarada:** 3.3
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** El descuento de hasta 3 puntos es individual; el spec de proceso debe incluir estos artefactos como entregables internos con fecha.
- **Estudio de APIs:** §14 propone una tabla de 'preguntas probables' con respuestas breves y una lista de trampas a tener resueltas.

### P650. ¿Qué reglas de trabajo aseguran que cada integrante conozca módulos que no escribió: rotación de pares, revisión obligatoria de cada PR por otro integrante que debe poder explicarlo, walkthroughs semanales, simulacro de validación individual antes del 7-oct? ¿Se prohíbe mergear código generado por IA que su autor no pueda explicar?

- **Requisitos:** —
- **Área declarada:** 3.3
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** La regla '1.0 en el proyecto si no pueden explicar' es un riesgo de nota mayor que cualquier requisito individual.
- **Estudio de APIs:** §8.5 sugiere argumentos metodológicos para la defensa oral; no define proceso de equipo.

---

## 4

### P651. Dado que 'lo no accesible en el uso no se considera cumplido', ¿cómo se hace visible cada proceso automático en la revisión de la final: (a) informe diario: ¿página de informes históricos y botón 'enviar ahora' al revisor?; (b) snapshot al cierre: ¿entregas cerradas en el pasado más una que cierre durante la ventana de revisión?; (c) actualización de fechas: ¿el revisor cambia una fecha en Canvas y ve el cambio en la app?; (d) comunicaciones automáticas: ¿historial de envíos?; (e) ¿log de actividad del worker de repos?

- **Requisitos:** R2.3.10, R2.4.4, R2.4.5, R2.6.1, R2.6.4, R2.6.7
- **Área declarada:** 4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Cada respuesta se traduce en pantallas adicionales (historial, log, 'enviar ahora') y en fechas concretas del dataset demo.
- **Estudio de APIs:** §9.1 sugiere guardar cada informe como página web; §9.4 propone outbox con pantalla de historial de comunicaciones; §7.4 botón 'sincronizar ahora'.

### P652. Para que dashboards y timeline tengan contenido el 6-oct, ¿se generará actividad real en los repos demo durante las 3 semanas previas (commits desde cuentas de estudiante, en distintos días y horas, con al menos un repo inactivo y un integrante sin commits), o se importará historia sintética (backfill con commits fechados)? ¿Cuántos repos y commits se consideran suficientes y quién ejecuta ese calendario de actividad?

- **Requisitos:** R2.4.6, R2.5.1, R2.5.2, R2.5.3, R2.5.4, R2.5.7, R2.5.8, R2.5.10
- **Área declarada:** 4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define un plan de generación de datos con fechas y responsables; sin historia los requisitos 2.5 se ven vacíos ante el revisor.
- **Estudio de APIs:** §8.2 backfill completo al ingresar un repo; §8.5 lista métricas requeridas; no aborda cómo poblar datos de demo.

### P653. ¿Con qué fechas se configuran las entregas del curso demo para la final: al menos una entrega ya cerrada (snapshot capturado), una que cierre entre el 6 y el 20 de octubre (para que el revisor vea la captura automática y el aviso de proximidad) y tareas 'activas' durante toda la ventana para que exista informe diario? ¿Quién mantiene vivo ese dataset durante las dos semanas?

- **Requisitos:** R2.4.5, R2.5.6, R2.6.1, R2.6.7
- **Área declarada:** 4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.6.1 no emite informe si no hay tareas activas; sin fechas planificadas el revisor no verá informes ni snapshots nuevos.
- **Estudio de APIs:** §9.1 implementa literalmente 'sin tareas activas no hay informe'; §7.5 el job barre lo vencido y no capturado.

### P654. Los revisores que creen tareas en el sandbox generarán repos reales en la org del equipo. ¿Se permite eliminar tareas y sus repos desde la app (el enunciado no lo pide), se limpian manualmente, o se acepta la acumulación? ¿Cómo se comporta el sistema al recrear una tarea con el mismo nombre: reutiliza el repo existente o crea uno con sufijo?

- **Requisitos:** R2.3.7, R2.3.8
- **Área declarada:** 4
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Afecta el modelo de estados (repo existente encontrado vs creado), la política de nombres y la operación del sandbox.
- **Estudio de APIs:** §5.4 sanitización y sufijo -2 ante 422; §5.5 trata 422 'ya existe' como éxito idempotente.

### P655. ¿Se hará una prueba de carga realista antes del 6-oct (p. ej. 25–40 repos con 2–3 colaboradores y archivos base) para observar los límites secundarios de GitHub (80 requests generadoras de contenido/min, 900 puntos/min) y validar el throttle del worker? ¿Con qué org y quién limpia después?

- **Requisitos:** R2.3.7, R2.3.10
- **Área declarada:** 4
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** El dataset demo pequeño no revela los límites; si el profesor prueba con un curso grande en la ventana de revisión, el worker debe comportarse correctamente.
- **Estudio de APIs:** §2.4 calcula 40 puntos por grupo y recomienda throttle de 1 repo cada 3–5 s.

### P656. Dado que 'las funcionalidades a las que no se puede acceder en el uso no se consideran cumplidas', ¿la administración de usuarios profesor (R2.1.1: listar, desactivar, reactivar, eliminar) tendrá una UI accesible para los revisores, con qué credencial (cuenta admin de demo entregada junto al link) y qué salvaguardas para que un revisor no desactive al profesor demo cuyo token de Canvas sostiene los jobs? ¿O R2.1.1 se interpreta solo como registro/autoadministración del perfil y se documenta así en el spec?

- **Requisitos:** R2.1.1, R2.1.7
- **Área declarada:** 4 / 2.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define si existe pantalla de administración, sus credenciales de revisión y la interpretación oficial de R2.1.1 frente al criterio de la sección 4.
- **Opciones planteadas:**
  - UI de admin + credencial admin para revisores
  - UI de admin visible solo al equipo (no evaluable)
  - R2.1.1 = registro + perfil propio, sin admin
- **Estudio de APIs:** §3 y §11 marcan R2.1.1 como 'App / BD ✅' sin describir pantallas ni rol admin.

---

## transversal

### P657. ¿Cómo interpreta el equipo la restricción 'los estudiantes no serán usuarios de la aplicación: toda su interacción deberá realizarse a través de Canvas y GitHub'? (a) Prohíbe cualquier página web de la app visitada por un estudiante (incluido el magic link OAuth de §6.2 y una página 'tu versión registrada de la entrega 1'); (b) solo prohíbe que tengan cuenta/login, permitiendo páginas sin autenticación accedidas por enlace firmado enviado por Canvas; (c) se consultará al profesor del curso antes de implementar §6.2. ¿Qué se responderá el 7-oct si preguntan por qué un estudiante abrió una URL de la app?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.12
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Habilita o descarta de raíz la verificación de propiedad por OAuth de GitHub (§6.2), páginas de estado para estudiantes y enlaces de confirmación; afecta la estrategia de enrolamiento evaluada en usabilidad.
- **Opciones planteadas:**
  - Ninguna página para estudiantes
  - Páginas sin login vía enlace firmado
  - Consultar al profesor del curso
- **Estudio de APIs:** §6.2 propone un magic link firmado hacia OAuth de GitHub y afirma que 'formalmente sigue interactuando a través de Canvas y GitHub'; el equipo aún no ha validado esa interpretación.

### P658. ¿La UI será solo en español (Chile)? ¿Formato de fechas y hora (dd-mm-yyyy HH:mm) en zona America/Santiago con indicación explícita 'hora de Chile'? ¿Se usan los términos de Canvas en español ('Tarea', 'Sección', 'Conjunto de grupos') para alinear con lo que el profesor ve en Canvas?

- **Requisitos:** R2.1.6, R2.2.6, R2.3.11, R2.5.6
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el glosario del spec, evita confusión UTC/CLT en pantallas de fechas (Canvas entrega UTC) y afecta la evaluación de 'guía adecuada'.
- **Estudio de APIs:** §14 recomienda guardar UTC y convertir al renderizar; no fija idioma ni formato.

### P659. ¿Tendrá la página del curso un checklist de progreso ('Canvas vinculado, GitHub vinculado, estudiantes sincronizados, 7/10 usuarios GitHub mapeados, 1 tarea') con enlaces a la acción pendiente? ¿Habrá textos de ayuda contextual, una página 'Guía para el profesor' y/o un tour la primera vez? ¿Quién redacta esos textos y en qué fecha se revisan?

- **Requisitos:** R2.1.6, R2.2.5, R2.2.6
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Es el criterio explícito de la parcial ('guía adecuada'); el spec debe listar los textos de ayuda como entregables con responsable.
- **Estudio de APIs:** §4.4 sugiere mostrar 'datos de Canvas actualizados hace X min'; §3.3 checklist de verificación; no describe un onboarding global.

### P660. Considerando que Canvas entrega fechas en UTC y Chile está en horario de verano (UTC-3) desde el 6-sep-2026: ¿todas las fechas se muestran en America/Santiago con etiqueta explícita, y los jobs (informe diario, cierres) se programan en esa zona? ¿El dataset demo incluye una entrega con fecha cercana a medianoche para verificar la conversión ante el revisor?

- **Requisitos:** R2.4.1, R2.4.5, R2.6.1
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Un error de zona horaria en la demo (fecha distinta a la que muestra Canvas) es visible de inmediato para el profesor.
- **Estudio de APIs:** §14 'Zonas horarias': guardar UTC y convertir al renderizar; §9.1 cron 07:00 America/Santiago.

### P661. ¿Existe una ficha por estudiante que consolide, a través de todas las tareas del curso, su sección, grupo(s) con historial, mapeo GitHub (fuente y cambios), repos y estados, snapshots, commits atribuidos, comunicaciones enviadas y notas publicadas? Si existe: ¿desde dónde se accede (clic en el nombre en cualquier tabla), qué roles la ven, e incluye tareas archivadas? Si no existe, ¿cómo responde el equipo docente a '¿qué pasa con el estudiante X?' sin recorrer cada tarea?

- **Requisitos:** R2.2.1, R2.2.4, R2.5.4, R2.6.5, R2.7.7
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define una vista y ruta adicional en la navegación, sus permisos y los datos que deben ser consultables por estudiante.
- **Estudio de APIs:** No lo aborda (§12 describe vistas por curso, tarea y repositorio).

### P662. Para las acciones 'crear repo base', 'sincronizar ahora', 'reintentar todos los fallidos', 'reenviar invitación', 'publicar nota' y 'enviar anuncio': ¿qué garantía de idempotencia se exige (botón deshabilitado, token de idempotencia, cola con deduplicación) y cuál es el comportamiento visible si el usuario repite la acción o hace doble click (mensaje 'ya en curso', segunda ejecución ignorada, o duplicado aceptado)?

- **Requisitos:** R2.3.5, R2.3.10, R2.4.4, R2.6.5, R2.6.6, R2.7.6
- **Área declarada:** transversal (idempotencia UI)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Un anuncio o nota duplicados son visibles para estudiantes; la spec debe definir criterios de aceptación de idempotencia por acción.
- **Estudio de APIs:** §5.5 idempotencia del worker y §9.4 outbox con constraint único (kind, target, delivery_id). No cubre acciones disparadas desde la UI.

### P663. ¿Qué debe mostrar cada vista cuando no hay datos: curso sin estudiantes o sin secciones, group set sin grupos aún (self-signup abierto), tarea sin entregas vinculadas, tarea sin repos, repo sin commits, entrega cerrada con snapshot 'sin commits' (¿qué corrige el ayudante y qué nota se publica?), dashboard antes del primer sync? ¿La verificación de vinculación (R2.1.6) falla o solo advierte cuando el curso tiene 0 estudiantes?

- **Requisitos:** R2.1.6, R2.2.6, R2.3.11, R2.4.5, R2.5.1, R2.5.10, R2.7.4
- **Área declarada:** transversal (estados vacíos)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Los estados vacíos son los primeros que verá el corrector en la demo; cada uno necesita un texto y una acción sugerida definidos.
- **Estudio de APIs:** §3.3 chequeo 'vemos estudiantes: n > 0'; §7.5 status NO_COMMITS 'dato valioso para el informe'. No define la UI de estados vacíos.

### P664. ¿Qué eventos deben quedar en un registro de auditoría visible en la app (quién, cuándo, qué, valor anterior → nuevo): cambios de vinculación, mapeos manuales y su fuente, reintentos, cambios de fecha detectados en Canvas, snapshots automáticos y manuales, asignaciones de corrector, notas publicadas, mensajes y anuncios enviados, altas/bajas de ayudantes y cambios de permisos? ¿Quién puede verlo, por cuánto tiempo se conserva y se exporta?

- **Requisitos:** R2.1.9, R2.2.5, R2.4.4, R2.4.5, R2.6.5, R2.7.6
- **Área declarada:** transversal (auditoría)
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin auditoría no se puede explicar en la validación del 7-oct 'por qué este repo tiene este estado'; define una entidad y una vista adicionales.
- **Estudio de APIs:** §7.4 'log de auditoría: quién/cuándo/de qué a qué' para fechas; §9.1 registro de envíos; §9.4 historial de comunicaciones. Cobertura parcial, sin definir alcance ni visibilidad.

### P665. Además del 422 'name already exists' para repos, ¿qué clave de idempotencia se define para cada efecto externo: mensaje/comentario al estudiante (unique (kind, target, delivery)), anuncio por cambio de fecha (¿uno por cambio o por día?), publicación de nota (re-PUT sobreescribe en Canvas: ¿permitido? ¿se registra quién/cuándo?), creación de tag (422 → verificar SHA; ¿qué hacer si el tag existe con OTRO SHA?), y procesamiento de webhooks (guardar X-GitHub-Delivery para descartar duplicados)?

- **Requisitos:** R2.3.7, R2.3.12, R2.6.5, R2.6.6, R2.7.6, R2.4.5, R2.5.2
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Un reinicio del worker sin idempotencia envía el mismo mensaje varias veces a estudiantes reales y duplica notas o anuncios; el caso 'tag con otro SHA' decide qué es la fuente de verdad (R2.4.7).
- **Estudio de APIs:** §5.5 (422 como éxito), §7.5 (tag existente → verificar SHA), §9.4 (outbox con constraint único). No cubre notas ni webhooks duplicados.

### P666. ¿Cuál es la política uniforme de reintentos por tipo de fallo: 5xx/timeouts (backoff exponencial, ¿máximo de intentos y tope de espera?), 403/429 rate limit (respetar retry-after / x-ratelimit-reset), 401 token inválido (no reintentar, marcar credencial rota), 404 recurso eliminado (no reintentar, marcar), 422 validación (no reintentar, mostrar error)? ¿Tras N fallos el ítem pasa a ERROR y exige 'reintentar' manual, o se reintenta indefinidamente con espera creciente?

- **Requisitos:** R2.3.11, R2.4.4, R2.6.4
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el comportamiento observable en la tabla de estados (R2.3.11) y en el informe diario, y evita tormentas de reintentos que agotan rate limits.
- **Estudio de APIs:** §2.4 ghRequest con 5 intentos y backoff; §1.5 backoff ante 403/429; no distingue 401/404/422.

### P667. ¿Se fija concurrencia 1 por token de Canvas (cola secuencial por curso) como propone el estudio? ¿Cómo se coordina cuando el mismo token del profesor lo usan a la vez la UI ('sincronizar ahora', checklist de verificación), el cron de sync y el envío masivo de Conversations? ¿El botón 'sincronizar ahora' tiene cooldown/debounce? ¿Se muestran X-Rate-Limit-Remaining y X-Request-Cost en un panel de diagnóstico?

- **Requisitos:** R2.2.1, R2.4.4, R2.6.5, R2.1.6
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Canvas devuelve 403 Rate Limit Exceeded por token; un profesor que hace clic repetido puede bloquear los jobs de su propio curso durante la demo.
- **Estudio de APIs:** §1.5 recomienda 'secuencial por curso (concurrencia 1 por token)'; §7.4 sugiere botón 'sincronizar ahora'.

### P668. ¿Cuál es el throttle concreto del creador de repos (p.ej. 1 repo cada 3–5 s) y para qué tamaño máximo de curso se dimensiona y se prueba (¿60 estudiantes? ¿300?)? ¿Se usa el plugin de throttling de Octokit o uno propio? ¿Qué muestra la UI mientras la cola avanza (contador, ETA)? ¿Se documenta el tamaño máximo soportado como requisito no funcional?

- **Requisitos:** R2.3.7, R2.3.10, R2.3.9
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** GitHub limita a 80 requests generadoras de contenido/min y 900 puntos/min; crear repo + colaboradores + archivos suma ~40 puntos por grupo. Sin throttle se reciben 403 secundarios a mitad de la demo.
- **Estudio de APIs:** §2.4 límites secundarios; §5.5 'máximo ~1 repo cada 3 s'.

### P669. Verificar contra la API real que un GET /repos/{o}/{r}/commits con If-None-Match que devuelve 304 efectivamente no descuenta del rate limit primario del installation token, y medir el costo real de un ciclo de reconciliación con N repos. ¿Cada cuántos minutos se reconcilia y con qué tope de repos por ciclo?

- **Requisitos:** R2.5.2, R2.5.3
- **Área declarada:** transversal
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** El estudio basa la viabilidad del polling de 60+ repos en este comportamiento; si no se cumple, hay que reducir frecuencia o depender más de webhooks.
- **Estudio de APIs:** §2.4 'truco que vale oro': 304 no descuenta; §8.2 reconciliador cada 15 min con ETag.

### P670. ¿Se implementa un iterador genérico de paginación que siga el header Link opaco (Canvas y GitHub) con tests y un límite de seguridad de páginas para evitar loops infinitos, o se usan octokit.paginate y una librería para Canvas? En la UI, ¿tablas paginadas/virtualizadas para cursos grandes (200+ estudiantes) o se asume <100 filas y se listan completas?

- **Requisitos:** R2.2.1, R2.2.3, R2.5.2, R2.3.11
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El default de Canvas es 10 ítems: sin paginación se 'pierden' estudiantes silenciosamente. Las tablas de estado y dashboard deben seguir siendo usables con muchos repos.
- **Estudio de APIs:** §1.4 paginación Canvas (per_page=100, Link opaco); §2.5 paginación GitHub.

### P671. ¿Qué timeouts se fijan: cliente HTTP hacia Canvas/GitHub (p.ej. 30 s), duración máxima de un job, y request web (los PaaS cortan a ~30 s)? ¿El checklist de verificación de R2.1.6 (8 chequeos, incluye crear y borrar un repo temporal) se ejecuta dentro de la request o de forma asíncrona con polling/SSE desde la UI y resultados parciales?

- **Requisitos:** R2.1.6, R2.5.1, R2.3.6
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un checklist síncrono puede superar el timeout del PaaS y mostrar error genérico justo en la pantalla que se evalúa como 'guía adecuada' el 16-sep.
- **Estudio de APIs:** §1.4 snippet con timeout=30; §3.3 checklist con botón 'reintentar' (sin decir si es síncrono).

### P672. ¿Servidor, BD y APIs en UTC (timestamptz) y la UI muestra siempre en America/Santiago (fija) o según el navegador del usuario? ¿El informe de las '07:00 America/Santiago' se programa con scheduler consciente de zona horaria o como hora UTC fija (se desfasa con el cambio de hora chileno: primer sábado de septiembre y de abril)? ¿Cómo se muestran fechas 'all_day' de Canvas y el caso due_at=null ('sin fecha')?

- **Requisitos:** R2.4.1, R2.4.5, R2.5.6, R2.6.1
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Un snapshot capturado con 3 h de error es un bug grave e invisible; la demo parcial cae el 16-sep, días después del cambio de hora en Chile.
- **Estudio de APIs:** §14 'Zonas horarias' (UTC, timestamptz, convertir al renderizar); §9.1 'CRON diario 07:00 America/Santiago'; §7.3 due_at null.

### P673. ¿La UI, mensajes de error, emails y mensajes a estudiantes por Canvas van 100% en español? ¿Se instala infraestructura de i18n (archivos de traducción) o se hardcodea español? ¿Formato de fecha/hora (DD-MM-YYYY HH:mm, 24 h), separador decimal (coma) y nombres de estados/roles definidos en un glosario único?

- **Requisitos:** R2.1.6, R2.3.12, R2.6.4, Sección 3.1 (usabilidad)
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** La usabilidad se evalúa en la parcial; textos mixtos inglés/español y formatos de fecha ambiguos restan claridad. Define si hay una capa técnica adicional que mantener.
- **Estudio de APIs:** No lo aborda (los ejemplos están en español).

### P674. ¿Se fija un nivel objetivo de accesibilidad (WCAG 2.1 AA) o solo mínimos: estados no comunicados solo por color (🟢🟡🔴 + texto), navegación por teclado en la corrección (R2.7.3), labels en formularios, contraste, foco visible? ¿Se audita con Lighthouse/axe antes de cada entrega?

- **Requisitos:** R2.3.11, R2.7.3, R2.5.5
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** La tabla de estados propuesta usa semáforos de color; sin texto alternativo es inaccesible y ambigua en proyector. Define criterios de aceptación de UI.
- **Estudio de APIs:** §5.6 propone iconos de color; §10.1 atajos de teclado.

### P675. ¿Dispositivos objetivo: solo desktop (demo presencial en proyector, 1366×768 / 1920×1080) o también tablet/móvil para ayudantes? ¿Las tablas anchas (estado de repos, dashboard) tienen scroll horizontal propio o rediseño móvil? ¿Se prueba en el proyector/resolución del aula antes del 16-sep?

- **Requisitos:** R2.5.1, R2.3.11, R2.7.2
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el alcance del CSS responsive y los criterios de aceptación visual; un dashboard que no cabe en el proyector arruina la demo.
- **Estudio de APIs:** No lo aborda.

### P676. Si el refresh token del profesor deja de funcionar (revocó la app en Canvas, replace_tokens, Developer Key deshabilitada, profesor retirado del curso) todos los jobs del curso fallan de madrugada. ¿Cómo se detecta (401 en refresh), se pausa el curso para evitar tormenta de reintentos, y se avisa (banner en UI, email al profesor, entrada en el informe)? ¿Cómo se evita que dos jobs refresquen el mismo token simultáneamente (lock / single-flight)? ¿Qué pasa si el único profesor con token válido se retira y quedan otros profesores sin haber autorizado Canvas?

- **Requisitos:** R2.4.4, R2.4.5, R2.6.1, R2.3.12
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la opción A/B del estudio (token del profesor vs de cada usuario) en términos operativos, y el estado 'credenciales rotas' que la UI debe mostrar.
- **Estudio de APIs:** §1.1 subraya la criticidad del refresh token; §3.4 opciones A (token del profesor) y B (token por usuario). No cubre revocación ni concurrencia.

### P677. ¿Sesión con cookie HttpOnly/Secure/SameSite firmada respaldada en servidor (BD/Redis) o stateless (JWT)? ¿Duración (8 h, 7 días, 'recordarme'), expiración por inactividad y cierre de sesión global? ¿Al retirar a un ayudante (R2.1.9) o cambiar sus permisos, su sesión activa se invalida de inmediato (exige verificar el rol en cada request)? ¿Protección CSRF: token por formulario del framework + SameSite, y parámetro state validado en los tres flujos OAuth (Google, Canvas, GitHub setup), guardado en un almacén que sobreviva reinicios de la instancia?

- **Requisitos:** R2.1.1, R2.1.2, R2.1.8, R2.1.9
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define criterios de aceptación de seguridad verificables y el comportamiento observable al retirar a un ayudante; un state en memoria se pierde con el sleep/reinicio del PaaS y rompe el login.
- **Estudio de APIs:** §1.1 'state es obligatorio en la práctica'; no cubre sesiones ni CSRF de la app.

### P678. ¿La autorización se verifica en el servidor en cada endpoint contra la membresía y permisos del usuario en ESE curso (no solo ocultando botones)? ¿Los IDs en URL son secuenciales (permiten enumerar cursos ajenos) o UUID/slug? ¿Un ayudante puede ver repos, estudiantes o notas de entregas que no tiene asignadas? ¿Se escriben tests automatizados de autorización (usuario A no accede a recursos del curso B; ayudante no ejecuta acciones de profesor por URL directa)?

- **Requisitos:** R2.1.7, R2.1.8, R2.7.2, R2.7.6
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El enunciado exige ≥3 permisos administrables; sin enforcement server-side y sin tests, el RBAC es cosmético y un IDOR expone datos de estudiantes de otros cursos.
- **Estudio de APIs:** §3.4 tabla de permisos propuesta (no aprobada); no trata enforcement ni IDOR.

### P679. ¿Qué datos personales de estudiantes se persisten (nombre, correo, sis_user_id, canvas_user_id, login de GitHub, avatar) y cuáles se evitan explícitamente? ¿Los ayudantes ven correos/sis_id? ¿El informe diario por email incluye nombres de estudiantes 'sin participación' (viajan por un proveedor SMTP de terceros)? ¿Política de retención y borrado al eliminar un curso, al concluir el semestre y al terminar las 2 semanas de disponibilidad? ¿Se incluye una nota de privacidad en la app y se evita PII en logs?

- **Requisitos:** R2.2.1, R2.5.4, R2.6.1, R2.6.4
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** La app concentra datos académicos de menores de edad potenciales en infraestructura gratuita de terceros; el spec debe fijar qué se guarda, quién lo ve y cuándo se borra.
- **Estudio de APIs:** §5.4 nombres de repo 'que no filtren datos sensibles'; §4.4 'nunca borren filas, marquen deleted_at'.

### P680. ¿Se activan cabeceras de seguridad (HSTS, X-Content-Type-Options, CSP básica, frame-ancestors) y se sanitiza el HTML proveniente de Canvas (descripciones de tareas, bodies de submissions, nombres) antes de renderizarlo en la app (XSS almacenado)? ¿Dependabot/npm audit/pip-audit en CI con política de actualización? ¿Rate limiting en endpoints públicos (webhook, unsubscribe, callbacks OAuth)?

- **Requisitos:** R2.3.1, R2.2.4, R2.6.3, R2.5.2
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Los bodies de submissions son texto controlado por estudiantes que la app muestra a docentes: es el vector de XSS más directo del sistema.
- **Estudio de APIs:** §6.1 limpia tags del body solo para parsear el login; no trata XSS ni cabeceras.

### P681. ¿El link de 'darse de baja' del email usa token firmado (HMAC/JWT) con expiración y de un solo uso, o permanente? ¿Baja inmediata al hacer clic (los escáneres de correo siguen links y producirían bajas involuntarias) o página de confirmación? ¿El mismo mecanismo permite volver a suscribirse sin login?

- **Requisitos:** R2.6.3, R2.6.4
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.6.3 exige suscripción/baja individual; el diseño del token define seguridad y criterios de aceptación del email.
- **Estudio de APIs:** §9.1 'link de darse de baja en el pie del email (con token firmado, sin login)'.

### P682. ¿Para qué escala se diseña y se prueba: N cursos simultáneos, estudiantes por curso, repos por tarea, commits por repo (p.ej. 3 cursos × 100 estudiantes × 3 tareas = 900 repos)? ¿Objetivo de tiempo de carga del dashboard (p.ej. <1 s p95 leyendo solo de BD) y de latencia 'push en GitHub → visible en dashboard' (segundos con webhook; ≤15 min con polling)? ¿Se ejecuta una prueba de carga sintética antes de la final?

- **Requisitos:** R2.5.1, R2.3.10, R2.5.2
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Convierte 'inmediato' (R2.5.1) y 'reciente' (R2.5.3) en números verificables y dimensiona rate limits, cola y BD gratuita.
- **Estudio de APIs:** §2.1 ejemplo con 60 estudiantes/60 repos; §8.3 'milisegundos' para el dashboard.

### P683. Ante errores sostenidos de Canvas o GitHub (caída, 401 por token revocado, 404 por curso concluido o tarea eliminada en Canvas, GitHub App desinstalada de la org), ¿se pausan los jobs del curso (circuit breaker) para no acumular reintentos ni consumir rate limit? ¿Cómo se muestra en la UI ('Canvas no responde desde hace 20 min', 'la App fue desinstalada: reinstalar') y a quién se notifica? ¿Se reanuda automáticamente al recuperarse o requiere acción del profesor?

- **Requisitos:** R2.3.11, R2.4.4, R2.5.5, R2.1.6
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define estados de salud por curso que la UI y el informe diario deben exponer, y evita que un curso roto degrade a los demás.
- **Estudio de APIs:** §5.5 estado ERROR por sujeto; §1.5 backoff; no cubre fallos prolongados ni desinstalación de la App.

### P684. Es muy probable que el profesor y los ayudantes evalúen las apps de VARIOS equipos del curso contra el MISMO curso de Canvas y la MISMA organización de GitHub (instalando varias GitHub Apps y vinculando el mismo curso en cada app). ¿Cómo garantiza la app que coexiste sin interferir con las demás: prefijo/namespace de repos único y configurable, topic o marcador propio para reconocer 'sus' repos y no adoptar por 422 repos creados por otra app, nombre único de la tarea de registro de usuarios GitHub (para no leer las entregas de la tarea de otro equipo), ignorar webhooks de repos que no están en su BD, no eliminar ni modificar nada que no haya creado, y no duplicar mensajes/anuncios a los mismos estudiantes? ¿Se ofrece una acción 'eliminar todo lo que esta app creó en esta org/curso' para dejar limpio el entorno del profesor?

- **Requisitos:** R2.1.4, R2.1.5, R2.2.5, R2.3.7, R2.3.8, R2.3.12, R2.6.6
- **Área declarada:** transversal / 3.1
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Sin reglas de aislamiento, dos apps pueden pisarse repos, robar mapeos o mandar mensajes duplicados durante la evaluación, y el fallo se atribuiría a la app del equipo.
- **Opciones planteadas:**
  - Prefijo único por instancia de la app + topic/marcador en cada repo; adoptar por 422 solo repos marcados
  - Namespace configurable por curso con vista previa
  - Acción 'limpiar lo creado por esta app' (repos, tarea de registro, anuncios) con confirmación
  - Ignorar eventos de repos ajenos y registrarlos en log
- **Estudio de APIs:** §5.4 propone sufijo -2 ante 422 y §5.5 adopta el 422 'name already exists' como éxito; §6.1 crea una tarea llamada 'Registro de usuario GitHub'; no aborda coexistencia con otras apps en la misma org o curso.

### P685. ¿Cuál es la lista cerrada de NO-objetivos que el spec declara explícitamente para que el evaluador no los espere y el equipo pueda responder '(fuera de alcance por diseño)' el 7-oct? Candidatos: autograding/ejecución de tests sobre el snapshot; detección de similitud/plagio entre repos; comentarios de código línea a línea dentro de la app; cualquier UI para estudiantes; crear/editar secciones, grupos o inscripciones en Canvas; editar rúbricas; entregas sin tarea de Canvas asociada; estudiantes no provenientes de Canvas (oyentes); GitHub Enterprise Server; notificaciones por Slack/WhatsApp; importar desde GitHub Classroom.

- **Requisitos:** R2.5.9, R2.7.4, R2.2.1, R2.3.1, R2.3.2
- **Área declarada:** transversal / proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Sin no-objetivos explícitos, la 'revisión usando la herramienta' puede penalizar ausencias que el equipo consideraba obvias.
- **Opciones planteadas:**
  - Sección 'Fuera de alcance' en el spec y en la guía para el revisor
  - Sin declaración formal
- **Estudio de APIs:** §12 describe la arquitectura mínima; no enumera no-objetivos.

### P686. Los estudiantes no usan la app pero su actividad en GitHub será monitoreada y sus datos de Canvas almacenados. ¿Se les informa (anuncio inicial en Canvas o texto en la tarea de registro) qué datos se recopilan, para qué y quién los ve, y se necesita el visto bueno del profesor/universidad para ello? Además, GET /enrollments devuelve el objeto grades (current_score/final_score) del estudiante: ¿la app lo descarta explícitamente antes de persistir, junto con otros campos no necesarios (login_id, sis_user_id) que llegan en las respuestas?

- **Requisitos:** R2.2.1, R2.5.2, R2.5.4, R2.6.5
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Un profesor puede preguntar por consentimiento y minimización de datos; el spec debe fijar qué se guarda y qué se comunica a los estudiantes.
- **Opciones planteadas:**
  - Anuncio informativo al vincular/crear primera tarea
  - Texto en la tarea de registro
  - Nada
  - Lista blanca de campos persistidos con descarte explícito de grades
- **Estudio de APIs:** §4.1 muestra que /enrollments trae grades; §14 y §3.1 no mencionan aviso a estudiantes ni minimización de campos.

### P687. ¿Cuál es el árbol exacto de navegación y URLs de la app? Propuesta a confirmar o corregir: Home = 'Mis cursos' → Curso (pestañas: Resumen / Estudiantes / Tareas / Equipo docente / Configuración) → Tarea (pestañas: Resumen / Entregas / Repositorios / Dashboard / Corrección / Comunicaciones / Configuración) → Repositorio (Timeline). ¿Hay breadcrumbs en todas las vistas y se preserva el contexto (pestaña activa, filtros) al volver atrás?

- **Requisitos:** R2.1.3, R2.3.11, R2.5.1, R2.7.2
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el mapa de pantallas del spec, las rutas, y qué vista es la 'puerta de entrada' de cada requisito (p.ej., dónde vive la tabla de estado de repos R2.3.11 vs el dashboard R2.5.1). Sin esto cada integrante inventa su propia jerarquía.
- **Opciones planteadas:**
  - Árbol curso→tarea→repo con pestañas
  - Sidebar global con secciones por curso
  - Vista única por tarea con paneles colapsables
- **Estudio de APIs:** §12 lista las vistas que leen de BD y §5.6/§10.1 describen tablas concretas, pero no propone jerarquía de navegación.

### P688. ¿El spec incluirá un catálogo cerrado de errores esperables con, para cada uno, el texto mostrado al usuario, la acción sugerida y quién puede resolverlo? Casos mínimos a decidir: token de Canvas expirado/revocado; scopes insuficientes; 403/429 por rate limit; GitHub App desinstalada; usuario GitHub inexistente; login corresponde a una Organization; repo ya existe; invitación de colaborador expirada; límite del plan de la org; tarea de Canvas eliminada; estudiante sin grupo en tarea grupal. ¿Se muestra el detalle técnico (código HTTP, mensaje de la API, id de request) en un desplegable 'Detalles técnicos'?

- **Requisitos:** R2.1.6, R2.2.6, R2.3.11
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Los mensajes orientados a acción son el corazón de 'guía adecuada'. Un catálogo permite escribir criterios de aceptación por error y evitar mensajes crudos de la API.
- **Estudio de APIs:** §5.6 muestra ejemplos ('🔴 Error: usuario inválido' con acción 'Corregir'); §2.4 detalla el manejo de 403/429; no hay catálogo unificado.

### P689. Indicador 'última sincronización': ¿con qué granularidad (por curso, por tarea, por fuente Canvas vs GitHub, por repositorio)? ¿Dónde se ubica (cabecera del curso, pie de cada tabla, tooltip del dato)? ¿Formato relativo ('hace 4 min') con tooltip absoluto en hora local? ¿Qué se muestra si nunca se sincronizó, o si la última ejecución falló (fecha del último éxito + aviso 'la sincronización de las 10:30 falló')?

- **Requisitos:** R2.2.1, R2.4.4, R2.5.2
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Es el indicador que da confianza en datos que pueden tener hasta 10–15 min de antigüedad; el spec debe fijar ubicación, formato y estados (nunca / ok / fallida / en curso).
- **Estudio de APIs:** §4.4: 'Registren last_synced_at y muéstrenlo en la UI (datos de Canvas actualizados hace 4 min)'; §7.4 vuelve a recomendarlo. No define granularidad ni estados de fallo.

### P690. ¿Existe un botón 'Sincronizar ahora'? Si sí: ¿para qué fuentes (roster Canvas, fechas Canvas, entregas de usuario GitHub, commits GitHub, disparar aprovisionamiento)? ¿Uno por fuente o uno global? ¿Quién puede pulsarlo (permiso)? ¿Se deshabilita mientras corre y tiene cooldown para respetar el throttling de Canvas? ¿Qué feedback da al terminar ('2 estudiantes nuevos, 1 fecha cambiada, 0 errores')? ¿Cómo se documenta que es complementario y que la creación de repos sigue siendo automática (R2.3.10)?

- **Requisitos:** R2.3.10, R2.4.4, R2.2.1
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Afecta la demo (evitar esperas de 2–10 min), la percepción de datos frescos y la coherencia con el requisito de automatismo sin interacción.
- **Opciones planteadas:**
  - Sin botón (solo automático)
  - Botón global por curso
  - Botones por fuente con cooldown
- **Estudio de APIs:** §7.4 recomienda ofrecer 'sincronizar ahora' para la demo; §1.5 exige concurrencia 1 por token de Canvas; §5.5 dice que 'no sirve un botón crear repos' como mecanismo principal.

### P691. ¿La app muestra un registro visible de cambios detectados en cada sincronización (nuevo estudiante, estudiante retirado, cambio de sección, cambio de integrantes de grupo, cambio de fecha con valor anterior→nuevo, tarea de Canvas eliminada)? ¿Dónde (pestaña 'Actividad' del curso, panel en la tarea)? ¿Con qué retención y con filtros por tipo?

- **Requisitos:** R2.2.1, R2.2.3, R2.4.4
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Permite al docente entender por qué algo cambió sin ir a Canvas; define una tabla de auditoría de sync y su UI.
- **Estudio de APIs:** §7.4 propone 'registrar en un log de auditoría: quién/cuándo/de qué a qué' para fechas; no lo generaliza al roster ni define UI.

### P692. ¿Qué acciones requieren confirmación explícita y con qué fuerza (modal simple / escribir el nombre / doble confirmación)? Lista a decidir: eliminar curso; desvincular Canvas o GitHub; eliminar tarea (¿y sus repos en GitHub: se borran, se archivan, se dejan intactos?); retirar ayudante con correcciones pendientes; cambiar el usuario GitHub de un estudiante que ya tiene repo con commits; reenviar invitación; publicar nota en Canvas cuando ya existe una; enviar anuncio o mensaje masivo (mostrar N destinatarios); 'reintentar todos los fallidos'. ¿Existe 'deshacer' para alguna y se registra quién ejecutó cada acción?

- **Requisitos:** R2.1.3, R2.1.9, R2.2.5, R2.6.5, R2.6.6, R2.7.6
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Cada acción destructiva necesita un flujo de UI definido y una regla de negocio sobre efectos en sistemas externos (GitHub/Canvas) que no se pueden revertir desde la app.
- **Estudio de APIs:** §3.4 indica efectos al retirar ayudante (reasignar entregas, revocar acceso a la org); el resto no lo aborda.

### P693. ¿Qué forma toma la ayuda embebida: tooltips en términos técnicos (installation, override, SHA, repositorio plantilla), panel lateral '¿Cómo funciona esta pantalla?', página de ayuda/FAQ dentro de la app, o los tres? Para lo que la app NO hace (crear group set, asignar integrantes, configurar overrides, crear rúbrica, crear org), ¿se muestra el mensaje 'esto se configura en Canvas/GitHub' con enlace profundo a la pantalla exacta y un botón 'ya lo hice, sincronizar'? ¿Quién redacta y dónde se versionan esos textos?

- **Requisitos:** R2.1.6, R2.2.3, R2.2.6, R2.7.5
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El enunciado exige guiar al equipo docente en procesos que requieren información de ambas plataformas; la ayuda embebida es la forma de cumplirlo sin salir del flujo.
- **Estudio de APIs:** §4.3 identifica unassigned=true para detectar estudiantes sin grupo; §14 lista prerrequisitos externos; no propone mecanismo de ayuda en UI.

### P694. ¿Idioma y tono de la interfaz: español de Chile únicamente, o bilingüe? ¿Tuteo ('Vincula tu curso'), formal ('Vincule su curso') o impersonal ('Vincular curso')? ¿Se usa la misma persona y tono en los mensajes automáticos que la app envía a estudiantes por Canvas, y en el informe por email? ¿Los términos que Canvas/GitHub muestran en inglés (p.ej., 'Assignment', 'Group Set', 'Organization') se dejan en inglés o se traducen?

- **Requisitos:** R2.1.6, R2.3.12, R2.6.5
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define una guía de redacción para todos los textos de UI, plantillas y correos, evitando mezclas de tono entre integrantes.
- **Estudio de APIs:** no lo aborda (los ejemplos de mensajes en §5.7 y §9.3 usan tuteo informal: 'Hola! Tu repositorio ya está creado').

### P695. ¿Cuál es el glosario oficial de la UI y su equivalencia con Canvas y GitHub? Pares a decidir: 'Tarea' (app) vs 'Entrega' (= assignment de Canvas) vs 'tarea de Canvas'; 'Grupo' vs 'conjunto de grupos/group set'; 'Sección'; 'Repositorio base' vs 'plantilla'; 'Organización'; 'Versión de entrega' vs 'snapshot' vs 'tag'; 'Corrección' vs 'Calificación' vs 'Revisión'; 'Ayudante' vs 'TA'; 'Corrector'. ¿Se muestra el término original entre paréntesis la primera vez o en tooltip?

- **Requisitos:** R2.3.1, R2.3.2, R2.2.3, R2.4.5, R2.7.1
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** La relación 1 tarea → N entregas (cada una una assignment de Canvas) es confusa; sin vocabulario fijo la UI, el spec y los mensajes al estudiante se contradicen.
- **Estudio de APIs:** §5.2 usa Assignment (app) → Delivery (Canvas assignment) → Repository → DeliverySnapshot como modelo, sin fijar términos de UI en español.

### P696. ¿Qué nivel mínimo de accesibilidad se compromete: contraste AA, foco visible, navegación completa por teclado en wizard y tablas, labels en todos los campos, y estados nunca comunicados solo por color (los ✅🟡🔴 propuestos necesitan texto/icono)? ¿Se aceptan emojis como indicadores de estado en producción o se usan iconos SVG + etiqueta textual? ¿Se verifica con Lighthouse/axe como criterio de aceptación?

- **Requisitos:** R2.3.11, R2.5.5, R2.7.7
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Convierte accesibilidad en criterios de aceptación concretos y evita indicadores de estado inconsistentes entre sistemas operativos y navegadores.
- **Estudio de APIs:** §5.6 y §8.6 usan emojis (✅ 🟡 🔴 📌 ⚠) como indicadores; no aborda accesibilidad.

### P697. ¿Qué dispositivos se soportan: desktop-first con degradación legible en tablet/móvil, o totalmente responsive? ¿Qué vistas deben funcionar bien en móvil (p.ej., ayudante revisando 'mis correcciones', profesor mirando alertas) y cuáles pueden declararse 'solo escritorio' (dashboard, tablas anchas con scroll horizontal)? ¿En qué resolución se probará la demo presencial (proyector)?

- **Requisitos:** R2.7.2, R2.5.1, R2.3.11
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define breakpoints y qué tablas necesitan versión de tarjetas; acota el esfuerzo de frontend antes del 16-sep.
- **Estudio de APIs:** no lo aborda.

### P698. ¿Se estandariza un componente 'Pendientes / Qué falta' reutilizado en curso y tarea, que liste en lenguaje de acción cada bloqueo con su CTA ('3 estudiantes sin usuario GitHub → Enviar recordatorio', '2 invitaciones sin aceptar → Reenviar', '1 grupo sin integrantes → Configurar en Canvas')? ¿Cuál es la lista cerrada de tipos de pendiente y su prioridad de orden?

- **Requisitos:** R2.2.6, R2.3.11, R2.5.5
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** R2.2.6 y R2.3.11 exigen mostrar 'claramente' lo que falta; un componente único con tipos definidos hace el requisito verificable y consistente.
- **Estudio de APIs:** §6.3 define el 'panel de faltantes' como unión de: sin login, grupos con integrante sin mapeo, estudiantes sin grupo (unassigned=true), invitaciones sin aceptar.

### P699. Sesiones: ¿duración, expiración por inactividad, opción 'recordarme', cookie de sesión de servidor vs JWT? ¿El cierre de sesión solo termina la sesión local o también revoca el token de Canvas (`DELETE /login/oauth2/token`), lo que rompería los jobs nocturnos que dependen del refresh_token del profesor?

- **Requisitos:** R2.1.2, R2.1.4
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Separar 'cerrar sesión en la app' de 'revocar credenciales de Canvas' evita que un logout rutinario detenga sync, snapshots e informes.
- **Estudio de APIs:** §1.1 documenta la revocación y advierte que el refresh_token almacenado es crítico para 2.6.1 y 2.4.5.

### P700. ¿Cómo se almacenan los secretos y tokens (refresh_token de Canvas, .pem de la GitHub App, webhook secret, client_secret de Google): cifrado en BD con qué clave y gestor, variables de entorno del despliegue? ¿Se ofrece al profesor un botón 'revocar / rotar credenciales del curso' y qué muestra la UI de la credencial (nunca el valor, sí fecha de autorización y usuario)?

- **Requisitos:** R2.1.4, R2.1.5
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define requisitos de seguridad verificables y una funcionalidad de administración de vinculación; el código se entrega por GitHub y un secreto commiteado es un hallazgo evidente.
- **Estudio de APIs:** §1.1 'guarden el refresh_token cifrado en BD'; §14 'Secretos: variables de entorno, no al repo'.

### P701. ¿Qué eventos de 2.1 se registran en un log de auditoría (registro de usuario, creación/edición/archivo de curso, vinculación/re-autorización/desvinculación de Canvas y GitHub, alta/baja/cambio de permisos de co-profesores y ayudantes)? ¿Quién puede consultarlo, con qué retención y es visible en la UI del curso?

- **Requisitos:** R2.1.1, R2.1.3, R2.1.4, R2.1.5, R2.1.7, R2.1.8, R2.1.9
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Permite responder 'quién cambió qué' en la validación oral y ante conflictos entre profesores; define una tabla y una vista.
- **Estudio de APIs:** §7.4 propone un log de auditoría solo para cambios de fecha ('quién/cuándo/de qué a qué').

### P702. ¿La zona horaria de visualización se configura por curso (p. ej. America/Santiago), se toma de Canvas (`time_zone` del curso) o del navegador del usuario? ¿Se muestra siempre la zona junto a fechas como 'vinculado el…', 'última sincronización hace…'?

- **Requisitos:** R2.1.3, R2.1.4
- **Área declarada:** transversal
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija una regla única para todas las fechas de la app (afecta 2.4 completo) y evita ambigüedad en la demo cuando el evaluador compara con Canvas.
- **Opciones planteadas:**
  - Por curso, configurable
  - Desde Canvas
  - Del navegador
- **Estudio de APIs:** §14 'guarden UTC y conviertan solo al renderizar' sin definir de dónde sale la zona horaria de renderizado.

### P703. El estudio recomienda 'nunca borrar filas, marcar deleted_at'. ¿Cómo se conjugan las claves únicas con el borrado lógico en cada caso: unique(curso, github_login) cuando el login perteneció a un estudiante retirado y ahora lo reclama otro; unique(curso, usuario) en membresías docentes cuando se retira y reincorpora a un ayudante; unique(curso, slug) de una tarea eliminada cuyo nombre se reutiliza; unique(github_repo_id) cuando un repo es adoptado por otra fila (R2.3.8/422)? Opciones: índices únicos parciales (WHERE deleted_at IS NULL), reactivar la fila existente en vez de crear otra, o sufijar el valor borrado.

- **Requisitos:** R2.2.1, R2.2.4, R2.3.8, R2.1.9, R2.3.1
- **Área declarada:** transversal (modelo de datos)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Sin una regla uniforme, el segundo alta de un mismo valor falla con error de constraint (bug invisible en demo) o crea duplicados que rompen la idempotencia del worker.
- **Opciones planteadas:**
  - Índices únicos parciales
  - Reactivar fila existente
  - Sufijar valores borrados
  - Borrado físico solo para ciertas tablas
- **Estudio de APIs:** §4.4 'Nunca borren filas al sincronizar: marquen deleted_at'; no aborda su interacción con claves únicas.

### P704. Si la BD se restaura a un respaldo anterior (o se reprocesan jobs tras un fallo a mitad), ¿qué garantiza el diseño respecto a efectos externos ya ocurridos que la BD 'olvidó': repos ya creados (la adopción por 422 ¿verifica que sea el repo correcto y no uno ajeno?), colaboradores ya invitados o aceptados, tags ya creados (422 → comparar SHA), mensajes/comentarios/anuncios ya enviados (el outbox también se pierde con la BD: ¿se reenvían duplicados a estudiantes?), notas ya publicadas (re-PUT sobrescribe)? ¿Se define y prueba un procedimiento de 'reconciliación post-restauración' (leer GitHub y Canvas antes de reanudar workers, o arrancar con comunicaciones salientes en pausa)?

- **Requisitos:** R2.3.7, R2.3.12, R2.4.5, R2.6.7, R2.7.6
- **Área declarada:** transversal (recuperación)
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Los efectos externos no son transaccionales con la BD; sin regla, una restauración puede bombardear a los estudiantes con mensajes repetidos o adoptar repos equivocados.
- **Opciones planteadas:**
  - Reconciliación post-restauración obligatoria
  - Arrancar con salientes en pausa
  - Aceptar duplicados
- **Estudio de APIs:** §5.5 trata 422 como éxito; §9.4 outbox con constraint único (que se pierde junto con la BD). No aborda restauración.

### P705. ¿El registro de auditoría es una tabla genérica (entity_type, entity_id, action, actor_id | 'system:job', before_json, after_json, occurred_at, correlation_id) o tablas de historial específicas por entidad (MappingHistory, DateChange, SnapshotVersion)? ¿Se escribe en la misma transacción que el cambio (garantía de consistencia) o de forma asíncrona (riesgo de perder eventos)? ¿Los cambios que detecta el sync sin actor humano (Canvas cambió una fecha) usan el mismo mecanismo que las acciones de usuario?

- **Requisitos:** R2.1.9, R2.2.5, R2.4.4, R2.4.5, R2.7.6
- **Área declarada:** transversal (auditoría)
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Decide cuántas tablas de historial existen, cómo se consultan desde la UI del curso y si la auditoría puede tener huecos ante fallos del worker.
- **Opciones planteadas:**
  - Tabla genérica transaccional
  - Historiales específicos por entidad
  - Genérica asíncrona vía outbox
- **Estudio de APIs:** §7.4 menciona 'un log de auditoría: quién/cuándo/de qué a qué' solo para fechas; no define su forma.

### P706. ¿Se fija la matriz de datos derivados y sus disparadores de recálculo? Ejemplos: cambio de roster → sujetos → filas Repository → fechas efectivas → estado deseado de colaboradores → alertas; cambio de mapeo → colaboradores deseados → atribución de commits → 'sin participación'; cambio de override → fechas efectivas → programación de snapshot → recordatorios; cambio de grupo → todo lo anterior más períodos. Para cada arista, ¿el recálculo es sincrónico en la misma transacción, un job encolado, o un recálculo completo periódico que tolera desfase? ¿Qué desfase máximo se acepta entre el cambio en Canvas y su efecto en cada derivado?

- **Requisitos:** R2.2.1, R2.2.3, R2.2.4, R2.4.4, R2.5.3, R2.5.4
- **Área declarada:** transversal (datos derivados)
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin la matriz, cada worker recalcula lo que cree necesario y aparecen inconsistencias (repo listo con fecha vieja, alerta sobre un retirado); define además los criterios de latencia medibles.
- **Opciones planteadas:**
  - Recálculo sincrónico en la transacción del sync
  - Jobs encolados por tipo de cambio
  - Recálculo completo periódico
- **Estudio de APIs:** No lo aborda; cada sección del estudio describe su worker de forma aislada.

---

## infraestructura

### P707. ¿Contra qué instancia de Canvas se desarrolla y se demuestra? (a) instancia institucional de la universidad con un curso del ramo; (b) Free-for-Teacher (canvas.instructure.com) con curso de prueba creado por el equipo; (c) Canvas open-source autoalojado (Docker). ¿Quién gestiona el acceso y para qué fecha debe estar decidido?

- **Requisitos:** R2.1.4, R2.1.6, R2.2.1, R2.2.2, R2.2.3
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Cambia la URL base, la disponibilidad de Developer Key, la capacidad de crear secciones/grupos/estudiantes ficticios y si el profesor puede verificar los efectos desde su lado.
- **Opciones planteadas:**
  - Institucional (requiere admin de la instancia)
  - Free-for-Teacher
  - Self-hosted Docker
  - FFT para la parcial + institucional para la final
- **Estudio de APIs:** §1.2 recomienda Free-for-Teacher como plan B y afirma que ahí 'son admin de su propia cuenta y pueden crear la Developer Key'.

### P708. ¿Es efectivo que en Free-for-Teacher un usuario puede crear Developer Keys (client_id/secret OAuth2) para su propia cuenta? Debe probarse entrando a canvas.instructure.com y buscando Admin → Developer Keys. Si NO es posible, ¿cuál es el mecanismo de autenticación Canvas para la demo (token manual del profesor de prueba) y cómo se compatibiliza con la política de Canvas que prohíbe pedir tokens manuales a otros usuarios?

- **Requisitos:** R2.1.4, R2.1.6
- **Área declarada:** infraestructura
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Si la afirmación del estudio es falsa, el flujo OAuth2 no podrá demostrarse en la parcial y el spec debe contemplar el modo 'token manual' como camino oficial o exigir Developer Key institucional.
- **Estudio de APIs:** §1.2 afirma que en FFT pueden crear la Developer Key; la misma sección cita que pedir tokens manuales a otros usuarios viola la API Policy de Canvas.

### P709. Si se usa la instancia institucional: ¿quién solicita la Developer Key (¿el profesor del ramo ante el administrador de Canvas?), con qué redirect_uri exacta (debe ser la URL pública definitiva), con qué scopes, en qué plazo se espera respuesta y cuál es la fecha límite para abandonar este camino y pasar al plan B?

- **Requisitos:** R2.1.4, R2.1.6
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Fija una dependencia crítica con fecha de corte; la redirect_uri obliga a tener la URL de deploy definida antes de solicitar la key.
- **Estudio de APIs:** §1.1 describe el flujo con Developer Key creada por el admin de la instancia; §1.3 lista los scopes necesarios; §13 hito 2 la marca 'Depende de terceros, Día 1'.

### P710. ¿Qué organización GitHub se usa para la demo y la revisión: una org nueva del equipo (plan Free), la org del curso administrada por el profesor, o ambas? ¿Quiénes son owners? ¿Es la misma org donde vive el código fuente del proyecto o una separada para no mezclar repos generados de estudiantes con el código entregable?

- **Requisitos:** R2.1.5, R2.3.7
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** La instalación de la GitHub App exige ser owner de la org; mezclar código fuente y repos generados complica la entrega 'todo el código por GitHub' y la limpieza del sandbox.
- **Estudio de APIs:** §3.3 describe la instalación de la App en la org; §14 recomienda repos privados y revisar límites del plan Free.

### P711. ¿Bajo qué cuenta se registra la GitHub App (personal de un integrante vs la organización del equipo), quién custodia la clave .pem y el webhook secret, y se marca la App como pública para que el profesor pueda instalarla en SU propia organización si quiere probar con ella? ¿Qué pasa si el integrante dueño pierde acceso a su cuenta?

- **Requisitos:** R2.1.5, R2.1.6
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define custodia de secretos, continuidad del servicio y si el flujo 'Conectar organización' funciona con orgs ajenas al equipo durante la revisión.
- **Estudio de APIs:** §2.2 describe JWT firmado con la .pem; §3.3 propone redirigir a github.com/apps/<app>/installations/new; §14 exige que la .pem no vaya al repositorio.

### P712. ¿Se hará antes del 10-sep una prueba end-to-end con la GitHub App instalada en la org: crear repo (POST /orgs/{org}/repos), generar desde template (/generate), agregar colaborador externo (PUT collaborators) y confirmar los códigos 201/204? ¿Quién la ejecuta y dónde se registra el resultado (lista definitiva de permisos de la App)?

- **Requisitos:** R2.3.5, R2.3.7, R2.3.9
- **Área declarada:** infraestructura
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un 403 descubierto el 15-sep bloquea el corazón de la demo; el resultado fija en el spec los permisos exactos que la App solicita.
- **Estudio de APIs:** §2.3 y Apéndice A.1/A.2 marcan como ambiguos los permisos para crear repos en org y para /generate; §13 hito 3 lo ubica en Día 1–2.

### P713. ¿Qué presupuesto y proveedor de hosting se acepta, sabiendo que los planes gratuitos suelen suspender el servicio tras inactividad (lo que detiene cron/workers y rompe R2.3.10, R2.4.5 y R2.6.1) y que la app debe estar viva al menos hasta el 20-oct? ¿Quién paga y con qué medio? ¿Se necesitan servicios separados para web, worker, Postgres y Redis o un solo proceso con cron interno?

- **Requisitos:** R2.3.10, R2.4.5, R2.6.1
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina la arquitectura de despliegue y un costo mensual que el spec debe registrar como restricción.
- **Opciones planteadas:**
  - Plan pago mínimo
  - Free tier + keep-alive externo
  - VPS propio
  - Servidor de la universidad
- **Estudio de APIs:** §12 propone Postgres + Redis + workers separados y deploy en Railway/Render/Fly.io; no discute costos ni suspensión por inactividad.

### P714. ¿Se fija desde ahora una URL HTTPS definitiva (subdominio del proveedor o dominio propio) que se use igual en la parcial y en la final? Los redirect URIs de Google, de la Developer Key de Canvas y de la GitHub App (callback, setup_url, webhook) quedan atados a ella; ¿quién compra y configura el dominio si se usa uno propio?

- **Requisitos:** R2.1.2, R2.1.4, R2.1.5
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Cambiar la URL entre entregas obliga a reconfigurar tres proveedores externos y puede romper OAuth el día de la revisión.
- **Estudio de APIs:** §1.1 redirect_uri fija en la Developer Key; §3.3 setup_url de la App; §8.1 URL del webhook configurada en la App.

### P715. ¿Publicar el proyecto de Google Cloud en 'Production' con scopes openid/email/profile requiere verificación de la app o basta con aceptar la pantalla 'app no verificada'? ¿Qué pantalla verá el revisor la primera vez y se explica en la guía de acceso?

- **Requisitos:** R2.1.2
- **Área declarada:** infraestructura
- **Tipo:** Investigable en docs · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Determina si hace falta registrar test users y qué advertencias verá el revisor en el login.
- **Estudio de APIs:** No lo aborda.

### P716. Si se usa Free-for-Teacher: ¿permite crear secciones múltiples, group sets, overrides por sección y por estudiante, rúbricas, anuncios y conversaciones vía API con el token del profesor? ¿Hay límites de estudiantes o de invitaciones por curso?

- **Requisitos:** R2.2.2, R2.2.3, R2.4.2, R2.4.3, R2.6.5, R2.6.6, R2.7.5
- **Área declarada:** infraestructura
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Si alguna capacidad falta, el dataset de prueba no cubrirá R2.4.2/R2.4.3 o R2.6.x y habrá que buscar otra instancia a tiempo.
- **Estudio de APIs:** §1.2 afirma que en FFT pueden 'cargar estudiantes de prueba, secciones y grupos'.

### P717. ¿Con qué lenguaje y framework se construirá la aplicación (backend y frontend), decidido según la experiencia real de cada integrante y no según la recomendación del estudio? ¿Quién del equipo domina cada capa y cuánto tiempo de aprendizaje se acepta con 8 días hasta la parcial?

- **Requisitos:** Sección 4 (libre y gratuito), R2.3.10, R2.6.1, R2.5.1
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina las librerías disponibles (Octokit resuelve JWT, renovación de tokens, paginación y throttling; en Python hay que armarlo con githubkit/PyGithub), la tecnología de cola/cron, las plantillas de deploy y la velocidad del equipo. Todo requisito de jobs en background (R2.3.10, R2.4.5, R2.6.1) depende de esta elección.
- **Opciones planteadas:**
  - Node + TypeScript (Next.js / Express / NestJS + Octokit)
  - Python (FastAPI / Django + githubkit o PyGithub + canvasapi)
  - Ruby on Rails
  - Java / Kotlin + Spring Boot
  - Otro con el que el equipo ya tenga experiencia
- **Estudio de APIs:** §12 sugiere Node+TypeScript (Octokit) o Python+FastAPI, Postgres, Redis; tabla de librerías por necesidad. No es una decisión aprobada.

### P718. ¿Arquitectura monolito con render en servidor (un solo servicio desplegable, cookies de sesión) o API + SPA separada (dos deploys, CORS, auth por token, monorepo o dos repos)? Si es SPA, ¿se sirve desde el mismo origen que la API o desde otro dominio?

- **Requisitos:** R2.5.1, R2.1.6, R2.7.3
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Cambia el número de servicios a pagar/mantener en hosting gratuito, el modelo de autenticación (cookie vs token), la superficie CSRF/CORS, la forma de entregar 'todo el código por GitHub' (uno o varios repos) y la cantidad de código para 4 semanas.
- **Opciones planteadas:**
  - Monolito SSR (templates + HTMX/Alpine o similar)
  - Framework full-stack con SSR y API integradas (Next.js/Nuxt/Rails)
  - API REST + SPA (React/Vue) en el mismo origen
  - API + SPA en orígenes distintos con CORS
- **Estudio de APIs:** §12 diagrama 'Web App (SSR o SPA + API)': lo deja abierto.

### P719. ¿Qué motor de base de datos y qué proveedor: PostgreSQL gestionado por el PaaS, Postgres externo (Neon, Supabase), MySQL, SQLite en disco (se pierde en redeploy si el filesystem es efímero) o MongoDB? ¿Quién es dueño de la cuenta del proveedor?

- **Requisitos:** R2.4.5, R2.4.7, R2.5.1, R2.3.10
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El worker idempotente necesita transacciones y locks (SELECT FOR UPDATE / advisory locks); las fechas exigen timestamptz; el SHA de cada entrega vive en la BD como fuente de verdad, así que la durabilidad y el backup del proveedor son críticos para R2.4.7.
- **Opciones planteadas:**
  - Postgres del PaaS (Render/Railway)
  - Postgres externo gratuito (Neon / Supabase)
  - SQLite con disco persistente pago
  - MySQL/MariaDB
  - MongoDB Atlas free
- **Estudio de APIs:** §12 'Postgres'; §8.3 modelo de datos relacional; §14 timestamptz.

### P720. ¿Qué herramienta de migraciones de esquema se usa (Prisma, Drizzle, Knex, Alembic, Django/Rails migrations) y las migraciones corren automáticamente en cada deploy o a mano? ¿Política ante migración fallida (rollback vs forward-fix)? ¿Se permiten migraciones destructivas después del 16-sep sobre la BD de producción que ya tiene los datos de la demo?

- **Requisitos:** R2.4.7, Sección 3.1, Sección 3.2
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Un deploy con migración rota deja la app caída frente a evaluadores; sin política, cada integrante migra de forma distinta. Define además si la BD de la demo parcial sobrevive hasta la final.
- **Estudio de APIs:** No lo aborda.

### P721. ¿En qué proveedor se despliega y con qué plan? ¿El equipo está dispuesto a pagar un monto pequeño (US$5–10/mes por servicio sin sleep) o interpreta 'libre y gratuito' como costo cero absoluto también para hosting? ¿Quién pone la tarjeta y a nombre de quién queda la cuenta? Verificar: Railway ya no ofrece plan gratuito permanente (crédito de prueba), Fly.io eliminó el free tier para cuentas nuevas, Render Free duerme y limita a un web service.

- **Requisitos:** Sección 3.2 (URL disponible 2 semanas), Sección 4 (libre y gratuito), R2.5.2
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Decide si hay sleep de instancia (afecta cron y webhooks), si se puede tener worker separado, si la URL sobrevive las 2 semanas post-entrega y si hay que reconfigurar redirect URIs al cambiar de proveedor.
- **Opciones planteadas:**
  - Render Free (sleep) / Render Starter pago
  - Railway con crédito de prueba o plan Hobby
  - Fly.io
  - Vercel (frontend) + backend en otro proveedor
  - VPS gratuito (Oracle Cloud Always Free) o VPS pago
  - Servidor de la universidad / PC propio con túnel
- **Estudio de APIs:** §12 'Deploy en Railway/Render/Fly.io' sin analizar planes ni sleep.

### P722. Si el hosting duerme la instancia por inactividad (Render Free ~15 min), ¿cómo se garantiza que los jobs periódicos (aprovisionamiento cada 2 min, snapshots cada 5, sync Canvas cada 10, informe 07:00) realmente se ejecuten? Si se usa un scheduler externo que llama a endpoints internos, ¿cómo se autentican esos endpoints (header con secreto) y qué pasa si se invocan dos veces seguidas?

- **Requisitos:** R2.3.10, R2.4.5, R2.6.1, R2.4.4
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** R2.3.10 exige creación 'automática, sin interacción de un usuario': si el proceso está dormido durante la demo, el repo no aparece. Un snapshot tardío sigue siendo correcto (until histórico) pero un informe que no se envía o un mapeo que no se procesa son fallos visibles.
- **Opciones planteadas:**
  - Pinger externo cada 5 min (UptimeRobot, cron-job.org) para mantener despierta la instancia
  - Scheduler externo (cron-job.org, GitHub Actions schedule) que llama a /jobs/run con secreto
  - Plan pago sin sleep
  - Worker en otro proveedor que no dorme (VPS/Oracle Free)
  - Aceptar la latencia y documentarla
- **Estudio de APIs:** §7.5 'no dependan de que el proceso esté vivo a la hora exacta'; §12 lista de crons. No menciona sleep del hosting.

### P723. GitHub exige respuesta al webhook en 10 s y no reintenta automáticamente las entregas fallidas de una GitHub App (solo redelivery manual o vía API). Con arranque en frío de 30–60 s en instancia dormida, ¿se acepta perder webhooks y depender del reconciliador cada 15 min, se implementa redelivery automático (GET /app/hook/deliveries + POST .../attempts), o el diseño final es 'solo polling' y los webhooks son un plus?

- **Requisitos:** R2.5.2, R2.5.10, R2.5.1
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la latencia real 'push en GitHub → visible en dashboard', el volumen de llamadas del reconciliador (rate limit) y qué se promete en el spec como comportamiento observable.
- **Opciones planteadas:**
  - Webhooks + reconciliador 15 min (aceptar pérdidas)
  - Webhooks + redelivery automático por API
  - Solo polling incremental (sin webhooks)
  - Webhooks solo en prod pago sin sleep
- **Estudio de APIs:** §8.1 webhooks + '202 en <10 s'; §8.2 reconciliador cada 15 min con ETag; no trata cold start ni redelivery.

### P724. ¿Cola con Redis (BullMQ / Celery), que exige un servicio Redis adicional (Upstash free 10k comandos/día, Render Redis free efímero), o cola respaldada en la propia base de datos (pg-boss, Solid Queue, django-q2, tabla jobs + SELECT ... FOR UPDATE SKIP LOCKED)? ¿O sin cola formal: cron en proceso que barre tablas de estado (patrón outbox)?

- **Requisitos:** R2.3.10, R2.6.7, R2.4.5
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Cada servicio extra en free tier es un punto de fallo y una cuenta más; la elección fija cómo se implementan locks, reintentos, idempotencia y el panel de estado de jobs.
- **Opciones planteadas:**
  - BullMQ/Celery + Redis externo
  - Cola en Postgres (pg-boss, Solid Queue, django-q2)
  - Cron en proceso + tablas de estado (sin cola)
- **Estudio de APIs:** §12 'Redis para la cola', BullMQ/Celery; §9.4 propone tabla notification_outbox.

### P725. ¿Scheduler y workers corren dentro del mismo proceso web (un solo servicio gratuito; riesgo de bloquear requests y de doble ejecución si el PaaS levanta 2 instancias durante un rolling deploy) o como servicio aparte (background worker es pago en Render)? Si es un solo proceso, ¿cómo se garantiza un único líder de cron (lock en BD, PID file, env flag)? ¿Dónde se cachea el installation token de GitHub (memoria vs BD/Redis) si hay más de una instancia?

- **Requisitos:** R2.3.10, R2.5.1, R2.4.5
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** La doble ejecución de aprovisionamiento crea repos/mensajes duplicados; el informe diario podría enviarse dos veces. Afecta costo y arquitectura.
- **Estudio de APIs:** §12 separa 'Web App' y 'Workers' como cajas distintas; §2.2 'cachéalo con TTL de ~50 min' sin decir dónde.

### P726. ¿Cómo se implementa el 'lock por sujeto' del worker de creación de repos y del job de snapshot (advisory lock de Postgres, SELECT FOR UPDATE SKIP LOCKED, lock en Redis, columna locked_until)? Si un job muere a mitad por reinicio del proceso, ¿en cuánto expira el lock, quién lo retoma y cuántos reintentos hay antes de pasar a ERROR definitivo visible en R2.3.11?

- **Requisitos:** R2.3.7, R2.3.10, R2.4.5
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Sin expiración, un reinicio deja sujetos bloqueados para siempre ('atascado'); sin lock, dos workers crean el mismo repo. Define la máquina de estados que la UI muestra.
- **Estudio de APIs:** §5.5 'idempotente, con lock por sujeto' sin especificar mecanismo ni expiración.

### P727. ¿Dónde viven los secretos (.pem de la GitHub App, client_id/secret de Canvas, client secret de Google, webhook secret, clave de cifrado de tokens, credenciales de email, DATABASE_URL): variables de entorno del PaaS, gestor de secretos, archivo .env cifrado (sops/dotenv-vault)? ¿Cómo se comparten entre integrantes (gestor de contraseñas compartido) y quién tiene acceso a producción? ¿Se incluye .env.example, pre-commit con gitleaks y escaneo de secretos en CI? Como el código se entrega por GitHub, ¿se rotan todos los secretos tras el 6-oct, y qué se hace si uno se commitea por error (rotar + reescribir historia)?

- **Requisitos:** R2.1.4, R2.1.5, R2.5.2, Sección 3.2
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Un .pem o client_secret en el historial del repo entregado es un hallazgo evidente en la corrección y un riesgo real sobre la org de GitHub y el curso de Canvas.
- **Estudio de APIs:** §14 'Secretos': no van al repo, variables de entorno; no cubre compartición ni rotación.

### P728. ¿Los refresh/access tokens de Canvas se cifran en la BD (AES-256-GCM con clave en variable de entorno, o cifrado de columna del ORM) o se guardan en claro? ¿Dónde vive la clave, qué pasa si se pierde (todos los profesores deben re-autorizar) y se soporta rotación (versión de clave por registro)? ¿La clave privada de la GitHub App se inyecta como env var multilínea o base64?

- **Requisitos:** R2.1.4, R2.4.5, R2.6.1, R2.7.6
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El token del profesor permite publicar notas y mensajes a estudiantes; su filtración desde un dump de BD gratuita es el peor escenario de seguridad del proyecto.
- **Estudio de APIs:** §1.1 'Guarda el refresh_token cifrado en BD'; no especifica mecanismo ni gestión de clave.

### P729. ¿La GitHub App se crea bajo la cuenta personal de un integrante o bajo una organización del equipo (transferible, varios administradores)? Como cada App tiene una sola webhook URL y una sola clave privada, ¿se crean Apps separadas para dev/staging/prod con orgs de prueba separadas, o una sola App apuntando a prod y en local se usa smee.io/ngrok? ¿Quién puede cambiar permisos de la App (cada cambio exige que la instalación acepte los nuevos permisos)?

- **Requisitos:** R2.1.5, R2.5.2, R2.3.7
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina cómo se prueba localmente el webhook, cuántas instalaciones hay que mantener y qué pasa con la App si el integrante dueño abandona el equipo.
- **Estudio de APIs:** §2.2 flujo de la App; §8.1 sugiere ngrok/cloudflared en local; §12 no trata entornos.

### P730. ¿Contra qué instancia(s) de Canvas se desarrolla y se demuestra: Canvas institucional (requiere Developer Key emitida por el administrador: ¿alguien ya la solicitó, a quién, con qué plazo y con qué redirect URIs?), Free-for-Teacher (canvas.instructure.com) o Canvas self-hosted en Docker? ¿La app soporta múltiples canvas_base_url (uno por curso) o una única instancia por entorno? Si el 16-sep no hay Developer Key, ¿la vinculación se hace pegando un token manual del profesor en una UI de emergencia (protegida por flag) además del flujo OAuth?

- **Requisitos:** R2.1.4, R2.1.6, R2.2.1
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Es la dependencia externa más crítica de la parcial: sin instancia con datos y sin credencial OAuth no hay demo. Decide el modelo de datos (base URL por curso) y las redirect URIs registradas.
- **Opciones planteadas:**
  - Canvas institucional con Developer Key del admin
  - Free-for-Teacher con cuenta del equipo
  - Canvas open source en Docker local/VPS
  - Combinación: institucional en prod, FFT en dev
- **Estudio de APIs:** §1.2 tokens manuales para desarrollo/demo y Plan B Free-for-Teacher; §3.2 'guarden canvas_base_url (la instancia varía)'.

### P731. Verificar si Free-for-Teacher (canvas.instructure.com) permite crear Developer Keys (OAuth2) desde la cuenta del equipo o si solo permite tokens de acceso manuales por usuario. Si solo hay tokens manuales, ¿cómo se demuestra el flujo OAuth completo el 16-sep?

- **Requisitos:** R2.1.4, R2.1.6
- **Área declarada:** infraestructura
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** El estudio afirma que en FFT 'ustedes son admin y pueden crear la Developer Key'; si no es así, el Plan B no cubre OAuth y hay que decidir entre token manual visible en la demo o conseguir la key institucional.
- **Estudio de APIs:** §1.2 Plan B: 'Free-for-Teacher, donde ustedes son admin de su propia cuenta y pueden crear la Developer Key' (sin evidencia).

### P732. ¿El proyecto de Google Cloud para OAuth queda en modo 'Testing' (máximo 100 usuarios de prueba agregados a mano: hay que registrar los gmail del profesor y ayudantes evaluadores antes de la demo) o se publica a 'Production' (pantalla 'app no verificada' si no se completa la verificación)? ¿Quién es dueño del proyecto GCP? ¿Un cliente OAuth por entorno con sus redirect URIs? Y dado que R2.1.2 restringe a gmail.com, ¿los evaluadores tienen cuentas gmail.com o usan @uandes.cl (Google Workspace)? ¿Se necesita allowlist de dominios configurable por entorno o un usuario local de emergencia?

- **Requisitos:** R2.1.2, R2.1.1
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Si un evaluador no puede iniciar sesión el 16-sep, la demo no empieza; el modo Testing exige conocer sus correos con antelación.
- **Estudio de APIs:** §3.1 solo describe la validación del claim email (@gmail.com, email_verified). No trata el estado del proyecto GCP.

### P733. ¿Cuántos entornos existen (local por desarrollador, staging, prod) y con qué datos? ¿Cómo se garantiza que dev/staging NUNCA envíen Conversations, anuncios, comentarios o emails a personas reales ni creen repos en la org real: modo dry-run/sandbox por variable de entorno, allowlist de destinatarios, org de GitHub y curso de Canvas distintos por entorno, interruptor global de comunicaciones salientes en prod para operaciones? ¿Cada desarrollador tiene BD local propia o comparten una?

- **Requisitos:** R2.6.5, R2.6.6, R2.3.7, R2.7.6
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Un job de prueba apuntando al curso real enviaría mensajes o publicaría notas a estudiantes verdaderos; es irreversible y visible para el profesor del curso.
- **Estudio de APIs:** No lo aborda.

### P734. ¿Qué organización de GitHub se usa en la demo (creada por el equipo, ¿quién es owner?) y, para uso real, ¿el profesor del curso tiene una org donde sea owner para instalar la App? ¿Plan Free de la org (repos privados con funciones limitadas) o se solicita GitHub Team gratuito vía GitHub Education for Teachers? ¿Cuántos colaboradores externos en repos privados permite la org elegida?

- **Requisitos:** R2.1.5, R2.3.7, R2.3.9
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Instalar una GitHub App exige ser owner de la org; las funciones disponibles (rulesets, branch protection en privados) dependen del plan y cambian el diseño de protección de tags.
- **Estudio de APIs:** §3.3 flujo de instalación; §14 'si la org es Free, revisen el límite de colaboradores en repos privados'.

### P735. Verificar en una org Free si los rulesets de tags (POST /orgs/{org}/rulesets, target tag) y la protección de ramas están disponibles en repositorios privados, o si requieren plan Team. Si no están disponibles, ¿se aceptan tags borrables (con el SHA en BD como única verdad) o se hacen repos públicos?

- **Requisitos:** R2.4.7, R2.4.5
- **Área declarada:** infraestructura
- **Tipo:** Verificar empíricamente · **Entrega:** Final (6-oct)
- **Por qué importa:** El estudio propone la ruleset como 'blindaje extra'; si el plan no lo permite, el spec debe declarar explícitamente que la evidencia de entrega es solo la BD y su backup.
- **Estudio de APIs:** §7.5 'Protejan los tags... ruleset de tags en la org. No es imprescindible si el SHA está en su BD'.

### P736. Con el installation token y el conjunto mínimo de permisos elegido, verificar en la semana 1 que POST /orgs/{org}/repos, PATCH is_template, POST /repos/{t}/{r}/generate, PUT collaborators (201 vs 204) y POST /git/refs funcionan (201/204) en la org de prueba, y si la configuración 'Repository creation' de la org restringe a la App. ¿Fecha límite de esta prueba y quién la hace?

- **Requisitos:** R2.3.5, R2.3.7, R2.3.9, R2.4.5
- **Área declarada:** infraestructura
- **Tipo:** Verificar empíricamente · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Un 403 descubierto el 15-sep obliga a cambiar permisos de la App y a que la instalación los acepte de nuevo; bloquea el corazón de la demo.
- **Estudio de APIs:** §2.3 'verifíquenlo empíricamente'; Apéndice A.1 y A.2.

### P737. ¿Se usa el subdominio del PaaS (*.onrender.com, *.up.railway.app, con TLS incluido) o un dominio propio (≈US$10/año, DNS, certificado automático)? Como Google, la Developer Key de Canvas y la GitHub App fijan redirect/webhook URIs, ¿la URL de producción queda congelada antes del 16-sep y es la misma que se entrega por Canvas el 6-oct? ¿Se registran de antemano las URIs de localhost, staging y prod en los tres proveedores?

- **Requisitos:** R2.1.2, R2.1.4, R2.1.5, R2.5.2, Sección 3.1
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Cambiar de URL a mitad de camino implica reconfigurar tres proveedores externos y reinstalar la App; el dominio también condiciona el remitente de email (SPF/DKIM).
- **Estudio de APIs:** §12 'necesita URL pública para los webhooks'; §1.1 redirect_uri fijo en el flujo OAuth.

### P738. ¿Se activa 'enforce scopes' en la Developer Key de Canvas y se enumera la lista exacta de scopes url:METHOD|path necesarios, o se deja sin scopes (token con todos los permisos del profesor)? En la GitHub App, ¿se piden solo Administration (write), Contents (write) y Metadata (read), y Members (write) únicamente si se decide invitar estudiantes a la org? ¿Se documenta la justificación de cada permiso para la validación del 7-oct?

- **Requisitos:** R2.1.4, R2.1.5, R2.6.5, R2.7.6
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Principio de mínimo privilegio verificable; cada permiso adicional de la App exige reaceptación por la instalación, y cada scope faltante en Canvas produce 401 en producción.
- **Estudio de APIs:** §1.3 lista de scopes; §2.3 tabla de permisos de la App; §6.4 Members opcional.

### P739. ¿El endpoint /webhooks/github valida X-Hub-Signature-256 con el body crudo y comparación en tiempo constante, rechaza con 401 sin firma, guarda X-GitHub-Delivery para descartar duplicados, limita el tamaño del body, maneja que el payload de push trae máximo 20 commits (¿fetch adicional de los restantes?), responde 202 y encola? ¿Está excluido del middleware de sesión/CSRF? ¿Se persiste el evento crudo para auditoría y por cuánto tiempo? ¿Cómo y cuándo se rota el webhook secret?

- **Requisitos:** R2.5.2, R2.5.10
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Es el único endpoint público sin autenticación de usuario; un payload forjado podría inflar la actividad de un repo (R2.5.4) o saturar la cola.
- **Estudio de APIs:** §8.1 verifySignature con timingSafeEqual y body crudo; '202 en <10 s'. No cubre duplicados, tamaño ni rotación.

### P740. ¿Logs estructurados (JSON) con correlation id por request y por job, sin tokens ni datos personales de estudiantes? ¿La retención del PaaS (Render free ~7 días) basta o se envían a un servicio gratuito (Better Stack, Axiom, Papertrail)? ¿Se usa Sentry/GlitchTip free para excepciones con alertas? ¿Habrá una pantalla de administración de jobs (última ejecución, duración, fallos, próxima ejecución, botón 'ejecutar ahora') visible en la demo para evidenciar que el proceso automático corre?

- **Requisitos:** R2.3.11, R2.6.4, R2.3.10
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Sin observabilidad no se puede diagnosticar por qué un repo no se creó ni demostrar que el informe diario salió; la pantalla de jobs es además evidencia para la corrección.
- **Estudio de APIs:** §9.1 'registro de envíos (sent_at, status)'; §7.4 'última sincronización' en UI; no cubre logging ni alertas.

### P741. ¿Existe endpoint /health que verifique BD (y opcionalmente conectividad a Canvas/GitHub) y un monitor externo gratuito (UptimeRobot, Better Uptime) con alerta a Telegram/WhatsApp/email del equipo? ¿Quién está 'de turno' entre el 6 y el 20 de octubre, con qué tiempo máximo de respuesta, y cómo se comunica una caída al profesor/ayudantes que están corrigiendo?

- **Requisitos:** Sección 3.2 (disponible al menos dos semanas)
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** 'Las funcionalidades a las que no se puede acceder no se consideran cumplidas': una caída no detectada durante la corrección equivale a funcionalidad inexistente.
- **Estudio de APIs:** §12 recuerda la exigencia de dos semanas; no propone monitoreo.

### P742. Si el SHA de cada entrega vive solo en la BD, perder la BD destruye la evidencia de qué corregir. ¿El plan gratuito elegido incluye backups automáticos (Neon/Supabase/Render free no incluyen PITR)? ¿Se agrega pg_dump diario vía GitHub Actions a un almacenamiento privado (cifrado, ¿dónde?) y se prueba una restauración completa antes del 6-oct? ¿El tag en GitHub se considera respaldo oficial del SHA?

- **Requisitos:** R2.4.5, R2.4.7, R2.7.4
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Define el requisito de durabilidad de R2.4.7 en términos operativos y qué se responde el 7-oct a '¿y si pierden la base de datos?'.
- **Estudio de APIs:** §7.5 'SHA en BD = verdad; un tag se puede borrar, una fila en su BD no'. No cubre backups de la BD.

### P743. Confirmar en la documentación del proveedor de BD gratuito elegido: Render Free Postgres expira y se borra a los 30 días; Supabase pausa proyectos tras 7 días sin actividad; Neon autosuspende con latencia de arranque en la primera consulta (¿afecta la 'inmediatez' de R2.5.1?); límites de almacenamiento (~0.5 GB) y de conexiones simultáneas. ¿La ventana 10-sep → 20-oct cabe dentro de esas condiciones?

- **Requisitos:** R2.5.1, Sección 3.2
- **Área declarada:** infraestructura
- **Tipo:** Investigable en docs · **Entrega:** Ambas entregas
- **Por qué importa:** Una BD que expira el 10-oct borra todo a mitad de la corrección; la latencia de reanudación puede hacer que el dashboard tarde segundos frente al evaluador.
- **Estudio de APIs:** No lo aborda.

### P744. ¿Qué proveedor de email y con qué límites (Resend 100/día y exige dominio verificado para enviar a terceros; Brevo 300/día; Mailgun; SMTP de Gmail con contraseña de aplicación ~500/día)? Sin dominio propio, ¿se acepta enviar desde una cuenta Gmail del equipo? ¿Remitente y nombre visibles ('ICC4201 Bot <...>')? ¿Cómo se demuestra el envío si el correo cae en spam (registro de envíos + informe accesible por URL)? ¿HTML + texto plano?

- **Requisitos:** R2.6.4, R2.6.3, R2.6.1
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** R2.6.4 depende de un tercero con cuotas; sin dominio verificado varios proveedores no entregan a destinatarios arbitrarios. Fija el plan de demostración del informe.
- **Estudio de APIs:** §9.1 sugiere SendGrid/Resend/Mailgun/SMTP Gmail, guardar registro de envíos y publicar el informe como página web.

### P745. ¿Qué identidad de committer/author llevan los commits que la app hace al repo base (PUT /contents) y los tags (nombre/correo de un bot del curso, la identidad <app>[bot], o el profesor)? ¿Los repos base y de estudiantes se crean privados por defecto (sin opción) o el profesor puede elegir visibilidad? ¿Quién queda como admin del repo (solo la App/owners de la org)?

- **Requisitos:** R2.3.6, R2.4.5, R2.3.7
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el aspecto del historial de Git que verán estudiantes y correctores, y la superficie de permisos (evitar admin a estudiantes).
- **Estudio de APIs:** §5.3 ejemplo committer 'ICC4201 Bot'; §14 'créenlos privados'; §5.4 'usen push, nunca admin'.

### P746. ¿Deploy con Dockerfile (mismo artefacto en local y producción) o buildpacks nativos del PaaS? ¿Rollback: redeploy del commit anterior (¿y las migraciones ya aplicadas?), o imagen/versión previa? ¿Cuánto tarda un deploy y cómo se evita perder jobs en curso durante el reinicio (graceful shutdown, jobs reanudables por estado persistido)? ¿Se fijan versiones de runtime (Node/Python) y lockfiles?

- **Requisitos:** R2.3.10, R2.4.5, Sección 3.2
- **Área declarada:** infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Un reinicio a mitad de la creación de 20 repos debe reanudarse sin duplicar; el rollback debe estar definido antes de necesitarlo frente a evaluadores.
- **Estudio de APIs:** No lo aborda.

### P747. ¿Se dispone de una URL pública HTTPS estable para el receptor de webhooks antes de la entrega final (proveedor de hosting elegido, quién lo administra, costo, disponibilidad las dos semanas posteriores al 6-oct) y de un túnel (ngrok/cloudflared) para desarrollo? Sin esto la ingesta por webhooks no puede probarse y el diseño debe cambiar a polling.

- **Requisitos:** R2.5.2, R2.5.10
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Condiciona la decisión webhooks vs polling y el calendario de despliegue.
- **Estudio de APIs:** §8.1 (ngrok/cloudflared o desplegar temprano) y §12 (URL pública necesaria para webhooks y disponibilidad de dos semanas).

### P748. ¿Qué proveedor se usará para el envío de correo: SMTP de una cuenta Gmail del equipo (requiere App Password con 2FA, ~500 correos/día en cuentas personales), SendGrid, Resend, Mailgun, Brevo u otro con plan gratuito? ¿Dispone el equipo de un dominio propio para verificar como remitente (varios proveedores solo permiten enviar a la dirección del propietario mientras no haya dominio verificado)?

- **Requisitos:** R2.6.4
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Condiciona deliverability, límites diarios, la dirección From posible y si el informe puede llegar a las cuentas de los correctores durante la revisión.
- **Opciones planteadas:**
  - Gmail SMTP con App Password
  - SendGrid plan gratuito
  - Resend plan gratuito
  - Mailgun
  - Brevo
  - SMTP institucional
- **Estudio de APIs:** §9.1 lista «SendGrid / Resend / Mailgun / SMTP de Gmail» sin elegir ni comparar límites.

### P749. ¿Tiene el equipo acceso a los registros DNS de un dominio para configurar SPF, DKIM y DMARC del remitente? Si no, ¿se acepta el riesgo de que el informe caiga en spam en las cuentas de los correctores y se mitiga con la versión web del informe en la app y una nota en la documentación?

- **Requisitos:** R2.6.4
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Define si «el correo llegó a la bandeja de entrada» es un criterio de aceptación verificable o una limitación documentada.
- **Estudio de APIs:** §9.1 anticipa que el correo puede «caer en spam» y recomienda la versión web como respaldo; no aborda SPF/DKIM/DMARC.

### P750. ¿Cuál es el volumen estimado de correos por día (cursos activos × suscritos + envíos de prueba) y cabe en el plan gratuito elegido? ¿El plan gratuito sigue vigente sin tarjeta ni expiración de trial durante las dos semanas posteriores al 6-oct (§3.2)? ¿Qué hace la app al agotar la cuota diaria (encola para el día siguiente, descarta, avisa)?

- **Requisitos:** R2.6.4
- **Área declarada:** infraestructura
- **Tipo:** Investigable en docs · **Entrega:** Final (6-oct)
- **Por qué importa:** Define la política ante cuota agotada y protege la disponibilidad exigida tras la entrega final.
- **Estudio de APIs:** No lo aborda.

### P751. ¿Quién crea el proyecto de Google Cloud y la pantalla de consentimiento OAuth, con qué cuenta (personal de un integrante vs cuenta del equipo)? ¿La app quedará 'En producción' o en estado 'Testing' (que solo permite iniciar sesión a usuarios de prueba agregados manualmente)? ¿Se agregarán los gmails del profesor y de los ayudantes evaluadores como usuarios de prueba, o se publicará, antes del 16-sep?

- **Requisitos:** R2.1.2
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Si la app OAuth está en Testing y los evaluadores no están listados, no podrán iniciar sesión en la demo; define el checklist de despliegue y la custodia del client_secret.
- **Estudio de APIs:** No lo aborda.

### P752. ¿Con qué cuenta se crea la GitHub App (cuenta personal de un integrante o una organización del equipo)? ¿Quién custodia la clave privada .pem y el webhook secret, y cómo se comparten con el resto del equipo y con el despliegue? ¿Qué organización de GitHub se usará en la demo del 16-sep y quién es su owner? ¿La organización del curso real la crea el profesor (no hay API para crear organizaciones) o el equipo?

- **Requisitos:** R2.1.5
- **Área declarada:** infraestructura
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Sin App ni org listas no hay demo; define responsables, secretos y si la app debe guiar al profesor a crear su propia org.
- **Estudio de APIs:** §13 hito 3 ('GitHub App creada + instalada en una org de prueba', Día 1–2, riesgo rojo); §14 los secretos van a variables de entorno.

---

## proceso

### P753. ¿Cuál es el dataset de prueba en Canvas para la parcial y para la final? Cantidad de estudiantes ficticios, secciones, group sets/grupos, tareas con overrides por sección e individuales; ¿incluye casos borde deliberados (estudiante en dos secciones, estudiante sin grupo, estudiante retirado/inactive, Test Student de Canvas, estudiante que entregó un usuario GitHub inexistente o el nombre de una organización, grupo modificado después de crear repos, tarea de Canvas eliminada tras vincularla)?

- **Requisitos:** R2.2.1, R2.2.2, R2.2.3, R2.2.6, R2.3.11, R2.4.2, R2.4.3
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El dataset define qué estados de la tabla R2.3.11 y del panel R2.2.6 se pueden mostrar; sin casos borde cargados esas funcionalidades no son 'accesibles en el uso'.
- **Estudio de APIs:** §13 hito 1 sugiere 2 secciones, ~10 estudiantes, 1 group set, 2 assignments con overrides; §4.1 advierte filtrar el Test Student; Apéndice A.7 pide probar precedencia de overrides con un caso real.

### P754. ¿Cómo se crean los estudiantes ficticios en Canvas y puede el equipo iniciar sesión como ellos? En Free-for-Teacher cada estudiante invitado necesita un correo real que acepte la invitación: ¿se crean N cuentas o alias de correo, se usan correos de los integrantes, o se piden cuentas de prueba al administrador institucional? ¿Cuántas se necesitan para demostrar la entrega del usuario GitHub vía tarea de Canvas y la recepción del mensaje/comentario?

- **Requisitos:** R2.2.4, R2.2.5, R2.3.12
- **Área declarada:** proceso
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Sin poder entrar como estudiante no se puede demostrar el enrolamiento (R2.2.4/R2.2.5) ni la notificación (R2.3.12) desde el lado de Canvas durante la demo.
- **Estudio de APIs:** §6.1 asume que los estudiantes entregan su usuario en una tarea de Canvas; no aborda cómo se crean las cuentas de estudiante de prueba.

### P755. ¿Cuántas cuentas GitHub de 'estudiante' se necesitan y de dónde salen? Se requieren para (a) validar mapeos con GET /users, (b) aceptar invitaciones a repos (pasar de 'invitación pendiente' a 'listo'), (c) hacer commits que alimenten dashboard y timeline en la final. Considerando que los Términos de GitHub limitan a una cuenta gratuita por persona: ¿cuentas de los integrantes, de terceros que colaboren, cuentas 'machine user'?

- **Requisitos:** R2.2.4, R2.3.9, R2.5.2, R2.5.4, R2.5.8
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Determina cuántos repos pueden llegar al estado READY y cuánta actividad real habrá para 2.5; el spec de datos de demo debe listar esas cuentas y quién las controla.
- **Estudio de APIs:** §5.4 explica 201 (invitación pendiente) vs 204 (acceso inmediato); §6.4 sugiere invitar a la org para simplificar estados.

### P756. ¿Quién presenta la demo del 16-sep (un presentador, rotación por etapa del flujo, o todos), quién opera el teclado, quién juega el rol de 'estudiante' en Canvas/GitHub en paralelo, y desde qué cuentas (profesor demo, estudiante demo, GitHub de estudiante)? ¿Habrá un ensayo cronometrado completo y en qué fecha?

- **Requisitos:** —
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** El guion del spec debe listar actores, cuentas y pasos; el ensayo detecta tiempos muertos del worker y fallas de red antes del día.
- **Estudio de APIs:** §13 propone un guion de demo pero no asigna roles.

### P757. ¿Cuál es el plan de contingencia para la demo presencial si falla la red del aula, la API de Canvas/GitHub responde 5xx o se agota el rate limit: hotspot móvil, segundo curso demo precargado, video grabado del flujo completo, respaldo de BD restaurable a un estado 'pre-demo'?

- **Requisitos:** R2.3.7, R2.3.12
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Define artefactos que hay que producir antes del 16-sep (video, snapshot de BD, curso espejo) y quién los prepara.
- **Estudio de APIs:** §8.1 menciona ngrok/cloudflared para localhost pero recomienda desplegar temprano; no aborda contingencias presenciales.

### P758. ¿Cuál es la definición de 'hecho' para cada requisito R2.x.y? A decidir si incluye: (1) accesible desde la UI desplegada en la URL oficial sin tocar BD ni consola; (2) demostrable con los datos demo; (3) estados de error y vacío visibles; (4) criterio de aceptación escrito en el spec y verificado por otro integrante; (5) documentado para la validación; (6) prueba automatizada.

- **Requisitos:** —
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Alinea la regla del enunciado ('no accesible = no cumplido') con el cierre de tareas del equipo y la trazabilidad del spec.
- **Estudio de APIs:** No lo aborda.

### P759. Sin punto base y con 20 días entre entregas, ¿cuál es el orden de prioridad de las secciones 2.4–2.7 para la final y qué elementos se declaran 'recortables' si falta tiempo (p. ej. extras de R2.5.9, comunicaciones automáticas R2.6.7, rúbrica embebida R2.7.5, OAuth GitHub §6.2, ruleset de tags)? ¿Qué criterio ordena: visibilidad en la revisión, riesgo técnico, dependencia externa?

- **Requisitos:** R2.4.3, R2.5.9, R2.6.7, R2.7.5, R2.7.6
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** Fija el backlog ordenado y evita decidir bajo presión el 4 de octubre.
- **Estudio de APIs:** §8.5 sugiere elegir 2–3 extras para 2.5.9; §7.5 marca la ruleset de tags como no imprescindible.

### P760. ¿Cuáles son los hitos internos con fecha: (parcial) dataset Canvas listo, App GitHub probada, primer deploy, código congelado, ensayo general; (final) fin de desarrollo, congelamiento para video, deploy final, prueba con revisor externo, simulacro de validación? ¿Se adopta el plan día a día del §13 o se redefine?

- **Requisitos:** —
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** El spec de proceso necesita un cronograma verificable; 8 días hasta la parcial obligan a atacar primero las dependencias externas.
- **Estudio de APIs:** §13 propone 10 hitos con días (Día 1 a Día 7) para la parcial.

### P761. ¿Cuántos integrantes tiene el equipo y qué roles se asignan (integración Canvas, integración GitHub/worker, frontend/UX, infraestructura/deploy/secretos, spec/QA/documentación, demo/video)? ¿Hay un responsable único de dependencias externas (Developer Key, org, cuentas de prueba) y otro de la disponibilidad post-entrega?

- **Requisitos:** —
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Los requisitos de la parcial dependen de tareas de infraestructura que nadie asume 'por defecto'.
- **Estudio de APIs:** No lo aborda.

### P762. ¿Se tomará un respaldo de la BD (y lista de repos de la org) inmediatamente antes de la demo del 16-sep y antes de la entrega del 6-oct, con procedimiento de restauración probado? ¿El seed reproducible incluye mapeos y repos ya creados o parte de cero?

- **Requisitos:** —
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Permite volver a un estado conocido si una demo o un revisor rompe datos.
- **Estudio de APIs:** No lo aborda.

### P763. ¿Qué commit/tag corresponde a 'la entrega parcial' y a 'la entrega final' (p. ej. git tag entrega-parcial, entrega-final), y se congela el deploy en ese tag hasta terminar la revisión? ¿Se permite seguir mergeando a main después del 6-oct mientras la URL sigue viva?

- **Requisitos:** —
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Garantiza que lo revisado es lo entregado y evita regresiones durante la ventana de dos semanas.
- **Estudio de APIs:** No lo aborda.

### P764. ¿En qué formato se escriben los criterios de aceptación del spec (Given/When/Then, checklist por pantalla) y se mantiene una matriz de trazabilidad R2.x.y → pantalla → criterio → estado (hecho/parcial/fuera de alcance) que pueda entregarse a los revisores como guion de prueba?

- **Requisitos:** —
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Estructura el spec completo que el equipo exige y da a los revisores un camino para encontrar cada funcionalidad ('no accesible = no cumplido').
- **Estudio de APIs:** §11 ofrece una matriz requisito → endpoints que puede servir de base para la trazabilidad.

### P765. ¿Quién decide las respuestas a este banco de preguntas de alcance, dónde se registran (decision log con id, fecha, responsable, requisitos afectados y criterio de aceptación resultante) y cuál es la fecha de corte para las que afectan la parcial versus la final? ¿El spec cita cada decisión (trazabilidad pregunta → decisión → requisito) y qué ocurre si una verificación empírica posterior contradice el supuesto de una decisión ya tomada?

- **Requisitos:** R2.1.1, R2.7.7
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Sin proceso de cierre, las preguntas quedan abiertas y alguien 'rellena huecos' implícitamente; define la mecánica del spec.
- **Estudio de APIs:** §13 y §14 proponen plan e hitos pero no un proceso de decisión ni un registro de decisiones de alcance.

### P766. ¿Qué niveles de test son obligatorios: unitarios para lógica pura (fecha efectiva con overrides, parser de login de GitHub, sanitización de nombres de repo, máquina de estados), integración contra mocks HTTP de Canvas/GitHub (nock/msw/responses con fixtures grabadas de la API real), e2e con Playwright sobre la UI? ¿Se corren tests de contrato contra las APIs reales en CI (con secretos) o solo manualmente? ¿Cobertura mínima exigida y quién la revisa?

- **Requisitos:** R2.4.3, R2.3.8, R2.2.4, R2.3.7
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Sin mocks, los tests dependen de instancias reales y consumen rate limit; la lógica de fechas y nombres es donde se pierden puntos y se pregunta el 7-oct.
- **Estudio de APIs:** No lo aborda.

### P767. ¿CI con GitHub Actions (ilimitado en repo público, 2.000 min/mes en privado) ejecutando lint/format (ESLint+Prettier / ruff+black), tests y build en cada PR como checks obligatorios? ¿Deploy automático a producción al mergear a main o manual con aprobación? ¿Existe staging con deploy automático de la rama de desarrollo? ¿Ventana de congelamiento de deploys antes del 16-sep y del 6-oct (p.ej. 24 h)?

- **Requisitos:** Sección 3.2 (código por GitHub), Sección 3.1
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Define el flujo diario del equipo y evita el deploy roto la noche anterior; decide si se necesita un segundo entorno (costo).
- **Estudio de APIs:** §13 hito 10 'nunca deployen la noche anterior'.

### P768. ¿Modelo de ramas (trunk-based con ramas cortas vs GitFlow), PRs obligatorios con al menos un revisor distinto del autor, protección de main, convención de commits (Conventional Commits), convención de nombres de ramas/issues y uso de GitHub Projects? ¿El repositorio del proyecto es público o privado, y quién se agrega como colaborador (profesor, ayudantes del curso)? ¿Se exige que cada integrante haya tocado cada módulo (por la validación individual del 7-oct)?

- **Requisitos:** Sección 3.2 (código por GitHub), Sección 4 (ser dueños del código)
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** La revisión individual del 7-oct penaliza no conocer el código; el flujo de PRs con revisión es el mecanismo para distribuir conocimiento. Público/privado afecta minutos de CI y exposición de secretos.
- **Estudio de APIs:** No lo aborda.

### P769. ¿Qué datos de demostración se preparan: curso Canvas de pruebas con 2 secciones, ~10 estudiantes, group set y assignments con overrides; y cuántas cuentas de GitHub 'estudiante' reales se necesitan (cuentas personales de los integrantes, cuentas secundarias — GitHub permite una cuenta gratuita por persona según sus términos) para mostrar invitación aceptada vs pendiente vs usuario inexistente? ¿Existe script de seed/reset para devolver la BD de producción y la org de GitHub (borrar repos de demo) al estado inicial antes de cada ensayo? ¿Cuántos ensayos completos cronometrados se hacen sobre producción?

- **Requisitos:** Sección 3.1, R2.2.4, R2.3.9, R2.3.11
- **Área declarada:** proceso
- **Tipo:** Dependencia externa · **Entrega:** Parcial (16-sep)
- **Por qué importa:** La demo exige mostrar el flujo con problemas visibles (R2.3.11); sin cuentas y datos controlados no se puede reproducir. El reset evita 422 'name already exists' en pleno ensayo.
- **Estudio de APIs:** §13 hito 1 (Canvas de pruebas con datos reales) y guion de demo; §13 'dejen visible un caso con problema'.

### P770. ¿Cómo se interpreta 'de uso libre y gratuito': solo librerías OSS (¿se aceptan GPL/AGPL o solo MIT/Apache/BSD?) y además servicios SaaS con free tier (hosting, email, Sentry, Google OAuth)? ¿Un plan de pago mínimo de hosting sería aceptable para el profesor? ¿Se genera un inventario de licencias (license-checker / pip-licenses) para la entrega y se verifica la licencia de fuentes, íconos y componentes de UI?

- **Requisitos:** Sección 4 (libre y gratuito)
- **Área declarada:** proceso
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Es un criterio explícito del enunciado; una dependencia con licencia incompatible o un servicio pago podrían cuestionarse en la corrección.
- **Estudio de APIs:** §12 'Stack sugerido (libre según el enunciado)'; no analiza licencias ni servicios.

### P771. Si el 16-sep falla un proveedor (Canvas institucional caído, incidente de GitHub, Google OAuth, hosting dormido o caído, internet del aula), ¿cuál es el plan B para cada uno y quién lo ejecuta? Opciones: correr localmente con túnel (ngrok/cloudflared) desde un notebook con hotspot; segunda cuenta/proveedor de hosting con la misma imagen; instancia Free-for-Teacher como Canvas alterno; login alternativo (token manual de Canvas, usuario local de emergencia) tras flag; snapshot de BD pre-demo; video grabado del flujo como último recurso. ¿Cuánto tiempo de la demo se tolera perder antes de activar el plan B?

- **Requisitos:** Sección 3.1, R2.1.4, R2.1.5, R2.3.7
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** La parcial vale 1.6 puntos y se evalúa en vivo; el plan B debe estar definido, ensayado y con roles asignados, no improvisado.
- **Estudio de APIs:** §1.2 token manual como Plan B; §8.1 ngrok/cloudflared para localhost; §13 'deploy temprano'.

### P772. ¿La demo del 16-sep se hace contra la producción desplegada (la misma URL entregada por Canvas) o desde localhost? Si es producción, ¿se congela el código 24 h antes, se prohíben deploys y se pre-calienta la instancia (ping) minutos antes para evitar el arranque en frío frente al profesor? ¿Se mantiene un tag/release de la versión demostrada?

- **Requisitos:** Sección 3.1, Sección 3.2
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Evita el deploy roto de última hora y el cold start de 40 s en el primer clic; el tag permite volver a la versión demostrada si algo se rompe después.
- **Estudio de APIs:** §13 hito 10 'Deploy con URL pública el día 6; nunca deployen la noche anterior'.

### P773. ¿Se exige README con instalación local, .env.example, pasos para crear la GitHub App, la Developer Key y el cliente Google, y un runbook operativo (reiniciar worker, rotar secreto, restaurar backup, agregar usuario de prueba de Google, reenviar webhook)? ¿Se registran las decisiones de infraestructura como ADRs cortos para que cada integrante pueda defenderlas el 7-oct?

- **Requisitos:** Sección 3.3 (validación 7-oct), Sección 4 (ser dueños del código)
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Final (6-oct)
- **Por qué importa:** La validación individual descuenta hasta 3 puntos por no conocer el proyecto; los ADRs y el runbook son la forma barata de distribuir ese conocimiento.
- **Estudio de APIs:** §14 lista preguntas probables del 7-oct con respuestas; no propone documentación del equipo.

### P774. ¿Hasta qué fecha se congelan las decisiones de stack, hosting, BD y cola (p.ej. 9-sep) para que el spec pueda fijar requisitos no funcionales, y quién es responsable de cada dependencia externa (Developer Key, GitHub App/org, proyecto Google, proveedor de email, cuenta de hosting) con fecha de 'listo'?

- **Requisitos:** Sección 3.1, Sección 3.2
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Sin fecha de congelamiento y responsables, las preguntas de esta lista quedan abiertas hasta la demo y el spec no puede cerrarse.
- **Estudio de APIs:** §13 propone hitos por día (Día 1: Canvas de pruebas, Developer Key, GitHub App) sin asignar responsables.

### P775. Para demostrar R2.5.4 y R2.5.8 se necesitan varios usuarios de GitHub distintos haciendo commits en un mismo repo grupal, y commits distribuidos en el tiempo para que el gráfico tenga contenido. ¿Con qué cuentas se hará (cuentas de los integrantes del equipo, cuentas de prueba, commits con distintos user.email sin cuenta asociada)? ¿Se preparará un script de generación de commits sintéticos con fechas distribuidas para la demo?

- **Requisitos:** R2.5.4, R2.5.8, R2.5.2
- **Área declarada:** proceso
- **Tipo:** Dependencia externa · **Entrega:** Final (6-oct)
- **Por qué importa:** Sin datos realistas la demo del dashboard y del timeline no puede evidenciar los requisitos; define un entregable interno de datos de prueba.
- **Estudio de APIs:** §13 plantea un Canvas de pruebas con estudiantes y overrides pero no datos de commits en GitHub.

### P776. ¿La ingesta de commits (webhook o polling) debe estar operativa desde la entrega parcial, aunque el dashboard no se demuestre el 16-sep, para acumular historial real hasta la final y detectar problemas temprano? ¿O se posterga y en la parcial sólo se muestra el estado de creación de repos?

- **Requisitos:** R2.5.2, R2.5.5
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Fija el alcance de la parcial y el plan de trabajo; decide si la infraestructura de workers se construye en la primera o segunda mitad.
- **Estudio de APIs:** §13 (plan de la parcial) no incluye la ingesta de commits; §8 la ubica implícitamente para la final.

### P777. ¿La aplicación tendrá un reloj inyectable (o un modo de simulación de tiempo controlado por variable de entorno en entornos no productivos) para probar y demostrar sin esperar días reales: cierre de entregas y captura, recordatorios de 48 h, informe diario, 'N días sin actividad' y cambio de horario? ¿O se probará solo con fechas históricas (el job barre todo lo vencido) y esperando tiempo real? ¿Qué se usará en la demo del 6-oct para provocar un cierre frente al revisor?

- **Requisitos:** R2.4.5, R2.6.1, R2.6.7, R2.3.10
- **Área declarada:** proceso / infraestructura
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Sin control del tiempo, gran parte de 2.4–2.6 no se puede probar ni demostrar de forma repetible.
- **Opciones planteadas:**
  - Reloj inyectable por entorno
  - Solo fechas históricas + tiempo real
  - Endpoint administrativo 'ejecutar job X como si fuera la fecha Y' (no productivo)
- **Estudio de APIs:** §7.5 señala que el job captura 'todo lo vencido y no capturado' (permite pruebas con fechas pasadas); no aborda simulación de tiempo ni pruebas de jobs.

### P778. El examinador del 7-oct puede preguntar por qué no se usó LTI 1.3 (un enlace dentro de Canvas que identifica al estudiante sin que use la app, alternativa al magic link OAuth) ni GitHub Classroom (que ya hace roster + creación de repos). ¿El equipo evalúa LTI como mecanismo de enrolamiento (requiere que el administrador emita una LTI Developer Key; ¿es viable en la instancia disponible?) o lo descarta, y documenta en un ADR la comparación con GitHub Classroom y la justificación de la estrategia elegida?

- **Requisitos:** R2.2.4, R2.2.5, R2.1.4
- **Área declarada:** proceso / 2.2
- **Tipo:** Decisión del equipo · **Entrega:** Ambas entregas
- **Por qué importa:** Prepara la defensa de la decisión de diseño más evaluada del proyecto (usabilidad del enrolamiento) y puede abrir una alternativa técnica.
- **Opciones planteadas:**
  - ADR de justificación sin implementar LTI
  - Explorar LTI 1.3 si el admin puede emitir la key
  - Fuera de alcance sin documentación
- **Estudio de APIs:** §0 y §6 afirman que no existe puente Canvas↔GitHub y proponen tarea de Canvas + OAuth opcional (§6.2); no evalúan LTI 1.3 ni GitHub Classroom.

### P779. Para la demo del 16-sep, ¿qué comunicaciones se mostrarán funcionando: solo «repositorio disponible» vía Canvas (necesaria para cerrar el flujo de R2.3.12), o también el recordatorio de mapeo faltante? ¿Se mostrará algún toggle de comunicación en la configuración de la tarea individual?

- **Requisitos:** R2.6.7, R2.3.12, R2.6.5
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Fija el alcance mínimo de comunicación exigible en la parcial y lo que se posterga a la final.
- **Estudio de APIs:** §13 hito 9 «Notificación al estudiante por Canvas» dentro del plan de la parcial; el guion de demo termina con «mostrar el mensaje que le llegó al estudiante en Canvas».

### P780. ¿Se asume que el estudiante recibirá el mensaje directo o anuncio por email según sus propias preferencias de notificación de Canvas (que la app no controla) y se documenta como limitación? En el entorno de demo (Free-for-Teacher con estudiantes ficticios), ¿cómo se mostrará que «le llegó» el mensaje (iniciar sesión como estudiante de prueba, mostrar la bandeja de Canvas del profesor)?

- **Requisitos:** R2.6.5, R2.6.6, R2.3.12
- **Área declarada:** proceso
- **Tipo:** Dependencia externa · **Entrega:** Ambas entregas
- **Por qué importa:** Define expectativas realistas y el guion de demo; Canvas no garantiza entrega por email.
- **Estudio de APIs:** §1.2 recomienda Free-for-Teacher como entorno de demo; §13 guion «mostrar el mensaje que le llegó al estudiante en Canvas».

### P781. ¿Qué criterios de aceptación de usabilidad medibles fija el equipo? Ejemplos a decidir: máximo de pantallas/pasos para el flujo registro→repos creados; tiempo objetivo para un profesor nuevo sin ayuda (p.ej., < 10 min); una prueba de usabilidad con un usuario externo (ayudante real) antes del 16-sep; 'cero callejones sin salida' (toda pantalla de error o vacío ofrece al menos una acción); toda acción en background muestra estado y última ejecución.

- **Requisitos:** R2.1.6, R2.3.11
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Convierte 'facilidad de uso' en criterios verificables que se pueden incluir en el spec y usar como checklist de QA antes de la demo.
- **Estudio de APIs:** no lo aborda (solo sugiere elementos puntuales de usabilidad: checklist verde/rojo, última sincronización, botón reintentar).

### P782. ¿R2.1.7–R2.1.9 (co-profesores, ayudantes, retiro) quedan fuera de la demo del 16-sep (el enunciado de la parcial no los menciona) o el equipo los incluye? ¿Los evaluadores (profesor y ayudantes de ICC4201) entrarán al mismo curso demo cada uno con su propio gmail, lo que exige que al menos la incorporación de co-profesores funcione en la parcial?

- **Requisitos:** R2.1.7, R2.1.8, R2.1.9
- **Área declarada:** proceso
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Determina el alcance de la parcial y si el link entregado por Canvas debe permitir a varios evaluadores operar sobre el mismo curso.
- **Estudio de APIs:** §13 (plan y guion de demo) no incluye co-profesores ni ayudantes; §3.1 del enunciado dice que el link debe poder ser utilizado por ayudantes y el profesor.

### P783. ¿Se diseña y migra el esquema COMPLETO (incluidos snapshots, commits, agregados, membresías temporales, outbox y corrección) antes del 16-sep aunque solo se implementen 2.1–2.3, para evitar migraciones destructivas sobre los datos de la demo que seguirán vivos hasta la final? ¿Qué tablas y columnas se declaran congeladas tras la parcial y cuál es la política para renombrar o eliminar columnas después (expand–contract, migraciones solo aditivas)?

- **Requisitos:** R2.4.5, R2.5.2, R2.7.6
- **Área declarada:** proceso / transversal (modelo de datos)
- **Tipo:** Decisión del equipo · **Entrega:** Parcial (16-sep)
- **Por qué importa:** Determina el orden del trabajo de la primera semana y si el curso demo de la parcial puede reutilizarse en la final sin reseed.
- **Opciones planteadas:**
  - Esquema completo desde el inicio
  - Incremental con migraciones solo aditivas
  - Incremental aceptando reseed en la final
- **Estudio de APIs:** §12 da la arquitectura mínima; §5.2 y §8.3 dan modelos parciales; no aborda la evolución del esquema.
