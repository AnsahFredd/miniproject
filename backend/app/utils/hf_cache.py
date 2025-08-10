import logging
from pathlib import Path
import time
from typing import List, Optional, Dict, Any, Tuple

from huggingface_hub import snapshot_download, hf_hub_url, login
from huggingface_hub.utils import HfHubHTTPError
from transformers import pipeline

from app.core.runtime import setup_runtime, get_hf_token, get_cache_dir

logger = logging.getLogger(__name__)

# Ensure runtime is configured at import
_CACHE_DIR = setup_runtime()

def hf_login_if_needed() -> None:
    """
    Log into Hugging Face if a token is available.
    Safe to call multiple times.
    """
    token = get_hf_token()
    if not token:
        return
    try:
        login(token=token, add_to_git_credential=False)
        logger.info("Authenticated to Hugging Face Hub with provided token")
    except Exception as e:
        logger.warning(f"Failed to authenticate to Hugging Face Hub: {e}")
    
def is_model_cached_locally(repo_id: str) -> bool:
    """Check if a model repo is alredy cached in_CACHE_DIR"""
    # Hugging Face cache dir use repo_id with '--' instead of '/'
    safe_id = repo_id.replace("/", "--")
    model_dir = Path(_CACHE_DIR) / "models--" / safe_id
    return model_dir.exists() and any(model_dir.rglob("*"))


def snapshot_download_with_retry(
    repo_id: str,
    revision: str = "main",
    allow_patterns: Optional[List[str]] = None,
    max_retries: int = 3,
    retry_delay_s: int = 20,
    timeout: Optional[float] = None, #Kept for compatibility, not used
) -> str:
    """
    Download or reuse local snapshot of a HF repo into the cache dir.
    Returns the local directory path where files are cached.
    """
    hf_login_if_needed()
    if is_model_cached_locally(repo_id):
        logger.info(f"[{repo_id}] found in local cache - skipping download.")
        # Return the existing model path
        safe_id = repo_id.replace("/", "--")
        return str(Path(_CACHE_DIR) / "models--" / safe_id)
    
    # Try download if not cached
    last_err: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[{repo_id}] snapshot_download attempt {attempt}/{max_retries}")
            local_dir = snapshot_download(
                repo_id=repo_id,
                revision=revision,
                cache_dir=_CACHE_DIR,
                allow_patterns=allow_patterns,
                resume_download=True,
                local_files_only=False,
                max_workers=2,
            )
            logger.info(f"[{repo_id}] snapshot available at {local_dir}")
            return local_dir
        except HfHubHTTPError as e:
            last_err = e
            logger.warning(f"[{repo_id}] Hub HTTP error: {e}")
        except Exception as e:
            last_err = e
            logger.warning(f"[{repo_id}] snapshot_download failed: {e}")
        if attempt < max_retries:
            logger.info(f"[{repo_id}] retrying in {retry_delay_s}s...")
            time.sleep(retry_delay_s)
    logger.error(f"Failed to download snapshot for {repo_id} after {max_retries} attempts")
    if last_err:
        raise last_err
    raise RuntimeError(f"Unknown error downloading {repo_id}")

def load_pipeline_with_cache(
    task: str,
    primary_id: str,
    *,
    local_model_path: Optional[str] = None,  # ✅ Added back
    fallbacks: Optional[List[str]] = None,
    device: int = -1,  # -1 = CPU
    model_kwargs: Optional[Dict[str, Any]] = None,
    tokenizer_kwargs: Optional[Dict[str, Any]] = None,
    retries: int = 2,
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Build a transformers pipeline with:
    1. Local folder loading (if provided)
    2. HF Hub caching if local model is unavailable
    3. Fallback model IDs if primary fails
    """
    hf_login_if_needed()
    fallbacks = fallbacks or []
    model_kwargs = model_kwargs or {}
    tokenizer_kwargs = tokenizer_kwargs or {}

    last_err: Optional[Exception] = None

    # 1️ Try local folder first
    if local_model_path and Path(local_model_path).exists():
        try:
            logger.info(f"Loading pipeline task={task} from local folder: {local_model_path}")
            pl = pipeline(
                task,
                model=local_model_path,
                tokenizer=local_model_path,
                device=device,
                model_kwargs={
                    "torch_dtype": "auto",
                    "low_cpu_mem_usage": True,
                    **model_kwargs,
                },
                tokenizer_kwargs={
                    "use_fast": True,
                    **tokenizer_kwargs,
                },
            )
            logger.info(f"Loaded pipeline from local folder {local_model_path}")
            return pl, local_model_path
        except Exception as e:
            last_err = e
            logger.warning(f"Failed to load pipeline from local folder: {e}")

    # 2️Try HF Hub model(s)
    tried = [primary_id] + fallbacks
    for model_id in tried:
        try:
            snapshot_download_with_retry(model_id, max_retries=retries)
        except Exception as e:
            logger.warning(f"Prewarm snapshot failed for {model_id}: {e}")

        try:
            logger.info(f"Loading pipeline task={task} model={model_id} with cache_dir={_CACHE_DIR}")
            pl = pipeline(
                task,
                model=model_id,
                tokenizer=model_id,
                device=device,
                cache_dir=_CACHE_DIR,
                model_kwargs={
                    "torch_dtype": "auto",
                    "low_cpu_mem_usage": True,
                    **model_kwargs,
                },
                tokenizer_kwargs={
                    "use_fast": True,
                    **tokenizer_kwargs,
                },
            )
            logger.info(f"Loaded pipeline for {model_id}")
            return pl, model_id
        except Exception as e:
            last_err = e
            logger.warning(f"Failed to load pipeline for {model_id}: {e}")

    logger.error(f"Could not build pipeline for: {tried}")
    if last_err:
        logger.error(f"Last error: {last_err}")
    return None, None
