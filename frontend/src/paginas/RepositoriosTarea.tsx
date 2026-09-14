import { useEffect, useState } from "react";
import {
  obtenerFechasEntregas,
  obtenerRepositoriosTarea,
  reintentarRepositorio,
  sustituirRepositorio,
  type FechasEntrega,
  type FilaRepositorio,
  type RepositoriosTarea,
} from "../lib/api";
import {
  colorEstadoRepositorio,
  fechaLegible,
  textoAccesoDocente,
  textoEstadoAcceso,
  textoEstadoRepositorio,
  textoMotivoRepositorio,
  textoTipoEntrega,
} from "../lib/textosTarea";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;
const INTERVALO_SONDEO_MS = 10_000;

function Contador({ etiqueta, valor, color }: { etiqueta: string; valor: number; color?: string }) {
  return (
    <div style={{ border: "1px solid #d0d7de", borderRadius: 6, padding: "0.5rem 0.75rem", minWidth: 120 }}>
      <div style={{ fontSize: "1.4rem", fontWeight: 600, color: color ?? "inherit" }}>{valor}</div>
      <div style={{ fontSize: "0.8rem", color: "#57606a" }}>{etiqueta}</div>
    </div>
  );
}

/** SPEC 08 S8.9 (R2.3.11): el estado de creacion y configuracion de todos los
 * repositorios de la tarea, con columnas que nunca se mezclan. Se refresca por
 * sondeo mientras haya trabajo en curso (nunca SSE ni WebSocket). */
export function BloqueRepositorios({ cursoId, tareaId }: { cursoId: string; tareaId: string }) {
  const [datos, setDatos] = useState<RepositoriosTarea | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  async function cargar() {
    setDatos(await obtenerRepositoriosTarea(cursoId, tareaId));
  }

  useEffect(() => {
    cargar();
    const temporizador = setInterval(cargar, INTERVALO_SONDEO_MS);
    return () => clearInterval(temporizador);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId, tareaId]);

  if (!datos) return <p>Cargando repositorios…</p>;
  const r = datos.resumen;
  const conProblemas = r.bloqueados + r.error_transitorio + r.error_permanente;

  async function onReintentar(fila: FilaRepositorio) {
    const resultado = await reintentarRepositorio(cursoId, tareaId, fila.repositorio_id);
    setMensaje(resultado.ok ? `Reintento encolado para ${fila.nombre}.` : resultado.error);
    await cargar();
  }

  async function onSustituir(fila: FilaRepositorio) {
    const confirmacion = window.prompt(
      `Sustituir crea un repositorio nuevo para ${fila.sujeto}. El repositorio perdido ` +
        `(${fila.nombre}) no vuelve: se conserva solo como evidencia. Para confirmar, escribe su nombre exacto:`,
    );
    if (confirmacion === null) return;
    const resultado = await sustituirRepositorio(cursoId, tareaId, fila.repositorio_id, confirmacion);
    setMensaje(resultado.ok ? "Sustitución encolada." : resultado.error);
    await cargar();
  }

  return (
    <section>
      <h2>Repositorios</h2>
      {mensaje && <p role="status">{mensaje}</p>}

      {r.en_curso && (
        <p>
          <strong>
            Creando {r.creados} de {r.sujetos_activos}
          </strong>
          {r.minutos_restantes > 0 && ` · quedan ~${r.minutos_restantes} min`}
          <span style={ESTILO_MOTIVO}> · se actualiza solo</span>
        </p>
      )}

      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
        <Contador etiqueta="Operativos" valor={r.operativos} color="#1a7f37" />
        <Contador etiqueta="Funcionando, incompleto" valor={r.degradados} color="#9a6700" />
        <Contador etiqueta="Esperando información" valor={r.esperando_informacion} color="#9a6700" />
        <Contador etiqueta="Creándose" valor={r.listos_para_crear + r.creando} />
        <Contador etiqueta="Esperando límite de GitHub" valor={r.esperando_limite} color="#9a6700" />
        <Contador etiqueta="Con problemas" valor={conProblemas} color={conProblemas ? "#cf222e" : undefined} />
        <Contador etiqueta="No accesibles en GitHub" valor={r.inaccesibles} />
        <Contador etiqueta="Fuera de alcance" valor={r.fuera_de_alcance} />
        <Contador etiqueta="Archivados" valor={r.archivados} />
      </div>
      {conProblemas > 0 && (
        <p style={ESTILO_MOTIVO}>
          Con problemas: {r.bloqueados} bloqueados · {r.error_transitorio} reintentando · {r.error_permanente} requieren tu
          acción.
        </p>
      )}

      {datos.filas.length === 0 ? (
        <p>Todavía no hay estudiantes en esta tarea. Se agregan solos tras la próxima sincronización.</p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>Estudiante</th>
                <th>Repositorio</th>
                <th>Estado</th>
                <th>Motivo</th>
                <th>Acceso del estudiante</th>
                <th>Equipo docente</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {datos.filas.map((f) => (
                <tr key={f.repositorio_id} style={{ opacity: f.sujeto_activo ? 1 : 0.6 }}>
                  <td>
                    {f.sujeto}
                    {f.cuenta_github && <div style={ESTILO_MOTIVO}>@{f.cuenta_github}</div>}
                  </td>
                  <td>
                    {f.url_html ? (
                      <a href={f.url_html} target="_blank" rel="noreferrer">
                        <code>{f.nombre}</code>
                      </a>
                    ) : (
                      <code>{f.nombre}</code>
                    )}
                    {f.reemplaza_a_id && <div style={ESTILO_MOTIVO}>sustituye a un repositorio anterior</div>}
                  </td>
                  <td style={{ color: colorEstadoRepositorio(f.estado), fontWeight: 600 }}>
                    {textoEstadoRepositorio(f.estado)}
                    {f.estado === "ERROR_TRANSITORIO" && f.proximo_intento_en && (
                      <div style={ESTILO_MOTIVO}>próximo intento {fechaLegible(f.proximo_intento_en)}</div>
                    )}
                  </td>
                  <td>
                    {f.motivo ? textoMotivoRepositorio(f.motivo) : "—"}
                    {f.error_mensaje_literal && <div style={ESTILO_MOTIVO}>{f.error_mensaje_literal}</div>}
                    {!f.sujeto_activo && <div style={ESTILO_MOTIVO}>Ya no es parte de la tarea en Canvas</div>}
                  </td>
                  <td>
                    {f.acceso_estado ? textoEstadoAcceso(f.acceso_estado) : "—"}
                    {f.acceso_error && <div style={ESTILO_MOTIVO}>{f.acceso_error}</div>}
                  </td>
                  <td>{f.acceso_docente ? textoAccesoDocente(f.acceso_docente) : "—"}</td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    {["ERROR_PERMANENTE", "ERROR_TRANSITORIO", "BLOQUEADO", "ESPERANDO_LIMITE"].includes(f.estado) && (
                      <button onClick={() => onReintentar(f)}>Reintentar</button>
                    )}
                    {f.estado === "INACCESIBLE" && <button onClick={() => onSustituir(f)}>Sustituir</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

/** SPEC 09 S9.5, modo lectura: «Cierre: ... · Sección 2: ... · N excepciones». */
export function LineaFechas({ cursoId, tareaId }: { cursoId: string; tareaId: string }) {
  const [fechas, setFechas] = useState<FechasEntrega[] | null>(null);

  useEffect(() => {
    obtenerFechasEntregas(cursoId, tareaId).then(setFechas);
  }, [cursoId, tareaId]);

  if (!fechas || fechas.length === 0) return null;
  return (
    <div style={{ marginTop: "0.75rem" }}>
      {fechas.map((f) => (
        <p key={f.entrega_id} style={{ margin: "0.25rem 0" }}>
          <strong>
            {textoTipoEntrega(f.tipo)} {f.orden}
          </strong>{" "}
          · Cierre: {f.cierre_base}
          {f.excepciones.map((e, i) => (
            <span key={i}>
              {" "}
              · {e.etiqueta}: {e.fecha}
            </span>
          ))}
          {f.sujetos_sin_fecha > 0 && <span style={ESTILO_MOTIVO}> · {f.sujetos_sin_fecha} sin fecha de cierre</span>}
        </p>
      ))}
    </div>
  );
}
