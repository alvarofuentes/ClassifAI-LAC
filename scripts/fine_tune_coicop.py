import argparse
import os
from pathlib import Path

# Desactivar límite artificial de memoria unificada en MPS (Apple Silicon)
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.0")

import pandas as pd
import torch
from datasets import Dataset
from setfit import SetFitModel, Trainer, TrainingArguments, sample_dataset

ROOT_DIR = Path(__file__).parent.parent
RAW_DATA_PATH = ROOT_DIR / "data" / "raw" / "coicop_master_index.csv"
LAC_DATA_PATH = ROOT_DIR / "data" / "benchmarks" / "lac_multicountry_benchmark.csv"
OUTPUT_MODEL_DIR = ROOT_DIR / "models" / "coicop-finetuned-v1"


def prepare_dataset(master_path: Path, lac_path: Path | None = None):
    """Carga y combina el catálogo maestro COICOP con los benchmarks de LAC para entrenamiento SetFit."""
    print(f"Cargando catálogo maestro desde: {master_path}")
    df_master = pd.read_csv(master_path, dtype=str).dropna(subset=["id", "text"])
    df_master["label"] = df_master["id"].str[:4]
    df_master = df_master[["text", "label"]]

    dfs = [df_master]

    if lac_path and lac_path.exists():
        print(f"Cargando benchmark multi-país de LAC desde: {lac_path}")
        df_lac = pd.read_csv(lac_path, dtype=str)
        df_lac["label"] = df_lac["target_code_4d"].astype(str).str.replace(r"[^\d]", "", regex=True).str.zfill(4)
        df_lac["text"] = df_lac["query_text"]
        df_lac = df_lac.dropna(subset=["label", "text"])
        df_lac = df_lac[["text", "label"]]
        dfs.append(df_lac)

    df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["text", "label"])
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""]

    # Convertimos las etiquetas a IDs numéricos contiguos que requiere SetFit
    unique_labels = sorted(df["label"].unique())
    label2id = {label: idx for idx, label in enumerate(unique_labels)}
    id2label = {idx: label for label, idx in label2id.items()}

    df["label_id"] = df["label"].map(label2id)

    print(f"Dataset consolidado: {len(df)} ejemplos únicos en {len(unique_labels)} clases COICOP.")

    hf_dataset = Dataset.from_pandas(df[["text", "label_id"]].rename(columns={"label_id": "label"}))

    return hf_dataset, unique_labels, id2label, label2id


def main():
    parser = argparse.ArgumentParser(description="Fine-Tuning de COICOP usando SetFit")
    parser.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        help="Modelo base de HuggingFace",
    )
    parser.add_argument("--epochs", type=int, default=1, help="Número de épocas (por defecto 1 en SetFit)")
    parser.add_argument("--batch-size", type=int, default=16, help="Tamaño de batch")
    parser.add_argument(
        "--samples-per-class",
        type=int,
        default=64,
        help="Número de muestras por clase para few-shot learning (usa 0 para todo el dataset)",
    )
    parser.add_argument(
        "--num-iterations",
        type=int,
        default=5,
        help="Número de iteraciones/pares generados por muestra para Contrastive Learning",
    )
    parser.add_argument("--max-length", type=int, default=64, help="Longitud máxima de tokens")
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Dispositivo (cpu, cuda, mps). Si no se provee, se detecta automáticamente.",
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

    print("==========================================")
    print("🚀 Iniciando Fine-Tuning SetFit para COICOP (Enriquecido LAC)")
    print("==========================================")
    print(f"Dispositivo activo: {device}")
    print(f"Modelo base: {args.model}")
    print(
        f"Épocas: {args.epochs} | Batch Size: {args.batch_size} | "
        f"Muestras/clase: {args.samples_per_class if args.samples_per_class > 0 else 'Todas'} | "
        f"Iteraciones/muestra: {args.num_iterations}"
    )

    if not RAW_DATA_PATH.exists():
        print(f"❌ Error: No se encontró el dataset base en {RAW_DATA_PATH}")
        return

    # 1. Preparar Dataset consolidado
    hf_dataset, unique_labels, id2label, label2id = prepare_dataset(RAW_DATA_PATH, LAC_DATA_PATH)

    # Dividir un subset para validación (split 90/10)
    dataset_dict = hf_dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = dataset_dict["train"]
    eval_dataset = dataset_dict["test"]

    # Aplicar few-shot sampling si se especificó
    if args.samples_per_class > 0:
        print(f"\nAplicando Few-Shot sampling ({args.samples_per_class} ejemplos por clase)...")
        train_dataset = sample_dataset(train_dataset, label_column="label", num_samples=args.samples_per_class)
        print(f"Dataset de entrenamiento balanceado: {len(train_dataset)} ejemplos.")

    # 2. Cargar el modelo base en el dispositivo
    print("\nDescargando y cargando modelo base...")
    model = SetFitModel.from_pretrained(args.model, labels=unique_labels)
    model.to(device)

    # 3. Configurar el entrenamiento
    training_args = TrainingArguments(
        batch_size=args.batch_size,
        num_epochs=args.epochs,
        num_iterations=args.num_iterations,
        max_length=args.max_length,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    from sklearn.metrics import accuracy_score

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        metric=accuracy_score,
    )

    # 4. Entrenar embeddings
    print("\n🔥 Comenzando entrenamiento Contrastive Learning...")
    trainer.train()

    # 5. Ajustar classification head
    print("\n🧠 Calibrando classification head (LogisticRegression) sobre los embeddings entrenados...")
    x_train = list(train_dataset["text"])
    y_train = list(train_dataset["label"])
    train_embeddings = model.model_body.encode(x_train, show_progress_bar=True)
    model.model_head.fit(train_embeddings, y_train)

    # 6. Guardar el modelo completo
    OUTPUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n💾 Guardando modelo entrenado en {OUTPUT_MODEL_DIR}...")
    model.save_pretrained(OUTPUT_MODEL_DIR)

    # 7. Evaluar final detallado (Top-1, Top-3, Top-5)
    print(f"\n📊 Evaluando modelo sobre conjunto de prueba ({len(eval_dataset)} ejemplos no vistos)...")
    try:
        import numpy as np

        x_test = list(eval_dataset["text"])
        y_test = list(eval_dataset["label"])

        test_embeddings = model.model_body.encode(x_test, show_progress_bar=True)
        preds_id = model.model_head.predict(test_embeddings)
        probs = model.model_head.predict_proba(test_embeddings)

        acc_top1 = accuracy_score(y_test, preds_id)
        top3_hits = 0
        top5_hits = 0
        for idx, true_label in enumerate(y_test):
            sorted_classes = np.argsort(probs[idx])[::-1]
            classes_top3 = [model.model_head.classes_[i] for i in sorted_classes[:3]]
            classes_top5 = [model.model_head.classes_[i] for i in sorted_classes[:5]]
            if true_label in classes_top3:
                top3_hits += 1
            if true_label in classes_top5:
                top5_hits += 1

        print("\n" + "=" * 55)
        print("🎯 RESULTADOS FINALES DE EVALUACIÓN (ENRIQUECIDO LAC)")
        print("=" * 55)
        print(f"Top-1 Accuracy (Acierto exacto): {acc_top1 * 100:.2f}%")
        print(f"Top-3 Accuracy:                  {top3_hits / len(y_test) * 100:.2f}%")
        print(f"Top-5 Accuracy:                  {top5_hits / len(y_test) * 100:.2f}%")
        print("=" * 55)
    except Exception as exc:
        print(f"⚠️ Nota en evaluación: {exc}")

    print("\n✅ Fine-tuning completado con éxito.")
    print("Para usarlo en producción, actualiza la variable MODEL_NAME para que apunte a esta carpeta.")


if __name__ == "__main__":
    main()
