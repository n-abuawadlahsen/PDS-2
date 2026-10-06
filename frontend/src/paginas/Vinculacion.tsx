import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  apiFetch,
  adoptarInstalacionHuerfana,
  iniciarInstalacionGithub,
  listarCursosCanvasDisponibles,
  listarInstalacionesHuerfanas,
  listarInstanciasCanvas,
  obtenerEstadoVinculacionCanvas,
  obtenerEstadoVinculacionGithub,
  vincularCanvas,
  urlApi,
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
import { EstadoTrabajo } from "../components/EstadoTrabajo";
function AjustesGenerales() {
  const { curso, recargar } = useCurso();
  const [nombre, setNombre] = useState(curso.nombre);
  const [roles, setRoles] = useState(
    (curso.roles_estudiante_extra ?? []).join(", "),
  );
  const [zona, setZona] = useState(curso.zona_horaria);
  const [inactividad, setInactividad] = useState(
    curso.umbral_dias_sin_actividad ?? 7,
  );
  const [desbalance, setDesbalance] = useState(
    curso.umbral_desbalance_pct ?? 70,
  );
  const op = useOperacion();
  useEffect(() => {
    setNombre(curso.nombre);
    setRoles((curso.roles_estudiante_extra ?? []).join(", "));
    setZona(curso.zona_horaria);
    setInactividad(curso.umbral_dias_sin_actividad ?? 7);
    setDesbalance(curso.umbral_desbalance_pct ?? 70);
  }, [curso]);
  return (
    <form
      className="form-stack"
      onSubmit={(e) => {
        e.preventDefault();
        void op.ejecutar(async () => {
          await comprobar(
            await apiFetch(`/api/cursos/${curso.id}`, {
              method: "PATCH",
              body: JSON.stringify({
                nombre,
                zona_horaria: zona,
                umbral_dias_sin_actividad: inactividad,
                umbral_desbalance_pct: desbalance,
                roles_estudiante_extra: roles.trim()
                  ? roles.split(",").map((r) => Number(r.trim()))
                  : [],
              }),
            }),
          );
          recargar();
        }, "Ajustes guardados. Las métricas se recalcularán con los nuevos valores.");
      }}
    >
      <Mensajes {...op} />
      <label>
        Nombre del curso
        <input
          required
          maxLength={200}
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          aria-invalid={Boolean(op.campos.nombre)}
        />
        {op.campos.nombre && (
          <span className="field-error">{op.campos.nombre}</span>
        )}
      </label>
      <label>
        Zona horaria
        <input
          required
          value={zona}
          onChange={(e) => setZona(e.target.value)}
          aria-invalid={Boolean(op.campos.zona_horaria)}
        />
        {op.campos.zona_horaria && (
          <span className="field-error">{op.campos.zona_horaria}</span>
        )}
        <span className="help">
          Zona IANA, por ejemplo America/Santiago. Los instantes y versiones
          registrados se conservan.
        </span>
      </label>
      <div className="form-grid">
        <label>
          Días sin actividad
          <input
            type="number"
            required
            min={1}
            max={30}
            value={inactividad}
            onChange={(e) => setInactividad(Number(e.target.value))}
          />
          {op.campos.umbral_dias_sin_actividad && (
            <span className="field-error">
              {op.campos.umbral_dias_sin_actividad}
            </span>
          )}
        </label>
        <label>
          Umbral de desbalance (%)
          <input
            type="number"
            required
            min={50}
            max={95}
            value={desbalance}
            onChange={(e) => setDesbalance(Number(e.target.value))}
          />
          {op.campos.umbral_desbalance_pct && (
            <span className="field-error">
              {op.campos.umbral_desbalance_pct}
            </span>
          )}
        </label>
      </div>
      <div>
        <label>
          Roles Canvas adicionales de estudiante
          <input
            value={roles}
            onChange={(e) => setRoles(e.target.value)}
            pattern="[0-9 ,]*"
            aria-invalid={Boolean(op.campos.roles_estudiante_extra)}
          />
          <span className="help">
            IDs de roles derivados de StudentEnrollment, separados por comas.
            Vacío conserva el padrón estándar. Guardar solicita una nueva
            sincronización.
          </span>
          {op.campos.roles_estudiante_extra && (
            <span className="field-error">
              {op.campos.roles_estudiante_extra}
            </span>
          )}
        </label>
      </div>
      <div>
        <button
          className="primary"
          disabled={op.ocupado || curso.estado === "ARCHIVADO"}
        >
          Guardar ajustes
        </button>
      </div>
    </form>
  );
}

interface VistaArchivo {
  repositorios: number;
  sin_capturar: number;
  capturas_pendientes?: {
    entrega_id: string;
    entrega: string;
    sujeto_id: string;
    cierre: string | null;
  }[];
  repositorios_por_archivar?: number;
  bloqueos?: { tarea_id: string; tarea: string; motivo: string }[];
  trabajos_archivado?: string[];
}
function ArchivoCurso() {
  const { curso, recargar } = useCurso();
  const op = useOperacion();
  const confirmar = useConfirmar();
  const archivado = curso.estado === "ARCHIVADO";
  const [archivarRepos, setArchivarRepos] = useState(true);
  const [vista, setVista] = useState<VistaArchivo | null>(null);
  const archivo = useConsulta(
    archivado ? `archivo:${curso.id}` : "",
    async (signal) => {
      if (!archivado) return null;
      const r = await apiFetch(
        `/api/cursos/${curso.id}/archivo/previsualizar`,
        { signal },
      );
      await comprobar(r);
      return r.json() as Promise<VistaArchivo>;
    },
  );
  return (
    <section className="panel">
      <h2>{archivado ? "Reactivar el curso" : "Archivar el curso"}</h2>
      <p>
        El archivo conserva tareas, repositorios, versiones y borradores. Pausa
        los procesos y las comunicaciones del curso. Puedes archivar también los
        repositorios en GitHub si cumplen las cinco guardas del cierre.
      </p>
      <Mensajes {...op} />
      {!archivado && (
        <label className="check">
          <input
            type="checkbox"
            checked={archivarRepos}
            onChange={(e) => setArchivarRepos(e.target.checked)}
          />
          Archivar también los repositorios en GitHub
        </label>
      )}
      {vista?.bloqueos?.map((b) => (
        <Aviso tipo="warning" key={b.tarea_id}>
          {b.tarea}: {b.motivo}{" "}
          <Link to={`/cursos/${curso.id}/tareas/${b.tarea_id}/entregas`}>
            Revisar cierre
          </Link>
        </Aviso>
      ))}
      {vista?.capturas_pendientes && vista.capturas_pendientes.length > 0 && (
        <details>
          <summary>
            Cierres sin versión capturada ({vista.sin_capturar})
          </summary>
          <ul>
            {vista.capturas_pendientes.map((c) => (
              <li key={`${c.entrega_id}:${c.sujeto_id}`}>
                {c.entrega} · sujeto {c.sujeto_id} ·{" "}
                {fechaLegible(c.cierre, curso.zona_horaria)}
              </li>
            ))}
          </ul>
        </details>
      )}
      {archivado && archivo.error && (
        <ErrorCarga error={archivo.error} reintentar={archivo.recargar} />
      )}
      {archivado &&
        archivo.datos?.trabajos_archivado?.map((id) => (
          <EstadoTrabajo
            key={id}
            ruta={`/api/cursos/${curso.id}/trabajos/${id}`}
            zona={curso.zona_horaria}
          />
        ))}
      <div className="actions">
        <a
          className="button"
          href={urlApi(`/api/cursos/${curso.id}/archivo/inventario.csv`)}
        >
          Descargar inventario CSV
        </a>
        <button
          disabled={op.ocupado}
          onClick={() => {
            void op.ejecutar(async () => {
              let descripcion =
                "Se restaurarán el estado, el modo de escritura y los procesos que estaban activos antes del archivo. Los archivos de repositorios pendientes se cancelarán; los ya archivados se reactivan desde el cierre de su tarea.";
              if (!archivado) {
                const r = await apiFetch(
                  `/api/cursos/${curso.id}/archivo/previsualizar`,
                );
                await comprobar(r);
                const vista = (await r.json()) as VistaArchivo;
                setVista(vista);
                if (archivarRepos && vista.bloqueos?.length)
                  throw new Error(
                    "Revisa los bloqueos del cierre o desmarca el archivo de repositorios para pausar solamente el curso.",
                  );
                const capturas = (vista.capturas_pendientes ?? [])
                  .map((c) => `${c.entrega} (sujeto ${c.sujeto_id})`)
                  .join("; ");
                descripcion = `${vista.repositorios} repositorios conservados; ${vista.sin_capturar} cierres todavía sin versión capturada.${capturas ? ` Pendientes: ${capturas}.` : ""} ${archivarRepos ? `Se solicitará el archivo de ${vista.repositorios_por_archivar ?? vista.repositorios} repositorios en GitHub, con las cinco guardas.` : "Los repositorios mantendrán su estado en GitHub."} Los procesos se detendrán y el curso quedará sólo en lectura. Desinstalar la GitHub App desde GitHub revoca todos sus accesos.`;
              }
              if (
                !(await confirmar({
                  titulo: archivado ? "Reactivar curso" : "Archivar curso",
                  descripcion,
                  accion: archivado ? "Reactivar" : "Archivar",
                  escribir: archivado ? undefined : curso.slug,
                  peligro: !archivado,
                }))
              )
                return;
              await comprobar(
                await apiFetch(
                  `/api/cursos/${curso.id}/${archivado ? "desarchivar" : "archivar"}`,
                  {
                    method: "POST",
                    body: JSON.stringify({
                      confirmar: true,
                      slug: curso.slug,
                      archivar_repositorios: !archivado && archivarRepos,
                    }),
                  },
                ),
              );
              recargar();
            });
          }}
        >
          {archivado ? "Reactivar curso" : "Revisar archivado"}
        </button>
      </div>
    </section>
  );
}
export function Vinculacion({ ajustes = false }: { ajustes?: boolean }) {
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
  if (curso.estado === "ARCHIVADO")
    return (
      <>
        <Cabecera titulo="Curso archivado" />
        <Aviso>
          La configuración está en lectura mientras el curso está archivado.
        </Aviso>
        {administra && <ArchivoCurso />}
      </>
    );
  return (
    <>
      <Cabecera
        titulo={ajustes ? "Ajustes del curso" : "Configuración del curso"}
        descripcion="Conecta el curso académico de Canvas y la organización de GitHub donde se crearán los repositorios."
      />
      <nav className="tabs" aria-label="Configuración">
        <Link
          aria-current={!ajustes ? "page" : undefined}
          to={`/cursos/${curso.id}/vinculacion`}
        >
          Conexiones
        </Link>
        <Link to={`/cursos/${curso.id}/verificacion`}>Verificación</Link>
        <Link
          aria-current={ajustes ? "page" : undefined}
          to={`/cursos/${curso.id}/ajustes`}
        >
          Ajustes
        </Link>
      </nav>
      {ajustes && (
        <section className="panel">
          <h2>Información del curso</h2>
          <dl className="facts">
            <div className="facts-ancha">
              <dt>Nombre</dt>
              <dd>{curso.nombre}</dd>
            </div>
            <div>
              <dt>Código</dt>
              <dd>{curso.codigo}</dd>
            </div>
            <div>
              <dt>Período</dt>
              <dd>{curso.periodo}</dd>
            </div>
            <div>
              <dt>Zona horaria</dt>
              <dd>{curso.zona_horaria}</dd>
            </div>
            <div>
              <dt>Estado</dt>
              <dd>
                <Estado valor={curso.estado} />
              </dd>
            </div>
          </dl>
          {["BORRADOR", "VINCULANDO"].includes(curso.estado) && (
            <Aviso>
              El curso se activa cuando Canvas y GitHub están conectados y la
              verificación no tiene errores bloqueantes.{" "}
              <Link to={`/cursos/${curso.id}/vinculacion`}>
                Ir a Conexiones
              </Link>
            </Aviso>
          )}
          {administra && <AjustesGenerales />}
        </section>
      )}
      {ajustes && administra && <ArchivoCurso />}
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
                    try {
                      const r = await listarCursosCanvasDisponibles(curso.id, {
                        token,
                        canvas_base_url: elegida,
                      });
                      if (!r.ok)
                        throw new Error(
                          r.error ??
                            "No pudimos consultar tus cursos de Canvas.",
                        );
                      setCursos(r.cursos);
                    } catch (error) {
                      setToken("");
                      setCursos(null);
                      throw error;
                    }
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
                                (Boolean(c.ya_vinculado_a) &&
                                  c.ya_vinculado_curso_id !== curso.id) ||
                                !titular ||
                                !escritura
                              }
                              onClick={() =>
                                void op.ejecutar(async () => {
                                  try {
                                    await comprobar(
                                      await vincularCanvas(curso.id, {
                                        token,
                                        canvas_base_url: elegida,
                                        canvas_course_id: c.canvas_course_id,
                                      }),
                                    );
                                  } finally {
                                    setToken("");
                                    setCursos(null);
                                  }
                                  canvas.recargar();
                                  recargar();
                                }, "Canvas está vinculado. Conecta GitHub y luego verifica las conexiones.")
                              }
                            >
                              {c.ya_vinculado_curso_id === curso.id
                                ? "Renovar mi credencial"
                                : "Elegir este curso"}
                            </button>
                          </div>
                          {c.ya_vinculado_a && (
                            <p className="help">
                              {c.ya_vinculado_curso_id === curso.id
                                ? "Este es el curso vinculado. Puedes renovar tu propia credencial."
                                : `Ya vinculado a ${c.ya_vinculado_a}.`}
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

export function Ajustes() {
  return <Vinculacion ajustes />;
}
