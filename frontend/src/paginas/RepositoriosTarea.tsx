import { useState } from "react";
import {
  obtenerFechasEntregas,
  obtenerRepositoriosTarea,
  reintentarRepositorio,
  sustituirRepositorio,
  verificarAccesosRepositorios,
  type FilaRepositorio,
} from "../lib/api";
import { useCurso } from "../components/Layout";
import {
  Aviso,
  Cargando,
  ErrorCarga,
  Estado,
  Mensajes,
  Paginacion,
  Tabla,
  Vacio,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import {
  fechaLegible,
  textoAccesoDocente,
  textoEstadoAcceso,
  textoEstadoRepositorio,
  textoMotivoRepositorio,
  textoTipoEntrega,
} from "../lib/textosTarea";
export function BloqueRepositorios({
  cursoId,
  tareaId,
}: {
  cursoId: string;
  tareaId: string;
}) {
  const { curso, puede } = useCurso();
  const op = useOperacion();
  const confirmar = useConfirmar();
  const c = useConsulta(
    `repositorios-${cursoId}-${tareaId}`,
    (signal) => obtenerRepositoriosTarea(cursoId, tareaId, signal),
    10_000,
  );
  const [buscar, setBuscar] = useState("");
  const [estado, setEstado] = useState("");
  const [pagina, setPagina] = useState(1);
  async function recuperar(f: FilaRepositorio, sustituir = false) {
    if (
      sustituir &&
      !(await confirmar({
        titulo: `Sustituir repositorio de ${f.sujeto}`,
        descripcion: `Se creará un repositorio nuevo. El registro de ${f.nombre} se conservará como evidencia del anterior.`,
        escribir: f.nombre,
        accion: "Sustituir repositorio",
        peligro: true,
      }))
    )
      return;
    void op.ejecutar(
      async () => {
        const r = sustituir
          ? await sustituirRepositorio(
              cursoId,
              tareaId,
              f.repositorio_id,
              f.nombre,
            )
          : await reintentarRepositorio(cursoId, tareaId, f.repositorio_id);
        if (!r.ok)
          throw new Error(r.error ?? "No se pudo solicitar la operación.");
        c.recargar();
      },
      sustituir
        ? "Sustitución solicitada. Consulta el progreso en la tabla."
        : "Reintento solicitado. El proceso continuará automáticamente.",
    );
  }
  if (!c.datos)
    return c.error ? (
      <ErrorCarga error={c.error} reintentar={c.recargar} />
    ) : (
      <Cargando texto="Consultando repositorios…" />
    );
  const r = c.datos.resumen;
  const verificacion = c.datos.verificacion_accesos;
  const comprobando = ["PENDIENTE", "EN_CURSO", "REINTENTAR"].includes(
    verificacion?.estado ?? "",
  );
  const enEspera =
    !!verificacion?.disponible_en &&
    new Date(verificacion.disponible_en).getTime() > Date.now();
  async function comprobarAccesos() {
    await op.ejecutar(async () => {
      const resultado = await verificarAccesosRepositorios(cursoId, tareaId);
      if (!resultado.ok || !resultado.datos)
        throw new Error(
          resultado.error ?? "No se pudo solicitar la comprobación.",
        );
      if (c.datos)
        c.actualizar({ ...c.datos, verificacion_accesos: resultado.datos });
    }, "Comprobación solicitada. Los accesos se actualizarán en esta tabla.");
  }
  const filas = c.datos.filas.filter(
    (f) =>
      (!estado || f.estado === estado) &&
      `${f.sujeto} ${f.cuenta_github ?? ""} ${f.nombre}`
        .toLocaleLowerCase("es-CL")
        .includes(buscar.toLocaleLowerCase("es-CL")),
  );
  const paginaActual = Math.min(
    pagina,
    Math.max(1, Math.ceil(filas.length / 20)),
  );
  const contadores: [string, number][] = [
    ["Operativos", r.operativos],
    ["Accesos pendientes", r.degradados],
    ["Esperando información", r.esperando_informacion],
    ["Por crear / creando", r.listos_para_crear + r.creando],
    ["Esperando a GitHub", r.esperando_limite],
    ["Bloqueados", r.bloqueados],
    ["Reintentando", r.error_transitorio],
    ["Requieren acción", r.error_permanente],
    ["Inaccesibles", r.inaccesibles],
    ["Fuera de alcance", r.fuera_de_alcance],
    ["Archivados", r.archivados],
  ];
  return (
    <>
      <div className="panel-header">
        <h2>Repositorios de estudiantes</h2>
        <span className="help">
          {c.cargando
            ? "Actualizando…"
            : "La tabla se refresca cada 10 segundos"}
        </span>
      </div>
      <Mensajes {...op} />
      <p className="help">
        {verificacion
          ? "GitHub se consulta cada minuto para comprobar invitaciones pendientes. Si hay muchas, se revisan por turnos y pueden tardar más."
          : "Las invitaciones se comprueban en GitHub en segundo plano."}{" "}
        La última comprobación de cada acceso aparece en su fila.
      </p>
      {verificacion && puede("tarea.administrar") && (
        <div className="actions">
          <button
            type="button"
            className="button secondary"
            disabled={
              op.ocupado ||
              comprobando ||
              enEspera ||
              !c.datos.filas.some((f) => f.sujeto_activo && f.url_html)
            }
            onClick={() => void comprobarAccesos()}
          >
            {comprobando
              ? "Comprobando invitaciones…"
              : "Comprobar invitaciones en GitHub"}
          </button>
          {!comprobando && enEspera && (
            <span className="help">
              Podrás solicitar otra comprobación en menos de un minuto.
            </span>
          )}
        </div>
      )}
      {comprobando && (
        <Aviso>
          La comprobación está pendiente o en curso. La tabla mostrará el
          resultado automáticamente.
        </Aviso>
      )}
      {verificacion?.estado === "REQUIERE_ATENCION" && (
        <Aviso tipo="error">
          No se pudo completar la comprobación de GitHub. Revisa el detalle de
          los repositorios e inténtalo de nuevo.
        </Aviso>
      )}
      {c.error && <ErrorCarga error={c.error} reintentar={c.recargar} />}
      {r.en_curso && (
        <Aviso>
          <strong>
            Creando {r.creados} de {r.sujetos_activos} repositorios
          </strong>
          {r.minutos_restantes > 0 &&
            ` · quedan aproximadamente ${r.minutos_restantes} min`}
          . Los estudiantes sin información completa continúan cuando la
          completen.
        </Aviso>
      )}
      <p className="help">
        {r.sujetos_activos} estudiantes activos en la tarea ·{" "}
        {r.sujetos_inactivos} inactivos. Los accesos pendientes no se cuentan
        como errores.
      </p>
      <div className="metrics">
        {contadores.map(([etiqueta, valor]) => (
          <div className="metric" key={etiqueta}>
            <strong>{valor}</strong>
            <span>{etiqueta}</span>
          </div>
        ))}
      </div>
      <div className="filters">
        <label>
          Buscar repositorio o estudiante
          <input
            type="search"
            value={buscar}
            onChange={(e) => {
              setBuscar(e.target.value);
              setPagina(1);
            }}
            placeholder="Nombre, cuenta o repositorio"
          />
        </label>
        <label>
          Estado del repositorio
          <select
            value={estado}
            onChange={(e) => {
              setEstado(e.target.value);
              setPagina(1);
            }}
          >
            <option value="">Todos los estados</option>
            {[
              ...new Set([
                ...c.datos.filas.map((f) => f.estado),
                ...(estado ? [estado] : []),
              ]),
            ].map((e) => (
              <option key={e} value={e}>
                {textoEstadoRepositorio(e)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {!filas.length ? (
        <Vacio>
          {c.datos.filas.length
            ? "No hay repositorios con estos filtros."
            : "Todavía no hay repositorios registrados. Se incorporan automáticamente después de sincronizar los estudiantes de esta tarea."}
        </Vacio>
      ) : (
        <>
          <Tabla etiqueta="Estado y accesos de los repositorios">
            <table>
              <thead>
                <tr>
                  <th scope="col">Estudiante</th>
                  <th scope="col">Repositorio</th>
                  <th scope="col">Estado y motivo</th>
                  <th scope="col">Acceso estudiante</th>
                  <th scope="col">Acceso docente</th>
                  <th scope="col">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filas
                  .slice((paginaActual - 1) * 20, paginaActual * 20)
                  .map((f) => (
                    <tr key={f.repositorio_id}>
                      <td>
                        <strong>{f.sujeto}</strong>
                        {f.cuenta_github && (
                          <p className="help">@{f.cuenta_github}</p>
                        )}
                        {!f.sujeto_activo && (
                          <p className="help">
                            Ya no forma parte de la tarea en Canvas
                          </p>
                        )}
                      </td>
                      <td>
                        {f.url_html ? (
                          <a href={f.url_html} target="_blank" rel="noreferrer">
                            {f.nombre}
                            <span className="sr-only">
                              {" "}
                              (abre GitHub en otra pestaña)
                            </span>
                          </a>
                        ) : (
                          <code>{f.nombre}</code>
                        )}
                        {f.reemplaza_a_id && (
                          <p className="help">
                            Sustituye a un repositorio anterior
                          </p>
                        )}
                      </td>
                      <td>
                        <Estado
                          valor={f.estado}
                          texto={textoEstadoRepositorio(f.estado)}
                        />
                        {f.motivo && (
                          <p className="help">
                            {textoMotivoRepositorio(f.motivo)}
                          </p>
                        )}
                        {f.error_mensaje_literal && (
                          <p className="help">{f.error_mensaje_literal}</p>
                        )}
                        {f.proximo_intento_en && (
                          <p className="help">
                            Próximo intento:{" "}
                            {fechaLegible(
                              f.proximo_intento_en,
                              curso.zona_horaria,
                            )}
                          </p>
                        )}
                      </td>
                      <td>
                        {f.acceso_estado
                          ? textoEstadoAcceso(f.acceso_estado)
                          : "Sin acceso informado"}
                        {f.cuenta_github && f.acceso_estado && (
                          <p className="help">
                            {f.acceso_verificado_en
                              ? `Comprobado en GitHub: ${fechaLegible(f.acceso_verificado_en, curso.zona_horaria)}`
                              : "Sin fecha de comprobación registrada"}
                          </p>
                        )}
                        {f.acceso_error && (
                          <p className="help">{f.acceso_error}</p>
                        )}
                      </td>
                      <td>
                        {f.acceso_docente
                          ? textoAccesoDocente(f.acceso_docente)
                          : "Sin acceso informado"}
                      </td>
                      <td>
                        {puede("tarea.administrar") && (
                          <div className="actions">
                            {[
                              "ERROR_PERMANENTE",
                              "ERROR_TRANSITORIO",
                              "BLOQUEADO",
                              "ESPERANDO_LIMITE",
                            ].includes(f.estado) && (
                              <button
                                disabled={op.ocupado}
                                onClick={() => recuperar(f)}
                              >
                                Reintentar
                              </button>
                            )}
                            {f.estado === "INACCESIBLE" && (
                              <button
                                className="danger"
                                disabled={op.ocupado}
                                onClick={() => recuperar(f, true)}
                              >
                                Sustituir
                              </button>
                            )}
                          </div>
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
            cambiar={setPagina}
          />
        </>
      )}
    </>
  );
}
export function LineaFechas({
  cursoId,
  tareaId,
}: {
  cursoId: string;
  tareaId: string;
}) {
  const c = useConsulta(`fechas-${cursoId}-${tareaId}`, (signal) =>
    obtenerFechasEntregas(cursoId, tareaId, signal),
  );
  if (c.error) return <ErrorCarga error={c.error} reintentar={c.recargar} />;
  if (!c.datos) return <Cargando texto="Consultando fechas por sección…" />;
  return (
    <>
      {c.datos.map((f) => (
        <div className="panel" key={f.entrega_id}>
          <strong>
            {textoTipoEntrega(f.tipo)} · Entrega {f.orden}
          </strong>
          <p>Cierre: {f.cierre_base}</p>
          {f.excepciones.map((e, i) => (
            <p key={i}>
              {e.etiqueta}: {e.fecha}
            </p>
          ))}
          {f.sujetos_sin_fecha > 0 && (
            <p className="help">
              {f.sujetos_sin_fecha} estudiantes sin fecha de cierre informada.
            </p>
          )}
        </div>
      ))}
    </>
  );
}
