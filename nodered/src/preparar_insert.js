// Arma el INSERT de la lectura en la tabla lecturas.
const L = msg.lectura;
msg.query = 'INSERT INTO lecturas (ts, lote_id, camara, nodo, variable, valor) VALUES ($1, $2, $3, $4, $5, $6)';
msg.params = [new Date(L.ts).toISOString(), msg.lote.id, L.camara, L.nodo, L.variable, L.valor];
return msg;
