"""
Motor de inferencia principal del sistema experto de triage mecanico.

Arquitectura: experta (PyKE-style forward-chaining) con salience por
especificidad de regla. Si experta no esta disponible, cae al motor
legacy basado en modulos.

Fuzzy scoring: si el engine no produce ningun Diagnostico, se aplica
scoring sobre DEFINICION_REGLAS. Toda regla que alcance >= 70% de sus
condiciones satisfechas es candidata; gana la de mayor urgencia y, en
empate, la de mayor confianza.
"""

# ---------------------------------------------------------------------------
# Importaciones del dominio (siempre disponibles)
# ---------------------------------------------------------------------------
from src.constantes import (
    # urgencias
    URGENCIA_CRITICA, URGENCIA_ALTA, URGENCIA_MODERADA, URGENCIA_BAJA,
    # seguro manejar
    SEGURO_NO, SEGURO_CON_PRECAUCION, SEGURO_SI,
    # ruidos
    RUIDO_CHIRRIDO, RUIDO_GOLPETEO, RUIDO_ZUMBIDO, RUIDO_CRUJIDO,
    # cuando ruido
    CUANDO_AL_FRENAR, CUANDO_AL_ACELERAR, CUANDO_SIEMPRE,
    CUANDO_EN_NEUTRO, CUANDO_EN_BACHES, CUANDO_AL_GIRAR,
    # humo
    HUMO_AZUL, HUMO_BLANCO, HUMO_NEGRO,
    # vibracion
    VIBRACION_VOLANTE, VIBRACION_PEDAL_FRENO, VIBRACION_TODO_EL_AUTO,
    # temperatura
    TEMP_NORMAL, TEMP_ALTA, TEMP_MUY_ALTA,
    # luces
    LUZ_TEMPERATURA, LUZ_ACEITE, LUZ_BATERIA, LUZ_CHECK_ENGINE,
    # comportamiento freno
    FRENO_VIBRA, FRENO_TARDA_MAS, FRENO_SE_VA_LADO,
    # liquido piso
    LIQUIDO_ACEITE, LIQUIDO_REFRIGERANTE,
    # sistemas
    SISTEMA_FRENOS, SISTEMA_MOTOR, SISTEMA_REFRIGERACION,
    SISTEMA_TRANSMISION, SISTEMA_SUSPENSION, SISTEMA_ELECTRICO,
    SISTEMA_NINGUNO,
    # diagnostico normal
    DIAGNOSTICO_SIN_FALLAS,
)

# ---------------------------------------------------------------------------
# Parche de compatibilidad: collections.Mapping fue movido a collections.abc
# en Python 3.10+. frozendict 1.2 (dependencia de experta) lo necesita en el
# namespace raiz, por lo que lo restauramos antes de importar experta.
# ---------------------------------------------------------------------------
import collections
import collections.abc
if not hasattr(collections, "Mapping"):
    collections.Mapping = collections.abc.Mapping
    collections.MutableMapping = collections.abc.MutableMapping
    collections.Callable = collections.abc.Callable

# ---------------------------------------------------------------------------
# Intento de importacion de experta
# ---------------------------------------------------------------------------
try:
    from experta import (
        Fact, Field, KnowledgeEngine, Rule, NOT, AS, MATCH, TEST, W, L,
    )
    _EXPERTA_DISPONIBLE = True
except (ImportError, Exception):
    _EXPERTA_DISPONIBLE = False

# ---------------------------------------------------------------------------
# Pesos de urgencia para desempate en fuzzy
# ---------------------------------------------------------------------------
_PESO_URGENCIA = {
    URGENCIA_CRITICA: 4,
    URGENCIA_ALTA: 3,
    URGENCIA_MODERADA: 2,
    URGENCIA_BAJA: 1,
}

# ---------------------------------------------------------------------------
# Catalogo de resultados de diagnostico por nombre de regla
# ---------------------------------------------------------------------------
_RESULTADOS: dict[str, dict] = {
    # --- FRENOS ---
    "frenos.pastillas_y_discos": {
        "diagnostico": "Pastillas y discos en mal estado",
        "urgencia": URGENCIA_CRITICA,
        "seguro_manejar": SEGURO_NO,
        "accion": (
            "Detener el vehiculo de forma segura. "
            "No conducir. Reemplazar pastillas y discos de inmediato."
        ),
        "sistema": SISTEMA_FRENOS,
    },
    "frenos.pinza_trabada": {
        "diagnostico": "Pinza de freno trabada",
        "urgencia": URGENCIA_CRITICA,
        "seguro_manejar": SEGURO_NO,
        "accion": (
            "No conducir. Remolcar al taller. "
            "Inspeccionar y reemplazar la pinza afectada."
        ),
        "sistema": SISTEMA_FRENOS,
    },
    "frenos.pastillas_desgastadas": {
        "diagnostico": "Pastillas de freno desgastadas",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller esta semana. "
            "Evitar frenadas bruscas hasta el reemplazo."
        ),
        "sistema": SISTEMA_FRENOS,
    },
    "frenos.discos_deformados": {
        "diagnostico": "Discos de freno deformados",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller pronto. "
            "Rectificar o reemplazar discos de freno."
        ),
        "sistema": SISTEMA_FRENOS,
    },
    "frenos.liquido_bajo": {
        "diagnostico": "Liquido de frenos bajo o contaminado",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Verificar y reponer nivel de liquido de frenos. "
            "Si persiste, revisar fugas y purgar el sistema."
        ),
        "sistema": SISTEMA_FRENOS,
    },
    # --- MOTOR ---
    "motor.presion_aceite_cojinetes": {
        "diagnostico": "Presion de aceite baja o cojinetes desgastados",
        "urgencia": URGENCIA_CRITICA,
        "seguro_manejar": SEGURO_NO,
        "accion": (
            "Apagar el motor de inmediato. No arrancar. "
            "Remolcar al taller. Riesgo de destruccion del motor."
        ),
        "sistema": SISTEMA_MOTOR,
    },
    "motor.junta_culata": {
        "diagnostico": "Fuga de refrigerante al motor - junta de culata",
        "urgencia": URGENCIA_CRITICA,
        "seguro_manejar": SEGURO_NO,
        "accion": (
            "Apagar el motor. No conducir. "
            "Remolcar al taller para inspeccion de culata."
        ),
        "sistema": SISTEMA_MOTOR,
    },
    "motor.quema_aceite": {
        "diagnostico": "Quema de aceite por anillos o guias",
        "urgencia": URGENCIA_MODERADA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller proximamente. Monitorear nivel de aceite "
            "frecuentemente. Evitar viajes largos."
        ),
        "sistema": SISTEMA_MOTOR,
    },
    "motor.mezcla_rica": {
        "diagnostico": "Mezcla rica o inyectores sucios",
        "urgencia": URGENCIA_MODERADA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller para diagnostico electronico. "
            "Limpiar o reemplazar inyectores y revisar sensores MAP/O2."
        ),
        "sistema": SISTEMA_MOTOR,
    },
    "motor.detonacion": {
        "diagnostico": "Detonacion o problema en la combustion",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Usar combustible de mayor octanaje. "
            "Llevar al taller para revisar bujias, advance y sensor de knock."
        ),
        "sistema": SISTEMA_MOTOR,
    },
    "motor.luz_aceite_sola": {
        "diagnostico": "Presion de aceite baja - nivel o bomba",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Verificar nivel de aceite. Si esta correcto, revisar bomba "
            "y filtro de aceite. No ignorar la luz."
        ),
        "sistema": SISTEMA_MOTOR,
    },
    "motor.humo_azul_solo": {
        "diagnostico": "Posible consumo de aceite - revisar nivel",
        "urgencia": URGENCIA_MODERADA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Verificar nivel de aceite. Si esta bajo, reponer y llevar al "
            "taller para inspeccion."
        ),
        "sistema": SISTEMA_MOTOR,
    },
    "motor.humo_negro_solo": {
        "diagnostico": "Posible mezcla rica o inyectores sucios",
        "urgencia": URGENCIA_MODERADA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller para diagnostico electronico. "
            "Revisar inyectores y sensor MAF."
        ),
        "sistema": SISTEMA_MOTOR,
    },
    # --- REFRIGERACION ---
    "refrigeracion.falla_multiple": {
        "diagnostico": "Falla multiple motor-refrigeracion",
        "urgencia": URGENCIA_CRITICA,
        "seguro_manejar": SEGURO_NO,
        "accion": (
            "Apagar el motor de inmediato. No conducir. "
            "Remolcar al taller. Posible dano grave en motor."
        ),
        "sistema": SISTEMA_REFRIGERACION,
    },
    "refrigeracion.recalentamiento_critico": {
        "diagnostico": "Recalentamiento critico del motor",
        "urgencia": URGENCIA_CRITICA,
        "seguro_manejar": SEGURO_NO,
        "accion": (
            "Apagar el motor inmediatamente. Dejar enfriar. "
            "No abrir la tapa del radiador en caliente. Remolcar al taller."
        ),
        "sistema": SISTEMA_REFRIGERACION,
    },
    "refrigeracion.fuga_con_recalentamiento": {
        "diagnostico": "Fuga en sistema de refrigeracion",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Reponer refrigerante y dirigirse al taller con precaucion. "
            "Monitorear temperatura constantemente."
        ),
        "sistema": SISTEMA_REFRIGERACION,
    },
    "refrigeracion.radiador_tapa": {
        "diagnostico": "Problema en radiador o tapa de expansion",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller con urgencia. "
            "Revisar tapa de expansion, radiador y mangueras."
        ),
        "sistema": SISTEMA_REFRIGERACION,
    },
    "refrigeracion.fuga_sin_recalentamiento": {
        "diagnostico": "Fuga de refrigerante sin recalentamiento",
        "urgencia": URGENCIA_MODERADA,
        "seguro_manejar": SEGURO_SI,
        "accion": (
            "Llevar al taller durante la semana. "
            "Verificar nivel de refrigerante antes de cada viaje."
        ),
        "sistema": SISTEMA_REFRIGERACION,
    },
    # --- TRANSMISION ---
    "transmision.diferencial_semiejes": {
        "diagnostico": "Falla en diferencial o semiejes",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller con urgencia. "
            "Inspeccionar diferencial, semiejes y juntas homocineticas."
        ),
        "sistema": SISTEMA_TRANSMISION,
    },
    "transmision.caja_interna": {
        "diagnostico": "Problema interno en caja de cambios",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller. "
            "Revisar sincronizadores y engranajes internos de la caja."
        ),
        "sistema": SISTEMA_TRANSMISION,
    },
    "transmision.tirones_embrague": {
        "diagnostico": "Tirones al cambiar - embrague o caja",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller. "
            "Inspeccionar embrague, cable de embrague y caja de cambios."
        ),
        "sistema": SISTEMA_TRANSMISION,
    },
    "transmision.cojinete": {
        "diagnostico": "Cojinete de transmision desgastado",
        "urgencia": URGENCIA_MODERADA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Programar revision en el taller. "
            "Reemplazar cojinete antes de que falle completamente."
        ),
        "sistema": SISTEMA_TRANSMISION,
    },
    "transmision.fuga_aceite": {
        "diagnostico": "Fuga de aceite de transmision",
        "urgencia": URGENCIA_MODERADA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Verificar nivel de aceite de transmision. "
            "Llevar al taller para identificar y sellar la fuga."
        ),
        "sistema": SISTEMA_TRANSMISION,
    },
    # --- SUSPENSION ---
    "suspension.rotula_homocinetica": {
        "diagnostico": "Rotula de direccion o junta homocinetica",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller con urgencia. "
            "Inspeccionar rotulas de direccion y juntas homocineticas."
        ),
        "sistema": SISTEMA_SUSPENSION,
    },
    "suspension.falla_grave": {
        "diagnostico": "Falla grave en suspension",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller con urgencia. "
            "Revisar amortiguadores, resortes y brazos de suspension."
        ),
        "sistema": SISTEMA_SUSPENSION,
    },
    "suspension.desalineacion": {
        "diagnostico": "Desalineacion o neumatico desinflado",
        "urgencia": URGENCIA_MODERADA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Verificar presion de neumaticos. "
            "Llevar al taller para alineacion y balanceo."
        ),
        "sistema": SISTEMA_SUSPENSION,
    },
    "suspension.bujes_rotulas": {
        "diagnostico": "Bujes o rotulas desgastadas",
        "urgencia": URGENCIA_MODERADA,
        "seguro_manejar": SEGURO_SI,
        "accion": (
            "Programar revision en el taller. "
            "Reemplazar bujes y rotulas desgastadas."
        ),
        "sistema": SISTEMA_SUSPENSION,
    },
    "suspension.desbalanceo": {
        "diagnostico": "Ruedas desbalanceadas o amortiguadores",
        "urgencia": URGENCIA_BAJA,
        "seguro_manejar": SEGURO_SI,
        "accion": (
            "Llevar al taller para balanceo de ruedas. "
            "Revisar amortiguadores en el proximo servicio."
        ),
        "sistema": SISTEMA_SUSPENSION,
    },
    # --- ELECTRICO ---
    "electrico.bateria_alternador": {
        "diagnostico": "Bateria debil o alternador fallando",
        "urgencia": URGENCIA_ALTA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Llevar al taller. "
            "Testear bateria y alternador. Revisar correa de transmision."
        ),
        "sistema": SISTEMA_ELECTRICO,
    },
    "electrico.sensor_gestion": {
        "diagnostico": "Falla en sensor o sistema de gestion",
        "urgencia": URGENCIA_MODERADA,
        "seguro_manejar": SEGURO_CON_PRECAUCION,
        "accion": (
            "Leer codigos de error con scanner OBD. "
            "Revisar sensores MAP, MAF, O2 y ECU."
        ),
        "sistema": SISTEMA_ELECTRICO,
    },
}

# ---------------------------------------------------------------------------
# Definicion de condiciones por regla (usado por el fuzzy scoring).
# Cada condicion es una tupla (campo, valor_esperado) o (campo, True/False)
# para booleans. El porcentaje de match se calcula sobre el total de
# condiciones definidas para la regla.
# ---------------------------------------------------------------------------
_DEFINICION_REGLAS: dict[str, list[tuple]] = {
    # FRENOS
    "frenos.pastillas_y_discos": [
        ("ruido", RUIDO_CHIRRIDO),
        ("cuando_ruido", CUANDO_AL_FRENAR),
        ("vibracion", True),
        ("donde_vibracion", VIBRACION_PEDAL_FRENO),
        ("comportamiento_freno", FRENO_VIBRA),
    ],
    "frenos.pinza_trabada": [
        ("comportamiento_freno", FRENO_SE_VA_LADO),
        ("vibracion", True),
    ],
    "frenos.pastillas_desgastadas": [
        ("ruido", RUIDO_CHIRRIDO),
        ("cuando_ruido", CUANDO_AL_FRENAR),
    ],
    "frenos.discos_deformados": [
        ("vibracion", True),
        ("donde_vibracion", VIBRACION_PEDAL_FRENO),
        ("comportamiento_freno", FRENO_VIBRA),
    ],
    "frenos.liquido_bajo": [
        ("comportamiento_freno", FRENO_TARDA_MAS),
    ],
    # MOTOR
    "motor.presion_aceite_cojinetes": [
        ("ruido", RUIDO_GOLPETEO),
        ("cuando_ruido", CUANDO_SIEMPRE),
        ("luces", LUZ_ACEITE),
        ("perdida_potencia", True),
        ("liquido_piso", LIQUIDO_ACEITE),
    ],
    "motor.junta_culata": [
        ("humo", HUMO_BLANCO),
        ("temperatura", TEMP_MUY_ALTA),
        ("luces", LUZ_TEMPERATURA),
        ("liquido_piso", LIQUIDO_REFRIGERANTE),
    ],
    "motor.quema_aceite": [
        ("humo", HUMO_AZUL),
        ("luces", LUZ_ACEITE),
        ("perdida_potencia", True),
        ("liquido_piso", LIQUIDO_ACEITE),
    ],
    "motor.mezcla_rica": [
        ("humo", HUMO_NEGRO),
        ("luces", LUZ_CHECK_ENGINE),
        ("perdida_potencia", True),
    ],
    "motor.detonacion": [
        ("ruido", RUIDO_GOLPETEO),
        ("cuando_ruido", CUANDO_AL_ACELERAR),
    ],
    "motor.luz_aceite_sola": [
        ("luces", LUZ_ACEITE),
        ("liquido_piso", LIQUIDO_ACEITE),
    ],
    "motor.humo_azul_solo": [
        ("humo", HUMO_AZUL),
    ],
    "motor.humo_negro_solo": [
        ("humo", HUMO_NEGRO),
    ],
    # REFRIGERACION
    "refrigeracion.falla_multiple": [
        ("temperatura", TEMP_MUY_ALTA),
        ("luces", LUZ_TEMPERATURA),
        ("perdida_potencia", True),
        ("liquido_piso", LIQUIDO_REFRIGERANTE),
    ],
    "refrigeracion.recalentamiento_critico": [
        ("temperatura", TEMP_MUY_ALTA),
        ("luces", LUZ_TEMPERATURA),
    ],
    "refrigeracion.fuga_con_recalentamiento": [
        ("temperatura", TEMP_ALTA),
        ("luces", LUZ_TEMPERATURA),
        ("liquido_piso", LIQUIDO_REFRIGERANTE),
    ],
    "refrigeracion.radiador_tapa": [
        ("humo", HUMO_BLANCO),
        ("temperatura", TEMP_ALTA),
    ],
    "refrigeracion.fuga_sin_recalentamiento": [
        ("liquido_piso", LIQUIDO_REFRIGERANTE),
        ("temperatura", TEMP_NORMAL),
    ],
    # TRANSMISION
    "transmision.diferencial_semiejes": [
        ("ruido", RUIDO_ZUMBIDO),
        ("cuando_ruido", CUANDO_SIEMPRE),
        ("perdida_potencia", True),
    ],
    "transmision.caja_interna": [
        ("ruido", RUIDO_GOLPETEO),
        ("cuando_ruido", CUANDO_EN_NEUTRO),
    ],
    "transmision.tirones_embrague": [
        ("perdida_potencia", True),
    ],
    "transmision.cojinete": [
        ("ruido", RUIDO_ZUMBIDO),
        ("cuando_ruido", CUANDO_AL_ACELERAR),
    ],
    "transmision.fuga_aceite": [
        ("liquido_piso", LIQUIDO_ACEITE),
    ],
    # SUSPENSION
    "suspension.rotula_homocinetica": [
        ("ruido", RUIDO_CRUJIDO),
        ("cuando_ruido", CUANDO_AL_GIRAR),
        ("donde_vibracion", VIBRACION_VOLANTE),
    ],
    "suspension.falla_grave": [
        ("donde_vibracion", VIBRACION_TODO_EL_AUTO),
    ],
    "suspension.desalineacion": [
        ("comportamiento_freno", FRENO_SE_VA_LADO),
    ],
    "suspension.bujes_rotulas": [
        ("ruido", RUIDO_CRUJIDO),
        ("cuando_ruido", CUANDO_EN_BACHES),
    ],
    "suspension.desbalanceo": [
        ("donde_vibracion", VIBRACION_VOLANTE),
    ],
    # ELECTRICO
    "electrico.bateria_alternador": [
        ("luces", LUZ_BATERIA),
    ],
    "electrico.sensor_gestion": [
        ("luces", LUZ_CHECK_ENGINE),
        ("perdida_potencia", True),
    ],
}

# ---------------------------------------------------------------------------
# Diagnostico de sistema normal (fallback final)
# ---------------------------------------------------------------------------
_DIAGNOSTICO_NORMAL: dict = {
    "diagnostico": DIAGNOSTICO_SIN_FALLAS,
    "urgencia": URGENCIA_BAJA,
    "seguro_manejar": SEGURO_SI,
    "accion": "El vehiculo esta en condiciones normales. Mantener los servicios regulares.",
    "reglas_disparadas": [],
    "sistema": SISTEMA_NINGUNO,
}


# ===========================================================================
# ENGINE CON EXPERTA
# ===========================================================================

def _construir_resultado(nombre_regla: str, reglas_disparadas: list[str]) -> dict:
    """Ensambla el dict de retorno combinando catalogo y lista de reglas.

    Args:
        nombre_regla: Clave en _RESULTADOS que identifica la regla ganadora.
        reglas_disparadas: Lista de nombres de reglas activadas durante la sesion.

    Returns:
        Dict completo con diagnostico, urgencia, seguro_manejar, accion,
        reglas_disparadas y sistema.
    """
    base = _RESULTADOS[nombre_regla]
    return {
        "diagnostico": base["diagnostico"],
        "urgencia": base["urgencia"],
        "seguro_manejar": base["seguro_manejar"],
        "accion": base["accion"],
        "reglas_disparadas": reglas_disparadas,
        "sistema": base["sistema"],
    }


if _EXPERTA_DISPONIBLE:

    class _Sintoma(Fact):
        """Hecho que representa los sintomas del vehiculo en la sesion."""
        pass

    class _Diagnostico(Fact):
        """Hecho que representa el resultado de un diagnostico activado."""
        nombre = Field(str, mandatory=True)

    class TriageEngine(KnowledgeEngine):
        """Motor de inferencia de triage mecanico basado en experta.

        Cada metodo decorado con @Rule codifica una regla de diagnostico.
        La salience determina el orden de disparo: mayor salience = mayor
        prioridad. El engine detiene la evaluacion en cuanto declara un
        _Diagnostico (agenda se vacia para esa regla).
        """

        # ----------------------------------------------------------------
        # FRENOS  (salience 80-100)
        # ----------------------------------------------------------------

        @Rule(
            _Sintoma(ruido=RUIDO_CHIRRIDO,
                     cuando_ruido=CUANDO_AL_FRENAR,
                     vibracion=True,
                     donde_vibracion=VIBRACION_PEDAL_FRENO,
                     comportamiento_freno=FRENO_VIBRA),
            NOT(_Diagnostico()),
            salience=100,
        )
        def frenos_pastillas_y_discos(self):
            """Chirrido al frenar + vibracion en pedal + freno vibra: pastillas y discos."""
            self.declare(_Diagnostico(nombre="frenos.pastillas_y_discos"))

        @Rule(
            _Sintoma(comportamiento_freno=FRENO_SE_VA_LADO,
                     vibracion=True),
            NOT(_Diagnostico()),
            salience=95,
        )
        def frenos_pinza_trabada(self):
            """Freno se va hacia un lado + vibracion: pinza trabada."""
            self.declare(_Diagnostico(nombre="frenos.pinza_trabada"))

        @Rule(
            _Sintoma(vibracion=True,
                     donde_vibracion=VIBRACION_PEDAL_FRENO,
                     comportamiento_freno=FRENO_VIBRA),
            NOT(_Diagnostico()),
            salience=85,
        )
        def frenos_discos_deformados(self):
            """Vibracion en pedal de freno + freno vibra: discos deformados."""
            self.declare(_Diagnostico(nombre="frenos.discos_deformados"))

        @Rule(
            _Sintoma(comportamiento_freno=FRENO_TARDA_MAS),
            NOT(_Diagnostico()),
            salience=82,
        )
        def frenos_liquido_bajo(self):
            """Freno tarda mas: liquido bajo o contaminado."""
            self.declare(_Diagnostico(nombre="frenos.liquido_bajo"))

        @Rule(
            _Sintoma(ruido=RUIDO_CHIRRIDO,
                     cuando_ruido=CUANDO_AL_FRENAR),
            NOT(_Diagnostico()),
            salience=80,
        )
        def frenos_pastillas_desgastadas(self):
            """Chirrido al frenar: pastillas desgastadas."""
            self.declare(_Diagnostico(nombre="frenos.pastillas_desgastadas"))

        # ----------------------------------------------------------------
        # MOTOR / COMBUSTION  (salience 58-99)
        # ----------------------------------------------------------------

        @Rule(
            _Sintoma(ruido=RUIDO_GOLPETEO,
                     cuando_ruido=CUANDO_SIEMPRE,
                     luces=LUZ_ACEITE,
                     perdida_potencia=True,
                     liquido_piso=LIQUIDO_ACEITE),
            NOT(_Diagnostico()),
            salience=99,
        )
        def motor_presion_aceite_cojinetes(self):
            """Golpeteo constante + luz aceite + perdida potencia + aceite en piso: cojinetes."""
            self.declare(_Diagnostico(nombre="motor.presion_aceite_cojinetes"))

        @Rule(
            _Sintoma(humo=HUMO_BLANCO,
                     temperatura=TEMP_MUY_ALTA,
                     luces=LUZ_TEMPERATURA,
                     liquido_piso=LIQUIDO_REFRIGERANTE),
            NOT(_Diagnostico()),
            salience=98,
        )
        def motor_junta_culata(self):
            """Humo blanco + temp muy alta + luz temp + refrigerante en piso: junta culata."""
            self.declare(_Diagnostico(nombre="motor.junta_culata"))

        @Rule(
            _Sintoma(ruido=RUIDO_GOLPETEO,
                     cuando_ruido=CUANDO_AL_ACELERAR),
            NOT(_Diagnostico()),
            salience=83,
        )
        def motor_detonacion(self):
            """Golpeteo al acelerar: detonacion / knocking."""
            self.declare(_Diagnostico(nombre="motor.detonacion"))

        @Rule(
            _Sintoma(luces=LUZ_ACEITE,
                     liquido_piso=LIQUIDO_ACEITE),
            NOT(_Diagnostico()),
            salience=79,
        )
        def motor_luz_aceite_sola(self):
            """Luz aceite + aceite en piso: presion baja, nivel o bomba."""
            self.declare(_Diagnostico(nombre="motor.luz_aceite_sola"))

        @Rule(
            _Sintoma(humo=HUMO_AZUL,
                     luces=LUZ_ACEITE,
                     perdida_potencia=True,
                     liquido_piso=LIQUIDO_ACEITE),
            NOT(_Diagnostico()),
            salience=81,
        )
        def motor_quema_aceite(self):
            """Humo azul + luz aceite + perdida potencia + aceite en piso: quema de aceite.

            salience=81 (> motor.luz_aceite_sola=79) porque tiene 4 condiciones
            especificas contra 2: regla mas especifica gana sobre la generica.
            """
            self.declare(_Diagnostico(nombre="motor.quema_aceite"))

        @Rule(
            _Sintoma(humo=HUMO_NEGRO,
                     luces=LUZ_CHECK_ENGINE,
                     perdida_potencia=True),
            NOT(_Diagnostico()),
            salience=76,
        )
        def motor_mezcla_rica(self):
            """Humo negro + check engine + perdida potencia: mezcla rica / inyectores."""
            self.declare(_Diagnostico(nombre="motor.mezcla_rica"))

        @Rule(
            _Sintoma(humo=HUMO_AZUL),
            NOT(_Diagnostico()),
            salience=60,
        )
        def motor_humo_azul_solo(self):
            """Humo azul sin otros sintomas fuertes: posible consumo de aceite."""
            self.declare(_Diagnostico(nombre="motor.humo_azul_solo"))

        @Rule(
            _Sintoma(humo=HUMO_NEGRO),
            NOT(_Diagnostico()),
            salience=58,
        )
        def motor_humo_negro_solo(self):
            """Humo negro sin otros sintomas fuertes: posible mezcla rica."""
            self.declare(_Diagnostico(nombre="motor.humo_negro_solo"))

        # ----------------------------------------------------------------
        # REFRIGERACION  (salience 70-97)
        # ----------------------------------------------------------------

        @Rule(
            _Sintoma(temperatura=TEMP_MUY_ALTA,
                     luces=LUZ_TEMPERATURA,
                     perdida_potencia=True,
                     liquido_piso=LIQUIDO_REFRIGERANTE),
            NOT(_Diagnostico()),
            salience=97,
        )
        def refrigeracion_falla_multiple(self):
            """Temp muy alta + luz temp + perdida potencia + refrigerante en piso: falla multiple."""
            self.declare(_Diagnostico(nombre="refrigeracion.falla_multiple"))

        @Rule(
            _Sintoma(temperatura=TEMP_MUY_ALTA,
                     luces=LUZ_TEMPERATURA),
            NOT(_Diagnostico()),
            salience=93,
        )
        def refrigeracion_recalentamiento_critico(self):
            """Temp muy alta + luz temperatura: recalentamiento critico."""
            self.declare(_Diagnostico(nombre="refrigeracion.recalentamiento_critico"))

        @Rule(
            _Sintoma(temperatura=TEMP_ALTA,
                     luces=LUZ_TEMPERATURA,
                     liquido_piso=LIQUIDO_REFRIGERANTE),
            NOT(_Diagnostico()),
            salience=84,
        )
        def refrigeracion_fuga_con_recalentamiento(self):
            """Temp alta + luz temp + refrigerante en piso: fuga con recalentamiento."""
            self.declare(_Diagnostico(nombre="refrigeracion.fuga_con_recalentamiento"))

        @Rule(
            _Sintoma(humo=HUMO_BLANCO,
                     temperatura=TEMP_ALTA),
            NOT(_Diagnostico()),
            salience=74,
        )
        def refrigeracion_radiador_tapa(self):
            """Humo blanco + temperatura alta: radiador o tapa de expansion."""
            self.declare(_Diagnostico(nombre="refrigeracion.radiador_tapa"))

        @Rule(
            _Sintoma(liquido_piso=LIQUIDO_REFRIGERANTE,
                     temperatura=TEMP_NORMAL),
            NOT(_Diagnostico()),
            salience=70,
        )
        def refrigeracion_fuga_sin_recalentamiento(self):
            """Refrigerante en piso + temperatura normal: fuga pasiva."""
            self.declare(_Diagnostico(nombre="refrigeracion.fuga_sin_recalentamiento"))

        # ----------------------------------------------------------------
        # TRANSMISION  (salience 55-75)
        # ----------------------------------------------------------------

        @Rule(
            _Sintoma(ruido=RUIDO_ZUMBIDO,
                     cuando_ruido=CUANDO_SIEMPRE,
                     perdida_potencia=True),
            NOT(_Diagnostico()),
            salience=75,
        )
        def transmision_diferencial_semiejes(self):
            """Zumbido constante + perdida potencia: diferencial o semiejes."""
            self.declare(_Diagnostico(nombre="transmision.diferencial_semiejes"))

        @Rule(
            _Sintoma(ruido=RUIDO_GOLPETEO,
                     cuando_ruido=CUANDO_EN_NEUTRO),
            NOT(_Diagnostico()),
            salience=73,
        )
        def transmision_caja_interna(self):
            """Golpeteo en neutro: problema interno en caja de cambios."""
            self.declare(_Diagnostico(nombre="transmision.caja_interna"))

        @Rule(
            _Sintoma(ruido=RUIDO_ZUMBIDO,
                     cuando_ruido=CUANDO_AL_ACELERAR),
            NOT(_Diagnostico()),
            salience=65,
        )
        def transmision_cojinete(self):
            """Zumbido al acelerar: cojinete de transmision."""
            self.declare(_Diagnostico(nombre="transmision.cojinete"))

        @Rule(
            _Sintoma(liquido_piso=LIQUIDO_ACEITE),
            NOT(_Diagnostico()),
            salience=57,
        )
        def transmision_fuga_aceite(self):
            """Aceite en piso: fuga de aceite de transmision."""
            self.declare(_Diagnostico(nombre="transmision.fuga_aceite"))

        @Rule(
            _Sintoma(perdida_potencia=True),
            NOT(_Diagnostico()),
            salience=55,
        )
        def transmision_tirones_embrague(self):
            """Perdida de potencia aislada: tirones en embrague o caja."""
            self.declare(_Diagnostico(nombre="transmision.tirones_embrague"))

        # ----------------------------------------------------------------
        # SUSPENSION  (salience 50-72)
        # ----------------------------------------------------------------

        @Rule(
            _Sintoma(ruido=RUIDO_CRUJIDO,
                     cuando_ruido=CUANDO_AL_GIRAR,
                     donde_vibracion=VIBRACION_VOLANTE),
            NOT(_Diagnostico()),
            salience=72,
        )
        def suspension_rotula_homocinetica(self):
            """Crujido al girar + vibracion en volante: rotula o junta homocinetica."""
            self.declare(_Diagnostico(nombre="suspension.rotula_homocinetica"))

        @Rule(
            _Sintoma(donde_vibracion=VIBRACION_TODO_EL_AUTO),
            NOT(_Diagnostico()),
            salience=68,
        )
        def suspension_falla_grave(self):
            """Vibracion en todo el auto: falla grave de suspension."""
            self.declare(_Diagnostico(nombre="suspension.falla_grave"))

        @Rule(
            _Sintoma(ruido=RUIDO_CRUJIDO,
                     cuando_ruido=CUANDO_EN_BACHES),
            NOT(_Diagnostico()),
            salience=62,
        )
        def suspension_bujes_rotulas(self):
            """Crujido en baches: bujes o rotulas desgastadas."""
            self.declare(_Diagnostico(nombre="suspension.bujes_rotulas"))

        @Rule(
            _Sintoma(donde_vibracion=VIBRACION_VOLANTE),
            NOT(_Diagnostico()),
            salience=52,
        )
        def suspension_desbalanceo(self):
            """Vibracion en volante sin crujido: desbalanceo o amortiguadores."""
            self.declare(_Diagnostico(nombre="suspension.desbalanceo"))

        @Rule(
            _Sintoma(comportamiento_freno=FRENO_SE_VA_LADO),
            NOT(_Diagnostico()),
            salience=50,
        )
        def suspension_desalineacion(self):
            """Freno se va hacia un lado (baja prioridad): desalineacion o neumatico."""
            self.declare(_Diagnostico(nombre="suspension.desalineacion"))

        # ----------------------------------------------------------------
        # ELECTRICO  (salience 45-60)
        # ----------------------------------------------------------------

        @Rule(
            _Sintoma(luces=LUZ_BATERIA),
            NOT(_Diagnostico()),
            salience=60,
        )
        def electrico_bateria_alternador(self):
            """Luz de bateria: bateria debil o alternador fallando."""
            self.declare(_Diagnostico(nombre="electrico.bateria_alternador"))

        @Rule(
            _Sintoma(luces=LUZ_CHECK_ENGINE,
                     perdida_potencia=True),
            NOT(_Diagnostico()),
            salience=65,
        )
        def electrico_sensor_gestion(self):
            """Check engine + perdida potencia: sensor o sistema de gestion."""
            self.declare(_Diagnostico(nombre="electrico.sensor_gestion"))


# ===========================================================================
# FUZZY SCORING (fallback cuando el engine no dispara ninguna regla)
# ===========================================================================

def _score_fuzzy(sintomas: dict) -> dict | None:
    """Aplica scoring difuso sobre todas las reglas definidas.

    Para cada regla calcula el porcentaje de condiciones satisfechas.
    Si alguna alcanza el umbral del 70%, la convierte en candidata.
    Ordena candidatas por urgencia descendente y luego por confianza
    descendente. Retorna el mejor candidato o None si ningun umbral se
    supera.

    Args:
        sintomas: Dict de sintomas del vehiculo.

    Returns:
        Dict de diagnostico completo o None si no hay candidatos >= 70%.
    """
    _UMBRAL = 0.70
    candidatos: list[tuple[int, float, str]] = []  # (peso_urgencia, confianza, nombre)

    for nombre, condiciones in _DEFINICION_REGLAS.items():
        if not condiciones:
            continue
        matcheadas = sum(
            1
            for campo, valor in condiciones
            if sintomas.get(campo) == valor
        )
        confianza = matcheadas / len(condiciones)
        if confianza >= _UMBRAL:
            urgencia = _RESULTADOS[nombre]["urgencia"]
            peso = _PESO_URGENCIA.get(urgencia, 0)
            candidatos.append((peso, confianza, nombre))

    if not candidatos:
        return None

    # Mayor urgencia primero; en empate, mayor confianza.
    candidatos.sort(key=lambda t: (t[0], t[1]), reverse=True)
    _peso, confianza, ganador = candidatos[0]

    resultado = _construir_resultado(ganador, [ganador])
    resultado["_fuzzy"] = True          # marca interna para trazabilidad
    resultado["_confianza"] = round(confianza * 100, 1)
    return resultado


# ===========================================================================
# MOTOR LEGADO (fallback si experta no esta disponible)
# ===========================================================================

def _diagnosticar_legado(sintomas: dict) -> dict:
    """Ejecuta el motor legacy de modulos en cadena como fallback.

    Importa los modulos de src/reglas/ en orden de prioridad y retorna
    el primer diagnostico que aplique.

    Args:
        sintomas: Dict de sintomas del vehiculo.

    Returns:
        Dict de diagnostico completo.
    """
    from src.reglas import (
        frenos,
        motor_combustion,
        refrigeracion,
        transmision,
        suspension,
        electrico,
    )
    for modulo in [frenos, motor_combustion, refrigeracion,
                   transmision, suspension, electrico]:
        resultado = modulo.diagnosticar(sintomas)
        if resultado is not None:
            return resultado
    return _DIAGNOSTICO_NORMAL.copy()


# ===========================================================================
# INTERFAZ PUBLICA
# ===========================================================================

def diagnosticar(sintomas: dict) -> dict:
    """Ejecuta el motor de triage mecanico sobre el conjunto de sintomas.

    Flujo de ejecucion:
      1. Si experta esta disponible, instancia TriageEngine, declara un
         _Sintoma con los datos del input y corre el engine.
      2. El engine dispara la regla de mayor salience cuyas condiciones
         se satisfagan; esa regla declara un _Diagnostico.
      3. Si el engine no produjo ningun _Diagnostico (ningun patron exacto),
         se aplica el scoring fuzzy sobre _DEFINICION_REGLAS con umbral 70%.
      4. Si tampoco hay candidato fuzzy, retorna el diagnostico normal.
      5. Si experta no esta instalado, cae al motor legado de modulos.

    Args:
        sintomas: Dict con las siguientes claves (todas requeridas):
            ruido (str): "ninguno" | "chirrido" | "golpeteo" | "zumbido"
                | "crujido".
            cuando_ruido (str): "ninguno" | "al_frenar" | "al_acelerar"
                | "siempre" | "en_neutro" | "en_baches" | "al_girar".
            humo (str): "ninguno" | "azul" | "blanco" | "negro".
            vibracion (bool): True si hay vibracion perceptible.
            donde_vibracion (str): "ninguna" | "volante" | "pedal_de_freno"
                | "todo_el_auto".
            temperatura (str): "normal" | "alta" | "muy_alta".
            luces (str): "ninguna" | "temperatura" | "aceite" | "bateria"
                | "check_engine".
            comportamiento_freno (str): "normal" | "vibra" | "tarda_mas"
                | "se_va_hacia_un_lado".
            perdida_potencia (bool): True si hay perdida de potencia notoria.
            liquido_piso (str): "ninguno" | "aceite" | "refrigerante".

    Returns:
        Dict con las claves:
            diagnostico (str): descripcion de la falla detectada.
            urgencia (str): "critica" | "alta" | "moderada" | "baja".
            seguro_manejar (str): "si" | "con_precaucion" | "no".
            accion (str): recomendacion inmediata para el conductor.
            reglas_disparadas (list[str]): nombres de reglas activadas.
            sistema (str): "frenos" | "motor" | "refrigeracion" |
                "transmision" | "suspension" | "electrico" | "ninguno".
    """
    if not _EXPERTA_DISPONIBLE:
        return _diagnosticar_legado(sintomas)

    # --- Normalizar booleans que pueden llegar como strings ---
    s = dict(sintomas)
    for campo in ("vibracion", "perdida_potencia"):
        if isinstance(s.get(campo), str):
            s[campo] = s[campo].lower() in ("true", "si", "1", "yes")

    # --- Ejecutar engine experta ---
    engine = TriageEngine()
    engine.reset()
    engine.declare(_Sintoma(**s))
    engine.run()

    # --- Recoger Diagnostico declarado ---
    diagnostico_fact = None
    reglas_disparadas: list[str] = []

    for fact in engine.facts.values():
        if isinstance(fact, _Diagnostico):
            nombre = fact["nombre"]
            reglas_disparadas.append(nombre)
            if diagnostico_fact is None:
                diagnostico_fact = nombre

    if diagnostico_fact is not None:
        return _construir_resultado(diagnostico_fact, reglas_disparadas)

    # --- Fallback fuzzy ---
    resultado_fuzzy = _score_fuzzy(s)
    if resultado_fuzzy is not None:
        return resultado_fuzzy

    return _DIAGNOSTICO_NORMAL.copy()
