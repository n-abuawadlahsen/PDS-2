import { expect, test } from "@playwright/test";
import { prepararOperacion } from "./fixtures-operacion";

test.beforeEach(async ({ page }) => {
  page.on("pageerror", (error) =>
    console.error("Error de navegador:", error.message),
  );
});

test("tablero pagina 200 sujetos y conserva filtros al visitar el timeline", async ({
  page,
}) => {
  const estado = await prepararOperacion(page);
  await page.goto("/cursos/curso-1/tareas/tarea-1");
  await expect(
    page.getByRole("heading", { name: "Tablero", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("200 repositorios · página 1 de 4"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Siguiente", exact: true }).click();
  await expect(
    page.getByRole("link", { name: "Grupo 51", exact: true }),
  ).toBeVisible();
  expect(
    estado.solicitudes.some(
      (r) => r.path.endsWith("/tablero") && r.query.includes("pagina=2"),
    ),
  ).toBeTruthy();
  await page.getByLabel("Sección", { exact: true }).selectOption("Sección 1");
  await expect(
    page.getByText("100 repositorios · página 1 de 2"),
  ).toBeVisible();
  await page.getByRole("link", { name: "Grupo 01", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Actividad de Grupo 01" }),
  ).toBeVisible();
  await page.getByLabel("Rama", { exact: true }).selectOption("desarrollo");
  await expect
    .poll(() =>
      estado.solicitudes.some(
        (r) =>
          r.path.endsWith("/timeline") && r.query.includes("rama=desarrollo"),
      ),
    )
    .toBeTruthy();
  await page.getByRole("link", { name: "Volver al tablero" }).click();
  await expect(page.getByLabel("Sección", { exact: true })).toHaveValue(
    "Sección 1",
  );
  await expect(
    page.getByText("100 repositorios · página 1 de 2"),
  ).toBeVisible();
});

test("recupera errores y actualizar encola una sola operación con cooldown", async ({
  page,
}) => {
  const estado = await prepararOperacion(page);
  estado.falloTablero = true;
  await page.goto("/cursos/curso-1/tareas/tarea-1");
  await expect(
    page.getByText("No se pudo consultar la actividad. Intenta nuevamente.", {
      exact: true,
    }),
  ).toBeVisible();
  estado.falloTablero = false;
  await page.getByRole("button", { name: "Intentar nuevamente" }).click();
  await expect(
    page.getByRole("heading", { name: "Tablero", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Actualizar ahora", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Actualización en curso", exact: true }),
  ).toBeDisabled();
  expect(
    estado.solicitudes.filter((r) => r.path.endsWith("/tablero/actualizar")),
  ).toHaveLength(1);
});

test("selección de entrega y recaptura preservan historial y zona de fecha", async ({
  page,
}) => {
  const estado = await prepararOperacion(page);
  await page.goto("/cursos/curso-1/tareas/tarea-1/entregas?entrega=entrega-1");
  await expect(
    page.getByRole("button", { name: "Parcial 1: Entrega parcial" }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Ver versiones", exact: true })
    .click();
  await expect(
    page.getByText("Versión registrada (sin etiqueta en GitHub)").first(),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Ver el código de esta versión" }),
  ).toHaveAttribute("href", /\/api\/.*version-1/);
  await page
    .getByRole("button", {
      name: "Recapturar con otra fecha de corte",
      exact: true,
    })
    .click();
  await page
    .getByLabel("Fecha de corte con zona horaria")
    .fill("2026-10-01T16:00:00-03:00");
  await page
    .getByLabel("Motivo (obligatorio, queda en la bitácora)")
    .fill("Extensión confirmada por el equipo docente");
  await page.getByRole("button", { name: "Confirmar", exact: true }).click();
  await expect(page.getByText("v2 · Vigente", { exact: false })).toBeVisible();
  await page
    .getByText("Versiones anteriores (1); ninguna se descarta", { exact: true })
    .click();
  await expect(page.getByText("v1 · Anterior", { exact: false })).toBeVisible();
  const solicitud = estado.solicitudes.find((r) =>
    r.path.endsWith("/recapturar"),
  );
  expect(solicitud?.body).toMatchObject({
    fecha_corte: "2026-10-01T19:00:00.000Z",
  });
  await expect(
    page
      .getByText("01-10-2026 16:00 (America/Santiago)", { exact: false })
      .first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Final 2: Entrega final" }).click();
  await expect(page).toHaveURL(/entrega=entrega-2/);
});

test("ayudante lector conserva evidencia sin controles de recaptura, hito o identidades", async ({
  page,
}) => {
  const estado = await prepararOperacion(page);
  estado.base.permisos = ["curso.ver", "correccion.corregir"];
  await page.goto("/cursos/curso-1/tareas/tarea-1/entregas");
  await page
    .getByRole("button", { name: "Ver versiones", exact: true })
    .click();
  await expect(
    page.getByRole("link", { name: "Ver el código de esta versión" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Recapturar con otra fecha de corte",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", {
      name: "Archivar repositorios de la tarea",
      exact: true,
    }),
  ).toHaveCount(0);
  await page.goto("/cursos/curso-1/tareas/tarea-1/repos/r-0");
  await expect(
    page.getByRole("heading", { name: "Actividad de Grupo 01" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Marcar hito", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Revelar correo", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Asociar identidad", exact: true }),
  ).toHaveCount(0);
});

test("identidad propaga solo a repositorios seleccionados y requiere confirmación", async ({
  page,
}) => {
  const estado = await prepararOperacion(page);
  await page.goto("/cursos/curso-1/tareas/tarea-1/repos/r-0");
  await page
    .getByRole("button", { name: "Asociar identidad", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Vista previa de propagación" }),
  ).toBeVisible();
  const casilla = page.getByRole("checkbox", { name: /Grupo 02/ });
  await expect(casilla).not.toBeChecked();
  await page.getByLabel("Estudiante", { exact: true }).selectOption("e-0");
  await casilla.check();
  await page.getByRole("button", { name: "Revisar y asociar" }).click();
  await expect(page.getByRole("dialog")).toContainText(
    "1 repositorios seleccionados",
  );
  expect(
    estado.solicitudes.filter((r) => r.path.endsWith("/resolver")),
  ).toHaveLength(0);
  await page
    .getByRole("button", { name: "Confirmar asociación", exact: true })
    .click();
  await expect
    .poll(
      () => estado.solicitudes.find((r) => r.path.endsWith("/resolver"))?.body,
    )
    .toMatchObject({ estudiante_id: "e-0", propagar_a: ["r-1"] });
});

test("cierre conserva las cinco guardas y confirma antes de encolar archivado", async ({
  page,
}) => {
  const estado = await prepararOperacion(page);
  await page.goto("/cursos/curso-1/tareas/tarea-1/entregas");
  await expect(
    page.getByRole("button", { name: "Archivar repositorios de la tarea" }),
  ).toBeDisabled();
  await expect(
    page.getByText("La entrega final todavía está abierta."),
  ).toBeVisible();
  estado.archivo.guardas.forEach((g) => {
    g.cumple = true;
    g.motivo = null;
  });
  estado.archivo.permitido = true;
  await page.reload();
  await page
    .getByRole("button", { name: "Archivar repositorios de la tarea" })
    .click();
  await expect(page.getByRole("dialog")).toContainText("197 repositorios");
  expect(
    estado.solicitudes.filter((r) => r.path.endsWith("/archivar")),
  ).toHaveLength(0);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Archivar repositorios", exact: true })
    .click();
  await expect(
    page.getByText("Archivado en curso para 197 repositorios."),
  ).toBeVisible();
});

test("crea tarea grupal y activa el aprovisionamiento desde la configuración", async ({
  page,
}) => {
  const estado = await prepararOperacion(page);
  await page.goto("/cursos/curso-1/tareas");
  await page.getByRole("button", { name: "Crear tarea", exact: true }).click();
  await page.getByLabel("Tarea de Canvas", { exact: true }).selectOption("456");
  await expect(
    page.getByText("Modalidad: Grupal", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Crear borrador" }).click();
  await expect(page).toHaveURL(/\/tareas\/tarea-1/);
  await page
    .getByRole("navigation", { name: "Secciones de la tarea" })
    .getByRole("link", { name: "Configuración", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Activar tarea", exact: true })
    .click();
  await expect(
    page.getByText("Comenzó el proceso automático", { exact: false }),
  ).toBeVisible();
  expect(
    estado.solicitudes.some(
      (r) => r.method === "POST" && r.path.endsWith("/activar"),
    ),
  ).toBeTruthy();
});
