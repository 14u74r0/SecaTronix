# 🌲 SecaSmart — Monitoreo inteligente del secado de madera (simulado)

> Un script en Python simula los sensores de una cámara de secado de madera y los publica por **MQTT**. **Node-RED** procesa los datos y genera alertas, **PostgreSQL** los guarda y **Grafana** los muestra en un tablero. Todo se levanta con un solo comando.

![Estado](https://img.shields.io/badge/estado-en%20dise%C3%B1o-orange)
![Docker](https://img.shields.io/badge/run-docker%20compose-2496ED)

Trabajo Final de IoT. **Caso:** Maderas del Norte S.A. (empresa ficticia, sector forestoindustrial).
**Integrantes:** Santiago Galeano · Alejandro Gauto · Lautaro Montivero.

---

## Tabla de contenidos

1. [Problema a resolver](#1-problema-a-resolver)
2. [Cumplimiento de los criterios del trabajo](#2-cumplimiento-de-los-criterios-del-trabajo)
3. [Arquitectura](#3-arquitectura)
4. [Stack y por qué](#4-stack-y-por-qué)
5. [Inicio rápido](#5-inicio-rápido)
6. [Estructura del repositorio](#6-estructura-del-repositorio)
7. [Simulador de sensores](#7-simulador-de-sensores)
8. [Mensajes MQTT](#8-mensajes-mqtt)
9. [Base de datos](#9-base-de-datos)
10. [Flujos de Node-RED y alertas](#10-flujos-de-node-red-y-alertas)
11. [Tablero en Grafana](#11-tablero-en-grafana)
12. [Roadmap](#12-roadmap)
13. [Ampliaciones futuras](#13-ampliaciones-futuras)

---

## 1. Problema a resolver

**¿Qué pasa?** Maderas del Norte S.A. asierra y fabrica muebles de pino y eucalipto. La madera debe secarse de forma gradual hasta una humedad final de ≈ 8–12 %. Si el proceso se desvía, aparecen alabeos, rajaduras y lotes con humedad despareja: **piezas defectuosas** (supuesto: ≈ 12 % por lote).

**¿Quién lo tiene?** El jefe de secadero y los operarios, que regulan la cámara por experiencia, con mediciones manuales puntuales y sin registro histórico. No ven qué pasa dentro de la cámara hasta que ya es tarde ("punto ciego").

**¿Por qué IoT lo resuelve?** Sensores distribuidos en la cámara miden temperatura y humedad de forma continua. Los datos se guardan por lote y el sistema avisa **antes** de que se arruine el secado (semáforo verde/amarillo/rojo).

> El trabajo es 100 % simulado: no usa hardware real. El diseño es tal que cambiar el simulador por ESP32 reales no modificaría el resto del sistema.

**Desafío (HMW):** ¿Cómo podríamos lograr que el secado de pino y eucalipto se monitoree de forma continua y confiable, para que los operarios detecten y corrijan a tiempo los desvíos y se reduzcan las piezas defectuosas, con tecnología simple de usar y mantener en la región?

---

## 2. Cumplimiento de los criterios del trabajo

| Criterio | Requisito | Cómo se cumple |
|---|---|---|
| Problema a resolver | Obligatorio | Sección 1 |
| Herramienta de automatización | Mínimo 1 | **Node-RED** (ingesta, reglas, alertas) |
| Dispositivos y datos | Opcional (real o simulado) | **Simulado** con un script en Python |
| Base de datos | Obligatorio | **PostgreSQL** |
| Protocolo de comunicación | Obligatorio (1) | **MQTT** (Mosquitto) |
| Visualización | Opcional | **Grafana** |

---

## 3. Arquitectura

```
┌───────────────┐   MQTT    ┌───────────┐         ┌───────────┐
│  Simulador    │ ────────► │ Mosquitto │ ──────► │ Node-RED  │
│  (Python)     │           │ (broker)  │         │ reglas +  │
└───────────────┘           └───────────┘         │ alertas   │
                                                  └─────┬─────┘
                                                        │ SQL
                                                  ┌─────▼─────┐      ┌──────────┐
                                                  │ PostgreSQL│ ───► │ Grafana  │
                                                  └───────────┘      │ tablero  │
                                                                     └──────────┘
```

Cinco contenedores, todos orquestados por `docker-compose.yml`.

---

## 4. Stack y por qué

El criterio fue **la opción más simple que cumple todos los requisitos**.

| Pieza | Herramienta | Por qué |
|---|---|---|
| Sensores simulados | **Python + paho-mqtt** | Un único script, fácil de entender y de modificar. |
| Protocolo | **MQTT (Mosquitto)** | Estándar de IoT; configuración mínima. |
| Automatización | **Node-RED** | Visual, nativo para MQTT, sin programar mucho. |
| Base de datos | **PostgreSQL** | Libre, conocida, se conecta directo a Node-RED y Grafana. |
| Visualización | **Grafana** | Dashboards listos con gráficos de series de tiempo y semáforo; se configura una sola vez por *provisioning*. |
| Despliegue | **Docker Compose** | Un comando para todo. |

### Qué se dejó afuera a propósito (para mantenerlo simple)

- **n8n:** no hace falta; Node-RED ya cubre la automatización y las alertas.
- **TimescaleDB:** PostgreSQL común alcanza para el volumen de datos simulados.
- **IA / modelos de predicción, Raspberry Pi, ESP32, LoRa, actuadores:** ver [Ampliaciones futuras](#13-ampliaciones-futuras).

---

## 5. Inicio rápido

> ⚠️ **Estado:** El simulador (backend) ya está implementado (Paso 1 y 2). Faltan integrar algunos pasos de Node-RED, DB y Grafana. Esta sección describe cómo va a funcionar completamente.

### Requisitos

- [Docker](https://docs.docker.com/get-docker/) con Docker Compose v2
- Puertos libres: `1883` (MQTT), `1880` (Node-RED), `3000` (Grafana), `5432` (PostgreSQL)

### Pasos

```bash
git clone https://github.com/<usuario>/<repo>.git
cd <repo>
cp .env.example .env
docker compose up -d
```

### Accesos

| Servicio | URL | Credenciales |
|---|---|---|
| Grafana (tablero) | http://localhost:3000 | definidas en `.env` |
| Node-RED (flujos) | http://localhost:1880 | sin login (solo desarrollo) |

> 🔒 Credenciales y acceso anónimo **solo para desarrollo local**.

### Comandos útiles

```bash
docker compose logs -f simulador                          # ver lo que publica el simulador
docker compose exec mosquitto mosquitto_sub -t "secadero/#" -v   # ver mensajes MQTT en vivo
docker compose down                                       # apagar (conserva datos)
docker compose down -v                                    # apagar y borrar datos
```

---

## 6. Estructura del repositorio

```
.
├── docker-compose.yml
├── .env.example
├── README.md
├── simulador/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── simulador.py
├── mosquitto/
│   └── mosquitto.conf
├── nodered/
│   └── flows.json
├── db/
│   └── init.sql
└── grafana/
    ├── provisioning/        # datasource y dashboard automáticos
    └── dashboards/
```

---

## 7. Simulador de sensores

Un solo script que simula **una cámara con 6 nodos** (arriba / medio / abajo × entrada / salida de aire). Publica una lectura por nodo cada pocos segundos.

| Variable | Unidad | Rango típico |
|---|---|---|
| `temp_aire` | °C | 40 – 80 |
| `hr_aire` | % | 30 – 95 |
| `humedad_madera` | % | 8 – 60 (baja con el tiempo hacia ≈ 10 %) |

**Comportamiento:**
- La humedad de la madera decae exponencialmente según especie (pino/eucalipto).
- Ruido aleatorio en cada lectura.
- Un parámetro `SIM_SPEED` acelera el tiempo para que un ciclo de varios días corra en minutos (útil para la demo).

**Fallas inyectables** (por variable de entorno o argumento):

| Escenario | Qué simula | Qué debería pasar |
|---|---|---|
| `normal` | Ciclo sin incidentes | Semáforo verde |
| `zona_humeda` | Un nodo seca más lento | Alerta por diferencia entre nodos |
| `falla_ventilador` | Sube la humedad del aire y baja el secado | Alerta roja |
| `sensor_trabado` | Un sensor repite el mismo valor | Alerta de dato sospechoso |

---

## 8. Mensajes MQTT

**Topic:** `secadero/<camara>/<nodo>/<variable>`
Ejemplo: `secadero/c01/n03/humedad_madera`

**Payload (JSON):**

```json
{
  "ts": "2026-10-22T14:40:00Z",
  "camara": "c01",
  "nodo": "n03",
  "variable": "humedad_madera",
  "valor": 23.4,
  "unidad": "%"
}
```

Las alertas se publican en `secadero/<camara>/alertas`.

---

## 9. Base de datos

PostgreSQL. Tablas (se crean automáticamente con `db/init.sql`):

| Tabla | Contenido |
|---|---|
| `lotes` | lote, especie, humedad inicial y objetivo, fecha de inicio y fin |
| `lecturas` | `ts, lote_id, camara, nodo, variable, valor` |
| `alertas` | `ts, lote_id, severidad (amarilla/roja), mensaje` |

Las lecturas y alertas referencian al lote con clave foránea.

---

## 10. Flujos de Node-RED y alertas

1. **Ingesta:** suscripción a `secadero/#`, validación básica del JSON y rango, e inserción en `lecturas`.
2. **Reglas:**
   - Humedad de la madera fuera de la curva esperada → amarilla/roja.
   - Diferencia entre nodos mayor a 2 % → amarilla.
   - Valor repetido muchas veces seguidas → dato sospechoso.
3. **Alertas:** se guardan en `alertas` y se publican por MQTT. *(Opcional: aviso por Telegram con un nodo de Node-RED.)*

---

## 11. Tablero en Grafana

- 🚦 **Semáforo** del estado de la cámara (verde / amarillo / rojo).
- 📉 **Curva de secado:** humedad de la madera real vs. objetivo.
- 🌡️ Temperatura y humedad del aire por nodo.
- 🔔 Tabla de **alertas** recientes.
- 📦 Selector de **lote**.

El dashboard se carga automáticamente al iniciar; no hay que configurarlo a mano.

---

## 12. Roadmap

- [x] **Paso 1:** `docker-compose.yml` con Mosquitto + PostgreSQL + Node-RED + Grafana funcionando.
- [x] **Paso 2:** simulador publicando en `normal`.
- [ ] **Paso 3:** Node-RED guardando las lecturas en PostgreSQL.
- [ ] **Paso 4:** tablero de Grafana con curva de secado.
- [ ] **Paso 5:** reglas y alertas + escenarios de falla.
- [ ] **Paso 6:** documentación final, capturas de pantalla y demo.

---

## 13. Ampliaciones futuras

Fuera del alcance del trabajo, pero contempladas en el diseño original de SecaSmart:

- Mapa de calor 2D por interpolación espacial.
- Código QR dinámico por pila con historial del lote.
- Modelo de IA para predecir humedad final y tiempo restante.
- Control asistido y automático (PID) de ventilación.
- Hardware real: ESP32 + sensores + gateway local. Como el simulador ya publica por MQTT con el mismo formato, el resto del sistema no cambiaría.
- Notificaciones por WhatsApp/Telegram con n8n.

---

<sub>Los datos, la empresa y los valores de este proyecto son ficticios y se usan con fines académicos.</sub>
