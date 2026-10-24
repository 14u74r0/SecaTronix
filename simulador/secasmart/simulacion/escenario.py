from typing import Dict, Optional
import copy
from secasmart.contracts.tipos import Escenario, EstadoNodo

class AplicadorFallas:
    """Implementación de AplicadorEscenario."""

    def __init__(self, escenario: Escenario):
        self.escenario = escenario
        self.stuck_values: Dict[str, EstadoNodo] = {}
        self.previous_states: Dict[str, EstadoNodo] = {}

    def aplicar(self, estados: dict[str, EstadoNodo], dt_simulado_s: float) -> dict[str, EstadoNodo]:
        if self.escenario == Escenario.NORMAL:
            self.previous_states = copy.deepcopy(estados)
            return copy.deepcopy(estados)

        nuevos_estados = copy.deepcopy(estados)

        for nodo, nuevo_est in nuevos_estados.items():
            if nodo in self.previous_states:
                prev_est = self.previous_states[nodo]
                target_humedad = 10.0

                factor = 1.0
                if self.escenario == Escenario.ZONA_HUMEDA and nodo == "n03":
                    factor = 0.5
                elif self.escenario == Escenario.FALLA_VENTILADOR:
                    factor = 0.3

                if factor != 1.0:
                    hm_viejo = prev_est.humedad_madera
                    hm_nuevo = nuevo_est.humedad_madera

                    if hm_viejo > target_humedad and hm_nuevo >= target_humedad:
                        ratio = (hm_nuevo - target_humedad) / (hm_viejo - target_humedad)
                        if ratio > 0:
                            hm_falla = target_humedad + (hm_viejo - target_humedad) * (ratio ** factor)
                        else:
                            hm_falla = hm_nuevo

                        hm_falla = max(8.0, hm_falla)
                        nuevo_est.humedad_madera = hm_falla

                        progress = 1.0 - (hm_falla - target_humedad) / (60.0 - target_humedad)
                        progress = max(0.0, min(1.0, progress))

                        nuevo_est.temp_aire = 40.0 + (40.0 * progress)
                        nuevo_est.hr_aire = 95.0 - (65.0 * progress)

            if self.escenario == Escenario.FALLA_VENTILADOR:
                nuevo_est.hr_aire = min(100.0, nuevo_est.hr_aire + 20.0)

            if self.escenario == Escenario.SENSOR_TRABADO and nodo == "n05":
                if nodo not in self.stuck_values:
                    self.stuck_values[nodo] = copy.deepcopy(nuevo_est)
                else:
                    stuck = self.stuck_values[nodo]
                    nuevo_est.humedad_madera = stuck.humedad_madera
                    nuevo_est.temp_aire = stuck.temp_aire
                    nuevo_est.hr_aire = stuck.hr_aire

        self.previous_states = copy.deepcopy(nuevos_estados)
        return nuevos_estados
