import { useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import {
  accionSobreMensaje,
  apiFetch,
  cambiarSuspension,
  enviarMensajeManual,
  obtenerBandeja,
  obtenerPersonas,
  type MensajeBandeja,
} from "../lib/api";
import { fechaFinal } from "../lib/apiFinal";
import { errorRespuesta } from "../lib/errores";
import { useCurso } from "../components/Layout";
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

const EVENTO: Record<string, string> = {
  repositorio_disponible: "Repositorio disponible",
  invitacion_aceptada: "Invitación aceptada",
  recordatorio_mapeo: "Recordatorio de cuenta de GitHub",
  recordatorio_invitacion: "Recordatorio de invitación",
  proximidad_cierre: "Cierre próximo",
  cambio_de_fecha: "Cambio de fecha",
  correccion_publicada: "Nota publicada",
  MANUAL: "Mensaje manual",
};
const CANAL: Record<string, string> = {
  CANVAS_CONVERSACION: "Conversación de Canvas",
  CANVAS_COMENTARIO: "Comentario en la entrega",
  CANVAS_ANUNCIO: "Anuncio de Canvas",
};

export function Comunicaciones() {
  const { cursoId = "" } = useParams();
  const { curso, puede } = useCurso();
  const [parametros, setParametros] = useSearchParams();
  const [abierto, setAbierto] = useState<string | null>(null);
  const [motivo, setMotivo] = useState("");
  const [suspensionAbierta, setSuspensionAbierta] = useState(false);
  const op = useOperacion();
  const confirmar = useConfirmar();
  const filtros = Object.fromEntries(
    [
      "canal",
      "evento",
      "estado",
      "tarea_id",
      "estudiante_id",
      "repositorio_id",
      "limite",
    ].map((k) => [k, parametros.get(k) ?? ""]),
  );
  const consulta = useConsulta(
    `comunicaciones:${cursoId}:${parametros.toString()}`,
    () => obtenerBandeja(cursoId, filtros),
  );
  const bandeja = consulta.datos;
  const suspendidas = bandeja?.comunicaciones_salientes === "SUSPENDIDAS";
  function filtrar(clave: string, valor: string) {
    const nuevos = new URLSearchParams(parametros);
    if (valor) nuevos.set(clave, valor);
    else nuevos.delete(clave);
    setParametros(nuevos, { replace: true });
  }
  async function accion(
    m: MensajeBandeja,
    tipo: "reintentar" | "reenviar" | "cancelar" | "retractar",
  ) {
    if (
      ["reenviar", "retractar"].includes(tipo) &&
      !(await confirmar({
        titulo:
          tipo === "reenviar"
            ? `Reenviar a ${m.destinatario}`
            : "Retirar anuncio de Canvas",
        descripcion:
          tipo === "reenviar"
            ? "Se enviará un nuevo mensaje. Las conversaciones de Canvas no se pueden retirar una vez enviadas."
            : `Se solicitará retirar el anuncio «${m.asunto ?? "Sin título"}» de Canvas.`,
        accion: tipo === "reenviar" ? "Reenviar mensaje" : "Retirar anuncio",
      }))
    )
      return;
    await op.ejecutar(async () => {
      const r = await accionSobreMensaje(cursoId, m.id, tipo);
      if (!r.ok)
        throw new Error(r.error || "No se pudo completar la operación.");
      consulta.recargar();
    }, "Solicitud registrada. Revisa el estado del mensaje en el historial.");
  }
  return (
    <>
      <Cabecera
        titulo="Comunicaciones"
        descripcion="Mensajes, anuncios y avisos del curso enviados a través de Canvas."
        acciones={
          <button disabled={consulta.cargando} onClick={consulta.recargar}>
            Actualizar historial
          </button>
        }
      />
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {!bandeja ? (
        !consulta.error && <Cargando />
      ) : (
        <>
          {suspendidas && (
            <Aviso tipo="warning">
              Las comunicaciones están suspendidas: los avisos quedan retenidos
              hasta reanudar. {bandeja.suspension_motivo} Lo retenido más de
              siete días caduca.
            </Aviso>
          )}
          {bandeja.canal_activo === "COMENTARIO_ENTREGA" && (
            <Aviso tipo="warning">
              Canvas no permite mensajes directos en este curso. Los avisos se
              envían como comentarios en la tarea de registro.
            </Aviso>
          )}
          {bandeja.canal_activo === "BLOQUEADO" && (
            <Aviso tipo="warning">
              Canvas no permite mensajes ni comentarios. Los avisos quedan
              retenidos hasta que el equipo resuelva la vinculación.
            </Aviso>
          )}
          <Mensajes error={op.error} mensaje={op.mensaje} />
          {puede("curso.administrar") && (
            <div className="panel">
              <button
                disabled={op.ocupado}
                onClick={() =>
                  suspendidas
                    ? op.ejecutar(async () => {
                        const r = await cambiarSuspension(cursoId, false, null);
                        if (!r.ok)
                          throw new Error(
                            r.error || "No se pudo completar la operación.",
                          );
                        consulta.recargar();
                      }, "Comunicaciones reanudadas.")
                    : setSuspensionAbierta(!suspensionAbierta)
                }
              >
                {suspendidas
                  ? "Reanudar comunicaciones"
                  : "Suspender comunicaciones"}
              </button>
              {suspensionAbierta && !suspendidas && (
                <form
                  className="form-stack"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void op.ejecutar(async () => {
                      const r = await cambiarSuspension(
                        cursoId,
                        true,
                        motivo.trim(),
                      );
                      if (!r.ok)
                        throw new Error(
                          r.error || "No se pudo completar la operación.",
                        );
                      setSuspensionAbierta(false);
                      setMotivo("");
                      consulta.recargar();
                    }, "Comunicaciones suspendidas.");
                  }}
                >
                  <label>
                    Motivo de la suspensión
                    <input
                      required
                      value={motivo}
                      maxLength={2000}
                      onChange={(e) => setMotivo(e.target.value)}
                    />
                  </label>
                  <p className="help">
                    Nada se escribirá en Canvas hasta reanudar. Los mensajes
                    actuales se conservan.
                  </p>
                  <button disabled={op.ocupado || !motivo.trim()}>
                    Confirmar suspensión
                  </button>
                </form>
              )}
            </div>
          )}
          {puede("comunicacion.enviar") ? (
            <Redactar
              cursoId={cursoId}
              onEnviado={(texto) => {
                op.setMensaje(texto);
                consulta.recargar();
              }}
            />
          ) : (
            <Aviso>
              Puedes consultar el historial. Para escribir o gestionar mensajes
              necesitas el permiso de enviar comunicaciones.
            </Aviso>
          )}
          <section className="panel">
            <h2>Historial</h2>
            <div className="filters">
              <label>
                Aviso
                <select
                  value={filtros.evento}
                  onChange={(e) => filtrar("evento", e.target.value)}
                >
                  <option value="">Todos los avisos</option>
                  {Object.entries(EVENTO).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Canal
                <select
                  value={filtros.canal}
                  onChange={(e) => filtrar("canal", e.target.value)}
                >
                  <option value="">Todos los canales</option>
                  {Object.entries(CANAL).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Estado
                <select
                  value={filtros.estado}
                  onChange={(e) => filtrar("estado", e.target.value)}
                >
                  <option value="">Todos los estados</option>
                  {[
                    "PENDIENTE",
                    "PROGRAMADO",
                    "DIFERIDO",
                    "EN_CURSO",
                    "ENVIADO",
                    "FALLIDO",
                    "SUPRIMIDO",
                    "CADUCADO",
                    "CANCELADO",
                    "RETRACTADO",
                  ].map((e) => (
                    <option key={e} value={e}>
                      {e.charAt(0) +
                        e.slice(1).toLowerCase().replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Últimos mensajes
                <select
                  value={filtros.limite || "200"}
                  onChange={(e) => filtrar("limite", e.target.value)}
                >
                  {[50, 200, 500].map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </label>
              {parametros.size > 0 && (
                <button onClick={() => setParametros({}, { replace: true })}>
                  Quitar filtros
                </button>
              )}
            </div>
            <p className="help">
              {bandeja.mensajes.length} mensajes recibidos, hasta{" "}
              {filtros.limite || 200} por consulta.{" "}
              {filtros.tarea_id && "Filtrado por tarea."}
              {filtros.estudiante_id && " Filtrado por estudiante."}
            </p>
            {bandeja.mensajes.length === 0 ? (
              <Vacio>No hay comunicaciones con estos filtros.</Vacio>
            ) : (
              <Tabla etiqueta="Historial de comunicaciones">
                <table>
                  <thead>
                    <tr>
                      <th>Aviso</th>
                      <th>Destinatario</th>
                      <th>Estado</th>
                      <th>Fecha</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bandeja.mensajes.map((m) => (
                      <FilaMensaje
                        key={m.id}
                        m={m}
                        zona={curso.zona_horaria}
                        abierto={abierto === m.id}
                        puedeEnviar={puede("comunicacion.enviar")}
                        ocupado={op.ocupado}
                        onAbrir={() =>
                          setAbierto(abierto === m.id ? null : m.id)
                        }
                        onAccion={(tipo) => accion(m, tipo)}
                      />
                    ))}
                  </tbody>
                </table>
              </Tabla>
            )}
          </section>
        </>
      )}
    </>
  );
}
function FilaMensaje({
  m,
  zona,
  abierto,
  puedeEnviar,
  ocupado,
  onAbrir,
  onAccion,
}: {
  m: MensajeBandeja;
  zona: string;
  abierto: boolean;
  puedeEnviar: boolean;
  ocupado: boolean;
  onAbrir: () => void;
  onAccion: (
    tipo: "reintentar" | "reenviar" | "cancelar" | "retractar",
  ) => void;
}) {
  const terminal = [
    "ENVIADO",
    "FALLIDO",
    "CANCELADO",
    "SUPRIMIDO",
    "CADUCADO",
    "RETRACTADO",
  ].includes(m.estado);
  return (
    <>
      <tr>
        <td>
          <button className="quiet" aria-expanded={abierto} onClick={onAbrir}>
            {EVENTO[m.evento] ?? "Comunicación"}
          </button>
          <div className="help">
            {CANAL[m.canal] ?? "Canvas"}
            {m.generacion > 1 && ` · reenvío ${m.generacion - 1}`}
          </div>
        </td>
        <td>{m.destinatario}</td>
        <td>
          {m.etiqueta_estado}
          {m.motivo && <div className="help">{m.motivo}</div>}
          {m.programado_para && (
            <div className="help">
              Programado: {fechaFinal(m.programado_para, zona)}
            </div>
          )}
        </td>
        <td>{fechaFinal(m.enviado_en ?? m.creado_en, zona)}</td>
        <td>
          <div className="actions">
            {m.enlace_canvas && (
              <a href={m.enlace_canvas} target="_blank" rel="noreferrer">
                Abrir en Canvas
              </a>
            )}
            {puedeEnviar && (
              <>
                {["FALLIDO", "CADUCADO"].includes(m.estado) && (
                  <button
                    disabled={ocupado}
                    onClick={() => onAccion("reintentar")}
                  >
                    Reintentar
                  </button>
                )}
                {m.estado === "ENVIADO" && (
                  <button
                    disabled={ocupado}
                    onClick={() =>
                      onAccion(
                        m.canal === "CANVAS_ANUNCIO" ? "retractar" : "reenviar",
                      )
                    }
                  >
                    {m.canal === "CANVAS_ANUNCIO"
                      ? "Retirar anuncio"
                      : "Reenviar"}
                  </button>
                )}
                {!terminal && m.estado !== "EN_CURSO" && (
                  <button
                    disabled={ocupado}
                    onClick={() => onAccion("cancelar")}
                  >
                    Cancelar
                  </button>
                )}
              </>
            )}
          </div>
        </td>
      </tr>
      {abierto && (
        <tr>
          <td colSpan={5}>
            {m.asunto && <strong>{m.asunto}</strong>}
            {m.cuerpo ? (
              <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
                {m.cuerpo}
              </pre>
            ) : (
              <p className="help">El texto se prepara al enviar el aviso.</p>
            )}
            {m.motivo_sin_enlace && (
              <p className="help">{m.motivo_sin_enlace}</p>
            )}
            {m.ultimo_error && (
              <Aviso tipo="warning">
                Respuesta de Canvas: {m.ultimo_error}
              </Aviso>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
function Redactar({
  cursoId,
  onEnviado,
}: {
  cursoId: string;
  onEnviado: (texto: string) => void;
}) {
  const [modo, setModo] = useState<"mensaje" | "anuncio" | null>(null);
  const [elegidos, setElegidos] = useState<Set<string>>(new Set());
  const [grupo, setGrupo] = useState("");
  const [secciones, setSecciones] = useState<Set<string>>(new Set());
  const [asunto, setAsunto] = useState("");
  const [cuerpo, setCuerpo] = useState("");
  const [buscar, setBuscar] = useState("");
  const [vista, setVista] = useState(false);
  const personas = useConsulta(
    `destinatarios:${cursoId}:${Boolean(modo)}`,
    () => (modo ? obtenerPersonas(cursoId) : Promise.resolve(null)),
  );
  const op = useOperacion();
  const confirmar = useConfirmar();
  function terminar(texto: string) {
    onEnviado(texto);
    setModo(null);
    setAsunto("");
    setCuerpo("");
    setElegidos(new Set());
    setSecciones(new Set());
    setGrupo("");
    setVista(false);
  }
  async function enviar() {
    await op.ejecutar(async () => {
      if (modo === "mensaje") {
        const base = {
          estudiante_ids: [...elegidos],
          grupo_id: grupo || null,
          asunto: asunto.trim(),
          cuerpo: cuerpo.trim(),
        };
        let r = await enviarMensajeManual(cursoId, base);
        if (
          !r.ok &&
          r.status === 409 &&
          (await confirmar({
            titulo: "Confirmar destinatarios inactivos",
            descripcion:
              r.error ||
              "Hay destinatarios inactivos. Confirma si deseas escribirles.",
            accion: "Enviar igualmente",
          }))
        )
          r = await enviarMensajeManual(cursoId, {
            ...base,
            confirmar_no_activos: true,
          });
        if (!r.ok)
          throw new Error(r.error || "No se pudo completar la operación.");
        terminar(
          r.datos?.aviso ??
            "Mensajes encolados. Revisa su estado en el historial.",
        );
      } else {
        const base = {
          titulo: asunto.trim(),
          cuerpo_html: cuerpo.trim(),
          seccion_ids: [...secciones],
        };
        const publicar = (
          datos: typeof base & { confirmacion_destinatarios?: number },
        ) =>
          apiFetch(`/api/cursos/${cursoId}/comunicaciones/anuncios`, {
            method: "POST",
            body: JSON.stringify(datos),
          });
        let respuesta = await publicar(base);
        if (respuesta.status === 409) {
          const json = (await respuesta.clone().json()) as {
            detail?: {
              codigo?: string;
              motivo?: string;
              destinatarios?: number;
            };
          };
          if (
            json.detail?.codigo === "CONFIRMAR_DESTINATARIOS" &&
            typeof json.detail.destinatarios === "number"
          ) {
            if (
              !(await confirmar({
                titulo: "Confirmar alcance del anuncio",
                descripcion:
                  json.detail.motivo ??
                  "Confirma el número de estudiantes que recibirán este anuncio.",
                escribir: String(json.detail.destinatarios),
                accion: "Publicar anuncio",
              }))
            )
              return;
            respuesta = await publicar({
              ...base,
              confirmacion_destinatarios: json.detail.destinatarios,
            });
          }
        }
        if (!respuesta.ok) throw await errorRespuesta(respuesta);
        const r = (await respuesta.json()) as { destinatarios: number };
        terminar(`Anuncio encolado para ${r.destinatarios} estudiantes.`);
      }
    });
  }
  if (!modo)
    return (
      <div className="actions">
        <button className="primary" onClick={() => setModo("mensaje")}>
          Escribir a estudiantes
        </button>
        <button onClick={() => setModo("anuncio")}>Publicar un anuncio</button>
      </div>
    );
  const seleccionGrupo = personas.datos?.grupos.find((g) => g.id === grupo);
  return (
    <section className="panel">
      <h2>
        {modo === "mensaje" ? "Mensaje a estudiantes" : "Anuncio del curso"}
      </h2>
      <Mensajes error={op.error} mensaje={null} />
      {personas.error && (
        <ErrorCarga error={personas.error} reintentar={personas.recargar} />
      )}
      {!personas.datos ? (
        !personas.error && <Cargando texto="Cargando destinatarios…" />
      ) : vista ? (
        <>
          <Aviso>
            Revisa el texto y el alcance antes de enviarlo a Canvas.{" "}
            {modo === "mensaje"
              ? "Cada persona recibe su propio mensaje y no se puede retirar."
              : "El anuncio se publica cerrado a comentarios."}
          </Aviso>
          <p>
            <strong>Destinatarios:</strong>{" "}
            {modo === "mensaje"
              ? `${elegidos.size} estudiantes seleccionados${seleccionGrupo ? ` y el grupo ${seleccionGrupo.nombre}` : ""}. Las personas repetidas reciben un solo mensaje.`
              : secciones.size
                ? personas.datos.secciones
                    .filter((s) => secciones.has(s.id))
                    .map((s) => s.nombre)
                    .join(", ")
                : "Todo el curso"}
          </p>
          <h3>{asunto}</h3>
          {modo === "mensaje" ? (
            <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
              {cuerpo}
            </pre>
          ) : (
            <iframe
              title="Vista previa del anuncio"
              sandbox=""
              srcDoc={`<meta http-equiv="Content-Security-Policy" content="default-src 'none'">${cuerpo}`}
              style={{
                width: "100%",
                height: 220,
                border: "1px solid var(--color-border)",
              }}
            />
          )}
          <div className="actions">
            <button disabled={op.ocupado} onClick={() => setVista(false)}>
              Volver a editar
            </button>
            <button className="primary" disabled={op.ocupado} onClick={enviar}>
              {op.ocupado
                ? "Encolando…"
                : modo === "mensaje"
                  ? "Confirmar y enviar"
                  : "Confirmar y publicar anuncio"}
            </button>
          </div>
        </>
      ) : (
        <form
          className="form-stack"
          onSubmit={(e) => {
            e.preventDefault();
            setVista(true);
          }}
        >
          {modo === "mensaje" ? (
            <>
              <p className="help">
                Cada estudiante recibe su propio mensaje. Puedes combinar un
                grupo y estudiantes individuales.
              </p>
              <label>
                Grupo
                <select
                  value={grupo}
                  onChange={(e) => setGrupo(e.target.value)}
                >
                  <option value="">Sin grupo</option>
                  {personas.datos.grupos.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.nombre}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Buscar estudiantes
                <input
                  value={buscar}
                  onChange={(e) => setBuscar(e.target.value)}
                  type="search"
                />
              </label>
              <fieldset>
                <legend>Estudiantes · {elegidos.size} seleccionados</legend>
                <div style={{ maxHeight: 220, overflowY: "auto" }}>
                  {personas.datos.estudiantes
                    .filter((e) =>
                      e.nombre
                        .toLocaleLowerCase("es")
                        .includes(buscar.toLocaleLowerCase("es")),
                    )
                    .map((e) => (
                      <label key={e.id} className="check">
                        <input
                          type="checkbox"
                          checked={elegidos.has(e.id)}
                          onChange={(ev) => {
                            const nuevos = new Set(elegidos);
                            if (ev.target.checked) nuevos.add(e.id);
                            else nuevos.delete(e.id);
                            setElegidos(nuevos);
                          }}
                        />
                        {e.nombre}
                        {!["ACTIVO", "INVITADO"].includes(e.estado) &&
                          " (inactivo)"}
                      </label>
                    ))}
                </div>
              </fieldset>
            </>
          ) : (
            <fieldset>
              <legend>Alcance del anuncio</legend>
              <p className="help">
                Sin secciones seleccionadas, llegará a todo el curso.
              </p>
              {personas.datos.secciones.map((s) => (
                <label key={s.id} className="check">
                  <input
                    type="checkbox"
                    checked={secciones.has(s.id)}
                    onChange={(e) => {
                      const nuevos = new Set(secciones);
                      if (e.target.checked) nuevos.add(s.id);
                      else nuevos.delete(s.id);
                      setSecciones(nuevos);
                    }}
                  />
                  {s.nombre} · {s.cantidad_estudiantes} estudiantes
                </label>
              ))}
            </fieldset>
          )}
          <label>
            {modo === "mensaje" ? "Asunto" : "Título"}
            <input
              required
              value={asunto}
              onChange={(e) => setAsunto(e.target.value)}
              maxLength={modo === "mensaje" ? 200 : 120}
            />
          </label>
          <label>
            {modo === "mensaje" ? "Mensaje" : "Texto del anuncio"}
            <textarea
              required
              value={cuerpo}
              onChange={(e) => setCuerpo(e.target.value)}
              rows={6}
              maxLength={modo === "mensaje" ? 4000 : 8000}
            />
          </label>
          <p className="help">
            {modo === "mensaje"
              ? "Texto plano, sin etiquetas HTML. Hasta 4.000 caracteres."
              : "Admite párrafos, listas, enlaces y negritas: <p>, <ul>, <li>, <a> y <strong>. Hasta 8.000 caracteres."}
          </p>
          <div className="actions">
            <button
              type="submit"
              className="primary"
              disabled={
                !asunto.trim() ||
                !cuerpo.trim() ||
                (modo === "mensaje" && !grupo && elegidos.size === 0)
              }
            >
              Previsualizar comunicación
            </button>
            <button type="button" onClick={() => setModo(null)}>
              Cerrar redacción
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
