import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  API_BASE_URL,
  agregarNotaInterna,
  guardarBorradorCorreccion,
  marcarCorreccionLista,
  obtenerPantallaCorreccion,
  type PantallaCorreccion,
} from "../lib/api";
import { PanelPublicacion } from "./PanelPublicacion";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;
const ESTILO_AMBAR = { background: "#fff3cd", padding: "0.5rem 0.75rem" } as const;

type Rubrica = Record<string, { points?: number; rating_id?: string; comments?: string }>;

/** Pantalla de corrección (S12.8): dos columnas, sin pestañas. Solo quien
 * corrige (o un profesor) edita; los demás ven la fila. */
export function CorreccionSujeto() {
  const { cursoId, entregaId, sujetoId } = useParams<{ cursoId: string; entregaId: string; sujetoId: string }>();
  const navegar = useNavigate();
  const [datos, setDatos] = useState<PantallaCorreccion | null>(null);
  const [nota, setNota] = useState("");
  const [comentario, setComentario] = useState("");
  const [rubrica, setRubrica] = useState<Rubrica>({});
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    if (!cursoId || !entregaId || !sujetoId) return;
    const d = await obtenerPantallaCorreccion(cursoId, entregaId, sujetoId);
    setDatos(d);
    setNota(d?.borrador?.nota ?? "");
    setComentario(d?.borrador?.comentario ?? "");
    setRubrica((d?.borrador?.rubrica as Rubrica) ?? {});
  }, [cursoId, entregaId, sujetoId]);

  useEffect(() => {
    setMensaje(null);
    setError(null);
    cargar();
  }, [cargar]);

  const guardar = useCallback(async () => {
    if (!cursoId || !entregaId || !sujetoId || !datos?.borrador) return false;
    const r = await guardarBorradorCorreccion(cursoId, entregaId, sujetoId, {
      nota: nota || null,
      rubrica: Object.keys(rubrica).length ? rubrica : null,
      comentario: comentario || null,
      version: datos.borrador.version,
    });
    if (r.ok) {
      setMensaje("Borrador guardado.");
      setError(null);
      await cargar();
      return true;
    }
    setError(r.error);
    return false;
  }, [cursoId, entregaId, sujetoId, datos, nota, rubrica, comentario, cargar]);

  const lista = useCallback(async () => {
    if (!cursoId || !entregaId || !sujetoId) return;
    if (!(await guardar())) return;
    const r = await marcarCorreccionLista(cursoId, entregaId, sujetoId);
    if (r.ok) setMensaje("Marcada como lista para publicar.");
    else setError(r.error);
    await cargar();
  }, [cursoId, entregaId, sujetoId, guardar, cargar]);

  const ir = useCallback(
    (sujeto: string | null) => {
      if (sujeto && cursoId && entregaId) navegar(`/cursos/${cursoId}/correccion/${entregaId}/${sujeto}`);
    },
    [cursoId, entregaId, navegar],
  );

  useEffect(() => {
    // S12.7: atajos, desactivados mientras se escribe en un campo.
    function tecla(e: KeyboardEvent) {
      const t = e.target as HTMLElement;
      if (["INPUT", "TEXTAREA", "SELECT"].includes(t.tagName) || !datos) return;
      if (e.key === "j" || e.key === "ArrowRight") ir(datos.navegacion.siguiente);
      else if (e.key === "k" || e.key === "ArrowLeft") ir(datos.navegacion.anterior);
      else if (e.key === "n") ir(datos.navegacion.siguiente_sin_corregir);
      else if (e.key === "s" && datos.es_propietario) guardar();
      else if (e.key === "l" && datos.es_propietario) lista();
    }
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [datos, ir, guardar, lista]);

  if (!cursoId || !entregaId || !sujetoId || !datos) return <p>Cargando…</p>;
  const v = datos.version;
  const abrir = (destino: string) => `${API_BASE_URL}/api/cursos/${cursoId}/versiones/${v?.id}/abrir?destino=${destino}`;
  const editable = datos.es_propietario && !["PUBLICANDO", "PUBLICADA", "PUBLICADA_CON_ADVERTENCIA"].includes(datos.estado);

  return (
    <main style={{ maxWidth: 1200 }}>
      <p>
        <Link to={`/cursos/${cursoId}/correccion`}>← Corrección</Link> · {datos.navegacion.posicion} de {datos.navegacion.total}{" "}
        <button disabled={!datos.navegacion.anterior} onClick={() => ir(datos.navegacion.anterior)}>
          Anterior
        </button>{" "}
        <button disabled={!datos.navegacion.siguiente} onClick={() => ir(datos.navegacion.siguiente)}>
          Siguiente
        </button>{" "}
        <button
          onClick={() =>
            datos.navegacion.siguiente_sin_corregir
              ? ir(datos.navegacion.siguiente_sin_corregir)
              : setMensaje("No queda ninguna sin corregir en esta entrega.")
          }
        >
          Siguiente sin corregir
        </button>
      </p>
      <h1>
        {datos.sujeto.nombre} · {datos.entrega.nombre}
      </h1>
      <p style={ESTILO_MOTIVO}>
        {datos.entrega.tarea} · cierre {datos.entrega.fecha_efectiva ?? "sin fecha"} · {datos.etiqueta} · corrige{" "}
        {datos.corrector ?? "nadie todavía"}
        {datos.sujeto.integrantes.length > 1 && ` · integrantes: ${datos.sujeto.integrantes.join(", ")}`}
      </p>
      {!datos.publicable && datos.motivo_no_publicable && (
        <p style={{ background: "#f8d7da", padding: "0.5rem" }}>No publicable en Canvas: {datos.motivo_no_publicable}.</p>
      )}
      {datos.banderas.version_desactualizada && (
        <p style={ESTILO_AMBAR}>Hay una versión nueva registrada: revísala antes de publicar.</p>
      )}
      {datos.banderas.reclamo_abierto && <p style={ESTILO_AMBAR}>Hay un reclamo abierto.</p>}
      {mensaje && <p style={{ background: "#efe", padding: "0.5rem" }}>{mensaje}</p>}
      {error && <p style={{ background: "#fee", padding: "0.5rem" }}>{error}</p>}

      <div style={{ display: "flex", gap: "1.5rem", alignItems: "flex-start" }}>
        <section style={{ flex: "0 0 40%" }}>
          <h2>Versión revisada</h2>
          {!v ? (
            <p>Todavía no hay una versión registrada para esta entrega.</p>
          ) : v.estado === "SIN_COMMITS" ? (
            <p>No se registró ningún commit anterior a la fecha de cierre.</p>
          ) : (
            <>
              <p>
                Commit <code>{v.sha_corto}</code> · corte {v.fecha_corte}
                {v.tag && ` · etiqueta ${v.tag}`}
              </p>
              {datos.acceso_docente === "CONCEDIDO" ? (
                <p>
                  <a href={abrir("arbol")} target="_blank" rel="noreferrer">
                    Ver el código de esta versión
                  </a>{" "}
                  ·{" "}
                  <a href={abrir("comparacion")} target="_blank" rel="noreferrer">
                    Comparar con la anterior
                  </a>{" "}
                  ·{" "}
                  <a href={abrir("zip")} target="_blank" rel="noreferrer">
                    Descargar
                  </a>
                </p>
              ) : (
                <p style={ESTILO_AMBAR}>{datos.motivo_sin_enlace}</p>
              )}
              {v.repositorio && v.sha && (
                <pre style={{ background: "#f6f8fa", padding: "0.5rem", whiteSpace: "pre-wrap" }}>
                  {`git clone https://github.com/${v.repositorio}.git\ncd ${v.repositorio.split("/")[1]}\ngit checkout ${v.sha}`}
                </pre>
              )}
              <p style={ESTILO_MOTIVO}>Tu acceso es de sólo lectura; no podrás empujar cambios.</p>
              {datos.repositorio_estado === "INACCESIBLE" && (
                <p style={ESTILO_AMBAR}>Versión registrada; el repositorio ya no está accesible en GitHub.</p>
              )}
            </>
          )}
          {datos.historial.length > 0 && (
            <>
              <h2>Entregas anteriores</h2>
              <ul>
                {datos.historial.map((h) => (
                  <li key={h.entrega}>
                    {h.entrega}: {h.estado}
                    {h.nota_publicada && ` · nota ${h.nota_publicada}`}
                  </li>
                ))}
              </ul>
            </>
          )}
          <h2>En Canvas</h2>
          <ul>
            {datos.canvas.map((c) => (
              <li key={c.estudiante}>
                {c.estudiante}: {c.score !== null ? `nota ${c.score}` : "sin nota"}
              </li>
            ))}
          </ul>
        </section>

        <section style={{ flex: 1 }}>
          {datos.rubrica.criterios.length > 0 ? (
            <>
              <h2>Rúbrica</h2>
              {datos.rubrica.cambio_sin_revisar && (
                <p style={ESTILO_AMBAR}>La rúbrica cambió en Canvas desde que guardaste: revisa los criterios.</p>
              )}
              {datos.rubrica.criterios.map((c) => {
                const soloLectura = Boolean(c.learning_outcome_id || c.criterion_use_range);
                const valor = rubrica[c.id] ?? {};
                return (
                  <div key={c.id} style={{ marginBottom: "0.5rem", opacity: soloLectura ? 0.6 : 1 }}>
                    <strong>{c.description}</strong> ({c.points} pts){soloLectura && " · se evalúa en SpeedGrader"}
                    {!soloLectura && (
                      <div>
                        {(c.ratings ?? []).map((r) => (
                          <label key={r.id} style={{ marginRight: "0.75rem" }}>
                            <input
                              type="radio"
                              disabled={!editable}
                              name={c.id}
                              checked={valor.rating_id === r.id}
                              onChange={() => setRubrica({ ...rubrica, [c.id]: { ...valor, rating_id: r.id, points: r.points } })}
                            />{" "}
                            {r.description} ({r.points})
                          </label>
                        ))}
                        <input
                          type="number"
                          disabled={!editable}
                          value={valor.points ?? ""}
                          min={0}
                          max={c.points}
                          step="0.5"
                          style={{ width: 70 }}
                          onChange={(e) =>
                            setRubrica({ ...rubrica, [c.id]: { ...valor, points: Number(e.target.value), rating_id: undefined } })
                          }
                        />
                        {valor.points !== undefined && !valor.rating_id && <span style={ESTILO_MOTIVO}> puntos libres</span>}
                      </div>
                    )}
                  </div>
                );
              })}
              {datos.rubrica.suma_sugerida !== null && (
                <p style={ESTILO_MOTIVO}>Suma de la rúbrica: {datos.rubrica.suma_sugerida}</p>
              )}
            </>
          ) : (
            <p style={ESTILO_MOTIVO}>Esta tarea no tiene rúbrica en Canvas: solo nota y comentario.</p>
          )}
          <h2>Nota y comentario</h2>
          {datos.borrador === null ? (
            <p style={ESTILO_MOTIVO}>Esta corrección está asignada a otra persona: puedes verla, no editarla.</p>
          ) : (
            <>
              <label>
                Nota ({datos.entrega.grading_type === "pass_fail" ? "pass o fail" : `sobre ${datos.entrega.puntos_posibles ?? "?"}`}){" "}
                <input value={nota} disabled={!editable} onChange={(e) => setNota(e.target.value)} style={{ width: 90 }} />
              </label>
              <label style={{ display: "block", marginTop: "0.5rem" }}>
                Comentario para el estudiante
                <textarea
                  value={comentario}
                  disabled={!editable}
                  onChange={(e) => setComentario(e.target.value)}
                  rows={6}
                  style={{ width: "100%" }}
                />
              </label>
              <p style={ESTILO_MOTIVO}>
                Al publicar se agrega un pie con la entrega, la versión revisada y quién corrigió. Se registrará en Canvas a nombre
                de {datos.titular}.
              </p>
              {editable && (
                <p>
                  <button onClick={guardar}>Guardar borrador</button>{" "}
                  <button onClick={lista}>Marcar como lista para publicar</button>
                  {!datos.puede_publicar && <span style={ESTILO_MOTIVO}> · en este curso publica las notas el profesor</span>}
                </p>
              )}
            </>
          )}
          <PanelPublicacion cursoId={cursoId} entregaId={entregaId} sujetoId={sujetoId} datos={datos} onCambio={cargar} />
          <NotasYReclamos cursoId={cursoId} entregaId={entregaId} sujetoId={sujetoId} datos={datos} onCambio={cargar} />
        </section>
      </div>
      <p style={ESTILO_MOTIVO}>Atajos: J/→ siguiente, K/← anterior, N siguiente sin corregir, S guardar, L lista.</p>
    </main>
  );
}

function NotasYReclamos({
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
  const [texto, setTexto] = useState("");
  const [desenlace, setDesenlace] = useState("");
  const [error, setError] = useState<string | null>(null);
  const CLASE: Record<string, string> = { NOTA: "Nota interna", RECLAMO_ABIERTO: "Reclamo", RECLAMO_CERRADO: "Reclamo cerrado" };

  async function enviar(ruta: "notas" | "reclamos" | "reclamos/cerrar") {
    const r = await agregarNotaInterna(cursoId, entregaId, sujetoId, ruta, {
      texto,
      ...(ruta === "reclamos/cerrar" ? { desenlace } : {}),
    });
    if (r.ok) {
      setTexto("");
      setError(null);
      onCambio();
    } else setError(r.error);
  }

  return (
    <section>
      <h2>Notas internas y reclamos</h2>
      <ul>
        {datos.notas_internas.map((n, i) => (
          <li key={i}>
            <strong>{CLASE[n.clase]}</strong> · {new Date(n.creada_en).toLocaleString("es-CL")}
            {n.texto && `: ${n.texto}`}
            {n.desenlace && ` (${n.desenlace.toLowerCase().replaceAll("_", " ")})`}
          </li>
        ))}
      </ul>
      {error && <p style={{ color: "#a00" }}>{error}</p>}
      <textarea value={texto} onChange={(e) => setTexto(e.target.value)} rows={2} style={{ width: "100%" }} />
      <p>
        {datos.es_propietario && (
          <button disabled={!texto} onClick={() => enviar("notas")}>
            Agregar nota interna
          </button>
        )}{" "}
        {!datos.banderas.reclamo_abierto ? (
          <button disabled={!texto} onClick={() => enviar("reclamos")}>
            Registrar reclamo
          </button>
        ) : (
          <>
            <select value={desenlace} onChange={(e) => setDesenlace(e.target.value)}>
              <option value="">¿Cómo terminó?</option>
              <option value="SIN_CAMBIO">Sin cambio</option>
              <option value="NOTA_CORREGIDA">Nota corregida</option>
              <option value="ERROR_DE_LA_APLICACION">Error de la aplicación</option>
            </select>{" "}
            <button disabled={!texto || !desenlace} onClick={() => enviar("reclamos/cerrar")}>
              Cerrar reclamo
            </button>
          </>
        )}
      </p>
    </section>
  );
}
