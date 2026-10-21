"""Release guards, run against the BUILT distribution before upload.

The same pair kirby-world runs: this package holds no rules text, licensed
prose or campaign content (kirby-api keeps that in its own database), so the
content guards kirby-cost and kirby-combat need do not apply. What remains is
a tag that disagrees with the built version, and a distribution whose module
does not import from the wheel.

Usage: python scripts/check_release.py dist/
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

FAILURES: list[str] = []


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def bad(msg: str) -> None:
    print(f"FAIL  {msg}")
    FAILURES.append(msg)


def the_one_wheel(dist: Path) -> Path | None:
    """A stale wheel left over in a local `dist/` would get guarded here
    while `twine upload dist/*` ships every wheel present. Insist on
    exactly one so a leftover build artifact fails loudly instead of being
    silently ignored (or silently approved)."""
    wheels = sorted(dist.glob("*.whl"))
    if not wheels:
        bad("no wheel in the distribution directory")
        return None
    if len(wheels) > 1:
        bad(
            "more than one wheel in the distribution directory: "
            f"{', '.join(w.name for w in wheels)}. "
            "Clean dist/ before building for release."
        )
        return None
    return wheels[0]


def built_version(wheel: Path) -> str | None:
    m = re.match(r"kirby_campaign-([^-]+)-", wheel.name)
    if not m:
        bad(f"cannot read a version out of {wheel.name}")
        return None
    return m.group(1)


def check_tag_matches(version: str) -> None:
    """A tag that does not match the built version publishes the wrong thing."""
    ref = os.environ.get("GITHUB_REF", "")
    if not ref.startswith("refs/tags/"):
        ok("not a tagged build; skipping the tag/version check")
        return
    tag = ref.removeprefix("refs/tags/").lstrip("v")
    if tag == version:
        ok(f"tag v{tag} agrees with the built version")
    else:
        bad(f"tag v{tag} does not match the built version {version}")


def check_imports_clean(wheel: Path, version: str) -> None:
    """The wheel must import, and answer the two-tier merge and the Team ->
    Side bridge, FROM THE WHEEL. Unlike kirby-world this package imports its
    one dependency (``kirby_combat.side``) at import time, so the probe runs
    with the build environment's site-packages, where that dependency is
    installed, and asserts where kirby_campaign itself came from: an editable
    install of this repo would otherwise answer from the source tree."""
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(wheel) as z:
            z.extractall(tmp)
        probe = (
            "import os, sys;"
            "sys.path.insert(0, os.environ['EXPECTED_ROOT']);"
            "import kirby_campaign as c;"
            "assert c.__file__.startswith(os.environ['EXPECTED_ROOT']), ("
            "  'imported from ' + c.__file__ + ', not the extracted wheel'"
            ");"
            "d = {k: 'def' for k in c.TEAM_OVERRIDES};"
            "i = {**{k: None for k in c.TEAM_OVERRIDES}, 'name': '', 'is_active': True, 'status_notes': None};"
            "e = c.effective_team(d, i);"
            "assert e['name'] == '' and e['agenda'] == 'def' and e['is_active'] is True"
        )
        res = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=tmp,
            env={"PATH": os.environ.get("PATH", ""), "EXPECTED_ROOT": tmp},
            capture_output=True,
            text=True,
            check=False,
        )
    if res.returncode == 0:
        ok(f"kirby-campaign {version}: imports FROM THE WHEEL and merges a team's two tiers")
    else:
        bad(f"the built wheel does not import cleanly: {res.stderr.strip()}")


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    if not dist.is_dir():
        print(f"no such directory: {dist}")
        return 1
    wheel = the_one_wheel(dist)
    if wheel is not None:
        version = built_version(wheel)
        if version is not None:
            check_tag_matches(version)
            check_imports_clean(wheel, version)
    print()
    if FAILURES:
        print(f"{len(FAILURES)} release guard(s) failed")
        return 1
    print("all release guards passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
