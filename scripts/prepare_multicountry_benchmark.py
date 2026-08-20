"""Script to extract and standardize multi-country benchmark data from docs/260819_COICOP.xlsx."""

import re
import sys
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = ROOT_DIR / "docs" / "260819_COICOP.xlsx"
FALLBACK_EXCEL_PATH = ROOT_DIR / "260319_COICOP.xlsx"
OUTPUT_DIR = ROOT_DIR / "data" / "benchmarks"

SHEET_METADATA = {
    "arg17": {"country": "Argentina", "country_code": "ARG", "year": 2017, "lang": "es"},
    "bol15": {"country": "Bolivia", "country_code": "BOL", "year": 2015, "lang": "es"},
    "bra17": {"country": "Brasil", "country_code": "BRA", "year": 2017, "lang": "pt"},
    "chl21": {"country": "Chile", "country_code": "CHL", "year": 2021, "lang": "es"},
    "col16": {"country": "Colombia", "country_code": "COL", "year": 2016, "lang": "es"},
    "cri18": {"country": "Costa Rica", "country_code": "CRI", "year": 2018, "lang": "es"},
    "cri24": {"country": "Costa Rica", "country_code": "CRI", "year": 2024, "lang": "es"},
    "dom18": {"country": "Rep. Dominicana", "country_code": "DOM", "year": 2018, "lang": "es"},
    "ecu24": {"country": "Ecuador", "country_code": "ECU", "year": 2024, "lang": "es"},
    "hnd23": {"country": "Honduras", "country_code": "HND", "year": 2023, "lang": "es"},
    "mex18": {"country": "México", "country_code": "MEX", "year": 2018, "lang": "es"},
    "mex24": {"country": "México", "country_code": "MEX", "year": 2024, "lang": "es"},
    "pan17": {"country": "Panamá", "country_code": "PAN", "year": 2017, "lang": "es"},
    "per19": {"country": "Perú", "country_code": "PER", "year": 2019, "lang": "es"},
    "ury16": {"country": "Uruguay", "country_code": "URY", "year": 2016, "lang": "es"},
}


def clean_coicop_code(code_val) -> str | None:
    """Normalize COICOP class code into 4 digits format (e.g. '01.1.1' -> '0111')."""
    if pd.isna(code_val):
        return None
    cleaned = str(code_val).strip().replace(".", "")
    cleaned = re.sub(r"[^\d]", "", cleaned)

    # Pad leading zero if 3 digits (e.g. 111 -> 0111)
    if len(cleaned) == 3:
        cleaned = "0" + cleaned

    if len(cleaned) >= 4:
        return cleaned[:4]
    return None


def clean_text(text_val) -> str:
    """Normalize query text string."""
    if pd.isna(text_val):
        return ""
    text = str(text_val).strip()
    # Replace multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text


def extract_benchmark():
    file_path = EXCEL_PATH if EXCEL_PATH.exists() else FALLBACK_EXCEL_PATH
    print(f"Reading multi-country spreadsheet: {file_path}")

    xl = pd.ExcelFile(file_path)
    all_rows = []

    for sheet_name in xl.sheet_names:
        if sheet_name not in SHEET_METADATA:
            continue

        meta = SHEET_METADATA[sheet_name]
        df = xl.parse(sheet_name)
        print(f"Processing sheet {sheet_name} ({meta['country']} {meta['year']}) with {len(df)} rows...")

        if "descrip" not in df.columns or "c_ccif_3" not in df.columns:
            print(f"⚠️ Warning: Missing required columns in {sheet_name}. Found: {df.columns.tolist()[:5]}")
            continue

        for idx, row in df.iterrows():
            text = clean_text(row.get("descrip", ""))
            code_4d = clean_coicop_code(row.get("c_ccif_3", ""))

            if not text or not code_4d:
                continue

            division_2d = code_4d[:2]

            all_rows.append(
                {
                    "sample_id": f"{sheet_name}_{idx}",
                    "sheet_name": sheet_name,
                    "country": meta["country"],
                    "country_code": meta["country_code"],
                    "year": meta["year"],
                    "lang": meta["lang"],
                    "query_text": text,
                    "target_code_4d": code_4d,
                    "target_division_2d": division_2d,
                    "c_gasto": str(row.get("c_gasto", "")).strip(),
                }
            )

    benchmark_df = pd.DataFrame(all_rows)
    print(f"\n✅ Extracted total of {len(benchmark_df)} valid benchmark items across {len(SHEET_METADATA)} sheets.")

    print("\nBreakdown by country dataset:")
    summary = (
        benchmark_df.groupby(["sheet_name", "country", "year"])
        .agg(total_items=("query_text", "count"), unique_classes=("target_code_4d", "nunique"))
        .reset_index()
    )
    print(summary.to_string(index=False))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = OUTPUT_DIR / "lac_multicountry_benchmark.parquet"
    csv_path = OUTPUT_DIR / "lac_multicountry_benchmark.csv"

    # Ensure clean string formatting with 4 digits
    benchmark_df["target_code_4d"] = benchmark_df["target_code_4d"].astype(str).str.zfill(4)
    benchmark_df["target_division_2d"] = benchmark_df["target_code_4d"].str[:2]

    benchmark_df.to_csv(csv_path, index=False)
    import polars as pl

    pl_df = pl.read_csv(
        csv_path,
        schema_overrides={
            "target_code_4d": pl.String,
            "target_division_2d": pl.String,
            "c_gasto": pl.String,
        },
    )
    pl_df.write_parquet(parquet_path)
    print(f"\n💾 Saved benchmark dataset to:\n- {parquet_path}\n- {csv_path}")
    return benchmark_df


if __name__ == "__main__":
    extract_benchmark()
