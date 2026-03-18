# Copyright 2026 by GuidoGerb Publishing, LLC
"""Package an MCP server for AWS Lambda deployment.

Creates a zip archive containing the ``mcp/`` package and the
server module, ready to upload to Lambda.  No Node.js or npm involved.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def package_lambda(
    output_path: Path | None = None,
    extra_dirs: list[Path] | None = None,
) -> Path:
    """Create a Lambda deployment zip.

    Parameters
    ----------
    output_path:
        Where to write the zip.  Defaults to ``dist/mcp-lambda.zip``.
    extra_dirs:
        Additional directories to include in the zip at their relative
        paths from the project root.

    Returns
    -------
    The path to the created zip file.
    """
    project_root = ROOT.parent
    if output_path is None:
        output_path = project_root / "dist" / "mcp-lambda.zip"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Include the entire mcp/ package
        mcp_dir = project_root / "mcp"
        for py_file in sorted(mcp_dir.rglob("*.py")):
            arcname = str(py_file.relative_to(project_root))
            zf.write(py_file, arcname)

        # Include any extra directories
        for extra in extra_dirs or []:
            abs_dir = project_root / extra
            if abs_dir.is_dir():
                for f in sorted(abs_dir.rglob("*.py")):
                    arcname = str(f.relative_to(project_root))
                    zf.write(f, arcname)

    output_path.write_bytes(buf.getvalue())
    return output_path
