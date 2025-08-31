# app/core/code_tools.py

"""
Utilidades para interactuar con herramientas de calidad de código como Ruff y MyPy.
"""

import json
import re
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class Diagnostic:
    """Representa un diagnóstico (error o advertencia) de una herramienta de linting."""

    tool: str
    message: str
    code: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None


def _run_command(command: list[str]) -> tuple[str, bool]:
    """Ejecuta un comando de shell y captura su salida."""
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=False, encoding="utf-8"
        )
        if result.returncode == 0:
            return result.stdout, True
        else:
            # Para ruff en modo JSON, el output de error está en stdout
            # Para otros, puede estar en stderr
            error_output = result.stdout or result.stderr
            return error_output.strip(), False
    except FileNotFoundError:
        tool_name = command[0]
        error_msg = (
            f"Error: El comando '{tool_name}' no se encontró. Asegúrate de que esté "
            "instalado y en el PATH del sistema."
        )
        return error_msg, False


def run_ruff_format(code: str) -> tuple[str, bool]:
    """Formatea código Python usando Ruff format."""
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name

    try:
        format_command = ["ruff", "format", tmp_file_path]
        output, success = _run_command(format_command)
        if success:
            formatted_code = Path(tmp_file_path).read_text(encoding="utf-8")
            return formatted_code, True
        else:
            return f"Error al formatear con Ruff: {output}", False
    finally:
        Path(tmp_file_path).unlink()


def run_ruff_check(code: str) -> tuple[list[Diagnostic], bool]:
    """Valida código Python usando Ruff check y devuelve una lista de diagnósticos."""
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name

    diagnostics = []
    try:
        check_command = ["ruff", "check", "--format", "json", "--exit-zero", tmp_file_path]
        output, _ = _run_command(check_command)
        
        if not output.strip():
            return [], True

        data = json.loads(output)
        for item in data:
            diagnostics.append(
                Diagnostic(
                    tool="Ruff",
                    code=item.get("code"),
                    message=item.get("message", ""),
                    line=item.get("location", {}).get("row"),
                    column=item.get("location", {}).get("column"),
                )
            )
        return diagnostics, True
    except json.JSONDecodeError:
        return [Diagnostic(tool="Ruff", message=f"Error: La salida de Ruff no es un JSON válido.\n{output}")], False
    except Exception as e:
        return [Diagnostic(tool="Ruff", message=f"Error inesperado al ejecutar Ruff: {e}")], False
    finally:
        Path(tmp_file_path).unlink()


def run_mypy_check(code: str) -> tuple[list[Diagnostic], bool]:
    """Valida código Python usando MyPy y devuelve una lista de diagnósticos."""
    diagnostics = []
    if not code.strip():
        return [], True

    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp_file:
        indented_code = textwrap.indent(code, '    ')
        wrapped_code = f"try:\n{indented_code}\nexcept Exception: pass"
        tmp_file.write(wrapped_code)
        tmp_file_path = tmp_file.name

    try:
        mypy_command = ["mypy", tmp_file_path, "--ignore-missing-imports"]
        output, _ = _run_command(mypy_command)

        if "Success: no issues found" in output:
            return [], True

        # Regex para parsear la salida de MyPy: file:line:col: type: message [code]
        pattern = re.compile(r"[^:]+:(\d+):(?:(\d+):)? (error|note|warning): (.+?)(?:\s+\[(.+)\])?")
        for line in output.splitlines():
            match = pattern.match(line)
            if match:
                diagnostics.append(
                    Diagnostic(
                        tool="MyPy",
                        line=int(match.group(1)),
                        column=int(match.group(2)) if match.group(2) else None,
                        message=match.group(4).strip(),
                        code=match.group(5),
                    )
                )
        return diagnostics, True
    except Exception as e:
        return [Diagnostic(tool="MyPy", message=f"Error inesperado al ejecutar MyPy: {e}")], False
    finally:
        Path(tmp_file_path).unlink()


def run_shell_command(command: str) -> tuple[str, bool]:
    """Ejecuta un comando de shell y captura su salida."""
    command_parts = command.split()
    return _run_command(command_parts)
