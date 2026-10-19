"""CI language-floor and real-history availability boundaries; no remote calls."""
import ast
import sys
from pathlib import Path

import pytest

from lattice_digest.consequence_graph_v3 import _normal, _any
from tests.test_v3_real_history_e2e import history_case, history_unavailable_reason, required_history_inputs, seed


def fstring_backslash_expressions(source):
    """3.13's best-effort feature_version parser misses this 3.11 restriction."""
    return [(node.lineno,ast.get_source_segment(source,node.value))
            for node in ast.walk(ast.parse(source)) if isinstance(node,ast.FormattedValue)
            and '\\' in (ast.get_source_segment(source,node.value) or '')]


def test_all_production_sources_parse_at_python311_language_floor():
    root=Path(__file__).resolve().parents[1]/'src'
    files=list(root.rglob('*.py'))
    assert files
    for p in files:
        source=p.read_text('utf-8-sig')
        ast.parse(source,filename=str(p),feature_version=(3,11))
        assert not fstring_backslash_expressions(source), str(p)


def test_canary_recognizes_old_fstring_backslash_error_without_executing_it():
    old='def old(value):\n    return f" {re.sub(r\'\\s+\', \' \', value).strip()} "\n'
    if sys.version_info < (3,12):
        with pytest.raises(SyntaxError,match=r'f-string.*backslash'):
            ast.parse(old)
    else:
        assert fstring_backslash_expressions(old)
    assert not fstring_backslash_expressions('def fixed(value):\n    return f" {value} "\n')


@pytest.mark.parametrize('value,expected',[
    (' ML--KEM\n\tkey_generation! ',' ml kem key generation '),
    ('LWE_64.2?',' lwe 64 2 '),('', '  '),(' \n\t!!! ', '  '),
    ('NTRU+ / Falcon',' ntru falcon '),('ABCdef',' abcdef '),
])
def test_normalization_behavior_unchanged(value,expected):
    assert _normal(value)==expected


@pytest.mark.parametrize('text,term,expected',[
    ('lattices','lattice',True),('signatures','signature',True),
    ('trapdoors','trapdoor',True),('ML-KEM implementation','ML KEM',True),
    ('notlattice','lattice',False),('signaturex','signature',False),
    ('embeddedlatticesvalue','lattice',False),('LWE','RLWE',False),
])
def test_relation_matching_boundaries_preserved(text,term,expected):
    assert _any(_normal(text),term) is expected


@pytest.mark.parametrize('kind',['daily','weekly','monthly'])
def test_unavailable_approved_python_marks_history_skip_before_fixtures(tmp_path,kind):
    missing=tmp_path/'missing-production-python.exe'
    reason=history_unavailable_reason(kind,source_root=tmp_path,python=missing)
    assert 'Python 3.13' in reason
    case=history_case(kind,source_root=tmp_path,python=missing)
    mark=next(m for m in case.marks if m.name=='skipif')
    assert mark.args==(True,) and mark.kwargs['reason']==reason


@pytest.mark.parametrize('kind',['daily','weekly','monthly'])
def test_missing_corpus_is_explicit_skip_not_empty_success(tmp_path,kind):
    python=tmp_path/'approved-python.exe';python.write_bytes(b'AVAILABILITY_ONLY_NOT_EXECUTED')
    reason=history_unavailable_reason(kind,source_root=tmp_path/'absent-corpus',python=python)
    assert 'required local input files are absent' in reason


@pytest.mark.parametrize('kind',['daily','weekly','monthly'])
def test_available_inputs_do_not_skip_or_weaken_real_content_assertions(tmp_path,kind):
    python=tmp_path/'approved-python.exe';python.write_bytes(b'AVAILABILITY_ONLY_NOT_EXECUTED')
    source=tmp_path/'source'
    for p in required_history_inputs(kind,source):
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'not a valid report')
    # The gate checks availability only. Actual E2E still parses/validates the bytes.
    assert history_unavailable_reason(kind,source_root=source,python=python) is None
    case=history_case(kind,source_root=source,python=python)
    assert next(m for m in case.marks if m.name=='skipif').args==(False,)


def test_snapshot_copy_is_independent_of_canonical_inode(tmp_path,monkeypatch):
    import tests.test_v3_real_history_e2e as history
    source=tmp_path/'source';original=source/'data/2026/daily/2026-10-05.json'
    original.parent.mkdir(parents=True);original.write_bytes(b'ORIGINAL')
    monkeypatch.setattr(history,'CAN',source)
    snapshot=tmp_path/'scratch';rows=seed(snapshot,'2026-10-05','2026-10-05')
    assert len(rows)==1
    copied=Path(rows[0]['snapshot']);assert copied.read_bytes()==b'ORIGINAL'
    copied.write_bytes(b'SCRATCH_MUTATION')
    assert original.read_bytes()==b'ORIGINAL'


def test_historical_execution_evidence_has_no_global_sealed_output_root():
    import tests.test_v3_real_history_e2e as history
    assert not hasattr(history,'E')
    source=Path(history.__file__).read_text('utf-8')
    assert "E=tmp_path/'execution-evidence'" in source
    assert '.ops/evidence/digest-v3-20261019' not in source
