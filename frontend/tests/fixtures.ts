import type { Page } from "@playwright/test";
export const curso = {
  id: "curso-1",
  estado: "ACTIVO",
  nombre: "Programación y desarrollo de software",
  codigo: "ICC4201",
  periodo: "2026-2",
  slug: "icc4201-2026-2",
  zona_horaria: "America/Santiago",
};
export const permisos = [
  "curso.ver",
  "curso.administrar",
  "equipo.administrar",
  "mapeo.editar",
  "tarea.administrar",
  "comunicacion.enviar",
];
export const perfil = {
  id: "profesor-1",
  nombre: "Docente de prueba",
  email: "docente.prueba@gmail.com",
  avatar_url: null,
  github_login_declarado: null,
  activo: true,
};
const fecha = "2026-09-14T18:00:00Z";
export const personas = {
  estudiantes: Array.from({ length: 45 }, (_, i) => ({
    id: `e-${i}`,
    canvas_user_id: 2000 + i,
    nombre:
      i === 0
        ? "Estudiante sin cuenta"
        : i === 1
          ? "Estudiante en conflicto"
          : `Estudiante ${String(i).padStart(2, "0")}`,
    estado: "ACTIVO",
    email: `estudiante${i}@example.test`,
    sis_user_id: `ID-${i}`,
    secciones: [i % 2 ? "Sección 2" : "Sección 1"],
    grupos: [],
    mapeo: {
      estado: i === 0 ? "SIN_DATO" : i === 1 ? "EN_CONFLICTO" : "VIGENTE",
      cuenta_login: i > 0 ? `estudiante-${i}` : null,
      motivo_invalidacion: null,
    },
  })),
  secciones: [
    {
      id: "s-1",
      nombre: "Sección 1",
      estado: "ACTIVA",
      cantidad_estudiantes: 23,
    },
    {
      id: "s-2",
      nombre: "Sección 2",
      estado: "ACTIVA",
      cantidad_estudiantes: 22,
    },
  ],
  grupos: [],
  roster_sincronizado_en: fecha,
  grupos_sincronizado_en: fecha,
  registro_estado: "ABIERTA",
};
export const tarea = {
  id: "tarea-1",
  nombre: "Tarea 1 · Estructuras de datos",
  slug: "t1-estructuras",
  modalidad: "INDIVIDUAL",
  estado: "ACTIVA",
  gitignore_template: null,
  activada_en: fecha,
  entregas: [
    {
      id: "entrega-1",
      canvas_assignment_id: 123,
      tipo: "FINAL",
      orden: 1,
      nombre: "Estructuras de datos",
      slug: "e1",
      publicada: true,
      due_at_base: "2026-09-21T02:59:00Z",
      estado_validacion: "VIGENTE",
      sincronizado_en: fecha,
    },
  ],
  repositorio_base: {
    id: "base-1",
    nombre: "icc4201-base",
    full_name: "organizacion-demo/icc4201-base",
    url_html: "https://github.com/organizacion-demo/icc4201-base",
    estado: "LISTO",
    rama_por_defecto: "principal",
    clase_error: null,
    error_mensaje_literal: null,
    archivos: [
      {
        ruta: "src/ejemplo.py",
        sha: "abc",
        tamano_bytes: 128,
        actualizado_en: fecha,
      },
    ],
  },
  nombre_repositorio_base: "icc4201-base",
  activar: { habilitada: true, motivo: null },
  vincular_otra_entrega: {
    habilitada: false,
    motivo: "Las múltiples entregas llegan el 23 de septiembre.",
  },
  crear_repositorio_base: {
    habilitada: false,
    motivo: "La tarea ya tiene un repositorio base.",
  },
};
export const repositorios = {
  verificacion_accesos: {
    intervalo_segundos: 60,
    trabajo_id: null as string | null,
    estado: null as string | null,
    solicitado_en: null as string | null,
    disponible_en: null as string | null,
  },
  resumen: {
    operativos: 195,
    degradados: 1,
    bloqueados: 0,
    esperando_limite: 0,
    error_transitorio: 0,
    error_permanente: 1,
    inaccesibles: 1,
    fuera_de_alcance: 0,
    archivados: 0,
    esperando_informacion: 1,
    listos_para_crear: 0,
    creando: 1,
    sujetos_activos: 200,
    sujetos_inactivos: 0,
    en_curso: true,
    creados: 197,
    minutos_restantes: 1,
  },
  filas: Array.from({ length: 200 }, (_, i) => ({
    repositorio_id: `r-${i}`,
    estudiante_id: `e-${i}`,
    sujeto: `Estudiante ${String(i).padStart(3, "0")}`,
    sujeto_activo: true,
    motivo_desactivacion: null,
    nombre: `icc4201-2026-2-t1-estructuras-estudiante-${2000 + i}`,
    url_html: i === 2 ? null : `https://github.com/organizacion-demo/repo-${i}`,
    estado:
      [
        "OPERATIVO",
        "DEGRADADO",
        "ESPERANDO_INFORMACION",
        "INACCESIBLE",
        "ERROR_PERMANENTE",
        "CREANDO",
      ][i] ?? "OPERATIVO",
    motivo:
      i === 1
        ? "FALTA_ACEPTAR_INVITACION_GITHUB"
        : i === 2
          ? "SIN_MAPEO_GITHUB"
          : null,
    error_codigo: null,
    error_mensaje_literal: null,
    intentos: 0,
    proximo_intento_en: null,
    cuenta_github: i === 2 ? null : `estudiante-${i}`,
    acceso_estado: i === 1 ? "INVITADO" : i === 2 ? "SIN_MAPEO" : "ACEPTADO",
    acceso_error: null,
    acceso_verificado_en: fecha as string | null,
    invitacion_url: null,
    acceso_docente: "CONCEDIDO",
    reemplaza_a_id: null,
    listo_en: fecha,
  })),
};
export async function preparar(page: Page) {
  const estado = {
    permisos: [...permisos],
    sesion: true,
    vacio: false,
    cursoVacio: false,
    reposRequests: 0,
    csv: [] as Record<string, string>[],
    llamadas: [] as { path: string; method: string; body: unknown }[],
    tarea: structuredClone(tarea),
    cuentas: structuredClone(personas),
    perfil: structuredClone(perfil),
    falloRepos: false,
  };
  await page.context().addCookies([
    {
      name: "csrf_token",
      value: "csrf-prueba",
      url: "http://127.0.0.1:4173",
    },
  ]);
  // Ninguna prueba alcanza servicios de terceros. Solo Vite y respuestas aisladas.
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.hostname !== "127.0.0.1") return route.abort();
    if (!url.pathname.startsWith("/api/")) return route.continue();
    const path = url.pathname;
    const method = request.method();
    const body = request.postDataJSON();
    estado.llamadas.push({ path, method, body });
    const responder = (json: unknown, status = 200) =>
      route.fulfill({ status, json });
    if (path === "/api/salud")
      return responder({ estado: "ok", servicio: "api" });
    if (path.endsWith("/equipo/invitaciones")) return responder([]);
    if (path === "/api/perfil/cierre")
      return responder({ puede_cerrar: true, cursos: [] });
    if (
      !estado.sesion &&
      path !== "/api/capacidades" &&
      !path.startsWith("/api/invitaciones/")
    )
      return responder({ detail: "sesion vencida" }, 401);
    if (path === "/api/perfil") {
      if (method === "PATCH") Object.assign(estado.perfil, body);
      return responder(estado.perfil);
    }
    if (path === "/api/perfil/cuenta-github") {
      estado.perfil.github_login_declarado = body?.login ?? null;
      return responder(estado.perfil);
    }
    if (path === "/api/perfil/sesiones")
      return responder(
        method === "GET"
          ? [
              {
                id: 1,
                agente: "Navegador de prueba",
                creada_en: fecha,
                es_la_actual: true,
              },
            ]
          : { ok: true },
      );
    if (path === "/api/capacidades")
      return responder({ perfil: "parcial", banderas: [] });
    if (path === "/api/cursos")
      return responder(
        method === "POST" ? { ...curso, ...body } : estado.vacio ? [] : [curso],
      );
    if (path.endsWith("/contexto"))
      return responder({
        rol: estado.permisos.includes("curso.administrar")
          ? "PROFESOR"
          : "AYUDANTE",
        permisos_efectivos: estado.permisos,
      });
    if (path.endsWith("/equipo"))
      return responder([
        {
          membresia_id: "m-1",
          usuario_id: perfil.id,
          nombre: perfil.nombre,
          email: perfil.email,
          rol: "PROFESOR",
          permisos: [],
          estado: "ACTIVA",
          retirada_en: null,
        },
      ]);
    if (path.endsWith("/personas")) return responder(estado.cuentas);
    if (path.endsWith("/mapeo/importar-csv")) {
      estado.csv.push(body);
      return responder({
        filas: [
          {
            fila: 1,
            canvas_user_id: 2000,
            login_id: null,
            github_login: "cuenta-prueba",
            resultado: body.aplicar === "true" ? "APLICADA" : "SE_APLICARIA",
            detalle: null,
          },
        ],
      });
    }
    if (path.endsWith("/pendientes"))
      return responder({
        bloque_1_sin_cuenta: [
          {
            estudiante_id: "e-0",
            nombre: "Estudiante sin cuenta",
            estado_estudiante: "ACTIVO",
            estado_mapeo: "SIN_DATO",
          },
        ],
        bloque_2_en_conflicto: [
          {
            estudiante_id: "e-1",
            nombre: "Estudiante en conflicto",
            estado_mapeo: "EN_CONFLICTO",
            cuenta_login: "cuenta-duplicada",
            motivo_invalidacion: null,
          },
        ],
        bloque_3_grupos_incompletos: [],
        bloque_4_invitaciones_sin_aceptar: [
          {
            estudiante_id: "e-2",
            nombre: "Estudiante invitado",
            estado_acceso: "INVITADO",
          },
        ],
      });
    if (path.endsWith("/recordatorio")) return responder({ ok: true }, 202);
    if (path === "/api/canvas/instancias")
      return responder([
        {
          base_url: "https://canvas.example.test",
          nombre_visible: "Canvas de prueba",
        },
      ]);
    if (path.endsWith("/vinculacion/canvas"))
      return responder(
        estado.cursoVacio
          ? []
          : [
              {
                titular_usuario_id: perfil.id,
                estado: "VALIDA",
                huella: "huella-de-prueba",
                orden_respaldo: 0,
                ultimo_chequeo_en: fecha,
              },
            ],
      );
    if (path.endsWith("/vinculacion/github"))
      return responder({
        org_login: estado.cursoVacio ? null : "organizacion-demo",
        installation_id: 1,
        equipo_docentes_slug: "docentes",
        curso_estado: curso.estado,
      });
    if (path.endsWith("/huerfanas")) return responder([]);
    if (path.endsWith("/verificacion/ultima"))
      return responder(
        estado.cursoVacio
          ? []
          : Array.from({ length: 19 }, (_, i) => ({
              item: String(i + 1),
              resultado: i === 2 ? "BLOQUEANTE" : "CORRECTO",
              detalle:
                i === 2
                  ? { motivo: "La cuenta está limitada a una sección" }
                  : {},
              ejecutada_en: fecha,
            })),
      );
    if (path.endsWith("/verificacion") && method === "POST")
      return responder({ ejecucion_id: "run-1" }, 202);
    if (path.endsWith("/verificacion/run-1"))
      return responder(
        Array.from({ length: 19 }, (_, i) => ({
          item: String(i + 1),
          resultado: "CORRECTO",
          detalle: {},
          ejecutada_en: fecha,
        })),
      );
    if (path.endsWith("/tareas/assignments-canvas"))
      return responder({
        assignments: [
          {
            canvas_assignment_id: 123,
            nombre: "Estructuras de datos",
            es_grupal: false,
            publicada: true,
            due_at: fecha,
            seleccionable: true,
            motivo: null,
          },
          {
            canvas_assignment_id: 456,
            nombre: "Proyecto grupal",
            es_grupal: true,
            publicada: true,
            due_at: fecha,
            seleccionable: false,
            motivo: "Las tareas grupales llegan el 23 de septiembre.",
          },
        ],
        sincronizado_en: fecha,
        plantillas_gitignore: ["Python", "Node"],
      });
    if (path.endsWith("/vista-previa-nombre"))
      return responder({
        slug: "tarea-prueba",
        slug_valido: true,
        slug_ocupado: false,
        ejemplo_repositorio: "icc4201-tarea-estudiante-2000",
        ejemplo_sujeto: "Estudiante de ejemplo",
        repositorio_base: "icc4201-base",
      });
    if (path.endsWith("/tareas"))
      return responder(
        estado.cursoVacio
          ? []
          : [
              {
                ...estado.tarea,
                cantidad_entregas: 1,
                estado_repositorio_base: "LISTO",
                creada_en: fecha,
              },
            ],
      );
    if (path.endsWith("/tareas/tarea-1")) return responder(estado.tarea);
    if (path.endsWith("/activar")) {
      if (!estado.permisos.includes("tarea.administrar"))
        return responder({ detail: "permiso insuficiente" }, 403);
      estado.tarea.estado = "ACTIVA";
      return responder(estado.tarea);
    }
    if (path.endsWith("/repositorios")) {
      estado.reposRequests++;
      if (estado.falloRepos)
        return responder({ detail: "Servicio no disponible" }, 503);
      return responder(repositorios);
    }
    if (path.endsWith("/sustituir") || path.endsWith("/reintentar"))
      return responder({ ok: true }, 202);
    if (path.endsWith("/entregas/fechas"))
      return responder([
        {
          entrega_id: "entrega-1",
          nombre: "Estructuras",
          tipo: "FINAL",
          orden: 1,
          cierre_base: "20 de septiembre, 23:59",
          fechas_distintas: 1,
          excepciones: [],
          sujetos_con_fecha: 200,
          sujetos_sin_fecha: 0,
        },
      ]);
    if (path.includes("/repositorio-base/archivos/")) {
      if (method === "GET")
        return responder({
          ruta: "src/ejemplo.py",
          tamano_bytes: 128,
          texto: "<script>window.pwned = true</script>",
          motivo_sin_texto: null,
        });
      return responder(estado.tarea);
    }
    if (path === "/api/vinculacion/github/callback")
      return responder({
        resultado: "VINCULADO",
        curso_id: curso.id,
        org_login: "organizacion-demo",
      });
    if (path.startsWith("/api/invitaciones/"))
      return responder({
        curso_nombre: curso.nombre,
        rol: "AYUDANTE",
        permisos: ["mapeo.editar"],
        email_enmascarado: "do***@gmail.com",
        estado: "PENDIENTE",
      });
    return responder({ detail: `Ruta sin fixture: ${method} ${path}` }, 501);
  });
  return estado;
}
