# ---- Base ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# ---- Instalación de Herramientas Adicionales ----
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- Dependencias ----
COPY pyproject.toml uv.lock ./
ENV UV_HTTP_TIMEOUT=300
# Instalamos todas las dependencias (principales y de desarrollo) desde pyproject.toml
RUN uv pip install --system --no-cache-dir '.[dev]'

# ---- Código Fuente ----
COPY . .

# ---- Configuración Final ----
# Creamos el directorio para la base de datos para evitar problemas de permisos.
RUN mkdir -p /app/data

# Creamos el script de entrada directamente en el Dockerfile para asegurar los finales de línea.
RUN printf '#!/bin/sh\nchown -R appuser:appuser /app/data\nexec "$@"' > /entrypoint.sh \
    && chmod +x /entrypoint.sh

# Creamos un usuario sin privilegios para ejecutar la aplicación por seguridad.
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Exponemos el puerto de Streamlit.
EXPOSE 8501

# ---- Healthcheck ----
# Docker usará este comando para verificar que la aplicación sigue saludable.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# ---- Comando de Ejecución ----
# El script de entrada se ejecuta primero, luego el CMD.
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]