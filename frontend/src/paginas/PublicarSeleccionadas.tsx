import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  comprobarContraCanvas,
  obtenerPantallaCorreccion,
  publicarCorreccion,
  type MatrizCorreccion,
} from "../lib/api";
import { prepararSinEntrega } from "../lib/apiFinal";
import { Aviso, Mensajes, useConfirmar } from "../components/ui";
import { useOperacion } from "../hooks/useConsulta";
import { useCurso } from "../components/Layout";
import { EstadoTrabajo } from "../components/EstadoTrabajo";
import {
  AccesosCorreccion,
  CausasParticipacion,
} from "../components/EvidenciaParticipacion";

interface ResultadoFila {
  entregaId: string;
  sujetoId: string;
  sujeto: string;
  texto: string;
  correcto: boolean;
}
export function PublicarSeleccionadas({
  cursoId,
  tareaId,
  matriz,
  onFin,
  puedePublicar = true,
}: {
  cursoId: string;
  tareaId: string;
  matriz: MatrizCorreccion;
  onFin: () => void;
  puedePublicar?: boolean;
}) {
  const listas = matriz.sujetos.flatMap((s) =>
    Object.entries(s.celdas)
      .filter(([, c]) => c.estado === "LISTA_PARA_PUBLICAR" && c.publicable)
      .map(([entregaId]) => ({
        entregaId,
        sujetoId: s.sujeto_id,
        sujeto: s.sujeto,
      })),
  );
  const [elegidas, setElegidas] = useState<Set<string>>(new Set());
  const [progreso, setProgreso] = useState<{
    actual: number;
    total: number;
  } | null>(null);
  const [resultados, setResultados] = useState<ResultadoFila[]>([]);
  const { curso } = useCurso();
  const [params, setParams] = useSearchParams();
  const claveComprobacion = `comprobacion-${tareaId}`;
  const trabajos = (params.get(claveComprobacion)?.split(",") ?? []).filter(
    (id) => /^[a-zA-Z0-9-]{1,80}$/.test(id),
  );
  const comprobando = trabajos.length > 0;
  const [sinEntrega, setSinEntrega] = useState(false);
  const op = useOperacion();
  const confirmar = useConfirmar();
  const vigente = useRef(true);
  const detener = useRef(false);
  const alFin = useRef(onFin);
  alFin.current = onFin;
  useEffect(() => {
    vigente.current = true;
    return () => {
      vigente.current = false;
      detener.current = true;
    };
  }, []);
  async function publicar() {
    const cola = listas.filter((fila) =>
      elegidas.has(`${fila.entregaId}/${fila.sujetoId}`),
    );
    if (
      !cola.length ||
      !(await confirmar({
        titulo: `Publicar ${cola.length} calificaciones`,
        descripcion:
          "Se publicarán en Canvas las correcciones seleccionadas, una por una. Cada resultado se verificará. Las filas con conflictos o requisitos pendientes quedarán disponibles para revisión individual.",
        accion: "Publicar seleccionadas",
      }))
    )
      return;
    await op.ejecutar(async () => {
      detener.current = false;
      setResultados([]);
      const salida: ResultadoFila[] = [];
      for (const [i, fila] of cola.entries()) {
        if (!vigente.current || detener.current) break;
        setProgreso({ actual: i + 1, total: cola.length });
        let texto: string;
        let correcto = false;
        try {
          // Releer evita volver a publicar una fila ya completada al retomar.
          const actual = await obtenerPantallaCorreccion(
            cursoId,
            fila.entregaId,
            fila.sujetoId,
          );
          if (!vigente.current || detener.current) break;
          if (!actual) texto = "La corrección no está disponible.";
          else if (
            ["PUBLICADA", "PUBLICADA_CON_ADVERTENCIA"].includes(actual.estado)
          ) {
            texto = "Ya estaba publicada; se omitió.";
            correcto = true;
          } else if (
            actual.estado !== "LISTA_PARA_PUBLICAR" ||
            !actual.publicable
          )
            texto =
              actual.motivo_no_publicable ??
              "La corrección ya no está lista para publicar.";
          else if (
            actual.banderas.reclamo_abierto ||
            actual.banderas.version_desactualizada ||
            actual.rubrica.cambio_sin_revisar ||
            (actual.repositorio_estado === "INACCESIBLE" &&
              !actual.banderas.reconocimiento_sin_codigo)
          )
            texto = "Requiere revisión y confirmación individual.";
          else {
            const r = await publicarCorreccion(
              cursoId,
              fila.entregaId,
              fila.sujetoId,
              {},
            );
            correcto =
              r.ok &&
              ["PUBLICADA", "PUBLICADA_CON_ADVERTENCIA"].includes(
                r.datos?.estado ?? "",
              );
            texto = r.ok
              ? r.datos?.estado === "PUBLICADA"
                ? "Publicada y verificada."
                : r.datos?.estado === "PUBLICADA_CON_ADVERTENCIA"
                  ? "Publicada con advertencia: revisa Canvas."
                  : r.datos?.error || "No se confirmó la publicación."
              : r.detalle?.codigo === "CONFLICTO"
                ? "Conflicto con Canvas: elige cómo resolverlo en la corrección."
                : r.detalle?.motivo || "No se pudo publicar.";
          }
        } catch {
          texto = "No pudimos conectar. Revisa el estado antes de reintentar.";
        }
        salida.push({ ...fila, texto, correcto });
        if (vigente.current) setResultados([...salida]);
      }
      if (vigente.current) {
        setProgreso(null);
        setElegidas(
          new Set(
            salida
              .filter((f) => !f.correcto)
              .map((f) => `${f.entregaId}/${f.sujetoId}`),
          ),
        );
        alFin.current();
      }
    });
  }
  return (
    <section aria-label="Acciones de publicación" className="panel">
      <div className="actions">
        <button
          disabled={op.ocupado || comprobando}
          onClick={() =>
            op.ejecutar(async () => {
              for (const entrega of matriz.entregas) {
                const resultado = await comprobarContraCanvas(
                  cursoId,
                  entrega.id,
                );
                if (!resultado.trabajo_id)
                  throw new Error(
                    "La comprobación se solicitó, pero el servidor no devolvió su identificador. Actualiza el estado para revisarlo.",
                  );
                setParams(
                  () => {
                    const nuevos = new URLSearchParams(window.location.search);
                    const ids = nuevos.get(claveComprobacion)?.split(",") ?? [];
                    nuevos.set(
                      claveComprobacion,
                      [...new Set([...ids, resultado.trabajo_id!])].join(","),
                    );
                    return nuevos;
                  },
                  { replace: true },
                );
              }
            }, "Comprobación encolada. Se consultará el resultado automáticamente.")
          }
        >
          {comprobando ? "Comprobando con Canvas…" : "Comprobar contra Canvas"}
        </button>
        <button disabled={op.ocupado} onClick={onFin}>
          Actualizar estado
        </button>
      </div>
      <Mensajes error={op.error} mensaje={op.mensaje} />
      {trabajos.map((id) => (
        <EstadoTrabajo
          key={id}
          ruta={`/api/cursos/${cursoId}/trabajos/${id}`}
          zona={curso.zona_horaria}
          cadencia={3000}
          alTerminar={(trabajo) => {
            setParams(
              () => {
                const nuevos = new URLSearchParams(window.location.search);
                const ids = (
                  nuevos.get(claveComprobacion)?.split(",") ?? []
                ).filter((t) => t !== trabajo.id);
                if (ids.length) nuevos.set(claveComprobacion, ids.join(","));
                else nuevos.delete(claveComprobacion);
                return nuevos;
              },
              { replace: true },
            );
            alFin.current();
            if (trabajo.estado !== "OK")
              op.setError(
                "La comprobación con Canvas requiere atención. El contraste anterior se conserva; revisa la vinculación antes de reintentar.",
              );
          }}
        />
      ))}
      {puedePublicar && (
        <>
          {listas.length > 0 && (
            <details>
              <summary>
                Publicación masiva · {listas.length} correcciones listas
              </summary>
              <p className="help">
                Selecciona explícitamente las calificaciones. No se resolverán
                conflictos ni se publicarán versiones pendientes de revisión
                automáticamente.
              </p>
              <fieldset disabled={op.ocupado}>
                <legend>Correcciones a publicar</legend>
                {listas.map((fila) => {
                  const clave = `${fila.entregaId}/${fila.sujetoId}`;
                  return (
                    <label key={clave} className="check">
                      <input
                        type="checkbox"
                        checked={elegidas.has(clave)}
                        onChange={(e) => {
                          const n = new Set(elegidas);
                          if (e.target.checked) n.add(clave);
                          else n.delete(clave);
                          setElegidas(n);
                        }}
                      />
                      {fila.sujeto} ·{" "}
                      {
                        matriz.entregas.find((e) => e.id === fila.entregaId)
                          ?.nombre
                      }
                    </label>
                  );
                })}
              </fieldset>
              <button
                className="primary"
                disabled={
                  !listas.some((f) =>
                    elegidas.has(`${f.entregaId}/${f.sujetoId}`),
                  ) || op.ocupado
                }
                onClick={publicar}
              >
                Publicar seleccionadas
              </button>
            </details>
          )}
          {progreso && (
            <div role="status">
              <p>
                Publicando {progreso.actual} de {progreso.total}…
              </p>
              <progress
                value={progreso.actual - 1}
                max={progreso.total}
                aria-label="Progreso de publicación"
              />
              <button
                onClick={() => {
                  detener.current = true;
                }}
              >
                Detener después de esta publicación
              </button>
            </div>
          )}
          {resultados.length > 0 && (
            <ul>
              {resultados.map((r) => (
                <li key={`${r.entregaId}/${r.sujetoId}`}>
                  <strong>{r.sujeto}</strong>: {r.texto}{" "}
                  <Link
                    to={`/cursos/${cursoId}/correccion/${r.entregaId}/${r.sujetoId}`}
                  >
                    Revisar corrección
                  </Link>
                </li>
              ))}
            </ul>
          )}
          {matriz.sujetos.some((s) =>
            Object.values(s.celdas).some((c) =>
              c.banderas.includes("sin_commits"),
            ),
          ) && (
            <>
              <button
                disabled={op.ocupado}
                onClick={() => setSinEntrega(!sinEntrega)}
              >
                Preparar calificaciones sin commits
              </button>
              {sinEntrega && (
                <SinEntrega cursoId={cursoId} matriz={matriz} onFin={onFin} />
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}
function SinEntrega({
  cursoId,
  matriz,
  onFin,
}: {
  cursoId: string;
  matriz: MatrizCorreccion;
  onFin: () => void;
}) {
  const [entrega, setEntrega] = useState(matriz.entregas[0]?.id ?? "");
  const [seleccion, setSeleccion] = useState<Set<string>>(new Set());
  const [nota, setNota] = useState("");
  const [comentario, setComentario] = useState(
    "No se registraron commits en tu repositorio al cierre de esta entrega.",
  );
  const [confirmacion, setConfirmacion] = useState("");
  const op = useOperacion();
  const filas = matriz.sujetos.filter((s) => {
    const c = s.celdas[entrega];
    return (
      c?.banderas.includes("sin_commits") &&
      !["PUBLICADA", "PUBLICADA_CON_ADVERTENCIA", "PUBLICANDO"].includes(
        c.estado,
      )
    );
  });
  return (
    <form
      className="form-stack"
      onSubmit={(e) => {
        e.preventDefault();
        void op.ejecutar(async () => {
          const r = await prepararSinEntrega(cursoId, entrega, {
            sujeto_ids: [...seleccion],
            nota: nota.trim(),
            comentario: comentario.trim(),
            confirmacion: confirmacion.trim(),
          });
          op.setMensaje(
            `${r.preparadas} correcciones preparadas. Selecciónalas en publicación masiva para publicarlas en Canvas.`,
          );
          setSeleccion(new Set());
          onFin();
        });
      }}
    >
      <h3>Calificaciones sin commits al cierre</h3>
      <Aviso tipo="warning">
        Revisa cada caso antes de seleccionarlo, especialmente si el estudiante
        aceptó su invitación a GitHub y si hay commits pendientes de atribuir.
        Consulta las causas registradas y la evidencia de esta entrega. Ningún
        sujeto está seleccionado por defecto.
      </Aviso>
      <Mensajes error={op.error} mensaje={op.mensaje} />
      <label>
        Entrega
        <select
          value={entrega}
          onChange={(e) => {
            setEntrega(e.target.value);
            setSeleccion(new Set());
          }}
        >
          {matriz.entregas.map((e) => (
            <option key={e.id} value={e.id}>
              {e.nombre}
            </option>
          ))}
        </select>
      </label>
      <fieldset disabled={op.ocupado}>
        <legend>Sujetos que revisaste</legend>
        {filas.map((s) => (
          <div className="form-stack" key={s.sujeto_id}>
            <label className="check">
              <input
                type="checkbox"
                checked={seleccion.has(s.sujeto_id)}
                onChange={(e) => {
                  const n = new Set(seleccion);
                  if (e.target.checked) n.add(s.sujeto_id);
                  else n.delete(s.sujeto_id);
                  setSeleccion(n);
                }}
              />
              {s.sujeto}
            </label>
            <AccesosCorreccion accesos={s.accesos} />
            <CausasParticipacion
              causas={s.celdas[entrega]?.causas_sin_participacion}
            />
            <Link
              to={`/cursos/${cursoId}/correccion/${entrega}/${s.sujeto_id}`}
            >
              Ver evidencia
            </Link>
          </div>
        ))}
      </fieldset>
      <label>
        Nota común
        <input
          required
          value={nota}
          maxLength={20}
          onChange={(e) => setNota(e.target.value)}
        />
      </label>
      <label>
        Comentario
        <textarea
          required
          value={comentario}
          maxLength={4000}
          onChange={(e) => setComentario(e.target.value)}
        />
      </label>
      <label>
        Confirmación escrita de tu revisión
        <textarea
          required
          minLength={10}
          maxLength={500}
          value={confirmacion}
          onChange={(e) => setConfirmacion(e.target.value)}
          placeholder="Explica por qué corresponde calificar estos casos sin commits."
        />
      </label>
      <button
        className="primary"
        disabled={
          op.ocupado ||
          !seleccion.size ||
          !nota.trim() ||
          !comentario.trim() ||
          confirmacion.trim().length < 10
        }
      >
        Preparar y marcar listas
      </button>
      <p className="help">
        Esta acción guarda la misma nota y comentario para los sujetos
        seleccionados. La publicación en Canvas requiere el paso siguiente.
      </p>
    </form>
  );
}
