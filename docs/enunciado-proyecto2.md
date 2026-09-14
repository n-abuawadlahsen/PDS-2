# Enunciado Proyecto 2 — Web (transcripción con IDs de requisito)

ICC4201 - Proyecto Desarrollo de Software 202620 · Universidad de los Andes · Facultad de Ingeniería y Ciencias Aplicadas

## 1 Introducción

En este proyecto deberán desarrollar una aplicación Web para apoyar la gestión de tareas de programación en cursos universitarios. Actualmente, el desarrollo y entrega de este tipo de tareas requiere coordinar información que se encuentra distribuida entre distintas plataformas. Por una parte, Canvas contiene la información académica del curso, incluyendo estudiantes, grupos, secciones, tareas, fechas de entrega y evaluaciones. Por otra, GitHub permite mantener los repositorios en los que los estudiantes desarrollan sus proyectos y registrar la evolución de su trabajo.

La aplicación deberá facilitar esta coordinación para profesores y ayudantes, automatizando la creación y administración de los repositorios asociados a las tareas y proporcionando herramientas para monitorear el avance y realizar posteriormente su corrección. **Los estudiantes no serán usuarios de la aplicación: toda su interacción deberá realizarse a través de Canvas y GitHub.** La aplicación deberá prestar especial atención a la facilidad de uso, guiando adecuadamente al equipo docente en los procesos que requieren información proveniente de ambas plataformas.

## 2 Detalles

### 2.1 Cursos y usuarios

La aplicación se organizará en torno a cursos administrados por profesores. Cada curso deberá vincular la información académica disponible en Canvas con una organización de GitHub utilizada para mantener los repositorios del curso. La aplicación deberá facilitar este proceso de configuración y entregar información suficiente para que el profesor pueda verificar que la vinculación se realizó correctamente.

La plataforma deberá:

- **R2.1.1** Crear y administrar usuarios de tipo profesor.
- **R2.1.2** Permitir que usuarios se registren asociando su cuenta de correo basada en gmail.com.
- **R2.1.3** Permitir a profesores crear y administrar sus cursos.
- **R2.1.4** Vincular cada curso con un curso disponible en Canvas.
- **R2.1.5** Vincular cada curso con una organización de GitHub.
- **R2.1.6** Guiar al profesor durante el proceso de vinculación, permitiendo verificar que las configuraciones realizadas son correctas.
- **R2.1.7** Incorporar otros usuarios como profesores del curso (mismos permisos).
- **R2.1.8** Incorporar ayudantes a un curso y administrar sus permisos dentro de la aplicación (uds. deben definir los permisos, mínimo 3).
- **R2.1.9** Permitir que el profesor retire posteriormente a un ayudante del curso.

### 2.2 Estudiantes y grupos

La información de los estudiantes, secciones y grupos deberá provenir de Canvas. Para poder administrar los repositorios, la aplicación deberá mantener una correspondencia entre cada estudiante del curso y su usuario de GitHub. **Cada grupo deberá definir una estrategia adecuada para realizar este proceso de enrolamiento, considerando que los estudiantes no ingresan directamente a la aplicación. Se evaluará la usabilidad de este proceso.**

La plataforma deberá:

- **R2.2.1** Obtener y mantener la información de los estudiantes inscritos en el curso.
- **R2.2.2** Identificar la sección a la que pertenece cada estudiante.
- **R2.2.3** Obtener los grupos definidos en Canvas para aquellas tareas que se realizan grupalmente, incluyendo sus integrantes.
- **R2.2.4** Asociar cada estudiante de Canvas con el usuario de GitHub que le corresponde.
- **R2.2.5** Proporcionar un mecanismo que permita completar progresivamente las asociaciones que aún no estén disponibles.
- **R2.2.6** Mostrar claramente al equipo docente los estudiantes o grupos para los cuales todavía falta información necesaria para administrar sus repositorios.

### 2.3 Tareas y repositorios

La aplicación deberá permitir administrar tareas de programación asociadas al curso. Una tarea podrá contemplar una única entrega o múltiples entregas parciales y finales. Cada entrega estará asociada a una tarea independiente en Canvas, pero todas las entregas de una misma tarea utilizarán el mismo repositorio de GitHub para cada estudiante o grupo. Para cada tarea se deberán crear automáticamente los repositorios necesarios, ya sean individuales o grupales según la configuración disponible en Canvas. **La creación de estos repositorios no deberá depender de una acción realizada por los estudiantes.**

La plataforma deberá:

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

### 2.4 Fechas y cierre de las tareas

Cada entrega asociada a una tarea deberá considerar la información de fechas definida en Canvas. Una misma tarea podrá tener múltiples entregas, cada una con su propia fecha de cierre. Además, un mismo curso puede contener distintas secciones con fechas diferentes, así como excepciones o extensiones aplicables solamente a determinados estudiantes o grupos.

La plataforma deberá permitir:

- **R2.4.1** Obtener y considerar las fechas de entrega definidas en Canvas para cada entrega asociada a una tarea.
- **R2.4.2** Considerar fechas diferentes para las distintas secciones del curso cuando así esté configurado en Canvas.
- **R2.4.3** Considerar extensiones o modificaciones de fecha correspondientes a estudiantes o grupos específicos.
- **R2.4.4** Mantener actualizadas las fechas en base a posibles cambios que ocurran en Canvas.
- **R2.4.5** Registrar automáticamente, para cada entrega, la versión del repositorio correspondiente a su fecha de cierre.
- **R2.4.6** Mantener de manera independiente las versiones correspondientes a las distintas entregas de una misma tarea.
- **R2.4.7** Mantener correctamente las versiones ya registradas aunque posteriormente continúe existiendo actividad en el repositorio.
- **R2.4.8** Permitir a profesores y ayudantes acceder directamente a la versión que corresponde revisar para cada entrega.

### 2.5 Seguimiento y monitoreo

La aplicación deberá entregar al equipo docente información que permita conocer fácilmente el estado de avance de una tarea mientras los estudiantes trabajan en ella. Esta información deberá encontrarse disponible de forma inmediata al ingresar a la vista de una tarea, **sin requerir esperar a que se recopile en ese momento la actividad de todos los repositorios**.

La plataforma deberá:

- **R2.5.1** Mostrar un dashboard general para cada tarea.
- **R2.5.2** Presentar información sobre la actividad de los distintos repositorios a lo largo del tiempo.
- **R2.5.3** Identificar repositorios que no han presentado actividad reciente.
- **R2.5.4** Identificar estudiantes que aún no hayan participado en el desarrollo de su repositorio.
- **R2.5.5** Mostrar el estado general de creación y configuración de los repositorios de la tarea.
- **R2.5.6** Mostrar claramente las distintas entregas asociadas a una tarea, sus fechas y su estado.
- **R2.5.7** Permitir consultar la actividad de los repositorios considerando los períodos correspondientes a las distintas entregas.
- **R2.5.8** Permitir comparar la participación de los integrantes de un mismo grupo.
- **R2.5.9** Incorporar otras métricas o visualizaciones que cada grupo considere útiles para apoyar el seguimiento del trabajo de los estudiantes.

- **R2.5.10 (párrafo final)** Además del dashboard general, cada repositorio deberá contar con una vista de *timeline* que permita revisar fácilmente la evolución del trabajo realizado, identificando cuándo se produjeron los principales cambios, qué integrantes participaron en ellos y las distintas entregas asociadas a la tarea.

### 2.6 Informes y comunicación

La plataforma deberá apoyar al equipo docente en la identificación de situaciones que puedan requerir su atención y facilitar la comunicación con los estudiantes utilizando los mecanismos disponibles en Canvas.

La plataforma deberá:

- **R2.6.1** Generar un informe docente diario con información relevante sobre el desarrollo de las tareas activas (si no hay tareas activas entonces no hay informe).
- **R2.6.2** Incluir en este informe situaciones que puedan requerir la intervención del equipo docente, tales como ausencia de actividad, estudiantes sin participación o problemas pendientes en la creación de repositorios.
- **R2.6.3** Permitir que profesores y ayudantes se suscriban o den de baja individualmente de estos informes.
- **R2.6.4** Enviar el informe a profesores y ayudantes suscritos a través de email.
- **R2.6.5** Enviar mensajes directos a través de Canvas a estudiantes cuando sea necesario comunicar información particular relacionada con una entrega o repositorio (creación, corrección, etc.).
- **R2.6.6** Generar anuncios en Canvas del curso para comunicar eventos generales asociados a una tarea, como cambio en las fechas de entrega.
- **R2.6.7** Generar automáticamente comunicaciones asociadas a determinados eventos relevantes, tales como la disponibilidad de los repositorios o la proximidad de una fecha correspondiente a alguna de las entregas de la tarea. Estas comunicaciones pueden ser activadas o desactivadas por el profesor dentro de cada tarea.

### 2.7 Corrección

Cada una de las entregas asociadas a una tarea deberá poder ser corregida de manera independiente. Las rúbricas y las calificaciones deberán mantenerse en Canvas, mientras que la aplicación deberá facilitar el acceso a la versión del código correspondiente a cada entrega y la distribución del trabajo entre los integrantes del equipo docente.

La plataforma deberá:

- **R2.7.1** Permitir al profesor asignar las entregas de los distintos estudiantes o grupos entre los ayudantes del curso.
- **R2.7.2** Permitir que cada ayudante identifique fácilmente cuáles son las entregas que tiene asignadas para corregir.
- **R2.7.3** Navegar de forma sencilla entre las distintas entregas asignadas.
- **R2.7.4** Acceder directamente a la versión del repositorio correspondiente a la entrega que está siendo revisada.
- **R2.7.5** Acceder a través de la plataforma a la rúbrica asociada en Canvas a dicha entrega.
- **R2.7.6** Registrar las calificaciones desde la plataforma de manera que queden almacenadas en Canvas.
- **R2.7.7** Mostrar el estado de corrección de los distintos grupos o estudiantes de una tarea.

## 3 Entregas

### 3.1 Entrega parcial [1.6 ptos.]

**Miércoles 16 de septiembre 13.30 (presencial).** Deberán realizar una demostración del flujo completo desde la creación de un usuario profesor, la creación de un curso, su vinculación con Canvas y github, la creación de una tarea individual y la creación automática de los repositorios asociados. Esto incluye entonces el proceso de asociación de los estudiantes en Canvas con sus cuentas de github.

Deberán entregar por Canvas un link para acceder a su entrega y que esta pueda ser utilizada por ayudantes y el profesor.

En esta entrega parcial se considerará en la evaluación la facilidad de uso y la guía adecuada para realizar todo el proceso.

### 3.2 Entrega final

**Martes 6 de octubre 16.00.** Deberán entregar por github todo su código, y por Canvas una URL donde su aplicación deberá estar disponible para ser utilizada al menos por las siguientes dos semanas a la entrega. Adicionalmente, deberán entregar también por Canvas un link a un video de máximo 3 minutos donde muestren el funcionamiento de su Web App y destaquen sus principales virtudes.

Además deberán entregar por Canvas la declaración de uso de IA.

### 3.3 Actividad Validación

El **miércoles 7 de octubre** en clases (presencial) habrá una actividad individual donde deberán demostrar el conocimiento de su proyecto. Esta actividad no tiene puntaje, sino que fallar en ella puede llevar a un descuento de hasta 3 puntos en la nota final del proyecto. El descuento es individual, no grupal.

## 4 Consideraciones

- No hay restricciones en el uso de lenguaje, frameworks o librerías mientras estas sean de uso libre y gratuito.
- La revisión es utilizando la herramienta, por ende, las funcionalidades a las que no se puede acceder en el uso no se consideran cumplidas aunque estén en el código.
- Recuerden que deben ser dueños de su código, en cualquier momento el profesor o los ayudantes pueden pedirles que expliquen como resolvieron alguna situación en su programa y uds. deben ser capaces de responder, de lo contrario tendrán un 1.0 en el proyecto.
- **NO HAY PUNTO BASE.**
