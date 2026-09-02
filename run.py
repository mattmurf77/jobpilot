"""JobPilot dev server. Usage: .venv/bin/python run.py  ->  http://127.0.0.1:5151
Set PORT to run on another port (e.g. PORT=5252 .venv/bin/python run.py)."""
import os

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5151")), debug=True)
