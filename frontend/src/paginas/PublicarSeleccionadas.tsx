import type { MatrizCorreccion } from "../lib/api";

/** Espacio para «Publicar seleccionadas» (S12.10.6); la publicación llega
 * con la Etapa F12. */
export function PublicarSeleccionadas(_props: {
  cursoId: string;
  tareaId: string;
  matriz: MatrizCorreccion;
  onFin: () => void;
}) {
  return null;
}
