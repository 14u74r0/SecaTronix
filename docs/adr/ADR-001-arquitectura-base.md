# ADR-001 — Arquitectura base y contratos

Estado: propuesta · Autor: Claude (Lead Architect) · Implementa: Jules

## Contexto
SecaSmart simula sensores de una cámara de secado y los lleva por MQTT → Node-RED → PostgreSQL → Grafana (ver README). Hay dos agentes trabajando en paralelo, así que los límites entre módulos deben estar escritos antes de implementar.

## Decisión
Separar el simulador en tres responsabilidades, que solo se hablan por los contratos de `simulador/secasmart/contracts/`:

| Módulo | Contrato | Responsabilidad |
|---|---|---|
| Simulación | `simulacion.py` (`ModeloSecado`, `AplicadorEscenario`, `Simulador`) | Física del secado por especie y fallas. No conoce MQTT ni lote. |
| Telemetría | `telemetria.py` (`SerializadorLectura`, `Publicador`, `Reloj`) | Convertir `Lectura` a topic/payload y publicarla. |
| Tipos | `tipos.py` | `Lectura`, `Alerta`, `EstadoNodo`, `ConfigSimulacion` y enums. |

Los formatos de intercambio con el resto del sistema son `contratos/lectura.schema.json` y `contratos/alerta.schema.json`, alineados con `docs/CONTRATO.md`.

## Estructura de carpetas objetivo
```
simulador/
├── Dockerfile, requirements.txt
├── main.py                      # arma config desde env, conecta las piezas (Jules)
└── secasmart/
    ├── contracts/               # SOLO Claude: tipos e interfaces
    ├── modelo/                  # implementa ModeloSecado (pino, eucalipto)
    ├── escenarios/              # implementa AplicadorEscenario
    ├── telemetria/              # implementa SerializadorLectura y Publicador (paho)
    └── simulador.py             # implementa Simulador
tests/                           # pytest; usa dobles en memoria de Publicador y Reloj
contratos/                       # JSON Schema de los mensajes MQTT
db/ nodered/ grafana/ mosquitto/ # sin cambios de responsabilidad
```

## Consecuencias
- Jules implementa contra `Protocol`s y puede testear cada módulo aislado con dobles.
- Cambiar paho por otro transporte, o el simulador por ESP32 reales, solo afecta a `Publicador`/`Simulador`.
- Todo cambio a `contracts/` o `contratos/` pasa por PR de Claude; Jules propone cambios en su PR sin editarlos.
- Pendiente (siguientes ramas `claude/arch/...`): esquema y vistas de `db/`, flujos de Node-RED.

## Fuera de alcance de este ADR
Lógica de decaimiento, reglas de alerta y dashboard (se implementan contra estos contratos).
