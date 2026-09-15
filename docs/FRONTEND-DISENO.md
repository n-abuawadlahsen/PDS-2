# Frontend de la entrega parcial

## Qué incluye

Rediseño de las pantallas de las etapas P1–P8, sobre React 18, React Router 6, Vite y TypeScript. La identidad sigue siendo **Proyecto 2**. La referencia visual es académica: navegación global oscura, navegación contextual blanca, tema claro, formularios sobrios y tablas de datos.

La aplicación sigue dirigida a profesores y ayudantes. No se agregaron módulos de la final ni interfaces de estudiantes. No hay datos de demostración, bypass de autenticación ni interceptores de pruebas en el código de producción.

## Organización

| Ubicación | Responsabilidad |
|---|---|
| `frontend/src/styles/themes.css` | **Todas las definiciones de color**, incluidas sombras y estados. |
| `frontend/src/styles/tokens.css` | Tipografía, espacios, radios y anchos de navegación. |
| `frontend/src/styles/global.css` | Formularios, botones, paneles, tablas, estados, diálogos y utilidades compartidas. |
| `frontend/src/styles/layout.css` | Estructura global, curso, acceso público y adaptación de navegación. |
| `frontend/src/config/theme.ts` | Identificadores, tema predeterminado, validación y preferencia visual. |
| `frontend/src/components/Layout.tsx` | Sesión, cursos, permisos, estructura, navegación y breadcrumbs. |
| `frontend/src/components/ui.tsx` | Cabeceras, avisos, estados, tablas, paginación, confirmaciones y selector de apariencia. |
| `frontend/src/components/ProgresoConfiguracion.tsx` | Presentación reutilizable del progreso; recibe estados calculados desde datos reales. |
| `frontend/src/hooks/useConsulta.ts` | Lectura cancelable, recarga, polling secuencial y operaciones con protección de doble clic. |
| `frontend/src/lib/api.ts` | Contratos existentes, cookies, CSRF y señales de cancelación de consultas. |
| `frontend/src/lib/errores.ts` | Normalización de errores, incluidos `detail` anidado y errores de validación. |
| `frontend/src/paginas/` | Pantallas y reglas de presentación específicas. |
| `frontend/tests/` | Pruebas de navegador y datos simulados, aislados del producto. |

No se incorporaron dependencias de ejecución. Playwright y axe se agregaron como dependencias de desarrollo para verificar flujos y accesibilidad; Prettier mantiene legible el código. Se agregó configuración de ESLint para que el script existente sea ejecutable.

## Cambiar colores y paletas

### Editar los colores

El único archivo para editar colores es **`frontend/src/styles/themes.css`**:

- `:root` define neutrales, superficies, estados, navegación y colores de respaldo.
- `:root[data-theme="institucional"]` define la identidad roja.
- `:root[data-theme="azul"]` define la identidad azul.
- `:root[data-theme="verde"]` define la identidad verde.

Los componentes consumen variables semánticas como `--color-primary`, `--color-text`, `--color-error` y `--color-focus-ring`. Éxito, advertencia y error mantienen su significado al cambiar de paleta. Las sombras también se definen aquí. No hay excepciones de colores de logos: la identificación del producto es tipográfica y los iconos usan `currentColor`.

### Cambiar el predeterminado

En **`frontend/src/config/theme.ts`**, cambia únicamente:

```ts
export const DEFAULT_THEME: ThemeName = "institucional";
```

`main.tsx` aplica el tema antes de montar React. Los neutros y la paleta roja de respaldo de CSS permiten pintar incluso antes de que se aplique la preferencia; la selección de ejecución procede exclusivamente de `theme.ts`.

### Probar desde la interfaz

Entra en **Cuenta → Mi perfil → Apariencia**. El selector aplica la paleta sin navegar, remontar componentes ni enviar solicitudes de negocio. Los campos escritos en Perfil conservan su contenido.

La preferencia se guarda en `localStorage` con la clave **`pds2.apariencia`**. Una preferencia válida guardada prevalece sobre `DEFAULT_THEME`. El botón **Restablecer apariencia** elimina esa preferencia y aplica el predeterminado; también se puede eliminar la clave desde las herramientas del navegador.

Valores desconocidos usan el predeterminado. Si el navegador bloquea el almacenamiento, el cambio sigue funcionando durante esa visita. Solo se almacena esta preferencia visual: no se guardan tokens, cookies ni permisos en `localStorage`.

### Agregar otra paleta

1. Agrega el identificador a `THEMES` y su nombre visible a `THEME_LABELS` en `theme.ts`.
2. Agrega en `themes.css` un selector `:root[data-theme="nuevo-identificador"]`.
3. Define los cinco tokens de identidad: `--color-primary`, `--color-primary-hover`, `--color-primary-active`, `--color-primary-subtle` y `--color-on-primary`. Los demás se heredan; enlace, selección y foco siguen los tokens de identidad.
4. Comprueba contraste y estados, incluyendo navegación, formularios, botones y diálogos. Los colores de estado no deben cambiar de significado.

No es necesario editar páginas o componentes.

## Navegación y recorrido

Se conservan las rutas anteriores de acceso, confirmación, invitación, retorno GitHub, cursos, equipo, vinculación, verificación, personas, pendientes, tareas y perfil. La ruta nueva **`/cursos/:cursoId`** muestra el inicio del curso. `/` abre Cursos y el control de sesión ofrece entrar si corresponde. Existe una página de enlace no encontrado.

La navegación del curso incluye Inicio, Configuración, Personas, Pendientes, Tareas y Equipo docente. La configuración agrupa visualmente vinculación y verificación sin cambiar las URLs del retorno OAuth.

El detalle de tarea organiza el contenido con enlaces que usan `?vista=resumen`, `?vista=entrega`, `?vista=base` y `?vista=repositorios`. La URL original sigue funcionando. Los paneles conservan su estado mientras cambia la sección; no se vacían archivos seleccionados ni filtros durante el polling.

Recorrido de la parcial:

1. Entrar con cuenta personal Gmail.
2. Crear curso e identificar código, período e identificador corto.
3. Añadir la credencial personal Canvas y seleccionar un curso real.
4. Declarar la cuenta GitHub docente en Perfil e instalar la App en la organización.
5. Consultar y ejecutar la verificación, con pruebas opcionales de escritura separadas.
6. Revisar estudiantes y cuentas; usar registro Canvas o alternativas docentes.
7. Crear una tarea individual como borrador y preparar una base opcional.
8. Activar la tarea una vez.
9. Observar creación progresiva, invitaciones y accesos; resolver Pendientes sin reactivar la tarea.

El inicio del curso usa cinco lecturas existentes para formar el progreso. Un fallo de consulta aparece como **Sin verificar**, no como completado. La falta de cuenta GitHub de un estudiante no bloquea la recomendación de configurar tareas.

## Comportamiento y contratos conservados

- Sesión opaca por cookie; `credentials: "include"` y `X-CSRF-Token` para mutaciones.
- Formularios de navegación POST para Google y confirmación, incluidos parámetros de invitación.
- `frontend/vercel.json` y la configuración de Vercel/Render permanecen intactos. Producción sigue usando `/api` y `/auth` bajo el origen de Vercel.
- El retorno GitHub comparte una única promesa de canje durante el doble efecto de StrictMode.
- Permisos desde `/contexto`, actualizados al cambiar de curso, recuperar foco, recibir `403` y cada 60 segundos. Un fallo de permisos no habilita escrituras.
- Las capacidades base P1–P8 siguen disponibles con `banderas: []`; no se agregan enlaces a módulos futuros. Las acciones de tarea respetan `{ habilitada, motivo }`.
- Checklist consulta cada 2 segundos durante una ejecución, con espera acotada. Repositorios consultan cada 10 segundos mientras su bloque esté montado; conservar los paneles de tarea mantiene ese comportamiento aunque se consulte otra sección.
- El polling programa la siguiente lectura después de completar la anterior. Las consultas reciben `AbortSignal`, cancelan al desmontar o cambiar su clave y descartan resultados obsoletos.
- Las recargas conservan datos existentes, búsqueda, página y foco. Las operaciones bloquean duplicación y muestran errores persistentes.
- Personas y repositorios filtran y paginan localmente el conjunto devuelto por la API; no existe una paginación de servidor inventada.
- CSV usa `csv` y `aplicar` como cadenas. Aplicar requiere previsualización vigente del mismo contenido; cambiarlo invalida incluso una respuesta de revisión que llegue tarde.
- Las fechas ISO se formatean con la zona horaria del curso. Las fechas ya formateadas por el endpoint de fechas se conservan como las devuelve el servidor.
- Archivos base usan JSON `contenido_base64`. La previsualización se muestra como texto; no se ejecuta HTML.
- Sustituir repositorio exige escribir su nombre exacto. Retirar personas, cambiar acceso, borrar o reemplazar archivos y cerrar la cuenta tienen confirmaciones explícitas.
- Las confirmaciones y el menú móvil utilizan `<dialog>` modal: foco inicial, cierre Escape, contenido de fondo inerte y retorno de foco nativo.

## Ejecución local

Usa **Node 22**, indicado en `frontend/.nvmrc` y `package.json`:

```bash
cd frontend
npm ci
npm run dev
```

Para API local, `frontend/.env` usa `VITE_API_BASE_URL=http://localhost:8000`; el README explica cómo levantar API, base de datos y trabajador. Para el proxy de Vercel, esta variable queda vacía o ausente. No se deben copiar secretos a variables `VITE_*`.

Para verificar:

```bash
cd frontend
npm run build
npm run lint
npm run format:check
npx playwright install chromium
npm test
```

`npm test` inicia Vite en `127.0.0.1:4173` con la base de API vacía e intercepta `/api/*` en el navegador de prueba. Bloquea conexiones a otros hosts. No necesita backend ni credenciales y no puede crear repositorios o enviar correos reales. El puerto 4173 debe estar libre.

Las capturas de la prueba visual institucional y las trazas de fallos se guardan en `frontend/test-results/`, excluido de Git. Los nombres y datos que aparecen allí son simulados.

## Estado de las limitaciones de integración

Las brechas de implementación de invitaciones, cierre del último profesor y sincronización de identidad GitHub se corrigieron en backend y frontend. La guía [CORRECCIONES-PARCIAL.md](CORRECCIONES-PARCIAL.md) describe los contratos, la migración `0002`, la recuperación del login tras el arranque de Render, las pruebas y la configuración para habilitar correo real.

El correo requiere un proveedor y dominio configurados en Render. Mientras tanto, se puede compartir el enlace desde Equipo. La comprobación de Google OAuth, entrega de correo y permisos externos con cuentas reales sigue pendiente del despliegue.

La referencia del plan al permiso de registro se alineó con `curso.administrar`. Las pantallas de la entrega final siguen fuera del alcance de la parcial.

## Qué prueba la validación

Resultado local con Node 22: compilación TypeScript/Vite, lint y formato aprobados; **25 pruebas automatizadas aprobadas** (24 de navegador y una de centralización de colores y contraste). En las pantallas y paletas examinadas, axe no detectó infracciones críticas ni graves. Esto no constituye una certificación completa de accesibilidad.

Las pruebas de navegador cubren sesión ausente, curso vacío, permisos de ayudante y revocación posterior, revisión CSV y respuestas tardías, activación bloqueada/aceptada, errores estructurados, polling, sustitución con confirmación escrita, declaración GitHub docente, previsualización segura, canje OAuth único, checklist, navegación móvil y preferencias de tema válidas/inválidas o sin almacenamiento.

Se comprueban las tres paletas con axe en pantallas de acceso, cursos, inicio, vinculación, personas, repositorios y Perfil, además del desbordamiento a 1920, 1366, 1024 y 390 px. La ampliación al 200 % se comprueba mediante `zoom` CSS en Chromium; no equivale a certificar el zoom nativo en todos los navegadores.

Las pruebas usan Chromium y datos simulados. No se verificaron OAuth real, cookies de producción, permisos reales de proveedores, correo, creación real de repositorios, Safari/Firefox ni proyector físico. Las migraciones se comprobaron únicamente en una base local de pruebas. No se hicieron despliegues, push ni operaciones reales en Canvas/GitHub.
