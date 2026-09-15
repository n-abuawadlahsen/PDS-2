import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  Link,
  NavLink,
  Outlet,
  useLocation,
  useParams,
} from "react-router-dom";
import {
  listarCursos,
  obtenerCapacidades,
  obtenerContexto,
  obtenerPerfil,
  type Capacidades,
  type Contexto,
  type Curso,
  type Perfil,
} from "../lib/api";
import { useConsulta } from "../hooks/useConsulta";
import { Aviso, Cargando, ErrorCarga, Estado } from "./ui";

type Sesion = {
  perfil: Perfil;
  cursos: Curso[];
  capacidades: Capacidades | null;
  recargar: () => void;
};
const SesionContext = createContext<Sesion | null>(null);
export function useSesion() {
  const s = useContext(SesionContext);
  if (!s) throw new Error("La sesión no está disponible");
  return s;
}
type CursoContexto = {
  curso: Curso;
  contexto: Contexto;
  puede: (permiso: string) => boolean;
  recargar: () => void;
};
const CursoContext = createContext<CursoContexto | null>(null);
export function useCurso() {
  const c = useContext(CursoContext);
  if (!c) throw new Error("El curso no está disponible");
  return c;
}

function Icono({ tipo }: { tipo: "cursos" | "cuenta" | "menu" }) {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      aria-hidden="true"
    >
      {tipo === "cursos" ? (
        <>
          <rect x="4" y="3" width="16" height="18" rx="2" />
          <path d="M8 3v18M12 8h5M12 12h5" />
        </>
      ) : tipo === "cuenta" ? (
        <>
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21v-2a8 8 0 0 1 16 0v2" />
        </>
      ) : (
        <path d="M4 6h16M4 12h16M4 18h16" />
      )}
    </svg>
  );
}
export function Publico({ children }: { children?: ReactNode }) {
  return (
    <div className="public-layout">
      <header className="public-header">
        <span className="public-mark">P2</span>
        <strong>Proyecto 2</strong>
        <span className="muted">Gestión docente</span>
      </header>
      <main className="public-main" id="contenido">
        {children ?? <Outlet />}
      </main>
      <footer className="public-footer">
        Canvas y GitHub · Un espacio para el equipo docente
      </footer>
    </div>
  );
}
export function LayoutAutenticado() {
  const [vencida, setVencida] = useState(false);
  const consulta = useConsulta("sesion", async (signal) => {
    const perfil = await obtenerPerfil(signal);
    if (!perfil) return null;
    const [cursos, capacidades] = await Promise.all([
      listarCursos(signal),
      obtenerCapacidades(signal).catch(() => null),
    ]);
    return { perfil, cursos, capacidades };
  });
  useEffect(() => {
    function acceso(event: Event) {
      if ((event as CustomEvent<{ status: number }>).detail.status === 401)
        setVencida(true);
    }
    window.addEventListener("pds2:acceso", acceso);
    return () => window.removeEventListener("pds2:acceso", acceso);
  }, []);
  if (vencida || (!consulta.cargando && !consulta.error && !consulta.datos))
    return (
      <Publico>
        <section className="panel">
          <h1>Vuelve a entrar</h1>
          <p>
            Necesitas una sesión activa para consultar tus cursos. Puedes entrar
            nuevamente con tu cuenta personal de Gmail.
          </p>
          <Link className="button primary" to="/acceso">
            Entrar con Google
          </Link>
        </section>
      </Publico>
    );
  if (!consulta.datos)
    return (
      <Publico>
        {consulta.error ? (
          <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
        ) : (
          <Cargando texto="Consultando tu sesión…" />
        )}
      </Publico>
    );
  return (
    <SesionContext.Provider
      value={{ ...consulta.datos, recargar: consulta.recargar }}
    >
      <Outlet />
    </SesionContext.Provider>
  );
}
const SECCIONES = [
  ["", "Inicio del curso"],
  ["vinculacion", "Configuración"],
  ["personas", "Personas"],
  ["pendientes", "Pendientes"],
  ["tareas", "Tareas"],
  ["equipo", "Equipo docente"],
] as const;
function EnlacesCurso({
  curso,
  cerrar,
}: {
  curso: Curso;
  cerrar?: () => void;
}) {
  const { pathname } = useLocation();
  return (
    <nav className="course-links" aria-label="Secciones del curso">
      {SECCIONES.map(([ruta, nombre]) => (
        <NavLink
          key={ruta}
          onClick={cerrar}
          end={!ruta}
          to={`/cursos/${curso.id}${ruta ? `/${ruta}` : ""}`}
          aria-current={
            ruta === "vinculacion" && pathname.endsWith("/verificacion")
              ? "page"
              : undefined
          }
        >
          {nombre}
        </NavLink>
      ))}
    </nav>
  );
}
export function Estructura({
  curso,
  children,
}: {
  curso?: Curso;
  children?: ReactNode;
}) {
  const { perfil } = useSesion();
  const { pathname } = useLocation();
  const menu = useRef<HTMLDialogElement>(null);
  const nombreSeccion = pathname.endsWith("/verificacion")
    ? "Verificación"
    : curso
      ? (SECCIONES.find(
          ([ruta]) => ruta && pathname.includes(`/${ruta}`),
        )?.[1] ?? "Inicio del curso")
      : pathname === "/perfil"
        ? "Mi perfil"
        : "Mis cursos";
  function cerrarMenu() {
    menu.current?.close();
  }
  useEffect(cerrarMenu, [pathname]);
  return (
    <div className="app-shell">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <nav className="global-nav" aria-label="Navegación global">
        <Link className="brand" to="/cursos">
          <strong>P2</strong>Proyecto 2
        </Link>
        <NavLink to="/cursos">
          <Icono tipo="cursos" />
          Cursos
        </NavLink>
        <NavLink className="nav-bottom" to="/perfil">
          <Icono tipo="cuenta" />
          Cuenta
        </NavLink>
      </nav>
      <header className="shell-header">
        <button
          className="mobile-toggle"
          aria-label="Abrir navegación"
          onClick={() => menu.current?.showModal()}
        >
          <Icono tipo="menu" />
        </button>
        <nav className="breadcrumbs" aria-label="Ubicación">
          <ol>
            <li>
              <Link to="/cursos">Cursos</Link>
            </li>
            {curso && (
              <li>
                <Link to={`/cursos/${curso.id}`}>
                  {curso.codigo} · {curso.periodo}
                </Link>
              </li>
            )}
            <li aria-current="page">{nombreSeccion}</li>
          </ol>
        </nav>
        <Link className="identity" to="/perfil">
          <span className="avatar" aria-hidden="true">
            {perfil.nombre.trim().slice(0, 1).toUpperCase()}
          </span>
          <span className="identity-name">{perfil.nombre}</span>
          <span className="sr-only"> · Mi perfil</span>
        </Link>
      </header>
      <div className={`workspace ${curso ? "" : "no-course"}`}>
        {curso && (
          <aside className="course-nav">
            <div className="course-nav-title">
              <strong>{curso.nombre}</strong>
              <span className="muted">{curso.periodo}</span>
            </div>
            <EnlacesCurso curso={curso} />
            <p className="course-nav-note">
              Canvas es la fuente de estudiantes y fechas. GitHub aloja los
              repositorios.
            </p>
          </aside>
        )}
        <main className="main-content" id="contenido" tabIndex={-1}>
          {children ?? <Outlet />}
        </main>
      </div>
      <dialog className="mobile-dialog" ref={menu} aria-label="Navegación">
        <div className="panel-header">
          <h2>Proyecto 2</h2>
          <button autoFocus onClick={cerrarMenu}>
            Cerrar
          </button>
        </div>
        <div className="actions">
          <Link to="/cursos" onClick={cerrarMenu}>
            Mis cursos
          </Link>
          <Link to="/perfil" onClick={cerrarMenu}>
            Mi perfil
          </Link>
        </div>
        {curso && (
          <>
            <hr />
            <h3>{curso.nombre}</h3>
            <EnlacesCurso curso={curso} cerrar={cerrarMenu} />
          </>
        )}
      </dialog>
    </div>
  );
}
export function LayoutCurso() {
  const { cursoId = "" } = useParams();
  const sesion = useSesion();
  const curso = sesion.cursos.find((c) => c.id === cursoId);
  const consulta = useConsulta(
    `contexto-${cursoId}`,
    (signal) => obtenerContexto(cursoId, signal),
    60_000,
  );
  const [revalidando, setRevalidando] = useState(false);
  useEffect(() => {
    function refrescar() {
      consulta.recargar();
    }
    function acceso(event: Event) {
      const { status, path } = (
        event as CustomEvent<{ status: number; path: string }>
      ).detail;
      if (
        status === 403 &&
        path.includes(`/cursos/${cursoId}/`) &&
        !path.endsWith("/contexto")
      ) {
        setRevalidando(true);
        consulta.recargar();
      }
    }
    window.addEventListener("focus", refrescar);
    window.addEventListener("pds2:acceso", acceso);
    return () => {
      window.removeEventListener("focus", refrescar);
      window.removeEventListener("pds2:acceso", acceso);
    };
  }, [cursoId, consulta.recargar]);
  useEffect(() => {
    if (!consulta.cargando) setRevalidando(false);
  }, [consulta.cargando]);
  if (!curso)
    return (
      <Estructura>
        <h1>Curso no disponible</h1>
        <Aviso tipo="warning">
          Este curso no aparece entre tus cursos. Puede que tu acceso haya
          cambiado.
        </Aviso>
        <Link className="button" to="/cursos">
          Volver a mis cursos
        </Link>
      </Estructura>
    );
  if (consulta.error || !consulta.datos)
    return (
      <Estructura curso={curso}>
        {consulta.error ? (
          <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
        ) : (
          <Cargando texto="Consultando tus permisos en este curso…" />
        )}
      </Estructura>
    );
  return (
    <CursoContext.Provider
      value={{
        curso,
        contexto: consulta.datos,
        puede: (permiso) =>
          !revalidando && consulta.datos!.permisos_efectivos.includes(permiso),
        recargar: () => {
          consulta.recargar();
          sesion.recargar();
        },
      }}
    >
      <Estructura curso={curso}>
        {revalidando && <Aviso>Actualizando tus permisos…</Aviso>}
        <Outlet key={cursoId} />
      </Estructura>
    </CursoContext.Provider>
  );
}
export function SinPermiso({
  children = "Solo un profesor puede realizar esta acción.",
}: {
  children?: ReactNode;
}) {
  return <p className="help">{children}</p>;
}
export function EstadoCurso({ curso }: { curso: Curso }) {
  return <Estado valor={curso.estado} />;
}
