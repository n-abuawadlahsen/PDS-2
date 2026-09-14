# Preguntas de alcance — Proyecto 2

Indice de las decisiones de alcance que el equipo debe cerrar antes de escribir la especificacion. Son 590 preguntas repartidas en 93 bloques tematicos y 12 documentos, uno por area del enunciado.

Provienen de dos corridas de agentes sobre el enunciado y el estudio tecnico de APIs. La primera produjo 783 preguntas en bruto. La segunda anadio 40, verifico las 823 contra el enunciado y fusiono duplicados hasta las 590 actuales. Ninguna quedo apartada por estar ya respondida en el enunciado.

Las preguntas no traen respuesta propuesta. Cuando hay alternativas, se listan como opciones sin recomendar ninguna.

## Documentos

| Area | Tema | Preguntas | Bloques | Bloquean la parcial |
|---|---|---|---|---|
| [2.1](area-2.1.md) | Cursos y usuarios | 63 | 9 | 32 |
| [2.2](area-2.2.md) | Estudiantes y grupos | 70 | 10 | 28 |
| [2.3](area-2.3.md) | Tareas y repositorios | 73 | 8 | 36 |
| [2.4](area-2.4.md) | Fechas de cierre y versiones | 49 | 8 | 2 |
| [2.5](area-2.5.md) | Seguimiento del avance | 66 | 9 | 3 |
| [2.6](area-2.6.md) | Informes y comunicacion | 60 | 10 | 10 |
| [2.7](area-2.7.md) | Correccion | 69 | 9 | 7 |
| [3.1](area-3.1.md) | Entrega parcial (16-sep) | 18 | 5 | 13 |
| [3.2-3.3-4](area-3.2-3.3-4.md) | Entrega final, validacion individual y evaluacion | 13 | 5 | 2 |
| [transversal](area-transversal.md) | Transversal | 46 | 7 | 30 |
| [infraestructura](area-infraestructura.md) | Infraestructura | 36 | 8 | 21 |
| [proceso](area-proceso.md) | Proceso del equipo | 27 | 5 | 9 |
| | **Total** | **590** | **93** | **193** |

## Reparto

| Tipo de pregunta | N |
|---|---|
| decision_equipo | 493 |
| verificar_empiricamente | 56 |
| dependencia_externa | 29 |
| investigable_en_docs | 12 |

| Aplica a | N |
|---|---|
| parcial | 90 |
| ambas | 198 |
| final | 302 |

## Bloques por area

### 2.1 — Cursos y usuarios

[Abrir el documento](area-2.1.md) · 63 preguntas

- Identidad, registro y administración de la plataforma (8)
- Modelo de curso, membresías y ciclo de vida (9)
- Flujo de configuración y vinculación del curso (2)
- Vinculación con Canvas (10)
- Vinculación con GitHub (12)
- Equipo docente: incorporación, permisos y alcance (7)
- Retiro de ayudantes y bajas (3)
- Verificación de la configuración (R2.1.6) (8)
- Casos borde, cambios de vinculación y recuperación (4)

### 2.2 — Estudiantes y grupos

[Abrir el documento](area-2.2.md) · 70 preguntas

- Estrategia de enrolamiento y alcance (7)
- Tarea de Canvas de registro y recoleccion del mapeo (6)
- Parseo, validacion y ciclo de vida del mapeo estudiante-GitHub (11)
- Acceso a GitHub: organizacion, invitaciones y recordatorios (3)
- Roster: quien cuenta como estudiante (6)
- Sincronizacion con Canvas (10)
- Secciones (4)
- Grupos de Canvas (10)
- Vista de informacion faltante, permisos y exenciones (6)
- Casos borde y recuperacion: cambios posteriores, retiros y datos inconsistentes (7)

### 2.3 — Tareas y repositorios

[Abrir el documento](area-2.3.md) · 73 preguntas

- Modelo estructural: tarea, entregas y sujetos (13)
- Repositorio base y contenido inicial (8)
- Nomenclatura de repositorios (2)
- Acceso a GitHub: modelo de colaboradores, invitaciones y configuracion del repositorio (12)
- Aprovisionamiento automatico: predicado, disparadores y arquitectura del worker (8)
- Visibilidad del estado, errores y usabilidad (6)
- Comunicacion con el estudiante a traves de Canvas (10)
- Cambios, casos borde y recuperacion (14)

### 2.4 — Fechas de cierre y versiones

[Abrir el documento](area-2.4.md) · 49 preguntas

- Alcance de la entrega parcial y entorno de prueba (2)
- Definicion de la fecha de cierre y de la fecha efectiva (6)
- Obtencion y sincronizacion de fechas desde Canvas (8)
- Zona horaria, formato y presentacion de fechas (3)
- Definicion y mecanismo de la version registrada (11)
- Acceso a la version, correccion y comunicacion de la entrega (6)
- Cambios posteriores, recalculo y recaptura (8)
- Integridad, manipulacion y fallos de infraestructura (5)

### 2.5 — Seguimiento del avance

[Abrir el documento](area-2.5.md) · 66 preguntas

- Arquitectura de ingesta y frescura de los datos (9)
- Modelo de datos del monitoreo (4)
- Definiciones operativas de actividad y de tiempo (8)
- Atribucion de commits y definicion de participacion (11)
- Contenido, rendimiento y usabilidad del dashboard (12)
- Entregas, periodos y fechas (6)
- Comparacion de integrantes y metricas adicionales (5)
- Timeline de la evolucion del trabajo (4)
- Casos borde, recuperacion y gobierno de datos (7)

### 2.6 — Informes y comunicacion

[Abrir el documento](area-2.6.md) · 60 preguntas

- Decisiones estructurales: emisor, canales y viabilidad tecnica (5)
- Informe docente diario: cuando existe y que cubre (8)
- Informe diario: correo, formato e infraestructura de envio (4)
- Suscripcion al informe diario (6)
- Informe diario: persistencia, ejecucion manual y recuperacion (4)
- Comunicaciones automaticas a estudiantes: catalogo y configuracion (8)
- Mensajes directos: redaccion, destinatarios y ritmo (8)
- Anuncios en Canvas (8)
- Trazabilidad, plantillas y notificaciones internas (3)
- Casos borde, fallos y recuperacion (6)

### 2.7 — Correccion

[Abrir el documento](area-2.7.md) · 69 preguntas

- Modelo y alcance de la corrección (decisiones estructurales) (5)
- Asignación de correctores (R2.7.1) (10)
- Vista del ayudante y navegación (R2.7.2, R2.7.3) (7)
- Acceso a la versión del repositorio (R2.7.4) (3)
- Rúbrica (R2.7.5) (5)
- Nota, comentario y publicación en Canvas (R2.7.6) (16)
- Identidad, credenciales y permisos para escribir en Canvas (6)
- Estado de corrección y seguimiento (R2.7.7) (5)
- Casos borde, conflictos y recuperación (12)

### 3.1 — Entrega parcial (16-sep)

[Abrir el documento](area-3.1.md) · 18 preguntas

- Alcance de la entrega parcial y criterios de evaluacion (4)
- Autenticacion, registro y vinculacion de cuentas (3)
- Entorno de entrega: despliegue, acceso de revisores y entregables (5)
- Demo presencial del 16-sep: logistica, guion y tiempos (4)
- Casos borde, concurrencia y recuperacion (2)

### 3.2-3.3-4 — Entrega final, validacion individual y evaluacion

[Abrir el documento](area-3.2-3.3-4.md) · 13 preguntas

- Alcance evaluable: que debe poder ver y hacer un revisor con la herramienta (3)
- Datos y operacion del entorno de demostracion (2)
- Entregables de la seccion 3.2 (3)
- Actividad de validacion individual del 7 de octubre y propiedad del codigo (3)
- Casos borde, limites y recuperacion del entorno (2)

### transversal — Transversal

[Abrir el documento](area-transversal.md) · 46 preguntas

- Alcance del producto y coexistencia en el entorno de evaluacion (3)
- Configuracion, modelo de datos y definiciones canonicas (7)
- Zona horaria, idioma y vocabulario (3)
- Navegacion, pantallas y guia al equipo docente (12)
- Sesion, autorizacion, credenciales y datos personales (7)
- Integracion con APIs externas: limites, concurrencia y resiliencia (7)
- Consistencia de efectos externos, trabajos en cola y recuperacion (7)

### infraestructura — Infraestructura

[Abrir el documento](area-infraestructura.md) · 36 preguntas

- Decisiones estructurales de plataforma y stack (5)
- Cuentas, instancias y credenciales de los servicios externos (9)
- Ejecucion automatica: scheduler, colas e ingesta de actividad (6)
- Repositorios generados: identidad, visibilidad y proteccion (2)
- Secretos, cifrado y entornos (3)
- Envio de correo del informe diario (3)
- Despliegue, migraciones y control de versiones (3)
- Operacion, observabilidad, almacenamiento y recuperacion (5)

### proceso — Proceso del equipo

[Abrir el documento](area-proceso.md) · 27 preguntas

- Organizacion del equipo, cierre de decisiones y planificacion (5)
- Alcance de cada entrega (4)
- Datos de demostracion, cuentas y entorno de prueba (5)
- Practicas de ingenieria, calidad y documentacion (8)
- Ejecucion de la demo, entrega y recuperacion (5)
