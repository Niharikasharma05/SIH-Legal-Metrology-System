"""Small S3-compatible storage boundary for original scan images."""

from __future__ import annotations

from uuid import UUID

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from settings import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket() -> None:
    """Provision a bucket only for local development; production is explicit."""
    if not settings.is_local:
        raise RuntimeError("Refusing to create a storage bucket outside local development")
    client = _client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket)
    except ClientError as error:
        if error.response["Error"]["Code"] not in {"404", "NoSuchBucket"}:
            raise
        client.create_bucket(Bucket=settings.minio_bucket)


def image_object_key(scan_id: UUID, image_id: UUID, extension: str = "jpg") -> str:
    extension = extension.lower().lstrip(".") or "jpg"
    return f"scans/{scan_id}/images/{image_id}.{extension}"


def report_object_key(scan_id: UUID, extension: str) -> str:
    """Deterministic report key — derived from scan_id alone, no separate
    DB column needed to look it up later. A scan's compliance verdict is
    only meant to be computed once it reaches a terminal status; if a
    report is regenerated for the same scan, overwriting the previous
    object at this same key is the correct behavior (the old report would
    just be a stale copy of the same verdict, not a different version
    worth keeping side by side). Revisit this if the system ever needs
    to keep multiple report versions per scan.
    """
    extension = extension.lower().lstrip(".")
    return f"scans/{scan_id}/reports/report.{extension}"


def report_exists(object_key: str) -> bool:
    try:
        _client().head_object(Bucket=settings.minio_bucket, Key=object_key)
        return True
    except ClientError as error:
        if error.response["Error"]["Code"] in {"404", "NoSuchKey"}:
            return False
        raise


def upload_image(object_key: str, body: bytes, content_type: str = "image/jpeg") -> None:
    _client().put_object(Bucket=settings.minio_bucket, Key=object_key, Body=body, ContentType=content_type)


def download_image(object_key: str) -> bytes:
    response = _client().get_object(Bucket=settings.minio_bucket, Key=object_key)
    try:
        return response["Body"].read()
    finally:
        response["Body"].close()