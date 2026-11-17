from datetime import date

from pipeline.lake.keys import generate_bronze_key, generate_bronze_prefix


def test_generate_generate_bronze_key_layout() -> None:
    key = generate_bronze_key("adzuna", date(2026, 11, 17), "run-001")

    assert key == "bronze/source=adzuna/dt=2026-11-17/run-001.json"


def test_same_inputs_give_same_key() -> None:
    first = generate_bronze_key("remotive", date(2026, 1, 5), "abc")
    second = generate_bronze_key("remotive", date(2026, 1, 5), "abc")

    assert first == second


def test_generate_generate_bronze_prefix_with_and_without_date() -> None:
    assert generate_bronze_prefix("adzuna") == "bronze/source=adzuna/"
    assert generate_bronze_prefix("adzuna", date(2026, 11, 17)) == (
        "bronze/source=adzuna/dt=2026-11-17/"
    )
