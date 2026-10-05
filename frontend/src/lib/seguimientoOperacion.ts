import { consultarOperacion } from "./apiOperacion";

export interface TrabajoOperacion {
  id: string;
  tipo: string;
  estado: string;
  intentos: number;
  max_intentos: number;
  creado_en: string;
  terminado_en: string | null;
  proximo_intento_en: string | null;
  requiere_atencion: boolean;
}
export interface SincronizacionOperacion {
  ok: boolean;
  en_curso: boolean;
  trabajos: TrabajoOperacion[];
  disponible_en: string;
}
export const solicitarSincronizacion = (cursoId: string) =>
  consultarOperacion<SincronizacionOperacion>(`/api/cursos/${cursoId}/sincronizaciones`, { method: "POST" });
export const obtenerTrabajo = (cursoId: string, id: string, signal?: AbortSignal) =>
  consultarOperacion<TrabajoOperacion>(`/api/cursos/${cursoId}/trabajos/${id}`, { signal });
export const obtenerTrabajoChecklist = (cursoId: string, ejecucionId: string, signal?: AbortSignal) =>
  consultarOperacion<TrabajoOperacion>(`/api/cursos/${cursoId}/verificacion/${ejecucionId}/trabajo`, { signal });
export interface MapeoHistorico {
  id: string;
  estado: string;
  origen: string | null;
  confianza: string | null;
  login_declarado: string | null;
  cuenta_login_actual: string | null;
  github_user_id: number | null;
  motivo_invalidacion: string | null;
  creado_en: string;
  vigente_desde: string | null;
  vigente_hasta: string | null;
  creado_por_nombre: string | null;
}
export const obtenerHistorialMapeo = (cursoId: string, estudianteId: string, signal?: AbortSignal) =>
  consultarOperacion<MapeoHistorico[]>(`/api/cursos/${cursoId}/personas/${estudianteId}/mapeo/historial`, { signal });
export const trabajoDetenido = (t: TrabajoOperacion) => t.estado === "OK" || t.requiere_atencion;
