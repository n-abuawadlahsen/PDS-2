# 8. Aprovisionamiento de repositorios

Este capítulo especifica cómo se crea una tarea vinculándola con una o más tareas ya existentes en Canvas, cómo cada una de esas tareas de Canvas se identifica como una entrega —parcial o final— de la tarea de la aplicación, cómo se determina si la tarea es individual o grupal, cómo se constituye el repositorio base opcional y sus archivos iniciales, el predicado exacto que determina cuándo un estudiante o un grupo está en condiciones de que se le cree su repositorio, la creación automática y **progresiva** de esos repositorios —sujeto a sujeto, a medida que su información se completa, nunca en lote y nunca por una acción de un usuario—, la incorporación automática de sus colaboradores, cómo se muestra al equipo docente el estado de creación y configuración de cada repositorio (incluidos los casos con información pendiente o con un problema que impide terminar el proceso), y el evento que hace que el estudiante reciba, a través de Canvas, lo necesario para acceder a su repositorio sin entrar nunca a la aplicación.

**Restricción que gobierna todo el capítulo.** El enunciado establece en §1 y repite en §2.3 que «la creación de estos repositorios no deberá depender de una acción realizada por los estudiantes», y **R2.3.10** exige además que ocurra «de forma automática, sin interacción directa de un usuario» — tampoco de un profesor o un ayudante. Ninguna regla de este capítulo exige que una persona pulse un botón para que un repositorio individual se cree; el único gesto humano posible en el camino normal es la configuración de la tarea, que ocurre una vez y antes de que exista ningún sujeto.

**Requisitos que satisface:**

- **R2.3.1** Crear una tarea en la plataforma vinculándola con una o más tareas ya creadas en Canvas.
- **R2.3.2** Identificar cada tarea de Canvas vinculada como una entrega de la tarea, pudiendo existir entregas parciales y una entrega final.
- **R2.3.3** Identificar la configuración de cada tarea según si en Canvas se encuentra como individual o grupal (todas las entregas asociadas a una misma tarea deben tener la misma configuración).
- **R2.3.4** Mantener un único conjunto de repositorios para todas las entregas asociadas a una misma tarea.
- **R2.3.5** Permitir al profesor crear desde la aplicación un repositorio base para una tarea (el repositorio base es opcional al momento de configurar la tarea).
- **R2.3.6** Incorporar y administrar los archivos iniciales que formarán parte del repositorio base.
- **R2.3.7** Crear automáticamente los repositorios correspondientes a los estudiantes o grupos de la tarea utilizando el repositorio base cuando corresponda.
- **R2.3.8** Asignar nombres automáticos e inequívocos a los repositorios creados.
- **R2.3.9** Incorporar automáticamente los estudiantes correspondientes a cada repositorio.
- **R2.3.10** Crear los repositorios progresivamente a medida que se disponga de toda la información requerida para cada estudiante o grupo. Esto debe hacerse de forma automática, sin interacción directa de un usuario.
- **R2.3.11** Mostrar claramente el estado de creación y configuración de todos los repositorios de una tarea, incluyendo aquellos casos en que exista información pendiente o algún problema que impida completar el proceso.
- **R2.3.12** Proporcionar al estudiante, a través de Canvas, la información necesaria para acceder al repositorio que le corresponde.

---

## 8.1 Cómo leer este capítulo

**Orden de precedencia aplicado, sin excepciones:** enunciado → carta de arquitectura (`A-nnn`) → actas de reconciliación (`RG-nnn`) → respuestas de alcance (`Q-2.3-nn`). `docs/ARQUITECTURA.md` es la **revisión 2** y es el documento más reciente: sus decisiones numeradas desde `A-180` en adelante ya incorporan, una por una, las correcciones que las actas de reconciliación introdujeron sobre la revisión 1. Donde una decisión antigua aparece marcada «ANULADA POR RG-nnn», este capítulo cita directamente la decisión vigente que la sustituye, nunca la anulada. Donde una acta contiene una regla de detalle que la revisión 2 no absorbió en una decisión `A-nnn` propia —composición del commit inicial, desglose del presupuesto por repositorio—, este capítulo cita la regla del acta porque no hay una `A-nnn` posterior que la contradiga.

**Qué no fija este capítulo, y dónde está.** El esquema completo de las tablas `tarea`, `entrega`, `sujeto`, `repositorio`, `repositorio_base` y `version_entrega` —todas sus columnas, sus claves y sus índices— se define en **§3** (modelo de datos); aquí se cita sólo el subconjunto de columnas del que dependen las reglas de negocio de este capítulo. El mecanismo HTTP exacto de cada llamada a la API de GitHub —qué *endpoint*, qué cabeceras, qué cuerpo, qué token— se define en **§6** (integración con GitHub); aquí se documenta únicamente cuándo se dispara esa llamada y con qué regla de negocio la gobierna. El motor genérico de trabajos en segundo plano —la cola sobre PostgreSQL, el planificador, el vigilante externo— se define en **§14** (infraestructura y despliegue); aquí se documenta la lógica de negocio específica del trabajo de aprovisionamiento: su predicado, su cadencia y el significado de sus reintentos. El mapeo entre un estudiante de Canvas y su cuenta de GitHub, con sus estados `SIN_DATO`/`VIGENTE`/etc., se define en **§7**; este capítulo lo **consume** como precondición del predicado de aprovisionamiento y no lo redefine. Las fechas de entrega, la fecha efectiva y la versión del repositorio registrada al cierre se definen en **§9**; este capítulo documenta la creación y la vida del repositorio **antes** del cierre, ese capítulo documenta qué ocurre **en** el cierre y después. El contenido exacto y la redacción de los mensajes que el estudiante recibe por Canvas se definen en **§11**; este capítulo documenta únicamente **qué evento** dispara esa comunicación.

**Correcciones de precedencia que este capítulo aplica y que conviene tener presentes desde el principio:**

| Punto | Lo que decía la respuesta o el acta | Lo que manda ahora | Fuente |
|---|---|---|---|
| Estado de un repositorio que deja de existir o de ser legible en GitHub | `HUERFANO`, con dos motivos (`ELIMINADO_EN_GITHUB`, `TRANSFERIDO_FUERA_DE_LA_ORGANIZACION`) | **`INACCESIBLE`**, con **cuatro** motivos: `BORRADO_EN_GITHUB`, `TRANSFERIDO_FUERA_DE_LA_ORG`, `FUERA_DEL_ALCANCE_DE_LA_INSTALACION`, `APP_SIN_ACCESO`. «Huérfano» queda reservado a `commit.huerfano` (historia reescrita) y no puede significar dos hechos distintos | RG-092 anulada por RG-013/RG-014/RG-015/RG-181 → **A-211** |
| Acción para reponer el repositorio de un sujeto cuyo repositorio desapareció | «Recrear»: reutiliza la **misma fila**, con `github_repo_id_anterior` y `recreado_por` | **«Sustituir»**: crea una **fila nueva** para el mismo sujeto, con `repositorio.reemplaza_a_id` apuntando a la anterior y `repositorio.recreado_en` en la nueva; la fila `INACCESIBLE` se conserva íntegra como evidencia y no se toca | RG-092 corregida por RG-014 (arbitraje cruzado) → **A-202** |
| Presupuesto de llamadas para aprovisionar un repositorio | Tres cifras publicadas por separado (`≤14`, `≤14`, `≤15`), sin distinguir si la tarea tiene repositorio base | **Una sola tabla**, con dos columnas —con base y sin base—: `≤16` llamadas con base, `≤13` sin base, para una tarea individual (más `2` por integrante adicional en una tarea grupal) | A-117 (revisión 1) → **RG-088** |
| Contenido inicial de un repositorio de estudiante cuando la tarea **no** declara repositorio base | No especificado más allá de «recibe un README.md inicial» | **Tres archivos exactos y ninguno más**, ninguno con fecha alguna: `README.md` personalizado por sujeto, `.gitignore` condicionado a `tarea.gitignore_template`, y `COMO-TRABAJAR.md` con el bloque de acceso y autenticación. Se escriben en un **único commit** por la Git Data API, a nombre de la cuenta `[bot]` de la instalación y nunca a nombre de un integrante del equipo docente | A-066 (revisión 1) → **RG-089, RG-090** |
| Espacio de cerrojo que serializa `aprovisionar_repositorios` frente a los demás trabajos del curso | Un cerrojo `(tipo, curso_id)` único, indistinto del que usan los trabajos que hablan con Canvas | **Dos espacios de cerrojo por curso, uno por proveedor**: `aprovisionar_repositorios` toma siempre `pg_advisory_lock(2, curso_id)` —el espacio de GitHub— y **nunca** el espacio `1` (Canvas), de modo que el aprovisionamiento de 600 repositorios no queda detrás de una sincronización lenta de Canvas | A-115 → **A-217** |
| Catálogo de trabajos en segundo plano que fija la cadencia y los reintentos de `aprovisionar_repositorios` | 27 trabajos | **31 trabajos**, cada uno con su fecha de entrada en servicio declarada; `aprovisionar_repositorios` conserva su fila, su cadencia y sus reintentos sin cambio, pero el catálogo que la gobierna es éste | A-114 → **A-218** |

**Vocabulario cerrado que este capítulo usa (A-154):** **sujeto**, **repositorio base**, **entrega**, **repositorio**, **incidencia**, **colaborador**. No se dice «alumno», «assignment» (a secas, sin calificarlo de «de Canvas»), «matching» ni «alerta». Todo estado interno se muestra traducido y **nunca aparece un identificador en mayúsculas en pantalla** (A-155).

---

## 8.2 Modelo estructural: tarea, entrega y sujeto (R2.3.1–R2.3.4)

El esquema completo de `tarea`, `entrega`, `visibilidad_entrega` y `sujeto` —todas sus columnas, unicidades e índices— se define en **§3**. Esta sección cita únicamente las columnas de las que dependen las reglas de negocio de R2.3.1 a R2.3.4.

### 8.2.1 Una tarea, una o más entregas de Canvas

**R2.3.1** se satisface porque `tarea` y `entrega` son entidades distintas: `entrega` tiene unicidad `(curso_id, canvas_assignment_id)` — una tarea de Canvas pertenece exactamente a una entrega de la aplicación y nunca a dos (A-080). Crear una tarea es, en su forma mínima, crear la fila de `tarea` y vincular al menos una tarea de Canvas como su primera entrega.

**R2.3.2** se satisface con `entrega.tipo ∈ {PARCIAL, FINAL}` y `entrega.orden`, con las siguientes reglas cerradas (A-080), sin excepción:

1. `orden` arranca en **1** y es **contiguo**: la n-ésima entrega vinculada recibe `orden = n`. Desvincular una entrega renumera el resto en la misma transacción, y esa renumeración sólo se permite mientras la tarea no tenga ninguna versión capturada (§9); después, desvincular queda prohibido y sólo cabe excluir la entrega.
2. **`FINAL` es siempre la de mayor `orden`.**
3. **Una tarea `ACTIVA` tiene exactamente una entrega `FINAL`** — ni cero ni dos. Una tarea en `BORRADOR` puede no tenerla todavía.
4. **La primera entrega vinculada nace `FINAL`.** Al vincular una segunda, la aplicación pregunta cuál de las dos es la final —con la anterior propuesta por defecto— y reordena. **Nunca lo decide en silencio.**

Una tarea con una sola entrega tiene esa única entrega como `FINAL` con `orden = 1`.

### 8.2.2 Modalidad: individual o grupal, una sola vez por tarea

**R2.3.3** exige que «todas las entregas asociadas a una misma tarea deben tener la misma configuración». La aplicación lo resuelve **estructuralmente** y no por comprobación: `tarea.modalidad ∈ {INDIVIDUAL, GRUPAL}` es una columna de `tarea`, no de `entrega` (A-080). Como la modalidad vive en la tarea y no en cada entrega, **es imposible representar dos entregas de la misma tarea con configuraciones distintas**: no hay ninguna combinación de filas que lo exprese.

`tarea.modalidad` se deriva de Canvas al vincular la primera entrega y **queda congelada tras el primer aprovisionamiento** (A-080): un cambio posterior de modalidad en Canvas no reescribe `tarea.modalidad` a mitad de tarea, porque eso invalidaría los sujetos —y los repositorios— ya creados. Ese caso (Canvas cambia la modalidad de un *assignment* después de que la tarea empezó a aprovisionarse) es el único que produce `tarea.estado = INCONSISTENTE`, y se documenta en 8.11.

### 8.2.3 `sujeto`: la unidad de aprovisionamiento

**R2.3.4** exige que todas las entregas de una tarea usen el mismo repositorio por estudiante o grupo. La aplicación lo satisface con una entidad intermedia, `sujeto`, que cuelga de **`tarea`** y de la que cuelga **`repositorio`** — nunca de `entrega` (A-081). Las versiones capturadas, en cambio, cuelgan de `(entrega, sujeto)` (§9): eso es lo que permite que dos entregas de la misma tarea compartan repositorio y a la vez tengan cada una su propia captura y su propia fecha.

`sujeto` es único por `(tarea_id, tipo, coalesce(estudiante_id, grupo_id))`, con `tipo ∈ {ESTUDIANTE, GRUPO}` derivado de `tarea.modalidad`, y un `CHECK` que exige que exactamente una de `estudiante_id`/`grupo_id` sea no nula (A-080, A-081).

### 8.2.4 Estado de la tarea y su relación con el aprovisionamiento

`tarea.estado ∈ {BORRADOR, ACTIVA, INCONSISTENTE, CERRADA, ARCHIVADA}` (A-080). El aprovisionamiento automático de repositorios opera sobre tareas `ACTIVA`; una tarea `BORRADOR` no tiene sujetos aprovisionándose porque la propia guarda de activación —§8.3— es la puerta de entrada. Cuando una tarea pasa a `INCONSISTENTE` por el cambio de modalidad que describe 8.2.2, los sujetos que aún no tienen repositorio quedan en `ESPERANDO_INFORMACION` con el motivo `TAREA_INCONSISTENTE` (A-094): el aprovisionamiento de sujetos **nuevos** se detiene, y **los repositorios ya creados no se tocan** (misma disciplina de A-030 que rige todo el sistema).

### Criterios de aceptación de 8.2

- **CA-8.2-01** Vincular una segunda tarea de Canvas a una tarea de la aplicación con `tarea.modalidad = INDIVIDUAL` que en Canvas está configurada como grupal es rechazado con un mensaje que explica la incompatibilidad, y no se crea la entrega.
- **CA-8.2-02** Desvincular la entrega `orden = 2` de una tarea con tres entregas deja las restantes con `orden = 1` y `orden = 2`, en la misma transacción.
- **CA-8.2-03** Intentar desvincular una entrega de una tarea que ya tiene alguna versión capturada es rechazado; la única acción disponible es excluirla.
- **CA-8.2-04** Tras vincular una segunda entrega sin que el profesor responda cuál es la final, la aplicación no completa la operación: no existe un estado intermedio con cero o dos entregas `FINAL`.
- **CA-8.2-05** Una consulta a `repositorio` para dos entregas distintas de la misma tarea y el mismo sujeto devuelve **la misma fila**.

---

## 8.3 Repositorio base y contenido inicial (R2.3.5, R2.3.6)

### 8.3.1 El repositorio base lo crea siempre la aplicación

**R2.3.5** dice literalmente «permitir al profesor crear **desde la aplicación** un repositorio base». Por eso **no se acepta vincular un repositorio base creado a mano** (A-066): la garantía de acceso automático de la instalación de la GitHub App sólo cubre lo que la propia aplicación crea, y aceptar uno externo reintroduciría el modo de fallo más difícil de diagnosticar del sistema —un aprovisionamiento que falla con `404` sin que el profesor entienda por qué—.

**El repositorio base es opcional**, tal como exige **R2.3.5**: `tarea.repositorio_base_id` es *nullable*, y una tarea sin base no tiene fila en `repositorio_base` — no existe el valor «no solicitado» (A-208). Si la tarea no declara base, los repositorios de cada sujeto se crean vacíos, con el contenido inicial que describe 8.3.4.

**Es una escritura síncrona desde la pantalla de tarea**, no un trabajo de cola: crear el repositorio base (`POST /orgs/{org}/repos` + `PATCH is_template`, §6) es la entrada 2 de las seis escrituras externas síncronas de la aplicación, y administrar sus archivos (8.3.3) es la entrada 3 (A-226). Las dos comparten el mismo contrato: lectura previa del efecto antes de producirlo, intención persistida en la misma transacción, un tope duro de 20 segundos de espera tras el cual la operación se convierte en trabajo de cola sin perderse, el resultado en pantalla con el error literal del proveedor si lo hubo, y registro en `bitacora`. **Ninguna de las seis envía comunicación a un estudiante.**

### 8.3.2 Máquina de estados de `repositorio_base`

`repositorio_base.estado` es un enum cerrado de **cinco** valores, `DEFAULT 'CREANDO'` (A-208):

| Estado | Se entra cuando | Sale a |
|---|---|---|
| `CREANDO` | Se lanzó la escritura síncrona de creación (o su degradación a trabajo de cola) | `CREADO_VACIO`, `ERROR` |
| `CREADO_VACIO` | `POST /orgs/{org}/repos` devolvió `201`, `PATCH is_template=true` respondió `200`, y el árbol sólo tiene el README de `auto_init` | `LISTO`, `INACCESIBLE` |
| `LISTO` | El árbol tiene al menos un archivo más que el README de `auto_init`, y `es_plantilla = true` verificado | `CREADO_VACIO` (el profesor borró los archivos), `INACCESIBLE` |
| `ERROR` | Fallo permanente al crear: nombre ocupado por un tercero que no supera las cinco condiciones de adopción (8.6.5), o la organización prohíbe crear | `CREANDO`, por acción explícita con `tarea.administrar` |
| `INACCESIBLE` | Webhook `repository` con acción `deleted` o `transferred` sobre el base, o dos ciclos consecutivos de `404`/`403` | `LISTO` o `CREADO_VACIO`, por comprobación positiva |

**La guarda de activación de la tarea usa este catálogo:** `BORRADOR → ACTIVA` exige `repositorio_base.estado = 'LISTO'` **sólo si la tarea declara repositorio base**; una tarea sin base se activa sin ninguna comprobación de base, porque convertirlo en requisito universal añadiría una exigencia que el enunciado no pone (A-208). El botón «Activar tarea» se muestra deshabilitado con el motivo escrito mientras el base declarado no esté `LISTO`.

**Con el base en `ERROR` o `INACCESIBLE`, el aprovisionamiento de los sujetos de esa tarea se detiene**, con el motivo escrito en pantalla — la operación de generación fallaría repositorio a repositorio —, y **los repositorios ya creados no se ven afectados**, porque la copia desde el repositorio base ocurre una sola vez por sujeto. **La tarea no pasa a `INCONSISTENTE`** por esta causa: ese estado queda reservado al cambio de modalidad de 8.2.4 (A-208).

`repositorio_base.rama_por_defecto` se lee siempre del campo `default_branch` de la respuesta `201` y **nunca se supone `main`** (A-068): la documentación no dice si el repositorio generado hereda la rama del repositorio base o el ajuste de la organización, y todo el monitoreo de actividad depende de ese nombre.

### 8.3.3 Archivos iniciales del repositorio base

**R2.3.6** se satisface con una pantalla propia del repositorio base: árbol de archivos, subir, reemplazar, renombrar, borrar y previsualizar texto (A-067). Cada operación es una escritura síncrona (8.3.1) y queda en `bitacora`. **Los cambios en el repositorio base no se propagan a los repositorios ya creados**: la copia hacia cada sujeto ocurre una sola vez, en el momento de su aprovisionamiento — la pantalla lo advierte explícitamente.

### 8.3.4 Contenido cuando la tarea no declara repositorio base

Cuando la tarea **no** tiene repositorio base, cada repositorio de sujeto se crea con `auto_init: false` y la aplicación escribe, mediante la Git Data API (§6 para el detalle HTTP), **un único commit inicial** cuyo SHA se persiste en `repositorio.commit_inicial_sha`. El árbol de ese commit contiene **exactamente tres archivos y ninguno más** (RG-089):

1. **`README.md`**, generado por la aplicación y personalizado por sujeto: nombre del curso, nombre de la tarea, nombre del estudiante o del grupo con sus integrantes, nombre exacto del repositorio, enlace a la tarea en Canvas y la línea que pide no borrar ni renombrar el repositorio.
2. **`.gitignore`**, sólo si el profesor eligió uno al configurar la tarea (`tarea.gitignore_template`), resuelto desde una lista fija.
3. **`COMO-TRABAJAR.md`**, con el bloque de acceso y autenticación: cómo llega la invitación, por qué la URL mostrará «no encontrado» hasta aceptarla, qué hacer si el correo no llega, y el tramo de autenticación con Git.

**Ninguno de los tres archivos lleva fecha alguna.** Las fechas de entrega cambian (**R2.4.4**, §9) y un archivo con una fecha obsoleta es peor que uno sin fechas; la fecha de cierre efectiva viaja donde ya viaja: en el mensaje de **R2.3.12** (8.10) y en el anuncio de curso. Cuando la tarea **sí** tiene repositorio base, nada de esto se ejecuta: `COMO-TRABAJAR.md` se precarga en el base por la pantalla de 8.3.3, y la generación desde plantilla lo copia sin coste adicional (RG-089).

**El commit inicial se escribe siempre a nombre de la cuenta `[bot]` de la instalación**, nunca a nombre de un integrante del equipo docente: la llamada de creación del commit no envía identidad de autor ni de *committer* (RG-090, mecanismo en §6). Esto tiene tres consecuencias que ya sostienen otras decisiones del sistema: el commit inicial nunca cuenta como participación de un estudiante (§10, A-118), el timeline lo etiqueta como commit de la aplicación (§10), y el estudiante ve con claridad que quien creó su repositorio fue la aplicación del curso, reconocible y distinguible de una suplantación.

**Camino alternativo, declarado de antemano.** Si la Git Data API no estuviera disponible con el conjunto de permisos congelado de la instalación, se usa `POST /orgs/{org}/repos` con `auto_init: true` y `gitignore_template`, que produce igualmente un único commit, a costa de un `README.md` genérico sin guía dentro del repositorio; en ese caso la guía viaja sólo por Canvas y la pantalla de la tarea lo declara: «los repositorios de esta tarea se crearon con el contenido mínimo de GitHub» (RG-089).

### Criterios de aceptación de 8.3

- **CA-8.3-01** Configurar una tarea sin repositorio base y activarla no exige ninguna comprobación sobre `repositorio_base`; el botón «Activar tarea» está habilitado en cuanto se cumplen las demás condiciones.
- **CA-8.3-02** Configurar una tarea con repositorio base y dejarlo en `CREADO_VACIO` (sin subir ningún archivo) mantiene el botón «Activar tarea» deshabilitado con el motivo «el repositorio base no tiene contenido» visible.
- **CA-8.3-03** Poner el repositorio base en `ERROR` detiene la creación de nuevos repositorios de sujeto para esa tarea, sin afectar a los ya creados, y sin mover `tarea.estado` a `INCONSISTENTE`.
- **CA-8.3-04** Un repositorio de sujeto creado sin repositorio base tiene exactamente un commit en su rama por defecto antes de cualquier trabajo del estudiante, con tres archivos en el árbol —o dos, si `tarea.gitignore_template` es nulo—, y ninguno contiene una fecha.
- **CA-8.3-05** El autor y el *committer* del commit inicial, leídos con la API de GitHub, resuelven a la cuenta de la GitHub App instalada, nunca a un profesor o ayudante del curso.
- **CA-8.3-06** Reemplazar un archivo del repositorio base después de que existan diez repositorios de estudiantes no modifica ninguno de esos diez.

---

## 8.4 Convención de nombres de repositorios (R2.3.8)

Esta sección reproduce íntegra la regla de nomenclatura fijada en ARQUITECTURA.md §10 (A-107 a A-111), porque **R2.3.8** exige nombres «automáticos e inequívocos» y la exactitud del algoritmo es normativa, no ilustrativa.

### 8.4.1 Plantilla del nombre

```
<curso.slug>-<tarea.slug>-<sujeto>

  <curso.slug>  slug del curso, ÚNICO GLOBALMENTE, <= 24 caracteres      p. ej.  icc4201-202620
  <tarea.slug>  slug de la tarea, único por curso, <= 24 caracteres      p. ej.  t1-ordenamiento
  <sujeto>      individual:  e<canvas_user_id>-<apellido-nombre>   legible <= 24
                grupal:      g<canvas_group_id>-<slug-grupo>       legible <= 24
                base:        base
```

(A-107)

**Ejemplos reales, calculables sin consultar nada** (con `curso.slug = icc4201-202620`):

| Caso | Nombre resultante | Longitud |
|---|---|---|
| Ana Gómez (`canvas_user_id` 5310), tarea 1 individual | `icc4201-202620-t1-ordenamiento-e5310-gomez-ana` | 46 |
| Grupo «Equipo 04» (`canvas_group_id` 8842), tarea 2 grupal | `icc4201-202620-t2-compilador-g8842-equipo-04` | 44 |
| Repositorio base de la tarea 1 | `icc4201-202620-t1-ordenamiento-base` | 35 |
| Estudiante con nombre íntegramente en escritura no latina, `canvas_user_id` 5310 | `icc4201-202620-t1-ordenamiento-e5310` | 36 |

### 8.4.2 Normalización y ensamblado, verificable paso a paso

`normalizar(texto)` se aplica **por componente**, nunca al nombre ya ensamblado (A-108):

1. Descomponer a `NFKD` y descartar las marcas diacríticas (`ñ` → `n`, tildes eliminadas).
2. Pasar a minúsculas.
3. Sustituir todo lo que no sea `[a-z0-9]` por `-`.
4. Colapsar guiones consecutivos.
5. Recortar guiones de los extremos.
6. **Truncar a 24 caracteres.**
7. **Volver a recortar guiones de los extremos**, porque el truncado del paso 6 puede haber caído justo sobre un guion.

Ensamblado:

8. Los **identificadores numéricos nunca se truncan** ni pasan por `normalizar`: `e5310`, `g8842` se escriben tal cual.
9. **Si el componente legible queda vacío** tras normalizar —un nombre íntegramente en escritura no latina, un grupo llamado «★»— **se omite entero, incluido su guion separador**: el sujeto queda como `e<canvas_user_id>` o `g<canvas_group_id>` a secas. **Nunca se produce `…-e5310-`**. La inequivocidad la aporta el identificador de Canvas, no la parte legible.
10. Se unen los componentes con `-` y se recortan guiones de los extremos del nombre completo una última vez.
11. Por construcción, el nombre nunca supera **90 caracteres** (`24 + 1 + 24 + 1 + 1 + 10 + 1 + 24`). Si aun así el ensamblado superase esa cota, se recorta el componente legible del sujeto hasta que quepa; si aun así no cupiera, se omite según el paso 9. **Nunca se recorta un identificador numérico y nunca se añade un sufijo.**

La parte legible del sujeto se deriva de `estudiante.nombre_ordenable` (apellido y nombre), no del nombre de pila suelto. `curso.codigo` (≤ 12 caracteres normalizados), `curso.periodo` (exactamente 6 caracteres) y `curso.slug` (≤ 24, forma `^[a-z0-9][a-z0-9-]*[a-z0-9]$`, único globalmente, editable por el profesor al crear el curso) se validan en el alta del curso, que es donde el problema de unicidad se paga una sola vez (A-108).

### 8.4.3 Por qué el identificador de Canvas y no el login de GitHub

La inequivocidad que exige **R2.3.8** la aporta `canvas_user_id` / `canvas_group_id`, no la parte legible ni el login de GitHub (A-109). Usar el login (`…-agomez`) queda descartado: el login puede cambiar y **el antiguo queda libre para que otra persona lo reclame**; como el nombre del repositorio no cambia nunca (8.4.4), un nombre construido sobre el login podría acabar designando a otra persona. Usar sólo el nombre de la persona queda descartado por los homónimos. Usar `sis_user_id` queda descartado porque puede no venir con el rol de profesor del equipo (§7).

### 8.4.4 El nombre no cambia nunca después de la creación

Aunque el estudiante renombre su cuenta de GitHub, aunque el profesor renombre la tarea, aunque cambie el nombre del grupo en Canvas (A-110). Renombrar rompería las URL ya enviadas por Canvas (**R2.3.12**) y las que los correctores tengan guardadas, a cambio de nada: la identidad viva está en `github_repo_id`, el nombre es una etiqueta estable. Si alguien renombra el repositorio directamente en GitHub, el webhook correspondiente actualiza `nombre` y `full_name` (§6), los enlaces se reconstruyen y nada se rompe, porque nada depende del nombre.

### 8.4.5 Colisión de nombre: nunca se añade sufijo

**No se sufija `-2`, `-3`** (A-111). Un sufijo destruiría la inequivocidad que **R2.3.8** exige y produciría dos nombres válidos para el mismo sujeto. Como el nombre incluye el identificador de Canvas, una colisión sólo puede significar dos cosas: el repositorio ya existe para ese mismo sujeto —reintento tras un fallo parcial—, resuelto por la adopción segura de 8.6.5; o hay una anomalía real, resuelta con `ERROR_PERMANENTE` y subtipo `NOMBRE_OCUPADO_POR_TERCERO` (8.11.3). La unicidad se refuerza con el índice `(curso_id, nombre)` y con la unicidad global de `curso.slug`, que es lo que impide que dos cursos distintos produzcan el mismo nombre.

### Criterios de aceptación de 8.4

- **CA-8.4-01** El nombre calculado para Ana Gómez (`canvas_user_id` 5310, tarea `t1-ordenamiento`, curso `icc4201-202620`) es exactamente `icc4201-202620-t1-ordenamiento-e5310-gomez-ana`.
- **CA-8.4-02** Un estudiante con nombre íntegramente en escritura no latina produce un nombre de repositorio terminado en el identificador numérico, sin guion colgante.
- **CA-8.4-03** Renombrar la cuenta de GitHub de un estudiante después de creado su repositorio no cambia el nombre del repositorio.
- **CA-8.4-04** Dos cursos con el mismo código y el mismo período no pueden tener el mismo `curso.slug`: el segundo alta lo rechaza y pide un slug distinto, nunca sufija uno automáticamente.
- **CA-8.4-05** El normalizador tiene pruebas automatizadas para: nombre con tildes y `ñ`; nombre íntegramente en escritura no latina; nombre que trunca justo sobre un guion; componente que queda vacío tras normalizar; y dos cursos distintos que no pueden producir el mismo nombre de repositorio.

---

## 8.5 El predicado de aprovisionamiento (R2.3.7, R2.3.9, R2.3.10)

### 8.5.1 Quién es sujeto de una tarea

Antes de que exista ningún repositorio, la aplicación tiene que decidir **para quién** lo crea. Esa decisión ocurre en dos pasos (A-164):

**Paso 1 — visibilidad, por entrega y por estudiante.** Para cada entrega vinculada se puebla `visibilidad_entrega`:

| Situación de la entrega en Canvas | Quién queda visible |
|---|---|
| `only_visible_to_overrides = false` | Todo estudiante del curso con matrícula `ACTIVO` o `INVITADO` |
| `only_visible_to_overrides = true` y la instancia devolvió `assignment_visibility` | Exactamente los `canvas_user_id` de ese arreglo |
| `only_visible_to_overrides = true` sin `assignment_visibility` | Los estudiantes alcanzados por algún `AssignmentOverride` de esa entrega |
| Ninguna de las anteriores resoluble | Nadie, y se abre incidencia `VISIBILIDAD_NO_RESOLUBLE` |

**No se supone visibilidad universal** cuando `only_visible_to_overrides` es verdadero: suponerla crearía repositorios a estudiantes a los que la entrega no aplica, y borrarlos después está prohibido.

**Paso 2 — materialización del sujeto.** El conjunto de sujetos de una tarea es:

- **Tarea `INDIVIDUAL`:** un sujeto por cada `estudiante` con matrícula `ACTIVO` o `INVITADO` que además sea visible en **al menos una** de las entregas vinculadas.
- **Tarea `GRUPAL`:** un sujeto por cada grupo del conjunto de grupos de la tarea que tenga al menos un integrante `accepted` que a su vez cumpla las dos condiciones anteriores.

**Por qué «al menos una entrega» y no «todas».** **R2.3.4** obliga a que todas las entregas de una tarea compartan el mismo conjunto de repositorios; exigir la intersección de visibilidad dejaría sin repositorio a estudiantes que sí deben entregar algo en alguna de ellas, incumpliendo **R2.3.7**. La unión no crea ningún efecto indebido porque la fecha efectiva y la captura se calculan por `(entrega, sujeto)` (§9): un sujeto no visible para una entrega concreta no recibe fecha efectiva ni se le captura versión en ella. La unión da repositorio; la visibilidad por entrega decide qué se le exige en cada una.

**Paso 3 — altas y bajas, que es lo que hace real R2.3.10.** El conjunto de sujetos de un curso se recalcula tras cada sincronización de padrón, de grupos o de tareas y fechas:

- **Sujeto nuevo** (matrícula nueva, grupo nuevo, *override* que le da visibilidad, mapeo que llega tarde): se inserta activo y entra directamente en la guarda de 8.5.2, **sin que nadie pulse nada**.
- **Sujeto que deja de cumplir la regla:** nunca se borra. Pasa a inactivo con un motivo (`SIN_MATRICULA_ACTIVA`, `SIN_VISIBILIDAD`, `GRUPO_DISUELTO`, `GRUPO_SIN_ACEPTADOS`), y su repositorio —si ya existía— pasa a `FUERA_DE_ALCANCE` conservando todo (8.11.1). Si vuelve a cumplirla, se reactiva la misma fila.

### 8.5.2 La guarda: cuándo un sujeto pasa de «esperando» a «listo para crear»

Esta guarda decide **cuándo** se aprovisiona un sujeto que ya fue materializado por 8.5.1 — decide *cuándo*, no *quién* (A-093):

- **Tarea individual:** el estudiante tiene mapeo de GitHub `VIGENTE` (§7, precondición que este capítulo consume y no redefine) y ninguna incidencia bloqueante que le afecte.
- **Tarea grupal:** el grupo tiene **al menos un integrante `accepted` con mapeo `VIGENTE`** y ninguna incidencia bloqueante sobre el grupo. Los demás integrantes se incorporan progresivamente a medida que su propio mapeo se resuelve (8.8).

Esto es literalmente **R2.3.10**: el repositorio se crea en cuanto hay **un** integrante con cuenta de GitHub conocida, no cuando todos la tienen, porque exigir el conjunto completo dejaría sin repositorio a un grupo entero por causa de uno solo de sus integrantes.

**El motivo por el que un sujeto sigue esperando siempre se declara**, con un catálogo cerrado de **siete** valores persistidos (A-094): `SIN_MAPEO_GITHUB`, `MAPEO_EN_CONFLICTO`, `SIN_GRUPO_ASIGNADO`, `GRUPO_SIN_INTEGRANTES_ACEPTADOS`, `ESTUDIANTE_EN_DOS_GRUPOS`, `TAREA_INCONSISTENTE` y `CURSO_EN_SOLO_LECTURA` (este último cuando `curso.modo_escritura = 'SOLO_LECTURA'`, 8.11.6). Un estado «pendiente» sin causa no satisface **R2.2.6** ni **R2.3.11**, que exigen mostrar *claramente* qué falta.

### Criterios de aceptación de 8.5

- **CA-8.5-01** Un grupo de cuatro integrantes en el que sólo uno tiene mapeo de GitHub `VIGENTE` tiene repositorio creado; los otros tres integrantes se incorporan como colaboradores conforme su mapeo se resuelve, sin recrear el repositorio.
- **CA-8.5-02** Un estudiante que se matricula el día 20 de un curso cuya tarea 1 ya tiene 150 repositorios creados obtiene el suyo sin que se toque ninguno de los 150.
- **CA-8.5-03** Un estudiante que pierde su matrícula activa deja de ser sujeto activo de la tarea, y su repositorio —si existía— queda en `FUERA_DE_ALCANCE` con toda su historia intacta.
- **CA-8.5-04** Una entrega con `only_visible_to_overrides=true` cuya visibilidad no puede resolverse por ninguna de las tres vías abre la incidencia `VISIBILIDAD_NO_RESOLUBLE` y no crea repositorio para nadie a partir de esa entrega en solitario.
- **CA-8.5-05** Un sujeto en `ESPERANDO_INFORMACION` muestra siempre uno de los siete motivos cerrados; no existe una fila «pendiente» sin motivo escrito en ninguna pantalla.

---

## 8.6 La máquina de estados del repositorio (R2.3.7, R2.3.9, R2.3.10, R2.3.11)

Es la máquina de estados más importante de este capítulo: gobierna la vida completa de un repositorio de sujeto desde que se materializa hasta que queda operativo, fuera de alcance, inaccesible o archivado. Tiene **quince** estados (A-092 corregida por A-211).

### 8.6.1 Tabla completa de estados y transiciones

| Estado | Se entra cuando | Sale a |
|---|---|---|
| `ESPERANDO_INFORMACION` | El sujeto existe pero no se cumple la guarda de 8.5.2 | `LISTO_PARA_CREAR` |
| `LISTO_PARA_CREAR` | Se cumple la guarda | `CREANDO` |
| `CREANDO` | El trabajo tomó el sujeto y llamó a GitHub | `CREADO_SIN_CONTENIDO`, `BLOQUEADO`, `ERROR_TRANSITORIO`, `ERROR_PERMANENTE` |
| `CREADO_SIN_CONTENIDO` | Respuesta `201`, contenido aún no observado | `CONTENIDO_LISTO` |
| `CONTENIDO_LISTO` | Se observó el commit inicial, o venció el sondeo acotado | `CONFIGURANDO_ACCESOS` |
| `CONFIGURANDO_ACCESOS` | Se emiten las invitaciones de colaborador de los estudiantes **y** se concede la lectura al equipo docente | `OPERATIVO`, `DEGRADADO`, `ERROR_TRANSITORIO` |
| `OPERATIVO` | Se cumple el predicado íntegro de 8.6.2 | `DEGRADADO`, `FUERA_DE_ALCANCE`, `ARCHIVADO` |
| `DEGRADADO` | Se niega el predicado y el repositorio existe y es usable | `CONFIGURANDO_ACCESOS`, `OPERATIVO`, `FUERA_DE_ALCANCE`, `ARCHIVADO` |
| `BLOQUEADO` | Política de la organización, permisos pendientes, o cupo agotado | `LISTO_PARA_CREAR` al desaparecer la causa, reevaluado cada 30 min |
| `ESPERANDO_LIMITE` | Límite de GitHub alcanzado | Vuelve al estado previo. **Nunca se pinta como error** |
| `ERROR_TRANSITORIO` | Fallo clasificado transitorio | Reintenta con retroceso exponencial, hasta 8 intentos en ~2 h |
| `ERROR_PERMANENTE` | Error clasificado no transitorio | Sólo por acción explícita del docente, con destino según subtipo (8.11.3) |
| `FUERA_DE_ALCANCE` | El sujeto se desactivó por la regla de 8.5.1, paso 3 | `OPERATIVO` o `DEGRADADO` si el sujeto vuelve a estar en alcance |
| `INACCESIBLE` | Ver 8.11.1 | Comprobación positiva, o sustitución explícita (8.11.4) |
| `ARCHIVADO` | Acción explícita del profesor, o webhook que informa de archivado en GitHub | Sólo a `OPERATIVO`/`DEGRADADO` por desarchivado explícito |

**Transición universal hacia `INACCESIBLE`, válida desde cualquier estado con identificador de GitHub ya asignado** —`CREADO_SIN_CONTENIDO`, `CONTENIDO_LISTO`, `CONFIGURANDO_ACCESOS`, `OPERATIVO`, `DEGRADADO`, `FUERA_DE_ALCANCE` y `ARCHIVADO`—: el repositorio puede dejar de existir o de ser legible en cualquiera de esos siete estados, y la tabla de arriba no la repite en cada fila para no perder legibilidad. Los motivos y la salida se documentan en 8.11.1 y 8.11.2.

`ARCHIVADO` cierra la máquina para el trabajo docente ya entregado; sus reglas de entrada, quién puede archivar y qué implica exactamente pertenecen al ciclo de cierre de la tarea y a su gobierno de permisos, fuera del alcance de este capítulo.

### 8.6.2 El predicado de `OPERATIVO`, escrito una sola vez

Un repositorio está **`OPERATIVO`** si y sólo si se cumplen las **tres** condiciones (A-092):

1. **Existe y su contenido está resuelto** — se alcanzó `CONTENIDO_LISTO`.
2. **Cobertura de estudiantes:** para cada integrante `accepted` del grupo (o para el único estudiante, si la tarea es individual) existe una fila de acceso con estado `ACEPTADO` o `ACCESO_DIRECTO` (8.8); **y** no hay ningún integrante `invited` o `requested` en Canvas todavía pendiente.
3. **Acceso docente:** el equipo docente tiene lectura concedida sobre el repositorio (§6 para el mecanismo, esta sección lo consume como precondición).

Cualquier otra situación en la que el repositorio exista es **`DEGRADADO`**, con un motivo obligatorio de esta lista cerrada: `FALTA_ACEPTAR_INVITACION_GITHUB`, `INVITACION_EXPIRADA`, `INTEGRANTE_SIN_MAPEO`, `INTEGRANTE_PENDIENTE_EN_CANVAS`, `SIN_ACCESO_DOCENTE`, `ERROR_AL_CONCEDER_ACCESO`.

**`DEGRADADO` no es un error y la interfaz no lo pinta como tal.** Su etiqueta es «Listo, falta gente por entrar», en ámbar y no en rojo: el repositorio funciona, el estudiante que ya entró puede trabajar, y lo que falta está nombrado. Es el estado normal de un repositorio recién creado. Por eso el aviso de **R2.3.12** (8.10) **no** cuelga de `OPERATIVO`: colgarlo de ahí equivaldría a no enviar nunca el mensaje que explica cómo aceptar la invitación cuya aceptación se está esperando.

**Consecuencia que se propaga a toda vista de conteo:** `OPERATIVO` y `DEGRADADO` se cuentan **por separado** y **nunca se suma `DEGRADADO` a la columna de problemas** (8.9).

**Cuándo se repara sin cambiar de estado.** `DEGRADADO → CONFIGURANDO_ACCESOS` tiene un único disparador: aparece un miembro del conjunto objetivo de accesos que todavía no tiene ninguna fila de acceso. En cualquier otro caso la reparación ocurre **sin transición**: una invitación reenviada, una invitación que por fin se acepta, o el acceso docente que se concede tras existir la fila, mueven el repositorio directamente `DEGRADADO → OPERATIVO` en cuanto el predicado se cumple entero, sin pasar de nuevo por `CONFIGURANDO_ACCESOS` (A-211).

### 8.6.3 El sondeo de contenido tras la creación, acotado y sin producir error

Cuando la tarea tiene repositorio base, la copia de contenido se comprueba con un sondeo de retroceso —no a cadencia fija— y con tope duro de **8 sondeos** (2 s, 2 s, 5 s, 5 s, 10 s, 10 s, 30 s, 30 s; 94 s acumulados) sobre el estado del árbol (A-096, mecanismo en §6). Si aparece el commit inicial, se guarda `commit_inicial_sha` y se pasa a `CONTENIDO_LISTO`. **Si se agotan los ocho sondeos, se pasa igualmente a `CONTENIDO_LISTO`**, con `commit_inicial_sha` nulo, una incidencia informativa, y la resolución delegada al reconciliador (§10). **La creación no se reintenta nunca por esta causa: el repositorio ya existe.**

Cuando la tarea **no** tiene base, el commit inicial se escribe sincrónicamente por la propia aplicación (8.3.4) y no requiere este sondeo.

### 8.6.4 Clasificación de errores y qué ve el docente

Todo fallo de una llamada a GitHub durante el aprovisionamiento se clasifica en una de **tres familias**, y la familia decide tanto el comportamiento como lo que el docente ve (A-116):

| Familia | Comportamiento | Qué ve el docente |
|---|---|---|
| **TRANSITORIO** (`429`, `5xx`, tiempo agotado, `403` de límite secundario, `404` durante la ventana de creación) | Retroceso exponencial con variación aleatoria, hasta el tope del trabajo | «Reintentando, próximo intento a las HH:MM» |
| **BLOQUEANTE** (política de la organización, permisos pendientes, cupo de invitaciones agotado) | Estado `BLOQUEADO` o `ESPERANDO_LIMITE`; no se reintenta en bucle; se reevalúa cada 30 min o cuando cambia la condición | «Esperando a GitHub por límite de uso. Reintento automático a las HH:MM» / «Falta aprobar permisos» |
| **PERMANENTE** (cuenta de GitHub inexistente, login que es una organización, `422` de validación, nombre ocupado por un tercero que no supera la adopción) | Cero reintentos; estado terminal con motivo y acción sugerida; mensaje literal del proveedor guardado | «Requiere tu acción: …», con el texto literal debajo |

**Un límite de la API de GitHub nunca se pinta como error del equipo** (Ley 5). El aprovisionamiento masivo de una tarea es exactamente el momento en que más presupuesto se consume, y es precisamente ahí donde esta distinción visual importa más.

### 8.6.5 Adopción segura ante un nombre ya existente

Antes de crear un repositorio se comprueba si el nombre ya existe. Si existe, **se adopta sólo si se cumplen las cinco condiciones siguientes** (A-097):

| # | Condición | Qué descarta |
|---|---|---|
| a | Tiene el topic `gestor-tareas` | Un repositorio ajeno a la aplicación |
| b | Pertenece a la organización vinculada al curso | Un repositorio de otra organización |
| c | Tiene el topic `curso-<slug>` de **este** curso | El repositorio de otro curso |
| d | Su descripción contiene el marcador que identifica exactamente este sujeto y esta tarea | El repositorio de otra tarea o de otro sujeto |
| e | Su historia no contiene commits ajenos al repositorio base | Un repositorio con trabajo real de alguien |

Cumplidas las cinco, se guarda su identificador de GitHub y se salta directamente a `CONFIGURANDO_ACCESOS`, lo que hace **idempotente** el aprovisionamiento sin depender de que la API distinga un reintento de una colisión real. En cualquier otro caso: `ERROR_PERMANENTE` con subtipo `NOMBRE_OCUPADO_POR_TERCERO`, con el detalle de qué condición falló. **Tratar la colisión como éxito a ciegas entregaría a un estudiante el repositorio de otro.**

### Criterios de aceptación de 8.6

- **CA-8.6-01** Un repositorio con todos los integrantes `ACEPTADO` y el acceso docente `CONCEDIDO` está en `OPERATIVO`; quitar la aceptación de uno de los integrantes lo mueve a `DEGRADADO` con `INTEGRANTE_PENDIENTE_EN_CANVAS` o el motivo que corresponda, nunca a un estado de error.
- **CA-8.6-02** El recuento de repositorios de una tarea nunca suma `DEGRADADO` a la columna de «con problemas»: tiene su propia columna.
- **CA-8.6-03** Un repositorio en `DEGRADADO` por `FALTA_ACEPTAR_INVITACION_GITHUB` cuya invitación se acepta pasa directamente a `OPERATIVO` sin transicionar por `CONFIGURANDO_ACCESOS`.
- **CA-8.6-04** Reintentar la creación de un repositorio cuyo nombre ya existe y que cumple las cinco condiciones de adopción no crea un segundo repositorio de GitHub ni una segunda fila en `repositorio`.
- **CA-8.6-05** Un fallo `429` durante la creación deja al repositorio en `ERROR_TRANSITORIO` con reintento visible, nunca en `ERROR_PERMANENTE`.
- **CA-8.6-06** Agotar los ocho sondeos de contenido de un repositorio con base sin ver el commit inicial no impide que el repositorio avance a `CONFIGURANDO_ACCESOS`, y deja una incidencia informativa, no un error.
- **CA-8.6-07** Un repositorio cuyo nombre colisiona con uno de otra tarea del mismo curso (condición d incumplida) queda en `ERROR_PERMANENTE` con `NOMBRE_OCUPADO_POR_TERCERO`, nunca se adopta.
- **CA-8.6-08** Un límite de tasa de GitHub durante el aprovisionamiento se muestra en ámbar con hora de reintento, nunca en rojo ni con vocabulario de error.

---

## 8.7 El trabajo `aprovisionar_repositorios`: disparadores, cadencia y reintentos (R2.3.10)

El motor genérico que ejecuta este trabajo —la cola sobre PostgreSQL, `SELECT … FOR UPDATE SKIP LOCKED`, el planificador, el vigilante externo— se define en **§14**. Esta sección documenta únicamente la lógica de negocio propia de `aprovisionar_repositorios`: cuándo se dispara, con qué ritmo y qué significan sus reintentos.

### 8.7.1 Disparadores y cadencia

`aprovisionar_repositorios` corre por **evento de dominio y por barrido**, con alcance por curso (A-114, A-218):

- **Evento de dominio:** en la misma transacción en que la materialización de sujetos (8.5.1, paso 3) detecta un sujeto nuevo o encuentra que un sujeto ya materializado acaba de cumplir la guarda de 8.5.2 —su mapeo pasó a `VIGENTE`, un integrante se aceptó en el grupo, el repositorio base pasó a `LISTO`, un sujeto se reactivó desde `FUERA_DE_ALCANCE`— se encola el trabajo para ese sujeto. Es la vía rápida.
- **Barrido de respaldo, cada 2 minutos:** re-evalúa todos los sujetos que siguen en `ESPERANDO_INFORMACION` o `LISTO_PARA_CREAR`. Es la garantía de que **ningún sujeto queda esperando indefinidamente** aunque un evento se pierda: el tope superior entre que un sujeto cumple la guarda y su repositorio empieza a crearse es de dos minutos.

**Clave de idempotencia:** `repo:<tarea>:<sujeto>` — encolar dos veces el mismo sujeto es un *no-op* garantizado por índice único, no por una comprobación en memoria (§14). **Reintentos:** hasta **8 en aproximadamente 2 horas**, con el significado de negocio de 8.6.4: sólo los fallos `TRANSITORIO` consumen reintentos; `BLOQUEANTE` espera y reevalúa; `PERMANENTE` no reintenta.

**Cerrojo:** el trabajo toma siempre el espacio de cerrojo **2** (GitHub) del curso y **nunca** el espacio 1 (Canvas), de modo que una sincronización lenta de Canvas —o el checklist de vinculación— nunca detiene el aprovisionamiento de 600 repositorios (A-217, corrección de precedencia en 8.1).

### 8.7.2 Ritmo y presupuesto

El ritmo nominal es **1 repositorio cada 6 segundos**, ajustado hacia abajo por un freno duro medido sobre las cabeceras de límite reales de la respuesta —nunca por aritmética teórica— para no bajar del 50 % del límite medido en la hora (§6 para el mecanismo). **R2.3.10 exige que la creación sea progresiva y automática, no que sea instantánea**: un curso de 200 sujetos puede tardar entre 20 y 40 minutos según cuánto se esté espaciando el ritmo, y la pantalla de tarea muestra el avance con su estimación (8.9.2).

**Desglose del coste por repositorio**, distinguiendo si la tarea tiene o no repositorio base (RG-088):

| Paso | Con base | Sin base |
|---|---|---|
| Lectura previa por nombre | 1 | 1 |
| Creación (`/generate` o `POST /orgs/{org}/repos`) | 1 | 1 |
| Ajuste de topics (8.4) | 1 | 1 |
| Ajuste de metadatos no cubiertos en la creación (`PATCH`) | ≤ 1 | ≤ 1 |
| Sondeo de contenido (8.6.3) | ≤ 8 | 0 |
| Commit inicial por Git Data (8.3.4) | 0 | 4 ó 5 |
| Permisos de Actions de la instalación | ≤ 1 | ≤ 1 |
| Lectura previa de colaborador + invitación, por integrante | 2 × n | 2 × n |
| Acceso del equipo docente | 1 | 1 |
| **Total, tarea individual (n = 1)** | **≤ 16** | **≤ 13** |
| **Tarea grupal** | **≤ 16 + 2·(n−1)** | **≤ 13 + 2·(n−1)** |

Esta tabla alimenta la función de dominio que estima el tiempo restante y que la pantalla de tarea muestra como «creando 12 de 60 · quedan ~9 min», recalculada en cada ciclo con el ritmo efectivo que el freno de presupuesto esté imponiendo en ese momento (RG-088).

### 8.7.3 Guarda anti-bucle

`aprovisionar_repositorios` **nunca crea un repositorio para un sujeto que ya tiene una fila de `repositorio` en un estado distinto de `INACCESIBLE`**, cualquiera que sea ese estado y tenga o no identificador de GitHub asignado (A-202). La única vía que produce una fila nueva para un sujeto que ya tuvo repositorio es la acción explícita de sustitución (8.11.4). Sin esta guarda, el trabajo idempotente recrearía repositorios en bucle ante cualquier inconsistencia transitoria.

### Criterios de aceptación de 8.7

- **CA-8.7-01** Encolar dos veces el mismo sujeto en la misma tarea produce una sola fila de trabajo pendiente.
- **CA-8.7-02** Un sujeto cuyo mapeo pasa a `VIGENTE` en el minuto 1 tiene su repositorio en `CREANDO` a más tardar en el minuto 3.
- **CA-8.7-03** Un ciclo de `aprovisionar_repositorios` corriendo junto con el checklist de vinculación del mismo curso no se bloquea mutuamente: se serializan sólo con otros trabajos del mismo espacio de cerrojo (GitHub).
- **CA-8.7-04** El tiempo estimado que muestra la pantalla de tarea para un aprovisionamiento en curso se recalcula al menos una vez por ciclo y coincide con la fórmula de coste de 8.7.2 aplicada al ritmo efectivo medido.
- **CA-8.7-05** Un sujeto con `repositorio.estado = ERROR_TRANSITORIO` con 8 intentos agotados no vuelve a reintentarse solo: pasa a `REQUIERE_ATENCION` con el último error visible (§14).

---

## 8.8 Colaboradores e invitaciones (R2.3.9)

### 8.8.1 Modelo de acceso del estudiante

Los estudiantes entran al repositorio como **colaboradores del repositorio**, con permiso `push` y nunca `admin`, y **no** como miembros de la organización de GitHub (A-064, A-065; mecanismo HTTP en §6). El repositorio es siempre privado. Esta decisión evita que el estudiante vea el repositorio de sus compañeros —un riesgo real si el permiso por defecto de la organización concediera lectura a los miembros— y no depende de ningún cupo que se agote a la escala de un curso.

**Consecuencia que el mensaje de R2.3.12 tiene que anticipar (8.10):** hasta que el estudiante acepta la invitación, la URL de su repositorio le muestra «no encontrado», porque GitHub responde `404` en vez de `403` a quien no tiene acceso a un repositorio privado.

### 8.8.2 Máquina de estados del acceso de un integrante

`acceso_repositorio.estado` tiene **diez** valores y **ninguno es terminal** (A-212):

| Estado | Se entra cuando | Sale a |
|---|---|---|
| `SIN_MAPEO` | El integrante no tiene mapeo de GitHub vigente | `POR_INVITAR` |
| `POR_INVITAR` | Hay mapeo vigente y el repositorio existe | `INVITADO`, `ACCESO_DIRECTO` |
| `INVITADO` | La invitación de colaborador se creó | `ACEPTADO`, `EXPIRADA`, `DESAPARECIDA` |
| `ACCESO_DIRECTO` | La invitación se resolvió de inmediato porque el estudiante ya tenía acceso previo | `ACEPTADO` (equivalente); **salta el estado pendiente** |
| `ACEPTADO` | Webhook de membresía, única señal documentada de aceptación | `DESAPARECIDA` |
| `EXPIRADA` | La reconciliación detecta que la invitación caducó | `POR_INVITAR` (reenvío) |
| `DESAPARECIDA` | Ni invitación abierta ni colaborador presente | `POR_INVITAR` |
| `REVOCACION_PROPUESTA` | Canvas indica que el integrante ya no pertenece al grupo; **ninguna persona ha decidido todavía** | `ACEPTADO`/`ACCESO_DIRECTO` (si se mantiene) o `REVOCACION_PROGRAMADA` |
| `REVOCACION_PROGRAMADA` | Una persona decidió revocar y el aviso salió, con hora de ejecución escrita | `REVOCADO`, o vuelta a `ACEPTADO`/`ACCESO_DIRECTO` si se revierte |
| `REVOCADO` | El retiro de colaborador se ejecutó con éxito | `POR_INVITAR`, si la persona vuelve al grupo |

**No existe señal documentada de rechazo de una invitación**: el estado se llama `DESAPARECIDA` y la interfaz dice literalmente «rechazada o caducada», porque nombrar una causa que no se puede probar sería mentir en pantalla (A-100).

**Política de reenvío:** máximo **3 reenvíos**, separados al menos **24 horas**, con este orden obligatorio antes de tocar nada: primero se comprueba si el estudiante ya es colaborador (si lo es, no se toca nada); si no, se comprueba si la invitación sigue viva (si lo está, sólo se reenvía el aviso por Canvas, sin tocar GitHub); sólo si la invitación expiró se elimina y se vuelve a crear. **Nunca se elimina y se recrea a ciegas.**

### 8.8.3 Revocación: nunca se ejecuta sola

Ninguna transición hacia `REVOCACION_PROGRAMADA` ocurre sin una decisión humana explícita, ni siquiera cuando la causa es un traslado de grupo detectado automáticamente (A-212). La ausencia se confirma en **dos ciclos consecutivos** de sincronización de grupos antes de proponer la revocación; a partir de ahí, la gracia se cuenta **desde la decisión humana**, no desde la detección: siete días naturales en el caso general, 24 horas si el motivo es un traslado de grupo, y cero si el acceso es de alguien que nunca debió tenerlo. Ninguna revocación es silenciosa: se avisa al retirarse el plazo y se confirma al ejecutarse. El repositorio **no cambia de estado** por una revocación propuesta o programada: se muestra un distintivo ámbar «acceso por revisar» sin transición del predicado de 8.6.2.

### 8.8.4 Acceso del equipo docente

La concesión de lectura al equipo docente ocurre dentro del mismo paso `CONFIGURANDO_ACCESOS` que las invitaciones de estudiante, y es la tercera condición del predicado de `OPERATIVO` (8.6.2). El modelo completo de cómo se concede —vía equipo de la organización o vía colaborador individual de respaldo—, sus permisos y su revocación al retirar a un ayudante, pertenecen al gobierno de permisos del curso y no se redefinen aquí; este capítulo sólo consume el hecho de que esa concesión es una precondición de que el repositorio llegue a `OPERATIVO`.

### Criterios de aceptación de 8.8

- **CA-8.8-01** Un estudiante que ya es colaborador del repositorio por una vía distinta produce `ACCESO_DIRECTO` y no una fila `INVITADO` pendiente de aceptación.
- **CA-8.8-02** Una invitación con 4 días de antigüedad sin aceptar recibe su primer reenvío; antes de reenviar, la aplicación comprueba si el estudiante ya entró y, si es así, no ejecuta ninguna llamada de escritura.
- **CA-8.8-03** Un integrante que sale de su grupo en Canvas no pierde acceso a su repositorio hasta que un profesor o ayudante decide explícitamente revocarlo; mientras tanto la fila queda en `REVOCACION_PROPUESTA`.
- **CA-8.8-04** Ejecutar una revocación programada cuyo `DELETE` a GitHub falla no mueve la fila a `REVOCADO` ni envía el mensaje de confirmación; queda una incidencia visible.
- **CA-8.8-05** Un traslado de grupo detectado automáticamente no revoca ningún acceso a las 24 horas por sí solo: la fila permanece en `REVOCACION_PROPUESTA` hasta que alguien decide.
- **CA-8.8-06** Cuatro reenvíos de la misma invitación en menos de 96 horas es imposible: el cuarto se bloquea por la regla de separación mínima de 24 horas entre reenvíos.

---

## 8.9 Visibilidad del estado de los repositorios (R2.3.11)

### 8.9.1 Columnas de estado, nunca mezcladas

La pantalla de tarea muestra el recuento de repositorios agrupado por lo que el docente necesita distinguir, nunca en una sola cifra de «listos» contra «no listos» (A-092, A-211):

- **Operativos** — predicado íntegro de 8.6.2 cumplido.
- **Funcionando, incompleto** — `DEGRADADO`, con su motivo.
- **Con problemas** — `BLOQUEADO`, `ERROR_TRANSITORIO`, `ERROR_PERMANENTE`, cada uno con su propia sub-cuenta.
- **No accesible en GitHub** — `INACCESIBLE`, con su motivo entre los cuatro cerrados de 8.11.1.
- **Fuera de alcance** — sujetos desactivados que conservan su repositorio (8.5.1).
- **Archivados** — fuera del alcance operativo de este capítulo, contados aparte.
- **Esperando información** / **listos para crear** — sujetos materializados que aún no tienen repositorio, con el motivo cerrado de 8.5.2.

Esta separación existe porque **R2.2.6** y **R2.3.11** piden mostrar *claramente* qué falta: colapsar `DEGRADADO` dentro de «con problemas» convertiría el estado más común y menos preocupante de un aprovisionamiento en curso en una alarma.

### 8.9.2 Progreso del aprovisionamiento en curso

Mientras hay sujetos en `ESPERANDO_INFORMACION`, `LISTO_PARA_CREAR` o `CREANDO`, la cabecera de la tarea muestra el avance —«creando 12 de 60 · quedan ~9 min»— calculado con la función de coste de 8.7.2 aplicada al ritmo efectivo del momento, no a una estimación fija (RG-088).

### 8.9.3 Incidencias que este capítulo produce

El catálogo cerrado de tipos de incidencia es una sola tabla que alimentan además Pendientes, el resumen de seguimiento y el informe diario (A-088, A-207); este capítulo produce o participa en éstas:

| Tipo | Motivo típico en este capítulo |
|---|---|
| `SIN_ACCESO_DOCENTE` | El equipo docente aún no tiene lectura concedida sobre el repositorio |
| `VISIBILIDAD_NO_RESOLUBLE` | Ninguna de las tres vías de 8.5.1 resuelve la visibilidad de una entrega |
| `REPO_NOMBRE_OCUPADO` | Colisión de nombre que no supera la adopción segura de 8.6.5 |
| `REPOSITORIO_INACCESIBLE` | Severidad ADVERTENCIA; una por repositorio, no una por versión afectada (8.11.1) |
| `GITHUB_PERMISOS_PENDIENTES` | La instalación de la GitHub App tiene permisos por aprobar que bloquean el aprovisionamiento |
| `INVITACION_NO_ACEPTADA`, `INVITACION_EXPIRADA` | Estados de acceso de 8.8.2 con más de 48 horas sin resolver |
| `ESTUDIANTE_EN_DOS_GRUPOS`, `GRUPO_INCOMPLETO` | Bloquean el aprovisionamiento del sujeto afectado hasta resolverse (§7) |
| `TAREA_INCONSISTENTE` | Cambio de modalidad detectado tras el primer aprovisionamiento (8.2.4) |

**Cada línea de incidencia lleva un motivo escrito y accionable**, nunca sólo un código: es la misma disciplina de A-094 y A-116 aplicada a toda la superficie visible de este capítulo.

### Criterios de aceptación de 8.9

- **CA-8.9-01** La pantalla de tarea muestra al menos siete contadores distintos para el estado de sus repositorios, y ninguno de ellos suma `DEGRADADO` a «con problemas».
- **CA-8.9-02** Durante un aprovisionamiento masivo, la estimación de tiempo restante se actualiza en cada ciclo de 2 minutos y nunca queda congelada mostrando un número obsoleto.
- **CA-8.9-03** Toda incidencia abierta por este capítulo tiene un `titulo`, un `detalle` y una `accion_sugerida` no vacíos.
- **CA-8.9-04** Un repositorio `INACCESIBLE` con seis versiones capturadas produce **una sola** incidencia `REPOSITORIO_INACCESIBLE`, no seis.
- **CA-8.9-05** Un límite de tasa de GitHub durante el aprovisionamiento masivo se refleja en la pantalla como espera, nunca como una fila en la columna «con problemas».
- **CA-8.9-06** Filtrar la vista de repositorios de una tarea por «fuera de alcance» muestra únicamente los sujetos desactivados que conservan repositorio, distintos de los archivados.

---

## 8.10 Comunicación al estudiante a través de Canvas (R2.3.12)

El contenido exacto, la redacción y el mecanismo de envío de los mensajes se definen en **§11**; esta sección documenta únicamente **qué evento de este capítulo dispara cada comunicación**.

### 8.10.1 El disparador es por persona, no por repositorio ni por sujeto

El evento que dispara el mensaje de acceso es que **el acceso de ese estudiante concreto** pase a `INVITADO` o `ACCESO_DIRECTO` (8.8.2) — **no** que el repositorio llegue a `OPERATIVO` (A-127). Colgarlo de `OPERATIVO` produciría dos fallos que R2.3.12 no tolera: en un grupo de cuatro se enviaría un solo mensaje sin decir a quién correspondía, y el integrante cuyo mapeo llega después —el caso central de **R2.3.10**— no lo recibiría nunca, porque el aviso ya se habría consumido para el grupo. Con el disparador por acceso individual, **cada integrante recibe su mensaje exactamente cuando hay algo que decirle**, incluido el que llega semanas después.

### 8.10.2 Qué eventos de este capítulo comunican, y qué canal

| Evento (nombre en §11) | Alcance | Disparador de este capítulo |
|---|---|---|
| `repositorio_disponible` | Por tarea, por persona | El acceso de ese estudiante pasa a `INVITADO` o `ACCESO_DIRECTO` (8.10.1) |
| `invitacion_aceptada` | Por tarea, por persona | El acceso de ese estudiante pasa a `ACEPTADO` (8.8.2) |
| `recordatorio_invitacion` | Por tarea, por persona | 48 horas desde la invitación sin aceptar, hasta 3 veces |

El canal exacto por el que viaja cada mensaje —mensaje directo, comentario en la tarea de registro, o bloqueo declarado si ninguno de los dos está disponible— y el contenido literal de cada uno se fijan en **§11** (A-127, A-130). Esta sección se limita a declarar que la aplicación **garantiza** un canal, porque un curso sin ningún permiso de mensajería no queda con **R2.3.12** silenciosamente incumplido: si ni el mensaje directo ni el comentario en entrega están disponibles, el asistente de vinculación del curso no completa la vinculación y lo dice explícitamente.

### 8.10.3 Qué información tiene que poder construirse en el momento del disparo

Para que el mensaje de §11 pueda redactarse, este capítulo garantiza que en el instante en que `acceso_repositorio` pasa a `INVITADO`/`ACCESO_DIRECTO` ya existen, resueltos y persistidos: el nombre exacto de la organización de GitHub, el nombre exacto del repositorio y su URL completa (8.4), y la fecha de cierre de la primera entrega aplicable a ese sujeto (§9, consumida aquí sólo como dato ya calculado). Sin estos tres datos resueltos, el evento no se dispara.

### Criterios de aceptación de 8.10

- **CA-8.10-01** Un grupo de cuatro integrantes cuyos mapeos se resuelven en cuatro momentos distintos produce cuatro disparos del evento `repositorio_disponible`, uno por integrante, nunca uno solo para el grupo.
- **CA-8.10-02** Un integrante que se incorpora al grupo tres semanas después de creado el repositorio recibe su propio disparo de `repositorio_disponible` en cuanto su acceso pasa a `INVITADO`.
- **CA-8.10-03** Vincular un curso en el que ni el mensaje directo ni el comentario en la tarea de registro están disponibles impide completar el asistente de vinculación, con el motivo escrito.
- **CA-8.10-04** El evento `repositorio_disponible` nunca se dispara antes de que el nombre del repositorio, su URL y la fecha de cierre aplicable estén resueltos y persistidos.
- **CA-8.10-05** El evento que dispara `repositorio_disponible` es independiente del estado `OPERATIVO`/`DEGRADADO` del repositorio: un repositorio `DEGRADADO` porque a otro integrante le falta el mapeo no impide que quien ya fue invitado reciba su mensaje.

---

## 8.11 Casos borde y recuperación

### 8.11.1 Un repositorio que desaparece o deja de ser legible en GitHub

Un repositorio en cualquier estado con identificador de GitHub asignado puede volverse **`INACCESIBLE`**, con `repositorio.motivo` de lista cerrada de cuatro valores (A-211):

```
BORRADO_EN_GITHUB                     — webhook repository, acción deleted
TRANSFERIDO_FUERA_DE_LA_ORG           — acción transferred con destino distinto del curso
FUERA_DEL_ALCANCE_DE_LA_INSTALACION   — installation_repositories, repositorios removidos
APP_SIN_ACCESO                        — dos ciclos de reconciliación con 404 o 403 no transitorio
```

`INACCESIBLE` conserva su serie histórica y su timeline íntegros, queda **fuera** de las alertas de actividad (§10) —no hay nada que leer— y se muestra en **columna propia** (8.9.1), nunca sumado a `OPERATIVO` ni oculto. Produce una sola incidencia `REPOSITORIO_INACCESIBLE`, severidad ADVERTENCIA, por repositorio y no por versión afectada.

### 8.11.2 Sustitución: la única vía para dar un repositorio nuevo a un sujeto que ya tuvo uno

`INACCESIBLE` **no** transita solo a `LISTO_PARA_CREAR`. La única salida es la acción explícita **«sustituir repositorio»**, de un profesor con permiso de administración de la tarea y con **confirmación escrita** que nombra al sujeto, al repositorio perdido y lo que no vuelve (A-202). La acción:

1. **Crea una fila nueva** de `repositorio` para el mismo sujeto, con `reemplaza_a_id` apuntando a la fila `INACCESIBLE` anterior, que se conserva íntegra como evidencia.
2. Nace en `LISTO_PARA_CREAR` y sigue el ciclo normal de 8.6, incluida la adopción segura si el nombre —determinista e inmutable, 8.4.4— coincidiera con algo existente.
3. **Nunca reutiliza la fila anterior**: reutilizarla haría que los commits, las identidades de Git y las versiones capturadas contra el repositorio perdido pasaran a colgar del nuevo, una atribución falsa de evidencia que las leyes de trazabilidad del sistema prohíben.
4. Queda registrada en `bitacora` con la acción `REPOSITORIO_SUSTITUIDO`.

La ficha del sujeto muestra los dos repositorios en orden, con la fecha de la sustitución.

### 8.11.3 Salida de `ERROR_PERMANENTE`: destino según el subtipo

Devolver a `LISTO_PARA_CREAR` un repositorio cuyo bloqueo real está en el mapeo del estudiante produciría el mismo error en el ciclo siguiente. Por eso la salida depende del subtipo (A-211):

| Subtipo | Acción | Destino |
|---|---|---|
| Organización prohíbe crear, exige 2FA, cuenta bloqueada por la organización, permiso insuficiente | «Reintentar» | `LISTO_PARA_CREAR` |
| Nombre ocupado por un tercero | «Reintentar», que vuelve a evaluar las cinco condiciones de 8.6.5 | `LISTO_PARA_CREAR`, o de nuevo `ERROR_PERMANENTE` con el detalle de qué condición falló |
| Cuenta de GitHub eliminada, o el login resuelve a una organización | «Corregir la cuenta de GitHub», que supersede el mapeo (§7) | `ESPERANDO_INFORMACION` con motivo `SIN_MAPEO_GITHUB` |

**El aprovisionamiento automático nunca saca por sí solo a un repositorio de `ERROR_PERMANENTE`**, ni siquiera si la causa desaparece sola: es lo que lo distingue de `BLOQUEADO`, que sí se reevalúa cada 30 minutos.

### 8.11.4 Un sujeto que sale de alcance conserva todo

Si un sujeto se desactiva por la regla de 8.5.1 después de que su repositorio ya existe, el repositorio pasa a `FUERA_DE_ALCANCE`, **conserva el repositorio, los commits y las versiones capturadas**, y se muestra en la tarea bajo «sujetos retirados» (A-095). No se borra —destruiría evidencia— y **no se archiva** —archivar impediría capturar versiones posteriores si el sujeto regresa—. Un cambio de configuración en Canvas nunca borra trabajo de estudiantes.

### 8.11.5 Cuando el aprovisionamiento reactiva un sujeto, no reemite nada por decreto

La transición `FUERA_DE_ALCANCE → OPERATIVO | DEGRADADO` **no** reemite ninguna invitación ni concede ningún acceso por sí misma: en la misma transacción en que el sujeto se reactiva se encolan la reconciliación de accesos y la sincronización de acceso docente, que aplican sus reglas normales de siempre —incluido el orden obligatorio de comprobación de 8.8.2, sin excepciones—. **El estado tras reactivar es el que dicte el predicado de 8.6.2 en ese instante**, nunca se escribe `OPERATIVO` por suposición (A-211).

### 8.11.6 El curso en modo de sólo lectura

Cuando `curso.modo_escritura = 'SOLO_LECTURA'` —gobierno del curso, fuera de este capítulo—, los sujetos que aún no tienen repositorio quedan en `ESPERANDO_INFORMACION` con el motivo `CURSO_EN_SOLO_LECTURA`, añadido a la lista cerrada de 8.5.2 (RG del acta de datos que corrige A-094). El aprovisionamiento no produce ninguna escritura hacia GitHub mientras el curso esté en ese modo; los repositorios ya creados no se ven afectados.

### Criterios de aceptación de 8.11

- **CA-8.11-01** Un repositorio `BORRADO_EN_GITHUB` no puede recibir una nueva captura de versión sin que medie la acción de sustitución.
- **CA-8.11-02** Ejecutar «sustituir repositorio» crea una fila nueva con `reemplaza_a_id` apuntando a la anterior; la fila anterior sigue existiendo, con su `github_repo_id` y su historia intactos.
- **CA-8.11-03** Un repositorio en `ERROR_PERMANENTE` por `CUENTA_ELIMINADA` no se reintenta con el botón genérico «reintentar»: exige corregir primero el mapeo del estudiante.
- **CA-8.11-04** Un sujeto que sale de alcance y vuelve a entrar tres semanas después conserva el mismo `repositorio_id` y su historia completa de commits.
- **CA-8.11-05** Reactivar un sujeto cuyo único estudiante ya era colaborador del repositorio no produce ninguna llamada de escritura hacia GitHub.
- **CA-8.11-06** Poner un curso en modo de sólo lectura detiene la creación de repositorios nuevos y dispara el motivo `CURSO_EN_SOLO_LECTURA` para los sujetos pendientes, sin tocar los repositorios existentes.
