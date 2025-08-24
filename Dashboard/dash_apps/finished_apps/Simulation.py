from django.db.models import Avg, Count
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import base64, io
import plotly.express as px
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import geopandas as gpd
from django.shortcuts import render
from django.core.serializers import serialize
from Dashboard.models import RadioMeasurement, NetworkPointofReception, ReceivedQualitySignalStrength, ReceivedQualityReadability, CellularMeasurement, CellSite, Operator, NetworkTechnology
import requests
import json
import plotly.graph_objs as go
from plotly.graph_objects import Figure, Scattermapbox
import dash
from math import radians, cos, sin, asin, sqrt
from Dashboard.models import Transmitter
import math
from shapely.geometry import Point, Polygon
from pykml import parser
import random
from django.utils import timezone
import folium
import branca.colormap as cm
from dash import dash_table, callback_context





external_stylesheets = [dbc.themes.BOOTSTRAP, '/static/css/print.css']

app = DjangoDash('Simulation', external_stylesheets=external_stylesheets)

# create a coverage map that uses data imported from a csv file
# the csv file contains the coordinates of the network points of reception
# the coordinates are used to create a geopandas dataframe
# the geopandas dataframe is used to create a map using plotly
# the map is displayed in the dashboard
# the map is used to simulate the coverage of the network
# the map is used to simulate the signal strength and readability of the network
# the map is used to simulate the network technology used in the network
# the map is used to simulate the operator of the network
# the map is used to simulate the cell site of the network
# the map is used to simulate the radio measurements of the network
# the map is used to simulate the cellular measurements of the network

mapbox_access_token = 'pk.eyJ1Ijoia3lsZWphaW11bmdhbCIsImEiOiJjbG9od3Jyb2swZHNnMnBvMnFuMnRmNTEzIn0.ntHmfeaXtXuNBlNsjfWACg'  # Replace with your Mapbox access token


app.layout = dbc.Container([
    # dcc.Graph(id='map-graph'),
    # Real data table container
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                html.H3('Real Data Table'),
            ]),
            dbc.Row([
                dbc.Col([
                    dash_table.DataTable(
                        id='real-data-table',
                        columns=[{"name": i, "id": i} for i in ['latitude', 'longitude', 'Signal_Strength_dbm']],
                        data=[],  # initially empty
                        editable=True,
                        row_deletable=True,
                        style_table={'height': '300px', 'overflowY': 'auto'}
                    )
                ], id='real-data-table-container'),
            ]),
            dbc.Row([
                html.H3('Simulation Data Table'),
            ]),
            dbc.Row([
                # Mock data table container
                dbc.Col([
                    dash_table.DataTable(
                        id='mock-data-table',
                        columns=[{"name": i, "id": i} for i in ['latitude', 'longitude', 'Signal_Strength_dbm']],
                        data=[],  # initially empty
                        editable=True,
                        row_deletable=True,
                        style_table={'height': '300px', 'overflowY': 'auto'}
                    )
                ], id='mock-data-table-container'),
            ]),
            # Add new mock data to the table
            dbc.Row([
                dbc.Col([
                    dcc.Input(id='mock-data-lat', type='number', placeholder='Latitude'),
                    dcc.Input(id='mock-data-lon', type='number', placeholder='Longitude'),
                    dcc.Input(id='mock-data-signal', type='number', placeholder='Signal Strength (dBm)'),
                    dbc.Button('Add New Mock Data', id='add-mock-data', n_clicks=0, color='primary', style={'background-color': '#007bff', 'border': 'none', 'color': 'white', 'text-align': 'center', 'display': 'inline-block', 'font-size': '16px', 'margin': '4px 2px', 'cursor': 'pointer', 'padding': '10px'}),
                ]),
            ]),
        ]),
    style={'margin-bottom': '10px'}),
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                        html.H1("VHF Radio Simulation Coverage Map"),
                        html.H6("Drag and Drop or Select your .csv and GeoJSON files to simulate the LoS coverage of the VHF radio network from your own data samples and compare it to the measurements taken from our measurement team"),
                ]),
            ]),
            dbc.Row([
                dbc.Col([
                        dcc.DatePickerSingle(
                        id='date-picker',
                        date='2023-08-24'
                        ),
                ]),
            ]),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        dcc.Upload(
                            id='upload-geojson',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select GeoJSON File')
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            },
                            # Allow only one file to be uploaded
                            multiple=False,
                            # Filename
                            filename=''
                        ),
                    ], id='upload-geojson-area', style={'display': 'block'}),
                ]),
            ]),
            dbc.Row([
                dbc.Col([
                        html.Div([
                            dcc.Upload(
                                id = 'upload-data',
                                children = html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select CSV Files')
                                ]),
                                style = {
                                    'width': '100%',
                                    'height': '500%',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px'
                                },
                                # Allow multiple files to be uploaded
                                multiple = True,
                                # Filename
                                filename = ''
                            ),
                        ], id='upload-area', style={'width': '100%', 'height': '800px', 'margin-bottom': '10px'}),
                        html.Iframe(id='coverage-map', style={'border': 'none', 'width': '1050%', 'height': '1000%'}),
                ],width=12, lg=100, xl=100),
            ]),

        ]),
        ),
    html.Br(),

    # Add more interactive components here
],)



# @app.callback(
#     Output('map-graph', 'figure'),
#     [Input('map-graph', 'id')]  # This is a dummy input to trigger the callback when the app starts
# )
# def update_map(_):
#     response = requests.get('http://127.0.0.1:8000/coverage_los')  # Update with correct URL
#     data = response.json()['data']

#     # Create a scattermapbox trace for each transmitter
#     traces = [
#         go.Scattermapbox(
#             lat=[transmitter['latitude']],
#             lon=[transmitter['longitude']],
#             mode='markers',
#             marker=go.scattermapbox.Marker(
#                 size=transmitter['coverage'],  # Use coverage as marker size
#                 sizemode='area',
#                 sizeref=0.1,  # Adjust this value to change the marker size
#                 sizemin=4,
#                 color='blue',
#                 opacity=0.4
#             ),
#             text=[transmitter['name']],
#             hoverinfo='text'
#         )
#         for transmitter in data
#     ]

#     layout = go.Layout(
#         autosize=True,
#         hovermode='closest',
#         mapbox=dict(
#             accesstoken=mapbox_access_token,
#             bearing=0,
#             center=dict(
#                 lat=10.6918,  # Update with the latitude of the center of your map
#                 lon=-61.2225  # Update with the longitude of the center of your map
#             ),
#             pitch=0,
#             zoom=7  # Update with the initial zoom level of your map
#         ),
#     )

#     return {'data': traces, 'layout': layout}




@app.callback(
    Output('output-coverage', 'children'),
    [Input('submit-val', 'n_clicks')],
    [State('input-lat', 'value'), State('input-lon', 'value')]

)
def check_LoSCoverage(n_clicks, lat, lon):
    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance in kilometers between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r

    def is_in_coverage_area(lat, lon):
        for transmitter in Transmitter.objects.all():
            coverage = 2.5 * (math.sqrt(transmitter.height) + math.sqrt(1))
            distance = haversine(lon, lat, transmitter.longitude, transmitter.latitude)
            if distance <= coverage:
                return True
        return False

    if n_clicks > 0:
        if lat is None or lon is None:
            return 'Please enter a valid latitude and longitude coordinate'
        else:
            in_coverage_area = is_in_coverage_area(lat, lon)
            if in_coverage_area:
                return 'The receiver is in the coverage area'
            else:
                return 'The receiver is not in the coverage area'
    else:
        return 'Error Has Occured'
    


#create a coverage map that compares Simulated values to real values












# app.layout = html.Div([
#     html.H1("VHF Radio Simulation Coverage Map"),
#     html.P("Drag and Drop or Select your .csv files to simulate the coverage of the VHF radio network from your own data samples"),
#     dcc.Upload(
#         id = 'upload-data',
#         children = html.Div([
#             'Drag and Drop or ',
#             html.A('Select Files')
#         ]),
#         style = {
#             'width': '100%',
#             'height': '60px',
#             'lineHeight': '60px',
#             'borderWidth': '1px',
#             'borderStyle': 'dashed',
#             'borderRadius': '5px',
#             'textAlign': 'center',
#             'margin': '10px'
#         },
#         # Allow multiple files to be uploaded
#         multiple = True,
#         # Filename
#         filename = ''
#     ),
#     dcc.Checklist(
#         id = 'apply-weather-effects',
#         options = [{'label': 'Apply Weather Effects', 'value': 'apply'}],
#         value = ['']
#     ),
#     html.Div(id = 'output-data-upload'),
# ])

# @app.callback(Output('output-data-upload', 'children'),
#               [Input('upload-data', 'contents'),
#                Input('apply-weather-effects', 'value')],
#               [State('upload-data', 'filename'),
#                State('upload-data', 'last_modified')])

    
# def update_output(list_of_contents,  apply_weather_effects, list_of_names, list_of_dates):
#     if list_of_contents is not None:
#         children = [
#             parse_contents(c, n, d, apply_weather_effects) for c, n, d in
#             zip(list_of_contents, list_of_names, list_of_dates)]
#         return children

# def apply_weather_effects_to_df(df):
#     # Add weather effects to the signal strength
#     df['signal_strength'] = df['signal_strength'] + 10
#     return df



# def parse_contents(contents, name, date, apply_weather_effects):
#     content_type, content_string = contents.split(',')

#     decoded = base64.b64decode(content_string)
#     try:
#         if 'csv' in name:
#             # Assume that the user uploaded a CSV file
#             df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

#             df['abs_signal_strength'] = df['signal_strength'].abs()

#             if apply_weather_effects and 'apply' in apply_weather_effects:
#                 df = apply_weather_effects_to_df(df)

#             # Create a scatter mapbox plot
#             fig = px.scatter_mapbox(df, lat="latitude", lon="longitude", color="signal_strength",
#                                 size="abs_signal_strength", color_continuous_scale=["blue", "green", "yellow", "red"],
#                                 size_max=15, zoom=10)

#             # Set the mapbox access token
            
#             fig.update_layout(
#                 mapbox={
#                 'accesstoken': mapbox_access_token,
#                 'style': "open-street-map",
#                 'center': {'lat': 10.6918, 'lon': -61.2225},
#                 'zoom': 7,  
#                 },
#                 margin={'l':0, 'r':0, 't':0, 'b':0}
#             )

#             return dcc.Graph(figure=fig)
#         elif 'kml' in name:
#             # The user uploaded a KML file
#             # Parse the KML data into a Python object
#             kml_obj = parser.fromstring(decoded)

#             # Create a plotly figure
#             fig = Figure()

#             # Add each geometry to the figure
#             for pm in kml_obj.Document.Placemark:
#                 for geom in pm.MultiGeometry.iterchildren():
#                     if geom.tag.endswith('LineString'):
#                         coordinates = geom.coordinates.pyval.split()
#                         lat, lon = zip(*[map(float, c.split(',')[:2]) for c in coordinates])
#                         fig.add_trace(Scattermapbox(
#                             lat=lat,
#                             lon=lon,
#                             mode='lines',
#                         ))

#             # Set the mapbox access token
#             fig.update_layout(
#                 mapbox={
#                     'accesstoken': mapbox_access_token,
#                     'style': "open-street-map",
#                     'center': {'lat': 10.6918, 'lon': -61.2225},
#                     'zoom': 7,  
#                 },
#                 margin={'l':0, 'r':0, 't':0, 'b':0}
#             )

#             return dcc.Graph(figure=fig)

#     except Exception as e:
#         print(e)
#         return html.Div([
#             'There was an error processing this file.'
#         ])
    
@app.callback(
    Output('mock-data-table', 'data'),
    [Input('upload-data', 'contents'),
     Input('add-mock-data', 'n_clicks'),
     Input('mock-data-lat', 'value'),
     Input('mock-data-lon', 'value'),
     Input('mock-data-signal', 'value')],
    [State('upload-data', 'filename'),
     State('upload-data', 'last_modified'),
     State('mock-data-table', 'data'),]
)
def update_mock_data_table(list_of_contents, n_clicks, lat, lon, signal, list_of_filenames, last_modified, existing_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'upload-data':
        # Process each file uploaded
        all_data = pd.DataFrame()
        for contents, filename in zip(list_of_contents, list_of_filenames):
            df = parse_contents(contents, filename)
            if df is not None:
                all_data = pd.concat([all_data, df], ignore_index=True)
        return all_data.to_dict('records')

    elif trigger_id == 'add-mock-data' and n_clicks > 0 and lat is not None and lon is not None and signal is not None:
        new_row = pd.DataFrame([{'latitude': lat, 'longitude': lon, 'Signal_Strength_dbm': signal}])
        existing_data_df = pd.DataFrame(existing_data)
        all_data = pd.concat([existing_data_df, new_row], ignore_index=True)
        return all_data.to_dict('records')

    return existing_data

    # Return the data for the mock data table
    

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            return pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return None
    
    
    
@app.callback(
    Output('real-data-table', 'data'),
    [Input('date-picker', 'date')]
)
def update_real_data_table(selected_date):
    if selected_date is None:
        raise dash.exceptions.PreventUpdate

    # Query the RadioMeasurement model for relevant data
    radio_measurements = RadioMeasurement.objects.filter(Measurement_Date=selected_date)
    df_radio = pd.DataFrame(list(radio_measurements.values('latitude', 'longitude', 'Signal_Strength_dbm')))
    print(df_radio)
    real_data = df_radio.to_dict('records')
    
    # Return the data for the real data table
    return real_data

# Modify the callback to update the tables and the map
@app.callback(
    [Output('coverage-map', 'srcDoc')],
    [Input('real-data-table', 'data'), Input('mock-data-table', 'data'), Input('upload-geojson', 'contents')]
)
def update_coverage_map(real_data, mock_data, geojson_content):

    # Convert the table data to dataframes
    df_radio = pd.DataFrame(real_data)
    df_mock = pd.DataFrame(mock_data)
    response = requests.get('http://127.0.0.1:8000/coverage_los')  # Update with correct URL
    data = response.json()['data']


    # Read GeoJSON content
    if geojson_content:
        content_type, content_string = geojson_content.split(',')
        decoded_geojson = base64.b64decode(content_string).decode('utf-8')
        geojson_data = json.loads(decoded_geojson)
    else:
        # If no GeoJSON content is provided, return an empty map
        return ['']

    # Create a map using folium
    m = folium.Map(location=[10.6918, -61.2225], zoom_start=9)
    real_color_scale = cm.LinearColormap(colors=['green', 'white'], vmin=-110, vmax=-40)
    real_color_scale.caption = 'Real Measurements Signal Strength (dBm)'
    mock_color_scale = cm.LinearColormap(colors=['red', 'white'], vmin=-110, vmax=-40)
    mock_color_scale.caption = 'Simulated Measurements Signal Strength (dBm)'

    # Add markers for transmitters
    for transmitter in data:
        folium.Marker(
            location=[transmitter['latitude'], transmitter['longitude']],
            popup=transmitter['name'],
            icon=folium.Icon(color='blue', icon='flag', prefix='fa')
        ).add_to(m)

    # Add real Radio data to the map
    for _, row in df_radio.iterrows():
        folium.Circle(
            location=[row['latitude'], row['longitude']],
            radius=100,
            color=real_color_scale(float(row['Signal_Strength_dbm'])),
            fill=True,
            fill_opacity=0.7,
            popup=str(row['Signal_Strength_dbm']),
        ).add_to(m)

    # Add mock Radio data to the map
    for _, row in df_mock.iterrows():
        folium.Circle(
            location=[row['latitude'], row['longitude']],
            radius=100,
            color=mock_color_scale(float(row['Signal_Strength_dbm'])),
            fill=True,
            fill_opacity=0.5,
            popup=str(row['Signal_Strength_dbm'])
        ).add_to(m)

    # Add GeoJSON layer
    folium.GeoJson(geojson_data, name='Transmitter Locations').add_to(m)

    # Define the legend HTML code
    legend_html = '''
    <div style="position: fixed; 
                top: 50px; left: 50px; width: 120px; height: 110px; 
                border:4px solid grey; z-index:9999; font-size:14px;
                background-color: white;
                ">
        <b>Legend</b> <br>
        <div style="margin: 5px; background-color: blue; width: 10px; height: 10px; display: inline-block;"></div> Transmitter <br>
        <div style="margin: 5px; background-color: green; width: 10px; height: 10px; display: inline-block;"></div> Real Data <br>
        <div style="margin: 5px; background-color: red; width: 10px; height: 10px; display: inline-block;"></div> Mock Data
    </div>
    '''

    # Add the legend to the map
    m.get_root().html.add_child(folium.Element(legend_html))
    m.add_child(real_color_scale)
    m.add_child(mock_color_scale)

    # Return the map
    return [m._repr_html_()]

# Add a callback to update the display of the upload area and the map
@app.callback(
    Output('upload-area', 'style'),
    Output('coverage-map', 'style'),
    Input('upload-data', 'contents')
)
def toggle_upload_area(list_of_contents):
        # if data is uploaded, hide the upload area and show the map
        return {'display': 'block'}, {'display': 'block', 'border': 'none', 'width': '100%', 'height': '800px', 'margin-bottom': '10px'}
