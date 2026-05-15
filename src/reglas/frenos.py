"""
Reglas de diagnóstico para el sistema de frenos.

Cubre: pastillas, discos, pinzas, líquido de frenos.
Casos de prueba cubiertos: 1, 2, 3, 4, 5.
"""

from src.constantes import (
    URGENCIA_CRITICA, URGENCIA_ALTA,
    SEGURO_NO, SEGURO_CON_PRECAUCION,
    RUIDO_CHIRRIDO, CUANDO_AL_FRENAR,
    VIBRACION_PEDAL_FRENO,
    FRENO_VIBRA, FRENO_TARDA_MAS, FRENO_SE_VA_LADO,
    SISTEMA_FRENOS,
)

# ---------------------------------------------------------------------------
# Identificadores de reglas (usados en reglas_disparadas)
# ---------------------------------------------------------------------------
_R_PASTILLAS_DESGASTADAS = "frenos.pastillas_desgastadas"
_R_DISCOS_DEFORMADOS = "frenos.discos_deformados"
_R_PINZA_TRABADA = "frenos.pinza_trabada"
_R_LIQUIDO_BAJO = "frenos.liquido_bajo_o_contaminado"
_R_PASTILLAS_Y_DISCOS = "frenos.pastillas_y_discos_mal_estado"


def _regla_pastillas_y_discos(s: dict) -> bool:
    """
    Condición: chirrido al frenar + vibración en pedal de freno + freno vibra.
    Combinación grave: pastillas y discos deteriorados simultáneamente.
    Prioridad máxima dentro del módulo — se evalúa primero.
    """
    return (
        s.get("ruido") == RUIDO_CHIRRIDO
        and s.get("cuando_ruido") == CUANDO_AL_FRENAR
        and s.get("vibracion") is True
        and s.get("donde_vibracion") == VIBRACION_PEDAL_FRENO
        and s.get("comportamiento_freno") == FRENO_VIBRA
    )


def _regla_pastillas_desgastadas(s: dict) -> bool:
    """
    Condición: chirrido al frenar, sin la combinación pastillas+discos.
    Desgaste de pastillas sin deterioro avanzado del disco.
    """
    return (
        s.get("ruido") == RUIDO_CHIRRIDO
        and s.get("cuando_ruido") == CUANDO_AL_FRENAR
        and not _regla_pastillas_y_discos(s)
    )


def _regla_discos_deformados(s: dict) -> bool:
    """
    Condición: vibración en pedal de freno + freno vibra, sin chirrido.
    Indica deformación (runout) de discos sin desgaste crítico de pastillas.
    """
    return (
        s.get("vibracion") is True
        and s.get("donde_vibracion") == VIBRACION_PEDAL_FRENO
        and s.get("comportamiento_freno") == FRENO_VIBRA
        and s.get("ruido") != RUIDO_CHIRRIDO
    )


def _regla_pinza_trabada(s: dict) -> bool:
    """
    Condición: freno se va hacia un lado.
    La pinza atascada aplica presión desigual → desvío lateral crítico.
    Nota: El módulo de suspensión también tiene regla de 'se_va_hacia_un_lado',
    pero frenos tiene prioridad mayor en el motor principal. Este módulo solo
    dispara esta regla cuando el síntoma está clasificado como comportamiento
    del freno, lo que la distingue del caso de desalineación (caso 24).
    """
    return s.get("comportamiento_freno") == FRENO_SE_VA_LADO


def _regla_liquido_bajo(s: dict) -> bool:
    """
    Condición: freno tarda más de lo normal en responder.
    Indica presión hidráulica insuficiente por nivel bajo o contaminación.
    """
    return s.get("comportamiento_freno") == FRENO_TARDA_MAS


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def diagnosticar(sintomas: dict) -> dict | None:
    """Evalúa los síntomas contra las reglas del sistema de frenos.

    Orden de evaluación (de mayor a menor gravedad):
      1. pastillas_y_discos      → critica (combinación peor caso)
      2. pinza_trabada           → critica (desvío lateral)
      3. pastillas_desgastadas   → alta
      4. discos_deformados       → alta
      5. liquido_bajo            → alta

    Args:
        sintomas: Dict con claves ruido, cuando_ruido, humo, vibracion,
            donde_vibracion, temperatura, luces, comportamiento_freno,
            perdida_potencia, liquido_piso.

    Returns:
        Dict con diagnostico, urgencia, seguro_manejar, accion,
        reglas_disparadas y sistema. None si ninguna regla aplica.
    """
    reglas_disparadas = []

    # Regla 1: peor caso — pastillas y discos combinados (caso 5)
    if _regla_pastillas_y_discos(sintomas):
        reglas_disparadas.append(_R_PASTILLAS_Y_DISCOS)
        return {
            "diagnostico": "Pastillas y discos en mal estado",
            "urgencia": URGENCIA_CRITICA,
            "seguro_manejar": SEGURO_NO,
            "accion": (
                "Detener el vehículo de forma segura. "
                "No conducir. Reemplazar pastillas y discos de inmediato."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_FRENOS,
        }

    # Regla 2: pinza de freno trabada (caso 3)
    if _regla_pinza_trabada(sintomas):
        reglas_disparadas.append(_R_PINZA_TRABADA)
        return {
            "diagnostico": "Pinza de freno trabada",
            "urgencia": URGENCIA_CRITICA,
            "seguro_manejar": SEGURO_NO,
            "accion": (
                "No conducir. Remolcar al taller. "
                "Inspeccionar y reemplazar la pinza afectada."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_FRENOS,
        }

    # Regla 3: pastillas desgastadas sin combo disco (caso 1)
    if _regla_pastillas_desgastadas(sintomas):
        reglas_disparadas.append(_R_PASTILLAS_DESGASTADAS)
        return {
            "diagnostico": "Pastillas de freno desgastadas",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller esta semana. "
                "Evitar frenadas bruscas hasta el reemplazo."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_FRENOS,
        }

    # Regla 4: discos deformados (caso 2)
    if _regla_discos_deformados(sintomas):
        reglas_disparadas.append(_R_DISCOS_DEFORMADOS)
        return {
            "diagnostico": "Discos de freno deformados",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller pronto. "
                "Rectificar o reemplazar discos de freno."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_FRENOS,
        }

    # Regla 5: líquido de frenos bajo o contaminado (caso 4)
    if _regla_liquido_bajo(sintomas):
        reglas_disparadas.append(_R_LIQUIDO_BAJO)
        return {
            "diagnostico": "Liquido de frenos bajo o contaminado",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Verificar y reponer nivel de líquido de frenos. "
                "Si persiste, revisar fugas y purgar el sistema."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_FRENOS,
        }

    return None
