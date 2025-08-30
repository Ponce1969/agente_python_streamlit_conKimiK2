# config.py
"""
Módulo de configuración centralizado para la aplicación.

Utiliza pydantic-settings para cargar y validar la configuración desde
variables de entorno y/o un archivo .env.
"""

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """
    Define las variables de configuración de la aplicación.
    """

    # Configuración para pydantic-settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- API Keys y Secretos ---
    groq_api_key: str = Field(..., description="API key para Groq.")
    master_password_hash: str = Field(
        ..., description="Hash de la contraseña maestra."
    )

    # --- Modelo LLM ---
    groq_model_name: str = Field(
        "moonshotai/kimi-k2-instruct",
        description="Nombre del modelo de Groq a utilizar.",
    )

    # --- Configuración del Chat ---
    conversation_window_messages: int = Field(
        20, description="Número de mensajes a mantener en el historial de contexto."
    )
    display_window_messages: int = Field(
        12, description="Número de mensajes a mostrar en la interfaz de chat."
    )
    messages_max_chars: int = Field(
        12000,
        description="Límite máximo de caracteres para el historial enviado a la API.",
    )
    file_context_max_chars: int = Field(
        8000,
        description="Límite máximo de caracteres para el contexto de un archivo.",
    )
    file_context_max_tokens: int = Field(
        2000, description="Límite máximo de tokens para el contexto de un archivo."
    )

    # --- Base de Datos ---
    db_path: str = Field(
        "data/chat_history.db",
        description="Ruta al archivo de la base de datos SQLite.",
    )
    purge_db_days: int = Field(
        30, description="Días de antigüedad para purgar mensajes de la base de datos."
    )

    


# Instancia única para ser importada en otros módulos
settings = Settings()

