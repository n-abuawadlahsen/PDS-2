import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { crearCurso } from "../lib/api";
import { useSesion, EstadoCurso } from "../components/Layout";
import { Cabecera, Mensajes, Vacio } from "../components/ui";
import { useOperacion } from "../hooks/useConsulta";

export function Cursos() {
  const { cursos, recargar } = useSesion();
  const navegar = useNavigate();
  const [creando, setCreando] = useState(false);
  const [form, setForm] = useState({
    nombre: "",
    codigo: "",
    periodo: "",
    slug: "",
    zona_horaria: "America/Santiago",
  });
  const operacion = useOperacion();
  return (
    <>
      <Cabecera
        titulo="Mis cursos"
        descripcion="Organiza tus tareas de programación y conecta Canvas con GitHub."
        acciones={
          !creando && (
            <button className="primary" onClick={() => setCreando(true)}>
              Crear curso
            </button>
          )
        }
      />
      <Mensajes {...operacion} />
      {creando ? (
        <section className="panel">
          <h2>Crear curso</h2>
          <p>
            Primero identifica el curso. Después podrás conectar Canvas y la
            organización de GitHub.
          </p>
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              void operacion.ejecutar(async () => {
                const nuevo = await crearCurso(form);
                recargar();
                navegar(`/cursos/${nuevo.id}/vinculacion`);
              });
            }}
          >
            <label>
              Nombre del curso
              <input
                required
                maxLength={200}
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                autoFocus
                placeholder="Introducción a la programación"
              />
            </label>
            <div className="form-grid">
              <label>
                Código
                <input
                  required
                  maxLength={12}
                  value={form.codigo}
                  onChange={(e) => setForm({ ...form, codigo: e.target.value })}
                  placeholder="ICC1101"
                  aria-describedby="codigo-ayuda"
                />
                <span id="codigo-ayuda" className="help">
                  Hasta 12 caracteres.
                </span>
              </label>
              <label>
                Período
                <input
                  required
                  minLength={6}
                  maxLength={6}
                  value={form.periodo}
                  onChange={(e) =>
                    setForm({ ...form, periodo: e.target.value })
                  }
                  placeholder="2026-2"
                  aria-describedby="periodo-ayuda"
                />
                <span id="periodo-ayuda" className="help">
                  6 caracteres, por ejemplo 2026-2.
                </span>
              </label>
            </div>
            <label>
              Identificador corto
              <input
                required
                maxLength={24}
                value={form.slug}
                onChange={(e) => setForm({ ...form, slug: e.target.value })}
                placeholder="icc1101-2026-2"
                aria-describedby="slug-ayuda"
              />
              <span className="help" id="slug-ayuda">
                Identifica este curso en los nombres de repositorios. Debe ser
                único; máximo 24 caracteres.
              </span>
            </label>
            <label>
              Zona horaria
              <input
                required
                value={form.zona_horaria}
                onChange={(e) =>
                  setForm({ ...form, zona_horaria: e.target.value })
                }
                aria-describedby="zona-ayuda"
              />
              <span className="help" id="zona-ayuda">
                Las fechas se muestran en esta zona, por ejemplo
                America/Santiago.
              </span>
            </label>
            <div className="actions">
              <button className="primary" disabled={operacion.ocupado}>
                {operacion.ocupado ? "Creando curso…" : "Crear y configurar"}
              </button>
              <button
                type="button"
                disabled={operacion.ocupado}
                onClick={() => setCreando(false)}
              >
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : cursos.length === 0 ? (
        <Vacio>
          <h2>Todavía no tienes cursos</h2>
          <p>Crea un curso para comenzar la vinculación con Canvas y GitHub.</p>
          <button className="primary" onClick={() => setCreando(true)}>
            Crear mi primer curso
          </button>
        </Vacio>
      ) : (
        <div className="course-grid">
          {cursos.map((c) => (
            <article key={c.id} className="panel course-card">
              <div className="panel-header">
                <span className="eyebrow">
                  {c.codigo} · {c.periodo}
                </span>
                <EstadoCurso curso={c} />
              </div>
              <h2>
                <Link to={`/cursos/${c.id}`}>{c.nombre}</Link>
              </h2>
              <p className="muted">{c.zona_horaria}</p>
              <footer className="actions">
                <Link className="button" to={`/cursos/${c.id}`}>
                  Abrir curso
                </Link>
                <Link to={`/cursos/${c.id}/tareas`}>Ver tareas</Link>
              </footer>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
