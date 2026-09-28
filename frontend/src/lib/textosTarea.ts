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
  SIN_MAPEO_GITHUB:
    "El estudiante todavía no tiene cuenta de GitHub registrada",
  MAPEO_EN_CONFLICTO: "La cuenta de GitHub del estudiante está en conflicto",
  SIN_GRUPO_ASIGNADO: "Sin grupo asignado",
  GRUPO_SIN_INTEGRANTES_ACEPTADOS: "El grupo no tiene integrantes aceptados",
  ESTUDIANTE_EN_DOS_GRUPOS: "El estudiante está en dos grupos",
  TAREA_INCONSISTENTE: "La tarea cambió de modalidad en Canvas",
  CURSO_EN_SOLO_LECTURA: "El curso está en modo de solo lectura",
  FALTA_ACEPTAR_INVITACION_GITHUB:
    "Falta que el estudiante acepte la invitación de GitHub",
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

function traducir(
  tabla: Record<string, string>,
  valor: string | null | undefined,
): string {
  if (!valor) return "—";
  return tabla[valor] ?? valor.toLowerCase().replaceAll("_", " ");
}

export const textoEstadoTarea = (v: string | null | undefined) =>
  traducir(ESTADO_TAREA, v);
export const textoModalidad = (v: string | null | undefined) =>
  traducir(MODALIDAD, v);
export const textoTipoEntrega = (v: string | null | undefined) =>
  traducir(TIPO_ENTREGA, v);
export const textoEstadoEntrega = (v: string | null | undefined) =>
  traducir(ESTADO_ENTREGA, v);
export const textoEstadoBase = (v: string | null | undefined) =>
  traducir(ESTADO_BASE, v);
export const textoEstadoRepositorio = (v: string | null | undefined) =>
  traducir(ESTADO_REPOSITORIO, v);
export const textoMotivoRepositorio = (v: string | null | undefined) =>
  traducir(MOTIVO_REPOSITORIO, v);
export const textoEstadoAcceso = (v: string | null | undefined) =>
  traducir(ESTADO_ACCESO, v);
export const textoAccesoDocente = (v: string | null | undefined) =>
  traducir(ESTADO_ACCESO_DOCENTE, v);

/** Color por familia (S8.6.4): el limite de GitHub y `DEGRADADO` van en ambar, nunca en rojo. */
export function colorEstadoRepositorio(estado: string): string {
  if (estado === "OPERATIVO") return "var(--color-success)";
  if (
    [
      "DEGRADADO",
      "ESPERANDO_LIMITE",
      "ESPERANDO_INFORMACION",
      "ERROR_TRANSITORIO",
    ].includes(estado)
  ) {
    return "var(--color-warning)";
  }
  if (["BLOQUEADO", "ERROR_PERMANENTE", "INACCESIBLE"].includes(estado))
    return "var(--color-error)";
  return "var(--color-text-secondary)";
}

export function fechaLegible(
  iso: string | null | undefined,
  zonaHoraria = "America/Santiago",
): string {
  if (!iso) return "sin fecha";
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "Fecha no disponible";
  try {
    return fecha.toLocaleString("es-CL", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: zonaHoraria,
    });
  } catch {
    return `${fecha.toISOString()} (UTC)`;
  }
}

export function tamanoLegible(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// --- Etapa final (F2-F6): textos de entregas, versiones y actividad ---

const ADVERTENCIA_ENTREGA: Record<string, string> = {
  LOCK_ANTES_DE_DUE: "Canvas deja de aceptar entregas antes de la fecha de cierre",
  UNLOCK_DESPUES_DE_DUE: "Canvas la abre después de su fecha de cierre",
  FINAL_ANTES_QUE_PARCIAL: "La entrega final cierra antes que una parcial",
  DOS_ENTREGAS_MISMA_FECHA: "Otra entrega de esta tarea cierra a la misma hora",
};

// S9.6.3: etiqueta fija por estado; nunca «sin entrega» para SIN_REPOSITORIO.
const ESTADO_CAPTURA: Record<string, string> = {
  CAPTURADA: "Versión registrada",
  CAPTURADA_SIN_TAG: "Versión registrada (sin etiqueta en GitHub)",
  SIN_COMMITS: "Sin commits al cierre",
  REVISAR: "Versión registrada, requiere revisión",
  SIN_REPOSITORIO: "Sin repositorio al cierre",
  ERROR: "Requiere tu acción",
  PENDIENTE_DE_CIERRE: "Aún no cierra",
  REGISTRANDO: "Registrando versión",
  SIN_FECHA: "Sin fecha de cierre",
  NO_APLICA: "Esta entrega no aplica a este sujeto",
};

const MOTIVO_VERSION: Record<string, string> = {
  SIN_REPOSITORIO_AL_CIERRE: "Su repositorio no estaba listo en la fecha de cierre",
  SUJETO_MATERIALIZADO_TRAS_EL_CIERRE: "Alta posterior a la fecha",
  FECHA_ADELANTADA: "Reemplazada: la fecha de cierre se adelantó",
  FECHA_EXTENDIDA: "Reemplazada: la fecha de cierre se extendió",
  CAPTURA_TARDIA_POR_ALCANCE:
    "Versión resuelta después del cierre, con el historial recuperado desde GitHub; la fecha de corte es la original",
};

const ESTADO_ETIQUETA: Record<string, string> = {
  PENDIENTE: "Etiqueta pendiente",
  CREADO: "Etiqueta creada",
  CONFLICTO: "La etiqueta apunta a otro commit",
  FALLIDO: "No se pudo crear la etiqueta",
  NO_APLICA: "Sin etiqueta",
};

const ADVERTENCIA_VERSION: Record<string, string> = {
  SIN_CAMBIOS_RESPECTO_A_LA_ANTERIOR: "Sin cambios respecto a la entrega anterior",
  SUJETO_RETIRADO: "El sujeto ya no estaba activo al cierre",
  FECHAS_POSIBLEMENTE_DESACTUALIZADAS: "La fecha llevaba más de 6 horas sin refrescarse desde Canvas",
  CAPTURA_DIFERIDA_POR_GITHUB: "Capturada más tarde porque GitHub no estaba disponible",
  USA_GIT_LFS:
    "Este repositorio usa Git LFS: si descargas el .zip, los archivos grandes llegarán como punteros de texto. Clona el repositorio si necesitas su contenido",
  TIENE_SUBMODULOS: "Este repositorio declara submódulos: su código vive en otros repositorios",
  SHA_PUEDE_SER_INALCANZABLE:
    "El commit ya no es accesible en GitHub; probablemente hubo un push --force. La versión registrada se conserva",
};

const ORIGEN_CAPTURA: Record<string, string> = {
  AUTOMATICA: "automática",
  MANUAL_AHORA: "manual: capturada ahora",
  MANUAL_FECHA: "manual: otra fecha de corte",
  MANUAL_SHA: "manual: commit fijado",
};

// SPEC 10 S10.6.1: el estado agregado de una entrega, nueve valores.
const ESTADO_ENTREGA_AGREGADO: Record<string, string> = {
  EXCLUIDA: "Excluida por el equipo docente",
  ELIMINADA_EN_CANVAS: "Eliminada en Canvas",
  NO_PUBLICADA: "No publicada en Canvas",
  VINCULADA_TRAS_EL_CIERRE: "Versiones no registradas: la fecha ya había pasado al vincular",
  SIN_FECHA: "Sin fecha de cierre",
  ABIERTA: "Abierta",
  EN_CIERRE: "Cerrando",
  CERRADA_CAPTURANDO: "Cerrada, registrando versiones",
  CERRADA_REGISTRADA: "Cerrada, versiones registradas",
};

// SPEC 10 S10.5.3: las tres causas, cada una con su acción.
const CAUSA_PARTICIPACION: Record<string, string> = {
  SIN_ACCESO: "no ha aceptado su invitación: reenvíala o avisa por Canvas",
  SIN_ATRIBUIR: "hay commits sin atribuir: puede haber usado otro correo de Git",
  SIN_COMMITS: "sin commits: contacta al estudiante",
};

export const textoEstadoEntregaAgregado = (v: string | null | undefined) => traducir(ESTADO_ENTREGA_AGREGADO, v);
export const textoCausaParticipacion = (v: string | null | undefined) => traducir(CAUSA_PARTICIPACION, v);
export const textoEstadoCaptura = (v: string | null | undefined) => traducir(ESTADO_CAPTURA, v);
export const textoMotivoVersion = (v: string | null | undefined) => traducir(MOTIVO_VERSION, v);
export const textoEstadoEtiqueta = (v: string | null | undefined) => traducir(ESTADO_ETIQUETA, v);
export const textoAdvertenciaVersion = (v: string | null | undefined) => traducir(ADVERTENCIA_VERSION, v);
export const textoOrigenCaptura = (v: string | null | undefined) => traducir(ORIGEN_CAPTURA, v);
export const textoAdvertenciaEntrega = (v: string | null | undefined) => traducir(ADVERTENCIA_ENTREGA, v);
