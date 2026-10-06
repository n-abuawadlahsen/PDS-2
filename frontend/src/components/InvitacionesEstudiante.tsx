import { useState } from "react";
import { useCurso } from "./Layout";
import { Cargando, ErrorCarga, Estado, Mensajes, useConfirmar } from "./ui";
import { EstadoTrabajo } from "./EstadoTrabajo";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import { consultarFinal, fechaFinal } from "../lib/apiFinal";

type Invitacion = {
  acceso_id: string;
  repositorio: string;
  estado: string;
  reenvios: number;
  ultimo_reenvio_en: string | null;
  proximo_reenvio_en: string | null;
  puede_solicitar: boolean;
};
export function InvitacionesEstudiante({
  estudianteId,
}: {
  estudianteId: string;
}) {
  const { curso, puede } = useCurso();
  const [abierto, setAbierto] = useState(false);
  const [trabajo, setTrabajo] = useState<string | null>(null);
  const ruta = `/api/cursos/${curso.id}/personas/${estudianteId}/invitaciones-github`;
  const consulta = useConsulta(`${ruta}:${abierto}`, (signal) =>
    abierto
      ? consultarFinal<Invitacion[]>(ruta, { signal })
      : Promise.resolve([]),
  );
  const op = useOperacion();
  const confirmar = useConfirmar();
  return (
    <details onToggle={(e) => setAbierto(e.currentTarget.open)}>
      <summary>Invitaciones de GitHub</summary>
      {consulta.cargando && <Cargando />}
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      <Mensajes {...op} />
      {trabajo && (
        <EstadoTrabajo
          ruta={`/api/cursos/${curso.id}/trabajos/${trabajo}`}
          zona={curso.zona_horaria}
          alTerminar={() => {
            setTrabajo(null);
            consulta.recargar();
          }}
        />
      )}
      {abierto &&
        !consulta.cargando &&
        !consulta.error &&
        !consulta.datos?.length && <p>No hay invitaciones registradas.</p>}
      {consulta.datos?.map((i) => (
        <div key={i.acceso_id}>
          <strong>{i.repositorio}</strong> <Estado valor={i.estado} />
          <p className="help">
            Reenvíos: {i.reenvios}/3. Último:{" "}
            {fechaFinal(i.ultimo_reenvio_en, curso.zona_horaria)}. Próximo:{" "}
            {i.proximo_reenvio_en
              ? fechaFinal(i.proximo_reenvio_en, curso.zona_horaria)
              : "Disponible si la invitación desapareció o expiró"}
            .
          </p>
          {puede("mapeo.editar") && (
            <button
              disabled={
                !i.puede_solicitar ||
                op.ocupado ||
                Boolean(trabajo) ||
                Boolean(
                  i.proximo_reenvio_en &&
                  Date.parse(i.proximo_reenvio_en) > Date.now(),
                )
              }
              onClick={() => {
                void op.ejecutar(async () => {
                  if (
                    !(await confirmar({
                      titulo: "Comprobar y reenviar invitación",
                      descripcion:
                        "Primero se comprobará si ya tiene acceso o si la invitación sigue vigente. Sólo se reenviará si expiró o desapareció, con un máximo de tres reenvíos separados por 24 horas.",
                      accion: "Solicitar comprobación",
                    }))
                  )
                    return;
                  const r = await consultarFinal<{ trabajo_id: string }>(
                    `${ruta}/${i.acceso_id}/reenviar`,
                    { method: "POST" },
                  );
                  setTrabajo(r.trabajo_id);
                }, "Comprobación solicitada.");
              }}
            >
              Comprobar y reenviar invitación
            </button>
          )}
        </div>
      ))}
    </details>
  );
}
