"""Contratos del simulador y la telemetría de SecaSmart.

Solo tipos e interfaces (sin lógica). Dueño: Claude. Jules implementa contra estos contratos.
Ver docs/CONTRATO.md y docs/adr/ADR-001-arquitectura-base.md.
"""
from .tipos import (
    Especie, Escenario, Severidad, Variable,
    Lectura, Alerta, EstadoNodo, ConfigSimulacion,
)
from .simulacion import ModeloSecado, AplicadorEscenario, Simulador
from .telemetria import Publicador, SerializadorLectura, Reloj

__all__ = [
    "Especie", "Escenario", "Severidad", "Variable",
    "Lectura", "Alerta", "EstadoNodo", "ConfigSimulacion",
    "ModeloSecado", "AplicadorEscenario", "Simulador",
    "Publicador", "SerializadorLectura", "Reloj",
]
