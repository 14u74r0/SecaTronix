import pytest
from datetime import datetime, timezone
from secasmart.contracts.tipos import Lectura, Variable
from secasmart.telemetria.serializador import SerializadorJSON

def test_serializador():
    serializador = SerializadorJSON()
    ts = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    lectura = Lectura(
        ts=ts,
        camara="c01",
        nodo="n01",
        variable=Variable.TEMP_AIRE,
        valor=42.1234,
        unidad="°C"
    )

    assert serializador.topic(lectura) == "secadero/c01/n01/temp_aire"

    payload = serializador.payload(lectura)
    assert payload["ts"] == "2023-01-01T12:00:00Z"
    assert payload["camara"] == "c01"
    assert payload["nodo"] == "n01"
    assert payload["variable"] == "temp_aire"
    assert payload["valor"] == 42.12
    assert payload["unidad"] == "°C"
