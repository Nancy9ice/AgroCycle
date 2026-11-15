"""Load settings from the environment and build the S3 and ClickHouse clients."""

import os

import boto3
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required setting: {name} (see .env.example)")
    return value


def s3_bucket() -> str:
    return _require("S3_BUCKET")


def s3_client():
    return boto3.client(
        "s3",
        region_name=_require("AWS_REGION"),
        aws_access_key_id=_require("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=_require("AWS_SECRET_ACCESS_KEY"),
    )


def nass_api_key() -> str:
    return _require("NASS_API_KEY")


def clickhouse_client():
    return clickhouse_connect.get_client(
        host=_require("CLICKHOUSE_HOST"),
        port=int(_require("CLICKHOUSE_PORT")),
        username=_require("CLICKHOUSE_USER"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        database=os.environ.get("CLICKHOUSE_DATABASE", "agrocycle"),
        secure=os.environ.get("CLICKHOUSE_SECURE", "true").lower() == "true",
    )
