"""
Reglas de diagnóstico para el sistema de refrigeración.

Cubre: recalentamiento crítico, fugas de refrigerante, problemas de
radiador/tapa de expansión, y fallo combinado motor-refrigeración.
Casos de prueba cubiertos: 11, 12, 13, 14, 15.
"""

from src.constantes import (
    URGENCIA_CRITICA, URGENCIA_ALTA, URGENCIA_MODERADA,
    SEGURO_NO, SEGURO_CON_PRECAUCION, SEGURO_SI,
    HUMO_BLANCO,
    TEMP_ALTA, TEMP_MUY_ALTA,
    LUZ_TEMPERATURA,
    LIQUIDO_REFRIGERANTE,
    SISTEMA_REFRIGERACION,
)

# ---------------------------------------------------------------------------
# Identificadores de reglas
# ---------------------------------------------------------------------------
_R_FALLA_MULTIPLE = "refrigeracion.falla_multiple_motor_refrigeracion"
_R_RECALENTAMIENTO_CRITICO = "refrigeracion.recalentamiento_critico"
_R_FUGA_CON_RECALENTAMIENTO = "refrigeracion.fuga_con_recalentamiento"
_R_RADIADOR_TAPA = "refrigeracion.radiador_tapa_expansion"
_R_FUGA_SIN_RECALENTAMIENTO = "refrigeracion.fuga_sin_recalentamiento"


def _regla_falla_multiple(s: dict) -> bool:
    """
    Condición: temperatura muy alta + luz de temperatura + pérdida de potencia
    + refrigerante en el piso.
    Fallo combinado del motor y el sistema de refrigeración: máxima gravedad.
    Evaluada primero para no confundirse con recalentamiento simple.
    """
    return (
        s.get("temperatura") == TEMP_MUY_ALTA
        and s.get("luces") == LUZ_TEMPERATURA
        and s.get("perdida_potencia") is True
        and s.get("liquido_piso") == LIQUIDO_REFRIGERANTE
    )


def _regla_recalentamiento_critico(s: dict) -> bool:
    """
    Condición: temperatura muy alta + luz de temperatura, sin pérdida de
    potencia ni refrigerante en el piso (no es fuga activa ni falla múltiple).
    Indica sobrecalentamiento severo: termostato bloqueado, bomba muerta, etc.
    """
    return (
        s.get("temperatura") == TEMP_MUY_ALTA
        and s.get("luces") == LUZ_TEMPERATURA
        and s.get("perdida_potencia") is not True
        and s.get("liquido_piso") != LIQUIDO_REFRIGERANTE
    )


def _regla_fuga_con_recalentamiento(s: dict) -> bool:
    """
    Condición: temperatura alta (no muy_alta) + luz de temperatura
    + refrigerante en el piso.
    Fuga activa que provoca recalentamiento moderado.
    """
    return (
        s.get("temperatura") == TEMP_ALTA
        and s.get("luces") == LUZ_TEMPERATURA
        and s.get("liquido_piso") == LIQUIDO_REFRIGERANTE
    )


def _regla_radiador_tapa(s: dict) -> bool:
    """
    Condición: humo blanco + temperatura alta, sin refrigerante en piso.
    El vapor blanco sin líquido en el suelo sugiere problema en radiador
    o tapa de expansión (pérdida por el tapón, no por manguera).
    """
    return (
        s.get("humo") == HUMO_BLANCO
        and s.get("temperatura") == TEMP_ALTA
        and s.get("liquido_piso") != LIQUIDO_REFRIGERANTE
    )


def _regla_fuga_sin_recalentamiento(s: dict) -> bool:
    """
    Condición: refrigerante en el piso, temperatura normal, sin luz.
    Fuga pasiva que aún no causó recalentamiento: grieta en manguera, etc.
    """
    return (
        s.get("liquido_piso") == LIQUIDO_REFRIGERANTE
        and s.get("temperatura") == "normal"
        and s.get("luces") != LUZ_TEMPERATURA
    )


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def diagnosticar(sintomas: dict) -> dict | None:
    """Evalúa los síntomas contra las reglas del sistema de refrigeración.

    Orden de evaluación (mayor a menor gravedad):
      1. falla_multiple              → critica
      2. recalentamiento_critico     → critica
      3. fuga_con_recalentamiento    → alta
      4. radiador_tapa               → alta
      5. fuga_sin_recalentamiento    → moderada

    Args:
        sintomas: Dict con claves ruido, cuando_ruido, humo, vibracion,
            donde_vibracion, temperatura, luces, comportamiento_freno,
            perdida_potencia, liquido_piso.

    Returns:
        Dict con diagnostico, urgencia, seguro_manejar, accion,
        reglas_disparadas y sistema. None si ninguna regla aplica.
    """
    reglas_disparadas = []

    # Regla 1: falla múltiple motor-refrigeración (caso 15)
    if _regla_falla_multiple(sintomas):
        reglas_disparadas.append(_R_FALLA_MULTIPLE)
        return {
            "diagnostico": "Falla multiple motor-refrigeracion",
            "urgencia": URGENCIA_CRITICA,
            "seguro_manejar": SEGURO_NO,
            "accion": (
                "Apagar el motor de inmediato. No conducir. "
                "Remolcar al taller. Posible daño grave en motor."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_REFRIGERACION,
        }

    # Regla 2: recalentamiento crítico sin fuga activa (caso 11)
    if _regla_recalentamiento_critico(sintomas):
        reglas_disparadas.append(_R_RECALENTAMIENTO_CRITICO)
        return {
            "diagnostico": "Recalentamiento critico del motor",
            "urgencia": URGENCIA_CRITICA,
            "seguro_manejar": SEGURO_NO,
            "accion": (
                "Apagar el motor inmediatamente. Dejar enfriar. "
                "No abrir la tapa del radiador en caliente. Remolcar al taller."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_REFRIGERACION,
        }

    # Regla 3: fuga con recalentamiento moderado (caso 12)
    if _regla_fuga_con_recalentamiento(sintomas):
        reglas_disparadas.append(_R_FUGA_CON_RECALENTAMIENTO)
        return {
            "diagnostico": "Fuga en sistema de refrigeracion",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Reponer refrigerante y dirigirse al taller con precaución. "
                "Monitorear temperatura constantemente."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_REFRIGERACION,
        }

    # Regla 4: problema en radiador o tapa de expansión (caso 13)
    if _regla_radiador_tapa(sintomas):
        reglas_disparadas.append(_R_RADIADOR_TAPA)
        return {
            "diagnostico": "Problema en radiador o tapa de expansion",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller con urgencia. "
                "Revisar tapa de expansión, radiador y mangueras."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_REFRIGERACION,
        }

    # Regla 5: fuga pasiva sin recalentamiento (caso 14)
    if _regla_fuga_sin_recalentamiento(sintomas):
        reglas_disparadas.append(_R_FUGA_SIN_RECALENTAMIENTO)
        return {
            "diagnostico": "Fuga de refrigerante sin recalentamiento",
            "urgencia": URGENCIA_MODERADA,
            "seguro_manejar": SEGURO_SI,
            "accion": (
                "Llevar al taller durante la semana. "
                "Verificar nivel de refrigerante antes de cada viaje."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_REFRIGERACION,
        }

    return None
