from fastapi import APIRouter
from app.storage.state import load_state, save_state
from app.git.diff import get_changed_files
from app.git.repo import get_current_commit
from app.parser.python_ast import parse_file
from app.analyzer.impact import analyze_impact
from app.docs.updater import update_doc_section
from pathlib import Path

router = APIRouter()

@router.post("/sync")
def sync_docs(repo_path: str):
    state = load_state()
    last_sha = state.get("last_commit")

    current_sha = get_current_commit(repo_path)
    if last_sha == current_sha:
        return {"status": "No changes"}

    changed_files = get_changed_files(repo_path, last_sha, current_sha)

    for file in changed_files:
        if not file.endswith(".py"):
            continue

        old_structure = {}  # load cached structure (v1: skip)
        new_structure = parse_file(f"{repo_path}/{file}")

        impact = analyze_impact(old_structure, new_structure)

        doc_path = Path("docs_output") / file.replace(".py", ".md")
        if not doc_path.exists():
            continue

        old_doc = doc_path.read_text()
        code_snippet = open(f"{repo_path}/{file}").read()

        new_doc = update_doc_section(old_doc, impact, code_snippet)
        doc_path.write_text(new_doc)

    save_state({"last_commit": current_sha})
    return {"updated_files": changed_files}
