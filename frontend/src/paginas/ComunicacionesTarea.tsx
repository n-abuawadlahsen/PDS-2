import { useState } from "react";
import { Link } from "react-router-dom";
import {
  cambiarReglaTarea,
  obtenerReglasTarea,
  type ReglaComunicacion,
} from "../lib/api";
import { useCurso } from "../components/Layout";
import {
  Aviso,
  Cargando,
  ErrorCarga,
  Mensajes,
  Vacio,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";

export function ComunicacionesTarea({
  cursoId,
  tareaId,
}: {
  cursoId: string;
  tareaId: string;
}) {
  const consulta = useConsulta(`reglas:${cursoId}:${tareaId}`, () =>
    obtenerReglasTarea(cursoId, tareaId),
  );
  const { puede, curso } = useCurso();
  const op = useOperacion();
  const confirmar = useConfirmar();
  const [vista, setVista] = useState<string | null>(null);
  async function cambiar(r: ReglaComunicacion) {
    if (
      r.activa &&
      r.advertencia_al_apagar &&
      !(await confirmar({
        titulo: `Desactivar «${r.titulo}»`,
        descripcion: r.advertencia_al_apagar,
        accion: "Desactivar aviso",
      }))
    )
      return;
    await op.ejecutar(async () => {
      const resultado = await cambiarReglaTarea(
        cursoId,
        tareaId,
        r.evento,
        !r.activa,
      );
      if (!resultado.ok)
        throw new Error(resultado.error || "No se pudo actualizar la regla.");
      consulta.recargar();
    }, "Regla de comunicación actualizada.");
  }
  return (
    <section className="panel">
      <h2>Comunicaciones automáticas</h2>
      <p className="help">
        Como máximo tres avisos automáticos por estudiante al día, entre las
        08:00 y las 21:00 ({curso.zona_horaria}).
      </p>
      {!puede("comunicacion.enviar") && (
        <Aviso>
          Tu permiso permite consultar estos avisos. El equipo con permiso para
          enviar comunicaciones puede modificarlos.
        </Aviso>
      )}
      <Mensajes error={op.error} mensaje={op.mensaje} />
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {!consulta.datos ? (
        !consulta.error && <Cargando />
      ) : consulta.datos.length === 0 ? (
        <Vacio>
          No hay reglas de comunicación disponibles para esta tarea.
        </Vacio>
      ) : (
        <>
          {consulta.datos.some(
            (r) => r.evento === "repositorio_disponible" && !r.activa,
          ) && (
            <Aviso tipo="warning">
              Los avisos de repositorio disponible están desactivados.
            </Aviso>
          )}
          <ul className="resource-list">
            {consulta.datos.map((r) => (
              <li key={r.evento}>
                <div className="actions">
                  <label>
                    <input
                      type="checkbox"
                      checked={r.activa}
                      disabled={!puede("comunicacion.enviar") || op.ocupado}
                      onChange={() => cambiar(r)}
                    />{" "}
                    {r.titulo}
                  </label>
                  <button
                    onClick={() =>
                      setVista(vista === r.evento ? null : r.evento)
                    }
                    aria-expanded={vista === r.evento}
                  >
                    {vista === r.evento ? "Ocultar texto" : "Ver texto"}
                  </button>
                </div>
                <p className="help">
                  {r.destinatarios_hoy !== null
                    ? `${r.destinatarios_hoy} destinatarios hoy.`
                    : "El alcance se determina cuando ocurre el evento."}
                  {!r.por_defecto && " Desactivado por defecto."}
                </p>
                {vista === r.evento && (
                  <div className="panel">
                    {r.vista_previa_con_ejemplo && (
                      <Aviso>Esta previsualización usa datos de ejemplo.</Aviso>
                    )}
                    <strong>{r.vista_previa_asunto}</strong>
                    <pre
                      style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}
                    >
                      {r.vista_previa_cuerpo}
                    </pre>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
      <Link to={`/cursos/${cursoId}/comunicaciones?tarea_id=${tareaId}`}>
        Ver el historial de esta tarea
      </Link>
    </section>
  );
}
