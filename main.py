# main.py
import logging

import streamlit as st
from groq import Groq

from config import settings

# ------------------------------------------------------------------
# 0. Configuración del Logging
# ------------------------------------------------------------------
def setup_logging():
    """Configura el logging para toda la aplicación."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# Módulos locales
from db import init_db, purge_old_messages, purge_old_login_attempts
from styles import load_css
from llm_handler import get_groq_client
from ui_components import render_chat_interface, render_sidebar
from utils import SecurityUtils, get_client_ip, rate_limiter

# ------------------------------------------------------------------
# 1. Configuración de la página
# ------------------------------------------------------------------
# Logger del módulo
logger = logging.getLogger(__name__)

from streamlit.errors import StreamlitAPIException

try:
    st.set_page_config(
        page_title="🤖 Agente Python 3.12+",
        page_icon="🐍",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except StreamlitAPIException as e:
    logger.error(f"Error al configurar la página de Streamlit: {e}")
    # Continuar es seguro, pero la configuración de la página puede no aplicarse.



# ------------------------------------------------------------------
# 2. Estado de la sesión
# ------------------------------------------------------------------
def initialize_session_state() -> None:
    """Inicializa el estado de la sesión de Streamlit."""
    if "client_ip" not in st.session_state:
        st.session_state.client_ip = get_client_ip()

    defaults = {
        "auth": False,
        "messages": [],
        "thread_id": None,
        "assistant_id": None,
        "run_id": None,
        "file_tokens_limit": settings.file_context_max_tokens,
        "file_context": None,
        "file_context_full": None,
        "file_chunks": None,
        "file_chunk_index": 0,
        "chunk_by_tokens": False,
        "auto_advance_chunks": False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Inicializar cliente de Groq con manejo de errores
    if "client" not in st.session_state:
        try:
            st.session_state.client = get_groq_client()
        except Exception as e:
            st.error(f"Error al inicializar el cliente de la API: {e}")
            st.session_state.client = None


# ------------------------------------------------------------------
# 4. Autenticación
# ------------------------------------------------------------------
def handle_authentication() -> bool:
    """Maneja la autenticación del usuario."""
    client_ip = st.session_state.client_ip

    if st.session_state.get("auth", False):
        return True

    if not rate_limiter.is_allowed(client_ip):
        st.error("Demasiados intentos de inicio de sesión. Inténtalo de nuevo más tarde.")
        return False

    st.warning("Por favor, introduce la contraseña para continuar.")
    password = st.text_input("Contraseña:", type="password")

    if st.button("Iniciar sesión"):
        # Verificar la contraseña solo si se ingresa algo
        if password and SecurityUtils.verify_password(password, settings.master_password_hash):
            st.session_state.auth = True
            st.rerun()
        else:
            st.session_state.auth = False
            rate_limiter.record_attempt(client_ip)
            st.error("Contraseña incorrecta.")
            # No hacer rerun aquí para que el mensaje de error permanezca visible

    return st.session_state.get("auth", False)


# ------------------------------------------------------------------
# 7. Main
# ------------------------------------------------------------------
def main() -> None:
    """Función principal que orquesta la aplicación."""
    initialize_session_state()
    load_css()

    # La autenticación es bloqueante. Si no es exitosa, se detiene la ejecución.
    if not handle_authentication():
        st.stop()

    # El resto de la app solo se renderiza si la autenticación es exitosa
    render_sidebar()
    render_chat_interface()


if __name__ == "__main__":
    setup_logging()
    try:
        init_db(settings.db_path)
        # Purga de datos de mantenimiento
        purge_old_messages(days=settings.purge_db_days)
        purge_old_login_attempts(days=7)  # Limpia logs de intentos de login antiguos
    except Exception as e:
        logger.critical(f"No se pudo inicializar o purgar la base de datos: {e}")
        # Dependiendo de la criticidad, podrías querer salir o mostrar un error
        st.error(f"Error crítico de la base de datos: {e}. La aplicación puede no funcionar.")

    main()
