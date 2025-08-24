from dash import dcc, html
import plotly.graph_objs as go
from django_plotly_dash import DjangoDash
import pandas as pd
from Dashboard.models import RadioMeasurement, ReceivedQualitySignalStrength, ReceivedQualityReadability
import dash_bootstrap_components as dbc
from django.db.models import Avg
import plotly.express as px
from collections import defaultdict

# Initialize the DjangoDash app
app = DjangoDash('Detailed_Analysis')

# Query the RadioMeasurement model for relevant data
measurements = RadioMeasurement.objects.select_related('SignalStrength', 'Readability').all()
# Fetch Signal_Strength_dbm
signal_strength_dbm = RadioMeasurement.objects.select_related('Signal_Strength_dbm','Field_Strength_dbuv_m', 'Measurement_Time').all()




# Process data into a format suitable for display in the heatmap
data_points = []
for measurement in measurements:
    color = None
    # Determine the color based on signal strength and readability
    if measurement.SignalStrength.Signalstrength_description in ['LOUD', 'GOOD'] or\
       measurement.Readability.Readability_description in ['CLEAR', 'READABLE']:
        color = 'green'
    elif measurement.SignalStrength.Signalstrength_description in ['WEAK', 'VERY WEAK'] or \
         measurement.Readability.Readability_description in ['DISTORTED', 'INTERMITTENT']:
        color = 'yellow'
    elif measurement.SignalStrength.Signalstrength_description == 'FADING' or \
         measurement.Readability.Readability_description == 'WITH INTERFERENCE':
        color = 'orange'
    elif measurement.SignalStrength.Signalstrength_description == 'NONE' or \
         measurement.Readability.Readability_description in ['UNREADABLE', 'NONE']:
        color = 'red'

    if color:
        data_points.append({
            'lat': measurement.latitude,
            'lon': measurement.longitude,
            'Signal_Strength_dbm': measurement.Signal_Strength_dbm,
            'color': color,
        })
# Define the legend for the heatmap
legend = html.Div([
    html.H4("Legend:", className="card-title", style={'textAlign': 'left', 'display': 'inline-block' }),
    html.Div([
        html.Div(style={'backgroundColor': 'green', 'borderRadius': '50%', 'width': '20px', 'height': '20px', 'display': 'inline-block'}),
        html.Span("Signal Strength Ratings: LOUD, GOOD; Readability Ratings: CLEAR, READABLE", style={'marginLeft': '10px', 'display': 'inline-block'}),
    ]),
    html.Div([
        html.Div(style={'backgroundColor': 'yellow', 'borderRadius': '50%', 'width': '20px', 'height': '20px', 'display': 'inline-block'}),
        html.Span("Signal Strength Ratings: WEAK, VERY WEAK; Readability Ratings: DISTORTED, INTERMITTENT", style={'marginLeft': '10px', 'display': 'inline-block'}),
    ]),
    html.Div([
        html.Div(style={'backgroundColor': 'orange', 'borderRadius': '50%', 'width': '20px', 'height': '20px', 'display': 'inline-block'}),
        html.Span("Signal Strength Ratings: FADING ; Readability Ratings: WITH INTERFERENCE", style={'marginLeft': '10px', 'display': 'inline-block'}),
    ]),
    html.Div([
        html.Div(style={'backgroundColor': 'red', 'borderRadius': '50%', 'width': '20px', 'height': '20px', 'display': 'inline-block'}),
        html.Span("Signal Strength Ratings: NONE ; Readability Ratings: UNREADABLE, NONE", style={'marginLeft': '10px', 'display': 'inline-block'}),
    ]),
], style={'width': '100%', 'margin': '0 auto', 'textAlign': 'left'})

# Convert data points to pandas DataFrame
df = pd.DataFrame(data_points)

# create dataframe for signal strength and measurement time
df2 = pd.DataFrame(list(signal_strength_dbm.values('Signal_Strength_dbm', 'Field_Strength_dbuv_m' ,'Measurement_Time')))
df_sorted = df2.sort_values('Measurement_Time')

# Query RadioMeasurement model for NPR_Sites related data
# Initialize data structures for aggregation
site_signal_strength = defaultdict(list)
site_readability = defaultdict(list)

# Process each measurement
for measurement in measurements:
    sites = measurement.npr_sites.split(", ")  # Assuming sites are comma-separated
    for site in sites:
        # Aggregate signal strength and readability ratings
        if measurement.SignalStrength:
            site_signal_strength[site].append(measurement.SignalStrength.Signalstrength_no)
        if measurement.Readability:
            site_readability[site].append(measurement.Readability.Readability_no)


# Calculate averages
avg_signal_strength = {site: sum(values)/len(values) for site, values in site_signal_strength.items() if values}
avg_readability = {site: sum(values)/len(values) for site, values in site_readability.items() if values}

# Combine into a single structure for use in app

npr_avg_data =[{
    'npr_site': site,
    'avg_signal_strength': avg_signal_strength.get(site, None),
    'avg_readability': avg_readability.get(site, None)
} for site in set(list(avg_signal_strength.keys()) + list(avg_readability.keys()))]

# Create radar plot
# Prepare data for plotting
npr_sites = [data['npr_site'] for data in npr_avg_data]
avg_signal_strengths = [data['avg_signal_strength'] for data in npr_avg_data]
avg_readabilities = [data['avg_readability'] for data in npr_avg_data]

# Create a new figure for the radar plot
fig = go.Figure()

# Add trace for Average Signal Strength
fig.add_trace(go.Scatterpolar(
    r=avg_signal_strengths,
    theta=npr_sites,
    fill='toself',
    name='Average Signal Strength',
    line_color='blue'
))

# Add trace for Average Readability
fig.add_trace(go.Scatterpolar(
    r=avg_readabilities,
    theta=npr_sites,
    fill='toself',
    name='Average Readability',
    line_color='red'
))

# Update the layout
fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, max(avg_signal_strengths + avg_readabilities)]
        )
    ),
    showlegend=True
)

# create a line chart for signal strength and measurement time
def create_line_chart(df, y_column, chart_name):
    return dbc.Container([
        dbc.Card(
            dcc.Graph(
                id=f'line_chart_{y_column}',
                figure={
                    'data': [
                        go.Scatter(
                            x=df['Measurement_Time'],
                            y=df[y_column],
                            mode='lines+markers',
                            opacity=0.7,
                            marker={
                                'size': 15,
                                'line': {'width': 0.5, 'color': 'white'}
                            },
                            name=chart_name
                        )
                    ],
                    'layout': go.Layout(
                        title=f'<b>{chart_name} vs Time</b>',
                        xaxis={'title': 'Time'},
                        yaxis={'title': chart_name},
                        margin={'l': 40, 'b': 40, 't': 100, 'r': 10},
                        legend={'x': 0, 'y': 1},
                        hovermode='closest',
                        height=500
                    )
                }
            ),
            style={
                'margin-top': '20px',
                'box-shadow': '0 4px 8px 0 rgba(0,0,0,0.2)',
                'transition': '0.3s',
                'border-radius': '5px',
                'background-color': 'white',
                'color': '#212529',
                'padding': '20px',
                'textAlign': 'center',
                'font-family': 'Arial, sans-serif',
                'width': '100%',
                'margin-bottom': '30px',
            })
    ])

# Create separate line charts
signal_strength_line_chart = create_line_chart(df_sorted, 'Signal_Strength_dbm', 'Signal Strength (dbm)')


# Define the data for the heatmap with color conditions
data = [
    go.Scattermapbox(
        lat=df['lat'],
        lon=df['lon'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=14,
            color=df['color'],
            opacity=0.7
        ),
        text='Signal Strength: ' + df['Signal_Strength_dbm'].astype(str),
        hoverinfo='lon+lat+text'
    )
]

# Define the layout for the heatmap
layout = go.Layout(
    mapbox=dict(
        accesstoken='pk.eyJ1Ijoia3lsZWphaW11bmdhbCIsImEiOiJjbG9od3Jyb2swZHNnMnBvMnFuMnRmNTEzIn0.ntHmfeaXtXuNBlNsjfWACg',
        center=dict(
            lat=10.6918,  # Change to your desired center latitude
            lon=-61.2225  # Change to your desired center longitude
        ),
        zoom=7
    ),
    margin=dict(l=0, r=0, t=0, b=0),
    height=800
)

# Add the heatmap to the app layout
app.layout = html.Div([
    dbc.Card([
        html.H4("Dot Distribution of Cellular and Radio Coverage at Sea in Trinidad and Tobago", className="card-title",
                style={
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'color': 'black', }
                ),
        #add legend to the map about what the colors mean
        legend,
        dcc.Graph(
            id='heatmap',
            figure={

                'data': data,
                'layout': layout
            }
        )] ,style={'margin-bottom': '80px',
            'box-shadow': '0 4px 8px 0 rgba(0,0,0,0.2)',
            'transition': '0.3s',
            'border-radius': '5px',  # Rounded borders
            'background-color': 'white',  # Light blue background
            'color': '#212529',  # Dark text
            'padding': '20px',
            'textAlign': 'center',  # Center the text
            'font-family': 'Arial, sans-serif',  # Font style
            'width': '100%',  # Set the width of the content box
            'height': 'auto',
            'margin-left': 'auto',
            'margin-right': 'auto',
            'margin-bottom': '20px',
            }),
        html.Br(),
        signal_strength_line_chart,
        html.Br(),
        dbc.Card([
        html.H4("Radar Plot of Average Signal Strength Rating and Readability Rating at NPR Sites", className="card-title",
                style={
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'color': 'black', }
                ),
        dcc.Graph(
            id='radar_plot',
            figure=fig
        )
            ], style={'margin-bottom': '80px',
                'box-shadow': '0 4px 8px 0 rgba(0,0,0,0.2)',
                'transition': '0.3s',
                'border-radius': '5px',  # Rounded borders
                'background-color': 'white',  # Light blue background
                'color': '#212529',  # Dark text
                'padding': '20px',
                'textAlign': 'center',  # Center the text
                'font-family': 'Arial, sans-serif',  # Font style
                'width': 'auto',  # Set the width of the content box
                'margin-left': 'auto',
                'margin-right': 'auto',
                'margin-bottom': '100px',})
 
])
