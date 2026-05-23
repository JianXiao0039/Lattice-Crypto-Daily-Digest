from __future__ import annotations

from lattice_digest.config import load_config_bundle
from lattice_digest.models import make_paper_record
from lattice_digest.ranker import rank_records


def test_crossref_non_crypto_lattice_candidates_all_filter_to_d() -> None:
    configs = load_config_bundle()
    records = [
        make_paper_record(
            title="Crystal lattice defects in solid-state materials",
            abstract="The lattice structure changes phonon lattice thermal conductivity.",
            source="crossref",
            source_url="https://doi.org/10.0000/crystal",
        ),
        make_paper_record(
            title="A lattice Boltzmann method for fluid simulation",
            abstract="We study lattice fluid turbulence with a lattice gas model.",
            source="crossref",
            source_url="https://doi.org/10.0000/boltzmann",
        ),
        make_paper_record(
            title="Lattice QCD and lattice gauge theory observables",
            abstract="The paper concerns lattice quantum chromodynamics.",
            source="crossref",
            source_url="https://doi.org/10.0000/qcd",
        ),
    ]

    ranked = rank_records(records, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert {record.relevance_label for record in ranked} == {"D"}

