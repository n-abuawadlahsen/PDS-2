import { expect, test } from "@playwright/test";
import { preparar } from "./fixtures";

// Dobles locales de los contratos P1–P6; no llaman a Google, Canvas o GitHub.
test("el acceso conserva solo destinos internos permitidos", async ({
  page,
}) => {
  await preparar(page);
  const destino = "/cursos/curso-1/personas?estado=SIN_DATO";
  await page.goto(`/acceso?destino=${encodeURIComponent(destino)}`);
  await expect(page.locator('input[name="destino"]')).toHaveValue(destino);
  await page.goto("/acceso?destino=https%3A%2F%2Fejemplo.test");
  await expect(page.locator('input[name="destino"]')).toHaveValue("/cursos");
  await page.goto(
    "/acceso?destino=%2Fcursos%5C%5Cejemplo.test&motivo=HD_PRESENTE",
  );
  await expect(page.locator('input[name="destino"]')).toHaveValue("/cursos");
  await expect(
    page.getByText("Cuenta de dominio gestionado", { exact: true }),
  ).toBeVisible();
});

test("equipo ofrece cinco permisos, conserva el último profesor y envía la selección", async ({
  page,
}) => {
  await preparar(page);
  let invitacion: { email: string; rol: string; permisos: string[] } | null =
    null;
  await page.route(
    "**/api/cursos/curso-1/equipo/invitaciones",
    async (route) => {
      if (route.request().method() === "POST") {
        invitacion = route.request().postDataJSON();
        return route.fulfill({ json: { id: "invitacion-nueva" } });
      }
      return route.fulfill({ json: [] });
    },
  );
  await page.goto("/cursos/curso-1/equipo");
  await expect(
    page.getByRole("button", { name: "Retirar", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Editar acceso" }).click();
  await expect(
    page
      .getByRole("combobox", { name: "Rol", exact: true })
      .locator('option[value="AYUDANTE"]'),
  ).toHaveAttribute("disabled", "");
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await page.getByRole("button", { name: "Incorporar integrante" }).click();
  const permisos = page.getByRole("group", { name: "Permisos del ayudante" });
  await expect(permisos.getByRole("checkbox")).toHaveCount(5);
  await expect(
    permisos.getByText("Siempre incluidos:", { exact: false }),
  ).toContainText("Corregir lo asignado");
  await expect(
    permisos.getByText("Administrar el equipo: exclusivo", { exact: false }),
  ).toBeVisible();
  await page
    .getByLabel("Correo de Google (Gmail o @miuandes.cl)")
    .fill("ayudante.ensayo@gmail.com");
  await permisos
    .getByRole("checkbox", { name: "Repartir correcciones", exact: false })
    .check();
  await permisos
    .getByRole("checkbox", { name: "Publicar nota", exact: false })
    .check();
  await page.getByRole("button", { name: "Registrar invitación" }).click();
  await expect(
    page.getByText("Invitación creada.", { exact: false }),
  ).toBeVisible();
  expect(invitacion).toMatchObject({
    rol: "AYUDANTE",
    permisos: ["mapeo.editar", "correccion.asignar", "nota.publicar"],
  });
});

test("el historial del equipo se consulta bajo demanda y es legible para ayudantes", async ({
  page,
}) => {
  const datos = await preparar(page);
  datos.permisos = ["curso.ver", "correccion.corregir"];
  let consultas = 0;
  await page.route("**/api/cursos/curso-1/equipo/historial", async (route) => {
    consultas++;
    return route.fulfill({
      json: [
        {
          accion: "PERMISOS_CAMBIADOS",
          entidad_id: "m-1",
          actor_usuario_id: "profesor-1",
          creado_en: "2026-10-01T13:00:00Z",
          antes: { permisos: [] },
          despues: { permisos: ["nota.publicar"] },
        },
      ],
    });
  });
  await page.goto("/cursos/curso-1/equipo");
  await expect(
    page.getByRole("heading", { name: "Equipo docente" }),
  ).toBeVisible();
  expect(consultas).toBe(0);
  await expect(
    page.getByRole("button", { name: "Incorporar integrante" }),
  ).toHaveCount(0);
  await page.getByText("Historial del equipo", { exact: true }).click();
  await expect(
    page.getByText("Permisos cambiados", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Permisos: Publicar nota", { exact: true }),
  ).toBeVisible();
  expect(consultas).toBe(1);
});

test("pendientes conduce a la persona correcta y el mapeo actualiza el espejo", async ({
  page,
}) => {
  const datos = await preparar(page);
  await page.route(
    "**/api/cursos/curso-1/personas/e-0/mapeo",
    async (route) => {
      expect(route.request().postDataJSON()).toEqual({
        login: "cuenta-ensayo",
      });
      datos.cuentas.estudiantes[0].mapeo = {
        estado: "VIGENTE",
        cuenta_login: "cuenta-ensayo",
        motivo_invalidacion: null,
      };
      return route.fulfill({ json: datos.cuentas.estudiantes[0].mapeo });
    },
  );
  await page.goto("/cursos/curso-1/pendientes");
  await page
    .getByRole("link", { name: "Revisar y asociar cuenta en Personas" })
    .click();
  await expect(page).toHaveURL(/estudiante=e-0/);
  await expect(
    page
      .getByRole("region", { name: "Estudiantes del curso" })
      .getByRole("row"),
  ).toHaveCount(2);
  await page.getByText("Asociar cuenta", { exact: true }).click();
  await page
    .getByLabel("Cuenta de GitHub de Estudiante sin cuenta")
    .fill("cuenta-ensayo");
  await page.getByRole("button", { name: "Validar y guardar" }).click();
  await expect(page.getByText("@cuenta-ensayo", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Ver todas las personas" }).click();
  await page.getByLabel("Buscar estudiante").fill("Estudiante 22");
  await page.reload();
  await expect(page.getByLabel("Buscar estudiante")).toHaveValue(
    "Estudiante 22",
  );
  await expect(
    page.getByRole("cell", { name: "Estudiante 22", exact: false }),
  ).toBeVisible();
});

test("la creación de registro con 202 no anuncia publicación y confirma después", async ({
  page,
}) => {
  const datos = await preparar(page);
  datos.cuentas.registro_estado = "NO_CREADA";
  await page.route("**/api/cursos/curso-1/registro-github", (route) =>
    route.fulfill({
      status: 202,
      json: { detail: "Canvas no respondió; se reintenta" },
    }),
  );
  await page.goto("/cursos/curso-1/personas");
  await page
    .getByRole("button", { name: "Crear tarea de registro en Canvas" })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Publicar registro", exact: true })
    .click();
  await expect(
    page.getByText("La creación quedó pendiente en Canvas.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByText("La tarea de registro está disponible en Canvas.", {
      exact: true,
    }),
  ).toHaveCount(0);
  datos.cuentas.registro_estado = "ABIERTA";
  await page.getByRole("button", { name: "Actualizar vista" }).click();
  await expect(
    page.getByText("La tarea de registro está disponible en Canvas.", {
      exact: true,
    }),
  ).toBeVisible();
});

test("checklist conserva ejecución tras recargar y las pruebas de escritura exigen consentimiento", async ({
  page,
}) => {
  const datos = await preparar(page);
  datos.cursoVacio = true;
  let consultas = 0;
  await page.route("**/api/cursos/curso-1/verificacion/run-1", (route) => {
    consultas++;
    return route.fulfill({
      json:
        consultas < 2
          ? []
          : Array.from({ length: 19 }, (_, i) => ({
              item: String(i + 1),
              resultado: "CORRECTO",
              detalle: {},
              ejecutada_en: "2026-10-01T13:00:00Z",
            })),
    });
  });
  await page.goto("/cursos/curso-1/verificacion");
  await expect(
    page.getByRole("button", { name: "Probar anuncio", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Probar comentario", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Ejecutar checklist completo" })
    .click();
  await expect(page).toHaveURL(/ejecucion=run-1/);
  await expect(page.getByText("En comprobación", { exact: true })).toHaveCount(
    19,
  );
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Ejecutar checklist completo" }),
  ).toBeEnabled();
  await expect(page.getByText("Correcto", { exact: true })).toHaveCount(19);
  await expect(page).not.toHaveURL(/ejecucion=/);
  expect(consultas).toBe(2);
});

test("un ayudante consulta recordatorios pero necesita permiso para cambiarlos", async ({
  page,
}) => {
  const datos = await preparar(page);
  datos.permisos = ["curso.ver", "correccion.corregir"];
  await page.route("**/api/capacidades", (route) =>
    route.fulfill({
      json: { perfil: "completo", banderas: ["comunicaciones_automaticas"] },
    }),
  );
  await page.route(
    "**/api/cursos/curso-1/comunicaciones-curso/recordatorio-mapeo",
    (route) => {
      expect(route.request().method()).toBe("GET");
      return route.fulfill({
        json: {
          evento: "recordatorio_mapeo",
          titulo: "Registro GitHub",
          activa: true,
          por_defecto: true,
          advertencia_al_apagar: null,
          destinatarios_hoy: 2,
          vista_previa_asunto: "Registra tu cuenta",
          vista_previa_cuerpo: "Declara tu cuenta en Canvas.",
          vista_previa_con_ejemplo: false,
        },
      });
    },
  );
  await page.goto("/cursos/curso-1/personas");
  await expect(
    page.getByRole("checkbox", { name: "Recordar por Canvas", exact: false }),
  ).toBeDisabled();
  await expect(
    page.getByText("Necesitas el permiso Enviar comunicaciones", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "Los correos e identificadores personales están enmascarados",
      { exact: false },
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Sincronizar con Canvas" }),
  ).toHaveCount(0);
});
