import { Link, useParams } from "react-router-dom";
import { aplicarBaja, obtenerBaja } from "../lib/api";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import { Cabecera, Cargando, ErrorCarga, Mensajes } from "../components/ui";

export function Baja() {
  const { token = "" } = useParams();
  const consulta = useConsulta(`baja:${token}`, () => obtenerBaja(token));
  const op = useOperacion();
  if (consulta.cargando) return <Cargando />;
  if (consulta.error)
    return <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />;
  const estado = consulta.datos;
  if (!estado)
    return (
      <section className="panel">
        <h1>Enlace no válido</h1>
        <p>
          Este enlace ya no es válido. Gestiona tus avisos desde{" "}
          <Link to="/perfil">tu perfil</Link>.
        </p>
      </section>
    );
  return (
    <section className="panel">
      <Cabecera
        titulo={`Informe diario · ${estado.curso_codigo}`}
        descripcion={estado.curso_nombre}
      />
      <p>
        {estado.activa
          ? "Estás suscrito al informe diario de este curso."
          : "No estás suscrito al informe diario de este curso."}
      </p>
      {!estado.activa && estado.otros_cursos_suscritos > 0 && (
        <p>Sigues suscrito a otros {estado.otros_cursos_suscritos} cursos.</p>
      )}
      <Mensajes error={op.error} mensaje={op.mensaje} />
      <button
        disabled={op.ocupado}
        onClick={() =>
          op.ejecutar(async () => {
            const nuevo = await aplicarBaja(
              token,
              estado.activa ? "baja" : "alta",
            );
            if (!nuevo)
              throw new Error(
                "No pudimos cambiar tu suscripción. El enlace puede haber caducado; puedes intentarlo desde tu perfil.",
              );
            consulta.actualizar(nuevo);
            op.setMensaje(
              nuevo.activa
                ? "Te suscribiste nuevamente."
                : "Te diste de baja de este curso.",
            );
          })
        }
      >
        {op.ocupado
          ? "Guardando…"
          : estado.activa
            ? "Darme de baja de este curso"
            : "Volver a suscribirme"}
      </button>
      <p className="help">
        Administra todos tus cursos desde <Link to="/perfil">tu perfil</Link>.
      </p>
    </section>
  );
}
