# Correcciones de integración de la parcial

## Qué cambia

### Acceso cuando Render está inactivo

El formulario de acceso ahora espera una respuesta JSON válida de `GET /api/salud` antes de navegar. La espera admite HTML de arranque, errores temporales y timeouts: reintenta durante un máximo de dos minutos y después ofrece volver a intentar. No se hace `fetch` a Google: el acceso, la confirmación y las invitaciones conservan sus formularios de navegación **POST**, sus campos ocultos y las cookies existentes.

Las capturas mostraban `/auth/google/inicio` seguido de `Method Not Allowed`. El backend solo aceptaba POST en esa ruta; una recarga como GET después de la página de arranque produce exactamente ese 405. No se capturó el tráfico de aquella sesión, por lo que la transformación del método es el diagnóstico compatible con la evidencia, no una traza de producción. Render documenta que muestra una página de carga durante el despertar del servicio gratuito: [documentación oficial](https://render.com/docs/free#spinning-down-on-idle).

También se añadieron rutas GET de recuperación para `/auth/google/inicio` y `/auth/confirmar`: devuelven a Acceso con una explicación. Esas rutas no inician OAuth ni aceptan confirmaciones por GET. Si el navegador ya había perdido el cuerpo de una invitación, hay que abrir nuevamente su enlace; la espera previa evita ese caso en el recorrido normal.

No cambia `frontend/vercel.json`: `/api/salud` utiliza el proxy existente. No hace falta un servicio de pings para corregir este error.

### Invitaciones al equipo docente

- El listado se obtiene del backend y persiste entre visitas.
- Crear una invitación también encola el correo en `mensaje_saliente`, en la misma transacción.
- La pantalla permite copiar el enlace, consultar el estado del correo, revocar y reenviar.
- Reenviar revoca el enlace anterior y genera uno nuevo. Se conserva el máximo de tres reenvíos por dirección y curso.
- Se limitan a 20 invitaciones pendientes por curso y 50 emisiones por usuario en 24 horas.
- El envío se ejecuta desde `despachar_outbox`; no depende de mantener abierta la página.
- Hay un límite global de diez correos de invitación por día UTC. Al agotarse, se difiere al día siguiente y se abre una incidencia. Los reintentos no reservan otra plaza para el mismo mensaje.
- El correo usa texto y HTML, un timeout de 20 segundos e idempotencia del proveedor. Hay hasta seis intentos ante fallos temporales; los rechazos permanentes quedan visibles y el enlace sigue siendo utilizable.
- Una invitación revocada, aceptada o vencida no se envía si aún estaba pendiente.
- `ENVIADO` significa que el proveedor aceptó el mensaje; no certifica llegada a Recibidos ni lectura.

La tabla de invitaciones conserva únicamente el hash del token. Para poder despacharlo y copiarlo después, el outbox conserva una copia **cifrada con el llavero versionado existente y asociada al curso**. El adaptador de correo no registra el enlace ni el cuerpo en logs ni los persiste en campos de cuerpo en claro. El listado exige `equipo.administrar` y se entrega con `Cache-Control: no-store`.

Las invitaciones anteriores a esta corrección no tienen una copia recuperable del token: la interfaz indica usar **Reenviar** para generar un enlace nuevo.

### Cierre de cuenta

`GET /api/perfil/cierre` informa los cursos bloqueantes. `DELETE /api/perfil` vuelve a comprobarlos dentro de la transacción: la consulta previa del navegador no autoriza el cierre por sí sola.

La comprobación cuenta profesores con membresía activa y cuenta activa en cursos `ACTIVO`. El cierre se serializa con los cambios de equipo y la aceptación de invitaciones mediante un cerrojo transaccional de PostgreSQL. Dos cierres simultáneos no pueden dejar el curso sin profesor. Un rechazo devuelve 409 y los cursos, sin desactivar la cuenta ni revocar sus sesiones.

Cuando procede, se revocan las sesiones, se retiran las membresías y credenciales Canvas, se promueve una credencial de respaldo válida o se degrada la vinculación, se encola la revocación de GitHub y se registra la bitácora. El historial de autoría se conserva.

### Cuenta GitHub docente

Declarar una cuenta comprueba su existencia, consentimiento, identidad numérica y elegibilidad global: no puede estar declarada por otra persona ni tener un mapeo de estudiante vigente en otro curso o en el mismo.

Guardar, retirar o cambiar la cuenta, aceptar una invitación, retirar o reincorporar a un integrante encola la actualización correspondiente. La limpieza conserva la identidad anterior en el trabajo, de modo que borrar el login del perfil no pierda el dato necesario para retirar sus accesos.

El trabajador comprueba el estado actual antes de incorporar; un trabajo atrasado de retiro no debe deshacer una reincorporación. Retira acceso al equipo, colaboraciones directas registradas y membresía de organización cuando la app la dio de alta. Una membresía de organización preexistente se conserva. El barrido horario actualiza estados y Equipo permite solicitar actualización manual.

La columna histórica `usuario.cuenta_github_id` ahora guarda el **ID numérico externo de GitHub**, con índice único; no es el UUID interno de `cuenta_github`. La migración `0002` amplía INTEGER a BIGINT sin borrar datos. Los perfiles antiguos se validan y completan al sincronizarse.

### Permisos y alcance

Se corrigió la referencia de P6 en el plan: crear/publicar la tarea de registro usa `curso.administrar`, como el backend y el capítulo 7 del SPEC. No se cambió este permiso a uno concedible a ayudantes. Las funciones de la entrega final siguen fuera del alcance.

## Correo real: configuración pendiente del despliegue

La integración implementada usa **Resend por HTTPS**: [envío](https://resend.com/docs/api-reference/emails/send-email) e [idempotencia](https://resend.com/docs/dashboard/emails/idempotency-keys). No se crea una cuenta en ese proveedor ni se modifica DNS desde este trabajo.

En el entorno del backend/trabajador de Render:

| Variable | Valor requerido |
| --- | --- |
| `ENTORNO` | `produccion` |
| `EMAIL_PROVEEDOR` | `resend` |
| `EMAIL_PROVIDER_API_KEY` | Clave del proveedor, solo en Render |
| `EMAIL_FROM` | Dirección del dominio verificado |
| `EMAIL_FROM_NOMBRE` | Nombre visible del proyecto |
| `EMAIL_REPLY_TO` | Dirección de respuesta |
| `EMAIL_DOMINIO_VERIFICADO` | Dominio remitente verificado, sin `https://` |
| `COMUNICACIONES_SALIENTES` | `activadas` |
| `DESTINATARIOS_PERMITIDOS` | Vacío, o direcciones habilitadas separadas por comas |

`EMAIL_PROVEEDOR` queda por defecto en `sin_configurar`; ninguna clave existente se interpreta automáticamente como una clave de Resend. Si falta configuración o los envíos están pausados, la invitación sigue disponible para compartir y el correo queda bloqueado con su motivo visible. El trabajador vuelve a evaluar el bloqueo.

Fuera de `produccion`, el adaptador de consola nunca envía correo real y registra solo metadatos sin tokens ni destinatarios. La pantalla distingue explícitamente el envío simulado.

Resend conserva las claves de idempotencia durante 24 horas. Un envío de resultado incierto con más de 23 horas queda en `REQUIERE_ATENCION` para no repetir automáticamente un correo fuera de esa protección. No se promete una garantía distribuida de entrega exactamente una vez ante una caída entre la aceptación remota y el commit local.

## Publicación

Esta corrección requiere actualizar **backend/trabajador y frontend**. Publicar solo Vercel dejaría el frontend llamando rutas que aún no existen en la versión anterior del backend.

1. Publicar la misma revisión en Render. Su trabajador aplica `alembic upgrade head` al arrancar, incluido `0002`, según el arranque ya configurado.
2. Comprobar en `/estado` que la revisión actual y esperada sean `0002`.
3. Publicar el frontend en Vercel, conservando raíz `frontend`, Node 22 y `VITE_API_BASE_URL` vacía/ausente.
4. Configurar el correo si se usará envío real. Compartir enlaces funciona aunque el correo esté pausado.

No se hicieron push, despliegues, envíos reales ni migraciones sobre Supabase desde este trabajo.

## Validación

Resultado local: **266 pruebas de backend y 25 pruebas de frontend aprobadas**, con 97 % de cobertura del dominio. También aprobaron build de TypeScript/Vite, ESLint, Prettier, Ruff, mypy y `alembic check`.

Se usó Python 3.12, una base PostgreSQL local dedicada y respuestas dobles para proveedores. La instalación local disponible es PostgreSQL 14; el CI del repositorio usa PostgreSQL 16. La base de prueba usa colación C como el contenedor del CI; con la colación local `en_US` una prueba existente de orden de nombres de archivos daba un orden diferente.

Se verificó tanto la actualización de `0001` a `0002` como la creación limpia y la ausencia de divergencia entre ORM y migraciones. Las pruebas cubren el cierre concurrente, retiro de credenciales y promoción de respaldo, identidad GitHub y revocación, invitaciones nominales, reenvíos, cuotas y reintentos. El contrato de Resend se prueba interceptando HTTP.

El navegador prueba arranque con HTML/503, espera agotada, conservación del POST y tokens, invitaciones persistentes, rechazo de cierre y los recorridos visuales existentes.

No se verificaron Google OAuth real, correo recibido, DNS del remitente ni permisos de la GitHub App con credenciales reales. Tampoco se indujo un apagado de Render en producción. Estas verificaciones necesitan el despliegue y las cuentas correspondientes; no son comportamientos simulados en la aplicación de producción.
