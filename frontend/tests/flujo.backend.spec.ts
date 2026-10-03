import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";

test("API real local: sesión opaca → crear curso → Canvas → GitHub App → espejo → tarea", async ({
  page,
  context,
}) => {
  const estado = JSON.parse(readFileSync(".backend-test-state.json", "utf8"));
  await context.addCookies([
    {
      name: "sesion",
      value: estado.sesion,
      domain: "127.0.0.1",
      path: "/",
      httpOnly: true,
      sameSite: "Lax",
    },
    {
      name: "csrf_token",
      value: estado.csrf,
      domain: "127.0.0.1",
      path: "/",
      sameSite: "Lax",
    },
  ]);
  const errores: string[] = [];
  page.on("pageerror", (error) => errores.push(error.message));
  // Único salto externo doblado: la instalación de GitHub devuelve al callback
  // real de nuestra API. El proveedor doble reconoce installation_id 8001.
  await page.route("https://github.com/**", async (route) => {
    const state = new URL(route.request().url()).searchParams.get("state");
    expect(state).toBeTruthy();
    await route.fulfill({
      status: 302,
      headers: {
        location: `http://127.0.0.1:4187/vinculacion/github/retorno?${new URLSearchParams({ state: state!, installation_id: "8001", setup_action: "install" })}`,
      },
      body: "",
    });
  });
  await page.goto("/cursos");
  await expect(
    page.getByRole("heading", { name: "Todavía no tienes cursos" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Crear mi primer curso" }).click();
  await page
    .getByLabel("Nombre del curso")
    .fill("Curso de revisión del frontend");
  await page.getByLabel("Código", { exact: true }).fill("ICC4201");
  await page.getByLabel("Período", { exact: true }).fill("2026-2");
  await page.getByLabel("Identificador corto").fill("revision-frontend");
  await page.getByRole("button", { name: "Crear y configurar" }).click();
  await expect(page).toHaveURL(/\/cursos\/[^/]+\/vinculacion/);
  const cursoId = page.url().split("/cursos/")[1].split("/")[0];
  await page.getByLabel("Mi token de acceso personal").fill("valido");
  await page.getByRole("checkbox").nth(0).check();
  await page.getByRole("checkbox").nth(1).check();
  await page.getByRole("button", { name: "Buscar mis cursos" }).click();
  await page.getByRole("button", { name: "Elegir este curso" }).click();
  await expect(
    page.getByText("Credencial válida", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Instalar en mi organización" })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "La organización org-valida quedó vinculada",
    { timeout: 20_000 },
  );
  await page.goto(`/cursos/${cursoId}/personas`);
  await expect(page.getByRole("heading", { name: "Personas" })).toBeVisible();
  await page.getByRole("button", { name: "Sincronizar con Canvas" }).click();
  await expect(page.getByRole("cell", { name: /Ana/ }).first()).toBeVisible({
    timeout: 40_000,
  });
  await page.goto(`/cursos/${cursoId}/tareas`);
  await page.getByRole("button", { name: "Crear tarea", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Crear tarea desde Canvas" }),
  ).toBeVisible();
  await page
    .getByLabel("Tarea de Canvas", { exact: true })
    .selectOption("9101");
  await page.getByRole("button", { name: "Crear borrador" }).click();
  await expect(page).toHaveURL(new RegExp(`/cursos/${cursoId}/tareas/[^/?]+`));
  await expect(page.locator("main h1")).toContainText("Ordenamiento");
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  await page.screenshot({
    path: "../docs/frontend/evidencias/api-real-tarea.png",
    fullPage: true,
  });
  expect(errores).toEqual([]);
});
