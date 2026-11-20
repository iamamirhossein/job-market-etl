from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar

from pipeline.models import JobPost


class ExtractError(Exception):
    """
    The source could not be extracted or Fetched.
    """


@dataclass(frozen=True)
class RejectedRow:
    raw_row: dict[str, Any]
    reason: str


@dataclass(frozen=True)
class ParseResult:
    postings: list[JobPost]
    rejected: list[RejectedRow]


class BaseExtractor(ABC):
    source: ClassVar[str]

    @abstractmethod
    def fetch(self) -> dict[str, Any]:
        """Return the raw data"""

    @abstractmethod
    def parse(self, data: dict[str, Any], fetched_at: datetime) -> ParseResult:
        """Return the parsed data (Validated JobPost and RejectedRow)"""
