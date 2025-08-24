from django.urls import path
from . import views
from .views import admin_login_view, admin_signup
from Dashboard.dash_apps.finished_apps import example
from Dashboard.dash_apps.finished_apps import Detailed_Analysis
from Dashboard.dash_apps.finished_apps import Simulation
from Dashboard.dash_apps.finished_apps import help
from .views import GenerateReportView

urlpatterns = [
    path('', views.Dashboard, name='Dashboard'),
    path('Detailed_analysis', views.Detailed_Analysis, name='Detailed_analysis'),
    path('Simulation', views.Simulation, name='Simulation'),
    path('Help', views.Help, name='Help'),
    path('coverage_los', views.coverage_los, name='coverage_los'),
    path('admin_login', admin_login_view.as_view(), name='admin_login'),
    path('admin_signup', admin_signup.as_view(), name='admin_signup'),
    path('admin_home', views.admin_home, name='admin_home'),
    path('logout', views.logout_view.as_view(), name='logout'),
    path('Enter_Data', views.Enter_Data, name='Enter_Data'),
    path('radio_measurement_create,', views.radio_measurement_form, name='radio_measurement_create'),
    path('cell_measurement_create,', views.cellular_measurement_form, name='cell_measurement_create'),
    path('geojson', views.geojson_view, name='geojson'),
    path('Report', GenerateReportView.as_view(), name='report')
]