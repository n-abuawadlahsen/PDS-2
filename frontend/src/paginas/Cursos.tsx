import { useState } from "react";
import {
  ArrowRight,
  BookOpen,
  ClipboardList,
  Plus,
  Search,
  Users,
  SlidersHorizontal,
} from "lucide-react";
import { Button } from "../components/primitives/button";
import { Input } from "../components/primitives/input";
import { Link, useNavigate } from "react-router-dom";
import { crearCurso } from "../lib/api";
import { useSesion, EstadoCurso } from "../components/Layout";
import { Cabecera, Mensajes, Vacio } from "../components/ui";
import { useOperacion } from "../hooks/useConsulta";

export function Cursos() {
  const { cursos, recargar, agregarCurso } = useSesion();
  const navegar = useNavigate();
  const [creando, setCreando] = useState(false);
  const [busqueda, setBusqueda] = useState("");
  const [estado, setEstado] = useState("");
  const visibles = cursos.filter(
    (curso) =>
      (!estado || curso.estado === estado) &&
      `${curso.nombre} ${curso.codigo} ${curso.periodo}`
        .toLocaleLowerCase("es")
        .includes(busqueda.toLocaleLowerCase("es")),
  );
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
            <Button onClick={() => setCreando(true)}>
              <Plus size={18} aria-hidden="true" />
              Crear curso
            </Button>
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
                try {
                  new Intl.DateTimeFormat("es-CL", {
                    timeZone: form.zona_horaria,
                  }).format();
                } catch {
                  throw new Error(
                    "La zona horaria no es válida. Usa, por ejemplo, America/Santiago.",
                  );
                }
                const nuevo = await crearCurso(
                  Object.fromEntries(
                    Object.entries(form).map(([campo, valor]) => [
                      campo,
                      valor.trim(),
                    ]),
                  ) as typeof form,
                );
                agregarCurso(nuevo);
                recargar();
                navegar(`/cursos/${nuevo.id}/vinculacion`);
              });
            }}
          >
            <label>
              Nombre del curso
              <Input
                required
                maxLength={200}
                aria-label="Nombre del curso"
                aria-invalid={Boolean(operacion.campos.nombre)}
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                autoFocus
                placeholder="Introducción a la programación"
              />
              {operacion.campos.nombre && (
                <span className="field-error" role="alert">
                  {operacion.campos.nombre}
                </span>
              )}
            </label>
            <div className="form-grid">
              <label>
                Código
                <Input
                  required
                  maxLength={12}
                  aria-label="Código"
                  aria-invalid={Boolean(operacion.campos.codigo)}
                  value={form.codigo}
                  onChange={(e) => setForm({ ...form, codigo: e.target.value })}
                  placeholder="ICC1101"
                  aria-describedby="codigo-ayuda"
                />
                {operacion.campos.codigo && (
                  <span className="field-error" role="alert">
                    {operacion.campos.codigo}
                  </span>
                )}
                <span id="codigo-ayuda" className="help">
                  Hasta 12 caracteres.
                </span>
              </label>
              <label>
                Período
                <Input
                  required
                  minLength={6}
                  maxLength={6}
                  aria-label="Período"
                  aria-invalid={Boolean(operacion.campos.periodo)}
                  value={form.periodo}
                  onChange={(e) =>
                    setForm({ ...form, periodo: e.target.value })
                  }
                  placeholder="2026-2"
                  aria-describedby="periodo-ayuda"
                />
                {operacion.campos.periodo && (
                  <span className="field-error" role="alert">
                    {operacion.campos.periodo}
                  </span>
                )}
                <span id="periodo-ayuda" className="help">
                  6 caracteres, por ejemplo 2026-2.
                </span>
              </label>
            </div>
            <label>
              Identificador corto
              <Input
                required
                maxLength={24}
                aria-label="Identificador corto"
                aria-invalid={Boolean(operacion.campos.slug)}
                value={form.slug}
                onChange={(e) => setForm({ ...form, slug: e.target.value })}
                placeholder="icc1101-2026-2"
                aria-describedby="slug-ayuda"
              />
              {operacion.campos.slug && (
                <span className="field-error" role="alert">
                  {operacion.campos.slug}
                </span>
              )}
              <span className="help" id="slug-ayuda">
                Identifica este curso en los nombres de repositorios. Debe ser
                único; máximo 24 caracteres.
              </span>
            </label>
            <label>
              Zona horaria
              <Input
                required
                aria-label="Zona horaria"
                aria-invalid={Boolean(operacion.campos.zona_horaria)}
                value={form.zona_horaria}
                onChange={(e) =>
                  setForm({ ...form, zona_horaria: e.target.value })
                }
                aria-describedby="zona-ayuda"
              />
              {operacion.campos.zona_horaria && (
                <span className="field-error" role="alert">
                  {operacion.campos.zona_horaria}
                </span>
              )}
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
        <div className="courses-workspace">
          <section aria-label="Tus cursos">
            <div className="course-toolbar">
              <label className="search-field">
                <span className="sr-only">Buscar cursos</span>
                <Search size={18} aria-hidden="true" />
                <Input
                  type="search"
                  placeholder="Buscar por nombre o código…"
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                />
              </label>
              <label className="course-state-filter">
                <span className="sr-only">Estado del curso</span>
                <select
                  value={estado}
                  onChange={(e) => setEstado(e.target.value)}
                >
                  <option value="">Todos los estados</option>
                  <option value="ACTIVO">Activos</option>
                  <option value="BORRADOR">Borradores</option>
                  <option value="VINCULANDO">En configuración</option>
                  <option value="ARCHIVADO">Archivados</option>
                  <option value="CANVAS_DESVINCULADO">
                    Canvas requiere atención
                  </option>
                  <option value="GITHUB_DESVINCULADO">
                    GitHub requiere atención
                  </option>
                </select>
              </label>
            </div>
            <p className="result-count" aria-live="polite">
              {visibles.length} de {cursos.length}{" "}
              {cursos.length === 1 ? "curso" : "cursos"}
            </p>
            {visibles.length === 0 ? (
              <Vacio>
                <h2>No hay cursos que coincidan</h2>
                <p>Prueba otro nombre o cambia el estado.</p>
                <button
                  onClick={() => {
                    setBusqueda("");
                    setEstado("");
                  }}
                >
                  Limpiar filtros
                </button>
              </Vacio>
            ) : (
              <div className="course-grid">
                {visibles.map((c) => (
                  <article
                    key={c.id}
                    className={`panel course-card course-color-${(Array.from(c.id).reduce((total, letra) => total + letra.charCodeAt(0), 0) % 6) + 1}`}
                  >
                    <Link
                      className="course-cover"
                      to={`/cursos/${c.id}`}
                      aria-label={`Abrir ${c.nombre}`}
                    >
                      <BookOpen
                        size={32}
                        strokeWidth={1.4}
                        aria-hidden="true"
                      />
                      <span>{c.codigo}</span>
                      <span className="course-cover-period">{c.periodo}</span>
                    </Link>
                    <div className="course-card-body">
                      <EstadoCurso curso={c} />
                      <h2>
                        <Link to={`/cursos/${c.id}`}>{c.nombre}</Link>
                      </h2>
                      <p className="muted">
                        {c.codigo} · Período {c.periodo}
                      </p>
                      <footer className="course-card-actions">
                        <Link to={`/cursos/${c.id}/tareas`}>
                          <ClipboardList size={17} aria-hidden="true" />
                          Tareas
                        </Link>
                        <Link to={`/cursos/${c.id}/personas`}>
                          <Users size={17} aria-hidden="true" />
                          Personas
                        </Link>
                        <Link
                          className="course-open"
                          to={`/cursos/${c.id}`}
                          aria-label={`Abrir curso ${c.nombre}`}
                        >
                          <ArrowRight size={19} aria-hidden="true" />
                        </Link>
                      </footer>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
          <aside className="courses-aside" aria-label="Guía de trabajo">
            <h2>Tu espacio docente</h2>
            <p className="muted">Canvas y GitHub, en un mismo lugar.</p>
            <ol className="workflow-guide">
              <li>
                <span>1</span>
                <div>
                  <strong>Conecta tu curso</strong>
                  <p>Vincula Canvas y la organización de GitHub.</p>
                </div>
              </li>
              <li>
                <span>2</span>
                <div>
                  <strong>Prepara las tareas</strong>
                  <p>
                    Define las entregas y activa la creación de repositorios.
                  </p>
                </div>
              </li>
              <li>
                <span>3</span>
                <div>
                  <strong>Acompaña y corrige</strong>
                  <p>
                    Revisa la actividad y publica las calificaciones en Canvas.
                  </p>
                </div>
              </li>
            </ol>
            <div className="aside-account">
              <SlidersHorizontal size={19} aria-hidden="true" />
              <div>
                <Link to="/perfil">Configurar mi cuenta</Link>
                <p className="help">Perfil, sesiones y notificaciones.</p>
              </div>
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
