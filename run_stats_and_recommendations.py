#!/usr/bin/env python3
"""
Skript zum Ausführen der Statistikanalyse, Empfehlungen und Benachrichtigungen.
Exportiert Statistiken als JSON und sendet sie an Discord und Telegram.
"""

import os
import logging
import argparse
import configparser
from datetime import datetime

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'stats_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def ensure_directories():
    """Stelle sicher, dass alle benötigten Verzeichnisse existieren."""
    directories = ['logs', 'data', 'data/stats', 'data/cache', 'config']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def ensure_config():
    """Stelle sicher, dass die Konfigurationsdatei existiert."""
    config_path = os.path.join('config', 'configuration.ini')
    
    if not os.path.exists(config_path):
        logger.info("Erstelle neue Konfigurationsdatei")
        config = configparser.ConfigParser()
        
        # Discord-Konfiguration
        config['discord'] = {
            'webhook_url': '',
            'enable_stats_posting': 'true',
            'enable_performer_recommendations': 'true',
            'enable_scene_recommendations': 'true'
        }
        
        # Telegram-Konfiguration
        config['telegram'] = {
            'token': '6202998414:AAGdvgh5GLVkdYGMH-c7KfHbjEV25lzREs4',
            'chat_id': '-802103319',
            'enable_stats_posting': 'true',
            'enable_performer_recommendations': 'true',
            'enable_scene_recommendations': 'true'
        }
        
        # Stash-Konfiguration
        config['stash'] = {
            'url': 'http://localhost:9999',
            'api_key': '',
            'username': '',
            'password': ''
        }
        
        # Allgemeine Konfiguration
        config['general'] = {
            'export_stats': 'true',
            'send_to_discord': 'true',
            'send_to_telegram': 'true'
        }
        
        with open(config_path, 'w') as configfile:
            config.write(configfile)
    
    return config_path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Stash Statistiken und Empfehlungen')
    parser.add_argument('--stats-only', action='store_true', help='Nur Statistiken generieren')
    parser.add_argument('--recommendations-only', action='store_true', help='Nur Empfehlungen generieren')
    parser.add_argument('--no-discord', action='store_true', help='Keine Discord-Benachrichtigungen senden')
    parser.add_argument('--no-telegram', action='store_true', help='Keine Telegram-Benachrichtigungen senden')
    parser.add_argument('--no-export', action='store_true', help='Keine JSON-Datei exportieren')
    return parser.parse_args()

def main():
    """Hauptfunktion zum Ausführen aller Module."""
    # Stelle sicher, dass alle Verzeichnisse existieren
    ensure_directories()
    
    # Stelle sicher, dass die Konfigurationsdatei existiert
    config_path = ensure_config()
    
    # Parse Kommandozeilenargumente
    args = parse_args()
    
    # Lade Konfiguration
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Importiere Module
    from stash_api import StashClient
    from modules import (
        StatisticsModule, 
        RecommendationModule, 
        DiscordModule, 
        TelegramModule,
        export_stats
    )
    
    # Initialisiere StashClient
    stash_url = config.get('stash', 'url', fallback='http://localhost:9999')
    api_key = config.get('stash', 'api_key', fallback='')
    
    logger.info(f"Verbinde mit Stash API: {stash_url}")
    stash_client = StashClient(url=stash_url, api_key=api_key)
    
    # Initialisiere Module
    stats_module = StatisticsModule(stash_client=stash_client)
    recommendation_module = RecommendationModule(stash_client=stash_client, stats_module=stats_module)
    
    # Generiere und exportiere Statistiken
    if not args.recommendations_only:
        logger.info("Generiere Statistiken...")
        stats = stats_module.generate_all_stats()
        logger.info("Statistiken erfolgreich generiert")
        
        # Exportiere Statistiken als JSON
        if not args.no_export and config.getboolean('general', 'export_stats', fallback=True):
            logger.info("Exportiere Statistiken als JSON...")
            export_result = export_stats(stats_module)
            if export_result['success']:
                logger.info(f"Statistiken exportiert nach: {export_result['path']}")
            else:
                logger.error(f"Fehler beim Exportieren der Statistiken: {export_result.get('error')}")
    
    # Sende Statistiken an Discord
    if not args.recommendations_only and not args.no_discord and config.getboolean('general', 'send_to_discord', fallback=True):
        logger.info("Sende Statistiken an Discord...")
        discord_module = DiscordModule(stats_module=stats_module, config_path=config_path)
        discord_module.send_statistics()
    
    # Sende Statistiken an Telegram
    if not args.recommendations_only and not args.no_telegram and config.getboolean('general', 'send_to_telegram', fallback=True):
        logger.info("Sende Statistiken an Telegram...")
        telegram_module = TelegramModule(stats_module=stats_module, config_path=config_path)
        telegram_module.send_statistics()
    
    # Generiere und sende Empfehlungen
    if not args.stats_only:
        logger.info("Generiere Empfehlungen...")
        performer_recs = recommendation_module.recommend_performers()
        scene_recs = recommendation_module.recommend_scenes()
        logger.info(f"Empfehlungen generiert: {len(performer_recs)} Performer, {sum(len(scenes) for scenes in scene_recs.values())} Szenen")
        
        # Sende Empfehlungen an Discord
        if not args.no_discord and config.getboolean('general', 'send_to_discord', fallback=True):
            logger.info("Sende Empfehlungen an Discord...")
            discord_module = DiscordModule(recommendation_module=recommendation_module, config_path=config_path)
            discord_module.send_recommendations()
        
        # Sende Empfehlungen an Telegram
        if not args.no_telegram and config.getboolean('general', 'send_to_telegram', fallback=True):
            logger.info("Sende Empfehlungen an Telegram...")
            telegram_module = TelegramModule(recommendation_module=recommendation_module, config_path=config_path)
            telegram_module.send_recommendations()
    
    logger.info("Alle Aufgaben abgeschlossen")

if __name__ == "__main__":
    main()
