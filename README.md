<div align="center">

# 🧠 Agente de Desarrollo IA  
### *Interactivo • Pedagógico • Profesional*  
*Python 3.12+ • Streamlit • Groq*

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com/)
[![Python](https://img.shields.io/badge/python-3.12+-3776ab?style=for-the-badge&logo=python&logoColor=ffdd54)](https://python.org/)
[![Ruff](https://img.shields.io/badge/code_style-ruff-20232a?style=for-the-badge&logo=ruff&logoColor=4f46e5)](https://beta.ruff.rs)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

> Un asistente que **piensa, explica y colabora** contigo — no solo genera código.

</div>

---

## ✨ ¿Qué lo hace especial?

| Característica | Detalle |
|----------------|---------|
| **🧑‍🏫 Mentor Multi-Rol** | Elige entre 5 perfiles (Arquitecto, Auditor, Ingeniero, etc.) con explicaciones paso a paso. |
| **🩺 Diagnóstico de Código** | Análisis en tiempo real con **Ruff + MyPy**: puntuación 0-100, gráficos y enlaces a documentación. |
| **⚡ Ejecución Segura** | Detecta automáticamente el comando (`uvicorn`, `python`, etc.) y lo ejecuta bajo demanda. |
| **🛡️ Transparencia Total** | Ningún cambio en archivos se aplica sin tu aprobación explícita. |
| **📊 Persistencia & Export** | Historial en SQLite y descarga de resultados en Markdown/PDF. |

---

## 🚀 Puesta en marcha en 30 segundos

### 1. Clona y entra al repo
```bash
git clone https://github.com/tu-usuario/ia-dev-agent.git
cd ia-dev-agent

2. Configura tus variables

cp .env.example .env
# Edita .env con tu GROQ_API_KEY y MASTER_PASSWORD

3. Levanta el contenedor

docker compose up --build -d

Ahora abre 👉 http://localhost:8501

    ¿Sin Docker? Revisa la sección Instalación local (próximamente).

🧰 Flujo de trabajo típico

    Selecciona un rol en la barra lateral.

    Sube contexto (archivos .py, .txt, .pdf).

    Pide una tarea → el agente genera código + explicación del porqué.

    Revisa y analiza:

        🩺 Analizar Salud → nota, puntuación y diagnósticos detallados.

        🎨 Formatear (Ruff) → estilo uniforme en un segundo.

        ▶️ Ejecutar → solo aparece si el código es ejecutable.

    Itera: acepta o rechaza propuestas de nuevos archivos/refactorizaciones.

🏗️ Arquitectura a vuelo de pájaro

ia-dev-agent
├── app/
│   ├── llm/        # Integración con modelos de lenguaje
│   ├── core/       # Lógica central y utilidades
│   ├── ui/         # Interfaz en Streamlit
│   └── db/         # Persistencia en SQLite
├── tests/          # Suite de pruebas
├── pyproject.toml  # Dependencias y configuración
├── docker-compose.yml
└── README.md

🧪 Calidad de código

Ejecuta dentro del contenedor:
Tarea	Comando
Lint + Fix	docker compose exec chat_app uv run ruff check --fix .
Type Check	docker compose exec chat_app uv run mypy .
Tests	docker compose exec chat_app uv run pytest
📖 Filosofía

    “El protagonista eres tú; el agente, un mentor paciente.”

Este proyecto es mi laboratorio personal para practicar:

    Python moderno

    Arquitectura limpia

    Buenas prácticas sin prisas

Cada commit es un paso más en mi aprendizaje 🛠️.