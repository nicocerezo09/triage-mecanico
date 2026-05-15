"""
Constantes del sistema experto de triage mecánico.
Centraliza todos los strings de dominio para evitar hardcoding.
"""

# ---------------------------------------------------------------------------
# Niveles de urgencia
# ---------------------------------------------------------------------------
URGENCIA_CRITICA = "critica"
URGENCIA_ALTA = "alta"
URGENCIA_MODERADA = "moderada"
URGENCIA_BAJA = "baja"

# ---------------------------------------------------------------------------
# Seguridad para manejar
# ---------------------------------------------------------------------------
SEGURO_NO = "no"
SEGURO_CON_PRECAUCION = "con_precaucion"
SEGURO_SI = "si"

# ---------------------------------------------------------------------------
# Síntomas: ruidos
# ---------------------------------------------------------------------------
RUIDO_NINGUNO = "ninguno"
RUIDO_CHIRRIDO = "chirrido"
RUIDO_GOLPETEO = "golpeteo"
RUIDO_ZUMBIDO = "zumbido"
RUIDO_CRUJIDO = "crujido"

# ---------------------------------------------------------------------------
# Síntomas: cuándo ocurre el ruido
# ---------------------------------------------------------------------------
CUANDO_NINGUNO = "ninguno"
CUANDO_AL_FRENAR = "al_frenar"
CUANDO_AL_ACELERAR = "al_acelerar"
CUANDO_SIEMPRE = "siempre"
CUANDO_EN_NEUTRO = "en_neutro"
CUANDO_EN_BACHES = "en_baches"
CUANDO_AL_GIRAR = "al_girar"

# ---------------------------------------------------------------------------
# Síntomas: humo
# ---------------------------------------------------------------------------
HUMO_NINGUNO = "ninguno"
HUMO_AZUL = "azul"
HUMO_BLANCO = "blanco"
HUMO_NEGRO = "negro"

# ---------------------------------------------------------------------------
# Síntomas: dónde se siente la vibración
# ---------------------------------------------------------------------------
VIBRACION_NINGUNA = "ninguna"
VIBRACION_VOLANTE = "volante"
VIBRACION_PEDAL_FRENO = "pedal_de_freno"
VIBRACION_TODO_EL_AUTO = "todo_el_auto"

# ---------------------------------------------------------------------------
# Síntomas: temperatura
# ---------------------------------------------------------------------------
TEMP_NORMAL = "normal"
TEMP_ALTA = "alta"
TEMP_MUY_ALTA = "muy_alta"

# ---------------------------------------------------------------------------
# Síntomas: luces de advertencia
# ---------------------------------------------------------------------------
LUZ_NINGUNA = "ninguna"
LUZ_TEMPERATURA = "temperatura"
LUZ_ACEITE = "aceite"
LUZ_BATERIA = "bateria"
LUZ_CHECK_ENGINE = "check_engine"

# ---------------------------------------------------------------------------
# Síntomas: comportamiento del freno
# ---------------------------------------------------------------------------
FRENO_NORMAL = "normal"
FRENO_VIBRA = "vibra"
FRENO_TARDA_MAS = "tarda_mas"
FRENO_SE_VA_LADO = "se_va_hacia_un_lado"

# ---------------------------------------------------------------------------
# Síntomas: líquido en el piso
# ---------------------------------------------------------------------------
LIQUIDO_NINGUNO = "ninguno"
LIQUIDO_ACEITE = "aceite"
LIQUIDO_REFRIGERANTE = "refrigerante"

# ---------------------------------------------------------------------------
# Sistemas del vehículo (para identificar origen del diagnóstico)
# ---------------------------------------------------------------------------
SISTEMA_FRENOS = "frenos"
SISTEMA_MOTOR = "motor"
SISTEMA_REFRIGERACION = "refrigeracion"
SISTEMA_TRANSMISION = "transmision"
SISTEMA_SUSPENSION = "suspension"
SISTEMA_ELECTRICO = "electrico"
SISTEMA_NINGUNO = "ninguno"

# ---------------------------------------------------------------------------
# Diagnóstico de sistema normal (sin fallas)
# ---------------------------------------------------------------------------
DIAGNOSTICO_SIN_FALLAS = "Sin fallas detectadas - sistema normal"
