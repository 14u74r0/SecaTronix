from typing import Dict, Optional
import copy
from secasmart.contracts.tipos import Escenario, EstadoNodo

class AplicadorFallas:
    """Implementación de AplicadorEscenario."""

    def __init__(self, escenario: Escenario):
        self.escenario = escenario
        self.stuck_values: Dict[str, EstadoNodo] = {}

    def aplicar(self, estados: dict[str, EstadoNodo], dt_simulado_s: float) -> dict[str, EstadoNodo]:
        if self.escenario == Escenario.NORMAL:
            return copy.deepcopy(estados)

        nuevos_estados = copy.deepcopy(estados)

        if self.escenario == Escenario.ZONA_HUMEDA:
            # Revertir parcialmente el avance en el nodo afectado (ej. n03 seca más lento)
            # Para simplificar, en un AplicadorEscenario posterior al avance del modelo
            # Podemos simular esto diciendo que n03 retiene más humedad artificialmente
            # pero una forma más robusta es aumentar la humedad.
            # Como AplicadorEscenario recibe los estados ya avanzados,
            # podemos deshacer parte del secado o sumarle humedad para frenar el progreso.
            if "n03" in nuevos_estados:
                # Una simplificación para "seca más lento": sumarle un delta
                # (aunque idealmente la física lo calcularía, el contrato dice que el aplicador inyecta fallas sobre estados).
                # Equivalente a la constante 0.5 del código original (seca a la mitad de velocidad).
                # Como no sabemos cuánto secó en este frame exactamente, podemos ralentizar agregando un pequeño factor.
                nuevos_estados["n03"].humedad_madera += dt_simulado_s * 0.0001
                # Evitar sobrepasar 100%
                nuevos_estados["n03"].humedad_madera = min(100.0, nuevos_estados["n03"].humedad_madera)

        elif self.escenario == Escenario.FALLA_VENTILADOR:
            for nodo, estado in nuevos_estados.items():
                estado.hr_aire += 20.0
                estado.hr_aire = min(100.0, estado.hr_aire)
                # También el secado se ralentiza drásticamente
                estado.humedad_madera += dt_simulado_s * 0.00015
                estado.humedad_madera = min(100.0, estado.humedad_madera)

        elif self.escenario == Escenario.SENSOR_TRABADO:
            if "n05" in nuevos_estados:
                if "n05" not in self.stuck_values:
                    self.stuck_values["n05"] = copy.deepcopy(nuevos_estados["n05"])
                else:
                    stuck = self.stuck_values["n05"]
                    nuevos_estados["n05"].humedad_madera = stuck.humedad_madera
                    nuevos_estados["n05"].temp_aire = stuck.temp_aire
                    nuevos_estados["n05"].hr_aire = stuck.hr_aire

        return nuevos_estados
