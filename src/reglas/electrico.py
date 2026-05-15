"""
Reglas de diagnóstico para el sistema eléctrico.

Cubre: batería/alternador, falla de sensor/gestión del motor.
Casos de prueba cubiertos: 26, 27, 28.

Nota: los casos 26 y 28 tienen síntomas idénticos (solo luz de batería).
Ambos se mapean al diagnóstico "Bateria debil o alternador fallando".
"""

from src.constantes import (
    URGENCIA_ALTA, URGENCIA_MODERADA,
    SEGURO_CON_PRECAUCION,
    LUZ_BATERIA, LUZ_CHECK_ENGINE,
    SISTEMA_ELECTRICO,
)

# ---------------------------------------------------------------------------
# Identificadores de reglas
# ---------------------------------------------------------------------------
_R_BATERIA_ALTERNADOR = "electrico.bateria_o_alternador"
_R_SENSOR_GESTION = "electrico.sensor_gestion_motor"


def _regla_bateria_alternador(s: dict) -> bool:
    """
    Condición: luz de batería encendida.
    Puede indicar batería débil, alternador que no carga o circuito de carga.
    Cubre casos 26 y 28 (síntomas idénticos en el dataset).
    """
    return s.get("luces") == LUZ_BATERIA


def _regla_sensor_gestion(s: dict) -> bool:
    """
    Condición: luz check_engine + pérdida de potencia.
    Sin humo ni temperatura elevada, apunta a falla de sensor o ECU.
    """
    return (
        s.get("luces") == LUZ_CHECK_ENGINE
        and s.get("perdida_potencia") is True
    )


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def diagnosticar(sintomas: dict) -> dict | None:
    """Evalúa los síntomas contra las reglas del sistema eléctrico.

    Orden de evaluación (mayor a menor gravedad):
      1. bateria_alternador  → alta
      2. sensor_gestion      → moderada

    Args:
        sintomas: Dict con claves ruido, cuando_ruido, humo, vibracion,
            donde_vibracion, temperatura, luces, comportamiento_freno,
            perdida_potencia, liquido_piso.

    Returns:
        Dict con diagnostico, urgencia, seguro_manejar, accion,
        reglas_disparadas y sistema. None si ninguna regla aplica.
    """
    reglas_disparadas = []

    # Regla 1: batería débil o alternador (casos 26 y 28)
    if _regla_bateria_alternador(sintomas):
        reglas_disparadas.append(_R_BATERIA_ALTERNADOR)
        return {
            "diagnostico": "Bateria debil o alternador fallando",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller. "
                "Testear batería y alternador. Revisar correa de transmisión."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_ELECTRICO,
        }

    # Regla 2: falla de sensor o sistema de gestión (caso 27)
    if _regla_sensor_gestion(sintomas):
        reglas_disparadas.append(_R_SENSOR_GESTION)
        return {
            "diagnostico": "Falla en sensor o sistema de gestion",
            "urgencia": URGENCIA_MODERADA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Leer códigos de error con scanner OBD. "
                "Revisar sensores MAP, MAF, O2 y ECU."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_ELECTRICO,
        }

    return None
