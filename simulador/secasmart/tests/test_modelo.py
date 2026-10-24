import pytest
import random
from secasmart.contracts.tipos import Especie, EstadoNodo
from secasmart.simulacion.modelo import ModeloSecadoFisico

def test_estado_inicial():
    rng = random.Random(42)
    modelo = ModeloSecadoFisico(Especie.PINO, rng)
    estado = modelo.estado_inicial("n01")

    assert estado.nodo == "n01"
    assert estado.humedad_madera == 60.0
    assert estado.temp_aire == 40.0
    assert estado.hr_aire == 95.0

def test_avanzar_reduce_humedad():
    rng = random.Random(42) # fixed seed
    modelo = ModeloSecadoFisico(Especie.PINO, rng)
    estado = EstadoNodo(nodo="n01", humedad_madera=60.0, temp_aire=40.0, hr_aire=95.0)

    nuevo_estado = modelo.avanzar(estado, 10000.0) # 10000 segundos for more noticeable change

    assert nuevo_estado.humedad_madera < 60.0
    # Because there is a noise uniform(-1, 1), the baseline temp_aire increases as progress happens.
    # At 10000 seconds, progress should be enough to overcome the noise.
    assert nuevo_estado.temp_aire > 40.0
    assert nuevo_estado.hr_aire < 95.0

def test_diferencia_especies():
    rng_pino = random.Random(42)
    rng_euca = random.Random(42)

    modelo_pino = ModeloSecadoFisico(Especie.PINO, rng_pino)
    modelo_euca = ModeloSecadoFisico(Especie.EUCALIPTO, rng_euca)

    estado_pino = EstadoNodo(nodo="n01", humedad_madera=60.0, temp_aire=40.0, hr_aire=95.0)
    estado_euca = EstadoNodo(nodo="n01", humedad_madera=60.0, temp_aire=40.0, hr_aire=95.0)

    nuevo_pino = modelo_pino.avanzar(estado_pino, 1000.0)
    nuevo_euca = modelo_euca.avanzar(estado_euca, 1000.0)

    # Pino seca más rápido, por lo que su humedad debe ser menor
    assert nuevo_pino.humedad_madera < nuevo_euca.humedad_madera
