from django.urls import path
from . import views


urlpatterns = [
    
    # ---------------------------------------------------- Auth ------------------------------------------------------------------- #
    path('', views.home, name='home'),
    path('save-cookie-consent/', views.save_cookie_consent, name='save_cookie_consent'),
    path('verify_otp1', views.verify_otp1 , name='verify_otp1'),
    path('otpviewpage1', views.otpviewpage1, name='otpviewpage1'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('national-dashboard/', views.national_dashboard, name='national_dashboard'),
    path('national-dashboard/applications/', views.applications_list, name='applications_list'),
    path("login/", views.home, name="login"),
    path('refresh-captcha/', views.refresh_captcha, name='refresh_captcha'),
    path("logout/", views.producer_logout, name="producer_logout"),
    
    path('login/change-password/', views.ChangePasswordFirst.as_view(), name='change_password_first'),

    path('verify_consent/', views.verify_consent, name='verifyconsent_detail'),

    path('contact-us/', views.contact_us, name='contact_us'),
    
    path('termsAndCondition/', views.termsAndCondition, name='termsAndCondition'),
    path('refundPolicy/', views.refundPolicy, name='refundPolicy'),
    path('privacyPolicy/', views.privacyPolicy, name='privacyPolicy'),
    
    path('forgetPassword/',views.forget_password , name='forget_password'),
    path('resetPassword/',views.reset_password , name='reset_password'),
    
    path('important-communications/', views.important_communications, name='important_communications'),
    
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/', views.resetPassword, name='resetPassword'),
    path('custom_reset_password/<uidb64>/<token>/', views.custom_reset_password, name='custom_reset_password'),
    
    path("protected_producer/<path:path>/", views.protected_file, name="protected_file"), 
    
    
    
    
    #  ------------------------------------------------- Signup ------------------------------------------------------------- #
    path('register/', views.RegistrationView.as_view(), name='signup'),
    path("fetch-gst-details/", views.fetch_gst_details, name="fetch-gst-details"),
    path('load-districts/', views.load_districts, name='load_districts'), 
    path('generate-otp/', views.GenerateOTPView.as_view(), name='generate_otp'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify_producer_otp'),
    path("resend-otp/", views.resend_otp1, name="resend_otp1"),
    path("resend_otp/", views.resend_otp, name="resend_otp"),
    
    
    
    # ---------------------------------------------------------- Producer dashboard & Forms -----------------------------------#
    path('producer/profile/', views.producer_profile, name='producer_profile'),
    path('dashboard/producer/', views.producer_dashboard, name='producer_dashboard'),
    path('reg-application/', views.reg_application, name='reg_application'),
    path('get_last_comment/<int:user_id>/', views.get_last_comment, name='get_last_comment'),
    path('get_trail/<int:user_id>/', views.get_trail, name='get_trail'),
    path('view-certificate/', views.view_certificate, name='view_producer_certificate'),
    
    path('get-progress/', views.get_user_progress, name='get_user_progress'),
    path('update-progress/', views.update_user_progress, name='update_user_progress'),
    
    path('producer/', views.producer, name='producer'),
    path('producer/general/', views.producergeneral, name='producergeneral'),
    path('save-facility-status/', views.save_manufacturing_status, name='save_manufacturing_status'),
    path('delete-facility-row/', views.delete_facility_row, name='delete_facility_row'),
    path('get-facility/<int:facility_id>/', views.get_facility, name='get_facility'),
    path('update-facility/', views.update_facility, name='update_facility'),
    path('submit-sales-summary/', views.submit_sales_summary, name='submit_sales_summary'),
    path('submit-sales-data/', views.submit_sales_data, name='submit_sales_data'),
    path('save-vehicle-data/', views.save_vehicle_data, name='save_vehicle_data'),
    path('producerdeclaration/', views.producerdeclaration, name='producerdeclaration'),
    path('delete-vehicle-type-data/', views.delete_vehicle_type_data, name='delete_vehicle_type_data'),
    
    
    # -------------------------------------------------------- Payment -------------------------------------------------------- #
    path('payment/initiate/', views.initiate_payment, name='initiatePayment'),
    path('payment/response/', views.payment_response, name='payment_response'),
    path('payment/receipt/', views.payment_receipt, name='payment_receipt'),
    path("payment-result/", views.payment_result, name="payment_result"),


    
    # -------------------------------------------------- Edit ----------------------------------------- #
    path('finalsubmit/', views.finalsubmit, name='final_submit'),
    
    
    
    
    # ------------------------------------------------------------ Consumer & Rvsfs ------------------------------------ #
    path('dashboard/consumer/', views.consumer_dashboard, name='consumer_dashboard'),
    path('dashboard/rvsf/', views.rvsf_dashboard, name='rvsf_dashboard'),
    path('reg-bulk-consumer-application/', views.reg_bulk_consumer_application, name='reg_bulk_consumer_application'),
    path('reg-rvsf-application/', views.reg_rvsf_application, name='reg_rvsf_application'),
    
    path("receive-certificates/", views.receive_certificates, name="receive_certificates"),
    path("mark_certificate_transferred/", views.mark_certificate_transferred, name="mark_certificate_transferred"), 
    path("send-otp-transfer-certificate/", views.send_sms_otp_for_transfer_certificate, name="send_sms_otp_for_transfer_certificate"),
    path("verify-otp-certificate/", views.verify_otp_certificate, name="verify_otp_certificate"),

]
