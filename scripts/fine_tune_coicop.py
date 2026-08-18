import argparse
import os
import torch
import pandas as pd
from pathlib import Path
from setfit import SetFitModel, Trainer, TrainingArguments
from datasets import Dataset

ROOT_DIR = Path(__file__).parent.parent
RAW_DATA_PATH = ROOT_DIR / "data" / "raw" / "coicop_master_index.csv"
OUTPUT_MODEL_DIR = ROOT_DIR / "models" / "coicop-finetuned-v1"

def prepare_dataset(csv_path: Path):
    """Carga y prepara el dataset para el entrenamiento SetFit."""
    print(f"Cargando datos desde: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str)
    
    # Asegurar que no hay nulos
    df = df.dropna(subset=['id', 'text'])
    
    # Tomamos solo los primeros 4 caracteres del id para que sean Clases COICOP a 4 dígitos
    df['label'] = df['id'].str[:4]
    
    # Convertimos las etiquetas a IDs numéricos contiguos que requiere SetFit
    unique_labels = sorted(df['label'].unique())
    label2id = {label: idx for idx, label in enumerate(unique_labels)}
    id2label = {idx: label for label, idx in label2id.items()}
    
    df['label_id'] = df['label'].map(label2id)
    
    print(f"Dataset cargado con {len(df)} filas y {len(unique_labels)} clases únicas.")
    
    # Convertimos a HuggingFace Dataset
    # SetFit espera típicamente las columnas 'text' y 'label' (numérica)
    hf_dataset = Dataset.from_pandas(df[['text', 'label_id']].rename(columns={'label_id': 'label'}))
    
    return hf_dataset, unique_labels, id2label, label2id

def main():
    parser = argparse.ArgumentParser(description="Fine-Tuning de COICOP usando SetFit")
    parser.add_argument("--model", type=str, default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2", help="Modelo base de HuggingFace")
    parser.add_argument("--epochs", type=int, default=3, help="Número de épocas")
    parser.add_argument("--batch-size", type=int, default=16, help="Tamaño de batch")
    parser.add_argument("--device", type=str, default=None, help="Dispositivo (cpu, cuda, mps). Si no se provee, se detecta automáticamente.")
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
            
    print(f"==========================================")
    print(f"🚀 Iniciando Fine-Tuning SetFit para COICOP")
    print(f"==========================================")
    print(f"Dispositivo activo: {device}")
    print(f"Modelo base: {args.model}")
    print(f"Épocas: {args.epochs} | Batch Size: {args.batch_size}")

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

    # 2. Cargar el modelo base en el dispositivo
    print("\nDescargando y cargando modelo base...")
    model = SetFitModel.from_pretrained(args.model, labels=unique_labels)
    model.to(device)

    # 3. Configurar el entrenamiento
    training_args = TrainingArguments(
        batch_size=args.batch_size,
        num_epochs=args.epochs,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        metric="accuracy"
    )

    # 4. Entrenar
    print("\n🔥 Comenzando entrenamiento Contrastive Learning...")
    trainer.train()

    # 5. Evaluar final
    print("\n📊 Evaluando modelo final...")
    metrics = trainer.evaluate()
    print(f"Métricas finales: {metrics}")

    # 6. Guardar el modelo
    OUTPUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n💾 Guardando modelo entrenado en {OUTPUT_MODEL_DIR}...")
    model.save_pretrained(OUTPUT_MODEL_DIR)
    
    print("\n✅ Fine-tuning completado con éxito.")
    print("Para usarlo en producción, actualiza la variable MODEL_NAME para que apunte a esta carpeta.")

if __name__ == "__main__":
    main()
