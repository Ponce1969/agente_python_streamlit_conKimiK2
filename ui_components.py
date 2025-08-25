# ui_components.py

"""
Módulo para componentes de la interfaz de usuario de Streamlit.
"""

# Aquí moveremos las funciones render_sidebar y render_chat_interface
from datetime import datetime

import streamlit as st
from groq import APIStatusError

from config import settings
from db import (
    delete_all_messages,
    load_all_messages,
    load_messages,
    load_messages_between,
    save_message,
)
from export import export_md, export_pdf
from file_handler import process_uploaded_file
from llm_handler import get_groq_response
from utils import chunk_text


def _render_theme_selector() -> None:
    """Renderiza un toggle para cambiar entre tema claro y oscuro."""
    st.subheader("Tema")

    # El valor inicial del toggle se basa en el estado actual del tema
    is_dark_mode = st.session_state.get("theme", "light") == "dark"

    # Crear el toggle. Su estado (on/off) determinará el tema.
    if st.toggle("Modo Oscuro", value=is_dark_mode, key="theme_toggle"):
        # Si el toggle está activado, el tema es oscuro
        if st.session_state.theme != "dark":
            st.session_state.theme = "dark"
            st.rerun()
    else:
        # Si el toggle está desactivado, el tema es claro
        if st.session_state.theme != "light":
            st.session_state.theme = "light"
            st.rerun()


def render_sidebar() -> None:
    """Renderiza la barra lateral con todas las opciones."""
    with st.sidebar:
        st.title("⚙️ Opciones")
        st.divider()

        _render_theme_selector()

        st.subheader("Análisis de Archivos")
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

    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)
    range_messages = []
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

    chunk_chars = (st.session_state.file_tokens_limit * 4 
                   if st.session_state.chunk_by_tokens 
                   else settings.file_context_max_chars)

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
        idx = c2.number_input("Parte", 1, total, idx + 1) - 1
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
            st.session_state.messages = [st.session_state.messages[0]] + history[-window_size:]

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤖 El agente está pensando..."):
                try:
                    response_generator = get_groq_response(st.session_state.client, st.session_state.messages)
                    full_response = st.write_stream(response_generator)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    save_message("assistant", full_response)
                except APIStatusError as e:
                    st.error(f"Error de la API de Groq: {e.message}")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {e}")
                else:
                    if st.session_state.get("auto_advance_chunks") and st.session_state.get("file_chunks"):
                        total = len(st.session_state.file_chunks)
                        idx = st.session_state.file_chunk_index
                        if idx < total - 1:
                            st.session_state.file_chunk_index += 1
                            st.rerun()

def _prepare_chat_messages(window_size: int) -> str:
    """Prepara el prompt del sistema y carga los mensajes iniciales."""
    system_prompt = settings.BASE_SYSTEM_PROMPT
    if st.session_state.file_context:
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
    return system_prompt

def _display_chat_messages(display_window: int) -> None:
    """Muestra los mensajes del historial de chat."""
    to_render = st.session_state.messages[1:]
    if len(to_render) > display_window:
        to_render = to_render[-display_window:]
    
    for msg in to_render:
        avatar = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

def render_chat_interface() -> None:
    st.title("🤖 Agente Experto en Python")

    window_size = settings.conversation_window_messages
    display_window = settings.display_window_messages

    _prepare_chat_messages(window_size)
    _display_chat_messages(display_window)
    _handle_chat_input(window_size)
