from __future__ import annotations

from lattice_digest.config import load_config_bundle


def test_sources_encode_required_recall_and_reliability_rules() -> None:
    configs = load_config_bundle()
    sources = {source["name"]: source for source in configs["sources"]["sources"]}

    assert sources["iacr_eprint"]["max_per_day"] == 1
    assert sources["iacr_eprint"]["max_requests_per_day"] == 1
    assert sources["iacr_eprint"]["cache_ttl_hours"] == 24
    assert sources["iacr_eprint"]["trust_level"] == "high"
    assert sources["iacr_eprint"]["priority"] == 100

    arxiv = sources["arxiv"]
    assert set(arxiv["categories"]) >= {"cs.CR", "cs.IT", "math.NT", "math.CO", "cs.DS", "cs.LG"}
    assert "cs_lg_required_context" in arxiv
    assert {"LWE", "SIS", "BKZ", "PQC"} <= set(arxiv["cs_lg_required_context"])
    assert {"sieving", "enumeration", "G6K", "fplll"} <= set(arxiv["query_terms"])

    dblp_venues = set(sources["dblp"]["venues"])
    assert {"CRYPTO", "EUROCRYPT", "ASIACRYPT", "TCC", "PKC", "CHES", "TCHES"} <= dblp_venues
    assert {"CCS", "USENIX Security", "IEEE S&P", "NDSS", "PQCrypto"} <= dblp_venues
    assert {"SAC", "CANS"} <= dblp_venues

    assert sources["crossref"]["role"] == "supplemental_only"
    assert sources["crossref"]["must_pass_strong_relevance_filter"] is True
    assert sources["crossref"]["require_strong_crypto_context"] is True
    assert sources["semantic_scholar"]["exclude_year_only_from_since_window"] is True
    assert sources["openalex"]["on_http_429"] == "warning_only"


def test_negative_config_contains_required_hard_false_positive_terms() -> None:
    configs = load_config_bundle()
    hard_negative = configs["negative"]["hard_negative"]
    flattened = {
        term.lower()
        for terms in hard_negative.values()
        for term in terms
    }

    for term in [
        "crystal lattice",
        "lattice qcd",
        "lattice boltzmann",
        "lattice gauge theory",
        "spin lattice",
        "optical lattice",
        "phonon lattice",
        "oxygen lattice",
        "materials lattice",
        "solid-state lattice",
        "lattice protein",
        "tissue lattice",
        "neural lattice in neuroscience",
        "epidemiological sis",
        "susceptible infected susceptible",
        "sis epidemic",
        "network sis model",
        "sis model in epidemiology",
        "sis dynamics",
        "social lattice",
        "graph lattice",
        "cellular lattice",
        "lattice random walk",
        "lattice animal",
        "lattice point counting",
    ]:
        assert term in flattened
