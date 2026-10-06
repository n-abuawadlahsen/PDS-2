import type { CeldaCorreccion, MatrizCorreccion } from "../lib/api";
import { fechaFinal } from "../lib/apiFinal";
import { textoEstadoAcceso } from "../lib/textosTarea";
import { useCurso } from "./Layout";

const CAUSA = {
  SIN_ACCESO: "Sin acceso al repositorio",
  SIN_ATRIBUIR: "Hay commits pendientes de atribuir",
  SIN_COMMITS: "Sin commits atribuidos en la ventana observada",
};

export function AccesosCorreccion({
  accesos,
}: {
  accesos: MatrizCorreccion["sujetos"][number]["accesos"];
}) {
  const { curso } = useCurso();
  if (!accesos?.length) return null;
  return (
    <details className="help">
      <summary>Acceso de integrantes</summary>
      <ul>
        {accesos.map((a) => (
          <li key={a.estudiante_id}>
            {a.nombre}:{" "}
            {a.estado ? textoEstadoAcceso(a.estado) : "No comprobado"}
            {a.verificado_en && (
              <div>
                Comprobado {fechaFinal(a.verificado_en, curso.zona_horaria)}
              </div>
            )}
          </li>
        ))}
      </ul>
      <p>Estado actual del espejo; puede cambiar después del cierre.</p>
    </details>
  );
}

export function CausasParticipacion({
  causas,
}: {
  causas: CeldaCorreccion["causas_sin_participacion"];
}) {
  const { curso } = useCurso();
  return (
    <details className="help">
      <summary>Causas de participación registradas</summary>
      {causas?.length ? (
        <ul>
          {causas.map((c) => (
            <li key={c.estudiante_id}>
              {c.nombre}: {CAUSA[c.causa] ?? "Requiere revisión"}
              <div>
                Registrada {fechaFinal(c.registrada_en, curso.zona_horaria)}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p>
          No hay una causa registrada para esta entrega. Revisa el acceso y la
          evidencia antes de calificar.
        </p>
      )}
    </details>
  );
}
