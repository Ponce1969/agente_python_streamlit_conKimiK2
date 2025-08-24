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

- `main.py`: UI de Streamlit, estado de sesión y flujo del chat. Sidebar con carga de archivos, exportación y mantenimiento.
- `db.py`: Acceso a SQLite (`init_db`, `save_message`, `load_messages`, `purge_old_messages`, `delete_all_messages`).
- `export.py`: Exportación a PDF/Markdown.
- `file_handler.py`: Procesamiento de archivos subidos.
- `utils.py`: Seguridad, validación de entorno, rate limiter.
- `docker-compose.yml`, `dockerfile`: Contenerización.
- `.env`: Variables de configuración (no se comitea).

## 🛠️ Stack

Python 3.12+, Streamlit, Groq API, `uv`, Docker, SQLite, ReportLab.

## 🚀 Puesta en marcha

Requisitos: Docker y Docker Compose.

1) Crea `.env` en la raíz con al menos:

```env
GROQ_API_KEY=tu_api_key_de_groq
MASTER_PASSWORD=tu_contraseña_maestra
DB_BACKEND=sqlite

# Control de contexto (opcional, recomendado)
CONVERSATION_WINDOW_MESSAGES=12
FILE_CONTEXT_MAX_CHARS=6000
MESSAGES_MAX_CHARS=10000
```

2) Ejecuta:

```bash
docker compose up --build -d
```

Abre http://localhost:8501 y usa la contraseña maestra.

### Ejemplos de archivos .env por entorno

Puedes mantener dos archivos y elegir cuál usar en despliegue. Por defecto, `load_dotenv()` carga `.env`.

- Para desarrollo: usa `.env.development` y copia a `.env` cuando ejecutes local.
- Para producción: usa `.env.production` y monta/inyecta como `.env` en el contenedor (o variables de entorno del orquestador).

Ejemplo desarrollo (`.env.development`):

```env
GROQ_API_KEY=api_key_de_pruebas_o_entorno_sandbox
MASTER_PASSWORD=dev_password_segura
DB_BACKEND=sqlite

CONVERSATION_WINDOW_MESSAGES=12
FILE_CONTEXT_MAX_CHARS=6000
MESSAGES_MAX_CHARS=10000

# Verbosidad útil en dev (opcional, si la app lo soporta)
LOG_LEVEL=INFO
```

Ejemplo producción (`.env.production`):

```env
GROQ_API_KEY=${GROQ_API_KEY}
MASTER_PASSWORD=${MASTER_PASSWORD}
DB_BACKEND=sqlite

# Límites un poco más conservadores para reducir costos/errores
CONVERSATION_WINDOW_MESSAGES=10
FILE_CONTEXT_MAX_CHARS=5000
MESSAGES_MAX_CHARS=9000

# Menos verboso en prod
LOG_LEVEL=WARNING
```

Sugerencias:
- En producción, no subas `.env.production`; usa secretos del orquestador (Docker/Compose `env_file`, GitHub Actions, Kubernetes Secrets, etc.).
- Si quieres que `python-dotenv` cargue un archivo distinto a `.env`, renombra/gestiona el archivo antes de ejecutar o pasa variables directamente al contenedor.

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

Archivo SQLite en `data/chat.db` (mapeado en Docker). Funciones en `db.py` para crear tablas/índices, guardar/cargar mensajes, purgar por fecha y borrar todo el historial.

## 🧯 Troubleshooting

- **HTTP 413**: baja `MESSAGES_MAX_CHARS` y/o `FILE_CONTEXT_MAX_CHARS`; borra historial; reduce `CONVERSATION_WINDOW_MESSAGES`.
- **“No hay mensajes para exportar”**: el historial está vacío; envía algún mensaje.
- **Logs con `init_db()` repetido**: es normal en Streamlit por las re-ejecuciones.