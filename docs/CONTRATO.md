# Contrato entre componentes

Flujo: `simulador → MQTT → Node-RED → PostgreSQL → Grafana`. Cada componente solo conoce a su vecino mediante este contrato.

## 1. MQTT (simulador → Node-RED)
- Topic de lecturas: `secadero/<camara>/<nodo>/<variable>` (variables: `temp_aire`, `hr_aire`, `humedad_madera`).
- Payload JSON: `ts` (ISO-8601 UTC), `camara`, `nodo`, `variable`, `valor` (número), `unidad`.
- El simulador **no conoce el lote**. Node-RED asigna el lote activo de la cámara.
- Alertas: `secadero/<camara>/alertas` (publica Node-RED). Payload: `ts, camara, lote_id, severidad ("amarilla"|"roja"), mensaje`.
- Variables de entorno del simulador: `MQTT_BROKER, MQTT_PORT, SIM_SPEED, SCENARIO` (`normal|zona_humeda|falla_ventilador|sensor_trabado`) y `ESPECIE` (`pino|eucalipto`, default `pino`). `docker-compose.yml` las pasa desde `.env`; Node-RED recibe también `SIM_SPEED`.

## 2. PostgreSQL (Node-RED → Grafana)
Tablas: `lotes`, `lecturas`, `alertas` (ver `db/init.sql`). Un lote "activo" por cámara = `fecha_fin IS NULL` (índice único: no puede haber dos).
- `lotes(id, lote, camara, especie, humedad_inicial, humedad_objetivo, k_esperada, fecha_inicio, fecha_fin)`
- `lecturas(id, ts, lote_id, camara, nodo, variable, valor)` — `ts` es `timestamptz` (UTC).
- `alertas(id, ts, lote_id, camara, regla, severidad, mensaje)` — `regla` ∈ `desvio_curva | diferencia_nodos | dato_sospechoso | falla_ventilador`.
- Función `nuevo_lote(camara, lote, especie)`: cierra el lote activo y abre otro (usarla cuando se reinicia el simulador o cambia `ESPECIE`).

Vistas que Grafana debe usar (no consultar tablas crudas cuando exista vista):
- `v_curva_secado(ts, lote_id, camara, humedad_real, humedad_objetivo)` — promedio de `humedad_madera` de los nodos por minuto vs objetivo del lote.
- `v_estado_camara(camara, lote_id, estado, ultima_alerta_ts)` — `estado` ∈ `verde|amarillo|rojo` (según alertas de los últimos 10 min del lote activo).
- `v_lecturas_nodo(ts, lote_id, camara, nodo, variable, valor)` — para temp/HR por nodo.
- Alertas recientes: tabla `alertas`.

## 3. Reglas de alerta (las implementa Node-RED, `nodered/src/reglas.js`)
| Regla | Condición | Severidad |
|---|---|---|
| Desvío de curva (`desvio_curva`) | `humedad_madera` promedio se desvía > 3 puntos de la curva esperada | amarilla; > 6 puntos → roja |
| Diferencia entre nodos (`diferencia_nodos`) | max − min de `humedad_madera` entre nodos > 2 puntos | amarilla |
| Dato sospechoso (`dato_sospechoso`) | mismo `valor` exacto 10 lecturas seguidas en un nodo/variable | amarilla |
| Falla de ventilador (`falla_ventilador`) | `hr_aire` promedio > 15 puntos sobre lo esperado | roja |

**Curva esperada** (`t` = segundos desde la primera lectura del lote × `SIM_SPEED`):
`H(t) = obj + (ini − obj) · exp(−k · t)` con `k = lotes.k_esperada` (pino 0.0002, eucalipto 0.00014);
`HR_esperada = 95 − 65 · (1 − (H − obj) / (ini − obj))`.

**Detalles de implementación**
- Se comparan nodos con lectura de los últimos 30 s y se exigen al menos 3.
- Una misma alerta no se repite antes de 60 s (de tiempo de lectura), salvo que escale de amarilla a roja.
- El lote activo se cachea 30 s en Node-RED: tras `nuevo_lote(...)` puede tardar hasta 30 s en tomarse.
- Si una cámara no tiene lote activo, sus lecturas se descartan y se avisa en el log.
- Las alertas se guardan en `alertas` y se publican en `secadero/<camara>/alertas` (payload según `contratos/alerta.schema.json`; `regla` queda solo en la base).

Rangos válidos para validar ingesta: temp 0–120 °C, hr 0–100 %, humedad_madera 0–100 %. Fuera de rango, `unidad` incorrecta, topic distinto del payload o JSON inválido: se descarta y se loguea.

## 4. Reparto de trabajo
- **Claude** (`claude/arch/logica-infra`): esquema, vistas, flujos Node-RED, reglas, compose. → Roadmap Paso 3.
- **Jules A** (`jules/feat/simulador`): corregir y completar `simulador/`. → ver issue/tarea del PR de Lautaro.
- **Jules B** (`jules/feat/grafana`): provisioning + dashboard. → Roadmap Paso 4.
