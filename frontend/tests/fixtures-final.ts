import type { Page } from "@playwright/test";
import type {
  PantallaCorreccion,
  MatrizCorreccion,
  MensajeBandeja,
} from "../src/lib/api";
import { preparar, curso } from "./fixtures";

/** Dobles de los contratos F9–F12; no alcanza Canvas, GitHub ni correo. */
export async function prepararFinal(page: Page) {
  const base = await preparar(page);
  base.permisos.push(
    "correccion.corregir",
    "correccion.asignar",
    "nota.publicar",
  );
  const estado = {
    base,
    conflicto: false,
    bloqueo: false,
    falloBorrador: false,
    falloMensaje: false,
    cantidad: 3,
    suscrito: false,
    suspendidas: false,
    comprobado: null as string | null,
    guardados: 0,
    publicaciones: 0,
    llamadas: [] as { path: string; method: string; body: unknown }[],
    filas: {} as Record<string, PantallaCorreccion>,
    mensajes: [] as MensajeBandeja[],
  };
  function pantalla(id: string): PantallaCorreccion {
    const i = Number(id.replace("sujeto-", "")) || 0;
    if (!estado.filas[id])
      estado.filas[id] = {
        entrega: {
          id: "entrega-1",
          nombre: "Entrega final",
          tarea_id: "tarea-1",
          tarea: "Proyecto de software",
          grading_type: "points",
          puntos_posibles: 100,
          fecha_efectiva: "06-10-2026 16:00 (America/Santiago)",
          origen_fecha: "BASE",
        },
        sujeto: {
          id,
          nombre: `Equipo ${String(i + 1).padStart(2, "0")}`,
          integrantes: ["Integrante de prueba A", "Integrante de prueba B"],
          activo: true,
        },
        estado: "EN_CURSO",
        etiqueta: "En curso",
        corrector: "Docente de prueba",
        es_propietario: true,
        puede_publicar: true,
        titular: "Docente de prueba",
        publicable: true,
        motivo_no_publicable: null,
        banderas: {
          version_desactualizada: false,
          reclamo_abierto: false,
          sin_commits: false,
          reconocimiento_sin_codigo: false,
        },
        version: {
          id: `version-${i}`,
          estado: "REGISTRADA",
          sha: "a1b2c3d4e5f6789012345678901234567890abcd12",
          sha_corto: "a1b2c3d",
          tag: "entrega-final",
          repositorio: "organizacion-prueba/proyecto-equipo-01",
          fecha_corte: "06-10-2026 16:00 (America/Santiago)",
        },
        repositorio_estado: "OPERATIVO",
        acceso_docente: "CONCEDIDO",
        motivo_sin_enlace: null,
        borrador: {
          nota: "75",
          comentario:
            "La estructura está bien resuelta. Revisa los casos límite en la validación.",
          rubrica: { calidad: { points: 40, rating_id: "bueno" } },
          version: 1,
        },
        rubrica: {
          criterios: [
            {
              id: "calidad",
              description: "Calidad de la implementación",
              points: 50,
              ratings: [
                { id: "excelente", description: "Excelente", points: 50 },
                { id: "bueno", description: "Logrado", points: 40 },
                { id: "suficiente", description: "Suficiente", points: 25 },
              ],
            },
          ],
          ajustes: {},
          usar_para_calificar: false,
          suma_sugerida: 40,
          cambio_sin_revisar: false,
        },
        notas_internas: [],
        historial: [
          {
            entrega: "Entrega parcial",
            estado: "Publicada",
            nota_publicada: "80",
          },
        ],
        canvas: [
          {
            estudiante: "Integrante de prueba A",
            score: null,
            calificada_en: null,
          },
          {
            estudiante: "Integrante de prueba B",
            score: null,
            calificada_en: null,
          },
        ],
        navegacion: {
          posicion: i + 1,
          total: estado.cantidad,
          anterior: i > 0 ? `sujeto-${i - 1}` : null,
          siguiente: i + 1 < estado.cantidad ? `sujeto-${i + 1}` : null,
          siguiente_sin_corregir:
            i + 1 < estado.cantidad ? `sujeto-${i + 1}` : null,
        },
      };
    const p = estado.filas[id];
    p.puede_publicar = base.permisos.includes("nota.publicar");
    p.publicable = !estado.bloqueo;
    p.motivo_no_publicable = estado.bloqueo
      ? "El período de calificación está cerrado"
      : null;
    return p;
  }
  function matriz(): MatrizCorreccion {
    const sujetos = Array.from({ length: estado.cantidad }, (_, i) =>
      pantalla(`sujeto-${i}`),
    );
    return {
      entregas: [{ id: "entrega-1", nombre: "Entrega final", orden: 1 }],
      sujetos: sujetos.map((p, i) => ({
        sujeto_id: p.sujeto.id,
        sujeto: p.sujeto.nombre,
        activo: true,
        seccion: i % 2 ? "Sección 2" : "Sección 1",
        celdas: {
          "entrega-1": {
            estado: p.estado,
            etiqueta: p.etiqueta,
            corrector: p.corrector,
            publicable: p.publicable,
            motivo_no_publicable: p.motivo_no_publicable,
            banderas: p.banderas.sin_commits ? ["sin_commits"] : [],
            contraste: estado.conflicto ? "DIVERGE" : "SIN_COMPROBAR",
          },
        },
      })),
      por_corrector: { "Docente de prueba": { EN_CURSO: estado.cantidad } },
      por_seccion: {
        "Sección 1": { EN_CURSO: Math.ceil(estado.cantidad / 2) },
        "Sección 2": { EN_CURSO: Math.floor(estado.cantidad / 2) },
      },
      por_entrega: { "Entrega final": { EN_CURSO: estado.cantidad } },
      contador: {
        corregidas: sujetos.filter((p) =>
          ["LISTA_PARA_PUBLICAR", "PUBLICADA"].includes(p.estado),
        ).length,
        con_nota_en_canvas: sujetos.filter((p) => p.estado === "PUBLICADA")
          .length,
        total: estado.cantidad,
        comprobado_en: estado.comprobado,
      },
    };
  }
  function suscripcion() {
    return {
      curso_id: curso.id,
      curso_nombre: curso.nombre,
      curso_codigo: curso.codigo,
      activa: estado.suscrito,
      origen_baja: estado.suscrito ? null : "USUARIO",
      se_genera_desde: "2026-10-01",
    };
  }
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();
    const body = request.postDataJSON();
    const responder = (json: unknown, status = 200) =>
      route.fulfill({ json, status });
    estado.llamadas.push({ path, method, body });
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
    if (path.endsWith("/correccion/correctores"))
      return responder([
        {
          membresia_id: "m-1",
          nombre: "Docente de prueba",
          rol: "PROFESOR",
          peso: 0,
          sin_github: false,
        },
        {
          membresia_id: "m-2",
          nombre: "Ayudante de prueba",
          rol: "AYUDANTE",
          peso: 1,
          sin_github: false,
        },
      ]);
    if (path.endsWith("/correccion/estado")) return responder(matriz());
    if (path.endsWith("/correccion"))
      return responder({
        mis_asignaciones: Array.from({ length: estado.cantidad }, (_, i) => {
          const p = pantalla(`sujeto-${i}`);
          return {
            entrega_id: "entrega-1",
            entrega: "Entrega final",
            tarea_id: "tarea-1",
            sujeto_id: p.sujeto.id,
            sujeto: p.sujeto.nombre,
            estado: p.estado,
            etiqueta: p.etiqueta,
            sin_commits: false,
            reclamo_abierto: false,
            version_desactualizada: false,
            nueva: i === 0,
            actualizado_en: "2026-10-02T14:00:00Z",
          };
        }),
        contador: { asignadas: estado.cantidad, corregidas: 0, publicadas: 0 },
        nuevas: 1,
        sin_corrector: 0,
        puede_repartir: base.permisos.includes("correccion.asignar"),
        puede_publicar: base.permisos.includes("nota.publicar"),
        es_profesor: base.permisos.includes("curso.administrar"),
        tareas: [
          {
            id: "tarea-1",
            nombre: "Proyecto de software",
            entregas: [{ id: "entrega-1", nombre: "Entrega final", orden: 1 }],
          },
        ],
      });
    if (path.endsWith("/comprobar")) {
      estado.comprobado = new Date().toISOString();
      return responder({ encolada: true, trabajo_id: "comprobar-1" }, 202);
    }
    if (path.endsWith("/trabajos/comprobar-1")) {
      return responder({
        id: "comprobar-1",
        estado: "OK",
        intentos: 1,
        max_intentos: 4,
        proximo_intento_en: null,
        terminado_en: estado.comprobado,
      });
    }
    const cor = path.match(/\/correccion\/entrega-1\/(sujeto-\d+)(?:\/(.+))?$/);
    if (cor) {
      const p = pantalla(cor[1]);
      const accion = cor[2];
      if (!accion) return responder(p);
      if (accion === "borrador") {
        if (estado.falloBorrador)
          return responder(
            {
              detail:
                "Otra persona actualizó este borrador. Tus cambios se conservan.",
            },
            409,
          );
        estado.guardados++;
        p.borrador = { ...body, version: (p.borrador?.version ?? 0) + 1 };
        p.estado = "EN_CURSO";
        p.etiqueta = "En curso";
        return responder({ estado: p.estado, version: p.borrador.version });
      }
      if (accion === "lista") {
        p.estado = "LISTA_PARA_PUBLICAR";
        p.etiqueta = "Lista para publicar";
        return responder({ estado: p.estado, nota: p.borrador?.nota });
      }
      if (accion === "publicar") {
        if (estado.bloqueo)
          return responder(
            {
              detail: {
                codigo: "PUBLICACION",
                motivo: "El período de calificación está cerrado",
              },
            },
            409,
          );
        if (estado.conflicto && body?.resolucion !== "PUBLICAR_MIA")
          return responder(
            {
              detail: {
                codigo: "CONFLICTO",
                motivo: "Canvas ya tiene otra nota",
                nota_propia: p.borrador?.nota,
                conflictos: [
                  {
                    estudiante: "Integrante de prueba A",
                    nota_canvas: 65,
                    calificada_en: "2026-10-02T12:00:00Z",
                  },
                ],
              },
            },
            409,
          );
        estado.publicaciones++;
        p.estado = "PUBLICADA";
        p.etiqueta = "Publicada";
        p.canvas.forEach((c) => {
          c.score = Number(p.borrador?.nota);
        });
        return responder({ estado: p.estado });
      }
      if (accion === "adoptar-canvas") {
        p.estado = "PUBLICADA";
        p.etiqueta = "Publicada";
        if (p.borrador) p.borrador.nota = "65";
        return responder({ estado: p.estado, nota: "65" });
      }
      if (accion === "reabrir" || accion === "reintentar") {
        p.estado = accion === "reabrir" ? "EN_CURSO" : "LISTA_PARA_PUBLICAR";
        p.etiqueta = accion === "reabrir" ? "En curso" : "Lista para publicar";
        return responder({ estado: p.estado });
      }
      if (accion === "rubrica-revisada") {
        p.rubrica.cambio_sin_revisar = false;
        return responder({ revisada: true });
      }
      if (accion === "notas" || accion.startsWith("reclamos")) {
        p.banderas.reclamo_abierto = accion === "reclamos";
        p.notas_internas.push({
          clase:
            accion === "notas"
              ? "NOTA"
              : accion.endsWith("cerrar")
                ? "RECLAMO_CERRADO"
                : "RECLAMO_ABIERTO",
          texto: body.texto,
          desenlace: body.desenlace ?? null,
          creada_en: "2026-10-02T16:00:00Z",
        });
        return responder({ reclamo_abierto: p.banderas.reclamo_abierto });
      }
    }
    if (path.endsWith("/reparto/previsualizar"))
      return responder({
        filas: matriz().sujetos.map((s) => ({
          sujeto_id: s.sujeto_id,
          sujeto: s.sujeto,
          actual: "Docente de prueba",
          propuesto: "Ayudante de prueba",
          estado: "En curso",
          sobrescribe: true,
        })),
        totales: { "Ayudante de prueba": estado.cantidad },
        requiere_decision: [],
      });
    if (path.endsWith("/reparto/aplicar"))
      return responder({ cambios: estado.cantidad });
    if (path.endsWith("/mis-notificaciones")) {
      if (method === "PUT") estado.suscrito = body.activa;
      return responder(suscripcion());
    }
    if (path === "/api/perfil/notificaciones") {
      if (method === "PUT") estado.suscrito = body.activa;
      return responder([suscripcion()]);
    }
    if (path.endsWith("/enlaces-de-baja/regenerar"))
      return responder({ regenerados: true });
    if (path.endsWith("/informes"))
      return responder({
        se_genera_desde: "2026-10-01",
        informes: [
          {
            fecha: "2026-10-02",
            estado: "GENERADO",
            motivo: null,
            origen: "AUTOMATICO",
          },
          {
            fecha: "2026-10-01",
            estado: "GENERADO",
            motivo: null,
            origen: "AUTOMATICO",
          },
        ],
      });
    const html =
      '<html lang="es"><body><h1>Informe diario · ICC4201</h1><h2>Requiere atención</h2><p>Una entrega está próxima al cierre.</p><h2>Actividad reciente</h2><p>Los equipos registraron avances en sus repositorios.</p></body></html>';
    if (path.includes("/informes/"))
      return responder({
        fecha: "2026-10-02",
        estado: "GENERADO",
        motivo: null,
        html,
        texto: "Informe diario",
        asunto: "Informe docente diario",
        frescura: {},
      });
    if (path.endsWith("/vista-previa") && path.includes("/informe-de-hoy/"))
      return responder({
        hay_tareas_activas: true,
        mensaje: null,
        html,
        texto: "Informe docente diario",
      });
    if (path.includes("/informe-de-hoy/"))
      return responder({ encolados: 1 }, 202);
    if (path.endsWith("/comunicaciones") && path.includes("/tareas/"))
      return responder([
        {
          evento: "repositorio_disponible",
          titulo: "Repositorio disponible",
          activa: true,
          por_defecto: true,
          advertencia_al_apagar:
            "El estudiante no recibirá el enlace a su repositorio.",
          destinatarios_hoy: 3,
          vista_previa_asunto: "Tu repositorio está listo",
          vista_previa_cuerpo: "Puedes comenzar a trabajar en tu repositorio.",
          vista_previa_con_ejemplo: true,
        },
      ]);
    if (path.endsWith("/comunicaciones")) {
      if (method === "PATCH") estado.suspendidas = body.suspendidas;
      return responder({
        comunicaciones_salientes: estado.suspendidas
          ? "SUSPENDIDAS"
          : "ACTIVAS",
        suspension_motivo: estado.suspendidas ? "Revisión del curso" : null,
        canal_activo: "CONVERSACION",
        mensajes: estado.mensajes,
      });
    }
    if (path.endsWith("/comunicaciones/mensajes")) {
      if (estado.falloMensaje)
        return responder(
          {
            detail:
              "Canvas no está disponible. Conserva el texto e intenta más tarde.",
          },
          503,
        );
      estado.mensajes.push({
        id: "mensaje-1",
        canal: "CANVAS_CONVERSACION",
        evento: "MANUAL",
        estado: "PENDIENTE",
        etiqueta_estado: "En cola",
        motivo: null,
        destinatario: "Estudiante de prueba",
        asunto: body.asunto,
        cuerpo: body.cuerpo,
        origen: "MANUAL",
        generacion: 1,
        reemplaza_a_id: null,
        tarea_id: null,
        creado_en: "2026-10-02T14:00:00Z",
        enviado_en: null,
        programado_para: null,
        enlace_canvas: null,
        motivo_sin_enlace: "El mensaje todavía está en cola.",
        ultimo_error: null,
      });
      return responder(
        {
          encolados: 1,
          aviso:
            "Se enviará 1 mensaje; puedes seguir su estado en el historial.",
        },
        202,
      );
    }
    if (path.endsWith("/comunicaciones/anuncios")) {
      if (body.confirmacion_destinatarios !== 45)
        return responder(
          {
            detail: {
              codigo: "CONFIRMAR_DESTINATARIOS",
              motivo:
                "Este anuncio llega a 45 estudiantes. Escribe ese número para confirmar.",
              destinatarios: 45,
            },
          },
          409,
        );
      return responder({ mensaje_id: "anuncio-1", destinatarios: 45 }, 202);
    }
    return route.fallback();
  });
  return Object.assign(estado, { pantalla, matriz });
}
