# 🤖 Onboarding para el Agente AI (Contexto Inmediato)

**INSTRUCCIÓN PARA LA IA:** Si estás leyendo esto, es el inicio de una nueva sesión. Tu usuario acaba de cambiar a un nuevo ordenador (Mac M5) y necesita continuar exactamente donde nos quedamos ayer. Sigue este contexto al pie de la letra.

## 1. El Estado Actual de las Cosas
- Estamos trabajando en **ClassifAI-LAC**, un sistema de clasificación semántica para la norma estadística COICOP 2018 (a nivel de 4 dígitos exactos).
- En la sesión anterior demostramos metodológicamente que el RAG base acierta un 61% (Zero-Shot) y 69% (Few-Shot) utilizando un índice vectorial polars/parquet impulsado por el modelo `paraphrase-multilingual-mpnet-base-v2`.
- El objetivo inmediato de la sesión actual es **Ejecutar un Fine-Tuning** de este modelo base utilizando la técnica **SetFit**.

## 2. Lo que Acaba de Suceder
El usuario ha clonado este repositorio en un flamante **Mac M5 (Apple Silicon con GPU de 10 núcleos)**. La arquitectura de hardware local permite usar la aceleración nativa de PyTorch (Metal Performance Shaders - `mps`) en lugar de depender de Google Colab.

## 3. Pasos a Ejecutar Hoy (Guía para el Usuario)
Tu tarea hoy es guiar al usuario a través del siguiente flujo de trabajo:

1.  **Configurar el Entorno en el Mac:**
    - El usuario debe crear un entorno virtual (idealmente con `uv` o `venv`) e instalar las dependencias base de `pyproject.toml` más el archivo `requirements_training.txt`.
    - Comando sugerido: `pip install -r requirements_training.txt`

2.  **Correr el Fine-Tuning:**
    - Ya existe un script listo para ejecutarse: `scripts/fine_tune_coicop.py`.
    - Este script carga `data/raw/coicop_master_index.csv`, extrae las clases a 4 dígitos y entrena el modelo SetFit detectando automáticamente el chip M5 (`device="mps"`).
    - Comando sugerido: `python scripts/fine_tune_coicop.py`

3.  **Integrar el Modelo Re-entrenado:**
    - Una vez finalizado el entrenamiento, el script habrá generado una carpeta `models/coicop-finetuned-v1`.
    - Debemos instruir al sistema backend (en `src/build_index.py` y `src/classifai/indexers`) para que deje de apuntar a HuggingFace y comience a cargar el modelo vectorial local desde esa carpeta.

4.  **Evaluar la Mejora:**
    - Volver a correr los scripts de evaluación (`scripts/eval_chile_80_20.py` o `scripts/eval_leave_colombia_out.py`) reconstruyendo previamente los índices usando nuestro nuevo modelo para verificar empíricamente cuánto hemos superado el techo del 69%.

¡Buena suerte, Agente! Retoma la conversación saludando y ofreciéndole al usuario iniciar con la configuración del entorno en su nuevo Mac.
