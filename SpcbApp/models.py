from django.db import models
from django.utils import timezone
import pytz
from datetime import datetime


# utc_time = timezone.now()  # 2026-01-09 11:57:30.134816+00:00

#     # Convert to local time (if TIME_ZONE is set in settings)
# local_time = timezone.localtime(utc_time)
# print(local_time)
# Create your models here.
class StateUsers(models.Model):
    username = models.CharField(max_length=150, unique=True , null=True)
    password = models.CharField(max_length=128, blank=True,null=True)
    auth_mobile = models.CharField(max_length=10, default=9999999999)
    auth_email = models.EmailField(default='test@gmail.com')
    OfficerName= models.CharField(max_length=100, null=True)
    officerDesignation = models.CharField(max_length=100, null=True)
    RoleAccess = models.CharField(max_length=100, null=True)
    State_id = models.IntegerField(default=0)
    District_id = models.IntegerField(default=0)
    first_login = models.IntegerField(default=0)
    DisableStatus = models.IntegerField(default=0)
    password_history = models.TextField(default='[]')
    
    class Meta:
            db_table = 'spcbapp_stateusers'
        
class StateRoles(models.Model):
    Rolename = models.CharField(max_length=100 , null=True)
    class Meta:
        db_table = 'spcbapp_stateroles'
    def __str__(self):
        return self.Rolename  # O
    
def get_india_time():
    """Returns current time in India timezone"""
    # Method 1: Using pytz directly (most reliable)
    # india_tz = pytz.timezone('Asia/Kolkata')
    # # Use timezone.now() to get UTC, then convert
    # utc_now = timezone.now()
    india_tz = pytz.timezone('Asia/Kolkata')
    # Get current time directly in IST
    ist_now = timezone.now().astimezone(india_tz)
    return ist_now
    

class ApplicationTrail(models.Model):
    AppNo = models.CharField(max_length=100 ,null=True)
    stateid = models.IntegerField(default=0)
    marked_to_designation = models.CharField(max_length=50 , null=True)
    marked_by_designation = models.CharField(max_length=50 , null=True) 
    marked_to_role = models.IntegerField(default=0)  # Recommending Authority / Reporting Authority
    marked_by_role = models.IntegerField(default=0)  # Recommending Authority / Reporting Authority
    # marked_to_id = models.IntegerField(default=0)  
    # marked_by_id = models.IntegerField(default=0)  
    comment = models.TextField(blank=True, null=True)
    added_by_userid = models.IntegerField(default=0)
    added_by_person= models.CharField(max_length=100 , null=True)
    added_to_userid = models.IntegerField(default=0)
    added_to_person= models.CharField(max_length=100 , null=True)
    industry_user_id = models.IntegerField(default=0)
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=get_india_time)
    
    # OR using the helper function:
    # created_at = models.DateTimeField(default=get_current_local_time)
    
    def __str__(self):
        return f"{self.AppNo} - {self.created_at}"

class ApplicationStatus(models.Model):
    AppStatus = models.IntegerField(unique=True)
    Description = models.CharField(max_length=100)
    RoleAccess = models.IntegerField(default=0)
    DisableStatus = models.IntegerField(default=0)


    def __str__(self):
        return self.Description  # O
class SignupChecklist(models.Model):
    industryid = models.IntegerField(default=0)
    AppNo = models.CharField(max_length=30)
    name_address = models.CharField(max_length=50 , null=True)
    remarks_name_address = models.CharField(max_length=500 , null=True)
    company_email = models.CharField(max_length=50 , null=True)
    remarks_company_email = models.CharField(max_length=500 , null=True)
    gst_certificate = models.CharField(max_length=50 , null=True)
    remarks_gst_certificate = models.CharField(max_length=500 , null=True)
    company_pan_card = models.CharField(max_length=50 , null=True)
    remarks_company_pan_card = models.CharField(max_length=500 , null=True)
    company_tin = models.CharField(max_length=50 , null=True)
    remarks_company_tin = models.CharField(max_length=500 , null=True)
    company_cin = models.CharField(max_length=50 , null=True)
    remarks_company_cin = models.CharField(max_length=500 , null=True)
    company_iec = models.CharField(max_length=50 , null=True)
    remarks_company_iec = models.CharField(max_length=500 , null=True)
    auth_person_details = models.CharField(max_length=500 , null=True)
    remarks_auth_person_details = models.CharField(max_length=500 , null=True)
    added_by = models.IntegerField(default=0)

class ActiveSession(models.Model):
    """
    Tracks the single allowed active session for a given principal.
    We support both admin users and Registration users.
    """
    USER_TYPES = (
        ("admin", "Django Admin/User"),
        ("user", "Registration user"),
    )
    user_type   = models.CharField(max_length=10, choices=USER_TYPES)
    user_id     = models.PositiveIntegerField()
    session_key = models.CharField(max_length=64, unique=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user_type", "user_id")

    def __str__(self):
        return f"{self.user_type}:{self.user_id} -> {self.session_key}"

class GeneralChecklist(models.Model):
    AppNo = models.CharField(max_length=100, unique=True)
    Industryid = models.IntegerField(default=0)
    rvsf_address = models.TextField(blank=True, null=True)
    remarks_rvsf_address = models.TextField(blank=True, null=True)
    gps_location = models.CharField(max_length=255, blank=True, null=True)
    remarks_gps_location = models.TextField(blank=True, null=True)
    rvsf_state = models.CharField(max_length=100, blank=True, null=True)
    remarks_rvsf_state = models.TextField(blank=True, null=True)
    cto_certificate = models.CharField(max_length=255, blank=True, null=True)
    remarks_cto_certificate = models.TextField(blank=True, null=True)
    cto_validity = models.CharField(max_length=100, blank=True, null=True)
    remarks_cto_validity = models.TextField(blank=True, null=True)
    howm_certificate = models.CharField(max_length=255, blank=True, null=True)
    remarks_howm_certificate = models.TextField(blank=True, null=True)
    dic_certificate = models.CharField(max_length=255, blank=True, null=True)
    remarks_dic_certificate = models.TextField(blank=True, null=True)
    rvsf_certificate = models.CharField(max_length=255, blank=True, null=True)
    remarks_rvsf_certificate = models.TextField(blank=True, null=True)
    rvsf_certificate_validity = models.CharField(max_length=100, blank=True, null=True)
    remarks_rvsf_certificate_validity = models.TextField(blank=True, null=True)
    process_flow = models.TextField(blank=True, null=True)
    remarks_process_flow = models.TextField(blank=True, null=True)
    material_balance_sheet = models.TextField(blank=True, null=True)
    remarks_material_balance_sheet = models.TextField(blank=True, null=True)
    annual_return = models.TextField(blank=True, null=True)
    remarks_annual_return = models.TextField(blank=True, null=True)
    added_by = models.IntegerField(default=0)


class EquipmentChecklist(models.Model):
    industryid = models.IntegerField(default=0)
    AppNo = models.CharField(max_length=100, unique=True)
    dismantling_equipment = models.BooleanField(default=False)
    remarks_dismantling_equipment = models.TextField(blank=True, null=True)
    depollution_equipment = models.BooleanField(default=False)
    remarks_depollution_equipment = models.TextField(blank=True, null=True)
    bailing_equipment = models.BooleanField(default=False)
    remarks_bailing_equipment = models.TextField(blank=True, null=True)
    shredding_equipment = models.BooleanField(default=False)
    remarks_shredding_equipment = models.TextField(blank=True, null=True)
    storage_equipment = models.BooleanField(default=False)
    remarks_storage_equipment = models.TextField(blank=True, null=True)
    classifier_equipment = models.BooleanField(default=False)
    remarks_classifier_equipment = models.TextField(blank=True, null=True)
    other_equipment = models.BooleanField(default=False)
    remarks_other_equipment = models.TextField(blank=True, null=True)
    added_by = models.IntegerField(default=0)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Checklist for AppNo: {self.AppNo}"
class FacilityChecklist(models.Model):
    industryid = models.IntegerField(default=0)
    AppNo = models.CharField(max_length=100, unique=True)
    geo_tagged_video = models.BooleanField(default=False)
    remarks_geo_tagged_video = models.TextField(blank=True, null=True)
    total_rvsf_area = models.BooleanField(default=False)
    remarks_total_rvsf_area = models.TextField(blank=True, null=True)
    shift_number = models.BooleanField(default=False)
    remarks_shift_number = models.TextField(blank=True, null=True)
    sectioned_power = models.BooleanField(default=False)
    remarks_sectioned_power = models.TextField(blank=True, null=True)
    employees_number = models.BooleanField(default=False)
    remarks_employees_number = models.TextField(blank=True , null=True)
    added_by = models.IntegerField(default=0)


class CapacityChecklist(models.Model):
    industryid = models.IntegerField(default=0)
    AppNo = models.CharField(max_length=100, unique=True)
    vehicle_category = models.BooleanField(default=False)
    remarks_vehicle_category = models.TextField(blank=True, null=True)
    vehicle_installed_capacity = models.BooleanField(default=False)
    remarks_vehicle_installed_capacity = models.TextField(blank=True, null=True)
    steel_installed_capacity = models.BooleanField(default=False)
    remarks_steel_installed_capacity = models.TextField(blank=True, null=True)
    vehicle_operating_capacity = models.BooleanField(default=False)
    remarks_vehicle_operating_capacity = models.TextField(blank=True, null=True)
    steel_operating_capacity = models.BooleanField(default=False)
    remarks_steel_operating_capacity = models.TextField(blank=True, null=True)
    added_by = models.IntegerField(default=0)

    def __str__(self):
        return f"Checklist for AppNo: {self.AppNo}"
    
class PollutionChecklist(models.Model):
    industryid = models.IntegerField(default=0)
    AppNo = models.CharField(max_length=100, unique=True)
    air_pollution = models.BooleanField(default=False)
    remarks_air_pollution = models.TextField(blank=True, null=True)
    water_pollution = models.BooleanField(default=False)
    remarks_water_pollution = models.TextField(blank=True, null=True)
    noise_pollution = models.BooleanField(default=False)
    remarks_noise_pollution = models.TextField(blank=True, null=True)
    added_by = models.IntegerField(default=0)

    def __str__(self):
        return f"Pollution Checklist - {self.AppNo}"
    

class WasteRecycleChecklist(models.Model):
    industryid = models.IntegerField(default=0)
    AppNo = models.CharField(max_length=100, unique=True)
    used_oil = models.BooleanField(default=False)
    remarks_used_oil = models.TextField(blank=True, null=True)
    plastic_waste = models.BooleanField(default=False)
    remarks_plastic_waste = models.TextField(blank=True, null=True)
    battery_waste = models.BooleanField(default=False)
    remarks_battery_waste = models.TextField(blank=True, null=True)
    tyre_waste = models.BooleanField(default=False)
    remarks_tyre_waste = models.TextField(blank=True, null=True)
    e_waste = models.BooleanField(default=False)
    remarks_e_waste = models.TextField(blank=True, null=True)
    steel_scrap = models.BooleanField(default=False)
    remarks_steel_scrap = models.TextField(blank=True, null=True)
    added_by = models.IntegerField(default=0)

    def __str__(self):
        return f"WasteRecycleChecklist - AppNo: {self.AppNo}"
    

class PaymentChecklist(models.Model):
    industryid = models.IntegerField(default=0)
    AppNo = models.CharField(max_length=100, unique=True)
    declaration = models.BooleanField(default=False)
    remarks_declaration = models.TextField(blank=True, null=True)
    registration_fee_details = models.BooleanField(default=False)
    remarks_registration_fee_details = models.TextField(blank=True, null=True)   
    added_by = models.IntegerField(default=0)
class UntTrails(models.Model):
    industryid = models.IntegerField(default=0)
    AppNo = models.CharField(max_length=100)
    stateid = models.IntegerField(default=0)
    officerid = models.IntegerField(default=0)
    SPCBComments= models.TextField(null=True)
    UnitComments = models.TextField(null=True)
    EditMode = models.IntegerField(default=0)
    SPCBCommentDate = models.DateTimeField(null=True, blank=True)
    UnitCommentDate = models.DateTimeField(null=True, blank=True)
    
    





    


    




