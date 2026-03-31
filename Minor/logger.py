"""
Output Logger for simulation tracking and JSON results storage.
"""

import os
import json
import numpy as np
from datetime import datetime


class OutputLogger:
    """
    Logger class that writes output to console and saves JSON results.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the logger with an output directory.
        
        Args:
            output_dir: Directory where output files will be saved
        """
        self.output_dir = output_dir
        self.log_lines = []
        self.start_time = datetime.now()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        self.json_file = os.path.join(output_dir, f"simulation_results_{timestamp}.json")
    
    def log(self, message: str):
        """Log a message to console and internal buffer."""
        print(message)
        self.log_lines.append(message)
    
    def save_json_results(self, results: dict):
        """
        Save results as JSON for programmatic analysis.
        
        Args:
            results: Dictionary containing simulation results
            
        Returns:
            str: Path to the saved JSON file
        """
        def convert_to_serializable(obj):
            """Recursively convert numpy types to Python native types."""
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(i) for i in obj]
            else:
                return obj
        
        serializable_results = convert_to_serializable(results)
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2)
        return self.json_file


# Global logger instance
LOGGER = OutputLogger()
