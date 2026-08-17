import pandas as pd

try:
    file_path = "260319_COICOP.xlsx"
    xl = pd.ExcelFile(file_path)
    print("Sheets:", xl.sheet_names)
    
    for sheet in xl.sheet_names:
        print(f"\n--- Sheet: {sheet} ---")
        df = xl.parse(sheet)
        print("Columns:", df.columns.tolist())
        print(df.head(5).to_string())
except Exception as e:
    print(f"Error: {e}")
