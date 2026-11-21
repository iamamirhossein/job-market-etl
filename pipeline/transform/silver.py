import html
import io
import re
from collections.abc import Iterable
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pipeline.models import JobPost

_SILVER_FIELDS: list["pa.Field[Any]"] = [
    pa.field("job_id", pa.string(), nullable=False),
    pa.field("source", pa.string(), nullable=False),
    pa.field("source_url", pa.string(), nullable=False),
    pa.field("source_job_id", pa.string(), nullable=False),
    pa.field("title", pa.string(), nullable=False),
    pa.field("category", pa.string()),
    pa.field("company", pa.string()),
    pa.field("location", pa.string()),
    pa.field("country", pa.string()),
    pa.field("salary_min", pa.float64()),
    pa.field("salary_max", pa.float64()),
    pa.field("salary_text", pa.string()),
    pa.field("currency", pa.string()),
    pa.field("tags", pa.list_(pa.string())),
    pa.field("description_text", pa.string()),
    pa.field("posted_at", pa.timestamp("us", tz="UTC"), nullable=False),
    pa.field("fetched_at", pa.timestamp("us", tz="UTC"), nullable=False),
]
SILVER_SCHEMA = pa.schema(_SILVER_FIELDS)

TAG_REGEX_PATTERN = re.compile(r"<[^>]*(?:>|$)")
SPACE_REGEX_PATTERN = re.compile(r"\s+")


def html_to_text(value: str) -> str:
    text = html.unescape(TAG_REGEX_PATTERN.sub(" ", value))
    return SPACE_REGEX_PATTERN.sub(" ", text).strip()


def normalize_tags(tags: Iterable[str]) -> list[str]:
    checked: dict[str, None] = {}
    for tag in tags:
        clean_value = tag.strip().lower()
        if clean_value:
            checked.setdefault(clean_value, None)
    return list(checked)


def job_post_to_frame(job_posts: Iterable[JobPost]) -> pd.DataFrame:
    """One row per job post, with the silver columns."""
    rows = [
        {
            "job_id": job_post.job_id,
            "source": job_post.source,
            "source_job_id": job_post.source_job_id,
            "source_url": str(job_post.source_url),
            "title": job_post.title,
            "company": job_post.company,
            "location": job_post.location,
            "country": job_post.country,
            "category": job_post.category,
            "salary_min": job_post.salary_min,
            "salary_max": job_post.salary_max,
            "salary_text": job_post.salary_text,
            "currency": job_post.currency,
            "tags": list(job_post.tags),
            "description_text": job_post.description,
            "posted_at": job_post.posted_at,
            "fetched_at": job_post.fetched_at,
        }
        for job_post in job_posts
    ]
    return pd.DataFrame(rows, columns=SILVER_SCHEMA.names)


def clean_job_posts(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the newest version of each job."""
    out = df.copy()
    out["description_text"] = out["description_text"].map(html_to_text)
    out["tags"] = out["tags"].map(normalize_tags)
    out = out.sort_values("fetched_at").drop_duplicates("job_id", keep="last")
    return out.sort_values("posted_at", ascending=False).reset_index(drop=True)


def convert_to_parquet_bytes(df: pd.DataFrame) -> bytes:
    table = pa.Table.from_pandas(df, schema=SILVER_SCHEMA, preserve_index=False)
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression="zstd")
    return buffer.getvalue()


def read_parquet_bytes(data: bytes) -> pd.DataFrame:
    return pq.read_table(io.BytesIO(data)).to_pandas()
