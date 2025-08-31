# 🗺️ ROADMAP de Desarrollo del Agente IA

Este documento describe el estado actual del proyecto y la hoja de ruta para sus futuras versiones, transformándolo en un producto de nivel profesional.

Diagrama de flujo de la UI del Agente Python

-┌───────────────────────────────┐
│      render_chat_interface     │
│  (orquesta todo el flujo UI)  │
└───────────────┬───────────────┘
                │
                ▼
      ┌─────────────────────┐
      │ _prepare_chat_msgs  │
      │ - Construye prompt  │
      │ - Carga mensajes    │
      │   iniciales en      │
      │   session_state     │
      └─────────┬───────────┘
                │
                ▼
      ┌─────────────────────┐
      │ _display_chat_msgs  │
      │ - Recorre session_state.messages
      │ - Muestra mensajes
      │ - Llama a _render_code_actions
      └─────────┬───────────┘
                │
                ▼
  ┌─────────────────────────────┐
  │ _render_code_actions        │
  │ - Extrae bloques de código │
  │ - Detecta <run_command>    │
  │ - Botones: Ejecutar,       │
  │   Ruff Formato/Check,      │
  │   MyPy Check               │
  │ - Actualiza session_state  │
  └─────────┬──────────────────┘
            │
            ▼
┌─────────────────────────────┐
│ _handle_chat_input          │
│ - Detecta input del usuario │
│ - Agrega mensaje a session_state.messages
│ - Llama a get_groq_response │
│ - Stream de respuesta       │
│ - Actualiza session_state.messages
└─────────────────────────────┘

Notas sobre la arquitectura

st.session_state es el eje central

Mantiene historial de mensajes (messages), chunks de archivo (file_chunks), índice actual (file_chunk_index) y resultados de análisis de código.

Cada función lee o actualiza este estado, garantizando persistencia entre interacciones de Streamlit.

Flujo de datos

_prepare_chat_msgs → Inicializa mensajes.

_display_chat_msgs → Renderiza mensajes y llama a _render_code_actions.

_render_code_actions → Analiza código y actualiza resultados en session_state.

_handle_chat_input → Procesa input de usuario, llama al LLM, agrega respuesta al historial.

Extensibilidad

Cada bloque de la UI puede extenderse (nuevas herramientas de análisis, comandos especiales, chunks de archivo).

Separación clara UI ↔ lógica ↔ estado.


Visión del Proyecto

Este repositorio implementa un asistente de programación en Python + Streamlit, con persistencia en SQLite.
El objetivo principal es aprender y practicar Python de forma profesional, usando tipado fuerte, buenas prácticas, herramientas de análisis estático y un entorno interactivo.

⚠️ Importante:
El asistente no actúa como reemplazo del programador, sino como ayudante que:

Explica conceptos.

Sugiere mejoras.

Revisa la calidad del código.

Ayuda a practicar con ejemplos claros.

Próximos Pasos

1. Reforzar la idea de ayudante, no actor.
2. Reescribir wrappers de Mypy y Ruff para integrarlos con el,
   sistema de salud.
3. Incorporar ejemplos de refactorización en vivo (antes/después).
4. Mini-retos de Python dentro del asistente (ej.: tipar una, 
   función, usar async).
5. Posibilidad de adjuntar notas personales o explicaciones dentro, 
   de la sesion .
6. Extenciones , Soporte para análisis de proyectos enteros  ,
   no solo archivos sueltos.


📖 Filosofía

El proyecto es un espacio de práctica personal.
Aquí la prioridad es:

Aprender.

Escribir código profesional.

Usar buenas prácticas modernas (tipado, testeo, análisis estático).

Iterar paso a paso, sin perder de vista que el protagonista es el programador.