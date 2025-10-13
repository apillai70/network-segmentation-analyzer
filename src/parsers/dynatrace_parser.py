"""Parser for Dynatrace log files."""

import json
from typing import List, Dict
from .base_parser import BaseLogParser


class DynatraceParser(BaseLogParser):
    """Parser for Dynatrace monitoring logs."""
    
    def parse(self) -> List[Dict[str, str]]:
        """Parse Dynatrace log file.
        
        Expected format: JSON lines with 'from_entity', 'to_entity', and 'connection_type' fields
        
        Returns:
            List of connection dictionaries
        """
        self.connections = []
        
        try:
            with open(self.log_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        connection = {
                            'source': data.get('from_entity', 'unknown'),
                            'destination': data.get('to_entity', 'unknown'),
                            'protocol': data.get('connection_type', 'unknown'),
                            'port': data.get('port', 'unknown')
                        }
                        self.connections.append(connection)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Error: Log file not found: {self.log_file_path}")
        
        return self.connections
