"""
Quick verifier:
- Loads each `practice.py`
- Replaces missing implementations with `solution.py` symbols
- Executes practice file tests

Run from `Case Interview Prep`:
python3 drills/verify_against_solution.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType


def load(name: str, path: pathlib.Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    root = pathlib.Path(__file__).resolve().parent
    drills = sorted(
        d
        for d in root.iterdir()
        if d.is_dir()
        and d.name[:2].isdigit()
        and (d / "practice.py").exists()
        and (d / "solution.py").exists()
    )
    for d in drills:
        practice = load(f"practice_{d.name}", d / "practice.py")
        solution = load(f"solution_{d.name}", d / "solution.py")

        for key, val in solution.__dict__.items():
            if key.startswith("_"):
                continue
            setattr(practice, key, val)

        src = (d / "practice.py").read_text()
        marker = 'if __name__ == "__main__":'
        assert marker in src, f"missing main block in {d.name}"

        block = marker + src.split(marker, 1)[1]
        ns = practice.__dict__.copy()
        ns["__name__"] = "__main__"
        exec(compile(block, str(d / "practice.py"), "exec"), ns)
        print(d.name)


if __name__ == "__main__":
    main()
