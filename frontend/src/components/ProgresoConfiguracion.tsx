import { Link } from "react-router-dom";
import { Estado } from "./ui";
export interface PasoConfiguracion {
  nombre: string;
  estado: "COMPLETADO" | "PENDIENTE" | "ATENCION" | "NO_VERIFICADO";
  detalle: string;
  ruta: string;
  permiso?: string;
}
/** Presentación del recorrido; quien carga los datos decide los estados, nunca los clics. */
export function ProgresoConfiguracion({
  cursoId,
  pasos,
}: {
  cursoId: string;
  pasos: PasoConfiguracion[];
}) {
  return (
    <ol className="progress-list">
      {pasos.map((p) => (
        <li key={p.nombre}>
          <span className="step-number" aria-hidden="true" />
          <div className="step-content">
            <Link to={`/cursos/${cursoId}${p.ruta}`}>{p.nombre}</Link>
            <p>{p.detalle}</p>
          </div>
          <span className="step-state">
            <Estado
              valor={p.estado}
              texto={
                {
                  COMPLETADO: "Completado",
                  PENDIENTE: "Pendiente",
                  ATENCION: "Requiere atención",
                  NO_VERIFICADO: "Sin verificar",
                }[p.estado]
              }
            />
          </span>
        </li>
      ))}
    </ol>
  );
}
