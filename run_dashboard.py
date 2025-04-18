#!/usr/bin/env python3
"""
Stash Analytics Dashboard Starter

Dieses Skript startet das interaktive Dashboard für die Analyse von StashApp-Daten.
"""

import os
import sys
import logging
import argparse
import pathlib
from stash_api import StashClient
from modules.statistics import StatisticsModule
from modules.recommendations import RecommendationModule
from modules.dashboard import DashboardModule

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Kommandozeilenargumente parsen"""
    parser = argparse.ArgumentParser(description='Stash Analytics Dashboard')
    parser.add_argument('--port', type=int, default=8050, help='Port für den Dashboard-Server (Standard: 8050)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host für den Dashboard-Server (Standard: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', help='Debug-Modus aktivieren')
    return parser.parse_args()

def ensure_data_directories():
    """Stellt sicher, dass alle benötigten Datenverzeichnisse existieren"""
    # Definiere die Verzeichnisse, die existieren müssen
    data_dirs = [
        "data",
        "data/cache",
        "data/exports",
        "config"
    ]
    
    # Erstelle die Verzeichnisse, falls sie nicht existieren
    for directory in data_dirs:
        dir_path = pathlib.Path(directory)
        if not dir_path.exists():
            logger.info(f"Erstelle Verzeichnis: {directory}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # Prüfe, ob eine Konfigurationsdatei existiert, falls nicht, erstelle eine Beispielkonfiguration
    config_file = pathlib.Path("config/configuration.ini")
    if not config_file.exists():
        # Verwende die Werte aus stash_api.py CONFIG
        from stash_api import CONFIG
        
        logger.info("Erstelle Konfigurationsdatei mit Werten aus stash_api.py")
        with open(config_file, "w") as f:
            f.write(f"""[stash]
url = {CONFIG.get("stash_url", "http://localhost:9999")}
api_key = {CONFIG.get("api_key", "")}

[dashboard]
cache_duration = 3600

[discord]
webhook_url = 
enable_stats_posting = false
enable_performer_recommendations = false
enable_scene_recommendations = false
""")

def main():
    """Hauptfunktion zum Starten des Dashboards"""
    args = parse_arguments()
    
    # Stelle sicher, dass alle benötigten Verzeichnisse existieren
    ensure_data_directories()
    
    # Importiere CONFIG aus stash_api.py
    from stash_api import CONFIG
    
    logger.info("Initialisiere Stash-Client...")
    logger.info(f"Verwende Stash-URL: {CONFIG.get('stash_url', 'http://localhost:9999')}")
    stash_client = StashClient()
    
    # Überprüfe, ob die Verbindung funktioniert
    try:
        performers = stash_client.get_performers()
        logger.info(f"Verbindung erfolgreich: {len(performers)} Performer gefunden")
    except Exception as e:
        logger.error(f"Fehler bei der Verbindung zum Stash-Server: {e}")
        logger.error("Bitte überprüfe die Stash-URL und den API-Key in config/configuration.ini oder stash_api.py")
    
    logger.info("Initialisiere Statistik-Module...")
    stats_module = StatisticsModule(stash_client)
    
    logger.info("Initialisiere Empfehlungs-Module...")
    recommendation_module = RecommendationModule(stash_client, stats_module)
    
    logger.info("Initialisiere Dashboard...")
    dashboard = DashboardModule(stats_module, recommendation_module)
    
    logger.info(f"Starte Dashboard-Server auf http://{args.host}:{args.port}/")
    dashboard.run_server(debug=args.debug, port=args.port, host=args.host)

if __name__ == "__main__":
    main()
