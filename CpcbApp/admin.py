from django.contrib import admin

from CpcbApp.models import RoleType, ProgressStatus, CpcbUser

# Register your models here.
admin.site.register(CpcbUser)
admin.site.register(RoleType)
admin.site.register(ProgressStatus)
