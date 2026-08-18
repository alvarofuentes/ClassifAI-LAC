import pandas as pd
from prepare_chile_split import is_orphan

def main():
    print("Building Index for Strategy 2 (Leave Colombia Out)...")
    
    # 1. Base Catalog
    base = pd.read_csv("data/raw/coicop_2018_es_traducido.csv", dtype=str)
    
    # 2. Expanded (No Colombia)
    expanded = pd.read_csv("data/raw/coicop_es_expanded_no_col.csv", dtype=str)
    
    # 3. Chile 100%
    chile = pd.read_csv("data/raw/ccif_2018_cl_ejemplos_es.csv", sep=';', dtype=str)
    chile['is_orphan'] = chile.apply(is_orphan, axis=1)
    chile = chile[chile['is_orphan'] == False]
    chile['id'] = chile['codigo_ccif'].str.replace('.', '').str[:4]
    chile['text'] = chile['frase_original']
    chile = chile[['id', 'text']].dropna()
    
    # Merge all
    master = pd.concat([base, expanded, chile], ignore_index=True)
    master = master.drop_duplicates(subset=['id', 'text'])
    
    output_path = "data/raw/coicop_master_no_col.csv"
    master.to_csv(output_path, index=False)
    print(f"Saved {len(master)} examples to {output_path}")

if __name__ == "__main__":
    main()
