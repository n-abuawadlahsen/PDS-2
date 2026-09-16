import { useState } from "react";
import { Link } from "react-router-dom";
import {
  adoptarInstalacionHuerfana,
  iniciarInstalacionGithub,
  listarCursosCanvasDisponibles,
  listarInstalacionesHuerfanas,
  listarInstanciasCanvas,
  obtenerEstadoVinculacionCanvas,
  obtenerEstadoVinculacionGithub,
  vincularCanvas,
  type CursoCanvasDisponible,
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
  Vacio,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import { fechaLegible } from "../lib/textosTarea";
export function Vinculacion() {
  const { curso, puede, recargar } = useCurso();
  const administra = puede("curso.administrar");
  const [instancia, setInstancia] = useState("");
  const [token, setToken] = useState("");
  const [titular, setTitular] = useState(false);
  const [escritura, setEscritura] = useState(false);
  const [cursos, setCursos] = useState<CursoCanvasDisponible[] | null>(null);
  const op = useOperacion();
  const githubOp = useOperacion();
  const confirmar = useConfirmar();
  const canvas = useConsulta(`canvas-${curso.id}`, (signal) =>
    obtenerEstadoVinculacionCanvas(curso.id, signal),
  );
  const github = useConsulta(`github-${curso.id}`, (signal) =>
    obtenerEstadoVinculacionGithub(curso.id, signal),
  );
  const instancias = useConsulta("instancias", listarInstanciasCanvas);
  const huerfanas = useConsulta(
    `huerfanas-${curso.id}-${administra}`,
    (signal) =>
      administra
        ? listarInstalacionesHuerfanas(curso.id, signal)
        : Promise.resolve([]),
  );
  const elegida = instancia || instancias.datos?.[0]?.base_url || "";
  return (
    <>
      <Cabecera
        titulo="Configuración del curso"
        descripcion="Conecta el curso académico de Canvas y la organización de GitHub donde se crearán los repositorios."
      />
      <nav className="tabs" aria-label="Configuración">
        <Link aria-current="page" to={`/cursos/${curso.id}/vinculacion`}>
          Conexiones
        </Link>
        <Link to={`/cursos/${curso.id}/verificacion`}>Verificación</Link>
      </nav>
      {!administra && (
        <Aviso>
          Solo un profesor puede modificar las conexiones. Puedes consultar sus
          estados.
        </Aviso>
      )}
      <div className="stack">
        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">01 · Información académica</p>
              <h2>Canvas</h2>
            </div>
            {canvas.datos && (
              <Estado
                valor={
                  canvas.datos.some((c) => c.estado === "VALIDA")
                    ? "VALIDA"
                    : "NO_VERIFICADO"
                }
                texto={
                  canvas.datos.some((c) => c.estado === "VALIDA")
                    ? "Credencial válida"
                    : "Sin credencial válida"
                }
              />
            )}
          </div>
          {canvas.error && (
            <ErrorCarga error={canvas.error} reintentar={canvas.recargar} />
          )}
          {!canvas.datos && !canvas.error && <Cargando />}
          {canvas.datos && canvas.datos.length > 0 && (
            <ul className="list-clean">
              {canvas.datos.map((c) => (
                <li key={c.titular_usuario_id}>
                  <strong>
                    {c.orden_respaldo === 0
                      ? "Credencial principal"
                      : `Credencial de respaldo ${c.orden_respaldo}`}
                  </strong>{" "}
                  · <Estado valor={c.estado} />
                  <p className="help">
                    Huella: {c.huella} · Última comprobación:{" "}
                    {c.ultimo_chequeo_en
                      ? fechaLegible(c.ultimo_chequeo_en, curso.zona_horaria)
                      : "sin verificar"}
                  </p>
                  <details>
                    <summary>Titular de la credencial</summary>
                    <code>{c.titular_usuario_id}</code>
                  </details>
                </li>
              ))}
            </ul>
          )}
          {administra && (
            <>
              <h3>Añadir mi credencial</h3>
              <p>
                Usa tu propio token personal. La aplicación verificará que seas
                profesor del curso seleccionado.
              </p>
              <details>
                <summary>Cómo obtener mi token en Canvas</summary>
                <p>
                  En tu instancia de Canvas, abre Cuenta → Configuraciones. En
                  la sección de integraciones aprobadas, genera un token de
                  acceso personal y cópialo aquí. Si esa opción no está
                  disponible, consulta al administrador de tu instancia.
                </p>
                <p className="help">
                  El token se usa para conectar tu cuenta; no se guarda en este
                  navegador.
                </p>
              </details>
              <Mensajes {...op} />
              {instancias.error && (
                <ErrorCarga
                  error={instancias.error}
                  reintentar={instancias.recargar}
                />
              )}
              <form
                className="form-stack"
                onSubmit={(e) => {
                  e.preventDefault();
                  void op.ejecutar(async () => {
                    const r = await listarCursosCanvasDisponibles(curso.id, {
                      token,
                      canvas_base_url: elegida,
                    });
                    if (!r.ok)
                      throw new Error(
                        r.error ?? "No pudimos consultar tus cursos de Canvas.",
                      );
                    setCursos(r.cursos);
                  });
                }}
              >
                <label>
                  Instancia de Canvas
                  <select
                    value={elegida}
                    onChange={(e) => {
                      setInstancia(e.target.value);
                      setCursos(null);
                    }}
                    disabled={op.ocupado}
                    required
                  >
                    {!instancias.datos?.length && (
                      <option value="">Sin instancias disponibles</option>
                    )}
                    {instancias.datos?.map((i) => (
                      <option key={i.base_url} value={i.base_url}>
                        {i.nombre_visible}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Mi token de acceso personal
                  <input
                    required
                    type="password"
                    autoComplete="off"
                    value={token}
                    disabled={op.ocupado}
                    onChange={(e) => {
                      setToken(e.target.value);
                      setCursos(null);
                    }}
                  />
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={titular}
                    onChange={(e) => setTitular(e.target.checked)}
                  />
                  Pego mi propio token; no pego el de otra persona.
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={escritura}
                    onChange={(e) => setEscritura(e.target.checked)}
                  />
                  Con esta credencial la aplicación publicará notas, anuncios,
                  mensajes y comentarios a mi nombre en Canvas, incluidos los
                  originados por otros miembros del equipo docente.
                </label>
                <div>
                  <button
                    className="primary"
                    disabled={
                      op.ocupado || !titular || !escritura || !token || !elegida
                    }
                  >
                    {op.ocupado ? "Consultando Canvas…" : "Buscar mis cursos"}
                  </button>
                </div>
              </form>
              {cursos && (
                <section>
                  <h3>Cursos de Canvas disponibles</h3>
                  {!cursos.length ? (
                    <Vacio>
                      No encontramos cursos activos donde figures como profesor
                      en esta instancia.
                    </Vacio>
                  ) : (
                    <ul className="list-clean">
                      {cursos.map((c) => (
                        <li key={c.canvas_course_id}>
                          <div className="panel-header">
                            <div>
                              <strong>{c.nombre}</strong>
                              <p className="help">
                                {c.codigo} ·{" "}
                                {c.termino ?? "Período no informado"}
                                {c.total_estudiantes !== null &&
                                  ` · ${c.total_estudiantes} estudiantes`}
                              </p>
                            </div>
                            <button
                              disabled={
                                op.ocupado ||
                                Boolean(c.ya_vinculado_a) ||
                                !titular ||
                                !escritura
                              }
                              onClick={() =>
                                void op.ejecutar(async () => {
                                  await comprobar(
                                    await vincularCanvas(curso.id, {
                                      token,
                                      canvas_base_url: elegida,
                                      canvas_course_id: c.canvas_course_id,
                                    }),
                                  );
                                  setToken("");
                                  setCursos(null);
                                  canvas.recargar();
                                  recargar();
                                }, "Canvas está vinculado. Conecta GitHub y luego verifica las conexiones.")
                              }
                            >
                              Elegir este curso
                            </button>
                          </div>
                          {c.ya_vinculado_a && (
                            <p className="help">
                              Ya vinculado a {c.ya_vinculado_a}.
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              )}
            </>
          )}
        </section>
        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">02 · Repositorios</p>
              <h2>GitHub</h2>
            </div>
            {github.datos && (
              <Estado
                valor={github.datos.org_login ? "CORRECTO" : "NO_VERIFICADO"}
                texto={
                  github.datos.org_login
                    ? "Organización vinculada"
                    : "Sin organización"
                }
              />
            )}
          </div>
          {github.error && (
            <ErrorCarga error={github.error} reintentar={github.recargar} />
          )}
          {!github.datos && !github.error && <Cargando />}
          {github.datos?.org_login ? (
            <>
              <p>
                Organización: <strong>{github.datos.org_login}</strong>
              </p>
              <p className="help">
                Equipo docente:{" "}
                {github.datos.equipo_docentes_slug ?? "No informado"}
              </p>
            </>
          ) : (
            <p>
              Instala la aplicación en la organización de GitHub del curso, no
              en una cuenta personal. El retorno identifica el curso
              automáticamente.
            </p>
          )}
          <Mensajes {...githubOp} />
          {administra && (
            <div className="actions">
              <button
                className={github.datos?.org_login ? "" : "primary"}
                disabled={githubOp.ocupado}
                onClick={() =>
                  void githubOp.ejecutar(async () => {
                    const r = await iniciarInstalacionGithub(curso.id);
                    window.location.assign(r.instalar_url);
                  })
                }
              >
                {githubOp.ocupado
                  ? "Abriendo GitHub…"
                  : github.datos?.org_login
                    ? "Revisar instalación en GitHub"
                    : "Instalar en mi organización"}
              </button>
              <Link to="/perfil">Revisar mi cuenta de GitHub docente</Link>
            </div>
          )}
          {huerfanas.error && (
            <ErrorCarga
              error={huerfanas.error}
              reintentar={huerfanas.recargar}
            />
          )}
          {administra && Boolean(huerfanas.datos?.length) && (
            <details>
              <summary>Instalaciones sin curso</summary>
              <ul className="list-clean">
                {huerfanas.datos?.map((h) => (
                  <li key={h.installation_id}>
                    <strong>{h.org_login}</strong>
                    <p className="help">
                      Registrada el{" "}
                      {fechaLegible(h.actualizada_en, curso.zona_horaria)}
                    </p>
                    <button
                      disabled={githubOp.ocupado}
                      onClick={async () => {
                        if (
                          await confirmar({
                            titulo: "Vincular una instalación existente",
                            descripcion: `La organización ${h.org_login} quedará vinculada a ${curso.nombre}.`,
                            escribir: h.org_login,
                            accion: "Vincular al curso",
                          })
                        )
                          void githubOp.ejecutar(async () => {
                            await comprobar(
                              await adoptarInstalacionHuerfana(curso.id, {
                                installation_id: h.installation_id,
                                org_login_confirmado: h.org_login,
                              }),
                            );
                            github.recargar();
                            huerfanas.recargar();
                            recargar();
                          }, "Organización vinculada. Revisa las conexiones.");
                      }}
                    >
                      Vincular a este curso
                    </button>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </section>
        <section className="panel next-step">
          <h2>Comprueba las conexiones</h2>
          <p>
            La verificación muestra los permisos disponibles y cualquier
            configuración que requiera atención.
          </p>
          <Link
            className="button primary"
            to={`/cursos/${curso.id}/verificacion`}
          >
            Ir a verificación
          </Link>
        </section>
      </div>
    </>
  );
}
