import argparse
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from pipeline.extract.base import BaseExtractor
from pipeline.extract.remotive import RemotiveExtractor
from pipeline.lake.client import LakeClient
from pipeline.lake.keys import generate_bronze_key

logger = logging.getLogger(__name__)

EXTRACTORS: dict[str, type[BaseExtractor]] = {
    RemotiveExtractor.source: RemotiveExtractor,
}


@dataclass(frozen=True)
class ExtractResult:
    source: str
    bronze_key: str
    accepted: int
    rejected: int


def run_extractor(
    extractor: BaseExtractor,
    lake_client: LakeClient,
    run_id: str,
    run_time: datetime,
) -> ExtractResult:
    """Fetch, store the raw response in bronze, then parse it."""
    row_data = extractor.fetch()
    bronze_key = generate_bronze_key(extractor.source, run_time.date(), run_id)
    lake_client.put_json(bronze_key, row_data)
    logger.info(f"Raw data from {extractor.source} stored in bronze: {bronze_key}")
    parsed_data = extractor.parse(row_data, run_time)
    logger.info(
        f"Extract finished: {extractor.source}, "
        f"accepted: {len(parsed_data.postings)}, "
        f"rejected: {len(parsed_data.rejected)}"
    )

    return ExtractResult(
        extractor.source,
        bronze_key,
        len(parsed_data.postings),
        len(parsed_data.rejected),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract jobs into the bronze layer.")
    parser.add_argument(
        "source",
        choices=sorted(EXTRACTORS),
        help="pick from the available extractors: ('remotive',)",
    )
    parser.add_argument(
        "--run-id",
        help="Reuse an id to overwrite an earlier run (default: current UTC time).",
    )
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    run_time = datetime.now(UTC)
    run_id = args.run_id or f"{run_time:%Y%m%d-%H%M%S}"

    lake = LakeClient.setup_settings(settings)
    lake.ensure_bucket()
    run_extractor(EXTRACTORS[args.source](), lake, run_id, run_time)


if __name__ == "__main__":
    main()
