from django import forms
from holiday_manager import models
from invites.models import User
from django.forms.extras import SelectDateWidget

class CreateProjectForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ('name', 'slug')
        

class AddHolidayRequestForm(forms.ModelForm):
    class Meta:
        model = models.HolidayRequest
        fields = ('start_date', 'end_date', 'notes')
        widgets = {
            'start_date': SelectDateWidget(),
            'end_date': SelectDateWidget()
        }
        

class ApprovalGroupForm(forms.ModelForm):
    class Meta:
        model = models.ApprovalGroup
        fields = ('name',)
        
        
class ApprovalRuleForm(forms.ModelForm):
    class Meta:
        model = models.ApprovalRule
        fields = ('approver',)
        

class ApproveRequestForm(forms.ModelForm):
    class Meta:
        model = models.HolidayApproval
        fields = ('notes',)
