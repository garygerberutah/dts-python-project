# Copyright 2026 by GuidoGerb Publishing, LLC
import argparse
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import boto3
import requests
from boto3.s3.transfer import TransferConfig
from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_MODELS_JSON = ROOT / "scripts" / "all-guidogerb-models.json"

# If downloading gated models like FLUX, run this in terminal first: export HF_TOKEN="your_token"
HF_TOKEN = os.environ.get("HF_TOKEN")

api = HfApi()
s3 = boto3.client("s3")

# Configure Boto3 to use small memory chunks so we don't crash CloudShell's 2GB RAM limit
transfer_config = TransferConfig(
    multipart_threshold=8 * 1024 * 1024,  # 8 MB
    max_concurrency=4,  # 4 threads to save RAM
    multipart_chunksize=8 * 1024 * 1024,  # 8 MB chunks
)


MIN_AGE_DAYS = 30


def model_last_modified(repo_id: str) -> datetime:
    """Return the last-modified datetime (UTC) of a HuggingFace repo."""
    info = api.repo_info(repo_id=repo_id, token=HF_TOKEN)
    return info.last_modified


def is_model_mature(repo_id: str, min_age_days: int = MIN_AGE_DAYS) -> bool:
    """Return True if the repo's latest commit is at least min_age_days old."""
    last_mod = model_last_modified(repo_id)
    if last_mod.tzinfo is None:
        last_mod = last_mod.replace(tzinfo=UTC)
    age = datetime.now(UTC) - last_mod
    return age >= timedelta(days=min_age_days)


def load_models(json_path: str) -> tuple[str, list[dict]]:
    """Load model definitions from a JSON file. Returns (s3_bucket, models)."""
    with open(json_path) as f:
        data = json.load(f)
    return data["s3_bucket"], data["models"]


def s3_key_exists(bucket: str, key: str) -> bool:
    """Check whether a key exists in S3."""
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except s3.exceptions.ClientError:
        return False


def verify_model_in_s3(bucket: str, s3_prefix: str, model_name: str) -> list[str]:
    """List all S3 objects under the model prefix. Returns list of keys found."""
    prefix = f"{s3_prefix}/{model_name}/"
    found = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            found.append(obj["Key"])
    return found


def stream_model_to_s3(bucket: str, model: dict) -> None:
    """Download a single model from Hugging Face and stream to S3."""
    repo_id = model["repo_id"]
    s3_prefix = model["s3_prefix"]
    model_name = repo_id.split("/")[-1]

    print(f"\n[{repo_id}] Fetching file list...")

    repo_files = api.list_repo_files(repo_id=repo_id, token=HF_TOKEN)

    valid_extensions = (".safetensors", ".pt", ".ckpt", ".json", ".yaml", ".txt")
    files_to_download = [f for f in repo_files if f.endswith(valid_extensions) and "onnx" not in f]

    skipped = 0
    uploaded = 0
    for file_path in files_to_download:
        s3_key = f"{s3_prefix}/{model_name}/{file_path}"

        if s3_key_exists(bucket, s3_key):
            skipped += 1
            continue

        download_url = f"https://huggingface.co/{repo_id}/resolve/main/{file_path}"
        print(f" -> Streaming {file_path} to s3://{bucket}/{s3_key}")

        headers = {}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"

        with requests.get(
            download_url, headers=headers, stream=True, allow_redirects=True
        ) as response:
            response.raise_for_status()
            s3.upload_fileobj(
                Fileobj=response.raw, Bucket=bucket, Key=s3_key, Config=transfer_config
            )
        uploaded += 1

    print(f"[{repo_id}] Done — {uploaded} uploaded, {skipped} already in S3.")


def verify_all(bucket: str, models: list[dict]) -> bool:
    """Verify every model has files in S3. Returns True if all present."""
    all_ok = True
    for model in models:
        repo_id = model["repo_id"]
        model_name = repo_id.split("/")[-1]
        keys = verify_model_in_s3(bucket, model["s3_prefix"], model_name)
        if keys:
            print(f"  ✓ {repo_id}: {len(keys)} files in S3")
        else:
            print(f"  ✗ {repo_id}: NOT FOUND in S3")
            all_ok = False
    return all_ok


def stream_models_to_s3(bucket: str, models: list[dict], min_age_days: int = MIN_AGE_DAYS) -> None:
    """Download all models from Hugging Face, skipping files already in S3.

    Only uploads models whose latest HuggingFace commit is at least
    min_age_days old. Set min_age_days=0 to skip the maturity check.
    """
    for model in models:
        repo_id = model["repo_id"]
        if min_age_days > 0:
            try:
                if not is_model_mature(repo_id, min_age_days):
                    print(
                        f"\n[{repo_id}] Skipped — last modified less than {min_age_days} days ago"
                    )
                    continue
            except Exception as exc:
                print(f"\n[{repo_id}] Could not check age ({exc}), skipping")
                continue
        stream_model_to_s3(bucket, model)
    print("\nAll mature models synced.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stream HuggingFace models to S3")
    parser.add_argument(
        "--models",
        default=str(DEFAULT_MODELS_JSON),
        help="Path to models JSON file (default: scripts/all-guidogerb-models.json)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify models exist in S3, do not download",
    )
    parser.add_argument(
        "--min-age-days",
        type=int,
        default=MIN_AGE_DAYS,
        help=f"Only upload models >= {MIN_AGE_DAYS} days since last commit (default)",
    )
    parser.add_argument(
        "--ignore-age",
        action="store_true",
        help="Ignore the age check and upload all models regardless of last commit date",
    )
    args = parser.parse_args()

    bucket, models = load_models(args.models)

    print(f"Loaded {len(models)} models from {args.models}")
    print(f"S3 bucket: {bucket}\n")

    if args.verify_only:
        print("=== Verifying models in S3 ===")
        ok = verify_all(bucket, models)
        return 0 if ok else 1

    age_days = 0 if args.ignore_age else args.min_age_days
    if age_days > 0:
        print(f"Only uploading models whose latest commit is >= {age_days} days old.")
    else:
        print("Age check disabled — uploading all models.")
    print("\n=== Starting direct memory stream to S3 (Disk usage: 0MB) ===")
    stream_models_to_s3(bucket, models, min_age_days=age_days)

    print("\n=== Verifying uploads ===")
    verify_all(bucket, models)
    return 0


if __name__ == "__main__":
    sys.exit(main())
