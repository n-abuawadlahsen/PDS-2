/**
 * Origen de la API, sin barra final. En produccion va vacio: Vercel hace de
 * proxy de `/api` y `/auth` hacia la API (`vercel.json`), las peticiones son del
 * mismo origen y las cookies de sesion quedan first-party. En local apunta a
 * `http://localhost:8000`. Ausente cuenta como vacio, nunca como "undefined".
 */
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").trim().replace(/\/+$/, "");

function leerCookie(nombre: string): string | null {
  const partes = document.cookie.split("; ").find((fila) => fila.startsWith(`${nombre}=`));
  return partes ? decodeURIComponent(partes.split("=").slice(1).join("=")) : null;
}

/**
 * Toda peticion viaja con `credentials: "include"` (sesion opaca por cookie,
 * SPEC 02 S2.2.6). Las mutaciones agregan `X-CSRF-Token` desde la cookie de
 * doble envio `csrf_token`, que el backend exige (S2.2.6).
 */
export async function apiFetch(path: string, opciones: RequestInit = {}): Promise<Response> {
  const metodo = (opciones.method ?? "GET").toUpperCase();
  const cabeceras = new Headers(opciones.headers);

  if (metodo !== "GET" && metodo !== "HEAD") {
    const csrf = leerCookie("csrf_token");
    if (csrf) cabeceras.set("X-CSRF-Token", csrf);
    if (!cabeceras.has("Content-Type") && opciones.body) {
      cabeceras.set("Content-Type", "application/json");
    }
  }

  return fetch(`${API_BASE_URL}${path}`, {
    ...opciones,
    credentials: "include",
    headers: cabeceras,
  });
}

export interface Perfil {
  id: string;
  email: string;
  nombre: string;
  avatar_url: string | null;
  activo: boolean;
}

export async function obtenerPerfil(): Promise<Perfil | null> {
  const respuesta = await apiFetch("/api/perfil");
  if (respuesta.status === 401) return null;
  if (!respuesta.ok) throw new Error(`GET /api/perfil -> ${respuesta.status}`);
  return respuesta.json();
}

export interface Capacidades {
  perfil: "parcial" | "completo";
  banderas: string[];
}

export async function obtenerCapacidades(): Promise<Capacidades> {
  const respuesta = await apiFetch("/api/capacidades");
  if (!respuesta.ok) throw new Error(`GET /api/capacidades -> ${respuesta.status}`);
  return respuesta.json();
}

// --- Etapa P2: curso, equipo, invitaciones (SPEC 02 S2.4, S2.5) ---

export interface Curso {
  id: string;
  estado: string;
  nombre: string;
  codigo: string;
  periodo: string;
  slug: string;
  zona_horaria: string;
}

export async function listarCursos(): Promise<Curso[]> {
  const respuesta = await apiFetch("/api/cursos");
  if (!respuesta.ok) throw new Error(`GET /api/cursos -> ${respuesta.status}`);
  return respuesta.json();
}

export interface CursoEntrada {
  nombre: string;
  codigo: string;
  periodo: string;
  slug: string;
  zona_horaria: string;
}

export async function crearCurso(datos: CursoEntrada): Promise<Curso> {
  const respuesta = await apiFetch("/api/cursos", { method: "POST", body: JSON.stringify(datos) });
  if (!respuesta.ok) throw new Error(`POST /api/cursos -> ${respuesta.status}`);
  return respuesta.json();
}

export interface Miembro {
  membresia_id: string;
  usuario_id: string;
  nombre: string;
  email: string;
  rol: "PROFESOR" | "AYUDANTE";
  permisos: string[];
  estado: "ACTIVA" | "RETIRADA";
  retirada_en: string | null;
}

export async function listarEquipo(cursoId: string): Promise<Miembro[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/equipo`);
  if (!respuesta.ok) throw new Error(`GET equipo -> ${respuesta.status}`);
  return respuesta.json();
}

export interface Contexto {
  rol: string;
  permisos_efectivos: string[];
}

export async function obtenerContexto(cursoId: string): Promise<Contexto> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/contexto`);
  if (!respuesta.ok) throw new Error(`GET contexto -> ${respuesta.status}`);
  return respuesta.json();
}

export async function invitarMiembro(
  cursoId: string,
  datos: { email: string; rol: "PROFESOR" | "AYUDANTE"; permisos: string[] },
): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/equipo/invitaciones`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export async function retirarMiembro(cursoId: string, membresiaId: string): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/equipo/${membresiaId}/retiro`, { method: "POST" });
}

export async function reincorporarMiembro(
  cursoId: string,
  membresiaId: string,
  permisos: string[],
): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/equipo/${membresiaId}/reincorporacion`, {
    method: "POST",
    body: JSON.stringify({ permisos }),
  });
}

export interface InvitacionPublica {
  curso_nombre: string;
  rol: string;
  permisos: string[];
  email_enmascarado: string;
  estado: string;
}

export async function obtenerInvitacionPublica(token: string): Promise<InvitacionPublica> {
  const respuesta = await apiFetch(`/api/invitaciones/${token}`);
  if (!respuesta.ok) throw new Error(`GET invitacion -> ${respuesta.status}`);
  return respuesta.json();
}

export async function aceptarInvitacionConSesion(token: string): Promise<Response> {
  return apiFetch(`/api/invitaciones/${token}/aceptar`, { method: "POST" });
}

// --- Etapa P3: vinculacion con Canvas (SPEC 04 S4.5, SPEC 05 S5.2) ---

export interface InstanciaCanvas {
  base_url: string;
  nombre_visible: string;
}

export async function listarInstanciasCanvas(): Promise<InstanciaCanvas[]> {
  const respuesta = await apiFetch("/api/canvas/instancias");
  if (!respuesta.ok) throw new Error(`GET instancias -> ${respuesta.status}`);
  return respuesta.json();
}

export interface CursoCanvasDisponible {
  canvas_course_id: number;
  nombre: string;
  codigo: string;
  termino: string | null;
  total_estudiantes: number | null;
  ya_vinculado_a: string | null;
}

export async function listarCursosCanvasDisponibles(
  cursoId: string,
  datos: { token: string; canvas_base_url: string },
): Promise<{ ok: boolean; cursos: CursoCanvasDisponible[]; error?: string }> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/vinculacion/canvas/cursos-disponibles`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
  const cuerpo = await respuesta.json().catch(() => []);
  if (!respuesta.ok) return { ok: false, cursos: [], error: cuerpo.detail ?? String(respuesta.status) };
  return { ok: true, cursos: cuerpo };
}

export async function vincularCanvas(
  cursoId: string,
  datos: { token: string; canvas_base_url: string; canvas_course_id: number },
): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/vinculacion/canvas`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export interface CredencialCanvasEstado {
  titular_usuario_id: string;
  estado: string;
  huella: string;
  orden_respaldo: number;
  ultimo_chequeo_en: string | null;
}

export async function obtenerEstadoVinculacionCanvas(cursoId: string): Promise<CredencialCanvasEstado[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/vinculacion/canvas`);
  if (!respuesta.ok) throw new Error(`GET vinculacion canvas -> ${respuesta.status}`);
  return respuesta.json();
}

// --- Etapa P4: vinculacion con GitHub y checklist (SPEC 04 S4.6-S4.7) ---

export async function iniciarInstalacionGithub(
  cursoId: string,
  orgLoginSugerido?: string,
): Promise<{ instalar_url: string }> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/vinculacion/github/iniciar`, {
    method: "POST",
    body: JSON.stringify({ org_login_sugerido: orgLoginSugerido ?? null }),
  });
  if (!respuesta.ok) throw new Error(`POST iniciar instalacion -> ${respuesta.status}`);
  return respuesta.json();
}

export interface CallbackInstalacionResultado {
  resultado: "VINCULADO" | "SOLICITUD_PENDIENTE" | "SIN_INSTALLATION_ID" | "STATE_INVALIDO";
  curso_id?: string;
  org_login?: string;
  equipo_docentes_slug?: string;
  curso_estado?: string;
}

export async function confirmarCallbackGithub(datos: {
  state: string;
  installation_id?: number;
  setup_action?: string;
}): Promise<{ ok: boolean; cuerpo: CallbackInstalacionResultado | { detail: unknown } }> {
  const respuesta = await apiFetch("/api/vinculacion/github/callback", {
    method: "POST",
    body: JSON.stringify(datos),
  });
  const cuerpo = await respuesta.json();
  return { ok: respuesta.ok, cuerpo };
}

export interface EstadoVinculacionGithub {
  org_login: string | null;
  installation_id: number | null;
  equipo_docentes_slug: string | null;
  curso_estado: string;
}

export async function obtenerEstadoVinculacionGithub(cursoId: string): Promise<EstadoVinculacionGithub> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/vinculacion/github`);
  if (!respuesta.ok) throw new Error(`GET vinculacion github -> ${respuesta.status}`);
  return respuesta.json();
}

export interface InstalacionHuerfana {
  installation_id: number;
  org_login: string;
  actualizada_en: string;
}

export async function listarInstalacionesHuerfanas(cursoId: string): Promise<InstalacionHuerfana[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/vinculacion/github/huerfanas`);
  if (!respuesta.ok) throw new Error(`GET huerfanas -> ${respuesta.status}`);
  return respuesta.json();
}

export async function adoptarInstalacionHuerfana(
  cursoId: string,
  datos: { installation_id: number; org_login_confirmado: string },
): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/vinculacion/github/huerfanas/adoptar`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export interface ItemVerificacion {
  item: string | null;
  resultado: "CORRECTO" | "ADVERTENCIA" | "BLOQUEANTE" | "NO_VERIFICADO" | "VERIFICADO_A_MANO";
  detalle: Record<string, unknown>;
  ejecutada_en: string;
}

export async function encolarChecklist(cursoId: string): Promise<{ ejecucion_id: string }> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/verificacion`, { method: "POST" });
  if (!respuesta.ok) throw new Error(`POST verificacion -> ${respuesta.status}`);
  return respuesta.json();
}

export async function reejecutarItem(cursoId: string, item: string): Promise<{ ejecucion_id: string }> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/verificacion/items/${item}`, {
    method: "POST",
  });
  if (!respuesta.ok) throw new Error(`POST reejecutar item -> ${respuesta.status}`);
  return respuesta.json();
}

export async function obtenerEjecucionVerificacion(
  cursoId: string,
  ejecucionId: string,
): Promise<ItemVerificacion[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/verificacion/${ejecucionId}`);
  if (!respuesta.ok) throw new Error(`GET ejecucion -> ${respuesta.status}`);
  return respuesta.json();
}

export async function obtenerUltimaVerificacion(cursoId: string): Promise<ItemVerificacion[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/verificacion/ultima`);
  if (!respuesta.ok) throw new Error(`GET ultima verificacion -> ${respuesta.status}`);
  return respuesta.json();
}

export async function firmarItem14AMano(cursoId: string): Promise<ItemVerificacion> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/verificacion/items/14/firmar`, {
    method: "POST",
  });
  if (!respuesta.ok) throw new Error(`POST firmar item 14 -> ${respuesta.status}`);
  return respuesta.json();
}

export async function ejecutarPruebaEscritura(
  cursoId: string,
  item: "5-bis" | "17-bis",
  consiento: boolean,
): Promise<ItemVerificacion> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/verificacion/items/${item}`, {
    method: "POST",
    body: JSON.stringify({ consiento }),
  });
  if (!respuesta.ok) throw new Error(`POST prueba ${item} -> ${respuesta.status}`);
  return respuesta.json();
}

// --- Etapa P5: espejo de Canvas (SPEC 07 S7.2-S7.3) ---

export interface MapeoGithubEspejo {
  estado: string;
  cuenta_login: string | null;
  motivo_invalidacion: string | null;
}

export interface EstudianteEspejo {
  id: string;
  canvas_user_id: number;
  nombre: string;
  estado: string;
  email: string | null;
  sis_user_id: string | null;
  secciones: string[];
  grupos: string[];
  mapeo: MapeoGithubEspejo;
}

export interface SeccionEspejo {
  id: string;
  nombre: string;
  estado: string;
  cantidad_estudiantes: number;
}

export interface GrupoEspejo {
  id: string;
  nombre: string;
  conjunto: string;
  estado: string;
  integrantes: string[];
}

export interface Personas {
  estudiantes: EstudianteEspejo[];
  secciones: SeccionEspejo[];
  grupos: GrupoEspejo[];
  roster_sincronizado_en: string | null;
  grupos_sincronizado_en: string | null;
  registro_estado: string;
}

export async function obtenerPersonas(cursoId: string): Promise<Personas> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/personas`);
  if (!respuesta.ok) throw new Error(`GET personas -> ${respuesta.status}`);
  return respuesta.json();
}

export interface CabeceraPersonas {
  con_cuenta_verificada: number;
  total: number;
}

export async function obtenerCabeceraPersonas(cursoId: string): Promise<CabeceraPersonas> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/personas/cabecera`);
  if (!respuesta.ok) throw new Error(`GET cabecera -> ${respuesta.status}`);
  return respuesta.json();
}

export async function sincronizarAhora(cursoId: string): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/sincronizaciones`, { method: "POST" });
}

// --- Etapa P6: mapeo estudiante <-> GitHub y Pendientes (SPEC 07 S7.4-S7.8) ---

export async function declararMapeoManual(
  cursoId: string,
  estudianteId: string,
  login: string,
): Promise<{ ok: boolean; cuerpo: MapeoGithubEspejo | { detail: { motivo: string; detalle: string } } }> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/personas/${estudianteId}/mapeo`, {
    method: "POST",
    body: JSON.stringify({ login }),
  });
  const cuerpo = await respuesta.json();
  return { ok: respuesta.ok, cuerpo };
}

export interface FilaCsvMapeo {
  fila: number;
  canvas_user_id: number | null;
  login_id: string | null;
  github_login: string;
  resultado: "SE_APLICARIA" | "APLICADA" | "INVALIDA" | "FALLIDA";
  detalle: string | null;
}

export async function importarMapeoCsv(
  cursoId: string,
  csv: string,
  aplicar: boolean,
): Promise<{ filas: FilaCsvMapeo[] }> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/mapeo/importar-csv`, {
    method: "POST",
    body: JSON.stringify({ csv, aplicar: aplicar ? "true" : "false" }),
  });
  if (!respuesta.ok) throw new Error(`POST importar csv -> ${respuesta.status}`);
  return respuesta.json();
}

export async function crearRegistroGithub(cursoId: string): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/registro-github`, { method: "POST" });
}

export async function restaurarRegistroGithub(cursoId: string): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/registro-github/restaurar`, { method: "POST" });
}

export interface FilaPendienteSinCuenta {
  estudiante_id: string;
  nombre: string;
  estado_estudiante: string;
  estado_mapeo: string;
}

export interface FilaPendienteEnConflicto {
  estudiante_id: string;
  nombre: string;
  estado_mapeo: string;
  motivo_invalidacion: string | null;
  cuenta_login: string | null;
}

export interface FilaPendienteGrupo {
  tipo: string;
  severidad: string;
  estudiante_id: string | null;
  nombre: string | null;
  detalle: Record<string, unknown>;
}

export interface FilaPendienteInvitacion {
  estudiante_id: string;
  nombre: string;
  estado_acceso: string;
}

export interface Pendientes {
  bloque_1_sin_cuenta: FilaPendienteSinCuenta[];
  bloque_2_en_conflicto: FilaPendienteEnConflicto[];
  bloque_3_grupos_incompletos: FilaPendienteGrupo[];
  bloque_4_invitaciones_sin_aceptar: FilaPendienteInvitacion[];
}

export async function obtenerPendientes(cursoId: string): Promise<Pendientes> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/pendientes`);
  if (!respuesta.ok) throw new Error(`GET pendientes -> ${respuesta.status}`);
  return respuesta.json();
}

export async function enviarRecordatorio(cursoId: string, estudianteId: string): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/pendientes/${estudianteId}/recordatorio`, { method: "POST" });
}

// --- Etapa P7: tareas, entregas y repositorio base (SPEC 08 S8.2-S8.3) ---

/** Resultado de una accion: o los datos nuevos, o el motivo escrito del backend. */
export interface Resultado<T> {
  ok: boolean;
  status: number;
  datos: T | null;
  error: string | null;
}

async function resultado<T>(respuesta: Response): Promise<Resultado<T>> {
  let cuerpo: unknown = null;
  try {
    cuerpo = await respuesta.json();
  } catch {
    cuerpo = null;
  }
  if (respuesta.ok) {
    return { ok: true, status: respuesta.status, datos: cuerpo as T, error: null };
  }
  const detalle = (cuerpo as { detail?: unknown } | null)?.detail;
  let error = `La operación falló (${respuesta.status}).`;
  if (typeof detalle === "string") error = detalle;
  else if (detalle && typeof detalle === "object" && "detalle" in detalle) {
    error = String((detalle as { detalle: unknown }).detalle);
  } else if (detalle && typeof detalle === "object" && "motivo" in detalle) {
    error = String((detalle as { motivo: unknown }).motivo);
  }
  return { ok: false, status: respuesta.status, datos: null, error };
}

export interface AccionHabilitada {
  habilitada: boolean;
  motivo: string | null;
}

export interface TareaResumen {
  id: string;
  nombre: string;
  slug: string;
  modalidad: string;
  estado: string;
  cantidad_entregas: number;
  estado_repositorio_base: string | null;
  creada_en: string;
}

export interface EntregaTarea {
  id: string;
  canvas_assignment_id: number;
  tipo: string;
  orden: number;
  nombre: string;
  slug: string;
  publicada: boolean;
  due_at_base: string | null;
  estado_validacion: string;
  advertencias: string[];
  sincronizado_en: string;
}

export interface ArchivoBase {
  ruta: string;
  sha: string;
  tamano_bytes: number;
  actualizado_en: string;
}

export interface RepositorioBase {
  id: string;
  nombre: string;
  full_name: string | null;
  url_html: string | null;
  estado: string;
  rama_por_defecto: string | null;
  clase_error: string | null;
  error_mensaje_literal: string | null;
  archivos: ArchivoBase[];
}

export interface TareaDetalle {
  id: string;
  nombre: string;
  slug: string;
  modalidad: string;
  estado: string;
  gitignore_template: string | null;
  activada_en: string | null;
  entregas: EntregaTarea[];
  repositorio_base: RepositorioBase | null;
  nombre_repositorio_base: string;
  activar: AccionHabilitada;
  vincular_otra_entrega: AccionHabilitada;
  crear_repositorio_base: AccionHabilitada;
}

export interface AssignmentCanvasOpcion {
  canvas_assignment_id: number;
  nombre: string;
  es_grupal: boolean;
  publicada: boolean;
  due_at: string | null;
  seleccionable: boolean;
  motivo: string | null;
}

export interface AssignmentsCanvas {
  assignments: AssignmentCanvasOpcion[];
  sincronizado_en: string | null;
  plantillas_gitignore: string[];
}

export interface VistaPreviaNombre {
  slug: string;
  slug_valido: boolean;
  slug_ocupado: boolean;
  ejemplo_repositorio: string | null;
  ejemplo_sujeto: string;
  repositorio_base: string | null;
}

export interface PrevisualizacionArchivo {
  ruta: string;
  tamano_bytes: number;
  texto: string | null;
  motivo_sin_texto: string | null;
}

export async function listarTareas(cursoId: string): Promise<TareaResumen[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas`);
  if (!respuesta.ok) throw new Error(`GET tareas -> ${respuesta.status}`);
  return respuesta.json();
}

export async function obtenerAssignmentsCanvas(cursoId: string): Promise<AssignmentsCanvas> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/assignments-canvas`);
  if (!respuesta.ok) throw new Error(`GET assignments-canvas -> ${respuesta.status}`);
  return respuesta.json();
}

export async function obtenerVistaPreviaNombre(
  cursoId: string,
  nombre: string,
  slug: string,
): Promise<VistaPreviaNombre> {
  const parametros = new URLSearchParams({ nombre });
  if (slug.trim()) parametros.set("slug", slug.trim());
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/vista-previa-nombre?${parametros}`);
  if (!respuesta.ok) throw new Error(`GET vista-previa-nombre -> ${respuesta.status}`);
  return respuesta.json();
}

export async function crearTarea(
  cursoId: string,
  datos: { nombre: string; slug: string | null; canvas_assignment_id: number; gitignore_template: string | null },
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas`, { method: "POST", body: JSON.stringify(datos) }),
  );
}

export async function obtenerTarea(cursoId: string, tareaId: string): Promise<TareaDetalle> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}`);
  if (!respuesta.ok) throw new Error(`GET tarea -> ${respuesta.status}`);
  return respuesta.json();
}

export async function activarTarea(cursoId: string, tareaId: string): Promise<Resultado<TareaDetalle>> {
  return resultado(await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/activar`, { method: "POST" }));
}

export async function desvincularEntrega(
  cursoId: string,
  tareaId: string,
  entregaId: string,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/entregas/${entregaId}`, { method: "DELETE" }),
  );
}

/** R2.3.2: vincular otra tarea de Canvas; hay que decir siempre cual es la final (A-080). */
export async function vincularEntrega(
  cursoId: string,
  tareaId: string,
  canvasAssignmentId: number,
  finalCanvasAssignmentId: number,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/entregas`, {
      method: "POST",
      body: JSON.stringify({
        canvas_assignment_id: canvasAssignmentId,
        final_canvas_assignment_id: finalCanvasAssignmentId,
      }),
    }),
  );
}

/** Con versiones registradas no se desvincula: se excluye, sin borrar nada. */
export async function excluirEntrega(
  cursoId: string,
  tareaId: string,
  entregaId: string,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/entregas/${entregaId}/excluir`, { method: "POST" }),
  );
}

export async function crearRepositorioBase(cursoId: string, tareaId: string): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repositorio-base`, { method: "POST" }),
  );
}

function rutaCodificada(ruta: string): string {
  return ruta.split("/").map(encodeURIComponent).join("/");
}

export async function escribirArchivoBase(
  cursoId: string,
  tareaId: string,
  ruta: string,
  contenidoBase64: string,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repositorio-base/archivos/${rutaCodificada(ruta)}`, {
      method: "PUT",
      body: JSON.stringify({ contenido_base64: contenidoBase64 }),
    }),
  );
}

export async function borrarArchivoBase(
  cursoId: string,
  tareaId: string,
  ruta: string,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repositorio-base/archivos/${rutaCodificada(ruta)}`, {
      method: "DELETE",
    }),
  );
}

export async function renombrarArchivoBase(
  cursoId: string,
  tareaId: string,
  desde: string,
  hacia: string,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repositorio-base/renombrar`, {
      method: "POST",
      body: JSON.stringify({ desde, hacia }),
    }),
  );
}

// --- Etapa P8: aprovisionamiento, estado y fechas (SPEC 08 S8.9, SPEC 09 S9.5) ---

export interface ResumenRepositorios {
  operativos: number;
  degradados: number;
  bloqueados: number;
  esperando_limite: number;
  error_transitorio: number;
  error_permanente: number;
  inaccesibles: number;
  fuera_de_alcance: number;
  archivados: number;
  esperando_informacion: number;
  listos_para_crear: number;
  creando: number;
  sujetos_activos: number;
  sujetos_inactivos: number;
  en_curso: boolean;
  creados: number;
  minutos_restantes: number;
}

/** Integrante `accepted` de un sujeto grupal con el estado de su acceso (F1). */
export interface IntegranteRepositorio {
  estudiante_id: string;
  nombre: string;
  cuenta_github: string | null;
  acceso_estado: string | null;
  acceso_error: string | null;
  invitacion_url: string | null;
}

export interface FilaRepositorio {
  repositorio_id: string;
  estudiante_id: string | null;
  sujeto: string;
  sujeto_tipo: "ESTUDIANTE" | "GRUPO";
  integrantes: IntegranteRepositorio[];
  sujeto_activo: boolean;
  motivo_desactivacion: string | null;
  nombre: string;
  url_html: string | null;
  estado: string;
  motivo: string | null;
  error_codigo: string | null;
  error_mensaje_literal: string | null;
  intentos: number;
  proximo_intento_en: string | null;
  cuenta_github: string | null;
  acceso_estado: string | null;
  acceso_error: string | null;
  invitacion_url: string | null;
  acceso_docente: string | null;
  reemplaza_a_id: string | null;
  listo_en: string | null;
}

export interface RepositoriosTarea {
  resumen: ResumenRepositorios;
  filas: FilaRepositorio[];
}

export interface ExcepcionFecha {
  origen: string;
  etiqueta: string;
  fecha: string;
  canvas_override_id: number | null;
  titulo: string | null;
  sujetos: string[];
}

export interface CandidataFecha {
  origen: string;
  etiqueta: string;
  fecha: string;
  canvas_override_id: number | null;
}

export interface FechasEntrega {
  entrega_id: string;
  nombre: string;
  tipo: string;
  orden: number;
  estado_validacion: string;
  cierre_base: string;
  fechas_distintas: number;
  excepciones: ExcepcionFecha[];
  ambiguas: { sujeto_id: string; sujeto: string; fecha: string; candidatas: CandidataFecha[] }[];
  sujetos_con_fecha: number;
  sujetos_sin_fecha: number;
}

export interface HistorialFechasSujeto {
  sujeto_id: string;
  sujeto: string;
  fechas: {
    fecha: string;
    origen: string;
    etiqueta: string;
    canvas_override_id: number | null;
    override_titulo: string | null;
    override_retirado: boolean;
    ambigua: boolean;
    estado: string;
    calculada_en: string;
    vigente_hasta: string | null;
  }[];
}

/** S9.4.1: el encadenamiento de fechas superseded por sujeto es el historial. */
export async function obtenerHistorialFechas(cursoId: string, entregaId: string): Promise<HistorialFechasSujeto[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/entregas/${entregaId}/historial-fechas`);
  if (!respuesta.ok) throw new Error(`GET historial-fechas -> ${respuesta.status}`);
  return respuesta.json();
}

// --- Etapa F4: versiones de entrega (SPEC 09 S9.6-S9.9) ---

export interface VersionEntrega {
  id: string;
  intento: number;
  vigente: boolean;
  estado: string;
  motivo: string | null;
  commit_sha: string | null;
  commit_mensaje: string | null;
  rama: string | null;
  fecha_corte: string;
  capturada_en: string;
  captura_tardia_minutos: number | null;
  tag_nombre: string | null;
  tag_estado: string;
  tag_motivo: string | null;
  tag_error: string | null;
  advertencias: string[];
  verificacion: Record<string, unknown>;
  origen_captura: string;
  motivo_manual: string | null;
  creada_por: string | null;
  integrantes: { nombre: string; github_login: string | null }[];
  sujeto_etiqueta: string;
  repositorio_full_name: string | null;
  fecha_origen: string | null;
  canvas_override_id: number | null;
  comparacion_base: string | null;
  enlaces: { arbol: string | null; comparacion: string | null; zip: string | null };
}

export interface FilaCaptura {
  sujeto_id: string;
  sujeto: string;
  fecha: string;
  estado_captura: string;
  version: VersionEntrega | null;
}

export interface ProgresoCaptura {
  entrega_id: string;
  estado_validacion: string;
  vencidas: number;
  registradas: number;
  por_estado: Record<string, number>;
  capturas_tardias: number;
  filas: FilaCaptura[];
}

export interface FichaVersion {
  sujeto: string;
  vigente: VersionEntrega | null;
  anteriores: VersionEntrega[];
  acceso_docente: string | null;
}

/** Los enlaces a GitHub pasan por la redireccion auditada del servidor (S9.9.4). */
export function urlApi(ruta: string): string {
  return `${API_BASE_URL}${ruta}`;
}

export async function obtenerProgresoCaptura(cursoId: string, entregaId: string): Promise<ProgresoCaptura> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/entregas/${entregaId}/progreso-captura`);
  if (!respuesta.ok) throw new Error(`GET progreso-captura -> ${respuesta.status}`);
  return respuesta.json();
}

export async function obtenerFichaVersion(
  cursoId: string,
  entregaId: string,
  sujetoId: string,
): Promise<FichaVersion> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/entregas/${entregaId}/sujetos/${sujetoId}/version`);
  if (!respuesta.ok) throw new Error(`GET version -> ${respuesta.status}`);
  return respuesta.json();
}

export type AccionVersion =
  | { tipo: "capturar-ahora"; motivo_manual: string }
  | { tipo: "recapturar"; motivo_manual: string; fecha_corte: string }
  | { tipo: "fijar-sha"; motivo_manual: string; sha: string };

/** S9.8.8: las tres acciones manuales; siempre con motivo escrito. */
export async function accionVersion(
  cursoId: string,
  entregaId: string,
  sujetoId: string,
  accion: AccionVersion,
): Promise<Resultado<VersionEntrega>> {
  const { tipo, ...cuerpo } = accion;
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/entregas/${entregaId}/sujetos/${sujetoId}/version/${tipo}`, {
      method: "POST",
      body: JSON.stringify(cuerpo),
    }),
  );
}

export async function registrarVersiones(cursoId: string, entregaId: string): Promise<Resultado<{ encoladas: number }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/entregas/${entregaId}/registrar-versiones`, { method: "POST" }),
  );
}

// --- Etapa F6: tablero y seguimiento (SPEC 10 S10.7-S10.8, S10.10.6) ---

export interface IntegranteTablero {
  estudiante_id: string;
  nombre: string;
  commits: number;
  dias_activos: number;
  adiciones: number | null;
  eliminaciones: number | null;
  causa: string | null;
  retirado: boolean;
  en_grupo_desde: string | null;
  salio_del_grupo: string | null;
}

export interface FilaTablero {
  repositorio_id: string;
  nombre: string;
  sujeto: string;
  sujeto_tipo: "ESTUDIANTE" | "GRUPO";
  seccion: string | null;
  estado: string;
  grupo_estado: string;
  motivo: string | null;
  no_aplica: boolean;
  actividad: string;
  dias_observados: number;
  umbral_dias: number;
  commits_periodo: number;
  commits_sin_atribuir: number;
  dias_desde_ultimo_commit: number | null;
  sparkline: number[];
  alertas: string[];
  integrantes: IntegranteTablero[];
  indice_desequilibrio: number | null;
  reparto_concentrado: boolean;
}

export interface Tablero {
  tarea: { id: string; nombre: string; modalidad: string; estado: string };
  procedencia: {
    ultima_ingesta: string | null;
    ultima_reconciliacion: string | null;
    datos_posiblemente_desactualizados: boolean;
    calculado_en: string | null;
    llamadas_externas: number;
    render_ms: number;
  };
  periodos: { clave: string; etiqueta: string }[];
  periodo: string;
  entregas: {
    entrega_id: string;
    orden: number;
    nombre: string;
    tipo: string;
    estado: string;
    fechas_distintas: number;
    sujetos: number;
    versiones_registradas: number;
  }[];
  repositorios: ResumenRepositorios;
  tarjetas: {
    repositorios_creados: number;
    sin_actividad: number;
    sin_dato_suficiente: number;
    sin_datos_todavia: number;
    sin_participacion: Record<string, number>;
    invitaciones_sin_aceptar: number;
    bloqueantes: number;
  };
  serie: { dia: string; commits: number }[];
  cierres: string[];
  histograma_previo_al_cierre: { dia: string; commits: number }[];
  progreso_frente_al_cierre: number | null;
  posicion_frente_al_curso: {
    commits: [number, number, number] | null;
    dias_activos: [number, number, number] | null;
    mediana_por_seccion: Record<string, number>;
    sujetos: number;
    excluidos: number;
  } | null;
  filas: FilaTablero[];
  total_filas: number;
  pagina: number;
  definicion_commit_contable: string;
  aviso_alcance: string;
}

export async function obtenerTablero(
  cursoId: string,
  tareaId: string,
  filtros: { periodo?: string; seccion?: string; grupoEstado?: string; soloAlertas?: boolean },
): Promise<Tablero> {
  const q = new URLSearchParams();
  if (filtros.periodo) q.set("periodo", filtros.periodo);
  if (filtros.seccion) q.set("seccion", filtros.seccion);
  if (filtros.grupoEstado) q.set("grupo_estado", filtros.grupoEstado);
  if (filtros.soloAlertas) q.set("solo_alertas", "true");
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/tablero?${q.toString()}`);
  if (!respuesta.ok) throw new Error(`GET tablero -> ${respuesta.status}`);
  return respuesta.json();
}

export async function actualizarTablero(
  cursoId: string,
  tareaId: string,
): Promise<{ encolada: boolean; en_curso: boolean; disponible_en: string }> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/tablero/actualizar`, {
    method: "POST",
  });
  return respuesta.json();
}

export async function silenciarIncidencia(cursoId: string, incidenciaId: string): Promise<boolean> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/incidencias/${incidenciaId}/silenciar`, {
    method: "POST",
  });
  return respuesta.ok;
}

export interface FilaSeguimiento {
  tarea_id: string;
  nombre: string;
  modalidad: string;
  repositorios: ResumenRepositorios;
  sin_actividad: number;
  sin_participacion: number;
  invitaciones_sin_aceptar: number;
}

export async function obtenerSeguimiento(cursoId: string): Promise<FilaSeguimiento[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/seguimiento`);
  if (!respuesta.ok) throw new Error(`GET seguimiento -> ${respuesta.status}`);
  return respuesta.json();
}

// --- Etapas F5 y F7: timeline e identidades de Git (SPEC 10 S10.3.7, S10.9) ---

export interface CommitTimeline {
  sha: string;
  sha_corto: string;
  fecha: string;
  mensaje: string | null;
  autor: string | null;
  regla_atribucion: string;
  senal_debil: boolean;
  etiqueta_exclusion: string | null;
  rama: string | null;
  destacado: string | null;
  hito: string | null;
  posterior_al_cierre_de: number | null;
  url: string | null;
}

export interface Timeline {
  repositorio: { id: string; nombre: string; estado: string; rama_por_defecto: string | null };
  sujeto: string;
  periodos: { clave: string; etiqueta: string }[];
  periodo: string;
  dias: { dia: string; colapsado: boolean; hasta: string | null; n_dias: number; commits: CommitTimeline[] }[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ciclo_de_vida: { fecha: string; tipo: string; detalle: Record<string, any> }[];
  marcas_entrega: {
    orden: number;
    entrega: string;
    fecha: string | null;
    aplica: boolean;
    versiones: { intento: number; vigente: boolean; estado: string; motivo: string | null; commit_sha: string | null }[];
  }[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  composicion: Record<string, any>[];
  franja: {
    periodo: string;
    entrega: string;
    integrantes: {
      estudiante_id: string;
      nombre: string;
      commits: number;
      dias_activos: number;
      causa: string | null;
    }[];
    sin_atribuir: number;
  }[];
  enlaces: { motivo: string | null };
  identidades_sin_resolver: number;
  sin_commits_contables: boolean;
  causa_vacia: string | null;
}

export async function obtenerTimeline(
  cursoId: string,
  tareaId: string,
  repoId: string,
  filtros: { periodo?: string; integrante?: string },
): Promise<Timeline> {
  const q = new URLSearchParams();
  if (filtros.periodo) q.set("periodo", filtros.periodo);
  if (filtros.integrante) q.set("integrante", filtros.integrante);
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repos/${repoId}/timeline?${q}`);
  if (!respuesta.ok) throw new Error(`GET timeline -> ${respuesta.status}`);
  return respuesta.json();
}

export async function marcarHito(cursoId: string, tareaId: string, repoId: string, sha: string, nota: string) {
  return apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repos/${repoId}/commits/${sha}/hito`, {
    method: "POST",
    body: JSON.stringify({ nota }),
  });
}

export async function desmarcarHito(cursoId: string, tareaId: string, repoId: string, sha: string) {
  return apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repos/${repoId}/commits/${sha}/hito`, {
    method: "DELETE",
  });
}

export interface IdentidadGit {
  id: string;
  email: string | null;
  nombre_visto: string | null;
  estado: string;
  estudiante: string | null;
  commits_contables: number;
}

export interface CandidatoPropagacion {
  repositorio_id: string;
  repositorio: string;
  identidad_id: string;
  nombre_visto: string | null;
  commits: number;
  marcada: boolean;
}

function baseIdentidades(cursoId: string, tareaId: string, repoId: string) {
  return `/api/cursos/${cursoId}/tareas/${tareaId}/repos/${repoId}/identidades`;
}

export async function listarIdentidades(cursoId: string, tareaId: string, repoId: string): Promise<IdentidadGit[]> {
  const respuesta = await apiFetch(baseIdentidades(cursoId, tareaId, repoId));
  if (!respuesta.ok) return [];
  return respuesta.json();
}

export async function obtenerPropagacion(
  cursoId: string,
  tareaId: string,
  repoId: string,
  identidadId: string,
): Promise<CandidatoPropagacion[]> {
  const respuesta = await apiFetch(`${baseIdentidades(cursoId, tareaId, repoId)}/${identidadId}/propagacion`);
  if (!respuesta.ok) return [];
  return respuesta.json();
}

export async function resolverIdentidad(
  cursoId: string,
  tareaId: string,
  repoId: string,
  identidadId: string,
  cuerpo: { estudiante_id?: string; no_es_estudiante?: boolean; propagar_a: string[]; confirmacion?: string },
): Promise<Resultado<IdentidadGit>> {
  return resultado(
    await apiFetch(`${baseIdentidades(cursoId, tareaId, repoId)}/${identidadId}/resolver`, {
      method: "POST",
      body: JSON.stringify(cuerpo),
    }),
  );
}

export async function revelarIdentidad(
  cursoId: string,
  tareaId: string,
  repoId: string,
  identidadId: string,
): Promise<string | null> {
  const respuesta = await apiFetch(`${baseIdentidades(cursoId, tareaId, repoId)}/${identidadId}/revelar`, {
    method: "POST",
  });
  if (!respuesta.ok) return null;
  return (await respuesta.json()).email;
}

// --- Etapa F8: cierre de la tarea (A-168, A-197) ---

export interface GuardaArchivado {
  numero: number;
  titulo: string;
  cumple: boolean;
  motivo: string | null;
  confirmacion: "SIN_CAPTURA" | "SIN_AVISO" | null;
  detalle: string[];
}

export interface EstadoArchivado {
  tarea_estado: string;
  archivables: number;
  archivados: number;
  fuera_de_alcance_o_inaccesibles: number;
  guardas: GuardaArchivado[];
  permitido: boolean;
  aviso: {
    destinatarios: number;
    encolados: number;
    enviados: number;
    bloqueados: number;
    ultimo_envio: string | null;
    canal_bloqueado: boolean;
  };
  en_curso: number;
  puede_desarchivar: boolean;
}

export async function obtenerArchivado(cursoId: string, tareaId: string): Promise<EstadoArchivado> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/archivado`);
  if (!respuesta.ok) throw new Error(`GET archivado -> ${respuesta.status}`);
  return respuesta.json();
}

export async function enviarAvisoArchivado(
  cursoId: string,
  tareaId: string,
): Promise<Resultado<{ encolados: number }>> {
  return resultado(await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/archivar/aviso`, { method: "POST" }));
}

export async function archivarTarea(
  cursoId: string,
  tareaId: string,
  confirmaciones: { confirmacion_sin_captura: string | null; confirmacion_sin_aviso: string | null },
): Promise<Resultado<{ repositorios: number }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/archivar`, {
      method: "POST",
      body: JSON.stringify(confirmaciones),
    }),
  );
}

export async function desarchivarTarea(
  cursoId: string,
  tareaId: string,
): Promise<Resultado<{ repositorios: number }>> {
  return resultado(await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/desarchivar`, { method: "POST" }));
}

export async function obtenerRepositoriosTarea(cursoId: string, tareaId: string): Promise<RepositoriosTarea> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repositorios`);
  if (!respuesta.ok) throw new Error(`GET repositorios -> ${respuesta.status}`);
  return respuesta.json();
}

export async function obtenerFechasEntregas(cursoId: string, tareaId: string): Promise<FechasEntrega[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/entregas/fechas`);
  if (!respuesta.ok) throw new Error(`GET fechas -> ${respuesta.status}`);
  return respuesta.json();
}

export async function reintentarRepositorio(
  cursoId: string,
  tareaId: string,
  repositorioId: string,
): Promise<Resultado<{ ok: boolean }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repositorios/${repositorioId}/reintentar`, {
      method: "POST",
    }),
  );
}

export async function sustituirRepositorio(
  cursoId: string,
  tareaId: string,
  repositorioId: string,
  confirmacion: string,
): Promise<Resultado<{ repositorio_id: string }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repositorios/${repositorioId}/sustituir`, {
      method: "POST",
      body: JSON.stringify({ confirmacion }),
    }),
  );
}

export async function previsualizarArchivoBase(
  cursoId: string,
  tareaId: string,
  ruta: string,
): Promise<Resultado<PrevisualizacionArchivo>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/repositorio-base/archivos/${rutaCodificada(ruta)}`),
  );
}

// --- Etapa F9: informe docente diario y suscripcion (SPEC 11 S11.3-S11.5) ---

export interface InformesCurso {
  se_genera_desde: string | null;
  informes: { fecha: string; estado: string; motivo: string | null; origen: string }[];
}

export interface InformeDia {
  fecha: string;
  estado: string;
  motivo: string | null;
  html: string | null;
  texto: string | null;
  asunto: string | null;
}

export interface VistaPreviaInforme {
  hay_tareas_activas: boolean;
  mensaje: string | null;
  html: string | null;
  texto: string | null;
}

export interface SuscripcionInforme {
  curso_id: string;
  curso_nombre: string;
  curso_codigo: string;
  activa: boolean;
  origen_baja: string | null;
  se_genera_desde: string | null;
}

export async function obtenerInformes(cursoId: string): Promise<InformesCurso> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/informes`);
  if (!respuesta.ok) throw new Error(`GET informes -> ${respuesta.status}`);
  return respuesta.json();
}

export async function obtenerInformeDia(cursoId: string, fecha: string): Promise<InformeDia | null> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/informes/${fecha}`);
  if (!respuesta.ok) return null;
  return respuesta.json();
}

export async function obtenerVistaPreviaInforme(cursoId: string): Promise<VistaPreviaInforme> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/informe-de-hoy/vista-previa`);
  if (!respuesta.ok) throw new Error(`GET vista previa -> ${respuesta.status}`);
  return respuesta.json();
}

export async function enviarmeInforme(cursoId: string): Promise<Resultado<{ encolados: number }>> {
  return resultado(await apiFetch(`/api/cursos/${cursoId}/informe-de-hoy/enviarme`, { method: "POST" }));
}

export async function enviarInformeASuscritos(cursoId: string): Promise<Resultado<{ encolados: number }>> {
  return resultado(await apiFetch(`/api/cursos/${cursoId}/informe-de-hoy/enviar`, { method: "POST" }));
}

export async function obtenerMisNotificaciones(cursoId: string): Promise<SuscripcionInforme> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/mis-notificaciones`);
  if (!respuesta.ok) throw new Error(`GET mis-notificaciones -> ${respuesta.status}`);
  return respuesta.json();
}

export async function cambiarMisNotificaciones(cursoId: string, activa: boolean): Promise<SuscripcionInforme> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/mis-notificaciones`, {
    method: "PUT",
    body: JSON.stringify({ activa }),
  });
  if (!respuesta.ok) throw new Error(`PUT mis-notificaciones -> ${respuesta.status}`);
  return respuesta.json();
}

export async function obtenerNotificacionesPerfil(): Promise<SuscripcionInforme[]> {
  const respuesta = await apiFetch("/api/perfil/notificaciones");
  if (!respuesta.ok) return [];
  return respuesta.json();
}

export async function cambiarTodasLasNotificaciones(activa: boolean): Promise<SuscripcionInforme[]> {
  const respuesta = await apiFetch("/api/perfil/notificaciones", {
    method: "PUT",
    body: JSON.stringify({ activa }),
  });
  if (!respuesta.ok) throw new Error(`PUT notificaciones -> ${respuesta.status}`);
  return respuesta.json();
}

export async function regenerarEnlacesDeBaja(): Promise<boolean> {
  const respuesta = await apiFetch("/api/perfil/enlaces-de-baja/regenerar", { method: "POST" });
  return respuesta.ok;
}

export interface EstadoBaja {
  curso_nombre: string;
  curso_codigo: string;
  activa: boolean;
  otros_cursos_suscritos: number;
}

export async function obtenerBaja(token: string): Promise<EstadoBaja | null> {
  const respuesta = await fetch(`${API_BASE_URL}/api/baja/${encodeURIComponent(token)}`, {
    credentials: "include",
  });
  if (!respuesta.ok) return null;
  return respuesta.json();
}

export async function aplicarBaja(token: string, accion: "baja" | "alta"): Promise<EstadoBaja | null> {
  const respuesta = await fetch(`${API_BASE_URL}/api/baja/${encodeURIComponent(token)}?accion=${accion}`, {
    method: "POST",
    credentials: "include",
  });
  if (!respuesta.ok) return null;
  return respuesta.json();
}

// --- Etapa F10: comunicaciones ampliadas (SPEC 11 S11.6-S11.8, S11.10) ---

export interface MensajeBandeja {
  id: string;
  canal: string;
  evento: string;
  estado: string;
  etiqueta_estado: string;
  motivo: string | null;
  destinatario: string;
  asunto: string | null;
  cuerpo: string | null;
  origen: string;
  generacion: number;
  reemplaza_a_id: string | null;
  tarea_id: string | null;
  creado_en: string;
  enviado_en: string | null;
  programado_para: string | null;
  enlace_canvas: string | null;
  motivo_sin_enlace: string | null;
  ultimo_error: string | null;
}

export interface Bandeja {
  comunicaciones_salientes: string;
  suspension_motivo: string | null;
  canal_activo: string | null;
  mensajes: MensajeBandeja[];
}

export async function obtenerBandeja(cursoId: string, filtros: Record<string, string>): Promise<Bandeja> {
  const q = new URLSearchParams(Object.entries(filtros).filter(([, v]) => v));
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/comunicaciones?${q}`);
  if (!respuesta.ok) throw new Error(`GET comunicaciones -> ${respuesta.status}`);
  return respuesta.json();
}

export async function accionSobreMensaje(
  cursoId: string,
  mensajeId: string,
  accion: "reintentar" | "reenviar" | "cancelar" | "retractar",
): Promise<Resultado<MensajeBandeja>> {
  return resultado(await apiFetch(`/api/cursos/${cursoId}/comunicaciones/${mensajeId}/${accion}`, { method: "POST" }));
}

export async function enviarMensajeManual(
  cursoId: string,
  cuerpo: {
    estudiante_ids: string[];
    grupo_id: string | null;
    asunto: string;
    cuerpo: string;
    confirmar_no_activos?: boolean;
  },
): Promise<Resultado<{ encolados: number; aviso: string }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/comunicaciones/mensajes`, { method: "POST", body: JSON.stringify(cuerpo) }),
  );
}

export async function publicarAnuncio(
  cursoId: string,
  cuerpo: { titulo: string; cuerpo_html: string; seccion_ids: string[]; confirmacion_destinatarios?: number },
): Promise<Resultado<{ destinatarios: number }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/comunicaciones/anuncios`, { method: "POST", body: JSON.stringify(cuerpo) }),
  );
}

export async function cambiarSuspension(
  cursoId: string,
  suspendidas: boolean,
  motivo: string | null,
): Promise<Resultado<{ comunicaciones_salientes: string }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/comunicaciones`, {
      method: "PATCH",
      body: JSON.stringify({ suspendidas, motivo }),
    }),
  );
}

export interface ReglaComunicacion {
  evento: string;
  titulo: string;
  activa: boolean;
  por_defecto: boolean;
  advertencia_al_apagar: string | null;
  destinatarios_hoy: number | null;
  vista_previa_asunto: string;
  vista_previa_cuerpo: string;
  vista_previa_con_ejemplo: boolean;
}

export async function obtenerReglasTarea(cursoId: string, tareaId: string): Promise<ReglaComunicacion[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/comunicaciones`);
  if (!respuesta.ok) return [];
  return respuesta.json();
}

export async function cambiarReglaTarea(
  cursoId: string,
  tareaId: string,
  evento: string,
  activa: boolean,
): Promise<Resultado<Record<string, number | boolean | string>>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/comunicaciones/${evento}`, {
      method: "PUT",
      body: JSON.stringify({ activa }),
    }),
  );
}

export async function obtenerReglaMapeo(cursoId: string): Promise<ReglaComunicacion | null> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/comunicaciones-curso/recordatorio-mapeo`);
  if (!respuesta.ok) return null;
  return respuesta.json();
}

export async function cambiarReglaMapeo(cursoId: string, activa: boolean): Promise<Resultado<Record<string, unknown>>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/comunicaciones-curso/recordatorio-mapeo`, {
      method: "PUT",
      body: JSON.stringify({ activa }),
    }),
  );
}

export async function suprimirComunicaciones(
  cursoId: string,
  estudianteId: string,
  alcance: "TODAS_AUTOMATICAS" | "SOLO_RECORDATORIOS",
  motivo: string,
): Promise<Resultado<{ alcance: string }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/estudiantes/${estudianteId}/supresion`, {
      method: "POST",
      body: JSON.stringify({ alcance, motivo }),
    }),
  );
}

export async function levantarSupresion(cursoId: string, estudianteId: string): Promise<Resultado<{ levantada: boolean }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/estudiantes/${estudianteId}/supresion`, { method: "DELETE" }),
  );
}
