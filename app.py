"""
Interfaz Streamlit para el sistema experto de triage mecánico.

Estructura:
- Sidebar: selector de categorías de síntomas + campos condicionales por categoría
- Panel principal: badge de urgencia, gauge Plotly, cards de diagnóstico,
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
    page_title="Triage Mecánico",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Casos demo
# ---------------------------------------------------------------------------
CASOS_DEMO = [
    {
        "nombre": "Pastillas y discos (crítico)",
        "sintomas": {
            "ruido": "chirrido",
            "cuando_ruido": "al_frenar",
            "humo": "ninguno",
            "donde_vibracion": "pedal_de_freno",
            "temperatura": "normal",
            "luces": "ninguna",
            "comportamiento_freno": "vibra",
            "perdida_potencia": False,
            "liquido_piso": "ninguno",
        },
    },
    {
        "nombre": "Recalentamiento crítico",
        "sintomas": {
            "ruido": "ninguno",
            "cuando_ruido": "ninguno",
            "humo": "ninguno",
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
    "ninguno": "Otro / No especificado",
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
    "bateria": "Batería",
    "check_engine": "Check Engine",
    "otro": "Otra luz",
}
OPCIONES_LIQUIDO_PISO = {
    "ninguno": "Ninguno",
    "aceite": "Aceite",
    "refrigerante": "Refrigerante",
    "agua": "Agua",
    "otro": "Otro líquido",
}
OPCIONES_DONDE_VIBRACION = {
    "ninguna": "Ninguna",
    "volante": "Volante",
    "pedal_de_freno": "Pedal de freno",
    "todo_el_auto": "Todo el auto",
    "otro": "Otro lugar",
}
OPCIONES_FRENO = {
    "normal": "Normal",
    "vibra": "Vibra",
    "tarda_mas": "Tarda más",
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
    "donde_vibracion": "ninguna",
    "temperatura": "normal",
    "luces": "ninguna",
    "comportamiento_freno": "normal",
    "perdida_potencia": False,
    "liquido_piso": "ninguno",
    "demo_index": 0,          # 0 = "— Personalizado —"
    "resultado": None,
    # Categorias activas (flujo secuencial)
    "cat_ruidos": False,
    "cat_humo_temp": False,
    "cat_visuales": False,
    "cat_vibracion": False,
    "cat_frenos": False,
}

for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Helpers de estado
# ---------------------------------------------------------------------------
def _inferir_categorias(sintomas: dict) -> dict:
    """Infiere que categorias deben activarse a partir de los valores de un caso demo.

    Args:
        sintomas: Dict de sintomas del caso demo.

    Returns:
        Dict con las claves cat_* y sus valores booleanos inferidos.
    """
    return {
        "cat_ruidos": sintomas.get("ruido", "ninguno") != "ninguno",
        "cat_humo_temp": (
            sintomas.get("humo", "ninguno") != "ninguno"
            or sintomas.get("temperatura", "normal") != "normal"
        ),
        "cat_visuales": (
            sintomas.get("luces", "ninguna") != "ninguna"
            or sintomas.get("perdida_potencia", False)
            or sintomas.get("liquido_piso", "ninguno") != "ninguno"
        ),
        "cat_vibracion": sintomas.get("donde_vibracion", "ninguna") != "ninguna",
        "cat_frenos": sintomas.get("comportamiento_freno", "normal") != "normal",
    }


def _aplicar_demo(idx: int) -> None:
    """Carga los sintomas del caso demo en el session_state e infiere categorias."""
    caso = CASOS_DEMO[idx - 1]  # idx=0 es "Personalizado"
    for campo, valor in caso["sintomas"].items():
        st.session_state[campo] = valor
    # Inferir y activar las categorias correspondientes
    cats = _inferir_categorias(caso["sintomas"])
    for k, v in cats.items():
        st.session_state[k] = v


def _build_sintomas() -> dict:
    """Construye el dict de sintomas a partir del session_state actual.

    Aplica logica condicional basada en categorias activas: si una categoria
    no esta activa, sus campos se fuerzan a valor neutro para evitar que
    valores residuales contaminen el diagnostico.

    Returns:
        Dict con las 10 claves que espera src.motor.diagnosticar:
        ruido, cuando_ruido, humo, vibracion, donde_vibracion,
        temperatura, luces, comportamiento_freno, perdida_potencia,
        liquido_piso.
    """
    cat_ruidos = st.session_state.get("cat_ruidos", False)
    cat_humo_temp = st.session_state.get("cat_humo_temp", False)
    cat_visuales = st.session_state.get("cat_visuales", False)
    cat_vibracion = st.session_state.get("cat_vibracion", False)
    cat_frenos = st.session_state.get("cat_frenos", False)

    # Ruido
    ruido = st.session_state["ruido"] if cat_ruidos else "ninguno"
    cuando_ruido = st.session_state["cuando_ruido"] if (cat_ruidos and ruido != "ninguno") else "ninguno"

    # Humo y temperatura
    humo = st.session_state["humo"] if cat_humo_temp else "ninguno"
    temperatura = st.session_state["temperatura"] if cat_humo_temp else "normal"

    # Senales visuales
    luces = st.session_state["luces"] if cat_visuales else "ninguna"
    perdida_potencia = st.session_state["perdida_potencia"] if cat_visuales else False
    liquido_piso = st.session_state["liquido_piso"] if cat_visuales else "ninguno"

    # Vibracion (calculada desde donde_vibracion)
    donde_vibracion = st.session_state["donde_vibracion"] if cat_vibracion else "ninguna"
    vibracion = donde_vibracion != "ninguna"

    # Frenos
    comportamiento_freno = st.session_state["comportamiento_freno"] if cat_frenos else "normal"

    return {
        "ruido": ruido,
        "cuando_ruido": cuando_ruido,
        "humo": humo,
        "vibracion": vibracion,
        "donde_vibracion": donde_vibracion,
        "temperatura": temperatura,
        "luces": luces,
        "comportamiento_freno": comportamiento_freno,
        "perdida_potencia": perdida_potencia,
        "liquido_piso": liquido_piso,
    }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("Triage Mecánico")
    st.caption("Sistema experto de diagnóstico de fallas en vehículos")

    st.divider()

    # ---- Selector de demo ----
    nombres_demo = ["— Personalizado —"] + [c["nombre"] for c in CASOS_DEMO]
    demo_sel = st.selectbox(
        "Cargar caso demo",
        options=range(len(nombres_demo)),
        format_func=lambda i: nombres_demo[i],
        index=st.session_state["demo_index"],
        key="_demo_sel_widget",
        help="Seleccioná un caso precargado para rellenar los campos automáticamente.",
    )

    if demo_sel != st.session_state["demo_index"]:
        st.session_state["demo_index"] = demo_sel
        if demo_sel > 0:
            _aplicar_demo(demo_sel)
        st.rerun()

    st.divider()

    # ---- Seleccion de categorias de sintomas ----
    st.markdown("**¿Qué síntomas detecta?**")
    st.caption("Seleccioná todas las que apliquen.")

    cat_ruidos = st.checkbox(
        "Ruidos",
        value=st.session_state["cat_ruidos"],
        key="cat_ruidos",
    )
    cat_humo_temp = st.checkbox(
        "Humo / Temperatura",
        value=st.session_state["cat_humo_temp"],
        key="cat_humo_temp",
    )
    cat_visuales = st.checkbox(
        "Señales visuales",
        value=st.session_state["cat_visuales"],
        key="cat_visuales",
    )
    cat_vibracion = st.checkbox(
        "Vibración",
        value=st.session_state["cat_vibracion"],
        key="cat_vibracion",
    )
    cat_frenos = st.checkbox(
        "Frenos",
        value=st.session_state["cat_frenos"],
        key="cat_frenos",
    )

    # ---- Campos condicionales por categoria ----

    # -- Ruidos --
    if st.session_state["cat_ruidos"]:
        st.divider()
        st.subheader("Ruidos")

        st.selectbox(
            "Tipo de ruido",
            options=_keys(OPCIONES_RUIDO),
            format_func=lambda v: OPCIONES_RUIDO[v],
            index=_index_of(OPCIONES_RUIDO, st.session_state["ruido"]),
            key="ruido",
        )

        ruido_activo = st.session_state["ruido"] != "ninguno"
        st.selectbox(
            "Cuándo ocurre el ruido",
            options=_keys(OPCIONES_CUANDO_RUIDO),
            format_func=lambda v: OPCIONES_CUANDO_RUIDO[v],
            index=_index_of(OPCIONES_CUANDO_RUIDO, st.session_state["cuando_ruido"]),
            key="cuando_ruido",
            disabled=not ruido_activo,
            help="Solo disponible cuando hay un ruido seleccionado.",
        )

    # -- Humo y temperatura --
    if st.session_state["cat_humo_temp"]:
        st.divider()
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

    # -- Senales visuales --
    if st.session_state["cat_visuales"]:
        st.divider()
        st.subheader("Señales visuales")

        st.selectbox(
            "Luz de advertencia encendida",
            options=_keys(OPCIONES_LUCES),
            format_func=lambda v: OPCIONES_LUCES[v],
            index=_index_of(OPCIONES_LUCES, st.session_state["luces"]),
            key="luces",
        )

        st.checkbox(
            "Pérdida de potencia",
            value=st.session_state["perdida_potencia"],
            key="perdida_potencia",
        )

        st.selectbox(
            "Líquido en el piso",
            options=_keys(OPCIONES_LIQUIDO_PISO),
            format_func=lambda v: OPCIONES_LIQUIDO_PISO[v],
            index=_index_of(OPCIONES_LIQUIDO_PISO, st.session_state["liquido_piso"]),
            key="liquido_piso",
        )

    # -- Vibracion --
    if st.session_state["cat_vibracion"]:
        st.divider()
        st.subheader("Vibración")

        st.selectbox(
            "Dónde se siente la vibración",
            options=_keys(OPCIONES_DONDE_VIBRACION),
            format_func=lambda v: OPCIONES_DONDE_VIBRACION[v],
            index=_index_of(OPCIONES_DONDE_VIBRACION, st.session_state["donde_vibracion"]),
            key="donde_vibracion",
        )

    # -- Frenos --
    if st.session_state["cat_frenos"]:
        st.divider()
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
st.title("Diagnóstico del Vehículo")

resultado = st.session_state.get("resultado")

if resultado is None:
    # Estado inicial: instrucciones
    st.info(
        "Seleccioná los síntomas en el panel lateral y presioná **Diagnosticar**, "
        "o elegí un **caso demo** para ver un ejemplo.",
        icon="ℹ️",
    )
    st.stop()

# ---------------------------------------------------------------------------
# Mapa de urgencia
# ---------------------------------------------------------------------------
_URGENCIA_CONFIG = {
    "critica":  {"color": "#e74c3c", "label": "CRÍTICA",  "valor": 87, "texto": "Crítica"},
    "alta":     {"color": "#e67e22", "label": "ALTA",     "valor": 62, "texto": "Alta"},
    "moderada": {"color": "#f1c40f", "label": "MODERADA", "valor": 37, "texto": "Moderada"},
    "baja":     {"color": "#2ecc71", "label": "BAJA",     "valor": 12, "texto": "Baja"},
}

urgencia = resultado.get("urgencia", "baja")
cfg = _URGENCIA_CONFIG.get(urgencia, _URGENCIA_CONFIG["baja"])

# ---------------------------------------------------------------------------
# Fila 1: Badge + Gauge (compacta, sin scroll)
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
        height=200,
        margin={"t": 40, "b": 10, "l": 30, "r": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#333"},
    )
    st.plotly_chart(gauge_fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Fila 2: 4 cards en una sola fila
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Resultado del diagnóstico")

seguro_manejar = resultado.get("seguro_manejar", "si")
_SEGURO_ICONO = {
    "si": "✅",
    "con_precaucion": "⚠️",
    "no": "🚫",
}
_SEGURO_TEXTO = {
    "si": "Sí, puede manejar",
    "con_precaucion": "Con precaución",
    "no": "No debe manejar",
}
icono_seguro = _SEGURO_ICONO.get(seguro_manejar, "✅")
texto_seguro = _SEGURO_TEXTO.get(seguro_manejar, seguro_manejar)

sistema = resultado.get("sistema", "ninguno").capitalize()
diagnostico_texto = resultado.get("diagnostico", "")
accion_texto = resultado.get("accion", "")

col1, col2, col3, col4 = st.columns(4, gap="medium")

_card_style = f"""
    background-color: #f8f9fa;
    border-left: 5px solid {cfg['color']};
    border-radius: 8px;
    padding: 1rem 1.1rem;
    height: 100%;
"""

with col1:
    st.markdown(
        f"""
        <div style="{_card_style}">
            <p style="margin:0 0 0.3rem 0; font-size:0.75rem; color:#666; text-transform:uppercase; letter-spacing:0.05em;">Sistema afectado</p>
            <p style="margin:0; font-size:1.15rem; font-weight:700; color:#222;">{sistema}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div style="{_card_style}">
            <p style="margin:0 0 0.3rem 0; font-size:0.75rem; color:#666; text-transform:uppercase; letter-spacing:0.05em;">Diagnóstico</p>
            <p style="margin:0; font-size:1rem; font-weight:600; color:#222;">{diagnostico_texto}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div style="{_card_style}">
            <p style="margin:0 0 0.3rem 0; font-size:0.75rem; color:#666; text-transform:uppercase; letter-spacing:0.05em;">Seguro para manejar</p>
            <p style="margin:0; font-size:1.1rem; font-weight:700; color:#222;">{icono_seguro} {texto_seguro}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div style="{_card_style}">
            <p style="margin:0 0 0.3rem 0; font-size:0.75rem; color:#666; text-transform:uppercase; letter-spacing:0.05em;">Acción recomendada</p>
            <p style="margin:0; font-size:0.9rem; color:#333;">{accion_texto}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Fila 3: Tabla de reglas disparadas (sin columna N°)
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Reglas que se dispararon")

reglas = resultado.get("reglas_disparadas", [])

if reglas:
    from src.motor import _RESULTADOS
    _URGENCIA_LABEL = {
        "critica": "🔴 Crítica",
        "alta": "🟠 Alta",
        "moderada": "🟡 Moderada",
        "baja": "🟢 Baja",
    }
    df_reglas = pd.DataFrame({
        "Regla": reglas,
        "Sistema": [r.split(".")[0].capitalize() if "." in r else r for r in reglas],
        "Diagnóstico asociado": [
            _RESULTADOS.get(r, {}).get("diagnostico", r) for r in reglas
        ],
        "Urgencia": [
            _URGENCIA_LABEL.get(_RESULTADOS.get(r, {}).get("urgencia", "baja"), "🟢 Baja")
            for r in reglas
        ],
    })
    st.dataframe(df_reglas, use_container_width=True, hide_index=True)
else:
    st.info("No se dispararon reglas específicas — el vehículo está en condiciones normales.", icon="✅")
