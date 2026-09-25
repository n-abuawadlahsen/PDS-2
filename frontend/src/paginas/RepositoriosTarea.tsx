import { useEffect, useState } from "react";
import {
  obtenerFechasEntregas,
  obtenerHistorialFechas,
  obtenerRepositoriosTarea,
  reintentarRepositorio,
  sustituirRepositorio,
  type FechasEntrega,
  type FilaRepositorio,
  type HistorialFechasSujeto,
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
                <th>Estudiante o grupo</th>
                <th>Repositorio</th>
                <th>Estado</th>
                <th>Motivo</th>
                <th>Acceso de los estudiantes</th>
                <th>Equipo docente</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {datos.filas.map((f) => (
                <tr key={f.repositorio_id} style={{ opacity: f.sujeto_activo ? 1 : 0.6 }}>
                  <td>
                    {f.sujeto}
                    {f.sujeto_tipo === "ESTUDIANTE" && f.cuenta_github && (
                      <div style={ESTILO_MOTIVO}>@{f.cuenta_github}</div>
                    )}
                    {f.sujeto_tipo === "GRUPO" && (
                      <div style={ESTILO_MOTIVO}>
                        {f.integrantes.length === 1 ? "1 integrante" : `${f.integrantes.length} integrantes`}
                      </div>
                    )}
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
                    {f.sujeto_tipo === "GRUPO" ? (
                      f.integrantes.length === 0 ? (
                        "—"
                      ) : (
                        <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
                          {f.integrantes.map((i) => (
                            <li key={i.estudiante_id}>
                              {i.nombre}
                              {i.cuenta_github && <span style={ESTILO_MOTIVO}> @{i.cuenta_github}</span>}
                              {": "}
                              {i.acceso_estado ? textoEstadoAcceso(i.acceso_estado) : "sin acceso todavía"}
                              {i.acceso_error && <div style={ESTILO_MOTIVO}>{i.acceso_error}</div>}
                            </li>
                          ))}
                        </ul>
                      )
                    ) : (
                      <>
                        {f.acceso_estado ? textoEstadoAcceso(f.acceso_estado) : "—"}
                        {f.acceso_error && <div style={ESTILO_MOTIVO}>{f.acceso_error}</div>}
                      </>
                    )}
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
        <FechasDeUnaEntrega key={f.entrega_id} cursoId={cursoId} fechas={f} />
      ))}
    </div>
  );
}

/** S9.5: «Cierre: ... · Sección 2: ... · N excepciones», con las excepciones
 * desplegables (sujeto, fecha, origen y override copiable) y la insignia
 * «fecha ambigua» con sus candidatas (CA-9.5-03). */
function FechasDeUnaEntrega({ cursoId, fechas: f }: { cursoId: string; fechas: FechasEntrega }) {
  const [historial, setHistorial] = useState<HistorialFechasSujeto[] | null>(null);
  const secciones = f.excepciones.filter((e) => e.origen === "SECCION");
  const otras = f.excepciones.filter((e) => e.origen !== "SECCION");
  return (
    <div style={{ margin: "0.25rem 0" }}>
      <strong>
        {textoTipoEntrega(f.tipo)} {f.orden}
      </strong>{" "}
      · Cierre: {f.cierre_base}
      {secciones.map((e) => (
        <span key={e.canvas_override_id ?? e.etiqueta}>
          {" "}
          · {e.etiqueta}: {e.fecha}
        </span>
      ))}
      {f.sujetos_sin_fecha > 0 && <span style={ESTILO_MOTIVO}> · {f.sujetos_sin_fecha} sin fecha de cierre</span>}
      {otras.length > 0 && (
        <details>
          <summary>{otras.length === 1 ? "1 excepción" : `${otras.length} excepciones`}</summary>
          <ul>
            {otras.map((e) => (
              <li key={e.canvas_override_id ?? e.etiqueta}>
                {e.sujetos.join(", ") || "nadie del curso"} — {e.fecha} · {e.etiqueta}
                {e.canvas_override_id !== null && <Override id={e.canvas_override_id} />}
              </li>
            ))}
          </ul>
        </details>
      )}
      {f.ambiguas.map((a) => (
        <details key={a.sujeto_id}>
          <summary>
            <span style={{ background: "#fff3cd", padding: "0 0.3rem" }}>fecha ambigua</span> {a.sujeto}: {a.fecha}
          </summary>
          <ul>
            {a.candidatas.map((c, i) => (
              <li key={i}>
                {c.etiqueta}: {c.fecha}
                {c.canvas_override_id !== null && <Override id={c.canvas_override_id} />}
              </li>
            ))}
          </ul>
          <p style={ESTILO_MOTIVO}>
            Se usa la más tardía: capturar antes de tiempo destruye trabajo legítimo.
          </p>
        </details>
      ))}
      <div>
        <button
          style={{ fontSize: "0.85rem" }}
          onClick={async () => setHistorial(historial ? null : await obtenerHistorialFechas(cursoId, f.entrega_id))}
        >
          {historial ? "Ocultar historial de fechas" : "Ver historial de fechas"}
        </button>
        {historial && (
          <table style={{ fontSize: "0.85rem" }}>
            <thead>
              <tr>
                <th>Estudiante o grupo</th>
                <th>Fecha de cierre</th>
                <th>Origen</th>
                <th>Vigencia</th>
              </tr>
            </thead>
            <tbody>
              {historial.flatMap((h) =>
                h.fechas.map((x, i) => (
                  <tr key={`${h.sujeto_id}-${i}`} style={{ opacity: x.estado === "VIGENTE" ? 1 : 0.6 }}>
                    <td>{i === 0 ? h.sujeto : ""}</td>
                    <td>
                      {x.fecha}
                      {x.ambigua && <span style={ESTILO_MOTIVO}> (ambigua)</span>}
                    </td>
                    <td>
                      {x.etiqueta}
                      {x.override_titulo && <span style={ESTILO_MOTIVO}> «{x.override_titulo}»</span>}
                      {x.override_retirado && <span style={ESTILO_MOTIVO}> (ya no existe en Canvas)</span>}
                    </td>
                    <td>
                      {x.estado === "VIGENTE"
                        ? `vigente desde ${fechaLegible(x.calculada_en)}`
                        : `reemplazada el ${fechaLegible(x.vigente_hasta)}`}
                    </td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function Override({ id }: { id: number }) {
  return (
    <>
      {" "}
      <code>{id}</code>{" "}
      <button
        style={{ fontSize: "0.75rem" }}
        title="Copiar el identificador del override de Canvas"
        onClick={() => navigator.clipboard?.writeText(String(id))}
      >
        copiar
      </button>
    </>
  );
}
