# Guion de Presentación — Triage Mecánico: Sistema Experto de Diagnóstico Automotriz

**Materia**: Análisis de Datos II — Sistemas Expertos y Redes de Conocimiento  
**Duración total**: 12 minutos  
**Integrantes**: 6 (2 minutos por bloque)

---

## BLOQUE 1 — Introducción y Problema del Dominio
**(Integrante 1 — ~2 min)**

### Apertura
"Buenas tardes. Vamos a presentar Triage Mecánico, un sistema experto basado en reglas que diagnostica fallas mecánicas en vehículos a partir de síntomas observables."

### El problema
Cuando un auto presenta una falla, el conductor enfrenta incertidumbre: ¿es grave? ¿puedo seguir manejando? El diagnóstico mecánico requiere experiencia que la mayoría de las personas no tiene.

Aquí es donde entra la **IA Simbólica**: en lugar de un modelo de caja negra que aprende de datos, construimos un sistema que razona con **reglas explícitas**, igual que lo haría un mecánico experto.

### Por qué un Sistema Experto y no Machine Learning
Como vimos en clase (Feigenbaum, 1982): "un SE usa conocimiento y procedimientos de inferencia para resolver problemas que normalmente requieren la experiencia humana."

A diferencia del Deep Learning, nuestro sistema es:
- **Interpretable**: cada diagnóstico tiene una regla identificable
- **Explicable**: la tabla de trazabilidad muestra exactamente qué reglas se dispararon
- **Mantenible**: agregar nuevas fallas solo requiere escribir nuevas reglas

### Dominio elegido
6 sistemas del vehículo: frenos, motor, refrigeración, transmisión, suspensión, eléctrico.  
Síntomas de entrada: ruidos, humo, temperatura, vibraciones, luces del tablero, comportamiento del freno y líquido en el piso.

---

## BLOQUE 2 — Base de Conocimiento
**(Integrante 2 — ~2 min)**

### Estructura de la Base de Conocimiento (RBES)
Como vimos en la Clase 4, la base de conocimiento de un RBES se divide en:

**Base de Reglas**: el corazón del sistema. Tenemos **28 reglas** organizadas en 6 módulos. Ejemplo real de nuestro sistema:

```
SI temperatura = muy_alta
Y liquido_piso = refrigerante
Y perdida_potencia = True
ENTONCES diagnostico = "Falla múltiple motor-refrigeración" (urgencia: crítica)
```

**Base de Hechos Generales (memoria a largo plazo)**: en nuestro caso, el catálogo de diagnósticos `_RESULTADOS` en `motor.py`. Contiene para cada regla: el diagnóstico, la urgencia, si es seguro manejar y la acción recomendada.

**Hechos Específicos del Caso (memoria de trabajo / working memory)**: los síntomas que ingresa el conductor en cada consulta. En Experta, esto es el objeto `_Sintoma(...)` que se declara al inicio de cada sesión.

**Base de Preguntas**: en nuestra implementación, la interfaz Streamlit funciona como módulo de preguntas. El conductor selecciona sus síntomas en el panel lateral y el sistema los transforma en hechos del caso.

### Organización de las reglas
Las reglas están organizadas por sistema y dentro de cada sistema por especificidad. Una regla más específica (más condiciones) tiene mayor **salience** y gana ante condiciones ambiguas.

---

## BLOQUE 3 — Motor de Inferencia
**(Integrante 3 — ~2 min)**

### Forward Chaining
Nuestro motor de inferencia implementa **encadenamiento hacia adelante (forward chaining)**: parte de los hechos (síntomas reportados) y aplica reglas hasta llegar a una conclusión (diagnóstico).

Esto contrasta con el backward chaining, donde se parte de una hipótesis y se buscan los hechos que la confirman.

### Ciclo Match-Resolve-Act
Como explicó el profesor en Clase 4, el motor repite el ciclo:

1. **Match (Coincidencia de patrones)**: compara los antecedentes de cada regla con los hechos en la working memory. En Experta, cada `@Rule` se evalúa contra el `_Sintoma` declarado.

2. **Resolve (Resolución de conflictos)**: cuando múltiples reglas coinciden, el motor elige cuál ejecutar. Usamos la estrategia de **salience** (importancia): la regla con mayor puntaje de prioridad gana. Por ejemplo, "pastillas y discos" tiene salience=100 porque es el diagnóstico más específico de frenos, mientras que "desequilibrio de ruedas" tiene salience=52.

3. **Act (Activación de consecuencia)**: la regla ganadora declara un nuevo hecho `_Diagnostico(nombre="...")`, que el orquestador convierte en el resultado final.

### Implementación con Experta
Experta es la librería Python equivalente a CLIPS, como vimos en Clase 5. Cada regla es un método decorado con `@Rule`:

```python
@Rule(
    _Sintoma(temperatura=TEMP_MUY_ALTA),
    NOT(_Diagnostico()),
    salience=93,
)
def refrigeracion_recalentamiento_critico(self):
    self.declare(_Diagnostico(nombre="refrigeracion.recalentamiento_critico"))
```

El `NOT(_Diagnostico())` asegura que la agenda solo ejecuta una regla: la de mayor salience.

---

## BLOQUE 4 — Innovaciones: Fuzzy Scoring y Síntomas Opcionales
**(Integrante 4 — ~2 min)**

### Limitación del RBES puro
Un RBES clásico requiere que TODAS las condiciones de una regla estén presentes. Si falta aunque sea una, la regla no dispara. Esto es demasiado rígido para el diagnóstico mecánico.

### Extensión 1: Síntomas visuales opcionales
Las luces del tablero son síntomas visuales que pueden no estar disponibles (foco quemado, conductor que no las nota). Implementamos que si el conductor no reporta ninguna luz (`luces="ninguna"`), esa condición se **excluye del chequeo** en lugar de bloquear la regla.

Esto modela la imprecisión del conocimiento humano: "tengo temperatura muy alta, aunque no vi la luz encendida". El SE igual diagnostica recalentamiento crítico.

### Extensión 2: Fuzzy Scoring (Sistema Experto Difuso)
Como vimos en Clase 5, los **Fuzzy ES** aplican lógica difusa cuando el conocimiento experto es impreciso. 

Cuando ninguna regla del engine dispara exactamente, nuestro fuzzy scorer evalúa el **grado de coincidencia** de cada regla:

```
confianza = condiciones_cumplidas / condiciones_activas
```

Si alguna regla supera el **umbral del 70%**, es candidata. Gana la de mayor urgencia y, en empate, la de mayor confianza. Esto permite diagnósticos parciales en casos donde los síntomas no son concluyentes.

### Extensión 3: Todas las reglas compatibles
En lugar de mostrar solo la regla ganadora, el sistema muestra **todas las reglas compatibles** con los síntomas actuales. Esto permite al mecánico verificar todas las áreas afectadas, aunque el diagnóstico principal sea el más urgente.

---

## BLOQUE 5 — Sistema de Explicación e Interfaz
**(Integrante 5 — ~2 min)**

### Sistema de Explicación (Trazabilidad)
Un componente clave de todo Sistema Experto es el **sistema de explicación**: permite al usuario entender POR QUÉ el sistema llegó a esa conclusión.

En nuestro caso, la tabla "Reglas que se dispararon" muestra:
- El identificador de cada regla (ej: `refrigeracion.recalentamiento_critico`)
- El sistema afectado (Refrigeración, Frenos, etc.)
- El diagnóstico asociado a cada regla
- El nivel de urgencia de cada una

Esto es fundamental en aplicaciones médicas/técnicas: no basta con dar un diagnóstico, hay que mostrar el razonamiento.

### Interfaz con Streamlit
Como el profesor presentó en Clase 5, Streamlit permite construir aplicaciones web interactivas para ciencia de datos en Python puro.

Nuestra interfaz tiene:
- **Sidebar de síntomas**: preguntas organizadas por categoría (ruidos, temperatura, frenos, etc.)
- **Badge de urgencia**: codificado por color (rojo=crítico, naranja=alto, amarillo=moderado, verde=bajo)
- **Gauge Plotly**: visualización del nivel de urgencia en escala 0-100
- **Cards de diagnóstico**: sistema, diagnóstico, seguridad, acción recomendada
- **Tabla de reglas**: trazabilidad completa del razonamiento
- **Casos demo**: 5 casos precargados para demostración

### Demo en vivo
[Demostración con el caso "Recalentamiento crítico sin luz de temperatura" para mostrar el nuevo comportamiento de síntomas opcionales]

---

## BLOQUE 6 — Arquitectura, Resultados y Conclusiones
**(Integrante 6 — ~2 min)**

### Arquitectura completa del sistema

```
Síntomas del conductor (Streamlit UI)
          |
          v
    src/motor.py  (orquestador)
          |
    [1] TriageEngine (Experta - Forward Chaining)
          | salience-based conflict resolution
          |
    [2] _encontrar_compatibles()  → todas las reglas compatibles
          |
    [3] Fallback: _score_fuzzy()  → si no hay match exacto
          |
          v
    Resultado: {diagnostico, urgencia, seguro_manejar, accion,
                reglas_disparadas, sistema}
          |
          v
    app.py (Streamlit) → Badge + Gauge + Cards + Tabla
```

### Resultados QA
El sistema fue validado contra 30 casos de prueba en `data/casos_prueba.csv`:
- **28/30 casos correctos** (93% de tasa de acierto)
- Los 2 casos restantes son inconsistencias del dataset (mismos síntomas, diagnósticos distintos)

### Tecnologías utilizadas
- **Python 3.12+**
- **Experta**: shell de sistema experto (alternativa Python a CLIPS)
- **Streamlit**: interfaz web reactiva
- **Plotly**: gauge de urgencia
- **Pandas**: tabla de trazabilidad

### Conclusiones
- Un RBES es la herramienta ideal cuando el conocimiento es explícito, las reglas son codificables y la explicabilidad es prioritaria
- La extensión fuzzy permite manejar la imprecisión inherente al diagnóstico de campo
- El modelo de síntomas opcionales agrega robustez ante información incompleta, mimicking the way expert human reasoning works under uncertainty
- Streamlit permite construir interfaces de demostración de calidad con muy poco código

### Trabajo futuro
- Incorporar más síntomas (ruidos específicos, códigos OBD)
- Agregar un componente de aprendizaje inductivo (Neural-ES híbrido)
- Integrar fuentes externas como bases de datos de fallas por modelo/año

---

*Fin del guion — Total: ~12 minutos*
