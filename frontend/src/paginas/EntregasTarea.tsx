import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  accionVersion,
  obtenerFichaVersion,
  obtenerProgresoCaptura,
  obtenerTarea,
  registrarVersiones,
  urlApi,
  type AccionVersion,
  type FichaVersion,
  type ProgresoCaptura,
  type TareaDetalle,
  type VersionEntrega,
} from "../lib/api";
import {
  textoAdvertenciaVersion,
  textoEstadoCaptura,
  textoEstadoEtiqueta,
  textoMotivoVersion,
  textoOrigenCaptura,
  textoTipoEntrega,
} from "../lib/textosTarea";
import { CierreTarea } from "./CierreTarea";
import { LineaFechas } from "./RepositoriosTarea";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "var(--color-text-secondary)" } as const;
const ESTILO_ERROR = { background: "var(--color-error-background)", padding: "0.75rem" } as const;
const REGLA_DE_CORTE =
  "Se registra el último commit cuya fecha de committer es anterior o igual a la fecha efectiva de cierre, en UTC.";

/** `/cursos/{id}/tareas/{tid}/entregas` (SPEC 13 S13.3.3; SPEC 09 S9.6-S9.9):
 * fechas con excepciones, estado de captura por sujeto y acceso directo a la
 * versión que corresponde revisar. Nada de esta pantalla llama a GitHub. */
export function EntregasTarea() {
  const { cursoId, tareaId } = useParams<{ cursoId: string; tareaId: string }>();
  const [tarea, setTarea] = useState<TareaDetalle | null>(null);
  const [entregaId, setEntregaId] = useState<string | null>(null);
  const [progreso, setProgreso] = useState<ProgresoCaptura | null>(null);
  const [ficha, setFicha] = useState<{ sujetoId: string; datos: FichaVersion } | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cursoId || !tareaId) return;
    obtenerTarea(cursoId, tareaId).then((t) => {
      setTarea(t);
      const final = t.entregas.find((e) => e.tipo === "FINAL") ?? t.entregas[0];
      setEntregaId((actual) => actual ?? final?.id ?? null);
    });
  }, [cursoId, tareaId]);

  async function cargarProgreso() {
    if (!cursoId || !entregaId) return;
    setProgreso(await obtenerProgresoCaptura(cursoId, entregaId));
  }

  useEffect(() => {
    setFicha(null);
    cargarProgreso();
    // Sondeo cada 10 s, como la pestaña de repositorios (nunca SSE ni WebSocket).
    const intervalo = setInterval(cargarProgreso, 10_000);
    return () => clearInterval(intervalo);
  }, [cursoId, entregaId]);

  async function abrirFicha(sujetoId: string) {
    if (!cursoId || !entregaId) return;
    if (ficha?.sujetoId === sujetoId) {
      setFicha(null);
      return;
    }
    setFicha({ sujetoId, datos: await obtenerFichaVersion(cursoId, entregaId, sujetoId) });
  }

  async function ejecutar(sujetoId: string, accion: AccionVersion) {
    if (!cursoId || !entregaId) return;
    setMensaje(null);
    setError(null);
    const r = await accionVersion(cursoId, entregaId, sujetoId, accion);
    if (r.ok) {
      setMensaje("Versión registrada. La etiqueta en GitHub se crea en segundo plano.");
      await cargarProgreso();
      setFicha({ sujetoId, datos: await obtenerFichaVersion(cursoId, entregaId, sujetoId) });
    } else {
      setError(r.error);
    }
  }

  async function onRegistrarTrasCierre() {
    if (!cursoId || !entregaId) return;
    const r = await registrarVersiones(cursoId, entregaId);
    if (r.ok && r.datos) {
      setMensaje(`Registrando ${r.datos.encoladas} versiones con la fecha de cierre de Canvas.`);
      await cargarProgreso();
    } else {
      setError(r.error);
    }
  }

  if (!cursoId || !tareaId || !tarea) return <p>Cargando…</p>;
  return (
    <main>
      <p>
        <Link to={`/cursos/${cursoId}/tareas/${tareaId}`}>← {tarea.nombre}</Link>
      </p>
      <h1>Entregas y versiones</h1>
      <p style={ESTILO_MOTIVO}>{REGLA_DE_CORTE}</p>
      {mensaje && <p style={{ background: "var(--color-success-background)", padding: "0.75rem" }}>{mensaje}</p>}
      {error && <p style={ESTILO_ERROR}>{error}</p>}

      <section>
        <h2>Fechas de cierre</h2>
        <LineaFechas cursoId={cursoId} tareaId={tareaId} />
      </section>

      <section>
        <h2>Versiones registradas</h2>
        <p>
          {tarea.entregas.map((e) => (
            <button
              key={e.id}
              disabled={e.id === entregaId}
              onClick={() => setEntregaId(e.id)}
              style={{ marginRight: "0.5rem" }}
            >
              {textoTipoEntrega(e.tipo)} {e.orden}: {e.nombre}
            </button>
          ))}
        </p>
        {progreso && (
          <>
            {progreso.estado_validacion === "VINCULADA_TRAS_EL_CIERRE" && (
              <div style={{ background: "var(--color-warning-background)", padding: "0.75rem" }}>
                <p>Versiones no registradas: la fecha de cierre ya había pasado al vincular.</p>
                <button onClick={onRegistrarTrasCierre}>
                  Registrar ahora las versiones con la fecha de cierre de Canvas
                </button>
              </div>
            )}
            <p>
              Registrando versiones: <strong>{progreso.registradas}</strong> de {progreso.vencidas} con la fecha
              vencida
              {progreso.capturas_tardias > 0 && (
                <span style={ESTILO_MOTIVO}> · {progreso.capturas_tardias} con captura tardía</span>
              )}
            </p>
            <table>
              <thead>
                <tr>
                  <th>Estudiante o grupo</th>
                  <th>Fecha de cierre</th>
                  <th>Estado de captura</th>
                  <th>Commit</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {progreso.filas.map((f) => (
                  <FilaSujeto
                    key={f.sujeto_id}
                    fila={f}
                    abierta={ficha?.sujetoId === f.sujeto_id ? ficha.datos : null}
                    onAbrir={() => abrirFicha(f.sujeto_id)}
                    onAccion={(accion) => ejecutar(f.sujeto_id, accion)}
                  />
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>

      {tarea.estado !== "BORRADOR" && <CierreTarea cursoId={cursoId} tareaId={tareaId} />}
    </main>
  );
}

function FilaSujeto({
  fila,
  abierta,
  onAbrir,
  onAccion,
}: {
  fila: ProgresoCaptura["filas"][number];
  abierta: FichaVersion | null;
  onAbrir: () => void;
  onAccion: (accion: AccionVersion) => void;
}) {
  const v = fila.version;
  return (
    <>
      <tr>
        <td>{fila.sujeto}</td>
        <td>{fila.fecha}</td>
        <td>
          {textoEstadoCaptura(fila.estado_captura)}
          {v?.motivo && <div style={ESTILO_MOTIVO}>{textoMotivoVersion(v.motivo)}</div>}
          {v?.captura_tardia_minutos && (
            <div style={ESTILO_MOTIVO}>captura tardía ({v.captura_tardia_minutos} min)</div>
          )}
          {v && v.origen_captura !== "AUTOMATICA" && <div style={ESTILO_MOTIVO}>manual</div>}
        </td>
        <td>
          {v?.commit_sha && v.enlaces.arbol ? (
            <a href={urlApi(v.enlaces.arbol)} target="_blank" rel="noreferrer">
              <code>{v.commit_sha.slice(0, 7)}</code>
            </a>
          ) : (
            "—"
          )}
        </td>
        <td>
          {fila.estado_captura !== "NO_APLICA" && fila.estado_captura !== "PENDIENTE_DE_CIERRE" && (
            <button onClick={onAbrir}>{abierta ? "Cerrar" : "Ver versiones"}</button>
          )}
        </td>
      </tr>
      {abierta && (
        <tr>
          <td colSpan={5}>
            <Ficha ficha={abierta} estadoCaptura={fila.estado_captura} onAccion={onAccion} />
          </td>
        </tr>
      )}
    </>
  );
}

function Ficha({
  ficha,
  estadoCaptura,
  onAccion,
}: {
  ficha: FichaVersion;
  estadoCaptura: string;
  onAccion: (accion: AccionVersion) => void;
}) {
  const [accion, setAccion] = useState<AccionVersion["tipo"] | null>(null);
  const [motivo, setMotivo] = useState("");
  const [fecha, setFecha] = useState("");
  const [sha, setSha] = useState("");
  const puedeCapturarAhora =
    !ficha.vigente || ficha.vigente.estado === "SIN_REPOSITORIO" || estadoCaptura === "REGISTRANDO";

  function confirmar() {
    if (accion === "capturar-ahora") onAccion({ tipo: accion, motivo_manual: motivo });
    if (accion === "recapturar")
      onAccion({ tipo: accion, motivo_manual: motivo, fecha_corte: new Date(fecha).toISOString() });
    if (accion === "fijar-sha") onAccion({ tipo: accion, motivo_manual: motivo, sha });
  }

  return (
    <div style={{ padding: "0.5rem 1rem", borderLeft: "3px solid var(--color-border)" }}>
      {ficha.vigente ? (
        <DetalleVersion version={ficha.vigente} accesoDocente={ficha.acceso_docente} />
      ) : (
        <p>Todavía no hay versión registrada.</p>
      )}
      {ficha.anteriores.length > 0 && (
        <details>
          <summary>Versiones anteriores ({ficha.anteriores.length}); ninguna se descarta</summary>
          {[...ficha.anteriores].reverse().map((v) => (
            <DetalleVersion key={v.id} version={v} accesoDocente={ficha.acceso_docente} />
          ))}
        </details>
      )}
      <p>
        {puedeCapturarAhora && <button onClick={() => setAccion("capturar-ahora")}>Capturar ahora</button>}{" "}
        <button onClick={() => setAccion("recapturar")}>Recapturar con otra fecha de corte</button>{" "}
        <button onClick={() => setAccion("fijar-sha")}>Fijar esta versión en un commit concreto</button>
        <span style={ESTILO_MOTIVO}> Las dos últimas son solo para profesores.</span>
      </p>
      {accion && (
        <fieldset>
          <legend>
            {accion === "capturar-ahora"
              ? "Capturar ahora"
              : accion === "recapturar"
                ? "Recapturar con otra fecha de corte"
                : "Fijar en un commit concreto"}
          </legend>
          {accion === "capturar-ahora" && ficha.vigente?.estado === "SIN_REPOSITORIO" && (
            <p style={ESTILO_MOTIVO}>
              Como no tenía repositorio al cierre, se captura con la fecha y hora de este momento.
            </p>
          )}
          {accion === "recapturar" && (
            <label>
              Fecha de corte{" "}
              <input type="datetime-local" value={fecha} onChange={(e) => setFecha(e.target.value)} />
            </label>
          )}
          {accion === "fijar-sha" && (
            <label>
              SHA del commit <input value={sha} onChange={(e) => setSha(e.target.value)} size={42} />
            </label>
          )}
          <p>
            <label>
              Motivo (obligatorio, queda en la bitácora){" "}
              <input value={motivo} onChange={(e) => setMotivo(e.target.value)} size={50} />
            </label>
          </p>
          <button
            disabled={
              motivo.trim().length < 10 || (accion === "recapturar" && !fecha) || (accion === "fijar-sha" && !sha)
            }
            onClick={confirmar}
          >
            Confirmar
          </button>{" "}
          <button onClick={() => setAccion(null)}>Cancelar</button>
        </fieldset>
      )}
    </div>
  );
}

function DetalleVersion({ version: v, accesoDocente }: { version: VersionEntrega; accesoDocente: string | null }) {
  return (
    <div style={{ margin: "0.5rem 0", opacity: v.vigente ? 1 : 0.75 }}>
      <strong>
        v{v.intento} · {textoEstadoCaptura(v.estado)}
      </strong>
      {!v.vigente && v.motivo && <span style={ESTILO_MOTIVO}> · {textoMotivoVersion(v.motivo)}</span>}
      <div style={ESTILO_MOTIVO}>
        Corte: {v.fecha_corte} · registrada el {v.capturada_en} · {textoOrigenCaptura(v.origen_captura)}
        {v.creada_por && ` por ${v.creada_por}`}
      </div>
      {v.motivo_manual && <div style={ESTILO_MOTIVO}>Motivo: «{v.motivo_manual}»</div>}
      {v.commit_sha && (
        <div>
          <code>{v.commit_sha}</code> {v.commit_mensaje && <span style={ESTILO_MOTIVO}>«{v.commit_mensaje}»</span>}
        </div>
      )}
      {v.tag_nombre && (
        <div style={ESTILO_MOTIVO}>
          <code>{v.tag_nombre}</code>: {textoEstadoEtiqueta(v.tag_estado)}
          {v.tag_error && ` (${v.tag_error})`}
        </div>
      )}
      {v.advertencias.map((a) => (
        <div key={a} style={{ background: "var(--color-warning-background)", padding: "0.2rem 0.4rem", marginTop: "0.2rem" }}>
          {textoAdvertenciaVersion(a)}
        </div>
      ))}
      {v.commit_sha && (
        <p>
          {accesoDocente === "CONCEDIDO" ? (
            <>
              {v.enlaces.arbol && (
                <a href={urlApi(v.enlaces.arbol)} target="_blank" rel="noreferrer">
                  Ver el código de esta versión
                </a>
              )}
              {v.enlaces.comparacion && (
                <>
                  {" · "}
                  <a href={urlApi(v.enlaces.comparacion)} target="_blank" rel="noreferrer">
                    Comparar ({v.comparacion_base})
                  </a>
                </>
              )}
              {v.advertencias.includes("SIN_CAMBIOS_RESPECTO_A_LA_ANTERIOR") && " · sin cambios respecto a la anterior"}
              {v.enlaces.zip && (
                <>
                  {" · "}
                  <a href={urlApi(v.enlaces.zip)} target="_blank" rel="noreferrer">
                    Descargar esta versión
                  </a>
                </>
              )}
              {!v.comparacion_base && <span style={ESTILO_MOTIVO}> · sin línea base registrada para este repositorio</span>}
            </>
          ) : (
            <span style={ESTILO_MOTIVO}>
              {accesoDocente === "ERROR"
                ? "GitHub rechazó dar lectura al equipo docente; reintenta desde la pestaña de repositorios."
                : "Preparando tu acceso al repositorio: el enlace aparece cuando el equipo docente tenga lectura."}
            </span>
          )}
        </p>
      )}
    </div>
  );
}
