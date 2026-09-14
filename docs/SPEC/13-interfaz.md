# 13. Interfaz, navegación y experiencia

---

## 13.1 Alcance del capítulo y fuentes

Este capítulo especifica **todo lo que un miembro del equipo docente ve, lee y pulsa**: el árbol de navegación y las URLs, el inventario cerrado de pantallas, los estados vacíos, de carga y de error, los mensajes al usuario, el idioma y el vocabulario, la accesibilidad, el comportamiento en distintas resoluciones y la guía embebida que §2.1 del enunciado exige y §3.1 evalúa.

**Contexto para quien no leyó ningún documento fuente.** La aplicación coordina Canvas y GitHub para que profesores y ayudantes de un curso universitario administren tareas de programación. **Los estudiantes no son usuarios de la aplicación**: no abren ninguna URL de ella, ni siquiera una pública (A-017, A-149, Q-transversal-01). Toda su interacción ocurre en Canvas y en GitHub. Por tanto, cada pantalla de este capítulo está dirigida a un profesor o a un ayudante, salvo las cuatro rutas públicas que se inventarían en §13.20 y que tampoco son para estudiantes.

**Regla de autoridad de este capítulo.** Manda el enunciado; después las actas de reconciliación (reglas `RG-nnn`); después la carta de arquitectura (decisiones `A-nnn`); por último las respuestas de alcance. Donde una respuesta de alcance decía una cosa y una regla `RG` dice otra, se escribe la regla y la respuesta queda anulada; los puntos concretos en que eso ocurre se señalan en el texto.

**Requisitos que este capítulo sirve de forma directa:** R2.1.6, R2.2.6, R2.3.11, R2.5.1, R2.5.5, R2.5.6, R2.5.10, R2.7.2, R2.7.3, R2.7.7. **De forma indirecta, todos los demás**, porque §4 del enunciado establece que «las funcionalidades a las que no se puede acceder en el uso no se consideran cumplidas aunque estén en el código».

**Fuentes normativas de este capítulo:** §16 de la carta (A-151, A-152, A-153, A-154, A-155, A-231, A-232), A-040, A-119, A-124, A-134–A-136, A-150, A-166, A-192, A-220, A-222, A-223; RG-121, RG-125, RG-126, RG-127, RG-128, RG-129, RG-130, RG-133, RG-142, RG-147, RG-148, RG-149, RG-150, RG-151, RG-190, RG-204; lote-23 (Q-transversal-02, 09, 12 a 25), lote-24 (Q-transversal-27, 30, 31, 32, 35, 36, 40, 44) y Q-3.1-04.

---

## 13.2 Los seis principios de interfaz

Estos seis principios son de arquitectura, no de estilo. Toda pantalla los cumple y hay una verificación asociada a cada uno.

| # | Principio | Enunciado normativo | Origen | Cómo se verifica |
|---|---|---|---|---|
| 1 | **Ninguna funcionalidad sin pantalla** | Si algo no tiene pantalla, no está hecho. El inventario de §13.5 es cerrado y completo | A-151 regla 1; §4 del enunciado | Prueba de alcanzabilidad de §13.21 |
| 2 | **Alcanzabilidad por el rol que el requisito nombra** | Una funcionalidad no está cubierta por tener pantalla: está cubierta cuando **la persona que el requisito nombra puede entrar en esa pantalla**. Si R2.6.3 dice «profesores **y ayudantes**», la pantalla no exige un permiso que un ayudante no pueda tener | A-151 regla 0; RG-149 | `test_alcanzabilidad`, parametrizada por perfil |
| 3 | **Ningún estado interno sin representación** | Las **siete** máquinas de estado (A-209, RG-049) tienen todos sus estados visibles con etiqueta en español. Nunca aparece un identificador en mayúsculas en pantalla | A-151 regla 2; A-155 | `test_todo_codigo_tiene_etiqueta` |
| 4 | **Ninguna automatización invisible** | Todo trabajo con efecto visible deja rastro consultable: última sincronización con su hora, bitácora de envíos, historial de versiones y `/operacion`. **Un revisor puede comprobar que la creación progresiva de R2.3.10 ocurrió sola, en lugar de tener que creerlo** | A-151 regla 3 | §13.9 y §13.17; paso 8 del guion de A-159 |
| 5 | **Lo que se ve, funciona** | Nunca se permite comportamiento parcial. Lo que no está listo cae en exactamente una de las tres capas de §13.20: bloqueo con mensaje, oculto por perfil de alcance, o deshabilitado con motivo y fecha | Q-3.1-04; A-156; §4 | Puerta de CI de rutas por perfil (RG-148, RG-161) |
| 6 | **Una sola verdad numérica** | Ninguna pantalla escribe su propio `WHERE` de exclusión. Todas las cifras salen de la capa de consulta única y **toda cifra lleva denominador escrito** | Q-transversal-09; A-088; A-092 | `test_consistencia_de_cifras`; prueba de predicados prohibidos |

**Criterios de aceptación de §13.2**

1. Ejecutar la prueba de alcanzabilidad en los dos modos, `parcial` y `completo`: ambas terminan en verde y ninguna lista de rutas está escrita a mano en la prueba.
2. Buscar en el árbol del frontend y del backend cualquiera de los predicados prohibidos (`Test Student`, `estado <> 'RETIRADO'`, `only_visible_to_overrides`, `es_merge`, `huerfano`, `workflow_state = 'accepted'`) fuera de `backend/app/dominio/universo.py` y de las tres vistas SQL: no hay ninguna coincidencia sin anotación de excepción con motivo escrito.
3. Recorrer la aplicación con datos de `infra/semilla_demo.py` y comprobar que ninguna pantalla muestra una cadena en MAYÚSCULAS_CON_GUION_BAJO.
4. Comprobar que el tablero de una tarea, la tabla de repositorios, Pendientes y el informe diario generado sobre el mismo conjunto de datos devuelven **los mismos números** para las mismas cifras.

---

## 13.3 Árbol de navegación y mapa de URLs

El árbol es cerrado. Toda ruta de la aplicación figura aquí; una ruta que no figure aquí no existe.

### 13.3.1 Árbol completo

```
/acceso                                              —                         R2.1.1, R2.1.2
/invitaciones/{token}                                — (pública)               R2.1.7, R2.1.8
/alcance                                             — (pública)               §3.1, §4
/privacidad                                          — (pública)               R2.6.3
/baja/{token}                                        — (pública)               R2.6.3, R2.6.4
/perfil                                              sesión                    R2.1.1
/cursos                                              sesión                    R2.1.3
/cursos/nuevo                                        curso.administrar         R2.1.4–R2.1.6
/cursos/{id}                                         curso.ver                 Resumen del curso
/cursos/{id}/vinculacion                             curso.administrar         R2.1.4–R2.1.6
/cursos/{id}/pendientes                              curso.ver                 R2.2.6
/cursos/{id}/personas                                curso.ver                 R2.2.1–R2.2.5
/cursos/{id}/personas/{estudiante_id}                curso.ver                 R2.2.1, R2.2.4, R2.5.4
/cursos/{id}/tareas                                  curso.ver                 R2.3.1
/cursos/{id}/tareas/{tid}                            curso.ver                 → /resumen
/cursos/{id}/tareas/{tid}/resumen                    curso.ver                 R2.4.1, R2.4.2, R2.5.1–R2.5.9
/cursos/{id}/tareas/{tid}/entregas                   curso.ver                 R2.3.2, R2.4.1–R2.4.8, R2.5.6
/cursos/{id}/tareas/{tid}/repositorios               curso.ver                 R2.3.4, R2.3.7–R2.3.11
/cursos/{id}/tareas/{tid}/base                       curso.ver / tarea.administrar   R2.3.5, R2.3.6
/cursos/{id}/tareas/{tid}/comunicaciones             curso.ver / comunicacion.enviar R2.6.6, R2.6.7
/cursos/{id}/tareas/{tid}/cierre                     tarea.administrar (rol PROFESOR) A-168, RG-201
/cursos/{id}/tareas/{tid}/repos/{rid}                curso.ver                 R2.5.10
/cursos/{id}/correccion                              curso.ver / correccion.corregir R2.7.1–R2.7.7
/cursos/{id}/equipo                                  curso.ver / equipo.administrar  R2.1.1, R2.1.7–R2.1.9
/cursos/{id}/mis-notificaciones                      curso.ver                 R2.6.3
/cursos/{id}/informes                                curso.ver                 R2.6.1, R2.6.2
/cursos/{id}/comunicaciones                          curso.ver / comunicacion.enviar R2.6.5, R2.6.6
/cursos/{id}/actividad                               curso.ver                 R2.2.1, R2.2.3, R2.4.4
/cursos/{id}/ajustes                                 curso.administrar         R2.1.4, R2.1.5
/operacion                                           rol PROFESOR en algún curso   defensa y demostración
/operacion/invariantes                               rol PROFESOR en algún curso   defensa y demostración
```

### 13.3.2 Notas de reconciliación sobre el árbol

1. **`/cursos/{id}` (Resumen) está registrada en los dos perfiles. [DECISIÓN NUEVA]** RG-148 no la nombra en su lista de rutas registradas bajo `parcial`, pero sí registra siete rutas que cuelgan de ella, y Q-transversal-19 fija para el 16 de septiembre el checklist de progreso, que vive exactamente aquí y que es la pieza de guía que §3.1 evalúa. Se declara registrada bajo los dos perfiles por ser la ruta contenedora del curso; sin ella ninguna pestaña de curso sería alcanzable.
2. **Las pestañas de la tarea son rutas y su registro sigue a los bloques de RG-148. [DECISIÓN NUEVA]** RG-148 registra `/cursos/{id}/tareas/{id}` y enumera los **cinco bloques** que existen bajo `parcial`. La correspondencia entre bloques y pestañas-ruta es ésta, y es la única: bloque 1 (línea de entregas) y bloque 2 (barra de estado de repositorios) → pestaña **Resumen**; bloque 3 (tabla completa de R2.3.11) → pestaña **Repositorios**; bloque 4 (repositorio base) → pestaña **Repositorio base**; bloque 5 (Comunicaciones) → pestaña **Comunicaciones**. Bajo `parcial` **no se registran** las pestañas **Entregas**, **Cierre** ni la vista de repositorio `/repos/{rid}`.
3. **`/cursos/{id}/informes`, `/cursos/{id}/comunicaciones`, `/cursos/{id}/actividad` y `/cursos/{id}/personas/{estudiante_id}` se registran sólo bajo `PERFIL_ALCANCE=completo`. [DECISIÓN NUEVA]** Las actas nombran `GET /api/cursos/{id}/informes` y «la pantalla del histórico» (RG-207), el filtro por motivo en `/cursos/{id}/comunicaciones` (RG-040) y el reintento manual de un `FALLIDO` desde esa misma pantalla (RG-038), pero ninguna de las cuatro figura en la lista de rutas registradas bajo `parcial` de RG-148, y el catálogo de banderas de RG-147 es cerrado en doce. Por tanto: no llevan bandera propia, se registran con el perfil `completo` y una llamada directa bajo `parcial` responde **`404` de enrutado**, nunca una pantalla vacía.
4. **`/operacion` no es una vista global.** Sirve exclusivamente datos de los cursos donde quien mira tiene `membresia_curso` con `estado = ACTIVA` y `rol = PROFESOR` (RG-127, A-232). Quien no tiene ninguna membresía así recibe `404` en todo el prefijo y **la entrada no aparece en su navegación**.
5. **Ningún identificador de la URL es secuencial.** Toda entidad usa clave primaria propia `UUID` v7 y la ruta expone esa clave. Un `UUID` válido de otro curso responde `404`, nunca `403`, para no confirmar su existencia (Q-transversal-27, A-022).

### 13.3.3 Registro de rutas por perfil de alcance

| Ruta | `parcial` (16-sep) | `completo` | Bandera que la libera |
|---|---|---|---|
| `/acceso`, `/perfil`, `/cursos`, `/cursos/nuevo`, `/cursos/{id}`, `/cursos/{id}/vinculacion`, `/cursos/{id}/equipo`, `/cursos/{id}/personas`, `/cursos/{id}/pendientes`, `/cursos/{id}/tareas`, `/cursos/{id}/tareas/{tid}`, `/cursos/{id}/ajustes`, `/operacion` | Registrada | Registrada | — |
| `/invitaciones/{token}`, `/alcance`, `/privacidad` | Registrada (pública) | Registrada (pública) | — |
| `…/tareas/{tid}/resumen`, `…/repositorios`, `…/base`, `…/comunicaciones` | Registrada | Registrada | — |
| `…/tareas/{tid}/entregas` | **No registrada** | Registrada | `versiones_entrega` (4) y `fechas_excepciones` (3) |
| `…/tareas/{tid}/cierre` | **No registrada** | Registrada | `tarea_archivado` (5) |
| `…/tareas/{tid}/repos/{rid}` | **No registrada** | Registrada | `repositorio_timeline` (7) |
| `/cursos/{id}/correccion` | **No registrada** | Registrada desde 05-oct 12:00 | `correccion` (12) |
| `/cursos/{id}/mis-notificaciones`, `/baja/{token}` | **No registrada** | Registrada desde 03-oct 12:00 | `mis_notificaciones` (9) |
| `/cursos/{id}/informes` | **No registrada** | Registrada desde 03-oct 12:00 | `informe_diario` (10) |
| `/cursos/{id}/comunicaciones`, `/cursos/{id}/actividad`, `/cursos/{id}/personas/{eid}` | **No registrada** | Registrada | Sin bandera; sigue al perfil |

**Cómo se aplica.** El perfil vive en la variable de entorno `PERFIL_ALCANCE ∈ {parcial, completo}` y **no en la base de datos**, para que no existan cursos con alcances distintos (RG-147). Se aplica **en el registro de rutas de FastAPI**: ocultar no es cosmético, y una llamada directa a una ruta no registrada responde `404` de enrutado y no un `500` a mitad de una consulta. El frontend consulta **una sola vez** `GET /api/capacidades`, que devuelve `{perfil, banderas[]}`, y construye la navegación con eso: **no existe una segunda lista de módulos en el frontend** (Q-3.1-04, RG-147).

**Criterios de aceptación de §13.3**

1. Arrancar la aplicación con `PERFIL_ALCANCE=parcial` y pedir `/cursos/{id}/correccion`, `/cursos/{id}/mis-notificaciones`, `/cursos/{id}/tareas/{tid}/repos/{rid}`, `/cursos/{id}/informes`, `/cursos/{id}/actividad` y `/cursos/{id}/comunicaciones`: las seis responden `404` de enrutado y ninguna aparece en la navegación.
2. Arrancar con `PERFIL_ALCANCE=completo` y comprobar que las mismas seis responden `200` y aparecen en la navegación.
3. Enumerar las rutas registradas del enrutador real y compararlas con la tabla de §13.3.3: no sobra ni falta ninguna en cada perfil.
4. Comprobar que la navegación del frontend se construye únicamente desde `GET /api/capacidades` y que no existe ninguna lista de módulos codificada en el frontend.
5. Pedir cualquier ruta de curso con un `UUID` de otro curso: responde `404`, no `403`.

---

## 13.4 Reglas de navegación y de contexto

### 13.4.1 Las cuatro reglas

| # | Regla | Enunciado normativo |
|---|---|---|
| 1 | **La pestaña es la ruta** | Cada pestaña de curso y de tarea tiene su propia URL: es enlazable, marcable y compartible entre miembros del equipo docente. **No existe estado de pestaña en memoria** |
| 2 | **`/cursos/{id}` es el Resumen y redirige a Pendientes cuando hay algo bloqueante** | El Resumen muestra cabecera, checklist de progreso, indicador de sincronización, «N de M estudiantes con cuenta verificada» y accesos a las tareas. **Redirige a `/cursos/{id}/pendientes` si existe al menos una incidencia abierta de severidad `BLOQUEANTE`.** La redirección es visible en la barra de direcciones, la pestaña Resumen queda marcada y accesible con un clic, y un aviso de una línea dice «te llevamos a Pendientes porque hay N cosas bloqueadas». **Nunca atrapa al usuario** |
| 3 | **Migas de pan y cabecera de curso persistente** | Bajo el curso, migas con la forma `Mis cursos / <curso> / <tarea> / <repositorio>`. La cabecera de curso es persistente en todas las vistas por debajo del curso y su contenido es el de §13.4.2 |
| 4 | **El contexto vive en la URL, no en el componente** | Pestaña activa, filtros, orden y página viajan como parámetros de consulta (`?estado=DEGRADADO&orden=nombre&pagina=2`). Volver atrás, adelante o pegar el enlace reproduce **exactamente** la misma vista. Lo único que se guarda en `localStorage` es si el panel «¿Cómo funciona esta pantalla?» está abierto o cerrado, que es una conveniencia por persona sin valor compartido |

### 13.4.2 Contenido obligatorio de la cabecera de curso

La cabecera de curso aparece en todas las rutas bajo `/cursos/{id}` y muestra, siempre y en este orden:

| Elemento | Qué dice | Origen |
|---|---|---|
| Nombre del curso, código y período | Texto plano | A-108 |
| Estado de vinculación | Canvas y GitHub, con su estado | A-041, A-192 |
| **Identidad de escritura en Canvas** | «La aplicación escribe en Canvas como *nombre del titular*» — **siempre visible, sin pasar el cursor** | A-036, Q-transversal-29 |
| Indicador de sincronización compacto | El **más antiguo** de los ámbitos relevantes para la pantalla actual (§13.8.3) | Q-transversal-20 |
| Contador de Pendientes | Número de incidencias abiertas, enlazado a `/cursos/{id}/pendientes` | A-150 |
| «N de M estudiantes con cuenta verificada» | Cifra con denominador escrito | A-150, Q-transversal-09 |
| Buscador del curso | Por nombre, `canvas_user_id` o login de GitHub, acotado al curso del contexto | Q-transversal-15 |
| **Banda roja persistente** | Si la credencial de Canvas es `INVALIDA`: qué falta, quién puede arreglarlo y enlace a la pantalla de sustitución | A-036 paso 5 |
| **Banda ámbar permanente** | Si `curso.comunicaciones_salientes = 'SUSPENDIDAS'` o `curso.modo_escritura = 'SOLO_LECTURA'`, con el motivo escrito | RG-037 |
| **Advertencia de zona discrepante** | Si `Course.time_zone` difiere de la zona configurada en el curso | A-152 |
| **Banda de alcance** | Sólo mientras quede alguna bandera activa; textos y régimen en §13.20.2 | RG-151 |

### 13.4.3 Congelación de rutas

Las rutas se congelan con la entrega parcial. Cualquier cambio posterior deja una **redirección permanente**, porque el informe diario ya enviado contiene enlaces profundos a rutas concretas (A-131) y un enlace roto en un correo antiguo es un fallo que no se puede reparar desde la aplicación.

**Criterios de aceptación de §13.4**

1. Aplicar un filtro y un orden en la tabla de repositorios, copiar la URL, abrirla en otra sesión del navegador: la vista se reproduce idéntica.
2. Pulsar «atrás» tras cambiar de pestaña dentro de una tarea: se vuelve a la pestaña anterior con sus filtros.
3. Entrar a `/cursos/{id}` en un curso con al menos una incidencia `BLOQUEANTE` abierta: la barra de direcciones muestra `/cursos/{id}/pendientes` y un aviso de una línea explica por qué; pulsar la pestaña Resumen devuelve a `/cursos/{id}` sin volver a redirigir en esa navegación.
4. Comprobar en cualquier pantalla de curso que la cabecera nombra la identidad de Canvas con la que se escribe, sin pasar el cursor por ningún elemento.
5. Invalidar la credencial de Canvas del curso en el entorno de ensayo: la banda roja aparece en **todas** las rutas del curso y enlaza a la pantalla de sustitución.

---

## 13.5 Inventario de pantallas

Inventario cerrado. Cada fila declara ruta, permiso de lectura, permiso de acción, contenido y requisitos que sirve.

### 13.5.1 Pantallas de sesión

| Pantalla | Ruta | Leer | Actuar | Contenido | Requisitos |
|---|---|---|---|---|---|
| **Acceso** | `/acceso` | — | — | Entrada con Google OIDC, `prompt=select_account` siempre; pantalla de confirmación del camino degradado de A-018 regla 3 | R2.1.1, R2.1.2 |
| **Mi perfil** | `/perfil` | sesión | sesión | Nombre, correo, identidades de Canvas vinculadas, **bloque «Mi cuenta de GitHub»** con el consentimiento literal de RG-133 y su casilla, sesiones abiertas y «cerrar sesión en todos mis dispositivos», «regenerar mis enlaces de baja» (capa 3 hasta el 03-oct), **cerrar mi cuenta** | R2.1.1 |
| **Mis cursos** | `/cursos` | sesión | `curso.administrar` para crear | Cursos del usuario con su rol y su estado | R2.1.3 |
| **Asistente de vinculación** | `/cursos/nuevo`, `/cursos/{id}/vinculacion` | `curso.administrar` | `curso.administrar` | Cuatro pasos con estado persistido: datos del curso; Canvas (pegar token propio y **elegir el curso de la lista**, nunca escribir el identificador); GitHub (instalar la App); verificación con el checklist de **21 ítems** y **cinco resultados** (A-192), asíncrono con sondeo (§13.9.2), más el botón separado de prueba de escritura | R2.1.4, R2.1.5, R2.1.6 |
| **Resumen del curso** | `/cursos/{id}` | `curso.ver` | según acción | Cabecera, **checklist de progreso de seis pasos derivado de datos** (§13.17.1), indicador de sincronización, «N de M estudiantes con cuenta verificada», accesos a tareas | R2.1.3 |
| **Equipo** | `/cursos/{id}/equipo` | `curso.ver` | `equipo.administrar` | Profesores y ayudantes con su estado, alta por invitación nominal a dirección `gmail.com`, **formulario con las siete casillas configurables** (§13.5.5), edición de permisos, cambio de rol, retiro y reincorporación, invitaciones pendientes y su revocación, historial de cambios, quién está suscrito al informe, texto permanente del consentimiento de RG-133 | R2.1.1, R2.1.7, R2.1.8, R2.1.9 |
| **Pendientes** | `/cursos/{id}/pendientes` | `curso.ver` | según acción | Todo lo que falta, en un solo sitio: los cuatro bloques de A-150 con el componente `ListaPendientes` (§13.12), exportación CSV y **botón manual de recordatorio de mapeo** (`comunicacion.enviar`, tope 1 por estudiante y día) | R2.2.6 |
| **Personas** | `/cursos/{id}/personas` | `curso.ver` | `mapeo.editar`, `comunicacion.enviar` | Estudiantes con su sección, conjuntos de grupos y grupos con su `workflow_state`, cuentas de GitHub vinculadas con su origen y evidencia, tarea de registro con su enlace, interruptor de `recordatorio_mapeo`, importación CSV, edición manual del mapeo, correo y `sis_user_id` **enmascarados** con botón «mostrar» que queda en `bitacora` | R2.2.1–R2.2.5 |
| **Ficha del estudiante** | `/cursos/{id}/personas/{estudiante_id}` | `curso.ver` | según acción | Nueve bloques plegables: identidad y matrículas; grupos con historial; cuenta de GitHub con **toda** su historia y evidencia; repositorios por tarea; versiones de entrega; actividad atribuida y commits sin atribuir; comunicaciones con su estado y exclusiones; notas publicadas; incidencias. Conmutador «incluir tareas archivadas», apagado por defecto. **Sin una sola llamada a Canvas ni a GitHub** | R2.2.1, R2.2.4, R2.5.4, R2.6.5, R2.7.7 |
| **Tareas** | `/cursos/{id}/tareas` | `curso.ver` | `tarea.administrar` | Lista de tareas con su estado y su modalidad; crear tarea con **vista previa en vivo del nombre de repositorio** que resultará; duplicar tarea con previsualización de qué se copia y qué no | R2.3.1 |
| **Corrección** | `/cursos/{id}/correccion` | `curso.ver` | `correccion.corregir`, `correccion.asignar`, `nota.publicar` | Tres pestañas: **Mis asignaciones** (vista por defecto del ayudante), **Estado de la entrega** (siempre visible, matriz nominal completa), **Repartir** (sólo con `correccion.asignar`). Panel izquierdo con el enlace por SHA, rúbrica leída en vivo, publicación de nota | R2.7.1–R2.7.7 |
| **Mis notificaciones** | `/cursos/{id}/mis-notificaciones` | `curso.ver` | `curso.ver` | **Mi** suscripción al informe diario y mis preferencias de aviso. Nunca la de otro | R2.6.3 |
| **Informes** | `/cursos/{id}/informes` | `curso.ver` | `curso.ver` | Histórico del informe diario con sus cinco secciones, vista previa del de hoy, botón «Enviarme el informe de hoy ahora», y la declaración «el informe diario de este curso se genera desde el DD-MM-YYYY» | R2.6.1, R2.6.2, R2.6.4 |
| **Comunicaciones del curso** | `/cursos/{id}/comunicaciones` | `curso.ver` | `comunicacion.enviar`, `curso.administrar` para los frenos | Bitácora de envíos con canal, plantilla, destinatario, estado y motivo; **pantalla «por qué no salió»** que llama a la misma función `guardas_outbox`; reintento manual de un `FALLIDO`; filtro por motivo; interruptores `comunicaciones_salientes` y `modo_escritura` | R2.6.5, R2.6.6 |
| **Actividad** | `/cursos/{id}/actividad` | `curso.ver` | — | Registro visible de los cambios detectados por cada sincronización, agrupados por ciclo y por día en la zona del curso, con `antes → despues`; filtros por tipo, fecha y sujeto; atajo «sólo cambios de fecha»; exportación CSV; **sin purga** | R2.2.1, R2.2.3, R2.4.4 |
| **Ajustes del curso** | `/cursos/{id}/ajustes` | `curso.administrar` | `curso.administrar` | Credenciales de Canvas con titular, huella, estado y orden de respaldo; «retirar mi credencial» y «hacer operativa la mía»; revinculación; zona horaria; `umbral_dias_sin_actividad` y `umbral_desbalance_pct` con su aviso de impacto; canal de comunicación activo; diagnóstico; **«Archivar el curso»** con confirmación de nivel 3 e inventario CSV | R2.1.4, R2.1.5 |
| **Operación** | `/operacion`, `/operacion/invariantes` | rol `PROFESOR` activo | rol `PROFESOR` activo | Un solo inventario de secciones, cada una etiquetada `CURSO` o `DESPLIEGUE` (§13.5.4) | Defensa y demostración |

### 13.5.2 Pestañas de la tarea

`/cursos/{id}/tareas/{tid}` redirige a `/resumen`.

| Pestaña | Ruta | Leer | Actuar | Contenido | Requisitos |
|---|---|---|---|---|---|
| **Resumen** | `…/resumen` | `curso.ver` | — | **Bloque 1 · Línea de entregas**: una fila por entrega con su tipo, su fecha de cierre **con zona escrita**, cuántas fechas distintas hay, la cuenta atrás y el **estado de la entrega** de la enumeración derivada de nueve valores de A-220, con sus contadores obligatorios. **Bloque 2 · Barra de estado de repositorios**: recuento por estado, con `OPERATIVO` y `DEGRADADO` **en columnas separadas** y `DEGRADADO` en su columna ámbar «funcionando, incompleto», más el recuento de sujetos activos y desactivados con su motivo. **Bloque 3 · Tarjetas de atención**: «sin actividad reciente» y «sin participación» con sus tres causas. **Bloque 4 · Serie temporal de commits por día** con selector de período por entrega. **Bloque 5 · Métricas adicionales y comparación intragrupo**. Panel plegado «Cambios recientes» de los últimos siete días acotado a la tarea | R2.4.1, R2.4.2, R2.5.1–R2.5.9 |
| **Entregas** | `…/entregas` | `curso.ver` | `tarea.administrar` | Vincular tareas de Canvas como entregas; tipo `PARCIAL`/`FINAL` y orden; panel de excepciones por estudiante y por grupo; columna «estado de captura» con el `commit_sha`, el `tag_estado` y el enlace por SHA; desvincular mientras no haya versión capturada | R2.3.2, R2.3.3, R2.4.1–R2.4.8, R2.5.6 |
| **Repositorios** | `…/repositorios` | `curso.ver` | `tarea.administrar` | **Tabla completa de R2.3.11**: una fila por sujeto con nombre del repositorio, URL, estado traducido, **motivo por fila**, estado del acceso del estudiante, acceso docente, última actividad. Paginada en servidor, ordenable, filtrable, exportable a CSV. Acciones por fila y en lote con su confirmación | R2.3.4, R2.3.7–R2.3.11 |
| **Repositorio base** | `…/base` | `curso.ver` | `tarea.administrar` | Crear el repositorio base, subir, reemplazar, renombrar y borrar archivos iniciales, estado del base con sus cinco valores y `LISTO` como guarda de activación | R2.3.5, R2.3.6 |
| **Comunicaciones** | `…/comunicaciones` | `curso.ver` | `comunicacion.enviar` | Los **siete** eventos de A-130 con su interruptor, su alcance y su plantilla; previsualización del texto que recibe el estudiante y **recuento de destinatarios antes de confirmar**; lista de excluidos con su motivo | R2.6.6, R2.6.7 |
| **Cierre** | `…/cierre` | `tarea.administrar` | `tarea.administrar` **y rol `PROFESOR`** | Cerrar la tarea; archivar los repositorios con las cinco guardas de A-197; desarchivar | A-168, A-197, RG-201 |
| **Repositorio** | `…/repos/{rid}` | `curso.ver` | — | Timeline de tres capas: todos los commits agrupados por día en la zona del curso, cada uno con su regla de atribución y su etiqueta de por qué no cuenta; eventos de ciclo de vida del repositorio; marcas de cada entrega con el commit capturado resaltado. El enlace a GitHub **no se pinta** si el acceso docente no está `CONCEDIDO`: en su lugar, el motivo y el botón de reintento | R2.5.10, R2.4.7 |

### 13.5.3 Pantallas públicas sin sesión

| Pantalla | Ruta | Contenido | Requisitos |
|---|---|---|---|
| **Aceptar invitación** | `/invitaciones/{token}` | Rol, permisos que se conceden y **el texto literal del consentimiento de RG-133** sobre el botón «Aceptar la invitación». Muestra el correo destinatario **enmascarado**. Es la pantalla donde el evaluador acepta su invitación | R2.1.7, R2.1.8, §3.1 |
| **Alcance** | `/alcance` | La tabla de A-157 requisito a requisito, con tres columnas —requisito, qué se puede hacer hoy, cuándo llega lo que falta— **generada desde el catálogo de banderas**, más la fecha de inicio del histórico del informe diario | §3.1, §4 |
| **Privacidad** | `/privacidad` | Qué datos se tratan, con qué fin, quién los ve, dónde viven, hasta cuándo, y cómo se dan de baja los avisos. Contacto del equipo | R2.6.3 |
| **Baja del informe** | `/baja/{token}` | Página de confirmación que nombra curso y dirección, con dos botones —«darme de baja» y «seguir suscrito»—; tras aplicar, ofrece «volver a suscribirme». **El `GET` no cambia nada**; sólo el `POST` | R2.6.3, R2.6.4 |

### 13.5.4 Inventario de secciones de `/operacion`

Cada sección declara si es de **curso** —y entonces va filtrada por `curso_id IN (cursos del solicitante)`, sin excepción— o de **despliegue**.

| Sección | Ámbito | Contenido |
|---|---|---|
| Colas y trabajos por estado y por motivo de cancelación | CURSO | Recuentos por estado de la máquina 6 |
| Trabajos en `REQUIERE_ATENCION` | CURSO | Con su **error literal** y botón de reintento |
| Últimos webhooks recibidos | CURSO | Incluye el contador de eventos `IGNORADO_AJENO` de las últimas 24 h |
| Última ejecución de cada uno de los **31** trabajos periódicos | CURSO | Un trabajo cuya bandera no está retirada **no aparece como vencido** |
| Los cuatro cubos de `presupuesto_api` | CURSO | Tres de GitHub por instalación, uno de Canvas por curso |
| Cola de etiquetas con su ritmo | CURSO | — |
| **Techo de frescura calculado y su recuento** | CURSO | «techo garantizado: 45 min · 600 repositorios en ingesta · 200 por ciclo cada 15 min». **Nunca un número escrito a mano** |
| `403` de Canvas clasificados | CURSO | Con su cuerpo literal |
| Capacidades degradadas | CURSO | Con su motivo y su fecha |
| Cerrojos tomados por proveedor | CURSO | — |
| Cursos con lecturas de *rulesets* apagadas | CURSO | — |
| **Bandeja «Mensajes retenidos»** y cadena `reemplaza_a_id` | CURSO | Con la etiqueta del motivo, nunca el código |
| Cola de publicaciones detenidas | CURSO | — |
| Violaciones de invariantes | CURSO | — |
| Fila `DENEGACIONES_ANOMALAS` | CURSO | — |
| **Desfase declarado frente a medido, por arista** | CURSO | Las 18 aristas de la matriz de derivados |
| Latencias p50/p95 por endpoint frente a los objetivos declarados | CURSO | — |
| Consumo del día de la cuota de correo **por reserva** | DESPLIEGUE | — |
| Latido del planificador | DESPLIEGUE | — |
| Revisión de esquema desplegada | DESPLIEGUE | — |
| Tamaño de la base | DESPLIEGUE | — |
| Bloque de rotación de claves | DESPLIEGUE | — |

`GET /api/operacion` devuelve las secciones **etiquetadas `CURSO` o `DESPLIEGUE`**, y **todo lo que muestra es dato medido y persistido, nunca una estimación escrita en el código**.

### 13.5.5 El formulario de permisos, en detalle

Es la pantalla donde se cumple R2.1.8, y su forma exacta está fijada por RG-121.

| Grupo | Permisos | Cómo se muestran |
|---|---|---|
| **Implícitos e irrevocables** | `curso.ver`, `correccion.corregir` | Marcados y fijos, con la nota «siempre incluidos» |
| **Configurables y concedibles (cinco)** | `tarea.administrar`, `mapeo.editar`, `correccion.asignar`, `nota.publicar`, `comunicacion.enviar` | Casillas editables |
| **Configurables y NO CONCEDIBLES (dos)** | `curso.administrar`, `equipo.administrar` | Casillas **deshabilitadas con el motivo escrito en el propio control**: «da acceso a la credencial de Canvas del curso» y «permitiría concederse a sí mismo el resto» |

La expresión **«los siete permisos concedibles» queda prohibida** en la interfaz, en la especificación y en el texto de la entrega: se escribe «los cinco concedibles» o «los siete configurables», que son cosas distintas. El conjunto preparado se llama **«Gestión completa (los cinco concedibles)»**. El servidor rechaza con `422` todo array de permisos de rol `AYUDANTE` que contenga una NO CONCEDIBLE.

**Criterios de aceptación de §13.5**

1. Recorrer el inventario pantalla por pantalla con `PERFIL_ALCANCE=completo` y comprobar que cada fila existe, carga con datos de `semilla_demo` y muestra el contenido declarado.
2. Entrar como ayudante sin permisos configurables y comprobar que alcanza `/cursos/{id}/mis-notificaciones`, `/cursos/{id}/pendientes`, `/cursos/{id}/personas`, el tablero de tarea y la pestaña «Estado de la entrega» de Corrección.
3. Abrir el formulario de permisos: las dos casillas NO CONCEDIBLES aparecen deshabilitadas con su motivo visible sin pasar el cursor; el conjunto preparado se llama «Gestión completa (los cinco concedibles)»; enviar por API un array con `curso.administrar` para un ayudante devuelve `422`.
4. Entrar a `/operacion` como profesor de un solo curso: ninguna sección de curso muestra datos de otro curso; las cinco secciones de despliegue se muestran sin filtrar.
5. Entrar a `/operacion` con un usuario sin ninguna membresía `ACTIVA` de rol `PROFESOR`: responde `404` y la entrada no aparece en la navegación.
6. Abrir la ficha de un estudiante y comprobar, con el registro de red del navegador, que no se produce ninguna llamada a Canvas ni a GitHub.

---

## 13.6 Puerta de entrada por requisito

Cada requisito tiene **una** puerta de entrada nombrada. Si un requisito tuviera dos candidatas, esta tabla decide.

| Requisito | Puerta de entrada | Rol mínimo que la alcanza |
|---|---|---|
| R2.1.1 | `/perfil` (cuenta propia) y `/cursos/{id}/equipo` (miembros del curso) | Profesor |
| R2.1.2 | `/acceso` | — |
| R2.1.3 | `/cursos` y `/cursos/{id}` | Ayudante (lectura) / Profesor (administrar) |
| R2.1.4 | `/cursos/{id}/vinculacion` paso 2 y `/cursos/{id}/ajustes` | Profesor |
| R2.1.5 | `/cursos/{id}/vinculacion` paso 3 | Profesor |
| R2.1.6 | `/cursos/{id}/vinculacion` paso 4, checklist de 21 ítems | Profesor |
| R2.1.7 | `/cursos/{id}/equipo` + `/invitaciones/{token}` | Profesor |
| R2.1.8 | `/cursos/{id}/equipo`, formulario de permisos | Profesor |
| R2.1.9 | `/cursos/{id}/equipo`, retiro | Profesor |
| R2.2.1 | `/cursos/{id}/personas` | Ayudante |
| R2.2.2 | `/cursos/{id}/personas`, columna Sección | Ayudante |
| R2.2.3 | `/cursos/{id}/personas`, bloque Grupos | Ayudante |
| R2.2.4 | `/cursos/{id}/personas`, bloque Cuentas de GitHub | Ayudante |
| R2.2.5 | `/cursos/{id}/personas` (tarea de registro, edición manual, CSV) y `/cursos/{id}/pendientes` (recordatorio manual) | Ayudante con `mapeo.editar` |
| R2.2.6 | `/cursos/{id}/pendientes` | Ayudante |
| R2.3.1 | `/cursos/{id}/tareas` | Ayudante con `tarea.administrar` |
| R2.3.2 | `…/tareas/{tid}/entregas` | Ayudante con `tarea.administrar` |
| R2.3.3 | `…/tareas/{tid}/entregas`, modalidad congelada y bloqueo de capa 1 | Ayudante con `tarea.administrar` |
| R2.3.4 | `…/tareas/{tid}/repositorios` | Ayudante |
| R2.3.5 | `…/tareas/{tid}/base` | Ayudante con `tarea.administrar` |
| R2.3.6 | `…/tareas/{tid}/base` | Ayudante con `tarea.administrar` |
| R2.3.7 | `…/tareas/{tid}/repositorios` | Ayudante |
| R2.3.8 | `…/tareas/{tid}/repositorios`, más la vista previa del nombre en el alta de curso y de tarea | Ayudante |
| R2.3.9 | `…/tareas/{tid}/repositorios`, columna de acceso del estudiante | Ayudante |
| R2.3.10 | `…/tareas/{tid}/repositorios` (contador que avanza solo) y `/operacion` (cola trabajando) | Ayudante |
| R2.3.11 | `…/tareas/{tid}/repositorios` — **la tabla completa, con motivo por fila** | Ayudante |
| R2.3.12 | `…/tareas/{tid}/comunicaciones` (evento `repositorio_disponible`) | Ayudante con `comunicacion.enviar` |
| R2.4.1 | `…/tareas/{tid}/resumen`, bloque 1 | Ayudante |
| R2.4.2 | `…/tareas/{tid}/resumen`, bloque 1, «N fechas distintas» | Ayudante |
| R2.4.3 | `…/tareas/{tid}/entregas`, panel de excepciones | Ayudante |
| R2.4.4 | `…/tareas/{tid}/entregas` y `/cursos/{id}/actividad`, atajo «sólo cambios de fecha» | Ayudante |
| R2.4.5 | `…/tareas/{tid}/entregas`, columna «estado de captura» | Ayudante |
| R2.4.6 | `…/tareas/{tid}/entregas`, una fila por entrega | Ayudante |
| R2.4.7 | `…/tareas/{tid}/repos/{rid}`, marcas de entrega sobre el eje | Ayudante |
| R2.4.8 | `…/tareas/{tid}/entregas` (enlace por SHA) y `/cursos/{id}/correccion` (panel izquierdo) | Ayudante |
| R2.5.1 | `…/tareas/{tid}/resumen` | Ayudante |
| R2.5.2 | `…/tareas/{tid}/resumen`, bloque 4 | Ayudante |
| R2.5.3 | `…/tareas/{tid}/resumen`, bloque 3 | Ayudante |
| R2.5.4 | `…/tareas/{tid}/resumen`, bloque 3 | Ayudante |
| R2.5.5 | `…/tareas/{tid}/resumen`, bloque 2, con enlace a la tabla completa | Ayudante |
| R2.5.6 | `…/tareas/{tid}/resumen`, bloque 1 | Ayudante |
| R2.5.7 | `…/tareas/{tid}/resumen`, selector de período por entrega | Ayudante |
| R2.5.8 | `…/tareas/{tid}/resumen`, bloque 5 | Ayudante |
| R2.5.9 | `…/tareas/{tid}/resumen`, bloque 5 | Ayudante |
| R2.5.10 | `…/tareas/{tid}/repos/{rid}` | Ayudante |
| R2.6.1 | `/cursos/{id}/informes` | Ayudante |
| R2.6.2 | `/cursos/{id}/informes`, secciones 1 y 3 | Ayudante |
| R2.6.3 | `/cursos/{id}/mis-notificaciones` y `/baja/{token}` | Ayudante |
| R2.6.4 | El correo, más `/cursos/{id}/informes` como respaldo cuando el correo falla | Ayudante |
| R2.6.5 | `…/tareas/{tid}/comunicaciones` y la ficha del estudiante | Ayudante con `comunicacion.enviar` |
| R2.6.6 | `…/tareas/{tid}/comunicaciones` | Ayudante con `comunicacion.enviar` |
| R2.6.7 | `…/tareas/{tid}/comunicaciones`, los siete interruptores | Ayudante con `comunicacion.enviar` |
| R2.7.1 | `/cursos/{id}/correccion` → Repartir | Ayudante con `correccion.asignar` |
| R2.7.2 | `/cursos/{id}/correccion` → Mis asignaciones (vista por defecto) | Ayudante |
| R2.7.3 | `/cursos/{id}/correccion`, barra «N de M», atajos de teclado, «siguiente sin corregir» | Ayudante |
| R2.7.4 | `/cursos/{id}/correccion`, panel izquierdo con el enlace por SHA | Ayudante |
| R2.7.5 | `/cursos/{id}/correccion`, rúbrica leída en vivo | Ayudante |
| R2.7.6 | `/cursos/{id}/correccion`, publicar nota | Ayudante con `nota.publicar` |
| R2.7.7 | `/cursos/{id}/correccion` → Estado de la entrega, matriz nominal completa | Ayudante |

**Precisión sobre R2.7.7.** La matriz nominal completa —sujeto, entrega, corrector asignado, estado de corrección, versión vigente y si está publicada—, los tres agregados, el doble contador «N de M corregidas en la aplicación · K de M con nota en Canvas · comprobado hace X», los filtros y la exportación CSV **se leen con `curso.ver`**. Lo acotado por propiedad es sólo el **trabajo**: abrir la corrección en modo edición, ver el borrador de otro corrector y ver sus notas internas y banderas. Sobre una fila ajena el botón principal es **«ver»**, no «corregir» (RG-125).

**Criterios de aceptación de §13.6**

1. Ejecutar la prueba de alcanzabilidad parametrizada por perfil: para cada requisito de esta tabla, el rol de menor privilegio que el enunciado nombra entra en su puerta de entrada sin recibir `403`.
2. Entrar como ayudante sin `correccion.asignar` a `/cursos/{id}/correccion`: la pestaña «Estado de la entrega» está visible y muestra la matriz nominal completa con los tres agregados y el doble contador; la pestaña «Repartir» no aparece; sobre una fila ajena el botón es «ver» y abrir su corrección en modo edición devuelve `403`.
3. Comprobar que ningún requisito de la tabla tiene dos puertas de entrada declaradas y que la puerta declarada existe en el inventario de §13.5.

---

## 13.7 Catálogo cerrado de componentes transversales

Ningún texto, formato ni comportamiento de esta lista se reimplementa por pantalla. Añadir un componente a esta lista es una decisión que se escribe.

| Componente | Qué garantiza | No admite |
|---|---|---|
| `Fecha(instante)` | Emite `dd-MM-yyyy HH:mm (Zona)` en la zona del curso | **Renderizar sin zona** |
| `FechaRelativa(instante)` | «hace 4 min», «ayer a las 18:03», con el absoluto en el `title` y en el texto que lee un lector de pantalla | Formato relativo sin absoluto asociado |
| `Numero(valor)` | `Intl.NumberFormat('es-CL')`: coma decimal, punto de miles | Reformatear una **nota** de Canvas |
| `Cifra(numerador, denominador, desglose)` | «37 de 40» más el nombre del denominador y su desglose en un *popover* accesible por teclado | **Renderizar un numerador sin denominador**: falla en desarrollo |
| `Estado(codigo)` | Icono SVG en línea + **etiqueta textual en español** + color como tercer canal | Comunicar un estado sólo por color; emojis |
| `SelloAntiguedad(sincronizado_en, techo_garantizado)` | «actualizado hace X · techo N»; ámbar si `ahora − sincronizado_en > techo`, rojo si lo dobla | Que una pantalla escriba una antigüedad a mano |
| `IndicadorSincronizacion(ambito)` | Los seis estados de §13.8.3 con su texto exacto y su acción. **Consume `SelloAntiguedad` y no calcula antigüedad por su cuenta** [DECISIÓN NUEVA] | Mostrar una fecha sin decir de qué ámbito es |
| `EstadoVacio(codigo)` | Título, explicación de una frase con la causa, acción única y marca de si es problema, leídos del archivo único de mensajes | Estado vacío genérico |
| `Error(codigo, detalle)` | Explicación en español, acción sugerida, **quién puede resolverlo**, y desplegable «Detalles técnicos» cerrado por defecto con código HTTP, mensaje literal, endpoint, `correlacion_id` y fecha con zona, con botón de copiado | Mostrar un mensaje crudo de la API sin explicación; ocultar el literal |
| `ListaPendientes(filtro)` | Filas de forma fija derivadas del tipo de incidencia, agrupación por tipo con recuento, acción por fila y por grupo | Texto libre por incidencia |
| `Confirmacion(nivel, efectos)` | Las tres formas de §13.13, con el texto de efectos derivado del **plan de efectos** del servidor | Redactar los efectos a mano en cada pantalla |
| `TablaPaginada` | Paginación en servidor, orden estable, filtro y búsqueda en servidor, «mostrando 1–50 de 213», selector de tamaño y **exportar CSV del conjunto completo** | Virtualización en cliente |
| `TablaAncha` | Contenedor con `overflow-x: auto`, **primera columna fija** e indicador de que hay más columnas | Que el `body` se desplace en horizontal |
| `HtmlSaneado` | Único lugar donde existe `dangerouslySetInnerHTML`; sólo acepta contenido con la marca de saneado del servidor | Renderizar HTML no marcado |
| `AccionNoDisponible` | Control presente, deshabilitado, con el motivo **visible sin pasar el cursor** y la fecha comprometida | La palabra «próximamente» |
| `Tooltip(termino)` | Glosa y definición desde el mapa único `término → glosa + definición`, accesible por teclado y por lector de pantalla | Definiciones escritas dos veces |
| `PanelComoFunciona(pantalla)` | Tres párrafos fijos: qué hace esta pantalla, de dónde vienen los datos y cuánta antigüedad pueden tener, y **qué NO hace la aplicación aquí** | Contenido genérico compartido entre pantallas |
| `BloqueSeConfiguraFuera(enlace, accion_de_sync)` | Frase «Esto se configura en Canvas», enlace profundo exacto y botón **«Ya lo hice, sincronizar»** que **encola** | Llamar a una API dentro de la petición |
| `ChecklistProgreso` | Seis pasos derivados de datos persistidos, con el paso pendiente más alto resaltado | Casillas que alguien marca a mano |
| `BandaAlcance` | Los dos textos de §13.20.2, con visibilidad derivada de `GET /api/capacidades` | Interruptor manual para ocultarla |

**Regla de tipografía de identificadores técnicos.** Login de GitHub, nombre de repositorio, URL, SHA y huella de credencial se muestran en **tipografía monoespaciada, con botón de copiado, sin traducir ni maquillar** (A-155). El mensaje de un commit truncado se muestra con elipsis y el `title` con la primera línea completa.

**Criterios de aceptación de §13.7**

1. Intentar renderizar `Cifra` sin denominador en el entorno de desarrollo: falla de forma visible.
2. Intentar renderizar `Fecha` sin zona: falla de forma visible.
3. Buscar `dangerouslySetInnerHTML` en `frontend/src/`: la única coincidencia está dentro de `HtmlSaneado`; la regla de ESLint y la prueba asociada fallan si aparece fuera.
4. Buscar en el frontend cualquier cálculo de antigüedad que no pase por `SelloAntiguedad`: la prueba de interfaz falla si una pantalla pinta una antigüedad sin usar el componente.
5. Comprobar que ningún archivo del frontend contiene la palabra «próximamente».

---

## 13.8 Cifras, denominadores y antigüedad del dato

### 13.8.1 Toda cifra lleva denominador

Formato fijo: **«37 de 40»** más el nombre del denominador y un desglose al pasar el cursor o al abrir el *popover* con el teclado:

> «37 de 40 **sujetos activos de la tarea** · 40 estudiantes con matrícula activa o invitada · 2 desactivados: 1 sin visibilidad, 1 sin grupo · 1 estudiante de prueba excluido»

| Cifra | Denominador canónico | Exclusiones que aplica |
|---|---|---|
| Estudiantes del curso | Matrículas `active` + `invited` | Estudiante de prueba de Canvas |
| Sujetos de la tarea | `v_sujeto_tarea WHERE activo` | Anteriores + sin visibilidad + grupo sin integrante `accepted` |
| Repositorios de la tarea | Sujetos activos | Ídem; `OPERATIVO` y `DEGRADADO` **en columnas separadas** |
| Cuentas de GitHub verificadas | Estudiantes del curso, **no** sujetos | Estudiante de prueba |
| Sujetos por corregir de una entrega | Sujetos activos **con fecha efectiva vigente para esa entrega** | Los no visibles para esa entrega |
| Destinatarios de una comunicación | Estudiantes con matrícula `active`/`invited` | Inactivos, concluidos, borrados |

**`DEGRADADO` nunca se suma a la columna de problemas.** Va en su propia columna ámbar, «funcionando, incompleto», con el motivo desglosado (A-092).

### 13.8.2 Un indicador no se pronuncia sobre una ventana más corta que su umbral

Si la ventana observada de un repositorio —que arranca en `max(repositorio.listo_en, curso.ingesta_actividad_desde)`— es **más corta que el umbral de inactividad**, el repositorio **no se cuenta entre los inactivos en ninguna parte** —ni en el tablero, ni en Pendientes, ni en la sección 3 del informe— y su tarjeta muestra el texto fijo:

> «Sin dato suficiente: se observan N días de los M que exige el umbral»

La sección 3 del informe diario declara la ventana en su encabezado: «actividad observada desde DD-MM-YYYY». **Un informe que dice «tres repositorios sin actividad» sin decir sobre cuántos días observa es un informe que engaña.**

### 13.8.3 El indicador de sincronización

Se registra y se muestra **por `(curso, ámbito)`**. Ámbitos, lista cerrada: `CANVAS_ROSTER`, `CANVAS_GRUPOS`, `CANVAS_TAREAS_Y_FECHAS`, `CANVAS_MAPEOS`, `GITHUB_ACTIVIDAD`, `GITHUB_ACCESOS`.

**Tres ubicaciones, ninguna redundante:**

1. **Cabecera del curso** — un indicador compacto que muestra **el más antiguo** de los ámbitos relevantes para la pantalla actual. Al pulsarlo, un *popover* lista **los seis ámbitos** con su estado propio, su hora y su botón «Sincronizar ahora».
2. **Pie de cada tabla** — el ámbito que alimenta esa tabla: bajo Personas, `CANVAS_ROSTER`; bajo la tabla de repositorios, `GITHUB_ACCESOS`; bajo el tablero, `GITHUB_ACTIVIDAD`.
3. **Vista de repositorio** — su propio indicador, porque su actividad puede estar retrasada aunque el curso esté al día.

**Nunca se muestra una fecha sin decir de qué ámbito es.**

| Estado | Texto exacto | Tratamiento |
|---|---|---|
| **Nunca** | «Todavía no se ha sincronizado» + **Sincronizar ahora** | Neutro |
| **En curso** | «Sincronizando… (empezó hace 12 s)», con indicador de progreso y botón deshabilitado | Neutro con animación |
| **Correcta** | «Actualizado hace 4 min» | Neutro |
| **Fallida** | «Actualizado hace 22 min. **La sincronización de las 10:30 falló.**» + motivo corto + **Detalles técnicos** + **Reintentar** | Ámbar; **rojo e incidencia** si falla tres ciclos seguidos |
| **`PARCIAL`** | «Actualizado hace 4 min. **No se aplicaron bajas: el roster llegó incompleto.**» | Ámbar, con la incidencia `ROSTER_SOSPECHOSO` enlazada |
| **`TRUNCADA`** | «Actualizado parcialmente: se alcanzó el tope de páginas y se continúa en el ciclo siguiente.» | Ámbar, con la incidencia `ROSTER_TRUNCADO` enlazada |

Los dos últimos **no son opcionales**: sin ellos el docente vería cifras que no corresponden al roster real sin ninguna pista de por qué.

**El indicador nunca llama a Canvas ni a GitHub.** Lee la vista `v_ultima_sincronizacion(curso_id, ambito)`. Y **nunca se escribe «en tiempo real» en ninguna parte**: la aplicación es honesta sobre la latencia en lugar de fingirla.

### 13.8.4 «Sincronizar ahora»

- **Un botón por ámbito**, dentro del *popover* de la cabecera, más **«Sincronizar todo»**, más dos botones especializados en su pantalla: el de la tarea de registro en Personas (`CANVAS_MAPEOS`) y el de actividad en el tablero (`GITHUB_ACTIVIDAD`).
- **Siempre encola**: `POST /api/cursos/{id}/sincronizar/{ambito}` devuelve `trabajo_id`. **Nunca llama a una API dentro de la petición HTTP.**
- **Permiso `curso.ver`**: una sincronización es una lectura, y atar el refresco de una pantalla a un permiso más fuerte dejaría al ayudante mirando datos que no puede actualizar.
- **Enfriamiento de 60 segundos por `(curso, ámbito)`, impuesto en el servidor** mediante la clave de idempotencia `sync:<ambito>:<curso_id>:<ventana_60s>` y su índice único parcial. El botón muestra «Disponible de nuevo en 43 s». El enfriamiento sólo en la interfaz queda descartado: bastaría recargar la página.
- **Retroalimentación**: la interfaz consulta `GET /api/cursos/{id}/trabajos/{tid}` cada 2 s hasta 60 s y muestra el resultado desde `sincronizacion.contadores`: «2 estudiantes nuevos · 1 sección nueva · 1 fecha cambiada (Entrega 2: 20-09-2026 23:59 → 22-09-2026 23:59) · 0 errores · 3,4 s». Si no cambió nada: «Sin cambios». Si sigue en cola pasados 60 s: «Sigue en cola; puedes seguirlo en Operación», con enlace.
- **Texto fijo junto al botón**: «Los repositorios se crean solos a medida que llega la información. Este botón sólo adelanta la lectura de Canvas.»
- **Acción distinta y con nombre distinto a propósito: «Reintentar aprovisionamiento»**, con `tarea.administrar`. **No se llama «crear repositorios»** en ninguna parte, porque contradiría en pantalla lo que R2.3.10 exige.

**Criterios de aceptación de §13.8**

1. Buscar en las pantallas cualquier número mostrado sin denominador: no hay ninguno.
2. Forzar un `sincronizacion.resultado = TRUNCADA` en el entorno de ensayo: el indicador muestra el texto exacto de la tabla, en ámbar, con la incidencia enlazada.
3. Pulsar «Sincronizar ahora» dos veces seguidas con un cronómetro: la segunda pulsación no encola nada, el botón muestra la cuenta atrás y la respuesta dice «Sincronización ya en curso, iniciada hace N s».
4. Preparar un repositorio con `listo_en` de hace 3 días y umbral de 7: no aparece entre los inactivos en ninguna vista y su tarjeta muestra «Sin dato suficiente: se observan 3 días de los 7 que exige el umbral».
5. Buscar la expresión «tiempo real» en el archivo único de mensajes: no aparece.

---

## 13.9 Estados de carga, sondeo y latencia percibida

### 13.9.1 Objetivos de latencia visibles

| Vista | Objetivo | Cómo se cumple |
|---|---|---|
| Tablero de tarea con 200 sujetos | **< 400 ms p95** | Lectura del espejo; **ninguna pantalla llama a GitHub** |
| Cualquier listado paginado | **< 600 ms p95** | Paginación en servidor, tamaño 50 por defecto, máximo 200 |
| `push` en GitHub → visible en el tablero | p50 < 30 s; p95 < 3 min; **garantizado ≤ techo calculado**; techo absoluto 24 h | Webhook, reconciliación cada 15 min con ETag, barrido nocturno |
| Aprovisionamiento de 200 sujetos | ≈ 20 min, **con estimación visible en pantalla** | Ritmo de 1 repositorio cada 6 s |
| Petición web completa | **corte propio a los 25 s**, con error nuestro en español | *Middleware* de presupuesto, `504` con `{codigo: "TIEMPO_AGOTADO"}` |
| Escrituras síncronas de A-169 | **20 s duros**; agotados, **la operación no se pierde**: pasa a la cola y **la pantalla lo dice con esas palabras** | «Esto está tardando; lo dejamos en cola y puedes seguirlo aquí» |

`/operacion` publica las latencias p50/p95 medidas frente a los objetivos declarados. **La promesa es comprobable, no una aspiración.**

### 13.9.2 El checklist de vinculación es asíncrono y muestra resultados parciales

`POST /api/cursos/{id}/verificacion` **encola** y devuelve `202` con `ejecucion_id`. Cada comprobación escribe su fila en cuanto termina, con `resultado ∈ {CORRECTO, ADVERTENCIA, BLOQUEANTE, NO_VERIFICADO, VERIFICADO_A_MANO}`. `GET /api/cursos/{id}/verificacion/{ejecucion_id}` devuelve el estado de los **21 ítems** y **la interfaz sondea cada 2 segundos, pintando cada semáforo en cuanto llega**. El profesor ve avanzar la lista, no una rueda.

- Tope global de **3 minutos**; lo que no termine queda `NO_VERIFICADO` con motivo «no respondió a tiempo», **nunca en verde**, y con un botón «volver a verificar» por ítem.
- **Un botón por ítem rojo que lleva exactamente al sitio donde se arregla.**
- **La prueba de escritura de Canvas no entra en el trabajo**: es síncrona, tiene su propio botón que aparece **después** de que el checklist termine, con su casilla de autorización y sus 20 s duros. **Verificar en diferido no es verificar.**
- **Se descartan SSE y WebSocket**: un canal persistente por profesor compite con el resto de peticiones, se cae con cada despliegue y exige reconexión propia; el sondeo se recupera solo si el navegador se refresca.

### 13.9.3 Reglas de carga

| Situación | Comportamiento |
|---|---|
| Carga inicial de una tabla | Esqueleto del alto final; **el contenido no salta al llegar** |
| Refresco de datos ya mostrados | Los datos anteriores permanecen visibles, con el sello de antigüedad en estado «en curso» |
| Acción en vuelo | Botón deshabilitado con su texto de progreso; nunca desaparece de la pantalla |
| Trabajo encolado | Se devuelve `trabajo_id` y se sondea `GET /api/cursos/{id}/trabajos/{tid}` cada 2 s hasta 60 s |
| Trabajo que excede el sondeo | «Sigue en cola; puedes seguirlo en Operación», con enlace. **Nada se pierde y nada bloquea la interfaz** |

**Criterios de aceptación de §13.9**

1. Ejecutar el checklist sobre un curso vinculado y comprobar que los ítems se pintan uno a uno, que los primeros responden en menos de un segundo y que ninguno queda en verde sin haberse ejecutado.
2. Provocar el timeout de un ítem: queda `NO_VERIFICADO` con su motivo escrito y su botón «volver a verificar».
3. Medir la vista de tarea con 200 sujetos en la prueba de carga: p95 por debajo de 400 ms, y ninguna llamada a GitHub en el registro de red.
4. Provocar el agotamiento de los 20 s de una escritura síncrona: la pantalla muestra el texto «Esto está tardando; lo dejamos en cola y puedes seguirlo aquí» y la operación aparece en la cola.
5. Comprobar en `/operacion` que la tabla de latencias medidas existe y que sus valores proceden de mediciones persistidas.

---

## 13.10 Catálogo cerrado de estados vacíos

**No hay estado vacío genérico.** Cada entrada tiene título, explicación de una frase con la causa, una única acción sugerida y la marca de si es un estado normal o un problema. Cada endpoint de listado devuelve, junto a la lista vacía, el **código de causa** (`SIN_SUJETOS`, `SUJETOS_ESPERANDO`, `SIN_SYNC`, `INVITACION_PENDIENTE`, …) para que la interfaz elija la entrada correcta sin volver a consultar.

| Vista | Situación | Texto | Acción | ¿Problema? |
|---|---|---|---|---|
| `/cursos` | Sin cursos | «Todavía no tienes cursos. Crea uno y vincúlalo con Canvas y con GitHub.» | **Crear curso** | No |
| Curso → Resumen | Curso en `BORRADOR` o `VINCULANDO` | «Falta terminar la vinculación: vas por el paso 3 de 4.» | **Continuar vinculación** | No |
| Personas | 0 estudiantes | «Canvas no devolvió estudiantes para este curso. Puede que el curso no esté publicado o que la matrícula aún no haya empezado.» | **Volver a verificar** + enlace profundo a Personas en Canvas + **Ya lo arreglé, sincronizar** | Advertencia |
| Personas → grupos | Conjunto de grupos sin grupos | «Este conjunto de grupos todavía no tiene grupos. Los estudiantes se están inscribiendo en Canvas, o falta crearlos.» | Enlace profundo al conjunto en Canvas + **Sincronizar** | No |
| Personas → grupos | Grupo sin ningún integrante `accepted` | «Nadie ha aceptado todavía la invitación a este grupo en Canvas. Sin al menos un integrante aceptado no se crea su repositorio.» | Enlace a Canvas | Advertencia |
| Tareas | 0 tareas | «Crea la primera tarea y vincúlala con una tarea de Canvas.» | **Crear tarea** | No |
| Tarea → Entregas | 0 entregas vinculadas | «Esta tarea todavía no tiene entregas. Vincula al menos una tarea de Canvas; la primera será la entrega final y podrás cambiarlo al añadir la segunda.» | **Vincular entrega** | No |
| Tarea → Repositorios | 0 repositorios **con sujetos esperando** | «Ningún repositorio todavía: faltan 7 cuentas de GitHub. Se crearán solos en cuanto lleguen.» | **Ver Pendientes** | Advertencia |
| Tarea → Repositorios | 0 repositorios **y 0 sujetos** | «Esta tarea no tiene sujetos: ninguna entrega vinculada es visible para ningún estudiante.» | **Revisar la visibilidad en Canvas** + enlace | **Sí**, bloqueante |
| Tarea → Resumen | Antes del primer sync de actividad | «Todavía no hemos recogido actividad de estos repositorios. La reconciliación corre cada 15 minutos; la próxima es a las 14:45.» | **Actualizar ahora** (encola) | No |
| Repositorio → Timeline | 0 commits **e invitación sin aceptar** | «Sin commits. La invitación a Ana Gómez sigue sin aceptar desde el 12-09-2026.» | **Reenviar invitación** | Advertencia |
| Repositorio → Timeline | 0 commits **con invitación aceptada** | «Sin commits. Ana Gómez aceptó la invitación el 12-09-2026 y todavía no ha subido nada.» | **Avisar por Canvas** | Advertencia |
| Entrega cerrada | Versión `SIN_COMMITS` | «Versión registrada: el repositorio no tenía ningún commit del estudiante en la fecha de cierre.» | **Abrir el repositorio** | Informativa |
| Corrección | Ayudante sin asignaciones | «No tienes entregas asignadas. El profesor reparte desde Corrección → Repartir.» | — | No |
| Pendientes | 0 incidencias | «No hay nada pendiente. Última comprobación: hace 3 min.» | — | No |
| Comunicaciones del curso | 0 mensajes | «Todavía no se ha enviado ningún mensaje desde este curso.» | — | No |
| Informes | Antes del primer informe | «El informe diario de este curso se genera desde el DD-MM-YYYY.» | — | No |
| Actividad | 0 cambios en el rango | «No se detectaron cambios en el rango seleccionado.» | Ampliar el rango | No |

**Dos reglas que acompañan al catálogo:**

1. **Versión `SIN_COMMITS`: la entrega se corrige y se publica igual.** La pantalla de corrección muestra el aviso, el enlace por SHA al commit inicial si existe, y **la aplicación no propone ninguna nota**: el formulario calcula pero no decide. Automatizar un cero sería decidir una calificación, y las calificaciones son del docente y viven en Canvas.
2. **La verificación de R2.1.6 con 0 estudiantes advierte, no falla.** La severidad del ítem correspondiente es «Advertencia si el curso está vacío», no bloqueante, y el motivo se escribe en pantalla: un curso puede estar legítimamente vacío antes de que abra la matrícula. La advertencia **permanece visible en la cabecera del curso** hasta que el roster deje de estar vacío.

**Criterios de aceptación de §13.10**

1. Ejecutar la prueba que recorre los códigos de causa devueltos por los endpoints de listado y comprueba que **todos** tienen entrada en el catálogo: falla la construcción si falta uno.
2. Crear un curso vacío y recorrer Personas, Tareas y Pendientes: las tres muestran su texto del catálogo, con su acción, y ninguna aparece muda.
3. Crear una tarea cuya entrega no sea visible para ningún estudiante: la pestaña Repositorios muestra el estado vacío **bloqueante** con su enlace a Canvas.
4. Ejecutar el checklist sobre un curso con 0 estudiantes: el ítem correspondiente queda en ámbar con su motivo y el checklist continúa hasta el final.

---

## 13.11 Catálogo cerrado de errores de la interfaz docente

Cada entrada lleva seis campos: **código** estable en ASCII, **familia** (`TRANSITORIO`, `PERMANENTE`, `BLOQUEANTE`), **texto en español**, **acción sugerida**, **quién puede resolverlo** y si bloquea. Toda entrada se muestra con la forma que fija A-155: explicación en español arriba, **mensaje literal del proveedor** en un bloque secundario dentro de un desplegable **«Detalles técnicos»** cerrado por defecto, con código HTTP, mensaje literal, endpoint, `correlacion_id` y fecha con zona, y botón de copiado.

| Código | Familia | Texto | Acción | Quién lo resuelve |
|---|---|---|---|---|
| `CANVAS_TOKEN_INVALIDO` | BLOQUEANTE | «La credencial de Canvas de Ana Pérez ya no es válida. La aplicación no puede leer ni escribir en Canvas de este curso.» Banda roja persistente | **Pegar mi credencial** | Cualquier profesor del curso |
| `CANVAS_PERMISO_AUSENTE` | PERMANENTE | «Tu token no tiene permiso para \<acción\> en este curso.» Nombra el ítem del checklist que lo detecta | **Volver a verificar** + instrucciones | El titular del token, o un administrador de Canvas |
| `CANVAS_CURSO_NO_DISPONIBLE` | BLOQUEANTE | «El curso de Canvas vinculado ya no está disponible para esta credencial.» | **Revisar en Canvas** · **Volver a verificar** | Profesor con `curso.administrar` |
| `LIMITE_API` | TRANSITORIO | «Esperando a GitHub por límite de uso. Reintento automático a las 15:12.» **En ámbar, nunca en rojo** | Ninguna; se puede seguir en `/operacion` | Nadie: es automático |
| `GITHUB_APP_DESINSTALADA` | BLOQUEANTE | «La aplicación ya no está instalada en la organización \<org\>. Los repositorios existentes siguen ahí; no se pueden crear ni configurar nuevos.» | **Reinstalar** | Profesor con `curso.administrar` |
| `GITHUB_PERMISOS_PENDIENTES` | BLOQUEANTE | «Hay permisos nuevos de la aplicación pendientes de aprobar en GitHub. Los trabajos que los necesitan están en espera, no fallidos.» | **Aprobar en GitHub** | Propietario de la organización |
| `GITHUB_USUARIO_NO_EXISTE` | PERMANENTE | «No existe una cuenta de GitHub con el nombre `jperez`.» | **Corregir la cuenta** · **Pedírselo al estudiante** (comentario en Canvas) | Ayudante con `mapeo.editar`, o el propio estudiante |
| `GITHUB_LOGIN_ES_ORGANIZACION` | PERMANENTE | «`icc4201` es una organización de GitHub, no una persona.» | Igual que el anterior | Igual |
| `GITHUB_LOGIN_REASIGNADO` | PERMANENTE | «El nombre `jperez` ahora pertenece a otra cuenta distinta de la que se registró.» | **Confirmar quién es** | Profesor o ayudante con `mapeo.editar` |
| `REPO_NOMBRE_OCUPADO` | PERMANENTE | «Ya existe un repositorio llamado `…` en la organización y no es de esta tarea.» **Con la condición de adopción que falló** | **Ver en GitHub** · **Cambiar el slug de la tarea** (sólo si aún no hay repositorios creados) | Profesor con `tarea.administrar` |
| `REPOSITORIO_INACCESIBLE` | PERMANENTE | «El repositorio ya no es accesible desde la aplicación. Su historia y sus versiones registradas se conservan.» | **Ver el motivo** · **Sustituir el repositorio** | Profesor con `tarea.administrar` |
| `INVITACION_DESAPARECIDA` | BLOQUEANTE | «La invitación a Ana Gómez fue **rechazada o caducó**.» — literal, porque la API no distingue las dos causas | **Reenviar**, con «reenvío 2 de 3» | Ayudante con `mapeo.editar` |
| `ORG_PROHIBE_CREAR_REPOS` | PERMANENTE | «GitHub no permite crear más repositorios en esta organización con la configuración actual.» + literal | **Reintentar** tras cambiarlo en GitHub | Propietario de la organización |
| `ORG_EXIGE_2FA` | PERMANENTE | «La organización exige verificación en dos pasos y esta cuenta no la tiene activada.» | **Avisar al estudiante** | El estudiante |
| `ENTREGA_ELIMINADA_EN_CANVAS` | PERMANENTE | «La tarea de Canvas vinculada a la entrega «Avance parcial» ya no existe.» | **Desvincular la entrega** (sólo si no hay versiones capturadas) · **Restaurarla en Canvas** | Profesor con `tarea.administrar` |
| `ESTUDIANTE_SIN_GRUPO` | BLOQUEANTE del sujeto | «Luis Rojas no está en ningún grupo del conjunto «Proyectos»; no recibirá repositorio.» | Enlace profundo al conjunto en Canvas + **Sincronizar** | Profesor, en Canvas |
| `MODALIDAD_INCOMPATIBLE` | PERMANENTE | «Esa tarea de Canvas es grupal y esta tarea es individual. Crea otra tarea o cambia la configuración en Canvas.» — **bloqueo en el momento de vincular** | **Crear otra tarea** | Profesor con `tarea.administrar` |
| `PERIODO_CALIFICACION_CERRADO` | PERMANENTE | «El período de calificación de Canvas está cerrado; no se pueden publicar notas.» | **Abrirlo en Canvas** | Administrador de Canvas |
| `CUOTA_CORREO_AGOTADA` | BLOQUEANTE | «Se agotó la cuota diaria de correo. El informe se enviará mañana; ya está disponible aquí.» | **Ver el informe** | Nadie: se reintenta solo |
| `CURSO_EN_SOLO_LECTURA` | BLOQUEANTE | «Este curso está en modo sólo lectura. Los mensajes se generan y quedan en espera; el aprovisionamiento está detenido.» + motivo escrito | **Reactivar** (con `curso.administrar`) | Profesor con `curso.administrar` |
| `PERMISO_INSUFICIENTE` | PERMANENTE | «No tienes el permiso \<nombre en español\> en este curso.» Nombra a quién pedírselo | — | Profesor con `equipo.administrar` |
| `NO_ENCONTRADO` | PERMANENTE | «No encontramos lo que buscas en este curso.» **Nunca confirma la existencia de un recurso de otro curso** | Volver | — |
| `YA_EN_CURSO` | TRANSITORIO | «Esta acción ya se está ejecutando, iniciada hace 12 s.» | Ver el progreso | Nadie |
| `TIEMPO_AGOTADO` | TRANSITORIO | «Esto está tardando; lo dejamos en cola y puedes seguirlo aquí.» | Seguir el trabajo | Nadie |
| `DEMASIADAS_PETICIONES` | TRANSITORIO | «Demasiadas peticiones en poco tiempo. Vuelve a intentarlo en N segundos.» Página `429` explicativa en español | Esperar | Nadie |

**Regla de cierre: un error sin fila en el catálogo no llega a pantalla tal cual.** Cae en un marco genérico que muestra **familia, mensaje literal y `correlacion_id`**, y **abre una incidencia** para que el equipo añada la fila. Un `403` cuyo cuerpo no se reconozca se clasifica como bloqueado —no como error del sujeto— y se muestra con el texto literal de GitHub, **sin traducirlo a un diagnóstico inventado**.

**Regla de responsabilidad.** Cada fila declara **quién** puede resolverlo, y la acción aparece **deshabilitada con el motivo escrito** si quien mira no puede ejecutarla. Un mensaje que induce a una acción imposible por permisos no es guía.

**Regla de rastro.** Un `403` sobre una ruta de curso emitido a alguien que **sí** tiene membresía `ACTIVA` en ese curso se escribe en `bitacora` con actor, `curso_id`, permiso exigido, ruta, método e identificador del recurso, tanto en lectura como en escritura. Un `403` o `404` a quien **no** tiene membresía activa va **sólo** al log estructurado, nunca a `bitacora` y nunca con el correo completo.

**Criterios de aceptación de §13.11**

1. Ejecutar la prueba de cobertura: **cada uno de los 51 tipos de incidencia, los 7 subtipos de `ERROR_PERMANENTE`, los 6 motivos de `DEGRADADO` y los motivos de `ESPERANDO_INFORMACION`** tienen entrada con texto y acción. Falta una y falla la construcción.
2. Provocar un `403` de Canvas con cuerpo desconocido en el entorno de ensayo: la pantalla muestra el marco genérico con familia, literal y `correlacion_id`, y se abre la incidencia correspondiente.
3. Abrir cualquier error y comprobar que el desplegable «Detalles técnicos» está cerrado por defecto, que contiene los cinco campos y que el botón de copiado funciona.
4. Entrar como ayudante sin `tarea.administrar` a una fila con `REPO_NOMBRE_OCUPADO`: la acción «Cambiar el slug de la tarea» aparece deshabilitada con el motivo escrito.
5. Provocar un `403` a un miembro activo y comprobar la fila en `bitacora` con permiso exigido, ruta y método; provocar un `404` a un no miembro y comprobar que **no** hay fila en `bitacora`.

---

## 13.12 Pendientes: el componente único de lo que falta

`ListaPendientes` es **un solo componente**, reutilizado en tres sitios, que lee la vista compartida `v_pendiente_curso` sobre la tabla `incidencia` —la misma que alimenta el estado de repositorios, la barra de resumen y el informe diario, de modo que **las tres vistas nunca se contradicen**:

1. `/cursos/{id}/pendientes` — completo, con los cuatro bloques de A-150 y exportación CSV.
2. **Cabecera del curso** — contador y los tres pendientes de mayor prioridad, plegado.
3. `…/tareas/{tid}/resumen` y `…/tareas/{tid}/repositorios` — el mismo componente **filtrado por `tarea_id`**, para que la tarea no invente su propio panel.

**Forma fija de cada fila:** `{ tipo, severidad, título en lenguaje de acción, sujeto nombrado, acción primaria, acción secundaria, enlace profundo }`. El título y la acción **no son texto libre**: se derivan del `tipo` por una función de dominio, de modo que la misma incidencia dice exactamente lo mismo en las tres pantallas y en el informe diario. `incidencia.accion_sugerida` guarda el **código** de acción, no la frase.

**Lista cerrada de tipos: los 51 de A-088 tras RG-190.** No hay ninguno fuera de esa lista. Orden: primero por severidad (`BLOQUEANTE` > `ADVERTENCIA` > `INFORMATIVA`) y dentro de ella por el entero de grupo.

| Prioridad | Grupo | Tipos |
|---|---|---|
| 10 | **El curso entero está parado** | `CANVAS_CREDENCIAL_INVALIDA`, `CANVAS_CURSO_NO_DISPONIBLE`, `SIN_CREDENCIAL_DE_RESPALDO`, `GITHUB_PERMISOS_PENDIENTES`, `PLANIFICADOR_DETENIDO`, `BASE_CERCA_DEL_LIMITE`, `LIMITE_API_ALCANZADO`, `ACCESO_DOCENTE_NO_REVOCADO`, `CUENTA_DOCENTE_ES_DE_ESTUDIANTE` |
| 20 | **Bloquean el aprovisionamiento de un sujeto** | `GITHUB_DUPLICADO`, `ESTUDIANTE_EN_DOS_GRUPOS`, `MAPEO_NO_RESUELTO`, `SIN_MAPEO`, `GITHUB_CUENTA_PERDIDA`, `GITHUB_LOGIN_REASIGNADO`, `ESTUDIANTE_SIN_GRUPO`, `GRUPO_INCOMPLETO`, `TAREA_INCONSISTENTE`, `MODALIDAD_INCOMPATIBLE`, `VISIBILIDAD_NO_RESOLUBLE`, `ENTREGA_ELIMINADA_EN_CANVAS`, `TAREA_REGISTRO_ALTERADA` |
| 30 | **El repositorio existe pero está incompleto o roto** | `REPO_ERROR_PERMANENTE`, `REPO_BLOQUEADO_POLITICA`, `REPO_NOMBRE_OCUPADO`, `REPOSITORIO_INACCESIBLE`, `SIN_ACCESO_DOCENTE`, `INVITACION_EXPIRADA`, `INVITACION_NO_ACEPTADA`, `MENSAJE_NO_ENTREGABLE` |
| 40 | **Evidencia y corrección** | `VERSION_ERROR`, `VERSION_REVISAR`, `PERIODO_CALIFICACION_CERRADO`, `CORRECCION_SIN_CORRECTOR`, `GRUPO_CAMBIO_TRAS_CIERRE`, `ALTA_TARDIA`, `NOTA_OCULTA_AL_ESTUDIANTE`, `NOTA_DIVERGENTE_EN_CANVAS` |
| 50 | **Seguimiento** | `SIN_ACTIVIDAD`, `SIN_PARTICIPACION` |
| 60 | **Datos de Canvas que hay que mirar** | `ROSTER_SOSPECHOSO`, `ROSTER_TRUNCADO`, `ESTUDIANTE_EN_DOS_SECCIONES`, `POSIBLE_FUSION_CANVAS`, `SECCION_CROSS_LISTED`, `DISCREPANCIA_FECHAS`, `OVERRIDE_NO_INTERPRETABLE` |
| 70 | **Operación** | `CUOTA_CORREO_AGOTADA`, `RESPALDO_FALLIDO`, `DENEGACIONES_ANOMALAS`, `CORREO_OPERATIVO_ELEVADO`, `COMUNICACIONES_SUSPENDIDAS` |

**[DECISIÓN NUEVA]** La asignación de prioridad de los catorce tipos que RG-190 añade sobre los 37 originales se fija en esta tabla; la fuente de origen enumeraba los grupos sobre el catálogo anterior y no los reparte.

**Lenguaje de acción, con ejemplos textuales fijos:** «3 estudiantes sin cuenta de GitHub → **Enviar recordatorio**»; «2 invitaciones sin aceptar hace más de 48 h → **Reenviar**»; «1 grupo sin integrantes aceptados → **Configurar en Canvas**» con enlace profundo; «Ana Gómez y Luis Rojas declararon la misma cuenta → **Resolver**»; «4 repositorios sin acceso del equipo docente → **Reintentar**». **Nunca aparece un identificador en mayúsculas.**

**Agrupación y expansión.** Las filas del mismo `tipo` se colapsan en una línea con recuento y se despliegan al pulsarla. La acción primaria puede ejecutarse **sobre el grupo entero** —«reenviar las 12 invitaciones»— con la confirmación de nivel 2 y el recuento a la vista.

**Silenciar, no posponer.** El verbo en las cuatro pantallas es **«silenciar»**. Sólo se silencian incidencias de severidad `ADVERTENCIA` o `INFORMATIVA` y sólo de los tipos `SIN_ACTIVIDAD` y `SIN_PARTICIPACION`. **Una incidencia `BLOQUEANTE` no se silencia jamás.** Silenciar **no cierra** la incidencia; exige **motivo escrito**; caduca sola en `min(ahora + 14 días, próxima fecha efectiva de cierre del sujeto)`; queda en `bitacora` con actor y fecha; permiso `curso.ver`. La incidencia silenciada **queda fuera de la sección 3 del informe diario** y se muestra plegada bajo **«silenciadas (N)»** en Pendientes y en el tablero: **no desaparece de la interfaz**.

**Ninguna llamada externa al pintar.** Las acciones **encolan** trabajos; nunca llaman a la API dentro de la petición.

**Criterios de aceptación de §13.12**

1. Comprobar que los tres consumidores del componente muestran, para el mismo curso, exactamente las mismas filas y los mismos recuentos.
2. Cambiar el texto de un tipo en el archivo único de mensajes y comprobar que cambia a la vez en Pendientes, en la cabecera, en la tarea y en el informe diario.
3. Silenciar una incidencia `SIN_ACTIVIDAD` sin escribir motivo: la acción se rechaza. Con motivo: la incidencia pasa al grupo plegado «silenciadas (N)» con el motivo y el actor visibles, sigue `abierta`, y desaparece de la sección 3 del informe.
4. Intentar silenciar una incidencia `BLOQUEANTE`: el control no existe y la API responde con rechazo explícito.
5. Preparar un curso con 200 estudiantes sin mapear: Pendientes muestra una sola línea agrupada con recuento, no doscientas filas.
6. Ejecutar la prueba que exige entrada de texto para los 51 tipos: falla la construcción si falta uno.

---

## 13.13 Confirmaciones, acciones destructivas y deshacer

### 13.13.1 Los tres niveles

| Nivel | Cuándo se aplica | Forma |
|---|---|---|
| **1 · Confirmación simple** | Efecto reversible dentro de la aplicación y **sin escritura externa** | Modal con el efecto en una frase y el recuento |
| **2 · Confirmación con recuento de efectos externos** | Produce escrituras en Canvas o en GitHub que **la aplicación no puede deshacer** | Modal que **enumera los efectos con su número** y exige marcar una casilla |
| **3 · Confirmación escrita** | Irreversible y de alcance de curso o de tarea completa | Lo anterior más **escribir el `slug`** del curso o de la tarea, o el propio correo |

### 13.13.2 Asignación acción por acción

| Acción | Nivel | Qué enumera el modal |
|---|---|---|
| **Eliminar curso** | **No existe** | Lo que existe es «Archivar el curso» |
| **Archivar el curso** | 3 (escribir el `slug` del curso) | Recuento de repositorios afectados, lista de lo que quedaría sin capturar, casilla marcada por defecto para archivar también los repositorios, descarga del inventario CSV, y el recordatorio de que **desinstalar la GitHub App desde GitHub revoca de una vez todos los accesos** |
| **Desvincular Canvas** | 2 | Se detienen las lecturas; las escrituras pendientes quedan encoladas en `ESPERANDO_CREDENCIAL`. Es reversible pegando una credencial |
| **Desvincular GitHub** | 3 | Libera la organización y la instalación; los repositorios existentes quedan fuera del alcance de la aplicación |
| **Eliminar tarea** | **No existe** | «Cerrar tarea» es nivel 1 |
| **Archivar los repositorios de la tarea** | 2 | Texto literal: **«Los repositorios NO se borran de GitHub. Pasan a sólo lectura: no se podrán crear tags nuevos y la ingesta de actividad se detiene. Los estudiantes conservan la lectura.»** Bloqueada mientras haya una entrega sin versión capturada y con cierre en el futuro. **Exige rol `PROFESOR`** |
| **Retirar a un ayudante con correcciones pendientes** | 2 | Cuántas asignaciones pasarán a `SIN_CORRECTOR`, que sus sesiones de ese curso se revocan de inmediato y que **pierde la lectura de los repositorios en GitHub**; ofrece reasignar en el mismo flujo |
| **Retirar a un profesor** | 2 | Se **rechaza** si es el último profesor activo, con el mensaje «promueve antes a otro profesor» |
| **Cambiar el usuario de GitHub de un estudiante que ya tiene repositorio con commits** | 3 (escribir el nombre del estudiante) | Se invita a la cuenta nueva; **se retira el acceso de la cuenta anterior** en el ciclo siguiente; **los commits ya atribuidos no cambian de autor**; el mapeo anterior queda `SUPERSEDIDO`, visible, nunca borrado. **Sin repositorio creado todavía, la misma acción es nivel 1** |
| **Reenviar invitación** | 1 | Las tres comprobaciones previas y el contador «reenvío 2 de 3, el anterior hace 26 h» |
| **Publicar una nota cuando ya existe** | 2 | Lee la *submission* actual antes de mostrar el modal y muestra **el valor que hay hoy en Canvas y el que lo va a sustituir**, quién publicó el anterior y cuándo, y avisa de que la escritura aparecerá firmada por el titular del token |
| **Enviar un anuncio o un mensaje masivo** | 2 | **Previsualización del texto y número de destinatarios**, más la lista de excluidos con su motivo |
| **«Reintentar todos los fallidos»** | 2 | Recuento de trabajos y **duración estimada** al ritmo real |
| **Suspender las comunicaciones del curso / pasar a sólo lectura** | 2 | Qué canales se detienen, que los mensajes se siguen generando y quedan `DIFERIDO`, y que caducan a los 7 días |
| **Cerrar mi cuenta** | 3 (escribir el propio correo) | — |

### 13.13.3 Deshacer

**Existe sólo donde es real, y se dice cuando no existe.** Hay deshacer para: revocar una invitación de equipo antes de aceptarse, desarchivar un repositorio y un curso, reactivar un sujeto, retirar la propia credencial y reasignar un corrector.

**No hay deshacer para nada que ya salió hacia Canvas o GitHub** —nota publicada, mensaje enviado, anuncio, invitación emitida—, y el modal lo dice con esas palabras en lugar de prometer una reversión imposible.

**La aplicación no borra repositorios de estudiantes, ni sus commits, ni tags, ni notas, bajo ninguna circunstancia, en ningún nivel de confirmación.**

### 13.13.4 El plan de efectos

Cada endpoint destructivo expone primero `GET …/efectos`, que devuelve los **recuentos reales** que el modal enumera, calculados sobre la misma capa de consulta que pinta la pantalla, para que el número del modal y el de la pantalla coincidan. Los de nivel 3 exigen el `slug` en el cuerpo y **lo verifican en el servidor**. **El texto de efectos se deriva del plan, nunca se redacta a mano en cada pantalla.** Toda acción confirmada queda en `bitacora` con su actor.

**Criterios de aceptación de §13.13**

1. Comprobar que cada acción de la tabla tiene exactamente un nivel asignado y que el nivel 3 verifica el `slug` **en el servidor**, no sólo en la interfaz.
2. Comparar el recuento que muestra el modal con el que produce la acción sobre el conjunto de datos de prueba: coinciden.
3. Abrir el modal de «Archivar los repositorios de la tarea»: contiene el texto literal sobre que no se borran de GitHub.
4. Intentar archivar los repositorios de una tarea con una entrega sin versión capturada y con cierre futuro: la acción está bloqueada con su motivo escrito.
5. Intentar retirar al último profesor activo: se rechaza con el mensaje «promueve antes a otro profesor».
6. Buscar la palabra «deshacer» en el archivo único de mensajes: aparece sólo en las seis acciones donde existe.

---

## 13.14 Repetición de acciones: doble clic, dos pestañas, dos personas

Tres capas, y ninguna sustituye a las otras: **botón deshabilitado mientras la acción corre** (comodidad), **token de idempotencia por formulario** (corrección frente al doble envío y al reintento del navegador) y **deduplicación en la cola por clave de acción** (corrección frente a dos pestañas y dos usuarios).

**El comportamiento visible ante repetición es «ya en curso», nunca un duplicado y nunca un silencio.**

Al montarse el formulario, el frontend genera un `UUID` v7 y lo envía en la cabecera `Idempotency-Key`:

| Situación | Respuesta |
|---|---|
| Misma clave, acción ya `TERMINADA` | **El resultado guardado tal cual**: mismo código y mismo cuerpo. Un doble envío es indistinguible del primero |
| Misma clave, acción `EN_CURSO` | `409` con `{codigo: "YA_EN_CURSO"}`; la interfaz muestra «esta acción ya se está ejecutando» |
| Clave distinta, acción equivalente en vuelo | `409 YA_EN_CURSO` por huella del cuerpo. Cubre las dos pestañas y los dos ayudantes |
| Misma clave con cuerpo distinto | `422 CLAVE_REUTILIZADA` |

| Acción | Qué ve el usuario al repetir |
|---|---|
| Crear repositorio base | El mismo resultado, con el repositorio ya creado. **Nunca dos repositorios** |
| Subir, reemplazar o borrar archivo del base | «Ese archivo cambió mientras editabas», con opción de recargar |
| Sincronizar ahora | «Sincronización ya en curso, iniciada hace 12 s». La segunda pulsación **no encola nada y lo dice** |
| Reintentar todos los fallidos | «Se reencolaron 7 de 12; los otros 5 ya estaban en cola». **Recuento explícito, no silencio** |
| Reenviar invitación | Botón **deshabilitado con la hora del próximo reenvío posible**: «podrás reenviar a partir de mañana 09:14» |
| Publicar nota | Confirmación explícita que dice que se va a sobrescribir en Canvas y quién publicó la anterior. **Nunca en silencio** |
| Enviar anuncio o mensaje | «En cola para envío a 43 personas». Doble clic ⇒ misma clave ⇒ **una sola fila** |

**Nada se ignora en silencio.** Un docente que pulsa dos veces y no ve nada concluye que no funcionó y vuelve a pulsar; el mensaje «ya en curso» con la hora de inicio corta ese bucle.

**Criterios de aceptación de §13.14**

1. Pulsar dos veces «Crear repositorio base» con la misma clave: se crea un solo repositorio y la segunda respuesta es idéntica a la primera.
2. Abrir dos pestañas y enviar el mismo anuncio desde ambas: se encola una sola fila y la segunda pestaña muestra `409 YA_EN_CURSO`.
3. Reenviar una invitación dos veces en menos de 24 h: el botón aparece deshabilitado con la hora exacta del próximo reenvío posible.
4. Comprobar que ninguna acción de la tabla responde con éxito silencioso ante una repetición.

---

## 13.15 Idioma, tono, formatos y vocabulario cerrado

### 13.15.1 Idioma

**Cien por cien español de Chile**, en interfaz, mensajes de error, correos del informe diario, mensajes y comentarios a estudiantes por Canvas y anuncios. **No hay versión bilingüe** y **no se instala ninguna biblioteca de i18n**: no hay segundo idioma, y una capa de traducción sin traducciones es código muerto.

**Los textos viven en un archivo único de mensajes**, con la misma estructura de claves jerárquicas en los dos lados: `frontend/src/textos/es-CL.ts` y `backend/app/infraestructura/mensajes/es_CL.py` (por ejemplo, `pendientes.sin_mapeo.titulo`, `errores.canvas.credencial_invalida.accion`). **Nunca se persiste texto de presentación**: en base de datos vive el código estable en ASCII y la etiqueta en español vive sólo en la capa de presentación.

La disciplina que lo hace verificable: una **regla de ESLint que prohíbe cadenas literales visibles en JSX** y una **prueba de backend que falla si aparece una cadena con acentos fuera del módulo de mensajes**. `lang="es-CL"` declarado en el documento.

### 13.15.2 Tono y persona

**Tuteo**, registro profesional, **sin emojis**. El mismo tono en la interfaz, en los mensajes automáticos al estudiante y en el informe por correo.

| Superficie | Persona | Ejemplo |
|---|---|---|
| Botones y acciones | **Infinitivo** | «Vincular curso», «Reenviar invitación», «Publicar nota», «Sincronizar ahora» |
| Textos, ayudas, estados vacíos y mensajes | **Tuteo** | «Vincula tu curso con Canvas para traer los estudiantes», «Todavía no tienes cursos», «Tu token ya no es válido» |
| Mensajes al estudiante | **Tuteo, nombrando el objeto exacto** | «Tu repositorio es `icc4201-202620-t1-ordenamiento-e5310-gomez-ana`, en la organización `…`» |

**Nunca se mezclan dentro de una frase**, y **nunca se usa el trato formal** («vincule su curso»), que en Chile suena institucional y distante en una herramienta interna del equipo docente.

### 13.15.3 Formatos

| Tipo de dato | Formato | Excepción |
|---|---|---|
| Fecha y hora | `dd-MM-yyyy HH:mm` **con la zona escrita al lado, siempre** | Ninguna |
| Números | `Intl.NumberFormat('es-CL')`: **coma decimal, punto de miles** | Las **notas** se muestran exactamente como las devuelve Canvas y **no se reformatean** |
| Porcentajes | Símbolo pegado: `60%` | — |
| Duraciones | En palabras: «hace 4 min», «en 2 h» | — |
| Identificadores técnicos | Monoespaciada, con botón de copiado, **sin traducir ni maquillar** | — |

### 13.15.4 Vocabulario cerrado

**No admite sinónimos en ninguna pantalla, ningún correo, ningún mensaje ni ningún nombre de tabla o de columna.**

| Se dice | Es exactamente | Glosa la primera vez | No se dice |
|---|---|---|---|
| **Curso** | Curso de la aplicación, vinculado a uno de Canvas | — | clase, ramo, course |
| **Sección** | `Section` de Canvas | «(*section* en Canvas)» | paralelo, section |
| **Conjunto de grupos** | `GroupCategory` colaborativa de Canvas | «(*group set* en Canvas)» | group set, categoría |
| **Grupo** | `Group` de una categoría colaborativa | — | equipo, team, group |
| **Estudiante** | Persona con matrícula de estudiante | — | alumno, student |
| **Tarea** | La agrupación con un único conjunto de repositorios (R2.3.4) | — | proyecto, assignment |
| **Entrega (parcial / final)** | Cada tarea de Canvas vinculada a una tarea (R2.3.2) | «(*assignment* en Canvas)» | submission, deadline, hito |
| **Tarea de Canvas** | Se usa **sólo** al hablar del objeto que vive en Canvas, en el asistente | — | — |
| **Organización** | La organización de GitHub del curso | «(*organization* en GitHub)» | org, cuenta |
| **Fecha de cierre** | Fecha efectiva aplicable a un sujeto | — | due date, plazo, vencimiento |
| **Versión de la entrega** | El estado inmutable del repositorio al cierre: el `commit_sha` | — | snapshot, corte, foto, tag |
| **Repositorio / Repositorio base** | Repositorio de GitHub / repositorio plantilla de la tarea | «(*template repository* en GitHub)» | repo del alumno, plantilla, template |
| **tag** | **Sólo** el objeto de Git en GitHub, en minúscula y en cursiva | — | usarlo como sinónimo de «versión de la entrega» |
| **Cuenta de GitHub vinculada** | Correspondencia estudiante ↔ usuario de GitHub | — | mapeo, matching, linkeo |
| **Invitación · Aceptada · Pendiente** | Estado del acceso al repositorio | — | invite, pending |
| **Corrección** | El trabajo de revisar una entrega de un sujeto | — | grading, revisión |
| **Nota** | El valor que el corrector escribe en la aplicación antes de publicar | — | — |
| **Calificación** | El valor que **vive en Canvas** tras publicar | — | — |
| **Publicar nota** | La acción de escribirla en Canvas | — | push de notas, subir notas |
| **Profesor / Ayudante** | Los dos roles de curso | — | admin, TA, staff |
| **Corrector** | **Rol funcional dentro de una entrega**, no un rol de curso | — | usarlo como nombre de rol |
| **Incidencia** | Problema que requiere atención del equipo docente | — | error, warning, alerta |
| **Silenciar** | Ocultar temporalmente una incidencia no bloqueante | — | posponer, snooze |
| **Informe diario** | El informe de R2.6.1 | — | reporte, digest |
| **Sincronización · «Actualizado hace X»** | Traída de datos desde Canvas o GitHub | — | sync, refresh, job |

**Dos precisiones que resuelven contradicciones aparentes:**

- **«tag»**: prohibido como sinónimo de «versión de la entrega»; permitido, en minúscula y en cursiva, para nombrar el objeto de Git, como el resto de términos de Git.
- **«corrector»**: prohibido como nombre de rol —el rol es Profesor o Ayudante—; permitido como función sobre una entrega concreta. La pantalla dice «Repartir entre el equipo docente» y la fila dice «Corrector: Ana Pérez».

Los términos de Git sin traducción asentada se dejan en **inglés y en minúscula**: *commit*, *push*, *branch*, *tag*, *merge*, *pull request*. Escribir «confirmación» por *commit* sólo confunde a quien va a mirar GitHub.

**Regla de glosa.** El término original aparece entre paréntesis **la primera vez que la pantalla lo nombra**, **nunca en un botón ni en un encabezado de columna**, y además vive en el *tooltip* permanente del término. En la especificación y en `docs/guia-revisor.md` la glosa aparece una vez, en la sección de vocabulario.

### 13.15.5 Mantenimiento

La guía vive en `docs/guia-de-redaccion.md`, versionada en el monorepo, con un responsable y un segundo capaz de defenderla. **Revisión completa de todos los textos el 14 de septiembre**, en la misma sesión que el segundo ensayo, con este criterio: **si un paso necesita explicación verbal para entenderse, el texto está mal**. Segunda revisión el **2 de octubre**.

**Criterios de aceptación de §13.15**

1. Ejecutar la puerta de CI de términos prohibidos sobre `frontend/src/textos/`, `backend/app/infraestructura/mensajes/`, las plantillas de mensajes y los documentos de especificación: no hay coincidencias fuera de la lista de excepciones anotadas.
2. Ejecutar la regla de ESLint `no-literal-strings` sobre JSX: no hay literales visibles fuera del archivo de mensajes.
3. Ejecutar la prueba de backend de cadenas acentuadas fuera del módulo de mensajes: no hay coincidencias.
4. Comprobar que ninguna nota de Canvas se reformatea: se muestra tal cual la devuelve la API.
5. Comprobar `lang="es-CL"` en el documento y ausencia total de emojis en el archivo de mensajes.
6. Recorrer las pantallas del guion de demostración y comprobar que ningún botón ni encabezado de columna contiene una glosa entre paréntesis.

---

## 13.16 Tiempo y fechas en la interfaz

| Regla | Enunciado normativo |
|---|---|
| **Almacenamiento** | UTC siempre. No existe una sola columna sin zona en el esquema |
| **Zona de presentación** | La **zona del curso**, tomada de `Course.time_zone` al vincular y editable por el profesor; por defecto `America/Santiago` si Canvas no la entrega |
| **La zona del navegador no se usa jamás** | Para que profesor y ayudante en husos distintos vean **la misma** fecha de cierre |
| **Formato único** | `dd-MM-yyyy HH:mm` con la zona al lado: `17-09-2026 23:59 (America/Santiago)`. **Nunca se muestra una hora desnuda** |
| **Alcance del formato** | También en «vinculado el…», «última sincronización», «capturada el…», «invitada el…» y en los pies de correo |
| **Ventanas relativas** | «hace 4 min», «últimas 48 h», «últimos 7 días» se calculan en UTC y se etiquetan con la fecha local equivalente en el *tooltip* |
| **Lector de pantalla** | Lee el **absoluto**, porque «hace 4 min» sin referencia no es útil fuera del momento |
| **Zona discrepante** | Si `Course.time_zone` difiere de la zona configurada, la cabecera del curso muestra una advertencia |
| **Eje de días y buckets** | El eje del timeline, el histograma y la sección 3 del informe usan **la zona del curso**, y los tres muestran el mismo número para el mismo repositorio |
| **`all_day`** | Si llega `all_day = true`, la interfaz muestra **la hora exacta convertida y además la etiqueta «todo el día»**, sin ocultar la hora. **No se inventa un 23:59** |
| **Sin fecha aplicable** | Si un sujeto es visible pero no tiene ninguna fecha aplicable, la entrega se muestra como **«sin fecha de cierre»**, que es distinto de «esta entrega no aplica a este sujeto»; la interfaz los distingue porque la acción del docente no es la misma |

El conjunto de datos de demostración incluye los cuatro casos límite —cierre a las 23:59 de la zona del curso, cierre a las 00:30 del día siguiente, `all_day = true` y `due_at` nulo— precisamente para poder enseñar la conversión delante del revisor y demostrar que la fecha que muestra la aplicación es la misma que muestra Canvas.

**Criterios de aceptación de §13.16**

1. Buscar en el frontend cualquier fecha renderizada sin el componente `Fecha`: no hay ninguna.
2. Abrir la aplicación con el sistema operativo en un huso distinto al del curso: todas las fechas siguen mostrándose en la zona del curso.
3. Abrir la entrega con `all_day = true`: se muestra la hora exacta convertida **y** la etiqueta «todo el día».
4. Abrir la entrega con `due_at` nulo: se muestra «sin fecha de cierre» y no aparece programada ninguna captura.
5. Cambiar la zona horaria del curso en Ajustes: la advertencia de zona discrepante aparece si difiere de la de Canvas, y los buckets se recalculan en el ciclo siguiente con constancia en `bitacora`.

---

## 13.17 Guía embebida al equipo docente

§2.1 del enunciado exige «prestar especial atención a la facilidad de uso, guiando adecuadamente al equipo docente en los procesos que requieren información proveniente de ambas plataformas», y §3.1 lo evalúa. La guía son **cinco piezas**, y ninguna sustituye a las otras.

### 13.17.1 (a) Checklist de progreso del curso

En `/cursos/{id}`. **Seis pasos derivados de datos persistidos, nunca de casillas que alguien marca a mano**, cada uno con enlace a la acción pendiente. El paso pendiente más alto aparece resaltado, y la primera vez que se entra a un curso sin tareas el checklist aparece desplegado.

| # | Paso | Qué muestra |
|---|---|---|
| 1 | Canvas vinculado | Con la identidad con la que la aplicación escribe |
| 2 | GitHub vinculado | Organización, alcance de la instalación y equipo `docentes` creado |
| 3 | Verificación ejecutada | «19 de 21 en verde, 2 advertencias», con fecha |
| 4 | Estudiantes sincronizados | «40 estudiantes, 2 secciones · actualizado hace 4 min» |
| 5 | Cuentas de GitHub | «**7 de 10** verificadas» |
| 6 | Primera tarea creada | O el enlace a crearla |

Endpoint: `GET /api/cursos/{id}/progreso`, que devuelve los seis pasos con su estado y su ruta de acción. **El checklist no puede mentir, porque no hay casilla que alguien marque por su cuenta.**

### 13.17.2 (b) Tooltips en todo término técnico

Desde un mapa único `término → glosa + definición` compartido con el vocabulario de §13.15.4: *installation*, *override*, SHA, *tag*, repositorio base, conjunto de grupos, sección, colaborador, *topic*, sujeto, versión de la entrega. Accesibles por teclado y por lector de pantalla.

### 13.17.3 (c) Panel «¿Cómo funciona esta pantalla?»

Uno por pantalla del inventario, lateral y plegable, con **tres párrafos fijos**: qué hace esta pantalla; **de dónde vienen los datos y cuánta antigüedad pueden tener**; y **qué NO hace la aplicación aquí** —que es donde los no-objetivos de §13.22 aparecen *in situ*—. Su estado abierto o cerrado se recuerda por persona en `localStorage`.

### 13.17.4 (d) Enlaces profundos con «Ya lo hice, sincronizar»

**Obligatorios para todo lo que la aplicación no hace.** Cada punto muestra la frase «Esto se configura en Canvas», el enlace exacto construido desde `canvas_base_url` o el `org_login`, y un botón que **encola** la sincronización correspondiente y devuelve su resultado.

**Los ocho puntos cubiertos:** crear un conjunto de grupos y asignar integrantes; configurar *overrides* de fecha; crear o editar una rúbrica; publicar el curso; abrir el período de calificación; crear la organización de GitHub; aprobar permisos pendientes de la App; desinstalar la App al cerrar el curso.

Si el enlace profundo fallara, **el botón «Ya lo hice, sincronizar» sigue cumpliendo su función**.

### 13.17.5 (e) Ayuda de la entrega, fuera de la aplicación

`docs/guia-revisor.md`, entregado por Canvas junto a la URL, con el recorrido sugerido de cinco minutos, la lista de no-objetivos de §13.22 y el vocabulario de §13.15.4.

### 13.17.6 Lo que se descarta, con su motivo

| Descartado | Motivo |
|---|---|
| **Página de ayuda o FAQ dentro de la aplicación** | El inventario de pantallas es cerrado, y una página de ayuda que nadie abre no cumple §4 mejor que una frase donde el usuario está trabajando. Su contenido vive en (c) y en (e) |
| **Tour guiado la primera vez** | El asistente de cuatro pasos ya **es** el recorrido guiado del único flujo que lo necesita, y un tour superpuesto es código que se rompe con cada cambio de interfaz en las tres semanas de mayor rotación del proyecto. Se sustituye por (a) |

### 13.17.7 Ayuda del lado del estudiante

Los estudiantes no entran a la aplicación, de modo que su ayuda vive donde ya están: la **descripción de la tarea de registro** en Canvas con un bloque «Problemas frecuentes»; el **anuncio de curso** fijado al inicio de cada tarea; el **`README.md` del repositorio base**, con la sección «Si algo no funciona»; y un **canal humano publicado** —el correo del equipo docente, con horario de días hábiles 09:00 a 18:00 (America/Santiago) y compromiso de respuesta en un día hábil—. Los textos son **los mismos** que la aplicación envía, porque están en el archivo único de mensajes.

En la interfaz esto se refleja en dos sitios: **cada estado de Pendientes y de la tabla de R2.3.11 lleva junto a sí la acción que lo resuelve**, y **el equipo puede previsualizar el texto que recibe el estudiante antes de enviarlo**.

**Criterios de aceptación de §13.17**

1. Crear un curso nuevo y comprobar que el checklist de progreso aparece desplegado, con el paso 1 resaltado, y que ningún paso admite marcarse a mano.
2. Completar la vinculación y comprobar que los pasos 1, 2 y 3 pasan a verde **por dato**, sin intervención.
3. Comprobar que los ocho puntos de (d) muestran su frase, su enlace y su botón, y que el botón encola un trabajo sin llamar a ninguna API dentro de la petición.
4. Abrir el panel «¿Cómo funciona esta pantalla?» en cada pantalla del inventario: los tres párrafos existen y el tercero nombra al menos un no-objetivo cuando lo hay.
5. Ejecutar el ensayo del 14 de septiembre aplicando el criterio: ningún paso del guion necesita explicación verbal para entenderse.

---

## 13.18 Accesibilidad

Se compromete una **lista mínima explícita de nueve reglas**, cada una convertida en criterio de aceptación y auditada con `axe` como puerta de CI. **No se compromete WCAG 2.1 AA completo**, y esa decisión se **declara por escrito** en `docs/guia-revisor.md` con su motivo: AA incluye criterios que en este producto son vacíos —subtítulos de medios que no existen— o directamente contradictorios con el alcance de escritorio declarado en §13.19, como el reflujo a 320 px.

| # | Regla | Criterio verificable |
|---|---|---|
| 1 | **Contraste** | 4,5:1 en texto normal; 3:1 en texto grande y en los bordes de los indicadores de estado. Verificado por `axe` |
| 2 | **Foco visible siempre** | Anillo de 2 px con contraste ≥ 3:1. `outline: none` sin sustituto está **prohibido** y lo detecta una regla de ESLint más `axe` |
| 3 | **Navegación completa por teclado** | En las cuatro superficies que importan: el asistente de cuatro pasos, las tablas de estado (R2.3.11), Pendientes y la pantalla de corrección con sus atajos (R2.7.3). Criterio: **el guion completo de la demostración se ejecuta sin ratón**, y se ensaya así el 14 de septiembre |
| 4 | **Etiquetas y errores de formulario** | Toda entrada con `<label>` asociado; todo error vinculado con `aria-describedby` y anunciado con `role="alert"` |
| 5 | **Ningún estado se comunica sólo por color** | Cada indicador es **icono SVG en línea + etiqueta textual en español**, y el color es el tercer canal, nunca el único. Conjunto único de doce iconos con `aria-hidden="true"`: **el significado lo lleva el texto** |
| 6 | **Tablas semánticas** | `<caption>` y `<th scope>`; encabezados ordenables con `aria-sort` |
| 7 | **Zoom al 200 %** | Sin pérdida de contenido ni de función en las vistas del guion |
| 8 | **Idioma declarado** | `lang="es-CL"` en el documento |
| 9 | **Regiones y salto** | `<main>`, `<nav>` y enlace «saltar al contenido» como primer foco |

**Los emojis quedan prohibidos como indicador de estado y en el producto entero**, con el motivo operativo escrito: se renderizan distinto en cada sistema operativo y navegador —la matriz declarada incluye cuatro—, un lector de pantalla los lee con nombres que no corresponden al estado, y **en un proyector a tres metros un círculo ámbar y uno rojo son indistinguibles**. La demostración se hace en proyector.

**Auditoría como puerta de CI.** `@axe-core/playwright` sobre **siete rutas** —`/acceso`, `/cursos`, `/cursos/{id}`, `/cursos/{id}/vinculacion`, `/cursos/{id}/pendientes`, `/cursos/{id}/tareas/{tid}/repositorios` y `/cursos/{id}/correccion`— con datos de `semilla_demo`, **fallando ante cualquier violación `critical` o `serious`**. Se ejecuta en cada *pull request* que toque el frontend y, completo, antes del **14 de septiembre** y del **2 de octubre**. Existe una vía de excepción anotada con motivo y fecha de corrección, visible en la revisión.

**Lighthouse se ejecuta como número informativo** (objetivo ≥ 95 en accesibilidad), **no como puerta**, porque su puntuación agrega heurísticas de distinto peso y un fallo real puede quedar enmascarado.

**Matriz de navegadores declarada:** Chrome, Edge y Firefox de escritorio en ventana normal y privada, más Safari de escritorio en ventana normal. **Safari en navegación privada queda fuera de alcance declarado.** La prueba en ventana privada antes del 16 de septiembre es criterio de aceptación, no una comprobación opcional.

**Criterios de aceptación de §13.18**

1. Ejecutar `axe` sobre las siete rutas: cero violaciones `critical` y cero `serious`.
2. Ejecutar el guion completo de la demostración **sin ratón**, de principio a fin.
3. Buscar `outline: none` en la hoja de estilos: cada coincidencia tiene sustituto visible con contraste ≥ 3:1.
4. Buscar cualquier emoji en el frontend y en el archivo de mensajes: no hay ninguno.
5. Recorrer las tablas de estado con un lector de pantalla: cada estado se anuncia con su etiqueta en español, no con el color ni con el nombre del icono.
6. Comprobar las cuatro combinaciones de la matriz de navegadores al menos una vez antes del 16 de septiembre, con constancia registrada.

---

## 13.19 Resoluciones, puntos de corte y comportamiento en pantalla estrecha

**Escritorio primero, con degradación legible en tablet y móvil para tres vistas nombradas.** El resto se declara «mejor en escritorio» y **no se rompe** en pantalla estrecha.

**Resolución de referencia: 1366×768.** Toda vista del guion de demostración está completa y legible a 1366×768 con el navegador al 100 %, **sin desplazamiento horizontal de página**. Segundo objetivo: 1920×1080.

| Punto de corte | Disposición |
|---|---|
| `≥ 1280 px` | Disposición completa, con el panel lateral «¿Cómo funciona esta pantalla?» visible si está desplegado |
| `768–1279 px` | Panel lateral plegado, navegación de pestañas con desplazamiento propio, tablas con su contenedor de desplazamiento horizontal |
| `< 768 px` | Versión de tarjetas **sólo** en las tres vistas de móvil |

**Las tres vistas que funcionan bien en móvil, y por qué cada una:**

1. **`/cursos/{id}/correccion`, «Mis asignaciones»** — un ayudante consultando qué le queda por corregir (R2.7.2). Tarjetas con sujeto, entrega, estado y enlace a la versión.
2. **`/cursos/{id}/pendientes`** — el profesor mirando qué está bloqueado (R2.2.6). El componente `ListaPendientes` en tarjetas, con la acción primaria por fila.
3. **El correo del informe diario** — se lee en el teléfono por definición (R2.6.4). Plantilla HTML **de una sola columna**, con alternativa en texto plano, **sin tablas anidadas de ancho fijo**.

**Vistas declaradas «mejor en escritorio»**, en la especificación y en `docs/guia-revisor.md`: el tablero de tarea (R2.5.1), la tabla de estado de repositorios (R2.3.11), el timeline (R2.5.10) y `/operacion`. En pantalla estrecha **no se ocultan**: muestran un aviso de una línea —«Esta vista está pensada para pantalla ancha»— y siguen siendo usables con su desplazamiento propio.

**Tablas anchas: desplazamiento horizontal propio, no versión de tarjetas.** El contenedor lleva `overflow-x: auto`; **el `body` nunca se desplaza en horizontal**; la **primera columna —nombre del estudiante o del grupo— queda fija**; y hay un indicador visual de que hay más columnas.

**Se declara fuera de alcance el tema oscuro**, con motivo: la demostración es en proyector y un único tema claro de alto contraste es lo que mejor se lee ahí; mantener dos paletas con los contrastes de §13.18 verificados en ambas duplicaría el trabajo sin destinatario.

**Prueba antes del 16 de septiembre.** En el ensayo del **14 de septiembre**, sobre el proyector real de la sala si está disponible y, si no, con el portátil forzado a **1366×768** y el navegador al 100 %. Lista de comprobación registrada: sin desplazamiento horizontal de página en ninguna vista del guion; texto de cuerpo ≥ 14 px; indicadores de estado legibles a tres metros —icono más etiqueta, no color solo—; el guion completo visible sin acercar; y las cuatro combinaciones de la matriz de navegadores comprobadas al menos una vez.

**Criterios de aceptación de §13.19**

1. Ejecutar la prueba de desbordamiento horizontal con Playwright a 1366×768 y a 390×844 sobre las siete rutas auditadas: el `body` no desborda en ninguna.
2. Abrir la tabla de repositorios con 200 filas a 1366×768: la primera columna queda fija, el indicador de más columnas es visible y la página no se desplaza en horizontal.
3. Abrir «Mis asignaciones» y Pendientes a 390×844: se muestran en tarjetas con su acción primaria por fila.
4. Abrir el tablero de tarea a 768 px: aparece el aviso «Esta vista está pensada para pantalla ancha» y la vista sigue siendo usable.
5. Registrar en `.workflow/mediciones/` la lista de comprobación del ensayo del 14 de septiembre, completa y firmada.

---

## 13.20 Régimen de alcance visible y superficie sin sesión

### 13.20.1 Las tres capas

Cada cosa que no está lista cae en **exactamente una** de estas tres capas, y la capa se decide con un criterio, no caso a caso.

| Capa | Cuándo se aplica | Cómo se ve |
|---|---|---|
| **1 · BLOQUEO con mensaje** | La acción **es alcanzable y sería estructuralmente incorrecta**, no simplemente no implementada | Se rechaza en el momento, diciendo qué configuración hay, qué se esperaba y qué hacer. **No se crea ninguna fila y no se toca ningún estado** |
| **2 · OCULTO por perfil de alcance** | Falta **un módulo entero**: una pantalla completa o un bloque autónomo del tablero | La ruta **no se registra en el backend** y el enlace no existe en la navegación. **No hay pantalla vacía, no hay «próximamente», no hay `404` accidental**: hay `404` de enrutado, que es honesto |
| **3 · DESHABILITADO con motivo** | Falta **una acción dentro de una pantalla que sí existe** y cuya ausencia sería desconcertante | Control presente, deshabilitado, con el motivo **visible sin pasar el cursor** y **la fecha comprometida** |

**Aplicación de capa 1, cerrada:** vincular un assignment **grupal** a una tarea individual; vincular un assignment cuyo conjunto de grupos difiera del de las entregas ya vinculadas; retirar al último profesor activo de un curso activo; pegar el token de otra persona; vincular una organización de GitHub ya vinculada a otro curso; completar la vinculación con el titular limitado a una sección.

**Aplicación de capa 3 bajo `parcial`, cerrada:** «Vincular otra entrega»; la modalidad **grupal** en la creación de tarea y los assignments grupales en el selector; la **columna «estado de captura»** de la línea de entregas, sustituida por la nota «el registro de versiones al cierre llega el 6 de octubre»; el **panel de excepciones** por estudiante y por grupo; los **cinco interruptores** de comunicación de la final; y **«regenerar mis enlaces de baja»** en `/perfil`.

**Los siete interruptores de comunicación existen y se muestran en los dos perfiles.** Bajo `parcial` están operativos **exactamente dos** —`repositorio_disponible` e `invitacion_aceptada`—; los **cinco restantes** —`recordatorio_mapeo`, `recordatorio_invitacion`, `proximidad_cierre`, `cambio_de_fecha` y `correccion_publicada`— se muestran **deshabilitados con el motivo visible y la fecha comprometida**. Lo que sostiene R2.2.5 el 16 de septiembre es el **botón manual** de Pendientes, con tope de 1 por estudiante y día y permiso `comunicacion.enviar`.

**«Próximamente» está prohibido como texto.** El texto siempre nombra la fecha comprometida.

### 13.20.2 La pantalla `/alcance` y la banda de cabecera

**`/alcance` no es un documento estático: se genera.** Publica la tabla de reparto requisito a requisito con tres columnas —requisito, qué se puede hacer hoy, cuándo llega lo que falta—, y **su tercera columna se calcula desde el catálogo de banderas**, no se teclea. Una bandera retirada convierte automáticamente su fila en «disponible desde DD-MM-YYYY». **No existe una segunda lista que mantener a mano.** Publica además la fecha de inicio del histórico del informe diario del curso.

**La banda de la cabecera cambia de texto una vez por bloque**, y enlaza siempre a `/alcance`:

| Período | Texto literal |
|---|---|
| 16 → 23 de septiembre | «Entrega parcial del 16 de septiembre. Esta versión cubre la creación del curso, la vinculación, el enrolamiento y la creación automática de repositorios. Ver el alcance completo.» |
| 24 de septiembre → 5 de octubre | «Versión en construcción hacia la entrega final del 6 de octubre. Ver qué está disponible hoy.» |

**La banda desaparece sola cuando no queda ninguna bandera activa**, el 5 de octubre a las 12:00. **No se retira a mano y no hay un interruptor para ocultarla.**

**`/alcance` no se retira: se congela.** Al eliminarse el catálogo, el generador escribe **una sola vez** la tabla resultante —todas las filas en «disponible», con su fecha— en un fichero versionado que `GET /api/alcance` sirve a partir de ese instante. La pantalla **queda accesible sin sesión hasta el 31 de octubre**, porque es la evidencia de que el recorte del 16 de septiembre fue deliberado y declarado.

### 13.20.3 Superficie sin sesión

Sólo estas rutas de interfaz existen sin sesión, y cada una lleva su limitador de tasa:

| Ruta de interfaz | Qué la autoriza | Límite |
|---|---|---|
| `/invitaciones/{token}` | Ninguna; pinta lo que devuelve `GET /api/invitaciones/{token}`, con el correo destinatario **enmascarado** | 60/min por IP truncada |
| `/alcance` | Ninguna | 60/min por IP truncada |
| `/privacidad` | Ninguna | 60/min por IP truncada |
| `GET` y `POST /baja/{token}` | Firma del token y alcance `(curso_id, usuario_id)` | 20/min por IP truncada |

**Ninguna de estas cuatro está destinada a un estudiante.** La aplicación **no expone ninguna ruta pública destinada a un estudiante**, ni de sólo lectura, ni de confirmación, ni de estado. Existe una **prueba de arquitectura** que recorre todas las rutas registradas y **falla la construcción** si aparece una ruta accesible sin sesión que no esté en la lista cerrada de rutas públicas.

**La página de baja nunca cambia nada con el `GET`.** El clic muestra una página que dice a qué curso y a qué dirección afecta y ofrece dos botones —«darme de baja» y «seguir suscrito»— que envían un `POST` con token anti-CSRF de formulario. Los escáneres de correo y los *prefetchers* siguen enlaces con `GET` y **no envían formularios**, de modo que **la baja involuntaria queda descartada sin depender del comportamiento de ningún cliente de correo**. Tras aplicar la baja, la misma página ofrece **«volver a suscribirme»**: la suscripción es bidireccional sin sesión.

**Página `429`.** Al superar un límite, la respuesta es una **página explicativa en español** con el tiempo de espera, no un error crudo del proveedor.

**Criterios de aceptación de §13.20**

1. Ejecutar `test_no_hay_rutas_publicas_de_estudiante`: enumera las rutas registradas y falla si aparece una sin sesión fuera de la lista cerrada.
2. Arrancar con `PERFIL_ALCANCE=parcial` y comprobar que los cinco interruptores de comunicación de la final aparecen **presentes y deshabilitados**, con motivo visible y la fecha «6 de octubre».
3. Buscar la palabra «próximamente» en todo el frontend: no aparece.
4. Abrir `/alcance` y comprobar que su tercera columna coincide con el estado real del catálogo de banderas, sin ninguna lista escrita a mano.
5. Con `PERFIL_ALCANCE=completo` y catálogo vacío: **ni la banda ni ninguna nota de capa 3 aparecen en ninguna pantalla**, y `/alcance` sigue respondiendo `200`.
6. Hacer `GET` sobre un enlace de baja y comprobar, en la base de datos, que la suscripción **no cambió**; hacer el `POST` y comprobar que cambió y que la pantalla lo confirma nombrando el curso.
7. Superar el límite de `/baja/{token}` desde una IP: se devuelve la página `429` en español, no un error crudo.

---

## 13.21 Puertas de verificación de este capítulo

Estas comprobaciones se ejecutan en integración continua y **fallan la construcción**. No son recomendaciones.

| Puerta | Qué comprueba | Sección |
|---|---|---|
| `test_alcanzabilidad` (modos `parcial` y `completo`) | Cada requisito es alcanzable por el rol de menor privilegio que el enunciado nombra; cada ruta declarada no registrada devuelve `404` de enrutado | §13.2, §13.3, §13.6 |
| Puerta de rutas por perfil | Falla si aparece registrada una ruta declarada oculta en el perfil en curso, y falla si aparece registrada una ruta sin sesión que no figure en la lista cerrada | §13.3, §13.20 |
| `test_todo_codigo_tiene_etiqueta` | Todo código de las siete máquinas de estado y de los catálogos cerrados tiene etiqueta en español | §13.2, §13.11 |
| Cobertura del catálogo de errores | Los 51 tipos de incidencia, los 7 subtipos de `ERROR_PERMANENTE`, los 6 motivos de `DEGRADADO` y los motivos de `ESPERANDO_INFORMACION` tienen texto y acción | §13.11 |
| Cobertura de estados vacíos | Todo código de causa devuelto por un endpoint de listado tiene entrada en el catálogo | §13.10 |
| `test_consistencia_de_cifras` | El tablero, la tabla de repositorios, Pendientes y el informe diario devuelven los mismos números sobre el mismo conjunto de datos | §13.2, §13.8 |
| Predicados prohibidos | Ningún consumidor escribe su propio `WHERE` de exclusión fuera de la capa de consulta única | §13.2 |
| `no-literal-strings` (ESLint) | No hay cadenas visibles fuera del archivo único de mensajes | §13.15 |
| Cadenas acentuadas en backend | No hay texto de presentación fuera del módulo de mensajes | §13.15 |
| Términos prohibidos | Ninguna palabra de la columna «no se dice» aparece en textos, plantillas ni especificación, fuera de las excepciones anotadas | §13.15 |
| `@axe-core/playwright` sobre siete rutas | Cero violaciones `critical` y `serious` | §13.18 |
| Desbordamiento horizontal | El `body` no desborda a 1366×768 ni a 390×844 en las siete rutas | §13.19 |
| `dangerouslySetInnerHTML` | Sólo existe dentro de `HtmlSaneado` | §13.7 |
| Antigüedad sin componente | Falla si una pantalla pinta una antigüedad sin usar `SelloAntiguedad` | §13.7, §13.8 |
| Contrato de autorización | Falla si una ruta bajo `/api/cursos/{curso_id}` o bajo `/api/operacion/**` se registra sin su dependencia de permiso y su acotación por curso | §13.3, §13.5 |

---

## 13.22 Fuera de alcance declarado, y dónde se dice en pantalla

La lista de no-objetivos es **cerrada**. Un no-objetivo que no esté en la lista **no es un no-objetivo: es un hueco**. Ampliarla es una decisión que se escribe con fecha y motivo. Vive en dos sitios —esta sección y `docs/guia-revisor.md`— y **cada no-objetivo con consecuencia en una pantalla se dice también *in situ***, porque una ausencia explicada en pantalla no se lee igual que un hueco mudo.

| # | No-objetivo | Motivo | Dónde se dice *in situ* |
|---|---|---|---|
| 1 | Autograding o ejecución de tests sobre la versión capturada | Ningún requisito lo pide; la aplicación no descarga ni archiva el código, sólo entrega enlaces | Pantalla de corrección, junto al enlace por SHA |
| 2 | Detección de similitud o plagio entre repositorios | No lo pide ningún requisito; exigiría descargar código | `docs/guia-revisor.md` |
| 3 | Comentarios de código línea a línea dentro de la aplicación | R2.7.4 pide **acceder** a la versión, no comentarla; el comentario de código vive en GitHub y el de la entrega en Canvas | Pantalla de corrección |
| 4 | Cualquier interfaz para estudiantes | §1 del enunciado | Personas |
| 5 | Crear o editar secciones, grupos e inscripciones en Canvas | R2.2.1–R2.2.3 dicen «obtener», no crear | Personas y grupos, con enlace profundo a Canvas y botón «Ya lo hice, sincronizar» |
| 6 | Editar rúbricas | §2.7 del enunciado: «las rúbricas y las calificaciones deberán mantenerse en Canvas» | Pantalla de corrección, sobre la rúbrica |
| 7 | Entregas sin tarea de Canvas asociada | R2.3.1 y R2.3.2 atan cada entrega a una tarea de Canvas | Tarea → Entregas |
| 8 | Estudiantes que no provienen de Canvas (oyentes) | §2.2: la información de estudiantes proviene de Canvas | Personas |
| 9 | GitHub Enterprise Server | Entrada fija del equipo: organización nueva y gratuita en GitHub.com | `docs/guia-revisor.md` |
| 10 | Notificaciones por Slack, WhatsApp o cualquier canal fuera de Canvas y correo | R2.6.4 dice email y R2.6.5/R2.6.6 dicen Canvas | `/cursos/{id}/mis-notificaciones` |
| 11 | Importar desde GitHub Classroom | Ningún requisito lo pide; el repositorio base lo crea la aplicación | `docs/guia-revisor.md` |

**Se añaden a la lista, porque el evaluador podría buscarlos:** reconstruir la relación de cursos con *cross-listing*; publicar nota en entregas moderadas o anónimas; los formatos de nota `gpa_scale` y `not_graded`; protección de tags y *rulesets*; el distintivo «Verified» de la GitHub App; **Safari en ventana privada**; **tema oscuro y versión de tarjetas de las tablas anchas**; los *differentiation tags* de Canvas como generadores de repositorio; y **WCAG 2.1 AA completo como compromiso formal**, sustituido por las nueve reglas de §13.18.

**Regla de mantenimiento.** Cada fila cita el motivo por el que **no** corresponde a ningún requisito `R2.x.y`, y la tabla de trazabilidad se revisa contra esta lista antes de cada entrega: **si un no-objetivo aparece en la trazabilidad, la lista está mal y cede la lista**.

**Criterios de aceptación de §13.22**

1. Comprobar que las once frases *in situ* existen en el archivo único de mensajes y aparecen en las pantallas indicadas.
2. Cruzar la lista contra la tabla de trazabilidad requisito → decisiones: ningún no-objetivo aparece como cobertura de un requisito.
3. Comprobar que `docs/guia-revisor.md` contiene la lista completa, el vocabulario y el recorrido sugerido de cinco minutos.
4. Comprobar que la declaración de no comprometer WCAG 2.1 AA completo aparece por escrito en `docs/guia-revisor.md` con las nueve reglas y su motivo.
