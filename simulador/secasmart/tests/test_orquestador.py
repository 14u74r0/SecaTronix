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
