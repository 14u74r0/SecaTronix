# Contrato entre componentes

Flujo: `simulador → MQTT → Node-RED → PostgreSQL → Grafana`. Cada componente solo conoce a su vecino mediante este contrato.

## 1. MQTT (simulador → Node-RED)
- Topic de lecturas: `secadero/<camara>/<nodo>/<variable>` (variables: `temp_aire`, `hr_aire`, `humedad_madera`).
- Payload JSON: `ts` (ISO-8601 UTC), `camara`, `nodo`, `variable`, `valor` (número), `unidad`.
- El simulador **no conoce el lote**. Node-RED asigna el lote activo de la cámara.
- Alertas: `secadero/<camara>/alertas` (publica Node-RED). Payload: `ts, camara, lote_id, severidad ("amarilla"|"roja"), mensaje`.
- Variables de entorno del simulador: `MQTT_BROKER, MQTT_PORT, SIM_SPEED, SCENARIO` (`normal|zona_humeda|falla_ventilador|sensor_trabado`), y nuevo: `ESPECIE` (`pino|eucalipto`, default `pino`).

## 2. PostgreSQL (Node-RED → Grafana)
Tablas: `lotes`, `lecturas`, `alertas` (ver `db/init.sql`). Un lote "activo" por cámara = `fecha_fin IS NULL`.
Vistas que Grafana debe usar (no consultar tablas crudas cuando exista vista):
- `v_curva_secado(ts, lote_id, camara, humedad_real, humedad_objetivo)` — promedio de `humedad_madera` de los nodos por minuto vs objetivo del lote.
- `v_estado_camara(camara, lote_id, estado, ultima_alerta_ts)` — `estado` ∈ `verde|amarillo|rojo` (según alertas de los últimos 10 min).
- `v_lecturas_nodo(ts, lote_id, camara, nodo, variable, valor)` — para temp/HR por nodo.
- Alertas recientes: tabla `alertas`.

## 3. Reglas de alerta (las implementa Node-RED)
| Regla | Condición | Severidad |
|---|---|---|
| Desvío de curva | `humedad_madera` promedio se desvía > 3 puntos de la curva esperada | amarilla; > 6 puntos → roja |
| Diferencia entre nodos | max − min de `humedad_madera` entre nodos > 2 puntos | amarilla |
| Dato sospechoso | mismo `valor` exacto 10 lecturas seguidas en un nodo/variable | amarilla |
| Falla de ventilador | `hr_aire` promedio > 15 puntos sobre lo esperado | roja |

Rangos válidos para validar ingesta: temp 0–120 °C, hr 0–100 %, humedad_madera 0–100 %. Fuera de rango se descarta y se loguea.

## 4. Reparto de trabajo
- **Claude** (`infra/logica-analista`): esquema, vistas, flujos Node-RED, reglas, compose. → Roadmap Paso 3.
- **Jules A** (`jules/simulador`): corregir y completar `simulador/`. → ver issue/tarea del PR de Lautaro.
- **Jules B** (`jules/grafana`): provisioning + dashboard. → Roadmap Paso 4.
