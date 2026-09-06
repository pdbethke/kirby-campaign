"""Executes every script in `examples/` and asserts it completes.

Nothing else imports or runs `examples/`, so a script there can silently
bit-rot behind a fully green suite. Same guard kirby-combat carries.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_EXAMPLES_DIR = _REPO_ROOT / "examples"
_EXAMPLE_SCRIPTS = sorted(_EXAMPLES_DIR.glob("*.py"))


def test_examples_directory_is_not_empty():
    assert _EXAMPLE_SCRIPTS, "no example scripts found under examples/"


@pytest.mark.parametrize(
    "script", _EXAMPLE_SCRIPTS, ids=lambda p: p.name,
)
def test_example_runs_to_completion(script: pathlib.Path):
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=_REPO_ROOT, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, (
        f"{script.name} exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert result.stdout.strip(), f"{script.name} printed nothing"
