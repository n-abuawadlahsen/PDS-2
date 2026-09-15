import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  confirmarCallbackGithub,
  type CallbackInstalacionResultado,
} from "../lib/api";
import { detalleLegible, mensajeError } from "../lib/errores";
import { Aviso, Cargando, ErrorCarga } from "../components/ui";
export function GithubRetorno() {
  const [params] = useSearchParams();
  const [resultado, setResultado] =
    useState<CallbackInstalacionResultado | null>(null);
  const [error, setError] = useState<string | null>(null);
  const canje = useRef<ReturnType<typeof confirmarCallbackGithub> | null>(null);
  useEffect(() => {
    let vigente = true;
    const state = params.get("state");
    const installationId = params.get("installation_id");
    if (!state) {
      setError(
        "GitHub no entregó la información de retorno. Vuelve a la configuración del curso para iniciar la instalación.",
      );
      return;
    }
    // Conserva la misma promesa durante el doble efecto de StrictMode. Nunca canjea dos veces.
    canje.current ??= confirmarCallbackGithub({
      state,
      installation_id: installationId ? Number(installationId) : undefined,
      setup_action: params.get("setup_action") ?? undefined,
    });
    canje.current
      .then((r) => {
        if (!vigente) return;
        if (r.ok) setResultado(r.cuerpo as CallbackInstalacionResultado);
        else
          setError(
            detalleLegible(r.cuerpo) ||
              "No pudimos completar la vinculación con GitHub.",
          );
      })
      .catch((e) => {
        if (vigente) setError(mensajeError(e));
      });
    return () => {
      vigente = false;
    };
  }, [params]);
  const textos: Record<CallbackInstalacionResultado["resultado"], string> = {
    VINCULADO: `La organización ${resultado?.org_login ?? ""} quedó vinculada. Continúa verificando las conexiones del curso.`,
    SOLICITUD_PENDIENTE:
      "La solicitud de instalación está pendiente de aprobación por un propietario de la organización. Revisa la configuración después de que la apruebe.",
    SIN_INSTALLATION_ID:
      "GitHub no devolvió una instalación. Si cancelaste el proceso, puedes iniciarlo nuevamente desde el curso.",
    STATE_INVALIDO:
      "El enlace de retorno venció o ya se utilizó. Revisa las instalaciones sin curso desde la configuración.",
  };
  return (
    <section className="panel">
      <h1>Conexión con GitHub</h1>
      {error && <ErrorCarga error={error} />}
      {!error && !resultado && <Cargando texto="Comprobando la instalación…" />}
      {resultado && (
        <Aviso
          tipo={resultado.resultado === "VINCULADO" ? "success" : "warning"}
        >
          {textos[resultado.resultado]}
        </Aviso>
      )}
      <Link
        className="button primary"
        to={
          resultado?.curso_id
            ? `/cursos/${resultado.curso_id}/vinculacion`
            : "/cursos"
        }
      >
        {resultado?.curso_id ? "Volver a configuración" : "Volver a mis cursos"}
      </Link>
    </section>
  );
}
