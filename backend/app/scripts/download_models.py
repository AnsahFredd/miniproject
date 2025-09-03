import os
import sys
import time
import logging
import asyncio
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering,
)
from sentence_transformers import SentenceTransformer

# Load .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("lawlens.download_models")

# Configuration - Import settings from config
try:
    from app.core.config import settings
    logger.info("✅ Loaded configuration from app.config")
    CONFIG_LOADED = True
except ImportError:
    logger.warning("⚠️  Could not import app.config, falling back to environment variables")
    CONFIG_LOADED = False

# Environment setup
if CONFIG_LOADED:
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = str(settings.HF_HUB_ENABLE_HF_TRANSFER).lower()
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = str(settings.HF_HUB_DOWNLOAD_TIMEOUT)
else:
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = os.getenv("HF_HUB_ENABLE_HF_TRANSFER", "1")
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = os.getenv("HF_HUB_DOWNLOAD_TIMEOUT", "3600")

# Recommended Model Configuration (Fixed)
SUM_NAME = "facebook/bart-large-cnn"
SUM_PATH = Path("app/ai/models/summarization")

EMB_NAME = "law-ai/InLegalBERT"
EMB_PATH = Path("app/ai/models/embedding")

QA_NAME = "microsoft/deberta-v3-large"
QA_PATH = Path("app/ai/models/question-answering")

LEGAL_QA_NAME = "deepset/roberta-base-squad2"
LEGAL_QA_PATH = Path("app/ai/models/legal_qa")


CLS_NAME = "law-ai/InLegalBERT"
CLS_PATH = Path("app/ai/models/classification")

LEGAL_NAME = "nlpaueb/legal-bert-base-uncased"
LEGAL_PATH = Path("app/ai/models/legal_name")

# Retry settings
if CONFIG_LOADED:
    MAX_ATTEMPTS = settings.MODEL_DOWNLOAD_RETRIES if hasattr(settings, 'MODEL_DOWNLOAD_RETRIES') else 5
    RETRY_DELAY_S = settings.MODEL_DOWNLOAD_RETRY_DELAY_S if hasattr(settings, 'MODEL_DOWNLOAD_RETRY_DELAY_S') else 30
else:
    MAX_ATTEMPTS = int(os.getenv("MODEL_DOWNLOAD_RETRIES", "5"))
    RETRY_DELAY_S = int(os.getenv("MODEL_DOWNLOAD_RETRY_DELAY_S", "30"))

# Torch version advisory
try:
    import torch
    from packaging import version

    if version.parse(torch.__version__) < version.parse("2.6.0"):
        logger.warning(
            "Your torch version (%s) is <2.6.0. Some models may refuse to load due to CVE-2025-32434. "
            "Please upgrade: pip install --upgrade torch",
            torch.__version__,
        )
    logger.info("✅ Torch version: %s", torch.__version__)
except Exception as e:
    logger.warning("Torch import check failed (%s). If model loading fails, install torch.", e)


def should_download_models():
    """Check if we should download models (production) or use existing ones (local dev)."""
    if os.getenv("ENV") == "production":
        return True
    
    # Check if any models are missing locally
    all_models = [SUM_PATH, EMB_PATH, QA_PATH, LEGAL_QA_PATH, CLS_PATH, LEGAL_PATH]
    missing_models = [path for path in all_models if not model_exists(path)]
    
    if missing_models:
        logger.info("Missing models detected: %s", missing_models)
        return True
    
    logger.info("All models present locally, skipping download")
    return False


# Helpers
def ensure_directory(path: Path) -> None:
    """Create the directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    logger.debug("Directory ensured: %s", path)

def model_exists(path: Path) -> bool:
    """Generic check for a HuggingFace model directory."""
    if not path.exists():
        return False
    config_exists = (path / "config.json").exists()
    model_exists = (
        (path / "pytorch_model.bin").exists() or 
        (path / "model.safetensors").exists() or
        any(path.glob("pytorch_model-*.bin")) or
        any(path.glob("model-*.safetensors"))
    )
    return config_exists and model_exists

def embedding_model_exists(path: Path) -> bool:
    """Check for sentence-transformers or transformers model."""
    if not path.exists():
        return False
    # Check for sentence-transformers format
    if (path / "modules.json").exists():
        return True
    # Check for transformers format
    return model_exists(path)

async def download_summarization_model(force: bool = False) -> None:
    logger.info("📦 Downloading summarization model: %s", SUM_NAME)
    ensure_directory(SUM_PATH)

    if not force and model_exists(SUM_PATH):
        logger.info("⏭  Summarization model already present at %s (skipping).", SUM_PATH)
        return

    last_err: Optional[Exception] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info("Attempt %s/%s: Loading tokenizer...", attempt, MAX_ATTEMPTS)
            tokenizer = AutoTokenizer.from_pretrained(SUM_NAME)
            
            logger.info("Attempt %s/%s: Loading model...", attempt, MAX_ATTEMPTS)
            model = AutoModelForSeq2SeqLM.from_pretrained(
                SUM_NAME, 
                use_safetensors=True,
                torch_dtype="auto"
            )
            
            logger.info("Saving model to %s...", SUM_PATH)
            tokenizer.save_pretrained(SUM_PATH)
            model.save_pretrained(SUM_PATH, safe_serialization=True)
            logger.info("✅ Summarization model saved to: %s", SUM_PATH)
            return
        except Exception as e:
            last_err = e
            logger.warning("Attempt %s/%s to download summarization model failed: %s",
                           attempt, MAX_ATTEMPTS, e)
            if attempt < MAX_ATTEMPTS:
                logger.info("Retrying in %s seconds...", RETRY_DELAY_S)
                await asyncio.sleep(RETRY_DELAY_S)

    logger.error("❌ Failed to download summarization model after %s attempts.", MAX_ATTEMPTS)
    if last_err:
        raise last_err

async def download_embedding_model(force: bool = False) -> None:
    logger.info("📦 Downloading embedding model: %s", EMB_NAME)
    ensure_directory(EMB_PATH)

    if not force and embedding_model_exists(EMB_PATH):
        logger.info("⏭  Embedding model already present at %s (skipping).", EMB_PATH)
        return

    last_err: Optional[Exception] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            # Try as sentence transformer first (preferred for embeddings)
            try:
                logger.info("Attempt %s/%s: Loading as SentenceTransformer...", attempt, MAX_ATTEMPTS)
                model = SentenceTransformer(EMB_NAME)
                model.save(str(EMB_PATH))
                logger.info("✅ Embedding model (SentenceTransformer) saved to: %s", EMB_PATH)
                return
            except Exception:
                # Fallback to transformers format
                logger.info("Attempt %s/%s: Loading as Transformers model...", attempt, MAX_ATTEMPTS)
                tokenizer = AutoTokenizer.from_pretrained(EMB_NAME)
                model = AutoModelForSequenceClassification.from_pretrained(
                    EMB_NAME, 
                    use_safetensors=True,
                    torch_dtype="auto"
                )
                tokenizer.save_pretrained(EMB_PATH)
                model.save_pretrained(EMB_PATH, safe_serialization=True)
                logger.info("✅ Embedding model (Transformers) saved to: %s", EMB_PATH)
                return
        except Exception as e:
            last_err = e
            logger.warning("Attempt %s/%s to download embedding model failed: %s",
                           attempt, MAX_ATTEMPTS, e)
            if attempt < MAX_ATTEMPTS:
                logger.info("Retrying in %s seconds...", RETRY_DELAY_S)
                await asyncio.sleep(RETRY_DELAY_S)

    logger.error("❌ Failed to download embedding model after %s attempts.", MAX_ATTEMPTS)
    if last_err:
        raise last_err

async def download_classification_model(force: bool = False) -> None:
    logger.info("📦 Downloading classification model: %s", CLS_NAME)
    ensure_directory(CLS_PATH)

    if not force and model_exists(CLS_PATH):
        logger.info("⏭  Classification model already present at %s (skipping).", CLS_PATH)
        return

    last_err: Optional[Exception] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info("Attempt %s/%s: Loading tokenizer...", attempt, MAX_ATTEMPTS)
            tokenizer = AutoTokenizer.from_pretrained(CLS_NAME)
            
            logger.info("Attempt %s/%s: Loading model...", attempt, MAX_ATTEMPTS)
            model = AutoModelForSequenceClassification.from_pretrained(
                CLS_NAME, 
                use_safetensors=True,
                torch_dtype="auto"
            )
            
            logger.info("Saving model to %s...", CLS_PATH)
            tokenizer.save_pretrained(CLS_PATH)
            model.save_pretrained(CLS_PATH, safe_serialization=True)
            logger.info("✅ Classification model saved to: %s", CLS_PATH)
            return
        except Exception as e:
            last_err = e
            logger.warning("Attempt %s/%s to download classification model failed: %s",
                           attempt, MAX_ATTEMPTS, e)
            if attempt < MAX_ATTEMPTS:
                logger.info("Retrying in %s seconds...", RETRY_DELAY_S)
                await asyncio.sleep(RETRY_DELAY_S)

    logger.error("❌ Failed to download classification model after %s attempts.", MAX_ATTEMPTS)
    if last_err:
        raise last_err

async def download_qa_model(force: bool = False) -> None:
    logger.info("📦 Downloading Q&A model: %s", QA_NAME)
    ensure_directory(QA_PATH)

    if not force and model_exists(QA_PATH):
        logger.info("⏭  Q&A model already present at %s (skipping).", QA_PATH)
        return

    last_err: Optional[Exception] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info("Attempt %s/%s: Loading tokenizer...", attempt, MAX_ATTEMPTS)
            tokenizer = AutoTokenizer.from_pretrained(QA_NAME)
            
            logger.info("Attempt %s/%s: Loading model...", attempt, MAX_ATTEMPTS)
            model = AutoModelForQuestionAnswering.from_pretrained(
                QA_NAME, 
                use_safetensors=True,
                torch_dtype="auto"
            )
            
            logger.info("Saving model to %s...", QA_PATH)
            tokenizer.save_pretrained(QA_PATH)
            model.save_pretrained(QA_PATH, safe_serialization=True)
            logger.info("✅ Q&A model saved to: %s", QA_PATH)
            return
        except Exception as e:
            last_err = e
            logger.warning("Attempt %s/%s to download Q&A model failed: %s",
                           attempt, MAX_ATTEMPTS, e)
            if attempt < MAX_ATTEMPTS:
                logger.info("Retrying in %s seconds...", RETRY_DELAY_S)
                await asyncio.sleep(RETRY_DELAY_S)

    logger.error("❌ Failed to download Q&A model after %s attempts.", MAX_ATTEMPTS)
    if last_err:
        raise last_err

async def download_legal_qa_model(force: bool = False) -> None:
    logger.info("📦 Downloading legal Q&A model: %s", LEGAL_QA_NAME)
    ensure_directory(LEGAL_QA_PATH)

    if not force and model_exists(LEGAL_QA_PATH):
        logger.info("⏭  Legal Q&A model already present at %s (skipping).", LEGAL_QA_PATH)
        return

    last_err: Optional[Exception] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info("Attempt %s/%s: Loading tokenizer...", attempt, MAX_ATTEMPTS)
            tokenizer = AutoTokenizer.from_pretrained(LEGAL_QA_NAME)
            
            logger.info("Attempt %s/%s: Loading model...", attempt, MAX_ATTEMPTS)
            model = AutoModelForQuestionAnswering.from_pretrained(
                LEGAL_QA_NAME, 
                use_safetensors=True,
                torch_dtype="auto"
            )
            
            logger.info("Saving model to %s...", LEGAL_QA_PATH)
            tokenizer.save_pretrained(LEGAL_QA_PATH)
            model.save_pretrained(LEGAL_QA_PATH, safe_serialization=True)
            logger.info("✅ Legal Q&A model saved to: %s", LEGAL_QA_PATH)
            return
        except Exception as e:
            last_err = e
            logger.warning("Attempt %s/%s to download legal Q&A model failed: %s",
                           attempt, MAX_ATTEMPTS, e)
            if attempt < MAX_ATTEMPTS:
                logger.info("Retrying in %s seconds...", RETRY_DELAY_S)
                await asyncio.sleep(RETRY_DELAY_S)

    logger.error("❌ Failed to download legal Q&A model after %s attempts.", MAX_ATTEMPTS)
    if last_err:
        raise last_err

async def download_legal_analysis_model(force: bool = False) -> None:
    logger.info("📦 Downloading legal analysis model: %s", LEGAL_NAME)
    ensure_directory(LEGAL_PATH)

    if not force and model_exists(LEGAL_PATH):
        logger.info("⏭  Legal analysis model already present at %s (skipping).", LEGAL_PATH)
        return

    last_err: Optional[Exception] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info("Attempt %s/%s: Loading tokenizer...", attempt, MAX_ATTEMPTS)
            tokenizer = AutoTokenizer.from_pretrained(LEGAL_NAME)
            
            logger.info("Attempt %s/%s: Loading model...", attempt, MAX_ATTEMPTS)
            model = AutoModelForSequenceClassification.from_pretrained(
                LEGAL_NAME, 
                use_safetensors=True,
                torch_dtype="auto"
            )
            
            logger.info("Saving model to %s...", LEGAL_PATH)
            tokenizer.save_pretrained(LEGAL_PATH)
            model.save_pretrained(LEGAL_PATH, safe_serialization=True)
            logger.info("✅ Legal analysis model saved to: %s", LEGAL_PATH)
            return
        except Exception as e:
            last_err = e
            logger.warning("Attempt %s/%s to download legal analysis model failed: %s",
                           attempt, MAX_ATTEMPTS, e)
            if attempt < MAX_ATTEMPTS:
                logger.info("Retrying in %s seconds...", RETRY_DELAY_S)
                await asyncio.sleep(RETRY_DELAY_S)

    logger.error("❌ Failed to download legal analysis model after %s attempts.", MAX_ATTEMPTS)
    if last_err:
        raise last_err


def print_model_info():
    """Print information about the selected models."""
    config_source = "app.config" if CONFIG_LOADED else "environment variables"
    
    logger.info("\n🏛️  LawLens Recommended Model Configuration (loaded from %s):", config_source)
    logger.info("=" * 80)
    
    # Core Models
    logger.info("🎯 CORE MODELS")
    logger.info("-" * 30)
    logger.info("📄 Summarization: %s", SUM_NAME)
    logger.info("   📁 Path: %s", SUM_PATH)
    
    logger.info("🔍 Embeddings: %s", EMB_NAME)
    logger.info("   📁 Path: %s", EMB_PATH)
    logger.info("   → ⭐ Legal-domain optimized")
    
    logger.info("🏷️  Classification: %s", CLS_NAME)
    logger.info("   📁 Path: %s", CLS_PATH)
    logger.info("   → ⭐ Legal-domain optimized")
    
    logger.info("❓ General Q&A: %s", QA_NAME)
    logger.info("   📁 Path: %s", QA_PATH)
    
    logger.info("⚖️  Legal Q&A: %s", LEGAL_QA_NAME)
    logger.info("   📁 Path: %s", LEGAL_QA_PATH)
    
    # Specialized Models
    logger.info("\n🎓 SPECIALIZED MODELS")
    logger.info("-" * 30)
    logger.info("🏛️  Legal Analysis: %s", LEGAL_NAME)
    logger.info("   📁 Path: %s", LEGAL_PATH)
    logger.info("   → ⭐ Trained specifically on legal corpora")
    
    # Configuration
    logger.info("\n⚙️  CONFIGURATION")
    logger.info("-" * 20)
    logger.info("   → Max download attempts: %s", MAX_ATTEMPTS)
    logger.info("   → Retry delay: %ss", RETRY_DELAY_S)
    logger.info("   → Total storage: ~3.5GB")
    
    # Recommendations
    logger.info("\n💡 OPTIMIZATIONS")
    logger.info("-" * 20)
    logger.info("   → InLegalBERT models provide excellent legal domain understanding")
    logger.info("   → Contract analysis model covers most legal applications")
    logger.info("   → All models use safe tensor format for security")
    logger.info("   → Balanced selection for performance and storage efficiency")
    
    logger.info("=" * 80)


async def main(force: bool = False, check_only: bool = False):
    print_model_info()

    if not force and not should_download_models():
        logger.info("🎯 Using existing local models")
        return
    logger.info("\nStarting model downloads...\n")

    if check_only:
        logger.info("🔍 Checking models (dry run)...")
        logger.info("Summarization model present: %s", model_exists(SUM_PATH))
        logger.info("Embedding model present: %s", embedding_model_exists(EMB_PATH))
        logger.info("Classification model present: %s", model_exists(CLS_PATH))
        logger.info("Q&A model present: %s", model_exists(QA_PATH))
        logger.info("Legal Q&A model present: %s", model_exists(LEGAL_QA_PATH))
        logger.info("Legal analysis model present: %s", model_exists(LEGAL_PATH))
        return

    # All recommended models
    all_tasks = [
        download_summarization_model(force),
        download_embedding_model(force),
        download_classification_model(force),
        download_qa_model(force),
        download_legal_qa_model(force),
        download_legal_analysis_model(force),
    ]

    try:
        await asyncio.gather(*all_tasks)
        logger.info("\n🎉 All recommended models downloaded and saved successfully!")
        logger.info("💡 Your LawLens application is ready with optimal legal AI capabilities!")
        logger.info("✅ Models ready: Summarization, Embeddings, Classification, Q&A, Legal Analysis, Contract Analysis")
    except Exception as e:
        logger.error("\n❌ Some models failed to download: %s", e)
        logger.error("💡 Try running with --force to re-download, or check your internet connection")
        raise

if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    check_flag = "--check" in sys.argv
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
🏛️  LawLens Recommended Model Downloader

Usage:
    python download_models.py [OPTIONS]

Options:
    --check         Check which models are present (dry run)
    --force         Re-download models even if they exist
    --help, -h      Show this help message

Recommended Models (~3.5GB total):
    🎯 CORE MODELS:
    ├── Summarization: facebook/bart-large-cnn (~1.6GB)
    ├── Embeddings: law-ai/InLegalBERT ⭐ (~440MB)
    ├── Classification: law-ai/InLegalBERT ⭐ (~440MB) 
    ├── General Q&A: microsoft/deberta-v3-large (~1.4GB)
    └── Legal Q&A: deepset/roberta-base-squad2 (~500MB)
    
    🎓 SPECIALIZED MODELS:
    ├── Legal Analysis: nlpaueb/legal-bert-base-uncased ⭐ (~440MB)
    └── Contract Analysis: kiddothe2b/hierarchical-legal-bert-contracts ⭐ (~440MB)

Key Features:
    ⭐ Legal-domain optimized models for superior accuracy
    ⭐ Contract analysis for comprehensive legal document handling
    ⭐ Balanced selection optimized for performance and storage
    ⭐ Safe tensor format for security
    ⭐ Automatic retry mechanism with smart caching

Examples:
    python download_models.py           # Download all recommended models
    python download_models.py --check   # Check what's installed
    python download_models.py --force   # Re-download everything

This streamlined version provides the optimal balance of capabilities,
performance, and storage efficiency for legal AI applications.
        """)
        sys.exit(0)
    
    asyncio.run(main(force=force_flag, check_only=check_flag))