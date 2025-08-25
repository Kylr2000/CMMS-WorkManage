
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, ButtonHolder
from .models import CustomUser, RadioMeasurement, NetworkPointofReception, CellularMeasurement, WorkOrder, Asset, WorkOrderUpdate

class RegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # Modify the choices of the 'user_type' field
        self.fields['user_type'].choices = [
            choice for choice in self.fields['user_type'].choices if choice[0] != 'Administrator'
        ]
    class Meta:
        model = CustomUser
        fields = ('email', 'user_type', 'password1', 'password2')

class AdminLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(AdminLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            ButtonHolder(Submit('login', 'Login', css_class='btn-primary'))
        )

class RadioMeasurementForm(forms.ModelForm):
    npr_sites = forms.ModelMultipleChoiceField(
        queryset=NetworkPointofReception.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = RadioMeasurement
        fields = '__all__'

    def save(self, commit=True):
        instance = super(RadioMeasurementForm, self).save(commit=False)
        # Convert selected NPR sites to a string
        instance.npr_sites = ','.join(str(site.id) for site in self.cleaned_data['npr_sites'])
        if commit:
            instance.save()
        return instance
    
# CellularMeasurementForm class    
class CellularMeasurementForm(forms.ModelForm):
    class Meta:
        model = CellularMeasurement
        fields = '__all__'



# Asset Form
# ---------------------------
class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_tag', 'name', 'location', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


# ---------------------------
# Work Order Form
# ---------------------------
class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'title',
            'description',
            'status',
            'priority',
            'assigned_to',
            'asset',
            'due_date',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


# ---------------------------
# Work Order Update Form
# ---------------------------
class WorkOrderUpdateForm(forms.ModelForm):
    class Meta:
        model = WorkOrderUpdate
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter update/comment here...'}),
        }

