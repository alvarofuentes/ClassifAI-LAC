import polars as pl
from pathlib import Path

ROOT = Path(__file__).parent.parent
INPUT = ROOT / "data" / "raw" / "tna_es.csv"
OUTPUT = ROOT / "data" / "raw" / "tna_gold_es.csv"

def main():
    print(f"Reading {INPUT}...")
    # Load with explicit string types to avoid numeric inference issues
    df = pl.read_csv(INPUT, schema_overrides={"id": pl.Utf8, "text": pl.Utf8})
    
    # Filter again just to be sure
    initial = df.height
    df = df.filter(pl.col("text").is_not_null() & (pl.col("text") != ""))
    print(f"Filtered {initial - df.height} empty rows.")
    
    # Write clean CSV
    df.write_csv(OUTPUT, quote_style="always")
    print(f"Successfully wrote {df.height} records to {OUTPUT}")

if __name__ == "__main__":
    main()
