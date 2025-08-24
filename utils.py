"""
Utilidades de seguridad y validación para el agente Python.
"""

import hashlib
import logging
import os
import secrets
from functools import lru_cache
from typing import Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityUtils:
    """Clase para manejar funciones de seguridad."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Genera hash seguro de contraseña."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verifica contraseña contra hash."""
        return SecurityUtils.hash_password(password) == hashed

    @staticmethod
    def generate_session_token() -> str:
        """Genera token de sesión seguro."""
        return secrets.token_urlsafe(32)


class EnvValidator:
    """Validador de variables de entorno."""

    REQUIRED_VARS = ["GROQ_API_KEY", "MASTER_PASSWORD"]

    @classmethod
    def validate_env(cls) -> dict[str, Any]:
        """Valida que todas las variables requeridas existan."""
        missing = []
        config = {}

        for var in cls.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                missing.append(var)
            else:
                config[var] = value

        if missing:
            raise ValueError(f"Variables de entorno faltantes: {', '.join(missing)}")

        return config

    @classmethod
    def get_secure_config(cls) -> dict[str, Any]:
        """Obtiene configuración validada y segura."""
        config = cls.validate_env()

        # Hash de contraseña para almacenamiento seguro
        config["MASTER_PASSWORD_HASH"] = SecurityUtils.hash_password(config["MASTER_PASSWORD"])
        del config["MASTER_PASSWORD"]  # No almacenar en texto plano

        return config


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
