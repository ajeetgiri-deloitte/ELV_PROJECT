from django.urls import path
from . import views

urlpatterns = [
    path('', views.rvsf_home, name='rvsf_home'),  # e.g., domain.com/rvsf/
    path('login/change_password/', views.ChangePasswordFirst.as_view(), name='change-password-first'),
    path('change-password1/', views.ChangePasswordView.as_view(), name='change-password1'),
    path('verify_otp', views.verify_otp , name='verify_otp'),

    path('api/states/', views.states_api, name='states_api'),
    
    path('generate-otp1/', views.GenerateOTPView.as_view(), name='generate_otp1'),
    path('verify-otp/', views.VerifyOTPView1.as_view(), name='verify_otp2'),
    path('otpviewpage', views.otpviewpage, name='otpviewpage'), #this is otpverify view
    # path("signup", views.rvsf_signup_view, name="rvsf_signup"),
    path("signup", views.RegistrationrvsfView.as_view(), name="rvsf_signup"),
    path('dashboard/', views.dashboard, name='rvsf_dashboard'),  # e.g., domain.com/rvsf/dashboard/
    path('check-user-status/', views.check_user_status, name='check_user_status'),
    path('fetch-gst-details', views.fetch_gst,name='fetchgst'),
    path('generaldetails', views.generaldetails,name='generaldetails'),
    path('capacityanddeclaration', views.capacity_declaration,name='capacityanddeclaration'),
    path('paymentsection', views.payment_section,name='paymentsection'),
    # path('initiate-additional-payment/', views.initiateAdditionalPayment, name='initiateAdditionalPayment'),
    path('rvsfdetails', views.rvsfdetails,name='rvsfdetails'),
    path('equipmentDetails', views.equipmentdetails,name='equipmentDetails'),
    path('delequipment',views.delequipment, name="delequipment"),
    path('facilityDetails', views.facilityDetails,name='facilityDetails'),
    path('Capacity', views.RvsfCapacity,name='Capacity'),
    path('PCD', views.fetch_gst,name='PCD'),
    path('edit_profile',views.edit_profile, name="edit_profile"),
    path('send-verification-otp11/', views.send_verification_otp11, name='send_verification_otp11'),
    path('verify-otp11/', views.verify_otp11, name='verify_otp11'),
    
    path('logoutrvsf', views.logoutrvsf, name='logoutrvsf'),
    path('check-username/', views.check_username, name='check_username'),
    path('AddVehicleType',views.AddVehicleType , name='AddVehicleType'),
    path('delete-vehicle-type/', views.delete_vehicle_type, name='delete_vehicle_type'),
    path('submit-plant-capacity/', views.submit_plant_capacity, name='submit_plant_capacity'),
    path('pollutiondetails', views.pollutiondetails, name="pollutiondetails"),
    path('add_device', views.add_device, name='add_device'),
    path('removedevice', views.delete_device, name='deletedevice'),
    path('add_waste', views.add_waste , name='add_waste'),
    path('delete_waste', views.delete_waste,name='delete_waste'),
    path('confirm', views.confirmapp, name='confirm'),
    path('postconfirmapp', views.postconfirmapp , name='postconfirmapp'),
    path('TrackApplication',views.track_application, name='TrackApplication'),
    path('viewchecklist', views.viewchecklist , name='viewchecklist'),
    path('viewchecklist1', views.viewchecklist1 , name='viewchecklist1'),
    path('resubmit_application', views.resubmit_application , name='resubmit_application'),
    # This Urls is created for edit application after recieving checklist
    path('editGeneralDetails', views.editGeneralDetails , name='editGeneralDetails'),
    path('AddGeneralDetails', views.AddGeneralDetails , name='AddGeneralDetails'),
    path('editEquipmentDetails' ,views.editEquipmentDetails, name='editEquipmentDetails'),
    path('AddRvsfFacility', views.AddRvsfFacility , name='AddRvsfFacility'),
    path('AddEquipmentDetails' , views.AddEquipmentDetails , name='AddEquipmentDetails'),
    path('editPollutionDetail', views.editPollutionDetail , name='editPollutionDetail'),
    path('viewRvsfCapacity' , views.viewRvsfCapacity , name='viewRvsfCapacity'),
    path('AddResponse' , views.AddResponse , name='AddResponse'),
    path('AddFinalResponse', views.AddFinalResponse, name='AddFinalResponse'),
    path('submittedapplication' , views.submittedapplication , name='submittedapplication'),
    path('forgetpassword',views.forgetpassword , name='forgetpassword'),
    path('resetpassword',views.resetpassword , name='resetpassword'),
    path("resend_otp_rvsf/", views.resend_otp_rvsf, name="resend_otp_rvsf"),
    

    path('payment/initiate/', views.initiate_rvsf_payment, name='initiateRvsfPayment'),
    path('payment/status/', views.paymentResponse, name='paymentResponse'),
    path('payment/reciept/', views.paymentreciept, name='paymentreciept'),
    path("consent/details/", views.get_consent_details, name='consent_dtails'),

    path("protected_rvsf/<path:path>/", views.protected_file, name="protected_file_rvsf"),

    # Transfer Certificate #
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
