import { lazy } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import {
  AccesoArea,
  Estructura,
  LayoutAutenticado,
  LayoutCurso,
  Publico,
} from "./components/Layout";
import { Confirmaciones } from "./components/ui";
import { Acceso } from "./paginas/Acceso";
import { Checklist } from "./paginas/Checklist";
import { Confirmar } from "./paginas/Confirmar";
import { Cursos } from "./paginas/Cursos";
import { Equipo } from "./paginas/Equipo";
import { GithubRetorno } from "./paginas/GithubRetorno";
import { InvitacionPublica } from "./paginas/InvitacionPublica";
import { PerfilPagina } from "./paginas/Perfil";
import { Pendientes } from "./paginas/Pendientes";
import { Tareas } from "./paginas/Tareas";
import { Ajustes, Vinculacion } from "./paginas/Vinculacion";
import { InicioCurso } from "./paginas/InicioCurso";
import { Baja } from "./paginas/Baja";
import { MisNotificaciones } from "./paginas/MisNotificaciones";

const Correccion = lazy(() =>
  import("./paginas/Correccion").then((modulo) => ({
    default: modulo.Correccion,
  })),
);
const CorreccionSujeto = lazy(() =>
  import("./paginas/CorreccionSujeto").then((modulo) => ({
    default: modulo.CorreccionSujeto,
  })),
);
const Comunicaciones = lazy(() =>
  import("./paginas/Comunicaciones").then((modulo) => ({
    default: modulo.Comunicaciones,
  })),
);
const Tarea = lazy(() =>
  import("./paginas/Tarea").then((modulo) => ({ default: modulo.Tarea })),
);
const EntregasTarea = lazy(() =>
  import("./paginas/EntregasTarea").then((modulo) => ({
    default: modulo.EntregasTarea,
  })),
);
const Informes = lazy(() =>
  import("./paginas/Informes").then((modulo) => ({ default: modulo.Informes })),
);
const RepositorioTimeline = lazy(() =>
  import("./paginas/RepositorioTimeline").then((modulo) => ({
    default: modulo.RepositorioTimeline,
  })),
);
const Seguimiento = lazy(() =>
  import("./paginas/Seguimiento").then((modulo) => ({
    default: modulo.Seguimiento,
  })),
);
const Personas = lazy(() =>
  import("./paginas/Personas").then((modulo) => ({ default: modulo.Personas })),
);

export function App() {
  return (
    <BrowserRouter>
      <Confirmaciones>
        <Routes>
          <Route path="/" element={<Navigate to="/cursos" replace />} />
          <Route element={<Publico />}>
            <Route path="/acceso" element={<Acceso />} />
            <Route path="/confirmar" element={<Confirmar />} />
            <Route
              path="/vinculacion/github/retorno"
              element={<GithubRetorno />}
            />
            <Route
              path="/invitaciones/:token"
              element={<InvitacionPublica />}
            />
            <Route path="/baja/:token" element={<Baja />} />
            <Route
              path="*"
              element={
                <section className="panel">
                  <h1>Página no encontrada</h1>
                  <p>El enlace no corresponde a una pantalla disponible.</p>
                  <Link className="button primary" to="/cursos">
                    Volver a mis cursos
                  </Link>
                </section>
              }
            />
          </Route>
          <Route element={<LayoutAutenticado />}>
            <Route element={<Estructura />}>
              <Route path="/cursos" element={<Cursos />} />
              <Route path="/perfil" element={<PerfilPagina />} />
            </Route>
            <Route path="/cursos/:cursoId" element={<LayoutCurso />}>
              <Route index element={<InicioCurso />} />
              <Route path="equipo" element={<Equipo />} />
              <Route
                path="ajustes"
                element={
                  <AccesoArea permiso="curso.administrar">
                    <Ajustes />
                  </AccesoArea>
                }
              />
              <Route
                path="vinculacion"
                element={
                  <AccesoArea permiso="curso.administrar">
                    <Vinculacion />
                  </AccesoArea>
                }
              />
              <Route
                path="verificacion"
                element={
                  <AccesoArea permiso="curso.administrar">
                    <Checklist />
                  </AccesoArea>
                }
              />
              <Route path="personas" element={<Personas />} />
              <Route path="pendientes" element={<Pendientes />} />
              <Route path="tareas" element={<Tareas />} />
              <Route path="tareas/:tareaId" element={<Tarea />} />
              <Route
                path="tareas/:tareaId/entregas"
                element={
                  <AccesoArea capacidad="versiones_entrega">
                    <EntregasTarea />
                  </AccesoArea>
                }
              />
              <Route
                path="tareas/:tareaId/repos/:repoId"
                element={
                  <AccesoArea capacidad="repositorio_timeline">
                    <RepositorioTimeline />
                  </AccesoArea>
                }
              />
              <Route
                path="seguimiento"
                element={
                  <AccesoArea capacidad="tablero_actividad">
                    <Seguimiento />
                  </AccesoArea>
                }
              />
              <Route
                path="informes"
                element={
                  <AccesoArea capacidad="informe_diario">
                    <Informes />
                  </AccesoArea>
                }
              />
              <Route
                path="informes/:fecha"
                element={
                  <AccesoArea capacidad="informe_diario">
                    <Informes />
                  </AccesoArea>
                }
              />
              <Route
                path="mis-notificaciones"
                element={
                  <AccesoArea capacidad="mis_notificaciones">
                    <MisNotificaciones />
                  </AccesoArea>
                }
              />
              <Route
                path="comunicaciones"
                element={
                  <AccesoArea capacidad="comunicaciones_automaticas">
                    <Comunicaciones />
                  </AccesoArea>
                }
              />
              <Route
                path="correccion"
                element={
                  <AccesoArea capacidad="correccion">
                    <Correccion />
                  </AccesoArea>
                }
              />
              <Route
                path="correccion/:entregaId/:sujetoId"
                element={
                  <AccesoArea capacidad="correccion">
                    <CorreccionSujeto />
                  </AccesoArea>
                }
              />
            </Route>
          </Route>
        </Routes>
      </Confirmaciones>
    </BrowserRouter>
  );
}
