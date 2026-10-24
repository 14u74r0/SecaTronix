import os
import time
import json
import random
from datetime import datetime, timezone
from typing import Iterable, Optional, Dict
import paho.mqtt.client as mqtt

from secasmart.contracts import (
    ConfigSimulacion,
    Escenario,
    Especie,
    Lectura,
    Variable,
    EstadoNodo,
    Reloj
)

class RelojReal(Reloj):
    def ahora_utc(self) -> datetime:
        return datetime.now(timezone.utc)

class SimuladorSecadero:
    def __init__(self, config: ConfigSimulacion):
        self.config = config

        self.estados: Dict[str, EstadoNodo] = {
            nodo: EstadoNodo(
                nodo=nodo,
                humedad_madera=60.0,
                temp_aire=40.0,
                hr_aire=95.0
            ) for nodo in self.config.nodos
        }
        self.stuck_values = {}

    def paso(self, dt_real_s: float, reloj: Optional[Reloj] = None) -> Iterable[Lectura]:
        if reloj is None:
            reloj = RelojReal()

        now = reloj.ahora_utc()
        dt_simulado_s = dt_real_s * self.config.sim_speed

        # k per simulated second (original was 0.001 per 5s step = 0.0002)
        decay_rate_per_sec = 0.0002
        target_humedad = 10.0

        for nodo, estado in self.estados.items():
            k_factor = 1.0

            if self.config.escenario == Escenario.ZONA_HUMEDA and nodo == "n03":
                k_factor = 0.5
            elif self.config.escenario == Escenario.FALLA_VENTILADOR:
                k_factor = 0.3

            k = decay_rate_per_sec * k_factor * dt_simulado_s

            if estado.humedad_madera > target_humedad:
                estado.humedad_madera -= k * (estado.humedad_madera - target_humedad)

            estado.humedad_madera = max(8.0, estado.humedad_madera)

            progress = 1.0 - (estado.humedad_madera - target_humedad) / (60.0 - target_humedad)
            progress = max(0.0, min(1.0, progress))

            base_temp = 40.0 + (40.0 * progress)
            base_hr = 95.0 - (65.0 * progress)

            if self.config.escenario == Escenario.FALLA_VENTILADOR:
                base_hr = min(95.0, base_hr + 20.0)

            estado.temp_aire = base_temp
            estado.hr_aire = base_hr

        lecturas = []
        for nodo, estado in self.estados.items():
            temp_ruido = estado.temp_aire + random.uniform(-1.0, 1.0)
            hr_ruido = max(0, min(100, estado.hr_aire + random.uniform(-2.0, 2.0)))
            hm_ruido = max(8.0, estado.humedad_madera + random.uniform(-0.1, 0.1))

            if self.config.escenario == Escenario.SENSOR_TRABADO and nodo == "n05":
                if nodo not in self.stuck_values:
                    self.stuck_values[nodo] = (temp_ruido, hr_ruido, hm_ruido)
                temp_ruido, hr_ruido, hm_ruido = self.stuck_values[nodo]

            lecturas.append(Lectura(ts=now, camara=self.config.camara, nodo=nodo, variable=Variable.TEMP_AIRE, valor=round(temp_ruido, 2), unidad="°C"))
            lecturas.append(Lectura(ts=now, camara=self.config.camara, nodo=nodo, variable=Variable.HR_AIRE, valor=round(hr_ruido, 2), unidad="%"))
            lecturas.append(Lectura(ts=now, camara=self.config.camara, nodo=nodo, variable=Variable.HUMEDAD_MADERA, valor=round(hm_ruido, 2), unidad="%"))

        return lecturas


def publish_reading(client: mqtt.Client, lectura: Lectura):
    ts_str = lectura.ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    topic = f"secadero/{lectura.camara}/{lectura.nodo}/{lectura.variable.value}"
    payload = {
        "ts": ts_str,
        "camara": lectura.camara,
        "nodo": lectura.nodo,
        "variable": lectura.variable.value,
        "valor": lectura.valor,
        "unidad": lectura.unidad
    }
    client.publish(topic, json.dumps(payload))
    print(f"Published {topic}: {payload}")

def main():
    broker = os.getenv('MQTT_BROKER', 'mosquitto')
    port = int(os.getenv('MQTT_PORT', 1883))
    sim_speed = float(os.getenv('SIM_SPEED', 1.0))
    escenario_str = os.getenv('SCENARIO', 'normal')

    try:
        escenario = Escenario(escenario_str)
    except ValueError:
        escenario = Escenario.NORMAL

    config = ConfigSimulacion(
        broker=broker,
        puerto=port,
        sim_speed=sim_speed,
        escenario=escenario,
        especie=Especie.PINO, # Default
    )

    simulador = SimuladorSecadero(config)
    client = mqtt.Client()

    connected = False
    while not connected:
        try:
            client.connect(config.broker, config.puerto, 60)
            connected = True
            print(f"Connected to MQTT broker at {config.broker}:{config.puerto}")
        except Exception as e:
            print(f"Waiting for MQTT broker... ({e})")
            time.sleep(5)

    client.loop_start()
    print(f"Starting simulation with SCENARIO={config.escenario.value}, SIM_SPEED={config.sim_speed}")

    try:
        while True:
            # We sleep for the real publication period (5.0s)
            time.sleep(config.periodo_publicacion_s)

            # Step the simulation by the same real time that elapsed
            lecturas = simulador.paso(config.periodo_publicacion_s)

            for lectura in lecturas:
                publish_reading(client, lectura)

    except KeyboardInterrupt:
        print("Simulation stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
