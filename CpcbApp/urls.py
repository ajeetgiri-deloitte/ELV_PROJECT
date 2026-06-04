from django.urls import path
from . import views

urlpatterns = [
    # ------------------------------------------------------ Admin ----------------------------------------------------------------- #
    path('', views.custom_admin_login, name='custom_admin_login'),
    path('change-password/', views.ChangeAdminPasswordFirst.as_view(), name='change_admin_password_first'),
    
    path('forgetCpcbPassword/',views.forget_cpcb_password , name='forget_cpcb_password'),
    path('resetCpcbPassword/',views.reset_cpcb_password , name='reset_cpcb_password'),
    
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('createuser/', views.create_user, name='create_user'),
    path('view_accounts/', views.view_user, name='view_user'),
    path('users/toggle/', views.toggle_user_status, name='toggle_user_status'),
    path('users/toggle/spcb', views.toggle_spcb_user_status, name='toggle_spcb_user_status'),
    path('cpcb_profile/', views.cpcb_profile , name='ViewCpcbProfile'),
    path('updatecpcbprofile/', views.updatecpcbprofile,name='updatecpcbprofile' ),
    path('allproducers/', views.admin_producer, name='admin_producers'),
    path('producers/', views.producer_details, name='producer_details'),
    path('producers/total/', views.producer_detail, name='producer_detail'),
    path('users/', views.all_users, name='all_users'),
    
    path('payment/receipt/', views.payment_receipt_admin, name='payment_receipt_admin'),
    path('get-applications/<int:user_id>/', views.get_applications, name='get_applications'),
    
    # ------------------------------------------------------------SPCBS User Creation-------------------------------------#
    path('register_spcbs/', views.register_spcbs, name='register_spcbs'),
    path('spcb_users/', views.spcb_users, name='spcb_users'),
    path('spcb_profile/', views.spcb_profile , name='ViewSpcbProfile'),
    path('updatespcbprofile/', views.updatespcbprofile,name='updatespcbprofile' ),
    
    path('generate-certificate/', views.generate_certificate, name='generate_certificate'),
    path('view-certificate/', views.view_certificate, name='view_certificate'),
    path('profile/', views.admin_profile, name='admin_profile'),
    path("logout/", views.admin_logout, name="admin_logout"),

    # ---------------------------------------------------------------- emSigner -----------------------------------------#
    path('generate_certificate/', views.create_pdf, name='create_pdf'),
    path('view-certs/', views.view_certs, name='view_producer_certs'),
    path("esign/cancel/", views.esign_cancel, name="esign_cancel"),
]
