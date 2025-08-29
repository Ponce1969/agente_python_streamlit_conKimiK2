# export.py

"""
Módulo de exportación mejorado con tipado consistente y optimización.
"""

import io
import logging
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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


def markdown_to_reportlab(text: str) -> str:
    """Convierte Markdown básico a formato compatible con ReportLab Paragraphs."""
    # Reemplazar saltos de línea por <br/>
    text = text.replace('\n', '<br/>')
    # Negrita: **texto** -> <b>texto</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Cursiva: *texto* -> <i>texto</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Código en línea: `código` -> <font name="Courier">código</font>
    text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
    return text

def create_pdf_styles() -> dict[str, ParagraphStyle]:
    """Crea y devuelve los estilos de párrafo para el PDF."""
    return {
        'Title': ParagraphStyle(
            'Title', fontName='Helvetica-Bold', fontSize=24, leading=28,
            spaceAfter=20, alignment=1
        ),
        'UserRole': ParagraphStyle(
            'UserRole', fontName='Helvetica-Bold', fontSize=12, leading=14, spaceAfter=6
        ),
        'AssistantRole': ParagraphStyle(
            'AssistantRole', fontName='Helvetica-Bold', fontSize=12, leading=14, spaceAfter=6
        ),
        'Content': ParagraphStyle(
            'Body', fontName='Helvetica', fontSize=10, leading=14
        ),
        'Code': ParagraphStyle(
            'Code', fontName='Courier', fontSize=9, leading=12, leftIndent=10,
            rightIndent=10, backColor=colors.HexColor('#F0F2F6'), padding=10,
            borderRadius=5, borderPadding=5
        )
    }

def _add_message_to_story(
    msg: dict[str, Any], story: list[Any], styles: dict[str, ParagraphStyle]
) -> None:
    """Añade un único mensaje al contenido del PDF."""
    role = msg.get("role")
    content = msg.get("content", "").strip()
    if not content:
        return

    role_display, role_style = (
        ("👤 Usuario", styles['UserRole'])
        if role == "user"
        else ("🤖 Agente", styles['AssistantRole'])
    )
    bg_color = colors.lightgrey if role == "user" else colors.white
    content_paragraph = Paragraph(markdown_to_reportlab(content), styles['Content'])

    message_table = Table(
        [[Paragraph(f"<b>{role_display}</b>", role_style), content_paragraph]],
        colWidths=['15%', '85%'],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.grey),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 5),
        ]),
        hAlign='LEFT',
    )
    story.append(message_table)
    story.append(Spacer(1, 0.1 * inch))

def export_pdf(messages: list[dict[str, Any]], quiet: bool = False) -> bytes:
    """Exporta el historial del chat a un archivo PDF con formato profesional."""
    if not messages:
        if not quiet:
            logger.warning("No hay mensajes para exportar a PDF")
        return b""

    buffer = io.BytesIO()
    try:
        doc = SimpleDocTemplate(
            buffer, pagesize=letter, topMargin=inch, bottomMargin=inch,
            leftMargin=inch, rightMargin=inch
        )
        styles = create_pdf_styles()
        story = [Paragraph("Historial del Chat", styles['Title'])]

        for msg in messages:
            _add_message_to_story(msg, story, styles)

        if len(story) <= 1:
            story.append(Paragraph("No hay mensajes válidos para mostrar.", styles['Content']))

        doc.build(story)
        buffer.seek(0)
        pdf_content = buffer.getvalue()

        if not quiet:
            logger.info(f"PDF exportado con {len(messages)} mensajes")
        return pdf_content

    except Exception as e:
        if not quiet:
            logger.error(f"Error exportando a PDF: {e}")
        return f"Error generando PDF: {str(e)}".encode()
    finally:
        buffer.close()
