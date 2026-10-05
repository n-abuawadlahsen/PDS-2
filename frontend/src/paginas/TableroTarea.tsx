import { useEffect, useId, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  obtenerPersonas,
  urlApi,
  type FilaTablero,
  type Tablero,
} from "../lib/api";
import { consultarOperacion, parametrosOperacion } from "../lib/apiOperacion";
import { useCurso } from "../components/Layout";
import { Cargando, ErrorCarga, Mensajes, Tabla, Vacio } from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import {
  fechaLegible,
  diaLegible,
  textoEstadoEntregaAgregado,
  textoCausaParticipacion,
  textoMotivoRepositorio,
} from "../lib/textosTarea";

import "../styles/operacion.css";

const ESTILO_MOTIVO = {
  fontSize: "0.85rem",
  color: "var(--color-text-secondary)",
} as const;
const ESTILO_AMBAR = {
  background: "var(--color-warning-background)",
  padding: "0.5rem 0.75rem",
} as const;

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
export function TableroTarea({
  cursoId,
  tareaId,
}: {
  cursoId: string;
  tareaId: string;
}) {
  const [parametros, setParametros] = useSearchParams();
  const { curso } = useCurso();
  const op = useOperacion();
  const [disponibleEn, setDisponibleEn] = useState<string | null>(null);
  const [actualizando, setActualizando] = useState(false);
  const [espera, setEspera] = useState(false);
  const personas = useConsulta(`secciones-tablero-${cursoId}`, (signal) =>
    obtenerPersonas(cursoId, signal),
  );
  const periodo = parametros.get("periodo") ?? undefined;
  const seccion = parametros.get("seccion") ?? undefined;
  const grupoEstado = parametros.get("grupo_estado") ?? undefined;
  const soloAlertas = parametros.get("solo_alertas") === "1";

  const pagina = Math.max(1, Number(parametros.get("pagina")) || 1);
  const filtros = parametrosOperacion({
    periodo,
    seccion,
    grupo_estado: grupoEstado,
    solo_alertas: soloAlertas,
    pagina,
  });
  const consulta = useConsulta(
    `tablero-${cursoId}-${tareaId}-${filtros}`,
    (signal) =>
      consultarOperacion<Tablero>(
        `/api/cursos/${cursoId}/tareas/${tareaId}/tablero?${filtros}`,
        { signal },
      ),
    actualizando ? 10_000 : 0,
  );
  const datos = consulta.datos;
  useEffect(() => {
    if (!disponibleEn) return;
    setEspera(true);
    const tiempo = setTimeout(
      () => {
        setEspera(false);
        setActualizando(false);
      },
      Math.max(0, new Date(disponibleEn).getTime() - Date.now()),
    );
    return () => clearTimeout(tiempo);
  }, [disponibleEn]);

  function cambiar(clave: string, valor: string | null) {
    const nuevos = new URLSearchParams(parametros);
    if (clave !== "pagina") nuevos.delete("pagina");
    if (valor) nuevos.set(clave, valor);
    else nuevos.delete(clave);
    setParametros(nuevos, { replace: true });
  }

  async function onActualizar() {
    await op.ejecutar(async () => {
      const r = await consultarOperacion<{
        encolada: boolean;
        en_curso: boolean;
        disponible_en: string;
      }>(`/api/cursos/${cursoId}/tareas/${tareaId}/tablero/actualizar`, {
        method: "POST",
      });
      setDisponibleEn(r.disponible_en);
      setActualizando(r.encolada || r.en_curso);
      op.setMensaje(
        r.encolada || r.en_curso
          ? "Actualización solicitada. Puedes seguir consultando los datos mientras llegan los nuevos."
          : `Ya hay una actualización reciente. Disponible el ${fechaLegible(r.disponible_en, curso.zona_horaria)}.`,
      );
    });
  }

  if (!datos)
    return consulta.error ? (
      <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
    ) : (
      <Cargando texto="Cargando tablero…" />
    );
  const p = datos.procedencia;
  const t = datos.tarjetas;
  const participacion = Object.entries(t.sin_participacion);
  return (
    <section className="operacion-tablero">
      <h2>Tablero</h2>
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      <p className="help">
        Datos actualizados: {fechaLegible(p.ultima_ingesta, curso.zona_horaria)}{" "}
        · última comprobación:{" "}
        {fechaLegible(p.ultima_reconciliacion, curso.zona_horaria)}
      </p>
      {p.datos_posiblemente_desactualizados && (
        <p style={ESTILO_AMBAR}>
          Los datos de actividad pueden estar desactualizados: no hay una
          lectura correcta en la última hora.
        </p>
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
        <button
          disabled={op.ocupado || espera}
          onClick={() => void onActualizar()}
        >
          {op.ocupado
            ? "Solicitando…"
            : actualizando
              ? "Actualización en curso"
              : "Actualizar ahora"}
        </button>{" "}
        <a
          href={urlApi(
            `/api/cursos/${cursoId}/tareas/${tareaId}/tablero.csv?${parametrosOperacion({ periodo: datos.periodo, seccion: params.get("seccion") ?? "", grupo_estado: params.get("grupo_estado") ?? "", solo_alertas: params.get("solo_alertas") === "1" })}`,
          )}
        >
          Exportar resultados en CSV
        </a>
      </div>
      <Mensajes {...op} />
      {espera && disponibleEn && (
        <p className="help">
          Puedes solicitar otra actualización el{" "}
          {fechaLegible(disponibleEn, curso.zona_horaria)}.
        </p>
      )}
      <p className="help">
        El CSV contiene los resultados del período con los filtros de esta tabla, en todas las páginas.
      </p>

      <h3>Entregas</h3>
      {datos.entregas.length === 0 ? (
        <p>Esta tarea todavía no tiene entregas vinculadas.</p>
      ) : (
        <ul>
          {datos.entregas.map((e) => (
            <li key={e.entrega_id}>
              <Link
                to={`/cursos/${cursoId}/tareas/${tareaId}/entregas?entrega=${e.entrega_id}`}
              >
                #{e.orden} {e.nombre}
              </Link>{" "}
              · {textoEstadoEntregaAgregado(e.estado)} · {e.sujetos} sujetos ·{" "}
              {e.versiones_registradas} versiones registradas
              {e.fechas_distintas > 1 &&
                ` · ${e.fechas_distintas} fechas distintas`}
            </li>
          ))}
        </ul>
      )}

      <h3>Estado de los repositorios</h3>
      <dl className="operacion-estados">
        {[
          {
            nombre: "Listos",
            valor: datos.repositorios.operativos,
            tono: "success",
          },
          {
            nombre: "Accesos pendientes",
            valor: datos.repositorios.degradados,
            tono: "warning",
          },
          {
            nombre: "Falta información",
            valor: datos.repositorios.esperando_informacion,
            tono: "warning",
          },
          {
            nombre: "En curso",
            valor:
              datos.repositorios.creando + datos.repositorios.listos_para_crear,
            detalle: `${datos.repositorios.listos_para_crear} por crear · ${datos.repositorios.creando} creando`,
          },
          {
            nombre: "Esperando",
            valor:
              datos.repositorios.error_transitorio +
              datos.repositorios.esperando_limite +
              datos.repositorios.bloqueados,
            detalle: `${datos.repositorios.esperando_limite} por límite · ${datos.repositorios.bloqueados} bloqueados · ${datos.repositorios.error_transitorio} reintentando`,
          },
          {
            nombre: "Requieren acción",
            valor: datos.repositorios.error_permanente,
            tono: "error",
          },
          {
            nombre: "Fuera de alcance",
            valor: datos.repositorios.fuera_de_alcance,
          },
          { nombre: "Archivados", valor: datos.repositorios.archivados },
          {
            nombre: "Inaccesibles",
            valor: datos.repositorios.inaccesibles,
            tono: "error",
          },
        ].map((estado) => (
          <div
            key={estado.nombre}
            className={`operacion-estado ${estado.tono ?? "neutral"}`}
          >
            <dt>{estado.nombre}</dt>
            <dd>{estado.valor}</dd>
            {estado.detalle && (
              <dd className="operacion-estado-detalle">{estado.detalle}</dd>
            )}
          </div>
        ))}
      </dl>

      <details>
        <summary>Ver todos los estados de creación</summary>
        <dl className="operacion-subestados">
          {Object.entries({
            Operativos: datos.repositorios.operativos,
            "Accesos pendientes": datos.repositorios.degradados,
            "Esperando información": datos.repositorios.esperando_informacion,
            "Listos para crear": datos.repositorios.listos_para_crear,
            Creándose: datos.repositorios.creando,
            "Esperando límite de GitHub": datos.repositorios.esperando_limite,
            Bloqueados: datos.repositorios.bloqueados,
            "Reintento automático": datos.repositorios.error_transitorio,
            "Requieren acción": datos.repositorios.error_permanente,
            "Fuera de alcance": datos.repositorios.fuera_de_alcance,
            Archivados: datos.repositorios.archivados,
            Inaccesibles: datos.repositorios.inaccesibles,
          }).map(([nombre, cantidad]) => (
            <div key={nombre}>
              <dt>{nombre}</dt>
              <dd>{cantidad}</dd>
            </div>
          ))}
        </dl>
      </details>
      <h3>Atención</h3>
      <div className="operacion-atencion">
        <div className="operacion-alerta">
          <h4>Sin actividad reciente</h4>
          <p className="operacion-alerta-cantidad">
            {t.sin_actividad}
            <span>de {t.repositorios_creados} repositorios</span>
          </p>
          <p className="help">
            {t.sin_dato_suficiente > 0 &&
              `${t.sin_dato_suficiente} sin dato suficiente. `}
            {t.sin_datos_todavia > 0 &&
              `${t.sin_datos_todavia} sin datos todavía.`}
          </p>
          <button
            className="operacion-enlace"
            onClick={() => cambiar("solo_alertas", "1")}
          >
            Consultar alertas
          </button>
        </div>
        <div className="operacion-alerta">
          <h4>Participación por revisar</h4>
          {participacion.length === 0 ? (
            <p className="operacion-alerta-cantidad">
              0<span>sin casos pendientes</span>
            </p>
          ) : (
            <dl className="operacion-causas">
              {participacion.map(([causa, cantidad]) => (
                <div key={causa}>
                  <dt>
                    {(
                      {
                        SIN_ACCESO: "Sin acceso",
                        SIN_ATRIBUIR: "Sin atribuir",
                        SIN_COMMITS: "Sin commits",
                      } as Record<string, string>
                    )[causa] ?? textoCausaParticipacion(causa)}
                  </dt>
                  <dd>{cantidad}</dd>
                </div>
              ))}
            </dl>
          )}
          <Link to={`/cursos/${cursoId}/pendientes`}>Revisar las causas</Link>
        </div>
        <div className="operacion-alerta">
          <h4>Invitaciones sin aceptar</h4>
          <p className="operacion-alerta-cantidad">
            {t.invitaciones_sin_aceptar}
            <span>accesos pendientes</span>
          </p>
          <Link to="?vista=repositorios">Revisar accesos</Link>
        </div>
        <div className="operacion-alerta">
          <h4>Incidencias bloqueantes</h4>
          <p className="operacion-alerta-cantidad">
            {t.bloqueantes}
            <span>requieren atención</span>
          </p>
          <Link to={`/cursos/${cursoId}/pendientes`}>Revisar pendientes</Link>
        </div>
      </div>
      <p className="help operacion-alcance">{datos.aviso_alcance}</p>

      <h3>Actividad en el tiempo</h3>
      {datos.serie.length === 0 ? (
        <p>Sin datos todavía para este periodo.</p>
      ) : (
        <Barras
          serie={datos.serie}
          cierres={datos.cierres}
          zona={curso.zona_horaria}
        />
      )}
      <p className="help">
        Las barras muestran commits por día. Las líneas verticales señalan
        cierres de entrega.
      </p>
      <details>
        <summary>Consultar los valores diarios</summary>
        <Tabla etiqueta="Actividad diaria">
          <table>
            <thead>
              <tr>
                <th>Día del curso</th>
                <th>Commits</th>
              </tr>
            </thead>
            <tbody>
              {datos.serie.map((d) => (
                <tr key={d.dia}>
                  <td>{diaLegible(d.dia)}</td>
                  <td>{d.commits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Tabla>
      </details>
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
      {datos.posicion_frente_al_curso &&
        datos.posicion_frente_al_curso.commits && (
          <p>
            Posición frente al curso ({datos.posicion_frente_al_curso.sujetos}{" "}
            sujetos): commits en el periodo, cuartiles{" "}
            {datos.posicion_frente_al_curso.commits.join(" / ")}; días activos{" "}
            {datos.posicion_frente_al_curso.dias_activos?.join(" / ")}. Mediana
            por sección:{" "}
            {Object.entries(datos.posicion_frente_al_curso.mediana_por_seccion)
              .map(([s, m]) => `${s} ${m}`)
              .join(" · ")}
            {datos.posicion_frente_al_curso.excluidos > 0 &&
              ` · ${datos.posicion_frente_al_curso.excluidos} excluidos (sin fecha para esta entrega o retirados)`}
          </p>
        )}
      <div className="filters">
        <label>
          Sección
          <select
            aria-label="Sección"
            value={seccion ?? ""}
            onChange={(e) => cambiar("seccion", e.target.value || null)}
          >
            <option value="">Todas las secciones</option>
            {personas.datos?.secciones.map((s) => (
              <option key={s.id} value={s.nombre}>
                {s.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Estado{" "}
          <select
            value={grupoEstado ?? ""}
            onChange={(e) => cambiar("grupo_estado", e.target.value || null)}
          >
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
            onChange={(e) =>
              cambiar("solo_alertas", e.target.checked ? "1" : null)
            }
          />{" "}
          Solo con alertas
        </label>
      </div>
      {personas.error && (
        <ErrorCarga error={personas.error} reintentar={personas.recargar} />
      )}
      {datos.filas.length === 0 ? (
        <Vacio>
          No hay repositorios con estos filtros. Prueba otro estado o sección.
        </Vacio>
      ) : (
        <Tabla etiqueta="Detalle y comparación de repositorios">
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
                <Fila
                  key={f.repositorio_id}
                  fila={f}
                  zona={curso.zona_horaria}
                  enlace={`/cursos/${cursoId}/tareas/${tareaId}/repos/${f.repositorio_id}?${new URLSearchParams({ periodo: datos.periodo, retorno: parametros.toString() })}`}
                />
              ))}
            </tbody>
          </table>
        </Tabla>
      )}
      <div className="pagination" aria-label="Paginación de repositorios">
        <span>
          {datos.total_filas} repositorios · página {datos.pagina} de{" "}
          {Math.max(1, Math.ceil(datos.total_filas / 50))}
        </span>
        <button
          disabled={pagina <= 1 || consulta.cargando}
          onClick={() => cambiar("pagina", String(pagina - 1))}
        >
          Anterior
        </button>
        <button
          disabled={pagina * 50 >= datos.total_filas || consulta.cargando}
          onClick={() => cambiar("pagina", String(pagina + 1))}
        >
          Siguiente
        </button>
      </div>
    </section>
  );
}

function Fila({
  fila: f,
  enlace,
  zona,
}: {
  fila: FilaTablero;
  enlace: string;
  zona: string;
}) {
  const [abierta, setAbierta] = useState(false);
  return (
    <>
      <tr>
        <td>
          <Link to={enlace}>{f.sujeto}</Link>
          {f.seccion && <div style={ESTILO_MOTIVO}>{f.seccion}</div>}
        </td>
        <td>
          {GRUPOS_ESTADO[f.grupo_estado] ?? "En proceso"}
          {f.motivo && (
            <p className="help">{textoMotivoRepositorio(f.motivo)}</p>
          )}
        </td>
        <td>
          {f.no_aplica ? (
            <span style={ESTILO_MOTIVO}>
              Esta entrega no aplica a este sujeto
            </span>
          ) : (
            f.commits_periodo
          )}
          {f.commits_sin_atribuir > 0 && (
            <div style={ESTILO_MOTIVO}>
              {f.commits_sin_atribuir} sin atribuir
            </div>
          )}
        </td>
        <td>
          {f.actividad === "SIN_DATOS_TODAVIA"
            ? "sin datos todavía"
            : f.actividad === "SIN_DATO_SUFICIENTE"
              ? `sin dato suficiente: se observan ${f.dias_observados} días de los ${f.umbral_dias} que exige el umbral`
              : (f.dias_desde_ultimo_commit ??
                "sin actividad desde su creación")}
        </td>
        <td>
          <Sparkline valores={f.sparkline} />
        </td>
        <td>
          {f.alertas.map((a) => (
            <div key={a}>
              {a === "SIN_ACTIVIDAD"
                ? "sin actividad reciente"
                : "alguien sin participación"}
            </div>
          ))}
          {f.reparto_concentrado && (
            <div style={{ color: "var(--color-warning)" }}>
              reparto concentrado
            </div>
          )}
          <button aria-expanded={abierta} onClick={() => setAbierta(!abierta)}>
            {abierta
              ? "Ocultar"
              : f.sujeto_tipo === "GRUPO"
                ? "Comparar integrantes"
                : "Ver detalle"}
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
                      {i.retirado && (
                        <span style={ESTILO_MOTIVO}> (retirado)</span>
                      )}
                      {i.salio_del_grupo && (
                        <span style={ESTILO_MOTIVO}>
                          {" "}
                          (salió el {fechaLegible(i.salio_del_grupo, zona)})
                        </span>
                      )}
                    </td>
                    <td>
                      {i.commits}
                      {i.causa && (
                        <span style={ESTILO_MOTIVO}>
                          {" "}
                          · {textoCausaParticipacion(i.causa)}
                        </span>
                      )}
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
                Commits sin atribuir en este repositorio:{" "}
                {f.commits_sin_atribuir}. Hay actividad sin autor reconocido; la
                comparación puede estar incompleta.
              </p>
            )}
            {f.sujeto_tipo === "GRUPO" && (
              <p style={ESTILO_MOTIVO}>
                Un commit con coautores se atribuye a cada integrante; la suma
                puede superar el total del repositorio. Índice de desequilibrio:{" "}
                {f.indice_desequilibrio === null
                  ? "no calculable"
                  : `${f.indice_desequilibrio}%`}
                . Esto no evalúa la calidad ni la justicia del reparto, y no
                cuenta líneas de código; es una señal para mirar el timeline del
                grupo.
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
  const puntos = valores
    .map(
      (v, i) =>
        `${(i * 60) / Math.max(1, valores.length - 1)},${18 - (v / maximo) * 16}`,
    )
    .join(" ");
  return (
    <svg
      width={60}
      height={20}
      role="img"
      aria-label={`máximo ${Math.max(0, ...valores)} commits en un día`}
    >
      <polyline
        points={puntos}
        fill="none"
        stroke="var(--color-primary)"
        strokeWidth={1.2}
      />
    </svg>
  );
}

function Barras({
  serie,
  cierres,
  zona,
}: {
  serie: { dia: string; commits: number }[];
  cierres: string[];
  zona: string;
}) {
  const [activo, setActivo] = useState(0);
  const barras = useRef<(SVGGElement | null)[]>([]);
  const tooltipId = useId();
  const ancho = 720;
  const alto = 180;
  const margen = { izquierda: 44, derecha: 12, arriba: 20, abajo: 32 };
  const graficoAncho = ancho - margen.izquierda - margen.derecha;
  const graficoAlto = alto - margen.arriba - margen.abajo;
  const maximo = Math.max(
    4,
    Math.ceil(Math.max(...serie.map((d) => d.commits)) / 4) * 4,
  );
  const paso = graficoAncho / serie.length;
  const diasCierre = new Set(
    cierres.map((c) => {
      const partes = new Intl.DateTimeFormat("en-CA", {
        timeZone: zona,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }).formatToParts(new Date(c));
      const valor = (tipo: Intl.DateTimeFormatPartTypes) =>
        partes.find((parte) => parte.type === tipo)?.value;
      return `${valor("year")}-${valor("month")}-${valor("day")}`;
    }),
  );
  const marcas = [
    ...new Set([
      0,
      Math.floor((serie.length - 1) / 3),
      Math.floor((2 * (serie.length - 1)) / 3),
      serie.length - 1,
    ]),
  ];
  const seleccion = serie[Math.min(activo, serie.length - 1)];
  return (
    <figure className="operacion-grafico">
      <div className="operacion-leyenda">
        <span>
          <i className="operacion-leyenda-barra" aria-hidden="true" />
          Commits por día
        </span>
        <span>
          <i className="operacion-leyenda-cierre" aria-hidden="true" />
          Cierre de entrega
        </span>
        <span id={tooltipId} role="tooltip" className="operacion-tooltip">
          {diaLegible(seleccion.dia)} ·{" "}
          <strong>{seleccion.commits} commits</strong>
        </span>
      </div>
      <div
        className="operacion-grafico-scroll"
        role="region"
        aria-label="Gráfico de actividad con desplazamiento horizontal"
        tabIndex={0}
      >
        <svg
          viewBox={`0 0 ${ancho} ${alto}`}
          role="group"
          aria-label="Actividad diaria. Usa las flechas para consultar los días."
          className="operacion-barras"
        >
          <text x={margen.izquierda} y={11} className="operacion-eje-titulo">
            Commits
          </text>
          {[0, 1, 2, 3, 4].map((n) => {
            const y = margen.arriba + graficoAlto - (n * graficoAlto) / 4;
            return (
              <g key={n} aria-hidden="true">
                <line
                  x1={margen.izquierda}
                  x2={ancho - margen.derecha}
                  y1={y}
                  y2={y}
                  className="operacion-grilla"
                />
                <text
                  x={margen.izquierda - 10}
                  y={y + 4}
                  textAnchor="end"
                  className="operacion-eje"
                >
                  {(maximo * n) / 4}
                </text>
              </g>
            );
          })}
          {serie.map((d, i) => {
            const altura = (d.commits / maximo) * graficoAlto;
            const x = margen.izquierda + i * paso;
            return (
              <g
                key={d.dia}
                ref={(nodo) => {
                  barras.current[i] = nodo;
                }}
                tabIndex={i === Math.min(activo, serie.length - 1) ? 0 : -1}
                role="img"
                aria-label={`${diaLegible(d.dia)}: ${d.commits} commits${diasCierre.has(d.dia) ? ", cierre de entrega" : ""}`}
                aria-describedby={tooltipId}
                className={`operacion-barra ${activo === i ? "seleccionada" : ""}`}
                onMouseEnter={() => setActivo(i)}
                onFocus={() => setActivo(i)}
                onKeyDown={(e) => {
                  const siguiente =
                    e.key === "ArrowRight"
                      ? Math.min(i + 1, serie.length - 1)
                      : e.key === "ArrowLeft"
                        ? Math.max(i - 1, 0)
                        : e.key === "Home"
                          ? 0
                          : e.key === "End"
                            ? serie.length - 1
                            : null;
                  if (siguiente !== null) {
                    e.preventDefault();
                    setActivo(siguiente);
                    barras.current[siguiente]?.focus();
                  }
                }}
              >
                <title>
                  {diaLegible(d.dia)}: {d.commits} commits
                </title>
                <rect
                  x={x}
                  y={margen.arriba}
                  width={paso}
                  height={graficoAlto}
                  className="operacion-barra-area"
                />
                <rect
                  x={x + 2}
                  y={margen.arriba + graficoAlto - altura}
                  width={Math.max(1, paso - 4)}
                  height={altura}
                  className="operacion-barra-valor"
                />
                {diasCierre.has(d.dia) && (
                  <line
                    x1={x + paso / 2}
                    x2={x + paso / 2}
                    y1={margen.arriba}
                    y2={margen.arriba + graficoAlto}
                    className="operacion-cierre"
                  />
                )}
              </g>
            );
          })}
          <line
            x1={margen.izquierda}
            x2={ancho - margen.derecha}
            y1={margen.arriba + graficoAlto}
            y2={margen.arriba + graficoAlto}
            className="operacion-eje-linea"
          />
          {marcas.map((i) => (
            <text
              key={i}
              x={margen.izquierda + (i + 0.5) * paso}
              y={alto - 10}
              textAnchor="middle"
              className="operacion-eje"
            >
              {diaLegible(serie[i].dia).slice(0, 5)}
            </text>
          ))}
        </svg>
      </div>
      <figcaption>
        <span className="operacion-grafico-ayuda-movil">
          Desplaza el gráfico para ver todos los días.{" "}
        </span>
        Fechas del curso · Usa Tab para entrar al gráfico y las flechas para
        recorrer sus valores.
      </figcaption>
    </figure>
  );
}
