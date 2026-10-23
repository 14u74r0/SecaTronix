"""Tipos de dominio compartidos. Sin lógica."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Variable(str, Enum):
    TEMP_AIRE = "temp_aire"          # °C, 0–120
    HR_AIRE = "hr_aire"              # %, 0–100
    HUMEDAD_MADERA = "humedad_madera"  # %, 0–100


class Especie(str, Enum):
    PINO = "pino"
    EUCALIPTO = "eucalipto"


class Escenario(str, Enum):
    NORMAL = "normal"
    ZONA_HUMEDA = "zona_humeda"
    FALLA_VENTILADOR = "falla_ventilador"
    SENSOR_TRABADO = "sensor_trabado"


class Severidad(str, Enum):
    AMARILLA = "amarilla"
    ROJA = "roja"


@dataclass(frozen=True)
class Lectura:
    """Una medición de un nodo. Se serializa tal cual al payload MQTT (docs/CONTRATO.md §1)."""
    ts: datetime              # UTC, con tzinfo
    camara: str               # ej. "c01"
    nodo: str                 # ej. "n03"
    variable: Variable
    valor: float
    unidad: str               # "°C" | "%"


@dataclass(frozen=True)
class Alerta:
    """Alerta generada por Node-RED (el simulador no las produce). Topic: secadero/<camara>/alertas."""
    ts: datetime
    camara: str
    lote_id: Optional[int]
    severidad: Severidad
    mensaje: str


@dataclass
class EstadoNodo:
    """Estado interno de un nodo simulado en un instante."""
    nodo: str
    humedad_madera: float
    temp_aire: float
    hr_aire: float


@dataclass(frozen=True)
class ConfigSimulacion:
    """Se construye desde variables de entorno (MQTT_BROKER, MQTT_PORT, SIM_SPEED, SCENARIO, ESPECIE)."""
    broker: str
    puerto: int
    sim_speed: float          # > 0. Factor de aceleración del tiempo simulado (una sola vez).
    escenario: Escenario
    especie: Especie
    camara: str = "c01"
    nodos: tuple[str, ...] = ("n01", "n02", "n03", "n04", "n05", "n06")
    periodo_publicacion_s: float = 5.0   # tiempo real entre ciclos de publicación
