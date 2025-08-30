# app/core/code_tools.py

"""
Utilidades para interactuar con herramientas de calidad de código como Ruff y MyPy.
"""

import subprocess
import tempfile
import textwrap
from pathlib import Path

def _run_command(command: list[str]) -> tuple[str, bool]:
    """Ejecuta un comando de shell y captura su salida."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        return result.stdout, True
    except subprocess.CalledProcessError as e:
        # Combinar stdout y stderr para un reporte de error completo
        error_output = e.stdout + "\n" + e.stderr
        return error_output.strip(), False
    except FileNotFoundError:
        tool_name = command[0]
        return f"Error: El comando '{tool_name}' no se encontró. Asegúrate de que esté instalado y en el PATH del sistema.", False

def run_ruff_format(code: str) -> tuple[str, bool]:
    """Formatea código Python usando Ruff format."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name

    try:
        format_command = ['ruff', 'format', tmp_file_path]
        _, success = _run_command(format_command)
        if success:
            formatted_code = Path(tmp_file_path).read_text(encoding='utf-8')
            return formatted_code, True
        else:
            # Si el formateo falla, ruff no escribe en el archivo, devuelve error.
            return "Error al formatear con Ruff.", False
    finally:
        Path(tmp_file_path).unlink() # Asegurarse de borrar el archivo temporal

def run_ruff_check(code: str) -> tuple[str, bool]:
    """Valida código Python usando Ruff check."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name

    try:
        # Usamos --exit-zero para que no lance error en los hallazgos, solo en errores de ejecución
        check_command = ['ruff', 'check', '--exit-zero', tmp_file_path]
        output, _ = _run_command(check_command)
        return output if output else "✅ No se encontraron problemas con Ruff.", True
    finally:
        Path(tmp_file_path).unlink()

def run_mypy_check(code: str) -> tuple[str, bool]:
    """Valida código Python usando MyPy."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as tmp_file:
        # MyPy necesita que los imports sean válidos. Añadimos un try-except genérico
        # para que el código del snippet no falle por imports no encontrados.
        # Usamos textwrap.indent para una indentación más robusta.
        if not code.strip():
             return "✅ No se encontraron problemas de tipado con MyPy.", True

        indented_code = textwrap.indent(code, '    ')
        wrapped_code = f"try:\n{indented_code}\nexcept Exception: pass"
        tmp_file.write(wrapped_code)
        tmp_file_path = tmp_file.name

    try:
        # --ignore-missing-imports es útil para snippets
        mypy_command = ['mypy', tmp_file_path, '--ignore-missing-imports']
        output, _ = _run_command(mypy_command)
        # Limpiar la salida para no mostrar el "Success" si no hay errores
        clean_output = '\n'.join(line for line in output.splitlines() if 'Success' not in line)
        return clean_output.strip() if clean_output else "✅ No se encontraron problemas de tipado con MyPy.", True
    finally:
        Path(tmp_file_path).unlink()

def run_shell_command(command: str) -> tuple[str, bool]:
    """Ejecuta un comando de shell y captura su salida."""
    # Dividimos el comando en una lista para Popen
    command_parts = command.split()
    return _run_command(command_parts)
