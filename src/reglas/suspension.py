"""
Reglas de diagnóstico para el sistema de suspensión y dirección.

Cubre: bujes/rótulas, desbalanceo de ruedas, falla grave de suspensión,
desalineación/neumático, rótula de dirección/junta homocinética.
Casos de prueba cubiertos: 21, 22, 23, 24, 25.

Nota: el caso 24 (se_va_hacia_un_lado) tiene síntomas idénticos al caso 3
(frenos). Dado que frenos tiene prioridad en el motor principal, el caso 3
es capturado por frenos y el caso 24 representa una inconsistencia conocida
del dataset de prueba.
"""

from src.constantes import (
    URGENCIA_ALTA, URGENCIA_MODERADA, URGENCIA_BAJA,
    SEGURO_NO, SEGURO_CON_PRECAUCION, SEGURO_SI,
    RUIDO_CRUJIDO,
    CUANDO_EN_BACHES, CUANDO_AL_GIRAR,
    VIBRACION_VOLANTE, VIBRACION_TODO_EL_AUTO,
    FRENO_SE_VA_LADO,
    SISTEMA_SUSPENSION,
)

# ---------------------------------------------------------------------------
# Identificadores de reglas
# ---------------------------------------------------------------------------
_R_ROTULA_HOMOCINETICA = "suspension.rotula_junta_homocinetica"
_R_FALLA_GRAVE = "suspension.falla_grave_suspension"
_R_DESALINEACION = "suspension.desalineacion_neumatico"
_R_BUJES_ROTULAS = "suspension.bujes_rotulas_desgastadas"
_R_DESBALANCEO = "suspension.desbalanceo_amortiguadores"


def _regla_rotula_homocinetica(s: dict) -> bool:
    """
    Condición: crujido al girar + vibración en volante.
    Combinación más específica: crujido direccional con feedback en volante.
    Evaluada primero para distinguirse de bujes simples.
    """
    return (
        s.get("ruido") == RUIDO_CRUJIDO
        and s.get("cuando_ruido") == CUANDO_AL_GIRAR
        and s.get("vibracion") is True
        and s.get("donde_vibracion") == VIBRACION_VOLANTE
    )


def _regla_falla_grave(s: dict) -> bool:
    """
    Condición: vibración en todo el auto (no solo volante).
    Vibración estructural generalizada indica falla de suspensión severa.
    """
    return (
        s.get("vibracion") is True
        and s.get("donde_vibracion") == VIBRACION_TODO_EL_AUTO
    )


def _regla_desalineacion(s: dict) -> bool:
    """
    Condición: freno se va hacia un lado.
    Sin otros síntomas de frenos activos, el desvío apunta a desalineación
    o neumático desinflado. En la práctica, el módulo de frenos captura
    este síntoma primero (prioridad del motor); esta regla es fallback
    para cuando el contexto es claramente de suspensión/dirección.
    """
    return s.get("comportamiento_freno") == FRENO_SE_VA_LADO


def _regla_bujes_rotulas(s: dict) -> bool:
    """
    Condición: crujido en baches, sin la combinación de rotula_homocinetica.
    Crujido al pasar irregularidades sin vibración en volante indica bujes
    o rótulas desgastadas.
    """
    return (
        s.get("ruido") == RUIDO_CRUJIDO
        and s.get("cuando_ruido") == CUANDO_EN_BACHES
        and not _regla_rotula_homocinetica(s)
    )


def _regla_desbalanceo(s: dict) -> bool:
    """
    Condición: vibración en volante, sin crujido al girar.
    Vibración aislada en volante sin ruido indica ruedas desbalanceadas
    o amortiguadores en mal estado.
    """
    return (
        s.get("vibracion") is True
        and s.get("donde_vibracion") == VIBRACION_VOLANTE
        and not _regla_rotula_homocinetica(s)
    )


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def diagnosticar(sintomas: dict) -> dict | None:
    """Evalúa los síntomas contra las reglas del sistema de suspensión y dirección.

    Orden de evaluación (mayor a menor gravedad):
      1. rotula_homocinetica  → alta (combinación crítica)
      2. falla_grave          → alta
      3. desalineacion        → moderada
      4. bujes_rotulas        → moderada
      5. desbalanceo          → baja

    Args:
        sintomas: Dict con claves ruido, cuando_ruido, humo, vibracion,
            donde_vibracion, temperatura, luces, comportamiento_freno,
            perdida_potencia, liquido_piso.

    Returns:
        Dict con diagnostico, urgencia, seguro_manejar, accion,
        reglas_disparadas y sistema. None si ninguna regla aplica.
    """
    reglas_disparadas = []

    # Regla 1: rótula de dirección o junta homocinética (caso 25)
    if _regla_rotula_homocinetica(sintomas):
        reglas_disparadas.append(_R_ROTULA_HOMOCINETICA)
        return {
            "diagnostico": "Rotula de direccion o junta homocinetica",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller con urgencia. "
                "Inspeccionar rótulas de dirección y juntas homocinéticas."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_SUSPENSION,
        }

    # Regla 2: falla grave de suspensión (caso 23)
    if _regla_falla_grave(sintomas):
        reglas_disparadas.append(_R_FALLA_GRAVE)
        return {
            "diagnostico": "Falla grave en suspension",
            "urgencia": URGENCIA_ALTA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Llevar al taller con urgencia. "
                "Revisar amortiguadores, resortes y brazos de suspensión."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_SUSPENSION,
        }

    # Regla 3: desalineación o neumático desinflado (caso 24)
    if _regla_desalineacion(sintomas):
        reglas_disparadas.append(_R_DESALINEACION)
        return {
            "diagnostico": "Desalineacion o neumatico desinflado",
            "urgencia": URGENCIA_MODERADA,
            "seguro_manejar": SEGURO_CON_PRECAUCION,
            "accion": (
                "Verificar presión de neumáticos. "
                "Llevar al taller para alineación y balanceo."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_SUSPENSION,
        }

    # Regla 4: bujes o rótulas desgastadas (caso 21)
    if _regla_bujes_rotulas(sintomas):
        reglas_disparadas.append(_R_BUJES_ROTULAS)
        return {
            "diagnostico": "Bujes o rotulas desgastadas",
            "urgencia": URGENCIA_MODERADA,
            "seguro_manejar": SEGURO_SI,
            "accion": (
                "Programar revisión en el taller. "
                "Reemplazar bujes y rótulas desgastadas."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_SUSPENSION,
        }

    # Regla 5: ruedas desbalanceadas o amortiguadores (caso 22)
    if _regla_desbalanceo(sintomas):
        reglas_disparadas.append(_R_DESBALANCEO)
        return {
            "diagnostico": "Ruedas desbalanceadas o amortiguadores",
            "urgencia": URGENCIA_BAJA,
            "seguro_manejar": SEGURO_SI,
            "accion": (
                "Llevar al taller para balanceo de ruedas. "
                "Revisar amortiguadores en el próximo servicio."
            ),
            "reglas_disparadas": reglas_disparadas,
            "sistema": SISTEMA_SUSPENSION,
        }

    return None
