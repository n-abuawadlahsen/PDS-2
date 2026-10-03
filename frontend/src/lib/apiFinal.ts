import { apiFetch, type PropuestaReparto } from "./api";
import { errorRespuesta } from "./errores";

/** Amplía contratos existentes sin duplicar cookies, CSRF ni el transporte. */
export async function consultarFinal<T>(
  ruta: string,
  opciones: RequestInit = {},
): Promise<T> {
  const respuesta = await apiFetch(ruta, opciones);
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json() as Promise<T>;
}
export interface RepartoEntrada {
  criterio: string;
  reasignar: boolean;
  incluir_no_calificables: boolean;
  manual: Record<string, string | null>;
  por_seccion: Record<string, string>;
}
export function repartoCompleto(
  cursoId: string,
  entregaId: string,
  accion: "previsualizar",
  cuerpo: RepartoEntrada,
): Promise<PropuestaReparto>;
export function repartoCompleto(
  cursoId: string,
  entregaId: string,
  accion: "aplicar",
  cuerpo: RepartoEntrada,
): Promise<{ cambios: number }>;
export function repartoCompleto(
  cursoId: string,
  entregaId: string,
  accion: string,
  cuerpo: RepartoEntrada,
) {
  return consultarFinal(
    `/api/cursos/${cursoId}/correccion/${entregaId}/reparto/${accion}`,
    {
      method: "POST",
      body: JSON.stringify(cuerpo),
    },
  );
}
export function prepararSinEntrega(
  cursoId: string,
  entregaId: string,
  cuerpo: {
    sujeto_ids: string[];
    nota: string;
    comentario: string;
    confirmacion: string;
  },
) {
  return consultarFinal<{ preparadas: number }>(
    `/api/cursos/${cursoId}/correccion/${entregaId}/sin-entrega`,
    {
      method: "POST",
      body: JSON.stringify(cuerpo),
    },
  );
}
export function fechaFinal(iso: string | null, zona: string): string {
  if (!iso) return "Sin información";
  const instante = new Date(iso);
  if (Number.isNaN(instante.getTime())) return iso;
  const partes = new Intl.DateTimeFormat("es-CL", {
    timeZone: zona,
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(instante);
  const obtener = (tipo: string) =>
    partes.find((parte) => parte.type === tipo)?.value ?? "";
  return `${obtener("day")}-${obtener("month")}-${obtener("year")} ${obtener("hour")}:${obtener("minute")} (${zona})`;
}
