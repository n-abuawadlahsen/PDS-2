import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { curso, preparar } from "./fixtures";

const base = "/cursos/curso-1";
test("Crear curso conserva la respuesta confirmada si falla refrescar la lista", async ({
  page,
}) => {
  await preparar(page);
  let creado = false;
  await page.route("**/api/cursos", (route) => {
    if (route.request().method() === "POST") {
      creado = true;
      return route.fulfill({ json: curso });
    }
    return creado
      ? route.fulfill({
          status: 503,
          json: { detail: "Actualización temporalmente no disponible" },
        })
      : route.fulfill({ json: [] });
  });
  await page.goto("/cursos");
  await page.getByRole("button", { name: "Crear mi primer curso" }).click();
  await page.getByLabel("Nombre del curso").fill(curso.nombre);
  await page.getByLabel("Código", { exact: true }).fill(curso.codigo);
  await page.getByLabel("Período", { exact: true }).fill(curso.periodo);
  await page.getByLabel("Identificador corto").fill(curso.slug);
  await page.getByRole("button", { name: "Crear y configurar" }).click();
  await expect(
    page.getByRole("heading", { name: "Configuración del curso" }),
  ).toBeVisible();
  await expect(
    page.getByText("No pudimos actualizar tus cursos.", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Actualizar mis cursos" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Curso no disponible" }),
  ).toHaveCount(0);
});
test("Cursos: buscar, filtrar y recorrer la navegación sin desborde", async ({
  page,
}) => {
  await preparar(page);
  const errores: string[] = [];
  page.on("pageerror", (error) => errores.push(error.message));
  await page.route("**/api/cursos", (route) =>
    route.fulfill({
      json: [
        curso,
        {
          ...curso,
          id: "curso-2",
          codigo: "ICC4203",
          nombre: "Aplicaciones móviles",
          estado: "VINCULANDO",
        },
        {
          ...curso,
          id: "curso-3",
          codigo: "ICC4204",
          nombre: "Introducción a la ingeniería de software",
        },
        {
          ...curso,
          id: "curso-4",
          codigo: "ICC0021",
          nombre: "Introducción al desarrollo de videojuegos",
        },
        {
          ...curso,
          id: "curso-5",
          codigo: "ICC3101",
          nombre: "Estructuras de datos y algoritmos",
        },
        {
          ...curso,
          id: "curso-6",
          codigo: "ICC2102",
          nombre: "Programación avanzada",
          estado: "ARCHIVADO",
        },
      ],
    }),
  );
  await page.goto("/cursos");
  await expect(page.locator(".course-card")).toHaveCount(6);
  await page.getByLabel("Buscar cursos").fill("móviles");
  await expect(page.locator(".course-card")).toHaveCount(1);
  await page.getByLabel("Estado del curso").selectOption("ACTIVO");
  await expect(
    page.getByRole("heading", { name: "No hay cursos que coincidan" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Limpiar filtros" }).click();
  for (const [nombre, width, height] of [
    ["escritorio", 1440, 900],
    ["portatil", 1366, 768],
    ["tablet", 768, 1024],
    ["movil", 390, 844],
    ["movil-360", 360, 800],
  ] as const) {
    await page.setViewportSize({ width, height });
    await expect(page.locator(".course-card")).toHaveCount(6);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: `../docs/frontend/evidencias/cursos-${nombre}.png`,
      fullPage: true,
    });
  }
  const a11y = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
    .analyze();
  expect(a11y.violations).toEqual([]);
  expect(errores).toEqual([]);
});

test("Acceso directo respeta capacidades y permisos, y retiene destino al expirar", async ({
  page,
}) => {
  const datos = await preparar(page);
  await page.goto(`${base}/correccion`);
  await expect(
    page.getByRole("heading", { name: "Área no disponible" }),
  ).toBeVisible();
  expect(
    datos.llamadas.filter((r) => r.path.endsWith("/correccion")),
  ).toHaveLength(0);
  datos.permisos = ["curso.ver", "correccion.corregir"];
  await page.goto(`${base}/ajustes`);
  await expect(
    page.getByRole("heading", { name: "Permiso insuficiente" }),
  ).toBeVisible();
  datos.sesion = false;
  await page.goto(`${base}/tareas?estado=ACTIVA`);
  await page.getByRole("link", { name: "Entrar con Google" }).click();
  await expect(page.locator('input[name="destino"]')).toHaveValue(
    `${base}/tareas?estado=ACTIVA`,
  );
});

test("Capturas del curso: vinculación, personas, pendientes y tareas", async ({
  page,
}) => {
  await preparar(page);
  for (const [nombre, ruta] of [
    ["vinculacion", "/vinculacion"],
    ["personas", "/personas"],
    ["pendientes", "/pendientes"],
    ["tareas", "/tareas"],
    ["repositorios", "/tareas/tarea-1?vista=repositorios"],
  ]) {
    await page.goto(`${base}${ruta}`);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator(".loading")).toHaveCount(0);
    for (const [tamano, width, height] of [
      ["escritorio", 1440, 900],
      ["movil", 390, 844],
    ] as const) {
      await page.setViewportSize({ width, height });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        nombre,
      ).toBeTruthy();
      await page.screenshot({
        path: `../docs/frontend/evidencias/${nombre}-${tamano}.png`,
        fullPage: true,
      });
    }
  }
});
