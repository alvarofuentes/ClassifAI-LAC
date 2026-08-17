import argparse
import pandas as pd
import os
import re

def clean_coicop_code(code: str) -> str:
    """
    Cleans a COICOP code by removing dots and taking the first 4 characters.
    For example: '01.1.1' -> '0111', '01.1.1.3' -> '0111'
    """
    if pd.isna(code):
        return ""
    code_str = str(code).replace('.', '')
    # For COICOP, the 4-digit level represents the class.
    return code_str[:4]

def main():
    parser = argparse.ArgumentParser(description="Augment a base catalog with regional examples.")
    parser.add_argument("--catalog", required=True, help="Path to base catalog CSV (must have 'id' and 'text' cols).")
    parser.add_argument("--examples", required=True, help="Path to examples file (CSV or Excel).")
    parser.add_argument("--text-col", required=True, help="Column name in examples containing the text description.")
    parser.add_argument("--code-col", required=True, help="Column name in examples containing the category code.")
    parser.add_argument("--output", required=True, help="Path to save the augmented catalog CSV.")
    parser.add_argument("--code-transform", choices=["none", "coicop_4digit"], default="none", help="Transformation to apply to the example codes.")
    
    args = parser.parse_args()
    
    print(f"Loading base catalog from {args.catalog}...")
    base_df = pd.read_csv(args.catalog, dtype=str)
    if "id" not in base_df.columns or "text" not in base_df.columns:
        raise ValueError("Base catalog must contain 'id' and 'text' columns.")
    
    print(f"Loading examples from {args.examples}...")
    ext = os.path.splitext(args.examples)[1].lower()
    
    examples_dfs = []
    if ext in [".xls", ".xlsx"]:
        xl = pd.ExcelFile(args.examples)
        for sheet in xl.sheet_names:
            print(f"  Reading sheet: {sheet}")
            df = xl.parse(sheet, dtype=str)
            if args.text_col in df.columns and args.code_col in df.columns:
                df = df[[args.code_col, args.text_col]].rename(columns={args.code_col: "id", args.text_col: "text"})
                examples_dfs.append(df)
            else:
                print(f"  Warning: sheet {sheet} missing required columns. Skipping.")
    elif ext == ".csv":
        df = pd.read_csv(args.examples, dtype=str)
        if args.text_col in df.columns and args.code_col in df.columns:
            df = df[[args.code_col, args.text_col]].rename(columns={args.code_col: "id", args.text_col: "text"})
            examples_dfs.append(df)
        else:
            raise ValueError(f"CSV missing required columns: {args.text_col}, {args.code_col}")
    else:
        raise ValueError("Unsupported file format for examples.")
        
    if not examples_dfs:
        raise ValueError("No valid examples found to append.")
        
    examples_df = pd.concat(examples_dfs, ignore_index=True)
    
    # Drop rows with NaN in id or text
    examples_df = examples_df.dropna(subset=["id", "text"])
    
    # Apply code transformations
    if args.code_transform == "coicop_4digit":
        examples_df["id"] = examples_df["id"].apply(clean_coicop_code)
        
    # Standardize texts (uppercase/lowercase depending on base? Let's just strip whitespace)
    examples_df["text"] = examples_df["text"].str.strip()
    
    # Drop duplicates in examples
    examples_df = examples_df.drop_duplicates()
    
    print(f"Extracted {len(examples_df)} unique examples.")
    
    # Filter out examples whose 'id' does not exist in the base catalog
    # (Optional, but good for data integrity)
    valid_ids = set(base_df["id"].dropna().unique())
    original_len = len(examples_df)
    examples_df = examples_df[examples_df["id"].isin(valid_ids)]
    print(f"Kept {len(examples_df)} examples after filtering by valid base catalog IDs (dropped {original_len - len(examples_df)}).")
    
    # Append to base catalog
    augmented_df = pd.concat([base_df, examples_df], ignore_index=True)
    augmented_df = augmented_df.drop_duplicates()
    
    augmented_df.to_csv(args.output, index=False)
    print(f"Successfully wrote {len(augmented_df)} rows to {args.output}")

if __name__ == "__main__":
    main()
