import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  accionSobreMensaje,
  cambiarSuspension,
  enviarMensajeManual,
  obtenerBandeja,
  obtenerPersonas,
  publicarAnuncio,
  type Bandeja,
  type MensajeBandeja,
  type Personas,
} from "../lib/api";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;
const ESTILO_AMBAR = { background: "#fff3cd", padding: "0.5rem 0.75rem" } as const;

const EVENTO: Record<string, string> = {
  repositorio_disponible: "Repositorio disponible",
  invitacion_aceptada: "Invitación aceptada",
  recordatorio_mapeo: "Recordatorio de cuenta de GitHub",
  recordatorio_invitacion: "Recordatorio de invitación",
  proximidad_cierre: "Cierre próximo",
  cambio_de_fecha: "Cambio de fecha",
  correccion_publicada: "Nota publicada",
  MANUAL: "Escrito a mano",
};
const CANAL: Record<string, string> = {
  CANVAS_CONVERSACION: "Canvas, conversación",
  CANVAS_COMENTARIO: "Canvas, comentario en la entrega",
  CANVAS_ANUNCIO: "Canvas, anuncio",
};

function fecha(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString("es-CL") : "";
}

/** Bandeja de comunicaciones del curso (SPEC 11 S11.10): todo lo que la
 * aplicación escribió o escribirá en Canvas, con su estado y el cuerpo exacto. */
export function Comunicaciones() {
  const { cursoId } = useParams<{ cursoId: string }>();
  const [parametros, setParametros] = useSearchParams();
  const [bandeja, setBandeja] = useState<Bandeja | null>(null);
  const [abierto, setAbierto] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const filtros = {
    canal: parametros.get("canal") ?? "",
    evento: parametros.get("evento") ?? "",
    estado: parametros.get("estado") ?? "",
    tarea_id: parametros.get("tarea_id") ?? "",
    estudiante_id: parametros.get("estudiante_id") ?? "",
  };

  async function cargar() {
    if (cursoId) setBandeja(await obtenerBandeja(cursoId, filtros));
  }
  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId, parametros]);

  function filtrar(clave: string, valor: string) {
    const nuevos = new URLSearchParams(parametros);
    if (valor) nuevos.set(clave, valor);
    else nuevos.delete(clave);
    setParametros(nuevos, { replace: true });
  }

  async function accion(m: MensajeBandeja, tipo: "reintentar" | "reenviar" | "cancelar" | "retractar") {
    if (!cursoId) return;
    if (tipo === "reenviar" && !window.confirm(`¿Reenviar a ${m.destinatario}? Los mensajes de Canvas no se pueden retirar.`))
      return;
    if (tipo === "retractar" && !window.confirm("¿Retirar este anuncio de Canvas?")) return;
    setError(null);
    const r = await accionSobreMensaje(cursoId, m.id, tipo);
    if (!r.ok) setError(r.error);
    await cargar();
  }

  async function suspension(suspender: boolean) {
    if (!cursoId) return;
    const motivo = suspender ? window.prompt("¿Por qué suspendes las comunicaciones del curso?") : null;
    if (suspender && !motivo) return;
    const r = await cambiarSuspension(cursoId, suspender, motivo);
    if (!r.ok) setError(r.error);
    await cargar();
  }

  if (!cursoId || !bandeja) return <p>Cargando…</p>;
  const suspendidas = bandeja.comunicaciones_salientes === "SUSPENDIDAS";
  return (
    <main>
      <p>
        <Link to={`/cursos/${cursoId}/tareas`}>← Tareas</Link>
      </p>
      <h1>Comunicaciones</h1>
      {suspendidas && (
        <p style={ESTILO_AMBAR}>
          Las comunicaciones del curso están suspendidas: nada se escribe en Canvas hasta reanudarlas
          {bandeja.suspension_motivo && ` (${bandeja.suspension_motivo})`}. Lo retenido más de siete días ya no se envía.
        </p>
      )}
      {bandeja.canal_activo === "COMENTARIO_ENTREGA" && (
        <p style={ESTILO_AMBAR}>Los avisos salen como comentario en la tarea de registro: Canvas no permite mensajes directos.</p>
      )}
      {bandeja.canal_activo === "BLOQUEADO" && (
        <p style={ESTILO_AMBAR}>Canvas no deja enviar mensajes ni comentarios en este curso: los avisos quedan retenidos.</p>
      )}
      <p>
        <button onClick={() => suspension(!suspendidas)}>
          {suspendidas ? "Reanudar comunicaciones" : "Suspender comunicaciones del curso"}
        </button>
      </p>
      {mensaje && <p style={{ background: "#efe", padding: "0.5rem" }}>{mensaje}</p>}
      {error && <p style={{ background: "#fee", padding: "0.5rem" }}>{error}</p>}

      <Redactar cursoId={cursoId} onEnviado={(t) => { setMensaje(t); cargar(); }} onError={setError} />

      <h2>Historial</h2>
      <p>
        <select value={filtros.evento} onChange={(e) => filtrar("evento", e.target.value)}>
          <option value="">Todos los avisos</option>
          {Object.entries(EVENTO).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>{" "}
        <select value={filtros.canal} onChange={(e) => filtrar("canal", e.target.value)}>
          <option value="">Todos los canales</option>
          {Object.entries(CANAL).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>{" "}
        <select value={filtros.estado} onChange={(e) => filtrar("estado", e.target.value)}>
          <option value="">Todos los estados</option>
          {["PENDIENTE", "PROGRAMADO", "DIFERIDO", "ENVIADO", "FALLIDO", "SUPRIMIDO", "CADUCADO", "CANCELADO"].map((e) => (
            <option key={e} value={e}>
              {e.toLowerCase()}
            </option>
          ))}
        </select>
      </p>
      {bandeja.mensajes.length === 0 ? (
        <p>No hay comunicaciones con estos filtros.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Aviso</th>
              <th>Para</th>
              <th>Estado</th>
              <th>Fecha</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {bandeja.mensajes.map((m) => (
              <FilaMensaje
                key={m.id}
                m={m}
                abierto={abierto === m.id}
                onAbrir={() => setAbierto(abierto === m.id ? null : m.id)}
                onAccion={(t) => accion(m, t)}
              />
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}

function FilaMensaje({
  m,
  abierto,
  onAbrir,
  onAccion,
}: {
  m: MensajeBandeja;
  abierto: boolean;
  onAbrir: () => void;
  onAccion: (t: "reintentar" | "reenviar" | "cancelar" | "retractar") => void;
}) {
  const terminal = ["ENVIADO", "FALLIDO", "CANCELADO", "SUPRIMIDO", "CADUCADO", "RETRACTADO"].includes(m.estado);
  return (
    <>
      <tr>
        <td>
          <button onClick={onAbrir} style={{ border: "none", background: "none", cursor: "pointer", textAlign: "left" }}>
            {EVENTO[m.evento] ?? m.evento}
          </button>
          <div style={ESTILO_MOTIVO}>
            {CANAL[m.canal] ?? m.canal}
            {m.generacion > 1 && ` · reenvío ${m.generacion - 1}`}
          </div>
        </td>
        <td>{m.destinatario}</td>
        <td>
          {m.etiqueta_estado}
          {m.motivo && <div style={ESTILO_MOTIVO}>{m.motivo}</div>}
          {m.estado === "PROGRAMADO" && m.programado_para && (
            <div style={ESTILO_MOTIVO}>para el {fecha(m.programado_para)}</div>
          )}
        </td>
        <td>{fecha(m.enviado_en ?? m.creado_en)}</td>
        <td>
          {m.enlace_canvas ? (
            <a href={m.enlace_canvas} target="_blank" rel="noreferrer">
              Abrir en Canvas
            </a>
          ) : null}{" "}
          {["FALLIDO", "CADUCADO"].includes(m.estado) && <button onClick={() => onAccion("reintentar")}>Reintentar</button>}
          {m.estado === "ENVIADO" && m.canal !== "CANVAS_ANUNCIO" && (
            <button onClick={() => onAccion("reenviar")}>Reenviar</button>
          )}
          {m.estado === "ENVIADO" && m.canal === "CANVAS_ANUNCIO" && (
            <button onClick={() => onAccion("retractar")}>Retirar anuncio</button>
          )}
          {!terminal && m.estado !== "EN_CURSO" && <button onClick={() => onAccion("cancelar")}>Cancelar</button>}
        </td>
      </tr>
      {abierto && (
        <tr>
          <td colSpan={5}>
            {m.asunto && <p><strong>{m.asunto}</strong></p>}
            {m.cuerpo ? (
              <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>{m.cuerpo}</pre>
            ) : (
              <p style={ESTILO_MOTIVO}>El texto se arma al enviarse.</p>
            )}
            {!m.enlace_canvas && m.motivo_sin_enlace && <p style={ESTILO_MOTIVO}>{m.motivo_sin_enlace}</p>}
            {m.ultimo_error && <p style={ESTILO_MOTIVO}>Respuesta de Canvas: {m.ultimo_error}</p>}
          </td>
        </tr>
      )}
    </>
  );
}

function Redactar({
  cursoId,
  onEnviado,
  onError,
}: {
  cursoId: string;
  onEnviado: (texto: string) => void;
  onError: (texto: string | null) => void;
}) {
  const [personas, setPersonas] = useState<Personas | null>(null);
  const [modo, setModo] = useState<"mensaje" | "anuncio" | null>(null);
  const [elegidos, setElegidos] = useState<Set<string>>(new Set());
  const [grupo, setGrupo] = useState("");
  const [secciones, setSecciones] = useState<Set<string>>(new Set());
  const [asunto, setAsunto] = useState("");
  const [cuerpo, setCuerpo] = useState("");

  useEffect(() => {
    if (modo && !personas) obtenerPersonas(cursoId).then(setPersonas);
  }, [modo, personas, cursoId]);

  async function enviar() {
    onError(null);
    if (modo === "mensaje") {
      let r = await enviarMensajeManual(cursoId, { estudiante_ids: [...elegidos], grupo_id: grupo || null, asunto, cuerpo });
      if (!r.ok && r.status === 409 && window.confirm(r.error ?? "")) {
        r = await enviarMensajeManual(cursoId, {
          estudiante_ids: [...elegidos],
          grupo_id: grupo || null,
          asunto,
          cuerpo,
          confirmar_no_activos: true,
        });
      }
      if (r.ok) onEnviado(r.datos?.aviso ?? "Mensajes encolados.");
      else onError(r.error);
    } else {
      const base = { titulo: asunto, cuerpo_html: cuerpo, seccion_ids: [...secciones] };
      let r = await publicarAnuncio(cursoId, base);
      if (!r.ok && r.status === 409) {
        const escrito = window.prompt(r.error ?? "Escribe el número de destinatarios para confirmar.");
        if (!escrito) return;
        r = await publicarAnuncio(cursoId, { ...base, confirmacion_destinatarios: Number(escrito) });
      }
      if (r.ok) onEnviado(`Anuncio encolado para ${r.datos?.destinatarios ?? 0} estudiantes.`);
      else onError(r.error);
    }
    setModo(null);
    setAsunto("");
    setCuerpo("");
    setElegidos(new Set());
  }

  if (!modo)
    return (
      <p>
        <button onClick={() => setModo("mensaje")}>Escribir a estudiantes</button>{" "}
        <button onClick={() => setModo("anuncio")}>Publicar un anuncio</button>
      </p>
    );
  return (
    <section style={{ border: "1px solid #ddd", padding: "0.75rem" }}>
      <h2>{modo === "mensaje" ? "Escribir a estudiantes" : "Publicar un anuncio"}</h2>
      {modo === "mensaje" ? (
        <>
          <p style={ESTILO_MOTIVO}>
            Cada estudiante recibe su propio mensaje; nunca una conversación grupal. Los mensajes de Canvas no se pueden
            retirar una vez enviados.
          </p>
          <label>
            Grupo{" "}
            <select value={grupo} onChange={(e) => setGrupo(e.target.value)}>
              <option value="">(ninguno)</option>
              {personas?.grupos.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.nombre}
                </option>
              ))}
            </select>
          </label>
          <div style={{ maxHeight: 180, overflowY: "auto", margin: "0.5rem 0" }}>
            {personas?.estudiantes.map((e) => (
              <label key={e.id} style={{ display: "block" }}>
                <input
                  type="checkbox"
                  checked={elegidos.has(e.id)}
                  onChange={(ev) => {
                    const n = new Set(elegidos);
                    if (ev.target.checked) n.add(e.id);
                    else n.delete(e.id);
                    setElegidos(n);
                  }}
                />{" "}
                {e.nombre}
              </label>
            ))}
          </div>
        </>
      ) : (
        <>
          <p style={ESTILO_MOTIVO}>Sin secciones elegidas, el anuncio llega a todo el curso. Se publica cerrado a comentarios.</p>
          {personas?.secciones.map((s) => (
            <label key={s.id} style={{ display: "block" }}>
              <input
                type="checkbox"
                checked={secciones.has(s.id)}
                onChange={(ev) => {
                  const n = new Set(secciones);
                  if (ev.target.checked) n.add(s.id);
                  else n.delete(s.id);
                  setSecciones(n);
                }}
              />{" "}
              {s.nombre} ({s.cantidad_estudiantes})
            </label>
          ))}
        </>
      )}
      <label style={{ display: "block" }}>
        {modo === "mensaje" ? "Asunto" : "Título"}
        <input value={asunto} onChange={(e) => setAsunto(e.target.value)} style={{ width: "100%" }} maxLength={modo === "mensaje" ? 200 : 120} />
      </label>
      <label style={{ display: "block" }}>
        {modo === "mensaje" ? "Mensaje (texto plano, hasta 4000 caracteres)" : "Texto (puedes usar <p>, <ul>, <li>, <a> y <strong>)"}
        <textarea value={cuerpo} onChange={(e) => setCuerpo(e.target.value)} rows={6} style={{ width: "100%" }} maxLength={modo === "mensaje" ? 4000 : 8000} />
      </label>
      <button disabled={!asunto || !cuerpo} onClick={enviar}>
        {modo === "mensaje" ? "Enviar" : "Publicar"}
      </button>{" "}
      <button onClick={() => setModo(null)}>Cancelar</button>
    </section>
  );
}
