1# 🐍 Agente de Chat IA para Python 3.12+

Asistente experto en Python 3.12+ con Streamlit y Groq (`moonshotai/kimi-k2-instruct`). Incluye persistencia en SQLite, exportación a PDF/Markdown, análisis de archivos y mantenimiento del historial.

## ✨ Características

- **UI renovada** con estilos para chat y bloques de código.
- **Streaming** de respuestas del modelo.
- **Exportación** a PDF y Markdown.
- **Análisis de archivos** (`.py`, `.txt`, `.md`, `.csv`, `.pdf`) con límite 5MB y manejo de errores.
- **Autenticación** con contraseña maestra (hash en memoria).
- **Historial persistente** en SQLite y botón para borrarlo desde la barra lateral.
- **Control de contexto** configurable para evitar errores HTTP 413.

## 📂 Estructura

- `main.py`: Punto de entrada de la aplicación. Orquesta la inicialización, autenticación y renderizado de la UI.
- `config.py`: Centraliza toda la configuración de la aplicación usando Pydantic-settings, cargando desde `.env`.
- `ui_components.py`: Contiene los componentes de la interfaz de usuario de Streamlit (`render_sidebar`, `render_chat_interface`).
- `llm_handler.py`: Gestiona toda la lógica de interacción con la API de Groq (LLM).
- `styles.py`: Define los estilos CSS para los temas claro y oscuro de la aplicación.
- `db.py`: Módulo de acceso a la base de datos SQLite.
- `export.py`: Lógica para exportar el historial del chat a Markdown y PDF.
- `file_handler.py`: Maneja la carga y procesamiento de archivos.
- `utils.py`: Contiene utilidades de seguridad (hashing, verificación) y el limitador de intentos (rate limiter).
- `docker-compose.yml`, `dockerfile`: Archivos para la contenerización con Docker.
- `.env`: Almacena las variables de entorno y secretos (no incluido en el control de versiones).

## 🛠️ Stack

Python 3.12+, Streamlit, Groq API, `uv`, Docker, SQLite, ReportLab.

## 🚀 Puesta en marcha

Requisitos: Docker y Docker Compose.

1) Crea `.env` en la raíz con al menos:

```env
# Credenciales obligatorias
GROQ_API_KEY="tu_api_key_de_groq"
MASTER_PASSWORD="tu_contraseña_maestra"

# Opcionales (valores por defecto mostrados)
GROQ_MODEL_NAME="moonshotai/kimi-k2-instruct"  # puedes cambiarlo por otro modelo de Groq
DB_PATH="db/chat_history.db"
CONVERSATION_WINDOW_MESSAGES=20
DISPLAY_WINDOW_MESSAGES=12
FILE_CONTEXT_MAX_CHARS=8000
MESSAGES_MAX_CHARS=12000
```

2) Ejecuta:

```bash
docker compose up --build -d
```

Abre http://localhost:8501 y usa la contraseña maestra.


## 🧰 Uso

- **Chat**: escribe tu pregunta. Respuesta en streaming.
- **Análisis de archivos**: sube un archivo en la barra lateral. Se inyecta al prompt con límite `FILE_CONTEXT_MAX_CHARS` (se muestra aviso si se trunca).
- **Exportar**: descarga historial como Markdown o PDF.
- **Mantenimiento**: botón “🗑️ Borrar historial (SQLite)” para eliminar la tabla de mensajes y limpiar el estado de sesión.

## ⚙️ Control de contexto

- `CONVERSATION_WINDOW_MESSAGES`: cuántos mensajes se cargan desde SQLite al iniciar.
- `FILE_CONTEXT_MAX_CHARS`: máximo de caracteres del archivo adjunto que van al prompt.
- `MESSAGES_MAX_CHARS`: máximo de caracteres del historial enviados por request (el mensaje `system` siempre se mantiene).

Sugerencias: 12 / 6000 / 10000. Si surge HTTP 413, reduce (p.ej., 8 / 4000 / 8000).

## 🔐 Autenticación

`MASTER_PASSWORD` se hashea al inicio (`MASTER_PASSWORD_HASH`) y no se guarda en texto plano. Hay limitador de intentos de login.

## 🧪 Calidad y desarrollo

```bash
uv run ruff check --fix .
uv run mypy .
```

Notas: algunas cadenas largas están partidas (E501). `render_chat_interface()` tiene `# noqa: C901` temporal.

## 🗃️ Base de datos

Archivo SQLite en `db/chat_history.db` (mapeado en Docker). Las funciones en `db.py` se encargan de crear tablas/índices, guardar/cargar mensajes, purgar por fecha y borrar todo el historial.

## 🧯 Troubleshooting

- **HTTP 413**: baja `MESSAGES_MAX_CHARS` y/o `FILE_CONTEXT_MAX_CHARS`; borra historial; reduce `CONVERSATION_WINDOW_MESSAGES`.
- **“No hay mensajes para exportar”**: el historial está vacío; envía algún mensaje.
- **Logs con `init_db()` repetido**: es normal en Streamlit por las re-ejecuciones.