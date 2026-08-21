from collections.abc import Iterator
from pathlib import Path

import boto3

from .base import FileStorage, StorageObject


class S3FileStorage(FileStorage):

    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None = None,
        region_name: str | None = None,
        public_url: str | None = None,
    ):
        self.bucket = bucket

        self.public_url = (
            public_url.rstrip("/")
            if public_url
            else None
        )

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
        )

    def save(
        self,
        source: Path,
        key: str,
        content_type: str,
    ) -> StorageObject:

        size = source.stat().st_size

        self.client.upload_file(
            str(source),
            self.bucket,
            key,
            ExtraArgs={
                "ContentType": content_type,
            },
        )

        return StorageObject(
            key=key,
            content_type=content_type,
            size=size,
        )

    def delete(
        self,
        key: str,
    ) -> None:

        self.client.delete_object(
            Bucket=self.bucket,
            Key=key,
        )

    def stat(
        self,
        key: str,
    ) -> StorageObject:

        response = self.client.head_object(
            Bucket=self.bucket,
            Key=key,
        )

        return StorageObject(
            key=key,
            content_type=response.get(
                "ContentType",
                "application/octet-stream",
            ),
            size=response["ContentLength"],
        )

    def get_url(
        self,
        key: str,
        expires: int = 3600,
    ) -> str:

        if self.public_url:
            return (
                f"{self.public_url}"
                f"/{key}"
            )

        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
            },
            ExpiresIn=expires,
        )

    def stream(
        self,
        key: str,
        start: int = 0,
        end: int | None = None,
        chunk_size: int = 1024 * 1024,
    ) -> Iterator[bytes]:

        byte_range = None

        if end is not None:
            byte_range = (
                f"bytes={start}-{end}"
            )
        elif start > 0:
            byte_range = (
                f"bytes={start}-"
            )

        params = {
            "Bucket": self.bucket,
            "Key": key,
        }

        if byte_range:
            params["Range"] = byte_range

        response = self.client.get_object(
            **params,
        )

        body = response["Body"]

        try:
            while True:

                chunk = body.read(
                    chunk_size
                )

                if not chunk:
                    break

                yield chunk

        finally:
            body.close()