# Stash API Tools

Eine Sammlung von Tools zur Analyse und Verwaltung von Stash-Daten mit Fokus auf Performer-Statistiken, Empfehlungen und Integration.

## Funktionen

- **Statistik-Modul**: Analysiert Cup-Größen, O-Counter und verschiedene Verhältnisse
- **Empfehlungs-Modul**: Schlägt ähnliche Performer und Szenen basierend auf Ihren Vorlieben vor
- **Dashboard-Modul**: Interaktives Web-Dashboard zur Visualisierung von Statistiken und Empfehlungen
- **Updater-Modul**: Aktualisiert Performer-Daten mit Cup-Größen und Verhältnis-Informationen
- **Discord-Modul**: Sendet Statistiken und Empfehlungen an Discord über Webhooks

## Installation

### Voraussetzungen

- Python 3.7 oder höher
- Stash-Server mit GraphQL API
- Pip (Python-Paketmanager)

### Abhängigkeiten installieren

```bash
pip install -e .
```

### Konfiguration

1. Klonen Sie das Repository oder laden Sie die Dateien herunter
2. Bearbeiten Sie die Datei `config/configuration.ini` und geben Sie Ihre Stash-API-Informationen und Discord-Webhook-URL ein

## Verwendung

### Statistiken generieren

```bash
python main.py stats
python main.py stats --output stats.json
```

### Empfehlungen generieren

```bash
python main.py recommend --type performers
python main.py recommend --type scenes
python main.py recommend --type all
```

### Dashboard starten

```bash
python main.py dashboard --port 8050
```

Öffnen Sie dann einen Browser und navigieren Sie zu `http://localhost:8050`

### Performer-Daten aktualisieren

```bash
python main.py update --type cup-sizes
python main.py update --type ratios
python main.py update --type all
```

### Send Recommendations to Discord

```bash
python main.py discord
```

This command will:
- Generate performer recommendations
- Generate scene recommendations
- Send the recommendations to the configured Discord webhook
- Print recommendations to the console

## Module

### Statistik-Modul

Analysiert Ihre Stash-Daten und generiert Statistiken zu:
- Cup-Größen-Verteilung
- O-Counter nach Cup-Größe
- Verhältnisse wie Cup-to-BMI, Cup-to-Height, Cup-to-Weight

### Empfehlungs-Modul

- **Performer-Empfehlungen**: Findet ähnliche Performer basierend auf Cup-Größe, Körpermaßen und anderen Faktoren
- **Szenen-Empfehlungen**: Schlägt Szenen vor, die ähnliche Tags wie Ihre favorisierten Szenen haben

### Dashboard-Modul

# Stash Statistics Dashboard

This interactive dashboard visualizes various statistics from your Stash data, focusing on performer metrics, cup sizes, sister sizes, o-counter values, and their correlations.

## Features

The dashboard includes the following features:

- **Cup Size Statistics**: Visualize cup size distribution, cup size by band size, and detailed cup size statistics
- **O-Counter Statistics**: See o-counter by cup size, top performers by o-counter, favorite vs non-favorite o-counter comparison, and o-counter distribution
- **Ratio Statistics**: Explore cup to BMI ratio, cup to height ratio, BMI distribution by cup size, and height distribution by cup size
- **Sister Size Statistics**: View sister size distribution, o-counter by sister size, volume distribution, and o-counter by volume category
- **Correlation Analysis**: Analyze correlations between o-counter & rating, cup size & BMI, cup size & height, and cup size & weight
- **Preference Analysis**: Examine performer clusters, preference profiles, and top performers by cluster

## Requirements

- Python 3.7 or higher
- Stash server with GraphQL API
- Python packages: dash, plotly, pandas, numpy

## Installation

1. Clone the repository or download the files
2. Install the required dependencies:

```bash
pip install -e .
```

## Usage

1. Edit the `config/configuration.ini` file to set your Stash API information:

```ini
[stash]
api_key = your_api_key_here
host = localhost
port = 9999
```

2. Run the dashboard:

```bash
python dashboard.py
```

3. Open your web browser and navigate to `http://localhost:8050`

### Command Line Options

- `--port`: Specify a custom port (default: 8050)
- `--debug`: Run in debug mode

Example:
```bash
python dashboard.py --port 8051 --debug
```

## Refreshing Data

To refresh the data displayed in the dashboard:

1. Click the "Refresh Data" button at the top of the page
2. The dashboard will fetch the latest data from your Stash server

## Dashboard Sections

### Cup Size Statistics
This tab shows the distribution of cup sizes among performers, visualized in various ways:
- **Cup Size Distribution**: Bar chart showing the count of performers with each cup size
- **Cup Size by Band Size**: Heatmap showing the frequency of band size and cup letter combinations
- **Cup Size Statistics Table**: Detailed table with cup size counts and percentages

### O-Counter Statistics
This tab focuses on orgasm counter statistics:
- **O-Counter by Cup Size**: Average o-counter value for each cup letter
- **Top Performers by O-Counter**: Table showing performers with the highest o-counter values
- **Favorite vs Non-Favorite O-Counter**: Comparison of o-counter statistics between favorite and non-favorite performers
- **O-Counter Distribution**: Histogram showing the distribution of o-counter values

### Ratio Statistics
This tab explores various ratios and relationships:
- **Cup to BMI Ratio**: How cup size relates to BMI
- **Cup to Height Ratio**: How cup size relates to height
- **BMI Distribution by Cup Size**: Box plot showing BMI distribution for each cup letter
- **Height Distribution by Cup Size**: Box plot showing height distribution for each cup letter

### Sister Size Statistics
This tab explores sister sizes and volume-related statistics:
- **Sister Size Distribution**: Most common sister sizes
- **O-Counter by Sister Size**: Average o-counter value for each sister size
- **Volume Distribution**: Performer count by volume category
- **O-Counter by Volume**: Average o-counter value for each volume category

### Correlation Analysis
This tab shows scatter plots with trendlines for various correlations:
- **O-Counter vs Rating Correlation**: How o-counter correlates with performer rating
- **Cup Size vs BMI Correlation**: Relationship between cup size and BMI
- **Cup Size vs Height Correlation**: Relationship between cup size and height
- **Cup Size vs Weight Correlation**: Relationship between cup size and weight

### Preference Analysis
This tab provides insights into performer preferences:
- **Performer Clusters**: Radar chart showing performer clusters based on various features
- **Preference Profile**: Summary of preference profile with statistical information
- **Top Performers by Cluster**: Tables showing top performers in each identified cluster

### Updater-Modul

- Aktualisiert Performer mit EU-Cup-Größen-Tags
- Fügt Verhältnis-Informationen zu Performer-Details hinzu

### Discord-Modul

Sendet regelmäßige Updates an Discord:
- Statistik-Zusammenfassungen mit Diagrammen
- Performer-Empfehlungen
- Szenen-Empfehlungen
- 

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.# Stash Analytics Dashboard

Ein interaktives Dashboard zur Analyse von StashApp-Daten mit Fokus auf Performer-Statistiken, O-Counter-Korrelationen und Brustgrößen-Analysen.

## Installation

1. Stelle sicher, dass Python 3.7+ installiert ist
2. Installiere die benötigten Abhängigkeiten:

```bash
pip install dash pandas plotly numpy requests
```

## Konfiguration

Bei der ersten Ausführung wird automatisch eine Konfigurationsdatei unter `config/configuration.ini` erstellt. Bearbeite diese Datei, um deine Stash-Instanz zu konfigurieren:

```ini
[stash]
url = http://localhost:9999
api_key = dein_api_key_hier

[dashboard]
cache_duration = 3600

[discord]
webhook_url = 
enable_stats_posting = false
enable_performer_recommendations = false
enable_scene_recommendations = false
```

## Verwendung

Starte das Dashboard mit:

```bash
python run_dashboard.py
```

Optionale Parameter:
- `--port PORT`: Port für den Dashboard-Server (Standard: 8050)
- `--host HOST`: Host für den Dashboard-Server (Standard: 0.0.0.0)
- `--debug`: Debug-Modus aktivieren

Öffne dann einen Browser und navigiere zu `http://localhost:8050`

## Datenverzeichnisse

Das Dashboard erstellt automatisch folgende Verzeichnisse:
- `data/cache`: Für zwischengespeicherte Statistiken
- `data/exports`: Für exportierte Daten
- `config`: Für Konfigurationsdateien
- `assets`: Für Dashboard-Assets wie CSS

## Fehlerbehebung

Wenn keine Daten angezeigt werden:
1. Überprüfe die Stash-URL und den API-Key in der Konfigurationsdatei
2. Stelle sicher, dass deine Stash-Instanz läuft und erreichbar ist
3. Prüfe, ob die Performer in Stash Messungen (measurements) mit Brustgrößen haben
