# Node-RED — ingesta, lote y reglas de alerta

Flujo único (`flows.json`, pestaña **SecaSmart**):

```
mqtt in secadero/+/+/+ → Validar lectura → Asignar lote ─┬→ INSERT lecturas
                                (descartadas → debug)     └→ Reglas de alerta → INSERT alertas
                                                                              └→ mqtt out secadero/<camara>/alertas
```

- **Validar:** JSON, campos, rangos, unidad y coherencia topic/payload (`contratos/lectura.schema.json`).
- **Lote:** consulta el lote activo de la cámara (caché 30 s). Sin lote activo, descarta y avisa.
- **Reglas:** `docs/CONTRATO.md` §3. El estado (últimos valores, repeticiones, enfriamiento) vive en memoria.
- **Base de datos:** nodo `node-red-contrib-postgresql`; host, puerto, base, usuario y clave se leen de las variables
  `POSTGRES_*` del contenedor (no hay credenciales en `flows.json`).

## Editar el flujo
La lógica está en `src/*.js` (una función por archivo) y `flows.json` se **genera**:

```bash
python3 nodered/src/build_flows.py     # regenera nodered/flows.json
node --test nodered/tests/funciones.test.js   # tests de las funciones (sin dependencias)
```
Si se cambia el flujo desde el editor web de Node-RED, hay que llevar el cambio a `src/` o se pierde al regenerar.

## Operación
- **Reiniciar el simulador** vuelve a arrancar la madera en 60 %: abrir un lote nuevo para que la curva esperada coincida:
  `docker compose exec postgres psql -U secasmart -c "SELECT nuevo_lote('c01','L-0002','pino');"`
- **Cambiar `ESPECIE`** (eucalipto): abrir un lote de esa especie (usa `k = 0.00014`):
  `SELECT nuevo_lote('c01','L-0003','eucalipto');`
- **Cambiar `init.sql`** solo se aplica con un volumen nuevo: `docker compose down -v`.
- La primera alerta tarda unos minutos reales a `SIM_SPEED=1`; para ver fallas rápido, usar `SIM_SPEED=60`
  (y un lote nuevo, porque cambia la velocidad de la curva).
