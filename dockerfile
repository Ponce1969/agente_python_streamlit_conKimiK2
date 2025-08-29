# ---- Base ----
# Usamos una imagen oficial de uv para Python 3.12.
# Esto nos da Python y uv en un solo paso, simplificando el build.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# ---- Instalación de Herramientas Adicionales ----
# La imagen base es mínima y no incluye curl, que es necesario para el healthcheck.
# Lo instalamos aquí, y limpiamos la caché de apt para mantener la imagen pequeña.
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- Dependencias ----
# Copiamos solo los archivos de dependencias primero.
# Docker cacheará este paso si los archivos no cambian, acelerando builds futuros.
COPY pyproject.toml uv.lock ./

# Instalamos las dependencias usando uv.
# --system para instalarlas en el entorno global de Python del contenedor.
RUN uv pip install --system --no-cache-dir .

# ---- Código Fuente ----
# Copiamos el resto del código de la aplicación.
COPY . .

# ---- Configuración Final ----
# Creamos el directorio para la base de datos para evitar problemas de permisos.
# Le damos permisos al usuario no-root que crea Streamlit.
RUN mkdir -p /app/data && chown -R 1001:1001 /app/data

# Exponemos el puerto de Streamlit.
EXPOSE 8501

# Comando para ejecutar la aplicación.
# Usamos 'python -m streamlit' para asegurar que el PYTHONPATH es correcto
# después de la refactorización a la carpeta 'app'.
CMD ["python", "-m", "streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]