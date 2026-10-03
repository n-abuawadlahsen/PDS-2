import { useState } from "react";
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
  Mensajes,
  Tabla,
  Vacio,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";

const ESTADO: Record<string, string> = {
  GENERADO: "Generado",
  SIN_TAREAS_ACTIVAS: "Sin tareas activas: no se envió",
  NO_GENERADO: "No se generó",
};
function fechaCorta(iso: string) {
  const [a, m, d] = iso.split("-");
  return `${d}-${m}-${a}`;
}
function Documento({ html }: { html: string }) {
  return (
    <iframe
      title="Contenido del informe docente"
      sandbox=""
      srcDoc={html}
      style={{
        width: "100%",
        minHeight: "65vh",
        border: "1px solid var(--color-border)",
        background: "white",
      }}
    />
  );
}
export function Informes() {
  const { cursoId = "", fecha } = useParams();
  const { curso, puede } = useCurso();
  const lista = useConsulta(`informes:${cursoId}`, () =>
    obtenerInformes(cursoId),
  );
  const dia = useConsulta(`informe:${cursoId}:${fecha}`, () =>
    fecha ? obtenerInformeDia(cursoId, fecha) : Promise.resolve(null),
  );
  const [vista, setVista] = useState<string | null>(null);
  const op = useOperacion();
  const confirmar = useConfirmar();
  return (
    <>
      <Cabecera
        titulo="Informe docente diario"
        descripcion={`Pendientes, actividad y próximos cierres. Envío a las 07:00 (${curso.zona_horaria}).`}
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
          <p className="help">
            {lista.datos.se_genera_desde
              ? `Historial disponible desde el ${fechaCorta(lista.datos.se_genera_desde)}.`
              : "Todavía no hay un informe generado para este curso."}{" "}
            Los informes anteriores conservan los datos del momento de su
            generación.
          </p>
          <Mensajes error={op.error} mensaje={op.mensaje} />
          <div className="actions">
            <button
              disabled={op.ocupado}
              onClick={() =>
                op.ejecutar(async () => {
                  const previa = await obtenerVistaPreviaInforme(cursoId);
                  setVista(previa.html);
                  if (!previa.hay_tareas_activas)
                    op.setMensaje(previa.mensaje ?? "No hay tareas activas.");
                })
              }
            >
              Vista previa de hoy
            </button>
            <button
              disabled={op.ocupado}
              onClick={() =>
                op.ejecutar(async () => {
                  const r = await enviarmeInforme(cursoId);
                  if (!r.ok)
                    throw new Error(
                      r.error || "No se pudo completar la operación.",
                    );
                  op.setMensaje(
                    r.datos?.encolados
                      ? "Tu informe quedó en cola. Puedes seguir trabajando mientras se envía."
                      : "No se encolaron nuevos envíos.",
                  );
                  lista.recargar();
                })
              }
            >
              Enviarme el informe de hoy
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
                  await op.ejecutar(async () => {
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
                Enviar a suscritos
              </button>
            )}
          </div>
          {vista && (
            <section className="panel">
              <div className="actions">
                <h2>Vista previa de hoy</h2>
                <button onClick={() => setVista(null)}>
                  Cerrar vista previa
                </button>
              </div>
              <p className="help">Esta vista no guarda ni envía un informe.</p>
              <Documento html={vista} />
            </section>
          )}
          {fecha && (
            <section className="panel">
              <h2>Informe del {fechaCorta(fecha)}</h2>
              {dia.error ? (
                <ErrorCarga error={dia.error} reintentar={dia.recargar} />
              ) : dia.cargando ? (
                <Cargando />
              ) : !dia.datos ? (
                <Vacio>No hay informe de ese día.</Vacio>
              ) : dia.datos.html ? (
                <Documento html={dia.datos.html} />
              ) : (
                <Aviso>
                  {ESTADO[dia.datos.estado] ?? "Informe no disponible"}
                  {dia.datos.motivo && `: ${dia.datos.motivo}`}
                </Aviso>
              )}
            </section>
          )}
          <section className="panel">
            <h2>Informes anteriores</h2>
            {lista.datos.informes.length === 0 ? (
              <Vacio>Cuando se genere el primer informe, aparecerá aquí.</Vacio>
            ) : (
              <Tabla etiqueta="Historial de informes">
                <table>
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Estado</th>
                      <th>Origen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lista.datos.informes.map((i) => (
                      <tr key={i.fecha}>
                        <td>
                          <Link to={`/cursos/${cursoId}/informes/${i.fecha}`}>
                            {fechaCorta(i.fecha)}
                          </Link>
                        </td>
                        <td>
                          {ESTADO[i.estado] ?? "No disponible"}
                          {i.motivo && <div className="help">{i.motivo}</div>}
                        </td>
                        <td>
                          {i.origen === "MANUAL"
                            ? "Generado manualmente"
                            : "Programado"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Tabla>
            )}
            {lista.datos.informes.length === 120 && (
              <p className="help">
                Se muestran los últimos 120 informes disponibles.
              </p>
            )}
          </section>
        </>
      )}
    </>
  );
}
