import logging
import numpy as np
import pandas as pd
import random
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class RecommendationModule:
    def __init__(self, stash_client=None, stats_module=None):
        """Initialize the recommendation module"""
        self.stash_client = stash_client
        self.stats_module = stats_module
        self.performers_data = []
        self.scenes_data = []
        
        # Cache für bereits generierte Empfehlungen
        self._performer_recommendation_cache = {}
        self._scene_recommendation_cache = {}
        
        # Zähler für Empfehlungsrotation
        self._recommendation_counter = 0
        
        # Load data
        self._load_data()
    
    def _load_data(self):
        """Load performers and scenes data"""
        try:
            self.performers_data = self.stash_client.get_performers() if self.stash_client else []
            self.scenes_data = self.stash_client.get_scenes() if self.stash_client else []
            logger.info(f"Loaded {len(self.performers_data)} performers and {len(self.scenes_data)} scenes")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.performers_data = []
            self.scenes_data = []
    
    def reload_data(self):
        """Reload data and clear caches"""
        self._load_data()
        self._performer_recommendation_cache = {}
        self._scene_recommendation_cache = {}
        self._recommendation_counter = 0
        logger.info("Reloaded data and cleared recommendation caches")
    
    def _calculate_similarity(self, base_performer, target_performer):
        """
        Calculate comprehensive similarity between two performers
        Considers multiple factors with weighted importance
        """
        similarity = 0
        weights = {
            'cup_to_bmi': 0.3,
            'o_counter': 0.2,
            'scene_count': 0.1,
            'band_size': 0.2,
            'cup_letter': 0.2,
            'volume': 0.3,  # Neues Gewicht für Brustvolumen
            'height': 0.1,  # Neues Gewicht für Körpergröße
            'weight': 0.1   # Neues Gewicht für Gewicht
        }
        
        # Cup-to-BMI similarity (normalized)
        if base_performer.get('bmi') and target_performer.get('bmi'):
            cup_to_bmi_base = base_performer.get('cup_to_bmi', 0)
            cup_to_bmi_target = target_performer.get('cup_to_bmi', 0)
            
            if cup_to_bmi_base and cup_to_bmi_target:
                bmi_similarity = 1 - min(abs(cup_to_bmi_base - cup_to_bmi_target) / max(cup_to_bmi_base, cup_to_bmi_target), 1)
                similarity += bmi_similarity * weights['cup_to_bmi']
        
        # O-Counter similarity
        base_o_counter = base_performer.get('o_counter', 0)
        target_o_counter = target_performer.get('o_counter', 0)
        if base_o_counter > 0 and target_o_counter > 0:
            o_counter_similarity = 1 - min(abs(base_o_counter - target_o_counter) / max(base_o_counter, target_o_counter), 1)
            similarity += o_counter_similarity * weights['o_counter']
        
        # Scene count similarity
        base_scene_count = base_performer.get('scene_count', 0)
        target_scene_count = target_performer.get('scene_count', 0)
        if base_scene_count > 0 and target_scene_count > 0:
            scene_count_similarity = 1 - min(abs(base_scene_count - target_scene_count) / max(base_scene_count, target_scene_count), 1)
            similarity += scene_count_similarity * weights['scene_count']
        
        # Band size similarity
        base_band = base_performer.get('band_size')
        target_band = target_performer.get('band_size')
        if base_band and target_band:
            try:
                band_similarity = 1 - min(abs(int(base_band) - int(target_band)) / max(int(base_band), int(target_band)), 1)
                similarity += band_similarity * weights['band_size']
            except (ValueError, ZeroDivisionError):
                pass
        
        # Cup letter similarity
        base_cup = base_performer.get('cup_letter')
        target_cup = target_performer.get('cup_letter')
        if base_cup and target_cup:
            cup_letters = 'ABCDEFGHIJK'
            try:
                base_cup_index = cup_letters.index(base_cup)
                target_cup_index = cup_letters.index(target_cup)
                cup_similarity = 1 - min(abs(base_cup_index - target_cup_index) / len(cup_letters), 1)
                similarity += cup_similarity * weights['cup_letter']
            except (ValueError, ZeroDivisionError):
                pass
        
        # Volumen-Ähnlichkeit (neu)
        base_volume = base_performer.get('volume_cc', 0)
        target_volume = target_performer.get('volume_cc', 0)
        if base_volume > 0 and target_volume > 0:
            volume_similarity = 1 - min(abs(base_volume - target_volume) / max(base_volume, target_volume), 1)
            similarity += volume_similarity * weights['volume']
        
        # Körpergröße-Ähnlichkeit (neu)
        base_height = base_performer.get('height_cm', 0)
        target_height = target_performer.get('height_cm', 0)
        if base_height > 0 and target_height > 0:
            height_similarity = 1 - min(abs(base_height - target_height) / 30, 1)  # 30cm als maximaler Unterschied
            similarity += height_similarity * weights['height']
        
        # Gewicht-Ähnlichkeit (neu)
        base_weight = base_performer.get('weight', 0)
        target_weight = target_performer.get('weight', 0)
        if base_weight > 0 and target_weight > 0:
            weight_similarity = 1 - min(abs(base_weight - target_weight) / 30, 1)  # 30kg als maximaler Unterschied
            similarity += weight_similarity * weights['weight']
        
        return similarity
    
    def _get_popular_tags(self, min_o_counter=1, top_n=20) -> List[str]:
        """
        Ermittelt die beliebtesten Tags basierend auf Szenen mit hohem O-Counter
        
        Args:
            min_o_counter: Minimaler O-Counter für die Berücksichtigung
            top_n: Anzahl der zurückzugebenden Top-Tags
            
        Returns:
            Liste der beliebtesten Tags
        """
        # Sammle Tags aus Szenen mit hohem O-Counter
        tag_counter = Counter()
        
        for scene in self.scenes_data:
            o_counter = scene.get('o_counter', 0)
            if o_counter >= min_o_counter:
                tags = scene.get('tags', [])
                for tag in tags:
                    tag_name = tag.get('name', '')
                    if tag_name:
                        # Gewichte Tags nach O-Counter
                        tag_counter[tag_name] += o_counter
        
        # Gib die häufigsten Tags zurück
        return [tag for tag, _ in tag_counter.most_common(top_n)]
    
    def _calculate_tag_similarity(self, tags1: List[str], tags2: List[str]) -> float:
        """
        Berechnet die Ähnlichkeit zwischen zwei Tag-Listen
        
        Args:
            tags1: Erste Tag-Liste
            tags2: Zweite Tag-Liste
            
        Returns:
            Ähnlichkeitswert zwischen 0 und 1
        """
        if not tags1 or not tags2:
            return 0.0
            
        # Jaccard-Ähnlichkeit: Größe der Schnittmenge / Größe der Vereinigungsmenge
        set1 = set(tags1)
        set2 = set(tags2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
            
        return intersection / union
    
    def _get_performer_tags(self, performer_name: str) -> List[str]:
        """
        Ermittelt alle Tags, die mit einem Performer verbunden sind
        
        Args:
            performer_name: Name des Performers
            
        Returns:
            Liste aller Tags des Performers
        """
        tags = []
        
        for scene in self.scenes_data:
            performers = scene.get('performers', [])
            performer_names = [p.get('name', '') for p in performers]
            
            if performer_name in performer_names:
                scene_tags = [t.get('name', '') for t in scene.get('tags', [])]
                tags.extend(scene_tags)
        
        # Entferne Duplikate
        return list(set(tags))
    
    def recommend_performers(self):
        """Generate performer recommendations based on top O-Counter performers"""
        # Erhöhe den Empfehlungszähler für Rotation
        self._recommendation_counter += 1
        
        # Prüfe, ob wir bereits Empfehlungen im Cache haben
        if self._performer_recommendation_cache:
            # Rotiere die Empfehlungen, um bei jedem Aufruf andere zu erhalten
            cached_recommendations = list(self._performer_recommendation_cache.values())
            rotation_index = self._recommendation_counter % len(cached_recommendations)
            rotated_recommendations = cached_recommendations[rotation_index:] + cached_recommendations[:rotation_index]
            
            # Gib die ersten 10 rotierten Empfehlungen zurück
            return rotated_recommendations[:10]
        
        if not self.performers_data:
            logger.warning("No performers data available for recommendations")
            return []
        
        try:
            # Get statistics
            stats = self.stats_module.generate_all_stats()
            
            # Get top O-Counter performers
            top_o_counter_performers = stats.get('top_o_counter_performers', [])
            
            # Get volume statistics for additional recommendations
            volume_stats = stats.get('volume_stats', {})
            top_volume_performers = volume_stats.get('top_volume_performers', [])
            
            # Get cup size statistics
            cup_stats = stats.get('cup_size_stats', {})
            cup_df = pd.DataFrame(cup_stats.get('cup_size_dataframe', []))
            
            # Kombiniere verschiedene Empfehlungsquellen
            recommendations = []
            
            # 1. Empfehlungen basierend auf Top O-Counter Performern
            for base_performer in top_o_counter_performers:
                # Find similar performers with o_counter = 0
                similar_performers = []
                
                for target_performer in self.performers_data:
                    # Skip the base performer itself
                    if target_performer.get('id') == base_performer.get('id'):
                        continue
                    
                    # Wir suchen nach Performern mit o_counter = 0 für Empfehlungen
                    if target_performer.get('o_counter', 0) != 0:
                        continue
                    
                    # Calculate similarity
                    similarity = self._calculate_similarity(base_performer, target_performer)
                    
                    if similarity > 0.5:  # Threshold for recommendation
                        similar_performers.append({
                            'id': target_performer.get('id'),
                            'name': target_performer.get('name', 'Unknown'),
                            'cup_size': f"{target_performer.get('band_size', 'N/A')}{target_performer.get('cup_letter', '')}",
                            'cup_to_bmi': target_performer.get('cup_to_bmi'),
                            'o_counter': target_performer.get('o_counter', 0),
                            'similarity': similarity,
                            'reason': f"Ähnlich zu {base_performer.get('name', 'Unknown')} (O-Counter: {base_performer.get('o_counter', 0)})"
                        })
                
                # Sort similar performers by similarity
                similar_performers.sort(key=lambda x: x['similarity'], reverse=True)
                
                if similar_performers:
                    recommendation_id = f"o_counter_{base_performer.get('id', '')}"
                    recommendation = {
                        'id': recommendation_id,
                        'performer': {
                            'name': base_performer.get('name', 'Unknown'),
                            'measurements': base_performer.get('measurements', 'N/A'),
                            'o_counter': base_performer.get('o_counter', 0),
                            'cup_to_bmi': base_performer.get('cup_to_bmi')
                        },
                        'similar_performers': similar_performers[:5],  # Top 5 similar performers
                        'recommendation_type': 'o_counter_similarity'
                    }
                    
                    # Speichere im Cache
                    self._performer_recommendation_cache[recommendation_id] = recommendation
                    recommendations.append(recommendation)
            
            # 2. Empfehlungen basierend auf Brustvolumen
            if top_volume_performers and not cup_df.empty:
                for volume_performer in top_volume_performers:
                    if volume_performer.get('o_counter', 0) > 0:
                        # Finde Performer mit ähnlichem Volumen aber O-Counter = 0
                        target_volume = volume_performer.get('volume_cc', 0)
                        
                        if target_volume > 0:
                            # Erstelle eine Liste von Performern mit ähnlichem Volumen
                            volume_similar_performers = []
                            
                            for performer in self.performers_data:
                                # Skip performers with o_counter > 0
                                if performer.get('o_counter', 0) > 0:
                                    continue
                                
                                performer_volume = performer.get('volume_cc', 0)
                                
                                if performer_volume > 0:
                                    # Berechne Volumen-Ähnlichkeit
                                    volume_diff = abs(performer_volume - target_volume)
                                    volume_similarity = max(0, 1 - (volume_diff / max(target_volume, performer_volume)))
                                    
                                    if volume_similarity > 0.7:  # Hoher Schwellenwert für Volumen-Ähnlichkeit
                                        volume_similar_performers.append({
                                            'id': performer.get('id'),
                                            'name': performer.get('name', 'Unknown'),
                                            'cup_size': performer.get('cup_size', 'N/A'),
                                            'volume_cc': performer_volume,
                                            'o_counter': 0,
                                            'similarity': volume_similarity,
                                            'reason': f"Ähnliches Brustvolumen wie {volume_performer.get('name', 'Unknown')} (O-Counter: {volume_performer.get('o_counter', 0)})"
                                        })
                            
                            # Sortiere nach Ähnlichkeit
                            volume_similar_performers.sort(key=lambda x: x['similarity'], reverse=True)
                            
                            if volume_similar_performers:
                                recommendation_id = f"volume_{volume_performer.get('id', '')}"
                                recommendation = {
                                    'id': recommendation_id,
                                    'performer': {
                                        'name': volume_performer.get('name', 'Unknown'),
                                        'measurements': volume_performer.get('measurements', 'N/A'),
                                        'o_counter': volume_performer.get('o_counter', 0),
                                        'volume_cc': volume_performer.get('volume_cc', 0),
                                        'cup_size': volume_performer.get('cup_size', 'N/A')
                                    },
                                    'similar_performers': volume_similar_performers[:5],
                                    'recommendation_type': 'volume_similarity'
                                }
                                
                                # Speichere im Cache
                                self._performer_recommendation_cache[recommendation_id] = recommendation
                                recommendations.append(recommendation)
            
            # 3. Empfehlungen basierend auf Cup-Größe
            cup_letter_stats = stats.get('cup_size_o_counter_correlation', {}).get('cup_letter_o_stats', [])
            
            if cup_letter_stats:
                # Sortiere nach durchschnittlichem O-Counter
                sorted_cup_stats = sorted(cup_letter_stats, key=lambda x: x.get('avg_o_count', 0), reverse=True)
                
                for cup_stat in sorted_cup_stats[:3]:  # Top 3 Cup-Größen
                    cup_letter = cup_stat.get('cup_letter')
                    avg_o_count = cup_stat.get('avg_o_count', 0)
                    
                    if cup_letter and avg_o_count > 0:
                        # Finde Performer mit dieser Cup-Größe und O-Counter = 0
                        cup_similar_performers = []
                        
                        for performer in self.performers_data:
                            if (performer.get('cup_letter') == cup_letter and 
                                performer.get('o_counter', 0) == 0):
                                
                                cup_similar_performers.append({
                                    'id': performer.get('id'),
                                    'name': performer.get('name', 'Unknown'),
                                    'cup_size': f"{performer.get('band_size', 'N/A')}{cup_letter}",
                                    'o_counter': 0,
                                    'similarity': 0.8,  # Feste Ähnlichkeit für Cup-Größen-Empfehlungen
                                    'reason': f"Cup-Größe {cup_letter} hat durchschnittlichen O-Counter von {avg_o_count:.2f}"
                                })
                        
                        # Mische die Performer für Vielfalt
                        random.shuffle(cup_similar_performers)
                        
                        if cup_similar_performers:
                            recommendation_id = f"cup_{cup_letter}"
                            recommendation = {
                                'id': recommendation_id,
                                'performer': {
                                    'name': f"Cup-Größe {cup_letter}",
                                    'measurements': f"Cup {cup_letter}",
                                    'o_counter': avg_o_count,
                                    'cup_letter': cup_letter
                                },
                                'similar_performers': cup_similar_performers[:5],
                                'recommendation_type': 'cup_size_popularity'
                            }
                            
                            # Speichere im Cache
                            self._performer_recommendation_cache[recommendation_id] = recommendation
                            recommendations.append(recommendation)
            
            # Mische die Empfehlungen für Vielfalt
            random.shuffle(recommendations)
            
            return recommendations[:10]  # Begrenze auf 10 Empfehlungen
        
        except Exception as e:
            logger.error(f"Error in performer recommendations: {e}", exc_info=True)
            return []
    
    def recommend_scenes(self):
        """Generate scene recommendations"""
        # Erhöhe den Empfehlungszähler für Rotation
        self._recommendation_counter += 1
        
        # Prüfe, ob wir bereits Empfehlungen im Cache haben
        if self._scene_recommendation_cache:
            # Rotiere die Empfehlungen, um bei jedem Aufruf andere zu erhalten
            cached_recommendations = self._scene_recommendation_cache.copy()
            
            # Rotiere jede Kategorie separat
            for category in cached_recommendations:
                scenes = cached_recommendations[category]
                if scenes:
                    rotation_index = self._recommendation_counter % len(scenes)
                    cached_recommendations[category] = scenes[rotation_index:] + scenes[:rotation_index]
            
            return cached_recommendations
        
        if not self.scenes_data:
            logger.warning("No scenes data available for recommendations")
            return {}
        
        try:
            # Erweiterte Szenenempfehlungslogik
            recommendations = {
                'favorite_performer_scenes': [],
                'non_favorite_performer_scenes': [],
                'recommended_performer_scenes': [],
                'similar_tag_scenes': []  # Neue Kategorie für Tag-basierte Empfehlungen
            }
            
            # Hole Statistiken
            stats = self.stats_module.generate_all_stats()
            
            # Hole beliebte Tags aus Szenen mit hohem O-Counter
            popular_tags = self._get_popular_tags(min_o_counter=3)
            
            # Hole Top-Performer nach O-Counter
            top_performers = stats.get('top_o_counter_performers', [])
            top_performer_names = [p.get('name', '') for p in top_performers]
            
            # Sammle Tags aus Szenen mit hohem O-Counter
            high_o_counter_tags = []
            for scene in self.scenes_data:
                if scene.get('o_counter', 0) >= 3:  # Szenen mit hohem O-Counter
                    scene_tags = [t.get('name', '') for t in scene.get('tags', [])]
                    high_o_counter_tags.extend(scene_tags)
            
            # Zähle Tag-Häufigkeiten
            tag_counter = Counter(high_o_counter_tags)
            most_common_tags = [tag for tag, _ in tag_counter.most_common(20)]
            
            # Verarbeite Szenen
            for scene in self.scenes_data:
                # Nur ungesehene Szenen empfehlen (O-Counter = 0)
                if scene.get('o_counter', 0) != 0:
                    continue
                    
                performers = scene.get('performers', [])
                tags = scene.get('tags', [])
                
                # Extrahiere Namen und Tag-Namen
                performer_names = [p.get('name', '') for p in performers]
                tag_names = [t.get('name', '') for t in tags]
                
                # Prüfe auf Lieblings-Performer
                has_favorite_performer = any(p.get('favorite', False) for p in performers)
                
                # Prüfe auf Top-Performer
                has_top_performer = any(name in top_performer_names for name in performer_names)
                
                # Berechne Tag-Ähnlichkeit zu beliebten Tags
                tag_similarity = self._calculate_tag_similarity(tag_names, most_common_tags)
                
                # Bereite Empfehlung vor
                recommendation = {
                    'id': scene.get('id'),
                    'title': scene.get('title', 'Unknown'),
                    'performers': performer_names,
                    'tags': tag_names,
                    'tag_similarity': tag_similarity,
                    'similarity': len(set(tag_names).intersection(popular_tags))  # Verbesserte Ähnlichkeitsmetrik
                }
                
                # Kategorisiere Empfehlungen
                if has_favorite_performer:
                    recommendations['favorite_performer_scenes'].append(recommendation)
                elif has_top_performer:
                    recommendations['recommended_performer_scenes'].append(recommendation)
                elif tag_similarity > 0.3:  # Schwellenwert für Tag-Ähnlichkeit
                    recommendations['similar_tag_scenes'].append(recommendation)
                else:
                    recommendations['non_favorite_performer_scenes'].append(recommendation)
            
            # Sortiere und begrenze Empfehlungen
            for category in recommendations:
                if category == 'similar_tag_scenes':
                    # Sortiere nach Tag-Ähnlichkeit
                    recommendations[category] = sorted(
                        recommendations[category], 
                        key=lambda x: x['tag_similarity'], 
                        reverse=True
                    )[:15]  # Mehr Tag-basierte Empfehlungen
                else:
                    # Sortiere nach Ähnlichkeit
                    recommendations[category] = sorted(
                        recommendations[category], 
                        key=lambda x: x['similarity'], 
                        reverse=True
                    )[:10]
            
            # Speichere im Cache
            self._scene_recommendation_cache = recommendations
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error in scene recommendations: {e}", exc_info=True)
            return {}
