"""Read-only scan of scheduled/triggered/manual for scripts with frontmatter.

Uses the same frontmatter format/regex as deploy.py (the GCP provisioning script) so a
script's `---` docstring block stays the single source of truth for what a script *is*.
This module never writes to scripts - only config/config.yaml's `schedules` list (see
store.py) is ever mutated by the management API, keeping the GCP Cloud Scheduler path
(driven by this same frontmatter) completely untouched.
"""

import re
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).parent.parent
AUTOMATION_FOLDERS = ["scheduled", "triggered", "manual"]
FRONTMATTER_RE = re.compile(r'^"""[\s]*---\s*(.*?)\s*---[\s]*"""', re.DOTALL)


def parse_frontmatter(file_path: Path) -> dict[str, Any] | None:
    import yaml

    content = file_path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.search(content)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def discover_scripts() -> list[dict[str, Any]]:
    """Scan folders for scripts, returning their frontmatter plus relative path/folder."""
    discovered = []

    for folder in AUTOMATION_FOLDERS:
        folder_path = BASE_PATH / folder
        if not folder_path.exists():
            continue

        for py_file in sorted(folder_path.glob("*.py")):
            if py_file.name.startswith("_") or py_file.name == "handler.py":
                continue

            frontmatter = parse_frontmatter(py_file) or {}
            script_path = str(py_file.relative_to(BASE_PATH)).replace("\\", "/")
            discovered.append(
                {
                    "script": script_path,
                    "folder": folder,
                    "name": frontmatter.get("name", py_file.stem),
                    "frontmatter": frontmatter,
                }
            )

    return discovered
