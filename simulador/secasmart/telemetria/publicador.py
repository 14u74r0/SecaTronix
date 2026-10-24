import json
import time
import paho.mqtt.client as mqtt
from typing import Optional
from secasmart.contracts.tipos import ConfigSimulacion, Lectura
from secasmart.contracts.telemetria import SerializadorLectura

class PublicadorMQTT:
    """Implementación de Publicador usando paho-mqtt."""

    def __init__(self, config: ConfigSimulacion, serializador: SerializadorLectura):
        self.config = config
        self.serializador = serializador
        self.client = mqtt.Client()
        self.conectado = False

    def conectar(self) -> None:
        while not self.conectado:
            try:
                self.client.connect(self.config.broker, self.config.puerto, 60)
                self.conectado = True
                print(f"Connected to MQTT broker at {self.config.broker}:{self.config.puerto}")
            except Exception as e:
                print(f"Waiting for MQTT broker at {self.config.broker}:{self.config.puerto}... ({e})")
                time.sleep(5)
        self.client.loop_start()

    def publicar(self, lectura: Lectura) -> None:
        topic = self.serializador.topic(lectura)
        payload = self.serializador.payload(lectura)
        self.client.publish(topic, json.dumps(payload))
        print(f"Published {topic}: {payload}")

    def cerrar(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
        self.conectado = False
