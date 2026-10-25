// Validar y normalizar una lectura MQTT (contrato: contratos/lectura.schema.json).
// Entrada : msg.topic, msg.payload (objeto JSON ya parseado por el nodo mqtt-in).
// Salida 1: msg.lectura = {ts (ms epoch), camara, nodo, variable, valor}  → lectura válida
// Salida 2: {payload:{motivo, topic}}                                    → lectura descartada
const VARIABLES = {
    temp_aire:      { min: 0, max: 120, unidad: '°C' },
    hr_aire:        { min: 0, max: 100, unidad: '%' },
    humedad_madera: { min: 0, max: 100, unidad: '%' },
};

function descartar(motivo) {
    const n = (flow.get('descartadas') || 0) + 1;
    flow.set('descartadas', n);
    if (n === 1 || n % 100 === 0) {
        node.warn(`Lectura descartada (${n} en total): ${motivo} — topic=${msg.topic}`);
    }
    return [null, { payload: { motivo, topic: msg.topic } }];
}

const p = msg.payload;
if (p === null || typeof p !== 'object' || Array.isArray(p)) return descartar('payload no es un objeto JSON');

const claves = ['ts', 'camara', 'nodo', 'variable', 'valor', 'unidad'];
for (const k of claves) {
    if (!(k in p)) return descartar(`falta el campo "${k}"`);
}
if (typeof p.camara !== 'string' || !/^c[0-9]{2}$/.test(p.camara)) return descartar('camara inválida');
if (typeof p.nodo !== 'string' || !/^n[0-9]{2}$/.test(p.nodo)) return descartar('nodo inválido');

const def = VARIABLES[p.variable];
if (!def) return descartar(`variable desconocida: ${p.variable}`);
if (p.unidad !== def.unidad) return descartar(`unidad inválida para ${p.variable}: ${p.unidad}`);

if (typeof p.valor !== 'number' || !Number.isFinite(p.valor)) return descartar('valor no numérico');
if (p.valor < def.min || p.valor > def.max) {
    return descartar(`valor fuera de rango para ${p.variable}: ${p.valor} (válido ${def.min}–${def.max})`);
}

const ts = typeof p.ts === 'string' ? Date.parse(p.ts) : NaN;
if (Number.isNaN(ts)) return descartar('ts inválido');

if (msg.topic !== `secadero/${p.camara}/${p.nodo}/${p.variable}`) {
    return descartar('el topic no coincide con el payload');
}

msg.lectura = { ts, camara: p.camara, nodo: p.nodo, variable: p.variable, valor: p.valor };
return [msg, null];
