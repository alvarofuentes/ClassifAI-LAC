"""Base interface for all ReRanker implementations."""

from abc import ABC, abstractmethod


class ReRankerBase(ABC):
    """Abstract base class for all ReRankers.

    A ReRanker is used to compute a similarity score between a query
    and a list of documents.
    """

    @abstractmethod
    def predict(self, query: str, docs: list[str]) -> list[float]:
        """Calculates a relevance score for each document against the query.

        Args:
            query (str): The search query.
            docs (list[str]): A list of candidate documents.

        Returns:
            list[float]: A list of scores corresponding to the documents.
                         Higher score means more relevant.
        """
        pass
