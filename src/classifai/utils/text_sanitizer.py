import re
import unicodedata
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TextSanitizer:
    """Utility class to clean text and detect file encoding."""

    @staticmethod
    def detect_encoding(file_path: Path) -> str:
        """Detect encoding of a file, falling back to utf-8."""
        try:
            import charset_normalizer
            with open(file_path, "rb") as f:
                payload = f.read(1024 * 10) # 10KB sample
                result = charset_normalizer.detect(payload)
                encoding = result["encoding"] or "utf-8"
                logger.info(f"Detected encoding for {file_path.name}: {encoding}")
                return encoding
        except (ImportError, Exception):
            return "utf-8"

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean invisible characters, control chars, and normalize Unicode."""
        if not isinstance(text, str):
            return ""

        # Remove control characters and invisible stuff
        # [\x00-\x1F\x7F-\x9F] are C0/C1 control codes
        # \ufeff is the BOM
        # Zero-width spaces and other non-printing chars
        text = re.sub(r"[\x00-\x1F\x7F-\x9F\ufeff]", "", text)
        
        # Normalize Unicode to NFKC (compatible characters)
        text = unicodedata.normalize("NFKC", text)
        
        # Strip and deduplicate spaces
        text = " ".join(text.split())
        
        return text

    @classmethod
    def sanitize_dataframe(cls, df, columns: list[str]):
        """Sanitize specified columns in a Polars or Pandas DataFrame."""
        # Polars implementation
        try:
            import polars as pl
            if isinstance(df, pl.DataFrame):
                for col in columns:
                    if col in df.columns:
                        df = df.with_columns(
                            pl.col(col).map_elements(lambda x: cls.clean_text(str(x)) if x is not None else "", return_dtype=pl.String)
                        )
                return df
        except ImportError:
            pass

        # Pandas fallback
        for col in columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: cls.clean_text(str(x)) if x is not None else "")
        return df
