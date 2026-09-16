import { descripcionDeMotivo } from "./mensajes";

export class ErrorApi extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export function detalleLegible(value: unknown): string {
  if (typeof value === "string") {
    const motivo = descripcionDeMotivo(value);
    if (motivo) return `${motivo.titulo}. ${motivo.texto}`;
    return /^[A-Z][A-Z_0-9]+$/.test(value)
      ? `No se pudo completar la operación: ${value.toLowerCase().replaceAll("_", " ")}.`
      : value;
  }
  if (Array.isArray(value))
    return value.map(detalleLegible).filter(Boolean).join(". ");
  if (value && typeof value === "object") {
    const r = value as Record<string, unknown>;
    for (const key of ["detail", "detalle", "msg", "mensaje", "motivo"]) {
      if (r[key] !== undefined) return detalleLegible(r[key]);
    }
  }
  return "";
}
export function mensajeError(error: unknown): string {
  if (error instanceof ErrorApi) return error.message;
  if (error instanceof TypeError)
    return "No pudimos conectar con la aplicación. Revisa tu conexión e intenta nuevamente.";
  if (error instanceof Error) return error.message;
  return (
    detalleLegible(error) ||
    "No pudimos completar la operación. Intenta nuevamente."
  );
}
export async function errorRespuesta(response: Response): Promise<ErrorApi> {
  const body: unknown = await response
    .clone()
    .json()
    .catch(() => null);
  const fallback: Record<number, string> = {
    401: "Tu sesión venció. Vuelve a entrar con Google.",
    403: "No tienes permiso para realizar esta acción. Los permisos del curso se actualizarán.",
    404: "No encontramos este recurso o ya no tienes acceso.",
    429: "Se alcanzó el límite de solicitudes. Espera antes de intentar nuevamente.",
  };
  const message = fallback[response.status] ?? detalleLegible(body);
  return new ErrorApi(
    response.status,
    message ||
      `No se pudo completar la operación (${response.status}). Intenta nuevamente.`,
  );
}
export async function comprobar(response: Response): Promise<void> {
  if (!response.ok) throw await errorRespuesta(response);
}
