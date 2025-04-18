import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StatsExporter:
    """Module for exporting statistics to JSON files."""
    
    def __init__(self, stats_module=None, output_dir=None):
        """Initialize the stats exporter module.
        
        Args:
            stats_module: Statistics module to get data from
            output_dir: Directory to save output files (default: data/stats)
        """
        self.stats_module = stats_module
        self.output_dir = output_dir or os.path.join('data', 'stats')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def export_stats(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Export statistics to a JSON file.
        
        Args:
            filename: Optional custom filename (default: stash_stats_YYYYMMDD_HHMMSS.json)
            
        Returns:
            Dict with export results including path and status
        """
        if not self.stats_module:
            logger.error("No statistics module provided")
            return {
                'success': False,
                'error': 'No statistics module provided',
                'path': None
            }
        
        try:
            # Generate statistics
            logger.info("Generating statistics for export...")
            stats = self.stats_module.generate_all_stats()
            
            # Add metadata
            stats_with_metadata = {
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0',
                    'generated_by': 'StatsExporter'
                },
                'statistics': stats
            }
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"stash_stats_{timestamp}.json"
            
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Full path
            filepath = os.path.join(self.output_dir, filename)
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats_with_metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Statistics exported to {filepath}")
            
            # Also save a copy as stash_stats.json (latest version)
            latest_filepath = os.path.join(self.output_dir, 'stash_stats.json')
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(stats_with_metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Latest statistics saved to {latest_filepath}")
            
            return {
                'success': True,
                'path': filepath,
                'latest_path': latest_filepath,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting statistics: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'path': None
            }
    
    def load_latest_stats(self) -> Dict[str, Any]:
        """Load the latest statistics from stash_stats.json.
        
        Returns:
            Dict with statistics or empty dict if file not found
        """
        latest_filepath = os.path.join(self.output_dir, 'stash_stats.json')
        
        try:
            if os.path.exists(latest_filepath):
                with open(latest_filepath, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                logger.info(f"Loaded statistics from {latest_filepath}")
                return stats
            else:
                logger.warning(f"No statistics file found at {latest_filepath}")
                return {}
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
            return {}


def export_stats(stats_module, filename=None, output_dir=None):
    """Helper function to export statistics."""
    exporter = StatsExporter(stats_module=stats_module, output_dir=output_dir)
    return exporter.export_stats(filename)


def load_latest_stats(output_dir=None):
    """Helper function to load the latest statistics."""
    exporter = StatsExporter(output_dir=output_dir)
    return exporter.load_latest_stats()
