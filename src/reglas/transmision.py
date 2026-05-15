"""
Reglas de diagnóstico para el sistema de transmisión.

Cubre: cojinetes, embrague/caja, fuga de aceite, diferencial/semiejes.
Casos de prueba cubiertos: 16, 17, 18, 19, 20.
"""

from src.constantes import (
    URGENCIA_ALTA, URGENCIA_MODERADA,
    SEGURO_CON_PRECAUCION,
    RUIDO_ZUMBIDO, RUIDO_GOLPETEO,
    CUANDO_AL_ACELERAR, CUANDO_SIEMPRE, CUANDO_EN_NEUTRO,
    LUZ_ACEITE,
    LIQUIDO_ACEITE,
    SISTEMA_TRANSMISION,
)

# ---------------------------------------------------------------------------
# Identificadores de reglas
# ---------------------------------------------------------------------------
_R_DIFERENCIAL_SEMIEJES = "transmision.diferencial_semiejes"
_R_CAJA_INTERNA = "transmision.problema_caja_interna"
_R_TIRONES_EMBRAGUE = "transmision.tirones_embrague_caja"
_R_COJINETE = "transmision.cojinete_desgastado"
_R_FUGA_ACEITE = "transmision.fuga_aceite_transmision"


def _regla_diferencial_semiejes(s: dict) -> bool:
    """
    Condición: zumbido constante (siempre) + pérdida de potencia.
    Indica falla en diferencial o semiejes bajo carga sostenida.
    Prioridad máxima: combina más síntomas que el cojinete simple.
    """
    return (
        s.get("ruido") == RUIDO_ZUMBIDO
        and s.get("cuando_ruido") == CUANDO_SIEMPRE
        and s.get("perdida_potencia") is True
    )


def _regla_caja_interna(s: dict) -> bool:
    """
    Condición: golpeteo en neutro.
    El golpeteo en ralentí sin carga apunta a problema interno de la caja.
    """
    return (
        s.get("ruido") == RUIDO_GOLPETEO
        and s.get("cuando_ruido") == CUANDO_EN_NEUTRO
    )


def _regla_tirones_embrague(s: dict) -> bool:
    """
    Condición: pérdida de potencia sin humo, sin ruido, sin luces de advertencia.
    Tirones al cambiar sin otras señales apuntan a embrague o caja de cambios.
    """
    return (
        s.get("perdida_potencia") is True
        and s.get("ruido") == "ninguno"
        and s.get("humo") == "ninguno"
        and s.get("luces") == "ninguna"
    )


def _regla_cojinete(s: dict) -> bool:
    """
    Condición: zumbido al acelerar.
    Zumbido bajo carga sin pérdida de potencia indica cojinete de transmisión.
    """
    return (
        s.get("ruido") == RUIDO_ZUMBIDO
        and s.get("cuando_ruido") == CUANDO_AL_ACELERAR
        and not _regla_diferencial_semiejes(s)
    )


def _regla_fuga_aceite(s: dict) -> bool:
    """
    Condición: aceite en el piso sin luz de aceite encendida.
    La luz apagada descarta el motor; el aceite en suelo apunta a caja o diferencial.
    """
    return (
        s.get("liquido_piso") == LIQUIDO_ACEITE
        and s.get("luces") != LUZ_ACEITE
    )


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def diagnosticar(sintomas: dict) -> dict | None:
    """Evalúa los síntomas contra las reglas del sistema de transmisión.

    Orden de evaluación (mayor a menor gravedad):
      1. diferencial_semiejes  → alta (más síntomas combinados)
      2. caja_interna          → alta
      3. tirones_embrague      → alta
      4. cojinete              → moderada
      5. fuga_aceite           → moderada

    Args:
        sintomas: Dict con claves ruido, cuando_ruido, humo, vibracion,
            donde_vibracion, temperatura, luces, comportamiento_freno,
            perdida_potencia, liquido_piso.

    Returns:
        Dict con diagnostico, urgencia, seguro_manejar, accion,
        reglas_disparadas y sistema. None si ninguna regla aplica.
    """
    reglas_disparadas = []

    # Regla 1: diferencial o semiejes (caso 20)
    if _regla_diferencial_semiejes(sintomas):
        reglas_disparadas.append(_R_DIFERENCIAL_SEMIEJES)
        return {
            "diagnostico": "Falla en diferencial o semiejes",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller con urgencia. "
                "Inspeccionar diferencial, semiejes y juntas homocinéticas."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_TRANSMISION,
        }

    # Regla 2: problema interno caja (caso 18)
    if _regla_caja_interna(sintomas):
        reglas_disparadas.append(_R_CAJA_INTERNA)
        return {
            "diagnostico": "Problema interno en caja de cambios",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller. "
                "Revisar sincronizadores y engranajes internos de la caja."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_TRANSMISION,
        }

    # Regla 3: tirones embrague/caja (caso 17)
    if _regla_tirones_embrague(sintomas):
        reglas_disparadas.append(_R_TIRONES_EMBRAGUE)
        return {
            "diagnostico": "Tirones al cambiar - embrague o caja",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller. "
                "Inspeccionar embrague, cable de embrague y caja de cambios."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_TRANSMISION,
        }

    # Regla 4: cojinete de transmisión (caso 16)
    if _regla_cojinete(sintomas):
        reglas_disparadas.append(_R_COJINETE)
        return {
            "diagnostico": "Cojinete de transmision desgastado",
            "urgencia": URGENCIA_MODERADA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Programar revisión en el taller. "
                "Reemplazar cojinete antes de que falle completamente."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_TRANSMISION,
        }

    # Regla 5: fuga de aceite de transmisión (caso 19)
    if _regla_fuga_aceite(sintomas):
        reglas_disparadas.append(_R_FUGA_ACEITE)
        return {
            "diagnostico": "Fuga de aceite de transmision",
            "urgencia": URGENCIA_MODERADA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Verificar nivel de aceite de transmisión. "
                "Llevar al taller para identificar y sellar la fuga."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_TRANSMISION,
        }

    return None
