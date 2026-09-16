"""IDML -> INDD export driver.

InDesign automation is an ops dependency (the plan's landmine #4). This driver:

  * If `INDESIGN_SERVER` is configured (a `redirix`/SOAP endpoint or a local
    InDesignServer binary path), it runs `export_indesign.jsx` headless.
  * Otherwise it returns manual instructions and the script path — no InDesign,
    no export, but the translated .idml is already a valid deliverable.

We do not bundle a SOAP client; the server invocation shells out to the
configured binary. This keeps the dependency optional and explicit.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

_JSX = os.path.join(os.path.dirname(__file__), "export_indesign.jsx")
_INDD_TO_IDML_JSX = os.path.join(os.path.dirname(__file__), "indd_to_idml.jsx")


@dataclass
class ExportResult:
    ok: bool
    indd: str | None
    message: str


@dataclass
class ConvertResult:
    ok: bool
    idml: str | None
    message: str


def export(idml_path: str, out_dir: str) -> ExportResult:
    base = os.path.splitext(os.path.basename(idml_path))[0]
    indd = os.path.abspath(os.path.join(out_dir, f"{base}.indd"))
    server = os.environ.get("INDESIGN_SERVER", "").strip()

    if not server:
        return ExportResult(
            ok=False, indd=None,
            message=(
                "No INDESIGN_SERVER configured. To produce INDD, open "
                f"{idml_path} in Adobe InDesign and run {_JSX} (File > Scripts), "
                "or set INDESIGN_SERVER to an InDesign Server binary/endpoint and "
                "re-run with --export."
            ),
        )

    if not os.path.exists(server):
        return ExportResult(False, None, f"INDESIGN_SERVER path not found: {server}")

    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        server, "-script", _JSX,
        "-scriptArgs", f"idmlPath={os.path.abspath(idml_path)}",
        "-scriptArgs", f"inddPath={indd}",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as e:
        return ExportResult(False, None, f"InDesign Server invocation failed: {e}")

    if proc.returncode != 0:
        return ExportResult(False, None,
                            f"InDesign Server error: {proc.stderr.strip()[:400]}")
    return ExportResult(True, indd, "exported INDD")


def convert_to_idml(indd_path: str, out_dir: str) -> ConvertResult:
    base = os.path.splitext(os.path.basename(indd_path))[0]
    idml = os.path.abspath(os.path.join(out_dir, f"{base}.idml"))
    server = os.environ.get("INDESIGN_SERVER", "").strip()

    if not server:
        return ConvertResult(
            ok=False, idml=None,
            message=(
                "No INDESIGN_SERVER configured. Set INDESIGN_SERVER to an "
                "InDesign Server binary/endpoint to convert uploaded .indd files."
            ),
        )

    if not os.path.exists(server):
        return ConvertResult(False, None, f"INDESIGN_SERVER path not found: {server}")

    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        server, "-script", _INDD_TO_IDML_JSX,
        "-scriptArgs", f"inddPath={os.path.abspath(indd_path)}",
        "-scriptArgs", f"idmlPath={idml}",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as e:
        return ConvertResult(False, None, f"InDesign Server invocation failed: {e}")

    if proc.returncode != 0:
        return ConvertResult(False, None,
                              f"InDesign Server error: {proc.stderr.strip()[:400]}")
    return ConvertResult(True, idml, "converted INDD to IDML")
