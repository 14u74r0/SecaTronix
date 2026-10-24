import pytest
from datetime import datetime, timezone
from secasmart.contracts.tipos import ConfigSimulacion, Especie, Escenario, Variable
from secasmart.simulacion.modelo import ModeloSecadoFisico
from secasmart.simulacion.escenario import AplicadorFallas
from secasmart.simulacion.orquestador import SimuladorOrquestador

class RelojFalso:
    def ahora_utc(self):
        return datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

def test_orquestador():
    config = ConfigSimulacion(
        broker="localhost",
        puerto=1883,
        sim_speed=1.0,
        escenario=Escenario.NORMAL,
        especie=Especie.PINO,
        camara="c01",
        nodos=("n01", "n02")
    )

    modelo = ModeloSecadoFisico(config.especie)
    aplicador = AplicadorFallas(config.escenario)
    reloj = RelojFalso()

    simulador = SimuladorOrquestador(config, modelo, aplicador, reloj)

    # 2 nodos * 3 variables = 6 lecturas
    lecturas = list(simulador.paso(5.0))

    assert len(lecturas) == 6
    assert lecturas[0].ts == reloj.ahora_utc()
    assert lecturas[0].camara == "c01"

    variables = set(l.variable for l in lecturas if l.nodo == "n01")
    assert variables == {Variable.TEMP_AIRE, Variable.HR_AIRE, Variable.HUMEDAD_MADERA}


def test_sensor_trabado_lecturas():
    config = ConfigSimulacion(
        broker="localhost",
        puerto=1883,
        sim_speed=1.0,
        escenario=Escenario.SENSOR_TRABADO,
        especie=Especie.PINO,
        camara="c01",
        nodos=("n01", "n05")
    )

    modelo = ModeloSecadoFisico(config.especie)
    aplicador = AplicadorFallas(config.escenario)
    reloj = RelojFalso()

    simulador = SimuladorOrquestador(config, modelo, aplicador, reloj)

    def get_lecturas(lects, nodo):
        return {l.variable: l.valor for l in lects if l.nodo == nodo}

    # First step
    lecturas1 = get_lecturas(simulador.paso(5.0), "n05")

    for _ in range(12):
        lecturas_siguientes = get_lecturas(simulador.paso(5.0), "n05")
        assert lecturas1 == lecturas_siguientes

    # Check that another node (e.g. n01) doesn't freeze its readings
    lecturas_n01_1 = get_lecturas(simulador.paso(5.0), "n01")

    # We step several times so humidity should dry down, meaning readings must change
    for _ in range(20):
        simulador.paso(5.0)

    lecturas_n01_end = get_lecturas(simulador.paso(5.0), "n01")
    assert lecturas_n01_1 != lecturas_n01_end
