# 2. Usuarios, roles y permisos

Este capítulo especifica quién puede entrar en la aplicación, cómo se registra, cómo se incorpora al
equipo docente de un curso, qué puede hacer cada persona en cada pantalla y cómo se retira ese acceso
cuando deja de corresponder. Cubre los requisitos **R2.1.1**, **R2.1.2**, **R2.1.7**, **R2.1.8** y
**R2.1.9** del enunciado, y sostiene **R2.1.3**–**R2.1.6**, que se especifican en el capítulo 3.

Está escrito para alguien que no ha leído ningún documento previo. Cada regla cita su origen: los
requisitos del enunciado como **R2.x.y**, las decisiones de la carta de arquitectura como **A-nnn**, y
las reglas de las actas de reconciliación como **RG-nnn**. Cuando una decisión se toma en este
capítulo porque las fuentes no la cerraban, aparece marcada con **[DECISION NUEVA]**.

---

## 2.0. Vocabulario, convenciones y orden de lectura

### 2.0.1. Vocabulario cerrado

La aplicación usa **español de Chile**, tratamiento de «tú», registro profesional y **sin emojis**
(A-154). El vocabulario de este capítulo es cerrado y no admite sinónimos en ninguna pantalla,
ningún correo y ningún nombre de tabla o columna:

| Se dice | Significa | No se dice |
|---|---|---|
| **Profesor** | Rol de curso con los nueve permisos implícitos e irrevocables | admin, titular, owner, coordinador |
| **Ayudante** | Rol de curso con un subconjunto explícito de permisos | TA, staff, corrector, colaborador |
| **Curso** | Curso de la aplicación, vinculado a uno de Canvas | clase, ramo, course |
| **Equipo** | Conjunto de profesores y ayudantes de un curso | staff, cuerpo docente, plantel |
| **Membresía** | La pertenencia de una persona a un curso, con su rol y sus permisos | rol, asignación, alta |
| **Invitación** | El enlace nominal de un solo uso que incorpora a alguien al equipo | invite, alta, solicitud |
| **Cuenta de GitHub vinculada** | Correspondencia entre una persona y un usuario de GitHub | mapeo, matching, linkeo |
| **Cerrar mi cuenta** | La acción por la que una persona desactiva su propio acceso | dar de baja, eliminar cuenta, borrar usuario |
| **Retirar** | Sacar a una persona del equipo de un curso (**R2.1.9**) | expulsar, eliminar, dar de baja |

**Ningún identificador en mayúsculas aparece en pantalla** (A-155). Los nombres técnicos de permisos,
estados y rutas de este capítulo son nombres de código, no textos de interfaz: la interfaz usa
siempre la etiqueta en español de la tabla §2.3.2.

### 2.0.2. Orden de precedencia aplicado en este capítulo

Enunciado → actas de reconciliación (RG) → carta de arquitectura (A) → respuestas de alcance. Donde
una respuesta de alcance decía una cosa y una regla RG dice otra, manda la regla, y este capítulo
recoge la regla. Las dos discrepancias que este capítulo resuelve por precedencia se declaran
explícitamente en §2.3.7 (limitadores de tasa) y §2.12.2 (nombres de endpoint).

---

## 2.1. Quién es usuario de la aplicación

### 2.1.1. Regla de admisión

**Los usuarios de la aplicación son exclusivamente el equipo docente: profesores y ayudantes**
(A-017). **Los estudiantes no tienen cuenta, no tienen sesión y no tienen ninguna ruta de acceso, ni
siquiera de sólo lectura.** Ninguna pantalla, ningún endpoint y ningún token emitido por la
aplicación concede acceso a un estudiante. Los estudiantes participan por Canvas y por GitHub, no por
esta aplicación.

### 2.1.2. No existe rol de administrador de plataforma

**No hay ningún rol global.** No existe consola de administración, no existe usuario capaz de ver
todos los cursos, no existe whitelist de correos, no existe aprobación previa y no existe la regla
«el primer usuario registrado es administrador» (A-165, RG-127). La administración de usuarios ocurre
en dos planos y sólo en dos:

| Plano | Dónde | Quién | Qué administra |
|---|---|---|---|
| **1 · Equipo del curso** | `/cursos/{id}/equipo` | Cualquier profesor del curso, con `equipo.administrar` | Los miembros de **ese** curso: alta, permisos, rol, retiro, reincorporación, invitaciones |
| **2 · Cuenta propia** | `/perfil` | Cada persona, sin permiso | Su nombre visible, su cuenta de GitHub, sus identidades de Canvas, sus sesiones y el cierre de su propia cuenta |

Un profesor **no puede cerrar la cuenta de otra persona**. Lo que puede hacer es retirarla de **su**
curso, que es su ámbito legítimo (A-165). El motivo de esta decisión es que un rol capaz de entrar a
todos los cursos sería el mayor agujero de privacidad del sistema sobre datos de estudiantes reales,
y el enunciado organiza la aplicación «en torno a cursos administrados por profesores» (§2.1 del
enunciado), no en torno a una consola de administración.

### 2.1.3. Cómo se llega a ser profesor o ayudante

Un usuario recién autenticado **no es profesor de nada** (A-018 regla 4). Existen exactamente tres
caminos para adquirir una membresía, y ninguno más:

| # | Camino | Rol resultante | Requisito |
|---|---|---|---|
| 1 | Crear un curso | `PROFESOR` del curso creado | Sesión válida (**R2.1.3**) |
| 2 | Aceptar una invitación de rol profesor | `PROFESOR` (**R2.1.7**) | Invitación nominal vigente a su dirección |
| 3 | Aceptar una invitación de rol ayudante | `AYUDANTE` (**R2.1.8**) | Invitación nominal vigente a su dirección |

**No existe un cuarto camino.** En particular, no se importan matrículas `TeacherEnrollment` ni
`TaEnrollment` de Canvas como altas de equipo: que alguien sea ayudante en la aplicación no implica
que exista en Canvas, ni al revés (Q-2.1-42, adoptada por A-024).

### 2.1.4. Criterios de aceptación de §2.1

| # | Comprobación |
|---|---|
| CA-2.1-01 | Recorrer el enrutador completo: ninguna ruta concede lectura de datos de un curso sin `membresia_curso` con `estado = ACTIVA` en ese curso, salvo las dieciséis rutas sin sesión de §2.11.4 |
| CA-2.1-02 | No existe en el esquema ninguna columna de rol global ni ninguna tabla `administrador`; una búsqueda del término en la migración inicial no devuelve nada |
| CA-2.1-03 | La navegación de la aplicación no muestra ninguna entrada de «administración global» a ningún usuario |
| CA-2.1-04 | Con una cuenta recién registrada y sin cursos, `GET /api/cursos` devuelve lista vacía y `/cursos` muestra el estado vacío guiado, no un error |

---

## 2.2. Registro y autenticación (R2.1.1, R2.1.2)

### 2.2.1. Mecanismo: Google OpenID Connect

El alta y el acceso se implementan con **Google OpenID Connect, flujo Authorization Code con PKCE**
(A-018). **No hay contraseña propia, no hay magic link y no hay ningún mecanismo de respaldo con
credencial local.** El motivo es que **R2.1.2** exige que el usuario se registre «asociando su cuenta
de correo basada en gmail.com», y OIDC es el único mecanismo que **prueba** esa asociación en lugar
de creerla: el `id_token` trae `email` junto con `email_verified`.

**Datos de Google que se persisten, y ninguno más:**

| Reclamación del `id_token` | Columna | Uso |
|---|---|---|
| `sub` | `usuario.google_sub` (única) | Identidad técnica: es lo que reconoce a quien vuelve |
| `email` | `usuario.email` (citext, única) | Identidad legible; no editable por su dueño |
| `name` | `usuario.nombre` | Nombre visible inicial, editable en `/perfil` |
| `picture` | `usuario.avatar_url` | Avatar |

**No se guarda el `id_token`, no se guarda ningún `access_token` ni `refresh_token` de Google, y no se
solicita ningún alcance más allá de `openid email profile`.** La aplicación no llama a ninguna API de
Google después del acceso, de modo que un volcado de la base de datos no contiene ninguna credencial
de terceros (A-018, mismo criterio que A-038 aplica a GitHub).

### 2.2.2. Flujo de acceso, paso a paso

| # | Paso | Detalle normativo |
|---|---|---|
| 1 | El usuario pulsa «Entrar con Google» en `/acceso` | Botón único; el texto anticipa la exigencia de `gmail.com` |
| 2 | `POST /auth/google/inicio` | Genera `code_verifier` (PKCE), `nonce` y `txn_id` aleatorio de 256 bits; firma el `state`; fija la cookie `oidc_txn`; redirige |
| 3 | Redirección a Google | `GET https://accounts.google.com/o/oauth2/v2/auth` con **`prompt=select_account` siempre, en todo acceso** (A-018 regla 2) |
| 4 | Retorno a `GET /auth/google/callback` | Se valida en este orden: firma del `state`, caducidad, `jti` no consumido, contraste de `sha256(txn_id)` con la cookie, canje del código con PKCE, `iss`, `aud`, `exp` y `nonce` del `id_token` |
| 5 | Reglas de admisión de correo | §2.2.4 |
| 6 | Alta o actualización de `usuario` | §2.2.5 |
| 7 | Creación de la sesión | §2.2.6 |

**El `state` es un JWT firmado con HMAC y caducidad de 10 minutos** que contiene el `nonce` esperado,
el destino de vuelta y `sha256(txn_id)` (A-018 regla 3). El `nonce` esperado vive **dentro del JWT
firmado**, no en el servidor: no hay estado de servidor que perder en una ventana privada. El `jti`
consumido se registra en `sesion.jti_oidc` para que un `state` no pueda reutilizarse.

**La cookie `oidc_txn`** se emite con `Secure; HttpOnly; SameSite=Lax; Path=/auth; Max-Age=600` y
existe **sólo** para vincular el flujo al navegador y defender contra el CSRF de inicio de sesión, es
decir, contra que un tercero consiga que la víctima quede autenticada en la cuenta del atacante.

**Camino degradado, y sólo si la cookie no vuelve** (ventana privada, ITP de Safari, bloqueo de
cookies): **la sesión no se crea todavía**. Se muestra en el propio origen de la aplicación una
pantalla de confirmación que **nombra la cuenta de Google a la que se va a entrar** y exige un gesto
explícito del usuario con un token anti-CSRF de formulario, en `POST /auth/confirmar`. **La firma, la
caducidad y el `nonce` se validan siempre, en los dos caminos**, sin excepción.

### 2.2.3. Matriz de navegadores declarada

| Navegador | Ventana normal | Ventana privada |
|---|---|---|
| Chrome de escritorio | Soportado | Soportado |
| Edge de escritorio | Soportado | Soportado |
| Firefox de escritorio | Soportado | Soportado |
| Safari de escritorio | Soportado | **Fuera de alcance declarado** |

Es la matriz de A-019, y se declara por escrito en la memoria de entrega. Si el agente de usuario
corresponde a Safari en navegación privada, `/acceso` muestra un aviso discreto que dice que ese modo
está fuera de la matriz declarada y ofrece abrir la aplicación en una ventana normal. **La prueba en
ventana privada es criterio de aceptación, no una comprobación opcional** (A-019).

### 2.2.4. Regla de admisión de correo (R2.1.2)

Se acepta el alta **si y sólo si** se cumplen las dos condiciones:

1. el `id_token` trae `email_verified = true`; **y**
2. el dominio del `email`, tras normalizar, es exactamente `gmail.com`.

Reglas complementarias, todas de A-018 regla 1:

- **`googlemail.com` se acepta, normalizándolo a `gmail.com`**: es el mismo dominio de Google servido
  con otro nombre y devuelve la misma cuenta.
- **Se rechaza cualquier correo que traiga la reclamación `hd`**, es decir, cualquier cuenta de Google
  Workspace con dominio gestionado, **incluida la cuenta institucional de la Universidad de los
  Andes**. La regla es explícita: **`hd` manda y se rechaza aunque la dirección termine en
  `@gmail.com`**, porque `hd` significa dominio gestionado.
- **La regla no se relaja bajo ninguna circunstancia.** El rechazo de una cuenta institucional es
  **cumplimiento de R2.1.2, no un fallo**, y así se escribe en el texto de la entrega (A-166 punto 5).

**La regla vive en dos sitios a la vez**, cinturón y tirantes: en el código del *callback*, y como
`CHECK` de la tabla `usuario` (`CHECK (email LIKE '%@gmail.com')`, A-075). Ni un error de programación
ni una migración pueden colar una dirección que no cumpla.

La comprobación es una función pura `normalizar_correo_google(email, hd)` en
`backend/app/dominio/`, sin entrada ni salida, que devuelve el correo normalizado o el motivo de
rechazo tipado: `HD_PRESENTE`, `DOMINIO_NO_GMAIL`, `CORREO_NO_VERIFICADO`. Casos de prueba
obligatorios: `ana@gmail.com`; `Ana@GMail.com`; `ana@googlemail.com`; `ana@uandes.cl` con `hd`;
`ana@gmail.com` **con `hd` presente**, que se rechaza igual; y `email_verified = false`.

### 2.2.5. Identidad de una persona: tres columnas

La identidad es doble en su función y triple en su representación (A-185, RG-002, adoptando
Q-2.1-04):

| Columna | Tipo y restricción | Función |
|---|---|---|
| `usuario.google_sub` | texto, **única** | **Identidad técnica.** Es el valor estable que emite Google y el que reconoce a quien vuelve |
| `usuario.email` | `citext`, **única**, `CHECK` de `@gmail.com` | **Identidad legible.** No editable por su dueño: es la identidad de Google y la clave de `usuario` |
| `usuario.email_canonico` | `citext`, **`NOT NULL UNIQUE`** | **Emparejamiento de invitaciones**, y nada más |

**Normalización, en este orden y sólo sobre correos ya aceptados por §2.2.4:**

1. minúsculas en todo el correo;
2. `googlemail.com` → `gmail.com`;
3. `email` guarda el resultado de 1 y 2, que es la forma canónica que devuelve Google;
4. `email_canonico` guarda además el *local-part* **sin puntos** y **sin el sufijo `+etiqueta`**.

La canonización **sólo se aplica a `gmail.com` y `googlemail.com`**, que es donde está documentado que
los puntos y el sufijo `+etiqueta` enrutan a la misma cuenta. La función vive en
`backend/app/dominio/` y **se ejecuta antes del `CHECK` y antes de escribir**.

**Por qué existe `email_canonico`:** un profesor que invita a `ana.perez+ramo@gmail.com` y una persona
que entra como `anaperez@gmail.com` **son la misma persona**, y sin canonización la invitación nunca
casaría. **El emparejamiento de una invitación se hace por `email_canonico`, nunca por la cadena
tecleada.**

**Cambio de dirección en Google.** Si Google devuelve un `google_sub` conocido con un `email` distinto,
**manda el `sub`**: se actualizan `email` y `email_canonico` en la misma transacción, el cambio queda
en `bitacora` y `/perfil` muestra un aviso. **Si el `email_canonico` nuevo chocara con el de otro
usuario existente, no se actualiza nada**, se deniega el acceso con mensaje explícito y se abre el
caso para el equipo: fusionar dos cuentas sería adivinar sobre la identidad de una persona.

### 2.2.6. Sesión

| Propiedad | Valor |
|---|---|
| Tipo | Cookie **opaca**: identificador aleatorio de 256 bits. **No es un JWT autocontenido** |
| Atributos | `Domain=.<dominio>; HttpOnly; Secure; SameSite=Lax; Path=/` |
| Estado | Tabla `sesion`, con `token_hash` único, `jti_oidc`, `creada_en`, `expira_en`, `revocada_en`, `agente`, `ip_truncada` |
| Expiración deslizante | **12 horas** |
| Expiración absoluta | **7 días** |
| CSRF | Toda mutación exige cabecera `X-CSRF-Token` contrastada contra una cookie de doble envío no `HttpOnly` |
| CORS | Lista blanca explícita, `allow_credentials=True`, métodos y cabeceras enumerados. **`allow_origins=["*"]` está prohibido**, con prueba automatizada que falla si aparece |

La sesión es **opaca y con estado en base de datos precisamente para que el retiro de un ayudante
(R2.1.9) invalide sus sesiones de inmediato** (A-009). Un JWT autocontenido no permitiría esa
revocación, y por eso queda descartado.

Al iniciar sesión se escribe **una fila de `sesion_membresia (sesion_id, membresia_id, version,
refrescada_en)` por cada membresía activa del usuario**, con la versión vigente en ese instante
(A-023). El mecanismo completo se especifica en §2.7.

### 2.2.7. Rechazos de acceso: catálogo cerrado de desenlaces

Un intento de acceso que no cumple la regla **no crea usuario, no crea sesión y no deja nada a
medias**. Se responde con una pantalla en el propio origen de la aplicación, con título, una frase que
explica el motivo concreto y las acciones que correspondan. **No existe estado «pendiente de
aprobación» ni pantalla de solicitud de acceso**, porque no hay administrador que apruebe (A-165).

| # | Motivo | Texto de la pantalla | Acción ofrecida |
|---|---|---|---|
| 1 | Dominio distinto de `gmail.com` | «Esta aplicación solo admite cuentas de `gmail.com`. Lo exige el requisito R2.1.2 del enunciado del proyecto. Entraste con *correo mostrado*.» | «Probar con otra cuenta» |
| 2 | Reclamación `hd` presente (Workspace) | «*correo* pertenece a un dominio gestionado (*hd*). Necesitas una cuenta personal de `gmail.com`.» | «Probar con otra cuenta» |
| 3 | `email_verified = false` | «Google indica que ese correo aún no está verificado. Verifícalo en tu cuenta de Google y vuelve a intentarlo.» | «Reintentar» |
| 4 | El usuario canceló en Google (`error=access_denied`) | «No autorizaste el acceso. Sin ese permiso no podemos identificarte.» | «Reintentar» |
| 5 | `state` inválido, caducado o ya consumido | «Tu intento de acceso caducó. Empieza de nuevo.» | «Empezar de nuevo» |
| 6 | Cookie `oidc_txn` ausente | **No es un rechazo:** pantalla de confirmación que nombra la cuenta y exige un clic | «Confirmar» / «Cancelar» |
| 7 | `usuario.activo = false` (cuenta cerrada) | «Esta cuenta fue cerrada por su titular el *fecha* y no puede volver a iniciar sesión.» | Contacto del equipo |
| 8 | Fallo del proveedor (5xx, tiempo agotado) | «Google no respondió. No es un problema de tu cuenta.» más el texto literal del error (A-155) | «Reintentar» |

Reglas fijas sobre estos desenlaces:

- El botón «Probar con otra cuenta» reinicia el flujo completo forzando `prompt=select_account`, lo
  que cierra el bucle de reintentos con auto-selección de la misma cuenta.
- **La fila 6 se distingue visualmente y por texto de las demás: es una confirmación, no un error**, y
  su botón principal entra.
- El *callback* **nunca devuelve `500` por un motivo previsto**: existe el tipo de error
  `RechazoAcceso(motivo, detalle)` en `backend/app/dominio/`, mapeado a la pantalla.
- Los ocho textos viven en el archivo único de mensajes (A-154).

**Dónde queda el rastro.** Los intentos rechazados se registran **sólo en el log estructurado** de
A-015, con `motivo`, `email_dominio` e `ip_truncada`. **No se persiste el correo completo de quien no
llegó a ser usuario**, y estos rechazos **nunca se escriben en `bitacora`**, que es la auditoría de
acciones con consecuencia sobre un curso y aquí no hay ni curso ni actor legítimo (A-183 destino 2,
RG-142 nivel 2).

### 2.2.8. Criterios de aceptación de §2.2

| # | Comprobación |
|---|---|
| CA-2.2-01 | Entrar con una cuenta `gmail.com` verificada crea el `usuario` y la `sesion` en menos de 30 segundos y deja al usuario en `/cursos` |
| CA-2.2-02 | Entrar con una cuenta institucional con `hd` produce la pantalla del motivo 2, **no crea ninguna fila** en `usuario` y no crea sesión |
| CA-2.2-03 | Entrar con `ana@gmail.com` que además trae `hd` se rechaza: la regla de `hd` prevalece sobre el sufijo del dominio |
| CA-2.2-04 | `ana@googlemail.com` entra y su `usuario.email` queda escrito como `ana@gmail.com` |
| CA-2.2-05 | Un `INSERT` directo en la base con `email = 'x@uandes.cl'` es rechazado por el `CHECK` de `usuario` |
| CA-2.2-06 | La URL de autorización construida contiene `prompt=select_account`; existe una prueba automatizada que **falla si el parámetro desaparece** |
| CA-2.2-07 | Reutilizar un `state` ya consumido produce el motivo 5 y no crea sesión |
| CA-2.2-08 | Un `state` con firma alterada produce el motivo 5 en los dos caminos, normal y degradado |
| CA-2.2-09 | En ventana privada de Chrome, Edge y Firefox el acceso se completa; si la cookie `oidc_txn` no vuelve, aparece la pantalla de confirmación que nombra la cuenta y un clic completa el acceso |
| CA-2.2-10 | `ana.perez+ramo@gmail.com` y `anaperez@gmail.com` producen el mismo `email_canonico` |
| CA-2.2-11 | Ningún registro del log ni ninguna fila de la base contiene el correo completo de un intento rechazado |
| CA-2.2-12 | Ninguna respuesta de la API devuelve `id_token`, `access_token` ni `refresh_token` de Google |

---

## 2.3. El catálogo de permisos (R2.1.8)

### 2.3.1. Aritmética de los nueve permisos

Se definen **nueve permisos nombrados** (A-021), muy por encima del mínimo de tres que exige
**R2.1.8**. La descomposición es normativa (A-178, RG-121):

| Grupo | Cuántos | Cuáles |
|---|---|---|
| **Implícitos e irrevocables** mientras la membresía esté activa | **2** | `curso.ver`, `correccion.corregir` |
| **Configurables** — los únicos valores que admite el array `permisos` | **7** | `curso.administrar`, `equipo.administrar`, `tarea.administrar`, `mapeo.editar`, `correccion.asignar`, `nota.publicar`, `comunicacion.enviar` |
| De los siete configurables, **concedibles a un ayudante** | **5** | `tarea.administrar`, `mapeo.editar`, `correccion.asignar`, `nota.publicar`, `comunicacion.enviar` |
| De los siete configurables, **NO CONCEDIBLES a un ayudante** | **2** | `curso.administrar`, `equipo.administrar` |

> **La expresión «los siete permisos concedibles» queda prohibida** en esta especificación, en la
> interfaz, en los correos y en el texto de la entrega. Se escribe **«los cinco concedibles»** o
> **«los siete configurables»**, que son cosas distintas (A-178, RG-121).

**El profesor tiene los nueve de forma implícita e irrevocable.** No existe «profesor con menos
permisos»: ésa sería la manera silenciosa de incumplir «mismos permisos» de **R2.1.7**.

### 2.3.2. Tabla normativa de permisos

| Nombre de código | Etiqueta en pantalla | Qué habilita exactamente | Profesor | Ayudante por defecto | Concedible a ayudante |
|---|---|---|---|---|---|
| `curso.ver` | **Ver el curso** | Ver el curso, personas, tareas, tablero, timeline, estado de repositorios, entregas y fechas | Sí (implícito) | **Sí (implícito)** | No revocable mientras la membresía esté activa |
| `correccion.corregir` | **Corregir lo asignado** | Abrir y trabajar **en modo edición sólo** las entregas asignadas a uno mismo y guardar la corrección local | Sí (implícito) | **Sí (implícito)** | No revocable |
| `curso.administrar` | **Administrar el curso** | Editar el curso, rehacer la vinculación con Canvas o GitHub, añadir, promover o retirar credenciales, cambiar la zona horaria, roles de estudiante adicionales, archivar el curso | Sí | No | **NO CONCEDIBLE** |
| `equipo.administrar` | **Administrar el equipo** | Incorporar y retirar profesores y ayudantes, cambiar rol, cambiar permisos, revocar y reenviar invitaciones | Sí | No | **NO CONCEDIBLE** |
| `tarea.administrar` | **Administrar tareas** | Crear y editar tareas, vincular entregas de Canvas, gestionar el repositorio base y sus archivos, forzar aprovisionamiento, reintentar fallos, «capturar ahora» sin cambiar la fecha de corte | Sí | No | Sí |
| `mapeo.editar` | **Editar cuentas de GitHub vinculadas** | Crear, corregir e invalidar la correspondencia estudiante ↔ cuenta de GitHub; importar CSV; reenviar invitaciones a estudiantes | Sí | **Sí** | Sí |
| `correccion.asignar` | **Repartir correcciones** | Repartir las entregas entre los correctores | Sí | No | Sí |
| `nota.publicar` | **Publicar nota** | Escribir calificación, comentario y rúbrica en Canvas | Sí | **No** | Sí |
| `comunicacion.enviar` | **Enviar comunicaciones** | Enviar mensajes y anuncios manuales por Canvas y activar o desactivar las comunicaciones automáticas de una tarea | Sí | No | Sí |

**[DECISION NUEVA]** Las etiquetas en pantalla de `curso.ver`, `correccion.corregir`,
`curso.administrar`, `equipo.administrar`, `tarea.administrar`, `mapeo.editar` y `correccion.asignar`
se fijan en esta tabla. Las fuentes fijaban sólo «Publicar nota» y «Enviar comunicaciones»
(Q-2.1-46), y A-155 exige una etiqueta fija y la misma palabra en todas las vistas. Las siete
etiquetas nuevas siguen el vocabulario cerrado de A-154 y no introducen ningún término prohibido.

### 2.3.3. Por qué dos permisos no son concedibles

| Permiso | Motivo del cierre por diseño | Texto que muestra el control deshabilitado |
|---|---|---|
| `curso.administrar` | Quien puede cambiar la credencial de Canvas puede actuar como el profesor sobre todo el curso | «da acceso a la credencial de Canvas del curso» |
| `equipo.administrar` | Quien administra el equipo puede concederse a sí mismo el resto de los permisos | «permitiría concederse a sí mismo el resto» |

Es una escalada de privilegios trivial y **se cierra por diseño, no por confianza** (A-021).

### 2.3.4. Qué significa «por defecto»

**«Por defecto» es el conjunto precargado en el formulario de invitación** (A-021, aclaración
explícita). No es una semilla que se aplique sola con valores distintos de los que se vieron en
pantalla, y no es un valor inmutable:

1. El profesor que invita **ve el conjunto precargado y lo puede editar antes de enviar**.
2. La invitación guarda el conjunto elegido en `invitacion_equipo.permisos`.
3. **Al aceptar se copia tal cual a `membresia_curso.permisos`.**
4. Cualquier profesor puede cambiarlo después desde `/cursos/{id}/equipo`; cada cambio queda en
   `bitacora` y surte efecto de inmediato (§2.7).

**El valor por defecto para un ayudante es la configuración conservadora: `mapeo.editar` marcado y
`nota.publicar` sin marcar** — ayudantes que corrigen y un profesor que publica. La otra
configuración —ayudantes que publican lo suyo— **es igual de legítima y se habilita con un clic**. La
aplicación soporta las dos; la que viene marcada es la que menos daño hace si nadie revisa el
formulario, porque publicar escribe en Canvas con la identidad del titular del token y esa escritura
es la única del sistema que un docente no puede deshacer desde la aplicación (A-021, A-142).

### 2.3.5. Conjuntos preparados

Los conjuntos preparados son **azúcar de interfaz y no entidades**: al elegir uno se marcan sus
casillas y el profesor puede seguir editándolas. **Lo que se persiste es siempre la lista de permisos,
nunca el nombre del conjunto** (Q-2.1-45, adoptada).

| Conjunto | Qué marca |
|---|---|
| **Sólo corregir** | Los dos implícitos y nada más: `permisos = '{}'` |
| **Corregir y publicar** | Añade `nota.publicar` |
| **Gestión completa (los cinco concedibles)** | `tarea.administrar`, `mapeo.editar`, `correccion.asignar`, `nota.publicar`, `comunicacion.enviar` |

**Ningún conjunto preparado contiene un permiso NO CONCEDIBLE** (RG-121). El tercero se llama
literalmente «Gestión completa (los cinco concedibles)», y ese nombre es normativo.

### 2.3.6. El formulario de permisos

El formulario de `/cursos/{id}/equipo` y el de invitación muestran **las siete casillas
configurables**, y en este orden y con esta apariencia (A-178, RG-121):

| Elemento | Estado en el formulario |
|---|---|
| Los **dos implícitos** | Marcados y fijos, con la nota **«siempre incluidos»** |
| Las **cinco concedibles** | Editables, cada una con su etiqueta en español y **una frase que dice qué habilita exactamente**, tomada de la columna correspondiente de §2.3.2 |
| Las **dos NO CONCEDIBLES** | **Deshabilitadas, con el motivo escrito en el propio control** (§2.3.3) |
| Los **tres conjuntos preparados** | Botones que marcan casillas; no se persiste su nombre |

Bajo el formulario aparece de forma permanente la frase: «los permisos son del curso completo; el
reparto de correcciones es lo que acota qué entrega abre cada persona» (Q-2.1-47, adoptada).

### 2.3.7. Alcance de los permisos

**Los permisos se otorgan exclusivamente a nivel de CURSO.** No hay permisos por tarea ni por sección,
y **la ausencia de una columna de alcance en `membresia_curso` es la decisión, no un olvido**
(Q-2.1-47). Consecuencias, todas explícitas:

1. **Un ayudante activo ve todo el curso en lectura.** `curso.ver` es implícito y no revocable, y
   habilita curso, personas, tareas, tablero, timeline, estado de repositorios, entregas y fechas.
2. **Lo que un ayudante NO ve, en ningún caso:** el token de Canvas ni ningún otro secreto —ninguna
   ruta de la API devuelve jamás un secreto y la columna se excluye explícitamente de todo esquema
   Pydantic de salida (A-034)—; la pantalla de credenciales y el asistente de vinculación
   (`curso.administrar`, NO CONCEDIBLE); las sesiones y el perfil de otras personas; y, en modo
   edición, las entregas de corrección que no tiene asignadas.
3. **Datos personales del estudiante visibles con `curso.ver`:** nombre, nombre ordenable, sección,
   grupo, `login_id`, correo cuando Canvas lo entregue, cuenta de GitHub vinculada, actividad y
   versiones. **Toda exportación a CSV queda registrada en `bitacora` con actor, curso y número de
   filas** (A-029), que es la contrapartida de trazabilidad al acceso amplio.
4. **El alcance de la corrección lo da la asignación, no un permiso de sección.** Repartir por sección
   existe como **modo de reparto**, no como recorte de permisos.
5. **Ámbito de `nota.publicar`:** un ayudante publica sólo sobre entregas asignadas a sí mismo, por la
   conjunción de la cláusula de propiedad de `correccion.corregir` y `nota.publicar`. Un profesor, que
   tiene los nueve, publica cualquiera.

### 2.3.8. La cláusula de propiedad acota el TRABAJO, no la LECTURA

Esta precisión es normativa y corrige una lectura anterior (A-180, RG-125):

| Se lee con `curso.ver`, para todo miembro activo | Queda acotado por propiedad |
|---|---|
| La **matriz nominal completa** del estado de corrección de una tarea: sujeto, entrega, corrector asignado, estado de corrección, versión vigente y si está publicada | Abrir la corrección **en modo edición** y guardar borrador |
| Los tres agregados: por corrector, por sección y por entrega | Ver el **borrador** de otro corrector: nota local, rúbrica local, comentario sin publicar |
| El doble contador «N de M corregidas en la aplicación · K de M con nota en Canvas · comprobado hace X» | Ver las **notas internas y banderas** de otro corrector |
| Los filtros, incluido el filtro por corrector, y la exportación a CSV de lo que se está viendo | — |

La pestaña de estado se llama **«Estado de la entrega»**, es **siempre visible** para todo miembro
activo, y **sobre una fila ajena el botón principal es «ver», no «corregir»**. La pestaña «Repartir»
exige `correccion.asignar`; publicar exige `nota.publicar`.

En la capa de repositorio, el filtro `sólo_propias` se aplica **únicamente** a las rutas de escritura
de corrección y a la lectura de `correccion.borrador`, `correccion.notas_internas` y
`correccion.banderas`.

### 2.3.9. Las seis acciones cerradas por ROL

La dependencia de autorización tiene la firma **`requiere(permiso, curso_id, rol_minimo=None)`**. El
valor `rol_minimo='PROFESOR'` se usa en **exactamente seis acciones y ninguna más**, enumeradas en la
constante **`ACCIONES_SOLO_PROFESOR`** de un único módulo (A-179, RG-122):

| # | Acción | Permiso que exige además |
|---|---|---|
| 1 | Confirmar una incidencia `POSIBLE_FUSION_CANVAS` | `mapeo.editar` |
| 2 | Recapturar una versión con otra fecha de corte (`origen_captura = MANUAL_FECHA`) | `tarea.administrar` |
| 3 | Fijar una versión en un SHA concreto (`origen_captura = MANUAL_SHA`) | `tarea.administrar` |
| 4 | Archivar y desarchivar los repositorios de una tarea | `tarea.administrar` |
| 5 | Entrar a `/operacion`, a `/operacion/invariantes` y a todo `/api/operacion/**` | — |
| 6 | Salir de `MODO_RECUPERACION` | — |

Reglas que gobiernan esta lista:

- **«Capturar ahora» sin cambiar la fecha de corte NO está en la lista**: es `tarea.administrar`, y un
  ayudante con ese permiso puede hacerlo.
- **Ninguna otra ruta, servicio o consulta lee `membresia_curso.rol` para decidir si una acción
  procede.** Una puerta de construcción falla si aparece una lectura de `rol` con efecto de
  autorización fuera de `requiere(...)`.
- La lista es **invariante respecto del perfil de alcance**: una acción de la lista que no esté
  registrada bajo el perfil vigente **no** incumple la lista; una acción registrada que exija rol sin
  figurar en ella **sí** la incumple.
- Un ayudante con `tarea.administrar` que llame directamente a una de estas rutas recibe **`403` con
  código `PERMISO_INSUFICIENTE`**, y en pantalla ve el control **deshabilitado con el motivo escrito**:
  «archivar los repositorios de la tarea es una acción reservada a un profesor del curso» (RG-123,
  RG-201).

**`/operacion` no es una vista global.** `/operacion`, `/operacion/invariantes`, todo
`/api/operacion/**` y la **forma completa** de `GET /estado` sirven **exclusivamente** datos de los
cursos donde el solicitante tiene `membresia_curso` con `estado = ACTIVA` y `rol = PROFESOR`
(A-232, RG-127). Un usuario sin ninguna membresía activa de rol profesor recibe **`404` en todo el
prefijo**, y la entrada a `/operacion` no aparece en su navegación.

### 2.3.10. El catálogo, defendido también en la base de datos

`membresia_curso.permisos` e `invitacion_equipo.permisos` son `text[]` y llevan **cuatro `CHECK`**,
todos en la migración inicial (A-181, RG-124, RG-145):

| # | Restricción |
|---|---|
| 1 | Los elementos del array se restringen a **los siete nombres configurables**. Los dos implícitos **nunca se persisten** |
| 2 | Se prohíbe `curso.administrar` y `equipo.administrar` cuando `rol = 'AYUDANTE'`, **en las dos tablas** |
| 3 | Se exige `permisos = '{}'` cuando `rol = 'PROFESOR'`. **La aplicación nunca lee `permisos` de una membresía de rol `PROFESOR`** |
| 4 | Se prohíbe `NULL` dentro del array, y toda escritura usa valores distintos |

**Validación de servidor, además del `CHECK`.** Se rechaza con **`422`** todo array de permisos de una
`membresia_curso` o de una `invitacion_equipo` de rol `AYUDANTE` que contenga un permiso NO
CONCEDIBLE, en `PATCH /api/cursos/{id}/miembros/{membresia_id}/permisos`, en
`PATCH /api/cursos/{id}/miembros/{membresia_id}/rol` y en
`POST /api/cursos/{id}/equipo/invitaciones`.

### 2.3.11. Dos cosas que no son permisos

**Ver y cambiar la propia suscripción al informe** (**R2.6.3**) y **editar el propio perfil** no
aparecen en el catálogo porque **no son permisos**: son acciones sobre uno mismo, disponibles para
todo miembro activo del curso con `curso.ver`, y viven fuera de `/cursos/{id}/ajustes` precisamente
por eso (A-021, A-132, A-151 regla 0).

### 2.3.12. Criterios de aceptación de §2.3

| # | Comprobación |
|---|---|
| CA-2.3-01 | El catálogo del código enumera exactamente nueve permisos, dos implícitos y siete configurables; una prueba falla si el número cambia |
| CA-2.3-02 | `PATCH /api/cursos/{id}/miembros/{membresia_id}/permisos` con `["curso.administrar"]` sobre un ayudante devuelve **`422`**; existe una prueba automatizada que lo intenta y espera `422` |
| CA-2.3-03 | Un `UPDATE` directo en la base que escriba `equipo.administrar` en los permisos de un ayudante es rechazado por el `CHECK` |
| CA-2.3-04 | Un `INSERT` directo de una membresía de rol `PROFESOR` con `permisos <> '{}'` es rechazado por el `CHECK` |
| CA-2.3-05 | Un `INSERT` directo con un nombre de permiso inventado es rechazado por el `CHECK` |
| CA-2.3-06 | El formulario de permisos muestra siete casillas: cinco editables, dos deshabilitadas con su motivo escrito, y los dos implícitos marcados y fijos con «siempre incluidos» |
| CA-2.3-07 | El tercer conjunto preparado se llama «Gestión completa (los cinco concedibles)» y **no marca ninguna casilla NO CONCEDIBLE** |
| CA-2.3-08 | Una búsqueda de texto en el repositorio no encuentra la expresión «los siete permisos concedibles» en código, interfaz, correos ni documentación |
| CA-2.3-09 | `GET /api/cursos/{curso_id}/tareas/{tarea_id}/correccion/estado` responde con la matriz nominal completa a un ayudante que sólo tiene los dos implícitos |
| CA-2.3-10 | Ese mismo ayudante recibe `403` al intentar abrir en modo edición una corrección que no tiene asignada, y `403` al leer el borrador de otro corrector |
| CA-2.3-11 | `ACCIONES_SOLO_PROFESOR` contiene exactamente seis entradas; una prueba de matriz ejecuta cada una como ayudante con el permiso correspondiente y espera `403` con código `PERMISO_INSUFICIENTE` |
| CA-2.3-12 | Una puerta de construcción falla si aparece una lectura de `membresia_curso.rol` con efecto de autorización fuera de `requiere(...)` |
| CA-2.3-13 | Un profesor de un curso A recibe `404` en `/api/operacion/**` al pedir un trabajo del curso B, donde no es profesor |
| CA-2.3-14 | Ninguna respuesta de la API contiene el token de Canvas ni ningún otro secreto; existe una prueba que recorre los esquemas de salida |

---

## 2.4. Modelo de membresía: el rol vive en la membresía

### 2.4.1. Regla estructural

El modelo es **`usuario` ⟷ `membresia_curso(curso, rol, permisos)` ⟷ `curso`**, con **el rol viviendo
en la membresía y no en el usuario** (A-020). **Una misma persona puede ser profesora de un curso y
ayudante de otro, y eso es normal, no una excepción.** Sólo hay dos roles: `PROFESOR` y `AYUDANTE`.

### 2.4.2. Invariantes del equipo docente

| # | Invariante | Consecuencia si se intenta violar |
|---|---|---|
| 1 | **Unicidad `(curso_id, usuario_id)`** en `membresia_curso` | Una persona tiene como mucho una membresía por curso. **Reincorporar reactiva la misma fila**, nunca crea una nueva |
| 2 | **Todo curso `ACTIVO` conserva al menos una `membresia_curso` `ACTIVA` de rol `PROFESOR`** | Retirar o degradar al último se rechaza con el mensaje **«promueve antes a otro profesor»**. Es el invariante 15 de `verificar_invariantes`, **bloqueante**, que lista y no auto-repara |
| 3 | **Los profesores no tienen jerarquía entre sí** | No hay «creador» con permisos reservados: cualquier profesor puede retirar a cualquiera, salvo al último |
| 4 | **Un cambio de rol o de permisos incrementa `membresia_curso.version` en la misma transacción** | El cambio surte efecto de inmediato (§2.7) |
| 5 | **`membresia_curso.estado ∈ {ACTIVA, RETIRADA}`**, nunca `DELETE` | La baja es lógica (A-030, A-190) |
| 6 | **Ninguna membresía ni invitación de rol `AYUDANTE` contiene un permiso NO CONCEDIBLE** | Es el invariante 16, **bloqueante**, que lista y no auto-repara: vaciar permisos a mano sería decidir por un profesor |
| 7 | **Ninguna cuenta de GitHub enlazada desde `usuario.cuenta_github_id` tiene un `mapeo_github` `VIGENTE` en ningún curso** | Es el invariante 17, **bloqueante**, que lista y no auto-repara (§2.8) |

`verificar_invariantes` comprueba diecisiete invariantes, y los tres últimos son los de esta tabla
(A-181, RG-124, RG-199). Sus violaciones se escriben en `resultado_invariante` y su fila de
`/operacion/invariantes` queda acotada a los cursos de quien mira.

### 2.4.3. Tablas y columnas

**`usuario`**

| Columna | Tipo y restricción | Semántica |
|---|---|---|
| `id` | uuid, PK | — |
| `email` | citext, **única**, `CHECK` de `@gmail.com` | Identidad legible; no editable por su dueño |
| `email_canonico` | citext, **`NOT NULL UNIQUE`** | Emparejamiento de invitaciones (§2.2.5) |
| `google_sub` | texto, **única** | Identidad técnica |
| `nombre` | texto | Nombre visible, editable en `/perfil` |
| `avatar_url` | texto | — |
| `cuenta_github_id` | uuid **NULL** → `cuenta_github(id)` `ON DELETE RESTRICT`, **índice único parcial donde no es nulo** | Cuenta de GitHub declarada (§2.8) |
| `consentimiento_github_en` | timestamptz **NULL** | Fecha del consentimiento de lectura de todo el código (§2.8.2) |
| `generacion_enlaces` | int `NOT NULL DEFAULT 1` | Revocación en bloque de los enlaces de baja del informe |
| `creado_en`, `ultimo_acceso_en` | timestamptz | — |
| `activo` | boolean | **`false` significa «esta persona cerró su cuenta»** y sólo lo escribe su dueño (§2.10.3) |
| `desactivado_en`, `desactivado_por` | timestamptz, uuid | — |

**`membresia_curso`**

| Columna | Tipo y restricción | Semántica |
|---|---|---|
| `id` | uuid, PK | — |
| `curso_id`, `usuario_id` | uuid, **único `(curso_id, usuario_id)`** | Invariante 1 |
| `rol` | `{PROFESOR, AYUDANTE}` | A-020 |
| `permisos` | `text[]`, con los cuatro `CHECK` de §2.3.10 | Vacío para un profesor |
| `estado` | `{ACTIVA, RETIRADA}` | Nunca se borra la fila |
| `version` | int | Se incrementa en cada cambio de rol o de permisos, y al retirar |
| `es_via_compartida` | boolean `NOT NULL DEFAULT false` | Marca «vía de acceso compartida» (§2.13.2) |
| `org_github_alta_por_app` | boolean `NOT NULL DEFAULT false` | Cierto sólo si la aplicación dio la membresía de organización (§2.9.3) |
| `org_github_estado` | `{NO_APLICA, SIN_CONSENTIMIENTO, PENDIENTE, ACTIVA, ERROR}` | Estado de la membresía en la organización de GitHub (§2.8.3) |
| `org_github_invitada_en`, `org_github_activa_en`, `org_github_reenvios`, `org_github_ultimo_reenvio_en`, `org_github_ultimo_error` | — | Relojes y rastro de la invitación de organización (§2.8.4) |
| `invitada_por`, `creada_en`, `retirada_en`, `retirada_por` | — | Auditoría del alta y del retiro |

**`invitacion_equipo`**

| Columna | Tipo y restricción | Semántica |
|---|---|---|
| `id` | uuid, PK | — |
| `curso_id` | uuid | — |
| `email` | citext | **Lo que el profesor escribió**, para mostrarlo tal cual |
| `email_canonico` | citext `NOT NULL`, **índice único parcial `(curso_id, email_canonico) WHERE estado = 'PENDIENTE'`** | Emparejamiento. **El índice sobre `(curso_id, email)` se retira** (A-185, RG-002) |
| `rol` | `{PROFESOR, AYUDANTE}` | — |
| `permisos` | `text[]`, con los cuatro `CHECK` de §2.3.10 | El conjunto que se vio en el formulario |
| `github_login_declarado` | texto **NULL** | Campo **opcional** del formulario; la invitación se envía igual si no se conoce |
| `token_hash` | texto | **Se guarda el hash, nunca el valor** |
| `estado` | `{PENDIENTE, ACEPTADA, REVOCADA, EXPIRADA}` | §2.5.2 |
| `invitada_por`, `expira_en`, `aceptada_en`, `revocada_en`, `revocada_por` | — | Auditoría |

**`sesion`** y **`sesion_membresia`** se especifican en §2.2.6 y §2.7.1.

### 2.4.4. Criterios de aceptación de §2.4

| # | Comprobación |
|---|---|
| CA-2.4-01 | La misma persona figura como `PROFESOR` en un curso y `AYUDANTE` en otro, y las dos membresías funcionan simultáneamente en la misma sesión |
| CA-2.4-02 | Un segundo `INSERT` de `membresia_curso` para el mismo `(curso_id, usuario_id)` es rechazado por la restricción única |
| CA-2.4-03 | Retirar al último profesor activo de un curso `ACTIVO` se rechaza con el mensaje «promueve antes a otro profesor», y la membresía sigue `ACTIVA` |
| CA-2.4-04 | Degradar a ayudante al último profesor activo se rechaza con el mismo mensaje |
| CA-2.4-05 | `verificar_invariantes` enumera diecisiete invariantes; los invariantes 15, 16 y 17 listan violaciones y **no las reparan** |
| CA-2.4-06 | El esquema desplegado contiene las once entradas de la migración inicial de RG-145 y una prueba de arranque falla si falta cualquiera |
| CA-2.4-07 | No existe la columna `membresia_curso.cuenta_github_id`: la cuenta de GitHub es un atributo de la persona |

---

## 2.5. Incorporación de profesores y ayudantes (R2.1.7, R2.1.8)

### 2.5.1. Mecanismo: invitación nominal, nunca búsqueda

**R2.1.7** y **R2.1.8** se implementan escribiendo una dirección `gmail.com` y enviando un **enlace de
un solo uso con caducidad de siete días** (A-024). **Nunca por búsqueda entre los usuarios
registrados**, por dos motivos: no existe directorio de usuarios que consultar, y buscar por correo
filtraría quién usa la aplicación.

Queda descartado igualmente el **enlace genérico sin destinatario**, porque lo podría usar cualquiera
que lo reciba.

### 2.5.2. Estados de la invitación

`invitacion_equipo.estado` tiene **exactamente cuatro valores y ninguno más**:

| Estado | Se entra cuando | Sale a |
|---|---|---|
| `PENDIENTE` | Un profesor con `equipo.administrar` envía la invitación | `ACEPTADA`, `REVOCADA`, `EXPIRADA` |
| `ACEPTADA` | El destinatario entra con Google y su `email_canonico` coincide | Terminal. Crea o reactiva la `membresia_curso` |
| `REVOCADA` | Un profesor la revoca antes de aceptarse | Terminal, con `revocada_por` y `revocada_en` |
| `EXPIRADA` | `expira_en` vencido con `estado` aún `PENDIENTE` | Terminal a efectos de uso; se puede reenviar, lo que crea una fila nueva |

**`EXPIRADA` se deriva en lectura y en uso** (`expira_en < now()` con `estado = 'PENDIENTE'`): **no la
escribe ningún trabajo periódico**, porque el catálogo de trabajos de A-114 es cerrado y no hace falta
ampliarlo para esto.

### 2.5.3. Flujo de incorporación

| # | Paso | Regla |
|---|---|---|
| 1 | En `/cursos/{id}/equipo`, un profesor pulsa «Incorporar» y elige **rol** | `PROFESOR` o `AYUDANTE` |
| 2 | El formulario precarga los permisos | Rol profesor: `permisos = '{}'`, con la nota de que un profesor tiene los nueve. Rol ayudante: `mapeo.editar` marcado, `nota.publicar` sin marcar, y las siete casillas de §2.3.6 editables |
| 3 | Se escribe la dirección | Validación: dominio exactamente `gmail.com`, aceptando `googlemail.com` normalizado. Se calcula y se guarda `email_canonico` |
| 4 | Campo opcional «cuenta de GitHub» | Se guarda en `invitacion_equipo.github_login_declarado`. **La invitación se envía igual si no se conoce** |
| 5 | Se genera un token aleatorio de 256 bits | **Se guarda su hash** en `token_hash`, nunca el valor. El enlace `https://app.<dominio>/invitaciones/<token>` viaja por correo. Caducidad de **7 días** |
| 6 | El correo sale por el *outbox* | Fila en `mensaje_saliente` con `canal = 'CORREO'`. **Nunca de forma síncrona**: una comunicación es un efecto sobre un tercero y no debe depender de que la petición HTTP del profesor termine bien |
| 7 | La pantalla responde | «Invitación enviada», y la fila aparece de inmediato como `PENDIENTE` con su antigüedad |

**Un profesor no puede invitar dos veces a la misma persona al mismo curso mientras la primera esté
pendiente**: lo impide el índice único parcial `(curso_id, email_canonico) WHERE estado = 'PENDIENTE'`,
y el mensaje de conflicto es «ya hay una invitación pendiente para esa dirección en este curso».

### 2.5.4. La pantalla pública de aceptación

`/invitaciones/{token}` es **una ruta pública sin sesión** (A-231, RG-129, RG-148), y no es accesoria:
es la pantalla donde el evaluador acepta su invitación y donde vive el consentimiento de §2.8.2.
Muestra:

- el nombre del curso;
- el **rol** que se concede;
- **la lista de permisos** que se conceden, con sus etiquetas en español;
- **el texto literal del consentimiento de lectura de todo el código** (§2.8.2), sobre el botón;
- el correo destinatario **enmascarado**;
- el botón «Aceptar la invitación».

`GET /api/invitaciones/{token}` autoriza por **hash del token** y devuelve el correo destinatario
enmascarado. Sus cuatro desenlaces se pintan sin sesión: válida, caducada, revocada, y correo que no
coincide.

### 2.5.5. Aceptación

1. Si el destinatario no tiene sesión, se le lleva a Google con `prompt=select_account`, lo que evita
   el auto-login silencioso a la cuenta equivocada.
2. Al volver, **se compara `email_canonico` del `id_token` con `invitacion_equipo.email_canonico`**.
   Si no coinciden, **la invitación no se acepta** y el mensaje es: «Esta invitación es para *correo
   enmascarado*. Has entrado con *otro correo*. Cambia de cuenta o pide una invitación nueva.»
3. Coincidiendo, **en una sola transacción**: se crea el `usuario` si no existía; se crea o
   **reactiva** la `membresia_curso`; se copian los permisos desde `invitacion_equipo.permisos`; se
   incrementa `version`; se inserta la fila de `sesion_membresia`; la invitación pasa a `ACEPTADA`; se
   escriben en `bitacora` las acciones `INVITACION_ACEPTADA` y `MEMBRESIA_CREADA`; y **se encola
   `sincronizar_acceso_docente`**.
4. La pantalla de bienvenida pide la **cuenta de GitHub** con validación en vivo, si no se declaró en
   la invitación (§2.8.1).

`POST /api/invitaciones/{token}/aceptar` autoriza por **hash del token más coincidencia con
`id_token.email`** (A-182, RG-129).

### 2.5.6. Acciones sobre una invitación pendiente

| Acción | Endpoint | Permiso | Regla |
|---|---|---|---|
| **Revocar** | `DELETE /api/cursos/{id}/equipo/invitaciones/{invitacion_id}` | `equipo.administrar` | `estado = REVOCADA`, con `revocada_por` y `revocada_en`; `bitacora` con `INVITACION_REVOCADA` |
| **Reenviar** | `POST /api/cursos/{id}/equipo/invitaciones/{invitacion_id}/reenviar` | `equipo.administrar` | **Revoca la anterior y crea una nueva con token nuevo**, para que un enlace filtrado deje de servir. **Máximo tres reenvíos por dirección y curso** |
| **Copiar el enlace** | — | `equipo.administrar` | La pantalla ofrece el enlace para entregarlo por otro medio si el correo cayera en *spam* |

### 2.5.7. Cuotas que gobiernan la incorporación

| Límite | Variable | Valor por defecto | Cómo se calcula |
|---|---|---|---|
| Invitaciones de equipo **pendientes por curso** | `LIMITE_INVITACIONES_PENDIENTES` | **20** | `invitacion_equipo WHERE curso_id = ? AND estado = 'PENDIENTE'` |
| Invitaciones emitidas por un usuario en 24 h | `LIMITE_INVITACIONES_DIA` | **50** | `invitada_por = ? AND creado_en > now() - 1 day` |
| Correos de invitación del **despliegue** por día | — | **10** | Cargados a la reserva `MARGEN` de la cuota de correo |

**Sobre el correo:** la cuota de correo es **del despliegue y del día**: 100 correos, repartidos en 60
informe / 20 operativo / 20 margen (A-133, RG-197). **No es una cuota por curso.** El correo de
invitación se carga a la reserva `MARGEN` con el tope propio de 10 al día, y **si se supera queda
`DIFERIDO` con `motivo_estado = 'CUOTA_AGOTADA'`**, se abre la incidencia `CUOTA_CORREO_AGOTADA` y
**nunca se descarta un envío en silencio**.

Un límite alcanzado **no produce un error técnico**: produce un mensaje en español que dice cuál es el
límite, cuánto queda y qué hacer.

### 2.5.8. Criterios de aceptación de §2.5

| # | Comprobación |
|---|---|
| CA-2.5-01 | Invitar a `ana.perez+ramo@gmail.com` y aceptar entrando como `anaperez@gmail.com` funciona: el emparejamiento es por `email_canonico` |
| CA-2.5-02 | Aceptar una invitación entrando con una dirección distinta produce el mensaje nominal y **no crea membresía** |
| CA-2.5-03 | Una invitación con `expira_en` vencido se muestra como caducada sin que ningún trabajo periódico haya escrito ese estado |
| CA-2.5-04 | Reenviar revoca la anterior: el enlace antiguo deja de servir y el nuevo funciona |
| CA-2.5-05 | El cuarto reenvío a la misma dirección y curso se rechaza con el motivo escrito |
| CA-2.5-06 | Un segundo `INSERT` de invitación pendiente para el mismo `(curso_id, email_canonico)` es rechazado por el índice único parcial |
| CA-2.5-07 | La tabla `invitacion_equipo` guarda el hash del token; una consulta directa no devuelve ningún token en claro |
| CA-2.5-08 | El conjunto de permisos que se vio en el formulario es idéntico al que queda en `membresia_curso.permisos` tras aceptar |
| CA-2.5-09 | Invitar a un ayudante con `curso.administrar` marcado es imposible en la interfaz y devuelve `422` por API |
| CA-2.5-10 | `/invitaciones/{token}` se pinta sin sesión y muestra rol, permisos y el texto literal del consentimiento sobre el botón |
| CA-2.5-11 | Superado `LIMITE_INVITACIONES_PENDIENTES`, la pantalla muestra el límite, lo que queda y la acción, no un error técnico |
| CA-2.5-12 | Un segundo profesor incorporado por invitación recibe **los nueve permisos**, sin distinción de «creador» respecto del primero |

---

## 2.6. Qué hace falta y qué no para ser miembro del equipo

### 2.6.1. Regla

**No se exige matrícula en Canvas ni credencial propia para ser co-profesor o ayudante del curso.**
Ser miembro del equipo es **un hecho de la aplicación, no de Canvas** (Q-2.1-43, adoptada sobre
A-020 y A-021). Que un ayudante no exista en Canvas **no le impide hacer nada de lo que la aplicación
le permite**, porque toda escritura en Canvas se ejecuta con la credencial operativa del curso.

**Lo único que exige matrícula en Canvas es pegar una credencial**, y exige las dos cosas a la vez:

| Condición | Detalle |
|---|---|
| `curso.administrar` | **NO CONCEDIBLE a un ayudante**, de modo que **un ayudante nunca puede pegar una credencial, ni la suya** |
| Matrícula de profesor activa en el curso de Canvas vinculado | Se comprueba en el momento del pegado con `GET /courses/:id/enrollments?user_id=self&type[]=TeacherEnrollment`. Rechazo explícito: «este token pertenece a alguien que no es profesor de ese curso» |

**Nadie pega jamás el token de otra persona.** La pantalla sólo ofrece «añadir **mi** credencial», y
sólo la ve quien tiene `curso.administrar` (A-035 regla 1).

### 2.6.2. Lo que la pantalla Equipo muestra sobre credenciales

Por cada **profesor**, una columna «Credencial de Canvas» con tres valores: «operativa», «respaldo
(orden N)» o «sin credencial». Y un aviso permanente cuando el curso tiene **una sola** credencial
válida:

> «Este curso depende de una única credencial de Canvas. Si se revoca, se detienen las comunicaciones
> y la publicación de notas. Cualquier profesor puede añadir la suya como respaldo.»

**Para los ayudantes esa columna no existe y el botón tampoco: no es una omisión, es la decisión.**

### 2.6.3. Criterios de aceptación de §2.6

| # | Comprobación |
|---|---|
| CA-2.6-01 | Un ayudante con los cinco concedibles no ve la columna «Credencial de Canvas» ni el botón «añadir mi credencial», y una llamada directa a la ruta de credenciales devuelve `403` |
| CA-2.6-02 | Un co-profesor sin matrícula en Canvas trabaja con normalidad: crea tareas, reparte correcciones y publica notas, que salen firmadas por el titular de la credencial operativa |
| CA-2.6-03 | Pegar un token cuyo titular no es profesor del curso de Canvas vinculado se rechaza con el mensaje nominal, no con un error genérico |
| CA-2.6-04 | Con una sola credencial válida, la pantalla Equipo muestra el aviso permanente con el texto literal de §2.6.2 |

---

## 2.7. Cambios de permisos y de rol: efecto inmediato

### 2.7.1. Mecanismo

`membresia_curso` lleva una columna `version` que **se incrementa en cada cambio de rol o de permisos,
en la misma transacción que el cambio** (A-023). **La comprobación es por membresía, no por sesión.**

- Existe la tabla **`sesion_membresia (sesion_id, membresia_id, version, refrescada_en)`**, con clave
  primaria `(sesion_id, membresia_id)`. Al iniciar sesión se escribe una fila por cada membresía
  activa del usuario, con la versión vigente en ese instante.
- **En cada petición**, `requiere(permiso, curso_id, rol_minimo=None)` —que ya resuelve la membresía
  del curso del contexto— comprueba **en el mismo `SELECT`** que
  `sesion_membresia.version = membresia_curso.version` **para esa membresía**.
- Si difieren, **la sesión no se destruye entera**: se recarga la fila desde `membresia_curso`, se
  aplican los permisos nuevos y, **si la membresía pasó a `RETIRADA`, se deniega el acceso a ese curso
  con `403`** y el mensaje «ya no formas parte de este curso». **El acceso del usuario a sus otros
  cursos no se toca.**
- **Una membresía nueva** —aceptar una invitación con la sesión ya abierta— inserta su fila de
  `sesion_membresia` en la primera petición que toque ese curso.

**El coste es cero llamadas extra: es el mismo `JOIN` que la autorización ya hacía.**

> El escalar `sesion.version_membresias` de la revisión 1 **queda retirado**: un escalar no puede
> representar N versiones, y A-020 declara normal que una misma persona sea profesora de un curso y
> ayudante de otro (A-023).

### 2.7.2. Cambio de permisos

| Aspecto | Regla |
|---|---|
| Endpoint | `PATCH /api/cursos/{id}/miembros/{membresia_id}/permisos` |
| Permiso | `equipo.administrar` |
| Alcance | **Sólo sobre miembros de rol `AYUDANTE`.** Un profesor no tiene permisos configurables |
| Validación | `422` si el array contiene un permiso NO CONCEDIBLE o un nombre fuera del catálogo |
| Efecto | Incrementa `version` en la misma transacción; **surte efecto de inmediato** |
| Auditoría | `bitacora` con la acción `PERMISOS_CAMBIADOS`, con `antes` y `despues` |

### 2.7.3. Cambio de rol

| Aspecto | Regla |
|---|---|
| Endpoint | `PATCH /api/cursos/{id}/miembros/{membresia_id}/rol` |
| Permiso | `equipo.administrar` |
| **Nunca en silencio** | El diálogo dice exactamente qué cambia antes de confirmar (A-165) |
| Promover a profesor | Concede los nueve permisos y lo dice. `permisos` se escribe **vacío** |
| Degradar a ayudante | **Exige elegir el subconjunto en el mismo diálogo**; no se hereda nada |
| Guarda | Se rechaza si degradaría al último profesor `ACTIVO` de un curso `ACTIVO` |
| Efecto y auditoría | Incrementa `version`; `bitacora` con `PERMISOS_CAMBIADOS` |

### 2.7.4. Jerarquía de administración

**Plana entre profesores.** Cualquier profesor puede editar los permisos de cualquier ayudante,
cambiar el rol de cualquier miembro y retirar a cualquiera, **salvo al último profesor activo**. **Un
ayudante no puede administrar a nadie**, porque `equipo.administrar` es NO CONCEDIBLE.

### 2.7.5. Historial

`/cursos/{id}/equipo` incluye un bloque **«Historial de cambios de equipo»**, que lee `bitacora`
filtrada por curso y responde la pregunta **«¿quién le dio ese permiso y cuándo?»**. Se sirve por
`GET /api/cursos/{id}/equipo/historial` con `curso.ver`.

Acciones de `bitacora` que alimentan este historial, del catálogo cerrado de A-184:
`INVITACION_EMITIDA`, `INVITACION_ACEPTADA`, `INVITACION_REVOCADA`, `MEMBRESIA_CREADA`,
`MEMBRESIA_RETIRADA`, `PERMISOS_CAMBIADOS`, `USUARIO_DESACTIVADO`, `AUTORIZACION_DENEGADA`,
`CUENTA_GITHUB_DOCENTE_VINCULADA`, `CUENTA_GITHUB_DOCENTE_DESVINCULADA`, `CUENTA_GITHUB_RECHAZADA`,
`INVITACION_ORG_REENVIADA`.

### 2.7.6. Criterios de aceptación de §2.7

| # | Comprobación |
|---|---|
| CA-2.7-01 | **Prueba obligatoria:** se abren dos sesiones del mismo usuario en dos cursos, se retira la membresía de uno, y la otra **sigue funcionando** |
| CA-2.7-02 | Retirado un permiso a un ayudante con la sesión abierta, **la petición siguiente** ya lo aplica: no hace falta volver a iniciar sesión |
| CA-2.7-03 | Retirada la membresía con la sesión abierta, la petición siguiente sobre ese curso devuelve `403` con el mensaje «ya no formas parte de este curso» |
| CA-2.7-04 | Aceptar una invitación con la sesión ya abierta permite entrar al curso nuevo sin cerrar sesión |
| CA-2.7-05 | Un `EXPLAIN` de la consulta de autorización muestra que la comprobación de versión no añade ninguna consulta adicional |
| CA-2.7-06 | Promover a profesor deja `permisos = '{}'` y el diálogo previo enumeró lo que se concede |
| CA-2.7-07 | Degradar a ayudante sin elegir subconjunto es imposible: el diálogo no permite confirmar |
| CA-2.7-08 | El historial de `/cursos/{id}/equipo` muestra, para un permiso concedido hoy, quién lo concedió y a qué hora con la zona escrita |

---

## 2.8. La cuenta de GitHub del docente y el acceso de lectura

### 2.8.1. Declaración de la cuenta

La cuenta de GitHub del equipo docente vive en **`usuario.cuenta_github_id`**, con índice único
parcial donde no es nulo. **`membresia_curso.cuenta_github_id` no existe**: la identidad es
`github_user_id`, no cambia al cambiar de curso, y por tanto **la unicidad es global y no por curso**
(A-185, RG-001).

| Aspecto | Regla |
|---|---|
| Dónde se declara | Bloque **«Mi cuenta de GitHub»** de `/perfil`, o la pantalla de bienvenida al aceptar una invitación |
| Endpoint | `PUT /api/perfil/cuenta-github` · `DELETE /api/perfil/cuenta-github` |
| Validación | En vivo con `GET /users/{login}`; se rechaza si resuelve a una organización, comparando `GET /users/{login}` con `GET /orgs/{login}` **sin confiar en el campo `type`** |
| Qué se persiste | El **`github_user_id` numérico** y el **`login` canónico devueltos por la API**, nunca lo tecleado |
| Auditoría | `bitacora` con `CUENTA_GITHUB_DOCENTE_VINCULADA` y `CUENTA_GITHUB_DOCENTE_DESVINCULADA` |
| Un ayudante que no la declara | **Conserva su membresía activa y no bloquea nada**: ve el texto «necesitas vincular tu cuenta de GitHub para abrir el código» en lugar del enlace |

**No se activa «Request user authorization (OAuth) during installation».** La identidad de GitHub del
docente se obtiene con esta declaración validada y **no se persiste ningún token de GitHub de ninguna
persona** (Q-2.1-33, sobre A-038).

**Elegibilidad, comprobada en toda la aplicación.** `PUT /api/perfil/cuenta-github` **rechaza con
`422`**, con mensaje explícito y registro en `bitacora` con `CUENTA_GITHUB_RECHAZADA`, todo
`github_user_id` que (A-187, RG-134, RG-199):

1. tenga un `mapeo_github` **`VIGENTE` en cualquier curso de la aplicación** —no sólo en los del
   declarante—, es decir, sea la cuenta de un estudiante; o
2. ya esté declarado por otro usuario; o
3. no valide contra `GET /users/{login}`, o resulte ser una organización.

**Cuenta no elegible es, en lista cerrada:** la cuenta enlazada desde `usuario.cuenta_github_id` de
cualquier `membresia_curso` `ACTIVA` de ese curso; cualquier miembro de `equipo_github_curso`; el
propietario de la organización; y la cuenta bot de la propia aplicación.

La comprobación es **una sola función de dominio**, `es_cuenta_elegible(github_user_id, curso_id) ->
motivo | None`, en `backend/app/dominio/elegibilidad.py`, y **su alcance es toda la aplicación, no el
curso**: si se acotara por curso, un ayudante podría declarar la cuenta de un estudiante de otro curso
y obtener lectura de todos los repositorios de éste.

### 2.8.2. Consentimiento fechado de lectura de todo el código

**El texto es literal, es el mismo en los tres sitios, y en los dos primeros hay que verlo ANTES de
que la acción ocurra** (A-186, RG-133):

> «Al aceptar, tu cuenta de GitHub entrará en la organización **{organización}** y tendrás **lectura
> de todos los repositorios** de los estudiantes de este curso, no sólo de los que te toque corregir.
> Ese acceso se retira automáticamente si dejas de ser miembro de este curso.»

| # | Dónde aparece | Cómo |
|---|---|---|
| 1 | Página pública `/invitaciones/{token}` | Sobre el botón «Aceptar la invitación», junto al rol y a la lista de permisos que se conceden |
| 2 | Bloque «Mi cuenta de GitHub» de `/perfil` | Sobre el botón que guarda el `login`, con una **casilla que hay que marcar** para habilitarlo. Al marcarla se persiste `usuario.consentimiento_github_en` |
| 3 | `/cursos/{id}/equipo` | Como texto permanente bajo la lista de miembros |

> **Sin ese consentimiento fechado, `sincronizar_acceso_docente` NO incorpora a esa persona a la
> organización ni al equipo `docentes`. Es una guarda, no un aviso.**

Las tres pantallas y la guarda están **operativas desde el 16 de septiembre y no llevan bandera**
(A-186, RG-137).

### 2.8.3. Estado de la membresía de organización

`membresia_curso.org_github_estado` toma **cinco valores** (A-186, RG-198, que amplía RG-096):

| Valor | Cuándo | Qué muestra la columna GitHub de `/cursos/{id}/equipo` |
|---|---|---|
| `NO_APLICA` | `usuario.cuenta_github_id` es nulo | Enlace a `/perfil` para declarar la cuenta, con el texto «sin cuenta declarada: no podrá abrir los repositorios» |
| `SIN_CONSENTIMIENTO` | La cuenta está declarada y `consentimiento_github_en` es nulo | «Pendiente de aceptar la lectura de todo el código del curso», con el enlace al bloque «Mi cuenta de GitHub» y el texto literal |
| `PENDIENTE` | Invitación a la organización enviada, sin aceptar | Fecha de la invitación, botón de reenvío y el enlace directo `https://github.com/orgs/{org}/invitation` |
| `ACTIVA` | La persona aceptó | `login` declarado y fecha de la última revalidación |
| `ERROR` | Tope de reenvíos agotado o error de GitHub | **Motivo literal de GitHub** y botón «reintentar ahora» |

**Doble `CHECK`:** `NO_APLICA` **si y sólo si** `usuario.cuenta_github_id` es nulo; `SIN_CONSENTIMIENTO`
**si y sólo si** la cuenta está declarada y `consentimiento_github_en` es nulo.

### 2.8.4. Relojes, reenvíos y caducidad

**Los relojes cuelgan de `org_github_invitada_en`, no del alta de la membresía** (A-186, RG-198).
Mientras el estado sea `NO_APLICA` o `SIN_CONSENTIMIENTO` **no corre el plazo de cinco días, no se
abre `INVITACION_NO_ACEPTADA`, no se reemite nada y no se consume cuota de correo**.

| Hito | Qué ocurre |
|---|---|
| Emisión | `sincronizar_acceso_docente` ejecuta `PUT /orgs/{org}/memberships/{login}` y escribe `PENDIENTE` con `org_github_invitada_en` |
| Reconciliación | Barrido horario que lee `GET /orgs/{org}/memberships/{login}` para cada membresía activa que no esté `ACTIVA`: `state = active` → `ACTIVA`, `state = pending` → `PENDIENTE` |
| **5 días** en `PENDIENTE` | Se abre `INVITACION_NO_ACEPTADA` con `detalle.ambito = ORGANIZACION_DOCENTE` y **se reemite** el `PUT`, que es idempotente |
| **7 días** sin aceptar | `INVITACION_EXPIRADA` con el mismo ámbito. La invitación a la organización caduca sola a los siete días |
| Tope | **Tres reenvíos, uno cada cinco días.** Agotado el tope: `org_github_estado = ERROR` y la incidencia queda con la acción «avisar a esta persona por correo», que un profesor pulsa y que se carga a la reserva `OPERATIVO` |

Consumo declarado: **≤ 15 invitaciones a la organización por curso, una sola vez**, y ≤ 15 lecturas de
reconciliación por hora y por curso.

### 2.8.5. Qué acceso concede y cómo

| # | Paso | Llamada | Permiso siempre |
|---|---|---|---|
| 1 | Crear el equipo docente | `POST /orgs/{org}/teams` con `name = "docentes"`, `privacy = "closed"` | — |
| 2 | Incorporar a la persona a la organización | `PUT /orgs/{org}/memberships/{login}` | — |
| 3 | Incorporarla al equipo | `PUT /orgs/{org}/teams/{team_slug}/memberships/{login}` | — |
| 4 | Dar lectura al equipo sobre cada repositorio | `PUT /orgs/{org}/teams/{team_slug}/repos/{org}/{repo}` con `{"permission": "pull"}` | **`pull`, nunca `write`, nunca `admin`** |

**Vía de respaldo**, si el equipo no puede crearse: `PUT /repos/{org}/{repo}/collaborators/{login}` con
`{"permission": "pull"}` por cada miembro con `curso.ver`, persistido con `via = COLABORADOR`.
`equipo_github_curso.via_efectiva` declara cuál quedó activa.

**Incorporar un ayudante después no toca ningún repositorio:** basta añadirlo al equipo, y hereda la
lectura. Ése es el motivo de fondo para preferir el equipo al colaborador individual.

`membresia_curso.org_github_alta_por_app` se escribe a `true` **en la misma transacción en que el `PUT
/orgs/{org}/memberships/{login}` devuelve éxito**, y **nunca** para quien ya era miembro u *owner* de
la organización antes. **La aplicación deshace lo que hizo y nada más** (A-188, RG-136).

### 2.8.6. Cuándo se pinta el enlace al repositorio

El enlace `https://github.com/{org}/{repo}/tree/{sha}` **se pinta sólo si se cumplen las dos
condiciones, y las dos se comprueban antes de pintar** (RG-097):

1. `acceso_docente_repositorio` de ese repositorio está en **`CONCEDIDO`**;
2. si `equipo_github_curso.via_efectiva = TEAM`, la **membresía de organización de quien está mirando**
   está en **`ACTIVA`**. Con `via_efectiva = COLABORADOR` la segunda condición se evalúa sobre la fila
   de esa persona.

Qué se muestra cuando falla la segunda, en lugar de un enlace que dará `404`:

| Situación de quien mira | Texto |
|---|---|
| `org_github_estado = NO_APLICA` | «Necesitas vincular tu cuenta de GitHub para abrir el código», con enlace a `/perfil` |
| `org_github_estado = SIN_CONSENTIMIENTO` | «Pendiente de aceptar la lectura de todo el código del curso», con el enlace al bloque «Mi cuenta de GitHub» |
| `org_github_estado = PENDIENTE` | «Tu invitación a la organización *org* de GitHub está pendiente: acéptala y vuelve», con el enlace directo y la fecha de envío |
| `org_github_estado = ERROR` | El motivo literal de GitHub y el botón «reenviar invitación», con la acción registrada en `bitacora` |

La comprobación vive en la función pura `puede_abrir_repositorio(usuario, repositorio) -> Resultado`
de `backend/app/dominio/`, y la usan la pantalla de corrección, el timeline y el enlace de comparación.

### 2.8.7. Criterios de aceptación de §2.8

| # | Comprobación |
|---|---|
| CA-2.8-01 | Declarar un `login` que resuelve a una organización se rechaza con `422` y mensaje explícito |
| CA-2.8-02 | Declarar el `login` de un estudiante con `mapeo_github` `VIGENTE` **en otro curso** se rechaza con `422` y queda en `bitacora` con `CUENTA_GITHUB_RECHAZADA` |
| CA-2.8-03 | Declarar un `login` ya declarado por otra persona se rechaza con `422` por el índice único parcial |
| CA-2.8-04 | Con la cuenta declarada y **sin** marcar la casilla de consentimiento, `sincronizar_acceso_docente` **no llama a GitHub** y la columna GitHub muestra `SIN_CONSENTIMIENTO` |
| CA-2.8-05 | Con `SIN_CONSENTIMIENTO` no se abre `INVITACION_NO_ACEPTADA` a los cinco días ni se consume cuota de correo |
| CA-2.8-06 | El texto del consentimiento es **idéntico, palabra por palabra**, en `/invitaciones/{token}`, en `/perfil` y en `/cursos/{id}/equipo` |
| CA-2.8-07 | `sincronizar_acceso_docente` repite la comprobación de elegibilidad **inmediatamente antes** de las dos escrituras; si falla, **no llama**, abre `CUENTA_DOCENTE_ES_DE_ESTUDIANTE` y avisa por correo a los profesores |
| CA-2.8-08 | Una prueba automatizada **falla si aparece una llamada a `PUT /orgs/{org}/memberships/` con un login que pertenece a un `mapeo_github` vigente**; la prueba se conserva **además** de la guarda, no en su lugar |
| CA-2.8-09 | Un ayudante con la invitación de organización `PENDIENTE` no ve el enlace al repositorio, sino el texto con el enlace directo de aceptación y la fecha de envío |
| CA-2.8-10 | `org_github_alta_por_app` queda en `false` para el profesor que ya era *owner* de la organización antes |
| CA-2.8-11 | El permiso concedido al equipo sobre cada repositorio es `pull`; no existe ninguna llamada que conceda `push` ni `admin` a un docente |

---

## 2.9. Retiro y reincorporación (R2.1.9)

### 2.9.1. Regla

El retiro de un ayudante o de un profesor es **baja lógica por curso, nunca borrado físico, y con
invalidación inmediata de la sesión en ese curso y sólo en ese curso** (A-025, A-165, A-188).

> **R2.1.9 no está cumplido si la persona retirada sigue pudiendo leer el código de los estudiantes.**
> Por eso la revocación en GitHub es parte del requisito y no un extra (A-025 punto 6, A-188).

### 2.9.2. La transacción del retiro

`POST /api/cursos/{id}/equipo/{membresia_id}/retiro`, con `requiere('equipo.administrar', curso_id)`.
**Se ejecuta entera o no se ejecuta:**

| # | Paso | Detalle |
|---|---|---|
| 1 | `membresia_curso.estado = RETIRADA` | Con `retirada_en` y `retirada_por` |
| 2 | Se incrementa `version` | Revoca sus sesiones **de ese curso** en la petición siguiente (§2.7.1) |
| 3 | Se vacían sus permisos | `permisos = '{}'` |
| 4 | Asignaciones de corrección | Las filas de `asignacion_correccion` cuya corrección no esté `PUBLICADA` pasan a `estado = SIN_CORRECTOR` y su `membresia_id` queda a nulo; el valor anterior se conserva en `bitacora` con `antes`/`despues`. Se abre una incidencia `CORRECCION_SIN_CORRECTOR` por curso, con recuento y enlace directo al reparto prefiltrado |
| 5 | Autoría | **Se conserva íntegra la autoría de lo que ya corrigió y publicó.** `correccion.corrector_usuario_id`, `publicacion_nota` y `bitacora` no se tocan |
| 6 | Suscripción al informe | `suscripcion_informe.activa = false` para ese curso. **No se reactiva sola al reincorporar**: la decide la persona desde `/cursos/{id}/mis-notificaciones` |
| 7 | Se encola `revocar_acceso_docente` | §2.9.3 |
| 8 | Si el retirado es **profesor** | §2.9.4 |
| 9 | `bitacora` | `MEMBRESIA_RETIRADA`, con actor, instante, `antes` y `despues` |

**Guarda:** la acción se rechaza si es **el último profesor `ACTIVO`** de un curso `ACTIVO`, con el
mensaje «promueve antes a otro profesor». Para un ayudante no hay invariante que lo impida.

**El retiro no se bloquea por trabajo pendiente.** No se reasigna nada automáticamente: la
reasignación automática repartiría trabajo a personas que no lo aceptaron y **cambiaría en silencio
quién corrige a quién**. Bloquear el retiro hasta reasignar convertiría una acción de seguridad en un
trámite y dejaría a la persona con acceso mientras tanto.

### 2.9.3. Los tres planos de revocación en GitHub

Dentro del trabajo `revocar_acceso_docente`, **en este orden** (A-188, RG-136, A-190):

| # | Plano | Llamada | Condición |
|---|---|---|---|
| 1 | **Equipo** (vía principal) | `DELETE /orgs/{org}/teams/{team_slug}/memberships/{login}` | **Siempre.** Una sola llamada revoca la lectura sobre todos los repositorios concedidos por el equipo |
| 2 | **Colaborador** (vía de respaldo) | `DELETE /repos/{org}/{repo}/collaborators/{login}` | Por **cada** fila de `acceso_docente_repositorio` con `via = COLABORADOR` y `estado = CONCEDIDO` de ese curso: un permiso de colaborador directo **no** se retira al salir de un equipo |
| 3 | **Membresía de la organización** | `DELETE /orgs/{org}/memberships/{login}` | **Si y sólo si `membresia_curso.org_github_alta_por_app = true`** |

**Cada plano hace su lectura previa** —`GET /orgs/{org}/teams/{slug}/memberships/{login}`,
`GET /repos/{o}/{r}/collaborators/{login}`, `GET /orgs/{org}/memberships/{login}`— para que un
reintento sobre algo ya revocado sea un *no-op* y no un error.

**Manejo de fallos:** reintento con retroceso exponencial, *jitter* y respeto de `retry-after`.
Agotados los cuatro intentos, el trabajo queda **`REQUIERE_ATENCION`** con su error literal,
**reintentable a mano desde `/operacion`**, y se abre la incidencia bloqueante
**`ACCESO_DOCENTE_NO_REVOCADO`** con el texto: «*Nombre* fue retirado del curso pero GitHub aún no ha
confirmado la revocación de su acceso de lectura. Reintenta, o quítalo a mano desde GitHub.»
**Nada se pierde en silencio.**

**Lo que nunca se revoca:** el acceso de los **estudiantes** a sus propios repositorios, y ningún
acceso que la aplicación no otorgara.

### 2.9.4. Retirar a un profesor arrastra sus credenciales de Canvas

**Todas las filas de `credencial_canvas` de ese profesor en ese curso pasan a `RETIRADA` en la misma
transacción del retiro**, y se dispara la **promoción automática**: la siguiente credencial `VALIDA`
del orden de respaldo pasa a `orden_respaldo = 0`, respetando el único parcial `curso_id` donde
`orden_respaldo = 0` (A-188, RG-139).

**El retiro no se bloquea por ser el titular de la única credencial**: el único invariante duro es el
del último profesor `ACTIVO`. Sin respaldo válido, el curso pasa a **`CANVAS_DESVINCULADO`**, se abre
`CANVAS_CREDENCIAL_INVALIDA`, **se detienen las lecturas de Canvas**, **las escrituras se encolan en
`ESPERANDO_CREDENCIAL` y no se descartan**, y lo que no depende de Canvas —aprovisionamiento, ingesta
de actividad, tableros, timeline y captura de versiones— **sigue funcionando**. Se avisa por correo a
todos los profesores del curso, con cargo a la reserva `OPERATIVO`.

**La misma regla rige cuando el retiro lo causa el cierre de cuenta del titular** (§2.10.3).

### 2.9.5. La confirmación nominal previa

El diálogo de `/cursos/{id}/equipo` enumera, **antes de confirmar y con números reales**, alimentado
por `GET /api/cursos/{id}/miembros/{membresia_id}/impacto-retiro`:

- «se cerrarán sus sesiones de este curso»;
- «perderá la lectura de los N repositorios del curso»;
- «quedarán M entregas sin corrector»;
- «su historial de correcciones se conserva».

**Si el retirado es profesor**, se añade **una frase más, la que corresponda de estas dos** (A-188,
RG-139):

- «Esta persona es la titular de la credencial operativa. A partir de ahora la aplicación escribirá en
  Canvas como *nombre del sucesor*.»
- «Esta persona es la titular de la credencial operativa y **no hay ninguna credencial de respaldo
  válida**. **Este curso quedará sin poder escribir en Canvas** hasta que un profesor pegue la suya.»

Un solo botón de confirmación, con el texto **«Retirar a *nombre* del curso»**, y un enlace secundario
**«Reasignar antes sus correcciones»**, que lleva al reparto sin retirar a nadie.

### 2.9.6. Reincorporación

| Aspecto | Regla |
|---|---|
| Endpoint | `POST /api/cursos/{id}/equipo/{membresia_id}/reincorporacion` |
| Permiso | `equipo.administrar` |
| Efecto | **Reactiva la misma fila de `membresia_curso`**, conservando historial y autoría. **No se crea una fila nueva** |
| Permisos | **Se vuelve a elegir el subconjunto**; nunca se restauran en silencio los que tenía |
| Suscripción al informe | **No se reactiva sola** |
| GitHub | Se encola `sincronizar_acceso_docente`, sujeto a las guardas de elegibilidad y de consentimiento de §2.8 |
| Visibilidad | Un miembro retirado **no desaparece** de `/cursos/{id}/equipo`: se muestra con «Retirado el dd-MM-yyyy HH:mm (zona)» y el botón «Reincorporar» |

### 2.9.7. Qué ve una persona retirada

| Ámbito | Qué ocurre |
|---|---|
| `/cursos` | **El curso no aparece.** Los cursos con membresía `RETIRADA` no se listan, ni siquiera en gris: ver el curso ya es acceso |
| URL directa del curso | **`403` con el mensaje explícito** de que fue retirada de ese curso, **no un `404` genérico**: el mensaje explícito es mejor guía y no revela nada que la persona no supiera |
| Otros cursos | **Intactos.** La comprobación es por membresía |
| Informe diario | Deja de recibirlo desde el ciclo siguiente |
| GitHub | Recibe `404` al abrir cualquier repositorio del curso, una vez completada la revocación |

### 2.9.8. Criterios de aceptación de §2.9

| # | Comprobación |
|---|---|
| CA-2.9-01 | Retirado un miembro, **las tres llamadas de revocación se ejecutan**, la lectura previa de cada plano queda en la bitácora del trabajo, y el `login` retirado **recibe `404` al abrir un repositorio del curso** |
| CA-2.9-02 | Retirar no borra ninguna fila: la membresía, las asignaciones, las correcciones, las publicaciones y la bitácora siguen existiendo |
| CA-2.9-03 | Las asignaciones pendientes del retirado quedan en `SIN_CORRECTOR` con incidencia visible en Pendientes, en el estado de corrección y en el informe diario, leyendo **la misma tabla `incidencia`** |
| CA-2.9-04 | El diálogo de confirmación muestra números reales, no marcadores de posición, y nombra a la persona en el botón |
| CA-2.9-05 | Retirar al titular de la credencial operativa con respaldo válido promueve la siguiente y muestra la primera frase adicional; sin respaldo válido, muestra la segunda y el curso pasa a `CANVAS_DESVINCULADO` |
| CA-2.9-06 | Con el curso en `CANVAS_DESVINCULADO`, la captura de versiones y el aprovisionamiento **siguen funcionando**, y las escrituras a Canvas quedan en `ESPERANDO_CREDENCIAL` |
| CA-2.9-07 | `DELETE /orgs/{org}/memberships/{login}` **no se ejecuta** para quien ya era miembro u *owner* antes de la aplicación |
| CA-2.9-08 | Agotados los cuatro reintentos, el trabajo queda `REQUIERE_ATENCION` con el error literal y se abre `ACCESO_DOCENTE_NO_REVOCADO` |
| CA-2.9-09 | Reincorporar reactiva la misma `membresia_curso` —mismo `id`— y exige elegir permisos de nuevo |
| CA-2.9-10 | Una persona retirada que abre la URL del curso recibe `403` con mensaje explícito, y sus otros cursos siguen accesibles en la misma sesión |
| CA-2.9-11 | Una prueba de arquitectura falla la construcción si aparece `DELETE /repos/{owner}/{repo}` en `backend/app/adaptadores/`: nunca se borra un repositorio, un commit, un tag de entrega ni una nota publicada |

---

## 2.10. Administración de la propia cuenta: `/perfil`

### 2.10.1. Qué contiene `/perfil`

Es el plano 2 de la administración (A-165). **Exige sesión y ningún permiso**, porque todo lo que hay
son acciones sobre uno mismo.

| Bloque | Contenido | Endpoints |
|---|---|---|
| **Identidad** | Nombre visible **editable**. **El correo no es editable**, se muestra en monoespaciado y con la nota de que es la identidad de Google y la clave de `usuario` | `GET/PATCH /api/perfil` |
| **Mi cuenta de GitHub** | Declaración con validación en vivo, casilla de consentimiento con el texto literal, fecha del consentimiento, y desvinculación | `PUT/DELETE /api/perfil/cuenta-github` |
| **Mis identidades de Canvas** | Una fila por instancia, con su `canvas_base_url` visible, y la posibilidad de desvincular | `GET/DELETE /api/perfil/identidades-canvas` |
| **Mis sesiones** | Sesiones abiertas con su agente y su antigüedad; cerrarlas todas | `GET/DELETE /api/perfil/sesiones` |
| **Notificaciones** | Control «regenerar mis enlaces de baja» | `POST /api/perfil/regenerar-enlaces` |
| **Cerrar mi cuenta** | §2.10.3 | `DELETE /api/perfil` |

**Si el correo de Google cambió**, este bloque muestra el aviso correspondiente (§2.2.5).

### 2.10.2. Qué NO contiene `/perfil`

No contiene ninguna acción sobre otra persona. **Un profesor no puede cerrar la cuenta de otro, ni
editar su nombre, ni ver sus sesiones.** Eso requeriría un rol de administrador global que esta
aplicación no tiene y que el enunciado no pide (A-165).

### 2.10.3. Cerrar la propia cuenta

**`usuario.activo = false` significa «esta persona cerró su cuenta» y sólo lo escribe su propio
dueño**, desde `/perfil`, con confirmación (A-165).

**Comprobación previa, obligatoria:** el cierre **se rechaza si esa persona es la única profesora
`ACTIVA` de algún curso `ACTIVO`**. La pantalla **lista esos cursos, enlaza a cada uno** y exige, para
cada uno, promover a otro profesor o archivar el curso antes de continuar. La comprobación vive en el
servicio de dominio `puede_cerrar_cuenta(usuario) -> lista de cursos bloqueantes`.

**Si el cierre procede, en una sola transacción y con los trabajos que encola:**

| # | Efecto |
|---|---|
| 1 | Se revocan **todas** sus sesiones |
| 2 | Sus membresías activas pasan a `RETIRADA` con el procedimiento completo de §2.9.2, incluida la revocación en GitHub por los tres planos de §2.9.3 |
| 3 | Sus credenciales de Canvas pasan a `RETIRADA` y se promueve la siguiente del orden de respaldo; si no había respaldo, ese curso pasa a `CANVAS_DESVINCULADO` con la degradación controlada de §2.9.4 |
| 4 | **No puede volver a iniciar sesión**: el motivo 7 de §2.2.7 |
| 5 | `bitacora` con `USUARIO_DESACTIVADO` |

**No se borra la fila** (A-030, A-190). Su autoría, sus correcciones publicadas y su bitácora se
conservan íntegras, y **la interfaz lo muestra como «cuenta cerrada» donde aparezca**. La reapertura
es una operación manual del equipo, registrada en `bitacora`.

### 2.10.4. Criterios de aceptación de §2.10

| # | Comprobación |
|---|---|
| CA-2.10-01 | El campo de correo de `/perfil` no es editable y lleva la nota de que es la identidad de Google |
| CA-2.10-02 | Cerrar sesión en «Mis sesiones» invalida las demás sesiones abiertas de esa persona en la petición siguiente |
| CA-2.10-03 | Intentar cerrar la cuenta siendo la única profesora activa de un curso activo se rechaza y **la pantalla lista los cursos bloqueantes con enlace a cada uno** |
| CA-2.10-04 | Tras cerrar la cuenta, un nuevo acceso con la misma cuenta de Google produce el motivo 7 con la fecha del cierre |
| CA-2.10-05 | Tras cerrar la cuenta, sus correcciones publicadas siguen existiendo y la interfaz muestra su nombre con la marca «cuenta cerrada» |
| CA-2.10-06 | Ninguna ruta permite a un usuario modificar el perfil, las sesiones o el estado de otra persona; existe una prueba que lo intenta y espera `403` o `404` |

---

## 2.11. Cómo se aplica la autorización

### 2.11.1. La dependencia única

**Una única dependencia de FastAPI, `requiere(permiso, curso_id, rol_minimo=None)`**, resuelve la
membresía activa, comprueba el permiso, contrasta `sesion_membresia.version` contra
`membresia_curso.version` en el mismo `SELECT` y adjunta el contexto a la petición (A-022, A-179).

| Regla | Enunciado |
|---|---|
| 1 | **Ninguna ruta de curso se registra sin ella**, y una puerta de construcción falla si aparece una |
| 2 | **Toda consulta al modelo se filtra por el `curso_id` del contexto.** No existe consulta que reciba un identificador de entidad sin acotar por curso, lo que cierra el acceso indirecto a datos de otro curso |
| 3 | **El frontend oculta lo que el usuario no puede hacer, pero ocultar no es autorizar.** La comprobación real está siempre en el servidor |
| 4 | `rol_minimo='PROFESOR'` se usa **sólo** en las seis acciones de §2.3.9 |

Para que la interfaz no adivine, `GET /api/cursos/{id}/contexto` devuelve **rol y permisos efectivos**
del usuario en ese curso, y es la única fuente de la que el frontend decide qué pinta.

### 2.11.2. La regla de tres niveles de la interfaz

No es «ocultar todo» ni «deshabilitar todo»: el comportamiento depende de si el permiso es
**recuperable** o no (Q-2.1-46, adoptada).

| Nivel | Qué | Comportamiento | Por qué |
|---|---|---|---|
| **1** | Pantallas y entradas de navegación que exigen un permiso **NO CONCEDIBLE**: `/cursos/{id}/ajustes`, el asistente de vinculación, y las acciones de `equipo.administrar` en `/cursos/{id}/equipo` | **Ocultas** para el ayudante | Un ayudante **nunca** puede obtener esos permisos. Mostrar una puerta permanentemente cerrada es ruido y sugiere que puede pedir algo que no existe |
| **2** | Acciones dentro de una pantalla que el ayudante **sí ve**, cuyo permiso es **concedible** | **Visibles y deshabilitadas, con el motivo escrito** en el propio control y al pasar el cursor: «Necesitas el permiso *Publicar nota*. Pídeselo a un profesor del curso» | Es recuperable, y hace el sistema de permisos **verificable en la revisión**: la única forma de comprobar que los permisos existen usando la herramienta es verlos negados con nombre |
| **3** | Servidor | **Siempre `403` con `requiere(...)`**, sin excepción | **Ocultar no es autorizar** |

Reglas complementarias:

- **La navegación del curso es la misma para los dos roles** —Personas, Pendientes, Tareas,
  Corrección, Equipo, Mis notificaciones—, con la única diferencia del nivel 1. Un ayudante entra al
  curso y ve el mismo mapa que su profesor.
- **La vista por defecto de un ayudante al entrar en Corrección es «Mis asignaciones»**: no tiene que
  buscar nada, que es literalmente **R2.7.2**.
- **Un control deshabilitado por falta de permiso de la aplicación y uno deshabilitado por falta de
  permiso en Canvas se distinguen en el texto:** «Necesitas el permiso *Enviar comunicaciones*» frente
  a «Tu curso de Canvas no permite publicar anuncios con esta credencial».
- Existe **un único componente `<AccionProtegida permiso="…">`** con los tres comportamientos y **un
  solo lugar donde se decide cuál aplica**, alimentado por la tabla de §2.3.2.

### 2.11.3. Códigos de respuesta

| Situación | Código | Cuerpo |
|---|---|---|
| Miembro activo del curso sin el permiso exigido | **`403`** | Código `PERMISO_INSUFICIENTE`, permiso exigido y etiqueta en español |
| Miembro activo con el permiso pero sin el rol de §2.3.9 | **`403`** | Código `PERMISO_INSUFICIENTE`, con el motivo de rol escrito |
| Membresía `RETIRADA` en ese curso | **`403`** | Mensaje «ya no formas parte de este curso» |
| Sin membresía en ese curso | **`404`** | Sin confirmar la existencia del recurso |
| Prefijo `/api/operacion/**` sobre un curso donde no es profesor | **`404`** | Nunca `403`, para no confirmar su existencia |
| Array de permisos inválido | **`422`** | Nombre del permiso rechazado y motivo |
| Ruta no registrada bajo el perfil de alcance vigente | **`404` de enrutado** | Nunca un `500` ni una pantalla vacía |

### 2.11.4. La superficie sin sesión

**El receptor de webhooks no es el único endpoint sin autenticación de usuario.** Ésta es la
superficie sin sesión completa, y **ninguna otra ruta puede quedar fuera de `requiere(...)` sin
figurar aquí** (A-182, RG-129). Se registran en un **router público único**, fuera del middleware de
sesión y de CSRF, con la dependencia `limitar(clave, limite)` sobre la tabla `cubo_tasa`:

| Ruta | Qué la autoriza | Límite |
|---|---|---|
| `POST /webhooks/github` | Firma `X-Hub-Signature-256` sobre el cuerpo crudo, en tiempo constante | 600/min por `installation_id`, contado **después** de validar la firma |
| `GET` y `POST /auth/google/inicio` | Ninguna: inicia el flujo OIDC | 30/min por IP truncada |
| `GET /auth/google/callback` | `state` firmado de un solo uso y cookie `oidc_txn` | 30/min por IP truncada |
| `GET` y `POST /auth/confirmar` | Camino degradado, con token anti-CSRF de formulario | 30/min por IP truncada |
| `GET /github/instalacion/callback` | `state` firmado | 30/min por IP truncada |
| `GET` y `POST /baja/{token}` | Firma del token y alcance `(curso_id, usuario_id)` | 20/min por IP truncada |
| `GET /r/{t}` | Firma del token de traza | 60/min por IP truncada |
| `GET /api/invitaciones/{token}` | Hash del token; devuelve el correo destinatario **enmascarado** | 20/min por IP truncada |
| `POST /api/invitaciones/{token}/aceptar` | Hash del token más coincidencia con `id_token.email` | 20/min por IP truncada |
| `/invitaciones/{token}` (página) | Ninguna: pinta lo que devuelve `GET /api/invitaciones/{token}` | 60/min por IP truncada |
| `GET /api/capacidades` | Ninguna: devuelve sólo el perfil de alcance y las banderas activas | 60/min por IP truncada |
| `/alcance` | Ninguna | 60/min por IP truncada |
| `/privacidad` | Ninguna | 60/min por IP truncada |
| `GET /salud` | Ninguna; no toca la base de datos | Sin límite |
| `GET /estado` (forma anónima) | Ninguna | 20/min por IP truncada |
| `POST /interno/latido` | HMAC del vigilante externo | 12/min por token del vigilante |

**Son dieciséis.** **Todo lo demás bajo `/api/**` exige sesión, con 300/min por `sesion_id`.**

**`GET /estado` tiene dos respuestas, no una:** la **anónima**, con booleanos y contadores agregados y
**sin un solo nombre ni identificador de curso**, que es la que consultan los monitores externos; y la
**completa**, con desglose por curso, que exige sesión y queda acotada a los cursos donde el
solicitante es profesor activo.

**Discrepancia resuelta por precedencia.** Los limitadores de esta tabla son los normativos y sustituyen
a `LIMITE_ACCESO_IP` (10 por 10 minutos) y `LIMITE_MUTACIONES_SESION` (30 por minuto) de Q-2.1-08, que
**quedan anulados** por RG-129. Las cuotas de negocio de esa misma respuesta —cursos e invitaciones—
se conservan, porque ninguna regla RG las contradice.

### 2.11.5. Dónde vive el rastro de una autorización denegada

**Dos destinos, sin zona intermedia sin decidir**, resueltos por un manejador central de `403` y `404`
con el mismo contexto que ya resolvió `requiere(...)` (A-183, RG-142):

| # | Destino | Cuándo | Qué se escribe |
|---|---|---|---|
| 1 | **`bitacora`** | Un `403` sobre una ruta de curso emitido a alguien que **sí** tiene membresía `ACTIVA` en ese curso, **vaya la ruta de escritura o de lectura** | Actor, `curso_id`, **`permiso_exigido`**, **`ruta`**, **`metodo`** e identificador del recurso, con la acción `AUTORIZACION_DENEGADA` |
| 2 | **Log estructurado** | Un `403` o `404` emitido a quien **no** tiene membresía activa en ese curso, y todo rechazo previo a la sesión | `motivo`, `ip_truncada` y, cuando exista, `usuario_id`. **Nunca a `bitacora`** y **nunca con el correo completo** de quien no llegó a ser usuario |

**Vigilancia.** Existe una alerta por correo, **operativa desde el 16 de septiembre**, que se dispara
cuando una misma `sesion_id` acumula **20 respuestas `403` o `404` de recurso ajeno en 10 minutos**, o
una misma IP truncada acumula **50 en 10 minutos**. Abre la incidencia **`DENEGACIONES_ANOMALAS`** y
aparece como fila propia en `/operacion` con el recuento de las últimas 24 horas, acotada por curso
(A-177 quinta alerta, RG-143).

### 2.11.6. Criterios de aceptación de §2.11

| # | Comprobación |
|---|---|
| CA-2.11-01 | La puerta de construcción falla si se registra una ruta bajo `/api/cursos/{curso_id}` sin la dependencia `requiere(...)` |
| CA-2.11-02 | La puerta de construcción falla si aparece registrada una ruta sin dependencia de sesión que no figure en la tabla de §2.11.4 |
| CA-2.11-03 | Un ayudante con `curso.ver` en el curso A recibe `404` al pedir por identificador una entidad del curso B |
| CA-2.11-04 | Ocultar un control en la interfaz nunca basta: una llamada directa a su endpoint sin el permiso devuelve `403` |
| CA-2.11-05 | Un ayudante ve el control «Publicar nota» **deshabilitado con el motivo escrito**, no oculto, cuando no tiene ese permiso |
| CA-2.11-06 | Un ayudante **no ve** la entrada de navegación a `/cursos/{id}/ajustes` ni al asistente de vinculación |
| CA-2.11-07 | Un `403` a un miembro activo deja fila en `bitacora` con `permiso_exigido`, `ruta` y `metodo`; un `404` a quien no es miembro **no** deja fila en `bitacora` |
| CA-2.11-08 | Veinte `403` de la misma sesión en 10 minutos abren `DENEGACIONES_ANOMALAS` y disparan el correo dentro del ciclo de vigilancia |
| CA-2.11-09 | La forma anónima de `GET /estado` no contiene ningún nombre ni identificador de curso |
| CA-2.11-10 | Una mutación sin cabecera `X-CSRF-Token` es rechazada; existe una prueba automatizada que falla si aparece `allow_origins=["*"]` |

---

## 2.12. Qué puede hacer cada rol en cada pantalla

### 2.12.1. Matriz de pantallas

«Ayudante» en la columna de acciones significa «ayudante **con ese permiso concedido**». Los permisos
implícitos `curso.ver` y `correccion.corregir` los tiene todo miembro activo.

| Pantalla | Ruta | Permiso para leer | Acciones y permiso que exigen |
|---|---|---|---|
| **Acceso** | `/acceso` | — | Entrar con Google |
| **Aceptar invitación** | `/invitaciones/{token}` | — (pública) | Aceptar la invitación: token válido más coincidencia de correo |
| **Mi perfil** | `/perfil` | Sesión | Editar nombre; declarar y desvincular cuenta de GitHub con su consentimiento; ver y desvincular identidades de Canvas; ver y cerrar sesiones; regenerar enlaces de baja; **cerrar mi cuenta**. **Sin permiso, sólo sobre uno mismo** |
| **Mis cursos** | `/cursos` | Sesión | Crear curso: **cualquier usuario con sesión** (**R2.1.3**) |
| **Asistente de vinculación** | `/cursos/nuevo`, `/cursos/{id}/vinculacion` | `curso.administrar` | Pegar la credencial propia, instalar la aplicación de GitHub, ejecutar el checklist, pruebas de escritura: `curso.administrar`. **Oculto para un ayudante (nivel 1)** |
| **Equipo** | `/cursos/{id}/equipo` | `curso.ver` | Invitar, editar permisos, cambiar rol, retirar, reincorporar, revocar y reenviar invitación, ver historial: `equipo.administrar`. **Los controles están ocultos para un ayudante (nivel 1); la lista, la columna GitHub y el texto del consentimiento sí se leen con `curso.ver`** |
| **Mis notificaciones** | `/cursos/{id}/mis-notificaciones` | `curso.ver` | Cambiar **mi** suscripción: **sin permiso**. Nadie puede dar de alta a otro |
| **Personas** | `/cursos/{id}/personas` | `curso.ver` | Crear y publicar la tarea de registro y el interruptor de recordatorio: `comunicacion.enviar`. Editar cuentas de GitHub vinculadas, importar CSV, reenviar invitación al estudiante: `mapeo.editar`. «Sincronizar ahora»: `curso.ver`, porque encola y no llama |
| **Pendientes** | `/cursos/{id}/pendientes` | `curso.ver` | Resolver conflicto de cuenta vinculada, escribir la cuenta, reenviar: `mapeo.editar`. Confirmar `POSIBLE_FUSION_CANVAS`: `mapeo.editar` **y rol `PROFESOR`**. Enviar recordatorio: `comunicacion.enviar` |
| **Tareas** | `/cursos/{id}/tareas` | `curso.ver` | Crear tarea: `tarea.administrar` |
| **Tarea** | `/cursos/{id}/tareas/{id}` | `curso.ver` | Vincular entregas, repositorio base y archivos, forzar aprovisionamiento, reintentar, «capturar ahora»: `tarea.administrar`. **Archivar y desarchivar los repositorios: `tarea.administrar` y rol `PROFESOR`.** Recapturar con otra fecha de corte y fijar un SHA: `tarea.administrar` y rol `PROFESOR`. Interruptores de comunicaciones y envío manual: `comunicacion.enviar` |
| **Repositorio** | `/cursos/{id}/tareas/{id}/repos/{id}` | `curso.ver` | Reintentar acceso docente: `tarea.administrar` |
| **Corrección** | `/cursos/{id}/correccion` | `curso.ver` | «Mis asignaciones» y **«Estado de la entrega»: siempre visibles** para todo miembro activo. Abrir en modo edición y guardar borrador: `correccion.corregir` **acotado por propiedad**. «Repartir»: `correccion.asignar`. **Publicar nota**: `nota.publicar` |
| **Ajustes del curso** | `/cursos/{id}/ajustes` | `curso.administrar` | Credenciales y su titular, revinculación, zona horaria, roles de estudiante adicionales, canal activo, archivar el curso: `curso.administrar`. **Oculto para un ayudante (nivel 1)** |
| **Operación** | `/operacion` | **Rol `PROFESOR`**, acotado a los cursos donde lo es | Reintentar trabajo `REQUIERE_ATENCION`, ejecutar un periódico, salir de `MODO_RECUPERACION`: rol `PROFESOR`. **`404` para quien no es profesor de ningún curso** |
| **Alcance** | `/alcance` | — (pública) | Sólo lectura |
| **Privacidad** | `/privacidad` | — (pública) | Sólo lectura |

### 2.12.2. Endpoints de administración de equipo

**[DECISION NUEVA]** Las respuestas de alcance nombraban las rutas de equipo de dos maneras
incompatibles —`/api/cursos/{id}/invitaciones/...` en Q-2.1-42 frente a
`/api/cursos/{id}/equipo/invitaciones` en RG-121, y `/miembros/{id}/retirar` en Q-2.1-49 frente a
`/equipo/{id}/retiro` en RG-139—. Mandan las formas que fija el acta, y las que el acta no fija se
normalizan bajo el mismo prefijo para que el enrutador y la especificación digan la misma palabra:

| Acción | Endpoint normativo | Permiso | Origen |
|---|---|---|---|
| Listar el equipo | `GET /api/cursos/{id}/equipo` | `curso.ver` | A-165 |
| Emitir invitación | `POST /api/cursos/{id}/equipo/invitaciones` | `equipo.administrar` | **RG-121** |
| Revocar invitación | `DELETE /api/cursos/{id}/equipo/invitaciones/{invitacion_id}` | `equipo.administrar` | A-165 |
| Reenviar invitación | `POST /api/cursos/{id}/equipo/invitaciones/{invitacion_id}/reenviar` | `equipo.administrar` | **[DECISION NUEVA]**, normalizada |
| Cambiar permisos | `PATCH /api/cursos/{id}/miembros/{membresia_id}/permisos` | `equipo.administrar` | **RG-121** |
| Cambiar rol | `PATCH /api/cursos/{id}/miembros/{membresia_id}/rol` | `equipo.administrar` | **RG-121** |
| Consultar el impacto de un retiro | `GET /api/cursos/{id}/miembros/{membresia_id}/impacto-retiro` | `equipo.administrar` | Q-2.1-49 |
| Retirar | `POST /api/cursos/{id}/equipo/{membresia_id}/retiro` | `equipo.administrar` | **RG-139** |
| Reincorporar | `POST /api/cursos/{id}/equipo/{membresia_id}/reincorporacion` | `equipo.administrar` | **[DECISION NUEVA]**, normalizada por simetría con `/retiro` |
| Historial de equipo | `GET /api/cursos/{id}/equipo/historial` | `curso.ver` | A-165 |
| Contexto de autorización | `GET /api/cursos/{id}/contexto` | Sesión más membresía activa | Q-2.1-46 |

### 2.12.3. Qué existe el 16 de septiembre

Todo el contenido de este capítulo está **operativo el 16 de septiembre**, con estas dos excepciones,
que responden `404` de enrutado y no una pantalla a medias (RG-148):

| Ruta o control | Estado bajo el perfil `parcial` | Nace |
|---|---|---|
| `/cursos/{id}/mis-notificaciones` y `GET/POST /baja/{token}` | No registradas | 3 de octubre, 12:00 |
| `POST /api/perfil/regenerar-enlaces` | No registrado. En `/perfil` el control aparece **deshabilitado con el motivo visible**: «todavía no se ha emitido ningún enlace de baja; esta acción llega el 6 de octubre» | 3 de octubre, 12:00 |
| `/cursos/{id}/correccion` | No registrada | 5 de octubre, 12:00 |
| `POST /api/cursos/{id}/tareas/{id}/archivar` y `.../desarchivar` | No registrados. **No hay control deshabilitado, porque no hay bloque** | 30 de septiembre, 20:00 |

**`/acceso`, `/perfil`, `/cursos`, `/cursos/{id}/equipo`, `/invitaciones/{token}`, `/alcance` y
`/privacidad` están registradas desde el 16 de septiembre**, y con ellas todo el ciclo de vida de una
membresía: registro, invitación, aceptación, permisos, cambio de rol, retiro y reincorporación
(A-157, RG-148).

### 2.12.4. Criterios de aceptación de §2.12

| # | Comprobación |
|---|---|
| CA-2.12-01 | Una prueba automatizada recorre el mapa de pantallas **rol por rol** y comprueba que cada requisito citado es alcanzable por los roles que el enunciado nombra, con el rol de menor privilegio que el requisito cita |
| CA-2.12-02 | Un ayudante alcanza `/cursos/{id}/mis-notificaciones` con sólo `curso.ver`: la pantalla **no** exige un permiso que un ayudante no puede tener |
| CA-2.12-03 | Un ayudante con `tarea.administrar` ve el control de archivar **deshabilitado con el motivo escrito** desde el 30 de septiembre, y una llamada directa devuelve `403` con `PERMISO_INSUFICIENTE` |
| CA-2.12-04 | Bajo el perfil `parcial`, cada ruta declarada no registrada devuelve **`404` de enrutado**, no un `500` ni una pantalla vacía |
| CA-2.12-05 | El enrutador real y esta matriz coinciden: la puerta de construcción falla si aparece registrada una ruta declarada oculta en el perfil vigente |
| CA-2.12-06 | Un ayudante entra en `/cursos/{id}/correccion` y su vista por defecto es «Mis asignaciones», sin buscar nada |
| CA-2.12-07 | Sobre una fila ajena de «Estado de la entrega», el botón principal dice «ver», no «corregir» |

---

## 2.13. Acceso del evaluador y cuentas compartidas

### 2.13.1. Cómo entra el evaluador

El enunciado exige entregar «un link para acceder a su entrega **y que ésta pueda ser utilizada por
ayudantes y el profesor**» (§3.1). **Un link que no se puede usar no cumple §3.1.** Las reglas de este
capítulo cierran todas las puertas por defecto —A-017 restringe los usuarios al equipo docente,
§2.2.4 rechaza toda cuenta institucional, §2.5.1 exige invitación nominal—, y por eso el acceso del
evaluador está decidido por escrito (A-166, A-178, A-189):

| # | Regla |
|---|---|
| 1 | **El profesor y los ayudantes del ramo se incorporan como AYUDANTES del curso de demostración**, por el mismo camino que cualquier otro miembro: invitación nominal a una dirección **`gmail.com`** solicitada por adelantado, por escrito y con acuse |
| 2 | **Se les conceden exactamente los cinco permisos concedibles.** Los dos NO CONCEDIBLES **siguen sin concederse**, y **se les explica por escrito en la entrega**, junto con lo que sí pueden hacer |
| 3 | **Se les incorpora al equipo `docentes` de GitHub**, por el camino de §2.8, con su consentimiento fechado. Sin este paso verían `404` al abrir los repositorios |
| 4 | **Se prepara un segundo curso de demostración** en el que el evaluador figura como **profesor**, con datos sintéticos y su propia organización de GitHub, para que pueda recorrer el asistente de vinculación, la administración de equipo y los ajustes. **No necesita token de Canvas propio**: ese curso queda en `BORRADOR`/`VINCULANDO` |
| 5 | **El texto de la entrega incluye, literalmente:** la URL de la aplicación, la instrucción de indicar una dirección `gmail.com`, el nombre del curso de demostración, un recorrido sugerido de cinco minutos, el texto del consentimiento de §2.8.2, y **la advertencia de que el registro exige una cuenta `gmail.com` porque lo exige R2.1.2 del propio enunciado** —una cuenta institucional será rechazada, y eso es cumplimiento, no un fallo— |
| 6 | **Si el evaluador prefiere no dar una dirección `gmail.com`**, la entrega ofrece una **cuenta `gmail.com` creada por el equipo**, sujeta al régimen de §2.13.2 |
| 7 | **Vigencia:** los accesos del evaluador se mantienen **hasta el 31 de octubre inclusive** |

### 2.13.2. Régimen de custodia de las cuentas compartidas

Las dos cuentas `gmail.com` de evaluación quedan sujetas a este régimen, **que no es un conjunto de
consejos** (A-189, RG-140):

| # | Regla |
|---|---|
| 1 | Están en el inventario de credenciales, con **custodio nombrado** —el responsable de infraestructura y su segundo—, viven en la bóveda compartida y tienen **verificación en dos pasos activada en la propia cuenta de Google** |
| 2 | **Reciben exactamente los cinco permisos concedibles, y ninguno más** |
| 3 | **La aplicación las marca** como **«vía de acceso compartida»**. La marca vive en `membresia_curso.es_via_compartida` y **aparece junto al nombre en toda vista donde la persona figure** |
| 4 | **Su uso queda en `bitacora` como el de cualquier miembro**, y la entrega declara por escrito que **la autoría registrada es la de la cuenta y no la de la persona** que la usó |
| 5 | **Su retirada es el 1 de noviembre** y consiste en **tres actos, no en uno**: retirar la membresía de cada curso (§2.9), sacarla del equipo `docentes` y de la organización por los tres planos de §2.9.3, y **cambiar la contraseña de la cuenta de Google**. **Sin el tercero, la retirada no cierra nada** |
| 6 | **El ejemplar impreso** que se lleva a la demostración **se destruye ese mismo día**, y su existencia queda anotada con fecha en `docs/operacion.md` |

**Qué puede enviar una cuenta compartida**, con las comunicaciones ya reanudadas (RG-141):

- **El interruptor de curso manda sobre el permiso**: con `curso.comunicaciones_salientes =
  SUSPENDIDAS` no sale ningún envío, tenga quien lo intente el permiso que tenga.
- **Todo envío desde una cuenta compartida queda en `bitacora` con la cuenta como actor y con la marca
  `es_via_compartida`**, y el diálogo previo dice, antes de enviar: «estás enviando desde una vía de
  acceso compartida; la autoría quedará registrada a nombre de la cuenta».
- **Los topes son los mismos y no se amplían**: 1 recordatorio manual por estudiante y día, 3 por
  estudiante en total. **Ningún tope se relaja para la demostración.**

### 2.13.3. Criterios de aceptación de §2.13

| # | Comprobación |
|---|---|
| CA-2.13-01 | La membresía del evaluador contiene exactamente los cinco permisos concedibles, y ninguno NO CONCEDIBLE |
| CA-2.13-02 | El evaluador abre un repositorio del curso de demostración desde la pantalla de corrección y **no recibe `404`** |
| CA-2.13-03 | El evaluador entra en el segundo curso como profesor y recorre el asistente de vinculación sin token de Canvas propio |
| CA-2.13-04 | La cuenta compartida aparece marcada como «vía de acceso compartida» **junto al nombre en toda vista donde figure** |
| CA-2.13-05 | Un envío desde la cuenta compartida deja fila en `bitacora` con la marca, y el diálogo previo mostró el texto literal |
| CA-2.13-06 | El calendario del equipo contiene un ítem con fecha 1 de noviembre con los tres actos de la retirada |

---

## 2.14. Trazabilidad y verificación del capítulo

### 2.14.1. Qué queda en `bitacora`

`bitacora` es *append-only* y registra **quién, cuándo, contra qué sistema, con qué resultado**
(A-029, A-184). Su catálogo de acciones es **cerrado**, declarado como enumeración en
`backend/app/dominio/bitacora.py` y defendido por un `CHECK` generado desde ella. **Añadir un valor es
una decisión que se registra en la carta**, y tres pruebas de arquitectura fallan la construcción: una
escritura con una `accion` fuera de la enumeración, una `entidad` fuera del censo de tablas, y un tipo
de incidencia sin fila en la tabla tipo → sujeto.

### 2.14.2. Puertas de construcción que este capítulo exige

| # | Puerta |
|---|---|
| 1 | Falla si se registra una ruta bajo `/api/cursos/{curso_id}` sin la dependencia `requiere(...)` |
| 2 | Falla si aparece una lectura de `membresia_curso.rol` con efecto de autorización fuera de `requiere(...)` |
| 3 | Falla si aparece registrada una ruta sin dependencia de sesión que no figure en §2.11.4 |
| 4 | Falla si aparece registrada, bajo el perfil en curso, una ruta declarada oculta en ese perfil |
| 5 | Falla si desaparece `prompt=select_account` de la URL de autorización |
| 6 | Falla si aparece `allow_origins=["*"]` |
| 7 | Falla si aparece `DELETE /repos/{owner}/{repo}` en `backend/app/adaptadores/` |
| 8 | Falla si aparece una llamada a `PUT /orgs/{org}/memberships/` con un login que pertenece a un `mapeo_github` vigente |
| 9 | **Prueba de alcanzabilidad**: recorre el mapa de pantallas rol por rol y comprueba que cada requisito es alcanzable por los roles que el enunciado nombra, y que cada ruta declarada no registrada devuelve `404` de enrutado |

### 2.14.3. Trazabilidad requisito → sección

| Requisito | Texto del enunciado | Secciones que lo cumplen |
|---|---|---|
| **R2.1.1** | Crear y administrar usuarios de tipo profesor | §2.1.2 (los dos planos), §2.2 (creación), §2.5 (incorporación), §2.7 (permisos y rol), §2.9 (retiro), §2.10 (cuenta propia) |
| **R2.1.2** | Permitir que usuarios se registren asociando su cuenta de correo basada en gmail.com | §2.2.1, §2.2.4, §2.2.5, §2.2.7 |
| **R2.1.3** | Permitir a profesores crear y administrar sus cursos | §2.1.3 camino 1, §2.12.1 fila «Mis cursos» (el resto, capítulo 3) |
| **R2.1.4**, **R2.1.5**, **R2.1.6** | Vincular con Canvas y con GitHub, y guiar la vinculación | §2.6 (quién puede pegar credencial), §2.12.1 fila «Asistente de vinculación» (el resto, capítulo 3) |
| **R2.1.7** | Incorporar otros usuarios como profesores del curso (mismos permisos) | §2.3.1 (el profesor tiene los nueve, sin grados), §2.4.2 invariante 3, §2.5, §2.7.3 |
| **R2.1.8** | Incorporar ayudantes y administrar sus permisos dentro de la aplicación, mínimo 3 | §2.3 completa (**nueve permisos nombrados**), §2.5, §2.7.2, §2.11.2 nivel 2 |
| **R2.1.9** | Permitir que el profesor retire posteriormente a un ayudante del curso | §2.7.1 (efecto inmediato), §2.9 completa (incluida la revocación en GitHub por tres planos) |

### 2.14.4. Criterios de aceptación de §2.14

| # | Comprobación |
|---|---|
| CA-2.14-01 | Una escritura en `bitacora` con una `accion` fuera de la enumeración falla la construcción |
| CA-2.14-02 | Las nueve puertas de §2.14.2 están implementadas y se ejecutan en cada `push` |
| CA-2.14-03 | La prueba de alcanzabilidad pasa en el modo `parcial` antes del 16 de septiembre y en el modo `completo` antes del 5 de octubre |
| CA-2.14-04 | Para cada requisito de la tabla §2.14.3 existe al menos una pantalla alcanzable por el rol que el enunciado nombra, comprobado con la herramienta y no leyendo el código |

---

## Anexo 2.A. Resumen de decisiones nuevas de este capítulo

| # | Decisión | Sección | Motivo |
|---|---|---|---|
| DN-02-01 | Etiquetas en pantalla de siete permisos que las fuentes no fijaban | §2.3.2 | A-155 exige etiqueta fija y la misma palabra en todas las vistas; las fuentes sólo fijaban «Publicar nota» y «Enviar comunicaciones» |
| DN-02-02 | Normalización de los endpoints de administración de equipo bajo el prefijo `/equipo/`, y nombre `reincorporacion` por simetría con `retiro` | §2.12.2 | Las respuestas de alcance daban dos formas incompatibles; el acta fija tres de ellas y este capítulo alinea el resto para que enrutador y especificación digan la misma palabra |

## Anexo 2.B. Discrepancias resueltas por precedencia

| # | Qué decía la fuente inferior | Qué manda | Sección |
|---|---|---|---|
| DP-02-01 | Q-2.1-08 fijaba `LIMITE_ACCESO_IP` en 10 por 10 minutos y `LIMITE_MUTACIONES_SESION` en 30 por minuto | **RG-129**: 30/min por IP truncada en `/auth/*` y 300/min por `sesion_id` en `/api/**`. Las dos variables **quedan anuladas**; las cuotas de negocio de la misma respuesta se conservan | §2.11.4 |
| DP-02-02 | Q-2.1-44 y Q-2.7-54 acotaban la matriz nominal de corrección a `correccion.asignar` | **RG-125** y **A-180**: la matriz nominal completa se lee con `curso.ver`; la propiedad acota el trabajo, no la lectura | §2.3.8 |
| DP-02-03 | Q-2.1-45, Q-2.1-44 y Q-2.1-10 hablaban de «los siete concedibles» | **RG-121** y **A-178**: cinco concedibles, siete configurables. La expresión queda prohibida | §2.3.1 |
| DP-02-04 | Q-2.1-51 y Q-2.1-07 llegaban sólo a dos planos de revocación en GitHub | **RG-136** y **A-188**: **tres** planos, con lectura previa en cada uno | §2.9.3 |
| DP-02-05 | Q-2.1-07 cubría el arrastre de credenciales de Canvas sólo en el cierre voluntario de cuenta | **RG-139** y **A-188**: también en el retiro de un profesor por otro profesor, con la frase adicional en la confirmación | §2.9.4 |
| DP-02-06 | RG-096 daba cuatro valores a `org_github_estado` | **RG-198** y **A-186**: **cinco**, con `SIN_CONSENTIMIENTO`, y los relojes colgando de `org_github_invitada_en` | §2.8.3, §2.8.4 |
| DP-02-07 | RG-003 y RG-134 acotaban la elegibilidad de la cuenta de GitHub a los cursos del declarante | **RG-199** y **A-187**: el alcance es **toda la aplicación**, con `CUENTA_DOCENTE_ES_DE_ESTUDIANTE` como único tipo de incidencia | §2.8.1 |
| DP-02-08 | Q-2.1-44 y Q-2.1-49 nombraban la ruta de retiro como `DELETE .../equipo/{membresia_id}` y `POST .../miembros/{id}/retirar` | **RG-139**: `POST /api/cursos/{id}/equipo/{membresia_id}/retiro` | §2.12.2 |
