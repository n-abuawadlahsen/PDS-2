import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  desmarcarHito,
  marcarHito,
  obtenerPersonas,
  resolverIdentidad,
  type CandidatoPropagacion,
  type CommitTimeline,
  type EstudianteEspejo,
  type IdentidadGit,
  type Timeline,
} from "../lib/api";
import {
  fechaLegible,
  diaLegible,
  textoEstadoCaptura,
  textoMotivoVersion,
  textoCausaParticipacion,
} from "../lib/textosTarea";

import { consultarOperacion, parametrosOperacion } from "../lib/apiOperacion";
import { comprobar } from "../lib/errores";
import { useCurso } from "../components/Layout";
import {
  Aviso,
  Cabecera,
  Cargando,
  ErrorCarga,
  Mensajes,
  Tabla,
  Vacio,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";

const ESTILO_MOTIVO = {
  fontSize: "0.85rem",
  color: "var(--color-text-secondary)",
} as const;
const ESTILO_AMBAR = {
  background: "var(--color-warning-background)",
  padding: "0.5rem 0.75rem",
} as const;

const EXCLUSION: Record<string, string> = {
  MERGE: "merge, no cuenta como aporte",
  COMMIT_INICIAL: "commit inicial de la plantilla",
  HUERFANO: "huérfano: dejó de ser alcanzable",
};

const EVENTO: Record<string, string> = {
  REPOSITORIO_CREADO: "Repositorio creado",
  REPOSITORIO_LISTO: "Repositorio listo",
  INVITACION_EMITIDA: "Invitación emitida",
  INVITACION_ACEPTADA: "Invitación aceptada",
  HISTORIA_REESCRITA: "Historia reescrita",
  RAMA_CREADA: "Rama creada",
  RAMA_BORRADA: "Rama borrada",
  ARCHIVADO: "Archivado",
  DESARCHIVADO: "Desarchivado",
};

const CAUSA_VACIA: Record<string, string> = {
  SIN_DATOS_TODAVIA:
    "Sin datos todavía: el repositorio aún no tuvo su primera lectura completa.",
  SIN_ACCESO: "Sin actividad: el estudiante no ha aceptado su invitación.",
  SIN_ATRIBUIR:
    "Hay commits sin atribuir: puede haber trabajado con otro correo de Git.",
  SIN_COMMITS: "Sin actividad: no hay commits contables en este repositorio.",
};

/** Timeline del repositorio (SPEC 10 S10.9): cuatro capas en un eje de días
 * del curso. Periodo, integrante y rama viajan en la URL. */
export function RepositorioTimeline() {
  const { cursoId, tareaId, repoId } = useParams<{
    cursoId: string;
    tareaId: string;
    repoId: string;
  }>();
  const [parametros, setParametros] = useSearchParams();
  const { curso, puede } = useCurso();
  const op = useOperacion();
  const [hito, setHito] = useState<CommitTimeline | null>(null);
  const [notaHito, setNotaHito] = useState("");
  const [abiertos, setAbiertos] = useState<Set<string>>(new Set());
  const periodo = parametros.get("periodo") ?? undefined;
  const integrante = parametros.get("integrante") ?? undefined;

  const rama = parametros.get("rama") ?? undefined;
  const filtros = parametrosOperacion({ periodo, integrante, rama });
  const consulta = useConsulta(
    `timeline-${cursoId}-${tareaId}-${repoId}-${filtros}`,
    (signal) =>
      consultarOperacion<Timeline>(
        `/api/cursos/${cursoId}/tareas/${tareaId}/repos/${repoId}/timeline?${filtros}`,
        { signal },
      ),
  );
  const datos = consulta.datos;

  function cambiar(clave: string, valor: string | null) {
    const nuevos = new URLSearchParams(parametros);
    if (valor) nuevos.set(clave, valor);
    else nuevos.delete(clave);
    setParametros(nuevos, { replace: true });
  }

  async function onHito(c: CommitTimeline) {
    if (!cursoId || !tareaId || !repoId || !puede("tarea.administrar")) return;
    if (!c.hito) {
      setHito(c);
      setNotaHito("");
      return;
    }
    await op.ejecutar(async () => {
      await comprobar(await desmarcarHito(cursoId, tareaId, repoId, c.sha));
      consulta.recargar();
    }, "Hito retirado. El cambio queda en el historial.");
  }
  if (!cursoId || !tareaId || !repoId || !datos)
    return consulta.error ? (
      <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
    ) : (
      <Cargando texto="Consultando la actividad del repositorio…" />
    );
  const retorno = new URLSearchParams(parametros.get("retorno") ?? "");
  retorno.set("vista", "actividad");
  if (!retorno.has("periodo")) retorno.set("periodo", datos.periodo);
  const ramas = [
    ...new Set(
      [
        datos.repositorio.rama_por_defecto,
        rama,
        ...datos.dias.flatMap((d) => d.commits.map((c) => c.rama)),
      ].filter((r): r is string => Boolean(r)),
    ),
  ];

  return (
    <div className="stack">
      <p>
        <Link to={`/cursos/${cursoId}/tareas/${tareaId}?${retorno}`}>
          ← Volver al tablero
        </Link>
      </p>
      <Cabecera
        titulo={`Actividad de ${datos.sujeto}`}
        descripcion={datos.repositorio.nombre}
        acciones={
          <Link
            className="button"
            to={`/cursos/${cursoId}/tareas/${tareaId}/entregas${periodo?.startsWith("entrega:") ? `?entrega=${periodo.slice(8)}` : ""}`}
          >
            Ver versiones de entrega
          </Link>
        }
      />
      <p className="help">
        Historia registrada en la aplicación · zona horaria {curso.zona_horaria}{" "}
        · rama por defecto:{" "}
        {datos.repositorio.rama_por_defecto ?? "No disponible"}
      </p>
      <Mensajes {...op} />
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {hito && (
        <form
          className="panel form-stack"
          onSubmit={(e) => {
            e.preventDefault();
            void op.ejecutar(async () => {
              await comprobar(
                await marcarHito(
                  cursoId,
                  tareaId,
                  repoId,
                  hito.sha,
                  notaHito.trim(),
                ),
              );
              setHito(null);
              consulta.recargar();
            }, "Hito registrado.");
          }}
        >
          <h2>Marcar hito en {hito.sha_corto}</h2>
          <label>
            Nota del hito
            <input
              autoFocus
              required
              maxLength={140}
              value={notaHito}
              onChange={(e) => setNotaHito(e.target.value)}
            />
          </label>
          <div className="actions">
            <button
              className="primary"
              disabled={op.ocupado || !notaHito.trim()}
            >
              Guardar hito
            </button>
            <button
              type="button"
              disabled={op.ocupado}
              onClick={() => setHito(null)}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}
      {datos.enlaces.motivo && (
        <p style={ESTILO_AMBAR}>{datos.enlaces.motivo}</p>
      )}
      {datos.sin_commits_contables && datos.causa_vacia && (
        <p style={ESTILO_AMBAR}>{CAUSA_VACIA[datos.causa_vacia]}</p>
      )}
      <div className="filters">
        <label>
          Período{" "}
          <select
            value={datos.periodo}
            onChange={(e) => cambiar("periodo", e.target.value)}
          >
            {datos.periodos.map((o) => (
              <option key={o.clave} value={o.clave}>
                {o.etiqueta}
              </option>
            ))}
          </select>
        </label>{" "}
        <label>
          Integrante{" "}
          <select
            value={integrante ?? ""}
            onChange={(e) => cambiar("integrante", e.target.value || null)}
          >
            <option value="">Todos</option>
            {(datos.franja[0]?.integrantes ?? []).map((i) => (
              <option key={i.estudiante_id} value={i.estudiante_id}>
                {i.nombre}
              </option>
            ))}
            <option value="sin_atribuir">Commits sin atribuir</option>
          </select>
        </label>
        <label>
          Rama
          <select
            aria-label="Rama"
            value={rama ?? ""}
            onChange={(e) => cambiar("rama", e.target.value || null)}
          >
            <option value="">Todas las ramas</option>
            {ramas.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
      </div>

      <section className="panel">
        <h2>Participación por tramo</h2>
        {datos.franja.map((t) => (
          <div key={t.periodo} style={{ marginBottom: "0.5rem" }}>
            <strong>{t.entrega}</strong>
            <ul>
              {t.integrantes.map((i) => (
                <li key={i.estudiante_id}>
                  {i.nombre}: {i.commits} commits · {i.dias_activos} días
                  activos
                  {i.causa && (
                    <span style={ESTILO_MOTIVO}>
                      {" "}
                      · {textoCausaParticipacion(i.causa)}
                    </span>
                  )}
                </li>
              ))}
              {t.sin_atribuir > 0 && (
                <li style={ESTILO_MOTIVO}>
                  sin atribuir: {t.sin_atribuir} commits
                </li>
              )}
            </ul>
          </div>
        ))}

        <p className="help">
          La coautoría puede hacer que la suma de los integrantes supere los
          commits del repositorio. Esta señal no mide la calidad del trabajo.
        </p>
      </section>
      <section className="panel">
        <h2>Historia</h2>
        {datos.dias.length === 0 ? (
          <p>No hay commits en este periodo.</p>
        ) : (
          <ul style={{ listStyle: "none", paddingLeft: 0 }}>
            {datos.dias.map((d) => {
              const clave = `${d.dia}-${d.hasta ?? ""}`;
              if (d.colapsado && !abiertos.has(clave)) {
                return (
                  <li key={clave} style={ESTILO_MOTIVO}>
                    <button
                      onClick={() => setAbiertos(new Set([...abiertos, clave]))}
                    >
                      {d.n_dias} días sin actividad ({diaLegible(d.dia)} →{" "}
                      {d.hasta ? diaLegible(d.hasta) : ""})
                    </button>
                  </li>
                );
              }
              return (
                <li key={clave}>
                  <strong>
                    {d.hasta
                      ? `${diaLegible(d.dia)} → ${diaLegible(d.hasta)}`
                      : diaLegible(d.dia)}
                  </strong>
                  <ul>
                    {d.commits.map((c) => (
                      <li key={c.sha}>
                        {c.url ? (
                          <a href={c.url} target="_blank" rel="noreferrer">
                            <code>{c.sha_corto}</code>
                          </a>
                        ) : (
                          <code>{c.sha_corto}</code>
                        )}{" "}
                        {c.mensaje || "Commit sin mensaje"} ·{" "}
                        {c.autor ?? "autor desconocido"}
                        <p className="help">
                          {fechaLegible(c.fecha, curso.zona_horaria)}
                          {c.rama && ` · rama ${c.rama}`}
                        </p>
                        {c.senal_debil && (
                          <span style={ESTILO_MOTIVO}>
                            {" "}
                            (atribución por correo, señal débil)
                          </span>
                        )}
                        {c.etiqueta_exclusion && (
                          <span style={ESTILO_MOTIVO}>
                            {" "}
                            ·{" "}
                            {EXCLUSION[c.etiqueta_exclusion] ??
                              c.etiqueta_exclusion}
                          </span>
                        )}
                        {c.posterior_al_cierre_de !== null && (
                          <span style={ESTILO_MOTIVO}>
                            {" "}
                            · posterior al cierre de la entrega{" "}
                            {c.posterior_al_cierre_de}
                          </span>
                        )}
                        {c.destacado && <strong> · {c.destacado}</strong>}{" "}
                        {puede("tarea.administrar") && (
                          <button
                            disabled={op.ocupado}
                            onClick={() => void onHito(c)}
                          >
                            {c.hito ? "Quitar hito" : "Marcar hito"}
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                </li>
              );
            })}
          </ul>
        )}
      </section>
      <section className="panel">
        <h2>Ciclo de vida</h2>
        <ul>
          {datos.ciclo_de_vida.map((e, i) => (
            <li key={i}>
              {fechaLegible(e.fecha, curso.zona_horaria)} ·{" "}
              {EVENTO[e.tipo] ?? e.tipo}
              {typeof e.detalle.estudiante === "string" &&
                ` · ${e.detalle.estudiante}`}
              {e.tipo === "HISTORIA_REESCRITA" &&
                ` · ${e.detalle.ref}: ${String(e.detalle.before).slice(0, 7)} → ${String(e.detalle.after).slice(0, 7)}, ${e.detalle.n_commits_huerfanos} commits huérfanos`}
            </li>
          ))}
        </ul>
      </section>
      <section className="panel">
        <h2>Entregas</h2>
        <ul>
          {datos.marcas_entrega.map((m) => (
            <li key={m.orden}>
              #{m.orden} {m.entrega}:{" "}
              {m.aplica
                ? m.fecha
                  ? fechaLegible(m.fecha, curso.zona_horaria)
                  : "sin fecha"
                : "no aplica"}
              {m.versiones.map((v) => (
                <span key={v.intento} style={{ opacity: v.vigente ? 1 : 0.6 }}>
                  {" "}
                  · v{v.intento}{" "}
                  {v.commit_sha ? (
                    <code>{v.commit_sha.slice(0, 7)}</code>
                  ) : (
                    textoEstadoCaptura(v.estado)
                  )}
                  {!v.vigente &&
                    v.motivo &&
                    ` (${textoMotivoVersion(v.motivo)})`}
                </span>
              ))}
            </li>
          ))}
        </ul>
      </section>
      {datos.composicion.length > 0 && (
        <>
          <h2>Composición del grupo</h2>
          <ul>
            {datos.composicion.map((c, i) => (
              <li key={i}>
                {c.estudiante
                  ? `${c.estudiante}: desde ${fechaLegible(c.desde, curso.zona_horaria)}${c.hasta ? ` hasta ${fechaLegible(c.hasta, curso.zona_horaria)}` : ""}`
                  : `Fuera del alcance de la tarea desde ${fechaLegible(c.sujeto_fuera_de_alcance, curso.zona_horaria)}`}
              </li>
            ))}
          </ul>
        </>
      )}

      <Identidades
        cursoId={cursoId}
        tareaId={tareaId}
        repoId={repoId}
        onCambio={consulta.recargar}
      />
    </div>
  );
}

function Identidades({
  cursoId,
  tareaId,
  repoId,
  onCambio,
}: {
  cursoId: string;
  tareaId: string;
  repoId: string;
  onCambio: () => void;
}) {
  const { puede } = useCurso();
  const edita = puede("mapeo.editar");
  const base = `/api/cursos/${cursoId}/tareas/${tareaId}/repos/${repoId}/identidades`;
  const consulta = useConsulta(`identidades-${base}`, (signal) =>
    consultarOperacion<IdentidadGit[]>(base, { signal }),
  );
  const [identidad, setIdentidad] = useState<IdentidadGit | null>(null);
  const [candidatos, setCandidatos] = useState<CandidatoPropagacion[]>([]);
  const [marcados, setMarcados] = useState<Set<string>>(new Set());
  const [revelados, setRevelados] = useState<Record<string, string>>({});
  const [estudiantes, setEstudiantes] = useState<EstudianteEspejo[]>([]);
  const [elegido, setElegido] = useState("");
  const [motivo, setMotivo] = useState("");
  const [noEstudiante, setNoEstudiante] = useState(false);
  const op = useOperacion();
  const confirmar = useConfirmar();
  async function preparar(i: IdentidadGit) {
    await op.ejecutar(async () => {
      const [personas, propagacion] = await Promise.all([
        obtenerPersonas(cursoId),
        consultarOperacion<CandidatoPropagacion[]>(
          `${base}/${i.id}/propagacion`,
        ),
      ]);
      setEstudiantes(personas.estudiantes);
      setCandidatos(propagacion);
      setIdentidad(i);
      setElegido("");
      setMotivo("");
      setNoEstudiante(false);
      setMarcados(new Set());
    });
  }
  async function resolver() {
    if (!identidad || !edita) return;
    const destino = noEstudiante
      ? "una persona ajena al curso"
      : estudiantes.find((e) => e.id === elegido)?.nombre;
    if (
      !(await confirmar({
        titulo: "Confirmar asociación de identidad",
        descripcion: `Se asociarán los commits de este correo a ${destino} en este repositorio${marcados.size ? ` y en ${marcados.size} repositorios seleccionados` : ""}. Se recalculará su participación.`,
        accion: "Confirmar asociación",
      }))
    )
      return;
    await op.ejecutar(async () => {
      const r = await resolverIdentidad(
        cursoId,
        tareaId,
        repoId,
        identidad.id,
        {
          ...(noEstudiante
            ? { no_es_estudiante: true }
            : { estudiante_id: elegido }),
          propagar_a: [...marcados],
          ...(motivo.trim() ? { confirmacion: motivo.trim() } : {}),
        },
      );
      if (!r.ok) throw new Error(r.error ?? "No se pudo asociar la identidad.");
      setIdentidad(null);
      consulta.recargar();
      onCambio();
    }, "Identidad asociada. La participación se actualizará con esta atribución.");
  }
  if (consulta.error)
    return <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />;
  if (!consulta.datos)
    return <Cargando texto="Consultando identidades de Git…" />;
  if (!consulta.datos.length) return null;
  return (
    <section className="panel">
      <h2>Identidades de Git</h2>
      <p className="help">
        Los correos permanecen ocultos hasta que solicites verlos. Úsalos para
        resolver la atribución de commits; pueden pertenecer a personas ajenas
        al curso.
      </p>
      <Mensajes {...op} />
      {!edita && (
        <Aviso>
          Necesitas permiso para editar el mapeo para revelar correos o asociar
          identidades. Puedes consultar su estado.
        </Aviso>
      )}
      <Tabla etiqueta="Identidades registradas en los commits">
        <table>
          <thead>
            <tr>
              <th>Identidad</th>
              <th>Atribución</th>
              <th>Commits</th>
              {edita && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {consulta.datos.map((i) => (
              <tr key={i.id}>
                <td>
                  <code>{revelados[i.id] ?? i.email ?? "Correo oculto"}</code>
                  <p className="help">{i.nombre_visto ?? "Sin nombre"}</p>
                </td>
                <td>
                  {i.estudiante ??
                    (i.estado === "NO_ES_ESTUDIANTE"
                      ? "No es un estudiante"
                      : "Sin atribuir")}
                </td>
                <td>{i.commits_contables}</td>
                {edita && (
                  <td>
                    <div className="actions">
                      <button
                        disabled={op.ocupado || Boolean(revelados[i.id])}
                        onClick={() =>
                          void op.ejecutar(async () => {
                            const r = await consultarOperacion<{
                              email: string;
                            }>(`${base}/${i.id}/revelar`, { method: "POST" });
                            setRevelados((actual) => ({
                              ...actual,
                              [i.id]: r.email,
                            }));
                          })
                        }
                      >
                        Revelar correo
                      </button>
                      <button
                        disabled={op.ocupado}
                        onClick={() => void preparar(i)}
                      >
                        Asociar identidad
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </Tabla>
      {identidad && edita && (
        <form
          className="form-stack"
          onSubmit={(e) => {
            e.preventDefault();
            void resolver();
          }}
        >
          <h3>
            Asociar {identidad.nombre_visto ?? identidad.email ?? "identidad"}
          </h3>
          <label>
            <input
              type="checkbox"
              checked={noEstudiante}
              onChange={(e) => setNoEstudiante(e.target.checked)}
            />{" "}
            No es un estudiante del curso
          </label>
          {!noEstudiante && (
            <label>
              Estudiante
              <select
                aria-label="Estudiante"
                required
                value={elegido}
                onChange={(e) => setElegido(e.target.value)}
              >
                <option value="">Elige un estudiante</option>
                {estudiantes.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.nombre}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label>
            Motivo de la asociación (obligatorio al reemplazar una existente)
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              required={Boolean(identidad.estudiante)}
              minLength={10}
              rows={2}
            />
          </label>
          <h3>Vista previa de propagación</h3>
          <p className="help">
            El mismo correo puede ser compartido por personas distintas.
            Selecciona explícitamente los repositorios que corresponden.
          </p>
          {candidatos.length ? (
            candidatos
              .filter((c) => c.repositorio_id !== repoId)
              .map((c) => (
                <label key={c.repositorio_id}>
                  <input
                    type="checkbox"
                    checked={marcados.has(c.repositorio_id)}
                    onChange={(e) =>
                      setMarcados((actual) => {
                        const nuevos = new Set(actual);
                        if (e.target.checked) nuevos.add(c.repositorio_id);
                        else nuevos.delete(c.repositorio_id);
                        return nuevos;
                      })
                    }
                  />{" "}
                  {c.repositorio} · {c.commits} commits ·{" "}
                  {c.nombre_visto ?? "Sin nombre"}
                </label>
              ))
          ) : (
            <Vacio>No se encontraron otros repositorios con este correo.</Vacio>
          )}
          <p>
            Se aplicará al repositorio actual y a {marcados.size} adicionales.
          </p>
          <div className="actions">
            <button
              className="primary"
              disabled={op.ocupado || (!noEstudiante && !elegido)}
            >
              Revisar y asociar
            </button>
            <button
              type="button"
              disabled={op.ocupado}
              onClick={() => setIdentidad(null)}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
