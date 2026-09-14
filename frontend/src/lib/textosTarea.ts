/**
 * Traduccion de los estados de tarea, entrega y repositorio base (A-155):
 * nunca aparece en pantalla un identificador en mayusculas.
 */
const ESTADO_TAREA: Record<string, string> = {
  BORRADOR: "Borrador",
  ACTIVA: "Activa",
  INCONSISTENTE: "Inconsistente con Canvas",
  CERRADA: "Cerrada",
  ARCHIVADA: "Archivada",
};

const MODALIDAD: Record<string, string> = {
  INDIVIDUAL: "Individual",
  GRUPAL: "Grupal",
};

const TIPO_ENTREGA: Record<string, string> = {
  PARCIAL: "Parcial",
  FINAL: "Final",
};

const ESTADO_ENTREGA: Record<string, string> = {
  VIGENTE: "Vigente",
  VINCULADA_TRAS_EL_CIERRE: "Vinculada después del cierre",
  ELIMINADA_EN_CANVAS: "Eliminada en Canvas",
  EXCLUIDA: "Excluida",
};

const ESTADO_BASE: Record<string, string> = {
  CREANDO: "Creándose",
  CREADO_VACIO: "Creado, sin contenido",
  LISTO: "Listo",
  ERROR: "Con error",
  INACCESIBLE: "Inaccesible en GitHub",
};

/** Maquina 2 (SPEC 08 S8.6.1). `DEGRADADO` no es un error: «Listo, falta gente por entrar». */
const ESTADO_REPOSITORIO: Record<string, string> = {
  ESPERANDO_INFORMACION: "Esperando información",
  LISTO_PARA_CREAR: "Listo para crear",
  CREANDO: "Creándose",
  CREADO_SIN_CONTENIDO: "Creado, copiando contenido",
  CONTENIDO_LISTO: "Contenido listo",
  CONFIGURANDO_ACCESOS: "Configurando accesos",
  OPERATIVO: "Operativo",
  DEGRADADO: "Listo, falta gente por entrar",
  BLOQUEADO: "Bloqueado",
  ESPERANDO_LIMITE: "Esperando a GitHub por límite de uso",
  ERROR_TRANSITORIO: "Reintentando",
  ERROR_PERMANENTE: "Requiere tu acción",
  FUERA_DE_ALCANCE: "Fuera de alcance",
  INACCESIBLE: "No accesible en GitHub",
  ARCHIVADO: "Archivado",
};

const MOTIVO_REPOSITORIO: Record<string, string> = {
  SIN_MAPEO_GITHUB: "El estudiante todavía no tiene cuenta de GitHub registrada",
  MAPEO_EN_CONFLICTO: "La cuenta de GitHub del estudiante está en conflicto",
  SIN_GRUPO_ASIGNADO: "Sin grupo asignado",
  GRUPO_SIN_INTEGRANTES_ACEPTADOS: "El grupo no tiene integrantes aceptados",
  ESTUDIANTE_EN_DOS_GRUPOS: "El estudiante está en dos grupos",
  TAREA_INCONSISTENTE: "La tarea cambió de modalidad en Canvas",
  CURSO_EN_SOLO_LECTURA: "El curso está en modo de solo lectura",
  FALTA_ACEPTAR_INVITACION_GITHUB: "Falta que el estudiante acepte la invitación de GitHub",
  INVITACION_EXPIRADA: "La invitación de GitHub expiró",
  INTEGRANTE_SIN_MAPEO: "Falta la cuenta de GitHub del estudiante",
  INTEGRANTE_PENDIENTE_EN_CANVAS: "Hay integrantes pendientes en Canvas",
  SIN_ACCESO_DOCENTE: "El equipo docente todavía no tiene lectura",
  ERROR_AL_CONCEDER_ACCESO: "GitHub rechazó conceder el acceso",
  BORRADO_EN_GITHUB: "Se borró en GitHub",
  TRANSFERIDO_FUERA_DE_LA_ORG: "Se transfirió fuera de la organización",
  FUERA_DEL_ALCANCE_DE_LA_INSTALACION: "Quedó fuera del alcance de la App",
  APP_SIN_ACCESO: "La App perdió el acceso",
};

/** Maquina 3 (S8.8.2). `DESAPARECIDA` se dice «rechazada o caducada» (A-100). */
const ESTADO_ACCESO: Record<string, string> = {
  SIN_MAPEO: "Sin cuenta de GitHub",
  POR_INVITAR: "Por invitar",
  INVITADO: "Invitado, sin aceptar",
  ACCESO_DIRECTO: "Con acceso",
  ACEPTADO: "Aceptó la invitación",
  EXPIRADA: "Invitación expirada",
  DESAPARECIDA: "Invitación rechazada o caducada",
  REVOCACION_PROPUESTA: "Acceso por revisar",
  REVOCACION_PROGRAMADA: "Revocación programada",
  REVOCADO: "Acceso revocado",
};

const ESTADO_ACCESO_DOCENTE: Record<string, string> = {
  PENDIENTE: "Pendiente",
  CONCEDIDO: "Concedido",
  REVOCADO: "Revocado",
  ERROR: "Con error",
};

function traducir(tabla: Record<string, string>, valor: string | null | undefined): string {
  if (!valor) return "—";
  return tabla[valor] ?? valor.toLowerCase().replaceAll("_", " ");
}

export const textoEstadoTarea = (v: string | null | undefined) => traducir(ESTADO_TAREA, v);
export const textoModalidad = (v: string | null | undefined) => traducir(MODALIDAD, v);
export const textoTipoEntrega = (v: string | null | undefined) => traducir(TIPO_ENTREGA, v);
export const textoEstadoEntrega = (v: string | null | undefined) => traducir(ESTADO_ENTREGA, v);
export const textoEstadoBase = (v: string | null | undefined) => traducir(ESTADO_BASE, v);
export const textoEstadoRepositorio = (v: string | null | undefined) => traducir(ESTADO_REPOSITORIO, v);
export const textoMotivoRepositorio = (v: string | null | undefined) => traducir(MOTIVO_REPOSITORIO, v);
export const textoEstadoAcceso = (v: string | null | undefined) => traducir(ESTADO_ACCESO, v);
export const textoAccesoDocente = (v: string | null | undefined) => traducir(ESTADO_ACCESO_DOCENTE, v);

/** Color por familia (S8.6.4): el limite de GitHub y `DEGRADADO` van en ambar, nunca en rojo. */
export function colorEstadoRepositorio(estado: string): string {
  if (estado === "OPERATIVO") return "#1a7f37";
  if (["DEGRADADO", "ESPERANDO_LIMITE", "ESPERANDO_INFORMACION", "ERROR_TRANSITORIO"].includes(estado)) {
    return "#9a6700";
  }
  if (["BLOQUEADO", "ERROR_PERMANENTE", "INACCESIBLE"].includes(estado)) return "#cf222e";
  return "#57606a";
}

export function fechaLegible(iso: string | null | undefined): string {
  if (!iso) return "sin fecha";
  return new Date(iso).toLocaleString("es-CL", { dateStyle: "medium", timeStyle: "short" });
}

export function tamanoLegible(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
