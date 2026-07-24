from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseDataAdapter(ABC):
    """Abstract base class for Data Adapters (CSV / JSON / Stream Data)."""
    
    @abstractmethod
    def load_trip_data(self, trip_id: str) -> List[Dict[str, Any]]:
        """Loads and normalizes trip frame data at 20 FPS."""
        pass
