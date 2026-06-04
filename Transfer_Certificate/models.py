from django.db import models
from RvsfApp.models import RvsfRegistration
from datetime import timedelta, date
from django.core.validators import RegexValidator, MinValueValidator, FileExtensionValidator
from django.utils import timezone


# -------------------------------------------
# PROCUREMENT DETAILS
# -------------------------------------------

class FinancialYear(models.Model):
    rvsf = models.ForeignKey(RvsfRegistration, on_delete=models.CASCADE)
    financial_year = models.CharField(max_length=12)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('rvsf', 'financial_year')
        db_table = 'Transfer_Certificate_FY'

    def __str__(self):
        return f"{self.rvsf} - {self.financial_year}"


class OpeningBalance(models.Model):
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)   # e.g. 2025-2026
    elv_type = models.CharField(max_length=50)        
    opening_balance_quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('financial_year', 'elv_type')
        db_table = 'Transfer_Certificate_openingbalance'

    def __str__(self):
        return f"{self.rvsf} - {self.financial_year} - {self.elv_type}"


class ProcurementData(models.Model):
    # -----------------------------
    # Procurement Types
    # -----------------------------
    PROCUREMENT_TYPE_CHOICES = (
        ("ELV", "Source of ELV"),
        ("AUTOMOBILE", "Automobile Steel Scrap"),
    )

    COLLECTION_TYPE_CHOICES = (
        ("collection_centre", "Collection Centre"),
        ("bulk_consumer", "Bulk Consumer"),
        ("owner_elv", "Owner of ELV"),
        ("insurance_company", "Insurance Company"),
        ("producer", "Producer"),
    )

    # -----------------------------
    # Parent Fields
    # -----------------------------
    rvsf = models.ForeignKey(RvsfRegistration, on_delete=models.CASCADE)
    financial_year = models.CharField(max_length=12)
    procurement_date = models.DateField()
    procurement_type = models.CharField(max_length=10, choices=PROCUREMENT_TYPE_CHOICES)
    collection_type = models.CharField(max_length=50, choices=COLLECTION_TYPE_CHOICES)

    # -----------------------------
    # Source Details (dynamic)
    # -----------------------------
    source_name = models.CharField(max_length=200, blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_registered = models.BooleanField(null=True, blank=True)

    # -----------------------------
    # Vehicle / Scrap Details
    # -----------------------------
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    fuel_type = models.CharField(max_length=50, blank=True, null=True)
    number_of_elvs = models.IntegerField(blank=True, null=True)

    # -----------------------------
    # Invoice / Certificate
    # -----------------------------
    certificate_of_deposit = models.FileField(upload_to="procurement/certificates/", blank=True, null=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    invoice_file = models.FileField(upload_to="procurement/invoices/", blank=True, null=True)

    # -----------------------------
    # Timestamps
    # -----------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.procurement_type} - {self.source_name} - {self.financial_year}"





# -------------------------------------------
# PRODUCTION DETAILS 
# -------------------------------------------

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    
    class Meta:
        db_table = 'Transfer_Certificate_Category'
        app_label = 'Transfer_Certificate'


class ProductionForm(models.Model):
    rvsf = models.ForeignKey(RvsfRegistration, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="production_entries")
    scrapping_date = models.DateField()

    # -------- ELV FIELDS --------
    elv_type = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    scrapped_qty = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    scrapped_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True
    )

    # -------- AUTOMOBILE SCRAP --------
    automobile_scrap_processed = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True
    )

    # -------- COMMON SCRAP DATA --------
    steel_scrap_recovered = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )

    other_scrap_recovered = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        null=True,
        blank=True
    )

    cert_generating_potential = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )
    financial_year = models.CharField(max_length=12)
    # -------- META --------
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} | {self.scrapping_date}"

    class Meta:
        db_table = 'Transfer_Certificate_ProductionForm'
        app_label = 'Transfer_Certificate'


# models.py

class OtherScrap(models.Model):
    rvsf = models.ForeignKey(
        RvsfRegistration,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    production = models.ForeignKey(
        'ProductionForm',
        on_delete=models.CASCADE,
        related_name='other_scraps'
    )

    wasteType = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    financial_year = models.CharField(max_length=12)
    created_at = models.DateTimeField(auto_now_add=True)



class SteelScrapSale(models.Model):
    # ===============================
    # USER / RVSF
    # ===============================
    rvsf_id = models.IntegerField(db_index=True)

    # ===============================
    # SALE DETAILS
    # ===============================
    sale_date = models.DateField(default=timezone.now)

    buyer_type = models.CharField(max_length=100)

    buyer_name = models.CharField(max_length=255)
    buyer_address = models.TextField()

    # GST (15 DIGIT VALIDATION)
    gst_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$',
                message="Enter a valid 15-character GST number"
            )
        ]
    )

    email = models.EmailField()

    # ===============================
    # INVOICE & QUANTITY
    # ===============================
    quantity_sold = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )

    invoice_amount = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )

    invoice_number = models.CharField(max_length=100)

    invoice_pdf = models.FileField(
        upload_to="steel_scrap_invoices/",
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf"])
        ]
    )
    financial_year = models.CharField(max_length=12)
    # ===============================
    # META
    # ===============================
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Transfer_Certificate_steel_scrap_sale"
        ordering = ["-sale_date"]

    def __str__(self):
        return f"{self.invoice_number} - {self.buyer_name}"



class WasteProcessing(models.Model):

    ACTIVITY_CHOICES = [
        ("recycled", "Recycled"),
        ("refurbish", "Refurbish"),
        ("disposal", "Disposal"),
    ]

    # -------- RELATION --------
    rvsf_id = models.IntegerField(db_index=True)

    # -------- WASTE DETAILS --------
    waste_type = models.CharField(
        max_length=100,
        help_text="Fetched dynamically from OtherScrap"
    )

    activity = models.CharField(
        max_length=20,
        choices=ACTIVITY_CHOICES
    )

    # -------- COMPLIANCE DOCUMENTS --------
    agreement_tsdf_certificate = models.FileField(
        upload_to="waste_tsdf_certificates/",
        help_text="Agreement copy or TSDF membership certificate",
        null=True,
        blank=True
    )
    manifest_document = models.FileField(
        upload_to="waste_manifest/",
        null=True,
        blank=True
    )

    processed_qty = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )

    # -------- RECEIVER / BUYER DETAILS --------
    buyer_name = models.CharField(
        max_length=255
    )

    # GST (15 DIGIT VALIDATION)
    gst_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$',
                message="Enter a valid 15-character GST number"
            )
        ]
    )

    buyer_address = models.TextField(
        null=True,
        blank=True
    )

    buyer_email = models.EmailField(
        null=True,
        blank=True
    )

    # -------- SALE / INVOICE DETAILS --------
    sale_date = models.DateField()

    invoice_number = models.CharField(
        max_length=100
    )

    invoice = models.FileField(
        upload_to="waste_invoice/"
    )
    financial_year = models.CharField(max_length=12)
    # -------- META --------
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.waste_type} | {self.activity} | {self.sale_date}"

    class Meta:
        db_table = 'Transfer_Certificate_waste_processing'
        app_label = 'Transfer_Certificate'


class DenominatedCertificate(models.Model):
    id = models.AutoField(primary_key=True)
    rvsf_id = models.IntegerField()
    total_certificate_value_denominated = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )
    # denomination_date = models.DateField(auto_now_add=True)
    denomination_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True,
        blank=True)   # 👈 NEW COLUMN
    financial_year = models.CharField(max_length=12)

    def save(self, *args, **kwargs):

        if not self.expiry_date and self.financial_year:

            # Extract start year from "2025-2026"
            start_year = int(self.financial_year.split("-")[0])

            # Add 5 years
            expiry_year = start_year + 5

            # Expiry at end of financial year (31 March)
            self.expiry_date = date(expiry_year + 1, 3, 31)

        super().save(*args, **kwargs)
            
    def __str__(self):
        return f"RVSF {self.rvsf_id} - {self.total_certificate_value_denominated} MT"


class DenominationDetail(models.Model):
    STATUS_CHOICES = [
        ("generated", "Generated"),
        ("under_transfer", "Under Transfer"),
        ("transferred", "Transferred"),
        ("reverted", "reverted")
    ]
    
    id = models.AutoField(primary_key=True)
    denomination_master = models.ForeignKey(
        DenominatedCertificate,
        on_delete=models.CASCADE,
        related_name="denomination_details"
    )
    rvsf_id = models.IntegerField()
    denomination_kg = models.IntegerField()   # 100,200,500...
    quantity = models.IntegerField()
    unique_id = models.CharField(max_length=100, unique=True)

    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="generated")
    def __str__(self):
        return self.unique_id
    
    
# class CertificateTransfer(models.Model):

#     id = models.AutoField(primary_key=True)

#     denomination_detail = models.ForeignKey(
#         DenominationDetail,
#         on_delete=models.CASCADE,
#         related_name="transfers"
#     )

#     producer_id = models.IntegerField()

#     transfer_date = models.DateField(default=timezone.now)
#     rvsf_id = models.IntegerField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Transfer of {self.denomination_detail.unique_id} to Producer {self.producer_id}"
    
import uuid

class CertificateTransaction(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    producer_id = models.IntegerField()
    rvsf_id = models.IntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.transaction_id)        
    

class CertificateTransfer(models.Model):

    denomination_detail = models.ForeignKey(
        DenominationDetail,
        on_delete=models.CASCADE,
        related_name="transfers"
    )

    transaction = models.ForeignKey(
        CertificateTransaction,
        on_delete=models.CASCADE,
        related_name="transfers"
    )

    status = models.CharField(
        max_length=20,
        default="pending"
    )

    transfer_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Transfer of {self.denomination_detail.unique_id} "
    
    
