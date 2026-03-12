CREATE TABLE IF NOT EXISTS propuestas (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    cliente TEXT NOT NULL,
    esquema TEXT NOT NULL,
    num_empleados INTEGER,
    ahorro_mensual NUMERIC(12,2),
    ahorro_anual NUMERIC(12,2),
    costo_actual NUMERIC(12,2),
    costo_propuesto NUMERIC(12,2),
    usuario TEXT DEFAULT 'Seba',
    notas TEXT
);
