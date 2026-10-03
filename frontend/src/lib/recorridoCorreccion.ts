export interface RecorridoCorreccion {
  entregaId: string;
  sujetos: string[];
  pendientes: string[];
  filtrado: boolean;
}
export interface ContextoCorreccion {
  recorrido?: RecorridoCorreccion;
  volver?: string;
}
