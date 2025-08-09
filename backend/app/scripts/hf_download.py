"""
Run this script to pre-warm the Hugging Face cache on your machine (or CI) without committing model files.

Usage:
  python scripts/hf_download_example.py --model facebook/bart-large-cnn
"""

import argparse
import logging
from utils.hf_cache import snapshot_download_with_retry
from core.runtime import setup_runtime

logging.basicConfig(level=logging.INFO)
setup_runtime()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Hugging Face repo id, e.g., facebook/bart-large-cnn")
    parser.add_argument("--revision", default="main")
    args = parser.parse_args()

    local_dir = snapshot_download_with_retry(args.model, revision=args.revision)
    print(f"Snapshot cached at: {local_dir}")

if __name__ == "__main__":
    main()
