import logging
from typing import List
from .base import ReRankerBase

class HuggingFaceCrossEncoder(ReRankerBase):
    """Cross-Encoder re-ranker using sentence-transformers."""
    
    def __init__(self, model_name: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"):
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise ImportError(
                "sentence_transformers is required for HuggingFaceCrossEncoder. "
                "Install it with: pip install sentence-transformers"
            )
            
        logging.info("Loading CrossEncoder model: %s", model_name)
        self.model = CrossEncoder(model_name)
        self.model_name = model_name

    def predict(self, query: str, docs: List[str]) -> List[float]:
        if not docs:
            return []
        # sentence-transformers CrossEncoder expects pairs of [query, doc]
        pairs = [[query, doc] for doc in docs]
        scores = self.model.predict(pairs)
        
        # Ensure scores is a list of floats
        if hasattr(scores, "tolist"):
            scores = scores.tolist()
            
        return [float(s) for s in scores]
