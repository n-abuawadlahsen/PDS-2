import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  aplicarReparto,
  obtenerBandejaCorreccion,
  obtenerMatrizCorreccion,
  previsualizarReparto,
  type BandejaCorreccion,
  type MatrizCorreccion,
  type PropuestaReparto,
} from "../lib/api";
import { PublicarSeleccionadas } from "./PublicarSeleccionadas";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;
const COLOR_ESTADO: Record<string, string> = {
  SIN_CORRECTOR: "#eee",
  ASIGNADA: "#e8f0fe",
  EN_CURSO: "#fff3cd",
  LISTA_PARA_PUBLICAR: "#d1ecf1",
  PUBLICANDO: "#d1ecf1",
  PUBLICADA: "#d4edda",
  PUBLICADA_CON_ADVERTENCIA: "#ffe8a1",
  ERROR_PUBLICACION: "#f8d7da",
};
const BANDERA: Record<string, string> = {
  version_desactualizada: "versión nueva",
  reclamo_abierto: "reclamo",
  sin_commits: "sin commits",
  reconocimiento_sin_codigo: "sin código",
  desalineada: "desalineada",
};
const CONTRASTE: Record<string, string> = {
  DIVERGE: "Canvas tiene otra nota",
  SOLO_EN_CANVAS: "nota solo en Canvas",
};

type Pestana = "mias" | "estado" | "repartir";

/** Bandeja de corrección (S12.6): mis asignaciones, estado de la entrega y
 * reparto. Todos ven la matriz completa; editar es solo de quien corrige. */
export function Correccion() {
  const { cursoId } = useParams<{ cursoId: string }>();
  const [parametros, setParametros] = useSearchParams();
  const [bandeja, setBandeja] = useState<BandejaCorreccion | null>(null);

  useEffect(() => {
    if (cursoId) obtenerBandejaCorreccion(cursoId).then(setBandeja);
  }, [cursoId]);

  if (!cursoId || !bandeja) return <p>Cargando…</p>;
  const porDefecto: Pestana = bandeja.es_profesor ? "estado" : "mias";
  const pestana = (parametros.get("pestana") as Pestana | null) ?? porDefecto;
  const tareaId = parametros.get("tarea") ?? bandeja.tareas[0]?.id ?? "";

  function ir(p: Pestana) {
    const n = new URLSearchParams(parametros);
    n.set("pestana", p);
    setParametros(n, { replace: true });
  }

  return (
    <main>
      <p>
        <Link to={`/cursos/${cursoId}/tareas`}>← Tareas</Link>
      </p>
      <h1>Corrección</h1>
      {bandeja.nuevas > 0 && (
        <p style={{ background: "#e8f0fe", padding: "0.5rem" }}>Se te asignaron {bandeja.nuevas} entregas nuevas.</p>
      )}
      <p>
        <button disabled={pestana === "mias"} onClick={() => ir("mias")}>
          Mis asignaciones
        </button>{" "}
        <button disabled={pestana === "estado"} onClick={() => ir("estado")}>
          Estado de la entrega
        </button>{" "}
        {bandeja.puede_repartir && (
          <button disabled={pestana === "repartir"} onClick={() => ir("repartir")}>
            Repartir
          </button>
        )}
      </p>
      {!bandeja.puede_repartir && bandeja.sin_corrector > 0 && (
        <p style={ESTILO_MOTIVO}>{bandeja.sin_corrector} entregas sin corrector: las reparte un profesor.</p>
      )}
      {pestana === "mias" && <MisAsignaciones cursoId={cursoId} bandeja={bandeja} />}
      {(pestana === "estado" || pestana === "repartir") && (
        <p>
          <label>
            Tarea{" "}
            <select
              value={tareaId}
              onChange={(e) => {
                const n = new URLSearchParams(parametros);
                n.set("tarea", e.target.value);
                setParametros(n, { replace: true });
              }}
            >
              {bandeja.tareas.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nombre}
                </option>
              ))}
            </select>
          </label>
        </p>
      )}
      {pestana === "estado" && tareaId && (
        <EstadoEntrega cursoId={cursoId} tareaId={tareaId} puedePublicar={bandeja.puede_publicar} />
      )}
      {pestana === "repartir" && tareaId && (
        <Repartir cursoId={cursoId} entregas={bandeja.tareas.find((t) => t.id === tareaId)?.entregas ?? []} />
      )}
    </main>
  );
}

function MisAsignaciones({ cursoId, bandeja }: { cursoId: string; bandeja: BandejaCorreccion }) {
  const [soloSinCorregir, setSoloSinCorregir] = useState(false);
  const filas = bandeja.mis_asignaciones.filter(
    (a) => !soloSinCorregir || a.estado === "ASIGNADA" || a.estado === "EN_CURSO",
  );
  if (bandeja.mis_asignaciones.length === 0) {
    return <p>No tienes entregas asignadas. Cuando un profesor reparta la corrección, aparecerán aquí.</p>;
  }
  const porEntrega = new Map<string, typeof filas>();
  for (const f of filas) porEntrega.set(f.entrega, [...(porEntrega.get(f.entrega) ?? []), f]);
  return (
    <section>
      <p>
        {bandeja.contador.asignadas} asignadas · {bandeja.contador.corregidas} corregidas · {bandeja.contador.publicadas}{" "}
        publicadas ·{" "}
        <label>
          <input type="checkbox" checked={soloSinCorregir} onChange={(e) => setSoloSinCorregir(e.target.checked)} /> sólo sin
          corregir
        </label>
      </p>
      {filas.length === 0 && <p>No te queda ninguna sin corregir.</p>}
      {[...porEntrega.entries()].map(([entrega, lista]) => (
        <div key={entrega}>
          <h2>{entrega}</h2>
          <ul>
            {lista.map((a) => (
              <li key={`${a.entrega_id}-${a.sujeto_id}`}>
                <Link to={`/cursos/${cursoId}/correccion/${a.entrega_id}/${a.sujeto_id}`}>{a.sujeto}</Link> · {a.etiqueta}
                {a.sin_commits && " · sin commits al cierre"}
                {a.reclamo_abierto && " · reclamo abierto"}
                {a.version_desactualizada && " · versión nueva"}
                {a.nueva && <strong> · nueva</strong>}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function EstadoEntrega({ cursoId, tareaId, puedePublicar }: { cursoId: string; tareaId: string; puedePublicar: boolean }) {
  const [matriz, setMatriz] = useState<MatrizCorreccion | null>(null);
  const [soloDiscrepancia, setSoloDiscrepancia] = useState(false);

  async function cargar() {
    setMatriz(await obtenerMatrizCorreccion(cursoId, tareaId));
  }
  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId, tareaId]);

  if (!matriz) return <p>Cargando…</p>;
  const c = matriz.contador;
  const sujetos = matriz.sujetos.filter(
    (s) => !soloDiscrepancia || Object.values(s.celdas).some((x) => x.contraste === "DIVERGE" || x.contraste === "SOLO_EN_CANVAS"),
  );
  return (
    <section>
      <p>
        <strong>
          {c.corregidas} de {c.total} corregidas en la aplicación · {c.con_nota_en_canvas} de {c.total} con nota en Canvas
        </strong>
        <span style={ESTILO_MOTIVO}>
          {" "}
          · {c.comprobado_en ? `comprobado el ${new Date(c.comprobado_en).toLocaleString("es-CL")}` : "sin comprobar contra Canvas"}
        </span>
      </p>
      <label style={ESTILO_MOTIVO}>
        <input type="checkbox" checked={soloDiscrepancia} onChange={(e) => setSoloDiscrepancia(e.target.checked)} /> sólo con
        discrepancia con Canvas
      </label>
      {puedePublicar && <PublicarSeleccionadas cursoId={cursoId} tareaId={tareaId} matriz={matriz} onFin={cargar} />}
      <table>
        <thead>
          <tr>
            <th>Sujeto</th>
            <th>Sección</th>
            {matriz.entregas.map((e) => (
              <th key={e.id}>{e.nombre}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sujetos.map((s) => (
            <tr key={s.sujeto_id}>
              <td>
                {s.sujeto}
                {!s.activo && <span style={ESTILO_MOTIVO}> (retirado)</span>}
              </td>
              <td>{s.seccion ?? ""}</td>
              {matriz.entregas.map((e) => {
                const celda = s.celdas[e.id];
                if (!celda) return <td key={e.id} style={ESTILO_MOTIVO}>no aplica</td>;
                return (
                  <td key={e.id} style={{ background: COLOR_ESTADO[celda.estado] }}>
                    <Link to={`/cursos/${cursoId}/correccion/${e.id}/${s.sujeto_id}`}>{celda.etiqueta}</Link>
                    <div style={ESTILO_MOTIVO}>
                      {celda.corrector ?? "sin corrector"}
                      {celda.banderas.map((b) => ` · ${BANDERA[b] ?? b}`)}
                      {!celda.publicable && " · no publicable"}
                      {CONTRASTE[celda.contraste] && ` · ${CONTRASTE[celda.contraste]}`}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <h2>Por corrector</h2>
      <Agregado tabla={matriz.por_corrector} />
      <h2>Por sección</h2>
      <Agregado tabla={matriz.por_seccion} />
    </section>
  );
}

function Agregado({ tabla }: { tabla: Record<string, Record<string, number>> }) {
  return (
    <ul>
      {Object.entries(tabla).map(([clave, estados]) => (
        <li key={clave}>
          {clave}:{" "}
          {Object.entries(estados)
            .map(([e, n]) => `${n} ${e.toLowerCase().replaceAll("_", " ")}`)
            .join(", ")}
        </li>
      ))}
    </ul>
  );
}

function Repartir({ cursoId, entregas }: { cursoId: string; entregas: { id: string; nombre: string }[] }) {
  const [entregaId, setEntregaId] = useState(entregas[0]?.id ?? "");
  const [criterio, setCriterio] = useState("EQUITATIVO");
  const [reasignar, setReasignar] = useState(false);
  const [propuesta, setPropuesta] = useState<PropuestaReparto | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function ver() {
    setError(null);
    setMensaje(null);
    const r = await previsualizarReparto(cursoId, entregaId, { criterio, reasignar });
    if (r.ok) setPropuesta(r.datos);
    else setError(r.error);
  }
  async function aplicar() {
    const r = await aplicarReparto(cursoId, entregaId, { criterio, reasignar });
    if (r.ok) setMensaje(`Reparto aplicado: ${r.datos?.cambios ?? 0} cambios.`);
    else setError(r.error);
    setPropuesta(null);
  }

  return (
    <section>
      <p>
        <select value={entregaId} onChange={(e) => setEntregaId(e.target.value)}>
          {entregas.map((e) => (
            <option key={e.id} value={e.id}>
              {e.nombre}
            </option>
          ))}
        </select>{" "}
        <select value={criterio} onChange={(e) => setCriterio(e.target.value)}>
          <option value="EQUITATIVO">Equitativo (por peso)</option>
          <option value="COPIA_ENTREGA_ANTERIOR">Mismo corrector que la entrega anterior</option>
        </select>{" "}
        <label>
          <input type="checkbox" checked={reasignar} onChange={(e) => setReasignar(e.target.checked)} /> reasignar también las
          que ya empezaron
        </label>{" "}
        <button onClick={ver}>Previsualizar</button>
      </p>
      <p style={ESTILO_MOTIVO}>
        Nada se escribe hasta confirmar. Por defecto solo se llenan las filas sin corrector; el borrador siempre se conserva.
      </p>
      {mensaje && <p style={{ background: "#efe", padding: "0.5rem" }}>{mensaje}</p>}
      {error && <p style={{ background: "#fee", padding: "0.5rem" }}>{error}</p>}
      {propuesta && (
        <>
          <p>
            {Object.entries(propuesta.totales)
              .map(([k, n]) => `${k}: ${n}`)
              .join(" · ")}
          </p>
          <table>
            <thead>
              <tr>
                <th>Sujeto</th>
                <th>Ahora</th>
                <th>Propuesto</th>
              </tr>
            </thead>
            <tbody>
              {propuesta.filas.map((f) => (
                <tr key={f.sujeto_id} style={{ background: f.sobrescribe ? "#fff3cd" : undefined }}>
                  <td>{f.sujeto}</td>
                  <td>{f.actual ?? "sin corrector"}</td>
                  <td>{f.propuesto ?? "sin corrector"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={aplicar}>Confirmar y aplicar</button>
        </>
      )}
    </section>
  );
}
