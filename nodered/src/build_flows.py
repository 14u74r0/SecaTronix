#!/usr/bin/env python3
"""Genera nodered/flows.json a partir de las funciones de nodered/src/*.js.

Uso (desde la raíz del repo):  python3 nodered/src/build_flows.py
flows.json se versiona (Docker lo monta tal cual); este script evita editar JavaScript dentro de un JSON.
Si se edita el flujo desde el editor de Node-RED, volver a reflejar el cambio acá o se pierde al regenerar.
"""
import json
import pathlib

SRC = pathlib.Path(__file__).resolve().parent
OUT = SRC.parent / "flows.json"
TAB = "tab_secasmart"


def js(nombre: str) -> str:
    return (SRC / f"{nombre}.js").read_text(encoding="utf-8")


def funcion(id_, nombre, archivo, x, y, wires, outputs=1):
    return {
        "id": id_, "type": "function", "z": TAB, "name": nombre, "func": js(archivo),
        "outputs": outputs, "timeout": 0, "noerr": 0, "initialize": "", "finalize": "", "libs": [],
        "x": x, "y": y, "wires": wires,
    }


def postgres(id_, nombre, x, y, wires=None):
    return {
        "id": id_, "type": "postgresql", "z": TAB, "name": nombre,
        "query": "-- La consulta llega en msg.query y los parámetros ($1, $2…) en msg.params",
        "postgreSQLConfig": "cfg_pg", "split": False, "rowsPerMsg": 1, "outputs": 1,
        "x": x, "y": y, "wires": wires or [[]],
    }


nodos = [
    {"id": TAB, "type": "tab", "label": "SecaSmart", "disabled": False,
     "info": "Ingesta MQTT → validación → lote → PostgreSQL, reglas de alerta → tabla alertas + MQTT. Ver docs/CONTRATO.md."},

    # --- Configuración compartida -------------------------------------------------------------
    {"id": "cfg_mqtt", "type": "mqtt-broker", "name": "Mosquitto", "broker": "mosquitto", "port": "1883",
     "clientid": "nodered-secasmart", "autoConnect": True, "usetls": False, "protocolVersion": "4",
     "keepalive": "60", "cleansession": True, "autoUnsubscribe": True,
     "birthTopic": "", "closeTopic": "", "willTopic": "", "birthQos": "0", "closeQos": "0", "willQos": "0"},
    {"id": "cfg_pg", "type": "postgreSQLConfig", "name": "PostgreSQL",
     "host": "POSTGRES_HOST", "hostFieldType": "env",
     "port": "POSTGRES_PORT", "portFieldType": "env",
     "database": "POSTGRES_DB", "databaseFieldType": "env",
     "ssl": "false", "sslFieldType": "bool",
     "applicationName": "secasmart-nodered", "applicationNameType": "str",
     "max": "10", "maxFieldType": "num", "idle": "1000", "idleFieldType": "num",
     "connectionTimeout": "10000", "connectionTimeoutFieldType": "num",
     "userFieldType": "env", "userEnv": "POSTGRES_USER",
     "passwordFieldType": "env", "passwordEnv": "POSTGRES_PASSWORD"},

    # --- Ingesta ------------------------------------------------------------------------------
    {"id": "in_mqtt", "type": "mqtt in", "z": TAB, "name": "secadero/+/+/+", "topic": "secadero/+/+/+",
     "qos": "1", "datatype": "json", "broker": "cfg_mqtt", "nl": False, "rap": True, "rh": 0, "inputs": 0,
     "x": 150, "y": 100, "wires": [["fn_validar"]]},
    funcion("fn_validar", "Validar lectura", "validar", 360, 100, [["fn_lote"], ["dbg_descartadas"]], outputs=2),
    {"id": "dbg_descartadas", "type": "debug", "z": TAB, "name": "Descartadas", "active": False, "tosidebar": True,
     "console": False, "tostatus": False, "complete": "payload", "targetType": "msg", "x": 590, "y": 40, "wires": []},

    funcion("fn_lote", "Asignar lote (caché 30 s)", "lote", 590, 100, [["fn_insert", "fn_reglas"], ["pg_lote"]], outputs=2),
    postgres("pg_lote", "Lote activo", 830, 160, [["fn_lote_cache"]]),
    funcion("fn_lote_cache", "Guardar lote en caché", "lote_cache", 1060, 160, [["fn_insert", "fn_reglas"]]),

    # --- Guardado de lecturas -----------------------------------------------------------------
    funcion("fn_insert", "Preparar INSERT lectura", "preparar_insert", 830, 240, [["pg_insert_lectura"]]),
    postgres("pg_insert_lectura", "INSERT lecturas", 1070, 240),

    # --- Reglas y alertas ---------------------------------------------------------------------
    funcion("fn_reglas", "Reglas de alerta", "reglas", 830, 320, [["fn_alerta"]]),
    funcion("fn_alerta", "Armar alerta", "armar_alerta", 1040, 320, [["pg_insert_alerta"], ["out_alertas"]], outputs=2),
    postgres("pg_insert_alerta", "INSERT alertas", 1260, 300),
    {"id": "out_alertas", "type": "mqtt out", "z": TAB, "name": "secadero/<camara>/alertas", "topic": "",
     "qos": "1", "retain": "false", "respTopic": "", "contentType": "", "userProps": "", "correl": "", "expiry": "",
     "broker": "cfg_mqtt", "x": 1290, "y": 360, "wires": []},

    # --- Errores ------------------------------------------------------------------------------
    {"id": "catch_all", "type": "catch", "z": TAB, "name": "Errores", "scope": None, "uncaught": False,
     "x": 150, "y": 440, "wires": [["dbg_errores"]]},
    {"id": "dbg_errores", "type": "debug", "z": TAB, "name": "Errores", "active": True, "tosidebar": True,
     "console": True, "tostatus": False, "complete": "true", "targetType": "full", "x": 350, "y": 440, "wires": []},
]

OUT.write_text(json.dumps(nodos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"OK: {OUT} ({len(nodos)} nodos)")
