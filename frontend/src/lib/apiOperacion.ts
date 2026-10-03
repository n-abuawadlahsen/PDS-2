import { apiFetch } from "./api";
import { errorRespuesta } from "./errores";

/** Reutiliza sesión y CSRF; las lecturas fallidas nunca se convierten en datos vacíos. */
export async function consultarOperacion<T>(
  ruta: string,
  opciones: RequestInit = {},
): Promise<T> {
  const respuesta = await apiFetch(ruta, opciones);
  if (!respuesta.ok) throw await errorRespuesta(respuesta);
  return respuesta.json() as Promise<T>;
}

export function parametrosOperacion(
  valores: Record<string, string | number | boolean | undefined>,
) {
  const parametros = new URLSearchParams();
  for (const [clave, valor] of Object.entries(valores)) {
    if (valor !== undefined && valor !== "" && valor !== false)
      parametros.set(clave, String(valor));
  }
  return parametros;
}
