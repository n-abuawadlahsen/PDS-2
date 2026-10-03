import { Link, useParams } from "react-router-dom";
import { cambiarMisNotificaciones, obtenerMisNotificaciones } from "../lib/api";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import {
  Aviso,
  Cabecera,
  Cargando,
  ErrorCarga,
  Estado,
  Mensajes,
} from "../components/ui";
import { useCurso } from "../components/Layout";

const MOTIVO_BAJA: Record<string, string> = {
  USUARIO: "Te diste de baja.",
  TOPE_SUSCRIPTORES:
    "Este curso alcanzó el máximo de 30 personas suscritas. Tu suscripción no se activó.",
  RETIRO_MEMBRESIA: "Dejaste de formar parte del equipo docente.",
  REBOTE:
    "Tu correo rechazó un envío. Vuelve a suscribirte cuando esté solucionado.",
};
export function MisNotificaciones() {
  const { cursoId = "" } = useParams();
  const { curso } = useCurso();
  const consulta = useConsulta(`suscripcion:${cursoId}`, () =>
    obtenerMisNotificaciones(cursoId),
  );
  const op = useOperacion();
  const s = consulta.datos;
  return (
    <>
      <Cabecera
        titulo="Mis notificaciones"
        descripcion="Elige qué informes recibes de este curso."
        acciones={
          <Link className="button" to={`/cursos/${cursoId}/informes`}>
            Ver informes
          </Link>
        }
      />
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {!s ? (
        !consulta.error && <Cargando />
      ) : (
        <section className="panel">
          <h2>Informe docente diario</h2>
          <p>
            Recibe los pendientes, la actividad y los próximos cierres a las
            07:00 ({curso.zona_horaria}). Solo se envía mientras haya tareas
            activas.
          </p>
          <p>
            <Estado
              valor={s.activa ? "ACTIVA" : "INACTIVA"}
              texto={s.activa ? "Suscripción activa" : "Sin suscripción"}
            />
          </p>
          {!s.activa && s.origen_baja && (
            <Aviso tipo="warning">
              {MOTIVO_BAJA[s.origen_baja] ?? "Tu suscripción está desactivada."}
            </Aviso>
          )}
          <Mensajes error={op.error} mensaje={op.mensaje} />
          <button
            className={s.activa ? "" : "primary"}
            disabled={op.ocupado}
            onClick={() =>
              op.ejecutar(async () => {
                const actualizada = await cambiarMisNotificaciones(
                  cursoId,
                  !s.activa,
                );
                consulta.actualizar(actualizada);
                op.setMensaje(
                  actualizada.activa
                    ? "Te suscribiste al informe diario."
                    : "Tu suscripción quedó desactivada.",
                );
              })
            }
          >
            {op.ocupado
              ? "Guardando…"
              : s.activa
                ? "Darme de baja"
                : "Suscribirme"}
          </button>
          <p className="help">
            Solo tú puedes cambiar tu suscripción. Administra todos tus cursos
            desde <Link to="/perfil">tu perfil</Link>.
          </p>
        </section>
      )}
    </>
  );
}
