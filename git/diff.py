import subprocess

def get_changed_files(repo_path, old_sha, new_sha):
    cmd = ["git", "diff", "--name-only", old_sha, new_sha]
    result = subprocess.check_output(cmd, cwd=repo_path)
    return result.decode().splitlines()
