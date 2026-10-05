import { expect, test } from "@playwright/test";
import { preparar } from "./fixtures";
import { prepararFinal } from "./fixtures-final";

test("Perfil cierra una sesión y desvincula solo la identidad confirmada", async ({
  page,
}) => {
  await preparar(page);
  let sesiones = [
    {
      id: "propia",
      agente: "Este navegador",
      creada_en: "2026-10-01T10:00:00Z",
      es_la_actual: true,
    },
    {
      id: "otra",
      agente: "Otro navegador",
      creada_en: "2026-10-01T10:00:00Z",
      es_la_actual: false,
    },
  ];
  let identidades = [
    {
      id: "canvas-1",
      canvas_base_url: "https://canvas-ensayo.test",
      canvas_user_id: 100,
      verificada_en: "2026-10-01T10:00:00Z",
      cursos: [{ id: "curso-1", nombre: "Curso de ensayo", operativa: true }],
    },
  ];
  const borrados: string[] = [];
  await page.route("**/api/perfil/sesiones**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (route.request().method() === "DELETE") {
      sesiones = sesiones.filter((s) => !path.endsWith(`/${s.id}`));
      borrados.push(path);
      await route.fulfill({ json: { ok: true, es_la_actual: false } });
    } else await route.fulfill({ json: sesiones });
  });
  await page.route("**/api/perfil/identidades-canvas**", async (route) => {
    if (route.request().method() === "DELETE") {
      identidades = [];
      borrados.push(new URL(route.request().url()).pathname);
      await route.fulfill({ json: { credenciales_retiradas: 1 } });
    } else await route.fulfill({ json: identidades });
  });
  await page.goto("/perfil");
  await page
    .getByRole("button", { name: "Cerrar sesión", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Cerrar sesión", exact: true })
    .click();
  await expect(page.getByText("Otro navegador", { exact: true })).toHaveCount(
    0,
  );
  await expect(page.getByText("Este navegador", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Desvincular identidad", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText(
    "esperando una nueva credencial",
  );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Cancelar", exact: true })
    .click();
  expect(borrados).toEqual(["/api/perfil/sesiones/otra"]);
  await page
    .getByRole("button", { name: "Desvincular identidad", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Desvincular identidad", exact: true })
    .click();
  await expect(
    page.getByText("No tienes identidades de Canvas vinculadas."),
  ).toBeVisible();
  expect(borrados).toEqual([
    "/api/perfil/sesiones/otra",
    "/api/perfil/identidades-canvas/canvas-1",
  ]);
});

test("Atrás y Adelante conservan el borrador hasta confirmar la salida", async ({
  page,
}) => {
  await prepararFinal(page);
  await page.goto("/cursos/curso-1/correccion/entrega-1/sujeto-0");
  await page.getByRole("button", { name: "Siguiente", exact: true }).click();
  await expect(page).toHaveURL(/sujeto-1$/);
  const nota = page.getByLabel("Nota (sobre 100)", { exact: true });
  await nota.fill("91");
  await page.evaluate(() => history.back());
  await expect(page.getByRole("dialog")).toContainText("Cambios sin guardar");
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(page).toHaveURL(/sujeto-1$/);
  await expect(nota).toHaveValue("91");
  await page.evaluate(() => history.back());
  await page
    .getByRole("button", { name: "Descartar y continuar", exact: true })
    .click();
  await expect(page).toHaveURL(/sujeto-0$/);
  await nota.fill("92");
  await page.evaluate(() => history.forward());
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(page).toHaveURL(/sujeto-0$/);
  await expect(nota).toHaveValue("92");
  await page
    .getByRole("button", { name: "Guardar borrador", exact: true })
    .click();
  await expect(
    page.getByText("Borrador guardado. No se publicó ninguna nota en Canvas."),
  ).toBeVisible();
  await page.evaluate(() => history.forward());
  await expect(page).toHaveURL(/sujeto-1$/);
  await expect(page.getByRole("dialog")).toHaveCount(0);
});
