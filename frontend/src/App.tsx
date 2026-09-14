import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
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

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/acceso" replace />} />
        <Route path="/acceso" element={<Acceso />} />
        <Route path="/confirmar" element={<Confirmar />} />
        <Route path="/cursos" element={<Cursos />} />
        <Route path="/cursos/:cursoId/equipo" element={<Equipo />} />
        <Route path="/cursos/:cursoId/vinculacion" element={<Vinculacion />} />
        <Route path="/cursos/:cursoId/verificacion" element={<Checklist />} />
        <Route path="/cursos/:cursoId/personas" element={<Personas />} />
        <Route path="/cursos/:cursoId/pendientes" element={<Pendientes />} />
        <Route path="/cursos/:cursoId/tareas" element={<Tareas />} />
        <Route path="/cursos/:cursoId/tareas/:tareaId" element={<Tarea />} />
        <Route path="/vinculacion/github/retorno" element={<GithubRetorno />} />
        <Route path="/invitaciones/:token" element={<InvitacionPublica />} />
        <Route path="/perfil" element={<PerfilPagina />} />
      </Routes>
    </BrowserRouter>
  );
}
