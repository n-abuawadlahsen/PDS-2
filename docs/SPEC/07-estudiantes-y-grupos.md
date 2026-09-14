# 7. Estudiantes, secciones y grupos

Este capítulo especifica cómo la aplicación obtiene y mantiene el padrón académico del curso desde Canvas —estudiantes, matrículas, secciones, conjuntos de grupos, grupos y pertenencias—, cómo obtiene el usuario de GitHub de cada estudiante sin que ningún estudiante entre a la aplicación, cómo muestra al equipo docente lo que falta, y qué ocurre en cada caso borde de alta, baja o cambio.

**Requisitos que satisface:** R2.2.1, R2.2.2, R2.2.3, R2.2.4, R2.2.5 y R2.2.6 por completo; y las partes de R2.1.6, R2.3.7, R2.3.9, R2.3.10, R2.3.11, R2.3.12, R2.4.2, R2.4.3, R2.5.4, R2.5.8, R2.6.2, R2.6.5, R2.6.7, R2.7.6 y R2.7.7 que dependen del padrón.

**Restricción que gobierna todo el capítulo:** el enunciado establece en §1 y repite en §2.3 que «los estudiantes no serán usuarios de la aplicación: toda su interacción deberá realizarse a través de Canvas y GitHub». Ninguna funcionalidad de este capítulo exige que un estudiante abra la aplicación, cree una cuenta en ella, siga un enlace hacia ella ni reciba correo desde ella.

**Segunda restricción:** el equipo tiene rol de **profesor** en Canvas, no de administrador de cuenta. No hay Developer Key propia, no hay `as_user_id`, no hay informes de cuenta y no está garantizado el acceso a `sis_user_id` ni al correo del estudiante. Todo lo que sigue está diseñado para funcionar con un token personal de profesor.

---

## 7.1 Cómo leer este capítulo

**Orden de precedencia aplicado, sin excepciones:** enunciado → actas de reconciliación (`RG-nnn`) → carta de arquitectura (`A-nnn`) → respuestas de alcance (`Q-…`). Donde una respuesta de alcance decía una cosa y una regla `RG` dice otra, manda la regla y este capítulo redacta la regla.

**Correcciones de precedencia que este capítulo aplica y que conviene tener presentes desde el principio:**

| Punto | Lo que decía la respuesta de alcance | Lo que manda ahora | Fuente |
|---|---|---|---|
| Permiso para crear o restaurar la tarea de registro | `tarea.administrar` | **`curso.administrar`**, que es NO CONCEDIBLE y por tanto exclusivo de un profesor | RG-083 |
| Fila del mapeo cuando no hay dato | Se creaba al llegar el primer candidato | **Se crea al espejar al estudiante**, con `estado = 'SIN_DATO'` y `cuenta_github_id` nulo | RG-004, A-210 |
| Motivos de invalidación del mapeo | Tres | **Cinco** | RG-005, A-210 |
| Salida de un integrante del grupo | Incidencia con dos botones, sin estado propio del acceso | **Tres estados nuevos en la máquina 3**: `REVOCACION_PROPUESTA`, `REVOCACION_PROGRAMADA`, `REVOCADO` | RG-183, A-212 |
| Traslado de grupo | Revocación automática a las 24 h | **Ninguna revocación se ejecuta sola**; la gracia se cuenta desde la decisión humana | RG-185, A-212 |
| Incidencias de la tarea de registro | Dos tipos (`TAREA_REGISTRO_ALTERADA`, `TAREA_REGISTRO_ELIMINADA`) | **Un solo tipo**, `TAREA_REGISTRO_ALTERADA`, con severidad derivada del detalle | RG-189 |
| Ámbito de la elegibilidad de una cuenta de GitHub | Por curso | **Toda la aplicación**: se rechaza un `github_user_id` con mapeo `VIGENTE` en cualquier curso | RG-199, A-187 |
| Composición del grupo al cierre | Tabla `integrante_version_entrega` | **`version_entrega.integrantes jsonb`**, inmutable | RG-028 |
| Ampliar catálogos cerrados | Cada área ampliaba el suyo | **Ningún código nuevo de incidencia, estado, motivo, trabajo o entidad se usa hasta que la carta incorpore la enmienda única** | RG-190 |

**Convenciones de escritura obligatorias en todo lo que este capítulo especifica:**

- Todo instante se almacena en UTC y se presenta en la zona del curso, con formato `dd-MM-yyyy HH:mm` y **la zona escrita al lado siempre** (A-152). Nunca se muestra una hora desnuda.
- Todo estado interno se muestra traducido, con etiqueta fija e idéntica en todas las vistas. **Nunca aparece un identificador en mayúsculas en pantalla** (A-155).
- Vocabulario cerrado (A-154): se dice **sección**, **conjunto de grupos**, **grupo**, **estudiante**, **cuenta de GitHub vinculada**, **incidencia**. No se dice paralelo, group set, alumno, mapeo, matching, error ni alerta.
- Ninguna pantalla consulta a Canvas o a GitHub para renderizarse (Ley 1, A-119). Toda vista lee el espejo y muestra su propio sello de antigüedad (A-231, RG-075).

---

## 7.2 Modelo de datos del padrón

### 7.2.1 Tablas espejo de Canvas

| Tabla | Columnas | Unicidad y notas |
|---|---|---|
| `seccion` | `id`, `curso_id`, `canvas_section_id`, `nombre`, `sis_section_id`, `nonxlist_course_id`, `estado`, `sincronizado_en` | **único (`curso_id`, `canvas_section_id`)**. `estado ∈ {ACTIVA, ELIMINADA}`. `nonxlist_course_id` no nulo ⇒ sección *cross-listed* (A-053) |
| `estudiante` | `id`, `curso_id`, `canvas_user_id`, `nombre`, `nombre_ordenable`, `login_id`, `sis_user_id`, `email`, `uuid`, `past_uuid`, `group_ids_canvas` (`jsonb`), `estado`, `primera_vista_en`, `ultima_vista_en`, `retirado_en` | **único (`curso_id`, `canvas_user_id`)**. `estado ∈ {ACTIVO, INVITADO, INACTIVO, CONCLUIDO, RETIRADO}`, **derivado** del conjunto de matrículas (A-044) |
| `matricula` | `id`, `curso_id`, `estudiante_id`, `seccion_id`, `canvas_enrollment_id`, `tipo`, `role_id`, `estado`, `limitada_a_seccion`, `activa`, `sincronizado_en` | **único (`curso_id`, `canvas_enrollment_id`)**. **Una fila por matrícula**, no por persona (A-044) |
| `conjunto_grupos` | `id`, `curso_id`, `canvas_group_category_id`, `nombre`, `no_colaborativo`, `self_signup`, `group_limit`, `auto_leader`, `sincronizado_en` | **único (`curso_id`, `canvas_group_category_id`)** |
| `grupo` | `id`, `curso_id`, `conjunto_grupos_id`, `canvas_group_id`, `nombre`, `slug`, `estado`, `lider_estudiante_id`, `is_full`, `sincronizado_en` | **único (`curso_id`, `canvas_group_id`)**. `estado ∈ {ACTIVO, ELIMINADO}` |
| `pertenencia_grupo` | `id`, `grupo_id`, `estudiante_id`, `workflow_state`, `activa`, `activa_desde`, `activa_hasta`, `ciclos_ausente`, `origen`, `sincronizado_en` | **único (`grupo_id`, `estudiante_id`)**. `workflow_state ∈ {accepted, invited, requested}`. **Sin unicidad (`conjunto_grupos`, `estudiante`)** (A-049) |

`entro_en` y `salio_en` **no existen**: la vigencia de una pertenencia se lee de `activa_desde` y `activa_hasta` (RG-008, A-212 punto 13). `ciclos_ausente` es el contador de la confirmación en dos ciclos y no es sinónimo de ninguna de las dos.

### 7.2.2 Tablas del puente Canvas ↔ GitHub

| Tabla | Columnas | Unicidad y notas |
|---|---|---|
| `cuenta_github` | `id`, `github_user_id` (`bigint`), `login`, `tipo`, `avatar_url`, `estado`, `revalidado_en` | **único `github_user_id`**, **global y sin `curso_id`**. `tipo ∈ {USER, ORGANIZATION, BOT}`; `estado ∈ {VALIDA, RENOMBRADA, NO_EXISTE, ES_ORGANIZACION}` |
| `mapeo_github` | `id`, `curso_id`, `estudiante_id`, `cuenta_github_id` (**nullable**), `origen`, `confianza`, `evidencia` (`jsonb`), `estado` (**`DEFAULT 'SIN_DATO'`**), `motivo_invalidacion`, `vigente_desde`, `vigente_hasta`, `creado_por`, `revalidado_en` | **único parcial (`curso_id`, `estudiante_id`) donde `estado <> 'SUPERSEDIDO'`**; **único parcial (`curso_id`, `estudiante_id`) donde `estado = 'VIGENTE'`**; **único parcial (`curso_id`, `cuenta_github_id`) donde `estado = 'VIGENTE'`** |

**El catálogo de cuentas es global; el mapeo es por curso** (A-077, A-079). La misma persona de GitHub es **una sola fila** en todo el sistema, de modo que la revalidación diaria se hace una vez por cuenta y no una vez por curso; la fila que la ata a un estudiante concreto lleva `curso_id` y no se propaga entre cursos. **No existe atajo de propagación entre cursos**: un curso nuevo empieza con cero mapeos y no se propone ningún valor tomado de otro curso, ni siquiera para confirmar, porque A-022 exige que toda consulta al modelo se filtre por el `curso_id` del contexto y proponer al profesor del curso B lo que un estudiante declaró en el curso A es exactamente el acceso indirecto que esa decisión cierra.

**El mapeo es *append-only*** (Ley 2, A-078). Corregir un mapeo **no actualiza la fila**: cierra la vigente con `estado = 'SUPERSEDIDO'` y `vigente_hasta`, y crea una fila nueva. Así el sistema puede responder «¿quién dijo que este repositorio era de este estudiante, cuándo y con qué evidencia?». **Nunca hay un `DELETE` sobre `mapeo_github`** (A-030).

### 7.2.3 Columnas de `curso` que este capítulo utiliza

| Columna | Tipo | Para qué |
|---|---|---|
| `canvas_assignment_id_registro` | `bigint` nullable | Identidad de la tarea de registro en Canvas (§7.6.2) |
| `registro_creado_en`, `registro_creado_por` | `timestamptz`, `uuid` | Auditoría de la creación |
| `registro_estado` | `text` | `NO_CREADA`, `ACTIVA`, `ALTERADA`, `DESAPARECIDA` |
| `registro_huella_config` | `bytea` | SHA-256 de los ocho campos de configuración de §7.6.2, recalculado con lo que Canvas devolvió |
| `roles_estudiante_extra` | `jsonb` | Lista de `role_id` de roles personalizados derivados de `StudentEnrollment`, configurable por curso |
| `canal_comunicacion_activo` | `text` | `CONVERSACION`, `COMENTARIO_ENTREGA` o `BLOQUEADO` (A-227, RG-103; nombres fijados en detalle en §4.9 y usados consistentemente por §11.9) |

### 7.2.4 Identidad: qué es clave y qué es dato de presentación

| Hecho | Clave duradera | Dato mutable de presentación |
|---|---|---|
| Persona en Canvas | **`canvas_user_id`**, único por curso | `nombre`, `nombre_ordenable`, `login_id`, `sis_user_id`, `email` |
| Cuenta en GitHub | **`cuenta_github.github_user_id`** (`bigint`) | `cuenta_github.login`, `avatar_url` |
| Sección, grupo, conjunto de grupos, matrícula | `canvas_section_id`, `canvas_group_id`, `canvas_group_category_id`, `canvas_enrollment_id` | `nombre`, `slug` |

**`canvas_user_id` es la clave de identidad efectiva del estudiante desde el 16 de septiembre** (RG-156, A-074). `sis_user_id`, `login_id`, `uuid` y `past_uuid` se persisten **cuando la instancia los entregue** y se usan **sólo como claves de reconciliación** (§7.8.4), nunca como identidad: `sis_user_id` sólo llega si el usuario vino de un import SIS **y** el llamante tiene permiso para ver información SIS, condición que un profesor no tiene garantizada.

**`cuenta_github.login` se guarda con las mayúsculas canónicas que devuelve la API y no en minúsculas**, porque nada compara por login: toda comparación, las dos unicidades y la atribución de commits se hacen sobre `github_user_id`. Dos escrituras distintas del mismo login (`JPerez` y `jperez`) resuelven al mismo `github_user_id` y colisionan correctamente en la base sin que nadie tenga que acordarse de normalizar.

### 7.2.5 Claves foráneas, cuarentena y jerarquía de fuentes

**`sync_roster` es la única fuente de qué personas existen en el curso.** `sync_grupos` y `recolector_mapeos` **no crean estudiantes bajo ninguna circunstancia** (RG-070 de la respuesta consolidada; regla operativa de Q-2.2-70).

- `pertenencia_grupo.estudiante_id`, `mapeo_github.estudiante_id`, `matricula.estudiante_id` y `matricula.seccion_id` son **`NOT NULL` con `FOREIGN KEY`**.
- Todas las claves foráneas se declaran **`ON DELETE RESTRICT ON UPDATE RESTRICT`**; no existe `CASCADE` ni `SET NULL` en ninguna migración, y una prueba de arquitectura falla la construcción si aparece (RG-048).
- `mapeo_github.cuenta_github_id` es **nullable** por el estado `SIN_DATO`, y figura por ese motivo en la lista cerrada de claves foráneas nullables de RG-048.
- Dentro de un ciclo de `sync_roster` se leen **primero las secciones y después las matrículas**, en la misma ejecución y bajo el mismo cerrojo, de modo que una sección nueva nunca llega después que la matrícula que la referencia.

**Cuarentena, nunca fila fantasma.** Un `canvas_user_id` que aparece en grupos o en entregas y no existe en `estudiante`:

1. **No se inserta.** Una fila «no inscrito» sería una segunda verdad sobre quién está en el curso.
2. Se registra en `sincronizacion.contadores.huerfanos[]` con `canvas_user_id`, nombre visto y fuente.
3. Se abre `ROSTER_TRUNCADO`, severidad **ADVERTENCIA**, **una sola por curso** con el detalle de todos los huérfanos dentro.
4. Se encola un `sync_roster` inmediato con clave de idempotencia `(curso_id, "roster_por_huerfano", ciclo)`, de modo que se dispara **una sola vez por ciclo** y no produce bucle. El caso más probable es un roster desfasado unos minutos.
5. Si tras ese ciclo la persona sigue sin aparecer, la incidencia queda abierta con el texto «aparece en *grupos* / *entregas* pero no figura en el roster del curso» y la acción «volver a sincronizar el roster». **No se puede aprovisionar a quien no está en el roster**, y no por una comprobación sino por construcción: la guarda de A-093 exige un mapeo `VIGENTE` sobre un `estudiante` existente, y sin fila de `estudiante` no hay sujeto (A-164).

**Entregas de quien no es estudiante.** Una entrega de la tarea de registro cuyo `user_id` no resuelve a un `estudiante` del curso **no crea mapeo**, se registra en `bitacora` y **no recibe comentario de respuesta**: responder a quien no es estudiante sería escribir a un desconocido. El *Test Student* queda fuera por A-050.

### 7.2.6 Criterios de aceptación de §7.2

1. Insertar directamente en la base una `pertenencia_grupo` con `estudiante_id` de otro curso falla por clave foránea, y la aplicación traduce la violación a incidencia, **nunca a un `500`**.
2. Una migración que contenga `ON DELETE CASCADE` o `ON DELETE SET NULL` **falla la construcción**.
3. Tras espejar un estudiante nuevo existe **exactamente una** fila de `mapeo_github` para él, con `estado = 'SIN_DATO'` y `cuenta_github_id` nulo, escrita en la **misma transacción**.
4. Intentar crear una segunda fila viva de `mapeo_github` para el mismo `(curso_id, estudiante_id)` con `estado <> 'SUPERSEDIDO'` es rechazado por el índice único parcial.
5. Un módulo distinto de `sync_roster` que escriba en la tabla `estudiante` **falla la prueba de arquitectura**.
6. Una consulta de listado de estudiantes que no filtre por `curso_id` falla la puerta de contrato de autorización.
7. Un estudiante con dos matrículas activas aparece **una sola vez** en la tabla de personas y **dos veces** en `matricula`.

---

## 7.3 Sincronización del padrón: secciones, grupos y pertenencias

**Esta sección especifica el proceso, no el esquema.** Las tablas ya están fijadas en §7.2.1; aquí se fija qué hace la aplicación con lo que Canvas devuelve, cuándo se marca `ACTIVA`/`ELIMINADA`, y qué ocurre ante un cambio. El mecanismo HTTP puro —endpoints, paginación, cabeceras— es de `docs/SPEC/05-integracion-canvas.md` y no se repite aquí.

### 7.3.1 Cadencias y disciplina de escritura

**`sync_roster` y `sync_grupos` corren cada 10 minutos, por curso, bajo el mismo cerrojo (`pg_advisory_lock(curso_id)`)** que serializa todo el tráfico de Canvas de ese curso. `sync_roster` lee **primero las secciones y después las matrículas**, en la misma ejecución, de modo que una sección nueva nunca llega después que la matrícula que la referencia (§7.2.5).

**`sync_grupos` tiene un freno automático de coste.** Si el gasto de API acumulado por `sync_grupos` en la última hora supera el **30 % del presupuesto horario de Canvas del curso**, la cadencia baja sola a **30 minutos** hasta que el presupuesto se recupera; el hecho se registra en `sincronizacion` y se muestra en `/operacion`. Nadie configura este freno: es automático y reversible.

**Ambos ciclos son idempotentes y conviven con el botón manual «Sincronizar ahora»**, que encola el mismo trabajo y nunca llama a Canvas dentro de la petición HTTP (Ley 1).

### 7.3.2 Secciones: ciclo de vida

`seccion` se actualiza por *upsert* sobre `(curso_id, canvas_section_id)` en cada ciclo de `sync_roster`. Una sección que deja de aparecer **dos ciclos completos consecutivos** pasa a `estado = 'ELIMINADA'`; **la fila no se borra** (§7.2.5, A-030). Una sección `ELIMINADA` que reaparece vuelve a `ACTIVA` en el mismo *upsert*, sin intervención.

**Una sección `ELIMINADA` con matrículas activas apuntando a ella no es un caso posible**: `matricula.seccion_id` es `NOT NULL FOREIGN KEY` (§7.2.5) y el orden de lectura de 7.3.1 garantiza que la matrícula referencia siempre una sección viva o recién leída en el mismo ciclo.

### 7.3.3 Conjuntos de grupos y grupos

**Sólo se sincronizan los conjuntos de grupos colaborativos.** Las *differentiation tags* (`no_colaborativo = true`) se detectan una vez al vincular el curso, se persisten como dato informativo y **no generan grupos, no reciben repositorio y no participan del cálculo de fechas**; se muestran con la etiqueta «este conjunto es una etiqueta de diferenciación, no genera repositorios».

`conjunto_grupos` y `grupo` se actualizan por *upsert* sobre `(curso_id, canvas_group_category_id)` y `(curso_id, canvas_group_id)` respectivamente. Un grupo que desaparece pasa a `estado = 'ELIMINADO'` sin borrarse; su desenlace exacto sobre los sujetos y repositorios que dependían de él es de §7.9.3, que remite a su vez a la máquina 2 del capítulo 8 para el estado del repositorio.

`pertenencia_grupo` se actualiza por *upsert* sobre `(grupo_id, estudiante_id)`, con `workflow_state ∈ {accepted, invited, requested}` tal como Canvas lo devuelve. **Sólo cuentan como integrantes del grupo, a todos los efectos de este capítulo, las pertenencias `accepted`**; los `invited` y `requested` se persisten y se muestran en Pendientes (§7.8) como «pendiente de aceptar en Canvas», pero no participan del predicado de completitud del grupo, que es materia del capítulo 8.

### 7.3.4 Pertenencias: alta automática, baja nunca automática

**La reconciliación es asimétrica, y lo es por diseño: las altas se aplican solas, las bajas nunca.**

**Alta de un integrante.** Cuando aparece una `pertenencia_grupo` nueva con `workflow_state = 'accepted'`, el *upsert* la persiste con `activa = true` y `activa_desde = now()` en el mismo ciclo. No hay guarda ni espera: **R2.3.9** exige incorporar automáticamente a los estudiantes correspondientes, y **R2.3.10** exige que ocurra sin interacción directa. Qué efecto tiene esa alta sobre el acceso a GitHub del integrante es del capítulo 8 (`reconciliar_accesos`, cada 15 minutos), que este capítulo no redefine.

**Baja de un integrante.** Cuando una pertenencia deja de estar `accepted` —desaparece de la respuesta de Canvas o cambia de estado—, y esa ausencia se confirma en **dos ciclos consecutivos** de `sync_grupos` (`pertenencia_grupo.ciclos_ausente`):

1. Se marca `pertenencia_grupo.activa = false` con `activa_hasta = now()`. **La fila no se borra** (A-030).
2. **No se revoca ningún acceso de GitHub por sí sola.** El efecto sobre `acceso_repositorio` —la propuesta de revocación, la gracia y quién decide— es la máquina 3 del capítulo 8 (§8.8), que este capítulo cita y no redefine.
3. Se abre `GRUPO_INCOMPLETO` con `detalle.subtipo = 'INTEGRANTE_SALIO_DEL_GRUPO'`, severidad **ADVERTENCIA**, con el nombre de la persona y el grupo, visible en Pendientes (§7.8).
4. En la ficha del grupo, la persona pasa a mostrarse como **«Ex integrante — conserva acceso al repositorio»**: nunca desaparece en silencio.

**La atribución de los commits que esa persona ya subió no cambia.** `commit.estudiante_id` se resuelve contra el mapeo vigente del estudiante, no contra su pertenencia al grupo; un ex integrante sigue apareciendo en el *timeline* de la actividad que hizo, con la ventana de participación que le corresponde (capítulo 10, no de este capítulo).

**La composición que se califica es la del cierre, no la actual.** `version_entrega.integrantes` (`jsonb`, capítulo 9) copia de forma inmutable, en el momento de la captura, quiénes eran integrantes `accepted` en ese instante. Un cambio de grupo posterior nunca reescribe una entrega ya cerrada.

### 7.3.5 Estudiante en dos secciones activas

No se elige en silencio entre las dos. Se registran **ambas** matrículas, la interfaz muestra las dos secciones con una etiqueta de conflicto, y se abre `ESTUDIANTE_EN_DOS_SECCIONES`, severidad informativa. El efecto sobre el cálculo de la fecha de cierre —se toma la más tardía y la fila queda marcada `ambigua = true`— es regla del capítulo 9 y no se repite aquí.

### 7.3.6 Doble pertenencia a un mismo conjunto de grupos

**No se impone unicidad `(conjunto_grupos, estudiante)` en la base de datos**: Canvas no garantiza que sea imposible, y una restricción única haría fallar la ingesta entera ante un dato que el sistema de origen sí admite. Cuando ocurre, se insertan **ambas** pertenencias, se abre `ESTUDIANTE_EN_DOS_GRUPOS`, severidad **BLOQUEANTE**, y **se bloquea el aprovisionamiento de los dos grupos implicados** hasta que un docente resuelva desde Pendientes (§7.8) cuál es la membresía correcta. No se puede saber cuál de las dos vale sin que alguien lo diga.

### 7.3.7 Traslado de grupo

Un estudiante que figura `accepted` en **exactamente otro** grupo del mismo `conjunto_grupos` en el mismo ciclo en que salió del anterior es un **traslado**, no una salida simple: se detecta en `sync_grupos`, abre `GRUPO_INCOMPLETO` con `detalle.subtipo = 'TRASLADO_DE_GRUPO'`, y su tratamiento en la máquina de accesos —gracia de 24 horas, aviso inmediato, ninguna revocación automática a las 24 horas— es del capítulo 8 (§8.8) y no se redefine aquí. **Si figura en dos grupos del mismo conjunto a la vez, no es un traslado**: rige §7.3.6.

### 7.3.8 Cautela ante cambios masivos

**Si un ciclo de `sync_grupos` devuelve cero pertenencias, o menos del 60 % de las del ciclo anterior para un mismo conjunto de grupos, no se aplica ninguna baja**: se registra `sincronizacion.resultado = 'PARCIAL'`, se abre `ROSTER_SOSPECHOSO` con el detalle de los grupos afectados, y se conserva el estado previo. Es la misma regla que A-045 aplica al roster de estudiantes, aplicada aquí a las pertenencias: un roster o un listado de grupos recortado por un fallo transitorio de permisos llega como un `200` normal, sin aviso, y sin esta cautela revocaría accesos y abriría incidencias falsas sobre medio curso.

### 7.3.9 Criterios de aceptación de §7.3

| Id | Criterio |
|---|---|
| CA-7.3-01 | Una sección ausente durante un solo ciclo de `sync_roster` permanece `ACTIVA`; sólo pasa a `ELIMINADA` tras dos ciclos completos de ausencia consecutivos |
| CA-7.3-02 | Un conjunto de grupos con `collaboration_state` distinto de colaborativo no aparece nunca como grupo con repositorio, sólo como etiqueta informativa |
| CA-7.3-03 | Un integrante que pasa a `accepted` en un grupo aparece con acceso en curso de concesión dentro del ciclo de `reconciliar_accesos` siguiente, sin que nadie lo apruebe |
| CA-7.3-04 | Un integrante que sale de un grupo conserva su acceso al repositorio hasta que un profesor o ayudante decide explícitamente revocarlo; la incidencia `GRUPO_INCOMPLETO` queda abierta mientras tanto |
| CA-7.3-05 | Un estudiante con dos matrículas activas en dos secciones distintas se muestra con las dos, nunca con una elegida en silencio |
| CA-7.3-06 | Un estudiante `accepted` a la vez en dos grupos del mismo conjunto bloquea el aprovisionamiento de ambos grupos y abre `ESTUDIANTE_EN_DOS_GRUPOS` |
| CA-7.3-07 | Un traslado de grupo detectado a las 10:00 no revoca ningún acceso a las 10:00 del día siguiente por sí solo: la fila permanece a la espera de la decisión de un profesor |
| CA-7.3-08 | Un ciclo de `sync_grupos` que devuelve menos del 60 % de las pertenencias del ciclo anterior de un conjunto de grupos no aplica ninguna baja y abre `ROSTER_SOSPECHOSO` |

---

## 7.4 Las cuatro vías para obtener el usuario de GitHub del estudiante

**R2.2.4** exige asociar cada estudiante de Canvas con su usuario de GitHub sin que el estudiante entre a la aplicación (§7.1). Existen **cuatro vías** y **las cuatro conviven**, en este orden de preferencia. No hay una quinta ni una tercera: el enunciado exige explícitamente definir una estrategia de enrolamiento y evaluar su usabilidad (§2.2), y este capítulo la fija en su totalidad.

### 7.4.1 Vía 1 — Tarea de Canvas de registro (vía principal)

La aplicación crea en Canvas, desde la pantalla de personas del curso, una tarea llamada **«Registro de tu cuenta de GitHub»**, individual, de tipo texto (`online_text_entry`), sin puntos y excluida de la nota final, publicada y con una fecha de cierre holgada. **El enunciado y las instrucciones los redacta la aplicación y el profesor puede editarlos antes de publicar.** El estudiante no entra a la aplicación en ningún momento: usa Canvas, que ya usa para todo lo demás.

**El permiso del que depende esta vía se comprueba en el checklist de vinculación** (capítulo 4, ítem 16): crear una tarea en Canvas exige el permiso de administrar tareas en el token del profesor, y es **bloqueante**. **Si el permiso faltara**, la creación de la tarea de registro se deshabilita con el motivo escrito en el propio botón, y la pantalla ofrece de inmediato las tres vías complementarias de §7.4.4–§7.4.6 más las instrucciones para que el profesor cree la tarea a mano en Canvas y la vincule después. **R2.2.4 y R2.2.5 siguen cumpliéndose por esas vías**; lo que se pierde es la comodidad, no el requisito.

**La recolección es incremental**, leyendo las entregas de esa tarea con un mecanismo cuyo detalle HTTP es del capítulo 5. La cadencia es de **3 minutos mientras la tarea de registro está abierta** y de **15 minutos si no lo está**, **más un volcado completo cada hora como red de seguridad**, porque no está garantizado que un reenvío del estudiante actualice de forma fiable la marca temporal que el sincronizador usa para leer sólo lo nuevo.

### 7.4.2 Extracción y validación del candidato

**El cuerpo de la entrega es HTML, no texto plano**, y el extractor lo trata como tal: quita etiquetas, decodifica entidades, normaliza espacios y recorta. Sobre el resultado se aplican, **en este orden**, cuatro patrones: URL de perfil (`github.com/<login>`), arroba (`@login`), login desnudo que cumpla las reglas de nombre de GitHub, y correo `…@users.noreply.github.com`. **Si ninguno casa, o casan dos candidatos distintos, el mapeo queda `NO_RESUELTO`** con el texto crudo conservado como evidencia.

**El candidato se valida siempre contra GitHub**, nunca se acepta a ciegas: se guarda el identificador numérico de la cuenta y el login canónico que la API devuelve, no el que escribió el estudiante. Se rechaza si la cuenta resuelve a una organización, comparando la respuesta de la cuenta contra la de una organización con el mismo nombre, sin confiar en un único campo de tipo cuyos valores literales no están garantizados por la documentación. Se rechaza también si la cuenta no es elegible (§7.5).

**No se usa OAuth de GitHub del estudiante para verificar la propiedad de la cuenta, y es una decisión deliberada, no una limitación técnica.** El enunciado fija que los estudiantes no son usuarios de la aplicación; un flujo de OAuth con enlace, *callback* y página propia admite la lectura de que el estudiante entra a la aplicación, y esa lectura no se va a defender durante una evaluación. La limitación se mitiga por tres caminos, no se esconde: la validación contra GitHub garantiza que la cuenta existe y es una persona; la doble unicidad de §7.6 impide que dos estudiantes reclamen la misma cuenta; y la invitación de colaborador de GitHub sólo la puede aceptar quien controla la cuenta, de modo que un usuario mal escrito se detecta porque su invitación nunca se acepta (visible en Pendientes, §7.8).

### 7.4.3 Vía 2 — Edición manual del equipo docente

Desde Pendientes (§7.8), un campo por estudiante con `mapeo.editar`, con **validación en vivo** contra GitHub — uno de los pocos casos permitidos de consulta en vivo desde una vista (Ley 1) — que muestra avatar, nombre y enlace al perfil antes de guardar, y avisa de inmediato si esa cuenta ya está asignada a otro estudiante o no es elegible (§7.5, §7.6.3).

### 7.4.4 Vía 3 — Importación CSV

Columnas `canvas_user_id` (o `login_id`) y `github_login`, con `mapeo.editar`. La pantalla muestra una **previsualización fila a fila** con el resultado de validación de cada una —qué se creará, qué se supersederá, qué fallará y por qué— **antes de aplicar nada**, y permite aplicar sólo las filas válidas. **Nunca se aplica a ciegas.**

### 7.4.5 Vía 4 — Reintento asistido

Un botón, con `mapeo.editar` o `comunicacion.enviar` según §2, envía un mensaje por Canvas a todos los estudiantes que aún no tienen mapeo `VIGENTE`, con el texto exacto de qué deben hacer y el enlace a la tarea de registro. **No es una fuente de datos nueva**: cada respuesta que produce se procesa exactamente como una entrega de la vía 1 (§7.4.1), con el mismo origen `AUTOSERVICIO_CANVAS`. Por eso `mapeo_github.origen` tiene **tres** valores y no cuatro —`AUTOSERVICIO_CANVAS`, `CARGA_DOCENTE`, `IMPORTACION_CSV`—: la vía 4 es un mecanismo para alimentar la vía 1, no una fuente distinta de evidencia. La cadencia, el tope y el canal exactos de este recordatorio son de `docs/SPEC/11-informes-y-comunicacion.md`, que este capítulo cita y no redefine.

### 7.4.6 El bucle se cierra dentro de Canvas

**La aplicación responde siempre por el mismo canal por el que le hablaron.** Cada intento de la vía 1 produce un comentario automático en la propia entrega del estudiante: si salió bien, qué cuenta quedó registrada con el login canónico y el nombre del repositorio que recibirá; si salió mal, qué escribió y qué debe corregir, con el motivo concreto. **Esta pieza es la que hace usable el proceso sin que el estudiante entre a la aplicación**: recibe confirmación en el mismo sitio donde actuó. El mecanismo general de comunicación —plantillas, canales de respaldo y sus disparadores— es de `docs/SPEC/11-informes-y-comunicacion.md`.

### 7.4.7 Criterios de aceptación de §7.4

| Id | Criterio |
|---|---|
| CA-7.4-01 | Con el permiso de administrar tareas ausente, el botón de crear la tarea de registro aparece deshabilitado con el motivo escrito, y las vías 2 a 4 siguen disponibles |
| CA-7.4-02 | Un texto entregado con dos URLs de perfil de GitHub distintas produce `NO_RESUELTO`, nunca una elección arbitraria entre las dos |
| CA-7.4-03 | Un candidato que resuelve a una organización nunca queda `VIGENTE`, y la entrega recibe el comentario correspondiente |
| CA-7.4-04 | Una entrega producida por el reintento asistido de la vía 4 se registra con `origen = 'AUTOSERVICIO_CANVAS'`, idéntico al de una entrega espontánea de la vía 1 |
| CA-7.4-05 | Ninguna pantalla de este capítulo ofrece un enlace de autenticación de GitHub dirigido al estudiante |
| CA-7.4-06 | Toda entrega de la tarea de registro produce, en un plazo acotado, un comentario automático en esa misma entrega |

---

## 7.5 Elegibilidad de una cuenta de GitHub, en toda la aplicación

### 7.5.1 Qué hace no elegible a una cuenta

**Una cuenta de GitHub no puede ser a la vez del equipo docente y de un estudiante.** Es no elegible, en lista cerrada: la cuenta enlazada desde el perfil de cualquier miembro **activo** del curso (profesor o ayudante); cualquier miembro del equipo de lectura docente del curso (capítulo 6); el propietario de la organización de GitHub; y la cuenta *bot* de la propia App. La comprobación es **una sola función de dominio**, sin lecturas ni escrituras propias, consumida por las dos puertas de §7.5.3.

### 7.5.2 Alcance: toda la aplicación, no el curso

**La comprobación no se acota al curso donde ocurre.** Rechaza una cuenta que tenga un mapeo `VIGENTE` en **cualquier curso** de la aplicación, no sólo en los del declarante, porque el identificador de una cuenta de GitHub es global y la unicidad de la cuenta declarada por un docente también lo es. **Si se acotara por curso, un ayudante podría declarar la cuenta de GitHub de un estudiante de otro curso y obtener lectura de todos los repositorios de éste**, que es precisamente el riesgo que esta regla cierra. Es la regla explícita de §7.1: la elegibilidad de una cuenta de GitHub se juega en toda la aplicación, no por curso.

### 7.5.3 Las dos puertas, con desenlaces distintos

| Puerta | Cuándo se usa | Desenlace |
|---|---|---|
| **Del docente** | `PUT` sobre el perfil de un profesor o ayudante, aceptación de una invitación al equipo, carga manual (§7.4.3) o importación CSV (§7.4.4) hecha por una persona | **Rechazo inmediato** con mensaje explícito, sin persistir nada, y registro en bitácora |
| **De la ingesta** | Recolector de la tarea de registro (§7.4.1), autoservicio del estudiante | No hay petición que rechazar: la fila se persiste con `estado = 'NO_RESUELTO'` y `motivo_invalidacion = 'CUENTA_NO_ELEGIBLE'`, con el texto «esa cuenta pertenece al equipo docente del curso; vuelve a entregar con tu cuenta personal» |

**Un solo tipo de incidencia para este hecho, distinto del de conflicto entre dos estudiantes.** Confundir «un estudiante declaró la cuenta de un docente» con «dos estudiantes declararon la misma cuenta» (§7.6.3) mezclaría en Pendientes un problema de acceso del equipo docente con un problema del padrón; son incidencias separadas.

**Guarda repetida en tiempo de ejecución, no sólo en el formulario.** La incorporación de un docente al equipo de lectura de GitHub (capítulo 6) repite esta comprobación inmediatamente antes de escribir; si falla, no llama, y se abre incidencia bloqueante con aviso a los profesores del curso.

### 7.5.4 Invariante nocturno

Además de las dos puertas, un invariante que corre una vez al día lista —y no auto-repara— cualquier colisión que haya podido colarse: por ejemplo, si una persona ya con mapeo `VIGENTE` como estudiante en un curso se incorpora después como ayudante de otro. **La colisión no invalida sola el mapeo del estudiante**: abre incidencia y deja que un docente decida, porque invalidar sin que nadie lo pida le quitaría el repositorio a quien no hizo nada malo.

### 7.5.5 Criterios de aceptación de §7.5

| Id | Criterio |
|---|---|
| CA-7.5-01 | Un profesor que intenta declarar como suya una cuenta de GitHub con mapeo `VIGENTE` en cualquier curso de la aplicación recibe rechazo inmediato, sin excepción por curso |
| CA-7.5-02 | Una entrega de la tarea de registro que declara la cuenta de un ayudante del mismo curso queda `NO_RESUELTO` con `motivo_invalidacion = 'CUENTA_NO_ELEGIBLE'`, nunca `VIGENTE` |
| CA-7.5-03 | El caso «cuenta de un docente declarada por un estudiante» y el caso «misma cuenta declarada por dos estudiantes» abren tipos de incidencia distintos y nunca se mezclan en una sola fila |
| CA-7.5-04 | El invariante nocturno de elegibilidad cruzada nunca invalida un mapeo por sí mismo: sólo abre incidencia |

---

## 7.6 Máquina de estados de `mapeo_github`

### 7.6.1 Nueve estados, un solo terminal

`mapeo_github.estado` es un enum cerrado de **nueve** valores, `DEFAULT 'SIN_DATO'`. **`SUPERSEDIDO` es el único terminal.**

| Estado | Se entra cuando | Sale a |
|---|---|---|
| `SIN_DATO` | El estudiante se espeja y no hay ningún candidato todavía (§7.2.6 criterio 3) | `RECIBIDO` |
| `RECIBIDO` | Llega un candidato sin validar, por cualquiera de las cuatro vías de §7.4 | `VIGENTE`, `NO_EXISTE`, `ES_ORGANIZACION`, `EN_CONFLICTO`, `NO_RESUELTO` |
| `NO_RESUELTO` | El texto era ambiguo, vacío, o casaron dos candidatos (§7.4.2) | `RECIBIDO` |
| `NO_EXISTE` | La cuenta no existe en GitHub | `RECIBIDO` |
| `ES_ORGANIZACION` | El candidato resuelve a una organización | `RECIBIDO` |
| `EN_CONFLICTO` | Esa cuenta ya está `VIGENTE` para otro estudiante del mismo curso (§7.6.3) | `VIGENTE`, tras resolución docente explícita |
| `VIGENTE` | La cuenta existe, es una persona y es elegible (§7.5) | `SUPERSEDIDO`, `INVALIDADO` |
| `INVALIDADO` | La revalidación periódica detecta un problema sobre una fila que era `VIGENTE` (§7.6.2) | `RECIBIDO` |
| `SUPERSEDIDO` | Una corrección creó una fila nueva (Ley 2, §7.2.2) | terminal |

**Un `RECIBIDO` que lleva más de 15 minutos sin resolverse se saca a `/operacion`** como caso a revisar, porque un candidato sin validar indefinidamente es exactamente la falta de información que **R2.2.6** exige mostrar. **Ninguna transición a `INVALIDADO` destruye el repositorio ni el acceso ya concedido**: abre incidencia y deja que un docente decida, con el mismo criterio que gobierna toda revocación en este capítulo (§7.3.4, §8.8).

### 7.6.2 Cinco motivos de invalidación

`mapeo_github.motivo_invalidacion` es un enum cerrado de **cinco** valores, no de tres:

| Motivo | Qué detectó la revalidación periódica | Qué hace la aplicación |
|---|---|---|
| `RENOMBRADO` | La cuenta sigue existiendo con otro login | **Se actualiza sola**, sin invalidar ni molestar a nadie: el identificador numérico no cambió |
| `CUENTA_ELIMINADA` | La cuenta ya no existe en GitHub | Abre incidencia; el estudiante queda sin cuenta vigente hasta que declare una nueva |
| `LOGIN_REASIGNADO` | El login guardado ahora resuelve a una cuenta con identificador numérico distinto | Otra persona reclamó ese login; **exige siempre confirmación humana**, nunca se resuelve sola |
| `ESTUDIANTE_RETIRADO` | El estudiante titular del mapeo pasó a `RETIRADO` (§7.9.1) | El mapeo queda `INVALIDADO` con este motivo; si el estudiante se reincorpora, la revalidación siguiente lo puede devolver a `VIGENTE` sin pedir el dato de nuevo |
| `CUENTA_NO_ELEGIBLE` | La elegibilidad cruzada de §7.5 detectó una colisión posterior a la validación inicial | Abre la incidencia de §7.5.3, distinta de un conflicto entre estudiantes |

**Un estudiante retirado y una cuenta no elegible son hechos distintos que exigen acciones distintas del equipo docente**, y por eso no comparten motivo: al primero se le espera de vuelta sin pedirle nada otra vez; a la segunda se le pide una cuenta nueva. **Una invalidación nunca borra la fila**: se supersede (§7.2.2) y el histórico queda íntegro.

### 7.6.3 Conflictos entre dos estudiantes

**Que dos estudiantes del mismo curso no puedan tener vigente la misma cuenta de GitHub es un índice único parcial de base de datos** (§7.2.2), no sólo una comprobación en código: es la última línea de defensa contra el error más caro del proyecto, que un estudiante reciba el repositorio de otro. Antes de llegar a esa restricción, la ingesta comprueba y produce la incidencia `EN_CONFLICTO` con los dos candidatos y sus evidencias, visible en Pendientes (§7.8). **Ninguno de los dos estudiantes recibe repositorio hasta que un docente resuelva** cuál de los dos mapeos queda `VIGENTE`; el otro queda `NO_RESUELTO` con el motivo escrito para que reentregue.

### 7.6.4 Reenvíos y precedencia entre fuentes

- Un valor nuevo **reemplaza al anterior mientras el mapeo no esté vigente y confirmado**: no hay pérdida de trabajo, el estudiante simplemente corrigió.
- **Si ya estaba `VIGENTE` y ya existe repositorio creado, un reenvío nunca cambia nada en silencio.** Se abre incidencia —`GITHUB_DUPLICADO` si colisiona con otro estudiante, o incidencia de mapeo pendiente si sólo cambia el valor propio— para que el docente decida. Cambiar en silencio a quién pertenece un repositorio ya creado es inaceptable.
- **Toda corrección crea una fila nueva y supersede la anterior** (§7.2.2): el historial completo de quién declaró qué, cuándo y con qué evidencia queda siempre disponible, sin excepción por vía de origen.
- **Entre las cuatro vías de §7.4 no hay jerarquía de fuente**: gana siempre el **último** valor procesado en orden temporal, sea cual sea su vía, salvo que ese valor sea rechazado por elegibilidad (§7.5) o por conflicto (§7.6.3), en cuyo caso el mapeo vigente anterior —si lo había— no se toca hasta que el conflicto se resuelva.

### 7.6.5 Criterios de aceptación de §7.6

| Id | Criterio |
|---|---|
| CA-7.6-01 | El único valor terminal de `mapeo_github.estado` es `SUPERSEDIDO`; ningún otro estado impide una transición futura |
| CA-7.6-02 | Una cuenta renombrada en GitHub actualiza sola el mapeo `VIGENTE` correspondiente, sin abrir incidencia ni pedir nada al estudiante |
| CA-7.6-03 | Un login reasignado a otra persona nunca se adopta sin confirmación explícita de un docente |
| CA-7.6-04 | Un estudiante que se retira con mapeo `VIGENTE` queda `INVALIDADO` con `motivo_invalidacion = 'ESTUDIANTE_RETIRADO'`, nunca `SUPERSEDIDO` ni borrado |
| CA-7.6-05 | Dos estudiantes que declaran la misma cuenta producen `EN_CONFLICTO` para ambos y ninguno recibe repositorio hasta la resolución docente |
| CA-7.6-06 | Un reenvío sobre un mapeo `VIGENTE` con repositorio ya creado nunca cambia el colaborador del repositorio sin que un docente lo confirme |

---

## 7.7 Completado progresivo del mapeo por el equipo docente

**R2.2.5** exige un mecanismo para completar progresivamente las asociaciones que la vía automática no resolvió. Ese mecanismo son las vías 2, 3 y 4 de §7.4, que aquí se describen desde la perspectiva del flujo de trabajo del docente, no de la extracción de datos.

### 7.7.1 Cuándo se usa cada vía

**Edición manual (§7.4.3)** es la vía de un caso a la vez: un estudiante concreto que no respondió, o cuyo candidato quedó `NO_RESUELTO` o `EN_CONFLICTO`. **Importación CSV (§7.4.4)** es la vía de volumen: un profesor que ya tiene, fuera de la aplicación, la correspondencia estudiante–GitHub de todo un curso o de una sección, y prefiere cargarla de una vez. **Reintento asistido (§7.4.5)** no completa nada por sí mismo: empuja al estudiante de vuelta a la vía 1.

**Las tres son necesarias y ninguna sustituye a las otras dos**: siempre queda un caso que no se resuelve solo, y el equipo docente necesita tanto la herramienta fina como la de volumen.

### 7.7.2 Secuencia recomendada

La aplicación propone en pantalla, con casillas, la secuencia que hace usable el proceso completo:

1. Vincular el curso y ejecutar el checklist (capítulo 4).
2. Publicar la tarea de registro **y** un anuncio de curso explicando el proceso y por qué la invitación de GitHub es legítima.
3. Esperar 48 horas y revisar Pendientes (§7.8).
4. Enviar el reintento asistido (§7.4.5) a quien falte.
5. Dejar que los repositorios se creen solos a medida que llegan los mapeos: **no hay que esperar al 100 %**, porque la creación es progresiva por diseño (capítulo 8).
6. Revisar las invitaciones de GitHub sin aceptar a las 48 horas de creados los repositorios (§7.8.1).

### 7.7.3 Criterios de aceptación de §7.7

| Id | Criterio |
|---|---|
| CA-7.7-01 | Un docente puede resolver un `NO_RESUELTO` individual sin tener que preparar ni subir un CSV |
| CA-7.7-02 | Un CSV con una fila inválida entre filas válidas aplica las válidas y reporta la inválida, nunca rechaza el archivo entero |
| CA-7.7-03 | El botón de reintento asistido nunca crea directamente una fila de `mapeo_github`: sólo produce, cuando el estudiante responde, una entrega que sigue el circuito de la vía 1 |

---

## 7.8 Vista de información faltante: Pendientes

**R2.2.6** exige mostrar claramente al equipo docente los estudiantes o grupos para los que falta información. La respuesta arquitectónica es una sola pantalla, no un listado accesorio: es la primera que ve el docente al entrar a un curso con trabajo por hacer, tiene contador en la navegación, y lee la misma tabla de incidencias que alimenta el estado de repositorios (capítulo 8) y el informe diario (capítulo 11), de modo que **las tres vistas nunca se contradicen entre sí**.

### 7.8.1 Los cuatro bloques

| Bloque | Contenido | Estados que agrupa |
|---|---|---|
| **1. Sin cuenta de GitHub** | Estudiantes cuyo mapeo no está `VIGENTE` | `SIN_DATO`, `RECIBIDO` atascado, `NO_RESUELTO`, `NO_EXISTE`, `ES_ORGANIZACION` |
| **2. Cuentas en conflicto** | Colisiones entre estudiantes o con el equipo docente | `EN_CONFLICTO`, `INVALIDADO` con `LOGIN_REASIGNADO` o `CUENTA_NO_ELEGIBLE` |
| **3. Grupos incompletos** | Composición del padrón que impide o degrada el aprovisionamiento | `GRUPO_INCOMPLETO` (sus dos subtipos), `ESTUDIANTE_EN_DOS_GRUPOS`, integrantes `invited`/`requested`, estudiantes sin grupo |
| **4. Invitaciones sin aceptar** | Accesos de GitHub concedidos y aún no confirmados | Estados de `acceso_repositorio` del capítulo 8, citados aquí y no redefinidos |

Cada bloque tiene recuento, exportación en CSV con `curso.ver`, y acción directa por fila. **Ningún estado pendiente vive sólo dentro de una tarea**: si algo bloquea un repositorio, aparece aquí, a nivel de curso, además de en la pantalla de esa tarea.

### 7.8.2 Cabecera del curso y señal de progreso

La cabecera del curso muestra siempre **«N de M estudiantes con cuenta verificada»**, para que el equipo docente sepa de un vistazo si el enrolamiento va bien sin abrir nada. El denominador `M` es el total de estudiantes con `estudiante.estado ∈ {ACTIVO, INVITADO}` (§7.2.1); un estudiante `RETIRADO`, `INACTIVO` o `CONCLUIDO` no cuenta en ninguno de los dos números, por la misma razón que §7.9.7 fija para las métricas del capítulo 10: contar como pendiente a quien ya no está sería una injusticia visible.

### 7.8.3 Qué consume el capítulo 8 de esta vista

**El predicado de qué sujeto ya puede aprovisionarse no se redefine aquí.** El capítulo 8 (§8.5.2) consume como precondición «el estudiante tiene mapeo `VIGENTE`» o, en tareas grupales, «el grupo tiene al menos un integrante `accepted` con mapeo `VIGENTE`», y declara con un catálogo cerrado de siete motivos por qué un sujeto sigue esperando. Este capítulo es la fuente de esos hechos —el estado del mapeo, la composición del grupo—, no de la decisión de aprovisionar.

### 7.8.4 Criterios de aceptación de §7.8

| Id | Criterio |
|---|---|
| CA-7.8-01 | Todo estudiante con `mapeo_github.estado` distinto de `VIGENTE` aparece en el bloque 1 de Pendientes, sin excepción |
| CA-7.8-02 | Los cuatro bloques de Pendientes y la tabla de estado de repositorios del capítulo 8 nunca muestran, para el mismo hecho, dos estados contradictorios |
| CA-7.8-03 | La cabecera «N de M» excluye de ambos números a todo estudiante `RETIRADO`, `INACTIVO` o `CONCLUIDO` |
| CA-7.8-04 | Exportar el bloque 3 filtrado produce un CSV con las mismas columnas que se ven en pantalla |

---

## 7.9 Casos borde de alta, baja y cambio

### 7.9.1 Estudiante que se retira y vuelve

**La clave de identidad es `canvas_user_id`** (§7.2.4), y por eso la reincorporación siempre encuentra la **misma** fila de `estudiante`: no se crea una segunda. Un estudiante ausente del roster durante dos ciclos consecutivos de `sync_roster` pasa a `RETIRADO`; su mapeo `VIGENTE`, si lo tenía, pasa a `INVALIDADO` con `motivo_invalidacion = 'ESTUDIANTE_RETIRADO'` (§7.6.2). **Nada se borra**: matrícula, mapeo histórico, membresías de grupo pasadas y accesos ya concedidos quedan intactos.

Si el estudiante reaparece en el roster —misma `canvas_user_id`— `estudiante.estado` vuelve a `ACTIVO` en el mismo *upsert*, y la revalidación periódica del mapeo puede devolver la fila `INVALIDADO` a `VIGENTE` sin que nadie vuelva a pedirle su cuenta de GitHub, porque la evidencia original sigue siendo válida. Lo que ocurre con su repositorio y su acceso al reactivarse es la máquina 2 del capítulo 8, citada y no redefinida aquí.

**Si el estudiante vuelve con un `canvas_user_id` distinto** —una fusión de cuentas en Canvas, no una reincorporación—, se aplica §7.9.8, no esta regla.

### 7.9.2 Estudiante que cambia de sección

Un cambio de sección se refleja como una nueva `matricula` con distinto `seccion_id` en el ciclo de `sync_roster` que lo detecte; la matrícula anterior se actualiza según lo que Canvas devuelva para ella (§7.2.4). **El mapeo de GitHub del estudiante no se ve afectado en absoluto**: la identidad de la cuenta no depende de la sección. El efecto de un cambio de sección sobre la fecha de cierre de una entrega en curso —si un *override* de sección aplicable cambia— es regla del capítulo 9 y no se repite aquí.

### 7.9.3 Cambio de grupo o de conjunto de grupos a mitad de tarea

**El aprovisionamiento se detiene; nada se archiva ni se re-asocia por parecido.** Cuatro escenarios:

| Ocurre en Canvas | Efecto en el padrón |
|---|---|
| **Se elimina un grupo** del conjunto de grupos | `grupo.estado = 'ELIMINADO'` (§7.3.3); sus integrantes pasan a mostrarse como pertenecientes a un grupo eliminado en Pendientes. El efecto sobre el repositorio existente —pasa a `FUERA_DE_ALCANCE`, conserva todo, no se archiva— es del capítulo 8 |
| **Se elimina el conjunto de grupos completo** | Todos sus grupos siguen la regla anterior; la tarea que dependía de ese conjunto queda `INCONSISTENTE` (capítulo 9), con su propio aprovisionamiento detenido por completo |
| **Una entrega vinculada cambia a otro conjunto de grupos** | Misma consecuencia: tarea `INCONSISTENTE`, aprovisionamiento detenido, hasta intervención docente |
| **Una entrega vinculada cambia de individual a grupal, o al revés** | Misma consecuencia; la aplicación no reinterpreta sola una tarea que ya empezó a aprovisionarse |

**Ninguno de los cuatro se resuelve adivinando.** Re-asociar automáticamente un grupo eliminado con uno nuevo por coincidencia de integrantes arriesgaría entregar a unos estudiantes el repositorio de otros; el mismo razonamiento que exige confirmación humana ante una posible fusión de cuentas (§7.9.8) exige aquí intervención docente explícita. El detalle completo de esta detención — el predicado que la gobierna, la pantalla y sus dos botones — es del capítulo 9 (tareas y entregas), que este capítulo cita.

Un cambio de **composición** de un grupo ya existente —sin que el grupo mismo desaparezca— sigue la regla ordinaria de §7.3.4: alta automática, baja nunca automática.

### 7.9.4 Estudiante que cambia su cuenta de GitHub

Se trata como cualquier corrección: la fila vigente se supersede y se crea una nueva (§7.6.4, Ley 2). **Si el repositorio ya existe y el mapeo anterior estaba `VIGENTE`, el cambio no se aplica en silencio**: abre incidencia y espera confirmación docente antes de que el capítulo 8 reconcilie el colaborador saliente y el entrante en GitHub. Los commits ya subidos con la cuenta anterior conservan su atribución (§7.3.4): el historial de Git no se reescribe porque el mapeo cambió.

### 7.9.5 Cuenta de GitHub ya usada por otro estudiante

Es exactamente §7.6.3: el índice único parcial la impide en la base, la ingesta la detecta antes y abre `EN_CONFLICTO` con los dos candidatos, y **ninguno de los dos estudiantes recibe repositorio hasta que un docente resuelva** cuál mapeo queda `VIGENTE`.

### 7.9.6 Cuenta de GitHub ya usada por el equipo docente, en cualquier curso

Es §7.5 en su totalidad: la comprobación de elegibilidad no se acota al curso donde ocurre el intento, rechaza una cuenta con mapeo `VIGENTE` en **cualquier** curso de la aplicación, y produce un desenlace distinto según la comprobación llegue por una puerta con peticionario o por la ingesta (§7.5.3).

### 7.9.7 Estudiante retirado con mapeo vigente

Es el caso central de §7.9.1: el mapeo `VIGENTE` de un estudiante que se retira **no se borra ni se supersede por el retiro**; pasa a `INVALIDADO` con `motivo_invalidacion = 'ESTUDIANTE_RETIRADO'` (§7.6.2), conservando la evidencia de quién declaró qué cuenta y cuándo. Es distinto de una invalidación por `CUENTA_ELIMINADA` o `LOGIN_REASIGNADO`: aquí el problema no es la cuenta, es que su titular ya no es sujeto de aprovisionamiento (capítulo 8), y la fila queda lista para reactivarse sola si la persona vuelve.

### 7.9.8 Fusión de cuentas en Canvas

**`canvas_user_id` no es inmutable frente a una fusión de usuarios**, operación administrativa que borra el usuario origen y traslada sus matrículas al destino, sin que exista una señal fiable de que ocurrió. La aplicación:

1. **No borra nada.** El estudiante desaparecido sigue el circuito ordinario de retiro (§7.9.1): pasa a `RETIRADO` y conserva mapeo, repositorio y versiones capturadas.
2. Si aparece un `canvas_user_id` **nuevo** cuyo `login_id` o `sis_user_id` coincide con uno de un estudiante recién `RETIRADO`, se abre `POSIBLE_FUSION_CANVAS`, proponiendo migrar el mapeo y el repositorio de la fila antigua a la nueva.
3. **Un profesor o ayudante con `mapeo.editar` confirma antes de que se mueva nada.** Fusionar sin confirmación sería adivinar sobre la identidad de una persona a partir de una coincidencia parcial, y el coste de equivocarse es dar el repositorio de alguien a otra persona.

Si nadie confirma, las dos filas —la `RETIRADA` y la nueva— siguen su camino de forma independiente: la nueva entra en el circuito de enrolamiento como cualquier alta (§7.9.9), sin heredar nada de la antigua hasta que alguien lo decida.

### 7.9.9 Datos huérfanos e inconsistencias entre fuentes

**`sync_roster` es la única fuente de qué personas existen en el curso** (§7.2.5): ningún otro sincronizador crea estudiantes. Un `canvas_user_id` que aparece en grupos o en la tarea de registro y no existe todavía en `estudiante` **no se inserta como fila fantasma**, porque eso sería una segunda verdad sobre quién está en el curso. En su lugar se pone en cuarentena: se registra como huérfano con su fuente, se abre `ROSTER_TRUNCADO` —una sola incidencia por curso, con el detalle de todos los huérfanos dentro—, y se encola un `sync_roster` inmediato, una sola vez por ciclo, porque el caso más probable con diferencia es un roster desfasado por unos minutos. Si tras ese ciclo la persona sigue sin aparecer, la incidencia queda abierta con la acción «volver a sincronizar el roster», y **no se puede aprovisionar a quien no está en el roster**: la guarda del capítulo 8 exige un mapeo `VIGENTE` sobre un `estudiante` existente, y sin fila de `estudiante` no hay sujeto.

Una entrega de la tarea de registro cuyo `user_id` no resuelve a un estudiante del curso sigue la misma regla: **no crea mapeo**, se registra en bitácora y **no recibe comentario de respuesta**, porque responder a quien no es estudiante sería escribir a un desconocido. El *estudiante de prueba* de Canvas queda excluido siempre del roster, del padrón y de toda comunicación de este capítulo.

Cuando el listado de grupos contradice al roster —por ejemplo, un integrante de grupo que la matrícula ya no reconoce como activo—, **manda el roster**: el dato de grupos se persiste como contraste y la discrepancia abre una incidencia informativa, nunca bloquea la lectura de grupos en sí.

### 7.9.10 Conclusión masiva del curso

**Que Canvas concluya el término o una sección no ejecuta, por sí sola, ninguna acción destructiva.** El retiro individual de un estudiante nunca revoca accesos ni archiva repositorios por construcción (§7.9.1, capítulo 8); ese hecho por sí mismo ya impide que una conclusión masiva tenga efecto sobre GitHub. Además, **si en un ciclo más del 30 % de los estudiantes activos del curso cambia de estado a la vez**, no se aplica ninguna desactivación: se registra `sincronizacion.resultado = 'PARCIAL'`, se abre `ROSTER_SOSPECHOSO` con el recuento, y la pantalla pide **confirmación explícita de un profesor** antes de aplicar el cambio — la misma cautela de §7.3.8, extendida al cambio de estado y no sólo a la desaparición de filas.

**Mientras exista alguna corrección de ese curso sin publicar** (capítulo 12), los estudiantes desactivados por conclusión del término **siguen siendo visibles y corregibles** en las pantallas de ese proceso: ocultarlos en bloque justo cuando hay que corregir sería el daño que esta regla existe para evitar. Las fechas de fin de sección o de término no alteran, por sí mismas, el cálculo de una fecha de cierre (capítulo 9); lo único que cambia el estado de un estudiante es lo que Canvas devuelve para su matrícula.

### 7.9.11 Criterios de aceptación de §7.9

| Id | Criterio |
|---|---|
| CA-7.9-01 | Un estudiante que se retira y se reincorpora con el mismo `canvas_user_id` conserva su mapeo histórico y nunca produce una segunda fila de `estudiante` |
| CA-7.9-02 | Un conjunto de grupos eliminado detiene el aprovisionamiento de esa tarea sin archivar ningún repositorio existente |
| CA-7.9-03 | Un estudiante que cambia su cuenta de GitHub con repositorio ya creado no reconcilia el colaborador en GitHub hasta que un docente confirma el cambio |
| CA-7.9-04 | Una posible fusión de cuentas en Canvas nunca migra mapeo ni repositorio sin confirmación explícita de un profesor o ayudante con `mapeo.editar` |
| CA-7.9-05 | Un `canvas_user_id` que aparece en una entrega de la tarea de registro sin existir en el roster no crea mapeo ni recibe comentario de respuesta |
| CA-7.9-06 | Una conclusión de término que cambia de estado a más del 30 % de los estudiantes activos de un curso en un solo ciclo no se aplica sin confirmación explícita de un profesor |
| CA-7.9-07 | Ningún estudiante retirado aparece jamás como «sin participación» en las métricas de un capítulo distinto de éste |

---

## 7.10 Trazabilidad de requisitos

| Requisito | Dónde se especifica |
|---|---|
| **R2.2.1** | §7.2.1 (tablas espejo), §7.2.5 (jerarquía de fuentes y cuarentena), §7.3.1–§7.3.2 (proceso de sincronización), §7.9.1, §7.9.9, §7.9.10 (casos borde de alta, baja y datos inconsistentes) |
| **R2.2.2** | §7.2.1 (tabla `seccion`), §7.3.2 (ciclo de vida de secciones), §7.3.5 (estudiante en dos secciones), §7.9.2 (cambio de sección) |
| **R2.2.3** | §7.2.1 (tablas de grupos), §7.3.3–§7.3.4 (proceso de sincronización y reconciliación de pertenencias), §7.3.6–§7.3.7 (doble pertenencia, traslado), §7.9.3 (cambio de grupo a mitad de tarea) |
| **R2.2.4** | §7.2.2 (tablas del puente), §7.4 (las cuatro vías completas), §7.5 (elegibilidad en toda la aplicación), §7.6 (máquina de estados de `mapeo_github`), §7.9.4–§7.9.8 (casos borde de cuenta de GitHub) |
| **R2.2.5** | §7.4.3–§7.4.6 (vías complementarias), §7.7 (completado progresivo, secuencia recomendada) |
| **R2.2.6** | §7.2.6 criterio 3 (fila anticipada de `mapeo_github`), §7.8 (Pendientes, las cuatro bloques y la cabecera del curso) |
