from django.contrib import admin
from  .models import CustomUser, RadioMeasurement, CellularMeasurement, ReceivedQualitySignalStrength, ReceivedQualityReadability, NetworkPointofReception, Operator, NetworkTechnology, CellSite


# Register your models here.
class MemberCustomUser(admin.ModelAdmin):
    list_display = ('email', 'user_type')
    

admin.site.register(CustomUser, MemberCustomUser)

class RadioMeasurementChange(admin.ModelAdmin):
    list_display = ('Measurement_Date', 'Measurement_Time', 'latitude', 'longitude', 'Field_Strength_dbuv_m', 'Signal_Strength_dbm', 'DSC_Response', 'Tx_site', 'Rx_site', 'SignalStrength', 'Readability', 'ReceivedQuality_Description', 'npr_sites')

admin.site.register(RadioMeasurement, RadioMeasurementChange)

class ReceivedQualitySignalStrengthChange(admin.ModelAdmin):
    list_display = ('Signalstrength_no', 'Signalstrength_description', 'Signalstrength_meaning')

admin.site.register(ReceivedQualitySignalStrength, ReceivedQualitySignalStrengthChange)

class ReceivedQualityReadabilityChange(admin.ModelAdmin):
    list_display = ('Readability_no', 'Readability_description', 'Readability_meaning')

admin.site.register(ReceivedQualityReadability, ReceivedQualityReadabilityChange)

class NetworkPointofReceptionChange(admin.ModelAdmin):
    list_display = ('Site_Name',)

admin.site.register(NetworkPointofReception, NetworkPointofReceptionChange)


class CellularMeasurementChange(admin.ModelAdmin):
    list_display = ('Date', 'Time', 'Latitude', 'Longitude', 'RSSI', 'RSCP', 'Cell_Site')

admin.site.register(CellularMeasurement, CellularMeasurementChange)

class OperatorChange(admin.ModelAdmin):
    list_display = ('Operator_Name', 'Operator_ID')

admin.site.register(Operator, OperatorChange)

class NetworkTechnologyChange(admin.ModelAdmin):
    list_display = ('Technology_name',)

admin.site.register(NetworkTechnology, NetworkTechnologyChange)

class CellSiteChange(admin.ModelAdmin):
    list_display = ('SiteName', 'Operator', 'Network_Technology')

admin.site.register(CellSite, CellSiteChange)