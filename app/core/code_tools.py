# app/core/code_tools.py

"""
Utilidades para interactuar con herramientas de calidad de código como Ruff y MyPy.
Incluye análisis, formateo y generación de informes de salud del código.
"""

import json
import re
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# ==========================
#   MODELOS DE DATOS
# ==========================

@dataclass
class Diagnostic:
    """Representa un diagnóstico (error, advertencia o nota) de una herramienta de análisis."""
    tool: str
    message: str
    severity: str  # "error", "warning", "note", "info"
    code: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None


@dataclass
class CodeHealthReport:
    """Contiene un informe completo sobre la calidad de un fragmento de código."""
    diagnostics: List[Diagnostic]
    score: int       # Puntuación de 0 a 100
    grade: str       # Nota en formato letra (A+, B, C-, etc.)
    summary: str


# ==========================
#   FUNCIONES INTERNAS
# ==========================

def _score_to_grade(score: int) -> str:
    """Convierte una puntuación numérica a una nota en formato letra."""
    if score >= 95:
        return "A+"
    if score >= 90:
        return "A"
    if score >= 85:
        return "B+"
    if score >= 80:
        return "B"
    if score >= 75:
        return "C+"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _calculate_health_report(diagnostics: List[Diagnostic]) -> CodeHealthReport:
    """Calcula la puntuación, nota y resumen a partir de una lista de diagnósticos."""
    score = 100
    severity_weights = {"error": 5, "warning": 2, "note": 1, "info": 1}

    for diag in diagnostics:
        score -= severity_weights.get(diag.severity, 1)

    score = max(0, score)
    grade = _score_to_grade(score)

    error_count = sum(1 for d in diagnostics if d.severity == "error")
    warning_count = sum(1 for d in diagnostics if d.severity == "warning")

    summary = (
        f"Análisis completado. "
        f"Se encontraron {error_count} errores y {warning_count} advertencias."
    )

    return CodeHealthReport(
        diagnostics=diagnostics,
        score=score,
        grade=grade,
        summary=summary,
    )


def _run_command(command: List[str]) -> Tuple[str, bool]:
    """Ejecuta un comando de shell y captura su salida."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
        )
        if result.returncode in [0, 1] and result.stdout:
            return result.stdout, True
        elif result.returncode == 0:
            return result.stdout, True
        else:
            return (result.stdout or result.stderr).strip(), False
    except FileNotFoundError:
        return (
            f"Error: El comando '{command[0]}' no se encontró. "
            "Asegúrate de que esté instalado y en el PATH del sistema.",
            False,
        )


# ==========================
#   FUNCIONES PÚBLICAS
# ==========================

def analyze_code_health(code: str) -> CodeHealthReport:
    """Realiza un análisis de salud completo del código, combinando Ruff y MyPy."""
    ruff_diags, _ = run_ruff_check(code)
    mypy_diags, _ = run_mypy_check(code)

    all_diagnostics = sorted(
        ruff_diags + mypy_diags,
        key=lambda d: (d.line or 0, d.column or 0),
    )

    return _calculate_health_report(all_diagnostics)


def run_ruff_format(code: str) -> Tuple[str, bool]:
    """Formatea código Python usando Ruff format."""
    with tempfile.NamedTemporaryFile(
        mode="w+",
        suffix=".py",
        delete=False,
        encoding="utf-8",
    ) as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name

    try:
        output, success = _run_command(["ruff", "format", tmp_file_path])
        if success:
            formatted_code = Path(tmp_file_path).read_text(encoding="utf-8")
            return formatted_code, True
        return f"Error al formatear con Ruff: {output}", False
    finally:
        Path(tmp_file_path).unlink()


def run_ruff_check(code: str) -> Tuple[List[Diagnostic], bool]:
    """Valida código Python usando Ruff check y devuelve una lista de diagnósticos."""
    with tempfile.NamedTemporaryFile(
        mode="w+",
        suffix=".py",
        delete=False,
        encoding="utf-8",
    ) as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name

    diagnostics: List[Diagnostic] = []
    try:
        # Intentar con la sintaxis moderna
        try:
            output, _ = _run_command([
                "ruff", "check", tmp_file_path,
                "--output-format", "json", "--exit-zero",
            ])
            data = json.loads(output)
        except (json.JSONDecodeError, Exception):
            # Fallback a la sintaxis antigua
            output, _ = _run_command([
                "ruff", "check", tmp_file_path,
                "--format", "json", "--exit-zero",
            ])
            data = json.loads(output)

        if not output.strip():
            return [], True

        for item in data:
            diagnostics.append(
                Diagnostic(
                    tool="Ruff",
                    code=item.get("code"),
                    message=item.get("message", ""),
                    severity=item.get("level", "warning").lower(),
                    line=item.get("location", {}).get("row"),
                    column=item.get("location", {}).get("column"),
                )
            )
        return diagnostics, True
    except json.JSONDecodeError:
        msg = f"Error: La salida de Ruff no es un JSON válido.\n{output}"
        return [Diagnostic(tool="Ruff", message=msg, severity="error")], False
    except Exception as e:
        return [Diagnostic(tool="Ruff", message=f"Error inesperado: {e}", severity="error")], False
    finally:
        Path(tmp_file_path).unlink()


def run_mypy_check(code: str) -> Tuple[List[Diagnostic], bool]:
    """Valida código Python usando MyPy y devuelve una lista de diagnósticos."""
    if not code.strip():
        return [], True

    with tempfile.NamedTemporaryFile(
        mode="w+",
        suffix=".py",
        delete=False,
        encoding="utf-8",
    ) as tmp_file:
        indented_code = textwrap.indent(code, "    ")
        wrapped_code = f"try:\n{indented_code}\nexcept Exception: pass"
        tmp_file.write(wrapped_code)
        tmp_file_path = tmp_file.name

    diagnostics: List[Diagnostic] = []
    try:
        output, _ = _run_command(["mypy", tmp_file_path, "--ignore-missing-imports"])

        if "Success: no issues found" in output:
            return [], True

        pattern = re.compile(
            r"[^:]+:(?P<line>\d+):(?:(?P<col>\d+):)?\s"
            r"(?P<severity>error|note|warning):\s(?P<msg>.+?)"
            r"(?:\s+\[(?P<code>[a-zA-Z0-9-]+)\])?"
        )
        for line in output.splitlines():
            match = pattern.match(line)
            if match:
                diagnostics.append(
                    Diagnostic(
                        tool="MyPy",
                        line=int(match.group("line")),
                        column=int(match.group("col")) if match.group("col") else None,
                        severity=match.group("severity").lower(),
                        message=match.group("msg").strip(),
                        code=match.group("code"),
                    )
                )
        return diagnostics, True
    except Exception as e:
        return [Diagnostic(tool="MyPy", message=f"Error inesperado: {e}", severity="error")], False
    finally:
        Path(tmp_file_path).unlink()


def run_shell_command(command: str) -> Tuple[str, bool]:
    """Ejecuta un comando de shell y captura su salida."""
    return _run_command(command.split())

