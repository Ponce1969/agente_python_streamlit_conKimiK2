# 🐍 Agente de Desarrollo IA Interactivo (Python 3.12+)

Este proyecto es un agente de IA interactivo y especializado para el desarrollo de backend con Python. Construido con Streamlit y la API de Groq, va más allá de un simple chatbot para convertirse en un asistente proactivo que participa en el ciclo de vida del desarrollo de software.

El agente puede generar código, analizarlo con herramientas de calidad, ejecutarlo bajo demanda y proponer modificaciones directamente sobre la base de código del proyecto.

---

## ✨ Características Principales

### Capacidades del Agente

- **Agente Multi-Personalidad**: Elige entre diferentes roles especializados (Arquitecto, Ingeniero de Código, Auditor de Seguridad, etc.) para obtener respuestas adaptadas a tareas específicas. Cada modo utiliza un prompt de sistema altamente detallado y técnico.
- **Análisis de Código Interactivo**: Analiza los bloques de código generados con un solo clic, usando herramientas estándar de la industria:
    - **Formatear (Ruff)**: Aplica formato de código consistente.
    - **Validar (Ruff)**: Detecta problemas de estilo y errores comunes.
    - **Validar (MyPy)**: Realiza un análisis estático de tipos.
- **Ejecución de Código Inteligente**: El agente identifica si el código generado es ejecutable y proporciona el comando exacto para correrlo (ej. `uvicorn main:app` para FastAPI o `python mi_script.py` para un script). El botón de ejecución solo se activa si el comando está presente.
- **Gestión de Archivos**: El agente puede proponer la creación de nuevos archivos o la modificación de los existentes. **Ningún cambio se realiza sin la confirmación explícita del usuario**.

### Funcionalidades de la Aplicación

- **UI Moderna**: Interfaz de usuario clara y funcional construida con Streamlit.
- **Streaming de Respuestas**: Las respuestas del modelo se muestran en tiempo real.
- **Análisis de Archivos**: Sube archivos (`.py`, `.txt`, `.pdf`, etc.) para que el agente los use como contexto en sus respuestas.
- **Persistencia**: El historial de conversaciones se guarda en una base de datos SQLite.
- **Exportación**: Descarga el historial del chat en formato Markdown o PDF.
- **Seguridad**: Autenticación mediante contraseña y limitador de intentos de login.

---

## 🏛️ Arquitectura

El proyecto sigue una estructura modular para facilitar la escalabilidad y el mantenimiento.

- `main.py`: Punto de entrada de la aplicación Streamlit. Orquesta la inicialización y la UI.
- `config.py`: Configuración centralizada mediante Pydantic-settings (carga desde `.env`).
- `app/styles.py`: Estilos CSS para la interfaz.
- `app/ui/components.py`: Lógica de los componentes de la UI de Streamlit.
- `app/llm/prompts.py`: **(Clave)** Define las personalidades del agente, las constantes de formato y los prompts de sistema detallados.
- `app/llm/llm_handler.py`: Gestiona la comunicación con la API de Groq.
- `app/core/code_tools.py`: Funciones para interactuar con herramientas de CLI como `ruff`, `mypy` y para ejecutar comandos de shell.
- `app/core/file_handler.py`: Lógica para la carga y procesamiento de archivos.
- `app/core/utils.py`: Utilidades de seguridad y rate limiting.
- `app/db/persistence.py`: Lógica de interacción con la base de datos SQLite (crear, leer, guardar, borrar).

---

## 🚀 Puesta en Marcha

**Requisitos**: Docker y Docker Compose.

1.  **Crear el archivo `.env`** en la raíz del proyecto con, como mínimo, las siguientes variables:

    ```env
    GROQ_API_KEY="tu_api_key_de_groq"
    MASTER_PASSWORD="tu_contraseña_maestra"
    ```

2.  **Ejecutar la aplicación**:

    ```bash
    docker compose up --build -d
    ```

3.  Abrir [http://localhost:8501](http://localhost:8501) en el navegador.

---

## 🧰 Flujo de Trabajo Típico

1.  **Selecciona un Modo**: En la barra lateral, elige la personalidad del agente que mejor se adapte a tu tarea (ej. "Ingeniero de Código").
2.  **Sube Contexto (Opcional)**: Sube un archivo existente para que el agente lo tenga en cuenta.
3.  **Genera Código**: Pide al agente que realice una tarea. Ej: "Crea un endpoint de FastAPI para obtener un usuario por su ID".
4.  **Analiza y Ejecuta**:
    - Usa los botones **Formatear** y **Validar** para asegurar la calidad del código generado.
    - Si el agente proporciona un comando de ejecución, el botón **▶️ Ejecutar** se activará. Úsalo para probar el código.
5.  **Itera y Refactoriza**: Pide al agente que añada una nueva funcionalidad o que refactorice el código. El agente puede proponerte crear un nuevo archivo o modificar uno existente. Aprueba la operación para que el agente aplique el cambio.

---

## 🧪 Calidad y Desarrollo

Para ejecutar los linters y type checkers localmente:

```bash
uv run ruff check --fix .
uv run mypy .
```
