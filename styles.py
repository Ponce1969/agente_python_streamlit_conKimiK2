# styles.py
import streamlit as st

# CSS unificado con variables para temas claro y oscuro.
# Se usan unidades `rem` para mejor accesibilidad y escalado.
CUSTOM_CSS: str = """
<style>
    /* --- Definición de variables CSS --- */
    body[data-theme="light"] {
        --app-bg: #f5f7fb;
        --chat-user-bg: #ffffff;
        --chat-user-border: #e6e8ec;
        --chat-assistant-bg: #f7fbff;
        --chat-assistant-border: #d6e9ff;
        --code-bg: #f6f8fa;
        --code-text: #24292e;
        --code-border: #eaeef2;
        --button-bg: #2563eb;
        --button-bg-hover: #1d4ed8;
        --button-text: white;
        --shadow: rgba(16, 24, 40, 0.04);
    }
    body[data-theme="dark"] {
        --app-bg: #0f172a;
        --chat-user-bg: #111827;
        --chat-user-border: #1f2937;
        --chat-assistant-bg: #0b1220;
        --chat-assistant-border: #1d2a44;
        --code-bg: #111827;
        --code-text: #e2e8f0;
        --code-border: #1f2937;
        --button-bg: #3b82f6;
        --button-bg-hover: #2563eb;
        --button-text: white;
        --shadow: rgba(0, 0, 0, 0.3);
    }

    /* --- Estilos Base --- */
    .stApp { 
        background-color: var(--app-bg) !important; 
    }
    h1 {
        font-size: 1.8rem !important;
        padding-bottom: 0.5rem;
    }
    [data-testid="stChatMessage"] {
        border: 1px solid;
        border-radius: 0.75rem; /* 12px */
        padding: 0.875rem 1rem; /* 14px 16px */
        box-shadow: 0 1px 2px var(--shadow);
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: var(--chat-user-bg);
        border-color: var(--chat-user-border);
        margin: 0.5rem 2.5rem 0.5rem 0; /* 8px 40px 8px 0 */
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background-color: var(--chat-assistant-bg);
        border-color: var(--chat-assistant-border);
        margin: 0.5rem 0 0.5rem 2.5rem; /* 8px 0 8px 40px */
    }
    [data-testid="stChatMessage"] code {
        color: var(--code-text);
        background-color: var(--code-bg);
        border: 1px solid var(--code-border);
        padding: 0.125rem 0.375rem; /* 2px 6px */
        border-radius: 0.375rem; /* 6px */
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    [data-testid="stChatMessage"] pre {
        background-color: var(--code-bg);
        color: var(--code-text);
        border: 1px solid var(--code-border);
        padding: 0.875rem 1rem; /* 14px 16px */
        border-radius: 0.625rem; /* 10px */
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .stDownloadButton button, .stButton button {
        background-color: var(--button-bg);
        color: var(--button-text);
        border-radius: 0.5rem; /* 8px */
        border: none;
        padding: 0.625rem 0.875rem; /* 10px 14px */
        transition: background-color 0.2s ease;
        box-shadow: 0 1px 2px var(--shadow);
    }
    .stDownloadButton button:hover, .stButton button:hover {
        background-color: var(--button-bg-hover);
    }
</style>
"""

def apply_global_styles() -> None:
    """Aplica el CSS global a la aplicación."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def apply_theme() -> None:
    """Aplica un script para establecer el tema actual en el body."""
    theme = st.session_state.get("theme", "light")
    theme_script = f"""
        <script>
            document.body.setAttribute('data-theme', '{theme}');
        </script>
    """
    st.markdown(theme_script, unsafe_allow_html=True)
