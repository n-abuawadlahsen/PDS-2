import type { Page } from "@playwright/test";
import type {
  EstadoArchivado,
  FichaVersion,
  ProgresoCaptura,
  Tablero,
  TareaDetalle,
  Timeline,
  VersionEntrega,
} from "../src/lib/api";
import { preparar, repositorios, tarea } from "./fixtures";

const fecha = "2026-10-01T18:00:00Z";
export const tareaOperacion: TareaDetalle = {
  ...tarea,
  nombre: "Proyecto 2 · Plataforma de gestión docente",
  modalidad: "GRUPAL",
  entregas: [
    {
      ...tarea.entregas[0],
      id: "entrega-1",
      tipo: "PARCIAL",
      nombre: "Entrega parcial",
      advertencias: [],
    },
    {
      ...tarea.entregas[0],
      id: "entrega-2",
      canvas_assignment_id: 456,
      orden: 2,
      tipo: "FINAL",
      nombre: "Entrega final",
      due_at_base: "2026-10-06T19:00:00Z",
      advertencias: [],
    },
  ],
  vincular_otra_entrega: { habilitada: true, motivo: null },
};
export const versionOperacion: VersionEntrega = {
  id: "version-1",
  intento: 1,
  vigente: true,
  estado: "CAPTURADA_SIN_TAG",
  motivo: null,
  commit_sha: "a".repeat(40),
  commit_mensaje: "Implementar permisos y navegación",
  rama: "desarrollo",
  fecha_corte: fecha,
  capturada_en: "2026-10-01T18:02:00Z",
  captura_tardia_minutos: null,
  tag_nombre: "entrega-parcial",
  tag_estado: "FALLIDO",
  tag_motivo: null,
  tag_error: "GitHub no respondió; se volverá a intentar",
  advertencias: [],
  verificacion: {},
  origen_captura: "AUTOMATICA",
  motivo_manual: null,
  creada_por: null,
  integrantes: [
    { nombre: "Estudiante de ensayo", github_login: "estudiante-demo" },
  ],
  sujeto_etiqueta: "Grupo 01",
  repositorio_full_name: "organizacion-demo/grupo-01",
  fecha_origen: "BASE",
  canvas_override_id: null,
  comparacion_base: "Versión parcial",
  enlaces: {
    arbol: "/api/cursos/curso-1/versiones/version-1/abrir?destino=arbol",
    comparacion: null,
    zip: null,
  },
};
export const tableroOperacion: Tablero = {
  tarea: {
    id: "tarea-1",
    nombre: tareaOperacion.nombre,
    modalidad: "GRUPAL",
    estado: "ACTIVA",
  },
  procedencia: {
    ultima_ingesta: fecha,
    ultima_reconciliacion: fecha,
    datos_posiblemente_desactualizados: false,
    calculado_en: fecha,
    llamadas_externas: 0,
    render_ms: 3,
  },
  periodos: [
    { clave: "entrega:entrega-1", etiqueta: "Hasta la entrega parcial" },
    { clave: "entrega:entrega-2", etiqueta: "Entre parcial y final" },
    { clave: "30d", etiqueta: "Últimos 30 días" },
    { clave: "todo", etiqueta: "Todo" },
  ],
  periodo: "entrega:entrega-2",
  entregas: tareaOperacion.entregas.map((e) => ({
    entrega_id: e.id,
    orden: e.orden,
    nombre: e.nombre,
    tipo: e.tipo,
    estado: e.tipo === "FINAL" ? "ABIERTA" : "CERRADA_REGISTRADA",
    fechas_distintas: 2,
    sujetos: 200,
    versiones_registradas: e.tipo === "FINAL" ? 0 : 198,
    cierre_desde:
      e.tipo === "FINAL" ? "2026-10-06T19:00:00Z" : "2026-09-20T02:59:00Z",
    cierre_hasta:
      e.tipo === "FINAL" ? "2026-10-08T19:00:00Z" : "2026-09-20T02:59:00Z",
  })),
  repositorios: repositorios.resumen,
  tarjetas: {
    repositorios_creados: 197,
    sin_actividad: 4,
    sin_dato_suficiente: 1,
    sin_datos_todavia: 1,
    sin_participacion: { SIN_ACCESO: 1, SIN_ATRIBUIR: 2 },
    invitaciones_sin_aceptar: 1,
    bloqueantes: 1,
  },
  serie: Array.from({ length: 14 }, (_, i) => ({
    dia: `2026-09-${String(i + 17).padStart(2, "0")}`,
    commits: [2, 5, 8, 4, 0, 0, 6, 9, 13, 5, 17, 24, 22, 31][i],
  })),
  cierres: ["2026-09-21T02:59:00Z"],
  histograma_previo_al_cierre: [],
  progreso_frente_al_cierre: null,
  posicion_frente_al_curso: null,
  filas: Array.from({ length: 200 }, (_, i) => ({
    repositorio_id: `r-${i}`,
    nombre: `icc4201-grupo-${i + 1}`,
    sujeto: `Grupo ${String(i + 1).padStart(2, "0")}`,
    sujeto_tipo: "GRUPO",
    seccion: i % 2 ? "Sección 2" : "Sección 1",
    estado: i === 1 ? "DEGRADADO" : "OPERATIVO",
    grupo_estado: i === 1 ? "FUNCIONANDO_INCOMPLETO" : "LISTOS",
    motivo: i === 1 ? "FALTA_ACEPTAR_INVITACION_GITHUB" : null,
    no_aplica: false,
    actividad: "CON_ACTIVIDAD",
    dias_observados: 30,
    umbral_dias: 7,
    commits_periodo: 5 + i,
    commits_sin_atribuir: i === 1 ? 2 : 0,
    dias_desde_ultimo_commit: i % 5,
    sparkline: [1, 3, 0, 0, 4, 2, 5, 3, 7, 4, 5],
    alertas: i === 1 ? ["SIN_PARTICIPACION"] : [],
    indice_desequilibrio: 20,
    reparto_concentrado: false,
    // Tres integrantes con aportes distintos para que la comparación se vea;
    // en el Grupo 02 (con alerta) uno no tiene commits atribuidos.
    integrantes: [
      { nombre: "Ana Soto", commits: 8 + i, dias_activos: 6 },
      { nombre: "Bruno Díaz", commits: 4, dias_activos: 3 },
      {
        nombre: "Carla Reyes",
        commits: i === 1 ? 0 : 2,
        dias_activos: i === 1 ? 0 : 1,
      },
    ].map((m, j) => ({
      estudiante_id: `e-${i}-${j}`,
      nombre: m.nombre,
      commits: m.commits,
      dias_activos: m.dias_activos,
      adiciones: m.commits * 30,
      eliminaciones: m.commits * 4,
      causa: m.commits === 0 ? "SIN_ATRIBUIR" : null,
      retirado: false,
      en_grupo_desde: fecha,
      salio_del_grupo: null,
    })),
  })),
  total_filas: 200,
  pagina: 1,
  definicion_commit_contable:
    "Se cuentan commits alcanzables; se excluyen merges y el commit inicial de la plantilla. Los commits de bots y docentes cuentan en la actividad del repositorio.",
  aviso_alcance:
    "La participación se mide por commits atribuidos; no incluye issues o revisiones.",
};
export const timelineOperacion: Timeline = {
  repositorio: {
    id: "r-0",
    nombre: "icc4201-2026-2-proyecto-2-grupo-01",
    estado: "OPERATIVO",
    rama_por_defecto: "desarrollo",
  },
  sujeto: "Grupo 01",
  periodos: tableroOperacion.periodos,
  periodo: "entrega:entrega-2",
  dias: [
    {
      dia: "2026-10-01",
      colapsado: false,
      hasta: null,
      n_dias: 1,
      commits: [
        {
          sha: "a".repeat(40),
          sha_corto: "aaaaaaa",
          fecha,
          mensaje: "Implementar permisos y navegación",
          autor: "Estudiante de ensayo",
          regla_atribucion: "GITHUB_ID",
          senal_debil: false,
          etiqueta_exclusion: null,
          rama: "desarrollo",
          destacado: "Versión de la entrega parcial",
          hito: null,
          posterior_al_cierre_de: 1,
          url: "https://github.com/organizacion-demo/grupo-01/commit/aaaaaaa",
        },
      ],
    },
  ],
  ciclo_de_vida: [
    { fecha: "2026-09-14T18:00:00Z", tipo: "REPOSITORIO_CREADO", detalle: {} },
    {
      fecha: "2026-09-14T18:03:00Z",
      tipo: "INVITACION_ACEPTADA",
      detalle: { estudiante: "Estudiante de ensayo" },
    },
  ],
  marcas_entrega: [
    {
      orden: 1,
      entrega: "Entrega parcial",
      fecha,
      aplica: true,
      versiones: [
        {
          intento: 1,
          vigente: true,
          estado: "CAPTURADA_SIN_TAG",
          motivo: null,
          commit_sha: "a".repeat(40),
        },
      ],
    },
  ],
  composicion: [
    {
      estudiante: "Estudiante de ensayo",
      desde: "2026-09-14T18:00:00Z",
      hasta: null,
    },
  ],
  franja: [
    {
      periodo: "entrega:entrega-1",
      entrega: "Entrega parcial",
      integrantes: [
        {
          estudiante_id: "e-0",
          nombre: "Estudiante de ensayo",
          commits: 11,
          dias_activos: 5,
          causa: null,
        },
      ],
      sin_atribuir: 2,
    },
  ],
  enlaces: { motivo: null },
  identidades_sin_resolver: 1,
  sin_commits_contables: false,
  causa_vacia: null,
};
const archivo: EstadoArchivado = {
  tarea_estado: "ACTIVA",
  archivables: 197,
  archivados: 0,
  fuera_de_alcance_o_inaccesibles: 1,
  guardas: [
    "Cierre final registrado",
    "Capturas completas",
    "Correcciones finalizadas",
    "Aviso previo entregado",
    "Repositorios disponibles",
  ].map((titulo, i) => ({
    numero: i + 1,
    titulo,
    cumple: i > 0,
    motivo: i === 0 ? "La entrega final todavía está abierta." : null,
    confirmacion: null,
    detalle: [],
  })),
  permitido: false,
  aviso: {
    destinatarios: 200,
    encolados: 200,
    enviados: 200,
    bloqueados: 0,
    ultimo_envio: fecha,
    canal_bloqueado: false,
  },
  en_curso: 0,
  puede_desarchivar: false,
};
export async function prepararOperacion(page: Page) {
  const base = await preparar(page);
  const estado = {
    base,
    tarea: structuredClone(tareaOperacion),
    tablero: structuredClone(tableroOperacion),
    timeline: structuredClone(timelineOperacion),
    version: structuredClone(versionOperacion),
    archivo: structuredClone(archivo),
    solicitudes: [] as {
      path: string;
      method: string;
      body: unknown;
      query: string;
    }[],
    falloTablero: false,
    falloCaptura: false,
  };
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();
    const body = request.postDataJSON();
    estado.solicitudes.push({ path, method, body, query: url.search });
    const responder = (json: unknown, status = 200) =>
      route.fulfill({ status, json });
    if (path === "/api/capacidades")
      return responder({
        perfil: "completo",
        banderas: [
          "tarea_multientrega",
          "tarea_modalidad_grupal",
          "fechas_excepciones",
          "versiones_entrega",
          "tarea_archivado",
          "tablero_actividad",
          "repositorio_timeline",
          "ingesta_actividad",
          "mis_notificaciones",
          "informe_diario",
          "comunicaciones_automaticas",
          "correccion",
        ],
      });
    if (path.endsWith("/tareas/tarea-1")) return responder(estado.tarea);
    if (path.endsWith("/tareas") && method === "POST") {
      estado.tarea.nombre = body.nombre;
      estado.tarea.estado = "BORRADOR";
      estado.tarea.modalidad =
        body.canvas_assignment_id === 456 ? "GRUPAL" : "INDIVIDUAL";
      estado.tarea.entregas = [
        { ...tareaOperacion.entregas[1], id: "entrega-2", orden: 1 },
      ];
      return responder(estado.tarea);
    }
    if (path.endsWith("/tareas"))
      return responder([
        {
          ...estado.tarea,
          cantidad_entregas: estado.tarea.entregas.length,
          creada_en: fecha,
          estado_repositorio_base: "LISTO",
        },
      ]);
    if (path.endsWith("/tareas/assignments-canvas"))
      return responder({
        assignments: [
          {
            canvas_assignment_id: 456,
            nombre: "Proyecto grupal",
            es_grupal: true,
            publicada: true,
            due_at: fecha,
            seleccionable: true,
            motivo: null,
          },
          {
            canvas_assignment_id: 123,
            nombre: "Entrega parcial",
            es_grupal: true,
            publicada: true,
            due_at: fecha,
            seleccionable: true,
            motivo: null,
          },
        ],
        sincronizado_en: fecha,
        plantillas_gitignore: ["Node", "Python"],
      });
    if (path.endsWith("/tareas/tarea-1/entregas") && method === "POST") {
      estado.tarea.entregas = structuredClone(tareaOperacion.entregas);
      return responder(estado.tarea);
    }
    if (path.endsWith("/activar")) {
      estado.tarea.estado = "ACTIVA";
      return responder(estado.tarea);
    }
    if (path.endsWith("/tablero/actualizar"))
      return responder(
        {
          encolada: true,
          en_curso: false,
          disponible_en: new Date(Date.now() + 300_000).toISOString(),
        },
        202,
      );
    if (path.endsWith("/tablero")) {
      if (estado.falloTablero)
        return responder(
          { detail: "No se pudo consultar la actividad. Intenta nuevamente." },
          503,
        );
      const pagina = Number(url.searchParams.get("pagina") ?? 1);
      let filas = estado.tablero.filas;
      if (url.searchParams.get("seccion"))
        filas = filas.filter(
          (f) => f.seccion === url.searchParams.get("seccion"),
        );
      if (url.searchParams.get("grupo_estado"))
        filas = filas.filter(
          (f) => f.grupo_estado === url.searchParams.get("grupo_estado"),
        );
      if (url.searchParams.get("solo_alertas"))
        filas = filas.filter((f) => f.alertas.length > 0);
      return responder({
        ...estado.tablero,
        pagina,
        periodo: url.searchParams.get("periodo") ?? estado.tablero.periodo,
        total_filas: filas.length,
        filas: filas.slice((pagina - 1) * 50, pagina * 50),
      });
    }
    if (path.endsWith("/timeline"))
      return responder({
        ...estado.timeline,
        periodo: url.searchParams.get("periodo") ?? estado.timeline.periodo,
      });
    if (path.endsWith("/hito")) {
      estado.timeline.dias[0].commits[0].hito =
        method === "DELETE" ? null : body.nota;
      return responder({ ok: true });
    }
    if (path.endsWith("/identidades"))
      return responder([
        {
          id: "identidad-1",
          email: "de***@example.test",
          nombre_visto: "Autor de ensayo",
          estado: "SIN_RESOLVER",
          estudiante: null,
          commits_contables: 2,
        },
      ]);
    if (path.endsWith("/propagacion"))
      return responder([
        {
          repositorio_id: "r-1",
          repositorio: "Grupo 02",
          identidad_id: "identidad-2",
          nombre_visto: "Autor de ensayo",
          commits: 3,
          marcada: false,
        },
      ]);
    if (path.endsWith("/revelar"))
      return responder({ email: "demo@example.test" });
    if (path.endsWith("/resolver"))
      return responder({
        id: "identidad-1",
        email: "de***@example.test",
        nombre_visto: "Autor de ensayo",
        estado: "RESUELTA",
        estudiante: "Estudiante de ensayo",
        commits_contables: 2,
      });
    if (path.endsWith("/progreso-captura")) {
      if (estado.falloCaptura)
        return responder({ detail: "No se pudo consultar la captura." }, 503);
      const entregaId = path.split("/").at(-2)!;
      const salida: ProgresoCaptura = {
        entrega_id: entregaId,
        estado_validacion: "VIGENTE",
        vencidas: 1,
        registradas: 1,
        por_estado: { CAPTURADA_SIN_TAG: 1 },
        capturas_tardias: 0,
        filas: [
          {
            sujeto_id: "sujeto-1",
            sujeto: "Grupo 01",
            fecha,
            estado_captura: "CAPTURADA_SIN_TAG",
            version: estado.version,
          },
        ],
      };
      return responder(salida);
    }
    if (path.endsWith("/version")) {
      const ficha: FichaVersion = {
        sujeto: "Grupo 01",
        vigente: estado.version,
        anteriores:
          estado.version.intento > 1
            ? [{ ...versionOperacion, vigente: false }]
            : [],
        acceso_docente: "CONCEDIDO",
      };
      return responder(ficha);
    }
    if (/\/version\/(recapturar|fijar-sha|capturar-ahora)$/.test(path)) {
      estado.version = {
        ...estado.version,
        id: "version-2",
        intento: 2,
        motivo_manual: body.motivo_manual,
        origen_captura: "MANUAL_FECHA",
        fecha_corte: body.fecha_corte ?? fecha,
      };
      return responder(estado.version);
    }
    if (path.endsWith("/archivado")) return responder(estado.archivo);
    if (path.endsWith("/archivar")) {
      estado.archivo.en_curso = 197;
      return responder({ repositorios: 197 }, 202);
    }
    if (path.endsWith("/archivar/aviso"))
      return responder({ encolados: 200 }, 202);
    if (path.endsWith("/entregas/fechas"))
      return responder(
        estado.tarea.entregas.map((e) => ({
          entrega_id: e.id,
          nombre: e.nombre,
          tipo: e.tipo,
          orden: e.orden,
          estado_validacion: "VIGENTE",
          cierre_base: "06-10-2026 16:00 (America/Santiago)",
          fechas_distintas: 1,
          excepciones: [],
          ambiguas: [],
          sujetos_con_fecha: 200,
          sujetos_sin_fecha: 0,
        })),
      );
    if (path.endsWith("/historial-fechas")) return responder([]);
    if (path.endsWith("/seguimiento"))
      return responder([
        {
          tarea_id: "tarea-1",
          nombre: estado.tarea.nombre,
          modalidad: "GRUPAL",
          repositorios: repositorios.resumen,
          sin_actividad: 4,
          sin_participacion: 3,
          invitaciones_sin_aceptar: 1,
        },
      ]);
    return route.fallback();
  });
  return estado;
}
