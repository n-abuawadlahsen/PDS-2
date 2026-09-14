import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { API_BASE_URL } from "../lib/api";
import { Aviso } from "../components/ui";
function correoDelToken(token: string): string | null {
  try {
    const json: unknown = JSON.parse(
      atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")),
    );
    return json &&
      typeof json === "object" &&
      "email" in json &&
      typeof json.email === "string"
      ? json.email
      : null;
  } catch {
    return null;
  }
}
export function Confirmar() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const [enviando, setEnviando] = useState(false);
  return (
    <section className="panel">
      <h1>Confirmar acceso</h1>
      <p>
        Tu navegador necesita una confirmación adicional para completar el
        acceso.
      </p>
      {token ? (
        <>
          <p>
            Vas a entrar como{" "}
            <strong>{correoDelToken(token) ?? "tu cuenta de Google"}</strong>.
          </p>
          <form
            method="POST"
            action={`${API_BASE_URL}/auth/confirmar`}
            onSubmit={() => setEnviando(true)}
          >
            <input type="hidden" name="token" value={token} />
            <button className="primary" disabled={enviando}>
              {enviando ? "Confirmando…" : "Confirmar y entrar"}
            </button>
          </form>
        </>
      ) : (
        <Aviso tipo="error">
          Falta la información de confirmación. Inicia el acceso nuevamente.
        </Aviso>
      )}
      <p className="help">
        <Link to="/acceso">Volver al acceso</Link>
      </p>
    </section>
  );
}
