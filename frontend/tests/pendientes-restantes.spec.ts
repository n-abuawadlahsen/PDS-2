import { expect, test } from "@playwright/test";
import { curso, preparar } from "./fixtures";
import { prepararFinal } from "./fixtures-final";

test("Archivo exige el identificador y conserva una reactivación real", async ({
  page,
}) => {
  await preparar(page);
  let actual = { ...curso, roles_estudiante_extra: [] as number[] };
  await page.route("**/api/cursos", (r) => r.fulfill({ json: [actual] }));
  await page.route("**/archivo/previsualizar", (r) =>
    r.fulfill({ json: { repositorios: 2, sin_capturar: 1 } }),
  );
  let archivos = 0;
  await page.route("**/api/cursos/curso-1/archivar", (r) => {
    expect(r.request().postDataJSON()).toEqual({
      confirmar: true,
      slug: curso.slug,
      archivar_repositorios: true,
    });
    archivos++;
    actual = { ...actual, estado: "ARCHIVADO" };
    return r.fulfill({ json: actual });
  });
  await page.route("**/api/cursos/curso-1/desarchivar", (r) => {
    actual = { ...actual, estado: "ACTIVO" };
    return r.fulfill({ json: actual });
  });
  await page.goto("/cursos/curso-1/ajustes");
  await page.getByRole("button", { name: "Revisar archivado" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("2 repositorios conservados; 1 cierres");
  await expect(
    dialog.getByRole("button", { name: "Archivar", exact: true }),
  ).toBeDisabled();
  await dialog.getByRole("textbox").fill(curso.slug);
  expect(archivos).toBe(0);
  await dialog.getByRole("button", { name: "Archivar", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Curso archivado" }),
  ).toBeVisible();
  await expect(
    page.getByText("Los procesos y comunicaciones están pausados.", {
      exact: false,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Reactivar curso", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Reactivar", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Ajustes del curso" }),
  ).toBeVisible();
  expect(archivos).toBe(1);
});

test("El archivo remoto muestra las guardas y permite pausar el curso conservando GitHub", async ({
  page,
}) => {
  await preparar(page);
  await page.route("**/archivo/previsualizar", (r) =>
    r.fulfill({
      json: {
        repositorios: 2,
        sin_capturar: 1,
        repositorios_por_archivar: 2,
        capturas_pendientes: [
          {
            entrega_id: "entrega-1",
            entrega: "Entrega final",
            sujeto_id: "sujeto-1",
            cierre: null,
          },
        ],
        bloqueos: [
          {
            tarea_id: "tarea-1",
            tarea: "Proyecto de software",
            motivo:
              "1 correcciones no están publicadas, excusadas ni excluidas.",
          },
        ],
      },
    }),
  );
  await page.goto("/cursos/curso-1/ajustes");
  const opcion = page.getByRole("checkbox", {
    name: "Archivar también los repositorios en GitHub",
  });
  await expect(opcion).toBeChecked();
  await page.getByRole("button", { name: "Revisar archivado" }).click();
  await expect(
    page.getByRole("link", { name: "Revisar cierre" }),
  ).toHaveAttribute("href", "/cursos/curso-1/tareas/tarea-1/entregas");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await opcion.uncheck();
  await page.getByRole("button", { name: "Revisar archivado" }).click();
  await expect(page.getByRole("dialog")).toContainText(
    "Los repositorios mantendrán su estado en GitHub",
  );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Cancelar", exact: true })
    .click();
});

test("Un ayudante puede solicitar aviso de entregas sin corrector con confirmación", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  estado.base.permisos.splice(
    0,
    estado.base.permisos.length,
    "curso.ver",
    "correccion.corregir",
  );
  await page.route("**/api/cursos/curso-1/correccion", (r) =>
    r.fulfill({
      json: {
        mis_asignaciones: [],
        contador: { asignadas: 0, corregidas: 0, publicadas: 0 },
        sin_corrector: 2,
        puede_repartir: false,
        puede_publicar: false,
        es_profesor: false,
        tareas: [],
        nuevas: 0,
      },
    }),
  );
  let avisos = 0;
  await page.route("**/correccion/avisar-profesores", (r) => {
    avisos++;
    return r.fulfill({ status: 202, json: { encolados: 1 } });
  });
  await page.goto("/cursos/curso-1/correccion");
  await page
    .getByRole("button", { name: "Avisar a los profesores", exact: true })
    .click();
  expect(avisos).toBe(0);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Solicitar aviso", exact: true })
    .click();
  await expect(
    page.getByText(
      "Aviso solicitado. Puedes consultar su estado en Comunicaciones.",
      { exact: true },
    ),
  ).toBeVisible();
  expect(avisos).toBe(1);
});

test("Fusión muestra evidencia y sólo confirma tras revisión", async ({
  page,
}) => {
  await preparar(page);
  let confirmadas = 0;
  const candidato = {
    estudiante_id: "e-antiguo",
    nombre: "Ana Soto",
    canvas_user_id: 2001,
    coincidencias: ["login_id"],
    motivo_bloqueo: null,
    repositorios_conservados: 1,
    versiones_conservadas: 3,
  };
  await page.route("**/personas/fusiones-canvas", (r) =>
    r.fulfill({
      json: {
        pendientes: confirmadas
          ? []
          : [
              {
                incidencia_id: "fusion-1",
                nombre: "Ana Soto",
                canvas_user_id: 4001,
                candidatos: [candidato],
              },
            ],
        historial: [],
      },
    }),
  );
  await page.route("**/fusiones-canvas/fusion-1/confirmar", (r) => {
    expect(r.request().postDataJSON()).toEqual({
      anterior_id: "e-antiguo",
      confirmar: true,
    });
    confirmadas++;
    return r.fulfill({
      json: { estudiante_id: "e-antiguo", canvas_user_id: 4001 },
    });
  });
  await page.goto("/cursos/curso-1/personas");
  await page
    .getByText("Revisar posibles fusiones de identidades Canvas", {
      exact: true,
    })
    .click();
  await expect(
    page.getByText("Se conservarán los repositorios (1) y las versiones (3)", {
      exact: false,
    }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../docs/frontend/evidencias/pendientes-fusion-movil.png",
    fullPage: false,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  await page
    .getByRole("button", { name: "Confirmar que es la misma persona" })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Cancelar", exact: true })
    .click();
  expect(confirmadas).toBe(0);
  await page
    .getByRole("button", { name: "Confirmar que es la misma persona" })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar fusión", exact: true })
    .click();
  await expect(
    page.getByText("No hay propuestas de fusión pendientes."),
  ).toBeVisible();
  expect(confirmadas).toBe(1);
});

test("El reenvío de estudiante comprueba la invitación mediante un trabajo", async ({
  page,
}) => {
  await preparar(page);
  let solicitado = false;
  await page.route("**/personas/e-0/invitaciones-github", (r) =>
    r.fulfill({
      json: [
        {
          acceso_id: "acceso-1",
          repositorio: "repo-ana",
          estado: solicitado ? "INVITADO" : "EXPIRADA",
          reenvios: solicitado ? 1 : 0,
          ultimo_reenvio_en: null,
          proximo_reenvio_en: null,
          puede_solicitar: !solicitado,
        },
      ],
    }),
  );
  await page.route("**/invitaciones-github/acceso-1/reenviar", (r) => {
    solicitado = true;
    return r.fulfill({
      status: 202,
      json: { trabajo_id: "trabajo-invitacion" },
    });
  });
  await page.route("**/trabajos/trabajo-invitacion", (r) =>
    r.fulfill({
      json: {
        id: "trabajo-invitacion",
        estado: "OK",
        intentos: 0,
        max_intentos: 4,
        proximo_intento_en: null,
        terminado_en: "2026-10-06T12:00:00Z",
      },
    }),
  );
  await page.goto("/cursos/curso-1/personas");
  await page
    .getByRole("row")
    .filter({ hasText: "Estudiante sin cuenta" })
    .getByText("Invitaciones de GitHub", { exact: true })
    .click();
  await page
    .getByRole("button", {
      name: "Comprobar y reenviar invitación",
      exact: true,
    })
    .click();
  await expect(page.getByRole("dialog")).toContainText(
    "máximo de tres reenvíos",
  );
  expect(solicitado).toBe(false);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Solicitar comprobación", exact: true })
    .click();
  await expect(
    page.getByText("Reenvíos: 1/3.", { exact: false }),
  ).toBeVisible();
});

test("Realinear usa los criterios originales después de previsualizar", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  await page.goto("/cursos/curso-1/correccion?pestana=repartir&tarea=tarea-1");
  await page
    .getByRole("checkbox", {
      name: "Realinear sólo las asignaciones que requieren revisión",
    })
    .check();
  await expect(page.getByLabel("Criterio", { exact: true })).toBeDisabled();
  await page
    .getByRole("button", { name: "Previsualizar reparto", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Propuesta de reparto" }),
  ).toBeVisible();
  const llamada = estado.llamadas.find((l) =>
    l.path.endsWith("/reparto/previsualizar"),
  );
  expect(llamada?.body).toMatchObject({ realinear: true });
});

test("Una entrega grupal enlaza Canvas y confirma el espejo al terminar la sincronización", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  estado.base.tarea.modalidad = "GRUPAL";
  let individual = false;
  let finalizada = false;
  const enlace = "https://canvas.test/courses/5001/assignments/9102/edit";
  await page.route("**/entregas/entrega-1/calificacion-individual", (r) => {
    expect(r.request().method()).toBe("GET");
    return r.fulfill({
      json: {
        es_grupal: true,
        individual,
        puede_cambiar: !individual,
        motivo: null,
        enlace_canvas: enlace,
      },
    });
  });
  await page.route("**/api/cursos/curso-1/sincronizaciones", (r) => {
    expect(r.request().method()).toBe("POST");
    return r.fulfill({ status: 202, json: { trabajo_id: "sync-grupal" } });
  });
  await page.route("**/trabajos/sync-grupal", (r) => {
    individual = finalizada;
    return r.fulfill({
      json: {
        id: "sync-grupal",
        estado: finalizada ? "OK" : "PENDIENTE",
        intentos: 1,
        max_intentos: 6,
        proximo_intento_en: null,
        terminado_en: null,
      },
    });
  });
  await page.goto("/cursos/curso-1/tareas/tarea-1/entregas");
  await expect(
    page.getByRole("link", {
      name: "Configurar calificación individual en Canvas",
    }),
  ).toHaveAttribute("href", enlace);
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .getByRole("heading", { name: "Calificación del grupo en Canvas" })
    .locator("..")
    .screenshot({
      path: "../docs/frontend/evidencias/pendientes-calificacion-grupal-movil.png",
    });
  await page
    .getByRole("button", { name: "Ya lo cambié en Canvas: sincronizar" })
    .click();
  expect(individual).toBe(false);
  await expect(
    page.getByText("Canvas aplica una misma nota a todos los integrantes."),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Ya lo cambié en Canvas: sincronizar" }),
  ).toBeDisabled();
  await expect(
    page.getByText("Trabajo: Pendiente.", { exact: false }),
  ).toBeVisible();
  finalizada = true;
  await expect(
    page.getByText("Canvas permite una nota por integrante."),
  ).toBeVisible();
});
