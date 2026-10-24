import math
import random
from typing import Optional
from secasmart.contracts.tipos import Especie, EstadoNodo

class ModeloSecadoFisico:
    """Implementación de ModeloSecado."""

    def __init__(self, especie: Especie, rng: Optional[random.Random] = None):
        self.especie = especie
        self.rng = rng or random.Random()
        self.target_humedad = 10.0

        # Tasa de decaimiento. Pino seca más rápido que Eucalipto.
        self.k_base = 0.001 if especie == Especie.PINO else 0.0007

    def estado_inicial(self, nodo: str) -> EstadoNodo:
        humedad = 60.0 + self.rng.uniform(-1.0, 1.0)
        temp = 40.0 + self.rng.uniform(-1.0, 1.0)
        hr = 95.0 + self.rng.uniform(-2.0, 2.0)

        return EstadoNodo(
            nodo=nodo,
            humedad_madera=humedad,
            temp_aire=temp,
            hr_aire=hr
        )

    def avanzar(self, estado: EstadoNodo, dt_simulado_s: float) -> EstadoNodo:
        hm = estado.humedad_madera

        if hm > self.target_humedad:
            # Usando decaimiento exponencial exacto: H_nuevo = H_target + (H - H_target) * exp(-k * dt)
            # Para mantener coherencia con el código original, k era por step de 5s,
            # pero ahora tenemos dt_simulado_s que ya incorpora el tiempo y sim_speed
            # El k original era 0.001 por 5s, o sea 0.0002 / s. Ajustemos self.k_base:
            k = self.k_base / 5.0

            # H(t) = target + (H0 - target) * exp(-k * t)
            hm_nuevo = self.target_humedad + (hm - self.target_humedad) * math.exp(-k * dt_simulado_s)
        else:
            hm_nuevo = hm

        # Añadir ruido aleatorio a la humedad
        hm_nuevo += self.rng.uniform(-0.1, 0.1)

        # Progreso basado en la humedad (de 60 a 10)
        progress = 1.0 - (hm_nuevo - self.target_humedad) / (60.0 - self.target_humedad)
        progress = max(0.0, min(1.0, progress))

        # Temp base sube de 40 a 80
        base_temp = 40.0 + (40.0 * progress)
        # HR base baja de 95 a 30
        base_hr = 95.0 - (65.0 * progress)

        # Ruido
        temp_nuevo = base_temp + self.rng.uniform(-1.0, 1.0)
        hr_nuevo = max(0.0, min(100.0, base_hr + self.rng.uniform(-2.0, 2.0)))

        return EstadoNodo(
            nodo=estado.nodo,
            humedad_madera=hm_nuevo,
            temp_aire=temp_nuevo,
            hr_aire=hr_nuevo
        )
