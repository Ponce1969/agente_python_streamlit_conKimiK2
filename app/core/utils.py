"""
Utilidades de seguridad y validación para el agente Python.
"""

import logging
import secrets
from functools import lru_cache

import bcrypt
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from app.db.persistence import count_recent_login_attempts, record_login_attempt

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityUtils:
    """Clase para manejar funciones de seguridad."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Genera un hash de la contraseña usando bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def is_password_valid(password: str, hashed_password: str) -> bool:
        """Verifica si una contraseña coincide con su hash."""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False

    @staticmethod
    @lru_cache(maxsize=128)
    def verify_password(password: str, hashed_password: str) -> bool:
        """Wrapper con cache para verificar contraseñas."""
        return SecurityUtils.is_password_valid(password, hashed_password)

    @staticmethod
    def generate_session_token() -> str:
        """Genera token de sesión seguro."""
        return secrets.token_urlsafe(32)


class RateLimiter:
    """Limitador de intentos persistente usando la base de datos."""

    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes

    def is_allowed(self, identifier: str) -> bool:
        """Verifica si un intento está permitido consultando la base de datos."""
        if not identifier or identifier == "unknown":
            return True  # No limitar si no hay identificador

        recent_attempts = count_recent_login_attempts(identifier, self.window_minutes)
        return recent_attempts < self.max_attempts

    def record_attempt(self, identifier: str) -> None:
        """Registra un intento de login en la base de datos."""
        if not identifier or identifier == "unknown":
            return  # No registrar si no hay identificador

        record_login_attempt(identifier)


# Instancia global del limitador
rate_limiter = RateLimiter()


def get_client_ip() -> str:
    """Obtiene la IP del cliente de la conexión actual."""
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return "unknown"

        # Devolvemos el ID de sesión como un identificador único.
        # Acceder a la IP real del cliente en Streamlit es complejo y usa APIs internas inestables.
        return str(ctx.session_id)

    except Exception as e:
        logger.warning(f"No se pudo obtener la IP del cliente: {e}")

    # Fallback si no se puede obtener la IP
    return "unknown"


@lru_cache(maxsize=128)
def validate_file_size(file_size: int, max_size_mb: int = 5) -> bool:
    """Valida tamaño de archivo con caché."""
    max_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_bytes


def chunk_text(text: str, chunk_size: int) -> list[str]:
    """Divide texto en trozos de tamaño máximo chunk_size.

    Se intenta cortar en saltos de línea si es posible para mejorar legibilidad.
    """
    if chunk_size <= 0 or not text:
        return [text] if text else []
    chunks: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        end = min(i + chunk_size, n)
        # buscar el último salto de línea antes de end para no cortar palabras/código
        newline_pos = text.rfind("\n", i, end)
        if newline_pos != -1 and newline_pos > i + int(0.6 * chunk_size):
            end = newline_pos
        chunks.append(text[i:end])
        i = end
    return chunks

def estimate_tokens(text: str) -> int:
    """Estimación simple de tokens (~4 chars/token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)
