from django.db import models

# Create your models here.
class StateUsers(models.Model):
    username = models.CharField(max_length=150, unique=True , null=True)
    password = models.CharField(max_length=128, blank=True,null=True)
    auth_mobile = models.CharField(max_length=10, default=9999999999)
    auth_email = models.EmailField(default='test@gmail.com')
    OfficerName= models.CharField(max_length=100, null=True)
    officerDesignation = models.CharField(max_length=100, null=True)
    RoleAccess = models.CharField(max_length=100, null=True)
    State_id = models.IntegerField(default=0)
    District_id = models.IntegerField(default=0)
    DisableStatus = models.IntegerField(default=0)
    
    class Meta:
            db_table = 'spcbapp_stateusers'
        
class StateRoles(models.Model):
    Rolename = models.CharField(max_length=100 , null=True)
    class Meta:
        db_table = 'spcbapp_stateroles'
    def __str__(self):
        return self.Rolename  # O
    
class ApplicationTrail(models.Model):
    AppNo = models.CharField(max_length=100 ,null=True)
    stateid = models.IntegerField(default=0)
    marked_to_designation = models.CharField(max_length=50 , null=True)
    marked_by_designation = models.CharField(max_length=50 , null=True) 
    marked_to_role = models.IntegerField(default=0)  # Recommending Authority / Reporting Authority
    marked_by_role = models.IntegerField(default=0)  # Recommending Authority / Reporting Authority
    comment = models.TextField(blank=True, null=True)
    added_by_userid = models.IntegerField(default=0)
    added_by_person= models.CharField(max_length=100 , null=True)
    added_to_userid = models.IntegerField(default=0)
    added_to_person= models.CharField(max_length=100 , null=True)
    industry_user_id = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class ApplicationStatus(models.Model):
    AppStatus = models.IntegerField(unique=True)
    Description = models.CharField(max_length=100)
    RoleAccess = models.IntegerField(default=0)
    DisableStatus = models.IntegerField(default=0)


    def __str__(self):
        return self.Description  # O
