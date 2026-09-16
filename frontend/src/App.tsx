import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import {
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
import { Personas } from "./paginas/Personas";
import { Tarea } from "./paginas/Tarea";
import { Tareas } from "./paginas/Tareas";
import { Vinculacion } from "./paginas/Vinculacion";
import { InicioCurso } from "./paginas/InicioCurso";

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
              <Route path="vinculacion" element={<Vinculacion />} />
              <Route path="verificacion" element={<Checklist />} />
              <Route path="personas" element={<Personas />} />
              <Route path="pendientes" element={<Pendientes />} />
              <Route path="tareas" element={<Tareas />} />
              <Route path="tareas/:tareaId" element={<Tarea />} />
            </Route>
          </Route>
        </Routes>
      </Confirmaciones>
    </BrowserRouter>
  );
}
