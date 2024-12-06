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
df['Shark.common.name'] = df['Shark.common.name'].fillna('Unknown')  # Fill missing shark names
df['Victim.activity'] = df['Victim.activity'].fillna('Unknown')  # Fill missing activities

# Save the original shark name in a separate column
df['Original.shark.name'] = df['Shark.common.name']

# Define the six most common sharks and "Unknown"
main_sharks = [
    "white shark",
    "tiger shark",
    "wobbegong",
    "bull shark",
    "whaler shark",
    "bronze whaler shark",
    "Unknown"
]

# Group other shark species into "Other Sharks" in the Shark.common.name column
df['Shark.common.name'] = df['Shark.common.name'].apply(
    lambda x: x if x in main_sharks else "Other Sharks"
)

# Define color mapping for the legend categories
color_mapping = {
    "white shark": "#D55E00",  
    "tiger shark": "#CC79A7",  
    "wobbegong": "#0072B2",   
    "bull shark": "#F0E442",  
    "whaler shark": "#009E73", 
    "bronze whaler shark": "#56B4E9",  
    "Unknown": "#999999",  
    "Other Sharks": "#E69F00"  
}

# Normalize "Victim.injury" column
df['Victim.injury'] = df['Victim.injury'].replace({'Injured': 'injured', 'injury': 'injured'})



# Mapbox access token (replace with your own)
px.set_mapbox_access_token("pk.eyJ1Ijoiam9zaC1zZCIsImEiOiJjbTQ4cThteXIwMmU0Mmxzamxoc3BpM21kIn0.u5cA7-M_pTVb2j96XC5E8A")

# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1('Shark Incident Geospatial Dashboard'),
            html.Hr(),
            html.P("Explore shark incidents across Australia. Filter by year, provocation, shark species, and activity. Hover over points for details."),
            dcc.Graph(id='month-bar-chart', figure={}),  # Bar chart placeholder for month
            dcc.Graph(id='injury-bar-chart', figure={}),  # Bar chart placeholder for injuries
            html.Div(id='year-range-display'),  # Display for selected years
            html.Div([
                html.Label('Year Range:'),
                dcc.RangeSlider(
                    id='year-slider',
                    min=int(df['Incident.year'].min()),  # Convert to int
                    max=int(df['Incident.year'].max()),  # Convert to int
                    value=[int(df['Incident.year'].min()), int(df['Incident.year'].max())],  # Convert to int
                    marks={
                        int(df['Incident.year'].min()): str(df['Incident.year'].min()),
                        int(df['Incident.year'].max()): str(df['Incident.year'].max())
                    },
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ]),

            html.Br(),
            html.Label('Provoked/Unprovoked:'),
            dcc.Dropdown(
                id='provoked-dropdown',
                options=[{'label': prov, 'value': prov} for prov in df['Provoked/unprovoked'].unique()],
                value=[],
                multi=True
            ),
            html.Br(),
            html.Label('Shark Species:'),
            dcc.Dropdown(
                id='shark-dropdown',
                options=[{'label': shark, 'value': shark} for shark in sorted(df['Shark.common.name'].unique())],
                value=[],
                multi=True
            ),
            html.Br(),
            html.Label('Victim Activity:'),
            dcc.Dropdown(
                id='activity-dropdown',
                options=[{'label': act, 'value': act} for act in sorted(df['Victim.activity'].unique())],
                value=[],
                multi=True
            )
        ], width=3),
        dbc.Col([
            dcc.Graph(id='map-graph', figure={})  # Main map placeholder
        ], width=9)
    ])
], fluid=True)


# Callback for the bar chart and map updates
@app.callback(
    [Output('month-bar-chart', 'figure'),
     Output('map-graph', 'figure'),
     Output('injury-bar-chart', 'figure')],  # Add the new output for the injury bar chart
    Input('year-slider', 'value'),
    Input('provoked-dropdown', 'value'),
    Input('shark-dropdown', 'value'),
    Input('activity-dropdown', 'value')
)
def update_graphs(year_range, provoked_values, shark_values, activity_values):
    # Filter data based on the inputs
    filtered_df = df[(df['Incident.year'] >= year_range[0]) & (df['Incident.year'] <= year_range[1])]

    if provoked_values:
        filtered_df = filtered_df[filtered_df['Provoked/unprovoked'].isin(provoked_values)]

    if shark_values:
        filtered_df = filtered_df[filtered_df['Shark.common.name'].isin(shark_values)]

    if activity_values:
        filtered_df = filtered_df[filtered_df['Victim.activity'].isin(activity_values)]

    # Bar chart: Incidents per month
    month_counts = filtered_df['Incident.month'].value_counts().sort_index()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_bar_chart = px.bar(
        x=month_names,
        y=[month_counts.get(i, 0) for i in range(1, 13)],
        labels={'x': 'Month', 'y': 'Number of Incidents'},
        title='Shark Incidents by Month'
    )

    # Bar chart: Victim injury counts
    injury_counts = filtered_df['Victim.injury'].value_counts()
    injury_bar_chart = px.bar(
        x=injury_counts.index,
        y=injury_counts.values,
        labels={'x': 'Victim Injury', 'y': 'Number of Incidents'},
        title='Shark Incidents by Victim Injury'
    )

    # Map chart
    map_chart = px.scatter_mapbox(
        filtered_df,
        lat='Latitude',
        lon='Longitude',
        color='Shark.common.name',  # Grouped categories for the legend
        color_discrete_map=color_mapping,  # Apply the custom color mapping
        hover_name='Location',
        hover_data={
            'Original.shark.name': True,  # Display the original shark name
            'Shark.common.name': False,  # Do not display the grouped name in the tooltip
            'Victim.activity': True,
            'Provoked/unprovoked': True,
            'Incident.year': True,
            'Location': True
        },
        zoom=3.7,
        center={"lat": -25.2744, "lon": 133.7751},
        height=1200
    )
    map_chart.update_layout(mapbox_style="light", title="Shark Incidents in Australia")

    return month_bar_chart, map_chart, injury_bar_chart  # Return the new injury bar chart


if __name__ == '__main__':
    app.run_server(debug=True, port=8053)
