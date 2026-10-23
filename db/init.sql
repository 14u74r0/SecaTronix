CREATE TABLE IF NOT EXISTS lotes (
    id SERIAL PRIMARY KEY,
    lote VARCHAR(255) NOT NULL,
    especie VARCHAR(100) NOT NULL,
    humedad_inicial FLOAT NOT NULL,
    humedad_objetivo FLOAT NOT NULL,
    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lecturas (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL,
    lote_id INT REFERENCES lotes(id),
    camara VARCHAR(50) NOT NULL,
    nodo VARCHAR(50) NOT NULL,
    variable VARCHAR(100) NOT NULL,
    valor FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS alertas (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL,
    lote_id INT REFERENCES lotes(id),
    severidad VARCHAR(50) NOT NULL,
    mensaje TEXT NOT NULL
);
