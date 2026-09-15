import { expect, test } from "@playwright/test";
import { preparar } from "./fixtures";

test("espera HTML de arranque y errores temporales antes del POST a Google", async ({
  page,
}) => {
  await preparar(page);
  let consultas = 0;
  let envios = 0;
  await page.route("**/api/salud", (route) => {
    consultas++;
    if (consultas === 1)
      return route.fulfill({
        status: 200,
        contentType: "text/html; charset=utf-8",
        body: "Render waking up",
      });
    if (consultas === 2)
      return route.fulfill({ status: 503, body: "Iniciando" });
    return route.fulfill({ json: { estado: "ok", servicio: "api" } });
  });
  await page.route("**/auth/google/inicio", (route) => {
    expect(route.request().method()).toBe("POST");
    expect(consultas).toBe(3);
    envios++;
    return route.fulfill({
      contentType: "text/html; charset=utf-8",
      body: "Google listo",
    });
  });
  await page.goto("/acceso");
  await page.getByRole("button", { name: "Entrar con Google" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Continuaremos automáticamente",
  );
  await expect(
    page.getByRole("button", { name: "Preparando acceso…" }),
  ).toBeDisabled();
  expect(envios).toBe(0);
  await expect(page.getByText("Google listo")).toBeVisible();
  expect(envios).toBe(1);
});

test("la espera conserva el token de invitación en el formulario POST", async ({
  page,
}) => {
  const datos = await preparar(page);
  datos.sesion = false;
  let cuerpo = "";
  await page.route("**/auth/google/inicio", (route) => {
    cuerpo = route.request().postData() ?? "";
    return route.fulfill({
      contentType: "text/html; charset=utf-8",
      body: "Continuación de invitación",
    });
  });
  await page.goto("/invitaciones/token-nominal");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Aceptar con Google" }).click();
  await expect(page.getByText("Continuación de invitación")).toBeVisible();
  expect(new URLSearchParams(cuerpo).get("invitacion_token")).toBe(
    "token-nominal",
  );
});

test("confirma por POST después de esperar al backend", async ({ page }) => {
  await preparar(page);
  let cuerpo = "";
  await page.route("**/auth/confirmar", (route) => {
    expect(route.request().method()).toBe("POST");
    cuerpo = route.request().postData() ?? "";
    return route.fulfill({
      contentType: "text/html; charset=utf-8",
      body: "Acceso confirmado",
    });
  });
  await page.goto("/confirmar?token=confirmacion-firmada");
  await page.getByRole("button", { name: "Confirmar y entrar" }).click();
  await expect(page.getByText("Acceso confirmado")).toBeVisible();
  expect(new URLSearchParams(cuerpo).get("token")).toBe("confirmacion-firmada");
});

test("si el servicio no responde permite reintentar sin navegar al error", async ({
  page,
}) => {
  await preparar(page);
  await page.clock.install();
  await page.route("**/api/salud", (route) => route.fulfill({ status: 503 }));
  await page.goto("/acceso");
  await page.getByRole("button", { name: "Entrar con Google" }).click();
  await page.clock.runFor(123_000);
  await expect(
    page.getByText("No pudimos conectar con el servicio.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Entrar con Google" }),
  ).toBeEnabled();
  expect(new URL(page.url()).pathname).toBe("/acceso");
});

test("perfil muestra los cursos bloqueantes si el cierre es rechazado al confirmar", async ({
  page,
}) => {
  await preparar(page);
  await page.route("**/api/perfil", (route) =>
    route.request().method() === "DELETE"
      ? route.fulfill({
          status: 409,
          json: {
            detail: {
              motivo: "UNICA_PROFESORA_ACTIVA",
              cursos: [{ curso_id: "curso-1", nombre: "Curso protegido" }],
            },
          },
        })
      : route.fallback(),
  );
  await page.goto("/perfil");
  await page
    .getByRole("button", { name: "Cerrar mi cuenta", exact: true })
    .click();
  const dialogo = page.getByRole("dialog");
  await dialogo.getByRole("textbox").fill("CERRAR");
  await dialogo
    .getByRole("button", { name: "Cerrar mi cuenta", exact: true })
    .click();
  await expect(
    page.getByRole("link", { name: "Curso protegido" }),
  ).toHaveAttribute("href", "/cursos/curso-1/equipo");
  expect(new URL(page.url()).pathname).toBe("/perfil");
});

test("invitaciones existentes sobreviven a recarga y reenvío reemplaza el enlace", async ({
  page,
}) => {
  await preparar(page);
  let i = {
    id: "i1",
    email: "ayudante@gmail.com",
    rol: "AYUDANTE",
    estado: "PENDIENTE",
    expira_en: "2026-12-01T12:00:00Z",
    enlace: "https://ejemplo.test/invitaciones/viejo",
    correo_estado: "BLOQUEADO",
    correo_motivo: "COMUNICACIONES_PAUSADAS",
    reenvios_restantes: 3,
  };
  await page.route("**/equipo/invitaciones", (route) =>
    route.fulfill({ json: [i] }),
  );
  await page.route("**/equipo/invitaciones/*/reenviar", (route) => {
    expect(route.request().headers()["x-csrf-token"]).toBe("csrf-prueba");
    i = {
      ...i,
      id: "i2",
      enlace: "https://ejemplo.test/invitaciones/nuevo",
      reenvios_restantes: 2,
    };
    return route.fulfill({ json: i });
  });
  await page.goto("/cursos/curso-1/equipo");
  await expect(
    page.getByLabel("Enlace de invitación para ayudante@gmail.com"),
  ).toHaveValue(i.enlace);
  await page.reload();
  await expect(
    page.getByText("El correo está pausado.", { exact: false }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Reenviar invitación", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Reenviar", exact: true })
    .click();
  await expect(
    page.getByLabel("Enlace de invitación para ayudante@gmail.com"),
  ).toHaveValue("https://ejemplo.test/invitaciones/nuevo");
});
