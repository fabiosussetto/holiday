from django import forms
from django.core.exceptions import FieldError
from holiday_manager import models
from django.forms.extras import SelectDateWidget
from django.forms.models import BaseInlineFormSet
import collections
#from django.forms import fields
#from django.forms import widgets
#import jsonfield

#WEEKDAYS = ((0, 'A'), (1, 'B'))

DAY_CHOICES = (
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday")
)


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
        
        
class EditProjectClosuresForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ('closure_week_days',)
    
    #week_day = forms.CharField(widget=forms.CheckboxSelectMultiple(choices=WEEKDAYS))
    closure_week_days = forms.MultipleChoiceField(choices=DAY_CHOICES, widget=forms.SelectMultiple())
    #week_day = forms.CharField(max_length=100)
        
        
class ClosurePeriodForm(ProjectFormMixin, forms.ModelForm):
    class Meta:
        model = models.ClosurePeriod
        fields = ('start', 'end', 'name')
        
        
        

class ListFormField(forms.TypedMultipleChoiceField):
    #def __init__(self, *args, **kwargs):
    #    kwargs['choices'] = utils.DAY_CHOICES
    #    kwargs.pop('max_length', None)
    #    kwargs['widget'] = forms.widgets.SelectMultiple
    #    super(WeekdayFormField, self).__init__(*args, **kwargs)
        
    def clean(self, value):
        value = super(ListFormField, self).clean(value)
        return ",".join([str(x) for x in value])