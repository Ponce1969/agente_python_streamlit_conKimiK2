# Plan de Refactorización y Evolución del Agente Experto en Python

Este documento describe los pasos propuestos para refactorizar y mejorar la aplicación, transformándola en una herramienta de productividad más robusta y profesional para el desarrollo de backend con Python.

---

## Fase 1: Reestructuración de Arquitectura

El objetivo de esta fase es organizar el código fuente en una estructura de directorios modular y escalable. Esto mejora la mantenibilidad y facilita la adición de nuevas funcionalidades.

---

## Fase 2: Mejoras Funcionales y de Escalabilidad

Una vez establecida la nueva arquitectura, podemos empezar a añadir funcionalidades que hagan de la herramienta un verdadero "agente" de desarrollo.

### Idea A: Modos de Especialización

Implementar un selector en la interfaz de usuario (`st.selectbox`) para permitir al usuario elegir un "modo" o "personalidad" para el agente. Cada modo utilizará un `SYSTEM_PROMPT` ajustado para tareas específicas.

### Idea B: Integración de Herramientas de Desarrollo

Darle al agente la capacidad de interactuar con herramientas de línea de comandos para analizar y ejecutar código.

---

## Fase 3: Implementación de la Idea A - "Modos de Especialización"

Esta fase se centra en implementar el selector de modos para el agente, permitiendo al usuario elegir una especialización y ajustando el `SYSTEM_PROMPT` en consecuencia.

---

## Fase 4: Profesionalización de Prompts

Esta fase se centra en mejorar radicalmente la calidad y especificidad de los prompts para guiar al modelo de forma más precisa y profesional.

### 4.1: Reconstrucción de `app/llm/prompts.py`

El objetivo es refactorizar completamente el archivo de prompts para que sea más modular, mantenible y potente.

- **Modernizar `AgentMode`**: Migrar de `Enum` a `StrEnum` y utilizar nombres de rol más descriptivos y profesionales (ej. "Arquitecto Python Senior").
- **Crear Constantes Modulares**: Extraer fragmentos de texto comunes y reutilizables de los prompts (como formatos de respuesta, estándares de testing, herramientas) a constantes `Final` para asegurar consistencia y facilitar el mantenimiento.
- **Reescribir `SYSTEM_PROMPTS`**: Reemplazar los prompts existentes por versiones mucho más detalladas y técnicas, utilizando f-strings para componerlos a partir de las constantes modulares. Cada prompt incluirá:
    - Especialización y stack tecnológico detallado.
    - Patrones de arquitectura y diseño.
    - Estándares de código, testing y dependencias.
    - Ejemplos de código de alta calidad.
- **Añadir Autovalidación**: Implementar una función `validate_prompts()` que se ejecute al inicio para verificar la integridad del diccionario de prompts, asegurando que todos los modos estén definidos y no estén vacíos.

### 4.2: Centralizar la Lógica de Contexto

Para mejorar la cohesión y seguir el principio de Responsabilidad Única, se centralizará toda la lógica de construcción de prompts.

- **Crear un Helper Central**: Implementar una función `get_system_prompt(mode: AgentMode, file_context: str | None) -> str` dentro de `app/llm/prompts.py`.
- **Refactorizar `_prepare_chat_messages`**: Modificar la función en `app/ui/components.py` para que, en lugar de construir el prompt manualmente, simplemente llame al nuevo helper `get_system_prompt`. Esto delega toda la lógica de manipulación de prompts al módulo `llm`.