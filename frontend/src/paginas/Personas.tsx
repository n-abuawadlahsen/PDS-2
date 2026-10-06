import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  apiFetch,
  crearRegistroGithub,
  declararMapeoManual,
  importarMapeoCsv,
  obtenerPersonas,
  restaurarRegistroGithub,
  sincronizarAhora,
  type FilaCsvMapeo,
} from "../lib/api";
import { comprobar, detalleLegible } from "../lib/errores";
import { EstadoTrabajo } from "../components/EstadoTrabajo";
import { useCurso } from "../components/Layout";
import {
  Cabecera,
  Cargando,
  ErrorCarga,
  Estado,
  Mensajes,
  Paginacion,
  Tabla,
  Vacio,
  etiqueta,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import { fechaLegible } from "../lib/textosTarea";
import { RecordatorioMapeo } from "./RecordatorioMapeo";
import { InvitacionesEstudiante } from "../components/InvitacionesEstudiante";
import { FusionesCanvas } from "../components/FusionesCanvas";

function HistorialMapeo({ estudianteId }: { estudianteId: string }) {
  const { curso } = useCurso();
  const [abierto, setAbierto] = useState(false);
  const consulta = useConsulta(
    `historial-mapeo:${curso.id}:${estudianteId}:${abierto}`,
    async (signal) => {
      if (!abierto) return [];
      const r = await apiFetch(
        `/api/cursos/${curso.id}/personas/${estudianteId}/mapeo/historial`,
        { signal },
      );
      await comprobar(r);
      return r.json() as Promise<
        {
          id: string;
          cuenta_login: string | null;
          estado: string;
          origen: string | null;
          creado_en: string;
          vigente_hasta: string | null;
        }[]
      >;
    },
  );
  return (
    <details onToggle={(e) => setAbierto(e.currentTarget.open)}>
      <summary>Historial de cuentas</summary>
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {consulta.cargando ? (
        <Cargando />
      ) : (
        <ul className="list-clean">
          {consulta.datos?.map((m) => (
            <li key={m.id}>
              <strong>
                {m.cuenta_login ? `@${m.cuenta_login}` : "Sin cuenta"}
              </strong>{" "}
              · {etiqueta(m.estado)}
              <p className="help">
                {fechaLegible(m.creado_en, curso.zona_horaria)} ·{" "}
                {m.origen ? etiqueta(m.origen) : "Origen no registrado"}
              </p>
              {m.vigente_hasta && (
                <p className="help">
                  Fin de vigencia:{" "}
                  {fechaLegible(m.vigente_hasta, curso.zona_horaria)}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
      {!consulta.cargando &&
        !consulta.error &&
        consulta.datos?.length === 0 && <p>Sin historial registrado.</p>}
    </details>
  );
}

const MOTIVOS_RECHAZO_MAPEO: Record<string, string> = {
  CUENTA_NO_EXISTE:
    "no existe en GitHub como cuenta de usuario. Revisa que el nombre esté bien escrito.",
  ES_ORGANIZACION:
    "es una organización de GitHub, no una cuenta personal. Pide al estudiante su usuario.",
  CUENTA_NO_ELEGIBLE:
    "no se puede asociar: pertenece a alguien del equipo docente o ya está asociada a otro estudiante en otro curso.",
  CUENTA_YA_ASIGNADA:
    "ya está asociada a otro estudiante de este curso. Revisa ese caso en Pendientes.",
};

// El backend responde {detail: {motivo, detalle}} y `detalle` es el login:
// sin esta traduccion, el mensaje mostraba solo la cuenta y no la causa.
function rechazoMapeoLegible(cuerpo: unknown): string {
  const detail = (cuerpo as { detail?: { motivo?: string; detalle?: string } })
    ?.detail;
  const texto = detail?.motivo
    ? MOTIVOS_RECHAZO_MAPEO[detail.motivo]
    : undefined;
  if (!texto) return detalleLegible(cuerpo);
  const login =
    detail?.detalle && !/\s/.test(detail.detalle) ? detail.detalle : null;
  return login ? `La cuenta @${login} ${texto}` : `La cuenta ${texto}`;
}

function EditorMapeo({
  estudianteId,
  nombre,
  actual,
  guardado,
}: {
  estudianteId: string;
  nombre: string;
  actual: string | null;
  guardado: () => void;
}) {
  const { curso } = useCurso();
  const [login, setLogin] = useState(actual ?? "");
  const op = useOperacion();
  return (
    <details>
      <summary>{actual ? "Corregir cuenta" : "Asociar cuenta"}</summary>
      <form
        className="form-stack"
        onSubmit={(e) => {
          e.preventDefault();
          void op.ejecutar(async () => {
            const r = await declararMapeoManual(
              curso.id,
              estudianteId,
              login.trim(),
            );
            if (!r.ok) throw new Error(rechazoMapeoLegible(r.cuerpo));
            guardado();
          }, "Cuenta asociada. El proceso continuará automáticamente.");
        }}
      >
        <label>
          Cuenta de GitHub de {nombre}
          <input
            required
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            autoComplete="off"
          />
        </label>
        <button disabled={op.ocupado || !login.trim()}>
          {op.ocupado ? "Validando…" : "Validar y guardar"}
        </button>
        <Mensajes {...op} />
      </form>
    </details>
  );
}
function ImportacionCsv({ guardado }: { guardado: () => void }) {
  const { curso } = useCurso();
  const [texto, setTexto] = useState("");
  const [revision, setRevision] = useState<{
    texto: string;
    filas: FilaCsvMapeo[];
    aplicada: boolean;
  } | null>(null);
  const version = useRef(0);
  const op = useOperacion();
  function cambiar(valor: string) {
    version.current += 1;
    setTexto(valor);
    setRevision(null);
    op.setMensaje(null);
  }
  const revisada =
    revision?.texto === texto &&
    !revision.aplicada &&
    revision.filas.some((f) => f.resultado === "SE_APLICARIA");
  return (
    <details className="panel">
      <summary>Alternativa docente: importar cuentas por CSV</summary>
      <p>
        Primero revisa las filas. Se aplicarán únicamente las válidas; el
        servidor vuelve a comprobar cada asociación al guardar.
      </p>
      <p className="help" id="csv-ayuda">
        Columnas: canvas_user_id (o login_id) y github_login.
      </p>
      <label>
        Contenido CSV
        <textarea
          aria-describedby="csv-ayuda"
          rows={5}
          value={texto}
          onChange={(e) => cambiar(e.target.value)}
          placeholder={"canvas_user_id,github_login\n2001,cuenta-estudiante"}
        />
      </label>
      <label className="help">
        O cargar un archivo CSV
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => {
            const archivo = e.target.files?.[0];
            if (archivo)
              void op.ejecutar(async () => cambiar(await archivo.text()));
          }}
        />
      </label>
      <Mensajes {...op} />
      <div className="actions">
        <button
          disabled={op.ocupado || !texto.trim()}
          onClick={() => {
            const versionConsultada = version.current;
            const contenido = texto;
            void op.ejecutar(async () => {
              const r = await importarMapeoCsv(curso.id, contenido, false);
              if (versionConsultada === version.current)
                setRevision({
                  texto: contenido,
                  filas: r.filas,
                  aplicada: false,
                });
            });
          }}
        >
          Previsualizar
        </button>
        <button
          className="primary"
          disabled={op.ocupado || !revisada}
          onClick={() => {
            if (!revisada || !revision) return;
            const contenido = revision.texto;
            const versionAplicada = version.current;
            void op.ejecutar(async () => {
              const r = await importarMapeoCsv(curso.id, contenido, true);
              if (versionAplicada === version.current)
                setRevision({
                  texto: contenido,
                  filas: r.filas,
                  aplicada: true,
                });
              guardado();
            }, "Importación procesada. Revisa el resultado de cada fila.");
          }}
        >
          Aplicar filas revisadas
        </button>
      </div>
      {!revisada && (
        <p className="help">
          Previsualiza el contenido vigente antes de aplicar. Cualquier cambio
          exige una nueva revisión.
        </p>
      )}
      {revision && (
        <Tabla etiqueta="Revisión de importación CSV" fija={false}>
          <table>
            <caption>
              {revision.aplicada
                ? "Resultado de la importación"
                : "Revisión antes de aplicar"}
            </caption>
            <thead>
              <tr>
                <th scope="col">Fila</th>
                <th scope="col">Estudiante</th>
                <th scope="col">GitHub</th>
                <th scope="col">Resultado</th>
                <th scope="col">Detalle</th>
              </tr>
            </thead>
            <tbody>
              {revision.filas.map((f) => (
                <tr key={f.fila}>
                  <td>{f.fila}</td>
                  <td>{f.canvas_user_id ?? f.login_id ?? "Sin identificar"}</td>
                  <td>{f.github_login}</td>
                  <td>
                    <Estado valor={f.resultado} />
                  </td>
                  <td>{f.detalle || "Sin observaciones"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Tabla>
      )}
    </details>
  );
}
export function Personas() {
  const { curso, puede } = useCurso();
  const [params, setParams] = useSearchParams();
  const confirmar = useConfirmar();
  const op = useOperacion();
  const [sincronizacion, setSincronizacion] = useState<{
    anterior: string | null;
  } | null>(null);
  const [registroPendiente, setRegistroPendiente] = useState(false);
  const consulta = useConsulta(
    `personas-${curso.id}`,
    (signal) => obtenerPersonas(curso.id, signal),
    sincronizacion ||
      registroPendiente ||
      params.has("sincronizacion") ||
      params.has("registro")
      ? 5000
      : 0,
  );
  const buscar = params.get("buscar") ?? "";
  const seccion = params.get("seccion") ?? "";
  const estado = params.get("estado") ?? "";
  const estudiante = params.get("estudiante");
  const pagina = Math.max(1, Number(params.get("pagina")) || 1);
  function filtro(clave: string, valor: string) {
    setParams(
      (actual) => {
        const siguiente = new URLSearchParams(actual);
        if (valor) siguiente.set(clave, valor);
        else siguiente.delete(clave);
        if (clave !== "pagina") siguiente.delete("pagina");
        return siguiente;
      },
      { replace: true },
    );
  }
  useEffect(() => {
    if (
      sincronizacion &&
      consulta.datos?.roster_sincronizado_en &&
      consulta.datos.roster_sincronizado_en !== sincronizacion.anterior
    ) {
      setSincronizacion(null);
      op.setMensaje("Los datos de estudiantes se actualizaron desde Canvas.");
    }
  }, [consulta.datos, sincronizacion]);
  useEffect(() => {
    if (
      registroPendiente &&
      ["ACTIVA", "ABIERTA"].includes(consulta.datos?.registro_estado ?? "")
    ) {
      setRegistroPendiente(false);
      op.setMensaje("La tarea de registro está disponible en Canvas.");
    }
  }, [consulta.datos, registroPendiente]);
  useEffect(() => {
    if (!sincronizacion && !registroPendiente) return;
    const temporizador = window.setTimeout(() => {
      setSincronizacion(null);
      setRegistroPendiente(false);
      op.setMensaje(
        "El proceso sigue sin confirmar su resultado. Usa Actualizar vista para consultar los cambios; los datos disponibles permanecen visibles.",
      );
    }, 180_000);
    return () => window.clearTimeout(temporizador);
  }, [sincronizacion, registroPendiente]);
  const d = consulta.datos;
  if (!d)
    return (
      <>
        <Cabecera titulo="Personas" />
        {consulta.error ? (
          <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
        ) : (
          <Cargando />
        )}
      </>
    );
  const filas = d.estudiantes.filter(
    (e) =>
      (!estudiante || e.id === estudiante) &&
      `${e.nombre} ${e.email ?? ""} ${e.sis_user_id ?? ""} ${e.mapeo.cuenta_login ?? ""}`
        .toLocaleLowerCase("es-CL")
        .includes(buscar.toLocaleLowerCase("es-CL")) &&
      (!seccion || e.secciones.includes(seccion)) &&
      (!estado || e.mapeo.estado === estado),
  );
  const paginaActual = Math.min(
    pagina,
    Math.max(1, Math.ceil(filas.length / 20)),
  );
  const estados = [...new Set(d.estudiantes.map((e) => e.mapeo.estado))];
  const secciones = [...new Set(d.estudiantes.flatMap((e) => e.secciones))];
  const estudiantesVigentes = d.estudiantes.filter((e) =>
    ["ACTIVO", "INVITADO"].includes(e.estado),
  );
  return (
    <>
      <Cabecera
        titulo="Personas"
        descripcion="Estudiantes, secciones y grupos de Canvas. Revisa las cuentas necesarias para crear sus repositorios."
        acciones={
          <>
            <button disabled={consulta.cargando} onClick={consulta.recargar}>
              Actualizar vista
            </button>
            {puede("curso.ver") && (
              <button
                className="primary"
                disabled={
                  op.ocupado ||
                  Boolean(sincronizacion) ||
                  params.has("sincronizacion")
                }
                onClick={() =>
                  void op.ejecutar(async () => {
                    const respuesta = await sincronizarAhora(curso.id);
                    await comprobar(respuesta);
                    const trabajo = (await respuesta.json()) as {
                      trabajo_id?: string;
                      trabajo_ids?: string[];
                    };
                    const ids =
                      trabajo.trabajo_ids ??
                      (trabajo.trabajo_id ? [trabajo.trabajo_id] : []);
                    if (ids.length) filtro("sincronizacion", ids.join(","));
                    setSincronizacion({ anterior: d.roster_sincronizado_en });
                  }, "Sincronización solicitada. Los datos se actualizarán cuando termine.")
                }
              >
                {sincronizacion
                  ? "Sincronización solicitada"
                  : "Sincronizar con Canvas"}
              </button>
            )}
          </>
        }
      />
      <Mensajes {...op} />
      <FusionesCanvas alCambiar={consulta.recargar} />
      {(params.get("sincronizacion")?.split(",") ?? [])
        .filter((id) => /^[a-zA-Z0-9-]{1,80}$/.test(id))
        .map((id) => (
          <EstadoTrabajo
            key={id}
            ruta={`/api/cursos/${curso.id}/trabajos/${id}`}
            zona={curso.zona_horaria}
            cadencia={5000}
            alTerminar={(trabajo) => {
              setParams(
                () => {
                  const nuevo = new URLSearchParams(window.location.search);
                  const pendientes = (
                    nuevo.get("sincronizacion")?.split(",") ?? []
                  ).filter((t) => t !== trabajo.id);
                  if (pendientes.length)
                    nuevo.set("sincronizacion", pendientes.join(","));
                  else nuevo.delete("sincronizacion");
                  return nuevo;
                },
                { replace: true },
              );
              consulta.recargar();
              if (["REQUIERE_ATENCION", "CANCELADO"].includes(trabajo.estado)) {
                setSincronizacion(null);
                op.setError(
                  "Una parte de la sincronización requiere atención. Los datos anteriores siguen disponibles; revisa Canvas y vuelve a solicitarla.",
                );
              }
            }}
          />
        ))}
      {params.get("registro") && (
        <EstadoTrabajo
          key={params.get("registro")}
          ruta={`/api/cursos/${curso.id}/trabajos/${params.get("registro")}`}
          zona={curso.zona_horaria}
          cadencia={5000}
          alTerminar={(trabajo) => {
            setParams(
              () => {
                const nuevo = new URLSearchParams(window.location.search);
                nuevo.delete("registro");
                return nuevo;
              },
              { replace: true },
            );
            consulta.recargar();
            if (["REQUIERE_ATENCION", "CANCELADO"].includes(trabajo.estado)) {
              setRegistroPendiente(false);
              op.setError(
                "La tarea de registro no pudo completarse. Revisa la vinculación Canvas y vuelve a solicitarla.",
              );
            }
          }}
        />
      )}
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      <div className="metrics">
        <div className="metric">
          <strong>{d.estudiantes.length}</strong>
          <span>Estudiantes sincronizados</span>
        </div>
        <div className="metric">
          <strong>
            {
              estudiantesVigentes.filter((e) => e.mapeo.estado === "VIGENTE")
                .length
            }{" "}
            / {estudiantesVigentes.length}
          </strong>
          <span>Inscripciones vigentes con cuenta verificada</span>
        </div>
        <div className="metric">
          <strong>{d.secciones.length}</strong>
          <span>Secciones</span>
        </div>
      </div>
      <RecordatorioMapeo cursoId={curso.id} />
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Registro de cuentas de GitHub</h2>
            <p className="help">
              Los estudiantes declaran su cuenta en la tarea de registro de
              Canvas, sin entrar a esta aplicación.
            </p>
          </div>
          <Estado valor={d.registro_estado} />
        </div>
        {puede("comunicacion.enviar") &&
          (d.registro_estado === "NO_CREADA" ||
            ["ALTERADA", "DESAPARECIDA"].includes(d.registro_estado)) && (
            <button
              className="primary"
              disabled={
                op.ocupado || registroPendiente || params.has("registro")
              }
              onClick={async () => {
                if (
                  !(await confirmar({
                    titulo:
                      d.registro_estado === "NO_CREADA"
                        ? "Crear registro en Canvas"
                        : "Restaurar registro en Canvas",
                    descripcion:
                      "Se publicará la tarea Registro de tu cuenta de GitHub en Canvas para que los estudiantes declaren su usuario. No tienen que acceder a esta aplicación.",
                    accion: "Publicar registro",
                  }))
                )
                  return;
                void op.ejecutar(async () => {
                  const respuesta = await (d.registro_estado === "NO_CREADA"
                    ? crearRegistroGithub(curso.id)
                    : restaurarRegistroGithub(curso.id));
                  await comprobar(respuesta);
                  if (respuesta.status === 202) {
                    const trabajo = (await respuesta.json()) as {
                      trabajo_id?: string;
                    };
                    if (trabajo.trabajo_id)
                      filtro("registro", trabajo.trabajo_id);
                    setRegistroPendiente(true);
                    op.setMensaje(
                      "La creación quedó pendiente en Canvas. Consultaremos el resultado mientras continúas trabajando.",
                    );
                  } else
                    op.setMensaje(
                      "La tarea de registro está disponible en Canvas.",
                    );
                  consulta.recargar();
                });
              }}
            >
              {d.registro_estado === "NO_CREADA"
                ? "Crear tarea de registro en Canvas"
                : "Restaurar tarea de registro"}
            </button>
          )}
        <p className="help">
          Una cuenta pendiente no detiene a los demás estudiantes.{" "}
          <Link to={`/cursos/${curso.id}/pendientes`}>Revisar pendientes</Link>
        </p>
      </section>
      <section className="panel">
        <h2>Estudiantes</h2>
        {estudiante && (
          <p className="help">
            Mostrando la persona seleccionada desde Pendientes.{" "}
            <button onClick={() => filtro("estudiante", "")}>
              Ver todas las personas
            </button>
          </p>
        )}
        {!puede("mapeo.editar") && (
          <p className="help">
            Los correos e identificadores personales están enmascarados para tu
            permiso actual.
          </p>
        )}
        <p className="help">
          Última sincronización:{" "}
          {d.roster_sincronizado_en
            ? fechaLegible(d.roster_sincronizado_en, curso.zona_horaria)
            : "todavía no se han obtenido datos de Canvas"}
          .{consulta.cargando && " Actualizando vista…"}
        </p>
        <div className="filters">
          <label>
            Buscar estudiante
            <input
              type="search"
              value={buscar}
              onChange={(e) => {
                filtro("buscar", e.target.value);
              }}
              placeholder="Nombre, correo o cuenta"
            />
          </label>
          <label>
            Sección
            <select
              value={seccion}
              onChange={(e) => {
                filtro("seccion", e.target.value);
              }}
            >
              <option value="">Todas las secciones</option>
              {secciones.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Cuenta de GitHub
            <select
              value={estado}
              onChange={(e) => {
                filtro("estado", e.target.value);
              }}
            >
              <option value="">Todos los estados</option>
              {estados.map((s) => (
                <option value={s} key={s}>
                  {etiqueta(s)}
                </option>
              ))}
            </select>
          </label>
        </div>
        {!filas.length ? (
          <Vacio>
            {d.estudiantes.length
              ? "No hay estudiantes que coincidan con los filtros."
              : d.roster_sincronizado_en
                ? "No hay estudiantes en los datos sincronizados."
                : "Aún no hay estudiantes sincronizados. Puedes solicitar la sincronización con Canvas."}
          </Vacio>
        ) : (
          <>
            <Tabla etiqueta="Estudiantes del curso">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Estudiante</th>
                    <th scope="col">Inscripción</th>
                    <th scope="col">Secciones y grupos</th>
                    <th scope="col">Cuenta de GitHub</th>
                  </tr>
                </thead>
                <tbody>
                  {filas
                    .slice((paginaActual - 1) * 20, paginaActual * 20)
                    .map((e) => (
                      <tr key={e.id}>
                        <td>
                          <strong>{e.nombre}</strong>
                          <p className="help">
                            {e.email ?? "Correo no disponible"}
                          </p>
                          {e.sis_user_id && (
                            <p className="help">{e.sis_user_id}</p>
                          )}
                        </td>
                        <td>
                          <Estado valor={e.estado} />
                        </td>
                        <td>
                          {e.secciones.join(", ") || "Sin sección informada"}
                          <p className="help">
                            Grupos: {e.grupos.join(", ") || "sin grupo"}
                          </p>
                        </td>
                        <td>
                          {e.mapeo.cuenta_login && (
                            <strong>@{e.mapeo.cuenta_login}</strong>
                          )}
                          <div>
                            <Estado valor={e.mapeo.estado} />
                          </div>
                          {e.mapeo.motivo_invalidacion && (
                            <p className="help">
                              {etiqueta(e.mapeo.motivo_invalidacion)}
                            </p>
                          )}
                          <HistorialMapeo estudianteId={e.id} />
                          <InvitacionesEstudiante estudianteId={e.id} />
                          {puede("mapeo.editar") && (
                            <EditorMapeo
                              estudianteId={e.id}
                              nombre={e.nombre}
                              actual={e.mapeo.cuenta_login}
                              guardado={consulta.recargar}
                            />
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </Tabla>
            <Paginacion
              total={filas.length}
              pagina={paginaActual}
              cambiar={(numero) => filtro("pagina", String(numero))}
            />
          </>
        )}
      </section>
      {puede("mapeo.editar") && <ImportacionCsv guardado={consulta.recargar} />}
      <div className="two-columns">
        <details className="panel">
          <summary>Secciones ({d.secciones.length})</summary>
          <ul className="list-clean">
            {d.secciones.map((s) => (
              <li key={s.id}>
                <strong>{s.nombre}</strong>
                <p className="help">
                  {s.cantidad_estudiantes} estudiantes · {etiqueta(s.estado)}
                </p>
              </li>
            ))}
          </ul>
          {!d.secciones.length && <p>No hay secciones sincronizadas.</p>}
        </details>
        <details className="panel">
          <summary>Grupos ({d.grupos.length})</summary>
          <p className="help">
            Integrantes y conjuntos de grupos sincronizados desde Canvas. Última
            sincronización:{" "}
            {d.grupos_sincronizado_en
              ? fechaLegible(d.grupos_sincronizado_en, curso.zona_horaria)
              : "sin sincronizar"}
            .
          </p>
          <ul className="list-clean">
            {d.grupos.map((g) => (
              <li key={g.id}>
                <strong>{g.nombre}</strong>
                <p className="help">
                  {g.conjunto} · {etiqueta(g.estado)}
                </p>
                <p>{g.integrantes.join(", ") || "Sin integrantes"}</p>
              </li>
            ))}
          </ul>
        </details>
      </div>
      <section className="panel next-step">
        <h2>Continúa con las tareas</h2>
        <p>Puedes continuar aunque queden cuentas de GitHub pendientes.</p>
        <Link className="button primary" to={`/cursos/${curso.id}/tareas`}>
          Ir a Tareas
        </Link>
      </section>
    </>
  );
}
