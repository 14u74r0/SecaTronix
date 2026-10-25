// Prepara cada alerta para dos destinos:
//   Salida 1: INSERT en la tabla alertas.
//   Salida 2: publicación MQTT en secadero/<camara>/alertas (contratos/alerta.schema.json).
const a = msg.payload;
const sql = {
    query: 'INSERT INTO alertas (ts, lote_id, camara, regla, severidad, mensaje) VALUES ($1, $2, $3, $4, $5, $6)',
    params: [a.ts, a.lote_id, a.camara, msg.regla, a.severidad, a.mensaje],
};
const mqtt = { topic: `secadero/${a.camara}/alertas`, payload: a };
return [sql, mqtt];
