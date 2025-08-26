# db.py

"""
Módulo de base de datos mejorado con índices, pooling y optimización.
"""

import logging
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any

from config import settings

# ------------------------------------------------------------------
# 1. Configuración
# ------------------------------------------------------------------
logger = logging.getLogger(__name__)

DB_PATH = settings.db_path
DB_DIR = os.path.dirname(DB_PATH)

@contextmanager
def get_db_connection(db_path: str = DB_PATH) -> Iterator[sqlite3.Connection]:
    """
    Context manager para conexiones de base de datos.

    Yields:
        sqlite3.Connection: Conexión a la base de datos
    """
    conn = None
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            timeout=30.0,  # Timeout para evitar bloqueos
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging para mejor performance
        conn.execute("PRAGMA synchronous = NORMAL")  # Balance entre seguridad y performance
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    """
    Inicializa la base de datos y crea las tablas e índices necesarios.
    """
    try:
        with get_db_connection() as conn:
            # Crear tabla de mensajes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Crear índices para mejorar performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages(timestamp DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_role 
                ON messages(role)
            """)

            # Crear tabla de metadata si es necesario
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Crear tabla de intentos de login
            conn.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_login_attempts_identifier_timestamp
                ON login_attempts(identifier, timestamp DESC)
            """)

            conn.commit()
            logger.info("Base de datos inicializada exitosamente")

    except sqlite3.Error as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise


def record_login_attempt(identifier: str) -> None:
    """Registra un intento de inicio de sesión en la base de datos."""
    with get_db_connection() as conn:
        conn.execute("INSERT INTO login_attempts (identifier) VALUES (?)", (identifier,))
        conn.commit()


def count_recent_login_attempts(identifier: str, window_minutes: int) -> int:
    """Cuenta los intentos de inicio de sesión recientes para un identificador."""
    window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM login_attempts WHERE identifier = ? AND timestamp > ?",
            (identifier, window_start)
        )
        # Asegurarse de que fetchone() no devuelve None
        result = cursor.fetchone()
        count = result[0] if result else 0
    return count


def purge_old_login_attempts(days: int = 7) -> None:
    """Elimina los registros de intentos de login más antiguos de 'days' días."""
    if days <= 0:
        return
    purge_date = datetime.utcnow() - timedelta(days=days)
    with get_db_connection() as conn:
        conn.execute("DELETE FROM login_attempts WHERE timestamp < ?", (purge_date,))
        conn.commit()


def save_message(role: str, content: str) -> None:
    """
    Guarda un nuevo mensaje en la base de datos.

    Args:
        role: El rol del emisor del mensaje ('user' o 'assistant').
        content: El contenido del mensaje.
    """
    with get_db_connection() as conn:
        conn.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))
        conn.commit()


def load_messages(limit: int = 20) -> list[dict[str, Any]]:
    """
    Carga los últimos 'limit' mensajes desde la base de datos para mantener
    un contexto de tamaño manejable.

    Args:
        limit: El número máximo de mensajes a cargar.

    Returns:
        Una lista de diccionarios, donde cada uno representa un mensaje,
        en orden cronológico.
    """
    with get_db_connection() as conn:
        # Obtenemos los N mensajes más recientes (vienen en orden descendente)
        cursor = conn.execute(
            "SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()

    # Invertimos la lista para que estén en orden cronológico (el más antiguo primero)
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def load_all_messages() -> list[dict[str, Any]]:
    """
    Carga todo el historial completo desde SQLite en orden cronológico.

    Returns:
        Lista de mensajes con llaves: 'role' y 'content'.
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT role, content FROM messages ORDER BY timestamp ASC"
        )
        rows = cursor.fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in rows]


def load_messages_between(start: datetime, end: datetime) -> list[dict[str, Any]]:
    """
    Carga mensajes en un rango de fechas [start, end] inclusive, en orden cronológico.

    Args:
        start: Fecha/hora de inicio del rango.
        end:   Fecha/hora de fin del rango.

    Returns:
        Lista de mensajes del rango.
    """
    # Formato compatible con SQLite DATETIME
    start_s = start.strftime("%Y-%m-%d %H:%M:%S")
    end_s = end.strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT role, content
            FROM messages
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
            """,
            (start_s, end_s),
        )
        rows = cursor.fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in rows]


def purge_old_messages(days: int) -> None:
    """
    Elimina los mensajes más antiguos de 'days' días de la base de datos.
    Esto es para mantenimiento y no afecta al contexto del chat activo.

    Args:
        days: El umbral de días para eliminar mensajes.
    """
    if not isinstance(days, int) or days <= 0:
        logger.warning(f"Se intentó purgar mensajes con un valor de días no válido: {days}")
        return

    try:
        purge_date = datetime.utcnow() - timedelta(days=days)
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM messages WHERE timestamp < ?", (purge_date,))
            conn.commit()
            logger.info(f"Se purgaron {cursor.rowcount} mensajes de más de {days} días.")
    except sqlite3.Error as e:
        logger.error(f"Error al purgar mensajes antiguos de la base de datos: {e}")


def delete_all_messages() -> None:
    """
    Elimina TODOS los mensajes de la base de datos.
    Esta es una operación destructiva.
    """
    with get_db_connection() as conn:
        conn.execute("DELETE FROM messages")
        conn.commit()
