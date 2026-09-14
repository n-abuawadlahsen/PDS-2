# 5. Integración con Canvas

Este capítulo especifica el cliente técnico que la aplicación usa para hablar con la API de Canvas: qué credencial usa y cómo vive esa credencial a lo largo del tiempo, qué endpoints llama y para qué, cómo y con qué cadencia se sincronizan los datos que Canvas es dueño de tener, cómo se escribe hacia Canvas sin que ninguna vista quede colgada de una llamada externa, cómo se respetan sus límites de tasa, cómo se clasifican y se muestran sus errores, y qué hace la aplicación en cada situación en la que Canvas deja de responder como se espera. Todo lo que sigue está escrito para el rol con el que el equipo opera: **profesor**, nunca administrador de cuenta de la instancia. Ese hecho no es una limitación de esta versión: es la restricción que gobierna cada decisión de este capítulo.

**Requisitos que satisface.** Este capítulo es transversal: no implementa por sí solo ningún requisito de negocio, sino el mecanismo del que dependen otros capítulos para cumplir los suyos. Sostiene la parte técnica de **R2.1.4**–**R2.1.6** (vinculación y verificación, cuyo flujo de pantalla fija §4); la obtención de datos que **R2.2.1**–**R2.2.6** necesitan (roster, secciones, grupos, tarea de registro, cuyo modelo y presentación fija §7); la obtención de fechas que **R2.4.1**–**R2.4.4** necesitan (tareas y *overrides*, cuyo cálculo de fecha efectiva fija §9); el canal de escritura que **R2.6.5**–**R2.6.7** usan para mensajes, comentarios y anuncios (cuyo contenido y cadencia fija §11); y el canal de escritura que **R2.7.6** usa para publicar una nota (cuyo flujo de corrección fija §12). Donde este capítulo cita un endpoint, describe **cómo** se llama y bajo qué contrato; el **qué** se envía y **cuándo** se decide enviarlo es de quien lo cita.

**Restricción que gobierna todo el capítulo.** El equipo tiene rol de **profesor** en la instancia institucional de Canvas, no de administrador de cuenta. En Canvas Cloud las *developer keys* las emite el administrador de la institución, y habilitar *scopes* es capacidad exclusiva de un administrador de cuenta raíz (`Q-infraestructura-08`). Por eso no existe *developer key* propia en el camino que se despliega, no existe `as_user_id` porque exige el permiso «Become other users» (`Q-2.7-49`), no hay informes de cuenta ni acceso garantizado a `sis_user_id`, y la aplicación **no crea cursos en Canvas: los vincula**. Toda decisión de este capítulo que dependiera de un privilegio de administrador de Canvas está mal planteada y queda descartada de antemano (§1.3 de este documento, restricción 1).

---

## 5.1 Cómo leer este capítulo

**Orden de precedencia aplicado, sin excepciones:** `docs/enunciado-proyecto2.md` → actas de reconciliación (`RG-nnn`) → `docs/ARQUITECTURA.md` (`A-nnn`) → respuestas de alcance (`Q-…`). Donde una respuesta de alcance decía una cosa y una regla `RG` la corrige, manda la regla y este capítulo redacta la regla, no la respuesta original.

**Correcciones de precedencia que este capítulo aplica y que conviene tener presentes desde el principio:**

| Punto | Lo que decía la carta (revisión 1 o A-nnn original) | Lo que manda ahora | Fuente |
|---|---|---|---|
| Almacén del presupuesto y del coste medido de Canvas | `sincronizacion.coste`, calculado en el cliente | **Cubo `CANVAS` de la tabla única `presupuesto_api`**, con los mismos cuatro cubos que GitHub | RG-071, A-219 |
| Cuándo un `403` de Canvas es límite de tasa | Se asumía por el código de estado | **Sólo si `X-Rate-Limit-Remaining` cae bajo el 10 % del máximo observado, o el cuerpo contiene literalmente `Rate Limit Exceeded`**; en cualquier otro caso es no transitorio | RG-070 |
| Nombre del subtipo de error cuando el permiso está en verde pero la llamada falla con `401` | `SCOPE_NO_CONCEDIDO` | **`LLAMADA_NO_AUTORIZADA`**, con dos redacciones distintas según la implementación de `ProveedorCredencialCanvas` activa | RG-068 |
| Mecanismo para representar que una capacidad de Canvas dejó de funcionar en caliente | Banderas booleanas sueltas por capacidad | **Mecanismo único de capacidad degradada**: filas `origen = RUNTIME` en `verificacion_vinculacion`, sin tabla ni columna nueva | RG-065, RG-066, A-193 |
| Cuántas llamadas hace `sonda_credencial_canvas` cada 15 minutos | Dos (`GET /users/self`, `GET /courses/:id`) | **Tres**: se añade `GET /courses/:id/enrollments?user_id=self&type[]=TeacherEnrollment` para vigilar también la pérdida del rol y la limitación por sección en caliente | RG-074 |
| Qué endpoints de escritura hacia Canvas se pueden llamar de forma síncrona desde una pantalla | Una lista implícita, contradicha en otro punto por «ninguna vista escribe hacia fuera salvo la nota» | **Lista cerrada de seis, con contrato único**, y la entrada 4 pasa a decir «crear **o restaurar** la tarea de registro» | A-169, A-226, RG-087, RG-083 |

**Explícitamente fuera del alcance de este capítulo, citado y no redefinido aquí:**

| Tema | Dónde vive | Qué cubre este capítulo en su lugar |
|---|---|---|
| Pantallas del asistente de vinculación, sus cuatro pasos y el checklist de 21 códigos | §4 «Vinculación» | Qué endpoint respalda cada comprobación del checklist, y el contrato de las escrituras síncronas que el asistente dispara |
| Modelo de datos de `estudiante`, `seccion`, `matricula`, `grupo`, `pertenencia_grupo`, `mapeo_github` | §3 «Modelo de datos» y §7 «Estudiantes y grupos» | Los endpoints que alimentan esas tablas y la cadencia con la que se sincronizan |
| Contenido, cadencia y catálogo de comunicaciones automáticas (mensajes, anuncios, recordatorios) | §11 «Informe diario y comunicación» | Los endpoints de mensajería de Canvas y el patrón general de escritura que ese capítulo instancia |
| Flujo de corrección, publicación de nota, contraste con `estado_canvas_submission` | §12 «Corrección» | El patrón general de escritura síncrona (del que «publicar nota» es un caso) y el endpoint que usa |
| Cálculo de la fecha efectiva por `(entrega, sujeto)`, sus cuatro orígenes y sus casos límite | §9 «Entregas, fechas y versiones» | Cómo se obtienen de Canvas las fechas base y los *overrides*, y el mecanismo que detecta que cambiaron |
| Motor genérico de trabajos en segundo plano: la cola en PostgreSQL, las cinco garantías, los espacios de cerrojo, la recuperación de huérfanos | §14 «Infraestructura y despliegue» | La cadencia y el propósito específicos de los trabajos que hablan con Canvas dentro de ese motor |

**Convenciones de escritura que este capítulo hereda y no reabre:**

- Todo instante se almacena en UTC y se presenta en la zona del curso, con formato `dd-MM-yyyy HH:mm` y la zona escrita al lado siempre (A-152).
- Todo estado interno se muestra traducido, con etiqueta fija; nunca aparece un identificador en mayúsculas en pantalla (A-155). Los mensajes de error de Canvas se muestran con su **texto literal** bajo una explicación en español.
- Vocabulario cerrado (A-154, §1.8 de este documento): se dice **sincronización** y **«actualizado hace X»**, nunca *sync*, *refresh* ni *job*.
- **Ley 1 — Espejo, no caché.** Ninguna vista de la aplicación llama a Canvas para renderizarse. Toda lectura de Canvas ocurre dentro de un trabajo en segundo plano y se persiste antes de que cualquier pantalla la muestre (§1.3, Ley 1; A-089).
- **Ley 5 — Un límite de una API externa nunca se pinta como error del equipo.** Se pinta como estado transitorio con la hora de reintento visible (§1.3, Ley 5; A-116). Este capítulo es donde esa ley se implementa para Canvas.

---

## 5.2 La credencial de Canvas y su ciclo de vida

### 5.2.1 Por qué un token de acceso personal y no OAuth2 general

El mecanismo que se implementa y se despliega es el **token de acceso personal generado por el propio profesor** (A-031). El profesor lo genera desde su perfil de Canvas (`/profile/settings` de la instancia) y lo pega en la pantalla de credenciales del curso. No es la opción más cómoda de programar entre dos alternativas equivalentes: es la única que el rol de profesor permite sin depender de un tercero.

La documentación de Canvas es explícita en dos puntos que, juntos, cierran cualquier otra lectura:

1. **Las *developer keys* las emite el administrador de la institución**, y habilitar *scopes* sobre ellas es capacidad exclusiva de un administrador de cuenta raíz (`Q-infraestructura-08`). El equipo no tiene ese rol y no lo va a tener durante la ventana del proyecto.
2. **Pedir a otro usuario que genere un token manualmente y lo introduzca en la aplicación viola la API Policy de Canvas**, que exige que las aplicaciones usadas por múltiples usuarios usen OAuth (`Q-infraestructura-08`). La aplicación respeta esta política sin tener OAuth2 disponible: **nadie pega jamás el token de otra persona** (§5.2.4).

**OAuth2 con *developer key* institucional es un camino alternativo, condicionado y preparado, no el camino principal** (A-032). El acceso a Canvas se abstrae tras la interfaz `ProveedorCredencialCanvas`, con dos implementaciones: `TokenPersonal` (la que se despliega y se demuestra) y `OAuth2DeveloperKey` (esqueleto con canje de código y refresco, escrito y probado en `ensayo`, sin desplegar en `produccion`). Si la universidad concediera una *developer key* institucional, se conmuta por la variable `CANVAS_AUTH` sin tocar el resto del sistema. **Ninguna funcionalidad de este documento depende de que ese camino se active.** El equipo escaló la solicitud por escrito el 10 de septiembre a las 09:00, con fecha límite de respuesta el 12 de septiembre, y el resultado —sea cual sea— se registra en `docs/`.

### 5.2.2 Modelo de datos de la credencial

Dos tablas separan dos cosas distintas: **quién es esta persona en Canvas** (identidad, ligada al usuario de la aplicación y a la instancia) y **con qué credencial escribe la aplicación en Canvas para este curso** (autorización, ligada al curso). `credencial_canvas` es tabla propia de la vinculación, definida y con sus columnas completas en `docs/SPEC/04-vinculacion.md` §4.2.2 — este capítulo la usa sin redefinirla. `identidad_canvas_usuario` se define aquí, porque es de este capítulo:

| Tabla | Columnas | Unicidad | Para qué |
|---|---|---|---|
| `identidad_canvas_usuario` | `id`, `usuario_id`, `canvas_base_url`, `canvas_user_id` (`bigint`), `verificada_en`, `ultima_confirmacion_en` | **(`usuario_id`, `canvas_base_url`)** y **(`canvas_base_url`, `canvas_user_id`)** | Que una persona sea siempre la misma persona de Canvas en una instancia dada, incluso con varios cursos y varias credenciales |

`credencial_canvas.estado ∈ {VALIDA, INVALIDA, RETIRADA}` (§4.2.2). **`usuario.canvas_user_id` no existe**: la identidad se lee siempre de `identidad_canvas_usuario`, nunca de una columna escalar en `usuario` (A-033). **La identidad es de la persona; la autorización de escritura es del curso**: las dos tablas conviven y no se confunden.

**`identidad_canvas_usuario` no es inmutable frente a una fusión de usuarios en Canvas.** `canvas_user_id` puede quedar obsoleto si Canvas fusiona dos cuentas (A-051); cuando eso ocurre, el titular corrige su propia identidad repitiendo el pegado tras confirmar en pantalla el cambio, y la corrección queda en `bitacora`.

### 5.2.3 Las cinco comprobaciones al pegar un token

**Esta sección es la fuente canónica** de esta regla de negocio; `docs/SPEC/04-vinculacion.md` §4.5.2 repite la misma tabla en la narrativa del asistente de vinculación y debe mantenerse idéntica a ésta — cualquier corrección a una comprobación se hace aquí primero.

Toda vez que alguien pega un token —el primer pegado del curso o una credencial de respaldo posterior— se ejecutan, **en este orden y siempre las cinco**, antes de guardar nada:

| # | Comprobación | Llamada | Si falla |
|---|---|---|---|
| 2.a | `GET /api/v1/users/self` responde `200` | — | Se rechaza: el token no sirve |
| 2.b | Ese `id` tiene una **matrícula de profesor activa en el curso de Canvas que se está vinculando** | `GET /courses/:id/enrollments?user_id=self&type[]=TeacherEnrollment` | Se rechaza con «este token pertenece a alguien que no es profesor de ese curso». **Es la comprobación que cierra el hueco de la API Policy**: es la única de las cinco que ya funciona en el primer pegado, cuando todavía no existe ninguna identidad registrada contra la que comparar |
| 2.c | Ese `(canvas_base_url, canvas_user_id)` **no está ya vinculado a otro usuario de la aplicación** | — (contra `identidad_canvas_usuario`) | Se rechaza y se abre incidencia: dos personas distintas no pueden ser la misma persona de Canvas |
| 2.d | Si el usuario **ya tiene** identidad registrada para esa instancia, el `id` devuelto **coincide** con ella | — | Se rechaza. Sólo aplica a partir del segundo pegado en esa instancia |
| 2.e | Si **no la tiene**, se registra ahora como identidad verificada, con `verificada_en` | — | — |

Estas cinco comprobaciones son **la implementación de A-033**: reescriben una comprobación de la revisión 1 que comparaba contra una columna vacía en el primer pegado —y por tanto era vacua exactamente en el único momento en que alguien podría intentar pegar el token de otro— por una que sí funciona desde el primer pegado (2.b) y una identidad propia por instancia (`identidad_canvas_usuario`), en lugar de un escalar único por usuario que no podía representar dos instancias de Canvas distintas.

El formulario de pegado dice explícitamente «pega tu propio token; no pegues el de otra persona», y el botón de envío está deshabilitado hasta marcar una casilla que lo afirma. **Sólo puede usar esta pantalla quien tiene `curso.administrar`**, permiso NO CONCEDIBLE a un ayudante.

### 5.2.4 Credencial operativa y credenciales de respaldo

Un curso designa **una credencial operativa** —la que usan los trabajos de fondo, `orden_respaldo = 0`— y admite credenciales de respaldo de otros profesores del curso, ordenadas por `orden_respaldo` creciente (A-035). Es lo que sostiene **R2.6.5**–**R2.6.7** y **R2.7.6**: si la única credencial se revocara, esos requisitos morirían con ella.

**Cómo se concilia con la API Policy citada en §5.2.1**, porque respaldo no puede significar «alguien pega el token de otro»:

1. **Nadie pega jamás el token de otra persona.** Una credencial de respaldo sólo puede crearla **su propio titular, desde su propia sesión**; la interfaz sólo ofrece «añadir **mi** credencial», y las cinco comprobaciones de §5.2.3 se ejecutan igual.
2. **El titular consiente por escrito y sabe exactamente a qué**, antes de guardar: «con esta credencial la aplicación publicará notas, anuncios, mensajes y comentarios **a tu nombre** en Canvas, incluidos los originados por otros miembros del equipo docente, y podrá hacerlo cuando tú no estés conectado. Puedes retirarla en cualquier momento.» Sin la casilla marcada no se guarda nada, y el consentimiento queda en `bitacora` con fecha (`credencial_canvas.consentimiento_en`).
3. **Cada titular ve y puede retirar lo suyo**: cuántas escrituras se han hecho con su credencial en los últimos 7 días y con qué destino, y el botón «retirar mi credencial», que la pasa a `RETIRADA` y promueve la siguiente del orden.

**Qué orden recibe una credencial nueva no se deja al implementador**, porque de ello depende con qué identidad aparecen firmadas todas las escrituras posteriores en Canvas:

| Situación al pegar | Orden que recibe | Por qué |
|---|---|---|
| **No hay credencial operativa válida** (la de `orden_respaldo = 0` está `INVALIDA` o `RETIRADA`) | `orden_respaldo = 0` de inmediato, desplazando a la inválida al final del orden | El curso está parado y lo urgente es que vuelva a funcionar; se anuncia en pantalla: «a partir de ahora la aplicación escribirá en Canvas como *nombre*» |
| **Hay credencial operativa válida** | `orden_respaldo = max + 1`: entra como respaldo, **no desplaza a nadie** | Cambiar en silencio la identidad con la que se firman las notas sería exactamente el efecto invisible que este documento prohíbe |
| Un profesor quiere **promover** su credencial habiendo otra válida | Acción explícita «hacer operativa la mía», con confirmación que nombra a la persona desplazada, aviso por correo a los profesores del curso y registro en `bitacora` | Es un cambio deliberado de identidad de escritura; se hace a propósito o no se hace |

**La cabecera del curso muestra siempre, en texto, con qué identidad de Canvas escribe la aplicación**, para que nadie tenga que deducirlo (A-036).

### 5.2.5 Cifrado y llavero versionado

El token se cifra con **AES-256-GCM**, con *nonce* aleatorio por fila y el `curso_id` como *additional authenticated data*, de modo que una fila cifrada **no puede reutilizarse en otro curso**. **Nunca se guarda en claro.** **Ninguna ruta de la API devuelve jamás un secreto**: la interfaz muestra únicamente la huella (`sha256` truncado, guardada en `credencial_canvas.huella`), el nombre del titular, el estado y la fecha de la última validación con éxito (A-034, A-191).

**La clave no es una: es un llavero versionado** (A-191, RG-138), gobernado por las variables `APP_ENCRYPTION_KEYS` (mapa de versión a clave de 32 bytes) y `APP_ENCRYPTION_KEY_ACTIVA` (la versión con la que se **cifra**); `credencial_canvas.version_clave` guarda la versión con la que se **descifra** esa fila. El arranque falla si la versión activa no está en el llavero. La rotación es en línea y reanudable: se añade la clave nueva, se cambia la versión activa, y el **recifrado perezoso** reescribe cada fila la próxima vez que la sonda periódica (§5.2.6) la valida, de modo que un ciclo migra todas. El mecanismo de rotación en sí —custodia, calendario, `/operacion`— es de `docs/SPEC/14-infraestructura-y-despliegue.md` §14.6.4; aquí sólo se fija que el token de Canvas es el dato que ese mecanismo protege, y que **es el único secreto que se persiste** en toda la aplicación (A-176).

**Detección de huella repetida entre cursos.** Como se guarda la huella, la aplicación detecta y advierte —sin llegar a impedirlo— si el mismo token se pegó en dos cursos distintos, porque es legítimo que un profesor use el mismo token en dos cursos suyos. La pantalla recomienda generar un token distinto por curso, con un propósito escrito en Canvas, para que revocar uno no afecte al otro.

### 5.2.6 Sonda periódica de la credencial

El trabajo `sonda_credencial_canvas` corre **cada 15 minutos, por curso**, bajo el cerrojo de Canvas del curso (§5.6.1), y ejecuta **tres** llamadas, no dos (RG-074, que corrige a A-037):

1. `GET /api/v1/users/self` — el token sigue siendo válido.
2. `GET /api/v1/courses/:id` — el curso de Canvas sigue accesible (§5.8).
3. `GET /api/v1/courses/:id/enrollments?user_id=self&type[]=TeacherEnrollment` — el titular **conserva** la matrícula de profesor y **no** está limitado a una sección.

Detectar la revocación o la pérdida del rol antes de que la note un envío fallido es lo que permite avisar en lugar de fallar. El resultado alimenta `credencial_canvas.estado`, `ultimo_chequeo_en` y `GET /estado`. Los dos desenlaces de la tercera llamada están descritos en §5.8 (matrícula perdida, matrícula limitada a sección).

### 5.2.7 Revocación, expiración y degradación controlada

Ante un `401` de Canvas, o un `403` no transitorio (§5.6.4) repetido **tres veces consecutivas** —contador `credencial_canvas.fallos_403_consecutivos`, que cualquier `2xx` de Canvas para ese curso pone a cero (RG-070)—:

1. La credencial pasa a `INVALIDA` de inmediato; el curso pasa a `CANVAS_DESVINCULADO`; se abre la incidencia `CANVAS_CREDENCIAL_INVALIDA`.
2. **Se promueve automáticamente la primera credencial de respaldo válida**, si existe. Si funciona, el resto de pasos no ocurre y queda registrado en `bitacora`.
3. **Los trabajos de lectura de Canvas se detienen** —no tiene sentido sincronizar contra datos que no se pueden leer— y **los trabajos de escritura se encolan, no se descartan**: publicaciones de nota, anuncios, mensajes y comentarios quedan en `trabajo` con estado `ESPERANDO_CREDENCIAL`.
4. **Lo que no depende de Canvas no se detiene**: aprovisionamiento, ingesta de actividad de GitHub, tableros, *timeline* y **captura de versiones**, porque las fechas efectivas ya están persistidas y **R2.4.5** no puede depender de que Canvas esté accesible en ese instante exacto.
5. Todo el curso muestra una **banda roja persistente** con el texto exacto de qué falta, quién puede arreglarlo y el enlace a la pantalla de sustitución. Se envía correo a todos los profesores del curso.
6. **Cualquier profesor del curso** —no sólo el titular original— puede pegar **su propia** credencial nueva, con el orden que recibe fijado por la tabla de §5.2.4. Al validarse, los trabajos encolados se reanudan en orden, respetando la idempotencia del *outbox* para no duplicar mensajes.
7. Si el titular **perdió el rol de profesor en Canvas** (matrícula ausente), la validación falla al comprobar el curso y no al comprobar el usuario; el mensaje distingue los dos casos porque la acción correctiva es distinta.

(A-036, con el contador de fallos consecutivos corregido por RG-070.)

**Cambiar la credencial operativa invalida el checklist de vinculación en la parte de Canvas y lo reencola**, porque un permiso verificado con un token ya no dice nada del token nuevo. Esta invalidación cae sobre los diecisiete ítems numerados de Canvas del checklist —los 19 numerados menos el 14 y el 18, que son de GitHub y no se tocan— más las dos pruebas de escritura `5-bis` y `17-bis`, diecinueve filas de `verificacion_vinculacion` en total, y también sobre las filas `origen = RUNTIME` de capacidad `CANVAS`; el mecanismo completo de ese reencolado, incluida la banda ámbar que lo anuncia, es de §4 (RG-069).

### 5.2.8 Varias instancias de Canvas

La aplicación soporta **varias instancias de Canvas** simultáneamente, elegidas de una **lista blanca configurable por entorno**, no de un campo libre y no de una constante fija:

- `curso.canvas_base_url` es un campo real por curso (índice único junto con `canvas_course_id`), normalizado al guardarse: esquema `https`, host en minúsculas, sin barra final.
- La lista de instancias admitidas vive en la variable de entorno `CANVAS_INSTANCIAS`, un JSON con `base_url`, `nombre_visible` y, sólo para el camino alternativo de §5.2.1, `oauth_client_id` y `oauth_client_secret`. **No existe ninguna tabla de instancias en la base de datos**: sería una entidad para una funcionalidad que hoy no cambia por curso más que en ese campo.
- El paso de vinculación —en §4— presenta la instancia institucional preseleccionada.

**Guarda de seguridad, no una convención**: el proceso comprueba al arrancar que la `CANVAS_BASE_URL` de `ensayo` **no coincide** con la de `produccion`, y **si coincide, el proceso no arranca** (`docs/SPEC/14-infraestructura-y-despliegue.md` §14.4).

### 5.2.9 Camino condicionado: OAuth2 con *developer key*

`OAuth2DeveloperKey` existe como implementación completa de `ProveedorCredencialCanvas` —canje de `code`, refresco de token, callback `GET /api/canvas/oauth/callback`—, escrita y probada, **no desplegada en producción**. Si la universidad concediera una *developer key* institucional, la lista congelada de *scopes* que esa *key* pediría es exactamente el catálogo de §5.3: 19 lecturas y 6 escrituras, 25 en total, cada una respaldada por una llamada real que este capítulo enumera. **Ningún *scope* se pide «por si acaso»**: añadir uno después de emitida la *key* obliga a reautorizar, así que la lista se congela con la petición.

**Qué pasa si falta un *scope*, en el camino condicionado.** Canvas responde `401` cuando el *scope* del endpoint solicitado no fue concedido. La aplicación no lo trata como credencial inválida a secas: es un `401` de familia PERMANENTE con `detalle.motivo = SCOPE_FALTANTE` y el endpoint literal que falló, sin añadir ningún tipo al catálogo cerrado de incidencias (`detalle` es `jsonb`), con el mensaje literal de Canvas bajo una explicación en español, y **detiene sólo la familia de trabajos que necesita ese endpoint**, nunca el curso entero.

**El mismo `401` con permiso en verde tiene dos redacciones distintas**, según qué implementación de `ProveedorCredencialCanvas` esté activa (RG-068):

| Implementación activa | Texto mostrado, con el cuerpo literal de Canvas debajo |
|---|---|
| `TokenPersonal` (la desplegada, A-031) | «Canvas ha rechazado esta llamada con `401` aunque tu cuenta tiene el permiso. No es tu contraseña ni el curso: la instancia no autoriza esta operación con este token. Genera un token nuevo desde tu perfil de Canvas y vuelve a pegarlo; si vuelve a ocurrir, consúltalo con la administración de Canvas.» **Nunca se nombra una *developer key***, porque en este camino no existe |
| `OAuth2DeveloperKey` (esqueleto, no desplegada) | «El token fue emitido por una clave de Canvas con permisos limitados y esta llamada no está autorizada. Esto no se arregla desde el curso: sólo un administrador de la cuenta puede habilitar el permiso de la clave.» |

### Criterios de aceptación de 5.2

1. Pegar un token cuyo `GET /api/v1/users/self` no responde `200` se rechaza sin escribir ninguna fila en `credencial_canvas` ni en `identidad_canvas_usuario`.
2. Pegar el token de alguien sin matrícula de profesor activa en el curso que se está vinculando se rechaza con el mensaje literal de la comprobación 2.b, incluso cuando es el **primer** pegado del curso.
3. Insertar directamente en la base una segunda fila con `orden_respaldo = 0` para el mismo curso falla por el índice único parcial.
4. Ante tres `403` no transitorios consecutivos de Canvas para un curso con una sola credencial, ésta pasa a `INVALIDA`, el curso a `CANVAS_DESVINCULADO`, y un `push` a un repositorio de ese curso durante la ventana de caída sigue generando actividad ingerida en el espejo.
5. Con dos credenciales válidas, pegar una tercera no cambia `orden_respaldo = 0` de la existente.
6. Ninguna respuesta de ninguna ruta de la API contiene el valor descifrado del token: prueba automatizada sobre los esquemas de salida.
7. Arrancar el backend con `APP_ENCRYPTION_KEY_ACTIVA` ausente del llavero falla el arranque con el nombre de la variable en el error.
8. Cambiar la credencial operativa de un curso deja las diecinueve filas de Canvas de `verificacion_vinculacion` (los diecisiete ítems numerados más `5-bis` y `17-bis`) en `NO_VERIFICADO` con motivo `CREDENCIAL_CAMBIADA` en la misma transacción.

---

## 5.3 Catálogo de endpoints de la API de Canvas

Estos son **todos** los endpoints de la API de Canvas que `ClienteCanvas` invoca, y ninguno más: la lista está congelada como el catálogo que respaldaría la petición de *scopes* de §5.2.9, y es también el inventario contra el que una prueba automatizada contrasta cada llamada real del cliente (`SCOPES_CANVAS`, en `backend/app/infraestructura/`), de modo que un endpoint nuevo sin pasar por este catálogo falla la construcción.

### 5.3.1 Lecturas (19)

| # | Endpoint | Para qué lo usa la aplicación | Cita |
|---|---|---|---|
| 1 | `GET /api/v1/users/self` | Validar el token al pegarlo y en cada ciclo de la sonda | A-033, A-037 |
| 2 | `GET /api/v1/courses` | Listar los cursos donde el titular del token es profesor, en el paso de vinculación | §4 (A-040) |
| 3 | `GET /api/v1/courses/:id` | Validar que el curso existe, está publicado y es accesible; sonda periódica | A-037, §4 |
| 4 | `GET /api/v1/courses/:course_id/permissions` | Comprobaciones de permisos del checklist de vinculación | §4 |
| 5 | `GET /api/v1/courses/:course_id/enrollments` | Comprobación 2.b de identidad; lectura del roster; detección de limitación por sección | §5.2.3, §5.4.3, §5.8 |
| 6 | `GET /api/v1/courses/:course_id/sections` | Sincronización de secciones; detección de *cross-listing* | §7 |
| 7 | `GET /api/v1/courses/:course_id/group_categories` | Sincronización de conjuntos de grupos | §7 |
| 8 | `GET /api/v1/group_categories/:group_category_id/groups` | Sincronización de grupos | §7 |
| 9 | `GET /api/v1/groups/:group_id/memberships` | Sincronización de integrantes de grupo, con `workflow_state` | §7 |
| 10 | `GET /api/v1/courses/:course_id/late_policy` | Política de entrega tardía, precondición de publicación de nota | §12 |
| 11 | `GET /api/v1/courses/:course_id/grading_periods` | Períodos de calificación abiertos, precondición de publicación de nota | §12 |
| 12 | `GET /api/v1/courses/:course_id/assignments` | Aceleración: qué tareas de Canvas existen y qué cambió | §5.4.3, §9 |
| 13 | `GET /api/v1/courses/:course_id/assignments/:id` | Detalle de una entrega vinculada individual | §9 |
| 14 | `GET /api/v1/courses/:course_id/assignments/:assignment_id/overrides` | **Fuente autoritativa de fechas**: fija el valor de la fecha efectiva | §5.4.3, §9 |
| 15 | `GET /api/v1/courses/:course_id/assignments/:assignment_id/gradeable_students` | Pre-chequeo de quién es calificable antes de publicar | §12 |
| 16 | `GET /api/v1/courses/:course_id/students/submissions` | Recolección de la tarea de registro; contraste de notas; botón «comprobar contra Canvas» | §7, §12 |
| 17 | `GET /api/v1/courses/:course_id/rubrics/:id` | Lectura en vivo de la rúbrica en la pantalla de corrección | §12 |
| 18 | `GET /api/v1/search/recipients` | Contraste de destinatarios válidos antes de un envío masivo | §11 |
| 19 | `GET /api/v1/courses/:course_id/discussion_topics` | Localizar y limpiar el anuncio de la prueba de escritura del checklist | §4 |

### 5.3.2 Escrituras (6)

Estas seis son exactamente las que alimentan la lista cerrada de escrituras síncronas de §5.5.1; ningún otro endpoint de escritura de Canvas existe en el código.

| # | Endpoint | Para qué lo usa la aplicación | Cita |
|---|---|---|---|
| 20 | `POST /api/v1/courses/:course_id/assignments` | Crear la tarea de registro «Registro de tu cuenta de GitHub» | §7 (A-144) |
| 21 | `PUT /api/v1/courses/:course_id/assignments/:id` | **Sólo** sobre dos rutas nombradas: restaurar la configuración de la tarea de registro (`:aid = curso.canvas_assignment_id_registro`), y el ajuste consentido de `submission_types` de una entrega ante la contingencia de A-143 | §7, §12 |
| 22 | `POST /api/v1/courses/:course_id/discussion_topics` | Anuncio de la prueba de escritura del checklist; anuncios de comunicación | §4, §11 |
| 23 | `DELETE /api/v1/courses/:course_id/discussion_topics/:topic_id` | Borrar el anuncio de la prueba de escritura tras verificar | §4 |
| 24 | `POST /api/v1/conversations` | Mensaje directo al estudiante (canal 1 de comunicación) | §11 |
| 25 | `PUT /api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id` | Nota, rúbrica y comentario de una entrega **en una sola petición**; y, con sólo `comment[text_comment]`, comentario de vuelta (canal 2 de comunicación, respuesta a la tarea de registro) | §7, §11, §12 |

**Prueba de arquitectura obligatoria: `PUT /courses/:course_id/assignments/:id` (endpoint 21) está prohibido en cualquier sitio de llamada que no sea uno de los dos nombrados arriba**, y falla la construcción si aparece en un tercero. La aplicación **no modifica ningún otro campo de un `assignment` de Canvas vinculado a una entrega**: en particular, no existe ninguna escritura de `assignment[grade_group_students_individually]`; ese campo se **lee** en `sync_tareas_y_fechas` y se persiste, y su efecto en la publicación de nota se deriva, nunca se fuerza (RG-082).

### Criterios de aceptación de 5.3

1. Una prueba automatizada recorre `ClienteCanvas` y falla la construcción si alguna llamada real usa un endpoint que no figura en este catálogo de 25.
2. `PUT /courses/:course_id/assignments/:id` aparece en el código únicamente en los dos sitios de llamada nombrados en §5.3.2, con la comprobación de `:aid` en tiempo de ejecución; una tercera aparición falla la construcción.
3. No existe en el código ninguna llamada a `PUT /courses/:course_id/assignments/:id` con el campo `grade_group_students_individually`.
4. El catálogo de 25 endpoints coincide, uno a uno, con la lista `SCOPES_CANVAS` de `backend/app/infraestructura/`.

---

## 5.4 Mecanismo de sincronización: *polling*, no *webhooks*

### 5.4.1 Por qué no hay un receptor de eventos de Canvas

La aplicación **no recibe ningún evento empujado por Canvas**. La lista cerrada de rutas de infraestructura del backend contiene exactamente un receptor de *webhooks*, `POST /webhooks/github`, y ninguno equivalente para Canvas (`docs/SPEC/14-infraestructura-y-despliegue.md` §14.2.4); el catálogo cerrado de 31 trabajos periódicos de ese mismo capítulo (§14.7.4) implementa **toda** la sincronización con Canvas mediante trabajos que preguntan con una cadencia fija, nunca mediante un evento que Canvas empuje. Esto no es una limitación de implementación: configurar un flujo de eventos de curso hacia un tercero en Canvas —lo más cercano es la exportación de *Live Events* a nivel de cuenta— es, otra vez, una capacidad de administrador de cuenta, y por la restricción de §1.3 el equipo no la tiene ni la va a tener. **El mecanismo de sincronización con Canvas es *polling*, con cadencias distintas por tipo de dato, y es la única vía posible bajo rol de profesor.**

Esta es la razón por la que, a diferencia de GitHub —donde el *push* llega por *webhook* en segundos y la reconciliación periódica es una red de seguridad (Ley 1, `docs/SPEC/14-infraestructura-y-despliegue.md`)—, para Canvas **el trabajo periódico no es una red de seguridad: es el único mecanismo que existe**. La cadencia de cada trabajo (§5.4.3) es, por tanto, el techo de frescura real del dato correspondiente, y cada pantalla que muestra un dato traído de Canvas lo declara con su propio sello de antigüedad, nunca con un número escrito a mano (A-231).

### 5.4.2 Paginación

**Se sigue siempre el header `Link`, nunca se calculan páginas.** La documentación de Canvas prescribe tratar esas URLs como opacas y comprobar siempre el `Link` (`Q-2.2-41`). Se envía `per_page=100` como valor de partida, pero **el cliente jamás asume que recibió 100**: mide `len(json)` en la primera llamada de cada recurso y lo persiste en `cursor_sincronizacion.per_page_medido`. **El número 100 no se escribe como hecho en ninguna parte de esta especificación.**

**Tope de seguridad de 50 páginas por llamada.** Al alcanzarlo, la sincronización **no falla**: cierra el ciclo, registra `sincronizacion.resultado = TRUNCADA`, deja el cursor donde estaba, abre la incidencia `ROSTER_TRUNCADO` (o la que corresponda al recurso) y continúa en el ciclo siguiente. Nunca se cuelga un trabajo por un curso anómalo, y nunca se pierde una página en silencio.

**Detección de bucle**: si la URL de `next` se repite, o una página vuelve vacía con `next` presente, se corta con incidencia — defensa contra un `Link` mal formado.

El iterador es **propio, uno solo, compartido por el cliente de Canvas y el de GitHub** (`adaptadores/paginacion.py`), no una librería de terceros: `octokit.paginate` no existe en el *stack* (el backend es Python) y un envoltorio de Canvas ocultaría las cabeceras `X-Request-Cost` y `X-Rate-Limit-Remaining` que el presupuesto medido de §5.6.2 necesita leer de cada respuesta.

Tabla `cursor_sincronizacion (id, curso_id, recurso, referencia, etag, ultimo_head_sha, per_page_medido, ultimo_exito_en, ultimo_backfill_en, estado, ultimo_error)`, único `(curso_id, recurso, referencia)`.

### 5.4.3 Cadencias de sincronización con Canvas

Los mecanismos genéricos de todo trabajo periódico —la cola en PostgreSQL, las cinco garantías compartidas, la recuperación de huérfanos, el catálogo cerrado de 31— son de `docs/SPEC/14-infraestructura-y-despliegue.md` §14.7; esta tabla lista **sólo** los trabajos que hablan con Canvas, su cadencia y qué sincronizan:

| Trabajo | Cadencia | Qué trae de Canvas |
|---|---|---|
| `sonda_credencial_canvas` | 15 min | Validez del token, del curso y de la matrícula de profesor (§5.2.6) |
| `sync_roster` | 10 min | Roster: `GET .../enrollments?type[]=StudentEnrollment` (endpoint 5) |
| `sync_grupos` | 10 min | Conjuntos de grupos, grupos y pertenencias (endpoints 7, 8, 9) |
| `sync_tareas_y_fechas` | 5 min; **1 min en las 2 h previas a un cierre** | Tareas y *overrides* (endpoints 12, 14), disparado por huella (§5.4.4) |
| `recolector_mapeos` | 3 min con la tarea de registro abierta; 15 min si no; volcado completo cada hora | Entregas de la tarea de registro (endpoint 16) |
| `materializar_sujetos` | tras cada `sync_*` y barrido cada 5 min | No llama a Canvas directamente: recalcula sobre lo que los anteriores dejaron |
| `ejecutar_checklist_vinculacion` | bajo demanda | Las llamadas de verificación del checklist (§4) |
| `revalidar_mapeos` | diario 04:00 | No llama a Canvas: revalida cuentas de GitHub |
| `comunicaciones_programadas` | 5 min | No lee Canvas; **escribe** por los endpoints 22 y 25 |
| `informe_diario` | 07:00 en la zona del curso | No llama a Canvas: lee el espejo |
| `reconciliar_notas_canvas` | inmediata al entrar en ventana de corrección; cada 30 min dentro de ella; 1 vez al día fuera; nunca en tarea archivada | Estado de las *submissions*: `GET .../students/submissions` (endpoint 16), `GET .../gradeable_students` (endpoint 15) |

**El trabajo `materializar_sujetos` toma el mismo cerrojo de Canvas que los `sync_*`** (§5.6.1), aunque no llame directamente a la API, precisamente para no correr en paralelo con ellos sobre el mismo curso.

Todas las cadencias, los espacios de cerrojo, las claves de idempotencia y las fechas de entrada en servicio de estos once trabajos están fijadas en el catálogo cerrado de `docs/SPEC/14-infraestructura-y-despliegue.md` §14.7.4; esta tabla es un resumen orientado a qué dato de Canvas alimenta cada uno.

### 5.4.4 Disparador de resincronización de fechas: una huella, no una marca de tiempo

`sync_tareas_y_fechas` **no** decide si algo cambió comparando `assignment.updated_at` contra la última vez vista. La documentación de Canvas describe `updated_at` como «la hora a la que la tarea fue modificada de cualquier forma», sin aclarar si crear, editar o borrar un *override* cuenta como modificar la tarea, y el objeto `AssignmentOverride` no expone ningún timestamp propio. Si la respuesta fuera que no la toca, una extensión concedida a un estudiante concreto sería invisible para el sincronizador y **R2.4.3** quedaría incumplido en silencio, que es la peor forma de incumplir un requisito.

En su lugar: en cada ciclo se recupera el conjunto completo de reglas de fecha de cada entrega (fecha base más todos los *overrides*), se normaliza y ordena canónicamente, se calcula un **SHA-256** (`entrega.huella_fechas`) y se compara con el almacenado. Si difiere, se recalculan las fechas efectivas y se reprograma lo que dependa de ellas. Cuesta una comparación de 32 bytes y es inmune al supuesto no documentado sobre `updated_at`. El cálculo de la fecha efectiva a partir de estas reglas —los cuatro orígenes, la prioridad entre ellos, los casos límite— es de §9 «Entregas, fechas y versiones»; este capítulo fija únicamente cómo se detecta que hay que volver a calcularla.

### Criterios de aceptación de 5.4

1. No existe en el código ningún receptor de eventos entrantes de Canvas: una búsqueda de rutas `POST` bajo un prefijo `/webhooks/canvas` o equivalente no encuentra nada, y la lista cerrada de rutas sin sesión de `docs/SPEC/14-infraestructura-y-despliegue.md` §14.2.4 no contiene ninguna.
2. Una respuesta de `GET .../enrollments` con menos de 100 elementos no hace que el cliente asuma que hay más páginas ni que no las hay: sigue exclusivamente el header `Link`.
3. Forzando una respuesta con 51 páginas en una prueba, la sincronización cierra el ciclo con `resultado = TRUNCADA`, abre incidencia y el cursor queda en la última página completa procesada.
4. Editando en Canvas un *override* de sección sin tocar la fecha base de la tarea, `entrega.huella_fechas` cambia en el siguiente ciclo de `sync_tareas_y_fechas` y se recalculan las fechas efectivas de los sujetos de esa sección.
5. `materializar_sujetos` nunca se observa ejecutándose al mismo tiempo que `sync_roster` o `sync_grupos` del mismo curso, comprobado con el registro de toma de cerrojos.

---

## 5.5 Escrituras en Canvas: el patrón único

### 5.5.1 Las seis escrituras síncronas y su contrato

**Toda escritura hacia Canvas que un usuario de la aplicación dispara desde una pantalla sigue uno de dos caminos, y sólo dos**: la lista cerrada de seis escrituras síncronas, o el *outbox* asíncrono (`mensaje_saliente`, despachado por `despachar_outbox`). **Cualquier otra escritura externa disparada desde una vista es un defecto de arquitectura y se rechaza en revisión de código** (A-169, Ley 1).

La diferencia entre las dos vías no es técnica, es de destinatario: una **comunicación** —mensaje, anuncio, comentario automático— tiene como destinatario a un tercero que no está mirando la pantalla en ese instante, así que puede reintentarse sin que nadie espere, y por eso va **siempre** por el *outbox*. Una **acción del docente sobre su propio curso** —crear la tarea de registro, publicar una nota— tiene como destinatario al propio profesor, que está esperando el resultado en pantalla, y por eso es **síncrona con contrato** (A-125, A-226).

| # | Escritura | Endpoint | Pantalla | Por qué tiene que ser síncrona |
|---|---|---|---|---|
| 1 | Prueba de escritura: crear y borrar el anuncio `[verificación app]` | 22, 23 | Asistente, §4 | El profesor acaba de marcar la casilla y el checklist tiene que ponerse verde delante de él |
| 2 | Crear el repositorio base (GitHub, no es de este capítulo) | — | Tarea → repositorio base | — |
| 3 | Subir, reemplazar o borrar un archivo del repositorio base (GitHub, no es de este capítulo) | — | Tarea → repositorio base → archivos | — |
| 4 | **Crear o restaurar** la tarea de registro en Canvas | 20, 21 | §7 (Personas) | El profesor revisa el enunciado, pulsa publicar y tiene que ver el enlace a la tarea creada para comprobarla en Canvas |
| 5 | Publicar una nota | 25 | §12 (Corrección) | Es la acción explícita del corrector, con relectura inmediata y resultado en pantalla |
| 6 | Validar un login de GitHub (lectura, no escritura de Canvas) | — | Pendientes | — |

Sólo las entradas 1, 4 y 5 tocan la API de Canvas; las entradas 2, 3 y 6 tocan GitHub o son lecturas, y su contrato específico se documenta en el capítulo que las posee. **Las seis comparten el mismo contrato, sin excepciones:**

1. **Lectura antes del efecto**: se comprueba si el efecto ya existe antes de producirlo, para que reintentar no duplique.
2. **Intención persistida antes de la llamada**, en la misma transacción, para que un proceso que muere a mitad deje rastro y no un hueco.
3. **Tiempo de espera duro de 20 segundos.** Si se agota, la operación **no se pierde**: se convierte en un trabajo de la cola, la pantalla lo dice con esas palabras y muestra dónde seguirla. Es la única forma de que una llamada lenta a Canvas no bloquee la interfaz.
4. **El resultado se muestra en pantalla**, con el error literal de Canvas si lo hubo.
5. **Queda en `bitacora`** como cualquier otra escritura externa.
6. **Ninguna de las seis envía una comunicación a un estudiante.** Si una acción síncrona debe además avisar a alguien, el aviso entra en el *outbox*: la escritura es síncrona, el aviso nunca lo es.

**La lista es cerrada y no crece**: todo endpoint nuevo de escritura hacia Canvas que se añada en el futuro **encola** un trabajo y no llama al proveedor dentro de la petición HTTP; los ejemplos actuales de ese patrón son `POST /api/cursos/{id}/verificacion` (encola `ejecutar_checklist_vinculacion`) y `POST /api/cursos/{id}/registro-github/restaurar` cuando no se toma el camino síncrono. Una prueba de arquitectura falla la construcción si un manejador de `backend/app/api/` invoca `ClienteCanvas` desde un sitio que no es una de las tres entradas síncronas de Canvas de la tabla de arriba (A-226, RG-087).

### 5.5.2 Firma de autoría: por qué toda escritura aparece firmada por el titular del token, y cómo se compensa

**Toda escritura en Canvas —nota, rúbrica, anuncio, mensaje, comentario— aparece firmada por el profesor titular de la credencial operativa, sea quien sea el ayudante o profesor que la originó.** No hay forma de evitarlo: `as_user_id` es el parámetro que permitiría que la aplicación actuara «como» otro usuario de Canvas, y exige el permiso «Become other users», exclusivo de un administrador de cuenta (`Q-2.7-49`). No es un defecto de esta implementación: es una consecuencia directa del rol de profesor, se declara en la interfaz y se compensa en **tres lugares**, como decisión de diseño y no como parche (A-142):

1. **La aplicación guarda en `correccion` y en `bitacora` quién corrigió realmente y quién pulsó el botón**, distintos de `grader_id`.
2. **Se añade al comentario de la entrega, dentro de Canvas, una línea final** con el nombre de quien originó la acción y la fecha: «Corregido por Ana Pérez (ayudante). Publicado por el sistema de gestión del curso.» Así la información existe también donde la buscaría quien no usa la aplicación.
3. **La pantalla de la acción lo dice explícitamente antes de confirmar**, para que nadie se sorprenda con el resultado.

Que `grader_id` valga exactamente el identificador del titular del token es una inferencia por eliminación, no una frase documentada por Canvas; se registra lo que Canvas devuelva en el campo correspondiente y se contrasta contra la identidad esperada.

Este mismo patrón —escritura firmada por el titular, autoría real conservada aparte, y una línea de trazabilidad dentro del propio objeto de Canvas cuando el canal lo permite— es el que cualquier capítulo que dispare una escritura hacia Canvas debe replicar; no se redefine caso por caso.

### Criterios de aceptación de 5.5

1. Una prueba de arquitectura falla la construcción si un manejador de `backend/app/api/` invoca `ClienteCanvas` desde fuera de las tres entradas síncronas de Canvas de §5.5.1.
2. Publicar una nota cuyo `PUT .../submissions/:user_id` tarda más de 20 segundos deja la operación como un trabajo en cola visible desde la pantalla de corrección, en vez de perder el resultado.
3. Crear la tarea de registro dos veces seguidas (doble clic) no produce dos tareas en Canvas: la segunda lectura previa encuentra la primera.
4. Toda fila de `publicacion_nota` y todo comentario escrito en una entrega por la aplicación puede resolverse, vía `correccion` y `bitacora`, al usuario real que la originó, aunque el `grader_id` de Canvas apunte al titular del token.
5. Ninguna de las seis escrituras síncronas de §5.5.1 tiene una llamada a `mensaje_saliente` en su mismo manejador: cualquier aviso que acompañe a la acción se encuentra en el *outbox*.

---

## 5.6 Límites de tasa, presupuesto medido y resiliencia

### 5.6.1 Concurrencia: una petición simultánea por curso

**Contra Canvas rige una sola petición simultánea por curso.** Todo trabajo que hable con Canvas toma `pg_advisory_lock(1, curso_id)` alrededor de sus llamadas a Canvas, y sólo alrededor de ellas: el mismo trabajo libera ese cerrojo antes de tomar el de GitHub si necesita los dos, y nunca retiene uno mientras espera al otro (`docs/SPEC/14-infraestructura-y-despliegue.md` §14.7.3; A-039, A-217, RG-062). La documentación de Canvas respalda esta elección: un cliente que no hace más de una petición simultánea es improbable que sea limitado, y las peticiones paralelas sufren una penalización previa. **Paralelizar contra Canvas perjudica a la aplicación; no se hace.**

El cerrojo, no un límite de tasa medido, es lo que serializa a Canvas: el presupuesto medido de §5.6.2 decide **cuándo** el trabajo con el cerrojo tomado debe esperar, no si puede correr en paralelo con otro.

### 5.6.2 Presupuesto medido: el cubo `CANVAS`

**Todo límite de tasa observado, de cualquier proveedor, vive en una sola tabla, `presupuesto_api`, con cuatro cubos** (RG-071, A-219; corrige a A-039/A-117, que calculaban el margen en el propio cliente). Uno de los cuatro cubos es de Canvas:

| Cubo | Ámbito | Fuente de capacidad y recarga | Consumidores |
|---|---|---|---|
| `CANVAS` | `CANVAS_CURSO` (el `curso_id`) | `X-Request-Cost` y `X-Rate-Limit-Remaining` de cada respuesta de Canvas | Todas las llamadas de `ClienteCanvas` |

`presupuesto_api (id, ambito, ambito_id, cubo, tokens, capacidad, recarga_por_minuto, ultima_recarga_en, limite_observado, restante_observado, reset_observado_en, actualizado_en)`, único `(ambito, ambito_id, cubo)`. **El objetivo autoimpuesto es el mismo para los cuatro cubos: no bajar del 50 % del límite real medido en la hora**, y por debajo del **20 %** sólo circulan las llamadas de máxima prioridad. `ClienteCanvas` toma y devuelve fichas del cubo `CANVAS` **en el mismo punto de salida en que clasifica los errores** (§5.6.3). El máximo observado por curso se lee de esta tabla, nunca de un cálculo propio del cliente.

`/operacion` muestra los cuatro cubos, el de Canvas incluido, con la misma tarjeta, el mismo margen y la misma antigüedad, como secciones de curso (`docs/SPEC/14-infraestructura-y-despliegue.md` §14.7, §14.9).

### 5.6.3 Clasificación de errores en tres familias

Todo error que `ClienteCanvas` recibe se clasifica en una de tres familias, y la familia decide el comportamiento **y decide lo que ve el docente** (A-116, §1.3 de este documento, Ley 5):

| Familia | Ejemplos en Canvas | Comportamiento | Qué ve el docente |
|---|---|---|---|
| **TRANSITORIO** | `429`; `5xx`; tiempo de espera agotado; `403` clasificado como límite de tasa (§5.6.4) | Retroceso exponencial con *jitter* (base 2 s, factor 2, tope 5 min, 6 intentos), hasta el tope del trabajo | «Reintentando, próximo intento a las HH:MM» |
| **BLOQUEANTE** | `401`, o `403` no transitorio, con la sonda de credencial en verde: se clasifica `LLAMADA_NO_AUTORIZADA` y **sólo degrada la capacidad afectada**, sin invalidar la credencial (§5.7) | Estado `BLOQUEADO` o `ESPERANDO_*`; no se reintenta en bucle; se reevalúa cada 30 minutos o cuando cambia la condición | «Esperando a Canvas por límite de uso. Reintento automático a las HH:MM» / el texto de §5.2.9 según la implementación activa |
| **PERMANENTE** | `422` de validación; `404` fuera de la ventana de creación; período de calificación cerrado; tipo de calificación no admitido | Cero reintentos; estado terminal con motivo y acción sugerida; se guarda el mensaje literal del proveedor | «Requiere tu acción: …», con el texto literal debajo |

**Un límite de la API de Canvas jamás se pinta como error del equipo** (Ley 5). Cuando la sonda de credencial está en verde y una llamada de escritura devuelve `401`, la credencial **no** se invalida: la degradación se acota a la capacidad concreta que falló, por el mecanismo único de §5.7, sin desvincular el curso por un permiso que faltaba en un solo endpoint.

### 5.6.4 El discriminador del `403`

`ClienteCanvas` clasifica cada `403` con un discriminador explícito y único en todo el sistema: es límite de tasa —familia TRANSITORIA, estado `ESPERANDO_LIMITE`, **nunca `ERROR`**— **si y sólo si** la respuesta trae `X-Rate-Limit-Remaining` por debajo del **10 %** del máximo observado para ese curso en `presupuesto_api`, **o** su cuerpo contiene literalmente `Rate Limit Exceeded`. **En cualquier otro caso el `403` es no transitorio**, se muestra con su cuerpo literal, y cuenta para el contador de tres de §5.2.7. Ese contador se pone a cero con cualquier respuesta `2xx` de Canvas para ese curso. El `429` es siempre límite y nunca cuenta para ese contador (RG-070).

Esta regla existe porque tratar todo `403` como límite de tasa escondería un permiso realmente insuficiente detrás de un mensaje de «espera», y tratar todo `403` como error permanente desvincularía un curso por una ráfaga legítima de tráfico. El discriminador es la línea que separa los dos casos con un hecho verificable en la propia respuesta, no con una suposición.

### 5.6.5 Configuración del cliente HTTP

`ClienteCanvas` fija sus tiempos de espera de forma explícita y uniforme, nunca por llamada:

| Ámbito | Valor |
|---|---|
| Conexión | 5 s |
| Lectura, peticiones de lectura | 20 s |
| Lectura, peticiones de escritura | 30 s |
| Agotamiento del *pool* de conexiones | 5 s |

Estos cuatro valores gobiernan cada llamada individual a Canvas; son distintos del tiempo de espera duro de **20 segundos** que envuelve a cada una de las tres escrituras síncronas de §5.5.1 en su conjunto (que puede incluir más de una llamada HTTP, por ejemplo la lectura previa más la creación), y también distintos del presupuesto de la petición web completa que fija `docs/SPEC/14-infraestructura-y-despliegue.md`. Cada respuesta de Canvas registra `X-Request-Cost` y `X-Rate-Limit-Remaining` en el cubo `CANVAS` de `presupuesto_api` (§5.6.2), incluidas las respuestas de error.

**Todos los instantes que Canvas devuelve se tratan como UTC en ISO 8601 con resolución de segundos**, que es el formato documentado. Toda comparación entre un instante de Canvas y uno de GitHub se hace truncada al segundo, porque ninguna de las dos APIs promete milisegundos.

### Criterios de aceptación de 5.6

1. Lanzando a la vez cinco trabajos de Canvas del mismo curso, una prueba automatizada verifica que se serializan y que en ningún instante hay dos peticiones simultáneas a Canvas para ese curso.
2. Un `403` con `X-Rate-Limit-Remaining` al 5 % del máximo observado se clasifica como límite de tasa y el trabajo queda `ESPERANDO_LIMITE`, nunca en un estado que se muestre como error.
3. Un `403` con `X-Rate-Limit-Remaining` al 40 % del máximo observado y sin `Rate Limit Exceeded` en el cuerpo se clasifica como no transitorio, incrementa el contador de fallos consecutivos y se muestra con el cuerpo literal de Canvas.
4. Tres `403` no transitorios consecutivos disparan el procedimiento completo de §5.2.7; un `2xx` intermedio pone el contador a cero y ningún `403` posterior por sí solo dispara ese procedimiento.
5. `/operacion` muestra el cubo `CANVAS` de `presupuesto_api` por curso, con su margen y su antigüedad, y el valor coincide con la última cabecera `X-Rate-Limit-Remaining` recibida para ese curso.
6. Una llamada de lectura a Canvas que no responde en 20 segundos se cancela con tiempo de espera agotado, se clasifica como TRANSITORIO y entra en retroceso exponencial.

---

## 5.7 Mecanismo de capacidad degradada aplicado a Canvas

**Existe un único mapa cerrado**, sin E/S, en `backend/app/dominio/capacidades.py`, que asocia cada capacidad de la aplicación —de Canvas y de GitHub— con su proveedor, el endpoint del que depende, el ítem del checklist que la verifica cuando lo hay, el requisito que sostiene y el estado degradado exacto en que queda la aplicación cuando esa capacidad se pierde (A-193, RG-065). Este capítulo fija las filas de proveedor `CANVAS`; el mecanismo genérico —cómo se escribe una fila `origen = RUNTIME`, cómo se deriva el estado de una capacidad, cómo se muestra en pantalla— es común a Canvas y a GitHub y está descrito una sola vez en A-193/RG-065; no se repite aquí.

**Disparador.** Cuando una llamada de `ClienteCanvas` devuelve `401`, o un `403` clasificado como no transitorio por §5.6.4, **con la sonda de credencial en verde**, se clasifica `LLAMADA_NO_AUTORIZADA` (RG-068), **la credencial no se invalida**, y ocurren siempre las cuatro mismas cosas: se escribe una fila `origen = RUNTIME` en `verificacion_vinculacion` con la capacidad afectada y el cuerpo literal en `detalle`; el control de la interfaz correspondiente queda deshabilitado con el motivo escrito, **nunca falla al pulsarlo**; se abre la incidencia del tipo que corresponde; y la capacidad vuelve a `DISPONIBLE` sólo cuando una ejecución posterior del checklist o una llamada con éxito lo demuestran.

**Capacidades de Canvas del mapa** (RG-066):

| Capacidad | Endpoint | Ítem del checklist | Requisito | Estado degradado |
|---|---|---|---|---|
| `PUBLICAR_NOTA` | 25 (con `posted_grade`) | 4 | R2.7.6 | Las correcciones pasan a `NO_PUBLICABLE` con motivo; nota, rúbrica y comentario locales se conservan intactos |
| `PUBLICAR_ANUNCIO` | 22 | 5, `5-bis` | R2.6.6, R2.4.2 | El interruptor de aviso de cambio de fecha queda deshabilitado con motivo; la pestaña de anuncios queda en modo lectura |
| `BORRAR_ANUNCIO` | 23 | 19 | Prueba de escritura del checklist | La limpieza diaria abre incidencia en vez de borrar; la prueba de escritura se ofrece igual, avisando de que habrá que borrarlo a mano |
| `ENVIAR_MENSAJE` | 24 | 6 | R2.3.12, R2.6.5 | El canal de comunicación activo pasa al canal 2 (comentario de entrega); si `COMENTAR_ENTREGA` también cae, `curso.canal_comunicacion_activo = BLOQUEADO` |
| `COMENTAR_ENTREGA` | 25 (con `comment[text_comment]`) | 17, `17-bis` | R2.3.12, R2.2.5 | Se retira el canal 2; la respuesta al estudiante en la tarea de registro no sale, y la fila lo dice |
| `CREAR_TAREA` | 20 | 16 | R2.2.4, R2.2.5 | El botón de crear la tarea de registro queda deshabilitado con motivo; quedan las vías complementarias del capítulo 7 |
| `EDITAR_TAREA_REGISTRO` | 21 | 16 | R2.2.5 | «Restaurar la configuración recomendada» queda deshabilitado; se muestra la diferencia campo a campo y el enlace profundo a Canvas |
| `LEER_ROSTER` | 5 (tipo `StudentEnrollment`) | 3, 15 | R2.2.1, R2.2.2 | `sync_roster` se detiene; la regla anti-bajas-masivas de §7 impide dar de baja a nadie mientras tanto; banda roja con el dato congelado y su antigüedad |
| `LEER_GRUPOS` | 7, 8, 9 | 9 | R2.2.3 | `sync_grupos` se detiene; no se pueden vincular tareas grupales nuevas mientras la capacidad esté caída |
| `LEER_FECHAS` | 12, 14 | sin ítem | R2.4.1–R2.4.4 | `sync_tareas_y_fechas` se detiene; `fecha_efectiva` queda congelada con su antigüedad visible; **la captura de versiones sigue** (§5.2.7 punto 4) |
| `LEER_SUBMISSIONS` | 16 | 4 | R2.7.7, R2.2.4 | `reconciliar_notas_canvas` y `recolector_mapeos` cierran en `PARCIAL` con motivo; el contraste con Canvas queda `NO_COMPROBADO` con su antigüedad |
| `LEER_GRADEABLE` | 15 | 4 | R2.7.6 | El pre-chequeo antes de publicar no se ejecuta: la publicación se ofrece igual, con el aviso de que no se pudo comprobar y con el error literal si Canvas la rechaza |
| `LEER_PERIODOS` | 11 | 11 | R2.7.6 | Igual que el anterior, con el mismo aviso |
| `LEER_POLITICA_ATRASO` | 10 | 10 | R2.7.6 | Se publica con `late_policy_status=none`; la relectura obligatoria antes de publicar detecta cualquier deducción real, y la pantalla lo advierte antes |

**No existe ninguna bandera booleana suelta por capacidad de Canvas** (por ejemplo, ninguna columna `curso.puede_enviar_mensajes`): el estado de una capacidad es siempre una derivación, la última fila `(curso_id, capacidad)` con `origen = RUNTIME`. `GET /api/cursos/{id}/salud` y la cabecera del curso muestran las capacidades de Canvas degradadas con su motivo y su fecha; las pantallas afectadas leen ese mismo derivado para deshabilitar sus controles, con el mismo texto en todas.

### Criterios de aceptación de 5.7

1. Todo endpoint de escritura de `ClienteCanvas` está cubierto por alguna fila de este mapa: prueba automatizada que recorre las 6 escrituras de §5.3.2 y falla si alguna no tiene capacidad asociada.
2. Forzando un `401` de `POST /api/v1/conversations` con la sonda de credencial en verde, la credencial del curso permanece `VALIDA`, el curso permanece vinculado, y sólo el botón de mensaje directo queda deshabilitado con el motivo escrito.
3. Con `ENVIAR_MENSAJE` y `COMENTAR_ENTREGA` degradadas a la vez, `curso.canal_comunicacion_activo` pasa a `BLOQUEADO` y la cabecera del curso lo declara.
4. Una llamada posterior con éxito al mismo endpoint devuelve la capacidad a `DISPONIBLE` y el control vuelve a habilitarse, sin intervención manual.
5. `/api/cursos/{id}/salud` lista cada capacidad de Canvas degradada con su motivo literal y la fecha en que se detectó.

---

## 5.8 Casos borde

| # | Caso | Detección | Comportamiento |
|---|---|---|---|
| 1 | **Token revocado o `401` sostenido** | Tres `403` no transitorios consecutivos, o un `401` con la sonda ya invalidando la credencial | Procedimiento completo de §5.2.7: credencial `INVALIDA`, curso `CANVAS_DESVINCULADO`, promoción de respaldo, lo que no depende de Canvas sigue funcionando |
| 2 | **El titular perdió su matrícula de profesor** | Tercera llamada de `sonda_credencial_canvas`: `GET .../enrollments?user_id=self&type[]=TeacherEnrollment` vuelve vacía | `CANVAS_DESVINCULADO` con el mensaje distinto que exige §5.2.7 punto 7: «tu cuenta ya no figura como profesora de este curso»; se promueve el respaldo si existe |
| 3 | **El titular queda limitado a una sección** (`limit_privileges_to_course_section = true` en una matrícula que antes no lo estaba) | Misma llamada de la sonda, sin que ninguna de las otras dos falle | La credencial **sigue válida y el curso no se desvincula**; se detienen únicamente `sync_roster` y `sync_grupos`; el ítem 3 del checklist se reescribe en caliente como `BLOQUEANTE` con `origen = RUNTIME`; se abre `ROSTER_TRUNCADO` con `detalle.causa = LIMITADO_A_SECCION`; banda roja con el texto de qué hacer y el botón para pegar la credencial de otro profesor. Se sale del estado en cuanto una sonda posterior lee el campo en `false` |
| 4 | **El curso de Canvas concluyó** (`workflow_state = 'completed'`, o su período ya pasó) | `GET /courses/:id` en la sonda, o en el checklist | El curso **sigue `ACTIVO`** en la aplicación y la lectura continúa; **las escrituras hacia Canvas se bloquean** y quedan `BLOQUEADO`, reevaluadas cada 30 min; la publicación de nota pasa por el pre-chequeo de períodos, que ya la declara `NO_PUBLICABLE` si el período está cerrado. Banda ámbar: «este curso figura como concluido en Canvas; seguimos leyendo, pero no enviaremos mensajes ni publicaremos notas» |
| 5 | **El curso de Canvas dejó de estar publicado o dejó de ser accesible** (`workflow_state = 'unpublished'` o `'deleted'`, o `404` en `GET /courses/:id`) | Misma llamada | `curso.estado` pasa a `CANVAS_DESVINCULADO`, con la degradación completa de §5.2.7: lecturas detenidas, escrituras encoladas, aprovisionamiento e ingesta de GitHub intactos. Banda roja y correo a los profesores. Se abre la incidencia `CANVAS_CURSO_NO_DISPONIBLE`, severidad BLOQUEANTE, con `detalle` llevando el `workflow_state` recibido |
| 6 | **Valor de `workflow_state` no previsto** | Ninguno de los valores anteriores | Se clasifica por lista blanca: sólo `available` es el caso normal, y todo valor desconocido produce banda ámbar informativa con el valor literal a la vista, **nunca una degradación silenciosa** |
| 7 | **Permiso en verde pero la llamada falla con `401`** | Respuesta de `GET .../permissions` en verde contraste con un `401` real de la llamada correspondiente | Se clasifica `LLAMADA_NO_AUTORIZADA` (§5.7), no se invalida la credencial ni se desvincula el curso; el checklist advierte por escrito, desde su propia pantalla, que un permiso en verde no garantiza que la llamada funcione, porque el endpoint de permisos informa de los permisos del usuario, no de lo que la instancia acepta en cada llamada |
| 8 | **Falta un *scope*** (sólo aplica al camino condicionado de OAuth2, §5.2.9) | `401` con causa de *scope* | Familia PERMANENTE con `detalle.motivo = SCOPE_FALTANTE`; se detiene sólo la familia de trabajos que necesita ese endpoint, no el curso |
| 9 | **La misma huella de token aparece en dos cursos** | Comparación de `credencial_canvas.huella` al guardar | Se advierte en pantalla, sin impedirlo: es legítimo que un profesor use el mismo token en dos cursos suyos |
| 10 | **Canvas Free-for-Teacher como plan alternativo de instancia** | — | Cerrado por hecho externo: el programa está discontinuado de forma permanente y no registra cuentas nuevas. No se planifica ningún camino que dependa de él; el desarrollo y la demostración se hacen siempre contra la instancia institucional (§1.2 de la carta de arquitectura) |
| 11 | **Roster que vuelve vacío o muy recortado sin ninguna señal de error** | `sync_roster` compara el recuento contra el ciclo anterior | Si un ciclo devuelve cero estudiantes o menos del 60 % del recuento anterior, **no se aplica ninguna baja**: se registra `sincronizacion.resultado = PARCIAL`, se abre `ROSTER_SOSPECHOSO` y se conserva el estado previo. Es la segunda línea de defensa detrás del caso 3, activa siempre aunque el checklist esté en verde |

**Falsos positivos en los casos 4 y 5.** La clasificación del estado del curso exige **dos ciclos consecutivos coincidentes** antes de pasar el curso a `CANVAS_DESVINCULADO`, con el mismo criterio con el que la baja de un estudiante exige dos ciclos: una lectura parcial aislada no basta para desvincular un curso entero.

**Lo que ningún caso de esta tabla hace nunca:** borrar un repositorio, un *commit*, una versión capturada o un mapeo; dar de baja al roster por un curso concluido; archivar repositorios automáticamente por esta causa. Archivar es siempre una decisión del docente sobre el trabajo de sus estudiantes, nunca una consecuencia automática de que Canvas cambiara de estado.

### Criterios de aceptación de 5.8

1. Simulando `limit_privileges_to_course_section = true` en la matrícula del titular durante la operación normal del curso, `sync_roster` y `sync_grupos` se detienen, el resto de trabajos sigue, y el ítem 3 del checklist pasa a `BLOQUEANTE` sin que el curso se desvincule.
2. Simulando `workflow_state = 'completed'` en `GET /courses/:id`, una publicación de nota pendiente queda `BLOQUEADO` y ningún mensaje se pierde; el aprovisionamiento de repositorios de ese curso, si estuviera en curso, continúa.
3. Simulando `workflow_state = 'deleted'`, el curso pasa a `CANVAS_DESVINCULADO` sólo después de dos ciclos consecutivos de la sonda con el mismo resultado, nunca con uno solo.
4. Un valor de `workflow_state` no listado en la tabla produce banda ámbar con el valor literal visible, y ningún trabajo se detiene por esa causa exclusivamente.
5. Un roster que cae de 200 a 40 estudiantes en un ciclo no da de baja a ninguno: `ROSTER_SOSPECHOSO` queda abierta y el roster anterior se conserva íntegro.
6. Pegar el mismo token en un segundo curso muestra la advertencia de huella repetida y **no** impide guardar la credencial.
