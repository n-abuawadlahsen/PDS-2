import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { API_BASE_URL } from "../lib/api";
import { descripcionDeMotivo } from "../lib/mensajes";
import { Aviso } from "../components/ui";
export function Acceso() {
  const [params] = useSearchParams();
  const motivo = descripcionDeMotivo(params.get("motivo"));
  const [enviando, setEnviando] = useState(false);
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
      <form
        method="POST"
        action={`${API_BASE_URL}/auth/google/inicio`}
        onSubmit={() => setEnviando(true)}
      >
        <button className="primary" type="submit" disabled={enviando}>
          {enviando ? "Abriendo Google…" : "Entrar con Google"}
        </button>
      </form>
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
