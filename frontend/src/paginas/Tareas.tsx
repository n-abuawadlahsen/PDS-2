import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  crearTarea,
  listarTareas,
  obtenerAssignmentsCanvas,
  obtenerVistaPreviaNombre,
  sincronizarAhora,
} from "../lib/api";
import { comprobar } from "../lib/errores";
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
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import {
  fechaLegible,
  textoEstadoBase,
  textoEstadoTarea,
  textoModalidad,
} from "../lib/textosTarea";
export function Tareas() {
  const { curso, puede } = useCurso();
  const navegar = useNavigate();
  const op = useOperacion();
  const lista = useConsulta(`tareas-${curso.id}`, (signal) =>
    listarTareas(curso.id, signal),
  );
  const [sincronizacion, setSincronizacion] = useState<{
    anterior: string | null;
  } | null>(null);
  const canvas = useConsulta(
    `assignments-${curso.id}`,
    (signal) => obtenerAssignmentsCanvas(curso.id, signal),
    sincronizacion ? 10_000 : 0,
  );
  const [crear, setCrear] = useState(false);
  const [assignment, setAssignment] = useState("");
  const [nombre, setNombre] = useState("");
  const [slug, setSlug] = useState("");
  const [gitignore, setGitignore] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [previewClave, setPreviewClave] = useState({ nombre: "", slug: "" });
  useEffect(() => {
    const t = setTimeout(() => setPreviewClave({ nombre, slug }), 300);
    return () => clearTimeout(t);
  }, [nombre, slug]);
  const preview = useConsulta(
    JSON.stringify([
      "preview",
      curso.id,
      previewClave.nombre,
      previewClave.slug,
    ]),
    (signal) =>
      previewClave.nombre.trim()
        ? obtenerVistaPreviaNombre(
            curso.id,
            previewClave.nombre,
            previewClave.slug,
            signal,
          )
        : Promise.resolve(null),
  );
  useEffect(() => {
    if (
      sincronizacion &&
      canvas.datos?.sincronizado_en &&
      canvas.datos.sincronizado_en !== sincronizacion.anterior
    ) {
      setSincronizacion(null);
      op.setMensaje("Las tareas de Canvas se actualizaron.");
    }
  }, [canvas.datos, sincronizacion]);
  const vistaVigente =
    previewClave.nombre === nombre && previewClave.slug === slug;
  const elegida = canvas.datos?.assignments.find(
    (a) => String(a.canvas_assignment_id) === assignment,
  );
  const tareas = lista.datos?.filter((t) =>
    t.nombre
      .toLocaleLowerCase("es-CL")
      .includes(busqueda.toLocaleLowerCase("es-CL")),
  );
  return (
    <>
      <Cabecera
        titulo="Tareas"
        descripcion="Configura tareas individuales desde Canvas y consulta la creación automática de sus repositorios."
        acciones={
          puede("tarea.administrar") &&
          !crear && (
            <button className="primary" onClick={() => setCrear(true)}>
              Crear tarea
            </button>
          )
        }
      />
      <Mensajes {...op} />
      {!puede("tarea.administrar") && (
        <Aviso>
          No tienes permiso para administrar las tareas de este curso. Puedes
          consultar sus entregas y repositorios.
        </Aviso>
      )}
      {crear && puede("tarea.administrar") && (
        <section className="panel">
          <h2>Crear tarea individual</h2>
          <p>
            La tarea de Canvas seleccionada será la única entrega de esta tarea.
            Se creará primero como borrador.
          </p>
          {canvas.error && (
            <ErrorCarga error={canvas.error} reintentar={canvas.recargar} />
          )}
          {!canvas.datos ? (
            !canvas.error && <Cargando />
          ) : (
            <>
              <p className="help">
                Canvas:{" "}
                {canvas.datos.sincronizado_en
                  ? `sincronizado el ${fechaLegible(canvas.datos.sincronizado_en, curso.zona_horaria)}`
                  : "sin sincronizar"}
                .
              </p>
              {puede("curso.administrar") && (
                <button
                  disabled={op.ocupado || Boolean(sincronizacion)}
                  onClick={() =>
                    void op.ejecutar(async () => {
                      await comprobar(await sincronizarAhora(curso.id));
                      setSincronizacion({
                        anterior: canvas.datos!.sincronizado_en,
                      });
                    }, "Sincronización solicitada. Esperaremos los datos actualizados de Canvas.")
                  }
                >
                  {sincronizacion
                    ? "Sincronización solicitada"
                    : "Sincronizar tareas de Canvas"}
                </button>
              )}
              {!canvas.datos.assignments.length ? (
                <Vacio>
                  No hay tareas de Canvas sincronizadas. Un profesor puede
                  solicitar la sincronización.
                </Vacio>
              ) : (
                <form
                  className="form-stack"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void op.ejecutar(async () => {
                      const r = await crearTarea(curso.id, {
                        nombre,
                        slug: slug.trim() || null,
                        canvas_assignment_id: Number(assignment),
                        gitignore_template: gitignore || null,
                      });
                      if (!r.ok || !r.datos)
                        throw new Error(
                          r.error ?? "No se pudo crear la tarea.",
                        );
                      navegar(`/cursos/${curso.id}/tareas/${r.datos.id}`);
                    });
                  }}
                >
                  <label>
                    Tarea de Canvas
                    <select
                      value={assignment}
                      required
                      onChange={(e) => {
                        setAssignment(e.target.value);
                        const a = canvas.datos!.assignments.find(
                          (a) =>
                            String(a.canvas_assignment_id) === e.target.value,
                        );
                        if (a && !nombre.trim()) setNombre(a.nombre);
                      }}
                    >
                      <option value="">Selecciona una tarea…</option>
                      {canvas.datos.assignments.map((a) => (
                        <option
                          key={a.canvas_assignment_id}
                          value={a.canvas_assignment_id}
                          disabled={!a.seleccionable}
                        >
                          {a.nombre}
                          {a.motivo ? ` — ${a.motivo}` : ""}
                        </option>
                      ))}
                    </select>
                  </label>
                  {canvas.datos.assignments.some((a) => !a.seleccionable) && (
                    <details>
                      <summary>
                        Por qué algunas tareas no están disponibles
                      </summary>
                      <ul>
                        {canvas.datos.assignments
                          .filter((a) => !a.seleccionable)
                          .map((a) => (
                            <li key={a.canvas_assignment_id}>
                              {a.nombre}:{" "}
                              {a.motivo ??
                                "No disponible para esta configuración"}
                            </li>
                          ))}
                      </ul>
                    </details>
                  )}
                  {elegida && (
                    <p className="help">
                      Cierre: {fechaLegible(elegida.due_at, curso.zona_horaria)}{" "}
                      ·{" "}
                      {elegida.publicada
                        ? "Publicada en Canvas"
                        : "Sin publicar en Canvas"}
                    </p>
                  )}
                  <label>
                    Nombre de la tarea
                    <input
                      required
                      value={nombre}
                      onChange={(e) => setNombre(e.target.value)}
                    />
                  </label>
                  <label>
                    Identificador corto (opcional)
                    <input
                      maxLength={24}
                      value={slug}
                      onChange={(e) => setSlug(e.target.value)}
                      placeholder={preview.datos?.slug ?? "tarea-1"}
                      aria-describedby="tarea-slug-ayuda"
                      aria-invalid={Boolean(
                        vistaVigente &&
                        preview.datos &&
                        (!preview.datos.slug_valido ||
                          preview.datos.slug_ocupado),
                      )}
                    />
                    <span id="tarea-slug-ayuda" className="help">
                      Si lo dejas vacío, se deriva del nombre. Solo minúsculas,
                      números y guiones; máximo 24 caracteres.
                    </span>
                  </label>
                  <label>
                    Plantilla .gitignore sin repositorio base (opcional)
                    <select
                      value={gitignore}
                      onChange={(e) => setGitignore(e.target.value)}
                    >
                      <option value="">Ninguna</option>
                      {canvas.datos.plantillas_gitignore.map((p) => (
                        <option key={p}>{p}</option>
                      ))}
                    </select>
                  </label>
                  {preview.error && (
                    <ErrorCarga
                      error={preview.error}
                      reintentar={preview.recargar}
                    />
                  )}
                  {nombre && (!vistaVigente || preview.cargando) && (
                    <Cargando texto="Calculando nombres de repositorio…" />
                  )}
                  {vistaVigente && preview.datos && (
                    <Aviso
                      tipo={
                        !preview.datos.slug_valido || preview.datos.slug_ocupado
                          ? "warning"
                          : "info"
                      }
                    >
                      {!preview.datos.slug_valido ? (
                        "El identificador no es válido."
                      ) : preview.datos.slug_ocupado ? (
                        "Este identificador ya está en uso en el curso."
                      ) : (
                        <>
                          <strong>Vista previa de nombres</strong>
                          <p>
                            Repositorio de {preview.datos.ejemplo_sujeto}:{" "}
                            <code>{preview.datos.ejemplo_repositorio}</code>
                          </p>
                          <p>
                            Base opcional:{" "}
                            <code>{preview.datos.repositorio_base}</code>
                          </p>
                          <p>
                            Los nombres no cambian después de crear los
                            repositorios.
                          </p>
                        </>
                      )}
                    </Aviso>
                  )}
                  <div className="actions">
                    <button
                      className="primary"
                      disabled={
                        op.ocupado ||
                        !elegida?.seleccionable ||
                        !vistaVigente ||
                        preview.cargando ||
                        !preview.datos?.slug_valido ||
                        preview.datos.slug_ocupado
                      }
                    >
                      {op.ocupado ? "Creando tarea…" : "Crear borrador"}
                    </button>
                    <button
                      type="button"
                      disabled={op.ocupado}
                      onClick={() => setCrear(false)}
                    >
                      Cancelar
                    </button>
                  </div>
                </form>
              )}
            </>
          )}
        </section>
      )}
      <section className="panel">
        <h2>Tareas del curso</h2>
        {lista.error && (
          <ErrorCarga error={lista.error} reintentar={lista.recargar} />
        )}
        {!tareas ? (
          !lista.error && <Cargando />
        ) : (
          <>
            <div className="filters">
              <label>
                Buscar tarea
                <input
                  type="search"
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  placeholder="Nombre de la tarea"
                />
              </label>
            </div>
            {!tareas.length ? (
              <Vacio>
                {lista.datos?.length
                  ? "No hay tareas con ese nombre."
                  : "Todavía no hay tareas. Crea la primera desde una tarea de Canvas."}
              </Vacio>
            ) : (
              <Tabla etiqueta="Tareas del curso">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Tarea</th>
                      <th scope="col">Modalidad</th>
                      <th scope="col">Estado</th>
                      <th scope="col">Entregas</th>
                      <th scope="col">Repositorio base</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tareas.map((t) => (
                      <tr key={t.id}>
                        <td>
                          <Link to={`/cursos/${curso.id}/tareas/${t.id}`}>
                            {t.nombre}
                          </Link>
                          <p className="help">{t.slug}</p>
                        </td>
                        <td>{textoModalidad(t.modalidad)}</td>
                        <td>
                          <Estado
                            valor={t.estado}
                            texto={textoEstadoTarea(t.estado)}
                          />
                        </td>
                        <td>{t.cantidad_entregas}</td>
                        <td>
                          {t.estado_repositorio_base
                            ? textoEstadoBase(t.estado_repositorio_base)
                            : "Sin base"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Tabla>
            )}
          </>
        )}
      </section>
    </>
  );
}
