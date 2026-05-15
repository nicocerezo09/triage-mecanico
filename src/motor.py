"""
Motor de inferencia principal del sistema experto de triage mecánico.

Encadena los 6 módulos de reglas en orden de prioridad y retorna
el primer diagnóstico que aplique, o el diagnóstico de sistema normal.
"""

from src.constantes import (
    URGENCIA_BAJA, SEGURO_SI,
    DIAGNOSTICO_SIN_FALLAS, SISTEMA_NINGUNO,
)
from src.reglas import (
    frenos,
    motor_combustion,
    refrigeracion,
    transmision,
    suspension,
    electrico,
)

# Orden de prioridad: sistemas de mayor riesgo de vida primero.
_MODULOS = [
    frenos,
    motor_combustion,
    refrigeracion,
    transmision,
    suspension,
    electrico,
]

_DIAGNOSTICO_NORMAL = {
    "diagnostico": DIAGNOSTICO_SIN_FALLAS,
    "urgencia": URGENCIA_BAJA,
    "seguro_manejar": SEGURO_SI,
    "accion": "El vehículo está en condiciones normales. Mantener los servicios regulares.",
    "reglas_disparadas": [],
    "sistema": SISTEMA_NINGUNO,
}


def diagnosticar(sintomas: dict) -> dict:
    """Corre todos los módulos de reglas en orden de prioridad y retorna el primer diagnóstico positivo.

    Aplica encadenamiento hacia adelante (forward chaining): evalúa cada módulo
    en secuencia y retorna en cuanto uno dispara (early-exit). El orden de los
    módulos en _MODULOS refleja riesgo de vida descendente: frenos > motor >
    refrigeracion > transmision > suspension > electrico.

    Args:
        sintomas: Dict con las siguientes claves (todas requeridas):
            ruido (str): tipo de ruido — "ninguno", "chirrido", "golpeteo",
                "zumbido", "crujido".
            cuando_ruido (str): momento del ruido — "ninguno", "al_frenar",
                "al_acelerar", "siempre", "en_neutro", "en_baches", "al_girar".
            humo (str): color del humo — "ninguno", "azul", "blanco", "negro".
            vibracion (bool): True si hay vibración perceptible.
            donde_vibracion (str): ubicación — "ninguna", "volante",
                "pedal_de_freno", "todo_el_auto".
            temperatura (str): lectura del tablero — "normal", "alta", "muy_alta".
            luces (str): luz de advertencia encendida — "ninguna", "temperatura",
                "aceite", "bateria", "check_engine".
            comportamiento_freno (str): respuesta del freno — "normal", "vibra",
                "tarda_mas", "se_va_hacia_un_lado".
            perdida_potencia (bool): True si hay perdida de potencia notoria.
            liquido_piso (str): líquido bajo el vehículo — "ninguno", "aceite",
                "refrigerante".

    Returns:
        Dict con las claves:
            diagnostico (str): descripción de la falla detectada.
            urgencia (str): "critica", "alta", "moderada" o "baja".
            seguro_manejar (str): "si", "con_precaucion" o "no".
            accion (str): recomendación inmediata para el conductor.
            reglas_disparadas (list[str]): identificadores de las reglas activadas.
            sistema (str): módulo de origen — "frenos", "motor", "refrigeracion",
                "transmision", "suspension", "electrico" o "ninguno".
    """
    for modulo in _MODULOS:
        resultado = modulo.diagnosticar(sintomas)
        if resultado is not None:
            return resultado
    return _DIAGNOSTICO_NORMAL
