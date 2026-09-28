import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  desmarcarHito,
  listarIdentidades,
  marcarHito,
  obtenerPersonas,
  obtenerPropagacion,
  obtenerTimeline,
  resolverIdentidad,
  revelarIdentidad,
  type CandidatoPropagacion,
  type CommitTimeline,
  type EstudianteEspejo,
  type IdentidadGit,
  type Timeline,
} from "../lib/api";
import { textoCausaParticipacion } from "../lib/textosTarea";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "var(--color-text-secondary)" } as const;
const ESTILO_AMBAR = { background: "var(--color-warning-background)", padding: "0.5rem 0.75rem" } as const;

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
  SIN_DATOS_TODAVIA: "Sin datos todavía: el repositorio aún no tuvo su primera lectura completa.",
  SIN_ACCESO: "Sin actividad: el estudiante no ha aceptado su invitación.",
  SIN_ATRIBUIR: "Hay commits sin atribuir: puede haber trabajado con otro correo de Git.",
  SIN_COMMITS: "Sin actividad: no hay commits contables en este repositorio.",
};

/** Timeline del repositorio (SPEC 10 S10.9): cuatro capas en un eje de días
 * del curso. Periodo, integrante y rama viajan en la URL. */
export function RepositorioTimeline() {
  const { cursoId, tareaId, repoId } = useParams<{ cursoId: string; tareaId: string; repoId: string }>();
  const [parametros, setParametros] = useSearchParams();
  const [datos, setDatos] = useState<Timeline | null>(null);
  const [abiertos, setAbiertos] = useState<Set<string>>(new Set());
  const periodo = parametros.get("periodo") ?? undefined;
  const integrante = parametros.get("integrante") ?? undefined;

  async function cargar() {
    if (!cursoId || !tareaId || !repoId) return;
    setDatos(await obtenerTimeline(cursoId, tareaId, repoId, { periodo, integrante }));
  }

  useEffect(() => {
    cargar();
  }, [cursoId, tareaId, repoId, periodo, integrante]);

  function cambiar(clave: string, valor: string | null) {
    const nuevos = new URLSearchParams(parametros);
    if (valor) nuevos.set(clave, valor);
    else nuevos.delete(clave);
    setParametros(nuevos, { replace: true });
  }

  async function onHito(c: CommitTimeline) {
    if (!cursoId || !tareaId || !repoId) return;
    if (c.hito) {
      await desmarcarHito(cursoId, tareaId, repoId, c.sha);
    } else {
      const nota = window.prompt("Nota del hito (hasta 140 caracteres)");
      if (!nota) return;
      await marcarHito(cursoId, tareaId, repoId, c.sha, nota.slice(0, 140));
    }
    await cargar();
  }

  if (!cursoId || !tareaId || !repoId || !datos) return <p>Cargando…</p>;
  return (
    <main>
      <p>
        <Link to={`/cursos/${cursoId}/tareas/${tareaId}`}>← Tarea</Link>
      </p>
      <h1>
        {datos.sujeto} · <code>{datos.repositorio.nombre}</code>
      </h1>
      <p style={ESTILO_MOTIVO}>Datos del espejo · 0 llamadas externas en esta vista</p>
      {datos.enlaces.motivo && <p style={ESTILO_AMBAR}>{datos.enlaces.motivo}</p>}
      {datos.sin_commits_contables && datos.causa_vacia && <p style={ESTILO_AMBAR}>{CAUSA_VACIA[datos.causa_vacia]}</p>}
      <p>
        <label>
          Periodo{" "}
          <select value={datos.periodo} onChange={(e) => cambiar("periodo", e.target.value)}>
            {datos.periodos.map((o) => (
              <option key={o.clave} value={o.clave}>
                {o.etiqueta}
              </option>
            ))}
          </select>
        </label>{" "}
        <label>
          Integrante{" "}
          <select value={integrante ?? ""} onChange={(e) => cambiar("integrante", e.target.value || null)}>
            <option value="">Todos</option>
            {(datos.franja[0]?.integrantes ?? []).map((i) => (
              <option key={i.estudiante_id} value={i.estudiante_id}>
                {i.nombre}
              </option>
            ))}
            <option value="sin_atribuir">Commits sin atribuir</option>
          </select>
        </label>
      </p>

      <h2>Participación por tramo</h2>
      {datos.franja.map((t) => (
        <div key={t.periodo} style={{ marginBottom: "0.5rem" }}>
          <strong>{t.entrega}</strong>
          <ul>
            {t.integrantes.map((i) => (
              <li key={i.nombre}>
                {i.nombre}: {i.commits} commits · {i.dias_activos} días activos
                {i.causa && <span style={ESTILO_MOTIVO}> · {textoCausaParticipacion(i.causa)}</span>}
              </li>
            ))}
            {t.sin_atribuir > 0 && <li style={ESTILO_MOTIVO}>sin atribuir: {t.sin_atribuir} commits</li>}
          </ul>
        </div>
      ))}

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
                  <button onClick={() => setAbiertos(new Set([...abiertos, clave]))}>
                    {d.n_dias} días sin actividad ({d.dia} → {d.hasta})
                  </button>
                </li>
              );
            }
            return (
              <li key={clave}>
                <strong>{d.hasta ? `${d.dia} → ${d.hasta}` : d.dia}</strong>
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
                      {c.mensaje} · {c.autor ?? "autor desconocido"}
                      {c.senal_debil && <span style={ESTILO_MOTIVO}> (atribución por correo, señal débil)</span>}
                      {c.etiqueta_exclusion && (
                        <span style={ESTILO_MOTIVO}> · {EXCLUSION[c.etiqueta_exclusion] ?? c.etiqueta_exclusion}</span>
                      )}
                      {c.posterior_al_cierre_de !== null && (
                        <span style={ESTILO_MOTIVO}> · posterior al cierre de la entrega {c.posterior_al_cierre_de}</span>
                      )}
                      {c.destacado && <strong> · {c.destacado}</strong>}{" "}
                      <button style={{ fontSize: "0.75rem" }} onClick={() => onHito(c)}>
                        {c.hito ? "Quitar hito" : "Marcar hito"}
                      </button>
                    </li>
                  ))}
                </ul>
              </li>
            );
          })}
        </ul>
      )}

      <h2>Ciclo de vida</h2>
      <ul>
        {datos.ciclo_de_vida.map((e, i) => (
          <li key={i}>
            {new Date(e.fecha).toLocaleString()} · {EVENTO[e.tipo] ?? e.tipo}
            {e.detalle.estudiante && ` · ${e.detalle.estudiante}`}
            {e.tipo === "HISTORIA_REESCRITA" &&
              ` · ${e.detalle.ref}: ${String(e.detalle.before).slice(0, 7)} → ${String(e.detalle.after).slice(0, 7)}, ${e.detalle.n_commits_huerfanos} commits huérfanos`}
          </li>
        ))}
      </ul>

      <h2>Entregas</h2>
      <ul>
        {datos.marcas_entrega.map((m) => (
          <li key={m.orden}>
            #{m.orden} {m.entrega}: {m.aplica ? (m.fecha ? new Date(m.fecha).toLocaleString() : "sin fecha") : "no aplica"}
            {m.versiones.map((v) => (
              <span key={v.intento} style={{ opacity: v.vigente ? 1 : 0.6 }}>
                {" "}
                · v{v.intento} {v.commit_sha ? <code>{v.commit_sha.slice(0, 7)}</code> : v.estado}
                {!v.vigente && v.motivo && ` (${v.motivo.toLowerCase().replaceAll("_", " ")})`}
              </span>
            ))}
          </li>
        ))}
      </ul>

      {datos.composicion.length > 0 && (
        <>
          <h2>Composición del grupo</h2>
          <ul>
            {datos.composicion.map((c, i) => (
              <li key={i}>
                {c.estudiante
                  ? `${c.estudiante}: desde ${new Date(c.desde).toLocaleDateString()}${c.hasta ? ` hasta ${new Date(c.hasta).toLocaleDateString()}` : ""}`
                  : `Fuera del alcance de la tarea desde ${new Date(c.sujeto_fuera_de_alcance).toLocaleDateString()}`}
              </li>
            ))}
          </ul>
        </>
      )}

      <Identidades cursoId={cursoId} tareaId={tareaId} repoId={repoId} onCambio={cargar} />
    </main>
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
  const [lista, setLista] = useState<IdentidadGit[]>([]);
  const [candidatos, setCandidatos] = useState<Record<string, CandidatoPropagacion[]>>({});
  const [marcados, setMarcados] = useState<Set<string>>(new Set());
  const [revelados, setRevelados] = useState<Record<string, string>>({});
  const [estudiantes, setEstudiantes] = useState<EstudianteEspejo[]>([]);
  const [elegido, setElegido] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    setLista(await listarIdentidades(cursoId, tareaId, repoId));
  }

  async function resolver(identidadId: string, cuerpo: { estudiante_id?: string; no_es_estudiante?: boolean }) {
    let r = await resolverIdentidad(cursoId, tareaId, repoId, identidadId, { ...cuerpo, propagar_a: [...marcados] });
    if (!r.ok && r.error?.includes("Escribe por qué")) {
      const texto = window.prompt(r.error ?? "");
      if (!texto) return;
      r = await resolverIdentidad(cursoId, tareaId, repoId, identidadId, {
        ...cuerpo,
        propagar_a: [...marcados],
        confirmacion: texto,
      });
    }
    setError(r.ok ? null : r.error);
    await cargar();
    onCambio();
  }
  useEffect(() => {
    cargar();
  }, [cursoId, tareaId, repoId]);

  if (lista.length === 0) return null;
  return (
    <section>
      <h2>Correos sin atribuir</h2>
      <p style={ESTILO_MOTIVO}>
        Estos correos vienen de los commits y pueden pertenecer a personas ajenas al curso. Úsalos sólo para asociar
        una cuenta y no los compartas fuera de la aplicación.
      </p>
      {error && <p style={{ background: "var(--color-error-background)", padding: "0.5rem" }}>{error}</p>}
      <ul>
        {lista.map((i) => (
          <li key={i.id}>
            <code>{revelados[i.id] ?? i.email}</code> · {i.nombre_visto ?? "sin nombre"} · {i.commits_contables} commits
            {i.estudiante && ` · asociado a ${i.estudiante}`}{" "}
            <button
              style={{ fontSize: "0.75rem" }}
              onClick={async () => {
                const r = await revelarIdentidad(cursoId, tareaId, repoId, i.id);
                if (r) setRevelados({ ...revelados, [i.id]: r });
                else setError("Revelar el correo exige el permiso de editar cuentas de GitHub.");
              }}
            >
              Revelar
            </button>{" "}
            <button
              style={{ fontSize: "0.75rem" }}
              onClick={async () => {
                if (estudiantes.length === 0) setEstudiantes((await obtenerPersonas(cursoId)).estudiantes);
                setCandidatos({ ...candidatos, [i.id]: await obtenerPropagacion(cursoId, tareaId, repoId, i.id) });
              }}
            >
              Asociar
            </button>
            {candidatos[i.id] && (
              <div>
                <p style={ESTILO_MOTIVO}>
                  El mismo correo aparece en estos repositorios. Correos como root@localhost se repiten entre
                  estudiantes distintos: marca sólo los que correspondan.
                </p>
                {candidatos[i.id].map((c) => (
                  <label key={c.repositorio_id} style={{ display: "block" }}>
                    <input
                      type="checkbox"
                      checked={marcados.has(c.repositorio_id)}
                      onChange={(e) => {
                        const nuevo = new Set(marcados);
                        if (e.target.checked) nuevo.add(c.repositorio_id);
                        else nuevo.delete(c.repositorio_id);
                        setMarcados(nuevo);
                      }}
                    />{" "}
                    {c.repositorio} · {c.commits} commits
                  </label>
                ))}
                <select
                  value={elegido[i.id] ?? ""}
                  onChange={(e) => setElegido({ ...elegido, [i.id]: e.target.value })}
                >
                  <option value="">Elige un estudiante</option>
                  {estudiantes.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.nombre}
                    </option>
                  ))}
                </select>{" "}
                <button disabled={!elegido[i.id]} onClick={() => resolver(i.id, { estudiante_id: elegido[i.id] })}>
                  Asociar a un estudiante
                </button>{" "}
                <button onClick={() => resolver(i.id, { no_es_estudiante: true })}>
                  No es un estudiante
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
