import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  obtenerBandejaCorreccion,
  obtenerCorrectores,
  obtenerMatrizCorreccion,
  obtenerPersonas,
  type BandejaCorreccion,
  type PropuestaReparto,
} from "../lib/api";
import {
  fechaFinal,
  repartoCompleto,
  type RepartoEntrada,
} from "../lib/apiFinal";
import { useCurso } from "../components/Layout";
import {
  Aviso,
  Cabecera,
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
import { PublicarSeleccionadas } from "./PublicarSeleccionadas";

const BANDERA: Record<string, string> = {
  version_desactualizada: "Versión nueva",
  reclamo_abierto: "Reclamo abierto",
  sin_commits: "Sin commits al cierre",
  reconocimiento_sin_codigo: "Calificada sin acceso al código",
  desalineada: "Reparto requiere revisión",
};
const CONTRASTE: Record<string, string> = {
  DIVERGE: "Canvas tiene otra nota",
  SOLO_EN_CANVAS: "Nota solo en Canvas",
};
const MOTIVOS: Record<string, string> = {
  PERIODO_CERRADO: "El período de Canvas está cerrado",
  NO_GRADEABLE: "Canvas no permite calificar este sujeto",
  NO_GRADED: "Esta tarea no lleva nota",
  GPA_SCALE: "La escala GPA no se publica desde aquí",
  LETTER_GRADE_SIN_ESQUEMA: "Falta el esquema de calificación con letras",
  MODERADA_O_ANONIMA: "La tarea es moderada o anónima",
  ENTREGA_DESPUBLICADA: "La entrega está despublicada en Canvas",
  ENTREGA_ELIMINADA: "La entrega se eliminó en Canvas",
  SUJETO_EXCLUIDO: "El sujeto está excluido de esta entrega",
  PUBLICACION_NO_AUTORIZADA:
    "La credencial de Canvas no permite publicar notas",
};
const motivoPublicacion = (motivo: string | null) =>
  motivo ? (MOTIVOS[motivo] ?? motivo) : "Revisa el detalle";
const ESTADOS = [
  "SIN_CORRECTOR",
  "ASIGNADA",
  "EN_CURSO",
  "LISTA_PARA_PUBLICAR",
  "PUBLICANDO",
  "PUBLICADA",
  "PUBLICADA_CON_ADVERTENCIA",
  "ERROR_PUBLICACION",
];
export function Correccion() {
  const { cursoId = "" } = useParams();
  const [parametros, setParametros] = useSearchParams();
  const consulta = useConsulta(`correccion:${cursoId}`, () =>
    obtenerBandejaCorreccion(cursoId),
  );
  const bandeja = consulta.datos;
  const pesta = parametros.get("pestana");
  const pestana = ["mias", "estado", "repartir"].includes(pesta ?? "")
    ? pesta
    : bandeja?.es_profesor
      ? "estado"
      : "mias";
  const tareaId = parametros.get("tarea") ?? bandeja?.tareas[0]?.id ?? "";
  function cambiar(clave: string, valor: string) {
    const nuevos = new URLSearchParams(parametros);
    nuevos.set(clave, valor);
    nuevos.delete("pagina");
    setParametros(nuevos, { replace: true });
  }
  return (
    <>
      <Cabecera
        titulo="Corrección"
        descripcion="Reparte el trabajo, revisa cada entrega y publica las calificaciones en Canvas."
      />
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {!bandeja ? (
        !consulta.error && <Cargando />
      ) : (
        <>
          {bandeja.nuevas > 0 && (
            <Aviso>Se te asignaron {bandeja.nuevas} entregas nuevas.</Aviso>
          )}
          <nav className="tabs" aria-label="Vistas de corrección">
            {[
              ["mias", "Mis asignaciones"],
              ["estado", "Estado de las entregas"],
              ...(bandeja.puede_repartir
                ? [["repartir", "Repartir correcciones"]]
                : []),
            ].map(([clave, texto]) => (
              <button
                key={clave}
                className={pestana === clave ? "active" : ""}
                aria-current={pestana === clave ? "page" : undefined}
                onClick={() => cambiar("pestana", clave)}
              >
                {texto}
              </button>
            ))}
          </nav>
          {!bandeja.puede_repartir && bandeja.sin_corrector > 0 && (
            <Aviso>
              {bandeja.sin_corrector} entregas sin corrector. El equipo con
              permiso para repartir puede asignarlas.
            </Aviso>
          )}
          {pestana === "mias" && (
            <MisAsignaciones cursoId={cursoId} bandeja={bandeja} />
          )}
          {pestana !== "mias" &&
            (bandeja.tareas.length === 0 ? (
              <Vacio>
                No hay tareas activas para corregir. Cuando actives una tarea
                aparecerá aquí.
              </Vacio>
            ) : (
              <label className="field">
                Tarea
                <select
                  value={tareaId}
                  onChange={(e) => cambiar("tarea", e.target.value)}
                >
                  {bandeja.tareas.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.nombre}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          {pestana === "estado" && tareaId && (
            <EstadoEntrega
              key={tareaId}
              cursoId={cursoId}
              tareaId={tareaId}
              puedePublicar={bandeja.puede_publicar}
            />
          )}
          {pestana === "repartir" &&
            (bandeja.puede_repartir ? (
              tareaId && (
                <Repartir
                  key={tareaId}
                  cursoId={cursoId}
                  tareaId={tareaId}
                  entregas={
                    bandeja.tareas.find((t) => t.id === tareaId)?.entregas ?? []
                  }
                  onCambio={consulta.recargar}
                />
              )
            ) : (
              <Aviso tipo="warning">
                No tienes permiso para repartir correcciones. Puedes consultar
                el estado de todas las entregas.
              </Aviso>
            ))}
        </>
      )}
    </>
  );
}
function MisAsignaciones({
  cursoId,
  bandeja,
}: {
  cursoId: string;
  bandeja: BandejaCorreccion;
}) {
  const [parametros, setParametros] = useSearchParams();
  const sinCorregir = parametros.get("pendientes") === "1";
  const entrega = parametros.get("entrega") ?? "";
  const filas = bandeja.mis_asignaciones.filter(
    (a) =>
      (!entrega || a.entrega_id === entrega) &&
      (!sinCorregir || ["ASIGNADA", "EN_CURSO"].includes(a.estado)),
  );
  const agrupadas = [
    ...new Map(
      bandeja.mis_asignaciones.map((a) => [a.entrega_id, a.entrega]),
    ).entries(),
  ];
  function filtrar(clave: string, valor: string) {
    const n = new URLSearchParams(parametros);
    if (valor) n.set(clave, valor);
    else n.delete(clave);
    setParametros(n, { replace: true });
  }
  return (
    <section className="panel">
      <h2>Mi trabajo</h2>
      <p>
        {bandeja.contador.asignadas} asignadas · {bandeja.contador.corregidas}{" "}
        corregidas · {bandeja.contador.publicadas} publicadas
      </p>
      {bandeja.mis_asignaciones.length === 0 ? (
        <Vacio>
          No tienes entregas asignadas. Cuando se reparta la corrección,
          aparecerán aquí.
        </Vacio>
      ) : (
        <>
          <div className="filters">
            <label>
              Entrega
              <select
                value={entrega}
                onChange={(e) => filtrar("entrega", e.target.value)}
              >
                <option value="">Todas mis entregas</option>
                {agrupadas.map(([id, nombre]) => (
                  <option key={id} value={id}>
                    {nombre}
                  </option>
                ))}
              </select>
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={sinCorregir}
                onChange={(e) =>
                  filtrar("pendientes", e.target.checked ? "1" : "")
                }
              />
              Solo sin corregir
            </label>
          </div>
          {filas.length === 0 ? (
            <Vacio>No hay asignaciones con estos filtros.</Vacio>
          ) : (
            <Tabla etiqueta="Mis entregas asignadas">
              <table>
                <thead>
                  <tr>
                    <th>Sujeto</th>
                    <th>Entrega</th>
                    <th>Estado</th>
                    <th>Atención</th>
                  </tr>
                </thead>
                <tbody>
                  {filas.map((a) => (
                    <tr key={`${a.entrega_id}/${a.sujeto_id}`}>
                      <td>
                        <Link
                          to={`/cursos/${cursoId}/correccion/${a.entrega_id}/${a.sujeto_id}`}
                          state={{
                            volver: `/cursos/${cursoId}/correccion?${parametros}`,
                            recorrido: {
                              entregaId: a.entrega_id,
                              sujetos: filas
                                .filter((f) => f.entrega_id === a.entrega_id)
                                .map((f) => f.sujeto_id),
                              pendientes: filas
                                .filter(
                                  (f) =>
                                    f.entrega_id === a.entrega_id &&
                                    ["ASIGNADA", "EN_CURSO"].includes(f.estado),
                                )
                                .map((f) => f.sujeto_id),
                              filtrado: true,
                            },
                          }}
                        >
                          {a.sujeto}
                        </Link>
                      </td>
                      <td>{a.entrega}</td>
                      <td>
                        <Estado valor={a.estado} texto={a.etiqueta} />
                      </td>
                      <td>
                        {[
                          a.sin_commits && "Sin commits al cierre",
                          a.reclamo_abierto && "Reclamo abierto",
                          a.version_desactualizada && "Versión nueva",
                          a.nueva && "Nueva asignación",
                        ]
                          .filter(Boolean)
                          .join(" · ") || "Sin avisos"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Tabla>
          )}
        </>
      )}
    </section>
  );
}
function EstadoEntrega({
  cursoId,
  tareaId,
  puedePublicar,
}: {
  cursoId: string;
  tareaId: string;
  puedePublicar: boolean;
}) {
  const consulta = useConsulta(`matriz:${cursoId}:${tareaId}`, () =>
    obtenerMatrizCorreccion(cursoId, tareaId),
  );
  const { curso } = useCurso();
  const [parametros, setParametros] = useSearchParams();
  const matriz = consulta.datos;
  const buscar = parametros.get("buscar") ?? "";
  const seccion = parametros.get("seccion") ?? "";
  const estado = parametros.get("estado") ?? "";
  const entrega = parametros.get("entrega") ?? "";
  const discrepancia = parametros.get("discrepancia") === "1";
  const pagina = Math.max(1, Number(parametros.get("pagina")) || 1);
  function filtrar(clave: string, valor: string) {
    const n = new URLSearchParams(parametros);
    if (valor) n.set(clave, valor);
    else n.delete(clave);
    if (clave !== "pagina") n.delete("pagina");
    setParametros(n, { replace: true });
  }
  if (!matriz)
    return consulta.error ? (
      <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
    ) : (
      <Cargando />
    );
  const entregas = matriz.entregas.filter((e) => !entrega || e.id === entrega);
  const sujetos = matriz.sujetos.filter(
    (s) =>
      s.sujeto
        .toLocaleLowerCase("es")
        .includes(buscar.toLocaleLowerCase("es")) &&
      (!seccion || s.seccion === seccion) &&
      entregas.some((e) => {
        const c = s.celdas[e.id];
        return (
          c &&
          (!estado || c.estado === estado) &&
          (!discrepancia || ["DIVERGE", "SOLO_EN_CANVAS"].includes(c.contraste))
        );
      }),
  );
  const c = matriz.contador;
  function exportar() {
    const csv = [
      [
        "Sujeto",
        "Sección",
        "Entrega",
        "Estado",
        "Corrector",
        "Publicable",
        "Motivo",
      ],
      ...sujetos.flatMap((s) =>
        entregas
          .filter((e) => s.celdas[e.id])
          .map((e) => {
            const celda = s.celdas[e.id];
            return [
              s.sujeto,
              s.seccion ?? "",
              e.nombre,
              celda.etiqueta,
              celda.corrector ?? "",
              celda.publicable ? "Sí" : "No",
              motivoPublicacion(celda.motivo_no_publicable),
            ];
          }),
      ),
    ]
      .map((fila) =>
        fila
          .map(
            (valor) =>
              `"${(/^[=+@-]/.test(valor) ? "'" : "") + valor.replaceAll('"', '""')}"`,
          )
          .join(","),
      )
      .join("\r\n");
    const url = URL.createObjectURL(
      new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "estado-correccion.csv";
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <section>
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      <div className="panel">
        <h2>Estado de las entregas</h2>
        <p>
          <strong>
            {c.corregidas} de {c.total} corregidas en la aplicación ·{" "}
            {c.con_nota_en_canvas} de {c.total} con nota en Canvas
          </strong>
        </p>
        <p className="help">
          {c.comprobado_en
            ? `Datos contrastados el ${fechaFinal(c.comprobado_en, curso.zona_horaria)}`
            : "Todavía no se ha comprobado el estado contra Canvas."}
        </p>
        <div className="filters">
          <label>
            Buscar sujeto
            <input
              type="search"
              value={buscar}
              onChange={(e) => filtrar("buscar", e.target.value)}
            />
          </label>
          <label>
            Entrega
            <select
              value={entrega}
              onChange={(e) => filtrar("entrega", e.target.value)}
            >
              <option value="">Todas las entregas</option>
              {matriz.entregas.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nombre}
                </option>
              ))}
            </select>
          </label>
          <label>
            Sección
            <select
              value={seccion}
              onChange={(e) => filtrar("seccion", e.target.value)}
            >
              <option value="">Todas las secciones</option>
              {[
                ...new Set(
                  matriz.sujetos.map((s) => s.seccion).filter(Boolean),
                ),
              ].map((s) => (
                <option key={s} value={s ?? ""}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label>
            Estado
            <select
              value={estado}
              onChange={(e) => filtrar("estado", e.target.value)}
            >
              <option value="">Todos los estados</option>
              {ESTADOS.map((e) => (
                <option key={e} value={e}>
                  {e.charAt(0) + e.slice(1).toLowerCase().replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={discrepancia}
              onChange={(e) =>
                filtrar("discrepancia", e.target.checked ? "1" : "")
              }
            />
            Solo discrepancias con Canvas
          </label>
          <button onClick={exportar} disabled={!sujetos.length}>
            Exportar CSV
          </button>
        </div>
        <PublicarSeleccionadas
          cursoId={cursoId}
          tareaId={tareaId}
          matriz={matriz}
          onFin={consulta.recargar}
          puedePublicar={puedePublicar}
        />
        {sujetos.length === 0 ? (
          <Vacio>No hay sujetos con estos filtros.</Vacio>
        ) : (
          <>
            <Tabla etiqueta="Matriz de corrección">
              <table>
                <thead>
                  <tr>
                    <th>Sujeto</th>
                    <th>Sección</th>
                    {entregas.map((e) => (
                      <th key={e.id}>{e.nombre}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sujetos.slice((pagina - 1) * 25, pagina * 25).map((s) => (
                    <tr key={s.sujeto_id}>
                      <td>
                        {s.sujeto}
                        {!s.activo && (
                          <div className="help">
                            Retirado, historial conservado
                          </div>
                        )}
                      </td>
                      <td>{s.seccion ?? "Sin sección"}</td>
                      {entregas.map((e) => {
                        const celda = s.celdas[e.id];
                        if (!celda) return <td key={e.id}>No aplica</td>;
                        return (
                          <td key={e.id}>
                            <Link
                              to={`/cursos/${cursoId}/correccion/${e.id}/${s.sujeto_id}`}
                              state={{
                                volver: `/cursos/${cursoId}/correccion?${parametros}`,
                                recorrido: {
                                  entregaId: e.id,
                                  sujetos: sujetos
                                    .filter((s) => s.celdas[e.id])
                                    .map((s) => s.sujeto_id),
                                  pendientes: sujetos
                                    .filter((s) =>
                                      ["ASIGNADA", "EN_CURSO"].includes(
                                        s.celdas[e.id]?.estado,
                                      ),
                                    )
                                    .map((s) => s.sujeto_id),
                                  filtrado: Boolean(
                                    buscar || seccion || estado || discrepancia,
                                  ),
                                },
                              }}
                            >
                              {celda.etiqueta}
                            </Link>
                            <div className="help">
                              {celda.corrector ?? "Sin corrector"}
                            </div>
                            {celda.banderas.map((b) => (
                              <div className="help" key={b}>
                                {BANDERA[b] ?? "Requiere revisión"}
                              </div>
                            ))}
                            {!celda.publicable && (
                              <div className="help">
                                No publicable:{" "}
                                {motivoPublicacion(celda.motivo_no_publicable)}
                              </div>
                            )}
                            {CONTRASTE[celda.contraste] && (
                              <div className="help">
                                {CONTRASTE[celda.contraste]}
                              </div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </Tabla>
            <Paginacion
              total={sujetos.length}
              pagina={pagina}
              tamano={25}
              cambiar={(n) => filtrar("pagina", String(n))}
            />
          </>
        )}
      </div>
      <div className="form-grid">
        <Agregado titulo="Por corrector" tabla={matriz.por_corrector} />
        <Agregado titulo="Por sección" tabla={matriz.por_seccion} />
        <Agregado titulo="Por entrega" tabla={matriz.por_entrega} />
      </div>
    </section>
  );
}
function Agregado({
  titulo,
  tabla,
}: {
  titulo: string;
  tabla: Record<string, Record<string, number>>;
}) {
  return (
    <section className="panel">
      <h2>{titulo}</h2>
      {Object.keys(tabla).length ? (
        <ul>
          {Object.entries(tabla).map(([clave, estados]) => (
            <li key={clave}>
              <strong>{clave}</strong>:{" "}
              {Object.entries(estados)
                .map(([e, n]) => `${n} ${e.toLowerCase().replaceAll("_", " ")}`)
                .join(", ")}
            </li>
          ))}
        </ul>
      ) : (
        <p className="help">Todavía no hay correcciones para comparar.</p>
      )}
    </section>
  );
}

function Repartir({
  cursoId,
  tareaId,
  entregas,
  onCambio,
}: {
  cursoId: string;
  tareaId: string;
  entregas: { id: string; nombre: string }[];
  onCambio: () => void;
}) {
  const [entregaId, setEntregaId] = useState(entregas[0]?.id ?? "");
  const [criterio, setCriterio] = useState("EQUITATIVO");
  const [reasignar, setReasignar] = useState(false);
  const [incluir, setIncluir] = useState(false);
  const [manual, setManual] = useState<Record<string, string | null>>({});
  const [porSeccion, setPorSeccion] = useState<Record<string, string>>({});
  const [seleccionados, setSeleccionados] = useState<Set<string>>(new Set());
  const [corrector, setCorrector] = useState("");
  const [propuesta, setPropuesta] = useState<PropuestaReparto | null>(null);
  const datos = useConsulta(`reparto:${cursoId}:${tareaId}`, async () => {
    const [correctores, personas, matriz] = await Promise.all([
      obtenerCorrectores(cursoId),
      obtenerPersonas(cursoId),
      obtenerMatrizCorreccion(cursoId, tareaId),
    ]);
    return { correctores, personas, matriz };
  });
  const op = useOperacion();
  const confirmar = useConfirmar();
  const cuerpo: RepartoEntrada = {
    criterio,
    reasignar,
    incluir_no_calificables: incluir,
    manual,
    por_seccion: porSeccion,
  };
  function editar() {
    setPropuesta(null);
  }
  if (!datos.datos)
    return datos.error ? (
      <ErrorCarga error={datos.error} reintentar={datos.recargar} />
    ) : (
      <Cargando />
    );
  const filas = datos.datos.matriz.sujetos.filter((s) => {
    const c = s.celdas[entregaId];
    return (
      c &&
      !["PUBLICANDO", "PUBLICADA", "PUBLICADA_CON_ADVERTENCIA"].includes(
        c.estado,
      )
    );
  });
  return (
    <section className="panel">
      <h2>Repartir correcciones</h2>
      <p className="help">
        Previsualiza el reparto antes de aplicarlo. La reasignación conserva el
        borrador de cada entrega y sujeto.
      </p>
      <Mensajes error={op.error} mensaje={op.mensaje} />
      <fieldset disabled={op.ocupado}>
        <legend>Configuración del reparto</legend>
        <div className="form-grid">
          <label>
            Entrega
            <select
              value={entregaId}
              onChange={(e) => {
                setEntregaId(e.target.value);
                setManual({});
                setSeleccionados(new Set());
                editar();
              }}
            >
              {entregas.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nombre}
                </option>
              ))}
            </select>
          </label>
          <label>
            Criterio
            <select
              value={criterio}
              onChange={(e) => {
                setCriterio(e.target.value);
                editar();
              }}
            >
              <option value="EQUITATIVO">Equitativo por peso</option>
              <option value="MANUAL">Manual y reasignación en bloque</option>
              <option value="SECCION">Por sección</option>
              <option value="COPIA_ENTREGA_ANTERIOR">
                Copiar entrega anterior
              </option>
            </select>
          </label>
        </div>
        <label className="check">
          <input
            type="checkbox"
            checked={reasignar}
            onChange={(e) => {
              setReasignar(e.target.checked);
              editar();
            }}
          />
          Reasignar también las que ya tienen corrector
        </label>
        {criterio === "EQUITATIVO" && (
          <label className="check">
            <input
              type="checkbox"
              checked={incluir}
              onChange={(e) => {
                setIncluir(e.target.checked);
                editar();
              }}
            />
            Incluir sujetos no calificables en el reparto automático
          </label>
        )}
        <p className="help">
          {datos.datos.correctores
            .map(
              (c) =>
                `${c.nombre} · peso ${c.peso}${c.sin_github ? " · sin cuenta GitHub, no podrá abrir el código" : ""}`,
            )
            .join(" / ")}
        </p>
        {criterio === "SECCION" && (
          <>
            <p className="help">
              Un sujeto con dos secciones activas requiere decisión manual. En
              grupos se usa la sección del integrante aceptado con menor
              identificador de Canvas.
            </p>
            {datos.datos.personas.secciones.map((s) => (
              <label key={s.id}>
                {s.nombre}
                <select
                  value={porSeccion[s.id] ?? ""}
                  onChange={(e) => {
                    const nuevos = { ...porSeccion };
                    if (e.target.value) nuevos[s.id] = e.target.value;
                    else delete nuevos[s.id];
                    setPorSeccion(nuevos);
                    editar();
                  }}
                >
                  <option value="">Sin propuesta</option>
                  {datos.datos?.correctores.map((c) => (
                    <option key={c.membresia_id} value={c.membresia_id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </>
        )}
        {criterio === "MANUAL" && (
          <>
            <div className="actions">
              <label>
                Corrector para el bloque
                <select
                  value={corrector}
                  onChange={(e) => setCorrector(e.target.value)}
                >
                  <option value="">Dejar sin corrector</option>
                  {datos.datos.correctores.map((c) => (
                    <option key={c.membresia_id} value={c.membresia_id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </label>
              <button
                disabled={!seleccionados.size}
                onClick={() => {
                  setManual({
                    ...manual,
                    ...Object.fromEntries(
                      [...seleccionados].map((s) => [s, corrector || null]),
                    ),
                  });
                  editar();
                }}
              >
                Aplicar al bloque seleccionado
              </button>
            </div>
            <Tabla etiqueta="Asignación manual">
              <table>
                <thead>
                  <tr>
                    <th>Seleccionar</th>
                    <th>Sujeto</th>
                    <th>Corrector propuesto</th>
                  </tr>
                </thead>
                <tbody>
                  {filas.map((s) => (
                    <tr key={s.sujeto_id}>
                      <td>
                        <input
                          type="checkbox"
                          aria-label={`Seleccionar ${s.sujeto}`}
                          checked={seleccionados.has(s.sujeto_id)}
                          onChange={(e) => {
                            const n = new Set(seleccionados);
                            if (e.target.checked) n.add(s.sujeto_id);
                            else n.delete(s.sujeto_id);
                            setSeleccionados(n);
                          }}
                        />
                      </td>
                      <td>{s.sujeto}</td>
                      <td>
                        <select
                          aria-label={`Corrector de ${s.sujeto}`}
                          value={
                            s.sujeto_id in manual
                              ? (manual[s.sujeto_id] ?? "")
                              : "conservar"
                          }
                          onChange={(e) => {
                            const n = { ...manual };
                            if (e.target.value === "conservar")
                              delete n[s.sujeto_id];
                            else n[s.sujeto_id] = e.target.value || null;
                            setManual(n);
                            editar();
                          }}
                        >
                          <option value="conservar">
                            Conservar:{" "}
                            {s.celdas[entregaId].corrector ?? "sin corrector"}
                          </option>
                          <option value="">Dejar sin corrector</option>
                          {datos.datos?.correctores.map((c) => (
                            <option key={c.membresia_id} value={c.membresia_id}>
                              {c.nombre}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Tabla>
          </>
        )}
        <button
          className="primary"
          disabled={!entregaId}
          onClick={() =>
            op.ejecutar(async () =>
              setPropuesta(
                await repartoCompleto(
                  cursoId,
                  entregaId,
                  "previsualizar",
                  cuerpo,
                ),
              ),
            )
          }
        >
          Previsualizar reparto
        </button>
      </fieldset>
      {propuesta && (
        <section>
          <h3>Propuesta de reparto</h3>
          <p>
            {Object.entries(propuesta.totales)
              .map(([nombre, cantidad]) => `${nombre}: ${cantidad}`)
              .join(" · ")}
          </p>
          {propuesta.requiere_decision.length > 0 && (
            <Aviso tipo="warning">
              {propuesta.requiere_decision.length} sujetos requieren decisión.
              Usa el reparto manual para resolverlos.
            </Aviso>
          )}
          <Tabla etiqueta="Vista previa del reparto">
            <table>
              <thead>
                <tr>
                  <th>Sujeto</th>
                  <th>Actual</th>
                  <th>Propuesto</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {propuesta.filas.map((f) => (
                  <tr key={f.sujeto_id}>
                    <td>{f.sujeto}</td>
                    <td>{f.actual ?? "Sin corrector"}</td>
                    <td>
                      {f.propuesto ?? "Sin corrector"}
                      {f.sobrescribe && (
                        <div className="help">
                          Se reasignará; el borrador se conserva
                        </div>
                      )}
                    </td>
                    <td>{f.estado}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Tabla>
          <button
            className="primary"
            disabled={op.ocupado}
            onClick={async () => {
              if (
                !(await confirmar({
                  titulo: "Aplicar reparto de correcciones",
                  descripcion: `Se aplicará el reparto de ${entregas.find((e) => e.id === entregaId)?.nombre ?? "esta entrega"}. Los borradores existentes se conservarán.`,
                  accion: "Confirmar y aplicar",
                }))
              )
                return;
              await op.ejecutar(async () => {
                const r = await repartoCompleto(
                  cursoId,
                  entregaId,
                  "aplicar",
                  cuerpo,
                );
                op.setMensaje(`Reparto aplicado: ${r.cambios} cambios.`);
                setPropuesta(null);
                datos.recargar();
                onCambio();
              });
            }}
          >
            Confirmar y aplicar
          </button>
        </section>
      )}
    </section>
  );
}
