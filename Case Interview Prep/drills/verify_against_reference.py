"""
Optional: confirm reference implementations satisfy practice tests.
Run from repo root: python3 drills/verify_against_reference.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType


def load(name: str, path: pathlib.Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main() -> None:
    root = pathlib.Path(__file__).resolve().parent
    drills = sorted(d for d in root.iterdir() if d.is_dir() and d.name[0:2].isdigit())
    for d in drills:
        pr = load(f"practice_{d.name}", d / "practice.py")
        rf = load(f"ref_{d.name}", d / "reference.py")
        for key, val in rf.__dict__.items():
            if key.startswith("_"):
                continue
            setattr(pr, key, val)
        src = (d / "practice.py").read_text()
        marker = 'if __name__ == "__main__":'
        assert marker in src, d.name
        tail = src.split(marker, 1)[1]
        block = marker + tail
        ns = pr.__dict__.copy()
        ns["__name__"] = "__main__"
        exec(compile(block, str(d / "practice.py"), "exec"), ns)
        print(d.name)


if __name__ == "__main__":
    main()
