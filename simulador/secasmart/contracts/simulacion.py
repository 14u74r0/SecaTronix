"""Contrato del módulo de simulación. Solo interfaces."""
from __future__ import annotations

from typing import Iterable, Protocol

from .tipos import ConfigSimulacion, Especie, EstadoNodo, Lectura


class ModeloSecado(Protocol):
    """Física simplificada del secado. Debe ser determinista dado un RNG con semilla."""

    especie: Especie

    def estado_inicial(self, nodo: str) -> EstadoNodo:
        """Estado al inicio del ciclo (humedad ≈ 60 %, temp ≈ 40 °C, HR ≈ 95 %)."""
        ...

    def avanzar(self, estado: EstadoNodo, dt_simulado_s: float) -> EstadoNodo:
        """Avanza el estado dt_simulado_s segundos de tiempo simulado (decaimiento exponencial hacia ≈ 10 %)."""
        ...


class AplicadorEscenario(Protocol):
    """Inyecta fallas sobre los estados (zona_humeda, falla_ventilador, sensor_trabado)."""

    def aplicar(self, estados: dict[str, EstadoNodo], dt_simulado_s: float) -> dict[str, EstadoNodo]:
        """Devuelve los estados con la falla aplicada. `normal` devuelve los estados sin cambios."""
        ...


class Simulador(Protocol):
    """Orquesta modelo + escenario y produce lecturas. No conoce MQTT ni el lote."""

    config: ConfigSimulacion

    def paso(self, dt_real_s: float) -> Iterable[Lectura]:
        """Avanza dt_real_s * sim_speed segundos simulados y devuelve una Lectura por nodo y variable."""
        ...
