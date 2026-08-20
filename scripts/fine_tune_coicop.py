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
OUTPUT_MODEL_DIR = ROOT_DIR / "models" / "coicop-finetuned-v1"


def prepare_dataset(csv_path: Path):
    """Carga y prepara el dataset para el entrenamiento SetFit."""
    print(f"Cargando datos desde: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str)

    # Asegurar que no hay nulos
    df = df.dropna(subset=["id", "text"])

    # Tomamos solo los primeros 4 caracteres del id para que sean Clases COICOP a 4 dígitos
    df["label"] = df["id"].str[:4]

    # Convertimos las etiquetas a IDs numéricos contiguos que requiere SetFit
    unique_labels = sorted(df["label"].unique())
    label2id = {label: idx for idx, label in enumerate(unique_labels)}
    id2label = {idx: label for label, idx in label2id.items()}

    df["label_id"] = df["label"].map(label2id)

    print(f"Dataset cargado con {len(df)} filas y {len(unique_labels)} clases únicas.")

    # Convertimos a HuggingFace Dataset
    # SetFit espera típicamente las columnas 'text' y 'label' (numérica)
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
        default=16,
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
    print("🚀 Iniciando Fine-Tuning SetFit para COICOP")
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

    # 1. Preparar Dataset
    hf_dataset, unique_labels, id2label, label2id = prepare_dataset(RAW_DATA_PATH)

    # Dividir un pequeño subset para validación (opcional, pero útil)
    # Hacemos un split 90/10
    dataset_dict = hf_dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = dataset_dict["train"]
    eval_dataset = dataset_dict["test"]

    # Aplicar few-shot sampling si se especificó
    if args.samples_per_class > 0:
        print(f"\nAplicando Few-Shot sampling ({args.samples_per_class} ejemplos por clase)...")
        train_dataset = sample_dataset(train_dataset, label_column="label", num_samples=args.samples_per_class)
        print(f"Dataset de entrenamiento reducido a {len(train_dataset)} ejemplos balanceados.")

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

    # 4. Entrenar
    print("\n🔥 Comenzando entrenamiento Contrastive Learning...")
    trainer.train()

    # 5. Guardar el modelo
    OUTPUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n💾 Guardando modelo entrenado en {OUTPUT_MODEL_DIR}...")
    model.save_pretrained(OUTPUT_MODEL_DIR)

    # 6. Evaluar final
    print("\n📊 Evaluando modelo final...")
    try:
        metrics = trainer.evaluate()
        print(f"Métricas finales: {metrics}")
    except Exception as exc:
        print(f"⚠️ Nota en evaluación: {exc}")

    print("\n✅ Fine-tuning completado con éxito.")
    print("Para usarlo en producción, actualiza la variable MODEL_NAME para que apunte a esta carpeta.")


if __name__ == "__main__":
    main()
