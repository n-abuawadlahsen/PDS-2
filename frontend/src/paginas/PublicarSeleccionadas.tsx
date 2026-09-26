import { useState } from "react";
import { comprobarContraCanvas, publicarCorreccion, type MatrizCorreccion } from "../lib/api";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;

/** «Publicar seleccionadas» (S12.10.6): la misma escritura individual, una
 * a una y en orden; si se interrumpe, al retomarla salta lo ya publicado. */
export function PublicarSeleccionadas({
  cursoId,
  matriz,
  onFin,
}: {
  cursoId: string;
  tareaId: string;
  matriz: MatrizCorreccion;
  onFin: () => void;
}) {
  const listas = matriz.sujetos.flatMap((s) =>
    Object.entries(s.celdas)
      .filter(([, c]) => c.estado === "LISTA_PARA_PUBLICAR" && c.publicable)
      .map(([entregaId]) => ({ entregaId, sujetoId: s.sujeto_id, sujeto: s.sujeto })),
  );
  const [elegidas, setElegidas] = useState<Set<string>>(new Set());
  const [progreso, setProgreso] = useState<string | null>(null);
  const [resultados, setResultados] = useState<string[]>([]);

  async function publicar() {
    const cola = listas.filter((l) => elegidas.has(`${l.entregaId}/${l.sujetoId}`));
    const salida: string[] = [];
    for (const [i, l] of cola.entries()) {
      setProgreso(`Publicando ${i + 1} de ${cola.length}…`);
      const r = await publicarCorreccion(cursoId, l.entregaId, l.sujetoId, {});
      salida.push(
        `${l.sujeto}: ${r.ok ? (r.datos?.estado === "PUBLICADA" ? "publicada" : r.datos?.estado?.toLowerCase().replaceAll("_", " ")) : r.detalle?.motivo}`,
      );
      setResultados([...salida]);
    }
    setProgreso(null);
    setElegidas(new Set());
    onFin();
  }

  async function comprobar() {
    for (const e of matriz.entregas) await comprobarContraCanvas(cursoId, e.id);
    setProgreso("Comprobación encolada: la vista se actualiza cuando termine.");
    setTimeout(onFin, 4000);
  }

  return (
    <div style={{ margin: "0.5rem 0" }}>
      <button onClick={comprobar}>Comprobar contra Canvas</button>{" "}
      {listas.length > 0 && (
        <>
          <span style={ESTILO_MOTIVO}>{listas.length} listas para publicar: </span>
          {listas.map((l) => {
            const clave = `${l.entregaId}/${l.sujetoId}`;
            return (
              <label key={clave} style={{ marginRight: "0.5rem" }}>
                <input
                  type="checkbox"
                  checked={elegidas.has(clave)}
                  onChange={(e) => {
                    const n = new Set(elegidas);
                    if (e.target.checked) n.add(clave);
                    else n.delete(clave);
                    setElegidas(n);
                  }}
                />{" "}
                {l.sujeto}
              </label>
            );
          })}
          <button disabled={elegidas.size === 0 || progreso !== null} onClick={publicar}>
            Publicar seleccionadas
          </button>
        </>
      )}
      {progreso && <p>{progreso}</p>}
      {resultados.length > 0 && (
        <ul style={ESTILO_MOTIVO}>
          {resultados.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
