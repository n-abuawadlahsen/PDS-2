import { Link } from "react-router-dom";
import {
  cambiarTodasLasNotificaciones,
  obtenerNotificacionesPerfil,
  regenerarEnlacesDeBaja,
} from "../lib/api";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import {
  Cargando,
  ErrorCarga,
  Estado,
  Mensajes,
  Vacio,
  useConfirmar,
} from "../components/ui";

export function NotificacionesPerfil() {
  const consulta = useConsulta("suscripciones:perfil", () =>
    obtenerNotificacionesPerfil(),
  );
  const op = useOperacion();
  const confirmar = useConfirmar();
  return (
    <section className="panel">
      <h2>Informe docente diario</h2>
      <p className="help">
        Cada curso envía su informe a las 07:00 de su zona horaria mientras
        tiene tareas activas.
      </p>
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {!consulta.datos ? (
        !consulta.error && <Cargando />
      ) : consulta.datos.length === 0 ? (
        <Vacio>No formas parte del equipo docente de ningún curso.</Vacio>
      ) : (
        <>
          <ul className="resource-list">
            {consulta.datos.map((f) => (
              <li key={f.curso_id}>
                <Link to={`/cursos/${f.curso_id}/mis-notificaciones`}>
                  {f.curso_codigo} · {f.curso_nombre}
                </Link>{" "}
                <Estado
                  valor={f.activa ? "ACTIVA" : "INACTIVA"}
                  texto={f.activa ? "Suscrito" : "Sin suscripción"}
                />
              </li>
            ))}
          </ul>
          <div className="actions">
            {[true, false].map((activa) => (
              <button
                key={String(activa)}
                disabled={op.ocupado}
                onClick={() =>
                  op.ejecutar(async () => {
                    const filas = await cambiarTodasLasNotificaciones(activa);
                    consulta.actualizar(filas);
                    op.setMensaje(
                      activa
                        ? `Suscripción activa en ${filas.filter((f) => f.activa).length} de ${filas.length} cursos. Revisa cada curso si alcanzó el máximo de suscriptores.`
                        : "Te diste de baja de todos tus cursos.",
                    );
                  })
                }
              >
                {activa ? "Suscribirme a todos" : "Darme de baja de todos"}
              </button>
            ))}
          </div>
        </>
      )}
      <Mensajes error={op.error} mensaje={op.mensaje} />
      <button
        disabled={op.ocupado}
        onClick={async () => {
          if (
            !(await confirmar({
              titulo: "Regenerar enlaces de baja",
              descripcion:
                "Los enlaces de los correos anteriores dejarán de funcionar. Los nuevos correos tendrán un enlace actualizado.",
              accion: "Regenerar enlaces",
            }))
          )
            return;
          await op.ejecutar(async () => {
            if (!(await regenerarEnlacesDeBaja()))
              throw new Error(
                "No pudimos regenerar los enlaces. Intenta nuevamente.",
              );
          }, "Los enlaces de baja anteriores quedaron invalidados.");
        }}
      >
        Regenerar mis enlaces de baja
      </button>
    </section>
  );
}
