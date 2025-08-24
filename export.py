# export.py

"""
Módulo de exportación mejorado con tipado consistente y optimización.
"""

import io
import logging
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)


def export_md(messages: list[dict[str, Any]], quiet: bool = False) -> bytes:
    """
    Exporta el historial del chat a un archivo Markdown bien formateado.

    Args:
        messages: Lista de mensajes del chat

    Returns:
        bytes: Contenido del archivo Markdown codificado en UTF-8
    """
    if not messages:
        if not quiet:
            logger.warning("No hay mensajes para exportar a Markdown")
        return b"# Historial vacio\n"

    md_content = "# Historial del Chat - Agente Python 3.12+\n\n"

    for idx, msg in enumerate(messages, 1):
        role = msg.get("role")
        content = msg.get("content", "").strip()

        if not content:
            logger.warning(f"Mensaje {idx} sin contenido, saltando")
            continue

        if role == "user":
            md_content += f"### Usuario\n\n{content}\n\n---\n\n"
        elif role == "assistant":
            md_content += f"### Agente\n\n{content}\n\n---\n\n"
        else:
            logger.warning(f"Rol desconocido en mensaje {idx}: {role}")

    return md_content.encode("utf-8")


def export_pdf(messages: list[dict[str, Any]], quiet: bool = False) -> bytes:
    """
    Exporta el historial del chat a un archivo PDF con formato profesional.

    Args:
        messages: Lista de mensajes del chat

    Returns:
        bytes: Contenido del archivo PDF
    """
    if not messages:
        if not quiet:
            logger.warning("No hay mensajes para exportar a PDF")
        return b""

    buffer = io.BytesIO()

    try:
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
        )

        styles = getSampleStyleSheet()
        story = []

        # Título principal
        story.append(Paragraph("Historial del Chat - Agente Python 3.12+", styles["h1"]))
        story.append(Spacer(1, 0.2 * inch))

        # Estilos personalizados
        user_style = styles["BodyText"]
        assistant_style = styles["BodyText"]

        # Procesar mensajes
        valid_messages = 0
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "").replace("\n", "<br/>")

            if not content.strip():
                continue

            valid_messages += 1

            if role == "user":
                story.append(Paragraph("<b>👤 Usuario:</b>", styles["h3"]))
                story.append(Paragraph(content, user_style))
                story.append(Spacer(1, 0.1 * inch))
            elif role == "assistant":
                story.append(Paragraph("<b>🤖 Agente:</b>", styles["h3"]))
                story.append(Paragraph(content, assistant_style))
                story.append(Spacer(1, 0.2 * inch))

        if valid_messages == 0:
            story.append(Paragraph("No hay mensajes validos para mostrar.", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)

        pdf_content = buffer.getvalue()
        if not quiet:
            logger.info(f"PDF exportado exitosamente con {valid_messages} mensajes")
        return pdf_content

    except Exception as e:
        if not quiet:
            logger.error(f"Error exportando a PDF: {e}")
        return f"Error generando PDF: {str(e)}".encode()
    finally:
        buffer.close()
