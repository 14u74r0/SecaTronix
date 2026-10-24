import random
from datetime import datetime, timezone
from typing import Iterable, Dict
from secasmart.contracts.tipos import ConfigSimulacion, Lectura, EstadoNodo, Variable, Escenario
from secasmart.contracts.simulacion import ModeloSecado, AplicadorEscenario
from secasmart.contracts.telemetria import Reloj

class RelojReal:
    def ahora_utc(self) -> datetime:
        return datetime.now(timezone.utc)

class SimuladorOrquestador:
    """Implementación de Simulador."""

    def __init__(self, config: ConfigSimulacion, modelo: ModeloSecado, aplicador: AplicadorEscenario, reloj: Reloj = None):
        self.config = config
        self.modelo = modelo
        self.aplicador = aplicador
        self.reloj = reloj or RelojReal()

        self.estados: Dict[str, EstadoNodo] = {}
        for nodo in self.config.nodos:
            self.estados[nodo] = self.modelo.estado_inicial(nodo)

    def paso(self, dt_real_s: float) -> Iterable[Lectura]:
        dt_simulado_s = dt_real_s * self.config.sim_speed

        # 1. Avanzar modelo físico
        nuevos_estados = {}
        for nodo, estado in self.estados.items():
            nuevos_estados[nodo] = self.modelo.avanzar(estado, dt_simulado_s)

        # 2. Aplicar escenario/fallas
        self.estados = self.aplicador.aplicar(nuevos_estados, dt_simulado_s)

        # 3. Generar lecturas con ruido
        ts = self.reloj.ahora_utc()
        lecturas = []

        rng = getattr(self.modelo, 'rng', random.Random())

        if not hasattr(self, '_last_published'):
            self._last_published = {}
            self._last_state = {}

        for nodo, estado in self.estados.items():
            needs_new_noise = True

            if self.config.escenario == Escenario.SENSOR_TRABADO and nodo == "n05":
                if nodo in self._last_state:
                    prev_est = self._last_state[nodo]
                    if (prev_est.humedad_madera == estado.humedad_madera and
                        prev_est.temp_aire == estado.temp_aire and
                        prev_est.hr_aire == estado.hr_aire):
                        needs_new_noise = False

            if needs_new_noise:
                temp_ruido = estado.temp_aire + rng.uniform(-1.0, 1.0)
                hr_ruido = max(0.0, min(100.0, estado.hr_aire + rng.uniform(-2.0, 2.0)))
                hm_ruido = max(8.0, estado.humedad_madera + rng.uniform(-0.1, 0.1))

                self._last_published[nodo] = (temp_ruido, hr_ruido, hm_ruido)
                self._last_state[nodo] = estado
            else:
                temp_ruido, hr_ruido, hm_ruido = self._last_published[nodo]

            lecturas.append(Lectura(ts=ts, camara=self.config.camara, nodo=nodo, variable=Variable.TEMP_AIRE, valor=round(temp_ruido, 2), unidad="°C"))
            lecturas.append(Lectura(ts=ts, camara=self.config.camara, nodo=nodo, variable=Variable.HR_AIRE, valor=round(hr_ruido, 2), unidad="%"))
            lecturas.append(Lectura(ts=ts, camara=self.config.camara, nodo=nodo, variable=Variable.HUMEDAD_MADERA, valor=round(hm_ruido, 2), unidad="%"))

        return lecturas
