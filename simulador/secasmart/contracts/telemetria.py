"""Contrato del módulo de telemetría (salida hacia MQTT). Solo interfaces."""
from __future__ import annotations

from datetime import datetime
from typing import Mapping, Protocol

from .tipos import Lectura


class Reloj(Protocol):
    """Inyectable para poder testear sin tiempo real."""

    def ahora_utc(self) -> datetime: ...


class SerializadorLectura(Protocol):
    """Traduce Lectura <-> (topic, payload) según docs/CONTRATO.md §1."""

    def topic(self, lectura: Lectura) -> str:
        """`secadero/<camara>/<nodo>/<variable>`."""
        ...

    def payload(self, lectura: Lectura) -> Mapping[str, object]:
        """Dict con claves: ts (ISO-8601 UTC, 'Z'), camara, nodo, variable, valor, unidad. Ver contratos/lectura.schema.json."""
        ...


class Publicador(Protocol):
    """Transporte. La implementación MQTT (paho) vive en simulador/; los tests usan un doble en memoria."""

    def conectar(self) -> None:
        """Reintenta hasta que el broker esté disponible."""
        ...

    def publicar(self, lectura: Lectura) -> None: ...

    def cerrar(self) -> None: ...
