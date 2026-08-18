import pandas as pd
import sys
import time

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("Please install deep-translator: uv add deep-translator")
    sys.exit(1)

def main():
    print("Reading Excel file...")
    # Read the first sheet, it seems it has no headers
    df = pd.read_excel('data/raw/COICOP_2018_English_structure.xlsx', header=None, names=['Code', 'Title', 'Definition', 'Includes', 'Includes also', 'Excludes'])
    
    # We only care about rows that have a Code
    df = df.dropna(subset=['Code'])
    
    # Create clean ID by removing dots
    df['clean_id'] = df['Code'].astype(str).str.replace('.', '')
    
    # The target level is 4-digits (e.g., '0111' from '01.1.1' or '01.1.1.1')
    # We will take the first 4 characters of the clean ID to group them
    df['id'] = df['clean_id'].str[:4]
    
    # We only care about valid 4-digit groups (excluding 2 or 3 digit summaries if they don't have subclass data)
    # Actually, all subclasses fall under a 4 digit class.
    df = df[df['id'].str.len() == 4]
    
    print(f"Extracted {len(df)} rows. Grouping by 4-digit ID...")
    
    # Fill NAs with empty string for concatenation
    cols_to_concat = ['Title', 'Definition', 'Includes', 'Includes also', 'Excludes']
    for col in cols_to_concat:
        if col in df.columns:
            df[col] = df[col].fillna('')
    
    # Concatenate text for each row
    def build_text(row):
        parts = []
        if str(row.get('Title', '')).strip():
            parts.append(f"Title: {str(row['Title']).strip()}")
        if str(row.get('Definition', '')).strip():
            parts.append(f"Definition: {str(row['Definition']).strip()}")
        if str(row.get('Includes', '')).strip():
            parts.append(f"Includes: {str(row['Includes']).strip()}")
        if str(row.get('Includes also', '')).strip():
            parts.append(f"Includes also: {str(row['Includes also']).strip()}")
        if str(row.get('Excludes', '')).strip():
            parts.append(f"Excludes: {str(row['Excludes']).strip()}")
        return " | ".join(parts)
        
    df['full_text'] = df.apply(build_text, axis=1)
    
    # Group by 'id' (the 4-digit code) and join all full_texts
    grouped = df.groupby('id')['full_text'].apply(lambda texts: " || ".join(texts)).reset_index()
    
    print(f"Found {len(grouped)} unique 4-digit categories. Starting translation...")
    
    translator = GoogleTranslator(source='en', target='es')
    
    translated_texts = []
    
    # Translate one by one with a small delay to avoid rate limits
    for idx, row in grouped.iterrows():
        cat_id = row['id']
        text = row['full_text']
        
        # Google Translate has a 5000 char limit per request
        if len(text) > 4900:
            text = text[:4900] + "..."
            
        print(f"Translating ID {cat_id} ({idx+1}/{len(grouped)})...")
        try:
            translated = translator.translate(text)
            translated_texts.append(translated)
        except Exception as e:
            print(f"Error translating ID {cat_id}: {e}")
            translated_texts.append(text) # fallback to english
            
        time.sleep(0.5) # respectful delay
        
    grouped['text'] = translated_texts
    
    # Clean up the spanish text to remove newlines, etc.
    grouped['text'] = grouped['text'].str.replace('\n', ' ').str.replace('\r', '')
    
    output_file = 'data/raw/coicop_2018_es_traducido.csv'
    grouped[['id', 'text']].to_csv(output_file, index=False)
    
    print(f"Translation complete! Saved base catalog to {output_file}")

if __name__ == '__main__':
    main()
