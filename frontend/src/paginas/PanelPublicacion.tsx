import { useState } from "react";
import {
  accionPublicacion,
  publicarCorreccion,
  type PantallaCorreccion,
  type ResultadoPublicacion,
} from "../lib/api";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;

/** Publicación en Canvas (S12.10, S12.14): el diálogo muestra a nombre de
 * quién quedará la nota, y un conflicto con Canvas nunca se resuelve solo. */
export function PanelPublicacion({
  cursoId,
  entregaId,
  sujetoId,
  datos,
  onCambio,
}: {
  cursoId: string;
  entregaId: string;
  sujetoId: string;
  datos: PantallaCorreccion;
  onCambio: () => void;
}) {
  const [abierto, setAbierto] = useState(false);
  const [versionRevisada, setVersionRevisada] = useState(false);
  const [confirmacionReclamo, setConfirmacionReclamo] = useState("");
  const [sinCodigo, setSinCodigo] = useState(false);
  const [conflicto, setConflicto] = useState<ResultadoPublicacion["detalle"]>(null);
  const [aceptoReemplazar, setAceptoReemplazar] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enCurso, setEnCurso] = useState(false);

  async function publicar(resolucion?: "PUBLICAR_MIA") {
    setEnCurso(true);
    setError(null);
    const r = await publicarCorreccion(cursoId, entregaId, sujetoId, {
      resolucion,
      version_revisada: versionRevisada,
      confirmacion_reclamo: confirmacionReclamo || undefined,
      reconocimiento_sin_codigo: sinCodigo,
    });
    setEnCurso(false);
    if (r.ok) {
      setMensaje(
        r.datos?.estado === "PUBLICADA"
          ? "Nota publicada y verificada en Canvas."
          : r.datos?.estado === "PUBLICADA_CON_ADVERTENCIA"
            ? "Se publicó, pero Canvas guardó algo distinto (por ejemplo, un descuento por atraso). Revísalo en Canvas."
            : `No se pudo publicar: ${r.datos?.error ?? ""}`,
      );
      setAbierto(false);
      setConflicto(null);
    } else if (r.detalle?.codigo === "CONFLICTO") {
      setConflicto(r.detalle);
    } else {
      setError(r.detalle?.motivo ?? "No se pudo publicar.");
    }
    onCambio();
  }

  async function accion(tipo: "reintentar" | "reabrir" | "adoptar-canvas" | "rubrica-revisada") {
    let motivo = "";
    if (tipo === "reabrir") {
      motivo = window.prompt("¿Por qué reabres la corrección?") ?? "";
      if (!motivo) return;
    }
    const r = await accionPublicacion(cursoId, entregaId, sujetoId, tipo, motivo);
    if (!r.ok) setError(r.error);
    else if (tipo === "adoptar-canvas") {
      setConflicto(null);
      setMensaje(`Se adoptó la nota de Canvas (${r.datos?.nota}). No se escribió nada en Canvas.`);
    }
    onCambio();
  }

  if (!datos.puede_publicar) return null;
  const e = datos.estado;
  return (
    <section style={{ borderTop: "1px solid #ddd", marginTop: "1rem" }}>
      <h2>Publicar en Canvas</h2>
      {mensaje && <p style={{ background: "#efe", padding: "0.5rem" }}>{mensaje}</p>}
      {error && <p style={{ background: "#fee", padding: "0.5rem" }}>{error}</p>}
      {datos.rubrica.cambio_sin_revisar && (
        <p>
          <button onClick={() => accion("rubrica-revisada")}>He revisado los cambios de la rúbrica</button>
        </p>
      )}
      {e === "LISTA_PARA_PUBLICAR" && !abierto && (
        <button disabled={!datos.publicable} onClick={() => setAbierto(true)}>
          Publicar la nota
        </button>
      )}
      {e === "LISTA_PARA_PUBLICAR" && abierto && !conflicto && (
        <div style={{ border: "1px solid #ddd", padding: "0.75rem" }}>
          <p>
            Se registrará en Canvas a nombre de <strong>{datos.titular}</strong>, con la nota{" "}
            <strong>{datos.borrador?.nota}</strong> y este comentario (con el pie de la versión revisada):
          </p>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", background: "#f6f8fa", padding: "0.5rem" }}>
            {datos.borrador?.comentario}
            {"\n\n—\nEntrega: "}
            {datos.entrega.nombre}
            {datos.version?.sha_corto ? `\nVersión revisada: ${datos.version.sha_corto}` : "\nVersión revisada: sin commits al cierre"}
          </pre>
          {datos.banderas.version_desactualizada && (
            <label style={{ display: "block" }}>
              <input type="checkbox" checked={versionRevisada} onChange={(ev) => setVersionRevisada(ev.target.checked)} /> He
              revisado la versión nueva
            </label>
          )}
          {datos.banderas.reclamo_abierto && (
            <label style={{ display: "block" }}>
              Hay un reclamo abierto: escribe por qué publicas igual
              <input value={confirmacionReclamo} onChange={(ev) => setConfirmacionReclamo(ev.target.value)} style={{ width: "100%" }} />
            </label>
          )}
          {datos.repositorio_estado === "INACCESIBLE" && !datos.banderas.reconocimiento_sin_codigo && (
            <label style={{ display: "block" }}>
              <input type="checkbox" checked={sinCodigo} onChange={(ev) => setSinCodigo(ev.target.checked)} /> Califico sin haber
              podido abrir el código de esta versión
            </label>
          )}
          <p style={ESTILO_MOTIVO}>Se envía sin descuento por atraso («late_policy_status» en none).</p>
          <button disabled={enCurso} onClick={() => publicar()}>
            {enCurso ? "Publicando…" : "Confirmar y publicar"}
          </button>{" "}
          <button onClick={() => setAbierto(false)}>Cancelar</button>
        </div>
      )}
      {conflicto && (
        <div style={{ border: "2px solid #e0a800", padding: "0.75rem" }}>
          <p>
            <strong>Canvas ya tiene otra nota.</strong> Nada se publicó.
          </p>
          <ul>
            {conflicto.conflictos?.map((c) => (
              <li key={c.estudiante}>
                {c.estudiante}: Canvas {c.nota_canvas ?? "sin nota"}
                {c.calificada_en && ` (puesta el ${new Date(c.calificada_en).toLocaleString("es-CL")})`} · aquí{" "}
                {conflicto.nota_propia}
              </li>
            ))}
          </ul>
          <label style={{ display: "block" }}>
            <input type="checkbox" checked={aceptoReemplazar} onChange={(ev) => setAceptoReemplazar(ev.target.checked)} /> Entiendo
            que reemplazaré la nota de Canvas
          </label>
          <button disabled={!aceptoReemplazar} onClick={() => publicar("PUBLICAR_MIA")}>
            Publicar la mía y reemplazar la de Canvas
          </button>{" "}
          <button onClick={() => accion("adoptar-canvas")}>Adoptar la de Canvas</button>{" "}
          <button onClick={() => setConflicto(null)}>Dejarlo como está</button>
        </div>
      )}
      {e === "ERROR_PUBLICACION" && <button onClick={() => accion("reintentar")}>Reintentar la publicación</button>}
      {(e === "PUBLICADA" || e === "PUBLICADA_CON_ADVERTENCIA") && (
        <p>
          {e === "PUBLICADA" ? "Publicada y verificada en Canvas." : "Publicada con advertencia: revisa la nota en Canvas."}{" "}
          <button onClick={() => accion("reabrir")}>Reabrir corrección</button>
        </p>
      )}
    </section>
  );
}
