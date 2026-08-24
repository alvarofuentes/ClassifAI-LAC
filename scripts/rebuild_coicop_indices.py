"""Script to rebuild and manage VectorStore indices for COICOP using Baseline and Fine-Tuned models."""

import sys
from pathlib import Path

from classifai.indexers.main import VectorStore
from classifai.vectorisers.huggingface import HuggingFaceVectoriser

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_MASTER_CSV = ROOT_DIR / "data" / "raw" / "coicop_master_index.csv"
OUTPUT_INDICES_DIR = ROOT_DIR / "data" / "indices"

FINETUNED_V1_MODEL_PATH = ROOT_DIR / "models" / "coicop-finetuned-v1"
FINETUNED_V2_MODEL_PATH = ROOT_DIR / "models" / "coicop-finetuned-v2"
BASELINE_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


def build_index(model_identifier: str, output_name: str, batch_size: int = 64, overwrite: bool = False):
    """Builds a VectorStore index for the master COICOP catalog."""
    output_dir = OUTPUT_INDICES_DIR / output_name
    output_dir_str = str(output_dir)

    vectoriser = HuggingFaceVectoriser(model_name=model_identifier)

    if output_dir.exists() and not overwrite:
        vectors_file = output_dir / "vectors.parquet"
        meta_file = output_dir / "metadata.json"
        if vectors_file.exists() and meta_file.exists():
            print(f"Index '{output_name}' already exists at {output_dir}. Loading from filespace...")
            return VectorStore.from_filespace(output_dir_str, vectoriser=vectoriser)

    print("\n=======================================================")
    print(f"Building VectorStore '{output_name}'")
    print(f"Model: {model_identifier}")
    print(f"Source catalog: {RAW_MASTER_CSV}")
    print(f"Batch size: {batch_size}")
    print("=======================================================")

    store = VectorStore(
        file_name=str(RAW_MASTER_CSV),
        data_type="csv",
        vectoriser=vectoriser,
        batch_size=batch_size,
        output_dir=output_dir_str,
        overwrite=True,
    )

    print(
        f"✅ Successfully built and saved index '{output_name}' "
        f"({store.num_vectors} vectors, dim={store.vector_shape})."
    )
    return store


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Rebuild COICOP VectorStore indices")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing indices")
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding batch size")
    args = parser.parse_args()

    OUTPUT_INDICES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Build Fine-Tuned v2 Index if exists
    if FINETUNED_V2_MODEL_PATH.exists():
        print(f"Found fine-tuned v2 model at {FINETUNED_V2_MODEL_PATH}")
        build_index(
            model_identifier=str(FINETUNED_V2_MODEL_PATH),
            output_name="coicop_master_finetuned_v2",
            batch_size=args.batch_size,
            overwrite=args.overwrite,
        )

    # 2. Build Fine-Tuned v1 Index if exists
    if FINETUNED_V1_MODEL_PATH.exists():
        print(f"Found fine-tuned v1 model at {FINETUNED_V1_MODEL_PATH}")
        build_index(
            model_identifier=str(FINETUNED_V1_MODEL_PATH),
            output_name="coicop_master_finetuned_v1",
            batch_size=args.batch_size,
            overwrite=args.overwrite,
        )

    # 3. Build Baseline Index
    print(f"\nSetting up Baseline model: {BASELINE_MODEL_NAME}")
    build_index(
        model_identifier=BASELINE_MODEL_NAME,
        output_name="coicop_master_baseline_mpnet",
        batch_size=args.batch_size,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()

