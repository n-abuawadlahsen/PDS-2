# Preguntas de alcance — Area infraestructura

36 preguntas finales, fusionadas desde 48 de entrada (46 del area mas 2 de la ronda critica); 21 bloquean la entrega parcial del 16-sep y ninguna quedo apartada por estar ya respondida en el enunciado.

## 1. Decisiones estructurales de plataforma y stack

### Q-infraestructura-01 — ¿Con que lenguaje y framework se construye la aplicacion (backend y frontend), decidido segun la experiencia real de cada integrante y no segun la recomendacion del estudio de APIs? ¿Que integrante domina cada capa, que librerias cliente se usaran para GitHub y para Canvas, y cuanto tiempo de aprendizaje se acepta considerando que quedan 8 dias hasta la parcial del 16-sep?

- **Requisitos:** Seccion 4 (libre y gratuito), R2.3.10, R2.5.1, R2.6.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Determina las librerias disponibles (Octokit resuelve JWT, renovacion de tokens, paginacion y throttling; en Python hay que armarlo con githubkit/PyGithub), la tecnologia de cola/cron, las plantillas de deploy y la velocidad del equipo. Todo requisito de jobs en background (R2.3.10, R2.4.5, R2.6.1) depende de esta eleccion.
- **Opciones:**
  - Node + TypeScript (Next.js / Express / NestJS + Octokit)
  - Python (FastAPI / Django + githubkit o PyGithub + canvasapi)
  - Ruby on Rails
  - Java / Kotlin + Spring Boot
  - Otro con el que el equipo ya tenga experiencia
- **Estudio de APIs:** §12 sugiere Node+TypeScript (Octokit) o Python+FastAPI, Postgres y Redis, con tabla de librerias por necesidad; el propio estudio aclara que no es una decision aprobada.
- **Fusiona:** P717

### Q-infraestructura-02 — ¿La arquitectura es un monolito con render en servidor (un solo servicio desplegable, cookies de sesion) o una API + SPA separada (dos deploys, CORS, autenticacion por token, monorepo o dos repositorios)? Si es SPA, ¿se sirve desde el mismo origen que la API o desde otro dominio?

- **Requisitos:** R2.5.1, R2.1.6, R2.7.3
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Cambia el numero de servicios a pagar y mantener en hosting gratuito, el modelo de autenticacion (cookie vs token), la superficie CSRF/CORS, la forma de entregar "todo el codigo por GitHub" (uno o varios repos) y la cantidad de codigo para 4 semanas.
- **Opciones:**
  - Monolito SSR (templates + HTMX/Alpine o similar)
  - Framework full-stack con SSR y API integradas (Next.js/Nuxt/Rails)
  - API REST + SPA (React/Vue) servida desde el mismo origen
  - API + SPA en origenes distintos con CORS
- **Estudio de APIs:** §12 dibuja "Web App (SSR o SPA + API)" y deja la eleccion abierta.
- **Fusiona:** P718

### Q-infraestructura-03 — ¿Que motor de base de datos y que proveedor se usan: PostgreSQL gestionado por el PaaS, Postgres externo (Neon, Supabase), MySQL/MariaDB, SQLite en disco (se pierde en redeploy si el filesystem es efimero) o MongoDB? ¿Quien es dueño de la cuenta del proveedor y quien tiene acceso a la base de produccion?

- **Requisitos:** R2.4.5, R2.4.7, R2.5.1, R2.3.10
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** El worker idempotente necesita transacciones y locks (SELECT FOR UPDATE / advisory locks); las fechas exigen timestamptz; el SHA de cada entrega vive en la base como fuente de verdad, asi que la durabilidad y el backup del proveedor son criticos para R2.4.7.
- **Opciones:**
  - Postgres del PaaS (Render/Railway)
  - Postgres externo gratuito (Neon / Supabase)
  - SQLite con disco persistente pago
  - MySQL/MariaDB
  - MongoDB Atlas free
- **Estudio de APIs:** §12 indica "Postgres"; §8.3 propone un modelo de datos relacional; §14 exige timestamptz.
- **Fusiona:** P719

### Q-infraestructura-04 — ¿En que proveedor y con que plan se despliega la aplicacion, y que presupuesto se acepta, sabiendo que los planes gratuitos suelen suspender el servicio tras inactividad (lo que detiene cron y workers y rompe R2.3.10, R2.4.5 y R2.6.1) y que la app debe seguir viva al menos hasta el 20-oct? ¿El equipo esta dispuesto a pagar un monto pequeño (US$5-10/mes por servicio sin sleep) o interpreta "libre y gratuito" como costo cero absoluto tambien para hosting? ¿Quien pone la tarjeta, a nombre de quien queda la cuenta y con que medio de pago? ¿Se necesitan servicios separados para web, worker, Postgres y Redis, o un solo proceso con cron interno? Verificar ademas: Railway ya no ofrece plan gratuito permanente (credito de prueba), Fly.io elimino el free tier para cuentas nuevas y Render Free duerme y limita a un web service.

- **Requisitos:** R2.3.10, R2.4.5, R2.5.2, R2.6.1, Seccion 3.2 (URL disponible dos semanas), Seccion 4 (libre y gratuito)
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Determina la arquitectura de despliegue y un costo mensual que el spec debe registrar como restriccion; decide si hay sleep de instancia (afecta cron y webhooks), si se puede tener worker separado, si la URL sobrevive las dos semanas post-entrega y si hay que reconfigurar redirect URIs al cambiar de proveedor.
- **Opciones:**
  - Render Free (con sleep) o Render Starter pago
  - Railway con credito de prueba o plan Hobby
  - Fly.io
  - Vercel (frontend) + backend en otro proveedor
  - VPS gratuito (Oracle Cloud Always Free) o VPS pago
  - Servidor de la universidad o PC propio con tunel
  - Plan pago minimo en un solo proveedor con todos los servicios
  - Free tier + keep-alive externo
- **Estudio de APIs:** §12 propone Postgres + Redis + workers separados y deploy en Railway/Render/Fly.io, sin analizar planes, costos ni suspension por inactividad.
- **Fusiona:** P713, P721

### Q-infraestructura-05 — ¿Se fija desde ahora una URL HTTPS definitiva y publica (subdominio del proveedor, con TLS incluido, o dominio propio de ~US$10/año con DNS y certificado) que se use igual en la parcial y en la final, quede congelada antes del 16-sep y sea la misma que se entrega el 6-oct? Los redirect URIs de Google, de la Developer Key de Canvas y de la GitHub App (callback, setup_url, webhook) quedan atados a ella: ¿se registran de antemano las URIs de localhost, staging y produccion en los tres proveedores? ¿Quien compra y configura el dominio, quien administra la URL, con que costo, y esta garantizada su disponibilidad durante las dos semanas posteriores al 6-oct? ¿Se dispone ademas de un tunel (ngrok/cloudflared/smee.io) para recibir webhooks en desarrollo, y que pasa con el diseño de ingesta si no se consigue una URL publica estable?

- **Requisitos:** R2.1.2, R2.1.4, R2.1.5, R2.5.2, R2.5.10, Seccion 3.1, Seccion 3.2
- **Tipo:** decision_equipo + dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Cambiar la URL entre entregas obliga a reconfigurar tres proveedores externos y a reinstalar la App, y puede romper OAuth el dia de la revision; sin URL publica estable la ingesta por webhooks no puede probarse y el diseño debe cambiar a polling. El dominio condiciona ademas el remitente de email (SPF/DKIM).
- **Opciones:**
  - Subdominio del PaaS (*.onrender.com, *.up.railway.app) para ambas entregas
  - Dominio propio comprado y administrado por el equipo
  - Dominio ya existente de un integrante o del curso
  - Subdominio del PaaS en la parcial y dominio propio en la final (asumiendo la reconfiguracion)
- **Estudio de APIs:** §1.1 fija la redirect_uri en la Developer Key; §3.3 el setup_url de la App; §8.1 la URL del webhook configurada en la App y sugiere ngrok/cloudflared o desplegar temprano; §12 recuerda que se necesita URL publica para los webhooks y la exigencia de dos semanas de disponibilidad.
- **Fusiona:** P714, P737, P747

## 2. Cuentas, instancias y credenciales de los servicios externos

### Q-infraestructura-06 — ¿Contra que instancia(s) de Canvas se desarrolla y se demuestra: la instancia institucional de la universidad con un curso del ramo (requiere Developer Key emitida por el administrador), Free-for-Teacher (canvas.instructure.com) con un curso de prueba creado por el equipo, o Canvas open-source autoalojado en Docker? ¿Quien gestiona el acceso y para que fecha debe estar decidido? ¿La aplicacion soporta multiples canvas_base_url (uno por curso) o una unica instancia por entorno? Si al 16-sep no hay Developer Key, ¿la vinculacion se hace pegando un token manual del profesor en una UI de emergencia protegida por flag, ademas del flujo OAuth?

- **Requisitos:** R2.1.4, R2.1.6, R2.2.1, R2.2.2, R2.2.3
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Es la dependencia externa mas critica de la parcial: sin instancia con datos y sin credencial OAuth no hay demo. Cambia la URL base, la disponibilidad de Developer Key, la capacidad de crear secciones/grupos/estudiantes ficticios, si el profesor puede verificar los efectos desde su lado, y decide el modelo de datos (base URL por curso) y las redirect URIs registradas.
- **Opciones:**
  - Instancia institucional con Developer Key emitida por el admin
  - Free-for-Teacher (canvas.instructure.com) con cuenta del equipo
  - Canvas open source autoalojado en Docker (local o VPS)
  - Combinacion: FFT para la parcial e institucional para la final
  - Combinacion: institucional en produccion y FFT en desarrollo
- **Estudio de APIs:** §1.2 recomienda Free-for-Teacher como plan B, afirma que ahi "son admin de su propia cuenta y pueden crear la Developer Key" y admite tokens manuales para desarrollo/demo; §3.2 pide guardar canvas_base_url porque "la instancia varia".
- **Fusiona:** P707, P730

### Q-infraestructura-07 — Si se usa la instancia institucional: ¿quien solicita la Developer Key (¿el profesor del ramo ante el administrador de Canvas?), con que redirect_uri exacta (debe ser la URL publica definitiva), con que scopes, en que plazo se espera respuesta y cual es la fecha limite para abandonar este camino y pasar al plan B?

- **Requisitos:** R2.1.4, R2.1.6
- **Tipo:** dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Fija una dependencia critica con fecha de corte; la redirect_uri obliga a tener la URL de deploy definida antes de solicitar la key.
- **Opciones:**
  - Solicitud ya iniciada por el profesor, con fecha de corte definida
  - Solicitud a cargo de un integrante del equipo ante el administrador
  - No se solicita: se va directo al plan B
- **Estudio de APIs:** §1.1 describe el flujo con Developer Key creada por el admin de la instancia; §1.3 lista los scopes necesarios; §13 hito 2 la marca "Depende de terceros, Dia 1".
- **Fusiona:** P709

### Q-infraestructura-08 — ¿Es efectivo que en Free-for-Teacher (canvas.instructure.com) un usuario puede crear Developer Keys (client_id/secret OAuth2) para su propia cuenta, o solo puede generar tokens de acceso manuales por usuario? Debe probarse empiricamente entrando a canvas.instructure.com y buscando Admin → Developer Keys. Si NO es posible, ¿cual es el mecanismo de autenticacion Canvas para la demo del 16-sep (token manual del profesor de prueba, conseguir la key institucional), como se demuestra entonces el flujo OAuth completo y como se compatibiliza con la politica de Canvas que prohibe pedir tokens manuales a otros usuarios?

- **Requisitos:** R2.1.4, R2.1.6
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Si la afirmacion del estudio es falsa, el flujo OAuth2 no podra demostrarse en la parcial y el spec debe contemplar el modo "token manual" como camino oficial o exigir Developer Key institucional.
- **Opciones:**
  - Se confirma que FFT permite crear Developer Key: OAuth2 completo en la demo
  - Solo tokens manuales: se demuestra con token manual y se documenta la limitacion
  - Solo tokens manuales: se escala a conseguir la key institucional antes del 16-sep
- **Estudio de APIs:** §1.2 afirma que en FFT "ustedes son admin de su propia cuenta y pueden crear la Developer Key" (sin evidencia) y la misma seccion cita que pedir tokens manuales a otros usuarios viola la API Policy de Canvas.
- **Fusiona:** P708, P731

### Q-infraestructura-09 — Si se usa Free-for-Teacher: ¿permite crear secciones multiples, group sets, overrides por seccion y por estudiante, rubricas, anuncios y conversaciones via API con el token del profesor? ¿Hay limites de estudiantes o de invitaciones por curso?

- **Requisitos:** R2.2.2, R2.2.3, R2.4.2, R2.4.3, R2.6.5, R2.6.6, R2.7.5
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Si alguna capacidad falta, el dataset de prueba no cubrira R2.4.2/R2.4.3 ni R2.6.x y habra que buscar otra instancia a tiempo.
- **Opciones:**
  - Se verifica y todas las capacidades estan disponibles: se usa FFT
  - Falta alguna capacidad: se cambia de instancia
  - Falta alguna capacidad: se documenta y se ajusta el dataset de demo
- **Estudio de APIs:** §1.2 afirma que en FFT pueden "cargar estudiantes de prueba, secciones y grupos"; no verifica overrides, rubricas ni conversaciones.
- **Fusiona:** P716

### Q-infraestructura-10 — ¿Quien crea el proyecto de Google Cloud y la pantalla de consentimiento OAuth, y con que cuenta (personal de un integrante o cuenta del equipo)? ¿El proyecto queda en modo "Testing" (maximo 100 usuarios de prueba agregados a mano, lo que obliga a registrar los gmail del profesor y de los ayudantes evaluadores antes del 16-sep) o se publica en "Production"? Publicar con scopes openid/email/profile, ¿requiere verificacion de la app o basta con aceptar la pantalla "app no verificada", y que pantalla exacta vera el revisor la primera vez (se explica en la guia de acceso)? ¿Se usa un cliente OAuth por entorno con sus propias redirect URIs? Y dado que R2.1.2 restringe a correos gmail.com, ¿los evaluadores tienen cuentas gmail.com o usan @uandes.cl (Google Workspace)? ¿Se necesita una allowlist de dominios configurable por entorno o un usuario local de emergencia? ¿Quien custodia el client_secret?

- **Requisitos:** R2.1.1, R2.1.2
- **Tipo:** dependencia_externa + investigable_en_docs · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Si un evaluador no puede iniciar sesion el 16-sep, la demo no empieza; el modo Testing exige conocer sus correos con antelacion y define el checklist de despliegue y la custodia del client_secret.
- **Opciones:**
  - Proyecto en Testing con los evaluadores registrados como usuarios de prueba
  - Proyecto publicado en Production asumiendo la pantalla "app no verificada"
  - Proyecto publicado y verificado ante Google
  - Un unico cliente OAuth para todos los entornos / un cliente por entorno
  - Allowlist de dominios configurable (gmail.com y/o dominio institucional) o usuario local de emergencia
- **Estudio de APIs:** §3.1 solo describe la validacion del claim email (@gmail.com, email_verified); no trata el estado del proyecto GCP, sus usuarios de prueba ni la verificacion.
- **Fusiona:** P715, P732, P751

### Q-infraestructura-11 — ¿Que organizacion de GitHub se usa para la demo del 16-sep y para la revision: una organizacion nueva del equipo (plan Free), la organizacion del curso administrada por el profesor, o ambas? ¿Quienes son owners de cada una? ¿Es la misma organizacion donde vive el codigo fuente entregable o una separada para no mezclar repos generados de estudiantes con el codigo del proyecto? Para uso real, ¿el profesor del curso tiene una organizacion donde sea owner para instalar la App, y quien la crea, dado que no existe API para crear organizaciones? ¿Se usa el plan Free de la organizacion (repos privados con funciones limitadas) o se solicita GitHub Team gratuito via GitHub Education for Teachers? ¿Cuantos colaboradores externos en repos privados admite la organizacion elegida?

- **Requisitos:** R2.1.5, R2.3.7, R2.3.9
- **Tipo:** decision_equipo + dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Instalar una GitHub App exige ser owner de la organizacion; mezclar codigo fuente y repos generados complica la entrega "todo el codigo por GitHub" y la limpieza del sandbox; y las funciones disponibles (rulesets, branch protection en privados) y el limite de colaboradores dependen del plan y cambian el diseño de proteccion de tags.
- **Opciones:**
  - Una organizacion nueva del equipo (Free) para todo
  - Dos organizaciones: una para el codigo entregable y otra para los repos generados
  - Organizacion del curso administrada por el profesor
  - Organizacion con GitHub Team gratuito via GitHub Education
- **Estudio de APIs:** §3.3 describe la instalacion de la App en la organizacion; §14 recomienda repos privados y advierte "si la org es Free, revisen el limite de colaboradores en repos privados".
- **Fusiona:** P710, P734

### Q-infraestructura-12 — ¿Bajo que cuenta se registra la GitHub App: la cuenta personal de un integrante o una organizacion del equipo (transferible, con varios administradores)? ¿Quien custodia la clave privada .pem y el webhook secret, y como se comparten con el resto del equipo y con el despliegue? ¿Se marca la App como publica para que el profesor pueda instalarla en SU propia organizacion, o queda privada? Como cada App tiene una sola webhook URL y una sola clave privada, ¿se crean Apps separadas para dev/staging/prod con organizaciones de prueba separadas, o una sola App apuntando a produccion y en local se usa smee.io/ngrok? ¿Quien puede cambiar los permisos de la App, sabiendo que cada cambio exige que la instalacion acepte los nuevos permisos? ¿Que pasa con la App y con la continuidad del servicio si el integrante dueño pierde acceso a su cuenta o abandona el equipo?

- **Requisitos:** R2.1.5, R2.1.6, R2.3.7, R2.5.2
- **Tipo:** decision_equipo + dependencia_externa · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define custodia de secretos, continuidad del servicio, si el flujo "Conectar organizacion" funciona con organizaciones ajenas al equipo durante la revision, como se prueba localmente el webhook y cuantas instalaciones hay que mantener. Sin App lista no hay demo.
- **Opciones:**
  - App bajo cuenta personal de un integrante
  - App bajo una organizacion del equipo (transferible)
  - Una sola App para todos los entornos + tunel en local
  - Apps separadas por entorno (dev/staging/prod) con orgs de prueba distintas
  - App publica (instalable por terceros) / App privada
- **Estudio de APIs:** §2.2 describe el JWT firmado con la .pem y el flujo de la App; §3.3 propone redirigir a github.com/apps/<app>/installations/new; §8.1 sugiere ngrok/cloudflared en local; §12 no trata entornos; §13 hito 3 marca "GitHub App creada + instalada en una org de prueba" (Dia 1-2, riesgo rojo); §14 exige que la .pem no vaya al repositorio y que los secretos vayan a variables de entorno.
- **Fusiona:** P711, P729, P752

### Q-infraestructura-13 — ¿Se activa "enforce scopes" en la Developer Key de Canvas y se enumera la lista exacta de scopes url:METHOD|path necesarios, o se deja sin scopes (token con todos los permisos del profesor)? En la GitHub App, ¿se piden solo Administration (write), Contents (write) y Metadata (read), y Members (write) unicamente si se decide invitar estudiantes a la organizacion? ¿Se documenta la justificacion de cada permiso para la validacion del 7-oct?

- **Requisitos:** R2.1.4, R2.1.5, R2.6.5, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Principio de minimo privilegio verificable; cada permiso adicional de la App exige reaceptacion por parte de la instalacion, y cada scope faltante en Canvas produce 401 en produccion.
- **Opciones:**
  - Developer Key con enforce scopes y lista minima enumerada
  - Developer Key sin scopes (permisos completos del profesor)
  - GitHub App con permisos minimos (Administration, Contents, Metadata)
  - GitHub App con permisos minimos + Members (write)
- **Estudio de APIs:** §1.3 lista los scopes de Canvas; §2.3 incluye la tabla de permisos de la App; §6.4 marca Members como opcional.
- **Fusiona:** P738

### Q-infraestructura-14 — ¿Se hara una prueba end-to-end (fecha limite propuesta: antes del 10-sep / semana 1) con la GitHub App instalada en la organizacion de prueba y el installation token, verificando que POST /orgs/{org}/repos, PATCH is_template, POST /repos/{t}/{r}/generate, PUT collaborators (201 vs 204) y POST /git/refs devuelven 201/204 con el conjunto minimo de permisos elegido, y si la configuracion "Repository creation" de la organizacion restringe a la App? ¿Quien la ejecuta, cual es la fecha limite y donde se registra el resultado (lista definitiva de permisos que la App solicita)?

- **Requisitos:** R2.3.5, R2.3.7, R2.3.9, R2.4.5
- **Tipo:** verificar_empiricamente · **Entrega:** parcial · **Bloquea la parcial:** si
- **Por que importa:** Un 403 descubierto el 15-sep obliga a cambiar los permisos de la App y a que la instalacion los acepte de nuevo; bloquea el corazon de la demo. El resultado fija en el spec los permisos exactos.
- **Opciones:**
  - Prueba ejecutada antes del 10-sep por un responsable designado
  - Prueba ejecutada durante la semana 1 con fecha limite explicita
  - Se omite la prueba y se asume la documentacion
- **Estudio de APIs:** §2.3 pide "verifiquenlo empiricamente" y marca como ambiguos los permisos para crear repos en organizacion y para /generate (Apendice A.1 y A.2); §13 hito 3 lo ubica en Dia 1-2.
- **Fusiona:** P712, P736

## 3. Ejecucion automatica: scheduler, colas e ingesta de actividad

### Q-infraestructura-15 — Si el hosting duerme la instancia por inactividad (Render Free ~15 min), ¿como se garantiza que los jobs periodicos (aprovisionamiento cada 2 min, snapshots cada 5, sincronizacion con Canvas cada 10, informe a las 07:00) realmente se ejecuten? Si se usa un scheduler externo que llama a endpoints internos, ¿como se autentican esos endpoints (header con secreto, IP allowlist, firma) y que ocurre si se invocan dos veces seguidas o en paralelo?

- **Requisitos:** R2.3.10, R2.4.4, R2.4.5, R2.6.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** R2.3.10 exige creacion "automatica, sin interaccion directa de un usuario": si el proceso esta dormido durante la demo, el repositorio no aparece. Un snapshot tardio sigue siendo correcto (until historico), pero un informe que no se envia o un mapeo que no se procesa son fallos visibles.
- **Opciones:**
  - Pinger externo cada 5 min (UptimeRobot, cron-job.org) para mantener despierta la instancia
  - Scheduler externo (cron-job.org, GitHub Actions schedule) que llama a /jobs/run con secreto
  - Plan pago sin sleep
  - Worker en otro proveedor que no duerme (VPS / Oracle Cloud Free)
  - Aceptar la latencia y documentarla
- **Estudio de APIs:** §7.5 pide que los jobs "no dependan de que el proceso este vivo a la hora exacta"; §12 lista los crons; no menciona el sleep del hosting.
- **Fusiona:** P722

### Q-infraestructura-16 — ¿Se usa una cola con Redis (BullMQ / Celery), que exige un servicio Redis adicional (Upstash free 10k comandos/dia, Render Redis free efimero), una cola respaldada en la propia base de datos (pg-boss, Solid Queue, django-q2, tabla jobs + SELECT ... FOR UPDATE SKIP LOCKED), o ninguna cola formal (cron en proceso que barre tablas de estado, patron outbox)?

- **Requisitos:** R2.3.10, R2.4.5, R2.6.7
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Cada servicio extra en free tier es un punto de fallo y una cuenta mas; la eleccion fija como se implementan locks, reintentos, idempotencia y el panel de estado de jobs.
- **Opciones:**
  - BullMQ/Celery + Redis externo
  - Cola en Postgres (pg-boss, Solid Queue, django-q2)
  - Cron en proceso + tablas de estado (sin cola)
- **Estudio de APIs:** §12 propone "Redis para la cola" con BullMQ/Celery; §9.4 propone una tabla notification_outbox.
- **Fusiona:** P724

### Q-infraestructura-17 — ¿El scheduler y los workers corren dentro del mismo proceso web (un solo servicio gratuito, con riesgo de bloquear requests y de doble ejecucion si el PaaS levanta dos instancias durante un rolling deploy) o como servicio aparte (el background worker es pago en Render)? Si es un solo proceso, ¿como se garantiza un unico lider de cron (lock en base de datos, PID file, variable de entorno)? ¿Donde se cachea el installation token de GitHub (memoria del proceso vs base de datos/Redis) si hay mas de una instancia?

- **Requisitos:** R2.3.10, R2.4.5, R2.5.1
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** La doble ejecucion del aprovisionamiento crea repositorios o mensajes duplicados y el informe diario podria enviarse dos veces. Afecta costo y arquitectura.
- **Opciones:**
  - Todo en el proceso web con eleccion de lider por lock en base de datos
  - Servicio de worker separado (pago o en otro proveedor)
  - Scheduler externo que dispara endpoints (sin cron interno)
  - Token de instalacion cacheado en memoria / en base de datos / en Redis
- **Estudio de APIs:** §12 separa "Web App" y "Workers" como cajas distintas; §2.2 dice "cacheenlo con TTL de ~50 min" sin indicar donde.
- **Fusiona:** P725

### Q-infraestructura-18 — ¿Como se implementa el "lock por sujeto" del worker de creacion de repositorios y del job de snapshot (advisory lock de Postgres, SELECT FOR UPDATE SKIP LOCKED, lock en Redis, columna locked_until)? Si un job muere a mitad por reinicio del proceso, ¿en cuanto expira el lock, quien lo retoma, cuantos reintentos hay antes de pasar a ERROR definitivo y como se refleja esa maquina de estados en la pantalla exigida por R2.3.11?

- **Requisitos:** R2.3.7, R2.3.10, R2.3.11, R2.4.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Sin expiracion, un reinicio deja sujetos bloqueados para siempre ("atascado"); sin lock, dos workers crean el mismo repositorio. Define la maquina de estados que la UI muestra.
- **Opciones:**
  - Advisory locks de Postgres
  - SELECT ... FOR UPDATE SKIP LOCKED sobre tabla de jobs
  - Lock distribuido en Redis con TTL
  - Columna locked_until con expiracion y barrido periodico
- **Estudio de APIs:** §5.5 exige que el worker sea "idempotente, con lock por sujeto", sin especificar mecanismo ni expiracion.
- **Fusiona:** P726

### Q-infraestructura-19 — GitHub exige respuesta al webhook en 10 s y no reintenta automaticamente las entregas fallidas de una GitHub App (solo redelivery manual o via API). Con arranque en frio de 30-60 s en una instancia dormida, ¿se acepta perder webhooks y depender del reconciliador cada 15 min, se implementa redelivery automatico (GET /app/hook/deliveries + POST .../attempts), o el diseño final es "solo polling" y los webhooks son un plus?

- **Requisitos:** R2.5.1, R2.5.2, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la latencia real "push en GitHub → visible en dashboard", el volumen de llamadas del reconciliador (rate limit) y que se promete en el spec como comportamiento observable.
- **Opciones:**
  - Webhooks + reconciliador cada 15 min (aceptar perdidas)
  - Webhooks + redelivery automatico por API
  - Solo polling incremental (sin webhooks)
  - Webhooks solo en produccion pagada sin sleep
- **Estudio de APIs:** §8.1 propone webhooks con "202 en <10 s"; §8.2 un reconciliador cada 15 min con ETag; no trata cold start ni redelivery.
- **Fusiona:** P723

### Q-infraestructura-20 — ¿El endpoint /webhooks/github valida X-Hub-Signature-256 con el body crudo y comparacion en tiempo constante, rechaza con 401 si no hay firma, guarda X-GitHub-Delivery para descartar duplicados, limita el tamaño del body, maneja que el payload de push trae como maximo 20 commits (¿fetch adicional de los restantes?), responde 202 y encola? ¿Esta excluido del middleware de sesion/CSRF? ¿Se persiste el evento crudo para auditoria y por cuanto tiempo? ¿Como y cuando se rota el webhook secret?

- **Requisitos:** R2.5.2, R2.5.10
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Es el unico endpoint publico sin autenticacion de usuario; un payload forjado podria inflar la actividad de un repositorio (R2.5.4) o saturar la cola.
- **Opciones:**
  - Validacion de firma + deduplicacion por delivery id + persistencia del crudo con retencion definida
  - Validacion de firma sin persistir el evento crudo
  - Rotacion programada del webhook secret / rotacion solo ante incidente
- **Estudio de APIs:** §8.1 muestra verifySignature con timingSafeEqual sobre el body crudo y "202 en <10 s"; no cubre duplicados, tamaño maximo ni rotacion del secret.
- **Fusiona:** P739

## 4. Repositorios generados: identidad, visibilidad y proteccion

### Q-infraestructura-21 — ¿Que identidad de committer/author llevan los commits que la aplicacion hace al repositorio base (PUT /contents) y los tags: el nombre y correo de un bot del curso, la identidad <app>[bot], o el profesor? ¿Los repositorios base y de estudiantes se crean privados por defecto (sin opcion) o el profesor puede elegir la visibilidad? ¿Quien queda como admin del repositorio (solo la App y los owners de la organizacion)?

- **Requisitos:** R2.3.6, R2.3.7, R2.4.5
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Define el aspecto del historial de Git que veran estudiantes y correctores, y la superficie de permisos (evitar dar admin a estudiantes).
- **Opciones:**
  - Committer con identidad de bot del curso ("ICC4201 Bot")
  - Identidad <app>[bot] de la GitHub App
  - Identidad del profesor vinculado
  - Repos siempre privados / visibilidad elegible por el profesor
- **Estudio de APIs:** §5.3 ejemplifica el committer "ICC4201 Bot"; §14 indica "creenlos privados"; §5.4 "usen push, nunca admin".
- **Fusiona:** P745

### Q-infraestructura-22 — Verificar en una organizacion con plan Free si los rulesets de tags (POST /orgs/{org}/rulesets, target tag) y la proteccion de ramas estan disponibles en repositorios privados, o si requieren plan Team. Si no estan disponibles, ¿se aceptan tags borrables (con el SHA en la base de datos como unica verdad) o se hacen los repositorios publicos?

- **Requisitos:** R2.4.5, R2.4.7
- **Tipo:** verificar_empiricamente · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El estudio propone la ruleset como "blindaje extra"; si el plan no lo permite, el spec debe declarar explicitamente que la evidencia de entrega es solo la base de datos y su respaldo.
- **Opciones:**
  - Rulesets disponibles: se protegen los tags
  - Tags borrables, SHA en base de datos como unica verdad
  - Repositorios publicos para habilitar la proteccion
  - Plan Team (via GitHub Education) para habilitar rulesets en privados
- **Estudio de APIs:** §7.5 "Protejan los tags... ruleset de tags en la org. No es imprescindible si el SHA esta en su BD".
- **Fusiona:** P735

## 5. Secretos, cifrado y entornos

### Q-infraestructura-23 — ¿Donde viven los secretos (.pem de la GitHub App, client_id/secret de Canvas, client secret de Google, webhook secret, clave de cifrado de tokens, credenciales de email, DATABASE_URL): variables de entorno del PaaS, gestor de secretos, archivo .env cifrado (sops/dotenv-vault)? ¿Como se comparten entre integrantes (gestor de contraseñas compartido) y quien tiene acceso a produccion? ¿Se incluye .env.example, pre-commit con gitleaks y escaneo de secretos en CI? Como el codigo se entrega por GitHub, ¿se rotan todos los secretos tras el 6-oct, y que se hace si uno se commitea por error (rotar + reescribir historia)?

- **Requisitos:** R2.1.4, R2.1.5, R2.5.2, Seccion 3.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Un .pem o un client_secret en el historial del repositorio entregado es un hallazgo evidente en la correccion y un riesgo real sobre la organizacion de GitHub y el curso de Canvas.
- **Opciones:**
  - Variables de entorno del PaaS + gestor de contraseñas compartido
  - Gestor de secretos externo (Doppler, Infisical, 1Password, Vault)
  - Archivo .env cifrado versionado (sops / dotenv-vault)
  - Con o sin escaneo automatico (gitleaks en pre-commit y en CI)
  - Rotacion completa tras la entrega del 6-oct / sin rotacion
- **Estudio de APIs:** §14 "Secretos": no van al repositorio, se usan variables de entorno; no cubre comparticion ni rotacion.
- **Fusiona:** P727

### Q-infraestructura-24 — ¿Los refresh/access tokens de Canvas se cifran en la base de datos (AES-256-GCM con clave en variable de entorno, cifrado de columna del ORM) o se guardan en claro? ¿Donde vive la clave, que pasa si se pierde (¿todos los profesores deben reautorizar?) y se soporta rotacion (version de clave por registro)? ¿La clave privada de la GitHub App se inyecta como variable de entorno multilinea o en base64?

- **Requisitos:** R2.1.4, R2.4.5, R2.6.1, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** El token del profesor permite publicar notas y mensajes a estudiantes; su filtracion desde un dump de una base de datos gratuita es el peor escenario de seguridad del proyecto.
- **Opciones:**
  - Cifrado a nivel de aplicacion (AES-256-GCM) con clave en variable de entorno
  - Cifrado de columna provisto por el ORM o por el motor
  - Tokens en claro, documentando el riesgo asumido
  - Con o sin version de clave por registro para permitir rotacion
  - .pem inyectado multilinea / en base64
- **Estudio de APIs:** §1.1 indica "Guarda el refresh_token cifrado en BD"; no especifica mecanismo ni gestion de la clave.
- **Fusiona:** P728

### Q-infraestructura-25 — ¿Cuantos entornos existen (local por desarrollador, staging, produccion) y con que datos? ¿Como se garantiza que dev y staging NUNCA envien Conversations, anuncios, comentarios o correos a personas reales ni creen repositorios en la organizacion real: modo dry-run/sandbox por variable de entorno, allowlist de destinatarios, organizacion de GitHub y curso de Canvas distintos por entorno, interruptor global de comunicaciones salientes en produccion para operaciones? ¿Cada desarrollador tiene su propia base de datos local o comparten una?

- **Requisitos:** R2.3.7, R2.6.5, R2.6.6, R2.7.6
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Un job de prueba apuntando al curso real enviaria mensajes o publicaria notas a estudiantes verdaderos; es irreversible y visible para el profesor del curso.
- **Opciones:**
  - Solo local + produccion
  - Local + staging + produccion, con organizacion y curso propios por entorno
  - Modo dry-run por variable de entorno (no se llama a las APIs de escritura)
  - Allowlist de destinatarios en entornos no productivos
  - Interruptor global de comunicaciones salientes operable en produccion
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P733

## 6. Envio de correo del informe diario

### Q-infraestructura-26 — ¿Que proveedor de email se usa y con que limites (Resend 100/dia y exige dominio verificado para enviar a terceros; Brevo 300/dia; Mailgun; SendGrid; SMTP de Gmail con App Password y 2FA, ~500/dia)? ¿Dispone el equipo de un dominio propio para verificar como remitente, dado que varios proveedores solo permiten enviar a la direccion del propietario mientras no haya dominio verificado? Sin dominio propio, ¿se acepta enviar desde una cuenta Gmail del equipo? ¿Que remitente y nombre visibles se usan ("ICC4201 Bot <...>")? ¿El correo se envia en HTML + texto plano? ¿Como se demuestra el envio si el correo cae en spam (registro de envios con sent_at/status + informe accesible por URL)?

- **Requisitos:** R2.6.1, R2.6.3, R2.6.4
- **Tipo:** dependencia_externa · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** R2.6.4 depende de un tercero con cuotas; sin dominio verificado varios proveedores no entregan a destinatarios arbitrarios. Condiciona la deliverability, la direccion From posible, si el informe llega a las cuentas de los correctores durante la revision y el plan para demostrar el envio.
- **Opciones:**
  - Gmail SMTP con App Password
  - SendGrid plan gratuito
  - Resend plan gratuito
  - Mailgun
  - Brevo
  - SMTP institucional
- **Estudio de APIs:** §9.1 sugiere SendGrid/Resend/Mailgun/SMTP de Gmail sin elegir ni comparar limites, y recomienda guardar registro de envios y publicar el informe como pagina web.
- **Fusiona:** P744, P748

### Q-infraestructura-27 — ¿Tiene el equipo acceso a los registros DNS de un dominio para configurar SPF, DKIM y DMARC del remitente? Si no, ¿se acepta el riesgo de que el informe caiga en spam en las cuentas de los correctores y se mitiga con la version web del informe dentro de la aplicacion y una nota en la documentacion?

- **Requisitos:** R2.6.4
- **Tipo:** dependencia_externa · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define si "el correo llego a la bandeja de entrada" es un criterio de aceptacion verificable o una limitacion documentada.
- **Opciones:**
  - Dominio propio con SPF/DKIM/DMARC configurados
  - Sin dominio: se asume el riesgo de spam y se documenta
  - Sin dominio: se mitiga con version web del informe accesible por URL
- **Estudio de APIs:** §9.1 anticipa que el correo puede "caer en spam" y recomienda la version web como respaldo; no aborda SPF/DKIM/DMARC.
- **Fusiona:** P749

### Q-infraestructura-28 — ¿Cual es el volumen estimado de correos por dia (cursos activos x suscritos + envios de prueba) y cabe en el plan gratuito elegido? ¿El plan gratuito sigue vigente sin tarjeta y sin expiracion de trial durante las dos semanas posteriores al 6-oct (Seccion 3.2)? ¿Que hace la aplicacion al agotar la cuota diaria: encola para el dia siguiente, descarta, avisa en la interfaz?

- **Requisitos:** R2.6.4
- **Tipo:** investigable_en_docs · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define la politica ante cuota agotada y protege la disponibilidad exigida tras la entrega final.
- **Opciones:**
  - Encolar y reintentar al dia siguiente
  - Descartar el envio y registrar el fallo
  - Avisar en la interfaz y exponer el informe solo por web
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P750

## 7. Despliegue, migraciones y control de versiones

### Q-infraestructura-29 — ¿Que herramienta de migraciones de esquema se usa (Prisma, Drizzle, Knex, Alembic, migraciones de Django/Rails) y las migraciones corren automaticamente en cada deploy o a mano? ¿Cual es la politica ante una migracion fallida (rollback vs forward-fix)? ¿Se permiten migraciones destructivas despues del 16-sep sobre la base de produccion que ya contiene los datos de la demo, es decir, la base de la parcial debe sobrevivir hasta la final?

- **Requisitos:** R2.4.7, Seccion 3.1, Seccion 3.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Un deploy con una migracion rota deja la app caida frente a los evaluadores; sin politica, cada integrante migra de forma distinta. Define ademas si la base de la demo parcial sobrevive hasta la final.
- **Opciones:**
  - Migraciones automaticas en cada deploy
  - Migraciones ejecutadas manualmente por un responsable
  - Politica de rollback / politica de forward-fix
  - Se permite recrear la base entre parcial y final / la base debe persistir
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P720

### Q-infraestructura-30 — ¿El deploy se hace con Dockerfile (mismo artefacto en local y produccion) o con buildpacks nativos del PaaS? ¿Como se hace rollback: redeploy del commit anterior (¿y las migraciones ya aplicadas?), o imagen/version previa? ¿Cuanto tarda un deploy y como se evita perder jobs en curso durante el reinicio (graceful shutdown, jobs reanudables por estado persistido)? ¿Se fijan las versiones de runtime (Node/Python) y los lockfiles?

- **Requisitos:** R2.3.10, R2.4.5, Seccion 3.2
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** si
- **Por que importa:** Un reinicio a mitad de la creacion de 20 repositorios debe reanudarse sin duplicar; el rollback debe estar definido antes de necesitarlo frente a los evaluadores.
- **Opciones:**
  - Dockerfile propio (mismo artefacto en local y produccion)
  - Buildpacks nativos del proveedor
  - Rollback por redeploy del commit anterior
  - Rollback por imagen/version previa etiquetada
  - Con o sin graceful shutdown y reanudacion de jobs por estado persistido
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P746

### Q-infraestructura-31 — ¿Se fija explicitamente la version de la API de GitHub (header X-GitHub-Api-Version, hoy 2026-03-10) en todas las llamadas, y que politica se adopta ante avisos de deprecacion o cambios de Canvas y GitHub entre el 9-sep y el 20-oct: quien revisa los changelogs y con que frecuencia, se permite actualizar dependencias o la version de API despues del congelamiento de codigo del 6-oct, y con que procedimiento (hotfix, redeploy, aviso a los revisores)? ¿Todas las dependencias quedan fijadas con lockfile y version exacta, incluidas las que se instalan en el build del proveedor de hosting, para que un redeploy durante las dos semanas posteriores produzca exactamente el mismo artefacto?

- **Requisitos:** Seccion 3.2, Seccion 4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** El enunciado obliga a mantener la app utilizable al menos dos semanas despues del 6-oct, cuando el codigo ya esta entregado. Un redeploy que resuelva versiones nuevas, o una deprecacion no vista, puede romper la app justo mientras la evaluan, sin que el equipo pueda modificar el codigo entregado.
- **Opciones:**
  - Version de API fijada por header en todas las llamadas / se acepta la version por defecto
  - Revision de changelogs con responsable y frecuencia definidos / sin revision
  - Congelamiento total de dependencias tras el 6-oct (solo hotfix documentado y avisado)
  - Se permiten actualizaciones de seguridad con redeploy y aviso a los revisores
  - Lockfile y versiones exactas fijadas tambien en el build del proveedor / build sin fijar
- **Estudio de APIs:** §2 y §15 usan la version 2026-03-10 de la API de GitHub y advierten sobre cambios en la documentacion de Canvas, pero no fijan politica de deprecaciones ni de congelamiento de dependencias.
- **Fusiona:** N015

## 8. Operacion, observabilidad, almacenamiento y recuperacion

### Q-infraestructura-32 — ¿Se usan logs estructurados (JSON) con correlation id por request y por job, sin tokens ni datos personales de estudiantes? ¿La retencion del PaaS (Render free ~7 dias) basta o se envian a un servicio gratuito (Better Stack, Axiom, Papertrail)? ¿Se usa Sentry/GlitchTip free para excepciones con alertas? ¿Habra una pantalla de administracion de jobs (ultima ejecucion, duracion, fallos, proxima ejecucion, boton "ejecutar ahora") visible en la demo para evidenciar que el proceso automatico corre?

- **Requisitos:** R2.3.10, R2.3.11, R2.6.4
- **Tipo:** decision_equipo · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Sin observabilidad no se puede diagnosticar por que un repositorio no se creo ni demostrar que el informe diario salio; la pantalla de jobs es ademas evidencia para la correccion.
- **Opciones:**
  - Logs estructurados JSON con correlation id / logs de texto plano del PaaS
  - Retencion solo del PaaS / envio a un agregador externo gratuito
  - Sentry/GlitchTip para excepciones / sin captura de excepciones
  - Con o sin pantalla de administracion de jobs con ejecucion manual
- **Estudio de APIs:** §9.1 propone un registro de envios (sent_at, status) y §7.4 mostrar la "ultima sincronizacion" en la UI; no cubre logging ni alertas.
- **Fusiona:** P740

### Q-infraestructura-33 — ¿Existe un endpoint /health que verifique la base de datos (y opcionalmente la conectividad a Canvas y GitHub) y un monitor externo gratuito (UptimeRobot, Better Uptime) con alerta a Telegram/WhatsApp/email del equipo? ¿Quien esta "de turno" entre el 6 y el 20 de octubre, con que tiempo maximo de respuesta, y como se comunica una caida al profesor y a los ayudantes que estan corrigiendo?

- **Requisitos:** Seccion 3.2 (disponible al menos dos semanas)
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** "Las funcionalidades a las que no se puede acceder no se consideran cumplidas": una caida no detectada durante la correccion equivale a funcionalidad inexistente.
- **Opciones:**
  - /health con verificacion de base de datos + monitor externo con alertas
  - /health sin monitor externo
  - Turnos asignados por dias entre los integrantes, con tiempo de respuesta comprometido
  - Sin turnos: revision oportunista y canal de contacto publicado
- **Estudio de APIs:** §12 recuerda la exigencia de dos semanas de disponibilidad; no propone monitoreo.
- **Fusiona:** P741

### Q-infraestructura-34 — Confirmar en la documentacion del proveedor de base de datos gratuito elegido: Render Free Postgres expira y se borra a los 30 dias; Supabase pausa proyectos tras 7 dias sin actividad; Neon autosuspende con latencia de arranque en la primera consulta (¿afecta la "inmediatez" exigida por R2.5.1?); limites de almacenamiento (~0,5 GB) y de conexiones simultaneas. ¿La ventana 10-sep → 20-oct cabe dentro de esas condiciones y que medida se toma si no cabe?

- **Requisitos:** R2.5.1, Seccion 3.2
- **Tipo:** investigable_en_docs · **Entrega:** ambas · **Bloquea la parcial:** no
- **Por que importa:** Una base que expira el 10-oct borra todo a mitad de la correccion; la latencia de reanudacion puede hacer que el dashboard tarde segundos frente al evaluador.
- **Opciones:**
  - El plan gratuito cubre la ventana completa: se documenta la evidencia
  - No la cubre: se migra a otro proveedor gratuito
  - No la cubre: se paga el plan minimo que la cubra
  - Se mantiene actividad artificial para evitar pausas por inactividad
- **Estudio de APIs:** No lo aborda.
- **Fusiona:** P743

### Q-infraestructura-35 — Si el SHA de cada entrega vive solo en la base de datos, perder la base destruye la evidencia de que corregir. ¿El plan gratuito elegido incluye backups automaticos (Neon/Supabase/Render free no incluyen PITR)? ¿Se agrega un pg_dump diario via GitHub Actions hacia un almacenamiento privado (cifrado, ¿donde?) y se prueba una restauracion completa antes del 6-oct? ¿El tag en GitHub se considera respaldo oficial del SHA?

- **Requisitos:** R2.4.5, R2.4.7, R2.7.4
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Define el requisito de durabilidad de R2.4.7 en terminos operativos y que se responde el 7-oct a "¿y si pierden la base de datos?".
- **Opciones:**
  - Backups automaticos del proveedor (si el plan los incluye)
  - pg_dump diario via GitHub Actions a almacenamiento privado cifrado
  - Sin respaldo propio: el tag en GitHub es la evidencia secundaria
  - Con o sin prueba de restauracion completa ejecutada antes del 6-oct
- **Estudio de APIs:** §7.5 afirma "SHA en BD = verdad; un tag se puede borrar, una fila en su BD no"; no cubre backups de la base de datos.
- **Fusiona:** P742

### Q-infraestructura-36 — ¿Donde se almacenan fisicamente los artefactos y datos crudos que el diseño podria requerir, sabiendo que el sistema de archivos de los PaaS gratuitos es efimero y que la base de datos gratuita ronda 0,5 GB? Artefactos candidatos: zip/tarball del snapshot como respaldo del SHA, payloads crudos de webhooks para reprocesar, JSON crudo de objetos de Canvas para depurar y recalcular, HTML de cada informe diario generado, archivos que el profesor sube para el repositorio base, adjuntos y cuerpos renderizados del log de comunicaciones. Decidir por cada uno: si se guarda o no, donde (columna bytea/JSONB en la base, servicio de objetos externo con plan gratuito, no se guarda), cuota estimada para el curso demo y para un curso de 60 repositorios, politica de poda (retencion en dias, poda automatica por job) y que pasa cuando se alcanza el limite de almacenamiento del plan (¿la app deja de ingerir commits, deja de guardar crudos, o cae?). ¿Se incluye este almacenamiento en el respaldo y en la prueba de restauracion?

- **Requisitos:** R2.4.5, R2.4.7, R2.5.2, R2.6.1
- **Tipo:** decision_equipo · **Entrega:** final · **Bloquea la parcial:** no
- **Por que importa:** Varias decisiones de robustez ya planteadas (respaldo del snapshot, reprocesar atribucion, historial de informes) presuponen almacenamiento que nadie ha dimensionado; si no cabe en el plan gratuito, esas decisiones deben cambiar antes de escribir el spec, no cuando la base se llene durante las dos semanas posteriores al 6-oct.
- **Opciones:**
  - No guardar crudos ni zips: solo datos normalizados
  - Crudos en JSONB en la base de datos con retencion corta y poda automatica
  - Artefactos en un servicio de objetos externo con plan gratuito
  - Guardar solo lo minimo para auditoria (SHA, ids externos) y regenerar todo bajo demanda
- **Estudio de APIs:** §12 solo nombra Postgres y Redis en la arquitectura y §8.1 recomienda procesar webhooks en background; el estudio no aborda donde persistir artefactos binarios ni datos crudos, ni su cuota o poda.
- **Fusiona:** N040

## Ya respondidas por el enunciado

Ninguna de las 48 preguntas de entrada del area infraestructura quedo marcada como YA_RESPONDIDA en la etapa de verificacion: las 46 preguntas del archivo de consolidacion y las 2 preguntas de la ronda critica (N015 y N040) fueron veredicto ABIERTA o ABIERTA/BLOQUEA. Los veredictos dejan constancia de que el enunciado solo aporta marco parcial y no respuesta, en particular:

- Seccion 4: "No hay restricciones en el uso de lenguaje, frameworks o librerias mientras estas sean de uso libre y gratuito" — enmarca pero no resuelve el stack, el proveedor de hosting, el presupuesto ni el congelamiento de dependencias.
- Seccion 3.2: "una URL donde su aplicacion debera estar disponible ... al menos por las siguientes dos semanas" — impone la exigencia de disponibilidad pero no nombra proveedor, plan, dominio ni responsable.
- R2.1.4 / R2.1.5 / R2.1.6: exigen vincular el curso con Canvas y con una organizacion de GitHub y verificar la vinculacion, sin identificar instancia, organizacion, credenciales ni custodios.
- R2.3.10: exige creacion "de forma automatica, sin interaccion directa de un usuario", sin decidir scheduler, cola ni topologia de procesos.
- R2.4.5 / R2.4.7: exigen registrar la version del repositorio a la fecha de cierre y "mantener correctamente las versiones ya registradas", sin fijar medio, formato, respaldo ni almacenamiento.
