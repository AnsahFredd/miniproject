import os
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# === Base Path for Summarization Model ===
MODEL_DIR = Path(__file__).resolve().parent.parent / "ai/models/bart-large-cnn"
MODEL_DIR = MODEL_DIR.as_posix()

if not Path(MODEL_DIR).exists():
    raise FileNotFoundError(f"Summarization model not found at {MODEL_DIR}")

# === Load Summarization Model ===
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR, local_files_only=True)
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

def summarize_text(text: str, max_length: int = 130, min_length: int = 30) -> str:
    """Generate a summary of the provided text."""
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]["summary_text"]

