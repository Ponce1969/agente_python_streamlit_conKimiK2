# main.py
import logging
import os
from collections.abc import Generator
from io import StringIO
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from groq import APIStatusError, Groq

# Módulos locales
from db import (
    delete_all_messages,
    init_db,
    load_all_messages,
    load_messages_between,
    load_messages,
    purge_old_messages,
    save_message,
)
from export import export_md, export_pdf
from file_handler import process_uploaded_file
from utils import EnvValidator, SecurityUtils, rate_limiter

# ------------------------------------------------------------------
# 1. Configuración inicial y constantes
# ------------------------------------------------------------------
load_dotenv()

# Configuración validada de entorno y constantes seguras
CONFIG: dict[str, Any] = EnvValidator.get_secure_config()
GROQ_API_KEY: str = CONFIG["GROQ_API_KEY"]
MASTER_PASSWORD_HASH: str = CONFIG["MASTER_PASSWORD_HASH"]

# Logger del módulo
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="🤖 Agente Python 3.12+",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modelo por defecto
MODEL: str = "moonshotai/kimi-k2-instruct"

BASE_SYSTEM_PROMPT: str = (
    "Eres un asistente experto en Python 3.12+, especializado en desarrollo backend y "
    "arquitectura de software moderna. Tu propósito es proporcionar respuestas claras, "
    "concisas y profesionales. Siempre debes seguir estas directrices:\n\n"
    "1.  **Formato Markdown**: Tus respuestas DEBEN estar en formato Markdown.\n"
    "2.  **Código Funcional**: Si incluyes código, debe ser completo, funcional y "
    "listo para usar.\n"
    "3.  **Tipado Estricto**: TODO el código Python debe usar tipado estricto ("
    "`str`, `int`, `List`, etc.).\n"
    "4.  **Estándares de Calidad**: El código debe cumplir con los estándares de "
    "`ruff` y `mypy`.\n"
    "5.  **Contexto de Experto**: Demuestra tu conocimiento en:\n"
    "    -   **Arquitectura**: Clean Architecture, Arquitectura Hexagonal, Patrones "
    "de Diseño, SOLID.\n"
    "    -   **Herramientas**: `uv`, `pyproject.toml`, `ruff`, `mypy`.\n"
    "    -   **Frameworks**: FastAPI, Pydantic.\n"
    "    -   **Bases de Datos**: SQLAlchemy 2.0 (con `asyncpg`), Alembic.\n"
    "    -   **Contenedores**: Docker, Docker Compose.\n\n"
    "**Sé directo y ve al grano. La calidad y la precisión son tu máxima prioridad.**"
)


# ------------------------------------------------------------------
# 2. Estilos CSS
# ------------------------------------------------------------------
def apply_custom_styles() -> None:
    theme = st.session_state.get("theme", "light")
    if theme not in {"light", "dark"}:
        theme = "light"

    css_light = """
    <style>
        /* Fondo general suave */
        body, .stApp { background-color: #f5f7fb !important; }

        /* Burbujas de chat: usuario */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background-color: #ffffff;
            border: 1px solid #e6e8ec;
            border-radius: 12px;
            padding: 14px 16px;
            margin: 8px 40px 8px 0;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
        }

        /* Burbujas de chat: asistente */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            background-color: #f7fbff;
            border: 1px solid #d6e9ff;
            border-radius: 12px;
            padding: 14px 16px;
            margin: 8px 0 8px 40px;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
        }

        /* Código inline estilo GitHub */
        [data-testid="stChatMessage"] code {
            color: #24292e;
            background-color: #f6f8fa;
            padding: 2px 6px;
            border-radius: 6px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            border: 1px solid #eaeef2;
        }

        /* Bloques de código claros y legibles */
        [data-testid="stChatMessage"] pre {
            background-color: #f6f8fa;
            color: #24292e;
            padding: 14px 16px;
            border-radius: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
            border: 1px solid #eaeef2;
        }

        /* Botones primarios */
        .stDownloadButton button, .stButton button {
            background-color: #2563eb;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 14px;
            transition: background-color 0.2s ease;
            box-shadow: 0 1px 2px rgba(16,24,40,0.06);
        }
        .stDownloadButton button:hover, .stButton button:hover { background-color: #1d4ed8; }
    </style>
    """

    css_dark = """
    <style>
        body, .stApp { background-color: #0f172a !important; color: #e2e8f0 !important; }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 14px 16px;
            margin: 8px 40px 8px 0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            background-color: #0b1220;
            border: 1px solid #1d2a44;
            border-radius: 12px;
            padding: 14px 16px;
            margin: 8px 0 8px 40px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }

        [data-testid="stChatMessage"] code {
            color: #e2e8f0;
            background-color: #111827;
            padding: 2px 6px;
            border-radius: 6px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            border: 1px solid #1f2937;
        }

        [data-testid="stChatMessage"] pre {
            background-color: #0b1220;
            color: #e2e8f0;
            padding: 14px 16px;
            border-radius: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
            border: 1px solid #1d2a44;
        }

        .stDownloadButton button, .stButton button {
            background-color: #3b82f6;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 14px;
            transition: background-color 0.2s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.35);
        }
        .stDownloadButton button:hover, .stButton button:hover { background-color: #2563eb; }
    </style>
    """

    st.markdown(css_dark if theme == "dark" else css_light, unsafe_allow_html=True)


# ------------------------------------------------------------------
# 2.1 Utilidades
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# 3. Estado de sesión
# ------------------------------------------------------------------
def initialize_session_state() -> None:
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "file_context" not in st.session_state:
        st.session_state.file_context = None
    if "file_context_full" not in st.session_state:
        st.session_state.file_context_full = None
    if "file_chunks" not in st.session_state:
        st.session_state.file_chunks: list[str] | None = None
    if "file_chunk_index" not in st.session_state:
        st.session_state.file_chunk_index = 0
    if "chunk_by_tokens" not in st.session_state:
        st.session_state.chunk_by_tokens = False
    if "file_tokens_limit" not in st.session_state:
        st.session_state.file_tokens_limit = int(os.getenv("FILE_CONTEXT_MAX_TOKENS", "2000"))
    if "auto_advance_chunks" not in st.session_state:
        st.session_state.auto_advance_chunks = False
    if "client" not in st.session_state:
        st.session_state.client = Groq(api_key=GROQ_API_KEY)
    if "theme" not in st.session_state:
        st.session_state.theme = "light"


# ------------------------------------------------------------------
# 4. Autenticación
# ------------------------------------------------------------------
def handle_authentication() -> bool:
    """Maneja la autenticación con seguridad mejorada."""
    if st.session_state.auth:
        return True

    # Obtener IP del cliente para rate limiting
    client_ip = st.session_state.get("client_ip", "unknown")

    if not rate_limiter.is_allowed(client_ip):
        st.error("Demasiados intentos fallidos. Por favor, espera 15 minutos.")
        st.stop()
        return False

    pwd_container = st.empty()
    with pwd_container.container():
        st.title("🔐 Autenticación Requerida")
        st.warning("Introduce la contraseña maestra para continuar.")
        pwd = st.text_input("Contraseña", type="password", key="pwd_input")

        if st.button("Acceder", key="login_button"):
            if SecurityUtils.verify_password(pwd, MASTER_PASSWORD_HASH):
                st.session_state.auth = True
                pwd_container.empty()
                st.rerun()
            else:
                rate_limiter.record_attempt(client_ip)
                remaining_attempts = max(0, 5 - len(rate_limiter.attempts.get(client_ip, [])))
                st.error(f"Contraseña incorrecta. Intentos restantes: {remaining_attempts}")

    st.stop()
    return False


# ------------------------------------------------------------------
# 5. Sidebar
# ------------------------------------------------------------------
def render_sidebar() -> None:
    with st.sidebar:
        st.title("⚙️ Opciones")
        st.divider()

        # Tema (binding directo a session_state para cambio inmediato con un solo click)
        st.subheader("Tema")
        # Asegurar default
        if "theme" not in st.session_state:
            st.session_state.theme = "light"
        st.radio(
            "Selecciona un tema",
            options=["light", "dark"],
            index=0 if st.session_state.theme == "light" else 1,
            format_func=lambda v: "Claro" if v == "light" else "Oscuro",
            horizontal=True,
            key="theme",
        )

        # Carga de archivos
        st.subheader("Análisis de Archivos")
        uploaded_file = st.file_uploader(
            "Sube un archivo para dar contexto",
            type=["py", "txt", "md", "csv", "pdf"],
            key="file_uploader",
            help="El contenido se añadirá al prompt del sistema.",
        )
        if uploaded_file and st.button(
            "Analizar Archivo", key="analyze_button", use_container_width=True
        ):
            with st.spinner("Analizando archivo..."):
                result: tuple[str | None, str | None] | None = process_uploaded_file(
                    uploaded_file
                )
                if result:
                    content, error = result
                    if error:
                        st.error(error)
                    elif content is not None:
                        st.session_state.file_context_full = content
                        st.session_state.file_chunks = None
                        st.session_state.file_chunk_index = 0
                        # por defecto, asignamos todo el contenido (puede que luego se fragmente en la UI)
                        st.session_state.file_context = content
                        st.success(f"✅ Archivo '{uploaded_file.name}' analizado.")

        st.divider()

        # Exportación
        st.subheader("Exportar Chat")
        # Últimos N
        n = st.number_input(
            "Últimos N mensajes",
            min_value=5,
            max_value=2000,
            value=50,
            step=5,
            help="Exporta solo la cola reciente desde la base de datos",
        )
        last_n_messages = load_messages(limit=int(n))
        all_messages = load_all_messages()

        # Rango por fechas
        st.caption("Exportar por rango de fechas")
        c_from, c_to = st.columns(2)
        with c_from:
            start_date = st.date_input("Desde", key="export_from_date")
            start_time = st.time_input("Hora desde", key="export_from_time")
        with c_to:
            end_date = st.date_input("Hasta", key="export_to_date")
            end_time = st.time_input("Hora hasta", key="export_to_time")

        from datetime import datetime
        try:
            start_dt = datetime.combine(start_date, start_time)
            end_dt = datetime.combine(end_date, end_time)
        except Exception:
            start_dt = end_dt = None

        range_messages: list[dict[str, str]] = []
        if start_dt and end_dt and start_dt <= end_dt:
            range_messages = load_messages_between(start_dt, end_dt)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                label="📥 Últimos N (MD)",
                data=export_md(last_n_messages, quiet=True),
                file_name="historial_ultimos.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.download_button(
                label="📄 Últimos N (PDF)",
                data=export_pdf(last_n_messages, quiet=True),
                file_name="historial_ultimos.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                label="📥 Todo (MD)",
                data=export_md(all_messages, quiet=True),
                file_name="historial_completo.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.download_button(
                label="📄 Todo (PDF)",
                data=export_pdf(all_messages, quiet=True),
                file_name="historial_completo.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        # Botones de rango por fechas
        st.markdown("\n")
        c3, c4 = st.columns(2)
        with c3:
            st.download_button(
                label="🗓️ Rango (MD)",
                data=export_md(range_messages, quiet=True) if range_messages else b"",
                file_name="historial_rango.md",
                mime="text/markdown",
                disabled=not bool(range_messages),
                use_container_width=True,
            )
        with c4:
            st.download_button(
                label="🗓️ Rango (PDF)",
                data=export_pdf(range_messages, quiet=True) if range_messages else b"",
                file_name="historial_rango.pdf",
                mime="application/pdf",
                disabled=not bool(range_messages),
                use_container_width=True,
            )

        st.divider()

        # Mantenimiento de base de datos / contexto
        st.subheader("Mantenimiento")
        # Si el archivo excede el límite de contexto, permitir selección de trozos
        max_ctx_chars = int(os.getenv("FILE_CONTEXT_MAX_CHARS", "8000"))
        if st.session_state.file_context_full:
            # Opciones de corte
            with st.expander("Ajustes de contexto del archivo", expanded=False):
                st.checkbox(
                    "Cortar por tokens (estimación)",
                    key="chunk_by_tokens",
                    help="En lugar de caracteres, usa un límite de tokens estimados (~4 chars/token).",
                )
                if st.session_state.chunk_by_tokens:
                    st.number_input(
                        "Límite de tokens por parte",
                        min_value=500,
                        max_value=8000,
                        value=int(st.session_state.file_tokens_limit),
                        step=100,
                        key="file_tokens_limit",
                        help="El tamaño real en caracteres será ~ tokens * 4.",
                    )
                st.checkbox(
                    "Avanzar automáticamente a la siguiente parte tras enviar",
                    key="auto_advance_chunks",
                )

            # Determinar tamaño de parte efectivo
            if st.session_state.chunk_by_tokens:
                chunk_chars = int(int(st.session_state.file_tokens_limit) * 4)
            else:
                chunk_chars = max_ctx_chars

            needs_chunking = len(st.session_state.file_context_full) > chunk_chars
            if needs_chunking:
                if st.session_state.file_chunks is None or (
                    st.session_state.file_chunks and len(st.session_state.file_chunks[0]) > chunk_chars
                ):
                    # Generar o regenerar chunks con nuevo tamaño
                    st.session_state.file_chunks = chunk_text(
                        st.session_state.file_context_full, chunk_chars
                    )
                    st.session_state.file_chunk_index = 0

                total_chunks = len(st.session_state.file_chunks)
                current_idx = st.session_state.file_chunk_index

                st.caption("El archivo es grande. Selecciona el tramo a incluir en el prompt:")
                cnav1, cnav2, cnav3 = st.columns([1, 2, 1])
                with cnav1:
                    if st.button("⟵ Anterior", disabled=current_idx <= 0):
                        st.session_state.file_chunk_index = max(0, current_idx - 1)
                with cnav2:
                    st.session_state.file_chunk_index = st.number_input(
                        "Parte",
                        min_value=1,
                        max_value=total_chunks,
                        value=st.session_state.file_chunk_index + 1,
                        step=1,
                    ) - 1
                with cnav3:
                    if st.button("Siguiente ⟶", disabled=current_idx >= total_chunks - 1):
                        st.session_state.file_chunk_index = min(total_chunks - 1, current_idx + 1)

                # Sincronizar el contexto visible
                current_idx = st.session_state.file_chunk_index
                current_part = st.session_state.file_chunks[current_idx]
                st.session_state.file_context = current_part
                st.info(
                    f"Parte {current_idx + 1}/{total_chunks} · {len(current_part)} chars (~{estimate_tokens(current_part)} tokens)"
                )
            else:
                # No requiere chunking
                st.session_state.file_context = st.session_state.file_context_full
        if st.button("🗑️ Borrar historial (SQLite)", use_container_width=True):
            try:
                delete_all_messages()
            except Exception as e:
                st.error(f"No se pudo borrar el historial: {e}")
            else:
                # Limpiar contexto en memoria y confirmar
                st.session_state.messages = []
                st.session_state.file_context = None
                st.success("Historial borrado correctamente.")
                # Importante: hacer rerun fuera del try/except para no capturar la excepción interna de rerun
                st.rerun()


# ------------------------------------------------------------------
# 6. Chat
# ------------------------------------------------------------------
def stream_handler(stream: Any) -> Generator[str, None, str]:
    """Procesa la respuesta en streaming de la API.

    Args:
        stream: Stream de respuesta de Groq API

    Yields:
        str: Fragmentos de contenido

    Returns:
        str: Contenido completo concatenado
    """
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


def render_chat_interface() -> None:  # noqa: C901
    st.title("🤖 Agente Experto en Python 3.12+")

    try:
        window_size = int(os.getenv("CONVERSATION_WINDOW_MESSAGES", "20"))
    except (ValueError, TypeError):
        window_size = 20
    # Límite de mensajes SOLO para visualizar en UI (no afecta al contexto enviado a la API)
    try:
        display_window = int(os.getenv("DISPLAY_WINDOW_MESSAGES", str(min(12, window_size))))
    except (ValueError, TypeError):
        display_window = min(12, window_size)

    system_prompt = BASE_SYSTEM_PROMPT
    if st.session_state.file_context:
        # Integrar directamente el tramo seleccionado del archivo sin truncar aquí.
        file_ctx = st.session_state.file_context
        system_prompt += (
            f"\n\n--- INICIO DEL CONTEXTO DEL ARCHIVO ADJUNTO ---\n"
            f"{file_ctx}\n"
            f"--- FIN DEL CONTEXTO ---"
        )

    if not st.session_state.messages:
        st.session_state.messages = [
            {"role": "system", "content": system_prompt},
            *load_messages(limit=window_size),
        ]
    st.session_state.messages[0] = {"role": "system", "content": system_prompt}

    # Renderizar solo los últimos 'display_window' mensajes (sin incluir el system)
    to_render = st.session_state.messages[1:]
    if len(to_render) > display_window:
        to_render = to_render[-display_window:]
    for msg in to_render:
        avatar = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Escribe tu pregunta sobre Python aquí..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_message("user", prompt)

        # Recortar ventana
        history = st.session_state.messages[1:]
        if len(history) > window_size:
            st.session_state.messages = [st.session_state.messages[0]] + history[-window_size:]

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤖 El agente está pensando..."):
                try:
                    # Limitar tamaño total del historial enviado a la API para evitar HTTP 413
                    def build_messages_with_limit(
                        messages: list[dict[str, str]], max_chars: int
                    ) -> list[dict[str, str]]:
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

                    max_hist_chars = int(os.getenv("MESSAGES_MAX_CHARS", "12000"))
                    messages_to_send = build_messages_with_limit(
                        st.session_state.messages, max_hist_chars
                    )

                    stream = st.session_state.client.chat.completions.create(
                        model=MODEL,
                        messages=messages_to_send,
                        temperature=0.3,
                        stream=True,
                        max_tokens=4096,
                    )
                    full_response: str = "".join(stream_handler(stream))
                    st.markdown(full_response, unsafe_allow_html=True)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )
                    save_message("assistant", full_response)

                except APIStatusError as e:
                    st.error(f"Error de la API de Groq: {e.message}")
                else:
                    # Auto avanzar de parte, si corresponde
                    if (
                        st.session_state.get("auto_advance_chunks")
                        and st.session_state.get("file_chunks")
                    ):
                        total_chunks = len(st.session_state.file_chunks)
                        idx = st.session_state.file_chunk_index
                        if idx < total_chunks - 1:
                            st.session_state.file_chunk_index = idx + 1
                            st.session_state.file_context = st.session_state.file_chunks[
                                st.session_state.file_chunk_index
                            ]


# ------------------------------------------------------------------
# 7. Main
# ------------------------------------------------------------------
def main() -> None:
    initialize_session_state()
    if not handle_authentication():
        return
    # Primero leer preferencia desde el sidebar
    render_sidebar()
    # Luego aplicar estilos según la preferencia ya elegida en esta misma ejecución
    apply_custom_styles()
    render_chat_interface()


if __name__ == "__main__":
    init_db()
    purge_old_messages(days=30)
    main()
