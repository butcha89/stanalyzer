import logging
import requests
import json
import configparser
import os
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramModule:
    def __init__(self, stats_module=None, recommendation_module=None, config_path=None):
        """Initialize the Telegram module"""
        # Default config path
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'config', 'configuration.ini'
            )
        
        # Read configuration
        config = configparser.ConfigParser()
        config.read(config_path)
        
        # Get Telegram settings
        self.token = config.get('telegram', 'token', fallback='6202998414:AAGdvgh5GLVkdYGMH-c7KfHbjEV25lzREs4')
        self.chat_id = config.get('telegram', 'chat_id', fallback='-802103319')
        self.enable_stats = config.getboolean('telegram', 'enable_stats_posting', fallback=True)
        self.enable_performer_recs = config.getboolean('telegram', 'enable_performer_recommendations', fallback=True)
        self.enable_scene_recs = config.getboolean('telegram', 'enable_scene_recommendations', fallback=True)
        
        # Store modules
        self.stats_module = stats_module
        self.recommendation_module = recommendation_module
    
    def format_performer_recommendations(self):
        """Format performer recommendations for output"""
        try:
            # Get performer recommendations
            performer_recs = self.recommendation_module.recommend_performers()
            
            if not performer_recs:
                logger.warning("No performer recommendations found")
                return "Keine Performer-Empfehlungen gefunden."
            
            # Build recommendation message
            message = "🌟 Performer-Empfehlungen 🌟\n\n"
            
            for rec in performer_recs[:5]:  # Limit to 5 recommendations for Telegram
                base_performer = rec['performer']
                similar = rec.get('similar_performers', [])
                
                message += f"**Empfohlener Performer**: {base_performer.get('name', 'Unknown')}\n"
                message += f"Measurements: {base_performer.get('measurements', 'N/A')}\n"
                message += f"O-Counter: {base_performer.get('o_counter', 0)}\n"
                message += f"Cup-to-BMI Factor: {base_performer.get('cup_to_bmi', 'N/A')}\n"
                
                if similar:
                    message += "\nÄhnlich zu:\n"
                    for sp in similar[:3]:  # Limit to 3 similar performers
                        message += (f"- {sp['name']} (Cup Size: {sp.get('cup_size', 'N/A')}, "
                                   f"O-Counter: {sp.get('o_counter', 0)}, "
                                   f"Similarity: {sp.get('similarity', 0):.2f})\n")
                
                message += "\n"
            
            return message
        
        except Exception as e:
            logger.error(f"Error formatting performer recommendations: {e}")
            return f"Fehler bei der Generierung von Performer-Empfehlungen: {e}"
    
    def format_scene_recommendations(self):
        """Format scene recommendations for output"""
        try:
            # Get scene recommendations
            scene_recs = self.recommendation_module.recommend_scenes()
            
            if not scene_recs:
                logger.warning("No scene recommendations found")
                return "Keine Szenen-Empfehlungen gefunden."
            
            # Build recommendation message
            message = "🎬 Szenen-Empfehlungen 🎬\n\n"
            
            # Process different recommendation categories
            categories = {
                'favorite_performer_scenes': "Szenen mit Lieblings-Performern",
                'non_favorite_performer_scenes': "Empfohlene Szenen",
                'recommended_performer_scenes': "Szenen mit empfohlenen Performern",
                'similar_tag_scenes': "Szenen mit ähnlichen Tags"
            }
            
            for category_key, category_name in categories.items():
                scenes = scene_recs.get(category_key, [])
                
                if not scenes:
                    continue
                
                message += f"**{category_name}**:\n"
                
                for i, scene in enumerate(scenes[:3], 1):
                    message += f"{i}. **{scene.get('title', 'Untitled')}**\n"
                    message += f"   Performers: {', '.join(scene.get('performers', ['N/A'])[:5])}\n"
                    
                    # Limit tag text to avoid Telegram message size issues
                    tags = scene.get('tags', ['N/A'])
                    tag_text = ', '.join(tags[:10])
                    if len(tags) > 10:
                        tag_text += "..."
                    message += f"   Tags: {tag_text}\n\n"
            
            return message
        
        except Exception as e:
            logger.error(f"Error formatting scene recommendations: {e}")
            return f"Fehler bei der Generierung von Szenen-Empfehlungen: {e}"
    
    def _get_bmi_category(self, bmi):
        """Get BMI category based on BMI value"""
        if bmi is None or pd.isna(bmi):
            return "Unbekannt"
        elif bmi < 18.5:
            return "Untergewicht"
        elif bmi < 25:
            return "Normalgewicht"
        elif bmi < 30:
            return "Übergewicht"
        else:
            return "Adipositas"

    def format_favorite_o_counter_stats(self, favorite_stats):
        """Format statistics about favorite vs non-favorite performers with o-counter"""
        message = "\n🔥 O-Counter bei Favoriten vs. Nicht-Favoriten 🔥\n"
        
        # Overall stats
        overall = favorite_stats.get('overall_stats', {})
        message += f"Gesamt-Performer mit O-Counter > 0: {overall.get('total_performers', 0)}\n"
        message += f"Favoriten: {overall.get('favorite_percentage', 0):.1f}%\n"
        message += f"Nicht-Favoriten: {overall.get('non_favorite_percentage', 0):.1f}%\n"
        
        # Favorite stats
        fav_stats = favorite_stats.get('favorite_stats', {})
        message += f"\nFavoriten mit O-Counter > 0: {fav_stats.get('count', 0)}\n"
        message += f"  Durchschnitt O-Counter: {fav_stats.get('avg_o_counter', 0):.2f}\n"
        message += f"  Median O-Counter: {fav_stats.get('median_o_counter', 0):.2f}\n"
        message += f"  Max O-Counter: {fav_stats.get('max_o_counter', 0)}\n"
        
        # Non-Favorite stats
        non_fav_stats = favorite_stats.get('non_favorite_stats', {})
        message += f"\nNicht-Favoriten mit O-Counter > 0: {non_fav_stats.get('count', 0)}\n"
        message += f"  Durchschnitt O-Counter: {non_fav_stats.get('avg_o_counter', 0):.2f}\n"
        message += f"  Median O-Counter: {non_fav_stats.get('median_o_counter', 0):.2f}\n"
        message += f"  Max O-Counter: {non_fav_stats.get('max_o_counter', 0)}\n"
        
        # List non-favorite performers with o-counter > 0
        non_fav_performers = non_fav_stats.get('performers', [])
        if non_fav_performers:
            message += "\n**Nicht-Favoriten mit O-Counter > 0**:\n"
            # Sort by o-counter and show top 10
            sorted_performers = sorted(non_fav_performers, key=lambda p: p.get('o_counter', 0), reverse=True)
            for i, performer in enumerate(sorted_performers[:10], 1):
                message += f"{i}. {performer.get('name', 'Unbekannt')} - O-Counter: {performer.get('o_counter', 0)}"
                if performer.get('rating100', 0) > 0:
                    message += f", Rating: {performer.get('rating100', 0)}/100"
                message += "\n"
        
        return message
    
    def format_rating_o_counter_correlation(self, rating_stats):
        """Format statistics about rating and o-counter correlation"""
        message = "\n⭐ Rating zu O-Counter Korrelation ⭐\n"
        
        # Overall correlation
        correlation = rating_stats.get('correlation', 0)
        message += f"Korrelation Rating-O-Counter: {correlation:.4f}\n"
        
        # High rated, high o-counter
        high_rated_high_o = rating_stats.get('high_rated_high_o', [])
        if high_rated_high_o:
            message += "\n**Hohe Bewertung, Hoher O-Counter**:\n"
            for i, performer in enumerate(high_rated_high_o[:5], 1):
                message += (f"{i}. {performer.get('name', 'Unbekannt')} - "
                           f"Rating: {performer.get('rating100', 0)}/100, "
                           f"O-Counter: {performer.get('o_counter', 0)}\n")
        
        # High rated, low o-counter
        high_rated_low_o = rating_stats.get('high_rated_low_o', [])
        if high_rated_low_o:
            message += "\n**Hohe Bewertung, Niedriger O-Counter**:\n"
            for i, performer in enumerate(high_rated_low_o[:5], 1):
                message += (f"{i}. {performer.get('name', 'Unbekannt')} - "
                           f"Rating: {performer.get('rating100', 0)}/100, "
                           f"O-Counter: {performer.get('o_counter', 0)}\n")
        
        # Low rated, high o-counter
        low_rated_high_o = rating_stats.get('low_rated_high_o', [])
        if low_rated_high_o:
            message += "\n**Niedrige Bewertung, Hoher O-Counter**:\n"
            for i, performer in enumerate(low_rated_high_o[:5], 1):
                message += (f"{i}. {performer.get('name', 'Unbekannt')} - "
                           f"Rating: {performer.get('rating100', 0)}/100, "
                           f"O-Counter: {performer.get('o_counter', 0)}\n")
        
        return message
    
    def format_sister_size_stats(self, sister_size_stats, volume_stats):
        """Format statistics about sister sizes and volumes"""
        message = "\n🔄 Sister Size und Volumen Statistik 🔄\n"
        
        # Original vs Sister stats
        original_vs_sister = sister_size_stats.get('original_vs_sister_stats', {})
        original_stats = original_vs_sister.get('original_stats', {})
        sister_stats = original_vs_sister.get('sister_stats', {})
        
        message += "\nVergleich Original vs. Sister Size:\n"
        message += f"- Durchschnitt O-Counter (Original): {original_stats.get('o_counter', 0):.2f}\n"
        message += f"- Durchschnitt O-Counter (Sister): {sister_stats.get('o_counter', 0):.2f}\n"
        message += f"- Durchschnitt Rating (Original): {original_stats.get('rating100', 0):.1f}/100\n"
        message += f"- Durchschnitt Rating (Sister): {sister_stats.get('rating100', 0):.1f}/100\n"
        
        # Top O-Counter sister sizes
        top_o_counter_sizes = original_vs_sister.get('top_o_counter_sizes', [])
        if top_o_counter_sizes:
            message += "\nSister Sizes mit höchstem O-Counter:\n"
            for i, size in enumerate(top_o_counter_sizes[:5], 1):
                message += (f"{i}. {size.get('sister_size', 'Unknown')}: "
                          f"O-Counter: {size.get('o_counter', 0):.2f}, "
                          f"Anzahl: {size.get('count', 0)}\n")
        
        # Volume stats
        volume_category_stats = volume_stats.get('volume_category_stats', [])
        if volume_category_stats:
            message += "\nO-Counter nach Volumen-Kategorie:\n"
            for stat in volume_category_stats:
                message += (f"- {stat.get('volume_category', 'Unknown')}: "
                          f"Avg O-Counter: {stat.get('avg_o_counter', 0):.2f}, "
                          f"Anzahl: {stat.get('performer_count', 0)}\n")
        
        # Volume correlation
        volume_correlation = volume_stats.get('volume_o_counter_correlation', 0)
        message += f"\nKorrelation Volumen zu O-Counter: {volume_correlation:.4f}\n"
        
        # Top volume performers
        top_volume_performers = volume_stats.get('top_volume_performers', [])
        if top_volume_performers:
            message += "\n**Top Performer nach Volumen:**\n"
            for i, performer in enumerate(top_volume_performers[:5], 1):
                message += (f"{i}. {performer.get('name', 'Unbekannt')} - "
                          f"Cup Size: {performer.get('cup_size', 'N/A')}, "
                          f"Volumen: {performer.get('volume_cc', 0):.1f}cc, "
                          f"Kategorie: {performer.get('volume_category', 'N/A')}, "
                          f"O-Counter: {performer.get('o_counter', 0)}\n")
        
        return message
    
    def format_statistics(self):
        """Format statistics for output"""
        try:
            # Generate statistics
            stats = self.stats_module.generate_all_stats()
            
            # Build stats message
            message = "📊 Stash Statistiken 📊\n\n"
            
            # Cup Size Distribution
            cup_stats = stats.get('cup_size_stats', {})
            cup_counts = cup_stats.get('cup_size_counts', {})
            
            message += "Cup-Größen Verteilung:\n"
            if cup_counts:
                sorted_cups = sorted(cup_counts.items(), key=lambda x: x[1], reverse=True)
                for cup, count in sorted_cups[:5]:  # Show top 5
                    message += f"    {cup}: {count} Performer\n"
            else:
                message += "    Keine Cup-Größen Daten verfügbar\n"
            
            # O-Counter Statistics
            message += "\nO-Counter Übersicht:\n"
            o_counter_stats = stats.get('o_counter_stats', {})
            avg_o_counter = o_counter_stats.get('average_o_counter', 0)
            median_o_counter = o_counter_stats.get('median_o_counter', 0)
            max_o_counter = o_counter_stats.get('max_o_counter', 0)
            total_performers = o_counter_stats.get('total_performers', 0)
            
            message += f"    Durchschnitt O-Counter: {avg_o_counter:.2f}\n"
            message += f"    Median O-Counter: {median_o_counter:.2f}\n"
            message += f"    Maximaler O-Counter: {max_o_counter}\n"
            message += f"    Anzahl Performer: {total_performers}\n"
            
            # Correlation Statistics
            cup_size_o_counter = stats.get('cup_size_o_counter_correlation', {})
            cup_letter_stats = cup_size_o_counter.get('cup_letter_o_stats', [])
            
            if cup_letter_stats:
                # Sort by average o-count
                sorted_stats_avg = sorted(cup_letter_stats, key=lambda x: x.get('avg_o_count', 0), reverse=True)
                
                message += "\nCup-Größe zu O-Counter Korrelation Average:\n"
                for stat in sorted_stats_avg[:5]:  # Show top 5
                    message += f"    Cup {stat.get('cup_letter', 'N/A')}: Durchschnitt O-Count {stat.get('avg_o_count', 0):.2f} (n={stat.get('performer_count', 0)})\n"
                
                # Check if we have median data
                if cup_letter_stats and 'median_o_count' in cup_letter_stats[0]:
                    # Sort by median o-count
                    sorted_stats_median = sorted(cup_letter_stats, key=lambda x: x.get('median_o_count', 0), reverse=True)
                    
                    message += "\nCup-Größe zu O-Counter Korrelation Median:\n"
                    for stat in sorted_stats_median[:5]:  # Show top 5
                        message += f"    Cup {stat.get('cup_letter', 'N/A')}: Median O-Count {stat.get('median_o_count', 0):.2f} (n={stat.get('performer_count', 0)})\n"
            
            # Ratio Statistics
            ratio_stats = stats.get('ratio_stats', {})
            ratio_data = ratio_stats.get('ratio_stats', [])
            
            if ratio_data:
                message += "\nCup-to-BMI Verhältnis:\n"
                sorted_ratios = sorted(ratio_data, 
                                       key=lambda x: abs(x.get('avg_cup_to_bmi', 0)) 
                                       if not pd.isna(x.get('avg_cup_to_bmi', 0)) else 0, 
                                       reverse=True)
                
                for stat in sorted_ratios[:5]:  # Show top 5
                    cup_to_bmi = stat.get('avg_cup_to_bmi', 0)
                    bmi_display = "nan" if pd.isna(cup_to_bmi) else f"{cup_to_bmi:.4f}"
                    message += f"    Cup {stat.get('cup_letter', 'N/A')}: Cup-to-BMI = {bmi_display} (n = {stat.get('performer_count', 0)})\n"
            
            # Get cup size dataframe for performer lookups
            cup_size_dataframe = cup_stats.get('cup_size_dataframe', [])
            
            # Create performer ID to cup size mapping
            performer_cup_map = {}
            if isinstance(cup_size_dataframe, list) and cup_size_dataframe:
                for performer_data in cup_size_dataframe:
                    if isinstance(performer_data, dict):
                        performer_id = performer_data.get('id')
                        if performer_id:
                            performer_cup_map[performer_id] = {
                                'cup_size': performer_data.get('cup_size', 'Unbekannt'),
                                'bmi': performer_data.get('bmi'),
                                'cup_to_bmi': performer_data.get('cup_to_bmi')
                            }
            
            # Top O-Counter Performers
            top_o_counter = stats.get('top_o_counter_performers', [])
            if top_o_counter:
                message += "\nTop O-Counter Performer:\n"
                for performer in top_o_counter[:5]:  # Show top 5
                    # Get performer details
                    performer_id = performer.get('id')
                    name = performer.get('name', 'N/A')
                    o_counter = performer.get('o_counter', 0)
                    scene_count = performer.get('scene_count', 0)
                    
                    # Extract cup size and bmi from measurements directly
                    measurements = performer.get('measurements', '')
                    cup_size = "Unbekannt"
                    
                    # Try to get cup size from performer_cup_map
                    cup_details = performer_cup_map.get(performer_id, {})
                    if cup_details.get('cup_size'):
                        cup_size = cup_details.get('cup_size')
                    # Fallback: Extract from measurements string
                    elif measurements:
                        import re
                        match = re.search(r'(\d{2})([A-KJ-Z]+)', measurements)
                        if match:
                            cup_size = f"{match.group(1)}{match.group(2)}"
                    
                    # Get BMI info
                    bmi = cup_details.get('bmi')
                    bmi_category = self._get_bmi_category(bmi)
                    cup_to_bmi = cup_details.get('cup_to_bmi')
                    
                    # Format performer output
                    message += f"    {name}\n"
                    message += f"    Cup: {cup_size}\n"
                    
                    if bmi is not None and not pd.isna(bmi):
                        message += f"    BMI: {bmi:.1f} ({bmi_category})\n"
                    
                    if cup_to_bmi is not None and not pd.isna(cup_to_bmi):
                        message += f"    Cup-to-BMI: {cup_to_bmi:.2f}\n"
                    
                    message += f"    O-Counter: {o_counter}\n"
                    message += f"    Szenenanzahl: {scene_count}\n\n"
            
            # Add new favorite and rating statistics
            favorite_o_counter_stats = stats.get('favorite_o_counter_stats', {})
            if favorite_o_counter_stats:
                message += self.format_favorite_o_counter_stats(favorite_o_counter_stats)
            
            rating_o_counter_correlation = stats.get('rating_o_counter_correlation', {})
            if rating_o_counter_correlation:
                message += self.format_rating_o_counter_correlation(rating_o_counter_correlation)
            
            # Add sister size statistics
            sister_size_stats = stats.get('sister_size_stats', {})
            volume_stats = stats.get('volume_stats', {})
            
            if sister_size_stats and 'original_vs_sister_stats' in sister_size_stats:
                message += self.format_sister_size_stats(sister_size_stats, volume_stats)
            
            return message
        
        except Exception as e:
            logger.error(f"Error formatting statistics: {e}", exc_info=True)
            return f"Fehler beim Generieren der Statistiken: {e}"
    
    def send_recommendations(self):
        """Send recommendations to Telegram"""
        logger.info("Preparing to send recommendations to Telegram")
        
        # Format recommendations
        performer_recs = self.format_performer_recommendations()
        scene_recs = self.format_scene_recommendations()
        
        # Combine messages
        full_message = performer_recs + "\n" + scene_recs
        
        # Print to console
        print("\n" + full_message)
        
        # Send to Telegram
        self._send_to_telegram(full_message)
    
    def send_statistics(self):
        """Send statistics to Telegram"""
        logger.info("Preparing to send statistics to Telegram")
        
        # Format statistics
        stats_message = self.format_statistics()
        
        # Print to console
        print("\n" + stats_message)
        
        # Send to Telegram
        self._send_to_telegram(stats_message)
    
    def _send_to_telegram(self, message):
        """Send message to Telegram"""
        if not self.token or not self.chat_id:
            logger.error("No Telegram token or chat ID configured")
            return
        
        try:
            # Split message if too long (Telegram has 4096 character limit)
            max_length = 4000  # Leave room for potential truncation message
            message_chunks = []
            
            # Split long messages into chunks
            while message:
                if len(message) <= max_length:
                    message_chunks.append(message)
                    break
                
                # Find a good split point
                split_point = message.rfind('\n', 0, max_length)
                if split_point == -1:
                    # If no newline found, try to split at a space
                    split_point = message.rfind(' ', 0, max_length)
                    if split_point == -1:
                        # If no space found, force split at max_length
                        split_point = max_length
                
                message_chunks.append(message[:split_point])
                message = message[split_point:].lstrip()
            
            # Send each chunk
            for i, chunk in enumerate(message_chunks, 1):
                # Add chunk number if multiple chunks
                if len(message_chunks) > 1:
                    chunk = f"Teil {i}/{len(message_chunks)}\n" + chunk
                
                # Prepare the API URL
                url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                
                # Prepare the payload
                payload = {
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown"
                }
                
                # Send the request
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent chunk {i} to Telegram")
                else:
                    logger.error(f"Failed to send chunk {i} to Telegram. Status code: {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")


def send_recommendations(recommendation_module, config_path=None):
    """Helper function to send recommendations"""
    telegram_module = TelegramModule(recommendation_module=recommendation_module, config_path=config_path)
    telegram_module.send_recommendations()


def send_statistics(stats_module, config_path=None):
    """Helper function to send statistics"""
    telegram_module = TelegramModule(stats_module=stats_module, config_path=config_path)
    telegram_module.send_statistics()
