"""Catalogo cerrado de los 31 trabajos (SPEC 14 S14.7.4). Ninguno mas.

Metadata declarativa, no ejecutable: cadencia, alcance, espacio de cerrojo,
clave de idempotencia, reintentos, bandera de alcance y fecha de entrada en
servicio. `HANDLERS_IMPLEMENTADOS` (en registro.py) declara cuales de estos 31
tienen ya una funcion real detras -- el resto simplemente no se siembra en
`trabajo_periodico` todavia, y por disenio no aparecen como "vencidos"
(S14.7.4, nota de lectura 3).

Anadir un trabajo es una decision que se registra en ARQUITECTURA.md (S14.7.4).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DefinicionTrabajo:
    nombre: str
    cadencia: str
    alcance: str
    cerrojo: str
    clave_idempotencia: str
    reintentos: str
    entra_en_servicio: str


CATALOGO: tuple[DefinicionTrabajo, ...] = (
    DefinicionTrabajo("tick_planificador", "30 s", "Global", "Global", "Ventana", "-", "16-sep"),
    DefinicionTrabajo(
        "sonda_credencial_canvas", "15 min", "Curso", "1", "Lectura pura", "3", "16-sep"
    ),
    DefinicionTrabajo(
        "sync_roster", "10 min", "Curso", "1", "Upsert por canvas_enrollment_id", "4", "16-sep"
    ),
    DefinicionTrabajo(
        "sync_grupos",
        "10 min",
        "Curso",
        "1",
        "Upsert por canvas_group_id y (grupo, estudiante)",
        "4",
        "16-sep",
    ),
    DefinicionTrabajo(
        "sync_tareas_y_fechas",
        "5 min; 1 min en las 2h previas a un cierre",
        "Curso",
        "1",
        "Comparacion de huella_fechas",
        "4",
        "16-sep",
    ),
    DefinicionTrabajo(
        "recolector_mapeos",
        "3 min con tarea de registro abierta; 15 min si no; volcado completo cada hora",
        "Curso",
        "1",
        "(canvas_assignment_id, canvas_user_id, submitted_at)",
        "4",
        "16-sep",
    ),
    DefinicionTrabajo(
        "materializar_sujetos",
        "Tras cada sync_* y barrido cada 5 min",
        "Curso",
        "1",
        "(tarea, conjunto_hash)",
        "3",
        "16-sep",
    ),
    DefinicionTrabajo(
        "ejecutar_checklist_vinculacion",
        "Bajo demanda, sin cadencia",
        "Curso",
        "1 y 2, por tramos y nunca a la vez",
        "(curso_id, ejecucion_id)",
        "1",
        "16-sep",
    ),
    DefinicionTrabajo(
        "revalidar_mapeos", "Diario 04:00", "Curso", "2", "github_user_id", "2", "16-sep"
    ),
    DefinicionTrabajo(
        "aprovisionar_repositorios",
        "Evento de dominio y barrido cada 2 min",
        "Curso",
        "2",
        "repo:<tarea>:<sujeto>",
        "8 en ~2h",
        "16-sep",
    ),
    DefinicionTrabajo(
        "reconciliar_accesos",
        "1 min pendientes; 15 min resto; bajo demanda",
        "Curso",
        "2",
        "(repositorio, estudiante)",
        "4",
        "16-sep",
    ),
    DefinicionTrabajo(
        "sincronizar_acceso_docente",
        "Al cambiar el equipo del curso y barrido cada 1h",
        "Curso",
        "2",
        "(repositorio, membresia)",
        "4",
        "16-sep",
    ),
    DefinicionTrabajo(
        "revocar_acceso_docente",
        "Al retirar una membresia",
        "Curso",
        "2",
        "(membresia, repositorio)",
        "4",
        "16-sep",
    ),
    DefinicionTrabajo(
        "revocar_acceso_estudiante",
        "Al aprobarse la revocacion",
        "Repositorio",
        "2",
        "revocacion:<acceso_repositorio_id>",
        "4",
        "16-sep",
    ),
    DefinicionTrabajo(
        "procesar_webhooks",
        "Continuo",
        "Global",
        "Por repositorio_id",
        "delivery_id",
        "5",
        "16-sep, con procesamiento acotado",
    ),
    DefinicionTrabajo(
        "verificar_instalacion_github", "1 h", "Curso", "2", "installation_id", "2", "16-sep"
    ),
    DefinicionTrabajo(
        "despachar_outbox",
        "30 s",
        "Global",
        "1 en su parte de Canvas",
        "mensaje_saliente.clave_idempotencia",
        "6, luego REQUIERE_ATENCION",
        "16-sep",
    ),
    DefinicionTrabajo(
        "limpieza_verificacion",
        "Diaria",
        "Curso",
        "1",
        "Prefijo de la prueba de escritura",
        "1",
        "16-sep",
    ),
    DefinicionTrabajo(
        "respaldo_base_datos", "Diario 05:00", "Global", "Global", "Fecha", "2", "16-sep"
    ),
    DefinicionTrabajo(
        "purga_retencion", "Diario 03:00", "Global", "Global", "Fecha", "1", "16-sep"
    ),
    DefinicionTrabajo("vigilancia", "5 min", "Global", "Global", "-", "-", "16-sep"),
    DefinicionTrabajo(
        "resolver_sha",
        "1 min",
        "Global",
        "2",
        "version:<entrega>:<sujeto>:<corte_epoch>",
        "8 en ~2h",
        "Bloque 1, 23-sep",
    ),
    DefinicionTrabajo(
        "crear_etiqueta",
        "Encolado por resolver_sha",
        "Sujeto",
        "2",
        "tag:<entrega>:<sujeto>:<intento>",
        "8 en ~2h",
        "Bloque 1, 23-sep",
    ),
    DefinicionTrabajo(
        "precierre_actividad",
        "Repartido en los 15 min previos a cada fecha efectiva",
        "Repositorio",
        "2",
        "(repositorio, corte_epoch)",
        "2",
        "Bloque 1, 23-sep",
    ),
    DefinicionTrabajo(
        "reconciliar_actividad",
        "15 min",
        "Repositorio activo",
        "2",
        "Upsert (repositorio, sha); ETag",
        "4",
        "Bloque 2, 30-sep",
    ),
    DefinicionTrabajo(
        "barrido_completo_actividad",
        "Diario 03:30",
        "Repositorio",
        "2",
        "Cursor ultimo_head_sha",
        "2",
        "Bloque 2, 30-sep",
    ),
    DefinicionTrabajo(
        "agregar_metricas",
        "10 min sobre 2 dias y pasada nocturna completa",
        "Curso",
        "2",
        "Recomputa, no incrementa",
        "2",
        "Bloque 2, 30-sep",
    ),
    DefinicionTrabajo(
        "comunicaciones_programadas",
        "5 min",
        "Tarea",
        "1",
        "(tarea, evento, sujeto, entrega, estudiante)",
        "3",
        "Bloque 3, 3-oct",
    ),
    DefinicionTrabajo(
        "informe_diario",
        "07:00 en la zona horaria del curso",
        "Curso",
        "1",
        "(curso, fecha)",
        "3",
        "Bloque 3, 3-oct",
    ),
    DefinicionTrabajo(
        "reconciliar_notas_canvas",
        "Inmediata al entrar en ventana; 30 min dentro; 1/dia fuera; nunca archivada",
        "Curso",
        "1",
        "(entrega, ventana)",
        "4",
        "Bloque 3, 3-oct",
    ),
    DefinicionTrabajo(
        "archivar_repositorios",
        "Accion del profesor",
        "Tarea",
        "2",
        "(tarea, repositorio)",
        "3",
        "Bloque 2, 30-sep",
    ),
)

assert len(CATALOGO) == 31, "El catalogo de trabajos debe tener exactamente 31 entradas (S14.7.4)"
