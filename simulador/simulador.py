import os
import time
import json
import random
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

# Configuration
BROKER = os.getenv('MQTT_BROKER', 'mosquitto')
PORT = int(os.getenv('MQTT_PORT', 1883))
SIM_SPEED = float(os.getenv('SIM_SPEED', 1.0))
SCENARIO = os.getenv('SCENARIO', 'normal')

CAMARA = "c01"
NODOS = ["n01", "n02", "n03", "n04", "n05", "n06"] # 6 nodes
VARIABLES = [
    {"nombre": "temp_aire", "unidad": "°C"},
    {"nombre": "hr_aire", "unidad": "%"},
    {"nombre": "humedad_madera", "unidad": "%"}
]

# Simulator state
state = {
    nodo: {
        "humedad_madera": 60.0,
        "temp_aire": 40.0,
        "hr_aire": 95.0,
        "stuck_value": None
    } for nodo in NODOS
}

def publish_reading(client, camara, nodo, variable, valor, unidad):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    topic = f"secadero/{camara}/{nodo}/{variable}"
    payload = {
        "ts": ts,
        "camara": camara,
        "nodo": nodo,
        "variable": variable,
        "valor": round(valor, 2),
        "unidad": unidad
    }
    client.publish(topic, json.dumps(payload))
    print(f"Published {topic}: {payload}")

def update_state(elapsed_time):
    # Simulate drying process
    decay_rate = 0.001 * SIM_SPEED # baseline decay rate per step
    target_humedad = 10.0

    for nodo in NODOS:
        # Base changes
        # decay formula: dH = -k * (H - target)
        k = decay_rate

        # apply scenarios
        if SCENARIO == "zona_humeda" and nodo == "n03":
            k = decay_rate * 0.5 # Dries slower

        if SCENARIO == "falla_ventilador":
            k = decay_rate * 0.3 # Drying slows significantly

        # Update humedad_madera
        if state[nodo]["humedad_madera"] > target_humedad:
            state[nodo]["humedad_madera"] -= k * (state[nodo]["humedad_madera"] - target_humedad)

        # Temp and HR changes based on progress
        progress = 1.0 - (state[nodo]["humedad_madera"] - target_humedad) / (60.0 - target_humedad)

        # Temp goes from 40 to 80
        base_temp = 40.0 + (40.0 * progress)
        # HR goes from 95 to 30
        base_hr = 95.0 - (65.0 * progress)

        if SCENARIO == "falla_ventilador":
            base_hr = min(95.0, base_hr + 20.0) # hr raises

        # Add noise
        state[nodo]["temp_aire"] = base_temp + random.uniform(-1.0, 1.0)
        state[nodo]["hr_aire"] = max(0, min(100, base_hr + random.uniform(-2.0, 2.0)))

        if SCENARIO == "sensor_trabado" and nodo == "n05":
            if state[nodo]["stuck_value"] is None:
                state[nodo]["stuck_value"] = {
                    "temp_aire": state[nodo]["temp_aire"],
                    "hr_aire": state[nodo]["hr_aire"],
                    "humedad_madera": state[nodo]["humedad_madera"]
                }
            state[nodo]["temp_aire"] = state[nodo]["stuck_value"]["temp_aire"]
            state[nodo]["hr_aire"] = state[nodo]["stuck_value"]["hr_aire"]
            state[nodo]["humedad_madera"] = state[nodo]["stuck_value"]["humedad_madera"]
        else:
            state[nodo]["humedad_madera"] += random.uniform(-0.1, 0.1) # small noise

def main():
    client = mqtt.Client()

    connected = False
    while not connected:
        try:
            client.connect(BROKER, PORT, 60)
            connected = True
            print(f"Connected to MQTT broker at {BROKER}:{PORT}")
        except Exception as e:
            print(f"Waiting for MQTT broker... ({e})")
            time.sleep(5)

    client.loop_start()

    print(f"Starting simulation with SCENARIO={SCENARIO}, SIM_SPEED={SIM_SPEED}")

    try:
        while True:
            update_state(5.0) # simulate 5 seconds passed per loop iteration

            for nodo in NODOS:
                for var in VARIABLES:
                    publish_reading(
                        client,
                        CAMARA,
                        nodo,
                        var["nombre"],
                        state[nodo][var["nombre"]],
                        var["unidad"]
                    )

            # Sleep logic - respect sim speed, but don't sleep less than 0.1s
            sleep_time = 5.0 / SIM_SPEED if SIM_SPEED > 0 else 5.0
            time.sleep(max(0.1, sleep_time))

    except KeyboardInterrupt:
        print("Simulation stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
