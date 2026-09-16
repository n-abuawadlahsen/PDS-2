-- Diagnóstico de solo lectura. Horas de salida en UTC.
-- Para otro caso, reemplazar el full_name en las tres consultas.
BEGIN TRANSACTION READ ONLY;
SET LOCAL TIME ZONE 'UTC';
SET LOCAL statement_timeout = '10s';

SELECT now() AS consultado_en,
       r.id AS repositorio_id, r.curso_id, r.tarea_id, r.full_name,
       r.estado AS repositorio_estado, r.motivo,
       r.error_mensaje_literal AS repositorio_error,
       r.actualizado_en AS repositorio_actualizado_en,
       t.estado AS tarea_estado, s.activo AS sujeto_activo,
       cg.login AS github_login,
       a.estado AS acceso_estado, a.invitado_en, a.aceptado_en,
       a.actualizado_en AS acceso_actualizado_en, a.ultimo_error AS acceso_error
FROM repositorio r
JOIN tarea t ON t.id = r.tarea_id
JOIN sujeto s ON s.id = r.sujeto_id
LEFT JOIN acceso_repositorio a ON a.repositorio_id = r.id
LEFT JOIN cuenta_github cg ON cg.id = a.cuenta_github_id
WHERE r.full_name = 'PDS-2-test/icc1101-2026-2-test1-e37482-parada-gonzalez-filipa-x';

SELECT p.tipo, p.activo, p.cadencia_segundos,
       p.ultima_ejecucion AS ultimo_encolado_en, p.proxima_ejecucion,
       now() - p.proxima_ejecucion AS desfase_programacion
FROM trabajo_periodico p
WHERE p.tipo = 'reconciliar_accesos'
  AND p.curso_id IN (
      SELECT r.curso_id FROM repositorio r
      WHERE r.full_name = 'PDS-2-test/icc1101-2026-2-test1-e37482-parada-gonzalez-filipa-x'
  );

SELECT j.id, j.tipo, j.estado, j.creado_en, j.tomado_en, j.terminado_en,
       j.intentos, j.max_intentos, j.proximo_intento_en, j.ultimo_error
FROM trabajo j
WHERE j.tipo = 'reconciliar_accesos'
  AND j.curso_id IN (
      SELECT r.curso_id FROM repositorio r
      WHERE r.full_name = 'PDS-2-test/icc1101-2026-2-test1-e37482-parada-gonzalez-filipa-x'
  )
ORDER BY j.creado_en DESC
LIMIT 20;

ROLLBACK;
