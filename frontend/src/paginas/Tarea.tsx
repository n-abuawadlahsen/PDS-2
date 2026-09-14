import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  activarTarea,
  borrarArchivoBase,
  crearRepositorioBase,
  desvincularEntrega,
  escribirArchivoBase,
  obtenerTarea,
  previsualizarArchivoBase,
  renombrarArchivoBase,
  type PrevisualizacionArchivo,
  type Resultado,
  type TareaDetalle,
} from "../lib/api";
import {
  fechaLegible,
  tamanoLegible,
  textoEstadoBase,
  textoEstadoEntrega,
  textoEstadoTarea,
  textoModalidad,
  textoTipoEntrega,
} from "../lib/textosTarea";
import { BloqueRepositorios, LineaFechas } from "./RepositoriosTarea";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;
const ESTILO_ERROR = { background: "#fee", padding: "0.75rem" } as const;

function leerComoBase64(archivo: File): Promise<string> {
  return new Promise((resolver, rechazar) => {
    const lector = new FileReader();
    lector.onload = () => resolver(String(lector.result).split(",", 2)[1] ?? "");
    lector.onerror = () => rechazar(lector.error);
    lector.readAsDataURL(archivo);
  });
}

/** `/cursos/{id}/tareas/{tid}` (SPEC 13 S13.5.2): entregas, repositorio base
 * (R2.3.5, R2.3.6) y activacion con su guarda escrita (A-208). */
export function Tarea() {
  const { cursoId, tareaId } = useParams<{ cursoId: string; tareaId: string }>();
  const [tarea, setTarea] = useState<TareaDetalle | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const [rutaNueva, setRutaNueva] = useState("");
  const [archivoNuevo, setArchivoNuevo] = useState<File | null>(null);
  const [renombrando, setRenombrando] = useState<{ desde: string; hacia: string } | null>(null);
  const [vista, setVista] = useState<PrevisualizacionArchivo | null>(null);
  const reemplazoRef = useRef<HTMLInputElement>(null);
  const [rutaReemplazo, setRutaReemplazo] = useState<string | null>(null);

  async function cargar() {
    if (!cursoId || !tareaId) return;
    setTarea(await obtenerTarea(cursoId, tareaId));
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId, tareaId]);

  async function ejecutar(accion: () => Promise<Resultado<TareaDetalle>>, exito: string) {
    setOcupado(true);
    setMensaje(null);
    setError(null);
    const r = await accion();
    setOcupado(false);
    if (r.ok && r.datos) {
      setTarea(r.datos);
      setMensaje(exito);
    } else {
      setError(r.error);
      await cargar();
    }
  }

  if (!cursoId || !tareaId || !tarea) {
    return (
      <main style={{ maxWidth: 900, margin: "4rem auto", fontFamily: "sans-serif" }}>
        <p>Cargando…</p>
      </main>
    );
  }

  const base = tarea.repositorio_base;
  const baseOperable = base !== null && (base.estado === "CREADO_VACIO" || base.estado === "LISTO");

  async function onSubir(evento: React.FormEvent) {
    evento.preventDefault();
    if (!archivoNuevo || !cursoId || !tareaId) return;
    const ruta = rutaNueva.trim() || archivoNuevo.name;
    const contenido = await leerComoBase64(archivoNuevo);
    await ejecutar(() => escribirArchivoBase(cursoId, tareaId, ruta, contenido), `Se subió ${ruta}.`);
    setArchivoNuevo(null);
    setRutaNueva("");
  }

  async function onReemplazo(archivos: FileList | null) {
    const archivo = archivos?.[0];
    if (!archivo || !rutaReemplazo || !cursoId || !tareaId) return;
    const ruta = rutaReemplazo;
    const contenido = await leerComoBase64(archivo);
    await ejecutar(() => escribirArchivoBase(cursoId, tareaId, ruta, contenido), `Se reemplazó ${ruta}.`);
    setRutaReemplazo(null);
    if (reemplazoRef.current) reemplazoRef.current.value = "";
  }

  async function onPrevisualizar(ruta: string) {
    if (!cursoId || !tareaId) return;
    setError(null);
    const r = await previsualizarArchivoBase(cursoId, tareaId, ruta);
    if (r.ok && r.datos) setVista(r.datos);
    else setError(r.error);
  }

  return (
    <main style={{ maxWidth: 900, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <p>
        <Link to={`/cursos/${cursoId}/tareas`}>← Tareas</Link>
      </p>
      <h1>{tarea.nombre}</h1>
      <p>
        <code>{tarea.slug}</code> · {textoModalidad(tarea.modalidad)} · <strong>{textoEstadoTarea(tarea.estado)}</strong>
        {tarea.activada_en && ` desde el ${fechaLegible(tarea.activada_en)}`}
      </p>

      {mensaje && <p role="status">{mensaje}</p>}
      {error && (
        <div role="alert" style={ESTILO_ERROR}>
          {error}
        </div>
      )}

      {tarea.estado === "BORRADOR" && (
        <section>
          <h2>Activar la tarea</h2>
          <p style={ESTILO_MOTIVO}>
            Activar es el único paso manual: después, los repositorios de los estudiantes se crean solos, a medida que
            cada uno tiene su información completa.
          </p>
          <button
            disabled={!tarea.activar.habilitada || ocupado}
            onClick={() => ejecutar(() => activarTarea(cursoId, tareaId), "La tarea quedó activa.")}
          >
            Activar tarea
          </button>
          {tarea.activar.motivo && <p style={ESTILO_MOTIVO}>{tarea.activar.motivo}</p>}
        </section>
      )}

      {tarea.estado !== "BORRADOR" && <BloqueRepositorios cursoId={cursoId} tareaId={tareaId} />}

      <section>
        <h2>Entregas</h2>
        {tarea.entregas.length === 0 ? (
          <p>Esta tarea no tiene entregas vinculadas.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Orden</th>
                <th>Tipo</th>
                <th>Tarea de Canvas</th>
                <th>Cierre en Canvas</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {tarea.entregas.map((e) => (
                <tr key={e.id}>
                  <td>{e.orden}</td>
                  <td>{textoTipoEntrega(e.tipo)}</td>
                  <td>
                    {e.nombre}
                    {!e.publicada && <span style={ESTILO_MOTIVO}> (sin publicar)</span>}
                  </td>
                  <td>{fechaLegible(e.due_at_base)}</td>
                  <td>{textoEstadoEntrega(e.estado_validacion)}</td>
                  <td>
                    <button
                      disabled={ocupado}
                      onClick={() => {
                        if (window.confirm(`¿Desvincular «${e.nombre}» de esta tarea?`)) {
                          ejecutar(() => desvincularEntrega(cursoId, tareaId, e.id), "Entrega desvinculada.");
                        }
                      }}
                    >
                      Desvincular
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <LineaFechas cursoId={cursoId} tareaId={tareaId} />
        <p>
          <button disabled>Vincular otra entrega</button>{" "}
          {tarea.vincular_otra_entrega.motivo && (
            <span style={ESTILO_MOTIVO}>{tarea.vincular_otra_entrega.motivo}</span>
          )}
        </p>
      </section>

      <section>
        <h2>Repositorio base</h2>
        {base === null ? (
          <>
            <p>
              Opcional. Si lo creas, cada repositorio de estudiante se genera a partir de él. Se llamará{" "}
              <code>{tarea.nombre_repositorio_base}</code>.
            </p>
            <button
              disabled={!tarea.crear_repositorio_base.habilitada || ocupado}
              onClick={() =>
                ejecutar(() => crearRepositorioBase(cursoId, tareaId), "Repositorio base creado en GitHub.")
              }
            >
              {ocupado ? "Creando en GitHub…" : "Crear repositorio base"}
            </button>
            {tarea.crear_repositorio_base.motivo && (
              <p style={ESTILO_MOTIVO}>{tarea.crear_repositorio_base.motivo}</p>
            )}
          </>
        ) : (
          <>
            <p>
              {base.url_html ? (
                <a href={base.url_html} target="_blank" rel="noreferrer">
                  {base.full_name ?? base.nombre}
                </a>
              ) : (
                <code>{base.nombre}</code>
              )}{" "}
              · <strong>{textoEstadoBase(base.estado)}</strong>
              {base.rama_por_defecto && ` · rama ${base.rama_por_defecto}`}
            </p>
            {base.error_mensaje_literal && (
              <div role="alert" style={ESTILO_ERROR}>
                {base.error_mensaje_literal}
              </div>
            )}
            {(base.estado === "ERROR" || base.estado === "CREANDO") && tarea.crear_repositorio_base.habilitada && (
              <button
                disabled={ocupado}
                onClick={() => ejecutar(() => crearRepositorioBase(cursoId, tareaId), "Repositorio base creado.")}
              >
                Reintentar la creación
              </button>
            )}

            {baseOperable && (
              <>
                <p style={ESTILO_MOTIVO}>
                  Los cambios en el repositorio base no se propagan a los repositorios de estudiantes que ya se hayan
                  creado: cada uno copia el base una sola vez, al crearse.
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>Archivo</th>
                      <th>Tamaño</th>
                      <th>Actualizado</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {base.archivos.map((a) => (
                      <tr key={a.ruta}>
                        <td>
                          {renombrando?.desde === a.ruta ? (
                            <input
                              value={renombrando.hacia}
                              onChange={(e) => setRenombrando({ desde: a.ruta, hacia: e.target.value })}
                            />
                          ) : (
                            <code>{a.ruta}</code>
                          )}
                        </td>
                        <td>{tamanoLegible(a.tamano_bytes)}</td>
                        <td>{fechaLegible(a.actualizado_en)}</td>
                        <td style={{ whiteSpace: "nowrap" }}>
                          {renombrando?.desde === a.ruta ? (
                            <>
                              <button
                                disabled={ocupado}
                                onClick={() => {
                                  const { desde, hacia } = renombrando;
                                  setRenombrando(null);
                                  ejecutar(
                                    () => renombrarArchivoBase(cursoId, tareaId, desde, hacia),
                                    `Se renombró ${desde} a ${hacia}.`,
                                  );
                                }}
                              >
                                Guardar
                              </button>{" "}
                              <button onClick={() => setRenombrando(null)}>Cancelar</button>
                            </>
                          ) : (
                            <>
                              <button onClick={() => onPrevisualizar(a.ruta)}>Ver</button>{" "}
                              <button
                                disabled={ocupado}
                                onClick={() => {
                                  setRutaReemplazo(a.ruta);
                                  reemplazoRef.current?.click();
                                }}
                              >
                                Reemplazar
                              </button>{" "}
                              <button disabled={ocupado} onClick={() => setRenombrando({ desde: a.ruta, hacia: a.ruta })}>
                                Renombrar
                              </button>{" "}
                              <button
                                disabled={ocupado}
                                onClick={() => {
                                  if (window.confirm(`¿Borrar ${a.ruta} del repositorio base?`)) {
                                    ejecutar(() => borrarArchivoBase(cursoId, tareaId, a.ruta), `Se borró ${a.ruta}.`);
                                  }
                                }}
                              >
                                Borrar
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <input
                  ref={reemplazoRef}
                  type="file"
                  style={{ display: "none" }}
                  onChange={(e) => onReemplazo(e.target.files)}
                />

                <form onSubmit={onSubir} style={{ marginTop: "1rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                  <input type="file" onChange={(e) => setArchivoNuevo(e.target.files?.[0] ?? null)} required />
                  <input
                    value={rutaNueva}
                    onChange={(e) => setRutaNueva(e.target.value)}
                    placeholder={archivoNuevo ? archivoNuevo.name : "ruta en el repositorio, p. ej. src/main.py"}
                  />
                  <button type="submit" disabled={!archivoNuevo || ocupado}>
                    {ocupado ? "Subiendo…" : "Subir archivo"}
                  </button>
                </form>
                <p style={ESTILO_MOTIVO}>Máximo 1 MB por archivo. No se admiten archivos dentro de .github/workflows/.</p>

                {vista && (
                  <div style={{ marginTop: "1rem" }}>
                    <h3>
                      {vista.ruta} <button onClick={() => setVista(null)}>Cerrar</button>
                    </h3>
                    {vista.texto !== null ? (
                      <pre style={{ background: "#f4f6f8", padding: "0.75rem", overflowX: "auto" }}>{vista.texto}</pre>
                    ) : (
                      <p>{vista.motivo_sin_texto}</p>
                    )}
                  </div>
                )}
              </>
            )}
          </>
        )}
      </section>
    </main>
  );
}
