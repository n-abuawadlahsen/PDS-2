# Revisión de limitaciones · 6 de octubre de 2026

La petición de corregir las limitaciones permitió completar contratos concretos del backend usando las tablas y procesos existentes. Esta revisión no añade migraciones, sustituye la autenticación ni cambia la política vigente de Gmail/miuandes.cl. Las escrituras siguen requiriendo sesión, CSRF y permisos del curso.

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

## Límites que siguen vigentes

| Límite | Evidencia y alcance pendiente |
| --- | --- |
| Integraciones externas | La prueba local utiliza FastAPI, PostgreSQL y trabajador reales, con dobles de Google/Canvas/GitHub. OAuth real, correos, repositorios y publicación de notas en proveedores reales requieren sus credenciales/configuración y un curso de ensayo. No quedan certificados por estas pruebas. |
| Ajustes que no están modelados | `modelos_curso.py` no persiste una configuración de roles Canvas adicionales. Tampoco existe un flujo de archivado del curso completo que coordine tareas, ingesta, correcciones y comunicaciones; el cierre/archivado por tarea sí está conectado. Implementarlos requiere completar esos flujos del servidor, además de la pantalla. |
| Fusión de identidades Canvas | No hay operación de confirmación de `POSIBLE_FUSION_CANVAS` ni algoritmo que conserve sus relaciones históricas. Mapeo manual/CSV e historial están conectados; una fusión no se simula por coincidencia de nombres. |
| Reenvío manual de invitación del estudiante | Existe el proceso automático de invitaciones/accesos; no hay un contrato de reenvío directo desde Personas para un estudiante concreto. Se conserva la consulta y comprobación de accesos. |
| Realineación del reparto | Existen `criterio_seccion_id` y `desalineada_motivo`, pero el reparto actual no guarda/recalcula ese criterio ante cambios de sección. No existe una acción de realineación automática. Se puede previsualizar/aplicar un nuevo reparto o reasignar manualmente. |
| Aviso por falta de corrector y opción de notas grupales | Se mantienen la incidencia y la bandeja de filas sin corrector, pero no hay acción de notificar a profesores desde esa fila. `grade_group_students_individually` se lee de Canvas y se respeta al publicar; no hay escritura de esa opción desde la app. |
| Borradores anteriores a la auditoría | Conservan su contenido y el autor persistido, pero no se puede recuperar con precisión la fecha y el rol histórico de guardado que nunca se registraron. La API devuelve fecha/rol desconocidos; un nuevo guardado registra ambos. |
| Histórico de causas y accesos | La matriz muestra las incidencias abiertas registradas para la entrega y el acceso actual del espejo, con sus fechas. No reconstruye retrospectivamente causas o accesos que no se persistieron. Si falta una causa, pide revisar la evidencia. |

El límite automático de tres recordatorios no es una limitación del envío manual: [SPEC 11, §11.6.3](../SPEC/11-informes-y-comunicacion.md) permite el recordatorio manual incluso después de agotar los automáticos. Se conserva el intervalo manual de 24 horas. Gmail y `miuandes.cl` son la política de identidad actualmente implementada por el proyecto.

La privacidad de los borradores sigue la función `es_propietario`: los profesores y el ayudante asignado pueden verlos; un ayudante no asignado recibe `borrador: null`, incluso si puede publicar. Los nuevos metadatos no abren una lectura alternativa de esa nota privada.

## Comprobación reproducible

- `frontend/tests/limitaciones.spec.ts`: 10 recorridos de regresión de sesiones/Canvas, validación, historial de navegación, fallos de trabajos, autoría, pesos, causas y finalización simultánea de sincronizaciones.
- `backend/tests/api/test_limitaciones_frontend.py`: 23 casos con PostgreSQL aislado; comprueban CSRF, pertenencia, permisos, índices de credenciales, auditoría, cooldown, datos históricos, CSV filtrado, autoría y ejecución del registro en cola.
- `frontend/tests/serve_backend.py --pytest` prepara un contenedor PostgreSQL propio, aplica las migraciones y ejecuta pytest sin usar la base del equipo. Si se solicita `--cov`, conserva esa opción; de lo contrario usa `--no-cov`.
- Resultados globales, comandos y capturas: [IMPLEMENTACION.md](IMPLEMENTACION.md).
