"""
Agitator Rye — Backend entry point.

Run from the backend/ directory:
    python run.py
"""

import os
import sys

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
        ws_max_size=16 * 1024 * 1024,  # 16MB WebSocket message limit
    )
