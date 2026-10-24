import pytest
from datetime import datetime, timezone
from secasmart.contracts import ConfigSimulacion, Escenario, Especie, Variable
from simulador import SimuladorSecadero, RelojReal

class RelojMock:
    def __init__(self):
        self.now = datetime(2023, 1, 1, tzinfo=timezone.utc)

    def ahora_utc(self) -> datetime:
        return self.now

def get_base_config(**kwargs):
    default_args = {
        "broker": "localhost",
        "puerto": 1883,
        "sim_speed": 1.0,
        "escenario": Escenario.NORMAL,
        "especie": Especie.PINO
    }
    default_args.update(kwargs)
    return ConfigSimulacion(**default_args)

def test_sim_speed():
    config_1x = get_base_config()
    config_10x = get_base_config(sim_speed=10.0)

    sim_1x = SimuladorSecadero(config_1x)
    sim_10x = SimuladorSecadero(config_10x)

    sim_1x.paso(5.0, RelojMock())
    sim_10x.paso(5.0, RelojMock())

    hm_1x = sim_1x.estados["n01"].humedad_madera
    hm_10x = sim_10x.estados["n01"].humedad_madera

    decay_1x = 60.0 - hm_1x
    decay_10x = 60.0 - hm_10x

    assert decay_10x > decay_1x * 9.5
    assert decay_10x < decay_1x * 10.5

def test_zona_humeda():
    config = get_base_config(escenario=Escenario.ZONA_HUMEDA)
    sim = SimuladorSecadero(config)

    # Run for a while to see the difference
    for _ in range(100):
        sim.paso(5.0, RelojMock())

    hm_normal = sim.estados["n01"].humedad_madera
    hm_humeda = sim.estados["n03"].humedad_madera

    # n03 dries slower (k_factor = 0.5), so its humidity should be higher
    assert hm_humeda > hm_normal + 2.0

def test_falla_ventilador():
    config_normal = get_base_config()
    config_falla = get_base_config(escenario=Escenario.FALLA_VENTILADOR)

    sim_normal = SimuladorSecadero(config_normal)
    sim_falla = SimuladorSecadero(config_falla)

    for _ in range(100):
        sim_normal.paso(5.0, RelojMock())
        sim_falla.paso(5.0, RelojMock())

    hm_normal = sim_normal.estados["n01"].humedad_madera
    hm_falla = sim_falla.estados["n01"].humedad_madera
    hr_falla = sim_falla.estados["n01"].hr_aire

    assert hm_falla > hm_normal
    assert hr_falla > sim_normal.estados["n01"].hr_aire

def test_sensor_trabado():
    config = get_base_config(escenario=Escenario.SENSOR_TRABADO)
    sim = SimuladorSecadero(config)

    lecturas1 = sim.paso(5.0, RelojMock())
    lecturas2 = sim.paso(5.0, RelojMock())

    def get_hm(lecturas, nodo):
        for l in lecturas:
            if l.nodo == nodo and l.variable == Variable.HUMEDAD_MADERA:
                return l.valor
        return None

    assert get_hm(lecturas1, "n05") == get_hm(lecturas2, "n05")
    assert get_hm(lecturas1, "n01") != get_hm(lecturas2, "n01")

def test_normal_boundaries_and_noise():
    config = get_base_config()
    sim = SimuladorSecadero(config)

    # Run until it should be below 8
    for _ in range(10000):
        sim.paso(5.0, RelojMock())

    # State should never go below 8
    for nodo, estado in sim.estados.items():
        assert estado.humedad_madera >= 8.0

    # Test that normal scenario max diff is <= 2
    lecturas = list(sim.paso(5.0, RelojMock()))
    hms = [l.valor for l in lecturas if l.variable == Variable.HUMEDAD_MADERA]

    max_hm = max(hms)
    min_hm = min(hms)

    assert max_hm - min_hm <= 2.0
