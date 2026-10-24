import os
import time
from secasmart.contracts.tipos import ConfigSimulacion, Escenario, Especie
from secasmart.simulacion.modelo import ModeloSecadoFisico
from secasmart.simulacion.escenario import AplicadorFallas
from secasmart.simulacion.orquestador import SimuladorOrquestador
from secasmart.telemetria.serializador import SerializadorJSON
from secasmart.telemetria.publicador import PublicadorMQTT

def parse_config() -> ConfigSimulacion:
    broker = os.getenv('MQTT_BROKER', 'mosquitto')
    puerto = int(os.getenv('MQTT_PORT', 1883))
    sim_speed = float(os.getenv('SIM_SPEED', 1.0))

    escenario_str = os.getenv('SCENARIO', 'normal')
    try:
        escenario = Escenario(escenario_str)
    except ValueError:
        escenario = Escenario.NORMAL

    especie_str = os.getenv('ESPECIE', 'pino')
    try:
        especie = Especie(especie_str)
    except ValueError:
        especie = Especie.PINO

    return ConfigSimulacion(
        broker=broker,
        puerto=puerto,
        sim_speed=sim_speed,
        escenario=escenario,
        especie=especie
    )

def main():
    config = parse_config()
    print(f"Iniciando simulador con configuración: {config}")

    modelo = ModeloSecadoFisico(config.especie)
    aplicador = AplicadorFallas(config.escenario)
    simulador = SimuladorOrquestador(config, modelo, aplicador)

    serializador = SerializadorJSON()
    publicador = PublicadorMQTT(config, serializador)

    publicador.conectar()

    try:
        while True:
            # We sleep for the real publication period (5.0s)
            time.sleep(config.periodo_publicacion_s)

            # Step the simulation by the same real time that elapsed
            lecturas = simulador.paso(config.periodo_publicacion_s)

            for lectura in lecturas:
                publicador.publicar(lectura)

    except KeyboardInterrupt:
        print("Simulación detenida por el usuario.")
    finally:
        publicador.cerrar()

if __name__ == "__main__":
    main()
