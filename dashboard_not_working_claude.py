#!/usr/bin/env python3
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import os
import sys
import configparser
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import modules
try:
    from stash_api.stash_client import StashClient
    from modules.statistics import StatisticsModule
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# Read configuration
config = configparser.ConfigParser()
config_path = os.path.join(project_root, 'config', 'configuration.ini')
config.read(config_path)

# Initialize app
app = dash.Dash(__name__, 
                suppress_callback_exceptions=True,
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

# Set page title
app.title = "Stash Statistics Dashboard"

# Initialize StashClient and StatisticsModule
try:
    stash_client = StashClient(config_path)
    stats_module = StatisticsModule(stash_client)
except Exception as e:
    print(f"Error initializing StashClient or StatisticsModule: {e}")
    sys.exit(1)

# Define reusable styles
COLORS = {
    'background': '#f9f9f9',
    'text': '#333333',
    'primary': '#007BFF',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
}

# Layout styles
CONTENT_STYLE = {
    "margin-left": "2rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "background-color": COLORS['background'],
}

CARD_STYLE = {
    "box-shadow": "0 4px 6px 0 rgba(0, 0, 0, 0.1)",
    "border-radius": "5px",
    "background-color": "white",
    "margin": "10px",
    "padding": "15px",
}

# Define layout
app.layout = html.Div(style=CONTENT_STYLE, children=[
    # Header
    html.Div([
        html.H1("Stash Statistics Dashboard", 
                style={"textAlign": "center", "margin-bottom": "30px", "color": COLORS['primary']}),
        
        # Refresh button
        html.Div([
            html.Button("Refresh Data", id="refresh-button", 
                        style={"background-color": COLORS['info'], 
                               "color": "white", 
                               "border": "none", 
                               "border-radius": "5px",
                               "padding": "10px 20px",
                               "cursor": "pointer"}),
            html.Div(id="refresh-message", style={"margin-top": "10px", "color": COLORS['success']})
        ], style={"text-align": "center", "margin-bottom": "20px"}),
        
        # Tabs for different statistics
        dcc.Tabs([
            # Cup Size Statistics Tab
            dcc.Tab(label="Cup Size Statistics", children=[
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("Cup Size Distribution", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="cup-size-distribution")
                        ], style=CARD_STYLE, className="six columns"),
                        
                        html.Div([
                            html.H3("Cup Size by Band Size", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="cup-band-heatmap")
                        ], style=CARD_STYLE, className="six columns"),
                    ], className="row"),
                    
                    html.Div([
                        html.Div([
                            html.H3("Cup Size Statistics", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            html.Div(id="cup-size-stats-table", 
                                    style={"margin-top": "15px", "overflow": "auto", "max-height": "300px"})
                        ], style=CARD_STYLE, className="twelve columns"),
                    ], className="row"),
                ])
            ]),
            
            # O-Counter Statistics Tab
            dcc.Tab(label="O-Counter Statistics", children=[
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("O-Counter by Cup Size", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="o-counter-by-cup")
                        ], style=CARD_STYLE, className="six columns"),
                        
                        html.Div([
                            html.H3("Top Performers by O-Counter", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            html.Div(id="top-o-counter-table", 
                                    style={"margin-top": "15px", "overflow": "auto", "max-height": "300px"})
                        ], style=CARD_STYLE, className="six columns"),
                    ], className="row"),
                    
                    html.Div([
                        html.Div([
                            html.H3("Favorite vs Non-Favorite O-Counter", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="favorite-vs-non-favorite")
                        ], style=CARD_STYLE, className="six columns"),
                        
                        html.Div([
                            html.H3("O-Counter Distribution", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="o-counter-distribution")
                        ], style=CARD_STYLE, className="six columns"),
                    ], className="row"),
                ])
            ]),
            
            # Ratio Statistics Tab
            dcc.Tab(label="Ratio Statistics", children=[
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("Cup to BMI Ratio by Cup Size", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="cup-to-bmi-ratio")
                        ], style=CARD_STYLE, className="six columns"),
                        
                        html.Div([
                            html.H3("Cup to Height Ratio by Cup Size", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="cup-to-height-ratio")
                        ], style=CARD_STYLE, className="six columns"),
                    ], className="row"),
                    
                    html.Div([
                        html.Div([
                            html.H3("BMI Distribution by Cup Size", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="bmi-distribution")
                        ], style=CARD_STYLE, className="six columns"),
                        
                        html.Div([
                            html.H3("Height Distribution by Cup Size", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="height-distribution")
                        ], style=CARD_STYLE, className="six columns"),
                    ], className="row"),
                ])
            ]),
            
            # Sister Size Statistics Tab
            dcc.Tab(label="Sister Size Statistics", children=[
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("Sister Size Distribution", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="sister-size-distribution")
                        ], style=CARD_STYLE, className="six columns"),
                        
                        html.Div([
                            html.H3("O-Counter by Sister Size", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="o-counter-by-sister-size")
                        ], style=CARD_STYLE, className="six columns"),
                    ], className="row"),
                    
                    html.Div([
                        html.Div([
                            html.H3("Volume Distribution", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="volume-distribution")
                        ], style=CARD_STYLE, className="six columns"),
                        
                        html.Div([
                            html.H3("O-Counter by Volume Category", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="o-counter-by-volume")
                        ], style=CARD_STYLE, className="six columns"),
                    ], className="row"),
                ])
            ]),
            
            # Correlation Analysis Tab
            dcc.Tab(label="Correlation Analysis", children=[
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("O-Counter vs Rating Correlation", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="o-counter-rating-correlation")
                        ], style=CARD_STYLE, className="six columns"),
                        
                        html.Div([
                            html.H3("Cup Size vs BMI Correlation", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="cup-size-bmi-correlation")
                        ], style=CARD_STYLE, className="six columns"),
                    ], className="row"),
                    
                    html.Div([
                        html.Div([
                            html.H3("Cup Size vs Height Correlation", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="cup-size-height-correlation")
                        ], style=CARD_STYLE, className="six columns"),
                        
                        html.Div([
                            html.H3("Cup Size vs Weight Correlation", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="cup-size-weight-correlation")
                        ], style=CARD_STYLE, className="six columns"),
                    ], className="row"),
                ])
            ]),
            
            # Preference Analysis Tab
            dcc.Tab(label="Preference Analysis", children=[
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("Performer Clusters", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            dcc.Graph(id="performer-clusters")
                        ], style=CARD_STYLE, className="six columns"),
                        
                        html.Div([
                            html.H3("Preference Profile", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            html.Div(id="preference-profile", 
                                    style={"margin-top": "15px", "overflow": "auto", "max-height": "300px"})
                        ], style=CARD_STYLE, className="six columns"),
                    ], className="row"),
                    
                    html.Div([
                        html.Div([
                            html.H3("Top Performers by Cluster", 
                                    style={"textAlign": "center", "color": COLORS['primary']}),
                            html.Div(id="top-performers-by-cluster", 
                                    style={"margin-top": "15px", "overflow": "auto", "max-height": "300px"})
                        ], style=CARD_STYLE, className="twelve columns"),
                    ], className="row"),
                ])
            ]),
        ], style={"margin-top": "20px"})
    ]),
    
    # Footer
    html.Div([
        html.P("Stash Statistics Dashboard © " + str(datetime.now().year), 
               style={"textAlign": "center", "color": COLORS['secondary']}),
        html.P(id="last-updated", 
               style={"textAlign": "center", "color": COLORS['secondary'], "fontSize": "smaller"}),
    ], style={"margin-top": "50px"}),
    
    # Hidden divs for storing data
    html.Div(id="stats-data", style={"display": "none"}),
    dcc.Interval(id="load-interval", interval=1*1000, n_intervals=0, max_intervals=1),
])

# Callback to load data on startup
@app.callback(
    Output("stats-data", "children"),
    Output("last-updated", "children"),
    Input("load-interval", "n_intervals"),
    Input("refresh-button", "n_clicks"),
    prevent_initial_call=False
)
def load_data(n_intervals, n_clicks):
    # Generate the timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate all statistics
    try:
        stats = stats_module.generate_all_stats()
        stats_json = json.dumps(stats, default=lambda o: str(o) if isinstance(o, pd.Series) or isinstance(o, np.ndarray) else o)
        return stats_json, f"Last updated: {timestamp}"
    except Exception as e:
        print(f"Error generating statistics: {e}")
        return "{}", f"Error loading data. Last attempt: {timestamp}"

# Callback for refresh message
@app.callback(
    Output("refresh-message", "children"),
    Input("refresh-button", "n_clicks"),
    prevent_initial_call=True
)
def show_refresh_message(n_clicks):
    if n_clicks:
        return "Data refreshed!"
    return ""

# Callback for cup size distribution graph
@app.callback(
    Output("cup-size-distribution", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_cup_size_distribution(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        cup_stats = stats.get("cup_size_stats", {})
        cup_counts = cup_stats.get("cup_size_counts", {})
        
        if not cup_counts:
            return go.Figure().update_layout(title="No cup size data available")
        
        # Sort cup sizes numerically by band size and alphabetically by cup letter
        def sort_key(cup_size):
            import re
            match = re.match(r'(\d+)([A-Za-z]+)', cup_size)
            if match:
                band, cup = match.groups()
                return (int(band), cup)
            return (0, '')
        
        sorted_cup_sizes = sorted(cup_counts.items(), key=lambda x: sort_key(x[0]))
        cups, counts = zip(*sorted_cup_sizes)
        
        fig = px.bar(
            x=cups, 
            y=counts, 
            title="Cup Size Distribution",
            labels={'x': 'Cup Size', 'y': 'Count'},
            color=counts,
            color_continuous_scale='Viridis'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            coloraxis_showscale=False
        )
        
        return fig
    except Exception as e:
        print(f"Error updating cup size distribution: {e}")
        return go.Figure().update_layout(title="Error loading cup size distribution")

# Callback for cup band heatmap
@app.callback(
    Output("cup-band-heatmap", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_cup_band_heatmap(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        cup_stats = stats.get("cup_size_stats", {})
        cup_size_dataframe = cup_stats.get("cup_size_dataframe", [])
        
        if not cup_size_dataframe:
            return go.Figure().update_layout(title="No cup size data available")
        
        # Create DataFrame from cup size data
        df = pd.DataFrame(cup_size_dataframe)
        
        # Ensure band_size and cup_letter columns exist
        if 'band_size' not in df.columns or 'cup_letter' not in df.columns:
            return go.Figure().update_layout(title="Missing required columns for heatmap")
        
        # Count occurrences of each band size and cup letter combination
        cross_tab = pd.crosstab(df['band_size'], df['cup_letter'])
        
        # Create heatmap
        fig = px.imshow(
            cross_tab,
            labels=dict(x="Cup Letter", y="Band Size", color="Count"),
            x=cross_tab.columns,
            y=cross_tab.index,
            color_continuous_scale='Viridis',
            title='Cup Size by Band Size Heatmap'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        # Add text annotations with the count value
        for i in range(len(cross_tab.index)):
            for j in range(len(cross_tab.columns)):
                fig.add_annotation(
                    x=j,
                    y=i,
                    text=str(cross_tab.iloc[i, j]),
                    showarrow=False,
                    font=dict(color="white" if cross_tab.iloc[i, j] > cross_tab.values.max()/2 else "black")
                )
        
        return fig
    except Exception as e:
        print(f"Error updating cup band heatmap: {e}")
        return go.Figure().update_layout(title="Error loading cup band heatmap")

# Callback for cup size stats table
@app.callback(
    Output("cup-size-stats-table", "children"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_cup_size_stats_table(stats_json):
    if not stats_json:
        return "No data available"
    
    try:
        stats = json.loads(stats_json)
        cup_stats = stats.get("cup_size_stats", {})
        cup_counts = cup_stats.get("cup_size_counts", {})
        
        if not cup_counts:
            return "No cup size data available"
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(list(cup_counts.items()), columns=['Cup Size', 'Count'])
        df['Percentage'] = df['Count'] / df['Count'].sum() * 100
        
        # Sort by count descending
        df = df.sort_values('Count', ascending=False)
        
        # Create HTML table
        table_header = [
            html.Thead(html.Tr([
                html.Th("Cup Size", style={"textAlign": "center", "backgroundColor": COLORS['primary'], "color": "white"}),
                html.Th("Count", style={"textAlign": "center", "backgroundColor": COLORS['primary'], "color": "white"}),
                html.Th("Percentage", style={"textAlign": "center", "backgroundColor": COLORS['primary'], "color": "white"})
            ]))
        ]
        
        rows = []
        for index, row in df.iterrows():
            row_style = {"backgroundColor": COLORS['light']} if index % 2 else {}
            rows.append(html.Tr([
                html.Td(row['Cup Size'], style={"textAlign": "center"}),
                html.Td(row['Count'], style={"textAlign": "center"}),
                html.Td(f"{row['Percentage']:.1f}%", style={"textAlign": "center"})
            ], style=row_style))
        
        table_body = [html.Tbody(rows)]
        
        table = html.Table(table_header + table_body, 
                           style={"width": "100%", "border": "1px solid #ddd", "borderCollapse": "collapse"})
        
        return table
    except Exception as e:
        print(f"Error updating cup size stats table: {e}")
        return "Error loading cup size statistics"

# Callback for o-counter by cup graph
@app.callback(
    Output("o-counter-by-cup", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_o_counter_by_cup(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        correlation_stats = stats.get("correlation_stats", {})
        cup_letter_o_stats = correlation_stats.get("cup_letter_o_stats", [])
        
        if not cup_letter_o_stats:
            return go.Figure().update_layout(title="No o-counter by cup data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(cup_letter_o_stats)
        
        # Sort alphabetically by cup letter
        df = df.sort_values('cup_letter')
        
        # Create bar chart
        fig = px.bar(
            df,
            x='cup_letter',
            y='avg_o_count',
            title='Average O-Counter by Cup Size',
            labels={'cup_letter': 'Cup Letter', 'avg_o_count': 'Average O-Counter'},
            color='avg_o_count',
            color_continuous_scale='Viridis',
            text='performer_count'
        )
        
        # Add text showing the number of performers
        fig.update_traces(
            texttemplate='n=%{text}',
            textposition='outside'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            coloraxis_showscale=False
        )
        
        return fig
    except Exception as e:
        print(f"Error updating o-counter by cup: {e}")
        return go.Figure().update_layout(title="Error loading o-counter by cup")

# Callback for top o-counter table
@app.callback(
    Output("top-o-counter-table", "children"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_top_o_counter_table(stats_json):
    if not stats_json:
        return "No data available"
    
    try:
        stats = json.loads(stats_json)
        top_o_counter_performers = stats.get("top_o_counter_performers", [])
        
        if not top_o_counter_performers:
            return "No top o-counter performers available"
        
        # Create HTML table
        table_header = [
            html.Thead(html.Tr([
                html.Th("Name", style={"textAlign": "center", "backgroundColor": COLORS['primary'], "color": "white"}),
                html.Th("O-Counter", style={"textAlign": "center", "backgroundColor": COLORS['primary'], "color": "white"}),
                html.Th("Measurements", style={"textAlign": "center", "backgroundColor": COLORS['primary'], "color": "white"}),
                html.Th("Scene Count", style={"textAlign": "center", "backgroundColor": COLORS['primary'], "color": "white"})
            ]))
        ]
        
        rows = []
        for i, performer in enumerate(top_o_counter_performers):
            row_style = {"backgroundColor": COLORS['light']} if i % 2 else {}
            rows.append(html.Tr([
                html.Td(performer['name'], style={"textAlign": "center"}),
                html.Td(performer['o_counter'], style={"textAlign": "center"}),
                html.Td(performer['measurements'], style={"textAlign": "center"}),
                html.Td(performer['scene_count'], style={"textAlign": "center"})
            ], style=row_style))
        
        table_body = [html.Tbody(rows)]
        
        table = html.Table(table_header + table_body, 
                           style={"width": "100%", "border": "1px solid #ddd", "borderCollapse": "collapse"})
        
        return table
    except Exception as e:
        print(f"Error updating top o-counter table: {e}")
        return "Error loading top o-counter performers"

# Callback for favorite vs non-favorite graph
@app.callback(
    Output("favorite-vs-non-favorite", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_favorite_vs_non_favorite(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        favorite_stats = stats.get("favorite_o_counter_stats", {})
        
        if not favorite_stats:
            return go.Figure().update_layout(title="No favorite o-counter data available")
        
        # Extract data
        fav_stats = favorite_stats.get("favorite_stats", {})
        non_fav_stats = favorite_stats.get("non_favorite_stats", {})
        
        # Create figure with comparison
        fig = go.Figure()
        
        # Add bars for average o-counter
        fig.add_trace(go.Bar(
            x=['Favorites', 'Non-Favorites'],
            y=[fav_stats.get('avg_o_counter', 0), non_fav_stats.get('avg_o_counter', 0)],
            name='Average O-Counter',
            marker_color=COLORS['primary'],
            text=[fav_stats.get('count', 0), non_fav_stats.get('count', 0)],
            texttemplate='n=%{text}',
            textposition='outside'
        ))
        
        # Add bars for median o-counter
        fig.add_trace(go.Bar(
            x=['Favorites', 'Non-Favorites'],
            y=[fav_stats.get('median_o_counter', 0), non_fav_stats.get('median_o_counter', 0)],
            name='Median O-Counter',
            marker_color=COLORS['info'],
            opacity=0.7
        ))
        
        # Update layout
        fig.update_layout(
            title='Favorite vs Non-Favorite O-Counter Comparison',
            xaxis_title='Performer Category',
            yaxis_title='O-Counter Value',
            barmode='group',
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return fig
    except Exception as e:
        print(f"Error updating favorite vs non-favorite: {e}")
        return go.Figure().update_layout(title="Error loading favorite vs non-favorite")

# Callback for o-counter distribution
@app.callback(
    Output("o-counter-distribution", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_o_counter_distribution(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        o_counter_stats = stats.get("o_counter_stats", {})
        
        if not o_counter_stats:
            return go.Figure().update_layout(title="No o-counter distribution data available")
        
        # Get performer o-counts
        performer_o_counts = o_counter_stats.get("performer_o_counts", {})
        
        if not performer_o_counts:
            return go.Figure().update_layout(title="No performer o-count data available")
        
        # Extract o-counter values
        o_counter_values = [data.get('total_o_count', 0) for data in performer_o_counts.values()]
        
        # Create histogram
        fig = px.histogram(
            x=o_counter_values,
            nbins=30,
            title='O-Counter Distribution',
            labels={'x': 'O-Counter Value', 'y': 'Frequency'},
            color_discrete_sequence=[COLORS['primary']]
        )
        
        # Add mean line
        mean_o_counter = sum(o_counter_values) / len(o_counter_values) if o_counter_values else 0
        fig.add_vline(x=mean_o_counter, line_dash="dash", line_color=COLORS['danger'],
                     annotation_text=f"Mean: {mean_o_counter:.1f}")
        
        # Update layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return fig
    except Exception as e:
        print(f"Error updating o-counter distribution: {e}")
        return go.Figure().update_layout(title="Error loading o-counter distribution")

# Callback for cup to BMI ratio
@app.callback(
    Output("cup-to-bmi-ratio", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_cup_to_bmi_ratio(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        ratio_stats = stats.get("ratio_stats", {})
        ratio_data = ratio_stats.get("ratio_stats", [])
        
        if not ratio_data:
            return go.Figure().update_layout(title="No cup to BMI ratio data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(ratio_data)
        
        # Sort alphabetically by cup letter
        df = df.sort_values('cup_letter')
        
        # Create bar chart
        fig = px.bar(
            df,
            x='cup_letter',
            y='avg_cup_to_bmi',
            title='Average Cup to BMI Ratio by Cup Size',
            labels={'cup_letter': 'Cup Letter', 'avg_cup_to_bmi': 'Average Cup to BMI Ratio'},
            color='avg_cup_to_bmi',
            color_continuous_scale='Viridis',
            text='performer_count'
        )
        
        # Add text showing the number of performers
        fig.update_traces(
            texttemplate='n=%{text}',
            textposition='outside'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            coloraxis_showscale=False
        )
        
        return fig
    except Exception as e:
        print(f"Error updating cup to BMI ratio: {e}")
        return go.Figure().update_layout(title="Error loading cup to BMI ratio")

# Callback for cup to height ratio
@app.callback(
    Output("cup-to-height-ratio", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_cup_to_height_ratio(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        ratio_stats = stats.get("ratio_stats", {})
        ratio_data = ratio_stats.get("ratio_stats", [])
        
        if not ratio_data:
            return go.Figure().update_layout(title="No cup to height ratio data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(ratio_data)
        
        # Sort alphabetically by cup letter
        df = df.sort_values('cup_letter')
        
        # Create bar chart
        fig = px.bar(
            df,
            x='cup_letter',
            y='avg_cup_to_height',
            title='Average Cup to Height Ratio by Cup Size',
            labels={'cup_letter': 'Cup Letter', 'avg_cup_to_height': 'Average Cup to Height Ratio'},
            color='avg_cup_to_height',
            color_continuous_scale='Viridis',
            text='performer_count'
        )
        
        # Add text showing the number of performers
        fig.update_traces(
            texttemplate='n=%{text}',
            textposition='outside'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            coloraxis_showscale=False
        )
        
        return fig
    except Exception as e:
        print(f"Error updating cup to height ratio: {e}")
        return go.Figure().update_layout(title="Error loading cup to height ratio")

# Callback for BMI distribution
@app.callback(
    Output("bmi-distribution", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_bmi_distribution(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        cup_stats = stats.get("cup_size_stats", {})
        cup_size_dataframe = cup_stats.get("cup_size_dataframe", [])
        
        if not cup_size_dataframe:
            return go.Figure().update_layout(title="No cup size data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(cup_size_dataframe)
        
        # Check if BMI column exists
        if 'bmi' not in df.columns or len(df[df['bmi'].notna()]) == 0:
            return go.Figure().update_layout(title="No BMI data available")
        
        # Filter out rows with missing BMI
        df = df[df['bmi'].notna()]
        
        # Create box plot grouped by cup_letter
        fig = px.box(
            df,
            x='cup_letter',
            y='bmi',
            title='BMI Distribution by Cup Letter',
            labels={'cup_letter': 'Cup Letter', 'bmi': 'BMI'},
            color='cup_letter',
            color_discrete_sequence=px.colors.qualitative.Vivid
        )
        
        # Add reference lines for BMI categories
        fig.add_hline(y=18.5, line_dash="dash", line_color="blue", annotation_text="Underweight <18.5")
        fig.add_hline(y=25, line_dash="dash", line_color="green", annotation_text="Normal 18.5-25")
        fig.add_hline(y=30, line_dash="dash", line_color="orange", annotation_text="Overweight 25-30")
        fig.add_hline(y=35, line_dash="dash", line_color="red", annotation_text="Obese >30")
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            showlegend=False
        )
        
        return fig
    except Exception as e:
        print(f"Error updating BMI distribution: {e}")
        return go.Figure().update_layout(title="Error loading BMI distribution")

# Callback for height distribution
@app.callback(
    Output("height-distribution", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_height_distribution(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        cup_stats = stats.get("cup_size_stats", {})
        cup_size_dataframe = cup_stats.get("cup_size_dataframe", [])
        
        if not cup_size_dataframe:
            return go.Figure().update_layout(title="No cup size data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(cup_size_dataframe)
        
        # Check if height_cm column exists
        if 'height_cm' not in df.columns or len(df[df['height_cm'].notna()]) == 0:
            return go.Figure().update_layout(title="No height data available")
        
        # Filter out rows with missing height
        df = df[df['height_cm'].notna()]
        
        # Create box plot grouped by cup_letter
        fig = px.box(
            df,
            x='cup_letter',
            y='height_cm',
            title='Height Distribution by Cup Letter',
            labels={'cup_letter': 'Cup Letter', 'height_cm': 'Height (cm)'},
            color='cup_letter',
            color_discrete_sequence=px.colors.qualitative.Vivid
        )
        
        # Add reference line for average female height
        avg_height = 165  # Average female height in cm
        fig.add_hline(y=avg_height, line_dash="dash", line_color="green", 
                     annotation_text=f"Avg Female Height (~{avg_height}cm)")
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            showlegend=False
        )
        
        return fig
    except Exception as e:
        print(f"Error updating height distribution: {e}")
        return go.Figure().update_layout(title="Error loading height distribution")

# Callback for sister size distribution
@app.callback(
    Output("sister-size-distribution", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_sister_size_distribution(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        sister_size_stats = stats.get("sister_size_stats", {})
        common_sister_sizes = sister_size_stats.get("common_sister_sizes", {})
        
        if not common_sister_sizes:
            return go.Figure().update_layout(title="No sister size data available")
        
        # Convert to lists for plotting
        sister_sizes = list(common_sister_sizes.keys())
        counts = list(common_sister_sizes.values())
        
        # Create bar chart for the top 15 most common sister sizes
        # Sort by count, then take top 15
        df = pd.DataFrame({'sister_size': sister_sizes, 'count': counts})
        df = df.sort_values('count', ascending=False).head(15)
        
        fig = px.bar(
            df,
            x='sister_size',
            y='count',
            title='Most Common Sister Sizes',
            labels={'sister_size': 'Sister Size', 'count': 'Count'},
            color='count',
            color_continuous_scale='Viridis'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            coloraxis_showscale=False
        )
        
        return fig
    except Exception as e:
        print(f"Error updating sister size distribution: {e}")
        return go.Figure().update_layout(title="Error loading sister size distribution")

# Callback for o-counter by sister size
@app.callback(
    Output("o-counter-by-sister-size", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_o_counter_by_sister_size(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        sister_size_stats = stats.get("sister_size_stats", {})
        original_vs_sister = sister_size_stats.get("original_vs_sister_stats", {})
        top_o_counter_sizes = original_vs_sister.get("top_o_counter_sizes", [])
        
        if not top_o_counter_sizes:
            return go.Figure().update_layout(title="No o-counter by sister size data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(top_o_counter_sizes)
        
        # Sort by o_counter descending
        df = df.sort_values('o_counter', ascending=False).head(10)
        
        # Create bar chart
        fig = px.bar(
            df,
            x='sister_size',
            y='o_counter',
            title='Top Sister Sizes by O-Counter',
            labels={'sister_size': 'Sister Size', 'o_counter': 'O-Counter'},
            color='o_counter',
            color_continuous_scale='Viridis',
            text='count'
        )
        
        # Add text showing the number of performers
        fig.update_traces(
            texttemplate='n=%{text}',
            textposition='outside'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            coloraxis_showscale=False
        )
        
        return fig
    except Exception as e:
        print(f"Error updating o-counter by sister size: {e}")
        return go.Figure().update_layout(title="Error loading o-counter by sister size")

# Callback for volume distribution
@app.callback(
    Output("volume-distribution", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_volume_distribution(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        volume_stats = stats.get("volume_stats", {})
        volume_category_stats = volume_stats.get("volume_category_stats", [])
        
        if not volume_category_stats:
            return go.Figure().update_layout(title="No volume data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(volume_category_stats)
        
        # Define the correct order of volume categories
        volume_order = [
            'Very Small', 'Small', 'Medium-Small', 'Medium', 
            'Medium-Large', 'Large', 'Very Large', 'Extremely Large'
        ]
        
        # Filter to include only categories in our order list
        df = df[df['volume_category'].isin(volume_order)]
        
        # Create bar chart
        fig = px.bar(
            df,
            x='volume_category',
            y='performer_count',
            title='Performer Count by Volume Category',
            labels={'volume_category': 'Volume Category', 'performer_count': 'Performer Count'},
            color='performer_count',
            color_continuous_scale='Viridis',
            category_orders={'volume_category': volume_order}
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            coloraxis_showscale=False
        )
        
        return fig
    except Exception as e:
        print(f"Error updating volume distribution: {e}")
        return go.Figure().update_layout(title="Error loading volume distribution")

# Callback for o-counter by volume
@app.callback(
    Output("o-counter-by-volume", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_o_counter_by_volume(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        volume_stats = stats.get("volume_stats", {})
        volume_category_stats = volume_stats.get("volume_category_stats", [])
        
        if not volume_category_stats:
            return go.Figure().update_layout(title="No volume data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(volume_category_stats)
        
        # Define the correct order of volume categories
        volume_order = [
            'Very Small', 'Small', 'Medium-Small', 'Medium', 
            'Medium-Large', 'Large', 'Very Large', 'Extremely Large'
        ]
        
        # Filter to include only categories in our order list
        df = df[df['volume_category'].isin(volume_order)]
        
        # Create bar chart
        fig = px.bar(
            df,
            x='volume_category',
            y='avg_o_counter',
            title='Average O-Counter by Volume Category',
            labels={'volume_category': 'Volume Category', 'avg_o_counter': 'Average O-Counter'},
            color='avg_o_counter',
            color_continuous_scale='Viridis',
            category_orders={'volume_category': volume_order},
            text='performer_count'
        )
        
        # Add text showing the number of performers
        fig.update_traces(
            texttemplate='n=%{text}',
            textposition='outside'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            coloraxis_showscale=False
        )
        
        return fig
    except Exception as e:
        print(f"Error updating o-counter by volume: {e}")
        return go.Figure().update_layout(title="Error loading o-counter by volume")

# Callback for o-counter rating correlation
@app.callback(
    Output("o-counter-rating-correlation", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_o_counter_rating_correlation(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        rating_correlation = stats.get("rating_o_counter_correlation", {})
        rating_data = rating_correlation.get("rating_o_counter_data", [])
        correlation = rating_correlation.get("correlation", 0)
        
        if not rating_data:
            return go.Figure().update_layout(title="No rating correlation data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(rating_data)
        
        # Create scatter plot
        fig = px.scatter(
            df,
            x='rating100',
            y='o_counter',
            title=f'O-Counter vs Rating (Correlation: {correlation:.3f})',
            labels={'rating100': 'Rating (0-100)', 'o_counter': 'O-Counter'},
            color='favorite',
            color_discrete_map={True: COLORS['danger'], False: COLORS['primary']},
            hover_data=['name', 'measurements'],
            trendline='ols'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            legend_title_text='Favorite'
        )
        
        return fig
    except Exception as e:
        print(f"Error updating o-counter rating correlation: {e}")
        return go.Figure().update_layout(title="Error loading o-counter rating correlation")

# Callback for cup size BMI correlation
@app.callback(
    Output("cup-size-bmi-correlation", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_cup_size_bmi_correlation(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        cup_stats = stats.get("cup_size_stats", {})
        cup_size_dataframe = cup_stats.get("cup_size_dataframe", [])
        
        if not cup_size_dataframe:
            return go.Figure().update_layout(title="No cup size data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(cup_size_dataframe)
        
        # Check if required columns exist
        required_cols = ['cup_numeric', 'bmi']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return go.Figure().update_layout(title=f"Missing columns: {', '.join(missing_cols)}")
        
        # Filter out rows with missing data
        df = df.dropna(subset=required_cols)
        
        # Calculate correlation
        correlation = df['cup_numeric'].corr(df['bmi'])
        
        # Create scatter plot
        fig = px.scatter(
            df,
            x='bmi',
            y='cup_numeric',
            title=f'Cup Size vs BMI (Correlation: {correlation:.3f})',
            labels={'bmi': 'BMI', 'cup_numeric': 'Cup Size Numeric Value'},
            color='favorite',
            color_discrete_map={True: COLORS['danger'], False: COLORS['primary']},
            hover_data=['name', 'cup_size'],
            trendline='ols'
        )
        
        # Add cup size legend on y-axis
        cup_mapping = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J'}
        cup_ticks = list(cup_mapping.keys())
        cup_labels = [cup_mapping.get(t, str(t)) for t in cup_ticks]
        
        fig.update_layout(
            yaxis=dict(
                tickmode='array',
                tickvals=cup_ticks,
                ticktext=cup_labels
            )
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            legend_title_text='Favorite'
        )
        
        return fig
    except Exception as e:
        print(f"Error updating cup size BMI correlation: {e}")
        return go.Figure().update_layout(title="Error loading cup size BMI correlation")

# Callback for cup size height correlation
@app.callback(
    Output("cup-size-height-correlation", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_cup_size_height_correlation(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        cup_stats = stats.get("cup_size_stats", {})
        cup_size_dataframe = cup_stats.get("cup_size_dataframe", [])
        
        if not cup_size_dataframe:
            return go.Figure().update_layout(title="No cup size data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(cup_size_dataframe)
        
        # Check if required columns exist
        required_cols = ['cup_numeric', 'height_cm']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return go.Figure().update_layout(title=f"Missing columns: {', '.join(missing_cols)}")
        
        # Filter out rows with missing data
        df = df.dropna(subset=required_cols)
        
        # Calculate correlation
        correlation = df['cup_numeric'].corr(df['height_cm'])
        
        # Create scatter plot
        fig = px.scatter(
            df,
            x='height_cm',
            y='cup_numeric',
            title=f'Cup Size vs Height (Correlation: {correlation:.3f})',
            labels={'height_cm': 'Height (cm)', 'cup_numeric': 'Cup Size Numeric Value'},
            color='favorite',
            color_discrete_map={True: COLORS['danger'], False: COLORS['primary']},
            hover_data=['name', 'cup_size'],
            trendline='ols'
        )
        
        # Add cup size legend on y-axis
        cup_mapping = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J'}
        cup_ticks = list(cup_mapping.keys())
        cup_labels = [cup_mapping.get(t, str(t)) for t in cup_ticks]
        
        fig.update_layout(
            yaxis=dict(
                tickmode='array',
                tickvals=cup_ticks,
                ticktext=cup_labels
            )
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            legend_title_text='Favorite'
        )
        
        return fig
    except Exception as e:
        print(f"Error updating cup size height correlation: {e}")
        return go.Figure().update_layout(title="Error loading cup size height correlation")

# Callback for cup size weight correlation
@app.callback(
    Output("cup-size-weight-correlation", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_cup_size_weight_correlation(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        cup_stats = stats.get("cup_size_stats", {})
        cup_size_dataframe = cup_stats.get("cup_size_dataframe", [])
        
        if not cup_size_dataframe:
            return go.Figure().update_layout(title="No cup size data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(cup_size_dataframe)
        
        # Check if required columns exist
        required_cols = ['cup_numeric', 'weight']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return go.Figure().update_layout(title=f"Missing columns: {', '.join(missing_cols)}")
        
        # Filter out rows with missing data
        df = df.dropna(subset=required_cols)
        
        # Calculate correlation
        correlation = df['cup_numeric'].corr(df['weight'])
        
        # Create scatter plot
        fig = px.scatter(
            df,
            x='weight',
            y='cup_numeric',
            title=f'Cup Size vs Weight (Correlation: {correlation:.3f})',
            labels={'weight': 'Weight (kg)', 'cup_numeric': 'Cup Size Numeric Value'},
            color='favorite',
            color_discrete_map={True: COLORS['danger'], False: COLORS['primary']},
            hover_data=['name', 'cup_size'],
            trendline='ols'
        )
        
        # Add cup size legend on y-axis
        cup_mapping = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J'}
        cup_ticks = list(cup_mapping.keys())
        cup_labels = [cup_mapping.get(t, str(t)) for t in cup_ticks]
        
        fig.update_layout(
            yaxis=dict(
                tickmode='array',
                tickvals=cup_ticks,
                ticktext=cup_labels
            )
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40),
            legend_title_text='Favorite'
        )
        
        return fig
    except Exception as e:
        print(f"Error updating cup size weight correlation: {e}")
        return go.Figure().update_layout(title="Error loading cup size weight correlation")

# Callback for performer clusters
@app.callback(
    Output("performer-clusters", "figure"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_performer_clusters(stats_json):
    if not stats_json:
        return go.Figure()
    
    try:
        stats = json.loads(stats_json)
        preference_profile = stats.get("preference_profile", {})
        cluster_analysis = preference_profile.get("cluster_analysis", {})
        cluster_centroids = cluster_analysis.get("cluster_centroids", [])
        
        if not cluster_centroids:
            return go.Figure().update_layout(title="No cluster data available")
        
        # Convert centroids to DataFrame
        feature_weights = preference_profile.get("feature_weights", {})
        features = list(feature_weights.keys())
        
        # Create figure for radar chart
        fig = go.Figure()
        
        # Add each cluster as a trace
        for i, centroid in enumerate(cluster_centroids):
            # Normalize centroid values for radar chart (0-1 scale)
            max_vals = [max(abs(c[j]) for c in cluster_centroids) for j in range(len(centroid))]
            normalized_centroid = [centroid[j] / max_vals[j] if max_vals[j] > 0 else 0 for j in range(len(centroid))]
            
            fig.add_trace(go.Scatterpolar(
                r=normalized_centroid,
                theta=features,
                fill='toself',
                name=f'Cluster {i}',
                line_color=px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
            ))
        
        # Update layout
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title='Performer Clusters Profile',
            showlegend=True,
            plot_bgcolor=COLORS['light'],
            paper_bgcolor=COLORS['light'],
            font={'color': COLORS['text']},
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return fig
    except Exception as e:
        print(f"Error updating performer clusters: {e}")
        return go.Figure().update_layout(title="Error loading performer clusters")

# Callback for preference profile
@app.callback(
    Output("preference-profile", "children"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_preference_profile(stats_json):
    if not stats_json:
        return "No data available"
    
    try:
        stats = json.loads(stats_json)
        preference_profile = stats.get("preference_profile", {})
        profile_data = preference_profile.get("preference_profile", {})
        
        if not profile_data:
            return "No preference profile data available"
        
        # Extract data
        total_performers = profile_data.get("total_relevant_performers", 0)
        avg_o_counter = profile_data.get("avg_o_counter", 0)
        avg_rating = profile_data.get("avg_rating", 0)
        most_common_cup_sizes = profile_data.get("most_common_cup_sizes", [])
        
        # Create HTML content
        content = [
            html.Div([
                html.H4("Preference Profile Summary"),
                html.P([
                    html.Strong("Total Relevant Performers: "), f"{total_performers}"
                ]),
                html.P([
                    html.Strong("Average O-Counter: "), f"{avg_o_counter:.2f}"
                ]),
                html.P([
                    html.Strong("Average Rating: "), f"{avg_rating:.1f}/100 ({avg_rating/20:.1f}/5)"
                ])
            ]),
            
            html.Div([
                html.H4("Most Common Cup Sizes"),
                html.Ul([
                    html.Li([
                        html.Strong(f"{item.get('size')}: "), f"{item.get('count')} performers"
                    ]) for item in most_common_cup_sizes
                ])
            ]),
            
            html.Div([
                html.H4("Feature Weights"),
                html.Ul([
                    html.Li([
                        html.Strong(f"{key}: "), f"{value:.1f}"
                    ]) for key, value in preference_profile.get("feature_weights", {}).items()
                ])
            ])
        ]
        
        return content
    except Exception as e:
        print(f"Error updating preference profile: {e}")
        return "Error loading preference profile"

# Callback for top performers by cluster
@app.callback(
    Output("top-performers-by-cluster", "children"),
    Input("stats-data", "children"),
    prevent_initial_call=True
)
def update_top_performers_by_cluster(stats_json):
    if not stats_json:
        return "No data available"
    
    try:
        stats = json.loads(stats_json)
        preference_profile = stats.get("preference_profile", {})
        top_performers = preference_profile.get("top_performers_by_cluster", {})
        
        if not top_performers:
            return "No top performers by cluster data available"
        
        # Create content for each cluster
        cluster_content = []
        
        for cluster_id, performers in top_performers.items():
            if not performers:
                continue
                
            # Create table for this cluster
            table_header = [
                html.Thead(html.Tr([
                    html.Th("Name", style={"textAlign": "center", "backgroundColor": COLORS['primary'], "color": "white"}),
                    html.Th("O-Counter", style={"textAlign": "center", "backgroundColor": COLORS['primary'], "color": "white"}),
                    html.Th("Rating", style={"textAlign": "center", "backgroundColor": COLORS['primary'], "color": "white"})
                ]))
            ]
            
            rows = []
            for i, performer in enumerate(performers):
                row_style = {"backgroundColor": COLORS['light']} if i % 2 else {}
                rows.append(html.Tr([
                    html.Td(performer.get('name', ''), style={"textAlign": "center"}),
                    html.Td(performer.get('o_counter', 0), style={"textAlign": "center"}),
                    html.Td(f"{performer.get('rating100', 0)}/100", style={"textAlign": "center"})
                ], style=row_style))
            
            table_body = [html.Tbody(rows)]
            
            table = html.Table(table_header + table_body, 
                              style={"width": "100%", "border": "1px solid #ddd", "borderCollapse": "collapse"})
            
            # Add cluster section
            cluster_content.append(html.Div([
                html.H4(f"Cluster {cluster_id}", 
                        style={"color": COLORS['primary'], "borderBottom": f"2px solid {COLORS['primary']}"}),
                table
            ], style={"marginBottom": "20px"}))
        
        return cluster_content
    except Exception as e:
        print(f"Error updating top performers by cluster: {e}")
        return "Error loading top performers by cluster"

# Main function to run the app
if __name__ == '__main__':
    # Get port from command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run the Stash Statistics Dashboard')
    parser.add_argument('--port', type=int, default=8050, help='Port number (default: 8050)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Print info
    print(f"Starting Stash Statistics Dashboard on port {args.port}")
    print(f"Open your browser and navigate to http://localhost:{args.port}")
    
    # Run server
    app.run_server(debug=args.debug, port=args.port)
