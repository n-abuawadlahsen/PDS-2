/** Catalogo de permisos para el formulario (SPEC 02 S2.3.2, S2.3.6). */
export interface DescripcionPermiso {
  clave: string;
  etiqueta: string;
  descripcion: string;
}

export const PERMISOS_IMPLICITOS: DescripcionPermiso[] = [
  { clave: "curso.ver", etiqueta: "Ver el curso", descripcion: "siempre incluido" },
  { clave: "correccion.corregir", etiqueta: "Corregir lo asignado", descripcion: "siempre incluido" },
];

export const PERMISOS_CONCEDIBLES: DescripcionPermiso[] = [
  { clave: "tarea.administrar", etiqueta: "Administrar tareas", descripcion: "Crear y editar tareas, gestionar el repositorio base" },
  { clave: "mapeo.editar", etiqueta: "Editar cuentas de GitHub vinculadas", descripcion: "Corregir la correspondencia estudiante-GitHub" },
  { clave: "correccion.asignar", etiqueta: "Repartir correcciones", descripcion: "Repartir las entregas entre los correctores" },
  { clave: "nota.publicar", etiqueta: "Publicar nota", descripcion: "Escribir calificación, comentario y rúbrica en Canvas" },
  { clave: "comunicacion.enviar", etiqueta: "Enviar comunicaciones", descripcion: "Mensajes y anuncios manuales" },
];

export const PERMISOS_NO_CONCEDIBLES: (DescripcionPermiso & { motivo: string })[] = [
  {
    clave: "curso.administrar",
    etiqueta: "Administrar el curso",
    descripcion: "",
    motivo: "da acceso a la credencial de Canvas del curso",
  },
  {
    clave: "equipo.administrar",
    etiqueta: "Administrar el equipo",
    descripcion: "",
    motivo: "permitiría concederse a sí mismo el resto",
  },
];

// Conjuntos preparados (S2.3.5): azucar de interfaz, nunca se persiste el nombre.
export const CONJUNTO_SOLO_CORREGIR: string[] = [];
export const CONJUNTO_CORREGIR_Y_PUBLICAR: string[] = ["nota.publicar"];
export const CONJUNTO_GESTION_COMPLETA: string[] = PERMISOS_CONCEDIBLES.map((p) => p.clave);

// Valor por defecto del formulario de invitacion para un ayudante (S2.3.4).
export const PERMISOS_AYUDANTE_POR_DEFECTO: string[] = ["mapeo.editar"];
