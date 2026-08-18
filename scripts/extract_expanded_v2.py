import pandas as pd
import os

def main():
    excel_path = "260319_COICOP.xlsx"
    output_path = "data/raw/coicop_es_expanded_v2.csv"
    
    # We exclude 'chl21' (Chile) as it is our test set.
    # We exclude 'COICOP' and 'COICOP_subclase' as they are not country data.
    country_sheets = ['arg17', 'bol15', 'bra17', 'col16', 'cri18', 'dom18', 'mex18', 'per19', 'ury16']
    
    print(f"Reading {excel_path}...")
    xl = pd.ExcelFile(excel_path)
    
    all_examples = []
    
    for sheet in country_sheets:
        print(f"Processing sheet: {sheet}")
        if sheet not in xl.sheet_names:
            print(f"  Warning: {sheet} not found.")
            continue
            
        df = xl.parse(sheet, dtype=str)
        
        # Ensure required columns exist
        if 'c_ccif_3' not in df.columns or 'descrip' not in df.columns:
            print(f"  Warning: Missing columns in {sheet}. Skipping.")
            continue
            
        # Drop rows with missing ID or text
        df = df.dropna(subset=['c_ccif_3', 'descrip'])
        
        # Clean ID: remove dots
        df['id'] = df['c_ccif_3'].str.replace('.', '')
        
        # Keep only rows where ID is exactly 4 digits
        df = df[df['id'].str.len() == 4]
        
        # Rename and keep relevant columns
        df = df[['id', 'descrip']].rename(columns={'descrip': 'text'})
        
        all_examples.append(df)
        print(f"  Extracted {len(df)} 4-digit examples.")
        
    master_df = pd.concat(all_examples, ignore_index=True)
    
    # Remove exact duplicates (same id and text)
    initial_len = len(master_df)
    master_df = master_df.drop_duplicates(subset=['id', 'text'])
    print(f"\nDropped {initial_len - len(master_df)} duplicates.")
    
    print(f"Saving {len(master_df)} examples to {output_path}...")
    master_df.to_csv(output_path, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
