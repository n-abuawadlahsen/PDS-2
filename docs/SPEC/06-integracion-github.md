# 6. Integración con GitHub

Este capítulo especifica el cliente técnico de GitHub: qué es la GitHub App que la aplicación opera, cómo se instala en la organización del curso, cómo se obtienen y se descartan los tokens con los que se habla con la API, qué endpoints REST y GraphQL usa y para qué, cómo se miden y se respetan los límites de tasa primario y secundario, qué webhooks recibe y cómo los procesa, qué significa operar sobre una organización nueva de plan gratuito, qué presupuesto de invitaciones consume el equipo docente, y qué la aplicación **nunca** hace contra un objeto de GitHub. No fija el modelo de datos de `repositorio`, `version_entrega`, `acceso_repositorio` ni de ninguna otra entidad —eso vive en `docs/SPEC/03-modelo-de-datos.md`, que este capítulo cita por nombre de tabla—; no fija el flujo de usuario del asistente de vinculación —eso vive en `docs/SPEC/04-vinculacion.md` (§4)—; no fija el predicado, el disparador ni la nomenclatura de cuándo se crea un repositorio —eso vive en `docs/SPEC/08-aprovisionamiento.md` (§8)—; no fija el mapeo estudiante ↔ cuenta de GitHub —eso vive en `docs/SPEC/07-estudiantes-y-grupos.md`—; y no fija el motor genérico de colas, cerrojos ni el catálogo completo de trabajos periódicos —eso vive en `docs/SPEC/14-infraestructura-y-despliegue.md` (§14.7), que este capítulo cita para todo lo que no sea específico de la API de GitHub.

**Requisitos que satisface.** Este capítulo es transversal y de soporte: no cumple por sí solo ningún `R2.x.y`, pero es la condición técnica de la que dependen **R2.1.5** y **R2.1.6** (vinculación con una organización de GitHub y su verificación), **R2.3.5**–**R2.3.12** (creación de repositorios, archivos iniciales, incorporación de estudiantes, convención de nombres, acceso del corrector), **R2.4.5**–**R2.4.8** (captura de versión, etiqueta, evidencia, acceso docente) y **R2.5.1**–**R2.5.10** (ingesta de actividad, líneas de tiempo, enlaces a GitHub) en la parte que depende de leer o escribir en GitHub. Ninguna afirmación de este capítulo compite con la lógica de negocio de esos capítulos: describe el mecanismo de la API que esa lógica invoca.

**Restricción que gobierna todo el capítulo:** la organización de GitHub del curso es **nueva y de plan gratuito** (§1.3 de `ARQUITECTURA.md`). No hay *rulesets* ni protección de ramas disponibles sobre repositorios privados con ese plan. Esa única restricción documental explica por qué el `commit_sha` persistido —y no la etiqueta de Git— es la evidencia normativa de una entrega (Ley 4), por qué el equipo docente entra a la organización en vez de recibir una promesa de protección que el plan no ofrece, y por qué el presupuesto de invitaciones a la organización se cuenta en unidades de un dígito y no de cientos.

---

## 6.1 Cómo leer este capítulo

**Orden de precedencia aplicado, sin excepciones:** `docs/enunciado-proyecto2.md` (`R2.x.y`) → actas de reconciliación (`RG-nnn`) → `docs/ARQUITECTURA.md` (`A-nnn`) → respuestas de alcance originales (`Q-2.1-nn`, `Q-2.3-nn`, `Q-transversal-nn`). Donde una respuesta de alcance decía una cosa y una regla `RG` la corrige, este capítulo redacta la regla vigente y no la original.

**Correcciones de precedencia que este capítulo aplica, y que conviene tener presentes desde el principio:**

| Punto | Lo que decía la fuente original | Lo que manda ahora | Fuente |
|---|---|---|---|
| Permisos de la GitHub App | Cuatro permisos cerrados desde el 16 de septiembre (A-060) | El conjunto de A-060 es sólo el **de partida**; se congela el **11 de septiembre a las 20:00** con el resultado de la medición, y `Workflows: write` se pide **si y sólo si** la medición demuestra que lo exige `POST /git/refs` | RG-078, RG-079, A-194 |
| Permiso mínimo de `/generate` y de `POST /git/refs` | Se asumía cerrado por la tabla oficial de GitHub | **No está cerrado por documentación**; queda `[MEDIR]` con desenlace escrito para cada resultado posible | RG-076, RG-077 |
| `PUT /repos/{o}/{r}/topics` | Se trataba como una llamada más del aprovisionamiento | **Es obligatoria** para la identidad de un repositorio adoptable, y si no fuera concedible el marcador de la descripción pasa a ser la única condición de identidad | RG-080 |
| Almacén de presupuesto de tasa | Un cálculo propio por cliente (Canvas y GitHub por separado) | **Un único almacén** `presupuesto_api` con cuatro cubos (`PRIMARIO`, `CONTENIDO`, `GRAFO` de GitHub y `CANVAS`), con el mismo objetivo de margen para los cuatro | RG-071 |
| Mecanismo de capacidad degradada | Banderas booleanas sueltas por capacidad (`topics_disponibles`, `rulesets_legibles`) | **Un mapa único** `dominio/capacidades.py`, compartido con Canvas, sin tabla ni bandera nueva por capacidad | RG-065, RG-067 |
| Cerrojo de serialización con GitHub | Un cerrojo por `(tipo, curso_id)` para cada trabajo | **Un solo espacio de cerrojo por curso para todo el tráfico con GitHub**, `pg_advisory_lock(2, curso_id)`, tomado y liberado por tramos | RG-062, A-217 |
| Desglose del coste de aprovisionar un repositorio | Tres cifras publicadas por separado («≤ 14», «≤ 14», «≤ 15») | **Un desglose único**, distinto para tarea con y sin repositorio base, con las cuatro llamadas antes repartidas contabilizadas juntas | RG-088 |
| Lista cerrada de eliminaciones externas | Seis eliminaciones (A-030) | **Nueve**: las tres nuevas son `DELETE .../collaborators`, `DELETE .../teams/.../memberships` y `DELETE /orgs/{org}/memberships`, todas contra GitHub | RG-191 |

**Convenciones de escritura obligatorias en todo lo que este capítulo especifica**, heredadas de A-154 y A-155 y aplicadas aquí sin excepción: todo estado interno se muestra traducido y nunca en mayúsculas en pantalla; los identificadores técnicos que alguien debe copiar —`login`, nombre de repositorio, SHA— no se traducen y llevan tipografía monoespaciada; los mensajes de error de GitHub se muestran con su **texto literal** bajo una explicación en español, nunca traducidos a un diagnóstico inventado. El vocabulario cerrado dice **cuenta de GitHub vinculada**, no «mapeo» ni «linkeo»; **repositorio**, no «repo del alumno» ni «plantilla»; **invitación · aceptada · pendiente**, no «invite» ni «pending» (A-154).

---

## 6.2 La GitHub App: naturaleza, identidad y mecánica de instalación

### 6.2.1 Por qué GitHub App, y no OAuth App ni token personal

La aplicación opera sobre GitHub **exclusivamente como GitHub App instalada en la organización del curso**. No se usa OAuth App, no se usa token de acceso personal de ningún profesor ni ayudante, y **no existe ningún token de acceso personal ni cuenta de máquina como respaldo de desarrollo en ningún artefacto del proyecto** (A-038, A-195; RG-081). El desarrollo y las pruebas destructivas se hacen contra una **segunda GitHub App**, registrada en el entorno `ensayo`, instalada en una segunda organización gratuita del equipo (§14.4 de `docs/SPEC/14-infraestructura-y-despliegue.md`).

Motivo, en los cinco ejes que la carta compara: **alcance** —la GitHub App es el único mecanismo cuyo alcance es exactamente una organización—; **caducidad** —su credencial se renueva sola, sin depender de que una persona mantenga vivo su token—; **límite de uso** —el límite es de la instalación, no compartido con la actividad humana de quien la instaló—; **webhooks** —incluidos en la App; un token personal no los trae—; **autoría** —las acciones quedan a nombre de la aplicación como cuenta `[bot]`, nunca a nombre de un integrante del equipo—. Un token personal ataría todo el sistema a una cuenta que puede revocarse sin aviso; una OAuth App autentica a una persona, no a una instalación, y no acota el alcance a una organización (Q-2.1-30).

### 6.2.2 Identidad pública y marca de la App

La GitHub App es **pública**, distribuida por URL de instalación, y **no se publica en GitHub Marketplace** —publicarla es opcional, exige revisión propia y no aporta nada al caso de uso— (A-057). Una App **privada** sólo puede instalarse en la cuenta que la registra, lo que impediría que un profesor cualquiera vinculara una organización distinta de la del equipo y dejaría **R2.1.5** incumplido para todo curso que no fuera el de la demostración (A-057, Q-2.1-31).

El estudiante ve el nombre de la App en la invitación a su repositorio y debe poder distinguirla de un intento de suplantación (A-059): nombre de **34 caracteres o menos**, único en todo GitHub, decidido el 10 de septiembre a las 09:00 junto con el dominio; descripción explícita del curso y de la universidad; avatar PNG de 200×200; y un repositorio `.github` de perfil en la organización, con `profile/README.md`, que explica qué es la App y quién la opera. Ese repositorio `.github` **lo crea una persona, no la aplicación**, no lleva el topic `gestor-tareas`, no tiene fila en la tabla `repositorio` y es uno de los **dos únicos repositorios públicos** de todo el proyecto junto al monorepo del equipo (RG-086). El distintivo «Verified» de GitHub queda fuera de alcance declarado porque exige verificación DNS del dominio institucional (A-059).

### 6.2.3 Mecánica de instalación: `state` firmado

El asistente de vinculación —cuyo flujo de pantallas fija `docs/SPEC/04-vinculacion.md`— envía al profesor a:

```
https://github.com/apps/<nombre-app>/installations/new?state=<jwt>
```

que es la forma documentada para preservar el estado de la aplicación a través de la instalación, la autenticación y la aceptación de permisos actualizados (A-058). El `state` es un **JWT de 15 minutos**, firmado con `SIGNING_KEY` (el mismo secreto que firma el `state` de OpenID Connect, inventariado en `docs/SPEC/14-infraestructura-y-despliegue.md` §14.6.2), que contiene `curso_id`, `usuario_id` y un `jti` de un solo uso. Al volver al `setup_url`, la aplicación resuelve el curso **por ese `state`**, nunca por deducción, nunca pidiéndole al profesor que copie un identificador (A-058, Q-2.1-37).

No existe ningún parámetro documentado de `installations/new` que preseleccione la organización de destino: el único parámetro que la documentación reconoce es `state` (Q-2.1-34). La aplicación no simula esa preselección con un parámetro no documentado, porque construir sobre un parámetro inventado es exactamente lo que la regla de trazabilidad de fuentes de la carta prohíbe.

### 6.2.4 La clave de la vinculación es `github_org_id`, nunca el `login` ni el `installation_id`

Aplicación directa de la **Ley 3** («la clave es la duradera, no la legible»): se persiste `curso.github_org_id` (`bigint`, único donde no es nulo) y **no** el `login` de la organización, que es un atributo mutable (A-027, A-074, Q-2.1-38).

| Identificador | Naturaleza | Consecuencia |
|---|---|---|
| `github_org_id` | Clave. Nunca cambia | Un renombre de la organización no rompe la vinculación ni exige revincular |
| `org_login` | Atributo de presentación, en `curso.github_org_login` e `instalacion_github.org_login` | Se refresca en cada ejecución de `verificar_instalacion_github` (cadencia horaria, catálogo cerrado de trabajos de `docs/SPEC/14-infraestructura-y-despliegue.md` §14.7.4) leyendo `GET /app/installations/{id}` → `account.login` |
| `installation_id` | Credencial operativa de la instalación, clave primaria de `instalacion_github` (Q-2.1-38, único por curso — A-028) | **Reemplazable.** Si la App se desinstala y se reinstala, GitHub emite un `installation_id` nuevo |

**Auto-reparación ante reinstalación de la misma organización:** cuando llega el webhook `installation` con acción `created` y un `installation_id` nuevo cuyo `account.id` coincide con el `github_org_id` de un curso ya vinculado, la aplicación **sustituye el `installation_id` anterior por el nuevo en la misma transacción**, deja el hecho en `bitacora` con los dos valores, cierra la incidencia de instalación perdida si estaba abierta, y **reanuda los trabajos que estaban `BLOQUEADO`** (Q-2.1-38). No exige revincular ni tocar ningún repositorio, porque los repositorios se identifican por `github_repo_id` y sus nombres no cambian nunca (A-074, A-110).

**Instalación en una cuenta personal, nunca aceptada.** Se detecta comparando `GET /users/{login}` con `GET /orgs/{login}` para la cuenta destino, **sin confiar en el campo `type` de la respuesta**, cuyos valores literales no constan como documentados (A-091, Q-2.3-66). Aceptar una cuenta personal dejaría sin la vía principal de acceso del equipo docente, que depende de un equipo de organización inexistente en una cuenta personal (Q-2.1-35).

**Una organización pertenece a un solo curso.** `curso.github_org_id` es único donde no es nulo; intentar vincular una organización ya vinculada a otro curso se rechaza nombrando el curso que la ocupa, en vez de crear una segunda verdad sobre a quién pertenece esa organización (A-027, A-028).

### 6.2.5 Alcance de la instalación: `selected repositories`, nunca exigencia de `all`

La aplicación **acepta** una instalación con alcance `repository_selection = selected` y **no exige** `all repositories`, que sería una petición de poder desproporcionada sobre la organización de un tercero (A-063). El hecho documentado del que depende esta decisión: **los repositorios que la propia App crea quedan incluidos automáticamente en el alcance de la instalación**, incluso con `selected` (Q-2.1-36, Q-2.3-29). Ése es el caso del 100 % de los repositorios que la aplicación produce —de estudiante, de grupo, base y `gestor-operaciones`—, porque el repositorio base **siempre** lo crea la App (§6.5.2, nunca un repositorio subido a mano) y el repositorio de operaciones también.

Detección continua de recorte de alcance: la App está suscrita al webhook `installation_repositories` (§6.8); su acción `removed` sobre un repositorio conocido lo marca `DEGRADADO` con motivo visible y abre incidencia; su acción `added` la cierra. El ítem 14 del checklist de vinculación —cuyo catálogo completo de 21 códigos fija `docs/SPEC/04-vinculacion.md`— contrasta además `GET /installation/repositories` contra los repositorios que la aplicación ya conoce, sin que eso añada un ítem nuevo al catálogo cerrado.

**No es viable que la aplicación amplíe el alcance añadiendo un repositorio existente a la instalación**: `PUT /user/installations/{installation_id}/repositories/{repository_id}` sólo funciona documentalmente con un token de acceso personal clásico con alcance `repo`, no con un token de instalación (Q-2.3-29). Por eso **no se acepta vincular un repositorio base creado a mano** (§6.5.2): la garantía de inclusión automática cubre lo que la App crea y no cubre nada más, y exigir que lo cree la App elimina el modo de fallo más difícil de diagnosticar del sistema — un `404` a mitad del aprovisionamiento sin causa visible (A-066, Q-2.1-36).

### 6.2.6 Ciclo de vida de la instalación: permisos pendientes, suspensión, desinstalación

La App se suscribe al webhook `installation` y procesa sus cinco acciones documentadas:

| Acción | Efecto |
|---|---|
| `created` | Vincula (§6.2.3) o repara (§6.2.4) según corresponda |
| `new_permissions_accepted` | `instalacion_github.permisos_pendientes = false`; se cierra la banda de advertencia y se reanudan los trabajos `BLOQUEADO` que esperaban el permiso |
| `suspend` | `instalacion_github.suspendida = true`; el curso muestra la banda correspondiente |
| `unsuspend` | Reanudación automática |
| `deleted` | El curso pasa a `GITHUB_DESVINCULADO`, se abre incidencia bloqueante, los trabajos de GitHub se encolan en `BLOQUEADO`, y **no se borra nada**: ni repositorios, ni commits, ni versiones, ni accesos registrados (A-030, Q-2.1-38) |

Mientras haya **permisos pendientes de aprobación** (acción `new_permissions_accepted` no recibida todavía), `instalacion_github.permisos_pendientes = true`, el curso muestra una banda de advertencia con el enlace a la aprobación, y **los trabajos que necesitan el permiso nuevo se encolan `BLOQUEADO`, no fallan** (A-062). La aplicación degrada; no se rompe. Añadir un permiso después de la congelación del 11 de septiembre a las 20:00 obliga a que cada instalación lo apruebe de nuevo, y por eso el conjunto de permisos no se toca después de esa hora salvo emergencia declarada (§6.4, A-061, A-194).

### Criterios de aceptación de 6.2

1. **CA-6.2-01.** `curso.github_org_id` es la única columna con unicidad efectiva sobre la organización; una prueba automatizada falla si aparece una comparación por `org_login` en lugar de por `github_org_id` en un punto de decisión de identidad.
2. **CA-6.2-02.** Reinstalando la App sobre la misma organización con un `installation_id` distinto, el curso conserva su vinculación, `instalacion_github.installation_id` se sustituye en la misma transacción, `bitacora` registra ambos valores y ningún trabajo `BLOQUEADO` por la pérdida de instalación queda huérfano.
3. **CA-6.2-03.** Un intento de vincular una cuenta personal se rechaza con el mensaje que nombra la restricción de **R2.1.5**, detectado comparando `GET /users/{login}` con `GET /orgs/{login}` y no el campo `type`.
4. **CA-6.2-04.** Un intento de vincular una organización ya vinculada a otro curso se rechaza nombrando ese curso.
5. **CA-6.2-05.** Instalando con `repository_selection = selected` sobre sólo el repositorio base, `POST /orgs/{org}/repos/{template}/generate` sobre un repositorio nuevo del mismo curso responde `201` sin ampliar manualmente el alcance.
6. **CA-6.2-06.** El webhook `installation_repositories` con acción `removed` sobre un repositorio conocido lo marca `DEGRADADO` en menos de un ciclo del trabajo `procesar_webhooks`.

---

## 6.3 Tokens de instalación: obtención, caché y no persistencia

**No se persiste ningún token de GitHub, en ninguna tabla, en ningún momento** (A-038). La única columna que la base de datos guarda sobre la credencial de GitHub es `instalacion_github.installation_id`, que **identifica** la instalación pero no autentica nada por sí sola.

### 6.3.1 Dos credenciales, dos usos

| Credencial | Cómo se obtiene | Para qué se usa | Vigencia |
|---|---|---|---|
| **JWT de la App** | Firmado en el momento con `GITHUB_APP_PRIVATE_KEY` (clave privada RSA de la App, inyectada en base64 y nunca escrita en disco — `docs/SPEC/14-infraestructura-y-despliegue.md` §14.6.4) y `GITHUB_APP_ID` | Llamadas a nivel de App: `GET /app/installations/{id}`, `GET /orgs/{org}/installation`, `POST /app/installations/{id}/access_tokens` | 10 minutos, el máximo que GitHub admite |
| **Token de instalación** | `POST /app/installations/{installation_id}/access_tokens`, autenticado con el JWT de la App | Todas las llamadas REST y GraphQL contra repositorios, colaboradores, equipos y organización de esa instalación | 1 hora |

### 6.3.2 Caché en memoria del proceso, nunca en base ni en almacén externo

El token de instalación se **cachea en memoria del proceso que lo emitió**, y se renueva **cinco minutos antes de su expiración** (A-038, §14.7.7 de `docs/SPEC/14-infraestructura-y-despliegue.md`). Con dos procesos —el servicio web y el trabajador, §3.1 de `docs/SPEC/14-infraestructura-y-despliegue.md`— cada uno mantiene su propia caché; el coste es, a lo sumo, una llamada de emisión extra por proceso y por hora, gasto que no compite con el presupuesto de contenido de §6.6.

**Consecuencia deseada y defendible: un volcado de la base de datos, incluido el respaldo diario cifrado de `docs/SPEC/14-infraestructura-y-despliegue.md` §14.11, no contiene ninguna credencial que permita escribir en GitHub.** Quien tuviera el volcado completo seguiría sin poder crear un solo repositorio ni invitar a un solo colaborador.

### 6.3.3 Quién más usa este mismo mecanismo

Ningún artefacto del proyecto tiene un segundo camino de autenticación contra GitHub. Los cuatro artefactos que escriben en una organización real —dos guiones de medición contra `ensayo`, el guion de semilla de demostración y el *workflow* `actividad_demo.yml`— emiten su propio token de instalación en caliente a partir de la clave privada, exactamente igual que la aplicación, con el módulo compartido `infra/_credenciales.py`; ninguno lo persiste (A-195, RG-081). La única excepción de todo el proyecto a la regla de autoría de §6.11.4 es la identidad de los commits que produce la semilla de demostración, acotada a `infra/` y al curso de demostración, y declarada por escrito en la memoria de entrega (RG-081).

### Criterios de aceptación de 6.3

1. **CA-6.3-01.** Una búsqueda en el esquema de base de datos no encuentra ninguna columna que almacene un token de acceso de GitHub, de instalación o de otro tipo.
2. **CA-6.3-02.** Deteniendo y reiniciando el trabajador a mitad de una operación, el proceso reemitido obtiene un token de instalación nuevo sin error visible para el usuario.
3. **CA-6.3-03.** Restaurando el volcado cifrado de respaldo sobre una base vacía, ninguna consulta a las tablas restauradas devuelve un valor que la API de GitHub acepte como token.
4. **CA-6.3-04.** Los cuatro artefactos de `infra/` y el *workflow* de demostración usan el módulo compartido `infra/_credenciales.py`; una revisión de `.github/workflows/actividad_demo.yml` confirma que el token se obtiene en el primer paso de cada ejecución y no se lee de un secreto persistido como token.

---

## 6.4 Permisos concedidos y su gobierno

El conjunto de permisos que la GitHub App solicita se congela **el 11 de septiembre a las 20:00**, con el resultado de la medición del 10 y 11 de septiembre sobre la organización de `ensayo`, y **no antes** (A-194, RG-078). Hasta ese instante, la tabla siguiente es el conjunto **de partida**, no el final.

| Ámbito | Permiso | Nivel | Para qué |
|---|---|---|---|
| Repositorio | Administration | write | `POST /orgs/{org}/repos`, `PATCH /repos/{o}/{r}` (`is_template`), `PUT .../collaborators/{u}` |
| Repositorio | Contents | write | `POST .../generate`, `PUT .../contents/{ruta}`, `POST .../git/refs`, lectura de commits; habilita los webhooks `push`, `create` y `delete` |
| Repositorio | Metadata | read | Obligatorio; habilita el webhook `repository` |
| Organización | Members | write | Recibir el webhook `member` —única señal documentada de que un estudiante aceptó una invitación de colaborador—, y crear y poblar el equipo `docentes` con lectura sobre cada repositorio (§6.10) |

**No se solicita `Organization Administration`**: su único uso sería crear *rulesets*, y los *rulesets* no están disponibles en plan gratuito para repositorios privados (§6.9). `Workflows: write` **se solicita si y sólo si** la medición demuestra que `POST /git/refs` falla con sólo `Contents: write` y funciona al añadirlo; si la medición sale positiva sin él, no se pide (RG-078). En cualquiera de los dos desenlaces, la aplicación **no sube archivos bajo `.github/workflows/`** (§6.11.5): no subir *workflows* es una decisión de producto, no una consecuencia del permiso concedido.

El único candidato ajeno a esta tabla es, por tanto, `Workflows: write`. `Administration: write` y `Contents: write` ya cubren ambos desenlaces posibles de la marca «Additional permissions» de `/generate` y de `POST /git/refs`, que es ambigua por diseño en la documentación oficial de GitHub —cubre a la vez «requiere varios permisos» y «vale cualquiera del conjunto»— (RG-076, RG-077).

**Por qué `Members` es `write` y no `read`.** Los estudiantes no consumen este permiso: siguen sin entrar a la organización (§6.10). Lo que lo exige es que el **equipo docente sí entra**, porque es la única forma documentada de que un ayudante pueda abrir la URL del repositorio de un estudiante que corrige: la documentación de GitHub enumera exactamente quién puede abrir un repositorio privado de una organización —el dueño, un colaborador del repositorio, o **un miembro de un equipo con acceso al repositorio**— y no hay una cuarta categoría (A-060, §6.10).

**Manejo de permisos pendientes:** ya descrito en §6.2.6. **El alcance de `Members: write` está acotado por escrito y verificado por prueba automatizada**: se usa exclusivamente sobre el equipo `docentes`, para añadir o quitar personas que son miembros activos del curso en la aplicación. Hay una prueba de arquitectura que falla la construcción si aparece una llamada a `PUT /orgs/{org}/memberships/{login}` con un `login` que pertenece a un `mapeo_github` vigente —es decir, a un estudiante— (A-060, §6.11.1).

### Criterios de aceptación de 6.4

1. **CA-6.4-01.** `docs/permisos.md` se escribe después de la prueba de permisos del 10-11 de septiembre, con una fila condicional para `Workflows: write` y la salida literal que la justifica o la descarta.
2. **CA-6.4-02.** El ítem 14 del checklist de vinculación compara los permisos concedidos de la instalación contra el conjunto congelado en `docs/permisos.md`, y falla como bloqueante si difieren.
3. **CA-6.4-03.** Una prueba automatizada falla la construcción si aparece, en cualquier punto del código, una llamada a `PUT /orgs/{org}/memberships/{login}` con un `login` con `mapeo_github` vigente.
4. **CA-6.4-04.** Ningún fichero bajo `.github/workflows/` se sube desde `backend/`, con o sin el permiso `Workflows: write` concedido.

---

## 6.5 Catálogo de endpoints REST y GraphQL usados

Todo endpoint de este catálogo se invoca **exclusivamente** desde `backend/app/adaptadores/cliente_github.py`. Una prueba de arquitectura falla la construcción si un módulo fuera de `backend/app/adaptadores/` instancia un cliente HTTP contra la API de GitHub (`docs/SPEC/14-infraestructura-y-despliegue.md` §14.9.4). Toda petición lleva las cabeceras `Accept: application/vnd.github+json`, `X-GitHub-Api-Version` con el valor de la constante única `GITHUB_API_VERSION` (`docs/SPEC/14-infraestructura-y-despliegue.md` §14.5.2 y §14.10.6) y un `User-Agent` que identifica al producto y al curso.

### 6.5.1 Nivel de App e instalación

| Endpoint | Propósito |
|---|---|
| `GET /app/installations/{installation_id}` | Leer estado, alcance y permisos de la instalación |
| `GET /orgs/{org}/installation` | Resolver la instalación a partir del `login` de organización, con JWT de App |
| `POST /app/installations/{installation_id}/access_tokens` | Emitir el token de instalación (§6.3) |
| `GET /installation/repositories` | Contrastar qué repositorios están dentro del alcance (§6.2.5) |

### 6.5.2 Repositorios

| Endpoint | Propósito | Escrituras permitidas (§6.11.2) |
|---|---|---|
| `POST /orgs/{org}/repos` | Crear un repositorio vacío (base sin plantilla, estudiante o grupo sin base, `gestor-operaciones`) | — |
| `POST /repos/{template_owner}/{template_repo}/generate` | Crear un repositorio de estudiante o de grupo a partir del repositorio base, con su bandera `is_template` en `true` | — |
| `PATCH /repos/{o}/{r}` | `is_template: true` al crear el repositorio base; y sólo con los campos de la lista blanca de §6.11.2 en el resto de casos | `description`, `private`, `archived`, nunca `name` |
| `GET /repos/{o}/{r}` | Lectura previa por nombre, antes de crear (evita duplicar) | — |
| `PUT /repos/{o}/{r}/topics` | Los tres topics obligatorios de identidad del repositorio (`gestor-tareas`, `curso-<slug>`, `tarea-<slug>`), citados por `docs/SPEC/08-aprovisionamiento.md` §8 | — |
| `PUT /repos/{o}/{r}/actions/permissions` | Deshabilitar Actions en el repositorio, si el conjunto de permisos lo permite | — |
| `DELETE /repos/{o}/{r}/contents/{ruta}` | Retirar un archivo del repositorio base (nunca de un repositorio de estudiante) | — |
| `PUT /repos/{o}/{r}/contents/{ruta}` | Subir o reemplazar un archivo del repositorio base | — |

**`DELETE /repos/{owner}/{repo}` no se invoca en ningún punto del código.** Una prueba de arquitectura falla la construcción si aparece (§6.11.3).

### 6.5.3 Contenido inicial sin repositorio base (Git Data API)

Cuando la tarea no tiene repositorio base, el commit inicial se construye con la Git Data API en cuatro llamadas encadenadas, cuyo árbol y disparadores documenta `docs/SPEC/08-aprovisionamiento.md`:

| Endpoint | Orden |
|---|---|
| `POST /repos/{o}/{r}/git/blobs` | 1 |
| `POST /repos/{o}/{r}/git/trees` | 2 |
| `POST /repos/{o}/{r}/git/commits` | 3, sin padres, **sin `author` ni `committer`** (§6.11.4) |
| `POST /repos/{o}/{r}/git/refs` | 4, sobre `refs/heads/{rama_por_defecto}` |

Camino alternativo si Git Data no estuviera disponible con el conjunto de permisos congelado: `POST /orgs/{org}/repos` con `auto_init: true`, que produce igualmente un único commit de andamiaje, a costa de un `README.md` genérico (RG-089, capacidad `ESCRIBIR_GIT_DATA` de §6.7.2).

### 6.5.4 Rama por defecto y comparación de commits

| Endpoint | Propósito |
|---|---|
| `default_branch` (campo del `201` de creación) | Se lee y se persiste; nunca se supone `main` |
| `GET /repos/{o}/{r}/commits` | Listado paginado, con `If-None-Match` y el ETag guardado (§6.8.4) |
| `GET /repos/{o}/{r}/compare/{before}...{after}` | Relleno paginado de un `push` grande, y detección de reescritura de historia (`diverged`) |
| `GET /repos/{o}/{r}/commits/{sha}` | Resolución puntual de un SHA (verificación de etiquetas, §6.9.3) |

### 6.5.5 Etiquetas de entrega

| Endpoint | Propósito |
|---|---|
| `POST /repos/{o}/{r}/git/refs` | Crear el tag `entrega/<orden>-<slug>/v<n>` sobre el `commit_sha` capturado |
| `GET /repos/{o}/{r}/git/ref/tags/{tag_nombre}` | Verificar que el tag sigue existiendo y apuntando al SHA esperado (§6.9.3) |

La nomenclatura, el disparador y la lógica de versión del tag viven en `docs/SPEC/08-aprovisionamiento.md` §8; este capítulo documenta sólo la llamada técnica.

### 6.5.6 Colaboradores (acceso de estudiante)

| Endpoint | Propósito |
|---|---|
| `PUT /repos/{o}/{r}/collaborators/{login}` | Invitar (o conceder acceso directo) con `{"permission": "push"}` — nunca `admin` |
| `GET /repos/{o}/{r}/collaborators/{login}` | Lectura previa: ¿ya es colaborador? (`204`/`404`) |
| `GET /repos/{o}/{r}/invitations` | Reconciliación: listar invitaciones pendientes del repositorio |
| `DELETE /repos/{o}/{r}/invitations/{invitation_id}` | Sólo cuando la invitación aparece `expired = true`, seguido de un `PUT collaborators` nuevo |
| `DELETE /repos/{o}/{r}/collaborators/{login}` | Único ejecutor de la revocación de acceso de un estudiante (§6.11.3) |

Casos borde de este grupo de endpoints en §6.12.

### 6.5.7 Organización y equipo docente

| Endpoint | Propósito |
|---|---|
| `POST /orgs/{org}/teams` | Crear el equipo `docentes` (una vez por curso) |
| `PUT /orgs/{org}/teams/{team_slug}/memberships/{login}` | Incorporar a un profesor o ayudante al equipo |
| `PUT /orgs/{org}/teams/{team_slug}/repos/{org}/{repo}` | Conceder `pull` al equipo sobre un repositorio, una sola llamada por repositorio |
| `PUT /orgs/{org}/memberships/{login}` | Incorporar a un profesor o ayudante a la organización (§6.10) |
| `GET /orgs/{org}/memberships/{login}` | Reconciliar el estado de la membresía (`active` / `pending`) |
| `DELETE /orgs/{org}/teams/{team_slug}/memberships/{login}` | Retirar del equipo (revoca la lectura sobre todos los repositorios de una vez) |
| `DELETE /orgs/{org}/memberships/{login}` | Retirar de la organización, sólo si fue la aplicación quien lo incorporó (§6.11.3) |
| `PUT /repos/{o}/{r}/collaborators/{login}` con `{"permission": "pull"}` | Vía de respaldo de acceso docente si el equipo no puede crearse o poblarse |

### 6.5.8 Enriquecimiento de actividad (GraphQL)

Consulta por lotes de 100 commits contra la API GraphQL de GitHub, de la que dependen `additions`, `deletions`, `changedFilesIfAvailable`, `authors`, `committedViaWeb` y `parents.totalCount`. Consume el cubo `GRAFO` (§6.6.2) y no el presupuesto REST. La lógica de atribución que consume este enriquecimiento vive en `docs/SPEC/10-seguimiento.md`.

### 6.5.9 Rulesets: sólo lectura, y sólo dos

**Prohibido por prueba de arquitectura:** cualquier `POST`, `PUT`, `PATCH` o `DELETE` sobre `rulesets` en cualquier ámbito, o sobre `branches/*/protection`. **Permitidas exactamente dos lecturas**, en lista blanca dentro de la propia prueba: `GET /orgs/{org}/rulesets` y `GET /repos/{o}/{r}/rulesets`, una vez por ciclo horario de `verificar_instalacion_github`, sobre un repositorio muestreado en rotación (RG-085). `POST /orgs/{org}/rulesets` **no se llama nunca**, porque figura bajo `Organization Administration`, permiso que este capítulo declara no solicitado en §6.4.

### 6.5.10 Escrituras síncronas contra el interior de una petición, frente a escrituras encoladas

De las seis escrituras externas síncronas que la aplicación ejecuta dentro de una petición HTTP —lista cerrada que fija `docs/SPEC/14-infraestructura-y-despliegue.md` §14.7.1 y su contrato (tiempo de espera duro de 20 segundos, degradación a trabajo de cola si se agota, error literal en pantalla, registro en `bitacora`)—, **dos** son contra GitHub: crear el repositorio base (`POST /orgs/{org}/repos` + `PATCH is_template`) y administrar sus archivos iniciales (`PUT`/`DELETE contents`). Todo lo demás de este catálogo —creación de repositorios de estudiante, invitaciones, acceso docente, etiquetas, enriquecimiento de actividad— se ejecuta **encolado**, nunca desde dentro de una petición. Una prueba de arquitectura falla la construcción si un manejador de `backend/app/api/` invoca `ClienteGitHub` fuera de esas dos entradas.

### Criterios de aceptación de 6.5

1. **CA-6.5-01.** Un análisis estático de `backend/app/adaptadores/` confirma que ningún endpoint de la API de GitHub se invoca desde un módulo distinto de `cliente_github.py`.
2. **CA-6.5-02.** Toda petición saliente registrada en una prueba de integración lleva `Accept: application/vnd.github+json` y `X-GitHub-Api-Version` con el valor de la constante única.
3. **CA-6.5-03.** Una búsqueda en el código no encuentra `DELETE /repos/{owner}/{repo}` en ningún punto.
4. **CA-6.5-04.** Una prueba de arquitectura falla la construcción si aparece un `POST`, `PUT`, `PATCH` o `DELETE` sobre `rulesets` o `branches/*/protection`.
5. **CA-6.5-05.** Un manejador de `backend/app/api/` que invoque `ClienteGitHub` fuera de las dos entradas síncronas de §6.5.10 falla la puerta de construcción correspondiente.

---

## 6.6 Límites de tasa: primario, secundario y presupuesto medido

### 6.6.1 Qué son y por qué la aplicación no puede calcularlos de antemano

GitHub aplica dos clases de límite a una instalación: un **límite primario** de peticiones por hora, publicado en las cabeceras `x-ratelimit-limit`, `x-ratelimit-remaining` y `x-ratelimit-reset` de cada respuesta REST, y **límites secundarios** no publicados que penalizan ráfagas de peticiones concurrentes o de creación de contenido, señalados con `403` o `429` sin cabecera de cupo asociada. El presupuesto real **no es calculable a priori**, porque GitHub no publica el coste en puntos de todos los endpoints ni permite consultar el estado del límite secundario por adelantado. Por eso el ritmo de la aplicación se fija bajo, se mide en la prueba de carga previa a la parcial, y se ajusta con datos observados, nunca con aritmética de papel (A-117).

El límite primario de la instalación parte de **5.000 peticiones/hora**, escala **+50/hora por repositorio por encima de 20**, con techo de **12.500/hora**. Una respuesta `304` sobre una petición condicional con ETag **no descuenta del límite primario** si va correctamente autenticada; que tampoco consuma límite secundario no está confirmado por documentación, y el reconciliador de §6.8.4 respeta igualmente el techo de concurrencia por prudencia (A-072, A-117).

### 6.6.2 Un único almacén con cuatro cubos

**Todo límite de tasa observado, de cualquier proveedor, vive en la tabla `presupuesto_api`**, con unicidad `(ambito, ambito_id, cubo)` (RG-071). De sus cuatro cubos, tres son de GitHub:

| Cubo | Ámbito | Fuente de capacidad y recarga | Consumidores |
|---|---|---|---|
| `PRIMARIO` | `GITHUB_INSTALACION` | `x-ratelimit-limit` / `-remaining` / `-reset` de cada respuesta REST | Todas las llamadas REST del catálogo de §6.5 |
| `CONTENIDO` | `GITHUB_INSTALACION` | Tope autoimpuesto de **30 fichas, recarga 30/min**, frente a las 80/min documentadas | Operaciones generadoras de contenido: creación de repositorios, invitaciones, escrituras de contenido, creación de etiquetas |
| `GRAFO` | `GITHUB_INSTALACION` | Cabeceras de la propia respuesta GraphQL (`x-ratelimit-limit`, `-remaining`, `-used`, `-reset`, `-resource`) | El enriquecimiento de actividad de §6.5.8 |

El objetivo autoimpuesto es el mismo para los cuatro cubos del almacén (los tres de GitHub y el `CANVAS` que documenta el capítulo de Canvas): **no bajar del 50 % del límite real medido en la hora**, y por debajo del **20 %** sólo circulan las clases de máxima prioridad. El máximo observado se lee siempre de `presupuesto_api`, nunca de un cálculo propio del cliente. `/operacion` —pantalla que fija `docs/SPEC/14-infraestructura-y-despliegue.md` §14.7.7— muestra los cuatro cubos con la misma tarjeta y el mismo margen, acotados por curso.

**Sub-limitador anidado del cubo `CONTENIDO`:** la cola de creación de etiquetas consume del mismo cubo con un tope propio de **≤ 20 creaciones por minuto**, y respeta además una reserva del 25 % garantizado para esa clase, porque crear la etiqueta es la operación de mayor prioridad del cubo (RG-072).

### 6.6.3 Concurrencia y ritmo

| Parámetro | Valor fijado | Referencia documentada |
|---|---|---|
| Concurrencia máxima contra GitHub | **4** | 100 concurrentes documentadas |
| Ritmo de creación de repositorios | **1 cada 6 segundos** | Recalculado sobre el desglose de coste real de §6.6.5 |
| Consultas GraphQL | **3 por minuto por instalación**, prioridad **P4** (la más baja: cede ante todo lo demás y se detiene por debajo del 20 % del cubo `GRAFO`) | Con lotes de 100, 30.000 commits de un semestre son 300 consultas |

Toda la serialización de tráfico con GitHub de un curso ocurre bajo **un solo espacio de cerrojo**, `pg_advisory_lock(2, curso_id)`, distinto del cerrojo de Canvas; el techo de concurrencia real lo pone este apartado, no el cerrojo (§6.1, RG-062, A-217, y `docs/SPEC/14-infraestructura-y-despliegue.md` §14.7.3 para el mecanismo genérico de cerrojos).

### 6.6.4 Freno duro y estrangulamiento automático

El cliente **lee `x-ratelimit-remaining` y `x-ratelimit-limit` en cada respuesta** y ajusta su ritmo para no bajar del 50 % del límite real medido en esa hora. Si el margen se estrecha, **espacia**; nunca se detiene ni falla por esa sola causa (A-117). Si `x-ratelimit-remaining` baja del **20 %**, el trabajo de reconciliación de actividad reduce su lote a la mitad; por debajo del **10 %**, sólo procesa repositorios con una entrega abierta en las próximas 24 horas.

**Ante `403` o `429`:** se respeta `retry-after` si viene en la respuesta; si no viene y `x-ratelimit-remaining` es 0, se espera hasta `x-ratelimit-reset`; en cualquier otro caso se espera **al menos un minuto**, y luego retroceso exponencial hasta 6 intentos. Es literalmente lo que prescribe la documentación de GitHub, y el motivo está también documentado: **seguir pidiendo mientras se está limitado puede acabar en el baneo de la integración** (Q-transversal-39). Un baneo el día de la evaluación sería catastrófico, y por eso el respeto del límite es una regla dura del cliente y no una optimización.

### 6.6.5 Desglose del coste real de aprovisionar un repositorio

El desglose se publica **una sola vez**, distinguiendo tarea con y sin repositorio base, con las cuatro llamadas que respuestas anteriores repartían por separado ya contabilizadas juntas (RG-088):

| Paso | Con base | Sin base |
|---|---|---|
| Lectura previa por nombre | 1 | 1 |
| Creación (`/generate` o `POST /orgs/{org}/repos`) | 1 | 1 |
| `PUT .../topics` | 1 | 1 |
| `PATCH .../repos` de ajustes no aceptados en la creación | ≤ 1 | ≤ 1 |
| Sondeo de contenido tras `/generate` | ≤ 8 | 0 |
| Commit inicial por Git Data | 0 | 4 ó 5 |
| `PUT .../actions/permissions` | ≤ 1 | ≤ 1 |
| Lectura previa de colaborador + invitación, por integrante | 2 × n | 2 × n |
| Acceso del equipo docente | 1 | 1 |
| **Total, tarea individual (n = 1)** | **≤ 16** | **≤ 13** |
| **Tarea grupal** | **≤ 16 + 2·(n−1)** | **≤ 13 + 2·(n−1)** |

El ritmo efectivo no lo fija esta aritmética: lo sigue gobernando el freno duro de §6.6.4. Esta tabla alimenta únicamente la estimación de tiempo que `docs/SPEC/08-aprovisionamiento.md` muestra en pantalla, recalculada en cada ciclo con el ritmo efectivo observado.

### 6.6.6 Qué ve el equipo docente cuando se alcanza un límite (Ley 5)

**Un límite de una API externa nunca se pinta como error del equipo.** El repositorio o el acceso afectado pasa al estado transitorio correspondiente —nunca a un estado que la interfaz muestre en rojo como fallo propio—, con **hora de reintento visible**: «Reintentando, próximo intento a las HH:MM» para lo transitorio; «Esperando a GitHub por límite de uso. Reintento automático a las HH:MM» para lo bloqueante (§6.7.1). El aprovisionamiento **no se detiene entero**: sólo se reprograma la operación concreta que topó con el límite, porque el límite de invitación es por repositorio y no por organización, y un repositorio agotado no afecta a los otros quinientos noventa y nueve.

### Criterios de aceptación de 6.6

1. **CA-6.6-01.** `presupuesto_api` tiene exactamente cuatro filas por instalación activa (`PRIMARIO`, `CONTENIDO`, `GRAFO`, más `CANVAS` a nivel de curso), y `/operacion` las muestra con el mismo formato de tarjeta.
2. **CA-6.6-02.** Lanzando cinco trabajos que hablan con GitHub del mismo curso a la vez, una prueba automatizada confirma que nunca hay más de 4 peticiones concurrentes contra la API de GitHub.
3. **CA-6.6-03.** Forzando `x-ratelimit-remaining` medido por debajo del 20 % en `ensayo`, el lote de `reconciliar_actividad` se reduce a la mitad; por debajo del 10 %, sólo procesa repositorios con entrega en las próximas 24 horas.
4. **CA-6.6-04.** Simulando un `429` sin cabecera `retry-after` y con `x-ratelimit-remaining = 0`, el cliente espera hasta `x-ratelimit-reset` antes de reintentar.
5. **CA-6.6-05.** Ningún texto de interfaz asociado a un estado `ESPERANDO_LIMITE` contiene la palabra «error»; todos muestran una hora de reintento.
6. **CA-6.6-06.** La estimación de tiempo de aprovisionamiento mostrada en pantalla usa la tabla de §6.6.5 y se recalcula en cada ciclo con el ritmo efectivo.

---

## 6.7 Clasificación de errores y capacidad degradada

### 6.7.1 Tres familias

Toda respuesta de error de la API de GitHub se clasifica en una de tres familias, y la familia decide el comportamiento del cliente **y lo que ve el equipo docente** (A-116; `docs/SPEC/14-infraestructura-y-despliegue.md` §14.7.5 documenta el mecanismo genérico compartido con Canvas):

| Familia | Ejemplos en GitHub | Comportamiento | Qué ve el docente |
|---|---|---|---|
| **TRANSITORIO** | `429`, `5xx`, tiempo de espera agotado, `403` de límite secundario, `404` durante la ventana de creación de un repositorio recién generado | Retroceso exponencial con *jitter*, hasta el tope del trabajo | «Reintentando, próximo intento a las HH:MM» |
| **BLOQUEANTE** | `403` por política de la organización, permisos pendientes de aprobación, cupo de invitaciones agotado, `401` con permiso en verde pero llamada no autorizada | Estado `BLOQUEADO` o `ESPERANDO_*`; **no se reintenta en bucle**; se reevalúa cada 30 minutos o cuando cambia la condición | «Esperando a GitHub por límite de uso» / «Falta aprobar permisos» |
| **PERMANENTE** | Cuenta de GitHub inexistente, `login` que resulta ser una organización, `422` de validación (por ejemplo, cuenta EMU — §6.12.5) | Cero reintentos; estado terminal con motivo y acción sugerida; se guarda el mensaje literal del proveedor | «Requiere tu acción: …», con el texto literal debajo |

**Todo `403` cuyo cuerpo no se reconozca se clasifica como BLOQUEANTE por defecto, nunca como PERMANENTE.** Es la clasificación conservadora: un error de límite tratado como permanente perdería trabajo útil; un error permanente tratado como límite sólo cuesta un reintento diferido (Q-2.3-32).

### 6.7.2 Mapa de capacidades degradadas específico de GitHub

El discriminador `LLAMADA_NO_AUTORIZADA` —un `401`, o un `403` clasificado como no transitorio, con la instalación viva y la sonda de credencial en verde— **no invalida la instalación ni desvincula el curso**: degrada únicamente la capacidad afectada, sobre el mecanismo único compartido con Canvas que fija `dominio/capacidades.py` (RG-065, y §6.1 de este capítulo para su corrección de precedencia). Las filas de proveedor `GITHUB` de ese mapa son exactamente éstas (RG-067):

| Capacidad | Endpoint del que depende | Estado degradado |
|---|---|---|
| `CREAR_REPOSITORIO` | `POST /orgs/{org}/repos`, `.../generate` | El aprovisionamiento se detiene con `PARCIAL`; la cabecera de la tarea declara que no puede crear, con el error literal |
| `ESCRIBIR_TOPICS` | `PUT .../topics` | El marcador de la descripción pasa a ser la única condición de identidad del repositorio (§6.1); la ficha declara que el curso opera sin topics |
| `ESCRIBIR_GIT_DATA` | `POST /git/blobs`, `/trees`, `/commits` | Camino alternativo de §6.5.3: `auto_init: true`, README genérico |
| `CREAR_REFERENCIA` | `POST .../git/refs` | `tag_creado = false`, `tag_estado = FALLIDO`; **la captura de versión no falla**: se muestra «versión registrada (sin etiqueta en GitHub)» |
| `INVITAR_COLABORADOR` | `PUT .../collaborators/{login}` | El acceso del estudiante queda `PENDIENTE` con motivo; incidencia y aviso; no se reintenta en bucle |
| `DESACTIVAR_ACTIONS` | `PUT .../actions/permissions` | Se omite el paso; la ficha del repositorio declara que Actions sigue habilitado en él |
| `LEER_RULESETS` | `GET /orgs/{org}/rulesets`, `GET /repos/{o}/{r}/rulesets` | Se deja de pedir tras el primer `403`; la tarjeta «sin actividad reciente» declara que no puede comprobarse si hay reglas activas |
| `INVITAR_ORGANIZACION` | `PUT /orgs/{org}/memberships/{login}` | `org_github_estado = ERROR` con el motivo literal (§6.10.3) |
| `CONCEDER_ACCESO_DOCENTE` | Equipo `docentes` o `PUT .../collaborators/{login}` con `pull` | `PENDIENTE` con `ultimo_error`; la pantalla de corrección explica en lugar de pintar un enlace roto |
| `ENRIQUECER_GRAFO` | API GraphQL | Se degrada a las reglas de atribución sobre REST; `adiciones`/`eliminaciones` quedan **nulas**, mostradas como «no disponible», nunca como un cero |

Cuando una capacidad se degrada: se escribe una fila de origen `RUNTIME` con el cuerpo literal en su detalle; el control de interfaz afectado queda deshabilitado con el motivo escrito y **nunca falla al pulsarlo**; se abre la incidencia correspondiente; y la capacidad **sólo** vuelve a `DISPONIBLE` cuando una ejecución posterior del checklist o una llamada con éxito lo demuestran (RG-065).

### 6.7.3 Ejemplos concretos de error permanente

| Situación | Cómo se manifiesta | Clasificación |
|---|---|---|
| Cuenta Enterprise Managed User (EMU) invitada a un repositorio de otra organización | `PUT .../collaborators/{login}` responde `422` con cuerpo documentado que nombra la restricción | PERMANENTE; acceso en estado terminal, se le pide al estudiante declarar una cuenta personal |
| Organización exige verificación en dos pasos y el estudiante no la tiene activada | El estudiante no puede aceptar la invitación (hecho no observable directamente por la API con el token de instalación) | Se detecta de forma reactiva; subtipo `ORG_EXIGE_2FA` del catálogo cerrado de subtipos de error permanente |
| Cuenta marcada o bloqueada por política de la organización destino | `403` al intentar añadirla como colaboradora | Subtipo `CUENTA_BLOQUEADA_POR_ORG`, con el texto literal de GitHub |
| Permiso insuficiente para la operación | `403` con cuerpo «Resource not accessible by integration» | BLOQUEANTE; degrada la capacidad correspondiente de §6.7.2, no invalida la instalación |

### Criterios de aceptación de 6.7

1. **CA-6.7-01.** Todo endpoint de escritura del catálogo de §6.5 está cubierto por al menos una fila del mapa de capacidades de §6.7.2; una prueba automatizada lo verifica.
2. **CA-6.7-02.** Un `403` con cuerpo no reconocido se clasifica BLOQUEANTE en la prueba unitaria correspondiente, nunca PERMANENTE.
3. **CA-6.7-03.** Simulando un `422` con el cuerpo documentado de cuenta EMU, el acceso del estudiante queda en estado terminal con el mensaje que le pide declarar una cuenta personal, y el mapeo vuelve a estado `RECIBIDO` en cuanto declara una cuenta nueva.
4. **CA-6.7-04.** Degradando la capacidad `CREAR_REFERENCIA` en `ensayo`, una captura de versión completa su transacción con `tag_creado = false` y sin abortar la persistencia del `commit_sha`.
5. **CA-6.7-05.** Degradando `ENRIQUECER_GRAFO`, la interfaz muestra «no disponible» en las columnas de adiciones y eliminaciones, nunca `0`.

---

## 6.8 Webhooks

### 6.8.1 Suscripciones

La App está suscrita a exactamente siete eventos, catálogo cerrado (A-070): **`push`, `create`, `delete`, `repository`, `member`, `installation`, `installation_repositories`**.

**No existen los eventos `member_invite` ni `repository_invitation`.** La creación de una invitación de colaborador **no genera ningún evento documentado**; sólo su aceptación lo hace, a través de `member` con acción `added`, que es —por ese mismo hecho— **la única señal documentada de que un estudiante aceptó una invitación a un repositorio** (A-070, Q-2.3-30). El equivalente para la organización, `organization`/`member_invited`, tampoco se suscribe: no aplica, porque los estudiantes no entran a la organización (§6.10).

| Evento | Se usa para |
|---|---|
| `push` | Fuente rápida de nuevos commits (§6.8.4 sobre por qué no es la única) |
| `create` | Detectar ramas y tags nuevos |
| `delete` | Detectar el borrado de una rama o de una etiqueta (`ref_type = tag`, patrón `entrega/*`, sin coste de petición) |
| `repository` | Cambios de nombre, de descripción, de visibilidad y de topics del repositorio, con acción `renamed`, `edited`, `privatized`/`publicized` |
| `member` | Aceptación de invitación de colaborador (`added`) |
| `installation` | Ciclo de vida de la instalación (§6.2.6) |
| `installation_repositories` | Cambios de alcance de la instalación (§6.2.5) |

### 6.8.2 Verificación, idempotencia y respuesta rápida

Cada entrega se verifica con `X-Hub-Signature-256`, HMAC-SHA256 en comparación de tiempo constante **sobre el cuerpo crudo, antes de parsear el JSON**. Un payload sin firma válida se rechaza con `401`, se registra y **nunca se procesa** (A-070). La idempotencia se garantiza por `X-GitHub-Delivery`, con restricción única en `evento_webhook`: una reentrega no duplica commits ni transiciones de estado. **El receptor valida, persiste y responde `202` en menos de 200 ms**; todo el procesamiento ocurre después, en el trabajador (`docs/SPEC/14-infraestructura-y-despliegue.md` §14.2.4 y §14.7.1 documentan la ruta y el mecanismo de cola compartido). Un receptor que procesa en línea es un receptor que GitHub puede considerar lento y dejar de reintentar.

### 6.8.3 Límites documentados del webhook que el diseño asume

- El array `commits` del payload de `push` trae **como máximo 2.048** commits; el propio payload remite a la Commits API para el resto — no son 20, como sugería el estudio preliminar.
- GitHub **no entrega** el evento si el payload supera **25 MB**, si se empujan más de **5.000 ramas** a la vez, o para tags cuando se empujan más de tres a la vez.
- El relleno de un `push` grande se hace con `GET /repos/{o}/{r}/compare/{before}...{after}`, **paginado**: el límite de 250 commits sólo aplica a la llamada sin paginar (A-071).

### 6.8.4 Reconciliación con ETag como red de seguridad, nunca fuente única

El webhook es la fuente **rápida**, nunca la **única**. Cada 15 minutos, por repositorio activo, `GET /repos/{o}/{r}/commits` con `If-None-Match` y el ETag guardado en `cursor_sincronizacion`. Existe un hueco documentado que ni el webhook ni el filtro `since` cubren: `since` filtra por fecha del **commit**, no por fecha del **push**, y el único campo que exponía la fecha de `push` en GraphQL está deprecado y retirado. **Un commit con fecha antigua empujado hoy es invisible para cualquier reconciliador basado en `since`** (A-072).

Estrategia: se guarda `ultimo_head_sha` por rama y se compara contra el head actual con `compare`. Si `compare` devuelve `diverged` (reescritura de historia, `push --force`), se recorre el historial desde el head con `GET /commits` paginado hasta topar con un SHA conocido. **Los commits que desaparecen de la historia no se borran**: se marcan huérfanos, porque forman parte del registro de actividad real y borrarlos falsearía la línea de tiempo que documenta `docs/SPEC/10-seguimiento.md`. Un barrido completo nocturno por repositorio cierra cualquier hueco restante. El disparo por hora, la cadencia exacta y el techo de frescura garantizado son mecanismo de trabajos en segundo plano y viven en `docs/SPEC/14-infraestructura-y-despliegue.md` §14.7.4; este capítulo documenta sólo por qué la llamada a la API existe y qué garantiza.

### Criterios de aceptación de 6.8

1. **CA-6.8-01.** Un payload de webhook sin cabecera `X-Hub-Signature-256`, o con una firma inválida, se rechaza con `401` y no produce ningún efecto en el dominio.
2. **CA-6.8-02.** Reenviando la misma entrega dos veces (mismo `X-GitHub-Delivery`), la segunda no duplica ninguna fila ni ninguna transición de estado.
3. **CA-6.8-03.** El receptor de `/webhooks/github` responde en menos de 200 ms en una medición de carga, sin bloquear en ningún procesamiento síncrono.
4. **CA-6.8-04.** Un `push` con más de 250 commits sin paginar se completa con `GET .../compare` paginado sin perder ningún commit.
5. **CA-6.8-05.** Un repositorio sin ningún webhook entregado en 15 minutos sigue teniendo su actividad al día gracias a la reconciliación por ETag, verificable comparando el head local contra GitHub.
6. **CA-6.8-06.** Un `push --force` que reescribe historia dejando commits huérfanos no elimina ninguna fila de `commit`; los marca huérfanos y los conserva.

---

## 6.9 La organización nueva de plan gratuito, y la Ley 4

### 6.9.1 Sin *rulesets*, sin protección de ramas

La organización del curso es **nueva y de plan gratuito**, restricción de entrada que este capítulo no reabre (§1.3 de `ARQUITECTURA.md`). En ese plan, **no hay *rulesets* ni protección de ramas disponibles sobre repositorios privados**. Un tag de Git en uno de esos repositorios es, por tanto, **borrable por cualquiera con permiso de escritura** sobre el repositorio — lo que incluye al propio estudiante, que recibe `push` (nunca `admin`, §6.5.6) sobre su repositorio.

### 6.9.2 El `commit_sha` es la evidencia normativa; el tag es una comodidad de navegación (Ley 4)

**El `commit_sha` persistido en `version_entrega` es la evidencia normativa de una entrega.** El tag de Git que la aplicación crea sobre ese commit **no lo es**: es una comodidad de navegación para que un corrector encuentre el punto exacto sin tener que copiar un SHA. Esta distinción es la Ley 4 de la carta de arquitectura, y existe precisamente porque el plan gratuito de la organización no ofrece ningún mecanismo que impida borrar o mover ese tag.

Consecuencia directa para el respaldo: el respaldo diario cifrado que documenta `docs/SPEC/14-infraestructura-y-despliegue.md` §14.11 existe porque de él cuelga esta ley entera. La evidencia durable son **tres copias**: la fila en la base de datos, el volcado cifrado diario, y el CSV de evidencia que acompaña a ese volcado con una fila por versión de entrega vigente y superseded (`curso_slug`, `tarea_slug`, `entrega_slug`, `commit_sha`, `tag_nombre`, `fecha_corte_utc`, entre otras columnas). **La etiqueta de Git no es respaldo oficial del SHA.**

### 6.9.3 Verificación y reposición del tag, sin sobrescribir jamás la evidencia

El tag se verifica periódicamente comparando el SHA al que apunta contra el `commit_sha` capturado (§6.5.5, `GET .../git/ref/tags/{nombre}`). Los desenlaces posibles:

| Resultado de la verificación | Qué hace la aplicación |
|---|---|
| El tag apunta al mismo SHA | Nada |
| El tag fue borrado (`404`) | **Se recrea** desde `version_entrega.commit_sha`, porque reponerlo no toca ninguna evidencia; se avisa siempre, nunca en silencio |
| El tag apunta a **otro** SHA | **Nunca se sobrescribe.** Se registra el conflicto con los dos SHA enfrentados y se abre una incidencia de revisión; el `commit_sha` persistido en base sigue siendo la verdad |
| El commit ya no es alcanzable | No se pinta ningún enlace; se registra la anomalía con los metadatos disponibles |

El disparador exacto de esta verificación, su cadencia y sus catálogos de incidencia asociados los fija `docs/SPEC/08-aprovisionamiento.md` §8; este capítulo documenta el mecanismo de API y la regla dura de nunca sobrescribir un tag que apunta a un SHA distinto del capturado. La detección inmediata del borrado también llega por el webhook `delete` con `ref_type = tag` sobre el patrón `entrega/*` (§6.8.1), sin coste de petición adicional.

### Criterios de aceptación de 6.9

1. **CA-6.9-01.** Ninguna prueba de aceptación de captura de versión depende de que el tag exista: la fila de `version_entrega` con su `commit_sha` se considera evidencia suficiente por sí sola.
2. **CA-6.9-02.** Borrando manualmente un tag de entrega en `ensayo`, el siguiente barrido lo recrea desde el `commit_sha` persistido y dispone de una incidencia visible que declara la reposición.
3. **CA-6.9-03.** Moviendo manualmente un tag de entrega a otro commit en `ensayo`, la aplicación **nunca** lo reescribe: el conflicto queda registrado con los dos SHA, y el `commit_sha` en base no cambia.
4. **CA-6.9-04.** El CSV de evidencia generado junto al respaldo diario contiene `commit_sha` y `tag_nombre` como columnas distintas, y es reconstruible sin acceso a GitHub.

---

## 6.10 El equipo docente en GitHub: presupuesto de invitaciones y modelo de acceso

### 6.10.1 Estudiantes como colaboradores de repositorio; equipo docente como miembros de organización

Los **estudiantes entran como colaboradores del repositorio**, nunca como miembros de la organización (§6.5.6). El **equipo docente entra a la organización** y a un equipo `docentes` dentro de ella (§6.5.7). Son dos modelos de acceso distintos y deliberados, no una inconsistencia:

| | Estudiante | Equipo docente |
|---|---|---|
| Mecanismo | `PUT .../collaborators/{login}` con `push` | `PUT /orgs/{org}/memberships/{login}` + `PUT .../teams/{slug}/memberships/{login}` |
| Cupo consumido | Invitaciones de colaborador **por repositorio** (50/24h, sin límite si ya es miembro de la organización) | Invitaciones **a la organización** (50/24h con organización nueva o gratuita) |
| Volumen real | Hasta 200 repositorios, cada uno con su propia ventana de cupo — nunca se acerca al límite | ≤ 15 personas, una sola vez por curso |
| Visibilidad | El estudiante sólo ve su propio repositorio | El equipo `docentes` recibe lectura sobre **todos** los repositorios del curso mediante una sola llamada por repositorio |

**Por qué esta asimetría es deliberada.** Invitar a los estudiantes a la organización activaría el cupo que sí es restrictivo en una organización nueva —200 invitaciones contra un tope de 50 cada 24 horas serían cuatro ventanas de un día completo— y abriría un agujero de privacidad: la visibilidad que un miembro de la organización tiene sobre los repositorios de sus compañeros depende de `default_repository_permission`, campo que no consta como legible con token de instalación. Diseñar el acceso de doscientos estudiantes sobre un campo que quizá no se pueda leer es inaceptable.

### 6.10.2 Presupuesto: ≤ 15 invitaciones por curso, una sola vez

El único consumo del cupo de invitación a la organización es el **equipo docente**: profesores, ayudantes y, para la entrega, el evaluador. Se emiten en el paso de vinculación, no durante el aprovisionamiento de repositorios. **Presupuesto declarado: ≤ 15 invitaciones a la organización por curso**, muy por debajo de las 50 de una ventana de 24 horas (§1.3 de `ARQUITECTURA.md`, A-163). Una vez que son miembros de la organización, añadirlos como colaboradores de lectura de cada repositorio —vía de respaldo, §6.10.3— **no consume cupo alguno** y responde `204`.

### 6.10.3 Mecánica de la invitación a la organización y al equipo

**Vía principal — equipo `docentes`.** Al vincular el curso, antes de crear ningún repositorio: se crea el equipo con `POST /orgs/{org}/teams` (`privacy: closed`), y cada miembro activo del curso se incorpora a la organización y al equipo con las dos llamadas de §6.5.7. El acceso de lectura sobre cada repositorio se concede con **una sola llamada por repositorio** al equipo, no una por persona: `PUT /orgs/{org}/teams/{team_slug}/repos/{org}/{repo}` con `{"permission": "pull"}`. Incorporar a un ayudante nuevo después no toca ningún repositorio: basta añadirlo al equipo. Retirarlo lo saca del equipo, y quitar a alguien de un equipo **revoca el acceso concedido a través de ese equipo** — una llamada retira la lectura sobre los cientos de repositorios del curso, sin recorrerlos uno a uno.

**Vía de respaldo — colaborador individual.** Si el equipo no puede crearse o poblarse, se ejecuta `PUT /repos/{o}/{r}/collaborators/{login}` con `pull` por cada persona con acceso al curso. Como los docentes ya son miembros de la organización, esta llamada responde `204` sin crear invitación y sin consumir cupo. La diferencia importante frente a la vía principal: un permiso de colaborador otorgado directamente **no se retira al salir de un equipo**, así que retirar a alguien por esta vía exige recorrer sus accesos repositorio a repositorio con `DELETE .../collaborators/{login}`. **Nunca `write`, nunca `admin`** en ninguna de las dos vías: el equipo docente recibe exclusivamente `pull`.

**Estado y reconciliación por persona.** La membresía de organización de cada docente se persiste, se reconcilia y se vigila: emitida (`PENDIENTE`), reconciliada por barrido horario (`GET /orgs/{org}/memberships/{login}` → `active`/`pending`), y sujeta a la caducidad documentada de siete días de la invitación a la organización. A los 5 días en `PENDIENTE` se reemite (idempotente); a los 7, sin aceptar, se marca expirada; tope de tres reenvíos, uno cada cinco días; agotado el tope, queda en error con la acción de avisar por correo (RG-096). El evaluador entra por este mismo camino, de modo que su invitación queda vigilada igual que la de cualquier otro miembro.

**Regla dura sobre el enlace del corrector.** El enlace al código de un repositorio sólo se pinta si el `acceso_docente_repositorio` de ese repositorio está `CONCEDIDO` **y**, cuando la vía es el equipo, la membresía de organización de quien está mirando está `ACTIVA` (RG-097). Con la vía de respaldo, la segunda condición se evalúa sobre la fila de acceso de esa persona en particular. Nunca se entrega un enlace que va a devolver `404`.

### Criterios de aceptación de 6.10

1. **CA-6.10-01.** Un curso recién vinculado con un equipo docente de 8 personas emite exactamente 8 invitaciones a la organización, nunca más, y ninguna de ellas cuenta contra el cupo de invitación por repositorio.
2. **CA-6.10-02.** El acceso de lectura del equipo docente sobre 600 repositorios se concede con 600 llamadas —una por repositorio, no 4.800 (una por repositorio y por persona)—.
3. **CA-6.10-03.** Retirando a un ayudante incorporado por la vía principal, una sola llamada de eliminación de membresía de equipo revoca su lectura sobre todos los repositorios del curso.
4. **CA-6.10-04.** Retirando a un ayudante incorporado por la vía de respaldo, la aplicación recorre y revoca sus accesos repositorio a repositorio, sin asumir que salir del equipo bastó.
5. **CA-6.10-05.** Una invitación a la organización sin aceptar durante 5 días dispara un reenvío idempotente; sin aceptar durante 7, queda marcada expirada; tres reenvíos agotados detienen el reenvío automático y abren una acción manual.
6. **CA-6.10-06.** La pantalla de corrección no pinta el enlace al repositorio de un corrector cuya membresía de organización está `PENDIENTE`; muestra en su lugar el motivo y el enlace de aceptación.

---

## 6.11 Reglas duras: qué la aplicación nunca hace sobre GitHub

### 6.11.1 Nunca modifica ni elimina un objeto cuyo identificador no proceda de una fila propia

**Regla general de todo este capítulo, verificable por prueba de arquitectura punto a punto:** toda escritura o eliminación contra la API de GitHub actúa sobre un objeto cuyo identificador —`github_repo_id`, `installation_id`, `login` de colaborador o de organización, `tag` de referencia— procede de una fila que la propia aplicación escribió o espejó, nunca de un valor construido, adivinado o recibido de un tercero sin verificación previa. Es la aplicación concreta de la Ley 2 y de la Ley 3 al lado de escritura del sistema: la aplicación no actúa sobre lo que no reconoce como suyo.

### 6.11.2 Lista blanca de `PATCH /repos/{o}/{r}`

**`name` está prohibido en todo punto del código, sin excepción, verificado por prueba de arquitectura.** El nombre de un repositorio no cambia nunca después de su creación (`docs/SPEC/08-aprovisionamiento.md` §8, para el porqué de negocio). Con los demás campos, la prueba falla salvo en los sitios de llamada enumerados en una lista blanca dentro de la propia prueba (RG-084):

| Campo | Sitios de llamada permitidos |
|---|---|
| `description` | (a) Reasignación de sujeto por fusión de Canvas confirmada por un docente; (b) vinculación manual de un repositorio existente; (c) restauración del marcador de identidad tras un `repository`/`edited` que lo borró |
| `private` | El manejador de `repository`/`privatized` o `publicized`, que restaura `private: true` con incidencia bloqueante |
| `archived` | El trabajo que ejecuta un desarchivado aprobado por una persona; `archived: true` no se escribe nunca desde ese mismo sitio |

**La descripción no se reescribe por un cambio de nombre legible.** Un renombrado de grupo en Canvas actualiza el espejo interno y la interfaz muestra el nombre vigente junto al nombre inmutable del repositorio; **no produce ninguna llamada a GitHub**. La descripción sólo se toca cuando el marcador de identidad dejaría de identificar al sujeto correcto.

### 6.11.3 Catálogo cerrado de eliminaciones externas: nueve, y tres son de GitHub

La lista cerrada de eliminaciones que la aplicación ejecuta contra un proveedor externo tiene **nueve** entradas (RG-191, corrigiendo las seis originales de A-030); **tres** son contra GitHub:

| Qué se borra | Por qué es legítimo |
|---|---|
| `DELETE /repos/{org}/{repo}/collaborators/{login}` | Es un permiso, no un dato de dominio; retirarlo es exactamente lo que exige la revocación de acceso de un estudiante o de un docente por la vía de respaldo |
| `DELETE /orgs/{org}/teams/{team_slug}/memberships/{login}` | Retira la lectura del equipo docente sobre todos los repositorios de una vez |
| `DELETE /orgs/{org}/memberships/{login}` | **Sólo** si la aplicación fue quien incorporó a esa persona a la organización: deshace lo que hizo y nada más |

**Ninguna de las tres toca un dato de dominio.** La prueba de arquitectura de §6.5.2 sigue vigente sin excepción: `DELETE /repos/{owner}/{repo}` no se invoca jamás, y **nunca se borra un repositorio, un commit, un tag de entrega ni una nota publicada**. Añadir una décima eliminación externa es una decisión que se registra en `ARQUITECTURA.md`, no una que se toma en el código.

### 6.11.4 Autoría: nunca a nombre de una persona del equipo

**No se envían los campos `author` ni `committer`** en `POST /repos/{o}/{r}/git/commits` ni en `PUT /repos/{o}/{r}/contents/{ruta}` (§6.5.3, §6.5.2), de modo que todo commit escrito por la aplicación queda a nombre de la **cuenta `[bot]` de la instalación** y **nunca a nombre de un integrante del equipo**. Una prueba de arquitectura falla la construcción si aparece un literal `"author"` o `"committer"` en el cuerpo de esas dos llamadas, dentro de `backend/`. La única excepción de todo el proyecto es la de `infra/` y el curso de demostración (§6.3.3), acotada por escrito y nunca presente en el código de la aplicación (A-196, RG-090).

Cuatro consecuencias, todas ya soportadas por el resto de la especificación: el commit inicial de andamiaje se excluye del recuento de participación de `docs/SPEC/10-seguimiento.md`; la cascada de atribución lo deja `SIN_ATRIBUIR`, porque una cuenta de bot no tiene mapeo estudiante vigente; en la línea de tiempo aparece etiquetado como commit de la aplicación; y el estudiante ve que quien creó su repositorio es la App del curso, reconocible y distinguible de una suplantación (§6.2.2).

### 6.11.5 Nunca escribe en `.github/workflows/`, nunca toca Actions ni Codespaces por repositorio

La pantalla de administración de archivos del repositorio base rechaza cualquier subida bajo `.github/workflows/`, con o sin el permiso `Workflows: write` concedido (§6.4): es una decisión de producto, no una consecuencia del permiso. Actions se gobierna **por política de organización, una sola vez, decidida por el profesor** desde los ajustes de GitHub; la aplicación no la deshabilita repositorio a repositorio —costaría al menos una llamada más por cada uno de hasta 600 repositorios sobre un permiso cuyo mínimo puede no estar disponible—. Codespaces queda fuera de alcance declarado: la aplicación no crea, no configura ni monitoriza Codespaces, y ningún requisito `R2.x.y` lo exige.

### Criterios de aceptación de 6.11

1. **CA-6.11-01.** Una prueba de arquitectura falla la construcción si aparece un `PATCH /repos/{o}/{r}` con el campo `name`, en cualquier punto del código.
2. **CA-6.11-02.** Una prueba de arquitectura falla la construcción si aparece un `PATCH /repos/{o}/{r}` con `description`, `private` o `archived` fuera de los sitios de llamada enumerados en la lista blanca de §6.11.2.
3. **CA-6.11-03.** Una búsqueda en `backend/adaptadores/` confirma que las únicas llamadas `DELETE` contra la API de GitHub son las tres de §6.11.3, y que ninguna se ejecuta sin comprobar antes la condición que la autoriza.
4. **CA-6.11-04.** Una prueba de arquitectura falla la construcción si aparece un literal `"author"` o `"committer"` en el cuerpo de `POST /git/commits` o de `PUT /contents` dentro de `backend/`.
5. **CA-6.11-05.** Ningún archivo se sube bajo `.github/workflows/` desde ninguna pantalla de la aplicación, y una prueba de validación de ruta lo confirma con un caso exacto.
6. **CA-6.11-06.** `PUT /repos/{o}/{r}/actions/permissions` no aparece en ningún trabajo del catálogo de `docs/SPEC/14-infraestructura-y-despliegue.md` §14.7.4 más allá de la creación inicial opcional del repositorio.

---

## 6.12 Casos borde del acceso de colaboradores estudiantiles

Estos casos son mecanismo de API puro; la máquina de estados de `acceso_repositorio` y sus disparadores de negocio viven en `docs/SPEC/08-aprovisionamiento.md`.

### 6.12.1 `201` frente a `204`, y por qué no hay estado pendiente que esperar en el segundo caso

`PUT /repos/{o}/{r}/collaborators/{login}` devuelve **`201`** cuando crea una invitación nueva, y **`204`** en los supuestos en los que el acceso queda concedido de inmediato —entre ellos, que el invitado ya sea miembro de la organización—. Un `204` **salta el estado pendiente**: no tiene sentido esperar la aceptación de una invitación que nunca se creó (Q-2.3-30).

### 6.12.2 No existe evento de rechazo; el estado se llama «rechazada o caducada»

No hay ningún evento documentado de rechazo de invitación de repositorio, y una invitación rechazada es indistinguible de una revocada o de una que nunca se aceptó. Por eso la aplicación **nunca** afirma en pantalla que un estudiante «rechazó» algo que no puede probar: el estado se llama `DESAPARECIDA` internamente y la interfaz dice literalmente «rechazada o caducada» — nombrarlo `RECHAZADA` sería mentir en la interfaz.

### 6.12.3 Invitación siempre por `login`, nunca por correo

La invitación a un repositorio se emite siempre por `login`, nunca por dirección de correo. La única exigencia documentada de correo verificado en GitHub está escrita para la invitación **a la organización** por dirección de correo, un objeto distinto que este proyecto no usa para estudiantes (§6.10.1). El `login` es lo que el estudiante declara y lo que se valida contra `GET /users/{login}`, del que se guardan el `id` numérico y el `login` canónico devuelto por la API — nunca el correo, que puede no ser legible con el token del profesor.

### 6.12.4 No hay estado propio para «cuenta recién creada sin correo verificado»

Una cuenta de GitHub recién creada, con el correo sin verificar, se trata como cualquier invitación pendiente común: no existe campo documentado que exponga si el correo de otra persona está verificado, y crear un estado inobservable sería afirmar en pantalla algo que la aplicación no puede probar. La mitigación real ocurre antes del problema: el texto de la tarea de registro de Canvas —que fija `docs/SPEC/07-estudiantes-y-grupos.md`— advierte al estudiante que verifique su correo antes de declarar su usuario.

### 6.12.5 Cuentas Enterprise Managed User (EMU)

Detectadas exclusivamente por el `422` documentado que `PUT .../collaborators/{login}` devuelve cuando el invitado es una cuenta EMU (§6.7.3). No se intenta adivinar por la forma del `login`, porque ese patrón no consta como documentado y adivinarlo produciría falsos rechazos sobre cuentas legítimas.

### 6.12.6 SAML SSO e IP allow list: fuera de alcance soportado, declarado por adelantado

Si la organización vinculada exige inicio de sesión único (SAML SSO) o restringe el acceso por lista de IP permitidas, la aplicación **no lo soporta ni lo detecta preventivamente**: la manifestación es un `403` al operar, que el clasificador de §6.7.1 trata como BLOQUEANTE con el mensaje literal. La organización de plan gratuito del curso no tiene estas restricciones disponibles por definición del plan; si se vinculara una organización institucional que sí las tuviera, la limitación se declara por escrito antes de vincular.

### Criterios de aceptación de 6.12

1. **CA-6.12-01.** Un `PUT collaborators` que responde `204` porque el invitado ya era miembro de la organización deja el acceso en estado concedido directamente, sin pasar por un estado de invitación pendiente.
2. **CA-6.12-02.** Ningún texto de interfaz usa la palabra «rechazada» sola; el texto exacto para ese caso es «rechazada o caducada».
3. **CA-6.12-03.** Una búsqueda en el código confirma que ninguna invitación a un repositorio se emite por dirección de correo.
4. **CA-6.12-04.** Simulando el `422` documentado de cuenta EMU en `ensayo`, el acceso del estudiante afectado queda en estado terminal con el mensaje que le pide una cuenta personal, sin reintento automático.
5. **CA-6.12-05.** La documentación de alcance declarado (la pantalla pública `/alcance` que fija `docs/SPEC/13-interfaz.md`) nombra explícitamente que SAML SSO y la lista de IP permitidas están fuera de lo soportado.
