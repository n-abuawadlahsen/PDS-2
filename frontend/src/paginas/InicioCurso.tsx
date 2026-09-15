import { Link } from "react-router-dom";
import {
  listarTareas,
  obtenerPersonas,
  obtenerEstadoVinculacionCanvas,
  obtenerEstadoVinculacionGithub,
  obtenerUltimaVerificacion,
} from "../lib/api";
import { useConsulta } from "../hooks/useConsulta";
import { useCurso } from "../components/Layout";
import { Cabecera, Cargando, ErrorCarga } from "../components/ui";

import {
  ProgresoConfiguracion,
  type PasoConfiguracion,
} from "../components/ProgresoConfiguracion";
export function InicioCurso() {
  const { curso, puede } = useCurso();
  const consulta = useConsulta(`inicio-${curso.id}`, async (signal) => {
    const [canvas, github, verificacion, personas, tareas] =
      await Promise.allSettled([
        obtenerEstadoVinculacionCanvas(curso.id, signal),
        obtenerEstadoVinculacionGithub(curso.id, signal),
        obtenerUltimaVerificacion(curso.id, signal),
        obtenerPersonas(curso.id, signal),
        listarTareas(curso.id, signal),
      ]);
    return { canvas, github, verificacion, personas, tareas };
  });
  const d = consulta.datos;
  const credenciales = d?.canvas.status === "fulfilled" ? d.canvas.value : null;
  const github = d?.github.status === "fulfilled" ? d.github.value : null;
  const verificaciones =
    d?.verificacion.status === "fulfilled"
      ? d.verificacion.value.filter((i) => i.item && !i.item.includes("bis"))
      : null;
  const personas = d?.personas.status === "fulfilled" ? d.personas.value : null;
  const tareas = d?.tareas.status === "fulfilled" ? d.tareas.value : null;
  const verificadas =
    personas?.estudiantes.filter((e) => e.mapeo.estado === "VIGENTE").length ??
    0;
  const pasos: PasoConfiguracion[] = [
    {
      nombre: "Curso creado",
      estado: "COMPLETADO",
      detalle: `${curso.codigo} · ${curso.periodo}`,
      ruta: "",
    },
    {
      nombre: "Vincular Canvas",
      estado: !credenciales
        ? "NO_VERIFICADO"
        : credenciales.some((c) => c.estado === "VALIDA")
          ? "COMPLETADO"
          : credenciales.length
            ? "ATENCION"
            : "PENDIENTE",
      detalle: !credenciales
        ? "No pudimos consultar las credenciales."
        : credenciales.some((c) => c.estado === "VALIDA")
          ? "Hay una credencial válida registrada."
          : "Un profesor debe añadir su credencial personal.",
      ruta: "/vinculacion",
      permiso: "curso.administrar",
    },
    {
      nombre: "Vincular GitHub",
      estado: !github
        ? "NO_VERIFICADO"
        : github.org_login
          ? "COMPLETADO"
          : "PENDIENTE",
      detalle: !github
        ? "No pudimos consultar la organización."
        : github.org_login
          ? `Organización: ${github.org_login}`
          : "Conecta la organización que alojará los repositorios.",
      ruta: "/vinculacion",
      permiso: "curso.administrar",
    },
    {
      nombre: "Verificar conexiones",
      estado: !verificaciones
        ? "NO_VERIFICADO"
        : verificaciones.some((i) => i.resultado === "BLOQUEANTE")
          ? "ATENCION"
          : verificaciones.length < 19 ||
              verificaciones.some((i) => i.resultado === "NO_VERIFICADO")
            ? "NO_VERIFICADO"
            : verificaciones.some((i) => i.resultado === "ADVERTENCIA")
              ? "ATENCION"
              : "COMPLETADO",
      detalle: verificaciones
        ? `${verificaciones.length} de 19 comprobaciones registradas. Revisa advertencias y verificaciones manuales.`
        : "No pudimos consultar la verificación.",
      ruta: "/verificacion",
      permiso: "curso.administrar",
    },
    {
      nombre: "Revisar estudiantes y cuentas",
      estado: !personas?.roster_sincronizado_en
        ? "NO_VERIFICADO"
        : verificadas < personas.estudiantes.length
          ? "ATENCION"
          : "COMPLETADO",
      detalle: personas
        ? `${verificadas} de ${personas.estudiantes.length} estudiantes con cuenta verificada. Los demás pueden completar su información después.`
        : "No pudimos consultar los estudiantes.",
      ruta: "/personas",
      permiso: "mapeo.editar",
    },
    {
      nombre: "Configurar y activar una tarea",
      estado: !tareas
        ? "NO_VERIFICADO"
        : tareas.some((t) => t.estado === "ACTIVA")
          ? "COMPLETADO"
          : "PENDIENTE",
      detalle: tareas
        ? `${tareas.length} ${tareas.length === 1 ? "tarea registrada" : "tareas registradas"}. La activación inicia la creación automática de repositorios.`
        : "No pudimos consultar las tareas.",
      ruta: "/tareas",
      permiso: "tarea.administrar",
    },
  ];
  // La información faltante de un estudiante no bloquea configurar tareas.
  const siguiente =
    pasos
      .slice(1)
      .find((p) => p.estado !== "COMPLETADO" && p.ruta !== "/personas") ??
    pasos.find((p) => p.estado !== "COMPLETADO");
  return (
    <>
      <Cabecera
        titulo={curso.nombre}
        descripcion={`${curso.codigo} · ${curso.periodo} · ${curso.zona_horaria}`}
        acciones={
          <button onClick={consulta.recargar} disabled={consulta.cargando}>
            Actualizar resumen
          </button>
        }
      />
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {!d ? (
        <Cargando />
      ) : (
        <>
          <section className="panel next-step">
            <p className="eyebrow">Siguiente paso</p>
            <h2>
              {siguiente
                ? siguiente.nombre
                : "Revisa el progreso de tus repositorios"}
            </h2>
            <p>
              {siguiente?.detalle ??
                "Las tareas activadas crean sus repositorios automáticamente. Consulta el estado y los accesos en cada tarea."}
            </p>
            <div className="actions">
              {siguiente?.permiso && !puede(siguiente.permiso) ? (
                <p className="help">
                  Un miembro del equipo con permiso debe completar este paso.
                  Puedes consultar Personas y Tareas.
                </p>
              ) : (
                <Link
                  className="button primary"
                  to={`/cursos/${curso.id}${siguiente?.ruta ?? "/tareas"}`}
                >
                  {siguiente ? "Revisar este paso" : "Ver tareas"}
                </Link>
              )}
            </div>
          </section>
          <div className="two-columns">
            <section className="panel">
              <h2>Preparación del curso</h2>
              <ProgresoConfiguracion cursoId={curso.id} pasos={pasos} />
            </section>
            <div className="stack">
              <section className="panel">
                <h2>Personas y tareas</h2>
                <p>
                  {personas
                    ? `${verificadas} de ${personas.estudiantes.length} estudiantes con cuenta de GitHub verificada.`
                    : "Estudiantes: información no disponible."}
                </p>
                <p>
                  {tareas
                    ? `${tareas.length} ${tareas.length === 1 ? "tarea disponible" : "tareas disponibles"}.`
                    : "Tareas: información no disponible."}
                </p>
                <div className="actions">
                  <Link to={`/cursos/${curso.id}/personas`}>Ver personas</Link>
                  <Link to={`/cursos/${curso.id}/tareas`}>Ver tareas</Link>
                </div>
              </section>
              <section className="panel">
                <h2>El proceso continúa solo</h2>
                <p>
                  Al activar una tarea, cada estudiante recibe su repositorio
                  cuando su información está completa. Una cuenta pendiente no
                  detiene a los demás.
                </p>
                <Link to={`/cursos/${curso.id}/pendientes`}>
                  Revisar pendientes
                </Link>
              </section>
            </div>
          </div>
        </>
      )}
    </>
  );
}
