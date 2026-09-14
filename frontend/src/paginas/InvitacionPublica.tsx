import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import {
  API_BASE_URL,
  aceptarInvitacionConSesion,
  obtenerInvitacionPublica,
  obtenerPerfil,
  type InvitacionPublica,
} from "../lib/api";

const TEXTO_CONSENTIMIENTO =
  "Al aceptar, das tu consentimiento para que el equipo docente de este curso pueda leer todo el código de los repositorios del curso a través de la aplicación.";

/** `/invitaciones/{token}`, ruta publica sin sesion (SPEC 02 S2.5.4). */
export function InvitacionPublica() {
  const { token } = useParams<{ token: string }>();
  const [parametros] = useSearchParams();
  const errorUrl = parametros.get("error");
  const [invitacion, setInvitacion] = useState<InvitacionPublica | null>(null);
  const [tieneSesion, setTieneSesion] = useState(false);
  const [error, setError] = useState<string | null>(errorUrl);
  const [aceptando, setAceptando] = useState(false);

  useEffect(() => {
    if (!token) return;
    obtenerInvitacionPublica(token).then(setInvitacion).catch(() => setError("NO_ENCONTRADA"));
    obtenerPerfil().then((p) => setTieneSesion(p !== null));
  }, [token]);

  async function onAceptarConSesion() {
    if (!token) return;
    setAceptando(true);
    const respuesta = await aceptarInvitacionConSesion(token);
    if (respuesta.ok) {
      window.location.href = "/cursos";
    } else {
      const cuerpo = await respuesta.json().catch(() => ({}));
      setError(cuerpo.detail ?? "NO_ACEPTABLE");
      setAceptando(false);
    }
  }

  if (!invitacion && !error) return <p>Cargando...</p>;

  if (!invitacion) {
    return (
      <main style={{ maxWidth: 480, margin: "4rem auto", fontFamily: "sans-serif" }}>
        <h1>Invitación no encontrada</h1>
        <p role="alert">Ese enlace de invitación no existe o ya no es válido.</p>
      </main>
    );
  }

  const yaResuelta = invitacion.estado !== "PENDIENTE";

  return (
    <main style={{ maxWidth: 480, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Invitación al curso {invitacion.curso_nombre}</h1>
      <p>
        Correo destinatario: <code>{invitacion.email_enmascarado}</code>
      </p>
      <p>
        Rol: <strong>{invitacion.rol}</strong>
      </p>
      <p>Permisos: {invitacion.permisos.length ? invitacion.permisos.join(", ") : "los del rol"}</p>

      {error && (
        <p role="alert">
          {error === "CORREO_NO_COINCIDE" &&
            `Esta invitación es para ${invitacion.email_enmascarado}. Entraste con otro correo. Cambiá de cuenta o pedí una invitación nueva.`}
          {error === "EXPIRADA" && "Esta invitación caducó."}
          {error === "REVOCADA" && "Esta invitación fue revocada."}
          {error === "YA_ACEPTADA" && "Esta invitación ya fue aceptada."}
          {!["CORREO_NO_COINCIDE", "EXPIRADA", "REVOCADA", "YA_ACEPTADA"].includes(error) && error}
        </p>
      )}

      {yaResuelta && !error && <p>Esta invitación ya no está pendiente ({invitacion.estado}).</p>}

      {!yaResuelta && (
        <>
          <p style={{ fontSize: "0.85rem", color: "#666" }}>{TEXTO_CONSENTIMIENTO}</p>
          {tieneSesion ? (
            <button onClick={onAceptarConSesion} disabled={aceptando}>
              Aceptar la invitación
            </button>
          ) : (
            <form method="POST" action={`${API_BASE_URL}/auth/google/inicio`}>
              <input type="hidden" name="invitacion_token" value={token} />
              <input type="hidden" name="destino" value="/cursos" />
              <button type="submit">Aceptar la invitación</button>
            </form>
          )}
        </>
      )}
    </main>
  );
}
