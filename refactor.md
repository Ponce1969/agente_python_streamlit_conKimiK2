# Plan de Refactorización y Evolución del Agente Experto en Python

Este documento describe los pasos propuestos para refactorizar y mejorar la aplicación, transformándola en una herramienta de productividad más robusta y profesional para el desarrollo de backend con Python.

---

## Fase 1: Reestructuración de Arquitectura

El objetivo de esta fase es organizar el código fuente en una estructura de directorios modular y escalable. Esto mejora la mantenibilidad y facilita la adición de nuevas funcionalidades.

### Nueva Estructura de Directorios Propuesta

```
/agentes
├── .streamlit/
│   └── config.toml
├── app/
│   ├── __init__.py
│   ├── main.py             # Punto de entrada principal de Streamlit
│   ├── config.py           # Configuración centralizada
│   ├── styles.py           # Estilos visuales
│   ├── core/
│   │   ├── __init__.py
│   │   ├── file_handler.py # Lógica para manejar archivos
│   │   └── utils.py        # Funciones de utilidad
│   ├── db/
│   │   ├── __init__.py
│   │   └── persistence.py  # Lógica de interacción con la base de datos
│   ├── llm/
│   │   ├── __init__.py
│   │   └── llm_handler.py  # Lógica para interactuar con el LLM
│   └── ui/
│       ├── __init__.py
│       └── components.py   # Componentes de la interfaz de Streamlit
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
└── refactor.md
```

---

## Fase 2: Mejoras Funcionales y de Escalabilidad

Una vez establecida la nueva arquitectura, podemos empezar a añadir funcionalidades que hagan de la herramienta un verdadero "agente" de desarrollo.

### Idea A: Modos de Especialización

Implementar un selector en la interfaz de usuario (`st.selectbox`) para permitir al usuario elegir un "modo" o "personalidad" para el agente. Cada modo utilizará un `SYSTEM_PROMPT` ajustado para tareas específicas.

*   **Modo "Generador de Código":** Optimizado para crear endpoints de FastAPI, modelos Pydantic, etc.
*   **Modo "Analista de Seguridad":** Enfocado en revisar código en busca de vulnerabilidades (ej. uso de `argon2`, inyección de dependencias en FastAPI).
*   **Modo "Experto en Base de Datos":** Especializado en generar consultas SQL para PostgreSQL y ayudar en el diseño de esquemas.
*   **Modo "Debugger y Refactor":** Ayuda a depurar y refactorizar código existente.

### Idea B: Integración de Herramientas de Desarrollo

Darle al agente la capacidad de interactuar con herramientas de línea de comandos para analizar y ejecutar código.

1.  **Ejecución de Código:** Añadir un botón "▶️ Ejecutar" que tome el código generado y lo ejecute de forma segura dentro del contenedor Docker, mostrando la salida (stdout/stderr) en la UI.
2.  **Análisis de Calidad de Código:** Integrar botones para:
    *   **"Validar con MyPy":** Ejecuta `mypy` sobre el código y muestra los errores de tipado.
    *   **"Formatear/Linter con Ruff":** Ejecuta `ruff` para formatear y detectar problemas de estilo y errores comunes.
3.  **Gestión de Archivos del Proyecto:** Permitir al agente proponer la creación o modificación de archivos en el espacio de trabajo, con una confirmación del usuario.

---

## Roadmap Sugerido

Se recomienda seguir los siguientes pasos para una evolución ordenada del proyecto:

1.  **Implementar la Fase 1:** Realizar la reestructuración de la arquitectura. Es la base que facilitará todo lo demás.
2.  **Implementar la Idea B.2 (Integración con MyPy/Ruff):** Esta es una mejora de alto impacto y relativamente sencilla que aporta un valor inmenso al flujo de trabajo.
3.  **Implementar la Idea A (Modos de Especialización):** Añadir esta capa de inteligencia contextual hará que el agente sea mucho más preciso y útil.
4.  **Explorar la Idea B.1 y B.3 (Ejecución de código y Gestión de archivos):** Estas son las funcionalidades más avanzadas y requieren consideraciones de seguridad adicionales, pero completarían la visión de un agente de desarrollo totalmente interactivo.
