import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  cambiarTodasLasNotificaciones,
  obtenerNotificacionesPerfil,
  regenerarEnlacesDeBaja,
  type SuscripcionInforme,
} from "../lib/api";

/** Vista agregada del informe diario en /perfil (S11.4.3): todos mis cursos,
 * con «suscribirme a todos» y «darme de baja de todos». */
export function NotificacionesPerfil() {
  const [filas, setFilas] = useState<SuscripcionInforme[]>([]);
  const [mensaje, setMensaje] = useState<string | null>(null);

  useEffect(() => {
    obtenerNotificacionesPerfil().then(setFilas);
  }, []);

  return (
    <section>
      <h2>Informe docente diario</h2>
      {filas.length === 0 ? (
        <p>No formas parte del equipo docente de ningún curso.</p>
      ) : (
        <ul>
          {filas.map((f) => (
            <li key={f.curso_id}>
              <Link to={`/cursos/${f.curso_id}/mis-notificaciones`}>
                {f.curso_codigo} · {f.curso_nombre}
              </Link>
              : {f.activa ? "suscrito" : "no suscrito"}
            </li>
          ))}
        </ul>
      )}
      {mensaje && <p role="status">{mensaje}</p>}
      <button onClick={async () => setFilas(await cambiarTodasLasNotificaciones(true))}>Suscribirme a todos</button>{" "}
      <button onClick={async () => setFilas(await cambiarTodasLasNotificaciones(false))}>Darme de baja de todos</button>{" "}
      <button
        onClick={async () =>
          setMensaje(
            (await regenerarEnlacesDeBaja())
              ? "Listo: los enlaces de baja de correos anteriores ya no funcionan."
              : "No se pudieron regenerar los enlaces.",
          )
        }
      >
        Regenerar mis enlaces de baja
      </button>
    </section>
  );
}
