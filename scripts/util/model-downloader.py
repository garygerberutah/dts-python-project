# Copyright 2026 by GuidoGerb Publishing, LLC
import os

import boto3
import requests
from boto3.s3.transfer import TransferConfig
from huggingface_hub import HfApi

S3_BUCKET = "ggp-models"

# If downloading gated models like FLUX, run this in terminal first: export HF_TOKEN="your_token"
HF_TOKEN = os.environ.get("HF_TOKEN")

MODEL_MAPPINGS = {
    # Test with a small LoRA first to verify it works
    "XLabs-AI/flux-RealismLora": "loras",
    # Large checkpoints that will stream directly to S3
    "Wan-AI/Wan2.2-T2V-A14B": "Wan-AI",
    "black-forest-labs/FLUX.1-schnell": "checkpoints",
    # DeepSeek foundation LLM (already uploaded)
    "deepseek-ai/DeepSeek-V3.2": "LLM - Foundation/Transformer/Deep-Seek",
    # DeepSeek multimodal OCR
    "deepseek-ai/DeepSeek-OCR-2": "Vision - OCR/Transformer/Deep-Seek",
}

api = HfApi()
s3 = boto3.client("s3")

# Configure Boto3 to use small memory chunks so we don't crash CloudShell's 2GB RAM limit
transfer_config = TransferConfig(
    multipart_threshold=8 * 1024 * 1024,  # 8 MB
    max_concurrency=4,  # 4 threads to save RAM
    multipart_chunksize=8 * 1024 * 1024,  # 8 MB chunks
)


def stream_models_to_s3():
    for repo_id, folder_name in MODEL_MAPPINGS.items():
        print(f"\n[{repo_id}] Fetching file list...")
        model_name = repo_id.split("/")[-1]

        # Get all files in the Hugging Face repository
        repo_files = api.list_repo_files(repo_id=repo_id, token=HF_TOKEN)

        # Filter for exact weights and configs (skipping massive redundant bin/onnx files)
        valid_extensions = (".safetensors", ".pt", ".ckpt", ".json", ".yaml", ".txt")
        files_to_download = [
            f for f in repo_files if f.endswith(valid_extensions) and "onnx" not in f
        ]

        for file_path in files_to_download:
            s3_key = f"{folder_name}/{model_name}/{file_path}"
            download_url = f"https://huggingface.co/{repo_id}/resolve/main/{file_path}"

            print(f" -> Streaming {file_path} directly to s3://{S3_BUCKET}/{s3_key}")

            headers = {}
            if HF_TOKEN:
                headers["Authorization"] = f"Bearer {HF_TOKEN}"

            # Stream the file content directly into boto3's multipart upload
            with requests.get(
                download_url, headers=headers, stream=True, allow_redirects=True
            ) as response:
                response.raise_for_status()

                s3.upload_fileobj(
                    Fileobj=response.raw, Bucket=S3_BUCKET, Key=s3_key, Config=transfer_config
                )
        print(f"Successfully synced {repo_id} to S3!")


if __name__ == "__main__":
    print("Starting direct memory stream to S3 (Disk usage: 0MB)")
    stream_models_to_s3()
