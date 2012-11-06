from django import forms
from django.core.exceptions import FieldError
from holiday_manager import models
from django.forms.extras import SelectDateWidget

class ProjectFormMixin(object):
    
    project = None
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super(ProjectFormMixin, self).__init__(*args, **kwargs)
        if project:
            self.set_project(project)
            
    def set_project(self, project):
        self.project = project
        for name, field in self.fields.items():
            if isinstance(field, forms.models.ModelChoiceField):
                try:
                    field.queryset = field.queryset.filter(project=self.project)
                except FieldError:
                    pass
                    
    def save(self, *args, **kwargs):
        self.instance.project = self.project
        return super(ProjectFormMixin, self).save(*args, **kwargs)
        


class CreateProjectForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ('name', 'slug')
        

class AddHolidayRequestForm(ProjectFormMixin, forms.ModelForm):
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
        
        
class ApprovalRuleForm(ProjectFormMixin, forms.ModelForm):
    class Meta:
        model = models.ApprovalRule
        fields = ('approver', 'order')
        

class ApproveRequestForm(forms.ModelForm):
    class Meta:
        model = models.HolidayApproval
        fields = ('notes',)

        
class EditProjectSettingsForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ('name', 'day_count_reset_date', 'default_timezone', 'default_days_off',)