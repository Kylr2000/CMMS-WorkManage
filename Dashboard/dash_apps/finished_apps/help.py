from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
import plotly.express as px
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import geopandas as gpd
from Dashboard.models import RadioMeasurement, NetworkPointofReception, ReceivedQualitySignalStrength, ReceivedQualityReadability, CellularMeasurement, CellSite, Operator, NetworkTechnology, Transmitter

external_stylesheets = [dbc.themes.BOOTSTRAP, '/static/css/print.css']
# Create a dash application
app = DjangoDash('Help', external_stylesheets=external_stylesheets)

# Fetch the data from the RecievedQualitySignalStrength model
data = ReceivedQualitySignalStrength.objects.all()
#place in dataframe
df = pd.DataFrame(data.values())
#Rename Signalstrength to Signal Reception
df = df.rename(columns={'Signalstrength_no': 'Signal Reception', 'Signalstrength_description': 'Description', 'Signalstrength_meaning': 'Meaning'})
# Fetch the data from the RecievedQualityReadability model
data1 = ReceivedQualityReadability.objects.all()
#place in dataframe
df1 = pd.DataFrame(data1.values())
#Rename Readability
df1 = df1.rename(columns={'Readability_no': 'Readability', 'Readability_description': 'Description', 'Readability_meaning': 'Meaning'})
#Create a dataframe for RSSI ratings: Excellent (RSSI>-60dBm, Good (-70dBm to -85 dBm,), Fair(-86 dBm to -100 dBm), Poor (-100 dBm to -120dBm) and No Signal (<-120 dBm)
cell_rate_data = {'Description': ['Excellent', 'Good', 'Fair', 'Poor', 'No Signal'], 'RSSI Range': ['RSSI>-60dBm', '-70dBm to -85 dBm', '-86 dBm to -100 dBm', '-100 dBm to -120dBm', '<-120 dBm']}
df_cell = pd.DataFrame(cell_rate_data) 

# Create a dashtable for the data
# Define color dictionary for signal reception description
color_dict = {'LOUD': 'green', 'GOOD': 'blue', 'WEAK': 'yellow', 'VERY WEAK': 'orange' ,'FADING': 'red', 'NONE': 'black'}
# Add a new column 'Color' to df by mapping the 'Description' column to the color_dict
df['Colour'] = df['Description'].str.upper().map(color_dict)
print(df)

table = dash_table.DataTable(df.to_dict('records'), [{"name": i, "id": i} for i in df.columns], style_header={
        'backgroundColor': 'rgb(210, 210, 210)',
        'color': 'black',
        'fontWeight': 'bold',
        'border': '1px solid white'})
table1 = dash_table.DataTable(df1.to_dict('records'), [{"name": i, "id": i} for i in df1.columns], style_header={
        'backgroundColor': 'rgb(210, 210, 210)',
        'color': 'black',
        'fontWeight': 'bold',
        'border': '1px solid white'})
table2 = dash_table.DataTable(df_cell.to_dict('records'), [{"name": i, "id": i} for i in df_cell.columns], style_header={
        'backgroundColor': 'rgb(210, 210, 210)',
        'color': 'black',
        'fontWeight': 'bold',
        'border': '1px solid white'})

# Create a dash layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Help Page"),
            html.H6("This is the help page for the dashboard. It contains information on the range used in the dashboard for rating/classifying the VHF Radio and Cellular Signal Strengths."),
    ]),
    ],align='end', style={'margin-top': '20px', 'margin-bottom': '20px'}),
    dbc.Card(
        dbc.CardBody([  
            dbc.Row([
                html.H3("Breakdown of Signal Reception Ratings"),
                html.H6("The standard used for both Radio Signal Reception and Readability is based on the ACP 125(G), “Communications Instructions – Radiotelephone Procedures”. The ACP 125(G) is a NATO standard that provides guidance on the use of radiotelephone procedures for military communications. The standard is used by the UK Ministry of Defence and other NATO countries. The standard provides guidance on the use of radiotelephone procedures for military communications. The standard is used by the UK Ministry of Defence and other NATO countries. The standard can be found on pages 67 and 68."),
                dcc.Link('ACP 125(G)', href='https://orwg.cap.gov/media/cms/ACP125GRadioTelephoneProceduresNOV2_EFFE1A51BA783.pdf', target='_blank'),
                table,
            ]),
        ]),style={'margin-top': '20px', 'margin-bottom': '40px'},
    ),
    dbc.Card(
        dbc.CardBody([
            html.H3("Breakdown of Readability Ratings"),
            dbc.Row([
                html.H6("The readability ratings are broken down into 6 categories and represent the size of the data point plotted on the map. Higher readability ratings are represented by larger data points."),
                table1
            ]),
        ]),
    ),
    dbc.Card(
        dbc.CardBody([  
            dbc.Row([
                html.H3("Cellular Signal Strength Ratings"),
                html.H6("The RSSI Ratings below are taken from the research by multiple telecommunications companies on RSSI ranges. These Companies were Cisco and OptConnect. Their studies can be found in the links below"),
                dcc.Link('OptConnect', href='https://pages.optconnect.com/identifying-signal-strength-and-interference', target='_blank'),
                dcc.Link('Cisco', href='https://www.cisco.com/c/en/us/support/docs/wireless/5500-series-wireless-controllers/116057-site-survey-guidelines-wlan-00.html', target='_blank'),
                table2
            ]),
        ]),style={'margin-top': '20px', 'margin-bottom': '40px'},
    )
])
