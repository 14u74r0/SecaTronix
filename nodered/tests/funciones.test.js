// Tests de las funciones de nodered/src/*.js. Sin dependencias: `node --test nodered/tests/`
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const SRC = path.join(__dirname, '..', 'src');

// Ejecuta el cuerpo de un "function node" con un entorno simulado (msg, node, context, flow, env).
function cargar(nombre, { env = {} } = {}) {
    const cuerpo = fs.readFileSync(path.join(SRC, `${nombre}.js`), 'utf8');
    const mem = (m) => ({ get: (k) => m.get(k), set: (k, v) => m.set(k, v) });
    const ctx = mem(new Map());
    const flow = mem(new Map());
    const avisos = [];
    const node = { warn: (m) => avisos.push(m), error: (m) => avisos.push(m) };
    const envObj = { get: (k) => env[k] };
    const fn = new Function('msg', 'node', 'context', 'flow', 'global', 'env', cuerpo);
    return { ejecutar: (msg) => fn(msg, node, ctx, flow, {}, envObj), avisos, flow, ctx };
}

// --- validar -------------------------------------------------------------------------------------------
const lecturaOk = () => ({
    topic: 'secadero/c01/n03/humedad_madera',
    payload: { ts: '2026-10-22T14:40:00Z', camara: 'c01', nodo: 'n03', variable: 'humedad_madera', valor: 23.4, unidad: '%' },
});

test('validar: acepta una lectura válida y normaliza', () => {
    const v = cargar('validar');
    const [ok, mal] = v.ejecutar(lecturaOk());
    assert.equal(mal, null);
    assert.equal(ok.lectura.nodo, 'n03');
    assert.equal(ok.lectura.ts, Date.parse('2026-10-22T14:40:00Z'));
});

test('validar: descarta payloads inválidos', () => {
    const casos = {
        'valor fuera de rango': (m) => { m.payload.valor = 140; },
        'humedad negativa': (m) => { m.payload.valor = -4.8; },
        'valor no numérico': (m) => { m.payload.valor = '23'; },
        'unidad incorrecta': (m) => { m.payload.unidad = '°C'; },
        'variable desconocida': (m) => { m.payload.variable = 'presion'; m.topic = 'secadero/c01/n03/presion'; },
        'topic distinto del payload': (m) => { m.topic = 'secadero/c01/n04/humedad_madera'; },
        'falta un campo': (m) => { delete m.payload.ts; },
        'ts inválido': (m) => { m.payload.ts = 'ayer'; },
        'nodo inválido': (m) => { m.payload.nodo = 'x1'; m.topic = 'secadero/c01/x1/humedad_madera'; },
        'payload no es objeto': (m) => { m.payload = 'hola'; },
    };
    for (const [nombre, mutar] of Object.entries(casos)) {
        const v = cargar('validar');
        const m = lecturaOk();
        mutar(m);
        const [ok, mal] = v.ejecutar(m);
        assert.equal(ok, null, nombre);
        assert.ok(mal && mal.payload.motivo, nombre);
    }
});

// --- reglas --------------------------------------------------------------------------------------------
const NODOS = ['n01', 'n02', 'n03', 'n04', 'n05', 'n06'];
const T0 = Date.parse('2026-10-22T14:00:00Z');
const LOTE = { id: 1, nombre: 'L-0001', especie: 'pino', hIni: 60, hObj: 10, k: 0.0002, t0: T0 };

// Valores "esperados" del simulador a los t segundos (SIM_SPEED = 1).
const hEsp = (t) => 10 + 50 * Math.exp(-0.0002 * t);
const hrEsp = (t) => 95 - 65 * (1 - (hEsp(t) - 10) / 50);

// Emite un ciclo completo (6 nodos × 3 variables) y devuelve las alertas generadas.
function ciclo(r, t, { h = {}, hr = {}, fijo = {} } = {}) {
    const alertas = [];
    let i = 0;
    for (const nodo of NODOS) {
        for (const variable of ['temp_aire', 'hr_aire', 'humedad_madera']) {
            i += 1;
            let valor;
            if (fijo[`${nodo}|${variable}`] !== undefined) valor = fijo[`${nodo}|${variable}`];
            else if (variable === 'humedad_madera') valor = (h[nodo] ?? hEsp(t)) + Math.sin(i + t) * 0.05;
            else if (variable === 'hr_aire') valor = (hr[nodo] ?? hrEsp(t)) + Math.cos(i + t) * 0.5;
            else valor = 40 + 40 * (1 - (hEsp(t) - 10) / 50) + Math.sin(i * t) * 0.4;
            const salida = r.ejecutar({
                lectura: { ts: T0 + t * 1000, camara: 'c01', nodo, variable, valor },
                lote: LOTE,
            });
            if (salida) alertas.push(...salida[0]);
        }
    }
    return alertas;
}

test('reglas: un secado normal no genera alertas', () => {
    const r = cargar('reglas');
    const todas = [];
    for (let t = 0; t <= 6000; t += 5) todas.push(...ciclo(r, t));
    assert.deepEqual(todas.map((a) => a.regla), []);
});

test('reglas: un nodo que seca lento genera diferencia_nodos (amarilla)', () => {
    const r = cargar('reglas');
    const todas = [];
    for (let t = 0; t <= 4000; t += 5) todas.push(...ciclo(r, t, { h: { n03: hEsp(t) + 8 } }));
    const dif = todas.filter((a) => a.regla === 'diferencia_nodos');
    assert.ok(dif.length >= 1);
    assert.equal(dif[0].payload.severidad, 'amarilla');
    assert.match(dif[0].payload.mensaje, /n03/);
    assert.equal(dif[0].payload.lote_id, 1);
});

test('reglas: humedad del aire alta en todos los nodos → falla_ventilador (roja)', () => {
    const r = cargar('reglas');
    const todas = [];
    for (let t = 0; t <= 4000; t += 5) {
        const hr = {};
        NODOS.forEach((n) => { hr[n] = Math.min(100, hrEsp(t) + 20); });
        todas.push(...ciclo(r, t, { hr }));
    }
    const f = todas.filter((a) => a.regla === 'falla_ventilador');
    assert.ok(f.length >= 1);
    assert.equal(f[0].payload.severidad, 'roja');
});

test('reglas: desvío de curva amarilla (>3) y roja (>6)', () => {
    const r = cargar('reglas');
    const t = 3000;
    const amarilla = ciclo(r, t, { h: Object.fromEntries(NODOS.map((n) => [n, hEsp(t) + 4])) });
    assert.equal(amarilla.find((a) => a.regla === 'desvio_curva').payload.severidad, 'amarilla');
    // Escala a roja en el mismo lote: se emite enseguida aunque haya enfriamiento de la amarilla.
    const roja = ciclo(r, t + 5, { h: Object.fromEntries(NODOS.map((n) => [n, hEsp(t + 5) + 8])) });
    assert.equal(roja.find((a) => a.regla === 'desvio_curva').payload.severidad, 'roja');
});

test('reglas: valor repetido 10 veces → dato_sospechoso (con 9 no)', () => {
    const r9 = cargar('reglas');
    let a9 = [];
    for (let i = 0; i < 9; i++) a9.push(...ciclo(r9, i * 5, { fijo: { 'n05|humedad_madera': 60 } }));
    assert.equal(a9.filter((a) => a.regla === 'dato_sospechoso').length, 0);

    const r10 = cargar('reglas');
    let a10 = [];
    for (let i = 0; i < 10; i++) a10.push(...ciclo(r10, i * 5, { fijo: { 'n05|humedad_madera': 60 } }));
    const s = a10.filter((a) => a.regla === 'dato_sospechoso');
    assert.equal(s.length, 1);
    assert.match(s[0].payload.mensaje, /n05/);
    assert.equal(s[0].payload.severidad, 'amarilla');
});

test('reglas: no repite la misma alerta antes de 60 s', () => {
    const r = cargar('reglas');
    const todas = [];
    // 11 ciclos (55 s) con la misma anomalía: 1 sola alerta de diferencia_nodos.
    for (let i = 0; i < 11; i++) todas.push(...ciclo(r, 3000 + i * 5, { h: { n03: hEsp(3000 + i * 5) + 8 } }));
    assert.equal(todas.filter((a) => a.regla === 'diferencia_nodos').length, 1);
    // Pasados los 60 s, vuelve a avisar.
    const mas = ciclo(r, 3000 + 65, { h: { n03: hEsp(3065) + 8 } });
    assert.equal(mas.filter((a) => a.regla === 'diferencia_nodos').length, 1);
});

test('reglas: la curva esperada respeta SIM_SPEED', () => {
    // A SIM_SPEED=10 el secado va 10x más rápido; con la humedad "de 1x" debe saltar el desvío.
    const r = cargar('reglas', { env: { SIM_SPEED: '10' } });
    const t = 600; // 10 min reales = 100 min simulados
    const hSim = 10 + 50 * Math.exp(-0.0002 * 10 * t);
    const ok = ciclo(r, t, { h: Object.fromEntries(NODOS.map((n) => [n, hSim])) });
    assert.equal(ok.filter((a) => a.regla === 'desvio_curva').length, 0);
    const r2 = cargar('reglas', { env: { SIM_SPEED: '10' } });
    const mal = ciclo(r2, t, { h: Object.fromEntries(NODOS.map((n) => [n, hEsp(t)])) });
    assert.ok(mal.filter((a) => a.regla === 'desvio_curva').length >= 1);
});

// --- lote / insert / alerta ----------------------------------------------------------------------------
test('lote: sin caché consulta la base; con caché sigue de largo', () => {
    const l = cargar('lote');
    const msg = { lectura: { ts: T0, camara: 'c01', nodo: 'n01', variable: 'hr_aire', valor: 90 } };
    const [pasa, consulta] = l.ejecutar(msg);
    assert.equal(pasa, null);
    assert.deepEqual(consulta.params, ['c01']);

    const c = cargar('lote_cache');
    c.flow.set('lotes', undefined);
    const sal = c.ejecutar({
        ...consulta,
        payload: [{ id: 7, lote: 'L-7', especie: 'pino', humedad_inicial: 60, humedad_objetivo: 10, k_esperada: 0.0002, t0: null }],
    });
    assert.equal(sal.lote.id, 7);
    assert.equal(sal.lote.t0, T0); // sin lecturas previas: la referencia es esta lectura
    assert.equal(sal.params, undefined);
});

test('lote_cache: sin lote activo descarta la lectura y avisa', () => {
    const c = cargar('lote_cache');
    const sal = c.ejecutar({ lectura: { camara: 'c01', ts: T0 }, payload: [] });
    assert.equal(sal, null);
    assert.equal(c.avisos.length, 1);
});

test('preparar_insert y armar_alerta respetan el contrato', () => {
    const ins = cargar('preparar_insert').ejecutar({
        lectura: { ts: T0, camara: 'c01', nodo: 'n02', variable: 'temp_aire', valor: 55.5 }, lote: { id: 3 },
    });
    assert.equal(ins.params.length, 6);
    assert.equal(ins.params[0], '2026-10-22T14:00:00.000Z');

    const [sql, mqtt] = cargar('armar_alerta').ejecutar({
        regla: 'desvio_curva',
        payload: { ts: '2026-10-22T14:00:00.000Z', camara: 'c01', lote_id: 3, severidad: 'roja', mensaje: 'x' },
    });
    assert.deepEqual(sql.params.slice(2, 5), ['c01', 'desvio_curva', 'roja']);
    assert.equal(mqtt.topic, 'secadero/c01/alertas');
    assert.deepEqual(Object.keys(mqtt.payload).sort(), ['camara', 'lote_id', 'mensaje', 'severidad', 'ts']);
});
