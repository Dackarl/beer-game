"""Interfaz Streamlit del Beer Game.

Los 4 jugadores entran a la MISMA url (cada quien desde su casa) y eligen su
rol. El estado de la partida es UNA sola instancia de GameState compartida
entre todas las sesiones (st.cache_resource), no una copia por navegador.
"""
import threading

import streamlit as st

from game.game_state import GameState, ROLES

TOTAL_RONDAS = 20


@st.cache_resource
def get_shared_state():
    return {
        "game": GameState(),
        "lock": threading.Lock(),
        "roles_ocupados": {},       # role -> True cuando alguien ya lo tomo
        "demanda_actual": None,     # dict role -> demanda de la ronda en curso
        "pedidos_ronda": {},        # dict role -> cantidad ya decidida esta ronda
        "terminado": False,
    }


shared = get_shared_state()
game: GameState = shared["game"]
lock: threading.Lock = shared["lock"]

st.set_page_config(page_title="Beer Game", page_icon="📦")
st.title("📦 Beer Game — cadena de suministro")

# --- Paso 1: elegir rol (una vez por sesion de navegador) ---
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.subheader("Elige tu rol")
    with lock:
        disponibles = [r for r in ROLES if r not in shared["roles_ocupados"]]

    if not disponibles:
        st.error("Los 4 roles ya están ocupados por otros jugadores.")
        st.stop()

    elegido = st.selectbox("Rol disponible", ["-- elige --"] + disponibles)
    if elegido != "-- elige --" and st.button("Confirmar rol"):
        with lock:
            if elegido in shared["roles_ocupados"]:
                st.warning("Ese rol ya lo tomó otro jugador, elige otro.")
            else:
                shared["roles_ocupados"][elegido] = True
                st.session_state.role = elegido
                st.rerun()
    st.stop()

role = st.session_state.role
st.subheader(f"Tu rol: {role}")

# --- Paso 2: si el juego ya termino, mostrar resultados finales ---
if shared["terminado"]:
    st.success(f"Partida terminada ({TOTAL_RONDAS} rondas).")
    st.metric("Costo total del juego", f"{game.total_cost():.1f}")
    st.write("Costo acumulado por jugador:")
    for r in ROLES:
        st.write(f"- {r}: {game.players[r].total_cost:.1f}")
    st.stop()

# --- Paso 3: asegurar que la ronda actual tenga demanda calculada ---
with lock:
    if shared["demanda_actual"] is None:
        shared["demanda_actual"] = game.start_round()
        shared["pedidos_ronda"] = {}
    demanda = shared["demanda_actual"]
    ronda_actual = game.round_number

jugador = game.players[role]

col1, col2, col3 = st.columns(3)
col1.metric("Ronda", f"{ronda_actual} / {TOTAL_RONDAS}")
col2.metric("Tu inventario", jugador.inventory)
col3.metric("Tu backlog", jugador.backlog)

st.info(f"Este turno te pidieron **{demanda[role]}** unidades.")

# --- Paso 4: decision de pedido ---
ya_decidido = role in shared["pedidos_ronda"]

if ya_decidido:
    st.success(f"Ya enviaste tu pedido: {shared['pedidos_ronda'][role]} unidades. Esperando a los demás...")
else:
    cantidad = st.number_input(
        "¿Cuánto quieres pedir a tu proveedor?",
        min_value=0, step=1, value=int(demanda[role]),
    )
    if st.button("Confirmar pedido"):
        with lock:
            shared["pedidos_ronda"][role] = int(cantidad)
        st.rerun()

st.divider()
st.write("**Estado de la ronda:**")
for r in ROLES:
    listo = "✅" if r in shared["pedidos_ronda"] else "⏳"
    st.write(f"{listo} {r}")

if st.button("🔄 Actualizar"):
    st.rerun()

# --- Paso 5: si ya estan los 4 pedidos, cerrar la ronda ---
with lock:
    if len(shared["pedidos_ronda"]) == len(ROLES) and shared["demanda_actual"] is not None:
        game.complete_round(shared["pedidos_ronda"])
        shared["demanda_actual"] = None
        shared["pedidos_ronda"] = {}
        if game.round_number >= TOTAL_RONDAS:
            shared["terminado"] = True
        st.rerun()
