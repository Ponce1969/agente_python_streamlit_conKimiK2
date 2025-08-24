# file_handler.py

"""
Manejador de archivos mejorado con validaciones y optimización.
"""

import logging
from io import BytesIO

import streamlit as st
from pypdf import PdfReader

logger = logging.getLogger(__name__)

# Definir límites de forma más flexible
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Tipos de archivo soportados
SUPPORTED_EXTENSIONS = {"py", "txt", "md", "csv", "pdf"}


class FileProcessor:
    """Clase para procesar archivos de forma segura y eficiente."""

    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """
        Valida que el archivo no exceda el tamaño máximo permitido.

        Args:
            file_size: Tamaño del archivo en bytes

        Returns:
            bool: True si el archivo es válido, False en caso contrario
        """
        return file_size <= MAX_FILE_SIZE_BYTES

    @staticmethod
    def validate_file_extension(file_name: str) -> bool:
        """
        Valida que la extensión del archivo esté soportada.

        Args:
            file_name: Nombre del archivo

        Returns:
            bool: True si la extensión es válida, False en caso contrario
        """
        extension = file_name.split(".")[-1].lower()
        return extension in SUPPORTED_EXTENSIONS

    @staticmethod
    def extract_text_from_file(
        uploaded_file: st.runtime.uploaded_file_manager.UploadedFile,
    ) -> tuple[str | None, str | None]:
        """
        Extrae texto de un archivo según su tipo.

        Args:
            uploaded_file: Archivo subido desde Streamlit

        Returns:
            Tupla (contenido, error_mensaje)
        """
        file_name = uploaded_file.name
        file_extension = file_name.split(".")[-1].lower()

        try:
            if file_extension in ["py", "txt", "md", "csv"]:
                content = uploaded_file.getvalue().decode("utf-8")
                return content, None

            elif file_extension == "pdf":
                pdf_bytes = BytesIO(uploaded_file.getvalue())
                pdf_reader = PdfReader(pdf_bytes)

                # Validar que el PDF tenga páginas
                if len(pdf_reader.pages) == 0:
                    return None, "El PDF está vacío"

                # Extraer texto de todas las páginas
                content = "\n".join(page.extract_text() or "" for page in pdf_reader.pages).strip()

                if not content:
                    return None, "No se pudo extraer texto del PDF"

                return content, None

            else:
                return None, f"Extensión de archivo no soportada: .{file_extension}"

        except UnicodeDecodeError:
            return (
                None,
                (
                    f"Error de codificación en el archivo '{file_name}'. "
                    f"Asegúrate de que esté en UTF-8"
                ),
            )
        except Exception as e:
            logger.error(f"Error procesando archivo {file_name}: {e}")
            return None, f"Error procesando el archivo '{file_name}': {str(e)}"


def process_uploaded_file(
    uploaded_file: st.runtime.uploaded_file_manager.UploadedFile,
) -> tuple[str | None, str | None]:
    """
    Procesa un archivo subido, valida su tamaño y extrae su contenido de texto.

    Args:
        uploaded_file: El archivo subido desde Streamlit.

    Returns:
        Una tupla (contenido, error_mensaje).
        - `contenido`: El texto extraído del archivo si el procesamiento es exitoso.
        - `error_message`: Un mensaje de error si ocurre algún problema.
    """
    if not uploaded_file:
        return None, "No se ha subido ningún archivo."

    file_name = uploaded_file.name
    file_size = uploaded_file.size

    # Validar tamaño
    if not FileProcessor.validate_file_size(file_size):
        error_msg = (
            f"El archivo '{file_name}' es demasiado grande "
            f"({file_size / 1024 / 1024:.2f} MB). "
            f"El tamaño máximo permitido es de {MAX_FILE_SIZE_MB} MB."
        )
        return None, error_msg

    # Validar extensión
    if not FileProcessor.validate_file_extension(file_name):
        return None, f"Tipo de archivo no soportado: {file_name}"

    # Procesar archivo
    content, error = FileProcessor.extract_text_from_file(uploaded_file)

    if content:
        logger.info(f"Archivo procesado exitosamente: {file_name} ({len(content)} caracteres)")

    return content, error
