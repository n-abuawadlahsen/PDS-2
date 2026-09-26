import { useEffect, useState } from "react";
import { cambiarReglaMapeo, obtenerReglaMapeo, type ReglaComunicacion } from "../lib/api";

/** Interruptor del recordatorio de cuenta de GitHub (S11.6.1): es el único
 * aviso de alcance curso y vive en Personas. */
export function RecordatorioMapeo({ cursoId }: { cursoId: string }) {
  const [regla, setRegla] = useState<ReglaComunicacion | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    obtenerReglaMapeo(cursoId).then(setRegla);
  }, [cursoId]);

  if (!regla) return null;
  return (
    <p>
      <label>
        <input
          type="checkbox"
          checked={regla.activa}
          onChange={async () => {
            const r = await cambiarReglaMapeo(cursoId, !regla.activa);
            if (!r.ok) setError(r.error);
            setRegla(await obtenerReglaMapeo(cursoId));
          }}
        />{" "}
        Recordar por Canvas a quien no ha registrado su cuenta de GitHub (hasta tres veces, nunca dos días seguidos)
      </label>
      {error && <span style={{ color: "#a00" }}> {error}</span>}
    </p>
  );
}
