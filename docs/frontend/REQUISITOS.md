# Trazabilidad de los 59 requisitos

Esta matriz describe la entrada funcional del frontend, no certifica servicios externos reales. El servidor conserva las automatizaciones y las reglas de dominio. La revisión vigente de limitaciones se detalla en [LIMITACIONES.md](LIMITACIONES.md).

En los contratos `…` representa exclusivamente `/api/cursos/{curso_id}`. Los identificadores de tarea, entrega, sujeto y repositorio se escriben en cada ruta para evitar confundir rutas de pantalla y API. Las lecturas de curso requieren `curso.ver`; los permisos adicionales y las limitaciones se detallan en la última columna y en los anexos por área.

| Requisito | Pantalla | Acción | Contrato | Cobertura / límite |
| --- | --- | --- | --- | --- |
| R2.1.1 | Acceso, Perfil, Equipo | Google, perfil/sesiones, roles | `POST /auth/google/inicio; GET/PATCH/DELETE /api/perfil; GET/DELETE /api/perfil/sesiones; GET …/equipo` | Conectado; perfil/sesiones propios, administración del equipo con `equipo.administrar`; cierre individual y de las demás sesiones; identidades Canvas propias |
| R2.1.2 | Acceso | Entrar con Google | `POST /auth/google/inicio` | Conectado; también admite miuandes.cl según backend |
| R2.1.3 | Cursos, Ajustes | Crear y configurar curso | `GET/POST /api/cursos; PATCH …; GET …/archivo/previsualizar; POST …/{archivar,desarchivar}` | Conectado; nombre, zona IANA, umbrales y roles Canvas adicionales; archivo confirmado con inventario, restauración y GitHub optativo con guardas |
| R2.1.4 | Vinculación | Credencial propia y selección de curso | `POST …/vinculacion/canvas/cursos-disponibles; POST …/vinculacion/canvas` | Conectado con `curso.administrar`; renovación propia habilitada por UUID; otros cursos ocupados quedan bloqueados |
| R2.1.5 | Vinculación | Instalar GitHub App y canjear retorno | `POST …/vinculacion/github/iniciar; POST /api/vinculacion/github/callback` | Conectado; inicio/adopción con `curso.administrar`, callback con sesión |
| R2.1.6 | Vinculación, Verificación | Ayuda, consentimientos, 19 ítems y dos pruebas | `GET …/verificacion/ultima; POST …/verificacion; GET …/verificacion/{ejecucion_id}; POST …/verificacion/items/{item}` | Conectado; API de lectura `curso.ver`, pantalla y escritura `curso.administrar`; ejecución recuperable y polling 2 s |
| R2.1.7 | Equipo, Invitación | Invitar profesor y aceptar | `POST …/equipo/invitaciones; POST /api/invitaciones/{token}/aceptar` | Conectado; emitir requiere `equipo.administrar`, aceptar requiere sesión y correo nominal coincidente |
| R2.1.8 | Equipo | Cinco permisos concedibles, implícitos y exclusivos | `PATCH …/miembros/{id}/permisos` | Conectado; edición con `equipo.administrar` |
| R2.1.9 | Equipo | Impacto, retiro confirmado y reincorporación | `GET …/miembros/{membresia_id}/impacto-retiro; POST …/equipo/{membresia_id}/retiro; POST …/equipo/{membresia_id}/reincorporacion` | Conectado con `equipo.administrar`; impacto real de repositorios/correcciones calculado por el servidor |
| R2.2.1 | Personas | Consultar espejo y sincronizar | `GET …/personas; POST …/sincronizaciones; GET …/personas/fusiones-canvas; POST …/personas/fusiones-canvas/{incidencia}/confirmar` | Conectado; sincronizar requiere `curso.ver`; fusión con evidencia y consentimiento de profesor conserva UUID/historia, rechaza dos historiales productivos |
| R2.2.2 | Personas | Secciones y filtros | `GET …/personas` | Conectado |
| R2.2.3 | Personas | Grupos, nombre del conjunto e integrantes | `GET …/personas` | Conectado; grupos con nombre de conjunto; no hay listado independiente de conjuntos vacíos |
| R2.2.4 | Personas | Registro Canvas, mapeo y CSV con preview | `POST …/registro-github; POST …/personas/{id}/mapeo; POST …/mapeo/importar-csv` | Conectado; registro exige `comunicacion.enviar`, mapeo/CSV `mapeo.editar`; historial detallado conectado |
| R2.2.5 | Personas, Pendientes | Corregir cuenta pendiente y actualizar | `POST …/personas/{id}/mapeo` | Conectado; continuación automática en backend |
| R2.2.6 | Pendientes | Causa, persona, grupo y recordatorio | `GET …/pendientes; POST …/pendientes/{id}/recordatorio` | Conectado; recordatorio con `comunicacion.enviar`; último/próximo envío y `Retry-After` disponibles |
| R2.3.1 | Tareas | Crear borrador desde Canvas | `GET …/tareas/assignments-canvas; POST …/tareas` | Conectado |
| R2.3.2 | Tarea, Entregas | Vincular parciales/final, excluir o desvincular | `POST …/tareas/{tarea_id}/entregas; DELETE …/tareas/{tarea_id}/entregas/{entrega_id}; POST …/tareas/{tarea_id}/entregas/{entrega_id}/excluir` | Conectado; guarda evidencia preservada |
| R2.3.3 | Tareas, Entregas | Modalidad derivada de Canvas | `GET …/tareas/assignments-canvas; GET …/entregas/{entrega}/calificacion-individual; POST …/sincronizaciones` | Conectado; conjunto Canvas visible; guía el cambio individual en Canvas y confirma el espejo al sincronizar, conforme a RG-082 |
| R2.3.4 | Tarea, Repositorios | Conjunto compartido de repositorios | `GET …/tareas/{id}/repositorios` | Lectura conectada; invariante del backend |
| R2.3.5 | Repositorio base | Crear base opcional | `POST …/tareas/{id}/repositorio-base` | Conectado; operación síncrona |
| R2.3.6 | Repositorio base | Subir, ver, reemplazar, renombrar y borrar | `GET/PUT/DELETE …/tareas/{tarea_id}/repositorio-base/archivos/{ruta}; POST …/tareas/{tarea_id}/repositorio-base/renombrar` | Conectado; preview de texto seguro |
| R2.3.7 | Configuración de tarea, Repositorios | Activar y consultar progreso | `POST …/tareas/{tarea_id}/activar; GET …/tareas/{tarea_id}/repositorios` | Activación conectada; ejecución automática del backend |
| R2.3.8 | Tareas | Vista previa del nombre inequívoco | `GET …/tareas/vista-previa-nombre` | Conectado; nombres definidos por backend |
| R2.3.9 | Repositorios, Personas | Accesos e invitaciones de integrantes | `GET …/tareas/{tarea_id}/repositorios; POST …/tareas/{tarea_id}/repositorios/verificar-accesos; GET …/personas/{estudiante}/invitaciones-github; POST …/personas/{estudiante}/invitaciones-github/{acceso}/reenviar` | Lectura, comprobación y reenvío manual conectados; revalida estado/permisos, tres reenvíos y 24 h entre ellos |
| R2.3.10 | Repositorios | Progreso y estados de espera | `GET …/tareas/{tarea_id}/repositorios` | Sondeo conectado; creación progresiva backend |
| R2.3.11 | Repositorios, Cierre | Estados, motivos, reintentos y cinco guardas | `GET …/tareas/{tarea_id}/repositorios; POST …/tareas/{tarea_id}/repositorios/{repositorio_id}/reintentar; GET …/tareas/{tarea_id}/archivado` | Conectado |
| R2.3.12 | Comunicaciones de tarea | Disponibilidad del repositorio y cola | `GET …/tareas/{tarea_id}/comunicaciones; PUT …/tareas/{tarea_id}/comunicaciones/{evento}; GET …/comunicaciones` | UI conectada; envío automático backend |
| R2.4.1 | Entregas | Fechas base de Canvas | `GET …/tareas/{id}/entregas/fechas` | Conectado |
| R2.4.2 | Entregas | Fechas y origen por sección | `GET …/tareas/{id}/entregas/fechas` | Conectado; cálculo solo backend |
| R2.4.3 | Entregas | Excepciones de grupos y estudiantes | `GET …/tareas/{id}/entregas/fechas` | Conectado; ambigüedad y candidatas |
| R2.4.4 | Entregas | Historia y actualización del espejo | `GET …/entregas/{id}/historial-fechas; POST …/sincronizaciones` | UI conectada; solicitar sincronización exige `curso.ver`; ejecución backend |
| R2.4.5 | Entregas | Estado de captura y captura manual permitida | `GET …/entregas/{entrega_id}/progreso-captura; POST …/entregas/{entrega_id}/registrar-versiones; POST …/entregas/{entrega_id}/sujetos/{sujeto_id}/version/capturar-ahora` | UI conectada; acciones manuales con `tarea.administrar`; captura automática backend |
| R2.4.6 | Entregas | Selección de entrega y sus versiones | `GET …/entregas/{entrega_id}/sujetos/{sujeto_id}/version` | Conectado |
| R2.4.7 | Entregas | Vigente e históricas, SHA/etiqueta separados | `GET …/entregas/{entrega_id}/sujetos/{sujeto_id}/version; POST …/entregas/{entrega_id}/sujetos/{sujeto_id}/version/recapturar` | Conectado; recaptura exige Profesor y `tarea.administrar`; historia persistida backend |
| R2.4.8 | Entregas, Corrección | Abrir código, comparar, descargar evidencia | `GET …/versiones/{version_id}/abrir?destino=arbol\|comparacion\|zip` | Conectado |
| R2.5.1 | Tablero de tarea | Cinco bloques y filtros | `GET …/tareas/{id}/tablero` | Conectado |
| R2.5.2 | Tablero, Timeline | Actividad diaria y commits | `GET …/tareas/{tarea_id}/tablero; GET …/tareas/{tarea_id}/repos/{repo_id}/timeline` | Conectado; datos del espejo |
| R2.5.3 | Tablero | Atención por falta de actividad | `GET …/tareas/{tarea_id}/tablero` | Conectado; umbrales/causas del servidor |
| R2.5.4 | Tablero, Timeline | Participación y atribución pendiente | `GET …/tareas/{tarea_id}/tablero; GET …/tareas/{tarea_id}/repos/{repo_id}/identidades` | Conectado; acceso/identidad no equivalen a falta de trabajo |
| R2.5.5 | Tablero, Repositorios | Contadores y subtipos de creación | `GET …/tareas/{tarea_id}/tablero; GET …/tareas/{tarea_id}/repositorios` | Conectado; degradado separado de problemas |
| R2.5.6 | Tablero, Entregas | Línea de entregas/fechas/estado | `GET …/tareas/{tarea_id}/tablero; GET …/tareas/{tarea_id}/entregas/fechas` | Conectado |
| R2.5.7 | Tablero, Timeline | Seleccionar período por entrega | `GET …/tareas/{tarea_id}/tablero?periodo={periodo}; GET …/tareas/{tarea_id}/repos/{repo_id}/timeline?periodo={periodo}` | Conectado; filtros en URL |
| R2.5.8 | Tablero, Timeline | Comparar integrantes y tramos | `GET …/tareas/{tarea_id}/tablero; GET …/tareas/{tarea_id}/repos/{repo_id}/timeline` | Conectado; coautoría explicada |
| R2.5.9 | Tablero | Días activos, líneas, distribuciones y exportación | `GET …/tareas/{tarea_id}/tablero; GET …/tareas/{tarea_id}/tablero.csv?periodo={periodo}` | Conectado; CSV exporta todas las filas del período que coinciden con los filtros |
| R2.5.10 | Timeline | Commits, ciclo de vida, entregas, composición e hitos | `GET …/tareas/{tarea_id}/repos/{repo_id}/timeline; POST/DELETE …/tareas/{tarea_id}/repos/{repo_id}/commits/{sha}/hito` | Conectado |
| R2.6.1 | Informes | Histórico, día y vista previa | `GET …/informes; GET …/informe-de-hoy/vista-previa` | UI conectada; generación diaria backend |
| R2.6.2 | Informes | Consultar situaciones del informe histórico | `GET …/informes/{fecha}` | Conectado; no reconstruye el histórico con datos actuales |
| R2.6.3 | Mis notificaciones, Perfil, Baja | Suscribir/re-alta/baja propia explícita | `GET/PUT …/mis-notificaciones; GET/PUT /api/perfil/notificaciones; GET/POST /api/baja/{token}` | Conectado |
| R2.6.4 | Informes | Envío propio y estado de generación/envío | `POST …/informe-de-hoy/enviarme` | UI conectada; correo real no ensayado |
| R2.6.5 | Comunicaciones | Mensaje individual, destinatarios, preview y cola | `POST …/comunicaciones/mensajes` | Conectado con `comunicacion.enviar`; vista previa local antes de enviar; proveedor real no ensayado |
| R2.6.6 | Comunicaciones | Anuncio con previsualización/confirmación | `POST …/comunicaciones/anuncios` | Conectado con `comunicacion.enviar`; vista previa local y confirmación de alcance cuando el backend la exige; proveedor real no ensayado |
| R2.6.7 | Comunicaciones tarea, Personas | Catálogo de siete reglas y vista previa | `GET …/tareas/{tarea_id}/comunicaciones; PUT …/tareas/{tarea_id}/comunicaciones/{evento}; GET/PUT …/comunicaciones-curso/recordatorio-mapeo` | UI conectada; seis reglas de tarea y una de curso; cambio con `comunicacion.enviar`; ejecución automática backend |
| R2.7.1 | Corrección → Repartir | Manual/equitativo/sección/copia, pesos, preview/aplicar y realineación | `POST …/correccion/{entrega}/reparto/{previsualizar,aplicar}; PATCH …/correccion/correctores/{membresia}/peso; POST …/correccion/avisar-profesores` | Conectado; reparto con `correccion.asignar`; conserva criterio/borrador al realinear y ofrece aviso a profesores al ayudante sin permiso de reparto |
| R2.7.2 | Corrección → Mis asignaciones | Bandeja propia y matriz legible | `GET …/correccion; GET …/tareas/{id}/correccion/estado` | Conectado |
| R2.7.3 | Corrección de sujeto | Anterior/siguiente conservando filtros y borrador | `GET …/correccion/{entrega}/{sujeto}` | Conectado; protección de cambios sin guardar también ante Atrás/Adelante |
| R2.7.4 | Corrección de sujeto | Evidencia/SHA, código y versión correcta | `GET …/correccion/{entrega_id}/{sujeto_id}; GET …/versiones/{version_id}/abrir?destino=arbol` | Conectado |
| R2.7.5 | Corrección de sujeto | Rúbrica leída por el backend | `GET …/correccion/{entrega}/{sujeto}` | Conectado; sin edición de rúbricas evaluables |
| R2.7.6 | Corrección, Publicación | Borrador/lista/publicar; conflicto y lote | `PUT …/correccion/{entrega_id}/{sujeto_id}/borrador; POST …/correccion/{entrega_id}/{sujeto_id}/lista; POST …/correccion/{entrega_id}/{sujeto_id}/publicar` | Conectado; borrador/lista requieren `correccion.corregir` y asignación propia, publicación `nota.publicar`; proveedor real no ensayado |
| R2.7.7 | Corrección → Estado | Matriz, contraste Canvas, publicable y motivos | `GET …/tareas/{id}/correccion/estado` | Conectado |
