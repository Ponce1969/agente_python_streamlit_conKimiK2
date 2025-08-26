# styles.py
import streamlit as st

def apply_global_styles() -> None:
    """Aplica el CSS global a la aplicación (sin tema dinámico)."""
    st.markdown("", unsafe_allow_html=True)

def apply_theme() -> None:
    """Aplica CSS dinámico según el tema seleccionado."""
    theme = st.session_state.get("theme", "light")
    
    if theme == "dark":
        css = """
        <style>
            /* Tema Oscuro Suave */
            .stApp {
                background-color: #1e293b !important;  /* Gris oscuro suave */
                color: #f1f5f9 !important;  /* Blanco ligeramente cálido */
            }
            [data-testid="stSidebar"] {
                background-color: #334155 !important;  /* Gris medio oscuro */
                border-right: 1px solid #475569 !important;
            }
            [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
                background-color: #334155 !important;  /* Gris medio */
                border: 1px solid #475569 !important;
                margin: 0.5rem 2.5rem 0.5rem 0;
                border-radius: 0.75rem;
                padding: 0.875rem 1rem;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }
            [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
                background-color: #2a3441 !important;  /* Gris azulado suave */
                border: 1px solid #3e4c5e !important;
                margin: 0.5rem 0 0.5rem 2.5rem;
                border-radius: 0.75rem;
                padding: 0.875rem 1rem;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }
            [data-testid="stChatMessage"] code {
                color: #e2e8f0 !important;
                background-color: #475569 !important;  /* Gris más claro */
                border: 1px solid #64748b !important;
                padding: 0.125rem 0.375rem;
                border-radius: 0.375rem;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            }
            [data-testid="stChatMessage"] pre {
                background-color: #334155 !important;
                color: #f1f5f9 !important;
                border: 1px solid #475569 !important;
                padding: 0.875rem 1rem;
                border-radius: 0.625rem;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .stDownloadButton button, .stButton button {
                background-color: #3b82f6 !important;
                color: white !important;
                border-radius: 0.5rem;
                border: none;
                padding: 0.625rem 0.875rem;
                transition: background-color 0.2s ease;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }
            .stDownloadButton button:hover, .stButton button:hover {
                background-color: #2563eb !important;
            }
            .stTextInput > div > div > input {
                background-color: #334155 !important;
                color: #f1f5f9 !important;
                border: 1px solid #475569 !important;
            }
            .stSelectbox > div > div > div {
                background-color: #334155 !important;
                color: #f1f5f9 !important;
                border: 1px solid #475569 !important;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #f1f5f9 !important;
            }
            .stMarkdown {
                color: #f1f5f9 !important;
            }
            /* Header/Cabecera */
            header[data-testid="stHeader"] {
                background-color: rgb(117, 107, 107) !important;
                border-bottom: 1px solid #475569 !important;
            }
            /* Input del chat - gris clarito */
            [data-testid="stChatInput"] {
                background-color: #64748b !important;  /* Gris clarito */
                border: 1px solid #94a3b8 !important;
                border-radius: 0.75rem;
            }
            [data-testid="stChatInput"] input {
                background-color: transparent !important;
                color: #f1f5f9 !important;
            }
            /* Footer - gris más oscuro que el input */
            .stBottomBlockContainer {
                background-color: #1e293b !important;  /* Gris más oscuro */
                border-top: 1px solid #334155 !important;
                padding: 1rem 0;
            }
            /* Scrollbar oscuro */
            ::-webkit-scrollbar {
                width: 8px;
            }
            ::-webkit-scrollbar-track {
                background: #334155 !important;
            }
            ::-webkit-scrollbar-thumb {
                background: #475569 !important;
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #64748b !important;
            }
        </style>
        """
    else:  # light theme
        css = """
        <style>
            /* Tema Claro */
            .stApp {
                background-color: #f5f7fb !important;
                color: #24292e !important;
            }
            [data-testid="stSidebar"] {
                background-color: #ffffff !important;
                border-right: 1px solid #e6e8ec !important;
            }
            [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
                background-color: #ffffff !important;
                border: 1px solid #e6e8ec !important;
                margin: 0.5rem 2.5rem 0.5rem 0;
                border-radius: 0.75rem;
                padding: 0.875rem 1rem;
                box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
            }
            [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
                background-color: #f7fbff !important;
                border: 1px solid #d6e9ff !important;
                margin: 0.5rem 0 0.5rem 2.5rem;
                border-radius: 0.75rem;
                padding: 0.875rem 1rem;
                box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
            }
            [data-testid="stChatMessage"] code {
                color: #24292e !important;
                background-color: #f6f8fa !important;
                border: 1px solid #eaeef2 !important;
                padding: 0.125rem 0.375rem;
                border-radius: 0.375rem;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            }
            [data-testid="stChatMessage"] pre {
                background-color: #f6f8fa !important;
                color: #24292e !important;
                border: 1px solid #eaeef2 !important;
                padding: 0.875rem 1rem;
                border-radius: 0.625rem;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .stDownloadButton button, .stButton button {
                background-color: #2563eb !important;
                color: white !important;
                border-radius: 0.5rem;
                border: none;
                padding: 0.625rem 0.875rem;
                transition: background-color 0.2s ease;
                box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
            }
            .stDownloadButton button:hover, .stButton button:hover {
                background-color: #1d4ed8 !important;
            }
            .stTextInput > div > div > input {
                background-color: #ffffff !important;
                color: #24292e !important;
                border: 1px solid #e6e8ec !important;
            }
            .stSelectbox > div > div > div {
                background-color: #ffffff !important;
                color: #24292e !important;
                border: 1px solid #e6e8ec !important;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #24292e !important;
            }
            .stMarkdown {
                color: #24292e !important;
            }
        </style>
        """
    
    st.markdown(css, unsafe_allow_html=True)

