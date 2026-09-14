import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  adoptarInstalacionHuerfana,
  iniciarInstalacionGithub,
  listarCursosCanvasDisponibles,
  listarInstalacionesHuerfanas,
  listarInstanciasCanvas,
  obtenerEstadoVinculacionCanvas,
  obtenerEstadoVinculacionGithub,
  vincularCanvas,
  type CredencialCanvasEstado,
  type CursoCanvasDisponible,
  type EstadoVinculacionGithub,
  type InstalacionHuerfana,
  type InstanciaCanvas,
} from "../lib/api";

/** Paso 2 del asistente de vinculacion: Canvas (SPEC 04 S4.4-S4.5). */
export function Vinculacion() {
  const { cursoId } = useParams<{ cursoId: string }>();
  const [instancias, setInstancias] = useState<InstanciaCanvas[]>([]);
  const [instanciaElegida, setInstanciaElegida] = useState("");
  const [token, setToken] = useState("");
  const [consentimientoTitular, setConsentimientoTitular] = useState(false);
  const [consentimientoEscritura, setConsentimientoEscritura] = useState(false);
  const [cursos, setCursos] = useState<CursoCanvasDisponible[] | null>(null);
  const [credenciales, setCredenciales] = useState<CredencialCanvasEstado[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  const [estadoGithub, setEstadoGithub] = useState<EstadoVinculacionGithub | null>(null);
  const [huerfanas, setHuerfanas] = useState<InstalacionHuerfana[]>([]);
  const [erroGithub, setErrorGithub] = useState<string | null>(null);

  function cargarEstadoGithub() {
    if (!cursoId) return;
    obtenerEstadoVinculacionGithub(cursoId).then(setEstadoGithub);
    listarInstalacionesHuerfanas(cursoId).then(setHuerfanas);
  }

  useEffect(() => {
    listarInstanciasCanvas().then((lista) => {
      setInstancias(lista);
      if (lista.length > 0) setInstanciaElegida(lista[0].base_url);
    });
    if (cursoId) obtenerEstadoVinculacionCanvas(cursoId).then(setCredenciales);
    cargarEstadoGithub();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId]);

  async function instalarGithub() {
    if (!cursoId) return;
    setErrorGithub(null);
    const { instalar_url } = await iniciarInstalacionGithub(cursoId);
    window.open(instalar_url, "_blank", "noopener,noreferrer");
  }

  async function adoptarHuerfana(instalacion: InstalacionHuerfana) {
    if (!cursoId) return;
    const confirmado = window.prompt(
      `Para confirmar, escribí el nombre de la organización: ${instalacion.org_login}`,
    );
    if (confirmado !== instalacion.org_login) return;
    const respuesta = await adoptarInstalacionHuerfana(cursoId, {
      installation_id: instalacion.installation_id,
      org_login_confirmado: confirmado,
    });
    if (respuesta.ok) {
      cargarEstadoGithub();
    } else {
      const cuerpo = await respuesta.json().catch(() => ({}));
      setErrorGithub(typeof cuerpo.detail === "string" ? cuerpo.detail : JSON.stringify(cuerpo.detail));
    }
  }

  async function buscarCursos(evento: React.FormEvent) {
    evento.preventDefault();
    if (!cursoId) return;
    setError(null);
    setCursos(null);
    const resultado = await listarCursosCanvasDisponibles(cursoId, {
      token,
      canvas_base_url: instanciaElegida,
    });
    if (!resultado.ok) {
      setError(resultado.error ?? "No se pudo listar cursos");
      return;
    }
    setCursos(resultado.cursos);
    if (resultado.cursos.length === 0) {
      setError("Tu cuenta de Canvas no figura como profesora de ningún curso activo en esa instancia.");
    }
  }

  async function elegirCurso(canvasCourseId: number) {
    if (!cursoId) return;
    setError(null);
    const respuesta = await vincularCanvas(cursoId, {
      token,
      canvas_base_url: instanciaElegida,
      canvas_course_id: canvasCourseId,
    });
    if (respuesta.ok) {
      setMensaje("Canvas vinculado correctamente.");
      setCredenciales(await obtenerEstadoVinculacionCanvas(cursoId));
      setCursos(null);
      setToken("");
    } else {
      const cuerpo = await respuesta.json().catch(() => ({}));
      const detalle = cuerpo.detail;
      if (detalle && typeof detalle === "object" && detalle.motivo === "CURSO_YA_VINCULADO") {
        setError(`Ese curso ya está vinculado a "${detalle.curso_ocupante}".`);
      } else if (detalle === "SIN_MATRICULA_PROFESOR") {
        setError("Este token pertenece a alguien que no es profesor de ese curso.");
      } else if (detalle === "LIMITADO_A_SECCION") {
        setError(
          "Tu matrícula de profesor está limitada a una sección. Pide una matrícula sin esa limitación, o usá la credencial de otro profesor.",
        );
      } else {
        setError(typeof detalle === "string" ? detalle : JSON.stringify(detalle));
      }
    }
  }

  const yaHayCredencial = credenciales.length > 0;

  return (
    <main style={{ maxWidth: 640, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Vinculación con Canvas</h1>
      {mensaje && <p role="status">{mensaje}</p>}

      {yaHayCredencial && (
        <section>
          <h2>Credenciales de este curso</h2>
          <ul>
            {credenciales.map((c) => (
              <li key={c.titular_usuario_id}>
                {c.orden_respaldo === 0 ? "Operativa" : `Respaldo (orden ${c.orden_respaldo})`} — {c.estado}{" "}
                (huella {c.huella})
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h2>Añadir mi credencial</h2>
        <form onSubmit={buscarCursos} style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxWidth: 420 }}>
          <label>
            Instancia de Canvas
            <select value={instanciaElegida} onChange={(e) => setInstanciaElegida(e.target.value)}>
              {instancias.map((i) => (
                <option key={i.base_url} value={i.base_url}>
                  {i.nombre_visible}
                </option>
              ))}
            </select>
          </label>
          <label>
            Mi token de acceso personal de Canvas
            <input required type="password" value={token} onChange={(e) => setToken(e.target.value)} />
          </label>
          <label>
            <input
              type="checkbox"
              checked={consentimientoTitular}
              onChange={(e) => setConsentimientoTitular(e.target.checked)}
            />{" "}
            Pego mi propio token; no pego el de otra persona.
          </label>
          <label>
            <input
              type="checkbox"
              checked={consentimientoEscritura}
              onChange={(e) => setConsentimientoEscritura(e.target.checked)}
            />{" "}
            Con esta credencial la aplicación publicará notas, anuncios, mensajes y comentarios a mi
            nombre en Canvas, incluidos los originados por otros miembros del equipo docente.
          </label>
          <button type="submit" disabled={!consentimientoTitular || !consentimientoEscritura || !token}>
            Buscar mis cursos
          </button>
        </form>

        {error && <p role="alert">{error}</p>}

        {cursos && cursos.length > 0 && (
          <ul>
            {cursos.map((c) => (
              <li key={c.canvas_course_id}>
                <strong>{c.nombre}</strong> ({c.codigo}) — {c.termino ?? "sin término"} —{" "}
                {c.total_estudiantes ?? "?"} estudiantes —{" "}
                <code>{c.canvas_course_id}</code>{" "}
                {c.ya_vinculado_a ? (
                  <span> ya vinculado a "{c.ya_vinculado_a}"</span>
                ) : (
                  <button onClick={() => elegirCurso(c.canvas_course_id)}>Elegir este curso</button>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Paso 3: vinculación con GitHub</h2>
        {estadoGithub?.org_login ? (
          <p>
            Organización vinculada: <strong>{estadoGithub.org_login}</strong>
            {estadoGithub.equipo_docentes_slug && (
              <> — equipo docente: <code>{estadoGithub.equipo_docentes_slug}</code></>
            )}
          </p>
        ) : (
          <>
            <p>
              Vas a instalar la aplicación en tu organización de GitHub. Elegí la organización del
              curso, no tu cuenta personal. No tenés que copiar ningún identificador: al volver, la
              aplicación resuelve el curso sola.
            </p>
            <button onClick={instalarGithub}>Instalar en mi organización de GitHub</button>
          </>
        )}
        {erroGithub && <p role="alert">{erroGithub}</p>}

        {huerfanas.length > 0 && (
          <div>
            <h3>Instalaciones sin curso</h3>
            <ul>
              {huerfanas.map((h) => (
                <li key={h.installation_id}>
                  {h.org_login} (instalada el {new Date(h.actualizada_en).toLocaleString()}){" "}
                  <button onClick={() => adoptarHuerfana(h)}>Adoptar para este curso</button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <p>
        {cursoId && <Link to={`/cursos/${cursoId}/verificacion`}>Paso 4: checklist de verificación</Link>}
      </p>
      <p>{cursoId && <Link to={`/cursos/${cursoId}/personas`}>Ver personas (estudiantes, secciones y grupos)</Link>}</p>
      <p>{cursoId && <Link to={`/cursos/${cursoId}/tareas`}>Ver tareas y crear una nueva</Link>}</p>
      <p>
        <Link to="/cursos">Volver a mis cursos</Link>
      </p>
    </main>
  );
}
