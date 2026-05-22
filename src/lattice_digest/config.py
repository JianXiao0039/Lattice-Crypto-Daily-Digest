from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_structured_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ModuleNotFoundError:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    return data


def load_config_bundle(config_dir: Path | None = None) -> dict[str, Any]:
    root = project_root()
    directory = config_dir or root / "config"
    return {
        "taxonomy": load_structured_file(directory / "taxonomy.yaml"),
        "keywords": load_structured_file(directory / "keywords.yaml"),
        "negative": load_structured_file(directory / "negative_keywords.yaml"),
        "sources": load_structured_file(directory / "sources.yaml"),
    }

