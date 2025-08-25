# llm_handler.py

"""
Módulo para manejar la interacción con el modelo de lenguaje (Groq API).
"""

import logging
from collections.abc import Generator
from io import StringIO
from typing import Any

from groq import APIStatusError, Groq
from groq.types.chat.chat_completion import ChatCompletionMessage

from config import settings

# Configuración del logger
logger = logging.getLogger(__name__)


def get_groq_client(api_key: str) -> Groq:
    """Inicializa y devuelve un cliente de Groq."""
    return Groq(api_key=api_key)

def stream_handler(stream: Any) -> Generator[str, None, str]:
    """Procesa la respuesta en streaming de la API."""
    buffer = StringIO()
    try:
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                buffer.write(content)
                yield content
    except Exception as e:
        logger.error(f"Error en stream_handler: {e}")
        yield "Error procesando la respuesta."
    return buffer.getvalue()

def build_messages_with_limit(
    messages: list[dict[str, str]], max_chars: int
) -> list[dict[str, str]]:
    """Construye la lista de mensajes sin exceder un límite de caracteres."""
    if not messages:
        return messages
    total = 0
    system_msg = messages[0]
    tail = messages[1:]
    selected: list[dict[str, str]] = []
    for m in reversed(tail):
        c = len(m.get("content", ""))
        if total + c > max_chars:
            break
        selected.append(m)
        total += c
    return [system_msg] + list(reversed(selected))

def get_groq_response(client: Groq, messages: list[dict[str, str]]) -> Generator[str, None, str]:
    """Obtiene una respuesta en streaming de la API de Groq."""
    try:
        messages_to_send = build_messages_with_limit(
            messages, settings.messages_max_chars
        )

        stream = client.chat.completions.create(
            model=settings.groq_model_name,
            messages=messages_to_send,  # type: ignore
            temperature=0.3,
            stream=True,
            max_tokens=4096,
        )
        final_response = yield from stream_handler(stream)
        return final_response

    except APIStatusError as e:
        logger.error(f"Error de la API de Groq: {e.message}")
        yield f"Error de la API de Groq: {e.message}"
        return ""
    except Exception as e:
        logger.error(f"Error inesperado al llamar a la API: {e}")
        yield f"Error inesperado: {e}"
        return ""