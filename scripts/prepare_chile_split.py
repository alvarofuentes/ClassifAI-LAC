import pandas as pd
from sklearn.model_selection import train_test_split

def is_orphan(row):
    """
    Heuristic to determine if an example is an orphan word 
    broken off from a larger compound phrase.
    """
    ejemplo = str(row.get('ejemplo', '')).strip()
    frase = str(row.get('frase_original', '')).strip()
    
    words_ejemplo = len(ejemplo.split())
    words_frase = len(frase.split())
    
    conjunctions = [" o ", " y ", " e ", " u "]
    has_conj = any(c in frase.lower() for c in conjunctions)
    
    if words_ejemplo == 1 and words_frase > 2 and has_conj:
        return True
        
    if len(ejemplo) < 3:
        return True
        
    return False

def main():
    print("Loading test dataset (CCIF 2018 LLM Extracted)...")
    df = pd.read_csv("data/raw/ccif_2018_cl_ejemplos_es.csv", sep=';', dtype=str)
    
    # Apply orphan filter
    df['is_orphan'] = df.apply(is_orphan, axis=1)
    df = df[df['is_orphan'] == False]
    
    # Clean COICOP code (remove dots, truncate to 4 digits)
    df['id'] = df['codigo_ccif'].str.replace('.', '').str[:4]
    
    # Use frase_original as the text
    df['text'] = df['frase_original']
    
    # Drop rows without text or valid ID
    df = df.dropna(subset=['text', 'id'])
    
    # Keep only id and text columns for the index structure
    df = df[['id', 'text']]
    
    # Drop duplicates
    df = df.drop_duplicates()
    
    print(f"Total valid examples for Chile: {len(df)}")
    
    # Split 80/20
    train_df, test_df = train_test_split(df, test_size=0.20, random_state=42)
    
    train_path = "data/raw/chile_train.csv"
    test_path = "data/raw/chile_test.csv"
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print(f"Saved {len(train_df)} examples to {train_path}")
    print(f"Saved {len(test_df)} examples to {test_path}")

if __name__ == "__main__":
    main()
