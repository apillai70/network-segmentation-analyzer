"""Parser for Splunk log files."""

import json
from typing import List, Dict
from .base_parser import BaseLogParser


class SplunkParser(BaseLogParser):
    """Parser for Splunk monitoring logs."""
    
    def parse(self) -> List[Dict[str, str]]:
        """Parse Splunk log file.
        
        Expected format: JSON lines with 'src', 'dest', and 'app' fields
        
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
                            'source': data.get('src', 'unknown'),
                            'destination': data.get('dest', 'unknown'),
                            'protocol': data.get('app', 'unknown'),
                            'port': data.get('dest_port', 'unknown')
                        }
                        self.connections.append(connection)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Error: Log file not found: {self.log_file_path}")
        
        return self.connections
