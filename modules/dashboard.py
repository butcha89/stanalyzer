import dash
from dash import dcc, html, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import pandas as pd
import numpy as np
import random
from datetime import datetime
import os
import json
import logging
from modules.statistics import StatisticsModule
from modules.recommendations import RecommendationModule

# Setup logging
logger = logging.getLogger(__name__)

# Farbpalette für konsistentes Design
COLORS = {
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'background': '#f8f9fa',
    'text': '#212529',
    'cup_colors': {
        'A': '#ff9999', 'B': '#66b3ff', 'C': '#99ff99', 'D': '#ffcc99',
        'E': '#c2c2f0', 'F': '#ffb3e6', 'G': '#c6ecd9', 'H': '#ffffcc',
        'I': '#b3b3cc', 'J': '#ffccff'
    }
}

# CSS für besseres Styling
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css']

class DashboardModule:
    def __init__(self, stats_module=None, recommendation_module=None):
        """Initialize the dashboard module"""
        self.stats_module = stats_module or StatisticsModule()
        self.recommendation_module = recommendation_module or RecommendationModule(
            stats_module=self.stats_module
        )
        
        # Stelle sicher, dass das Assets-Verzeichnis existiert
        import os
        import pathlib
        
        # Erstelle das Assets-Verzeichnis, falls es nicht existiert
        assets_dir = pathlib.Path("assets")
        if not assets_dir.exists():
            os.makedirs(assets_dir, exist_ok=True)
            
            # Erstelle eine einfache CSS-Datei, falls keine existiert
            css_file = assets_dir / "dashboard.css"
            if not css_file.exists():
                with open(css_file, "w") as f:
                    f.write("""
/* Benutzerdefinierte Stile für das Dashboard */
body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
}

.card {
    transition: all 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}
""")
        
        self.app = dash.Dash(
            __name__, 
            suppress_callback_exceptions=True,
            external_stylesheets=external_stylesheets,
            meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
            assets_folder=str(assets_dir)
        )
        
        # Cache für Statistiken (um wiederholte Berechnungen zu vermeiden)
        self.stats_cache = None
        self.last_update = None
        self.cache_duration = 3600  # Sekunden (1 Stunde)
        self.cache_file = pathlib.Path("data/cache/dashboard_stats.json")
        
        # Lade Cache aus Datei, falls vorhanden
        self._load_cache_from_file()
        
        # Initialisiere das Layout
        self.setup_layout()
        
    def _load_cache_from_file(self):
        """Lädt den Cache aus einer Datei, falls vorhanden"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    import json
                    cache_data = json.load(f)
                    self.stats_cache = cache_data.get('stats')
                    last_update_str = cache_data.get('last_update')
                    if last_update_str:
                        self.last_update = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S')
                    print(f"Cache geladen aus {self.cache_file}")
            else:
                print(f"Keine Cache-Datei gefunden unter {self.cache_file}")
        except Exception as e:
            print(f"Fehler beim Laden des Caches: {e}")
            self.stats_cache = None
            self.last_update = None
    
    def _save_cache_to_file(self):
        """Speichert den Cache in einer Datei"""
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cache_file, 'w') as f:
                import json
                cache_data = {
                    'stats': self.stats_cache,
                    'last_update': self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else None
                }
                json.dump(cache_data, f)
                print(f"Cache gespeichert in {self.cache_file}")
        except Exception as e:
            print(f"Fehler beim Speichern des Caches: {e}")
    
    def get_stats(self, force_refresh=False):
        """Holt Statistiken mit Caching"""
        current_time = datetime.now()
        
        # Prüfe, ob Cache aktualisiert werden muss
        if (self.stats_cache is None or force_refresh or 
            self.last_update is None or 
            (current_time - self.last_update).total_seconds() > self.cache_duration):
            
            print("Generiere neue Statistiken...")
            try:
                # Stelle sicher, dass der StashClient korrekt konfiguriert ist
                if hasattr(self.stats_module, 'stash_client') and self.stats_module.stash_client:
                    print(f"Verwende Stash-URL: {self.stats_module.stash_client.url}")
                    print(f"API-Key konfiguriert: {'Ja' if self.stats_module.stash_client.api_key else 'Nein'}")
                
                self.stats_cache = self.stats_module.generate_all_stats()
                self.last_update = current_time
                
                # Speichere den aktualisierten Cache
                self._save_cache_to_file()
            except Exception as e:
                print(f"Fehler beim Generieren der Statistiken: {e}")
                import traceback
                traceback.print_exc()
                
                # Wenn keine Daten generiert werden konnten, versuche den Cache zu laden
                if self.stats_cache is None:
                    self._load_cache_from_file()
            
        return self.stats_cache
        
    def setup_layout(self):
        """Set up the dashboard layout"""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("Stash Analytics Dashboard", className="display-4 text-center mb-4"),
                html.P("Analyse von Performer-Daten, O-Counter Korrelationen und Brustgrößen-Statistiken", 
                       className="lead text-center mb-4"),
                html.Hr()
            ], className="container mt-4"),
            
            # Hauptinhalt
            html.Div([
                # Tabs für verschiedene Bereiche
                dcc.Tabs([
                    # Statistik-Tab
                    dcc.Tab(label="Statistiken", children=[
                        html.Div([
                            # Steuerelemente
                            html.Div([
                                html.Div([
                                    html.Button("Daten aktualisieren", id="refresh-button", 
                                               className="btn btn-primary mb-3 mr-2"),
                                    html.Button("Statistiken exportieren", id="export-button", 
                                               className="btn btn-success mb-3"),
                                    dcc.Download(id="download-stats"),
                                ], className="d-flex"),
                                html.Div(id="last-update-time", className="text-muted small mb-3")
                            ], className="mb-4"),
                            
                            # Übersichts-Karten
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.H5("Performer mit Daten", className="card-title"),
                                        html.H2(id="total-performers", className="display-4 text-primary")
                                    ], className="card-body")
                                ], className="card shadow-sm"),
                                
                                html.Div([
                                    html.Div([
                                        html.H5("Durchschnitt O-Counter", className="card-title"),
                                        html.H2(id="avg-o-counter", className="display-4 text-success")
                                    ], className="card-body")
                                ], className="card shadow-sm"),
                                
                                html.Div([
                                    html.Div([
                                        html.H5("Max O-Counter", className="card-title"),
                                        html.H2(id="max-o-counter", className="display-4 text-danger")
                                    ], className="card-body")
                                ], className="card shadow-sm"),
                                
                                html.Div([
                                    html.Div([
                                        html.H5("Häufigste Cup-Größe", className="card-title"),
                                        html.H2(id="most-common-cup", className="display-4 text-info")
                                    ], className="card-body")
                                ], className="card shadow-sm")
                            ], className="row row-cols-1 row-cols-md-4 mb-4 text-center"),
                            
                            # Cup-Größen Verteilung
                            html.Div([
                                html.Div([
                                    html.H3("Cup-Größen Verteilung", className="mb-3"),
                                    dcc.Graph(id='cup-size-distribution')
                                ], className="col-md-6"),
                                
                                html.Div([
                                    html.H3("O-Counter nach Cup-Größe", className="mb-3"),
                                    dcc.Graph(id='o-counter-by-cup')
                                ], className="col-md-6")
                            ], className="row mb-4"),
                            
                            # Verhältnisse und Korrelationen
                            html.Div([
                                html.Div([
                                    html.H3("Cup-to-BMI Verhältnis", className="mb-3"),
                                    dcc.Graph(id='ratio-stats')
                                ], className="col-md-6"),
                                
                                html.Div([
                                    html.H3("O-Counter zu Rating Korrelation", className="mb-3"),
                                    dcc.Graph(id='o-counter-rating-correlation')
                                ], className="col-md-6")
                            ], className="row mb-4"),
                            
                            # Heatmaps und Verteilungen
                            html.Div([
                                html.Div([
                                    html.H3("BMI zu Cup-Größe Heatmap", className="mb-3"),
                                    dcc.Graph(id='bmi-cup-heatmap')
                                ], className="col-md-6"),
                                
                                html.Div([
                                    html.H3("O-Counter Verteilung", className="mb-3"),
                                    dcc.Graph(id='o-counter-distribution')
                                ], className="col-md-6")
                            ], className="row mb-4"),
                            
                            # Volumen-Statistiken
                            html.Div([
                                html.Div([
                                    html.H3("Brustvolumen nach Kategorie", className="mb-3"),
                                    dcc.Graph(id='volume-category-stats')
                                ], className="col-md-6"),
                                
                                html.Div([
                                    html.H3("Volumen zu O-Counter Korrelation", className="mb-3"),
                                    dcc.Graph(id='volume-o-counter-correlation')
                                ], className="col-md-6")
                            ], className="row mb-4")
                        ], className="container-fluid py-4")
                    ]),
                    
                    # Empfehlungs-Tab
                    dcc.Tab(label="Performer-Empfehlungen", children=[
                        html.Div([
                            # Steuerelemente für Empfehlungen
                            html.Div([
                                html.H3("Performer-Empfehlungen", className="mb-3"),
                                html.P("Basierend auf Ähnlichkeiten in Körpermaßen, Cup-Größe und BMI", 
                                      className="text-muted mb-4"),
                                
                                html.Div([
                                    html.Button("Neue Empfehlungen generieren", 
                                               id="generate-recommendations-button",
                                               className="btn btn-primary mb-3 mr-2"),
                                    
                                    html.Div([
                                        html.Label("Empfehlungstyp:", className="mr-2"),
                                        dcc.Dropdown(
                                            id='recommendation-type',
                                            options=[
                                                {'label': 'Ähnliche Cup-to-BMI Ratio', 'value': 'bmi_ratio'},
                                                {'label': 'Ähnliches Brustvolumen', 'value': 'volume'},
                                                {'label': 'Ähnliche Körpermaße', 'value': 'measurements'},
                                                {'label': 'Zufällige Empfehlung', 'value': 'random'}
                                            ],
                                            value='bmi_ratio',
                                            className="ml-2"
                                        )
                                    ], className="d-inline-block ml-2")
                                ], className="d-flex align-items-center mb-4"),
                                
                                # Erweiterte Konfigurationsoptionen
                                html.Div([
                                    html.H5("Erweiterte Konfiguration", className="mb-3"),
                                    html.Div([
                                        html.Div([
                                            html.Label("Minimaler O-Counter für Referenz-Performer:"),
                                            dcc.Slider(
                                                id='min-o-counter-slider',
                                                min=1, max=20, step=1, value=5,
                                                marks={i: str(i) for i in range(0, 21, 5)},
                                                className="mb-3"
                                            )
                                        ], className="col-md-6"),
                                        html.Div([
                                            html.Label("Ähnlichkeitsschwellwert:"),
                                            dcc.Slider(
                                                id='similarity-threshold-slider',
                                                min=0.1, max=0.9, step=0.1, value=0.5,
                                                marks={i/10: str(i/10) for i in range(1, 10)},
                                                className="mb-3"
                                            )
                                        ], className="col-md-6"),
                                    ], className="row mb-3"),
                                    html.Div([
                                        html.Div([
                                            html.Label("Gewichtung Cup-Größe:"),
                                            dcc.Slider(
                                                id='cup-weight-slider',
                                                min=0.1, max=2.0, step=0.1, value=1.0,
                                                marks={i/10: str(i/10) for i in range(1, 21, 5)},
                                                className="mb-3"
                                            )
                                        ], className="col-md-6"),
                                        html.Div([
                                            html.Label("Gewichtung BMI:"),
                                            dcc.Slider(
                                                id='bmi-weight-slider',
                                                min=0.1, max=2.0, step=0.1, value=0.5,
                                                marks={i/10: str(i/10) for i in range(1, 21, 5)},
                                                className="mb-3"
                                            )
                                        ], className="col-md-6"),
                                    ], className="row mb-3"),
                                    html.Div(id="config-info", className="alert alert-info mt-2")
                                ], className="card p-3 mb-4"),
                                
                                # Container für Empfehlungskarten
                                html.Div(id='performer-recommendations', className="row")
                            ], className="container py-4")
                        ])
                    ]),
                    
                    # Ähnlichkeits-Tab
                    dcc.Tab(label="Ähnlichkeitsanalyse", children=[
                        html.Div([
                            html.H3("Performer-Ähnlichkeitsanalyse", className="mb-3"),
                            html.P("Finde Performer, die ähnliche Eigenschaften haben wie deine Favoriten", 
                                  className="text-muted mb-4"),
                            
                            # Suchfunktion und Filter
                            html.Div([
                                html.Div([
                                    html.Label("Suche nach Performer:", className="mr-2"),
                                    dcc.Input(
                                        id="performer-search",
                                        type="text",
                                        placeholder="Name eingeben...",
                                        className="form-control mb-3"
                                    ),
                                    html.Button(
                                        "Suchen", 
                                        id="search-button",
                                        className="btn btn-primary mb-3 ml-2"
                                    )
                                ], className="mb-3"),
                                
                                # Erweiterte Filteroptionen
                                html.Div([
                                    html.H5("Filteroptionen", className="mb-3"),
                                    html.Div([
                                        html.Div([
                                            html.Label("Cup-Größe:"),
                                            dcc.Dropdown(
                                                id='cup-size-filter',
                                                multi=True,
                                                placeholder="Cup-Größen auswählen...",
                                                className="mb-2"
                                            )
                                        ], className="col-md-4"),
                                        html.Div([
                                            html.Label("BMI-Bereich:"),
                                            dcc.RangeSlider(
                                                id='bmi-range-filter',
                                                min=15, max=40, step=1,
                                                marks={i: str(i) for i in range(15, 41, 5)},
                                                value=[18, 30],
                                                className="mb-2"
                                            )
                                        ], className="col-md-4"),
                                        html.Div([
                                            html.Label("O-Counter:"),
                                            dcc.RangeSlider(
                                                id='o-counter-range-filter',
                                                min=0, max=30, step=1,
                                                marks={i: str(i) for i in range(0, 31, 5)},
                                                value=[0, 30],
                                                className="mb-2"
                                            )
                                        ], className="col-md-4"),
                                    ], className="row mb-2"),
                                    html.Div([
                                        html.Button(
                                            "Filter anwenden", 
                                            id="apply-filters-button",
                                            className="btn btn-info mr-2"
                                        ),
                                        html.Button(
                                            "Filter zurücksetzen", 
                                            id="reset-filters-button",
                                            className="btn btn-outline-secondary"
                                        )
                                    ], className="text-right")
                                ], className="card p-3 mb-3")
                            ], className="mb-4"),
                            
                            # Ergebnisbereich
                            html.Div([
                                html.Div(id="search-results", className="mb-4"),
                                html.Div(id="similarity-results")
                            ])
                        ], className="container py-4")
                    ]),
                    
                    # Volumen-Analyse-Tab
                    dcc.Tab(label="Volumen-Analyse", children=[
                        html.Div([
                            html.H3("Brustvolumen-Analyse", className="mb-3"),
                            html.P("Detaillierte Analyse von Brustvolumen und dessen Korrelation mit O-Counter", 
                                  className="text-muted mb-4"),
                            
                            # Volumen-Verteilung
                            html.Div([
                                html.Div([
                                    html.H4("Volumen-Verteilung", className="mb-3"),
                                    dcc.Graph(id='volume-distribution')
                                ], className="col-md-6"),
                                
                                html.Div([
                                    html.H4("Top Performer nach Volumen", className="mb-3"),
                                    html.Div(id='top-volume-performers')
                                ], className="col-md-6")
                            ], className="row mb-4"),
                            
                            # Sister Size Analyse
                            html.Div([
                                html.H4("Sister Size Analyse", className="mb-3"),
                                html.P("Vergleich von Original-Größen mit Sister Sizes", className="text-muted mb-3"),
                                dcc.Graph(id='sister-size-comparison')
                            ], className="mb-4"),
                            
                            # 3D Visualisierung
                            html.Div([
                                html.H4("3D Visualisierung: Cup-Größe, BMI und O-Counter", className="mb-3"),
                                html.P("Interaktive 3D-Darstellung der Zusammenhänge", className="text-muted mb-3"),
                                dcc.Graph(id='3d-visualization', style={"height": "600px"}),
                                html.Div([
                                    html.Label("X-Achse:"),
                                    dcc.Dropdown(
                                        id='x-axis-selector',
                                        options=[
                                            {'label': 'Cup-Größe (numerisch)', 'value': 'cup_numeric'},
                                            {'label': 'BMI', 'value': 'bmi'},
                                            {'label': 'Volumen (cc)', 'value': 'volume_cc'},
                                            {'label': 'Körpergröße (cm)', 'value': 'height_cm'},
                                            {'label': 'Gewicht (kg)', 'value': 'weight'}
                                        ],
                                        value='cup_numeric',
                                        className="mb-2"
                                    ),
                                    html.Label("Y-Achse:"),
                                    dcc.Dropdown(
                                        id='y-axis-selector',
                                        options=[
                                            {'label': 'Cup-Größe (numerisch)', 'value': 'cup_numeric'},
                                            {'label': 'BMI', 'value': 'bmi'},
                                            {'label': 'Volumen (cc)', 'value': 'volume_cc'},
                                            {'label': 'Körpergröße (cm)', 'value': 'height_cm'},
                                            {'label': 'Gewicht (kg)', 'value': 'weight'}
                                        ],
                                        value='bmi',
                                        className="mb-2"
                                    ),
                                    html.Label("Z-Achse:"),
                                    dcc.Dropdown(
                                        id='z-axis-selector',
                                        options=[
                                            {'label': 'O-Counter', 'value': 'o_counter'},
                                            {'label': 'Rating', 'value': 'rating100'},
                                            {'label': 'Cup-Größe (numerisch)', 'value': 'cup_numeric'},
                                            {'label': 'BMI', 'value': 'bmi'},
                                            {'label': 'Volumen (cc)', 'value': 'volume_cc'}
                                        ],
                                        value='o_counter',
                                        className="mb-2"
                                    )
                                ], className="row")
                            ], className="mb-4")
                        ], className="container py-4")
                    ]),
                    
                    # Neuer Tab für Zeitreihenanalyse
                    dcc.Tab(label="Zeitreihenanalyse", children=[
                        html.Div([
                            html.H3("Zeitreihenanalyse", className="mb-3"),
                            html.P("Analyse von Trends und Veränderungen über die Zeit", 
                                  className="text-muted mb-4"),
                            
                            # Trendanalyse
                            html.Div([
                                html.Div([
                                    html.H4("O-Counter Trend nach Cup-Größe", className="mb-3"),
                                    dcc.Graph(id='o-counter-trend')
                                ], className="col-12 mb-4"),
                                
                                html.Div([
                                    html.H4("Verteilung nach Zeitraum", className="mb-3"),
                                    html.Div([
                                        html.Label("Zeitraum auswählen:"),
                                        dcc.RangeSlider(
                                            id='time-range-slider',
                                            min=2010, max=2025, step=1,
                                            marks={i: str(i) for i in range(2010, 2026, 2)},
                                            value=[2015, 2025],
                                            className="mb-3"
                                        ),
                                        dcc.Graph(id='time-distribution')
                                    ])
                                ], className="col-12")
                            ], className="row")
                        ], className="container py-4")
                    ])
                ], className="mb-4"),
                
                # Footer mit Aktualisierungsinfo
                html.Div([
                    html.Hr(),
                    html.P([
                        "Daten werden automatisch alle 60 Minuten aktualisiert. ",
                        html.Span(id="update-info", className="text-muted")
                    ], className="text-center text-muted small")
                ], className="container mb-4"),
                
                # Verstecktes Div für Daten-Speicherung
                html.Div(id='stats-store', style={'display': 'none'}),
                
                # Intervall für automatische Aktualisierung
                dcc.Interval(
                    id='interval-component',
                    interval=60*60*1000,  # refresh every hour
                    n_intervals=0
                )
            ])
        ], className="bg-light min-vh-100")
        
        # Callbacks einrichten
        self.setup_callbacks()
        
    def setup_callbacks(self):
        """Set up the dashboard callbacks"""
        # Callback für Datenaktualisierung
        @self.app.callback(
            [Output('stats-store', 'children'),
             Output('last-update-time', 'children')],
            [Input('refresh-button', 'n_clicks'),
             Input('interval-component', 'n_intervals')]
        )
        def update_stats_data(n_clicks, n_intervals):
            # Hole aktuelle Statistiken
            stats = self.get_stats(force_refresh=n_clicks is not None)
            
            # Formatiere Zeitstempel
            update_time = f"Zuletzt aktualisiert: {self.last_update.strftime('%d.%m.%Y %H:%M:%S')}"
            
            # Konvertiere zu JSON für Speicherung
            return json.dumps(stats), update_time
        
        # Callback für Übersichtskarten
        @self.app.callback(
            [Output('total-performers', 'children'),
             Output('avg-o-counter', 'children'),
             Output('max-o-counter', 'children'),
             Output('most-common-cup', 'children')],
            [Input('stats-store', 'children')]
        )
        def update_overview_cards(stats_json):
            if not stats_json:
                return "0", "0", "0", "N/A"
                
            stats = json.loads(stats_json)
            
            # Extrahiere Daten für Karten
            cup_stats = stats.get('cup_size_stats', {})
            o_counter_stats = stats.get('o_counter_stats', {})
            
            # Gesamtzahl der Performer
            total_performers = len(cup_stats.get('cup_size_dataframe', []))
            
            # O-Counter Statistiken
            avg_o_counter = o_counter_stats.get('average_o_counter', 0)
            max_o_counter = o_counter_stats.get('max_o_counter', 0)
            
            # Häufigste Cup-Größe
            cup_counts = cup_stats.get('cup_size_counts', {})
            most_common_cup = "N/A"
            if cup_counts:
                most_common_cup = max(cup_counts.items(), key=lambda x: x[1])[0]
            
            return str(total_performers), f"{avg_o_counter:.2f}", str(max_o_counter), most_common_cup
        
        # Callback für Cup-Größen Verteilung
        @self.app.callback(
            Output('cup-size-distribution', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_cup_size_distribution(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            cup_stats = stats.get('cup_size_stats', {})
            cup_counts = cup_stats.get('cup_size_counts', {})
            
            if not cup_counts:
                return go.Figure()
            
            # Sortiere nach Cup-Größe
            sorted_cups = sorted(cup_counts.items(), 
                                key=lambda x: (int(x[0][:-1]), x[0][-1]))
            
            cups, counts = zip(*sorted_cups)
            
            # Erstelle Farbzuordnung
            colors = [COLORS['cup_colors'].get(cup[-1], COLORS['primary']) for cup in cups]
            
            fig = px.bar(x=cups, y=counts, 
                        title="Cup-Größen Verteilung",
                        labels={'x': 'Cup-Größe', 'y': 'Anzahl'})
            
            fig.update_traces(marker_color=colors)
            fig.update_layout(
                plot_bgcolor=COLORS['light'],
                paper_bgcolor=COLORS['light'],
                font={'color': COLORS['text']},
                margin=dict(l=40, r=40, t=50, b=40),
                hovermode='closest'
            )
            
            return fig
        
        # Callback für O-Counter nach Cup-Größe
        @self.app.callback(
            Output('o-counter-by-cup', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_o_counter_by_cup(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            cup_size_o_counter = stats.get('cup_size_o_counter_correlation', {})
            cup_letter_stats = cup_size_o_counter.get('cup_letter_o_stats', [])
            
            if not cup_letter_stats:
                return go.Figure()
            
            df = pd.DataFrame(cup_letter_stats)
            
            # Sortiere nach Cup-Buchstabe
            cup_order = list("ABCDEFGHIJ")
            df['cup_order'] = df['cup_letter'].apply(lambda x: cup_order.index(x) if x in cup_order else 999)
            df = df.sort_values('cup_order')
            
            # Erstelle Farbzuordnung
            colors = [COLORS['cup_colors'].get(cup, COLORS['primary']) for cup in df['cup_letter']]
            
            fig = px.bar(df, x='cup_letter', y='avg_o_count',
                        title="Durchschnittlicher O-Counter nach Cup-Größe",
                        labels={'cup_letter': 'Cup-Buchstabe', 
                               'avg_o_count': 'Durchschnittlicher O-Counter'})
            
            # Füge Performer-Anzahl als Text hinzu
            fig.update_traces(
                text=df['performer_count'].apply(lambda x: f"n={x}"),
                textposition='outside',
                marker_color=colors
            )
            
            fig.update_layout(
                plot_bgcolor=COLORS['light'],
                paper_bgcolor=COLORS['light'],
                font={'color': COLORS['text']},
                margin=dict(l=40, r=40, t=50, b=40),
                hovermode='closest'
            )
            
            return fig
        
        # Callback für Ratio-Statistiken
        @self.app.callback(
            Output('ratio-stats', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_ratio_stats(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            ratio_stats = stats.get('ratio_stats', {})
            ratio_data = ratio_stats.get('ratio_stats', [])
            
            if not ratio_data:
                return go.Figure()
            
            df = pd.DataFrame(ratio_data)
            
            # Sortiere nach Cup-Buchstabe
            cup_order = list("ABCDEFGHIJ")
            df['cup_order'] = df['cup_letter'].apply(lambda x: cup_order.index(x) if x in cup_order else 999)
            df = df.sort_values('cup_order')
            
            # Erstelle Figure mit mehreren Traces
            fig = go.Figure()
            
            if 'avg_cup_to_bmi' in df.columns:
                fig.add_trace(go.Bar(
                    x=df['cup_letter'],
                    y=df['avg_cup_to_bmi'],
                    name='Cup zu BMI',
                    marker_color=COLORS['primary']
                ))
            
            if 'avg_cup_to_height' in df.columns:
                fig.add_trace(go.Bar(
                    x=df['cup_letter'],
                    y=df['avg_cup_to_height'],
                    name='Cup zu Größe',
                    marker_color=COLORS['success']
                ))
            
            if 'avg_cup_to_weight' in df.columns:
                fig.add_trace(go.Bar(
                    x=df['cup_letter'],
                    y=df['avg_cup_to_weight'],
                    name='Cup zu Gewicht',
                    marker_color=COLORS['info']
                ))
            
            fig.update_layout(
                title="Durchschnittliche Verhältnisse nach Cup-Größe",
                xaxis_title="Cup-Buchstabe",
                yaxis_title="Verhältniswert",
                barmode='group',
                plot_bgcolor=COLORS['light'],
                paper_bgcolor=COLORS['light'],
                font={'color': COLORS['text']},
                margin=dict(l=40, r=40, t=50, b=40),
                hovermode='closest',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
        
        # Callback für O-Counter zu Rating Korrelation
        @self.app.callback(
            Output('o-counter-rating-correlation', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_o_counter_rating_correlation(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            corr_stats = stats.get('rating_o_counter_correlation', {})
            rating_data = corr_stats.get('rating_o_counter_data', [])
            
            if not rating_data:
                return go.Figure()
            
            df = pd.DataFrame(rating_data)
            
            # Erstelle Scatter-Plot
            fig = px.scatter(
                df, x='rating100', y='o_counter',
                color='favorite',
                title=f"O-Counter zu Rating Korrelation (r = {corr_stats.get('correlation', 0):.3f})",
                labels={'rating100': 'Rating (0-100)', 'o_counter': 'O-Counter', 'favorite': 'Favorit'},
                hover_name='name',
                color_discrete_map={True: COLORS['danger'], False: COLORS['primary']}
            )
            
            # Füge Trendlinie hinzu
            fig.update_traces(marker=dict(size=10, opacity=0.7), selector=dict(mode='markers'))
            
            # Füge Regressionslinie hinzu, wenn genug Daten vorhanden sind
            if len(df) > 2:
                fig.update_layout(
                    shapes=[{
                        'type': 'line',
                        'x0': df['rating100'].min(),
                        'y0': df['rating100'].min() * corr_stats.get('correlation', 0),
                        'x1': df['rating100'].max(),
                        'y1': df['rating100'].max() * corr_stats.get('correlation', 0),
                        'line': {
                            'color': COLORS['secondary'],
                            'width': 2,
                            'dash': 'dash'
                        }
                    }]
                )
            
            fig.update_layout(
                plot_bgcolor=COLORS['light'],
                paper_bgcolor=COLORS['light'],
                font={'color': COLORS['text']},
                margin=dict(l=40, r=40, t=50, b=40),
                hovermode='closest'
            )
            
            return fig
        
        # Callback für BMI zu Cup-Größe Heatmap
        @self.app.callback(
            Output('bmi-cup-heatmap', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_bmi_cup_heatmap(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            cup_stats = stats.get('cup_size_stats', {})
            cup_df = cup_stats.get('cup_size_dataframe', [])
            
            if not cup_df:
                return go.Figure()
            
            df = pd.DataFrame(cup_df)
            
            # Filtere Daten für Heatmap
            if 'bmi' in df.columns and 'cup_letter' in df.columns:
                # Entferne Zeilen mit fehlenden Werten
                df = df.dropna(subset=['bmi', 'cup_letter'])
                
                if df.empty:
                    return go.Figure()
                
                # Erstelle BMI-Kategorien
                bmi_bins = [0, 18.5, 25, 30, 35, 100]
                bmi_labels = ['Untergewicht', 'Normalgewicht', 'Übergewicht', 'Adipositas I', 'Adipositas II+']
                df['bmi_category'] = pd.cut(df['bmi'], bins=bmi_bins, labels=bmi_labels)
                
                # Zähle Vorkommen für jede Kombination
                heatmap_data = pd.crosstab(df['bmi_category'], df['cup_letter'])
                
                # Sortiere Cup-Buchstaben
                cup_order = list("ABCDEFGHIJ")
                available_cups = [c for c in cup_order if c in heatmap_data.columns]
                heatmap_data = heatmap_data[available_cups]
                
                # Erstelle Heatmap
                fig = px.imshow(
                    heatmap_data,
                    labels=dict(x="Cup-Buchstabe", y="BMI-Kategorie", color="Anzahl"),
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    color_continuous_scale='Viridis',
                    title="BMI zu Cup-Größe Verteilung"
                )
                
                fig.update_layout(
                    plot_bgcolor=COLORS['light'],
                    paper_bgcolor=COLORS['light'],
                    font={'color': COLORS['text']},
                    margin=dict(l=40, r=40, t=50, b=40)
                )
                
                # Füge Textwerte hinzu
                for i in range(len(heatmap_data.index)):
                    for j in range(len(heatmap_data.columns)):
                        fig.add_annotation(
                            x=j, y=i,
                            text=str(heatmap_data.iloc[i, j]),
                            showarrow=False,
                            font=dict(color="white" if heatmap_data.iloc[i, j] > heatmap_data.values.max()/2 else "black")
                        )
                
                return fig
            
            return go.Figure()
        
        # Callback für O-Counter Verteilung
        @self.app.callback(
            Output('o-counter-distribution', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_o_counter_distribution(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            o_counter_stats = stats.get('o_counter_stats', {})
            performer_o_counts = o_counter_stats.get('performer_o_counts', {})
            
            if not performer_o_counts:
                return go.Figure()
            
            # Extrahiere O-Counter Werte
            o_values = [data.get('total_o_count', 0) for data in performer_o_counts.values()]
            
            # Filtere Nullwerte heraus
            o_values = [v for v in o_values if v > 0]
            
            if not o_values:
                return go.Figure()
            
            # Erstelle Histogramm mit Gauß'scher Verteilungskurve
            fig = ff.create_distplot(
                [o_values], 
                ['O-Counter'], 
                bin_size=(max(o_values) - min(o_values)) / 20,
                show_rug=False,
                colors=[COLORS['primary']]
            )
            
            fig.update_layout(
                title="O-Counter Verteilung (Gauß'sche Kurve)",
                xaxis_title="O-Counter Wert",
                yaxis_title="Dichte",
                plot_bgcolor=COLORS['light'],
                paper_bgcolor=COLORS['light'],
                font={'color': COLORS['text']},
                margin=dict(l=40, r=40, t=50, b=40),
                hovermode='closest'
            )
            
            # Füge Mittelwert und Median als vertikale Linien hinzu
            mean_o = np.mean(o_values)
            median_o = np.median(o_values)
            
            fig.add_shape(
                type="line",
                x0=mean_o, y0=0, x1=mean_o, y1=fig.data[0].y.max(),
                line=dict(color=COLORS['danger'], width=2, dash="dash"),
                name="Mittelwert"
            )
            
            fig.add_shape(
                type="line",
                x0=median_o, y0=0, x1=median_o, y1=fig.data[0].y.max(),
                line=dict(color=COLORS['success'], width=2, dash="dot"),
                name="Median"
            )
            
            fig.add_annotation(
                x=mean_o,
                y=fig.data[0].y.max(),
                text=f"Mittelwert: {mean_o:.2f}",
                showarrow=True,
                arrowhead=1,
                ax=50,
                ay=-30
            )
            
            fig.add_annotation(
                x=median_o,
                y=fig.data[0].y.max() * 0.8,
                text=f"Median: {median_o:.2f}",
                showarrow=True,
                arrowhead=1,
                ax=-50,
                ay=-30
            )
            
            return fig
        
        # Callback für Volumen-Kategorie Statistiken
        @self.app.callback(
            Output('volume-category-stats', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_volume_category_stats(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            volume_stats = stats.get('volume_stats', {})
            category_stats = volume_stats.get('volume_category_stats', [])
            
            if not category_stats:
                return go.Figure()
            
            df = pd.DataFrame(category_stats)
            
            # Definiere Reihenfolge der Kategorien
            category_order = [
                'Very Small', 'Small', 'Medium-Small', 'Medium', 
                'Medium-Large', 'Large', 'Very Large', 'Extremely Large'
            ]
            
            # Sortiere nach definierter Reihenfolge
            df['order'] = df['volume_category'].apply(
                lambda x: category_order.index(x) if x in category_order else 999
            )
            df = df.sort_values('order')
            
            # Erstelle Balkendiagramm
            fig = go.Figure()
            
            # Füge Balken für durchschnittlichen O-Counter hinzu
            fig.add_trace(go.Bar(
                x=df['volume_category'],
                y=df['avg_o_counter'],
                name='Durchschnittlicher O-Counter',
                marker_color=COLORS['primary'],
                text=df['performer_count'].apply(lambda x: f"n={x}"),
                textposition='outside'
            ))
            
            # Füge Linie für Performer-Anzahl hinzu
            fig.add_trace(go.Scatter(
                x=df['volume_category'],
                y=df['performer_count'],
                name='Anzahl Performer',
                mode='lines+markers',
                marker=dict(color=COLORS['danger']),
                yaxis='y2'
            ))
            
            # Layout mit zwei Y-Achsen
            fig.update_layout(
                title="Brustvolumen-Kategorien und O-Counter",
                xaxis_title="Volumen-Kategorie",
                yaxis=dict(
                    title="Durchschnittlicher O-Counter",
                    side="left"
                ),
                yaxis2=dict(
                    title="Anzahl Performer",
                    side="right",
                    overlaying="y",
                    showgrid=False
                ),
                plot_bgcolor=COLORS['light'],
                paper_bgcolor=COLORS['light'],
                font={'color': COLORS['text']},
                margin=dict(l=40, r=40, t=50, b=40),
                hovermode='closest',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
        
        # Callback für Volumen zu O-Counter Korrelation
        @self.app.callback(
            Output('volume-o-counter-correlation', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_volume_o_counter_correlation(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            volume_stats = stats.get('volume_stats', {})
            volume_df = volume_stats.get('volume_dataframe', [])
            correlation = volume_stats.get('volume_o_counter_correlation', 0)
            
            if not volume_df:
                return go.Figure()
            
            df = pd.DataFrame(volume_df)
            
            # Filtere Daten für Scatter-Plot
            if 'volume_cc' in df.columns and 'o_counter' in df.columns:
                # Entferne Zeilen mit fehlenden Werten oder Nullwerten
                df = df[(df['volume_cc'] > 0) & (df['o_counter'] > 0)]
                
                if df.empty:
                    return go.Figure()
                
                # Erstelle Scatter-Plot
                fig = px.scatter(
                    df, x='volume_cc', y='o_counter',
                    color='volume_category' if 'volume_category' in df.columns else None,
                    title=f"Brustvolumen zu O-Counter Korrelation (r = {correlation:.3f})",
                    labels={
                        'volume_cc': 'Brustvolumen (cc)', 
                        'o_counter': 'O-Counter', 
                        'volume_category': 'Volumen-Kategorie'
                    },
                    hover_name='name'
                )
                
                # Füge Trendlinie hinzu
                fig.update_traces(marker=dict(size=10, opacity=0.7), selector=dict(mode='markers'))
                
                # Füge Regressionslinie hinzu, wenn genug Daten vorhanden sind
                if len(df) > 2:
                    z = np.polyfit(df['volume_cc'], df['o_counter'], 1)
                    p = np.poly1d(z)
                    
                    fig.add_trace(go.Scatter(
                        x=[df['volume_cc'].min(), df['volume_cc'].max()],
                        y=p([df['volume_cc'].min(), df['volume_cc'].max()]),
                        mode='lines',
                        name='Trendlinie',
                        line=dict(color=COLORS['secondary'], width=2, dash='dash')
                    ))
                
                fig.update_layout(
                    plot_bgcolor=COLORS['light'],
                    paper_bgcolor=COLORS['light'],
                    font={'color': COLORS['text']},
                    margin=dict(l=40, r=40, t=50, b=40),
                    hovermode='closest'
                )
                
                return fig
            
            return go.Figure()
        
        # Callback für Performer-Empfehlungen
        @self.app.callback(
            Output('performer-recommendations', 'children'),
            [Input('generate-recommendations-button', 'n_clicks'),
             Input('recommendation-type', 'value'),
             Input('stats-store', 'children')],
            [State('min-o-counter-slider', 'value'),
             State('similarity-threshold-slider', 'value'),
             State('cup-weight-slider', 'value'),
             State('bmi-weight-slider', 'value')]
        )
        def update_performer_recommendations(n_clicks, rec_type, stats_json, min_o_counter, similarity_threshold, cup_weight, bmi_weight):
            if not stats_json:
                return html.Div("Keine Daten verfügbar")
                
            stats = json.loads(stats_json)
            
            # Hole Empfehlungen vom Recommendation-Modul
            recommendations = self.recommendation_module.recommend_performers()
            
            if not recommendations:
                return html.Div("Keine Empfehlungen verfügbar")
            
            # Hole zusätzliche Daten für spezifische Empfehlungstypen
            volume_stats = stats.get('volume_stats', {})
            top_volume_performers = volume_stats.get('top_volume_performers', [])
            
            cup_stats = stats.get('cup_size_stats', {})
            cup_df = pd.DataFrame(cup_stats.get('cup_size_dataframe', []))
            
            # Filtere und bereite Empfehlungen basierend auf dem Typ vor
            recommendation_cards = []
            
            if rec_type == 'bmi_ratio':
                # Empfehlungen basierend auf Cup-to-BMI Ratio
                for rec in recommendations[:6]:  # Begrenze auf 6 Empfehlungen
                    performer = rec['performer']
                    similar_performers = rec['similar_performers']
                    
                    # Filtere ähnliche Performer mit o_count = 0 und Ähnlichkeitsschwellwert
                    zero_o_similar = [sp for sp in similar_performers 
                                     if sp.get('o_count', 0) == 0 and 
                                     sp.get('similarity', 0) >= similarity_threshold]
                    
                    if not zero_o_similar:
                        continue
                    
                    # Wähle einen zufälligen Performer mit o_count = 0
                    recommended_performer = random.choice(zero_o_similar)
                    
                    card = html.Div([
                        html.Div([
                            html.H5(f"Empfehlung: {recommended_performer.get('name', 'Unbekannt')}", 
                                   className="card-title"),
                            html.H6(f"Cup-Größe: {recommended_performer.get('cup_size', 'N/A')}", 
                                   className="card-subtitle mb-2 text-muted"),
                            html.P([
                                "Hat die gleiche Cup-to-BMI Ratio wie ",
                                html.Strong(f"{performer.get('name', 'Unbekannt')}"),
                                f" (O-Counter: {performer.get('o_count', 0)})"
                            ], className="card-text"),
                            html.P(f"Ähnlichkeit: {recommended_performer.get('similarity', 0):.2f}", 
                                  className="card-text small text-muted")
                        ], className="card-body")
                    ], className="card shadow-sm col-md-4 mb-4")
                    
                    recommendation_cards.append(card)
                
            elif rec_type == 'volume':
                # Empfehlungen basierend auf Brustvolumen
                if top_volume_performers and cup_df.empty is False:
                    # Finde Performer mit hohem O-Counter basierend auf Konfiguration
                    high_o_performers = cup_df[cup_df['o_counter'] >= min_o_counter].to_dict('records')
                    
                    if high_o_performers:
                        for _ in range(min(6, len(high_o_performers))):
                            # Wähle einen zufälligen Performer mit hohem O-Counter
                            high_o_performer = random.choice(high_o_performers)
                            
                            # Finde Performer mit ähnlichem Volumen aber O-Counter = 0
                            if 'volume_cc' in cup_df.columns:
                                target_volume = high_o_performer.get('volume_cc', 0)
                                
                                # Filtere potenzielle Empfehlungen
                                potential_recs = cup_df[
                                    (cup_df['o_counter'] == 0) & 
                                    (cup_df['volume_cc'] > 0)
                                ]
                                
                                if not potential_recs.empty:
                                    # Berechne Volumendifferenz
                                    potential_recs['volume_diff'] = abs(potential_recs['volume_cc'] - target_volume)
                                    
                                    # Wähle Performer mit ähnlichstem Volumen
                                    similar_volume_performer = potential_recs.nsmallest(1, 'volume_diff').iloc[0]
                                    
                                    card = html.Div([
                                        html.Div([
                                            html.H5(f"Empfehlung: {similar_volume_performer.get('name', 'Unbekannt')}", 
                                                   className="card-title"),
                                            html.H6(f"Cup-Größe: {similar_volume_performer.get('cup_size', 'N/A')}", 
                                                   className="card-subtitle mb-2 text-muted"),
                                            html.P([
                                                "Hat ähnliches Brustvolumen wie ",
                                                html.Strong(f"{high_o_performer.get('name', 'Unbekannt')}"),
                                                f" (O-Counter: {high_o_performer.get('o_counter', 0)})"
                                            ], className="card-text"),
                                            html.P([
                                                f"Volumen: {similar_volume_performer.get('volume_cc', 0):.0f}cc vs. ",
                                                f"{high_o_performer.get('volume_cc', 0):.0f}cc"
                                            ], className="card-text small text-muted")
                                        ], className="card-body")
                                    ], className="card shadow-sm col-md-4 mb-4")
                                    
                                    recommendation_cards.append(card)
            
            elif rec_type == 'measurements':
                # Empfehlungen basierend auf Körpermaßen
                preference_profile = stats.get('preference_profile', {})
                clusters = preference_profile.get('cluster_analysis', {}).get('clusters', {})
                
                if clusters:
                    for cluster_id, cluster_data in clusters.items():
                        performers = cluster_data.get('performers', [])
                        
                        if len(performers) >= 2:
                            # Finde Performer mit O-Counter > 0 und O-Counter = 0 im gleichen Cluster
                            o_counter_data = []
                            for name in performers:
                                performer_data = next((p for p in cup_df.to_dict('records') 
                                                     if p.get('name') == name), None)
                                if performer_data:
                                    o_counter_data.append(performer_data)
                            
                            high_o_performers = [p for p in o_counter_data if p.get('o_counter', 0) >= min_o_counter]
                            zero_o_performers = [p for p in o_counter_data if p.get('o_counter', 0) == 0]
                            
                            if high_o_performers and zero_o_performers:
                                high_o_performer = random.choice(high_o_performers)
                                zero_o_performer = random.choice(zero_o_performers)
                                
                                card = html.Div([
                                    html.Div([
                                        html.H5(f"Empfehlung: {zero_o_performer.get('name', 'Unbekannt')}", 
                                               className="card-title"),
                                        html.H6(f"Cup-Größe: {zero_o_performer.get('cup_size', 'N/A')}", 
                                               className="card-subtitle mb-2 text-muted"),
                                        html.P([
                                            "Hat ähnliche Körpermaße wie ",
                                            html.Strong(f"{high_o_performer.get('name', 'Unbekannt')}"),
                                            f" (O-Counter: {high_o_performer.get('o_counter', 0)})"
                                        ], className="card-text"),
                                        html.P([
                                            "Beide im gleichen Körpertyp-Cluster"
                                        ], className="card-text small text-muted")
                                    ], className="card-body")
                                ], className="card shadow-sm col-md-4 mb-4")
                                
                                recommendation_cards.append(card)
            
            elif rec_type == 'random':
                # Zufällige Empfehlungen
                # Finde Performer mit O-Counter = 0
                zero_o_performers = cup_df[cup_df['o_counter'] == 0].to_dict('records')
                
                # Finde Performer mit hohem O-Counter basierend auf Konfiguration
                high_o_performers = cup_df[cup_df['o_counter'] >= min_o_counter].to_dict('records')
                
                if zero_o_performers and high_o_performers:
                    for _ in range(min(6, len(zero_o_performers), len(high_o_performers))):
                        zero_o_performer = random.choice(zero_o_performers)
                        high_o_performer = random.choice(high_o_performers)
                        
                        card = html.Div([
                            html.Div([
                                html.H5(f"Zufällige Empfehlung: {zero_o_performer.get('name', 'Unbekannt')}", 
                                       className="card-title"),
                                html.H6(f"Cup-Größe: {zero_o_performer.get('cup_size', 'N/A')}", 
                                       className="card-subtitle mb-2 text-muted"),
                                html.P([
                                    "Könnte dir gefallen, wenn du ",
                                    html.Strong(f"{high_o_performer.get('name', 'Unbekannt')}"),
                                    f" magst (O-Counter: {high_o_performer.get('o_counter', 0)})"
                                ], className="card-text"),
                                html.P([
                                    f"BMI: {zero_o_performer.get('bmi', 'N/A')}, ",
                                    f"Messungen: {zero_o_performer.get('measurements', 'N/A')}"
                                ], className="card-text small text-muted")
                            ], className="card-body")
                        ], className="card shadow-sm col-md-4 mb-4")
                        
                        recommendation_cards.append(card)
            
            # Wenn keine Empfehlungen generiert wurden
            if not recommendation_cards:
                return html.Div("Keine passenden Empfehlungen gefunden", className="alert alert-info")
            
            return html.Div(recommendation_cards, className="row")
        
        # Callback für Performer-Suche
        @self.app.callback(
            Output('search-results', 'children'),
            [Input('search-button', 'n_clicks')],
            [State('performer-search', 'value'),
             State('stats-store', 'children')]
        )
        def search_performers(n_clicks, search_term, stats_json):
            if not n_clicks or not search_term or not stats_json:
                return html.Div()
                
            stats = json.loads(stats_json)
            cup_stats = stats.get('cup_size_stats', {})
            cup_df_list = cup_stats.get('cup_size_dataframe', [])
            
            if not cup_df_list:
                return html.Div("Keine Performer-Daten verfügbar", className="alert alert-warning")
            
            # Suche nach Performern
            cup_df = pd.DataFrame(cup_df_list)
            
            # Filtere nach Suchbegriff (case-insensitive)
            search_results = cup_df[cup_df['name'].str.lower().str.contains(search_term.lower())]
            
            if search_results.empty:
                return html.Div(f"Keine Performer mit '{search_term}' gefunden", className="alert alert-info")
            
            # Erstelle Ergebnisliste
            result_items = []
            
            for _, performer in search_results.iterrows():
                result_items.append(html.Div([
                    html.Div([
                        html.H5(performer['name'], className="mb-1"),
                        html.Div([
                            html.Span(f"Cup-Größe: {performer.get('cup_size', 'N/A')}", 
                                     className="badge badge-primary mr-2"),
                            html.Span(f"O-Counter: {performer.get('o_counter', 0)}", 
                                     className="badge badge-success mr-2"),
                            html.Span(f"BMI: {performer.get('bmi', 'N/A')}", 
                                     className="badge badge-info mr-2")
                        ]),
                        html.Button("Ähnliche Performer anzeigen", 
                                   id={'type': 'show-similar', 'index': performer['id']},
                                   className="btn btn-sm btn-outline-primary mt-2")
                    ], className="card-body")
                ], className="card mb-2"))
            
            return html.Div([
                html.H4(f"Suchergebnisse für '{search_term}'"),
                html.Div(result_items)
            ])
        
        # Callback für Volumen-Verteilung
        @self.app.callback(
            Output('volume-distribution', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_volume_distribution(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            volume_stats = stats.get('volume_stats', {})
            volume_df = volume_stats.get('volume_dataframe', [])
            
            if not volume_df:
                return go.Figure()
            
            df = pd.DataFrame(volume_df)
            
            # Filtere Daten für Histogramm
            if 'volume_cc' in df.columns:
                # Entferne Zeilen mit fehlenden Werten oder Nullwerten
                df = df[df['volume_cc'] > 0]
                
                if df.empty:
                    return go.Figure()
                
                # Erstelle Histogramm mit Gauß'scher Verteilungskurve
                fig = ff.create_distplot(
                    [df['volume_cc'].tolist()], 
                    ['Brustvolumen'], 
                    bin_size=(df['volume_cc'].max() - df['volume_cc'].min()) / 20,
                    show_rug=False,
                    colors=[COLORS['primary']]
                )
                
                fig.update_layout(
                    title="Brustvolumen-Verteilung",
                    xaxis_title="Volumen (cc)",
                    yaxis_title="Dichte",
                    plot_bgcolor=COLORS['light'],
                    paper_bgcolor=COLORS['light'],
                    font={'color': COLORS['text']},
                    margin=dict(l=40, r=40, t=50, b=40),
                    hovermode='closest'
                )
                
                # Füge Mittelwert und Median als vertikale Linien hinzu
                mean_vol = df['volume_cc'].mean()
                median_vol = df['volume_cc'].median()
                
                fig.add_shape(
                    type="line",
                    x0=mean_vol, y0=0, x1=mean_vol, y1=fig.data[0].y.max(),
                    line=dict(color=COLORS['danger'], width=2, dash="dash"),
                    name="Mittelwert"
                )
                
                fig.add_shape(
                    type="line",
                    x0=median_vol, y0=0, x1=median_vol, y1=fig.data[0].y.max(),
                    line=dict(color=COLORS['success'], width=2, dash="dot"),
                    name="Median"
                )
                
                fig.add_annotation(
                    x=mean_vol,
                    y=fig.data[0].y.max(),
                    text=f"Mittelwert: {mean_vol:.0f}cc",
                    showarrow=True,
                    arrowhead=1,
                    ax=50,
                    ay=-30
                )
                
                fig.add_annotation(
                    x=median_vol,
                    y=fig.data[0].y.max() * 0.8,
                    text=f"Median: {median_vol:.0f}cc",
                    showarrow=True,
                    arrowhead=1,
                    ax=-50,
                    ay=-30
                )
                
                return fig
            
            return go.Figure()
        
        # Callback für Top Volume Performers
        @self.app.callback(
            Output('top-volume-performers', 'children'),
            [Input('stats-store', 'children')]
        )
        def update_top_volume_performers(stats_json):
            if not stats_json:
                return html.Div("Keine Daten verfügbar")
                
            stats = json.loads(stats_json)
            volume_stats = stats.get('volume_stats', {})
            top_performers = volume_stats.get('top_volume_performers', [])
            
            if not top_performers:
                return html.Div("Keine Daten zu Top-Performern nach Volumen verfügbar", 
                               className="alert alert-info")
            
            # Erstelle Tabelle mit Top-Performern
            table_header = [
                html.Thead(html.Tr([
                    html.Th("Name"),
                    html.Th("Cup-Größe"),
                    html.Th("Volumen (cc)"),
                    html.Th("Kategorie"),
                    html.Th("O-Counter")
                ]))
            ]
            
            rows = []
            for performer in top_performers:
                rows.append(html.Tr([
                    html.Td(performer.get('name', 'Unbekannt')),
                    html.Td(performer.get('cup_size', 'N/A')),
                    html.Td(f"{performer.get('volume_cc', 0):.0f}"),
                    html.Td(performer.get('volume_category', 'N/A')),
                    html.Td(performer.get('o_counter', 0))
                ]))
            
            table_body = [html.Tbody(rows)]
            
            return html.Div([
                html.H5("Top Performer nach Brustvolumen"),
                html.Table(table_header + table_body, className="table table-striped table-hover")
            ])
        
        # Callback für Sister Size Vergleich
        @self.app.callback(
            Output('sister-size-comparison', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_sister_size_comparison(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            sister_size_stats = stats.get('sister_size_stats', {})
            original_vs_sister = sister_size_stats.get('original_vs_sister_stats', {})
            
            if not original_vs_sister:
                return go.Figure()
            
            # Extrahiere Daten für Vergleich
            original_stats = original_vs_sister.get('original_stats', {})
            sister_stats = original_vs_sister.get('sister_stats', {})
            
            # Erstelle Balkendiagramm für Vergleich
            categories = ['O-Counter', 'Rating', 'Volumen']
            original_values = [
                original_stats.get('o_counter', 0),
                original_stats.get('rating100', 0),
                original_stats.get('volume_cc', 0) / 100  # Skaliere für bessere Darstellung
            ]
            sister_values = [
                sister_stats.get('o_counter', 0),
                sister_stats.get('rating100', 0),
                sister_stats.get('volume_cc', 0) / 100  # Skaliere für bessere Darstellung
            ]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=categories,
                y=original_values,
                name='Original-Größe',
                marker_color=COLORS['primary']
            ))
            
            fig.add_trace(go.Bar(
                x=categories,
                y=sister_values,
                name='Sister Size',
                marker_color=COLORS['success']
            ))
            
            fig.update_layout(
                title="Vergleich: Original-Größe vs. Sister Size",
                xaxis_title="Metrik",
                yaxis_title="Wert",
                barmode='group',
                plot_bgcolor=COLORS['light'],
                paper_bgcolor=COLORS['light'],
                font={'color': COLORS['text']},
                margin=dict(l=40, r=40, t=50, b=40),
                hovermode='closest',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Füge Anmerkungen für Volumen hinzu
            fig.add_annotation(
                x=2, y=original_values[2],
                text=f"{original_stats.get('volume_cc', 0):.0f}cc",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-20
            )
            
            fig.add_annotation(
                x=2, y=sister_values[2],
                text=f"{sister_stats.get('volume_cc', 0):.0f}cc",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-20
            )
            
            return fig
        
        # Callback für Export-Funktion
        @self.app.callback(
            Output('download-stats', 'data'),
            [Input('export-button', 'n_clicks')],
            [State('stats-store', 'children')]
        )
        def export_statistics(n_clicks, stats_json):
            if not n_clicks or not stats_json:
                return None
                
            stats = json.loads(stats_json)
            
            # Erstelle ein Dictionary mit den wichtigsten Statistiken für den Export
            export_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'cup_size_stats': stats.get('cup_size_stats', {}).get('cup_size_counts', {}),
                'o_counter_stats': {
                    'average': stats.get('o_counter_stats', {}).get('average_o_counter', 0),
                    'median': stats.get('o_counter_stats', {}).get('median_o_counter', 0),
                    'max': stats.get('o_counter_stats', {}).get('max_o_counter', 0)
                },
                'volume_stats': stats.get('volume_stats', {}).get('volume_stats', {}),
                'ratio_stats': stats.get('ratio_stats', {}).get('ratio_stats', [])
            }
            
            # Erstelle einen Dateinamen mit Zeitstempel
            filename = f"stash_stats_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            return dict(content=json.dumps(export_data, indent=2), filename=filename)
            
        # Callback für Filter-Initialisierung
        @self.app.callback(
            Output('cup-size-filter', 'options'),
            [Input('stats-store', 'children')]
        )
        def initialize_filters(stats_json):
            if not stats_json:
                return []
                
            stats = json.loads(stats_json)
            cup_stats = stats.get('cup_size_stats', {})
            cup_counts = cup_stats.get('cup_size_counts', {})
            
            # Erstelle Dropdown-Optionen für Cup-Größen
            cup_options = [{'label': f"{cup} ({count})", 'value': cup} 
                          for cup, count in sorted(cup_counts.items())]
            
            return cup_options
            
        # Callback für Filter-Anwendung
        @self.app.callback(
            Output('search-results', 'children'),
            [Input('apply-filters-button', 'n_clicks'),
             Input('search-button', 'n_clicks')],
            [State('performer-search', 'value'),
             State('cup-size-filter', 'value'),
             State('bmi-range-filter', 'value'),
             State('o-counter-range-filter', 'value'),
             State('stats-store', 'children')]
        )
        def apply_filters(filter_clicks, search_clicks, search_term, cup_sizes, bmi_range, o_counter_range, stats_json):
            # Bestimme, welcher Button geklickt wurde
            ctx = dash.callback_context
            if not ctx.triggered:
                return html.Div()
                
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if not stats_json:
                return html.Div("Keine Daten verfügbar", className="alert alert-warning")
                
            stats = json.loads(stats_json)
            cup_stats = stats.get('cup_size_stats', {})
            cup_df_list = cup_stats.get('cup_size_dataframe', [])
            
            if not cup_df_list:
                return html.Div("Keine Performer-Daten verfügbar", className="alert alert-warning")
            
            # Erstelle DataFrame
            cup_df = pd.DataFrame(cup_df_list)
            
            # Wende Filter an
            if button_id == 'apply-filters-button' or (button_id == 'search-button' and search_term):
                filtered_df = cup_df.copy()
                
                # Textsuche
                if search_term:
                    filtered_df = filtered_df[filtered_df['name'].str.lower().str.contains(search_term.lower())]
                
                # Cup-Größen Filter
                if cup_sizes and len(cup_sizes) > 0:
                    filtered_df = filtered_df[filtered_df['cup_size'].isin(cup_sizes)]
                
                # BMI-Bereich Filter
                if bmi_range and len(bmi_range) == 2:
                    filtered_df = filtered_df[(filtered_df['bmi'] >= bmi_range[0]) & 
                                             (filtered_df['bmi'] <= bmi_range[1])]
                
                # O-Counter-Bereich Filter
                if o_counter_range and len(o_counter_range) == 2:
                    filtered_df = filtered_df[(filtered_df['o_counter'] >= o_counter_range[0]) & 
                                             (filtered_df['o_counter'] <= o_counter_range[1])]
                
                if filtered_df.empty:
                    return html.Div("Keine Performer entsprechen den Filterkriterien", className="alert alert-info")
                
                # Erstelle Ergebnisliste
                result_items = []
                
                for _, performer in filtered_df.iterrows():
                    result_items.append(html.Div([
                        html.Div([
                            html.H5(performer['name'], className="mb-1"),
                            html.Div([
                                html.Span(f"Cup-Größe: {performer.get('cup_size', 'N/A')}", 
                                         className="badge badge-primary mr-2"),
                                html.Span(f"O-Counter: {performer.get('o_counter', 0)}", 
                                         className="badge badge-success mr-2"),
                                html.Span(f"BMI: {performer.get('bmi', 'N/A')}", 
                                         className="badge badge-info mr-2")
                            ]),
                            html.Button("Ähnliche Performer anzeigen", 
                                       id={'type': 'show-similar', 'index': performer['id']},
                                       className="btn btn-sm btn-outline-primary mt-2")
                        ], className="card-body")
                    ], className="card mb-2"))
                
                filter_text = []
                if search_term:
                    filter_text.append(f"Suchbegriff: '{search_term}'")
                if cup_sizes and len(cup_sizes) > 0:
                    filter_text.append(f"Cup-Größen: {', '.join(cup_sizes)}")
                if bmi_range and len(bmi_range) == 2:
                    filter_text.append(f"BMI: {bmi_range[0]}-{bmi_range[1]}")
                if o_counter_range and len(o_counter_range) == 2:
                    filter_text.append(f"O-Counter: {o_counter_range[0]}-{o_counter_range[1]}")
                
                filter_description = ", ".join(filter_text)
                
                return html.Div([
                    html.H4(f"Suchergebnisse ({len(filtered_df)} Performer)"),
                    html.P(filter_description, className="text-muted mb-3"),
                    html.Div(result_items)
                ])
            
            return html.Div()
            
        # Callback für Filter-Reset
        @self.app.callback(
            [Output('cup-size-filter', 'value'),
             Output('bmi-range-filter', 'value'),
             Output('o-counter-range-filter', 'value')],
            [Input('reset-filters-button', 'n_clicks')]
        )
        def reset_filters(n_clicks):
            if not n_clicks:
                return dash.no_update, dash.no_update, dash.no_update
            return [], [18, 30], [0, 30]
            
        # Callback für 3D-Visualisierung
        @self.app.callback(
            Output('3d-visualization', 'figure'),
            [Input('x-axis-selector', 'value'),
             Input('y-axis-selector', 'value'),
             Input('z-axis-selector', 'value'),
             Input('stats-store', 'children')]
        )
        def update_3d_visualization(x_axis, y_axis, z_axis, stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            cup_stats = stats.get('cup_size_stats', {})
            cup_df_list = cup_stats.get('cup_size_dataframe', [])
            
            if not cup_df_list:
                return go.Figure()
            
            df = pd.DataFrame(cup_df_list)
            
            # Filtere Zeilen mit fehlenden Werten
            df = df.dropna(subset=[x_axis, y_axis, z_axis])
            
            if df.empty:
                return go.Figure()
            
            # Erstelle 3D-Scatter-Plot
            axis_labels = {
                'cup_numeric': 'Cup-Größe (numerisch)',
                'bmi': 'BMI',
                'volume_cc': 'Volumen (cc)',
                'height_cm': 'Körpergröße (cm)',
                'weight': 'Gewicht (kg)',
                'o_counter': 'O-Counter',
                'rating100': 'Rating (0-100)'
            }
            
            fig = px.scatter_3d(
                df, x=x_axis, y=y_axis, z=z_axis,
                color='o_counter',
                size='o_counter',
                size_max=15,
                opacity=0.7,
                color_continuous_scale=px.colors.sequential.Viridis,
                hover_name='name',
                hover_data=['cup_size', 'measurements', 'o_counter', 'rating100'],
                labels={
                    x_axis: axis_labels.get(x_axis, x_axis),
                    y_axis: axis_labels.get(y_axis, y_axis),
                    z_axis: axis_labels.get(z_axis, z_axis),
                    'o_counter': 'O-Counter'
                }
            )
            
            fig.update_layout(
                scene=dict(
                    xaxis_title=axis_labels.get(x_axis, x_axis),
                    yaxis_title=axis_labels.get(y_axis, y_axis),
                    zaxis_title=axis_labels.get(z_axis, z_axis)
                ),
                margin=dict(l=0, r=0, b=0, t=30),
                coloraxis_colorbar=dict(title="O-Counter")
            )
            
            return fig
            
        # Callback für Zeitreihenanalyse
        @self.app.callback(
            Output('o-counter-trend', 'figure'),
            [Input('stats-store', 'children')]
        )
        def update_o_counter_trend(stats_json):
            if not stats_json:
                return go.Figure()
                
            stats = json.loads(stats_json)
            cup_stats = stats.get('cup_size_stats', {})
            cup_df_list = cup_stats.get('cup_size_dataframe', [])
            
            if not cup_df_list:
                return go.Figure()
            
            df = pd.DataFrame(cup_df_list)
            
            # Simuliere Zeitreihendaten (da wir keine echten Zeitdaten haben)
            # In einer realen Anwendung würden hier tatsächliche Zeitstempel verwendet
            cup_letters = sorted(df['cup_letter'].unique())
            years = list(range(2015, 2026))
            
            # Erstelle synthetische Trenddaten
            trend_data = []
            for cup in cup_letters:
                cup_performers = df[df['cup_letter'] == cup]
                if cup_performers.empty:
                    continue
                    
                avg_o_counter = cup_performers['o_counter'].mean()
                
                for year in years:
                    # Simuliere eine leichte Variation über die Jahre
                    variation = (year - 2015) * 0.1 * avg_o_counter
                    trend_data.append({
                        'cup_letter': cup,
                        'year': year,
                        'avg_o_counter': avg_o_counter + variation
                    })
            
            trend_df = pd.DataFrame(trend_data)
            
            # Erstelle Liniendiagramm
            fig = px.line(
                trend_df, x='year', y='avg_o_counter', color='cup_letter',
                title="O-Counter Trend nach Cup-Größe (simulierte Daten)",
                labels={'year': 'Jahr', 'avg_o_counter': 'Durchschnittlicher O-Counter', 'cup_letter': 'Cup-Buchstabe'}
            )
            
            fig.update_layout(
                plot_bgcolor=COLORS['light'],
                paper_bgcolor=COLORS['light'],
                font={'color': COLORS['text']},
                margin=dict(l=40, r=40, t=50, b=40),
                hovermode='closest',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
            
        # Callback für Zeitverteilung
        @self.app.callback(
            Output('time-distribution', 'figure'),
            [Input('time-range-slider', 'value'),
             Input('stats-store', 'children')]
        )
        def update_time_distribution(time_range, stats_json):
            if not stats_json or not time_range or len(time_range) != 2:
                return go.Figure()
                
            stats = json.loads(stats_json)
            cup_stats = stats.get('cup_size_stats', {})
            cup_df_list = cup_stats.get('cup_size_dataframe', [])
            
            if not cup_df_list:
                return go.Figure()
            
            # Simuliere Zeitdaten für die Visualisierung
            # In einer realen Anwendung würden hier tatsächliche Zeitstempel verwendet
            start_year, end_year = time_range
            
            # Erstelle synthetische Daten für die Zeitverteilung
            cup_counts = cup_stats.get('cup_size_counts', {})
            time_data = []
            
            for cup, count in cup_counts.items():
                # Verteile die Anzahl über die Jahre im ausgewählten Bereich
                years = list(range(start_year, end_year + 1))
                year_counts = []
                
                # Simuliere eine Verteilung über die Jahre
                total = 0
                for year in years:
                    # Mehr neuere Daten als ältere (simuliert Wachstum)
                    year_weight = (year - start_year + 1) / (end_year - start_year + 1)
                    year_count = int(count * year_weight * 0.2)
                    total += year_count
                    year_counts.append(year_count)
                
                # Stelle sicher, dass die Summe stimmt
                if total < count:
                    # Verteile den Rest auf die Jahre
                    remainder = count - total
                    for i in range(remainder):
                        year_counts[i % len(year_counts)] += 1
                
                for year, year_count in zip(years, year_counts):
                    time_data.append({
                        'cup_size': cup,
                        'year': year,
                        'count': year_count
                    })
            
            time_df = pd.DataFrame(time_data)
            
            # Erstelle gestapeltes Balkendiagramm
            fig = px.bar(
                time_df, x='year', y='count', color='cup_size',
                title=f"Cup-Größen Verteilung {start_year}-{end_year} (simulierte Daten)",
                labels={'year': 'Jahr', 'count': 'Anzahl', 'cup_size': 'Cup-Größe'}
            )
            
            fig.update_layout(
                plot_bgcolor=COLORS['light'],
                paper_bgcolor=COLORS['light'],
                font={'color': COLORS['text']},
                margin=dict(l=40, r=40, t=50, b=40),
                hovermode='closest',
                barmode='stack'
            )
            
            return fig
            
        # Callback für Konfigurationsinfo
        @self.app.callback(
            Output('config-info', 'children'),
            [Input('min-o-counter-slider', 'value'),
             Input('similarity-threshold-slider', 'value'),
             Input('cup-weight-slider', 'value'),
             Input('bmi-weight-slider', 'value')]
        )
        def update_config_info(min_o_counter, similarity_threshold, cup_weight, bmi_weight):
            return [
                html.P([
                    "Aktuelle Konfiguration: ",
                    html.Br(),
                    f"Minimaler O-Counter: {min_o_counter}, ",
                    f"Ähnlichkeitsschwellwert: {similarity_threshold}, ",
                    html.Br(),
                    f"Gewichtung Cup-Größe: {cup_weight}, ",
                    f"Gewichtung BMI: {bmi_weight}"
                ])
            ]
        
        # Callback für Update-Info
        @self.app.callback(
            Output('update-info', 'children'),
            [Input('stats-store', 'children')]
        )
        def update_info_text(stats_json):
            if not stats_json:
                return "Keine Daten geladen."
                
            stats = json.loads(stats_json)
            
            # Zähle die Anzahl der Performer mit Daten
            cup_stats = stats.get('cup_size_stats', {})
            performer_count = len(cup_stats.get('cup_size_dataframe', []))
            
            # Zähle die Anzahl der Performer mit O-Counter > 0
            o_counter_stats = stats.get('o_counter_stats', {})
            o_counter_performers = o_counter_stats.get('total_performers', 0)
            
            return f"Daten für {performer_count} Performer geladen, davon {o_counter_performers} mit O-Counter > 0."
    
    def run_server(self, debug=True, port=8050, host='0.0.0.0'):
        """Run the dashboard server"""
        self.app.run(debug=debug, port=port, host=host)
