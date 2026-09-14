import { useSearchParams } from "react-router-dom";
import { API_BASE_URL } from "../lib/api";

/** Decodifica solo para MOSTRAR el correo; la verificacion real es del backend. */
function correoDelToken(token: string): string | null {
  try {
    const payload = token.split(".")[1];
    const json = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    return typeof json.email === "string" ? json.email : null;
  } catch {
    return null;
  }
}

/**
 * Camino degradado de S2.2.2: "no es un error, es una confirmacion". Un clic
 * explicito de la persona completa el acceso. Se envia como una NAVEGACION de
 * formulario (POST real del navegador), no como `fetch`: asi el navegador
 * sigue el 302 de vuelta al frontend de forma nativa y aplica las cookies de
 * sesion que ese redirect trae, sin las complicaciones de CORS que tendria
 * seguir una cadena de redirecciones entre origenes distintos con `fetch`.
 */
export function Confirmar() {
  const [parametros] = useSearchParams();
  const token = parametros.get("token") ?? "";
  const correo = correoDelToken(token);

  return (
    <main style={{ maxWidth: 480, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Confirmar acceso</h1>
      <p>
        Tu navegador no devolvió la cookie de inicio de sesión (es normal en ventana privada). Vas a
        entrar como <strong>{correo ?? "esa cuenta de Google"}</strong>.
      </p>
      <form method="POST" action={`${API_BASE_URL}/auth/confirmar`}>
        <input type="hidden" name="token" value={token} />
        <button type="submit" disabled={!token}>
          Confirmar
        </button>
      </form>
    </main>
  );
}
