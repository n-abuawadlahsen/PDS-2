import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ejecutarPruebaEscritura,
  encolarChecklist,
  firmarItem14AMano,
  obtenerEjecucionVerificacion,
  obtenerUltimaVerificacion,
  reejecutarItem,
  type ItemVerificacion,
} from "../lib/api";

/** Los 19 items numerados, en el orden en que se muestran (S4.7.2). El
 * carril de Canvas corre en serie y el de GitHub en paralelo; aqui solo
 * importa el orden de lectura para la persona, no el de ejecucion. */
const NOMBRES_ITEMS: Record<string, string> = {
  "1": "El token es válido y es tuyo",
  "2": "El curso existe, es visible y está publicado",
  "3": "Eres profesor del curso y no estás limitado a una sección",
  "4": "Puedes editar notas",
  "5": "Puedes publicar anuncios",
  "6": "Puedes enviar mensajes",
  "7": "Puedes ver correos de estudiantes",
  "8": "Secciones legibles y detección de cross-listing",
  "9": "Conjuntos de grupos colaborativos",
  "10": "Política de entrega tardía del curso",
  "11": "Períodos de calificación abiertos",
  "12": "Tamaño real de página que acepta la instancia",
  "13": "Zona horaria del curso",
  "14": "La App está instalada, con permisos congelados y la organización presentable",
  "15": "Estudiantes legibles",
  "16": "Puedes crear y editar tareas en Canvas",
  "17": "Puedes escribir comentarios en las entregas",
  "18": "Cada docente del curso tiene membresía activa en la organización",
  "19": "Puedes borrar anuncios propios",
};

const ORDEN_VISUAL = [
  "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
  "11", "12", "13", "14", "15", "16", "17", "18", "19",
];

const COLOR_RESULTADO: Record<string, string> = {
  CORRECTO: "#1a7f37",
  ADVERTENCIA: "#9a6700",
  BLOQUEANTE: "#cf222e",
  NO_VERIFICADO: "#57606a",
  VERIFICADO_A_MANO: "#8250df",
};

function Insignia({ resultado }: { resultado: string }) {
  return (
    <span
      style={{
        color: "white",
        background: COLOR_RESULTADO[resultado] ?? "#57606a",
        borderRadius: 4,
        padding: "0.1rem 0.5rem",
        fontSize: "0.85rem",
      }}
    >
      {resultado}
    </span>
  );
}

export function Checklist() {
  const { cursoId } = useParams<{ cursoId: string }>();
  const [items, setItems] = useState<Record<string, ItemVerificacion>>({});
  const [corriendo, setCorriendo] = useState(false);
  const [consiento5bis, setConsiento5bis] = useState(false);
  const [consiento17bis, setConsiento17bis] = useState(false);
  const intervalo = useRef<number | undefined>(undefined);

  const cargarUltima = useCallback(() => {
    if (!cursoId) return;
    obtenerUltimaVerificacion(cursoId).then((lista) => {
      setItems((previo) => {
        const siguiente = { ...previo };
        for (const item of lista) if (item.item) siguiente[item.item] = item;
        return siguiente;
      });
    });
  }, [cursoId]);

  useEffect(() => {
    cargarUltima();
  }, [cargarUltima]);

  useEffect(() => () => window.clearInterval(intervalo.current), []);

  function sondear(cursoIdActual: string, ejecucionId: string, cantidadEsperada: number) {
    setCorriendo(true);
    let intentos = 0;
    intervalo.current = window.setInterval(async () => {
      intentos += 1;
      const lista = await obtenerEjecucionVerificacion(cursoIdActual, ejecucionId);
      setItems((previo) => {
        const siguiente = { ...previo };
        for (const item of lista) if (item.item) siguiente[item.item] = item;
        return siguiente;
      });
      // Tope 180s (S4.7.1): a 2s por sondeo, no hay razon para pasar de 95 vueltas.
      if (lista.length >= cantidadEsperada || intentos >= 95) {
        window.clearInterval(intervalo.current);
        setCorriendo(false);
      }
    }, 2000);
  }

  async function ejecutarTodo() {
    if (!cursoId) return;
    const { ejecucion_id } = await encolarChecklist(cursoId);
    sondear(cursoId, ejecucion_id, 19);
  }

  async function reejecutar(item: string) {
    if (!cursoId) return;
    const { ejecucion_id } = await reejecutarItem(cursoId, item);
    sondear(cursoId, ejecucion_id, 1);
  }

  async function firmarAMano() {
    if (!cursoId) return;
    const fila = await firmarItem14AMano(cursoId);
    setItems((previo) => ({ ...previo, "14": fila }));
  }

  async function probarEscritura(item: "5-bis" | "17-bis", consiento: boolean) {
    if (!cursoId) return;
    const fila = await ejecutarPruebaEscritura(cursoId, item, consiento);
    setItems((previo) => ({ ...previo, [item]: fila }));
  }

  const item14 = items["14"];
  const requiereFirma = Boolean(item14 && (item14.detalle as { requiere_firma_manual?: boolean }).requiere_firma_manual);

  return (
    <main style={{ maxWidth: 760, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Paso 4: checklist de verificación</h1>
      <p>
        <button onClick={ejecutarTodo} disabled={corriendo}>
          {corriendo ? "Ejecutando…" : "Ejecutar checklist completo"}
        </button>
      </p>

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <tbody>
          {ORDEN_VISUAL.map((id) => {
            const fila = items[id];
            return (
              <tr key={id} style={{ borderBottom: "1px solid #ddd" }}>
                <td style={{ padding: "0.4rem 0.5rem", width: "2rem" }}>{id}</td>
                <td style={{ padding: "0.4rem 0.5rem" }}>{NOMBRES_ITEMS[id]}</td>
                <td style={{ padding: "0.4rem 0.5rem", whiteSpace: "nowrap" }}>
                  {fila ? <Insignia resultado={fila.resultado} /> : <em>sin ejecutar</em>}
                </td>
                <td style={{ padding: "0.4rem 0.5rem" }}>
                  <button onClick={() => reejecutar(id)} disabled={corriendo}>
                    Reejecutar
                  </button>
                  {id === "14" && requiereFirma && (
                    <button onClick={firmarAMano} style={{ marginLeft: "0.5rem" }}>
                      Firmar a mano
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <section style={{ marginTop: "2rem" }}>
        <h2>Pruebas de escritura opcionales</h2>
        <p>
          Se ejecutan de inmediato (no forman parte del checklist encolado) y solo si marcás la
          casilla correspondiente.
        </p>
        <p>
          <label>
            <input
              type="checkbox"
              checked={consiento5bis}
              onChange={(e) => setConsiento5bis(e.target.checked)}
            />{" "}
            Autorizo la prueba de anuncio de sección (5-bis)
          </label>{" "}
          <button onClick={() => probarEscritura("5-bis", consiento5bis)}>Probar</button>{" "}
          {items["5-bis"] && <Insignia resultado={items["5-bis"].resultado} />}
        </p>
        <p>
          <label>
            <input
              type="checkbox"
              checked={consiento17bis}
              onChange={(e) => setConsiento17bis(e.target.checked)}
            />{" "}
            Autorizo la prueba de comentario en una entrega (17-bis)
          </label>{" "}
          <button onClick={() => probarEscritura("17-bis", consiento17bis)}>Probar</button>{" "}
          {items["17-bis"] && <Insignia resultado={items["17-bis"].resultado} />}
        </p>
      </section>

      <p>
        {cursoId && <Link to={`/cursos/${cursoId}/vinculacion`}>Volver al asistente de vinculación</Link>}
      </p>
    </main>
  );
}
