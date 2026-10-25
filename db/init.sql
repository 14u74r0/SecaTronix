-- SecaSmart — esquema de PostgreSQL.
-- Se ejecuta UNA vez, cuando se crea el volumen de datos. Para re-aplicarlo: `docker compose down -v`.
-- Contrato: docs/CONTRATO.md §2 (tablas y vistas que consume Grafana).

-- ---------------------------------------------------------------------------
-- Tablas
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS lotes (
    id               SERIAL PRIMARY KEY,
    lote             VARCHAR(255)     NOT NULL,
    camara           VARCHAR(50)      NOT NULL DEFAULT 'c01',
    especie          VARCHAR(100)     NOT NULL,
    humedad_inicial  DOUBLE PRECISION NOT NULL,
    humedad_objetivo DOUBLE PRECISION NOT NULL,
    -- Tasa esperada de secado en 1/s de tiempo simulado: H(t) = obj + (ini - obj) * exp(-k * t)
    -- La usa Node-RED para la curva esperada (regla "desvío de curva").
    k_esperada       DOUBLE PRECISION NOT NULL DEFAULT 0.0002,
    fecha_inicio     TIMESTAMPTZ      NOT NULL DEFAULT now(),
    fecha_fin        TIMESTAMPTZ
);

-- Un único lote activo (fecha_fin IS NULL) por cámara.
CREATE UNIQUE INDEX IF NOT EXISTS ux_lotes_activo_por_camara
    ON lotes (camara) WHERE fecha_fin IS NULL;

CREATE TABLE IF NOT EXISTS lecturas (
    id      BIGSERIAL PRIMARY KEY,
    ts      TIMESTAMPTZ      NOT NULL,
    lote_id INT              NOT NULL REFERENCES lotes (id),
    camara  VARCHAR(50)      NOT NULL,
    nodo    VARCHAR(50)      NOT NULL,
    variable VARCHAR(100)    NOT NULL CHECK (variable IN ('temp_aire', 'hr_aire', 'humedad_madera')),
    valor   DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_lecturas_lote_variable_ts ON lecturas (lote_id, variable, ts);
CREATE INDEX IF NOT EXISTS ix_lecturas_nodo_ts          ON lecturas (camara, nodo, variable, ts DESC);

CREATE TABLE IF NOT EXISTS alertas (
    id        BIGSERIAL PRIMARY KEY,
    ts        TIMESTAMPTZ NOT NULL,
    lote_id   INT          REFERENCES lotes (id),
    camara    VARCHAR(50)  NOT NULL,
    regla     VARCHAR(50)  NOT NULL,   -- desvio_curva | diferencia_nodos | dato_sospechoso | falla_ventilador
    severidad VARCHAR(50)  NOT NULL CHECK (severidad IN ('amarilla', 'roja')),
    mensaje   TEXT         NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_alertas_camara_ts ON alertas (camara, ts DESC);

-- ---------------------------------------------------------------------------
-- Lote de arranque (la cámara c01 empieza con un lote de pino)
-- ---------------------------------------------------------------------------

INSERT INTO lotes (lote, camara, especie, humedad_inicial, humedad_objetivo, k_esperada)
SELECT 'L-0001', 'c01', 'pino', 60, 10, 0.0002
WHERE NOT EXISTS (SELECT 1 FROM lotes WHERE camara = 'c01' AND fecha_fin IS NULL);

-- Cierra el lote activo de la cámara y abre uno nuevo. Devuelve el id del lote nuevo.
-- Uso: SELECT nuevo_lote('c01', 'L-0002', 'eucalipto');
-- (hacerlo cuando se reinicia el simulador: arranca de nuevo con 60 % de humedad).
CREATE OR REPLACE FUNCTION nuevo_lote(
    p_camara  TEXT,
    p_lote    TEXT,
    p_especie TEXT,
    p_humedad_inicial  DOUBLE PRECISION DEFAULT 60,
    p_humedad_objetivo DOUBLE PRECISION DEFAULT 10
) RETURNS INT AS $$
DECLARE
    v_id INT;
BEGIN
    UPDATE lotes SET fecha_fin = now() WHERE camara = p_camara AND fecha_fin IS NULL;
    INSERT INTO lotes (lote, camara, especie, humedad_inicial, humedad_objetivo, k_esperada)
    VALUES (p_lote, p_camara, p_especie, p_humedad_inicial, p_humedad_objetivo,
            CASE lower(p_especie) WHEN 'eucalipto' THEN 0.00014 ELSE 0.0002 END)
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- Vistas para Grafana (contrato §2)
-- ---------------------------------------------------------------------------

-- Lecturas crudas por nodo (temperatura / humedad del aire por nodo).
CREATE OR REPLACE VIEW v_lecturas_nodo AS
SELECT ts, lote_id, camara, nodo, variable, valor
FROM lecturas;

-- Curva de secado: promedio de humedad de la madera entre nodos, por minuto, contra el objetivo del lote.
CREATE OR REPLACE VIEW v_curva_secado AS
SELECT date_trunc('minute', l.ts) AS ts,
       l.lote_id,
       l.camara,
       avg(l.valor)              AS humedad_real,
       lo.humedad_objetivo       AS humedad_objetivo
FROM lecturas l
JOIN lotes lo ON lo.id = l.lote_id
WHERE l.variable = 'humedad_madera'
GROUP BY date_trunc('minute', l.ts), l.lote_id, l.camara, lo.humedad_objetivo;

-- Semáforo de la cámara según las alertas de los últimos 10 minutos del lote activo.
CREATE OR REPLACE VIEW v_estado_camara AS
SELECT lo.camara,
       lo.id AS lote_id,
       CASE
           WHEN bool_or(a.severidad = 'roja')     THEN 'rojo'
           WHEN bool_or(a.severidad = 'amarilla') THEN 'amarillo'
           ELSE 'verde'
       END AS estado,
       max(a.ts) AS ultima_alerta_ts
FROM lotes lo
LEFT JOIN alertas a
       ON a.lote_id = lo.id
      AND a.ts >= now() - interval '10 minutes'
WHERE lo.fecha_fin IS NULL
GROUP BY lo.camara, lo.id;
