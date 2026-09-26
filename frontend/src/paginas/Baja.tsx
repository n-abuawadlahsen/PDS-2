import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { aplicarBaja, obtenerBaja, type EstadoBaja } from "../lib/api";

/** Confirmación de baja desde el enlace del correo (S11.4.4). Abrir la página
 * no cambia nada; solo el botón da de baja o vuelve a suscribir. */
export function Baja() {
  const { token } = useParams<{ token: string }>();
  const [estado, setEstado] = useState<EstadoBaja | null | undefined>(undefined);
  const [hecho, setHecho] = useState(false);

  useEffect(() => {
    if (token) obtenerBaja(token).then(setEstado);
  }, [token]);

  if (!token || estado === undefined) return <p>Cargando…</p>;
  if (estado === null)
    return (
      <main>
        <h1>Enlace no válido</h1>
        <p>
          Este enlace ya no es válido. Puedes gestionar tus avisos desde tu <Link to="/perfil">perfil</Link>.
        </p>
      </main>
    );

  async function cambiar(accion: "baja" | "alta") {
    if (!token) return;
    const nuevo = await aplicarBaja(token, accion);
    if (nuevo) {
      setEstado(nuevo);
      setHecho(true);
    }
  }

  return (
    <main>
      <h1>Informe docente diario de {estado.curso_codigo}</h1>
      {estado.activa ? (
        <>
          <p>Estás suscrito al informe diario de {estado.curso_nombre}.</p>
          <button onClick={() => cambiar("baja")}>Darme de baja de este curso</button>
        </>
      ) : (
        <>
          <p>
            {hecho ? "Te has dado de baja" : "No estás suscrito"} del informe de {estado.curso_nombre}
            {estado.otros_cursos_suscritos > 0 && `; sigues suscrito a otros ${estado.otros_cursos_suscritos} cursos`}.
          </p>
          <button onClick={() => cambiar("alta")}>Volver a suscribirme</button>
        </>
      )}
      <p style={{ fontSize: "0.85rem", color: "#666" }}>
        Para todos tus cursos a la vez, entra a tu <Link to="/perfil">perfil</Link>.
      </p>
    </main>
  );
}
