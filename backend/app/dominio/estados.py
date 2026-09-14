"""Catalogos cerrados de estado (SPEC 14 S14.7.1, S14.8.1; A-184).

Fuente unica de la que la puerta de contrato "catalogos cerrados generados desde
dominio/estados.py" (S14.9.3) deriva los CHECK de la migracion. Anadir un valor
aqui y en la migracion es una decision que se registra en ARQUITECTURA.md.
"""

from __future__ import annotations

from enum import StrEnum


class EstadoTrabajo(StrEnum):
    """Maquina de estados de `trabajo` (S14.7.1)."""

    PENDIENTE = "PENDIENTE"
    EN_CURSO = "EN_CURSO"
    OK = "OK"
    REINTENTAR = "REINTENTAR"
    BLOQUEADO = "BLOQUEADO"
    ESPERANDO_CREDENCIAL = "ESPERANDO_CREDENCIAL"
    ESPERANDO_LIMITE = "ESPERANDO_LIMITE"
    REQUIERE_ATENCION = "REQUIERE_ATENCION"
    CANCELADO = "CANCELADO"


# Estados que liberan la clave de idempotencia para un nuevo encolado (S14.7.2
# garantia 1: "indice unico parcial ... en los estados no terminales"). El resto
# sigue ocupando el hueco porque el trabajo logico aun no se dio por bueno.
ESTADOS_TERMINALES_TRABAJO: frozenset[EstadoTrabajo] = frozenset(
    {EstadoTrabajo.OK, EstadoTrabajo.CANCELADO}
)


class ResultadoSincronizacion(StrEnum):
    """Resultado de un ciclo de sincronizacion (tabla `sincronizacion`, Etapa 0)."""

    OK = "OK"
    PARCIAL = "PARCIAL"
    TRUNCADA = "TRUNCADA"
    FALLIDA = "FALLIDA"


class FamiliaError(StrEnum):
    """Clasificacion de errores externos en tres familias (S14.7.5, A-116)."""

    TRANSITORIO = "TRANSITORIO"
    BLOQUEANTE = "BLOQUEANTE"
    PERMANENTE = "PERMANENTE"


class EstadoCurso(StrEnum):
    """Maquina de estados de `curso` (Etapa P2, PLAN-IMPLEMENTACION.md)."""

    BORRADOR = "BORRADOR"
    VINCULANDO = "VINCULANDO"
    ACTIVO = "ACTIVO"
    CANVAS_DESVINCULADO = "CANVAS_DESVINCULADO"
    GITHUB_DESVINCULADO = "GITHUB_DESVINCULADO"
    ARCHIVADO = "ARCHIVADO"


class RolMembresia(StrEnum):
    """Solo dos roles (SPEC 02 S2.4.1, A-020). El rol vive en la membresia, no en el usuario."""

    PROFESOR = "PROFESOR"
    AYUDANTE = "AYUDANTE"


class EstadoMembresia(StrEnum):
    """Baja logica, nunca DELETE (SPEC 02 S2.4.2 invariante 5, A-030, A-190)."""

    ACTIVA = "ACTIVA"
    RETIRADA = "RETIRADA"


class EstadoInvitacion(StrEnum):
    """Cuatro valores y ninguno mas (SPEC 02 S2.5.2)."""

    PENDIENTE = "PENDIENTE"
    ACEPTADA = "ACEPTADA"
    REVOCADA = "REVOCADA"
    EXPIRADA = "EXPIRADA"


class EstadoCredencialCanvas(StrEnum):
    """SPEC 04 S4.2.2, SPEC 05 S5.2.2."""

    VALIDA = "VALIDA"
    INVALIDA = "INVALIDA"
    RETIRADA = "RETIRADA"


class ResultadoVerificacion(StrEnum):
    """Los cinco resultados posibles de un item del checklist (SPEC 04 S4.7.4).

    VERIFICADO_A_MANO nunca se escribe automaticamente: solo la firma de un
    profesor en pantalla (S4.7.3) lo produce.
    """

    CORRECTO = "CORRECTO"
    ADVERTENCIA = "ADVERTENCIA"
    BLOQUEANTE = "BLOQUEANTE"
    NO_VERIFICADO = "NO_VERIFICADO"
    VERIFICADO_A_MANO = "VERIFICADO_A_MANO"


class OrigenVerificacion(StrEnum):
    """SPEC 04 S4.2.2: CHECKLIST (item no nulo, capacidad nula) o RUNTIME (al reves)."""

    CHECKLIST = "CHECKLIST"
    RUNTIME = "RUNTIME"


class CarrilVerificacion(StrEnum):
    """Los dos carriles del checklist (SPEC 04 S4.7.1): Canvas en serie, GitHub en paralelo."""

    CANVAS = "CANVAS"
    GITHUB = "GITHUB"


class ViaEfectivaEquipoGithub(StrEnum):
    """SPEC 04 S4.2.2, SPEC 06 S6.10.3: vía principal (equipo) o de respaldo (colaborador)."""

    TEAM = "TEAM"
    COLABORADOR = "COLABORADOR"


class EstadoEquipoGithub(StrEnum):
    """No fijado por el SPEC con un catalogo explicito; ACTIVO/ERROR es la
    decision minima razonable para representar "se creo y se pobló" frente a
    "algo fallo y necesita reintento", documentada aqui por si diverge."""

    ACTIVO = "ACTIVO"
    ERROR = "ERROR"


class ViaAnuncioSeccion(StrEnum):
    """SPEC 04 S4.2.1, S4.7.2 (prueba de escritura 5-bis)."""

    SECCION = "SECCION"
    CURSO = "CURSO"
    NINGUNA = "NINGUNA"
    NO_VERIFICADO = "NO_VERIFICADO"


class CanalComunicacionActivo(StrEnum):
    """SPEC 04 S4.2.1: canal vigente para R2.3.12 y R2.6.5."""

    CONVERSACION = "CONVERSACION"
    COMENTARIO_ENTREGA = "COMENTARIO_ENTREGA"
    BLOQUEADO = "BLOQUEADO"


class EstadoOrgGithubMembresia(StrEnum):
    """SPEC 02 S2.8.3 (membresia_curso.org_github_estado)."""

    NO_APLICA = "NO_APLICA"
    SIN_CONSENTIMIENTO = "SIN_CONSENTIMIENTO"
    PENDIENTE = "PENDIENTE"
    ACTIVA = "ACTIVA"
    ERROR = "ERROR"


class EstadoSeccion(StrEnum):
    """SPEC 07 S7.2.1. Nunca se borra una fila; se marca ELIMINADA (A-030)."""

    ACTIVA = "ACTIVA"
    ELIMINADA = "ELIMINADA"


class EstadoEstudiante(StrEnum):
    """SPEC 07 S7.2.1: derivado del conjunto de matriculas (A-044), nunca
    escrito directamente desde una llamada a Canvas."""

    ACTIVO = "ACTIVO"
    INVITADO = "INVITADO"
    INACTIVO = "INACTIVO"
    CONCLUIDO = "CONCLUIDO"
    RETIRADO = "RETIRADO"


class EstadoGrupo(StrEnum):
    """SPEC 07 S7.2.1, S7.3.3."""

    ACTIVO = "ACTIVO"
    ELIMINADO = "ELIMINADO"


class WorkflowStatePertenenciaGrupo(StrEnum):
    """SPEC 07 S7.2.1: valores tal como Canvas los devuelve, en minuscula
    deliberadamente (no se traducen a mayusculas como los estados propios)."""

    ACCEPTED = "accepted"
    INVITED = "invited"
    REQUESTED = "requested"


class TipoCuentaGithub(StrEnum):
    """SPEC 07 S7.2.2."""

    USER = "USER"
    ORGANIZATION = "ORGANIZATION"
    BOT = "BOT"


class EstadoCuentaGithub(StrEnum):
    """SPEC 07 S7.2.2: catalogo global (`cuenta_github`), no confundir con
    `mapeo_github.estado` (por curso)."""

    VALIDA = "VALIDA"
    RENOMBRADA = "RENOMBRADA"
    NO_EXISTE = "NO_EXISTE"
    ES_ORGANIZACION = "ES_ORGANIZACION"


class OrigenMapeoGithub(StrEnum):
    """SPEC 07 S7.4.5: tres valores, no cuatro -- la via 4 (reintento
    asistido) alimenta la via 1, no es una fuente distinta."""

    AUTOSERVICIO_CANVAS = "AUTOSERVICIO_CANVAS"
    CARGA_DOCENTE = "CARGA_DOCENTE"
    IMPORTACION_CSV = "IMPORTACION_CSV"


class EstadoMapeoGithub(StrEnum):
    """SPEC 07 S7.6.1: nueve estados, `SUPERSEDIDO` el unico terminal."""

    SIN_DATO = "SIN_DATO"
    RECIBIDO = "RECIBIDO"
    NO_RESUELTO = "NO_RESUELTO"
    NO_EXISTE = "NO_EXISTE"
    ES_ORGANIZACION = "ES_ORGANIZACION"
    EN_CONFLICTO = "EN_CONFLICTO"
    VIGENTE = "VIGENTE"
    INVALIDADO = "INVALIDADO"
    SUPERSEDIDO = "SUPERSEDIDO"


ESTADOS_MAPEO_GITHUB_TERMINALES: frozenset[EstadoMapeoGithub] = frozenset(
    {EstadoMapeoGithub.SUPERSEDIDO}
)


class MotivoInvalidacionMapeo(StrEnum):
    """SPEC 07 S7.6.2: cinco motivos, no tres."""

    RENOMBRADO = "RENOMBRADO"
    CUENTA_ELIMINADA = "CUENTA_ELIMINADA"
    LOGIN_REASIGNADO = "LOGIN_REASIGNADO"
    ESTUDIANTE_RETIRADO = "ESTUDIANTE_RETIRADO"
    CUENTA_NO_ELEGIBLE = "CUENTA_NO_ELEGIBLE"


class EstadoTareaRegistro(StrEnum):
    """SPEC 07 S7.2.3 (`curso.registro_estado`)."""

    NO_CREADA = "NO_CREADA"
    ACTIVA = "ACTIVA"
    ALTERADA = "ALTERADA"
    DESAPARECIDA = "DESAPARECIDA"


class ModalidadTarea(StrEnum):
    """SPEC 08 S8.2.2 (A-080): vive en `tarea`, nunca en `entrega` -- es lo que
    hace estructuralmente imposible dos entregas con configuraciones distintas
    (R2.3.3)."""

    INDIVIDUAL = "INDIVIDUAL"
    GRUPAL = "GRUPAL"


class EstadoTarea(StrEnum):
    """SPEC 08 S8.2.4 (A-080)."""

    BORRADOR = "BORRADOR"
    ACTIVA = "ACTIVA"
    INCONSISTENTE = "INCONSISTENTE"
    CERRADA = "CERRADA"
    ARCHIVADA = "ARCHIVADA"


class TipoEntrega(StrEnum):
    """SPEC 08 S8.2.1 (A-080): `FINAL` es siempre la de mayor `orden`."""

    PARCIAL = "PARCIAL"
    FINAL = "FINAL"


class EstadoValidacionEntrega(StrEnum):
    """A-203: escalar cerrado de cuatro valores. `DESPUBLICADA` y `ADVERTENCIA`
    no son valores de esta columna (viven en `publicada` y `advertencias`)."""

    VIGENTE = "VIGENTE"
    VINCULADA_TRAS_EL_CIERRE = "VINCULADA_TRAS_EL_CIERRE"
    ELIMINADA_EN_CANVAS = "ELIMINADA_EN_CANVAS"
    EXCLUIDA = "EXCLUIDA"


class AdvertenciaEntrega(StrEnum):
    """A-203 punto 3: catalogo cerrado de cuatro valores de `entrega.advertencias`."""

    LOCK_ANTES_DE_DUE = "LOCK_ANTES_DE_DUE"
    UNLOCK_DESPUES_DE_DUE = "UNLOCK_DESPUES_DE_DUE"
    FINAL_ANTES_QUE_PARCIAL = "FINAL_ANTES_QUE_PARCIAL"
    DOS_ENTREGAS_MISMA_FECHA = "DOS_ENTREGAS_MISMA_FECHA"


class OrigenVisibilidadEntrega(StrEnum):
    """A-164 paso 1: de donde sale `visibilidad_entrega.visible`."""

    TODOS = "TODOS"
    ASSIGNMENT_VISIBILITY = "ASSIGNMENT_VISIBILITY"
    OVERRIDE = "OVERRIDE"
    SUPUESTO = "SUPUESTO"


class EstadoRepositorioBase(StrEnum):
    """A-208: cinco valores, `DEFAULT 'CREANDO'`. No existe "no solicitado":
    una tarea sin base simplemente no tiene fila."""

    CREANDO = "CREANDO"
    CREADO_VACIO = "CREADO_VACIO"
    LISTO = "LISTO"
    ERROR = "ERROR"
    INACCESIBLE = "INACCESIBLE"


class TipoSujeto(StrEnum):
    """A-081: derivado de `tarea.modalidad`."""

    ESTUDIANTE = "ESTUDIANTE"
    GRUPO = "GRUPO"


class MotivoDesactivacionSujeto(StrEnum):
    """A-164 paso 3: un sujeto nunca se borra, se desactiva con motivo."""

    SIN_MATRICULA_ACTIVA = "SIN_MATRICULA_ACTIVA"
    SIN_VISIBILIDAD = "SIN_VISIBILIDAD"
    GRUPO_DISUELTO = "GRUPO_DISUELTO"
    GRUPO_SIN_ACEPTADOS = "GRUPO_SIN_ACEPTADOS"


class EstadoRepositorio(StrEnum):
    """Maquina 2 (S8.6.1, A-092 corregida por A-211): quince estados."""

    ESPERANDO_INFORMACION = "ESPERANDO_INFORMACION"
    LISTO_PARA_CREAR = "LISTO_PARA_CREAR"
    CREANDO = "CREANDO"
    CREADO_SIN_CONTENIDO = "CREADO_SIN_CONTENIDO"
    CONTENIDO_LISTO = "CONTENIDO_LISTO"
    CONFIGURANDO_ACCESOS = "CONFIGURANDO_ACCESOS"
    OPERATIVO = "OPERATIVO"
    DEGRADADO = "DEGRADADO"
    BLOQUEADO = "BLOQUEADO"
    ESPERANDO_LIMITE = "ESPERANDO_LIMITE"
    ERROR_TRANSITORIO = "ERROR_TRANSITORIO"
    ERROR_PERMANENTE = "ERROR_PERMANENTE"
    FUERA_DE_ALCANCE = "FUERA_DE_ALCANCE"
    INACCESIBLE = "INACCESIBLE"
    ARCHIVADO = "ARCHIVADO"


class MotivoEsperandoInformacion(StrEnum):
    """S8.5.2 (A-094 corregida por A-211/A-225): siete motivos cerrados."""

    SIN_MAPEO_GITHUB = "SIN_MAPEO_GITHUB"
    MAPEO_EN_CONFLICTO = "MAPEO_EN_CONFLICTO"
    SIN_GRUPO_ASIGNADO = "SIN_GRUPO_ASIGNADO"
    GRUPO_SIN_INTEGRANTES_ACEPTADOS = "GRUPO_SIN_INTEGRANTES_ACEPTADOS"
    ESTUDIANTE_EN_DOS_GRUPOS = "ESTUDIANTE_EN_DOS_GRUPOS"
    TAREA_INCONSISTENTE = "TAREA_INCONSISTENTE"
    CURSO_EN_SOLO_LECTURA = "CURSO_EN_SOLO_LECTURA"


class MotivoDegradado(StrEnum):
    """S8.6.2 (A-092): seis motivos cerrados. `DEGRADADO` no es un error."""

    FALTA_ACEPTAR_INVITACION_GITHUB = "FALTA_ACEPTAR_INVITACION_GITHUB"
    INVITACION_EXPIRADA = "INVITACION_EXPIRADA"
    INTEGRANTE_SIN_MAPEO = "INTEGRANTE_SIN_MAPEO"
    INTEGRANTE_PENDIENTE_EN_CANVAS = "INTEGRANTE_PENDIENTE_EN_CANVAS"
    SIN_ACCESO_DOCENTE = "SIN_ACCESO_DOCENTE"
    ERROR_AL_CONCEDER_ACCESO = "ERROR_AL_CONCEDER_ACCESO"


class MotivoInaccesible(StrEnum):
    """S8.11.1 (A-211): cuatro motivos cerrados."""

    BORRADO_EN_GITHUB = "BORRADO_EN_GITHUB"
    TRANSFERIDO_FUERA_DE_LA_ORG = "TRANSFERIDO_FUERA_DE_LA_ORG"
    FUERA_DEL_ALCANCE_DE_LA_INSTALACION = "FUERA_DEL_ALCANCE_DE_LA_INSTALACION"
    APP_SIN_ACCESO = "APP_SIN_ACCESO"


class SubtipoErrorPermanente(StrEnum):
    """A-098: siete subtipos de `ERROR_PERMANENTE`."""

    ORG_PROHIBE_CREAR_REPOS = "ORG_PROHIBE_CREAR_REPOS"
    ORG_EXIGE_2FA = "ORG_EXIGE_2FA"
    CUENTA_BLOQUEADA_POR_ORG = "CUENTA_BLOQUEADA_POR_ORG"
    CUENTA_ELIMINADA = "CUENTA_ELIMINADA"
    LOGIN_ES_ORGANIZACION = "LOGIN_ES_ORGANIZACION"
    NOMBRE_OCUPADO_POR_TERCERO = "NOMBRE_OCUPADO_POR_TERCERO"
    PERMISO_INSUFICIENTE = "PERMISO_INSUFICIENTE"


class EstadoAccesoRepositorio(StrEnum):
    """Maquina 3 (S8.8.2, A-212): diez valores, ninguno terminal."""

    SIN_MAPEO = "SIN_MAPEO"
    POR_INVITAR = "POR_INVITAR"
    INVITADO = "INVITADO"
    ACCESO_DIRECTO = "ACCESO_DIRECTO"
    ACEPTADO = "ACEPTADO"
    EXPIRADA = "EXPIRADA"
    DESAPARECIDA = "DESAPARECIDA"
    REVOCACION_PROPUESTA = "REVOCACION_PROPUESTA"
    REVOCACION_PROGRAMADA = "REVOCACION_PROGRAMADA"
    REVOCADO = "REVOCADO"


class EstadoAccesoDocente(StrEnum):
    """A-163: `acceso_docente_repositorio.estado`."""

    PENDIENTE = "PENDIENTE"
    CONCEDIDO = "CONCEDIDO"
    REVOCADO = "REVOCADO"
    ERROR = "ERROR"


class ViaAccesoDocente(StrEnum):
    """A-163: via principal (equipo) o de respaldo (colaborador individual)."""

    TEAM = "TEAM"
    COLABORADOR = "COLABORADOR"


class AlcanceReglaFecha(StrEnum):
    """A-080 `regla_fecha.alcance`: la fila `BASE` y los tres alcances de override."""

    BASE = "BASE"
    SECCION = "SECCION"
    GRUPO = "GRUPO"
    ESTUDIANTES = "ESTUDIANTES"


class OrigenFechaEfectiva(StrEnum):
    """S9.3.2 (A-055): nivel de la cadena de precedencia que produjo la fecha."""

    BASE = "BASE"
    SECCION = "SECCION"
    GRUPO = "GRUPO"
    ADHOC = "ADHOC"


class EstadoFechaEfectiva(StrEnum):
    """S9.4.1: el recalculo nunca actualiza en sitio (Ley 2)."""

    VIGENTE = "VIGENTE"
    SUPERSEDIDA = "SUPERSEDIDA"


class CanalMensaje(StrEnum):
    """S11.2.1 (A-125): un solo outbox para los cuatro canales."""

    CANVAS_CONVERSACION = "CANVAS_CONVERSACION"
    CANVAS_ANUNCIO = "CANVAS_ANUNCIO"
    CANVAS_COMENTARIO = "CANVAS_COMENTARIO"
    CORREO = "CORREO"


class EstadoMensaje(StrEnum):
    """Maquina 7 (S11.2.2): quince estados, `DEFAULT 'PENDIENTE'`."""

    PROGRAMADO = "PROGRAMADO"
    DIFERIDO = "DIFERIDO"
    PENDIENTE = "PENDIENTE"
    EN_CURSO = "EN_CURSO"
    ENVIADO = "ENVIADO"
    REINTENTAR = "REINTENTAR"
    ESPERANDO_LIMITE = "ESPERANDO_LIMITE"
    ESPERANDO_CREDENCIAL = "ESPERANDO_CREDENCIAL"
    BLOQUEADO = "BLOQUEADO"
    REQUIERE_ATENCION = "REQUIERE_ATENCION"
    FALLIDO = "FALLIDO"
    CANCELADO = "CANCELADO"
    SUPRIMIDO = "SUPRIMIDO"
    CADUCADO = "CADUCADO"
    RETRACTADO = "RETRACTADO"


class OrigenMensaje(StrEnum):
    """S11.2.1."""

    AUTOMATICO = "AUTOMATICO"
    MANUAL = "MANUAL"
    SISTEMA = "SISTEMA"
