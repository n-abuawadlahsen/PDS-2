import type { PantallaCorreccion } from "../lib/api";

/** Espacio del diálogo de publicación (S12.10); llega con la Etapa F12. */
export function PanelPublicacion(_props: {
  cursoId: string;
  entregaId: string;
  sujetoId: string;
  datos: PantallaCorreccion;
  onCambio: () => void;
}) {
  return null;
}
