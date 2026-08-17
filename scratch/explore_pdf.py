import sys
import fitz

def extract_body(pdf_path, out_txt):
    print(f"Opening {pdf_path}...")
    doc = fitz.open(pdf_path)
    
    with open(out_txt, "w", encoding="utf-8") as f:
        # Extract pages 100 to 120 which should be in the meat of the catalog
        for i in range(100, 120):
            if i >= len(doc):
                break
            text = doc[i].get_text()
            f.write(f"--- PAGE {i} ---\n")
            f.write(text)
            f.write("\n\n")
    print(f"Extraction saved to {out_txt}")

if __name__ == "__main__":
    extract_body("ccif_2018-cl.pdf", "scratch/pdf_body_sample.txt")
