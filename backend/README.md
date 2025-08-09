# Deploying to Render Free Tier with Hugging Face Models

This backend loads models dynamically from the Hugging Face Hub and caches them on disk to avoid committing large binaries to Git.

Key changes:
- Models are never committed to Git (see .gitignore).
- All services load models on-demand with cache_dir and fallbacks to smaller models.
- Caching uses HF_HOME/TRANSFORMERS_CACHE to persist across restarts where possible.

## Render configuration

Recommended environment variables (Service Settings → Environment):
- HUGGINGFACE_API_KEY: hf_... (only if you use private repos; optional for public models)
- HUGGINGFACE_CACHE_DIR: /opt/render/model-cache (if you mount a Disk)
- TOKENIZERS_PARALLELISM: false
- OMP_NUM_THREADS: 1
- MKL_NUM_THREADS: 1
- NUMEXPR_MAX_THREADS: 1
- HF_HUB_ENABLE_HF_TRANSFER: 1
- HF_HUB_DOWNLOAD_TIMEOUT: 1800

If you can, attach a Render Disk (1-5 GB is plenty for smaller models):
- Mount path: /opt/render/model-cache
- Set HUGGINGFACE_CACHE_DIR to that mount path.

If not using a Disk, the cache will be in /tmp/hf-cache by default (ephemeral). Models may re-download on redeploys.

## render.yaml example

services:
  - type: web
    name: your-backend
    env: python
    plan: free
    region: oregon
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port 10000
    envVars:
      - key: TOKENIZERS_PARALLELISM
        value: "false"
      - key: OMP_NUM_THREADS
        value: "1"
      - key: MKL_NUM_THREADS
        value: "1"
      - key: NUMEXPR_MAX_THREADS
        value: "1"
      - key: HF_HUB_ENABLE_HF_TRANSFER
        value: "1"
      - key: HF_HUB_DOWNLOAD_TIMEOUT
        value: "1800"
      - key: HUGGINGFACE_CACHE_DIR
        value: "/opt/render/model-cache" # if Disk mounted
    disk:
      name: model-cache
      mountPath: /opt/render/model-cache
      sizeGB: 3

Notes:
- If you cannot mount a Disk, you can still run on free tier. The app will re-download models on cold starts or deploys.
- Prefer smaller models by setting:
  - SUMMARIZATION_MODEL=sshleifer/distilbart-cnn-12-6
  - QA_MODEL=distilbert-base-cased-distilled-squad
  - LEGAL_QA_MODEL=deepset/roberta-base-squad2 (heavier; use only if memory allows)
  - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
  - CLASSIFICATION_MODEL=nlpaueb/legal-bert-base-uncased (or your repo if small enough)

## Memory optimization tips

- Lazy loading: models are loaded only when methods are invoked.
- CPU-only inference: device=-1 avoids GPU deps on Render.
- Thread limits: OMP/MKL/TOKENIZERS vars reduce CPU and memory pressure.
- Chunk large texts before summarization/QA.
- Use smaller models where possible (see defaults above).
- Consider quantization for very large models, but note CPU int8 quantization (bitsandbytes) can be complex on Render free tier.

## Fallback strategies

- If primary model fails to load, the services try a sequence of fallback models.
- If all ML fallbacks fail, classification reverts to rule-based heuristics; QA returns a helpful error; summarization returns a message.

## Pre-warming cache (optional)

You can pre-warm the cache locally or in CI so the first request on Render is fast:

python scripts/hf_download_example.py --model sshleifer/distilbart-cnn-12-6
python scripts/hf_download_example.py --model sentence-transformers/all-MiniLM-L6-v2

The cache location is controlled by HUGGINGFACE_CACHE_DIR / HF_HOME / TRANSFORMERS_CACHE.

## GitHub hygiene

- .gitignore excludes model binaries and caches.
- If you must store some binaries, use Git LFS (not recommended for 100s of MB+ models).
- Keep only code and config in your repo.
