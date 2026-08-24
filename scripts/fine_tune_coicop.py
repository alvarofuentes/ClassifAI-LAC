"""Fine-Tuning of COICOP classifier using SetFit with Multi-Country Stratification and Anti-Overfitting Controls."""

import argparse
import os
from pathlib import Path

# Desactivar límite artificial de memoria unificada en MPS (Apple Silicon)
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.0")

import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from setfit import SetFitModel, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = ROOT_DIR / "data" / "raw" / "coicop_master_index.csv"
LAC_DATA_PATH = ROOT_DIR / "data" / "benchmarks" / "lac_multicountry_benchmark.parquet"
LAC_FALLBACK_CSV = ROOT_DIR / "data" / "benchmarks" / "lac_multicountry_benchmark.csv"
TRAIN_SPLIT_PATH = ROOT_DIR / "data" / "benchmarks" / "lac_train_split.parquet"
TEST_SPLIT_PATH = ROOT_DIR / "data" / "benchmarks" / "lac_test_split.parquet"
OUTPUT_MODEL_DIR_V2 = ROOT_DIR / "models" / "coicop-finetuned-v2"


def create_stratified_splits(
    benchmark_path: Path,
    fallback_csv: Path,
    train_out: Path,
    test_out: Path,
    train_ratio: float = 0.8,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Splits benchmark into stratified train and test partitions by country dataset."""
    if benchmark_path.exists():
        df = pd.read_parquet(benchmark_path)
    elif fallback_csv.exists():
        df = pd.read_csv(fallback_csv, dtype=str)
    else:
        raise FileNotFoundError(f"Benchmark file not found at {benchmark_path} or {fallback_csv}")

    df["target_code_4d"] = (
        df["target_code_4d"].astype(str).str.replace(r"[^\d]", "", regex=True).str.zfill(4)
    )
    df["query_text"] = df["query_text"].astype(str).str.strip()
    df = df.dropna(subset=["target_code_4d", "query_text"])
    df = df[df["query_text"] != ""]

    train_list = []
    test_list = []

    # Stratify by sheet_name (country dataset)
    for sheet_name, group in df.groupby("sheet_name"):
        shuffled = group.sample(frac=1.0, random_state=seed).reset_index(drop=True)
        split_idx = int(len(shuffled) * train_ratio)
        train_list.append(shuffled.iloc[:split_idx])
        test_list.append(shuffled.iloc[split_idx:])

    df_train = pd.concat(train_list, ignore_index=True)
    df_test = pd.concat(test_list, ignore_index=True)

    train_out.parent.mkdir(parents=True, exist_ok=True)
    df_train.to_parquet(train_out, index=False)
    df_test.to_parquet(test_out, index=False)

    print(
        f"✅ Generated stratified split: {len(df_train)} train examples (80%) | "
        f"{len(df_test)} test examples (20% held-out) across {df['sheet_name'].nunique()} countries."
    )
    return df_train, df_test


def prepare_balanced_dataset(
    master_path: Path,
    df_train_lac: pd.DataFrame,
    max_samples_per_country_class: int = 20,
    seed: int = 42,
) -> tuple[Dataset, list[str], dict[int, str], dict[str, int]]:
    """Combines COICOP master catalog with balanced multi-country train records to prevent dataset domination."""
    print(f"Cargando catálogo maestro desde: {master_path}")
    df_master = pd.read_csv(master_path, dtype=str).dropna(subset=["id", "text"])
    df_master["label"] = df_master["id"].str[:4]
    df_master = df_master[["text", "label"]]

    # Balance LAC training data: take up to max_samples_per_country_class per (country, class)
    sampled_lac_parts = []
    for (sheet, label), group in df_train_lac.groupby(["sheet_name", "target_code_4d"]):
        n_sample = min(len(group), max_samples_per_country_class)
        sampled_lac_parts.append(group.sample(n_sample, random_state=seed))

    df_lac_balanced = pd.concat(sampled_lac_parts, ignore_index=True)
    df_lac_balanced["label"] = df_lac_balanced["target_code_4d"]
    df_lac_balanced["text"] = df_lac_balanced["query_text"]
    df_lac_balanced = df_lac_balanced[["text", "label"]]

    df_combined = pd.concat([df_master, df_lac_balanced], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=["text", "label"])
    df_combined["text"] = df_combined["text"].astype(str).str.strip()
    df_combined = df_combined[df_combined["text"] != ""]

    unique_labels = sorted(df_combined["label"].unique())
    label2id = {label: idx for idx, label in enumerate(unique_labels)}
    id2label = {idx: label for label, idx in label2id.items()}

    df_combined["label_id"] = df_combined["label"].map(label2id)

    print(
        f"Dataset consolidado y balanceado: {len(df_combined)} ejemplos únicos en "
        f"{len(unique_labels)} clases COICOP (evitando dominación de datasets masivos)."
    )

    hf_dataset = Dataset.from_pandas(df_combined[["text", "label_id"]].rename(columns={"label_id": "label"}))
    return hf_dataset, unique_labels, id2label, label2id


def main():
    parser = argparse.ArgumentParser(description="Fine-Tuning COICOP v2 con Estratificación y Anti-Overfitting")
    parser.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        help="Modelo base de HuggingFace",
    )
    parser.add_argument("--epochs", type=int, default=1, help="Número de épocas")
    parser.add_argument("--batch-size", type=int, default=16, help="Tamaño de batch")
    parser.add_argument(
        "--samples-per-country-class",
        type=int,
        default=25,
        help="Máximo de ejemplos por país y por clase COICOP para balancear",
    )
    parser.add_argument(
        "--num-iterations",
        type=int,
        default=10,
        help="Iteraciones por muestra para Contrastive Learning",
    )
    parser.add_argument("--max-length", type=int, default=64, help="Longitud máxima de tokens")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_MODEL_DIR_V2),
        help="Directorio destino del modelo v2",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Dispositivo (cpu, cuda, mps)",
    )
    args = parser.parse_args()

    # Detectar dispositivo
    if args.device:
        device = args.device
    else:
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

    output_model_path = Path(args.output_dir)

    print("===================================================================")
    print("🚀 Iniciando Fine-Tuning SetFit v2 para COICOP (Anti-Overfitting LAC)")
    print("===================================================================")
    print(f"Dispositivo activo: {device}")
    print(f"Modelo base: {args.model}")
    print(f"Destino del modelo: {output_model_path}")
    print(
        f"Épocas: {args.epochs} | Batch Size: {args.batch_size} | "
        f"Muestras máx/país/clase: {args.samples_per_country_class} | "
        f"Iteraciones contrastivas: {args.num_iterations}"
    )

    if not RAW_DATA_PATH.exists():
        print(f"❌ Error: No se encontró el catálogo maestro en {RAW_DATA_PATH}")
        return

    # 1. Crear / Cargar partición estratificada 80/20
    df_train_lac, df_test_lac = create_stratified_splits(
        benchmark_path=LAC_DATA_PATH,
        fallback_csv=LAC_FALLBACK_CSV,
        train_out=TRAIN_SPLIT_PATH,
        test_out=TEST_SPLIT_PATH,
        train_ratio=0.8,
        seed=42,
    )

    # 2. Preparar dataset de entrenamiento balanceado
    hf_dataset, unique_labels, id2label, label2id = prepare_balanced_dataset(
        master_path=RAW_DATA_PATH,
        df_train_lac=df_train_lac,
        max_samples_per_country_class=args.samples_per_country_class,
        seed=42,
    )

    # Validación interna (split 90/10 del dataset de entrenamiento balanceado)
    dataset_dict = hf_dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = dataset_dict["train"]
    eval_dataset = dataset_dict["test"]

    print(f"\nConjunto de entrenamiento interno: {len(train_dataset)} ejemplos.")
    print(f"Conjunto de validación interna:     {len(eval_dataset)} ejemplos.")

    # 3. Cargar el modelo base
    print("\nDescargando y cargando modelo base...")
    model = SetFitModel.from_pretrained(args.model, labels=unique_labels)
    model.to(device)

    # 4. Configurar el entrenamiento con Early Stopping / Best Model
    training_args = TrainingArguments(
        batch_size=args.batch_size,
        num_epochs=args.epochs,
        num_iterations=args.num_iterations,
        max_length=args.max_length,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        metric=accuracy_score,
    )

    # 5. Entrenar embeddings
    print("\n🔥 Comenzando entrenamiento Contrastive Learning v2...")
    trainer.train()

    # 6. Ajustar classification head
    print("\n🧠 Calibrando classification head (LogisticRegression) sobre los embeddings entrenados...")
    x_train = list(train_dataset["text"])
    y_train = list(train_dataset["label"])
    train_embeddings = model.model_body.encode(x_train, show_progress_bar=True)
    model.model_head.fit(train_embeddings, y_train)

    # 7. Guardar el modelo v2
    output_model_path.mkdir(parents=True, exist_ok=True)
    print(f"\n💾 Guardando modelo entrenado en {output_model_path}...")
    model.save_pretrained(output_model_path)

    # 8. Evaluación de control sobre el conjunto de test ciego (20% nunca visto)
    print(f"\n📊 Evaluando modelo sobre TEST SPLIT CIEGO ({len(df_test_lac)} ejemplos de los 15 países)...")
    try:
        x_blind = list(df_test_lac["query_text"])
        y_blind = list(df_test_lac["target_code_4d"])

        test_embeddings = model.model_body.encode(x_blind, show_progress_bar=True)
        preds_id = model.model_head.predict(test_embeddings)
        probs = model.model_head.predict_proba(test_embeddings)

        acc_top1 = accuracy_score(y_blind, preds_id)
        top3_hits = 0
        top5_hits = 0
        for idx, true_label in enumerate(y_blind):
            sorted_classes = np.argsort(probs[idx])[::-1]
            classes_top3 = [model.model_head.classes_[i] for i in sorted_classes[:3]]
            classes_top5 = [model.model_head.classes_[i] for i in sorted_classes[:5]]
            if true_label in classes_top3:
                top3_hits += 1
            if true_label in classes_top5:
                top5_hits += 1

        print("\n" + "=" * 65)
        print("🎯 RESULTADOS FINALES EN TEST SPLIT CIEGO (OUT-OF-SAMPLE)")
        print("=" * 65)
        print(f"Top-1 Accuracy (Acierto exacto 4D): {acc_top1 * 100:.2f}%")
        print(f"Top-3 Accuracy:                     {top3_hits / len(y_blind) * 100:.2f}%")
        print(f"Top-5 Accuracy:                     {top5_hits / len(y_blind) * 100:.2f}%")
        print("=" * 65)
    except Exception as exc:
        print(f"⚠️ Nota en evaluación de test ciego: {exc}")

    print(f"\n✅ Fine-tuning v2 completado con éxito y guardado en {output_model_path}.")


if __name__ == "__main__":
    main()

