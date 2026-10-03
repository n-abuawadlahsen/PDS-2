# Configuración, acceso y personas (P1–P6)

Revisión realizada contra las rutas de `backend/app/api/rutas/{auth,perfil,cursos,vinculacion,verificacion,personas,pendientes,comunicaciones}.py`. No se modificó el backend ni se añadieron respuestas ficticias al producto.

## Pantalla → acción → contrato → permiso

Todas las rutas de esta tabla llevan prefijo `/api`, salvo las rutas `/auth`. `{c}` identifica al curso, `{m}` a la membresía y `{e}` al estudiante.

| Pantalla | Acción y contrato real | Permiso | Implementación |
| --- | --- | --- | --- |
| Acceso / Confirmar | `POST /auth/google/inicio`, `POST /auth/confirmar`; cookie opaca y formulario de navegación | Pública | Conserva destino interno permitido; rechazos de Google y confirmación existente. No guarda credenciales. |
| Perfil | `GET/PATCH/DELETE /perfil`, `GET /perfil/cierre` | Sesión propia | Nombre editable, correo de identidad, cierre confirmado y cursos que bloquean el cierre. |
| Perfil | `GET/DELETE /perfil/sesiones`, `PUT/DELETE /perfil/cuenta-github` | Sesión propia | Sesiones abiertas, cerrar las demás, cuenta docente GitHub y consentimiento. |
| Cursos | `GET/POST /cursos`, `GET /cursos/{c}/contexto` | Sesión / membresía activa | Curso nuevo y contexto de permisos reales; implementación general en shell/Cursos. |
| Equipo | `GET /cursos/{c}/equipo`, `GET /cursos/{c}/equipo/historial` | `curso.ver` | Lista legible e historial bajo demanda. Todos los profesores tienen nueve permisos. |
| Equipo | `POST/GET /cursos/{c}/equipo/invitaciones`, `POST .../{invitacion}/reenviar`, `DELETE .../{invitacion}` | `equipo.administrar` | Emisión, enlace nominal, estado del correo, reenvío y revocación. Formulario con cinco permisos concedibles, dos implícitos y dos exclusivos de profesor explicados. |
| Equipo | `PATCH /cursos/{c}/miembros/{m}/permisos`, `PATCH .../rol`, `GET .../impacto-retiro`, `POST /cursos/{c}/equipo/{m}/retiro`, `POST .../reincorporacion`, `POST .../github/reintentar` | `equipo.administrar` | Conserva último profesor, previsualiza sesiones y efectos de retiro, permite reincorporación y reintento de acceso GitHub. |
| Invitación | `GET /invitaciones/{token}`, `POST .../aceptar` o OAuth con `invitacion_token` | Token nominal / sesión coincidente | Rol, permisos, consentimiento y estados vencido/revocado/aceptado; cambiar cuenta conserva la invitación. |
| Vinculación / Ajustes | `GET /canvas/instancias`, `GET /cursos/{c}/vinculacion/canvas`, `POST .../canvas/cursos-disponibles`, `POST .../canvas` | Escritura `curso.administrar` | Credencial propia con consentimientos y selección desde cursos reales. Cursos ocupados visibles y deshabilitados. Token descartado al vincular o fallar. |
| Vinculación / Ajustes | `GET /cursos/{c}/vinculacion/github`, `POST .../github/iniciar`, `GET .../github/huerfanas`, `POST .../github/huerfanas/adoptar`, `POST /vinculacion/github/callback` | `curso.administrar` / callback con sesión | GitHub App, retorno validado, instalación existente y adopción con confirmación escrita. No hay token personal GitHub. |
| Verificación | `GET /cursos/{c}/verificacion/ultima`, `POST .../verificacion`, `GET .../verificacion/{ejecucion}`, `POST .../items/{item}` | Lectura `curso.ver`, escritura `curso.administrar` | 19 comprobaciones agrupadas, fecha y resultado; sondeo cada 2 segundos. ID de ejecución en URL para retomar tras recarga; resultados anteriores no representan comprobaciones pendientes como correctas. |
| Verificación | `POST .../items/14/firmar`, `POST .../items/5-bis`, `POST .../items/17-bis` | `curso.administrar` | Firma manual separada y dos pruebas de escritura con consentimiento explícito. |
| Personas | `GET /cursos/{c}/personas` | `curso.ver` | Espejo completo (sin paginación de servidor), paginación local de 20 filas, filtros en URL, secciones/grupos y sello de sincronización. Mantiene enmascarado del servidor. |
| Personas | `POST /cursos/{c}/sincronizaciones`, `POST .../registro-github`, `POST .../registro-github/restaurar` | **Contrato: `curso.administrar`** | Sincronización encolada y registro confirmado antes de publicar. Un `202` permanece pendiente y se consulta el espejo; nunca anuncia publicación anticipada. |
| Personas | `POST /cursos/{c}/personas/{e}/mapeo`, `POST .../mapeo/importar-csv` | `mapeo.editar` | Validación docente y archivo/textarea CSV, previsualización fila a fila y aplicación de la revisión vigente. Cambiar el CSV invalida la revisión. |
| Pendientes | `GET /cursos/{c}/pendientes`, `POST .../pendientes/{e}/recordatorio` | Lectura `curso.ver`, envío `comunicacion.enviar` | Cuatro grupos de pendientes, causa y enlace a la persona por ID estable. Diferencia envío confirmado / cola y limita repetición tras `429`. |
| Personas | `GET/PUT /cursos/{c}/comunicaciones-curso/recordatorio-mapeo` | Lectura `curso.ver`, cambio `comunicacion.enviar` | Regla automática, vista previa, carga/error recuperable, permiso explícito y bloqueo de doble envío. Respeta capacidad `comunicaciones_automaticas`. |

## Trazabilidad del enunciado

| Requisito | Entrada y evidencia funcional |
| --- | --- |
| R2.1.1 | Acceso Google, Perfil, Equipo, invitación nominal, roles/retiro/reincorporación. |
| R2.1.2 | Registro/inicio mediante Google. Gmail personal admitido; diferencia institucional existente consignada abajo. |
| R2.1.3 | Cursos → Crear curso → Vinculación; Ajustes muestra datos y operaciones de conexión disponibles. La edición general posterior no tiene endpoint. |
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

## Límites y discrepancias verificables

1. **Dominio de Google.** `backend/app/dominio/identidad.py::normalizar_correo_google` admite Gmail personal y `@miuandes.cl`, aunque el documento pide únicamente Gmail. Acceso, invitaciones y rechazos reflejan el contrato vigente. No se cambió la política de identidad del backend.
2. **Permisos de sincronización y tarea de registro.** `personas.py` exige `CURSO_ADMINISTRAR` tanto en `POST /sincronizaciones` como en `POST /registro-github` y `/restaurar`. El documento solicita respectivamente `curso.ver` y `comunicacion.enviar`. Un ayudante con esos permisos recibe `403`; la UI no ofrece una acción que su contrato rechaza.
3. **Renovar la credencial del mismo curso Canvas.** El backend permite un upsert mediante `POST /vinculacion/canvas`, pero no expone el `canvas_course_id` del curso actual. La lista `POST /canvas/cursos-disponibles` informa `ya_vinculado_a` solamente como nombre, también para el curso propio, sin identificador ni bandera que permita distinguirlo de otro curso. Reproducción: vincular curso, regresar, buscar cursos con nueva credencial; la opción propia se devuelve ocupada. Se conserva deshabilitada para no decidir por coincidencia de nombres ni habilitar otro curso ocupado. Falta un identificador estable de curso ocupante, `es_vinculo_actual`, o el vínculo Canvas actual legible.
4. **Ajustes generales y datos de perfil.** No hay `PATCH /cursos/{id}` para cambiar nombre/zona/roles Canvas/canal ni endpoint de archivar el curso (sí existen operaciones de archivado por tarea). Tampoco hay lectura/desvinculación de identidades Canvas en Perfil o cierre individual de una sesión: el contrato ofrece cerrar todas las demás. Se muestran únicamente datos y acciones disponibles.
5. **Historial detallado de mapeos y fusiones Canvas.** `GET /personas` entrega solo el mapeo vigente. No hay endpoint para leer su historial, confirmar `POSIBLE_FUSION_CANVAS` o reenviar directamente la invitación GitHub de un estudiante. La UI conserva las causas recibidas, edición/CSV y navegación a repositorios sin fabricar esas operaciones.
6. **Hora exacta del siguiente recordatorio.** `POST /pendientes/{id}/recordatorio` devuelve `429` con texto sin `Retry-After`; `GET /pendientes` no entrega `ultimo_recordatorio_en`. El límite implementado es 24 horas desde el último envío. Se explica la espera sin inventar una hora. Este contrato directo no impone el máximo total de tres del SPEC; la regla de recordatorios automáticos tiene su propia política.
7. **Estado de ejecución.** El checklist devuelve filas por ejecución, sin estado del job/fecha de próximo intento; el frontend muestra avance por ítems y conserva los pendientes tras un tiempo de espera. Las sincronizaciones devuelven `{ok,en_curso}` sin identificador consultable; se sondea la actualización del espejo y no se declara un resultado no confirmado.
8. **Impacto de retiro incompleto.** `GET /miembros/{id}/impacto-retiro` devuelve `repositorios_perdidos` y `entregas_sin_corrector` como constantes `0`. La confirmación utiliza solo el contador real de sesiones y explica las consecuencias de acceso/credenciales; no presenta esas constantes como un cálculo de correcciones afectadas.
9. **Marca de vía compartida.** `MiembroSalida`/`ContextoSalida` no incluyen `es_via_compartida`. No puede identificarse visualmente una cuenta compartida de forma fiable hasta que la API exponga esa propiedad.

## Validación de esta área

Pruebas en `frontend/tests/configuracion.spec.ts`: destino de acceso permitido, los cinco permisos y la guarda del último profesor, historial legible por ayudantes, Pendientes → mapeo actualizado, registro de Canvas con `202`, reanudación del checklist tras recarga y regla automática bloqueada sin permiso. Las pruebas usan dobles HTTP de los esquemas reales, exclusivamente en Playwright. Google/Canvas/GitHub reales no se verificaron con estas pruebas.

Comando normal desde `frontend`: `npm test -- tests/configuracion.spec.ts`. En trabajo paralelo se usó una configuración temporal equivalente en `/tmp/pds2-configuracion.playwright.ts`, puerto 4184, para no disputar el puerto 4173 de la suite general. El resultado final se registra en IMPLEMENTACION.md junto con la verificación global.

Resultado del área: **7/7 pruebas pasaron** en Chromium (3,6 s); ESLint de las nueve pantallas editadas pasó. Capturas inspeccionadas: `evidencias/configuracion-portatil.png` (1366×768), `evidencias/personas-movil-detalle.png` (390×844) y `evidencias/pendientes-movil.png` (360×844). La comprobación de anchura de Personas a 390 y 360 px no detectó desborde de documento; la tabla conserva desplazamiento dentro de su región. El recorrido de capturas no produjo `pageerror`. Datos exclusivamente sintéticos; no hay tokens en las imágenes.
