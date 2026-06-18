from __future__ import annotations

import argparse
from pathlib import Path

from lattice_digest.obsidian_scaffold import DEFAULT_OUTPUT_DIR, generate_scaffolds
from lattice_digest.reading_queue import DEFAULT_STATE_PATH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Obsidian paper notes from the local reading queue.")
    parser.add_argument("--latest", action="store_true", help="Use the current reading queue state and default output directory.")
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update-queue", action="store_true", default=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = generate_scaffolds(
        state_path=args.state_path,
        output_dir=args.output_dir,
        update_queue=args.update_queue and not args.dry_run,
        dry_run=args.dry_run,
        refresh_generated=args.latest and not args.dry_run,
    )
    entries = result["plan"]["entries"]
    print(
        "Obsidian notes export: selected={selected}, written={written}, refreshed={refreshed}, skipped_existing={skipped}".format(
            selected=len(entries),
            written=len(result["written"]),
            refreshed=len(result["refreshed"]),
            skipped=len(result["skipped_existing"]),
        )
    )
    if args.dry_run:
        print("DRY RUN: no notes written and queue state unchanged.")
    for entry in entries:
        print(f"target: {entry['path']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
