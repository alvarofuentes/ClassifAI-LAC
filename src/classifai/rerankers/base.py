"""Base interface for all ReRanker implementations."""

from abc import ABC, abstractmethod
from typing import List

class ReRankerBase(ABC):
    """Abstract base class for all ReRankers.
    
    A ReRanker is used to compute a similarity score between a query
    and a list of documents.
    """

    @abstractmethod
    def predict(self, query: str, docs: List[str]) -> List[float]:
        """Calculates a relevance score for each document against the query.
        
        Args:
            query (str): The search query.
            docs (List[str]): A list of candidate documents.
            
        Returns:
            List[float]: A list of scores corresponding to the documents.
                         Higher score means more relevant.
        """
        pass
