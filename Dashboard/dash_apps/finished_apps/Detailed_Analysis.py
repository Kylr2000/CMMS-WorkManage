from django.db.models import Avg, Count
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import base64, io
import plotly.express as px
import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import geopandas as gpd
from django.shortcuts import render
from django.core.serializers import serialize
from Dashboard.models import RadioMeasurement, NetworkPointofReception, ReceivedQualitySignalStrength, ReceivedQualityReadability, CellularMeasurement, CellSite, Operator, NetworkTechnology
from collections import defaultdict
from django.db.models import Max, Min
from datetime import datetime as dt
from django.db.models import F
from django.db.models import Q
from datetime import datetime
from django.db import models
import matplotlib.pyplot as plt
from django.db.models import FloatField
from django.db.models.functions import Power
from Dashboard.models import Transmitter
from plotly.graph_objs import Figure, Scatter
from django.db.models.functions import ExtractHour
import numpy as np
from django.db.models.functions import Cast, Substr
from django.db.models import CharField, IntegerField


external_stylesheets = [dbc.themes.BOOTSTRAP, '/static/css/print.css']

# Initialize the DjangoDash app
app = DjangoDash('Detailed_Analysis', external_stylesheets=external_stylesheets)
# Get unique network technologies and cell sites for dropdown options
network_technologies = NetworkTechnology.objects.values_list('Technology_name', flat=True).distinct()
cell_sites = CellSite.objects.values_list('SiteName', flat=True).distinct()


mapbox_access_token = 'pk.eyJ1Ijoia3lsZWphaW11bmdhbCIsImEiOiJjbG9od3Jyb2swZHNnMnBvMnFuMnRmNTEzIn0.ntHmfeaXtXuNBlNsjfWACg'  # Replace with your Mapbox access token
# Query the CellularMeasurement model to get the range of available dates
date_range = CellularMeasurement.objects.aggregate(Min('Date'), Max('Date'))
# Create the layout for the app



# Callback for updating map based on the data type selected
@app.callback(
    [Output('map', 'figure'),
     Output('map-title', 'children')],
    [Input('data-type', 'value')]
)

# Function to update the map based on the data type selected
# Function to update the map based on the data type selected
def update_map(data_type):
    # If the data type is radio
    if 'radio' in data_type:
        # Query the RadioMeasurement model for relevant data
        measurements = RadioMeasurement.objects.select_related('SignalStrength', 'Readability').all()

        # Create a dataframe from the measurements
        df = pd.DataFrame(list(measurements.values('latitude', 'longitude', 'SignalStrength__Signalstrength_no', 'Readability__Readability_no', 'SignalStrength__Signalstrength_description', 'Readability__Readability_description')))
        # Create a map using plotly
        fig = px.scatter_mapbox(df, lat='latitude', lon='longitude', hover_data=['SignalStrength__Signalstrength_description', 'Readability__Readability_description'], color='SignalStrength__Signalstrength_no', size='Readability__Readability_no',
                        color_continuous_scale=["black", "red", "orange", "yellow", "blue", "green"],
                        labels={'SignalStrength__Signalstrength_description': 'Signal Reception', 
                                'Readability__Readability_description': 'Readability',
                                'Readability__Readability_no': 'Readability Measurement',
                                'SignalStrength__Signalstrength_no': 'Signal Reception Measurement'},)
        # Update the map layout
        fig.update_layout(
                mapbox={
                'accesstoken': mapbox_access_token,
                'style': "open-street-map",
                'center': {'lat': 10.6918, 'lon': -61.2225},
                'zoom': 7,  
                },
                margin={'l':0, 'r':0, 't':0, 'b':0}
            )
        map_title = "Colour coded map of Signal Reception and Readability for VHF Radio in Trinidad and Tobago"
        # Return the map
        return fig, map_title

    # If the data type is cellular
    if 'cellular' in data_type:
        # Query the CellularMeasurement model for relevant data
        cellular_measurements = CellularMeasurement.objects.all().select_related('Cell_Site')
        # Create a dataframe from the cellular measurements
        df = pd.DataFrame(list(CellularMeasurement.objects.all().values('Latitude', 'Longitude', 'RSSI', 'RSCP', 'Cell_Site__Operator__Operator_Name', 'Cell_Site__Network_Technology__Technology_name')))
        # Create a new column 'Signal_Strength' that contains the appropriate signal strength measure based on the network technology
        df['Signal_Strength'] = df.apply(lambda row: row['RSCP'] if row['Cell_Site__Network_Technology__Technology_name'] == '3G' else row['RSSI'], axis=1)
        df['size']=10
        # Create a map using plotly
        fig = px.scatter_mapbox(df, lat='Latitude', lon='Longitude', hover_data=['Cell_Site__Operator__Operator_Name', 'Cell_Site__Network_Technology__Technology_name'], color='Signal_Strength', size='size',
                                color_continuous_scale=["red", "yellow", "green"],
                                labels={'Cell_Site__Operator__Operator_Name': 'Operator', 
                                'Cell_Site__Network_Technology__Technology_name': 'Network Technology',
                                'Signal_Strength': 'Signal Strength (dBm)'},)

        # Update the map layout
        fig.update_layout(
                mapbox={
                'accesstoken': mapbox_access_token,
                'style': "open-street-map",
                'center': {'lat': 10.6918, 'lon': -61.2225},
                'zoom': 7,  
                },
                margin={'l':0, 'r':0, 't':0, 'b':0}
            )
        map_title = "Colour coded map of Signal Strength for Cellular Networks in Trinidad and Tobago"
        # Return the map
        return fig, map_title

# Radar plot for signal strength and readability
@app.callback(
    Output('radar-plot', 'figure'),
    [Input('data-type', 'value')]
)

def update_radar_plot(data_type):

    if 'radio' in data_type:
        # Query the RadioMeasurement model for relevant data
        measurements = RadioMeasurement.objects.select_related('SignalStrength', 'Readability').all()

        # Initialize data structures for aggregation
        site_signal_strength = defaultdict(list)
        site_readability = defaultdict(list)
        processed_sites = set()  # Keep track of processed sites

        # Process each measurement
        for measurement in measurements:
            sites = measurement.npr_sites.split(",")  # Assuming sites are comma-separated
            for site in sites:
                site = site.strip()  # Remove any leading or trailing whitespace
                if site not in processed_sites:
                    processed_sites.add(site)  # Mark site as processed
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

        return fig
    

# # Callback to update the network type hourly comparison graph
# @app.callback(
#     Output('networktype-hourlycomp-graph', 'figure'),
#     [Input('network-technology-dropdown', 'value'),
#      Input('my-date-picker', 'date'),
#      Input('cell-site-dropdown', 'value')]
# )

# def update_networktype_hourlycomp_graph(selected_network_technologies, date, selected_cell_site):
#     figure = Figure()
#     for network_technology in selected_network_technologies:
#         if network_technology == '3G':
#             filtered_data = CellularMeasurement.objects.exclude(
#                 RSCP=0,
#             ).filter(
#                 RSCP__isnull=False,
#                 Cell_Site__SiteName=selected_cell_site,
#                 Date=date
#             )
#             readings = filtered_data.values("Time", "RSCP").order_by('Time')
#             print(readings)
#         elif network_technology == '4G':
#             filtered_data = CellularMeasurement.objects.exclude(
#                 RSSI=0,
#             ).filter(
#                 RSSI__isnull=False,
#                 Cell_Site__SiteName=selected_cell_site,
#                 Date=date
#             )
#             readings = filtered_data.values("Time", "RSSI").order_by('Time')
#             print(readings)

#         figure.add_trace(Scatter(x=[item['Time'] for item in readings], y=[item['RSCP' if network_technology == '3G' else 'RSSI'] for item in readings], mode='lines', name=network_technology))
#     return figure
# treemap for Signal Strength in VHF Radio by Transmitter
# Query the RadioMeasurement model for relevant data
radio_measurements = RadioMeasurement.objects.all().select_related('SignalStrength', 'Readability')
#Get the associated npr site for each measurement
treemap_data = []
for rm in radio_measurements:
    treemap_data.append({
        'Measurement_Date': rm.Measurement_Date,
        'Measurement_Time': rm.Measurement_Time,
        'latitude': rm.latitude,
        'longitude': rm.longitude,
        'Field_Strength_dbuv_m': rm.Field_Strength_dbuv_m,
        'Signal_Strength_dbm': rm.Signal_Strength_dbm,
        'DSC_Response': rm.DSC_Response,
        'Tx_site': rm.Tx_site,
        'Rx_site': rm.Rx_site,
        'SignalStrength_description': rm.SignalStrength.Signalstrength_description if rm.SignalStrength else None,
        'Readability_description': rm.Readability.Readability_description if rm.Readability else None,
        'ReceivedQuality_Description': rm.ReceivedQuality_Description,
        'npr_sites': rm.npr_sites if rm.npr_sites else None,

    })

# Create a dataframe from the radio measurement
df = pd.DataFrame(treemap_data)

#split string for npr_sites
df = df.assign(npr_sites=df['npr_sites'].str.split(',')).explode('npr_sites')

# Strip whitespace and convert to lowercase
df['npr_sites'] = df['npr_sites'].str.strip().str.lower()

df_grouped = df.groupby('npr_sites').agg({
    'Field_Strength_dbuv_m': 'mean',
    'Signal_Strength_dbm': 'mean',
}).reset_index()


fig = px.treemap(df_grouped, path=[px.Constant("Trinidad and Tobago"), 'npr_sites'], values='Field_Strength_dbuv_m',
                  color='Signal_Strength_dbm',
                  color_continuous_scale='RdBu',
                  color_continuous_midpoint=np.average(df_grouped['Signal_Strength_dbm'], weights=df_grouped['Field_Strength_dbuv_m']))
fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

#Marginal Distribution plots
#Select related Cell Measurement
measurements = CellularMeasurement.objects.select_related('Cell_Site__Operator', 'Cell_Site__Network_Technology').all()

data = [{
    'Operator': m.Cell_Site.Operator.Operator_Name if m.Cell_Site.Operator else None,
    'Technology': m.Cell_Site.Network_Technology.Technology_name if m.Cell_Site.Network_Technology else None,
    'Date': m.Date,
    'RSSI': m.RSSI,
    'RSCP': m.RSCP,
} for m in measurements]

df = pd.DataFrame(data)
print(df)

df_rssi = df[df['Technology'] == '4G']
print(df_rssi)
df_rscp = df[df['Technology'] == '3G']
print(df_rscp)

# fig_rssi = px.histogram(df_rssi, x="RSSI", title="Distribution of RSSI Values for [Technology Name]",
#                         labels={"RSSI": "RSSI (dBm)"})
# fig_rssi.show()

# fig_rscp = px.histogram(df_rscp, x="RSCP", title="Distribution of RSCP Values for [Technology Name]",
#                         labels={"RSCP": "RSCP (dBm)"})
# fig_rscp.show()

df_combined = pd.concat([
    df_rssi.rename(columns={"RSSI": "Signal_Value"}).assign(Technology_Metric="3G"),
    df_rscp.rename(columns={"RSCP": "Signal_Value"}).assign(Technology_Metric="4G")
])

fig_combined = px.histogram(df_combined, x="Signal_Value", color="Technology_Metric", 
                   facet_col="Technology_Metric", barmode='overlay', marginal="box",
                   title="Distribution of Signal Values by Network Technology",
                   labels={"Signal_Value": "Signal Value (dBm)"})
    
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Detailed Analysis Dashboard"),
            html.H6( """This dashboard provides detailed analysis of signal strength and readability for radio and cellular networks in Trinidad and Tobago. 
                    It includes maps, radar plots, treemaps and Marginal distibution plots to visualize and analyze the data.
                    To know more about the scale used in the dashboard for rating/classifying the VHF Radio and Cellular Signal Strengths, please visit the FAQ page at the bottom of
                    the Sidebar.
        
                    """

                ),
            ]),
    ], align='end', style={'margin-top': '20px', 'margin-bottom': '20px'}),

    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H3(id='map-title', style={'text-align': 'left'}),
                ]),
                dbc.Col([
                    html.H6("Please choose the data type to display on the map from the dropdown below:", style={'text-align': 'left', 'color': 'black', 'fontSize': 15}),
                    # Dropdown to select the data type
                    dcc.Dropdown(
                        id='data-type',
                        options=[
                            {'label': 'Radio', 'value': 'radio'},
                            {'label': 'Cellular', 'value': 'cellular'}
                        ],
                        value='radio',
                    ),
                ]),
            ], style={'margin-bottom': '10px'}),
            html.Div(
                children=[
                    html.P(
                        """
                        The map below displays the signal strength and readability for radio and cellular networks in Trinidad and Tobago.
                        The map displays signal reception as a colour gradient and readability as the size of the markers for VHF Radio.
                        For cellular networks, the map displays signal strength as a colour gradient for 3G and 4G networks.
                        The map provides a visual representation of the signal strength and readability across the country.

                        """
                    ),
                ],
                style={'margin-bottom': '20px'}
            ),
                    # Div to hold the map
                    html.Div([
                        dcc.Graph(id='map')
                    ], style={'margin-bottom': '20px'}),

            dbc.Row([
                dbc.Col([
                    html.P('The radar plot below displays the average signal strength and readability for VHF Radio networks in Trinidad and Tobago. The plot provides a visual representation of the average signal strength and readability for each network point of reception (NPR) site.'),
                ]),
            ]),
            dbc.Row([
                dbc.Col([
                    # Div to hold the radar plot
                    html.Div([
                        dcc.Graph(id='radar-plot')
                    ]),
                ]),
            ]),
        ]),
    ),
    html.Br(),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H3("Average VHF Radio Signal Strength measured per Coast Station")
                        ]),
                        dbc.Col([
                            html.P("The treemaps below display the average VHF Radio Signal Strength per Coast Station."),
                        ]),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            # Div to hold the RSSI treemap
                            html.Div([
                                dcc.Graph(figure=fig)
                            ]),
                        ]),
                    ], style={'margin-bottom': '20px'}),
                ]),
            ),
        ),
    ]),
    html.Br(),
        dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H3("Marignal Distribution Plot of Signal Strength across 3G and 4G Networks in Trinidad and Tobago")
                        ]),
                        dbc.Col([
                            html.P("The purpose of this graph is to visually compare the distribution of signal values (RSSI and RSCP) for different network technologies, highlighting how each technology performs in terms of signal strength"),
                        ]),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            # Div to hold the RSSI treemap
                            html.Div([
                                dcc.Graph(figure=fig_combined)
                            ]),
                        ]),
                    ], style={'margin-bottom': '20px'}),
                ]),
            ),
        ),
    ]),

])



