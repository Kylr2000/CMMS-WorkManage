from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# Create your models here.

class Operator(models.Model):
    Operator_Name = models.CharField(max_length=200)
    Operator_ID = models.CharField(max_length=200)

    def __str__(self):
        return self.Operator_Name

class NetworkTechnology(models.Model):
    Technology_name = models.CharField(max_length=200)
    def __str__(self):
        return self.Technology_name

class CellSite(models.Model):
    SiteName = models.CharField(max_length=200, blank=True, null=True)
    Operator = models.ForeignKey(Operator, related_name='cell_site', on_delete=models.CASCADE, blank=True, null=True)
    Network_Technology = models.ForeignKey(NetworkTechnology, related_name='cell_site', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.SiteName
    
class CellularMeasurement(models.Model):
    Cell_Site = models.ForeignKey(CellSite, related_name='cellular_measurements', on_delete=models.CASCADE)
    Date = models.DateField()
    Time = models.TimeField()
    Latitude = models.FloatField()
    Longitude = models.FloatField()
    RSSI = models.IntegerField()
    RSCP = models.IntegerField()

class NetworkPointofReception(models.Model):
    Site_Name = models.CharField(max_length=100)

    def __str__(self):
        return self.Site_Name


class ReceivedQualitySignalStrength(models.Model):
    Signalstrength_no = models.IntegerField()
    Signalstrength_description = models.TextField()
    Signalstrength_meaning = models.TextField()

    def __str__(self):
        return self.Signalstrength_description


class ReceivedQualityReadability(models.Model):
    Readability_no = models.IntegerField()
    Readability_description = models.TextField()
    Readability_meaning = models.TextField()

    def __str__(self):
        return self.Readability_description


class RadioMeasurement(models.Model):
    Measurement_Date = models.DateField()
    Measurement_Time = models.TimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    Field_Strength_dbuv_m = models.FloatField()
    Signal_Strength_dbm = models.FloatField()
    DSC_Response = models.CharField(max_length=100, blank=True, null=True)
    Tx_site = models.CharField(max_length=100, blank=True, null=True)
    Rx_site = models.CharField(max_length=100, blank=True, null=True)
    SignalStrength = models.ForeignKey(ReceivedQualitySignalStrength, related_name='radio_measurements', on_delete=models.CASCADE, blank=True, null=True)
    Readability = models.ForeignKey(ReceivedQualityReadability, related_name='radio_measurements', on_delete=models.CASCADE, blank=True, null=True)
    ReceivedQuality_Description = models.TextField(blank=True, null=True)
    npr_sites = models.CharField(max_length=255, blank=True, null=True)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, user_type='staff', **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if user_type not in ['admin', 'staff', 'technician', 'engineer']:
            raise ValueError("Invalid user type")
        
        user = self.model(email=self.normalize_email(email), user_type=user_type, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        return self.create_user(email, password, user_type='admin', **extra_fields)



class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Define all user roles here
    USER_TYPE_CHOICES = [
        ('admin', 'Administrator'),
        ('staff', 'Staff'),
        ('technician', 'Technician'),
        ('engineer', 'Engineer'),
    ]

    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='staff')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Only True for admin/staff
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"

    # Optional helper properties
    @property
    def is_admin(self):
        return self.user_type == 'admin' or self.is_superuser

    @property
    def is_technician(self):
        return self.user_type == 'technician'

    @property
    def is_engineer(self):
        return self.user_type == 'engineer'
    
class Transmitter(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    height = models.FloatField()

# ---------------------------
# Asset model (same as before)
# ---------------------------
class Asset(models.Model):
    asset_tag = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.asset_tag} - {self.name}"


# ---------------------------
# Work Order model
# ---------------------------
class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    assigned_to = models.ForeignKey(
        CustomUser,
        limit_choices_to={'user_type': 'technician'},  # restrict assignment to technicians
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)
    completed_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


# ---------------------------
# Work Order Update / Comments
# ---------------------------
class WorkOrderUpdate(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey(
        CustomUser,
        limit_choices_to={'user_type': 'technician'},
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    comment = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update for {self.work_order.title} by {self.updated_by}"


