from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

    from app.core.config import Settings

logger = logging.getLogger(__name__)

_NOT_FOUND_CODES = {"404", "NoSuchKey", "NoSuchBucket", "NotFound"}


class LakeError(Exception):
    """Any failure while talking to the object store."""


class ObjectNotFoundError(LakeError):
    """The requested key does not exist in the bucket."""


def _error_code(exc: ClientError) -> str:
    return str(exc.response.get("Error", {}).get("Code", ""))


class LakeClient:
    """Small wrapper around boto3: the only place that knows about S3."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
    ) -> None:
        self._bucket = bucket
        self._s3: S3Client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
            config=Config(
                s3={"addressing_style": "path"},
                retries={"max_attempts": 3},
                connect_timeout=3,
                read_timeout=10,
            ),
        )

    @classmethod
    def setup_settings(cls, settings: Settings) -> LakeClient:
        return cls(
            endpoint_url=settings.lake_endpoint_url,
            access_key=settings.lake_access_key,
            secret_key=settings.lake_secret_key.get_secret_value(),
            bucket=settings.lake_bucket,
        )

    @property
    def bucket(self) -> str:
        return self._bucket

    def ensure_bucket(self) -> None:
        try:
            self._s3.head_bucket(Bucket=self._bucket)
            return
        except ClientError as exc:
            if _error_code(exc) not in _NOT_FOUND_CODES:
                raise LakeError(f"cannot access bucket {self._bucket!r}") from exc
        except BotoCoreError as exc:
            raise LakeError(f"cannot reach the lake: {exc}") from exc

        try:
            self._s3.create_bucket(Bucket=self._bucket)
        except (ClientError, BotoCoreError) as exc:
            raise LakeError(f"cannot create bucket {self._bucket!r}") from exc
        logger.info("Created bucket %s", self._bucket)

    def is_reachable(self) -> bool:
        try:
            self._s3.head_bucket(Bucket=self._bucket)
        except (ClientError, BotoCoreError):
            return False
        return True

    def put_json(self, key: str, data: Any) -> None:
        body = json.dumps(data).encode("utf-8")
        try:
            self._s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=body,
                ContentType="application/json",
            )
        except (ClientError, BotoCoreError) as exc:
            raise LakeError(f"failed to write {key!r}") from exc
        logger.debug("Wrote %s (%d bytes)", key, len(body))

    def get_json(self, key: str) -> Any:
        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=key)
            body = response["Body"].read()
        except ClientError as exc:
            if _error_code(exc) in _NOT_FOUND_CODES:
                raise ObjectNotFoundError(f"object {key!r} not found") from exc
            raise LakeError(f"failed to read {key!r}") from exc
        except BotoCoreError as exc:
            raise LakeError(f"failed to read {key!r}") from exc
        return json.loads(body)

    def exists(self, key: str) -> bool:
        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            if _error_code(exc) in _NOT_FOUND_CODES:
                return False
            raise LakeError(f"failed to check {key!r}") from exc
        except BotoCoreError as exc:
            raise LakeError(f"failed to check {key!r}") from exc
        return True

    def list_keys(self, prefix: str = "") -> list[str]:
        keys: list[str] = []
        paginator = self._s3.get_paginator("list_objects_v2")
        try:
            for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
                keys.extend(obj["Key"] for obj in page.get("Contents", []))
        except (ClientError, BotoCoreError) as exc:
            raise LakeError(f"failed to list {prefix!r}") from exc
        return keys
