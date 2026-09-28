import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { cambiarMisNotificaciones, obtenerMisNotificaciones, type SuscripcionInforme } from "../lib/api";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "var(--color-text-secondary)" } as const;

const MOTIVO_BAJA: Record<string, string> = {
  USUARIO: "Te diste de baja.",
  TOPE_SUSCRIPTORES: "Este curso ya tiene 30 personas suscritas, el máximo; no quedaste suscrito.",
  RETIRO_MEMBRESIA: "Dejaste de formar parte del equipo docente.",
  REBOTE: "Tu correo rechazó un envío; vuelve a suscribirte cuando esté solucionado.",
};

/** Autogestión de la suscripción al informe diario de un curso (S11.4.5):
 * cada persona decide la suya, con solo ver el curso. */
export function MisNotificaciones() {
  const { cursoId } = useParams<{ cursoId: string }>();
  const [s, setS] = useState<SuscripcionInforme | null>(null);

  useEffect(() => {
    if (cursoId) obtenerMisNotificaciones(cursoId).then(setS);
  }, [cursoId]);

  if (!cursoId || !s) return <p>Cargando…</p>;
  return (
    <main>
      <p>
        <Link to={`/cursos/${cursoId}/tareas`}>← Tareas</Link> · <Link to={`/cursos/${cursoId}/informes`}>Informes</Link>
      </p>
      <h1>Mis notificaciones · {s.curso_codigo}</h1>
      <section>
        <h2>Informe docente diario</h2>
        <p>
          Llega a las 07:00 (hora del curso) con lo que requiere tu atención, lo pendiente, la actividad y los próximos
          cierres. Solo se envía mientras hay alguna tarea activa.
        </p>
        <p>
          <strong>{s.activa ? "Estás suscrito." : "No estás suscrito."}</strong>
          {!s.activa && s.origen_baja && <span style={ESTILO_MOTIVO}> {MOTIVO_BAJA[s.origen_baja] ?? ""}</span>}
        </p>
        <button onClick={async () => setS(await cambiarMisNotificaciones(cursoId, !s.activa))}>
          {s.activa ? "Darme de baja" : "Suscribirme"}
        </button>
        <p style={ESTILO_MOTIVO}>Tu suscripción es solo tuya: nadie más puede cambiarla. Para todos tus cursos, usa tu perfil.</p>
      </section>
    </main>
  );
}
