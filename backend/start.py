"""GrapeHub startup helper — ensures correct working directory before uvicorn starts."""
import os
import sys

# Force CWD to the directory containing this file (backend/)
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Ensure backend/ is in PYTHONPATH
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import uvicorn

if __name__ == "__main__":
    # reload=False keeps a single clean process (avoids orphaned reloader sockets).
    # Change to reload=True during active development if desired.
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
