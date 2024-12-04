import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

# Load and preprocess data
df = pd.read_excel('dataset/Australian Shark-Incident Database Public Version.xlsx')
df = df.dropna(subset=['Latitude', 'Longitude'])
df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
df = df.dropna(subset=['Latitude', 'Longitude'])
df['Provoked/unprovoked'] = df['Provoked/unprovoked'].fillna('Unknown').str.capitalize()
df['Shark.common.name'] = df['Shark.common.name'].fillna('Unknown') # Fill missing shark names
df['Victim.activity'] = df['Victim.activity'].fillna('Unknown') # Fill missing activities

# Mapbox access token (REPLACE with your own)
px.set_mapbox_access_token("pk.eyJ1Ijoiam9zaC1zZCIsImEiOiJjbTQ4cThteXIwMmU0Mmxzamxoc3BpM21kIn0.u5cA7-M_pTVb2j96XC5E8A")

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1('Shark Incident Geospatial Dashboard'),
            html.Hr(),
            html.P("Explore shark incidents across Australia. Filter by year, provocation, shark species, and activity. Hover over points for details."), # Added introductory text
            html.Div(id='year-range-display'), # Display for selected years
            dcc.RangeSlider(
                id='year-slider',
                min=df['Incident.year'].min(),
                max=df['Incident.year'].max(),
                value=[df['Incident.year'].min(), df['Incident.year'].max()],
                marks={year: str(year) if year == df['Incident.year'].min() or year == df['Incident.year'].max() else ''
                       for year in range(int(df['Incident.year'].min()), int(df['Incident.year'].max()) + 1)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            html.Br(),
            html.Label('Provoked/Unprovoked:'),
            dcc.Dropdown(
                id='provoked-dropdown',
                options=[{'label': prov, 'value': prov} for prov in df['Provoked/unprovoked'].unique()],
                value=[],  # Start with all selected by default
                multi=True
            ),
            html.Br(),
            html.Label('Shark Species:'),
            dcc.Dropdown(
                id='shark-dropdown',
                options=[{'label': shark, 'value': shark} for shark in sorted(df['Shark.common.name'].unique())],  # Sorted options
                value=[], # No default species selected; starts with all data. This line is not needed with multi=True
                multi=True
            ),
            html.Br(),
            html.Label('Victim Activity:'),
            dcc.Dropdown(
                id='activity-dropdown',
                options=[{'label': act, 'value': act} for act in sorted(df['Victim.activity'].unique())],  # Sorted options
                value=[],
                multi=True # Allow multiple selections
            )
        ], width=3),
        dbc.Col([
            dcc.Graph(id='map-graph', figure={}) 
        ], width=9)
    ])
], fluid=True)

# Callback for dynamic year display
@app.callback(
    Output('year-range-display', 'children'),
    Input('year-slider', 'value')
)

def display_year_range(year_range):
    return f"Selected "

# Callback
@app.callback(
    Output('map-graph', 'figure'),
    Input('year-slider', 'value'),
    Input('provoked-dropdown', 'value'),  # Changed to dropdown
    Input('shark-dropdown', 'value'),
    Input('activity-dropdown', 'value')
)
def update_map(year_range, provoked_values, shark_values, activity_values):
    filtered_df = df[(df['Incident.year'] >= year_range[0]) & (df['Incident.year'] <= year_range[1])]

    # Provoked/Unprovoked filtering (now using dropdown)
    if provoked_values:  # Check if any provoked values are selected
        filtered_df = filtered_df[filtered_df['Provoked/unprovoked'].isin(provoked_values)]

    if shark_values:
        filtered_df = filtered_df[filtered_df['Shark.common.name'].isin(shark_values)]

    if activity_values:
        filtered_df = filtered_df[filtered_df['Victim.activity'].isin(activity_values)]

    fig = px.scatter_mapbox(filtered_df,
                            lat='Latitude',
                            lon='Longitude',
                            color='Shark.common.name',
                            hover_name='Location',
                           hover_data = ['Shark.common.name', 'Victim.activity','Provoked/unprovoked', "Incident.year"], # Include more data in the hover
                            zoom=3.5,
                            center={"lat": -25.2744, "lon": 133.7751}, # Center map on Australia
                            height=800)
    fig.update_layout(mapbox_style="light", title="Shark Incidents in Australia")
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=8053)