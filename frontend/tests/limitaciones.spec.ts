import { expect, test } from "@playwright/test";
import { curso, preparar } from "./fixtures";
import { prepararFinal } from "./fixtures-final";
import type { MatrizCorreccion } from "../src/lib/api";

const ruta = "/cursos/curso-1/correccion/entrega-1/sujeto-0";

test("Perfil cierra solo la sesión elegida y confirma la desvinculación Canvas", async ({
  page,
}) => {
  await preparar(page);
  let sesiones = [
    {
      id: "s-1",
      es_la_actual: true,
      creada_en: "2026-10-06T12:00:00Z",
      agente: "Navegador actual",
    },
    {
      id: "s-2",
      es_la_actual: false,
      creada_en: "2026-10-05T12:00:00Z",
      agente: "Otro navegador",
    },
  ];
  let identidades = [
    {
      id: "canvas-1",
      canvas_base_url: "https://canvas.example.test",
      canvas_user_id: 42,
      verificada_en: "2026-10-06T12:00:00Z",
      cursos: [{ id: "curso-1", nombre: "Curso de prueba", operativa: true }],
    },
  ];
  let cierres = 0,
    retiros = 0;
  await page.route("**/api/perfil/sesiones", (r) =>
    r.fulfill({ json: sesiones }),
  );
  await page.route("**/api/perfil/sesiones/s-2", (r) => {
    cierres++;
    sesiones = sesiones.filter((s) => s.id !== "s-2");
    return r.fulfill({ json: { ok: true, es_la_actual: false } });
  });
  await page.route("**/api/perfil/identidades-canvas", (r) =>
    r.fulfill({ json: identidades }),
  );
  await page.route("**/api/perfil/identidades-canvas/canvas-1", (r) => {
    retiros++;
    identidades = [];
    return r.fulfill({ json: { ok: true, credenciales_retiradas: 1 } });
  });
  await page.goto("/perfil");
  await expect(
    page.getByText("https://canvas.example.test", { exact: true }),
  ).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  await page.screenshot({
    path: "../docs/frontend/evidencias/limitaciones-perfil-escritorio.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  await page.screenshot({
    path: "../docs/frontend/evidencias/limitaciones-perfil-movil.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  await page.setViewportSize({ width: 1366, height: 768 });
  await page
    .getByRole("button", { name: "Cerrar otra sesión", exact: true })
    .click();
  expect(cierres).toBe(0);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Cerrar sesión", exact: true })
    .click();
  await expect(page.getByText("Otro navegador", { exact: true })).toHaveCount(
    0,
  );
  expect(cierres).toBe(1);
  await expect(
    page.getByRole("button", { name: "Cerrar esta sesión", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Desvincular identidad", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Cancelar", exact: true })
    .click();
  expect(retiros).toBe(0);
  await page
    .getByRole("button", { name: "Desvincular identidad", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText(
    "se retirarán tus credenciales de 1 curso",
  );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Desvincular identidad", exact: true })
    .click();
  await expect(
    page.getByText("No tienes identidades de Canvas vinculadas."),
  ).toBeVisible();
  expect(retiros).toBe(1);
});

test("Atrás y Adelante protegen el borrador y cancelar conserva la nota", async ({
  page,
}) => {
  await prepararFinal(page);
  await page.goto(ruta);
  await page.getByRole("button", { name: "Siguiente", exact: true }).click();
  await expect(page).toHaveURL(/sujeto-1$/);
  await page.getByRole("button", { name: "Siguiente", exact: true }).click();
  await expect(page).toHaveURL(/sujeto-2$/);
  await page.getByLabel("Nota (sobre 100)", { exact: true }).fill("91");
  await page.evaluate(() => history.back());
  await expect(
    page.getByRole("dialog", { name: "Cambios sin guardar" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(
    page.getByLabel("Nota (sobre 100)", { exact: true }),
  ).toHaveValue("91");
  await expect(page).toHaveURL(/sujeto-2$/);
  await page.evaluate(() => history.back());
  await page
    .getByRole("button", { name: "Descartar y continuar", exact: true })
    .click();
  await expect(page).toHaveURL(/sujeto-1$/);
  await expect(
    page.getByLabel("Nota (sobre 100)", { exact: true }),
  ).not.toHaveValue("91");
  await page.getByLabel("Nota (sobre 100)", { exact: true }).fill("92");
  await page.evaluate(() => history.forward());
  await expect(
    page.getByRole("dialog", { name: "Cambios sin guardar" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(
    page.getByLabel("Nota (sobre 100)", { exact: true }),
  ).toHaveValue("92");
  await page
    .getByRole("button", { name: "Guardar borrador", exact: true })
    .click();
  await expect(
    page.getByText("Borrador guardado. No se publicó ninguna nota en Canvas."),
  ).toBeVisible();
  await page.evaluate(() => history.forward());
  await expect(page).toHaveURL(/sujeto-2$/);
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("Ajustes guarda nombre, zona y umbrales y conserva el formulario ante error", async ({
  page,
}) => {
  await preparar(page);
  let datos: unknown;
  let fallo = true;
  let confirmado: Record<string, unknown> = {};
  await page.route("**/api/cursos", (r) =>
    r.fulfill({ json: [{ ...curso, ...confirmado }] }),
  );
  await page.route("**/api/cursos/curso-1", (r) => {
    datos = r.request().postDataJSON();
    if (!fallo) confirmado = datos as Record<string, unknown>;
    return r.fulfill({
      status: fallo ? 422 : 200,
      json: fallo
        ? {
            detail: [
              {
                loc: ["body", "zona_horaria"],
                msg: "Zona horaria no reconocida",
              },
            ],
          }
        : { ok: true },
    });
  });
  await page.goto("/cursos/curso-1/ajustes");
  await page
    .getByLabel("Nombre del curso", { exact: true })
    .fill("Curso actualizado");
  await page.getByRole("textbox", { name: /^Zona horaria/ }).fill("UTC");
  await page.getByLabel("Días sin actividad", { exact: true }).fill("12");
  await page
    .getByRole("button", { name: "Guardar ajustes", exact: true })
    .click();
  await expect(
    page
      .locator(".field-error")
      .getByText("Zona horaria no reconocida", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByLabel("Nombre del curso", { exact: true }),
  ).toHaveValue("Curso actualizado");
  fallo = false;
  await page
    .getByRole("button", { name: "Guardar ajustes", exact: true })
    .click();
  await expect(
    page.getByText("Ajustes guardados.", { exact: false }),
  ).toBeVisible();
  await page.setViewportSize({ width: 360, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  await page.screenshot({
    path: "../docs/frontend/evidencias/limitaciones-ajustes-movil.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  expect(datos).toEqual({
    nombre: "Curso actualizado",
    zona_horaria: "UTC",
    umbral_dias_sin_actividad: 12,
    umbral_desbalance_pct: 70,
  });
});

test("Renovar Canvas habilita el curso propio y mantiene bloqueado otro con igual nombre", async ({
  page,
}) => {
  await preparar(page);
  await page.route("**/canvas/cursos-disponibles", (r) =>
    r.fulfill({
      json: [
        {
          canvas_course_id: 123,
          nombre: "Curso idéntico",
          codigo: "A",
          termino: null,
          total_estudiantes: 0,
          ya_vinculado_a: "Curso idéntico",
          ya_vinculado_curso_id: "curso-1",
        },
        {
          canvas_course_id: 124,
          nombre: "Curso idéntico",
          codigo: "B",
          termino: null,
          total_estudiantes: 0,
          ya_vinculado_a: "Curso idéntico",
          ya_vinculado_curso_id: "curso-ajeno",
        },
      ],
    }),
  );
  await page.goto("/cursos/curso-1/vinculacion");
  await page
    .getByLabel("Mi token de acceso personal", { exact: true })
    .fill("credencial-de-ensayo");
  await page.getByRole("checkbox").nth(0).check();
  await page.getByRole("checkbox").nth(1).check();
  await page
    .getByRole("button", { name: "Buscar mis cursos", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Renovar mi credencial", exact: true }),
  ).toBeEnabled();
  await expect(
    page.getByRole("button", { name: "Elegir este curso", exact: true }),
  ).toBeDisabled();
});

test("Checklist muestra el fallo del trabajo y permite volver a verificar", async ({
  page,
}) => {
  await preparar(page);
  await page.route("**/verificacion/run-1", (r) => r.fulfill({ json: [] }));
  await page.route("**/verificacion/run-1/estado", (r) =>
    r.fulfill({
      json: {
        id: "job-fallido",
        estado: "REQUIERE_ATENCION",
        intentos: 1,
        max_intentos: 1,
        proximo_intento_en: null,
        terminado_en: null,
      },
    }),
  );
  await page.goto("/cursos/curso-1/verificacion?ejecucion=run-1");
  await expect(
    page.getByText("La verificación no pudo completarse.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Ejecutar checklist completo",
      exact: true,
    }),
  ).toBeEnabled();
});

test("Borrador carga la fecha y autoría auditadas, y el comentario guardado", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  const borrador = estado.pantalla("sujeto-0").borrador!;
  borrador.guardado_en = "2026-10-06T12:00:00Z";
  borrador.autor = {
    usuario_id: "autor-1",
    nombre: "Ayudante de ensayo",
    rol: "AYUDANTE",
    es_via_compartida: false,
  };
  borrador.comentario_renderizado =
    "Revisión de ensayo\n\nCorregido por Ayudante de ensayo (ayudante).";
  await page.goto(ruta);
  await expect(
    page.getByText("Último borrador de Ayudante de ensayo (ayudante).", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("status").filter({ hasText: "Borrador guardado el" }),
  ).toContainText("06-10-2026");
  await page
    .getByText("Comentario guardado que se publicará en Canvas", {
      exact: true,
    })
    .click();
  await expect(page.locator(".comentario-canvas")).toContainText(
    "Ayudante de ensayo (ayudante)",
  );
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  await page.screenshot({
    path: "../docs/frontend/evidencias/limitaciones-correccion-escritorio.png",
    fullPage: true,
  });
});

test("Editar pesos guarda en la API y exige una nueva previsualización", async ({
  page,
}) => {
  await prepararFinal(page);
  let peso = 1;
  let aplicaciones = 0;
  await page.route("**/correccion/correctores", (r) =>
    r.fulfill({
      json: [
        {
          membresia_id: "m-1",
          nombre: "Docente de prueba",
          rol: "PROFESOR",
          peso: 0,
          sin_github: false,
        },
        {
          membresia_id: "m-2",
          nombre: "Ayudante de prueba",
          rol: "AYUDANTE",
          peso,
          sin_github: false,
        },
      ],
    }),
  );
  await page.route("**/correccion/correctores/m-2/peso", (r) => {
    peso = r.request().postDataJSON().peso;
    return r.fulfill({ json: { membresia_id: "m-2", peso } });
  });
  await page.route("**/reparto/aplicar", (r) => {
    aplicaciones++;
    return r.fulfill({ json: { cambios: 1 } });
  });
  await page.goto("/cursos/curso-1/correccion?pestana=repartir");
  await page.getByText("Pesos del reparto equitativo", { exact: true }).click();
  const campo = page.getByRole("spinbutton", {
    name: "Peso de Ayudante de prueba",
    exact: true,
  });
  await campo.fill("5");
  await page
    .locator("form")
    .filter({ has: campo })
    .getByRole("button", { name: "Guardar peso", exact: true })
    .click();
  await expect(campo).toHaveValue("5");
  await expect(
    page.getByText("Ayudante de prueba · peso 5", { exact: false }),
  ).toBeVisible();
  expect(peso).toBe(5);
  expect(aplicaciones).toBe(0);
});

test("Matriz muestra el acceso y la causa de la entrega sin inferir datos ausentes", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  const matriz: MatrizCorreccion = estado.matriz();
  const fila = matriz.sujetos[0];
  fila.accesos = [
    {
      estudiante_id: "e-1",
      nombre: "Integrante de ensayo",
      estado: "INVITADO",
      verificado_en: "2026-10-06T12:00:00Z",
    },
  ];
  fila.celdas["entrega-1"].banderas = ["sin_commits"];
  fila.celdas["entrega-1"].causas_sin_participacion = [
    {
      estudiante_id: "e-1",
      nombre: "Integrante de ensayo",
      causa: "SIN_ACCESO",
      registrada_en: "2026-10-06T12:00:00Z",
    },
  ];
  matriz.sujetos[1].celdas["entrega-1"].banderas = ["sin_commits"];
  await page.route("**/correccion/estado", (r) => r.fulfill({ json: matriz }));
  await page.goto("/cursos/curso-1/correccion?pestana=estado");
  await page.getByText("Acceso de integrantes", { exact: true }).click();
  await expect(
    page.getByText("Integrante de ensayo: Invitado, sin aceptar", {
      exact: false,
    }),
  ).toBeVisible();
  await page
    .getByText("Causas de participación registradas", { exact: true })
    .first()
    .click();
  await expect(
    page.getByText("Integrante de ensayo: Sin acceso al repositorio", {
      exact: false,
    }),
  ).toBeVisible();
  await page
    .getByText("Causas de participación registradas", { exact: true })
    .nth(1)
    .click();
  await expect(
    page.getByText("No hay una causa registrada para esta entrega.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  await page.screenshot({
    path: "../docs/frontend/evidencias/limitaciones-matriz-escritorio.png",
    fullPage: true,
  });
});

test("Comprobación Canvas informa fallo del trabajo y permite volver a solicitarla", async ({
  page,
}) => {
  await prepararFinal(page);
  await page.route("**/trabajos/comprobar-1", (r) =>
    r.fulfill({
      json: {
        id: "comprobar-1",
        estado: "REQUIERE_ATENCION",
        intentos: 4,
        max_intentos: 4,
        proximo_intento_en: null,
        terminado_en: "2026-10-06T12:00:00Z",
      },
    }),
  );
  await page.goto("/cursos/curso-1/correccion?pestana=estado");
  await page
    .getByRole("button", { name: "Comprobar contra Canvas", exact: true })
    .click();
  await expect(
    page.getByText("La comprobación con Canvas requiere atención.", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Comprobar contra Canvas", exact: true }),
  ).toBeEnabled();
  expect(new URL(page.url()).searchParams.has("comprobacion-tarea-1")).toBe(
    false,
  );
});

test("Sincronizaciones que terminan juntas limpian todos sus trabajos y conservan filtros", async ({
  page,
}) => {
  await preparar(page);
  await page.route("**/trabajos/j-*", (r) =>
    r.fulfill({
      json: {
        id: new URL(r.request().url()).pathname.split("/").at(-1),
        estado: "OK",
        intentos: 1,
        max_intentos: 4,
        proximo_intento_en: null,
        terminado_en: "2026-10-06T12:00:00Z",
      },
    }),
  );
  await page.goto(
    "/cursos/curso-1/personas?sincronizacion=j-1,j-2&registro=j-3&buscar=Ensayo",
  );
  await expect
    .poll(() => new URL(page.url()).searchParams.get("sincronizacion"))
    .toBeNull();
  await expect
    .poll(() => new URL(page.url()).searchParams.get("registro"))
    .toBeNull();
  expect(new URL(page.url()).searchParams.get("buscar")).toBe("Ensayo");
  await expect(
    page.getByRole("button", { name: "Sincronizar con Canvas", exact: true }),
  ).toBeEnabled();
});
