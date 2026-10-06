import { useEffect, useRef } from "react";
import { useBlocker } from "react-router-dom";
import { useConfirmar } from "../components/ui";

/** Protege enlaces, navegación programática e historial con el mismo diálogo. */
export function useProtegerCambios(cambios: boolean) {
  const confirmar = useConfirmar();
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      cambios &&
      (currentLocation.pathname !== nextLocation.pathname ||
        currentLocation.search !== nextLocation.search),
  );
  const actual = useRef(blocker);
  actual.current = blocker;
  const preguntando = useRef(false);
  const montado = useRef(true);

  useEffect(() => {
    montado.current = true;
    return () => {
      montado.current = false;
    };
  }, []);

  useEffect(() => {
    if (blocker.state !== "blocked" || preguntando.current) return;
    preguntando.current = true;
    void confirmar({
      titulo: "Cambios sin guardar",
      descripcion:
        "Guarda el borrador antes de continuar, o confirma que deseas descartar estos cambios.",
      accion: "Descartar y continuar",
      peligro: true,
    })
      .then((acepta) => {
        if (!montado.current || actual.current.state !== "blocked") return;
        if (acepta) actual.current.proceed();
        else actual.current.reset();
      })
      .finally(() => {
        preguntando.current = false;
      });
  }, [blocker, confirmar]);

  useEffect(() => {
    if (!cambios) return;
    const salir = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", salir);
    return () => window.removeEventListener("beforeunload", salir);
  }, [cambios]);
}
