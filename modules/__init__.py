# Initialisierung der Module
# Importiere nur die Klassen, die direkt benötigt werden
from .statistics import StatisticsModule
from .recommendations import RecommendationModule
from .discord import DiscordModule, send_recommendations, send_statistics
from .telegram import TelegramModule
from .stats_exporter import StatsExporter, export_stats, load_latest_stats
