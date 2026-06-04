# models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
from registration.models import *

from django.contrib.auth.models import AbstractUser
    
    
class CpcbUser(models.Model):  
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    mobile_no = models.CharField(max_length=20, blank=True, default='')
    division = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=True)
    first_login = models.IntegerField(default=0)
    password_history = models.TextField(default='[]')
    # Add these for Django login compatibility
    is_admin = models.BooleanField(default=False)
    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.username

    class Meta:
        db_table = 'CpcbApp_user'
        app_label = 'CpcbApp'


class RoleType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'CpcbApp_roletype'
        app_label = 'CpcbApp'
    
class ProgressStatus(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    
    class Meta:
        db_table = 'CpcbApp_progressstatus'
        app_label = 'CpcbApp'


YES_NO_CHOICES = [
    ('yes', 'Yes'),
    ('no', 'No'),
]


class Checklist(models.Model):
    producer = models.ForeignKey('registration.producerGeneralDetails', on_delete=models.CASCADE, related_name='checklist')
    
    producer_name_address = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_producer_name_address = models.TextField(blank=True, null=True)

    company_email = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_company_email = models.TextField(blank=True, null=True)

    upload_gst_certificate = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_upload_gst_certificate = models.TextField(blank=True, null=True)
    
    year_of_incorporation = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_year_of_incorporation = models.TextField(blank=True, null=True)

    pan_card_uploaded = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_pan_card_uploaded = models.TextField(blank=True, null=True)
    
    tin_certificate_uploaded = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_tin_certificate_uploaded = models.TextField(blank=True, null=True)

    cin_certificate_uploaded = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_cin_certificate_uploaded = models.TextField(blank=True, null=True)

    iec_certificate_uploaded = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_iec_certificate_uploaded = models.TextField(blank=True, null=True)

    authorized_person_details = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_authorized_person_details = models.TextField(blank=True, null=True)
    
    authorized_person_pan_details = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_authorized_person_pan_details = models.TextField(blank=True, null=True)
    
    nature_of_business = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_nature_of_business = models.TextField(blank=True, null=True)

    name_address_facility = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_name_address_facility = models.TextField(blank=True, null=True)

    activity_type = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_activity_type = models.TextField(blank=True, null=True)

    capacity_of_facility = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_capacity_of_facility = models.TextField(blank=True, null=True)

    data_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_data_transport = models.TextField(blank=True, null=True)

    fy_data_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_fy_data_transport = models.TextField(blank=True, null=True)
    
    vehicle_data_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_vehicle_data_transport = models.TextField(blank=True, null=True)
    
    manufactured_data_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_manufactured_data_transport = models.TextField(blank=True, null=True)
    
    open_market_sales_data_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_open_market_sales_data_transport = models.TextField(blank=True, null=True)
    
    other_producer_sales_data_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_other_producer_sales_data_transport = models.TextField(blank=True, null=True)
    
    cobranding_sales_data_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_cobranding_sales_data_transport = models.TextField(blank=True, null=True)
    
    uploaded_excel_other_producer_standard_format_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_uploaded_excel_other_producer_standard_format_transport = models.TextField(blank=True, null=True)
    
    self_use_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_self_use_transport = models.TextField(blank=True, null=True)
    
    exported_vehicles_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_exported_vehicles_transport = models.TextField(blank=True, null=True)
    
    uploaded_ca_certificates_each_fy_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_uploaded_ca_certificates_each_fy_transport = models.TextField(blank=True, null=True)
    
    data_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_data_non_transport = models.TextField(blank=True, null=True)
    
    fy_data_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_fy_data_non_transport = models.TextField(blank=True, null=True)
    
    vehicle_data_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_vehicle_data_non_transport = models.TextField(blank=True, null=True)
    
    manufactured_data_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_manufactured_data_non_transport = models.TextField(blank=True, null=True)
    
    open_market_sales_data_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_open_market_sales_data_non_transport = models.TextField(blank=True, null=True)
    
    other_producer_sales_data_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_other_producer_sales_data_non_transport = models.TextField(blank=True, null=True)
    
    cobranding_sales_data_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_cobranding_sales_data_non_transport = models.TextField(blank=True, null=True)
    
    uploaded_excel_standard_format_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_uploaded_excel_standard_format_non_transport = models.TextField(blank=True, null=True)
    
    self_use_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_self_use_non_transport = models.TextField(blank=True, null=True)
    
    exported_vehicles_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_exported_vehicles_non_transport = models.TextField(blank=True, null=True)
    
    uploaded_ca_certificates_each_fy_non_transport = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_uploaded_ca_certificates_each_fy_non_transport = models.TextField(blank=True, null=True)

    provided_annual_turnover_both_fy = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_provided_annual_turnover_both_fy = models.TextField(blank=True, null=True)

    uploaded_ca_certificate_each_fy = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_uploaded_ca_certificate_each_fy = models.TextField(blank=True, null=True)
    
    uploaded_undertaking = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_uploaded_undertaking = models.TextField(blank=True, null=True)
    
    reg_fee = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    remarks_reg_fee = models.TextField(blank=True, null=True)
    
    
    def __str__(self):
        return f"Checklist #{self.pk}"
    
    
    class Meta:
        db_table = 'CpcbApp_checklist'
        app_label = 'CpcbApp'

class Noting(models.Model):
    producer = models.ForeignKey('registration.producerGeneralDetails', on_delete=models.CASCADE, related_name='noting')
    checklist = models.ForeignKey('Checklist', on_delete=models.CASCADE, related_name='noting_checklist', blank=True, null=True)
    
    comment = models.TextField(blank=False, null=False)
    last_updated_by = models.IntegerField(blank=False)
    forwarded_from = models.IntegerField(blank=False)
    forwarded_to = models.IntegerField(blank=False)
    forwarded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'CpcbApp_noting'
        app_label = 'CpcbApp'

class CertificateRegistry(models.Model):
    producer = models.ForeignKey('registration.producerGeneralDetails', on_delete=models.CASCADE)
    registration_no = models.CharField(max_length=20, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.registration_no
    
    class Meta:
        db_table = 'CpcbApp_certificateregistry'
        app_label = 'CpcbApp'
