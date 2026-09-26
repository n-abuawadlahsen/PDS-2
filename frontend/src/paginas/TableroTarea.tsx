import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { actualizarTablero, obtenerTablero, urlApi, type FilaTablero, type Tablero } from "../lib/api";
import { textoEstadoEntregaAgregado, textoCausaParticipacion } from "../lib/textosTarea";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;
const ESTILO_TARJETA = { border: "1px solid #ddd", padding: "0.5rem 0.75rem", minWidth: "11rem" } as const;
const ESTILO_AMBAR = { background: "#fff3cd", padding: "0.5rem 0.75rem" } as const;

const GRUPOS_ESTADO: Record<string, string> = {
  LISTOS: "Listos",
  FUNCIONANDO_INCOMPLETO: "Funcionando, incompleto",
  FALTA_INFORMACION: "Falta información",
  EN_CURSO: "En curso",
  ESPERANDO: "Esperando",
  REQUIERE_ACCION: "Requiere acción",
  FUERA_DE_ALCANCE: "Fuera de alcance",
  ARCHIVADO: "Archivado",
  INACCESIBLE: "Inaccesible",
};

/** Tablero de la tarea (SPEC 10 S10.7): una sola página de cinco bloques,
 * pintada del espejo. El periodo y los filtros viajan en la URL. */
export function TableroTarea({ cursoId, tareaId }: { cursoId: string; tareaId: string }) {
  const [parametros, setParametros] = useSearchParams();
  const [datos, setDatos] = useState<Tablero | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const periodo = parametros.get("periodo") ?? undefined;
  const seccion = parametros.get("seccion") ?? undefined;
  const grupoEstado = parametros.get("grupo_estado") ?? undefined;
  const soloAlertas = parametros.get("solo_alertas") === "1";

  async function cargar() {
    setDatos(await obtenerTablero(cursoId, tareaId, { periodo, seccion, grupoEstado, soloAlertas }));
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId, tareaId, periodo, seccion, grupoEstado, soloAlertas]);

  function cambiar(clave: string, valor: string | null) {
    const nuevos = new URLSearchParams(parametros);
    if (valor) nuevos.set(clave, valor);
    else nuevos.delete(clave);
    setParametros(nuevos, { replace: true });
  }

  async function onActualizar() {
    const r = await actualizarTablero(cursoId, tareaId);
    setMensaje(
      r.encolada
        ? "Actualización en curso: los datos llegan en unos minutos."
        : `Ya hay una actualización reciente; podrás pedir otra a las ${new Date(r.disponible_en).toLocaleTimeString()}.`,
    );
  }

  if (!datos) return <p>Cargando tablero…</p>;
  const p = datos.procedencia;
  const t = datos.tarjetas;
  const participacion = Object.entries(t.sin_participacion);
  return (
    <section>
      <h2>Tablero</h2>
      <p style={ESTILO_MOTIVO}>
        Datos del espejo · última ingesta {p.ultima_ingesta ? new Date(p.ultima_ingesta).toLocaleString() : "—"} ·
        última reconciliación {p.ultima_reconciliacion ? new Date(p.ultima_reconciliacion).toLocaleString() : "—"} ·
        0 llamadas externas en esta vista · render {p.render_ms} ms
      </p>
      {p.datos_posiblemente_desactualizados && (
        <p style={ESTILO_AMBAR}>
          Los datos de actividad pueden estar desactualizados: no hay una lectura correcta en la última hora.
        </p>
      )}
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
        <button onClick={onActualizar}>Actualizar ahora</button>{" "}
        <a href={urlApi(`/api/cursos/${cursoId}/tareas/${tareaId}/tablero.csv?periodo=${datos.periodo}`)}>
          Exportar CSV
        </a>
      </p>
      {mensaje && <p style={ESTILO_MOTIVO}>{mensaje}</p>}

      <h3>Entregas</h3>
      {datos.entregas.length === 0 ? (
        <p>Esta tarea todavía no tiene entregas vinculadas.</p>
      ) : (
        <ul>
          {datos.entregas.map((e) => (
            <li key={e.entrega_id}>
              <strong>
                #{e.orden} {e.nombre}
              </strong>{" "}
              · {textoEstadoEntregaAgregado(e.estado)} · {e.sujetos} sujetos · {e.versiones_registradas} versiones
              registradas
              {e.fechas_distintas > 1 && ` · ${e.fechas_distintas} fechas distintas`}
            </li>
          ))}
        </ul>
      )}

      <h3>Estado de los repositorios</h3>
      <p>
        Listos {datos.repositorios.operativos} · Funcionando, incompleto {datos.repositorios.degradados} · Falta
        información {datos.repositorios.esperando_informacion} · En curso{" "}
        {datos.repositorios.creando + datos.repositorios.listos_para_crear} · Esperando{" "}
        {datos.repositorios.error_transitorio + datos.repositorios.esperando_limite + datos.repositorios.bloqueados} ·
        Requiere acción {datos.repositorios.error_permanente}
        <span style={ESTILO_MOTIVO}>
          {" "}
          · Fuera de alcance {datos.repositorios.fuera_de_alcance} · Archivados {datos.repositorios.archivados} ·
          Inaccesibles {datos.repositorios.inaccesibles}
        </span>
      </p>

      <h3>Atención</h3>
      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        <div style={ESTILO_TARJETA}>
          <strong>Sin actividad reciente</strong>
          <div>
            {t.sin_actividad} de {t.repositorios_creados} repositorios creados
          </div>
          {t.sin_dato_suficiente > 0 && <div style={ESTILO_MOTIVO}>{t.sin_dato_suficiente} sin dato suficiente</div>}
          {t.sin_datos_todavia > 0 && <div style={ESTILO_MOTIVO}>{t.sin_datos_todavia} sin datos todavía</div>}
        </div>
        <div style={ESTILO_TARJETA}>
          <strong>Sin participación</strong>
          {participacion.length === 0 ? (
            <div>Nadie</div>
          ) : (
            participacion.map(([causa, n]) => (
              <div key={causa}>
                {textoCausaParticipacion(causa)}: {n}
              </div>
            ))
          )}
          <div style={ESTILO_MOTIVO}>{datos.aviso_alcance}</div>
        </div>
        <div style={ESTILO_TARJETA}>
          <strong>Invitaciones sin aceptar</strong>
          <div>{t.invitaciones_sin_aceptar}</div>
        </div>
        <div style={ESTILO_TARJETA}>
          <strong>Incidencias bloqueantes</strong>
          <div>{t.bloqueantes}</div>
        </div>
      </div>

      <h3>Actividad en el tiempo</h3>
      {datos.serie.length === 0 ? (
        <p>Sin datos todavía para este periodo.</p>
      ) : (
        <Barras serie={datos.serie} cierres={datos.cierres} />
      )}
      {datos.histograma_previo_al_cierre.length > 0 && (
        <p style={ESTILO_MOTIVO}>
          Últimos 14 días antes del cierre:{" "}
          {datos.histograma_previo_al_cierre.map((d) => d.commits).join(" · ")}
          {datos.progreso_frente_al_cierre !== null &&
            ` · ${datos.progreso_frente_al_cierre}% de los sujetos con commits en las 48 h previas a su cierre`}
        </p>
      )}
      <p style={ESTILO_MOTIVO}>{datos.definicion_commit_contable}</p>

      <h3>Detalle por repositorio</h3>
      {datos.posicion_frente_al_curso && datos.posicion_frente_al_curso.commits && (
        <p>
          Posición frente al curso ({datos.posicion_frente_al_curso.sujetos} sujetos): commits en el periodo, cuartiles{" "}
          {datos.posicion_frente_al_curso.commits.join(" / ")}; días activos{" "}
          {datos.posicion_frente_al_curso.dias_activos?.join(" / ")}. Mediana por sección:{" "}
          {Object.entries(datos.posicion_frente_al_curso.mediana_por_seccion)
            .map(([s, m]) => `${s} ${m}`)
            .join(" · ")}
          {datos.posicion_frente_al_curso.excluidos > 0 &&
            ` · ${datos.posicion_frente_al_curso.excluidos} excluidos (sin fecha para esta entrega o retirados)`}
        </p>
      )}
      <p>
        <label>
          Estado{" "}
          <select value={grupoEstado ?? ""} onChange={(e) => cambiar("grupo_estado", e.target.value || null)}>
            <option value="">Todos</option>
            {Object.entries(GRUPOS_ESTADO).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>{" "}
        <label>
          <input
            type="checkbox"
            checked={soloAlertas}
            onChange={(e) => cambiar("solo_alertas", e.target.checked ? "1" : null)}
          />{" "}
          solo con alertas
        </label>
      </p>
      <table>
        <thead>
          <tr>
            <th>Sujeto</th>
            <th>Estado</th>
            <th>Commits en el periodo</th>
            <th>Días desde el último commit</th>
            <th>30 días</th>
            <th>Alertas</th>
          </tr>
        </thead>
        <tbody>
          {datos.filas.map((f) => (
            <Fila key={f.repositorio_id} fila={f} />
          ))}
        </tbody>
      </table>
      {datos.total_filas > datos.filas.length && (
        <p style={ESTILO_MOTIVO}>
          Mostrando {datos.filas.length} de {datos.total_filas} repositorios.
        </p>
      )}
    </section>
  );
}

function Fila({ fila: f }: { fila: FilaTablero }) {
  const [abierta, setAbierta] = useState(false);
  return (
    <>
      <tr>
        <td>
          {f.sujeto}
          {f.seccion && <div style={ESTILO_MOTIVO}>{f.seccion}</div>}
        </td>
        <td>{GRUPOS_ESTADO[f.grupo_estado] ?? f.grupo_estado}</td>
        <td>
          {f.no_aplica ? (
            <span style={ESTILO_MOTIVO}>Esta entrega no aplica a este sujeto</span>
          ) : (
            f.commits_periodo
          )}
          {f.commits_sin_atribuir > 0 && <div style={ESTILO_MOTIVO}>{f.commits_sin_atribuir} sin atribuir</div>}
        </td>
        <td>
          {f.actividad === "SIN_DATOS_TODAVIA"
            ? "sin datos todavía"
            : f.actividad === "SIN_DATO_SUFICIENTE"
              ? `sin dato suficiente: se observan ${f.dias_observados} días de los ${f.umbral_dias} que exige el umbral`
              : (f.dias_desde_ultimo_commit ?? "sin actividad desde su creación")}
        </td>
        <td>
          <Sparkline valores={f.sparkline} />
        </td>
        <td>
          {f.alertas.map((a) => (
            <div key={a}>{a === "SIN_ACTIVIDAD" ? "sin actividad reciente" : "alguien sin participación"}</div>
          ))}
          {f.reparto_concentrado && <div style={{ color: "#8a6d00" }}>reparto concentrado</div>}
          <button style={{ fontSize: "0.8rem" }} onClick={() => setAbierta(!abierta)}>
            {abierta ? "Ocultar" : f.sujeto_tipo === "GRUPO" ? "Comparar integrantes" : "Ver detalle"}
          </button>
        </td>
      </tr>
      {abierta && (
        <tr>
          <td colSpan={6}>
            <table>
              <thead>
                <tr>
                  <th>Integrante</th>
                  <th>Commits</th>
                  <th>Días activos</th>
                  <th>Líneas añadidas</th>
                  <th>Líneas eliminadas</th>
                </tr>
              </thead>
              <tbody>
                {f.integrantes.map((i) => (
                  <tr key={i.estudiante_id}>
                    <td>
                      {i.nombre}
                      {i.retirado && <span style={ESTILO_MOTIVO}> (retirado)</span>}
                      {i.salio_del_grupo && (
                        <span style={ESTILO_MOTIVO}> (salió el {new Date(i.salio_del_grupo).toLocaleDateString()})</span>
                      )}
                    </td>
                    <td>
                      {i.commits}
                      {i.causa && <span style={ESTILO_MOTIVO}> · {textoCausaParticipacion(i.causa)}</span>}
                    </td>
                    <td>{i.dias_activos}</td>
                    <td>{i.adiciones ?? "no disponible"}</td>
                    <td>{i.eliminaciones ?? "no disponible"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {f.commits_sin_atribuir > 0 && (
              <p style={ESTILO_MOTIVO}>
                Commits sin atribuir en este repositorio: {f.commits_sin_atribuir}. Hay actividad sin autor reconocido;
                la comparación puede estar incompleta.
              </p>
            )}
            {f.sujeto_tipo === "GRUPO" && (
              <p style={ESTILO_MOTIVO}>
                Índice de desequilibrio:{" "}
                {f.indice_desequilibrio === null ? "no calculable" : `${f.indice_desequilibrio}%`}. Esto no evalúa la
                calidad ni la justicia del reparto, y no cuenta líneas de código; es una señal para mirar el timeline
                del grupo.
              </p>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

function Sparkline({ valores }: { valores: number[] }) {
  const maximo = Math.max(1, ...valores);
  const puntos = valores.map((v, i) => `${(i * 60) / (valores.length - 1)},${18 - (v / maximo) * 16}`).join(" ");
  return (
    <svg width={60} height={20} role="img" aria-label={`máximo ${Math.max(...valores)} commits en un día`}>
      <polyline points={puntos} fill="none" stroke="#4a6fa5" strokeWidth={1.2} />
    </svg>
  );
}

function Barras({ serie, cierres }: { serie: { dia: string; commits: number }[]; cierres: string[] }) {
  const ancho = 640;
  const alto = 120;
  const maximo = Math.max(1, ...serie.map((d) => d.commits));
  const paso = ancho / serie.length;
  const diasCierre = new Set(cierres.map((c) => c.slice(0, 10)));
  return (
    <svg width="100%" viewBox={`0 0 ${ancho} ${alto + 16}`} role="img" aria-label="commits contables por día">
      {serie.map((d, i) => {
        const h = (d.commits / maximo) * alto;
        return (
          <g key={d.dia}>
            <rect x={i * paso + 1} y={alto - h} width={Math.max(1, paso - 2)} height={h} fill="#4a6fa5">
              <title>
                {d.dia}: {d.commits} commits
              </title>
            </rect>
            {diasCierre.has(d.dia) && (
              <line x1={i * paso + paso / 2} x2={i * paso + paso / 2} y1={0} y2={alto} stroke="#c0392b" />
            )}
          </g>
        );
      })}
      <text x={0} y={alto + 14} fontSize={10}>
        {serie[0]?.dia}
      </text>
      <text x={ancho} y={alto + 14} fontSize={10} textAnchor="end">
        {serie[serie.length - 1]?.dia}
      </text>
    </svg>
  );
}
