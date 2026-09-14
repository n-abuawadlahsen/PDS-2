|     |     |           |     | ICC4201  | - Proyecto Desarrollo | de Software | 202620 |
| --- | --- | --------- | --- | -------- | --------------------- | ----------- | ------ |
|     |     | Enunciado |     | Proyecto | 2                     |             |        |
Web
1 Introduccio´n
Enesteproyectodeber´andesarrollarunaaplicaci´onWebparaapoyarlagesti´ondetareasdeprogra-
maci´on en cursos universitarios. Actualmente, el desarrollo y entrega de este tipo de tareas requiere
coordinarinformaci´onqueseencuentradistribuidaentredistintasplataformas. Porunaparte, Can-
vas contiene la informaci´on acad´emica del curso, incluyendo estudiantes, grupos, secciones, tareas,
fechas de entrega y evaluaciones. Por otra, GitHub permite mantener los repositorios en los que los
estudiantes desarrollan sus proyectos y registrar la evoluci´on de su trabajo.
La aplicaci´on deber´a facilitar esta coordinaci´on para profesores y ayudantes, automatizando la
creaci´on y administraci´on de los repositorios asociados a las tareas y proporcionando herramientas
paramonitorearelavanceyrealizarposteriormentesucorrecci´on. Losestudiantesnoser´anusuarios
de la aplicaci´on: toda su interacci´on deber´a realizarse a trav´es de Canvas y GitHub. La aplicaci´on
deber´a prestar especial atenci´on a la facilidad de uso, guiando adecuadamente al equipo docente en
los procesos que requieren informaci´on proveniente de ambas plataformas.
2 Detalles
| 2.1 Cursos | y usuarios |     |     |     |     |     |     |
| ---------- | ---------- | --- | --- | --- | --- | --- | --- |
La aplicaci´on se organizar´a en torno a cursos administrados por profesores. Cada curso deber´a
vincular la informaci´on acad´emica disponible en Canvas con una organizaci´on de GitHub utilizada
paramantenerlosrepositoriosdelcurso. Laaplicaci´ondeber´afacilitaresteprocesodeconfiguraci´on
y entregar informaci´on suficiente para que el profesor pueda verificar que la vinculaci´on se realiz´o
correctamente.
| La plataforma | deber´a:      |          |                   |     |     |     |     |
| ------------- | ------------- | -------- | ----------------- | --- | --- | --- | --- |
| 1. Crear      | y administrar | usuarios | de tipo profesor. |     |     |     |     |
2. Permitir que usuarios se registren asociando su cuenta de correo basada en gmail.com.
| 3. Permitir | a profesores | crear y      | administrar   | sus cursos. |     |     |     |
| ----------- | ------------ | ------------ | ------------- | ----------- | --- | --- | --- |
| 4. Vincular | cada curso   | con un curso | disponible    | en Canvas.  |     |     |     |
| 5. Vincular | cada curso   | con una      | organizaci´on | de GitHub.  |     |     |     |
6. Guiar al profesor durante el proceso de vinculaci´on, permitiendo verificar que las configura-
| ciones | realizadas | son correctas. |     |     |     |     |     |
| ------ | ---------- | -------------- | --- | --- | --- | --- | --- |
7. Incorporar otros usuarios como profesores del curso (mismos permisos).
8. Incorporar ayudantes a un curso y administrar sus permisos dentro de la aplicaci´on (uds.
| deben | definir los | permisos, m´ınimo | 3). |     |     |     |     |
| ----- | ----------- | ----------------- | --- | --- | --- | --- | --- |
9. Permitir que el profesor retire posteriormente a un ayudante del curso.
1
FacultadIngenier´ıayCienciasAplicadas
UniversidaddelosAndes

|     |             |     |     |          |     |     | ICC4201 | - Proyecto Desarrollo | de Software | 202620 |
| --- | ----------- | --- | --- | -------- | --- | --- | ------- | --------------------- | ----------- | ------ |
| 2.2 | Estudiantes |     |     | y grupos |     |     |         |                       |             |        |
La informaci´on de los estudiantes, secciones y grupos deber´a provenir de Canvas. Para poder ad-
ministrar los repositorios, la aplicaci´on deber´a mantener una correspondencia entre cada estudiante
del curso y su usuario de GitHub. Cada grupo deber´a definir una estrategia adecuada para re-
alizar este proceso de enrolamiento, considerando que los estudiantes no ingresan directamente a la
| aplicaci´on. |               | Se  | evaluar´a | la usabilidad |     | de este | proceso. |     |     |     |
| ------------ | ------------- | --- | --------- | ------------- | --- | ------- | -------- | --- | --- | --- |
|              | La plataforma |     | deber´a:  |               |     |         |          |     |     |     |
1. Obtener y mantener la informaci´on de los estudiantes inscritos en el curso.
|     | 2. Identificar |     | la secci´on | a la | que | pertenece | cada estudiante. |     |     |     |
| --- | -------------- | --- | ----------- | ---- | --- | --------- | ---------------- | --- | --- | --- |
3. Obtener los grupos definidos en Canvas para aquellas tareas que se realizan grupalmente,
|     | incluyendo |     | sus | integrantes. |     |     |     |     |     |     |
| --- | ---------- | --- | --- | ------------ | --- | --- | --- | --- | --- | --- |
4. Asociar cada estudiante de Canvas con el usuario de GitHub que le corresponde.
5. Proporcionar un mecanismo que permita completar progresivamente las asociaciones que au´n
|     | no  | est´en | disponibles. |     |     |     |     |     |     |     |
| --- | --- | ------ | ------------ | --- | --- | --- | --- | --- | --- | --- |
6. Mostrar claramente al equipo docente los estudiantes o grupos para los cuales todav´ıa falta
|     | informaci´on |     | necesaria      | para | administrar |     | sus repositorios. |     |     |     |
| --- | ------------ | --- | -------------- | ---- | ----------- | --- | ----------------- | --- | --- | --- |
| 2.3 | Tareas       |     | y repositorios |      |             |     |                   |     |     |     |
La aplicaci´on deber´a permitir administrar tareas de programaci´on asociadas al curso. Una tarea
podr´a contemplar una u´nica entrega o mu´ltiples entregas parciales y finales. Cada entrega estar´a
asociadaaunatareaindependienteenCanvas,perotodaslasentregasdeunamismatareautilizar´an
el mismo repositorio de GitHub para cada estudiante o grupo. Para cada tarea se deber´an crear
autom´aticamente los repositorios necesarios, ya sean individuales o grupales segu´n la configuraci´on
disponible en Canvas. La creaci´on de estos repositorios no deber´a depender de una acci´on realizada
por los estudiantes.
|     | La plataforma |     | deber´a: |     |     |     |     |     |     |     |
| --- | ------------- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
1. Crear una tarea en la plataforma vincul´andola con una o m´as tareas ya creadas en Canvas.
2. Identificar cada tarea de Canvas vinculada como una entrega de la tarea, pudiendo existir
|     | entregas |     | parciales | y una | entrega | final. |     |     |     |     |
| --- | -------- | --- | --------- | ----- | ------- | ------ | --- | --- | --- | --- |
3. Identificar la configuraci´on de cada tarea segu´n si en Canvas se encuentra como individual o
grupal (todas las entregas asociadas a una misma tarea deben tener la misma configuraci´on).
4. Mantener un u´nico conjunto de repositorios para todas las entregas asociadas a una misma
tarea.
5. Permitiralprofesorcreardesdelaaplicaci´onunrepositoriobaseparaunatarea(elrepositorio
|     | base | es opcional |     | al momento |     | de configurar | la tarea). |     |     |     |
| --- | ---- | ----------- | --- | ---------- | --- | ------------- | ---------- | --- | --- | --- |
6. Incorporar y administrar los archivos iniciales que formar´an parte del repositorio base.
2
FacultadIngenier´ıayCienciasAplicadas
UniversidaddelosAndes

|     |     |     | ICC4201 | - Proyecto Desarrollo | de Software | 202620 |
| --- | --- | --- | ------- | --------------------- | ----------- | ------ |
7. Crearautom´aticamentelosrepositorioscorrespondientesalosestudiantesogruposdelatarea
| utilizando | el repositorio | base cuando | corresponda. |     |     |     |
| ---------- | -------------- | ----------- | ------------ | --- | --- | --- |
8. Asignar nombres autom´aticos e inequ´ıvocos a los repositorios creados.
9. Incorporar autom´aticamente los estudiantes correspondientes a cada repositorio.
10. Crear los repositorios progresivamente a medida que se disponga de toda la informaci´on re-
querida para cada estudiante o grupo. Esto debe hacerse de forma autom´atica, sin interacci´on
| directa | de un usuario. |     |     |     |     |     |
| ------- | -------------- | --- | --- | --- | --- | --- |
11. Mostrar claramente el estado de creaci´on y configuraci´on de todos los repositorios de una
tarea, incluyendo aquellos casos en que exista informaci´on pendiente o algu´n problema que
| impida | completar el | proceso. |     |     |     |     |
| ------ | ------------ | -------- | --- | --- | --- | --- |
12. Proporcionar al estudiante, a trav´es de Canvas, la informaci´on necesaria para acceder al
| repositorio | que le corresponde. |               |     |     |     |     |
| ----------- | ------------------- | ------------- | --- | --- | --- | --- |
| 2.4 Fechas  | y cierre            | de las tareas |     |     |     |     |
Cada entrega asociada a una tarea deber´a considerar la informaci´on de fechas definida en Canvas.
Una misma tarea podr´a tener mu´ltiples entregas, cada una con su propia fecha de cierre. Adem´as,
un mismo curso puede contener distintas secciones con fechas diferentes, as´ı como excepciones o
| extensiones   | aplicables solamente | a determinados | estudiantes | o grupos. |     |     |
| ------------- | -------------------- | -------------- | ----------- | --------- | --- | --- |
| La plataforma | deber´a              | permitir:      |             |           |     |     |
1. Obtener y considerar las fechas de entrega definidas en Canvas para cada entrega asociada a
| una | tarea. |     |     |     |     |     |
| --- | ------ | --- | --- | --- | --- | --- |
2. Considerar fechas diferentes para las distintas secciones del curso cuando as´ı est´e configurado
| en  | Canvas. |     |     |     |     |     |
| --- | ------- | --- | --- | --- | --- | --- |
3. Considerar extensiones o modificaciones de fecha correspondientes a estudiantes o grupos
espec´ıficos.
4. Mantener actualizadas las fechas en base a posibles cambios que ocurran en Canvas.
5. Registrar autom´aticamente, para cada entrega, la versi´on del repositorio correspondiente a su
| fecha | de cierre. |     |     |     |     |     |
| ----- | ---------- | --- | --- | --- | --- | --- |
6. Mantener de manera independiente las versiones correspondientes a las distintas entregas de
| una | misma tarea. |     |     |     |     |     |
| --- | ------------ | --- | --- | --- | --- | --- |
7. Mantener correctamente las versiones ya registradas aunque posteriormente continu´e ex-
| istiendo | actividad en | el repositorio. |     |     |     |     |
| -------- | ------------ | --------------- | --- | --- | --- | --- |
8. Permitir a profesores y ayudantes acceder directamente a la versi´on que corresponde revisar
| para | cada entrega. |     |     |     |     |     |
| ---- | ------------- | --- | --- | --- | --- | --- |
3
FacultadIngenier´ıayCienciasAplicadas
UniversidaddelosAndes

|                 |     |           | ICC4201 | - Proyecto Desarrollo | de Software | 202620 |
| --------------- | --- | --------- | ------- | --------------------- | ----------- | ------ |
| 2.5 Seguimiento | y   | monitoreo |         |                       |             |        |
La aplicaci´on deber´a entregar al equipo docente informaci´on que permita conocer f´acilmente el
estado de avance de una tarea mientras los estudiantes trabajan en ella. Esta informaci´on deber´a
encontrarsedisponibledeformainmediataalingresaralavistadeunatarea,sin requerir esperar
a que se recopile en ese momento la actividad de todos los repositorios.
| La plataforma | deber´a:     |         |                  |     |     |     |
| ------------- | ------------ | ------- | ---------------- | --- | --- | --- |
| 1. Mostrar    | un dashboard | general | para cada tarea. |     |     |     |
2. Presentar informaci´on sobre la actividad de los distintos repositorios a lo largo del tiempo.
| 3. Identificar | repositorios | que no han | presentado | actividad reciente. |     |     |
| -------------- | ------------ | ---------- | ---------- | ------------------- | --- | --- |
4. Identificar estudiantes que au´n no hayan participado en el desarrollo de su repositorio.
5. Mostrar el estado general de creaci´on y configuraci´on de los repositorios de la tarea.
6. Mostrar claramente las distintas entregas asociadas a una tarea, sus fechas y su estado.
7. Permitir consultar la actividad de los repositorios considerando los per´ıodos correspondientes
| a las | distintas entregas. |     |     |     |     |     |
| ----- | ------------------- | --- | --- | --- | --- | --- |
8. Permitir comparar la participaci´on de los integrantes de un mismo grupo.
9. Incorporar otras m´etricas o visualizaciones que cada grupo considere u´tiles para apoyar el
| seguimiento | del trabajo | de los estudiantes. |     |     |     |     |
| ----------- | ----------- | ------------------- | --- | --- | --- | --- |
Adem´as del dashboard general, cada repositorio deber´a contar con una vista de timeline que
permita revisar f´acilmente la evoluci´on del trabajo realizado, identificando cu´ando se produjeron
los principales cambios, qu´e integrantes participaron en ellos y las distintas entregas asociadas a la
tarea.
| 2.6 Informes | y comunicacio´n |     |     |     |     |     |
| ------------ | --------------- | --- | --- | --- | --- | --- |
La plataforma deber´a apoyar al equipo docente en la identificaci´on de situaciones que puedan
requerir su atenci´on y facilitar la comunicaci´on con los estudiantes utilizando los mecanismos
| disponibles   | en Canvas. |     |     |     |     |     |
| ------------- | ---------- | --- | --- | --- | --- | --- |
| La plataforma | deber´a:   |     |     |     |     |     |
1. Generar un informe docente diario con informaci´on relevante sobre el desarrollo de las tareas
| activas | (si no hay tareas | activas | entonces no | hay informe). |     |     |
| ------- | ----------------- | ------- | ----------- | ------------- | --- | --- |
2. Incluir en este informe situaciones que puedan requerir la intervenci´on del equipo docente,
tales como ausencia de actividad, estudiantes sin participaci´on o problemas pendientes en la
| creaci´on | de repositorios. |     |     |     |     |     |
| --------- | ---------------- | --- | --- | --- | --- | --- |
3. Permitir que profesores y ayudantes se suscriban o den de baja individualmente de estos
informes.
4
FacultadIngenier´ıayCienciasAplicadas
UniversidaddelosAndes

|     |     |     | ICC4201 | - Proyecto Desarrollo | de Software | 202620 |
| --- | --- | --- | ------- | --------------------- | ----------- | ------ |
4. Enviar el informe a profesores y ayudantes suscritos a trav´es de email.
5. Enviar mensajes directos a trav´es de Canvas a estudiantes cuando sea necesario comunicar
informaci´on particular relacionada con una entrega o repositorio (creaci´on, correcci´on, etc.).
6. GeneraranunciosenCanvasdelcursoparacomunicareventosgeneralesasociadosaunatarea,
| como | cambio en las fechas | de entrega. |     |     |     |     |
| ---- | -------------------- | ----------- | --- | --- | --- | --- |
7. Generar autom´aticamente comunicaciones asociadas a determinados eventos relevantes, tales
como la disponibilidad de los repositorios o la proximidad de una fecha correspondiente a
alguna de las entregas de la tarea. Estas comunicaciones pueden ser activadas o desactivadas
| por el | profesor dentro | de cada tarea. |     |     |     |     |
| ------ | --------------- | -------------- | --- | --- | --- | --- |
2.7 Correcci´on
Cadaunadelasentregasasociadasaunatareadeber´apodersercorregidademaneraindependiente.
Las ru´bricas y las calificaciones deber´an mantenerse en Canvas, mientras que la aplicaci´on deber´a
facilitar el acceso a la versi´on del c´odigo correspondiente a cada entrega y la distribuci´on del trabajo
| entre los integrantes | del equipo | docente. |     |     |     |     |
| --------------------- | ---------- | -------- | --- | --- | --- | --- |
| La plataforma         | deber´a:   |          |     |     |     |     |
1. Permitir al profesor asignar las entregas de los distintos estudiantes o grupos entre los ayu-
| dantes | del curso. |     |     |     |     |     |
| ------ | ---------- | --- | --- | --- | --- | --- |
2. Permitir que cada ayudante identifique f´acilmente cu´ales son las entregas que tiene asignadas
| para       | corregir.         |                     |          |            |     |     |
| ---------- | ----------------- | ------------------- | -------- | ---------- | --- | --- |
| 3. Navegar | de forma sencilla | entre las distintas | entregas | asignadas. |     |     |
4. Acceder directamente a la versi´on del repositorio correspondiente a la entrega que est´a siendo
revisada.
5. Acceder a trav´es de la plataforma a la ru´brica asociada en Canvas a dicha entrega.
6. RegistrarlascalificacionesdesdelaplataformademaneraquequedenalmacenadasenCanvas.
7. Mostrar el estado de correcci´on de los distintos grupos o estudiantes de una tarea.
3 Entregas
| 3.1 Entrega | parcial [1.6 | ptos.] |     |     |     |     |
| ----------- | ------------ | ------ | --- | --- | --- | --- |
Mi´ercoles16deseptiembre13.30(presencial). Deber´anrealizarunademostraci´ondelflujocompleto
desdelacreaci´ondeunusuarioprofesor,lacreaci´ondeuncurso,suvinculaci´onconCanvasygithub,
la creacio´n de una tarea individual y la creaci´on autom´atica de los repositorios asociados. Esto
incluye entonces el proceso de asociaci´on de los estudiantes en Canvas con sus cuentas de github.
Deber´an entregar por Canvas un link para acceder a su entrega y que esta pueda ser utilizada
| por ayudantes | y el profesor. |     |     |     |     |     |
| ------------- | -------------- | --- | --- | --- | --- | --- |
En esta entrega parcial se considerar´a en la evaluaci´on la facilidad de uso y la gu´ıa adecuada
| para realizar | todo el proceso. |     |     |     |     |     |
| ------------- | ---------------- | --- | --- | --- | --- | --- |
5
FacultadIngenier´ıayCienciasAplicadas
UniversidaddelosAndes

|             |     |       |     | ICC4201 | - Proyecto Desarrollo | de Software | 202620 |
| ----------- | --- | ----- | --- | ------- | --------------------- | ----------- | ------ |
| 3.2 Entrega |     | final |     |         |                       |             |        |
Martes 6 de octubre 16.00. Deber´an entregar por github todo su c´odigo, y por Canvas una URL
dondesuaplicaci´ondeber´aestardisponibleparaserutilizadaalmenosporlassiguientesdossemanas
a la entrega. Adicionalmente, deber´an entregar tambi´en por Canvas un link a un video de m´aximo
3 minutos donde muestren el funcionamiento de su Web App y destaquen sus principales virtudes.
| Adem´as       | deber´an | entregar    | por Canvas la | declaraci´on | de uso de IA. |     |     |
| ------------- | -------- | ----------- | ------------- | ------------ | ------------- | --- | --- |
| 3.3 Actividad |          | Validaci´on |               |              |               |     |     |
El mi´ercoles 7 de octubre en clases (presencial) habr´a una actividad individual donde deber´an
demostrar el conocimiento de su proyecto. Esta actividad no tiene puntaje, sino que fallar en
ella puede levar a un descuento de hasta 3 puntos en la nota final del proyecto. El descuento es
| individual, | no grupal. |     |     |     |     |     |     |
| ----------- | ---------- | --- | --- | --- | --- | --- | --- |
4 Consideraciones
No hay restricciones en el uso de lenguaje, frameworks o librer´ıas mientras estas sean de uso libre
y gratuito.
La revisi´on es utilizando la herramienta, por ende, las funcionalidades a las que no se puede
acceder en el uso no se consideran cumplidas aunque est´en en el c´odigo.
Recuerden que deben ser duen˜os de su c´odigo, en cualquier momento el profesor o los ayudantes
pueden pedirles que expliquen como resolvieron alguna situaci´on en su programa y uds. deben ser
| capaces | de responder, | de lo contrario | tendr´an | un 1.0 | en el proyecto. |     |     |
| ------- | ------------- | --------------- | -------- | ------ | --------------- | --- | --- |
| NO      | HAY PUNTO     | BASE.           |          |        |                 |     |     |
6
FacultadIngenier´ıayCienciasAplicadas
UniversidaddelosAndes