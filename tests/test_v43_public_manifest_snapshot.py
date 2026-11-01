"""The publisher must receive the exact bounded manifest that was validated."""
from pathlib import Path
import pytest
from lattice_digest import public_report
from lattice_digest.report_gate import GateError, strict_json
from tests.test_public_report_pipeline import canonical, DAY


def test_export_hashes_generated_bytes_without_unbounded_artifact_reads(canonical, tmp_path, monkeypatch):
    output = tmp_path/'public'
    real_read = Path.read_bytes
    def unbounded_read(path):
        if path.is_relative_to(output):
            pytest.fail('public candidate reached an unbounded read')
        return real_read(path)
    monkeypatch.setattr(Path, 'read_bytes', unbounded_read)
    manifest = public_report.export(canonical, 'daily', str(DAY), output)
    checked, files = public_report.inspect_tree(output)
    assert checked == manifest and strict_json(files['manifest.json']) == manifest


def test_validated_manifest_has_no_unbounded_second_read(canonical, tmp_path, monkeypatch):
    output = tmp_path/'public'
    public_report.export(canonical, 'daily', str(DAY), output)
    target = output/'manifest.json'
    original = target.read_bytes()
    real_read = Path.read_bytes
    def substituted(path):
        if path == target:
            return b'TEST_ONLY_UNVALIDATED_MANIFEST_SECOND_READ'
        return real_read(path)
    monkeypatch.setattr(Path, 'read_bytes', substituted)
    manifest, files = public_report.inspect_tree(output)
    assert files['manifest.json'] == original
    assert strict_json(files['manifest.json']) == manifest


def test_actual_manifest_changed_during_inspection_is_rejected(canonical, tmp_path, monkeypatch):
    output = tmp_path/'public'
    public_report.export(canonical, 'daily', str(DAY), output)
    real_catalog = public_report.validate_catalog
    def changed(manifest, files):
        real_catalog(manifest, files)
        # Actual valid-JSON whitespace mutation after the first bounded read.
        with (output/'manifest.json').open('ab') as stream:
            stream.write(b' ')
    monkeypatch.setattr(public_report, 'validate_catalog', changed)
    with pytest.raises(GateError) as failure:
        public_report.inspect_tree(output)
    assert failure.value.code == 'PAIR_HASH_MISMATCH'
