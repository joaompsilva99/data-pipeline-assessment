import pandas as pd
from abc import ABC, abstractmethod


class StorageBase(ABC):
    """Abstract interface for writing content to a storage"""

    @abstractmethod
    def write_csv(self, df: pd.DataFrame, destination: str) -> None:
        pass
