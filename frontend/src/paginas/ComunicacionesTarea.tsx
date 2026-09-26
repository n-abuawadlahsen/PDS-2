import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { cambiarReglaTarea, obtenerReglasTarea, type ReglaComunicacion } from "../lib/api";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;

/** Pestaña «Comunicaciones» de la tarea (S11.6.3): los seis avisos de la
 * tarea, cada uno con su vista previa y a cuántas personas llegaría hoy. */
export function ComunicacionesTarea({ cursoId, tareaId }: { cursoId: string; tareaId: string }) {
  const [reglas, setReglas] = useState<ReglaComunicacion[]>([]);
  const [vista, setVista] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    setReglas(await obtenerReglasTarea(cursoId, tareaId));
  }
  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId, tareaId]);

  async function cambiar(r: ReglaComunicacion) {
    if (r.activa && r.advertencia_al_apagar && !window.confirm(`${r.advertencia_al_apagar} ¿Apagar igual?`)) return;
    setError(null);
    const resultado = await cambiarReglaTarea(cursoId, tareaId, r.evento, !r.activa);
    if (!resultado.ok) setError(resultado.error);
    await cargar();
  }

  if (reglas.length === 0) return null;
  const apagadoRepo = reglas.some((r) => r.evento === "repositorio_disponible" && !r.activa);
  return (
    <section>
      <h2>Comunicaciones</h2>
      {apagadoRepo && (
        <p style={{ background: "#fff3cd", padding: "0.5rem" }}>Avisos de repositorio desactivados.</p>
      )}
      {error && <p style={{ background: "#fee", padding: "0.5rem" }}>{error}</p>}
      <ul style={{ listStyle: "none", paddingLeft: 0 }}>
        {reglas.map((r) => (
          <li key={r.evento} style={{ marginBottom: "0.5rem" }}>
            <label>
              <input type="checkbox" checked={r.activa} onChange={() => cambiar(r)} /> {r.titulo}
            </label>
            {!r.por_defecto && <span style={ESTILO_MOTIVO}> (apagado por defecto)</span>}
            {r.destinatarios_hoy !== null && (
              <span style={ESTILO_MOTIVO}> · llegaría hoy a {r.destinatarios_hoy}</span>
            )}{" "}
            <button style={{ fontSize: "0.75rem" }} onClick={() => setVista(vista === r.evento ? null : r.evento)}>
              {vista === r.evento ? "Ocultar texto" : "Ver texto"}
            </button>
            {vista === r.evento && (
              <div style={{ border: "1px solid #ddd", padding: "0.5rem", marginTop: "0.25rem" }}>
                {r.vista_previa_con_ejemplo && <p style={ESTILO_MOTIVO}>Datos de ejemplo.</p>}
                <p>
                  <strong>{r.vista_previa_asunto}</strong>
                </p>
                <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>{r.vista_previa_cuerpo}</pre>
              </div>
            )}
          </li>
        ))}
      </ul>
      <p style={ESTILO_MOTIVO}>
        Como máximo tres avisos automáticos por estudiante al día, entre las 08:00 y las 21:00.{" "}
        <Link to={`/cursos/${cursoId}/comunicaciones?tarea_id=${tareaId}`}>Ver lo enviado en esta tarea</Link>
      </p>
    </section>
  );
}
