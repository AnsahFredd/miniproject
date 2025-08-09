import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_CACHE_CANDIDATES = [
    # If you mount a Render Disk, point to it first (recommended)
    os.getenv("HUGGINGFACE_CACHE_DIR"),
    os.getenv("HF_HOME"),
    "/opt/render/model-cache",     # example Render Disk mount (configure in render.yaml)
    "/opt/render/cache/huggingface",
    "/var/cache/huggingface",
    "/tmp/hf-cache",               # fallback (ephemeral)
]

def setup_runtime() -> str:
    """
    Configure runtime environment variables for memory friendliness and caching.
    Returns the resolved Hugging Face cache directory.
    """
    cache_dir = get_cache_dir()
    os.makedirs(cache_dir, exist_ok=True)

    # Hugging Face cache directories
    os.environ.setdefault("HF_HOME", cache_dir)
    os.environ.setdefault("TRANSFORMERS_CACHE", cache_dir)
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")  # faster downloads
    # Timeouts
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", os.getenv("HF_HUB_DOWNLOAD_TIMEOUT", "1800"))  # 30m

    # Tokenizers and threads: keep CPU usage and memory low
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("OMP_NUM_THREADS", os.getenv("OMP_NUM_THREADS", "1"))
    os.environ.setdefault("MKL_NUM_THREADS", os.getenv("MKL_NUM_THREADS", "1"))
    os.environ.setdefault("NUMEXPR_MAX_THREADS", os.getenv("NUMEXPR_MAX_THREADS", "1"))

    # Optional auth token (if you have private repos); safe to be empty
    if os.getenv("HUGGINGFACE_API_KEY"):
        os.environ["HF_TOKEN"] = os.environ["HUGGINGFACE_API_KEY"]

    logger.info(f"Hugging Face cache directory set to: {cache_dir}")
    return cache_dir

def get_cache_dir() -> str:
    """
    Resolve a cache directory. Prefer configured envs or known writable locations.
    """
    for candidate in DEFAULT_CACHE_CANDIDATES:
        if not candidate:
            continue
        try:
            Path(candidate).mkdir(parents=True, exist_ok=True)
            return str(Path(candidate))
        except Exception:
            continue
    # Final fallback
    fallback = str(Path.home() / ".cache" / "huggingface")
    Path(fallback).mkdir(parents=True, exist_ok=True)
    return fallback

def get_hf_token() -> Optional[str]:
    """Return HF token if configured."""
    return os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")

def is_render() -> bool:
    """Detect Render environment."""
    return bool(os.getenv("RENDER", ""))

def advise_persistent_disk() -> None:
    """
    Log advice about using a persistent disk for model cache in Render free tier.
    """
    if is_render():
        logger.info(
            "If you experience cache misses on each deploy, mount a Render Disk and set "
            "HUGGINGFACE_CACHE_DIR=/opt/render/model-cache in your service env."
        )
