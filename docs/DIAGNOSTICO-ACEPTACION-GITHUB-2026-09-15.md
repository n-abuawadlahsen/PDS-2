# Diagnóstico de aceptación de invitación en GitHub

Este informe describe la versión `e299392`. La corrección posterior del desfase
está documentada en [ACTUALIZACION-ACCESOS-GITHUB.md](ACTUALIZACION-ACCESOS-GITHUB.md).

## Resultado

GitHub confirma que `Filipa-X` tiene acceso de escritura al repositorio
`PDS-2-test/icc1101-2026-2-test1-e37482-parada-gonzalez-filipa-x`.
El usuario confirmó durante el diagnóstico que la aplicación ya muestra a
Filipa con acceso. El caso queda resuelto como un desfase entre la aceptación
en GitHub y la sincronización: la pantalla se refresca cada 10 segundos, pero
las aceptaciones se consultan en GitHub cada 15 minutos.

No se ha consultado la base de datos de producción ni el historial de ejecución
del trabajador. Por tanto, no se conoce el instante exacto en que la aplicación
registró la aceptación, aunque su actualización quedó confirmada por el usuario.

## Evidencia consultada

Diagnóstico sobre el código del commit `e299392`, el 15 de septiembre de 2026.
Consultas autenticadas de solo lectura con GitHub CLI, usando la sesión local
existente. Horas expresadas en `America/Santiago` (UTC−3 en esta fecha).

| Evidencia | Resultado |
| --- | --- |
| Evento del repositorio `MemberEvent`, acción `added` | `Filipa-X`, 18:18:39; valor original `2026-09-15T21:18:39Z` |
| Hora del archivo de captura de la aplicación | 18:26:15; 7 min 36 s después del evento |
| Commit `bb0d4cc3fcfbeae4788b5599c26a37d5222689a9` | Autor `Filipa-X`, 18:28:51 |
| `GET /repos/{owner}/{repo}/collaborators/Filipa-X` | HTTP 204: colaboradora |
| `GET /repos/{owner}/{repo}/collaborators/Filipa-X/permission` | `permission: write`, `role_name: write` |
| `GET /repos/{owner}/{repo}/invitations` | Lista vacía: ninguna invitación pendiente en ese repositorio |
| `GET https://proyecto2-api-oyxf.onrender.com/estado` | Base alcanzable, revisión actual y esperada `0002`, `degradado: false`, 9 trabajos periódicos activos |
| Nueva revisión de la aplicación por el usuario | «Ya aparece con acceso» |

El contador de 9 trabajos informa cuántas programaciones están activas. **No
demuestra que los trabajos se estén ejecutando con éxito**, ni muestra el último
resultado de `reconciliar_accesos`.

La consulta de permisos se hizo con la identidad de GitHub CLI, no con el token
de instalación que usa producción. Confirma el acceso de la estudiante; no
verifica por sí sola los permisos ni las respuestas que recibe la GitHub App.

## Flujo encontrado en el código

1. `frontend/src/paginas/RepositoriosTarea.tsx` consulta la API cada `10_000` ms.
2. `backend/app/api/rutas/repositorios.py` devuelve el estado guardado en la BD;
   esa lectura no consulta GitHub ni ejecuta una sincronización.
3. `backend/app/adaptadores/programacion_repo.py` programa
   `reconciliar_accesos` cada `900` segundos por curso.
4. `backend/app/adaptadores/aprovisionamiento_repo.py`, función
   `_reconciliar_repositorio`, consulta si el estudiante ya es colaborador.
   Si la respuesta es positiva, cambia `INVITADO` a `ACEPTADO` y recalcula el
   estado del repositorio. Si el resto de condiciones se cumple, queda
   `OPERATIVO`.
5. No existe receptor de webhooks de GitHub para adelantar esa detección.

La cadencia de 15 minutos corresponde al plan de implementación P8. No es una
garantía de actualización en 15 minutos exactos: se suman el tick del
planificador, la espera en cola, posibles reintentos y el refresco de pantalla.
API y trabajador comparten el servicio gratuito de Render; una suspensión del
servicio también interrumpe el procesamiento mientras está suspendido. No se
observó ni se confirmó una suspensión durante esta prueba.

## Validación local

Se ejecutó en la base de pruebas local, con los proveedores simulados, el caso
existente:

```text
tests/api/test_aprovisionamiento.py::test_ca_8_6_03_aceptar_la_invitacion_lleva_a_operativo
1 passed
```

Comprueba aceptación → ejecución del trabajo → `ACEPTADO` / `OPERATIVO` y retiro
de la estudiante del listado de invitaciones pendientes. Valida el flujo del
código; no prueba el estado del trabajador desplegado.

## Conclusión y mejora de claridad

No se observó un fallo persistente de aceptación: GitHub concedió el acceso y
la aplicación terminó reflejándolo. El texto «Actualización automática cada
10 segundos» no comunica la cadencia de consulta a GitHub. Conviene aclararlo
en la interfaz para evitar interpretar el estado guardado como una comprobación
en tiempo real. Esa mejora no se implementó como parte de este diagnóstico.

## Para diagnosticar una futura demora persistente

Ejecutar [la consulta de diagnóstico](diagnostico-aceptacion-github.sql) en la
base de datos de la aplicación. Solo lee el repositorio indicado, su acceso,
la programación y los trabajos recientes de ese curso; no selecciona tokens,
credenciales ni payloads. No se ejecutó en producción durante este diagnóstico.

Interpretación:

- `acceso_estado = ACEPTADO` y repositorio `OPERATIVO`: el backend ya detectó
  la aceptación. Si la pantalla aún muestra otra cosa, comparar su respuesta
  de `/repositorios` con la base consultada y comprobar el entorno desplegado.
- No hay programación activa de `reconciliar_accesos`: falta programar el curso.
- `proxima_ejecucion` vencida o trabajos `PENDIENTE` antiguos: investigar el
  planificador, la cola y el trabajador en Render.
- Trabajos `REINTENTAR`, `REQUIERE_ATENCION` o `EN_CURSO` prolongado: consultar
  `ultimo_error`, horas y logs del trabajador.
- Trabajo `OK` posterior a la aceptación pero acceso aún `INVITADO`: revisar
  los filtros de tarea/sujeto, la identidad guardada y el error del repositorio.
  El reconciliador captura algunos errores de GitHub por repositorio y puede
  terminar el trabajo como `OK` aunque no haya podido actualizar ese acceso.

No se cambiaron estados en producción, no se reenviaron invitaciones y no se
modificó el comportamiento del frontend o del backend durante el diagnóstico.

## Referencias externas

- [GitHub: comprobar si una cuenta es colaboradora](https://docs.github.com/en/rest/collaborators/collaborators#check-if-a-user-is-a-repository-collaborator).
- [Render: suspensión de servicios gratuitos por inactividad](https://render.com/docs/free#spinning-down-on-idle).
