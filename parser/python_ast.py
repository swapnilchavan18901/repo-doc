import os
from pathlib import Path

def list_python_files(repo_path: str):
    repo = Path(repo_path)
    return [
        str(p) for p in repo.rglob("*.py")
        if "venv" not in str(p)
    ]
