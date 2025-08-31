# ui_components.py

"""
Módulo para componentes de la interfaz de usuario de Streamlit.
"""

import re
from datetime import date, datetime
from typing import Any, List

import streamlit as st
from groq import APIStatusError, Groq
from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.config import settings
from app.core import code_tools
from app.core.code_tools import Diagnostic
from app.core.export import export_md, export_pdf
from app.core.file_handler import process_uploaded_file
from app.core.utils import chunk_text
from app.db.persistence import (
    delete_all_messages,
    load_all_messages,
    load_messages,
    load_messages_between,
    save_message,
)
from app.llm.llm_handler import get_groq_response
from app.llm.prompts import AgentMode, get_system_prompt


def handle_agent_mode_change() -> None:
    """
    Callback para manejar el cambio de modo del agente.
    
    Reinicia el historial de chat con el nuevo prompt de sistema para forzar
    la adopción de la nueva "personalidad" y evitar la contaminación del contexto.
    """
    selected_mode_value = st.session_state.get(
        "agent_mode", AgentMode.CODE_GENERATOR.value
    )
    selected_mode = AgentMode(selected_mode_value)

    file_context = st.session_state.get("file_context")
    system_prompt = get_system_prompt(mode=selected_mode, file_context=file_context)

    # Reinicia el historial de mensajes para forzar el nuevo modo
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

    # Limpia los resultados de análisis residuales de conversaciones anteriores
    keys_to_delete = [
        k
        for k in st.session_state.keys()
        if isinstance(k, str) and k.startswith("analysis_result_")
    ]
    for key in keys_to_delete:
        del st.session_state[key]


def render_sidebar() -> None:
    """Renderiza la barra lateral con todos sus componentes."""
    with st.sidebar:
        st.title("Configuración del Agente")

        st.selectbox(
            label="Elige el modo del agente:",
            options=[mode.value for mode in AgentMode],
            key="agent_mode",
            index=1,  # Default to "Ingeniero de Código"
            on_change=handle_agent_mode_change,
            help=(
                "Cambiar el modo reiniciará la conversación actual para adoptar la "
                "nueva personalidad."
            ),
        )

        st.divider()
        _render_file_uploader()
        st.divider()
        _render_export_options()
        st.divider()
        _render_maintenance_options()


def _render_file_uploader() -> None:
    """Renderiza el cargador de archivos y maneja la lógica de análisis."""
    uploaded_file: UploadedFile | None = st.file_uploader(
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
                    st.session_state.file_context = content
                    st.success(f"✅ Archivo '{uploaded_file.name}' analizado.")


def _render_export_options() -> None:
    """Renderiza las opciones para exportar el historial de chat."""
    st.subheader("Exportar Chat")
    n: int = int(
        st.number_input(
            "Últimos N mensajes", min_value=5, max_value=2000, value=50, step=5
        )
    )
    last_n_messages: list[dict[str, Any]] = load_messages(limit=n)
    all_messages: list[dict[str, Any]] = load_all_messages()

    st.caption("Exportar por rango de fechas")
    c_from, c_to = st.columns(2)
    start_date: date = c_from.date_input("Desde", key="export_from_date")  # type: ignore
    start_time = c_from.time_input("Hora desde", key="export_from_time")
    end_date: date = c_to.date_input("Hasta", key="export_to_date")  # type: ignore
    end_time = c_to.time_input("Hora hasta", key="export_to_time")

    range_messages: list[dict[str, Any]] = []
    if isinstance(start_date, date) and isinstance(end_date, date):
        start_dt = datetime.combine(start_date, start_time)
        end_dt = datetime.combine(end_date, end_time)
        if start_dt <= end_dt:
            range_messages = load_messages_between(start_dt, end_dt)

    c1, c2 = st.columns(2)
    c1.download_button(
        "Últimos N (MD)",
        export_md(last_n_messages, True),
        "historial_ultimos.md",
        "text/markdown",
        use_container_width=True,
    )
    c1.download_button(
        "Últimos N (PDF)",
        export_pdf(last_n_messages, True),
        "historial_ultimos.pdf",
        "application/pdf",
        use_container_width=True,
    )
    c2.download_button(
        "Todo (MD)",
        export_md(all_messages, True),
        "historial_completo.md",
        "text/markdown",
        use_container_width=True,
    )
    c2.download_button(
        "Todo (PDF)",
        export_pdf(all_messages, True),
        "historial_completo.pdf",
        "application/pdf",
        use_container_width=True,
    )

    st.markdown("\n")
    c3, c4 = st.columns(2)
    c3.download_button(
        "Rango (MD)",
        export_md(range_messages, True) if range_messages else b"",
        "historial_rango.md",
        "text/markdown",
        disabled=not range_messages,
        use_container_width=True,
    )
    c4.download_button(
        "Rango (PDF)",
        export_pdf(range_messages, True) if range_messages else b"",
        "historial_rango.pdf",
        "application/pdf",
        disabled=not range_messages,
        use_container_width=True,
    )


def _render_maintenance_options() -> None:
    """Renderiza las opciones de mantenimiento y gestión de contexto."""
    st.subheader("Mantenimiento")
    if st.session_state.get("file_context_full"):
        _render_chunk_manager()

    if st.button("Borrar historial (SQLite)", use_container_width=True):
        try:
            delete_all_messages()
            st.session_state.messages = []
            st.session_state.file_context = None
            st.success("Historial borrado.")
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo borrar el historial: {e}")

def _render_chunk_manager() -> None:
    """Gestiona la división del contexto de archivo en partes (chunks)."""
    with st.expander("Ajustes de contexto del archivo", expanded=False):
        st.checkbox("Cortar por tokens", key="chunk_by_tokens")
        if st.session_state.get("chunk_by_tokens"):
            st.number_input("Límite de tokens", value=2000, key="file_tokens_limit")
        st.checkbox("Avanzar automáticamente", key="auto_advance_chunks")

    chunk_chars: int = (
        st.session_state.get("file_tokens_limit", 2000) * 4
        if st.session_state.get("chunk_by_tokens")
        else settings.file_context_max_chars
    )

    if len(st.session_state.get("file_context_full", "")) > chunk_chars:
        if st.session_state.get("file_chunks") is None or (
            st.session_state.file_chunks
            and len(st.session_state.file_chunks[0]) > chunk_chars
        ):
            st.session_state.file_chunks = chunk_text(
                st.session_state.file_context_full, chunk_chars
            )
            st.session_state.file_chunk_index = 0

        total = len(st.session_state.file_chunks)
        idx = st.session_state.file_chunk_index
        st.caption(f"El archivo es grande. Selecciona la parte (1-{total}):")
        c1, c2, c3 = st.columns([1, 2, 1])
        if c1.button("⟵", disabled=idx <= 0):
            st.session_state.file_chunk_index -= 1
        idx = int(c2.number_input("Parte", 1, total, idx + 1)) - 1
        st.session_state.file_chunk_index = idx
        if c3.button("⟶", disabled=idx >= total - 1):
            st.session_state.file_chunk_index += 1

        st.session_state.file_context = st.session_state.file_chunks[idx]
        st.info(f"Parte {idx+1}/{total} · {len(st.session_state.file_context)} chars")


def _handle_chat_input(window_size: int) -> None:
    """Gestiona la entrada del usuario y la respuesta del modelo."""
    if prompt := st.chat_input("Escribe tu pregunta sobre Python aquí..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_message("user", prompt)

        history = st.session_state.messages[1:]
        if len(history) > window_size:
            limit = int(window_size)
            st.session_state.messages = [
                st.session_state.messages[0]
            ] + history[-limit:]

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤖 El agente está pensando..."):
                try:
                    client: Groq = st.session_state.client
                    messages: list[dict[str, str]] = st.session_state.messages
                    response_generator = get_groq_response(client, messages)

                    full_response = st.write_stream(response_generator)

                    st.session_state.messages.append(
                        {"role": "assistant", "content": str(full_response)}
                    )
                    save_message("assistant", str(full_response))

                    auto_advance = st.session_state.get("auto_advance_chunks")
                    chunks_exist = st.session_state.get("file_chunks")
                    if auto_advance and chunks_exist:
                        total = len(st.session_state.file_chunks)
                        idx = st.session_state.file_chunk_index
                        if idx < total - 1:
                            st.session_state.file_chunk_index += 1
                            st.rerun()
                except APIStatusError as e:
                    st.error(f"Error de la API de Groq: {e.message}")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {e}")


def _prepare_chat_messages(window_size: int) -> None:
    """Prepara el prompt del sistema y carga los mensajes iniciales."""
    selected_mode_value = st.session_state.get(
        "agent_mode", AgentMode.CODE_GENERATOR.value
    )
    selected_mode = AgentMode(selected_mode_value)

    system_prompt = get_system_prompt(
        mode=selected_mode, file_context=st.session_state.get("file_context")
    )

    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {"role": "system", "content": system_prompt},
            *load_messages(limit=window_size),
        ]
    else:
        # Actualiza el prompt del sistema si ha cambiado (ej. por carga de archivo)
        st.session_state.messages[0] = {"role": "system", "content": system_prompt}


def _display_diagnostics(diagnostics: List[Diagnostic]):
    """Muestra una lista de diagnósticos de forma estructurada y amigable."""
    if not diagnostics:
        st.success("✅ ¡Excelente! No se encontraron problemas.")
        return

    st.warning(f"Se encontraron {len(diagnostics)} problemas:")

    for diag in diagnostics:
        with st.container(border=True):
            line_info = f"Línea: {diag.line}" if diag.line else "General"
            code_info = f"`{diag.code}`" if diag.code else ""
            st.markdown(f"**{diag.tool}**: {code_info} ({line_info})")
            st.markdown(f"> {diag.message}")
            if diag.tool == "Ruff" and diag.code:
                url = f"https://docs.astral.sh/ruff/rules/{diag.code.lower()}/"
                st.link_button("Ver documentación de la regla", url)


def _render_code_actions(content: str, msg_index: int) -> None:
    """Renderiza botones de acción para bloques de código en un mensaje."""
    run_command_match = re.search(r"<run_command>(.*?)</run_command>", content, re.DOTALL)
    run_command = run_command_match.group(1).strip() if run_command_match else None

    code_blocks = re.findall(r"```(python)?\n?(.*?)```", content, re.DOTALL)
    if not code_blocks:
        return

    code_to_analyze = code_blocks[0][1]
    analysis_key = f"analysis_result_{msg_index}"

    st.write("---")
    c1, c2, c3, c4 = st.columns(4)

    if c1.button(
        "▶️ Ejecutar",
        key=f"run_code_{msg_index}",
        use_container_width=True,
        disabled=not run_command,
    ):
        if run_command:
            output, success = code_tools.run_shell_command(run_command)
            title = "Resultado de la Ejecución" if success else "Error en la Ejecución"
            st.session_state[analysis_key] = (title, output)
            st.rerun()

    if c2.button("Formatear (Ruff)", key=f"ruff_fmt_{msg_index}", use_container_width=True):
        formatted_code, success = code_tools.run_ruff_format(code_to_analyze)
        title = "Código Formateado" if success else "Error de Formateo"
        st.session_state[analysis_key] = (title, formatted_code)
        st.rerun()

    if c3.button("Validar (Ruff)", key=f"ruff_chk_{msg_index}", use_container_width=True):
        diagnostics, _ = code_tools.run_ruff_check(code_to_analyze)
        st.session_state[analysis_key] = ("Análisis de Ruff", diagnostics)
        st.rerun()

    if c4.button("Validar (MyPy)", key=f"mypy_chk_{msg_index}", use_container_width=True):
        diagnostics, _ = code_tools.run_mypy_check(code_to_analyze)
        st.session_state[analysis_key] = ("Análisis de MyPy", diagnostics)
        st.rerun()

    if analysis_key in st.session_state:
        title, result = st.session_state.pop(analysis_key)
        with st.expander(f"Resultado: {title}", expanded=True):
            if isinstance(result, list) and all(isinstance(d, Diagnostic) for d in result):
                _display_diagnostics(result)
            elif isinstance(result, str):
                output_lang = 'python' if title == "Código Formateado" else 'bash'
                st.code(result, language=output_lang, line_numbers=True)


def _display_chat_messages(display_window: int) -> None:
    """Muestra los mensajes del historial de chat."""
    messages_to_render = st.session_state.get("messages", [])[1:]

    if len(messages_to_render) > display_window:
        messages_to_render = messages_to_render[-display_window:]

    for i, msg in enumerate(messages_to_render):
        avatar = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                _render_code_actions(msg["content"], msg_index=i)

def render_chat_interface() -> None:
    """Función principal que renderiza toda la interfaz de chat."""
    st.title("🤖 Agente Experto en Python")

    window_size = settings.conversation_window_messages
    display_window = settings.display_window_messages

    _prepare_chat_messages(window_size)
    _display_chat_messages(display_window)
    _handle_chat_input(window_size)