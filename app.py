"""
Interfaz Streamlit para el sistema experto de triage mecanico.

Estructura:
- Sidebar: inputs organizados por sistema del auto + selector de demos
- Panel principal: badge de urgencia, gauge Plotly, card de diagnostico,
  tabla de reglas disparadas
"""

import sys
import os

# Permite importar src.motor desde la raiz del proyecto
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.motor import diagnosticar

# ---------------------------------------------------------------------------
# Configuracion de pagina
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Triage Mecanico",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Casos demo
# ---------------------------------------------------------------------------
CASOS_DEMO = [
    {
        "nombre": "Pastillas y discos (critico)",
        "sintomas": {
            "ruido": "chirrido",
            "cuando_ruido": "al_frenar",
            "humo": "ninguno",
            "vibracion": True,
            "donde_vibracion": "pedal_de_freno",
            "temperatura": "normal",
            "luces": "ninguna",
            "comportamiento_freno": "vibra",
            "perdida_potencia": False,
            "liquido_piso": "ninguno",
        },
    },
    {
        "nombre": "Recalentamiento critico",
        "sintomas": {
            "ruido": "ninguno",
            "cuando_ruido": "ninguno",
            "humo": "ninguno",
            "vibracion": False,
            "donde_vibracion": "ninguna",
            "temperatura": "muy_alta",
            "luces": "temperatura",
            "comportamiento_freno": "normal",
            "perdida_potencia": False,
            "liquido_piso": "ninguno",
        },
    },
    {
        "nombre": "Quema de aceite",
        "sintomas": {
            "ruido": "ninguno",
            "cuando_ruido": "ninguno",
            "humo": "azul",
            "vibracion": False,
            "donde_vibracion": "ninguna",
            "temperatura": "normal",
            "luces": "aceite",
            "comportamiento_freno": "normal",
            "perdida_potencia": True,
            "liquido_piso": "aceite",
        },
    },
    {
        "nombre": "Falla en diferencial",
        "sintomas": {
            "ruido": "zumbido",
            "cuando_ruido": "siempre",
            "humo": "ninguno",
            "vibracion": False,
            "donde_vibracion": "ninguna",
            "temperatura": "normal",
            "luces": "ninguna",
            "comportamiento_freno": "normal",
            "perdida_potencia": True,
            "liquido_piso": "ninguno",
        },
    },
    {
        "nombre": "Sin fallas detectadas",
        "sintomas": {
            "ruido": "ninguno",
            "cuando_ruido": "ninguno",
            "humo": "ninguno",
            "vibracion": False,
            "donde_vibracion": "ninguna",
            "temperatura": "normal",
            "luces": "ninguna",
            "comportamiento_freno": "normal",
            "perdida_potencia": False,
            "liquido_piso": "ninguno",
        },
    },
]

# ---------------------------------------------------------------------------
# Opciones de cada campo (valor_interno -> etiqueta visible)
# ---------------------------------------------------------------------------
OPCIONES_RUIDO = {
    "ninguno": "Ninguno",
    "chirrido": "Chirrido",
    "golpeteo": "Golpeteo",
    "zumbido": "Zumbido",
    "crujido": "Crujido",
}
OPCIONES_CUANDO_RUIDO = {
    "ninguno": "Ninguno",
    "al_frenar": "Al frenar",
    "al_acelerar": "Al acelerar",
    "siempre": "Siempre",
    "en_neutro": "En neutro",
    "en_baches": "En baches",
    "al_girar": "Al girar",
}
OPCIONES_HUMO = {
    "ninguno": "Ninguno",
    "azul": "Azul",
    "blanco": "Blanco",
    "negro": "Negro",
}
OPCIONES_TEMPERATURA = {
    "normal": "Normal",
    "alta": "Alta",
    "muy_alta": "Muy alta",
}
OPCIONES_LUCES = {
    "ninguna": "Ninguna",
    "temperatura": "Temperatura",
    "aceite": "Aceite",
    "bateria": "Bateria",
    "check_engine": "Check Engine",
}
OPCIONES_LIQUIDO_PISO = {
    "ninguno": "Ninguno",
    "aceite": "Aceite",
    "refrigerante": "Refrigerante",
}
OPCIONES_DONDE_VIBRACION = {
    "ninguna": "Ninguna",
    "volante": "Volante",
    "pedal_de_freno": "Pedal de freno",
    "todo_el_auto": "Todo el auto",
}
OPCIONES_FRENO = {
    "normal": "Normal",
    "vibra": "Vibra",
    "tarda_mas": "Tarda mas",
    "se_va_hacia_un_lado": "Se va hacia un lado",
}


def _keys(opciones: dict) -> list:
    """Retorna la lista de claves internas de un dict de opciones.

    Args:
        opciones: Dict con formato {valor_interno: etiqueta_visible}.

    Returns:
        Lista de strings con los valores internos, en orden de insercion.
    """
    return list(opciones.keys())


def _labels(opciones: dict) -> list:
    """Retorna la lista de etiquetas visibles de un dict de opciones.

    Args:
        opciones: Dict con formato {valor_interno: etiqueta_visible}.

    Returns:
        Lista de strings con las etiquetas para mostrar al usuario.
    """
    return list(opciones.values())


def _index_of(opciones: dict, valor: str) -> int:
    """Retorna el indice de un valor interno dentro de un dict de opciones.

    Usado para sincronizar el widget de Streamlit con el session_state
    cuando se carga un caso demo.

    Args:
        opciones: Dict con formato {valor_interno: etiqueta_visible}.
        valor: Valor interno a buscar.

    Returns:
        Indice entero de la clave encontrada, o 0 si no existe.
    """
    keys = _keys(opciones)
    return keys.index(valor) if valor in keys else 0


# ---------------------------------------------------------------------------
# Estado de sesion — valores iniciales
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "ruido": "ninguno",
    "cuando_ruido": "ninguno",
    "humo": "ninguno",
    "vibracion": False,
    "donde_vibracion": "ninguna",
    "temperatura": "normal",
    "luces": "ninguna",
    "comportamiento_freno": "normal",
    "perdida_potencia": False,
    "liquido_piso": "ninguno",
    "demo_index": 0,          # 0 = "— Personalizado —"
    "resultado": None,
}

for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Helpers de estado
# ---------------------------------------------------------------------------
def _aplicar_demo(idx: int) -> None:
    """Carga los sintomas del caso demo en el session_state."""
    caso = CASOS_DEMO[idx - 1]  # idx=0 es "Personalizado"
    for campo, valor in caso["sintomas"].items():
        st.session_state[campo] = valor


def _build_sintomas() -> dict:
    """Construye el dict de sintomas a partir del session_state actual.

    Aplica logica condicional para los campos dependientes: si no hay ruido,
    fuerza cuando_ruido a "ninguno"; si no hay vibracion, fuerza
    donde_vibracion a "ninguna". Esto evita que valores residuales de
    sesiones anteriores contaminen el diagnostico.

    Returns:
        Dict con las 10 claves que espera src.motor.diagnosticar:
        ruido, cuando_ruido, humo, vibracion, donde_vibracion,
        temperatura, luces, comportamiento_freno, perdida_potencia,
        liquido_piso.
    """
    ruido = st.session_state["ruido"]
    vibracion = st.session_state["vibracion"]
    return {
        "ruido": ruido,
        # Si el ruido es ninguno, el campo condicional no aplica
        "cuando_ruido": st.session_state["cuando_ruido"] if ruido != "ninguno" else "ninguno",
        "humo": st.session_state["humo"],
        "vibracion": vibracion,
        # Si no hay vibracion, el campo condicional no aplica
        "donde_vibracion": st.session_state["donde_vibracion"] if vibracion else "ninguna",
        "temperatura": st.session_state["temperatura"],
        "luces": st.session_state["luces"],
        "comportamiento_freno": st.session_state["comportamiento_freno"],
        "perdida_potencia": st.session_state["perdida_potencia"],
        "liquido_piso": st.session_state["liquido_piso"],
    }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("Triage Mecanico")
    st.caption("Sistema experto de diagnostico de fallas en vehiculos")

    st.divider()

    # ---- Selector de demo ----
    nombres_demo = ["— Personalizado —"] + [c["nombre"] for c in CASOS_DEMO]
    demo_sel = st.selectbox(
        "Cargar caso demo",
        options=range(len(nombres_demo)),
        format_func=lambda i: nombres_demo[i],
        index=st.session_state["demo_index"],
        key="_demo_sel_widget",
        help="Selecciona un caso precargado para rellenar los campos automaticamente.",
    )

    if demo_sel != st.session_state["demo_index"]:
        st.session_state["demo_index"] = demo_sel
        if demo_sel > 0:
            _aplicar_demo(demo_sel)
        st.rerun()

    st.divider()

    # ---- Seccion: Ruidos ----
    st.subheader("Ruidos")

    ruido_val = st.selectbox(
        "Tipo de ruido",
        options=_keys(OPCIONES_RUIDO),
        format_func=lambda v: OPCIONES_RUIDO[v],
        index=_index_of(OPCIONES_RUIDO, st.session_state["ruido"]),
        key="ruido",
    )

    ruido_activo = st.session_state["ruido"] != "ninguno"
    cuando_ruido_val = st.selectbox(
        "Cuando ocurre el ruido",
        options=_keys(OPCIONES_CUANDO_RUIDO),
        format_func=lambda v: OPCIONES_CUANDO_RUIDO[v],
        index=_index_of(OPCIONES_CUANDO_RUIDO, st.session_state["cuando_ruido"]),
        key="cuando_ruido",
        disabled=not ruido_activo,
        help="Solo disponible cuando hay un ruido seleccionado.",
    )

    st.divider()

    # ---- Seccion: Humo y temperatura ----
    st.subheader("Humo y temperatura")

    st.selectbox(
        "Color del humo",
        options=_keys(OPCIONES_HUMO),
        format_func=lambda v: OPCIONES_HUMO[v],
        index=_index_of(OPCIONES_HUMO, st.session_state["humo"]),
        key="humo",
    )

    st.selectbox(
        "Temperatura del motor",
        options=_keys(OPCIONES_TEMPERATURA),
        format_func=lambda v: OPCIONES_TEMPERATURA[v],
        index=_index_of(OPCIONES_TEMPERATURA, st.session_state["temperatura"]),
        key="temperatura",
    )

    st.divider()

    # ---- Seccion: Senales visuales ----
    st.subheader("Senales visuales")

    st.selectbox(
        "Luz de advertencia encendida",
        options=_keys(OPCIONES_LUCES),
        format_func=lambda v: OPCIONES_LUCES[v],
        index=_index_of(OPCIONES_LUCES, st.session_state["luces"]),
        key="luces",
    )

    st.checkbox(
        "Perdida de potencia",
        value=st.session_state["perdida_potencia"],
        key="perdida_potencia",
    )

    st.selectbox(
        "Liquido en el piso",
        options=_keys(OPCIONES_LIQUIDO_PISO),
        format_func=lambda v: OPCIONES_LIQUIDO_PISO[v],
        index=_index_of(OPCIONES_LIQUIDO_PISO, st.session_state["liquido_piso"]),
        key="liquido_piso",
    )

    st.divider()

    # ---- Seccion: Vibracion ----
    st.subheader("Vibracion")

    st.checkbox(
        "Hay vibracion",
        value=st.session_state["vibracion"],
        key="vibracion",
    )

    vibracion_activa = st.session_state["vibracion"]
    st.selectbox(
        "Donde se siente la vibracion",
        options=_keys(OPCIONES_DONDE_VIBRACION),
        format_func=lambda v: OPCIONES_DONDE_VIBRACION[v],
        index=_index_of(OPCIONES_DONDE_VIBRACION, st.session_state["donde_vibracion"]),
        key="donde_vibracion",
        disabled=not vibracion_activa,
        help="Solo disponible cuando hay vibracion.",
    )

    st.divider()

    # ---- Seccion: Frenos ----
    st.subheader("Frenos")

    st.selectbox(
        "Comportamiento del freno",
        options=_keys(OPCIONES_FRENO),
        format_func=lambda v: OPCIONES_FRENO[v],
        index=_index_of(OPCIONES_FRENO, st.session_state["comportamiento_freno"]),
        key="comportamiento_freno",
    )

    st.divider()

    # ---- Boton de diagnostico ----
    diagnosticar_btn = st.button(
        "Diagnosticar",
        type="primary",
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Logica de diagnostico
# ---------------------------------------------------------------------------
if diagnosticar_btn or (st.session_state["demo_index"] > 0 and st.session_state.get("resultado") is None):
    sintomas = _build_sintomas()
    st.session_state["resultado"] = diagnosticar(sintomas)

# ---------------------------------------------------------------------------
# Panel principal
# ---------------------------------------------------------------------------
st.title("Diagnostico del Vehiculo")

resultado = st.session_state.get("resultado")

if resultado is None:
    # Estado inicial: instrucciones
    st.info(
        "Configure los sintomas en el panel lateral y presione **Diagnosticar**, "
        "o seleccione un **caso demo** para ver un ejemplo precargado.",
        icon="ℹ️",
    )
    st.stop()

# ---------------------------------------------------------------------------
# Mapa de urgencia
# ---------------------------------------------------------------------------
_URGENCIA_CONFIG = {
    "critica":  {"color": "#e74c3c", "label": "CRITICA",  "valor": 87, "texto": "Critica"},
    "alta":     {"color": "#e67e22", "label": "ALTA",     "valor": 62, "texto": "Alta"},
    "moderada": {"color": "#f1c40f", "label": "MODERADA", "valor": 37, "texto": "Moderada"},
    "baja":     {"color": "#2ecc71", "label": "BAJA",     "valor": 12, "texto": "Baja"},
}

urgencia = resultado.get("urgencia", "baja")
cfg = _URGENCIA_CONFIG.get(urgencia, _URGENCIA_CONFIG["baja"])

# ---------------------------------------------------------------------------
# Fila 1: Badge + Gauge
# ---------------------------------------------------------------------------
col_badge, col_gauge = st.columns([1, 2], gap="large")

with col_badge:
    st.markdown(
        f"""
        <div style="
            background-color: {cfg['color']};
            color: white;
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-align: center;
            padding: 1.2rem 2rem;
            border-radius: 12px;
            margin-top: 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        ">
            URGENCIA<br>{cfg['label']}
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_gauge:
    gauge_fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=cfg["valor"],
            number={"suffix": "", "font": {"size": 28}},
            title={"text": "Nivel de urgencia", "font": {"size": 16}},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickvals": [0, 25, 50, 75, 100],
                    "ticktext": ["0", "25", "50", "75", "100"],
                    "tickfont": {"size": 12},
                },
                "bar": {"color": cfg["color"], "thickness": 0.25},
                "steps": [
                    {"range": [0, 25],   "color": "#d5f5e3"},  # baja      - verde claro
                    {"range": [25, 50],  "color": "#fef9e7"},  # moderada  - amarillo claro
                    {"range": [50, 75],  "color": "#fdebd0"},  # alta      - naranja claro
                    {"range": [75, 100], "color": "#fadbd8"},  # critica   - rojo claro
                ],
                "threshold": {
                    "line": {"color": cfg["color"], "width": 4},
                    "thickness": 0.75,
                    "value": cfg["valor"],
                },
            },
        )
    )
    gauge_fig.update_layout(
        height=280,
        margin={"t": 40, "b": 10, "l": 30, "r": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#333"},
    )
    st.plotly_chart(gauge_fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Fila 2: Card de diagnostico
# ---------------------------------------------------------------------------
st.divider()

seguro_manejar = resultado.get("seguro_manejar", "si")
_SEGURO_ICONO = {
    "si": "✅",
    "con_precaucion": "⚠️",
    "no": "🚫",
}
_SEGURO_TEXTO = {
    "si": "Si, puede manejar",
    "con_precaucion": "Con precaucion",
    "no": "No debe manejar",
}
icono_seguro = _SEGURO_ICONO.get(seguro_manejar, "✅")
texto_seguro = _SEGURO_TEXTO.get(seguro_manejar, seguro_manejar)

sistema = resultado.get("sistema", "ninguno").capitalize()
diagnostico_texto = resultado.get("diagnostico", "")
accion_texto = resultado.get("accion", "")

st.subheader("Resultado del diagnostico")

col_info1, col_info2 = st.columns(2, gap="large")

with col_info1:
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            border-left: 5px solid {cfg['color']};
            border-radius: 8px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 0.5rem;
        ">
            <p style="margin:0 0 0.4rem 0; font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:0.05em;">Sistema afectado</p>
            <p style="margin:0; font-size:1.3rem; font-weight:700; color:#222;">{sistema}</p>
        </div>
        <div style="
            background-color: #f8f9fa;
            border-left: 5px solid {cfg['color']};
            border-radius: 8px;
            padding: 1.2rem 1.4rem;
        ">
            <p style="margin:0 0 0.4rem 0; font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:0.05em;">Diagnostico</p>
            <p style="margin:0; font-size:1.15rem; font-weight:600; color:#222;">{diagnostico_texto}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_info2:
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            border-left: 5px solid {cfg['color']};
            border-radius: 8px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 0.5rem;
        ">
            <p style="margin:0 0 0.4rem 0; font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:0.05em;">Seguro para manejar</p>
            <p style="margin:0; font-size:1.3rem; font-weight:700; color:#222;">{icono_seguro} {texto_seguro}</p>
        </div>
        <div style="
            background-color: #f8f9fa;
            border-left: 5px solid {cfg['color']};
            border-radius: 8px;
            padding: 1.2rem 1.4rem;
        ">
            <p style="margin:0 0 0.4rem 0; font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:0.05em;">Accion recomendada</p>
            <p style="margin:0; font-size:1.0rem; color:#333;">{accion_texto}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Fila 3: Tabla de reglas disparadas
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Trazabilidad — Reglas disparadas")

reglas = resultado.get("reglas_disparadas", [])

if reglas:
    df_reglas = pd.DataFrame(
        {
            "N°": range(1, len(reglas) + 1),
            "Regla disparada": reglas,
            "Modulo": [r.split(".")[0].capitalize() if "." in r else r for r in reglas],
        }
    )
    st.dataframe(
        df_reglas,
        use_container_width=True,
        hide_index=True,
        column_config={
            "N°": st.column_config.NumberColumn(width="small"),
            "Regla disparada": st.column_config.TextColumn(width="large"),
            "Modulo": st.column_config.TextColumn(width="medium"),
        },
    )
else:
    st.info("No se dispararon reglas especificas — el vehiculo esta en condiciones normales.", icon="✅")
