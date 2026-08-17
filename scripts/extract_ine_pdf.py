import re
import fitz
import pandas as pd

def extract_examples_from_pdf(pdf_path, output_csv):
    print(f"Reading {pdf_path}...")
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"

    print("Parsing text with regex...")
    
    # We want to find sections that start with Clase, Subclase, or Producto followed by a code
    # e.g., "Producto 01.1.8.09.02" or "Subclase 01.1.8.09.00"
    # Then we capture everything until the next Clase/Subclase/Producto or Excluye
    
    # Regex to match the code block
    block_pattern = re.compile(
        r"(?:Clase|Subclase|Producto)\s+(\d{2}\.\d\.\d(?:\.\d{2}\.\d{2})?)\s*\n"
        r"(.*?)" # name of category
        r"Incluye:\s*\n"
        r"((?:-\s*.*?\n)+)", 
        re.MULTILINE | re.DOTALL
    )

    examples = []
    
    # Find all matching blocks
    for match in block_pattern.finditer(full_text):
        raw_code = match.group(1).strip()
        # Clean code to 4 digits: "01.1.8.09.02" -> "0118"
        clean_code = raw_code.replace('.', '')[:4]
        
        incluye_text = match.group(3)
        
        # Parse bullet points
        bullets = re.findall(r"-\s*(.*?)(?:\n|$)", incluye_text)
        for bullet in bullets:
            # Bullet items are usually comma separated and end with ; or .
            # e.g., "chicles, dulces, caramelos, toffee."
            clean_bullet = bullet.strip().rstrip(';').rstrip('.')
            items = [item.strip() for item in clean_bullet.split(',') if item.strip()]
            for item in items:
                # Discard items that are too long (probably full sentences) or too short
                if 2 < len(item) < 100 and "etc" not in item.lower():
                    examples.append({"id": clean_code, "text": item})

    df = pd.DataFrame(examples)
    df = df.drop_duplicates()
    
    # Optional: Filter out codes that don't look like 4 digits (e.g. they might be 3 digits if it was a group)
    df = df[df['id'].str.len() == 4]
    
    print(f"Extracted {len(df)} unique examples.")
    df.to_csv(output_csv, index=False)
    print(f"Saved to {output_csv}")

if __name__ == "__main__":
    extract_examples_from_pdf("ccif_2018-cl.pdf", "data/raw/ine_chile_examples.csv")
