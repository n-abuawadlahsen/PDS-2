import { useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
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
import { useCurso } from "../components/Layout";
import {
  Aviso,
  Cabecera,
  Cargando,
  ErrorCarga,
  Estado,
  Mensajes,
  Tabla,
  Vacio,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import { BloqueRepositorios, LineaFechas } from "./RepositoriosTarea";
function leerComoBase64(archivo: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const lector = new FileReader();
    lector.onload = () => resolve(String(lector.result).split(",", 2)[1] ?? "");
    lector.onerror = () =>
      reject(new Error("No pudimos leer el archivo seleccionado."));
    lector.readAsDataURL(archivo);
  });
}
export function Tarea() {
  const { tareaId = "" } = useParams();
  return <EditorTarea key={tareaId} tareaId={tareaId} />;
}
function EditorTarea({ tareaId }: { tareaId: string }) {
  const { curso, puede } = useCurso();
  const cursoId = curso.id;
  const administra = puede("tarea.administrar");
  const consulta = useConsulta(`tarea-${cursoId}-${tareaId}`, (signal) =>
    obtenerTarea(cursoId, tareaId, signal),
  );
  const [params, setParams] = useSearchParams();
  const pestana = params.get("vista") ?? "resumen";
  const [rutaNueva, setRutaNueva] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [renombrando, setRenombrando] = useState<{
    desde: string;
    hacia: string;
  } | null>(null);
  const [vista, setVista] = useState<PrevisualizacionArchivo | null>(null);
  const reemplazoRef = useRef<HTMLInputElement>(null);
  const nuevoRef = useRef<HTMLInputElement>(null);
  const rutaReemplazo = useRef("");
  const op = useOperacion();
  const confirmar = useConfirmar();
  const tarea = consulta.datos;
  async function cambiar(accion: () => Promise<Resultado<TareaDetalle>>) {
    const r = await accion();
    if (!r.ok || !r.datos)
      throw new Error(r.error ?? "No se pudo completar la operación.");
    consulta.actualizar(r.datos);
    return true;
  }
  if (!tarea)
    return consulta.error ? (
      <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
    ) : (
      <Cargando texto="Consultando la tarea…" />
    );
  const base = tarea.repositorio_base;
  const baseOperable = base && ["LISTO", "CREADO_VACIO"].includes(base.estado);
  const pestanas = [
    ["resumen", "Resumen"],
    ["entrega", "Entrega y fechas"],
    ["base", "Repositorio base"],
    ["repositorios", "Repositorios de estudiantes"],
  ];
  const pestanaValida = pestanas.some(([p]) => p === pestana)
    ? pestana
    : "resumen";
  return (
    <>
      <p className="help">
        <Link to={`/cursos/${cursoId}/tareas`}>← Todas las tareas</Link>
      </p>
      <Cabecera
        titulo={tarea.nombre}
        descripcion={`${textoModalidad(tarea.modalidad)} · ${tarea.slug}`}
        acciones={
          <Estado valor={tarea.estado} texto={textoEstadoTarea(tarea.estado)} />
        }
      />
      <Mensajes {...op} />
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      <nav className="tabs" aria-label="Secciones de la tarea">
        {pestanas.map(([clave, nombre]) => (
          <Link
            key={clave}
            to={`?vista=${clave}`}
            aria-current={pestanaValida === clave ? "page" : undefined}
          >
            {nombre}
          </Link>
        ))}
      </nav>
      {!administra && (
        <Aviso>
          Estás consultando esta tarea. No tienes permiso para administrarla.
        </Aviso>
      )}
      <div hidden={pestanaValida !== "resumen"} className="stack">
        <section className="panel">
          <h2>
            {tarea.estado === "BORRADOR"
              ? "Preparar y activar"
              : "Estado de la tarea"}
          </h2>
          <p>
            {tarea.entregas.length} entrega vinculada ·{" "}
            {base
              ? `Repositorio base: ${textoEstadoBase(base.estado)}`
              : "Sin repositorio base"}
          </p>
          {tarea.activada_en && (
            <p>
              Activada el {fechaLegible(tarea.activada_en, curso.zona_horaria)}.
            </p>
          )}
          {tarea.estado === "BORRADOR" ? (
            <>
              <p>
                Al activar esta tarea, los repositorios se crearán
                automáticamente a medida que cada estudiante tenga la
                información necesaria. Quienes aún no tengan una cuenta GitHub
                asociada quedarán pendientes y continuarán cuando la completen.
              </p>
              {administra && (
                <button
                  className="primary"
                  disabled={op.ocupado || !tarea.activar.habilitada}
                  onClick={() =>
                    void op.ejecutar(async () => {
                      await cambiar(() => activarTarea(cursoId, tareaId));
                      setParams({ vista: "repositorios" });
                    }, "La tarea está activa. Comenzó el proceso automático de creación; los repositorios aparecerán progresivamente.")
                  }
                >
                  {op.ocupado ? "Activando…" : "Activar tarea"}
                </button>
              )}
              {tarea.activar.motivo && (
                <p className="help">{tarea.activar.motivo}</p>
              )}
              <p className="help">
                Puedes añadir archivos iniciales en{" "}
                <Link to="?vista=base">Repositorio base</Link> antes de activar.
              </p>
            </>
          ) : (
            <>
              <p>
                La creación y la configuración de accesos se realizan
                automáticamente. Consulta por separado el estado de cada
                repositorio y sus invitaciones.
              </p>
              <Link className="button primary" to="?vista=repositorios">
                Ver progreso de repositorios
              </Link>
            </>
          )}
        </section>
        <section className="panel">
          <h2>Información académica</h2>
          <p>
            Las fechas provienen de Canvas y se consultan en la zona horaria{" "}
            {curso.zona_horaria}. En esta versión hay una entrega por tarea.
          </p>
          <Link to="?vista=entrega">Consultar entrega y fechas</Link>
        </section>
      </div>
      <section hidden={pestanaValida !== "entrega"} className="panel">
        <h2>Entrega y fechas</h2>
        <p className="help">
          Solo lectura desde Canvas · {curso.zona_horaria}. «Final» identifica
          la entrega de esta tarea.
        </p>
        {!tarea.entregas.length ? (
          <Vacio>No hay entregas vinculadas a esta tarea.</Vacio>
        ) : (
          <Tabla etiqueta="Entrega de la tarea">
            <table>
              <thead>
                <tr>
                  <th scope="col">Tarea de Canvas</th>
                  <th scope="col">Entrega</th>
                  <th scope="col">Cierre</th>
                  <th scope="col">Estado</th>
                  <th scope="col">Acción</th>
                </tr>
              </thead>
              <tbody>
                {tarea.entregas.map((e) => (
                  <tr key={e.id}>
                    <td>
                      {e.nombre}
                      {!e.publicada && (
                        <p className="help">Sin publicar en Canvas</p>
                      )}
                    </td>
                    <td>
                      {textoTipoEntrega(e.tipo)} · {e.orden}
                    </td>
                    <td>{fechaLegible(e.due_at_base, curso.zona_horaria)}</td>
                    <td>{textoEstadoEntrega(e.estado_validacion)}</td>
                    <td>
                      {administra && (
                        <button
                          className="danger"
                          disabled={op.ocupado}
                          onClick={async () => {
                            if (
                              await confirmar({
                                titulo: "Desvincular entrega",
                                descripcion: `Se quitará la relación con «${e.nombre}» en esta tarea. El servidor verificará si esta acción está permitida.`,
                                accion: "Desvincular",
                                peligro: true,
                              })
                            )
                              void op.ejecutar(
                                () =>
                                  cambiar(() =>
                                    desvincularEntrega(cursoId, tareaId, e.id),
                                  ),
                                "Entrega desvinculada.",
                              );
                          }}
                        >
                          Desvincular
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Tabla>
        )}
        <LineaFechas cursoId={cursoId} tareaId={tareaId} />
        <div className="actions">
          <button disabled>Vincular otra entrega</button>
        </div>
        <p className="help">
          {tarea.vincular_otra_entrega.motivo ??
            "Esta versión permite una sola entrega por tarea."}
        </p>
      </section>
      <section hidden={pestanaValida !== "base"} className="panel">
        <h2>Repositorio base opcional</h2>
        <p>
          Contiene los archivos iniciales que se copian al crear cada
          repositorio. Cambiar la base no modifica los repositorios de
          estudiantes ya creados.
        </p>
        {!base ? (
          <>
            <p>
              Nombre previsto: <code>{tarea.nombre_repositorio_base}</code>.
            </p>
            {administra && (
              <button
                className="primary"
                disabled={
                  op.ocupado || !tarea.crear_repositorio_base.habilitada
                }
                onClick={() =>
                  void op.ejecutar(
                    () => cambiar(() => crearRepositorioBase(cursoId, tareaId)),
                    "Repositorio base creado en GitHub.",
                  )
                }
              >
                {op.ocupado ? "Creando base…" : "Crear repositorio base"}
              </button>
            )}
            {tarea.crear_repositorio_base.motivo && (
              <p className="help">{tarea.crear_repositorio_base.motivo}</p>
            )}
          </>
        ) : (
          <>
            <div className="panel-header">
              <div>
                {base.url_html ? (
                  <a href={base.url_html} target="_blank" rel="noreferrer">
                    {base.full_name ?? base.nombre}
                    <span className="sr-only">
                      {" "}
                      (abre GitHub en otra pestaña)
                    </span>
                  </a>
                ) : (
                  <code>{base.nombre}</code>
                )}
                <p className="help">
                  Rama: {base.rama_por_defecto ?? "Todavía no informada"}
                </p>
              </div>
              <Estado
                valor={base.estado}
                texto={textoEstadoBase(base.estado)}
              />
            </div>
            {base.error_mensaje_literal && (
              <ErrorCarga error={base.error_mensaje_literal} />
            )}
            {administra &&
              ["ERROR", "CREANDO"].includes(base.estado) &&
              tarea.crear_repositorio_base.habilitada && (
                <button
                  disabled={op.ocupado}
                  onClick={() =>
                    void op.ejecutar(
                      () =>
                        cambiar(() => crearRepositorioBase(cursoId, tareaId)),
                      "Estado del repositorio base actualizado.",
                    )
                  }
                >
                  Reintentar creación de base
                </button>
              )}
            {baseOperable && (
              <>
                {!base.archivos.length ? (
                  <Vacio>
                    La base aún no contiene archivos. Añade los archivos
                    iniciales para prepararla.
                  </Vacio>
                ) : (
                  <Tabla etiqueta="Archivos del repositorio base">
                    <table>
                      <thead>
                        <tr>
                          <th scope="col">Archivo</th>
                          <th scope="col">Tamaño</th>
                          <th scope="col">Actualización</th>
                          <th scope="col">Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {base.archivos.map((a) => (
                          <tr key={a.ruta}>
                            <td>
                              <code>{a.ruta}</code>
                            </td>
                            <td>{tamanoLegible(a.tamano_bytes)}</td>
                            <td>
                              {fechaLegible(
                                a.actualizado_en,
                                curso.zona_horaria,
                              )}
                            </td>
                            <td>
                              {renombrando?.desde === a.ruta ? (
                                <form
                                  onSubmit={(e) => {
                                    e.preventDefault();
                                    const r = renombrando;
                                    void op.ejecutar(async () => {
                                      await cambiar(() =>
                                        renombrarArchivoBase(
                                          cursoId,
                                          tareaId,
                                          r.desde,
                                          r.hacia,
                                        ),
                                      );
                                      setRenombrando(null);
                                    }, "Archivo renombrado.");
                                  }}
                                >
                                  <label>
                                    Nueva ruta
                                    <input
                                      value={renombrando.hacia}
                                      onChange={(e) =>
                                        setRenombrando({
                                          ...renombrando,
                                          hacia: e.target.value,
                                        })
                                      }
                                      required
                                      autoFocus
                                    />
                                  </label>
                                  <div className="actions">
                                    <button disabled={op.ocupado}>
                                      Guardar
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => setRenombrando(null)}
                                    >
                                      Cancelar
                                    </button>
                                  </div>
                                </form>
                              ) : (
                                <div className="actions">
                                  <button
                                    disabled={op.ocupado}
                                    onClick={() =>
                                      void op.ejecutar(async () => {
                                        const r =
                                          await previsualizarArchivoBase(
                                            cursoId,
                                            tareaId,
                                            a.ruta,
                                          );
                                        if (!r.ok || !r.datos)
                                          throw new Error(
                                            r.error ??
                                              "No se pudo abrir el archivo.",
                                          );
                                        setVista(r.datos);
                                      })
                                    }
                                  >
                                    Ver
                                  </button>
                                  {administra && (
                                    <>
                                      <button
                                        disabled={op.ocupado}
                                        onClick={() => {
                                          rutaReemplazo.current = a.ruta;
                                          reemplazoRef.current?.click();
                                        }}
                                      >
                                        Reemplazar
                                      </button>
                                      <button
                                        disabled={op.ocupado}
                                        onClick={() =>
                                          setRenombrando({
                                            desde: a.ruta,
                                            hacia: a.ruta,
                                          })
                                        }
                                      >
                                        Renombrar
                                      </button>
                                      <button
                                        className="danger"
                                        disabled={op.ocupado}
                                        onClick={async () => {
                                          if (
                                            await confirmar({
                                              titulo:
                                                "Borrar archivo de la base",
                                              descripcion: `Se borrará ${a.ruta} del repositorio base. Los repositorios de estudiantes ya creados no cambian.`,
                                              accion: "Borrar archivo",
                                              peligro: true,
                                            })
                                          )
                                            void op.ejecutar(
                                              () =>
                                                cambiar(() =>
                                                  borrarArchivoBase(
                                                    cursoId,
                                                    tareaId,
                                                    a.ruta,
                                                  ),
                                                ),
                                              "Archivo borrado de la base.",
                                            );
                                        }}
                                      >
                                        Borrar
                                      </button>
                                    </>
                                  )}
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </Tabla>
                )}
                {administra && (
                  <>
                    <input
                      ref={reemplazoRef}
                      type="file"
                      className="sr-only"
                      tabIndex={-1}
                      aria-label="Archivo de reemplazo"
                      onChange={async (e) => {
                        const elegido = e.target.files?.[0];
                        const ruta = rutaReemplazo.current;
                        e.target.value = "";
                        if (!elegido) return;
                        if (
                          await confirmar({
                            titulo: "Reemplazar archivo",
                            descripcion: `${ruta} se reemplazará con ${elegido.name}. Los repositorios ya creados no cambian.`,
                            accion: "Reemplazar",
                          })
                        )
                          void op.ejecutar(async () => {
                            const contenido = await leerComoBase64(elegido);
                            await cambiar(() =>
                              escribirArchivoBase(
                                cursoId,
                                tareaId,
                                ruta,
                                contenido,
                              ),
                            );
                          }, "Archivo reemplazado.");
                      }}
                    />
                    <form
                      className="form-stack"
                      onSubmit={async (e) => {
                        e.preventDefault();
                        if (!archivo) return;
                        const ruta = rutaNueva.trim() || archivo.name;
                        if (
                          base.archivos.some((a) => a.ruta === ruta) &&
                          !(await confirmar({
                            titulo: "Reemplazar archivo existente",
                            descripcion: `Ya existe ${ruta}. Se reemplazará su contenido en la base.`,
                            accion: "Reemplazar",
                          }))
                        )
                          return;
                        void op.ejecutar(async () => {
                          const contenido = await leerComoBase64(archivo);
                          await cambiar(() =>
                            escribirArchivoBase(
                              cursoId,
                              tareaId,
                              ruta,
                              contenido,
                            ),
                          );
                          setArchivo(null);
                          setRutaNueva("");
                          if (nuevoRef.current) nuevoRef.current.value = "";
                        }, "Archivo guardado en el repositorio base.");
                      }}
                    >
                      <h3>Añadir archivo</h3>
                      <label>
                        Archivo inicial
                        <input
                          ref={nuevoRef}
                          type="file"
                          required
                          disabled={op.ocupado}
                          onChange={(e) =>
                            setArchivo(e.target.files?.[0] ?? null)
                          }
                        />
                      </label>
                      <label>
                        Ruta dentro del repositorio (opcional)
                        <input
                          value={rutaNueva}
                          onChange={(e) => setRutaNueva(e.target.value)}
                          placeholder={archivo?.name ?? "src/main.py"}
                          disabled={op.ocupado}
                        />
                      </label>
                      <p className="help">
                        Máximo 1 MB por archivo. No se admiten archivos dentro
                        de .github/workflows/.
                      </p>
                      <div>
                        <button
                          className="primary"
                          disabled={op.ocupado || !archivo}
                        >
                          {op.ocupado ? "Guardando archivo…" : "Subir archivo"}
                        </button>
                      </div>
                    </form>
                  </>
                )}
              </>
            )}
          </>
        )}
        {vista && (
          <section className="panel">
            <div className="panel-header">
              <h3>{vista.ruta}</h3>
              <button onClick={() => setVista(null)}>
                Cerrar vista previa
              </button>
            </div>
            {vista.texto !== null ? (
              <pre>{vista.texto}</pre>
            ) : (
              <p>{vista.motivo_sin_texto}</p>
            )}
          </section>
        )}
      </section>
      <section hidden={pestanaValida !== "repositorios"} className="panel">
        {tarea.estado !== "BORRADOR" ? (
          <BloqueRepositorios cursoId={cursoId} tareaId={tareaId} />
        ) : (
          <Vacio>
            <h2>La tarea todavía es un borrador</h2>
            <p>La creación automática comienza después de activarla.</p>
            <Link to="?vista=resumen">Revisar y activar la tarea</Link>
          </Vacio>
        )}
      </section>
    </>
  );
}
