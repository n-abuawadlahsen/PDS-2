# Frontend docente · Proyecto 2

## Alcance y decisiones

Se conserva React 18, Vite y la sesión opaca por cookie/CSRF. La API implementada manda sobre referencias abreviadas del plan. El diseño toma las tres capturas adjuntas como referencia: barra global oscura, navegación de curso, tarjetas con color identificador, listas y tablas claras. No se copian marcas de Canvas ni se añade un portal de estudiante.

## Matriz de trabajo

| Pantalla | Acciones y contratos reales (prefijo `/api`) | Permisos/capacidad | Revisión |
| --- | --- | --- | --- |
| Acceso / perfil | POST `/auth/google/inicio`, `/auth/confirmar`; GET/PATCH `/perfil`, sesiones y cierre | Sesión propia | P1 |
| Cursos / inicio | GET/POST `/cursos`; GET `/{curso}/contexto` | Sesión / curso.ver | P2 |
| Equipo / invitación | `/cursos/{curso}/equipo`, invitaciones, permisos, retiro, reincorporación | equipo.administrar; lectura curso.ver | P2 |
| Vinculación / ajustes | Credencial y selección Canvas, instalación GitHub, checklist | curso.administrar | P3–P4 |
| Personas / pendientes | Espejo, mapeos, CSV con preview, registro, sincronización y recordatorios | curso.ver, mapeo.editar, comunicacion.enviar; guardas reales de configuración | P5–P6 |
| Tareas / base | `/cursos/{curso}/tareas`, entregas Canvas, base y archivos, activación | tarea.administrar | P7, F1–F2 |
| Repositorios / tablero | `/tareas/{tarea}/repositorios`, tablero y refresco | curso.ver; tablero_actividad | P8, F6 |
| Entregas / versiones | Fechas, progreso de captura, versiones, acceso auditado | curso.ver, tarea.administrar; recaptura/fijación profesor | F3–F4 |
| Timeline / identidades | `/tareas/{tarea}/repos/{repo}/timeline`, identidades y propagación | curso.ver, mapeo.editar, tarea.administrar | F5, F7 |
| Cierre | Cinco guardas, archivar/desarchivar | Profesor + tarea.administrar | F8 |
| Informes / suscripciones | Histórico, preview, envío propio, suscripción personal y `/baja/{token}` | curso.ver; informe_diario / mis_notificaciones | F9 |
| Comunicaciones | Bandeja, preview, cola, detalle, reintento/cancelación y reglas | curso.ver / comunicacion.enviar | F10 |
| Corrección / publicación | Asignaciones/matriz, reparto preview, borrador, lista, contraste y conflictos Canvas | correccion.corregir + asignación; correccion.asignar; nota.publicar | F11–F12 |

Las rutas de autenticación mantienen `/auth`, sin prefijo `/api`. Los contratos completos, métodos, permisos y límites están en [Configuración P1–P6](CONFIGURACION-CONTRATOS.md), [Operación P7–P8/F1–F8](OPERACION.md) e [Informes, comunicaciones y corrección F9–F12](F9-F12.md).

La [revisión de limitaciones de octubre](LIMITACIONES.md) registra las correcciones en frontend y backend: sesiones/identidades propias, renovación Canvas, ajustes, permisos, historial, trabajos, recordatorios, retiro, CSV, pesos, autoría, causas de participación y protección del borrador. La revisión posterior completa roles Canvas adicionales, archivo/restauración del curso y archivo remoto optativo, fusiones confirmadas, reenvío de invitaciones por estudiante, realineación del reparto, aviso a profesores y el flujo guiado de configuración individual en Canvas para notas grupales. La migración `0012` persiste roles, contexto del criterio de reparto y alias de identidades fusionadas, sin reescribir versiones ni borrar historial.

La [matriz de trazabilidad](REQUISITOS.md) contiene los **59 requisitos únicos del enunciado**, con pantalla, acción, contrato y límite cuando corresponde. “Conectado” significa que utiliza el contrato disponible; no certifica procesos externos que el frontend no ejecuta.

## Diseño y herramientas preparadas

- Node **22.22.1** instalado y fijado en `.node-version`; `.nvmrc` conserva la línea 22.x. Dependencias y lockfile actualizados mediante npm.
- shadcn/ui configurado mediante `components.json`, alias `@`, Tailwind 4 y componentes de botón, campo, skeleton y diálogo Radix. Se reutilizan las tablas, formularios y cliente existentes. Los estilos de Tailwind se limitan a `src` para que las capturas de prueba no disparen recargas del servidor.
- Lato autoalojada, pesos 400/700; iconos Lucide. No hay dependencias de fuentes externas en ejecución.
- Tokens semánticos en `frontend/src/styles/themes.css` y `tokens.css`: navegación `#2D3B45`, enlace `#005B94`, acento institucional rojo, superficies claras, bordes finos y estados con texto. Se conservan las tres paletas claras del perfil; no hay tema oscuro.
- Barra global de 88 px, navegación de curso de 220 px, tarjetas con identidad de color, breadcrumbs y selector de curso. A menor anchura, menú modal y una columna. Tablas y gráfico tienen desplazamiento interno cuando es necesario.
- Polling sin peticiones superpuestas y suspendido en pestañas ocultas; datos previos conservados tras errores. Diálogos con foco controlado, casillas/radios espaciados, confirmaciones de impacto, filtros en URL y errores junto a los campos.
- Las pantallas de tarea, Personas, seguimiento, entregas, timeline, informes, comunicaciones y corrección se cargan por ruta. Entrar a Cursos no descarga todas las pantallas de corrección.
- Playwright y Chromium instalados; axe integrado en las pruebas existentes y las nuevas. Referencias de preparación: [shadcn para Vite](https://ui.shadcn.com/docs/installation/vite) y [navegadores de Playwright](https://playwright.dev/docs/browsers).

## Levantar y revisar

Desde la raíz, para el frontend conectado a la API local existente en el puerto 8000:

```bash
cd frontend
npm ci
VITE_API_BASE_URL= API_PROXY_TARGET=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5175 --strictPort
```

Abrir `http://127.0.0.1:5175`. El proxy conserva el mismo origen para `/api`, `/auth`, `/salud` y `/estado`. `API_PROXY_TARGET` permite apuntar a otro puerto sin exponer secretos en el bundle. Para OAuth, la API debe tener `FRONTEND_ORIGEN` y la URL pública de retorno configurados para el origen local elegido. La preparación normal de API, PostgreSQL y trabajador está en el [README](../../README.md); no se reescribieron los `.env` del equipo.

Para revisar los flujos sin credenciales reales:

```bash
cd frontend
npm run tools:browser
npm test
npm run test:visual
# Exploración interactiva de los casos:
npm test -- --ui
```

Las pruebas normales levantan Vite en `127.0.0.1:4173`, utilizan respuestas HTTP sintéticas conformes a los contratos y cierran el servidor al terminar. Otro puerto se selecciona con `PLAYWRIGHT_PORT=4194 npm test`. Los datos sintéticos existen únicamente en `frontend/tests`, nunca se ofrecen como datos del producto.

Prueba adicional con FastAPI, trabajador y PostgreSQL reales, sin credenciales ni envíos externos:

```bash
cd backend
uv sync --frozen --dev
cd ../frontend
npm run test:backend
```

Requiere Docker en ejecución, Python 3.12 preparado en `backend/.venv` y puertos 8017/4187 libres. El script crea **su propio contenedor efímero**, configura los adaptadores dobles existentes, genera claves temporales y crea una sesión opaca mediante una utilidad de pruebas del backend. No añade endpoints ni bypass de autenticación a la aplicación. El cierre por SIGTERM retira contenedor, procesos y archivo de cookies con modo 0600. Las comunicaciones salientes permanecen pausadas. Nunca usa la base del equipo.

## Validación ejecutada

- `npm run format:check`, `npm run typecheck`, `npm run lint` y `npm run build`.
- **75 pruebas Playwright pasaron** en la suite completa del 6 de octubre. Cubren los siete recorridos solicitados, ambos roles, 200 sujetos, CSV con revisión, filtros/paginación, polling, sesión vencida, errores de red, rechazo de permisos, vínculos degradados, trabajos en curso, cooldown, borradores, conflicto y publicación individual/masiva. Incluyen los 10 casos de `limitaciones.spec.ts` y los siete de `pendientes-restantes.spec.ts`, con confirmaciones, conservación tras errores, archivo/restauración, guardas de GitHub, fusión, reenvío, aviso y configuración grupal.
- **497 pruebas del backend pasaron** sobre PostgreSQL efímero aislado, con **96,36 % de cobertura de `app.dominio`**, por encima del mínimo del 70 %. Ruff, comprobación de formato y mypy pasaron; mypy revisó 159 archivos. Los 23 casos de la primera revisión y los 17 de la segunda comprueban permisos, CSRF, aislamiento entre cuentas/cursos, auditoría, conservación de versiones, cuotas, guardas e idempotencia de trabajos.
- **6 pruebas visuales pasaron** tras los últimos ajustes de composición: Cursos, configuración, Personas/Pendientes, tareas/repositorios, tablero, entregas/timeline, corrección, informes y comunicaciones. Axe no encontró infracciones en los escenarios comprobados. También se verifican contraste de tokens, navegación por teclado, foco al cerrar diálogos y ampliación de texto al 200 %. Esto no equivale a una certificación completa de WCAG.
- **2 pruebas con API real local pasaron**: sesión opaca → curso vacío → crear → vincular Canvas → retorno GitHub App → sincronizar Personas → crear tarea de Canvas → guardar roles y comprobar persistencia tras recargar; además, archivar un curso → rechazar escritura → reactivar y conservar configuración. Aquí las llamadas a nuestra API no se interceptan; los proveedores externos usan los dobles del backend y se simula únicamente el salto de instalación de GitHub.
- La migración `0011` fallaba al duplicar el prefijo de la restricción. Con autorización expresa se aplicó `op.f` a sus cuatro nombres, sin alterar reglas de datos. Pasaron migración desde cero y recorrido `0011 → 0010 → 0011`, exclusivamente sobre la base efímera. Ruff pasó para esa migración y el servidor de prueba Python.
- La migración `0012`, necesaria para las limitaciones solicitadas, pasó desde cero y en el recorrido `0012 → 0010 → 0012`. No se aplicó esta migración a una base compartida o de producción.
- Consola sin `pageerror` en los recorridos de evidencia. Los errores HTTP deliberados se verifican como estados de recuperación; no se presentan como resultados exitosos.

## Evidencia visual inspeccionada

Las [42 capturas](evidencias/) contienen únicamente personas y cursos sintéticos. Se revisaron alineación, jerarquía, contraste, tablas, menús, formularios y anchura del documento. La vista Cursos se comprobó en **1440×900, 1366×768, 768×1024, 390×844 y 360 px**; las demás tienen muestras de escritorio y móvil. Se corrigieron tarjetas desalineadas, grupos de acciones sin separación, radios de rúbrica demasiado próximos y ejes del gráfico poco legibles en móvil. Se inspeccionaron las capturas de Perfil, Ajustes, autoría/comentario de corrección y causas/accesos en la matriz, además de fusión, configuración grupal en móvil y curso archivado con API local.

Ejemplos: [Cursos](evidencias/cursos-escritorio.png), [Cursos móvil](evidencias/cursos-movil.png), [Vinculación](evidencias/vinculacion-escritorio.png), [Personas](evidencias/personas-movil.png), [Tablero](evidencias/tablero-escritorio.png), [Actividad móvil](evidencias/tablero-actividad-movil.png), [Entregas](evidencias/entregas-movil.png), [Corrección](evidencias/correccion-escritorio.png) y [flujo con API real local](evidencias/api-real-tarea.png).

Regresiones corregidas: [Perfil móvil](evidencias/limitaciones-perfil-movil.png), [Ajustes móvil](evidencias/limitaciones-ajustes-movil.png), [Autoría y comentario](evidencias/limitaciones-correccion-escritorio.png) y [Accesos/causas](evidencias/limitaciones-matriz-escritorio.png).

Últimos flujos: [Fusión Canvas móvil](evidencias/pendientes-fusion-movil.png), [Configuración grupal móvil](evidencias/pendientes-calificacion-grupal-movil.png) y [Curso archivado con API local](evidencias/api-real-archivo.png).

## Límites restantes verificables

El detalle vigente y la evidencia de cada límite están en [LIMITACIONES.md](LIMITACIONES.md). Los flujos del servidor enumerados como pendientes en la revisión anterior quedaron conectados. La configuración individual del assignment se cambia en Canvas y se confirma mediante sincronización, respetando RG-082 y la precedencia de SPEC 12, §12.1.4. Las fusiones con evidencia productiva en ambas identidades requieren resolver explícitamente esa evidencia. Un reparto antiguo sin contexto o un curso archivado sin auditoría previa no permiten reconstruir una configuración que nunca se guardó.

Los borradores antiguos y los históricos de causas/accesos solo pueden mostrar lo que efectivamente se persistió. La nueva auditoría registra autoría/fecha en los siguientes guardados. No se ejecutaron OAuth, correos, repositorios ni notas en proveedores reales; la integración comprobada utiliza sus dobles existentes.

Las limitaciones anteriores de renovación, sesiones, ajustes generales, permisos, historial de mapeo, estado de trabajos, pesos, comentario renderizado, CSV filtrado y navegación Atrás/Adelante quedaron corregidas. Se conserva la política vigente de Gmail/miuandes.cl.

No se realizaron despliegues, push ni cambios de secretos.

Comprobación completa del backend sin utilizar la base del equipo, desde la raíz:

```bash
backend/.venv/bin/python frontend/tests/serve_backend.py --pytest -q --cov=app.dominio --cov-fail-under=70
```
