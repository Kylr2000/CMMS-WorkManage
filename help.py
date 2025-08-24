import datetime
from Dashboard.models import RadioMeasurement, NetworkPointofReception, ReceivedQualitySignalStrength, ReceivedQualityReadability

# Helper function to convert DMS to decimal degrees
def dms_to_dd(degrees, minutes, seconds):
    return degrees + (minutes / 60.0) + (seconds / 3600.0)

# Function to create a RadioMeasurement instance
def create_radio_measurement(reading_data):
    # Convert DMS latitude and longitude to decimal degrees
    latitude_dd = dms_to_dd(*reading_data['latitude'])
    longitude_dd = dms_to_dd(*reading_data['longitude'])

    # Create or get the ReceivedQualitySignalStrength and ReceivedQualityReadability instances
    signal_strength_instance = ReceivedQualitySignalStrength.objects.get(Signalstrength_no=reading_data['Signalstrength_no'])
    readability_instance = ReceivedQualityReadability.objects.get(Readability_no=reading_data['Readability_no'])

    # Create the RadioMeasurement instance
    radio_measurement = RadioMeasurement(
        Measurement_Date=datetime.datetime.strptime(reading_data['Date'], '%d-%m-%Y').date(),
        Measurement_Time=datetime.datetime.strptime(reading_data['Time'], '%H:%M:%S').time(),
        latitude=latitude_dd,
        longitude=-longitude_dd,  # Western longitude should be negative
        Field_Strength_dbuv_m=reading_data['Field_Strength_dbuv_m'],
        Signal_Strength_dbm=reading_data['Signal_Strength_dbm'],
        DSC_Response=reading_data['DSC_Response'],
        Tx_site=reading_data['Tx_site'],
        Rx_site=reading_data['Rx_site'],
        ReceivedQuality_Description=reading_data['ReceivedQuality_Description'],
        SignalStrength=signal_strength_instance,
        Readability=readability_instance
    )

    # Save the instance to the database
    radio_measurement.save()

    # Associate NPR sites that are in range
    for site_name in reading_data['npr_sites']:
        npr_site = NetworkPointofReception.objects.get(Site_Name=site_name)
        radio_measurement.npr_sites.add(npr_site)

    # Confirm the save and associations
    print(f'Successfully added RadioMeasurement with ID: {radio_measurement.id}')

# Example usage
readings = [
    {
        'Date': '24-08-2023',
        'Time': '12:10:00',
        'latitude': (10, 50, 54.19),
        'longitude': (61, 43, 2.37),
        'Field_Strength_dbuv_m': 58,
        'Signal_Strength_dbm': -48.99,
        'DSC_Response': 'NO',
        'Signalstrength_no': 5,
        'Readability_no': 6,
        'Tx_site': 'NP',
        'Rx_site': 'Portable and TTCG Mobile',
        'ReceivedQuality_Description': 'Portable receiving with slight distortion',
        'npr_sites': ['Morne Bleu', 'North Post'],
    },
    {
        'Date': '24-08-2023',
        'Time': '12:25:00',
        'latitude': (10, 55, 24.99),
        'longitude': (61, 42, 26.2),
        'Field_Strength_dbuv_m': 45.4,
        'Signal_Strength_dbm': -61.59,
        'DSC_Response': 'NO',
        'Signalstrength_no': 5,
        'Readability_no': 6,
        'Tx_site': 'NP',
        'Rx_site': 'Portable and TTCG Mobile',
        'ReceivedQuality_Description': 'Portable receiving with slight distortion',
        'npr_sites': ['Morne Bleu', 'North Post'],
    },
    # Add additional dictionaries for each record
]

# Iterate over each reading and create a RadioMeasurement
for reading in readings:
    create_radio_measurement(reading)
