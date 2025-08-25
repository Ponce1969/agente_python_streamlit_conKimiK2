# main.py
import logging
import os

import streamlit as st
from groq import Groq

from config import settings

# Módulos locales
from db import init_db, purge_old_messages
from styles import apply_global_styles, apply_theme
from ui_components import render_chat_interface, render_sidebar
from utils import SecurityUtils, rate_limiter

# ------------------------------------------------------------------
# 1. Configuración de la página
# ------------------------------------------------------------------
st.set_page_config(
    page_title="🤖 Agente Python 3.12+",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Logger del módulo
logger = logging.getLogger(__name__)



# ------------------------------------------------------------------
# 2. Estado de la sesión
# ------------------------------------------------------------------
def initialize_session_state() -> None:
    """Inicializa el estado de la sesión de Streamlit."""
    # Diccionario con los valores por defecto para el estado de la sesión
    defaults = {
        "client": lambda: Groq(api_key=settings.groq_api_key),
        "messages": [],
        "file_context": None,
        "file_context_full": None,
        "file_chunks": None,
        "file_chunk_index": 0,
        "chunk_by_tokens": False,
        "file_tokens_limit": int(os.getenv("FILE_CONTEXT_MAX_TOKENS", "2000")),
        "auto_advance_chunks": False,
        "theme": "light",
        "auth": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            # Si el valor es una función (para inicialización lazy), la llamamos
            st.session_state[key] = value() if callable(value) else value
    if "auth" not in st.session_state:
        st.session_state.auth = False


# ------------------------------------------------------------------
# 4. Autenticación
# ------------------------------------------------------------------
def handle_authentication() -> bool:
    """Maneja la autenticación con seguridad mejorada."""
    if st.session_state.get("auth", False):
        return True

    client_ip = st.session_state.get("client_ip", "unknown")

    if not rate_limiter.is_allowed(client_ip):
        st.error("Demasiados intentos fallidos. Por favor, espera 15 minutos.")
        return False

    st.title("🔐 Autenticación Requerida")
    st.warning("Introduce la contraseña maestra para continuar.")
    password = st.text_input("Contraseña", type="password", key="password_input")

    if st.button("Acceder", key="login_button"):
        if SecurityUtils.verify_password(password, settings.master_password_hash):
            st.session_state.auth = True
            st.rerun()
        else:
            rate_limiter.record_attempt(client_ip)
            attempts = len(rate_limiter.attempts.get(client_ip, []))
            attempts_left = rate_limiter.max_attempts - attempts
            st.error(f"Contraseña incorrecta. Quedan {attempts_left} intentos.")
    
    return False




# ------------------------------------------------------------------
# 7. Main
# ------------------------------------------------------------------
def main() -> None:
    """Función principal que orquesta la aplicación."""
    apply_global_styles()
    initialize_session_state()

    if handle_authentication():
        apply_theme()
        render_sidebar()
        render_chat_interface()


if __name__ == "__main__":
    init_db(settings.db_path)
    purge_old_messages(days=settings.purge_db_days)
    main()
