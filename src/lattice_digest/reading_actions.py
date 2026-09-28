"""One monthly reading action and source-evidence contract."""
from enum import StrEnum


class ReadingAction(StrEnum):
    MUST_READ = 'Must Read'
    SHOULD_SKIM = 'Should Skim'
    TRACK_LATER = 'Track Later'
    IGNORE = 'Ignore / Peripheral'


def has_source_content(record):
    abstract = str(record.get('abstract') or '').strip()
    if abstract and abstract.lower() not in {'unknown', 'todo_verify', 'n/a'} and not abstract.startswith(('TODO_VERIFY', 'model-generated')):
        return True
    for block in record.get('evidence_versions') or []:
        if isinstance(block, dict) and block.get('source_url') and block.get('evidence_type') in {'abstract', 'full_text', 'conclusion', 'source_excerpt'} and block.get('text') and block.get('provenance_strength') in {'authoritative', 'source_grounded'}:
            return True
    return False


def reading_action(record):
    if not has_source_content(record) or record.get('daily_input_defects'):
        return ReadingAction.TRACK_LATER
    label = str(record.get('priority_label') or '')
    if label in {'必须精读', 'Read today'}:
        return ReadingAction.MUST_READ
    if label in {'建议精读', 'Read this week'}:
        return ReadingAction.SHOULD_SKIM
    if label in {'可略读', '暂存', 'Skim for related work', 'Save for background'}:
        return ReadingAction.TRACK_LATER
    score = int(record.get('reading_priority_score') or record.get('reading_priority') or 0)
    return ReadingAction.MUST_READ if score >= 70 else ReadingAction.SHOULD_SKIM if score >= 50 else ReadingAction.TRACK_LATER if score >= 30 else ReadingAction.IGNORE
