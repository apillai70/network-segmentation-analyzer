"""Parser for Extrahop log files."""

import json
from typing import List, Dict
from .base_parser import BaseLogParser


class ExtrahopParser(BaseLogParser):
    """Parser for Extrahop monitoring logs."""
    
    def parse(self) -> List[Dict[str, str]]:
        """Parse Extrahop log file.
        
        Expected format: JSON lines with 'source_ip', 'dest_ip', and 'protocol' fields
        
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
                            'source': data.get('source_ip', 'unknown'),
                            'destination': data.get('dest_ip', 'unknown'),
                            'protocol': data.get('protocol', 'unknown'),
                            'port': data.get('port', 'unknown')
                        }
                        self.connections.append(connection)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Error: Log file not found: {self.log_file_path}")
        
        return self.connections
