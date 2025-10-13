"""Base parser class for log files."""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseLogParser(ABC):
    """Abstract base class for log parsers."""
    
    def __init__(self, log_file_path: str):
        """Initialize the parser with a log file path.
        
        Args:
            log_file_path: Path to the log file to parse
        """
        self.log_file_path = log_file_path
        self.connections = []
    
    @abstractmethod
    def parse(self) -> List[Dict[str, str]]:
        """Parse the log file and extract network connections.
        
        Returns:
            List of connection dictionaries with 'source', 'destination', and 'protocol' keys
        """
        pass
    
    def get_connections(self) -> List[Dict[str, str]]:
        """Get the parsed connections.
        
        Returns:
            List of connection dictionaries
        """
        return self.connections
