from lattice_digest.artifact_paths import (
    daily_data_path,
    daily_digest_path,
    monthly_data_path,
    monthly_digest_path,
    weekly_data_path,
    weekly_digest_path,
)


def test_writer_path_helpers_remain_year_partitioned_canonical():
    assert daily_data_path("2026-06-23").as_posix() == "data/2026/daily/2026-06-23.json"
    assert daily_digest_path("2026-06-23").as_posix() == "digests/2026/daily/2026-06-23.md"
    assert weekly_data_path("2026-W25").as_posix() == "data/2026/weekly/2026-W25.json"
    assert weekly_digest_path("2026-W25").as_posix() == "digests/2026/weekly/2026-W25.md"
    assert monthly_data_path("2026-06").as_posix() == "data/2026/monthly/2026-06.json"
    assert monthly_digest_path("2026-06").as_posix() == "digests/2026/monthly/2026-06.md"
