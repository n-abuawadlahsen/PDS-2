# Configuración, acceso y personas (P1–P6)

Revisión realizada contra las rutas de `backend/app/api/rutas/{auth,perfil,cursos,vinculacion,verificacion,personas,pendientes,comunicaciones}.py`. Se completaron los contratos que impedían los flujos de esta área, usando los modelos existentes. La revisión de octubre está en [LIMITACIONES.md](LIMITACIONES.md).

## Pantalla → acción → contrato → permiso

Todas las rutas de esta tabla llevan prefijo `/api`, salvo las rutas `/auth`. `{c}` identifica al curso, `{m}` a la membresía y `{e}` al estudiante.

| Pantalla | Acción y contrato real | Permiso | Implementación |
| --- | --- | --- | --- |
| Acceso / Confirmar | `POST /auth/google/inicio`, `POST /auth/confirmar`; cookie opaca y formulario de navegación | Pública | Conserva destino interno permitido; rechazos de Google y confirmación existente. No guarda credenciales. |
| Perfil | `GET/PATCH/DELETE /perfil`, `GET /perfil/cierre` | Sesión propia | Nombre editable, correo de identidad, cierre confirmado y cursos que bloquean el cierre. |
| Perfil | `GET/DELETE /perfil/sesiones`, `DELETE /perfil/sesiones/{id}`, `GET /perfil/identidades-canvas`, `DELETE .../{id}`, `PUT/DELETE /perfil/cuenta-github` | Sesión propia | Cierre individual/de las demás, identidades Canvas propias con retiro confirmado de credenciales y cuenta docente GitHub. |
| Ajustes | `PATCH /cursos/{c}` | `curso.administrar` | Nombre, zona IANA y umbrales; errores junto al campo, auditoría y recálculo en cola. |
| Cursos | `GET/POST /cursos`, `GET /cursos/{c}/contexto` | Sesión / membresía activa | Curso nuevo y contexto de permisos reales; implementación general en shell/Cursos. |
| Equipo | `GET /cursos/{c}/equipo`, `GET /cursos/{c}/equipo/historial` | `curso.ver` | Lista legible e historial bajo demanda. Todos los profesores tienen nueve permisos. |
| Equipo | `POST/GET /cursos/{c}/equipo/invitaciones`, `POST .../{invitacion}/reenviar`, `DELETE .../{invitacion}` | `equipo.administrar` | Emisión, enlace nominal, estado del correo, reenvío y revocación. Formulario con cinco permisos concedibles, dos implícitos y dos exclusivos de profesor explicados. |
| Equipo | `PATCH /cursos/{c}/miembros/{m}/permisos`, `PATCH .../rol`, `GET .../impacto-retiro`, `POST /cursos/{c}/equipo/{m}/retiro`, `POST .../reincorporacion`, `POST .../github/reintentar` | `equipo.administrar` | Conserva último profesor, calcula repositorios/correcciones afectados; el retiro impide acceso al curso y conserva borradores. Marca la vía compartida. |
| Invitación | `GET /invitaciones/{token}`, `POST .../aceptar` o OAuth con `invitacion_token` | Token nominal / sesión coincidente | Rol, permisos, consentimiento y estados vencido/revocado/aceptado; cambiar cuenta conserva la invitación. |
| Vinculación / Ajustes | `GET /canvas/instancias`, `GET /cursos/{c}/vinculacion/canvas`, `POST .../canvas/cursos-disponibles`, `POST .../canvas` | Escritura `curso.administrar` | Credencial propia con consentimientos. Renueva el vínculo propio por UUID; otros cursos ocupados quedan deshabilitados. Token descartado al vincular o fallar. |
| Vinculación / Ajustes | `GET /cursos/{c}/vinculacion/github`, `POST .../github/iniciar`, `GET .../github/huerfanas`, `POST .../github/huerfanas/adoptar`, `POST /vinculacion/github/callback` | `curso.administrar` / callback con sesión | GitHub App, retorno validado, instalación existente y adopción con confirmación escrita. No hay token personal GitHub. |
| Verificación | `GET /cursos/{c}/verificacion/ultima`, `POST .../verificacion`, `GET .../verificacion/{ejecucion}`, `GET .../{ejecucion}/estado`, `POST .../items/{item}` | Lectura `curso.ver`, escritura `curso.administrar` | 19 comprobaciones, sondeo cada 2 segundos, estado/intentos/próximo reintento del trabajo. ID de ejecución en URL; los fallos no convierten pendientes en correctos. |
| Verificación | `POST .../items/14/firmar`, `POST .../items/5-bis`, `POST .../items/17-bis` | `curso.administrar` | Firma manual separada y dos pruebas de escritura con consentimiento explícito. |
| Personas | `GET /cursos/{c}/personas` | `curso.ver` | Espejo completo (sin paginación de servidor), paginación local de 20 filas, filtros en URL, secciones/grupos y sello de sincronización. Mantiene enmascarado del servidor. |
| Personas | `POST /cursos/{c}/sincronizaciones`, `POST .../registro-github`, `POST .../registro-github/restaurar`, `GET .../trabajos/{id}` | Sincronizar `curso.ver`; registro `comunicacion.enviar` | IDs consultables en URL y estado real de cada trabajo, incluido el registro en cola; no anuncia publicación anticipada. |
| Personas | `POST /cursos/{c}/personas/{e}/mapeo`, `POST .../mapeo/importar-csv` | `mapeo.editar` | Validación docente y archivo/textarea CSV, previsualización fila a fila y aplicación de la revisión vigente. Cambiar el CSV invalida la revisión. |
| Personas | `GET /cursos/{c}/personas/{e}/mapeo/historial` | `curso.ver` | Historial bajo demanda por IDs estables y fecha, sin evidencia sensible del proveedor. |
| Pendientes | `GET /cursos/{c}/pendientes`, `POST .../pendientes/{e}/recordatorio` | Lectura `curso.ver`, envío `comunicacion.enviar` | Cuatro grupos, causa y persona por ID; último/próximo envío y `Retry-After` en `429`. |
| Personas | `GET/PUT /cursos/{c}/comunicaciones-curso/recordatorio-mapeo` | Lectura `curso.ver`, cambio `comunicacion.enviar` | Regla automática, vista previa, carga/error recuperable, permiso explícito y bloqueo de doble envío. Respeta capacidad `comunicaciones_automaticas`. |

## Trazabilidad del enunciado

| Requisito | Entrada y evidencia funcional |
| --- | --- |
| R2.1.1 | Acceso Google, Perfil, Equipo, invitación nominal, roles/retiro/reincorporación. |
| R2.1.2 | Registro/inicio mediante Google. Gmail personal admitido; diferencia institucional existente consignada abajo. |
| R2.1.3 | Cursos → Crear curso → Vinculación; Ajustes edita nombre, zona horaria y umbrales. |
| R2.1.4 | Vinculación Canvas → credencial propia → buscar cursos → seleccionar → verificación. |
| R2.1.5 | Vinculación GitHub → instalación App → callback → verificación. |
| R2.1.6 | Ayuda de token, consentimientos, progreso persistido y checklist con motivos/pruebas explícitas. |
| R2.1.7 | Equipo → Incorporar integrante → Profesor / Cambiar rol. Guarda del último profesor. |
| R2.1.8 | Equipo → Ayudante → cinco permisos individuales más dos implícitos/no concedibles explicados. |
| R2.1.9 | Equipo → Retirar → consultar impacto → confirmar; revocación GitHub queda en trabajo de backend. |
| R2.2.1 | Personas → espejo, estado de matrícula, sincronización, sello de antigüedad. |
| R2.2.2 | Personas → sección del estudiante y filtros. |
| R2.2.3 | Personas → grupos/conjunto/integrantes de Canvas; sin edición local de Canvas. |
| R2.2.4 | Personas → registro en Canvas, edición docente o CSV. |
| R2.2.5 | Pendientes → persona seleccionada → validar cuenta / enviar recordatorio. El backend reanuda la creación progresiva. |
| R2.2.6 | Pendientes → sin cuenta, conflicto, grupo incompleto o invitación pendiente con causa/acción. |

## Límites que siguen vigentes

La política vigente admite Gmail personal y `miuandes.cl`. Se mantiene esa decisión del proyecto. No están implementados la configuración de roles Canvas adicionales, archivado del curso completo, confirmación de fusiones Canvas ni reenvío manual directo de invitaciones de estudiantes; sus alcances concretos están en [LIMITACIONES.md](LIMITACIONES.md).

Las restricciones anteriores de renovación Canvas, ajustes generales, sesiones/identidades, historial, permisos, cooldown, impacto del retiro, vía compartida y estado de trabajos quedaron corregidas. Las pruebas de esta área usan dobles de proveedores; no certifican OAuth ni envíos externos reales.

## Validación de esta área

Pruebas en `frontend/tests/configuracion.spec.ts`: destino de acceso permitido, los cinco permisos y la guarda del último profesor, historial legible por ayudantes, Pendientes → mapeo actualizado, registro de Canvas con `202`, reanudación del checklist tras recarga y regla automática bloqueada sin permiso. Las pruebas usan dobles HTTP de los esquemas reales, exclusivamente en Playwright. Google/Canvas/GitHub reales no se verificaron con estas pruebas.

Comando normal desde `frontend`: `npm test -- tests/configuracion.spec.ts`. En trabajo paralelo se usó una configuración temporal equivalente en `/tmp/pds2-configuracion.playwright.ts`, puerto 4184, para no disputar el puerto 4173 de la suite general. El resultado final se registra en IMPLEMENTACION.md junto con la verificación global.

Resultado del área: **7/7 pruebas pasaron** en Chromium (3,6 s); ESLint de las nueve pantallas editadas pasó. Capturas inspeccionadas: `evidencias/configuracion-portatil.png` (1366×768), `evidencias/personas-movil-detalle.png` (390×844) y `evidencias/pendientes-movil.png` (360×844). La comprobación de anchura de Personas a 390 y 360 px no detectó desborde de documento; la tabla conserva desplazamiento dentro de su región. El recorrido de capturas no produjo `pageerror`. Datos exclusivamente sintéticos; no hay tokens en las imágenes.
