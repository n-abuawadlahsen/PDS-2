# 14. Infraestructura, despliegue y CI/CD

Este capítulo especifica dónde corre la aplicación, con qué artefactos se construye, cómo se despliega, cómo se opera y cómo se sostiene hasta el 31 de octubre de 2026. Cubre la topología de despliegue, la base de datos, los entornos, el motor de trabajos en segundo plano, la gestión de configuración y secretos, las puertas de construcción, el despliegue continuo con su reversión, las migraciones de esquema, el respaldo con su restauración probada, el correo transaccional como pieza de infraestructura y el régimen de sostenimiento posterior a la entrega.

Todo lo que sigue está redactado para alguien que no ha leído ningún documento previo del proyecto. Cada sección cita los requisitos `R2.x.y` del enunciado que satisface y las decisiones de la carta de arquitectura (`A-nnn`) y de las actas de reconciliación (`RG-nnn`) de las que proviene. Donde esta especificación completa un hueco que ninguna fuente cerraba, la decisión aparece marcada con **[DECISIÓN NUEVA]**.

**Contexto mínimo.** La aplicación es una herramienta web para el equipo docente de un curso de programación (profesores y ayudantes) que integra Canvas LMS y GitHub para gestionar tareas de programación. Los estudiantes **no** son usuarios de la aplicación. El equipo tiene rol de **profesor** en Canvas, nunca de administrador de la instancia.

**Roles de operación citados en todo el capítulo** (los nombres propios viven en `docs/operacion.md`, escritos antes del 10 de septiembre a las 09:00):

| Rol | Responsabilidad |
|---|---|
| **RI** | Infraestructura y entrega: Render, Vercel, Supabase, dominio, DNS, secretos, CI/CD, respaldo |
| **RX** | Integraciones externas: `ClienteCanvas`, `ClienteGitHub`, GitHub App, mediciones |
| **RD** | Dominio y datos: modelo, máquinas de estado, catálogo de trabajos |
| **RF** | Interfaz: React, pantallas y textos |

Cada rol tiene un **segundo** nombrado y capaz de defenderlo. Ningún rol es dueño exclusivo de un secreto ni de una cuenta.

---

## 14.1 Principios y restricciones de entrada

Las decisiones de este capítulo son aplicación de ocho principios. Ninguna decisión posterior los contradice.

| # | Principio | Consecuencia operativa | Origen |
|---|---|---|---|
| 1 | **Espejo, no caché** | La base de datos de la aplicación es un espejo mantenido de Canvas y de GitHub. **Ninguna vista consulta una API externa para renderizarse.** Toda lectura externa ocurre dentro de un trabajo en segundo plano | Ley 1; **R2.5.1** |
| 2 | **Nada se sobrescribe** | Versiones de entrega, mapeos, fechas efectivas y publicaciones de nota son *append-only*. La infraestructura nunca ejecuta una operación que destruya evidencia | Ley 2; **R2.4.6**, **R2.4.7** |
| 3 | **La evidencia vive en nuestra base** | El `commit_sha` persistido es la evidencia normativa de una entrega. El respaldo diario cifrado existe porque de él cuelga esa ley entera | Ley 4; A-016, A-170 |
| 4 | **Un límite de una API externa nunca se pinta como error del equipo** | Se pinta como estado transitorio con hora de reintento visible | Ley 5; A-116 |
| 5 | **El coste de infraestructura se paga donde compra cumplimiento** | §4 del enunciado acota «libre y gratuito» a *lenguaje, frameworks o librerías*, y no dice nada del alojamiento. Interpretarlo como coste cero en infraestructura obligaría a incumplir **R2.3.10**, **R2.4.5**, **R2.5.1**, **R2.5.2** y **R2.6.1** | A-004; §4 |
| 6 | **Un solo motor de datos** | PostgreSQL es la única base de datos. No hay Redis, no hay almacén de objetos, no hay segundo motor. Cada servicio eliminado es un modo de fallo menos en un despliegue que debe seguir en pie hasta el 31 de octubre | A-005, A-112 |
| 7 | **La infraestructura es código revisable** | Los dos servicios de Render se declaran en `infra/render.yaml` versionado, no a mano en el panel. Ninguna configuración de despliegue vive únicamente en una consola web | Q-infraestructura-30 |
| 8 | **Reproducibilidad del artefacto** | Ni Render ni Vercel resuelven una versión en el momento de construir. Un redespliegue el 20 de octubre produce el mismo artefacto que el del 6 de octubre | §3.2; Q-infraestructura-30, Q-infraestructura-31 |

**Restricciones de entrada que este capítulo no reabre:**

| Restricción | Enunciado de la restricción |
|---|---|
| Rol en Canvas | El equipo es **profesor**, no administrador. No hay Developer Key propia en el caso general, ni `as_user_id`, ni informes de cuenta, ni acceso garantizado a `sis_user_id` |
| Organización de GitHub | Nueva y de plan gratuito. La protección de ramas sólo está disponible en repositorios públicos |
| Dos despliegues | Frontend y backend viven en proveedores distintos y en subdominios distintos del mismo dominio propio |
| Estudiantes | No son usuarios de la aplicación y nunca reciben credenciales de acceso a ella |

### Criterios de aceptación de 14.1

1. `infra/render.yaml` existe en el repositorio y declara los dos servicios; ninguna propiedad de servicio se ha editado a mano en el panel de Render sin quedar reflejada en ese fichero.
2. Una búsqueda en `backend/app/api/` no encuentra ninguna invocación a `ClienteCanvas` ni a `ClienteGitHub` fuera de las seis escrituras síncronas autorizadas; la puerta de construcción correspondiente está en verde.
3. El inventario de servicios contratados es exactamente cuatro (web, trabajador, base de datos, frontend) y no existe ninguna cuenta activa de Redis, de almacén de objetos ni de un segundo motor de base de datos.

---

## 14.2 Topología de despliegue, dominios y coste

### 14.2.1 Servicios

La aplicación se despliega en **cuatro servicios y ninguno más** (**A-003**, **A-004**, **A-005**, **A-002**):

| Servicio | Proveedor | Plan | Qué ejecuta | Se paga |
|---|---|---|---|---|
| `api` (web) | Render | Pago mínimo | Servicio HTTP de la API REST, montado desde la imagen Docker del backend | Sí |
| `trabajador` (*background worker*) | Render | Pago mínimo | Planificador y ejecutor de la cola de trabajos, desde la **misma imagen** | Sí |
| Base de datos | Supabase | Gratuito | PostgreSQL, único almacén del sistema | No |
| Frontend | Vercel | Gratuito | Estáticos de la SPA React servidos desde CDN | No |

**Los dos servicios de Render están contratados en plan de pago desde el 10 de septiembre de 2026 hasta el 31 de octubre de 2026** (**A-004**, **A-161**). El plan gratuito de Render suspende un servicio web que pasa 15 minutos sin tráfico entrante, y un servicio suspendido produce tres incumplimientos simultáneos y visibles: se pierden los webhooks de GitHub que alimentan **R2.5.2** y **R2.5.3**; no corren los trabajos periódicos, de modo que no hay creación progresiva (**R2.3.10**), ni captura de versión al cierre (**R2.4.5**), ni informe diario (**R2.6.1**); y la primera carga tarda decenas de segundos, lo que contradice **R2.5.1**. Sostener un plan gratuito con un *pinger* externo queda **expresamente descartado**: mantiene el servicio vivo pero no elimina el arranque en frío del primer golpe.

**Separar web y trabajador es una decisión de diseño, no de escalado** (**A-003**): una saturación del trabajador no degrada la interfaz que el evaluador está mirando, y cada mitad se reinicia por su cuenta.

**Presupuesto declarado: hasta 40 dólares estadounidenses para toda la ventana**, con este desglose: dos servicios Render a su precio publicado del plan de pago mínimo durante aproximadamente mes y medio, más el dominio por un año. Vercel, Supabase y el proveedor de correo, cero. **RI confirma el precio publicado el 10 de septiembre antes de contratar y lo registra en `docs/operacion.md`**; si excediera los 40 dólares, se escala al equipo en el momento.

**Titularidad y acceso.** Las cuentas de Render, Vercel, Supabase y Google Cloud se crean con la **cuenta de correo operativa del equipo**, nunca con la personal de nadie, con verificación en dos pasos activada. **A la consola de producción acceden exactamente dos personas: RI y su segundo.** El medio de pago lo pone RI; si su medio de pago fallara, la contingencia declarada es la tarjeta del segundo de RI **ese mismo día**, y no se conmuta a plan gratuito. La retirada de los servicios está en el calendario del equipo para el **1 de noviembre**.

### 14.2.2 Dominio y URLs

**Se registra un dominio propio y la URL definitiva se congela antes de que exista una sola línea de configuración externa** (**A-008**). El dominio se compra el **10 de septiembre por la tarde**, inmediatamente después del hito «decisión del nombre del producto y del dominio» de las 09:00 de ese día, por un año, con renovación automática desactivada y baja programada. **RI lo compra y lo administra.**

| Entorno | Frontend | Backend |
|---|---|---|
| `produccion` | `https://app.<dominio>` (Vercel) | `https://api.<dominio>` (Render) |
| `ensayo` | `https://app-ensayo.<dominio>` | `https://api-ensayo.<dominio>` |
| local | `http://localhost:5173` | `http://localhost:8000` |

**No se opera sobre `*.vercel.app` ni sobre `*.onrender.com`.** Los certificados los gestionan Vercel y Render. **La URL que se entrega el 16 de septiembre es exactamente la que se entrega el 6 de octubre**, y se mantiene en pie hasta el **31 de octubre inclusive**.

El motivo es de fiabilidad, no de estética: con los dos subdominios bajo el mismo sitio registrable, la cookie de sesión es *same-site* y **desaparecen por construcción** el bloqueo de cookies de terceros, la mitigación de seguimiento de Safari y el parámetro `state` de OpenID Connect que no sobrevive al redirect en ventana privada. Además, el dominio propio es el que habilita SPF y DKIM propios para **R2.6.4**.

**Contingencia fechada** (**A-010**): si el dominio propio no está operativo el **12 de septiembre**, se conmuta al mecanismo de sesión alternativo (*token* de acceso de 15 minutos en memoria del frontend con *refresh* rotativo, hasheado en base, con detección de reutilización y revocación en cadena). **La decisión de conmutar se toma el 12 de septiembre, no el 15.**

### 14.2.3 URIs registradas ante terceros

Las diez entradas siguientes se registran el **10 de septiembre** y ninguna después. La lista es la lista de verificación literal de ese día, y su cumplimiento se registra con captura fechada en `.workflow/mediciones/`.

| Proveedor | Entrada | Valor |
|---|---|---|
| Google OIDC, cliente `produccion` | Redirect URI | `https://api.<dominio>/auth/google/callback` |
| Google OIDC, cliente `ensayo` | Redirect URI | `https://api-ensayo.<dominio>/auth/google/callback` |
| Google OIDC, cliente local | Redirect URI | `http://localhost:8000/auth/google/callback` |
| GitHub App `produccion` | Callback URL | `https://api.<dominio>/github/instalacion/callback` |
| GitHub App `produccion` | Setup URL (con «redirect on update») | `https://api.<dominio>/github/instalacion/setup` |
| GitHub App `produccion` | Webhook URL | `https://api.<dominio>/webhooks/github` |
| GitHub App `ensayo` | Callback y Setup | Equivalentes bajo `api-ensayo.<dominio>` |
| GitHub App `ensayo` | Webhook URL | Un canal de `smee.io` |
| Developer Key de Canvas (condicionada) | `redirect_uri` | `https://api.<dominio>/auth/canvas/callback` |
| Proveedor de correo | Remitente y DNS | `informes@send.<dominio>`, con SPF y DKIM publicados |

**Webhooks en desarrollo.** La GitHub App de `ensayo` apunta su webhook a un canal de `smee.io`, y contra ese mismo canal se conectan a la vez el backend desplegado de `ensayo` y el cliente `smee` de cada desarrollador. Así se prueban webhooks en local **sin registrar una tercera GitHub App**. **La App de `produccion` nunca pasa por `smee.io`**: apunta directamente a `https://api.<dominio>/webhooks/github`. Si `smee.io` no estuviera disponible en un día de desarrollo, se sustituye por un túnel equivalente cambiando únicamente la URL del webhook de la App de `ensayo`, sin tocar el código.

### 14.2.4 Rutas de infraestructura expuestas por el backend

| Ruta | Método | Sesión | Para qué |
|---|---|---|---|
| `/salud` | `GET` | No | Vivo. No toca la base de datos |
| `/estado` | `GET` | Anónima agregada / completa con sesión | Listo y diagnóstico |
| `/webhooks/github` | `POST` | No | Receptor de webhooks; valida firma, persiste y responde `202` en menos de 200 ms |
| `/interno/latido` | `POST` | No, firmado por HMAC | Vigilante externo del planificador |
| `/auth/google/callback` | `GET` | No | Retorno de OpenID Connect |
| `/github/instalacion/callback` | `GET` | Sí | Retorno de instalación de la GitHub App |
| `/github/instalacion/setup` | `GET` | Sí | Retorno de actualización de la instalación |

Todas ellas figuran en la lista cerrada de rutas sin sesión del capítulo de gobierno y de seguridad, y la **puerta de construcción «superficie sin sesión»** falla si aparece una ruta sin dependencia de sesión que no esté en esa lista.

### Criterios de aceptación de 14.2

1. `https://app.<dominio>` y `https://api.<dominio>` responden con certificado válido y sin advertencia del navegador, y ninguna de las dos redirige a un dominio de proveedor.
2. Una consulta al panel de Render muestra los dos servicios en plan de pago con fecha de contratación del 10 de septiembre.
3. `GET https://api.<dominio>/salud` devuelve `200` con `estado`, `version`, `servicio` y `hora` en menos de 50 ms, sin consultar la base de datos.
4. La lista de diez URIs de 14.2.3 está registrada en los tres proveedores y hay una captura fechada de cada una en `.workflow/mediciones/`.
5. La URL entregada por Canvas el 16 de septiembre y la entregada el 6 de octubre son idénticas carácter a carácter.
6. `docs/operacion.md` nombra a RI y a su segundo como únicas personas con acceso a la consola de producción, y el resto del equipo confirma por escrito que no dispone de la cadena de conexión de producción.

---

## 14.3 Base de datos

### 14.3.1 Proveedor y topología

**PostgreSQL gestionado por Supabase, plan gratuito, es la única base de datos del sistema** (**A-005**). Se usan **dos proyectos**, uno por entorno: `produccion` y `ensayo`, que es exactamente lo que concede el plan.

Las alternativas se descartan por documentación, no por preferencia:

| Alternativa | Hecho verificado | Consecuencia |
|---|---|---|
| PostgreSQL gratuito del PaaS | Las bases gratuitas **expiran 30 días después de su creación** y una base expirada es **inaccesible** salvo pago; los días de gracia sirven para pagar, no para consultar | Una base creada el 10 de septiembre deja de responder el 10 de octubre, en mitad de la ventana que §3.2 protege. Incumplimiento garantizado |
| Neon en plan gratuito | Tope de **100 CU-hours** por proyecto | Con un trabajador que consulta la base cada 30 segundos el *compute* está prácticamente siempre despierto y el presupuesto mensual se agota. El arranque en frío no era el problema |
| SQLite con disco persistente | Incompatible con dos procesos y con `SELECT … FOR UPDATE SKIP LOCKED` | Descartada |
| MySQL o MariaDB | Sin `pg_advisory_lock`, sin `jsonb`, sin índices únicos parciales | Descartada: cuatro tablas críticas dependen de índices únicos parciales |
| Base documental | El modelo es relacional, con 70 entidades y unicidades duras que son la última línea de defensa | Descartada |

**Supabase encaja** porque su criterio de pausa es la **inactividad de una semana** y unas pocas peticiones diarias bastan para evitarla —actividad que el planificador produce por diseño con su tick de 30 segundos—; porque **500 MB por proyecto** es holgado frente al presupuesto de la sección 14.3.3; y porque concede **dos proyectos**, que son exactamente los dos entornos exigidos.

**La base definitiva se crea el 10 de septiembre y no se recrea nunca.** Recrearla entre la parcial y la final está prohibido: borraría la evidencia de la demostración del 16 de septiembre, incluida la bitácora que la hace defendible el 7 de octubre.

### 14.3.2 Conexiones

| Parámetro | Valor fijado | Motivo |
|---|---|---|
| Modo de conexión | **Siempre por el conector con *pooling*** del proveedor | El límite real de conexiones simultáneas del plan gratuito no está documentado |
| `pool_size` | **10 por proceso** (web y trabajador por separado) | Techo propio conservador en vez de descubrir el límite en producción |
| `max_overflow` | **0** | Un tope duro es un tope duro |
| Contingencia si la medición del 13 de septiembre no admite 10 | Bajar a **5** y activar el modo `transaction` del *pooler* | Es configuración, no rediseño |

### 14.3.3 Tamaño, retención y frenos

**Presupuesto de tamaño: del orden de 160 MB sobre 500 MB** para un curso de 200 sujetos, que es el peor caso acotado por construcción. Un curso de demostración de 30 estudiantes ocupa del orden de 5 MB; un curso de 60 repositorios con 3 tareas y 8 semanas, del orden de 55 MB.

Un trabajo diario mide `pg_database_size` y aplica **dos escalones, automáticos y sin intervención**:

| Escalón | Umbral | Qué ocurre |
|---|---|---|
| Aviso y acortado | **300 MB** (60 %) | Correo de aviso con cargo a la reserva operativa; la retención del cuerpo de `evento_webhook` baja a **3 días**; la de `accion_ui` baja a 3 días y la de `cubo_tasa` a 6 horas |
| Freno duro | **400 MB** (80 %) | Se abre la incidencia bloqueante `BASE_CERCA_DEL_LIMITE` y **se deja de persistir cuerpos nuevos**, conservando cabeceras |

**En ninguno de los dos escalones se toca un solo dato de evidencia.** La aplicación nunca deja de ingerir *commits*, nunca deja de capturar versiones y nunca cae por esta causa.

Política de retención, en resumen (la tabla completa por entidad vive en el capítulo de modelo de datos):

| Clase de dato | Retención |
|---|---|
| `commit`, `autoria_commit`, `version_entrega`, `bitacora`, `publicacion_nota` | **Sin purga**: son evidencia |
| Cabecera de `evento_webhook` | Indefinida |
| Cuerpo (`payload`) de `evento_webhook` | **7 días**, truncado a 64 KB al persistir; 3 días por encima de 300 MB |
| `trabajo` en estado terminal | 30 días |
| `sincronizacion`, `presupuesto_api`, `resultado_invariante` | 90 días |
| `accion_ui` | 14 días |
| `cubo_tasa` | 24 horas |
| Ficheros de respaldo | 14 días |

La purga la ejecuta el trabajo `purga_retencion` a las **03:00** diarias. **Nunca toca `commit`, `autoria_commit`, `version_entrega`, `bitacora` ni `publicacion_nota`.**

### 14.3.4 Lo que no se guarda

| Artefacto | ¿Se guarda? | Motivo |
|---|---|---|
| Zip o *tarball* del código del repositorio | **No** | La aplicación no descarga ni archiva el código: entrega enlaces. La evidencia es el `commit_sha` |
| Archivos que el profesor sube al repositorio base | **No se persisten** | Se transmiten a GitHub dentro de la petición y el búfer temporal se descarta. El repositorio base **es** el almacén. Topes propios: 5 MB por archivo, 50 archivos y 25 MB por repositorio base, rechazados por encima con mensaje que remite a `git push` |
| Adjuntos de comunicaciones | **No existen** | La aplicación no envía adjuntos por ningún canal |

El sistema de archivos de Render se considera **efímero y de sólo tránsito**: nada persiste allí más allá de la petición o del trabajo en curso.

### Criterios de aceptación de 14.3

1. La cadena de conexión configurada en los dos servicios apunta al conector con *pooling*, y una inspección del pool de la aplicación muestra `pool_size = 10` y `max_overflow = 0` en cada proceso.
2. `GET /estado` expone el tamaño ocupado de la base y su porcentaje sobre el límite, y ese valor coincide con `SELECT pg_size_pretty(pg_database_size(current_database()))`.
3. Cargado el conjunto de datos de demostración, el tamaño medido queda registrado con fecha, comando y salida en `.workflow/mediciones/`, y es inferior a 300 MB.
4. Forzando artificialmente el umbral de 300 MB en `ensayo`, la retención del cuerpo de `evento_webhook` baja a 3 días y llega un correo operativo; ninguna fila de `commit`, `version_entrega`, `bitacora` ni `publicacion_nota` desaparece.
5. Existen exactamente dos proyectos de base de datos, uno por entorno, y la cadena de conexión de `ensayo` no coincide con la de `produccion`.

---

## 14.4 Entornos y barreras de aislamiento

**Hay tres entornos y la separación es física, no una convención** (**A-006**, **A-167**, **Q-infraestructura-25**).

| Entorno | Base de datos | Canvas | GitHub | Correo |
|---|---|---|---|---|
| `produccion` | Proyecto Supabase propio | Instancia institucional, curso real | Organización `<marca>-curso` y GitHub App `<marca>` | Proveedor transaccional real |
| `ensayo` | **Segundo** proyecto Supabase | **`CANVAS_MODO=doble`**, con respuestas grabadas | Organización `<marca>-ensayo` y App `<marca>-ensayo` | Implementación de **consola** |
| local, uno por desarrollador | **PostgreSQL propio en Docker**, nunca compartido, nunca Supabase | `CANVAS_MODO=doble` | Organización `<marca>-ensayo`, con `curso.slug` propio `local-<iniciales>` y webhooks por `smee.io` | Consola |

**Cada desarrollador tiene su propia base local.** Compartir una base de desarrollo produce migraciones pisadas y estados irreproducibles.

**Por qué `ensayo` no apunta a Canvas real por defecto.** El equipo tiene rol de profesor: no puede crear cursos por API y recibe **un** curso. Prometer un entorno destructivo que no existe sería peor que no prometerlo. Por eso `ensayo` arranca en modo doble, alimentado por **respuestas grabadas del curso real en modo sólo lectura**, anonimizadas al grabar y versionadas en `infra/grabaciones_canvas/`. Las grabaciones se regeneran antes del ensayo del 14 de septiembre y antes de la congelación del 5 de octubre. En paralelo se solicita por escrito un segundo curso de pruebas antes del 12 de septiembre; si llega, `ensayo` conmuta a `CANVAS_MODO=real` por configuración y **nada del diseño cambia**.

**Cuatro barreras independientes impiden que `ensayo` o local toquen a personas reales.** No es una sola bandera; fallar una no basta para causar daño.

| # | Barrera | Cómo actúa |
|---|---|---|
| 1 | **Doble de pruebas de Canvas** | `ProveedorCredencialCanvas` y `ClienteCanvas` se satisfacen con respuestas grabadas. **Las escrituras se aceptan, se registran y no salen a ninguna parte**: publicar una nota en `ensayo` devuelve una respuesta verosímil y queda en `bitacora` marcada como simulada |
| 2 | **Comprobación de arranque** | El proceso verifica que la `CANVAS_BASE_URL` de `ensayo` **no coincide** con la de `produccion`; **si coincide, el proceso no arranca**. Es una comprobación de seguridad, no una convención |
| 3 | **Organización y App distintas por entorno** | Un experimento local no puede crear un repositorio en la organización de producción aunque alguien se equivoque de curso, porque el `installation_id` es otro |
| 4 | **Correo de consola más lista blanca** | Fuera de `produccion` los correos se escriben en el log estructurado y no salen. Sobre esa base, `DESTINATARIOS_PERMITIDOS` filtra por correo y por `canvas_user_id`, y es la barrera que actúa si alguien conmutara a `CANVAS_MODO=real` |

**Interruptor de comunicaciones salientes, en dos niveles**, porque un interruptor global operable por cualquier profesor afectaría a cursos ajenos:

| Nivel | Mecanismo | Quién lo opera | Efecto |
|---|---|---|---|
| Por curso | `curso.comunicaciones_salientes` | Profesor con `curso.administrar` desde `/cursos/{id}/ajustes` | El despachador deja los mensajes retenidos y el curso muestra una banda con el recuento. **Nada se descarta nunca** |
| Global del despliegue | Variable de entorno `COMUNICACIONES_SALIENTES` (`activadas` \| `pausadas`) | **Sólo RI**, y exige redespliegue | Existe para el caso de incidente, no para el uso diario |

**Las alertas operativas del sistema no consultan el interruptor por curso**: una aplicación que no puede avisar de que está rota es peor que una aplicación caída.

**El guion de semilla de datos de demostración exige una confirmación explícita con el nombre del entorno escrito a mano** antes de ejecutar cualquier escritura.

### Criterios de aceptación de 14.4

1. Configurando en `ensayo` la misma `CANVAS_BASE_URL` que en `produccion`, el proceso **no arranca** y el log declara el motivo con texto explícito.
2. En `ensayo`, publicar una nota deja una fila en `bitacora` marcada como simulada y **ninguna** llamada saliente en el registro de coste de Canvas.
3. En `ensayo`, un intento de envío de correo a una dirección que no está en `DESTINATARIOS_PERMITIDOS` queda registrado y no se envía.
4. Existen dos organizaciones de GitHub y dos GitHub App, con `installation_id` distintos, y el `installation_id` de `ensayo` no aparece en la configuración de `produccion`.
5. Cada desarrollador ejecuta el conjunto de pruebas contra su propia base local; no existe ninguna cadena de conexión de desarrollo compartida en la bóveda.
6. Activado el interruptor por curso, el recuento de mensajes retenidos crece y ningún mensaje pasa a estado terminal de descarte.

---

## 14.5 Artefacto de construcción y arranque

### 14.5.1 Un solo Dockerfile, dos comandos

El backend se despliega con **Dockerfile propio, y el mismo artefacto corre en local, en `ensayo` y en `produccion`**. El fichero es **multietapa**, con la imagen base **fijada por digest** y no por etiqueta móvil:

| Etapa | Contenido |
|---|---|
| `constructor` | Imagen base `python:3.12-slim@sha256:<digest>`; instalación de dependencias con el gestor fijado y modo `frozen`, que **falla** si el fichero de bloqueo y el manifiesto divergen |
| `ejecucion` | Misma imagen base por digest; copia del entorno virtual; usuario no root `app`; etiqueta `org.opencontainers.image.revision` con el SHA de git. **Sin `HEALTHCHECK` propio**: la comprobación de salud la hace la plataforma contra `/salud` |

Un único Dockerfile y **dos comandos de arranque**, declarados en `infra/render.yaml`:

| Servicio Render | Comando de arranque |
|---|---|
| `api` (web) | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --timeout-graceful-shutdown 25` |
| `trabajador` (worker) | `python -m app.trabajos.ejecutor` |

**[DECISIÓN NUEVA]** Las fuentes citan dos nombres distintos para el punto de entrada del trabajador (`app.trabajos.trabajador` y `app.trabajos.ejecutor`) y dos para el de la aplicación web (`app.api:app` y `app.main:app`). Esta especificación fija **`app.trabajos.ejecutor`** y **`app.main:app`**, que son los que figuran en la decisión que declara la tabla de servicios de Render, y prohíbe cualquier otro nombre. Un nombre distinto en el fichero de despliegue y en el código es un despliegue que arranca en local y falla en la plataforma.

El frontend se despliega con la integración de Git de Vercel, con raíz `frontend/`: no hay Dockerfile posible ni hace falta, porque el artefacto es el resultado de la construcción de Vite con su fichero de bloqueo fijado.

### 14.5.2 Fijación de versiones

**Ninguna instalación resuelve versiones en el momento de construir**, ni en Render ni en Vercel.

| Qué | Cómo se fija | Dónde |
|---|---|---|
| Python | `python:3.12-slim@sha256:<digest>`, digest exacto | `Dockerfile` |
| Dependencias del backend | Fichero de bloqueo versionado; instalación en modo `frozen`, que **falla** si diverge del manifiesto | Repositorio y CI |
| Node del frontend | `engines.node = "22.x"`, `.nvmrc` y versión fijada en el proyecto de Vercel | Repositorio y Vercel |
| Dependencias del frontend | `package-lock.json` versionado; **`npm ci`**, nunca `npm install` | Repositorio y Vercel |
| Imagen final | Etiquetada con el SHA de git y expuesta en `GET /salud` como `version` | Render |
| Versión de la API de GitHub | Constante única `GITHUB_API_VERSION = 2026-03-10`, enviada como cabecera `X-GitHub-Api-Version` en **cada** petición | Código |

Se conserva copia del `Dockerfile` con su digest en la entrega. Si el registro retirase ese digest, fijar el nuevo entra por el procedimiento de corrección urgente de 14.10.5, con aviso a los revisores.

### 14.5.3 Presupuestos de despliegue

Cada cifra se mide y se registra con fecha en `.workflow/mediciones/` el **12 de septiembre**; ninguna es una estimación de papel.

| Fase | Presupuesto declarado |
|---|---|
| Construcción de la imagen con caché de capas | ≤ **6 minutos** |
| Arranque del web hasta que `GET /salud` responde `200` | ≤ **30 segundos** |
| Arranque del trabajador: cerrojo, migraciones y primer tick | ≤ **60 segundos** |
| Reversión a la imagen anterior | ≤ **3 minutos** |

### Criterios de aceptación de 14.5

1. `docker build` sobre el árbol del repositorio produce una imagen cuyo `org.opencontainers.image.revision` coincide con el SHA de git del *commit* construido.
2. Modificando el manifiesto de dependencias sin regenerar el fichero de bloqueo, la construcción **falla**, y falla también en CI.
3. `GET /salud` en producción devuelve un `version` idéntico al SHA del último *commit* integrado en `main`.
4. Los cuatro presupuestos de 14.5.3 tienen medición fechada del 12 de septiembre en `.workflow/mediciones/`, con el tiempo real observado.
5. `infra/render.yaml` declara los dos servicios con los comandos de arranque literales de 14.5.1, y no existe ningún tercer comando de arranque en el repositorio.
6. Un redespliegue sin cambios ejecutado el 13 de octubre devuelve el mismo `version` en `GET /salud` y la aplicación sigue en pie.

---

## 14.6 Configuración y secretos

### 14.6.1 Reglas de fondo

1. **Toda la configuración viaja por variables de entorno.** Ninguna URL, ningún origen y ningún identificador de proveedor está cableado en el código.
2. **Ningún secreto entra al repositorio, ni siquiera cifrado.** El repositorio es **público** desde el primer día, porque §3.2 exige entregar el código por GitHub y porque en plan gratuito la protección de ramas sólo está disponible en repositorios públicos.
3. **`.env.example` lista todas las claves y ningún valor.**
4. **La carga de configuración se valida al arrancar** y el proceso **falla el arranque** si falta un secreto obligatorio, en lugar de fallar en la primera llamada.
5. **Ninguna ruta de la API devuelve jamás un secreto**, y las columnas que los contienen están excluidas de todo esquema de salida.
6. **Un filtro central de logs redacta** la cabecera `Authorization`, el token cifrado, cualquier clave de correo, la clave privada de la GitHub App y la cadena de conexión; no se confía en la disciplina de quien escribe cada línea de log.

### 14.6.2 Inventario cerrado de secretos operativos

El inventario es **cerrado**: un secreto vivo fuera de él no se rota, no se custodia y no se retira. Es la lista contra la que se ensaya la rotación antes del 6 de octubre, contra la que se rota el 7 de octubre, y contra la que la puerta de secretos comprueba que nada vive en el árbol ni en el historial (**A-176**, **RG-138**, **RG-202**).

| # | Secreto | Quién lo usa | Custodia y retirada |
|---|---|---|---|
| 1 | `DATABASE_URL` | Backend | Bóveda compartida; rotación en `docs/operacion.md` |
| 2 | `APP_ENCRYPTION_KEYS` | Cifrado del token de Canvas | Bóveda compartida; llavero versionado |
| 3 | `APP_ENCRYPTION_KEY_ACTIVA` | Cifrado del token de Canvas | Bóveda compartida |
| 4 | `GOOGLE_CLIENT_ID` | OpenID Connect | Bóveda compartida |
| 5 | `GOOGLE_CLIENT_SECRET` | OpenID Connect | Bóveda compartida |
| 6 | `GITHUB_APP_ID` | Backend y `.github/workflows/actividad_demo.yml` | Bóveda compartida y *secrets* del repositorio |
| 7 | `GITHUB_APP_PRIVATE_KEY` (PEM en base64) | Los mismos | Bóveda compartida y *secrets* del repositorio |
| 8 | `GITHUB_WEBHOOK_SECRET` | Receptor de webhooks | Bóveda compartida |
| 9 | `GITHUB_WEBHOOK_SECRET_ANTERIOR` | Receptor, **sólo durante la ventana de rotación** | Se retira al cerrar la ventana |
| 10 | `EMAIL_PROVIDER_API_KEY` | Adaptador de correo | Bóveda compartida |
| 11 | `SIGNING_KEY` | `state` de OIDC y de instalación, tokens de baja y de traza, firma del latido | Bóveda compartida |
| 12 | `SIGNING_KEY_ANTERIOR` | Verificación, **sólo durante la ventana de 7 días** | Se retira al cerrar la ventana |
| 13 | `GITHUB_ENSAYO_APP_ID` | Guiones de medición de `infra/` | Bóveda compartida; **se retira al cerrar la medición de permisos** |
| 14 | `GITHUB_ENSAYO_APP_PRIVATE_KEY` | Los mismos | Bóveda compartida; **se retira al cerrar la medición de permisos** |
| 15 | `CANVAS_TOKEN_DEMO` | Guion de semilla de demostración | Token del profesor titular del curso de demostración; **se retira el 1 de noviembre** |

**Las dos cuentas de correo compartidas de evaluación entran en el mismo inventario** como credenciales de acceso, con custodio nombrado y fecha de retirada.

**Ninguno vive en la base de datos ni en el repositorio.** El **token de Canvas es el único secreto que se persiste**, cifrado; **no se persiste ningún token de GitHub**. **No existe ninguna cuenta de máquina y no existe ningún token de acceso personal** en ningún artefacto del proyecto: los cuatro artefactos de `infra/` y el *workflow* de demostración se autentican con **token de instalación de una GitHub App, emitido en caliente a partir de la clave privada**, exactamente igual que la aplicación, y ninguno lo persiste.

### 14.6.3 Configuración no secreta

Estas variables gobiernan el comportamiento del despliegue y **no** son secretos, pero su ausencia también falla el arranque.

| Variable | Valores | Efecto |
|---|---|---|
| `ENTORNO` | `produccion` \| `ensayo` \| `local` | Etiqueta de todo log; gobierna la banda de entorno en la interfaz |
| `PERFIL_ALCANCE` | `parcial` \| `completo` | Gobierna el catálogo cerrado de banderas de alcance: qué rutas se registran y qué trabajos se encolan. **No es estado del dominio y no vive en base de datos** |
| `CANVAS_MODO` | `doble` \| `real` | Selecciona la implementación de `ClienteCanvas` |
| `CANVAS_BASE_URL` | URL | Instancia de Canvas del entorno; se contrasta al arrancar contra la de producción |
| `COMUNICACIONES_SALIENTES` | `activadas` \| `pausadas` | Interruptor global del despliegue |
| `DESTINATARIOS_PERMITIDOS` | Lista | Lista blanca de destinatarios fuera de producción |
| `EMAIL_FROM`, `EMAIL_FROM_NOMBRE`, `EMAIL_REPLY_TO` | Cadenas | Remitente visible del correo |
| `EMAIL_DOMINIO_VERIFICADO` | Dominio | Contrastado contra `EMAIL_FROM` al arrancar; una discrepancia se declara en `GET /estado` |
| `VITE_API_BASE_URL` | URL | URL del backend que consume el frontend, distinta por entorno |
| `APP_VERSION` | SHA de git | Se inyecta en la construcción de la imagen y se devuelve en `GET /salud` |

**[DECISIÓN NUEVA]** `ENTORNO` y `APP_VERSION` no figuraban con nombre en ninguna fuente, aunque las tres decisiones que exigen etiquetar cada línea de log con el entorno y la versión, y devolver `version` en `GET /salud`, las presuponen. Se fijan aquí con esos nombres, se añaden a `.env.example` y se declaran obligatorias en la validación de arranque.

### 14.6.4 Cifrado del token de Canvas y llavero de claves

El token de acceso de Canvas se cifra con **AES-256-GCM**, con *nonce* aleatorio por fila y el `curso_id` como *additional authenticated data*, de modo que una fila cifrada **no puede reutilizarse en otro curso**. **Nunca se guarda en claro.**

**La clave no es una: es un llavero versionado** (**RG-138**, **A-191**).

| Elemento | Contenido |
|---|---|
| `APP_ENCRYPTION_KEYS` | Mapa de versión a clave de 32 bytes en base64 |
| `APP_ENCRYPTION_KEY_ACTIVA` | La versión con la que se **cifra** |
| `credencial_canvas.version_clave` (`smallint NOT NULL DEFAULT 1`) | La versión con la que se **descifra** esa fila |

**El arranque falla** si `APP_ENCRYPTION_KEY_ACTIVA` no está en `APP_ENCRYPTION_KEYS`. **Las variables `APP_ENCRYPTION_KEY` y `APP_ENCRYPTION_KEY_ANTERIOR` no existen**, y no existe ningún comando de rotación de clave maestra única.

**Rotación en línea y reanudable:** se añade la clave nueva, se cambia la versión activa, y el **recifrado perezoso** reescribe cada fila la próxima vez que la sonda de credenciales la valida —cada 15 minutos, de modo que un ciclo migra todas—. La clave antigua se retira cuando no queda ninguna fila con esa versión, comprobable con una consulta, y `/operacion` muestra cuántas filas faltan durante la rotación.

**Qué ocurre si se pierde el llavero:** las filas de `credencial_canvas` quedan indescifrables y el sistema **degrada de forma controlada**. El descifrado fallido se trata como credencial inválida: la credencial pasa a `INVALIDA`, el curso pasa a `CANVAS_DESVINCULADO`, se abre la incidencia `CANVAS_CREDENCIAL_INVALIDA`, **las lecturas de Canvas se detienen y las escrituras se encolan en `ESPERANDO_CREDENCIAL` sin descartarse**, y **lo que no depende de Canvas no se detiene**: aprovisionamiento, ingesta de actividad, tableros, línea de tiempo y captura de versiones. Todo el curso muestra una banda roja persistente y se avisa por correo a todos sus profesores; cualquier profesor puede entonces pegar su propia credencial nueva de forma guiada.

**La clave privada de la GitHub App se inyecta en base64**, no como variable multilínea: una variable multilínea se corrompe con facilidad al copiarla entre consolas y produce fallos de firma difíciles de diagnosticar. Se decodifica al arrancar y **nunca se escribe en disco**.

### 14.6.5 Acceso, detección y rotación

| Ámbito | Quién accede | Cómo |
|---|---|---|
| `produccion` | **RI y su segundo, y nadie más** | Consolas de Render, Vercel, Supabase y Google Cloud, todas con verificación en dos pasos |
| `ensayo` | Todo el equipo | Bóveda compartida |
| Local | Cada integrante, los suyos | Bóveda compartida y `.env` local ignorado por Git |

El gestor de contraseñas es una **bóveda compartida en plan gratuito**, con una organización cuyos dos miembros son RI y su segundo para los secretos de producción, y una colección aparte, accesible a todo el equipo, para los de `ensayo` y local. **El resto del equipo no necesita ningún secreto de producción para trabajar**, y esa es la verificación de que el reparto es correcto.

**Detección automática, en dos capas:**

1. **Pre-commit local** con el detector de secretos, instalado por `infra/instalar_hooks.sh`, que impide el *commit* antes de que exista.
2. **Puerta de construcción obligatoria**: el mismo detector **sobre árbol e historial del push**, con **cualquier hallazgo** como condición de fallo. `main` está protegida y la puerta no se puede saltar. Un falso positivo se resuelve con una regla de exclusión revisada en *pull request*, **nunca desactivando la puerta**.

**Rotación:**

| Momento | Alcance | Procedimiento |
|---|---|---|
| **Ensayo, antes del 6 de octubre** | Las quince entradas | Se ejecuta el procedimiento escrito de cada una, incluidos los dos casos difíciles: el secreto del webhook con su ventana de doble validación, y el llavero de cifrado con su versión por fila |
| **Programada, el 7 de octubre** | Las quince entradas | Después de la entrega del código y de la actividad de validación, cuando la superficie de exposición es máxima y la aplicación debe seguir en pie hasta el 31 de octubre |
| **Inmediata ante hallazgo** | El secreto comprometido | **El orden no es negociable**: (1) **rotar**, porque un secreto publicado se considera comprometido en el instante en que se publica y reescribir la historia no lo des-filtra; (2) reescribir el historial y forzar el `push`; (3) registrar el incidente en `docs/operacion.md` con fecha, alcance y acciones |

Un fichero `.env` cifrado y versionado queda **descartado**: en un repositorio público deja material cifrado al alcance de cualquiera para siempre. Un gestor de secretos externo queda **descartado**: un proveedor más que operar y que puede caer, para un equipo de cuatro personas y quince secretos, cuando las variables de entorno de las plataformas ya son el mecanismo nativo.

### Criterios de aceptación de 14.6

1. `.env.example` contiene exactamente las quince claves de secretos de 14.6.2 y las variables no secretas de 14.6.3, **sin un solo valor**.
2. Arrancando el backend sin `APP_ENCRYPTION_KEY_ACTIVA`, o con una versión activa ausente del llavero, el proceso **no arranca** y el error nombra la variable.
3. La puerta de secretos corre sobre árbol e historial en cada `push` y está en verde; un *commit* de prueba con una clave privada simulada la pone en rojo y no puede integrarse.
4. Ninguna respuesta de la API contiene el token de Canvas: una revisión de los esquemas de salida y una prueba automatizada lo confirman.
5. Ejecutada una rotación completa del llavero en `ensayo`, todas las filas de `credencial_canvas` quedan con la versión nueva en un ciclo de sonda, `/operacion` muestra el contador llegando a cero y ninguna credencial pasa a `INVALIDA`.
6. El ensayo de rotación de los quince secretos queda registrado con fecha antes del 6 de octubre en `docs/operacion.md`.
7. Emitiendo deliberadamente una línea de log con una cabecera `Authorization` y con el nombre de un estudiante, la prueba automatizada de redacción falla si alguno aparece en la salida.

---

## 14.7 Trabajos en segundo plano

### 14.7.1 La cola y el planificador viven en PostgreSQL

**No se usa Redis, ni Celery, ni ningún intermediario externo** (**A-112**). La cola **es la tabla `trabajo`**, consumida con `SELECT … FOR UPDATE SKIP LOCKED`. El planificador **es la tabla `trabajo_periodico`**, con `proxima_ejecucion`, recorrida por un **tick del trabajador cada 30 segundos** que encola lo vencido.

Cuatro razones, en orden:

1. **Permite encolar el trabajo y escribir el cambio de dominio que lo justifica en la misma transacción.** Eso es lo que da idempotencia real; con un intermediario externo esas dos escrituras no son atómicas y aparece el hueco clásico: el repositorio queda `CREANDO` y el trabajo nunca se encoló, o al revés.
2. Elimina un servicio, un coste y un modo de fallo en un despliegue que debe seguir en pie hasta el 31 de octubre.
3. Hace la cola **inspeccionable desde la propia interfaz**, lo que es útil en la demostración y en la defensa del 7 de octubre.
4. Es defendible en una revisión de código sin apelar a la magia de un intermediario.

Contrapartida asumida por escrito: **la cola no sobrevive a la pérdida de la base**. Es aceptable porque la base ya es el punto único de verdad y está respaldada a diario.

Columnas de la tabla `trabajo`: `id`, `tipo`, `clave_idempotencia`, `curso_id`, `payload`, `estado`, `intentos`, `max_intentos`, `proximo_intento_en`, `tomado_por`, `tomado_en`, `ultimo_error`, `coste_api`, `creado_en`, `terminado_en`, `motivo_cancelacion`. Columnas de `trabajo_periodico`: `id`, `tipo`, `curso_id`, `cadencia_segundos`, `proxima_ejecucion`, `ultima_ejecucion`, `activo`, con unicidad `(tipo, curso_id)`.

Estados de `trabajo`: `PENDIENTE → EN_CURSO → {OK | REINTENTAR | BLOQUEADO | ESPERANDO_CREDENCIAL | ESPERANDO_LIMITE | REQUIERE_ATENCION | CANCELADO}`. **Un trabajo agotado no desaparece**: queda `REQUIERE_ATENCION` con su último error literal, visible y reintentable a mano desde `/operacion`.

El patrón de bandeja de salida vive en una tabla aparte, `mensaje_saliente`, despachada por el trabajo `despachar_outbox` cada 30 segundos. **Ninguna comunicación se envía de forma síncrona desde una vista.**

### 14.7.2 Las cinco garantías que comparte todo trabajo

Ninguna es opcional (**A-115**).

| # | Garantía | Cómo se implementa |
|---|---|---|
| 1 | **Clave de idempotencia única** | **Índice único parcial en base de datos** sobre `trabajo.clave_idempotencia` en los estados no terminales, no una comprobación en memoria. Encolar dos veces el mismo trabajo lógico es una operación sin efecto |
| 2 | **Transacción con el dominio** | Encolar el trabajo y escribir el cambio de estado que lo justifica ocurren en la **misma** transacción |
| 3 | **Intención antes de llamada, y lectura antes de todo efecto externo** | Se persiste la intención (`repositorio.estado = CREANDO`, `mensaje_saliente.estado = PENDIENTE`) y **se lee para comprobar si el efecto ya está producido** |
| 4 | **Reintento con retroceso exponencial, *jitter* y tope** | Respetando siempre `retry-after`. El tope es el de cada trabajo, no un número global |
| 5 | **Serialización por curso con dos espacios de cerrojo** | Ver 14.7.3 |

La garantía 3, en detalle, porque es la que hace inocuo un reinicio a mitad de una operación externa:

| Antes de… | Se lee… |
|---|---|
| Crear un repositorio | El repositorio por nombre |
| Añadir un colaborador | El colaborador y las invitaciones pendientes |
| Crear una etiqueta | La referencia de la etiqueta |
| Publicar una nota | La *submission* actual, comparando puntaje y fecha de calificación |
| Enviar correo, mensaje, anuncio o comentario | `mensaje_saliente.clave_idempotencia` |

**El peor caso de un reinicio es una lectura de más**, nunca un repositorio duplicado ni una invitación repetida.

### 14.7.3 Dos espacios de cerrojo por curso, uno por proveedor

**Sustituye a cualquier granularidad anterior** (**A-217**, **RG-062**):

| Espacio | Qué protege | Por qué |
|---|---|---|
| `pg_advisory_lock(1, curso_id)` | **Todo el tráfico con Canvas** del curso | Contra Canvas rige **una sola petición simultánea por curso**: un cliente que no hace más de una petición simultánea es improbable que sea limitado, y las peticiones paralelas sufren penalización previa |
| `pg_advisory_lock(2, curso_id)` | **Todo el tráfico con GitHub** del curso | GitHub sí admite concurrencia; el techo lo pone el presupuesto medido (concurrencia 4), no el cerrojo |
| `pg_advisory_lock('global', tipo)` | Trabajos de alcance global | Un solo ejecutor por instante |

**Tres reglas, y las tres son verificables:**

1. **Ningún trabajo retiene un cerrojo mientras espera al otro carril.** El trabajo de checklist toma el cerrojo 1 sólo alrededor de sus llamadas a Canvas y el 2 sólo alrededor de las suyas a GitHub, y **los libera entre ítems**.
2. **Un trabajo que necesite los dos los toma siempre en orden 1 y luego 2**, nunca al revés.
3. **`infra/cerrojos.py` expone `cerrojo_canvas(curso_id)` y `cerrojo_github(curso_id)` como únicos puntos de toma**, y una prueba de arquitectura **falla la construcción** si aparece una toma en orden inverso o una toma anidada de dos cerrojos del mismo espacio.

Con un solo cerrojo por curso, los 180 segundos del checklist de vinculación pararían el aprovisionamiento de cientos de repositorios y la reconciliación de actividad **delante del evaluador**. Por eso son dos.

**Un cerrojo consultivo se libera solo** en cuanto la transacción termina o la conexión cae: **no existe el escenario de sujeto bloqueado para siempre** que un cerrojo con tiempo de vida en un almacén externo sí tiene.

### 14.7.4 Catálogo cerrado de trabajos

**Son 31 trabajos, y ninguno más.** Añadir uno es una decisión que se registra en la carta de arquitectura. El planificador declara para cada uno cadencia, alcance, espacio de cerrojo, clave de idempotencia, reintentos, bandera de alcance y fecha de entrada en servicio (**A-114**, **A-218**, **RG-194**, **RG-153**).

| # | Trabajo | Cadencia | Alcance | Cerrojo | Clave de idempotencia | Reintentos | Entra en servicio |
|---|---|---|---|---|---|---|---|
| 1 | `tick_planificador` | 30 s | Global | Global | Ventana | — | 16-sep |
| 2 | `sonda_credencial_canvas` | 15 min | Curso | 1 | Lectura pura | 3 | 16-sep |
| 3 | `sync_roster` | 10 min | Curso | 1 | Upsert por `canvas_enrollment_id` | 4 | 16-sep |
| 4 | `sync_grupos` | 10 min | Curso | 1 | Upsert por `canvas_group_id` y `(grupo, estudiante)` | 4 | 16-sep |
| 5 | `sync_tareas_y_fechas` | 5 min; **1 min en las 2 h previas a un cierre** | Curso | 1 | Comparación de `huella_fechas` | 4 | 16-sep |
| 6 | `recolector_mapeos` | 3 min con la tarea de registro abierta; 15 min si no; **volcado completo cada hora** | Curso | 1 | `(canvas_assignment_id, canvas_user_id, submitted_at)` | 4 | 16-sep |
| 7 | `materializar_sujetos` | Tras cada `sync_*` y barrido cada 5 min | Curso | 1 | `(tarea, conjunto_hash)` | 3 | 16-sep |
| 8 | `ejecutar_checklist_vinculacion` | Bajo demanda, sin cadencia | Curso | **1 y 2, por tramos y nunca a la vez** | `(curso_id, ejecucion_id)` | 1 | 16-sep |
| 9 | `revalidar_mapeos` | Diario 04:00 | Curso | 2 | `github_user_id` | 2 | 16-sep |
| 10 | `aprovisionar_repositorios` | Evento de dominio y barrido cada 2 min | Curso | 2 | `repo:<tarea>:<sujeto>` | 8 en ~2 h | 16-sep |
| 11 | `reconciliar_accesos` | 15 min | Curso | 2 | `(repositorio, estudiante)` | 4 | 16-sep |
| 12 | `sincronizar_acceso_docente` | Al cambiar el equipo del curso y barrido cada 1 h | Curso | 2 | `(repositorio, membresia)` | 4 | 16-sep |
| 13 | `revocar_acceso_docente` | Al retirar una membresía | Curso | 2 | `(membresia, repositorio)` | 4 | 16-sep |
| 14 | `revocar_acceso_estudiante` | Al aprobarse la revocación | Repositorio | 2 | `revocacion:<acceso_repositorio_id>` | 4 | 16-sep |
| 15 | `procesar_webhooks` | Continuo | Global | Por `repositorio_id` | `delivery_id` | 5 | 16-sep, con procesamiento acotado |
| 16 | `verificar_instalacion_github` | 1 h | Curso | 2 | `installation_id` | 2 | 16-sep |
| 17 | `despachar_outbox` | 30 s | Global | 1 en su parte de Canvas | `mensaje_saliente.clave_idempotencia` | 6, luego `REQUIERE_ATENCION` | 16-sep |
| 18 | `limpieza_verificacion` | Diaria | Curso | 1 | Prefijo de la prueba de escritura | 1 | 16-sep |
| 19 | `respaldo_base_datos` | Diario 05:00 | Global | Global | Fecha | 2 | 16-sep |
| 20 | `purga_retencion` | Diario 03:00 | Global | Global | Fecha | 1 | 16-sep |
| 21 | `vigilancia` | 5 min | Global | Global | — | — | 16-sep |
| 22 | `resolver_sha` | 1 min | Global | 2 | `version:<entrega>:<sujeto>:<corte_epoch>` | 8 en ~2 h | Bloque 1, 23-sep |
| 23 | `crear_etiqueta` | Encolado por `resolver_sha` | Sujeto | 2 | `tag:<entrega>:<sujeto>:<intento>` | 8 en ~2 h | Bloque 1, 23-sep |
| 24 | `precierre_actividad` | **Repartido a lo largo de los 15 min previos** a cada fecha efectiva | **Repositorio** | 2 | `(repositorio, corte_epoch)` | 2 | Bloque 1, 23-sep |
| 25 | `reconciliar_actividad` | 15 min | Repositorio activo | 2 | Upsert `(repositorio, sha)`; ETag | 4 | Bloque 2, 30-sep |
| 26 | `barrido_completo_actividad` | Diario 03:30 | Repositorio | 2 | Cursor `ultimo_head_sha` | 2 | Bloque 2, 30-sep |
| 27 | `agregar_metricas` | 10 min sobre los últimos 2 días y pasada nocturna completa | Curso | 2 | Recomputa, no incrementa | 2 | Bloque 2, 30-sep |
| 28 | `comunicaciones_programadas` | 5 min | Tarea | 1 | `(tarea, evento, sujeto, entrega, estudiante)` | 3 | Bloque 3, 3-oct |
| 29 | `informe_diario` | **07:00 en la zona horaria del curso** | Curso | 1 | `(curso, fecha)` | 3 | Bloque 3, 3-oct |
| 30 | `reconciliar_notas_canvas` | Inmediata al entrar la entrega en ventana de corrección; **cada 30 min** dentro de ella; **una vez al día** fuera; nunca en tarea archivada | Curso | 1 | `(entrega, ventana)` | 4 | Bloque 3, 3-oct |
| 31 | `archivar_repositorios` | Acción del profesor | Tarea | 2 | `(tarea, repositorio)` | 3 | Bloque 2, 30-sep |

**[DECISIÓN NUEVA]** La fila 7, `materializar_sujetos`, toma el **cerrojo 1**. La tabla de espacios de cerrojo no lo enumera en ninguno de los dos carriles, mientras que la garantía que sustituye lo clasificaba entre los trabajos del carril de Canvas y el catálogo le asignaba el cerrojo por curso. Situarlo en el carril de Canvas es la única lectura que evita que corra en paralelo con los `sync_*` del mismo curso, que es precisamente lo que la regla de una sola petición simultánea por curso existe para impedir.

**Notas de lectura del catálogo:**

- **La partición de la captura de versiones suma uno al catálogo, no dos**: donde el calendario y las banderas dicen «captura de versiones» se leen `resolver_sha` y `crear_etiqueta`, con la misma bandera, la misma fecha y las dos claves.
- **`precierre_actividad` es por repositorio y se reparte en 15 minutos, no en 2.** Cuando una entrega cierra a la misma hora para todo el curso, la alternativa serían 200 reconciliaciones en 120 segundos, por encima del presupuesto propio de llamadas. Repartidas en 900 segundos son una cada 4,5 segundos. **La captura sigue disparándose a la hora exacta**: lo que se adelanta es la puesta al día del espejo, no el corte.
- **Un trabajo cuya bandera de alcance no está retirada no se encola y no aparece como vencido**, para que la alerta «trabajo periódico sin ejecutarse durante tres ciclos» no se dispare por diseño.
- **No existen** `verificar_publicacion_notas` ni `verificar_etiquetas_entrega`: la verificación de etiquetas vive en el barrido nocturno.

### 14.7.5 Clasificación de errores

La familia decide el comportamiento **y decide lo que ve el docente** (**A-116**).

| Familia | Ejemplos | Comportamiento | Qué ve el docente |
|---|---|---|---|
| **TRANSITORIO** | `429`, `5xx`, tiempo de espera agotado, `403` de límite secundario, `404` durante la ventana de creación | Retroceso exponencial con *jitter*, hasta el tope del trabajo | «Reintentando, próximo intento a las HH:MM» |
| **BLOQUEANTE** | `403` por política de la organización, permisos pendientes de aprobación, cupo de invitaciones agotado, credencial de Canvas inválida | Estado `BLOQUEADO` o `ESPERANDO_*`; **no se reintenta en bucle**; se reevalúa cada 30 minutos o cuando cambia la condición | «Esperando a GitHub por límite de uso. Reintento automático a las HH:MM» / «Falta aprobar permisos» |
| **PERMANENTE** | Cuenta de GitHub inexistente, login que es una organización, tipo de calificación no admitido, período de calificación cerrado, `422` de validación | **Cero reintentos**; estado terminal con motivo y acción sugerida; se guarda el mensaje literal del proveedor | «Requiere tu acción: …», con el texto literal debajo |

**Un límite de una API externa jamás se pinta como error del equipo.** Todo `403` cuyo cuerpo no se reconozca se clasifica como **BLOQUEANTE**, con el mensaje literal del proveedor a la vista, nunca traducido a un diagnóstico inventado.

### 14.7.6 Recuperación de trabajos huérfanos

Dos mecanismos, para dos causas distintas:

| Causa | Mecanismo | Umbral |
|---|---|---|
| Apagado ordenado (reinicio o despliegue) | El ejecutor devuelve la fila a `PENDIENTE` con `tomado_por` y `tomado_en` a nulo y `proximo_intento_en = now()`, y **no la cuenta como intento fallido**: no fue un fallo, fue un reinicio | 25 s de gracia |
| Muerte sin señal (falta de memoria, caída del nodo) | El trabajo `vigilancia`, cada 5 minutos, devuelve a `PENDIENTE` toda fila en `EN_CURSO` cuyo `tomado_en` tenga **más de 10 minutos** y cuya conexión ya no sostenga el cerrojo, comprobado contra `pg_locks` | 10 min |

**Retomar es seguro precisamente por la garantía 3**: se lee antes de todo efecto externo.

### 14.7.7 Elección de ejecutor y vigilante externo

**Aunque el trabajador sea uno solo, un despliegue progresivo puede solapar dos instancias durante unos segundos.** Por eso el tick del planificador toma `pg_advisory_lock('global', 'tick_planificador')` antes de encolar nada: **un solo ejecutor por instante**. Y aunque dos ticks se solaparan, la clave de idempotencia única en base haría del segundo encolado una operación sin efecto. Son **dos defensas independientes**, no una. **No se usa fichero de proceso** —el sistema de ficheros es efímero— **ni variable de entorno que designe al líder** —no sobrevive a un reinicio ni distingue dos instancias de la misma configuración—.

**El token de instalación de GitHub se cachea en memoria del proceso, nunca en base y nunca en un almacén externo**, hasta cinco minutos antes de su expiración. Con dos procesos, cada uno mantiene su propia caché, lo que a lo sumo cuesta una llamada extra por proceso y hora. **La consecuencia es deliberada y defendible: un volcado de la base de datos no contiene ninguna credencial que permita escribir en GitHub.**

**Vigilante externo del planificador, que no es un *pinger*.** Un *workflow* programado de GitHub Actions llama **cada 10 minutos** a `POST /interno/latido`. Ese endpoint **no mantiene vivo nada** —los servicios están en plan de pago y no se suspenden— y **su efecto primario es una comprobación**:

1. Lee el máximo de `trabajo_periodico.ultima_ejecucion` y el retraso máximo de `proxima_ejecucion` vencida.
2. **Si el planificador está al día, responde `200` y no hace nada más.**
3. **Sólo si hay algún trabajo periódico vencido por más de tres cadencias**, abre la incidencia `PLANIFICADOR_DETENIDO`, dispara la alerta por correo con cargo a la reserva operativa, y **entonces** fuerza un ciclo de planificación como medida de recuperación.

Es deliberadamente externo al despliegue que vigila: un vigilante alojado en el mismo proceso que el planificador **se muere con él y no avisa de nada**. La puntualidad de los *cron* de GitHub Actions no está garantizada y **no hace falta que lo esté**: el planificador real es el tick de 30 segundos; esto sólo detecta que ha dejado de latir. Si el *workflow* dejara de correr, no se cae nada: se pierde la detección temprana.

**Autenticación del latido:** cabecera `X-Latido-Firma: v1={hex}` con HMAC-SHA256 sobre la cadena `{timestamp}.{nonce}`, calculado con `SIGNING_KEY` y comparado en **tiempo constante**. Se rechaza con `401` si falta la cabecera, si la firma no valida, si `timestamp` está fuera de una ventana de **±5 minutos** o si el `nonce` ya se consumió —el `nonce` se registra como `trabajo.clave_idempotencia` del tipo `latido`, cuyo índice único parcial hace la detección de repetición **estructural**—. **No se usa lista blanca de direcciones IP**: los ejecutores de GitHub Actions no tienen dirección estable y una lista blanca daría falsa sensación de control. El endpoint se monta **fuera del middleware de sesión y del de CSRF**.

Invocarlo dos veces seguidas o en paralelo no produce ningún efecto distinto de invocarlo una vez: es de lectura salvo en el caso de recuperación, y ese caso toma el cerrojo global.

### Criterios de aceptación de 14.7

1. Lanzando a la vez los cinco trabajos de Canvas del mismo curso, la prueba automatizada verifica que **se serializan** y que en ningún instante hay dos peticiones simultáneas a Canvas para ese curso.
2. Una prueba de arquitectura falla la construcción si aparece una toma de cerrojos en orden inverso o una toma anidada de dos cerrojos del mismo espacio.
3. Lanzando dos trabajadores contra la misma base, **sólo uno encola** en cada tick y **ningún trabajo se ejecuta dos veces**.
4. Encolando dos veces el mismo trabajo lógico, la segunda inserción es rechazada por el índice único parcial y no crea fila.
5. Matando el proceso trabajador sin señal a mitad de un trabajo, el trabajo vuelve a `PENDIENTE` en un máximo de 10 minutos por acción de `vigilancia`, y al reintentarse no duplica ningún efecto externo.
6. Reiniciando el trabajador a mitad de la creación de 20 repositorios, al terminar existen exactamente 20 repositorios, ninguna invitación duplicada y ningún mensaje repetido.
7. `POST /interno/latido` sin firma, con firma inválida, con marca de tiempo fuera de la ventana de ±5 minutos o con un `nonce` repetido devuelve `401` en los cuatro casos.
8. Deteniendo el trabajador durante más de tres cadencias del trabajo periódico más frecuente, se abre `PLANIFICADOR_DETENIDO` y llega el correo operativo.
9. `/operacion` lista los 31 trabajos con su última ejecución, y un trabajo cuya bandera de alcance no está retirada **no** aparece como vencido.

---

## 14.8 Migraciones de esquema

### 14.8.1 Una sola migración, anterior al 16 de septiembre

**Hay una sola migración de esquema en todo el proyecto y es anterior al 16 de septiembre** (**A-175**, **RG-144**, **RG-193**). La herramienta es Alembic sobre el ORM fijado.

Esa migración crea, de una vez:

| Contenido | Detalle |
|---|---|
| **Las 70 entidades del censo** | Incluidas las diez que ningún código leerá hasta la entrega final. Crear diez tablas vacías cuatro semanas antes no cuesta nada y **elimina la única migración que podía fallar delante del evaluador** |
| **Todas las columnas que la autorización y la seguridad necesitan** | Aunque el código que las lee llegue después: banderas de alta y de vía compartida en `membresia_curso`, los cuatro `CHECK` sobre permisos y rol, `usuario.cuenta_github_id` con índice único parcial, `usuario.consentimiento_github_en`, `usuario.generacion_enlaces`, `credencial_canvas.version_clave`, `bitacora.permiso_exigido`, `.ruta` y `.metodo`, `suscripcion_informe.origen_baja` y `.dada_de_baja_en`, la tabla `cubo_tasa` con clave primaria `(clave, ventana_inicio)`, y `verificacion_vinculacion.detalle jsonb` |
| **Todas las columnas de ingesta y de comunicación** | `commit.parent_shas`, `commit.en_rama_por_defecto`, `commit.recibido_en`, `cursor_sincronizacion.ultimo_backfill_en`, `curso.ingesta_actividad_desde` y `mensaje_saliente.reserva` |
| **Todos los valores de todos los catálogos cerrados** | Los 51 tipos de incidencia, los siete subtipos de error permanente, los enumerados de las siete máquinas de estado, los veinte motivos de estado de mensaje, los dieciséis motivos de cancelación de trabajo, los seis motivos de revocación de acceso, los cinco motivos de versión de entrega, los siete motivos de etiqueta, los cinco resultados de verificación de vinculación, los cinco estados de organización de GitHub y los diez motivos de no publicable |
| **Todos los índices únicos parciales** | Los que el patrón *append-only* exige sobre mapeos, identidades de Git, repositorios y versiones de entrega |

**Motivo, escrito para que nadie lo reabra:** ampliar un `CHECK` es un `ALTER`, y un `ALTER` en la ventana de la entrega final pone en rojo la puerta de migraciones **el mismo día de la defensa**. Sin esta regla, **la primera incidencia de un tipo nuevo abortaría la transacción que la abre**, en producción y delante del evaluador.

**Convención de nombres de restricciones fijada desde la primera migración**, en la metadata del ORM. Sin ella, la herramienta genera nombres distintos en cada entorno y las migraciones dejan de ser reproducibles.

`docs/operacion.md` declara **qué tablas nacen vacías y qué bloque las empieza a escribir**.

### 14.8.2 Política posterior al 16 de septiembre

| Ventana | Qué se permite | Qué se prohíbe |
|---|---|---|
| 17-sep → 5-oct | Añadir tabla, añadir columna *nullable* o con `DEFAULT`, añadir índice | `DROP TABLE`, `DROP COLUMN`, renombrar en sitio, estrechar un tipo, `ALTER … TYPE`, cambiar una clave, cambiar una unicidad |
| 6-oct → 31-oct | Nada, salvo corrección urgente documentada | La fase de *contract* queda **prohibida hasta el 31 de octubre**: una columna que sobre **se deja y se documenta** |
| Desde el 5-oct 20:00 | Ninguna migración, ni siquiera aditiva | Todo, salvo el procedimiento de corrección urgente de 14.10.5 |

La política es **expand–contract y sólo aditiva**: se añade columna, se rellena, se empieza a leer; **nunca se borra en la misma versión en que se deja de escribir**. Esa regla no es sólo higiene: es lo que hace que **la imagen anterior siga funcionando contra el esquema nuevo**, y por tanto lo que hace segura la reversión de 14.10.4.

### 14.8.3 Quién aplica las migraciones y qué ocurre si fallan

1. **Las aplica el trabajador al arrancar**, tomando antes un `pg_advisory_lock` dedicado, mediante `aplicar_migraciones()` en `backend/app/infraestructura/migraciones.py`, invocado **antes** de tomar ningún trabajo. **El servicio web nunca migra.** Con dos procesos desde la misma imagen, esto elimina la carrera de dos procesos migrando a la vez y hace que el orden de arranque no importe: el web arranca, responde `GET /salud`, y `GET /estado` declara el esquema como `pendiente` hasta que el trabajador termina.
2. **Cada revisión se ejecuta en una transacción.** Una revisión que falla **no deja esquema a medias**: deja la base en la revisión anterior y **el trabajador no arranca**, con el error literal en el log y en `GET /estado`. El fallo se convierte así en «no se despliega» en lugar de en «se despliega roto».
3. **La política ante una migración fallida es corrección hacia delante, nunca reversión de esquema.** La corrección es una revisión nueva que arregla la anterior, revisada por otra persona y desplegada por el camino normal.
4. **`alembic downgrade` no se ejecuta nunca contra `produccion`.** Existe en el código, se prueba en `ensayo`, y está prohibido por escrito en `docs/operacion.md`: un descenso que borra una columna destruye datos que la Ley 2 declara inmutables. La función de arranque **sólo expone `upgrade`**.
5. **Prueba de arranque obligatoria:** al iniciar, el proceso compara el esquema desplegado con el esperado y **falla si falta una columna o un valor de catálogo** de la lista de 14.8.1.
6. **`GET /estado` expone `esquema.revision_actual` y `esquema.revision_esperada`.** Si difieren, `/operacion` muestra banda ámbar «esquema en migración».

**Técnicas obligatorias para no bloquear tablas con datos:** `CREATE INDEX CONCURRENTLY` fuera de transacción, y `ALTER TABLE … ADD COLUMN` con `DEFAULT`, que en las versiones vigentes de PostgreSQL no reescribe la tabla. El volumen real es de decenas de miles de filas, no de millones.

### 14.8.4 Puertas de construcción relativas a migraciones

| Comprobación | Condición de fallo |
|---|---|
| Aplicación limpia | `alembic upgrade head` sobre base efímera falla |
| Divergencia | Existe una migración pendiente de generar entre los modelos y las migraciones |
| Contenido prohibido | Aparece un fichero de migración con fecha **posterior al 16 de septiembre** que contenga `DROP`, `ALTER … TYPE`, un cambio de clave o un cambio de unicidad |
| Esquema desplegado | El esquema desplegado no contiene alguna columna o algún valor de catálogo de la lista de 14.8.1 |
| Datos reales | **Toda revisión nueva se aplica también sobre una copia del esquema de producción**, restaurada desde el volcado cifrado más reciente sobre el proyecto de `ensayo` |

### Criterios de aceptación de 14.8

1. `alembic upgrade head` sobre una base vacía crea las 70 tablas, todos los `CHECK` completos y todos los índices únicos parciales, y termina sin error.
2. Añadiendo una columna al modelo sin generar su migración, la construcción **falla** por divergencia.
3. Creando un fichero de migración con fecha posterior al 16 de septiembre que contenga `DROP COLUMN`, la construcción **falla**.
4. Arrancando el servicio web contra una base sin migrar, `GET /salud` responde `200` y `GET /estado` declara el esquema como pendiente; el web **no** aplica ninguna migración.
5. Provocando el fallo de una revisión en `ensayo`, el trabajador **no arranca**, la base queda en la revisión anterior y el error literal aparece en `GET /estado`.
6. Una búsqueda en el código confirma que la función de arranque no expone `downgrade`, y `docs/operacion.md` recoge la prohibición por escrito.
7. Insertando una incidencia de cada uno de los 51 tipos del catálogo sobre el esquema desplegado, ninguna transacción aborta por violación de `CHECK`.

---

## 14.9 Integración continua: las puertas de construcción

### 14.9.1 Repositorio y protección de rama

**El código se entrega en un único repositorio público del equipo**, con `backend/`, `frontend/`, `infra/`, `docs/`, `.workflow/` y `.github/workflows/`. Es público por dos razones concretas: §3.2 exige entregar todo el código por GitHub, y en una organización de plan gratuito **la protección de ramas sólo está disponible en repositorios públicos**. Ser público obliga además a una higiene de secretos desde el primer día.

**`main` está protegida: no se empuja directo, se integra por *pull request* con todas las puertas en verde.**

La estructura interna del backend es fija y no negociable, porque de ella depende una puerta:

| Paquete | Contenido |
|---|---|
| `backend/app/dominio/` | Reglas de negocio puras: entidades, máquinas de estado, cálculo de fecha efectiva, materialización de sujetos, atribución de *commits*, ventanas de entrega, normalización de nombres. **No importa el cliente HTTP, ni el ORM, ni el framework web. Sin entrada ni salida** |
| `backend/app/adaptadores/` | `ClienteCanvas`, `ClienteGitHub`, `ProveedorCorreo`, repositorios del ORM. Todo lo que habla con el mundo |
| `backend/app/api/` | Rutas y esquemas de entrada y salida |
| `backend/app/trabajos/` | Los 31 trabajos del catálogo cerrado |
| `backend/app/infraestructura/` | Configuración, cifrado, logs, migraciones, cerrojos, banderas de alcance |

### 14.9.2 Diez puertas de herramienta

Corren en **cada `push` y cada *pull request***.

| # | Puerta | Herramienta | Condición de fallo |
|---|---|---|---|
| 1 | Formato y lint del backend | `ruff format --check`, `ruff check` | Cualquier hallazgo |
| 2 | Tipos del backend | `mypy --strict` sobre `backend/app` | Cualquier error |
| 3 | Pruebas del backend | `pytest` con cobertura | Fallo, o cobertura de línea **< 70 % medida con `--cov=backend/app/dominio`** |
| 4 | **Pureza del dominio** | Prueba de arquitectura sobre los *imports* | Cualquier módulo de `backend/app/dominio/` que importe el cliente HTTP, el ORM o el framework web |
| 5 | Migraciones | `alembic upgrade head` sobre base efímera y comprobación de divergencia | Divergencia entre modelos y migraciones |
| 6 | Lint y tipos del frontend | `eslint`, `tsc --noEmit` | Cualquier error |
| 7 | Construcción del frontend | `vite build` | Fallo |
| 8 | Construcción de la imagen | `docker build` | Fallo |
| 9 | Secretos | Detector de secretos sobre **árbol e historial** del push | Cualquier hallazgo |
| 10 | Dependencias | Auditoría de dependencias del backend y del frontend, excluyendo las de desarrollo | Vulnerabilidad alta o crítica |

### 14.9.3 Ocho puertas de contrato, con orden de evaluación

Viven en un único *workflow* `.github/workflows/puertas.yml`, con **un trabajo por fila** y **en este orden** (**A-174**, **RG-161**):

| # | Puerta | Falla la construcción si… | Fuente de datos única |
|---|---|---|---|
| 1 | **Contrato de autorización** | Una ruta bajo `/api/cursos/{curso_id}` se registra sin dependencia de permiso | El enrutador real del framework |
| 2 | **Rol fuera de la dependencia** | Aparece una lectura del rol de la membresía con efecto de autorización fuera de la dependencia `requiere(...)`, o una ruta registrada exige rol mínimo sin figurar en la constante de acciones sólo de profesor | La constante `ACCIONES_SOLO_PROFESOR` |
| 3 | **Superficie sin sesión** | Se registra una ruta sin dependencia de sesión que no figura en la lista cerrada de rutas sin sesión | La lista cerrada de rutas sin sesión |
| 4 | **Registro por perfil** | Bajo el perfil en curso aparece registrada una ruta declarada oculta en ese perfil, o falta una declarada registrada | La lista normativa de rutas por perfil |
| 5 | **Acotación del panel** | Una ruta de `/api/operacion/**`, o `/api/estado` en su forma completa, se registra sin la dependencia que acota por los cursos del solicitante | La regla de acotación del panel |
| 6 | **Alcanzabilidad** | La prueba de alcanzabilidad parametrizada no pasa en el modo correspondiente a la construcción | El enrutador real y la tabla de alcance como estructura de datos |
| 7 | **Migraciones** | Se cumple cualquiera de las condiciones de 14.8.4 | El esquema desplegado |
| 8 | **Banderas** | Queda en el código una bandera del catálogo de alcance sin usar, o el catálogo no está vacío después del **5 de octubre a las 12:00** | El catálogo de banderas |

**Tres reglas de convivencia, que no son consejos:**

1. **Las puertas 3 y 4 son complementarias y se evalúan en ese orden.** La 3 dice *qué está permitido que exista sin sesión*; la 4 dice *qué está permitido que exista hoy*. Una ruta puede figurar en la lista sin sesión y estar prohibida en el perfil en curso; el caso contrario —registrada en el perfil y ausente de la lista sin sesión— **es siempre un fallo**.
2. **Ningún rojo se resuelve registrando media pantalla ni relajando una comprobación de seguridad.** Si una puerta se pone en rojo por una decisión de alcance, la salida es **mover la bandera**, no bajar la puerta.
3. **Las ocho corren en los dos perfiles.** Las puertas 4 y 6 se parametrizan por `PERFIL_ALCANCE`; las otras seis dan el mismo resultado en los dos.

Las puertas 2, 3, 4 y 8 leen **exclusivamente** de su fuente de datos única. **No se escriben listas a mano en las pruebas.**

### 14.9.4 Pruebas de arquitectura que cuelgan de la puerta de pruebas

Fallan la construcción igual que las anteriores:

| Prueba | Qué comprueba |
|---|---|
| `test_check_coincide_con_enum` | Todo `CHECK` desplegado coincide con el enumerado declarado en `backend/app/dominio/estados.py`, que es la **fuente única de todos los enumerados del sistema** |
| `test_toda_transicion_declarada_tiene_origen_alcanzable` | Ninguna transición de las siete máquinas de estado parte de un estado inalcanzable |
| `test_todo_codigo_tiene_etiqueta` | Todo valor de todo catálogo tiene etiqueta en español en el archivo único de mensajes |
| Prohibición de borrado en cascada | No existe `ON DELETE CASCADE` ni `ON DELETE SET NULL` en el esquema |
| Censo de modelos | Todo modelo del ORM está en el censo cerrado de 70 entidades |
| Frontera de adaptadores | Ningún manejador de `backend/app/api/` invoca `ClienteCanvas` ni `ClienteGitHub` fuera de las seis escrituras síncronas autorizadas |
| Orden y anidamiento de cerrojos | Ninguna toma en orden inverso ni anidada del mismo espacio |
| Cabeceras del cliente de GitHub | Las cabeceras por defecto contienen `Accept`, `X-GitHub-Api-Version` y `User-Agent`; ningún módulo fuera de `backend/app/adaptadores/` instancia un cliente HTTP contra la API de GitHub |
| Origen permisivo prohibido | No aparece una configuración de CORS con origen comodín |
| Autoría de *commits* escritos por la aplicación | No aparece un literal de autor o de *committer* en el cuerpo de las escrituras de Git |

### 14.9.5 Catálogo cerrado de *workflows*

**[DECISIÓN NUEVA]** El repositorio contiene **exactamente tres *workflows* de GitHub Actions, y ninguno más**. Ninguna fuente cerraba esta lista, y una lista abierta es la forma más rápida de que aparezca un ejecutor con un secreto fuera del inventario cerrado de 14.6.2.

| Fichero | Disparo | Qué hace | Secretos que consume |
|---|---|---|---|
| `.github/workflows/puertas.yml` | Cada `push` y cada *pull request* | Las diez puertas de herramienta y las ocho de contrato, en los dos perfiles de alcance | Ninguno |
| `.github/workflows/vigilante.yml` | Programado cada 10 minutos | Llama a `POST /interno/latido` con la firma HMAC | `SIGNING_KEY` |
| `.github/workflows/actividad_demo.yml` | Programado y bajo demanda, **sólo sobre la organización del curso de demostración** | Genera actividad de demostración con token de instalación emitido en cada ejecución | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` |

**No existe un *workflow* de despliegue**, por el motivo de 14.10.1.

### Criterios de aceptación de 14.9

1. Un *pull request* con cualquiera de las dieciocho puertas en rojo **no puede integrarse** en `main`; la protección de rama lo impide sin excepción manual.
2. Registrando deliberadamente una ruta bajo `/api/cursos/{curso_id}` sin dependencia de permiso, la puerta 1 se pone en rojo.
3. Importando el ORM desde un módulo de `backend/app/dominio/`, la puerta de pureza se pone en rojo.
4. Registrando una ruta sin sesión que no figura en la lista cerrada, la puerta 3 se pone en rojo; declarándola en la lista pero prohibiéndola en el perfil en curso, se pone en rojo la 4 y no la 3.
5. La construcción se ejecuta en los dos perfiles de alcance y las seis puertas no parametrizadas dan el mismo resultado en ambos.
6. Después del 5 de octubre a las 12:00, la puerta 8 se pone en rojo si el catálogo de banderas no está vacío.
7. `.github/workflows/` contiene exactamente los tres ficheros de 14.9.5.
8. La cobertura medida sobre `backend/app/dominio` es igual o superior al 70 % y el informe queda registrado en la construcción.

---

## 14.10 Despliegue continuo, apagado ordenado y reversión

### 14.10.1 Disparo del despliegue

**El despliegue a producción se dispara sólo al integrar en `main`.** Se materializa con la **integración de Git nativa** de las dos plataformas: Render construye la imagen desde el `Dockerfile` de `backend/` con `autoDeploy` restringido a la rama `main` y declarado en `infra/render.yaml`; Vercel construye el frontend con raíz `frontend/`.

**[DECISIÓN NUEVA]** La carta contemplaba disparar el despliegue con *deploy hooks* de la plataforma. Esta especificación fija la **integración de Git con `autoDeploy` sobre `main`** en su lugar, por un motivo concreto: la URL de un *deploy hook* es una credencial, y almacenarla obligaría a introducir un decimosexto secreto en un inventario que las actas declaran **cerrado en quince entradas**. La integración de Git obtiene el mismo comportamiento —desplegar sólo al integrar en `main`— **sin ningún secreto nuevo que custodiar, rotar y retirar**.

### 14.10.2 Secuencia de un despliegue

| Paso | Quién | Qué ocurre |
|---|---|---|
| 1 | Plataforma | Construye la imagen desde el `Dockerfile`, con caché de capas, en ≤ 6 minutos |
| 2 | Servicio web | Arranca, **no migra**, responde `GET /salud` en ≤ 30 segundos. `GET /estado` declara el esquema como pendiente |
| 3 | Trabajador | Arranca, toma el cerrojo consultivo de migraciones, aplica `alembic upgrade head`, lo libera y empieza el bucle, en ≤ 60 segundos |
| 4 | Trabajador anterior | Recibe la señal de terminación y ejecuta el apagado ordenado de 14.10.3 |
| 5 | Monitor externo | Queda silenciado durante 10 minutos, declarado en el procedimiento, para no producir falsos positivos |

### 14.10.3 Apagado ordenado

**Trabajador**, ante la señal de terminación:

1. Se marca para parar y **deja de tomar trabajos nuevos de inmediato**.
2. El trabajo en vuelo dispone de **25 segundos**. Si termina, se confirma su transacción normalmente.
3. Si no termina, su fila vuelve a **`PENDIENTE`** con `tomado_por` y `tomado_en` a nulo y `proximo_intento_en = now()`, y **no se cuenta como intento fallido**: no fue un fallo, fue un reinicio.
4. La red de seguridad para la muerte sin señal es el trabajo `vigilancia` de 14.7.6.

**Servicio web:** deja de aceptar conexiones y termina las que están en vuelo en ≤ 25 segundos. El receptor de webhooks **valida, persiste y responde `202` en menos de 200 ms**, así que prácticamente nunca hay nada en vuelo; y si se perdiera una entrega, el proveedor la reenvía y la unicidad de `evento_webhook.delivery_id` la hace idempotente.

**Los trabajos del catálogo son de grano fino** —un repositorio, una captura, un mensaje— precisamente para que quepan en la ventana de 25 segundos: el aprovisionamiento de 200 sujetos son 200 trabajos, no uno.

### 14.10.4 Reversión

**La reversión es volver al despliegue anterior de la plataforma, que reutiliza la imagen ya construida de ese *commit*.** Objetivo: **menos de 3 minutos y sin construir nada**.

Queda **descartada** la reversión por `git revert` más redespliegue: reconstruye la imagen —minutos de espera con la aplicación caída— y una reconstrucción puede resolver algo distinto si algo no estuviera fijado.

**Las migraciones ya aplicadas no lo impiden.** Por la regla de compatibilidad hacia atrás de 14.8.2, **la imagen anterior funciona contra el esquema nuevo**. **No se revierte esquema nunca.** Ésa es la propiedad —y no la buena suerte— que hace segura la reversión.

**La reversión se ensaya el 12 de septiembre**, desplegando una versión deliberadamente rota y volviendo atrás, con el tiempo cronometrado y registrado en `.workflow/mediciones/`. Un procedimiento de reversión que nunca se ha ejecutado no es un procedimiento.

### 14.10.5 Congelación y corrección urgente

Rige la **congelación del 5 de octubre a las 20:00**. A partir de ahí:

- **No se actualiza ninguna dependencia**, ni por seguridad, salvo por el procedimiento de corrección urgente.
- **No se cambia `GITHUB_API_VERSION`.**
- **No entra ninguna migración**, ni siquiera aditiva.

**Procedimiento de corrección urgente, único camino legal:**

| Paso | Acción |
|---|---|
| 1 | Reproducción escrita del fallo en `docs/operacion.md` |
| 2 | Cambio mínimo, revisado por un segundo integrante |
| 3 | Las dieciocho puertas de construcción en verde |
| 4 | Etiqueta `hotfix-YYYYMMDD-n` en el repositorio |
| 5 | Despliegue y **verificación de que la reversión sigue disponible** antes de anunciarlo |
| 6 | **Aviso a los revisores**: mensaje por Canvas al profesor y a los ayudantes, comentario en la entrega, y entrada en `bitacora` con actor y fecha |

**Actualizaciones de seguridad:** entran sólo por este procedimiento y **sólo si la vulnerabilidad es alcanzable desde el código desplegado**. Una vulnerabilidad alta o crítica en una dependencia que el sistema no ejecuta **se documenta y no se toca**: cambiar una dependencia durante la corrección tiene más probabilidad de romper la aplicación que la vulnerabilidad de ser explotada en tres semanas.

### 14.10.6 Vigilancia de contratos externos y de deprecaciones

**La versión de la API de GitHub se fija por cabecera en todas las llamadas.** `ClienteGitHub` —único punto del sistema autorizado a hablar con la API de GitHub— envía en **cada** petición `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2026-03-10` y un `User-Agent` que identifica al producto y al curso. El valor vive en **una única constante** `GITHUB_API_VERSION`, y una prueba de arquitectura falla la construcción si las cabeceras por defecto no la contienen.

**Canvas no ofrece cabecera de versión.** La política equivalente es una **prueba de contrato semanal**, ejecutada contra el curso real en modo sólo lectura, que verifica que cada campo del que depende el sistema **sigue existiendo y con el tipo esperado**. Un fallo abre incidencia y correo operativo; **no rompe producción**.

| Qué se revisa | Frecuencia | Registro |
|---|---|---|
| Registro de cambios y página de cambios incompatibles de la API de GitHub | **Lunes 09:00** del 9-sep al 5-oct; **lunes y jueves** del 6-oct al 31-oct | Entrada fechada en `.workflow/mediciones/vigilancia-api.md`, **aunque no haya nada** |
| Notas de versión y tabla de deprecaciones de Canvas | Misma cadencia | Ídem |
| Auditoría de dependencias | En **cada** `push`, puerta 10 | Registro de la construcción |
| Prueba de contrato de Canvas | Semanal | `.workflow/mediciones/` |

**Una revisión sin hallazgos también se registra: la ausencia de entrada significa que nadie miró.**

**El 13 de octubre**, a mitad de la ventana de sostenimiento, se ejecuta un **redespliegue deliberado sin cambios** y se comprueba que la aplicación sigue en pie y que `GET /salud` devuelve el mismo `version`. Es la prueba de que la reproducibilidad es real y no una promesa.

### Criterios de aceptación de 14.10

1. Un *commit* directo a `main` es rechazado por la protección de rama; sólo una integración por *pull request* con las puertas en verde dispara despliegue.
2. Desplegando una versión deliberadamente rota en `ensayo` y revirtiendo al despliegue anterior, el tiempo cronometrado es **inferior a 3 minutos** y queda registrado con fecha el 12 de septiembre.
3. Tras la reversión, la imagen anterior funciona contra el esquema migrado y ninguna ruta devuelve error de esquema.
4. Reiniciando el trabajador durante un trabajo largo, la fila vuelve a `PENDIENTE` con `intentos` **sin incrementar**.
5. `/operacion` muestra el número de trabajos recuperados por vencimiento de toma en las últimas 24 horas, y esa cifra es cero en operación normal.
6. Una revisión de las llamadas salientes confirma que todas llevan `X-GitHub-Api-Version` con el valor de la constante única, y una búsqueda en el código encuentra ese valor escrito en un solo sitio.
7. `.workflow/mediciones/vigilancia-api.md` tiene una entrada por cada lunes desde el 9 de septiembre, con hallazgos o con la mención expresa de que no los hubo.
8. El redespliegue sin cambios del 13 de octubre queda registrado con la comparación del `version` antes y después.

---

## 14.11 Respaldo, restauración y evidencia

El plan gratuito de base de datos **no ofrece respaldos gestionados ni recuperación a un punto en el tiempo**, y ése es el motivo directo de que exista el respaldo propio (**A-016**, **A-170**, **Q-infraestructura-35**). **Sin este respaldo, la base es punto único de fallo de toda la evidencia de R2.4.5 a R2.4.7.**

| Elemento | Decisión |
|---|---|
| **Quién lo ejecuta** | El trabajo `respaldo_base_datos` del catálogo cerrado, alcance global, **05:00 diarias**, cerrojo global, clave de idempotencia igual a la fecha, 2 reintentos. **No se hace con un *workflow* de GitHub Actions**: exigiría exponer la cadena de conexión como secreto de un repositorio público y dejaría el respaldo dependiendo de la puntualidad de un *cron* que no está garantizada |
| **Contenido** | Volcado completo, comprimido y **cifrado con AES-256-GCM antes de salir del proceso**, de modo que el contenido no es legible ni siquiera por un miembro de la organización |
| **Destino** | Repositorio **privado** `gestor-operaciones`, **creado por la propia GitHub App**, lo que garantiza que queda dentro del alcance de la instalación. Se sube con el **token de instalación** obtenido en caliente, sobre `respaldos/{fecha}.sql.gz.enc`. **No se usan activos de versión** |
| **Segundo artefacto** | `respaldos/{fecha}-evidencia.csv.enc`, con una fila por versión de entrega vigente y superseded: `curso_slug`, `tarea_slug`, `entrega_slug`, `orden`, `tipo_sujeto`, `id_sujeto`, `repo_full_name`, `commit_sha`, `tag_nombre`, `fecha_corte_utc`, `intento`, `vigente`. Ocupa del orden de **120 KB para 600 repositorios** y **es restaurable sin PostgreSQL** |
| **Retención** | **14 días**, aplicada por el mismo trabajo, que borra los ficheros más antiguos |
| **Custodia de la clave** | El llavero de cifrado se custodia **fuera de la plataforma de despliegue**, en la bóveda compartida, con una copia por integrante, y el nombre del fichero incluye la versión de clave. Sin esa custodia, perder el entorno de despliegue destruiría la capacidad de restaurar: el respaldo seguiría existiendo y sería ilegible |
| **Fallo** | Incidencia `RESPALDO_FALLIDO` y correo con cargo a la reserva operativa. **Dos fallos consecutivos elevan la incidencia a bloqueante** y aparece banda en `/operacion`. Si el último respaldo tiene más de 30 horas, banda ámbar |

**Prueba de restauración completa, dos veces y con fecha: una antes del 16 de septiembre y otra antes del 6 de octubre.** Se descarga el último fichero, se descifra y se restaura sobre el proyecto de `ensayo`; se cronometra; y se compara el recuento de filas de `version_entrega`, `commit`, `bitacora` y `publicacion_nota` contra el origen. El resultado se registra en `.workflow/mediciones/`. **Un respaldo que nadie restaura no es un respaldo.**

**La etiqueta de Git no es respaldo oficial del SHA.** El `commit_sha` persistido es la evidencia normativa; la etiqueta es una comodidad de navegación. Con organización de plan gratuito no hay reglas aplicables a repositorios privados, de modo que cualquiera con permiso de escritura puede borrar una etiqueta. **La evidencia durable son tres copias: la fila en la base, el volcado cifrado diario y el CSV de evidencia.**

**Todo lo que la aplicación persiste entra en el respaldo**, porque todo vive en PostgreSQL. Lo único que no entra es lo que deliberadamente no se guarda: el código de los repositorios, que vive en GitHub y cuya evidencia es el SHA.

Si el volcado creciera por encima del tamaño admitido por la API de contenidos, se trocea en partes numeradas `{fecha}.sql.gz.enc.part01` y siguientes; el tamaño real se mide en la primera ejecución del 12 de septiembre.

### Criterios de aceptación de 14.11

1. Existe un fichero de respaldo cifrado por cada uno de los últimos 14 días en `gestor-operaciones/respaldos/`, y ninguno anterior.
2. `GET /estado` expone `respaldo.ultimo_exito_en` y `respaldo.tamano_bytes`, y el valor de fecha es de las últimas 30 horas.
3. La prueba de restauración anterior al 16 de septiembre está registrada con fecha, tiempo cronometrado y comparación de recuentos de las cuatro tablas de evidencia; la segunda, antes del 6 de octubre, también.
4. Descifrando el CSV de evidencia del día, cada fila de `version_entrega` vigente aparece con su `commit_sha`, y el recuento coincide con la consulta equivalente en la base.
5. Forzando el fallo del trabajo de respaldo dos días seguidos en `ensayo`, se abre `RESPALDO_FALLIDO`, la incidencia se eleva a bloqueante y aparece la banda en `/operacion`.
6. El repositorio `gestor-operaciones` es privado, lo creó la aplicación, lleva el topic de operaciones y **no** lleva el topic de tareas, y el equipo docente no tiene acceso a él.

---

## 14.12 Correo transaccional y DNS como infraestructura

Esta sección fija la **pieza de infraestructura**: proveedor, dominio remitente, registros DNS y contabilidad de la cuota. El contenido del informe docente y las reglas de suscripción viven en el capítulo de informes y comunicación.

### 14.12.1 Proveedor y adaptador

El proveedor de correo es un **servicio transaccional en plan gratuito**, detrás de la interfaz `ProveedorCorreo` con **dos implementaciones**: la de producción y la de **consola** para desarrollo y pruebas (**A-133**). El adaptador vive en `backend/app/adaptadores/` y expone `enviar(destinatario, asunto, html, texto, clave_idempotencia, reserva)`, con tiempo de espera explícito de **20 segundos**. **Lo consume únicamente el trabajo `despachar_outbox`: ninguna vista envía correo.**

El límite operativo verificado contra la página oficial de precios es de **100 correos al día**. El adaptador con sus dos implementaciones está en pie el **12 de septiembre**.

**El correo se envía siempre en dos partes, HTML y texto plano**, en la misma llamada. El HTML es de tabla única, sin JavaScript, sin imágenes externas y sin fuentes remotas.

Remitente visible, fijado y no negociable, con sus tres cadenas en variables de entorno y **nunca incrustadas en el código**:

| Cabecera | Valor |
|---|---|
| `From` | `"<NOMBRE_PRODUCTO> · ICC4201" <informes@send.<dominio>>` |
| `Reply-To` | `contacto@<dominio>` |
| `Subject` | `Informe docente · <nombre del curso> · dd-MM-yyyy` |

**No se envía desde una cuenta de correo personal ni gratuita del equipo**: no hay página oficial de límites de envío para una cuenta gratuita, el remitente sería una persona y no el producto, y la clave de aplicación sería un secreto de larga vida ligado a una cuenta personal.

**Un item de arranque avisa en `GET /estado` si `EMAIL_FROM` no pertenece al dominio configurado en `EMAIL_DOMINIO_VERIFICADO`**, para que nadie despliegue con un remitente no verificado.

### 14.12.2 DNS y autenticación del remitente

El equipo **tiene y ejerce control de los registros DNS**, porque el dominio es propio. Se usa el subdominio de envío `send.<dominio>` para que un problema de reputación de correo **no arrastre** a `app.<dominio>` ni a `api.<dominio>`.

| Fecha | Acción | Registro |
|---|---|---|
| **10-sep, 09:00** | Se decide nombre y dominio y se registra el dominio | — |
| **11-sep** | Se añade `send.<dominio>` en el panel del proveedor y se publican **literalmente** los registros que ese panel dicta | **SPF** (TXT en `send.<dominio>`) y **DKIM** (clave pública que emite el proveedor) |
| **11-sep** | Se publica DMARC en modo observación | `_dmarc.<dominio>` TXT: `v=DMARC1; p=none; rua=mailto:dmarc@<dominio>; fo=1; adkim=r; aspf=r` |
| **12-sep** | Se confirma el dominio como verificado y se guarda **captura fechada** | — |
| **20-sep** | Tras siete días de informes agregados sin fallos de alineación, se endurece DMARC | `v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc@<dominio>; fo=1` |

**Los valores exactos de SPF y DKIM son los que dicte el panel del proveedor y no se transcriben aquí como hecho**: quedan registrados con su valor literal en `.workflow/mediciones/` el 11 de septiembre. **Publicar `p=reject` desde el primer día queda descartado**: sin observación previa, un fallo de alineación tira el correo del informe justo en la ventana de corrección.

**«El correo llegó a la bandeja de entrada» es un criterio de aceptación verificable, y se verifica así, no por impresión:** el **28 de septiembre** y de nuevo el **5 de octubre** se envía el informe de prueba a tres buzones —una cuenta de correo comercial mayoritaria, una de otro proveedor mayoritario y un correo institucional—, se abre el original del mensaje y se comprueba que las tres líneas dicen **SPF: PASS, DKIM: PASS y DMARC: PASS**, y que el mensaje está en Recibidos y no en la carpeta de no deseado. Las capturas fechadas van a `.workflow/mediciones/`. **Si alguna de las tres da FAIL o el mensaje cae en no deseado, no se entrega esa versión**: se corrige el registro y se repite.

**Mitigación permanente, además de los registros y no en su lugar:** el informe **siempre** queda disponible en la aplicación con histórico y URL propia; el correo lleva en su cabecera visible la frase «si no ves este correo en tu bandeja, el informe completo está siempre en <enlace>»; y el texto de la entrega dice dónde encontrarlo sin depender del correo.

### 14.12.3 Cuota, reservas y comportamiento al agotarse

**La cuota es del proveedor sobre la cuenta: 100 correos al día para todo el despliegue. No es una cuota por curso** (**RG-197**). Contarla por curso haría que dos cursos con incidentes simultáneos creyeran tener 40 envíos operativos cuando el proveedor sólo acepta 20, y el segundo incidente se perdería en silencio justo cuando más importa.

| Reserva | Cuota diaria | Quién consume |
|---|---|---|
| `INFORME` | **60** | Un correo por suscriptor activo; el informe se envía **uno por destinatario**, nunca uno con varios destinatarios, porque el enlace de baja es por persona y porque un envío conjunto expondría las direcciones del equipo docente entre sí |
| `OPERATIVO` | **20** | Las cinco alertas del sistema, el correo a los profesores ante una vinculación rota, el aviso de tamaño de base, la alerta del vigilante del planificador, `RESPALDO_FALLIDO` y los dos correos de acceso docente |
| `MARGEN` | **20** | Sin asignar; absorbe reintentos y picos |

**Techo transitorio de 40 envíos operativos diarios entre el 16 de septiembre y el 2 de octubre**, con la incidencia informativa `CORREO_OPERATIVO_ELEVADO` por encima de 20.

**Volumen real esperado, con la aritmética escrita:** el equipo docente de un curso de demostración son ocho personas o menos; con dos cursos activos y todos suscritos, el consumo diario del informe es **16 envíos o menos** frente a los 60 reservados. El correo operativo, agrupado en **un solo correo por ciclo de vigilancia**, consume típicamente de 0 a 2 envíos diarios. Los envíos de prueba salen por `ensayo`, con su propia clave y su propia cuenta, y **no consumen la cuota de producción**; sólo las dos pruebas de entregabilidad salen por producción y son **6 envíos en total**. **Techo diario planificado: 18 sobre 100.**

**Qué hace la aplicación al agotar la cuota: encola y reintenta al día siguiente. Nada se descarta nunca.**

1. Antes de cada envío, `despachar_outbox` consulta el consumo del día por reserva.
2. Si la reserva y el margen están agotados, la fila pasa a **`DIFERIDO`** con `motivo_estado = 'CUOTA_AGOTADA'` y `proximo_intento_en` a las **00:05 del día siguiente en la zona horaria del curso**, **no se descarta y no cuenta como intento fallido**.
3. Se abre la incidencia **`CUOTA_CORREO_AGOTADA`**, visible en Pendientes y en `/operacion`.
4. Orden de cesión: el correo operativo **nunca baja de 5 envíos diarios**; por encima de 5 cede al informe; el informe cede el último y **por suscriptor**, por antigüedad de suscripción, no por curso.
5. Ante un `429` del proveedor se respeta `retry-after` si viene; si no, retroceso exponencial con *jitter* hasta 6 intentos. **Cualquier `4xx` de cuota no reconocido se trata como BLOQUEANTE**, es decir, sin reintento en bucle.

**Las comunicaciones por Canvas —conversaciones, comentarios y anuncios— no consumen esta cuota.**

**El consumo del día por reserva es una magnitud de despliegue** y se muestra sin filtrar en `/operacion`; el resto de secciones del panel están acotadas a los cursos donde quien mira es profesor activo.

### Criterios de aceptación de 14.12

1. El dominio de envío figura como verificado en el panel del proveedor, con captura fechada del 12 de septiembre en `.workflow/mediciones/`.
2. Los tres registros DNS —SPF, DKIM y DMARC— resuelven públicamente, y el valor literal de cada uno está registrado con fecha.
3. Las pruebas de entregabilidad del 28 de septiembre y del 5 de octubre muestran SPF, DKIM y DMARC en PASS en los tres buzones, con el mensaje en Recibidos, y las capturas están archivadas.
4. Arrancando con un `EMAIL_FROM` ajeno al dominio verificado, `GET /estado` lo declara y el hecho aparece en `/operacion`.
5. Agotando deliberadamente la reserva de informe en `ensayo`, los mensajes pasan a `DIFERIDO` con motivo `CUOTA_AGOTADA`, se abre `CUOTA_CORREO_AGOTADA`, **ninguno se pierde**, y al día siguiente a las 00:05 se reintentan.
6. Fuera de producción, ningún correo sale hacia el exterior: todos quedan escritos en el log estructurado.
7. El informe se envía como un correo por destinatario: una consulta a `mensaje_saliente` para una fecha muestra tantas filas como suscriptores activos, cada una con su propio destinatario.

---

## 14.13 Salud, sostenimiento y retirada

### 14.13.1 Endpoints de salud

| Endpoint | Qué comprueba | Quién lo usa |
|---|---|---|
| `GET /salud` | **Vivo**: el proceso responde. **No toca la base de datos.** Devuelve `estado`, `version`, `servicio` y `hora` en menos de 50 ms | Comprobación de salud de la plataforma y monitor externo |
| `GET /estado` | **Listo y diagnóstico**: consulta trivial a PostgreSQL, tamaño de la base, presupuesto de GitHub, validez de la credencial de Canvas por curso, antigüedad de la última sincronización por curso, retraso del planificador, revisión de esquema, último respaldo con éxito | Monitor externo, panel `/operacion`, equipo |

**`/salud` no toca la base a propósito:** si lo hiciera, un parpadeo de la base haría que la plataforma considerara el servicio enfermo y lo reiniciara en bucle, convirtiendo un problema de 10 segundos en una caída. **`/estado` devuelve `200` con `degradado: true` cuando algo está en ámbar y `503` sólo si la base de datos es inalcanzable.**

**`/estado` tiene dos respuestas según quién pregunte**, para poder monitorizarse desde fuera sin exponer nada:

| Forma | Contenido | Acceso |
|---|---|---|
| **Anónima** | Booleanos y contadores agregados, **sin un solo nombre ni identificador de curso** | Pública |
| **Completa** | Desglose por curso | Sólo con sesión y permiso de lectura del curso, acotada a los cursos del solicitante |

**Ninguna de las dos devuelve jamás un secreto.** La **puerta de acotación del panel** falla la construcción si `/api/estado` en su forma completa se registra sin la dependencia que acota por los cursos del solicitante.

### 14.13.2 Monitor externo y guardia

**Monitor externo en plan gratuito, intervalo de 5 minutos, tres monitores:**

| # | Objetivo | Condición de alerta |
|---|---|---|
| 1 | `https://api.<dominio>/salud` | Código distinto de `200` |
| 2 | `https://app.<dominio>/` | Ausencia de la palabra clave «Iniciar sesión» —detecta un frontend desplegado pero roto, que un `200` no detecta— |
| 3 | `https://api.<dominio>/estado` | Ausencia de la marca de planificador al día |

Las alertas del monitor salen **por la infraestructura del monitor** (correo del equipo y grupo de mensajería), de modo que **no consumen la cuota de 100 correos diarios** y de modo que **una caída de la aplicación no impide avisar de la caída de la aplicación**.

Esto **complementa y no sustituye** al vigilante del planificador de 14.7.7: uno vigila que la aplicación responda desde fuera, el otro vigila que el planificador lata. **Ninguno de los dos es un *pinger***, y la prueba es que los servicios están en plan de pago y no se suspenden.

**Turno de guardia del 6 al 31 de octubre**, escrito en `docs/operacion.md` y en el calendario compartido, no en la memoria de nadie:

| Elemento | Compromiso |
|---|---|
| Rotación | **Dos días por integrante**, cuatro integrantes, cubriendo del 6 al 31 de octubre inclusive. Cada turno tiene **titular y suplente nombrados** |
| Respuesta | Acuse en **≤ 30 minutos** y mitigación iniciada en **≤ 2 horas** entre las 08:00 y las 23:00; fuera de ese horario, acuse y mitigación **a primera hora del día siguiente**, y en ningún caso más de **12 horas** |
| Escalado | Sin acuse en 30 minutos, la alerta se reenvía al grupo completo; sin mitigación en 2 horas, se convoca a los cuatro |
| **Primera acción, siempre la misma** | Abrir `/operacion`, mirar los bloques de despliegue, cola y límites, y **si el último despliegue es la causa probable, revertir a la imagen anterior**, que tarda menos de 3 minutos. **Diagnosticar después, con la aplicación en pie** |
| Registro | Toda incidencia deja entrada fechada en `docs/operacion.md` con hora de detección, hora de restablecimiento, causa y acción |

**Comunicación de una caída al profesor y a los ayudantes que están corrigiendo:**

1. **Aplicación en pie pero degradada:** banda persistente en la cabecera del curso con el texto exacto de qué no funciona y desde cuándo.
2. **Aplicación caída:** mensaje desde la cuenta del equipo por Canvas al profesor y a los ayudantes, más comentario en la entrega, indicando qué ocurrió, la hora estimada de restablecimiento y que **el trabajo de corrección no se pierde**, porque las notas y las rúbricas viven en Canvas y las versiones están registradas y respaldadas.
3. **Dirección de contacto publicada por adelantado** en el texto de la entrega, atendida por quien esté de turno.
4. **Al restablecerse**, un segundo mensaje por el mismo canal diciendo que ya está y que se comprobó.

### 14.13.3 Calendario de infraestructura

| Fecha | Hito |
|---|---|
| **10-sep 09:00** | Decisión de nombre y dominio; registro del dominio; creación de las cuentas con la cuenta de correo operativa |
| **10-sep** | Contratación de los dos servicios de pago; creación del proyecto de base de datos definitivo; registro de las diez URIs ante terceros |
| **11-sep** | Primer despliegue con Docker; publicación de los registros DNS de correo |
| **12-sep** | Verificación del dominio remitente; **ensayo cronometrado de la reversión**; mediciones de construcción, arranque y primer respaldo |
| **13-sep** | Medición de capacidad, caducidad y límite de conexiones de la base |
| **14-sep** | Ensayo completo del guion de demostración **sobre producción**, incluida la provocación deliberada de dos fallos |
| **Antes del 16-sep** | Migración inicial aplicada; respaldo diario funcionando y **restauración ya probada**; puertas de construcción en verde con `main` protegida; motor de cola, planificador, bitácora, clasificación de errores y panel de operación en pie; las cinco alertas por correo operativas |
| **23-sep / 30-sep / 3-oct** | Entrada en servicio de los trabajos de los Bloques 1, 2 y 3, con retirada fechada de su bandera de alcance |
| **28-sep y 5-oct** | Pruebas de entregabilidad de correo |
| **Antes del 6-oct** | Segunda prueba de restauración; ensayo de rotación de los quince secretos |
| **5-oct 12:00** | Catálogo de banderas de alcance eliminado del código |
| **5-oct 20:00** | **Congelación**: sólo correcciones urgentes documentadas |
| **7-oct** | **Rotación programada de los quince secretos** |
| **13-oct** | Redespliegue deliberado sin cambios |
| **6-oct → 31-oct** | Turnos de guardia; vigilancia diaria de las cinco alertas y de la cuota de correo; revisión de deprecaciones lunes y jueves |
| **1-nov** | Retirada de servicios, de accesos del evaluador y de `CANVAS_TOKEN_DEMO` |

### 14.13.4 Sostenimiento comprometido

§3.2 exige la aplicación disponible **al menos dos semanas** después del 6 de octubre. Esta especificación compromete **hasta el 31 de octubre inclusive**, con margen, y lo sostiene con decisiones concretas y no con buena voluntad: base de datos que no caduca en esa ventana, servicios que no se suspenden, artefacto reproducible, respaldo diario con restauración probada, comprobación automática de salud con alerta por correo, reversión ensayada de menos de 3 minutos, congelación de despliegue y turnos de guardia nombrados.

### Criterios de aceptación de 14.13

1. Los tres monitores externos están configurados con intervalo de 5 minutos y hay captura fechada de su configuración en `.workflow/mediciones/`.
2. Deteniendo el servicio web en `ensayo`, el monitor emite alerta en menos de 5 minutos por un canal que no depende del proveedor de correo de la aplicación.
3. `GET /estado` sin sesión devuelve únicamente booleanos y contadores agregados: una revisión de la respuesta confirma que no contiene ningún nombre ni identificador de curso.
4. `GET /estado` con sesión devuelve exclusivamente los cursos donde el solicitante es profesor activo; solicitando el desglose de un curso ajeno, la respuesta no lo incluye.
5. `docs/operacion.md` contiene el calendario de turnos del 6 al 31 de octubre con titular y suplente por turno, y la primera acción escrita de la guardia.
6. La aplicación responde en su URL comprometida el 20 de octubre y el 31 de octubre, con `GET /salud` en `200` y el mismo `version` que el día de la entrega, salvo corrección urgente registrada.
7. El 1 de noviembre quedan registradas por escrito la baja de los servicios de pago, la retirada de los accesos del evaluador y la retirada del token de demostración.

---

## 14.14 Trazabilidad: requisito → sección

| Requisito o cláusula | Qué exige, en corto | Secciones de este capítulo que lo sostienen |
|---|---|---|
| **R2.1.4**, **R2.1.5** | Vincular el curso con Canvas y con GitHub | 14.2.3 (URIs registradas), 14.6.2 y 14.6.4 (credenciales vivas y cifradas), 14.4 (entornos separados) |
| **R2.1.7**, **R2.1.8** | Equipo docente y permisos | 14.9.3 (puertas de contrato 1, 2 y 5), 14.6 (custodia) |
| **R2.1.9** | Retirar a un ayudante con efecto inmediato | 14.9.3 (puerta de autorización), 14.7.4 (trabajos de revocación) |
| **R2.3.10** | Crear los repositorios progresivamente, **de forma automática y sin interacción de un usuario** | 14.7 completa (cola, planificador, garantías, catálogo), 14.2.1 (servicios que no se suspenden), 14.10.3 (apagado ordenado sin duplicar) |
| **R2.3.11** | Mostrar claramente el estado de creación, incluidos los problemas | 14.7.5 (clasificación de errores con mensaje literal), 14.7.4 |
| **R2.4.4** | Mantener las fechas actualizadas | 14.7.4 (`sync_tareas_y_fechas`) |
| **R2.4.5**, **R2.4.7** | Registrar y conservar la versión de cada entrega | 14.7.4 (`resolver_sha`, `crear_etiqueta`, `precierre_actividad`), 14.8.2 (prohibición de migraciones destructivas), 14.11 (respaldo y CSV de evidencia) |
| **R2.5.1** | Tablero disponible **de forma inmediata** | 14.1 principio 1, 14.2.1 (sin arranque en frío), 14.3 (base que no autosuspende) |
| **R2.5.2**, **R2.5.3**, **R2.5.10** | Actividad de los repositorios a lo largo del tiempo | 14.2.1 (webhooks no se pierden), 14.7.4 (ingesta, reconciliación y barrido), 14.6.2 (secreto del webhook) |
| **R2.6.1** | Generar el informe docente diario | 14.7.4 (`informe_diario` a las 07:00 de la zona del curso), 14.3.3 (informe persistido sin purga) |
| **R2.6.3** | Suscripción y baja individuales | 14.12.3 (un correo por destinatario) |
| **R2.6.4** | **Enviar** el informe por correo | 14.12 completa (proveedor, DNS, cuota, encolado sin descarte) |
| **§3.1** | Demostración en vivo el 16 de septiembre | 14.13.3 (calendario), 14.8.3 (una migración fallida no despliega roto), 14.4 (ensayo destructivo sin tocar el curso real) |
| **§3.2** | URL disponible al menos dos semanas después del 6 de octubre | 14.2.2 (URL congelada), 14.3.1 (base que no caduca), 14.5.2 (artefacto reproducible), 14.10.4 (reversión), 14.13.4 (sostenimiento hasta el 31 de octubre) |
| **§3.3** | Actividad individual de validación del 7 de octubre | 14.6 (inventario de secretos con dueños y procedimiento), 14.7.1 (cola defendible sin apelar a magia), 14.11 (restauración probada) |
| **§4** | «Lo que no se puede usar no cuenta» y libertad de lenguaje y librerías | 14.1 principio 5, 14.2.1 (el coste compra cinco requisitos), 14.9 (puertas que impiden entregar algo inaccesible) |

### Criterios de aceptación de 14.14

1. Cada fila de la tabla apunta a una sección existente de este capítulo, y ninguna sección principal del capítulo queda sin al menos un requisito o cláusula asociada.
2. Los criterios de aceptación de las secciones 14.1 a 14.13 se pueden ejecutar sin acceso a documentos distintos de éste, salvo para las magnitudes que este capítulo declara medidas y registradas en `.workflow/mediciones/`.
