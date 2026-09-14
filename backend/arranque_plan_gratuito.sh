#!/usr/bin/env bash
# Arranque para el plan GRATUITO de Render (sin tarjeta): un solo web service
# corre la API y el trabajador en el mismo contenedor, porque Render no tiene
# plan gratuito para background workers.
#
# Desviacion consciente de SPEC 14 S14.5.1 (dos servicios con un comando cada
# uno). Con plan de pago se usa infra/render.yaml y este archivo sobra.
#
# Si cualquiera de los dos procesos termina, el contenedor termina con el y
# Render lo reinicia: nunca queda una API sana con el trabajador muerto.
set -u

python -m app.trabajos.ejecutor &
trabajador=$!

uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}" --timeout-graceful-shutdown 25 &
api=$!

# Render detiene el contenedor con SIGTERM: se reenvia a los dos para que el
# trabajador libere sus trabajos y la API cierre las conexiones en orden.
detener() {
    kill -TERM "$trabajador" "$api" 2>/dev/null
    wait
    exit 0
}
trap detener TERM INT

wait -n "$trabajador" "$api"
codigo=$?
echo "arranque_plan_gratuito: un proceso termino (codigo $codigo); se detiene el contenedor" >&2
kill -TERM "$trabajador" "$api" 2>/dev/null
wait
exit "$codigo"
