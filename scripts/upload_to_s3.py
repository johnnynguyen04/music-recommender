"""upload the trained ncf checkpoint + a metrics blob to s3.

reads from env (or .env file):
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION, MODEL_BUCKET

usage:
  uv run python scripts/upload_to_s3.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
BUCKET = os.environ.get("MODEL_BUCKET")


def main():
    if not BUCKET:
        sys.exit("MODEL_BUCKET env var required (e.g. music-recommender-models)")
    s3 = boto3.client("s3", region_name=REGION)
    _ensure_bucket(s3, BUCKET, REGION)

    artifacts = ROOT / "artifacts" / "ncf.pt"
    metrics = ROOT / "results" / "metrics"

    _put(s3, artifacts, "ncf.pt")
    _put(s3, metrics / "comparison.json", "metrics/comparison.json")
    _put(s3, metrics / "classical.json", "metrics/classical.json")
    _put(s3, metrics / "neural.json", "metrics/neural.json")
    _put(s3, metrics / "hybrid.json", "metrics/hybrid.json")
    _put(s3, metrics / "match_rate.json", "metrics/match_rate.json")

    print(f"\nuploaded to s3://{BUCKET}/")
    print("verify with:  aws s3 ls s3://{BUCKET}/ --recursive".format(BUCKET=BUCKET))


def _ensure_bucket(s3, bucket: str, region: str):
    try:
        s3.head_bucket(Bucket=bucket)
        return
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code not in ("404", "NoSuchBucket"):
            raise
    print(f"creating bucket {bucket} in {region}")
    if region == "us-east-1":
        s3.create_bucket(Bucket=bucket)
    else:
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": region},
        )


def _put(s3, path: Path, key: str):
    if not path.exists():
        print(f"skip (missing): {path}")
        return
    print(f"upload {path.name} -> s3://{BUCKET}/{key}  ({path.stat().st_size / 1024:.1f} KB)")
    s3.upload_file(str(path), BUCKET, key)


if __name__ == "__main__":
    main()
