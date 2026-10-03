import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { prepararOperacion } from "./fixtures-operacion";
import { prepararFinal } from "./fixtures-final";

test("Revisión visual de tablero, entregas y timeline en portátil y móvil", async ({
  page,
}) => {
  await prepararOperacion(page);
  const errores: string[] = [];
  page.on("pageerror", (error) => errores.push(error.message));
  for (const [nombre, ruta, titulo] of [
    ["tablero", "/cursos/curso-1/tareas/tarea-1", "Tablero"],
    [
      "entregas",
      "/cursos/curso-1/tareas/tarea-1/entregas",
      "Entregas y versiones",
    ],
    [
      "timeline",
      "/cursos/curso-1/tareas/tarea-1/repos/r-0",
      "Actividad de Grupo 01",
    ],
  ]) {
    await page.goto(ruta);
    await expect(
      page.getByRole("heading", { name: titulo, exact: true }),
    ).toBeVisible();
    await expect(page.locator(".loading")).toHaveCount(0);
    for (const [tamano, width, height] of [
      ["escritorio", 1440, 900],
      ["movil", 390, 844],
    ] as const) {
      await page.setViewportSize({ width, height });
      await page.evaluate(() => scrollTo(0, 0));
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        nombre,
      ).toBeTruthy();
      await page.screenshot({
        path: `../docs/frontend/evidencias/${nombre}-${tamano}.png`,
      });
      const resultado = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
        .analyze();
      expect(resultado.violations, `${nombre} ${tamano}`).toEqual([]);
    }
    if (nombre === "tablero") {
      await page.locator(".operacion-barra").first().focus();
      await page.keyboard.press("ArrowRight");
      await expect(page.getByRole("tooltip")).toContainText("18-09-2026");
      await page
        .getByRole("heading", { name: "Actividad en el tiempo" })
        .scrollIntoViewIfNeeded();
      await page.screenshot({
        path: "../docs/frontend/evidencias/tablero-actividad-movil.png",
      });
      await page.setViewportSize({ width: 1440, height: 900 });
      await page
        .getByRole("heading", { name: "Actividad en el tiempo" })
        .scrollIntoViewIfNeeded();
      await page.screenshot({
        path: "../docs/frontend/evidencias/tablero-actividad.png",
      });
    }
  }
  expect(errores).toEqual([]);
});

test("Corrección, informes y comunicaciones accesibles en escritorio y móvil", async ({
  page,
}) => {
  await prepararFinal(page);
  const errores: string[] = [];
  page.on("pageerror", (error) => errores.push(error.message));
  for (const [nombre, ruta, titulo] of [
    [
      "correccion",
      "/cursos/curso-1/correccion/entrega-1/sujeto-0",
      "Equipo 01",
    ],
    ["matriz-correccion", "/cursos/curso-1/correccion", "Corrección"],
    ["informes", "/cursos/curso-1/informes", "Informe docente diario"],
    ["comunicaciones", "/cursos/curso-1/comunicaciones", "Comunicaciones"],
  ]) {
    await page.goto(ruta);
    await expect(
      page.getByRole("heading", { name: titulo, exact: true }),
    ).toBeVisible();
    await expect(page.locator(".loading")).toHaveCount(0);
    for (const [tamano, width, height] of [
      ["escritorio", 1440, 900],
      ["movil", 390, 844],
    ] as const) {
      await page.setViewportSize({ width, height });
      await page.evaluate(() => scrollTo(0, 0));
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        nombre,
      ).toBeTruthy();
      await page.screenshot({
        path: `../docs/frontend/evidencias/${nombre}-${tamano}.png`,
      });
      const resultado = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
        .analyze();
      expect(resultado.violations, `${nombre} ${tamano}`).toEqual([]);
    }
  }
  expect(errores).toEqual([]);
});
