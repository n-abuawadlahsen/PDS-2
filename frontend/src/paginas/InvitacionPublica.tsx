import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  API_BASE_URL,
  aceptarInvitacionConSesion,
  obtenerInvitacionPublica,
  obtenerPerfil,
} from "../lib/api";
import { comprobar } from "../lib/errores";
import { PERMISOS_CONCEDIBLES } from "../lib/permisos";
import {
  Aviso,
  Cargando,
  ErrorCarga,
  Estado,
  Mensajes,
  etiqueta,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
const ERRORES: Record<string, string> = {
  CORREO_NO_COINCIDE:
    "La cuenta actual no coincide con la destinataria. Vuelve a entrar con la cuenta invitada.",
  EXPIRADA: "Esta invitación venció. Solicita una nueva al profesor.",
  REVOCADA: "Esta invitación fue revocada.",
  YA_ACEPTADA: "Esta invitación ya fue aceptada.",
};
export function InvitacionPublica() {
  const { token = "" } = useParams();
  const [params] = useSearchParams();
  const op = useOperacion();
  const [consiento, setConsiento] = useState(false);
  const [entrando, setEntrando] = useState(false);
  const c = useConsulta(`invitacion-${token}`, async (signal) => {
    const [invitacion, perfil] = await Promise.all([
      obtenerInvitacionPublica(token, signal),
      obtenerPerfil(signal),
    ]);
    return { invitacion, perfil };
  });
  if (!c.datos)
    return (
      <section className="panel">
        <h1>Invitación al curso</h1>
        {c.error ? (
          <ErrorCarga error={c.error} reintentar={c.recargar} />
        ) : (
          <Cargando />
        )}
      </section>
    );
  const { invitacion: i, perfil } = c.datos;
  const pendiente = i.estado === "PENDIENTE";
  return (
    <section className="panel">
      <p className="eyebrow">Equipo docente</p>
      <h1>Invitación a {i.curso_nombre}</h1>
      <p>
        Destinatario: <strong>{i.email_enmascarado}</strong>
      </p>
      <p>
        Rol: <strong>{etiqueta(i.rol)}</strong>
      </p>
      <Estado valor={i.estado} />
      <p>
        Permisos:{" "}
        {i.rol === "PROFESOR"
          ? "Administración completa del curso"
          : [
              "Consultar el curso",
              ...PERMISOS_CONCEDIBLES.filter((p) =>
                i.permisos.includes(p.clave),
              ).map((p) => p.etiqueta),
            ].join(", ")}
        .
      </p>
      {params.get("error") && (
        <Aviso tipo="error">
          {ERRORES[params.get("error")!] ??
            "No pudimos completar la aceptación. Revisa tu cuenta e intenta nuevamente."}
        </Aviso>
      )}
      <Mensajes {...op} />
      {pendiente ? (
        <>
          <label className="check">
            <input
              type="checkbox"
              checked={consiento}
              onChange={(e) => setConsiento(e.target.checked)}
            />
            Al aceptar, doy mi consentimiento para que el equipo docente de este
            curso pueda leer todo el código de los repositorios del curso a
            través de la aplicación.
          </label>
          {perfil ? (
            <>
              <p className="help">Sesión actual: {perfil.email}.</p>
              <button
                className="primary"
                disabled={!consiento || op.ocupado}
                onClick={() =>
                  void op.ejecutar(async () => {
                    const r = await aceptarInvitacionConSesion(token);
                    if (!r.ok) {
                      const cuerpo = (await r
                        .clone()
                        .json()
                        .catch(() => null)) as { detail?: string } | null;
                      if (cuerpo?.detail && ERRORES[cuerpo.detail])
                        throw new Error(ERRORES[cuerpo.detail]);
                    }
                    await comprobar(r);
                    window.location.assign("/cursos");
                  })
                }
              >
                Aceptar invitación
              </button>
            </>
          ) : (
            <form
              method="POST"
              action={`${API_BASE_URL}/auth/google/inicio`}
              onSubmit={() => setEntrando(true)}
            >
              <input type="hidden" name="invitacion_token" value={token} />
              <input type="hidden" name="destino" value="/cursos" />
              <button className="primary" disabled={!consiento || entrando}>
                {entrando ? "Abriendo Google…" : "Aceptar con Google"}
              </button>
            </form>
          )}
          <p className="help">
            Entra con la cuenta personal Gmail a la que se envió esta
            invitación.
          </p>
        </>
      ) : (
        <Aviso>
          {ERRORES[i.estado === "ACEPTADA" ? "YA_ACEPTADA" : i.estado] ??
            "Esta invitación ya no está pendiente."}
        </Aviso>
      )}
      <p className="help">
        <Link to="/acceso">Entrar con otra cuenta de Google</Link> ·{" "}
        <Link to="/cursos">Ir a mis cursos</Link>
      </p>
    </section>
  );
}
