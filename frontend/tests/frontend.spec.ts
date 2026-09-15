import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { preparar, repositorios } from "./fixtures";

async function sinDesborde(page: import("@playwright/test").Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
}
test("sesión vencida y rutas públicas conservan recuperación y POST de navegación", async ({
  page,
}) => {
  const datos = await preparar(page);
  datos.sesion = false;
  await page.goto("/cursos");
  await expect(
    page.getByRole("heading", { name: "Vuelve a entrar" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Entrar con Google" }).click();
  await expect(page.locator("form")).toHaveAttribute("method", "POST");
  await expect(page.locator("form")).toHaveAttribute(
    "action",
    "/auth/google/inicio",
  );
  await page.goto("/confirmar?token=prueba");
  await expect(page.locator("form")).toHaveAttribute(
    "action",
    "/auth/confirmar",
  );
  await page.goto("/ruta-inexistente");
  await expect(
    page.getByRole("heading", { name: "Página no encontrada" }),
  ).toBeVisible();
});
test("curso vacío, formulario y paleta conservan trabajo", async ({ page }) => {
  const datos = await preparar(page);
  datos.vacio = true;
  await page.goto("/cursos");
  await expect(
    page.getByRole("heading", { name: "Todavía no tienes cursos" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Crear mi primer curso" }).click();
  await page.getByLabel("Nombre del curso").fill("Mi nuevo curso");
  await page.goto("/perfil");
  await page.getByLabel("Nombre", { exact: true }).fill("Nombre sin guardar");
  for (const tema of ["azul", "verde", "institucional"]) {
    await page
      .getByRole("combobox", { name: "Apariencia", exact: true })
      .selectOption(tema);
    await expect(page.locator("html")).toHaveAttribute("data-theme", tema);
    await expect(page.getByLabel("Nombre", { exact: true })).toHaveValue(
      "Nombre sin guardar",
    );
    expect(datos.llamadas.filter((r) => r.method !== "GET")).toHaveLength(0);
  }
  await page
    .getByRole("combobox", { name: "Apariencia", exact: true })
    .selectOption("verde");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "verde");
  await page.evaluate(() =>
    localStorage.setItem("pds2.apariencia", "tema-invalido"),
  );
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme",
    "institucional",
  );
  await page.getByRole("button", { name: "Restablecer apariencia" }).click();
  expect(
    await page.evaluate(() => localStorage.getItem("pds2.apariencia")),
  ).toBeNull();
});
test("CSV solo aplica la revisión vigente y envía CSRF", async ({ page }) => {
  const datos = await preparar(page);
  await page.goto("/cursos/curso-1/personas");
  await page
    .getByText("Alternativa docente: importar cuentas por CSV", { exact: true })
    .click();
  await page
    .getByLabel("Contenido CSV")
    .fill("canvas_user_id,github_login\n2000,cuenta-prueba");
  const aplicar = page.getByRole("button", { name: "Aplicar filas revisadas" });
  await expect(aplicar).toBeDisabled();
  await page
    .getByRole("button", { name: "Previsualizar", exact: true })
    .click();
  await expect(aplicar).toBeEnabled();
  await page
    .getByLabel("Contenido CSV")
    .fill("canvas_user_id,github_login\n2000,otra-cuenta");
  await expect(aplicar).toBeDisabled();
  await page
    .getByRole("button", { name: "Previsualizar", exact: true })
    .click();
  await expect(aplicar).toBeEnabled();
  const solicitud = page.waitForRequest(
    (r) =>
      r.url().includes("importar-csv") && r.postDataJSON().aplicar === "true",
  );
  await aplicar.click();
  expect((await solicitud).headers()["x-csrf-token"]).toBe("csrf-prueba");
  await expect(aplicar).toBeDisabled();
  expect(datos.csv.map((r) => r.aplicar)).toEqual(["false", "false", "true"]);
});
test("bloqueo de activación, creación progresiva y revocación de permiso", async ({
  page,
}) => {
  const datos = await preparar(page);
  datos.tarea.estado = "BORRADOR";
  datos.tarea.activar = {
    habilitada: false,
    motivo: "La base todavía no está lista.",
  } as typeof datos.tarea.activar;
  await page.goto("/cursos/curso-1/tareas/tarea-1");
  await expect(
    page.getByRole("button", { name: "Activar tarea" }),
  ).toBeDisabled();
  await expect(page.getByText("La base todavía no está lista.")).toBeVisible();
  datos.tarea.activar.habilitada = true;
  await page.reload();
  await page.getByRole("button", { name: "Activar tarea" }).click();
  await expect(
    page.getByText("Comenzó el proceso automático", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", {
      name: "Listo, falta gente por entrar",
      exact: false,
    }),
  ).toBeVisible();
  datos.tarea.estado = "BORRADOR";
  await page.goto("/cursos/curso-1/tareas/tarea-1");
  await expect(
    page.getByRole("button", { name: "Activar tarea" }),
  ).toBeEnabled();
  datos.permisos = ["curso.ver"];
  await page.getByRole("button", { name: "Activar tarea" }).click();
  await expect(
    page.getByText("No tienes permiso para administrarla.", { exact: false }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Activar tarea" })).toHaveCount(
    0,
  );
});
test("ayudante conserva lectura y no recibe acciones administrativas", async ({
  page,
}) => {
  const d = await preparar(page);
  d.permisos = ["curso.ver"];
  await page.goto("/cursos/curso-1/personas");
  await expect(
    page.getByRole("heading", { name: "Personas", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Alternativa docente: importar cuentas por CSV"),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Sincronizar con Canvas" }),
  ).toHaveCount(0);
  await page.goto("/cursos/curso-1/tareas/tarea-1?vista=repositorios");
  await expect(
    page.getByRole("cell", { name: "Estudiante 000", exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Sustituir", exact: true }),
  ).toHaveCount(0);
});
test("polling conserva filtro, foco, página y datos ante fallo", async ({
  page,
}) => {
  const d = await preparar(page);
  await page.clock.install();
  await page.goto("/cursos/curso-1/tareas/tarea-1?vista=repositorios");
  await page.getByLabel("Buscar repositorio o estudiante").fill("Estudiante 0");
  await page.getByRole("button", { name: "Siguiente", exact: true }).click();
  await page.getByLabel("Buscar repositorio o estudiante").focus();
  const antes = d.reposRequests;
  await page.clock.fastForward(11_000);
  await expect.poll(() => d.reposRequests).toBeGreaterThan(antes);
  await expect(page.getByText("Página 2 de", { exact: false })).toBeVisible();
  await expect(
    page.getByLabel("Buscar repositorio o estudiante"),
  ).toBeFocused();
  d.falloRepos = true;
  await page.clock.fastForward(11_000);
  await expect(page.getByText("Servicio no disponible")).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "Estudiante 020", exact: false }),
  ).toBeVisible();
});
test("sustitución requiere texto exacto y devuelve foco al cerrar", async ({
  page,
}) => {
  const d = await preparar(page);
  await page.goto("/cursos/curso-1/tareas/tarea-1?vista=repositorios");
  const abrir = page.getByRole("button", { name: "Sustituir", exact: true });
  await abrir.click();
  const dialogo = page.getByRole("dialog");
  const confirmar = dialogo.getByRole("button", {
    name: "Sustituir repositorio",
    exact: true,
  });
  await expect(confirmar).toBeDisabled();
  await page.keyboard.press("Escape");
  await expect(dialogo).not.toBeVisible();
  await expect(abrir).toBeFocused();
  await abrir.click();
  await dialogo.getByRole("textbox").fill(repositorios.filas[3].nombre);
  await confirmar.click();
  await expect(
    page.getByText("Sustitución solicitada.", { exact: false }),
  ).toBeVisible();
  expect(d.llamadas.find((r) => r.path.endsWith("/sustituir"))?.body).toEqual({
    confirmacion: repositorios.filas[3].nombre,
  });
});
test("cuenta GitHub docente usa consentimiento real y vista previa de archivo es texto", async ({
  page,
}) => {
  const d = await preparar(page);
  await page.goto("/perfil");
  await page.getByLabel("Nombre de usuario de GitHub").fill("docente-github");
  const guardar = page.getByRole("button", {
    name: "Guardar cuenta de GitHub",
  });
  await expect(guardar).toBeDisabled();
  await page
    .getByRole("checkbox", { name: "Declaro mi propia cuenta", exact: false })
    .check();
  await guardar.click();
  await expect(
    page.getByText("Cuenta de GitHub registrada.", { exact: false }),
  ).toBeVisible();
  expect(
    d.llamadas.find((r) => r.path.endsWith("/cuenta-github"))?.body,
  ).toEqual({ login: "docente-github", consiento: true });
  await page.goto("/cursos/curso-1/tareas/tarea-1?vista=base");
  await page.getByRole("button", { name: "Ver", exact: true }).click();
  await expect(page.locator("pre")).toContainText("<script>");
  expect(await page.evaluate(() => "pwned" in window)).toBe(false);
});
test("callback de GitHub se canjea una sola vez", async ({ page }) => {
  const d = await preparar(page);
  await page.goto("/vinculacion/github/retorno?state=prueba&installation_id=1");
  await expect(
    page.getByText("quedó vinculada", { exact: false }),
  ).toBeVisible();
  expect(
    d.llamadas.filter((r) => r.path === "/api/vinculacion/github/callback"),
  ).toHaveLength(1);
});
test("checklist conserva bloqueantes y las pruebas opcionales exigen consentimiento", async ({
  page,
}) => {
  const d = await preparar(page);
  await page.goto("/cursos/curso-1/verificacion");
  await expect(page.getByText("Bloqueante", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Probar anuncio" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Probar comentario" }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Ejecutar checklist completo" })
    .click();
  await expect(
    page.getByRole("button", { name: "Ejecutar checklist completo" }),
  ).toBeEnabled({ timeout: 10_000 });
  expect(
    d.llamadas.filter((r) => r.method === "POST").map((r) => r.path),
  ).toEqual(["/api/cursos/curso-1/verificacion"]);
});
test("móvil: navegación modal, Escape y Pendientes sin desbordamiento", async ({
  page,
}) => {
  await preparar(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/cursos/curso-1/pendientes");
  await expect(
    page.getByRole("heading", { name: "Pendientes", exact: true }),
  ).toBeVisible();
  await sinDesborde(page);
  const boton = page.getByRole("button", { name: "Abrir navegación" });
  await boton.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(boton).toBeFocused();
  await boton.click();
  await page
    .getByRole("dialog")
    .getByRole("link", { name: "Tareas", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Tareas", exact: true }),
  ).toBeVisible();
  await sinDesborde(page);
});
for (const tema of ["institucional", "azul", "verde"]) {
  test(`accesibilidad y adaptación en tema ${tema}`, async ({
    page,
  }, testInfo) => {
    await preparar(page);
    await page.addInitScript(
      (t) => localStorage.setItem("pds2.apariencia", t),
      tema,
    );
    for (const ruta of [
      "/acceso",
      "/cursos",
      "/cursos/curso-1",
      "/cursos/curso-1/vinculacion",
      "/cursos/curso-1/personas",
      "/cursos/curso-1/tareas/tarea-1?vista=repositorios",
      "/perfil",
    ]) {
      await page.goto(ruta);
      await expect(page.locator("h1")).toBeVisible();
      await expect(page.locator(".loading")).toHaveCount(0);
      const resultados = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa"])
        .analyze();
      expect(
        resultados.violations.filter(
          (v) => v.impact === "critical" || v.impact === "serious",
        ),
        `${tema} ${ruta}`,
      ).toEqual([]);
      if (tema === "institucional") {
        await page.screenshot({
          path: testInfo.outputPath(`${ruta.replace(/[^a-z0-9]/gi, "-")}.png`),
          fullPage: true,
        });
      }
      for (const width of [1920, 1366, 1024, 390]) {
        await page.setViewportSize({ width, height: 844 });
        await sinDesborde(page);
      }
      await page.setViewportSize({ width: 1366, height: 768 });
    }
  });
}

test("una revisión CSV tardía no valida contenido modificado", async ({
  page,
}) => {
  await preparar(page);
  let liberar!: () => void;
  const espera = new Promise<void>((resolve) => {
    liberar = resolve;
  });
  await page.route("**/mapeo/importar-csv", async (route) => {
    await espera;
    await route.fallback();
  });
  await page.goto("/cursos/curso-1/personas");
  await page
    .getByText("Alternativa docente: importar cuentas por CSV", { exact: true })
    .click();
  await page
    .getByLabel("Contenido CSV")
    .fill("canvas_user_id,github_login\n2000,primera");
  const peticion = page.waitForRequest("**/mapeo/importar-csv");
  await page
    .getByRole("button", { name: "Previsualizar", exact: true })
    .click();
  await peticion;
  await page
    .getByLabel("Contenido CSV")
    .fill("canvas_user_id,github_login\n2000,segunda");
  liberar();
  await expect(
    page.getByRole("button", { name: "Previsualizar", exact: true }),
  ).toBeEnabled();
  await expect(
    page.getByRole("button", { name: "Aplicar filas revisadas" }),
  ).toBeDisabled();
  await expect(page.getByRole("caption")).toHaveCount(0);
});
test("error estructurado de activación conserva el borrador y explica el motivo", async ({
  page,
}) => {
  const d = await preparar(page);
  d.tarea.estado = "BORRADOR";
  await page.route("**/activar", (route) =>
    route.fulfill({
      status: 409,
      json: {
        detail: {
          motivo: "BASE_NO_LISTA",
          detalle: "La base cambió mientras revisabas la tarea.",
        },
      },
    }),
  );
  await page.goto("/cursos/curso-1/tareas/tarea-1");
  await page.getByRole("button", { name: "Activar tarea" }).click();
  await expect(
    page.getByText("La base cambió mientras revisabas la tarea."),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Activar tarea" }),
  ).toBeEnabled();
  expect(d.tarea.estado).toBe("BORRADOR");
});
test("apariencia funciona sin almacenamiento y el diseño admite ampliación al 200 %", async ({
  page,
}) => {
  await preparar(page);
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() {
        throw new DOMException("Bloqueado", "SecurityError");
      },
    });
  });
  await page.goto("/perfil");
  await page
    .getByRole("combobox", { name: "Apariencia", exact: true })
    .selectOption("azul");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "azul");
  // Ampliación CSS en Chromium: duplica texto, controles y medidas de layout.
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  await page.getByRole("button", { name: "Restablecer apariencia" }).click();
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme",
    "institucional",
  );
  await sinDesborde(page);
});
test("curso sin conexiones y consultas fallidas nunca figuran como completados", async ({
  page,
}) => {
  const d = await preparar(page);
  d.cursoVacio = true;
  d.cuentas.roster_sincronizado_en = null as unknown as string;
  await page.route("**/vinculacion/github", (route) =>
    route.fulfill({
      status: 503,
      json: { detail: "Temporalmente no disponible" },
    }),
  );
  await page.goto("/cursos/curso-1");
  await expect(
    page.getByRole("heading", { name: "Vincular Canvas", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("No pudimos consultar la organización."),
  ).toBeVisible();
  const paso = page
    .locator(".progress-list li")
    .filter({ hasText: "Vincular GitHub" });
  await expect(paso.getByText("Sin verificar", { exact: true })).toBeVisible();
});
