import pytest
from secasmart.contracts.tipos import Escenario, EstadoNodo
from secasmart.simulacion.escenario import AplicadorFallas

def test_escenario_normal():
    aplicador = AplicadorFallas(Escenario.NORMAL)
    estados = {"n01": EstadoNodo("n01", 50.0, 40.0, 80.0)}
    nuevos = aplicador.aplicar(estados, 10.0)

    assert estados["n01"].humedad_madera == nuevos["n01"].humedad_madera
    # Ensure it's a deepcopy
    assert id(estados["n01"]) != id(nuevos["n01"])

def test_falla_ventilador():
    aplicador = AplicadorFallas(Escenario.FALLA_VENTILADOR)
    estados = {"n01": EstadoNodo("n01", 50.0, 40.0, 80.0)}
    nuevos = aplicador.aplicar(estados, 10.0)

    assert nuevos["n01"].hr_aire == 100.0  # 80 + 20
    assert nuevos["n01"].humedad_madera > 50.0 # ralentiza el secado

def test_sensor_trabado():
    aplicador = AplicadorFallas(Escenario.SENSOR_TRABADO)
    estados1 = {"n05": EstadoNodo("n05", 50.0, 40.0, 80.0)}

    # Primer ciclo lo guarda
    nuevos1 = aplicador.aplicar(estados1, 10.0)
    assert nuevos1["n05"].humedad_madera == 50.0

    # Segundo ciclo, cambia el input pero el output queda igual
    estados2 = {"n05": EstadoNodo("n05", 40.0, 60.0, 50.0)}
    nuevos2 = aplicador.aplicar(estados2, 10.0)

    assert nuevos2["n05"].humedad_madera == 50.0
    assert nuevos2["n05"].temp_aire == 40.0
    assert nuevos2["n05"].hr_aire == 80.0
