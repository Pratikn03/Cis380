import subprocess
import sys
from pathlib import Path


def test_build_recommender_index_script_runs(tmp_path):
    """Smoke test: script should run from repo root without ModuleNotFoundError.

    We don't assert on produced artifacts (they may depend on local datasets),
    only that the script executes and prints its success messages.
    """

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "build_recommender_index.py"
    assert script.exists()

    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stderr
    # Basic signal that it reached the end.
    assert "Saved recommender vectors" in (proc.stdout or "")
