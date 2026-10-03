import { expect, test } from "@playwright/test";
import { prepararFinal } from "./fixtures-final";

const ruta = "/cursos/curso-1/correccion/entrega-1/sujeto-0";
test("borrador, lista y publicación son operaciones separadas y explícitas", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  await page.goto(ruta);
  await page.getByLabel("Nota (sobre 100)", { exact: true }).fill("82");
  await page
    .getByRole("button", { name: "Guardar borrador", exact: true })
    .click();
  await expect(
    page.getByText("Borrador guardado. No se publicó ninguna nota en Canvas."),
  ).toBeVisible();
  expect(estado.guardados).toBe(1);
  expect(estado.publicaciones).toBe(0);
  await page.getByRole("button", { name: "Marcar lista", exact: true }).click();
  await page
    .getByRole("button", { name: "Publicar en Canvas", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(estado.publicaciones).toBe(0);
  await page
    .getByRole("button", { name: "Confirmar y publicar", exact: true })
    .click();
  await expect(
    page.getByText("Nota publicada y verificada en Canvas.", { exact: true }),
  ).toBeVisible();
  expect(estado.publicaciones).toBe(1);
  expect(estado.pantalla("sujeto-0").borrador?.nota).toBe("82");
});
test("conflicto de Canvas mantiene las tres decisiones y adoptar no publica", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  estado.conflicto = true;
  estado.pantalla("sujeto-0").estado = "LISTA_PARA_PUBLICAR";
  await page.goto(ruta);
  await page
    .getByRole("button", { name: "Publicar en Canvas", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Confirmar y publicar", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Conflicto con Canvas" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Publicar la mía", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Dejarlo como está", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Adoptar la de Canvas", exact: true })
    .click();
  await expect(
    page.getByText(
      "Se adoptó la nota de Canvas (65). No se escribió en Canvas.",
    ),
  ).toBeVisible();
  expect(estado.publicaciones).toBe(0);
});
test("publicación bloqueada conserva visible su motivo", async ({ page }) => {
  const estado = await prepararFinal(page);
  estado.bloqueo = true;
  estado.pantalla("sujeto-0").estado = "LISTA_PARA_PUBLICAR";
  await page.goto(ruta);
  await expect(
    page.getByText(/No publicable en Canvas: El período/),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Publicar en Canvas", exact: true }),
  ).toBeDisabled();
  expect(estado.publicaciones).toBe(0);
});
test("conserva el formulario tras conflicto y protege la navegación con cambios", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  estado.falloBorrador = true;
  await page.goto(ruta);
  await page.getByLabel("Nota (sobre 100)", { exact: true }).fill("91");
  await page
    .getByRole("button", { name: "Guardar borrador", exact: true })
    .click();
  await expect(
    page.getByText(/Otra persona actualizó este borrador/),
  ).toBeVisible();
  await expect(
    page.getByLabel("Nota (sobre 100)", { exact: true }),
  ).toHaveValue("91");
  await page.getByRole("button", { name: "Siguiente", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(page).toHaveURL(new RegExp("sujeto-0$"));
  await expect(
    page.getByLabel("Nota (sobre 100)", { exact: true }),
  ).toHaveValue("91");
});
test("recorrido respeta sección y entrega con matriz de 200 sujetos", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  estado.cantidad = 200;
  await page.goto(
    "/cursos/curso-1/correccion?pestana=estado&seccion=Secci%C3%B3n+1&entrega=entrega-1",
  );
  await expect(page.getByText("100 resultados · Página 1 de 4")).toBeVisible();
  await page
    .getByRole("link", { name: "En curso", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Equipo 01", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Siguiente", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Equipo 03", exact: true }),
  ).toBeVisible();
  await expect(page).toHaveURL(/entrega-1\/sujeto-2$/);
});
test("ayudante puede revisar pero no repartir, enviar ni publicar", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  estado.base.permisos = ["curso.ver", "correccion.corregir"];
  await page.goto("/cursos/curso-1/correccion?pestana=repartir");
  await expect(
    page.getByText(/No tienes permiso para repartir correcciones/),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Previsualizar reparto" }),
  ).toHaveCount(0);
  await page.goto("/cursos/curso-1/comunicaciones");
  await expect(page.getByText(/Puedes consultar el historial/)).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Escribir a estudiantes" }),
  ).toHaveCount(0);
  await page.goto(ruta);
  await expect(
    page.getByRole("button", { name: "Guardar borrador" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Publicar en Canvas", exact: true }),
  ).toHaveCount(0);
});
test("suscripción, informe, previsualización y resultado en cola", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  await page.goto("/cursos/curso-1/mis-notificaciones");
  await page.getByRole("button", { name: "Suscribirme", exact: true }).click();
  await expect(
    page.getByText("Te suscribiste al informe diario."),
  ).toBeVisible();
  expect(estado.suscrito).toBe(true);
  await page.getByRole("link", { name: "Ver informes", exact: true }).click();
  await page
    .getByRole("button", { name: "Vista previa de hoy", exact: true })
    .click();
  await expect(
    page
      .frameLocator('iframe[title="Contenido del informe docente"]')
      .getByRole("heading", { name: "Requiere atención" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Enviarme el informe de hoy" })
    .click();
  await expect(page.getByText(/Tu informe quedó en cola/)).toBeVisible();
  await page.goto("/cursos/curso-1/comunicaciones");
  await page.getByRole("button", { name: "Escribir a estudiantes" }).click();
  await page.getByLabel("Estudiante sin cuenta", { exact: true }).check();
  await page.getByLabel("Asunto", { exact: true }).fill("Revisión de entrega");
  await page
    .getByRole("textbox", { name: "Mensaje", exact: true })
    .fill("Revisa los comentarios de tu entrega en Canvas.");
  await page
    .getByRole("button", { name: "Previsualizar comunicación" })
    .click();
  expect(estado.mensajes).toHaveLength(0);
  await page
    .getByRole("button", { name: "Confirmar y enviar", exact: true })
    .click();
  await expect(page.getByText("En cola", { exact: true })).toBeVisible();
  expect(estado.mensajes).toHaveLength(1);
});
test("un fallo de comunicación conserva destinatarios y texto", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  estado.falloMensaje = true;
  await page.goto("/cursos/curso-1/comunicaciones");
  await page.getByRole("button", { name: "Escribir a estudiantes" }).click();
  await page.getByLabel("Estudiante sin cuenta", { exact: true }).check();
  await page.getByLabel("Asunto", { exact: true }).fill("Texto conservado");
  await page
    .getByRole("textbox", { name: "Mensaje", exact: true })
    .fill("Este mensaje debe permanecer tras el error.");
  await page
    .getByRole("button", { name: "Previsualizar comunicación" })
    .click();
  await page
    .getByRole("button", { name: "Confirmar y enviar", exact: true })
    .click();
  await expect(page.getByText(/Canvas no está disponible/)).toBeVisible();
  await page.getByRole("button", { name: "Volver a editar" }).click();
  await expect(
    page.getByRole("textbox", { name: "Mensaje", exact: true }),
  ).toHaveValue("Este mensaje debe permanecer tras el error.");
  await expect(
    page.getByLabel("Estudiante sin cuenta", { exact: true }),
  ).toBeChecked();
});

test("publicación masiva requiere selección y confirmación, y publica una vez por sujeto", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  for (const id of ["sujeto-0", "sujeto-1"]) {
    const p = estado.pantalla(id);
    p.estado = "LISTA_PARA_PUBLICAR";
    p.etiqueta = "Lista para publicar";
  }
  await page.goto("/cursos/curso-1/correccion?pestana=estado");
  await page
    .getByText("Publicación masiva · 2 correcciones listas", { exact: true })
    .click();
  await page
    .getByRole("checkbox", { name: "Equipo 01 · Entrega final" })
    .check();
  await page
    .getByRole("checkbox", { name: "Equipo 02 · Entrega final" })
    .check();
  await page
    .getByRole("button", { name: "Publicar seleccionadas", exact: true })
    .click();
  expect(estado.publicaciones).toBe(0);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Publicar seleccionadas", exact: true })
    .click();
  await expect.poll(() => estado.publicaciones).toBe(2);
  await expect(
    page.getByText("Publicada y verificada.", { exact: false }).first(),
  ).toBeVisible();
  expect(
    estado.llamadas.filter((r) => r.path.endsWith("/publicar")),
  ).toHaveLength(2);
});

test("anuncio exige confirmar el alcance devuelto por el servidor", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  await page.goto("/cursos/curso-1/comunicaciones");
  await page
    .getByRole("button", { name: "Publicar un anuncio", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Título", exact: true })
    .fill("Próxima revisión");
  await page
    .getByRole("textbox", { name: "Texto del anuncio", exact: true })
    .fill("<p>La próxima revisión será en clases.</p>");
  await page
    .getByRole("button", { name: "Previsualizar comunicación" })
    .click();
  await page
    .getByRole("button", { name: "Confirmar y publicar anuncio" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Confirmar alcance del anuncio" }),
  ).toBeVisible();
  await page.getByRole("dialog").getByRole("textbox").fill("45");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Publicar anuncio", exact: true })
    .click();
  await expect(
    page.getByText("Anuncio encolado para 45 estudiantes.", { exact: true }),
  ).toBeVisible();
  expect(
    estado.llamadas.filter((r) => r.path.endsWith("/comunicaciones/anuncios")),
  ).toHaveLength(2);
});

test("reparto por sección muestra la propuesta antes de escribir", async ({
  page,
}) => {
  const estado = await prepararFinal(page);
  await page.goto("/cursos/curso-1/correccion?pestana=repartir");
  await page
    .getByRole("combobox", { name: "Criterio", exact: true })
    .selectOption("SECCION");
  await page
    .getByRole("combobox", { name: "Sección 1", exact: true })
    .selectOption("m-2");
  await page.getByRole("button", { name: "Previsualizar reparto" }).click();
  await expect(
    page.getByRole("heading", { name: "Propuesta de reparto" }),
  ).toBeVisible();
  expect(
    estado.llamadas.filter((r) => r.path.endsWith("/reparto/aplicar")),
  ).toHaveLength(0);
  await page
    .getByRole("button", { name: "Confirmar y aplicar", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar y aplicar", exact: true })
    .click();
  await expect(page.getByText("Reparto aplicado: 3 cambios.")).toBeVisible();
  const llamada = estado.llamadas.find((r) =>
    r.path.endsWith("/reparto/aplicar"),
  );
  expect(llamada?.body).toMatchObject({
    criterio: "SECCION",
    por_seccion: { "s-1": "m-2" },
  });
});
