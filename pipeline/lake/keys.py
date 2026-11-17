import re
from datetime import date

BRONZE_PREFIX = "bronze"

_VALID_NAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*")


def _validate(lable: str, value: str) -> str:
    if not _VALID_NAME_PATTERN.fullmatch(value):
        raise ValueError(
            f"ivalid {lable} {value!r}: allowed lowercase letters, digits, '-' and '_'"
        )
    return value


def generate_bronze_prefix(source: str, run_date: date | None = None) -> str:
    pref = f"{BRONZE_PREFIX}/source={_validate('source', source)}/"
    if run_date is not None:
        pref += f"dt={run_date:%Y-%m-%d}/"
    return pref


def generate_bronze_key(source: str, run_date: date, run_id: str) -> str:
    val = (
        f"{generate_bronze_prefix(source, run_date)}{_validate('run_id', run_id)}.json"
    )
    return val
