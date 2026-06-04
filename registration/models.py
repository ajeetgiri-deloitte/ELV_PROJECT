# models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random

from django.contrib.auth.models import AbstractUser



class OtherProducerExcelData(models.Model):
    producer = models.ForeignKey('producerGeneralDetails', on_delete=models.CASCADE, related_name='otherproducerexcel')
    sales_data = models.ForeignKey('ProducerSalesData', on_delete=models.CASCADE, related_name='otherproducerexcelsales')
    producer_name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    gst = models.CharField(max_length=50, blank=True, null=True)
    mobile_no = models.CharField(max_length=20, blank=True, null=True)
    email_id = models.EmailField(blank=True, null=True)
    vehicle_category = models.CharField(max_length=50, blank=True, null=True)
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    other_vehicle_type = models.CharField(max_length=255, blank=True, null=True)
    hsn_code = models.CharField(max_length=50, blank=True, null=True)
    no_of_vehicle_sold = models.IntegerField(blank=True, null=True)
    total_weight_vehicles = models.FloatField(blank=True, null=True)
    total_weight_steel_used = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.producer_name} - {self.vehicle_type}"

class CobrandedExcelData(models.Model):
    producer = models.ForeignKey('producerGeneralDetails', on_delete=models.CASCADE, related_name='cobrandedexcel')
    sales_data = models.ForeignKey('ProducerSalesData', on_delete=models.CASCADE, related_name='cobrandedexcelsales')
    cobrand_partners_name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    gst = models.CharField(max_length=50, blank=True, null=True)
    mobile_no = models.CharField(max_length=20, blank=True, null=True)
    email_id = models.EmailField(blank=True, null=True)
    cobrand_share_percentage = models.FloatField(blank=True, null=True)
    manufactured_facility = models.CharField(max_length=50, blank=True, null=True)
    vehicle_category = models.CharField(max_length=50, blank=True, null=True)
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    other_vehicle_type = models.CharField(max_length=255, blank=True, null=True)
    hsn_code = models.CharField(max_length=50, blank=True, null=True)
    no_of_vehicle_sold = models.IntegerField(blank=True, null=True)
    total_weight_vehicles = models.FloatField(blank=True, null=True)
    total_weight_steel_used = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.producer_name} - {self.vehicle_type}"

class State(models.Model):
    state_id = models.AutoField(primary_key=True)
    state_name = models.CharField(max_length=255)
    country_id = models.IntegerField()  # Assuming country_id is an integer
    state_url = models.TextField(null=True)
    status = models.BooleanField(default=True)  # Assuming status is active/inactive

    class Meta:
        db_table = 'tbl_state'
        verbose_name = 'State'
        verbose_name_plural = 'States'

    def __str__(self):
        return self.state_name

class District(models.Model):
    city_id = models.AutoField(primary_key=True)
    city_name = models.CharField(max_length=255)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='districts')

    class Meta:
        db_table = 'cities'  # Adjust table name if needed
        verbose_name = 'District'
        verbose_name_plural = 'Districts'

    def __str__(self):
        return self.city_name

class OTP(models.Model):
    TYPE_CHOICES = [
        ('company_email', 'Company Email'),
        ('authorized_person_email', 'Authorized Person Email'),
        ('authorized_person_mobile', 'Authorized Person Mobile'),
    ]
    
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)  # Type of OTP (email/mobile)
    authorization = models.CharField(max_length=255)  # Email or mobile number
    otp = models.CharField(max_length=6, blank=True, null=True)  # OTP value
    otp_verified = models.BooleanField(default=False)  # OTP verification status
    otp_expires_at = models.DateTimeField(null=True, blank=True)  # Expiry time of OTP
    created_at = models.DateTimeField(auto_now_add=True)  # When the OTP was generated

    def generate_otp(self):
        """Generate a new OTP and set expiration time."""
        # self.otp = str(random.randint(100000, 999999))
        self.otp = "123456"
        self.otp_expires_at = timezone.now() + timedelta(minutes=15)
        self.save()

class Registration(models.Model):
    ENTITY_TYPES = (
        (3, 'Producer'),
        (2, 'Bulk Consumer'),
        (1, 'RVSFs'),
    )
    
    # NATURE_OF_BUSINESS = (
    #     (1, 'Manufacturing and Sale of Vehicles under Own Brand'),
    #     (2, 'Assembly and Sale of Vehicles under Own Brand'),
    #     (3, 'Sale of Vehicles under Own Brand (Manufactured by Another Manufacturer)'),
    #     (4, 'Import of Vehicles and sale Under Own brand'),
    #     (5, 'Import of Vehicles and sale Under Other Brand'),
    #     (6, 'Import of Vehicles for Self Use'),
    # )

    BUSINESS_CATEGORIES = (
        ('Government Agency', 'Government Agency'),
        ('Government-Owned Enterprise (Govt. / PSU)', 'Government-Owned Enterprise (Govt. / PSU)'),
        ('Private Limited Company (Ltd.)', 'Private Limited Company (Ltd.)'),
        ('Proprietorship/Partnership Firm', 'Proprietorship/Partnership Firm'),
        ('Limited Liability Partnership (LLP)', 'Limited Liability Partnership (LLP)'),
        ('Cooperative Society/Trust', 'Cooperative Society/Trust'),
    )

    entity_types = models.CharField(max_length=10, blank=True)
    gst_no = models.CharField(max_length=15, unique=True, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    legal_name = models.CharField(max_length=200, blank=True)
    company_email = models.EmailField(blank=True)
    # incorporation_date = models.DateField(null=True, blank=True)
    business_category = models.CharField(max_length=50, choices=BUSINESS_CATEGORIES, blank=True)
    # nature_of_business = models.CharField(max_length=20, blank=True)
    registered_address = models.TextField(blank=True)
    state = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    pin_code = models.CharField(max_length=6, blank=True)
    website = models.URLField(blank=True, null=True)
    pan_no = models.CharField(max_length=10, blank=True)
    tin = models.CharField(max_length=20, blank=True)
    cin = models.CharField(max_length=21, blank=True)
    # iec = models.CharField(max_length=10, blank=True)
    
    authorized_person_name = models.CharField(max_length=200, blank=True)
    authorized_person_designation = models.CharField(max_length=200, blank=True)
    authorized_person_email = models.EmailField(blank=True)
    authorized_person_mobile = models.CharField(max_length=15, blank=True)
    authorized_person_pan = models.CharField(max_length=10, blank=True)
    
    username = models.CharField(max_length=50, blank=True)  # Add this
    password = models.CharField(max_length=100, blank=True)  # Store raw or hashed as per your need
    password_history = models.TextField(default='[]')
    first_login = models.IntegerField(default=0)
    completed_step = models.CharField(max_length=50, default='')
    status = models.IntegerField(default=0)
    application_submitted = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.company_name} - {self.gst_no}"
    
    def get_entity_type_names(self):
        entity_dict = dict(self.ENTITY_TYPES)
        entity_ids = self.entity_types.split(',') if self.entity_types else []
        return [entity_dict.get(int(eid)) for eid in entity_ids if eid.isdigit()]

    # def get_nature_of_business_names(self):
    #     nature_dict = dict(self.NATURE_OF_BUSINESS)
    #     nature_ids = self.nature_of_business.split(',') if self.nature_of_business else []
    #     return [nature_dict.get(int(nid)) for nid in nature_ids if nid.isdigit()]

class producerGeneralDetails(models.Model):
    # Entity Details
    gst_no = models.CharField(max_length=15, unique=True)
    gst_doc = models.FileField(upload_to='documents/gst/')
    company_name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255)
    company_email = models.EmailField()
    incorporation_date = models.IntegerField()
    business_category = models.CharField(max_length=255)
    registered_address = models.TextField()
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)
    website = models.URLField(blank=True, null=True)

    # Company Identifiers
    pan_no = models.CharField(max_length=10)
    pan_doc = models.FileField(upload_to='documents/company_pan/')
    tin = models.CharField(max_length=20, blank=True, null=True)
    tin_doc = models.FileField(upload_to='documents/tin/')
    cin = models.CharField(max_length=21, blank=True, null=True)
    cin_doc = models.FileField(upload_to='documents/cin/')
    iec = models.CharField(max_length=20, blank=True, null=True)
    iec_doc = models.FileField(upload_to='documents/iec/')

    # Authorized Person Details
    authorized_person_name = models.CharField(max_length=255)
    authorized_person_designation = models.CharField(max_length=255)
    authorized_person_email = models.EmailField()
    authorized_person_mobile = models.CharField(max_length=15)
    authorized_person_pan = models.CharField(max_length=10)

    # Uploaded Document
    doc = models.FileField(upload_to='documents/auth_person_pan')
    user_type = models.CharField(max_length=10)
    status = models.IntegerField(default=0)
    forwarded_to = models.IntegerField(default=0)
    application_type = models.IntegerField(default=0)
    
    # has_facility = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')], default='No')
    application_submitted = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} ({self.gst_no})"

class ManufacturingDetails(models.Model):
    NATURE_OF_BUSINESS = (
        (1, 'P-1: Manufactured/assemble and Sale of Vehicles under Own Brand'),
        (2, 'P-2: Sale of Vehicles under Own Brand (Manufactured/assembled by Another Manufacturer)'),
        (3, 'P-3: Manufacture/assemble of vehicles and sold to another producer'),
        (4, 'P-4: Manufacture/assemble of vehicles and sold in open market with another producer brand.'),
        (5, 'P-5: Import of Vehicles and sale Under Own brand'),
        (6, 'P-6: Import of Vehicles and sale Under imported brand itself.'),
        (7, 'P-7: Import of Vehicles and sale to other producer.'),
        (8, 'P-8: Import of Vehicles for Self Use.'),
    )
    
    producer = models.ForeignKey('producerGeneralDetails', on_delete=models.CASCADE, related_name='facilities')
    
    # Nature of Business – store as comma-separated values
    nature_of_business = models.CharField(max_length=255)  # Could also use ManyToManyField with a separate model
    has_facility = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')], default='No')

    created_at = models.DateTimeField(auto_now_add=True)

    def get_nature_of_business_names(self):
        nature_dict = dict(self.NATURE_OF_BUSINESS)
        nature_ids = self.nature_of_business.split(',') if self.nature_of_business else []
        return [nature_dict.get(int(nid)) for nid in nature_ids if nid.isdigit()]
    
class ManufacturingFacilityDetails(models.Model):
    ACTIVITY_CHOICES = [
        ('Manufacturing', 'Manufacturing of vehicles'),
        ('Assembly', 'Assembly of vehicles'),
    ]
    
    producer = models.ForeignKey('producerGeneralDetails', on_delete=models.CASCADE, related_name='manyfacturingfacilities')
    manufacturer = models.ForeignKey('ManufacturingDetails', on_delete=models.CASCADE, related_name='facilitiesdetails')
    
    name = models.CharField(max_length=255)
    address = models.TextField()
    state = models.CharField(max_length=100, blank=True)
    gstin = models.CharField(max_length=15)
    year_of_establishment = models.PositiveIntegerField()

    # These are optional and shown conditionally based on activity types
    manufacturing_capacity = models.CharField(max_length=255, blank=True, null=True)
    assembly_capacity = models.CharField(max_length=255, blank=True, null=True)

    # To track selected activity types (multi-choice)
    activity_types = models.JSONField(default=list)  # stores e.g., ["Manufacturing", "Assembly"]
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class ProducerSalesSummary(models.Model):
    CATEGORY_CHOICES = [
        ('transport', 'Transport'),
        ('non_transport', 'Non-Transport'),
    ]

    producer = models.ForeignKey('producerGeneralDetails', on_delete=models.CASCADE, related_name='sales_summaries')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    financial_year = models.CharField(max_length=9)  # e.g., "2024-25"
    total_epr_target = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    ca_certificate = models.FileField(upload_to='ca_certificates/')

    class Meta:
        unique_together = ('producer', 'category', 'financial_year')


class ProducerSalesData(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('2W', '2 Wheeler'),
        ('3W', '3 Wheeler'),
        ('LMV', 'Light Motor Vehicle'),
        ('MMV', 'Medium Motor Vehicle'),
        ('HMV', 'Heavy Motor Vehicle'),
        ('Other', 'Other'),
    ]

    CATEGORY_CHOICES = [
        ('transport', 'Transport'),
        ('non_transport', 'Non-Transport'),
    ]

    producer = models.ForeignKey('producerGeneralDetails', on_delete=models.CASCADE, related_name='vehicle_sales')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    financial_year = models.CharField(max_length=9)  # e.g., "2024-25"
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPE_CHOICES)

    # Manufacturing / Procurement
    no_of_vehicles_manufactured = models.PositiveIntegerField(default=0)
    no_of_vehicles_imported = models.PositiveIntegerField(default=0)
    no_of_vehicles_procurred_domestically = models.PositiveIntegerField(default=0)

    # Open Market Sales
    open_market_vehicles = models.PositiveIntegerField(default=0)
    open_market_vehicle_weight = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    open_market_steel_weight = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    open_market_brand_name = models.CharField(max_length=100, blank=True)

    # Other Producer Sales
    producer_vehicles = models.PositiveIntegerField(default=0)
    producer_vehicle_weight = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    producer_steel_weight = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    producer_sale_file = models.FileField(upload_to='producer_sale_files/', blank=True, null=True)

    # Co-branded Sales
    cobranded_vehicles = models.PositiveIntegerField(default=0)
    cobranded_vehicle_weight = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    cobranded_steel_weight = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    cobranded_brand_name = models.CharField(max_length=100, blank=True)
    cobranded_partner_file = models.FileField(upload_to='cobranded_partner_files/', blank=True, null=True)

    # Self Use
    selfuse_vehicles = models.PositiveIntegerField(default=0)
    selfuse_vehicle_weight = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    selfuse_steel_weight = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    # Exports
    export_vehicles = models.PositiveIntegerField(default=0)

    # EPR Obligations
    vehicle_number_qty = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    vehicle_weight_qty = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    epr_qty = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    epr_target = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)



class ProducerDeclaration(models.Model):
    producer = models.ForeignKey('producerGeneralDetails', on_delete=models.CASCADE, related_name='declaration')
    turnover_23_24 = models.DecimalField(max_digits=15, decimal_places=2)
    turnover_24_25 = models.DecimalField(max_digits=15, decimal_places=2)
    undertaking_file = models.FileField(upload_to='undertakings/')
    ca_certificate_23_24 = models.FileField(upload_to='ca_certs/')
    ca_certificate_24_25 = models.FileField(upload_to='ca_certs/')
    declaration = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    



class Transaction(models.Model):
    owner = models.ForeignKey(producerGeneralDetails, on_delete=models.DO_NOTHING, blank=False, null=True)
    order_id = models.CharField(max_length=30, unique=True)
    txn_id = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    amount_initiated = models.IntegerField(blank=False)
    was_success = models.BooleanField(default=False)
    status = models.CharField(max_length=30, blank=True, null=True)
    log = models.TextField(null=True, blank=True)
    registered_for = models.TextField(null=True, blank=True)
    txn_date = models.DateTimeField(default=timezone.now, blank=True)
    ru_date = models.DateTimeField(blank=True, null=True)
    s2s_date = models.DateTimeField(blank=True, null=True)
    
    # Payment snapshot fields
    turnover_23_24 = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    turnover_24_25 = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_turnover = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    average_turnover = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    additional_registration_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    

    def __str__(self):
        return f'{self.owner.id} [{self.order_id}]'
    
    class Meta:
        db_table = 'registration_transaction'
    


class ProducerRegistrationFee(models.Model):
    min_turnover = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    max_turnover = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    registration_fee = models.IntegerField()

    def __str__(self):
        return f"{self.min_turnover} - {self.max_turnover} => ₹{self.registration_fee}"


class RVSFRegistrationFee(models.Model):
    min_turnover = models.IntegerField(null=True, blank=True)
    max_turnover = models.IntegerField(null=True, blank=True)
    registration_fee = models.IntegerField()

    def __str__(self):
        return f"{self.min_turnover} - {self.max_turnover} ELVs => ₹{self.registration_fee}"
    


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