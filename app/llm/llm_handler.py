# llm_handler.py

"""
Módulo para manejar la interacción con el modelo de lenguaje (Groq API).
"""

import logging
from collections.abc import Generator, Iterator

import streamlit as st
from groq import APIStatusError, Groq
from groq.types.chat import ChatCompletionChunk, ChatCompletionMessageParam

from app.config import settings

# Configuración del logger
logger = logging.getLogger(__name__)


@st.cache_resource
def get_groq_client() -> Groq:
    """
    Inicializa y devuelve un cliente de Groq cacheado para toda la app.
    
    Raises:
        ValueError: Si la API key de Groq no está configurada en los settings.
    """
    if not settings.groq_api_key:
        raise ValueError("La API key de Groq no está configurada.")
    return Groq(api_key=settings.groq_api_key)


def build_messages_with_limit(
    messages: list[dict[str, str]], max_chars: int
) -> list[ChatCompletionMessageParam]:
    """
    Construye la lista de mensajes para la API sin exceder un límite de caracteres.
    
    Conserva el primer mensaje (sistema) y trunca los más antiguos del historial.
    """
    if not messages:
        return []

    system_message = messages[0]
    history = messages[1:]
    
    char_count = 0
    selected_history: list[dict[str, str]] = []

    for message in reversed(history):
        message_len = len(message.get("content", ""))
        if char_count + message_len > max_chars:
            break
        selected_history.append(message)
        char_count += message_len
    
    # Revertir para mantener el orden cronológico
    final_history = list(reversed(selected_history))
    
    # Convertir a ChatCompletionMessageParam para compatibilidad con la API
    # Esta conversión asume que los roles y contenidos son correctos.
    final_messages: list[ChatCompletionMessageParam] = [
        {"role": m["role"], "content": m["content"]} # type: ignore
        for m in [system_message] + final_history
    ]
    
    return final_messages


def get_groq_response(
    client: Groq, messages: list[dict[str, str]]
) -> Generator[str, None, None]:
    """
    Obtiene una respuesta en streaming de la API de Groq.

    Args:
        client: El cliente de la API de Groq.
        messages: La lista de mensajes de la conversación.

    Yields:
        str: Fragmentos de la respuesta del modelo.
    """
    try:
        messages_to_send = build_messages_with_limit(
            messages, settings.messages_max_chars
        )

        stream: Iterator[ChatCompletionChunk] = client.chat.completions.create(
            model=settings.groq_model_name,
            messages=messages_to_send,
            temperature=settings.temperature,
            stream=True,
            max_tokens=settings.max_tokens,
        )

        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    except APIStatusError as e:
        error_message = f"Error de la API de Groq: {e.message}"
        logger.error(error_message)
        yield error_message
    except Exception as e:
        error_message = f"Error inesperado al llamar a la API: {e}"
        logger.error(error_message)
        yield error_message