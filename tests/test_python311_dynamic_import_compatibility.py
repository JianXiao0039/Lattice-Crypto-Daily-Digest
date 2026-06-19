from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]


def _safe_dynamic_import(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def test_track_precision_dynamic_import_supports_python311_dataclasses() -> None:
    module = _safe_dynamic_import(
        "v0_5_track_precision_python311_dynamic_import",
        ROOT / "scripts" / "evaluate_v0_5_track_precision.py",
    )

    assert module.TrackRule.__dataclass_fields__
    assert module.TrackRule.__module__ in sys.modules
    assert sys.modules[module.TrackRule.__module__] is module


def test_shadow_pilot_dynamic_import_registers_nested_modules() -> None:
    module = _safe_dynamic_import(
        "v0_5_shadow_pilot_python311_dynamic_import",
        ROOT / "scripts" / "run_v0_5_shadow_pilot.py",
    )

    assert module.SAMPLE.TrackRule.__dataclass_fields__
    assert module.SAMPLE.TrackRule.__module__ in sys.modules
    assert sys.modules[module.SAMPLE.TrackRule.__module__] is module.SAMPLE
    assert hasattr(module, "run_pilot")
