import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  crearRegistroGithub,
  declararMapeoManual,
  importarMapeoCsv,
  obtenerPersonas,
  restaurarRegistroGithub,
  type FilaCsvMapeo,
} from "../lib/api";
import { SeguimientoTrabajos, SincronizarCanvas } from "../components/SeguimientoTrabajos";
import { obtenerHistorialMapeo } from "../lib/seguimientoOperacion";
import { fechaLegible } from "../lib/textosTarea";
import { comprobar, detalleLegible } from "../lib/errores";
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
            if (!r.ok) throw new Error(detalleLegible(r.cuerpo));
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
function HistorialMapeo({ estudianteId }: { estudianteId: string }) {
  const { curso } = useCurso();
  const [abierto, setAbierto] = useState(false);
  const c = useConsulta(`historial-${curso.id}-${estudianteId}-${abierto}`, (signal) =>
    abierto ? obtenerHistorialMapeo(curso.id, estudianteId, signal) : Promise.resolve([]));
  return <details onToggle={(e) => setAbierto(e.currentTarget.open)}>
    <summary>Historial de cuentas</summary>
    {abierto && <>
      {c.error ? <ErrorCarga error={c.error} reintentar={c.recargar} /> : c.cargando ? <Cargando /> : !c.datos?.length ? <p>No hay asociaciones registradas.</p> :
        <ol className="list-clean">{c.datos.map((m) => <li key={m.id}>
          <strong>{m.login_declarado ? `@${m.login_declarado}` : "Sin usuario declarado"}</strong> · <Estado valor={m.estado} />
          <p className="help">{fechaLegible(m.creado_en, curso.zona_horaria)} · {m.origen ? etiqueta(m.origen) : "Origen no registrado"} · {m.creado_por_nombre ?? "Sin autor docente registrado"}</p>
          {m.cuenta_login_actual && <p className="help">Cuenta actual: @{m.cuenta_login_actual} · Identificador de GitHub: {m.github_user_id}</p>}
          {m.vigente_desde && <p className="help">Vigencia: {fechaLegible(m.vigente_desde, curso.zona_horaria)} — {m.vigente_hasta ? fechaLegible(m.vigente_hasta, curso.zona_horaria) : "sin término registrado"}</p>}
          {m.motivo_invalidacion && <p>{etiqueta(m.motivo_invalidacion)}</p>}
        </li>)}</ol>}
    </>}
  </details>;
}

export function Personas() {
  const { curso, puede } = useCurso();
  const [params, setParams] = useSearchParams();
  const confirmar = useConfirmar();
  const op = useOperacion();
  const [registroPendiente, setRegistroPendiente] = useState(false);
  const [trabajoRegistro, setTrabajoRegistro] = useState<string | null>(null);
  const consulta = useConsulta(
    `personas-${curso.id}`,
    (signal) => obtenerPersonas(curso.id, signal),
    registroPendiente ? 5000 : 0,
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
    if (registroPendiente && consulta.datos?.registro_estado === "ABIERTA") {
      setRegistroPendiente(false);
      op.setMensaje("La tarea de registro está disponible en Canvas.");
    }
  }, [consulta.datos, registroPendiente]);
  useEffect(() => {
    if (!registroPendiente) return;
    const temporizador = window.setTimeout(() => {
      setRegistroPendiente(false);
      op.setMensaje(
        "El proceso sigue sin confirmar su resultado. Usa Actualizar vista para consultar los cambios; los datos disponibles permanecen visibles.",
      );
    }, 180_000);
    return () => window.clearTimeout(temporizador);
  }, [registroPendiente]);
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
            <SincronizarCanvas actualizado={consulta.recargar} />
          </>
        }
      />
      <Mensajes {...op} />
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
              disabled={op.ocupado || registroPendiente}
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
                    setRegistroPendiente(true);
                    const cuerpo = await respuesta.json();
                    setTrabajoRegistro(cuerpo.trabajo_id ?? null);
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
        {trabajoRegistro && <SeguimientoTrabajos ids={[trabajoRegistro]} terminado={() => { setRegistroPendiente(false); consulta.recargar(); }} />}
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
                : "Aún no hay estudiantes sincronizados. Un profesor puede solicitar la sincronización con Canvas."}
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
