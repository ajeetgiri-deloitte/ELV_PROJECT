from django.contrib import admin

from SpcbApp.models import ApplicationStatus, StateRoles, StateUsers
from registration.models import State

# Register your models here.


admin.site.register(StateUsers)
admin.site.register(StateRoles)
admin.site.register(ApplicationStatus)
admin.site.register(State)
