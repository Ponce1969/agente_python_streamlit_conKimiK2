# ui_components.py

"""
Módulo para componentes de la interfaz de usuario de Streamlit.
"""

import re
from datetime import datetime, date

import streamlit as st
from groq import APIStatusError

from app.config import settings
from app.core import code_tools
from app.db.persistence import (
    delete_all_messages,
    load_all_messages,
    load_messages,
    load_messages_between,
    save_message,
)
from app.core.export import export_md, export_pdf
from app.core.file_handler import process_uploaded_file
from app.llm.llm_handler import get_groq_response
from app.core.utils import chunk_text
from app.llm.prompts import AgentMode, get_system_prompt


def render_sidebar() -> None:
    """Renderiza la barra lateral con todos sus componentes."""
    with st.sidebar:
        st.title("Configuración del Agente")
        
        st.selectbox(
            "Elige el modo del agente:",
            options=[mode.value for mode in AgentMode],
            key="agent_mode",
            index=0
        )

        st.divider()
        _render_file_uploader()
        st.divider()
        _render_export_options()
        st.divider()
        _render_maintenance_options()

def _render_file_uploader() -> None:
    """Renderiza el cargador de archivos y maneja la lógica de análisis."""
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
            result = process_uploaded_file(uploaded_file)
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
    n = st.number_input(
        "Últimos N mensajes", min_value=5, max_value=2000, value=50, step=5
    )
    last_n_messages = load_messages(limit=int(n))
    all_messages = load_all_messages()

    st.caption("Exportar por rango de fechas")
    c_from, c_to = st.columns(2)
    start_date = c_from.date_input("Desde", key="export_from_date")
    start_time = c_from.time_input("Hora desde", key="export_from_time")
    end_date = c_to.date_input("Hasta", key="export_to_date")
    end_time = c_to.time_input("Hora hasta", key="export_to_time")

    range_messages = []
    if isinstance(start_date, date) and isinstance(end_date, date):
        start_dt = datetime.combine(start_date, start_time)
        end_dt = datetime.combine(end_date, end_time)
        if start_dt <= end_dt:
            range_messages = load_messages_between(start_dt, end_dt)

    c1, c2 = st.columns(2)
    c1.download_button(
        "Últimos N (MD)", export_md(last_n_messages, True), "historial_ultimos.md", "text/markdown", use_container_width=True
    )
    c1.download_button(
        "Últimos N (PDF)", export_pdf(last_n_messages, True), "historial_ultimos.pdf", "application/pdf", use_container_width=True
    )
    c2.download_button(
        "Todo (MD)", export_md(all_messages, True), "historial_completo.md", "text/markdown", use_container_width=True
    )
    c2.download_button(
        "Todo (PDF)", export_pdf(all_messages, True), "historial_completo.pdf", "application/pdf", use_container_width=True
    )

    st.markdown("\n")
    c3, c4 = st.columns(2)
    c3.download_button(
        "Rango (MD)", export_md(range_messages, True) if range_messages else b"", "historial_rango.md", "text/markdown", disabled=not range_messages, use_container_width=True
    )
    c4.download_button(
        "Rango (PDF)", export_pdf(range_messages, True) if range_messages else b"", "historial_rango.pdf", "application/pdf", disabled=not range_messages, use_container_width=True
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
        if st.session_state.chunk_by_tokens:
            st.number_input("Límite de tokens", value=2000, key="file_tokens_limit")
        st.checkbox("Avanzar automáticamente", key="auto_advance_chunks")

    chunk_chars = (
        st.session_state.file_tokens_limit * 4 
        if st.session_state.chunk_by_tokens 
        else settings.file_context_max_chars
    )

    if len(st.session_state.file_context_full) > chunk_chars:
        if st.session_state.file_chunks is None or \
           len(st.session_state.file_chunks[0]) > chunk_chars:
            st.session_state.file_chunks = chunk_text(
                st.session_state.file_context_full, chunk_chars
            )
            st.session_state.file_chunk_index = 0

        total = len(st.session_state.file_chunks)
        idx = st.session_state.file_chunk_index
        st.caption(f"El archivo es grande. Selecciona la parte (1-{total}):")
        c1, c2, c3 = st.columns([1, 2, 1])
        if c1.button("⟵", disabled=idx <= 0): st.session_state.file_chunk_index -= 1
        idx = int(c2.number_input("Parte", 1, total, idx + 1)) - 1
        st.session_state.file_chunk_index = idx
        if c3.button("⟶", disabled=idx >= total - 1): st.session_state.file_chunk_index += 1
        
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
            st.session_state.messages = [st.session_state.messages[0]] + history[-limit:]

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤖 El agente está pensando..."):
                try:
                    response_generator = get_groq_response(st.session_state.client, st.session_state.messages)
                    full_response = st.write_stream(response_generator)
                    
                    st.session_state.messages.append({"role": "assistant", "content": str(full_response)})
                    save_message("assistant", str(full_response))
                    
                    if st.session_state.get("auto_advance_chunks") and st.session_state.get("file_chunks"):
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
    selected_mode_value = st.session_state.get("agent_mode", AgentMode.PYTHON_ARCHITECT.value)
    selected_mode = AgentMode(selected_mode_value)

    system_prompt = get_system_prompt(
        mode=selected_mode,
        file_context=st.session_state.get("file_context")
    )

    if not st.session_state.messages:
        st.session_state.messages = [
            {"role": "system", "content": system_prompt},
            *load_messages(limit=window_size),
        ]
    else:
        st.session_state.messages[0] = {"role": "system", "content": system_prompt}

def _render_code_actions(content: str, msg_index: int):
    """Renderiza botones de acción para bloques de código en un mensaje."""
    # Extraer comando de ejecución si existe
    run_command_match = re.search(r"<run_command>(.*?)</run_command>", content, re.DOTALL)
    run_command = run_command_match.group(1).strip() if run_command_match else None

    # Extraer solo el código Python para las otras herramientas
    code_blocks = re.findall(r"```(python)?\n?(.*?)""", content, re.DOTALL)
    if not code_blocks:
        return

    code_to_analyze = code_blocks[0][1]
    analysis_key = f"analysis_result_{msg_index}"

    st.write("---")
    c1, c2, c3, c4 = st.columns(4)

    # Botón de Ejecutar (condicional)
    if c1.button("▶️ Ejecutar", key=f"run_code_{msg_index}", use_container_width=True, disabled=not run_command):
        if run_command:
            output, success = code_tools.run_shell_command(run_command)
            title = "Resultado de la Ejecución" if success else "Error en la Ejecución"
            st.session_state[analysis_key] = (title, output)
            st.rerun()

    # Botones de Análisis de Código
    if c2.button("Formatear (Ruff)", key=f"ruff_fmt_{msg_index}", use_container_width=True):
        formatted_code, success = code_tools.run_ruff_format(code_to_analyze)
        st.session_state[analysis_key] = ("Código Formateado", formatted_code) if success else ("Error de Formateo", formatted_code)
        st.rerun()

    if c3.button("Validar (Ruff)", key=f"ruff_chk_{msg_index}", use_container_width=True):
        ruff_output, _ = code_tools.run_ruff_check(code_to_analyze)
        st.session_state[analysis_key] = ("Análisis de Ruff", ruff_output)
        st.rerun()

    if c4.button("Validar (MyPy)", key=f"mypy_chk_{msg_index}", use_container_width=True):
        mypy_output, _ = code_tools.run_mypy_check(code_to_analyze)
        st.session_state[analysis_key] = ("Análisis de MyPy", mypy_output)
        st.rerun()

    # Mostrar resultados
    if analysis_key in st.session_state:
        title, output = st.session_state.pop(analysis_key)
        with st.expander(f"Resultado: {title}", expanded=True):
            output_lang = 'python' if title == "Código Formateado" else 'bash'
            st.code(output, language=output_lang, line_numbers=True)

def _display_chat_messages(display_window: int) -> None:
    """Muestra los mensajes del historial de chat."""
    to_render = st.session_state.messages[1:]
    if len(to_render) > display_window:
        to_render = to_render[-display_window:]
    
    for i, msg in enumerate(to_render):
        avatar = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                _render_code_actions(msg["content"], i)

def render_chat_interface() -> None:
    st.title("🤖 Agente Experto en Python")

    window_size = settings.conversation_window_messages
    display_window = settings.display_window_messages

    _prepare_chat_messages(window_size)
    _display_chat_messages(display_window)
    _handle_chat_input(window_size)
