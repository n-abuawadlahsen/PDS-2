# Operación docente: tareas, entregas y seguimiento

Las pantallas reutilizan los contratos de `backend/app/api/rutas/{tareas,repositorios,versiones,tablero,timeline,identidades,archivado}.py`. No se modificó el backend. El tablero queda como primera pestaña cuando `GET /api/capacidades` incluye `tablero_actividad`; en este backend una bandera presente **habilita** la capacidad, incluso con perfil parcial.

| Requisitos / etapa | Pantalla y acción | Contrato real | Permiso | Estado |
| --- | --- | --- | --- | --- |
| R2.3.1–4 · P7/F1/F2 | Tareas: crear borrador individual/grupal desde Canvas; vincular parciales y elegir final | `GET tareas/assignments-canvas`, `GET tareas/vista-previa-nombre`, `POST tareas`, `POST tareas/{id}/entregas` | `curso.ver` / `tarea.administrar` | Conectado; modalidad y conjunto derivan de Canvas |
| R2.3.2 · F2 | Entregas: desvincular sin versiones; excluir parcial con evidencia | `GET entregas/{id}/progreso-captura`, `DELETE tareas/{id}/entregas/{id}`, `POST …/excluir` | `tarea.administrar` | Evidencia consultada antes de ofrecer la acción; historial conservado |
| R2.3.5–6 · P7 | Repositorio base: crear, subir, previsualizar, reemplazar, renombrar, borrar | `POST tareas/{id}/repositorio-base`, `GET/PUT/DELETE …/archivos/{ruta}`, `POST …/renombrar` | `curso.ver` / `tarea.administrar` | Conectado; resultados síncronos reales |
| R2.3.7–11 · P8 | Configuración: activar; Repositorios: progreso, acceso, reintento y sustitución | `POST …/activar`, `GET …/repositorios`, `POST …/reintentar`, `POST …/sustituir`, `POST …/verificar-accesos` | `curso.ver` / `tarea.administrar` | Aprovisionamiento progresivo; sustitución confirma nombre exacto |
| R2.4.1–4 · F3 | Entregas: fechas base, sección, extensiones, ambigüedad e historial | `GET tareas/{id}/entregas/fechas`, `GET entregas/{id}/historial-fechas` | `curso.ver` | Lectura del cálculo del servidor; no se recalculan fechas en React |
| R2.4.5–8 · F4 | Entregas: captura, vigente y anteriores, SHA y etiqueta separados, abrir código; captura manual | `GET …/progreso-captura`, `GET …/sujetos/{id}/version`, `POST …/registrar-versiones`, `POST …/version/{capturar-ahora,recapturar,fijar-sha}`; enlaces auditados retornados por servidor | Lectura `curso.ver`; escritura `tarea.administrar`; recapturar/fijar además Profesor | Conectado; selección en URL; sondeo sin superposición; errores recuperables |
| R2.5.1–9 · F5/F6 | Tablero: cinco bloques, período, sección/estado/alertas, comparación, serie y CSV; Seguimiento del curso | `GET …/tablero?periodo&seccion&grupo_estado&solo_alertas&pagina`, `POST …/tablero/actualizar`, `GET …/tablero.csv?periodo`, `GET cursos/{id}/seguimiento` | `curso.ver` | Paginación real de 50; CSV explica alcance completo del período; cooldown y estados de datos ausentes |
| R2.5.10 · F7 | Timeline: cuatro capas, rama e integrante, hitos, acceso a versiones | `GET …/repos/{id}/timeline?periodo&integrante&rama`, `POST/DELETE …/commits/{sha}/hito` | Lectura `curso.ver`; hito `tarea.administrar` | Filtros y retorno al tablero conservados; fechas de curso |
| F5/F7 | Timeline: identidades, revelar correo, asociar y previsualizar propagación explícita | `GET …/identidades`, `POST …/{id}/revelar`, `GET …/{id}/propagacion`, `POST …/{id}/resolver` | Lectura `curso.ver`; cambios `mapeo.editar` | Casillas desmarcadas; confirmación antes de propagar; sin correos completos automáticos |
| R2.3.11 · F8 | Cierre: cinco guardas, aviso, archivar y desarchivar | `GET …/archivado`, `POST …/archivar/aviso`, `POST …/archivar`, `POST …/desarchivar` | `tarea.administrar` y Profesor | Guardas visibles, confirmación, resultado encolado y sondeo |

Los endpoints se muestran relativos a `/api/cursos/{curso_id}` cuando corresponde. La ingesta, captura automática, creación y avisos automáticos pertenecen a procesos del servidor; la UI muestra sus resultados y no simula su ejecución.

## Contratos y limitaciones verificables

- `AssignmentCanvasSalida` entrega `es_grupal`, pero no el nombre ni identificador del conjunto de grupos. La creación informa que se usa el conjunto definido en Canvas; no inventa un selector ni una opción para cambiarlo.
- `tablero.csv` acepta solo período y exporta todo el conjunto, aunque la tabla tenga sección/estado/alertas. La interfaz lo explica junto al enlace.
- La captura manual permite introducir un instante ISO 8601 con zona/desplazamiento explícito. Evita interpretar fechas en la zona del navegador; al confirmar se envía UTC y al mostrar se utiliza la zona del curso.
- La validación automatizada usa `tests/fixtures-operacion.ts`, aislada de producción y de proveedores. No acredita OAuth, envío real de Canvas, creación real en GitHub ni trabajo real del scheduler.

## Verificación

Pruebas de comportamiento en `frontend/tests/operacion.spec.ts`: paginación de 200 sujetos; filtros y retorno desde timeline; error recuperable y cooldown; selección de entrega/recaptura con historial; permisos de ayudante; propagación de identidades con confirmación; guardas de cierre; tarea grupal y activación. Comando: `cd frontend && npm run test -- tests/operacion.spec.ts`.

Validación ejecutada: los siete casos de comportamiento pasaron (seis en la corrida conjunta y creación/activación en la repetición focalizada tras corregir el selector). `tsc --noEmit` pasó para todo el frontend; ESLint pasó para los módulos de operación. La repetición focalizada usó `npm run test -- tests/operacion.spec.ts --grep 'crea tarea grupal' --output=/tmp/pds2-operacion-results` para aislar los artefactos mientras otros agentes verificaban pantallas.

Las capturas representativas y los resultados del conjunto se registran en `IMPLEMENTACION.md`. Los pantallazos de fallos se inspeccionaron para diagnosticar un selector ambiguo y recargas HMR durante ediciones simultáneas; no se presentan como evidencia de una pantalla final.
