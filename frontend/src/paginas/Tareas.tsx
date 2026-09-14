import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  crearTarea,
  listarTareas,
  obtenerAssignmentsCanvas,
  obtenerVistaPreviaNombre,
  sincronizarAhora,
  type AssignmentsCanvas,
  type TareaResumen,
  type VistaPreviaNombre,
} from "../lib/api";
import { fechaLegible, textoEstadoBase, textoEstadoTarea, textoModalidad } from "../lib/textosTarea";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;

/** `/cursos/{id}/tareas` (SPEC 13 S13.5.1): lista de tareas y alta con vista
 * previa en vivo del nombre de repositorio que resultara (R2.3.1). */
export function Tareas() {
  const { cursoId } = useParams<{ cursoId: string }>();
  const navegar = useNavigate();
  const [tareas, setTareas] = useState<TareaResumen[] | null>(null);
  const [canvas, setCanvas] = useState<AssignmentsCanvas | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  const [assignmentId, setAssignmentId] = useState<number | null>(null);
  const [nombre, setNombre] = useState("");
  const [slug, setSlug] = useState("");
  const [gitignore, setGitignore] = useState("");
  const [vista, setVista] = useState<VistaPreviaNombre | null>(null);
  const [creando, setCreando] = useState(false);

  async function cargar() {
    if (!cursoId) return;
    const [lista, espejo] = await Promise.all([listarTareas(cursoId), obtenerAssignmentsCanvas(cursoId)]);
    setTareas(lista);
    setCanvas(espejo);
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId]);

  useEffect(() => {
    if (!cursoId || !nombre.trim()) {
      setVista(null);
      return;
    }
    const temporizador = setTimeout(async () => {
      setVista(await obtenerVistaPreviaNombre(cursoId, nombre, slug));
    }, 300);
    return () => clearTimeout(temporizador);
  }, [cursoId, nombre, slug]);

  async function onSincronizar() {
    if (!cursoId) return;
    const respuesta = await sincronizarAhora(cursoId);
    setMensaje(
      respuesta.ok
        ? "Sincronización encolada. Recarga en unos segundos para ver las tareas de Canvas."
        : `No se pudo encolar (${respuesta.status}).`,
    );
  }

  function onElegirAssignment(valor: string) {
    const id = valor ? Number(valor) : null;
    setAssignmentId(id);
    const elegida = canvas?.assignments.find((a) => a.canvas_assignment_id === id);
    if (elegida && !nombre.trim()) setNombre(elegida.nombre);
  }

  async function onCrear(evento: React.FormEvent) {
    evento.preventDefault();
    if (!cursoId || assignmentId === null) return;
    setCreando(true);
    setMensaje(null);
    const r = await crearTarea(cursoId, {
      nombre,
      slug: slug.trim() || null,
      canvas_assignment_id: assignmentId,
      gitignore_template: gitignore || null,
    });
    setCreando(false);
    if (r.ok && r.datos) {
      navegar(`/cursos/${cursoId}/tareas/${r.datos.id}`);
    } else {
      setMensaje(r.error);
    }
  }

  if (!tareas || !canvas) {
    return (
      <main style={{ maxWidth: 900, margin: "4rem auto", fontFamily: "sans-serif" }}>
        <p>Cargando…</p>
      </main>
    );
  }

  const elegida = canvas.assignments.find((a) => a.canvas_assignment_id === assignmentId);

  return (
    <main style={{ maxWidth: 900, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Tareas</h1>
      {mensaje && <p role="status">{mensaje}</p>}

      <section>
        <h2>Tareas del curso ({tareas.length})</h2>
        {tareas.length === 0 ? (
          <p>Todavía no hay tareas. Crea la primera abajo, a partir de una tarea de Canvas.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Identificador</th>
                <th>Modalidad</th>
                <th>Estado</th>
                <th>Entregas</th>
                <th>Repositorio base</th>
              </tr>
            </thead>
            <tbody>
              {tareas.map((t) => (
                <tr key={t.id}>
                  <td>
                    <Link to={`/cursos/${cursoId}/tareas/${t.id}`}>{t.nombre}</Link>
                  </td>
                  <td>
                    <code>{t.slug}</code>
                  </td>
                  <td>{textoModalidad(t.modalidad)}</td>
                  <td>{textoEstadoTarea(t.estado)}</td>
                  <td>{t.cantidad_entregas}</td>
                  <td>{t.estado_repositorio_base ? textoEstadoBase(t.estado_repositorio_base) : "Sin base"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>Crear tarea</h2>
        <p style={ESTILO_MOTIVO}>
          Tareas de Canvas sincronizadas {canvas.sincronizado_en ? `el ${fechaLegible(canvas.sincronizado_en)}` : "nunca"}.{" "}
          <button type="button" onClick={onSincronizar}>
            Sincronizar ahora
          </button>
        </p>

        {canvas.assignments.length === 0 ? (
          <p>
            Todavía no hay tareas de Canvas en la aplicación. Pulsa «Sincronizar ahora» y recarga la página en unos
            segundos.
          </p>
        ) : (
          <form onSubmit={onCrear} style={{ display: "grid", gap: "0.75rem", maxWidth: 640 }}>
            <label>
              Tarea de Canvas (será la entrega final)
              <br />
              <select value={assignmentId ?? ""} onChange={(e) => onElegirAssignment(e.target.value)} required>
                <option value="">Elige una tarea de Canvas…</option>
                {canvas.assignments.map((a) => (
                  <option key={a.canvas_assignment_id} value={a.canvas_assignment_id} disabled={!a.seleccionable}>
                    {a.nombre}
                    {a.motivo ? ` — ${a.motivo}` : ""}
                  </option>
                ))}
              </select>
            </label>
            {elegida && (
              <p style={ESTILO_MOTIVO}>
                Cierre en Canvas: {fechaLegible(elegida.due_at)} · {elegida.publicada ? "publicada" : "sin publicar"}
              </p>
            )}

            <label>
              Nombre de la tarea
              <br />
              <input value={nombre} onChange={(e) => setNombre(e.target.value)} required style={{ width: "100%" }} />
            </label>

            <label>
              Identificador corto (opcional; se deriva del nombre)
              <br />
              <input
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder={vista?.slug ?? "t1-ordenamiento"}
                maxLength={24}
              />
            </label>

            <label>
              Plantilla .gitignore para repositorios sin base (opcional)
              <br />
              <select value={gitignore} onChange={(e) => setGitignore(e.target.value)}>
                <option value="">Ninguna</option>
                {canvas.plantillas_gitignore.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </label>

            {vista && (
              <div style={{ background: "#f4f6f8", padding: "0.75rem" }}>
                {!vista.slug_valido ? (
                  <p>
                    El identificador «{vista.slug}» no es válido: solo minúsculas, números y guiones, hasta 24
                    caracteres.
                  </p>
                ) : vista.slug_ocupado ? (
                  <p>Ya existe una tarea con el identificador «{vista.slug}» en este curso. Elige otro.</p>
                ) : (
                  <>
                    <p style={{ margin: 0 }}>
                      Repositorio de {vista.ejemplo_sujeto}: <code>{vista.ejemplo_repositorio}</code>
                    </p>
                    <p style={{ margin: 0 }}>
                      Repositorio base, si lo creas: <code>{vista.repositorio_base}</code>
                    </p>
                    <p style={{ ...ESTILO_MOTIVO, marginBottom: 0 }}>
                      El nombre de un repositorio no cambia nunca después de crearse.
                    </p>
                  </>
                )}
              </div>
            )}

            <button type="submit" disabled={creando || assignmentId === null || (vista !== null && (!vista.slug_valido || vista.slug_ocupado))}>
              {creando ? "Creando…" : "Crear tarea"}
            </button>
          </form>
        )}
      </section>

      <p>
        {cursoId && <Link to={`/cursos/${cursoId}/personas`}>Ver personas</Link>} ·{" "}
        {cursoId && <Link to={`/cursos/${cursoId}/vinculacion`}>Volver al asistente de vinculación</Link>}
      </p>
    </main>
  );
}
