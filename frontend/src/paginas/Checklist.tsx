import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ejecutarPruebaEscritura,
  encolarChecklist,
  firmarItem14AMano,
  obtenerEjecucionVerificacion,
  obtenerUltimaVerificacion,
  reejecutarItem,
  type ItemVerificacion,
} from "../lib/api";
import { useCurso } from "../components/Layout";
import {
  Aviso,
  Cabecera,
  Cargando,
  ErrorCarga,
  Estado,
  Mensajes,
  Tabla,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
const NOMBRES_ITEMS: Record<string, string> = {
  "1": "El token es válido y es tuyo",
  "2": "El curso existe, es visible y está publicado",
  "3": "Eres profesor del curso y no estás limitado a una sección",
  "4": "Puedes editar notas",
  "5": "Puedes publicar anuncios",
  "6": "Puedes enviar mensajes",
  "7": "Puedes ver correos de estudiantes",
  "8": "Secciones legibles y detección de cross-listing",
  "9": "Conjuntos de grupos colaborativos",
  "10": "Política de entrega tardía del curso",
  "11": "Períodos de calificación abiertos",
  "12": "Tamaño real de página que acepta la instancia",
  "13": "Zona horaria del curso",
  "14": "La App está instalada, con permisos congelados y la organización presentable",
  "15": "Estudiantes legibles",
  "16": "Puedes crear y editar tareas en Canvas",
  "17": "Puedes escribir comentarios en las entregas",
  "18": "Cada docente del curso tiene membresía activa en la organización",
  "19": "Puedes borrar anuncios propios",
};

const ORDEN_VISUAL = [
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "10",
  "11",
  "12",
  "13",
  "14",
  "15",
  "16",
  "17",
  "18",
  "19",
];

export function Checklist() {
  const { curso, puede, recargar } = useCurso();
  const administra = puede("curso.administrar");
  const [ejecucion, setEjecucion] = useState<{
    id: string;
    cantidad: number;
  } | null>(null);
  const [items, setItems] = useState<Record<string, ItemVerificacion>>({});
  const [consentimientos, setConsentimientos] = useState({
    "5-bis": false,
    "17-bis": false,
  });
  const op = useOperacion();
  const confirmar = useConfirmar();
  const ultima = useConsulta(`verificacion-${curso.id}`, (signal) =>
    obtenerUltimaVerificacion(curso.id, signal),
  );
  const corrida = useConsulta(
    `ejecucion-${curso.id}-${ejecucion?.id ?? "ninguna"}`,
    (signal) =>
      ejecucion
        ? obtenerEjecucionVerificacion(curso.id, ejecucion.id, signal)
        : Promise.resolve([]),
    ejecucion ? 2000 : 0,
  );
  function incorporar(lista: ItemVerificacion[]) {
    setItems((prev) => {
      const siguientes = { ...prev };
      for (const i of lista) if (i.item) siguientes[i.item] = i;
      return siguientes;
    });
  }
  useEffect(() => {
    if (ultima.datos) incorporar(ultima.datos);
  }, [ultima.datos]);
  useEffect(() => {
    if (corrida.datos && ejecucion) {
      incorporar(corrida.datos);
      if (corrida.datos.length >= ejecucion.cantidad) {
        setEjecucion(null);
        recargar();
      }
    }
  }, [corrida.datos, ejecucion, recargar]);
  useEffect(() => {
    if (!ejecucion) return;
    const timer = setTimeout(() => {
      setEjecucion(null);
      op.setError(
        "La verificación está tardando más de lo esperado. Los ítems sin respuesta siguen sin verificar. Actualiza los resultados o reintenta.",
      );
    }, 180_000);
    return () => clearTimeout(timer);
  }, [ejecucion]);
  const ocupado = op.ocupado || ejecucion !== null;
  const filas = Object.values(items).filter(
    (i) => i.item && !i.item.includes("bis"),
  );
  return (
    <>
      <Cabecera
        titulo="Verificación de conexiones"
        descripcion="Comprueba los permisos de Canvas y GitHub antes de continuar con las tareas."
        acciones={
          <button disabled={ocupado} onClick={ultima.recargar}>
            Actualizar resultados
          </button>
        }
      />
      <nav className="tabs" aria-label="Configuración">
        <Link to={`/cursos/${curso.id}/vinculacion`}>Conexiones</Link>
        <Link aria-current="page" to={`/cursos/${curso.id}/verificacion`}>
          Verificación
        </Link>
      </nav>
      <Mensajes {...op} />
      {ultima.error && (
        <ErrorCarga error={ultima.error} reintentar={ultima.recargar} />
      )}
      {corrida.error && (
        <ErrorCarga error={corrida.error} reintentar={corrida.recargar} />
      )}
      <div className="metrics">
        {[
          ["CORRECTO", "Correctas"],
          ["VERIFICADO_A_MANO", "Manuales"],
          ["ADVERTENCIA", "Advertencias"],
          ["BLOQUEANTE", "Bloqueantes"],
          ["NO_VERIFICADO", "Sin verificar"],
        ].map(([codigo, texto]) => (
          <div className="metric" key={codigo}>
            <strong>
              {codigo === "NO_VERIFICADO"
                ? 19 -
                  filas.filter((i) => i.resultado !== "NO_VERIFICADO").length
                : filas.filter((i) => i.resultado === codigo).length}
            </strong>
            <span>{texto} · de 19</span>
          </div>
        ))}
      </div>
      <section className="panel">
        <div className="panel-header">
          <h2>Comprobaciones del curso</h2>
          {administra && (
            <button
              className="primary"
              disabled={ocupado}
              onClick={() =>
                void op.ejecutar(async () => {
                  const r = await encolarChecklist(curso.id);
                  setItems({});
                  setEjecucion({ id: r.ejecucion_id, cantidad: 19 });
                }, "Verificación solicitada. Los resultados aparecerán a medida que se completen.")
              }
            >
              {ocupado ? "Verificando…" : "Ejecutar checklist completo"}
            </button>
          )}
        </div>
        {!administra && (
          <Aviso>
            Solo un profesor puede ejecutar comprobaciones. Los resultados están
            disponibles para consulta.
          </Aviso>
        )}
        {ejecucion && <Cargando texto="La verificación sigue en curso…" />}
        <Tabla etiqueta="Comprobaciones de Canvas y GitHub" fija={false}>
          <table>
            <thead>
              <tr>
                <th scope="col">Comprobación</th>
                <th scope="col">Resultado</th>
                <th scope="col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {ORDEN_VISUAL.map((id) => (
                <tr key={id}>
                  <td>
                    <strong>
                      {id}. {NOMBRES_ITEMS[id]}
                    </strong>
                    <p className="help">
                      {["14", "18"].includes(id) ? "GitHub" : "Canvas"}
                    </p>
                    {items[id]?.detalle &&
                      Object.keys(items[id].detalle).length > 0 && (
                        <details>
                          <summary>Ver motivo y detalles</summary>
                          <pre>
                            {JSON.stringify(items[id].detalle, null, 2)}
                          </pre>
                        </details>
                      )}
                  </td>
                  <td>
                    <Estado valor={items[id]?.resultado ?? "NO_VERIFICADO"} />
                  </td>
                  <td>
                    {administra && (
                      <div className="actions">
                        <button
                          disabled={ocupado}
                          onClick={() =>
                            void op.ejecutar(async () => {
                              const r = await reejecutarItem(curso.id, id);
                              setEjecucion({ id: r.ejecucion_id, cantidad: 1 });
                            })
                          }
                        >
                          Reintentar{" "}
                          <span className="sr-only">comprobación {id}</span>
                        </button>
                        {id === "14" &&
                          Boolean(items[id]?.detalle.requiere_firma_manual) && (
                            <button
                              disabled={ocupado}
                              onClick={async () => {
                                if (
                                  await confirmar({
                                    titulo: "Registrar verificación manual",
                                    descripcion:
                                      "Confirma que revisaste la configuración indicada de la organización. Quedará registrada como verificación manual con tu identidad.",
                                    accion: "Registrar verificación",
                                  })
                                )
                                  void op.ejecutar(async () =>
                                    incorporar([
                                      await firmarItem14AMano(curso.id),
                                    ]),
                                  );
                              }}
                            >
                              Verificar manualmente
                            </button>
                          )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Tabla>
      </section>
      <section className="panel">
        <h2>Pruebas opcionales de escritura</h2>
        <p>
          Estas pruebas realizan acciones en Canvas y requieren tu autorización
          por separado. No se incluyen al ejecutar el checklist completo.
        </p>
        {(["5-bis", "17-bis"] as const).map((id) => (
          <div className="panel" key={id}>
            <label className="check">
              <input
                type="checkbox"
                checked={consentimientos[id]}
                disabled={!administra || ocupado}
                onChange={(e) =>
                  setConsentimientos({
                    ...consentimientos,
                    [id]: e.target.checked,
                  })
                }
              />
              {id === "5-bis"
                ? "Autorizo crear y borrar un anuncio de prueba en Canvas."
                : "Autorizo escribir un comentario de prueba en una entrega de Canvas."}
            </label>
            <div className="actions">
              <button
                disabled={!administra || ocupado || !consentimientos[id]}
                onClick={() =>
                  void op.ejecutar(async () => {
                    incorporar([
                      await ejecutarPruebaEscritura(curso.id, id, true),
                    ]);
                    setConsentimientos((prev) => ({ ...prev, [id]: false }));
                  })
                }
              >
                Probar {id === "5-bis" ? "anuncio" : "comentario"}
              </button>
              {items[id] && <Estado valor={items[id].resultado} />}
            </div>
            {!consentimientos[id] && (
              <p className="help">
                Marca la autorización para habilitar esta prueba.
              </p>
            )}
          </div>
        ))}
      </section>
      <section className="panel next-step">
        <h2>Continúa con los estudiantes</h2>
        <p>
          Revisa la información sincronizada desde Canvas y las cuentas de
          GitHub asociadas.
        </p>
        <Link className="button primary" to={`/cursos/${curso.id}/personas`}>
          Ir a Personas
        </Link>
      </section>
    </>
  );
}
