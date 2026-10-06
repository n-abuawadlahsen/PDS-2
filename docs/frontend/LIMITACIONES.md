# Revisión de limitaciones · 6 de octubre de 2026

La petición de corregir las limitaciones permitió completar contratos del backend y sus pantallas. La migración `0012` añade los roles Canvas adicionales, el contexto original del reparto y los alias de identidades fusionadas; se verificó únicamente en PostgreSQL local aislado. Se conserva la autenticación y la política vigente de Gmail/miuandes.cl. Las escrituras siguen requiriendo sesión, CSRF y permisos del curso.

## Limitaciones corregidas

| Área | Resultado verificable |
| --- | --- |
| Perfil | Cierre de una sesión concreta, incluida la actual, sin revocar otras cuentas/sesiones. Lectura y desvinculación de identidades Canvas propias con confirmación, retiro de credenciales y promoción del respaldo válido. Conserva cursos, membresías e historial. |
| Canvas | La lista identifica al curso ocupante por UUID. Permite renovar la credencial del vínculo propio; otro curso sigue bloqueado aunque tenga el mismo nombre. Recupera credenciales retiradas/inválidas sin colisionar con el índice de la credencial operativa. |
| Ajustes | Edición persistida de nombre, zona IANA y umbrales de actividad/desbalance, con validación y auditoría. Conserva código, período, slug e instantes históricos; encola el recálculo de métricas. |
| Permisos | Sincronizar Personas requiere `curso.ver`; crear/restaurar el registro GitHub requiere `comunicacion.enviar`. La interfaz aplica las mismas reglas. |
| Historial | Personas permite consultar los mapeos históricos del estudiante por su ID y curso, sin exponer evidencia sensible del proveedor. |
| Recordatorios | Pendientes muestra último envío y próximo momento permitido. El rechazo `429` incluye `Retry-After`; el bloqueo de fila impide envíos manuales simultáneos. |
| Equipo | El impacto de retiro calcula repositorios concedidos y correcciones que quedarán sin corrector. No cuenta acceso por equipo para quien todavía no lo aceptó, correcciones terminales ni publicaciones en curso. La vía compartida se identifica en Equipo y en el contexto del curso. |
| Trabajos | Checklist, sincronización, registro GitHub y comprobación de notas Canvas entregan IDs consultables, estado, intentos y próximo reintento. El sondeo termina en `OK`, `CANCELADO` o `REQUIERE_ATENCION`; los IDs en URL permiten retomar. El estado público excluye payloads y errores internos. |
| Registro en cola | Se corrigió un `202` que revertía la transacción y dejaba el trabajo sin persistir. Se registró su ejecutor real, que revalida permisos y completa creación/restauración mediante el adaptador Canvas existente. Reejecutarlo no duplica la tarea confirmada. |
| Tareas y CSV | La selección de tarea muestra nombre/ID real del conjunto Canvas. El CSV del tablero aplica período, sección, estado y alertas igual que la tabla, y exporta todas las filas coincidentes, sin limitarse a la página. |
| Reparto | Edición auditada de pesos entre 0 y 10; `null` recupera el predeterminado del rol. Cambiar un peso invalida la previsualización y no reasigna correcciones por sí solo. |
| Borradores | Cada guardado registra autor, rol, vía compartida y fecha del servidor. La pantalla muestra esos datos y el comentario completo que publicará el backend; el pie conserva al autor de la corrección aunque publique otra persona. |
| Evidencia de participación | La matriz relaciona sujeto/repositorio por UUID, muestra accesos comprobados y causas de las incidencias de la entrega: sin acceso, sin atribuir o sin commits. No convierte la ausencia de incidencias en una causa ni en cero. La selección para preparar notas por falta de entrega sigue siendo explícita. |
| Navegación | El data router protege el borrador ante Atrás/Adelante, enlaces y navegación programática; la recarga/cierre usa la advertencia del navegador. Cancelar conserva el formulario. |
| Roles Canvas | Ajustes persiste IDs adicionales derivados de `StudentEnrollment`, con validación, auditoría y sincronización en cola. Se combinan los resultados paginados del padrón estándar y de los roles seleccionados, sin duplicar inscripciones ni incorporar docentes. |
| Archivo del curso | Confirmación escrita del slug, inventario CSV y lista de cierres sin captura. Pausa trabajos, ingesta y comunicaciones; bloquea escrituras y conserva versiones/borradores. La opción de archivar también GitHub está marcada por defecto y exige las cinco guardas. Sólo los trabajos de esa tanda consentida pueden completar el archivo remoto; reevalúan las guardas. Reactivar restaura las pausas previas y cancela archivos remotos todavía pendientes. Los repositorios ya archivados se reactivan desde el cierre de su tarea. |
| Fusión Canvas | Personas detecta coincidencias exactas de login/SIS entre una identidad retirada y otra nueva, muestra evidencia e historial y exige confirmación de profesor. Conserva el UUID con historia, repositorios, mapeos y versiones inmutables; la fila nueva queda como alias retirado. No fusiona automáticamente por nombres. |
| Invitaciones del estudiante | Personas permite comprobar y solicitar reenvío por estudiante/repositorio. El trabajo consulta el estado real antes de reenviar, revalida permisos y limita a tres reenvíos con 24 horas de separación. Un doble clic devuelve el mismo trabajo; otros accesos se conservan. |
| Realineación | Los repartos nuevos guardan su criterio, secciones, integrantes y mapa de correctores. La sincronización marca cambios sin reasignar ni borrar borradores. Repartir permite previsualizar y aplicar sólo las filas desalineadas según el criterio original; los casos ambiguos exigen decisión docente. |
| Aviso a profesores | Un ayudante puede solicitar un aviso por entregas sin corrector. El outbox revalida destinatarios y necesidad, registra el estado real, evita duplicados durante 24 horas y comparte la reserva diaria de correo con las invitaciones. |
| Notas grupales | Entregas muestra el ajuste del espejo, explica su efecto y ofrece al profesor un enlace profundo a la configuración en Canvas, antes de cualquier intento de publicación. Después del cambio externo, permite sincronizar y actualiza el ajuste sólo al terminar el trabajo. No modifica el assignment vinculado, conforme a RG-082. |
| Guarda de correcciones | El cierre de repositorios cuenta las correcciones no terminales, exceptuando entregas/sujetos excluidos y casos no calificables. Se comprueba al solicitar y antes de cada archivo remoto. |

## Límites que siguen vigentes

| Límite | Evidencia y alcance pendiente |
| --- | --- |
| Configuración de tareas en Canvas | [SPEC 12, §12.1.4](../SPEC/12-correccion.md) establece que la aplicación no modifica campos de un assignment vinculado (RG-082), prevaleciendo sobre §12.10.3. La opción individual se cambia en Canvas y se consulta mediante sincronización. |
| Integraciones externas | La prueba local utiliza FastAPI, PostgreSQL y trabajador reales, con dobles de Google/Canvas/GitHub. OAuth real, correos, repositorios y publicación de notas en proveedores reales requieren sus credenciales/configuración y un curso de ensayo. No quedan certificados por estas pruebas. |
| Fusiones con dos historiales productivos | Se rechazan si la identidad nueva ya tiene repositorios creados/en creación, versiones, correcciones iniciadas o cuenta GitHub declarada. Hace falta resolver qué evidencia corresponde a cada identidad; una coincidencia de login/SIS no autoriza a sobrescribir esas relaciones. La pantalla muestra el motivo. |
| Repartos anteriores | No se reconstruye el criterio detallado de asignaciones que nunca guardaron su contexto. Se mantienen y pueden repartirse explícitamente para registrar un nuevo criterio. |
| Cursos archivados anteriores | Sin una auditoría del estado previo no se inventa una configuración de restauración. La reactivación responde con un motivo concreto; los nuevos archivos sí conservan su configuración. |
| Borradores anteriores a la auditoría | Conservan su contenido y el autor persistido, pero no se puede recuperar con precisión la fecha y el rol histórico de guardado que nunca se registraron. La API devuelve fecha/rol desconocidos; un nuevo guardado registra ambos. |
| Histórico de causas y accesos | La matriz muestra las incidencias abiertas registradas para la entrega y el acceso actual del espejo, con sus fechas. No reconstruye retrospectivamente causas o accesos que no se persistieron. Si falta una causa, pide revisar la evidencia. |

El límite automático de tres recordatorios no es una limitación del envío manual: [SPEC 11, §11.6.3](../SPEC/11-informes-y-comunicacion.md) permite el recordatorio manual incluso después de agotar los automáticos. Se conserva el intervalo manual de 24 horas. Gmail y `miuandes.cl` son la política de identidad actualmente implementada por el proyecto.

La privacidad de los borradores sigue la función `es_propietario`: los profesores y el ayudante asignado pueden verlos; un ayudante no asignado recibe `borrador: null`, incluso si puede publicar. Los nuevos metadatos no abren una lectura alternativa de esa nota privada.

## Comprobación reproducible

- `frontend/tests/limitaciones.spec.ts`: 10 recorridos de regresión de sesiones/Canvas, validación, historial de navegación, fallos de trabajos, autoría, pesos, causas y finalización simultánea de sincronizaciones.
- `backend/tests/api/test_limitaciones_frontend.py`: 23 casos con PostgreSQL aislado; comprueban CSRF, pertenencia, permisos, índices de credenciales, auditoría, cooldown, datos históricos, CSV filtrado, autoría y ejecución del registro en cola.
- `frontend/tests/pendientes-restantes.spec.ts`: siete recorridos de archivo/restauración, guardas, fusión, reenvío, realineación, aviso y configuración grupal.
- `backend/tests/api/test_pendientes_restantes.py`: 17 casos de permisos, consentimiento, conservación de versiones, alias, auditoría, cuotas, idempotencia, revalidación de guardas y bloqueo de trabajos/comunicaciones al archivar.
- `frontend/tests/serve_backend.py --pytest` prepara un contenedor PostgreSQL propio, aplica las migraciones y ejecuta pytest sin usar la base del equipo. Si se solicita `--cov`, conserva esa opción; de lo contrario usa `--no-cov`.
- Resultados globales, comandos y capturas: [IMPLEMENTACION.md](IMPLEMENTACION.md).
