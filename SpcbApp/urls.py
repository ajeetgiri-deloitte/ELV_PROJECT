from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='spcb_home'),  # e.g., domain.com/rvsf/
    path('dashboard' , views.Dashboard , name='dashboard'),
    path('change_password/', views.ChangePasswordFirstspcb.as_view(), name='change-password-first-spcb'),
    path('addspcbuser' , views.addspcbuser , name='addspcbuser' ),
    path('viewusers' ,views.viewusers , name='viewusers'),
    path('user/toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('user/get-applications/<int:user_id>/', views.get_user_applications, name='get_user_applications'),
    path('viewroles' , views.viewroles , name='viewroles'),
    path('updateRole', views.updateRole , name='updateRole'),
    path('rvsf_applications' , views.rvsf_applications , name= "rvsf_applications"),
    path('list_rvsf',views.list_rvsf , name="list_rvsf"),
    path('viewapplication' , views.viewapplication , name='viewapplication'),
    path("mark_application", views.mark_application, name="mark_application"),
    path('get-trails/', views.get_trails, name='get_trails'),
    path('viewchecklist',views.checklist , name='checklist'),
    # The Checklist Part Form Submission
    path('signupchecklist' ,views.signupchecklist , name='signupchecklist'),
    path('general-checklist/save/', views.insert_or_update_general_checklist, name='save_general_checklist'),
    path('save_equipment_checklist', views.save_equipment_checklist , name='save_equipment_checklist'),
    path('PostFacilityCheckList', views.PostFacilityCheckList , name='PostFacilityCheckList'),
    path('capacity-checklist/', views.CapacityChecklistView, name='CapacityChecklist'),
    path('SavePollutionChecklist' , views.SavePollutionChecklist , name='SavePollutionChecklist'),
    path('SaveWasteRecycleChecklist', views.SaveWasteRecycleChecklist , name='SaveWasteRecycleChecklist'),
    path('SaveDeclarationChecklist', views.SaveDeclarationChecklist, name='SaveDeclarationChecklist'),
    path('mark_back_to_applicant' , views.mark_back_to_applicant , name='mark_back_to_applicant'),
    path('ViewGeneralDetails' , views.ViewGeneralDetails , name='ViewGeneralDetails'),
    path('ViewEquipmentDetails' , views.ViewEquipmentDetails , name='ViewEquipmentDetails'),
    path('ViewFacilityDetails' , views.ViewFacilityDetails , name='ViewFacilityDetails'),
    path('ViewRvsfCapacityDetails' , views.ViewRvsfCapacityDetails , name='ViewRvsfCapacityDetails'),
    path('ViewPollutionDetails' , views.ViewPollutionDetails , name='ViewPollutionDetails'),
    path('ViewWasteRecycleDetails' , views.ViewWasteRecycleDetails , name='ViewWasteRecycleDetails'),
    path('ViewDeclarationDetails' , views.ViewDeclarationDetails , name='ViewDeclarationDetails'),
    path('save_general_trail' , views.save_general_trail , name='save_general_trail'),
    path('MarkIncomplete', views.MarkIncomplete , name='MarkIncomplete'),
    path('GenerateCertificate' , views.GenerateCertificate , name = 'GenerateCertificate'),
    

        # ---------------------------------------------------------------- emSigner -----------------------------------------#
    path('elv/admin/generate_certificate/<int:user_id>/', views.create_pdf, name='create_pdf'),
    path('elv/admin/view-certs/', views.view_certs, name='view_certs'),

    path('upload-attested-certificate/', views.upload_attested_certificate, name='upload_attested_certificate'),
    path('get-certificate-info/', views.get_certificate_info, name='get_certificate_info'),
# urls.py
    path("image-proxy/", views.image_proxy, name="image_proxy"),



    # --------------------------------------------------------- Logics from Producer ------------------------------------ #
    path('rvsfDetails/' , views.rvsf_detail , name = 'rvsf_detail'),
    path('spcbforgetpassword',views.spcbforgetpassword , name='spcbforgetpassword'),
    path('spcbresetpassword',views.spcbresetpassword , name='spcbresetpassword'),
    path('logout', views.logoutspcb, name='logoutspcb'),

    path("protected_spcb/<path:path>/", views.protected_file, name="protected_file_spcb"),
]