// Asignar el lote activo de la cámara. El lote se cachea 30 s para no consultar la base en cada mensaje.
// Salida 1: lote en caché → sigue el flujo (msg.lote).
// Salida 2: sin caché      → va a la consulta SQL (msg.query / msg.params).
const TTL_MS = 30000;
const cache = flow.get('lotes') || {};
const c = cache[msg.lectura.camara];
if (c && Date.now() - c.cargado < TTL_MS) {
    msg.lote = c.lote;
    return [msg, null];
}
msg.query = 'SELECT l.id, l.lote, l.especie, l.humedad_inicial, l.humedad_objetivo, l.k_esperada, ' +
            '(SELECT min(ts) FROM lecturas WHERE lote_id = l.id) AS t0 ' +
            'FROM lotes l WHERE l.camara = $1 AND l.fecha_fin IS NULL';
msg.params = [msg.lectura.camara];
return [null, msg];
