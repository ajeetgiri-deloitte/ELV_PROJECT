from django.urls import path
from . import views

urlpatterns = [
    path("protected_cert/<path:path>/", views.protected_cert_file, name="protected_cert_file"), 
    
    # Generation and transfer module Procurement details
    path('opening-balance/', views.opening_balance, name='opening_balance'),
    path('procurement-dashboard/', views.procurement_dashboard, name='procurement_dashboard'),
    path('add-procurement-details/', views.add_procurement_details, name='add_procurement_details'),
    
    
    path("production_dashboard/", views.production_dashboard, name="production_dashboard"),
    path("production_form/", views.production_form, name="production_form"),
    path("production/save/", views.save_production_form, name="save_production_form"),

    path("waste_dashboard/", views.waste_dashboard, name="waste_dashboard"),
    path("waste_form/", views.waste_form, name="waste_form"),
    path("waste/save/", views.save_waste_form, name="save_waste_form"),
    
    path("certificate_generation_dashboard/", views.certificate_generation_dashboard, name="certificate_generation_dashboard"),
    path("certificate_generation_form/", views.certificate_generation_form, name="certificate_generation_form"),
    
    path("denominate_epr_dashboard/", views.denominate_epr_dashboard, name="denominate_epr_dashboard"),
    path("denominate/certificate/", views.denominate_epr_certificate, name="denominate_epr_certificate"),
    
    path("send-otp-transfer/", views.send_sms_otp_for_transfer, name="send_sms_otp_transfer"),
    path("verify-otp-transfer/", views.verify_otp_cert, name="verify_otp_cert"),
    
    path("certificate_transfer_dashboard/", views.certificate_transfer_dashboard, name="certificate_transfer_dashboard"),
    path("transfer_certificate/", views.transfer_certificate, name="transfer_certificate"),
    
    path("certificate_details/", views.certificate_details, name="certificate_details"),
    

    
    
    
    
]