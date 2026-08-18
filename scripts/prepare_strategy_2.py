import pandas as pd
import os

def main():
    excel_path = "260319_COICOP.xlsx"
    index_output = "data/raw/coicop_es_expanded_no_col.csv"
    test_output = "data/raw/colombia_test.csv"
    
    # We exclude 'chl21' (Chile) as it is our test set? 
    # NO! For Strategy 2, Chile is in the index!
    # Wait, the user has Chile in `ccif_2018_cl_ejemplos_es.csv` (which is already extracted).
    # We will build the index by merging:
    # 1. base catalog
    # 2. coicop_es_expanded_no_col.csv (8 countries)
    # 3. Chile 100%
    
    index_sheets = ['arg17', 'bol15', 'bra17', 'cri18', 'dom18', 'mex18', 'per19', 'ury16'] # col16 is excluded
    
    print(f"Reading {excel_path}...")
    xl = pd.ExcelFile(excel_path)
    
    # 1. Extract Index Sheets
    all_examples = []
    for sheet in index_sheets:
        df = xl.parse(sheet, dtype=str)
        df = df.dropna(subset=['c_ccif_3', 'descrip'])
        df['id'] = df['c_ccif_3'].str.replace('.', '')
        df = df[df['id'].str.len() == 4]
        df = df[['id', 'descrip']].rename(columns={'descrip': 'text'})
        all_examples.append(df)
        
    master_df = pd.concat(all_examples, ignore_index=True).drop_duplicates(subset=['id', 'text'])
    master_df.to_csv(index_output, index=False)
    print(f"Saved {len(master_df)} index examples to {index_output}")
    
    # 2. Extract Colombia Test Set
    col_df = xl.parse('col16', dtype=str)
    col_df = col_df.dropna(subset=['c_ccif_3', 'descrip'])
    col_df['id'] = col_df['c_ccif_3'].str.replace('.', '')
    col_df = col_df[col_df['id'].str.len() == 4]
    col_df = col_df[['id', 'descrip']].rename(columns={'descrip': 'text'}).drop_duplicates()
    col_df.to_csv(test_output, index=False)
    print(f"Saved {len(col_df)} test examples to {test_output}")

if __name__ == "__main__":
    main()
