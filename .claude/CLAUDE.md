# Triage Mecánico · Sistema Experto

## Descripción del proyecto
Sistema experto en Python + Streamlit que diagnostica fallas
mecánicas en autos por síntomas (ruidos, humo, vibraciones).

## Sub-Agent Routing Rules

**Paralelo** (todas las condiciones se cumplen):
- 3+ tareas independientes
- Sin estado compartido entre tareas
- Archivos separados sin riesgo de conflicto

**Secuencial** (cualquiera de estas aplica):
- Tarea B depende del output de tarea A
- Archivos compartidos (riesgo de conflicto)
- Scope poco claro (explorar antes de actuar)

## Orden de ejecución sugerido
1. motor-reglas  → escribe src/motor.py y src/reglas/*.py
2. qa-tester     → valida contra data/casos_prueba.csv
3. ui-builder    → construye app.py conectada al motor
4. documentador  → README + docstrings