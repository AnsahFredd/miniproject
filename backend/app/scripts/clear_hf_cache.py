#!/usr/bin/env python3
"""
Script to clear Hugging Face cache and fix commit hash issues.
Usage: python scripts/clear_hf_cache.py [--model MODEL_NAME] [--all]
"""

import sys
import argparse
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hf_cache import cache_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Clear Hugging Face model cache")
    parser.add_argument("--model", help="Specific model to clear cache for")
    parser.add_argument("--all", action="store_true", help="Clear all caches")
    parser.add_argument("--prewarm", help="Pre-warm specific model after clearing")
    
    args = parser.parse_args()
    
    if args.all:
        logger.info("Clearing all Hugging Face caches...")
        success = cache_manager.clear_all_cache()
        if success:
            logger.info("✅ All caches cleared successfully")
        else:
            logger.error("❌ Failed to clear all caches")
            return 1
    
    elif args.model:
        logger.info(f"Clearing cache for model: {args.model}")
        success = cache_manager.clear_model_cache(args.model)
        if success:
            logger.info(f"✅ Cache cleared for {args.model}")
        else:
            logger.error(f"❌ Failed to clear cache for {args.model}")
            return 1
    
    if args.prewarm:
        logger.info(f"Pre-warming model: {args.prewarm}")
        success = cache_manager.prewarm_model_snapshot(args.prewarm)
        if success:
            logger.info(f"✅ Model {args.prewarm} pre-warmed successfully")
        else:
            logger.error(f"❌ Failed to pre-warm {args.prewarm}")
            return 1
    
    if not args.all and not args.model and not args.prewarm:
        # Default: clear cache for problematic AnsahFredd models
        problematic_models = [
            "AnsahFredd/summarization_model",
            "AnsahFredd/classification_model", 
            "AnsahFredd/embedding_model"
        ]
        
        for model in problematic_models:
            logger.info(f"Clearing cache for problematic model: {model}")
            cache_manager.clear_model_cache(model)
            
            # Try to pre-warm with latest revision
            logger.info(f"Pre-warming {model} with latest revision...")
            cache_manager.prewarm_model_snapshot(model, "main")
    
    logger.info("Cache management completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
