import logging
from datetime import UTC, datetime
from typing import Any, ClassVar

import httpx
from pydantic import ValidationError
from starlette import status
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.wait import wait_base

from pipeline.extract.base import BaseExtractor, ExtractError, ParseResult, RejectedRow
from pipeline.models import JobPost

logger = logging.getLogger(__name__)

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
USER_AGENT = "job-market-etl/0.1 (personal project)"
HTTP_TIMEOUT = 10
WAIT_MULTIPLIER = 1
WAIT_MIN = 1
WAIT_MAX = 10
MAX_ATTEMPTS = 3


class _RetryableStatusError(Exception):
    """Status code that may succeed later: 429 or 5xx."""


class RemotiveExtractor(BaseExtractor):
    source: ClassVar[str] = "remotive"

    def __init__(
        self,
        http_client: httpx.Client | None = None,
        wait: wait_base | None = None,
    ) -> None:
        self._client = http_client or httpx.Client(
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        self._wait = wait or wait_exponential(
            multiplier=WAIT_MULTIPLIER, min=WAIT_MIN, max=WAIT_MAX
        )

    def fetch(self) -> dict[str, Any]:
        retries = Retrying(
            stop=stop_after_attempt(MAX_ATTEMPTS),
            wait=self._wait,
            retry=retry_if_exception_type((httpx.TransportError, _RetryableStatusError)),
            reraise=True,
        )
        try:
            response = retries(self._send_get)
            data: dict[str, Any] = response.json()
        except (httpx.HTTPError, _RetryableStatusError, ValueError) as exc:
            msg = f"{self.source} failed with {exc}"
            raise ExtractError(msg) from exc
        return data

    def _send_get(self) -> httpx.Response:
        response = self._client.get(REMOTIVE_URL)
        if (
            response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            or response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR
        ):
            logger.warning(
                f"{self.source} failed with status code {response.status_code}, may retry"
            )
            msg = f"returned status code {response.status_code}"
            raise _RetryableStatusError(msg)
        response.raise_for_status()
        return response

    def parse(self, data: dict[str, Any], fetched_at: datetime) -> ParseResult:
        posts: list[JobPost] = []
        rejected: list[RejectedRow] = []
        raw_jobs = data.get("jobs", [])
        for raw_job in raw_jobs:
            try:
                posts.append(self._convert_to_job_post(raw_job, fetched_at))
            except (ValidationError, KeyError, ValueError) as exc:
                rejected.append(RejectedRow(raw_row=raw_job, reason=str(exc)))
        return ParseResult(postings=posts, rejected=rejected)

    def _convert_to_job_post(self, row: dict[str, Any], fetched_at: datetime) -> JobPost:
        posted_at = datetime.fromisoformat(row["publication_date"])
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=UTC)
        return JobPost(
            source=self.source,
            source_job_id=str(row["id"]),
            source_url=row["url"],
            title=row["title"],
            company=row.get("company_name"),
            description=row.get("description") or "",
            location=row.get("candidate_required_location"),
            salary_text=row.get("salary") or None,
            tags=row.get("tags") or (),
            category=row.get("category"),
            posted_at=posted_at,
            fetched_at=fetched_at,
        )
