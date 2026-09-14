import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { confirmarCallbackGithub, type CallbackInstalacionResultado } from "../lib/api";

/**
 * URL de retorno unica de la GitHub App (S4.6.1): GitHub no sabe de que curso
 * se trata, por eso el `state` firmado es lo unico que resuelve el curso, y
 * esta pantalla no vive bajo `/cursos/:id`.
 */
export function GithubRetorno() {
  const [params] = useSearchParams();
  const [resultado, setResultado] = useState<CallbackInstalacionResultado | null>(null);
  const [error, setError] = useState<string | null>(null);
  // El `jti` del state es de un solo uso (A-058): un segundo canje del mismo
  // state (p. ej. el doble efecto de StrictMode en desarrollo) falla igual
  // que uno caducado. Esta ref evita llamar al backend dos veces.
  const yaCanjeado = useRef(false);

  useEffect(() => {
    if (yaCanjeado.current) return;
    yaCanjeado.current = true;

    const state = params.get("state");
    if (!state) {
      setError("GitHub no envió ningún `state`. Volvé a intentar la instalación desde el curso.");
      return;
    }
    const installationId = params.get("installation_id");
    confirmarCallbackGithub({
      state,
      installation_id: installationId ? Number(installationId) : undefined,
      setup_action: params.get("setup_action") ?? undefined,
    }).then(({ ok, cuerpo }) => {
      if (ok) {
        setResultado(cuerpo as CallbackInstalacionResultado);
      } else {
        const detalle = (cuerpo as { detail?: unknown }).detail;
        setError(typeof detalle === "string" ? detalle : JSON.stringify(detalle));
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main style={{ maxWidth: 640, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Volviendo de GitHub…</h1>
      {error && <p role="alert">{error}</p>}
      {resultado?.resultado === "VINCULADO" && (
        <p role="status">
          Organización <strong>{resultado.org_login}</strong> vinculada. Equipo docente:{" "}
          <code>{resultado.equipo_docentes_slug}</code>.
        </p>
      )}
      {resultado?.resultado === "SOLICITUD_PENDIENTE" && (
        <p role="status">
          Pediste instalar la aplicación. Un owner de esa organización tiene que aprobarla. Te
          avisaremos en cuanto ocurra; podés cerrar esta página.
        </p>
      )}
      {resultado?.resultado === "SIN_INSTALLATION_ID" && (
        <p role="status">
          GitHub no nos devolvió ninguna instalación. Si cancelaste, podés volver a intentarlo.
        </p>
      )}
      {resultado?.resultado === "STATE_INVALIDO" && (
        <p role="alert">
          El enlace de retorno venció o no es válido. Si instalaste la App fuera del asistente,
          buscala en el bloque "Instalaciones sin curso" del paso 3.
        </p>
      )}
      {resultado?.curso_id && (
        <p>
          <Link to={`/cursos/${resultado.curso_id}/vinculacion`}>Volver al asistente de vinculación</Link>
        </p>
      )}
      {!resultado?.curso_id && (
        <p>
          <Link to="/cursos">Volver a mis cursos</Link>
        </p>
      )}
    </main>
  );
}
