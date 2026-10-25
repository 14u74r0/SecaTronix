// Reglas de alerta (docs/CONTRATO.md §3). Mantiene el estado por cámara en el contexto del nodo.
// Entrada : msg.lectura + msg.lote
// Salida 1: array de alertas {payload:{ts,camara,lote_id,severidad,mensaje}, regla}
const CFG = {
    FRESCO_S: 30,          // una lectura sirve para comparar nodos si es de los últimos 30 s
    COOLDOWN_S: 60,        // no repetir la misma alerta antes de 60 s (salvo que escale a roja)
    REPETICIONES: 10,      // valores idénticos seguidos → dato sospechoso
    MIN_NODOS: 3,          // mínimo de nodos con dato fresco para comparar
    DIF_NODOS: 2,          // puntos de humedad entre nodos → amarilla
    DESVIO_AMARILLA: 3,    // puntos contra la curva esperada
    DESVIO_ROJA: 6,
    DESVIO_HR: 15,         // puntos de HR sobre lo esperado → falla de ventilador (roja)
};
const SIM_SPEED = parseFloat(env.get('SIM_SPEED')) || 1;
const RANGO = { amarilla: 1, roja: 2 };

const L = msg.lectura;
const lote = msg.lote;
const estado = context.get('estado') || {};
const cam = estado[L.camara] = estado[L.camara] || { valores: {}, rep: {}, alertas: {} };
context.set('estado', estado);

const salida = [];
function emitir(regla, clave, severidad, mensaje) {
    const previa = cam.alertas[clave];
    const permitido = !previa
        || RANGO[severidad] > RANGO[previa.severidad]
        || (L.ts - previa.ts) >= CFG.COOLDOWN_S * 1000;
    if (!permitido) return;
    cam.alertas[clave] = { severidad, ts: L.ts };
    salida.push({
        regla,
        payload: { ts: new Date(L.ts).toISOString(), camara: L.camara, lote_id: lote.id, severidad, mensaje },
    });
}

// Curva esperada: H(t) = obj + (ini - obj) * exp(-k * SIM_SPEED * t); HR esperada ligada a la humedad.
function esperado() {
    const t = Math.max(0, (L.ts - lote.t0) / 1000);
    const h = lote.hObj + (lote.hIni - lote.hObj) * Math.exp(-lote.k * SIM_SPEED * t);
    const avance = 1 - (h - lote.hObj) / (lote.hIni - lote.hObj);   // 0 → 1
    return { h, hr: 95 - 65 * avance };
}
const f1 = (x) => x.toFixed(1);

// Valores frescos (último de cada nodo) de una variable.
function frescos(variable) {
    const lim = L.ts - CFG.FRESCO_S * 1000;
    const out = [];
    for (const k of Object.keys(cam.valores)) {
        const v = cam.valores[k];
        if (v.variable === variable && v.ts >= lim) out.push(v);
    }
    return out;
}

// 1) Registrar la lectura y detectar valor repetido (dato sospechoso).
const key = `${L.nodo}|${L.variable}`;
cam.valores[key] = { nodo: L.nodo, variable: L.variable, valor: L.valor, ts: L.ts };
const rep = cam.rep[key] = cam.rep[key] || { ultimo: null, n: 0 };
if (rep.ultimo === L.valor) { rep.n += 1; } else { rep.ultimo = L.valor; rep.n = 1; }
if (rep.n >= CFG.REPETICIONES) {
    emitir('dato_sospechoso', `dato_sospechoso|${key}`, 'amarilla',
        `Sensor ${L.nodo}: ${L.variable} repite el valor ${L.valor} en ${rep.n} lecturas seguidas (dato sospechoso)`);
}

// 2) Reglas sobre la humedad de la madera.
if (L.variable === 'humedad_madera') {
    const fs = frescos('humedad_madera');
    if (fs.length >= CFG.MIN_NODOS) {
        let max = fs[0], min = fs[0], suma = 0;
        for (const v of fs) { if (v.valor > max.valor) max = v; if (v.valor < min.valor) min = v; suma += v.valor; }
        const prom = suma / fs.length;

        const dif = max.valor - min.valor;
        if (dif > CFG.DIF_NODOS) {
            emitir('diferencia_nodos', 'diferencia_nodos', 'amarilla',
                `Diferencia de humedad entre nodos: ${f1(dif)} puntos (${max.nodo}=${f1(max.valor)} %, ${min.nodo}=${f1(min.valor)} %)`);
        }

        const esp = esperado();
        const desvio = prom - esp.h;
        const ad = Math.abs(desvio);
        if (ad > CFG.DESVIO_AMARILLA) {
            const sev = ad > CFG.DESVIO_ROJA ? 'roja' : 'amarilla';
            emitir('desvio_curva', 'desvio_curva', sev,
                `Humedad promedio ${f1(prom)} % se desvía ${desvio > 0 ? '+' : ''}${f1(desvio)} puntos de la curva esperada (${f1(esp.h)} %)`);
        }
    }
}

// 3) Falla de ventilador: la humedad del aire sube sobre lo esperado.
if (L.variable === 'hr_aire') {
    const fs = frescos('hr_aire');
    if (fs.length >= CFG.MIN_NODOS) {
        const prom = fs.reduce((a, v) => a + v.valor, 0) / fs.length;
        const esp = esperado();
        if (prom - esp.hr > CFG.DESVIO_HR) {
            emitir('falla_ventilador', 'falla_ventilador', 'roja',
                `Humedad del aire promedio ${f1(prom)} % supera en ${f1(prom - esp.hr)} puntos lo esperado (${f1(esp.hr)} %): posible falla de ventilador`);
        }
    }
}

return salida.length ? [salida] : null;
