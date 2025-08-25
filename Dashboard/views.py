from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render, redirect
from plotly.offline import plot
import plotly.graph_objects as go
from .forms import AdminLoginForm, RegistrationForm, RadioMeasurementForm, CellularMeasurementForm
from django.urls import reverse_lazy
from django.views import generic, View
from .models import RadioMeasurement, CellularMeasurement
from django.core.serializers import serialize
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import UserPassesTestMixin
from .models import RadioMeasurement, NetworkPointofReception, ReceivedQualitySignalStrength, ReceivedQualityReadability, CellularMeasurement, CellSite, NetworkTechnology, Operator, Transmitter
import json, os
from jinja2 import Environment, FileSystemLoader
from django.http import HttpResponse
import matplotlib.pyplot as plt
import pandas as pd
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from .models import Transmitter
import math
from datetime import datetime
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import AssetForm, WorkOrderForm, WorkOrderUpdateForm
from .models import WorkOrder



# Create your views here.

@staff_member_required(login_url='admin_login')
def Dashboard(request):

    return render(request, 'dashapp/myfirst.html')



def Detailed_Analysis(request):
     return render(request, 'dashapp/Detailed_analysis.html')

def Help(request):
    return render(request, 'dashapp/Help.html')

def calculate_coverage(height):
     A = 2.5 * (math.sqrt(height) + math.sqrt(1))
     
     return A*1852

def coverage_los(request):
    data = []
    for transmitter in Transmitter.objects.all():
        coverage = calculate_coverage(transmitter.height)
        data.append({
            'name': transmitter.name,
            'latitude': transmitter.latitude,
            'longitude': transmitter.longitude,
            'height': transmitter.height,
            'coverage': coverage,
        })
    return JsonResponse({'data': data}, safe=False)


def Simulation(request):
    return render(request, 'dashapp/Simulation.html')

class admin_login_view(generic.FormView):
    form_class = AdminLoginForm
    template_name = 'dashapp/admin_login.html'
    success_url = reverse_lazy('Dashboard')  # <-- change here

    def get(self, request, *args, **kwargs):
        if 'next' in request.GET:
            messages.error(request, 'Please login as a registered user or administrator')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=email, password=password)
        if user is not None:
            login(self.request, user)
            return super(admin_login_view, self).form_valid(form)
        else:
            return self.form_invalid(form)
          
def admin_home(request):
        return render(request, 'dashapp/admin_home.html')

class admin_signup(generic.CreateView):
     form_class = RegistrationForm
     template_name = 'dashapp/admin_signup.html'
     success_url = reverse_lazy('admin_home')
     
class logout_view(generic.RedirectView):
     url = reverse_lazy('admin_login')
     def get(self, request, *args, **kwargs):
          logout(request)
          return super(logout_view, self).get(request, *args, **kwargs)
     
def Enter_Data(request):
     return render(request, 'dashapp/Enter_Data.html')


def radio_measurement_form(request):
    if request.method == 'POST':
        form = RadioMeasurementForm(request.POST)
        if form.is_valid():
            radio_measurement = form.save(commit=False)
            # Process the npr_sites data here
            # For example, you might receive a list of NPR site IDs from the form
            npr_site_ids = form.cleaned_data['npr_sites']
            # Convert the list of IDs to a comma-separated string
            radio_measurement.npr_sites = ','.join(map(str, npr_site_ids))
            radio_measurement.save()
            # Redirect to a new URL, for example, the detail view of the measurement
            return redirect('admin_home')
    else:
        form = RadioMeasurementForm()

    return render(request, 'forms/radio_measurement_create.html', {'form': form})

def cellular_measurement_form(request):
    if request.method == 'POST':
        form = CellularMeasurementForm(request.POST)
        if form.is_valid():
            cellular_measurement = form.save()
            # Redirect to a new URL, for example, the detail view of the measurement
            return redirect('admin_home')
    else:
        form = CellularMeasurementForm()

    return render(request, 'forms/cell_measurement_create.html', {'form': form})

@method_decorator(staff_member_required(login_url='admin_login'), name='dispatch')
class GenerateReportView( View):
        def get(self, request, *args, **kwargs):
            def generate_report(request):
                    # Get the start and end dates from the request's query parameters
                start_date_str = request.GET.get('start_date')
                end_date_str = request.GET.get('end_date')
                coverage_type = request.GET.get('coverage_type')

                # Convert the dates from strings to datetime.date objects
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
                radio_data = []
                cell_data = []

                #Fetch both RadioMeasurement and CellularMeasurement data
                if coverage_type == 'all':
                    print("Fetching all measurements")
                    radio_measurements = RadioMeasurement.objects.filter(Measurement_Date__range=[start_date, end_date])
                    cellular_measurements = CellularMeasurement.objects.filter(Date__range=[start_date, end_date])
                                    # Initialize an empty list to hold the report data
                    radio_data = []
                    cell_data = []


                    # Iterate over the measurements
                    for measurement in radio_measurements:
                        # Fetch the related ReceivedQualitySignalStrength and ReceivedQualityReadability objects
                        signal_strength = ReceivedQualitySignalStrength.objects.get(Signalstrength_description=measurement.SignalStrength)
                        readability = ReceivedQualityReadability.objects.get(Readability_description=measurement.Readability)

                        # Add the measurement data to the report data
                        radio_data.append({
                            'Time': measurement.Measurement_Time,
                            'Signal Strength (dBm)': measurement.Signal_Strength_dbm,
                            'Field Strength (dBuV/m)': measurement.Field_Strength_dbuv_m,
                            'Signal Strength Rating': signal_strength.Signalstrength_description,
                            'Readability Rating': readability.Readability_description,

                        })
                        
                    cellular_measurements = CellularMeasurement.objects.filter(Date__range=[start_date, end_date])
                    cell_data = []
                    # Iterate over the cellular measurements using the models
                    for measurement in cellular_measurements:
                        # Fetch the related CellSite and NetworkTechnology objects
                        cell_site = CellSite.objects.get(id=measurement.Cell_Site_id)
                        network_technology = NetworkTechnology.objects.get(id=cell_site.Network_Technology_id)
                        operator = Operator.objects.get(id=cell_site.Operator_id)

                        # Add the measurement data to the report data
                        cell_data.append({
                            'Cellular Time': measurement.Time,
                            'Latitude': measurement.Latitude,
                            'Longitude': measurement.Longitude,
                            'RSSI': measurement.RSSI,
                            'RSCP': measurement.RSCP,
                            'Site Name': cell_site.SiteName,
                            'Operator': operator.Operator_Name,
                            'Network Technology': network_technology.Technology_name,
                        })
                    #calculate average RSSI and RSCP
                    rssi_avg = cellular_measurements.exclude(RSSI=0).aggregate(Avg('RSSI'))['RSSI__avg']
                    rscp_avg = cellular_measurements.exclude(RSCP=0).aggregate(Avg('RSCP'))['RSCP__avg']

                    #calculate number of 3G readings
                    three_g = cellular_measurements.filter(Cell_Site__Network_Technology=1).count()
                    #calculate number of 4G readings
                    four_g = cellular_measurements.filter(Cell_Site__Network_Technology=2).count()

                elif coverage_type == 'Radio':
                    radio_measurements = RadioMeasurement.objects.filter(Measurement_Date__range=[start_date, end_date])
                    radio_data = []

                    # Iterate over the measurements
                    for measurement in radio_measurements:
                        # Fetch the related ReceivedQualitySignalStrength and ReceivedQualityReadability objects
                        signal_strength = ReceivedQualitySignalStrength.objects.get(Signalstrength_description=measurement.SignalStrength)
                        readability = ReceivedQualityReadability.objects.get(Readability_description=measurement.Readability)

                        # Add the measurement data to the report data
                        radio_data.append({
                            'Time': measurement.Measurement_Time,
                            'Signal Strength (dBm)': measurement.Signal_Strength_dbm,
                            'Field Strength (dBuV/m)': measurement.Field_Strength_dbuv_m,
                            'Signal Strength Rating': signal_strength.Signalstrength_description,
                            'Readability Rating': readability.Readability_description,

                        })
                elif coverage_type == 'Cellular':
                    cellular_measurements = CellularMeasurement.objects.filter(Date__range=[start_date, end_date])
                    cell_data = []
                    # Iterate over the cellular measurements using the models
                    for measurement in cellular_measurements:
                        # Fetch the related CellSite and NetworkTechnology objects
                        cell_site = CellSite.objects.get(id=measurement.Cell_Site_id)
                        network_technology = NetworkTechnology.objects.get(id=cell_site.Network_Technology_id)
                        operator = Operator.objects.get(id=cell_site.Operator_id)

                        # Add the measurement data to the report data
                        cell_data.append({
                            'Cellular Time': measurement.Time,
                            'Latitude': measurement.Latitude,
                            'Longitude': measurement.Longitude,
                            'RSSI': measurement.RSSI,
                            'RSCP': measurement.RSCP,
                            'Site Name': cell_site.SiteName,
                            'Operator': operator.Operator_Name,
                            'Network Technology': network_technology.Technology_name,
                        })
                    #calculate average RSSI and RSCP
                    rssi_avg = cellular_measurements.exclude(RSSI=0).aggregate(Avg('RSSI'))['RSSI__avg']
                    rscp_avg = cellular_measurements.exclude(RSCP=0).aggregate(Avg('RSCP'))['RSCP__avg']

                    #calculate number of 3G readings
                    three_g = cellular_measurements.filter(Cell_Site__Network_Technology=1).count()
                    #calculate number of 4G readings
                    four_g = cellular_measurements.filter(Cell_Site__Network_Technology=2).count()
                

                
                

                # Convert the report data to a DataFrame
                radio_df = pd.DataFrame(radio_data)
                cell_df = pd.DataFrame(cell_data)

                # Load the Jinja2 template
                env = Environment(loader=FileSystemLoader('templates'))
                template = env.get_template('Report.html')

                # Render the template with the report data and the graph
                report_html = template.render(
                    report1=radio_df.to_html(index=False),
                    report2=cell_df.to_html(index=False),
                    rssi=rssi_avg,
                    rscp=rscp_avg,
                    three_g=three_g,
                    four_g=four_g)

                # Return the report as an HTML response
                return HttpResponse(report_html)
            return generate_report(request)
        

def geojson_view(request):
    # Load the GeoJSON file
    with open('dash_apps/corrected_transmitter_towers.geojson') as f:
        geojson = json.load(f)

    # Return the GeoJSON as a JSON response
    return JsonResponse(geojson)



@login_required
def create_asset(request):
    if request.method == "POST":
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("Dashboard")  # adjust to your success page
    else:
        form = AssetForm()
    return render(request, "dashapp/asset_form.html", {"form": form})


@login_required
def create_workorder(request):
    if request.method == "POST":
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("Dashboard")
    else:
        form = WorkOrderForm()
    return render(request, "dashapp/workorder_form.html", {"form": form})


@login_required
def add_workorder_update(request, pk):
    work_order = get_object_or_404(WorkOrder, pk=pk)
    if request.method == "POST":
        form = WorkOrderUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.work_order = work_order
            update.updated_by = request.user
            update.save()
            return redirect("Dashboard")
    else:
        form = WorkOrderUpdateForm()
    return render(request, "dashapp/workorder_update_form.html", {"form": form, "work_order": work_order})
                
     
     

          


   
