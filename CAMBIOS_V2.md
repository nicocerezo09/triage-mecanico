# Cambios versión 2 — Triage Mecánico

## Motor de inferencia (`src/motor.py`)

### Librería `experta`
- Se reemplazó el motor de módulos en cadena por un `KnowledgeEngine` de la librería `experta` (forward chaining declarativo).
- Las 30 reglas de diagnóstico se definen con el decorador `@Rule` y un parámetro `salience` que controla la prioridad de disparo.
- Se agregó un parche de compatibilidad para Python 3.10+ (`collections.Mapping` → `collections.abc.Mapping`) que permite usar `experta 1.9.4` con Python 3.13.
- El motor legacy (módulos `src/reglas/*.py`) queda como fallback si `experta` no está disponible.

### Matching fuzzy al 70 %
- Si ninguna regla matchea exacto, se calcula un puntaje de confianza para cada regla: `condiciones_cumplidas / total_condiciones * 100`.
- Toda regla que supere el umbral del 70 % es candidata al diagnóstico.
- En caso de empate, gana la de mayor urgencia; luego la de mayor confianza.
- Esto permite diagnosticar combinaciones de síntomas parciales que antes retornaban "Sin fallas detectadas".

### Corrección de bugs de prioridad
- **Bug "chirrido domina todo"**: `frenos.pastillas_desgastadas` (salience 80) ahora pierde ante reglas de motor y refrigeración con mayor salience (81–99). Por ejemplo, `motor.quema_aceite` (salience 81) gana cuando hay humo azul + pérdida de potencia + aceite en piso, aunque también haya chirrido al frenar.
- **Bug "humo solo → sin fallas"**: Se agregaron dos nuevas reglas:
  - `motor.humo_azul_solo` (salience 60, urgencia moderada): "Posible consumo de aceite — revisar nivel"
  - `motor.humo_negro_solo` (salience 58, urgencia moderada): "Posible mezcla rica o inyectores sucios"
- **Bug "pinza_trabada vs desalineación"**: La regla `frenos.pinza_trabada` ahora requiere `vibracion=True` además de `comportamiento_freno=se_va_hacia_un_lado`, diferenciándola del caso de desalineación/neumático desinflado.
- **Bug "sensor_gestion vs tirones_embrague"**: Se subió la salience de `electrico.sensor_gestion` de 55 a 65 para que gane ante `transmision.tirones_embrague` cuando hay `luces=check_engine + perdida_potencia`.

### Nuevas constantes (`src/constantes.py`)
Se agregaron valores para los nuevos campos de la UI:
- `CUANDO_OTRO = "otro"`
- `LIQUIDO_AGUA = "agua"`
- `LIQUIDO_OTRO = "otro"`
- `VIBRACION_OTRO = "otro"`
- `LUZ_OTRO = "otro"`

---

## Interfaz (`app.py`)

### Ortografía y tildes
Se corrigieron todas las tildes faltantes en la interfaz:

| Antes | Después |
|---|---|
| Triage Mecanico | Triage Mecánico |
| diagnostico de fallas en vehiculos | diagnóstico de fallas en vehículos |
| Recalentamiento critico | Recalentamiento crítico |
| Cuando ocurre el ruido | Cuándo ocurre el ruido |
| Senales visuales | Señales visuales |
| Perdida de potencia | Pérdida de potencia |
| Liquido en el piso | Líquido en el piso |
| Vibracion | Vibración |
| Donde se siente la vibracion | Dónde se siente la vibración |
| Diagnostico del Vehiculo | Diagnóstico del Vehículo |
| Resultado del diagnostico | Resultado del diagnóstico |
| Bateria | Batería |
| Tarda mas | Tarda más |
| Si, puede manejar | Sí, puede manejar |
| Con precaucion | Con precaución |
| CRITICA | CRÍTICA |

### Flujo de preguntas en árbol
- **Antes**: todos los campos siempre visibles en el sidebar.
- **Ahora**: el usuario primero elige qué categorías de síntomas detecta (checkboxes: Ruidos / Humo-Temperatura / Señales visuales / Vibración / Frenos). Las preguntas de cada categoría solo aparecen si esa categoría está marcada. Si una categoría no está activa, sus campos se fuerzan a valores neutros, evitando diagnósticos contaminados por valores residuales.

### Nuevas opciones en dropdowns
- **Cuándo ocurre el ruido**: "Ninguno" renombrado a "Otro / No especificado" (al usarse solo cuando ya hay un ruido seleccionado, "ninguno" no tenía sentido).
- **Luz de advertencia**: agregada opción "Otra luz".
- **Líquido en el piso**: agregadas opciones "Agua" y "Otro líquido".
- **Dónde se siente la vibración**: agregada opción "Otro lugar".

### Eliminación del checkbox "Hay vibración"
- Era redundante con el dropdown "Dónde se siente la vibración".
- El campo booleano `vibracion` ahora se calcula internamente: `True` si `donde_vibracion != "ninguna"`.

### Panel de resultados compacto
- El gauge se redujo de 280 a 200 px de alto.
- Las 4 cards de resultado (Sistema / Diagnóstico / Seguro para manejar / Acción) se muestran en una sola fila de 4 columnas, eliminando la necesidad de scroll.

### Tabla de reglas disparadas
- Se eliminó la columna "N°" que siempre mostraba "1".
- El subheader cambió de "Trazabilidad — Reglas disparadas" a "Reglas que se dispararon".

---

## Dependencias (`requirements.txt`)

- Se agregó `experta>=1.9.4`.

---

## Casos de prueba (`data/casos_prueba.csv`)

- **Caso 3**: se agregó `vibracion=si, donde_vibracion=pedal_de_freno` para que el síntoma de pinza trabada sea distinguible del de desalineación.
- **Caso 28**: se corrigió el diagnóstico esperado de "Alternador no carga..." a "Bateria debil o alternador fallando" (los casos 26 y 28 tenían síntomas idénticos con diagnósticos distintos, lo cual es indeterminable por cualquier motor determinista).

**Resultado final: 30/30 casos pasan.**
