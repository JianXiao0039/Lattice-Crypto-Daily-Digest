from __future__ import annotations

import argparse
from pathlib import Path

from lattice_digest.reading_queue import (
    DEFAULT_EXPORT_DIR,
    DEFAULT_STATE_PATH,
    export_obsidian,
    import_queue,
    load_import_candidates,
    load_state,
    save_state,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export the local reading queue from existing radar artifacts.")
    parser.add_argument("--latest", action="store_true", help="Import the latest available weekly/daily radar candidates first.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    state = load_state(args.state_path)
    if args.latest:
        candidates, metadata = load_import_candidates(days=args.days, data_dir=args.data_dir)
        state, summary = import_queue(state, candidates)
        state["last_import"] = metadata
        print(
            "Reading queue latest import: imported={imported}, updated={updated}, skipped={skipped}, total={total}, input={input_mode}".format(
                **summary,
                input_mode=metadata["input_mode"],
            )
        )
        if not args.dry_run:
            save_state(args.state_path, state)
            print(f"wrote: {args.state_path}")
    targets = export_obsidian(state, args.output_dir, dry_run=args.dry_run)
    if args.dry_run:
        print("DRY RUN: reading queue dashboard files were not written.")
    for path in targets:
        prefix = "would write" if args.dry_run else "wrote"
        print(f"{prefix}: {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
