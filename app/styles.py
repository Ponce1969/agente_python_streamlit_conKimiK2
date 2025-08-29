# styles.py
import streamlit as st

def load_css() -> None:
    """
    Carga una hoja de estilos CSS optimizada y adaptable a los temas de Streamlit.
    Utiliza variables de tema de Streamlit para asegurar la consistencia
    entre los modos claro y oscuro.
    """
    css = """
    <style>
        /* --- ESTILOS GENERALES Y RESET --- */

        /* Ajuste del scrollbar para que coincida con el tema */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--secondary-background-color);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: color-mix(in srgb, var(--primary-color), #000 10%);
        }

        /* --- ESTILOS DE COMPONENTES ESPECÍFICOS --- */

        /* Contenedor de mensajes del chat */
        [data-testid="stChatMessage"] {
            border-radius: 0.75rem;
            padding: 0.875rem 1rem;
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            border: 1px solid transparent;
            transition: all 0.3s ease;
        }

        /* Mensaje del usuario */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background-color: var(--secondary-background-color);
            margin-right: 2.5rem;
            border-color: color-mix(in srgb, var(--text-color), transparent 90%);
        }

        /* Mensaje del asistente */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            /* Un color ligeramente distinto para el asistente, derivado del fondo secundario */
            background-color: color-mix(in srgb, var(--secondary-background-color), var(--primary-color) 4%);
            margin-left: 2.5rem;
            border-color: color-mix(in srgb, var(--primary-color), transparent 85%);
        }

        /* Bloques de código dentro de los mensajes */
        [data-testid="stChatMessage"] code {
            color: var(--text-color);
            background-color: color-mix(in srgb, var(--secondary-background-color), var(--text-color) 5%);
            border: 1px solid color-mix(in srgb, var(--text-color), transparent 90%);
            padding: 0.125rem 0.375rem;
            border-radius: 0.375rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }

        /* Bloques de preformateado (código multi-línea) */
        [data-testid="stChatMessage"] pre {
            background-color: color-mix(in srgb, var(--secondary-background-color), #000 5%);
            color: var(--text-color);
            border: 1px solid color-mix(in srgb, var(--text-color), transparent 90%);
            padding: 0.875rem 1rem;
            border-radius: 0.625rem;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        /* Estilo para el modo oscuro de los bloques de preformateado */
        [data-theme="dark"] [data-testid="stChatMessage"] pre {
             background-color: color-mix(in srgb, var(--secondary-background-color), #fff 5%);
        }


        /* Botones principales y de descarga */
        .stDownloadButton button, .stButton button {
            border-radius: 0.5rem;
            padding: 0.625rem 0.875rem;
            transition: all 0.2s ease;
            /* El color de fondo y texto ya lo gestiona Streamlit con primaryColor */
        }

        .stDownloadButton button:hover, .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
        }

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)