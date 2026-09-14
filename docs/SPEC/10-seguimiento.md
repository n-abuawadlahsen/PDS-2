# 10. Seguimiento del avance

## 10.1 Alcance del capítulo, vocabulario y principios

### 10.1.1 Qué cubre este capítulo

Este capítulo especifica cómo la aplicación **recopila la actividad de los repositorios de GitHub, la atribuye a estudiantes concretos, la convierte en métricas y la presenta** al equipo docente en tres pantallas: el **tablero de la tarea**, la **comparación entre integrantes** y la **línea de tiempo (timeline) de cada repositorio**. Cubre además la **vista de seguimiento del curso** y las **alertas** que alimentan el informe diario del capítulo 11.

Cubre los requisitos **R2.5.1** a **R2.5.10** en su totalidad, y aporta las piezas de las que dependen **R2.6.1**, **R2.6.2** (situaciones que requieren intervención), **R2.4.5** y **R2.4.7** (la actividad que sostiene la captura de versiones) y **R2.7.4** (el aviso de commits no incluidos en la versión registrada).

**No cubre**: la creación de repositorios (capítulo 8), el cálculo de fechas efectivas y la captura de versiones (capítulo 9), el informe diario y las comunicaciones (capítulo 11) ni la corrección (capítulo 12). Este capítulo consume esas piezas y declara en cada punto de qué capítulo vienen.

### 10.1.2 Vocabulario cerrado del capítulo

La aplicación usa **una sola palabra por hecho** (A-154). Las de este capítulo son:

| Término | Significado exacto en la aplicación |
|---|---|
| **Sujeto** | La unidad a la que pertenece un repositorio: un estudiante en una tarea individual, un grupo en una tarea grupal (A-080) |
| **Commit** | Un objeto commit de Git identificado por su `sha` dentro de un repositorio |
| **Commit contable** | El commit que entra en los recuentos de participación y de actividad, según el predicado único de §10.5.1 |
| **Actividad del repositorio** | Existencia de commits contables, cualquiera que sea su autor, incluidos bots y equipo docente |
| **Actividad de los estudiantes** | Existencia de commits contables con al menos un acreditado que sea estudiante del curso (§10.5.2) |
| **Día del curso** | El día de calendario en la zona horaria del curso, `curso.zona_horaria` (§10.5.4) |
| **Ventana de una entrega** | El intervalo `(inicio, cierre]` calculado **por sujeto** según §10.6.3 |
| **Espejo** | La copia local en PostgreSQL de lo que la aplicación ha leído de GitHub y de Canvas |
| **Huérfano** | Adjetivo de un **commit** que dejó de ser alcanzable tras una reescritura de historia (`commit.huerfano`). **Nunca** designa un repositorio: el repositorio que desaparece está `INACCESIBLE` (RG-013, RG-181) |
| **Silenciar** | Ocultar temporalmente una alerta no bloqueante conservándola abierta. El verbo «posponer» **no existe** en la aplicación (RG-042) |

### 10.1.3 Los seis principios que gobiernan todo el capítulo

| # | Principio | Consecuencia verificable | Origen |
|---|---|---|---|
| P1 | **Ninguna pantalla de seguimiento llama a GitHub ni a Canvas.** Toda vista se pinta desde el espejo | Contador de llamadas externas por petición **igual a 0**; prueba de CI con clientes que lanzan excepción | Ley 1, A-119, A-220 |
| P2 | **Una sola definición por número.** Cada predicado, umbral y ventana vive en **una única función de dominio** que consumen tablero, timeline, comparación e informe | Prueba automatizada que compara los cuatro consumidores sobre el mismo repositorio y período | A-171, A-205, RG-030 |
| P3 | **Los agregados se recomputan, nunca se incrementan.** Ninguna ruta de ingesta suma a un contador | Ejecutar `agregar_metricas` dos veces seguidas no cambia ninguna fila | A-114, A-221 |
| P4 | **La aplicación no acusa.** Un dato ausente o no atribuido se declara como tal; nunca se presenta como falta del estudiante | Ningún estudiante aparece como «sin participación» mientras su repositorio tenga commits sin atribuir | A-118, A-120, Q-2.5-28 |
| P5 | **La historia se muestra entera; la métrica se calcula con el predicado.** Lo que no cuenta se muestra igualmente, con su etiqueta y su motivo | El timeline muestra merges, commit inicial y huérfanos, cada uno etiquetado | A-124, A-171, A-205 |
| P6 | **Nada se borra.** Los commits, las versiones y la bitácora son evidencia | Ninguna migración contiene `ON DELETE CASCADE`; la prueba de arquitectura falla si aparece | A-030, RG-048 |

### 10.1.4 Criterios de aceptación de §10.1

1. Abrir cualquier pantalla de este capítulo con el inspector de red del navegador y comprobar que la respuesta de la API interna trae la cabecera `X-Llamadas-Externas: 0`.
2. Ejecutar la suite de CI y comprobar que existe y pasa la prueba que sustituye `ClienteCanvas` y `ClienteGitHub` por dobles que lanzan excepción en todos sus métodos, para el tablero, el timeline y la vista de curso.
3. Buscar en el código la cadena `HUERFANO` y comprobar que no aparece como valor admisible de `repositorio.estado`.
4. Buscar la cadena `posponer` en el archivo único de mensajes y comprobar que no existe.

---

## 10.2 Ingesta de actividad desde GitHub

### 10.2.1 Las tres fuentes y el requisito de frescura NFR-2.5-A

La ingesta es **híbrida, de tres fuentes**, y ninguna sustituye a las otras (A-070, A-072, A-221):

| Fuente | Qué aporta | Cadencia | Trabajo |
|---|---|---|---|
| **Webhooks de la GitHub App** | Vía rápida: cada `push` llega en segundos y no consume presupuesto de la API | Continua | `procesar_webhooks` |
| **Reconciliación condicional** | Red de seguridad frente a entregas perdidas por GitHub | 15 min | `reconciliar_actividad` |
| **Barrido completo nocturno** | Cierre de cualquier hueco que las dos anteriores no cubran, y relleno hacia atrás | Diario 03:30 | `barrido_completo_actividad` |
| **Precierre** | Puesta al día del espejo antes de cada fecha efectiva de cierre | Repartido en los 15 min previos a cada cierre, por repositorio | `precierre_actividad` |

El requisito no funcional **NFR-2.5-A** se declara con **tres números, no con uno** (A-223, RG-100):

| Nivel | Valor | Quién lo sostiene |
|---|---|---|
| **Objetivo declarado** | **p95 ≤ 60 s** y **p99 ≤ 180 s** entre la recepción del webhook `push` y la visibilidad del commit en el tablero y el timeline | Receptor que responde `202` en < 200 ms más `procesar_webhooks` continuo |
| **Techo garantizado sin webhook** | **`ceil(repositorios_en_ingesta_del_curso / 200) × 15 min`**, donde el recuento excluye los repositorios `ARCHIVADO`, `FUERA_DE_ALCANCE` e `INACCESIBLE`. Con 200 repositorios, 15 minutos; con 600, **45 minutos** | `reconciliar_actividad` |
| **Techo absoluto** | **24 horas** | `barrido_completo_actividad` |

Reglas asociadas, sin excepción:

1. El techo garantizado es una **función pura `techo_frescura(curso) -> timedelta`** con pruebas para 200 repositorios, 600 repositorios y el caso degradado. **La pantalla muestra el resultado calculado y el recuento del que sale**, nunca un número escrito a mano: «techo garantizado: 45 min · 600 repositorios en ingesta · 200 por ciclo cada 15 min».
2. Si la medición demuestra que una respuesta `304` consume límite secundario, la cadencia pasa a **30 minutos** y el tope a **100 repositorios por ciclo**, y la fórmula se recalcula sola. **Subir el tope por ciclo queda descartado**, porque los 200 son lo que mantiene el ciclo dentro del freno por presupuesto medido (A-219).
3. La latencia real se **mide y se publica**: `/operacion` muestra p50 y p95 de `commit.recibido_en − evento_push.recibido_en` de las últimas 24 horas, la antigüedad del último webhook recibido y la última ejecución de cada trabajo periódico.

### 10.2.2 Eventos suscritos y despachador

La GitHub App se suscribe a **exactamente siete eventos**, lista congelada el 11 de septiembre a las 20:00 junto con los permisos (A-061, A-070). Cada evento tiene un consumidor nombrado; no hay ninguna suscripción «por si acaso».

| Evento | Acciones tratadas | Para qué se usa | Requisitos que sostiene |
|---|---|---|---|
| `push` | — | Fuente rápida de commits: alimenta `evento_push` y `commit` | R2.5.2, R2.5.3, R2.5.4, R2.5.7, R2.5.8, R2.5.10 |
| `create` | — | Hito `RAMA_CREADA`; disparador de recorrido cuando `before` viene en ceros | R2.5.10 |
| `delete` | — | Hito `RAMA_BORRADA`. **No borra ningún commit ya ingerido** | R2.5.10 |
| `repository` | `renamed`, `archived`, `unarchived`, `deleted`, `transferred`, `privatized`, `publicized` | Nombre y `full_name` (A-110); entrada a `ARCHIVADO` (A-168); entrada a `INACCESIBLE` (RG-013) | R2.3.11, R2.5.5, R2.5.10 |
| `member` | `added`, `removed` | **Única señal documentada de que un estudiante aceptó su invitación**: cierra el estado pendiente de `acceso_repositorio` sin sondeo | R2.3.9, R2.3.11, R2.5.5 |
| `installation` | `new_permissions_accepted`, `suspend`, `unsuspend`, `deleted` | Salud de la instalación | R2.5.5 |
| `installation_repositories` | `added`, `removed` | Detecta que un repositorio sale del alcance de la instalación → motivo `FUERA_DEL_ALCANCE_DE_LA_INSTALACION` | R2.3.11, R2.5.5 |

**Reglas del despachador**, sin excepción:

1. El receptor `POST /webhooks/github` **verifica `X-Hub-Signature-256` sobre el cuerpo crudo antes de parsear**, persiste la entrega y responde **`202` en menos de 200 ms**. **No procesa en línea** (A-070).
2. Existe **un manejador por par `(evento, acción)`**. El despachador recibe una **lista blanca de pares activos por perfil de alcance**; un par que no está en la lista **se persiste, se marca `IGNORADO` y no produce error**. Una acción nueva de GitHub nunca rompe el receptor.
3. **No existen los eventos `member_invite` ni `repository_invitation`**: la creación de una invitación no genera evento; sólo su aceptación. Ninguna parte del diseño los supone.
4. **No se suscriben `pull_request`, `pull_request_review`, `issues` ni `organization`.** La actividad que no son commits **no se ingiere y no cuenta**, y la interfaz lo declara por escrito bajo la tarjeta de **R2.5.4** y al pie de la sección 3 del informe diario: «la participación se mide por commits atribuidos; la actividad en issues, pull requests y revisiones no se recopila».

### 10.2.3 Del `push` al `commit`: relleno, historia reescrita y ramas

**Regla de relleno.** Un `push` cuyo array `commits` no contiene toda la comparación se rellena con `GET /repos/{o}/{r}/compare/{before}...{after}` paginado con `per_page=100`, con **tope de 30 páginas, es decir 3000 commits por push**.

| Situación del push | Qué hace la aplicación |
|---|---|
| `before` y `after` normales y el payload trae todos los commits | Se ingiere del payload; **no se llama a GitHub** |
| Payload incompleto o truncado (`payload_truncado = true`, o `n_commits_payload` menor que la comparación) | Relleno con `compare/{before}...{after}` paginado hasta 30 páginas |
| `before` en ceros (rama nueva) | Recorrido de `GET /repos/{o}/{r}/commits?sha={ref}&per_page=100` **hasta topar con un SHA ya conocido**, con el mismo tope de 30 páginas |
| `after` en ceros (rama borrada) | No hay commits que ingerir: se registra el hito `RAMA_BORRADA` y **no se borra ningún commit** |
| `compare` devuelve `status = diverged` (`push --force`) | Recorrido del historial desde el head hasta un SHA conocido; los commits que desaparecen de la historia se marcan `huerfano = true` y **nunca se borran** |
| Se agota el tope de 30 páginas | `evento_push.completado = false`, incidencia informativa y el repositorio queda marcado para el barrido nocturno |

**Precisiones que la implementación no puede ignorar:**

- El array `commits` del payload tiene un tope de **2048** entradas.
- Al paginar `compare`, la lista de archivos cambiados **sólo llega en la primera página** y está limitada a 300 archivos para toda la comparación; y **el último commit devuelto puede no ser el más reciente** si hay más páginas. Por eso el relleno **nunca deduce la cabeza de la rama de la respuesta de `compare`**: la toma del `after` del propio payload.
- GitHub **no entrega el evento** cuando el payload supera 25 MB ni cuando se empujan más de 5000 ramas de una vez. Esos dos casos **no se aceptan como pérdida**: los cubre `reconciliar_actividad`, con lo que su techo de latencia es el declarado en §10.2.1 y no infinito.
- **`since` no se usa nunca en la ingesta corriente**, porque filtra por fecha del commit y no por fecha del push. La única excepción declarada es el relleno hacia atrás de §10.2.6, donde se usa con `repositorio.listo_en` y su semántica es la correcta para ese caso.
- **La Events API queda descartada** como fuente auxiliar: su retención es de 300 eventos y 30 días, menor que un semestre, y añadiría una segunda verdad sobre los mismos commits.
- **`pushedDate` no se usa**: está deprecado y retirado.

**Estrategia de la reconciliación**, en este orden (A-072):

1. `cursor_sincronizacion` guarda, por `(curso_id, recurso = 'commits', referencia = 'repo:<github_repo_id>:<ref>')`, el `ultimo_head_sha` confirmado y el `etag` de la última respuesta.
2. Cada 15 minutos se pide `GET /repos/{o}/{r}/commits` con `If-None-Match`. Un `304` cierra el ciclo **sin escribir nada**.
3. Si hay cambios, se compara `ultimo_head_sha...head_actual`. Con `status = ahead` se ingiere la diferencia; con `identical` o `behind` no hay nada nuevo; con **`diverged`** se recorre el historial desde el head hasta un SHA conocido y se marcan los huérfanos.
4. **`ultimo_head_sha` sólo avanza cuando el recorrido de esa rama termina con éxito.** Un recorrido interrumpido se reejecuta entero en el ciclo siguiente y es un no-op sobre las filas ya presentes.
5. **No se persiste ningún cursor intra-página**, y es una decisión declarada: la API REST sólo ofrece `page`, `per_page` y la cabecera `Link`, y ninguno es un marcador reanudable. Reejecutar un recorrido de 30 páginas cuesta a lo sumo 30 llamadas condicionales y es idempotente.

**Ramas.** Se ingieren los commits de **todas las ramas**, sin filtrar por `ref`:

| # | Regla | Motivo |
|---|---|---|
| 1 | El webhook `push` se procesa sin filtrar por `ref`; el reconciliador mantiene un cursor por cada `ref` vista | Un estudiante que trabaja en su propia rama **sí ha participado** (R2.5.4) |
| 2 | `commit.rama_detectada` guarda la `ref` que trajo el commit por primera vez | El timeline etiqueta la rama de cada commit (R2.5.10) |
| 3 | El índice **único `(repositorio_id, sha)`** hace estructuralmente imposible contar dos veces el mismo commit por aparecer en dos ramas o por una fusión | Sin doble conteo en R2.5.2 y R2.5.8 |
| 4 | Las métricas cuentan **todos los commits contables del repositorio, esté el commit en la rama que esté** | R2.5.3 no marca como inactivo un repositorio con trabajo en ramas |
| 5 | **La captura de versión no cambia**: se resuelve sobre `repositorio.rama_por_defecto`, usando `commit.en_rama_por_defecto` | R2.4.5: lo que se corrige es lo que el estudiante integró |
| 6 | Tope de **50 ramas activas por repositorio**; por encima sólo se reconcilian la rama por defecto y las 10 con actividad más reciente, con incidencia informativa | Impide que un repositorio anómalo consuma el presupuesto de todo el curso |

La pantalla de corrección muestra el aviso «hay N commits en ramas no fusionadas» cuando los haya, con enlace al timeline, para que el corrector sepa que existe trabajo fuera de la versión capturada.

### 10.2.4 Idempotencia, orden y concurrencia

La ingesta garantiza que reprocesar cualquier cosa no cambia ningún número, con **cuatro reglas estructurales respaldadas por restricciones de base de datos y no por comprobaciones en memoria**:

| # | Regla | Cómo se garantiza |
|---|---|---|
| 1 | **Deduplicación de la entrega** | Índice único `evento_webhook.delivery_id`. Una reentrega de GitHub inserta cero filas y no vuelve a procesar |
| 2 | **Clave de idempotencia del commit** | Índice único `commit (repositorio_id, sha)`. Toda escritura es `INSERT … ON CONFLICT DO UPDATE` que **sólo enriquece campos nulos** —`adiciones`, `eliminaciones`, `archivos_tocados`, `via_web`, `autor_github_user_id`— y **nunca reescribe** `fecha_committer`, `sha`, `n_padres`, `recibido_en` ni `origen_ingesta` de una fila ya presente |
| 3 | **Los agregados se recomputan** | `metrica_repositorio_dia` y `participacion_entrega` los produce `agregar_metricas` con borrado e inserción de la ventana recalculada dentro de una sola transacción. **Ninguna ruta de ingesta suma a un contador** |
| 4 | **Concurrencia por cerrojo explícito** | `procesar_webhooks` toma `pg_advisory_xact_lock` por `repositorio_id`; `reconciliar_actividad`, `barrido_completo_actividad` y `precierre_actividad` toman el **espacio de cerrojo 2 (GitHub) del curso** y además el cerrojo por `repositorio_id` durante su fase de escritura |

**El orden de llegada es irrelevante por diseño.** GitHub no garantiza orden de entrega y el sistema no lo necesita: los commits son hechos independientes identificados por su SHA, y todo lo que depende del orden —la cabeza de una rama, el conjunto de huérfanos, los agregados— **se deriva, no se acumula**.

**Cerrojos**: se usa siempre `pg_advisory_xact_lock`, que se libera con la transacción; **nunca** el cerrojo de sesión en la ruta de ingesta.

### 10.2.5 Resolución del destino de un evento

Tras validar la firma y persistir la entrega, el destino de cada evento se resuelve con una **cascada cerrada de cinco pasos, exhaustiva y mutuamente excluyente**. Ningún evento cae en una rama sin nombre.

| # | Se intenta resolver por | Resultado |
|---|---|---|
| 1 | `repository.id` contra `repositorio.github_repo_id` | Destino: repositorio de estudiante o grupo. Procesamiento normal |
| 2 | `repository.id` contra `repositorio_base.github_repo_id` | Destino: repositorio base (§10.2.7) |
| 3 | `repository.name` igual al repositorio de operaciones del curso de esa instalación | `estado = DESCARTADO_ESPERADO`. **No es ruido y no abre nada** |
| 4 | `(curso de la instalación, repository.name)` contra `repositorio.nombre` con `github_repo_id` **nulo** | Destino: repositorio recién creado cuyo `201` aún no se ha persistido. Se rellena `github_repo_id` con el del payload y se procesa. Es el caso de carrera del aprovisionamiento masivo |
| 5 | Nada casa | `estado = SIN_DESTINO_PENDIENTE`, con reintento y caducidad |

**Por qué el paso 4 siempre tiene contra qué casar:** la fila del repositorio se **reserva antes de llamar a GitHub** (`repositorio.estado = CREANDO`), el nombre se calcula antes de crear y **no cambia nunca**, y `(curso_id, nombre)` es único. El paso 4 sólo actúa sobre filas con `github_repo_id` nulo, es decir, sobre repositorios que la propia aplicación acaba de pedir.

**Eventos sin destino.** Se reintentan con retroceso exponencial —1, 5, 15 y 60 minutos— durante **24 horas**. Si en ese plazo aparece el destino, el evento se procesa con normalidad. Agotado el plazo, pasa a `DESCARTADO_SIN_DESTINO` **conservando su cabecera indefinidamente**, y **no se abre ninguna incidencia**: se cuenta en `/operacion` como «entregas sin destino en las últimas 24 h».

**Repositorios de la organización que la aplicación no conoce.** El trabajo `verificar_instalacion_github` los lista cada hora y los **reporta** en `/operacion` como «repositorios no reconocidos», con nombre, topics y fecha de creación. **Nunca se adoptan automáticamente por coincidencia de nombre, de topic ni de plantilla**: la adopción es la del capítulo 8, con sus cinco condiciones, y sólo ocurre cuando el aprovisionador llega a ese sujeto. Adoptar por patrón entregaría a un estudiante el repositorio de otro.

> **[DECISION NUEVA]** El estado de `evento_webhook` que en las respuestas de alcance se llamaba `HUERFANO` pasa a llamarse **`SIN_DESTINO_PENDIENTE`**. Motivo: A-154 prohíbe usar el mismo término para dos hechos, y «huérfano» ya designa un commit que dejó de ser alcanzable (`commit.huerfano`). La enumeración completa de `evento_webhook.estado` queda en **ocho valores**: `RECIBIDO`, `PENDIENTE_BLOQUE_2`, `PROCESADO`, `IGNORADO`, `SIN_DESTINO_PENDIENTE`, `DESCARTADO_ESPERADO`, `DESCARTADO_SIN_DESTINO`, `ERROR`; se declara en `backend/app/dominio/estados.py` y su `CHECK` viaja completo en la migración inicial.

### 10.2.6 Volcado inicial y relleno hacia atrás

**Volcado inicial de un repositorio.** Cuando un repositorio entra al sistema —transición a `CONTENIDO_LISTO`— se programa un volcado con `GET /repos/{o}/{r}/commits?sha=<rama_por_defecto>&per_page=100`, **tope de 30 páginas**, ejecutado por `barrido_completo_actividad` y **fuera de la ruta de aprovisionamiento**, para no sumar llamadas al presupuesto de creación. El resultado se escribe en `cursor_sincronizacion` (`ultimo_backfill_en`, `ultimo_head_sha`, `estado`).

En la práctica cuesta **una página por repositorio**, porque todos los repositorios de estudiantes los crea la aplicación y su historia empieza vacía o con el commit de la plantilla. El tope de 30 páginas existe para el único caso en que la historia puede ser larga: un repositorio adoptado tras un reintento. Si el tope se agota, `cursor_sincronizacion.estado = TRUNCADO`, incidencia informativa, reintento en el barrido siguiente y el timeline declara «historia anterior no ingerida». **Nunca se muestra un número como si fuera completo.**

**Relleno hacia atrás, obligatorio y no opcional.** El cuerpo de `evento_webhook` se retiene 7 días, de modo que los cuerpos crudos de la ventana **16 → 23 de septiembre no existen** cuando el procesamiento de `push` entra en servicio. Al activarse ese bloque, `barrido_completo_actividad` ejecuta, **para cada repositorio y una sola vez**, un relleno histórico con `GET /repos/{o}/{r}/commits?sha=<rama_por_defecto>&since=<repositorio.listo_en>` paginado por `Link`, con clave de idempotencia `(repositorio_id, 'backfill')`, y escribe `cursor_sincronizacion.ultimo_backfill_en`.

Consecuencias declaradas:

1. El relleno **no depende de los cuerpos retenidos** y deja `commit` completo **desde `repositorio.listo_en`**, de modo que **R2.5.2** y **R2.5.3** cubren también los días previos a la entrada en servicio del procesamiento.
2. **El instante desde el que la ingesta es fiable se escribe en `curso.ingesta_actividad_desde`**, y de ahí lo lee el criterio de significación temporal de §10.7.2.
3. El criterio para retirar la bandera de alcance correspondiente es: **relleno ejecutado y `ultimo_backfill_en` escrito en todos los repositorios**.

**El volcado inicial no se sustituye por escritura directa.** Ninguna fila de `commit`, `version_entrega`, `metrica_repositorio_dia` ni `participacion_entrega` se inserta si no procede de la ingesta normal, tampoco en el curso de demostración: la carga histórica se produce con commits reales retrodatados en repositorios reales, y entra al espejo por el relleno hacia atrás y por el barrido nocturno.

### 10.2.7 Actividad del repositorio base

El repositorio base de una tarea **se reconoce y se ingiere de forma acotada, y se excluye por completo de R2.5**:

| Aspecto | Regla |
|---|---|
| `push` sobre el repositorio base | Actualiza `repositorio_base.rama_por_defecto` cuando cambia y `repositorio_base.ultimo_push_en`; alimenta el **historial de cambios del repositorio base** —quién subió, reemplazó, renombró o borró qué archivo y cuándo— que se muestra en la pantalla del repositorio base (R2.3.6) |
| Sus commits | **No entran** en `commit`, ni en `metrica_repositorio_dia`, ni en `participacion_entrega`, ni en ninguna serie, tarjeta, alerta o informe de R2.5 |
| Timeline | El repositorio base **no tiene vista de timeline de R2.5.10**: tiene el historial de archivos descrito |

Motivo: el repositorio base no tiene sujeto ni integrantes y no es trabajo de estudiantes; contarlo falsearía todas las medias del curso.

### 10.2.8 Hasta cuándo se ingiere, y retención

Un repositorio entra en `reconciliar_actividad`, `barrido_completo_actividad` y `precierre_actividad` mientras se cumplan **las tres** condiciones, evaluadas por una **única función de dominio `repositorio_en_ingesta(repositorio, tarea, fechas, ahora)`** que usan los tres trabajos:

| # | Condición |
|---|---|
| 1 | `repositorio.estado ∈ {OPERATIVO, DEGRADADO}` — quedan fuera `ARCHIVADO`, `INACCESIBLE`, `FUERA_DE_ALCANCE` y los estados de error |
| 2 | `tarea.estado ∈ {ACTIVA, INCONSISTENTE}` — quedan fuera `BORRADOR`, `CERRADA` y `ARCHIVADA` |
| 3 | `ahora ≤ max(due_at_utc de las fechas efectivas vigentes de ese sujeto) + 14 días` (**cola de gracia**) |

La cola de gracia de 14 días cubre las recapturas por cambio de fecha, la corrección de la entrega final y las dos semanas posteriores a la entrega que exige §3.2 del enunciado. Fuera de esas condiciones, el repositorio **sigue recibiendo webhooks** —cuestan cero peticiones y su procesamiento es local— y deja de consumir presupuesto de sondeo. **Una reprogramación reactiva la ingesta**: si la sincronización de fechas detecta un cambio que mueve una fecha efectiva al futuro, el repositorio vuelve a entrar en los tres trabajos en el ciclo siguiente.

**Retención**, con freno automático por tamaño de base:

| Dato | Retención |
|---|---|
| Cuerpo de `evento_webhook` (`payload`) | **Truncado a 64 KB** al escribirse, con `payload_bytes` y `payload_truncado`; se conserva **7 días**, que bajan a **3 días** si el tamaño de la base supera 300 MB. Por encima de 400 MB se abre `BASE_CERCA_DEL_LIMITE` y **se deja de persistir cuerpos nuevos** |
| Cabecera de `evento_webhook` | **Indefinida**: `delivery_id`, evento, acción, firma válida, tiempos, estado y error. La deduplicación por `delivery_id` sigue funcionando para siempre |
| `commit`, `autoria_commit`, `version_entrega`, `bitacora`, `publicacion_nota` | **Sin purga: son evidencia** |
| `evento_push`, `cursor_sincronizacion` | Sin purga; volumen despreciable |

**La recomputación histórica de métricas no depende de los payloads.** Como los agregados se recomputan desde `commit` y `autoria_commit`, corregir una regla de atribución y recalcular todo el semestre es **un pase nocturno de `agregar_metricas`**, sin reingerir nada de GitHub y sin necesitar un solo cuerpo crudo.

### 10.2.9 Presupuesto de llamadas y estados transitorios

Todo límite de tasa observado vive en la tabla **`presupuesto_api`**, con unicidad `(ambito, ambito_id, cubo)` y **cuatro cubos** (A-219, RG-071). Los que consume este capítulo son:

| Cubo | Ámbito | Consumidores de este capítulo |
|---|---|---|
| `PRIMARIO` | `GITHUB_INSTALACION` | `reconciliar_actividad`, `barrido_completo_actividad`, `precierre_actividad`, relleno de `compare` y recorridos de historia |
| `GRAFO` | `GITHUB_INSTALACION` | El enriquecimiento por GraphQL de §10.3.5 |

Reglas de freno, idénticas para los dos cubos:

1. Objetivo autoimpuesto: **no bajar del 50 %** del límite real medido en la hora.
2. Por debajo del **20 %** de límite restante, `reconciliar_actividad` **reduce su lote a la mitad** y el enriquecimiento por GraphQL **se detiene por completo**, por ser el único dato del sistema que ninguna alerta necesita.
3. Por debajo del **10 %**, `reconciliar_actividad` sólo procesa repositorios con una entrega abierta en las próximas 24 horas.
4. Techo de concurrencia autoimpuesto: **4**, frente a los 100 documentados.
5. Ante `403` o `429` se respeta `retry-after`; si no viene y el restante es 0, se espera hasta el reinicio; en cualquier otro caso se espera al menos un minuto y se retrocede exponencialmente hasta 6 intentos.
6. El estado resultante es **`ESPERANDO_LIMITE`, nunca `ERROR`**. La interfaz muestra, en ámbar y no en rojo: **«Esperando a GitHub por límite de uso. Reintento automático a las HH:MM.»** Un límite de API **nunca se pinta como error del equipo**.

### 10.2.10 Modelo de datos de la ingesta

| Tabla | Columnas relevantes de este capítulo | Unicidad e índices |
|---|---|---|
| `evento_webhook` | `id`, `delivery_id`, `evento`, `accion`, `firma_valida`, `payload` (jsonb, truncado a 64 KB), `payload_bytes`, `payload_truncado`, `repositorio_id` (nullable), `repositorio_base_id` (nullable), `motivo_no_resuelto`, `recibido_en`, `procesado_en`, `estado`, `error` | **único `delivery_id`** |
| `evento_push` | `id`, `repositorio_id`, `delivery_id`, `ref`, `before_sha`, `after_sha`, `n_commits_payload`, `completado`, `forzado`, `divergido`, `n_commits_huerfanos`, `recibido_en` | índice `(repositorio_id, recibido_en)` |
| `commit` | `id`, `repositorio_id`, `sha` (char 40), `parent_shas` (text[]), `n_padres`, `es_merge`, `rama_detectada`, `en_rama_por_defecto`, `mensaje_resumen`, `autor_nombre`, `autor_email`, `autor_github_user_id`, `committer_github_user_id`, `fecha_autor`, `fecha_committer`, `via_web`, `adiciones`, `eliminaciones`, `archivos_tocados`, `sin_cambios`, `identidad_git_id`, `estudiante_id`, `regla_atribucion`, `motivo_exclusion`, `autor_es_bot`, `autor_es_docente`, `huerfano`, `huerfano_desde`, `historia_importada`, `firma_estado`, `firma_motivo`, `origen_ingesta`, `recibido_en`, `ingresado_en`, `enriquecido_en` | **único `(repositorio_id, sha)`**; índices `(repositorio_id, fecha_committer)`, `(repositorio_id, estudiante_id, fecha_committer)` y `(repositorio_id, en_rama_por_defecto, fecha_committer)` |
| `cursor_sincronizacion` | `id`, `curso_id`, `recurso`, `referencia`, `etag`, `ultimo_head_sha`, `per_page_medido`, `ultimo_exito_en`, `ultimo_backfill_en`, `estado`, `ultimo_error` | **único `(curso_id, recurso, referencia)`** |
| `presupuesto_api` | `ambito`, `ambito_id`, `cubo`, capacidad, restante, reinicio, observado en | **único `(ambito, ambito_id, cubo)`** |

Enumeraciones cerradas de la ingesta, todas declaradas en `backend/app/dominio/estados.py` y con su `CHECK` generado desde ahí:

| Columna | Valores |
|---|---|
| `commit.origen_ingesta` | `WEBHOOK`, `RELLENO_COMPARE`, `RECORRIDO`, `RECONCILIACION`, `BARRIDO`, `BACKFILL_INICIAL` |
| `commit.motivo_exclusion` | `NINGUNO`, `MERGE`, `COMMIT_INICIAL`, `HUERFANO` |
| `commit.regla_atribucion` | `AUTOR_GITHUB`, `EMAIL_NOREPLY`, `EMAIL_DIRECTO`, `IDENTIDAD_DOCENTE`, `SIN_ATRIBUIR` |
| `commit.firma_estado` | `VERIFICADA`, `NO_VERIFICADA`, `DESCONOCIDA` (por defecto) |
| `cursor_sincronizacion.estado` | `AL_DIA`, `BACKFILL_PENDIENTE`, `TRUNCADO`, `ERROR` |
| `evento_webhook.estado` | Los ocho de §10.2.5 |

Dos columnas de `commit` tienen semántica próxima y **no son sinónimos**: `recibido_en` es el instante en que la aplicación supo del SHA por primera vez —el `recibido_en` del `evento_push` cuando viene por webhook, el instante del ciclo en otro caso—, se escribe **una sola vez** y nunca se actualiza; `ingresado_en` es el instante de la escritura de la fila. La diferencia entre ambos mide el retraso del trabajador y se publica en `/operacion`.

### 10.2.11 Criterios de aceptación de §10.2

1. Enviar dos veces la misma entrega de webhook con el mismo `X-GitHub-Delivery` y comprobar que `commit`, `metrica_repositorio_dia` y `participacion_entrega` quedan **idénticos** y que `/operacion` incrementa el contador de entregas duplicadas descartadas.
2. Enviar una entrega con firma inválida y comprobar que se persiste con `firma_valida = false`, que **no se procesa** y que la respuesta sigue siendo `202` en menos de 200 ms.
3. Lanzar el receptor y el reconciliador a la vez sobre el mismo repositorio y comprobar, en el registro, que se serializan por `repositorio_id` y que ningún commit se duplica.
4. Empujar una rama nueva con 250 commits y comprobar que el timeline los muestra todos y que `evento_push.completado = true`.
5. Ejecutar `push --force` que descarte tres commits y comprobar que las tres filas siguen en `commit` con `huerfano = true` y `huerfano_desde` escrito, que `evento_push.divergido = true` y `n_commits_huerfanos = 3`, y que el timeline muestra el hito «historia reescrita».
6. Detener el trabajador 20 minutos, empujar un commit y comprobar que aparece en el tablero en el ciclo siguiente de `reconciliar_actividad`, con el sello de antigüedad correspondiente.
7. Enviar un evento `push` de un repositorio que no está en la base y comprobar que queda `SIN_DESTINO_PENDIENTE`, que se reintenta y que a las 24 horas pasa a `DESCARTADO_SIN_DESTINO` **sin abrir ninguna incidencia** y apareciendo en `/operacion`.
8. Empujar un commit al repositorio base y comprobar que aparece en su historial de archivos y que **no** aparece en ninguna métrica ni en ninguna serie de la tarea.
9. Comprobar en `/operacion` que el techo garantizado que se muestra coincide con `ceil(recuento / 200) × 15 min` para el recuento real del curso, y que ese recuento excluye los `ARCHIVADO`, `FUERA_DE_ALCANCE` e `INACCESIBLE`.
10. Forzar `x-ratelimit-remaining` por debajo del 20 % y comprobar que la vista muestra el texto ámbar de espera con la hora de reintento y que el estado del trabajo es `ESPERANDO_LIMITE`, nunca `ERROR`.

---

## 10.3 Atribución de commits a estudiantes

### 10.3.1 La cascada de atribución

La atribución es el punto donde una regla mal elegida produce **acusaciones falsas de no participar**. La cascada tiene **cinco resultados posibles**, se evalúa en este orden exacto y **gana la primera regla que casa** (A-118, A-205):

| # | Regla | Condición | Confianza | Resultado |
|---|---|---|---|---|
| 1 | `AUTOR_GITHUB` | El commit trae `author.id` y ese `github_user_id` está en un `mapeo_github` **vigente** del curso | **ALTA** | Atribuido |
| 2 | `EMAIL_NOREPLY` | `author.email` tiene la forma `ID+login@users.noreply.github.com` y el `ID` coincide con un mapeo vigente | **ALTA** | Atribuido |
| 3 | `EMAIL_DIRECTO` | El correo del autor coincide, normalizado, con el correo conocido del estudiante en Canvas | **MEDIA** | Atribuido y **marcado como señal débil en la interfaz** |
| 4 | `IDENTIDAD_DOCENTE` | Un miembro del equipo docente con `mapeo.editar` asoció esa identidad de Git a un estudiante | **ALTA** | Atribuido, con actor y fecha en `bitacora` |
| 5 | `SIN_ATRIBUIR` | Ninguna de las anteriores | — | `estudiante_id` nulo y **visible como «commits sin atribuir»** |

Reglas de aplicación, sin excepción:

1. **Una regla posterior nunca sobrescribe a una anterior.** La reatribución de §10.3.4 sólo **mejora**: sustituye una regla más débil por otra más fuerte, y el cambio queda en `bitacora`.
2. **La clave es siempre el `github_user_id` numérico.** **Nunca se compara por `login`.** Existe una prueba automatizada que falla si alguna consulta une por `login`.
3. **El nombre no atribuye.** No existe regla automática por nombre normalizado: la documentación admite que el usuario de GitHub asociado a un commit puede no venir, y adivinar por nombre produce homónimos atribuidos mal. El nombre **sí se muestra** en el bloque de commits sin atribuir, como contexto para que una persona decida.
4. **Normalización del correo**: minúsculas y recorte de espacios. **No se eliminan puntos ni sufijos `+etiqueta`**, porque esa equivalencia es propia de un proveedor concreto y no es universal.
5. **La regla 3 es condicional.** Depende de que el token del profesor pueda ver el correo del estudiante en Canvas, hecho **no fijado**. Si la comprobación sale negativa, **la regla 3 desaparece y no pasa nada más**: la cobertura baja, la aplicación lo declara en pantalla y las reglas 1, 2 y 4 cubren el resto.
6. **La firma criptográfica del commit no participa en la atribución.** `commit.firma_estado` y `commit.firma_motivo` son informativos, se muestran como icono discreto en la capa 1 del timeline y en la ficha del commit, y **nunca modifican `metrica_repositorio_dia.commits` ni `participacion_entrega.commits`**. Ponderar por firma produciría acusaciones falsas masivas, porque ningún estudiante de pregrado tiene clave GPG o SSH configurada por defecto, y además una firma prueba integridad, no identidad frente al mapeo del curso. **No se pide a los estudiantes que firmen sus commits.**
7. **Sí se les pide configurar el correo de Git.** La instrucción viaja por los tres canales que ya existen —el enunciado de la tarea de registro, el comentario de confirmación del mapeo y el anuncio de curso al inicio de cada tarea— con este texto: «usa en tus commits el correo asociado a tu cuenta `<login>` de GitHub, o el correo `ID+login@users.noreply.github.com`».

### 10.3.2 `autoria_commit`: una sola tabla de autoría

«Qué estudiantes se acreditan por un commit» vive en **una única tabla, `autoria_commit`** (A-205, RG-029). **La tabla `commit_autoria` no existe**, y ninguna pantalla ni columna usa el valor `IDENTIDAD_MANUAL`.

| Columna | Tipo y restricción |
|---|---|
| `commit_id` | uuid, obligatorio, referencia a `commit` con `ON DELETE RESTRICT` |
| `estudiante_id` | uuid, nullable, referencia a `estudiante` con `ON DELETE RESTRICT` |
| `identidad_git_id` | uuid, nullable, referencia a `identidad_git` con `ON DELETE RESTRICT` |
| `papel` | texto, obligatorio, `CHECK IN ('AUTOR','COAUTOR')` |
| `regla_atribucion` | texto, obligatorio, `CHECK IN ('AUTOR_GITHUB','EMAIL_NOREPLY','EMAIL_DIRECTO','IDENTIDAD_DOCENTE','SIN_ATRIBUIR')` |
| `confianza` | texto, obligatorio, `CHECK IN ('ALTA','MEDIA')` |
| — | `CHECK (estudiante_id IS NOT NULL OR identidad_git_id IS NOT NULL)` |
| **Clave primaria** | `(commit_id, coalesce(estudiante_id, identidad_git_id))` |

Reglas:

1. El discriminador se llama **`papel`** y no `tipo`, porque `tipo` ya está tomado en `cuenta_github.tipo`, `sujeto.tipo` y `entrega.tipo`.
2. `commit.estudiante_id`, `commit.regla_atribucion` y `commit.identidad_git_id` **se conservan denormalizados** como autor principal y **coinciden siempre con la fila `papel = 'AUTOR'`**. Una prueba de dominio falla si divergen.
3. **Todos los agregados de participación se calculan desde `autoria_commit`**, nunca desde `commit.estudiante_id`.
4. Un **co-autor no resuelto** se representa con `estudiante_id` nulo, `identidad_git_id` apuntando a su fila y `regla_atribucion = 'SIN_ATRIBUIR'`, y aparece en el timeline como **co-autor no atribuido**.
5. `participacion_entrega` recibe dos columnas derivadas: **`commits_coautorados`** y **`commits_sin_atribuir_repo`**.

> **Corrección de una respuesta de alcance.** La tabla hermana `participacion_sin_atribuir` **no existe**: no está en el censo cerrado de 70 entidades. La fila «Sin atribuir» de la comparación entre integrantes se deriva de `autoria_commit` con `estudiante_id` nulo, y su recuento vive denormalizado en `participacion_entrega.commits_sin_atribuir_repo`.

### 10.3.3 Co-autores

| # | Regla | Motivo |
|---|---|---|
| 1 | **Fuente única: `Commit.authors` de GraphQL**, que es el campo documentado como «la lista de autores de este commit basada en el autor git y en el trailer `Co-authored-by`, con el autor git siempre primero». **No se escribe ningún analizador propio de mensajes de commit** | Un analizador propio duplicaría lógica con peor cobertura |
| 2 | **Un co-autor sólo cuenta si se resuelve** por la misma cascada de §10.3.1. El que no resuelve no cuenta y aparece en el timeline como co-autor no atribuido | Coherente con cómo GitHub acredita la contribución |
| 3 | **Peso 1 completo por persona.** El commit cuenta **una vez para cada acreditado**: `participacion_entrega.commits` suma 1 al autor git y 1 a cada co-autor resuelto | Repartir medio commit inventa una aritmética sin respaldo y rompe el umbral «cero commits» |
| 4 | **Las líneas se atribuyen íntegras al autor git y no se suman al co-autor**, con la etiqueta «commit compartido» | No inflar una métrica que la propia interfaz declara señal débil |
| 5 | **La consecuencia se declara en pantalla**: la suma de commits por integrante **puede superar** el total de commits del repositorio, y la comparación lo dice literalmente junto al gráfico, con el desglose de `commits_coautorados` | Un número que no cuadra sin explicación es peor que un número menos preciso |
| 6 | Las **exclusiones de §10.5.1 se aplican antes**: un merge con co-autores sigue sin contar para nadie | Predicado único |
| 7 | Si el enriquecimiento por GraphQL degrada, **los co-autores no se cuentan**, `autoria_commit` queda con la única fila del autor git y la interfaz lo dice: «co-autores no disponibles en este curso». **No se inventa una vía alternativa** | Degradación declarada de antemano |

Un estudiante no puede inflar su participación añadiendo co-autores falsos: el co-autor **sólo cuenta si resuelve a un `mapeo_github` vigente del mismo curso**, de modo que sólo puede acreditar a un compañero real, y la comparación muestra `commits_coautorados` aparte.

### 10.3.4 Identidades de Git no resueltas y corrección docente

Los autores no resueltos se agrupan en **`identidad_git`**, cuya unidad es **`(repositorio_id, email_normalizado)`**, de modo que una persona con `mapeo.editar` asocia de una vez todos los commits de un mismo autor no resuelto.

`identidad_git` es ***append-only*** y su unicidad es **parcial** (RG-006):

| Columna | Regla |
|---|---|
| `curso_id` | Obligatoria, derivada de `repositorio` al insertar. **No participa en ningún índice único**: sirve al índice **no único** `(curso_id, email_normalizado)` que sostiene la propuesta de propagación |
| `estado` | `SIN_RESOLVER` (por defecto), `RESUELTA`, `NO_ES_ESTUDIANTE`, `SUPERSEDIDA` |
| `resuelta_por`, `resuelta_en` | Actor y fecha de la corrección |
| `vigente_desde`, `vigente_hasta` | Vigencia de la fila |
| `nombre_visto`, `nombre_visto_ultimo` | Nombre de autor tal como llegó en los commits |
| Índice único | **parcial**: `(repositorio_id, email_normalizado) WHERE estado <> 'SUPERSEDIDA'` |

`commit.identidad_git_id` apunta a **la fila que se vio en la ingesta**; la lectura resuelve por `(repositorio_id, email_normalizado)` a la fila vigente, de modo que una supersesión **no obliga a reescribir decenas de miles de filas de `commit`**.

**Corrección docente**, con seis reglas:

1. **La unidad de corrección es la identidad, no el commit.** Se corrige `(repositorio_id, email_normalizado)`, y todos sus commits pasados y futuros heredan la corrección.
2. **Es *append-only***: corregir cierra la fila vigente y crea otra; **nunca se edita en sitio**. Queda en `bitacora` con la acción `IDENTIDAD_GIT_RESUELTA` o `IDENTIDAD_GIT_SUPERSEDIDA`.
3. **Retroactividad total dentro del repositorio.** Se reescribe `autoria_commit` con `regla_atribucion = 'IDENTIDAD_DOCENTE'` **sólo para los commits que las reglas 1 a 3 no habían resuelto**: la corrección docente **nunca pisa** a `AUTOR_GITHUB` ni a `EMAIL_NOREPLY`. Si se intenta corregir una identidad ya resuelta automáticamente, la pantalla lo advierte y exige una **confirmación escrita** que queda en `bitacora`.
4. **La propagación al resto del curso es una propuesta, nunca automática.** Tras aplicar la corrección, la pantalla lista los demás repositorios del curso donde aparece el mismo correo normalizado, con nombre visto y número de commits, y **casillas desmarcadas por defecto**; se aplica sólo a lo marcado, en una sola transacción, y cada aplicación crea su propia fila `RESUELTA` en el repositorio de destino. **El motivo se declara por escrito en la pantalla:** correos genéricos como `user@localhost`, `root@localhost` o el de un ejecutor de integración continua aparecen en repositorios de estudiantes distintos, y una identidad de curso **atribuiría el trabajo de uno a otro**.
5. **Recomputo inmediato.** En la misma transacción se encola `agregar_metricas` para los repositorios afectados, que recomputa `participacion_entrega` y `metrica_repositorio_dia`, reevalúa el predicado de participación y **cierra automáticamente** las incidencias `SIN_PARTICIPACION` cuya causa desaparece, dejando constancia del motivo del cierre.
6. **Nunca crea ni modifica un `mapeo_github`.** Asociar un correo de Git a un estudiante es un hecho sobre la atribución de commits; el mapeo estudiante ↔ cuenta de GitHub tiene sus propias vías. Confundirlos permitiría dar un repositorio a alguien a partir de un correo escrito en un commit, que no prueba nada.

También se puede marcar una identidad como **`NO_ES_ESTUDIANTE`**, lo que la excluye del predicado de participación **sin atribuirla a nadie**. Es la salida para el correo de un bot, de un ejecutor de integración continua o de una persona ajena al curso.

**Reatribución automática.** El paso 1 de cada ciclo de `agregar_metricas` reevalúa la cascada sobre los commits de la ventana cuyo `estudiante_id` sea nulo o cuya `regla_atribucion` sea más débil que la ahora disponible; el pase nocturno completo la reevalúa sobre el curso entero. Los disparadores explícitos son cuatro, y los cuatro escriben en `bitacora` y marcan el curso para pase completo:

| Disparador | Efecto |
|---|---|
| Un `mapeo_github` pasa a `VIGENTE` | Se reatribuyen los commits de ese `github_user_id` y de su correo `noreply` |
| Un mapeo se supersede por corrección | Igual, con la cuenta nueva |
| Se resuelve una `identidad_git` | Reescritura de `autoria_commit` del repositorio, y de los propagados |
| Cambia la composición del equipo docente | Recálculo de `commit.autor_es_docente` en el pase nocturno |

**No puede haber doble conteo por reatribuir**, porque los agregados se recomputan desde `autoria_commit` y no tienen memoria propia.

### 10.3.5 Enriquecimiento por GraphQL

Los campos que sólo GraphQL entrega —`authors`, `committedViaWeb`, `parents.totalCount`, `additions`, `deletions`, `changedFilesIfAvailable`— se piden en **una única consulta por lotes de 100 commits**, encolada tras la ingesta:

| Aspecto | Regla |
|---|---|
| Cubo de presupuesto | **`GRAFO`**, con capacidad y recarga derivadas de las cabeceras de la propia respuesta GraphQL. **No consume del presupuesto REST** |
| Tope propio | **3 consultas por minuto por instalación**. Con lotes de 100, los 30 000 commits de un semestre son 300 consultas, es decir unos 100 minutos repartidos |
| Prioridad | **La más baja**: cede ante las escrituras síncronas, la creación de etiquetas y el aprovisionamiento |
| Corte | **Se detiene por completo por debajo del 20 %** de límite restante |
| Tope por repositorio y ciclo | **200 commits**, priorizando los de los períodos de entrega abiertos |
| Marca de progreso | `commit.enriquecido_en`, que evita repetir y alimenta el contador «commits pendientes de enriquecer» de `/operacion` |
| Instrumentación | Cada respuesta registra sus cabeceras en `presupuesto_api` y en `/operacion` |

**Vía de respaldo y degradación, escritas de antemano:**

1. Si los campos de líneas no llegan por GraphQL, se usa `GET /repos/{o}/{r}/commits/{sha}` **sólo para commits contables**, en un enriquecimiento de baja prioridad con el mismo corte al 20 %.
2. Si tampoco cabe en el presupuesto, `adiciones` y `eliminaciones` quedan **nulas** y la interfaz muestra **«no disponible»**. **Nunca se muestra un cero como si fuera un dato**, porque un cero falso convertiría un commit normal en «sin cambios».
3. Si `authors` no llega, **los co-autores no se cuentan** y la interfaz declara «co-autores y ediciones desde la web no disponibles en este curso».
4. **Ninguna funcionalidad se cae por esta degradación**, porque **ninguna métrica que gobierne una alerta depende de las líneas**.

`commit.archivos_tocados` se calcula **sin coste** del propio payload de `push`, sumando `added`, `removed` y `modified`.

**Los endpoints `stats/` de GitHub no se usan**: ni como fuente agregada, ni para volcado inicial, ni para contraste. Las tres razones se escriben en la memoria de entrega: serían **una segunda verdad** —agregan por autor de Git y no por la cascada de atribución—; su comportamiento **no está respaldado por documentación verificada**, incluido el `202` que devuelven mientras GitHub calcula la caché; y **su coste en puntos no es presupuestable**, porque no se publica.

### 10.3.6 Datos personales de terceros en los commits

Un commit puede llevar el correo de cualquiera —un co-autor, el autor de un fragmento copiado, alguien que usó la misma máquina—, y esos terceros no son parte del curso. La regla es la misma en todas las pantallas:

| Situación | Qué se muestra |
|---|---|
| Commit atribuido por las reglas 1, 2, 3 o 4 | **El nombre del estudiante en Canvas**, no el nombre ni el correo de Git, más la marca de la regla de atribución. La regla 3 se marca como **débil** |
| Commit sin atribuir | **El nombre de autor tal como viene en el commit** —texto que el propio autor eligió publicar en la historia— y el **correo ofuscado**, con la forma `jp•••@g•••.com`, conservando la primera letra de la parte local y la del dominio |
| Correo `ID+login@users.noreply.github.com` | **Se muestra completo, sin ofuscar y sin acción de revelado.** No es un dato de contacto personal: es la evidencia del mapeo y contiene el identificador numérico duradero |
| Correo de Canvas del estudiante | Se muestra **en Personas** a quien tenga `curso.ver`. **No se muestra junto a los commits ni en el timeline** |

**Revelar el correo completo** es una acción explícita, disponible sólo con **`mapeo.editar`**, **sobre un autor cada vez**, y **queda en `bitacora`** con la acción `EMAIL_AUTOR_REVELADO`, el actor, el repositorio y la identidad de Git.

Dos garantías técnicas:

1. **La ofuscación se aplica en el esquema de salida del servidor**, no en el navegador, de modo que el correo completo **no viaja** al cliente salvo por el endpoint de revelado.
2. Existe una **prueba automatizada que falla la construcción** si algún esquema de salida de las rutas de seguimiento contiene un correo sin ofuscar.

La pantalla de resolución de identidades muestra siempre este texto fijo: **«Estos correos vienen de los commits y pueden pertenecer a personas ajenas al curso. Úsalos sólo para asociar una cuenta y no los compartas fuera de la aplicación.»**

### 10.3.7 Endpoints de atribución

| Método y ruta | Permiso | Qué hace |
|---|---|---|
| `GET /api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/identidades` | `curso.ver` | Lista las identidades de Git del repositorio con correo ofuscado, nombre visto, número de commits contables y fechas del primero y del último |
| `POST /api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/identidades/{identidad_id}/resolver` | `mapeo.editar` | Cuerpo `{estudiante_id | no_es_estudiante: true, propagar_a: [repositorio_id]}`. Aplica las seis reglas de §10.3.4 en una transacción y encola el recomputo |
| `GET /api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/identidades/{identidad_id}/propagacion` | `mapeo.editar` | Devuelve los repositorios candidatos del curso con el mismo correo normalizado |
| `POST /api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/identidades/{identidad_id}/revelar` | `mapeo.editar` | Devuelve el correo completo y escribe `bitacora` en la misma transacción |

> **[DECISION NUEVA]** Las respuestas de alcance situaban la resolución de identidades bajo `/api/cursos/{c}/repos/{r}/…` y el revelado bajo `/api/cursos/{c}/identidades-git/{id}/…`. Se normalizan las cuatro rutas bajo el prefijo `/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/`, que es el mismo del timeline, porque `identidad_git` cuelga del repositorio y el repositorio cuelga de la tarea. La normalización no cambia ninguna regla de negocio ni ningún permiso.

### 10.3.8 Criterios de aceptación de §10.3

1. Crear un commit con un correo desconocido y comprobar que queda `SIN_ATRIBUIR`, que aparece agrupado en «Correos sin atribuir» del repositorio y que **ningún integrante del grupo aparece como «sin participación»** mientras esa fila exista.
2. Resolver esa identidad hacia un estudiante y comprobar, en menos de un ciclo, que sus commits **pasados** quedan atribuidos con `regla_atribucion = IDENTIDAD_DOCENTE`, que `participacion_entrega` se recalcula y que la incidencia se cierra con motivo.
3. Intentar resolver una identidad ya atribuida por `AUTOR_GITHUB` y comprobar que la pantalla exige confirmación escrita y que, tras confirmar, **la atribución de confianza alta no se pisa**.
4. Aplicar una propagación con dos casillas marcadas de cuatro candidatos y comprobar que sólo se crean dos filas `RESUELTA` y que la bitácora registra actor, fecha y alcance.
5. Empujar un commit con dos trailers `Co-authored-by` de dos estudiantes del curso y comprobar que `autoria_commit` tiene tres filas —una `AUTOR` y dos `COAUTOR`—, que cada uno suma 1 commit y que las líneas se atribuyen sólo al autor git.
6. Comprobar en la comparación entre integrantes que, con co-autoría, la suma por integrante puede superar el total del repositorio y que la pantalla lo declara junto al gráfico.
7. Abrir el detalle de un commit sin atribuir y comprobar que el correo llega ofuscado en la respuesta de la API; pulsar «revelar» con `mapeo.editar` y comprobar que aparece completo y que queda una fila en `bitacora` con la acción `EMAIL_AUTOR_REVELADO`.
8. Repetir el paso anterior con un usuario sin `mapeo.editar` y comprobar que el control no está disponible y que el endpoint responde `403`.
9. Comprobar que existe y pasa la prueba de CI que falla si un esquema de salida de seguimiento devuelve un correo sin ofuscar, y la que falla si una consulta une por `login`.
10. Desactivar el enriquecimiento por GraphQL y comprobar que la comparación sigue funcionando, que las columnas de líneas muestran «no disponible» y que **ninguna alerta cambia**.

---

## 10.4 Métricas, agregados y alertas: el motor `agregar_metricas`

### 10.4.1 Qué produce y cuándo corre

Un único trabajo, **`agregar_metricas`**, transforma `commit` y `autoria_commit` —el espejo que produce el capítulo 6 de este documento— en los números que el resto del capítulo presenta. Corre **cada 10 minutos sobre los últimos 2 días de cada curso, más un pase nocturno que recorre el curso entero**, con cerrojo `(tipo, curso_id)` (P1, P3). El pase nocturno es lo que garantiza que una corrección de atribución (§10.3.4) o un cambio de zona horaria del curso (§10.5.4) queden reflejados en todo el histórico sin reingerir nada de GitHub.

Cada ciclo ejecuta, **en este orden y siempre los tres pasos**:

1. **Reatribución.** Reevalúa la cascada de §10.3.1 sobre los commits de la ventana cuyo `estudiante_id` sea nulo o cuya `regla_atribucion` sea más débil que la ahora disponible (§10.3.4).
2. **Recomputación de agregados.** Borra e inserta, dentro de una sola transacción, las filas de `metrica_repositorio_dia` y `participacion_entrega` de la ventana recalculada (P3). Ninguna fila se suma a la anterior: se sustituye entera.
3. **Evaluación y materialización de alertas.** Abre, mantiene o cierra las filas de `incidencia` de tipo `SIN_ACTIVIDAD` y `SIN_PARTICIPACION` (§10.4.3) a partir de los agregados que el paso 2 acaba de dejar.

**Consecuencias declaradas, sin excepción:**

- La **latencia máxima de aparición de una alerta** es de 10 minutos desde que el commit que la resuelve o la abre queda ingerido.
- Existe **historial de alertas consultable**: desde cuándo persiste una situación, cuándo se resolvió y quién o qué la resolvió, porque `incidencia` nunca se purga (P6, A-030).
- El **informe diario del capítulo 11 es reproducible**, porque su sección «Sin actividad» lee exactamente la misma tabla `incidencia` que este capítulo pinta en el tablero, y no recalcula con una consulta propia (P2).
- Ejecutar `agregar_metricas` dos veces seguidas sobre la misma ventana **no cambia ninguna fila** (P3, CA-10.4-01).

### 10.4.2 Modelo de datos: agregados y resumen

| Tabla | Columnas relevantes | Unicidad e índices |
|---|---|---|
| `metrica_repositorio_dia` | `repositorio_id`, `dia` (día del curso, §10.5.4), `commits`, `commits_excluidos`, `commits_merge`, `commits_de_bot`, `commits_docentes`, `dias_activos_acumulados` | **PK `(repositorio_id, dia)`** |
| `participacion_entrega` | `entrega_id`, `repositorio_id`, `estudiante_id`, `commits`, `adiciones`, `eliminaciones`, `dias_activos`, `primer_commit_en`, `ultimo_commit_en`, `commits_coautorados`, `commits_sin_atribuir_repo` (§10.3.2, denormalizada, no vive en una tabla propia) | **PK `(entrega_id, repositorio_id, estudiante_id)`** |
| `resumen_tarea` | `tarea_id`, `calculado_en`, `contadores` (jsonb: bloques 1 a 3 del tablero, §10.7.1) | **PK `tarea_id`** |

`commits_excluidos` agrupa los tres motivos cerrados del predicado de §10.5.1 (`MERGE`, `COMMIT_INICIAL`, `HUERFANO`); `commits_merge` se conserva aparte porque el bloque 5 del tablero lo muestra desglosado. `commits_de_bot` y `commits_docentes` son **contadores informativos que nunca restan de `commits`** (§10.5.1). Ninguna de las tres tablas es nueva frente al espejo que §10.2 y §10.3 ya declaran: `resumen_tarea` es la única incorporación de esta sección, y existe **sólo** para que la parte superior del tablero (§10.7) se lea con una consulta por clave primaria y no con un `GROUP BY` en cada petición.

> **Corrección de una respuesta de alcance.** Una tabla hermana `participacion_sin_atribuir` **no existe**, por la misma razón ya fijada en §10.3.2: la fila «Sin atribuir» de la comparación entre integrantes (§10.8.1) se deriva de `autoria_commit` con `estudiante_id` nulo y su recuento vive denormalizado en `participacion_entrega.commits_sin_atribuir_repo`. Esta sección no reabre esa decisión.

### 10.4.3 Catálogo de alertas de seguimiento

Este capítulo produce **exactamente dos tipos de incidencia** del catálogo cerrado que otros capítulos también consumen: **`SIN_ACTIVIDAD`** (§10.5.3, un repositorio) y **`SIN_PARTICIPACION`** (§10.5.3, un estudiante dentro de un repositorio, con su causa de §10.5.3). Las dos son idempotentes por el índice **único parcial `(curso_id, tipo, sujeto_tipo, sujeto_id) WHERE abierta`**: reevaluar el mismo hecho no abre una segunda fila.

| Transición | Regla |
|---|---|
| Abrir | El paso 3 de §10.4.1 inserta la fila cuando el predicado correspondiente (§10.5.3) pasa a verdadero y no existe ya una fila abierta para ese `(tipo, sujeto)` |
| Mantener | Si el predicado sigue siendo verdadero, la fila abierta **no se toca**: ni su fecha de apertura ni su identidad cambian, de modo que «detectada hace N días» siga siendo cierto |
| Cerrar | Cuando el predicado pasa a falso, se escribe `resuelta_en` con `resuelta_por = SISTEMA` y un motivo. **La fila nunca se borra** (P6) |
| Silenciar | Una persona con `curso.ver` puede **silenciar** la alerta (§10.1.2): la incidencia sigue abierta y sigue contando en el historial, pero deja de aparecer en el tablero y en la sección 3 del informe diario del capítulo 11 mientras dure el silenciamiento, y reaparece plegada, con su motivo, en Pendientes |

**Consecuencia de diseño para el capítulo 11:** la sección «Sin actividad» de su informe diario lee `incidencia WHERE tipo IN ('SIN_ACTIVIDAD','SIN_PARTICIPACION') AND abierta AND NOT silenciada`, sin ninguna otra condición, por lo que el umbral y las tres causas de esta sección **son** las que ese informe muestra, letra por letra (P2).

### 10.4.4 Criterios de aceptación de §10.4

1. **CA-10.4-01.** Ejecutar `agregar_metricas` dos veces seguidas sobre la misma ventana y comprobar que ninguna fila de `metrica_repositorio_dia`, `participacion_entrega`, `resumen_tarea` ni `incidencia` cambia en la segunda ejecución.
2. **CA-10.4-02.** Empujar un commit que resuelve la única causa de una incidencia `SIN_PARTICIPACION` abierta y comprobar que, en menos de un ciclo (10 minutos), la incidencia queda cerrada con `resuelta_por = SISTEMA` y con motivo, y que sigue existiendo en el historial.
3. **CA-10.4-03.** Silenciar una incidencia `SIN_ACTIVIDAD` desde Pendientes y comprobar que desaparece del bloque 3 del tablero y de la sección «Sin actividad» del informe diario del mismo día, pero sigue visible, plegada, en Pendientes.
4. **CA-10.4-04.** Comprobar que el tablero, el informe diario del capítulo 11 y Pendientes muestran, para el mismo repositorio y el mismo día, la misma fecha de apertura de una incidencia `SIN_ACTIVIDAD`, porque los tres leen la misma tabla.

---

## 10.5 Predicados operativos: commit contable, actividad y umbral (R2.5.3, R2.5.4)

### 10.5.1 Commit contable

**«Commit contable»** es el predicado único que decide qué commit entra en `metrica_repositorio_dia.commits` y en `participacion_entrega.commits` (§10.1.2). Vive en **una sola función de un solo argumento**, `es_commit_contable(commit)`, en `backend/app/dominio/metricas.py`, y la usan el tablero, el timeline, la comparación entre integrantes y el informe diario del capítulo 11 sin excepción (P2).

Se excluyen **exactamente tres motivos**, cerrados en `commit.motivo_exclusion ∈ {NINGUNO, MERGE, COMMIT_INICIAL, HUERFANO}`:

| Motivo | Condición | Por qué |
|---|---|---|
| `MERGE` | `commit.es_merge = true` (más de un padre) | No es aporte de trabajo nuevo |
| `COMMIT_INICIAL` | `commit.sha = repositorio.commit_inicial_sha` | Es andamiaje de la plantilla, no trabajo del sujeto |
| `HUERFANO` | `commit.huerfano = true` | Dejó de ser alcanzable tras una reescritura de historia (§10.2.3); se conserva como registro, no cuenta como aporte |

**Los commits de bots y del equipo docente SÍ son contables.** Excluirlos ampliaría el predicado más allá de estos tres motivos, y esta sección no lo hace. En su lugar, `commit.autor_es_bot` y `commit.autor_es_docente` son dos **hechos informativos** que se derivan aparte —el primero cuando `autor_github_user_id` resuelve a una cuenta de tipo `BOT` o es la cuenta de la propia GitHub App; el segundo cuando coincide con la cuenta de GitHub de un miembro activo del equipo docente y **no** coincide con ningún `mapeo_github` vigente del curso—, y `metrica_repositorio_dia` los cuenta aparte en `commits_de_bot` y `commits_docentes`, **que nunca restan de `commits`**.

Los commits excluidos **no se pierden**: se cuentan en `commits_excluidos` y `commits_merge` (§10.4.2), y el timeline (§10.9.1) los muestra a todos con su etiqueta —«merge, no cuenta como aporte», «commit inicial de la plantilla», «huérfano: dejó de ser alcanzable el dd-MM»— porque la historia se muestra entera y la métrica se calcula con el predicado (P5).

### 10.5.2 Actividad del repositorio y actividad de los estudiantes

Este capítulo distingue **dos hechos que no son sinónimos** (§10.1.2), y la distinción es la que impide que un `push` del profesor o de un bot apague una alerta que debería seguir abierta:

- **Actividad del repositorio**: existe al menos un commit contable en la ventana, sea quien sea su autor.
- **Actividad de los estudiantes**: existe al menos un commit contable en la ventana con al menos una fila de `autoria_commit` cuyo `estudiante_id` no sea nulo.

Las alertas de **R2.5.3** (§10.5.3) y de **R2.5.4** (§10.5.3) se evalúan sobre la **segunda** función, `hay_actividad_estudiantil(repositorio, ventana)`, nunca sobre el recuento crudo de `commits`. Un `push` del equipo docente arreglando un `README` o un commit automático de un bot de integración continua **no cierra** una alerta de inactividad ni de no participación. La interfaz declara la diferencia con estas palabras, fijas en el archivo único de mensajes (A-154): «actividad del repositorio» frente a «actividad de los estudiantes».

### 10.5.3 Umbral de días sin actividad y las tres causas de «sin participación»

**Origen y rango del umbral.** La columna `curso.umbral_dias_sin_actividad` ya existe en el modelo del curso —el capítulo 4 la menciona de paso, al margen del alcance de ese capítulo— y **esta sección fija su contrato**, porque gobierna un predicado que sólo este capítulo consume: `smallint NOT NULL DEFAULT 7`, con `CHECK BETWEEN 1 AND 30`, editable únicamente con `curso.administrar` desde la pantalla de ajustes del curso. **7 días** es el valor con el que arranca cualquier curso nuevo, y el rango de 1 a 30 excluye tanto un umbral inservible por demasiado corto como uno que no alertaría nunca dentro de un semestre.

**Umbral en ventana crítica.** Cuando un repositorio tiene alguna entrega con fecha efectiva vigente que vence en menos de 72 horas, el umbral que se aplica **a ese repositorio** baja a **2 días**, sin que nadie lo configure: es un valor **derivado**, no una segunda columna, calculado por la misma función que produce el predicado de inactividad. El propósito es que un repositorio parado a tres días de un cierre se marque antes que uno parado a mitad de semestre, sin bajar el umbral general del curso para todos los repositorios a la vez.

**Repositorio sin actividad reciente (R2.5.3).** El predicado es: `hay_actividad_estudiantil(repositorio, ventana) = false` para la ventana de los últimos N días, donde N es el umbral aplicable (7 por defecto, o 2 en ventana crítica). **Un indicador no se pronuncia sobre una ventana más corta que su propio umbral**: la ventana observada de un repositorio arranca en `max(repositorio.listo_en, curso.ingesta_actividad_desde)` (§10.2.6) hasta ahora, y si esa ventana observada es más corta que el umbral, el repositorio **no se cuenta entre los inactivos en ninguna parte** —ni en el tablero, ni en Pendientes, ni en la sección 3 del informe diario del capítulo 11— y su tarjeta muestra el texto fijo **«Sin dato suficiente: se observan N días de los M que exige el umbral»**. **R2.6.2** pide informar, no alarmar, y un repositorio de tres días de antigüedad no puede llevar cuatro días sin actividad.

**Estudiante sin participación (R2.5.4).** El predicado base —cero commits contables atribuidos a ese estudiante en la ventana de la entrega vigente (§10.6.3)— **no es configurable**: no depende de `curso.umbral_dias_sin_actividad` ni de ningún otro valor editable, porque la acción docente que dispara no admite grados. Sobre ese cero, esta sección fija el **catálogo cerrado de exactamente tres causas**, evaluadas en este orden —gana la primera que casa— y **cada una con su propio predicado y su propia acción docente** (P4: la aplicación no acusa sin decir por qué):

| # | Causa | Predicado | Problema | Acción del docente |
|---|---|---|---|---|
| 1 | `SIN_ACCESO` | `acceso_repositorio.estado` del estudiante **no** está en `{ACEPTADO, ACCESO_DIRECTO}` | De **acceso**: no ha aceptado su invitación de colaborador | Reenviar la invitación o avisar por Canvas |
| 2 | `SIN_ATRIBUIR` | El acceso está aceptado, el estudiante tiene cero commits atribuidos **y** existen commits sin atribuir en ese repositorio dentro de la ventana | De **configuración de su Git**: puede haber trabajado con un correo que la cascada de §10.3.1 no resuelve | Pedirle que configure el correo de su cuenta de GitHub, o asociar la identidad desde §10.3.4 |
| 3 | `SIN_COMMITS` | El acceso está aceptado, el estudiante tiene cero commits atribuidos y **no** hay commits sin atribuir pendientes en el repositorio | De **trabajo**: no ha hecho nada, y no hay una explicación técnica alternativa | Contactar al estudiante |

Esta precedencia es la aplicación literal de P4: mientras el repositorio tenga commits sin atribuir, **ningún** estudiante de ese repositorio se marca con la causa más grave (`SIN_COMMITS`) hasta que la atribución se resuelva, porque uno de esos commits podría ser suyo. Las tres causas son **excluyentes** —un estudiante lleva exactamente una— y se muestran siempre con su nombre y su acción, nunca como un cero desnudo (§10.1.3 P4).

**Invitación sin aceptar en Pendientes.** El umbral de 48 horas desde la invitación que hace aparecer una invitación pendiente en Pendientes tampoco es configurable; es el mismo umbral que ya fija el capítulo 8 para esa pantalla, y esta sección lo cita sin redefinirlo.

### 10.5.4 Día del curso

**«Día del curso»** es la fecha de calendario en la zona horaria del curso, `curso.zona_horaria` (§10.1.2), y es la unidad de `metrica_repositorio_dia.dia`, del histograma de §10.8.4 y de la agrupación del timeline (§10.9.2). Se calcula con una función de **un solo argumento**:

```
dia = (commit.fecha_committer AT TIME ZONE 'UTC' AT TIME ZONE curso.zona_horaria)::date
```

La migración que crea la columna lleva ese comentario literal, para que nadie tenga que deducirlo leyendo este capítulo. **No contradice** la regla de que todo instante se almacena en UTC y ningún cálculo de negocio usa hora local: un *bucket* diario no es un instante que decida nada por sí mismo, es una agregación cuyo único consumidor es la presentación al equipo docente, y agregarla en UTC produciría, para un curso en Chile, un histograma que atribuye al día siguiente el trabajo de la noche anterior.

Si **`curso.zona_horaria` cambia**, `agregar_metricas` recalcula **todos** los `dia` del curso en el ciclo siguiente y lo deja escrito en `bitacora`: las métricas son recomputables por diseño (P3), así que el recálculo es correcto y barato.

**Lo que sigue en UTC:** los umbrales que son intervalos —«sin actividad en 7 días», «48 horas antes del cierre»— se evalúan como diferencias de instantes (`ahora_utc − último_commit > interval`), nunca como comparación de fechas de calendario. **Un intervalo no tiene zona; un día sí.** La interfaz etiqueta ambos con la fecha local equivalente (§10.1.2, formato de fecha ya fijado en otros capítulos de este documento).

### 10.5.5 Criterios de aceptación de §10.5

1. **CA-10.5-01.** Comprobar que `es_commit_contable` y `dia_del_curso` reciben exactamente un argumento cada una, y que existe una prueba de dominio que falla la construcción si alguna de las dos consulta `autor_es_bot`, `autor_es_docente` o cualquier columna ajena a su firma.
2. **CA-10.5-02.** Empujar un commit del bot de la propia aplicación a un repositorio sin actividad de estudiantes y comprobar que **no** cierra la incidencia `SIN_ACTIVIDAD` ni la de `SIN_PARTICIPACION` de ningún integrante.
3. **CA-10.5-03.** Crear un repositorio hace 3 días con el umbral por defecto de 7 y comprobar que **no** aparece como «sin actividad reciente» en ninguna pantalla, y que muestra el texto «sin dato suficiente» con el recuento de días observados.
4. **CA-10.5-04.** Con un repositorio a 48 horas de una fecha efectiva de cierre, comprobar que el umbral aplicado es 2 días y que la tarjeta correspondiente lo declara por escrito.
5. **CA-10.5-05.** Con un repositorio que tiene commits sin atribuir y un estudiante con cero commits atribuidos, comprobar que ese estudiante aparece con causa `SIN_ATRIBUIR` y no `SIN_COMMITS`, y que al resolver la identidad correspondiente la causa se recalcula en el ciclo siguiente.
6. **CA-10.5-06.** Cambiar `curso.zona_horaria` y comprobar que, tras el pase nocturno, el histograma de un repositorio con commits nocturnos desplaza sus barras al día correcto en la nueva zona.

---

## 10.6 Entregas: estado agregado, ventanas y línea de entregas (R2.5.6, R2.5.7)

### 10.6.1 Estado agregado de una entrega

El «estado» que **R2.5.6** exige mostrar para cada entrega es una **enumeración cerrada de nueve valores, derivada y no persistida**, evaluada de arriba abajo —el primero que se cumple es el estado—, calculada en `backend/app/dominio/estado_entrega.py` y precomputada en `resumen_tarea` (§10.4.2) con `calculado_en` visible. Es **fuente única** de la línea de entregas de este capítulo (§10.6.4), de la sección correspondiente del informe diario del capítulo 11 y de la pantalla de la entrega del capítulo 9.

| # | Estado | Etiqueta | Condición |
|---|---|---|---|
| 1 | `EXCLUIDA` | «Excluida por el equipo docente» | `entrega.estado_validacion = 'EXCLUIDA'` (capítulo 9) |
| 2 | `ELIMINADA_EN_CANVAS` | «Eliminada en Canvas» | `entrega.estado_validacion = 'ELIMINADA_EN_CANVAS'` (capítulo 9) |
| 3 | `NO_PUBLICADA` | «No publicada en Canvas» | `entrega.publicada = false` (capítulo 9) |
| 4 | `VINCULADA_TRAS_EL_CIERRE` | «Versiones no registradas: la fecha ya había pasado al vincular» | `entrega.estado_validacion = 'VINCULADA_TRAS_EL_CIERRE'` (capítulo 9) |
| 5 | `SIN_FECHA` | «Sin fecha de cierre» | Ninguna `fecha_efectiva` vigente con `due_at_utc` no nulo para ningún sujeto |
| 6 | `ABIERTA` | «Abierta · cierra en X» | Ninguna fecha efectiva ha vencido todavía |
| 7 | `EN_CIERRE` | «Cerrando · N de M sujetos ya cerrados» | Alguna fecha efectiva venció y alguna sigue pendiente (secciones o excepciones con fechas distintas, capítulo 9) |
| 8 | `CERRADA_CAPTURANDO` | «Cerrada · registrando versiones (M de N)» | Todas vencieron y algún sujeto con fecha efectiva no tiene aún versión vigente en estado terminal |
| 9 | `CERRADA_REGISTRADA` | «Cerrada · N versiones registradas» | Todo sujeto con fecha efectiva tiene versión vigente en uno de los seis estados terminales de `version_entrega` (capítulo 9) |

**Por qué esa precedencia:** una decisión humana deliberada (1) manda sobre un hecho de Canvas (2), y un assignment que ya no existe (2) manda sobre uno simplemente despublicado (3), porque un assignment eliminado no puede estar publicado. Esta sección **no redefine** `entrega.estado_validacion` ni los seis estados terminales de `version_entrega`: los consume tal como el capítulo 9 los fija y sólo los combina.

**El estado agregado nunca aparece solo.** Junto a él se muestran siempre los contadores por sujeto: «N sujetos · M versiones registradas · K sin commits · J en revisión · P sin repositorio al cierre · Q con error · R sin fecha», más «N fechas distintas» cuando las hay (§10.6.4). Un estado sin sus contadores escondería que la mitad del curso quedó sin capturar, que es justo lo que el equipo docente necesita ver.

### 10.6.2 El periodo de una entrega y la entrega anterior por sujeto

El periodo de actividad de una entrega **se calcula por sujeto, con la fecha efectiva propia de cada sujeto, nunca con la fecha base de la tarea** (R2.4.2, R2.4.3): dos sujetos de la misma entrega pueden tener fechas efectivas distintas, y una ventana común atribuiría a uno el trabajo del plazo extra de otro, o le quitaría a otro los días de su propia extensión.

**La entrega anterior de la entrega `E` para el sujeto `S`** es la entrega de la misma tarea con el **mayor `orden` estrictamente menor que `E.orden`** que además tenga `fecha_efectiva` vigente y no nula para `S`. Si no existe ninguna, no hay entrega anterior. De ahí sale el inicio de la ventana:

| Caso | Inicio de la ventana |
|---|---|
| Existe entrega anterior para `S` | El `due_at_utc` de **su** fecha efectiva, exclusivo |
| No existe entrega anterior para `S` | `repositorio.creado_en` de ese sujeto |
| `S` entró en alcance después de la entrega anterior y su repositorio se creó más tarde | El más tardío de los dos: `max(due_at_anterior, repositorio.creado_en)` — no se le atribuye actividad de un período en que no tenía repositorio |
| `E` no tiene fecha efectiva para `S` | **No hay ventana**: el selector muestra «esta entrega no aplica a este sujeto» y no se calcula participación |

**Recorte adicional en tareas grupales.** Dentro de un repositorio de grupo, la medición de un integrante concreto recorta además la ventana a su intervalo de pertenencia, guardado en `pertenencia_grupo.activa_desde` / `pertenencia_grupo.activa_hasta` (capítulo 7):

```
inicio = max(due_at_entrega_anterior_del_sujeto, repositorio.creado_en, activa_desde)
fin    = min(due_at_de_esta_entrega_del_sujeto, coalesce(activa_hasta, 'infinity'))
```

Es la misma regla de «no se atribuye actividad de un período en que no correspondía», aplicada a la pertenencia en vez de a la existencia del repositorio. Un integrante que entró a mitad de un tramo no aparece como «sin participación» por el trabajo que el grupo hizo antes de que llegara (§10.5.3): su ventana empieza el día de su entrada, con la etiqueta «en el grupo desde dd-MM».

### 10.6.3 Ventana de una entrega

**«Ventana de una entrega»** es, por definición cerrada de este capítulo (§10.1.2), el intervalo **`(inicio, cierre]`**, calculado por sujeto según §10.6.2, donde `cierre` es el `due_at_utc` de la fecha efectiva de **esta** entrega para ese sujeto. La ventana es **abierta por la izquierda y cerrada por la derecha**: un commit cuya `fecha_committer` coincide exactamente con un cierre pertenece a la entrega que cierra, y no a la siguiente. Es la misma inclusividad que el capítulo 9 fija por escrito para el commit de cierre, y mantener las dos iguales es lo que impide que este capítulo y la versión capturada discrepen en el segundo exacto.

Esta ventana, y sólo ella, es la que usan la serie temporal del tablero (§10.7.3), el selector de periodo (§10.7.4), la comparación entre integrantes (§10.8.1) y la franja de participación del timeline (§10.9.2): **una sola función de dominio**, ninguna copia (P2).

### 10.6.4 Línea de entregas y representación de fechas heterogéneas

El bloque 1 del tablero (§10.7.1) es la **línea de entregas**: una fila por entrega, ordenada por su `orden`, con columnas cerradas — `#`, nombre, tipo (Parcial/Final), fecha de cierre base con la zona escrita, «N fechas distintas» con desglose al pulsar, cuenta atrás o «cerrada hace X», el **estado agregado** de §10.6.1 y los contadores «M de N versiones registradas · K sin commits · J en revisión». Es la respuesta literal a «mostrar claramente las distintas entregas asociadas a una tarea, sus fechas y su estado» (**R2.5.6**).

**Cuando hay varias fechas efectivas** para la misma entrega —por sección, por grupo o por excepción individual (capítulo 9)—, la fila de la línea de entregas y el gráfico de §10.7.3 las representan con esta regla cerrada:

| Número de fechas efectivas distintas | Cómo se muestra |
|---|---|
| 1 | Una sola fecha, con su zona |
| 2 a 5 | Cada fecha, etiquetada con su `origen`: `BASE`, `SECCION: <nombre>`, `GRUPO: <nombre>`, `ADHOC: N estudiantes` |
| 6 o más | «N fechas distintas», de `min(due_at)` a `max(due_at)`, con el desglose completo al pulsar |

El selector de periodo lo declara explícitamente: «periodo de la entrega N **para cada sujeto**» cuando hay fechas distintas. **Se descarta expresamente colapsar todas las fechas en una sola** —ni la base ni el máximo de los `override`— porque produciría, según el caso, ignorar las excepciones de R2.4.2/R2.4.3 o contar como dentro de plazo el trabajo de un sujeto que ya había cerrado.

### 10.6.5 Commits posteriores al cierre

Un commit posterior al cierre de la entrega `k` y anterior o igual al cierre de la entrega `k+1` **pertenece a la ventana de la entrega `k+1`**, sin excepción (§10.6.3): no queda huérfano de ventana, no se cuenta dos veces y no se reparte. Sobre esa asignación, este capítulo añade dos piezas de contexto que no alteran ningún recuento:

1. **Etiqueta derivada**, calculada en la consulta y nunca persistida: `posterior_al_cierre_de ∈ {ninguno, entrega_id}`, la mayor entrega cuya fecha efectiva para ese sujeto es anterior a la `fecha_committer` del commit. El timeline (§10.9.1) la muestra como «posterior al cierre de la entrega N».
2. **Indicador por repositorio**, en la fila del tablero (§10.7.1), en la ficha del sujeto y en la cabecera de la pantalla de corrección del capítulo 12: **«N commits no incluidos en la versión registrada»**, definido como los commits contables de la rama por defecto con `fecha_committer` posterior a `version_entrega.fecha_corte_utc` de la versión **vigente** de esa `(entrega, sujeto)` (capítulo 9). Hace visible, sin ambigüedad, que el corrector no está revisando el estado actual del repositorio, que es exactamente lo que **R2.4.7** protege.

**Después de la última entrega**, los commits posteriores al cierre de la entrega `FINAL` **no pertenecen a ninguna ventana** y **no suman en ninguna `participacion_entrega`**. El selector de periodo (§10.7.4) ofrece la opción «Después del cierre final», que dibuja esos commits sobre fondo sombreado con la etiqueta «actividad posterior al cierre»: **se ven, no se suman**.

### 10.6.6 Cambios de fecha: recómputo y aviso

Cuando la sincronización de fechas del capítulo 9 detecta que una fecha efectiva cambió, este capítulo **recalcula automáticamente y avisa**, sin excepción:

1. **Recálculo inmediato**, en la misma transacción que supersede la `fecha_efectiva`: se encola `agregar_metricas` para los repositorios afectados. **Ninguna ventana de este capítulo se persiste** (§10.6.3), así que el periodo, el gráfico, las líneas de cierre y `participacion_entrega` quedan correctos en el ciclo siguiente sin ninguna migración.
2. **Aviso visible durante 72 horas**: una banda en la pantalla de la tarea —«La fecha de cierre de la entrega N cambió el DD-MM a las HH:MM: de X a Y, para N sujetos. Los periodos y las métricas se recalcularon»—, con la fila de esa entrega marcada como cambiada recientemente y la línea de cierre anterior dibujada en trazo discontinuo junto a la nueva mientras dure el aviso. **Los números de este capítulo nunca cambian solos sin explicación en pantalla.**
3. **Versiones ya capturadas**: no se recalculan hacia atrás salvo lo que manda el capítulo 9; cuando ese capítulo supersede una versión, la línea de entregas muestra **ambas**, con su motivo, porque lo registrado se conserva (**R2.4.7**).

### 10.6.7 Entregas degradadas: sin fecha, no publicada, eliminada o vinculada tras el cierre

Los cuatro estados degradados del catálogo de §10.6.1 (`SIN_FECHA`, `NO_PUBLICADA`, `ELIMINADA_EN_CANVAS`, `VINCULADA_TRAS_EL_CIERRE`) **nunca ocultan la entrega**: ocultarla haría desaparecer sin explicación las versiones ya capturadas y las métricas de su periodo. En cada uno:

- **`SIN_FECHA`**: la ventana de esa entrega es `(inicio, ahora]`, abierta por arriba, y el selector la nombra «periodo abierto: sin fecha de cierre»; el gráfico no dibuja línea de cierre; las alertas por proximidad de fecha no se disparan.
- **`NO_PUBLICADA`**: es un borrador legítimo del profesor (capítulo 9); se conservan fechas, sujetos, repositorios y versiones, y se suspenden las alertas por fecha y las comunicaciones de esa entrega.
- **`ELIMINADA_EN_CANVAS`** y **`VINCULADA_TRAS_EL_CIERRE`**: se conserva la última fecha conocida, rotulada como tal; se desactivan alertas por fecha y programación de capturas nuevas; **las versiones ya capturadas siguen accesibles**, porque son evidencia (P6) y el capítulo 9 las sitúa en el espejo, no en Canvas.

**Esto no se confunde con una credencial de Canvas inválida** (capítulo 5): cuando la credencial falla, las fechas ya persistidas siguen sirviendo y ninguna entrega pasa a `ELIMINADA_EN_CANVAS` por esa causa; el curso muestra en su lugar la banda de reconexión pendiente que ese capítulo define.

### 10.6.8 Criterios de aceptación de §10.6

1. **CA-10.6-01.** Recorrer los nueve casos de la tabla de §10.6.1, uno por uno, y comprobar que el estado agregado que produce `estado_entrega.py` coincide con el esperado, incluido el caso mixto de dos secciones con fechas distintas donde una ya cerró y otra no (`EN_CIERRE`).
2. **CA-10.6-02.** Con dos sujetos de la misma entrega con fechas efectivas distintas, comprobar que la serie temporal y `participacion_entrega` usan la ventana **de cada sujeto** y no una fecha común, y que la línea de entregas muestra «2 fechas distintas» con el desglose por `origen`.
3. **CA-10.6-03.** Un commit cuya `fecha_committer` coincide exactamente con el segundo del cierre de la entrega 1 se cuenta en la ventana de la entrega 1, no en la de la entrega 2.
4. **CA-10.6-04.** Un integrante que se incorpora a un grupo a mitad del periodo de una entrega no aparece con causa `SIN_COMMITS` por el trabajo anterior a su ingreso; su ventana arranca en `pertenencia_grupo.activa_desde`.
5. **CA-10.6-05.** Un commit posterior al cierre de la entrega 1 y anterior al cierre de la entrega 2 aparece en la ventana de la entrega 2 con la etiqueta «posterior al cierre de la entrega 1», y el indicador «commits no incluidos en la versión registrada» de la entrega 1 lo cuenta.
6. **CA-10.6-06.** Cambiar en Canvas la fecha de cierre de una entrega ya reflejada en el tablero y comprobar que, tras el ciclo de sincronización del capítulo 9, la línea de entregas, el gráfico y `participacion_entrega` quedan correctos y que aparece la banda de aviso con la fecha anterior y la nueva.
7. **CA-10.6-07.** Una entrega despublicada en Canvas aparece en la línea de entregas con estado `NO_PUBLICADA`, conserva sus versiones y no dispara ninguna alerta por fecha.

---

## 10.7 El tablero de la tarea (R2.5.1, R2.5.2, R2.5.5)

### 10.7.1 Contenido cerrado, una sola pantalla

El **tablero de la tarea** es la respuesta a **R2.5.1** («mostrar un dashboard general para cada tarea») y es la pantalla que se abre por defecto al entrar a una tarea, en `/cursos/{curso_id}/tareas/{tarea_id}`, con las demás vistas de la tarea como pestañas bajo ella. Es **una sola página de desplazamiento vertical, no una serie de pestañas**: repartir su contenido en pestañas escondería **R2.5.5** y **R2.5.6** detrás de un clic, que es precisamente lo que el enunciado no admite para información que debe estar disponible «de forma inmediata».

**Contenido fijo, de arriba abajo:**

| Bloque | Contenido | Requisito |
|---|---|---|
| Cabecera | Nombre de la tarea, modalidad (`INDIVIDUAL`/`GRUPAL`), estado de la tarea, línea de procedencia (§10.7.5), botón «Actualizar ahora» (§10.7.8) y el selector de periodo que gobierna a la vez los bloques 4 y 5 | — |
| 1 — Línea de entregas | §10.6.4 | **R2.5.6** |
| 2 — Estado de los repositorios | §10.7.2 | **R2.5.5** |
| 3 — Tarjetas de atención | Cuatro tarjetas: «sin actividad reciente» (§10.5.3), «sin participación» desglosada en las tres causas de §10.5.3, «invitaciones sin aceptar» (capítulo 8), «incidencias bloqueantes abiertas» | **R2.5.3**, **R2.5.4** |
| 4 — Actividad en el tiempo | §10.7.3 | **R2.5.2**, **R2.5.7** |
| 5 — Detalle, comparación y métricas adicionales | Tabla por repositorio (§10.7.6) más la comparación entre integrantes y las métricas adicionales del capítulo §10.8 | **R2.5.8**, **R2.5.9** |

**No hay una fila de tarjetas KPI separada.** Los números del tablero **son** los de la barra del bloque 2 y los de las cuatro tarjetas del bloque 3; duplicarlos en una fila aparte produciría dos números para el mismo hecho, que es justo lo que P2 impide.

### 10.7.2 Estado de creación y configuración de repositorios (R2.5.5)

Este bloque **consume, sin redefinirlo**, el estado de la máquina de estados del repositorio que fija el capítulo 8: una barra apilada agrupa los estados en seis segmentos —`Listos` (`OPERATIVO`), `Funcionando, incompleto` (`DEGRADADO`, con su motivo desglosado), `Falta información` (`ESPERANDO_INFORMACION`, con su motivo), `En curso` (los estados intermedios de creación), `Esperando` (los estados transitorios de error o de límite) y `Requiere acción` (`ERROR_PERMANENTE`)—, y fuera de la barra, en línea aparte, `Fuera de alcance` y `Archivado` e `Inaccesible`, cada uno con su recuento propio.

**`DEGRADADO` nunca se suma a la columna de problemas** (capítulo 8): tiene su propia columna ámbar, porque un repositorio `DEGRADADO` funciona y sólo le falta gente por entrar. Junto a la barra, el recuento de sujetos activos y desactivados del curso, con su motivo. Un enlace «ver tabla completa» lleva a la vista de estado de repositorios del capítulo 8; **es el mismo componente de datos con dos presentaciones**, no dos consultas distintas, para que este resumen y esa tabla nunca diverjan.

**Universo de las métricas de actividad.** Los bloques 3, 4 y 5 de este tablero sólo consideran repositorios con `github_repo_id` no nulo — es decir, los que ya existen en GitHub. Un sujeto en `ESPERANDO_INFORMACION` o en cualquier estado previo a la existencia del repositorio **no entra en el numerador ni en el denominador** de «sin actividad reciente» ni de «sin participación»: aparece entero en este bloque 2, con su motivo, y en ningún otro sitio como un cero. Cada tarjeta del bloque 3 escribe su denominador explícito —«sin actividad reciente: 4 de 182 repositorios creados»— y **nunca se muestra un porcentaje sin su denominador al lado**.

### 10.7.3 Actividad en el tiempo (R2.5.2)

El bloque 4 combina, con jerarquía explícita, tres representaciones sobre `metrica_repositorio_dia`, ninguna opcional:

1. **Por defecto, serie agregada de la tarea**: barras de commits contables por día del curso (§10.5.4), con las líneas o la banda de cierre de cada entrega superpuestas (§10.6.4). Es la única representación que sigue siendo legible con cientos de repositorios porque no depende de su número.
2. **Selección de hasta 8 repositorios** para superponer como líneas finas sobre la agregada, elegidos desde el propio gráfico o desde la tabla del bloque 5. Por encima de 8 el selector lo dice en vez de aceptar y degradar la lectura.
3. **Sparkline por fila** en la tabla del bloque 5: treinta días, sin ejes, con el máximo y la fecha al pasar el cursor — sale directamente de `metrica_repositorio_dia` y es lo que hace visible «a lo largo del tiempo» para todos los repositorios a la vez, sin necesidad de abrir el gráfico agregado.

Cada punto de la serie es **un día, nunca un commit**: el contrato de la API interna nunca crece con el volumen de actividad, sólo con el rango de fechas.

### 10.7.4 Rango temporal por defecto y selector de periodo (R2.5.7)

El rango por defecto del bloque 4 es el **periodo de la entrega vigente** (§10.6.3) — la de menor `orden` cuya fecha efectiva máxima aún no ha vencido, o la `FINAL` si todas vencieron —, con 7 días de margen visual a cada lado para que las líneas de cierre no queden pegadas al borde. Cuando la tarea no tiene ninguna entrega vinculada, no se dibuja un gráfico plano: se muestra el estado vacío correspondiente (§10.7.7).

El selector de periodo —compartido por los bloques 4 y 5, y por la comparación entre integrantes (§10.8.1)— ofrece un conjunto cerrado: una opción por entrega («hasta la entrega 1», «entre la 1 y la 2», …), «Después del cierre final» cuando corresponde (§10.6.5), «Últimos 30 días» y «Todo». **Es la aplicación literal de R2.5.7**: «permitir consultar la actividad de los repositorios considerando los períodos correspondientes a las distintas entregas» se cumple mostrando, ya en la carga inicial, exactamente uno de esos períodos, no dejándolo como una opción escondida.

### 10.7.5 Rendimiento, procedencia y frescura

**Presupuesto de rendimiento**, heredado de los principios de §10.1: la respuesta del servidor para el tablero completo se mide en **p95 por debajo de 400 ms con 200 sujetos**, apoyada en `resumen_tarea` (§10.4.2) y en los índices declarados en §10.2 y §10.3. El criterio que puede fallar la construcción **no es el tiempo, es el cero de llamadas externas** (§10.1.4): un tablero lento con datos precomputados sigue cumpliendo R2.5; uno rápido que llama a GitHub o a Canvas, no.

**Línea de procedencia**, visible bajo la cabecera del tablero y del timeline (§10.9): «Datos del espejo · última ingesta hace X · última reconciliación HH:MM · 0 llamadas externas en esta vista · render Y ms», con explicación al pasar el cursor. Es el artefacto que hace comprobable, y no sólo declarado, el principio P1: junto a las cabeceras `X-Llamadas-Externas` de §10.1.4 y a la prueba de CI con clientes que lanzan excepción, cierra en tres capas la misma garantía.

### 10.7.6 Filtros, orden, agrupación y persistencia

La tabla del bloque 5 tiene, combinables: filtro por sección, por estado del repositorio (los seis grupos de §10.7.2), por motivo, un interruptor «solo con alertas» (incidencia abierta, sin actividad, o algún estudiante sin participación) y el selector de periodo de §10.7.4. Orden por defecto: **«días desde el último commit», descendente**, con desempate por nombre del sujeto; agrupación opcional por sección o por estado.

Los filtros aplicados y el periodo elegido **viajan en la URL**, de modo que un enlace compartido con otro miembro del equipo docente muestra exactamente lo mismo, y además se recuerdan por usuario y por tarea. La tabla se pagina por el servidor: nunca se envían todas las filas del curso al navegador.

### 10.7.7 Estados vacíos: «sin datos todavía» frente a «cero actividad»

Este capítulo distingue siempre, con textos y consecuencias distintas, dos situaciones que a simple vista parecen iguales:

| Situación | Estado | Consecuencia |
|---|---|---|
| El repositorio nunca tuvo una lectura de actividad con éxito | **Sin datos todavía** | No entra en ninguna alerta de §10.5.3; se muestra «primera lectura prevista a las HH:MM» |
| Hubo lectura con éxito y cero commits contables en el periodo | **0 commits** | Puede entrar en las alertas de §10.5.3 si corresponde |

**Mientras un repositorio esté en «sin datos todavía», no se abre ninguna incidencia `SIN_ACTIVIDAD` ni `SIN_PARTICIPACION`** (§10.4.3): es la aplicación de P4 al caso de la ingesta incompleta, no acusar por error a nadie cuyos datos aún no se han recopilado. La misma distinción gobierna la tarea sin entregas vinculadas, la tarea sin sujetos, y el gráfico del bloque 4 sin ningún punto: en cada caso se muestra el texto correspondiente, nunca un eje vacío o un cero mudo.

### 10.7.8 Actualizar ahora y degradación de la ingesta

El botón **«Actualizar ahora»** encola una reconciliación (§10.2) para los repositorios de la tarea; responde de inmediato y **nunca llama a GitHub dentro de la petición del usuario** (P1). Tiene cooldown —2 minutos por tarea y usuario, 5 minutos por tarea— y se deshabilita con el motivo escrito cuando el presupuesto de la API de GitHub está por debajo del freno de §10.2.9, sin pintarse como error del equipo (§10.1.3 P1, Ley de estado transitorio ya fijada en el vocabulario del capítulo 6).

Si la reconciliación de un curso falla tres ciclos consecutivos, o la última con éxito supera los 60 minutos, aparece una **banda ámbar persistente**: «Los datos de actividad pueden estar desactualizados: última lectura correcta a las HH:MM». Es lo único que distingue «hace 40 minutos que no hay commits nuevos» de «hace 40 minutos que no leemos», y sin ella un fallo de ingesta se presentaría como calma en el curso, que es el peor desenlace posible para un tablero de seguimiento.

### 10.7.9 Criterios de aceptación de §10.7

1. **CA-10.7-01.** Abrir el tablero de una tarea con 200 sujetos y comprobar, con el inspector de red, que la respuesta llega en menos de 400 ms en el percentil 95 y con la cabecera `X-Llamadas-Externas: 0`.
2. **CA-10.7-02.** Comprobar que la barra del bloque 2 nunca suma `DEGRADADO` a `Requiere acción`, y que un sujeto sin repositorio aún creado no aparece con un cero en el bloque 3 ni en el bloque 5, sino en el bloque 2 con su motivo.
3. **CA-10.7-03.** Entrar a una tarea recién creada, sin entregas vinculadas y sin sujetos, y comprobar que cada bloque muestra su estado vacío específico con su llamada a la acción, y que ningún gráfico se dibuja plano en cero.
4. **CA-10.7-04.** Pulsar «Actualizar ahora» dos veces seguidas dentro del cooldown y comprobar que la segunda no encola un segundo trabajo y que la interfaz explica cuándo terminará la actualización en curso.
5. **CA-10.7-05.** Detener la reconciliación de un curso durante más de 60 minutos y comprobar que aparece la banda de datos posiblemente desactualizados con la hora de la última lectura correcta.
6. **CA-10.7-06.** Filtrar la tabla del bloque 5 por sección y por «solo con alertas», copiar la URL, abrirla en otra sesión con el mismo permiso, y comprobar que muestra exactamente el mismo filtro y el mismo periodo.

---

## 10.8 Comparación de integrantes y métricas adicionales (R2.5.8, R2.5.9)

### 10.8.1 Columnas y alcance temporal de la comparación

La comparación entre integrantes de un mismo grupo (**R2.5.8**) tiene **cuatro columnas por integrante**, en este orden: **commits** (contables, §10.5.1), **días activos** (días del curso con al menos un commit contable atribuido), **líneas añadidas** y **líneas eliminadas**. Las cuatro salen de `participacion_entrega` (§10.4.2). **Las líneas se muestran como contexto y nunca gobiernan un cálculo, un orden por defecto ni una alerta**: el índice de desequilibrio de §10.8.2, el orden de la tabla y toda tarjeta de atención se calculan sólo con commits contables y días activos, porque las líneas de código son trivialmente inflables con archivos generados y nunca se usan como medida de aporte (§10.3.5).

El alcance temporal es **seleccionable con el mismo selector de §10.7.4**, calculado por sujeto (§10.6.3). El valor por defecto es el periodo de la entrega abierta más próxima; si no hay ninguna abierta, el de la última entrega vencida.

Bajo la tabla se muestra siempre una fila no atribuible: **«commits sin atribuir en este repositorio: N»**, derivada de `autoria_commit` con `estudiante_id` nulo y con el recuento denormalizado en `participacion_entrega.commits_sin_atribuir_repo` (§10.3.2, §10.4.2). Esa fila **no se reparte** entre integrantes, y su presencia degrada visualmente la comparación con el texto «hay actividad sin autor reconocido; la comparación puede estar incompleta» (P4).

**Consecuencia declarada de la coautoría** (§10.3.3): la suma de commits por integrante puede superar el total de commits del repositorio, y la pantalla lo dice literalmente junto al gráfico, con el desglose de `commits_coautorados`.

### 10.8.2 Índice de desequilibrio

Junto a las barras por integrante, una tarjeta única de grupo muestra el **índice de desequilibrio**: `commits_contables_del_integrante_que_más_aporta / commits_contables_atribuidos_del_grupo` en el periodo seleccionado, en porcentaje entero. Los commits sin atribuir **no entran ni en numerador ni en denominador**.

La señal se enciende cuando se cumplen **las tres** condiciones: el grupo tiene al menos 2 integrantes con acceso aceptado, al menos **10 commits contables atribuidos** en el periodo (muestra mínima, para no alarmar sobre un grupo con tres commits en total), y el índice supera el **umbral configurable** — `curso.umbral_desbalance_pct` (`smallint`, `CHECK BETWEEN 50 AND 95`, por defecto **70**, editable con `curso.administrar`, con anulación opcional por tarea). Se enciende también, sin depender del índice, cuando **un integrante tiene cero commits contables y otro tiene tres o más** en el mismo periodo.

**Es señal, no veredicto**: color ámbar, nunca rojo; etiqueta «reparto concentrado»; texto fijo bajo la tarjeta: «esto no evalúa la calidad ni la justicia del reparto, y no cuenta líneas de código; es una señal para mirar el timeline del grupo». **No se incorpora al informe diario del capítulo 11 ni al catálogo de incidencias**: el caso extremo de un integrante en cero ya llega a ese informe por la vía de `SIN_PARTICIPACION` (§10.4.3), de modo que la situación accionable no se pierde por dejar fuera el índice.

### 10.8.3 Tareas individuales: posición frente al curso

En tareas `INDIVIDUAL` (capítulo 7) el bloque de comparación no se oculta: se sustituye por **«Posición frente al curso»**, que responde a la misma pregunta docente —«¿quién va descolgado?»— con la unidad que tiene sentido cuando no hay grupo. Muestra, para commits contables y días activos, una distribución del curso (cuartiles) con dos líneas de referencia: la **mediana de la sección** del estudiante como referencia principal —porque las secciones pueden tener fechas de cierre distintas (R2.4.2) y mezclar poblaciones con calendarios distintos compara mal— y la mediana del curso como referencia secundaria. **Nunca se muestran posiciones numeradas del 1 al N ni la palabra «ranking»**: se ordena por la columna que el docente elija, y el orden por defecto es ascendente en commits, porque lo que se busca es el extremo bajo.

Toda distribución declara sobre cuántos sujetos se calcula y excluye del denominador a los sujetos desactivados (§10.10.2) y a los que no tienen fecha efectiva para la entrega seleccionada; los excluidos se listan aparte con su motivo.

### 10.8.4 Las cinco métricas adicionales de R2.5.9

**R2.5.9** —«incorporar otras métricas o visualizaciones que cada grupo considere útiles»— se cierra con **exactamente cinco métricas**, cada una con definición operativa y criterio de aceptación, decisión de este capítulo:

| # | Métrica | Definición operativa | Alimenta |
|---|---|---|---|
| 1 | Distribución del trabajo en el tiempo | Histograma de commits contables por día del curso (§10.5.4) en los 14 días previos al cierre de la entrega seleccionada | **R2.5.2** |
| 2 | Reparto dentro del grupo | El índice de desequilibrio de §10.8.2 | **R2.5.8** |
| 3 | Racha de días sin actividad | Días del curso completos transcurridos desde el último commit contable del repositorio; «sin actividad desde su creación» si nunca tuvo ninguno | **R2.5.3** |
| 4 | Progreso frente al cierre | Porcentaje de sujetos con al menos un commit contable en las 48 horas previas a **su propia** fecha efectiva de cierre, con cuenta atrás a la más próxima | **R2.5.6** |
| 5 | Días activos distintos por integrante | Número de días del curso con al menos un commit contable atribuido a ese estudiante | La cuarta columna de §10.8.1 |

**Ninguna otra métrica entra en el alcance comprometido de este capítulo.** El enlace de comparación entre las versiones de dos entregas consecutivas que el corrector usa es navegación de corrección del capítulo 12, no una métrica de R2.5.9, y no se cuenta dos veces. Cada métrica muestra su definición operativa al pasar el cursor y comparte, con el tablero, el timeline y el informe del capítulo 11, la **misma función de dominio** que la produce (P2).

### 10.8.5 Criterios de aceptación de §10.8

1. **CA-10.8-01.** Comprobar que ni el índice de desequilibrio ni el orden por defecto de la comparación cambian cuando se desactiva el enriquecimiento de líneas (§10.3.5): ninguno de los dos depende de ellas.
2. **CA-10.8-02.** Un grupo con 8 y 2 commits contables atribuidos muestra un índice de desequilibrio del 80 %; un grupo con cero commits atribuidos muestra «no calculable», nunca 0 % ni 100 %.
3. **CA-10.8-03.** Un grupo con menos de 10 commits contables atribuidos en el periodo no enciende la señal de reparto concentrado aunque su índice supere el umbral, salvo que un integrante tenga cero y otro tenga tres o más.
4. **CA-10.8-04.** En una tarea `INDIVIDUAL`, comprobar que el bloque 5 muestra «Posición frente al curso» con la mediana de sección y la mediana del curso, y que en ningún punto aparece un número de posición ni la palabra «ranking».
5. **CA-10.8-05.** Comprobar que las cinco métricas de §10.8.4, y sólo ellas, aparecen citadas en la memoria de entrega como cumplimiento de R2.5.9, cada una con su prueba automatizada.

---

## 10.9 Timeline del repositorio (R2.5.10)

### 10.9.1 Las cuatro capas

Cada repositorio tiene su propia vista de **timeline**, en un eje temporal único cuyos días son días del curso (§10.5.4), con **cuatro capas superpuestas**. Es la vista propia de **R2.5.10**, con su propio párrafo en el enunciado, y por eso tiene su propia sección completa en este capítulo.

1. **Commits.** Todos los commits del repositorio, agrupados por día, con autor atribuido, su regla de atribución (§10.3.1) y la etiqueta de por qué no cuenta cuando corresponde: «merge, no cuenta como aporte», «commit inicial de la plantilla», «huérfano: dejó de ser alcanzable el dd-MM» (§10.5.1, P5). El timeline es la historia; el recuento es la métrica, y la pantalla lo dice.
2. **Ciclo de vida del repositorio.** Creación, contenido listo, invitación emitida, invitación aceptada, cambio de rama por defecto, renombrado (capítulo 8); más **historia reescrita** (con la `ref`, los SHA `before`/`after` y el número de commits que pasaron a huérfanos, §10.2.3), **rama borrada** y **archivado o desarchivado** — los tres llegan por eventos a los que la GitHub App ya está suscrita (§10.2.2) y sin marca en el timeline dejarían tramos de la historia sin explicación.
3. **Marcas de entrega.** Una marca vertical por entrega con su fecha efectiva para ese sujeto (§10.6.3), el commit capturado resaltado y el tag si existe (capítulo 9). Cuando hubo recaptura por cambio de fecha, se muestran **las dos** marcas: la vigente destacada y la anterior en gris con su motivo, porque lo registrado se conserva (**R2.4.7**).
4. **Cambios de composición.** Entrada y salida de integrantes del grupo (`pertenencia_grupo.activa_desde`/`activa_hasta`, capítulo 7) y salida o vuelta de un sujeto al alcance de la tarea. Son hechos de Canvas, no acciones del equipo docente, y son la única explicación honesta de por qué la autoría de un tramo cambia a mitad de camino.

**Qué no entra, y por qué.** Los actos del equipo docente —comunicaciones enviadas, notas publicadas, cambios de permisos— no aparecen en el timeline: **R2.5.10** habla de la evolución del trabajo de los estudiantes, y esos actos ya tienen mejor trazabilidad en la bitácora y en la pantalla de corrección del capítulo 12. Mezclarlos convertiría el timeline en un registro de auditoría y taparía lo que el requisito pide ver.

Al pulsar un día se despliegan sus commits con mensaje, líneas añadidas y eliminadas (§10.3.5) y enlace a GitHub, condicionado a que el acceso docente esté concedido (capítulo 8): mientras no lo esté, el enlace no se pinta y en su lugar aparece el motivo, porque un enlace que devuelve un error no cumple «revisar fácilmente la evolución del trabajo».

### 10.9.2 Navegación, franja de participación y filtros

El timeline se navega **agrupado por día del curso**, con **paginación por ventana de entrega** —la página inicial es el periodo de la entrega abierta más próxima para ese sujeto (§10.6.3)— y **colapso de tramos de tres o más días consecutivos sin ningún commit contable** en una fila plegable «N días sin actividad (dd-MM → dd-MM)», que es la representación directa de la métrica 3 de §10.8.4. No hay desplazamiento infinito: rompería la navegación por teclado y haría imposible un enlace estable a un tramo concreto.

Sobre el eje, una **franja de participación por tramo entre entregas** —la terna `(entrega, repositorio, estudiante)`, que ya es la clave de `participacion_entrega` (§10.4.2), sin ningún agregado nuevo— muestra, por integrante, commits contables, días activos y una barra proporcional, más la fila «sin atribuir: N commits» cuando la haya. **Un integrante con cero commits contables en el tramo se marca con la causa de §10.5.3, nunca con un cero mudo**, y si entró o salió del grupo dentro del tramo lleva la etiqueta correspondiente con su ventana recortada (§10.6.2). La franja y la comparación del bloque 5 del tablero (§10.8.1) muestran siempre los mismos números, porque leen la misma tabla a través de la misma función de ventana (P2).

Tres filtros combinables: por integrante (incluida la opción «commits sin atribuir»), por periodo de entrega (el mismo selector de §10.7.4) y por rama, cuando la ingesta cubre más de la rama por defecto (§10.2.3). El estado —ventana, filtros, capas activas— viaja en la URL.

### 10.9.3 Cambios principales e hitos

**R2.5.10** exige identificar «cuándo se produjeron los principales cambios». Un commit se marca como **destacado**, con su motivo escrito al lado y nunca sólo con un color, si cumple al menos una de estas reglas, evaluadas en este orden:

| # | Regla | Motivo mostrado |
|---|---|---|
| a | Es el commit capturado como versión de una entrega (capítulo 9), vigente o superseded | «versión de la entrega N» |
| b | Es un commit de fusión (`es_merge = true`) | «integración de trabajo (merge)» |
| c | Es el primer commit contable de un integrante en el repositorio | «primera participación de *nombre*» |
| d | Es el primer commit contable tras una racha de inactividad igual o mayor al umbral de §10.5.3 | «vuelta al trabajo tras N días» |
| e | Marcado como **hito** por un miembro del equipo docente, con nota de hasta 140 caracteres | «hito: nota del docente» |

Los hitos manuales (regla e) los marca y desmarca quien tenga `tarea.administrar`; el desmarcado es lógico, no un borrado, y ambos quedan en bitácora. Las reglas a–d no dependen del enriquecimiento de líneas (§10.3.5), así que esta funcionalidad no se cae si ese enriquecimiento se degrada; una métrica de tamaño de commit **no** se usa como criterio de destacado, porque el tamaño no es una medida de calidad ni de aporte (§10.3.5, §10.8.1).

### 10.9.4 Criterios de aceptación de §10.9

1. **CA-10.9-01.** Abrir el timeline de un repositorio con una reescritura de historia y comprobar que la capa 1 muestra los commits huérfanos con su etiqueta y que la capa 2 muestra el evento «historia reescrita» con `before`, `after` y el número de commits afectados.
2. **CA-10.9-02.** Comprobar que un tramo de cuatro días sin commits contables aparece colapsado en una sola fila plegable, y que al expandirla no se pierde ningún commit.
3. **CA-10.9-03.** Comprobar que la franja de participación y la comparación del bloque 5 del tablero muestran, para el mismo repositorio y el mismo tramo, exactamente los mismos números de commits y de días activos.
4. **CA-10.9-04.** Un integrante con cero commits en un tramo aparece con su causa de §10.5.3 escrita junto al cero, nunca con el cero solo.
5. **CA-10.9-05.** Marcar un commit como hito con `tarea.administrar`, comprobar que aparece destacado con su nota, y que un usuario sin ese permiso no ve el control de marcado.
6. **CA-10.9-06.** Sin acceso docente concedido sobre un repositorio, comprobar que el enlace a GitHub de cada commit no se pinta y que en su lugar aparece el motivo con la acción para resolverlo.

---

## 10.10 Casos borde y gobierno de datos

### 10.10.1 Repositorio que deja de ser accesible en GitHub

Un repositorio borrado, transferido fuera de la organización o fuera del alcance de la instalación (capítulo 6) pasa a `INACCESIBLE` (capítulo 8) sin que este capítulo lo re-derive. Sus consecuencias para el seguimiento: se cuenta en columna propia en el bloque 2 del tablero (§10.7.2), nunca sumado a `OPERATIVO`; su historia —`commit`, `version_entrega`, `participacion_entrega`, `bitacora`— se conserva íntegra (P6) y sigue alimentando el tablero y el timeline; y el enlace a GitHub de cada commit se sustituye por el motivo, con la misma regla que gobierna la falta de acceso docente (§10.9.1). **Un repositorio cuya última reconciliación con éxito supera tres cadencias del techo garantizado (§10.2.1) se marca «datos posiblemente desactualizados»** en su fila y en su timeline, para que un silencio de la ingesta nunca se lea como calma en el curso.

### 10.10.2 Estudiante retirado del curso o que sale de un grupo

Un estudiante retirado del curso (capítulo 7) se muestra como «retirado», con toda su historia, y **queda fuera de las alertas de §10.5.3 y del denominador de la métrica 4 de §10.8.4** desde la fecha de su retiro: alertar sobre alguien que ya no está en el curso convertiría la lista de «sin participación» en ruido y el equipo docente dejaría de leerla. Sus commits **permanecen atribuidos al repositorio y a él**, se conservan en la comparación con la etiqueta «retirado el dd-MM» y en el timeline con la marca correspondiente en la capa 4 (§10.9.1).

**Salir de un grupo no es retirarse del curso.** El estudiante sigue activo; `pertenencia_grupo.activa_hasta` (capítulo 7) recorta su ventana de medición (§10.6.2) sin mover sus commits del repositorio donde se hicieron —moverlos entre repositorios destruiría la trazabilidad que exige **R2.4.7**—, y el cambio se marca en la capa 4 del timeline de los dos repositorios implicados. La recomputación de agregados es **inmediata**, en la misma transacción que registra el cambio de pertenencia, para que el equipo docente nunca vea, ni siquiera un ciclo, una alerta que ya se sabe falsa.

### 10.10.3 Repositorio base y repositorio de operaciones

Ninguna métrica, tarjeta, alerta ni serie de este capítulo incluye actividad del repositorio base ni del repositorio de operaciones del curso, tal como ya fija §10.2.7: contarlos falsearía todas las medias del curso, porque ninguno de los dos tiene sujeto.

### 10.10.4 Datos personales de terceros fuera de la ingesta

Las reglas de exposición de nombres y correos de §10.3.6 rigen **en todas las pantallas de este capítulo**, no sólo en la resolución de identidades: la comparación entre integrantes, la franja de participación del timeline y cualquier exportación (§10.10.5) muestran el correo ofuscado salvo revelado explícito con `mapeo.editar`, y el correo de Canvas del estudiante no se muestra junto a los commits en ninguna de estas pantallas.

### 10.10.5 Exportación y enlaces compartidos

El tablero, la comparación y el timeline se pueden **exportar a CSV** —una fila por repositorio del bloque 5, o una fila por estudiante de la comparación— y su URL con filtros aplicados es un **enlace permanente**, útil dentro del equipo docente porque exige sesión activa y `curso.ver` en ese curso: compartirla con alguien de fuera no le da acceso a nada. Todo CSV lleva, en líneas de comentario antes del encabezado, la definición de «commit contable» de §10.5.1 y la fecha de generación; toda exportación queda en bitácora con actor, filtros y número de filas, porque es una salida de datos personales. **No hay enlaces públicos ni tokens de solo lectura**, y no se exportan formatos que congelen una cifra que caduca al día siguiente como si fuera vigente (PDF).

### 10.10.6 Vista de seguimiento a nivel de curso

Además del tablero por tarea, existe una vista de curso en `/cursos/{curso_id}/seguimiento`, con `curso.ver`: una fila por tarea activa —con la barra de estado de repositorios comprimida, las tarjetas de atención y el enlace al tablero completo— y un bloque «hoy» que renderiza el informe diario vigente del capítulo 11. **No sustituye a ese informe**: el informe es un objeto congelado y enviado, con valor de trazabilidad; esta vista es en vivo sobre el espejo, con valor de estado actual. Ambos comparten la misma función de consolidación, para que nunca diverjan (P2).

### 10.10.7 Permisos de seguimiento

El tablero, el timeline y la vista de curso se rigen por **`curso.ver`**, que ya es implícito y no revocable para cualquier miembro activo del equipo docente: **ningún ayudante ve un tablero recortado a los repositorios que corrige**, porque el filtro por asignación de corrección pertenece a la bandeja del capítulo 12, no al seguimiento. Configurar los umbrales de curso (§10.5.3, §10.8.2) exige `curso.administrar`; su anulación por tarea, marcar hitos del timeline (§10.9.3) y las demás acciones de tarea exigen `tarea.administrar`; resolver identidades y revelar un correo (§10.3.4, §10.3.6) exigen `mapeo.editar`. **No se crea ningún permiso nuevo para este capítulo**: los que ya define el modelo de roles bastan y se reutilizan tal cual.

### 10.10.8 Criterios de aceptación de §10.10

1. **CA-10.10-01.** Un repositorio que pasa a `INACCESIBLE` conserva su historia visible en el tablero y en el timeline, con el enlace a GitHub sustituido por el motivo.
2. **CA-10.10-02.** Un estudiante retirado del curso desaparece de las tarjetas de «sin participación» pero sus commits siguen visibles, atribuidos y marcados «retirado el dd-MM» en la comparación.
3. **CA-10.10-03.** Un estudiante que sale de un grupo a mitad de una entrega conserva sus commits atribuidos al repositorio de origen, y el cambio queda marcado en el timeline de origen y de destino en la misma transacción.
4. **CA-10.10-04.** Exportar la comparación de un repositorio con un estudiante sin `mapeo.editar` produce un CSV con los correos ofuscados; repetir la exportación con `mapeo.editar` produce el correo completo y una fila en bitácora.
5. **CA-10.10-05.** Un ayudante sin repositorios asignados en corrección abre el tablero completo de una tarea y ve las mismas cifras que un profesor.
6. **CA-10.10-06.** La vista de curso y el informe diario del capítulo 11 del mismo día muestran, para la misma tarea, el mismo recuento de «sin actividad reciente».

---

## 10.11 Trazabilidad de requisitos

| Requisito | Dónde se especifica |
|---|---|
| **R2.5.1** | §10.7.1 (contenido cerrado del tablero, pantalla por defecto de la tarea) |
| **R2.5.2** | §10.7.3 (serie agregada, selección de repositorios, sparklines), §10.5.1 (commit contable) |
| **R2.5.3** | §10.5.3 (umbral de días sin actividad, ventana observada), §10.4.3 (incidencia `SIN_ACTIVIDAD`) |
| **R2.5.4** | §10.5.3 (las tres causas de «sin participación»), §10.3 (atribución de commits) |
| **R2.5.5** | §10.7.2 (estado de creación y configuración, consumido del capítulo 8, no redefinido) |
| **R2.5.6** | §10.6.1 (estado agregado de nueve valores), §10.6.4 (línea de entregas) |
| **R2.5.7** | §10.6.2–§10.6.3 (ventana por sujeto), §10.7.4 (selector de periodo) |
| **R2.5.8** | §10.8.1–§10.8.2 (comparación entre integrantes, índice de desequilibrio) |
| **R2.5.9** | §10.8.4 (las cinco métricas adicionales) |
| **R2.5.10** | §10.9 (timeline: cuatro capas, navegación, cambios principales) |
