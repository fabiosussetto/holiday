from django import forms
from django.core.exceptions import FieldError
from holiday_manager import models
from django.forms.extras import SelectDateWidget
from django.forms.models import BaseInlineFormSet
import collections
#from django.forms import fields
#from django.forms import widgets
#import jsonfield

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
        fields = ('name', 'slug', 'plan_users', 'plan')
        
    def save(self, **kwargs):
        return models.Project.subscription.create(self.instance)
        
        

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
        widgets = {
            'approver': forms.Select(attrs={'class': 'select2'}),
            'order': forms.HiddenInput(attrs={'class': 'order'})
        }

class ApprovalRulesFormset(BaseInlineFormSet):
    
    def clean(self):
        try:
            approvers = [form.cleaned_data['approver'] for form in self.forms if 'approver' in form.cleaned_data]
            occourrences = collections.Counter(approvers)
            duplicates = [item for item in occourrences if occourrences[item] > 1]
            if duplicates:
                raise forms.ValidationError("You can specify an approver just once.")
        except AttributeError:
            pass
    

class ApproveRequestForm(forms.ModelForm):
    class Meta:
        model = models.HolidayApproval
        fields = ('notes',)

        
class EditProjectSettingsForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ('name', 'day_count_reset_date', 'default_timezone', 'default_days_off',
                  'google_calendar_id')
        widgets = {
            'google_calendar_id': forms.Select(),
        }
        
        
class ClosurePeriodForm(ProjectFormMixin, forms.ModelForm):
    class Meta:
        model = models.ClosurePeriod
        fields = ('start', 'end', 'name')
        
        
#class JSONListWidget(widgets.MultiWidget):
#    pass
    
        
#class JSONListField(fields.MultiValueField):
#    widget = JSONListWidget
    
    

    #def __init__(self, *args, **kwargs):
    #    """
    #    Have to pass a list of field types to the constructor, else we
    #    won't get any data to our compress method.
    #    """
    #    all_fields = (
    #        fields.CharField(),
    #        fields.CharField(),
    #        )
    #    super(UserAutoCompleteField, self).__init__(all_fields, *args, **kwargs)

    #def compress(self, data_list):
    #    """
    #    Takes the values from the MultiWidget and passes them as a
    #    list to this function. This function needs to compress the
    #    list into a single object to save.
    #    """
    #    if data_list:
    #        return User.objects.get(id=data_list[0])
    #    return None
    
    
#class JSONListField(jsonfield.JSONField):
#    widget = JSONListWidget
#    
#    def render(self, name, value, attrs=None):
#        print value
#        return super(JSONListField, self).render(name, value, attrs=attrs)