# 11. Informe docente diario y comunicación

Este capítulo especifica la generación del informe docente diario —qué contiene, cuándo existe y
cuándo deliberadamente no existe—, la suscripción y desuscripción individual de profesores y
ayudantes, el envío del informe por correo, los mensajes directos que la aplicación envía a un
estudiante por Canvas, los anuncios de curso, y el catálogo cerrado de comunicaciones automáticas que
el profesor activa o desactiva dentro de cada tarea. Cubre también el modelo de datos único del que
salen las cuatro clases de comunicación —mensaje directo, anuncio, comentario de entrega y correo—,
su trazabilidad y su comportamiento ante fallos, cuota agotada o canal degradado.

**Requisitos que satisface:**

- **R2.6.1** Generar un informe docente diario con información relevante sobre el desarrollo de las
  tareas activas (si no hay tareas activas entonces no hay informe).
- **R2.6.2** Incluir en este informe situaciones que puedan requerir la intervención del equipo
  docente, tales como ausencia de actividad, estudiantes sin participación o problemas pendientes en
  la creación de repositorios.
- **R2.6.3** Permitir que profesores y ayudantes se suscriban o den de baja individualmente de estos
  informes.
- **R2.6.4** Enviar el informe a profesores y ayudantes suscritos a través de email.
- **R2.6.5** Enviar mensajes directos a través de Canvas a estudiantes cuando sea necesario comunicar
  información particular relacionada con una entrega o repositorio (creación, corrección, etc.).
- **R2.6.6** Generar anuncios en Canvas del curso para comunicar eventos generales asociados a una
  tarea, como cambio en las fechas de entrega.
- **R2.6.7** Generar automáticamente comunicaciones asociadas a determinados eventos relevantes,
  tales como la disponibilidad de los repositorios o la proximidad de una fecha correspondiente a
  alguna de las entregas de la tarea. Estas comunicaciones pueden ser activadas o desactivadas por el
  profesor dentro de cada tarea.

---

## 11.1 Cómo leer este capítulo

**Orden de precedencia aplicado, sin excepciones:** enunciado → actas de reconciliación (`RG-nnn`,
con `parte-4-cruce.md` arbitrando sobre `parte-1`, `parte-2` y `parte-3` donde se contradicen) →
carta de arquitectura (`A-nnn`, en su texto ya corregido por las actas) → respuestas de alcance
(`Q-2.6-nn`). Donde una respuesta de alcance de los lotes 15 a 17 decía una cosa y una regla `RG` dice
otra, manda la regla y este capítulo redacta la regla.

### 11.1.1 Fuera de alcance de este capítulo: qué se cita y dónde vive

| Tema | Dónde se especifica | Qué hace este capítulo con él |
|---|---|---|
| Mecanismo técnico de la llamada a la API de Canvas para enviar un mensaje o publicar un anuncio: endpoint, autenticación, cabeceras, quién queda firmando la escritura | **§5 Integración con Canvas** | Sólo cita el endpoint y el formato por canal (A-126); no redefine cómo se autentica la llamada |
| Infraestructura de correo transaccional: proveedor, DNS, cuota diaria repartida en tres reservas, variable `EMAIL_PROVIDER_API_KEY`, interfaz `ProveedorCorreo` | **§14.12** | Cita la cuota y el proveedor; especifica el contenido, la plantilla y la lógica de envío propias del informe |
| Dashboard de seguimiento: umbral de días sin actividad, las tres causas de «sin participación», cálculo de métricas | **§10** | Consume esos predicados ya calculados para armar las secciones 3 y 4 del informe; no redefine el umbral ni la atribución |
| Estado de aprovisionamiento de repositorios: qué está pendiente, bloqueado o con error | **§8 Aprovisionamiento de repositorios** | Consume ese estado para la sección 1 y 2 del informe; no redefine la máquina de estados del repositorio |
| Catálogo completo de los nueve permisos y quién puede tenerlos | **§2 Roles y permisos** | Cita `comunicacion.enviar` y `curso.ver`; no redefine la matriz |
| `curso.canal_comunicacion_activo`, su cascada de tres canales y su degradación | **§7.2.3** (ya existente) | Usa la columna y la cascada tal como están fijadas; §11.9 explica su efecto sobre los mensajes de este capítulo, sin rediseñarla |
| Revocación del acceso de un estudiante al salir de un grupo, y sus dos avisos obligatorios | Máquina de acceso al repositorio (**A-212**, **RG-009**, **RG-010**) | **No es una comunicación de R2.6.7.** §11.6.6 explica por qué queda fuera del catálogo de este capítulo |

### 11.1.2 Correcciones de precedencia que este capítulo aplica

Las respuestas de alcance de los lotes 15, 16 y 17 son la fuente de contenido más detallada del área
2.6, pero cuatro actas de reconciliación las corrigen en puntos concretos. **Manda siempre la columna
derecha.**

| Punto | Lo que proponía una respuesta de alcance | Lo que rige ahora | Fuente |
|---|---|---|---|
| Componente variable de la clave de idempotencia | `version`, incrementado de forma ad-hoc por cada caso (reenvío, cambio de fecha, reactivación) | **`generacion`**, columna `smallint` materializada y auditable, con `reemplaza_a_id` encadenando la reemisión con la fila retenida | RG-036, A-224 |
| Índice de unicidad de `mensaje_saliente.clave_idempotencia` | Único **parcial**, excluyendo los estados terminales de descarte (`CANCELADO`, `SUPRIMIDO`, `CADUCADO`, `RETRACTADO`) | Único **total**, sin excepción. Una reemisión legítima no reutiliza la clave: incrementa `generacion` y produce una clave nueva | RG-036, A-224 |
| Ámbito de la cuota de correo del informe | «Una sola cuota por curso y por ventana» | **Es del despliegue y del día**: 100 correos diarios para toda la instalación, repartidos 60 informe / 20 operativo / 20 margen | RG-104 → RG-197, A-228 |
| Esquema de `informe_diario` | `hay_tareas_activas` booleano; columnas `periodo_desde` / `periodo_hasta` | **`estado`** con tres valores (`GENERADO`, `SIN_TAREAS_ACTIVAS`, `NO_GENERADO`) y `motivo`; **`ventana_desde_utc`** / **`ventana_hasta_utc`**, acumulada desde el último informe generado con éxito y acotada a 7 días | RG-041, RG-207, A-229 |
| Rutas y caducidad del enlace de baja | `/informes/baja/{token}` y `/informes/alta/{token}`; token de 30 días | **`GET`/`POST /baja/{token}`** y re-suscripción con **`POST /baja/{token}?accion=alta`**; token HMAC-SHA256 de **90 días**, reutilizable, con revocación en bloque vía `usuario.generacion_enlaces` | RG-131 |
| Caducidad de los enlaces de traza `/r/{t}` de cada línea del informe | 30 días | **90 días**, la misma cifra que el enlace de baja: «hay una sola cifra en la especificación» | RG-131 |
| Octavo evento del catálogo de comunicaciones automáticas: `salida_de_grupo` | Evento de alcance TAREA, canal activo, activado por defecto, tope 1 por `(tarea, sujeto, estudiante)`, caducidad 72 h | **No existe como evento de R2.6.7.** El aviso al estudiante que sale de un grupo es `aviso_revocacion_acceso` / `confirmacion_revocacion_acceso`: una notificación **obligatoria** de la transacción de revocación de acceso, sin interruptor, sin tope y sin fila en `regla_comunicacion` | RG-010 |
| Máquina de estados de `mensaje_saliente` | Enumerada de forma dispersa, sin catálogo cerrado de motivos | **Máquina 7 del sistema**, quince estados cerrados (§11.2.2), veinte motivos cerrados (§11.2.4) y siete guardas del outbox en orden fijo (§11.2.3) | RG-038, RG-039, RG-040 |
| Comprobación del interruptor de una regla de comunicación antes de reintentar | Bastaba comprobarlo al encolar | Se comprueba **dentro del trabajo, inmediatamente antes de cada intento** (guarda 4 de §11.2.3), no sólo al encolar | RG-039 |

**Convenciones de escritura obligatorias, heredadas de §7.1 y §12.1 y aplicadas aquí sin excepción:**
todo instante se almacena en UTC y se presenta en la zona horaria del curso con formato
`dd-MM-yyyy HH:mm` y la zona escrita al lado siempre (A-152); todo estado interno se muestra
traducido con etiqueta fija, nunca un identificador en mayúsculas en pantalla (A-155); el vocabulario
es el cerrado de A-154 —**informe diario**, **incidencia**, **repositorio**— y no admite sinónimos;
ninguna pantalla de este capítulo llama a Canvas o a GitHub para pintarse (Ley 1, A-119): todo sale
del espejo, y la única llamada en vivo es la que un docente dispara explícitamente para enviar un
correo de prueba o comprobar un anuncio contra Canvas (§11.10).

---

## 11.2 Modelo de datos de las comunicaciones salientes

**Un único outbox para las cuatro comunicaciones hacia el exterior** —mensaje de Canvas, anuncio de
Canvas, comentario de entrega y correo—: la tabla `mensaje_saliente` y el trabajo `despachar_outbox`
(A-125). Ninguna comunicación se envía de forma síncrona desde una vista: no es una de las seis
escrituras síncronas de A-169, precisamente porque un aviso a un tercero no puede depender de que una
petición HTTP del docente termine bien.

### 11.2.1 `mensaje_saliente`: columnas

| Bloque | Columnas | Regla |
|---|---|---|
| **Identidad y canal** | `id`, `curso_id`, `canal ∈ {CANVAS_CONVERSACION, CANVAS_ANUNCIO, CANVAS_COMENTARIO, CORREO}`, `evento` | `evento` es uno de los siete de §11.6.1, o `MANUAL` (mensaje o anuncio redactado por una persona), `INFORME_DIARIO` (el correo del informe) o `VERIFICACION` (la prueba de escritura de A-042) |
| **Idempotencia** | `clave_idempotencia = hash(canal, destinatario, plantilla, entidad, generacion)`, **única en base de datos, índice total** | RG-036, A-224. `generacion smallint NOT NULL DEFAULT 1` y `reemplaza_a_id uuid NULL` encadenan toda reemisión: fecha cambiada, regla reactivada, mensaje retractado que hay que reemitir, reenvío pedido por el destinatario |
| **Vínculos** | `tarea_id`, `entrega_id`, `sujeto_id`, `repositorio_id`, `estudiante_id`, `membresia_id` (las seis FK, **indexadas**, nullable), `referencia jsonb` | Las seis columnas son las que hacen posible leer el historial por tarea, por estudiante o por repositorio sin recorrer un `jsonb` opaco; `referencia` guarda el contexto que no es una entidad propia (ámbito de un anuncio, fecha anterior y nueva, etc.) |
| **Destinatario** | `destinatario` (texto legible), `destinatario_canvas_user_id` (`bigint`) | Ley 3: la clave es `destinatario_canvas_user_id`; el texto es dato de presentación |
| **Contenido** | `plantilla`, `plantilla_version`, `asunto` (≤ 255 caracteres, único límite documentado del endpoint de conversaciones — `Q-2.6-03`), `cuerpo_renderizado`, `canal_efectivo` | `cuerpo_renderizado` se escribe en el **despacho**, no al encolar, para que un cambio de horario de verano no produzca una hora equivocada (Q-2.6-41 punto 6). `canal_efectivo` registra cuál de los canales de A-127 se usó realmente cuando hubo degradación (§11.9) |
| **Origen y autoría** | `origen ∈ {AUTOMATICO, MANUAL, SISTEMA}`, `disparado_por_usuario_id`, `disparado_por_trabajo_id`, `credencial_canvas_id`, `es_prueba` | `credencial_canvas_id` es la columna sin la cual no se puede auditar a nombre de quién salió la escritura (A-142). `es_prueba` marca los envíos de prueba de §11.6.3 y §11.9; su clave lleva el prefijo `prueba:` más el `usuario_id`, de modo que probar una plantilla **no consume ni satisface** la clave del envío real |
| **Programación** | `programado_para`, `caduca_en` | `programado_para` materializa la ventana horaria de §11.7.6; `caduca_en` es la caducidad por tipo de §11.2.4 |
| **Estado** | `estado` (máquina 7, quince valores, §11.2.2), `motivo_estado` (veinte valores, §11.2.4), `intentos`, `ultimo_codigo_http`, `ultimo_error_literal`, `tomado_por`, `tomado_en` | `ultimo_error_literal` guarda el texto **literal** del proveedor, nunca una traducción (A-155) |
| **Resultado** | `canvas_id_resultante` (`{conversation_id, message_id}` o `{discussion_topic_id}` o `{submission_comment_id}`), `canvas_html_url`, `proveedor_id` (correo), `enviado_en` | Sin llamada adicional (Ley 1): el enlace «abrir en Canvas» se construye desde estas columnas |
| **Retractación** | `retractado_en`, `retractado_por`, `cancelacion_solicitada` | §11.8.8 |

**Unicidad y trazabilidad.** `mensaje_saliente` entra en la lista de tablas **sin purga** de A-090,
junto a `commit`, `version_entrega`, `bitacora` y `publicacion_nota`, porque es la evidencia de
**R2.3.12** y de **R2.6.4**. Un `cuerpo_renderizado` por encima de 16 KB se trunca y se marca
`cuerpo_truncado`, mismo patrón que A-090 aplica a `evento_webhook`.

### 11.2.2 Los quince estados de `mensaje_saliente` (máquina 7)

`PROGRAMADO` → `PENDIENTE` → `EN_CURSO` → { `ENVIADO` | `REINTENTAR` | `ESPERANDO_LIMITE` |
`ESPERANDO_CREDENCIAL` | `BLOQUEADO` | `REQUIERE_ATENCION` | `FALLIDO` }, más `DIFERIDO` y las
salidas laterales `CANCELADO`, `SUPRIMIDO`, `CADUCADO` y `RETRACTADO`. `DEFAULT 'PENDIENTE'`.
(RG-038.)

| Estado | Significado | Etiqueta en pantalla |
|---|---|---|
| `PROGRAMADO` | Tiene hora futura de envío | «Programado para el DD-MM a las HH:MM» |
| `DIFERIDO` | Retenido por una condición externa reversible, no por un fallo | «En espera» |
| `PENDIENTE` | Listo para que `despachar_outbox` lo tome | «En cola» |
| `EN_CURSO` | Tomado por el despachador | «Enviando» |
| `ENVIADO` | Confirmado por el proveedor | «Enviado» |
| `REINTENTAR` | `5xx`, error de red o tiempo agotado | «Reintentando, próximo intento a las HH:MM» |
| `ESPERANDO_LIMITE` | `429` o `403` de límite de tasa | «Esperando a Canvas por límite de uso» (Ley 5: nunca se pinta como error) |
| `ESPERANDO_CREDENCIAL` | `401`; dispara A-036 entero | «Esperando credencial de Canvas» |
| `BLOQUEADO` | `403` por permiso retirado; se reevalúa cada 30 min | «Bloqueado por permisos de Canvas» |
| `REQUIERE_ATENCION` | Quedó `EN_CURSO` más de 10 minutos: pudo haberse enviado | «Pudo haberse enviado» |
| `FALLIDO` | Agotados los 6 intentos, o `4xx` permanente | «No se pudo enviar» |
| `CANCELADO` | La entidad que lo originó desapareció | «Cancelado» |
| `SUPRIMIDO` | La condición que lo originó ya no se cumple | «No se envió (filtrado)» |
| `CADUCADO` | Venció `caduca_en`, o la retención de un diferido se prolongó | «Ya no tenía sentido» |
| `RETRACTADO` | Retirado a petición del docente | «Retirado» |

**Estados terminales:** `ENVIADO`, `FALLIDO`, `CANCELADO`, `SUPRIMIDO`, `CADUCADO`, `RETRACTADO`. Un
`FALLIDO` **no se reintenta solo nunca más**: sólo por acción de un docente desde
`/cursos/{id}/comunicaciones` o desde `/operacion` (§11.10). `REQUIERE_ATENCION` no es terminal y
**no se reenvía a ciegas**: el diseño prefiere no duplicar aunque eso signifique un envío perdido, y
lo declara en pantalla, porque un estudiante que recibe el mismo mensaje cinco veces deja de leerlos
—y eso sí rompe **R2.3.12**.

**Clasificación por respuesta del proveedor**, con las tres familias de A-116:

| Respuesta | Familia | Desenlace |
|---|---|---|
| `429`, o `403` cuyo cuerpo menciona límite o *throttling* | TRANSITORIO | `ESPERANDO_LIMITE`, retroceso exponencial con *jitter* base 2 s, factor 2, tope 5 min, máximo 6 intentos |
| `5xx`, tiempo de espera agotado, error de red | TRANSITORIO | `REINTENTAR`, mismo retroceso, hasta 6 intentos |
| `401` | BLOQUEANTE | `ESPERANDO_CREDENCIAL`, dispara A-036 completo: credencial a `INVALIDA`, promoción automática del respaldo, curso a `CANVAS_DESVINCULADO`, banda roja, correo a los profesores |
| `403` por permiso retirado (`send_messages`) | BLOQUEANTE | `BLOQUEADO`, reevaluado cada 30 min; conmuta al canal 2 de A-127 si procede (§11.9) |
| `4xx` por destinatario inválido o de validación del cuerpo | PERMANENTE | Cero reintentos; `FALLIDO` con el cuerpo literal; **el lote continúa con el resto** |
| `403` con cuerpo no reconocido | — | Se trata como BLOQUEANTE, nunca como fallo del estudiante, y se muestra el literal |

Una fila `EN_CURSO` cuyo `tomado_en` lleva vencido más de 10 minutos **no se reenvía a ciegas**: pasa
a `REQUIERE_ATENCION`, visible en `/operacion` y en el historial, y decide un docente. La garantía no
depende de la memoria del proceso: la clave única total (§11.2.1) y las garantías 1 a 3 de A-115 son
las que impiden un duplicado.

### 11.2.3 Las siete guardas del outbox, en orden fijo

`despachar_outbox` evalúa siete guardas **en este orden exacto**, en una única función
`guardas_outbox(mensaje) -> (estado, motivo) | None` de `backend/app/dominio/comunicaciones.py`: la
primera que se cumple decide el desenlace. Ninguna otra parte del sistema decide por su cuenta si un
mensaje puede salir; la pantalla «por qué no salió» llama a la misma función. (RG-039.)

| # | Guarda | Desenlace | `motivo_estado` |
|---|---|---|---|
| 1 | `caduca_en` vencido | `CADUCADO` | `CADUCIDAD_ALCANZADA` |
| 2 | Destinatario sin matrícula `active` ni `invited` | `SUPRIMIDO` | `MATRICULA_NO_ACTIVA` |
| 3 | `supresion_comunicacion` vigente para ese estudiante | `SUPRIMIDO` | `SUPRESION_POR_ESTUDIANTE` |
| 4 | `regla_comunicacion.activa = false` para `(curso, tarea, evento)` | `SUPRIMIDO` | `REGLA_DESACTIVADA` |
| 5 | `curso.modo_escritura = 'SOLO_LECTURA'` | `DIFERIDO` | `MODO_SOLO_LECTURA` |
| 6 | `curso.comunicaciones_salientes = 'SUSPENDIDAS'` y canal ∈ {`CANVAS_CONVERSACION`, `CANVAS_ANUNCIO`, `CANVAS_COMENTARIO`} | `DIFERIDO` | `SUSPENSION_DE_CURSO` |
| 7 | `ventana_supresion` vigente que cubre el mensaje | `DIFERIDO` | `VENTANA_TRAS_RESTAURACION` |

**Por qué ese orden:** primero las cuatro razones terminales —el mensaje ya no tiene sentido, el
destinatario no es alcanzable, alguien decidió no escribirle, el evento está apagado— y después las
tres reversibles. Al revés, un mensaje caducado quedaría diferido esperando una reanudación que nunca
lo hará útil. La guarda 6 **nunca detiene el canal `CORREO`**: la suspensión de comunicaciones de un
curso frena sólo lo que se escribe en Canvas (A-225).

**Cuándo se comprueba:** dentro del trabajo, **inmediatamente antes de cada intento**, no sólo al
encolar. Con `despachar_outbox` cada 30 segundos, la ventana real de un envío indeseado —por ejemplo,
tras apagar un interruptor— es el tiempo de una petición HTTP (RG-039, corrige la lectura de que
bastaba comprobar al encolar). Un mensaje `DIFERIDO` por las guardas 5, 6 o 7 durante más de 7 días
pasa a `CADUCADO` con `motivo_estado = 'SUSPENSION_PROLONGADA'`, en el trabajo `purga_retencion` de
las 03:00.

### 11.2.4 Catálogo cerrado de `motivo_estado` (veinte valores)

Ningún valor pertenece a dos estados; el catálogo es obligatorio en los seis estados terminales
laterales y en `DIFERIDO`. Añadir un valor es una decisión que se registra en la carta. (RG-040.)

| Estado | Motivos |
|---|---|
| `CADUCADO` | `CADUCIDAD_ALCANZADA`, `SUSPENSION_PROLONGADA` |
| `SUPRIMIDO` | `MATRICULA_NO_ACTIVA`, `SUPRESION_POR_ESTUDIANTE`, `REGLA_DESACTIVADA`, `YA_ACEPTADO`, `MAPEO_YA_VIGENTE`, `ENTREGA_EXCLUIDA`, `NO_ES_DESTINATARIO_VALIDO`, `FUERA_DEL_GRUPO`, `TAREA_REGISTRO_AUSENTE` |
| `DIFERIDO` | `MODO_SOLO_LECTURA`, `SUSPENSION_DE_CURSO`, `VENTANA_TRAS_RESTAURACION`, `PUBLICACION_PENDIENTE`, `CUOTA_AGOTADA` |
| `CANCELADO` | `CURSO_ARCHIVADO`, `TAREA_ARCHIVADA`, `ENTREGA_ELIMINADA`, `ACCION_DOCENTE` |

`CUOTA_AGOTADA` es el único nombre para el agotamiento de la cuota de correo de §14.12: no existe
`CUOTA_CORREO_AGOTADA` como motivo de mensaje (ese nombre queda para la incidencia homónima).
`ACCION_DOCENTE` es también el término que usan `motivo_revocacion` y `motivo_cancelacion` en otros
capítulos, para que un mismo hecho se nombre igual en todas partes (A-154).

**Caducidad por tipo de evento** (`caduca_en`), evaluada antes de cada intento (guarda 1):

| Evento | `caduca_en` |
|---|---|
| `proximidad_cierre` (48 h y 6 h) | La `fecha_efectiva` vigente de esa entrega para ese sujeto |
| `recordatorio_invitacion` | El instante en que `acceso_repositorio` pasa a `ACEPTADO`, o el cierre de la última entrega de la tarea |
| `recordatorio_mapeo` | El instante en que el mapeo pasa a `VIGENTE`, o el cierre de la tarea de registro |
| `cambio_de_fecha` | 24 h desde el cambio, o la fecha nueva si es antes |
| `repositorio_disponible`, `invitacion_aceptada`, `correccion_publicada` | **Nunca caducan.** Son hechos, no avisos con ventana: tarde es mejor que nunca, porque **R2.3.12** exige que el estudiante reciba la información de acceso |
| Informe diario por correo | No caduca: se difiere (`CUOTA_AGOTADA`) y se reintenta al día siguiente |

### 11.2.5 `plantilla_mensaje`: versionada, con sobrescritura opcional por curso

Las plantillas de todo este capítulo viven en la tabla `plantilla_mensaje
(id, curso_id nullable, clave, canal, asunto, cuerpo, version, activa, creada_por, creada_en,
vigente_hasta)`, *append-only*: editar no actualiza la fila, cierra la vigente y crea una nueva con
`version = anterior + 1` (Ley 2). `curso_id` nulo es la plantilla base del sistema, cargada por
migración desde el archivo único de mensajes de A-126 y A-154; **nunca por tarea** —`recordatorio_mapeo`
es de curso por A-130 regla 3 y no tendría dónde vivir una plantilla de tarea, y un curso con cinco
tareas y siete eventos produciría treinta y cinco textos que nadie revisa de una sentada (A-126)—.
(Q-2.6-53.)

**Variables por clave, catálogo cerrado, no espacio global**: cada evento expone sólo las variables
que le corresponden (`{{estudiante.nombre}}`, `{{repositorio.url}}`, `{{entrega.fecha_cierre}}`,
`{{version.sha_corto}}`, etc.), para que una plantilla de recordatorio de mapeo no pueda referenciar
una variable de versión que no tiene valor. No existe `{{fecha_local}}`: toda fecha se nombra por lo
que es y se renderiza siempre con el formato de A-152.

**Validación bloqueante al guardar:** variable desconocida o no disponible para esa clave se rechaza;
`{{` sin cerrar o filtros se rechazan (el motor es sustitución pura, sin lógica); las variables
obligatorias por clave no se pueden omitir (`repositorio_disponible` sin `{{repositorio.url}}` no se
guarda, porque sin la URL el mensaje incumple **R2.3.12**); el formato por canal de A-126 se aplica
(texto plano sin etiquetas para `CANVAS_CONVERSACION`/`CANVAS_COMENTARIO`, lista blanca de cinco
etiquetas para `CANVAS_ANUNCIO`/`CORREO`); asunto ≤ 255 caracteres; sin emojis, español de Chile, «tú»
(A-154).

**Previsualización con datos reales, obligatoria antes de activar cualquier comunicación** (A-130):
se renderiza contra un estudiante de ejemplo del curso, o contra un sujeto sintético marcado «datos
de ejemplo» si aún no hay ninguno resoluble; toda variable no resuelta se resalta en ámbar con su
nombre, **nunca en blanco**. El envío de prueba (§11.6.3) es siempre a uno mismo, por correo o por
Canvas, y nunca a un estudiante.

### 11.2.6 `supresion_comunicacion`: silenciar a una persona, no al curso

`supresion_comunicacion (id, curso_id, estudiante_id, alcance, motivo, creada_por, creada_en,
vigente_hasta, levantada_en, levantada_por)`, con `alcance ∈ {TODAS_AUTOMATICAS,
SOLO_RECORDATORIOS}` y único parcial `(curso_id, estudiante_id)` donde `levantada_en IS NULL`.
`motivo` es obligatorio y de texto libre; requiere `comunicacion.enviar`. Mientras esté vigente, la
guarda 3 de §11.2.3 suprime toda fila automática dirigida a esa persona; **los mensajes manuales no
se ven afectados**, porque quien redacta uno sabe lo que hace. (Q-2.6-42(e).)

### 11.2.7 `cambio_fecha`: la fila que agrupa un cambio de fecha antes de comunicarlo

`cambio_fecha (id, entrega_id, huella_anterior, huella_nueva, ambito, seccion_ids[], sujeto_ids[],
detectado_en, ventana_cierra_en, anunciado_en, mensaje_saliente_id)`, con `ambito ∈ {CURSO, SECCION,
GRUPO, ADHOC}`. Es la fila sobre la que actúan el umbral, el *debounce* y la idempotencia del anuncio
de cambio de fecha (§11.8.3, §11.8.6). (Q-2.6-45, Q-2.6-46, Q-2.6-49.)

### 11.2.8 Criterios de aceptación de §11.2

| # | Criterio |
|---|---|
| CA-11.2-01 | Un `INSERT` que intente una segunda fila viva con la misma `clave_idempotencia` es rechazado por el índice único **total**, no por un índice parcial |
| CA-11.2-02 | Reemitir un mensaje suprimido no reutiliza su clave: la fila nueva lleva `generacion` incrementada y `reemplaza_a_id` apuntando a la anterior, y las dos coexisten en el historial |
| CA-11.2-03 | El `CHECK` de `mensaje_saliente.estado` contiene exactamente los quince valores, generado desde `backend/app/dominio/estados.py` |
| CA-11.2-04 | El `CHECK` de `motivo_estado` contiene exactamente los veinte valores, y ningún valor aparece bajo dos estados distintos |
| CA-11.2-05 | Ejecutar `guardas_outbox` sobre un mensaje con `caduca_en` vencido **y** regla desactivada devuelve `CADUCADO`, nunca `SUPRIMIDO`: gana la guarda de menor número |
| CA-11.2-06 | Apagar un interruptor con un mensaje `EN_CURSO` no lo cancela; termina y, si falla, no reintenta |
| CA-11.2-07 | Guardar una plantilla `repositorio_disponible` sin la variable `{{repositorio.url}}` es rechazado con el nombre de la variable faltante |
| CA-11.2-08 | Un envío de prueba de una plantilla a sí mismo no impide que el estudiante usado como ejemplo reciba después su propio mensaje real |
| CA-11.2-09 | `mensaje_saliente` no aparece en ninguna tabla de retención con purga; una búsqueda en el catálogo de A-090 lo confirma |

---

## 11.3 El informe docente diario: contenido y condición de existencia (R2.6.1, R2.6.2)

### 11.3.1 Cuándo existe: la definición de «tarea activa»

**Una tarea es activa, a efectos del informe, si y sólo si se cumplen tres condiciones**, evaluadas
por una única función de `backend/app/dominio/informe.py` que usan también la pantalla de vista
previa y ninguna otra consulta reimplementa (Q-2.6-06):

1. `tarea.estado ∈ {ACTIVA, INCONSISTENTE}`.
2. `curso.estado ∈ {ACTIVO, CANVAS_DESVINCULADO, GITHUB_DESVINCULADO}` —los dos estados laterales se
   incluyen a propósito: lo que no depende de Canvas no se detiene, y el informe se construye
   enteramente desde el espejo (Ley 1).
3. Y al menos una de estas tres patas:
   - **(a) Fecha viva** — alguna `fecha_efectiva` vigente de alguna entrega **publicada** de la
     tarea cuyo cierre no ha vencido, evaluada sobre todos los sujetos.
   - **(b) Aprovisionamiento incompleto** — algún `repositorio` en un estado distinto de
     `OPERATIVO`, `FUERA_DE_ALCANCE` y `ARCHIVADO`, o algún sujeto activo en
     `ESPERANDO_INFORMACION`.
   - **(c) Problema abierto** — alguna incidencia abierta de severidad `BLOQUEANTE`, o de tipo
     `VERSION_REVISAR` o `VERSION_ERROR`, de un sujeto de la tarea.

**Si no hay tareas activas, no se genera ni se envía nada**, exactamente como dice el requisito
(«si no hay tareas activas entonces no hay informe»), y el histórico registra la fila del día con
`estado = 'SIN_TAREAS_ACTIVAS'`, para poder demostrar que la ausencia fue deliberada y no un fallo
(A-131).

### 11.3.2 `informe_diario`: esquema

| Columna | Tipo | Regla |
|---|---|---|
| `curso_id`, `fecha` | uuid, date | **Único `(curso_id, fecha)`**, con `fecha` en la zona horaria del curso |
| `estado` | text | `CHECK IN ('GENERADO', 'SIN_TAREAS_ACTIVAS', 'NO_GENERADO')` |
| `motivo` | text nullable | Obligatorio si `estado = 'NO_GENERADO'` (por ejemplo, `SISTEMA_DETENIDO`) |
| `ventana_desde_utc`, `ventana_hasta_utc` | timestamptz | Ver §11.3.3 |
| `origen` | text | `CHECK IN ('PROGRAMADO', 'MANUAL')` |
| `disparado_por_usuario_id` | uuid nullable | Quien disparó una generación manual |
| `frescura` | jsonb | Antigüedad de la sincronización con Canvas y con GitHub en el instante de generación (§11.3.5) |
| `contenido`, `contenido_html`, `contenido_texto` | jsonb, text, text | Se congelan al generarse y **no se actualizan nunca** (Ley 2, igual que `version_entrega`) |

`hay_tareas_activas` **se retira del esquema**: un booleano no distingue «no había tareas activas» de
«no se pudo generar», y A-131 exige poder demostrar cuál de las dos ocurrió. Las columnas
`periodo_desde` / `periodo_hasta` de propuestas anteriores no existen: los nombres correctos llevan la
zona en el nombre, como exigen A-073 y A-152. (RG-041, RG-207.)

**Histórico:** no falta ninguna fila de `informe_diario` **entre la primera generada para el curso y
hoy**. La primera fila es la del día en que el trabajo entra en servicio para ese curso; no se generan
filas retroactivas para los días anteriores. `/cursos/{id}/mis-notificaciones` y `/api/cursos/{id}/informes`
declaran esa fecha de inicio con el texto «el informe diario de este curso se genera desde el
DD-MM-YYYY» (RG-207, A-229).

### 11.3.3 Generación: ritmo, ventana acumulada y días perdidos

**Trabajo `informe_diario`: 07:00 en la zona horaria del curso, más un barrido cada 30 minutos entre
las 07:00 y las 23:00 de esa misma zona**, *no-op* si la fila `(curso, hoy)` ya existe —la misma
doctrina que A-101 aplica a la captura de versiones: barrer lo vencido, no disparar a una hora exacta
única—. Bajo `pg_advisory_lock(curso_id)` por hablar con Canvas (A-217). (A-114, A-131, A-152, A-229.)

**Si el sistema estuvo detenido y el día del curso ya terminó cuando vuelve, el informe de ese día no
se genera retroactivamente**: la fila queda `estado = 'NO_GENERADO'`, `motivo = 'SISTEMA_DETENIDO'`.
Las secciones 1 a 4 son estado en el instante de generación y son irreconstruibles hacia atrás; fingir
un informe de ayer con datos de hoy sería mentir.

**Ventana acumulada.** `ventana_desde_utc` es el `ventana_hasta_utc` del último informe **generado
con éxito** del curso, o `curso.creado_en` si es el primero; **acotada a 7 días**. En el caso normal
son 24 horas exactas; si el informe de ayer no se generó, el de hoy cubre 48 horas y el encabezado lo
dice con esas palabras. **Sólo la sección 5** usa la ventana; las secciones 1 a 4 son estado en el
instante de generación, no una ventana acumulada (A-229).

### 11.3.4 Contenido: cinco secciones fijas, cada una se omite si está vacía

Las cinco secciones de A-131, en este orden, cada una omitida si no tiene líneas. Cada línea nombrada
en una sección se lee de **la misma tabla `incidencia`** que alimenta Pendientes, el estado de
repositorios y el tablero (A-088), de modo que el informe, la pantalla de tarea y Pendientes nunca se
contradicen (Q-2.6-09).

| # | Sección | Contenido |
|---|---|---|
| 1 | **Requiere tu atención hoy** | Repositorios `BLOQUEADO` o `ERROR_PERMANENTE` con su subtipo y el mensaje literal de GitHub (§8); incidencias abiertas de severidad `BLOQUEANTE` de la tarea; `CANVAS_CREDENCIAL_INVALIDA` y `GITHUB_PERMISOS_PENDIENTES`; versiones en `REVISAR` o `VERSION_ERROR`; comunicaciones en `FALLIDO` definitivo (las que reintentan no aparecen — Ley 5); recordatorio del canal de comunicación activo mientras no sea el canal 1 (§11.9) |
| 2 | **Información pendiente** | Estudiantes sin cuenta de GitHub, invitaciones sin aceptar con más de 48 h, grupos incompletos, estudiantes sin grupo, sujetos en `ESPERANDO_INFORMACION` con su motivo, entregas vinculadas sin publicar en Canvas |
| 3 | **Sin actividad** | Repositorios sin commits contables según el umbral de §10 (7 días por defecto, 2 en ventana crítica) y estudiantes sin participación, **con las tres causas distinguidas** (§10); declara en su encabezado la ventana observada («actividad observada desde DD-MM-YYYY»), y **no se pronuncia** sobre un repositorio cuya ventana observada sea más corta que el umbral —ese repositorio no cuenta como inactivo en ninguna parte y muestra «sin dato suficiente» (RG-155): **R2.6.2** pide informar, no alarmar. Las incidencias `SIN_ACTIVIDAD` y `SIN_PARTICIPACION` que un docente silenció desde Pendientes quedan **fuera de esta sección** (RG-042) |
| 4 | **Próximos cierres** | Entregas que cierran en las próximas 72 h, con el número de sujetos sin ningún commit; cambios de fecha detectados en Canvas durante el período |
| 5 | **Resumen del período** (se titula así, no «resumen de ayer», cuando la ventana cubre más de un día) | Commits contables y repositorios activos, versiones capturadas desglosadas por estado, notas publicadas y correcciones pendientes, repositorios que pasaron a `OPERATIVO` en el período |

**Reglas de redacción, sin excepción:** cada línea lleva un enlace profundo a la pantalla exacta
donde se resuelve; **tope de 10 elementos nombrados por línea**, con «y N más» y enlace a la vista
completa; cada incidencia se nombra **una sola vez, en la sección de mayor severidad**, y en cualquier
otra sólo se cuenta; el orden de las líneas dentro de una sección es por severidad
(`BLOQUEANTE` → `ADVERTENCIA` → `INFORMATIVA`), luego por antigüedad de la incidencia (la más vieja
primero), luego alfabético. (Q-2.6-08, Q-2.6-09, Q-2.6-11.)

**Cuando no hay alertas.** Si hay al menos una tarea activa, el informe **se genera y se envía
siempre**, aunque las secciones 1 a 3 estén vacías: las secciones 4 y 5 casi nunca lo están, y si lo
estuvieran el cuerpo es un resumen breve de una sola pantalla. El asunto no lleva el prefijo
`[Requiere atención]` en ese caso (§11.5.1). El silencio queda reservado, sin excepciones, al único
caso que el requisito nombra: no hay tareas activas (Q-2.6-12).

### 11.3.5 Frescura de los datos

Una credencial de Canvas inválida o una GitHub App desinstalada **no impiden generar el informe**: se
construye enteramente desde el espejo (Ley 1). `informe_diario.frescura` (`jsonb`) registra, por
fuente, el instante de la última sincronización con éxito y el estado de la credencial o de la
instalación; se renderiza como cabecera del informe, en pantalla y en el correo, con las mismas tres
bandas de color que el componente `SelloAntiguedad` de A-231. La sección 1 encabeza con la reconexión
pendiente cuando corresponde. **Con más de 24 horas sin sincronización con éxito de Canvas, el
informe antepone al contenido una advertencia de datos viejos y omite la sección 5**, porque un
resumen del período sin ingesta del período sería falso (Q-2.6-27).

### 11.3.6 Criterios de aceptación de §11.3

| # | Criterio |
|---|---|
| CA-11.3-01 | Un curso sin ninguna tarea `ACTIVA`/`INCONSISTENTE` y sin repositorios pendientes ni incidencias bloqueantes produce una fila `SIN_TAREAS_ACTIVAS` y **no encola ningún correo** |
| CA-11.3-02 | Una tarea con todos los repositorios `OPERATIVO`, sin incidencias abiertas y con la única entrega ya vencida **no** cuenta como activa, y deja de aparecer en el informe del día siguiente |
| CA-11.3-03 | Con el planificador detenido más de un día del curso, la fila de ese día queda `NO_GENERADO` con `motivo = 'SISTEMA_DETENIDO'`, y el informe siguiente declara la ventana ampliada en su encabezado |
| CA-11.3-04 | Un repositorio con menos días observados que el umbral configurado no aparece como «sin actividad» en la sección 3, y muestra el texto de dato insuficiente |
| CA-11.3-05 | Una incidencia `SIN_PARTICIPACION` silenciada desde Pendientes no aparece en la sección 3 del informe del mismo día, pero sigue visible, plegada, en Pendientes |
| CA-11.3-06 | Revocar la credencial de Canvas operativa no impide que el informe del día siguiente se genere; su cabecera muestra la antigüedad de la sincronización con Canvas en ámbar o rojo según corresponda |
| CA-11.3-07 | Ninguna sección del informe muestra más de 10 elementos nombrados sin colapsar en «y N más» |
| CA-11.3-08 | Un mismo repositorio bloqueado aparece en la sección 1 y, si además el estudiante correspondiente está sin participación, se cuenta —sin nombrarse de nuevo— en la sección 3 |

---

## 11.4 Suscripción y desuscripción individual (R2.6.3)

### 11.4.1 Dónde vive: `/cursos/{id}/mis-notificaciones`

**Cada profesor y cada ayudante controla su propia suscripción**, en una pantalla propia que exige
sólo `curso.ver` —no `curso.administrar`—, de modo que es accesible a todo miembro activo del curso,
profesor o ayudante por igual: es la corrección explícita que A-132 introduce sobre la ubicación
original bajo `/cursos/{id}/ajustes`, pantalla que exige `curso.administrar`, permiso **NO CONCEDIBLE**
a un ayudante. Sin esta corrección, **R2.6.3** —«permitir que profesores **y ayudantes** se suscriban
o den de baja individualmente»— sería inalcanzable para la mitad de sus destinatarios (A-132, regla 0
de A-151).

La pantalla está enlazada desde la navegación del curso y desde el pie de cada informe.
`/cursos/{id}/ajustes` conserva `curso.administrar` y sigue conteniendo credenciales, vinculación y
zona horaria: lo que se mueve es la suscripción, no el permiso.

### 11.4.2 `suscripcion_informe`

`suscripcion_informe (curso_id, usuario_id, activa, origen_baja, dada_de_baja_en, actualizada_en)`,
clave primaria `(curso_id, usuario_id)`. **La suscripción es por curso**, con un interruptor por cada
curso en el que la persona participa; no existe un interruptor global, porque tener a la vez un valor
global y excepciones por curso crearía dos verdades sobre el mismo hecho. Como comodidad —no como
estado nuevo— `/perfil` ofrece una vista agregada de todos los cursos del usuario con dos acciones
masivas, «suscribirme a todos» y «darme de baja de todos», que escriben N filas y quedan en `bitacora`
como cualquier otro cambio (Q-2.6-18).

**Cambiar la propia suscripción no es un permiso** (§2): es una acción sobre uno mismo, y por eso no
aparece en la tabla de los nueve permisos de §2.

### 11.4.3 Alta por defecto y tope de suscriptores

**Opt-out para todos: profesores y ayudantes quedan suscritos por defecto.** Al crear un curso o al
aceptar una invitación de equipo, la fila nace con `activa = true` en la misma transacción que la
membresía. Un sistema entregado en el que por defecto nadie recibe nada haría **R2.6.4** imposible de
comprobar sin configurar antes el sistema. Se informa en el correo de invitación («al aceptar quedarás
suscrito al informe docente diario de este curso, que llega a las 07:00; puedes darte de baja en un
clic») y con un banner en el primer acceso (Q-2.6-19).

**Excepción por cuota:** el informe consume la reserva `INFORME` del correo del despliegue (§14.12),
con **máximo 30 suscriptores activos por curso** (A-228). Si el curso ya tiene 30 activos, la fila
nace con `activa = false` y `origen_baja = 'TOPE_SUSCRIPTORES'`, y la persona ve en su primer acceso
el aviso correspondiente; nunca se supera el tope en silencio.

### 11.4.4 El enlace de baja: token firmado

**El enlace de baja de cada correo del informe usa un token firmado con HMAC-SHA256** sobre
`SIGNING_KEY` (§14.6), verificado en tiempo constante, con
`payload = {curso_id, usuario_id, generacion_enlaces, emitido_en, expira_en, jti}`. **No es un JWT
genérico**: no se acepta ningún algoritmo declarado por el propio token. (RG-131.)

| Regla | Valor |
|---|---|
| Caducidad | **90 días, reutilizable** dentro del plazo. Los enlaces de traza de cada línea (`/r/{t}`) caducan también a 90 días: una sola cifra en toda la especificación |
| Rutas | **`GET /baja/{token}`** (página de confirmación, no modifica nada) y **`POST /baja/{token}`** (da de baja). Re-suscripción: **`POST /baja/{token}?accion=alta`**. Las rutas `/informes/baja/{token}` y `/informes/alta/{token}` **no existen** |
| Revocación en bloque | `usuario.generacion_enlaces` entra en el `payload`; «regenerar mis enlaces de baja» en `/perfil` la incrementa e invalida de golpe todos los tokens anteriores de esa persona |
| CSRF | El endpoint **no está autenticado por cookie**: el doble envío de §2 no aplica; su autorización es la propia firma y el alcance `(curso_id, usuario_id)`. Se aceptan dos entradas de `POST`: el formulario de confirmación del propio origen, y el `POST` de un clic que hace el cliente de correo por `List-Unsubscribe` con `List-Unsubscribe-Post: List-Unsubscribe=One-Click` (RFC 8058), sin token de formulario |
| Alcance | Sólo modifica la suscripción de `(curso_id, usuario_id)` que lleva firmada; no crea sesión y no da acceso a ningún dato del curso. Limitador: 20/min por IP truncada |

**Da de baja sólo del curso de ese informe**, semántica coherente con un correo por curso (§11.5.1):
la página de confirmación lo dice explícitamente («te has dado de baja del informe de *ICC4201*;
sigues suscrito a otros N cursos») y enlaza a la vista agregada de `/perfil`.

### 11.4.5 Autogestión estricta: nadie da de baja a otro

**La suscripción es estrictamente self-service.** No existe ninguna acción «suscribir a todos» ni
«desuscribir a X» en `/cursos/{id}/equipo`, ni con `equipo.administrar`. El profesor **puede ver
quién está suscrito** —columna de sólo lectura, información de coordinación— pero no puede cambiarlo.
La única acción de un profesor sobre la suscripción ajena es indirecta y legítima: retirar a esa
persona del curso, que desactiva su suscripción como efecto en cascada (§11.4.6). Las bajas
automáticas del sistema —retiro de membresía, rebote de correo, tope de suscriptores— no son
excepciones a esta regla: son reglas declaradas y auditables, no «otro usuario dándome de baja»
(Q-2.6-21).

### 11.4.6 Cascada al retirar, al rebotar y al reincorporarse

**Se desactiva, nunca se borra**, y lo ya encolado se cancela antes de salir (Q-2.6-23):

1. **Al retirar a un ayudante o a un profesor**, la misma transacción que pone
   `membresia_curso.estado = RETIRADA` escribe `suscripcion_informe.activa = false`,
   `origen_baja = 'RETIRO_MEMBRESIA'`.
2. **Lo ya encolado no se envía.** `despachar_outbox` revalida, inmediatamente antes de la llamada,
   que el destinatario sigue teniendo membresía `ACTIVA` y suscripción activa (guarda 2 de §11.2.3);
   si no, el mensaje pasa a `SUPRIMIDO` sin consumir cuota.
3. **Rebote duro o queja de spam** del proveedor de correo (§14.12) desactiva **todas** las
   suscripciones de esa persona con `origen_baja = 'REBOTE'`, con banner de reactivación en su
   próximo acceso.
4. **Reincorporación:** la suscripción se restaura a `activa = true` por defecto, **salvo que la
   última baja tuviera `origen_baja = 'USUARIO'`**, en cuyo caso permanece de baja y el banner de
   primer acceso lo explica. Se respeta la decisión propia; las bajas que fueron efecto del sistema sí
   se deshacen, porque su causa desapareció.

### 11.4.7 Criterios de aceptación de §11.4

| # | Criterio |
|---|---|
| CA-11.4-01 | `/cursos/{id}/mis-notificaciones` responde `200` a una sesión de ayudante con sólo los dos permisos implícitos, y `/cursos/{id}/ajustes` le responde `403` |
| CA-11.4-02 | Aceptar una invitación de equipo crea `membresia_curso` y `suscripcion_informe.activa = true` en la misma transacción |
| CA-11.4-03 | Un `GET /baja/{token}` no cambia ningún dato; un `POST /baja/{token}` desactiva la suscripción y un `POST /baja/{token}?accion=alta` posterior la reactiva |
| CA-11.4-04 | Un token con `generacion_enlaces` distinta de la actual del usuario es rechazado, aunque no haya caducado por fecha |
| CA-11.4-05 | No existe ninguna ruta que reciba un `usuario_id` de destino para cambiar la suscripción de otra persona; una prueba automatizada recorre las rutas registradas y lo confirma |
| CA-11.4-06 | Retirar a un ayudante con un correo del informe ya encolado para él hace que ese mensaje termine en `SUPRIMIDO` con `motivo_estado = 'MATRICULA_NO_ACTIVA'`, y el proveedor no lo recibe |
| CA-11.4-07 | Reincorporar a una persona que se dio de baja por sí misma la deja de baja; reincorporar a una que fue retirada por el profesor la deja suscrita |
| CA-11.4-08 | El trigésimo primer intento de suscripción activa en un curso queda con `origen_baja = 'TOPE_SUSCRIPTORES'` y no incrementa el consumo de la reserva `INFORME` |

---

## 11.5 Envío del informe por correo (R2.6.4)

**La infraestructura de correo transaccional —proveedor, DNS, la cuota diaria de 100 correos
repartida en tres reservas 60/20/20, el orden de cesión, la interfaz `ProveedorCorreo` y las pruebas
de entregabilidad— está fijada en §14.12 y no se redefine aquí.** Esta sección especifica el
contenido, la plantilla y la lógica de envío propias del informe, que consume la reserva `INFORME`.

### 11.5.1 Un correo por curso y por suscriptor

**Nunca un correo consolidado con varios cursos, y nunca un informe por tarea.** El documento es uno
por `(curso, fecha)` —la unicidad que ya impone `informe_diario`— con las cinco secciones agrupadas
por tarea dentro de cada una. (Q-2.6-08.)

- **Asunto:** `<código del curso> · Informe docente del <dd-MM-yyyy>`. Con al menos una línea en la
  sección 1, el asunto antepone `[Requiere atención]`. Sin emojis.
- **Orden de las tareas:** por fecha efectiva de cierre más próxima aún no vencida, ascendente; las
  tareas sin cierre futuro, por nombre.
- **Granularidad de la suscripción** (§11.4.2, por curso) es lo que hace posible este reparto: darse
  de baja de un curso no apaga el informe de los demás.

### 11.5.2 Formato del correo

**HTML multipart con alternativa completa en texto plano**, con resumen accionable en el cuerpo y
enlace a la versión web para el detalle largo: el correo tiene que ser útil sin abrir nada. Una sola
columna, ancho máximo 600 px, CSS en línea, sin imágenes remotas, sin fuentes externas, sin
JavaScript; contraste suficiente en modo claro y oscuro.

**Contenido y datos personales:** se incluyen nombres completos de estudiantes y grupos y logins de
GitHub, porque son los datos de trabajo del equipo docente; **no se incluye ninguna dirección de
correo de estudiante**, ni notas, ni motivos de extensión. Tope de 10 elementos nombrados por línea
(§11.3.4).

**Remitente y respuestas** (variables concretas fijadas en §14.12): `From` con el dominio propio,
nunca el correo personal de un integrante; `Reply-To` al buzón de soporte del equipo. Cabeceras
`List-Unsubscribe` y `List-Unsubscribe-Post: List-Unsubscribe=One-Click` construidas con el token de
§11.4.4. Pie fijo con el curso, por qué se recibe, el enlace de baja y el enlace a
`/cursos/{id}/mis-notificaciones`.

### 11.5.3 Enlaces profundos: retorno firmado, nunca la home

**Cada enlace del correo preserva el destino con un parámetro de retorno firmado, validado contra una
lista blanca de rutas propias.** Nunca se aterriza en la home. Cada enlace apunta a
`https://app.<dominio>/r/{t}`, con `t` firmado con `SIGNING_KEY`, conteniendo
`{ruta, informe_id, destinatario_id, jti, exp}` (caducidad 90 días, §11.4.4). `t` **no autentica ni
concede acceso a nada**: sólo transporta el destino. `/r/{t}` valida firma, caducidad y que `ruta`
casa con la lista blanca de rutas propias, registra el clic y responde `302`. Si no hay sesión, el
destino se conserva a través del inicio de sesión con Google (§2).

**Si el destino ya no existe, si la persona perdió el permiso o nunca perteneció al curso: una única
respuesta genérica**, `404`, con el texto «Este contenido ya no está disponible o no tienes acceso».
No se distingue entre los tres casos, para no revelar la existencia del recurso ni la pertenencia de
nadie a un curso. (Q-2.6-16.)

### 11.5.4 Ejecución manual: tres acciones, tres permisos

Existen tres acciones, ninguna reemplaza el documento del día ni rompe la unicidad `(curso_id,
fecha)` (Q-2.6-25):

| # | Acción | Permiso | Efecto |
|---|---|---|---|
| 1 | **Vista previa del informe de hoy** | `curso.ver` | Renderiza con los datos actuales; no persiste y no envía |
| 2 | **Enviarme el informe de hoy** | `curso.ver` | Genera el documento del día si aún no existe (`origen = 'MANUAL'`, `disparado_por_usuario_id`) y lo envía **sólo a quien lo pide**, con tope de 2 reenvíos por persona y día, con cargo a la reserva de margen del correo, no a la del informe |
| 3 | **Generar y enviar ahora a los suscritos** | `curso.administrar` | Genera el documento si no existe y lo envía a todos los suscriptores activos, dentro de la cuota de §14.12 |

**El documento del día es único e inmutable.** Si la fila `(curso, fecha)` ya existe, las acciones 2
y 3 **no la regeneran**: reenvían ese documento, con `generacion` incrementada en la clave de
idempotencia (§11.2.1) para que la reemisión no choque con el envío programado de las 07:00.
**Si no hay tareas activas, ninguna acción envía nada** y la pantalla lo dice con el texto literal del
requisito.

### 11.5.5 Idempotencia y cuota

**Clave de idempotencia del correo:** `hash(CORREO, destinatario, informe_diario_correo,
informe_diario.id, generacion)` (§11.2.1, RG-036). Con `pg_advisory_lock(curso_id)` (A-217) y esta
clave, dos ejecuciones del trabajo el mismo día producen una sola fila y un solo correo por
suscriptor, aunque el trabajador se reinicie o el planificador lata dos veces.

**Cuota:** el informe consume la reserva `INFORME` de la cuota diaria del despliegue (60 sobre 100,
§14.12), y **cede el último** cuando la cuota se agota: se envía a los suscriptores que quepan por
orden de antigüedad de suscripción, y el resto queda `DIFERIDO` con `motivo_estado = 'CUOTA_AGOTADA'`
(§11.2.4). **El informe siempre queda disponible en la aplicación aunque el correo falle**: R2.6.4
pide enviarlo, R2.6.1 pide generarlo, y generarlo y conservarlo aunque el envío falle es lo que
impide perder el requisito por una cuota de un tercero (A-228).

### 11.5.6 Criterios de aceptación de §11.5

| # | Criterio |
|---|---|
| CA-11.5-01 | Un profesor suscrito a dos cursos con tareas activas en ambos recibe **dos** correos distintos, cada uno con su propio código de curso en el asunto |
| CA-11.5-02 | Ejecutar el trabajo `informe_diario` dos veces el mismo día para el mismo curso produce **una** fila `informe_diario` y **un** `mensaje_saliente` por suscriptor, nunca dos |
| CA-11.5-03 | La acción «Enviarme el informe de hoy» ejecutada por un ayudante sin `curso.administrar` responde `200` y no genera envío a nadie más que a él |
| CA-11.5-04 | La acción «Generar y enviar ahora a los suscritos» ejecutada por un ayudante sin `curso.administrar` responde `403` |
| CA-11.5-05 | Un clic en un enlace del correo hacia una tarea ya archivada devuelve la página genérica de «no disponible», nunca un `500` ni un mensaje que revele que la tarea existió |
| CA-11.5-06 | Con la reserva `INFORME` agotada, los correos que no caben quedan `DIFERIDO` con `motivo_estado = 'CUOTA_AGOTADA'`, ninguno se pierde, y el informe sigue visible en `/cursos/{id}/informes/{fecha}` |
| CA-11.5-07 | El correo del informe no contiene, en ninguna parte del HTML ni del texto plano, una dirección de correo de un estudiante |
| CA-11.5-08 | Un reenvío manual del informe de un día anterior produce una fila `mensaje_saliente` con `generacion` mayor que la del envío original, sin chocar con la clave de idempotencia existente |

---

## 11.6 Catálogo de comunicaciones automáticas activables por tarea (R2.6.7)

### 11.6.1 Los siete eventos: catálogo cerrado

**La lista de eventos que generan comunicación automática es la de A-130: siete, cerrada, y no se
amplía ni se hace extensible por configuración.** Cada uno declara su alcance, su disparador exacto,
su canal, su valor por defecto y su tope, siempre por persona.

| Evento | Alcance | Cuándo se dispara | Canal | Por defecto | Tope (siempre por persona) |
|---|---|---|---|---|---|
| `repositorio_disponible` | Tarea | El acceso de ese estudiante pasa a `INVITADO` o `ACCESO_DIRECTO` (§11.6.2) | Canal activo (§11.9) | Activado | 1 por `(tarea, sujeto, estudiante)` |
| `invitacion_aceptada` | Tarea | Webhook `member`/`added` | Canal activo | Activado | 1 por `acceso_repositorio` |
| `recordatorio_mapeo` | **Curso** (`tarea_id` nulo) | 09:00 en la zona del curso, a quien falte cuenta de GitHub | Canal activo | Activado | Máx. 3 por estudiante y **curso** en total, nunca dos días seguidos |
| `recordatorio_invitacion` | Tarea | 48 h tras invitar sin aceptar | Canal activo | Activado | Máx. 3 por `(repositorio, estudiante)`, separados ≥ 24 h |
| `proximidad_cierre` | Tarea | 48 h y 6 h antes de la fecha efectiva de cada entrega | Canal activo | Activado | 1 por `(entrega, estudiante, ventana, fecha objetivo)` |
| `cambio_de_fecha` | Tarea | El sincronizador detecta un cambio de fecha (§11.8.2) | Anuncio, con `specific_sections` si procede | Activado | 1 por cambio (fila de `cambio_fecha`) |
| `correccion_publicada` | Tarea | Se crea la fila de `publicacion_nota` de esa persona | Canal activo | **Desactivado** | 1 por `(publicacion_nota, estudiante)` |

**El evento `repositorio_disponible` nunca caduca y no puede quedar suspendido por decisión de un
interruptor de forma permanente sin consecuencia visible**, porque su contenido es literalmente
**R2.3.12**: si el profesor lo apaga, la pantalla lo advierte —«los estudiantes de esta tarea no
recibirán la dirección de su repositorio; tendrás que dársela tú»— y la tarjeta de la tarea lleva la
marca permanente «avisos de repositorio desactivados» (Q-2.6-29).

### 11.6.2 Disparadores exactos, evento por evento

- **`repositorio_disponible` e `invitacion_aceptada`** cuelgan del **acceso de la persona**, no del
  estado del repositorio: A-127 lo fija así a propósito, porque colgarlo de que el repositorio llegue
  a `OPERATIVO` dejaba sin mensaje al integrante cuyo mapeo llega tarde —el caso central de
  **R2.3.10**—. Dos plantillas distintas según la respuesta de GitHub fue `201` (invitación pendiente)
  o `204` (acceso inmediato); la primera advierte que hasta aceptar la invitación la URL mostrará
  «no encontrado», porque GitHub responde `404` en repositorios privados (§8, `Q-2.3-35`).
- **`recordatorio_invitacion`** no reenvía la invitación de GitHub salvo que esté caducada, y
  comprueba antes, en orden: si ya aceptó (no se envía nada, se corrige el estado), si la invitación
  sigue viva (sólo se avisa por Canvas), y sólo si expiró se reemite con `DELETE` + `PUT` (§8, A-100).
- **`recordatorio_mapeo`** se suspende automáticamente 24 horas después de publicada la tarea de
  registro, y deja de enviarse en cuanto el mapeo queda `VIGENTE`, se agotan los tres envíos, vence
  la tarea de registro, el estudiante deja de estar activo, o hay una supresión vigente (§11.2.6).
  Después de agotado, el estudiante no desaparece: queda en Pendientes con la acción manual
  «enviar recordatorio», sin tope automático porque la dispara una persona.
- **`proximidad_cierre`** se calcula **siempre sobre la fecha efectiva por sujeto**, nunca sobre la
  fecha base: dos estudiantes de la misma entrega reciben el recordatorio en momentos distintos si
  sus cierres son distintos, que es la lectura fiel de **R2.4.3**. No se omite si el sujeto ya tiene
  commits recientes: es información de calendario, no un juicio sobre el trabajo (§11.6.5,
  Q-2.6-33).
- **`correccion_publicada`** se encola **al crear** la fila de `publicacion_nota` de esa persona —
  después de que §12 verificó la nota contra Canvas—, nunca al pulsar «publicar»: así el mensaje y
  Canvas nunca pueden decir cosas distintas. En tarea grupal es siempre un mensaje por persona, con
  su propia nota, nunca un hilo grupal (§11.7.2).

### 11.6.3 Interruptores: alcance, valores por defecto y permiso

**Seis eventos de alcance TAREA se activan dentro de cada tarea** —literalmente lo que pide
**R2.6.7**—; **`recordatorio_mapeo`, de alcance CURSO, se activa en `/cursos/{id}/personas`**.
Ninguna fila se precrea al crear la tarea: la ausencia de fila significa «valor por defecto», y la
fila se materializa la primera vez que alguien la toca, con `actualizada_por` y `actualizada_en`.
**No existe herencia desde una plantilla de curso** para los eventos de tarea, ni granularidad por
entrega: el `CHECK` en base limita `alcance = 'CURSO'` a `recordatorio_mapeo` en exclusiva. (Q-2.6-29.)

Permiso: **`comunicacion.enviar`** (§2), el mismo que gobierna los mensajes manuales y los anuncios
manuales. Un ayudante sin el permiso ve el bloque «Comunicaciones» en modo lectura, con los
interruptores deshabilitados y el motivo escrito, nunca ocultos.

**Previsualización obligatoria antes de encender o apagar cualquier interruptor** (A-130): la
pantalla muestra el canal por el que saldrá, el texto renderizado con un destinatario real, el
recuento exacto de personas a las que llegaría hoy y el tope aplicable.

### 11.6.4 Efecto de desactivar y reactivar

**Al desactivar,** en la misma transacción que escribe `regla_comunicacion.activa = false`, todo
`mensaje_saliente` de ese `(curso, tarea, evento)` en un estado no terminal pasa a `CANCELADO` con
`motivo_estado = 'REGLA_DESACTIVADA'` (§11.2.4). Lo que está `EN_CURSO` se deja terminar: un `UPDATE`
no puede retirar una llamada ya en vuelo. El outbox **nunca reintenta un mensaje cuya regla está
desactivada**, porque la guarda 4 (§11.2.3) se comprueba dentro del trabajo, inmediatamente antes de
cada intento.

**Al reactivar, se recalcula, no se vacía la cola acumulada.** El trabajo `comunicaciones_programadas`
recalcula desde cero el conjunto de mensajes que corresponden ahora: un `proximidad_cierre` cuya
fecha objetivo sigue en el futuro se reprograma con su clave (§11.6.5); uno cuya ventana ya pasó **no**
se reprograma; y `repositorio_disponible` de quienes fueron invitados mientras el interruptor estaba
apagado **sí se envía**, porque es un hecho que sigue siendo verdad y **R2.3.12** no admite que un
interruptor apagado por unos días deje a media clase sin la información de acceso a su repositorio.
(Q-2.6-58.)

**Toda auditoría incluye el efecto en número, no sólo el cambio de booleano:** `bitacora` registra
`{"cancelados": N, "en_curso": M}` al apagar y `{"programados": N, "descartados_por_fecha": M}` al
encender, junto al actor y la fecha.

### 11.6.5 Tope transversal, fusión de plantillas y ventana horaria

**Tope duro: 3 mensajes automáticos por estudiante y día del curso**, contando todos los tipos y
todas las tareas. Al superarlo, el mensaje pasa a `DIFERIDO_POR_TOPE` y se reevalúa al día siguiente,
según una tabla fija de prioridad —arriba lo que caduca hoy (`proximidad_cierre` H6), en medio lo que
desbloquea al estudiante (`repositorio_disponible`), abajo lo que puede esperar
(`recordatorio_mapeo`)—. `repositorio_disponible` no cede nunca por caducidad (§11.2.4), sólo por
orden de prioridad si el día está lleno, y al día siguiente sale igual.

**Fusión, antes que diferir:** cuando `repositorio_disponible` y `proximidad_cierre` coinciden para la
misma persona en el mismo ciclo de evaluación, se emite **un solo mensaje** con una plantilla que dice
las dos cosas, no dos mensajes separados. Los dos interruptores se respetan por separado: si uno está
apagado, sale la plantilla simple del otro.

**Ventana horaria: 08:00 a 21:00 en la zona del curso**, fija y no configurable, para los eventos que
pueden esperar. Fuera de ella, `programado_para` se adelanta a las 08:00 del día siguiente del curso.
**`proximidad_cierre` con ventana H6 no espera**: sale a la hora exacta, porque su `caduca_en` es el
propio cierre. Los mensajes manuales tampoco esperan: los escribe una persona que sabe qué hora es.
(Q-2.6-40, Q-2.6-41.)

### 11.6.6 Qué queda fuera de este catálogo: los avisos de revocación de acceso

**El aviso al estudiante que sale de un grupo no es un evento de este catálogo.** Cuando la salida de
un integrante de un grupo con repositorio ya creado propone y —tras la decisión de un docente—
ejecuta la revocación de su acceso, la transacción de revocación envía **`aviso_revocacion_acceso`**
al proponerse y **`confirmacion_revocacion_acceso`** al ejecutarse: son notificaciones **obligatorias**
de esa transacción, sin interruptor, sin tope y sin fila en `regla_comunicacion`, porque «un aviso que
se puede apagar no puede ser parte obligatoria de una transacción que retira un acceso» (A-212,
RG-009, RG-010). Ese mecanismo —motivos, plazos de gracia, séptima eliminación externa— se especifica
en el capítulo de acceso a repositorios y no se redefine aquí. **La entrada de un integrante nuevo a
un grupo con repositorio ya creado sí usa este catálogo**: es exactamente el disparador de
`repositorio_disponible` de §11.6.2, sin ninguna regla adicional, con el texto completo —nunca una
versión abreviada, porque es la primera vez que esa persona ve ese repositorio.

### 11.6.7 Criterios de aceptación de §11.6

| # | Criterio |
|---|---|
| CA-11.6-01 | El `CHECK` de `regla_comunicacion.evento` contiene exactamente los siete valores de §11.6.1; un `INSERT` con un octavo valor es rechazado |
| CA-11.6-02 | Un `INSERT` de `regla_comunicacion` con `alcance = 'CURSO'` y `evento <> 'recordatorio_mapeo'` es rechazado por el `CHECK` |
| CA-11.6-03 | Invitar a un integrante que llega tarde a un grupo de cuatro produce **cuatro** mensajes `repositorio_disponible` en total, uno por integrante, cada uno en el momento en que se le invita, nunca uno solo «al grupo» |
| CA-11.6-04 | Apagar `repositorio_disponible` en una tarea muestra el diálogo de advertencia y dos días después ningún estudiante invitado en ese período recibió el mensaje |
| CA-11.6-05 | Reactivar ese mismo interruptor dos días después envía `repositorio_disponible` a todos los que fueron invitados mientras estuvo apagado |
| CA-11.6-06 | Un estudiante que recibiría un `repositorio_disponible` y un `proximidad_cierre` H48 el mismo ciclo recibe **un** mensaje fusionado, no dos |
| CA-11.6-07 | Un estudiante que ya recibió 3 mensajes automáticos ese día no recibe un cuarto aunque se cumpla el disparador de un evento adicional; ese mensaje queda `DIFERIDO_POR_TOPE` |
| CA-11.6-08 | El aprovisionamiento de un repositorio a las 03:00 no produce ningún mensaje a estudiantes antes de las 08:00 hora del curso |
| CA-11.6-09 | Retirar a un integrante de un grupo con repositorio produce `aviso_revocacion_acceso`, **no** una fila en `mensaje_saliente.evento = 'salida_de_grupo'`, que no existe en el `CHECK` |

---

## 11.7 Mensajes directos a estudiantes (R2.6.5)

### 11.7.1 Redacción libre dentro de un marco fijo

**El equipo docente puede redactar y enviar un mensaje directo a un estudiante o a un grupo desde la
aplicación**, con cuerpo de texto libre dentro de un marco fijo que la aplicación genera: encabezado
con el curso y, cuando aplica, la tarea, la entrega y el repositorio; cuerpo libre, con un desplegable
de plantillas del catálogo como punto de partida —«consulta de actividad», «problema con la
invitación», «cuenta de GitHub incorrecta», «aviso de corrección»—, editable desde ahí o escrito desde
cero; pie de mensaje con el contacto docente y, a diferencia de los automáticos, **quién lo escribió**
(«Escrito por *nombre*, equipo docente de *código*»). Límite propio de 4.000 caracteres —la
documentación no publica ningún límite para `body`—, texto plano, URL completas en su propia línea.
Permiso: `comunicacion.enviar` (§2). (Q-2.6-36.)

**Va por el outbox como cualquier otra comunicación** (A-125): la pantalla dice «se enviarán N
mensajes; puedes seguir el estado aquí» y nunca llama a Canvas dentro de la petición HTTP. Un mensaje
enviado no se puede retirar (§11.2.1, retractación sólo existe para el canal de anuncio, §11.8.8); la
pantalla lo advierte antes de confirmar.

### 11.7.2 Destinatarios: siempre personas, expansión de grupos

**Siempre conversaciones individuales privadas, `group_conversation=false`, también para los mensajes
manuales y también cuando el destinatario lógico es un grupo.** Un grupo no tiene bandeja de entrada:
la aplicación **expande el grupo a sus integrantes `accepted`** y envía un mensaje por persona, con la
misma clave de idempotencia por persona de A-125. Un hilo grupal haría que los integrantes se vieran
entre sí y respondieran a todos, y convertiría cualquier aviso sobre el trabajo del grupo en una
conversación pública con el equipo docente dentro; una sola regla en todo el sistema —siempre por
persona— es más defendible que una excepción para el canal manual. (Q-2.6-37, A-130 regla 1.)

**Redacción:** con sujeto individual, «tu repositorio»; con sujeto grupal, «el repositorio de tu grupo
*nombre*» —nunca «vuestro repositorio» sin nombrar el grupo, porque un estudiante puede pertenecer a
grupos distintos en tareas distintas—.

### 11.7.3 Qué no se nombra: privacidad entre pares

**Ningún mensaje a un estudiante nombra a otro estudiante ni describe su situación**, ni siquiera
dentro del mismo grupo, y **no es configurable por el profesor**. Lo que sí se dice es el conteo y la
consecuencia: «falta 1 integrante por registrar su cuenta de GitHub y otro por aceptar la invitación;
cuando lo hagan, entrarán automáticamente». Las plantillas dirigidas a un estudiante no admiten
ninguna variable que resuelva a una persona distinta del destinatario (catálogo cerrado de §11.2.5), y
una prueba de arquitectura falla la construcción si una plantilla de canal a estudiante referencia a
un tercero. **Las extensiones individuales se comunican por su fecha, nunca por su origen**: el
mensaje de `proximidad_cierre` dice «tu fecha de cierre es *fecha*», nunca de qué regla proviene —el
campo `fecha_efectiva.origen` es información exclusiva del equipo docente—. La salida legítima para lo
que un docente sí quiera decir con nombres es el mensaje manual (§11.7.1), firmado con su nombre y
registrado en `bitacora`: lo que una persona puede decidir caso a caso no debe automatizarlo un
trabajo periódico dirigido a doscientas personas. (Q-2.6-38.)

### 11.7.4 Asunto y conversación por evento

**Una conversación nueva por evento**, con asunto fijo por plantilla, prefijado con el código del
curso —`[<curso.codigo>] <texto de la plantilla>`— y limitado a 255 caracteres. **El asunto nunca
lleva información que no esté también en el cuerpo**: cada plantilla empieza repitiendo su asunto en
la primera línea del cuerpo, porque la documentación admite que el asunto **se ignora al reutilizar
una conversación existente**. En el canal 2 (comentario en la entrega de la tarea de registro, §11.9)
no hay asunto; el texto empieza igual por la línea de título. (Q-2.6-39.)

### 11.7.5 Filtro de destinatarios por matrícula

**No se envían comunicaciones automáticas a matrículas que no estén `active` o `invited`.** El filtro
es la guarda 2 de §11.2.3, y depende del tipo de mensaje: `invited` sí recibe `repositorio_disponible`
e `invitacion_aceptada` —A-164 lo materializa como sujeto con repositorio, y quien tiene repositorio
tiene derecho a saber dónde está, que es literalmente **R2.3.12**—, pero **no** recibe recordatorios
de fecha o de mapeo, porque avisarle de algo que aún no ve es ruido. `deleted` nunca, sin excepción.
El **mensaje manual** puede dirigirse a `inactive` o `completed` con confirmación nominal explícita
—«tu nota de la parcial quedó publicada aunque ya no estés en el curso» es exactamente el caso de
**R2.6.5**—, pero nunca a `deleted`. Toda exclusión se registra como fila `SUPRIMIDO`, nunca en
silencio (§11.2.4). (Q-2.6-56, A-129.)

### 11.7.6 Ritmo: ventana horaria y concurrencia

La ventana de 08:00 a 21:00 en la zona del curso (§11.6.5) aplica igual a los mensajes automáticos de
este catálogo; los mensajes manuales no esperan. **Envío secuencial, un destinatario por llamada**,
con la concurrencia 1 por curso contra Canvas (A-039, A-217): nunca `recipients[]=course_X` ni
`bulk_message`, porque **R2.3.12** exige entregar a cada estudiante la información de **su**
repositorio, irrepresentable en un mensaje de contexto.

### 11.7.7 Dónde responde el estudiante

**La aplicación no lee `Conversations` ni ningún otro buzón de Canvas, nunca**: no está en la lista
cerrada de consultas en vivo de A-089, y una prueba de arquitectura falla la construcción si aparece
esa lectura. En consecuencia, las respuestas de los estudiantes caen en la bandeja personal de Canvas
del titular de la credencial operativa (§2), y eso se declara en tres sitios: en el consentimiento
previo a guardar una credencial; en el pie de cada plantilla («si tienes dudas, responde a este
mensaje en Canvas: llegará a *nombre del titular*, profesor del curso»; en un mensaje manual escrito
por un ayudante, «tu respuesta llegará a *titular*, no a *ayudante*»); y en la pantalla de
credenciales, que desglosa por canal cuántas escrituras se hicieron con la credencial de cada titular
en los últimos 7 días. Ninguna de estas comunicaciones consume la cuota de correo de §14.12, que es de
correo electrónico propio. (Q-2.6-43.)

### 11.7.8 Criterios de aceptación de §11.7

| # | Criterio |
|---|---|
| CA-11.7-01 | Enviar un mensaje manual a un grupo de tres produce **tres** filas de `mensaje_saliente`, una por integrante `accepted`, y ninguna con `group_conversation=true` |
| CA-11.7-02 | Ninguna plantilla dirigida a un estudiante contiene una variable que resuelva a otra persona; la prueba de arquitectura sobre el archivo de plantillas lo confirma |
| CA-11.7-03 | El cuerpo de un mensaje de `proximidad_cierre` a un estudiante con extensión individual muestra su fecha pero no la palabra «extensión», «excepción» ni el origen de la regla |
| CA-11.7-04 | El asunto de una conversación automática nunca supera 255 caracteres, y su texto completo aparece también como primera línea del cuerpo |
| CA-11.7-05 | Un estudiante con matrícula `invited` recibe `repositorio_disponible` al ser invitado a su repositorio, y no recibe `proximidad_cierre` mientras siga `invited` |
| CA-11.7-06 | Un estudiante con matrícula `deleted` no recibe ningún mensaje, automático o manual, aunque un docente lo intente explícitamente: la interfaz lo impide |
| CA-11.7-07 | Un lote de 50 mensajes a una tarea grande sale con una sola petición en vuelo a Canvas en cada instante, verificable en `/operacion` |
| CA-11.7-08 | El texto de consentimiento de la credencial operativa incluye la frase sobre dónde llegan las respuestas de los estudiantes, y no se puede guardar la credencial sin haberlo mostrado |

---

## 11.8 Anuncios en Canvas (R2.6.6)

### 11.8.1 Automáticos y manuales; borrador en la aplicación, nunca `published=false`

**Los anuncios automáticos (`cambio_de_fecha`) se publican sin revisión previa** —el interruptor de la
tarea **es** la aprobación exigida por **R2.6.7**—; **los anuncios manuales se redactan y previsualizan
en la aplicación**, se guardan como borrador propio (`mensaje_saliente.estado` con la máquina de
§11.2.2) y sólo salen al confirmar, con opción de publicación inmediata o programada. **Nunca se usa
`published=false` en Canvas para simular un borrador**: la documentación no promete que esa
combinación con `is_announcement=true` no notifique a los estudiantes, y un «borrador» que en
realidad avisara a doscientas personas sería el peor fallo posible de este módulo. El borrador vive
**en la aplicación**: se puede editar, previsualizar, descartar o publicar, admite varios revisores del
equipo docente y queda en `bitacora` con autor y fecha. (Q-2.6-44.)

**Publicación programada:** `delayed_post_at`, parámetro documentado, se envía en el momento de
confirmar —la espera la hace Canvas, no la aplicación—.

### 11.8.2 Ámbito: curso, sección o mensaje individual

**El ámbito del anuncio lo determina el ámbito real del cambio de fecha**, no el campo que el
profesor tocó, calculado sobre el conjunto de sujetos cuya `fecha_efectiva` **realmente cambió**,
cruzado con el `origen` de la regla que ganó (`BASE | SECCION | GRUPO | ADHOC`, A-055). (Q-2.6-45.)

| Ámbito del cambio | Qué se comunica | Canal |
|---|---|---|
| Fecha base, o afecta a todas las secciones | Anuncio a todo el curso | `POST /discussion_topics`, sin `specific_sections` |
| Override de sección | Anuncio dirigido a esa sección | `specific_sections` (§11.8.7 para el plan alternativo) |
| Override de grupo | **Ningún anuncio.** Mensaje directo individual a cada integrante `accepted` | Canal activo (§11.9), «la fecha de cierre del grupo *nombre* ha cambiado», sin decir de dónde viene el cambio (§11.7.3) |
| Override ADHOC (uno o varios estudiantes) | **Ningún anuncio, nunca.** Mensaje directo sólo a los alcanzados | Igual, «tu fecha de cierre ha cambiado» |

**Más de tres secciones afectadas en la misma ventana se consolidan en un solo anuncio de curso** con
la tabla de fechas por sección, en vez de publicar tres o más anuncios seguidos. Un estudiante
alcanzado por un override individual no recibe además el anuncio de sección si su propia fecha no
cambió; el anuncio de sección incluye la línea «si tienes una fecha distinta acordada con el equipo
docente, se mantiene la tuya».

### 11.8.3 Umbral y *debounce*: no todo cambio dispara un anuncio

**Umbral de 60 minutos sobre la fecha efectiva:** se anuncia si al menos un sujeto ve moverse su fecha
efectiva más de 60 minutos; los cambios de una hora o menos se aplican íntegramente —se reprograma la
captura y los recordatorios— pero **no se anuncian**, porque un anuncio por un ajuste de cuarenta
minutos devalúa los que sí importan. **`lock_at` y `unlock_at` no disparan anuncio**, porque no mueven
la fecha que gobierna la captura (A-055, A-101); si tras el cambio `lock_at` queda antes del `due_at`
efectivo de algún sujeto, se abre la incidencia `DISCREPANCIA_FECHAS` para el docente, sin anunciar
nada al estudiante. (Q-2.6-46.)

***Debounce* de 20 minutos, con la fecha final.** Al detectarse un cambio anunciable se abre —o se
reutiliza— la fila `cambio_fecha` (§11.2.7) de esa entrega con `ventana_cierra_en = ahora + 20 min`.
Toda detección posterior dentro de la ventana actualiza la huella y las fechas sin emitir nada y sin
ampliar la ventana. Al vencer, si el resultado neto ya no supera el umbral —el profesor deshizo su
cambio—, no se anuncia nada.

**Un cambio sobre una entrega ya cerrada con versión capturada sí se anuncia**, y el texto dice qué
pasó con la versión: si la fecha se adelanta, la captura anterior queda no vigente y se recaptura; si
se retrasa, se programa una nueva y ambas quedan visibles (§10, **R2.4.7**).

### 11.8.4 Contenido fijo del anuncio automático

**Plantilla `cambio_de_fecha_anuncio`, en HTML mínimo, no editable.** Título
`Cambio de fecha — <tarea> · <entrega>`, truncado a 120 caracteres. Cuerpo en orden fijo: qué entrega
y qué tarea; fecha anterior → fecha nueva, ambas en hora del curso con la zona escrita; a quién aplica
(todo el curso, o la sección, o la lista si son varias); la línea de salvaguarda sobre fechas
particulares; si corresponde, la línea sobre qué pasó con la versión ya registrada; enlace a la tarea
en Canvas; el pie de mensaje automático (§11.7.7). **No lleva nombres de estudiantes, ni el origen de
la regla de fecha, ni el motivo del cambio** —la aplicación no lo conoce y no se inventa lo que no
sabe—. La no editabilidad es deliberada: un anuncio automático editable plantea la pregunta de qué se
publica cuando el cambio llega a las 3 de la madrugada y nadie editó nada. Quien quiera matizar el
mensaje dispone del anuncio manual. (Q-2.6-47.)

### 11.8.5 Anuncios manuales

**El equipo docente puede redactar anuncios libres**, asociados a una tarea o al curso, con título y
cuerpo en HTML mínimo (mismas cinco etiquetas de A-126), selección de secciones con recuento de
destinatarios antes de confirmar, y publicación inmediata o programada. Permiso: `comunicacion.enviar`.
**Este es el camino que publica el anuncio de curso al inicio de cada tarea que A-127 exige**
—explicando el flujo completo de invitación a GitHub y avisando de que es legítima—, con una plantilla
precargada y editable. Un anuncio manual **no tiene interruptor** y no cuenta para el tope transversal
de §11.6.5: es una acción del docente, no una comunicación automática. (Q-2.6-48.)

### 11.8.6 Idempotencia del anuncio de cambio de fecha

**La clave se ancla en `cambio_fecha.id`, no en el par de huellas de fecha.** Una secuencia de cambio
A→B→A→B produce **dos** anuncios distintos, porque corresponde a dos filas de `cambio_fecha`
distintas; una clave basada sólo en `(fecha anterior, fecha nueva)` suprimiría el segundo A→B y
dejaría el tablón con una fecha vieja. Un reinicio del trabajador dentro de la misma ventana de
*debounce* no duplica, porque la fila abierta es la misma. Se guarda `discussion_topic_id` y el
enlace a Canvas en el historial (§11.10). (Q-2.6-49.)

### 11.8.7 `specific_sections`: verificación previa y plan B automático

**Se verifica empíricamente antes de operar con secciones**, como parte del ítem 5 del checklist de
vinculación (§2, §5), desdoblado en 5.a (permiso) y 5.b (llamada real con y sin `specific_sections`),
porque un permiso en verde no garantiza que la llamada funcione. El resultado se persiste en
`curso.via_anuncio_seccion ∈ {SECCION, CURSO, NINGUNA, NO_VERIFICADO}`:

- **`SECCION`** — los anuncios de sección usan `specific_sections` normalmente.
- **`CURSO`** — **plan B automático**: todo anuncio que debería ir a una sección se publica a todo el
  curso, con la primera línea del cuerpo diciendo «Esto afecta a la sección *nombre*». Publicar a
  todo el curso declarando a quién afecta es mejor que no publicar, porque las secciones son
  agrupaciones públicas del curso —a diferencia de las extensiones individuales, que §11.8.2 ya
  excluye del canal de anuncios—.
- **`NINGUNA`** — **R2.6.6 no puede cumplirse en ese curso**: el interruptor de `cambio_de_fecha`
  queda deshabilitado con el motivo, la pestaña de anuncios queda en modo lectura, y se declara en la
  cabecera del curso y en la memoria de entrega. No se finge que sí.

**Degradación en caliente:** si en tiempo de ejecución una publicación con `specific_sections` falla,
el despachador reintenta una sola vez sin ella, con el cuerpo del plan B; si también falla, la fila
queda `REQUIERE_ATENCION` con el error literal. El plan B es **automático**, no una acción manual,
porque el evento que más lo necesita —el cambio de fecha— es urgente. (Q-2.6-50.)

### 11.8.8 Ciclo de vida: comentarios, edición y retractación

**Los anuncios de la aplicación nacen cerrados a comentarios** por defecto —`locked=true`—,
respetando siempre la configuración de comentarios del propio curso de Canvas si el profesor la
cambió allí; existe un interruptor de curso, por defecto apagado, para admitirlos. **Antes de
publicarse, un anuncio se edita y se cancela sin tocar Canvas** —la fila está en un estado no
terminal—. **Después de publicado, no se edita**: una corrección se publica como anuncio nuevo que
cita y enlaza al anterior (Ley 2), nunca reescribiendo el que ya notificó a la clase. **Retractación,
por canal, sin fingir simetría**: un anuncio de curso sí se puede retirar con `DELETE
/discussion_topics/:id` (requiere el mismo permiso de moderación del checklist), y la fila pasa a
`RETRACTADO`, no se borra; un comentario de entrega, una conversación o un correo **no** se pueden
retirar desde la aplicación —se declara así **antes** de enviar, no después—. Todo envío manual por
un canal sin retractación, o que alcance a más de 10 personas o sea un anuncio de curso, exige
confirmación reforzada: teclear el número de destinatarios. (Q-2.6-51.)

### 11.8.9 Criterios de aceptación de §11.8

| # | Criterio |
|---|---|
| CA-11.8-01 | Ninguna llamada del sistema a `POST /discussion_topics` incluye `published=false`; una prueba de arquitectura lo confirma |
| CA-11.8-02 | Un cambio de 40 minutos en la fecha efectiva de una entrega reprograma la captura y los recordatorios, y **no** produce ninguna fila en `mensaje_saliente` con `canal = 'CANVAS_ANUNCIO'` |
| CA-11.8-03 | Tres ediciones de la misma fecha dentro de 15 minutos producen **un** anuncio, con la fecha final |
| CA-11.8-04 | Un override de grupo que mueve la fecha de un grupo produce mensajes individuales a sus integrantes `accepted` y **cero** anuncios |
| CA-11.8-05 | Con `curso.via_anuncio_seccion = 'CURSO'`, un anuncio dirigido a una sección se publica a todo el curso con la línea «Esto afecta a la sección…» en primer lugar |
| CA-11.8-06 | Publicar un anuncio de cambio de fecha dos veces por la misma secuencia A→B→A→B (con reversión intermedia) produce **dos** filas en el historial, no una suprimida por la clave |
| CA-11.8-07 | Editar el título o el cuerpo de un anuncio ya publicado no está disponible en la interfaz; la única acción es «publicar corrección», que crea un anuncio nuevo enlazado al anterior |
| CA-11.8-08 | Un anuncio manual a más de 10 destinatarios exige teclear el número exacto antes de habilitar el botón de confirmar |

---

## 11.9 El canal de comunicación con el estudiante y su degradación

**Esta sección no redefine `curso.canal_comunicacion_activo` ni la cascada de A-127: los usa tal
como están fijados en §7.2.3 y explica su efecto sobre las comunicaciones de este capítulo.** El
canal con el estudiante se degrada en orden: **canal 1**, mensaje directo por `Conversations`;
**canal 2**, comentario en la entrega de la tarea de registro; **canal 3**, bloqueo declarado. La
conmutación es automática, según el mapa de capacidades del checklist (§5): si `ENVIAR_MENSAJE` cae,
`despachar_outbox` conmuta al canal 2 y registra el resultado en `mensaje_saliente.canal_efectivo`; si
también cae `COMENTAR_ENTREGA`, el mensaje queda `BLOQUEADO` con reevaluación cada 30 minutos y
**`curso.canal_comunicacion_activo` pasa a `BLOQUEADO`**, hecho declarado en la cabecera del curso y
recordado en la sección 1 del informe diario mientras no vuelva a ser el canal 1 (§11.3.4).

**Con el canal `BLOQUEADO`, los avisos obligatorios de otros capítulos se comportan así, y este
capítulo sólo lo cita:**

| Aviso | Qué ocurre |
|---|---|
| Aviso previo de archivado de una tarea | La acción de archivar queda bloqueada mientras el canal esté `BLOQUEADO`; un profesor con `curso.administrar` puede archivar igualmente con confirmación escrita que declara a cuántos estudiantes no se pudo avisar (§8) |
| Aviso de revocación de acceso (§11.6.6) | El mensaje no sale; la propuesta de revocación no se puede aprobar hasta que conste el aviso o el profesor declare por escrito que avisó por otra vía |
| Invitación al repositorio y guía de acceso (**R2.3.12**) | El aprovisionamiento **continúa**; la tarea muestra una banda con el número de estudiantes que no han recibido las instrucciones, con texto exportable |
| `correccion_publicada` | Se queda en el outbox y sale sola cuando el canal se recupera; no se pierde y no se duplica, por la idempotencia total de §11.2.1 |

**Ningún aviso obligatorio se da por enviado cuando no salió, y ninguna acción irreversible se ejecuta
apoyándose en un aviso que no salió.**

---

## 11.10 Trazabilidad: la bandeja de comunicaciones

**Un único historial para las cuatro clases de comunicación**, construido sobre `mensaje_saliente**
(§11.2.1): no hay un log paralelo. Se lee con `curso.ver` —incluido el cuerpo exacto, porque es un
mensaje que el propio equipo docente ya envió a su estudiante—; actuar exige `comunicacion.enviar`.
(Q-2.6-52.)

**Pantallas:**

| Pantalla | Filtrado por | Contenido |
|---|---|---|
| `/cursos/{id}/comunicaciones` | curso completo | Tabla con filtros por canal, evento, estado, fecha, destinatario y origen; fila expandible con el cuerpo exacto |
| Pestaña «Comunicaciones» de `/cursos/{id}/tareas/{id}` | `tarea_id` | Los envíos de esa tarea, junto a los interruptores del catálogo (§11.6.3) |
| Bloque en la ficha del estudiante, en `/cursos/{id}/personas` | `estudiante_id` | Responde en una revisión «¿supo este estudiante dónde estaba su repositorio?» — la evidencia demostrable de **R2.3.12** |
| Capa en el timeline del repositorio (§10) | `repositorio_id` | Los envíos de ese repositorio junto a los commits y las marcas de entrega |
| `/operacion` | despliegue / curso del solicitante | Cola cruda por estado, consumo de cuota por reserva (§14.12), último error literal |

**Acciones:** «Abrir en Canvas» (enlace construido desde `canvas_id_resultante`, sin ninguna llamada;
si es nulo por fallo, se pinta el motivo, no un enlace roto); «Reintentar» (sólo `FALLIDO` o
`CADUCADO`, reencola la misma fila y la misma clave); «Reenviar» (sólo `ENVIADO`, crea fila nueva con
`generacion` incrementada y `reemplaza_a_id`, tope de 3 reenvíos por fila original, confirmación
reforzada); «Cancelar» (estados no terminales); y el envío manual desde donde se ve el problema
—«Recordar cuenta de GitHub» en la tabla de repositorios, «Avisar a este estudiante» en su ficha—, que
entra al outbox como cualquier otro con `origen = 'MANUAL'`.

**Criterio de aceptación demostrable, que es el propósito de esta sección:** abrir la ficha de un
estudiante y ver la línea «Repositorio disponible · enviado el 16-09-2026 11:04 (America/Santiago) ·
Canvas, conversación · a nombre de *titular de la credencial*», con el cuerpo exacto que recibió y un
enlace que abre esa conversación en Canvas. Eso es **R2.3.12** demostrado, no afirmado.

### Criterios de aceptación de §11.10

| # | Criterio |
|---|---|
| CA-11.10-01 | `/cursos/{id}/comunicaciones` responde `403` a una sesión sin `curso.ver` para ese curso, y `200` para cualquier miembro activo, profesor o ayudante |
| CA-11.10-02 | Un `POST .../reintentar` sobre una fila `ENVIADO` responde `409`; sobre una fila `FALLIDO` la reencola con la misma `clave_idempotencia` |
| CA-11.10-03 | Un `POST .../reenviar` sobre una fila `ENVIADO` crea una fila nueva con `generacion` mayor y `reemplaza_a_id` apuntando a la original |
| CA-11.10-04 | Una consulta a la capa de comunicaciones del timeline de un repositorio no realiza ninguna llamada a Canvas ni a GitHub |
| CA-11.10-05 | Una fila con `canvas_id_resultante` nulo no pinta ningún enlace «Abrir en Canvas»; pinta el motivo del fallo |

---

## 11.11 Casos borde, fallos y recuperación

**Entrega o tarea de registro eliminada en Canvas.** Con la confirmación en dos ciclos consecutivos
de §5/§8 y la incidencia `ENTREGA_ELIMINADA_EN_CANVAS`, los pendientes de esa entrega
(`proximidad_cierre`, `correccion_publicada`) se cancelan con `motivo_estado = 'ENTREGA_ELIMINADA'`;
**lo que no se cancela** es `repositorio_disponible`, `invitacion_aceptada` y `recordatorio_invitacion`,
porque cuelgan del acceso y del repositorio, no de la entrega, y el repositorio sigue existiendo. A
los estudiantes **no se les comunica nada automáticamente** —un anuncio automático de un borrado casi
siempre accidental alarmaría a toda la clase por algo que se corrige en un minuto—; la propia
incidencia ofrece el botón «anunciar a los estudiantes» con la plantilla precargada, que el profesor
decide usar o no. Si la tarea eliminada es la **tarea de registro** (A-144), `recordatorio_mapeo` se
suspende de inmediato con `motivo_estado = 'TAREA_REGISTRO_AUSENTE'` —su texto enlaza a una tarea que
ya no existe—, y si el canal activo era el canal 2, el curso pasa al canal 3 (§11.9): no se finge que
**R2.3.12** se puede seguir cumpliendo por ese canal. (RG-021, Q-2.6-59.)

**Cuota de correo agotada.** Se especifica íntegra en §14.12 y en §11.5.5: el informe cede el último,
por suscriptor y por antigüedad, y nada se descarta — queda `DIFERIDO` con `motivo_estado =
'CUOTA_AGOTADA'` y se reintenta al día siguiente.

**Canal de Canvas bloqueado.** Se especifica en §11.9: el aprovisionamiento de repositorios continúa,
los avisos obligatorios de otros capítulos tienen su propio comportamiento declarado, y ningún mensaje
se da por enviado cuando no salió.

**Matrícula que deja de ser alcanzable a mitad de una comunicación en curso.** El filtro de §11.7.5 se
reevalúa **dentro del trabajo, inmediatamente antes de cada intento** (guarda 2 de §11.2.3): un
estudiante que se retira del curso entre el momento en que se encoló su recordatorio y el momento del
despacho no lo recibe, sin que nadie tenga que cancelarlo a mano.

**Fecha que cambia después de enviado un recordatorio de proximidad.** Sí se envía un segundo
recordatorio, con una plantilla que dice explícitamente que la fecha cambió, porque la clave de
idempotencia de `proximidad_cierre` incluye la fecha objetivo (§11.2.1): una fecha distinta produce
una clave distinta, y el recordatorio anterior —si aún no salió— se cancela en la misma transacción
que recalcula `fecha_efectiva`, para que nunca convivan dos recordatorios contradictorios en la cola.
Un tope duro de 3 avisos por `(entrega, estudiante, ventana)` en total corta el caso de un profesor
que mueve la fecha varias veces. (Q-2.6-57.)

**Repositorio que pasa `READY → ERROR → READY`, o se elimina y se recrea.** Un vaivén de estado
**no** reenvía `repositorio_disponible`, porque su clave de idempotencia cuelga de
`acceso_repositorio.id` y del `github_repo_id`, ninguno de los cuales cambia por un vaivén. Un
repositorio **recreado** con un `github_repo_id` nuevo **sí** vuelve a disparar el mensaje, porque
Ley 3 hace de esa columna la clave duradera: es otro repositorio, con otra invitación que aceptar.
(Q-2.6-57.)

### Criterios de aceptación de §11.11

| # | Criterio |
|---|---|
| CA-11.11-01 | Eliminar en Canvas la entrega final de una tarea con recordatorios de proximidad ya programados cancela esos recordatorios en menos de dos ciclos del sincronizador, sin cancelar `repositorio_disponible` de esa misma tarea |
| CA-11.11-02 | Eliminar la tarea de registro con el canal activo en canal 2 hace que `curso.canal_comunicacion_activo` pase a `BLOQUEADO` y que la cabecera del curso lo declare |
| CA-11.11-03 | Retirar a un estudiante del curso mientras su recordatorio de mapeo está `PENDIENTE` en el outbox produce `SUPRIMIDO` con `motivo_estado = 'MATRICULA_NO_ACTIVA'` en el siguiente ciclo del despachador, sin intervención manual |
| CA-11.11-04 | Cambiar la fecha de una entrega después de enviado el recordatorio de 48 horas, dentro de la misma ventana, cancela el recordatorio pendiente y programa uno nuevo con la plantilla de «la fecha cambió» |
| CA-11.11-05 | Eliminar y recrear un repositorio produce un nuevo `repositorio_disponible` a los integrantes con mapeo vigente, distinto del mensaje original en `mensaje_saliente.id` |

---

## 11.12 Trazabilidad de requisitos

| Requisito | Dónde se especifica |
|---|---|
| **R2.6.1** | §11.3 (cuándo existe el informe, esquema de `informe_diario`, generación) |
| **R2.6.2** | §11.3.4 (contenido de las cinco secciones, tres causas y umbral citados de §10) |
| **R2.6.3** | §11.4 (suscripción por curso, opt-out, autogestión, enlace de baja) |
| **R2.6.4** | §11.5 (correo por curso y suscriptor, formato, ejecución manual, cuota citada de §14.12) |
| **R2.6.5** | §11.7 (mensajes directos manuales y automáticos, destinatarios, privacidad entre pares) |
| **R2.6.6** | §11.8 (anuncios automáticos y manuales, ámbito, umbral, retractación) |
| **R2.6.7** | §11.6 (catálogo cerrado de siete eventos, interruptores por tarea, efecto de activar/desactivar) |
