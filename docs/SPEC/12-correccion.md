# 12. Corrección y publicación de notas

Este capítulo especifica cómo el equipo docente reparte el trabajo de corrección, corrige una
entrega, accede al código exacto que debe revisar, evalúa la rúbrica de Canvas, calcula y publica la
nota, y sigue el avance de la corrección de una tarea. Cubre los siete requisitos del área **R2.7**
del enunciado y las decisiones de la carta de arquitectura y del acta de reconciliación que los
sostienen.

---

## 12.1 Alcance, vocabulario y orden de precedencia

### 12.1.1 Qué entra y qué no entra en este capítulo

| Entra | No entra (y dónde está) |
|---|---|
| Reparto de entregas entre correctores, con sus cuatro mecánicas | Alta y retiro de miembros del equipo docente (capítulo de equipo y permisos) |
| Bandeja del corrector, navegación y atajos | Captura de la versión del repositorio (capítulo de versiones de entrega) |
| Pantalla de corrección y sus estados borde | Aprovisionamiento de repositorios y acceso del estudiante |
| Lectura y evaluación de la rúbrica de Canvas | Creación o edición de rúbricas: **la aplicación no crea rúbricas** |
| Cálculo, validación y publicación de la nota, el comentario y la rúbrica en Canvas | Redacción y despacho de comunicaciones al estudiante (capítulo de comunicaciones); aquí sólo se fija **cuándo** se encola el evento |
| Contraste con lo que Canvas tiene y estado de avance por tarea | Informe diario completo (capítulo de informes); aquí sólo su sección de avance |
| Reclamos sobre una entrega y panel de evidencia | Timeline de actividad del repositorio (capítulo de seguimiento) |

**Los estudiantes no son usuarios de la aplicación.** No abren la pantalla de corrección, no ven
notas internas y no registran reclamos por sí mismos. Lo único que les llega es lo que la aplicación
escribe **en Canvas**: la nota, el comentario de la entrega y la evaluación de rúbrica.

### 12.1.2 Vocabulario cerrado del capítulo

| Término | Significado exacto |
|---|---|
| **Sujeto** | La unidad que se corrige: un estudiante en una tarea individual, un grupo en una tarea grupal. Fila de `sujeto`. |
| **Entrega** | Un `assignment` de Canvas vinculado a una tarea de la aplicación. Una tarea tiene entregas parciales y una final, y **cada una se corrige de forma independiente**. |
| **Corrección** | La fila `correccion (entrega_id, sujeto_id)`. Es el borrador y el registro local del trabajo del corrector. |
| **Asignación** | La fila `asignacion_correccion (entrega_id, sujeto_id)` que dice **quién** corrige ese par. |
| **Versión registrada** | La fila `version_entrega` vigente de ese par: el SHA capturado a la fecha efectiva de cierre. Es lo que se corrige. |
| **Publicación** | La escritura de nota, comentario y rúbrica en Canvas mediante `PUT .../submissions/:user_id`. |
| **Conjunto congelado** | La lista de integrantes del grupo en el instante de la captura, guardada en `version_entrega.integrantes`. Es a quién se califica. |
| **Corrector real** | La persona que escribió el borrador (`correccion.corrector_usuario_id`), que **no** es necesariamente quien pulsa publicar ni el titular del token de Canvas. |
| **Credencial operativa** | El token personal de Canvas de un profesor del curso con `orden_respaldo = 0`. Toda escritura en Canvas se hace con ella. |

### 12.1.3 Reglas transversales que este capítulo obedece sin excepción

| # | Regla | Origen |
|---|---|---|
| 1 | Ninguna pantalla llama a Canvas ni a GitHub para pintarse. La única excepción es la rúbrica, que es lectura en vivo con caché de 15 minutos. | Ley 1, A-089, A-119, A-137 |
| 2 | Nada se sobrescribe ni se borra: `publicacion_nota` es *append-only*, `version_entrega` es inmutable, `nota_interna_correccion` es *append-only*. | Ley 2, A-030, A-085, A-087 |
| 3 | La evidencia de qué se evaluó es el `commit_sha` en la base propia, no la etiqueta de GitHub. | Ley 4, A-104 |
| 4 | Todo estado se muestra traducido al español con etiqueta fija; los identificadores técnicos (SHA, login, URL) van en monoespaciada con botón de copiado; los errores de Canvas se muestran **literales** bajo una explicación en español. | A-155 |
| 5 | Todo instante se muestra en la zona horaria del curso con la zona escrita al lado: `dd-MM-yyyy HH:mm (America/Santiago)`. **Nunca una hora desnuda.** | A-152 |
| 6 | Toda acción con consecuencia queda en `bitacora` con actor, entidad, `antes` y `despues`, en la misma transacción que el efecto. | A-029, A-115 garantía 2 |
| 7 | Contra Canvas hay **una sola petición simultánea por curso**, impuesta por `pg_advisory_lock` sobre el espacio de cerrojo de Canvas. | A-039, RG-062 |
| 8 | Nada cambia de responsable, de nota o de versión en silencio: todo efecto se ve en pantalla antes de aplicarse. | A-036, A-147 |

### 12.1.4 Precedencia: dónde el acta corrige a las respuestas de alcance

El acta de reconciliación manda sobre la carta y sobre las respuestas de alcance. Estos ocho puntos
son los que un implementador puede encontrar contradichos en documentos anteriores; **manda siempre
la columna derecha**.

| Lo que decía una respuesta de alcance | Lo que rige |
|---|---|
| `NO_PUBLICABLE` es el noveno estado de la corrección | **No es un estado.** La máquina 5 tiene **ocho** estados y la imposibilidad de publicar es la bandera `publicable` con `motivo_no_publicable` de diez valores (RG-032, RG-205, A-214) |
| `ESPERANDO_CREDENCIAL` es un estado lateral de la corrección | La corrección se queda en `PUBLICANDO`; la espera vive en el **trabajo** (RG-033, A-214 punto 4) |
| `asignacion_correccion.estado ∈ {ASIGNADA, SIN_CORRECTOR}` | La columna **no existe**. Hay un solo estado persistido, `correccion.estado` (RG-034, A-206 punto 4) |
| `correccion` tiene columnas espejo `canvas_*` y `contraste_canvas` | **No las tiene.** El espejo es `estado_canvas_submission`, por estudiante, y `contraste_canvas` es una **derivación** (RG-031, RG-187, A-206) |
| El tercer valor del contraste se llama `DISCREPA` | Se llama **`DIVERGE`** (RG-186) |
| El conjunto congelado vive en la tabla `integrante_version_entrega` | Vive en **`version_entrega.integrantes jsonb`**; esa tabla no existe (RG-028, A-204) |
| Existe la acción «calificar individualmente a cada integrante en Canvas», que escribe el assignment | **No existe.** La aplicación no modifica ningún campo del assignment vinculado; la pantalla explica y ofrece un enlace profundo a Canvas (RG-082) |
| La matriz nominal de estado exige `correccion.asignar`; existen los trabajos `verificar_publicacion_notas` y `publicar_notas_lote` | La matriz nominal se lee con **`curso.ver`** (RG-125); **ninguno de esos dos trabajos existe** (RG-101, RG-194) |

**Las columnas `criterio`, `criterio_seccion_id`, `desalineada_motivo` y `desalineada_en` de
`asignacion_correccion` se conservan**: RG-034 retira únicamente la columna `estado` y no arbitra
sobre las demás.

---

## 12.2 Modelo de datos de la corrección

### 12.2.1 Grano: el par `(entrega, sujeto)`

La unidad de asignación y de corrección es **el par `(entrega, sujeto)`, y ninguna otra**. No es
`(entrega, repositorio)` —un sujeto puede aparecer en el reparto sin repositorio todavía— ni
`(entrega, estudiante)` —en una tarea grupal el sujeto es el grupo, se corrige una vez y se publica
una vez—. **No hay herencia entre entregas de una misma tarea**: cada entrega se reparte y se
corrige por separado, porque el enunciado exige en §2.7 que cada entrega pueda corregirse de manera
independiente (A-134).

La única tabla con grano de estudiante es `publicacion_nota`, y la única tabla espejo con grano de
estudiante es `estado_canvas_submission`, porque Canvas devuelve `score` y `graded_at` por persona.

*Requisitos: **R2.7.1**, **R2.7.6**, **R2.7.7**. Decisiones: A-081, A-087, A-134, A-139, RG-031.*

### 12.2.2 `asignacion_correccion`

| Columna | Tipo | Regla |
|---|---|---|
| `id` | uuid | Clave primaria |
| `entrega_id` | uuid | FK a `entrega`, `ON DELETE RESTRICT` |
| `sujeto_id` | uuid | FK a `sujeto`, `ON DELETE RESTRICT` |
| `membresia_id` | uuid **nullable** | FK a `membresia_curso`. Nulo significa «sin corrector» |
| `asignada_por` | uuid | Membresía que aplicó el reparto. **Se conserva aunque después se vacíe `membresia_id`** |
| `asignada_en` | timestamptz | Instante del reparto |
| `iniciada_en` | timestamptz nullable | Primera apertura de la pantalla por el corrector. **No se borra nunca, ni al reasignar** |
| `criterio` | text | `MANUAL \| EQUITATIVO \| SECCION \| COPIA_ENTREGA_ANTERIOR` |
| `criterio_seccion_id` | uuid nullable | Sección usada cuando `criterio = SECCION` |
| `desalineada_motivo` | text nullable | `CAMBIO_DE_SECCION \| CAMBIO_DE_GRUPO` |
| `desalineada_en` | timestamptz nullable | Cuándo se detectó la desalineación |

**Unicidad `(entrega_id, sujeto_id)`**, en la base de datos y no en el código: es la garantía de que
hay **exactamente un corrector por entrega y sujeto**. **No existe la columna `estado`** (RG-034).

**Invariante comprobado por prueba automatizada:** `asignacion_correccion.membresia_id IS NULL` si y
sólo si `correccion.estado = 'SIN_CORRECTOR'`.

### 12.2.3 `correccion`

Una fila por `(entrega_id, sujeto_id)`, con unicidad sobre ese par.

| Bloque | Columnas |
|---|---|
| **Identidad** | `id`, `entrega_id`, `sujeto_id`, `version_entrega_id` (FK a la versión efectivamente revisada) |
| **Estado** | `estado` (máquina 5, ocho valores, `DEFAULT 'SIN_CORRECTOR'`), `trabajo_publicacion_id` (FK a `trabajo`, nullable) |
| **Borrador** | `nota_local` (numeric o texto según `grading_type`), `rubrica_local` (`jsonb`), `comentario` (texto libre del corrector), `comentario_renderizado` (texto con el pie), `escalado_aplicado` (booleano) |
| **Rúbrica** | `huella_rubrica` (`bytea`), `rubrica_revisada_en` (timestamptz nullable) |
| **Autoría y concurrencia** | `corrector_usuario_id`, `version` (entero, arranca en 1), `actualizado_en`, `lista_en` |
| **Publicabilidad** | `publicable` (booleano `NOT NULL DEFAULT true`), `motivo_no_publicable` (enum de diez valores, nullable) |
| **Banderas ortogonales** | `version_desactualizada`, `reclamo_abierto`, `sin_commits`, `reconocimiento_sin_codigo` (+ `reconocimiento_sin_codigo_en`) |
| **Resultado** | `tipo_resultado` (`NOTA \| EXCUSADA`, por defecto `NOTA`), `publicada_en`, `intentos`, `ultimo_error` |
| **Reapertura** | `motivo_reapertura` (texto nullable), `reabierta_en`, `reabierta_por` |
| **Coordinación** | `banderas` (`text[]`, catálogo cerrado de cinco valores) |

**`correccion` no tiene ninguna columna espejo de Canvas.** Ni `canvas_score`, ni
`canvas_graded_at`, ni `contraste_canvas`, ni `canvas_verificado_en`: todas fueron retiradas porque
`correccion` es por sujeto y Canvas responde por estudiante (RG-031, RG-187, A-206).

### 12.2.4 `publicacion_nota` — la evidencia de qué se escribió

*Append-only*, con unicidad `(correccion_id, estudiante_id, intento)`. **Una fila por estudiante y
por intento**, también en tareas grupales.

| Columna | Qué guarda |
|---|---|
| `correccion_id`, `estudiante_id`, `intento` | Clave. `intento` crece; nunca se reutiliza |
| `payload_enviado` (`jsonb`) | La petición exacta: `posted_grade`, `late_policy_status`, `text_comment` renderizado, `group_comment`, `rubric_assessment` completo, y el `canvas_score` que había antes |
| `codigo_http`, `respuesta` (`jsonb`) | El código y el **cuerpo literal** que devolvió Canvas |
| `score_devuelto`, `entered_score_devuelto`, `grade_devuelto` | Lo que Canvas guardó, leído en la verificación |
| `grader_id_reportado`, `assessor_id_reportado` | La atribución que Canvas reporta |
| `late_policy_status_enviado` | Siempre `none`, salvo la acción explícita de «marcar como no entregada» |
| `publicado_por_usuario_id`, `credencial_canvas_id` | Quién pulsó y con qué credencial se escribió |
| `intentada_en` | Instante de la escritura |

`posted_at_devuelto` **no existe**: la visibilidad de la nota para el estudiante se lee de
`estado_canvas_submission.posted_at` (RG-101).

### 12.2.5 `estado_canvas_submission` — el espejo de Canvas, por estudiante

```
estado_canvas_submission (
  entrega_id, estudiante_id, workflow_state, score, entered_score, graded_at, grader_id,
  excused, late, seconds_late, points_deducted, submitted_at, posted_at, gradeable,
  origen text NOT NULL DEFAULT 'CANVAS', sincronizado_en timestamptz NOT NULL,
  PRIMARY KEY (entrega_id, estudiante_id)
)
```

Es la **única** fuente de «qué tiene Canvas». La escribe el trabajo `reconciliar_notas_canvas` desde
el endpoint masivo, leído **una vez por entrega**. `submission_summary` **no se usa en ninguna
pantalla ni en ningún trabajo** (A-142, A-206, RG-101).

### 12.2.6 `nota_interna_correccion` — el canal interno del equipo docente

*Append-only*: una nota no se edita ni se borra; se añade otra.

| Columna | Regla |
|---|---|
| `id`, `correccion_id`, `autor_membresia_id`, `texto`, `creada_en` | Base de la tabla |
| `clase` | `NOTA \| RECLAMO_ABIERTO \| RECLAMO_CERRADO`, por defecto `NOTA` **[DECISION NUEVA]** |
| `desenlace_reclamo` | `SIN_CAMBIO \| NOTA_CORREGIDA \| ERROR_DE_LA_APLICACION`, obligatorio si y sólo si `clase = 'RECLAMO_CERRADO'` **[DECISION NUEVA]** |

**[DECISION NUEVA]** — El reclamo sobre una entrega se registra como una fila de esta tabla y **no
abre ninguna incidencia**. El catálogo de tipos de incidencia es cerrado en 51 valores (A-207,
RG-190) y `RECLAMO_ENTREGA` no está en él; el censo de entidades es cerrado en 70 (RG-192), así que
tampoco cabe una tabla nueva. Una columna `clase` sobre una tabla que ya existe y ya es *append-only*
da la misma trazabilidad —autor, fecha, texto, desenlace— sin abrir ningún catálogo cerrado.

### 12.2.7 Columnas que este capítulo usa de otras entidades

| Entidad | Columna | Para qué |
|---|---|---|
| `membresia_curso` | `peso_correccion` (smallint, `CHECK 0–10`) | Capacidad del corrector en el reparto equitativo. Por defecto **1** para ayudante y **0** para profesor |
| `membresia_curso` | `correccion_vista_en` (timestamptz nullable) | Calcula el aviso «se te asignaron N entregas nuevas» |
| `entrega` | `tiene_rubrica`, `canvas_rubric_id`, `rubric_association_id`, `rubrica_points_possible`, `use_rubric_for_grading`, `free_form_criterion_comments`, `hide_points`, `hide_score_total` | Rúbrica y sus ajustes |
| `entrega` | `grading_type`, `grading_standard_id`, `puntos_posibles` | Unidad y validación de la nota |
| `entrega` | `submission_types`, `post_manually`, `grade_group_students_individually`, `publicada`, `estado_validacion`, `validaciones`, `advertencias` | Condiciones de la publicación |
| `entrega` | `fecha_objetivo_correccion` (timestamptz nullable) | Plazo de corrección |
| `version_entrega` | `commit_sha`, `estado`, `tag_estado`, `tag_nombre`, `motivo`, `advertencias`, `verificacion`, `integrantes` (`jsonb`), `vigente`, `intento`, `reemplaza_a_id` | Qué se corrige y a quién se califica |
| `acceso_docente_repositorio` | `estado` | Si se pinta el enlace al código |
| `repositorio` | `estado`, `full_name` | Si el enlace abrirá o dará `404` |

### 12.2.8 Criterios de aceptación — modelo de datos

1. Un `INSERT` de una segunda fila de `asignacion_correccion` con el mismo `(entrega_id, sujeto_id)`
   es rechazado por la base de datos, no por el código.
2. Un `INSERT` de una segunda fila de `correccion` con el mismo `(entrega_id, sujeto_id)` es
   rechazado por la base de datos.
3. La prueba `test_membresia_nula_equivale_a_sin_corrector` recorre todas las filas y falla si
   alguna tiene `membresia_id` nulo con estado distinto de `SIN_CORRECTOR`, o al revés.
4. Un `SELECT` sobre `information_schema.columns` demuestra que `asignacion_correccion` **no** tiene
   columna `estado` y que `correccion` **no** tiene ninguna columna cuyo nombre empiece por `canvas_`
   ni se llame `contraste_canvas` o `canvas_verificado_en`.
5. Un `UPDATE` sobre una fila de `publicacion_nota` es rechazado por la regla *append-only*; un
   segundo intento de publicación con el mismo `(correccion_id, estudiante_id, intento)` viola la
   unicidad.
6. Un `UPDATE` sobre `nota_interna_correccion.texto` es rechazado.
7. La tabla `estado_canvas_submission` existe con clave primaria `(entrega_id, estudiante_id)` y una
   búsqueda de la cadena `submission_summary` en todo el repositorio no devuelve ninguna llamada.

---

## 12.3 Máquina de estados de la corrección y sus banderas

### 12.3.1 Los ocho estados (máquina 5)

`SIN_CORRECTOR` → `ASIGNADA` → `EN_CURSO` → `LISTA_PARA_PUBLICAR` → `PUBLICANDO` →
{ `PUBLICADA` | `PUBLICADA_CON_ADVERTENCIA` | `ERROR_PUBLICACION` }, con `DEFAULT 'SIN_CORRECTOR'`.

| Estado | Etiqueta en pantalla | Significado |
|---|---|---|
| `SIN_CORRECTOR` | «Sin corrector» | La fila existe y nadie la corrige |
| `ASIGNADA` | «Asignada» | Tiene corrector y nadie la ha abierto |
| `EN_CURSO` | «En curso» | El corrector la abrió; puede haber borrador |
| `LISTA_PARA_PUBLICAR` | «Lista para publicar» | El corrector terminó; falta la escritura en Canvas |
| `PUBLICANDO` | «Publicando» | Hay una escritura en vuelo o encolada |
| `PUBLICADA` | «Publicada» | La verificación confirmó la nota para todos los integrantes congelados |
| `PUBLICADA_CON_ADVERTENCIA` | «Publicada con advertencia» | Se escribió, pero lo que Canvas devolvió no coincide del todo |
| `ERROR_PUBLICACION` | «Error al publicar» | Canvas rechazó la escritura |

**Ningún identificador en mayúsculas aparece en pantalla** (A-155).

### 12.3.2 Disparador exacto de cada transición

| Transición | Evento que la dispara |
|---|---|
| → `SIN_CORRECTOR` (alta) | Se materializa la fila `correccion`: al aplicar un reparto sobre sujetos activos, al capturar la versión si no se repartió antes, o al detectar en Canvas una nota para un sujeto sin fila propia (entonces la derivación de contraste da `SOLO_EN_CANVAS`) |
| → `SIN_CORRECTOR` (retroceso) | El retiro del ayudante vacía `membresia_id`. Se abre `CORRECCION_SIN_CORRECTOR`, **una por entrega afectada** |
| → `ASIGNADA` | `membresia_id` recibe un corrector: reparto manual, equitativo, por sección, copia de la entrega anterior, o reasignación |
| → `EN_CURSO` | El corrector **abre por primera vez** la pantalla de esa corrección. Es automático y escribe `asignacion_correccion.iniciada_en`. **No hay botón «empezar»** |
| → `LISTA_PARA_PUBLICAR` | El corrector pulsa «Marcar como lista». Exige nota válida según el `grading_type` y `version_entrega_id` no nulo |
| → `PUBLICANDO` | Alguien con `nota.publicar` confirma la publicación y el pre-chequeo pasa. La intención se persiste **antes** de la llamada y `trabajo_publicacion_id` queda escrito en la misma transacción |
| → `PUBLICADA` | La verificación devuelve, **para todos** los integrantes del conjunto congelado, `score` igual a lo enviado con tolerancia `0,001`, `graded_at` no nulo y posterior o igual a la escritura, `points_deducted = 0` y —si la entrega tiene rúbrica— evaluación de rúbrica presente |
| → `PUBLICADA_CON_ADVERTENCIA` | La verificación devuelve `score ≠ entered_score`, o `points_deducted ≠ 0`, o algún integrante sigue sin nota, sin comentario o sin rúbrica tras el pase de remedio |
| → `ERROR_PUBLICACION` | Canvas devolvió error. El cuerpo literal queda en `publicacion_nota.respuesta`. Sale a `LISTA_PARA_PUBLICAR` al reintentar |
| `PUBLICANDO` → `LISTA_PARA_PUBLICAR` | El trabajo de publicación se **cancela** (por ejemplo con `motivo_cancelacion = 'VERSION_SUPERSEDIDA'`), con el aviso escrito |
| `PUBLICADA` → `EN_CURSO` | Acción explícita **«Reabrir corrección»** con motivo obligatorio |

Toda transición pasa por **una única función** en `backend/app/dominio/correccion.py`, que lleva la
tabla de transiciones legales como dato y escribe `bitacora` en la misma transacción. Una prueba de
arquitectura falla si alguna ruta escribe `correccion.estado` sin pasar por ella.

### 12.3.3 `publicable` y `motivo_no_publicable`: la imposibilidad de publicar no es un estado

`correccion.publicable` es un booleano `NOT NULL DEFAULT true`. Cuando es `false`, la **única**
transición prohibida es `LISTA_PARA_PUBLICAR → PUBLICANDO`. Todo lo demás sigue disponible: la
corrección se reparte, se abre, se trabaja y se marca como lista, **porque la corrección local es
trabajo docente válido aunque la nota no pueda viajar a Canvas**.

| `motivo_no_publicable` | Texto en pantalla | Quién lo reevalúa |
|---|---|---|
| `PERIODO_CERRADO` | «El período de calificación de Canvas cerró el *fecha*» | `reconciliar_notas_canvas` y el pre-chequeo al abrir |
| `NO_GRADEABLE` | «Canvas no acepta calificar a esta persona: su matrícula está inactiva o el curso está concluido» | `reconciliar_notas_canvas` y el pre-chequeo al abrir |
| `NO_GRADED` | «Esta tarea está configurada como *no calificada* en Canvas y no admite notas» | `sync_tareas_y_fechas` |
| `GPA_SCALE` | «Canvas no documenta un formato de nota para este tipo de calificación» | `sync_tareas_y_fechas` |
| `LETTER_GRADE_SIN_ESQUEMA` | «Esta tarea califica por letras y no tiene esquema definido en Canvas» | `sync_tareas_y_fechas` |
| `MODERADA_O_ANONIMA` | «Esta entrega usa calificación moderada o anónima; la publicación de nota está fuera de alcance» | `sync_tareas_y_fechas` |
| `ENTREGA_DESPUBLICADA` | «Esta tarea no está publicada en Canvas» | `sync_tareas_y_fechas`, desde `entrega.publicada` |
| `ENTREGA_ELIMINADA` | «Esta tarea ya no existe en Canvas» | `sync_tareas_y_fechas` |
| `SUJETO_EXCLUIDO` | «Este sujeto está excluido de la tarea» | `materializar_sujetos` y la acción «readmitir» |
| `PUBLICACION_NO_AUTORIZADA` | «Canvas no autoriza esta escritura con la credencial del curso» | El mecanismo único de capacidades degradadas |

**Cuando la causa desaparece, la bandera vuelve a `true` sola, sin tocar el estado**, y el aviso se
retira de la pantalla. El distintivo rojo **«No publicable en Canvas — *motivo*»** aparece junto al
chip de estado, en la matriz de estado y en la pantalla de corrección.

`LETTER_GRADE_SIN_ESQUEMA` es un motivo de la enumeración, pero **no bloquea**: cuando la entrega es
`letter_grade` sin esquema, la aplicación publica el valor numérico con `prefer_points_over_scheme=true`
(§12.10.1) y la bandera permanece en `true`. El motivo queda reservado al caso en que la instancia
rechace también esa vía, comprobado por la relectura.

### 12.3.4 Banderas ortogonales

| Bandera | Tipo | Qué significa | Efecto |
|---|---|---|---|
| `publicable` + `motivo_no_publicable` | booleano + enum | La nota no puede viajar a Canvas | Bloquea sólo `LISTA_PARA_PUBLICAR → PUBLICANDO` |
| `version_desactualizada` | booleano | Se recapturó la versión después de que el corrector empezó | Banda ámbar; bloquea publicar hasta confirmar |
| `reclamo_abierto` | booleano | Hay un reclamo del estudiante registrado por un docente | Distintivo; exige confirmación escrita al republicar |
| `sin_commits` | booleano | La versión vigente quedó en `SIN_COMMITS` | Cubo aparte en la bandeja; habilita el flujo masivo de §12.14.3 |
| `reconocimiento_sin_codigo` (+ `_en`) | booleano + timestamptz | Se publicó sin que nadie hubiera podido abrir el código | Se muestra de forma permanente junto a la nota |

**`contraste_canvas` no es una bandera de `correccion`: es una derivación** (§12.14).

### 12.3.5 Criterios de aceptación — estados

1. El `CHECK` de `correccion.estado` contiene exactamente los ocho valores y se genera desde
   `backend/app/dominio/estados.py`; la prueba `test_check_coincide_con_enum` falla si difieren.
2. No existe el valor `NO_PUBLICABLE` en ninguna columna de estado del sistema.
3. Con `publicable = false`, un `POST .../publicar` responde `409` y el estado no cambia; en la misma
   corrección, `PUT .../borrador` y `POST .../lista` responden `200`.
4. Abrir por primera vez la pantalla de una corrección `ASIGNADA` la deja en `EN_CURSO` y escribe
   `iniciada_en`, sin que el usuario pulse ningún botón.
5. La prueba `test_todo_codigo_tiene_etiqueta` falla la construcción si algún estado, motivo o
   bandera de este capítulo carece de etiqueta en español.
6. Recorrer las once transiciones de §12.3.2 deja once filas de `bitacora`, cada una con actor,
   entidad, `antes` y `despues`.
7. Cortar el proceso entre la escritura de la intención y la llamada a Canvas deja la corrección en
   `PUBLICANDO` con `trabajo_publicacion_id` apuntando a una fila de `trabajo` en `PENDIENTE`, nunca
   un hueco.

---

## 12.4 Permisos y visibilidad

### 12.4.1 Qué permiso gobierna cada acción

No se crea ningún permiso nuevo. Las acciones de este capítulo las gobiernan **cuatro** de los nueve
permisos ya definidos. `curso.ver` y `correccion.corregir` son **implícitos e irrevocables** para
todo miembro activo, profesor o ayudante; `correccion.asignar` y `nota.publicar` son **configurables
y concedibles** a un ayudante, y vienen **desactivados por defecto**.

| Acción | Permiso | Profesor | Ayudante |
|---|---|---|---|
| Ver el estado de corrección de toda la tarea: **matriz nominal completa**, agregados, doble contador, filtros y exportación a CSV | `curso.ver` | Sí | **Sí** |
| Ver la rúbrica de la entrega en la aplicación | `curso.ver` | Sí | Sí |
| Ver el enlace al código de **cualquier** repositorio del curso y el enlace de comparación | `curso.ver` | Sí | Sí |
| Ver la nota y el comentario **ya publicados** de cualquier sujeto, y el historial de publicaciones | `curso.ver` | Sí | Sí |
| Registrar un reclamo sobre una corrección | `curso.ver` | Sí | Sí |
| Abrir la corrección **en modo edición** y guardar borrador | `correccion.corregir` **acotado por propiedad** | Sí (todas) | **Sólo las asignadas a él** |
| Ver el **borrador** ajeno (nota local, rúbrica local, comentario sin publicar) | `correccion.corregir` + propiedad | Sí | **No** |
| Ver el **texto** de notas internas ajenas | `correccion.corregir` + propiedad | Sí | **No** |
| Ver las **banderas** de cualquier corrección | `curso.ver` | Sí | **Sí** (son etiquetas de estado, no contenido sensible) |
| Repartir, reasignar y realinear | `correccion.asignar` | Sí | No por defecto; concedible |
| Publicar, dispensar, marcar como no entregada, reabrir y adoptar la nota de Canvas | `nota.publicar` | Sí | No por defecto; concedible |
| Cerrar un reclamo con desenlace `NOTA_CORREGIDA` | `nota.publicar` | Sí | No por defecto; concedible |
| Fijar la fecha objetivo de corrección de una entrega | `tarea.administrar` | Sí | No por defecto; concedible |
| Recapturar una versión con otra fecha de corte o fijarla en un SHA concreto | `tarea.administrar` **más rol `PROFESOR`** | Sí | **No, aunque tenga el permiso** |

### 12.4.2 La cláusula de propiedad acota el trabajo, no la lectura

`correccion.corregir` filtra por `asignacion_correccion.membresia_id`, y ese filtro se aplica
**únicamente** a las rutas de escritura de corrección y a la lectura de `correccion.nota_local`,
`correccion.rubrica_local`, `correccion.comentario` sin publicar y el **texto** de
`nota_interna_correccion`. **No acota el estado que se puede leer**: la pestaña «Estado de la
entrega» es siempre visible para todo miembro activo y muestra la matriz nominal completa (RG-125).

Sobre una fila ajena, el botón principal es **«ver»**, no «corregir».

### 12.4.3 No existe el ayudante «sin permiso de corrección»

`correccion.corregir` es implícito y no revocable. Lo que existe es:

| Situación | Qué ve |
|---|---|
| Ayudante **sin asignaciones** | Bandeja vacía: «no tienes entregas asignadas para corregir en este curso», con enlace al estado general de la tarea |
| Ayudante **sin `nota.publicar`** | En lugar de «Publicar en Canvas», el botón **«Marcar como lista para publicar»**, y el texto «en este curso publica las notas el profesor» |
| Ayudante **retirado** | Pierde el acceso al curso de inmediato —las sesiones abiertas se invalidan— y pierde la lectura de los repositorios en GitHub en el mismo acto |

### 12.4.4 El equipo docente lee todo el código del curso, y se declara

No se crea un permiso «ver el código», y la razón es dura: la lectura `pull` sobre todos los
repositorios del curso la concede **GitHub** al equipo `docentes`, no la aplicación. Un permiso que
ocultara el enlace sería una cortina, porque el ayudante abriría la URL de GitHub igual. **Ocultar no
es autorizar.** Por eso se declara por escrito, con consentimiento fechado, en el formulario de
invitación, en la pantalla de aceptación de la invitación y en la memoria de entrega. La concesión es
**`pull` y sólo `pull`**: un corrector nunca puede empujar sobre el repositorio que corrige ni borrar
una etiqueta de entrega.

### 12.4.5 Con qué identidad escribe la aplicación en Canvas

**Toda escritura en Canvas se ejecuta con la credencial operativa del curso**, que es el token
personal de un profesor. En consecuencia, `grader_id` en Canvas será el del titular del token, sea
quien sea el ayudante que corrigió. **`as_user_id` no se envía jamás**, y una prueba de arquitectura
falla la construcción si el parámetro aparece en cualquier llamada del cliente de Canvas.

La pérdida de trazabilidad dentro de Canvas se compensa en tres lugares, y las tres son obligatorias:

1. La aplicación guarda **quién corrigió** (`correccion.corrector_usuario_id`), **quién pulsó**
   (`publicacion_nota.publicado_por_usuario_id`) y **con qué credencial se escribió**
   (`publicacion_nota.credencial_canvas_id`).
2. **Añade al comentario de la entrega una línea final** con el nombre y el rol del corrector real,
   de modo que la información existe **también dentro de Canvas**.
3. **La pantalla lo dice antes de publicar**: «Se registrará en Canvas a nombre de *{titular de la
   credencial}*».

Un ayudante **no necesita cuenta de Canvas, ni matrícula de TA, ni token propio** para corregir ni
para publicar. La pantalla Equipo lo dice por escrito al invitar.

### 12.4.6 Criterios de aceptación — permisos

1. Una sesión de ayudante sin `correccion.asignar` abre la pestaña «Estado de la entrega» y ve la
   matriz nominal completa, los tres agregados y el doble contador; la pestaña «Repartir» no aparece.
2. Esa misma sesión, sobre una fila ajena, ve el botón «ver»; un `PUT .../borrador` sobre esa
   corrección responde `403`, y la respuesta de `GET .../{entrega}/{sujeto}` no incluye `nota_local`,
   `rubrica_local`, `comentario` ni el texto de las notas internas, pero **sí** incluye las banderas.
3. Una sesión de ayudante sin `nota.publicar` ve el botón «Publicar en Canvas» ausente y en su lugar
   «Marcar como lista para publicar»; un `POST .../publicar` directo responde `403` con código
   `PERMISO_INSUFICIENTE`.
4. Un ayudante con `tarea.administrar` que llama a `POST .../version` con otra fecha de corte recibe
   `403`; el mismo llamado desde una sesión de profesor con el mismo permiso responde `202`.
5. Retirar el permiso `correccion.asignar` a un ayudante con la sesión abierta hace que la siguiente
   petición a una ruta de reparto responda `403`, sin que la persona tenga que volver a entrar.
6. La puerta de integración continua del contrato de autorización falla si alguna ruta bajo
   `/api/cursos/{curso_id}/**` de este capítulo se registra sin dependencia de permiso.
7. Una búsqueda de `as_user_id` en el cliente de Canvas no devuelve ninguna aparición y la prueba de
   arquitectura correspondiente está en verde.

---

## 12.5 Asignación de entregas entre correctores (R2.7.1)

### 12.5.1 Quién asigna y quién es elegible como corrector

Asignar y reasignar exige `correccion.asignar` (§12.4.1): implícito para el profesor, concedible al
ayudante y desactivado por defecto (A-021, Q-2.7-09). **No existe auto-asignación**: un ayudante sin
el permiso no puede tomar del conjunto sin corrector una fila para sí mismo, porque eso rompería
`asignada_por` como decisión de coordinación y produciría carreras entre dos ayudantes tomando la
misma fila (Q-2.7-09). Lo único que ofrece la bandeja a quien no tiene el permiso es el contador
«N sin corrector» y el botón **«avisar a los profesores»**, que encola un mensaje interno por el
*outbox* de comunicación del equipo docente —nunca a Canvas ni al estudiante—.

**Es elegible como corrector cualquier miembro activo del curso, profesor o ayudante**, porque
`correccion.corregir` es implícito e irrevocable para los dos roles (A-021, §12.4.1) y **R2.1.7**
obliga a que un segundo profesor tenga exactamente los mismos permisos que el primero (Q-2.7-08). La
capacidad del corrector en el reparto automático la fija `membresia_curso.peso_correccion` (ya
declarada en §12.2.7): entero `0`–`10`, con **`1` por defecto para ayudante y `0` para profesor**.
`peso = 0` excluye del reparto automático sin excluir de la asignación manual: es el caso del
profesor que no corrige por defecto y del ayudante jefe que coordina sin corregir (Q-2.7-07,
Q-2.7-08). La lista de candidatos excluye siempre las membresías `RETIRADA` y marca en ámbar a quien
no tenga cuenta de GitHub vinculada, con el aviso «no podrá abrir el código hasta vincular su
cuenta» —la vinculación en sí es de otro capítulo (§12.1.1); aquí sólo se lee su efecto—.

### 12.5.2 Conjunto de sujetos que entran en el reparto

Se puede asignar **desde que la entrega está vinculada**, sin esperar al cierre ni a la captura de
`version_entrega`: la asignación nace `ASIGNADA` sin exigir versión (§12.3.2), y mientras no exista
versión vigente la pantalla de corrección muestra la cuenta atrás al cierre en vez del enlace al
código (§12.8.5). Quién aparece en el reparto, sin excepciones (Q-2.7-10):

| Situación del sujeto | ¿Entra en el reparto? | Marca |
|---|---|---|
| Activo, con `fecha_efectiva` vigente y repositorio `OPERATIVO` o `DEGRADADO` | Sí | — |
| Activo, con `fecha_efectiva` vigente y repositorio sin llegar a operativo todavía | Sí, se puede asignar | «sin repositorio todavía», con el motivo y enlace a Pendientes |
| Activo, sin visibilidad para esa entrega o sin ninguna fecha aplicable | No | Bloque plegado «no aplica a esta entrega (N)» |
| Desactivado, sin versión capturada | No | Bloque «sujetos retirados», con su motivo |
| Desactivado, con versión capturada o corrección iniciada | Sí | «fuera de alcance, con versión registrada»; se corrige y se publica si Canvas lo permite |

Sobre ese conjunto, cuatro marcas derivadas —nunca calculadas en vivo (Ley 1)— avisan sin excluir:
`YA_CALIFICADA_EN_CANVAS`, `EXCUSADA`, `NO_CALIFICABLE` y `SIN_VERSION`, obtenidas de
`estado_canvas_submission` (§12.2.5) y de `gradeable_students` (§12.11.2). Sólo `NO_CALIFICABLE`
altera el reparto automático: el equitativo la salta por defecto, con una casilla para incluirla
(Q-2.7-11). Ninguna marca quita a un sujeto de la vista que **R2.7.7** obliga a mostrar completa.

Un sujeto que llega tarde —el trabajo `materializar_sujetos` lo crea sin que nadie pulse nada— entra
en el mismo ciclo con `asignacion_correccion.membresia_id` nulo si la entrega ya tenía reparto
aplicado, y se abre la incidencia **`CORRECCION_SIN_CORRECTOR`** (una por entrega afectada, no una
por fila) con severidad `ADVERTENCIA`. **Nunca se asigna automáticamente** (A-036, A-147): el botón
**«repartir sólo los nuevos»** ejecuta el equitativo únicamente sobre las filas `SIN_CORRECTOR`, con
los contadores ya poblados por lo vigente, sin tocar ninguna fila existente (Q-2.7-10).

### 12.5.3 Las cuatro mecánicas de reparto

Se implementan cuatro, obligatorias para la entrega final (A-134, Q-2.7-06):

1. **Manual**: selector de corrector por fila, y selección múltiple + «asignar a…» para bloques.
2. **Equitativo automático**: balancea el número de pares `(entrega, sujeto)`, normalizado por
   `peso_correccion` — **no** balancea estudiantes, porque un grupo se corrige, se publica y cuenta
   una sola vez (A-081, A-139, Q-2.7-07). Algoritmo determinista: se ordena por
   `nombre_ordenable` (grupos por `grupo.nombre`) y cada sujeto va al corrector con menor
   `asignados / peso`; empates por `peso` descendente y luego por nombre del corrector. La misma
   entrada produce siempre el mismo reparto.
3. **Por sección**: un corrector por `seccion`; cada sujeto va al corrector de la sección de su
   matrícula activa, y en tareas grupales, a la sección del integrante `accepted` de menor
   `canvas_user_id` (regla determinista, escrita en pantalla). Un sujeto con dos secciones activas
   queda **sin asignar y marcado** —«requiere decisión»—, con las dos opciones a la vista.
4. **Reasignación en bloque**: seleccionar filas y reasignarlas a otro corrector o vaciarlas a
   `SIN_CORRECTOR`.

Existe además la comodidad **«copiar el reparto de la entrega anterior»** (`criterio =
COPIA_ENTREGA_ANTERIOR`, ya declarado en §12.2.2), que precarga el corrector que tuvo cada sujeto en
la entrega anterior según A-173 —definición que este capítulo usa sin reabrir (§9)—; los sujetos sin
entrega anterior quedan sin proponer.

**Mecánica común, sin excepciones: previsualizar, confirmar, aplicar en una transacción.** Ningún
modo escribe al pulsar; todos producen una propuesta con el reparto resultante por corrector, el
detalle fila a fila y qué se pisa. Sólo «aplicar» escribe, con una entrada por fila en `bitacora`
(A-029). **Las asignaciones existentes no se pisan por defecto**: equitativo y por sección reparten
sólo lo que está en `SIN_CORRECTOR`, salvo que se marque explícitamente «reasignar también las que ya
empezaron» — y entonces el corrector anterior recibe el aviso de novedades de §12.6.5 y su trabajo se
conserva (Q-2.7-06, Q-2.7-66). El reparto de una entrega es independiente del de las demás entregas
de la misma tarea (§2.7 del enunciado, A-134): no hay herencia automática, sólo la comodidad descrita.

### 12.5.4 Desalineación tras el reparto

Cada fila guarda con qué regla se creó (`criterio`, `criterio_seccion_id`, ya declarados en §12.2.2).
Tras cada sincronización de roster o de grupos, el mismo ciclo de `materializar_sujetos` recalcula la
premisa: si una fila `SECCION` cambió de sección, o un integrante cambió de grupo, se escribe
`desalineada_motivo ∈ {CAMBIO_DE_SECCION, CAMBIO_DE_GRUPO}` con `desalineada_en` (Q-2.7-14). **La
asignación no se mueve sola.** La fila conserva corrector, borrador y estado; aparece con un
distintivo ámbar y el contador «N asignaciones desalineadas» junto al botón **«realinear»**, que
recalcula sólo esas filas con el criterio original y previsualiza antes de aplicar. Las filas
`MANUAL` nunca se marcan: no había premisa automática que romper. En tarea grupal, el sujeto no
cambia de identidad al cambiar la composición del grupo (A-081); lo que varía es a quién se califica,
gobernado por el conjunto congelado al corte (§12.2.7, A-139), no por el reparto.

### 12.5.5 Reasignación y retiro de un ayudante

La reasignación es libre mientras la corrección no esté `PUBLICANDO`; el borrador es propiedad del
par `(entrega, sujeto)`, no del corrector, y **nunca se descarta** (Ley 2, A-030):

| Estado de la corrección | ¿Reasignable? | Qué pasa con el borrador |
|---|---|---|
| `SIN_CORRECTOR`, `ASIGNADA` | Sí | No hay borrador |
| `EN_CURSO`, `LISTA_PARA_PUBLICAR` | Sí | Se conserva íntegro; el nuevo corrector ve la banda «borrador iniciado por *nombre* el *fecha*» |
| `PUBLICANDO` | No | Botón «publicación en curso» |
| `PUBLICADA`, `PUBLICADA_CON_ADVERTENCIA`, `ERROR_PUBLICACION` | Sí | Se conserva; una nueva publicación crea `publicacion_nota` con `intento` siguiente |

Toda reasignación queda en `bitacora` con actor, `antes` y `despues`; la cadena se muestra en la
pantalla de corrección y en la de estado. `correccion.corrector_usuario_id` guarda quién escribió
realmente el último borrador —no quien lo asignó—, que es el dato que §12.4.5 usa para la línea de
atribución del comentario en Canvas (Q-2.7-12).

**Al retirar a un ayudante** (A-025), sus asignaciones cuya corrección no esté `PUBLICADA`,
`PUBLICADA_CON_ADVERTENCIA` ni `PUBLICANDO` pasan a `SIN_CORRECTOR` en la misma transacción del
retiro —es la transición de «retroceso» ya fijada en §12.3.2—, conservando `asignada_por`,
`asignada_en` y el borrador; se abre `CORRECCION_SIN_CORRECTOR` por entrega afectada, con el enlace
directo a «repartir sólo los nuevos» (Q-2.7-13). Las correcciones ya publicadas **no se tocan**: la
autoría real y la línea de atribución en Canvas siguen nombrando a quien las hizo (A-025 punto 5). El
diálogo de retiro —que vive en la pantalla de Equipo, fuera de este capítulo— puede ofrecer repartir
de inmediato lo liberado con el mismo equitativo de §12.5.3; la acción en sí, y la revocación del
acceso de lectura en GitHub, se ejecutan por los mecanismos ya fijados en A-025 y A-163.

### 12.5.6 Concurrencia del reparto

Un reparto automático se ejecuta entero dentro de una transacción que toma
`pg_advisory_xact_lock` sobre `(hash('reparto'), entrega_id)`: dos ejecuciones simultáneas no se
pisan, la segunda ve el resultado de la primera y termina informando que no quedaban entregas sin
asignar —el reparto es idempotente, no acumulativo—. La última defensa es estructural: la unicidad
`(entrega_id, sujeto_id)` de `asignacion_correccion` (§12.2.2) hace irrepresentable un doble
corrector, comprobado por la base de datos y no por el código (Q-2.7-66).

### Criterios de aceptación de 12.5

1. **CA-12.5-01.** Un sujeto sin repositorio operativo aparece en la propuesta de reparto con la
   marca «sin repositorio todavía» y se puede asignar igual.
2. **CA-12.5-02.** Ejecutar el equitativo dos veces sobre la misma entrega sin cambios intermedios
   produce el mismo reparto byte a byte.
3. **CA-12.5-03.** `materializar_sujetos` que crea un sujeto tardío sobre una entrega con reparto ya
   aplicado deja esa fila en `SIN_CORRECTOR` y abre (o incrementa) la incidencia
   `CORRECCION_SIN_CORRECTOR` de esa entrega, sin tocar ninguna otra fila.
4. **CA-12.5-04.** Cambiar la sección de un estudiante cuya asignación se creó con `criterio =
   SECCION` marca la fila `desalineada_motivo = CAMBIO_DE_SECCION` sin cambiar su corrector, y el
   botón «realinear» la corrige tras previsualización.
5. **CA-12.5-05.** Retirar a un ayudante con correcciones en `EN_CURSO` las deja en `SIN_CORRECTOR`
   con el borrador intacto; las que estaban `PUBLICADA` conservan `corrector_usuario_id` sin cambio.
6. **CA-12.5-06.** Dos peticiones de reparto equitativo simultáneas sobre la misma entrega, lanzadas
   en paralelo en una prueba de concurrencia, nunca producen dos correctores para el mismo sujeto.
7. **CA-12.5-07.** Una sesión de ayudante sin `correccion.asignar` que llama a la ruta de reparto
   recibe `403`; la misma sesión ve el contador «N sin corrector» y el botón «avisar a los
   profesores» cuando existen filas sin corrector.

---

## 12.6 Bandeja del corrector: identificación de las entregas asignadas (R2.7.2)

### 12.6.1 «Mis asignaciones» como vista por defecto

`/cursos/{id}/correccion` tiene tres pestañas: **«Mis asignaciones»**, por defecto para un ayudante;
**«Estado de la entrega»**, siempre visible y por defecto para un profesor (§12.13); y **«Repartir»**,
sólo con `correccion.asignar` (A-135). La bandeja lee `correccion.corregir` filtrado por propiedad en
el servidor —nunca en el cliente (A-022)— y agrupa por tarea y entrega, con cabecera «Tarea *N* ·
*tipo de entrega* · cierra el *fecha* (*zona*)».

Columnas, en este orden: sujeto (con el número de integrantes si es grupo), sección, estado de la
corrección traducido (§12.3.1), estado de la versión, fecha efectiva de cierre con su origen
(§12.8.4), banderas (§12.17.4), y última modificación del borrador. **Orden por defecto:
`nombre_ordenable` ascendente, desempate por `sujeto.id`** — estable, no cambia al corregir, y es el
mismo orden que gobierna la navegación de §12.7 (A-135). El estado **no** entra en el orden: es
columna y filtro. Filtros: entrega, estado, sección, banderas, y el conmutador «sólo sin corregir»,
reflejados en la URL. Cabecera con el doble contador **«N asignadas · M corregidas · K publicadas»**,
restringido a lo propio de la sesión.

### 12.6.2 Estados vacíos, con causa

Tres variantes, nunca una pantalla en blanco (Q-2.7-16):

| Situación | Texto |
|---|---|
| Sin ninguna asignación en el curso | «no tienes entregas asignadas para corregir en este curso», con enlace al estado general de la tarea |
| Todas las asignadas están terminadas | «has terminado tus *N* entregas asignadas», con el recuento de publicadas |
| Asignadas pero ninguna disponible todavía | «tienes *N* entregas asignadas, pero ninguna está disponible todavía», listando cada una con su fecha efectiva de cierre |

### 12.6.3 Aviso de novedades

`membresia_curso.correccion_vista_en` (ya declarada en §12.2.7) se compara contra
`asignacion_correccion.asignada_en`: cuando hay asignaciones posteriores a la última visita, aparece
la banda **«se te asignaron N entregas nuevas»** en la navegación de Corrección. **El aviso es sólo
en la aplicación**: no se envía correo por asignación ni por reasignación —el reparto de la cuota
diaria de comunicaciones no reserva margen para ello (§11), y un reparto de 200 sujetos generaría
tantos correos como correctores en un solo gesto—. Quien esté suscrito al informe diario ve su propio
avance en la sección de resumen que ese capítulo ya construye (§12.14.3).

### 12.6.4 Señal transversal entre cursos

No se crea una pantalla nueva fuera del árbol de cursos. Cada tarjeta de `/cursos` (Mis cursos) suma
el contador **«N por corregir»**; al pulsarlo entra directamente a la bandeja de ese curso con el
filtro «sólo sin corregir» aplicado. Es la forma en que un ayudante de varios cursos ve, en una sola
pantalla, dónde tiene trabajo pendiente, sin duplicar la verdad que ya vive en `asignacion_correccion`.

### Criterios de aceptación de 12.6

1. **CA-12.6-01.** Un ayudante que entra por primera vez a `/cursos/{id}/correccion` ve «Mis
   asignaciones» activa, sin tener que seleccionar nada.
2. **CA-12.6-02.** La lista de un ayudante con 40 asignaciones en el curso y 12 en la entrega
   filtrada muestra exactamente esas 12, ordenadas por `nombre_ordenable`, idéntico entre dos
   sesiones distintas del mismo usuario.
3. **CA-12.6-03.** Un ayudante sin ninguna asignación ve el primer estado vacío; uno con todo
   publicado ve el segundo; uno con asignaciones cuya fecha aún no venció ve el tercero, con la lista
   de fechas.
4. **CA-12.6-04.** Asignar tres entregas nuevas a un ayudante hace que, en su siguiente visita a
   Corrección, aparezca «se te asignaron 3 entregas nuevas»; ningún correo se encola por ese evento.
5. **CA-12.6-05.** La tarjeta de un curso en `/cursos` muestra el número exacto de asignaciones
   pendientes del usuario en sesión, y pulsarla abre la bandeja con «sólo sin corregir» activo.

---

## 12.7 Navegación entre entregas asignadas (R2.7.3)

### 12.7.1 Orden, posición y filtros

El recorrido usa el mismo orden estable de §12.6.1 y se fija **al abrir la bandeja**: si el conjunto
cambia mientras el corrector navega —por ejemplo, un sujeto tardío que entra en el reparto—, no se
reordena en silencio (A-036, A-147); aparece un aviso discreto «la lista cambió: *N* entregas» con el
botón «actualizar recorrido». La barra de posición muestra siempre **«N de M»**, y **«N de M
(filtrado)»** cuando hay un filtro activo. «Siguiente» y «anterior» avanzan **dentro del conjunto tal
como está filtrado en pantalla**: un corrector que filtró por sección no sale de esa sección al
navegar (A-135, Q-2.7-17).

### 12.7.2 «Siguiente sin corregir»

Botón aparte del «siguiente» simple. Salta al próximo elemento en `ASIGNADA` o `EN_CURSO` dentro del
mismo filtro; al llegar al final da una vuelta completa una sola vez y, si no queda ninguno, muestra
«no queda ninguna sin corregir en esta entrega» en lugar de repetir el ciclo.

### 12.7.3 Atajos de teclado

Obligatorios, visibles con `?` y listados en el pie de la pantalla de corrección (A-135, A-002):
`J`/`→` siguiente · `K`/`←` anterior · `N` siguiente sin corregir · `S` guardar ahora · `L` marcar
como lista · `P` abrir el diálogo de publicar · `Esc` cerrar diálogo. **`P` abre el diálogo, nunca
publica**: ninguna tecla produce por sí sola una escritura en Canvas. Los atajos se desactivan con el
foco en un campo de texto.

### 12.7.4 Límite del recorrido: una entrega, nunca más

La navegación **no cruza tareas ni entregas**: cambiar de entrega cambia la rúbrica, la versión, la
fecha efectiva y el criterio de corrección, y encadenarlas induciría a corregir una entrega con la
rúbrica de otra. Al terminar el recorrido, una tarjeta de cierre dice «has recorrido las *N* entregas
asignadas de *Tarea · Entrega*» y enlaza a las demás entregas con asignaciones pendientes, con su
recuento. Cada elemento tiene URL propia (`/cursos/{id}/correccion/{entrega_id}/{sujeto_id}`),
compartible y compatible con el botón «atrás» del navegador.

### Criterios de aceptación de 12.7

1. **CA-12.7-01.** Con un filtro de sección activo, pulsar «siguiente» repetidamente nunca produce
   un sujeto de otra sección.
2. **CA-12.7-02.** «Siguiente sin corregir» sobre una entrega con una sola fila pendiente la
   encuentra sin importar la posición actual, y una segunda pulsación muestra el mensaje de
   agotamiento en vez de repetir la vuelta.
3. **CA-12.7-03.** Pulsar `P` abre el diálogo de publicación y no ejecuta ningún `PUT` contra Canvas
   hasta que el diálogo se confirma explícitamente.
4. **CA-12.7-04.** No existe ninguna ruta de navegación (siguiente, anterior, siguiente sin corregir)
   que cruce el `entrega_id` del recorrido activo.
5. **CA-12.7-05.** Abrir la URL de un elemento del recorrido directamente, sin pasar por la bandeja,
   carga la pantalla de corrección con la barra de posición correcta respecto del recorrido completo
   de esa entrega.

---

## 12.8 Acceso a la versión del repositorio en la pantalla de corrección (R2.7.4)

Este capítulo **no define** cómo se arma la URL del `commit_sha`, cómo se calcula la entrega anterior
para la comparación, ni cómo se audita la apertura: ese mecanismo es **§9.9 "Acceso directo a la
versión para profesores y ayudantes"** (`docs/SPEC/09-entregas-fechas-y-versiones.md`), construido
íntegro sobre `version_entrega` y sus columnas ya citadas en §12.2.7. Lo que fija esta sección es
**dónde y cómo aparece ese mecanismo ensamblado dentro de la pantalla de corrección**.

### 12.8.1 Columna izquierda de la pantalla de corrección

La pantalla `/cursos/{id}/correccion/{entrega_id}/{sujeto_id}` reparte el trabajo en dos columnas,
sin pestañas —el corrector necesita ver el código y evaluar a la vez— con una cabecera fija de
contexto (sujeto, sección, tarea, entrega, fecha efectiva con zona y origen, estado de la corrección,
corrector asignado, barra de navegación de §12.7). La **columna izquierda (~40%)** ensambla:

1. **El panel de acceso de §9.9.2**: enlace `tree/{sha}` destacado con copiado, enlace al tag si
   existe, y enlace de comparación `compare/{sha_anterior}...{sha_actual}` con la entrega anterior
   según A-173 (§9.9.3). Se pinta sólo si `acceso_docente_repositorio = CONCEDIDO`; con `PENDIENTE` o
   `ERROR` se muestra el motivo y el reintento, nunca un enlace que dará `404` (A-136, §9.9.2).
2. **El botón «descargar esta versión» de §9.9.4**, enlace al `.zip` por SHA que la aplicación ni
   sirve ni almacena.
3. Los tres enlaces de este panel —árbol, comparación, descarga— pasan por el **endpoint auditado**
   de §9.9.4: la apertura queda en `bitacora` con actor, versión y momento, sin coste de llamadas
   externas.
4. **[DECISIÓN DE ESTE CAPÍTULO]** Bloque de comandos de git listos para copiar, porque el corrector
   normalmente necesita ejecutar el código, no sólo mirarlo:

   ```
   git clone https://github.com/{org}/{repo}.git
   cd {repo}
   git checkout {sha}
   ```

   con la variante por tag cuando existe, y la línea fija «tu acceso es de sólo lectura; no podrás
   empujar cambios» (A-163). No amplía el mecanismo de §9.9: se construye desde los mismos campos
   persistidos y no cuesta ninguna llamada adicional.
5. **Metadatos de la versión**, en tres bloques: **qué versión es** (SHA corto con el completo al
   pasar el cursor, nombre del tag o el motivo de su ausencia, `intento`/versión con enlace a la
   anterior si superseció otra, estado traducido; en `REVISAR`, los dos SHA candidatos con su fuente
   según `version_entrega.verificacion`, §9.10.2); **por qué es esa versión** (fecha efectiva con
   origen y regla de corte escrita literalmente: «último commit cuya fecha de committer es anterior o
   igual a la fecha efectiva de cierre, en UTC», A-102; fecha y autor del commit capturado, con su
   regla de atribución); y **cuánto trabajo hay detrás** (commits contables de la ventana de esa
   entrega, autores distintos, y «N commits posteriores al cierre» en ámbar con el texto «hay
   actividad posterior al cierre; la versión registrada no cambia» cuando N > 0, enlazando el
   `compare` entre el SHA capturado y el head actual — A-085, **R2.4.7**).
6. **Historial de entregas anteriores del mismo sujeto**: una fila por entrega de menor `orden` con
   `fecha_efectiva` vigente para ese sujeto (A-173), con su SHA, su nota y comentario publicados, su
   corrector real y su fecha de publicación; si no hay entrega anterior, enlaza al timeline del
   repositorio (**R2.5.10**). El enlace de comparación de cada fila usa la misma guarda de acceso
   docente. La nota de la entrega actual **nunca se precarga** con la anterior.

### 12.8.2 Advertencias de contenido

Si la versión trae `USA_GIT_LFS`, `TIENE_SUBMODULOS` o `ARBOL_TRUNCADO` (§9.10.5, A-101), aparecen en
la cabecera de la pantalla, para que el corrector sepa por qué puede faltar contenido antes de
penalizar por ello.

### 12.8.3 Estados borde de esta pantalla, todos con texto propio

| Situación | Qué muestra |
|---|---|
| Sin versión capturada todavía | «la versión se registrará al cierre: *fecha* (*zona*)», con cuenta atrás; «Marcar como lista» deshabilitado |
| Versión `SIN_COMMITS` (§9, A-101) | «no hay commits anteriores al cierre, más allá del inicial»; no es un error, la etiqueta no es roja |
| Versión `REVISAR` | «versión registrada, requiere revisión», con los dos SHA candidatos y el enlace a la incidencia |
| Versión sin etiqueta en GitHub | «versión registrada (sin etiqueta en GitHub)»; el enlace por SHA funciona igual |
| Versión recapturada | Banda «esta versión se recapturó el *fecha*; motivo: *motivo*», con enlace a la anterior |
| Repositorio `INACCESIBLE` (A-230) | «versión registrada; el repositorio ya no está accesible en GitHub desde *fecha*, por *motivo*»; **no bloquea la corrección ni la publicación** |
| `acceso_docente_repositorio` `PENDIENTE`/`ERROR` | El motivo y «reintentar ahora» |
| Corrector sin cuenta de GitHub vinculada | «vincula tu cuenta de GitHub para abrir el código», con enlace a `/perfil` |

### 12.8.4 La fecha efectiva, siempre con zona y origen

Todo instante de esta pantalla sigue A-152: `dd-MM-yyyy HH:mm (America/Santiago)`, nunca una hora
desnuda. El origen de `fecha_efectiva` se traduce siempre: `BASE` → «fecha general de la entrega»,
`SECCION` → «fecha de la sección *N*», `GRUPO` → «fecha del grupo *nombre*», `ADHOC` → «extensión
individual»; con `ambigua = true`, se añade en ámbar «este sujeto tiene dos fechas aplicables; se usa
la más tardía», con enlace a la incidencia. La conversión de UTC a la zona del curso se hace en una
única función del frontend, sin excepciones.

### 12.8.5 Reconocimiento cuando nadie pudo abrir el código

Cuando el repositorio se vuelve `INACCESIBLE` antes de que la corrección llegara a `EN_CURSO`, el
diálogo de publicación exige marcar **«califico sin haber podido abrir el código de esta versión»**
(A-230); queda `correccion.reconocimiento_sin_codigo = true` con su timestamptz, y el distintivo se
muestra de forma permanente junto a la nota. Si la corrección ya estaba `EN_CURSO` o más avanzada, no
se pide nada.

### Criterios de aceptación de 12.8

1. **CA-12.8-01.** Con `acceso_docente_repositorio = CONCEDIDO`, la columna izquierda pinta el enlace
   `tree/{sha}`, el bloque de comandos de git con el SHA exacto de `version_entrega`, y el enlace de
   comparación cuando existe entrega anterior para ese sujeto.
2. **CA-12.8-02.** Con `acceso_docente_repositorio = PENDIENTE`, ningún enlace a GitHub se pinta en
   la pantalla; se muestra el motivo y la hora del próximo intento.
3. **CA-12.8-03.** Un repositorio `INACCESIBLE` (A-230) no bloquea «Marcar como lista» ni «Publicar
   en Canvas»; muestra el texto de versión registrada en lugar del enlace.
4. **CA-12.8-04.** Abrir el enlace del árbol desde esta pantalla deja una fila en `bitacora` con la
   acción de apertura, el actor y la versión, vía el endpoint auditado de §9.9.4.
5. **CA-12.8-05.** Una corrección que no llegó a `EN_CURSO` antes de que su repositorio pasara a
   `INACCESIBLE` no permite publicar sin marcar el reconocimiento; una que ya estaba `EN_CURSO`
   publica sin ese paso.
6. **CA-12.8-06.** El contador «N commits posteriores al cierre» de una versión con actividad después
   del corte es mayor que cero y el `compare` que ofrece usa el SHA capturado, no el `HEAD` actual,
   como extremo izquierdo.
7. **CA-12.8-07.** Ninguna consulta de esta pantalla contiene una llamada HTTP a GitHub fuera del
   endpoint auditado de apertura de §9.9.4; una prueba con un doble que lanza excepción en
   `ClienteGitHub` pasa para el resto del render.

---

## 12.9 Rúbrica de Canvas en la pantalla de corrección (R2.7.5)

Este capítulo **no define** el mecanismo HTTP de lectura de la rúbrica: ese es `docs/SPEC/05-integracion-canvas.md`
§5.3.1 (endpoint 17, `GET /courses/:id/rubrics/:id`) y §5.4 (caché de 15 minutos, A-089, A-137, ya
citados en §12.1.3 regla 1). Lo que fija esta sección es cómo se clasifica, se presenta y se evalúa
esa rúbrica en la columna derecha de la pantalla de corrección.

### 12.9.1 Clasificación de criterios

La rúbrica embebida en el `assignment` (sin `include[]`) trae `criterion_id`, `ratings[]` y sus `id`;
los ajustes de presentación (`free_form_criterion_comments`, `hide_points`, `hide_score_total`) se
leen con la llamada adicional a `rubrics/:id`, ya declarados en `entrega` (§12.2.7). Cada criterio se
clasifica en tres clases (A-138, Q-2.7-29):

| Clase | Cuándo | Tratamiento |
|---|---|---|
| **Evaluable** | Criterio con `ratings` y puntos | Selector de rating + campo numérico, sincronizados; eligiendo un rating se precargan sus puntos, y un número sin rating exacto deja el selector en «puntos libres» |
| **Solo lectura** | `learning_outcome_id` no nulo, o `criterion_use_range = true` | Se pinta en gris con candado y el texto «se evalúa en SpeedGrader» con enlace a Canvas; su `criterion_id` **no** entra en el payload |
| **No suma** | `ignore_for_scoring = true` | Se evalúa igual que un criterio evaluable, pero se excluye de la suma sugerida, con la etiqueta «no suma» |

Si la rúbrica contiene al menos una fila de sólo lectura, **no se ofrece suma sugerida**: el campo de
nota nace vacío con el texto «esta rúbrica incluye criterios que la aplicación no puede calcular;
escribe la nota final» (A-138). Con `free_form_criterion_comments = true` se oculta el selector de
ratings y el criterio se evalúa con puntos y comentario, sin `rating_id`.

### 12.9.2 Formulario y validación antes de enviar

Grilla criterios × ratings; comentario por criterio, plegado salvo con comentarios libres. Cuatro
validaciones de cliente, contra la lectura de rúbrica inmediatamente anterior al envío: todo
`criterion_id` del payload existe en esa lectura; todo `rating_id` pertenece a ese criterio; `0 ≤
points ≤ criterio.points`; la suma frente a `rubric_settings.points_possible` es sólo informativa y
nunca bloquea, porque el crédito extra es legítimo (A-141, §12.10.1).

### 12.9.3 Cambios de rúbrica entre lecturas: reconciliación, nunca pérdida

`correccion.huella_rubrica` (ya declarada en §12.2.3) es un `SHA-256` sobre la serialización canónica
de los criterios, sus ratings y los tres ajustes de presentación, calculado en cada lectura. Al abrir
una corrección cuya huella difiere de la persistida, el borrador **no se descarta**: la pantalla entra
en **modo reconciliación** con tres bloques —criterios que siguen igual con su valor conservado,
criterios eliminados con la etiqueta «eliminado en Canvas; estos N puntos ya no cuentan», y criterios
nuevos vacíos y obligatorios—. **La publicación queda bloqueada** hasta pulsar **«He revisado los
cambios»**, que se registra en `bitacora` (Q-2.7-28). Se relee de nuevo justo antes de publicar
(§12.1.3 regla 1); si volvió a cambiar, la publicación se cancela sin efecto y la pantalla vuelve al
paso de reconciliación. **Ningún `PUT` lleva un `criterion_id` ausente de la lectura inmediatamente
anterior.**

### 12.9.4 Sin rúbrica asociada

Cuando `entrega.tiene_rubrica = false` (§12.2.7), la pantalla muestra sólo nota y comentario, con la
banda «esta entrega no tiene rúbrica asociada en Canvas; puedes registrar la nota y el comentario
igual» y el enlace a la pantalla de rúbricas del curso en Canvas —**la aplicación no crea rúbricas**
(§12.1.1). El `PUT` de publicación se envía sin ninguna clave `rubric_assessment[...]` (Q-2.7-26).

### 12.9.5 `use_rubric_for_grading` y desajuste de puntos

Con `use_rubric_for_grading = true`, el campo de nota se **precarga** con la suma de criterios y la
pantalla dice «esta rúbrica está ligada a la calificación en Canvas»; con `false`, la suma se muestra
sólo como sugerencia con la etiqueta «sugerencia; en Canvas esta rúbrica no calcula la nota». En los
dos casos el corrector puede sobrescribir, y **manda lo que Canvas devuelve** tras publicar (A-141).
Si `rubric_settings.points_possible` difiere de `entrega.puntos_posibles`, se muestran los dos números
juntos con el interruptor **«escalar proporcionalmente a los puntos de la tarea»**
(`correccion.escalado_aplicado`, ya declarada), apagado por defecto, con el resultado calculado antes
de confirmar. `hide_points` y `hide_score_total` no cambian el cálculo ni el envío: son ajustes de
presentación **hacia el estudiante**, que se respetan en el comentario de la entrega (§12.10.2) y se
ignoran en el formulario del corrector, cuyo destinatario es el equipo docente (Q-2.7-27).

### Criterios de aceptación de 12.9

1. **CA-12.9-01.** Una fila con `criterion_use_range = true` se pinta en modo lectura y su
   `criterion_id` no aparece en el `rubric_assessment` enviado.
2. **CA-12.9-02.** Elegir un rating rellena el campo de puntos con el valor exacto del rating; escribir
   un número sin coincidencia exacta deja el selector en «puntos libres».
3. **CA-12.9-03.** Cambiar un criterio en Canvas entre la apertura y el guardado de un borrador deja
   la corrección en modo reconciliación en la siguiente apertura, sin borrar el valor de los criterios
   que siguen existiendo.
4. **CA-12.9-04.** Publicar sin pulsar «He revisado los cambios» tras una reconciliación pendiente
   responde `409` y no llama a Canvas.
5. **CA-12.9-05.** Una entrega con `tiene_rubrica = false` muestra el formulario reducido y su `PUT`
   de publicación no contiene la clave `rubric_assessment`.
6. **CA-12.9-06.** El interruptor de escalado, apagado por defecto, no altera la nota mostrada hasta
   que se activa explícitamente y se confirma la previsualización.

---

## 12.10 Registro de la calificación: formulario, comentario y publicación en Canvas (R2.7.6)

Este capítulo **no define** el mecanismo HTTP de escritura: es `docs/SPEC/05-integracion-canvas.md`
§5.3.2 (endpoint 25, `PUT .../submissions/:user_id`) y §5.5 (la escritura síncrona número 5 de la
lista cerrada, con su contrato de seis puntos: lectura antes del efecto, intención persistida antes
de la llamada, tope de 20 s, resultado en pantalla, registro en `bitacora`, ninguna comunicación al
estudiante). Lo que fija esta sección es **cuándo** se publica, **qué** se envía y **con qué regla de
negocio**, sobre la máquina de estados ya fijada en §12.3.

### 12.10.1 El borrador es local; publicar es un acto explícito

Guardar (`PUT …/borrador`) escribe `nota_local`, `rubrica_local` y `comentario` y **nunca llama a
Canvas**; con el primer contenido guardado, la corrección pasa a `EN_CURSO` (§12.3.2). «Marcar como
lista» exige una nota válida según el `grading_type` de la entrega:

| `grading_type` | Campo | `submission[posted_grade]` |
|---|---|---|
| `points` | Numérico, dos decimales | El número: `18.5` |
| `percent` | Numérico 0–100 | Con el signo: `85.5%` |
| `pass_fail` | Selector de dos estados | `pass` o `fail` |
| `letter_grade` con esquema | Selector del esquema | La letra: `A-` |
| `letter_grade` sin esquema | Numérico, con motivo escrito | El número, con `prefer_points_over_scheme=true` |
| `gpa_scale`, `not_graded` | Deshabilitado, con motivo | Nada: nace `NO_PUBLICABLE` (§12.3.3) |

La aplicación **no redondea**: el campo acepta como máximo dos decimales y envía exactamente lo que
el corrector escribió; tras publicar se relee siempre y la interfaz muestra el valor que **Canvas**
devolvió, no el enviado (A-141). El formulario calcula la sugerencia de la rúbrica pero no decide: el
corrector puede sobrescribir el campo final en cualquier momento.

### 12.10.2 Comentario y pie de trazabilidad

El comentario del corrector es opcional, pero toda publicación envía siempre `comment[text_comment]`,
porque la aplicación añade un **pie de trazabilidad fijo** que compensa la firma única del titular de
la credencial (A-142, §12.4.5) — mecanismo que este capítulo ya fijó en §12.4.5 y no redefine, sólo
completa con el contenido exacto que `correccion.comentario_renderizado` (§12.2.3) produce:

```
<texto libre del corrector, si lo escribió>

—
Entrega: <nombre de la entrega> (cierre <fecha> <zona>)
Versión revisada: <sha corto> · https://github.com/<org>/<repo>/tree/<sha completo>
Corregido por <nombre> (<rol>). Publicado por el sistema de gestión del curso.
```

Si `hide_points` o `hide_score_total` de la asociación de rúbrica son `true`, el pie **no** incluye
puntos por criterio ni total (Q-2.7-27). Si la versión no existe (`SIN_COMMITS`), la línea de versión
se sustituye por «no se registró ninguna confirmación anterior a la fecha de cierre». El texto íntegro
se muestra en el diálogo de publicación **antes** de confirmar, y es la misma previsualización que
protege contra escribir en el campo equivocado (§12.17.4). Se persiste literal en
`publicacion_nota.payload_enviado` (Q-2.7-25).

### 12.10.3 Grano de la escritura: una llamada por grupo, salvo excepción documentada

El grano de la corrección es `(entrega, sujeto)`, pero el grano de la escritura en Canvas lo decide
`entrega.grade_group_students_individually` (ya declarada en §12.2.7), leído de Canvas y no decidido
por la aplicación (A-139, Q-2.7-34):

| `grade_group_students_individually` | Escritura |
|---|---|
| `false` (Canvas propaga a todos) | **Una** llamada, dirigida al integrante del conjunto congelado con menor `canvas_user_id` **entre los que aparecen en `gradeable_students`** (§12.11.2), con `comment[group_comment]=true` |
| `true` (Canvas no propaga) | **N** llamadas, una por integrante, sin `group_comment` |

No existe override manual por integrante cuando el campo es `false`: cualquier `PUT` volvería a
propagar a todos. En su lugar, la pantalla ofrece **«calificar individualmente a cada integrante en
Canvas»**, que cambia `assignment[grade_group_students_individually]` a `true` con previsualización y
consentimiento explícito —mismo patrón de A-143/A-144—, exige `tarea.administrar` y sólo se ofrece
mientras no exista ninguna fila de `publicacion_nota` para esa entrega.

### 12.10.4 Pre-chequeo obligatorio, antes de llamar a Canvas

Por entrega, antes de cada publicación, con caché de 15 minutos: se leen los **períodos de
calificación** (`is_closed`); si el que contiene la fecha de la entrega está cerrado, la corrección
pasa a `NO_PUBLICABLE` con `motivo_no_publicable = PERIODO_CERRADO` **sin intentar la llamada**
(§12.3.3, A-140, Q-2.7-64); se comprueba el estudiante contra `gradeable_students` —filtro
conservador, no verdad documentada—, y si no aparece, `motivo_no_publicable = NO_GRADEABLE` (A-140,
Q-2.7-63); se lee la política de entrega tardía y, si hay deducción automática activa, se avisa al
corrector de que la aplicación va a enviar **`late_policy_status=none`** siempre, salvo la acción
explícita «marcar como no entregada» (§12.2.4, A-139, Q-2.7-67).

### 12.10.5 Verificación posterior obligatoria

Inmediatamente después de escribir, la aplicación relee con la lectura masiva de §12.11.2 y compara,
por integrante del conjunto congelado, `score` con lo enviado (tolerancia `0,001`), `graded_at` y
`points_deducted`. El resultado decide la transición: a `PUBLICADA` si todos concuerdan, a
`PUBLICADA_CON_ADVERTENCIA` si alguno difiere o quedó sin nota tras el remedio individual, a
`ERROR_PUBLICACION` si Canvas rechazó la escritura, con el cuerpo literal en
`publicacion_nota.respuesta` (§12.3.2). **Si la propagación de un grupo no alcanzó a alguien, se
publica individualmente al que falte**, con una llamada por persona: la iteración es el remedio, no
el mecanismo (A-139).

### 12.10.6 Publicación masiva por el profesor

Desde la pestaña «Estado de la entrega» (§12.13), quien tiene `nota.publicar` selecciona filas en
`LISTA_PARA_PUBLICAR` y pulsa «publicar seleccionadas». **No es un trabajo nuevo ni usa
`update_grades`**: ejecuta la misma escritura individual de §12.10.3, una por sujeto y en secuencia,
con barra de progreso «publicando *N* de *M*», resultado por fila y reanudable si se cierra la
pestaña —al reintentar, las ya publicadas se saltan—. Respeta la regla de una sola petición
simultánea por curso contra Canvas (§12.1.3 regla 7). Un fallo en un sujeto no bloquea el resto del
lote (A-139, Q-2.7-04).

### 12.10.7 Entregas sin commits: flujo masivo explícito

Una versión en `SIN_COMMITS` se asigna y se abre igual que cualquier otra, nunca se califica sola; en
la bandeja aparece en un cubo aparte «Sin commits al cierre (N)». El profesor dispone de la acción
**«Publicar sin entrega (N sujetos)»**: lista los sujetos afectados con la causa probable —«no aceptó
la invitación», «hay commits sin atribuir», «rama por defecto, último commit hace *N* días»—,
**excluye por defecto** a quienes nunca aceptaron la invitación, pide una sola nota que la aplicación
propone pero no aplica sola, un comentario editable con la plantilla «no se registraron commits en tu
repositorio al cierre de esta entrega», exige confirmación escrita, y ejecuta el lote sujeto a sujeto
con el pre-chequeo completo de §12.10.4, sin `late_policy_status=missing` (Q-2.7-61).

### Criterios de aceptación de 12.10

1. **CA-12.10-01.** Guardar un borrador no produce ninguna llamada HTTP a Canvas; sólo «Publicar en
   Canvas» la produce, tras confirmación.
2. **CA-12.10-02.** El `PUT` de publicación de una entrega `pass_fail` envía exactamente `pass` o
   `fail`, nunca un valor numérico intermedio.
3. **CA-12.10-03.** El comentario enviado a Canvas siempre contiene el pie de trazabilidad, incluso
   cuando el corrector no escribió texto libre.
4. **CA-12.10-04.** Publicar una entrega grupal con `grade_group_students_individually = false`
   produce exactamente una llamada a Canvas, dirigida al integrante calificable de menor
   `canvas_user_id`, con `group_comment = true`.
5. **CA-12.10-05.** Publicar sobre un período de calificación cerrado deja la corrección en
   `NO_PUBLICABLE` con `motivo_no_publicable = PERIODO_CERRADO` sin que se registre ninguna llamada
   HTTP de escritura.
6. **CA-12.10-06.** Tras una publicación exitosa, si la relectura devuelve un `score` distinto del
   enviado más allá de `0,001`, la corrección queda `PUBLICADA_CON_ADVERTENCIA` con el descuento
   visible.
7. **CA-12.10-07.** Interrumpir una publicación masiva a mitad y reanudarla no vuelve a publicar las
   filas ya confirmadas.
8. **CA-12.10-08.** El flujo «Publicar sin entrega» excluye por defecto a los sujetos cuya invitación
   nunca fue aceptada, y su lista es editable antes de confirmar.

---

## 12.11 Estado de corrección de la tarea: matriz, agregados y doble contador (R2.7.7)

### 12.11.1 La pestaña «Estado de la entrega»

Es la tercera pestaña de `/cursos/{id}/correccion` (§12.6.1), **siempre visible para todo miembro
activo del curso**: se lee con `curso.ver`, tal como fija §12.4.2, y **no** exige
`correccion.asignar` — es la corrección de precedencia que ya deja escrita §12.1.4 (RG-125). Contiene
dos vistas:

1. **Matriz nominal**: una fila por sujeto activo de la tarea, una columna por entrega, cada celda
   coloreada por `correccion.estado` con la etiqueta en español de §12.3.1 y los distintivos de las
   banderas ortogonales (§12.3.4, §12.17). Sobre una fila ajena el botón principal es **«ver»**, nunca
   «corregir» (§12.4.2).
2. **Tres tablas de agregados**: por corrector, por sección y por entrega, con el recuento por estado.

Cabecera con el **doble contador**, siempre las dos cifras juntas: **«N de M corregidas en la
aplicación · K de M con nota en Canvas · comprobado hace X»**. N sale de `correccion.estado ∈
{PUBLICADA, PUBLICADA_CON_ADVERTENCIA}`; K sale de `estado_canvas_submission` (§12.2.5), nunca de
`submission_summary` (§12.1.3 regla 1, A-142). Filtros: entrega, corrector, sección, estado, «sólo con
discrepancia con Canvas», «sólo retirados», «sólo sin commits». Exportación a CSV de lo que la sesión
puede ver.

### 12.11.2 De dónde sale «lo que Canvas dice»

El espejo `estado_canvas_submission` (§12.2.5) se llena con la lectura masiva y paginada `GET
/courses/:id/students/submissions?student_ids[]=all&assignment_ids[]=<id>` (§5.3.1 endpoint 16), leída
**una vez por entrega**, nunca una vez por estudiante. Un sujeto se considera «con nota en Canvas» si
y sólo si `graded_at` y `score` son ambos no nulos — predicado que no depende de `workflow_state`,
cuyo comportamiento sobre una submission `unsubmitted` calificada no está documentado
**[MEDIR]** (`Q-2.7-55`). Si Canvas tiene nota para un sujeto sin fila de `correccion`, se crea la
fila en `SIN_CORRECTOR`. La misma lectura alimenta `gradeable_students` (§12.10.4) y el pre-chequeo de
publicación.

### 12.11.3 Presupuesto y frescura

La respuesta de `GET .../correccion/estado` se resuelve en una sola consulta agregada, bajo el mismo
techo de rendimiento que el resto de tableros de la aplicación: **menos de 400 ms en el percentil 95
con 200 sujetos**, y **nunca llama a Canvas para renderizarse** (Ley 1, §12.1.3 regla 1). El botón
**«comprobar contra Canvas»** no lee en la petición: **encola** la reconciliación de §12.15 y la vista
se revalida cuando el trabajo termina.

### Criterios de aceptación de 12.11

1. **CA-12.11-01.** Una sesión de ayudante sin `correccion.asignar` abre «Estado de la entrega» y ve
   la matriz nominal completa, los tres agregados y el doble contador; la pestaña «Repartir» no le
   aparece.
2. **CA-12.11-02.** El segundo número del doble contador nunca se calcula desde
   `submission_summary`; una búsqueda de esa cadena en el código de esta pantalla no encuentra
   ninguna llamada.
3. **CA-12.11-03.** Filtrar «sólo con discrepancia con Canvas» muestra exactamente los sujetos cuyo
   `contraste_canvas` deriva en `DIVERGE` o `SOLO_EN_CANVAS` (§12.14).
4. **CA-12.11-04.** El render de la matriz con 200 sujetos y 3 entregas responde bajo 400 ms en el
   percentil 95, sin ninguna llamada HTTP externa.
5. **CA-12.11-05.** Pulsar «comprobar contra Canvas» no bloquea la interfaz mientras dura la
   reconciliación; la vista se actualiza sola cuando el trabajo encolado termina.

---

## 12.12 Plazo de corrección y seguimiento de avance (R2.7.7, continuación)

### 12.12.1 Fecha objetivo de corrección

`entrega.fecha_objetivo_correccion` (ya declarada en §12.2.7) es nullable y la fija un profesor con
`tarea.administrar` desde la tarjeta de la entrega; la aplicación **propone** cierre + 7 días en la
zona del curso y **no la aplica sola** — sin confirmación explícita, la entrega no tiene plazo y no
genera alertas (A-021, Q-2.7-57).

### 12.12.2 Incidencia por atraso

Cuando `ahora > fecha_objetivo_correccion` y quedan correcciones fuera de `{PUBLICADA,
PUBLICADA_CON_ADVERTENCIA, NO_PUBLICABLE}`, se abre **`CORRECCION_ATRASADA`** (severidad
`ADVERTENCIA`, una por entrega), visible en Pendientes, en la matriz de §12.11.1 con un distintivo
sobre la cabecera de la columna, y en el informe docente diario, porque esa incidencia se lee de la
misma tabla que alimenta las secciones de ese informe (§11.3.4, `docs/SPEC/11-informes-y-comunicacion.md`) —
este capítulo no redefine en cuál de sus cinco secciones aparece; se cierra sola cuando la entrega deja
de tener correcciones pendientes o pasa a `CERRADA`.

### 12.12.3 Contador de avance por corrector

Las tres tablas de agregados de §12.11.1 ya dan, por corrector, cuántas entregas le quedan; ese mismo
dato es el que compone la línea de avance de corrección del resumen del período que el informe diario
ya construye (§11.3.4, sección de resumen del período): este capítulo aporta el contenido —«notas
publicadas y correcciones pendientes» por entrega vencida— y ese capítulo posee el formato y el envío.

### Criterios de aceptación de 12.12

1. **CA-12.12-01.** Proponer una fecha objetivo de corrección y no confirmarla dentro del diálogo dice
   que la entrega no tiene plazo; ninguna alerta se genera para ella.
2. **CA-12.12-02.** Confirmar una fecha objetivo ya vencida con correcciones pendientes abre
   `CORRECCION_ATRASADA` en el ciclo siguiente, con severidad `ADVERTENCIA`.
3. **CA-12.12-03.** Publicar la última corrección pendiente de una entrega atrasada cierra la
   incidencia sin intervención manual.
4. **CA-12.12-04.** Un ayudante con `tarea.administrar` que intenta fijar la fecha objetivo recibe
   `403` si no tiene también rol `PROFESOR`, salvo que el permiso se lo conceda explícitamente sobre
   esa acción (§12.4.1).

---

## 12.13 Reconciliación periódica con Canvas: el trabajo `reconciliar_notas_canvas` (R2.7.7, continuación)

**Canvas es la fuente de verdad de qué está realmente calificado**, y la aplicación lo sincroniza en
sentido inverso de forma periódica (Q-2.7-56). El mecanismo genérico de todo trabajo periódico —cola,
garantías, recuperación de huérfanos— es de `docs/SPEC/14-infraestructura-y-despliegue.md` y de la
cadencia ya resumida en `docs/SPEC/05-integracion-canvas.md` §5.4.3; este capítulo fija sólo las
reglas de negocio que gobiernan cuándo se dispara y qué produce.

### 12.13.1 Cadencia

Por entrega, no por curso: **cada 30 minutos** mientras la entrega esté en ventana de corrección
—desde su fecha efectiva máxima vencida hasta que todas sus correcciones estén en estado terminal, o
hasta 21 días después del cierre, lo que ocurra antes—; **una vez al día** fuera de esa ventana
mientras la tarea no esté `CERRADA`; **nunca** para tareas `ARCHIVADA`. Se dispara además
**inmediatamente** después de cada publicación (§12.10.5) y **bajo demanda** con el botón «comprobar
contra Canvas» (§12.11.3), que encola y no llama dentro de la petición HTTP.

### 12.13.2 Frescura y encolado automático

Al abrir la pestaña «Estado» o una corrección, si `estado_canvas_submission.sincronizado_en` tiene más
de 30 minutos, se **encola automáticamente** la reconciliación y la vista se revalida al terminar; la
vista nunca espera por ella (Ley 1).

### Criterios de aceptación de 12.13

1. **CA-12.13-01.** Una entrega fuera de ventana de corrección con tarea `CERRADA` no dispara ningún
   ciclo de `reconciliar_notas_canvas`.
2. **CA-12.13-02.** Publicar una nota dispara, en la misma operación, una reconciliación inmediata
   para esa entrega.
3. **CA-12.13-03.** Abrir la pestaña «Estado» con el espejo de más de 30 minutos de antigüedad encola
   la reconciliación sin bloquear el primer render.

---

## 12.14 Contraste con Canvas: derivación de `contraste_canvas` y conflictos de publicación (R2.7.7, continuación)

### 12.14.1 `contraste_canvas` es una derivación, no una columna

Tal como adelanta §12.3.4, `contraste_canvas` **no se persiste en `correccion`**: es el resultado de
una función pura en `backend/app/dominio/estado_correccion.py` que compara la última
`publicacion_nota` exitosa de cada integrante del conjunto congelado contra las filas de
`estado_canvas_submission` (§12.2.5) de esos mismos integrantes (RG-187). Toma exactamente cuatro
valores, sin excepción:

| Valor | Cuándo |
|---|---|
| `NO_COMPROBADO` | Nunca se leyó el espejo para ese sujeto |
| `CONCUERDA` | El `score` de Canvas coincide con la última publicación propia, tolerancia `0,001` |
| `DIVERGE` | El `score` difiere, o `graded_at` de Canvas es posterior a la última publicación propia |
| `SOLO_EN_CANVAS` | Hay nota en Canvas sin ninguna `publicacion_nota` propia que la explique |

**Persistir esta bandera junto a la tabla espejo produciría dos verdades del mismo hecho** en cuanto
un ciclo actualice una y no la otra; por eso se calcula siempre en el momento de leerse (RG-187).
Cuando diverge, se abre la incidencia **`NOTA_DIVERGENTE_EN_CANVAS`** (`ADVERTENCIA`), con el detalle
literal: «Canvas: *nota* puesta por *nombre* el *fecha* · aplicación: *nota* publicada el *fecha*».
**El estado local nunca se sobrescribe con lo que diga Canvas**: `correccion.estado` conserva lo que
la aplicación hizo, y es `contraste_canvas` el que cambia (Ley 2).

### 12.14.2 Conflicto al momento de publicar

Antes de cada escritura, la lectura previa de §12.10.4/§5.5 —garantía 3 del contrato único de
escrituras síncronas— se convierte aquí en regla de conflicto: hay conflicto cuando la submission de
Canvas tiene `graded_at` no nulo **y** (no existe publicación propia exitosa para ese estudiante, **o**
`graded_at` de Canvas es posterior a la última publicación propia, **o** el `score` de Canvas difiere
de la última nota propia más allá de `0,001`) (Q-2.7-58). Ante conflicto, la corrección **permanece en
`LISTA_PARA_PUBLICAR`**, no se llama a Canvas, se abre `NOTA_DIVERGENTE_EN_CANVAS`, y el diálogo
muestra las dos versiones con tres salidas nombradas:

1. **«Publicar la mía y reemplazar la de Canvas»** — exige marcar una casilla y queda en `bitacora`
   con el valor anterior en `antes`.
2. **«Adoptar la de Canvas»** — copia la nota al espejo, cierra la incidencia y **no escribe en
   Canvas**.
3. **«Dejarlo como está»** — no cambia nada.

En una entrega grupal, el chequeo se hace sobre **todos** los integrantes del conjunto de corte, y
basta uno en conflicto para abrir el diálogo, que los lista todos. La comprobación se hace con la
**misma llamada masiva** de §12.11.2, sin coste adicional cuando se publica un lote.

### 12.14.3 Recorrección tras una republicación con reclamo abierto

Toda republicación sobre una corrección con `reclamo_abierto = true` exige la confirmación escrita
descrita en §12.17.2, además de la comparación de conflicto de esta sección; las dos comprobaciones
se aplican juntas, no una en lugar de la otra.

### Criterios de aceptación de 12.14

1. **CA-12.14-01.** Con dos filas de `estado_canvas_submission` iguales a la última publicación
   propia, `contraste_canvas` deriva `CONCUERDA` sin abrir ninguna incidencia.
2. **CA-12.14-02.** Con una nota puesta en SpeedGrader después de la última publicación propia,
   `contraste_canvas` deriva `DIVERGE` y abre `NOTA_DIVERGENTE_EN_CANVAS` con el detalle de las dos
   notas y sus autores.
3. **CA-12.14-03.** Intentar publicar sobre un conflicto detectado responde con el diálogo de
   conflicto y **ningún** `PUT` se envía hasta que se elige una de las tres salidas.
4. **CA-12.14-04.** Elegir «Adoptar la de Canvas» cierra la incidencia y no genera ninguna llamada de
   escritura a Canvas.
5. **CA-12.14-05.** Una relectura posterior a la propia publicación exitosa nunca se interpreta como
   conflicto ajeno, porque su `graded_at` no es posterior a `publicacion_nota.intentada_en`.

---

## 12.15 Casos borde, conflictos y recuperación

### 12.15.1 Reclamo de un estudiante sobre una nota

Los estudiantes no son usuarios de la aplicación (§12.1.1) y no registran reclamos por sí mismos: un
reclamo llega por Canvas o por correo, y **un miembro del equipo docente con `curso.ver` lo registra**
desde la pantalla de corrección con el botón «Registrar reclamo». Se modela con el mecanismo ya
fijado en §12.2.6: se añade una fila de `nota_interna_correccion` con `clase = RECLAMO_ABIERTO` y se
pone `correccion.reclamo_abierto = true` (§12.3.4) — **no se abre ninguna incidencia**, porque el
catálogo de tipos es cerrado y esta fila da la misma trazabilidad (§12.2.6).

Efectos, y ninguno más: (1) distintivo visible en la bandeja, en la matriz de §12.11.1 y en la
pantalla de corrección; (2) toda republicación exige la confirmación de §12.14.3; (3) se abre el panel
**«Evidencia de la entrega»**, construido enteramente desde datos persistidos, sin ninguna llamada
externa (Ley 1): el SHA capturado con su fecha de committer, la fecha efectiva de cierre con su regla
de origen, la regla de corte de A-102 escrita literalmente, los commits del repositorio en las 48
horas alrededor del corte marcando los huérfanos, y el historial completo de versiones de ese par con
su `intento` y su `motivo` (Q-2.7-68). **No congela la nota**: congelarla impediría exactamente lo que
un reclamo fundado exige, que es corregirla.

El reclamo se cierra con una nueva fila `clase = RECLAMO_CERRADO` y `desenlace_reclamo ∈ {SIN_CAMBIO,
NOTA_CORREGIDA, ERROR_DE_LA_APLICACION}` (§12.2.6, obligatorio), con `nota.publicar` si el desenlace es
`NOTA_CORREGIDA` (§12.4.1). Un mensaje opcional al estudiante sale por el canal de comunicación activo
y siempre por el *outbox* —este capítulo sólo fija que se encola, no su redacción ni su despacho
(§12.1.1).

### 12.15.2 Corrección de una nota ya publicada

`PUBLICADA` o `PUBLICADA_CON_ADVERTENCIA` → `EN_CURSO` con la acción explícita **«Reabrir
corrección»** y motivo obligatorio (`correccion.motivo_reapertura`, ya declarada en §12.2.3; §12.3.2).
**La nota publicada no se modifica jamás de forma automática**: una nueva publicación crea
`publicacion_nota` con `intento` siguiente (Ley 2) y pasa por el chequeo de conflicto de §12.14.2 antes
de escribir. La nota anterior queda íntegra en el historial.

### 12.15.3 Entrega sin versión registrada aún

Cubierto en §12.8.3 y §12.5.2: la asignación y la corrección local avanzan sin versión; sólo
«Publicar en Canvas» las necesita (`correccion.version_entrega_id` no nulo, exigido al marcar como
lista, §12.3.2).

### 12.15.4 Ayudante que pierde el permiso a mitad de corregir

Retirar `nota.publicar` a un ayudante con la sesión abierta hace que su siguiente `POST .../publicar`
responda `403` sin que la persona tenga que volver a entrar (§12.4.6, A-023); su borrador y las
correcciones ya `LISTA_PARA_PUBLICAR` quedan intactas, a la espera de quien conserve el permiso. El
retiro completo del curso está cubierto en §12.5.5 y §12.4.3.

### 12.15.5 Versión recapturada mientras la corrección avanzaba

Cuando aparece una versión vigente distinta de `correccion.version_entrega_id`, se marca
`version_desactualizada = true` (§12.3.4) y se abre `CORRECCION_DESACTUALIZADA` (`ADVERTENCIA`,
Q-2.7-60). En `ASIGNADA`/`EN_CURSO`, banda ámbar con los dos SHA y el enlace de comparación; al marcar
como lista se actualiza `version_entrega_id` y la bandera se limpia. En `LISTA_PARA_PUBLICAR`, la
publicación queda bloqueada hasta «He revisado la versión nueva» (un clic, con `bitacora`). En
`PUBLICADA`/`PUBLICADA_CON_ADVERTENCIA`, la nota en Canvas **no se toca nunca automáticamente**; la
decisión de recorregir la toma un humano, y si se recorrige, pasa por §12.14.2.

### 12.15.6 Estudiante retirado del curso

Un sujeto retirado **nunca desaparece** de la corrección (A-030, A-164): queda visible con su estado
real, en un cubo plegado «Retirados (N)», cerrado por defecto y nunca oculto. La corrección se puede
abrir y completar localmente sin restricción; sólo la escritura en Canvas depende del pre-chequeo de
§12.10.4 (`gradeable_students`), que puede dejarla `NO_PUBLICABLE` con motivo `NO_GRADEABLE`
(Q-2.7-62). En grupo, el retiro **no** cambia el conjunto de integrantes al que se propaga la nota: es
historia congelada al corte (§12.2.7, A-139); lo que sí se ajusta es que el destinatario de la
escritura única (§12.10.3) se elige entre los integrantes que sí son calificables.

### 12.15.7 Entrega eliminada o despublicada en Canvas

Detectado por sincronización (`entrega.estado_validacion`, ya citado en §12.2.7), con la cautela
anti-parpadeo de dos ciclos consecutivos. **`DESPUBLICADA`**: todo se conserva, se sigue trabajando, la
publicación queda `NO_PUBLICABLE` con motivo `ENTREGA_DESPUBLICADA` (§12.3.3), vuelve sola a publicable
si se republica en Canvas. **`ELIMINADA_EN_CANVAS`**: `NO_PUBLICABLE` con motivo `ENTREGA_ELIMINADA`;
se conservan intactas versiones, correcciones y notas ya publicadas; las dos únicas salidas son
restaurar la tarea en Canvas o marcar la entrega como excluida (Q-2.7-65). En los dos casos, el trabajo
del corrector —nota, rúbrica, comentario locales— no se pierde.

### 12.15.8 Entrega espontánea en Canvas y política de atraso

La lectura masiva de §12.11.2 ya trae `submitted_at`, `late` y `points_deducted` sin llamada
adicional. Si un estudiante entregó algo en Canvas pese a que el trabajo evaluable es el repositorio
(Ley 4), la pantalla de corrección muestra el bloque **«Este estudiante entregó algo en Canvas»**, con
la advertencia de que lo evaluable sigue siendo el SHA capturado. Si `points_deducted` llega distinto
de cero tras publicar, la corrección queda `PUBLICADA_CON_ADVERTENCIA` con el descuento visible y el
enlace para corregirlo en Canvas (§12.10.4, Q-2.7-67): **la diferencia nunca es silenciosa**.

### 12.15.9 Retroalimentación al código: sólo por Canvas

La aplicación no crea ni registra nada del lado de GitHub más allá de lo que otro capítulo ya crea
(repositorios, colaboradores, tags de entrega): no se solicitan permisos de *issues* ni de *pull
requests*, y el equipo docente tiene sólo `pull` (§12.4.4). La revisión línea a línea se resuelve con
el enlace de comparación ya ensamblado en §12.8.1; para comentar, el corrector escribe en el
formulario de §12.10.2, que viaja a Canvas junto con la nota. **Un comentario que un corrector deje a
título personal en GitHub queda fuera del sistema**: no se registra, no aparece en `bitacora` y no
cuenta como retroalimentación entregada; la pantalla lo dice en una línea para que nadie lo suponga
cubierto (Q-2.7-69).

### Criterios de aceptación de 12.15

1. **CA-12.15-01.** Registrar un reclamo añade una fila `RECLAMO_ABIERTO` en `nota_interna_correccion`
   y pone `correccion.reclamo_abierto = true`, sin abrir ninguna incidencia nueva.
2. **CA-12.15-02.** Cerrar un reclamo exige un `desenlace_reclamo` de los tres valores cerrados; un
   cierre sin desenlace responde `422`.
3. **CA-12.15-03.** Reabrir una corrección `PUBLICADA` exige un motivo no vacío y la deja en
   `EN_CURSO`; la nota ya publicada permanece en el historial de `publicacion_nota` sin alteración.
4. **CA-12.15-04.** Retirar `nota.publicar` a un ayudante con la pantalla de corrección abierta hace
   que su siguiente intento de publicar responda `403` sin recargar sesión.
5. **CA-12.15-05.** Recapturar una versión sobre una corrección `PUBLICADA` no modifica
   `correccion.estado` ni la nota en Canvas; sólo marca `version_desactualizada` y abre la incidencia
   correspondiente.
6. **CA-12.15-06.** Un sujeto retirado sigue visible en la matriz y en la bandeja, dentro del cubo
   «Retirados», y su corrección se puede completar localmente aunque no sea publicable.
7. **CA-12.15-07.** Una entrega que pasa a `ELIMINADA_EN_CANVAS` conserva sin cambios todas sus
   `version_entrega`, sus correcciones y sus `publicacion_nota` ya escritas.
8. **CA-12.15-08.** Un comentario de commit dejado en GitHub por un corrector no aparece en
   `bitacora` ni en ninguna vista de retroalimentación de la aplicación.

---

## 12.16 Trazabilidad de requisitos

| Requisito | Dónde se especifica |
|---|---|
| **R2.7.1** | §12.5 (asignación, cuatro mecánicas, sujetos tardíos, desalineación, reasignación y retiro de un ayudante) |
| **R2.7.2** | §12.6 (bandeja «Mis asignaciones», estados vacíos, aviso de novedades) |
| **R2.7.3** | §12.7 (orden estable, siguiente/anterior, siguiente sin corregir, atajos de teclado) |
| **R2.7.4** | §12.8 (ensamblaje del mecanismo de §9.9 dentro de la pantalla de corrección; metadatos de versión; estados borde) |
| **R2.7.5** | §12.9 (clasificación de criterios, formulario, reconciliación ante cambios de rúbrica) |
| **R2.7.6** | §12.10 (formulario de nota, comentario con pie de trazabilidad, grano de la escritura, pre-chequeo, verificación, publicación masiva) |
| **R2.7.7** | §12.11 a §12.14 (matriz nominal y doble contador, plazo y seguimiento de avance, reconciliación periódica, derivación de `contraste_canvas` y conflictos de publicación) |
| Casos borde y recuperación | §12.15 (reclamos, republicación, versión desactualizada, estudiante retirado, entrega eliminada, entrega espontánea, retroalimentación fuera de Canvas) |
