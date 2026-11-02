import os
import sys
from pathlib import Path
import uvicorn

# Ensure repository root is on sys.path
_repo_root = Path(__file__).resolve().parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from backend.app.main import app

if __name__ == "__main__":
    # Dev server in AI Studio must bind to port 3000
    port = int(os.environ.get("DEFAULT_APP_PORT") or (os.environ.get("PORT") if os.environ.get("RENDER") else None) or 3000)
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=False)
