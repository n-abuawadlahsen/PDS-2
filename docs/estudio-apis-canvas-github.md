# Estudio de APIs — Canvas LMS + GitHub REST
### Proyecto 2 (Web) · ICC4201 Desarrollo de Software · 202620

> Documento de investigación técnica. Mapea **cada requisito del enunciado** a los
> endpoints concretos de la API de Canvas y de la API REST de GitHub
> (versión `2026-03-10`), con ejemplos ejecutables, decisiones de arquitectura y
> los puntos donde la documentación **no** da lo que el enunciado pide.
>
> Fecha: 2026-09-08 · Entrega parcial: mié 16-sep 13:30 · Entrega final: mar 6-oct 16:00

---

## 0. Resumen ejecutivo

**¿Se puede hacer todo lo que pide el enunciado con estas dos APIs? Sí, con tres excepciones que hay que resolver por diseño, no por API.**

| # | Problema | Por qué | Solución adoptada |
|---|---|---|---|
| 1 | **Canvas no tiene webhooks** en la API pública | Live Events / Canvas Data requieren configuración de administrador de la instancia | *Polling* incremental con `updated_at` + `include[]=all_dates,overrides`. Ver §7.4 |
| 2 | **No existe un mapeo Canvas→GitHub** | Son dos universos de identidad distintos | Recolección vía **tarea de Canvas** (los estudiantes entregan su usuario) + validación contra `GET /users/{username}`. Ver §6 |
| 3 | **Las "versiones de entrega" no son un objeto de GitHub** | Git no tiene "snapshot en fecha X" | Guardar el **SHA** en tu BD (fuente de verdad) + crear un **tag inmutable** `refs/tags/entrega-N` por conveniencia. Ver §8 |

**Modelo de autenticación recomendado**

- **Canvas** → OAuth2 *authorization code* con una *Developer Key* de la institución; el token del **profesor** es el que actúa. Tokens de 1 hora + `refresh_token`.
- **GitHub** → **GitHub App** instalada en la organización del curso. Es la única opción que da: token acotado a la org, *rate limit* alto, webhooks incluidos, y que no depende del PAT personal de un profesor.
- **Login de la app** → Google OAuth restringido a `hd`/dominio `gmail.com` (requisito 2.1.2).

**Los 3 riesgos que más proyectos rompen**

1. Pedir permiso `admin` a los estudiantes sobre su repo → pueden borrar los tags de entrega. Usar `push`.
2. Hacer el dashboard "en vivo" llamando a GitHub al cargar la página → el enunciado lo prohíbe explícitamente (§2.5) y además te comes el *rate limit*. Hay que **precomputar**.
3. Ignorar `AssignmentOverride` → las fechas por sección y las extensiones individuales (§2.4.2 y 2.4.3) valen puntos y son invisibles si solo lees `assignment.due_at`.

---

## 1. Autenticación — Canvas

### 1.1 Flujo OAuth2 (web application flow)

Canvas usa OAuth2. La app se registra como **Developer Key** (la crea un administrador de la instancia Canvas; en Canvas Cloud lo hace el admin institucional, en open source se genera en Site Admin).

**Paso 1 — Redirigir al usuario:**

```
GET https://<canvas>/login/oauth2/auth
  ?client_id=<CLIENT_ID>
  &response_type=code
  &redirect_uri=https://tuapp.cl/oauth/canvas/callback
  &state=<CSRF_RANDOM>
  &scope=<lista de scopes separados por espacio>
```

- `state` es obligatorio en la práctica (protección CSRF); guárdalo en sesión y valídalo al volver.
- `scope` es opcional: si la Developer Key tiene *"enforce scopes"* activado, **debes** enumerar cada scope. Los scopes de Canvas tienen la forma `url:GET|/api/v1/courses` (ver §1.3).

**Paso 2 — Canvas redirige de vuelta:**

```
https://tuapp.cl/oauth/canvas/callback?code=XXX&state=YYY
# o, si el usuario rechaza:
https://tuapp.cl/oauth/canvas/callback?error=access_denied&error_description=...&state=YYY
```

**Paso 3 — Canjear el code por tokens:**

```bash
curl -X POST 'https://<canvas>/login/oauth2/token' \
  -d 'grant_type=authorization_code' \
  -d 'client_id=<CLIENT_ID>' \
  -d 'client_secret=<CLIENT_SECRET>' \
  -d 'redirect_uri=https://tuapp.cl/oauth/canvas/callback' \
  -d 'code=XXX'
```

```json
{
  "access_token": "1/fFAGRNJru1FTz70BzhT3Zg",
  "token_type": "Bearer",
  "user": { "id": 42, "name": "Profesor Ejemplo", "global_id": "10000000000042" },
  "refresh_token": "tIh2YBWGiC0GgGRglT9Ylwv2MnTvy8csfGyfK2PYK...",
  "expires_in": 3600
}
```

> ⚠️ El `code` es de **un solo uso**. `replace_tokens=1` invalida tokens previos del mismo usuario.

**Paso 4 — Usar el token:**

```bash
curl -H 'Authorization: Bearer <ACCESS_TOKEN>' \
     'https://<canvas>/api/v1/courses'
```

(También se acepta `?access_token=` en query string, pero **no lo uses**: queda en logs y en el historial.)

**Paso 5 — Refrescar (el access token dura 1 hora):**

```bash
curl -X POST 'https://<canvas>/login/oauth2/token' \
  -d 'grant_type=refresh_token' \
  -d 'client_id=<CLIENT_ID>' \
  -d 'client_secret=<CLIENT_SECRET>' \
  -d 'refresh_token=<REFRESH_TOKEN>'
```

Devuelve un **nuevo `access_token`** pero **el mismo `refresh_token`** (no se rota). Guarda el `refresh_token` cifrado en BD; es lo que permite que los *jobs* nocturnos (informe diario, snapshots de cierre) funcionen sin el profesor conectado. **Esto es crítico**: sin refresh token guardado, el requisito 2.6.1 (informe diario) y el 2.4.5 (snapshot automático a la hora de cierre) no funcionan de madrugada.

**Logout / revocación:**

```bash
curl -X DELETE 'https://<canvas>/login/oauth2/token' -H 'Authorization: Bearer <TOKEN>'
```

### 1.2 Tokens manuales (para desarrollo)

Un usuario puede generar un token en `Account → Settings → New Access Token`. Sirve para desarrollar y para la demo del 16-sep si no consiguen Developer Key a tiempo.

> ⚠️ La documentación es explícita: *"asking any other user to manually generate a token and enter it into your application is a violation of Canvas' API Policy"*. O sea: pueden usar **su propio** token para desarrollo, pero la app entregada debe implementar OAuth2. **Impleméntenlo igual** aunque en la demo usen un token pegado a mano — es un punto de evaluación fácil de perder.

**Plan B recomendado:** si la universidad no les da Developer Key, usen **Free-for-Teacher** (`canvas.instructure.com`), donde ustedes son admin de su propia cuenta y pueden crear la Developer Key, cargar estudiantes de prueba, secciones y grupos. Es el entorno más realista para la demo.

### 1.3 Scopes

Cada endpoint documenta su scope con el formato `url:<METHOD>|<path>`. Ejemplos reales que van a necesitar:

```
url:GET|/api/v1/courses
url:GET|/api/v1/courses/:course_id/users
url:GET|/api/v1/courses/:course_id/enrollments
url:GET|/api/v1/courses/:course_id/sections
url:GET|/api/v1/courses/:course_id/group_categories
url:GET|/api/v1/group_categories/:group_category_id/groups
url:GET|/api/v1/groups/:group_id/users
url:GET|/api/v1/courses/:course_id/assignments
url:GET|/api/v1/courses/:course_id/assignments/:assignment_id/overrides
url:GET|/api/v1/courses/:course_id/assignments/:assignment_id/submissions
url:PUT|/api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id
url:GET|/api/v1/courses/:course_id/rubrics
url:POST|/api/v1/conversations
url:POST|/api/v1/courses/:course_id/discussion_topics
```

### 1.4 Paginación

Canvas pagina con el header `Link` (RFC 5988):

```
Link: <https://<canvas>/api/v1/courses/1/users?page=2&per_page=100>; rel="next",
      <https://<canvas>/api/v1/courses/1/users?page=1&per_page=100>; rel="current",
      <https://<canvas>/api/v1/courses/1/users?page=1&per_page=100>; rel="first"
```

`rel` posibles: `current`, `next`, `prev`, `first`, `last`. La primera página no trae `prev`.

Reglas de la documentación:
- El **default es 10 ítems**. Siempre manden `per_page=100`.
- *"These links should be treated as opaque"* — sigan el `next` tal cual, **no construyan la URL a mano**.
- Los nombres de header son *case-insensitive*: no parseen `Link` de forma sensible a mayúsculas.

```python
import requests

def canvas_paginate(url, token, params=None):
    """Itera todas las páginas siguiendo el header Link."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {**(params or {}), "per_page": 100}
    while url:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        yield from r.json()
        url = r.links.get("next", {}).get("url")   # requests parsea Link solo
        params = None                              # el next ya trae todo
```

### 1.5 Throttling (§ crítico para el sync)

Canvas usa un *leaky bucket* por token:

| Header | Significado |
|---|---|
| `X-Request-Cost` | Costo (float) que descontó esta request de tu cuota |
| `X-Rate-Limit-Remaining` | Cuota restante |

- Al agotarla: **`403 Forbidden (Rate Limit Exceeded)`** (la doc actual también menciona `429`; manejen **ambos**).
- Las requests **en paralelo** pagan una *pre-flight penalty* adicional que se reembolsa al terminar.
- Cita textual: *"Any API client that makes no more than one simultaneous request is unlikely to be throttled"*.
- Cada **access token tiene su propia cuota** → un profesor no afecta a otro.

**Implicación de diseño:** el worker de sincronización de Canvas debe ser **secuencial por curso** (concurrencia 1 por token), con *backoff* exponencial ante 403/429. No hagan `Promise.all` sobre 40 estudiantes.

---

## 2. Autenticación — GitHub

### 2.1 Por qué GitHub App y no PAT

| Opción | Rate limit | Problemas |
|---|---|---|
| PAT clásico / fine-grained | 5.000 req/h **por usuario** | Atado a una persona; si el profesor lo revoca o se va, todo muere. Mala práctica evidente en la corrección. |
| OAuth App | 5.000 req/h | Actúa como el usuario; mismo problema. |
| **GitHub App** ✅ | 5.000 base, **+50 req/h por repo sobre 20** y **+50 req/h por usuario sobre 20**, tope **12.500 req/h** (15.000 si la org es Enterprise Cloud) | Requiere firmar JWT. Es lo correcto. |

Con un curso de 60 estudiantes y 60 repos, la fórmula te da bastante más que 5.000 req/h. Esto importa de verdad cuando sincronizas commits de 60 repos.

### 2.2 Flujo de autenticación de la App

**Paso 1 — Generar un JWT** firmado con la clave privada `.pem` de la App (RS256):

```javascript
import jwt from "jsonwebtoken";

function appJWT(appId, privateKey) {
  const now = Math.floor(Date.now() / 1000);
  return jwt.sign(
    {
      iat: now - 60,        // 60s de margen por clock skew
      exp: now + 9 * 60,    // máximo 10 minutos
      iss: appId,           // App ID (o client_id)
    },
    privateKey,
    { algorithm: "RS256" }
  );
}
```

**Paso 2 — Obtener el `installation_id`** de la organización del curso:

```bash
curl -H "Accept: application/vnd.github+json" \
     -H "Authorization: Bearer <JWT>" \
     -H "X-GitHub-Api-Version: 2026-03-10" \
     https://api.github.com/orgs/ORG/installation
```

Otras rutas útiles: `GET /app/installations` (todas), `GET /repos/{owner}/{repo}/installation`, `GET /users/{username}/installation`. Si estás respondiendo un webhook, el `installation.id` viene en el payload.

**Paso 3 — Canjear por un installation access token:**

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <JWT>" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/app/installations/INSTALLATION_ID/access_tokens \
  -d '{"repositories":["icc4201-t1-jperez"],"permissions":{"contents":"write"}}'
```

- Body opcional: `repositories` / `repository_ids` (hasta **500**) y `permissions` (nunca puede exceder los permisos concedidos a la App).
- **El token expira en 1 hora.** Cachéalo con TTL de ~50 min.

**Paso 4 — Usarlo:**

```bash
curl -H "Authorization: Bearer <INSTALLATION_TOKEN>" \
     -H "X-GitHub-Api-Version: 2026-03-10" \
     https://api.github.com/orgs/ORG/repos
```

**Con Octokit (recomendado, maneja la renovación solo):**

```javascript
import { App } from "octokit";

const app = new App({ appId: APP_ID, privateKey: PRIVATE_KEY });
const octokit = await app.getInstallationOctokit(INSTALLATION_ID);

await octokit.request("POST /orgs/{org}/repos", {
  org: "icc4201-2026",
  name: "icc4201-t1-jperez",
  private: true,
  auto_init: false,
});
```

### 2.3 Permisos que debe pedir la GitHub App

| Ámbito | Permiso | Nivel | Para qué (requisito) |
|---|---|---|---|
| Repositorio | **Administration** | write | Crear repos, agregar/quitar colaboradores (2.3.7, 2.3.9) |
| Repositorio | **Contents** | write | Archivos del repo base, crear tags de entrega (2.3.6, 2.4.5) |
| Repositorio | **Metadata** | read | Obligatorio; listar repos, estadísticas (2.5) |
| Repositorio | **Webhooks** | write | Solo si crean hooks por repo (mejor usar el webhook de la App) |
| Organización | **Members** | write | Invitar estudiantes a la org (opcional, ver §6.4) |
| Organización | **Administration** | write | Crear repos dentro de la org — **verifíquenlo empíricamente**, la doc de fine-grained tokens habla de "Administration" a nivel repositorio |

> 🔎 **Verificar en la práctica.** La doc dice que `POST /orgs/{org}/repos` requiere *"Administration repository permissions (write)"*, lo cual es ambiguo para creación en org. Hagan una prueba temprana (semana 1) creando un repo con la App: si da `403`, suban el permiso de organización. **No dejen esto para el 15 de septiembre.**

### 2.4 Rate limits y cómo no chocarse

**Primarios**

| Identidad | Límite |
|---|---|
| Sin autenticar | 60 req/h |
| PAT / usuario | 5.000 req/h |
| **Installation de GitHub App** | 5.000 base; +50/h por repo sobre 20; +50/h por usuario sobre 20; **máx. 12.500/h** (15.000 en Enterprise Cloud) |
| OAuth app (client credentials, datos públicos) | 5.000/h (15.000 si la org es Enterprise Cloud) |

**Secundarios (los que realmente te van a morder)**

- Máximo **100 requests concurrentes**.
- Máximo **900 puntos por minuto** en REST: `GET`/`HEAD`/`OPTIONS` = **1 punto**; `POST`/`PATCH`/`PUT`/`DELETE` = **5 puntos**.
- Contenido: **80 requests generadoras de contenido por minuto** y **500 por hora**.

> 🚨 **Esto define el diseño del creador masivo de repos (2.3.7 y 2.3.10).** Crear un repo (5 pts) + agregar 3 colaboradores (15 pts) + subir 4 archivos (20 pts) = 40 puntos por grupo. Con 20 grupos = 800 puntos. Cabe en un minuto por los pelos, pero el límite de **80 content-creating requests/min** lo revienta. **Encolar con throttle de ~1 repo cada 3–5 segundos** y estado persistido. Esto además calza perfecto con el requisito 2.3.10 ("crear progresivamente, de forma automática, sin interacción de un usuario").

**Headers de respuesta:** `x-ratelimit-limit`, `x-ratelimit-remaining`, `x-ratelimit-reset` (epoch UTC), y `retry-after` cuando aplica.

**Manejo correcto:**

```javascript
async function ghRequest(octokit, route, params, attempt = 0) {
  try {
    return await octokit.request(route, params);
  } catch (err) {
    const retryAfter = err.response?.headers?.["retry-after"];
    const remaining  = err.response?.headers?.["x-ratelimit-remaining"];
    const reset      = err.response?.headers?.["x-ratelimit-reset"];

    if ((err.status === 403 || err.status === 429) && attempt < 5) {
      let waitMs;
      if (retryAfter) waitMs = Number(retryAfter) * 1000;          // límite secundario
      else if (remaining === "0") waitMs = (Number(reset) * 1000) - Date.now(); // primario
      else waitMs = 2 ** attempt * 1000;                           // backoff genérico
      await new Promise(r => setTimeout(r, Math.max(waitMs, 1000)));
      return ghRequest(octokit, route, params, attempt + 1);
    }
    throw err;
  }
}
```

> 💡 **Truco que vale oro para el sync:** las *conditional requests* con `ETag` / `If-None-Match` que devuelven **`304 Not Modified` no descuentan del rate limit primario**. Guarden el `etag` de cada `GET /repos/.../commits` y mándenlo de vuelta. Con 60 repos poleados cada 10 minutos, esto es la diferencia entre funcionar y no funcionar.

### 2.5 Paginación GitHub

Igual que Canvas: header `link` con `rel="next"` / `rel="last"`. `per_page` máx **100**, default 30.

```javascript
// Octokit lo resuelve solo:
const commits = await octokit.paginate("GET /repos/{owner}/{repo}/commits", {
  owner, repo, since: lastSync, per_page: 100,
});
```

Manualmente:

```javascript
const nextPattern = /(?<=<)([\S]*)(?=>; rel="next")/i;
// ...leer response.headers.link y repetir mientras incluya rel="next"
```

Algunos endpoints usan cursores (`before`/`after`) o `since` en vez de `page`.

---

## 3. Requisito 2.1 — Cursos y usuarios

### 3.1 Registro con cuenta gmail.com (2.1.2)

No es Canvas ni GitHub: es **Google OAuth 2.0 / OpenID Connect**. Al validar el `id_token`, exijan que el claim `email` termine en `@gmail.com` y que `email_verified === true`. (Si usaran Google Workspace, el claim `hd` daría el dominio; para `gmail.com` puro `hd` no viene, así que validen el sufijo del email.)

### 3.2 Vincular el curso de la app con un curso de Canvas (2.1.4)

**Listar los cursos donde el usuario es profesor:**

```bash
curl -H 'Authorization: Bearer <TOKEN>' \
  'https://<canvas>/api/v1/courses?enrollment_type=teacher&enrollment_state=active&include[]=term&include[]=total_students&per_page=100'
```

| Parámetro | Valores |
|---|---|
| `enrollment_type` | `teacher`, `student`, `ta`, `observer`, `designer` |
| `enrollment_state` | `active`, `invited_or_pending`, `completed` |
| `state[]` | `unpublished`, `available`, `completed`, `deleted` |
| `include[]` | `term`, `total_students`, `sections`, `teachers`, `account`, `concluded`, `course_image`, `syllabus_body`, … |

Campos relevantes del objeto `Course`: `id`, `name`, `course_code`, `sis_course_id`, `workflow_state`, `start_at`, `end_at`, `enrollment_term_id`, `total_students`.

**Guarden en su BD:** `canvas_course_id`, `canvas_base_url` (la instancia varía), `course_code`, y el `id` del profesor que hizo la vinculación.

### 3.3 Vincular con una organización de GitHub (2.1.5)

Flujo recomendado, que además cumple el 2.1.6 (*"guiar al profesor y permitir verificar que la configuración es correcta"*):

1. El profesor pulsa **"Conectar organización"** → lo mandan a
   `https://github.com/apps/<tu-app>/installations/new` (pantalla de instalación de la GitHub App).
2. GitHub redirige al `setup_url` con `?installation_id=...&setup_action=install`.
3. La app guarda el `installation_id` y consulta `GET /orgs/{org}/installation` para confirmar.

**Pantalla de verificación (esto es literalmente lo que pide 2.1.6):** ejecuten y muestren en verde/rojo:

| Chequeo | Llamada |
|---|---|
| La org existe y la App está instalada | `GET /orgs/{org}/installation` → 200 |
| Podemos crear repos | `POST /orgs/{org}/repos` con un repo `--verificacion-temporal` → 201, luego `DELETE /repos/{org}/{repo}` |
| Podemos invitar colaboradores | permisos `Administration: write` presentes en la instalación |
| El curso de Canvas responde | `GET /api/v1/courses/{id}` → 200 |
| Vemos estudiantes | `GET /api/v1/courses/{id}/users?enrollment_type[]=student` → n > 0 |
| Vemos secciones | `GET /api/v1/courses/{id}/sections` → n ≥ 1 |
| Vemos tareas | `GET /api/v1/courses/{id}/assignments` → n ≥ 0 |
| Podemos publicar anuncios | permiso del token del profesor |

Esa tabla, renderizada con ✅/❌ y un botón "reintentar", es un punto de usabilidad barato y muy visible en la corrección del 16-sep.

### 3.4 Profesores y ayudantes (2.1.7 – 2.1.9)

**Esto vive en la BD de ustedes, no en Canvas.** El enunciado dice *"administrar sus permisos dentro de la aplicación (uds. deben definir los permisos, mínimo 3)"*.

Propuesta de permisos (≥3, granular y defendible en la actividad de validación del 7-oct):

| Permiso | Descripción | Profesor | Ayudante jefe | Ayudante |
|---|---|---|---|---|
| `course.manage` | Editar curso, vinculaciones, invitar personas | ✅ | — | — |
| `assignment.manage` | Crear/editar tareas y repos base | ✅ | ✅ | — |
| `repo.provision` | Disparar/reintentar creación de repositorios | ✅ | ✅ | — |
| `grading.assign` | Asignar entregas a correctores | ✅ | ✅ | — |
| `grading.submit` | Publicar notas en Canvas | ✅ | ✅ | ✅ (solo asignadas) |
| `student.communicate` | Enviar mensajes/anuncios por Canvas | ✅ | ✅ | — |
| `report.subscribe` | Suscribirse al informe diario | ✅ | ✅ | ✅ |

**Nota de coherencia:** que un ayudante exista en su app **no** implica que exista en Canvas. Para que un ayudante pueda publicar notas (2.7.6) necesita un token de Canvas con permiso sobre el curso, o sea debe tener un `TaEnrollment` en Canvas. Dos caminos:

- **A (simple y robusto):** todas las escrituras a Canvas se hacen con el token del **profesor** (la app actúa "en nombre del curso"). El ayudante opera en la app; la app usa el token del profesor. Documenten esta decisión.
- **B (correcto pero frágil):** cada ayudante hace su propio OAuth con Canvas y la app usa su token. Requiere que estén enrolados como TA en Canvas.

Recomendación: **A** como default, **B** como *fallback* si el token del profesor está expirado. Y muéstrenlo en la UI ("las notas se publican como *Profesor X*").

**Retirar un ayudante (2.1.9):** además de borrar el rol en su BD, reasignen las entregas que tenía pendientes y revoquen su acceso a la org de GitHub si se lo dieron (`DELETE /orgs/{org}/memberships/{username}`).

---

## 4. Requisito 2.2 — Estudiantes, secciones y grupos (Canvas)

### 4.1 Estudiantes inscritos (2.2.1)

Dos endpoints, y conviene usar **los dos**:

**a) Vista "usuarios":**

```bash
curl -H 'Authorization: Bearer <TOKEN>' \
 'https://<canvas>/api/v1/courses/<course_id>/users?enrollment_type[]=student&enrollment_state[]=active&include[]=enrollments&include[]=avatar_url&per_page=100'
```

Rutas equivalentes: `GET /api/v1/courses/:course_id/users` y `GET /api/v1/courses/:course_id/search_users`.

| Parámetro | Valores |
|---|---|
| `search_term` | nombre parcial o ID completo |
| `sort` | `username`, `last_login`, `email`, `sis_id` |
| `enrollment_type[]` | `teacher`, `student`, `student_view`, `ta`, `observer`, `designer` |
| `enrollment_role_id` | rol específico del curso |
| `include[]` | `enrollments`, `locked`, `avatar_url`, `test_student`, `bio`, `custom_links`, `current_grading_period_scores`, `uuid` |
| `user_id` / `user_ids[]` | traer la página que contiene a un usuario / filtrar por IDs |
| `enrollment_state[]` | `active`, `invited`, `rejected`, `completed`, `inactive` |

> ⚠️ **Filtrar el Test Student.** El usuario de "Student View" aparece como `student_view` / `test_student`. Si no lo filtran, van a intentar crearle un repositorio a un estudiante fantasma. No incluyan `include[]=test_student` y filtren `enrollment_type[]=student` explícitamente.

**b) Vista "enrollments" — la que realmente necesitan**, porque trae la sección:

```bash
curl -H 'Authorization: Bearer <TOKEN>' \
 'https://<canvas>/api/v1/courses/<course_id>/enrollments?type[]=StudentEnrollment&state[]=active&per_page=100'
```

```json
{
  "id": 1,
  "course_id": 1,
  "sis_course_id": "SHEL93921",
  "course_section_id": 1,
  "sis_section_id": "SHEL93921",
  "sis_user_id": "SHEL93921",
  "enrollment_state": "active",
  "type": "StudentEnrollment",
  "user_id": 1,
  "role": "StudentEnrollment",
  "role_id": 1,
  "user": { "id": 3, "name": "Student 1", "sortable_name": "1, Student", "short_name": "Stud 1" },
  "grades": { "current_score": 35, "final_score": 6.67 }
}
```

Parámetros: `type[]` (`StudentEnrollment`, `TeacherEnrollment`, `TaEnrollment`, `DesignerEnrollment`, `ObserverEnrollment`), `state[]` (`active`, `invited`, `creation_pending`, `deleted`, `rejected`, `completed`, `inactive`, `current_and_invited`, `current_and_future`, …), `include[]` (`avatar_url`, `group_ids`, `locked`, `can_be_removed`, `uuid`, `current_points`).

> 💡 `include[]=group_ids` te da los grupos del estudiante en la **misma llamada**. Úsalo.

Otros endpoints del recurso: `GET /api/v1/sections/:section_id/enrollments`, `GET /api/v1/users/:user_id/enrollments`, `POST /api/v1/courses/:course_id/enrollments`, `DELETE /api/v1/courses/:course_id/enrollments/:id`, `PUT .../reactivate`.

### 4.2 Secciones (2.2.2)

```bash
curl -H 'Authorization: Bearer <TOKEN>' \
 'https://<canvas>/api/v1/courses/<course_id>/sections?include[]=total_students&per_page=100'
```

Endpoints del recurso Sections:

| Método | Path |
|---|---|
| GET | `/api/v1/courses/:course_id/sections` |
| POST | `/api/v1/courses/:course_id/sections` |
| GET | `/api/v1/courses/:course_id/sections/:id` · `/api/v1/sections/:id` |
| PUT | `/api/v1/sections/:id` |
| DELETE | `/api/v1/sections/:id` |
| GET | `/api/v1/sections/:id/users` |
| POST | `/api/v1/sections/:id/crosslist/:new_course_id` |
| DELETE | `/api/v1/sections/:id/crosslist` |

Campos: `id`, `name`, `sis_section_id`, `course_id`, `start_at`, `end_at`, `restrict_enrollments_to_section_dates`, `nonxlist_course_id`, `total_students`.
`include[]`: `students`, `avatar_url`, `enrollments`, `total_students`, `passback_status`, `permissions`.

> ⚠️ **Un estudiante puede estar en más de una sección.** Su modelo de datos debe soportar N:M entre estudiante y sección, o al menos manejar el caso al calcular fechas efectivas (§7.3). Y `restrict_enrollments_to_section_dates` cambia qué fechas aplican.

### 4.3 Grupos (2.2.3)

En Canvas los grupos viven en **Group Categories** (los "group sets"). Una *assignment* grupal apunta a un `group_category_id`.

**Categorías del curso:**

```bash
GET /api/v1/courses/:course_id/group_categories
# param: collaboration_state = all | collaborative | non_collaborative
```

Campos de `GroupCategory`: `id`, `name`, `role`, `self_signup` (`enabled`/`restricted`/null), `auto_leader`, `context_type`, `course_id`, `group_limit`, `sis_group_category_id`, `non_collaborative`.

**Grupos de una categoría:**

```bash
GET /api/v1/group_categories/:group_category_id/groups
GET /api/v1/group_categories/:group_category_id/users   # params: search_term (≥3), unassigned=true
GET /api/v1/courses/:course_id/groups                   # todos los grupos visibles del curso
GET /api/v1/groups/:group_id
GET /api/v1/groups/:group_id/users
GET /api/v1/groups/:group_id/memberships
```

Campos de `Group`: `id`, `name`, `description`, `group_category_id`, `members_count`, `context_type`, `course_id`, `is_public`, `join_level`, `is_full`.

> 💡 `GET /api/v1/group_categories/:id/users?unassigned=true` es **exactamente** lo que necesitan para el requisito 2.2.6 ("mostrar estudiantes o grupos para los cuales falta información"): les da los estudiantes sin grupo asignado, que son los que van a quedar sin repositorio.

### 4.4 Estrategia de sincronización

```python
def sync_course(course):
    sections   = list(paginate(f"/courses/{course.id}/sections"))
    enrollments= list(paginate(f"/courses/{course.id}/enrollments",
                               {"type[]":"StudentEnrollment","state[]":"active",
                                "include[]":"group_ids"}))
    categories = list(paginate(f"/courses/{course.id}/group_categories"))
    groups     = {c["id"]: list(paginate(f"/group_categories/{c['id']}/groups"))
                  for c in categories}
    # upsert por canvas_id; marcar como 'retirado' lo que ya no viene (no borrar)
```

**Reglas de oro:**
- **Nunca borren** filas al sincronizar: marquen `deleted_at`. Un estudiante que se retira sigue teniendo un repo con historia.
- Guarden `canvas_user_id` como clave estable; el nombre y el email cambian.
- Registren `last_synced_at` y muéstrenlo en la UI ("datos de Canvas actualizados hace 4 min") — es usabilidad gratis.

---

## 5. Requisito 2.3 — Tareas, repositorio base y creación de repos

### 5.1 Leer tareas de Canvas (2.3.1 – 2.3.3)

```bash
curl -H 'Authorization: Bearer <TOKEN>' \
 'https://<canvas>/api/v1/courses/<course_id>/assignments?include[]=all_dates&include[]=overrides&per_page=100'
```

Endpoints del recurso Assignments:

| Método | Path |
|---|---|
| GET | `/api/v1/courses/:course_id/assignments` |
| GET | `/api/v1/courses/:course_id/assignment_groups/:assignment_group_id/assignments` |
| GET | `/api/v1/users/:user_id/courses/:course_id/assignments` |
| GET | `/api/v1/courses/:course_id/assignments/:id` |
| POST | `/api/v1/courses/:course_id/assignments` |
| PUT | `/api/v1/courses/:course_id/assignments/:id` |
| DELETE | `/api/v1/courses/:course_id/assignments/:id` |
| POST | `/api/v1/courses/:course_id/assignments/:assignment_id/duplicate` |

`include[]`: `submission`, `assignment_visibility`, `all_dates`, `overrides`, `observed_users`, `can_edit`, `score_statistics`, `ab_guid`, `peer_review`, `academic_integrity_pledge`.

**Campos que deciden todo tu modelo:**

| Campo | Uso en el proyecto |
|---|---|
| `id`, `name`, `html_url` | identidad y link a Canvas |
| `due_at`, `lock_at`, `unlock_at` | fecha base (2.4.1) |
| `all_dates[]` | array de `AssignmentDate`, uno por override → **la lista completa de fechas** |
| `overrides[]` | objetos `AssignmentOverride` completos |
| `only_visible_to_overrides` | si es `true`, la fecha base **no aplica a nadie** |
| **`group_category_id`** | **`null` ⇒ tarea individual; con valor ⇒ tarea grupal** (2.3.3) |
| `grade_group_students_individually` | si `false`, la nota se propaga a todo el grupo (2.7.6) |
| `published` | no creen repos para tareas no publicadas |
| `submission_types` | útil para la tarea de recolección de usuarios GitHub (§6) |
| `updated_at` | **clave para el polling incremental** (2.4.4) |

### 5.2 Modelo de datos: Tarea (app) → 1..N entregas (Canvas)

El enunciado (2.3.1, 2.3.2) pide explícitamente esta relación. Modelo mínimo:

```
Assignment (app)            -- "la tarea"
  id, course_id, name, slug
  is_group (bool)           -- derivado de group_category_id
  group_category_id (null si individual)
  base_repo_full_name (nullable, 2.3.5)
  repo_name_template

Delivery (app)              -- "la entrega"
  id, assignment_id
  canvas_assignment_id      -- 1:1 con una tarea de Canvas
  kind: 'partial' | 'final'
  order_index
  snapshot_status

Repository (app)
  id, assignment_id
  owner_kind: 'student' | 'group'
  canvas_user_id | canvas_group_id
  github_full_name, github_repo_id, default_branch
  state: PENDING_MAPPING | QUEUED | CREATING | CREATED |
         COLLABORATORS_PENDING | READY | ERROR
  last_error, created_at

DeliverySnapshot (app)
  delivery_id, repository_id
  effective_due_at         -- ¡por estudiante/grupo! (§7.3)
  commit_sha, committed_at, tag_name
  captured_at, status
```

**Validación obligatoria (2.3.3):** *"todas las entregas asociadas a una misma tarea deben tener la misma configuración"*. Al vincular una segunda tarea de Canvas, comparen su `group_category_id` con el de la primera y **rechacen** con un mensaje claro si difieren. Ese chequeo es visible y suma en usabilidad.

### 5.3 Repositorio base (2.3.5, 2.3.6)

**Crearlo como *template repository*** — así el 2.3.7 se vuelve una sola llamada por estudiante.

```bash
# 1) Crear el repo base en la org
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <INSTALLATION_TOKEN>" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/orgs/ORG/repos \
  -d '{"name":"icc4201-t1-base","description":"Repositorio base Tarea 1","private":true,"auto_init":true}'
```

Parámetros de `POST /orgs/{org}/repos`: `name` (requerido), `description`, `private` (default `false`), `visibility` (`public`/`private`), `auto_init` (*"Pass `true` to create an initial commit with empty README"*), `team_id`, `gitignore_template`.
Permiso fine-grained: **Administration (write)**.

> ⚠️ **`auto_init: true` es importante.** Un repo vacío no tiene commits, y `POST /git/refs` no puede crear referencias en repos vacíos. Sin commit inicial, ni el template ni los tags funcionan.

```bash
# 2) Marcarlo como template
curl -X PATCH \
  -H "Authorization: Bearer <INSTALLATION_TOKEN>" \
  https://api.github.com/repos/ORG/icc4201-t1-base \
  -d '{"is_template":true}'
```

**Subir los archivos iniciales (2.3.6):**

```bash
curl -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <INSTALLATION_TOKEN>" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/repos/ORG/icc4201-t1-base/contents/README.md \
  -d '{
        "message":"Agrega enunciado",
        "content":"IyBUYXJlYSAxCg==",
        "branch":"main",
        "committer":{"name":"ICC4201 Bot","email":"bot@icc4201.cl"}
      }'
```

`PUT /repos/{owner}/{repo}/contents/{path}`:

| Parámetro | Notas |
|---|---|
| `message` | requerido |
| `content` | requerido, **base64** |
| `sha` | **requerido al actualizar** un archivo existente (blob SHA actual) |
| `branch` | default: rama por defecto |
| `committer` / `author` | `{name, email}` |

Permiso: **Contents (write)** (o Contents + Workflows write si suben archivos en `.github/workflows/`).
Respuestas: `200` OK, `201` creado, `409` conflicto, `422` validación.
Advertencia de la doc: *"If you use this endpoint and the Delete endpoint in parallel, concurrent requests will conflict"* → suban archivos **en serie**.

**Límites de tamaño de `GET /contents`:** ≤1 MB todo funciona; 1–100 MB solo `raw`/`object` (el campo `content` viene vacío con `encoding:"none"`); >100 MB no soportado. Para el repo base eso basta; si necesitan subir algo grande, usen la Git Data API (blobs → tree → commit).

**UI recomendada:** un explorador de archivos del repo base dentro de la app (listar con `GET /contents`, editar en un textarea, subir con `PUT`), más un botón "abrir en GitHub". Cumple 2.3.6 sin salir de la app.

### 5.4 Crear los repos de estudiantes/grupos (2.3.7 – 2.3.10)

**Con repo base (template):**

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <INSTALLATION_TOKEN>" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/repos/ORG/icc4201-t1-base/generate \
  -d '{
        "owner":"ORG",
        "name":"icc4201-2026-t1-jperez",
        "description":"Tarea 1 — Juan Pérez (Sección 2)",
        "private":true,
        "include_all_branches":false
      }'
```

`POST /repos/{template_owner}/{template_repo}/generate` — params: `owner`, `name`, `description`, `include_all_branches`, `private`. El repo plantilla debe tener `is_template: true`.

**Sin repo base** (el enunciado dice que el repo base es *opcional*): `POST /orgs/{org}/repos` con `auto_init: true`.

**Nombres automáticos e inequívocos (2.3.8).** Requisitos: únicos en la org, estables, legibles, y que no filtren datos sensibles.

```
Individual:  {curso}-{periodo}-{tarea}-{githublogin}
             icc4201-2026-2-t1-jperez

Grupal:      {curso}-{periodo}-{tarea}-g{canvas_group_id}-{slug_grupo}
             icc4201-2026-2-t1-g8842-los-punteros
```

Incluir el `canvas_group_id` garantiza unicidad aunque dos grupos se llamen igual. Sanitizar: minúsculas, `[^a-z0-9-]` → `-`, colapsar guiones, truncar a 100 chars, y ante colisión (`422`) reintentar con sufijo `-2`.

**Agregar a los estudiantes (2.3.9):**

```bash
curl -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <INSTALLATION_TOKEN>" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/repos/ORG/icc4201-2026-2-t1-jperez/collaborators/jperez \
  -d '{"permission":"push"}'
```

`PUT /repos/{owner}/{repo}/collaborators/{username}` — `permission`: `pull`, `triage`, `push`, `maintain`, `admin`.

> 🚨 **Usen `push`, NUNCA `admin`.** Con `admin` el estudiante puede **borrar tags** (destruye la evidencia de la entrega, requisito 2.4.7), cambiar la visibilidad del repo, o eliminarlo. Con `push` puede hacer todo el trabajo normal.

Semántica de la respuesta, importante para su máquina de estados:

| Código | Significado |
|---|---|
| `201` | Se creó una **invitación** (el usuario no es miembro de la org) → estado *pendiente* |
| `204` | Se agregó/actualizó directo (ya era miembro de la org o ya era colaborador) |

Para org-owned repos, si el usuario no es miembro de la organización se agrega como **outside collaborator** y **debe aceptar la invitación por email**. Eso significa que "repo creado" ≠ "estudiante tiene acceso".

**Monitorear invitaciones pendientes (esto es el requisito 2.3.11 y 2.2.6):**

```bash
GET /repos/{owner}/{repo}/invitations
```

Devuelve `id`, `invitee`, `permissions`, `created_at`, `expired`. También: `PATCH /repos/{owner}/{repo}/invitations/{invitation_id}` (cambiar permiso) y `DELETE .../invitations/{invitation_id}` (revocar, útil para reenviar).

Otros: `GET /repos/{owner}/{repo}/collaborators`, `DELETE /repos/{owner}/{repo}/collaborators/{username}`.

**Alternativa con Teams** (más limpia para grupos grandes, más llamadas):

```bash
POST /orgs/{org}/teams
  {"name":"t1-g8842","privacy":"closed"}
PUT  /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}
  {"permission":"push"}
```

Permisos para el segundo: Administration repo (write) + Members org (read) + Metadata repo (read). Para este proyecto, **colaboradores directos es más simple y suficiente**.

### 5.5 El worker de aprovisionamiento (2.3.10) — el corazón del proyecto

> *"Crear los repositorios progresivamente a medida que se disponga de toda la información requerida para cada estudiante o grupo. Esto debe hacerse de forma automática, sin interacción directa de un usuario."*

Esto **exige un job en background**. No sirve un botón "crear repos".

```
┌────────────────────────────────────────────────────────────┐
│ CRON cada 2 min: provision_repositories()                  │
├────────────────────────────────────────────────────────────┤
│ para cada Assignment activo:                               │
│   sujetos = estudiantes (o grupos) de la tarea             │
│   para cada sujeto sin Repository en estado READY:         │
│     ¿tiene(n) github_login mapeado?                        │
│        no  → state = PENDING_MAPPING; continue             │
│        sí  → encolar job crear_repo(sujeto)                │
└────────────────────────────────────────────────────────────┘

crear_repo(sujeto):   # idempotente, con lock por sujeto
  1. state = CREATING
  2. si base_repo:  POST /repos/{org}/{base}/generate
     si no:         POST /orgs/{org}/repos  (auto_init)
     └ 422 "name already exists" → GET el repo y continuar (idempotencia)
  3. state = CREATED; guardar github_repo_id, default_branch
  4. para cada integrante: PUT .../collaborators/{login}
     └ 201 → invitación pendiente | 204 → acceso inmediato
  5. state = READY si todos 204; COLLABORATORS_PENDING si hay 201
  6. notificar por Canvas (§9.3) → requisito 2.3.12
  7. cualquier excepción → state = ERROR, last_error = msg, reintento con backoff
```

**Throttle:** máximo ~1 repo cada 3 s (recuerden: 80 requests generadoras de contenido por minuto).
**Idempotencia:** un `422` de "ya existe" **no es un error**, es un reintento exitoso. Sin esto, un reinicio del worker deja repos duplicados o el sistema atascado.

### 5.6 Vista de estado de repositorios (2.3.11)

Tabla con una fila por estudiante/grupo y estas columnas — es literalmente el requisito:

| Estudiante/Grupo | Sección | GitHub user | Repo | Colaboradores | Estado | Acción |
|---|---|---|---|---|---|---|
| Juan Pérez | 2 | `jperez` ✅ | `…-t1-jperez` ↗ | 1/1 aceptado | 🟢 Listo | — |
| Grupo 12 | 1 | 2/3 mapeados | — | — | 🟡 Falta usuario de M. Soto | Recordar |
| Ana Díaz | 2 | `adiaz` ✅ | `…-t1-adiaz` ↗ | 0/1 pendiente | 🟡 Invitación sin aceptar | Reenviar |
| Luis Rojas | 1 | `lrojas` ❌ no existe | — | — | 🔴 Error: usuario inválido | Corregir |

Con filtro "solo problemas" y un botón "reintentar todos los fallidos".

### 5.7 Entregar la URL del repo al estudiante (2.3.12)

*"Proporcionar al estudiante, a través de Canvas, la información necesaria para acceder al repositorio."* Dos mecanismos, usen **ambos**:

**a) Comentario en la entrega de Canvas** (contextual, aparece en la tarea):

```bash
curl -X PUT -H 'Authorization: Bearer <CANVAS_TOKEN>' \
 'https://<canvas>/api/v1/courses/<cid>/assignments/<aid>/submissions/<user_id>' \
 -d 'comment[text_comment]=Tu repositorio: https://github.com/ORG/icc4201-2026-2-t1-jperez  (revisa tu correo para aceptar la invitación)' \
 -d 'comment[group_comment]=true'
```

**b) Mensaje directo (Conversation)** — ver §9.3.

---

## 6. El puente que no existe: mapear Canvas ↔ GitHub (2.2.4, 2.2.5)

**No hay ningún endpoint que relacione un usuario de Canvas con uno de GitHub.** Ustedes lo construyen. El enunciado dice: *"Cada grupo deberá definir una estrategia adecuada... Se evaluará la usabilidad de este proceso"*. Es un punto de diseño evaluado, no un detalle.

### 6.1 Estrategia recomendada: tarea de Canvas como formulario

Los estudiantes **no entran a la app** (restricción del enunciado). Pero sí entran a Canvas. Entonces:

1. La app crea (o el profesor vincula) una tarea de Canvas tipo "Registro de usuario GitHub":

```bash
curl -X POST -H 'Authorization: Bearer <TOKEN>' \
 'https://<canvas>/api/v1/courses/<cid>/assignments' \
 -d 'assignment[name]=Registro de usuario GitHub' \
 -d 'assignment[submission_types][]=online_text_entry' \
 -d 'assignment[points_possible]=0' \
 -d 'assignment[published]=true' \
 -d 'assignment[description]=<p>Escribe SOLO tu nombre de usuario de GitHub (ej: jperez). Sin la URL, sin @.</p>'
```

2. La app poletea las entregas:

```bash
GET /api/v1/courses/:cid/assignments/:aid/submissions?include[]=user&per_page=100
```

3. Por cada entrega, extraer el login del `body` (viene como HTML → limpiar tags), normalizar (quitar `@`, quitar `https://github.com/`, trim, lowercase) y **validar contra GitHub**:

```bash
GET https://api.github.com/users/{username}
# 200 → existe (usar el campo `login` canónico de la respuesta, respeta mayúsculas)
# 404 → no existe
```

4. Si es válido → guardar mapeo y **confirmar por comentario en la entrega**. Si no → comentario pidiendo corrección. Ese loop de feedback automático es la parte "usable" del requisito.

```python
import re, html

def parse_github_login(submission_body: str) -> str | None:
    text = html.unescape(re.sub(r"<[^>]+>", " ", submission_body or "")).strip()
    m = re.search(r"(?:github\.com/)?@?([A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)\s*$", text)
    return m.group(1) if m else None

def validate(login, gh):
    r = gh.get(f"/users/{login}")
    if r.status_code == 200 and r.json()["type"] == "User":
        return r.json()["login"]      # login canónico
    return None
```

> ⚠️ **Validar `type == "User"`.** Si un estudiante escribe el nombre de una organización, `GET /users/{org}` también devuelve 200 pero con `type: "Organization"`, y no se puede agregar como colaborador.

**Ventajas:** cero fricción, usa solo Canvas y GitHub, deja registro auditable, y la fecha de entrega de esa tarea sirve de plazo natural.
**Desventaja:** no prueba que el estudiante *sea dueño* de esa cuenta.

### 6.2 Complemento: verificación por OAuth de GitHub (opcional, suma puntos)

Un *magic link* firmado (JWT con `canvas_user_id`, 7 días de vigencia) enviado por Canvas Conversation → el estudiante hace clic → OAuth de GitHub → la app llama `GET /user` con su token y obtiene el `login` **verificado**. El estudiante nunca crea cuenta en la app; solo autoriza en GitHub. Formalmente sigue interactuando "a través de Canvas y GitHub".

### 6.3 Completar progresivamente (2.2.5) y mostrar faltantes (2.2.6)

- **Recordatorio automático:** job diario que envía Canvas Conversation solo a los estudiantes sin mapeo (§9.3).
- **Carga manual del docente:** tabla editable con búsqueda incremental — el ayudante escribe el usuario y la app valida contra GitHub en vivo. Esencial como escape hatch.
- **Import CSV** (`canvas_user_id, github_login`) para casos masivos.
- **Panel de faltantes:** la unión de (estudiantes sin `github_login`) + (grupos con ≥1 integrante sin mapeo) + (`GET /group_categories/:id/users?unassigned=true`, estudiantes sin grupo) + (invitaciones de repo sin aceptar).

### 6.4 Sobre invitar a la organización

Opcional, pero mejora la experiencia: si los estudiantes son **miembros de la org**, `PUT .../collaborators/{username}` devuelve `204` (acceso inmediato) en vez de `201` (invitación pendiente por email). Menos estados que manejar.

```bash
PUT /orgs/{org}/memberships/{username}   -d '{"role":"member"}'
GET /orgs/{org}/memberships/{username}   # state: "pending" | "active"
GET /orgs/{org}/members                  # filter, role
GET /orgs/{org}/members/{username}       # 204 = es miembro, 404 = no
DELETE /orgs/{org}/memberships/{username}
```

Permiso: **Members organization (write)**. Igual hay una invitación que aceptar, pero es una sola por semestre, no una por tarea.

---

## 7. Requisito 2.4 — Fechas, overrides y cierre de entregas

Esta es la sección **más subestimada del enunciado** y la que más fácil se pierde puntos.

### 7.1 AssignmentOverride

Objeto `AssignmentOverride`:

| Campo | Descripción |
|---|---|
| `id` | id del override |
| `assignment_id` | tarea afectada (también `quiz_id`, `context_module_id`, `discussion_topic_id`, `wiki_page_id`, `attachment_id`) |
| `student_ids[]` | override **ADHOC** (extensión individual → requisito 2.4.3) |
| `group_id` | override por grupo |
| `course_section_id` | override por sección (→ requisito 2.4.2) |
| `title` | nombre del override |
| `due_at`, `all_day`, `all_day_date` | fecha de entrega |
| `unlock_at`, `lock_at` | apertura/cierre |

**Endpoints:**

| Método | Path |
|---|---|
| GET | `/api/v1/courses/:course_id/assignments/:assignment_id/overrides` |
| GET | `/api/v1/courses/:course_id/assignments/:assignment_id/overrides/:id` |
| POST | `/api/v1/courses/:course_id/assignments/:assignment_id/overrides` |
| PUT | `/api/v1/courses/:course_id/assignments/:assignment_id/overrides/:id` |
| DELETE | `/api/v1/courses/:course_id/assignments/:assignment_id/overrides/:id` |

Y también, más eficiente: `include[]=all_dates` e `include[]=overrides` en la llamada a assignments, que trae todo en una sola request.

### 7.2 `all_dates` — la forma barata de leerlo todo

```jsonc
// GET /courses/1/assignments/55?include[]=all_dates&include[]=overrides
{
  "id": 55,
  "name": "Tarea 1 — Entrega parcial",
  "due_at": "2026-09-16T16:30:00Z",     // fecha "everyone"
  "lock_at": "2026-09-18T16:30:00Z",
  "only_visible_to_overrides": false,
  "group_category_id": null,
  "all_dates": [
    { "base": true,  "due_at": "2026-09-16T16:30:00Z", "title": "Everyone else" },
    { "id": 901, "base": false, "due_at": "2026-09-17T16:30:00Z", "title": "Sección 2" },
    { "id": 902, "base": false, "due_at": "2026-09-20T16:30:00Z", "title": "1 student" }
  ],
  "overrides": [
    { "id": 901, "course_section_id": 12, "due_at": "2026-09-17T16:30:00Z" },
    { "id": 902, "student_ids": [3345],   "due_at": "2026-09-20T16:30:00Z" }
  ]
}
```

### 7.3 Algoritmo: fecha efectiva por estudiante

```python
from datetime import datetime

def effective_due_at(student, assignment, overrides, student_sections, student_group_id):
    """Devuelve (due_at, origen) para UN estudiante en UNA entrega."""
    # 1) Override ADHOC (estudiante específico) — máxima prioridad
    for o in overrides:
        if student.canvas_id in (o.get("student_ids") or []):
            return o["due_at"], f"extensión individual (override {o['id']})"

    # 2) Override de grupo (solo tareas grupales)
    if student_group_id:
        for o in overrides:
            if o.get("group_id") == student_group_id:
                return o["due_at"], f"grupo (override {o['id']})"

    # 3) Override de sección. Si el estudiante está en varias secciones con
    #    override, Canvas aplica la fecha MÁS TARDÍA (la más permisiva).
    section_dates = [o["due_at"] for o in overrides
                     if o.get("course_section_id") in student_sections and o.get("due_at")]
    if section_dates:
        return max(section_dates, key=parse_iso), "sección"

    # 4) Fecha base — salvo que la tarea sea solo para overrides
    if assignment.get("only_visible_to_overrides"):
        return None, "no visible para este estudiante"
    return assignment.get("due_at"), "fecha general"
```

**Casos borde que sí van a aparecer:**
- `due_at: null` en el override → significa "sin fecha de entrega" para ese target, no "usa la base".
- `only_visible_to_overrides: true` + estudiante sin override → la tarea **no existe** para él; no le creen snapshot ni lo cuenten como atrasado.
- Para un **grupo**, la fecha efectiva del repositorio es ambigua si sus integrantes tienen fechas distintas. **Decisión sugerida: usar `max()` de las fechas efectivas de los integrantes** (nadie pierde trabajo por un compañero con menos plazo) y **mostrar en la UI** que ese repo tiene fechas heterogéneas.

### 7.4 Mantener las fechas actualizadas (2.4.4) — sin webhooks

Canvas **no ofrece webhooks salientes** en la API pública (Live Events y Canvas Data requieren configuración de administrador de la instancia y no van a tenerla). Por lo tanto: **polling**.

```
CRON cada 10 min, por curso activo:
  GET /courses/{cid}/assignments?include[]=all_dates&include[]=overrides&per_page=100
  para cada assignment vinculada:
      si assignment.updated_at > delivery.canvas_updated_at:
          recalcular fechas efectivas de todos los sujetos
          si cambió la fecha de una entrega NO capturada aún:
              reprogramar el job de snapshot
              si el cambio es "relevante" (>1h) y el profesor lo activó:
                  publicar anuncio en Canvas (requisito 2.6.6)
          registrar en un log de auditoría: quién/cuándo/de qué a qué
```

Costo: ~1 request por curso cada 10 min. Trivial para el throttling de Canvas. **Muestren "última sincronización" en la UI** y ofrezcan un botón "sincronizar ahora" — corrige la percepción de datos viejos durante la demo.

### 7.5 Registrar la versión del repo al cierre (2.4.5 – 2.4.7)

> *"Registrar automáticamente, para cada entrega, la versión del repositorio correspondiente a su fecha de cierre"* + *"mantener correctamente las versiones ya registradas aunque posteriormente continúe existiendo actividad"*.

**Concepto:** un snapshot = **un SHA de commit**. Inmutable por definición en Git.

**Paso 1 — encontrar el último commit hasta la fecha de cierre:**

```bash
curl -H "Authorization: Bearer <TOKEN>" \
 'https://api.github.com/repos/ORG/REPO/commits?sha=main&until=2026-09-16T16:30:00Z&per_page=1'
```

`GET /repos/{owner}/{repo}/commits` params: `sha` (rama o SHA de inicio), `path`, `author`, `committer`, `since`, `until` (ISO 8601), `per_page` (máx 100), `page`. El primer resultado es el commit más reciente **en o antes de** `until`.

**Paso 2 — persistir el SHA en la BD.** *Esta es la fuente de verdad.* Un tag se puede borrar; una fila en su base de datos, no.

**Paso 3 — crear un tag inmutable (conveniencia + trazabilidad):**

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <INSTALLATION_TOKEN>" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/repos/ORG/REPO/git/refs \
  -d '{"ref":"refs/tags/entrega-1-cierre","sha":"aa218f56b14c9653891f9e74264a383fa43fefbd"}'
```

Reglas de nombres de referencias: deben empezar con `refs` y tener al menos dos slashes → `refs/heads/<rama>`, `refs/tags/<tag>`. No se pueden crear refs en repos vacíos. Permiso: **Contents (write)**.

Otros endpoints de refs: `GET /repos/{o}/{r}/git/ref/{ref}`, `GET /repos/{o}/{r}/git/matching-refs/{ref}`, `PATCH /repos/{o}/{r}/git/refs/{ref}` (`sha`, `force`), `DELETE /repos/{o}/{r}/git/refs/{ref}`.

**Paso 4 — link directo para el corrector (2.4.8):**

```
https://github.com/ORG/REPO/tree/<SHA>                     # código en esa versión exacta
https://github.com/ORG/REPO/compare/<SHA_entrega1>...<SHA_entrega2>   # diff entre entregas
https://github.com/ORG/REPO/commits/<SHA>                  # historial hasta ahí
```

El `compare` entre entregas parciales es una funcionalidad que el enunciado no pide explícitamente pero que a un corrector le cambia la vida — buen candidato para el 2.5.9 ("otras métricas o visualizaciones").

**Múltiples entregas independientes (2.4.6):** una fila `DeliverySnapshot` por `(delivery_id, repository_id)`, cada una con su SHA y su tag `entrega-1`, `entrega-2`, `entrega-final`. Nunca se sobrescriben.

**Robustez del job de snapshot:**

```
CRON cada 5 min: capture_due_snapshots()
  para cada (delivery, repository) sin snapshot y con effective_due_at <= now():
     commit = GET /repos/../commits?sha={default_branch}&until={effective_due_at}&per_page=1
     si no hay commits  → status = NO_COMMITS  (¡esto es un dato valioso para el informe!)
     si hay             → guardar sha + committed_at; POST /git/refs (tag)
                          si el tag ya existe (422) → verificar que apunte al mismo SHA
     status = CAPTURED
```

> ⚠️ **No dependan de que el proceso esté vivo a la hora exacta.** El job debe barrer *todo lo vencido y no capturado*, no "disparar a las 16:30". Si el servidor estaba caído, al levantarse captura igual — y el resultado es idéntico porque `until` es una fecha histórica.

> 🔒 **Protejan los tags.** Con `push` los estudiantes ya no pueden borrar el repo, pero sí pueden borrar tags. Si quieren blindaje extra, creen una *ruleset* de tags en la org (`POST /orgs/{org}/rulesets` con `target: "tag"`). No es imprescindible si el SHA está en su BD.

---

## 8. Requisito 2.5 — Seguimiento y monitoreo

> *"Esta información deberá encontrarse disponible de forma inmediata al ingresar a la vista de una tarea, **sin requerir esperar a que se recopile en ese momento** la actividad de todos los repositorios."*

Traducción: **la vista lee de su base de datos, nunca de la API de GitHub.** Si en la demo el dashboard tarda 8 segundos porque está llamando a GitHub, perdieron el requisito aunque los datos sean correctos.

### 8.1 Ingesta en tiempo real: webhooks

Con GitHub App, la App recibe eventos de **todos** los repos de la instalación automáticamente — no hay que crear un webhook por repo. Configuren la URL del webhook en la App y suscríbanse a: `push`, `create`, `delete`, `repository`, `member`, `member_invite` (según disponibilidad).

**Evento `push`** — payload relevante:

| Campo | Uso |
|---|---|
| `ref` | `refs/heads/main` → filtrar rama por defecto si quieren |
| `before` / `after` | SHAs |
| `commits[]` | cada uno con `id`, `timestamp`, `author` (`name`, `email`, `username`), `added[]`, `modified[]`, `removed[]` |
| `pusher` | quién hizo push |
| `head_commit` | commit más reciente del push |
| `repository` | `full_name`, `id` |
| `installation.id` | para renovar el token |

**Validación obligatoria de la firma:**

```javascript
import crypto from "crypto";

function verifySignature(rawBody, header, secret) {
  const expected = "sha256=" +
    crypto.createHmac("sha256", secret).update(rawBody).digest("hex");
  const a = Buffer.from(expected), b = Buffer.from(header || "");
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}
// header: X-Hub-Signature-256
```

> ⚠️ Usen el **body crudo** (antes de `JSON.parse`) y **`timingSafeEqual`**, no `===`.
> ⚠️ Respondan `202` en <10 s y procesen en background: GitHub reintenta si tardan.

Si están en localhost para la demo, usen `ngrok`/`cloudflared` — o, mejor, desplieguen temprano (igual necesitan una URL pública para la entrega final).

### 8.2 Backfill y respaldo: polling incremental

Los webhooks se pierden (deploys, caídas). Necesitan un reconciliador:

```javascript
// cada 15 min por repo, con ETag para no gastar rate limit
const res = await octokit.request("GET /repos/{owner}/{repo}/commits", {
  owner, repo,
  since: repoRow.last_commit_synced_at,   // ISO 8601
  per_page: 100,
  headers: repoRow.etag ? { "if-none-match": repoRow.etag } : {},
});
// 304 Not Modified → nada nuevo, y NO descuenta del rate limit primario
```

También hay que hacer un backfill completo la primera vez que un repo entra al sistema.

### 8.3 Modelo de datos para el dashboard

```
CommitRecord
  repository_id, sha (PK), authored_at, committed_at
  author_github_login (nullable), author_email, author_name
  student_id (nullable, resuelto por login o email)
  additions, deletions, changed_files (opcional)
  message_first_line

RepoActivityDaily        -- tabla agregada, la que lee el dashboard
  repository_id, day, commits, authors_json, additions, deletions

RepoStatus               -- una fila por repo, actualizada en cada ingesta
  repository_id, last_commit_at, total_commits, distinct_authors,
  members_with_zero_commits_json
```

El dashboard hace `SELECT` sobre `RepoActivityDaily` y `RepoStatus`. Milisegundos.

### 8.4 Atribución de commits a estudiantes — el problema silencioso

Un commit puede no traer `author.login`:

| Caso | Qué pasa | Solución |
|---|---|---|
| El estudiante configuró `git config user.email` con un correo no registrado en GitHub | `author` viene `null`; solo hay `commit.author.email` y `.name` | Fallback: match por email conocido (Canvas) y por `name` normalizado |
| Ediciones desde la web de GitHub | `author.login` correcto | ok |
| `Co-authored-by:` en el mensaje (pair programming) | GitHub lo cuenta aparte | Parsear el trailer del mensaje si quieren crédito compartido |
| Merge commits | inflan el conteo | Márquenlos (`parents.length > 1`) y permitan excluirlos |

**Regla:** guarden **siempre** `author_email` y `author_name` además del login, y en la UI muestren "N commits sin atribuir" con la lista de emails desconocidos, para que el docente pueda mapearlos a mano. Es honesto y evita acusar injustamente a un estudiante de "sin participación" (requisito 2.5.4).

### 8.5 Métricas y visualizaciones

**Requeridas por el enunciado:**

| Req. | Métrica | Fuente |
|---|---|---|
| 2.5.2 | Actividad de repos en el tiempo | serie diaria de commits por repo (`RepoActivityDaily`) |
| 2.5.3 | Repos sin actividad reciente | `RepoStatus.last_commit_at < now() - X días`; X configurable |
| 2.5.4 | Estudiantes sin participación | integrantes con 0 commits atribuidos |
| 2.5.5 | Estado de creación/configuración | máquina de estados de §5.6 |
| 2.5.6 | Entregas, fechas y estado | `Delivery` + `DeliverySnapshot` |
| 2.5.7 | Actividad **por período de entrega** | filtrar commits por `[entrega_anterior.due, entrega_actual.due]` |
| 2.5.8 | Comparar integrantes de un grupo | commits/líneas/días activos por autor dentro del repo |

**API de estadísticas de GitHub** (para backfill agregado rápido, no para el render):

| Endpoint | Devuelve |
|---|---|
| `GET /repos/{o}/{r}/stats/contributors` | por autor: `total` + `weeks[]` con `w` (timestamp), `a` (additions), `d` (deletions), `c` (commits) |
| `GET /repos/{o}/{r}/stats/commit_activity` | último año: por semana `days[]` (dom–sáb), `total`, `week` |
| `GET /repos/{o}/{r}/stats/code_frequency` | por semana: `[timestamp, additions, deletions]` |
| `GET /repos/{o}/{r}/stats/participation` | 52 semanas: `owner[]` y `all[]` |
| `GET /repos/{o}/{r}/stats/punch_card` | `[día(0-6), hora(0-23), commits]` |

> ⚠️ **El famoso `202`.** *"If the data hasn't been cached when you query a repository's statistics, you'll receive a `202` response; a background job is also fired to start compiling these statistics."* Hay que reintentar después. El caché se invalida en cada push a la rama por defecto. **Nunca llamen esto desde el render de una página** — es la receta perfecta para violar el requisito 2.5. Úsenlo en el worker, guarden el resultado.

**Extras que valen para el 2.5.9** (elijan 2–3, no 9):
- **Heatmap día×hora** (`punch_card`) → detecta el clásico "todo el trabajo la noche anterior".
- **Curva acumulada de commits vs. fecha de entrega**, con línea vertical en cada `due_at`.
- **Índice de concentración** (% de commits del integrante más activo) → señal de grupos desbalanceados. Muéstrenlo como *señal*, no como veredicto.
- **Días desde el último commit**, ordenable — la columna más útil para un ayudante.
- **Ritmo:** días distintos con actividad / días transcurridos.

> 🧠 **Advertencia metodológica que conviene decir en la defensa oral del 7-oct:** líneas añadidas/borradas es una métrica pésima de contribución (un `package-lock.json` o un archivo generado la destruye). Prioricen **número de commits** y **días activos distintos**, y filtren archivos binarios/generados. Que ustedes lo sepan y lo digan es exactamente el tipo de criterio que se evalúa en la actividad de validación.

### 8.6 Timeline por repositorio

> *"cada repositorio deberá contar con una vista de timeline que permita revisar fácilmente la evolución del trabajo, identificando cuándo se produjeron los principales cambios, qué integrantes participaron y las distintas entregas."*

Una línea de tiempo vertical, alimentada 100% desde su BD:

```
│ ● 2026-09-02 14:03  jperez     "Setup inicial del proyecto"     +240 −0   4 archivos
│ ● 2026-09-05 23:51  msoto      "Agrega parser de comandos"      +180 −12
│ ┣━━━━━━━━ 📌 ENTREGA PARCIAL · 16-09 16:30 · SHA aa218f5 · [ver código] ━━━━
│ ● 2026-09-18 10:22  jperez     "Corrige bug de índices"         +12 −8
│ ⚠ 11 días sin actividad
│ ● 2026-09-29 02:14  msoto      "Implementa dashboard"           +520 −30
│ ┣━━━━━━━━ 📌 ENTREGA FINAL · 06-10 16:00 · SHA 9f3c1de · [ver código] ━━━━
```

Elementos: commit (autor, mensaje, hora, tamaño), marcador de entrega con link al SHA, gaps de inactividad resaltados, filtro por autor y por rango de entrega.

---

## 9. Requisito 2.6 — Informes y comunicación

### 9.1 Informe docente diario (2.6.1 – 2.6.4)

*"Si no hay tareas activas entonces no hay informe"* — condición explícita, impleméntenla literalmente.

```
CRON diario 07:00 America/Santiago:
  para cada curso:
     tareas_activas = tareas con alguna entrega cuyo período esté vigente
     si vacío: continue          # ← requisito explícito, sin informe
     construir informe:
        · repos sin actividad en N días        (2.6.2)
        · estudiantes con 0 commits            (2.6.2)
        · repos en estado ERROR / PENDING      (2.6.2)
        · invitaciones sin aceptar
        · estudiantes sin usuario GitHub mapeado
        · entregas que vencen en <48 h + estado de avance
        · resumen: commits en las últimas 24 h, repos activos/total
     enviar a los suscritos con report.subscribe = true
```

**Suscripción individual (2.6.3):** tabla `report_subscriptions(user_id, course_id, enabled)`, toggle en la UI **y** link de "darse de baja" en el pie del email (con token firmado, sin login). Cuesta 20 minutos y es exactamente lo que pide el requisito.

**Envío por email (2.6.4):** esto **no** es Canvas — es SMTP. Usen SendGrid / Resend / Mailgun / SMTP de Gmail. Manden HTML + texto plano. Guarden un registro de envíos (`sent_at`, `status`) para poder demostrarlo en la corrección.

> 💡 Guarden cada informe generado también como página web accesible (`/courses/:id/reports/2026-09-16`), y en el email pongan el resumen + link. Así pueden mostrar el informe en la demo aunque el correo se demore o caiga en spam.

### 9.2 Anuncios en Canvas (2.6.6)

```bash
curl -X POST -H 'Authorization: Bearer <CANVAS_TOKEN>' \
 'https://<canvas>/api/v1/courses/<cid>/discussion_topics' \
 -F 'title=Cambio de fecha — Tarea 1' \
 -F 'message=<p>La entrega parcial se movió al <b>18 de septiembre, 16:30</b>.</p>' \
 -F 'is_announcement=true' \
 -F 'published=true' \
 -F 'specific_sections=12,13'
```

| Parámetro | Notas |
|---|---|
| `is_announcement` | `true` → es anuncio, no discusión |
| `title`, `message` | el `message` acepta HTML |
| `published` | `false` = borrador |
| `delayed_post_at` | programar publicación futura |
| `specific_sections` | IDs separados por coma, o `"all"` |
| `lock_at` | cuándo se cierra a comentarios |

**Listar anuncios:** `GET /api/v1/courses/:cid/discussion_topics?only_announcements=true`

> 💡 `specific_sections` calza perfecto con fechas por sección: si cambia la fecha solo de la Sección 2, el anuncio va solo a la Sección 2.

### 9.3 Mensajes directos por Canvas (2.6.5)

```bash
curl -X POST -H 'Authorization: Bearer <CANVAS_TOKEN>' \
 'https://<canvas>/api/v1/conversations' \
 -d 'recipients[]=3345' \
 -d 'recipients[]=3346' \
 -d 'subject=Tu repositorio de la Tarea 1' \
 -d 'body=Hola! Tu repositorio ya está creado: https://github.com/ORG/icc4201-t1-jperez — revisa tu correo para aceptar la invitación.' \
 -d 'group_conversation=false' \
 -d 'context_code=course_1234'
```

| Parámetro | Descripción (textual de la doc) |
|---|---|
| `recipients[]` | **requerido** — *"user ids (either numeric IDs or UUIDs prefixed with 'uuid:'), or course/group ids prefixed with 'course_' or 'group_'"* |
| `body` | **requerido** — el mensaje |
| `subject` | máx. 255 chars; se ignora al reutilizar una conversación |
| `group_conversation` | *"When false, individual private conversations will be created with each recipient"* |
| `force_new` | fuerza mensaje nuevo aunque exista conversación privada previa |
| `context_code` | el curso o grupo que da contexto (`course_1234`) |
| `attachment_ids[]` | archivos previamente subidos a la carpeta "conversation attachments" del emisor |

**Agregar mensaje a una conversación existente:**

```bash
curl -X POST -H 'Authorization: Bearer <TOKEN>' \
 'https://<canvas>/api/v1/conversations/2/add_message' -d 'body=Recordatorio: quedan 24 horas.'
```

> ⚠️ **`group_conversation=false` para notificaciones masivas.** Si lo dejan en `true` con 40 destinatarios, crean **un hilo grupal** donde 40 estudiantes se ven entre sí y pueden responder a todos. Para "tu repo es X", quieren **conversaciones privadas individuales** → `group_conversation=false`.
>
> ⚠️ Para mandar el repo **de cada** estudiante, es una llamada por estudiante (el body es distinto). Con `recipients[]` múltiples, el body es el mismo para todos. Respeten el throttling: secuencial, con pausa.

### 9.4 Comunicaciones automáticas por evento (2.6.7)

*"pueden ser activadas o desactivadas por el profesor dentro de cada tarea"* → tabla de flags por tarea:

| Evento | Canal | Flag |
|---|---|---|
| Repositorio disponible | Conversation individual + comentario en la entrega | `notify_repo_ready` |
| Falta usuario de GitHub (recordatorio) | Conversation individual | `notify_missing_mapping` |
| Faltan 48 h para una entrega | Conversation individual o anuncio | `notify_deadline_48h` |
| Faltan 24 h y el repo no tiene commits | Conversation individual | `notify_no_activity` |
| Cambio de fecha en Canvas | Anuncio (con `specific_sections`) | `notify_date_change` |
| Corrección publicada | Conversation individual | `notify_graded` |

**Implementación:** tabla `notification_outbox(id, kind, target, payload, scheduled_for, sent_at, error)` + worker. Ventajas: idempotencia (una fila = un envío, con constraint único por `(kind, target, delivery_id)`), reintentos, y una **pantalla de historial de comunicaciones** que pueden mostrar en la demo. Sin outbox, van a mandar el mismo mensaje 5 veces al reiniciar el worker.

---

## 10. Requisito 2.7 — Corrección

### 10.1 Asignación de correctores (2.7.1 – 2.7.3)

Vive en su BD: `grading_assignment(delivery_id, repository_id, grader_user_id, status)`.

- Asignación manual (drag & drop o selects) + **automática** (repartir equitativamente, o por sección).
- Vista "Mis correcciones" para el ayudante: lista filtrada por `grader_user_id`, con estados `pendiente / en curso / listo`.
- Navegación **anterior / siguiente** con atajos de teclado. El enunciado pide explícitamente *"navegar de forma sencilla entre las distintas entregas asignadas"* (2.7.3) — un botón "siguiente sin corregir" es la diferencia entre usable y no usable.

### 10.2 Acceso a la versión correcta (2.7.4)

Link directo al SHA capturado: `https://github.com/ORG/REPO/tree/<sha>`. Nunca linkeen a `main` — para cuando el ayudante corrija, `main` ya cambió. Muestren además "capturado el 16-09 16:30 · 47 commits · último por msoto".

### 10.3 Rúbrica de Canvas (2.7.5)

```bash
GET /api/v1/courses/:course_id/rubrics
GET /api/v1/courses/:course_id/rubrics/:id?include[]=associations&include[]=assignment_associations&style=full
```

`include[]`: `assessments`, `graded_assessments`, `peer_assessments`, `associations`, `assignment_associations`. `style`: `full` | `comments_only`.

**Objetos:**

| Objeto | Campos clave |
|---|---|
| `Rubric` | `id`, `title`, `points_possible`, `free_form_criterion_comments`, `hide_score_total`, `data[]` (criterios), `associations` |
| `RubricCriterion` | `id`, `description`, `long_description`, `points`, `criterion_use_range`, `ratings[]` |
| `RubricRating` | `id`, `criterion_id`, `description`, `long_description`, `points` |
| `RubricAssessment` | `id`, `rubric_id`, `rubric_association_id`, `score`, `artifact_type`, `artifact_id`, `artifact_attempt`, `assessment_type`, `assessor_id`, `data`, `comments` |
| `RubricAssociation` | `id`, `rubric_id`, `association_id`, `association_type` (`Assignment`/`Course`/`Account`), `use_for_grading`, `purpose` (`grading`/`bookmark`), `hide_points` |

> 💡 **Atajo:** el objeto `Assignment` ya trae `rubric` y `rubric_settings` embebidos cuando la tarea tiene una rúbrica asociada. Para renderizar la rúbrica del corrector, eso suele bastar y ahorra una llamada.

Rendericen la rúbrica como una grilla clickeable (criterios × ratings) al lado del link al código. Ese es el requisito 2.7.5 bien hecho.

### 10.4 Publicar notas en Canvas (2.7.6)

```bash
curl -X PUT -H 'Authorization: Bearer <CANVAS_TOKEN>' \
 'https://<canvas>/api/v1/courses/<cid>/assignments/<aid>/submissions/<user_id>' \
 -d 'submission[posted_grade]=5.8' \
 -d 'rubric_assessment[criterion_1][points]=8' \
 -d 'rubric_assessment[criterion_1][rating_id]=rat_3' \
 -d 'rubric_assessment[criterion_1][comments]=Buena arquitectura, falta manejo de errores' \
 -d 'rubric_assessment[criterion_2][points]=5' \
 -d 'comment[text_comment]=Revisado sobre la versión aa218f5 (entrega parcial).' \
 -d 'comment[group_comment]=true'
```

**Parámetros de `PUT .../submissions/:user_id`:**

| Parámetro | Notas |
|---|---|
| `submission[posted_grade]` | puntos, porcentaje, nota en letra o pass/fail |
| `submission[excuse]` | boolean |
| `submission[late_policy_status]` | `late`, `missing`, `extended`, `none` |
| `rubric_assessment[criterion_id][points]` | puntaje del criterio |
| `rubric_assessment[criterion_id][rating_id]` | rating elegido |
| `rubric_assessment[criterion_id][comments]` | comentario por criterio |
| `comment[text_comment]` | comentario general |
| `comment[group_comment]` | boolean — enviar a todo el grupo |
| `comment[media_comment_id]` | audio/video |

**Notas grupales:** si la tarea tiene `grade_group_students_individually: false`, calificar a **un** integrante propaga la nota a todo el grupo. Si es `true`, hay que llamar por cada integrante. **Lean ese campo antes de calificar** o van a dejar a medio grupo sin nota.

**Otros endpoints útiles:**

| Endpoint | Uso |
|---|---|
| `GET /api/v1/courses/:cid/assignments/:aid/submissions?include[]=user&include[]=submission_comments&grouped=true` | listar entregas |
| `GET /api/v1/courses/:cid/students/submissions?student_ids[]=...&assignment_ids[]=...` | varias tareas de una vez |
| `GET /api/v1/courses/:cid/assignments/:aid/submissions/:user_id` | una entrega |
| `POST /api/v1/courses/:cid/submissions/update_grades` · `POST /api/v1/courses/:cid/assignments/:aid/submissions/update_grades` | **calificación masiva asíncrona** (devuelve un `Progress`; hay que poletear su estado) |
| `GET /api/v1/courses/:cid/assignments/:aid/submission_summary` | *"the number of submissions... graded, ungraded, not submitted"* → **directo para el requisito 2.7.7** |
| `GET /api/v1/courses/:cid/assignments/:aid/gradeable_students` | quiénes se pueden calificar |

### 10.5 Estado de corrección (2.7.7)

Combinen su BD (quién tiene asignado qué, quién marcó "listo") con `submission_summary` de Canvas (fuente de verdad de qué está realmente calificado). Muestren ambos: *"18/25 corregidas en la app · 17/25 con nota en Canvas"* — la diferencia expone errores de publicación que de otro modo pasan desapercibidos.

---

## 11. Matriz completa: requisito → endpoints

| Req. | Qué pide | Canvas | GitHub | App / BD |
|---|---|---|---|---|
| 2.1.1 | Usuarios profesor | — | — | ✅ |
| 2.1.2 | Registro con gmail.com | — | — | Google OAuth (validar `@gmail.com` + `email_verified`) |
| 2.1.3 | Crear/administrar cursos | — | — | ✅ |
| 2.1.4 | Vincular con curso Canvas | `GET /courses?enrollment_type=teacher` · `GET /courses/:id` | — | guarda `canvas_course_id` |
| 2.1.5 | Vincular con org GitHub | — | instalación de la App · `GET /orgs/{org}/installation` | guarda `installation_id` |
| 2.1.6 | Guiar y verificar | varias (checklist §3.3) | `POST /orgs/{org}/repos` de prueba | pantalla de diagnóstico |
| 2.1.7 | Otros profesores | — | — | ✅ |
| 2.1.8 | Ayudantes + permisos (≥3) | — | — | ✅ RBAC |
| 2.1.9 | Retirar ayudante | — | `DELETE /orgs/{org}/memberships/{u}` | reasignar correcciones |
| 2.2.1 | Estudiantes | `GET /courses/:id/users` · `GET /courses/:id/enrollments` | — | upsert |
| 2.2.2 | Sección de cada uno | `enrollment.course_section_id` · `GET /courses/:id/sections` | — | N:M |
| 2.2.3 | Grupos de Canvas | `GET /courses/:id/group_categories` · `GET /group_categories/:id/groups` · `GET /groups/:id/users` | — | upsert |
| 2.2.4 | Mapear a usuario GitHub | tarea de recolección + `GET .../submissions` | `GET /users/{username}` | tabla de mapeo |
| 2.2.5 | Completar progresivamente | `POST /conversations` (recordatorios) | `GET /users/{u}` (validar) | UI editable + CSV |
| 2.2.6 | Mostrar faltantes | `GET /group_categories/:id/users?unassigned=true` | `GET /repos/../invitations` | panel de pendientes |
| 2.3.1 | Tarea ↔ 1..N tareas Canvas | `GET /courses/:id/assignments` | — | Assignment→Delivery |
| 2.3.2 | Entregas parciales/final | `assignment.id` por entrega | — | `kind`, `order_index` |
| 2.3.3 | Individual vs grupal | `assignment.group_category_id` | — | validar consistencia |
| 2.3.4 | Un set de repos por tarea | — | — | FK a Assignment, no a Delivery |
| 2.3.5 | Crear repo base | — | `POST /orgs/{org}/repos` + `PATCH {is_template:true}` | — |
| 2.3.6 | Archivos del repo base | — | `PUT /repos/../contents/{path}` · `GET /repos/../contents` | explorador |
| 2.3.7 | Crear repos automáticamente | — | `POST /repos/{o}/{t}/generate` o `POST /orgs/{org}/repos` | worker |
| 2.3.8 | Nombres inequívocos | — | — | plantilla + sanitización |
| 2.3.9 | Agregar estudiantes | — | `PUT /repos/../collaborators/{u}` (`push`) | — |
| 2.3.10 | Creación progresiva automática | — | idem, en cola | **cron + queue** |
| 2.3.11 | Estado de repos | — | `GET /repos/../invitations` · `GET /repos/../collaborators` | máquina de estados |
| 2.3.12 | Informar al estudiante | `PUT .../submissions/:uid` (`comment[text_comment]`) · `POST /conversations` | — | outbox |
| 2.4.1 | Fechas de Canvas | `GET /courses/:id/assignments?include[]=all_dates` | — | — |
| 2.4.2 | Fechas por sección | `.../overrides` (`course_section_id`) | — | fecha efectiva |
| 2.4.3 | Extensiones individuales | `.../overrides` (`student_ids[]`, `group_id`) | — | fecha efectiva |
| 2.4.4 | Mantener actualizadas | polling con `updated_at` | — | cron 10 min |
| 2.4.5 | Versión al cierre | — | `GET /repos/../commits?until=` + `POST /git/refs` | `DeliverySnapshot` |
| 2.4.6 | Versiones independientes | — | tags `entrega-N` | fila por (delivery, repo) |
| 2.4.7 | No alterar lo registrado | — | SHA inmutable | SHA en BD = verdad |
| 2.4.8 | Acceso directo a la versión | — | `github.com/O/R/tree/<sha>` | link |
| 2.5.1 | Dashboard por tarea | — | — | lee de BD |
| 2.5.2 | Actividad en el tiempo | — | webhook `push` + `GET /repos/../commits?since=` | agregados diarios |
| 2.5.3 | Repos sin actividad | — | idem | `last_commit_at` |
| 2.5.4 | Estudiantes sin participar | — | atribución de autor | 0 commits |
| 2.5.5 | Estado de configuración | — | — | §5.6 |
| 2.5.6 | Entregas, fechas, estado | fechas efectivas | snapshots | — |
| 2.5.7 | Actividad por período | — | filtro por rango | query |
| 2.5.8 | Comparar integrantes | — | `stats/contributors` (backfill) | por autor |
| 2.5.9 | Métricas propias | — | `stats/punch_card`, `code_frequency` | heatmap, curva |
| 2.5.x | Timeline por repo | — | `GET /repos/../commits` | vista |
| 2.6.1 | Informe diario | — | — | cron 07:00 |
| 2.6.2 | Situaciones de atención | — | — | reglas |
| 2.6.3 | Suscripción individual | — | — | tabla + unsubscribe |
| 2.6.4 | Envío por email | — | — | SMTP/SendGrid |
| 2.6.5 | Mensaje directo | `POST /conversations` | — | outbox |
| 2.6.6 | Anuncios | `POST /courses/:id/discussion_topics` (`is_announcement=true`, `specific_sections`) | — | — |
| 2.6.7 | Automáticas por evento | ambas anteriores | — | flags por tarea |
| 2.7.1 | Asignar correctores | — | — | ✅ |
| 2.7.2 | Ver mis correcciones | — | — | filtro |
| 2.7.3 | Navegar entre entregas | — | — | UI + atajos |
| 2.7.4 | Versión de la entrega | — | `tree/<sha>` | link |
| 2.7.5 | Rúbrica de Canvas | `GET /courses/:id/rubrics/:id` o `assignment.rubric` | — | grilla |
| 2.7.6 | Registrar notas en Canvas | `PUT .../submissions/:uid` + `rubric_assessment[..]` | — | — |
| 2.7.7 | Estado de corrección | `GET .../submission_summary` | — | + BD |

---

## 12. Arquitectura mínima que satisface el enunciado

```
┌──────────────┐   Google OAuth (gmail.com)
│   Navegador  │◄──────────────────────────────┐
└──────┬───────┘                               │
       │ HTTPS                                 │
┌──────▼─────────────────────────────────────┐ │
│  Web App (SSR o SPA + API)                 │─┘
│   · RBAC (profesor / ay. jefe / ayudante)  │
│   · TODAS las vistas leen de Postgres      │◄─── requisito 2.5 (inmediatez)
└──────┬──────────────────────┬──────────────┘
       │                      │
┌──────▼───────┐      ┌───────▼────────────────────────────┐
│  PostgreSQL  │      │  Workers (cola: BullMQ / Celery)   │
│  · cursos    │◄────►│  ① sync_canvas        cada 10 min  │
│  · repos     │      │  ② provision_repos    cada  2 min  │
│  · commits   │      │  ③ capture_snapshots  cada  5 min  │
│  · snapshots │      │  ④ backfill_commits   cada 15 min  │
│  · outbox    │      │  ⑤ daily_report       07:00 CLT    │
└──────────────┘      │  ⑥ send_outbox        cada  1 min  │
       ▲              └───────┬────────────────────────────┘
       │                      │
┌──────┴──────────┐    ┌──────▼──────┐        ┌──────────────┐
│ Webhook receiver│    │ Canvas API  │        │  GitHub API  │
│ /webhooks/github│    │ OAuth2 +    │        │  GitHub App  │
│ (HMAC SHA-256)  │    │ refresh tkn │        │  JWT → inst. │
└─────────────────┘    └─────────────┘        └──────────────┘
```

**Stack sugerido** (libre según el enunciado): Node + TypeScript (Octokit oficial resuelve JWT, renovación de tokens, paginación y reintentos) o Python + FastAPI (`PyGithub`/`githubkit` + `requests`). Postgres. Redis para la cola. Deploy en Railway/Render/Fly.io — recuerden que la app debe estar **disponible al menos dos semanas después de la entrega final** y necesita URL pública para los webhooks.

**Librerías que ahorran días:**

| Necesidad | Node | Python |
|---|---|---|
| GitHub App + REST | `octokit` (`App`, `.paginate`, throttling plugin) | `githubkit` o `PyGithub` |
| Canvas | `axios` + wrapper propio (no hay SDK oficial bueno) | `canvasapi` (no oficial, cubre lo esencial) |
| Cola/cron | `bullmq` + `node-cron` | `celery` + `celery beat` |
| JWT | `jsonwebtoken` | `pyjwt[crypto]` |

---

## 13. Plan para la entrega parcial (miércoles 16-sep 13:30)

El enunciado pide demostrar el **flujo completo**: crear profesor → crear curso → vincular Canvas → vincular GitHub → crear tarea individual → mapear estudiantes → crear repos automáticamente. Y evalúa **facilidad de uso y guía adecuada**.

**Lo mínimo indispensable:**

| # | Hito | Riesgo | Hacer primero |
|---|---|---|---|
| 1 | Canvas de pruebas con datos reales (2 secciones, ~10 estudiantes, 1 group set, 2 assignments con overrides) | 🔴 Sin esto no hay demo | **Día 1** |
| 2 | Developer Key de Canvas (o token manual + OAuth implementado igual) | 🔴 Depende de terceros | **Día 1** |
| 3 | GitHub App creada + instalada en una org de prueba; probar `POST /orgs/{org}/repos` | 🔴 Es donde aparecen los 403 de permisos | **Día 1–2** |
| 4 | Login Google + CRUD de cursos | 🟢 | Día 2–3 |
| 5 | Wizard de vinculación con **checklist de verificación** (§3.3) | 🟡 Es lo que se evalúa como "guía adecuada" | Día 3–4 |
| 6 | Sync de estudiantes, secciones, grupos | 🟢 | Día 4 |
| 7 | Tarea de recolección de usuarios GitHub + parsing + validación | 🟡 | Día 5 |
| 8 | Worker de creación de repos + tabla de estados | 🔴 Corazón de la demo | Día 5–7 |
| 9 | Notificación al estudiante por Canvas | 🟢 | Día 7 |
| 10 | Deploy con URL pública (se entrega por Canvas) | 🔴 Nunca deployen la noche anterior | Día 6 |

**Guion de demo sugerido (≈6 min):** registro con Gmail → crear curso → vincular Canvas (mostrar el selector de cursos reales) → vincular org GitHub → **checklist en verde** → crear tarea vinculando 1 assignment de Canvas → ver 10 estudiantes, 3 sin mapear → mostrar la tarea de Canvas donde entregan su usuario → simular una entrega → el worker crea los repos en vivo → tabla de estados pasando a verde → abrir un repo en GitHub → mostrar el mensaje que le llegó al estudiante en Canvas.

> 🎯 **Dejen visible un caso con problema** (un estudiante sin usuario GitHub, una invitación pendiente). El requisito 2.3.11 pide *"mostrar claramente... aquellos casos en que exista información pendiente o algún problema"*. Una demo donde todo está en verde no demuestra ese requisito.

---

## 14. Trampas y decisiones que conviene tener resueltas para el 7 de octubre

La actividad de validación es individual y pueden descontar hasta 3 puntos. Estas son las preguntas que un profesor haría, con la respuesta corta:

| Pregunta probable | Respuesta breve |
|---|---|
| *¿Cómo saben qué código corregir si el estudiante siguió trabajando?* | Guardamos el SHA del último commit anterior a la fecha efectiva de cierre; el SHA es inmutable y además creamos un tag. |
| *¿Y si un estudiante borra el tag?* | La verdad está en nuestra BD, no en el tag. Además les damos permiso `push`, no `admin`. |
| *¿Cómo manejan que la Sección 2 entregue un día después?* | `AssignmentOverride` con `course_section_id`; calculamos fecha efectiva por estudiante con precedencia ADHOC > grupo > sección > base. |
| *¿Y una extensión a un solo alumno?* | Override ADHOC con `student_ids[]`, que tiene la máxima precedencia. |
| *¿Por qué el dashboard carga instantáneo?* | Ingerimos commits por webhook y los agregamos por día; la vista solo hace SELECT. Nunca llamamos a GitHub en el render. |
| *¿Qué pasa si se cae el webhook?* | Reconciliador cada 15 min con `?since=` y ETag; el `304` ni siquiera gasta rate limit. |
| *¿Cómo evitan crear dos repos al mismo estudiante?* | El job es idempotente: lock por sujeto y `422 name already exists` se trata como éxito. |
| *¿Cómo evitan que el rate limit los bloquee al crear 60 repos?* | Cola con throttle; GitHub permite 80 requests generadoras de contenido por minuto y 900 puntos/min (POST = 5 pts). |
| *¿Por qué GitHub App y no un token personal?* | Rate limit mayor y escalable, token acotado a la org, webhooks incluidos, y no depende de la cuenta de una persona. |
| *¿Cómo detectan a un estudiante que no participó?* | Atribuimos commits por `author.login`, con fallback a email y nombre; mostramos los commits no atribuidos para no acusar por error. |
| *¿Por qué no usan líneas de código para comparar aportes?* | Es fácil de inflar (archivos generados, lock files). Usamos commits y días activos distintos. |
| *¿Canvas les avisa cuando cambia una fecha?* | No, la API pública no tiene webhooks; poleteamos con `updated_at` cada 10 minutos. |

**Otras trampas concretas:**

- **Zonas horarias.** Canvas devuelve ISO 8601 en UTC. Chile es UTC−3 (o −4 según DST). Guarden todo en UTC (`timestamptz`) y conviertan solo al renderizar. Un snapshot capturado con 3 horas de error es un bug invisible y grave.
- **Test Student.** Filtrarlo siempre; si no, van a intentar crear un repo para "Test Student".
- **Estudiantes que se retiran.** `enrollment_state` pasa a `deleted`/`inactive`. No borren su repo ni su historia; márquenlos.
- **Repos privados vs. públicos.** Créenlos **privados**. Si la org es Free, revisen el límite de colaboradores en repos privados de organización.
- **Rama por defecto.** No asuman `main`. Léanla de `repository.default_branch` — un template puede traer `master`.
- **Secretos.** El `.pem` de la GitHub App, el `client_secret` de Canvas y el webhook secret **no van al repo**. Variables de entorno. (Y el enunciado pide entregar todo el código por GitHub: un `.pem` commiteado es un hallazgo obvio.)
- **Declaración de uso de IA.** Está pedida explícitamente en la entrega final. Anótenlo ahora.

---

## 15. Referencias

**Canvas LMS API**
- Portal: https://developerdocs.instructure.com/services/canvas
- OAuth2: https://developerdocs.instructure.com/services/canvas/oauth2/file.oauth
- Throttling: https://developerdocs.instructure.com/services/canvas/basics/file.throttling
- Paginación: https://developerdocs.instructure.com/services/canvas/basics/file.pagination
- Courses · Sections · Enrollments · Users · Groups · Group Categories · Assignments · Submissions · Rubrics · Conversations · Discussion Topics: `https://developerdocs.instructure.com/services/canvas/resources/<recurso>`
- Truco: agregar `.md` a cualquier URL devuelve la versión Markdown (más fácil de leer y de scrapear). El índice completo está en `https://developerdocs.instructure.com/llms.txt`.

**GitHub REST API (v2026-03-10)**
- Índice: https://docs.github.com/en/rest
- Repos · Contents · Collaborators · Invitations · Commits · Git refs · Teams · Orgs members · Webhooks · Statistics: `https://docs.github.com/en/rest/<categoría>/<recurso>`
- Rate limits: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- Paginación: https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api
- Autenticación como installation: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation
- Webhooks y payloads: https://docs.github.com/en/webhooks/webhook-events-and-payloads

---

## Apéndice A — Puntos a verificar empíricamente

Cosas que la documentación deja ambiguas y que **deben probar en los primeros días**, porque cambian el diseño:

1. **Permisos exactos para `POST /orgs/{org}/repos` con installation token.** La doc habla de "Administration repository permissions (write)"; para creación *en la organización* puede requerir permiso de organización. Prueben y ajusten.
2. **Permisos exactos para `POST /repos/{t_owner}/{t_repo}/generate`.** No quedó documentado con claridad en la página consultada.
3. **`include[]=email` en `GET /courses/:id/users`.** La documentación clásica no lo lista entre los valores permitidos. Si necesitan el correo del estudiante, la ruta segura es `GET /api/v1/users/:id/profile` (campo `primary_email`) con los permisos adecuados, o simplemente no depender del email y comunicarse por Conversations.
4. **`bulk_message` en `POST /conversations`.** Aparece en versiones de la documentación pero no en la tabla actual de parámetros. Prueben antes de depender de él.
5. **Comportamiento de `403` vs `429` en throttling de Canvas.** La doc menciona ambos según la versión. Manejen los dos.
6. **Límite real de `per_page` en Canvas.** *"There is an unspecified limit"*: 100 funciona de forma confiable; no asuman más.
7. **Precedencia exacta de overrides cuando un estudiante está en dos secciones con fechas distintas.** El comportamiento documentado es "la más permisiva gana", pero verifíquenlo con un caso de prueba real en su Canvas: es un caso que un ayudante puede pedirles reproducir.
