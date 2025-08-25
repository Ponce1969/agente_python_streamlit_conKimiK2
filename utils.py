"""
Utilidades de seguridad y validación para el agente Python.
"""

import logging
import secrets
from functools import lru_cache

import bcrypt

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
        return hashed.decode("utf-8")  # type: ignore

    @staticmethod
    def is_password_valid(password: str, hashed_password: str) -> bool:
        """Verifica si una contraseña coincide con su hash."""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))  # type: ignore
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
    """Limitador de intentos para prevenir ataques de fuerza bruta."""

    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self.attempts: dict[str, list[float]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """Verifica si un intento está permitido."""
        import time

        current_time = time.time()
        window_start = current_time - (self.window_minutes * 60)

        # Limpiar intentos antiguos
        self.attempts[identifier] = [
            timestamp for timestamp in self.attempts.get(identifier, []) if timestamp > window_start
        ]

        return len(self.attempts.get(identifier, [])) < self.max_attempts

    def record_attempt(self, identifier: str) -> None:
        """Registra un intento de login."""
        import time

        if identifier not in self.attempts:
            self.attempts[identifier] = []
        self.attempts[identifier].append(time.time())


# Instancia global del limitador
rate_limiter = RateLimiter()


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
