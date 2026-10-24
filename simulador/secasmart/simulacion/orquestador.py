from datetime import datetime, timezone
from typing import Iterable, Dict
from secasmart.contracts.tipos import ConfigSimulacion, Lectura, EstadoNodo, Variable
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

        # 3. Generar lecturas
        ts = self.reloj.ahora_utc()
        lecturas = []

        for nodo, estado in self.estados.items():
            lecturas.append(Lectura(ts=ts, camara=self.config.camara, nodo=nodo, variable=Variable.TEMP_AIRE, valor=estado.temp_aire, unidad="°C"))
            lecturas.append(Lectura(ts=ts, camara=self.config.camara, nodo=nodo, variable=Variable.HR_AIRE, valor=estado.hr_aire, unidad="%"))
            lecturas.append(Lectura(ts=ts, camara=self.config.camara, nodo=nodo, variable=Variable.HUMEDAD_MADERA, valor=estado.humedad_madera, unidad="%"))

        return lecturas
