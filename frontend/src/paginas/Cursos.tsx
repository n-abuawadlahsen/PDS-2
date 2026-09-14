import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { crearCurso, listarCursos, obtenerPerfil, type Curso, type Perfil } from "../lib/api";

export function Cursos() {
  const [perfil, setPerfil] = useState<Perfil | null | "cargando">("cargando");
  const [cursos, setCursos] = useState<Curso[]>([]);
  const [creando, setCreando] = useState(false);
  const [form, setForm] = useState({ nombre: "", codigo: "", periodo: "", slug: "", zona_horaria: "America/Santiago" });
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    const datos = await obtenerPerfil();
    setPerfil(datos);
    if (datos) setCursos(await listarCursos());
  }

  useEffect(() => {
    cargar();
  }, []);

  async function onCrear(evento: React.FormEvent) {
    evento.preventDefault();
    setError(null);
    try {
      await crearCurso(form);
      setCreando(false);
      setForm({ nombre: "", codigo: "", periodo: "", slug: "", zona_horaria: "America/Santiago" });
      await cargar();
    } catch {
      setError("No se pudo crear el curso. Revisá que el slug no esté en uso y que el código tenga hasta 12 caracteres.");
    }
  }

  if (perfil === "cargando") return <p>Cargando...</p>;
  if (perfil === null)
    return (
      <p>
        Sin sesión. Andá a <Link to="/acceso">/acceso</Link>.
      </p>
    );

  return (
    <main style={{ maxWidth: 640, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Mis cursos</h1>

      <ul>
        {cursos.map((c) => (
          <li key={c.id}>
            <Link to={`/cursos/${c.id}/equipo`}>{c.nombre}</Link> — {c.codigo} {c.periodo} ({c.estado}) —{" "}
            <Link to={`/cursos/${c.id}/vinculacion`}>vinculación</Link> —{" "}
            <Link to={`/cursos/${c.id}/tareas`}>tareas</Link>
          </li>
        ))}
        {cursos.length === 0 && <li>Todavía no tenés cursos.</li>}
      </ul>

      {!creando && <button onClick={() => setCreando(true)}>Crear curso</button>}

      {creando && (
        <form onSubmit={onCrear} style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxWidth: 320 }}>
          <label>
            Nombre
            <input required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
          </label>
          <label>
            Código (máx. 12)
            <input
              required
              maxLength={12}
              value={form.codigo}
              onChange={(e) => setForm({ ...form, codigo: e.target.value })}
            />
          </label>
          <label>
            Periodo (6 caracteres, ej. 2026-2)
            <input
              required
              minLength={6}
              maxLength={6}
              value={form.periodo}
              onChange={(e) => setForm({ ...form, periodo: e.target.value })}
            />
          </label>
          <label>
            Slug (máx. 24, único)
            <input
              required
              maxLength={24}
              value={form.slug}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
            />
          </label>
          <label>
            Zona horaria
            <input
              required
              value={form.zona_horaria}
              onChange={(e) => setForm({ ...form, zona_horaria: e.target.value })}
            />
          </label>
          {error && <p role="alert">{error}</p>}
          <div>
            <button type="submit">Guardar</button>{" "}
            <button type="button" onClick={() => setCreando(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      <p>
        <Link to="/perfil">Mi perfil</Link>
      </p>
    </main>
  );
}
