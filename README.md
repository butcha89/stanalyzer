# Stash API Tools

A collection of tools for analyzing and managing Stash data with a focus on performer statistics, recommendations, and integration.

## Features

- **Statistics Module**: Analyzes cup sizes, O-counter, and various ratios
- **Recommendation Module**: Suggests similar performers and scenes based on your preferences
- **Dashboard Module**: Interactive web dashboard for visualizing statistics and recommendations
- **Updater Module**: Updates performer data with cup sizes and ratio information
- **Discord Module**: Sends statistics and recommendations to Discord via webhooks
- **Telegram Module**: Sends statistics and recommendations to Telegram

## Installation

### Prerequisites

- Python 3.7 or higher
- Stash server with GraphQL API
- Pip (Python package manager)

### Installing Dependencies

```bash
pip install -e .
Configuration

Clone the repository or download the files
Edit the config/configuration.ini file with your Stash API information and webhook URLs

Usage
Statistics
Generate and view statistics about your Stash data:
bashpython main.py stats
python main.py stats --output custom_stats.json
Recommendations
Generate performer and scene recommendations:
bashpython main.py recommend --type performers
python main.py recommend --type scenes
python main.py recommend --type all
Dashboard
Start the interactive dashboard:
bashpython run_dashboard.py
python run_dashboard.py --port 8051
python run_dashboard.py --host 127.0.0.1 --port 8050 --debug
Open your browser and navigate to http://localhost:8050 (or your custom port)
Update Performer Data
Update performer metadata:
bashpython main.py update --type cup-sizes
python main.py update --type ratios
python main.py update --type all
Discord Integration
Send data to Discord:
bashpython main.py discord
python main.py discord --type recommendations
python main.py discord --type stats
python main.py discord --type all
Comprehensive Stats and Recommendations
Run all statistics, recommendations and notifications in one command:
bashpython run_stats_and_recommendations.py
Additional options:
bashpython run_stats_and_recommendations.py --stats-only
python run_stats_and_recommendations.py --recommendations-only
python run_stats_and_recommendations.py --no-discord
python run_stats_and_recommendations.py --no-telegram
python run_stats_and_recommendations.py --no-export
Modules
Statistics Module
Analyzes your Stash data and generates statistics on:

Cup size distribution
O-counter by cup size
Ratios like cup-to-BMI, cup-to-height, cup-to-weight
Sister sizes and volume analysis
Rating and O-counter correlations

Recommendation Module

Performer Recommendations: Finds similar performers based on cup size, body measurements and other factors
Scene Recommendations: Suggests scenes with similar tags to your favorite scenes

Dashboard Module
The interactive dashboard visualizes various statistics from your Stash data, including:

Cup Size Statistics: Cup size distribution, cup size by band size, and detailed cup size statistics
O-Counter Statistics: O-counter by cup size, top performers by O-counter, and O-counter distribution
Ratio Statistics: Cup to BMI ratio, cup to height ratio, and related distributions
Sister Size Statistics: Sister size distribution, O-counter by sister size, volume distribution
Correlation Analysis: Correlations between O-counter & rating, cup size & BMI, etc.
Preference Analysis: Performer clusters, preference profiles, and top performers by cluster
Visualization Tools: Interactive charts and graphs for all statistics

Updater Module

Updates performers with EU cup size tags
Adds ratio information to performer details

Discord Module
Sends regular updates to Discord:

Statistics summaries with charts
Performer recommendations
Scene recommendations

Telegram Module
Similar to the Discord module, but sends data to Telegram:

Statistics summaries
Performer recommendations
Scene recommendations

Troubleshooting
If no data is displayed:

Check your Stash URL and API key in the configuration file
Ensure your Stash instance is running and accessible
Verify that performers in Stash have measurements with cup sizes

License
This project is licensed under the MIT License.
