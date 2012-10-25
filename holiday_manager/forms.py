from django import forms
from holiday_manager import models

        
class AddHolidayRequestForm(forms.ModelForm):
    class Meta:
        model = models.HolidayRequest
        fields = ('start_date', 'end_date', 'notes')
        

class ApprovalGroupForm(forms.ModelForm):
    class Meta:
        model = models.ApprovalGroup
        fields = ('name',)
        
        
class ApprovalRuleForm(forms.ModelForm):
    class Meta:
        model = models.ApprovalRule
        fields = ('approver',)
    
        
