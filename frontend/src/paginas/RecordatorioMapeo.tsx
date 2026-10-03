import {
  apiFetch,
  cambiarReglaMapeo,
  type ReglaComunicacion,
} from "../lib/api";
import { comprobar } from "../lib/errores";
import { useCurso, useSesion } from "../components/Layout";
import { Cargando, ErrorCarga, Mensajes, useConfirmar } from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";

export function RecordatorioMapeo({ cursoId }: { cursoId: string }) {
  const { puede } = useCurso();
  const { capacidades } = useSesion();
  const disponible = capacidades?.banderas.includes(
    "comunicaciones_automaticas",
  );
  const consulta = useConsulta(
    `recordatorio-mapeo-${cursoId}-${disponible}`,
    async (signal) => {
      if (!disponible) return null;
      const respuesta = await apiFetch(
        `/api/cursos/${cursoId}/comunicaciones-curso/recordatorio-mapeo`,
        { signal },
      );
      await comprobar(respuesta);
      return respuesta.json() as Promise<ReglaComunicacion>;
    },
  );
  const op = useOperacion();
  const confirmar = useConfirmar();
  if (!disponible) return null;
  const regla = consulta.datos;
  return (
    <section className="panel">
      <h2>Recordatorios de cuentas pendientes</h2>
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {!regla ? (
        !consulta.error && <Cargando />
      ) : (
        <>
          <label className="check">
            <input
              type="checkbox"
              checked={regla.activa}
              disabled={!puede("comunicacion.enviar") || op.ocupado}
              onChange={async () => {
                const activa = !regla.activa;
                if (
                  !activa &&
                  regla.advertencia_al_apagar &&
                  !(await confirmar({
                    titulo: "Desactivar recordatorios",
                    descripcion: regla.advertencia_al_apagar,
                    accion: "Desactivar",
                  }))
                )
                  return;
                void op.ejecutar(
                  async () => {
                    const r = await cambiarReglaMapeo(cursoId, activa);
                    if (!r.ok)
                      throw new Error(
                        r.error ?? "No pudimos cambiar el recordatorio.",
                      );
                    consulta.actualizar({ ...regla, activa });
                  },
                  activa
                    ? "Recordatorios automáticos activados."
                    : "Recordatorios automáticos desactivados.",
                );
              }}
            />
            Recordar por Canvas a quien no ha registrado su cuenta de GitHub
          </label>
          <p className="help">
            Hasta tres recordatorios automáticos por estudiante, nunca dos días
            seguidos.
          </p>
          {!puede("comunicacion.enviar") && (
            <p className="help">
              Necesitas el permiso Enviar comunicaciones para cambiar esta
              preferencia.
            </p>
          )}
          <details>
            <summary>Ver contenido del recordatorio</summary>
            <strong>{regla.vista_previa_asunto}</strong>
            <p className="preserve-lines">{regla.vista_previa_cuerpo}</p>
          </details>
        </>
      )}
      <Mensajes {...op} />
    </section>
  );
}
