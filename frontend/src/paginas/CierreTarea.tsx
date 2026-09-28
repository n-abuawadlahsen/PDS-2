import { useEffect, useState } from "react";
import {
  archivarTarea,
  desarchivarTarea,
  enviarAvisoArchivado,
  obtenerArchivado,
  type EstadoArchivado,
} from "../lib/api";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "var(--color-text-secondary)" } as const;

const CONSECUENCIAS = [
  "Cada repositorio pasa a sólo lectura en GitHub: los estudiantes lo siguen viendo, pero no pueden subir cambios.",
  "Las versiones ya capturadas no cambian: la evidencia es el commit registrado aquí.",
  "No se pueden crear etiquetas nuevas, y la actividad deja de leerse para esos repositorios.",
  "Es reversible: «Desarchivar» vuelve a abrir todos los repositorios archivados de la tarea.",
];

/** Bloque «Cierre de la tarea» (A-168, A-197): las cinco guardas a la vista
 * antes de habilitar el botón. Archivar y desarchivar son sólo del profesor. */
export function CierreTarea({ cursoId, tareaId }: { cursoId: string; tareaId: string }) {
  const [estado, setEstado] = useState<EstadoArchivado | null>(null);
  const [sinCaptura, setSinCaptura] = useState("");
  const [sinAviso, setSinAviso] = useState("");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    setEstado(await obtenerArchivado(cursoId, tareaId));
  }
  useEffect(() => {
    cargar();
  }, [cursoId, tareaId]);

  if (!estado) return null;

  // Una guarda que falla sólo por falta de confirmación se supera escribiéndola.
  const superable = estado.guardas.every(
    (g) =>
      g.cumple ||
      (g.confirmacion === "SIN_CAPTURA" && sinCaptura.trim().length >= 10) ||
      (g.confirmacion === "SIN_AVISO" && sinAviso.trim().length >= 10),
  );
  const habilitado = estado.archivables > 0 && estado.en_curso === 0 && superable;
  const pideCaptura = estado.guardas.some((g) => !g.cumple && g.confirmacion === "SIN_CAPTURA");
  const pideAviso = estado.guardas.some((g) => !g.cumple && g.confirmacion === "SIN_AVISO");
  const avisoPendiente = estado.aviso.destinatarios > 0 && estado.aviso.encolados < estado.aviso.destinatarios;

  async function onAviso() {
    setError(null);
    const r = await enviarAvisoArchivado(cursoId, tareaId);
    if (r.ok) setMensaje(`Aviso previo encolado para ${r.datos?.encolados ?? 0} estudiantes.`);
    else setError(r.error);
    await cargar();
  }

  async function onArchivar() {
    if (!window.confirm(`¿Archivar ${estado?.archivables} repositorios de esta tarea?`)) return;
    setError(null);
    const r = await archivarTarea(cursoId, tareaId, {
      confirmacion_sin_captura: pideCaptura ? sinCaptura : null,
      confirmacion_sin_aviso: pideAviso ? sinAviso : null,
    });
    if (r.ok) setMensaje(`Archivado en curso para ${r.datos?.repositorios ?? 0} repositorios.`);
    else setError(r.error);
    await cargar();
  }

  async function onDesarchivar() {
    if (!window.confirm("¿Desarchivar todos los repositorios archivados de esta tarea?")) return;
    setError(null);
    const r = await desarchivarTarea(cursoId, tareaId);
    if (r.ok) setMensaje(`Desarchivado en curso para ${r.datos?.repositorios ?? 0} repositorios.`);
    else setError(r.error);
    await cargar();
  }

  return (
    <section>
      <h2>Cierre de la tarea</h2>
      <p>
        {estado.tarea_estado === "ARCHIVADA" ? "La tarea está archivada. " : ""}
        {estado.archivables} repositorios por archivar · {estado.archivados} archivados
        {estado.fuera_de_alcance_o_inaccesibles > 0 &&
          ` · ${estado.fuera_de_alcance_o_inaccesibles} fuera de alcance o inaccesibles`}
        {estado.en_curso > 0 && ` · ${estado.en_curso} en curso`}
      </p>
      {mensaje && <p style={{ background: "var(--color-success-background)", padding: "0.5rem" }}>{mensaje}</p>}
      {error && <p style={{ background: "var(--color-error-background)", padding: "0.5rem" }}>{error}</p>}

      {estado.archivables > 0 && (
        <>
          <ol>
            {estado.guardas.map((g) => (
              <li key={g.numero}>
                <strong>{g.cumple ? "Cumple" : "Falta"}</strong> · {g.titulo}
                {g.motivo && <div style={ESTILO_MOTIVO}>{g.motivo}</div>}
                {g.detalle.length > 0 && (
                  <ul style={ESTILO_MOTIVO}>
                    {g.detalle.slice(0, 10).map((d) => (
                      <li key={d}>{d}</li>
                    ))}
                    {g.detalle.length > 10 && <li>y {g.detalle.length - 10} más</li>}
                  </ul>
                )}
                {g.numero === 4 && avisoPendiente && (
                  <div>
                    <button onClick={onAviso}>Enviar aviso previo por Canvas</button>
                  </div>
                )}
              </li>
            ))}
          </ol>
          {pideCaptura && (
            <label style={{ display: "block" }}>
              Por qué archivas con entregas sin versión capturada
              <textarea value={sinCaptura} onChange={(e) => setSinCaptura(e.target.value)} rows={2} style={{ width: "100%" }} />
            </label>
          )}
          {pideAviso && (
            <label style={{ display: "block" }}>
              Declara cuántos estudiantes no recibieron el aviso y cómo les avisaste
              <textarea value={sinAviso} onChange={(e) => setSinAviso(e.target.value)} rows={2} style={{ width: "100%" }} />
            </label>
          )}
          <p style={ESTILO_MOTIVO}>Qué implica archivar:</p>
          <ul style={ESTILO_MOTIVO}>
            {CONSECUENCIAS.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
          <button disabled={!habilitado} onClick={onArchivar}>
            Archivar repositorios de la tarea
          </button>{" "}
        </>
      )}
      {estado.puede_desarchivar && (
        <button disabled={estado.en_curso > 0} onClick={onDesarchivar}>
          Desarchivar
        </button>
      )}
      <p style={ESTILO_MOTIVO}>Sólo un profesor del curso puede archivar o desarchivar.</p>
    </section>
  );
}
