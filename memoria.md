# Memoria del Proyecto: ClassifAI-LAC

## 1. Objetivo del Proyecto
Desarrollar y optimizar una herramienta automatizada (ClassifAI) para la clasificación estadística estandarizada de gastos de consumo de hogares latinoamericanos según la norma internacional **COICOP 2018**, llegando hasta el nivel de 4 dígitos (Clases).

## 2. Arquitectura Base
El núcleo original del sistema es una aplicación rápida basada en FastAPI, Polars y RAG (Retrieval-Augmented Generation) semántico.
- **Backend:** Python (FastAPI).
- **Indexación Vectorial:** Utiliza `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` combinado con BM25 para realizar un enrutamiento rápido. Las representaciones vectoriales se guardan en `.parquet`.
- **Integración Humana:** Posee un Dashboard de administración (`/admin/training`) que permite a estadísticos revisar ejemplos dudosos, inyectar el conocimiento en un CSV en tiempo real, y re-entrenar (hot-reload) el vectorstore sin tiempos de caída.

## 3. Evolución Metodológica y Resultados

A lo largo de nuestras sesiones, la precisión del sistema (Top-1 Accuracy) evolucionó a través de inyecciones de datos y validaciones rigurosas:

*   **Fase 1 (Línea Base Cero-Shot):** Probando un índice que solo conocía los "títulos formales" de COICOP frente a una encuesta real. El modelo se confundía gravemente con dialectos. *(Precisión: ~28%)*.
*   **Fase 2 (Inyección Regional Cero-Shot):** Expandimos la base indexando ~25,000 literales reales de encuestas de gasto de 8 países latinoamericanos distintos (Bolivia, Brasil, Colombia, Costa Rica, Ecuador, Perú, Uruguay, etc.). Al evaluar contra Colombia excluyéndola del entrenamiento (Leave-One-Out), probamos que el modelo ahora entiende "dialectos" y regionalismos no explícitos. *(Precisión: 61.82%)*.
*   **Fase 3 (Evaluación In-Domain - Few Shot):** Validamos con datos de Chile separando 80% entrenamiento / 20% testeo. *(Precisión: 69.07%, subiendo a 77.26% en el Top-3)*.

## 4. Retos Abordados
- **Rigurosidad Jerárquica:** Fue necesario limpiar y estandarizar profundamente los CSV de origen para asegurar que el modelo siempre predijera exactamente 4 dígitos y que no existiera "contaminación" cruzada entre subniveles.
- **Sintaxis y Acentos:** Se utilizaron scripts en Polars para normalizar caracteres, remover tildes y asegurar consistencia lingüística al momento de evaluar las cadenas de texto (`frase_original`).

## 5. Próximos Pasos (Estado Actual)
El motor de similitud (embeddings) actual es genérico. El próximo hito tecnológico es aplicar **Contrastive Learning (Fine-Tuning con SetFit)** sobre el modelo de HuggingFace utilizando los ~25,000 datos curados. Esto separará rígidamente las fronteras de decisión de las 187 clases de COICOP en el espacio hiperdimensional, apuntando a superar la barrera del 85% de precisión global.
