from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_structured_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}

    try:
        data = json.loads(text)
    except json.JSONDecodeError as json_error:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise ValueError(
                f"{path} is not valid JSON and PyYAML is not installed; "
                "install pyyaml or use JSON-compatible configuration."
            ) from exc

        try:
            data = yaml.safe_load(text)
        except Exception as yaml_error:  # noqa: BLE001 - include both parser failures with the path.
            raise ValueError(
                f"{path} is neither valid JSON nor valid YAML: "
                f"JSON error: {json_error}; YAML error: {yaml_error}"
            ) from yaml_error
    if data is None:
        return {}
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
