import { errorRespuesta, detalleLegible } from "./errores";
/**
 * Origen de la API, sin barra final. En produccion va vacio: Vercel hace de
 * proxy de `/api` y `/auth` hacia la API (`vercel.json`), las peticiones son del
 * mismo origen y las cookies de sesion quedan first-party. En local apunta a
 * `http://localhost:8000`. Ausente cuenta como vacio, nunca como "undefined".
 */
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "")
  .trim()
  .replace(/\/+$/, "");

function leerCookie(nombre: string): string | null {
  const partes = document.cookie
    .split("; ")
    .find((fila) => fila.startsWith(`${nombre}=`));
  return partes
    ? decodeURIComponent(partes.split("=").slice(1).join("="))
    : null;
}

/**
 * Toda peticion viaja con `credentials: "include"` (sesion opaca por cookie,
 * SPEC 02 S2.2.6). Las mutaciones agregan `X-CSRF-Token` desde la cookie de
 * doble envio `csrf_token`, que el backend exige (S2.2.6).
 */
export async function apiFetch(
  path: string,
  opciones: RequestInit = {},
): Promise<Response> {
  const metodo = (opciones.method ?? "GET").toUpperCase();
  const cabeceras = new Headers(opciones.headers);

  if (metodo !== "GET" && metodo !== "HEAD") {
    const csrf = leerCookie("csrf_token");
    if (csrf) cabeceras.set("X-CSRF-Token", csrf);
    if (!cabeceras.has("Content-Type") && opciones.body) {
      cabeceras.set("Content-Type", "application/json");
    }
  }

  const respuesta = await fetch(`${API_BASE_URL}${path}`, {
    ...opciones,
    credentials: "include",
    headers: cabeceras,
  });
  if (respuesta.status === 401 || respuesta.status === 403) {
    window.dispatchEvent(
      new CustomEvent("pds2:acceso", {
        detail: { status: respuesta.status, path },
      }),
    );
  }
  return respuesta;
}

export interface Perfil {
  id: string;
  email: string;
  nombre: string;
  avatar_url: string | null;
  github_login_declarado: string | null;
  activo: boolean;
}

export async function obtenerPerfil(
  signal?: AbortSignal,
): Promise<Perfil | null> {
  const respuesta = await apiFetch("/api/perfil", { signal });
  if (respuesta.status === 401) return null;
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export interface Capacidades {
  perfil: "parcial" | "completo";
  banderas: string[];
}

export async function obtenerCapacidades(
  signal?: AbortSignal,
): Promise<Capacidades> {
  const respuesta = await apiFetch("/api/capacidades", { signal });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
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
  umbral_dias_sin_actividad?: number;
  umbral_desbalance_pct?: number;
}

export async function listarCursos(signal?: AbortSignal): Promise<Curso[]> {
  const respuesta = await apiFetch("/api/cursos", { signal });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
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
  const respuesta = await apiFetch("/api/cursos", {
    method: "POST",
    body: JSON.stringify(datos),
  });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
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
  es_via_compartida?: boolean;
  github_login?: string | null;
  github_estado?: string | null;
  github_error?: string | null;
}

export async function listarEquipo(
  cursoId: string,
  signal?: AbortSignal,
): Promise<Miembro[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/equipo`, { signal });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export interface Contexto {
  rol: string;
  permisos_efectivos: string[];
  es_via_compartida?: boolean;
}

export async function obtenerContexto(
  cursoId: string,
  signal?: AbortSignal,
): Promise<Contexto> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/contexto`, {
    signal,
  });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
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

export async function retirarMiembro(
  cursoId: string,
  membresiaId: string,
): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/equipo/${membresiaId}/retiro`, {
    method: "POST",
  });
}

export async function reincorporarMiembro(
  cursoId: string,
  membresiaId: string,
  permisos: string[],
): Promise<Response> {
  return apiFetch(
    `/api/cursos/${cursoId}/equipo/${membresiaId}/reincorporacion`,
    {
      method: "POST",
      body: JSON.stringify({ permisos }),
    },
  );
}

export interface InvitacionPublica {
  curso_nombre: string;
  rol: string;
  permisos: string[];
  email_enmascarado: string;
  estado: string;
}

export async function obtenerInvitacionPublica(
  token: string,
  signal?: AbortSignal,
): Promise<InvitacionPublica> {
  const respuesta = await apiFetch(`/api/invitaciones/${token}`, { signal });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function aceptarInvitacionConSesion(
  token: string,
): Promise<Response> {
  return apiFetch(`/api/invitaciones/${token}/aceptar`, { method: "POST" });
}

// --- Etapa P3: vinculacion con Canvas (SPEC 04 S4.5, SPEC 05 S5.2) ---

export interface InstanciaCanvas {
  base_url: string;
  nombre_visible: string;
}

export async function listarInstanciasCanvas(
  signal?: AbortSignal,
): Promise<InstanciaCanvas[]> {
  const respuesta = await apiFetch("/api/canvas/instancias", { signal });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export interface CursoCanvasDisponible {
  canvas_course_id: number;
  nombre: string;
  codigo: string;
  termino: string | null;
  total_estudiantes: number | null;
  ya_vinculado_a: string | null;
  ya_vinculado_a_id: string | null;
  es_vinculo_actual: boolean;
}

export async function listarCursosCanvasDisponibles(
  cursoId: string,
  datos: { token: string; canvas_base_url: string },
): Promise<{ ok: boolean; cursos: CursoCanvasDisponible[]; error?: string }> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/vinculacion/canvas/cursos-disponibles`,
    {
      method: "POST",
      body: JSON.stringify(datos),
    },
  );
  const cuerpo = await respuesta.json().catch(() => []);
  if (!respuesta.ok)
    return {
      ok: false,
      cursos: [],
      error: detalleLegible(cuerpo.detail) || String(respuesta.status),
    };
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

export async function obtenerEstadoVinculacionCanvas(
  cursoId: string,
  signal?: AbortSignal,
): Promise<CredencialCanvasEstado[]> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/vinculacion/canvas`,
    { signal },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

// --- Etapa P4: vinculacion con GitHub y checklist (SPEC 04 S4.6-S4.7) ---

export async function iniciarInstalacionGithub(
  cursoId: string,
  orgLoginSugerido?: string,
): Promise<{ instalar_url: string }> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/vinculacion/github/iniciar`,
    {
      method: "POST",
      body: JSON.stringify({ org_login_sugerido: orgLoginSugerido ?? null }),
    },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export interface CallbackInstalacionResultado {
  resultado:
    | "VINCULADO"
    | "SOLICITUD_PENDIENTE"
    | "SIN_INSTALLATION_ID"
    | "STATE_INVALIDO";
  curso_id?: string;
  org_login?: string;
  equipo_docentes_slug?: string;
  curso_estado?: string;
}

export async function confirmarCallbackGithub(datos: {
  state: string;
  installation_id?: number;
  setup_action?: string;
}): Promise<{
  ok: boolean;
  cuerpo: CallbackInstalacionResultado | { detail: unknown };
}> {
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

export async function obtenerEstadoVinculacionGithub(
  cursoId: string,
  signal?: AbortSignal,
): Promise<EstadoVinculacionGithub> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/vinculacion/github`,
    { signal },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export interface InstalacionHuerfana {
  installation_id: number;
  org_login: string;
  actualizada_en: string;
}

export async function listarInstalacionesHuerfanas(
  cursoId: string,
  signal?: AbortSignal,
): Promise<InstalacionHuerfana[]> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/vinculacion/github/huerfanas`,
    { signal },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function adoptarInstalacionHuerfana(
  cursoId: string,
  datos: { installation_id: number; org_login_confirmado: string },
): Promise<Response> {
  return apiFetch(
    `/api/cursos/${cursoId}/vinculacion/github/huerfanas/adoptar`,
    {
      method: "POST",
      body: JSON.stringify(datos),
    },
  );
}

export interface ItemVerificacion {
  item: string | null;
  resultado:
    | "CORRECTO"
    | "ADVERTENCIA"
    | "BLOQUEANTE"
    | "NO_VERIFICADO"
    | "VERIFICADO_A_MANO";
  detalle: Record<string, unknown>;
  ejecutada_en: string;
}

export async function encolarChecklist(
  cursoId: string,
): Promise<{ ejecucion_id: string }> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/verificacion`, {
    method: "POST",
  });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function reejecutarItem(
  cursoId: string,
  item: string,
): Promise<{ ejecucion_id: string }> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/verificacion/items/${item}`,
    {
      method: "POST",
    },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerEjecucionVerificacion(
  cursoId: string,
  ejecucionId: string,
  signal?: AbortSignal,
): Promise<ItemVerificacion[]> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/verificacion/${ejecucionId}`,
    { signal },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerUltimaVerificacion(
  cursoId: string,
  signal?: AbortSignal,
): Promise<ItemVerificacion[]> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/verificacion/ultima`,
    { signal },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function firmarItem14AMano(
  cursoId: string,
): Promise<ItemVerificacion> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/verificacion/items/14/firmar`,
    {
      method: "POST",
    },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function ejecutarPruebaEscritura(
  cursoId: string,
  item: "5-bis" | "17-bis",
  consiento: boolean,
): Promise<ItemVerificacion> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/verificacion/items/${item}`,
    {
      method: "POST",
      body: JSON.stringify({ consiento }),
    },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
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

export async function obtenerPersonas(
  cursoId: string,
  signal?: AbortSignal,
): Promise<Personas> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/personas`, {
    signal,
  });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export interface CabeceraPersonas {
  con_cuenta_verificada: number;
  total: number;
}

export async function obtenerCabeceraPersonas(
  cursoId: string,
): Promise<CabeceraPersonas> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/personas/cabecera`);
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function sincronizarAhora(cursoId: string): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/sincronizaciones`, {
    method: "POST",
  });
}

// --- Etapa P6: mapeo estudiante <-> GitHub y Pendientes (SPEC 07 S7.4-S7.8) ---

export async function declararMapeoManual(
  cursoId: string,
  estudianteId: string,
  login: string,
): Promise<{
  ok: boolean;
  cuerpo: MapeoGithubEspejo | { detail: { motivo: string; detalle: string } };
}> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/personas/${estudianteId}/mapeo`,
    {
      method: "POST",
      body: JSON.stringify({ login }),
    },
  );
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
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/mapeo/importar-csv`,
    {
      method: "POST",
      body: JSON.stringify({ csv, aplicar: aplicar ? "true" : "false" }),
    },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function crearRegistroGithub(cursoId: string): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/registro-github`, { method: "POST" });
}

export async function restaurarRegistroGithub(
  cursoId: string,
): Promise<Response> {
  return apiFetch(`/api/cursos/${cursoId}/registro-github/restaurar`, {
    method: "POST",
  });
}

export interface FilaPendienteSinCuenta {
  recordatorios_enviados?: number;
  recordatorios_en_cola?: number;
  maximo_recordatorios?: number;
  ultimo_recordatorio_en?: string | null;
  proximo_recordatorio_en?: string | null;
  recordatorio_bloqueado?: string | null;
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
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function enviarRecordatorio(
  cursoId: string,
  estudianteId: string,
): Promise<Response> {
  return apiFetch(
    `/api/cursos/${cursoId}/pendientes/${estudianteId}/recordatorio`,
    { method: "POST" },
  );
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
  if (!respuesta.ok) {
    const error = await errorRespuesta(respuesta);
    return {
      ok: false,
      status: respuesta.status,
      datos: null,
      error: error.message,
    };
  }
  const cuerpo: unknown = await respuesta.json().catch(() => null);
  return {
    ok: true,
    status: respuesta.status,
    datos: cuerpo as T,
    error: null,
  };
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
  canvas_group_category_id?: number | null;
  conjunto_grupos_nombre?: string | null;
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

export async function listarTareas(
  cursoId: string,
  signal?: AbortSignal,
): Promise<TareaResumen[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas`, { signal });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerAssignmentsCanvas(
  cursoId: string,
  signal?: AbortSignal,
): Promise<AssignmentsCanvas> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/tareas/assignments-canvas`,
    { signal },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerVistaPreviaNombre(
  cursoId: string,
  nombre: string,
  slug: string,
  signal?: AbortSignal,
): Promise<VistaPreviaNombre> {
  const parametros = new URLSearchParams({ nombre });
  if (slug.trim()) parametros.set("slug", slug.trim());
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/tareas/vista-previa-nombre?${parametros}`,
    { signal },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function crearTarea(
  cursoId: string,
  datos: {
    nombre: string;
    slug: string | null;
    canvas_assignment_id: number;
    gitignore_template: string | null;
  },
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas`, {
      method: "POST",
      body: JSON.stringify(datos),
    }),
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
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/entregas/${entregaId}/excluir`,
      { method: "POST" },
    ),
  );
}

export async function obtenerTarea(
  cursoId: string,
  tareaId: string,
  signal?: AbortSignal,
): Promise<TareaDetalle> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}`, {
    signal,
  });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function activarTarea(
  cursoId: string,
  tareaId: string,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/activar`, {
      method: "POST",
    }),
  );
}

export async function desvincularEntrega(
  cursoId: string,
  tareaId: string,
  entregaId: string,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/entregas/${entregaId}`,
      { method: "DELETE" },
    ),
  );
}

export async function crearRepositorioBase(
  cursoId: string,
  tareaId: string,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/repositorio-base`,
      { method: "POST" },
    ),
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
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/repositorio-base/archivos/${rutaCodificada(ruta)}`,
      {
        method: "PUT",
        body: JSON.stringify({ contenido_base64: contenidoBase64 }),
      },
    ),
  );
}

export async function borrarArchivoBase(
  cursoId: string,
  tareaId: string,
  ruta: string,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/repositorio-base/archivos/${rutaCodificada(ruta)}`,
      {
        method: "DELETE",
      },
    ),
  );
}

export async function renombrarArchivoBase(
  cursoId: string,
  tareaId: string,
  desde: string,
  hacia: string,
): Promise<Resultado<TareaDetalle>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/repositorio-base/renombrar`,
      {
        method: "POST",
        body: JSON.stringify({ desde, hacia }),
      },
    ),
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
  acceso_verificado_en?: string | null;
  invitacion_url: string | null;
  acceso_docente: string | null;
  reemplaza_a_id: string | null;
  listo_en: string | null;
}

export interface RepositoriosTarea {
  resumen: ResumenRepositorios;
  filas: FilaRepositorio[];
  verificacion_accesos?: VerificacionAccesos;
}

export interface VerificacionAccesos {
  intervalo_segundos: number;
  trabajo_id: string | null;
  estado: string | null;
  solicitado_en: string | null;
  disponible_en: string | null;
}

export async function verificarAccesosRepositorios(
  cursoId: string,
  tareaId: string,
): Promise<Resultado<VerificacionAccesos>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/repositorios/verificar-accesos`,
      { method: "POST" },
    ),
  );
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
  ambiguas: {
    sujeto_id: string;
    sujeto: string;
    fecha: string;
    candidatas: CandidataFecha[];
  }[];
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
export async function obtenerHistorialFechas(
  cursoId: string,
  entregaId: string,
): Promise<HistorialFechasSujeto[]> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/entregas/${entregaId}/historial-fechas`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
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
  enlaces: {
    arbol: string | null;
    comparacion: string | null;
    zip: string | null;
  };
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

export async function obtenerProgresoCaptura(
  cursoId: string,
  entregaId: string,
): Promise<ProgresoCaptura> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/entregas/${entregaId}/progreso-captura`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerFichaVersion(
  cursoId: string,
  entregaId: string,
  sujetoId: string,
): Promise<FichaVersion> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/entregas/${entregaId}/sujetos/${sujetoId}/version`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
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
    await apiFetch(
      `/api/cursos/${cursoId}/entregas/${entregaId}/sujetos/${sujetoId}/version/${tipo}`,
      {
        method: "POST",
        body: JSON.stringify(cuerpo),
      },
    ),
  );
}

export async function registrarVersiones(
  cursoId: string,
  entregaId: string,
): Promise<Resultado<{ encoladas: number }>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/entregas/${entregaId}/registrar-versiones`,
      { method: "POST" },
    ),
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
  filtros: {
    periodo?: string;
    seccion?: string;
    grupoEstado?: string;
    soloAlertas?: boolean;
  },
): Promise<Tablero> {
  const q = new URLSearchParams();
  if (filtros.periodo) q.set("periodo", filtros.periodo);
  if (filtros.seccion) q.set("seccion", filtros.seccion);
  if (filtros.grupoEstado) q.set("grupo_estado", filtros.grupoEstado);
  if (filtros.soloAlertas) q.set("solo_alertas", "true");
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/tareas/${tareaId}/tablero?${q.toString()}`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function actualizarTablero(
  cursoId: string,
  tareaId: string,
): Promise<{ encolada: boolean; en_curso: boolean; disponible_en: string }> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/tareas/${tareaId}/tablero/actualizar`,
    {
      method: "POST",
    },
  );
  return respuesta.json();
}

export async function silenciarIncidencia(
  cursoId: string,
  incidenciaId: string,
): Promise<boolean> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/incidencias/${incidenciaId}/silenciar`,
    {
      method: "POST",
    },
  );
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

export async function obtenerSeguimiento(
  cursoId: string,
): Promise<FilaSeguimiento[]> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/seguimiento`);
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
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
  repositorio: {
    id: string;
    nombre: string;
    estado: string;
    rama_por_defecto: string | null;
  };
  sujeto: string;
  periodos: { clave: string; etiqueta: string }[];
  periodo: string;
  dias: {
    dia: string;
    colapsado: boolean;
    hasta: string | null;
    n_dias: number;
    commits: CommitTimeline[];
  }[];
  ciclo_de_vida: {
    fecha: string;
    tipo: string;
    detalle: Record<string, unknown>;
  }[];
  marcas_entrega: {
    orden: number;
    entrega: string;
    fecha: string | null;
    aplica: boolean;
    versiones: {
      intento: number;
      vigente: boolean;
      estado: string;
      motivo: string | null;
      commit_sha: string | null;
    }[];
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
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/tareas/${tareaId}/repos/${repoId}/timeline?${q}`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function marcarHito(
  cursoId: string,
  tareaId: string,
  repoId: string,
  sha: string,
  nota: string,
) {
  return apiFetch(
    `/api/cursos/${cursoId}/tareas/${tareaId}/repos/${repoId}/commits/${sha}/hito`,
    {
      method: "POST",
      body: JSON.stringify({ nota }),
    },
  );
}

export async function desmarcarHito(
  cursoId: string,
  tareaId: string,
  repoId: string,
  sha: string,
) {
  return apiFetch(
    `/api/cursos/${cursoId}/tareas/${tareaId}/repos/${repoId}/commits/${sha}/hito`,
    {
      method: "DELETE",
    },
  );
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

export async function listarIdentidades(
  cursoId: string,
  tareaId: string,
  repoId: string,
): Promise<IdentidadGit[]> {
  const respuesta = await apiFetch(baseIdentidades(cursoId, tareaId, repoId));
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerPropagacion(
  cursoId: string,
  tareaId: string,
  repoId: string,
  identidadId: string,
): Promise<CandidatoPropagacion[]> {
  const respuesta = await apiFetch(
    `${baseIdentidades(cursoId, tareaId, repoId)}/${identidadId}/propagacion`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function resolverIdentidad(
  cursoId: string,
  tareaId: string,
  repoId: string,
  identidadId: string,
  cuerpo: {
    estudiante_id?: string;
    no_es_estudiante?: boolean;
    propagar_a: string[];
    confirmacion?: string;
  },
): Promise<Resultado<IdentidadGit>> {
  return resultado(
    await apiFetch(
      `${baseIdentidades(cursoId, tareaId, repoId)}/${identidadId}/resolver`,
      {
        method: "POST",
        body: JSON.stringify(cuerpo),
      },
    ),
  );
}

export async function revelarIdentidad(
  cursoId: string,
  tareaId: string,
  repoId: string,
  identidadId: string,
): Promise<string | null> {
  const respuesta = await apiFetch(
    `${baseIdentidades(cursoId, tareaId, repoId)}/${identidadId}/revelar`,
    {
      method: "POST",
    },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
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

export async function obtenerArchivado(
  cursoId: string,
  tareaId: string,
): Promise<EstadoArchivado> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/tareas/${tareaId}/archivado`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function enviarAvisoArchivado(
  cursoId: string,
  tareaId: string,
): Promise<Resultado<{ encolados: number }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/archivar/aviso`, {
      method: "POST",
    }),
  );
}

export async function archivarTarea(
  cursoId: string,
  tareaId: string,
  confirmaciones: {
    confirmacion_sin_captura: string | null;
    confirmacion_sin_aviso: string | null;
  },
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
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/tareas/${tareaId}/desarchivar`, {
      method: "POST",
    }),
  );
}

export async function obtenerRepositoriosTarea(
  cursoId: string,
  tareaId: string,
  signal?: AbortSignal,
): Promise<RepositoriosTarea> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/tareas/${tareaId}/repositorios`,
    { signal },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerFechasEntregas(
  cursoId: string,
  tareaId: string,
  signal?: AbortSignal,
): Promise<FechasEntrega[]> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/tareas/${tareaId}/entregas/fechas`,
    { signal },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function reintentarRepositorio(
  cursoId: string,
  tareaId: string,
  repositorioId: string,
): Promise<Resultado<{ ok: boolean }>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/repositorios/${repositorioId}/reintentar`,
      {
        method: "POST",
      },
    ),
  );
}

export async function sustituirRepositorio(
  cursoId: string,
  tareaId: string,
  repositorioId: string,
  confirmacion: string,
): Promise<Resultado<{ repositorio_id: string }>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/repositorios/${repositorioId}/sustituir`,
      {
        method: "POST",
        body: JSON.stringify({ confirmacion }),
      },
    ),
  );
}

export async function previsualizarArchivoBase(
  cursoId: string,
  tareaId: string,
  ruta: string,
): Promise<Resultado<PrevisualizacionArchivo>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/repositorio-base/archivos/${rutaCodificada(ruta)}`,
    ),
  );
}

// --- Etapa F9: informe docente diario y suscripcion (SPEC 11 S11.3-S11.5) ---

export interface InformesCurso {
  se_genera_desde: string | null;
  informes: {
    fecha: string;
    estado: string;
    motivo: string | null;
    origen: string;
  }[];
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
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerInformeDia(
  cursoId: string,
  fecha: string,
): Promise<InformeDia | null> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/informes/${fecha}`);
  if ([404, 410].includes(respuesta.status)) return null;
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerVistaPreviaInforme(
  cursoId: string,
): Promise<VistaPreviaInforme> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/informe-de-hoy/vista-previa`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function enviarmeInforme(
  cursoId: string,
): Promise<Resultado<{ encolados: number }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/informe-de-hoy/enviarme`, {
      method: "POST",
    }),
  );
}

export async function enviarInformeASuscritos(
  cursoId: string,
): Promise<Resultado<{ encolados: number }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/informe-de-hoy/enviar`, {
      method: "POST",
    }),
  );
}

export async function obtenerMisNotificaciones(
  cursoId: string,
): Promise<SuscripcionInforme> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/mis-notificaciones`);
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function cambiarMisNotificaciones(
  cursoId: string,
  activa: boolean,
): Promise<SuscripcionInforme> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/mis-notificaciones`,
    {
      method: "PUT",
      body: JSON.stringify({ activa }),
    },
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerNotificacionesPerfil(): Promise<
  SuscripcionInforme[]
> {
  const respuesta = await apiFetch("/api/perfil/notificaciones");
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function cambiarTodasLasNotificaciones(
  activa: boolean,
): Promise<SuscripcionInforme[]> {
  const respuesta = await apiFetch("/api/perfil/notificaciones", {
    method: "PUT",
    body: JSON.stringify({ activa }),
  });
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function regenerarEnlacesDeBaja(): Promise<boolean> {
  const respuesta = await apiFetch("/api/perfil/enlaces-de-baja/regenerar", {
    method: "POST",
  });
  return respuesta.ok;
}

export interface EstadoBaja {
  curso_nombre: string;
  curso_codigo: string;
  activa: boolean;
  otros_cursos_suscritos: number;
}

export async function obtenerBaja(token: string): Promise<EstadoBaja | null> {
  const respuesta = await fetch(
    `${API_BASE_URL}/api/baja/${encodeURIComponent(token)}`,
    {
      credentials: "include",
    },
  );
  if ([404, 410].includes(respuesta.status)) return null;
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function aplicarBaja(
  token: string,
  accion: "baja" | "alta",
): Promise<EstadoBaja | null> {
  const respuesta = await fetch(
    `${API_BASE_URL}/api/baja/${encodeURIComponent(token)}?accion=${accion}`,
    {
      method: "POST",
      credentials: "include",
    },
  );
  if ([404, 410].includes(respuesta.status)) return null;
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
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

export async function obtenerBandeja(
  cursoId: string,
  filtros: Record<string, string>,
): Promise<Bandeja> {
  const q = new URLSearchParams(Object.entries(filtros).filter(([, v]) => v));
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/comunicaciones?${q}`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function accionSobreMensaje(
  cursoId: string,
  mensajeId: string,
  accion: "reintentar" | "reenviar" | "cancelar" | "retractar",
): Promise<Resultado<MensajeBandeja>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/comunicaciones/${mensajeId}/${accion}`,
      { method: "POST" },
    ),
  );
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
    await apiFetch(`/api/cursos/${cursoId}/comunicaciones/mensajes`, {
      method: "POST",
      body: JSON.stringify(cuerpo),
    }),
  );
}

export async function publicarAnuncio(
  cursoId: string,
  cuerpo: {
    titulo: string;
    cuerpo_html: string;
    seccion_ids: string[];
    confirmacion_destinatarios?: number;
  },
): Promise<Resultado<{ destinatarios: number }>> {
  return resultado(
    await apiFetch(`/api/cursos/${cursoId}/comunicaciones/anuncios`, {
      method: "POST",
      body: JSON.stringify(cuerpo),
    }),
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

export async function obtenerReglasTarea(
  cursoId: string,
  tareaId: string,
): Promise<ReglaComunicacion[]> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/tareas/${tareaId}/comunicaciones`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function cambiarReglaTarea(
  cursoId: string,
  tareaId: string,
  evento: string,
  activa: boolean,
): Promise<Resultado<Record<string, number | boolean | string>>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/tareas/${tareaId}/comunicaciones/${evento}`,
      {
        method: "PUT",
        body: JSON.stringify({ activa }),
      },
    ),
  );
}

export async function obtenerReglaMapeo(
  cursoId: string,
): Promise<ReglaComunicacion | null> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/comunicaciones-curso/recordatorio-mapeo`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function cambiarReglaMapeo(
  cursoId: string,
  activa: boolean,
): Promise<Resultado<Record<string, unknown>>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/comunicaciones-curso/recordatorio-mapeo`,
      {
        method: "PUT",
        body: JSON.stringify({ activa }),
      },
    ),
  );
}

export async function suprimirComunicaciones(
  cursoId: string,
  estudianteId: string,
  alcance: "TODAS_AUTOMATICAS" | "SOLO_RECORDATORIOS",
  motivo: string,
): Promise<Resultado<{ alcance: string }>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/estudiantes/${estudianteId}/supresion`,
      {
        method: "POST",
        body: JSON.stringify({ alcance, motivo }),
      },
    ),
  );
}

export async function levantarSupresion(
  cursoId: string,
  estudianteId: string,
): Promise<Resultado<{ levantada: boolean }>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/estudiantes/${estudianteId}/supresion`,
      { method: "DELETE" },
    ),
  );
}

// --- Etapa F11: correccion (SPEC 12 S12.5-S12.8, S12.11) ---

export interface AsignacionPropia {
  entrega_id: string;
  entrega: string;
  tarea_id: string;
  sujeto_id: string;
  sujeto: string;
  estado: string;
  etiqueta: string;
  sin_commits: boolean;
  reclamo_abierto: boolean;
  version_desactualizada: boolean;
  nueva: boolean;
  actualizado_en: string;
}

export interface BandejaCorreccion {
  mis_asignaciones: AsignacionPropia[];
  contador: { asignadas: number; corregidas: number; publicadas: number };
  nuevas: number;
  sin_corrector: number;
  puede_repartir: boolean;
  puede_publicar: boolean;
  es_profesor: boolean;
  tareas: {
    id: string;
    nombre: string;
    entregas: { id: string; nombre: string; orden: number }[];
  }[];
}

export interface CeldaCorreccion {
  estado: string;
  etiqueta: string;
  corrector: string | null;
  publicable: boolean;
  motivo_no_publicable: string | null;
  banderas: string[];
  contraste: string;
}

export interface MatrizCorreccion {
  entregas: { id: string; nombre: string; orden: number }[];
  sujetos: {
    sujeto_id: string;
    sujeto: string;
    activo: boolean;
    seccion: string | null;
    celdas: Record<string, CeldaCorreccion>;
  }[];
  por_corrector: Record<string, Record<string, number>>;
  por_entrega: Record<string, Record<string, number>>;
  por_seccion: Record<string, Record<string, number>>;
  contador: {
    corregidas: number;
    con_nota_en_canvas: number;
    total: number;
    comprobado_en: string | null;
  };
}

export interface CriterioRubrica {
  id: string;
  description: string;
  points: number;
  ratings?: { id: string; description: string; points: number }[];
  learning_outcome_id?: string;
  criterion_use_range?: boolean;
  ignore_for_scoring?: boolean;
}

export interface PantallaCorreccion {
  entrega: {
    id: string;
    nombre: string;
    tarea_id: string;
    tarea: string;
    grading_type: string;
    puntos_posibles: number | null;
    fecha_efectiva: string | null;
    origen_fecha: string | null;
  };
  sujeto: {
    id: string;
    nombre: string;
    integrantes: string[];
    activo: boolean;
  };
  estado: string;
  etiqueta: string;
  corrector: string | null;
  es_propietario: boolean;
  puede_publicar: boolean;
  titular: string;
  publicable: boolean;
  motivo_no_publicable: string | null;
  banderas: {
    version_desactualizada: boolean;
    reclamo_abierto: boolean;
    sin_commits: boolean;
    reconocimiento_sin_codigo: boolean;
  };
  version: {
    id: string;
    estado: string;
    sha: string | null;
    sha_corto: string | null;
    tag: string | null;
    repositorio: string | null;
    fecha_corte: string;
  } | null;
  repositorio_estado: string | null;
  acceso_docente: string | null;
  motivo_sin_enlace: string | null;
  borrador: {
    nota: string | null;
    rubrica: Record<
      string,
      { points?: number; rating_id?: string; comments?: string }
    > | null;
    comentario: string | null;
    version: number;
  } | null;
  rubrica: {
    criterios: CriterioRubrica[];
    ajustes: Record<string, unknown>;
    usar_para_calificar: boolean;
    suma_sugerida: number | null;
    cambio_sin_revisar: boolean;
  };
  notas_internas: {
    clase: string;
    texto: string | null;
    desenlace: string | null;
    creada_en: string;
  }[];
  historial: {
    entrega: string;
    estado: string;
    nota_publicada: string | null;
  }[];
  canvas: {
    estudiante: string;
    score: number | null;
    calificada_en: string | null;
  }[];
  navegacion: {
    posicion: number;
    total: number;
    anterior: string | null;
    siguiente: string | null;
    siguiente_sin_corregir: string | null;
  };
}

export async function obtenerBandejaCorreccion(
  cursoId: string,
): Promise<BandejaCorreccion> {
  const respuesta = await apiFetch(`/api/cursos/${cursoId}/correccion`);
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerMatrizCorreccion(
  cursoId: string,
  tareaId: string,
): Promise<MatrizCorreccion> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/tareas/${tareaId}/correccion/estado`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerPantallaCorreccion(
  cursoId: string,
  entregaId: string,
  sujetoId: string,
): Promise<PantallaCorreccion | null> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/correccion/${entregaId}/${sujetoId}`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

function rutaCorreccion(cursoId: string, entregaId: string, sujetoId: string) {
  return `/api/cursos/${cursoId}/correccion/${entregaId}/${sujetoId}`;
}

export async function guardarBorradorCorreccion(
  cursoId: string,
  entregaId: string,
  sujetoId: string,
  cuerpo: {
    nota: string | null;
    rubrica: Record<string, unknown> | null;
    comentario: string | null;
    version: number | null;
  },
): Promise<Resultado<{ estado: string; version: number }>> {
  return resultado(
    await apiFetch(`${rutaCorreccion(cursoId, entregaId, sujetoId)}/borrador`, {
      method: "PUT",
      body: JSON.stringify(cuerpo),
    }),
  );
}

export async function marcarCorreccionLista(
  cursoId: string,
  entregaId: string,
  sujetoId: string,
): Promise<Resultado<{ estado: string; nota: string }>> {
  return resultado(
    await apiFetch(`${rutaCorreccion(cursoId, entregaId, sujetoId)}/lista`, {
      method: "POST",
    }),
  );
}

export async function agregarNotaInterna(
  cursoId: string,
  entregaId: string,
  sujetoId: string,
  ruta: "notas" | "reclamos" | "reclamos/cerrar",
  cuerpo: { texto: string; desenlace?: string },
): Promise<Resultado<Record<string, unknown>>> {
  return resultado(
    await apiFetch(`${rutaCorreccion(cursoId, entregaId, sujetoId)}/${ruta}`, {
      method: "POST",
      body: JSON.stringify(cuerpo),
    }),
  );
}

export interface CorrectorCurso {
  membresia_id: string;
  nombre: string;
  rol: string;
  peso: number;
  sin_github: boolean;
}

export async function obtenerCorrectores(
  cursoId: string,
): Promise<CorrectorCurso[]> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/correccion/correctores`,
  );
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json();
}

export interface PropuestaReparto {
  filas: {
    sujeto_id: string;
    sujeto: string;
    actual: string | null;
    propuesto: string | null;
    estado: string;
    sobrescribe: boolean;
  }[];
  totales: Record<string, number>;
  requiere_decision: string[];
}

export async function previsualizarReparto(
  cursoId: string,
  entregaId: string,
  cuerpo: {
    criterio: string;
    reasignar: boolean;
    manual?: Record<string, string | null>;
  },
): Promise<Resultado<PropuestaReparto>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/correccion/${entregaId}/reparto/previsualizar`,
      {
        method: "POST",
        body: JSON.stringify(cuerpo),
      },
    ),
  );
}

export async function aplicarReparto(
  cursoId: string,
  entregaId: string,
  cuerpo: {
    criterio: string;
    reasignar: boolean;
    manual?: Record<string, string | null>;
  },
): Promise<Resultado<{ cambios: number }>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/correccion/${entregaId}/reparto/aplicar`,
      {
        method: "POST",
        body: JSON.stringify(cuerpo),
      },
    ),
  );
}

// --- Etapa F12: publicacion de notas (SPEC 12 S12.10, S12.14) ---

export interface ResultadoPublicacion {
  ok: boolean;
  status: number;
  datos: { estado: string; error?: string } | null;
  detalle: {
    codigo?: string;
    motivo?: string;
    conflictos?: {
      estudiante: string;
      nota_canvas: number | null;
      calificada_en: string | null;
    }[];
    nota_propia?: string | null;
  } | null;
}

export async function publicarCorreccion(
  cursoId: string,
  entregaId: string,
  sujetoId: string,
  cuerpo: {
    resolucion?: "PUBLICAR_MIA";
    version_revisada?: boolean;
    confirmacion_reclamo?: string;
    reconocimiento_sin_codigo?: boolean;
  },
): Promise<ResultadoPublicacion> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/correccion/${entregaId}/${sujetoId}/publicar`,
    {
      method: "POST",
      body: JSON.stringify(cuerpo),
    },
  );
  let json: unknown = null;
  try {
    json = await respuesta.json();
  } catch {
    json = null;
  }
  if (respuesta.ok)
    return {
      ok: true,
      status: respuesta.status,
      datos: json as { estado: string },
      detalle: null,
    };
  const detalle = (json as { detail?: unknown } | null)?.detail;
  return {
    ok: false,
    status: respuesta.status,
    datos: null,
    detalle:
      typeof detalle === "object" && detalle
        ? (detalle as ResultadoPublicacion["detalle"])
        : { motivo: String(detalle ?? "") },
  };
}

export async function accionPublicacion(
  cursoId: string,
  entregaId: string,
  sujetoId: string,
  accion: "reintentar" | "reabrir" | "adoptar-canvas" | "rubrica-revisada",
  motivo = "",
): Promise<Resultado<{ estado?: string; nota?: string }>> {
  return resultado(
    await apiFetch(
      `/api/cursos/${cursoId}/correccion/${entregaId}/${sujetoId}/${accion}`,
      {
        method: "POST",
        body: JSON.stringify({ motivo }),
      },
    ),
  );
}

export async function comprobarContraCanvas(
  cursoId: string,
  entregaId: string,
): Promise<boolean> {
  const respuesta = await apiFetch(
    `/api/cursos/${cursoId}/correccion/${entregaId}/comprobar`,
    { method: "POST" },
  );
  return respuesta.ok;
}
