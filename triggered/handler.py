"""Flask handler for triggered automations."""

import importlib.util
import re
import sys
from pathlib import Path

import yaml
from flask import Flask, jsonify, request

app = Flask(__name__)
BASE_PATH = Path(__file__).parent.parent


def load_automation(file_path: str):
    """Dynamically load an automation module."""
    full_path = BASE_PATH / file_path
    spec = importlib.util.spec_from_file_location("automation", full_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["automation"] = module
    spec.loader.exec_module(module)
    return module


def discover_routes() -> dict[str, str]:
    """Discover triggered automations and their routes from frontmatter."""
    routes = {}
    triggered_path = BASE_PATH / "triggered"
    
    for py_file in triggered_path.glob("*.py"):
        if py_file.name.startswith("_") or py_file.name == "handler.py":
            continue
        
        content = py_file.read_text(encoding="utf-8")
        match = re.search(r'^"""[\s]*---\s*(.*?)\s*---[\s]*"""', content, re.DOTALL)
        
        if match:
            try:
                fm = yaml.safe_load(match.group(1))
                if fm.get("type") == "triggered" and fm.get("enabled", True):
                    path = fm.get("path", f"/{fm['name']}")
                    routes[path] = str(py_file.relative_to(BASE_PATH))
            except yaml.YAMLError:
                continue
    
    return routes


ROUTES = discover_routes()


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "routes": list(ROUTES.keys())})


@app.route("/<path:path>", methods=["GET", "POST"])
def handle_request(path):
    full_path = f"/{path}"
    
    if full_path not in ROUTES:
        return jsonify({"error": "not found", "routes": list(ROUTES.keys())}), 404
    
    try:
        module = load_automation(ROUTES[full_path])
        if hasattr(module, "main"):
            result = module.main(request.json if request.is_json else None)
            return jsonify({"status": "success", "result": result})
        return jsonify({"error": "no main() function"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
