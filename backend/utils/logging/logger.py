"""Enhanced logging configuration for MAESTRO."""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class MaestroLogger:
    """Custom logger for MAESTRO system."""
    
    def __init__(self, name: str, log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level))
        
        # Create handlers
        self._add_console_handler()
        self._add_file_handler()
        
    def _add_console_handler(self):
        """Add console handler with formatting."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def _add_file_handler(self):
        """Add rotating file handler."""
        log_dir = Path("storage/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_dir / "maestro.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def log_agent_interaction(self, agent_name: str, query: str, response: dict):
        """Log agent interactions in structured format."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "query": query,
            "response_summary": str(response)[:200],
            "success": "error" not in response
        }
        self.logger.info(json.dumps(log_entry))

def get_logger(name: str) -> MaestroLogger:
    """Factory function to get logger instance."""
    return MaestroLogger(name)
