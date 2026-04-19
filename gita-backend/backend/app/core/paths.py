"""Safe path resolution for scripts and file inputs."""

from __future__ import annotations

from pathlib import Path


def resolve_existing_file(path: Path, *, description: str = "file") -> Path:
    """
    Resolve a user-supplied path to an absolute path and ensure it exists and is a file.

    Raises:
        FileNotFoundError: If the path does not exist or is not a file.
        ValueError: If the resolved path contains suspicious traversal (rare on POSIX).
    """
    p = path.expanduser().resolve(strict=False)
    if not p.is_file():
        raise FileNotFoundError(f"{description} not found: {p}")
    return p


def resolve_path_within_optional_base(path: Path, *, base: Path | None) -> Path:
    """
    Resolve `path`; if `base` is set, require the resolved path to be under `base`
    (prevents ``../`` escape when inputs are meant to stay inside a project directory).
    """
    p = path.expanduser().resolve(strict=False)
    if base is not None:
        b = base.resolve(strict=False)
        try:
            p.relative_to(b)
        except ValueError as exc:
            raise ValueError(f"path must be under {b}: {p}") from exc
    return p
