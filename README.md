# Triage Mecanico — Sistema Experto de Diagnostico Automotriz

Trabajo Practico Final — Inteligencia Artificial / Sistemas Expertos  
Universidad — 2026

---

## Descripcion

Triage Mecanico es un sistema experto basado en reglas que diagnostica fallas mecanicas
en vehiculos a partir de sintomas observables: ruidos, color del humo, temperatura,
vibraciones, luces de tablero y comportamiento del freno.

El sistema encadena seis modulos de reglas (uno por sistema del vehiculo) en orden de
prioridad medica descendente — de mayor riesgo a menor — y retorna el primer diagnostico
que aplique junto con el nivel de urgencia, la recomendacion de seguridad y la accion
sugerida. Si ningun modulo dispara, se informa que el vehiculo esta en condiciones normales.

La interfaz grafica, construida con Streamlit, permite ingresar sintomas manualmente o
cargar uno de los cinco casos demo precargados. El resultado se presenta como un badge
de urgencia codificado por color, un gauge Plotly y una tabla de trazabilidad con las
reglas disparadas.

---

## Instalacion

### Requisitos previos

- Python 3.10 o superior
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd triage-mecanico

# 2. (Opcional) Crear entorno virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Lanzar la aplicacion
streamlit run app.py
```

La aplicacion abre automaticamente en `http://localhost:8501`.

---

## Uso

### Caso demo (forma rapida)

1. En el panel lateral, desplegar el selector **"Cargar caso demo"**.
2. Elegir uno de los cinco casos predefinidos (por ejemplo, "Recalentamiento critico").
3. Los campos se rellenan automaticamente y el diagnostico aparece en pantalla.

### Sintomas propios (caso manual)

1. Seleccionar **"— Personalizado —"** en el selector de demos.
2. Completar los campos del panel lateral agrupados por categoria:
   - **Ruidos**: tipo de ruido y momento en que ocurre.
   - **Humo y temperatura**: color del escape y lectura del tablero.
   - **Senales visuales**: luz de advertencia encendida, perdida de potencia y liquido en el piso.
   - **Vibracion**: presencia y ubicacion (volante, pedal de freno, todo el auto).
   - **Frenos**: comportamiento al frenar.
3. Presionar **"Diagnosticar"**.

### Interpretar el resultado

| Elemento | Descripcion |
|---|---|
| Badge de urgencia | Critica / Alta / Moderada / Baja, con color semaforo |
| Gauge | Nivel numerico de urgencia en escala 0-100 |
| Sistema afectado | Modulo que disparo la regla (frenos, motor, etc.) |
| Diagnostico | Falla concreta identificada |
| Seguro para manejar | Si / Con precaucion / No debe manejar |
| Accion recomendada | Paso inmediato a seguir |
| Tabla de trazabilidad | Identificadores de las reglas que se activaron |

---

## Arquitectura

```
Sintomas ingresados por el usuario
            |
            v
     src/motor.py  (orquestador)
            |
    Encadena modulos en orden de prioridad:
            |
      +-----+-------+------------+-------------+------------+----------+
      |             |            |             |            |          |
  frenos    motor_combustion  refrigeracion  transmision  suspension  electrico
      |             |            |             |            |          |
      +-----+-------+------------+-------------+------------+----------+
            |
    Primer resultado no-None
            |
            v
     Diccionario de diagnostico:
     {
       diagnostico,
       urgencia,
       seguro_manejar,
       accion,
       reglas_disparadas,
       sistema
     }
            |
            v
       app.py  (Streamlit)
       Muestra badge, gauge, card y tabla de reglas
```

El motor aplica encadenamiento hacia adelante (forward chaining): evalua cada modulo en
orden, y retorna el primer diagnostico positivo. Los modulos de mayor riesgo de vida
(frenos, motor) se evaluan antes que los de menor riesgo (suspension, electrico).

---

## Sistemas cubiertos

| Sistema | Archivo | Reglas | Casos de prueba |
|---|---|---|---|
| Frenos | `src/reglas/frenos.py` | 5 | 1, 2, 3, 4, 5 |
| Motor de combustion | `src/reglas/motor_combustion.py` | 6 | 6, 7, 8, 9, 10, 29 |
| Refrigeracion | `src/reglas/refrigeracion.py` | 5 | 11, 12, 13, 14, 15 |
| Transmision | `src/reglas/transmision.py` | 5 | 16, 17, 18, 19, 20 |
| Suspension | `src/reglas/suspension.py` | 5 | 21, 22, 23, 24, 25 |
| Electrico | `src/reglas/electrico.py` | 2 | 26, 27, 28 |
| **Total** | | **28** | **30** |

### Detalle de reglas por sistema

**Frenos**
- `pastillas_y_discos_mal_estado` — chirrido al frenar + vibracion en pedal + freno vibra (caso critico combinado)
- `pinza_trabada` — freno se va hacia un lado
- `pastillas_desgastadas` — chirrido al frenar sin combinacion disco
- `discos_deformados` — vibracion en pedal sin chirrido
- `liquido_bajo_o_contaminado` — freno tarda mas

**Motor de combustion**
- `presion_aceite_baja_cojinetes` — golpeteo constante + luz aceite + perdida potencia + aceite en piso
- `junta_culata_refrigerante` — humo blanco + temperatura muy alta + luz temperatura + refrigerante en piso
- `quema_aceite_anillos_guias` — humo azul + luz aceite + perdida potencia + aceite en piso
- `mezcla_rica_inyectores` — humo negro + check engine + perdida potencia
- `detonacion_combustion` — golpeteo al acelerar sin luz aceite
- `luz_aceite_nivel_bomba` — luz aceite + aceite en piso sin golpeteo

**Refrigeracion**
- `falla_multiple_motor_refrigeracion` — temperatura muy alta + luz temperatura + perdida potencia + refrigerante en piso
- `recalentamiento_critico` — temperatura muy alta + luz temperatura, sin fuga activa
- `fuga_con_recalentamiento` — temperatura alta + luz temperatura + refrigerante en piso
- `radiador_tapa_expansion` — humo blanco + temperatura alta sin refrigerante en piso
- `fuga_sin_recalentamiento` — refrigerante en piso con temperatura normal

**Transmision**
- `diferencial_semiejes` — zumbido constante + perdida de potencia
- `problema_caja_interna` — golpeteo en neutro
- `tirones_embrague_caja` — perdida de potencia sin ruido, humo ni luces
- `cojinete_desgastado` — zumbido al acelerar sin perdida de potencia
- `fuga_aceite_transmision` — aceite en piso sin luz de aceite

**Suspension**
- `rotula_junta_homocinetica` — crujido al girar + vibracion en volante
- `falla_grave_suspension` — vibracion en todo el auto
- `desalineacion_neumatico` — freno se va hacia un lado (fallback de suspension)
- `bujes_rotulas_desgastadas` — crujido en baches sin vibracion en volante
- `desbalanceo_amortiguadores` — vibracion en volante sin crujido al girar

**Electrico**
- `bateria_o_alternador` — luz de bateria encendida
- `sensor_gestion_motor` — check engine + perdida de potencia

---

## Resultados QA

El modulo de pruebas ejecuta los 30 casos de `data/casos_prueba.csv` contra el motor y
compara el diagnostico producido con el esperado.

| Metrica | Valor |
|---|---|
| Casos totales | 30 |
| Casos que pasan | 28 |
| Tasa de acierto | 93% |

### Los 2 casos que no pasan

**Caso 24 — Desalineacion o neumatico desinflado**  
Sintomas: `comportamiento_freno = se_va_hacia_un_lado`, todos los demas en estado normal.  
El dataset espera que este caso sea capturado por el modulo de suspension como
desalineacion. Sin embargo, esos sintomas son identicos a los del caso 3 (pinza de freno
trabada), y el modulo de frenos tiene prioridad en el motor principal. El motor retorna
correctamente "Pinza de freno trabada" (urgencia critica), que es el diagnostico mas
conservador ante sintomas ambiguos. La inconsistencia es del dataset, no del motor.

**Caso 28 — Alternador no carga**  
Sintomas: `luces = bateria`, todos los demas en estado normal.  
El dataset espera "Alternador no carga - riesgo de quedarse sin energia", pero los
sintomas son identicos a los del caso 26 ("Bateria debil o alternador fallando"). El
motor produce el diagnostico del caso 26, que es igualmente correcto desde el punto de
vista clinico. La distincion entre los dos diagnosticos requeriria informacion adicional
(tension del alternador, edad de la bateria) que no forma parte del schema de sintomas.

Ambos fallos son inconsistencias del dataset: sintomas identicos mapeados a diagnosticos
distintos. No representan bugs del motor de inferencia.

---

## Estructura de archivos

```
triage-mecanico/
|
|-- app.py                      # Interfaz Streamlit (sidebar, gauge, tabla)
|-- requirements.txt            # Dependencias Python
|-- README.md                   # Este archivo
|
|-- src/
|   |-- __init__.py
|   |-- motor.py                # Orquestador: encadena los 6 modulos en orden de prioridad
|   |-- constantes.py           # Todas las constantes del dominio (sin hardcoding en reglas)
|   |
|   `-- reglas/
|       |-- __init__.py
|       |-- frenos.py           # 5 reglas: pastillas, discos, pinza, liquido
|       |-- motor_combustion.py # 6 reglas: aceite, junta culata, mezcla, detonacion
|       |-- refrigeracion.py    # 5 reglas: recalentamiento, fugas, radiador
|       |-- transmision.py      # 5 reglas: cojinetes, caja, embrague, diferencial
|       |-- suspension.py       # 5 reglas: rotulas, desbalanceo, alineacion
|       `-- electrico.py        # 2 reglas: bateria/alternador, sensor/ECU
|
`-- data/
    `-- casos_prueba.csv        # 30 casos con sintomas y diagnostico esperado
```

---

## Tecnologias utilizadas

- Python 3.10+
- Streamlit — interfaz web reactiva
- Plotly — gauge chart de urgencia
- Pandas — tabla de reglas disparadas

---

## Decisiones de diseno

**Orden de prioridad medica**: los modulos se encadenan de mayor a menor riesgo de vida.
Frenos va primero porque una falla de frenos puede causar accidentes inmediatos.
Electrico va ultimo porque sus fallas raramente son inmediatamente peligrosas.

**Retorno del primer match**: el motor aplica early-exit en cuanto un modulo dispara.
Esto implica que los casos ambiguos se resuelven siempre a favor del diagnostico mas
conservador (mayor urgencia), lo cual es correcto en un sistema de triage.

**Constantes centralizadas**: todos los valores de dominio estan en `src/constantes.py`.
Las reglas nunca usan strings literales, lo que facilita cambios y evita errores tipograficos.

**Reglas privadas con docstring**: cada condicion logica tiene su propia funcion `_regla_*`
documentada con la justificacion medica, lo que permite auditar y modificar reglas
individualmente sin tocar la funcion publica `diagnosticar`.
