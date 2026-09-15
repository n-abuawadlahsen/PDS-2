# Actualización de invitaciones de GitHub

## Problema y comportamiento nuevo

En la prueba del 15 de septiembre una estudiante aceptó su invitación y pudo
hacer commits, pero la aplicación conservó temporalmente «Invitado, sin
aceptar». La tabla se refrescaba cada 10 segundos; el backend comprobaba GitHub
cada 15 minutos. El [diagnóstico](DIAGNOSTICO-ACEPTACION-GITHUB-2026-09-15.md)
contiene la evidencia y la confirmación posterior del acceso.

Ahora el trabajo `reconciliar_accesos` se programa cada **60 segundos**:

- Prioriza repositorios con accesos pendientes (`DEGRADADO`), del más antiguo
  al más recientemente revisado.
- Procesa como máximo **20 repositorios por trabajo**. Con muchos pendientes
  puede requerir varios ciclos. El resto de repositorios se vuelve elegible
  para revisión a los 15 minutos; se reservan hasta 4 lugares del lote para
  esos repositorios, para que muchos pendientes no los posterguen indefinidamente.
- Los intentos fallidos también avanzan en la ronda, para que un repositorio
  problemático no retenga siempre el primer lugar.
- No acumula barridos periódicos si ya hay una comprobación pendiente, en
  ejecución o esperando reintento para ese curso.
- Al arrancar el trabajador, actualiza las programaciones activas existentes
  a 60 segundos y adelanta su próxima ejecución si correspondía. No hay que
  recrear cursos o tareas; no reactiva programaciones pausadas.

Es una reducción del desfase, no una actualización instantánea por webhook.
Se suman la espera en cola, el tick de 30 segundos del planificador, la duración
de GitHub y el refresco de la tabla. La suspensión del servicio de Render o los
errores del proveedor también pueden retrasar la comprobación.

Este ajuste sustituye la cadencia de 15 minutos de P8/SPEC 14 §14.7.4 para los
pendientes, por solicitud del usuario tras la prueba real. Reutiliza el trabajo
existente y el cerrojo de GitHub por curso; no añade un tipo de trabajo.

## Pantalla y comprobación manual

La pantalla distingue «La tabla se refresca cada 10 segundos» de la consulta
periódica a GitHub. Cada acceso muestra su fecha de comprobación real; si no
hay una fecha registrada se indica explícitamente.

El botón **Comprobar invitaciones en GitHub** solicita un trabajo para la tarea
actual. Respeta `tarea.administrar`, CSRF y el estado activo de la tarea. No
llama a GitHub dentro de la petición HTTP. Si ya existe una solicitud en curso
o se hizo una hace menos de un minuto, reutiliza esa solicitud. Solicitudes
concurrentes se serializan mediante el bloqueo de la fila del curso.

El botón muestra la espera y se deshabilita mientras la solicitud está en
curso o dentro del intervalo mínimo. La tabla sigue consultando el backend y
muestra los resultados automáticamente, también si la comprobación falla.
El límite de 20 repositorios también se aplica a la solicitud manual; el resto
continúa en los siguientes ciclos.

Cuando GitHub confirma que la cuenta ya es colaboradora, el backend registra
`ACEPTADO`, retira el enlace de invitación pendiente y recalcula el repositorio
como `OPERATIVO` si se cumplen sus demás condiciones. No usa un commit como
prueba de aceptación: consulta el acceso efectivo en GitHub.

Los errores de GitHub se conservan por repositorio y el trabajo pasa a
reintento; ya no termina como exitoso si hubo comprobaciones fallidas. Los
avances de otros repositorios se conservan. La fecha de comprobación solo
cambia después de una respuesta del proveedor, nunca por refrescar la pantalla
ni por intentar una consulta que falló.

## Contrato y migración

- `POST /api/cursos/{curso_id}/tareas/{tarea_id}/repositorios/verificar-accesos`
  devuelve HTTP 202 y el identificador, estado, fecha de solicitud y fecha en
  que puede pedirse otra comprobación.
- El `GET .../repositorios` incluye `verificacion_accesos`, correspondiente a la
  última solicitud manual de la tarea, y `acceso_verificado_en` por fila.
  La respuesta usa `Cache-Control: no-store`.
- Migración **`0003`**: añade `acceso_repositorio.verificado_en`, timestamp con
  zona horaria y nullable. No rellena fechas históricas ficticias ni cambia
  permisos, repositorios o identidades existentes.

## Despliegue

Publicar backend y frontend de esta revisión. El trabajador aplica
`alembic upgrade head` al arrancar como en el despliegue existente. Comprobar
en `/estado` que `revision_actual` y `revision_esperada` sean **`0003`**, y que
el trabajador haya iniciado. No se requieren nuevas variables de entorno ni
configurar webhooks.

Para comprobarlo, aceptar una invitación pendiente en una cuenta de prueba y
observar su fila. Puede esperarse al siguiente ciclo o solicitar la comprobación
manual. El resultado debe incluir la fecha de consulta y el acceso aceptado.

## Pruebas

Las pruebas añadidas cubren la actualización de programaciones de cursos ya
existentes, aceptación durante un ciclo periódico, deduplicación de solicitudes,
CSRF, fallos sin fechas ficticias, rotación de lotes y la actualización visible
de la tabla en el navegador. Las pruebas usan proveedores simulados; la nueva
versión todavía debe verificarse tras desplegarla con GitHub real.

Verificación local completada sobre `916ee9f` (incluye el cambio remoto del ítem
16 de Canvas) más esta corrección:

- Backend: **277 pruebas aprobadas**, cobertura del dominio **97 %**.
- Frontend: **27 pruebas aprobadas**, incluidas accesibilidad y adaptación.
- Build de frontend, ESLint, Prettier, Ruff y mypy aprobados.
- Actualización local `0002 → 0003` y `alembic check` aprobados, sin divergencia
  entre modelos y migraciones.

El remoto se integró con `git pull --ff-only origin main`, sin conflictos.
Estos cambios quedan locales para revisión y publicación por el usuario.
