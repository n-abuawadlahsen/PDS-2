# 3. Modelo de dominio y datos

## 3.0 Qué fija este capítulo y cómo se lee

Este capítulo es la definición normativa del modelo de datos de la aplicación: **todas** las entidades persistidas, sus campos, sus claves, sus unicidades y sus relaciones; qué información se copia desde Canvas y desde GitHub y qué información se consulta en vivo sin copiarse; y qué se conserva, qué se supersede y qué se purga.

El lector de este capítulo no necesita haber leído ningún otro documento. Todo lo que hace falta para escribir la migración inicial y los modelos de persistencia está aquí.

**Qué NO fija este capítulo.** Las tablas de transición de las máquinas de estado —qué transición es legal desde qué estado y con qué disparador— **no viven en un capítulo único**: cada una se fija en el capítulo funcional dueño de la entidad que gobierna. `curso.estado` en el capítulo 4; `acceso_repositorio` («máquina 3», citada así en el capítulo 7) y el estado del propio `repositorio` en el capítulo 8; `version_entrega` en el capítulo 9; el estado de la corrección en el capítulo 12; `mensaje_saliente` («máquina 7») en el capítulo 11. Aquí se declara el **catálogo cerrado de valores** de cada columna de estado, porque ese catálogo es una restricción del esquema (`CHECK`) y viaja en la migración inicial. Los contratos de las llamadas a Canvas y a GitHub se fijan en los capítulos de integraciones (5 y 6); las reglas de autorización, en el capítulo 2 y en el de gobierno.

**Vocabulario de la especificación.** «La aplicación registra», «la fila se supersede», «el índice impide». No hay condicionales: cada frase de este capítulo describe una obligación verificable contra la base de datos desplegada.

**Procedencia.** Cada sección cita entre paréntesis los requisitos `R2.x.y` del enunciado que satisface y las decisiones `A-nnn` de la carta de arquitectura y `RG-nnn` de las actas de reconciliación de las que proviene. Donde una decisión de la carta fue anulada por una regla del acta, se escribe únicamente la regla vigente.

---

## 3.1 Convenciones transversales del esquema

**Requisitos:** todos, por dependencia de esquema · **Decisiones:** A-073, A-074, RG-046, RG-048, RG-049, RG-192, RG-193, RG-203, A-200

### 3.1.1 Reglas de forma

| # | Regla | Verificación |
|---|---|---|
| C-01 | Toda tabla tiene clave primaria propia `id uuid` (UUID **v7**, ordenable por tiempo), salvo las tablas cuya clave natural es un par de claves foráneas, enumeradas en C-02 | Prueba de arquitectura sobre los modelos |
| C-02 | Tablas con clave primaria compuesta y sin `id` propio: `sesion_membresia`, `visibilidad_entrega`, `metrica_repositorio_dia`, `participacion_entrega`, `suscripcion_informe`, `estado_canvas_submission`, `exposicion_entrega`, `resumen_tarea`, `preferencia_vista`, `cubo_tasa`, `salud_proveedor_curso`, `estado_sistema`, `autoria_commit`, `instalacion_github` (su PK es `installation_id`), `accion_ui` (su PK es `clave`) | Lista cerrada; ampliarla es una decisión que se registra |
| C-03 | **Ningún identificador externo es clave primaria.** Canvas fusiona usuarios y GitHub renombra cuentas | Prueba de arquitectura |
| C-04 | Los identificadores externos viven en columnas propias de tipo `bigint`, con índice único donde corresponda | Revisión de la migración |
| C-05 | Nombres de tabla y de columna en **español**, `snake_case`, **singular** | Prueba de arquitectura |
| C-06 | Toda tabla lleva `creado_en` y `actualizado_en` | Prueba de arquitectura |
| C-07 | Toda tabla espejo lleva además `sincronizado_en` y `origen ∈ {CANVAS, GITHUB, DOCENTE, SISTEMA}` | Prueba de arquitectura |
| C-08 | **Todo instante es `timestamptz` en UTC.** No existe una sola columna `timestamp` sin zona en el esquema. Ningún cálculo de negocio usa hora local: la zona horaria es exclusivamente una propiedad de presentación (A-073) | Prueba de arquitectura que recorre el esquema desplegado |
| C-09 | Las dos únicas columnas de tipo `date` del esquema son `metrica_repositorio_dia.dia` e `informe_diario.fecha`, y **las dos están expresadas en la zona horaria del curso**, declarada en `curso.zona_horaria` (A-152, A-171) | Comentario de columna obligatorio en la migración |
| C-10 | Toda clave foránea se declara `ON DELETE RESTRICT ON UPDATE RESTRICT`. **No existe `CASCADE` ni `SET NULL` en ninguna migración** (RG-048) | Prueba de arquitectura: falla la construcción si una migración contiene `ON DELETE CASCADE` u `ON DELETE SET NULL` |
| C-11 | Toda clave foránea es `NOT NULL` salvo la lista cerrada de §3.17.3, y cada excepción lleva comentario de columna con su motivo | Prueba de arquitectura |
| C-12 | Todo enumerado del sistema se declara en `backend/app/dominio/estados.py` y el `CHECK` de su columna se **genera** desde esa declaración. **No existe ningún enumerado fuera de ese módulo**, tampoco en los adaptadores (RG-203) | Pruebas `test_check_coincide_con_enum` y `test_todo_codigo_tiene_etiqueta`, que fallan la construcción |
| C-13 | Todo código de todo catálogo cerrado tiene **etiqueta en español** en el archivo único de mensajes; ninguna pantalla muestra jamás el código (A-155) | `test_todo_codigo_tiene_etiqueta` |
| C-14 | **Hay una sola migración de esquema y es anterior al 16 de septiembre de 2026.** Crea las 72 entidades del censo, todas sus columnas y **todos** los valores de todos los catálogos cerrados, incluidos los que ningún código escribirá hasta la entrega final (RG-193) | Puerta 7 de CI: ningún fichero de migración posterior al 16 de septiembre con `DROP`, `ALTER … TYPE`, cambio de clave o de unicidad |
| C-15 | Una prueba de arranque compara el esquema desplegado con el esperado y **falla el arranque** si falta una columna, un índice o un valor de catálogo | Arranque de la aplicación |

### 3.1.2 Regla de identidad frente a los sistemas externos

**Toda entidad espejada de un sistema externo se identifica por el identificador numérico de ese sistema, nunca por nombre, correo ni login** (A-074, «Ley 3»).

| Entidad externa | Identidad | Por qué no otra cosa |
|---|---|---|
| Estudiante | `estudiante.canvas_user_id` (`bigint`) | `sis_user_id` puede no venir con rol de profesor; el correo no tiene visibilidad garantizada |
| Matrícula | `matricula.canvas_enrollment_id` (`bigint`) | Una persona tiene varias matrículas (dos secciones) |
| Sección | `seccion.canvas_section_id` (`bigint`) | — |
| Grupo y conjunto de grupos | `grupo.canvas_group_id`, `conjunto_grupos.canvas_group_category_id` | — |
| Assignment de Canvas | `entrega.canvas_assignment_id`, `assignment_canvas.canvas_assignment_id` | — |
| Cuenta de GitHub | `cuenta_github.github_user_id` (`bigint`) | El `login` cambia **y el antiguo queda libre para que otra persona lo reclame** |
| Repositorio de GitHub | `repositorio.github_repo_id` (`bigint`) | El nombre puede cambiar por acción de un estudiante |
| Instalación de la GitHub App | `instalacion_github.installation_id` (`bigint`) | — |

`estudiante.sis_user_id` y `estudiante.login_id` se persisten cuando la instancia los entrega, **exclusivamente como claves de reconciliación** ante una fusión de usuarios en Canvas, **nunca como identidad**.

El `login` de GitHub y el nombre del repositorio se persisten como **dato de presentación** y se revalidan; ninguna consulta de negocio los usa como criterio de unión.

### 3.1.3 Criterios de aceptación de §3.1

1. Una consulta sobre el catálogo del sistema no devuelve ninguna columna de tipo `timestamp without time zone`.
2. Una consulta sobre las restricciones de clave foránea del esquema desplegado devuelve `RESTRICT` en la regla de borrado y de actualización de **todas** ellas.
3. El fichero de la migración inicial contiene 72 sentencias de creación de tabla y ningún `ALTER … TYPE`.
4. Renombrar un valor de un enumerado en `dominio/estados.py` sin regenerar el `CHECK` **rompe la construcción** en la prueba `test_check_coincide_con_enum`.
5. Retirar la etiqueta en español de cualquier código **rompe la construcción** en `test_todo_codigo_tiene_etiqueta`.
6. Toda tabla del censo tiene `creado_en` y `actualizado_en`; toda tabla espejo tiene además `sincronizado_en` y `origen`.

---

## 3.2 Censo cerrado de entidades

**Requisitos:** todos · **Decisiones:** RG-046, RG-192, A-198, RG-193

El sistema tiene un **censo cerrado** de entidades. La lista se declara en `backend/app/dominio/censo.py` y **una prueba de arquitectura falla la construcción si existe un modelo de persistencia que no está en ella**. Añadir una entidad es una decisión que se registra en la carta de arquitectura, igual que añadir un tipo de incidencia.

**`integrante_version_entrega` no existe** (la composición congelada del grupo vive en `version_entrega.integrantes`) y **`commit_autoria` no existe** (el nombre es `autoria_commit`).

> **[DECISION NUEVA] El censo se declara con 72 entradas, no con 70.** RG-046, RG-192 y A-198 fijan el censo como «las 47 entidades de A-075 a A-087 más 23 nuevas». La enumeración literal de las tablas de A-075 a A-087 arroja **49** filas, no 47: el número 47 es un error de suma en la carta, arrastrado desde su revisión 1. **No se añade ni se retira ninguna entidad respecto de lo que las actas fijan**; sólo se corrige el total, que pasa a 49 + 23 = **72**. La prueba de `censo.py` se escribe contra la **enumeración**, nunca contra la cifra, y ninguna otra decisión depende del número. Donde el acta o la carta digan «70 entidades», se lee «las entidades del censo».

### 3.2.1 Las 72 entidades, por bloque

| # | Entidad | Bloque | Origen | Entrega |
|---|---|---|---|---|
| 1 | `usuario` | Identidad y gobierno | Propia | Parcial |
| 2 | `identidad_canvas_usuario` | Identidad y gobierno | Propia | Parcial |
| 3 | `sesion` | Identidad y gobierno | Propia | Parcial |
| 4 | `sesion_membresia` | Identidad y gobierno | Propia | Parcial |
| 5 | `invitacion_equipo` | Identidad y gobierno | Propia | Parcial |
| 6 | `curso` | Identidad y gobierno | Propia | Parcial |
| 7 | `membresia_curso` | Identidad y gobierno | Propia | Parcial |
| 8 | `credencial_canvas` | Identidad y gobierno | Propia | Parcial |
| 9 | `instalacion_github` | Identidad y gobierno | Espejo GitHub | Parcial |
| 10 | `equipo_github_curso` | Identidad y gobierno | Espejo GitHub | Parcial |
| 11 | `verificacion_vinculacion` | Identidad y gobierno | Propia | Parcial |
| 12 | `intento_instalacion_github` | Identidad y gobierno | Propia | Parcial |
| 13 | `verificacion_canal` | Identidad y gobierno | Propia | Parcial |
| 14 | `seccion` | Espejo de Canvas | Espejo Canvas | Parcial |
| 15 | `estudiante` | Espejo de Canvas | Espejo Canvas | Parcial |
| 16 | `matricula` | Espejo de Canvas | Espejo Canvas | Parcial |
| 17 | `conjunto_grupos` | Espejo de Canvas | Espejo Canvas | Parcial |
| 18 | `grupo` | Espejo de Canvas | Espejo Canvas | Parcial |
| 19 | `pertenencia_grupo` | Espejo de Canvas | Espejo Canvas | Parcial |
| 20 | `assignment_canvas` | Espejo de Canvas | Espejo Canvas | Parcial |
| 21 | `cuenta_github` | Puente Canvas ↔ GitHub | Espejo GitHub | Parcial |
| 22 | `mapeo_github` | Puente Canvas ↔ GitHub | Propia | Parcial |
| 23 | `tarea` | Tareas, entregas y fechas | Propia | Parcial |
| 24 | `entrega` | Tareas, entregas y fechas | Espejo Canvas | Parcial |
| 25 | `visibilidad_entrega` | Tareas, entregas y fechas | Derivada | Parcial |
| 26 | `sujeto` | Tareas, entregas y fechas | Derivada | Parcial |
| 27 | `regla_fecha` | Tareas, entregas y fechas | Espejo Canvas | Parcial |
| 28 | `fecha_efectiva` | Tareas, entregas y fechas | Derivada | Parcial |
| 29 | `repositorio_base` | Tareas, entregas y fechas | Espejo GitHub | Parcial |
| 30 | `archivo_repositorio_base` | Tareas, entregas y fechas | Espejo GitHub | Parcial |
| 31 | `exposicion_entrega` | Tareas, entregas y fechas | Derivada | Parcial |
| 32 | `cambio_fecha` | Tareas, entregas y fechas | Propia | Final |
| 33 | `repositorio` | Repositorios y accesos | Espejo GitHub | Parcial |
| 34 | `acceso_repositorio` | Repositorios y accesos | Espejo GitHub | Parcial |
| 35 | `acceso_docente_repositorio` | Repositorios y accesos | Espejo GitHub | Parcial |
| 36 | `version_entrega` | Versiones de entrega | Evidencia | Parcial |
| 37 | `identidad_git` | Actividad | Derivada | Parcial |
| 38 | `commit` | Actividad | Espejo GitHub | Parcial |
| 39 | `autoria_commit` | Actividad | Derivada | Parcial |
| 40 | `evento_push` | Actividad | Espejo GitHub | Parcial |
| 41 | `evento_webhook` | Actividad | Espejo GitHub | Parcial |
| 42 | `metrica_repositorio_dia` | Actividad | Derivada | Parcial |
| 43 | `participacion_entrega` | Actividad | Derivada | Parcial |
| 44 | `cursor_sincronizacion` | Actividad | Propia | Parcial |
| 45 | `hito_repositorio` | Actividad | Propia | Final |
| 46 | `resumen_tarea` | Actividad | Caché declarada | Final |
| 47 | `asignacion_correccion` | Corrección | Propia | Parcial |
| 48 | `correccion` | Corrección | Propia | Parcial |
| 49 | `publicacion_nota` | Corrección | Evidencia | Parcial |
| 50 | `estado_canvas_submission` | Corrección | Espejo Canvas | Final |
| 51 | `nota_interna_correccion` | Corrección | Propia | Final |
| 52 | `regla_comunicacion` | Comunicaciones | Propia | Parcial |
| 53 | `mensaje_saliente` | Comunicaciones | Propia | Parcial |
| 54 | `plantilla_mensaje` | Comunicaciones | Propia | Parcial |
| 55 | `suscripcion_informe` | Comunicaciones | Propia | Parcial |
| 56 | `informe_diario` | Comunicaciones | Propia | Parcial |
| 57 | `supresion_comunicacion` | Comunicaciones | Propia | Final |
| 58 | `ventana_supresion` | Comunicaciones | Propia | Final |
| 59 | `incidencia` | Incidencias y auditoría | Propia | Parcial |
| 60 | `bitacora` | Incidencias y auditoría | Evidencia | Parcial |
| 61 | `trabajo` | Infraestructura del dominio | Propia | Parcial |
| 62 | `trabajo_periodico` | Infraestructura del dominio | Propia | Parcial |
| 63 | `sincronizacion` | Infraestructura del dominio | Propia | Parcial |
| 64 | `cubo_tasa` | Infraestructura del dominio | Propia | Parcial |
| 65 | `presupuesto_api` | Infraestructura del dominio | Propia | Parcial |
| 66 | `salud_proveedor_curso` | Infraestructura del dominio | Propia | Parcial |
| 67 | `estado_sistema` | Infraestructura del dominio | Propia | Parcial |
| 68 | `resultado_invariante` | Infraestructura del dominio | Propia | Parcial |
| 69 | `respaldo` | Infraestructura del dominio | Propia | Parcial |
| 70 | `accion_ui` | Infraestructura del dominio | Propia | Final |
| 71 | `cambio_pendiente` | Infraestructura del dominio | Propia | Final |
| 72 | `preferencia_vista` | Infraestructura del dominio | Propia | Final |

### 3.2.2 Qué significa la columna «Entrega»

**Las 72 tablas se crean en la migración inicial, todas, antes del 16 de septiembre.** La columna «Entrega» dice **qué tablas empiezan a escribirse antes del 16 de septiembre** y cuáles nacen vacías y empiezan a escribirse con la entrega final. Crear doce tablas vacías cuatro semanas antes no cuesta nada y elimina la única migración que podía fallar delante del evaluador (RG-193).

El criterio de reparto es: una tabla es de la parcial si un requisito demostrado el 16 de septiembre escribe en ella, **o** si añadirla después obligaría a migrar filas ya creadas o a reconstruir un hecho que ya no será observable. Es el motivo por el que `autoria_commit` es de la parcial: los co-autores llegan del enriquecimiento del grafo en el mismo lote de ingesta, y reconstruirlos después obliga a reconsultar la API commit a commit.

`docs/operacion.md` declara qué tablas nacen vacías y qué bloque de trabajo las empieza a escribir.

### 3.2.3 Criterios de aceptación de §3.2

1. `backend/app/dominio/censo.py` contiene exactamente las 72 entradas de la tabla anterior.
2. Añadir un modelo de persistencia sin añadirlo al censo **rompe la construcción**.
3. Escribir en `bitacora.entidad` un valor que no sea uno de esos 72 nombres, más el literal `sistema`, **rompe la construcción**.
4. Tras aplicar la migración inicial en una base vacía, una consulta al catálogo devuelve 72 tablas de dominio.
5. Ninguna de las doce tablas marcadas «Final» tiene filas el 16 de septiembre, y ninguna falta en el esquema.

---
