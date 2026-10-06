import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  enviarInformeASuscritos,
  enviarmeInforme,
  obtenerInformeDia,
  obtenerInformes,
  obtenerVistaPreviaInforme,
} from "../lib/api";
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

const ESTADO: Record<string, string> = {
  GENERADO: "Generado",
  SIN_TAREAS_ACTIVAS: "Sin tareas activas: no se envió",
  NO_GENERADO: "No se generó",
};
// Etiqueta corta para el historial; el texto largo queda en el visor.
const ESTADO_CORTO: Record<string, [string, string]> = {
  GENERADO: ["COMPLETADO", "Generado"],
  SIN_TAREAS_ACTIVAS: ["NEUTRAL", "Sin tareas activas"],
  NO_GENERADO: ["ERROR", "No se generó"],
};
const DIAS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

function fechaCorta(iso: string) {
  const [a, m, d] = iso.split("-");
  return `${d}-${m}-${a}`;
}
function diaSemana(iso: string) {
  const [a, m, d] = iso.split("-").map(Number);
  return DIAS[new Date(a, m - 1, d).getDay()];
}

/** Muestra el HTML del informe aislado: sin scripts, con los enlaces abriendo
 * en la pestaña principal y con la altura de su contenido (sin doble scroll). */
function Documento({ html }: { html: string }) {
  const marco = useRef<HTMLIFrameElement>(null);
  const [alto, setAlto] = useState(480);
  function ajustar() {
    const cuerpo = marco.current?.contentDocument?.documentElement;
    if (cuerpo) setAlto(cuerpo.scrollHeight + 2);
  }
  useEffect(() => {
    window.addEventListener("resize", ajustar);
    return () => window.removeEventListener("resize", ajustar);
  }, []);
  return (
    <iframe
      ref={marco}
      title="Contenido del informe docente"
      // allow-same-origin solo para medir la altura: sin allow-scripts el
      // documento no puede ejecutar código.
      sandbox="allow-same-origin allow-top-navigation-by-user-activation"
      srcDoc={`<base target="_top"><style>body{margin:0}</style>${html}`}
      onLoad={ajustar}
      className="informe-documento"
      style={{ height: alto }}
    />
  );
}

export function Informes() {
  const { cursoId = "", fecha } = useParams();
  const { curso, puede } = useCurso();
  const lista = useConsulta(`informes:${cursoId}`, () =>
    obtenerInformes(cursoId),
  );
  // El documento solo se carga al elegir una fecha: el visor vacío ofrece el
  // más reciente con un clic en vez de abrirlo solo.
  const seleccionada = fecha;
  const masReciente = lista.datos?.informes[0]?.fecha;
  const dia = useConsulta(`informe:${cursoId}:${seleccionada}`, () =>
    seleccionada
      ? obtenerInformeDia(cursoId, seleccionada)
      : Promise.resolve(null),
  );
  const [vista, setVista] = useState<string | null>(null);
  const [accion, setAccion] = useState<string | null>(null);
  const op = useOperacion();
  const confirmar = useConfirmar();
  const visor = useRef<HTMLElement>(null);

  useEffect(() => {
    if (fecha) {
      setVista(null);
      if (window.matchMedia("(max-width: 960px)").matches)
        visor.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [fecha]);

  async function ejecutar(nombre: string, tarea: () => Promise<void>) {
    setAccion(nombre);
    try {
      await op.ejecutar(tarea);
    } finally {
      setAccion(null);
    }
  }

  return (
    <>
      <Cabecera
        titulo="Informe docente diario"
        descripcion={`Pendientes, actividad y próximos cierres de las tareas activas. Se envía cada día a las 07:00 (${curso.zona_horaria}).`}
        acciones={
          <Link className="button" to={`/cursos/${cursoId}/mis-notificaciones`}>
            Mi suscripción
          </Link>
        }
      />
      {lista.error && (
        <ErrorCarga error={lista.error} reintentar={lista.recargar} />
      )}
      {!lista.datos ? (
        !lista.error && <Cargando />
      ) : (
        <>
          <Mensajes error={op.error} mensaje={op.mensaje} />
          <section className="panel informe-hoy" aria-labelledby="informe-hoy">
            <div>
              <h2 id="informe-hoy">Informe de hoy</h2>
              <p className="help">
                Revisa cómo se ve antes del envío o recíbelo ahora en tu correo.
              </p>
            </div>
            <div className="actions">
              <button
                disabled={op.ocupado}
                aria-pressed={vista !== null}
                onClick={() =>
                  ejecutar("vista", async () => {
                    const previa = await obtenerVistaPreviaInforme(cursoId);
                    setVista(previa.html);
                    if (!previa.hay_tareas_activas)
                      op.setMensaje(
                        previa.mensaje ??
                          "No hay tareas activas: hoy no se enviaría informe.",
                      );
                    visor.current?.scrollIntoView({
                      behavior: "smooth",
                      block: "start",
                    });
                  })
                }
              >
                {accion === "vista" ? "Generando…" : "Vista previa de hoy"}
              </button>
              <button
                disabled={op.ocupado}
                onClick={() =>
                  ejecutar("enviarme", async () => {
                    const r = await enviarmeInforme(cursoId);
                    if (!r.ok)
                      throw new Error(
                        r.error || "No se pudo completar la operación.",
                      );
                    op.setMensaje(
                      r.datos?.encolados
                        ? "Tu informe quedó en cola. Llegará a tu correo en unos minutos."
                        : "No se encolaron nuevos envíos (puedes pedirlo hasta dos veces al día).",
                    );
                    lista.recargar();
                  })
                }
              >
                {accion === "enviarme"
                  ? "Enviando…"
                  : "Enviarme el informe de hoy"}
              </button>
              {puede("curso.administrar") && (
                <button
                  className="primary"
                  disabled={op.ocupado}
                  onClick={async () => {
                    if (
                      !(await confirmar({
                        titulo: "Enviar informe a las personas suscritas",
                        descripcion: `Se enviará por correo el informe de hoy de ${curso.nombre} a quienes estén suscritos. Si el informe ya existe, se enviará el mismo documento.`,
                        accion: "Generar y enviar",
                      }))
                    )
                      return;
                    await ejecutar("suscritos", async () => {
                      const r = await enviarInformeASuscritos(cursoId);
                      if (!r.ok)
                        throw new Error(
                          r.error || "No se pudo completar la operación.",
                        );
                      op.setMensaje(
                        `Informe encolado para ${r.datos?.encolados ?? 0} personas suscritas.`,
                      );
                      lista.recargar();
                    });
                  }}
                >
                  {accion === "suscritos" ? "Enviando…" : "Enviar a suscritos"}
                </button>
              )}
            </div>
          </section>

          <div className="informes-layout">
            <section className="panel" aria-labelledby="historial-informes">
              <h2 id="historial-informes">Historial</h2>
              <p className="help">
                {lista.datos.se_genera_desde
                  ? `Desde el ${fechaCorta(lista.datos.se_genera_desde)}. Cada informe conserva los datos del día en que se generó.`
                  : "Todavía no hay un informe generado para este curso."}
              </p>
              {lista.datos.informes.length === 0 ? (
                <Vacio>
                  Cuando se genere el primer informe, aparecerá aquí.
                </Vacio>
              ) : (
                <ul className="informes-lista">
                  {lista.datos.informes.map((i) => {
                    const [valor, texto] = ESTADO_CORTO[i.estado] ?? [
                      "NEUTRAL",
                      "No disponible",
                    ];
                    const actual = !vista && i.fecha === seleccionada;
                    return (
                      <li key={i.fecha}>
                        <Link
                          to={`/cursos/${cursoId}/informes/${i.fecha}`}
                          aria-current={actual ? "page" : undefined}
                          onClick={() => setVista(null)}
                        >
                          <span className="informes-fecha">
                            <span className="informes-dia">
                              {diaSemana(i.fecha)}
                            </span>{" "}
                            {fechaCorta(i.fecha)}
                          </span>
                          <Estado valor={valor} texto={texto} />
                          <span className="help">
                            {i.origen === "MANUAL" ? "Manual" : "Programado"}
                          </span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              )}
              {lista.datos.informes.length === 120 && (
                <p className="help">Se muestran los últimos 120 informes.</p>
              )}
            </section>

            <section
              ref={visor}
              className="panel informe-visor"
              aria-labelledby="visor-informe"
            >
              <div className="panel-header">
                <h2 id="visor-informe">
                  {vista
                    ? "Vista previa de hoy"
                    : seleccionada
                      ? `Informe del ${diaSemana(seleccionada)} ${fechaCorta(seleccionada)}`
                      : "Informe"}
                </h2>
                {vista && (
                  <button className="quiet" onClick={() => setVista(null)}>
                    Cerrar vista previa
                  </button>
                )}
              </div>
              {vista ? (
                <>
                  <Aviso>Vista previa: no se guarda ni se envía a nadie.</Aviso>
                  <Documento html={vista} />
                </>
              ) : !seleccionada ? (
                masReciente ? (
                  <div className="empty">
                    <p>Elige un informe del historial.</p>
                    <Link
                      className="button primary"
                      to={`/cursos/${cursoId}/informes/${masReciente}`}
                    >
                      Ver el más reciente ({diaSemana(masReciente)}{" "}
                      {fechaCorta(masReciente)})
                    </Link>
                  </div>
                ) : (
                  <Vacio>
                    Aún no hay informes. Usa «Vista previa de hoy» para ver cómo
                    se verá el de hoy.
                  </Vacio>
                )
              ) : dia.error ? (
                <ErrorCarga error={dia.error} reintentar={dia.recargar} />
              ) : dia.cargando ? (
                <Cargando texto="Cargando informe…" />
              ) : !dia.datos ? (
                <Vacio>No hay informe de ese día.</Vacio>
              ) : dia.datos.html ? (
                <Documento html={dia.datos.html} />
              ) : (
                <Aviso tipo="warning">
                  {ESTADO[dia.datos.estado] ?? "Informe no disponible"}
                  {dia.datos.motivo && `: ${dia.datos.motivo}`}
                </Aviso>
              )}
            </section>
          </div>
        </>
      )}
    </>
  );
}
