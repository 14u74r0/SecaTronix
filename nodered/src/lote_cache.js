// Recibe el resultado de la consulta del lote activo y lo guarda en caché.
// Si la cámara no tiene lote activo la lectura se descarta (se avisa, sin inundar el log).
const filas = msg.payload;
if (!Array.isArray(filas) || filas.length === 0) {
    const n = (flow.get('sin_lote') || 0) + 1;
    flow.set('sin_lote', n);
    if (n === 1 || n % 100 === 0) {
        node.warn(`La cámara ${msg.lectura.camara} no tiene lote activo; lectura descartada (${n}). ` +
                  `Crear uno con: SELECT nuevo_lote('${msg.lectura.camara}', 'L-XXXX', 'pino');`);
    }
    return null;
}
const r = filas[0];
const lote = {
    id: r.id,
    nombre: r.lote,
    especie: r.especie,
    hIni: Number(r.humedad_inicial),
    hObj: Number(r.humedad_objetivo),
    k: Number(r.k_esperada),
    // Instante de referencia de la curva esperada: primera lectura del lote (o esta, si es la primera).
    t0: r.t0 ? new Date(r.t0).getTime() : msg.lectura.ts,
};
const cache = flow.get('lotes') || {};
cache[msg.lectura.camara] = { lote, cargado: Date.now() };
flow.set('lotes', cache);

msg.lote = lote;
delete msg.query;
delete msg.params;
msg.payload = undefined;
return msg;
