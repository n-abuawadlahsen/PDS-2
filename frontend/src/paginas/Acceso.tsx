import { useSearchParams } from "react-router-dom";
import { FormularioAcceso } from "../components/FormularioAcceso";
import { descripcionDeMotivo } from "../lib/mensajes";
import { Aviso } from "../components/ui";
export function Acceso() {
  const [params] = useSearchParams();
  const motivo =
    params.get("motivo") === "SERVICIO_REINICIADO"
      ? {
          titulo: "El servicio ya está disponible",
          texto:
            "La conexión se interrumpió mientras iniciaba. Vuelve a pulsar Entrar con Google. Si venías de una invitación, abre nuevamente su enlace.",
        }
      : descripcionDeMotivo(params.get("motivo"));
  return (
    <section className="panel access-card">
      <p className="eyebrow">Equipo docente</p>
      <h1>Tus cursos, conectados</h1>
      <p>
        Coordina estudiantes, tareas y repositorios de programación entre Canvas
        y GitHub.
      </p>
      {motivo && (
        <Aviso tipo="error">
          <strong>{motivo.titulo}</strong>
          <p>{motivo.texto}</p>
        </Aviso>
      )}
      <FormularioAcceso
        action="/auth/google/inicio"
        texto="Entrar con Google"
      />
      <p className="help">
        Usa una cuenta personal de <strong>gmail.com</strong>. Las cuentas
        institucionales gestionadas no están habilitadas.
      </p>
      <hr />
      <p className="help">
        Este espacio es para profesores y ayudantes. Los estudiantes participan
        a través de Canvas y GitHub.
      </p>
    </section>
  );
}
