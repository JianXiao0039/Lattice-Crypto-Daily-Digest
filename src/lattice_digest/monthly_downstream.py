"""Every Monthly downstream path derives from RuntimePaths."""
from __future__ import annotations
from lattice_digest.runtime_paths import RuntimePaths


def run_downstream(paths: RuntimePaths, from_date: str, to_date: str, *, obsidian: bool = False) -> None:
    from lattice_digest.reading_queue import main as queue_main
    from lattice_digest.research_artifact_export import generate_research_artifact_export
    from lattice_digest.research_progress import generate_research_progress
    window = ['--from-date', from_date, '--to-date', to_date]
    result = queue_main(['import', '--data-dir', str(paths.data_root), '--state-path',
                         str(paths.state_root / 'reading-queue.json'), *window])
    if result:
        raise ValueError('canonical reading queue import failed')
    generate_research_artifact_export(from_date=from_date, to_date=to_date,
                                     daily_data_dir=paths.data_root,
                                     output_dir=paths.export_root / 'research-artifacts')
    if obsidian:
        from lattice_digest.monthly_obsidian import export_notes
        export_notes(paths)
    generate_research_progress(from_date=from_date, to_date=to_date,
                              reading_queue=paths.state_root / 'reading-queue.json',
                              source_health_dir=paths.audit_root / 'source-health',
                              obsidian_notes_dir=paths.export_root / 'obsidian-paper-notes' / 'Papers',
                              artifact_dir=paths.export_root / 'research-artifacts',
                              output_dir=paths.export_root / 'research-progress')
