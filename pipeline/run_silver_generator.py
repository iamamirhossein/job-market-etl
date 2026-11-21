import argparse
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from pipeline.extract.base import BaseExtractor
from pipeline.lake.client import LakeClient
from pipeline.lake.keys import generate_bronze_prefix, generate_silver_key
from pipeline.models import JobPost
from pipeline.run_extractor import EXTRACTORS
from pipeline.transform.silver import (
    clean_job_posts,
    convert_to_parquet_bytes,
    job_post_to_frame,
)

logger = logging.getLogger(__name__)

CONTENT_TYPE = "application/vnd.apache.parquet"


@dataclass(frozen=True)
class SilverResult:
    source: str
    silver_key: str
    bronze_files: int
    parsed: int
    rejected: int
    rows: int


def build_silver(
    extractor: BaseExtractor,
    lake_client: LakeClient,
    run_date: date,
) -> SilverResult:
    """Turn every bronze file of one source and day into one silver Parquet file."""
    bronze_keys = lake_client.list_keys(
        generate_bronze_prefix(extractor.source, run_date)
    )
    if not bronze_keys:
        msg = f"no bronze data for {extractor.source} on {run_date}"
        raise FileNotFoundError(msg)

    job_posts: list[JobPost] = []
    rejected = 0
    for key in bronze_keys:
        data = lake_client.get_json(key)
        fetched_at = lake_client.last_modified(key)
        result = extractor.parse(data, fetched_at)
        job_posts.extend(result.postings)
        rejected += len(result.rejected)

    df = clean_job_posts(job_post_to_frame(job_posts))
    silver_key = generate_silver_key(extractor.source, run_date)
    lake_client.put_bytes(silver_key, convert_to_parquet_bytes(df), CONTENT_TYPE)

    logger.info(
        f"Silver written: {silver_key} ({len(bronze_keys)} bronze files,"
        f" {len(job_posts)} parsed,"
        f" {rejected} rejected,"
        f" {len(df)} unique rows)",
    )
    return SilverResult(
        source=extractor.source,
        silver_key=silver_key,
        bronze_files=len(bronze_keys),
        parsed=len(job_posts),
        rejected=rejected,
        rows=len(df),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the silver layer for one day.")
    parser.add_argument("source", choices=sorted(EXTRACTORS))
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=datetime.now(UTC).date(),
        help="Day to process, YYYY-MM-DD (default: today, UTC).",
    )
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    lake_client = LakeClient.setup_settings(settings)
    build_silver(EXTRACTORS[args.source](), lake_client, args.date)


if __name__ == "__main__":
    main()
