"""
scripts/download_model.py
Download embedding model ke folder lokal sebelum ingestion.
Set env var SEBELUM import apapun dari HuggingFace.
"""
import os

# MUST be set BEFORE any huggingface/transformers import
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
from pathlib import Path

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
SAVE_DIR = Path("models/paraphrase-multilingual-mpnet-base-v2")


def main():
    print(f"Downloading model: {MODEL_NAME}")
    print(f"Save directory  : {SAVE_DIR.resolve()}")
    print(f"HF_HUB_DISABLE_XET = {os.environ.get('HF_HUB_DISABLE_XET')}")
    print("-" * 60)

    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    from sentence_transformers import SentenceTransformer

    print("Loading model from HuggingFace (this may take a few minutes)...")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Saving model to: {SAVE_DIR.resolve()}")
    model.save(str(SAVE_DIR))

    print()
    print("=" * 60)
    print("  Model downloaded and saved successfully!")
    print(f"  Path: {SAVE_DIR.resolve()}")
    print()
    print("  Test embedding:")
    test = model.encode(["Pasien mengalami nyeri dada dan sesak napas."])
    print(f"  Vector dim: {len(test[0])}")
    print(f"  Sample: {test[0][:5].tolist()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
