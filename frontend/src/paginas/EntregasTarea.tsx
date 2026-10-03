import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  accionVersion,
  registrarVersiones,
  urlApi,
  type AccionVersion,
  type FichaVersion,
  type ProgresoCaptura,
  type TareaDetalle,
  type VersionEntrega,
} from "../lib/api";
import {
  fechaLegible,
  textoAdvertenciaVersion,
  textoEstadoCaptura,
  textoEstadoEtiqueta,
  textoMotivoVersion,
  textoOrigenCaptura,
  textoTipoEntrega,
} from "../lib/textosTarea";
import { CierreTarea } from "./CierreTarea";
import { LineaFechas } from "./RepositoriosTarea";

import { consultarOperacion } from "../lib/apiOperacion";
import { useCurso, useSesion } from "../components/Layout";
import {
  Aviso,
  Cabecera,
  Cargando,
  ErrorCarga,
  Mensajes,
  Tabla,
  Vacio,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";

const ESTILO_MOTIVO = {
  fontSize: "0.85rem",
  color: "var(--color-text-secondary)",
} as const;
const REGLA_DE_CORTE =
  "Se registra el último commit cuya fecha de committer es anterior o igual a la fecha efectiva de cierre, en UTC.";

/** `/cursos/{id}/tareas/{tid}/entregas` (SPEC 13 S13.3.3; SPEC 09 S9.6-S9.9):
 * fechas con excepciones, estado de captura por sujeto y acceso directo a la
 * versión que corresponde revisar. Nada de esta pantalla llama a GitHub. */
export function EntregasTarea() {
  const { cursoId, tareaId } = useParams<{
    cursoId: string;
    tareaId: string;
  }>();
  const { puede } = useCurso();
  const { capacidades } = useSesion();
  const [parametros, setParametros] = useSearchParams();
  const consulta = useConsulta(
    `entregas-tarea-${cursoId}-${tareaId}`,
    (signal) =>
      consultarOperacion<TareaDetalle>(
        `/api/cursos/${cursoId}/tareas/${tareaId}`,
        { signal },
      ),
  );
  const tarea = consulta.datos;
  const preferida = tarea?.entregas.find(
    (e) => e.id === parametros.get("entrega"),
  );
  const entregaId =
    preferida?.id ??
    tarea?.entregas.find((e) => e.tipo === "FINAL")?.id ??
    tarea?.entregas[0]?.id;
  const captura = useConsulta(
    `captura-${cursoId}-${entregaId}`,
    (signal) =>
      entregaId
        ? consultarOperacion<ProgresoCaptura>(
            `/api/cursos/${cursoId}/entregas/${entregaId}/progreso-captura`,
            { signal },
          )
        : Promise.resolve(null),
    10_000,
  );
  const progreso = captura.datos;
  const [sujetoId, setSujetoId] = useState<string | null>(null);
  const ficha = useConsulta(
    `ficha-${cursoId}-${entregaId}-${sujetoId}`,
    (signal) =>
      entregaId && sujetoId
        ? consultarOperacion<FichaVersion>(
            `/api/cursos/${cursoId}/entregas/${entregaId}/sujetos/${sujetoId}/version`,
            { signal },
          )
        : Promise.resolve(null),
  );
  const op = useOperacion();
  const confirmar = useConfirmar();
  function seleccionarEntrega(id: string) {
    setSujetoId(null);
    const nuevos = new URLSearchParams(parametros);
    nuevos.set("entrega", id);
    setParametros(nuevos);
  }
  async function ejecutar(id: string, accion: AccionVersion) {
    if (!cursoId || !entregaId) return;
    await op.ejecutar(async () => {
      const r = await accionVersion(cursoId, entregaId, id, accion);
      if (!r.ok) throw new Error(r.error ?? "No se pudo registrar la versión.");
      captura.recargar();
      ficha.recargar();
    }, "Versión registrada. La etiqueta de GitHub se crea en segundo plano; las versiones anteriores se conservan.");
  }
  async function onRegistrarTrasCierre() {
    if (!cursoId || !entregaId || !puede("tarea.administrar")) return;
    if (
      !(await confirmar({
        titulo: "Registrar versiones después del cierre",
        descripcion:
          "Se registrará la evidencia de esta entrega usando las fechas de cierre de Canvas. Podrás consultar su progreso por estudiante o grupo.",
        accion: "Registrar versiones",
      }))
    )
      return;
    await op.ejecutar(async () => {
      const r = await registrarVersiones(cursoId, entregaId);
      if (!r.ok || !r.datos)
        throw new Error(r.error ?? "No se pudo iniciar la captura.");
      op.setMensaje(
        `Se solicitaron ${r.datos.encoladas} versiones con la fecha de cierre de Canvas.`,
      );
      captura.recargar();
    });
  }
  if (!cursoId || !tareaId || !tarea)
    return consulta.error ? (
      <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
    ) : (
      <Cargando />
    );

  return (
    <div className="stack">
      <p>
        <Link to={`/cursos/${cursoId}/tareas/${tareaId}`}>
          ← {tarea.nombre}
        </Link>
      </p>
      <Cabecera
        titulo="Entregas y versiones"
        descripcion="Revisa las fechas de cierre y la evidencia registrada para cada estudiante o grupo."
      />
      <p style={ESTILO_MOTIVO}>{REGLA_DE_CORTE}</p>
      <Mensajes {...op} />
      {captura.error && (
        <ErrorCarga error={captura.error} reintentar={captura.recargar} />
      )}
      {ficha.error && (
        <ErrorCarga error={ficha.error} reintentar={ficha.recargar} />
      )}
      {ficha.cargando && sujetoId && (
        <Cargando texto="Consultando versiones…" />
      )}

      <section className="panel">
        <h2>Fechas de cierre</h2>
        <LineaFechas cursoId={cursoId} tareaId={tareaId} />
      </section>

      <section className="panel">
        <h2>Versiones registradas</h2>
        <div className="actions">
          {tarea.entregas.map((e) => (
            <button
              key={e.id}
              disabled={e.id === entregaId}
              aria-pressed={e.id === entregaId}
              onClick={() => seleccionarEntrega(e.id)}
              style={{ marginRight: "0.5rem" }}
            >
              {textoTipoEntrega(e.tipo)} {e.orden}: {e.nombre}
            </button>
          ))}
        </div>
        {!tarea.entregas.length && (
          <Vacio>Esta tarea todavía no tiene entregas vinculadas.</Vacio>
        )}
        {captura.cargando && !progreso && entregaId && (
          <Cargando texto="Consultando capturas…" />
        )}
        {progreso && (
          <>
            {progreso.estado_validacion === "VINCULADA_TRAS_EL_CIERRE" && (
              <div
                style={{
                  background: "var(--color-warning-background)",
                  padding: "0.75rem",
                }}
              >
                <p>
                  Versiones no registradas: la fecha de cierre ya había pasado
                  al vincular.
                </p>
                {puede("tarea.administrar") && (
                  <button
                    disabled={op.ocupado}
                    onClick={() => void onRegistrarTrasCierre()}
                  >
                    Registrar ahora las versiones con la fecha de cierre de
                    Canvas
                  </button>
                )}
              </div>
            )}
            <p>
              Registrando versiones: <strong>{progreso.registradas}</strong> de{" "}
              {progreso.vencidas} con la fecha vencida
              {progreso.capturas_tardias > 0 && (
                <span style={ESTILO_MOTIVO}>
                  {" "}
                  · {progreso.capturas_tardias} con captura tardía
                </span>
              )}
            </p>
            <Tabla etiqueta="Versiones por estudiante o grupo">
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
                      abierta={sujetoId === f.sujeto_id ? ficha.datos : null}
                      ocupado={op.ocupado}
                      onAbrir={() =>
                        setSujetoId(
                          sujetoId === f.sujeto_id ? null : f.sujeto_id,
                        )
                      }
                      onAccion={(accion) => ejecutar(f.sujeto_id, accion)}
                    />
                  ))}
                </tbody>
              </table>
            </Tabla>
          </>
        )}
      </section>

      {tarea.estado !== "BORRADOR" &&
        capacidades?.banderas.includes("tarea_archivado") && (
          <CierreTarea cursoId={cursoId} tareaId={tareaId} />
        )}
    </div>
  );
}

function FilaSujeto({
  fila,
  abierta,
  onAbrir,
  onAccion,
  ocupado,
}: {
  fila: ProgresoCaptura["filas"][number];
  abierta: FichaVersion | null;
  onAbrir: () => void;
  onAccion: (accion: AccionVersion) => void;
  ocupado: boolean;
}) {
  const { curso } = useCurso();
  const v = fila.version;
  return (
    <>
      <tr>
        <td>{fila.sujeto}</td>
        <td>
          {/^\d{4}-\d{2}-\d{2}T/.test(fila.fecha)
            ? fechaLegible(fila.fecha, curso.zona_horaria)
            : fila.fecha}
        </td>
        <td>
          {textoEstadoCaptura(fila.estado_captura)}
          {v?.motivo && (
            <div style={ESTILO_MOTIVO}>{textoMotivoVersion(v.motivo)}</div>
          )}
          {v?.captura_tardia_minutos && (
            <div style={ESTILO_MOTIVO}>
              captura tardía ({v.captura_tardia_minutos} min)
            </div>
          )}
          {v && v.origen_captura !== "AUTOMATICA" && (
            <div style={ESTILO_MOTIVO}>manual</div>
          )}
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
          {fila.estado_captura !== "NO_APLICA" &&
            fila.estado_captura !== "PENDIENTE_DE_CIERRE" && (
              <button onClick={onAbrir}>
                {abierta ? "Cerrar" : "Ver versiones"}
              </button>
            )}
        </td>
      </tr>
      {abierta && (
        <tr>
          <td colSpan={5}>
            <Ficha
              ficha={abierta}
              estadoCaptura={fila.estado_captura}
              onAccion={onAccion}
              ocupado={ocupado}
            />
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
  ocupado,
}: {
  ficha: FichaVersion;
  estadoCaptura: string;
  onAccion: (accion: AccionVersion) => void;
  ocupado: boolean;
}) {
  const { contexto, puede, curso } = useCurso();
  const administra = puede("tarea.administrar");
  const profesor = administra && contexto.rol === "PROFESOR";
  const [accion, setAccion] = useState<AccionVersion["tipo"] | null>(null);
  const [motivo, setMotivo] = useState("");
  const [fecha, setFecha] = useState("");
  const [sha, setSha] = useState("");
  const puedeCapturarAhora =
    !ficha.vigente ||
    ficha.vigente.estado === "SIN_REPOSITORIO" ||
    estadoCaptura === "REGISTRANDO";

  function confirmar() {
    if (accion === "capturar-ahora")
      onAccion({ tipo: accion, motivo_manual: motivo });
    if (accion === "recapturar")
      onAccion({
        tipo: accion,
        motivo_manual: motivo,
        fecha_corte: new Date(fecha).toISOString(),
      });
    if (accion === "fijar-sha")
      onAccion({ tipo: accion, motivo_manual: motivo, sha: sha.trim() });
  }

  return (
    <div
      style={{
        padding: "0.5rem 1rem",
        borderLeft: "3px solid var(--color-border)",
      }}
    >
      {ficha.vigente ? (
        <DetalleVersion
          version={ficha.vigente}
          accesoDocente={ficha.acceso_docente}
        />
      ) : (
        <p>Todavía no hay versión registrada.</p>
      )}
      {ficha.anteriores.length > 0 && (
        <details>
          <summary>
            Versiones anteriores ({ficha.anteriores.length}); ninguna se
            descarta
          </summary>
          {[...ficha.anteriores].reverse().map((v) => (
            <DetalleVersion
              key={v.id}
              version={v}
              accesoDocente={ficha.acceso_docente}
            />
          ))}
        </details>
      )}
      <p>
        {administra && puedeCapturarAhora && (
          <button onClick={() => setAccion("capturar-ahora")}>
            Capturar ahora
          </button>
        )}{" "}
        {profesor && (
          <button onClick={() => setAccion("recapturar")}>
            Recapturar con otra fecha de corte
          </button>
        )}{" "}
        {profesor && (
          <button onClick={() => setAccion("fijar-sha")}>
            Fijar esta versión en un commit concreto
          </button>
        )}
        <span style={ESTILO_MOTIVO}>
          {" "}
          Las dos últimas son solo para profesores.
        </span>
      </p>
      {accion && administra && (
        <fieldset>
          <legend>
            {accion === "capturar-ahora"
              ? "Capturar ahora"
              : accion === "recapturar"
                ? "Recapturar con otra fecha de corte"
                : "Fijar en un commit concreto"}
          </legend>
          <Aviso>
            Esta acción registra una nueva versión. La evidencia anterior y las
            notas ya publicadas se conservan; no se modifica automáticamente la
            calificación.
          </Aviso>
          {accion === "capturar-ahora" &&
            ficha.vigente?.estado === "SIN_REPOSITORIO" && (
              <p style={ESTILO_MOTIVO}>
                Como no tenía repositorio al cierre, se captura con la fecha y
                hora de este momento.
              </p>
            )}
          {accion === "recapturar" && (
            <label>
              Fecha de corte con zona horaria
              <input
                type="text"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                placeholder="2026-10-06T16:00:00-03:00"
                aria-describedby="fecha-corte-ayuda"
              />
              <span id="fecha-corte-ayuda" className="help">
                Incluye Z para UTC o el desplazamiento horario. La zona del
                curso es {curso.zona_horaria}. Ejemplo:
                2026-10-06T16:00:00-03:00.
              </span>
            </label>
          )}
          {accion === "fijar-sha" && (
            <label>
              SHA del commit{" "}
              <input
                maxLength={40}
                value={sha}
                onChange={(e) => setSha(e.target.value)}
                size={42}
              />
            </label>
          )}
          <p>
            <label>
              Motivo (obligatorio, queda en la bitácora){" "}
              <input
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                size={50}
              />
            </label>
          </p>
          <button
            disabled={
              ocupado ||
              motivo.trim().length < 10 ||
              (accion === "recapturar" &&
                (!/[zZ]|[+-]\d{2}:\d{2}$/.test(fecha) ||
                  Number.isNaN(new Date(fecha).getTime()))) ||
              (accion === "fijar-sha" && !/^[a-fA-F0-9]{40}$/.test(sha.trim()))
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

function DetalleVersion({
  version: v,
  accesoDocente,
}: {
  version: VersionEntrega;
  accesoDocente: string | null;
}) {
  const { curso } = useCurso();
  return (
    <div style={{ margin: "0.5rem 0", opacity: v.vigente ? 1 : 0.75 }}>
      <strong>
        v{v.intento} · {v.vigente ? "Vigente" : "Anterior"} ·{" "}
        {textoEstadoCaptura(v.estado)}
      </strong>
      {!v.vigente && v.motivo && (
        <span style={ESTILO_MOTIVO}> · {textoMotivoVersion(v.motivo)}</span>
      )}
      <div style={ESTILO_MOTIVO}>
        Corte: {fechaLegible(v.fecha_corte, curso.zona_horaria)} · registrada el{" "}
        {fechaLegible(v.capturada_en, curso.zona_horaria)} ·{" "}
        {textoOrigenCaptura(v.origen_captura)}
        {v.creada_por && ` por ${v.creada_por}`}
      </div>
      {v.motivo_manual && (
        <div style={ESTILO_MOTIVO}>Motivo: «{v.motivo_manual}»</div>
      )}
      {v.commit_sha && (
        <div>
          <code>{v.commit_sha}</code>{" "}
          {v.commit_mensaje && (
            <span style={ESTILO_MOTIVO}>«{v.commit_mensaje}»</span>
          )}
        </div>
      )}
      {v.tag_nombre && (
        <div style={ESTILO_MOTIVO}>
          <code>{v.tag_nombre}</code>: {textoEstadoEtiqueta(v.tag_estado)}
          {v.tag_error && ` (${v.tag_error})`}
        </div>
      )}
      {v.advertencias.map((a) => (
        <div
          key={a}
          style={{
            background: "var(--color-warning-background)",
            padding: "0.2rem 0.4rem",
            marginTop: "0.2rem",
          }}
        >
          {textoAdvertenciaVersion(a)}
        </div>
      ))}
      {v.commit_sha && (
        <p>
          {accesoDocente === "CONCEDIDO" ? (
            <>
              {v.enlaces.arbol && (
                <a
                  href={urlApi(v.enlaces.arbol)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Ver el código de esta versión
                </a>
              )}
              {v.enlaces.comparacion && (
                <>
                  {" · "}
                  <a
                    href={urlApi(v.enlaces.comparacion)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Comparar ({v.comparacion_base})
                  </a>
                </>
              )}
              {v.advertencias.includes("SIN_CAMBIOS_RESPECTO_A_LA_ANTERIOR") &&
                " · sin cambios respecto a la anterior"}
              {v.enlaces.zip && (
                <>
                  {" · "}
                  <a
                    href={urlApi(v.enlaces.zip)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Descargar esta versión
                  </a>
                </>
              )}
              {!v.comparacion_base && (
                <span style={ESTILO_MOTIVO}>
                  {" "}
                  · sin línea base registrada para este repositorio
                </span>
              )}
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
