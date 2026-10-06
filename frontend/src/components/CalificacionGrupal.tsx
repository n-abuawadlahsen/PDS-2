import { useState } from "react";
import { useCurso } from "./Layout";
import { Aviso, ErrorCarga, Mensajes } from "./ui";
import { EstadoTrabajo } from "./EstadoTrabajo";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import { consultarFinal } from "../lib/apiFinal";

type Vista = {
  es_grupal: boolean;
  individual: boolean;
  puede_cambiar: boolean;
  motivo: string | null;
  enlace_canvas: string | null;
};
export function CalificacionGrupal({ entregaId }: { entregaId: string }) {
  const { curso, puede } = useCurso();
  const ruta = `/api/cursos/${curso.id}/entregas/${entregaId}/calificacion-individual`;
  const consulta = useConsulta(ruta, (signal) =>
    consultarFinal<Vista>(ruta, { signal }),
  );
  const op = useOperacion();
  const [trabajo, setTrabajo] = useState<string | null>(null);
  const [enCurso, setEnCurso] = useState(false);
  if (consulta.error)
    return <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />;
  const vista = consulta.datos;
  if (!vista?.es_grupal) return null;
  return (
    <section className="panel">
      <h2>Calificación del grupo en Canvas</h2>
      <p>
        {vista.individual
          ? "Canvas permite una nota por integrante."
          : "Canvas aplica una misma nota a todos los integrantes."}
      </p>
      <p>
        Esta opción se cambia en la configuración de la tarea en Canvas. La
        aplicación consulta ese ajuste al sincronizar y lo respeta al publicar.
      </p>
      <Mensajes {...op} />
      {vista.motivo && <Aviso>{vista.motivo}</Aviso>}
      <div className="actions">
        {!vista.individual &&
          vista.puede_cambiar &&
          vista.enlace_canvas &&
          puede("tarea.administrar") && (
            <a
              className="button"
              href={vista.enlace_canvas}
              target="_blank"
              rel="noreferrer"
            >
              Configurar calificación individual en Canvas
            </a>
          )}
        <button
          disabled={op.ocupado || enCurso || curso.estado === "ARCHIVADO"}
          onClick={() => {
            void op.ejecutar(async () => {
              const r = await consultarFinal<{ trabajo_id: string | null }>(
                `/api/cursos/${curso.id}/sincronizaciones`,
                { method: "POST" },
              );
              if (!r.trabajo_id)
                throw new Error("No se confirmó el trabajo de sincronización.");
              setTrabajo(r.trabajo_id);
              setEnCurso(true);
            }, "Sincronización solicitada. El ajuste se actualizará cuando termine el trabajo.");
          }}
        >
          Ya lo cambié en Canvas: sincronizar
        </button>
      </div>
      {trabajo && (
        <EstadoTrabajo
          key={trabajo}
          ruta={`/api/cursos/${curso.id}/trabajos/${trabajo}`}
          zona={curso.zona_horaria}
          alTerminar={(t) => {
            setEnCurso(false);
            if (t.estado === "OK") consulta.recargar();
          }}
        />
      )}
    </section>
  );
}
