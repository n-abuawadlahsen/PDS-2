import { expect, test } from "@playwright/test";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

function archivos(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? archivos(join(dir, e.name)) : [join(dir, e.name)],
  );
}
function luminancia(hex: string) {
  const rgb = [1, 3, 5]
    .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return rgb.reduce((n, v, i) => n + v * [0.2126, 0.7152, 0.0722][i], 0);
}
function contraste(a: string, b: string) {
  const [menor, mayor] = [luminancia(a), luminancia(b)].sort((x, y) => x - y);
  return (mayor + 0.05) / (menor + 0.05);
}
test("paletas completas: contraste funcional y colores centralizados", () => {
  const fuentes = archivos("src").filter((p) => /\.(css|tsx?)$/.test(p));
  const contenido = fuentes.map((p) => readFileSync(p, "utf8")).join("\n");
  const referencias = [...contenido.matchAll(/var\((--[\w-]+)/g)].map(
    (m) => m[1],
  );
  const definiciones = new Set(
    [...contenido.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]),
  );
  expect(referencias.filter((r) => !definiciones.has(r))).toEqual([]);
  for (const p of fuentes.filter((p) => !p.endsWith("themes.css"))) {
    expect(readFileSync(p, "utf8"), p).not.toMatch(
      /#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/,
    );
  }
  const css = readFileSync("src/styles/themes.css", "utf8");
  const extraer = (s: string): Record<string, string> =>
    Object.fromEntries(
      [...s.matchAll(/--color-([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;/g)].map((m) => [
        m[1],
        m[2],
      ]),
    );
  const comunes = extraer(css.split(":root,")[0]);
  for (const tema of ["institucional", "azul", "verde"]) {
    const bloque = css.match(
      new RegExp(`:root\\[data-theme="${tema}"\\]\\s*\\{([^}]+)`),
    )![1];
    const colores = { ...comunes, ...extraer(bloque) };
    const textos = [
      ["text", "surface"],
      ["text-secondary", "surface"],
      ["placeholder", "surface"],
      ["primary", "surface"],
      ["on-primary", "primary"],
      ["on-primary", "primary-hover"],
      ["on-primary", "primary-active"],
      ["primary", "primary-subtle"],
      ["sidebar-text", "sidebar"],
      ["sidebar-text", "sidebar-hover"],
      ...["success", "warning", "error", "info"].map((e) => [
        e,
        `${e}-background`,
      ]),
    ];
    for (const [texto, fondo] of textos)
      expect(
        contraste(colores[texto], colores[fondo]),
        `${tema}: ${texto}/${fondo}`,
      ).toBeGreaterThanOrEqual(4.5);
    const limites = [
      ...["success", "warning", "error", "info"].map((e) => [
        `${e}-border`,
        `${e}-background`,
      ]),
      ["border-strong", "surface"],
      ["primary", "surface"],
      ["sidebar-text", "sidebar"],
    ];
    for (const [borde, fondo] of limites)
      expect(
        contraste(colores[borde], colores[fondo]),
        `${tema}: ${borde}/${fondo}`,
      ).toBeGreaterThanOrEqual(3);
  }
});
