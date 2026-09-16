import { Link, useSearchParams } from "react-router-dom";
import { FormularioAcceso } from "../components/FormularioAcceso";
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
          <FormularioAcceso action="/auth/confirmar" texto="Confirmar y entrar">
            <input type="hidden" name="token" value={token} />
          </FormularioAcceso>
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
