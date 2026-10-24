from typing import Mapping
from secasmart.contracts.tipos import Lectura

class SerializadorJSON:
    """Implementación de SerializadorLectura."""

    def topic(self, lectura: Lectura) -> str:
        return f"secadero/{lectura.camara}/{lectura.nodo}/{lectura.variable.value}"

    def payload(self, lectura: Lectura) -> Mapping[str, object]:
        return {
            "ts": lectura.ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "camara": lectura.camara,
            "nodo": lectura.nodo,
            "variable": lectura.variable.value,
            "valor": round(lectura.valor, 2),
            "unidad": lectura.unidad
        }
