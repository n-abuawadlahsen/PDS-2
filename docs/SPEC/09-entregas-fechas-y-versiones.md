# 9. Entregas, fechas de cierre efectivas y versiones

Este capítulo especifica cómo la aplicación obtiene y mantiene las fechas de cierre de cada entrega de una tarea a partir de lo definido en Canvas —fecha base, fechas por sección y excepciones por estudiante o por grupo—, cómo materializa una **fecha efectiva** única y auditable para cada par `(entrega, sujeto)`, cómo la mantiene al día ante cambios posteriores en Canvas, cómo registra automáticamente al cierre la **versión** del repositorio correspondiente —el `commit_sha` a la fecha de corte—, cómo mantiene esa versión independiente de las demás entregas de la misma tarea, por qué la versión ya registrada no cambia aunque el repositorio siga recibiendo actividad, y cómo el equipo docente accede directamente a la versión que le corresponde revisar.

**Requisitos que satisface:**

- **R2.4.1** Obtener y considerar las fechas de entrega definidas en Canvas para cada entrega asociada a una tarea.
- **R2.4.2** Considerar fechas diferentes para las distintas secciones del curso cuando así esté configurado en Canvas.
- **R2.4.3** Considerar extensiones o modificaciones de fecha correspondientes a estudiantes o grupos específicos.
- **R2.4.4** Mantener actualizadas las fechas en base a posibles cambios que ocurran en Canvas.
- **R2.4.5** Registrar automáticamente, para cada entrega, la versión del repositorio correspondiente a su fecha de cierre.
- **R2.4.6** Mantener de manera independiente las versiones correspondientes a las distintas entregas de una misma tarea.
- **R2.4.7** Mantener correctamente las versiones ya registradas aunque posteriormente continúe existiendo actividad en el repositorio.
- **R2.4.8** Permitir a profesores y ayudantes acceder directamente a la versión que corresponde revisar para cada entrega.

---

## 9.1 Cómo leer este capítulo

**Orden de precedencia aplicado, sin excepciones:** enunciado → carta de arquitectura (`A-nnn`, `docs/ARQUITECTURA.md` revisión 2 — el documento más reciente, que ya incorpora la mayoría de las actas y lo señala con «ANULADA POR RG-nnn … Manda ahora A-nnn») → actas de reconciliación (`RG-nnn`, para lo que la carta no ha absorbido todavía o para el detalle de arbitraje) → respuestas de alcance (`Q-2.4-nn`). Donde una respuesta de alcance queda corregida por una regla `RG` o por la propia carta, este capítulo redacta directamente el resultado ya corregido y lo señala en la tabla siguiente.

**Restricción que gobierna todo el capítulo (Ley 1 y Ley 2, A-119, A-078):** ninguna pantalla de este capítulo consulta a Canvas o a GitHub para renderizarse; toda vista lee el espejo persistido —`fecha_efectiva`, `version_entrega`— y muestra su propio sello de antigüedad. Y **nada se sobrescribe, todo se supersede**: corregir una fecha o recapturar una versión nunca actualiza la fila anterior en sitio; cierra la vigente y crea una nueva, de modo que la pregunta «¿qué se capturó, cuándo y con qué fecha lo justificó?» siempre tiene respuesta en la base.

### Correcciones de precedencia que este capítulo aplica

| Punto | Lo que decía la respuesta de alcance | Lo que manda ahora | Fuente |
|---|---|---|---|
| Estados de `version_entrega` | Once valores, mezclando las fases del trabajo de captura (`PROGRAMADA`, `EN_VENTANA`, `RESOLVIENDO_SHA`, `ESPERANDO_LIMITE`, `ERROR_TRANSITORIO`) con los estados de la fila | **Seis valores, todos terminales, sin `DEFAULT`**. Las fases previas son del trabajo `capturar_versiones` (máquina 6), no de la fila; **no existe ninguna fila de `version_entrega` antes de que el SHA quede resuelto** | RG-024, RG-025, A-213 |
| Entrega vinculada con fecha ya vencida | `version_entrega.motivo = 'FECHA_YA_VENCIDA_AL_VINCULAR'`, con captura automática encolada al vincular | **No existe ese motivo de versión.** Es un estado de la *entrega*, `entrega.estado_validacion = 'VINCULADA_TRAS_EL_CIERRE'`, porque gobierna una guarda de captura; **no se captura nada hasta que el profesor confirma explícitamente** | RG-019, RG-195, A-203 |
| `version_entrega.motivo` | Cuatro valores | **Cinco valores**: se añade `CAPTURA_TARDIA_POR_ALCANCE`, para la captura que el sistema resuelve solo con el corte original cuando el trabajo de captura entró en servicio después de que la fecha ya hubiera vencido | RG-026, RG-154, RG-195, A-204 |
| `version_entrega.tag_motivo` | Seis valores | **Siete valores**: se añade `REPOSITORIO_INACCESIBLE` | RG-025, RG-181, RG-188, A-213 |
| Transiciones de `version_entrega.estado` tras la inserción | Una sola transición permitida (`CAPTURADA_SIN_TAG → CAPTURADA`) | **Dos transiciones**: se añade `CAPTURADA → CAPTURADA_SIN_TAG`, con un único origen —verificación diaria de etiquetas y webhook `delete`/`ref_type=tag`—, porque una etiqueta ya creada puede perderse después | RG-026, RG-188, A-213 |
| Columna que explica por qué se capturó a esa hora | FK obligatoria `version_entrega.fecha_efectiva_id` | **No existe esa columna** en el catálogo cerrado de `version_entrega` que fija A-204/RG-026. El motivo de la fecha se recupera consultando el historial *append-only* de `fecha_efectiva` para `(entrega_id, sujeto_id)` por `fecha_corte_utc`, no por una clave foránea directa | A-204, RG-026 (ausencia), citado contra Q-2.4-25 |
| Assignment eliminado en Canvas | `entrega.estado_validacion = 'HUERFANA'`, incidencia `ENTREGA_HUERFANA` | Valor **`ELIMINADA_EN_CANVAS`**; incidencia única **`ENTREGA_ELIMINADA_EN_CANVAS`** (severidad BLOQUEANTE) — el nombre coincide letra por letra con el estado, porque A-154 exige la misma palabra para el mismo hecho | RG-019, RG-021, A-203 |

**Vocabulario ya fijado en §7 y que este capítulo no redefine, solo usa:** `fecha_efectiva.origen ∈ {BASE, SECCION, GRUPO, ADHOC}` (§7.2.1, A-055). Se dice **fecha de cierre** (nunca *due date*, plazo o vencimiento) y **versión de la entrega** (nunca *snapshot*, corte o foto) — A-154. Todo instante se almacena en UTC y se presenta en la zona del curso con formato `dd-MM-yyyy HH:mm` y **la zona escrita al lado siempre** (A-152); nunca se muestra una hora desnuda. Todo estado interno se muestra traducido, con etiqueta fija; nunca aparece un identificador en mayúsculas en pantalla (A-155).

**Explícitamente fuera de este capítulo, citado y no redefinido:** el esquema completo de `tarea`, `entrega`, `regla_fecha`, `fecha_efectiva` y `version_entrega` —columnas, tipos, índices— vive en `docs/SPEC/03-modelo-de-datos.md` (censo de 72 entidades, filas 24, 27, 28 y 36); este capítulo cita las columnas por su nombre y documenta el **proceso** que las llena. Cómo se crea y aprovisiona un repositorio, y cuándo llega a estar `OPERATIVO` con acceso docente `CONCEDIDO`, es §8. La mecánica HTTP de la lectura de fechas contra Canvas (paginación, `include[]`, reintentos) es §5. La mecánica HTTP de la creación de etiquetas y de la lectura de commits contra GitHub es §6. El dashboard que **muestra** estas fechas y versiones —línea de entregas, estado agregado de R2.5.6— es §10. El acceso a la versión desde la pantalla de corrección (R2.7.4) y la publicación de la nota son §12. La composición congelada del grupo, `version_entrega.integrantes jsonb`, ya está fijada en RG-028 y citada en §7; este capítulo la usa sin reabrirla.

### Criterios de aceptación de §9.1

1. **CA-9.1-01.** Ninguna consulta de este capítulo contiene un cliente HTTP a Canvas o a GitHub fuera de los trabajos de sincronización y captura declarados en §9.4 y §9.6; una prueba con dobles que lanzan excepción en `ClienteCanvas` y `ClienteGitHub` pasa para toda pantalla de fecha o de versión.
2. **CA-9.1-02.** Buscar en el código la cadena `FECHA_YA_VENCIDA_AL_VINCULAR` no produce resultados fuera de comentarios históricos; `entrega.estado_validacion` acepta exactamente cuatro valores y `version_entrega.estado` acepta exactamente seis.
3. **CA-9.1-03.** Buscar la cadena `version_entrega.fecha_efectiva_id` en el esquema desplegado no produce ninguna columna.

---

## 9.2 Qué entidades usa este capítulo y qué no redefine

| Tabla | Rol en este capítulo | Definición completa |
|---|---|---|
| `tarea`, `sujeto` | Contexto: la fecha efectiva y la versión se calculan por `(entrega, sujeto)`, y `sujeto` cuelga de `tarea`, nunca de `entrega` (A-081) | §8, §3 |
| `entrega` | Trae `due_at_base`, `unlock_at`/`lock_at` (vía `regla_fecha`), `all_day`, `huella_fechas`, `canvas_updated_at`, `estado_validacion`, `validaciones`, `advertencias`, `ciclos_ausente`, `detectada_ausente_en`, `orden`, `slug`, `tipo ∈ {PARCIAL, FINAL}` | §3 (censo, fila 24); columnas fijadas en A-080, A-203, RG-019, RG-020 |
| `visibilidad_entrega` | Determina para qué `(entrega, estudiante)` existe siquiera la pregunta de la fecha (A-164) | §3 (fila 25), §7 |
| `regla_fecha` | Copia cruda de cada `AssignmentOverride` y de la fecha base de Canvas: `alcance`, `canvas_override_id`, `seccion_id`, `grupo_id`, `estudiante_ids bigint[]`, `due_at`, `unlock_at`, `lock_at`, `titulo` | §3 (fila 27); A-080 |
| `fecha_efectiva` | El resultado materializado de este capítulo: una fila por `(entrega_id, sujeto_id)` con `due_at_utc`, `origen`, `regla_fecha_id`, `ambigua`, `calculada_en`, `estado`, `vigente_hasta` | §3 (fila 28); A-080, A-082 |
| `version_entrega` | El otro resultado materializado: `commit_sha`, `commit_tree_sha`, `commit_fecha_autor`, `commit_fecha_committer`, `commit_mensaje`, `rama`, `fecha_corte_utc`, `intento`, `tag_nombre`, `tag_estado`, `tag_motivo`, `tag_error`, `tag_creado`, `estado`, `motivo`, `motivo_repositorio`, `vigente`, `reemplaza_a_id`, `advertencias text[]`, `verificacion jsonb`, `integrantes jsonb`, `origen_captura`, `creada_por_usuario_id`, `motivo_manual`, `capturada_en`, `repositorio_id` (**nullable**) | §3 (fila 36); A-084, A-204, RG-025, RG-026, RG-028 |
| `repositorio`, `repositorio_base`, `acceso_docente_repositorio` | Fuente de si hay repositorio, de su rama por defecto y de si el equipo docente ya tiene lectura | §8 |
| `commit`, `autoria_commit`, `evento_push` | El espejo de actividad del que se lee el commit de cierre | §6, §10 |

Este capítulo **no** redefine ninguna de estas columnas: las cita por nombre y documenta el algoritmo que las produce, que es contenido de proceso y no de esquema (A-055, A-082, A-101/A-213 son decisiones de proceso, no de tabla).

---

## 9.3 Cálculo de la fecha efectiva (R2.4.1, R2.4.2, R2.4.3)

### 9.3.1 Fuente autoritativa y por qué son dos llamadas y no una

Para cada entrega vinculada se leen **dos fuentes con jerarquía explícita** (A-054, §5 para la mecánica HTTP):

| Fuente | Qué aporta | Rol |
|---|---|---|
| **Aceleración** — `assignments?include[]=all_dates&include[]=overrides&include[]=assignment_visibility` | Detecta rápido y barato qué pudo cambiar; puebla `visibilidad_entrega` | Indicio, nunca fija el valor |
| **Autoridad** — `assignments/:aid/overrides`, paginado por entrega | El único origen que trae `student_ids` de los `AssignmentOverride` | **Fija `regla_fecha`** |

**Una discrepancia entre ambas fuentes abre incidencia** `DISCREPANCIA_FECHAS` con `detalle.motivo = ACELERACION_VS_AUTORIDAD`, y manda siempre la autoridad (A-054, Q-2.4-09). No se asume que los arrays de `include[]` sean completos: la documentación no lo garantiza, y como de esas fechas depende cuándo se captura la versión, apoyarse en un array sin garantía de completitud queda descartado.

### 9.3.2 El algoritmo de precedencia (A-055)

Para cada `(entrega, sujeto)` se calcula **un único instante** y se persiste en `fecha_efectiva` con la regla que lo produjo. Prioridad, de mayor a menor:

| # | Nivel | Condición | `origen` |
|---|---|---|---|
| 1 | Extensión individual | Override cuyo `student_ids` contiene el `canvas_user_id` del sujeto (o de alguno de sus integrantes, en tarea grupal) | `ADHOC` |
| 2 | Grupo | Override dirigido al `group_id` del sujeto, **evaluado sólo si la tarea es grupal** | `GRUPO` |
| 3 | Sección | Override dirigido a la sección de la matrícula activa del sujeto (o de alguno de sus integrantes) | `SECCION` |
| 4 | Base | `due_at` de la entrega, sin override aplicable | `BASE` |

**Reglas de aplicación, sin excepción:**

- **Empate dentro del mismo nivel** (dos secciones activas, dos `ADHOC`): gana **la fecha más tardía**; la fila se marca `ambigua = true` y se abre incidencia. Se elige la más tardía porque capturar antes de tiempo destruye trabajo legítimo, mientras que capturar más tarde sólo incluye trabajo adicional que el docente puede ver (A-055).
- **Un `ADHOC` más restrictivo que la sección igualmente gana**, aunque sea anterior: la cadena es estricta entre niveles y la regla de «la más tardía» sólo opera dentro de un mismo nivel (Q-2.4-04).
- **Sujeto no visible para esa entrega** (A-164): no se calcula fecha efectiva, no se programa captura, y la interfaz dice «esta entrega no aplica a este sujeto».
- **Sujeto visible sin ninguna fecha aplicable** (`due_at` nulo en la base y en todos los overrides que le alcanzan): no se programa captura; el estado es `SIN_FECHA`, «Sin fecha de cierre». No se inventa una fecha.
- **Fechas de sección** (`start_at`, `end_at`, `restrict_enrollments_to_section_dates`): se persisten en `seccion` pero **se ignoran para el cálculo**, porque la documentación las describe sólo en términos de matrícula y participación y no les atribuye efecto sobre `due_at` (Q-2.4-16). Si el `due_at` efectivo cae fuera del rango de participación de la sección, se muestra una advertencia informativa sin alterar el cálculo.

### 9.3.3 Sujeto grupal: el máximo entre integrantes, no un valor único

En una tarea grupal el sujeto es el grupo (A-081, A-164); hay **una sola versión por repositorio y por entrega**. La fecha que la rige se calcula aplicando la cadena de 9.3.2 **a cada integrante `accepted`** (los que cuentan según A-048) y tomando el **máximo** de las fechas resultantes (Q-2.4-05):

- Un integrante `SIN_FECHA` no aporta candidato y no anula al resto; si ninguno aporta candidato, el sujeto queda `SIN_FECHA`.
- Si las fechas resultantes no son todas iguales, la fila se marca `ambigua = true`, `origen` toma el valor del nivel que produjo el máximo, y se abre incidencia `DISCREPANCIA_FECHAS` con `detalle.motivo = GRUPO_HETEROGENEO` y la lista de integrantes con su fecha.
- Se elige el máximo por el mismo criterio de 9.3.2: capturar antes de tiempo destruye trabajo legítimo.
- La regla de sección de 9.3.2 punto 3, que habla de «la sección de su matrícula activa», se extiende para un sujeto grupal: se evalúa sobre las secciones de sus integrantes `accepted`; si difieren, se aplica el criterio general —la más tardía, `ambigua = true` e incidencia (Q-2.4-40).

### 9.3.4 `lock_at`, `unlock_at` y fechas de todo el día

| Campo | Rol exacto |
|---|---|
| `due_at` | **El único campo que dispara la captura**, que ordena la línea de entregas y que alimenta comunicaciones e informes. `fecha_efectiva.due_at_utc` se calcula sobre `due_at` y sobre nada más, como instante absoluto en UTC (Q-2.4-03, A-153) |
| `lock_at` | No manda nunca. Se persiste crudo en `regla_fecha.lock_at` y se muestra como dato informativo —«Canvas deja de aceptar entregas: …»— leído de la regla que ganó. Si es anterior a `due_at`, se advierte sin alterar ningún cálculo (Q-2.4-03) |
| `unlock_at` | No define el inicio del período de actividad de §10 (eso lo fija A-122/A-173 por los cierres, no por `unlock_at`). Alimenta únicamente el estado presentacional `FUTURA` de la entrega cuando es posterior a ahora (Q-2.4-07) |
| `all_day` / `all_day_date` | **No participan en ningún cálculo.** El disparo de la captura usa siempre `due_at` tal cual, como instante absoluto en UTC; nunca se deriva un fin de día. Si `all_day = true` llega, la interfaz muestra la hora exacta convertida **y además** la etiqueta «todo el día», sin ocultar la hora. `entrega.all_day` es triestado (`true`/`false`/`NULL` = «no informado»); con `NULL` no se muestra nada (A-153, Q-2.4-18) |

**No existe fecha de cierre manual introducida en la aplicación**, ni por entrega ni por sujeto: crear una fecha paralela a la de Canvas rompería la Ley 1 (Q-2.4-03).

### 9.3.5 Sujeto sin repositorio y overrides con datos sucios

| Situación | Qué hace la aplicación |
|---|---|
| El sujeto es visible en **al menos una** entrega de la tarea, aunque no en ésta | Se le aprovisiona repositorio igual (§8, A-164 paso 2); para la entrega que no le aplica, no hay fecha ni captura y la columna de esa entrega muestra «No aplica». El denominador de la línea de entregas de esa entrega no lo cuenta (Q-2.4-06) |
| `course_section_id` de un override apunta a una sección desconocida | Se encola un `sync_secciones` prioritario; si persiste **dos ciclos**, el override no contribuye a la fecha. Incidencia `OVERRIDE_NO_INTERPRETABLE`, ADVERTENCIA |
| `student_ids` con estudiantes no inscritos | Esos identificadores se ignoran para la fecha; si **todos** lo son, el override no contribuye. Advertencia en `regla_fecha.advertencias`; incidencia sólo en el caso «todos» |
| `group_id` de un grupo inexistente, o de otra `group_category`, o de una *differentiation tag* (`non_collaborative=true`) | El override **no aplica** al cálculo (A-047, A-055 nivel 2 sólo se evalúa en tarea grupal sobre el conjunto de grupos de la tarea). Incidencia `OVERRIDE_NO_INTERPRETABLE`, ADVERTENCIA |
| Override sin `due_at` ni `lock_at` | No aporta fecha, pero **sí aporta visibilidad**: entra en `visibilidad_entrega` con `origen = OVERRIDE`. Sin incidencia: es un uso legítimo | 

La regla de esperar **dos ciclos** antes de descartar un override sucio es la misma prudencia que el padrón aplica a un roster truncado (§7): un dato que falta puede ser un sync a medias, y actuar al primer intento produce falsos positivos sobre la fecha de cierre de una persona real (Q-2.4-39).

### Criterios de aceptación de §9.3

1. **CA-9.3-01.** Un estudiante con `ADHOC` y perteneciente a una sección con override propio recibe la fecha del `ADHOC`, aunque sea anterior a la de su sección; la fila queda con `origen = 'ADHOC'`.
2. **CA-9.3-02.** Dos secciones con override activo sobre el mismo sujeto (matriculado en ambas) producen `ambigua = true`, la fecha más tardía de las dos, e incidencia `ESTUDIANTE_EN_DOS_SECCIONES`.
3. **CA-9.3-03.** Un grupo con tres integrantes `accepted` en secciones con fechas distintas y sin `ADHOC` propio recibe la mayor de las tres fechas, con `ambigua = true` e incidencia `DISCREPANCIA_FECHAS` cuyo `detalle.motivo = GRUPO_HETEROGENEO`.
4. **CA-9.3-04.** Un override cuyo `due_at` es explícitamente nulo sobre una entrega con `due_at` base produce `fecha_efectiva` ausente para ese sujeto y estado `SIN_FECHA`, no un `due_at` heredado de la base.
5. **CA-9.3-05.** Cambiar `all_day` a `true` sobre una entrega con `due_at` a las 02:59 hora del curso no modifica ningún cálculo de captura; sólo añade la etiqueta «todo el día» en pantalla.

---

## 9.4 Materialización, resincronización y huella de cambios (R2.4.4)

### 9.4.1 La fecha efectiva se materializa, no se calcula al vuelo

`fecha_efectiva` es una **tabla**, no una vista ni una función (A-082). Se llena de forma *eager*: en cuanto la entrega está vinculada y el sujeto existe, en la misma transacción del trabajo que lo detecta. El índice único parcial `(entrega_id, sujeto_id) WHERE estado = 'VIGENTE'` más el índice `(estado, due_at_utc) WHERE estado = 'VIGENTE'` son lo que convierte «todo lo vencido y no capturado» en una consulta indexada para el trabajo de captura de §9.6, en vez de recalcular la prioridad de overrides de todo el curso en cada tick (Q-2.4-08).

**El recálculo no actualiza en sitio.** Por la Ley 2, la fila vigente pasa a `estado = 'SUPERSEDIDA'` con `vigente_hasta = now()` y se inserta una fila nueva `VIGENTE`. Ese encadenamiento **es** el historial de cambios de fecha: no hace falta una tabla aparte, porque una tabla `historial_fecha` separada duplicaría lo que la Ley 2 ya produce (Q-2.4-08, Q-2.4-13).

### 9.4.2 El disparador de resincronización es una huella, no `updated_at`

**Se descarta `assignment.updated_at`** como disparador: la documentación no aclara si crear, editar o borrar un `AssignmentOverride` cuenta como «modificar la tarea», y `AssignmentOverride` no expone ningún timestamp propio. Si la respuesta fuera que no lo toca, las extensiones individuales serían invisibles para el sincronizador y **R2.4.3 quedaría incumplido en silencio** (A-056).

**Decisión:** en cada ciclo se recupera el conjunto completo de reglas de fecha de la entrega por la fuente de autoridad, se normaliza y ordena canónicamente —reglas por `canvas_override_id` ascendente con `BASE` primero, `estudiante_ids` ordenados, instantes en UTC truncados al segundo, `titulo` excluido de la huella porque es cosmético— y se calcula un **SHA-256** (`entrega.huella_fechas`). Se compara con el valor almacenado. Si difiere: se reescribe `regla_fecha`, se recalculan las fechas efectivas con supersede, se reprograman las capturas (§9.6, §9.8) y se evalúan las comunicaciones (§11). Cuesta una comparación de 32 bytes y es inmune al supuesto no documentado (A-056, Q-2.4-10).

`entrega.canvas_updated_at` se persiste igualmente, pero sólo como dato informativo; **ningún camino de código lo lee para decidir**.

### 9.4.3 Cambio significativo frente a cambio cosmético

| Reacción | Cuándo |
|---|---|
| **Recalcular** fechas efectivas, sujetos, visibilidad | Siempre que cambie la huella. Sin umbral |
| **Registrar en historial** (supersede de `fecha_efectiva` + `bitacora`) | Siempre que cambie la huella. Sin umbral |
| **Alertar al docente** (banda en la tarea + informe) | Cambio de fecha efectiva sobre una entrega ya vencida o ya capturada; cambio de modalidad; `published` que pasa a `false` |
| **Anunciar en Canvas** | Sólo cambios de fecha de origen `BASE` o `SECCION`, de **60 minutos o más**, con `regla_comunicacion` del evento activa (§11) |

Campos **cosméticos** —descripción, HTML reserializado, orden de arrays, `title` de un override, variaciones de espaciado o mayúsculas— se actualizan en silencio, sin historial y sin alerta (Q-2.4-11). El nombre legible de la entrega es cosmético a efectos de reacción: se actualiza en pantalla y **no cambia `entrega.slug`**, que se congela con la primera captura (A-172).

### 9.4.4 Cadencia y orden de sincronización

| Escenario | Cadencia |
|---|---|
| Régimen normal | `sync_tareas_y_fechas` cada **5 minutos**, por curso |
| Dentro de las **2 horas** previas a una fecha efectiva de cierre | Cada **1 minuto** (A-114) |
| Botón «sincronizar ahora» | Encola de inmediato con permiso `curso.ver`; **nunca llama a la API dentro de la petición** (A-089). Si ya hay un ciclo en vuelo para el curso, el botón dice «sincronizando ahora mismo» y no encola un segundo, porque el cerrojo es `pg_advisory_lock(curso_id)` (A-115 garantía 5) |

**Orden fijo, no negociable dentro de un ciclo:** `sync_roster` → `sync_grupos` → `sync_tareas_y_fechas` → `materializar_sujetos` (Q-2.4-39). Las secciones y los grupos deben existir en la base antes de interpretar overrides que los referencian, y los sujetos se materializan sobre roster, grupos y visibilidad ya sincronizados. Si un `sync_roster` o `sync_grupos` del ciclo termina en `FALLIDA` o `TRUNCADA`, `sync_tareas_y_fechas` se pospone: ningún cálculo de fecha se hace sobre datos de un paso que falló.

Latencia máxima entre un cambio en Canvas y su reflejo en `fecha_efectiva.calculada_en`: **6 minutos** en régimen normal, **2 minutos** dentro de las dos horas previas a un cierre, **60 segundos** con «sincronizar ahora» (Q-2.4-12).

### Criterios de aceptación de §9.4

1. **CA-9.4-01.** Crear un `AssignmentOverride` en Canvas y esperar 6 minutos produce una fila `fecha_efectiva` nueva `VIGENTE` y la anterior (si existía) queda `SUPERSEDIDA` con `vigente_hasta` escrito.
2. **CA-9.4-02.** Editar sólo el `title` de un override existente no produce ninguna fila nueva de `fecha_efectiva` ni entrada en `bitacora`.
3. **CA-9.4-03.** Ejecutar `sync_grupos` con resultado `FALLIDA` en un ciclo pospone `sync_tareas_y_fechas` de ese ciclo; el ciclo siguiente lo reintenta.
4. **CA-9.4-04.** Pulsar «sincronizar ahora» dos veces seguidas mientras el primer ciclo sigue en vuelo encola un único trabajo, verificable por el `trabajo_id` devuelto.
5. **CA-9.4-05.** Un `group_id` que no resuelve a ningún grupo colaborativo del `conjunto_grupos` de la tarea deja el override sin efecto sobre la fecha y abre `OVERRIDE_NO_INTERPRETABLE` con severidad ADVERTENCIA.

---

## 9.5 Zona horaria y formato de presentación

Coherente con la convención global fijada en A-152 y ya citada por §7:

- **Almacenamiento:** UTC siempre, `timestamptz`. Ningún cálculo de negocio de este capítulo —vencimiento de `due_at`, comparación de huella, ventana de gracia— usa hora local.
- **Presentación:** la zona del curso (`curso.zona_horaria`, tomada de `Course.time_zone` al vincular, `America/Santiago` por defecto), no la del navegador ni una preferencia por usuario, para que profesor y ayudante en husos distintos vean la misma fecha de cierre.
- **Formato fijo:** `dd-MM-yyyy HH:mm` con la zona escrita al lado siempre — `17-09-2026 23:59 (America/Santiago)`. Reloj de 24 horas. La forma relativa se añade, nunca sustituye: «17-09-2026 23:59 (America/Santiago) · vence en 2 días».
- **Fechas heterogéneas**, formato exacto de la línea de entregas: «Cierre: 16-09-2026 23:59 (America/Santiago) · Sección 2: 17-09-2026 23:59 · 3 excepciones», con «3 excepciones» como desplegable con nombre del sujeto, fecha, etiqueta de origen (`ADHOC` → «Extensión individual», `GRUPO` → «Grupo Ⅹ», `SECCION` → «Sección Ⅹ») y el `canvas_override_id` en monoespaciado con botón de copiado (Q-2.4-17, Q-2.4-19).
- **Ambigüedad:** una fila `ambigua = true` lleva la insignia «fecha ambigua» y lista todas las candidatas con su origen.

### Criterios de aceptación de §9.5

1. **CA-9.5-01.** Ninguna vista de este capítulo renderiza un instante sin la zona horaria a su lado.
2. **CA-9.5-02.** Cambiar `curso.zona_horaria` no cambia ningún `due_at_utc` almacenado; sólo cambia la conversión de presentación en la siguiente carga de pantalla.
3. **CA-9.5-03.** Una fecha `ambigua = true` muestra, al desplegar, todas las fechas candidatas con su `origen` y su `canvas_override_id`.

---

## 9.6 Captura de `version_entrega`: disparador, máquina de estados y algoritmo de cierre (R2.4.5)

### 9.6.1 Disparador y por qué no existe fila antes de resolver el SHA

**Se programa por `(entrega, sujeto)`**, con su fecha efectiva propia — la única forma de cumplir R2.4.2 y R2.4.3 a la vez sobre la captura. El disparador: **una fila de `fecha_efectiva` vigente con `due_at_utc` vencido y sin `version_entrega` vigente** entra en la cola del trabajo `capturar_versiones`, que corre **cada minuto**, con una **gracia de 60 segundos** para absorber el desfase de relojes (A-101).

**No se persiste ninguna fila de `version_entrega` antes de que el SHA quede resuelto** (RG-024, A-213). El motivo es estructural: si existiera una fila con un estado «programado» ya vigente, el propio disparador —«sin `version_entrega` vigente»— dejaría de encolar la captura, y **R2.4.5 quedaría incumplido en silencio**. Las fases previas a la inserción —resolución del SHA contra el espejo y contra GitHub, espera de presupuesto de API, reintento tras error transitorio— son **fases del trabajo `capturar_versiones` en la máquina de trabajos** (§11 para la mecánica de colas), no valores de `version_entrega.estado`.

El botón **«capturar ahora»** se ofrece sobre la `fecha_efectiva` vencida sin versión vigente, no sobre una fila previa; su endpoint lleva la clave de idempotencia de A-103, de modo que pulsarlo dos veces no captura dos veces. La barra «registrando versiones: 43 de 60» de la línea de entregas (§10) se calcula sobre `fecha_efectiva` vencidas, **no sobre filas de `version_entrega`**.

### 9.6.2 Dos fases, dos claves de idempotencia

El trabajo `capturar_versiones` se divide en dos, con dos claves de idempotencia distintas (RG-024, Q-2.4-26):

| Fase | Trabajo | Clave de idempotencia | Qué produce |
|---|---|---|---|
| 1 — Resolver el SHA | `resolver_sha` | `version:<entrega>:<sujeto>:<corte_epoch>` | Inserta la fila `version_entrega` en un estado terminal, con `tag_estado ∈ {PENDIENTE, NO_APLICA}` |
| 2 — Crear la etiqueta | `crear_etiqueta` | `tag:<entrega>:<sujeto>:<intento>` | Sólo puede mover `CAPTURADA_SIN_TAG → CAPTURADA` y `tag_estado PENDIENTE → {CREADO, CONFLICTO, FALLIDO}` |

Separar las dos fases es lo que permite que un `403` de límite al crear la etiqueta **no impida registrar la evidencia**, que es lo único que R2.4.5 exige (A-213).

**Criterio de tiempo (Q-2.4-27):** SHA registrado dentro de **5 minutos** siguientes al cierre en el percentil 95, **15 minutos** en el peor caso, para un curso de 200 sujetos que cierran a la misma hora. Etiqueta creada dentro de **60 minutos**, sin criterio de percentil, porque es comodidad de navegación y no evidencia (Ley 4). La línea de entregas muestra el progreso en vivo y, cuando `capturada_en - fecha_corte_utc > 15 minutos`, la fila lleva la etiqueta «captura tardía» con el retraso en minutos.

### 9.6.3 `version_entrega.estado`: seis valores terminales, y `tag_estado` como eje aparte

`version_entrega.estado` es un enum cerrado de **seis valores, todos terminales, sin `DEFAULT`** (RG-025, A-213):

| Estado | Etiqueta en pantalla | Significa |
|---|---|---|
| `CAPTURADA` | «Versión registrada» | SHA resuelto y etiqueta creada |
| `CAPTURADA_SIN_TAG` | «Versión registrada (sin etiqueta en GitHub)» | SHA resuelto; la etiqueta está pendiente, en conflicto, falló o no se pudo intentar |
| `SIN_COMMITS` | «Sin commits al cierre» | El repositorio existía y no hay commits contables anteriores al cierre, más allá del inicial. **No es error** |
| `REVISAR` | «Versión registrada, requiere revisión» | El espejo y la fuente de contraste de GitHub discreparon en el SHA de cierre |
| `SIN_REPOSITORIO` | «Sin repositorio al cierre» | El sujeto no tenía repositorio utilizable en la fecha de corte |
| `ERROR` | «Requiere tu acción» | Fallo permanente en la resolución del SHA |

`SUPERSEDIDA` **no es un valor de `estado`**: se expresa con `vigente = false` y `motivo`, de modo que se conserva para siempre que aquella fila fue `CAPTURADA` o `SIN_COMMITS` (R2.4.7, §9.8).

La etiqueta de GitHub es una **segunda enumeración independiente**: `tag_estado ∈ {PENDIENTE, CREADO, CONFLICTO, FALLIDO, NO_APLICA}`, con `tag_motivo` de **siete** valores —`REPOSITORIO_ARCHIVADO`, `LIMITE_API`, `SHA_DISTINTO`, `PERMISO_INSUFICIENTE`, `SIN_COMMITS`, `DESCONOCIDO`, `REPOSITORIO_INACCESIBLE`— y `tag_error` con el **texto literal de GitHub** siempre (A-213, RG-188). `'TAG_OCUPADO'` no es un valor de `tag_error`: es un motivo de la incidencia `VERSION_REVISAR`.

**Invariante escrito por implicaciones, no por equivalencia (RG-025):**

- `estado = CAPTURADA` ⟹ `tag_estado = CREADO`
- `estado = CAPTURADA_SIN_TAG` ⟹ `tag_estado ∈ {PENDIENTE, CONFLICTO, FALLIDO}`
- `estado ∈ {SIN_COMMITS, SIN_REPOSITORIO, ERROR}` ⟹ `tag_estado = NO_APLICA`
- `estado = REVISAR` ⟹ `tag_estado ∈ {CREADO, PENDIENTE, CONFLICTO, FALLIDO}` — `REVISAR` describe una discrepancia de SHA y es ortogonal a la etiqueta

**Dos transiciones posteriores a la inserción, y sólo dos** (RG-026, RG-188): `CAPTURADA_SIN_TAG → CAPTURADA`, cuando la fase 2 crea la etiqueta con éxito; y `CAPTURADA → CAPTURADA_SIN_TAG`, con un único origen declarado —el bloque de verificación diaria de etiquetas y el webhook `delete` con `ref_type = tag`—, porque una etiqueta ya creada puede borrarse o moverse después de la captura. Las dos escriben `estado` y `tag_estado` en la misma sentencia.

### 9.6.4 Selección del commit de cierre: doble fuente, regla escrita

**No se confía en `GET /commits?until=…&per_page=1`**: la documentación no garantiza que `until` sea inclusivo en el segundo exacto, ni que filtre por fecha de *committer*, ni el orden de retorno del endpoint (A-102, Q-2.4-22). El procedimiento, defendible porque no descansa en ninguna semántica no documentada:

1. **Fuente primaria — el espejo propio:** `MAX(fecha_committer) ≤ fecha_corte` sobre la rama por defecto en `commit`, excluyendo `huerfano = true` y el commit inicial del repositorio base.
2. **Fuente de contraste — GitHub:** se pide con `until = corte + 1 segundo` y se hace **selección local** del commit de mayor `committer.date` que cumpla `≤ corte`; nunca se toma «el primero» de la lista. Pedir un segundo por encima del corte y filtrar localmente hace que la inclusividad de `until` deje de importar.
3. **Si coinciden** → el SHA queda resuelto y el estado final lo fija la fase de etiqueta. **Si difieren** → se guardan ambas en `version_entrega.verificacion`, se toma la del espejo, y el estado es `REVISAR` con incidencia visible. **Si no hay ninguno** → `SIN_COMMITS`.
4. Si las 100 candidatas devueltas son todas posteriores al corte, se sigue `Link` hasta 5 páginas; agotadas, manda el espejo con `REVISAR`.

**La regla se declara por escrito y se muestra en la interfaz:** «último commit cuya fecha de committer es anterior o igual a la fecha efectiva de cierre, en UTC» — inclusiva en el segundo exacto. Se usa **fecha de committer**, no de autor, porque es la única marca que llega por las dos vías de ingesta (webhook y reconciliación); la fecha de push no se usa porque el único campo que la daba, `pushedDate` de GraphQL, está deprecado y retirado (Q-2.4-23).

**Rama:** se resuelve siempre sobre `repositorio.rama_por_defecto`, leída de la respuesta de creación y nunca supuesta `main` (A-102, §6). Si hay commits contables fuera de esa rama dentro de la ventana de la entrega, la versión se inserta con `advertencias += HAY_COMMITS_EN_OTRAS_RAMAS` (Q-2.4-21).

### 9.6.5 `SIN_COMMITS`: dos motivos, nunca error

| `motivo` | Cuándo | Etiqueta |
|---|---|---|
| `REPOSITORIO_VACIO` | El repositorio no tiene ningún commit | «Repositorio vacío al cierre» |
| `SOLO_COMMIT_INICIAL` | El único commit anterior al corte es el andamiaje del repositorio base | «Solo el contenido inicial: el estudiante no hizo ningún commit» |

El commit inicial se identifica por `repositorio.commit_inicial_sha` (persistido por §8 al observar el contenido tras `generate`); si es nulo, se reconoce retroactivamente cuando cumple las tres condiciones: `n_padres = 0`, `fecha_committer ≤ repositorio.listo_en`, y su autor no resuelve a ningún mapeo vigente del curso. **Nunca se adivina por el mensaje del commit ni por el nombre del autor** (Q-2.4-29). No se crea etiqueta sobre `SIN_COMMITS`: `tag_estado = NO_APLICA`, `tag_motivo = SIN_COMMITS`.

### 9.6.6 `SIN_REPOSITORIO`: nunca «sin entrega»

| `motivo` | Cuándo |
|---|---|
| `SIN_REPOSITORIO_AL_CIERRE` | El sujeto existía al cierre pero su repositorio no estaba en estado utilizable |
| `SUJETO_MATERIALIZADO_TRAS_EL_CIERRE` | El sujeto no existía al cierre: matrícula nueva, grupo nuevo, u override que le dio visibilidad después |

**No se consulta a GitHub**: en la fecha de corte ese repositorio no existía y la llamada no puede hacerse. La etiqueta visible es **«Sin repositorio al cierre — alta posterior a la fecha»**, y **nunca «sin entrega»**: afirmar que el estudiante no entregó nada cuando lo que ocurrió es que la aplicación no le dio repositorio a tiempo es una afirmación falsa con consecuencia de nota (RG-027).

**Cuando el repositorio aparece más tarde no se captura sola.** Al alcanzar el estado listo (§8), se abre incidencia `VERSION_REVISAR` sobre ese `(entrega, sujeto)` con la acción sugerida «captura ahora la versión o fija una fecha de corte propia»; el botón «capturar ahora» de §9.8.6 la resuelve en un clic. Una captura automática con `until` histórico produciría con certeza un `SIN_COMMITS` indistinguible de un estudiante que no trabajó, que es exactamente el falso «sin entrega» que se evita (RG-027, Q-2.4-41).

### 9.6.7 Entrega vinculada con la fecha ya vencida: confirmación explícita, nunca captura automática

Si al vincular una entrega su fecha ya pasó, la entrega nace en `estado_validacion = 'VINCULADA_TRAS_EL_CIERRE'` y **no se captura nada**. La pantalla muestra, calculado sobre el espejo y sin llamar a GitHub: cuántos sujetos hay, cuántos tienen repositorio, y para cada uno qué SHA se registraría con esa fecha de corte. El botón dice **«registrar ahora las versiones con la fecha de cierre de Canvas»**; al pulsarlo, encola la captura de todos los sujetos con `origen_captura = MANUAL_AHORA` y el actor registrado (RG-019, Q-2.4-44, §9.8.6). Mientras no se pulse, la entrega funciona con normalidad para todo lo demás y la tarjeta muestra «versiones no registradas: la fecha de cierre ya había pasado al vincular».

Capturar 200 repositorios como efecto colateral de pulsar «vincular» sería un efecto invisible; no capturar nunca dejaría R2.4.5 incumplido para esa entrega de forma permanente. La confirmación explícita es la única opción que cumple el requisito sin sorprender a nadie.

### 9.6.8 Cuando el trabajo de captura entró en servicio después de que la fecha ya venció

Distinto del caso anterior: una entrega **vinculada a tiempo**, cuya fecha vence **mientras el trabajo `capturar_versiones` todavía no está en servicio** (el caso del arranque del sistema, análogo al relleno histórico del 16 al 23 de septiembre de §10). El sistema la captura solo, en cuanto el trabajo entra en servicio, **con el corte original**: `version_entrega.motivo = 'CAPTURA_TARDIA_POR_ALCANCE'`, con advertencia visible para el corrector — «versión resuelta después del cierre, con el historial recuperado desde GitHub; la fecha de corte es la original». **No se presenta jamás como una captura ocurrida al cierre** (RG-154, RG-195).

Los dos casos no se solapan: `CAPTURA_TARDIA_POR_ALCANCE` describe una entrega cuya fecha venció mientras el trabajo de captura no estaba en servicio; `VINCULADA_TRAS_EL_CIERRE` describe una entrega que se vinculó con la fecha ya pasada, y su captura exige un acto humano.

### Criterios de aceptación de §9.6

1. **CA-9.6-01.** Ninguna fila de `version_entrega` existe para un `(entrega, sujeto)` cuya `fecha_efectiva` vigente no esté vencida.
2. **CA-9.6-02.** Un cierre masivo de 200 sujetos a la misma hora produce SHA resuelto para el percentil 95 dentro de 5 minutos, medible contra `capturada_en - fecha_corte_utc`.
3. **CA-9.6-03.** Forzar una discrepancia entre el espejo y GitHub en el commit de cierre produce `estado = REVISAR` con ambos SHA guardados en `verificacion` e incidencia visible.
4. **CA-9.6-04.** Un repositorio sin commits del estudiante (sólo el commit inicial) produce `estado = SIN_COMMITS`, `motivo = SOLO_COMMIT_INICIAL`, sin etiqueta creada.
5. **CA-9.6-05.** Vincular una entrega cuya fecha ya venció no produce ninguna fila `version_entrega` hasta que un profesor o ayudante con `tarea.administrar` pulsa «registrar ahora».
6. **CA-9.6-06.** Un `403` de límite de API al crear la etiqueta dentro de una captura deja la fila en `CAPTURADA_SIN_TAG` con `tag_motivo = LIMITE_API`, y el SHA queda registrado igual.
7. **CA-9.6-07.** Borrar manualmente la etiqueta de una versión `CAPTURADA` en GitHub produce, en el ciclo de verificación siguiente, la transición `CAPTURADA → CAPTURADA_SIN_TAG` con `tag_estado = PENDIENTE`, seguida de su recreación automática.

---

## 9.7 Independencia entre entregas de una misma tarea (R2.4.6)

### 9.7.1 Unicidad y por qué basta con una clave compuesta

Las versiones capturadas cuelgan de `(entrega, sujeto)`, nunca de `tarea` ni de `repositorio` a secas (A-081). La unicidad de base es **`(entrega_id, sujeto_id, intento)`**, más el índice único parcial **`(entrega_id, sujeto_id) WHERE vigente`**: dos entregas de la misma tarea son filas completamente distintas e independientes, cada una con su propio `intento` desde 1 (RG-025, A-084).

### 9.7.2 El nombre del tag hace la independencia visible

El tag —comodidad de navegación, nunca la evidencia normativa (Ley 4)— se nombra `entrega/<orden>-<entrega.slug>/v<n>`, donde `<n>` es exactamente `version_entrega.intento`, por `(entrega, sujeto)` (A-104, A-172, §6 para la mecánica HTTP de creación). Ejemplo completo, calculable sin consultar nada: en una tarea con «Avance parcial» (`orden` 1) y «Entrega final» (`orden` 2), los tags del repositorio de un mismo sujeto son `entrega/1-avance-parcial/v1` y `entrega/2-entrega-final/v1`; si la fecha final se adelanta y se recaptura, aparece `entrega/2-entrega-final/v2` **junto al v1**, no en su lugar.

### 9.7.3 Mismo SHA en dos entregas, y fechas cruzadas

Ninguno de los dos casos es un error del sistema: son configuraciones que Canvas admite y que el algoritmo de §9.3 produce legítimamente (Q-2.4-33).

| Caso | Tratamiento |
|---|---|
| **El mismo SHA se captura para dos entregas consecutivas** | Legal por construcción: la unicidad es por `(entrega_id, sujeto_id, intento)`, no por SHA. La segunda fila lleva `advertencias += SIN_CAMBIOS_RESPECTO_A_LA_ANTERIOR`; en pantalla, «sin cambios respecto a *Avance parcial*» sustituye al botón de comparación. No se bloquea, no abre incidencia, no se comunica al estudiante |
| **Fechas cruzadas para un sujeto** (la extensión de la entrega 1 cae después del cierre de la entrega 2) | Se acepta, se alerta, no se bloquea. Incidencia `DISCREPANCIA_FECHAS`, ADVERTENCIA, con distintivo «fechas cruzadas» en la ficha del sujeto. **Toda la interfaz ordena las entregas por `orden`, nunca por fecha** |

**«La entrega anterior», definida por sujeto (A-173), ampliada para el caso cruzado (Q-2.4-33):** la entrega de la misma tarea con el mayor `orden` estrictamente menor que además tenga fecha efectiva vigente y no nula para ese sujeto **y** cuyo `due_at_utc` sea estrictamente anterior al de la entrega actual para ese sujeto. Si no lo cumple, se sigue bajando por `orden` hasta encontrar una que sí lo cumpla o hasta agotar la lista. Esta es la misma función de dominio que usa §10 para las ventanas de actividad, el enlace `compare` de §9.9 y la detección de SHA repetido de esta sección: **una sola implementación**, no tres.

### 9.7.4 Cambio de grupo entre entregas de la misma tarea

Si un estudiante pasa del grupo G1 al G2 entre la parcial y la final, la versión de la parcial queda registrada en el repositorio de G1 y la de la final en el de G2: son dos sujetos distintos de la misma tarea, y ninguna de las dos versiones se pierde (A-081, Q-2.4-42). Esto no rompe R2.3.4, que exige un conjunto de repositorios por tarea, no una asignación fija de personas a repositorio.

**El cambio no se bloquea**; abre incidencia `CAMBIO_DE_GRUPO_ENTRE_ENTREGAS`, ADVERTENCIA, con los dos grupos y la fecha de detección. En el panel de corrección de la entrega final de G2 aparece una banda informativa: «*<nombre>* se incorporó a este grupo el DD-MM-AAAA; su trabajo de *Avance parcial* está en `<repositorio de G1>`», con enlace sujeto a las mismas condiciones de acceso de §9.9. La ficha del estudiante (§7) lista todas sus entregas de la tarea con su sujeto y repositorio de origen.

### Criterios de aceptación de §9.7

1. **CA-9.7-01.** Las versiones de la entrega parcial y de la entrega final de un mismo sujeto son dos filas con `intento = 1` cada una, y una recaptura de la final no toca el `intento` de la parcial.
2. **CA-9.7-02.** Los tags de dos entregas de la misma tarea sobre el mismo repositorio nunca colisionan de nombre.
3. **CA-9.7-03.** Capturar el mismo SHA para dos entregas consecutivas no abre incidencia y marca la segunda fila con `SIN_CAMBIOS_RESPECTO_A_LA_ANTERIOR`.
4. **CA-9.7-04.** Un estudiante que cambia de grupo entre la parcial y la final aparece en la ficha del estudiante con sus dos entregas y sus dos repositorios de origen.

---

## 9.8 Inmutabilidad de la versión registrada ante actividad posterior (R2.4.7)

### 9.8.1 Qué es evidencia y qué es mutable

**La fila nunca se borra** (A-030). De sus columnas, **una lista cerrada es mutable** y todo lo demás es evidencia inmutable (RG-026):

| Mutables | Inmutables (evidencia) |
|---|---|
| `vigente` (transición única `true → false`) | `commit_sha`, `commit_tree_sha`, `commit_fecha_autor`, `commit_fecha_committer`, `commit_mensaje`, `fecha_corte_utc`, `rama`, `intento`, `capturada_en`, `tag_nombre`, `integrantes` (RG-028), y todo el bloque de contexto copiado (§9.9.1) |
| `motivo` | — |
| `tag_estado`, `tag_motivo`, `tag_error`, `tag_creado` | — |
| `advertencias` | — |
| `estado` (sólo en las dos transiciones de §9.6.3) | — |

**Una función única de transición rechaza cualquier escritura sobre una columna que no esté en esta lista**, verificado por prueba de arquitectura.

### 9.8.2 Recaptura ante cambio de fecha: R2.4.4 y R2.4.7 conviven

Cuando la fecha efectiva de una entrega cambia después de tener versión capturada, la aplicación actúa automáticamente, sin pedir confirmación, y de forma simétrica (A-103, Q-2.4-37):

| Situación | Qué ocurre |
|---|---|
| La fecha **se adelanta** a un instante ya pasado, con versión ya capturada | Se captura de nuevo con la fecha nueva; la anterior queda `vigente = false`, `motivo = 'FECHA_ADELANTADA'`; **ambas quedan visibles** |
| La fecha **se retrasa** | La captura existente queda `vigente = false`, `motivo = 'FECHA_EXTENDIDA'`; se programa una captura nueva para el instante nuevo |
| La fecha cambia **antes** de que la captura ocurra | Se reprograma; no hay fila que superseder |

**Nada se descarta nunca.** La fila anterior conserva su SHA, su fecha de corte, su bloque denormalizado y su etiqueta `v1`, que sigue existiendo en GitHub apuntando al SHA anterior (A-172). La clave de idempotencia del trabajo de captura incluye la fecha de corte en epoch: la misma fecha nunca captura dos veces y una fecha distinta siempre captura de nuevo.

**Quién aprueba: nadie.** R2.4.4 exige mantener las fechas actualizadas; pedir confirmación humana convertiría un requisito automático en una cola de aprobaciones. Lo que sí queda registrado es `canvas_override_id` y `override_titulo` (bloque copiado, §9.9.1) y el instante en que la aplicación lo detectó, por la huella de §9.4.

**Interacción con una corrección en curso:**

| Estado de `correccion` al recapturar | Qué ocurre |
|---|---|
| `SIN_CORRECTOR` o `ASIGNADA` | Nada especial; el corrector verá la versión nueva al abrir |
| `EN_CURSO` o `LISTA_PARA_PUBLICAR` | `correccion.version_desactualizada = true`; banda ámbar persistente con enlace de comparación y botón «adoptar la versión nueva» |
| `PUBLICADA` o `PUBLICADA_CON_ADVERTENCIA` | **La nota publicada no se modifica jamás de forma automática.** Se abre incidencia `VERSION_REVISAR`; el panel ofrece «reabrir la corrección» (§12) |

### 9.8.3 Commits posteriores al cierre: se muestran, no se registran de nuevo

Se registra **una sola versión por entrega**, la del cierre; no existe un segundo snapshot a `lock_at` (A-101, Q-2.4-34). El atraso se muestra como indicador **derivado del espejo, sin coste de API y sin fila nueva**: `commits_posteriores_al_cierre` (commits contables con `fecha_committer > fecha_corte_utc` en la rama de la versión), `ultimo_commit_posterior_en`, y un enlace `…/compare/{commit_sha}...{rama}`. Frase exacta: «N commits después del cierre; no forman parte de la versión corregida». **Hacia Canvas no se escribe ningún estado de atraso**: la publicación de nota sigue enviando `late_policy_status=none` (§12, A-139/A-140).

### 9.8.4 Manipulación tras el cierre: push retrodatado e historia reescrita

Se registra, se conserva, y se alerta al corrector. **Nunca se recaptura, nunca se excluyen commits del snapshot, nunca se notifica al estudiante de forma automática** (Q-2.4-45):

| Señal | Cómo se detecta | Marca |
|---|---|---|
| Push posterior al cierre con commits de fecha anterior | `commit.fecha_committer ≤ fecha_corte_utc` de una versión vigente **y** el `evento_push` que lo trajo tiene `recibido_en > fecha_corte_utc` | `commit.retrodatado = true`; `advertencias += PUSH_POSTERIOR_CON_FECHA_ANTERIOR` |
| Reescritura de historia sobre la rama de la versión | `compare` devuelve `diverged` (§6); los commits que desaparecen se marcan `huerfano = true` y **no se borran** | `advertencias += HISTORIA_REESCRITA_TRAS_EL_CIERRE` |

La versión es inmutable (A-085) y su SHA apunta a un objeto Git inmutable: los commits retrodatados no estaban en ese árbol en el momento de la captura y no entran ahora. Recapturar los metería dentro, que es exactamente lo contrario de lo que R2.4.7 pide. Tras detectar una reescritura, se comprueba que el SHA siga alcanzable (`GET /commits/{sha}`); si no, se eleva a prioridad la recreación de la etiqueta y se añade `SHA_PUEDE_SER_INALCANZABLE`. Se añade el tipo de incidencia **`MANIPULACION_TRAS_CIERRE`**, ADVERTENCIA — no «fraude», porque existen causas legítimas (`rebase`, `amend`, un commit antiguo empujado tarde) y nombrar un estado con una causa que no se puede probar sería mentir en pantalla (mismo criterio de A-100).

### 9.8.5 Etiqueta borrada o movida: se detecta y se recrea, nunca en silencio

| Resultado de la verificación diaria | Qué se hace |
|---|---|
| `200` con el mismo SHA | Nada |
| `404` (la etiqueta ya no existe) | **Se recrea** desde el SHA guardado; `tag_estado` vuelve a `CREADO`; se abre incidencia `TAG_ALTERADO` |
| `200` con otro SHA (la etiqueta se movió) | **No se sobrescribe jamás**: `tag_estado = CONFLICTO`, `tag_motivo = SHA_DISTINTO`, incidencia `TAG_ALTERADO` |

Detección por dos caminos: el webhook `delete` con `ref_type = tag` cuyo `ref` casa con el patrón `entrega/*`, y el barrido diario que hace, para cada versión vigente con `tag_estado = CREADO`, la misma lectura que ya prescribe la verificación previa a crear (A-115 garantía 3) (Q-2.4-46). No se implementa protección de rama ni *ruleset* de tags: no existen para repositorios privados en el plan gratuito de la organización (`Q-infraestructura-22`, §14); es precisamente el origen de la Ley 4 y esta decisión es su consecuencia operativa.

### 9.8.6 Repositorio archivado

**La aplicación no archiva ni desarchiva nunca por su cuenta** (§8, A-168). Si un repositorio se archiva —sólo por acción explícita de un profesor, o porque alguien lo archivó en GitHub— antes de una captura pendiente: se registra el SHA y **no se desarchiva**; la fila queda `CAPTURADA_SIN_TAG` con `tag_estado = FALLIDO`, `tag_motivo = REPOSITORIO_ARCHIVADO`, e incidencia `VERSION_REVISAR` con la acción sugerida «desarchiva el repositorio y pulsa *reintentar etiqueta*», habilitada sólo cuando llega el webhook `repository`/`unarchived` (Q-2.4-47, A-101). Las versiones ya capturadas sobre un repositorio que se archiva después **no se tocan, no se marcan irrecuperables y no cambian de estado**: son inmutables y la evidencia normativa es el `commit_sha` en la base propia, respaldada a diario (A-230, Ley 4, A-016).

### 9.8.7 Repositorio inaccesible

Cuando un repositorio pasa a `INACCESIBLE` (§8), sus filas de `version_entrega` **no se modifican**. La incidencia es informativa, `REPOSITORIO_INACCESIBLE`, una por repositorio y no una por versión. El corrector puede seguir corrigiendo y publicar la nota: la calificación depende del SHA capturado y del bloque denormalizado de la propia fila, no de que GitHub siga sirviendo el repositorio (A-230). Si la corrección no llegó a `EN_CURSO` antes de que el repositorio se volviera inaccesible, la publicación exige marcar «califico sin haber podido abrir el código de esta versión», registrado en `bitacora` con la acción `CALIFICADA_SIN_CODIGO` (§12).

### 9.8.8 Acciones manuales sobre la versión: tres, y sólo tres

Ninguna acción manual borra ni modifica la versión automática: las tres crean una fila nueva con `intento = anterior + 1` y dejan la anterior `vigente = false` (Q-2.4-38):

| # | Acción | Quién | Qué hace | `origen_captura` |
|---|---|---|---|---|
| 1 | **«Capturar ahora»** | `tarea.administrar` | Adelanta el trabajo sin cambiar la fecha de corte. Sólo disponible sin versión vigente | `MANUAL_AHORA` |
| 2 | **«Recapturar con otra fecha de corte»** | Sólo rol `PROFESOR` | Crea `intento + 1` con la fecha indicada, pasada y posterior a la creación del repositorio | `MANUAL_FECHA` |
| 3 | **«Fijar esta versión en un commit concreto»** | Sólo rol `PROFESOR` | Crea `intento + 1` con el SHA indicado, verificado antes contra GitHub; si no pertenece al repositorio, se rechaza | `MANUAL_SHA` |

**Por qué 2 y 3 son de rol y no de permiso concedible:** fijar a mano qué código se corrige es la única acción del sistema que puede decidir la nota de un estudiante sin que quede huella en Canvas; se reserva al rol `PROFESOR` sin abrir un octavo permiso, con la comprobación en el servidor —«ocultar el botón no es autorizar»— y no en la interfaz (§2 para el catálogo de permisos).

**Auditoría obligatoria en las tres:** `version_entrega.origen_captura`, `creada_por_usuario_id` y `motivo_manual` (texto libre obligatorio, mínimo 10 caracteres, pedido en un diálogo que no se puede saltar), más una fila en `bitacora` con `antes`/`después`. La fila lleva el distintivo «manual» en toda vista donde aparezca. Un `CHECK` impide que `origen_captura ≠ AUTOMATICA` conviva con `creada_por_usuario_id` nulo o `motivo_manual` vacío.

### 9.8.9 Estudiante retirado y sujeto grupal sin integrantes

Se captura **siempre que exista repositorio**, cualquiera que sea el estado de la matrícula al cierre; la versión se conserva para siempre, marcada con `advertencias += SUJETO_RETIRADO` cuando el `estado_sujeto_al_cierre` copiado no es `ACTIVO` ni `INVITADO` (Q-2.4-40, A-030, A-095). Se excluye de los agregados de §10 y de §11, con la línea «N sujetos retirados, excluidos de estos números» — nunca desaparece en silencio (A-164 paso 3). No se asigna automáticamente a un corrector en el reparto equitativo, pero sí es asignable a mano (§12). Si un sujeto grupal se queda sin ningún integrante `accepted`, se desactiva con `motivo_desactivacion = GRUPO_SIN_ACEPTADOS` (§7) y su repositorio pasa a `FUERA_DE_ALCANCE` conservándolo todo; las versiones ya capturadas siguen siendo válidas y visibles.

### Criterios de aceptación de §9.8

1. **CA-9.8-01.** Un intento de `UPDATE` sobre `commit_sha`, `commit_fecha_committer` o `fecha_corte_utc` de una fila `version_entrega` cualquiera falla, garantizado por la función única de transición.
2. **CA-9.8-02.** Adelantar la fecha efectiva de una entrega ya capturada produce una fila nueva `vigente = true` con `motivo = 'FECHA_ADELANTADA'` y dos filas visibles en la ficha de la entrega.
3. **CA-9.8-03.** Un `push --force` que descarte tres commits deja las tres filas en `commit` con `huerfano = true`, no recaptura ninguna versión, y añade `HISTORIA_REESCRITA_TRAS_EL_CIERRE` a la advertencia de la versión afectada si alguno estaba antes del corte.
4. **CA-9.8-04.** Borrar la etiqueta de una versión `CAPTURADA` produce su recreación automática dentro de 24 horas y una incidencia `TAG_ALTERADO`.
5. **CA-9.8-05.** Usar la acción «fijar esta versión en un commit concreto» con un SHA de otro repositorio es rechazada antes de escribir nada.
6. **CA-9.8-06.** Un estudiante retirado tras el cierre de la parcial conserva su versión de la parcial, visible y correcta, y queda excluido del denominador de la línea de entregas con la nota «N retirados excluidos».

---

## 9.9 Acceso directo a la versión para profesores y ayudantes (R2.4.8)

### 9.9.1 Todo lo necesario vive en la propia fila («FK para navegar, copia para leer»)

`version_entrega` copia, en el momento de la captura, un **bloque de contexto congelado** además de la evidencia: `github_repo_id`, `repositorio_full_name`, `org_login`, `rama`, `installation_id` vigente; `sujeto_tipo`, `sujeto_etiqueta`, `estado_sujeto_al_cierre`; `seccion_nombre`, `canvas_section_id`; `origen` de la fecha, `canvas_override_id`, `override_titulo`, `ambigua`; y, para el grupo, `integrantes jsonb` (RG-028, ya citado). Las claves foráneas `entrega_id`, `sujeto_id`, `repositorio_id`, todas sin `ON DELETE CASCADE`, permiten navegar al dato vivo cuando existe; la copia hace la fila legible y correcta **aunque el origen desaparezca** —un override borrado en Canvas, un grupo renombrado, un repositorio renombrado— porque A-030 prohíbe borrar y ninguna de esas desapariciones puede volver ilegible una versión ya registrada (Q-2.4-30). Es la Ley 2 llevada a sus consecuencias: el origen no siempre es de la aplicación.

### 9.9.2 El enlace: URL por SHA, no por etiqueta

El acceso directo es un enlace a GitHub, `https://github.com/{org}/{repo}/tree/{sha}`, construido desde el bloque copiado y **sin depender de que la etiqueta exista** (A-104, Q-2.4-31). Abre porque el equipo docente tiene lectura sobre todos los repositorios del curso vía el equipo `docentes` de la organización, con acceso concedido antes de que el repositorio llegue a `OPERATIVO` (§8, A-163). La pantalla comprueba `acceso_docente_repositorio` **antes de pintar el enlace** (§12, A-136):

| Estado del acceso docente | Qué se muestra |
|---|---|
| `CONCEDIDO` | Enlace con botón de copiado |
| `PENDIENTE` | «Preparando tu acceso al repositorio» con la hora del próximo intento |
| `ERROR` | Motivo literal de GitHub y botón de reintento |
| Repositorio `SHA_NO_ALCANZABLE` (404/422 al pedir el commit) | No se pinta el enlace; se muestran los metadatos persistidos y «el commit ya no es accesible en GitHub; probablemente hubo un `push --force`. La versión registrada y sus datos se conservan» |
| Repositorio `INACCESIBLE` | «versión registrada; el repositorio ya no está accesible en GitHub desde *fecha*, por *motivo*» |

**Entregar un enlace roto es peor que decir por qué no está listo.**

### 9.9.3 Comparación entre versiones

Junto al enlace por SHA, si hay una entrega anterior (definida por §9.7.3), la interfaz ofrece `…/compare/{sha_anterior}...{sha_actual}` — «para un corrector, ver qué cambió entre la parcial y la final es más útil que ver el árbol completo» (A-104, Q-2.4-32). Para la primera entrega, o cuando no aplica la anterior, se ofrece la comparación contra `repositorio.commit_inicial_sha` con la etiqueta «desde el inicio del repositorio»; si ese SHA es nulo, no se ofrece comparación y se muestra «sin línea base registrada para este repositorio» — no se inventa una base, por el mismo criterio con el que §9.3 no inventa una fecha.

### 9.9.4 Descarga y auditoría de apertura

Botón **«descargar esta versión»**: enlace a `https://github.com/{org}/{repo}/archive/{sha}.zip`. **La aplicación no sirve el archivo, no lo descarga y no lo almacena** — coherente con que no archiva código en ningún punto de este capítulo ni de §8 (Q-2.4-31). No se define ningún permiso nuevo: quien puede abrir el árbol ya puede descargarlo desde GitHub.

Los tres enlaces —árbol, comparación, descarga— **no apuntan directo a GitHub desde el HTML**: pasan por un endpoint auditado que comprueba el permiso, escribe en `bitacora` quién abrió qué versión y cuándo, y responde con una redirección. Coste: cero llamadas externas; beneficio: responder «quién revisó esta entrega y cuándo» sin abrir GitHub (Q-2.4-31).

### Criterios de aceptación de §9.9

1. **CA-9.9-01.** Abrir el enlace de una versión con `acceso_docente_repositorio = CONCEDIDO` redirige a `…/tree/{sha}` y deja una fila en `bitacora` con la acción de apertura, el actor y la versión.
2. **CA-9.9-02.** Abrir el enlace de una versión cuyo repositorio tiene `acceso_docente_repositorio = PENDIENTE` no produce un enlace roto ni una llamada a GitHub; muestra el motivo y la hora del próximo intento.
3. **CA-9.9-03.** El enlace de comparación de la entrega final usa el SHA de la versión vigente de la entrega inmediatamente anterior **para ese sujeto**, no de la entrega con `orden` numéricamente anterior sin más.
4. **CA-9.9-04.** Ningún endpoint de este capítulo descarga ni almacena contenido de un repositorio de estudiante.

---

## 9.10 Integridad ante manipulación y fallos de infraestructura

### 9.10.1 Tres capas de blindaje, ni una más (Ley 4)

| Capa | Qué es | Rol |
|---|---|---|
| `version_entrega.commit_sha` (base propia) | Fila inmutable, *append-only* | **Es la evidencia normativa** |
| Respaldo diario cifrado (`pg_dump`, AES-256-GCM, retención 14 días) | Trabajo nocturno de §14 | Impide que la base sea punto único de fallo de toda la evidencia de R2.4.5–R2.4.7 (A-016) |
| Tag ligero en GitHub | `POST /git/refs` (§6) | Comodidad de navegación; mantiene el commit alcanzable mientras nadie lo borre |

**No se implementan**: protección de rama o *ruleset* de tags (no disponible en repositorios privados de un plan gratuito de organización), ni archivo/*mirror* del código (la aplicación no descarga ni archiva contenido, entrega enlaces — §9.9.4). Ambas exclusiones están citadas en §9.8.5.

### 9.10.2 Verificación diaria de alcanzabilidad

El barrido nocturno de actividad (§10) comprueba, para cada `version_entrega` vigente de cada repositorio, que el SHA siga siendo legible y, si `tag_creado = true`, que la etiqueta siga apuntando al mismo SHA. **La comprobación no modifica la fila** de evidencia: escribe la incidencia `VERSION_REVISAR` con `detalle.motivo ∈ {SHA_NO_ALCANZABLE, TAG_BORRADO, TAG_MOVIDO, REPOSITORIO_INACCESIBLE}`, ya cubierta en §9.8.4 y §9.8.5.

### 9.10.3 Canvas caído en el momento de capturar: se captura igual

**Lo que no depende de Canvas no se detiene**, y la captura de versiones es uno de esos procesos: la fecha ya está persistida y materializada (§9.4), así que R2.4.5 no puede depender de que Canvas esté accesible en ese instante (A-036 punto 4, Q-2.4-48). Umbral de antigüedad de `fecha_efectiva.calculada_en` en el momento de capturar:

| Antigüedad | Qué ocurre |
|---|---|
| ≤ 6 horas | Captura normal, sin marca |
| > 6 horas | Captura; `advertencias += FECHAS_POSIBLEMENTE_DESACTUALIZADAS`, visible en la ficha y en la bandeja del corrector |
| > 48 horas | Captura; la misma advertencia **y** incidencia `VERSION_REVISAR` con la acción sugerida «restablece la credencial de Canvas y revisa esta fecha» |

Seis horas son 72 ciclos fallidos consecutivos del sincronizador de 5 minutos — un fallo sostenido, no un hipo. **El umbral no es configurable**: no es una preferencia pedagógica, es un criterio de fiabilidad de la evidencia.

### 9.10.4 GitHub inaccesible en el momento de capturar: se suspende y reintenta, nunca falla

Sin token de instalación no hay forma de leer el SHA: la fila queda en fase de trabajo `ERROR_TRANSITORIO` con `motivo = GITHUB_SIN_ACCESO`, clasificada **BLOQUEANTE** (no TRANSITORIO): no se reintenta en bucle, se reevalúa cada 30 minutos o cuando cambia la condición, y **no consume los 8 reintentos** normales del trabajo — agotarlos convertiría un problema de infraestructura en un estado terminal del trabajo de un estudiante (Q-2.4-48). Cuando GitHub vuelve, la captura se ejecuta con `until` histórico y el resultado es correcto, porque el repositorio y su historia existían en el instante del cierre — la diferencia exacta con §9.6.6, donde el repositorio no existía y capturar con fecha histórica produciría un falso «sin entrega». La fila lleva `advertencias += CAPTURA_DIFERIDA_POR_GITHUB` y la etiqueta «captura tardía» de §9.6.2.

**Nunca se bloquea la entrega esperando intervención humana**, en ninguno de los dos casos: bloquear significaría que una credencial revocada un viernes deja sin evidencia todo un fin de semana de cierres.

### 9.10.5 Contenido que el snapshot no puede representar del todo

Al capturar se comprueba, con coste acotado (1 a 4 peticiones, sin descargar nada), la existencia de `.gitattributes` y `.gitmodules` en el árbol del commit (A-101, Q-2.4-49):

| Advertencia | Texto exacto |
|---|---|
| `USA_GIT_LFS` (sólo si `.gitattributes` declara `filter=lfs`) | «este repositorio usa Git LFS: si descargas el `.zip`, los archivos grandes llegarán como punteros de texto, no como el binario. Clona el repositorio si necesitas su contenido» |
| `TIENE_SUBMODULOS` | «este repositorio declara submódulos (*lista*): su código vive en otros repositorios y puede no estar en lo que ves» |
| `ARBOL_TRUNCADO` | «el árbol de este commit es muy grande y la comprobación de contenido fue parcial» |

Son banderas informativas que **no cambian el `estado`** de la versión: sigue siendo `CAPTURADA`. La prevención se hace en el mensaje de invitación del estudiante (§8) con una línea fija sobre no usar LFS ni submódulos.

### Criterios de aceptación de §9.10

1. **CA-9.10-01.** Revocar la credencial de Canvas y forzar un cierre no impide que `capturar_versiones` registre el SHA; la fila lleva `FECHAS_POSIBLEMENTE_DESACTUALIZADAS` si la fecha lleva más de 6 horas sin refrescarse.
2. **CA-9.10-02.** Simular una instalación de GitHub suspendida en el momento de un cierre deja la fila en fase `ERROR_TRANSITORIO` con `motivo = GITHUB_SIN_ACCESO`, reevaluada cada 30 minutos, sin consumir los 8 reintentos normales.
3. **CA-9.10-03.** Un repositorio con `.gitmodules` en el commit de cierre produce `advertencias` con `TIENE_SUBMODULOS` sin cambiar `estado`.
4. **CA-9.10-04.** El barrido diario de verificación de alcanzabilidad no ejecuta jamás un `UPDATE` sobre `commit_sha`, `fecha_corte_utc` ni ninguna columna de la lista de evidencia inmutable.

---

## 9.11 Catálogos cerrados de este capítulo

| Columna | Valores |
|---|---|
| `fecha_efectiva.origen` | `BASE`, `SECCION`, `GRUPO`, `ADHOC` (citado de §7) |
| `fecha_efectiva.estado` | `VIGENTE`, `SUPERSEDIDA` |
| `entrega.estado_validacion` | `VIGENTE`, `VINCULADA_TRAS_EL_CIERRE`, `ELIMINADA_EN_CANVAS`, `EXCLUIDA` |
| `entrega.advertencias` | `LOCK_ANTES_DE_DUE`, `UNLOCK_DESPUES_DE_DUE`, `FINAL_ANTES_QUE_PARCIAL`, `DOS_ENTREGAS_MISMA_FECHA` |
| `version_entrega.estado` | `CAPTURADA`, `CAPTURADA_SIN_TAG`, `SIN_COMMITS`, `REVISAR`, `SIN_REPOSITORIO`, `ERROR` |
| `version_entrega.motivo` | `SIN_REPOSITORIO_AL_CIERRE`, `SUJETO_MATERIALIZADO_TRAS_EL_CIERRE`, `FECHA_ADELANTADA`, `FECHA_EXTENDIDA`, `CAPTURA_TARDIA_POR_ALCANCE` |
| `version_entrega.tag_estado` | `PENDIENTE`, `CREADO`, `CONFLICTO`, `FALLIDO`, `NO_APLICA` |
| `version_entrega.tag_motivo` | `REPOSITORIO_ARCHIVADO`, `LIMITE_API`, `SHA_DISTINTO`, `PERMISO_INSUFICIENTE`, `SIN_COMMITS`, `DESCONOCIDO`, `REPOSITORIO_INACCESIBLE` |
| `version_entrega.origen_captura` | `AUTOMATICA`, `MANUAL_AHORA`, `MANUAL_FECHA`, `MANUAL_SHA` |
| `version_entrega.advertencias` (texto libre sobre catálogo cerrado) | `HAY_COMMITS_EN_OTRAS_RAMAS`, `SIN_CAMBIOS_RESPECTO_A_LA_ANTERIOR`, `SUJETO_RETIRADO`, `PUSH_POSTERIOR_CON_FECHA_ANTERIOR`, `HISTORIA_REESCRITA_TRAS_EL_CIERRE`, `SHA_PUEDE_SER_INALCANZABLE`, `FECHAS_POSIBLEMENTE_DESACTUALIZADAS`, `CAPTURA_DIFERIDA_POR_GITHUB`, `USA_GIT_LFS`, `TIENE_SUBMODULOS`, `ARBOL_TRUNCADO` |
| Tipos de incidencia de este capítulo | `DISCREPANCIA_FECHAS`, `OVERRIDE_NO_INTERPRETABLE`, `VERSION_REVISAR`, `TAG_ALTERADO`, `MANIPULACION_TRAS_CIERRE`, `ENTREGA_ELIMINADA_EN_CANVAS`, `CAMBIO_DE_GRUPO_ENTRE_ENTREGAS` (catálogo completo de incidencias en §11) |

Ningún código nuevo de estado, motivo o incidencia se usa fuera de estas listas hasta que la carta de arquitectura incorpore la enmienda correspondiente (RG-190, citado de §7).

---

## 9.12 Endpoints de este capítulo

| Método y ruta | Permiso | Qué hace |
|---|---|---|
| `GET /api/cursos/{curso_id}/tareas/{tarea_id}/entregas` | `curso.ver` | Fecha base, fechas por sección y recuento de excepciones de cada entrega |
| `GET /api/cursos/{curso_id}/entregas/{entrega_id}/historial-fechas` | `curso.ver` | Encadenamiento de `fecha_efectiva` superseded por sujeto |
| `POST /api/cursos/{curso_id}/sincronizaciones` | `curso.ver` | Encola `sync_tareas_y_fechas` («sincronizar ahora»); nunca llama a Canvas en línea |
| `GET /api/cursos/{curso_id}/entregas/{entrega_id}/progreso-captura` | `curso.ver` | Recuento de `version_entrega` por estado para la barra de progreso |
| `GET /api/cursos/{curso_id}/entregas/{entrega_id}/sujetos/{sujeto_id}/version` | `curso.ver` | Fila vigente, filas superseded y los dos recuentos calculados (commits, commits posteriores) |
| `POST …/version/capturar-ahora` | `tarea.administrar` | Acción manual 1 de §9.8.8 |
| `POST …/version/recapturar` | Rol `PROFESOR` | Acción manual 2 de §9.8.8 |
| `POST …/version/fijar-sha` | Rol `PROFESOR` | Acción manual 3 de §9.8.8, con verificación previa del SHA contra GitHub |
| `POST /api/cursos/{curso_id}/entregas/{entrega_id}/registrar-versiones` | `tarea.administrar` | Confirma la captura masiva de una entrega `VINCULADA_TRAS_EL_CIERRE` (§9.6.7) |
| `GET /api/cursos/{curso_id}/versiones/{version_id}/abrir?destino=arbol\|comparacion\|zip` | `curso.ver` + `acceso_docente_repositorio = CONCEDIDO` | Redirección auditada a GitHub; escribe `bitacora` (§9.9.4) |

### Criterios de aceptación de §9.12

1. **CA-9.12-01.** Ninguna de las rutas de este capítulo se registra sin la dependencia de permiso correspondiente (puerta de contrato de autorización, §2).
2. **CA-9.12-02.** `POST …/version/recapturar` y `POST …/version/fijar-sha` responden `403` a una sesión con rol `AYUDANTE`, aunque tenga `tarea.administrar` concedido.
3. **CA-9.12-03.** `POST /api/cursos/{curso_id}/sincronizaciones` responde antes de 200 ms y no contiene ninguna llamada HTTP a Canvas dentro de la petición.

---

## Resumen de dónde vive cada pieza

| Pieza | Vive en |
|---|---|
| Esquema de `entrega`, `regla_fecha`, `fecha_efectiva`, `version_entrega` | §3 |
| Creación y estado del repositorio, `acceso_docente_repositorio` | §8 |
| Mecánica HTTP contra Canvas (paginación, `include[]`, reintentos) | §5 |
| Mecánica HTTP contra GitHub (creación de tags, lectura de commits) | §6 |
| Algoritmo de `fecha_efectiva` y su resincronización | **§9** (este capítulo) |
| Captura, máquina de estados e inmutabilidad de `version_entrega` | **§9** (este capítulo) |
| Acceso directo a la versión (R2.4.8) | **§9** (este capítulo); su aparición dentro de la pantalla de corrección es §12 |
| Línea de entregas, estado agregado de R2.5.6, tablero | §10 |
| Comunicaciones automáticas (`version_registrada`, `cambio_de_fecha`) | §11 |
| Corrección, publicación de nota, `correccion.version_entrega_id` | §12 |
