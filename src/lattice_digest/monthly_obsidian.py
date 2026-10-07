"""Optional profile adapter for the published create-only Obsidian interface."""
from lattice_digest.runtime_paths import RuntimePaths
from scripts.export_obsidian_notes import main as notes_main


def export_notes(paths: RuntimePaths) -> None:
    result = notes_main(['--latest', '--state-path', str(paths.state_root / 'reading-queue.json'),
                         '--output-dir', str(paths.export_root / 'obsidian-paper-notes' / 'Papers')])
    if result:
        raise ValueError('canonical Obsidian export failed')
