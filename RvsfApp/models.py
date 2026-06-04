import uuid
from django.db import models
from django.forms import ValidationError
from django.core.validators import RegexValidator
from datetime import datetime  # Add this too for the current year check
import os
from registration.models import District, State
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import FileExtensionValidator
from  .validators import validate_pdf_extension, validate_file_size
from django.utils import timezone


# upload file with unique name


def consent_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"consent_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/Consent", filename)

def authorization_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"authorization_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/Authorization", filename)

def dic_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"dic_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/DICRegistration", filename)

def rvsf_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"rvsf_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/Rvsfpdf", filename)

def flow_diagram_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"flow_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/FlowDaigram", filename)

def material_balance_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"mb_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/MaterialBalance", filename)

def annual_return_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"annual_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/AnnualReturns", filename)
def annual_return_upload_path1(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"annual_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/AnnualReturns1", filename)
def annual_return_upload_path2(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"annual_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/AnnualReturns1", filename)

def equipment_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"equipment_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/equipmentspdf", filename)

def geo_video_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"geo_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("videos/geo_tagged", filename)

def approval_doc(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"approval_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/ProfileApprovals", filename)

def DeviceDoc(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"DeviceDoc_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/DeviceDoc", filename)

def AgreementDoc(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"AgreementDoc_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/AgreementDoc", filename)
def GstDoc(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"GstDoc_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/GstDoc", filename)
def PanDoc(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"PanDoc_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/PanDoc", filename)
def TinDoc(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"TinDoc_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/TinDoc", filename)
def CinDoc(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"CinDoc_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/CinDoc", filename)
def IecDoc(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"IecDoc_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("RVSFDocs/IecDoc", filename)

def unique_undertaking_path(instance, filename):
    # get file extension (e.g., .pdf)
    ext = filename.split('.')[-1]
    # generate random 10-character string
    unique_name = uuid.uuid4().hex[:10]
    # build new filename
    filename = f"{unique_name}.{ext}"
    # save under desired folder
    return os.path.join('RVSFDocs/undertaking/', filename)  

def attested_certificate_path(instance, filename):
    print('yha tk pahunch gya hu main')
    ext = filename.split('.')[-1]
    unique_name = uuid.uuid4().hex[:10]
    filename = f"attested_certificate_{instance.id}_{unique_name}.{ext}"
    print(filename)
    return os.path.join('RVSFDocs/attested_certificates/', filename)

# Create your models here.
class RvsfRegistration(models.Model):
    gst_no = models.CharField(max_length=15, unique=True)
    company_name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200)
    company_email = models.EmailField()
    business_category = models.CharField(max_length=100)
    registered_address = models.TextField()
    password_history = models.TextField(default='[]')
    state = models.CharField(max_length=50)
    district = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=6)
    website = models.URLField(blank=True, null=True)
    company_pan = models.CharField(max_length=10)
    tin_no = models.CharField(max_length=50, blank=True, null=True)
    cin = models.CharField(max_length=50, blank=True, null=True)
    iec = models.CharField(max_length=50, blank=True, null=True)
    username = models.CharField(max_length=150, unique=True , null=True)
    password = models.CharField(max_length=128, blank=True,null=True)
    auth_mobile = models.CharField(max_length=10, default=9999999999)
    auth_email = models.EmailField(default='test@gmail.com')
    authorized_person_name = models.CharField(max_length=200, blank=True)
    auth_designation = models.CharField(max_length=200, blank=True)
    auth_pan = models.CharField(max_length=10, null=True)
    disable = models.IntegerField(default=0)
    first_login = models.IntegerField(default=0)
    completed_step = models.CharField(max_length=50, default='')
    undertaking = models.FileField(upload_to=unique_undertaking_path, blank=True, null=True)
    status = models.CharField(max_length=100,null=True)
    attested_certificate = models.FileField(upload_to=attested_certificate_path, blank=True, null=True)
    attested_certificate_uploaded_at = models.DateTimeField(blank=True, null=True)



    def __str__(self):
        return self.company_name

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    


    
    
class GeneralDetails(models.Model):
    # address = models.CharField(max_length=255)
    # latitude = models.FloatField()
    # longitude = models.FloatField()
    # state = models.CharField(max_length=100 , default='NA')
    # district = models.CharField(max_length=100 ,default='NA')
    # pin_code = models.CharField(max_length=20 , default='NA')

    # cto_number = models.CharField(max_length=100)
    # consent_validity = models.DateField()
    # cto_pdf = models.FileField(upload_to=consent_upload_path, validators=[validate_file_size])

    # howm_validity = models.DateField()
    # howm_pdf = models.FileField(upload_to=authorization_upload_path, validators=[validate_file_size])

    # dic_validity = models.DateField()
    # dic_pdf = models.FileField(upload_to=dic_upload_path, validators=[validate_file_size])

    # rvsf_reg_no = models.CharField(max_length=100)
    # rvsf_validity = models.DateField()
    # rvsf_pdf = models.FileField(upload_to=rvsf_upload_path, validators=[validate_file_size])

    # process_flow_pdf = models.FileField(upload_to=flow_diagram_upload_path, validators=[validate_file_size])

    # material_balance_pdf = models.FileField(upload_to=material_balance_upload_path, validators=[validate_file_size])

    # annual_returns_pdf = models.FileField(upload_to=annual_return_upload_path, validators=[validate_file_size])
    gst_pdf = models.FileField(upload_to=GstDoc, blank=True, validators=[validate_file_size])
    pan_pdf = models.FileField(upload_to=PanDoc, blank=True, validators=[validate_file_size])
    tin_pdf = models.FileField(upload_to=TinDoc,  blank=True,validators=[validate_file_size])
    cin_pdf = models.FileField(upload_to=CinDoc, blank=True, validators=[validate_file_size])
    iec_pdf = models.FileField(upload_to=IecDoc,blank=True, validators=[validate_file_size])


    userid = models.IntegerField(default=0, unique=True)
    status = models.CharField(max_length=100,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class RvsfDetails(models.Model):
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    state = models.CharField(max_length=100 , default='NA')
    district = models.CharField(max_length=100 , default='NA')
    
    # district = models.CharField(max_length=100 ,default='NA')
    # pin_code = models.CharField(max_length=20 , default='NA')

    cto_number = models.CharField(max_length=100)
    gpcbid = models.CharField(max_length=100)
    consent_validity = models.DateField()
    cto_pdf = models.FileField(upload_to=consent_upload_path, validators=[validate_file_size])

    howm_validity = models.DateField()
    howm_pdf = models.FileField(upload_to=authorization_upload_path, validators=[validate_file_size])

    dic_validity = models.DateField()
    dic_pdf = models.FileField(upload_to=dic_upload_path, validators=[validate_file_size])

    rvsf_reg_no = models.CharField(max_length=100)
    rvsf_validity = models.DateField()
    rvsf_pdf = models.FileField(upload_to=rvsf_upload_path, validators=[validate_file_size])

    process_flow_pdf = models.FileField(upload_to=flow_diagram_upload_path, validators=[validate_file_size])

    material_balance_pdf = models.FileField(upload_to=material_balance_upload_path, validators=[validate_file_size])

    annual_returns_pdf = models.FileField(upload_to=annual_return_upload_path, validators=[validate_file_size])
    annual_returns_pdf1 = models.FileField(upload_to=annual_return_upload_path1 , validators=[validate_file_size])
    annual_returns_pdf2 = models.FileField(upload_to=annual_return_upload_path2 , validators=[validate_file_size])
    # tin_pdf = models.FileField(upload_to=TinDoc,  blank=True,validators=[validate_file_size])
    # pan_pdf = models.FileField(upload_to=PanDoc, blank=True, validators=[validate_file_size])
    # cin_pdf = models.FileField(upload_to=CinDoc, blank=True, validators=[validate_file_size])
    # gst_pdf = models.FileField(upload_to=GstDoc, blank=True, validators=[validate_file_size])
    # iec_pdf = models.FileField(upload_to=IecDoc,blank=True, validators=[validate_file_size])


    userid = models.IntegerField(default=0, unique=True)
    status = models.CharField(max_length=100,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    encorp_year = models.CharField(
        max_length=4,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{4}$',
                message='Year must be exactly 4 digits (e.g., 2022)',
                code='invalid_year'
            )
        ]
    )
    unit_commencement_year = models.CharField(
        max_length=4,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{4}$',
                message='Year must be exactly 4 digits (e.g., 2022)',
                code='invalid_year'
            )
        ]
    )
    
    def clean(self):
        """Add additional validation at model level"""
        super().clean()
        
        if self.encorp_year:
            year_int = int(self.encorp_year)
            current_year = datetime.now().year
            
            if year_int > current_year:
                raise ValidationError({
                    'encorp_year': f'Year cannot be in the future (max {current_year})'
                })
            
            if year_int < 1900:  # Adjust minimum as needed
                raise ValidationError({
                    'encorp_year': 'Year must be at least 1900'
                })




class EquipmentType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.name

class EquipmentEntry(models.Model):
    userid = models.IntegerField(default=0)
    equipment_type = models.CharField(max_length=100,null=True)
    equipment_description = models.CharField(max_length=1000,null=True)
    equipment_id = models.IntegerField(default=0)
    power_rating = models.IntegerField(default=0)
    operating_hours = models.IntegerField(default=0)
    capacity_equipment_perton = models.IntegerField(default=0)
    quantity = models.PositiveIntegerField()
    # geo_tagged_pdf = models.FileField(upload_to='RVSFDocs/equipmentspdf', validators=[validate_file_size])
    geo_tagged_pdf = models.FileField(upload_to=equipment_upload_path, validators=[validate_file_size])
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100,null=True)

    def validate_video_size(file):
     max_size_mb = 20
     if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Video file size must be under {max_size_mb} MB.")

class RvsfFacility(models.Model):
    user_id = models.IntegerField()  # Or models.ForeignKey(User, ...) if using Django's auth

    geo_video = models.FileField(upload_to=geo_video_upload_path, validators=[validate_file_size])

    total_area = models.DecimalField(max_digits=10, decimal_places=2)
    shifts_per_day = models.IntegerField()
    no_of_employees = models.IntegerField()
    sectioned_power = models.IntegerField(default=0)
    storage_parking_area = models.IntegerField(default=0)
    storage_depolluted_fluids = models.IntegerField(default=0)
    storage_hazardous_waste = models.IntegerField(default=0)
    storage_processed_scrap = models.IntegerField(default=0)
    storage_segregated_spares = models.IntegerField(default=0)
    storage_others = models.CharField(max_length=100,null=True)
    storage_others_description = models.CharField(max_length=100,null=True)
    status = models.CharField(max_length=100,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

class ProfileApproval(models.Model):
    username = models.CharField(max_length=150, unique=True , null=True)
    password = models.CharField(max_length=128, blank=True,null=True)
    auth_mobile = models.CharField(max_length=10, default=9999999999)
    auth_email = models.EmailField(default='test@gmail.com')
    approval_doc = models.FileField(upload_to=approval_doc, validators=[validate_file_size])
    Status = models.IntegerField(default=0)

class VehicleType(models.Model):
    vehicle_type = models.CharField(max_length=200, null=True)
    userid = models.IntegerField(default=0)
    Remarks = models.TextField(null=True)

class PlantCapacity(models.Model):
    installed_vehicles = models.FloatField(default=0.00)
    installed_steel = models.FloatField(default=0.00)
    operating_vehicles1 = models.FloatField(default=0.00)
    operating_vehicles2 = models.FloatField(default=0.00)
    operating_vehicles3 = models.FloatField(default=0.00)
    operating_steel1 = models.FloatField(default=0.00)
    operating_steel2 = models.FloatField(default=0.00) 
    operating_steel3 = models.FloatField(default=0.00)
    year1= models.CharField(max_length=50, null=True)
    year2= models.CharField(max_length=50, null=True)
    year3= models.CharField(max_length=50, null=True)
    userid = models.IntegerField(default=0)
    status = models.CharField(max_length=100,null=True)

class PollutionDevice(models.Model):
    userid = models.IntegerField(default=0)
    device_type = models.CharField(max_length=20, null= True)
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    device_doc = models.FileField(upload_to=DeviceDoc, null=True, blank=True)
    status = models.CharField(max_length=100,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class WasteRecycled(models.Model):
    userid = models.IntegerField(default=0)
    category = models.CharField(max_length=100)
    qty_recovered = models.FloatField()
    qty_recycled = models.FloatField()
    recycler_name = models.CharField(max_length=255)
    agreement_details = models.TextField()
    agreement = models.FileField(upload_to=AgreementDoc, null=True, blank=True)
    status = models.CharField(max_length=100,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ConfirmApplication(models.Model):
   
   STATUS_CHOICES = [
    (1, 'Submitted'),
    (2, 'Scrutiny'),
    (3, 'Inspection'),
    (4, 'Approved'),
    (5, 'Clarification Required'),
    (6, 'Response Received'),
    (7, 'Rejected'),
    ]
   userid = models.IntegerField(default=0, db_index=True)
   appno = models.CharField(max_length=100  ,null=True)
   certificateno = models.CharField(max_length=100  ,null=True)
   paymentstatus= models.IntegerField(default=0)
   paymentModeStatus = models.CharField(max_length=100, null=True)
   transactionNo = models.CharField(max_length=100 ,  default='1')
   registrationfees= models.BigIntegerField(default=0)
   state_id = models.IntegerField(default=0)
   statename = models.CharField(max_length=100 , null=True)
   role_id = models.IntegerField(default=0)
   appstatus = models.IntegerField(choices=STATUS_CHOICES, default=1)
   incomplete = models.IntegerField(default=0)
   response = models.IntegerField(default=0)
   incompleteRemark = models.TextField(null=True)
   IndustryRemark = models.TextField(null=True)
   certificateattested = models.IntegerField(default=0)
   updated_at = models.DateTimeField(auto_now=True)
   created_at = models.DateTimeField(auto_now_add=True)
   marked_to_id = models.IntegerField(default=0)  
   marked_by_id = models.IntegerField(default=0)

class PaymentLog(models.Model):
    # payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=100)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.payment.order_id} - {self.action}"


# class Payment(models.Model):
#     owner = models.ForeignKey(RvsfRegistration, on_delete=models.DO_NOTHING, blank=False, null=True)
#     order_id = models.CharField(max_length=30, unique=True)
#     txn_id = models.CharField(max_length=50, blank=True, null=True)
#     email = models.EmailField(max_length=254, blank=True, null=True)
#     amount_initiated = models.IntegerField(blank=False)
#     was_success = models.BooleanField(default=False)
#     status = models.CharField(max_length=30, blank=True, null=True)
#     log = models.TextField(null=True, blank=True)
#     registered_for = models.TextField(null=True, blank=True)
#     txn_date = models.DateTimeField(default=timezone.now, blank=True)
#     ru_date = models.DateTimeField(blank=True, null=True)
#     s2s_date = models.DateTimeField(blank=True, null=True)

#     def __str__(self):
#         return f'{self.owner.id} [{self.order_id}]'

class Payment(models.Model):
    PAYMENT_TYPES = (
        ('initial', 'Initial Payment'),
        ('additional', 'Additional Payment'),
    )
    
    owner = models.ForeignKey(RvsfRegistration, on_delete=models.DO_NOTHING, blank=False, null=True)
    order_id = models.CharField(max_length=30, unique=True)
    txn_id = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    amount_initiated = models.IntegerField(blank=False)
    was_success = models.BooleanField(default=False)
    status = models.CharField(max_length=30, blank=True, null=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='initial')
    metadata = models.JSONField(default=dict, blank=True, null=True)  # For storing additional data
    log = models.TextField(null=True, blank=True)
    registered_for = models.TextField(null=True, blank=True)
    txn_date = models.DateTimeField(default=timezone.now, blank=True)
    ru_date = models.DateTimeField(blank=True, null=True)
    s2s_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.owner.id} [{self.order_id}]'

    # class Meta:
    #     db_table = 'rvsf_payment'

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