import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { API_BASE_URL } from "../lib/api";
import { descripcionDeMotivo } from "../lib/mensajes";

/** S2.2.3: Safari en navegacion privada esta fuera de la matriz declarada (A-019). */
function esSafariPrivadaProbable(): boolean {
  const ua = navigator.userAgent;
  const esSafari = /^((?!chrome|android|crios|fxios).)*safari/i.test(ua);
  return esSafari;
}

export function Acceso() {
  const [parametros] = useSearchParams();
  const motivo = descripcionDeMotivo(parametros.get("motivo"));
  const avisoSafari = useMemo(esSafariPrivadaProbable, []);

  return (
    <main style={{ maxWidth: 480, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Proyecto 2</h1>

      {motivo && (
        <div role="alert" style={{ background: "#fee", padding: "1rem", marginBottom: "1rem" }}>
          <strong>{motivo.titulo}</strong>
          <p>{motivo.texto}</p>
        </div>
      )}

      {avisoSafari && (
        <p style={{ fontSize: "0.85rem", color: "#666" }}>
          Si estás en Safari en navegación privada, ese modo está fuera de la matriz de navegadores
          declarada. Te recomendamos abrir la aplicación en una ventana normal.
        </p>
      )}

      <form method="POST" action={`${API_BASE_URL}/auth/google/inicio`}>
        <button type="submit" style={{ padding: "0.75rem 1.5rem", fontSize: "1rem" }}>
          Entrar con Google
        </button>
      </form>
    </main>
  );
}
