import logging
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

def snapshot_download_with_retry(
    repo_id: str,
    revision: str = "main",
    allow_patterns: Optional[List[str]] = None,
    max_retries: int = 3,
    retry_delay_s: int = 20,
    timeout: Optional[float] = None,
) -> str:
    """
    Download or reuse local snapshot of a HF repo into the cache dir.
    Returns the local directory path where files are cached.
    """
    hf_login_if_needed()
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
                max_workers=4,
                timeout=timeout,
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
    fallbacks: Optional[List[str]] = None,
    device: int = -1,  # -1 = CPU
    model_kwargs: Optional[Dict[str, Any]] = None,
    tokenizer_kwargs: Optional[Dict[str, Any]] = None,
    retries: int = 2,
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Build a transformers pipeline with caching and graceful fallbacks.
    Returns (pipeline_obj, used_model_id) where pipeline_obj can be None on failure.
    """
    hf_login_if_needed()
    fallbacks = fallbacks or []
    model_kwargs = model_kwargs or {}
    tokenizer_kwargs = tokenizer_kwargs or {}

    tried: List[str] = [primary_id] + fallbacks
    last_err: Optional[Exception] = None

    for model_id in tried:
        # Prewarm cache via snapshot_download (optional but helps progress/timeout handling)
        try:
            snapshot_download_with_retry(model_id, max_retries=retries)
        except Exception as e:
            logger.warning(f"Prewarm snapshot failed for {model_id}: {e} (will let pipeline handle it)")

        try:
            logger.info(f"Loading pipeline task={task} model={model_id} (CPU) with cache_dir={_CACHE_DIR}")
            pl = pipeline(
                task,
                model=model_id,
                tokenizer=model_id,
                device=device,
                cache_dir=_CACHE_DIR,
                model_kwargs={
                    # Reduce memory usage; auto dtype where possible
                    "torch_dtype": "auto",
                    "low_cpu_mem_usage": True,
                    **model_kwargs,
                },
                tokenizer_kwargs={
                    "use_fast": True,
                    **tokenizer_kwargs,
                },
                # trust_remote_code stays False by default for safety
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
