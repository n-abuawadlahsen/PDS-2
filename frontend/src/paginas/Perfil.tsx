import { useEffect, useState } from "react";
import { apiFetch, obtenerPerfil, type Perfil as PerfilTipo } from "../lib/api";

interface FilaSesion {
  id: number;
  agente: string | null;
  creada_en: string;
  es_la_actual: boolean;
}

/**
 * `/perfil`, recorte de Etapa P1 (SPEC 02 S2.10): identidad, sesiones y
 * cerrar cuenta. El resto (cuenta de GitHub, identidades de Canvas, enlaces
 * de baja) llega con las etapas que crean esas tablas -- ver README de la
 * carpeta backend/app/api/rutas/perfil.py.
 */
export function PerfilPagina() {
  const [perfil, setPerfil] = useState<PerfilTipo | null>(null);
  const [nombre, setNombre] = useState("");
  const [sesiones, setSesiones] = useState<FilaSesion[]>([]);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [cursosBloqueantes, setCursosBloqueantes] = useState<unknown[] | null>(null);

  async function cargar() {
    const datos = await obtenerPerfil();
    setPerfil(datos);
    if (datos) setNombre(datos.nombre);
    const respuestaSesiones = await apiFetch("/api/perfil/sesiones");
    if (respuestaSesiones.ok) setSesiones(await respuestaSesiones.json());
  }

  useEffect(() => {
    cargar();
  }, []);

  async function guardarNombre(evento: React.FormEvent) {
    evento.preventDefault();
    const respuesta = await apiFetch("/api/perfil", {
      method: "PATCH",
      body: JSON.stringify({ nombre }),
    });
    if (respuesta.ok) {
      setMensaje("Nombre actualizado.");
      setPerfil(await respuesta.json());
    } else {
      setMensaje("No se pudo actualizar el nombre.");
    }
  }

  async function cerrarOtrasSesiones() {
    const respuesta = await apiFetch("/api/perfil/sesiones", { method: "DELETE" });
    if (respuesta.ok) {
      setMensaje("Se cerraron las demás sesiones.");
      cargar();
    }
  }

  async function cerrarCuenta() {
    if (!window.confirm("¿Cerrar tu cuenta? No se puede deshacer desde aquí.")) return;
    const respuesta = await apiFetch("/api/perfil", { method: "DELETE" });
    if (respuesta.status === 409) {
      const cuerpo = await respuesta.json();
      setCursosBloqueantes(cuerpo.detail?.cursos ?? []);
      return;
    }
    if (respuesta.ok) {
      window.location.href = "/acceso";
    }
  }

  if (!perfil) return <p>Cargando...</p>;

  return (
    <main style={{ maxWidth: 640, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Mi perfil</h1>
      {mensaje && <p role="status">{mensaje}</p>}

      <section>
        <h2>Identidad</h2>
        <form onSubmit={guardarNombre}>
          <label>
            Nombre
            <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
          </label>
          <button type="submit">Guardar</button>
        </form>
        <p>
          Correo <code>{perfil.email}</code> (no editable: es la identidad de tu cuenta de Google).
        </p>
      </section>

      <section>
        <h2>Mis sesiones</h2>
        <ul>
          {sesiones.map((s) => (
            <li key={s.id}>
              {s.agente ?? "agente desconocido"} — {new Date(s.creada_en).toLocaleString("es-CL")}
              {s.es_la_actual && " (esta sesión)"}
            </li>
          ))}
        </ul>
        <button onClick={cerrarOtrasSesiones}>Cerrar las demás sesiones</button>
      </section>

      <section>
        <h2>Cerrar mi cuenta</h2>
        {cursosBloqueantes && cursosBloqueantes.length > 0 && (
          <p role="alert">
            No podés cerrar la cuenta: sos la única profesora activa de {cursosBloqueantes.length}{" "}
            curso(s). Promové a otro profesor o archivá el curso primero.
          </p>
        )}
        <button onClick={cerrarCuenta}>Cerrar mi cuenta</button>
      </section>
    </main>
  );
}
