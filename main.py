import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env from backend/.env or root .env
backend_env = Path(__file__).resolve().parent / "backend" / ".env"
root_env = Path(__file__).resolve().parent / ".env"
if backend_env.exists():
    load_dotenv(backend_env)
elif root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

from backend.main import app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
