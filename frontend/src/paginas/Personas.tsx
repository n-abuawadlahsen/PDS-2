import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  crearRegistroGithub,
  declararMapeoManual,
  importarMapeoCsv,
  obtenerCabeceraPersonas,
  obtenerPersonas,
  restaurarRegistroGithub,
  sincronizarAhora,
  type CabeceraPersonas,
  type FilaCsvMapeo,
  type Personas as PersonasDatos,
} from "../lib/api";

function formatoAntiguedad(iso: string | null): string {
  if (!iso) return "nunca sincronizado";
  const fecha = new Date(iso);
  return `sincronizado el ${fecha.toLocaleString()}`;
}

/** Campo de edicion manual del mapeo GitHub de un estudiante (Via 2, S7.4.3). */
function EditorMapeo({
  cursoId,
  estudianteId,
  onGuardado,
}: {
  cursoId: string;
  estudianteId: string;
  onGuardado: () => void;
}) {
  const [login, setLogin] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onGuardar() {
    if (!login.trim()) return;
    setEnviando(true);
    setError(null);
    const { ok, cuerpo } = await declararMapeoManual(cursoId, estudianteId, login.trim());
    if (ok) {
      setLogin("");
      onGuardado();
    } else if ("detail" in cuerpo) {
      setError(`${cuerpo.detail.motivo}: ${cuerpo.detail.detalle}`);
    }
    setEnviando(false);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem" }}>
      <div style={{ display: "flex", gap: "0.25rem" }}>
        <input
          value={login}
          onChange={(e) => setLogin(e.target.value)}
          placeholder="usuario de GitHub"
          style={{ width: "10rem" }}
        />
        <button onClick={onGuardar} disabled={enviando || !login.trim()}>
          {enviando ? "…" : "Guardar"}
        </button>
      </div>
      {error && <span style={{ color: "#b00020", fontSize: "0.75rem" }}>{error}</span>}
    </div>
  );
}

/** `/cursos/{id}/personas` (SPEC 07 S7.2, S7.8.2): estudiantes, secciones y
 * grupos, siempre leidos del espejo (Ley 1) -- nunca de Canvas en vivo. */
export function Personas() {
  const { cursoId } = useParams<{ cursoId: string }>();
  const [datos, setDatos] = useState<PersonasDatos | null>(null);
  const [cabecera, setCabecera] = useState<CabeceraPersonas | null>(null);
  const [sincronizando, setSincronizando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [csvTexto, setCsvTexto] = useState("");
  const [previewCsv, setPreviewCsv] = useState<FilaCsvMapeo[] | null>(null);

  async function cargar() {
    if (!cursoId) return;
    setDatos(await obtenerPersonas(cursoId));
    setCabecera(await obtenerCabeceraPersonas(cursoId));
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId]);

  async function onSincronizarAhora() {
    if (!cursoId) return;
    setSincronizando(true);
    setMensaje(null);
    const respuesta = await sincronizarAhora(cursoId);
    if (respuesta.ok) {
      setMensaje("Sincronización encolada. Los datos se actualizan en unos minutos.");
    } else {
      setMensaje(`No se pudo encolar la sincronización (${respuesta.status}).`);
    }
    setSincronizando(false);
  }

  async function onCrearRegistro() {
    if (!cursoId) return;
    const respuesta = await crearRegistroGithub(cursoId);
    setMensaje(
      respuesta.ok
        ? "Tarea de registro de GitHub creada/activa en Canvas."
        : `No se pudo crear la tarea (${respuesta.status}).`,
    );
    await cargar();
  }

  async function onRestaurarRegistro() {
    if (!cursoId) return;
    const respuesta = await restaurarRegistroGithub(cursoId);
    setMensaje(respuesta.ok ? "Tarea de registro restaurada." : `No se pudo restaurar (${respuesta.status}).`);
    await cargar();
  }

  async function onPreviewCsv() {
    if (!cursoId || !csvTexto.trim()) return;
    const resultado = await importarMapeoCsv(cursoId, csvTexto, false);
    setPreviewCsv(resultado.filas);
  }

  async function onAplicarCsv() {
    if (!cursoId || !csvTexto.trim()) return;
    const resultado = await importarMapeoCsv(cursoId, csvTexto, true);
    setPreviewCsv(resultado.filas);
    await cargar();
  }

  if (!datos) {
    return (
      <main style={{ maxWidth: 900, margin: "4rem auto", fontFamily: "sans-serif" }}>
        <p>Cargando…</p>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 1000, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Personas</h1>
      {cabecera && (
        <p>
          <strong>
            {cabecera.con_cuenta_verificada} de {cabecera.total}
          </strong>{" "}
          estudiantes con cuenta verificada
        </p>
      )}
      <p style={{ fontSize: "0.85rem", color: "#666" }}>
        {formatoAntiguedad(datos.roster_sincronizado_en)} (roster) —{" "}
        {formatoAntiguedad(datos.grupos_sincronizado_en)} (grupos)
      </p>
      <p>
        <button onClick={onSincronizarAhora} disabled={sincronizando}>
          {sincronizando ? "Encolando…" : "Sincronizar ahora"}
        </button>{" "}
        <span style={{ fontSize: "0.85rem", color: "#666" }}>
          Registro de GitHub: <strong>{datos.registro_estado}</strong>
        </span>{" "}
        {datos.registro_estado === "NO_CREADA" && (
          <button onClick={onCrearRegistro}>Crear tarea de registro</button>
        )}
        {(datos.registro_estado === "ALTERADA" || datos.registro_estado === "DESAPARECIDA") && (
          <button onClick={onRestaurarRegistro}>Restaurar tarea de registro</button>
        )}
      </p>
      {mensaje && <p role="status">{mensaje}</p>}

      <section>
        <h2>Estudiantes ({datos.estudiantes.length})</h2>
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Estado</th>
              <th>Correo</th>
              <th>Secciones</th>
              <th>Grupos</th>
              <th>Cuenta GitHub</th>
            </tr>
          </thead>
          <tbody>
            {datos.estudiantes.map((e) => (
              <tr key={e.id}>
                <td>{e.nombre}</td>
                <td>{e.estado}</td>
                <td>{e.email ?? "—"}</td>
                <td>{e.secciones.join(", ") || "—"}</td>
                <td>{e.grupos.join(", ") || "sin grupo"}</td>
                <td>
                  {e.mapeo.estado === "VIGENTE" ? (
                    <span>{e.mapeo.cuenta_login}</span>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                      <span style={{ fontSize: "0.8rem", color: "#666" }}>{e.mapeo.estado}</span>
                      {cursoId && (
                        <EditorMapeo cursoId={cursoId} estudianteId={e.id} onGuardado={cargar} />
                      )}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Importar mapeo por CSV</h2>
        <p style={{ fontSize: "0.85rem", color: "#666" }}>
          Columnas: <code>canvas_user_id</code> (o <code>login_id</code>) y <code>github_login</code>.
        </p>
        <textarea
          value={csvTexto}
          onChange={(e) => setCsvTexto(e.target.value)}
          rows={4}
          style={{ width: "100%", fontFamily: "monospace" }}
          placeholder={"canvas_user_id,github_login\n2001,estudiante-valido"}
        />
        <p>
          <button onClick={onPreviewCsv}>Previsualizar</button>{" "}
          <button onClick={onAplicarCsv}>Aplicar filas válidas</button>
        </p>
        {previewCsv && (
          <table>
            <thead>
              <tr>
                <th>Fila</th>
                <th>canvas_user_id</th>
                <th>github_login</th>
                <th>Resultado</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              {previewCsv.map((f) => (
                <tr key={f.fila}>
                  <td>{f.fila}</td>
                  <td>{f.canvas_user_id ?? f.login_id}</td>
                  <td>{f.github_login}</td>
                  <td>{f.resultado}</td>
                  <td>{f.detalle ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>Secciones ({datos.secciones.length})</h2>
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Estado</th>
              <th>Estudiantes</th>
            </tr>
          </thead>
          <tbody>
            {datos.secciones.map((s) => (
              <tr key={s.id}>
                <td>{s.nombre}</td>
                <td>{s.estado}</td>
                <td>{s.cantidad_estudiantes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Grupos ({datos.grupos.length})</h2>
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Conjunto</th>
              <th>Estado</th>
              <th>Integrantes</th>
            </tr>
          </thead>
          <tbody>
            {datos.grupos.map((g) => (
              <tr key={g.id}>
                <td>{g.nombre}</td>
                <td>{g.conjunto}</td>
                <td>{g.estado}</td>
                <td>{g.integrantes.join(", ") || "vacío"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <p>
        {cursoId && <Link to={`/cursos/${cursoId}/pendientes`}>Ver Pendientes</Link>}
        {" · "}
        {cursoId && <Link to={`/cursos/${cursoId}/tareas`}>Ver tareas</Link>}
        {" · "}
        {cursoId && <Link to={`/cursos/${cursoId}/vinculacion`}>Volver al asistente de vinculación</Link>}
      </p>
    </main>
  );
}
