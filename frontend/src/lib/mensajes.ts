/**
 * Archivo unico de mensajes de rechazo de acceso (SPEC 02 S2.2.7, A-154).
 * Ocho motivos, catalogo cerrado. El texto no interpola el correo completo
 * (simplificacion de Etapa P1, ver app/api/rutas/auth.py del backend): dice
 * "esa cuenta de Google" en vez de mostrar la direccion.
 */
export interface DescripcionMotivo {
  titulo: string;
  texto: string;
  accion: string;
}

export const MOTIVOS_RECHAZO: Record<string, DescripcionMotivo> = {
  DOMINIO_NO_GMAIL: {
    titulo: "Dominio de correo no admitido",
    texto: "Usa una cuenta Google con correo @miuandes.cl o una cuenta personal de gmail.com.",
    accion: "Probar con otra cuenta",
  },
  HD_PRESENTE: {
    titulo: "Cuenta de dominio gestionado",
    texto:
      "Esa cuenta de Google pertenece a un dominio gestionado que no está habilitado. Usa tu cuenta @miuandes.cl o una cuenta personal de gmail.com.",
    accion: "Probar con otra cuenta",
  },
  CORREO_NO_VERIFICADO: {
    titulo: "Correo sin verificar",
    texto:
      "Google indica que ese correo aún no está verificado. Verifícalo en tu cuenta de Google y vuelve a intentarlo.",
    accion: "Reintentar",
  },
  ACCESO_CANCELADO: {
    titulo: "Acceso cancelado",
    texto:
      "No autorizaste el acceso. Sin ese permiso no podemos identificarte.",
    accion: "Reintentar",
  },
  STATE_INVALIDO: {
    titulo: "Intento caducado",
    texto: "Tu intento de acceso caducó. Empieza de nuevo.",
    accion: "Empezar de nuevo",
  },
  CUENTA_CERRADA: {
    titulo: "Cuenta cerrada",
    texto:
      "Esta cuenta fue cerrada por su titular y no puede volver a iniciar sesión.",
    accion: "Contactar al equipo",
  },
  FALLO_PROVEEDOR: {
    titulo: "Google no respondió",
    texto: "Google no respondió. No es un problema de tu cuenta.",
    accion: "Reintentar",
  },
  CONFLICTO_IDENTIDAD: {
    titulo: "No pudimos completar el acceso",
    texto:
      "El correo asociado a tu cuenta de Google ya pertenece a otra cuenta de la aplicación. Contacta al equipo del curso.",
    accion: "Contactar al equipo",
  },
};

export function descripcionDeMotivo(
  motivo: string | null,
): DescripcionMotivo | null {
  if (!motivo) return null;
  return MOTIVOS_RECHAZO[motivo] ?? null;
}
