"""
Reglas de diagnóstico para el motor de combustión interna.

Cubre: consumo de aceite, junta de culata, mezcla rica/inyectores,
detonación, presión de aceite baja y luz de aceite sin otros síntomas.
Casos de prueba cubiertos: 6, 7, 8, 9, 10, 29.
"""

from src.constantes import (
    URGENCIA_CRITICA, URGENCIA_ALTA, URGENCIA_MODERADA,
    SEGURO_NO, SEGURO_CON_PRECAUCION,
    RUIDO_GOLPETEO,
    CUANDO_AL_ACELERAR, CUANDO_SIEMPRE,
    HUMO_AZUL, HUMO_BLANCO, HUMO_NEGRO,
    TEMP_MUY_ALTA,
    LUZ_ACEITE, LUZ_TEMPERATURA, LUZ_CHECK_ENGINE,
    LIQUIDO_ACEITE, LIQUIDO_REFRIGERANTE,
    SISTEMA_MOTOR,
)

# ---------------------------------------------------------------------------
# Identificadores de reglas
# ---------------------------------------------------------------------------
_R_QUEMA_ACEITE = "motor.quema_aceite_anillos_guias"
_R_JUNTA_CULATA = "motor.junta_culata_refrigerante"
_R_MEZCLA_RICA = "motor.mezcla_rica_inyectores"
_R_DETONACION = "motor.detonacion_combustion"
_R_PRESION_ACEITE_COJINETES = "motor.presion_aceite_baja_cojinetes"
_R_LUZ_ACEITE_SOLA = "motor.luz_aceite_nivel_bomba"


def _regla_presion_aceite_cojinetes(s: dict) -> bool:
    """
    Condición: golpeteo constante (siempre) + luz de aceite + pérdida de
    potencia + líquido de aceite en el piso.
    Combinación crítica: presión baja con probable daño en cojinetes.
    Máxima prioridad dentro del módulo.
    """
    return (
        s.get("ruido") == RUIDO_GOLPETEO
        and s.get("cuando_ruido") == CUANDO_SIEMPRE
        and s.get("luces") == LUZ_ACEITE
        and s.get("perdida_potencia") is True
        and s.get("liquido_piso") == LIQUIDO_ACEITE
    )


def _regla_junta_culata(s: dict) -> bool:
    """
    Condición: humo blanco + temperatura muy alta + luz de temperatura
    + líquido refrigerante en el piso.
    Indica fuga de refrigerante hacia la cámara de combustión: junta culata.
    """
    return (
        s.get("humo") == HUMO_BLANCO
        and s.get("temperatura") == TEMP_MUY_ALTA
        and s.get("luces") == LUZ_TEMPERATURA
        and s.get("liquido_piso") == LIQUIDO_REFRIGERANTE
    )


def _regla_quema_aceite(s: dict) -> bool:
    """
    Condición: humo azul + luz de aceite + pérdida de potencia
    + aceite en el piso.
    Indica consumo interno de aceite por anillos desgastados o guías de válvula.
    """
    return (
        s.get("humo") == HUMO_AZUL
        and s.get("luces") == LUZ_ACEITE
        and s.get("perdida_potencia") is True
        and s.get("liquido_piso") == LIQUIDO_ACEITE
    )


def _regla_mezcla_rica(s: dict) -> bool:
    """
    Condición: humo negro + luz check_engine + pérdida de potencia.
    Indica mezcla aire-combustible demasiado rica o inyectores obstruidos.
    """
    return (
        s.get("humo") == HUMO_NEGRO
        and s.get("luces") == LUZ_CHECK_ENGINE
        and s.get("perdida_potencia") is True
    )


def _regla_detonacion(s: dict) -> bool:
    """
    Condición: golpeteo al acelerar (knocking), sin luz de aceite ni pérdida.
    Indica detonación prematura o problema en la combustión.
    """
    return (
        s.get("ruido") == RUIDO_GOLPETEO
        and s.get("cuando_ruido") == CUANDO_AL_ACELERAR
        and s.get("luces") != LUZ_ACEITE
    )


def _regla_luz_aceite_sola(s: dict) -> bool:
    """
    Condición: luz de aceite encendida + aceite en piso, sin golpeteo
    ni pérdida de potencia severa.
    Indica presión de aceite baja por nivel bajo o falla de bomba,
    antes de que haya daño en cojinetes.
    """
    return (
        s.get("luces") == LUZ_ACEITE
        and s.get("liquido_piso") == LIQUIDO_ACEITE
        and s.get("ruido") != RUIDO_GOLPETEO
    )


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def diagnosticar(sintomas: dict) -> dict | None:
    """Evalúa los síntomas contra las reglas del motor de combustión interna.

    Orden de evaluación (mayor a menor gravedad):
      1. presion_aceite_cojinetes → critica
      2. junta_culata             → critica
      3. quema_aceite             → moderada
      4. mezcla_rica              → moderada
      5. detonacion               → alta
      6. luz_aceite_sola          → alta

    Args:
        sintomas: Dict con claves ruido, cuando_ruido, humo, vibracion,
            donde_vibracion, temperatura, luces, comportamiento_freno,
            perdida_potencia, liquido_piso.

    Returns:
        Dict con diagnostico, urgencia, seguro_manejar, accion,
        reglas_disparadas y sistema. None si ninguna regla aplica.
    """
    reglas_disparadas = []

    # Regla 1: presión de aceite baja con cojinetes (caso 10)
    if _regla_presion_aceite_cojinetes(sintomas):
        reglas_disparadas.append(_R_PRESION_ACEITE_COJINETES)
        return {
            "diagnostico": "Presion de aceite baja o cojinetes desgastados",
            "urgencia": URGENCIA_CRITICA,
            "seguro_manejar": SEGURO_NO,
            "accion": (
                "Apagar el motor de inmediato. No arrancar. "
                "Remolcar al taller. Riesgo de destrucción del motor."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_MOTOR,
        }

    # Regla 2: junta de culata (caso 7)
    if _regla_junta_culata(sintomas):
        reglas_disparadas.append(_R_JUNTA_CULATA)
        return {
            "diagnostico": "Fuga de refrigerante al motor - junta de culata",
            "urgencia": URGENCIA_CRITICA,
            "seguro_manejar": SEGURO_NO,
            "accion": (
                "Apagar el motor. No conducir. "
                "Remolcar al taller para inspección de culata."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_MOTOR,
        }

    # Regla 3: quema de aceite (caso 6)
    if _regla_quema_aceite(sintomas):
        reglas_disparadas.append(_R_QUEMA_ACEITE)
        return {
            "diagnostico": "Quema de aceite por anillos o guias",
            "urgencia": URGENCIA_MODERADA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller próximamente. Monitorear nivel de aceite "
                "frecuentemente. Evitar viajes largos."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_MOTOR,
        }

    # Regla 4: mezcla rica / inyectores (caso 8)
    if _regla_mezcla_rica(sintomas):
        reglas_disparadas.append(_R_MEZCLA_RICA)
        return {
            "diagnostico": "Mezcla rica o inyectores sucios",
            "urgencia": URGENCIA_MODERADA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller para diagnóstico electrónico. "
                "Limpiar o reemplazar inyectores y revisar sensores MAP/O2."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_MOTOR,
        }

    # Regla 5: detonación / knocking (caso 9)
    if _regla_detonacion(sintomas):
        reglas_disparadas.append(_R_DETONACION)
        return {
            "diagnostico": "Detonacion o problema en la combustion",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Usar combustible de mayor octanaje. "
                "Llevar al taller para revisar bujías, advance y sensor de knock."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_MOTOR,
        }

    # Regla 6: luz de aceite sin golpeteo (caso 29)
    if _regla_luz_aceite_sola(sintomas):
        reglas_disparadas.append(_R_LUZ_ACEITE_SOLA)
        return {
            "diagnostico": "Presion de aceite baja - nivel o bomba",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Verificar nivel de aceite. Si está correcto, revisar bomba "
                "y filtro de aceite. No ignorar la luz."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_MOTOR,
        }

    return None
